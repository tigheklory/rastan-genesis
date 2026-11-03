-- Whole-game ORIGINAL ARCADE Rastan actor/PC090OJ semantic sweep.
--
-- This records evidence, not family conclusions.  In particular, actor class,
-- animation state, record selector, and compositor family remain separate fields.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "Rastan maincpu unavailable")
local program = assert(cpu.spaces["program"], "Rastan maincpu program space unavailable")
local main_region = assert(machine.memory.regions[":maincpu"], "Rastan maincpu region unavailable")

local out_dir = assert(os.getenv("LEXICON_OUT"), "LEXICON_OUT is required")
local label = assert(os.getenv("LEXICON_LABEL"), "LEXICON_LABEL is required")
local selector_text = assert(os.getenv("LEXICON_SELECTOR"), "LEXICON_SELECTOR is required")
local selector = assert(tonumber(selector_text), "LEXICON_SELECTOR must be numeric")
local max_frames = tonumber(os.getenv("LEXICON_FRAMES") or "5200")
local A5 = 0x0010c000
local OBJ = 0x00d00000

local out = assert(io.open(out_dir .. "/observations.csv", "w"))
local summary = assert(io.open(out_dir .. "/summary.txt", "w"))
out:write(table.concat({
  "entry_label", "selector", "frame", "state0", "state2", "state4", "round_byte",
  "segment", "sprite_ctrl", "renderer_mode", "block", "actor_index", "actor_address", "active",
  "actor_class", "actor_flags2", "actor_flags3", "actor_state", "record_selector", "actor_mode3e",
  "animation", "world_x", "world_y", "base_code", "flip", "actor_attr",
  "compositor_family", "owned_record_start", "owned_record_count", "piece_records"
}, ","), "\n")

local function r8(address)
  local ok, value = pcall(function() return program:read_u8(address) end)
  return ok and (value & 0xff) or 0
end

local function r16(address)
  local ok, value = pcall(function() return program:read_u16(address) end)
  return ok and (value & 0xffff) or 0
end

local function w8(address, value)
  pcall(function() program:write_u8(address, value & 0xff) end)
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end

local function set_input(name, on)
  if fields[name] then fields[name]:set_value(on and 1 or 0) end
end

local blocks = {
  {name="actor_2c8", offset=0x02c8, count=9},
  {name="actor_508", offset=0x0508, count=2},
  {name="actor_5c8", offset=0x05c8, count=6},
  {name="actor_748", offset=0x0748, count=11},
  {name="actor_8c8", offset=0x08c8, count=5},
}

local function owned_range(block, index, boss_mode)
  if boss_mode then
    if block == "actor_5c8" then
      return 140 + math.min(index, 3) * 10 + math.max(index - 3, 0) * 20,
        (index < 3) and 10 or 20
    elseif block == "actor_748" then
      return 46 + index * 6, 6
    elseif block == "actor_8c8" then
      return 96 + index * 4, 4
    end
    return -1, 0
  end
  if block == "actor_2c8" then
    return 140 + index * 10, (index == 8) and 19 or 10
  elseif block == "actor_508" then
    return 57 + index * 13, 13
  elseif block == "actor_5c8" then
    return 96 + index * 4, 4
  elseif block == "actor_748" then
    return 46 + index, 1
  end
  return -1, 0
end

local function record_string(start_record, count)
  if start_record < 0 or count <= 0 then return "" end
  local pieces = {}
  for record = start_record, start_record + count - 1 do
    local base = OBJ + record * 8
    local w0, y, code, x = r16(base), r16(base + 2), r16(base + 4), r16(base + 6)
    if ((w0 | y | code | x) ~= 0) and y ~= 0x0180 then
      pieces[#pieces + 1] = string.format("%d:%04X:%04X:%04X:%04X", record, w0, y, code, x)
    end
  end
  return table.concat(pieces, "|")
end

local seen = {}
local frames = 0
local observations = 0
local block_hits = {}

local function patch_selector()
  -- Same original-ROM byte used by the established MAME cheat.  Region write is
  -- authoritative; the program-space write is a compatibility fallback.
  pcall(function() main_region:write_u8(0x05ff9f, selector) end)
  pcall(function() program:write_u8(0x05ff9f, selector) end)
end

local function drive()
  set_input("Coin 1", frames >= 120 and frames <= 132)
  set_input("1 Player Start", frames >= 175 and frames <= 187)
  set_input("P1 Right", frames >= 480)
  set_input("P1 Button 1", frames >= 600 and (frames % 113) < 12)
  set_input("P1 Button 2", frames >= 600 and (frames % 157) < 14)
end

local function sample()
  local state0, state2, state4 = r16(A5), r16(A5 + 2), r16(A5 + 4)
  local round_byte = r8(A5 + 0x0118)
  local segment = r16(A5 + 0x013e)
  local sprite_ctrl = r16(0x00380000)
  local renderer_mode = r16(A5 + 0x02a2)
  local boss_mode = renderer_mode == 2
  for _, block in ipairs(blocks) do
    for index = 0, block.count - 1 do
      local actor = A5 + block.offset + index * 0x40
      local active = r8(actor)
      local state = r8(actor + 5)
      local class = r8(actor + 1)
      local selector_value = r8(actor + 6)
      local base_code = r16(actor + 0x1e)
      local family = r8(actor + 0x38)
      local start_record, record_count = owned_range(block.name, index, boss_mode)
      local pieces = record_string(start_record, record_count)
      if active ~= 0 and state ~= 0 and (base_code ~= 0 or pieces ~= "") then
        local key = table.concat({block.name, index, class, selector_value, r8(actor + 0x3e), base_code,
          family, r8(actor + 0x0b), r8(actor + 0x27), pieces}, ":")
        if not seen[key] then
          seen[key] = true
          observations = observations + 1
          block_hits[block.name] = (block_hits[block.name] or 0) + 1
          local fields_out = {
            label, string.format("0x%02X", selector), tostring(frames),
            string.format("0x%04X", state0), string.format("0x%04X", state2),
            string.format("0x%04X", state4), string.format("0x%02X", round_byte),
            string.format("0x%04X", segment), string.format("0x%04X", sprite_ctrl),
            string.format("0x%04X", renderer_mode), block.name, tostring(index),
            string.format("0x%06X", actor),
            string.format("0x%02X", active), string.format("0x%02X", class),
            string.format("0x%02X", r8(actor + 2)), string.format("0x%02X", r8(actor + 3)),
            string.format("0x%02X", state), string.format("0x%02X", selector_value),
            string.format("0x%02X", r8(actor + 0x3e)),
            string.format("0x%02X", r8(actor + 0x0b)),
            string.format("0x%04X", r16(actor + 0x16)),
            string.format("0x%04X", r16(actor + 0x1a)),
            string.format("0x%04X", base_code), string.format("0x%02X", r8(actor + 0x20)),
            string.format("0x%02X", r8(actor + 0x27)), string.format("0x%02X", family),
            tostring(start_record), tostring(record_count), pieces
          }
          out:write(table.concat(fields_out, ","), "\n")
        end
      end
    end
  end
end

local closed = false
local function close()
  if closed then return end
  closed = true
  summary:write(string.format("entry_label=%s\nselector=0x%02X\nframes=%d\nobservations=%d\n",
    label, selector, frames, observations))
  for _, block in ipairs(blocks) do
    summary:write(string.format("%s_unique_observations=%d\n", block.name, block_hits[block.name] or 0))
  end
  summary:write(string.format("final_state=%04X/%04X/%04X\n", r16(A5), r16(A5 + 2), r16(A5 + 4)))
  out:close()
  summary:close()
end

emu.register_frame_done(function()
  frames = frames + 1
  if frames <= 300 then patch_selector() end
  drive()
  if frames >= 200 and (frames % 2) == 0 then
    -- Keep the bounded sweep alive long enough to observe late spawns; this does
    -- not change object identity or graphics semantics.
    w8(A5 + 0x0101, 3)
    w8(A5 + 0x013a, 0x30)
    sample()
  end
  if frames >= max_frames then
    close()
    machine:exit()
  end
end)

emu.register_stop(close)
