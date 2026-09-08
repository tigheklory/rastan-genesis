local mac=manager.machine
local cpu=assert(mac.devices[":maincpu"]); local pr=assert(cpu.spaces["program"])
local out=assert(io.open(os.getenv("DUMP_OUT"),"w"))
local function r8(a) return pr:read_u8(a)&0xff end
local function r16(a) return pr:read_u16(a)&0xffff end
local fields={}
for _,port in pairs(mac.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function setin(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local VC=0xFF6180
local function d(a,b) local x=(b-a)%262; return x end   -- scanlines from mark a to mark b (wrap 262)
local frame=0; local worst=-1; local wrec={}
local names={"palette","tiles","bgPlaneB","fgPlaneA","sprites","scroll"}
emu.register_frame_done(function()
  frame=frame+1
  setin("P1 A", frame>=120 and frame<=132)
  setin("P1 Start", frame>=175 and frame<=187)
  setin("P1 Right", frame>=360)
  if frame>=420 then
    local v={} for i=0,6 do v[i]=r8(VC+i) end
    local total=d(v[0],v[6])
    if total>worst and total<262 then
      worst=total
      wrec={frame=frame, v=v, total=total}
    end
  end
  if frame>=1200 then
    if wrec.frame then
      out:write(string.format("WORST publication frame=%d total=%d scanlines (vblank window ~38; active=224)\n",wrec.frame,wrec.total))
      out:write("  raw V marks [entry..scroll]: ")
      for i=0,6 do out:write(wrec.v[i].." ") end
      out:write("\n  per-commit scanlines:\n")
      for i=0,5 do out:write(string.format("    %-9s %d\n", names[i+1], d(wrec.v[i],wrec.v[i+1]))) end
    else out:write("no gameplay frames captured\n") end
    out:flush(); mac:exit()
  end
end)
