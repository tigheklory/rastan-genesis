-- ORIGINAL ARCADE rastan: coin+start, then walk RIGHT (with jumps/attacks) to reach
-- the Stage-1 CAVE (tm0 idx a5@0x1386 in 56..111), sampling the arcade FG map state.
local A5=0x0010C000
local SEG=A5+0x13E; local TM0=A5+0x1386; local SEL=A5+0x10A8
local GRP=A5+0x10CC; local STR=A5+0x10CA; local FGX=A5+0x10AE; local FGY=A5+0x10B0
local C6=A5+0x10C6
local frame=0; local cpu,prog
local F={}          -- input fields
local tm0_max=0; local seg_max=0; local cave_first=-1; local cave_frames=0
local seq={}; local lastseg=-1; local cave_samples={}
local function root() return os.getenv("GENESISTAN_ROOT") or "." end
local function u16(a) return prog:read_u16(a)&0xFFFF end
local function findfields()
  for tag,port in pairs(manager.machine.ioport.ports) do
    for fname,field in pairs(port.fields) do
      if fname=="Coin 1" then F.coin=field
      elseif fname=="1 Player Start" then F.start=field
      elseif fname=="P1 Right" then F.right=field
      elseif fname=="P1 Button 1" then F.b1=field
      elseif fname=="P1 Button 2" then F.b2=field end
    end
  end
end
local function press(f,v) if f then f:set_value(v) end end
local function body()
  frame=frame+1; if not cpu or not prog then return end
  -- input schedule
  press(F.coin, (frame>=60 and frame<=66) and 1 or 0)
  press(F.start,(frame>=120 and frame<=126) and 1 or 0)
  if frame>=180 then
    press(F.right,1)                                   -- hold right
    press(F.b1, (frame%48<8) and 1 or 0)               -- jump pulses (clear gaps)
    press(F.b2, (frame%26<4) and 1 or 0)               -- attack pulses (kill enemies)
  end
  -- sample
  local seg=u16(SEG); local tm0=u16(TM0)
  if tm0>tm0_max then tm0_max=tm0 end
  if seg>seg_max then seg_max=seg end
  if tm0>=56 and tm0<=111 then
    cave_frames=cave_frames+1
    if cave_first<0 then cave_first=frame end
    if #cave_samples<60 then
      cave_samples[#cave_samples+1]=string.format(
        "f%06d CAVE seg=%d tm0=%d sel=%d grp=%d str=%d fgx=%d fgy=%d c6=0x%06x",
        frame,seg,tm0,u16(SEL),u16(GRP),u16(STR),u16(FGX),u16(FGY),prog:read_u32(C6)&0xFFFFFF)
    end
  end
  if seg~=lastseg then if #seq<300 then seq[#seq+1]=string.format("f%06d seg=%d tm0=%d",frame,seg,tm0) end; lastseg=seg end
end
_G.cw_reset=emu.add_machine_reset_notifier(function() cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end; findfields() end)
_G.cw_frame=emu.add_machine_frame_notifier(function() local ok,e=pcall(body); if not ok then emu.print_error(tostring(e)) end end)
_G.cw_stop=emu.add_machine_stop_notifier(function()
  local d=root().."/build/mame/home/cave_walk"; os.execute("mkdir -p '"..d.."'")
  local fh=io.open(d.."/summary.txt","w")
  fh:write(string.format("frames=%d seg_max=%d tm0_max=%d cave_first_frame=%d cave_frames=%d\n",frame,seg_max,tm0_max,cave_first,cave_frames))
  fh:write("CAVE_REACHED="..((cave_frames>0) and "YES" or "NO").."\n")
  fh:write("fields: coin="..tostring(F.coin~=nil).." start="..tostring(F.start~=nil).." right="..tostring(F.right~=nil).."\n")
  fh:write("\n== segment transitions ==\n"); for _,s in ipairs(seq) do fh:write(s.."\n") end
  fh:write("\n== cave-region samples ==\n"); for _,s in ipairs(cave_samples) do fh:write(s.."\n") end
  fh:close(); emu.print_info("cave_walk: tm0_max="..tm0_max.." cave_frames="..cave_frames)
end)
cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end; findfields()
