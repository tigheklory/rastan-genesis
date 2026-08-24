-- Deterministic runtime validation for the seven Build-0310 Plane-A residency epochs.
-- It changes only the retained arcade semantic record at the real gameplay installer boundary;
-- the production installer, generated package, DMA path, and LUT are otherwise unmodified.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local state = cpu.state
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local symbols_path = assert(os.getenv("EPOCH_GATE_SYMBOLS"), "EPOCH_GATE_SYMBOLS is required")
local constants_path = assert(os.getenv("EPOCH_GATE_CONSTANTS"), "EPOCH_GATE_CONSTANTS is required")
local target_record = assert(tonumber(os.getenv("EPOCH_GATE_TARGET_RECORD")),
  "EPOCH_GATE_TARGET_RECORD is required")
local target_epoch = assert(tonumber(os.getenv("EPOCH_GATE_TARGET_EPOCH")),
  "EPOCH_GATE_TARGET_EPOCH is required")
local target_package = tonumber(os.getenv("EPOCH_GATE_TARGET_PACKAGE")) or target_epoch
local max_frames = tonumber(os.getenv("EPOCH_GATE_MAX_FRAMES") or "800")
local required_survival_frames = tonumber(os.getenv("EPOCH_GATE_SURVIVAL_FRAMES") or "8")

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
for _, name in ipairs({
    "fg_boundary_install", "fg_boundary_packages", "fg_boundary_active_lut",
    "fg_boundary_conflict_lut",
    "fg_boundary_epoch_transitions", "fg_boundary_pattern_dma_transitions",
    "fg_boundary_active_record", "fg_boundary_active_package",
    "genesistan_current_scene_id",
}) do
  assert(symbols[name], "missing symbol: " .. name)
end
for _, name in ipairs({
    "FG_BOUNDARY_RECORDS", "FG_BOUNDARY_PACKAGES", "FG_BOUNDARY_DESC_OFFSET",
    "FG_BOUNDARY_DESC_BYTES", "FG_BOUNDARY_FIXED_B_OFFSET",
    "FG_BOUNDARY_FIXED_B_MAP_COUNT", "FG_BOUNDARY_SLOT_FIRST",
    "FG_BOUNDARY_SLOT_COUNT", "FG_BOUNDARY_BINARY_LEN",
    "FG_BOUNDARY_CONFLICT_CODE_FIRST", "FG_BOUNDARY_CONFLICT_CODE_COUNT",
}) do
  assert(constants[name], "missing boundary constant: " .. name)
end
assert(target_record >= 0 and target_record < constants.FG_BOUNDARY_RECORDS,
  "target record outside generated table")
assert(target_epoch >= 0 and target_epoch < 7, "target semantic epoch outside generated table")
assert(target_package >= 0 and target_package < constants.FG_BOUNDARY_PACKAGES,
  "target runtime package outside generated table")

local function r8(address) return program:read_u8(address) & 0xff end
local function r16(address) return program:read_u16(address) & 0xffff end
local function r32(address) return program:read_u32(address) & 0xffffffff end
local function reg(name)
  local item = state[name]
  return item and (item.value & 0xffffffff) or 0
end
local function scene() return r8(symbols.genesistan_current_scene_id) end
local function active_lut_slot(code)
  local first = constants.FG_BOUNDARY_CONFLICT_CODE_FIRST
  local limit = first + constants.FG_BOUNDARY_CONFLICT_CODE_COUNT
  if code >= first and code < limit then
    return r16(symbols.fg_boundary_conflict_lut + (code - first) * 2)
  end
  return r16(symbols.fg_boundary_active_lut + code * 2)
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local package_base = symbols.fg_boundary_packages
local record_entry = package_base + target_record * 4
local generated_package = r16(record_entry)
local variants = r16(record_entry + 2)
assert(generated_package == target_package,
  string.format("record %d maps to package %d, expected %d", target_record,
    generated_package, target_package))
assert(variants == 1, "Phase-1 record unexpectedly has variants")

local descriptor = package_base + constants.FG_BOUNDARY_DESC_OFFSET
  + target_package * constants.FG_BOUNDARY_DESC_BYTES
local package_data = package_base + r32(descriptor)
local map_count = r16(descriptor + 4)
local upload_count = r16(descriptor + 6)
local identity_count = r16(descriptor + 8)
local required_patterns = r16(descriptor + 10)
local package_end = package_data + (map_count + upload_count + identity_count) * 4
assert(package_data >= package_base and
       package_end <= package_base + constants.FG_BOUNDARY_BINARY_LEN,
  "selected package span outside generated blob")

local fixed_map = package_base + constants.FG_BOUNDARY_FIXED_B_OFFSET
local frame = 0
local taps = {}
local record_forced = false
local installer_injections = 0
local install_frame = -1
local full_a_lut = false
local full_b_lut = false
local a_lut_mismatch = "none"
local b_lut_mismatch = "none"
local sp_valid = true
local crash_entries = 0
local result_written = false
local summary_path = trace_dir .. "/epoch_gate_summary.txt"
local events = assert(io.open(trace_dir .. "/epoch_gate_events.tsv", "w"))
events:write("frame\tevent\tpc\tsp\tscene\trecord\tepoch\tnote\n")

local function log_event(name, note)
  events:write(string.format("%d\t%s\t%06X\t%08X\t%02X\t%d\t%d\t%s\n",
    frame, name, reg("PC") & 0xffffff, reg("SP"), scene(), target_record,
    target_epoch, note or ""))
  events:flush()
end

-- Follow final ROM vectors because postpatch shift-table reflow can move the linked handlers.
for _, vector in ipairs({0x000008, 0x00000c, 0x000010}) do
  local pc = r32(vector) & 0xffffff
  taps[#taps + 1] = program:install_read_tap(pc, pc + 1, "exception_vector",
    function(_, data, _)
      crash_entries = crash_entries + 1
      log_event("EXCEPTION", string.format("vector=%06X target=%06X", vector, pc))
      return data
    end)
end

local function verify_maps()
  for index = 0, map_count - 1 do
    local pair = package_data + index * 4
    local code, slot = r16(pair), r16(pair + 2)
    local actual = active_lut_slot(code)
    if actual ~= slot then
      a_lut_mismatch = string.format("index=%d code=%04X expected=%04X actual=%04X",
        index, code, slot, actual)
      return false
    end
    if slot ~= 0 and slot >= constants.FG_BOUNDARY_SLOT_FIRST + constants.FG_BOUNDARY_SLOT_COUNT then
      a_lut_mismatch = string.format("index=%d code=%04X invalid_slot=%04X",
        index, code, slot)
      return false
    end
  end
  return true
end

local function verify_fixed_b()
  for index = 0, constants.FG_BOUNDARY_FIXED_B_MAP_COUNT - 1 do
    local pair = fixed_map + index * 4
    local code, slot = r16(pair), r16(pair + 2)
    if slot < 1 or slot >= constants.FG_BOUNDARY_SLOT_FIRST then
      b_lut_mismatch = string.format("index=%d code=%04X invalid_slot=%04X",
        index, code, slot)
      return false
    end
    local actual = active_lut_slot(code)
    if actual ~= slot then
      b_lut_mismatch = string.format("index=%d code=%04X expected=%04X actual=%04X",
        index, code, slot, actual)
      return false
    end
  end
  return true
end

local function write_summary(result, reason)
  if result_written then return end
  result_written = true
  local out = assert(io.open(summary_path, "w"))
  out:write(string.format("result=%s\n", result))
  out:write(string.format("reason=%s\n", reason))
  out:write(string.format("external_frames=%d\n", frame))
  out:write(string.format("target_record=%d\n", target_record))
  out:write(string.format("target_epoch=%d\n", target_epoch))
  out:write(string.format("target_runtime_package=%d\n", target_package))
  out:write(string.format("generated_record_mapping=%d\n", generated_package))
  out:write(string.format("required_patterns=%d\n", required_patterns))
  out:write(string.format("map_count=%d\n", map_count))
  out:write(string.format("upload_count=%d\n", upload_count))
  out:write(string.format("active_record=%d\n", r16(symbols.fg_boundary_active_record)))
  out:write(string.format("active_epoch=%d\n", r16(symbols.fg_boundary_active_package)))
  out:write(string.format("epoch_transitions=%d\n", r32(symbols.fg_boundary_epoch_transitions)))
  out:write(string.format("pattern_dma_transitions=%d\n",
    r32(symbols.fg_boundary_pattern_dma_transitions)))
  out:write(string.format("full_plane_a_lut=%s\n", full_a_lut and "PASS" or "FAIL"))
  out:write(string.format("plane_a_lut_mismatch=%s\n", a_lut_mismatch))
  out:write(string.format("full_fixed_plane_b_lut=%s\n", full_b_lut and "PASS" or "FAIL"))
  out:write(string.format("plane_b_lut_mismatch=%s\n", b_lut_mismatch))
  out:write(string.format("installer_injections=%d\n", installer_injections))
  out:write(string.format("exceptions=%d\n", crash_entries))
  out:write(string.format("sp_valid=%s\n", sp_valid and "YES" or "NO"))
  out:close()
  events:close()
  machine:exit()
end

local function drive_inputs()
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
end

emu.register_frame_done(function()
  frame = frame + 1
  drive_inputs()

  local sp = reg("SP") & 0xffffff
  if sp < 0xe00000 or sp > 0xffffff or (sp & 1) ~= 0 then sp_valid = false end
  if crash_entries > 0 then
    write_summary("FAIL", "exception handler entered")
    return
  end

  -- MAME's translated 68000 execution can bypass instruction-fetch taps. Once the normal
  -- gameplay gate has naturally installed epoch 0, invoke the actual production installer as a
  -- subroutine: push the interrupted PC as the RTS return, preserve the live A5 base, and change
  -- only the retained arcade record. Record 0 therefore exercises the same-epoch no-op path;
  -- records for epochs 1..6 exercise genuine package transitions.
  if not record_forced and scene() == 1 and
     r16(symbols.fg_boundary_active_package) == 0 and
     r32(symbols.fg_boundary_epoch_transitions) >= 1 then
    local a5 = reg("A5") & 0xffffff
    local pc = reg("PC") & 0xffffff
    local call_sp = (reg("SP") - 4) & 0xffffff
    assert(a5 >= 0xff0000 and a5 <= 0xffffff, "A5 not in Genesis WRAM")
    assert(call_sp >= 0xe00000 and call_sp <= 0xfffffc and (call_sp & 1) == 0,
      "cannot inject installer call with invalid SP")
    program:write_u16((a5 + 0x013e) & 0xffffff, target_record)
    program:write_u32(call_sp, pc)
    state["SP"].value = call_sp
    state["PC"].value = symbols.fg_boundary_install
    installer_injections = installer_injections + 1
    record_forced = true
    log_event("INSTALLER_INJECTED", string.format("a5=%06X return=%06X", a5, pc))
  end

  if r16(symbols.fg_boundary_active_record) == target_record and
     r16(symbols.fg_boundary_active_package) == target_package and
     r32(symbols.fg_boundary_epoch_transitions) >= 1 then
    if install_frame < 0 then
      install_frame = frame
      full_a_lut = verify_maps()
      full_b_lut = verify_fixed_b()
      log_event("TARGET_EPOCH_ACTIVE", string.format(
        "patterns=%d maps=%d uploads=%d", required_patterns, map_count, upload_count))
    end
    if frame - install_frame >= required_survival_frames then
      if record_forced and full_a_lut and full_b_lut and sp_valid then
        write_summary("PASS", "target epoch installed through production boundary")
      else
        write_summary("FAIL", "target epoch assertions incomplete")
      end
      return
    end
  end

  if frame >= max_frames then write_summary("FAIL", "maximum frame budget reached") end
end)
