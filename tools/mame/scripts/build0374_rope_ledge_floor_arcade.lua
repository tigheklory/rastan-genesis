-- Build 0374 evidence capture: ORIGINAL ARCADE player floor-contact probes.
-- Human play only.  Press M once immediately after landing on the target ledge.

local machine = manager.machine
assert(machine.system.name == "rastan", "requires ORIGINAL ARCADE machine 'rastan'")

local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")

local A5 = 0x0010C000
local PRE_FRAMES, POST_FRAMES = 600, 120
local PROBES = {
  { setup_pc=0x053B6A, debug_setup_pc=0x053B68, pc=0x053B6E, name="center" },
  { setup_pc=0x053C3C, debug_setup_pc=0x053C3A, pc=0x053C40, name="left" },
  { setup_pc=0x053D0E, debug_setup_pc=0x053D0C, pc=0x053D12, name="right" },
}
local AFTER_FLOOR_CALL_PC = 0x05386A

local function reg(name)
  local s = cpu.state[name]
  return s and (s.value & 0xffffffff) or 0
end
local function r16(address)
  local ok, value = pcall(function() return program:read_u16(address & 0xffffff) end)
  return ok and (value & 0xffff) or 0
end
local function hex(value, width) return string.format("%0" .. width .. "X", value) end

local output = assert(io.open(trace_dir .. "/floor_contact_events.tsv", "w"))
local metadata = assert(io.open(trace_dir .. "/trace_metadata.txt", "w"))
local header = {
  "frame", "USER_MARK", "event", "pc", "probe",
  "a5_register", "player_x", "player_y", "player_state",
  "foot_extent_a5_1130", "d6_pending", "probe_x_d1", "probe_y_d2",
  "a0_collision_address", "collision_word", "collision_low7", "branch_result",
  "result_player_y", "result_d6", "result_player_state",
  "result_contact_flags_a5_10CE", "result_ground_flags_a5_1132",
  "result_vertical_a5_10D8", "result_vertical_a5_10DA",
  "a5_013E", "a5_10A8", "a5_10CA", "a5_10CC",
  "foreground_scroll_x", "foreground_scroll_y"
}
output:write(table.concat(header, "\t"), "\n")

metadata:write("platform=ORIGINAL ARCADE\n")
metadata:write("machine=rastan\n")
metadata:write("capture=actual_player_floor_contact_probes\n")
metadata:write("marker_key=M\nmarker_event=USER_MARK\n")
metadata:write("pre_frames=600\npost_frames=120\n")
metadata:write("floor_routine_arcade=0x053B34\n")
metadata:write("lookup_arcade=0x053A2E\n")
metadata:write("probe_read_center=0x053B6E\n")
metadata:write("probe_read_left=0x053C40\n")
metadata:write("probe_read_right=0x053D12\n")
metadata:write("after_floor_call=0x05386A\n")
metadata:write("started=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
metadata:flush()

local marker_code = assert(machine.input:code_from_token("KEYCODE_M"), "KEYCODE_M unavailable")
local frame, marked, marker_prev, mark_frame = 0, false, false, -1
local post_remaining, closed = 0, false
local buffered, pending = {}, {}
local setup = {}
local taps = {}
local probe_events_seen = 0
local debug_log = machine.debugger and machine.debugger.consolelog or nil
local debug_log_index = 0

local function classification(low7)
  if low7 == 1 or low7 == 3 or low7 == 4 or low7 == 7 then return "FLOOR_ACCEPTED" end
  if low7 == 6 then return "SPECIAL_CODE_06" end
  if low7 == 8 then return "SPECIAL_CODE_08" end
  if low7 == 0x7e then return "SPECIAL_CODE_7E" end
  return "FLOOR_REJECTED"
end

local function snapshot_setup(probe_name)
  setup[probe_name] = { d1=reg("D1"), d2=reg("D2"), d6=reg("D6") }
end

local function snapshot_probe(probe_pc, probe_name)
  probe_events_seen = probe_events_seen + 1
  local a0 = reg("A0") & 0xffffff
  local word = r16(a0)
  local before = setup[probe_name] or { d1=0, d2=0, d6=reg("D6") }
  local row = {
    frame=frame, mark=0, event="FLOOR_PROBE", pc=probe_pc, probe=probe_name,
    a5reg=reg("A5") & 0xffffff,
    player_x=r16(A5+0x10BE), player_y=r16(A5+0x10C0),
    player_state=r16(A5+0x10E8), foot=r16(A5+0x1130), d6=before.d6,
    d1=before.d1, d2=before.d2, a0=a0, word=word, low7=word & 0x7f,
    result=classification(word & 0x7f),
    segment=r16(A5+0x013E), selector=r16(A5+0x10A8),
    strip=r16(A5+0x10CA), group=r16(A5+0x10CC),
    scroll_x=r16(A5+0x10AE), scroll_y=r16(A5+0x10B0),
  }
  pending[#pending+1] = row
end

local function format_row(r)
  return table.concat({
    tostring(r.frame), tostring(r.mark or 0), r.event or "",
    hex(r.pc or 0,6), r.probe or "", hex(r.a5reg or 0,6),
    hex(r.player_x or 0,4), hex(r.player_y or 0,4), hex(r.player_state or 0,4),
    hex(r.foot or 0,4), hex(r.d6 or 0,8), hex(r.d1 or 0,8), hex(r.d2 or 0,8),
    hex(r.a0 or 0,6), hex(r.word or 0,4), hex(r.low7 or 0,2), r.result or "",
    hex(r.result_y or 0,4), hex(r.result_d6 or 0,8), hex(r.result_state or 0,4),
    hex(r.result_contact or 0,4), hex(r.result_ground or 0,4),
    hex(r.result_vd8 or 0,4), hex(r.result_vda or 0,4),
    hex(r.segment or 0,4), hex(r.selector or 0,4), hex(r.strip or 0,4), hex(r.group or 0,4),
    hex(r.scroll_x or 0,4), hex(r.scroll_y or 0,4)
  }, "\t")
end

local function retain(row)
  if marked then
    output:write(format_row(row), "\n")
  else
    buffered[#buffered+1] = row
    local oldest = frame - PRE_FRAMES
    while #buffered > 0 and buffered[1].frame < oldest do table.remove(buffered, 1) end
  end
end

local function finalize_floor_call()
  if #pending == 0 then return end
  for _, row in ipairs(pending) do
    row.result_y = r16(A5+0x10C0)
    row.result_d6 = reg("D6")
    row.result_state = r16(A5+0x10E8)
    row.result_contact = r16(A5+0x10CE)
    row.result_ground = r16(A5+0x1132)
    row.result_vd8 = r16(A5+0x10D8)
    row.result_vda = r16(A5+0x10DA)
    retain(row)
  end
  pending = {}
end

local function split_csv(payload)
  local values = {}
  for value in payload:gmatch("[^,]+") do values[#values+1] = value end
  return values
end

local function parse_hex(value) return tonumber(value, 16) or 0 end

local function drain_debug_log()
  for index=debug_log_index+1, debug_log and #debug_log or 0 do
    local line = tostring(debug_log[index])
    local probe_payload = line:match("^B374P,(.*)$")
    local result_payload = line:match("^B374R,(.*)$")
    if probe_payload then
      probe_events_seen = probe_events_seen + 1
      local v = split_csv(probe_payload)
      local word = parse_hex(v[13])
      local before = setup[v[1]] or { d1=0, d2=0, d6=parse_hex(v[9]) }
      local probe_pc = 0
      for _, p in ipairs(PROBES) do if p.name == v[1] then probe_pc = p.pc end end
      pending[#pending+1] = {
        frame=tonumber(v[2]) or frame, mark=0, event="FLOOR_PROBE",
        pc=probe_pc, probe=v[1], a5reg=parse_hex(v[4]),
        player_x=parse_hex(v[5]), player_y=parse_hex(v[6]), player_state=parse_hex(v[7]),
        foot=parse_hex(v[8]), d6=before.d6, d1=before.d1, d2=before.d2,
        a0=parse_hex(v[12]), word=word, low7=word & 0x7f,
        result=classification(word & 0x7f),
        segment=parse_hex(v[14]), selector=parse_hex(v[15]), strip=parse_hex(v[16]),
        group=parse_hex(v[17]), scroll_x=parse_hex(v[18]), scroll_y=parse_hex(v[19]),
      }
    elseif line:match("^B374S,") then
      local v = split_csv(line:match("^B374S,(.*)$"))
      setup[v[1]] = { d1=parse_hex(v[3]), d2=parse_hex(v[4]), d6=parse_hex(v[5]) }
    elseif result_payload then
      local v = split_csv(result_payload)
      for _, row in ipairs(pending) do
        row.result_y=parse_hex(v[3]); row.result_d6=parse_hex(v[4])
        row.result_state=parse_hex(v[5]); row.result_contact=parse_hex(v[6])
        row.result_ground=parse_hex(v[7]); row.result_vd8=parse_hex(v[8])
        row.result_vda=parse_hex(v[9]); retain(row)
      end
      pending = {}
    end
  end
  if debug_log then debug_log_index = #debug_log end
end

if type(program.install_execute_tap) == "function" then
  for _, p in ipairs(PROBES) do
    local pcopy = p
    taps[#taps+1] = program:install_execute_tap(
      pcopy.setup_pc, pcopy.setup_pc, "floor_setup_" .. pcopy.name,
      function() snapshot_setup(pcopy.name) end)
    taps[#taps+1] = program:install_execute_tap(
      pcopy.pc, pcopy.pc, "floor_probe_" .. pcopy.name,
      function() snapshot_probe(pcopy.pc, pcopy.name) end)
  end
  taps[#taps+1] = program:install_execute_tap(
    AFTER_FLOOR_CALL_PC, AFTER_FLOOR_CALL_PC, "after_floor_call", finalize_floor_call)
else
  assert(debug_log, "MAME lacks execute taps; launch with -debug -debugger none")
  for _, p in ipairs(PROBES) do
    -- Debugger actions observe post-instruction state.  Stop on the final
    -- ADD D6,D2 so D1/D2 are complete but the lookup has not clobbered D1.
    cpu.debug:bpset(p.debug_setup_pc, "1", string.format(
      'printf "B374S,%s,%%d,%%08X,%%08X,%%08X\\n",frame,d1,d2,d6; g', p.name))
    local action = string.format(
      'printf "B374P,%s,%%d,%%06X,%%06X,%%04X,%%04X,%%04X,%%04X,%%08X,%%08X,%%08X,%%06X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\\n",frame,pc,a5,w@10D0BE,w@10D0C0,w@10D0E8,w@10D130,d6,d1,d2,a0,w@a0,w@10C13E,w@10D0A8,w@10D0CA,w@10D0CC,w@10D0AE,w@10D0B0; g',
      p.name)
    cpu.debug:bpset(p.pc, "1", action)
  end
  cpu.debug:bpset(AFTER_FLOOR_CALL_PC, "1",
    'printf "B374R,%d,%06X,%04X,%08X,%04X,%04X,%04X,%04X,%04X\\n",frame,pc,w@10D0C0,d6,w@10D0E8,w@10D0CE,w@10D132,w@10D0D8,w@10D0DA; g')
  machine.debugger:command("go")
end

local function marker_row()
  return {
    frame=frame, mark=1, event="USER_MARK", pc=reg("PC") & 0xffffff, probe="",
    a5reg=reg("A5") & 0xffffff,
    player_x=r16(A5+0x10BE), player_y=r16(A5+0x10C0),
    player_state=r16(A5+0x10E8), foot=r16(A5+0x1130), d6=reg("D6"),
    d1=reg("D1"), d2=reg("D2"), a0=reg("A0") & 0xffffff,
    word=0, low7=0, result="MARKER",
    result_y=r16(A5+0x10C0), result_d6=reg("D6"), result_state=r16(A5+0x10E8),
    result_contact=r16(A5+0x10CE), result_ground=r16(A5+0x1132),
    result_vd8=r16(A5+0x10D8), result_vda=r16(A5+0x10DA),
    segment=r16(A5+0x013E), selector=r16(A5+0x10A8),
    strip=r16(A5+0x10CA), group=r16(A5+0x10CC),
    scroll_x=r16(A5+0x10AE), scroll_y=r16(A5+0x10B0),
  }
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_debug_log()
  local down = false
  local ok = pcall(function() down = machine.input:code_pressed(marker_code) end)
  local first_press = ok and down and not marker_prev and not marked
  marker_prev = ok and down or false
  if first_press then
    marked, mark_frame, post_remaining = true, frame, POST_FRAMES
    for _, row in ipairs(buffered) do output:write(format_row(row), "\n") end
    buffered = {}
    output:write(format_row(marker_row()), "\n"); output:flush()
    metadata:write("USER_MARK_frame=" .. tostring(frame) .. "\n"); metadata:flush()
    emu.print_info("USER_MARK floor trace frame=" .. tostring(frame))
  elseif marked and post_remaining > 0 then
    post_remaining = post_remaining - 1
    if post_remaining == 0 then
      output:flush()
      emu.print_info("USER_MARK floor trace window complete; stop MAME when ready")
    end
  end
end)

local function finish()
  if closed then return end
  closed = true
  drain_debug_log()
  finalize_floor_call()
  metadata:write("ended=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
  metadata:write("marked=" .. tostring(marked) .. "\n")
  metadata:write("mark_frame=" .. tostring(mark_frame) .. "\n")
  metadata:write("floor_probe_events_seen=" .. tostring(probe_events_seen) .. "\n")
  metadata:close(); output:close()
end
emu.register_stop(finish)
