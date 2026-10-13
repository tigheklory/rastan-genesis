-- Build 0417 / 0417_do A-0154 scanout-time forensic (read-only).
--
-- Natural Round-1 play to record 2.  Reconstructs VDP VRAM from the real
-- control/data-port traffic, timestamps writes at the beam position, captures
-- the rendered frame before terminal reads, then dumps real VRAM/CRAM/VSRAM.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local screen = assert(m.screens:at(1))
local outdir = assert(os.getenv("A0154_SCANOUT_OUTDIR"))
local label = os.getenv("A0154_SCANOUT_LABEL") or "unknown"
os.execute('mkdir -p "' .. outdir .. '"')

local A5 = 0x00ff0000
local A_RECORD, A_PLAYER_X, A_PLAYER_Y, A_PLAYER_STATE = A5+0x013e, A5+0x10be, A5+0x10c0, A5+0x10e8
local A_BG_X, A_FG_X, A_BG_Y, A_FG_Y = 0x00ff4098,0x00ff409a,0x00ff409c,0x00ff409e
local A_STAGE, A_PACKAGE, A_LUT = 0x00ff50a0,0x00ffb230,0x00ff6288
local A_VC = 0x00ff61e4
local ACTUAL_SLOT, CONTROL_SLOT = 0x03a4, 0x0468
local ACTUAL_LO, ACTUAL_HI = ACTUAL_SLOT*32, ACTUAL_SLOT*32+31
local CONTROL_LO, CONTROL_HI = CONTROL_SLOT*32, CONTROL_SLOT*32+31
local occ = {
  {44,30,"LA-0543"},{48,30,"LA-0092"},{44,34,"LA-0543"},
  {52,34,"LA-0092"},{40,38,"LA-0092"},{44,38,"LA-0543"},
}
for _,o in ipairs(occ) do
  o.row=o[2]&31; o.stage=A_STAGE+2*(o.row*64+o[1]); o.name=0xe000+2*(o.row*64+o[1])
end

local function r8(a) return p:read_u8(a)&0xff end
local function r16(a) return p:read_u16(a)&0xffff end
local function pc() local s=cpu.state["CURPC"] or cpu.state["PC"]; return s and s.value&0xffffff or 0 end
local function beam()
  -- YM7101 HV counter: V in the high byte, coarse H in the low byte.  This is
  -- the same hardware observation used by the ROM's existing vblank_vc audit.
  local hv=p:read_u16(0x00c00008)&0xffff
  return (hv>>8)&0xff,hv&0xff
end
local function hexbytes(t,lo,hi)
  local a={}; for i=lo,hi do a[#a+1]=string.format("%02x",t[i] or 0) end; return table.concat(a)
end
local function overlap(a,n,lo,hi)
  for i=0,n-1 do local q=(a+i)&0xffff; if q>=lo and q<=hi then return true end end
  return false
end

local events=assert(io.open(outdir.."/vdp_events.tsv","w"))
events:write("label\tframe\tvpos\thpos\tpc\tevent\tdest\tbytes\tsource\told\tnew\tdetail\n")
local frames=assert(io.open(outdir.."/frame_state.tsv","w"))
frames:write("label\tframe\trecord\tpackage\tfg_x\tfg_y\tbg_x\tbg_y\tplayer_x\tplayer_y\tplayer_state\tlut_0117\tvc0\tvc1\tvc2\tvc3\tvc4\tvc5\tvc6\n")
local frame=-1
local vram={}; for i=0,0xffff do vram[i]=0 end
local autoinc,addr,code,pending=2,0,0,nil
local dl,dh,sl,sm,sh=0,0,0,0,0
local taps={}
local pending_dma=nil

local function all_trace_enabled()
  local rec=r16(A_RECORD)
  return frame>=1300 and (rec==2 or rec==3)
end

local function event(kind,dest,n,source,old,new,detail)
  local y,x=beam()
  detail=string.format("fg=%04X,%04X bg=%04X,%04X %s",r16(A_FG_X),r16(A_FG_Y),r16(A_BG_X),r16(A_BG_Y),detail or "")
  events:write(string.format("%s\t%d\t%d\t%d\t%06X\t%s\t%04X\t%d\t%06X\t%s\t%s\t%s\n",
    label,frame,y,x,pc(),kind,dest or 0,n or 0,source or 0,old or "",new or "",detail)); events:flush()
end
local function close_pending_dma(reason)
  if not pending_dma then return end
  local y,x=beam()
  if all_trace_enabled() then
    event("DMA_END_BOUND",pending_dma.dest,pending_dma.bytes,pending_dma.source,"","",
      string.format("type=%s start=%d,%d end=%d,%d reason=%s",
        pending_dma.kind,pending_dma.v,pending_dma.h,y,x,reason or "next_vdp_access"))
  end
  pending_dma=nil
end
local function relevant(a,n)
  if overlap(a,n,ACTUAL_LO,ACTUAL_HI) or overlap(a,n,CONTROL_LO,CONTROL_HI) then return true end
  for _,o in ipairs(occ) do if overlap(a,n,o.name,o.name+1) then return true end end
  return a>=0xfc00 and a<0xfc04
end
local function write_bytes(a,bytes,kind,source,detail)
  local old={}; for i=1,#bytes do old[i-1]=vram[(a+i-1)&0xffff] or 0 end
  for i=1,#bytes do vram[(a+i-1)&0xffff]=bytes[i]&0xff end
  local oldword=#bytes==2 and ((old[0]<<8)|old[1]) or 0
  local newword=#bytes==2 and ((bytes[1]<<8)|bytes[2]) or 0
  local target_name=a>=0xe000 and a<0xf000 and #bytes==2 and
    (((oldword&0x07ff)==ACTUAL_SLOT) or ((newword&0x07ff)==ACTUAL_SLOT))
  if all_trace_enabled() or relevant(a,#bytes) or target_name then
    local nt={}; for i=1,#bytes do nt[i-1]=bytes[i]&0xff end
    event(kind,a,#bytes,source,hexbytes(old,0,#bytes-1),hexbytes(nt,0,#bytes-1),detail)
  end
end
local function accept_command(cmd)
  addr=((cmd>>16)&0x3fff)|((cmd&3)<<14)
  code=((cmd>>30)&3)|((cmd>>2)&0x3c)
  if all_trace_enabled() then
    event("VDP_COMMAND",addr,0,0,"","",string.format("command=%08X code=%02X dma=%d autoinc=%d",cmd,code,(cmd&0x80)~=0 and 1 or 0,autoinc))
  end
  if (cmd&0x80)==0 then return end
  local words=(dh<<8)|dl; if words==0 then words=0x10000 end
  local src=(((sh&0x7f)<<16)|(sm<<8)|sl)*2
  local kind=({[1]="VRAM",[3]="CRAM",[5]="VSRAM"})[code&0x0f] or string.format("CODE_%02X",code)
  local sy,sx=beam()
  if all_trace_enabled() then
    event("DMA_START",addr,words*2,src,"","",string.format("type=%s words=%d start=%d,%d source_mode=%02X",kind,words,sy,sx,sh))
  end
  pending_dma={dest=addr,bytes=words*2,source=src,kind=kind,v=sy,h=sx}
  if (code&0x0f)==1 and (sh&0x80)==0 then
    local bytes={}
    for i=0,words-1 do local w=r16((src+i*2)&0xffffff); bytes[#bytes+1]=(w>>8)&0xff; bytes[#bytes+1]=w&0xff end
    local old_actual=hexbytes(vram,ACTUAL_LO,ACTUAL_HI)
    for i=0,words-1 do
      local wa=(addr+i*autoinc)&0xffff
      local w=(bytes[i*2+1]<<8)|bytes[i*2+2]
      local old0,old1=vram[wa] or 0,vram[(wa+1)&0xffff] or 0
      vram[wa]=(w>>8)&0xff; vram[(wa+1)&0xffff]=w&0xff
      if relevant(wa,2) then
        event("DMA_TARGET_WORD",wa,2,src+i*2,string.format("%02x%02x",old0,old1),string.format("%04x",w),string.format("type=%s len_words=%d",kind,words))
      end
    end
    if overlap(addr,math.max(2,(words-1)*autoinc+2),ACTUAL_LO,ACTUAL_HI) then
      event("A0154_DMA_COMPLETE",addr,words*2,src,old_actual,hexbytes(vram,ACTUAL_LO,ACTUAL_HI),string.format("len_words=%d",words))
    end
  end
end
local function ctrl_word(w)
  if (w&0xe000)==0x8000 then
    local reg=(w>>8)&0x1f; local val=w&0xff
    if all_trace_enabled() then event("VDP_REG_WRITE",reg,1,0,"",string.format("%02X",val),string.format("reg=%02X",reg)) end
    if reg==1 then event("VDP_REG1",0,0,0,"","",string.format("value=%02X display=%s",val,(val&0x40)~=0 and "ON" or "OFF"))
    elseif reg==0x0f then autoinc=val
    elseif reg==0x13 then dl=val elseif reg==0x14 then dh=val
    elseif reg==0x15 then sl=val elseif reg==0x16 then sm=val elseif reg==0x17 then sh=val end
    pending=nil
  elseif pending==nil then pending=w else local cmd=(pending<<16)|w; pending=nil; accept_command(cmd) end
end
taps[#taps+1]=p:install_write_tap(0x00c00004,0x00c00007,"a0154_ctrl",function(_,data,mask)
  close_pending_dma("next_control_write")
  mask=mask or 0xffffffff
  if mask==0xffffffff then ctrl_word((data>>16)&0xffff); ctrl_word(data&0xffff)
  else ctrl_word(data&0xffff) end
  return data
end)
taps[#taps+1]=p:install_write_tap(0x00c00000,0x00c00003,"a0154_data",function(_,data,mask)
  close_pending_dma("next_data_write")
  if (code&0x0f)==1 then
    mask=mask or 0xffffffff
    if mask==0xffffffff then
      local hi=(data>>16)&0xffff; write_bytes(addr,{(hi>>8)&0xff,hi&0xff},"PIO",0,""); addr=(addr+autoinc)&0xffff
      local lo=data&0xffff; write_bytes(addr,{(lo>>8)&0xff,lo&0xff},"PIO",0,""); addr=(addr+autoinc)&0xffff
    else local w=data&0xffff; write_bytes(addr,{(w>>8)&0xff,w&0xff},"PIO",0,""); addr=(addr+autoinc)&0xffff end
  elseif all_trace_enabled() then
    mask=mask or 0xffffffff
    local n=(mask==0xffffffff) and 4 or 2
    event("PIO_NONVRAM",addr,n,0,"",string.format("%08X",data&0xffffffff),string.format("code=%02X autoinc=%d",code,autoinc))
  end
  return data
end)
for i,o in ipairs(occ) do
  taps[#taps+1]=p:install_write_tap(o.stage,o.stage+1,"a0154_stage"..i,function(_,data)
    local y,x=beam(); event("STAGE_WORD",o.stage,2,0,string.format("%04X",r16(o.stage)),string.format("%04X",data&0xffff),string.format("occ=%d beam=%d,%d",i,y,x)); return data
  end)
end
taps[#taps+1]=p:install_write_tap(A_LUT+0x117*2,A_LUT+0x117*2+1,"a0154_lut",function(_,data)
  event("LUT_0117",A_LUT+0x117*2,2,0,string.format("%04X",r16(A_LUT+0x117*2)),string.format("%04X",data&0xffff),""); return data
end)
taps[#taps+1]=p:install_write_tap(A_PACKAGE,A_PACKAGE+1,"a0154_package",function(_,data)
  event("PACKAGE",A_PACKAGE,2,0,string.format("%04X",r16(A_PACKAGE)),string.format("%04X",data&0xffff),""); return data
end)
taps[#taps+1]=p:install_write_tap(A_VC,A_VC+7,"a0154_vc",function(off,data)
  event("VC_MARK",off,1,0,"",string.format("%02X",data&0xff),string.format("mark=%d",off-A_VC)); return data
end)
_G.build0417_A0154_scanout_taps=taps

local fields={}; for _,port in pairs(m.ioport.ports) do for name,f in pairs(port.fields) do fields[name]=f end end
local function key(n,on) if fields[n] then fields[n]:set_value(on and 1 or 0) end end
local function vdp_read_cmd(a,c)
  p:write_u16(0xc00004,(a&0x3fff)|((c&3)<<14)); p:write_u16(0xc00004,((a>>14)&3)|((c&0x3c)<<2))
end
local terminal=false
local function terminal_dump()
  terminal=true
  local f=assert(io.open(outdir.."/terminal_actual_vram.bin","wb")); p:write_u16(0xc00004,0x8f02); vdp_read_cmd(0,0)
  for _=0,0x7fff do local w=p:read_u16(0xc00000)&0xffff; f:write(string.char((w>>8)&0xff,w&0xff)) end; f:close()
  f=assert(io.open(outdir.."/terminal_cram.bin","wb")); vdp_read_cmd(0,8)
  for _=0,63 do local w=p:read_u16(0xc00000)&0xffff; f:write(string.char((w>>8)&0xff,w&0xff)) end; f:close()
  f=assert(io.open(outdir.."/terminal_vsram.bin","wb")); vdp_read_cmd(0,4)
  for _=0,39 do local w=p:read_u16(0xc00000)&0xffff; f:write(string.char((w>>8)&0xff,w&0xff)) end; f:close()
  f=assert(io.open(outdir.."/reconstructed_vram.bin","wb")); for i=0,0xffff do f:write(string.char(vram[i] or 0)) end; f:close()
end
local captured=false
local target_snapshots=0
local function capture()
  captured=true
  local sx,sy=r16(A_FG_X),r16(A_FG_Y)
  local f=assert(io.open(outdir.."/capture.tsv","w"))
  f:write("label\tframe\trecord\tpackage\tfg_x\tfg_y\tbg_x\tbg_y\tplayer_x\tplayer_y\tplayer_state\tlut\truntime_occ\tphysical_col\tphysical_row\tscreen_x0\tscreen_y0\tscreen_x1\tscreen_y1\tscanline_first\tscanline_last\tstage_addr\tstage_word\tname_addr\treconstructed_name\n")
  local n=0; local hs=(sx-16)&0x01ff; local vs=(-sy+8)&0x01ff
  for row=0,31 do for col=0,63 do
    local na=0xe000+2*(row*64+col); local nw=((vram[na]or 0)<<8)|(vram[na+1]or 0)
    if (nw&0x07ff)==ACTUAL_SLOT then
      n=n+1; local sa=A_STAGE+2*(row*64+col)
      -- YM7101 scroll values are displacement magnitudes: fetch coordinate is
      -- screen+scroll, hence displayed cell origin is cell-scroll.  MAME's H40
      -- active image has the established two-pixel origin used here.
      local xs=(col*8-hs+2)&0x01ff; local ys=(row*8-vs)&0x00ff
      f:write(string.format("%s\t%d\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%06X\t%04X\t%04X\t%04X\n",
        label,frame,r16(A_RECORD),r16(A_PACKAGE),sx,sy,r16(A_BG_X),r16(A_BG_Y),r16(A_PLAYER_X),r16(A_PLAYER_Y),r16(A_PLAYER_STATE),r16(A_LUT+0x117*2),n,col,row,xs,ys,xs+7,ys+7,ys,ys+7,sa,r16(sa),na,nw))
    end
  end end
  f:close()
  screen:snapshot(outdir.."/actual_frame.png")
  terminal_dump(); events:close(); frames:close(); m:exit()
end

emu.register_frame_done(function()
  if terminal then return end
  frame=frame+1
  key("Coin 1",frame>=120 and frame<=132); key("P1 A",frame>=120 and frame<=132)
  key("1 Player Start",frame>=175 and frame<=187); key("P1 Start",frame>=175 and frame<=187)
  local rec=r16(A_RECORD)
  key("P1 Right",frame>=360)
  key("P1 B",frame>=500 and frame%70<10)
  key("P1 C",frame>=520 and frame%45<8)
  -- The owner frame is the upper rope view.  Once record 2 is reached, hold
  -- UP while the established right/jump route contacts and climbs the rope.
  key("P1 Up",rec==2 or rec==3)
  if frame%30==0 then frames:write(string.format("%s\t%d\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\n",
    label,frame,r16(A_RECORD),r16(A_PACKAGE),r16(A_FG_X),r16(A_FG_Y),r16(A_BG_X),r16(A_BG_Y),r16(A_PLAYER_X),r16(A_PLAYER_Y),r16(A_PLAYER_STATE),r16(A_LUT+0x117*2),r8(A_VC),r8(A_VC+1),r8(A_VC+2),r8(A_VC+3),r8(A_VC+4),r8(A_VC+5),r8(A_VC+6))); frames:flush() end
  if r16(A_RECORD)==3 and r16(A_LUT+0x117*2)==ACTUAL_SLOT then
    local sx=r16(A_FG_X)
    if sx>=0x0100 and sx<=0x0128 and target_snapshots<40 then
      target_snapshots=target_snapshots+1
      screen:snapshot(string.format("%s/target_%02d_f%04d_x%04X.png",outdir,target_snapshots,frame,sx))
    end
    if not captured and sx>=0x0100 and sx<=0x0104 then capture() end
  end
  if frame>5000 then event("TARGET_NOT_REACHED",0,0,0,"","",""); events:close(); frames:close(); m:exit() end
end)

print(string.format("[A0154 scanout] %s -> %s",label,outdir))
