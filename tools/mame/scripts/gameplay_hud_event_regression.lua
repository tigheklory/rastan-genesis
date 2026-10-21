-- Writer-triggered reduced-gameplay-HUD regression for Genesis NTSC.
-- Reuses the established deterministic coin/START route.  Once gameplay is
-- stable, it invokes the retained arcade BCD score-award routine exactly as a
-- caller would (D0=0x1234, JSR-compatible return stack), then verifies the
-- persistent semantic HUD lane and both alternating staged SAT banks.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local symbols_path = assert(os.getenv("HUD_EVENT_SYMBOLS"), "HUD_EVENT_SYMBOLS is required")
local output_path = assert(os.getenv("HUD_EVENT_OUTPUT"), "HUD_EVENT_OUTPUT is required")
local score_award_pc = assert(tonumber(os.getenv("HUD_EVENT_SCORE_AWARD_PC") or "", 16),
  "HUD_EVENT_SCORE_AWARD_PC is required")

local function parse_symbols(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local address, name = line:match("^([0-9A-Fa-f]+)%s+%S%s+([^%s]+)$")
    if address and name then result[name] = tonumber(address, 16) end
  end
  return result
end

local symbols = parse_symbols(symbols_path)
for _, name in ipairs({"genesistan_current_scene_id", "gameplay_hud_semantic_count",
  "gameplay_hud_semantic_queue", "gameplay_hud_score_dirty", "staged_sprite_sat",
  "staged_sprite_sat_b", "pc090oj_sat_bank"}) do
  assert(symbols[name], "missing symbol: " .. name)
end

local function r8(a) return program:read_u8(a) & 0xff end
local function r16(a) return program:read_u16(a) & 0xffff end
local function w32(a, v) program:write_u32(a, v & 0xffffffff) end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame, gameplay_frame, injected_frame = 0, nil, nil
local initial_queue, changed_queue = nil, nil
local initial_count, changed_count = nil, nil
local bank_seen = {[0]=false, [1]=false}
local hud_event_validated = false
local continue_frame, reentry_frame = nil, nil
local death_entries, last_player_state = 0, -1
local errors = {}

local function fail(message) errors[#errors + 1] = message end

local function queue_snapshot(count)
  local out = {}
  for i = 0, count * 4 - 1 do out[#out + 1] = r16(symbols.gameplay_hud_semantic_queue + i * 2) end
  return table.concat(out, ",")
end

local function validate_labels(count)
  -- Arcade leading-zero suppression permits the all-zero score to contain
  -- only the persistent 1/U/P label records.
  if count < 3 then fail("semantic_count_below_minimum"); return end
  local base = symbols.gameplay_hud_semantic_queue + (count - 3) * 8
  local expected = {
    {0x0010, 0xD039, 0x0040},
    {0x0000, 0xD048, 0x0028},
    {0x0000, 0xD046, 0x0038},
  }
  for i, e in ipairs(expected) do
    local p = base + (i - 1) * 8
    if r16(p + 2) ~= e[1] or r16(p + 4) ~= e[2] or r16(p + 6) ~= e[3] then
      fail("label_semantics_" .. i)
    end
  end
end

local function validate_sat_bank(base, count, tag)
  -- The HUD lane is finalized first.  Semantic Y is translated by -8 and
  -- Genesis SAT bias +0x80; X receives +0x80.  Tile words are deliberately
  -- ignored because residency owns their physical slots.
  local label = count - 3
  local expected = {
    {index=label,   y=0x0088, x=0x00C0},
    {index=label+1, y=0x0078, x=0x00A8},
    {index=label+2, y=0x0078, x=0x00B8},
  }
  for _, e in ipairs(expected) do
    local p = base + e.index * 8
    if r16(p) ~= e.y or r16(p + 6) ~= e.x then fail(tag .. "_label_geometry_" .. e.index) end
  end
  for i = 0, label - 1 do
    local p = base + i * 8
    if r16(p) ~= 0x0088 then fail(tag .. "_digit_y_" .. i) end
  end
end

local function finish(result, reason)
  local out = assert(io.open(output_path, "w"))
  out:write(string.format("result=%s\nreason=%s\nframe=%d\n", result, reason, frame))
  out:write(string.format("gameplay_frame=%s\ninjected_frame=%s\n",
    tostring(gameplay_frame), tostring(injected_frame)))
  out:write(string.format("death_entries=%d\ncontinue_frame=%s\nreentry_frame=%s\n",
    death_entries, tostring(continue_frame), tostring(reentry_frame)))
  out:write(string.format("score=%02X%02X%02X\ndirty=%02X\n",
    r8(0xff011e), r8(0xff011d), r8(0xff011c), r8(symbols.gameplay_hud_score_dirty)))
  out:write(string.format("initial_count=%s\nchanged_count=%s\n",
    tostring(initial_count), tostring(changed_count)))
  out:write(string.format("initial_queue=%s\nchanged_queue=%s\n",
    tostring(initial_queue), tostring(changed_queue)))
  out:write(string.format("sat_bank_0_seen=%s\nsat_bank_1_seen=%s\n",
    bank_seen[0] and "YES" or "NO", bank_seen[1] and "YES" or "NO"))
  out:write("errors=" .. table.concat(errors, ",") .. "\n")
  out:close()
  machine:exit()
end

local function drive_inputs()
  local continue_coin = continue_frame and frame >= continue_frame + 1 and frame <= continue_frame + 13
  local continuing = continue_frame and frame >= continue_frame + 24 and frame <= continue_frame + 36
  set_input("Coin 1", (frame >= 120 and frame <= 132) or continue_coin)
  set_input("P1 A", (frame >= 120 and frame <= 132) or continue_coin)
  set_input("1 Player Start", (frame >= 175 and frame <= 187) or continuing)
  set_input("P1 Start", (frame >= 175 and frame <= 187) or continuing)
  for _, name in ipairs({"P1 Up", "P1 Down", "P1 Left", "P1 Right", "P1 B", "P1 C"}) do
    set_input(name, false)
  end
end

emu.register_frame_done(function()
  frame = frame + 1
  drive_inputs()
  local gameplay = r16(0xff0000) == 2 and r16(0xff0002) == 3 and
    r16(0xff0004) == 0 and r8(symbols.genesistan_current_scene_id) == 1
  if gameplay and not gameplay_frame then gameplay_frame = frame end
  if not gameplay_frame then
    if frame >= 1200 then finish("FAIL", "gameplay_not_reached") end
    return
  end

  local player_state = r16(0xff10e8)
  if player_state == 8 and last_player_state ~= 8 then death_entries = death_entries + 1 end
  last_player_state = player_state

  local age = frame - gameplay_frame
  if not hud_event_validated and age == 20 then
    initial_count = r16(symbols.gameplay_hud_semantic_count)
    initial_queue = queue_snapshot(initial_count)
    validate_labels(initial_count)
    if r8(symbols.gameplay_hud_score_dirty) ~= 0 then fail("initial_dirty_not_clear") end
    if r8(0xff011e) ~= 0 or r8(0xff011d) ~= 0 or r8(0xff011c) ~= 0 then fail("initial_score_nonzero") end
  elseif not hud_event_validated and age == 24 then
    -- External test tooling emulates JSR score_award with packed-BCD +1234.
    local pc = assert(cpu.state["PC"], "PC unavailable")
    local d0 = assert(cpu.state["D0"], "D0 unavailable")
    local sp = assert(cpu.state["SP"] or cpu.state["A7"], "SP unavailable")
    local return_pc = pc.value & 0xffffff
    local stack = (sp.value - 4) & 0xffffff
    w32(stack, return_pc)
    sp.value = stack
    d0.value = 0x00001234
    pc.value = score_award_pc
    injected_frame = frame
  elseif not hud_event_validated and age >= 27 and age <= 42 then
    local bank = r16(symbols.pc090oj_sat_bank) & 1
    bank_seen[bank] = true
    if r8(0xff011e) == 0 and r8(0xff011d) == 0x12 and r8(0xff011c) == 0x34 and
       r8(symbols.gameplay_hud_score_dirty) == 0 then
      changed_count = r16(symbols.gameplay_hud_semantic_count)
      changed_queue = queue_snapshot(changed_count)
      validate_labels(changed_count)
      validate_sat_bank(symbols.staged_sprite_sat, changed_count, "bank0")
      validate_sat_bank(symbols.staged_sprite_sat_b, changed_count, "bank1")
    end
  elseif not hud_event_validated and age == 43 then
    if not changed_count then fail("score_dirty_rebuild_not_observed") end
    if changed_count and changed_count < 7 then fail("high_order_digits_missing") end
    if initial_queue == changed_queue then fail("score_queue_did_not_change") end
    if not bank_seen[0] or not bank_seen[1] then fail("both_sat_banks_not_observed") end
    if #errors ~= 0 then finish("FAIL", "contract_mismatch"); return end
    hud_event_validated = true
  end

  if hud_event_validated and not continue_frame and r16(0xff0000) == 2 and
      r16(0xff0002) == 4 and r16(0xff0004) == 8 then
    continue_frame = frame
  end
  if continue_frame and not reentry_frame and frame > continue_frame + 36 and gameplay and
      r16(0xff0034) ~= 0 then
    reentry_frame = frame
  end
  if reentry_frame and frame >= reentry_frame + 12 then
    local count = r16(symbols.gameplay_hud_semantic_count)
    validate_labels(count)
    if r8(symbols.gameplay_hud_score_dirty) ~= 0 then fail("reentry_dirty_not_consumed") end
    if count < 3 then fail("reentry_hud_missing") end
    if death_entries < 3 then fail("final_life_route_incomplete") end
    if #errors == 0 then finish("PASS", "writer_event_both_sat_banks_and_continue_reentry")
    else finish("FAIL", "reentry_contract_mismatch") end
    return
  end
  if frame >= 10000 then
    finish("FAIL", "lifecycle_frame_budget_exhausted")
  end
end)
