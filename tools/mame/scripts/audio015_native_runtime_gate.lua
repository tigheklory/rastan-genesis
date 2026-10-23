-- AUDIO-015 permanent-audio runtime gate.
-- Reuses the established gameplay-entry input route and observes the production
-- 68000/Z80 boundary without altering RAM, registers, timing, or gameplay.

local machine = manager.machine
local maincpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local z80 = assert(machine.devices[":genesis_snd_z80"], "missing Genesis Z80")
local mprog = assert(maincpu.spaces["program"], "missing 68000 program space")
local zprog = assert(z80.spaces["program"], "missing Z80 program space")
local zstate = z80.state
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local driver_path = assert(os.getenv("AUDIO015_Z80_BIN"), "AUDIO015_Z80_BIN is required")
local rom_path = assert(os.getenv("AUDIO015_ROM"), "AUDIO015_ROM is required")
local max_frames = tonumber(os.getenv("AUDIO015_MAX_FRAMES") or "1100")
local no_input = os.getenv("AUDIO015_NO_INPUT") == "1"
local seed_source = tonumber(os.getenv("AUDIO015_SEED_SOURCE") or "")
local seed_applied = false

local driver_file = assert(io.open(driver_path, "rb"))
local driver = assert(driver_file:read("*a"))
driver_file:close()
local rom_file = assert(io.open(rom_path, "rb"))
local rom = assert(rom_file:read("*a"))
rom_file:close()

local function zreg(name)
  local item = zstate[name]
  return item and (item.value & 0xffff) or 0
end
local function z8(address) return zprog:read_u8(address) & 0xff end
local function m16(address) return mprog:read_u16(address) & 0xffff end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local events = assert(io.open(trace_dir .. "/audio_runtime_events.tsv", "w"))
events:write("frame\tevent\tz80_pc\tz80_sp\taddress\tdata\tnote\n")
local frame = 0
local taps = {}
local first_invalid_pc = nil
local first_invalid_sp = nil
local first_invalid_address = nil
local command_values = {}
local consumed_values = {}
local command_data_writes = 0
local qhead_writes = 0
local qtail_writes = 0
local active_writes = 0
local active_seen = false
local timer_status_reads = 0
local timer_overflow_reads = 0
local timer_control_writes = 0
local timer_control_at_active = nil
local active_frame = nil
local ym_address_writes = 0
local ym_data_writes = 0
local ym_port0_latch = 0
local timer_register_events = {}
local timer_register_counts = {}
local psg_writes = 0
local banked_reads = 0
local banked_mismatches = 0
local bank_values = {}
local bank_value_count = 0
local min_stream_address = nil
local max_stream_address = nil
local first_stream_bytes = {}
local last_cur = nil
local cur_changes = 0
local loop_source = nil
local loop_seen = false

local function event(kind, address, data, note)
  events:write(string.format("%d\t%s\t%04X\t%04X\t%04X\t%02X\t%s\n",
    frame, kind, zreg("PC"), zreg("SP"), address or 0, data or 0, note or ""))
  events:flush()
end

local function check_pc(address)
  local pc = zreg("PC")
  if pc >= #driver and first_invalid_pc == nil then
    first_invalid_pc = pc
    first_invalid_sp = zreg("SP")
    first_invalid_address = address
    event("INVALID_PC", address, 0, "PC outside uploaded driver")
  end
end

-- Do not install a read tap on the YM2612 status port.  The driver polls that
-- memory-mapped device continuously, and interposing a Lua handler changes the
-- emulated device-access path.  Timer cadence is observed non-invasively from
-- the driver's register-$27 writes below.
taps[#taps + 1] = zprog:install_read_tap(0x8000, 0xffff, "audio015_banked_reads",
  function(address, data, _)
    banked_reads = banked_reads + 1
    local bank = z8(0x1fa6)
    if not bank_values[bank] then
      bank_values[bank] = true
      bank_value_count = bank_value_count + 1
    end
    local source = bank * 0x8000 + (address - 0x8000)
    if loop_source and source >= loop_source then loop_seen = true end
    if min_stream_address == nil or source < min_stream_address then min_stream_address = source end
    if max_stream_address == nil or source > max_stream_address then max_stream_address = source end
    local expected = source < #rom and rom:byte(source + 1) or nil
    if expected ~= data then banked_mismatches = banked_mismatches + 1 end
    if #first_stream_bytes < 24 then
      first_stream_bytes[#first_stream_bytes + 1] = string.format("%06X:%02X", source, data)
    end
    return data
  end)
taps[#taps + 1] = zprog:install_write_tap(0x0000, #driver - 1, "audio015_code_writes",
  function(address, data, _)
    if frame > 3 then event("CODE_WRITE", address, data, "write into uploaded executable") end
    return data
  end)
taps[#taps + 1] = zprog:install_write_tap(0x1fa3, 0x1fa3, "audio015_active",
  function(address, data, _)
    active_writes = active_writes + 1
    if (data & 0xff) ~= 0 then
      active_seen = true
      if active_frame == nil then
        active_frame = frame
        timer_control_at_active = timer_control_writes
      end
    end
    event("ACTIVE_WRITE", address, data, "")
    return data
  end)
taps[#taps + 1] = zprog:install_write_tap(0x1fd1, 0x1fd1, "audio015_qtail",
  function(address, data, _)
    qtail_writes = qtail_writes + 1
    event("QTAIL_WRITE", address, data, "")
    return data
  end)
taps[#taps + 1] = zprog:install_read_tap(0x1fe0, 0x1fef, "audio015_qdata_consume",
  function(address, data, _)
    consumed_values[#consumed_values + 1] = data & 0xff
    event("COMMAND_READ", address, data, "Z80 consumption")
    return data
  end)
taps[#taps + 1] = zprog:install_write_tap(0x4000, 0x4003, "audio015_ym",
  function(address, data, _)
    if address == 0x4000 or address == 0x4002 then
      ym_address_writes = ym_address_writes + 1
      if address == 0x4000 then ym_port0_latch = data & 0xff end
      if (data & 0xff) == 0x27 then timer_control_writes = timer_control_writes + 1 end
    else
      ym_data_writes = ym_data_writes + 1
      if address == 0x4001 and ym_port0_latch >= 0x24 and ym_port0_latch <= 0x27 and #timer_register_events < 64 then
        timer_register_events[#timer_register_events + 1] = string.format("%d:%02X=%02X", frame, ym_port0_latch, data & 0xff)
      end
      if address == 0x4001 and ym_port0_latch >= 0x24 and ym_port0_latch <= 0x27 then
        local key = string.format("%02X=%02X", ym_port0_latch, data & 0xff)
        timer_register_counts[key] = (timer_register_counts[key] or 0) + 1
      end
    end
    return data
  end)
taps[#taps + 1] = zprog:install_write_tap(0x7f11, 0x7f11, "audio015_psg",
  function(_, data, _)
    psg_writes = psg_writes + 1
    return data
  end)

-- These are 68000-side writes through the Genesis Z80 aperture.
taps[#taps + 1] = mprog:install_write_tap(0x00a01fd0, 0x00a01fd1, "audio015_qhead",
  function(address, data, _)
    qhead_writes = qhead_writes + 1
    event("QHEAD_WRITE", address & 0xffff, data, "68000 publication")
    return data
  end)
taps[#taps + 1] = mprog:install_write_tap(0x00a01fe0, 0x00a01fef, "audio015_qdata",
  function(address, data, _)
    command_data_writes = command_data_writes + 1
    command_values[#command_values + 1] = data & 0xff
    event("COMMAND_WRITE", address & 0xffff, data, "68000 publication")
    return data
  end)
local function write_summary(result, reason)
  local commands = {}
  for _, value in ipairs(command_values) do commands[#commands + 1] = string.format("%02X", value) end
  local consumed = {}
  for _, value in ipairs(consumed_values) do consumed[#consumed + 1] = string.format("%02X", value) end
  local out = assert(io.open(trace_dir .. "/audio_runtime_summary.txt", "w"))
  out:write("result=", result, "\nreason=", reason, "\n")
  out:write(string.format("frames=%d\n", frame))
  out:write(string.format("driver_bytes=%d\n", #driver))
  out:write(string.format("driver_input_bytes=%d\n", #driver))
  out:write(string.format("first_invalid_pc=%s\n", first_invalid_pc and string.format("%04X", first_invalid_pc) or "NONE"))
  out:write(string.format("first_invalid_sp=%s\n", first_invalid_sp and string.format("%04X", first_invalid_sp) or "NONE"))
  out:write(string.format("first_invalid_access=%s\n", first_invalid_address and string.format("%04X", first_invalid_address) or "NONE"))
  out:write("command_values=", table.concat(commands, ","), "\n")
  out:write("consumed_values=", table.concat(consumed, ","), "\n")
  out:write(string.format("command_data_writes=%d\nqhead_writes=%d\nqtail_writes=%d\n", command_data_writes, qhead_writes, qtail_writes))
  out:write(string.format("active_writes=%d\nactive_seen=%s\n", active_writes, active_seen and "YES" or "NO"))
  out:write(string.format("timer_status_reads=%d\ntimer_overflow_reads=%d\ntimer_control_writes=%d\n", timer_status_reads, timer_overflow_reads, timer_control_writes))
  out:write(string.format("active_frame=%s\ntimer_control_at_active=%s\n",
    active_frame and tostring(active_frame) or "NONE",
    timer_control_at_active and tostring(timer_control_at_active) or "NONE"))
  out:write(string.format("ym_address_writes=%d\nym_data_writes=%d\npsg_writes=%d\n", ym_address_writes, ym_data_writes, psg_writes))
  out:write("timer_register_events=", table.concat(timer_register_events, ","), "\n")
  local timer_count_rows = {}
  for key, count in pairs(timer_register_counts) do timer_count_rows[#timer_count_rows + 1] = key .. ":" .. tostring(count) end
  table.sort(timer_count_rows)
  out:write("timer_register_counts=", table.concat(timer_count_rows, ","), "\n")
  local banks = {}
  for value, _ in pairs(bank_values) do banks[#banks + 1] = value end
  table.sort(banks)
  local bank_text = {}
  for _, value in ipairs(banks) do bank_text[#bank_text + 1] = string.format("%02X", value) end
  out:write(string.format("banked_reads=%d\nbanked_mismatches=%d\nbank_values=%s\n",
    banked_reads, banked_mismatches, table.concat(bank_text, ",")))
  out:write(string.format("stream_address_min=%s\nstream_address_max=%s\n",
    min_stream_address and string.format("%06X", min_stream_address) or "NONE",
    max_stream_address and string.format("%06X", max_stream_address) or "NONE"))
  out:write("first_stream_bytes=", table.concat(first_stream_bytes, " "), "\n")
  out:write(string.format("stream_pointer_changes=%d\n", cur_changes))
  out:write(string.format("loop_source=%s\nloop_seen=%s\n",
    loop_source and string.format("%06X", loop_source) or "NONE",
    loop_seen and "YES" or "NO"))
  out:write(string.format("final_pc=%04X\nfinal_sp=%04X\nfinal_active=%02X\nfinal_qhead=%02X\nfinal_qtail=%02X\n",
    zreg("PC"), zreg("SP"), z8(0x1fa3), z8(0x1fd0), z8(0x1fd1)))
  out:write(string.format("final_ym_status=%02X\n", z8(0x4000)))
  local music_periods = timer_control_at_active and math.floor((timer_control_writes - timer_control_at_active) / 2) or 0
  local expected_periods = active_frame and math.floor((frame - active_frame) * 1.011 + 0.5) or 0
  out:write(string.format("music_periods=%d\nexpected_music_periods=%d\nmusic_period_error=%d\n",
    music_periods, expected_periods, music_periods - expected_periods))
  out:close()
  events:close()
  machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  if not no_input then
    set_input("Coin 1", frame >= 120 and frame <= 132)
    set_input("P1 A", frame >= 120 and frame <= 132)
    set_input("1 Player Start", frame >= 175 and frame <= 187)
    set_input("P1 Start", frame >= 175 and frame <= 187)
    set_input("P1 Right", frame >= 360)
  end

  check_pc(zreg("PC"))
  local cur = z8(0x1fa0) | (z8(0x1fa1) << 8) | (z8(0x1fa2) << 16)
  if loop_source == nil then
    local candidate = z8(0x1fc3) | (z8(0x1fc4) << 8) | (z8(0x1fc5) << 16)
    if candidate ~= 0 then loop_source = candidate end
  end
  if last_cur ~= nil and cur ~= last_cur then cur_changes = cur_changes + 1 end
  last_cur = cur

  if seed_source and active_seen and not seed_applied then
    local bank = math.floor(seed_source / 0x8000)
    local window = 0x8000 + (seed_source % 0x8000)
    zprog:write_u8(0x1fa0, seed_source & 0xff)
    zprog:write_u8(0x1fa1, (seed_source >> 8) & 0xff)
    zprog:write_u8(0x1fa2, (seed_source >> 16) & 0xff)
    zprog:write_u8(0x1fa4, window & 0xff)
    zprog:write_u8(0x1fa5, (window >> 8) & 0xff)
    zprog:write_u8(0x1fa6, bank & 0xff)
    for bit = 0, 8 do zprog:write_u8(0x6000, (bank >> bit) & 1) end
    seed_applied = true
    event("BOUNDARY_SEED", window, bank, string.format("source=%06X", seed_source))
  end

  if first_invalid_pc ~= nil then
    write_summary("FAIL", "Z80 PC left uploaded executable")
  elseif frame >= max_frames then
    local music_periods = timer_control_at_active and math.floor((timer_control_writes - timer_control_at_active) / 2) or 0
    local expected_periods = active_frame and math.floor((frame - active_frame) * 1.011 + 0.5) or 0
    local pass
    if seed_source then
      pass = seed_applied and first_invalid_pc == nil and banked_reads > 32 and
        banked_mismatches == 0 and bank_value_count >= 2
    else
      pass = active_seen and command_data_writes >= 2 and
        qtail_writes >= 2 and music_periods > 700 and math.abs(music_periods - expected_periods) <= 12 and
        ym_data_writes > 32 and psg_writes > 4 and banked_reads > 32 and
        banked_mismatches == 0 and bank_value_count >= 1 and cur_changes > 8 and loop_seen
    end
    write_summary(pass and "PASS" or "FAIL", pass and "production audio path observed" or "audio activity requirement missing")
  end
end)
