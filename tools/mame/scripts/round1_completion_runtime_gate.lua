-- PROMT-ID-0108 live Round-1 completion/content gate.
-- Normal controller input plus the repository's established "Finish Current
-- Sub-Round Now!" mutation for the two pre-boss boundaries.  The mutation
-- requests completion only; the retained arcade transition code owns teardown,
-- stage/package activation, palette/audio decisions, and boss progression.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local z80 = machine.devices[":genesis_snd_z80"]
local zp = z80 and z80.spaces["program"] or nil
local screen = assert(machine.screens:at(1))
local outdir = assert(os.getenv("R1C_OUTDIR"), "R1C_OUTDIR required")
local symbols_path = assert(os.getenv("R1C_SYMBOLS"), "R1C_SYMBOLS required")
local route = os.getenv("R1C_ROUTE") or "direct"
local max_frames = tonumber(os.getenv("R1C_MAX_FRAMES") or "24000")

local function parse_symbols(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local address, name = line:match("^([0-9A-Fa-f]+)%s+%S%s+([^%s]+)$")
    if address and name then result[name] = tonumber(address, 16) end
  end
  return result
end
local s = parse_symbols(symbols_path)
for _, name in ipairs({"genesistan_current_scene_id", "genesistan_current_pc080sn_tileset_id", "staged_fg_buffer",
  "staged_bg_buffer", "staged_palette_words", "plane_a_resident_logical_rows",
  "fg_boundary_active_record", "fg_boundary_active_package",
  "genesistan_hook_tilemap_bg_blockcopy",
  "genesistan_plane_a_scene_scroll_reseed_native", "genesistan_plane_a_scene_scroll_reseed_native_exit"}) do
  assert(s[name], "missing symbol " .. name)
end
local capture_stageclear = os.getenv("R1C_CAPTURE_STAGECLEAR") == "1"
local debugger_log = machine.debugger and machine.debugger.consolelog or nil
local debugger_log_index = debugger_log and #debugger_log or 0
local stageclear_registers = nil
local stageclear_debug_rows = {}
if capture_stageclear then
  assert(machine.debugger and machine.debugger.consolelog,
    "R1C_CAPTURE_STAGECLEAR requires -debug -debugger none")
  cpu.debug:bpset(s.genesistan_hook_tilemap_bg_blockcopy, "w@ff13aa==a", string.format(
    "save %s/stageclear_hook_entry_bg.bin,%x,1000; printf \"R1C_STAGECLEAR_BLOCK,%%d,%%X,%%X,%%X,%%X,%%X\\n\",frame,a0,a1,d0,d1,d2; g",
    outdir, s.staged_bg_buffer))
  local call_pc = tonumber(os.getenv("R1C_STAGECLEAR_CALL_PC") or "")
  if call_pc then
    cpu.debug:bpset(call_pc, "w@ff13aa==a",
      'printf "R1C_STAGECLEAR_CALL,%d,%08X,%08X,%08X,%08X,%08X,%08X\\n",frame,a0,a1,a2,d0,d1,d2; g')
  end
  local return_pc = tonumber(os.getenv("R1C_STAGECLEAR_RETURN_PC") or "")
  if return_pc then
    cpu.debug:bpset(return_pc, "w@ff13aa==a", string.format(
      "save %s/stageclear_hook_exit_bg.bin,%x,1000; g", outdir, s.staged_bg_buffer))
  end
end
local function drain_stageclear_debugger_log()
  if not capture_stageclear then return end
  for index = debugger_log_index + 1, #debugger_log do
    local line = tostring(debugger_log[index])
    local payload = line:match("^R1C_STAGECLEAR_BLOCK,(.*)$") or
      line:match("^R1C_STAGECLEAR_CALL,(.*)$")
    if payload then
      stageclear_registers = payload
      stageclear_debug_rows[#stageclear_debug_rows + 1] = line
    end
  end
  debugger_log_index = #debugger_log
end

local capture_reseed = os.getenv("R1C_CAPTURE_RESEED") == "1"
if capture_reseed then
  assert(machine.debugger and machine.debugger.consolelog,
    "R1C_CAPTURE_RESEED requires -debug -debugger none")
  local condition = "w@ff1242==16"
  cpu.debug:bpset(s.genesistan_plane_a_scene_scroll_reseed_native, condition, string.format(
    "save %s/staged_before.bin,%x,1000; save %s/reseed_workram_entry.bin,ff0000,1400; save %s/native_bss_entry.bin,ff4000,8700; save %s/active_lut_entry.bin,%x,5000; printf \"R1C_RESEED_ENTRY,%%d,%%X,%%X,%%X,%%X,%%X\\n\",frame,w@ff013e,d@ff1000,d@ff1004,w@ff10a8,w@ff10b0; g",
    outdir, s.staged_fg_buffer, outdir, outdir, outdir, s.fg_boundary_active_lut))
  cpu.debug:bpset(s.genesistan_plane_a_scene_scroll_reseed_native_exit, condition, string.format(
    "save %s/staged_after.bin,%x,1000; save %s/reseed_workram_exit.bin,ff0000,1400; printf \"R1C_RESEED_EXIT,%%d,%%X,%%X,%%X,%%X,%%X\\n\",frame,w@ff013e,d@ff1000,d@ff1004,w@ff10a8,w@ff10b0; g",
    outdir, s.staged_fg_buffer, outdir))
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  if fields[name] then fields[name]:set_value(on and 1 or 0) end
end

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local A5 = 0x00ff0000
local function progression_marker() return r8(A5 + 0x1243) end
local function stage() return r16(A5 + 0x1242) end
local function round() return r8(A5 + 0x0118) end
local function scene() return r8(s.genesistan_current_scene_id) end
local function gameplay() return scene() == 1 and r16(A5) == 2 end

os.execute('mkdir -p "' .. outdir .. '"')
local events = assert(io.open(outdir .. "/events.tsv", "w"))
events:write("frame\tevent\tround\tprogression_marker\tstage\trecord\tactive_record\tpackage\tend_owner\tend_state\tend_timer\tplayer_state\n")
local frame, last_marker, marker_at = 0, -1, 0
local finish_requests, last_finish_request = 0, -10000
local torches_seen, torch_changes = false, 0
local torch_last = {}
local end_states, end_entry, large_art, round2 = {}, false, false, false
local scene_clear_command, round2_ready = false, false
local stageclear_bg_writes = 0
local boss_scene_converged, boss_buffers_dumped = false, false
local presentation_captured = {}
local finished = false

local torch_cells = {
  {10,47,43}, {10,15,43}, {11,47,44}, {11,15,44},
  {12,47,45}, {12,15,45}, {11,48,44}, {10,16,43},
  {12,48,45}, {11,16,44}, {13,48,46}, {12,16,45},
}
local function log(event)
  events:write(string.format("%d\t%s\t%02X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
    frame, event, round(), progression_marker(), stage(), r16(A5 + 0x013e),
    r16(s.fg_boundary_active_record), r16(s.fg_boundary_active_package),
    r16(A5 + 0x13d8), r16(A5 + 0x13da), r16(A5 + 0x13dc), r16(A5 + 0x10e8)))
  events:flush()
end
local taps = {}
if zp then
  taps[#taps + 1] = zp:install_read_tap(0x1fe0, 0x1fef, "r1_scene_clear_command",
    function(_, data, _)
      if (data & 0xff) == 0x27 then
        scene_clear_command = true
        log("SCENE_CLEAR_COMMAND_27")
      end
      return data
    end)
end
taps[#taps + 1] = p:install_write_tap(
  s.staged_bg_buffer, s.staged_bg_buffer + 0x0fff, "r1_stageclear_bg_stage",
  function(_, data, _)
    if r16(A5 + 0x13aa) == 10 then stageclear_bg_writes = stageclear_bg_writes + 1 end
    return data
  end)
local function sample_torches()
  local exact = true
  for i, cell in ipairs(torch_cells) do
    local row, col, logical_plus_one = cell[1], cell[2], cell[3]
    if r8(s.plane_a_resident_logical_rows + row) ~= logical_plus_one then exact = false end
    local word = r16(s.staged_fg_buffer + row * 128 + col * 2)
    if torch_last[i] and torch_last[i] ~= word then torch_changes = torch_changes + 1 end
    torch_last[i] = word
  end
  if exact then torches_seen = true end
end
local function dump_words(path, address, count)
  local f = assert(io.open(path, "wb"))
  for i = 0, count - 1 do f:write(string.pack(">I2", r16(address + i * 2))) end
  f:close()
end
local function dump_vram_names(path, base)
  -- Read the real Mega Drive VRAM through the VDP data port.  The exposed
  -- :gen_vdp videoram space is only the 16-KiB Mode-4 compatibility view.
  p:write_u16(0x00c00004, 0x8f02)
  p:write_u16(0x00c00004, base & 0x3fff)
  p:write_u16(0x00c00004, (base >> 14) & 3)
  local f = assert(io.open(path, "wb"))
  for _ = 0, 2047 do
    local word = p:read_u16(0x00c00000) & 0xffff
    f:write(string.char((word >> 8) & 0xff, word & 0xff))
  end
  f:close()
end
local function dump_vram(path)
  p:write_u16(0x00c00004, 0x8f02)
  p:write_u16(0x00c00004, 0)
  p:write_u16(0x00c00004, 0)
  local f = assert(io.open(path, "wb"))
  for _ = 0, 32767 do
    local word = p:read_u16(0x00c00000) & 0xffff
    f:write(string.char((word >> 8) & 0xff, word & 0xff))
  end
  f:close()
end
local function dump_cram(path)
  -- Terminal diagnostic read; each presentation snapshot is taken only once.
  p:write_u16(0x00c00004, 0x0000)
  p:write_u16(0x00c00004, 0x0020)
  local f = assert(io.open(path, "wb"))
  for _ = 0, 63 do
    local word = p:read_u16(0x00c00000) & 0xffff
    f:write(string.char((word >> 8) & 0xff, word & 0xff))
  end
  f:close()
end
local function sample_boss_scene()
  if scene() == 1 and r8(s.genesistan_current_pc080sn_tileset_id) == 1 and
     r16(A5 + 0x013e) >= 0x0017 and
     r16(s.fg_boundary_active_record) == 0x0016 and
     r16(s.fg_boundary_active_package) == 0x0005 and torches_seen then
    boss_scene_converged = true
    if not boss_buffers_dumped then
      dump_words(outdir .. "/boss_staged_plane_a.bin", s.staged_fg_buffer, 2048)
      dump_words(outdir .. "/boss_staged_plane_b.bin", s.staged_bg_buffer, 2048)
      dump_vram_names(outdir .. "/boss_vram_plane_a.bin", 0xe000)
      dump_vram_names(outdir .. "/boss_vram_plane_b.bin", 0xc000)
      dump_vram(outdir .. "/boss_vram.bin")
      pcall(function() screen:snapshot(outdir .. "/boss_scene.png") end)
      boss_buffers_dumped = true
      log("BOSS_SCENE_CONVERGED")
    end
  end
end
local function sample_stageclear_art()
  -- The R1 descriptor at 0x5635E targets PC080SN BG C-window 0xC00A28.
  -- The native block-copy hook maps that 14x16 rectangle to Plane B row 10,
  -- column 10.  Inspect that semantic destination, not the unrelated ending
  -- surface used by the superseded observer.
  local distinct, nonblank = {}, 0
  for row = 10, 23 do
    for col = 10, 25 do
      local word = r16(s.staged_bg_buffer + (row * 64 + col) * 2)
      distinct[word] = true
      if (word & 0x07ff) ~= 0 then nonblank = nonblank + 1 end
    end
  end
  local count = 0 for _ in pairs(distinct) do count = count + 1 end
  if count >= 16 and nonblank >= 64 then large_art = true end
end
local function capture_presentation_state(state)
  if presentation_captured[state] then return end
  presentation_captured[state] = true
  local prefix = string.format("%s/presentation_state_%02d", outdir, state)
  dump_words(prefix .. "_staged_plane_a.bin", s.staged_fg_buffer, 2048)
  dump_words(prefix .. "_staged_plane_b.bin", s.staged_bg_buffer, 2048)
  dump_words(prefix .. "_staged_palette.bin", s.staged_palette_words, 64)
  dump_cram(prefix .. "_cram.bin")
  dump_vram_names(prefix .. "_vram_plane_a.bin", 0xe000)
  dump_vram_names(prefix .. "_vram_plane_b.bin", 0xc000)
  dump_vram(prefix .. "_vram.bin")
  pcall(function() screen:snapshot(prefix .. ".png") end)
  -- State 9 still owns the just-finished boss display.  State 10 performs the
  -- Stage Clear producers; state 11 is the first stable post-producer frame.
  if state == 11 then sample_stageclear_art() end
  log(string.format("ROUND_PRESENTATION_STATE_%d", state))
end
local function sample_scene_clear_queue()
  if scene_clear_command or not zp then return end
  for address = 0x1fe0, 0x1fef do
    local value = zp:read_u8(address) & 0xff
    if value == 0x27 and not scene_clear_command then
      scene_clear_command = true
      log("SCENE_CLEAR_COMMAND_27")
      return
    end
  end
end
local function staged_bg_has_round_ready()
  -- Native frontend glyph slots: R,E,A,D,Y.  Require the exact contiguous
  -- READY word sequence produced by the retained per-round text descriptor;
  -- a mere non-gameplay interval is not evidence that READY was displayed.
  local ready = {0x0027, 0x001b, 0x0017, 0x001a, 0x002d}
  for row = 0, 31 do
    for col = 0, 59 do
      local match = true
      for i = 1, #ready do
        local word = r16(s.staged_bg_buffer + (row * 64 + col + i - 1) * 2)
        if (word & 0x07ff) ~= ready[i] then match = false; break end
      end
      if match then return true end
    end
  end
  return false
end
local function request_round1_finish()
  local marker = progression_marker()
  local target
  if marker < 0x10 then target = 0x10
  elseif marker < 0x16 then target = 0x16
  else return false end
  p:write_u8(A5 + 0x1243, target)
  p:write_u8(A5 + 0x0047, 1)
  p:write_u8(A5 + 0x0005, 2)
  p:write_u8(A5 + 0x0104, 1)
  p:write_u8(A5 + 0x0003, 2)
  finish_requests = finish_requests + 1
  log("FINISH_SUBROUND_REQUEST")
  return true
end
local function finish(reason)
  if finished then return end
  drain_stageclear_debugger_log()
  finished = true
  log(reason)
  local ok
  if route == "direct" then
    -- Direct R1-S3 deliberately bypasses the retained natural Round-clear
    -- context.  It is a torch/scene regression route, not post-boss proof.
    ok = boss_scene_converged and torches_seen and torch_changes >= 3
  else
    -- Round 1 must traverse the retained states 9..13 Stage Clear controller,
    -- the READY presentation, and only then resume gameplay in Round 2.  The
    -- distinct 0x05725A/0x057272 ending remains gated by round selector 6.
    ok = boss_scene_converged and torches_seen and torch_changes >= 3 and
      end_states[9] and end_states[10] and end_states[11] and
      end_states[12] and end_states[13] and large_art and
      scene_clear_command and round2_ready and round2
  end
  local f = assert(io.open(outdir .. "/summary.txt", "w"))
  f:write("result=" .. (ok and "PASS" or "FAIL") .. "\n")
  f:write("reason=" .. reason .. "\n")
  f:write("route=" .. route .. "\n")
  f:write("frames=" .. frame .. "\n")
  f:write("finish_subround_requests=" .. finish_requests .. "\n")
  f:write("torches_exact_residency=" .. (torches_seen and "YES" or "NO") .. "\n")
  f:write("torch_word_changes=" .. torch_changes .. "\n")
  f:write("boss_scene_converged=" .. (boss_scene_converged and "YES" or "NO") .. "\n")
  f:write("endround_entered=" .. (end_entry and "YES" or "NO") .. "\n")
  for state = 9, 13 do
    f:write(string.format("round_presentation_state%d=%s\n", state,
      end_states[state] and "YES" or "NO"))
  end
  f:write("large_art_nonuniform=" .. (large_art and "YES" or "NO") .. "\n")
  f:write("scene_clear_command_27=" .. (scene_clear_command and "YES" or "NO") .. "\n")
  f:write("stageclear_bg_writes=" .. stageclear_bg_writes .. "\n")
  f:write("stageclear_entry_registers=" .. (stageclear_registers or "NOT_CAPTURED") .. "\n")
  if #stageclear_debug_rows > 0 then
    local debug_file = assert(io.open(outdir .. "/stageclear_debugger.tsv", "w"))
    debug_file:write(table.concat(stageclear_debug_rows, "\n"), "\n")
    debug_file:close()
  end
  f:write("round2_ready_observed=" .. (round2_ready and "YES" or "NO") .. "\n")
  f:write("round2=" .. (round2 and "YES" or "NO") .. "\n")
  f:write(string.format("final_round=%02X\nfinal_progression_marker=%02X\nfinal_stage=%04X\n",
    round(), progression_marker(), stage()))
  f:close(); events:close(); machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_stageclear_debugger_log()
  key("Coin 1", frame >= 120 and frame <= 132)
  key("P1 A", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187)
  key("P1 Start", frame >= 175 and frame <= 187)

  if progression_marker() ~= last_marker then
    last_marker, marker_at = progression_marker(), frame
    log("PROGRESSION_MARKER_CHANGE")
  end

  local in_boss = gameplay() and stage() == 0x0016
  if route == "natural" and gameplay() and not in_boss then
    local player_state = r16(A5 + 0x10e8)
    local stable = r16(A5) == 2 and r16(A5 + 2) == 3 and
      player_state >= 1 and player_state <= 3
    if stable and frame - last_finish_request >= 180 and request_round1_finish() then
      last_finish_request = frame
    end
    key("P1 Right", true); key("P1 Left", false); key("P1 Up", false)
    key("P1 B", false); key("P1 C", false)
  elseif in_boss then
    local phase = frame % 360
    key("P1 Right", phase < 180); key("P1 Left", phase >= 180)
    key("P1 Up", false)
    key("P1 B", (frame % 24) < 12)
    key("P1 C", (frame % 50) < 8)
    sample_torches()
    sample_boss_scene()
  else
    key("P1 Right", false); key("P1 Left", false)
    key("P1 Up", false); key("P1 B", false); key("P1 C", false)
  end

  local state = r16(A5 + 0x13aa)
  if (state >= 9 and state <= 13) or scene() == 2 then
    if not end_entry then end_entry = true; log("ENDROUND_ENTRY") end
    if state >= 9 and state <= 13 then
      end_states[state] = true
      -- State changes can become visible to the frame notifier before the
      -- retained producer's final writes have crossed the next publication
      -- boundary.  Capture the two content-bearing dwell states only after a
      -- few stable ticks; entry snapshots caused the false split-screen proof
      -- rejected by Tighe on Build 0553.
      local timer = r16(A5 + 0x1392)
      if (state ~= 11 and state ~= 13) or timer >= 8 then
        capture_presentation_state(state)
      end
    end
    sample_scene_clear_queue()
  end
  if not round2_ready and end_states[13] and staged_bg_has_round_ready() then
    round2_ready = true
    dump_words(outdir .. "/round2_ready_staged_plane_a.bin", s.staged_fg_buffer, 2048)
    dump_words(outdir .. "/round2_ready_staged_plane_b.bin", s.staged_bg_buffer, 2048)
    dump_vram_names(outdir .. "/round2_ready_vram_plane_a.bin", 0xe000)
    dump_vram_names(outdir .. "/round2_ready_vram_plane_b.bin", 0xc000)
    pcall(function() screen:snapshot(outdir .. "/round2_ready.png") end)
    log("ROUND2_READY")
  end
  if round() >= 2 and gameplay() and r16(A5 + 0x013e) >= 0x0017 then round2 = true end
  if route == "direct" and round2 and torches_seen and torch_changes >= 3 then
    finish("DIRECT_R1S3_COMPLETE")
  elseif route == "natural" and round2 and boss_scene_converged then finish("ROUND2")
  elseif frame % 300 == 0 then log("HEARTBEAT")
  elseif frame >= max_frames then finish("MAX_FRAMES") end
end)

emu.register_stop(function() if not finished then finish("STOPPED") end end)
print(string.format("[r1_completion] route=%s max_frames=%d out=%s", route, max_frames, outdir))
