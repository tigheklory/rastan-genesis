-- Diagnostic: confirm A5 base + detect cave via the LIVE tilemap0 descriptor.
-- a5@0x10FC = descriptor base (0x3951C + tm0*0xC). Descriptor attr word 0x0003 = cave.
local frame=0; local cpu,prog
local a5seen={}; local attr_hist={}; local cave_first=-1; local cave_frames=0
local seg_seen={}; local tm0_seen={}; local samples={}; local last_attr=-1; local seq={}
local function root() return os.getenv("GENESISTAN_ROOT") or "." end
local function body()
  frame=frame+1; if not cpu or not prog then return end
  local a5=0
  if cpu.state["A5"] then a5=cpu.state["A5"].value & 0xFFFFFF end
  a5seen[a5]=(a5seen[a5] or 0)+1
  if a5<0x100000 or a5>0x110000 then return end     -- only sample when A5 is the work-RAM base
  local seg=prog:read_u16(a5+0x13E)&0xFFFF
  local tm0=prog:read_u16(a5+0x1386)&0xFFFF
  local descbase=prog:read_u32(a5+0x10FC)&0xFFFFFF
  local attr=0
  if descbase>=0x39000 and descbase<0x3A000 then attr=prog:read_u16(descbase)&0xFFFF end
  seg_seen[seg]=(seg_seen[seg] or 0)+1
  tm0_seen[tm0]=true
  attr_hist[attr]=(attr_hist[attr] or 0)+1
  if attr==0x0003 then
    cave_frames=cave_frames+1
    if cave_first<0 then cave_first=frame end
    if #samples<40 then samples[#samples+1]=string.format("f%06d CAVE a5=0x%06x seg=%d tm0=%d descbase=0x%06x attr=0x%04x",frame,a5,seg,tm0,descbase,attr) end
  end
  if attr~=last_attr then if #seq<200 then seq[#seq+1]=string.format("f%06d attr 0x%04x->0x%04x seg=%d tm0=%d descbase=0x%06x",frame,last_attr&0xFFFF,attr,seg,tm0,descbase) end; last_attr=attr end
end
_G.cd_reset=emu.add_machine_reset_notifier(function() cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end end)
_G.cd_frame=emu.add_machine_frame_notifier(function() local ok,e=pcall(body); if not ok then emu.print_error(tostring(e)) end end)
_G.cd_stop=emu.add_machine_stop_notifier(function()
  local d=root().."/build/mame/home/cave_diag"; os.execute("mkdir -p '"..d.."'")
  local fh=io.open(d.."/summary.txt","w")
  fh:write(string.format("frames=%d cave_first=%d cave_frames=%d\n",frame,cave_first,cave_frames))
  fh:write("A5 values seen (top): "); local ak={} for k in pairs(a5seen) do ak[#ak+1]=k end table.sort(ak,function(a,b) return a5seen[a]>a5seen[b] end)
  for i=1,math.min(4,#ak) do fh:write(string.format("0x%06x(%d) ",ak[i],a5seen[ak[i]])) end fh:write("\n")
  fh:write("attr histogram: "); for k,v in pairs(attr_hist) do fh:write(string.format("0x%04x=%d ",k,v)) end fh:write("\n")
  fh:write("tm0 values seen: "); local tk={} for k in pairs(tm0_seen) do tk[#tk+1]=k end table.sort(tk) fh:write(table.concat(tk,",").."\n")
  fh:write("CAVE_REACHED="..((cave_frames>0) and "YES" or "NO").."\n\n== attr transitions ==\n"); for _,s in ipairs(seq) do fh:write(s.."\n") end
  fh:write("\n== cave samples ==\n"); for _,s in ipairs(samples) do fh:write(s.."\n") end
  fh:close(); emu.print_info("cave_diag: cave_frames="..cave_frames)
end)
cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end
