-- RG-019 arcade ground-truth: latch stage state at first appearance (state2==3 & pstate in 1..3).
local machine=manager.machine
local prog=assert(machine.devices[":maincpu"].spaces["program"])
local region=machine.memory.regions[":maincpu"]
local td=assert(os.getenv("TRACE_DIR"))
local sel_addr=tonumber(os.getenv("SEL_ADDR") or "0x5FFFD")
local sel_val=tonumber(os.getenv("SEL_VAL") or "-1")
local maxf=tonumber(os.getenv("MAX_FRAMES") or "3000")
local fields={}; for _,p in pairs(machine.ioport.ports) do for n,f in pairs(p.fields) do fields[n]=f end end
local function si(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local function r8(a) return prog:read_u8(a)&0xff end
local function r16(a) return prog:read_u16(a)&0xffff end
if sel_val>=0 and region then region:write_u8(sel_addr,sel_val) end
local frame=0; local latched=nil; local appeared=nil
emu.register_frame_done(function()
  frame=frame+1
  if sel_val>=0 and region then region:write_u8(sel_addr,sel_val) end
  si("Coin 1", frame>=600 and frame<=612)
  si("1 Player Start", frame>=655 and frame<=667)
  si("P1 Right", appeared~=nil)
  local s2=r16(0x10C002); local ps=r16(0x10D0E8)
  if appeared==nil and r16(0x10C000)==2 and s2==3 and ps>=1 and ps<=3 then
    appeared=frame
    latched=string.format("APPEAR@%d round=%02X stage=%04X subr=%02X s0=%04X s2=%04X ps=%04X px=%04X cfg9F=%02X cfgFD=%02X",
      frame, r8(0x10C118), r16(0x10D242), r8(0x10D243), r16(0x10C000), s2, ps, r16(0x10D0BE), r8(0x05FF9F), r8(0x05FFFD))
  end
  if frame>=maxf then
    local o=assert(io.open(td.."/probe.tsv","w"))
    o:write(string.format("sel=0x%06X val=%d\n%s\n",sel_addr,sel_val, latched or "NO APPEARANCE by frame "..maxf))
    o:close(); machine:exit()
  end
end)
