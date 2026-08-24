-- Bounded ORIGINAL ARCADE Plane-B progression observation.
-- Evidence only: records semantic transitions, never used as compiler input.

local trace_dir = os.getenv("PLANE_B_TRACE_DIR")
if not trace_dir or trace_dir == "" then
  error("PLANE_B_TRACE_DIR must name an existing project trace directory")
end

local A5_BASE = 0x0010C000
local DESC_TABLE = 0x0003951C
local STREAM_BASE = 0x00050F6B
local STREAM_END = 0x00051009
local cpu = assert(manager.machine.devices[":maincpu"], "rastan maincpu unavailable")
local program = assert(cpu.spaces["program"], "rastan maincpu program space unavailable")

local events = assert(io.open(trace_dir .. "/plane_b_semantic_events.tsv", "w"))
local summary = assert(io.open(trace_dir .. "/plane_b_capture_summary.txt", "w"))
local frame = 0
local event_number = 0
local previous = nil
local closed = false
local route_frames = 0
local min_fg_y, max_fg_y, min_bg_y, max_bg_y

local function r16(a) return program:read_u16(a) & 0xffff end
local function r32(a) return program:read_u32(a) & 0xffffffff end
local function cpu_value(name)
  local state = cpu.state[name]
  return state and (state.value & 0xffffffff) or 0
end
local function cycles()
  local ok, value = pcall(function()
    if type(cpu.total_cycles) == "function" then return cpu:total_cycles() end
    return cpu.total_cycles
  end)
  return ok and (tonumber(value) or 0) or 0
end
local function hex(v, n) return string.format("%0" .. n .. "X", v) end

local function sample()
  local desc = r32(A5_BASE + 0x10fc) & 0xffffff
  local desc_valid = desc >= DESC_TABLE and desc + 5 < 0x00040000
  local desc_delta = desc_valid and (desc - DESC_TABLE) or -1
  local desc_index = desc_valid and math.floor(desc_delta / 6) or -1
  return {
    pc = cpu_value("PC") & 0xffffff,
    a5 = cpu_value("A5") & 0xffffff,
    state0 = r16(A5_BASE + 0x0000), state2 = r16(A5_BASE + 0x0002),
    state4 = r16(A5_BASE + 0x0004), scene = r16(A5_BASE + 0x0118),
    stage = r16(A5_BASE + 0x1242), segment = r16(A5_BASE + 0x013e),
    tm0 = r16(A5_BASE + 0x1386), selector = r16(A5_BASE + 0x10a8),
    previous_selector = r16(A5_BASE + 0x132c),
    strip = r16(A5_BASE + 0x10ca), group = r16(A5_BASE + 0x10cc),
    page_ptr = r32(A5_BASE + 0x10c6) & 0xffffff,
    fg_x = r16(A5_BASE + 0x10ae), fg_y = r16(A5_BASE + 0x10b0),
    bg_x = r16(A5_BASE + 0x10ec), bg_y = r16(A5_BASE + 0x10ee),
    delta_x = r16(A5_BASE + 0x10d8), delta_y = r16(A5_BASE + 0x10da),
    player_x = r16(A5_BASE + 0x10be), player_y = r16(A5_BASE + 0x10c0),
    player_mode = r16(A5_BASE + 0x10e8),
    event_active = r16(A5_BASE + 0x10e8),
    event_flag_1376 = r16(A5_BASE + 0x1376),
    event_flag_1384 = r16(A5_BASE + 0x1384),
    event_flag_13c6 = r16(A5_BASE + 0x13c6),
    desc_cursor = desc, desc_index = desc_index,
    desc_aligned = desc_valid and desc_delta % 6 == 0,
    desc_attr = desc_valid and r16(desc) or 0xffff,
    desc_source = desc_valid and (r32(desc + 2) & 0xffffff) or 0xffffff,
    active_source = r32(0x0010D100) & 0xffffff,
    active_attr = r16(0x0010D104),
    hw_bg_x = r16(0x00C40000), hw_fg_x = r16(0x00C40002),
    hw_bg_y = r16(0x00C20000), hw_fg_y = r16(0x00C20002),
  }
end

local keys = {
  "state0", "state2", "state4", "scene", "stage", "segment", "tm0",
  "selector", "previous_selector", "page_ptr", "player_mode", "event_flag_1376",
  "event_flag_1384", "event_flag_13c6", "desc_cursor", "desc_index", "desc_attr",
  "desc_source", "active_source", "active_attr",
}

events:write(table.concat({
  "event", "frame", "cycles", "pc", "changed", "state0", "state2", "state4",
  "scene", "stage", "segment", "tm0", "selector", "previous_selector", "strip", "group",
  "stream_ptr", "stream_offset", "player_x", "player_y", "player_mode",
  "fg_x_10ae", "fg_y_10b0", "bg_x_10ec", "bg_y_10ee", "delta_x_10d8", "delta_y_10da",
  "hw_c40002_fg_x", "hw_c20002_fg_y", "hw_c40000_bg_x", "hw_c20000_bg_y",
  "event_flag_1376", "event_flag_1384", "event_flag_13c6",
  "desc_cursor_10d0fc", "desc_index", "desc_aligned", "desc_attr", "desc_source",
  "active_source_10d100", "active_attr_10d104",
}, "\t"), "\n")

local function changed(cur)
  if not previous then return "INITIAL" end
  local out = {}
  for _, key in ipairs(keys) do
    if cur[key] ~= previous[key] then out[#out + 1] = key end
  end
  return table.concat(out, ",")
end

local function write_event(cur, why)
  event_number = event_number + 1
  local stream_offset = cur.page_ptr >= STREAM_BASE and cur.page_ptr < STREAM_END
      and cur.page_ptr - STREAM_BASE or -1
  events:write(table.concat({
    tostring(event_number), tostring(frame), tostring(cycles()), hex(cur.pc, 6), why,
    hex(cur.state0, 4), hex(cur.state2, 4), hex(cur.state4, 4), hex(cur.scene, 4),
    hex(cur.stage, 4), hex(cur.segment, 4), hex(cur.tm0, 4), hex(cur.selector, 4),
    hex(cur.previous_selector, 4), hex(cur.strip, 4), hex(cur.group, 4), hex(cur.page_ptr, 6),
    stream_offset >= 0 and tostring(stream_offset) or "NA", hex(cur.player_x, 4),
    hex(cur.player_y, 4), hex(cur.player_mode, 4), hex(cur.fg_x, 4), hex(cur.fg_y, 4),
    hex(cur.bg_x, 4), hex(cur.bg_y, 4), hex(cur.delta_x, 4), hex(cur.delta_y, 4),
    hex(cur.hw_fg_x, 4), hex(cur.hw_fg_y, 4), hex(cur.hw_bg_x, 4), hex(cur.hw_bg_y, 4),
    hex(cur.event_flag_1376, 4), hex(cur.event_flag_1384, 4), hex(cur.event_flag_13c6, 4),
    hex(cur.desc_cursor, 6), tostring(cur.desc_index), cur.desc_aligned and "1" or "0",
    hex(cur.desc_attr, 4), hex(cur.desc_source, 6), hex(cur.active_source, 6),
    hex(cur.active_attr, 4),
  }, "\t"), "\n")
  events:flush()
end

local function update()
  frame = frame + 1
  local cur = sample()
  local route = cur.page_ptr >= STREAM_BASE and cur.page_ptr < STREAM_END
  if route then
    route_frames = route_frames + 1
    min_fg_y = min_fg_y and math.min(min_fg_y, cur.fg_y) or cur.fg_y
    max_fg_y = max_fg_y and math.max(max_fg_y, cur.fg_y) or cur.fg_y
    min_bg_y = min_bg_y and math.min(min_bg_y, cur.bg_y) or cur.bg_y
    max_bg_y = max_bg_y and math.max(max_bg_y, cur.bg_y) or cur.bg_y
  end
  local why = changed(cur)
  if why ~= "" then write_event(cur, why) end
  previous = cur
end

local function close()
  if closed then return end
  closed = true
  events:flush(); events:close()
  summary:write("platform=ORIGINAL ARCADE\n")
  summary:write("machine=rastan\n")
  summary:write("external_frames=" .. frame .. "\n")
  summary:write("semantic_events=" .. event_number .. "\n")
  summary:write("route_frames=" .. route_frames .. "\n")
  summary:write("fg_y_10b0_min=" .. (min_fg_y and hex(min_fg_y, 4) or "NA") .. "\n")
  summary:write("fg_y_10b0_max=" .. (max_fg_y and hex(max_fg_y, 4) or "NA") .. "\n")
  summary:write("bg_y_10ee_min=" .. (min_bg_y and hex(min_bg_y, 4) or "NA") .. "\n")
  summary:write("bg_y_10ee_max=" .. (max_bg_y and hex(max_bg_y, 4) or "NA") .. "\n")
  summary:write("finished=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
  summary:close()
  emu.print_info(string.format("Plane-B bounded capture closed: frames=%d events=%d", frame, event_number))
end

_G.plane_b_progression_frame = emu.add_machine_frame_notifier(function()
  local ok, message = pcall(update)
  if not ok then emu.print_error("Plane-B progression logger: " .. tostring(message)) end
end)
_G.plane_b_progression_stop = emu.add_machine_stop_notifier(close)

emu.print_info("ORIGINAL ARCADE bounded Plane-B logging ACTIVE: " .. trace_dir)
