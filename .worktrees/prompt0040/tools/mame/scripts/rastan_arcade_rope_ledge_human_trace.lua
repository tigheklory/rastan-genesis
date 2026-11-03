-- ORIGINAL ARCADE Rastan: human-played missing rope-side ledge capture.
--
-- This script never drives game input.  Tighe plays to the exact location and
-- presses M once.  The first rising edge of M is the authoritative USER_MARK.
-- Only a 120-frame window on either side of that mark is retained.
--
-- Outputs in $TRACE_DIR:
--   rope_ledge_frames.tsv      core state around USER_MARK
--   rope_ledge_user_mark.tsv   prominent same-frame USER_MARK state
--   rope_ledge_terrain.tsv     bounded Layer-A/source/collision neighborhood
--   trace_metadata.txt         capture identity and completion summary

local machine = manager.machine
assert(machine.system.name == "rastan", "this trace is for ORIGINAL ARCADE machine 'rastan'")

local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")

local A5 = 0x0010C000
local LAYER_A = 0x00C08000
local COLLISION = A5 + 0x1E00
local PRE_FRAMES = 120
local POST_FRAMES = 120

local function r16(address) return program:read_u16(address) & 0xffff end
local function r32(address) return program:read_u32(address) & 0xffffffff end
local function s16(value)
  value = value & 0xffff
  return value >= 0x8000 and value - 0x10000 or value
end

local function cpu_value(name)
  local state = cpu.state[name]
  return state and (state.value & 0xffffffff) or 0
end

local frames = assert(io.open(trace_dir .. "/rope_ledge_frames.tsv", "w"))
local marks = assert(io.open(trace_dir .. "/rope_ledge_user_mark.tsv", "w"))
local terrain = assert(io.open(trace_dir .. "/rope_ledge_terrain.tsv", "w"))
local metadata = assert(io.open(trace_dir .. "/trace_metadata.txt", "w"))

local core_header = table.concat({
  "frame", "USER_MARK", "event", "pc", "a5_register",
  "a5_013E", "a5_10A8", "a5_10CA", "a5_10CC",
  "fg_scroll_x", "fg_scroll_y",
  "player_screen_x", "player_screen_y",
  "player_world_ring_x", "player_world_ring_y",
  "collision_probe_row", "collision_probe_col", "collision_probe_word"
}, "\t")

frames:write(core_header, "\n")
marks:write(core_header, "\n")
terrain:write(table.concat({
  "frame", "USER_MARK", "role", "rel_row", "rel_col",
  "logical_row", "logical_col", "row_group", "col_block",
  "live_row_source_ptr", "source_delta_blocks", "source_entry",
  "descriptor_attr", "metatile", "metatile_cell", "layer_a_cell",
  "collision_address", "collision_word"
}, "\t"), "\n")

metadata:write("platform=ORIGINAL ARCADE\n")
metadata:write("machine=rastan\n")
metadata:write("capture=human_play_missing_rope_side_ledge\n")
metadata:write("marker_key=M\n")
metadata:write("marker_event=USER_MARK\n")
metadata:write("pre_frames=120\npost_frames=120\n")
metadata:write("a5_base=0x0010C000\n")
metadata:write("player_screen_raw=a5+0x10BE/a5+0x10C0\n")
metadata:write("player_world_ring=(player_screen-foreground_scroll)&0x01FF\n")
metadata:write("source_table=a5+0x1000..a5+0x103C\n")
metadata:write("layer_a_hw_base=0x00C08000\n")
metadata:write("collision_grid_base=0x0010DE00\n")
metadata:write("started=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
metadata:flush()

local input = machine.input
local marker_code = assert(input:code_from_token("KEYCODE_M"), "KEYCODE_M unavailable")
local marker_prev = false
local frame = 0
local marked = false
local mark_frame = -1
local post_remaining = 0
local pre = {}
local closed = false

local function sample_state(is_mark)
  local screen_x = r16(A5 + 0x10BE)
  local screen_y = r16(A5 + 0x10C0)
  local fg_x = r16(A5 + 0x10AE)
  local fg_y = r16(A5 + 0x10B0)
  local ring_x = (screen_x - fg_x) & 0x01ff
  local ring_y = (screen_y - fg_y) & 0x01ff

  -- Exact address arithmetic of original arcade collision lookup 0x53A2E,
  -- evaluated with the retained player screen/local coordinates as the probe.
  local collision_col = ((((ring_x >> 1) + 8) & 0x00fc) >> 2) & 0x3f
  local collision_row = (ring_y >> 3) & 0x3f
  local collision_word = r16(COLLISION + collision_row * 0x80 + collision_col * 2)

  return {
    frame = frame,
    mark = is_mark and 1 or 0,
    event = is_mark and "USER_MARK" or "",
    pc = cpu_value("PC") & 0xffffff,
    a5 = cpu_value("A5") & 0xffffff,
    segment = r16(A5 + 0x013E),
    selector = r16(A5 + 0x10A8),
    strip = r16(A5 + 0x10CA),
    group = r16(A5 + 0x10CC),
    fg_x = fg_x,
    fg_y = fg_y,
    screen_x = screen_x,
    screen_y = screen_y,
    ring_x = ring_x,
    ring_y = ring_y,
    collision_row = collision_row,
    collision_col = collision_col,
    collision_word = collision_word,
  }
end

local function format_core(s)
  return table.concat({
    tostring(s.frame), tostring(s.mark), s.event,
    string.format("%06X", s.pc), string.format("%06X", s.a5),
    string.format("%04X", s.segment), string.format("%04X", s.selector),
    string.format("%04X", s.strip), string.format("%04X", s.group),
    string.format("%04X", s.fg_x), string.format("%04X", s.fg_y),
    string.format("%04X", s.screen_x), string.format("%04X", s.screen_y),
    string.format("%03X", s.ring_x), string.format("%03X", s.ring_y),
    tostring(s.collision_row), tostring(s.collision_col),
    string.format("%04X", s.collision_word)
  }, "\t")
end

local function resolve_source_cell(s, row, col)
  row = row & 0x3f
  col = col & 0x3f
  local row_group = (row >> 2) & 0x0f
  local col_block = (col >> 2) & 0x0f
  local live_ptr = r32(A5 + 0x1000 + row_group * 4) & 0xffffff
  local current_group = s.group & 0x0f
  local front_col = current_group * 4 + (s.strip & 3)
  local delta = col_block - current_group
  if col > front_col then delta = delta - 16 end
  local source_entry = (live_ptr + delta * 4) & 0xffffff
  local attr = r16(source_entry)
  local metatile = r16(source_entry + 2)
  local metatile_cell = r16(0x00000200 + metatile + (row & 3) * 8 + (col & 3) * 2)
  local ring_index = row * 64 + col
  return row_group, col_block, live_ptr, delta, source_entry, attr, metatile,
    metatile_cell, r16(LAYER_A + ring_index * 2),
    COLLISION + ring_index * 2, r16(COLLISION + ring_index * 2)
end

local function write_terrain(s)
  local player_row = (s.ring_y >> 3) & 0x3f
  local player_col = (s.ring_x >> 3) & 0x3f

  -- Five-by-five is enough to include the player cell and immediately adjacent
  -- 4x4-metatile boundaries.  The collision-probe center is separately tagged.
  for dr = -2, 2 do
    for dc = -2, 2 do
      local row = (player_row + dr) & 0x3f
      local col = (player_col + dc) & 0x3f
      local role = (dr == 0 and dc == 0) and "PLAYER_CELL" or "NEAR_PLAYER"
      if row == s.collision_row and col == s.collision_col then
        role = role .. "+COLLISION_PROBE"
      end
      local rg, cb, live, delta, source, attr, metatile, source_cell,
        layer_cell, collision_address, collision_word = resolve_source_cell(s, row, col)
      terrain:write(table.concat({
        tostring(s.frame), "USER_MARK", role, tostring(dr), tostring(dc),
        tostring(row), tostring(col), tostring(rg), tostring(cb),
        string.format("%06X", live), tostring(delta), string.format("%06X", source),
        string.format("%04X", attr), string.format("%04X", metatile),
        string.format("%04X", source_cell), string.format("%04X", layer_cell),
        string.format("%06X", collision_address), string.format("%04X", collision_word)
      }, "\t"), "\n")
    end
  end

  -- If the exact collision lookup is outside the 5x5 visual neighborhood,
  -- preserve that one authoritative cell as an additional bounded row.
  local dr = (s.collision_row - player_row) & 0x3f
  local dc = (s.collision_col - player_col) & 0x3f
  if dr > 31 then dr = dr - 64 end
  if dc > 31 then dc = dc - 64 end
  if math.abs(dr) > 2 or math.abs(dc) > 2 then
    local row, col = s.collision_row, s.collision_col
    local rg, cb, live, delta, source, attr, metatile, source_cell,
      layer_cell, collision_address, collision_word = resolve_source_cell(s, row, col)
    terrain:write(table.concat({
      tostring(s.frame), "USER_MARK", "COLLISION_PROBE", tostring(dr), tostring(dc),
      tostring(row), tostring(col), tostring(rg), tostring(cb),
      string.format("%06X", live), tostring(delta), string.format("%06X", source),
      string.format("%04X", attr), string.format("%04X", metatile),
      string.format("%04X", source_cell), string.format("%04X", layer_cell),
      string.format("%06X", collision_address), string.format("%04X", collision_word)
    }, "\t"), "\n")
  end
  terrain:flush()
end

emu.register_frame_done(function()
  frame = frame + 1
  local down = false
  local ok = pcall(function() down = input:code_pressed(marker_code) end)
  local is_mark = ok and down and not marker_prev and not marked
  marker_prev = (ok and down) or false

  local s = sample_state(is_mark)
  local line = format_core(s)

  if is_mark then
    marked = true
    mark_frame = frame
    for _, old_line in ipairs(pre) do frames:write(old_line, "\n") end
    frames:write(line, "\n")
    marks:write(line, "\n")
    write_terrain(s)
    frames:flush(); marks:flush()
    post_remaining = POST_FRAMES
    metadata:write("USER_MARK_frame=" .. tostring(frame) .. "\n")
    metadata:flush()
    emu.print_info(string.format(
      "USER_MARK frame=%d segment=%04X selector=%04X strip=%04X group=%04X " ..
      "screen=%04X,%04X world_ring=%03X,%03X collision=%d,%d:%04X",
      frame, s.segment, s.selector, s.strip, s.group, s.screen_x, s.screen_y,
      s.ring_x, s.ring_y, s.collision_row, s.collision_col, s.collision_word))
  elseif marked and post_remaining > 0 then
    frames:write(line, "\n")
    post_remaining = post_remaining - 1
    if post_remaining == 0 then
      frames:flush()
      emu.print_info("USER_MARK capture window complete; stop MAME when ready")
    end
  elseif not marked then
    pre[#pre + 1] = line
    if #pre > PRE_FRAMES then table.remove(pre, 1) end
  end
end)

local function finish()
  if closed then return end
  closed = true
  metadata:write("ended=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
  metadata:write("total_frames=" .. tostring(frame) .. "\n")
  metadata:write("USER_MARK_seen=" .. (marked and "YES" or "NO") .. "\n")
  if marked then metadata:write("USER_MARK_frame=" .. tostring(mark_frame) .. "\n") end
  frames:flush(); marks:flush(); terrain:flush(); metadata:flush()
  frames:close(); marks:close(); terrain:close(); metadata:close()
end

_G.rastan_rope_ledge_human_trace_stop = emu.add_machine_stop_notifier(function()
  pcall(finish)
end)

emu.print_info("ORIGINAL ARCADE rope-ledge human trace armed: press M once for USER_MARK")
