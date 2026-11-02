-- Build 0529 human-played R1-S2 rope trace. This script never writes game memory or input.
local m = manager.machine
assert(m.system.name == "genesis", "requires GENESIS NTSC machine 'genesis'")
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local td = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local mode = assert(os.getenv("TRACE_MODE"), "TRACE_MODE is required")
local function envaddr(n)
  local value=os.getenv(n)
  assert(value,n.." missing")
  return assert(tonumber(value),n.." invalid")
end
local A5=0x00ff0000
local STAGED=envaddr("R1S2_STAGED_FG_ADDR")
local DIRTY=envaddr("R1S2_FG_ROW_DIRTY_ADDR")
local COL_DIRTY=envaddr("R1S2_FG_COL_DIRTY_ADDR")
local NARROW=envaddr("R1S2_NARROW_COUNT_ADDR")
local SCROLL_X=envaddr("R1S2_SCROLL_X_ADDR")
local SCROLL_Y=envaddr("R1S2_SCROLL_Y_ADDR")
local VC=envaddr("R1S2_VBLANK_VC_ADDR")
local SRC_REF=envaddr("R1S2_SRC_REF_ADDR")
local pcs={
  SELECTOR0=envaddr("R1S2_PC_SELECTOR0"), SELECTOR12=envaddr("R1S2_PC_SELECTOR12"),
  PAN_UP=envaddr("R1S2_PC_PAN_UP"), PAN_DOWN=envaddr("R1S2_PC_PAN_DOWN"),
  FG_COMMIT=envaddr("R1S2_PC_FG_COMMIT"), SCROLL_COMMIT=envaddr("R1S2_PC_SCROLL_COMMIT")
}
local function r8(a) return p:read_u8(a)&0xff end
local function r16(a) return p:read_u16(a)&0xffff end
local function r32(a) return p:read_u32(a)&0xffffffff end
local function reg(n) local s=cpu.state[n]; return s and (s.value&0xffffffff) or 0 end
local function hx(v,n) return string.format("%0"..n.."X",v) end
local frames=assert(io.open(td.."/frames.tsv","w"))
local events=assert(io.open(td.."/events.tsv","w"))
local markers=assert(io.open(td.."/markers.tsv","w"))
local meta=assert(io.open(td.."/metadata.txt","w"))
frames:write(table.concat({"frame","marker","input","invincibility_state","player_x","player_y","accum_up","accum_down","accum_left","accum_right","step_y","camera_delta","scroll_flags","scroll_direction","fg_x","fg_y","staged_fg_x","staged_fg_y","record","selector","completed_selector","strip","group","player_state","facing","src_ref","fg_row_dirty","fg_col_dirty","narrow_count","selection_mode","entering_logical_rows","entering_physical_rows","vc0","vc1","vc2","vc3","vc4","vc5","vc6","plane_a_vlines","total_vlines","dirty_write_count","vc_write_sequence","path_events","staged_rows"},"\t"),"\n")
events:write("frame\tevent\tpc\tdetail\n")
markers:write("frame\tmode\tfg_y\trecord\tselector\tstrip\tgroup\tplayer_x\tplayer_y\n")
meta:write("platform=GENESIS NTSC MAME\nmachine=genesis\nmode="..mode.."\n")
meta:write("rom="..(os.getenv("ROM_NAME") or "UNKNOWN").."\nrom_sha256="..(os.getenv("ROM_SHA") or "UNKNOWN").."\n")
meta:write("source_commit="..(os.getenv("SOURCE_COMMIT") or "UNKNOWN").."\nstarted="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\n")
meta:write("input_policy=manual only; no ioport or WRAM writes\nmarker_key=M\n")
meta:write("inferred_fields=scroll_direction,selection_mode,entering rows; all are labeled derived\n")
meta:write("verified_player_state=a5+10E8 (state 4 is rope-attached); facing=a5+1114 (2 visually left)\n")
meta:write("invincibility=a5+0040 bit 0040 from original startup configuration; trace does not write it\n")

local frame,closed=0,false
local last_y=nil
local rowwrites={}
local path_hits={}
local path_sequence={}
local dirty_write_count=0
local vc_write_sequence={}
local taps={}
local debuglog=m.debugger and m.debugger.consolelog or nil
local debug_index=debuglog and #debuglog or 0
local marker_code=assert(m.input:code_from_token("KEYCODE_M"),"KEYCODE_M unavailable")
local marker_prev=false

local function add_event(name,pc,detail)
  events:write(string.format("%d\t%s\t%06X\t%s\n",frame,name,pc&0xffffff,detail or ""))
end
local function hit(name)
  path_hits[name]=(path_hits[name] or 0)+1
  path_sequence[#path_sequence+1]=name
  add_event(name,reg("PC"),"execution")
end

-- Prefer execute taps when exposed; otherwise use debugger breakpoints and drain their log.
local exec_kind="execute_tap"
if type(p.install_execute_tap)=="function" then
  for name,pc in pairs(pcs) do
    local n=name
    taps[#taps+1]=p:install_execute_tap(pc,pc,"r1s2_"..n,function() hit(n) end)
  end
else
  exec_kind="debugger_breakpoints"
  assert(debuglog,"launch with -debug -debugger none")
  for name,pc in pairs(pcs) do
    cpu.debug:bpset(pc,"1",string.format('printf "R1S2,%s,%%06X\\n",pc; g',name))
  end
  m.debugger:command("go")
end
meta:write("execution_event_mechanism="..exec_kind.."\n")

local function drain_debug()
  if not debuglog then return end
  for i=debug_index+1,#debuglog do
    local name,pc=tostring(debuglog[i]):match("^R1S2,([A-Z0-9_]+),([0-9A-Fa-f]+)")
    if name then
      path_hits[name]=(path_hits[name] or 0)+1
      path_sequence[#path_sequence+1]=name
      add_event(name,tonumber(pc,16) or 0,"debugger execution")
    end
  end
  debug_index=#debuglog
end

-- Aggregate writes by physical row. PC sets expose later/conflicting writers without per-word I/O.
taps[#taps+1]=p:install_write_tap(STAGED,STAGED+0x0fff,"r1s2_staged",function(off,data,mask)
  local rel=off-STAGED
  local row=(rel>>7)&31
  local col=(rel>>1)&63
  local w=rowwrites[row] or {count=0,first=63,last=0,hash=0,pcs={}}
  w.count=w.count+1; if col<w.first then w.first=col end; if col>w.last then w.last=col end
  w.hash=((w.hash*65599)+(data&0xffff)+col)&0xffffffff
  w.pcs[hx(reg("PC")&0xffffff,6)]=true
  rowwrites[row]=w
  return data
end)
taps[#taps+1]=p:install_write_tap(DIRTY,DIRTY+3,"r1s2_dirty",function(_,data)
  dirty_write_count=dirty_write_count+1; return data
end)
taps[#taps+1]=p:install_write_tap(VC,VC+7,"r1s2_vc",function(off,data)
  vc_write_sequence[#vc_write_sequence+1]=string.format("%d:%02X",off-VC,data&0xff); return data
end)
_G.r1s2_rope_trace_taps=taps

local function signed16(v) return v>=0x8000 and v-0x10000 or v end
local function vdelta(a,b) local d=(b-a)%262; return d end
local function derive_rows(oldy,newy)
  if oldy==nil then return "","" end
  local ot=(((-oldy+8)&0x1ff)>>3)&63
  local nt=(((-newy+8)&0x1ff)>>3)&63
  local f=(nt-ot)&63; local b=(ot-nt)&63
  local logical={}
  if f>0 and f<=8 then for i=1,f do logical[#logical+1]=(ot+i+31)&63 end
  elseif b>0 and b<=8 then for i=1,b do logical[#logical+1]=(ot-i)&63 end end
  local physical={}; for _,v in ipairs(logical) do physical[#physical+1]=v&31 end
  return table.concat(logical,","),table.concat(physical,",")
end
local function selection_mode()
  local sel,done,rec=r16(A5+0x10a8),r16(A5+0x132c),r16(A5+0x013e)
  if sel~=0 then return done==0 and ("derived:predecessor_record_"..tostring((rec-1)&0xffff)) or ("derived:predecessor_pan_record_"..tostring((rec-1)&0xffff)) end
  return "derived:current_dynamic_or_previous_selector0"
end
local function sorted_keys(t) local a={}; for k in pairs(t) do a[#a+1]=k end; table.sort(a); return table.concat(a,",") end
local function close()
  if closed then return end; closed=true; drain_debug()
  meta:write("ended="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\ntotal_frames="..frame.."\n")
  frames:flush(); events:flush(); markers:flush(); meta:flush()
  frames:close(); events:close(); markers:close(); meta:close()
end

emu.register_frame_done(function()
  frame=frame+1; drain_debug()
  local down=false; pcall(function() down=m.input:code_pressed(marker_code) end)
  local mark=down and not marker_prev; marker_prev=down
  local y=r16(A5+0x10b0); local logical,physical=derive_rows(last_y,y)
  local delta=last_y and signed16((y-last_y)&0xffff) or 0
  local direction=delta<0 and "derived:up" or (delta>0 and "derived:down" or "derived:none")
  local staged={}
  for row,w in pairs(rowwrites) do
    local d=string.format("row=%d count=%d cols=%d-%d hash=%08X pcs=%s",row,w.count,w.first,w.last,w.hash,sorted_keys(w.pcs))
    staged[#staged+1]=d; add_event("STAGED_ROW_WRITES",0,d)
  end
  table.sort(staged)
  local paths=table.concat(path_sequence,">")
  local vc={}; for i=0,6 do vc[#vc+1]=r8(VC+i) end
  local row=table.concat({
    frame,mark and 1 or 0,hx(r16(A5+0x0016),4),hx(r16(A5+0x0040),4),hx(r16(A5+0x10be),4),hx(r16(A5+0x10c0),4),
    hx(r16(A5+0x1262),4),hx(r16(A5+0x1264),4),hx(r16(A5+0x1266),4),hx(r16(A5+0x1268),4),
    signed16(r16(A5+0x10de)),signed16(r16(A5+0x10da)),hx(r16(A5+0x10d0),4),direction,
    hx(r16(A5+0x10ae),4),hx(y,4),hx(r16(SCROLL_X),4),hx(r16(SCROLL_Y),4),
    hx(r16(A5+0x013e),4),hx(r16(A5+0x10a8),4),hx(r16(A5+0x132c),4),hx(r16(A5+0x10ca),4),hx(r16(A5+0x10cc),4),
    hx(r16(A5+0x10e8),4),hx(r16(A5+0x1114),4),hx(r32(SRC_REF)&0xffffff,6),hx(r32(DIRTY),8),hx(r32(COL_DIRTY),8),r16(NARROW),
    selection_mode(),logical,physical,vc[1],vc[2],vc[3],vc[4],vc[5],vc[6],vc[7],vdelta(vc[4],vc[5]),vdelta(vc[1],vc[7]),dirty_write_count,table.concat(vc_write_sequence,","),paths,table.concat(staged,";")
  },"\t")
  frames:write(row,"\n")
  if mark then
    markers:write(table.concat({frame,mode,hx(y,4),hx(r16(A5+0x013e),4),hx(r16(A5+0x10a8),4),hx(r16(A5+0x10ca),4),hx(r16(A5+0x10cc),4),hx(r16(A5+0x10be),4),hx(r16(A5+0x10c0),4)},"\t"),"\n")
    markers:flush(); emu.print_info("R1-S2 USER_MARK recorded at trace frame "..frame)
  end
  if frame%60==0 then frames:flush(); events:flush() end
  rowwrites={}; path_hits={}; path_sequence={}; dirty_write_count=0; vc_write_sequence={}; last_y=y
end)
_G.r1s2_rope_trace_stop=emu.add_machine_stop_notifier(close)
emu.print_info("R1-S2 "..mode.." human trace armed; press M whenever corruption is visible")
