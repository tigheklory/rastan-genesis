-- Read-only: measure worst-case VBlank publication overrun. The _s variant computes it into the P1
-- score BCD (0xFF011E) as scanlines overrun (0=fit in vblank, N=bled N active lines). We also read the
-- live VDP V-counter to sanity-check. Drives coin/start + right-scroll to load the heavy publication.
local mac=manager.machine
local cpu=assert(mac.devices[":maincpu"]); local pr=assert(cpu.spaces["program"])
local out=assert(io.open(os.getenv("DUMP_OUT"),"w"))
local function r8(a) return pr:read_u8(a)&0xff end
local function r16(a) return pr:read_u16(a)&0xffff end
local fields={}
for _,port in pairs(mac.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function setin(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local frame=0; local peak=0
emu.register_frame_done(function()
  frame=frame+1
  setin("P1 A", frame>=120 and frame<=132)
  setin("P1 Start", frame>=175 and frame<=187)
  setin("P1 Right", frame>=360)                 -- keep scrolling right = heavy horizontal publication
  local score=string.format("%02X%02X%02X", r8(0xFF011E), r8(0xFF011F), r8(0xFF0120))
  if frame%60==0 then
    out:write(string.format("f=%d score/metric(0xFF011E..)=%s scrollX=%d scrollY=%d rec=%d\n",
      frame, score, r16(0xFF409A), r16(0xFF409E), r16(0xFF013E))); out:flush()
  end
  if frame>=1200 then mac:exit() end
end)
