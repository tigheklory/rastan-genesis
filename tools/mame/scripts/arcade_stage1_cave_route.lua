-- ORIGINAL ARCADE Rastan Stage-1 cave route capture.
-- Observation only: records retained arcade semantic/world state while a human plays.

local trace_dir = os.getenv("CAVE_ROUTE_TRACE_DIR")
if not trace_dir or trace_dir == "" then
  error("CAVE_ROUTE_TRACE_DIR must name an existing project trace directory")
end

local A5_BASE = 0x0010C000
local cpu = manager.machine.devices[":maincpu"]
local program = assert(cpu and cpu.spaces["program"], "rastan maincpu program space unavailable")

local frames_path = trace_dir .. "/arcade_stage1_cave_route_frames.csv"
local events_path = trace_dir .. "/arcade_stage1_cave_route_events.tsv"
local metadata_path = trace_dir .. "/logger_metadata.txt"
local frames = assert(io.open(frames_path, "w"))
local events = assert(io.open(events_path, "w"))
local metadata = assert(io.open(metadata_path, "w"))

local frame = 0
local event_number = 0
local error_count = 0
local closed = false
local previous = nil

local function r16(address)
  return program:read_u16(address) & 0xffff
end

local function r32(address)
  return program:read_u32(address) & 0xffffffff
end

local function signed16(value)
  value = value & 0xffff
  return value >= 0x8000 and value - 0x10000 or value
end

local function total_cycles()
  local ok, value = pcall(function()
    if type(cpu.total_cycles) == "function" then return cpu:total_cycles() end
    return cpu.total_cycles
  end)
  return ok and (tonumber(value) or 0) or 0
end

local function cpu_value(name)
  local state = cpu.state[name]
  return state and (state.value & 0xffffffff) or 0
end

local function read_sample()
  local sample = {
    pc = cpu_value("PC") & 0xffffff,
    a5 = cpu_value("A5") & 0xffffff,
    state0 = r16(A5_BASE + 0x0000),
    state2 = r16(A5_BASE + 0x0002),
    state4 = r16(A5_BASE + 0x0004),
    segment = r16(A5_BASE + 0x013e),
    tm0 = r16(A5_BASE + 0x1386),
    selector = r16(A5_BASE + 0x10a8),
    strip = r16(A5_BASE + 0x10ca),
    group = r16(A5_BASE + 0x10cc),
    page_ptr = r32(A5_BASE + 0x10c6) & 0xffffff,
    player_x = r16(A5_BASE + 0x10be),
    player_y = r16(A5_BASE + 0x10c0),
    fg_x = r16(A5_BASE + 0x10ae),
    fg_y = r16(A5_BASE + 0x10b0),
    bg_x = r16(A5_BASE + 0x10ec),
    bg_y = r16(A5_BASE + 0x10ee),
    direction = r16(A5_BASE + 0x10d0),
    x_accum = r16(A5_BASE + 0x10b8),
    y_accum = r16(A5_BASE + 0x10ba),
    player_mode = r16(A5_BASE + 0x10e8),
    descriptor_base = r32(A5_BASE + 0x10fc) & 0xffffff,
    sources = {},
    blocks = {},
  }
  for index = 0, 15 do
    sample.sources[index + 1] = r32(A5_BASE + 0x1000 + index * 4) & 0xffffff
    sample.blocks[index + 1] = r32(A5_BASE + 0x1040 + index * 4) & 0xffffff
  end
  return sample
end

local function pointer_list(values)
  local out = {}
  for index = 1, 16 do out[index] = string.format("%06X", values[index]) end
  return table.concat(out, " ")
end

local core_fields = {
  "state0", "state2", "state4", "segment", "tm0", "selector", "strip", "group",
  "page_ptr", "player_x", "player_y", "fg_x", "fg_y", "bg_x", "bg_y",
  "direction", "x_accum", "y_accum", "player_mode", "descriptor_base",
}

local function changed_fields(sample)
  if not previous then return "INITIAL" end
  local changed = {}
  for _, name in ipairs(core_fields) do
    if sample[name] ~= previous[name] then changed[#changed + 1] = name end
  end
  for index = 1, 16 do
    if sample.sources[index] ~= previous.sources[index] then
      changed[#changed + 1] = string.format("source%02d", index - 1)
    end
    if sample.blocks[index] ~= previous.blocks[index] then
      changed[#changed + 1] = string.format("block%02d", index - 1)
    end
  end
  return table.concat(changed, ",")
end

local frame_header = {
  "external_frame", "cycles", "pc", "a5_register", "a5_is_10c000",
  "state0", "state2", "state4", "segment", "tm0", "selector", "strip", "group",
  "page_ptr", "player_x_raw", "player_y_raw", "player_x_signed", "player_y_signed",
  "fg_scroll_x_raw", "fg_scroll_y_raw", "fg_scroll_x_signed", "fg_scroll_y_signed",
  "bg_scroll_x_raw", "bg_scroll_y_raw", "bg_scroll_x_signed", "bg_scroll_y_signed",
  "direction", "x_accum", "y_accum", "player_mode", "descriptor_base",
}
for index = 0, 15 do frame_header[#frame_header + 1] = string.format("fg_source_%02d", index) end
for index = 0, 15 do frame_header[#frame_header + 1] = string.format("fg_block_%02d", index) end
frames:write(table.concat(frame_header, ","), "\n")

events:write(table.concat({
  "event_number", "external_frame", "cycles", "pc", "changed_fields", "segment", "tm0",
  "selector", "strip", "group", "page_ptr", "player_x", "player_y", "fg_x", "fg_y",
  "bg_x", "bg_y", "player_mode", "fg_sources_00_15", "fg_blocks_00_15",
}, "\t"), "\n")

metadata:write("platform=ORIGINAL ARCADE\n")
metadata:write("machine=rastan\n")
metadata:write("a5_expected=0x0010C000\n")
metadata:write("player_world_x=a5+0x10BE (proven)\n")
metadata:write("player_world_y=a5+0x10C0 (proven)\n")
metadata:write("fg_scroll_x=a5+0x10AE (proven)\n")
metadata:write("fg_scroll_y=a5+0x10B0 (proven)\n")
metadata:write("bg_scroll_x=a5+0x10EC (proven)\n")
metadata:write("bg_scroll_y=a5+0x10EE (proven)\n")
metadata:write("fg_sources=a5+0x1000..0x103C\n")
metadata:write("fg_rebuilt_block_pointers=a5+0x1040..0x107C\n")
metadata:write("started=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
metadata:flush()

local function write_sample()
  frame = frame + 1
  local sample = read_sample()
  local row = {
    tostring(frame), tostring(total_cycles()), string.format("%06X", sample.pc),
    string.format("%06X", sample.a5), sample.a5 == A5_BASE and "1" or "0",
    string.format("%04X", sample.state0), string.format("%04X", sample.state2),
    string.format("%04X", sample.state4), string.format("%04X", sample.segment),
    string.format("%04X", sample.tm0), string.format("%04X", sample.selector),
    string.format("%04X", sample.strip), string.format("%04X", sample.group),
    string.format("%06X", sample.page_ptr), string.format("%04X", sample.player_x),
    string.format("%04X", sample.player_y), tostring(signed16(sample.player_x)),
    tostring(signed16(sample.player_y)), string.format("%04X", sample.fg_x),
    string.format("%04X", sample.fg_y), tostring(signed16(sample.fg_x)),
    tostring(signed16(sample.fg_y)), string.format("%04X", sample.bg_x),
    string.format("%04X", sample.bg_y), tostring(signed16(sample.bg_x)),
    tostring(signed16(sample.bg_y)), string.format("%04X", sample.direction),
    string.format("%04X", sample.x_accum), string.format("%04X", sample.y_accum),
    string.format("%04X", sample.player_mode), string.format("%06X", sample.descriptor_base),
  }
  for index = 1, 16 do row[#row + 1] = string.format("%06X", sample.sources[index]) end
  for index = 1, 16 do row[#row + 1] = string.format("%06X", sample.blocks[index]) end
  frames:write(table.concat(row, ","), "\n")

  local changed = changed_fields(sample)
  if changed ~= "" then
    event_number = event_number + 1
    events:write(table.concat({
      tostring(event_number), tostring(frame), tostring(total_cycles()), string.format("%06X", sample.pc),
      changed, string.format("%04X", sample.segment), string.format("%04X", sample.tm0),
      string.format("%04X", sample.selector), string.format("%04X", sample.strip),
      string.format("%04X", sample.group), string.format("%06X", sample.page_ptr),
      string.format("%04X", sample.player_x), string.format("%04X", sample.player_y),
      string.format("%04X", sample.fg_x), string.format("%04X", sample.fg_y),
      string.format("%04X", sample.bg_x), string.format("%04X", sample.bg_y),
      string.format("%04X", sample.player_mode), pointer_list(sample.sources), pointer_list(sample.blocks),
    }, "\t"), "\n")
  end
  previous = sample

  if frame % 60 == 0 then frames:flush(); events:flush() end
end

local function close_files()
  if closed then return end
  closed = true
  frames:flush(); events:flush()
  metadata:write("finished=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
  metadata:write("external_frames=" .. tostring(frame) .. "\n")
  metadata:write("events=" .. tostring(event_number) .. "\n")
  metadata:write("logger_errors=" .. tostring(error_count) .. "\n")
  metadata:close(); frames:close(); events:close()
  emu.print_info(string.format("arcade cave route capture closed: frames=%d events=%d", frame, event_number))
end

_G.arcade_cave_route_frame = emu.add_machine_frame_notifier(function()
  local ok, message = pcall(write_sample)
  if not ok then
    error_count = error_count + 1
    emu.print_error("arcade cave route logger: " .. tostring(message))
  end
end)
_G.arcade_cave_route_stop = emu.add_machine_stop_notifier(close_files)

emu.print_info("ORIGINAL ARCADE Stage-1 cave route logging ACTIVE: " .. trace_dir)
