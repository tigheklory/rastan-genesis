-- PROMPT RG-004 bounded frontend presentation probe.
-- Reuses the established final-life input route, then stops at the Continue
-- dwell. It never supplies gameplay direction or attack input.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local vdp = assert(machine.devices[":gen_vdp"], "missing :gen_vdp")
local vram = assert(vdp.spaces["videoram"], "missing Genesis VRAM space")
local symbols_path = assert(os.getenv("RG004_SYMBOLS"), "RG004_SYMBOLS is required")
local output_path = assert(os.getenv("RG004_OUTPUT"), "RG004_OUTPUT is required")

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
                        "genesistan_current_scene_id",
                        "genesistan_current_pc080sn_tileset_id"}) do
  assert(symbols[name], "missing symbol: " .. name)
end

local function r8(address) return program:read_u8(address) & 0xff end
local function r16(address) return program:read_u16(address) & 0xffff end
local function v16(address) return vram:read_u16(address) & 0xffff end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame = 0
local continue_frame = nil
local finished = false
local function finish()
  if finished then return end
  finished = true
  local out = assert(io.open(output_path, "w"))
  out:write(string.format("frame=%d\nstate=%04X/%04X/%04X\nscene=%02X\ntileset=%02X\n",
    frame, r16(0xff0000), r16(0xff0002), r16(0xff0004),
    r8(symbols.genesistan_current_scene_id),
    r8(symbols.genesistan_current_pc080sn_tileset_id)))
  for line = 0, 3 do
    out:write(string.format("palette_line_%d=", line))
    for entry = 0, 15 do
      out:write(string.format("%04X%s",
        r16(symbols.staged_palette_words + (line * 16 + entry) * 2),
        entry == 15 and "\n" or ","))
    end
  end
  local base_cell = 0x1240 // 4
  local distinct_stage, distinct_vram = {}, {}
  local mismatch = 0
  for row = 0, 9 do
    for col = 0, 11 do
      local cell = base_cell + row * 64 + col
      local sw = r16(symbols.staged_bg_buffer + cell * 2)
      local vw = v16(0xc000 + cell * 2)
      distinct_stage[sw] = true
      distinct_vram[vw] = true
      if sw ~= vw then mismatch = mismatch + 1 end
    end
  end
  local function count(t) local n = 0; for _ in pairs(t) do n = n + 1 end; return n end
  out:write(string.format("continue_stage_distinct=%d\ncontinue_vram_distinct=%d\ncontinue_name_mismatch=%d\n",
    count(distinct_stage), count(distinct_vram), mismatch))
  out:close()
  machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
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
    if frame >= continue_frame + 2 then finish(); return end
  end
  if frame >= 4000 then finish() end
end)
