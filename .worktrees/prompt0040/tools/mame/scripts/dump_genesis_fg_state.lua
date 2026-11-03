-- GENESIS NTSC state dumper (TOOLING). Boots from a loaded save state (-state quick), lets it settle a
-- few frames, then dumps the native FG producer's staged output for offline decode:
--   staged_fg_buffer   (0xFF50E4, 2048 words = 64x32 Plane-A nametable)
--   staged_palette_words(0xFF60E4, 64 words = 4 CRAM lines x 16)
--   staged_scroll_x_fg (0xFF40DE) / staged_scroll_y_fg (0xFF40E2)
-- Output dir from GEN_DUMP_OUT. Raw little/big-endian words written as big-endian bytes; Python decodes.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local prog = assert(cpu.spaces["program"], "missing program space")
local out = os.getenv("GEN_DUMP_OUT") or "."

local function dump_words(path, base, nwords)
  local f = assert(io.open(path, "wb"))
  for i = 0, nwords - 1 do
    local w = prog:read_u16(base + i * 2) & 0xffff
    f:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  f:close()
end

local frame = 0
_G._gen_dump = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if frame == 8 then
    dump_words(out .. "/fg_buffer.bin", 0x00FF50E4, 2048)
    dump_words(out .. "/cram.bin", 0x00FF60E4, 64)
    local sx = prog:read_u16(0x00FF40DE) & 0xffff
    local sy = prog:read_u16(0x00FF40E2) & 0xffff
    local m = assert(io.open(out .. "/scroll.txt", "w"))
    m:write(string.format("scroll_x_fg=%d\nscroll_y_fg=%d\n", sx, sy))
    m:close()
    emu.print_info("GENESIS FG STATE dumped -> " .. out)
    machine:exit()
  end
end)
