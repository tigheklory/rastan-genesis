-- ORIGINAL ARCADE rastan: sample segment (a5@0x13E) + tilemap0 idx (a5@0x1386) to
-- detect whether attract reaches a CAVE segment (tm0 idx 56..111, attr 0x0003).
local A5=0x0010C000
local SEG=A5+0x13E      -- 0x0010C13E segment index a5@0x13E
local TM0=A5+0x1386     -- 0x0010D386 tilemap0 sub-index a5@0x1386
local frame=0; local cpu,prog
local seg_hist={}; local tm0_max=0; local tm0_min=0xFFFF; local cave_frames=0; local seq={}; local lastseg=-1
local function root() return os.getenv("GENESISTAN_ROOT") or "." end
local function body()
  frame=frame+1; if not cpu or not prog then return end
  local seg=prog:read_u16(SEG)&0xFFFF; local tm0=prog:read_u16(TM0)&0xFFFF
  seg_hist[seg]=(seg_hist[seg] or 0)+1
  if tm0>tm0_max then tm0_max=tm0 end; if tm0<tm0_min then tm0_min=tm0 end
  if tm0>=56 and tm0<=111 then cave_frames=cave_frames+1 end
  if seg~=lastseg then if #seq<200 then seq[#seq+1]=string.format("f%06d seg=%d tm0=%d",frame,seg,tm0) end; lastseg=seg end
end
_G.cs_reset=emu.add_machine_reset_notifier(function() cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end end)
_G.cs_frame=emu.add_machine_frame_notifier(function() local ok=pcall(body) end)
_G.cs_stop=emu.add_machine_stop_notifier(function()
  local d=root().."/build/mame/home/cave_reach"; os.execute("mkdir -p '"..d.."'")
  local fh=io.open(d.."/summary.txt","w")
  fh:write(string.format("frames=%d tm0_min=%d tm0_max=%d cave_frames(tm0 56..111)=%d\n",frame,tm0_min,tm0_max,cave_frames))
  fh:write("CAVE_REACHED="..((cave_frames>0) and "YES" or "NO").."\n\n== segment transitions ==\n")
  for _,s in ipairs(seq) do fh:write(s.."\n") end
  fh:close()
  emu.print_info("cave_reach: cave_frames="..cave_frames.." tm0_max="..tm0_max)
end)
cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end
