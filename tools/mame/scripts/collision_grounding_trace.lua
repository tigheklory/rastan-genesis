-- Automated Stage-1 collision-grounding provenance trace.
--
-- TARGET_PLATFORM=genesis traces the translated native publishers and retained
-- postprocessor. TARGET_PLATFORM=arcade traces the original producer. Both use
-- the same ordered schema and stop after the first class 0x17/0x18 grounding
-- acceptance. No RAM or gameplay state is seeded.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local mem = assert(cpu.spaces["program"])
local state = cpu.state

local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local platform = os.getenv("TARGET_PLATFORM") or "genesis"
local max_frames = tonumber(os.getenv("MAX_FRAMES") or "1000")
local trace_mode = os.getenv("TRACE_MODE") or "combined"
local expected_logical_y = tonumber(os.getenv("EXPECTED_LOGICAL_Y"))
  or (platform == "arcade" and 121 or 129)
assert(platform == "genesis" or platform == "arcade", "TARGET_PLATFORM must be genesis or arcade")
assert(trace_mode == "combined" or trace_mode == "writers" or trace_mode == "consumer",
  "TRACE_MODE must be combined, writers, or consumer")

local cfg
if platform == "genesis" then
  cfg = {
    wram = 0x00ff0000,
    collision = 0x00ff1e00,
    actor_accept_pc = 0x00041528,
    actor_base = 0x00ff02c8,
    native_sel0_lo = 0x0007042a,
    native_sel0_hi = 0x0007055b,
    native_sel12_lo = 0x0007055c,
    native_sel12_hi = 0x0007068f,
    post_lo = 0x0005a46c,
    post_hi = 0x0005a51f,
  }
else
  cfg = {
    wram = 0x0010c000,
    collision = 0x0010de00,
    actor_accept_pc = 0x00041328,
    actor_base = 0x0010c2c8,
    native_sel0_lo = 0,
    native_sel0_hi = 0,
    native_sel12_lo = 0,
    native_sel12_hi = 0,
    post_lo = 0x0005a29c,
    post_hi = 0x0005a34f,
  }
end

local frame = 0
local event_no = 0
local accepted = false
local stop_frame = nil
local closed = false
local keep = {}
local last_actor_collision_read = {}
local collision_tap = nil

local events = assert(io.open(trace_dir .. "/" .. platform .. "_grounding_events.tsv", "w"))
events:write(table.concat({
  "event", "frame", "platform", "kind", "writer_family", "pc", "address",
  "row", "col", "previous", "new", "overwritten", "selector", "segment",
  "group", "strip", "directed_strip", "cell", "descriptor_ptr", "block_ptr",
  "descriptor_word", "source_offset", "collision_source_word", "dest_row",
  "dest_col", "scroll_y", "map_cursor", "actor_index", "actor_class",
  "actor_x", "candidate_y", "accepted_row", "logical_y", "row38_word",
  "row39_word", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
  "a0", "a1", "a2", "a3", "a4", "a5", "a6", "sp", "notes"
}, "\t"), "\n")

local summary = assert(io.open(trace_dir .. "/" .. platform .. "_grounding_summary.txt", "w"))

local function reg(name)
  local ok, value = pcall(function() return state[name].value end)
  if ok and value then return value & 0xffffffff end
  return 0
end

local function pc()
  local value = reg("CURPC")
  if value == 0 then value = reg("PC") end
  return value & 0xffffff
end

local function r8(address)
  local ok, value = pcall(function() return mem:read_u8(address) end)
  return ok and (value & 0xff) or 0
end

local function r16(address)
  local ok, value = pcall(function() return mem:read_u16(address) end)
  return ok and (value & 0xffff) or 0
end

local function r32(address)
  local ok, value = pcall(function() return mem:read_u32(address) end)
  return ok and (value & 0xffffffff) or 0
end

local function signed16(value)
  value = value & 0xffff
  return value >= 0x8000 and value - 0x10000 or value
end

local function row_col(address)
  local index = ((address - cfg.collision) >> 1) & 0x0fff
  return (index >> 6) & 0x3f, index & 0x3f
end

local function writer_family(writer_pc)
  if platform == "genesis" then
    if writer_pc >= cfg.native_sel0_lo and writer_pc <= cfg.native_sel0_hi then return "native_selector0" end
    if writer_pc >= cfg.native_sel12_lo and writer_pc <= cfg.native_sel12_hi then return "native_selector12" end
  end
  if writer_pc >= cfg.post_lo and writer_pc <= cfg.post_hi then return "retained_postprocessor" end
  return platform == "arcade" and "original_arcade_producer" or "other"
end

local collision_last = {}
local collision_frame_last = {}
for watched_row = 38, 39 do
  for watched_col = 0, 63 do
    local watched_address = cfg.collision + watched_row * 0x80 + watched_col * 2
    collision_last[watched_address] = r16(watched_address)
    collision_frame_last[watched_address] = collision_last[watched_address]
  end
end

local function append(values)
  event_no = event_no + 1
  values.event = event_no
  values.frame = frame
  values.platform = platform
  local names = {
    "event", "frame", "platform", "kind", "writer_family", "pc", "address",
    "row", "col", "previous", "new", "overwritten", "selector", "segment",
    "group", "strip", "directed_strip", "cell", "descriptor_ptr", "block_ptr",
    "descriptor_word", "source_offset", "collision_source_word", "dest_row",
    "dest_col", "scroll_y", "map_cursor", "actor_index", "actor_class",
    "actor_x", "candidate_y", "accepted_row", "logical_y", "row38_word",
    "row39_word", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
    "a0", "a1", "a2", "a3", "a4", "a5", "a6", "sp", "notes"
  }
  local out = {}
  for _, name in ipairs(names) do out[#out + 1] = tostring(values[name] or "") end
  events:write(table.concat(out, "\t"), "\n")
  if (event_no % 32) == 0 then events:flush() end
end

local function hex(value, width)
  return string.format("%0" .. tostring(width) .. "X", value & ((width == 4) and 0xffff or 0xffffffff))
end

local function install_collision_tap()
  if trace_mode == "consumer" then return end
  if collision_tap then
    collision_tap:remove()
    collision_tap = nil
  end
  collision_tap = mem:install_write_tap(
  cfg.collision, cfg.collision + 0x1fff, "collision_grounding_rows", function(offset, data, mask)
    -- MAME 0.276 supplies the absolute program-space address here.
    local address = offset & 0xffffff
    if (address & 1) ~= 0 then return data end
    local row, col = row_col(address)
    if row ~= 38 and row ~= 39 then return data end

    local writer_pc = pc()
    local family = writer_family(writer_pc)
    local segment = reg("D4") & 0xffff
    local selector = r16(cfg.wram + 0x10a8)
    local strip = r16(cfg.wram + 0x10ca) & 3
    local directed = strip
    if selector == 1 then directed = (~strip) & 3 end
    local block = reg("D6")
    local desc_ptr = 0
    local desc_word = 0
    if platform == "genesis" and segment < 16 then
      desc_ptr = r32(cfg.wram + 0x1000 + segment * 4)
      if family == "native_selector0" or family == "native_selector12" then
        block = r32(cfg.wram + 0x1040 + segment * 4)
      end
      desc_word = r16(cfg.wram + 0x1080 + segment * 2)
    elseif platform == "arcade" then
      local a3 = reg("A3") & 0xffffff
      if a3 >= 0x10d040 and a3 < 0x10d080 then segment = (a3 - 0x10d040) // 4 end
      desc_ptr = r32(a3)
      block = reg("A2")
      desc_word = r16(reg("A1") & 0xffffff)
    end

    local previous = collision_last[address] or 0
    local new_value = data & 0xffff
    collision_last[address] = new_value
    append({
      kind = "COLLISION_WRITE", writer_family = family, pc = hex(writer_pc, 6),
      address = hex(address, 6), row = row, col = col,
      previous = hex(previous, 4), new = hex(new_value, 4),
      -- Whether this event is later overwritten is determined from the ordered
      -- history after capture; do not confuse that with changing the prior word.
      overwritten = "SEE_ORDERED_HISTORY",
      selector = hex(selector, 4), segment = segment,
      group = r16(cfg.wram + 0x10cc) & 0xffff, strip = strip,
      directed_strip = directed,
      cell = platform == "arcade" and (reg("D2") & 0xffff) or (reg("D5") & 0xffff),
      descriptor_ptr = hex(desc_ptr, 8), block_ptr = hex(block, 8),
      descriptor_word = hex(desc_word, 4), source_offset = hex((function()
        if platform == "arcade" and family == "original_arcade_producer" then
          local cell = reg("D2") & 0xffff
          local source_strip = strip
          if writer_pc >= 0x055a14 then
            if selector ~= 2 then source_strip = (~strip) & 3 end
          return 0x20 + source_strip * 2 + cell * 8
        end
          return 0x20 + strip * 2 + cell * 8
        end
        if platform == "genesis"
            and (family == "native_selector0" or family == "native_selector12") then
          return 0x20 + (reg("D0") & 0xffff)
        end
        return reg("D0")
      end)(), 4),
      collision_source_word = hex(new_value, 4), dest_row = row, dest_col = col,
      scroll_y = hex(r16(cfg.wram + 0x10b0), 4),
      map_cursor = hex(r32(cfg.wram + 0x10a4), 8),
      d0 = hex(reg("D0"), 8), d1 = hex(reg("D1"), 8), d2 = hex(reg("D2"), 8),
      d3 = hex(reg("D3"), 8), d4 = hex(reg("D4"), 8), d5 = hex(reg("D5"), 8),
      d6 = hex(reg("D6"), 8), d7 = hex(reg("D7"), 8),
      a0 = hex(reg("A0"), 8), a1 = hex(reg("A1"), 8), a2 = hex(reg("A2"), 8),
      a3 = hex(reg("A3"), 8), a4 = hex(reg("A4"), 8), a5 = hex(reg("A5"), 8),
      a6 = hex(reg("A6"), 8), sp = hex(reg("SP"), 8),
      notes = "pre-write previous value; PC is runtime PC on Genesis and arcade PC on arcade"
    })
    return data
  end)
  keep[#keep + 1] = collision_tap
end

install_collision_tap()

if trace_mode ~= "writers" then
keep[#keep + 1] = mem:install_read_tap(
  cfg.actor_accept_pc, cfg.actor_accept_pc + 5, "actor_ground_accept", function(offset, data, mask)
    local current_pc = pc()
    if current_pc < cfg.actor_accept_pc or current_pc > cfg.actor_accept_pc + 5 then return nil end
    local a4 = reg("A4") & 0xffffff
    local delta = a4 - cfg.actor_base
    if delta < 0 or (delta % 0x40) ~= 0 then return nil end
    local index = delta // 0x40
    local class = r8(a4 + 1)
    if index < 0 or index >= 29 or (class ~= 0x17 and class ~= 0x18) then return nil end

    local logical_y = r16(cfg.wram + 0x0218)
    local subrow = r16(cfg.wram + 0x10b0) & 7
    local candidate = logical_y
    if subrow ~= 0 then candidate = (logical_y + 8 - subrow) & 0xffff end
    local accepted_row = (((candidate - r16(cfg.wram + 0x10b0)) & 0x01f8) >> 3) & 0x3f
    local actor_x = r16(a4 + 0x16)
    local col = ((actor_x & 0x01f8) >> 3) & 0x3f
    local row38 = r16(cfg.collision + 38 * 0x80 + col * 2)
    local row39 = r16(cfg.collision + 39 * 0x80 + col * 2)

    append({
      kind = "ACTOR_GROUND_ACCEPT", writer_family = "actor_grounding_consumer",
      pc = hex(pc(), 6), address = hex(a4 + 0x1a, 6), row = accepted_row, col = col,
      selector = hex(r16(cfg.wram + 0x10a8), 4),
      scroll_y = hex(r16(cfg.wram + 0x10b0), 4),
      map_cursor = hex(r32(cfg.wram + 0x10a4), 8), actor_index = index,
      actor_class = hex(class, 2), actor_x = hex(actor_x, 4),
      candidate_y = candidate, accepted_row = accepted_row, logical_y = logical_y,
      row38_word = hex(row38, 4), row39_word = hex(row39, 4),
      d0 = hex(reg("D0"), 8), d1 = hex(reg("D1"), 8), d2 = hex(reg("D2"), 8),
      d3 = hex(reg("D3"), 8), d4 = hex(reg("D4"), 8), d5 = hex(reg("D5"), 8),
      d6 = hex(reg("D6"), 8), d7 = hex(reg("D7"), 8),
      a0 = hex(reg("A0"), 8), a1 = hex(reg("A1"), 8), a2 = hex(reg("A2"), 8),
      a3 = hex(reg("A3"), 8), a4 = hex(reg("A4"), 8), a5 = hex(reg("A5"), 8),
      a6 = hex(reg("A6"), 8), sp = hex(reg("SP"), 8),
      notes = "instruction fetch before A4+0x1A logical-Y store"
    })
    if r16(cfg.wram + 0x10b0) == 0x0149 and logical_y == expected_logical_y and not accepted then
      accepted = true
      stop_frame = frame + 90
    end
    return nil
  end)

keep[#keep + 1] = mem:install_read_tap(
  cfg.collision, cfg.collision + 0x1fff, "actor_grounding_collision_reads", function(offset, data, mask)
    local current_pc = pc()
    local address = offset & 0xffffff
    if (address & 1) ~= 0 then return nil end
    local a4 = reg("A4") & 0xffffff
    local delta = a4 - cfg.actor_base
    local index = -1
    local class = 0
    if delta >= 0 and (delta % 0x40) == 0 then
      index = delta // 0x40
      if index >= 0 and index < 29 then class = r8(a4 + 1) end
    end
    local row, col = row_col(address)
    if index >= 0 and (class == 0x17 or class == 0x18) then
      last_actor_collision_read[index] = { address = address, row = row, col = col, value = data & 0xffff }
    end
    if row ~= 38 and row ~= 39 and not (index >= 0 and (class == 0x17 or class == 0x18)) then return nil end
    append({
      kind = "ACTOR_COLLISION_READ", writer_family = "actor_grounding_consumer",
      pc = hex(current_pc, 6), address = hex(address, 6), row = row, col = col,
      new = hex(data & 0xffff, 4), actor_index = index, actor_class = hex(class, 2),
      actor_x = hex(r16(a4 + 0x16), 4), candidate_y = reg("D2") & 0xffff,
      scroll_y = hex(r16(cfg.wram + 0x10b0), 4),
      d0 = hex(reg("D0"), 8), d1 = hex(reg("D1"), 8), d2 = hex(reg("D2"), 8),
      d3 = hex(reg("D3"), 8), d4 = hex(reg("D4"), 8), d5 = hex(reg("D5"), 8),
      d6 = hex(reg("D6"), 8), d7 = hex(reg("D7"), 8),
      a0 = hex(reg("A0"), 8), a1 = hex(reg("A1"), 8), a2 = hex(reg("A2"), 8),
      a3 = hex(reg("A3"), 8), a4 = hex(reg("A4"), 8), a5 = hex(reg("A5"), 8),
      a6 = hex(reg("A6"), 8), sp = hex(reg("SP"), 8),
      notes = "ordered actor grounding collision-map read"
    })
    return nil
  end)
end

local observed_actor_y = {}

local function poll_collision_rows()
  for watched_row = 38, 39 do
    for watched_col = 0, 63 do
      local address = cfg.collision + watched_row * 0x80 + watched_col * 2
      local current = r16(address)
      local previous = collision_frame_last[address]
      if current ~= previous then
        append({
          kind = "COLLISION_FRAME_DIFF", writer_family = "frame_poll_provenance",
          pc = hex(pc(), 6), address = hex(address, 6), row = watched_row, col = watched_col,
          previous = hex(previous, 4), new = hex(current, 4),
          overwritten = previous ~= 0 and "YES" or "NO",
          selector = hex(r16(cfg.wram + 0x10a8), 4),
          group = r16(cfg.wram + 0x10cc) & 0xffff,
          strip = r16(cfg.wram + 0x10ca) & 3,
          scroll_y = hex(r16(cfg.wram + 0x10b0), 4),
          map_cursor = hex(r32(cfg.wram + 0x10a4), 8),
          notes = "external-frame change; PC is sampled at frame boundary, not asserted writer"
        })
        collision_frame_last[address] = current
        collision_last[address] = current
      end
    end
  end
end

local function poll_grounded_actor()
  for index = 0, 28 do
    local actor = cfg.actor_base + index * 0x40
    local class = r8(actor + 1)
    local active = r8(actor)
    local logical_y = r16(actor + 0x1a)
    if active ~= 0 and (class == 0x17 or class == 0x18) and logical_y ~= 0 and logical_y ~= 0x0180 then
      local prior = observed_actor_y[index]
      observed_actor_y[index] = logical_y
      if prior == nil then
        local subrow = r16(cfg.wram + 0x10b0) & 7
        local candidate = logical_y
        if subrow ~= 0 then candidate = (logical_y + 8 - subrow) & 0xffff end
        local accepted_row = (((candidate - r16(cfg.wram + 0x10b0)) & 0x01f8) >> 3) & 0x3f
        local actor_x = r16(actor + 0x16)
        local read = last_actor_collision_read[index]
        local col = read and read.col or (((actor_x & 0x01f8) >> 3) & 0x3f)
        if read then accepted_row = read.row end
        append({
          kind = "ACTOR_FRAME_OBSERVED", writer_family = "frame_poll_fallback",
          pc = hex(pc(), 6), address = hex(actor + 0x1a, 6), row = accepted_row, col = col,
          selector = hex(r16(cfg.wram + 0x10a8), 4),
          scroll_y = hex(r16(cfg.wram + 0x10b0), 4),
          map_cursor = hex(r32(cfg.wram + 0x10a4), 8), actor_index = index,
          actor_class = hex(class, 2), actor_x = hex(actor_x, 4),
          candidate_y = candidate, accepted_row = accepted_row, logical_y = logical_y,
          row38_word = hex(r16(cfg.collision + 38 * 0x80 + col * 2), 4),
          row39_word = hex(r16(cfg.collision + 39 * 0x80 + col * 2), 4),
          notes = "first external-frame observation; fallback if instruction fetch tap is unavailable"
        })
        if r16(cfg.wram + 0x10b0) == 0x0149 and logical_y == expected_logical_y and not accepted then
          accepted = true
          stop_frame = frame + 90
        end
      end
    end
  end
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end

local function set_any(names, on)
  for _, name in ipairs(names) do
    if fields[name] then fields[name]:set_value(on and 1 or 0) end
  end
end

local function drive()
  if platform == "genesis" then
    set_any({"P1 A"}, frame >= 120 and frame <= 132)
    set_any({"P1 Start"}, frame >= 175 and frame <= 187)
  else
    set_any({"Coin 1", "Coin 1 (Impulse)"}, frame >= 300 and frame <= 312)
    set_any({"1 Player Start", "P1 Start"}, frame >= 360 and frame <= 372)
    -- Advance the item/READY sequence, then walk into the first Stage-1 actor.
    set_any({"P1 Button 1"}, frame >= 500 and frame <= 550)
    set_any({"P1 Right"}, frame >= 500)
  end
end

local function close_files(reason)
  if closed then return end
  closed = true
  summary:write("platform=", platform, "\n")
  summary:write("frames=", tostring(frame), "\n")
  summary:write("events=", tostring(event_no), "\n")
  summary:write("actor_accept_seen=", tostring(accepted), "\n")
  summary:write("trace_mode=", trace_mode, "\n")
  summary:write("expected_logical_y=", tostring(expected_logical_y), "\n")
  summary:write("scene=", string.format("%02X", r8(cfg.wram + 0x78a8)), "\n")
  summary:write("state0=", string.format("%04X", r16(cfg.wram)), "\n")
  summary:write("state2=", string.format("%04X", r16(cfg.wram + 2)), "\n")
  summary:write("state4=", string.format("%04X", r16(cfg.wram + 4)), "\n")
  summary:write("stop_reason=", reason, "\n")
  events:flush(); events:close()
  summary:flush(); summary:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  drive()
  -- The Genesis driver can replace program-space handlers during startup. Refresh
  -- the tap after those transitions so later native WRAM publications stay visible.
  if trace_mode ~= "consumer" and (frame == 20 or frame == 100 or frame == 200) then
    install_collision_tap()
  end
  poll_collision_rows()
  poll_grounded_actor()
  if (stop_frame and frame >= stop_frame) or frame >= max_frames then
    close_files(stop_frame and "post_accept_window_complete" or "max_frames")
    machine:exit()
  end
end)

emu.add_machine_stop_notifier(function()
  close_files("machine_stop")
end)

summary:write("# Automated collision grounding trace; no memory/state seeding.\n")
summary:write("initial_row38_nonzero=", tostring((function()
  local count = 0
  for col = 0, 63 do if collision_frame_last[cfg.collision + 38 * 0x80 + col * 2] ~= 0 then count = count + 1 end end
  return count
end)()), "\n")
summary:write("initial_row39_nonzero=", tostring((function()
  local count = 0
  for col = 0, 63 do if collision_frame_last[cfg.collision + 39 * 0x80 + col * 2] ~= 0 then count = count + 1 end end
  return count
end)()), "\n")
summary:flush()
