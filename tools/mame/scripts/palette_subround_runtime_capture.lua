-- Prompt 0014: Genesis-NTSC runtime proof for one direct-start subround.
-- Reuses the established coin/start cadence and terminal VDP-port read method.
local m=manager.machine
local p=assert(m.devices[":maincpu"].spaces["program"])
local screen=nil; for _,candidate in pairs(m.screens) do screen=candidate; break end
assert(screen)
local out=assert(os.getenv("TRACE_DIR"))
local expect=tonumber(assert(os.getenv("EXPECT_STAGE")))
local staged=tonumber(assert(os.getenv("STAGED_PALETTE_ADDR")))
local active_record=tonumber(assert(os.getenv("ACTIVE_RECORD_ADDR")))
local active_package=tonumber(assert(os.getenv("ACTIVE_PACKAGE_ADDR")))
local fields={}; for _,port in pairs(m.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function key(n,on) if fields[n] then fields[n]:set_value(on and 1 or 0) end end
local function r16(a) return p:read_u16(a)&0xffff end
local function dump_words(path, words)
  local f=assert(io.open(path,"wb")); for _,w in ipairs(words) do
    f:write(string.char((w>>8)&255,w&255))
  end; f:close()
end
local function vdp_read_cmd(a,c)
  p:write_u16(0xc00004,(a&0x3fff)|((c&3)<<14))
  p:write_u16(0xc00004,((a>>14)&3)|((c&0x3c)<<2))
end
local function capture(frame,appeared)
  screen:snapshot(out.."/frame.png")
  local sw={}; for i=0,63 do sw[#sw+1]=r16(staged+i*2) end
  dump_words(out.."/staged_cram.bin",sw)
  vdp_read_cmd(0,8); local cw={}; for _=0,63 do cw[#cw+1]=r16(0xc00000) end
  dump_words(out.."/actual_cram.bin",cw)
  p:write_u16(0xc00004,0x8f02); vdp_read_cmd(0,0)
  local vf=assert(io.open(out.."/actual_vram.bin","wb")); for _=0,0x7fff do
    local w=r16(0xc00000); vf:write(string.char((w>>8)&255,w&255))
  end; vf:close()
  local meta=assert(io.open(out.."/runtime.tsv","w"))
  meta:write("frame\tappeared\texpect_stage\tstage\trecord_cursor\tactive_record\tactive_package\tscene\tplayer_state\n")
  meta:write(string.format("%d\t%d\t%04X\t%04X\t%04X\t%04X\t%04X\t%02X\t%04X\n",
    frame,appeared,expect,r16(0xff1242),r16(0xff013e),r16(active_record),
    r16(active_package),p:read_u8(0xffc640)&255,r16(0xff10e8)))
  meta:close(); m:exit()
end
local frame,appeared=0,nil
emu.register_frame_done(function()
  frame=frame+1
  key("Coin 1",frame>=120 and frame<=132); key("P1 A",frame>=120 and frame<=132)
  key("1 Player Start",frame>=175 and frame<=187); key("P1 Start",frame>=175 and frame<=187)
  if not appeared and r16(0xff0000)==2 and r16(0xff0002)==3 then appeared=frame end
  if appeared then key("P1 Right",true) end
  if appeared and frame>=appeared+120 then capture(frame,appeared)
  elseif frame>=1600 then capture(frame,appeared or -1) end
end)
