-- GENESIS staged_palette_words write-provenance tracer (TOOLING, non-shipping).
-- Taps every write into staged_palette_words (0xFF60E4, 64 words) and logs frame, writer PC,
-- target line (0..3), entry, and value. Drives coin/start + walk-right to reach R1/P1 gameplay
-- so we can see WHICH producer PC loads/animates each CRAM line (esp. Line 2 / Layer B).
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")
local state = cpu.state
local out = os.getenv("GEN_PW_OUT") or "."
local STAGED = 0x00FF60E4
local SCENE = 0x00FFC0AC
local RUN_FRAMES = tonumber(os.getenv("GEN_PW_FRAMES") or "2000")

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local csv = assert(io.open(out .. "/staged_palette_writers.csv", "w"))
csv:write("frame,pc,line,entry,value\n")
local frame = 0
local logged = 0
local LOG_CAP = 4000

local tap = program:install_write_tap(STAGED, STAGED + 0x7F, "pw", function(offset, data, mask)
  if program:read_u8(SCENE) ~= 1 then return end        -- gameplay only
  if logged >= LOG_CAP then return end
  local rel = offset - STAGED
  local line = rel >> 5
  local entry = (rel & 0x1F) >> 1
  local pc = state["PC"].value & 0xffffff
  csv:write(string.format("%d,%06X,%d,%d,%04X\n", frame, pc, line, entry, data & 0xffff))
  logged = logged + 1
end)

_G._pw_trace = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  set_input("P1 A", frame >= 120 and frame <= 150)
  set_input("P1 Start", frame >= 180 and frame <= 210)
  set_input("P1 Right", frame >= 260)
  if frame % 300 == 0 then csv:flush() end
  if frame >= RUN_FRAMES then
    csv:flush(); csv:close()
    emu.print_info(string.format("STAGED PALETTE WRITERS: %d rows -> %s", logged, out))
    machine:exit()
  end
end)
emu.print_info("STAGED PALETTE WRITER TRACE ARMED -> " .. out)
