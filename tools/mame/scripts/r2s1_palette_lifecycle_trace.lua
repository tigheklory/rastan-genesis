-- PROMT-ID-0138: external GENESIS NTSC R2-S1 palette lifecycle trace.
-- This host-only tool records retained state, scene ownership, palette-hook
-- arguments, and every staged Line-2 write.  The "progressed" route uses the
-- established original A5+0x40 debug-invincibility gate only until record 29,
-- then releases it so the retained death/respawn lifecycle runs normally.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")
local state = cpu.state
local symbols_path = assert(os.getenv("R2PAL_SYMBOLS"), "R2PAL_SYMBOLS is required")
local output_path = assert(os.getenv("R2PAL_OUTPUT"), "R2PAL_OUTPUT is required")
local route = os.getenv("R2PAL_ROUTE") or "initial"
local max_frames = tonumber(os.getenv("R2PAL_FRAMES") or "18000")
local target_record = tonumber(os.getenv("R2PAL_TARGET_RECORD") or "29")

local function parse_symbols(path)
  local result = {}
  for line in assert(io.lines(path)) do
    local address, name = line:match("^([0-9A-Fa-f]+)%s+%S%s+([^%s]+)$")
    if address and name then result[name] = tonumber(address, 16) end
  end
  return result
end
local symbols = parse_symbols(symbols_path)
for _, name in ipairs({"staged_palette_words", "genesistan_current_scene_id",
  "genesistan_pc090oj_hook_zero_fill_56440", "genesistan_frontend_owner_reset",
  "genesistan_gameplay_owner_reset", "load_scene_tiles", "genesistan_palette_hook_59ad4"}) do
  assert(symbols[name], "missing symbol " .. name)
end

local function r8(a) return program:read_u8(a) & 0xff end
local function r16(a) return program:read_u16(a) & 0xffff end
local function l2_text(base)
  local values = {}
  for i = 0, 15 do values[#values + 1] = string.format("%04X", r16(base + i * 2)) end
  return table.concat(values, ",")
end
local function retained_text()
  return string.format("human=%04X round=%04X record=%04X stage=%04X 13aa=%04X 13ac=%04X 13ae=%04X 13b0=%04X fade238=%04X scene=%02X state=%04X/%04X/%04X",
    r16(0xff0034), r16(0xff0118), r16(0xff013e), r16(0xff1242),
    r16(0xff13aa), r16(0xff13ac), r16(0xff13ae), r16(0xff13b0),
    r16(0xff0238), r8(symbols.genesistan_current_scene_id),
    r16(0xff0000), r16(0xff0002), r16(0xff0004))
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on) if fields[name] then fields[name]:set_value(on and 1 or 0) end end

local out = assert(io.open(output_path, "w"))
out:write("route=" .. route .. "\n")
out:write("frame\tevent\tpc\td0\td1\ta0\tstate\tl2\n")
local frame, finished = 0, false
local taps = {}
local gameplay_frame, teardown_frame, restore_frame = nil, nil, nil
local stable_after_restore = 0
local previous_tuple = ""

local function event(name)
  out:write(string.format("%d\t%s\t%06X\t%08X\t%08X\t%08X\t%s\t%s\n",
    frame, name, state["PC"].value & 0xffffff, state["D0"].value & 0xffffffff,
    state["D1"].value & 0xffffffff, state["A0"].value & 0xffffffff,
    retained_text(), l2_text(symbols.staged_palette_words + 0x40)))
  out:flush()
end

local function exec_observer(name)
  local a = symbols[name]
  taps[#taps + 1] = program:install_read_tap(a, a + 1, "r2pal_" .. name,
    function(_, data) event(name); return data end)
end
for _, name in ipairs({"genesistan_pc090oj_hook_zero_fill_56440",
  "genesistan_frontend_owner_reset", "genesistan_gameplay_owner_reset",
  "load_scene_tiles", "genesistan_palette_hook_59ad4"}) do exec_observer(name) end

local l2_base = symbols.staged_palette_words + 0x40
taps[#taps + 1] = program:install_write_tap(l2_base, l2_base + 0x1f, "r2pal_l2",
  function(offset, data, mask)
    out:write(string.format("%d\tL2_WRITE_%02X\t%06X\t%08X\t%08X\t%08X\t%s\t%04X\n",
      frame, offset - l2_base, state["PC"].value & 0xffffff,
      state["D0"].value & 0xffffffff, state["D1"].value & 0xffffffff,
      state["A0"].value & 0xffffffff, retained_text(), data & 0xffff))
    return data
  end)

local function vdp_read_command(address, code)
  program:write_u16(0xc00004, (address & 0x3fff) | ((code & 3) << 14))
  program:write_u16(0xc00004, ((address >> 14) & 3) | ((code & 0x3c) << 2))
end
local function finish(reason)
  if finished then return end
  finished = true
  local staged = l2_text(l2_base)
  vdp_read_command(0, 8)
  local cram = {}
  for i = 0, 63 do cram[i] = program:read_u16(0xc00000) & 0xffff end
  local actual = {}
  for i = 32, 47 do actual[#actual + 1] = string.format("%04X", cram[i]) end
  out:write(string.format("terminal_reason=%s\nterminal_frame=%d\nterminal_state=%s\nterminal_staged_l2=%s\nterminal_cram_l2=%s\n",
    reason, frame, retained_text(), staged, table.concat(actual, ",")))
  out:close()
  machine:exit()
end

_G._r2pal = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  local human = route ~= "attract"
  key("Coin 1", human and frame >= 120 and frame <= 132)
  key("P1 A", human and frame >= 120 and frame <= 132)
  key("1 Player Start", human and frame >= 175 and frame <= 187)
  key("P1 Start", human and frame >= 175 and frame <= 187)

  local in_game = r16(0xff0000) == 2 and r16(0xff0002) == 3 and r8(symbols.genesistan_current_scene_id) == 1
  if in_game and not gameplay_frame then gameplay_frame = frame; event("GAMEPLAY_FIRST") end
  local record = r16(0xff013e)
  if route == "progressed" and in_game and record < target_record then
    program:write_u16(0xff0040, 0x0040)
    key("P1 Right", true)
    key("P1 Button 1", frame % 30 < 6)
    key("P1 Button 2", frame % 30 < 12)
    key("P1 B", frame % 30 < 6)
    key("P1 C", frame % 30 < 12)
  elseif route == "progressed" then
    program:write_u16(0xff0040, 0)
  end

  local tuple = string.format("%04X/%04X/%04X/%02X/%04X/%04X/%04X/%04X/%04X",
    r16(0xff0000), r16(0xff0002), r16(0xff0004), r8(symbols.genesistan_current_scene_id),
    r16(0xff0034), record, r16(0xff13aa), r16(0xff13ac), r16(0xff13b0))
  if tuple ~= previous_tuple then event("STATE_CHANGE"); previous_tuple = tuple end

  if gameplay_frame and not teardown_frame and r8(symbols.genesistan_current_scene_id) == 0 then
    if route ~= "progressed" or record >= target_record then teardown_frame = frame; event("TEARDOWN_SEEN") end
  end
  if teardown_frame and not restore_frame and in_game and frame > teardown_frame then
    restore_frame = frame; event("RESTORE_SEEN")
  end
  if restore_frame and in_game then stable_after_restore = stable_after_restore + 1 else stable_after_restore = 0 end

  if route == "initial" and gameplay_frame and frame >= gameplay_frame + 180 then finish("INITIAL_STABLE")
  elseif route == "attract" and gameplay_frame and frame >= gameplay_frame + 180 then finish("ATTRACT_GAMEPLAY")
  elseif (route == "early" or route == "progressed") and stable_after_restore >= 180 then finish("RESPAWN_STABLE")
  elseif frame >= max_frames then finish("TIMEOUT") end
end)

emu.print_info("R2-S1 PALETTE LIFECYCLE TRACE ARMED: " .. route)
