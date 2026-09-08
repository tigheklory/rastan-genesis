local mac=manager.machine
local cpu=assert(mac.devices[":maincpu"]); local pr=assert(cpu.spaces["program"])
local out=assert(io.open(os.getenv("DUMP_OUT"),"w"))
local function r16(a) return pr:read_u16(a)&0xffff end
local function r32(a) return pr:read_u32(a)&0xffffffff end
local fields={}
for _,port in pairs(mac.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function setin(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local frame=0; local shots=0
emu.register_frame_done(function()
  frame=frame+1
  setin("P1 A", frame>=120 and frame<=132)
  setin("P1 Start", frame>=175 and frame<=187)
  setin("P1 Right", frame>=360 and frame<=420)   -- brief nudge into the level, then release
  -- dump when Plane-A staging holds real content, a handful of times
  local nonzero=false
  for c=0,63 do if r16(0xFF50A0+(20*64+c)*2)~=0 then nonzero=true break end end
  if nonzero and frame%30==0 and shots<6 then
    shots=shots+1
    out:write(string.format("f=%d rec=%d strip_grp=%d scrollX=%d scrollY=%d\n",
      frame, r16(0xFF013E), r16(0xFF10CC), r16(0xFF409A), r16(0xFF409E)))
    out:write(string.format("   0x1000[0]=%06X 0x1040[0]=%06X 0x1000[5]=%06X 0x1040[5]=%06X\n",
      r32(0xFF1000)&0xFFFFFF, r32(0xFF1040)&0xFFFFFF, r32(0xFF1000+20)&0xFFFFFF, r32(0xFF1040+20)&0xFFFFFF))
    out:write("   staged row20 c28..47: ")
    for c=28,47 do out:write(string.format("%04X ", r16(0xFF50A0+(20*64+c)*2))) end
    out:write("\n"); out:flush()
  end
  if shots>=6 or frame>=1400 then mac:exit() end
end)
