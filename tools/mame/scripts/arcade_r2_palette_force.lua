local m=manager.machine; local prog=m.devices[":maincpu"].spaces["program"]; local region=m.memory.regions[":maincpu"]
local td=assert(os.getenv("TRACE_DIR"))
local fields={}; for _,p in pairs(m.ioport.ports) do for n,f in pairs(p.fields) do fields[n]=f end end
local function si(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
if region then region:write_u8(0x5FF9F,0xFE) end  -- R2 outside stage
local frame=0; local done=false
emu.register_frame_done(function() frame=frame+1
 if region then region:write_u8(0x5FF9F,0xFE) end
 if frame>=700 then prog:write_u16(0x10C118,2) end  -- force round 2 after start, before stage palette load
 si("Coin 1",frame>=600 and frame<=612); si("1 Player Start",frame>=655 and frame<=667); si("P1 Right",frame>=800)
 local s2=prog:read_u16(0x10C002)&0xffff; local ps=prog:read_u16(0x10D0E8)&0xffff
 if not done and prog:read_u16(0x10C000)==2 and s2==3 and ps>=1 and ps<=3 then
   done=true
   local o=assert(io.open(td.."/palram.tsv","w"))
   o:write(string.format("round=%d stage=0x%04X frame=%d\n",prog:read_u16(0x10C118),prog:read_u16(0x10D242),frame))
   for bank=0,15 do
     local ws={}; for i=0,15 do ws[#ws+1]=string.format("%04X",prog:read_u16(0x200000+bank*32+i*2)&0xffff) end
     o:write(string.format("bank 0x%03X: %s\n",bank,table.concat(ws," ")))
   end
   o:close(); m:exit()
 end
 if frame>=3000 then local o=io.open(td.."/palram.tsv","w"); o:write("NO APPEARANCE\n"); o:close(); m:exit() end
end)
