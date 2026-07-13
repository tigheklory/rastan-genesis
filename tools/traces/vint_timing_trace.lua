-- Build 0162 VINT timing trace harness.
-- Tooling-only: observes the Genesis VINT service chain and VDP reg-1 writes.

local machine = manager.machine
local cpu = machine.devices[':maincpu'] or machine.devices['maincpu']
local prog = cpu and cpu.spaces and cpu.spaces['program'] or nil

local trace_dir = os.getenv('TRACE_DIR') or 'states/traces/vint_timing'
local csv_name = os.getenv('VINT_TIMING_CSV') or 'build0162_vint_timing.csv'
local summary_name = os.getenv('VINT_TIMING_SUMMARY') or 'build0162_vint_timing_summary.txt'
local frame_limit = tonumber(os.getenv('VINT_TRACE_FRAMES') or '0') or 0
local auto_start = os.getenv('VINT_AUTO_START') == '1'

os.execute("mkdir -p '" .. trace_dir .. "'")

local csv_path = trace_dir .. '/' .. csv_name
local summary_path = trace_dir .. '/' .. summary_name
local csv = assert(io.open(csv_path, 'w'))
local summary = assert(io.open(summary_path, 'w'))

local frame = 0
local finalized = {}
local frame_stats = {}
local counts = {}
local install_status = {}
local tap_refs = {}
local finished = false
local last_service_entry_cycle = nil
local longest_chain_cycles = nil
local longest_chain_frame = nil
local frames_sampled = 0
local frames_no_service = 0
local frames_entry_no_rte = 0
local reg1_vint_disabled = 0
local ipm_ge6_then_no_service = 0
local input_initialized = false
local p1_a_field = nil
local p1_start_field = nil

local EXEC_POINTS = {
  { addr = 0x000700C2, event = 'VBLANK_SERVICE_ENTRY' },
  { addr = 0x00070108, event = 'VBLANK_SERVICE_TAIL_JMP' },
  { addr = 0x0003A208, event = 'ARCADE_VBLANK_ENTRY' },
  { addr = 0x0003A27A, event = 'ARCADE_VBLANK_CLEAR_MASK' },
  { addr = 0x0003A27E, event = 'ARCADE_VBLANK_RTE' },
  { addr = 0x00071BDC, event = 'PC090OJ_SR_MASK_SAVE' },
  { addr = 0x00071C14, event = 'PC090OJ_SR_RESTORE' },
}

local function bump(name)
  counts[name] = (counts[name] or 0) + 1
end

local function q(v)
  if v == nil then return '' end
  local s = tostring(v)
  if s:find('[,\n\r"]') then
    s = '"' .. s:gsub('"', '""') .. '"'
  end
  return s
end

local function write_csv(fields)
  for i = 1, #fields do
    if i > 1 then csv:write(',') end
    csv:write(q(fields[i]))
  end
  csv:write('\n')
  csv:flush()
end

write_csv({
  'external_frame', 'event', 'pc', 'cycles', 'vcounter', 'hcounter',
  'sr', 'ipm', 'write_addr', 'write_value', 'vdp_reg', 'vdp_value',
  'vint_enabled', 'display_enabled', 'notes'
})

local function hex(v, width)
  if v == nil or v == '' then return '' end
  return string.format('0x%0' .. tostring(width or 6) .. 'X', v & ((1 << ((width or 6) * 4)) - 1))
end

local function reg(name)
  local ok, val = pcall(function()
    if cpu and cpu.state and cpu.state[name] then return cpu.state[name].value end
    return nil
  end)
  if ok and val ~= nil then return val & 0xffffffff end
  return nil
end

local function pc()
  local v = reg('PC')
  if v ~= nil then return v & 0xffffff end
  return nil
end

local function sr()
  local v = reg('SR')
  if v ~= nil then return v & 0xffff end
  return nil
end

local function ipm_from_sr(s)
  if s == nil then return nil end
  return (s >> 8) & 0x7
end

local function cycle_count()
  local ok, val = pcall(function()
    if not cpu then return nil end
    if type(cpu.total_cycles) == 'function' then return cpu:total_cycles() end
    if cpu.total_cycles ~= nil then return cpu.total_cycles end
    if type(cpu.cycles) == 'function' then return cpu:cycles() end
    if cpu.cycles ~= nil then return cpu.cycles end
    return nil
  end)
  if ok and val ~= nil then return tonumber(val) end
  return nil
end

local function machine_time_seconds()
  local ok, val = pcall(function()
    if machine and machine.time and type(machine.time.as_double) == 'function' then
      return machine.time:as_double()
    end
    return nil
  end)
  if ok and val ~= nil then return tonumber(val) end
  return nil
end

local screen = nil
pcall(function()
  if machine.screens then
    screen = machine.screens[':screen'] or machine.screens['screen'] or machine.screens:at(1)
  end
end)

local function screen_pos(which)
  local ok, val = pcall(function()
    if not screen then return nil end
    local member = screen[which]
    if type(member) == 'function' then return screen[which](screen) end
    if member ~= nil then return member end
    return nil
  end)
  if ok and val ~= nil then return tonumber(val) end
  return nil
end

local function screen_frame_number()
  local ok, val = pcall(function()
    if not screen then return nil end
    local member = screen.frame_number
    if type(member) == 'function' then return screen:frame_number() end
    if member ~= nil then return member end
    return nil
  end)
  if ok and val ~= nil then return tonumber(val) end
  return nil
end

local function init_input_fields()
  if input_initialized then return end
  input_initialized = true
  pcall(function()
    for _, port in pairs(machine.ioport.ports) do
      for fname, field in pairs(port.fields) do
        if fname == 'P1 A' then p1_a_field = field end
        if fname == 'P1 Start' then p1_start_field = field end
      end
    end
  end)
end

local function drive_auto_input()
  if not auto_start then return end
  init_input_fields()
  local a_down = frame >= 120 and frame <= 132
  local start_down = frame >= 175 and frame <= 187
  if p1_a_field then p1_a_field:set_value(a_down and 1 or 0) end
  if p1_start_field then p1_start_field:set_value(start_down and 1 or 0) end
end

local function read_u8(addr)
  local ok, val = pcall(function() return prog:read_u8(addr) end)
  if ok and val ~= nil then return val & 0xff end
  return nil
end

local function read_u16(addr)
  local hi = read_u8(addr)
  local lo = read_u8(addr + 1)
  if hi == nil or lo == nil then return nil end
  return ((hi << 8) | lo) & 0xffff
end

local function state_note()
  if not prog then return '' end
  local s0 = read_u16(0x00ff0000)
  local s2 = read_u16(0x00ff0002)
  local s4 = read_u16(0x00ff0004)
  if s0 == nil or s2 == nil or s4 == nil then return '' end
  return string.format('state=%04X/%04X/%04X', s0, s2, s4)
end

local function stats_for(f)
  local st = frame_stats[f]
  if not st then
    st = { service_entry = 0, service_tail = 0, arcade_entry = 0, arcade_rte = 0, reg1_disabled = 0 }
    frame_stats[f] = st
  end
  return st
end

local function log_event(event, pc_override, write_addr, write_value, vdp_reg, vdp_value, vint_enabled, display_enabled, notes)
  local p = pc_override or pc()
  local s = sr()
  local i = ipm_from_sr(s)
  local cyc = cycle_count()
  local vc = screen_pos('vpos')
  local hc = screen_pos('hpos')
  local st = stats_for(frame)

  bump(event)

  if event == 'VBLANK_SERVICE_ENTRY' then
    st.service_entry = st.service_entry + 1
    last_service_entry_cycle = cyc
  elseif event == 'VBLANK_SERVICE_TAIL_JMP' then
    st.service_tail = st.service_tail + 1
  elseif event == 'ARCADE_VBLANK_ENTRY' then
    st.arcade_entry = st.arcade_entry + 1
  elseif event == 'ARCADE_VBLANK_RTE' then
    st.arcade_rte = st.arcade_rte + 1
    if cyc ~= nil and last_service_entry_cycle ~= nil then
      local delta = cyc - last_service_entry_cycle
      if delta >= 0 and (longest_chain_cycles == nil or delta > longest_chain_cycles) then
        longest_chain_cycles = delta
        longest_chain_frame = frame
      end
    end
  elseif event == 'VDP_REG1_WRITE' then
    if vint_enabled == '0' or vint_enabled == 0 or vint_enabled == false then
      st.reg1_disabled = st.reg1_disabled + 1
      reg1_vint_disabled = reg1_vint_disabled + 1
    end
  end

  local extra = notes or ''
  local sf = screen_frame_number()
  local mt = machine_time_seconds()
  if sf ~= nil then extra = extra == '' and ('screen_frame=' .. tostring(sf)) or (extra .. ';screen_frame=' .. tostring(sf)) end
  if mt ~= nil then extra = extra == '' and string.format('time=%.9f', mt) or (extra .. string.format(';time=%.9f', mt)) end
  local sn = state_note()
  if sn ~= '' then
    if extra ~= '' then extra = extra .. ';' .. sn else extra = sn end
  end

  write_csv({
    frame,
    event,
    p and hex(p, 6) or '',
    cyc or '',
    vc or '',
    hc or '',
    s and hex(s, 4) or '',
    i or '',
    write_addr and hex(write_addr, 8) or '',
    write_value and hex(write_value, 4) or '',
    vdp_reg or '',
    vdp_value and hex(vdp_value, 2) or '',
    vint_enabled == nil and '' or (vint_enabled and '1' or '0'),
    display_enabled == nil and '' or (display_enabled and '1' or '0'),
    extra
  })
end

local function decode_vdp_word(word, addr, raw_note)
  local vdp_reg = nil
  local vdp_value = nil
  local vint_enabled = nil
  local display_enabled = nil
  local event = 'VDP_CTRL_WRITE'
  local notes = raw_note or ''

  if (word & 0x8000) ~= 0 then
    vdp_reg = (word >> 8) & 0x1f
    vdp_value = word & 0xff
    if vdp_reg == 1 then
      event = 'VDP_REG1_WRITE'
      vint_enabled = (vdp_value & 0x20) ~= 0
      display_enabled = (vdp_value & 0x40) ~= 0
      if not vint_enabled then
        notes = notes == '' and 'VINT_DISABLED' or (notes .. ';VINT_DISABLED')
      end
    end
  end

  log_event(event, pc(), addr, word, vdp_reg, vdp_value, vint_enabled, display_enabled, notes)
end

local function handle_vdp_ctrl_write(offset, data, mem_mask)
  local addr = offset & 0xffffff
  local d = data or 0
  local mask = mem_mask or 0
  if d > 0xffff then
    decode_vdp_word((d >> 16) & 0xffff, addr, string.format('raw32=%08X mask=%08X word=hi', d & 0xffffffff, mask & 0xffffffff))
    decode_vdp_word(d & 0xffff, addr, string.format('raw32=%08X mask=%08X word=lo', d & 0xffffffff, mask & 0xffffffff))
  else
    decode_vdp_word(d & 0xffff, addr, string.format('mask=%08X', mask & 0xffffffff))
  end
end

local function install_exec_tap(point)
  if not prog or type(prog.install_execute_tap) ~= 'function' then
    install_status[#install_status + 1] = string.format('EXEC %-26s %06X ok=false err=install_execute_tap unavailable', point.event, point.addr)
    return
  end
  local ok, tap = pcall(function()
    return prog:install_execute_tap(point.addr, point.addr, 'vint_' .. point.event, function()
      log_event(point.event, point.addr, nil, nil, nil, nil, nil, nil, 'execute_tap')
    end)
  end)
  if ok and tap then
    tap_refs[#tap_refs + 1] = tap
    install_status[#install_status + 1] = string.format('EXEC %-26s %06X ok=true', point.event, point.addr)
  else
    install_status[#install_status + 1] = string.format('EXEC %-26s %06X ok=false err=%s', point.event, point.addr, tostring(tap))
  end
end

local function install_write_taps()
  if not prog then
    install_status[#install_status + 1] = 'WRITE VDP_CTRL 00C00004-00C00007 ok=false err=no program space'
    return
  end
  local ok, tap = pcall(function()
    return prog:install_write_tap(0x00c00004, 0x00c00007, 'vint_vdp_ctrl_w', handle_vdp_ctrl_write)
  end)
  if ok and tap then
    tap_refs[#tap_refs + 1] = tap
    install_status[#install_status + 1] = 'WRITE VDP_CTRL 00C00004-00C00007 ok=true'
  else
    install_status[#install_status + 1] = 'WRITE VDP_CTRL 00C00004-00C00007 ok=false err=' .. tostring(tap)
  end
end

local function finalize_frame(f)
  if finalized[f] then return end
  finalized[f] = true
  local st = stats_for(f)
  frames_sampled = frames_sampled + 1
  if st.service_entry == 0 then frames_no_service = frames_no_service + 1 end
  if st.service_entry > 0 and st.arcade_rte == 0 then frames_entry_no_rte = frames_entry_no_rte + 1 end

  local s = sr()
  st.frame_end_ipm = ipm_from_sr(s)
  if f > 0 then
    local prev = frame_stats[f - 1]
    if prev and prev.frame_end_ipm and prev.frame_end_ipm >= 6 and st.service_entry == 0 then
      ipm_ge6_then_no_service = ipm_ge6_then_no_service + 1
    end
  end
end

local function write_summary()
  if finished then return end
  finished = true
  finalize_frame(frame)

  summary:write('Build 0162 VINT timing trace summary\n')
  summary:write('CSV: ' .. csv_path .. '\n')
  summary:write('frames_sampled=' .. tostring(frames_sampled) .. '\n')
  summary:write('vblank_service_entries=' .. tostring(counts['VBLANK_SERVICE_ENTRY'] or 0) .. '\n')
  summary:write('vblank_service_tail_exits=' .. tostring(counts['VBLANK_SERVICE_TAIL_JMP'] or 0) .. '\n')
  summary:write('arcade_vblank_entries=' .. tostring(counts['ARCADE_VBLANK_ENTRY'] or 0) .. '\n')
  summary:write('arcade_vblank_rtes=' .. tostring(counts['ARCADE_VBLANK_RTE'] or 0) .. '\n')
  summary:write('frames_with_no_vblank_service=' .. tostring(frames_no_service) .. '\n')
  summary:write('frames_with_entry_but_no_rte=' .. tostring(frames_entry_no_rte) .. '\n')
  summary:write('vdp_reg1_writes=' .. tostring(counts['VDP_REG1_WRITE'] or 0) .. '\n')
  summary:write('vdp_reg1_writes_with_vint_disabled=' .. tostring(reg1_vint_disabled) .. '\n')
  if longest_chain_cycles ~= nil then
    summary:write('longest_service_chain_cycles=' .. tostring(longest_chain_cycles) .. ' frame=' .. tostring(longest_chain_frame) .. '\n')
  else
    summary:write('longest_service_chain_cycles=unavailable\n')
  end
  summary:write('ipm_ge6_frame_end_then_next_frame_no_service=' .. tostring(ipm_ge6_then_no_service) .. '\n')
  summary:write('\nInstall status:\n')
  for _, line in ipairs(install_status) do summary:write(line .. '\n') end
  summary:flush()
  csv:flush()
end

if not cpu or not prog then
  install_status[#install_status + 1] = 'ERROR no maincpu/program space; trace cannot install taps'
else
  for _, point in ipairs(EXEC_POINTS) do install_exec_tap(point) end
  install_write_taps()
end

log_event('TRACE_START', pc(), nil, nil, nil, nil, nil, nil, 'csv=' .. csv_path .. ';summary=' .. summary_path)

_G.vint_timing_stop_subscription = emu.add_machine_stop_notifier(function()
  write_summary()
end)

_G.vint_timing_frame_subscription = emu.register_frame_done(function()
  drive_auto_input()
  finalize_frame(frame)
  frame = frame + 1
  if frame_limit > 0 and frame >= frame_limit then
    write_summary()
    machine:exit()
  end
end)
