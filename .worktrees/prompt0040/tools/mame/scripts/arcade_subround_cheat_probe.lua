-- RG-019 arcade ground-truth: latch stage state at first appearance (state2==3 & pstate in 1..3).
local machine=manager.machine
local prog=assert(machine.devices[":maincpu"].spaces["program"])
local region=machine.memory.regions[":maincpu"]
local screen=assert(machine.screens:at(1))
local td=assert(os.getenv("TRACE_DIR"))
local sel_addr=tonumber(os.getenv("SEL_ADDR") or "0x5FFFD")
local sel_val=tonumber(os.getenv("SEL_VAL") or "-1")
local maxf=tonumber(os.getenv("MAX_FRAMES") or "3000")
local capture_static=(os.getenv("CAPTURE_STATIC") or "0") == "1"
local fields={}; for _,p in pairs(machine.ioport.ports) do for n,f in pairs(p.fields) do fields[n]=f end end
local function si(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local function r8(a) return prog:read_u8(a)&0xff end
local function r16(a) return prog:read_u16(a)&0xffff end
local function dump(path,address,size)
  local out=assert(io.open(path,"wb"))
  for offset=0,size-1 do out:write(string.char(r8(address+offset))) end
  out:close()
end
if sel_val>=0 and region then region:write_u8(sel_addr,sel_val) end
local frame=0; local latched=nil; local appeared=nil; local captured=false
emu.register_frame_done(function()
  frame=frame+1
  if sel_val>=0 and region then region:write_u8(sel_addr,sel_val) end
  si("Coin 1", frame>=600 and frame<=612)
  si("1 Player Start", frame>=655 and frame<=667)
  si("P1 Right", appeared~=nil and not capture_static)
  local s2=r16(0x10C002); local ps=r16(0x10D0E8)
  if appeared==nil and r16(0x10C000)==2 and s2==3 and ps>=1 and ps<=3 then
    appeared=frame
    latched=string.format("APPEAR@%d round=%02X stage=%04X subr=%02X s0=%04X s2=%04X ps=%04X px=%04X cfg9F=%02X cfgFD=%02X",
      frame, r8(0x10C118), r16(0x10D242), r8(0x10D243), r16(0x10C000), s2, ps, r16(0x10D0BE), r8(0x05FF9F), r8(0x05FFFD))
  end
  if capture_static and appeared and not captured and frame>=appeared+15 then
    captured=true
    dump(td.."/pc080sn_name_ram.bin",0xC00000,0x10000)
    dump(td.."/collision_map.bin",0x10DE00,0x2000)
    dump(td.."/descriptor_state.bin",0x10D000,0x0100)
    local ok,err=pcall(function() screen:snapshot(td.."/frame.png") end)
    local meta=assert(io.open(td.."/capture.tsv","w"))
    meta:write("frame\tstage\trecord\tselector\tscroll_a_x\tscroll_a_y\tscroll_b_x\tscroll_b_y\tstrip_index\tstrip_group\tstage_byte\tphase3_enable\tphase3_tick\tsnapshot\n")
    meta:write(string.format("%d\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%02X\t%04X\t%04X\t%s\n",
      frame,r16(0x10D242),r16(0x10C13E),r16(0x10D0A8),r16(0x10D0AE),r16(0x10D0B0),r16(0x10D0EC),r16(0x10D0EE),
      r16(0x10D0CA),r16(0x10D0CC),r8(0x10C118),r16(0x10D360),r16(0x10D362),ok and "PASS" or tostring(err)))
    meta:close()
  end
  if frame>=maxf or (captured and frame>=appeared+17) then
    local o=assert(io.open(td.."/probe.tsv","w"))
    o:write(string.format("sel=0x%06X val=%d\n%s\n",sel_addr,sel_val, latched or "NO APPEARANCE by frame "..maxf))
    o:close(); machine:exit()
  end
end)
