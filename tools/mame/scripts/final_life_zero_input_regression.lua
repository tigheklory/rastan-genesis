-- Deterministic final-life regression route.
-- Drives only COIN/START, then explicitly releases every gameplay control.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local state = cpu.state
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local symbols_path = assert(os.getenv("FINAL_LIFE_SYMBOLS"), "FINAL_LIFE_SYMBOLS is required")
local max_frames = tonumber(os.getenv("FINAL_LIFE_MAX_FRAMES") or "12000")
-- The arcade-owned GAME OVER dwell advances a 10-step counter once per 96
-- frames, so a correct zero-input transition can remain in subphase 8 for
-- roughly 960 frames.  Keep the stall bound beyond that intentional dwell.
local stall_frames = tonumber(os.getenv("FINAL_LIFE_STALL_FRAMES") or "1200")

local function r16(address) return program:read_u16(address) & 0xffff end
local function r32(address) return program:read_u32(address) & 0xffffffff end
local function r8(address) return program:read_u8(address) & 0xff end
local function reg(name)
  local item = state[name]
  return item and (item.value & 0xffffffff) or 0
end

local function parse_symbols(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local address, name = line:match("^([0-9A-Fa-f]+)%s+%S%s+([^%s]+)$")
    if address and name then result[name] = tonumber(address, 16) end
  end
  return result
end
local symbols = parse_symbols(symbols_path)
for _, name in ipairs({"genesistan_presentation_readiness", "genesistan_current_scene_id",
                        "genesistan_scene_present_pending", "palette_pending",
                        "native_player_body_count", "pc090oj_emitted_count"}) do
  assert(symbols[name], "missing symbol: " .. name)
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
local display_on = false
local ready_visible_frames = 0
local ready_visible_deaths = {}
local unsafe_visible_frames = 0
local unsafe_display_on_writes = 0
local post_ready_blank_frames = 0
local post_ready_blank_deaths = {}
local continue_reached = false
local continue_visible_frames = 0
local game_over_visible_frames = 0
local visible_restarts = {}
local restart_recorded_for_death = 0
local blank_seen_for_death = {}
local last_presentation_latch = -1
local last_ready_state = -1
local taps = {}
local events = assert(io.open(trace_dir .. "/events.tsv", "w"))
local frames = assert(io.open(trace_dir .. "/bounded_frames.tsv", "w"))
events:write("frame\tevent\tpc\tsp\touter\tphase\tsubphase\tlives\thp\tplayer_state\tdeath_step\tsession\tdata\n")
frames:write("frame\tpc\tsp\touter\tphase\tsubphase\tlives\thp\tplayer_state\tdeath_step\tsession\tdisplay\tpresentation\tready_state\tscene\tscene_pending\tpalette_pending\tplayer_body_count\temitted_count\tplayer_x\tplayer_y\tselector_primary\tselector_secondary\n")

local function snapshot_line(tag, data)
  events:write(string.format("%d\t%s\t%06X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%s\n",
    frame, tag, reg("PC") & 0xffffff, reg("SP"), r16(0xff0000), r16(0xff0002),
    r16(0xff0004), r16(0xff0100), r16(0xff013a), r16(0xff10e8),
    r16(0xff12f4), r16(0xff0034), data or ""))
  events:flush()
end

local function presentation_data()
  return string.format("display=%s latch=%02X ready=%04X scene=%02X scene_pending=%02X palette_pending=%02X body=%04X emitted=%04X x=%04X y=%04X sel=%04X/%04X",
    display_on and "ON" or "OFF", r8(symbols.genesistan_presentation_readiness), r16(0xff13aa),
    r8(symbols.genesistan_current_scene_id), r8(symbols.genesistan_scene_present_pending),
    r8(symbols.palette_pending), r16(symbols.native_player_body_count),
    r16(symbols.pc090oj_emitted_count), r16(0xff10be), r16(0xff10c0),
    r16(0xff1244), r16(0xff1246))
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

-- Observe only VDP register writes.  The RG-015 latch is consumed by the
-- completed publication event; this proves that no display-enable occurs
-- while HOLD is active and identifies READY/gameplay reveal boundaries.
taps[#taps + 1] = program:install_write_tap(0x00c00004, 0x00c00007, "final_life_vdp_ctrl",
  function(_, data, mask)
    mask = mask or 0xffffffff
    local function control_word(word)
      if (word & 0xff00) == 0x8100 then
        local next_on = (word & 0x0040) ~= 0
        local latch = r8(symbols.genesistan_presentation_readiness)
        if next_on and latch == 1 then unsafe_display_on_writes = unsafe_display_on_writes + 1 end
        display_on = next_on
        snapshot_line("VDP_REG1", presentation_data())
      end
    end
    if mask == 0xffffffff then control_word((data >> 16) & 0xffff) end
    control_word(data & 0xffff)
    return data
  end)

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
  local ready_death_count, post_ready_blank_count = 0, 0
  for _ in pairs(ready_visible_deaths) do ready_death_count = ready_death_count + 1 end
  for _ in pairs(post_ready_blank_deaths) do post_ready_blank_count = post_ready_blank_count + 1 end
  out:write(string.format("ready_visible_frames=%d\nready_visible_deaths=%d\nunsafe_visible_frames=%d\nunsafe_display_on_writes=%d\npost_ready_blank_frames=%d\npost_ready_blank_deaths=%d\ncontinue_reached=%s\ncontinue_visible_frames=%d\ngame_over_visible_frames=%d\nvisible_restarts=%d\n",
    ready_visible_frames, ready_death_count, unsafe_visible_frames,
    unsafe_display_on_writes, post_ready_blank_frames, post_ready_blank_count,
    continue_reached and "YES" or "NO", continue_visible_frames,
    game_over_visible_frames, #visible_restarts))
  for index, restart in ipairs(visible_restarts) do
    out:write(string.format("restart_%d=%s\n", index, restart))
  end
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
  local latch = r8(symbols.genesistan_presentation_readiness)
  local ready_state = r16(0xff13aa)
  -- RG-015's only stable visibility states are NORMAL (0, display on) and
  -- HOLD (1, display off). READY (2) is consumed inside the publication
  -- completion routine before the worker/frame boundary can observe it.
  display_on = latch == 0
  if latch ~= last_presentation_latch or ready_state ~= last_ready_state then
    snapshot_line("PRESENTATION_STATE", presentation_data())
    last_presentation_latch = latch
    last_ready_state = ready_state
  end
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

  if latch == 1 and display_on then unsafe_visible_frames = unsafe_visible_frames + 1 end
  if death_entries > 0 and latch == 1 and not display_on then blank_seen_for_death[death_entries] = true end
  -- The retained human-session READY owner is outer/phase/subphase 2/2/7.
  -- A5+0x13AA is a related frontend word (observed as 1 here), not the READY
  -- controller state; using 13 made a genuinely visible READY dwell report as
  -- absent.  Key this assertion to the proven 0x03A74E -> subphase-7 event.
  local ready_active = outer == 2 and phase == 2 and subphase == 7
  if death_entries > 0 and death_entries <= 2 and ready_active and display_on then
    ready_visible_frames = ready_visible_frames + 1
    ready_visible_deaths[death_entries] = true
  end
  if death_entries > 0 and death_entries <= 2 and ready_visible_deaths[death_entries] and
     not ready_active and not display_on then
    post_ready_blank_frames = post_ready_blank_frames + 1
    post_ready_blank_deaths[death_entries] = true
  end
  if death_entries > restart_recorded_for_death and death_entries <= 2 and
     blank_seen_for_death[death_entries] and
     ready_visible_deaths[death_entries] and post_ready_blank_deaths[death_entries] and
     outer == 2 and phase == 3 and not ready_active and player_state == 3 and display_on then
    local restart = string.format("frame=%d state=%04X x=%04X y=%04X sel=%04X/%04X scene=%02X pending=%02X palette=%02X body=%04X emitted=%04X",
      frame, player_state, r16(0xff10be), r16(0xff10c0), r16(0xff1244), r16(0xff1246),
      r8(symbols.genesistan_current_scene_id), r8(symbols.genesistan_scene_present_pending),
      r8(symbols.palette_pending), r16(symbols.native_player_body_count),
      r16(symbols.pc090oj_emitted_count))
    visible_restarts[#visible_restarts + 1] = restart
    restart_recorded_for_death = death_entries
    snapshot_line("FIRST_VISIBLE_RESTART", restart)
  end
  if gameplay_seen and death_entries >= 1 and lives == 0 and final_armed_frame < 0 then
    final_armed_frame = frame
    snapshot_line("FINAL_LIFE_ZERO", "armed")
  end
  if outer == 2 and phase == 4 and subphase == 8 then
    continue_reached = true
    if display_on then continue_visible_frames = continue_visible_frames + 1 end
  end
  if outer == 2 and phase == 4 and (subphase == 5 or subphase == 6) and display_on then
    game_over_visible_frames = game_over_visible_frames + 1
  end

  local pc = reg("PC") & 0xffffff
  if final_armed_frame >= 0 or (frame % 60) == 0 then
    frames:write(string.format("%d\t%06X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%s\t%02X\t%04X\t%02X\t%02X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
      frame, pc, reg("SP"), outer, phase, subphase, lives, r16(0xff013a), player_state,
      r16(0xff12f4), r16(0xff0034), display_on and "ON" or "OFF", latch, ready_state,
      r8(symbols.genesistan_current_scene_id), r8(symbols.genesistan_scene_present_pending),
      r8(symbols.palette_pending), r16(symbols.native_player_body_count),
      r16(symbols.pc090oj_emitted_count), r16(0xff10be), r16(0xff10c0),
      r16(0xff1244), r16(0xff1246)))
    frames:flush()
  end

  if exception then finish("FAIL", "exception_" .. exception); return end
  if unsafe_display_on_writes > 0 or unsafe_visible_frames > 0 then
    finish("FAIL", "unsafe_generation_became_visible"); return
  end
  -- Correct final-death flow enters terminal phase 4, exhausts lives, then reaches
  -- the GAME OVER setup/dwell (subphase 5/6) or leaves the gameplay umbrella.
  if final_armed_frame >= 0 and phase == 4 and (subphase == 5 or subphase == 6) then
    local ready_death_count, post_ready_blank_count = 0, 0
    for _ in pairs(ready_visible_deaths) do ready_death_count = ready_death_count + 1 end
    for _ in pairs(post_ready_blank_deaths) do post_ready_blank_count = post_ready_blank_count + 1 end
    if ready_death_count ~= 2 then finish("FAIL", "ready_not_visible_on_both_nonfinal_deaths"); return end
    if post_ready_blank_count ~= 2 then finish("FAIL", "post_ready_loading_blank_missing"); return end
    if #visible_restarts ~= 2 then finish("FAIL", "nonfinal_restart_count_mismatch"); return end
    if not continue_reached or continue_visible_frames == 0 then finish("FAIL", "continue_never_visible"); return end
    if game_over_visible_frames == 0 then finish("FAIL", "game_over_frontend_handoff_not_visible"); return end
    finish("PASS", "game_over_transition_and_death_respawn_presentation_reached"); return
  end
  if final_armed_frame >= 0 and outer ~= 2 then
    finish("FAIL", "frontend_transition_before_required_continue_game_over_visibility"); return
  end
  if final_armed_frame >= 0 and frame - last_transition_frame >= stall_frames then
    finish("FAIL", "final_life_state_stalled"); return
  end
  if frame >= max_frames then finish("FAIL", "maximum_frame_budget_reached") end
end)
