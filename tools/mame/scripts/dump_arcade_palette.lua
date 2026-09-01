-- ORIGINAL ARCADE rastan state dumper (TOOLING). Boots from a loaded save state (-state quick), settles,
-- then dumps arcade palette RAM (0x200000) and a few a5 workram scroll/segment words for offline decode.
-- Output dir from ARC_DUMP_OUT.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local prog = assert(cpu.spaces["program"], "missing program space")
local out = os.getenv("ARC_DUMP_OUT") or "."

local function dump(path)
  local f = assert(io.open(path, "wb"))
  for a = 0x200000, 0x2003FF, 2 do            -- 32 banks x 16 words, big-endian xBGR-555
    local w = prog:read_u16(a) & 0xffff
    f:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  f:close()
end

-- Load the save state AFTER machine init (boot-time -state load segfaults the rastan driver headless).
local frame = 0
_G._arc_dump = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if frame == 3 then
    pcall(function() machine:load(os.getenv("ARC_STATE") or "quick") end)
  end
  if frame == 16 then
    dump(out .. "/palram.bin")   -- 512 words = 32 banks x 16
    local a5 = (cpu.state["A5"] and (cpu.state["A5"].value & 0xffffff)) or 0
    local m = assert(io.open(out .. "/arc_state.txt", "w"))
    m:write(string.format("A5=0x%06X\n", a5))
    if a5 ~= 0 then
      m:write(string.format("seg_a5_13E=%d\n", prog:read_u16(a5 + 0x13E) & 0xffff))
      m:write(string.format("scroll_fg_10B0=%d\n", prog:read_u16(a5 + 0x10B0) & 0xffff))
      m:write(string.format("scroll_bg_10EE=%d\n", prog:read_u16(a5 + 0x10EE) & 0xffff))
    end
    m:close()
    emu.print_info("ARCADE PAL dumped -> " .. out)
    machine:exit()
  end
end)
