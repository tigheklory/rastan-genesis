-- GENESIS NTSC live CRAM probe (TOOLING). Coins/starts via the established input method, reaches steady
-- R1/P1 gameplay, and dumps staged_palette_words (0xFF60E4, 4 lines x 16 words = committed CRAM shadow)
-- at several steady frames. Output dir from GEN_CRAM_OUT.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")
local out = os.getenv("GEN_CRAM_OUT") or "."
local BASE = 0x00FF60E4          -- staged_palette_words (from apps/rastan-direct/out/symbol.txt)

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end
local function dump(path)
  local f = assert(io.open(path, "wb"))
  for a = BASE, BASE + 0x7E, 2 do
    local w = program:read_u16(a) & 0xffff
    f:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  f:close()
end

local frame = 0
_G._gen_cram_probe = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  if frame == 420 then dump(out .. "/cram_f420.bin") end
  if frame == 600 then dump(out .. "/cram_f600.bin") end
  if frame == 800 then
    dump(out .. "/cram_f800.bin")
    emu.print_info("GENESIS CRAM PROBE dumped frames 420/600/800 -> " .. out)
    machine:exit()
  end
end)
