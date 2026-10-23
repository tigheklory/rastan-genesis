-- PROMPT RG-004 bounded frontend presentation probe.
-- Reuses the established final-life input route, then stops at the Continue
-- dwell. It never supplies gameplay direction or attack input.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local symbols_path = assert(os.getenv("RG004_SYMBOLS"), "RG004_SYMBOLS is required")
local output_path = assert(os.getenv("RG004_OUTPUT"), "RG004_OUTPUT is required")
local continue_dwell_frames = tonumber(os.getenv("RG004_CONTINUE_DWELL_FRAMES") or "120")
local route = os.getenv("RG004_ROUTE") or "final_life"

local function parse_symbols(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local address, name = line:match("^([0-9A-Fa-f]+)%s+%S%s+([^%s]+)$")
    if address and name then result[name] = tonumber(address, 16) end
  end
  return result
end

local symbols = parse_symbols(symbols_path)
for _, name in ipairs({"staged_bg_buffer", "staged_palette_words",
                        "bg_row_dirty", "bg_col_dirty", "palette_pending",
                        "genesistan_frontend_presentation_reset",
                        "genesistan_current_scene_id",
                        "genesistan_current_pc080sn_tileset_id",
                        "genesistan_presentation_readiness"}) do
  assert(symbols[name], "missing symbol: " .. name)
end

local function r8(address) return program:read_u8(address) & 0xff end
local function r16(address) return program:read_u16(address) & 0xffff end

-- MAME's :gen_vdp "videoram" Lua space is only the inherited 16-KiB Mode-4
-- compatibility window.  Read actual Mega Drive VRAM/CRAM through the 68000
-- VDP ports, using the established terminal-read method from
-- probe_genesis_vram_space.lua/build0417_A0154_scanout_timing.lua.  This is
-- done only after the terminal Continue state has been reached; the machine
-- exits immediately afterward, so the diagnostic cannot perturb gameplay.
local function vdp_read_command(address, code)
  program:write_u16(0x00c00004, (address & 0x3fff) | ((code & 3) << 14))
  program:write_u16(0x00c00004, ((address >> 14) & 3) | ((code & 0x3c) << 2))
end

local function read_actual_vram()
  local words = {}
  program:write_u16(0x00c00004, 0x8f02)
  vdp_read_command(0, 0)
  for index = 0, 0x7fff do
    words[index] = program:read_u16(0x00c00000) & 0xffff
  end
  return words
end

local function read_actual_cram()
  local words = {}
  vdp_read_command(0, 8)
  for index = 0, 63 do
    words[index] = program:read_u16(0x00c00000) & 0xffff
  end
  return words
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame = 0
local continue_frame = nil
local continue_visible_frames = 0
local finished = false
local attract_events = {}
local attract_taps = {}
local attract_last_tuple = ""
local attract_demo_seen = false
local attract_demo_death_seen = false
local attract_second_title_frame = nil
local first_title_palette = nil
local second_title_palette = nil
local display_on = false
local unsafe_display_on_writes = 0
local second_title_display_enable_writes = 0
local second_title_display_disable_writes = 0

local function palette_snapshot()
  local result = {}
  for index = 0, 63 do
    result[index + 1] = r16(symbols.staged_palette_words + index * 2)
  end
  return result
end

local function palette_text(values)
  local lines = {}
  for line = 0, 3 do
    local entries = {}
    for entry = 0, 15 do
      entries[#entries + 1] = string.format("%04X", values[line * 16 + entry + 1])
    end
    lines[#lines + 1] = table.concat(entries, ",")
  end
  return lines
end

local function attract_event(tag)
  attract_events[#attract_events + 1] = string.format(
    "%d\t%s\t%06X\t%04X/%04X/%04X\t%02X\t%02X",
    frame, tag, cpu.state["PC"].value & 0xffffff,
    r16(0xff0000), r16(0xff0002), r16(0xff0004),
    r8(symbols.genesistan_current_scene_id),
    r8(symbols.genesistan_current_pc080sn_tileset_id))
end

local function install_exec_observer(address, name)
  attract_taps[#attract_taps + 1] = program:install_read_tap(address, address + 1,
    "rg004_" .. name, function(_, data)
      attract_event(name)
      return data
    end)
end

local function finish_attract(result, reason)
  if finished then return end
  finished = true
  local actual_cram = read_actual_cram()
  local out = assert(io.open(output_path, "w"))
  out:write(string.format("route=attract\nresult=%s\nreason=%s\nframe=%d\n", result, reason, frame))
  out:write(string.format("state=%04X/%04X/%04X\nscene=%02X\ntileset=%02X\n",
    r16(0xff0000), r16(0xff0002), r16(0xff0004),
    r8(symbols.genesistan_current_scene_id),
    r8(symbols.genesistan_current_pc080sn_tileset_id)))
  out:write(string.format(
    "display=%s\npresentation_readiness=%02X\nsecond_title_display_enable_writes=%d\n" ..
    "second_title_display_disable_writes=%d\nsecond_title_visibility=%s\nunsafe_display_on_writes=%d\n",
    display_on and "ON" or "OFF", r8(symbols.genesistan_presentation_readiness),
    second_title_display_enable_writes, second_title_display_disable_writes,
    second_title_display_enable_writes > 0 and display_on and
      r8(symbols.genesistan_presentation_readiness) == 0 and "PASS" or "FAIL",
    unsafe_display_on_writes))
  out:write(string.format("demo_seen=%s\ndemo_death_seen=%s\n",
    attract_demo_seen and "YES" or "NO", attract_demo_death_seen and "YES" or "NO"))
  if first_title_palette then
    for line, value in ipairs(palette_text(first_title_palette)) do
      out:write(string.format("first_title_line_%d=%s\n", line - 1, value))
    end
  end
  if second_title_palette then
    for line, value in ipairs(palette_text(second_title_palette)) do
      out:write(string.format("second_title_line_%d=%s\n", line - 1, value))
    end
  end
  for line = 0, 3 do
    local entries = {}
    for entry = 0, 15 do
      entries[#entries + 1] = string.format("%04X", actual_cram[line * 16 + entry])
    end
    out:write(string.format("terminal_cram_line_%d=%s\n", line, table.concat(entries, ",")))
  end
  out:write("events:\nframe\ttag\tpc\tstate\tscene\ttileset\n")
  for _, event in ipairs(attract_events) do out:write(event .. "\n") end
  out:close()
  machine:exit()
end

-- Observe the actual Genesis VDP register-1 writes.  Semantic state and CRAM
-- can be correct while the display-enable bit remains clear, which is the
-- RG-017 failure that the previous RG-004 route could not distinguish.
attract_taps[#attract_taps + 1] = program:install_write_tap(
  0x00c00004, 0x00c00007, "rg004_vdp_ctrl", function(_, data, mask)
    mask = mask or 0xffffffff
    local function control_word(word)
      if (word & 0xff00) == 0x8100 then
        local next_on = (word & 0x0040) ~= 0
        if next_on and r8(symbols.genesistan_presentation_readiness) == 1 then
          unsafe_display_on_writes = unsafe_display_on_writes + 1
        end
        if attract_second_title_frame then
          if next_on then
            second_title_display_enable_writes = second_title_display_enable_writes + 1
          else
            second_title_display_disable_writes = second_title_display_disable_writes + 1
          end
        end
        display_on = next_on
      end
    end
    if mask == 0xffffffff then control_word((data >> 16) & 0xffff) end
    control_word(data & 0xffff)
    return data
  end)

local function finish()
  if finished then return end
  finished = true
  local actual_vram = read_actual_vram()
  local actual_cram = read_actual_cram()
  local out = assert(io.open(output_path, "w"))
  out:write(string.format("frame=%d\nstate=%04X/%04X/%04X\nscene=%02X\ntileset=%02X\n",
    frame, r16(0xff0000), r16(0xff0002), r16(0xff0004),
    r8(symbols.genesistan_current_scene_id),
    r8(symbols.genesistan_current_pc080sn_tileset_id)))
  out:write(string.format("presentation_readiness=%02X\ncontinue_visible_frames=%d\ncontinue_visibility=%s\n",
    r8(symbols.genesistan_presentation_readiness), continue_visible_frames,
    continue_visible_frames > 0 and "PASS" or "FAIL"))
  out:write(string.format("continue_reached=%s\n", continue_frame and "YES" or "NO"))
  out:write(string.format("bg_row_dirty=%08X\nbg_col_dirty=%08X%08X\npalette_pending=%02X\n",
    program:read_u32(symbols.bg_row_dirty) & 0xffffffff,
    program:read_u32(symbols.bg_col_dirty) & 0xffffffff,
    program:read_u32(symbols.bg_col_dirty + 4) & 0xffffffff,
    r8(symbols.palette_pending)))
  for line = 0, 3 do
    out:write(string.format("palette_line_%d_stage=", line))
    for entry = 0, 15 do
      out:write(string.format("%04X%s",
        r16(symbols.staged_palette_words + (line * 16 + entry) * 2),
        entry == 15 and "\n" or ","))
    end
    out:write(string.format("palette_line_%d_cram=", line))
    for entry = 0, 15 do
      out:write(string.format("%04X%s", actual_cram[line * 16 + entry],
        entry == 15 and "\n" or ","))
    end
  end
  local base_cell = 0x1240 // 4
  local distinct_stage, distinct_vram = {}, {}
  local mismatch = 0
  local panel_cells = {}
  for row = 0, 9 do
    for col = 0, 11 do panel_cells[base_cell + row * 64 + col] = true end
  end
  local outside_nonzero, outside_mismatch = 0, 0
  local outside_examples = {}
  for cell = 0, 2047 do
    if not panel_cells[cell] then
      local sw = r16(symbols.staged_bg_buffer + cell * 2)
      local vw = actual_vram[(0xc000 + cell * 2) // 2]
      if (sw & 0x07ff) ~= 0 then
        outside_nonzero = outside_nonzero + 1
        if #outside_examples < 16 then
          outside_examples[#outside_examples + 1] = string.format("%04X:%04X/%04X", cell, sw, vw)
        end
      end
      if sw ~= vw then outside_mismatch = outside_mismatch + 1 end
    end
  end
  out:write(string.format("outside_panel_nonzero_slots=%d\noutside_panel_name_mismatch=%d\noutside_panel_examples=%s\n",
    outside_nonzero, outside_mismatch, table.concat(outside_examples, ",")))
  out:write("row\tcol\tcell\tstage_word\tvram_word\tstage_slot\tvram_slot\tstage_pattern_nonzero\tvram_pattern_nonzero\tstage_pattern_sum\tvram_pattern_sum\n")
  for row = 0, 9 do
    for col = 0, 11 do
      local cell = base_cell + row * 64 + col
      local sw = r16(symbols.staged_bg_buffer + cell * 2)
      local vw = actual_vram[(0xc000 + cell * 2) // 2]
      distinct_stage[sw] = true
      distinct_vram[vw] = true
      if sw ~= vw then mismatch = mismatch + 1 end
      local ss, vs = sw & 0x07ff, vw & 0x07ff
      local sn, vn, sh, vh = 0, 0, 0, 0
      for word = 0, 15 do
        local sv = actual_vram[ss * 16 + word]
        local vv = actual_vram[vs * 16 + word]
        if sv ~= 0 then sn = sn + 1 end
        if vv ~= 0 then vn = vn + 1 end
        sh = (sh + sv) & 0xffff
        vh = (vh + vv) & 0xffff
      end
      out:write(string.format("%d\t%d\t%04X\t%04X\t%04X\t%04X\t%04X\t%d\t%d\t%04X\t%04X\n",
        row, col, cell, sw, vw, ss, vs, sn, vn, sh, vh))
    end
  end
  local function count(t) local n = 0; for _ in pairs(t) do n = n + 1 end; return n end
  out:write(string.format("continue_stage_distinct=%d\ncontinue_vram_distinct=%d\ncontinue_name_mismatch=%d\n",
    count(distinct_stage), count(distinct_vram), mismatch))
  out:close()
  machine:exit()
end

if route == "attract" then
  -- Current Build-0464 address-map authority:
  -- arcade 0x056440 -> runtime 0x0564AE; arcade 0x03AD4C -> 0x03AF4E.
  install_exec_observer(0x0564ae, "ARCADE_056440")
  install_exec_observer(0x03af4e, "ARCADE_03AD4C")
  install_exec_observer(symbols.genesistan_frontend_presentation_reset,
    "FRONTEND_PRESENTATION_RESET")
end

emu.register_frame_done(function()
  frame = frame + 1
  if route == "attract" then
    for _, name in ipairs({"Coin 1", "P1 A", "1 Player Start", "P1 Start",
                           "P1 Up", "P1 Down", "P1 Left", "P1 Right", "P1 B", "P1 C"}) do
      set_input(name, false)
    end
    local outer, phase, subphase = r16(0xff0000), r16(0xff0002), r16(0xff0004)
    local tuple = string.format("%04X/%04X/%04X", outer, phase, subphase)
    if tuple ~= attract_last_tuple then
      attract_event("STATE")
      attract_last_tuple = tuple
    end
    if not first_title_palette and outer == 0 and phase == 1 then
      first_title_palette = palette_snapshot()
      attract_event("FIRST_TITLE")
    end
    if outer == 2 and phase == 3 then attract_demo_seen = true end
    if attract_demo_seen and r16(0xff10e8) == 8 then
      attract_demo_death_seen = true
    end
    if attract_demo_death_seen and outer == 0 and phase == 1 then
      if not attract_second_title_frame then
        attract_second_title_frame = frame
        second_title_palette = palette_snapshot()
        attract_event("SECOND_TITLE")
      elseif frame >= attract_second_title_frame + 5 then
        if second_title_display_enable_writes > 0 and display_on and
           r8(symbols.genesistan_presentation_readiness) == 0 and
           unsafe_display_on_writes == 0 then
          finish_attract("PASS", "SECOND_TITLE_VISIBLE")
        else
          finish_attract("FAIL", "SECOND_TITLE_REACHED_DISPLAY_OFF")
        end
        return
      end
    end
    if frame >= 20000 then finish_attract("FAIL", "MAX_FRAMES"); return end
    return
  end

  local coin = frame >= 120 and frame <= 132
  local start = frame >= 175 and frame <= 187
  set_input("Coin 1", coin)
  set_input("P1 A", coin)
  set_input("1 Player Start", start)
  set_input("P1 Start", start)
  for _, name in ipairs({"P1 Up", "P1 Down", "P1 Left", "P1 Right", "P1 B", "P1 C"}) do
    set_input(name, false)
  end

  if r16(0xff0000) == 2 and r16(0xff0002) == 4 and r16(0xff0004) == 8 then
    if not continue_frame then continue_frame = frame end
    if r8(symbols.genesistan_presentation_readiness) == 0 then
      continue_visible_frames = continue_visible_frames + 1
    end
    if frame >= continue_frame + continue_dwell_frames then finish(); return end
  end
  if frame >= 4000 then finish() end
end)
