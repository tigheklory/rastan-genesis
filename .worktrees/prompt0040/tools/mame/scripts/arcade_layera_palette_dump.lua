-- ORIGINAL ARCADE (rastan) Layer-A palette-RAM capture (TOOLING ONLY).
-- Coins up + starts using the established input method, reaches R1/P1 gameplay, and dumps arcade
-- palette RAM 0x200000..0x2003FF (banks 0..31, 512 words) at two gameplay frames to confirm stability.
-- Output dir from LAYERA_PAL_OUT. Authoritative source of the true displayed Layer-A palette contents.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")
local out = os.getenv("LAYERA_PAL_OUT") or "."

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local function dump_palette(path)
  local f = assert(io.open(path, "wb"))
  for a = 0x200000, 0x2003FF, 2 do          -- banks 0..31 x 16 words, big-endian xBGR-555
    local w = program:read_u16(a) & 0xffff
    f:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  f:close()
end

local frame = 0
_G._layera_pal_notifier = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  if frame == 360 then dump_palette(out .. "/palette_ram_f360.bin") end
  if frame == 460 then dump_palette(out .. "/palette_ram_f460.bin") end
  if frame == 700 then dump_palette(out .. "/palette_ram_f700.bin") end
  if frame == 1000 then
    dump_palette(out .. "/palette_ram_f1000.bin")
    emu.print_info("LAYERA PALETTE CAPTURED frames 360/460/700/1000 -> " .. out)
    machine:exit()
  end
end)
