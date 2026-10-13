-- Build-0406 native-sprite closeout coverage.
--
-- Reuses the established _c six-button MODE rack-advance control.  Lua only
-- supplies controller inputs and observes state/counters; it performs no
-- emulated-memory writes.  Exact counter write taps preserve the actor/player
-- tuple at the first generated-table miss.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local outdir = assert(os.getenv("NATIVE_CLOSEOUT_OUTDIR"), "NATIVE_CLOSEOUT_OUTDIR is required")
local max_frames = tonumber(os.getenv("NATIVE_CLOSEOUT_MAX_FRAMES") or "120000")
local dwell_frames = tonumber(os.getenv("NATIVE_CLOSEOUT_DWELL_FRAMES") or "600")
local no_progress_frames = tonumber(os.getenv("NATIVE_CLOSEOUT_NO_PROGRESS_FRAMES") or "24000")
local attract_mode = os.getenv("NATIVE_CLOSEOUT_ATTRACT") == "1"
local natural_right_mode = os.getenv("NATIVE_CLOSEOUT_NATURAL_RIGHT") == "1"
local natural_target_progress = tonumber(os.getenv("NATIVE_CLOSEOUT_TARGET_PROGRESS") or "-1")
local adapter_pc = tonumber(os.getenv("NATIVE_CLOSEOUT_ADAPTER_PC") or "")

os.execute('mkdir -p "' .. outdir .. '"')
local events = assert(io.open(outdir .. "/coverage_events.tsv", "w"))
local summary_path = outdir .. "/coverage_summary.txt"

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function reg(name)
  local s = cpu.state[name]
  return s and (s.value & 0xffffffff) or 0
end

local function envaddr(name, fallback)
  return tonumber(os.getenv(name) or string.format("0x%08X", fallback))
end
local A_SCENE = envaddr("NATIVE_CLOSEOUT_SCENE_ADDR", 0x00ffc55c)
local A_GAME_MODE = 0x00ff0000
local A_ROUND = 0x00ff0118
local A_PROGRESS = 0x00ff013e
local A_SUBROUND = 0x00ff1243
local A_PLAYER_FALLBACK = envaddr("NATIVE_CLOSEOUT_PLAYER_FALLBACK_ADDR", 0x00ffbed8)
local A_GENERIC_FALLBACK = envaddr("NATIVE_CLOSEOUT_GENERIC_FALLBACK_ADDR", 0x00ffbeda)
local A_SPECIALIZED_HIT = envaddr("NATIVE_CLOSEOUT_SPECIALIZED_HIT_ADDR", 0x00ffbedc)
local A_PLAYER_ADAPTER = envaddr("NATIVE_CLOSEOUT_PLAYER_ADAPTER_ADDR", 0x00ffbede)
local A_EMIT = envaddr("NATIVE_CLOSEOUT_EMIT_ADDR", 0x00ffbed4)
local A_CRASH = envaddr("NATIVE_CLOSEOUT_CRASH_ADDR", 0x00ff6180)

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
assert(fields["P1 Mode"], "P1 Mode unavailable: launch with -ctrl1 md6button")
local function key(name, on)
  local f = fields[name]
  if f then f:set_value(on and 1 or 0) end
end

events:write(table.concat({
  "frame", "event", "pc", "scene", "game_mode", "round", "progress",
  "subround", "player_state", "player_anim", "player_weapon", "a4",
  "actor_active", "actor_selector", "actor_orient", "actor_state3",
  "actor_subframe", "actor_base", "actor_x", "actor_y", "actor_family",
  "player_fallback", "generic_fallback", "specialized_hit", "player_adapter"
}, "\t"), "\n")

local frame = -1
local finished = false
local unique_progress, unique_subround, unique_round = {}, {}, {}
local mode_presses = 0
local gameplay_frames = 0
local last_mode_gameplay_frame = -100000
local last_subround = -1
local subround_changed_at_gameplay_frame = -100000
local last_progress_key = nil
local last_progress_gameplay_frame = 0
local last_progress_display_frame = 0
local first_fallback = nil

local function row(event)
  local a4 = reg("A4") & 0xffffff
  local active, selector, orient, state3, subframe, base, ax, ay, family = 0,0,0,0,0,0,0,0,0
  if a4 >= 0xff0000 and a4 <= 0xffffff then
    active = r8(a4)
    selector = r8(a4 + 1)
    orient = r8(a4 + 2)
    state3 = r8(a4 + 3)
    subframe = r8(a4 + 0x0b)
    ax = r16(a4 + 0x16)
    ay = r16(a4 + 0x1a)
    base = r16(a4 + 0x1e)
    family = r8(a4 + 0x38)
  end
  events:write(string.format(
    "%d\t%s\t%06X\t%02X\t%04X\t%02X\t%04X\t%02X\t%04X\t%04X\t%04X\t%06X\t%02X\t%02X\t%02X\t%02X\t%02X\t%04X\t%04X\t%04X\t%02X\t%u\t%u\t%u\t%u\n",
    frame, event, reg("PC") & 0xffffff, r8(A_SCENE), r16(A_GAME_MODE),
    r8(A_ROUND), r16(A_PROGRESS), r8(A_SUBROUND), r16(0xff10e8),
    r16(0xff10ea), r16(0xff12fa), a4, active, selector, orient, state3,
    subframe, base, ax, ay, family, r16(A_PLAYER_FALLBACK),
    r16(A_GENERIC_FALLBACK), r16(A_SPECIALIZED_HIT), r16(A_PLAYER_ADAPTER)))
  events:flush()
end

-- MAME tap objects must remain strongly reachable for the lifetime of the run.
-- A chunk-local table can be collected after script initialization.
_G.native_closeout_taps = _G.native_closeout_taps or {}
local taps = _G.native_closeout_taps
-- A_EMIT is written once when the native producer completes a gameplay worker.
-- Count that event rather than display frames, so movement and MODE dwell do
-- not run ahead while one-pending VINT work is coalesced under load.
taps[#taps + 1] = p:install_write_tap(A_EMIT, A_EMIT + 1,
  "native_worker_completion", function()
    if r8(A_SCENE) == 1 and r16(A_GAME_MODE) == 2 then
      gameplay_frames = gameplay_frames + 1
    end
  end)
local function counter_tap(name)
  return function()
    row(name)
    if (name == "PLAYER_FALLBACK" or name == "GENERIC_FALLBACK") and not first_fallback then
      first_fallback = name
    end
  end
end
taps[#taps + 1] = p:install_write_tap(A_PLAYER_FALLBACK, A_PLAYER_FALLBACK + 1,
  "native_player_fallback", counter_tap("PLAYER_FALLBACK"))
taps[#taps + 1] = p:install_write_tap(A_GENERIC_FALLBACK, A_GENERIC_FALLBACK + 1,
  "native_generic_fallback", counter_tap("GENERIC_FALLBACK"))
taps[#taps + 1] = p:install_write_tap(A_SPECIALIZED_HIT, A_SPECIALIZED_HIT + 1,
  "native_specialized_hit", counter_tap("SPECIALIZED_HIT"))
taps[#taps + 1] = p:install_write_tap(A_PLAYER_ADAPTER, A_PLAYER_ADAPTER + 1,
  "native_player_adapter", counter_tap("PLAYER_ADAPTER"))

local adapter_log, adapter_console, adapter_console_index
if adapter_pc then
  adapter_log = assert(io.open(outdir .. "/adapter_callers.tsv", "w"))
  adapter_log:write("frame\tmessage\n")
  adapter_console = assert(machine.debugger and machine.debugger.consolelog,
    "NATIVE_CLOSEOUT_ADAPTER_PC requires -debug -debugger none")
  adapter_console_index = #adapter_console
end
local function drain_adapter_calls()
  if not adapter_console then return end
  for i = adapter_console_index + 1, #adapter_console do
    local message = tostring(adapter_console[i])
    adapter_log:write(string.format("%d\t%s\n", frame, message))
  end
  adapter_console_index = #adapter_console
  adapter_log:flush()
end

local function dump(reason)
  if finished then return end
  finished = true
  drain_adapter_calls()
  row(reason)
  local f = assert(io.open(summary_path, "w"))
  local function count(t) local n=0 for _ in pairs(t) do n=n+1 end return n end
  local function keys(t)
    local a={} for k in pairs(t) do a[#a+1]=k end
    table.sort(a)
    local o={} for _,v in ipairs(a) do o[#o+1]=string.format("%02X",v) end
    return table.concat(o, ",")
  end
  f:write("result=" .. reason .. "\n")
  f:write("frames=" .. frame .. "\n")
  f:write("gameplay_frames=" .. gameplay_frames .. "\n")
  f:write("last_progress_gameplay_frame=" .. last_progress_gameplay_frame .. "\n")
  f:write("no_progress_display_frames=" .. (frame - last_progress_display_frame) .. "\n")
  f:write("mode_presses=" .. mode_presses .. "\n")
  f:write("rounds_seen_count=" .. count(unique_round) .. "\n")
  f:write("rounds_seen=" .. keys(unique_round) .. "\n")
  f:write("subrounds_seen_count=" .. count(unique_subround) .. "\n")
  f:write("subrounds_seen=" .. keys(unique_subround) .. "\n")
  f:write("progress_values_seen_count=" .. count(unique_progress) .. "\n")
  f:write(string.format("player_fallback=%u\n", r16(A_PLAYER_FALLBACK)))
  f:write(string.format("generic_fallback=%u\n", r16(A_GENERIC_FALLBACK)))
  f:write(string.format("specialized_hit=%u\n", r16(A_SPECIALIZED_HIT)))
  f:write(string.format("player_piece_adapter=%u\n", r16(A_PLAYER_ADAPTER)))
  f:write("first_fallback=" .. (first_fallback or "NONE") .. "\n")
  f:write(string.format("crash_flag=%04X\n", r16(A_CRASH)))
  f:close()
  events:close()
  if adapter_log then adapter_log:close() end
  machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_adapter_calls()
  key("Coin 1", not attract_mode and frame >= 120 and frame <= 132)
  key("P1 A", not attract_mode and frame >= 120 and frame <= 132)
  key("1 Player Start", not attract_mode and frame >= 175 and frame <= 187)
  key("P1 Start", not attract_mode and frame >= 175 and frame <= 187)

  local gameplay = r8(A_SCENE) == 1 and r16(A_GAME_MODE) == 2
  local subround = r8(A_SUBROUND)
  if gameplay then
    local round = r8(A_ROUND)
    local progress = r16(A_PROGRESS)
    unique_round[round] = true
    unique_progress[progress] = true
    unique_subround[subround] = true
    local progress_key = string.format("%02X:%02X:%04X", round, subround, progress)
    if progress_key ~= last_progress_key then
      last_progress_key = progress_key
      last_progress_gameplay_frame = gameplay_frames
      last_progress_display_frame = frame
    end
    if subround ~= last_subround then
      last_subround = subround
      subround_changed_at_gameplay_frame = gameplay_frames
      row("SUBROUND_CHANGE")
    end

    local t = gameplay_frames
    local target_reached = natural_target_progress >= 0 and r16(A_PROGRESS) == natural_target_progress
    if natural_right_mode or target_reached then
      key("P1 Right", true)
      key("P1 Left", false)
      key("P1 Up", target_reached and ((frame % 180) < 120))
      key("P1 B", (frame >= 500) and ((frame % 70) < 10))
      key("P1 C", (frame >= 520) and ((frame % 45) < 8))
    else
      key("P1 Right", not attract_mode and (t % 960) < 480)
      key("P1 Left", not attract_mode and (t % 960) >= 480)
      key("P1 Up", not attract_mode and (t % 360) >= 180 and (t % 360) < 300)
      key("P1 B", not attract_mode and (t % 45) < 7)
      key("P1 C", not attract_mode and (t % 90) < 12)
    end

    local stable = gameplay_frames - subround_changed_at_gameplay_frame >= dwell_frames
    local released = gameplay_frames - last_mode_gameplay_frame > 30
    local press = not attract_mode and not natural_right_mode and not target_reached and
      stable and released and (gameplay_frames % 20) < 10
    key("P1 Mode", press)
    if press and gameplay_frames - last_mode_gameplay_frame > 30 then
      last_mode_gameplay_frame = gameplay_frames
      mode_presses = mode_presses + 1
      row("MODE_PRESS")
    end
  else
    key("P1 Right", false); key("P1 Left", false); key("P1 Up", false)
    key("P1 B", false); key("P1 C", false); key("P1 Mode", false)
  end

  if frame % 300 == 0 then row("HEARTBEAT") end
  if r16(A_CRASH) ~= 0 then dump("CRASH")
  elseif first_fallback then dump("FALLBACK")
  elseif not attract_mode and subround >= 0x89 and gameplay and
      gameplay_frames - subround_changed_at_gameplay_frame >= dwell_frames then dump("COMPLETE")
  elseif gameplay and frame - last_progress_display_frame >= no_progress_frames then
    dump("NO_PROGRESS")
  elseif frame >= max_frames then dump("ABSOLUTE_MAX_FRAMES") end
end)

emu.register_stop(function()
  if not finished then dump("STOPPED") end
end)

print(string.format("[native_closeout] READY dwell_workers=%d no_progress_display=%d absolute_max_display=%d; output=%s",
  dwell_frames, no_progress_frames, max_frames, outdir))

-- Optional host-only caller diagnostic.  The RAM write tap above is retained
-- for MAME versions that expose direct 68000 WRAM accesses through taps; this
-- exact entry breakpoint also works when the core's direct path bypasses them.
if adapter_pc then
  assert(machine.debugger and machine.debugger.consolelog,
    "NATIVE_CLOSEOUT_ADAPTER_PC requires -debug -debugger none")
  cpu.debug:bpset(adapter_pc, "1",
    'printf "PLAYER_ADAPTER_CALL,%d,%d,%d,%d\\n",pc,sp,w@sp,w@(sp+2); g')
end
