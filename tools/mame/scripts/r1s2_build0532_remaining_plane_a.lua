-- Read-only Build-0532 ordered Plane-A writer/residency trace (PROMT-ID-0072).
-- Records every staging write, every provenance write, pre/post touched rows,
-- VDP rows, and a complete 32-row marker snapshot. It never writes emulated
-- memory or controller input.
local m = manager.machine
assert(m.system.name == "genesis", "requires GENESIS NTSC machine 'genesis'")
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local vdp = assert(m.devices[":gen_vdp"])
local vram = assert(vdp.spaces["videoram"])
local td = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")

local function envnum(name)
  local value = assert(os.getenv(name), name .. " missing")
  return assert(tonumber(value), name .. " invalid")
end
local A5, PLANE_A = 0x00ff0000, 0x0000e000
local STAGED = envnum("R1S2_STAGED_FG_ADDR")
local DIRTY = envnum("R1S2_FG_ROW_DIRTY_ADDR")
local OWNER = envnum("R1S2_PROVENANCE_ADDR")
local FG_COMMIT = envnum("R1S2_PC_FG_COMMIT")
local SCROLL_COMMIT = envnum("R1S2_PC_SCROLL_COMMIT")
local SEL0 = envnum("R1S2_PC_SELECTOR0")
local SEL12 = envnum("R1S2_PC_SELECTOR12")
local RESEED = envnum("R1S2_PC_RESEED")
local PAN = envnum("R1S2_PC_PAN")
local RESOLVER = envnum("R1S2_PC_RESOLVER")
local FG_FILL = envnum("R1S2_PC_FG_FILL")
local PHASE3 = envnum("R1S2_PC_PHASE3")
local MAX_FRAMES = tonumber(os.getenv("TRACE_MAX_FRAMES") or "0") or 0

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function vr16(a) return (((vram:read_u8(a) & 0xff) << 8) | (vram:read_u8(a+1) & 0xff)) & 0xffff end
local function reg(n) local s=cpu.state[n]; return s and (s.value & 0xffffffff) or 0 end
local function hx(v,n) return string.format("%0"..n.."X",v) end
local function dirty(row) return (r32(DIRTY) >> row) & 1 end
local function row_words(kind,row)
  local t, base = {}, row * 0x80
  for c=0,63 do t[#t+1] = kind == "staged" and r16(STAGED+base+c*2) or vr16(PLANE_A+base+c*2) end
  return t
end
local function hash(words)
  local h=2166136261
  for _,w in ipairs(words) do h=((h ~ w)*16777619)&0xffffffff end
  return h
end
local function words_text(words)
  local t={}; for i,w in ipairs(words) do t[i]=hx(w,4) end; return table.concat(t,",")
end
local function state()
  local strip,group=r16(A5+0x10ca),r16(A5+0x10cc)
  return table.concat({
    "fg_y="..hx(r16(A5+0x10b0),4), "record="..hx(r16(A5+0x013e),4),
    "selector="..hx(r16(A5+0x10a8),4), "completed_selector="..hx(r16(A5+0x132c),4),
    "strip="..hx(strip,4), "group="..hx(group,4),
    "front="..tostring(((group&15)*4+(strip&3))&63),
    "player_x="..hx(r16(A5+0x10be),4), "player_y="..hx(r16(A5+0x10c0),4)
  },";")
end
local function writer(pc)
  if pc>=SEL0 and pc<SEL12 then return "selector0" end
  if pc>=SEL12 and pc<RESEED then return "selector12" end
  if pc>=RESEED and pc<PAN then return "scene_reseed" end
  if pc>=PAN and pc<0x0007147c then return "pan_or_materializer" end
  if pc>=FG_FILL and pc<PHASE3 then return "fg_fill" end
  if pc>=PHASE3 and pc<PHASE3+0x50 then return "phase3_animation" end
  return "other"
end

local writes=assert(io.open(td.."/ordered_writes.tsv","w"))
local owners=assert(io.open(td.."/provenance_writes.tsv","w"))
local rows=assert(io.open(td.."/row_snapshots.tsv","w"))
local events=assert(io.open(td.."/events.tsv","w"))
local frames=assert(io.open(td.."/frames.tsv","w"))
local markers=assert(io.open(td.."/markers.tsv","w"))
local markerrows=assert(io.open(td.."/marker_rows.tsv","w"))
local meta=assert(io.open(td.."/metadata.txt","w"))
writes:write("sequence\tframe\tpc\twriter\tphysical\tcolumn\told_word\tnew_word\towner_before\tdirty_before\tstate\n")
owners:write("sequence\tframe\tpc\tphysical\told_owner\tnew_owner\tstaged_hash\tvdp_hash\tdirty\tstate\n")
rows:write("sequence\tframe\tphase\tphysical\towner\tdirty\tstaged_hash\tvdp_hash\tstaged_words_64\tvdp_words_64\tstate\n")
events:write("sequence\tframe\tevent\tpc\trow_dirty\tstate\n")
frames:write("frame\tfg_y\tdelta\tdirection\trecord\tselector\tcompleted_selector\tstrip\tgroup\tfront\trow_dirty\towners\n")
markers:write("frame\tsequence\tfg_y\trecord\tselector\tstrip\tgroup\tfront\tplayer_x\tplayer_y\n")
markerrows:write("frame\tphysical\towner\tdirty\tstaged_hash\tvdp_hash\tstaged_words_64\tvdp_words_64\tstate\n")
meta:write("platform=GENESIS NTSC MAME\nmachine=genesis\npurpose=Build 0532 remaining R1-S2 first-bad-transition\n")
meta:write("input_policy=manual only; no game-memory, ROM, controller, or save-state writes\n")
meta:write("rom_sha256="..(os.getenv("ROM_SHA") or "UNKNOWN").."\nrom_source_commit="..(os.getenv("ROM_SOURCE_COMMIT") or "UNKNOWN").."\n")
meta:write("marker_key=M\nstarted="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\n")

local frame,sequence,last_y,closed=0,0,nil,false
local touched, taps = {}, {}
local marker=assert(m.input:code_from_token("KEYCODE_M")); local marker_down=false
local function snapshot(file,phase,row)
  local sw,vw=row_words("staged",row),row_words("vdp",row)
  sequence=sequence+1
  file:write(table.concat({sequence,frame,phase,row,hx(r8(OWNER+row),2),dirty(row),hx(hash(sw),8),hx(hash(vw),8),words_text(sw),words_text(vw),state()},"\t"),"\n")
end
local function event(name)
  sequence=sequence+1
  events:write(table.concat({sequence,frame,name,hx(reg("PC")&0xffffff,6),hx(r32(DIRTY),8),state()},"\t"),"\n")
end

taps[#taps+1]=p:install_write_tap(STAGED,STAGED+0x0fff,"r1s2_0532_staged",function(off,data,mask)
  local rel=off-STAGED; local row=(rel>>7)&31; local col=(rel>>1)&63
  if not touched[row] then snapshot(rows,"PRE_FIRST_WRITE",row); touched[row]=true end
  sequence=sequence+1
  local pc=reg("PC")&0xffffff
  writes:write(table.concat({sequence,frame,hx(pc,6),writer(pc),row,col,hx(r16(off&0xfffffe),4),hx(data&0xffff,4),hx(r8(OWNER+row),2),dirty(row),state()},"\t"),"\n")
  return data
end)
taps[#taps+1]=p:install_write_tap(OWNER,OWNER+31,"r1s2_0532_owner",function(off,data,mask)
  local row=off-OWNER; local sw,vw=row_words("staged",row),row_words("vdp",row)
  sequence=sequence+1
  owners:write(table.concat({sequence,frame,hx(reg("PC")&0xffffff,6),row,hx(r8(off),2),hx(data&0xff,2),hx(hash(sw),8),hx(hash(vw),8),dirty(row),state()},"\t"),"\n")
  touched[row]=true
  return data
end)
if type(p.install_execute_tap)=="function" then
  for _,item in ipairs({{FG_COMMIT,"PLANE_A_COMMIT"},{SCROLL_COMMIT,"SCROLL_COMMIT"},{SEL0,"SELECTOR0_ENTRY"},{SEL12,"SELECTOR12_ENTRY"},{PAN,"PAN_UP_ENTRY"}}) do
    local pc,name=item[1],item[2]
    taps[#taps+1]=p:install_execute_tap(pc,pc,"r1s2_0532_"..name,function() event(name) end)
  end
end
_G.r1s2_build0532_taps=taps

local function marker_dump()
  markers:write(table.concat({frame,sequence,hx(r16(A5+0x10b0),4),hx(r16(A5+0x013e),4),hx(r16(A5+0x10a8),4),hx(r16(A5+0x10ca),4),hx(r16(A5+0x10cc),4),((r16(A5+0x10cc)&15)*4+(r16(A5+0x10ca)&3))&63,hx(r16(A5+0x10be),4),hx(r16(A5+0x10c0),4)},"\t"),"\n")
  for row=0,31 do
    local sw,vw=row_words("staged",row),row_words("vdp",row)
    markerrows:write(table.concat({frame,row,hx(r8(OWNER+row),2),dirty(row),hx(hash(sw),8),hx(hash(vw),8),words_text(sw),words_text(vw),state()},"\t"),"\n")
  end
  markerrows:flush(); markers:flush(); event("USER_MARK")
  emu.print_info("Build 0532 remaining Plane-A marker recorded at frame "..frame)
end
local function close()
  if closed then return end; closed=true
  meta:write("ended="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\nframes="..frame.."\nsequences="..sequence.."\n")
  for _,f in ipairs({writes,owners,rows,events,frames,markers,markerrows,meta}) do f:flush(); f:close() end
end
emu.register_frame_done(function()
  frame=frame+1
  local y=r16(A5+0x10b0); local delta=last_y and (((y-last_y+0x8000)&0xffff)-0x8000) or 0
  local direction=delta<0 and "up" or (delta>0 and "down" or "none")
  local ownertext={}; for row=0,31 do ownertext[#ownertext+1]=hx(r8(OWNER+row),2) end
  frames:write(table.concat({frame,hx(y,4),delta,direction,hx(r16(A5+0x013e),4),hx(r16(A5+0x10a8),4),hx(r16(A5+0x132c),4),hx(r16(A5+0x10ca),4),hx(r16(A5+0x10cc),4),((r16(A5+0x10cc)&15)*4+(r16(A5+0x10ca)&3))&63,hx(r32(DIRTY),8),table.concat(ownertext,",")},"\t"),"\n")
  for row,_ in pairs(touched) do snapshot(rows,"POST_FRAME",row) end
  touched={}; last_y=y
  local down=false; pcall(function() down=m.input:code_pressed(marker) end)
  if down and not marker_down then marker_dump() end; marker_down=down
  if frame%60==0 then for _,f in ipairs({writes,owners,rows,events,frames}) do f:flush() end end
  if MAX_FRAMES>0 and frame>=MAX_FRAMES then close(); m:exit() end
end)
_G.r1s2_build0532_stop=emu.add_machine_stop_notifier(close)
emu.print_info("Build 0532 remaining Plane-A trace armed; press M at first visible corruption")
