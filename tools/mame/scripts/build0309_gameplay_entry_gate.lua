-- Start-to-gameplay regression gate for generated PC080SN boundary packages.
-- This is crash-prevention evidence, not a visual acceptance test.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local state = cpu.state
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local symbols_path = assert(os.getenv("GAMEPLAY_GATE_SYMBOLS"), "GAMEPLAY_GATE_SYMBOLS is required")
local constants_path = assert(os.getenv("GAMEPLAY_GATE_CONSTANTS"), "GAMEPLAY_GATE_CONSTANTS is required")
local max_frames = tonumber(os.getenv("GAMEPLAY_GATE_MAX_FRAMES") or "1000")
local required_post_entry_frames = tonumber(os.getenv("GAMEPLAY_GATE_SURVIVAL_FRAMES") or "240")

local function parse_symbols(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local address, name = line:match("^([0-9A-Fa-f]+)%s+%S%s+([^%s]+)$")
    if address and name then result[name] = tonumber(address, 16) end
  end
  return result
end

local function parse_constants(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local name, value = line:match("^%.equ%s+([A-Z0-9_]+),%s+([0-9A-Fa-fx]+)")
    if name and value then result[name] = tonumber(value) end
  end
  return result
end

local symbols = parse_symbols(symbols_path)
local constants = parse_constants(constants_path)
local required_symbols = {
  "fg_boundary_install", "fg_boundary_packages", "fg_boundary_active_lut",
  "fg_boundary_epoch_transitions", "fg_boundary_active_record",
  "fg_boundary_active_package", "genesistan_current_scene_id",
}
for _, name in ipairs(required_symbols) do
  assert(symbols[name], "missing symbol: " .. name)
end
local required_constants = {
  "FG_BOUNDARY_DESC_OFFSET", "FG_BOUNDARY_FIXED_B_OFFSET",
  "FG_BOUNDARY_BINARY_LEN", "FG_BOUNDARY_PACKAGES",
}
for _, name in ipairs(required_constants) do
  assert(constants[name], "missing boundary constant: " .. name)
end

local function r8(address)
  return program:read_u8(address) & 0xff
end
local function r16(address)
  return program:read_u16(address) & 0xffff
end
local function r32(address)
  return program:read_u32(address) & 0xffffffff
end
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

local summary_path = trace_dir .. "/gameplay_entry_gate_summary.txt"
local frames = assert(io.open(trace_dir .. "/gameplay_entry_gate_frames.tsv", "w"))
local events = assert(io.open(trace_dir .. "/gameplay_entry_gate_events.tsv", "w"))
frames:write("frame\tpc\tsp\tstate0\tstate2\tstate4\tscene\tactive_record\tactive_package\tepochs\tplayer_x\n")
events:write("frame\tevent\tpc\tsp\tstate0\tstate2\tstate4\tscene\tnote\n")

local frame = 0
local taps = {}
local credit = false
local start = false
local ready = false
local gameplay = false
local fixed_b = false
local record0 = false
local gameplay_install_entries = 0
local bus_errors = 0
local address_errors = 0
local illegal_instructions = 0
local crash_common_entries = 0
local sp_valid = true
local first_gameplay_frame = -1
local install_frame = -1
local player_x_at_entry = nil
local player_x_changed = false
local result_written = false

local function scene()
  return r8(symbols.genesistan_current_scene_id)
end
local function log_event(name, note)
  events:write(string.format("%d\t%s\t%06X\t%08X\t%04X\t%04X\t%04X\t%02X\t%s\n",
    frame, name, reg("PC") & 0xffffff, reg("SP"), r16(0xff0000), r16(0xff0002),
    r16(0xff0004), scene(), note or ""))
  events:flush()
end
local function install_fetch_tap(symbol, event_name, callback)
  local pc = symbols[symbol]
  taps[#taps + 1] = program:install_read_tap(pc, pc + 1, event_name,
    function(_, data, _)
      if callback then callback() end
      log_event(event_name, "instruction fetch")
      return data
    end)
end

install_fetch_tap("fg_boundary_install", "FG_BOUNDARY_INSTALL", function()
  if scene() == 1 then gameplay_install_entries = gameplay_install_entries + 1 end
end)
-- The postpatch shift table can move the late crash-handler section relative to the
-- linker's symbol file. Read the actual ROM vectors so the gate follows the final binary.
local crash_vectors = {
  {pc=r32(0x000008) & 0xffffff, name="BUS_ERROR", count=function() bus_errors = bus_errors + 1 end},
  {pc=r32(0x00000c) & 0xffffff, name="ADDRESS_ERROR", count=function() address_errors = address_errors + 1 end},
  {pc=r32(0x000010) & 0xffffff, name="ILLEGAL_INSTRUCTION", count=function() illegal_instructions = illegal_instructions + 1 end},
}
local crash_region_start = math.min(
  crash_vectors[1].pc, crash_vectors[2].pc, crash_vectors[3].pc)
local crash_region_end = crash_region_start + 0x1000
for _, item in ipairs(crash_vectors) do
  taps[#taps + 1] = program:install_read_tap(item.pc, item.pc + 1, item.name,
    function(_, data, _)
      item.count()
      crash_common_entries = crash_common_entries + 1
      log_event(item.name, string.format("vector target %06X", item.pc))
      return data
    end)
end

local package_base = symbols.fg_boundary_packages
local fixed_map = package_base + constants.FG_BOUNDARY_FIXED_B_OFFSET
local fixed_code = r16(fixed_map)
local fixed_slot = r16(fixed_map + 2)
local desc0 = package_base + constants.FG_BOUNDARY_DESC_OFFSET
local package0_data = package_base + r32(desc0)
local record0_code = r16(package0_data)
local record0_slot = r16(package0_data + 2)

local function active_lut_slot(code)
  return r16(symbols.fg_boundary_active_lut + code * 2)
end

local function write_summary(result, reason)
  if result_written then return end
  result_written = true
  local post_frames = install_frame >= 0 and (frame - install_frame) or 0
  local out = assert(io.open(summary_path, "w"))
  out:write(string.format("result=%s\n", result))
  out:write(string.format("reason=%s\n", reason))
  out:write(string.format("external_frames=%d\n", frame))
  out:write(string.format("credit_accepted=%s\n", credit and "PASS" or "FAIL"))
  out:write(string.format("start_accepted=%s\n", start and "PASS" or "FAIL"))
  out:write(string.format("round1_ready=%s\n", ready and "PASS" or "FAIL"))
  out:write(string.format("fixed_b_install=%s\n", fixed_b and "PASS" or "FAIL"))
  out:write(string.format("record0_plane_a_install=%s\n", record0 and "PASS" or "FAIL"))
  out:write(string.format("gameplay_reached=%s\n", gameplay and "PASS" or "FAIL"))
  out:write(string.format("player_control_observed=%s\n", player_x_changed and "PASS" or "FAIL"))
  out:write(string.format("post_entry_frames=%d\n", post_frames))
  out:write(string.format("required_post_entry_frames=%d\n", required_post_entry_frames))
  out:write(string.format("gameplay_install_entries=%d\n", gameplay_install_entries))
  out:write(string.format("active_record=%04X\n", r16(symbols.fg_boundary_active_record)))
  out:write(string.format("active_package=%04X\n", r16(symbols.fg_boundary_active_package)))
  out:write(string.format("residency_epochs=%d\n", r32(symbols.fg_boundary_epoch_transitions)))
  out:write(string.format("fixed_b_probe=code_%04X_slot_%04X_active_%04X\n",
    fixed_code, fixed_slot, active_lut_slot(fixed_code)))
  out:write(string.format("record0_probe=code_%04X_slot_%04X_active_%04X\n",
    record0_code, record0_slot, active_lut_slot(record0_code)))
  out:write(string.format("address_errors=%d\n", address_errors))
  out:write(string.format("bus_errors=%d\n", bus_errors))
  out:write(string.format("illegal_instructions=%d\n", illegal_instructions))
  out:write(string.format("crash_handler_entries=%d\n", crash_common_entries))
  out:write(string.format("sp_valid=%s\n", sp_valid and "YES" or "NO"))
  out:write(string.format("binary_contract_bytes=%d\n", constants.FG_BOUNDARY_BINARY_LEN))
  out:close()
  frames:close()
  events:close()
  machine:exit()
end

local function drive_inputs()
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
  set_input("P1 Right", frame >= 360)
end

emu.register_frame_done(function()
  frame = frame + 1
  drive_inputs()

  local s0, s2, s4 = r16(0xff0000), r16(0xff0002), r16(0xff0004)
  local current_scene = scene()
  local current_sp = reg("SP") & 0xffffff
  local current_pc = reg("PC") & 0xffffff
  local current_x = r16(0xff10be)
  -- MAME's translated 68000 execution can bypass read taps after an exception.
  -- The final ROM vectors still authoritatively locate the isolated crash section.
  if crash_common_entries == 0 and current_pc >= crash_region_start and current_pc < crash_region_end then
    crash_common_entries = 1
    log_event("CRASH_REGION", string.format("pc=%06X vectors=%06X/%06X/%06X",
      current_pc, crash_vectors[1].pc, crash_vectors[2].pc, crash_vectors[3].pc))
  end
  if current_sp < 0xe00000 or current_sp > 0xffffff or (current_sp & 1) ~= 0 then
    sp_valid = false
  end
  if s0 >= 1 then credit = true end
  if s0 == 2 then start = true end
  if s0 == 2 and s2 == 2 and (s4 == 6 or s4 == 7) then ready = true end
  if current_scene == 1 then
    gameplay = true
    if first_gameplay_frame < 0 then first_gameplay_frame = frame end
  end

  local active_record = r16(symbols.fg_boundary_active_record)
  local active_package = r16(symbols.fg_boundary_active_package)
  local epochs = r32(symbols.fg_boundary_epoch_transitions)
  if active_record == 0 and active_package == 0 and epochs >= 1 then
    if install_frame < 0 then
      install_frame = frame
      player_x_at_entry = current_x
      log_event("PACKAGE0_INSTALLED", string.format("x=%04X epochs=%d", current_x, epochs))
    end
    fixed_b = active_lut_slot(fixed_code) == fixed_slot
    record0 = active_lut_slot(record0_code) == record0_slot
  end
  if player_x_at_entry and current_x ~= player_x_at_entry then player_x_changed = true end

  if (frame % 10) == 0 or frame == install_frame then
    frames:write(string.format("%d\t%06X\t%08X\t%04X\t%04X\t%04X\t%02X\t%04X\t%04X\t%d\t%04X\n",
      frame, reg("PC") & 0xffffff, reg("SP"), s0, s2, s4, current_scene,
      active_record, active_package, epochs, current_x))
    frames:flush()
  end

  local exception_count = bus_errors + address_errors + illegal_instructions + crash_common_entries
  if exception_count > 0 then
    write_summary("FAIL", "exception/crash handler entered")
    return
  end
  if install_frame >= 0 and frame - install_frame >= required_post_entry_frames then
    if credit and start and ready and gameplay and fixed_b and record0 and player_x_changed and sp_valid then
      write_summary("PASS", "READY-to-gameplay package install survived with valid state")
    else
      write_summary("FAIL", "post-entry assertions incomplete")
    end
    return
  end
  if frame >= max_frames then write_summary("FAIL", "maximum frame budget reached") end
end)
