-- Deterministic final-life regression route.
-- Drives only COIN/START, then explicitly releases every gameplay control.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local state = cpu.state
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local max_frames = tonumber(os.getenv("FINAL_LIFE_MAX_FRAMES") or "12000")
local stall_frames = tonumber(os.getenv("FINAL_LIFE_STALL_FRAMES") or "900")

local function r16(address) return program:read_u16(address) & 0xffff end
local function r32(address) return program:read_u32(address) & 0xffffffff end
local function reg(name)
  local item = state[name]
  return item and (item.value & 0xffffffff) or 0
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame = 0
local finished = false
local gameplay_seen = false
local death_entries = 0
local final_armed_frame = -1
local last_transition_frame = 0
local last_tuple = ""
local last_player_state = -1
local taps = {}
local events = assert(io.open(trace_dir .. "/events.tsv", "w"))
local frames = assert(io.open(trace_dir .. "/bounded_frames.tsv", "w"))
events:write("frame\tevent\tpc\tsp\touter\tphase\tsubphase\tlives\thp\tplayer_state\tdeath_step\tsession\tdata\n")
frames:write("frame\tpc\tsp\touter\tphase\tsubphase\tlives\thp\tplayer_state\tdeath_step\tsession\n")

local function snapshot_line(tag, data)
  events:write(string.format("%d\t%s\t%06X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%s\n",
    frame, tag, reg("PC") & 0xffffff, reg("SP"), r16(0xff0000), r16(0xff0002),
    r16(0xff0004), r16(0xff0100), r16(0xff013a), r16(0xff10e8),
    r16(0xff12f4), r16(0xff0034), data or ""))
  events:flush()
end

local function install_word_tap(address, name)
  taps[#taps + 1] = program:install_write_tap(address, address + 1, name,
    function(_, data, mask)
      snapshot_line("WRITE_" .. name, string.format("value=%08X mask=%08X", data & 0xffffffff, mask & 0xffffffff))
      last_transition_frame = frame
      return data
    end)
end

install_word_tap(0xff0000, "OUTER")
install_word_tap(0xff0002, "PHASE")
install_word_tap(0xff0004, "SUBPHASE")
install_word_tap(0xff0100, "LIVES")
install_word_tap(0xff10e8, "PLAYER_STATE")
install_word_tap(0xff12f4, "DEATH_STEP")

local vectors = {
  {name="BUS_ERROR", address=r32(0x000008) & 0xffffff},
  {name="ADDRESS_ERROR", address=r32(0x00000c) & 0xffffff},
  {name="ILLEGAL_INSTRUCTION", address=r32(0x000010) & 0xffffff},
}
local exception = nil
for _, item in ipairs(vectors) do
  taps[#taps + 1] = program:install_read_tap(item.address, item.address + 1, item.name,
    function(_, data, _)
      exception = item.name
      snapshot_line(item.name, string.format("vector=%06X", item.address))
      return data
    end)
end

local function finish(result, reason)
  if finished then return end
  finished = true
  snapshot_line("FINISH", reason)
  local out = assert(io.open(trace_dir .. "/summary.txt", "w"))
  out:write(string.format("result=%s\nreason=%s\nframes=%d\n", result, reason, frame))
  out:write(string.format("gameplay_seen=%s\ndeath_entries=%d\nfinal_armed_frame=%d\n",
    gameplay_seen and "YES" or "NO", death_entries, final_armed_frame))
  out:write(string.format("pc=%06X\nsp=%08X\nouter=%04X\nphase=%04X\nsubphase=%04X\n",
    reg("PC") & 0xffffff, reg("SP"), r16(0xff0000), r16(0xff0002), r16(0xff0004)))
  out:write(string.format("lives=%04X\nhp=%04X\nplayer_state=%04X\ndeath_step=%04X\nsession=%04X\n",
    r16(0xff0100), r16(0xff013a), r16(0xff10e8), r16(0xff12f4), r16(0xff0034)))
  out:close()
  frames:close()
  events:close()
  machine:exit()
end

local function drive_inputs()
  local coin = frame >= 120 and frame <= 132
  local start = frame >= 175 and frame <= 187
  set_input("Coin 1", coin)
  set_input("P1 A", coin)
  set_input("1 Player Start", start)
  set_input("P1 Start", start)
  for _, name in ipairs({"P1 Up", "P1 Down", "P1 Left", "P1 Right", "P1 B", "P1 C"}) do
    set_input(name, false)
  end
end

emu.register_frame_done(function()
  frame = frame + 1
  drive_inputs()

  local outer, phase, subphase = r16(0xff0000), r16(0xff0002), r16(0xff0004)
  local lives, player_state = r16(0xff0100), r16(0xff10e8)
  local tuple = string.format("%04X/%04X/%04X/%04X/%04X", outer, phase, subphase, lives, player_state)
  if tuple ~= last_tuple then
    snapshot_line("STATE", tuple)
    last_tuple = tuple
    last_transition_frame = frame
  end
  if outer == 2 and phase == 3 then gameplay_seen = true end
  if player_state == 8 and last_player_state ~= 8 then
    death_entries = death_entries + 1
    snapshot_line("DEATH_ENTRY", string.format("count=%d", death_entries))
  end
  last_player_state = player_state
  if gameplay_seen and death_entries >= 1 and lives == 0 and final_armed_frame < 0 then
    final_armed_frame = frame
    snapshot_line("FINAL_LIFE_ZERO", "armed")
  end

  local pc = reg("PC") & 0xffffff
  if final_armed_frame >= 0 or (frame % 60) == 0 then
    frames:write(string.format("%d\t%06X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
      frame, pc, reg("SP"), outer, phase, subphase, lives, r16(0xff013a), player_state,
      r16(0xff12f4), r16(0xff0034)))
    frames:flush()
  end

  if exception then finish("FAIL", "exception_" .. exception); return end
  -- Correct final-death flow enters terminal phase 4, exhausts lives, then reaches
  -- the GAME OVER setup/dwell (subphase 5/6) or leaves the gameplay umbrella.
  if final_armed_frame >= 0 and phase == 4 and (subphase == 5 or subphase == 6) then
    finish("PASS", "game_over_transition_reached"); return
  end
  if final_armed_frame >= 0 and outer ~= 2 then
    finish("PASS", "post_gameplay_frontend_transition_reached"); return
  end
  if final_armed_frame >= 0 and frame - last_transition_frame >= stall_frames then
    finish("FAIL", "final_life_state_stalled"); return
  end
  if frame >= max_frames then finish("FAIL", "maximum_frame_budget_reached") end
end)
