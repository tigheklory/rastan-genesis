-- RG-019 Genesis subround functional probe: latch the STAGE INDEX (a5@0x1242 = 0x00FF1242)
-- at first appearance (state2==3, player_state in 1..3).  The stage index -- not the round
-- counter -- is the authoritative selection result (confirmed on the arcade: R6 -> 0x73).
local machine=manager.machine
local prog=assert(machine.devices[":maincpu"].spaces["program"])
local td=assert(os.getenv("TRACE_DIR"))
local exp_stage=tonumber(os.getenv("EXPECT_STAGE") or "-1")
local maxf=tonumber(os.getenv("MAX_FRAMES") or "1400")
local fields={}; for _,p in pairs(machine.ioport.ports) do for n,f in pairs(p.fields) do fields[n]=f end end
local function si(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local function r16(a) return prog:read_u16(a)&0xffff end
local function r8(a) return prog:read_u8(a)&0xff end
local frame=0; local latched=nil; local appeared=nil
emu.register_frame_done(function()
  frame=frame+1
  si("Coin 1", frame>=120 and frame<=132); si("P1 A", frame>=120 and frame<=132)
  si("1 Player Start", frame>=175 and frame<=187); si("P1 Start", frame>=175 and frame<=187)
  si("P1 Right", appeared~=nil)
  local s2=r16(0x00FF0002); local ps=r16(0x00FF10E8)
  if appeared==nil and r16(0x00FF0000)==2 and s2==3 and ps>=1 and ps<=3 then
    appeared=frame
    latched=string.format("APPEAR@%d stage=0x%04X round=%02X px=0x%04X cfg5FF9F=0x%02X",
      frame, r16(0x00FF1242), r8(0x00FF0118), r16(0x00FF10BE), r8(0x0005FF9F))
  end
  if frame>=maxf then
    local o=assert(io.open(td.."/probe.tsv","w"))
    local got = latched and tonumber(latched:match("stage=0x(%x+)"),16) or -1
    local res = (exp_stage<0) and "N/A" or ((got==exp_stage) and "PASS" or "FAIL")
    o:write(string.format("expect_stage=0x%04X %s result=%s\n",(exp_stage<0 and 0 or exp_stage),latched or "NO-APPEARANCE",res))
    o:close(); machine:exit()
  end
end)
