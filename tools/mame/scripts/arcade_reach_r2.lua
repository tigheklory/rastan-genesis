-- Reach a genuine Round 2 (round counter 0x10C118==2) via invincibility + repeatedly completing the
-- current subround (write the subround-complete flag), then dump palette RAM. Authentic round advance.
local m=manager.machine; local prog=m.devices[":maincpu"].spaces["program"]
local td=assert(os.getenv("TRACE_DIR"))
local ca=emu.plugin and emu.plugin.cheat
if ca then for i,d in pairs(ca.list()) do if d=="Invincibility" then local c=ca.get(i); if c then c.set_enabled(true) end end end end
local fields={}; for _,p in pairs(m.ioport.ports) do for n,f in pairs(p.fields) do fields[n]=f end end
local function si(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local frame=0; local dumped=false; local lastforce=0
emu.register_frame_done(function() frame=frame+1
 si("Coin 1",frame>=400 and frame<=412); si("1 Player Start",frame>=455 and frame<=467); si("P1 Right",frame>=600)
 local round=prog:read_u16(0x10C118)&0xffff
 -- once in gameplay, force subround completion periodically to advance toward R2
 if frame>=900 and (frame-lastforce)>=180 and round<2 then
   prog:write_u8(0x10D243,0x89)  -- finish-current-subround marker (from the MAME cheat)
   lastforce=frame
 end
 if not dumped and round==2 then
   dumped=true
   local o=assert(io.open(td.."/palram.tsv","w"))
   o:write(string.format("round=%d stage=0x%04X frame=%d\n",round,prog:read_u16(0x10D242),frame))
   for bank=0,15 do local ws={}; for i=0,15 do ws[#ws+1]=string.format("%04X",prog:read_u16(0x200000+bank*32+i*2)&0xffff) end
     o:write(string.format("bank 0x%03X: %s\n",bank,table.concat(ws," "))) end
   o:close(); m:exit()
 end
 if frame>=6000 then local o=io.open(td.."/palram.tsv","w"); o:write(string.format("round never reached 2 (last=%d)\n",round)); o:close(); m:exit() end
end)
