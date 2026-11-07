-- PROMT-ID-0105 live Round-1 completion gate.
-- Normal controller input plus the repository's established "Finish Current
-- Sub-Round Now!" mutation for the two pre-boss boundaries.  The mutation
-- requests completion only; the retained arcade transition code owns teardown,
-- stage/package activation, palette/audio decisions, and boss progression.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
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
  "staged_bg_buffer", "plane_a_resident_logical_rows",
  "fg_boundary_active_record", "fg_boundary_active_package",
  "genesistan_plane_a_scene_scroll_reseed_native", "genesistan_plane_a_scene_scroll_reseed_native_exit"}) do
  assert(s[name], "missing symbol " .. name)
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
local boss_scene_converged, boss_buffers_dumped = false, false
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
local function sample_boss_scene()
  if scene() == 1 and r8(s.genesistan_current_pc080sn_tileset_id) == 1 and
     r16(A5 + 0x013e) >= 0x0017 and
     r16(s.fg_boundary_active_record) == 0x0016 and
     r16(s.fg_boundary_active_package) == 0x0005 and torches_seen then
    boss_scene_converged = true
    if not boss_buffers_dumped then
      dump_words(outdir .. "/boss_staged_plane_a.bin", s.staged_fg_buffer, 2048)
      dump_words(outdir .. "/boss_staged_plane_b.bin", s.staged_bg_buffer, 2048)
      boss_buffers_dumped = true
      log("BOSS_SCENE_CONVERGED")
    end
  end
end
local function sample_large_art()
  local distinct = {}
  for i = 0, 2047 do distinct[r16(s.staged_bg_buffer + i * 2)] = true end
  local count = 0 for _ in pairs(distinct) do count = count + 1 end
  if count >= 32 then large_art = true end
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
  finished = true
  log(reason)
  local ok
  if route == "direct" then
    -- Direct R1-S3 deliberately bypasses the retained natural Round-clear
    -- context.  It is a torch/scene regression route, not post-boss proof.
    ok = boss_scene_converged and torches_seen and torch_changes >= 3
  else
    -- Round 1 advances directly to Round 2.  The 0x05725A/0x057272 large-art
    -- ending is source-gated by round selector 6 and is not an R1 condition.
    ok = boss_scene_converged and torches_seen and torch_changes >= 3 and round2
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
  f:write("endround_state8=" .. (end_states[8] and "YES" or "NO") .. "\n")
  f:write("endround_state10=" .. (end_states[10] and "YES" or "NO") .. "\n")
  f:write("large_art_nonuniform=" .. (large_art and "YES" or "NO") .. "\n")
  f:write("round2=" .. (round2 and "YES" or "NO") .. "\n")
  f:write(string.format("final_round=%02X\nfinal_progression_marker=%02X\nfinal_stage=%04X\n",
    round(), progression_marker(), stage()))
  f:close(); events:close(); machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
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

  local owner, state = r16(A5 + 0x13d8), r16(A5 + 0x13da)
  if owner == 1 or scene() == 2 then
    if not end_entry then end_entry = true; log("ENDROUND_ENTRY") end
    if state <= 11 then end_states[state] = true end
    if state >= 2 and state <= 8 and frame % 30 == 0 then sample_large_art() end
  end
  if round() >= 2 or stage() >= 23 then round2 = true end
  if route == "direct" and round2 and torches_seen and torch_changes >= 3 then
    finish("DIRECT_R1S3_COMPLETE")
  elseif route == "natural" and round2 and boss_scene_converged then finish("ROUND2")
  elseif frame % 300 == 0 then log("HEARTBEAT")
  elseif frame >= max_frames then finish("MAX_FRAMES") end
end)

emu.register_stop(function() if not finished then finish("STOPPED") end end)
print(string.format("[r1_completion] route=%s max_frames=%d out=%s", route, max_frames, outdir))
