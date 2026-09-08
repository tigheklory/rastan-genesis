--[[
opt003_natural_transition.lua
=============================
OPT-003 valid-transition test (GENESIS NTSC target).

The canonical build0310_epoch_gate reaches the Layer-A installer by SYNTHETIC
mid-frame injection: it writes the target record to a5+0x013E, pushes the
interrupted PC, and jumps the CPU straight into fg_boundary_install. That test
is timing-fragile at active_lut[0x034C].

This tool instead reaches the SAME record 2(pkg0) -> record 3(pkg5) epoch
transition through NATURAL arcade progression: it drives coin/start, then holds
P1 Right so the player scrolls and the arcade's own segment boundary
(fg_boundary_advance_segment, the replacement for arcade 0x0558FE) advances the
record on its own and calls the real installer. No injection, no forced record
write, no PC hijack.

It then observes active_lut[0x034C] at the moment record 3 first becomes active
and for several frames after, plus package/record/installer state, so we can
classify OPT-003 as a real production bug or a synthetic-gate artifact.

OUTPUT: build/mame/home/opt003_natural/opt003_natural.log
RUN:    tools/mame/run_opt003_natural_wsl.sh [rom]
--]]

local TARGET_RECORD  = tonumber(os.getenv("OPT003_TARGET_RECORD") or "3")
local EXPECTED_SLOT  = tonumber(os.getenv("OPT003_EXPECTED_SLOT") or "0x0420")
local CODE           = 0x034C
local MAX_FRAMES     = tonumber(os.getenv("OPT003_MAX_FRAMES") or "5000")
local OBSERVE_FRAMES = tonumber(os.getenv("OPT003_OBSERVE_FRAMES") or "24")

local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local program = cpu.spaces["program"]
local state = cpu.state

-- Symbols from nm output (out/symbol.txt), passed via env as name=hexaddr pairs.
local symbols = {}
do
  local s = os.getenv("OPT003_SYMBOLS") or ""
  for name, hex in s:gmatch("([%w_]+)=([0-9a-fA-F]+)") do
    symbols[name] = tonumber(hex, 16)
  end
end
local required = {"fg_boundary_active_record", "fg_boundary_active_package",
  "fg_boundary_active_lut", "fg_boundary_epoch_transitions",
  "genesistan_current_scene_id"}
for _, n in ipairs(required) do
  assert(symbols[n], "missing symbol: " .. n)
end

local function r8(a)  return program:read_u8(a)  & 0xff end
local function r16(a) return program:read_u16(a) & 0xffff end
local function r32(a) return program:read_u32(a) & 0xffffffff end
local function reg(n) local i = state[n]; return i and (i.value & 0xffffffff) or 0 end
local function rec()  return r16(symbols.fg_boundary_active_record) & 0xffff end
local function pkg()  return r16(symbols.fg_boundary_active_package) & 0xffff end
local function scene() return r8(symbols.genesistan_current_scene_id) end
local function lut(code) return r16(symbols.fg_boundary_active_lut + code * 2) & 0xffff end
local function eptrans() return r32(symbols.fg_boundary_epoch_transitions) end

local homedir = machine.options.entries.homepath:value():match("([^;]+)") or "."
local dir = homedir .. "/opt003_natural"
os.execute('mkdir -p "' .. dir .. '" 2>/dev/null')
local log_path = dir .. "/opt003_natural.log"
do local f = io.open(log_path, "w"); if f then f:close() end end
local function logln(s)
  local f = io.open(log_path, "a"); if f then f:write(s .. "\n"); f:close() end
  emu.print_info(s)
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, on)
  if fields[name] then fields[name]:set_value(on and 1 or 0) end
end

local frame = 0
local reached_frame = -1
local prev_rec, prev_pkg = -1, -1
local crash = 0

-- follow final vectors for exceptions
for _, v in ipairs({0x000008, 0x00000c, 0x000010}) do
  local pc = r32(v) & 0xffffff
  program:install_read_tap(pc, pc + 1, "exc", function(_, d) crash = crash + 1; return d end)
end

logln(string.format("==== opt003 natural transition rom=%s target_record=%d code=%04X expect=%04X ====",
  tostring(emu.romname()), TARGET_RECORD, CODE, EXPECTED_SLOT))

emu.register_frame_done(function()
  frame = frame + 1

  -- Genesis: press P1 Start a few times to get past title/attract into gameplay, then scroll.
  set_input("P1 Start", (frame >= 120 and frame <= 130) or (frame >= 180 and frame <= 190)
                        or (frame >= 240 and frame <= 250))
  if frame > 300 then
    set_input("P1 Right", true)                 -- scroll forward
    set_input("P1 C", (frame % 40) < 8)         -- jump (Genesis C) to clear gaps/obstacles
    set_input("P1 B", (frame % 24) < 8)         -- attack (Genesis B) to kill blockers
  end

  -- Log record/package transitions and the LUT entry once we are in gameplay.
  if scene() == 1 then
    local rc, pk = rec(), pkg()
    if rc ~= prev_rec or pk ~= prev_pkg then
      logln(string.format("frame=%d scene=1 record=%d package=%d lut034C=%04X eptrans=%d %s",
        frame, rc, pk, lut(CODE), eptrans(),
        (rc == TARGET_RECORD and reached_frame < 0) and "<== TARGET RECORD REACHED" or ""))
      prev_rec, prev_pkg = rc, pk
      if rc == TARGET_RECORD and reached_frame < 0 then reached_frame = frame end
    end
  end

  -- Observe the LUT for a window after reaching the target record.
  if reached_frame >= 0 and frame >= reached_frame and frame <= reached_frame + OBSERVE_FRAMES then
    logln(string.format("  observe frame=%d record=%d package=%d lut034C=%04X eptrans=%d exc=%d",
      frame, rec(), pkg(), lut(CODE), eptrans(), crash))
  end

  if reached_frame >= 0 and frame == reached_frame + OBSERVE_FRAMES + 1 then
    local final = lut(CODE)
    logln(string.format("RESULT target_record=%d reached_frame=%d final_lut034C=%04X expected=%04X verdict=%s crash=%d",
      TARGET_RECORD, reached_frame, final, EXPECTED_SLOT,
      (final == EXPECTED_SLOT) and "CORRECT" or "WRONG", crash))
    machine:exit()
  end

  if frame >= MAX_FRAMES then
    logln(string.format("RESULT target_record=%d NOT_REACHED_within=%d last_record=%d last_pkg=%d lut034C=%04X crash=%d",
      TARGET_RECORD, MAX_FRAMES, rec(), pkg(), lut(CODE), crash))
    machine:exit()
  end
end)
