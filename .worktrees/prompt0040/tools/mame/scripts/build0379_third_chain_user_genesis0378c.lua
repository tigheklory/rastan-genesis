-- Build 0379 investigation only: user-controlled Genesis Build 0386_c trace.
--
-- This script never supplies controls and never writes emulated memory.  Tighe
-- plays normally, reaches/attaches to the third chain, then presses M once.
-- The first M rising edge is USER_MARK and arms a bounded 720-frame capture.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local input = machine.input
local outdir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")

-- The Build-0386_c rack-advance control is the Genesis six-button MODE input.
-- MAME defaults ctrl1 to the three-button mdpad, so require the caller to use
-- `-ctrl1 md6button` and fail visibly instead of silently offering no MODE key.
local has_p1_mode = false
for _, port in pairs(machine.ioport.ports) do
  for name, _ in pairs(port.fields) do
    if name == "P1 Mode" then has_p1_mode = true end
  end
end
assert(has_p1_mode, "P1 Mode unavailable: relaunch MAME with -ctrl1 md6button")

local states = assert(io.open(outdir .. "/third_chain_states.tsv", "w"))
local probes = assert(io.open(outdir .. "/third_chain_probe_events.tsv", "w"))
local sources = assert(io.open(outdir .. "/third_chain_source_tables.tsv", "w"))
local metadata = assert(io.open(outdir .. "/trace_metadata.txt", "w"))

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function reg(n)
  local s = cpu.state[n]
  return s and (s.value & 0xffffffff) or 0
end

local marker_code = assert(input:code_from_token("KEYCODE_M"), "KEYCODE_M unavailable")
local frame, marked, marker_prev, mark_frame = 0, false, false, -1
local capture_frames = 720
local closed = false
local debuglog = machine.debugger and machine.debugger.consolelog or nil
local debug_index = debuglog and #debuglog or 0

states:write(table.concat({
  "frame", "USER_MARK", "event", "pc", "progression", "map_stream_ptr",
  "selector", "strip", "group", "player_state", "player_substate", "player_x",
  "player_y", "requested_x", "requested_y", "velocity_x", "velocity_y",
  "ground_property", "contact_ptr", "fg_scroll_x", "fg_scroll_y", "special_solid"
}, "\t"), "\n")

probes:write(table.concat({
  "frame", "event", "pc", "d0", "d1_probe_x", "d2_probe_y", "d6_pending",
  "a0", "collision_word", "collision_low7", "progression", "map_stream_ptr",
  "selector", "strip", "group", "player_state", "player_substate", "player_x",
  "player_y", "requested_x", "requested_y", "velocity_x", "velocity_y",
  "ground_property", "contact_ptr", "fg_scroll_x", "fg_scroll_y"
}, "\t"), "\n")

sources:write(table.concat({
  "frame", "table_index", "live_source_ptr", "rebuilt_metatile_ptr",
  "rebuilt_attr", "progression", "map_stream_ptr", "selector", "strip", "group"
}, "\t"), "\n")

metadata:write("purpose=third-chain retained-state identity and blocked-exit transition\n")
metadata:write("rom=dist/rastan-direct/rastan_direct_video_test_build_0386_c.bin\n")
metadata:write("control=user only; no scripted input\n")
metadata:write("memory_writes=NO\n")
metadata:write("marker_key=M\nmarker_event=USER_MARK\n")
metadata:write("capture_frames_after_mark=" .. tostring(capture_frames) .. "\n")
metadata:write("debugger_breakpoints=armed only after USER_MARK\n")
metadata:write("controller1=md6button\n")
metadata:write("required_input_field=P1 Mode\n")
metadata:flush()

local function state_row(event, mark)
  states:write(string.format(
    "%d\t%d\t%s\t%06X\t%04X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%08X\t%04X\t%04X\t%04X\n",
    frame, mark and 1 or 0, event or "", reg("PC") & 0xffffff,
    r16(0xff013e), r32(0xff10c6), r16(0xff10a8), r16(0xff10ca), r16(0xff10cc),
    r16(0xff10e8), r16(0xff10ea), r16(0xff10be), r16(0xff10c0),
    r16(0xff10dc), r16(0xff10de), r16(0xff10d4), r16(0xff10d6),
    r16(0xff1132), r32(0xff1134), r16(0xff10ae), r16(0xff10b0), r16(0xff0242)))
  states:flush()
end

local function source_snapshot()
  for i = 0, 15 do
    sources:write(string.format(
      "%d\t%d\t%08X\t%08X\t%04X\t%04X\t%08X\t%04X\t%04X\t%04X\n",
      frame, i, r32(0xff1000 + i * 4), r32(0xff1040 + i * 4),
      r16(0xff1080 + i * 2), r16(0xff013e), r32(0xff10c6),
      r16(0xff10a8), r16(0xff10ca), r16(0xff10cc)))
  end
  sources:flush()
end

local probe_pcs = {
  [0x053B4A] = "COLLISION_LOOKUP_ENTRY",
  [0x053BAC] = "HEAD_CENTER_RESULT",
  [0x053BE0] = "HEAD_LEFT_RESULT",
  [0x053C14] = "HEAD_RIGHT_RESULT",
  [0x053C8A] = "FEET_CENTER_RESULT",
  [0x053D5C] = "FEET_LEFT_RESULT",
  [0x053E2E] = "FEET_RIGHT_RESULT",
  [0x05396A] = "UP_MOVE_ENTRY",
  [0x053996] = "HEAD_RESULT_FLAGS",
  [0x05399E] = "HEAD_BLOCK_BRANCH",
  [0x0539A0] = "RETRY_SMALLER_MOVE"
}

local taps = {}
local function write_probe(name)
  local a0 = reg("A0") & 0xffffff
  probes:write(string.format(
    "%d\t%s\t%06X\t%08X\t%08X\t%08X\t%08X\t%06X\t%04X\t%02X\t%04X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%08X\t%04X\t%04X\n",
    frame, name, reg("PC") & 0xffffff, reg("D0"), reg("D1"), reg("D2"), reg("D6"),
    a0, r16(a0), r16(a0) & 0x7f, r16(0xff013e), r32(0xff10c6),
    r16(0xff10a8), r16(0xff10ca), r16(0xff10cc), r16(0xff10e8),
    r16(0xff10ea), r16(0xff10be), r16(0xff10c0), r16(0xff10dc), r16(0xff10de),
    r16(0xff10d4), r16(0xff10d6), r16(0xff1132), r32(0xff1134),
    r16(0xff10ae), r16(0xff10b0)))
end

local function arm_probe_capture()
  if type(p.install_execute_tap) == "function" then
    for pc, name in pairs(probe_pcs) do
      local event_name = name
      taps[#taps + 1] = p:install_execute_tap(pc, pc, "third_chain_" .. event_name,
        function() if marked and not closed then write_probe(event_name) end end)
    end
    metadata:write("probe_capture=execute_taps\n")
  else
    assert(debuglog, "launch with -debug -debugger none")
    for pc, name in pairs(probe_pcs) do
      local action = string.format(
        'printf "TC379,%s,%%d,%%06X,%%08X,%%08X,%%08X,%%08X,%%06X,%%04X,%%04X,%%08X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%08X,%%04X,%%04X\\n",frame,pc,d0,d1,d2,d6,a0,w@a0,w@FF013E,l@FF10C6,w@FF10A8,w@FF10CA,w@FF10CC,w@FF10E8,w@FF10EA,w@FF10BE,w@FF10C0,w@FF10DC,w@FF10DE,w@FF1132,l@FF1134,w@FF10AE,w@FF10B0; g',
        name)
      cpu.debug:bpset(pc, "1", action)
    end
    metadata:write("probe_capture=debugger_breakpoints\n")
    machine.debugger:command("go")
  end
  metadata:flush()
end

local function drain_debug_log()
  if not debuglog then return end
  for i = debug_index + 1, #debuglog do
    local line = tostring(debuglog[i])
    local payload = line:match("^(TC379,.*)")
    if payload then
      local fields = {}
      for v in payload:gmatch("[^,]+") do fields[#fields + 1] = v end
      if #fields >= 25 then
        local word = tonumber(fields[10], 16) or 0
        probes:write(table.concat({
          fields[3], fields[2], fields[4], fields[5], fields[6], fields[7], fields[8],
          fields[9], fields[10], string.format("%02X", word & 0x7f), fields[11],
          fields[12], fields[13], fields[14], fields[15], fields[16], fields[17],
          fields[18], fields[19], fields[20], fields[21], "", "", fields[22],
          fields[23], fields[24], fields[25]
        }, "\t"), "\n")
      end
    end
  end
  debug_index = #debuglog
end

local function finish()
  if closed then return end
  drain_debug_log()
  metadata:write("USER_MARK_seen=" .. (marked and "YES" or "NO") .. "\n")
  if marked then metadata:write("USER_MARK_frame=" .. tostring(mark_frame) .. "\n") end
  metadata:write("capture_complete=YES\n")
  metadata:flush()
  states:flush(); probes:flush(); sources:flush()
  closed = true
  emu.print_info("Third-chain trace complete; stop MAME and return the three TSV files plus trace_metadata.txt")
end

emu.register_frame_done(function()
  if closed then return end
  frame = frame + 1
  local down = false
  local ok = pcall(function() down = input:code_pressed(marker_code) end)
  local first_press = ok and down and not marker_prev and not marked
  marker_prev = (ok and down) or false

  if first_press then
    marked = true
    mark_frame = frame
    state_row("USER_MARK", true)
    source_snapshot()
    arm_probe_capture()
    emu.print_info("USER_MARK third-chain trace frame=" .. tostring(frame) .. "; capture armed for 720 frames")
  elseif marked then
    drain_debug_log()
    state_row("", false)
    if ((frame - mark_frame) % 30) == 0 then source_snapshot() end
    if frame - mark_frame >= capture_frames then finish() end
  end
end)

emu.register_stop(function() finish() end)
emu.print_info("Build 0386_c third-chain user trace ready: attach to the third chain, then press M once")
