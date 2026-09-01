-- GENESIS VRAM/CRAM dumper (TOOLING). From a loaded save state, dumps the full 64KB VDP VRAM (tile pixels
-- + plane nametables) and the staged CRAM shadow, so the actual on-screen cave can be rendered offline and
-- compared to the Palette Composer reference. Output dir from GEN_DUMP_OUT.
local machine = manager.machine
local vdp = assert(machine.devices[":gen_vdp"], "missing :gen_vdp")
local vram = assert(vdp.spaces["videoram"], "missing videoram space")
local cpu = assert(machine.devices[":maincpu"])
local prog = assert(cpu.spaces["program"])
local out = os.getenv("GEN_DUMP_OUT") or "."

local frame = 0
_G._vramdump = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if frame ~= 8 then return end
  local f = assert(io.open(out .. "/vram.bin", "wb"))
  for a = 0, 0xFFFF do f:write(string.char(vram:read_u8(a) & 0xff)) end
  f:close()
  local c = assert(io.open(out .. "/cram_shadow.bin", "wb"))
  for i = 0, 63 do local w = prog:read_u16(0x00FF60E4 + i*2) & 0xffff; c:write(string.char((w>>8)&0xff, w&0xff)) end
  c:close()
  local m = assert(io.open(out .. "/regs.txt", "w"))
  m:write(string.format("scroll_x_fg=%d\nscroll_y_fg=%d\nplane_a_base=0xE000\n",
    prog:read_u16(0x00FF40DE) & 0xffff, prog:read_u16(0x00FF40E2) & 0xffff))
  m:close()
  emu.print_info("GENESIS VRAM dumped -> " .. out)
  machine:exit()
end)
