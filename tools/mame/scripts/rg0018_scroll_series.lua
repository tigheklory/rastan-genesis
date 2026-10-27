-- Prompt 0018: read-only matched-input Genesis NTSC R1-S1 scroll series.
-- Captures physical VRAM plus retained arcade camera/ring state. No RAM writes.
local m=manager.machine
local p=assert(m.devices[":maincpu"].spaces["program"])
local screen=nil; for _,s in pairs(m.screens) do screen=s; break end
assert(screen)
local out=assert(os.getenv("TRACE_DIR"))
local fields={}; for _,port in pairs(m.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function key(n,on) if fields[n] then fields[n]:set_value(on and 1 or 0) end end
local function r16(a) return p:read_u16(a)&0xffff end
local function r32(a) return p:read_u32(a)&0xffffffff end
local function vdp_read_cmd(a,c)
  p:write_u16(0xc00004,(a&0x3fff)|((c&3)<<14))
  p:write_u16(0xc00004,((a>>14)&3)|((c&0x3c)<<2))
end
local function capture(frame,appeared,offset)
  local tag=string.format("%04d",offset)
  screen:snapshot(out.."/frame_"..tag..".png")
  p:write_u16(0xc00004,0x8f02); vdp_read_cmd(0,0)
  local f=assert(io.open(out.."/vram_"..tag..".bin","wb"))
  for _=0,0x7fff do local w=r16(0xc00000); f:write(string.char((w>>8)&255,w&255)) end
  f:close()
  local s=assert(io.open(out.."/state_"..tag..".tsv","w"))
  s:write("frame\tappeared\toffset\tstage\trecord\tselector\tfg_x\tfg_y\tbg_x\tbg_y\tstrip\tgroup\tplayer_x\tplayer_y\tactive_record\tactive_package\tpalette_asset\tsrc0\tsrc1\tsrc2\tsrc3\n")
  s:write(string.format("%d\t%d\t%d\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%08X\t%08X\t%08X\t%08X\n",
    frame,appeared,offset,r16(0xff1242),r16(0xff013e),r16(0xff10a8),
    r16(0xff10ae),r16(0xff10b0),r16(0xff10b2),r16(0xff10b4),
    r16(0xff10ca),r16(0xff10cc),r16(0xff10e4),r16(0xff10e6),
    r16(0xffb2b8),r16(0xffb2bc),r16(0xff400c),r32(0xff1000),r32(0xff1004),r32(0xff1008),r32(0xff100c)))
  s:close()
end
local wanted={}
for offset=0,120,10 do wanted[offset]=true end
for _,offset in ipairs({240,360,480,600,720,840}) do wanted[offset]=true end
local frame,appeared=0,nil
emu.register_frame_done(function()
  frame=frame+1
  key("Coin 1",frame>=120 and frame<=132); key("P1 A",frame>=120 and frame<=132)
  key("1 Player Start",frame>=175 and frame<=187); key("P1 Start",frame>=175 and frame<=187)
  if not appeared and r16(0xff0000)==2 and r16(0xff0002)==3 then appeared=frame end
  if appeared then
    local off=frame-appeared
    key("P1 Right",true)
    key("P1 B",(off%45)<8)
    key("P1 C",(off%100)>=55 and (off%100)<68)
    if wanted[off] then capture(frame,appeared,off) end
    if off>=840 then m:exit() end
  elseif frame>=1800 then m:exit() end
end)
