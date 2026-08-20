-- Map each Stage-1 segment (a5@0x13E) to its FG strip-source bases (a5@0x1000..0x103C)
-- + scroll, over the attract demo (which reaches the cave per Tighe). A5=0x10C000.
local A5=0x0010C000
local frame=0; local cpu,prog; local seen={}; local order={}
local function root() return os.getenv("GENESISTAN_ROOT") or "." end
local function body()
  frame=frame+1; if not cpu or not prog then return end
  local a5=cpu.state["A5"] and (cpu.state["A5"].value&0xFFFFFF) or 0
  if a5~=0x10C000 then return end
  local seg=prog:read_u16(A5+0x13E)&0xFFFF
  if not seen[seg] then
    seen[seg]=frame
    local bases={}
    for i=0,15 do bases[#bases+1]=string.format("0x%06x",prog:read_u32(A5+0x1000+i*4)&0xFFFFFF) end
    order[#order+1]=string.format("seg=%2d first_frame=%06d fgx=%d fgy=%d tm0=%d | strip0..3=%s %s %s %s | strip8..11=%s %s %s %s",
      seg,frame,prog:read_u16(A5+0x10AE)&0xFFFF,prog:read_u16(A5+0x10B0)&0xFFFF,prog:read_u16(A5+0x1386)&0xFFFF,
      bases[1],bases[2],bases[3],bases[4],bases[9],bases[10],bases[11],bases[12])
  end
end
_G.ss_reset=emu.add_machine_reset_notifier(function() cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end end)
_G.ss_frame=emu.add_machine_frame_notifier(function() pcall(body) end)
_G.ss_stop=emu.add_machine_stop_notifier(function()
  local d=root().."/build/mame/home/seg_src_map"; os.execute("mkdir -p '"..d.."'")
  local fh=io.open(d.."/summary.txt","w")
  fh:write(string.format("frames=%d distinct_segments=%d\n\n",frame,#order))
  for _,s in ipairs(order) do fh:write(s.."\n") end
  fh:close(); emu.print_info("seg_src_map: segments="..#order)
end)
cpu=manager.machine.devices[":maincpu"]; if cpu then prog=cpu.spaces["program"] end
