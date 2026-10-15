-- Deterministic original-arcade gameplay-start -> first-rope-attach benchmark.
-- Input route: COIN, START, then RIGHT continuously from the semantic start.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local trial = tonumber(os.getenv("ROPE_BENCH_TRIAL") or "1")
local max_frames = tonumber(os.getenv("ROPE_BENCH_MAX_FRAMES") or "12000")
local coin_frame = tonumber(os.getenv("ROPE_BENCH_COIN_FRAME") or "600")
local start_press_frame = tonumber(os.getenv("ROPE_BENCH_START_FRAME") or "655")
local use_invincibility = os.getenv("ROPE_BENCH_INVINCIBLE") ~= "0"

local A5 = 0x10c000

-- Enable the stock MAME `rastan` Invincibility cheat, rather than duplicating
-- it as a benchmark-owned gameplay patch.  The cheat engine continuously sets
-- bit 6 at A5+0x0040, which is the game's built-in invincibility/debug gate.
local invincibility_cheat = nil
if use_invincibility then
  local cheat_api = assert(emu.plugin and emu.plugin.cheat,
    "MAME cheat plugin unavailable; launch with -cheat")
  for index, description in pairs(cheat_api.list()) do
    if description == "Invincibility" then
      invincibility_cheat = assert(cheat_api.get(index), "Invincibility cheat unavailable")
      invincibility_cheat.set_enabled(true)
      break
    end
  end
  assert(invincibility_cheat, "stock rastan Invincibility cheat not found")
end

local function r8(address) return program:read_u8(address) & 0xff end
local function r16(address) return program:read_u16(address) & 0xffff end
local function now_seconds()
  local value = machine.time
  return value.seconds + value.attoseconds / 1e18
end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
assert(fields["Coin 1"], "missing Coin 1 input")
assert(fields["1 Player Start"], "missing 1 Player Start input")
assert(fields["P1 Right"], "missing P1 Right input")
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame = 0
local started = false
local start_frame = -1
local start_time = 0
local finished = false
local last_progress_key = nil
local last_progress_frame = 0

local function write_result(result, reason)
  if finished then return end
  finished = true
  local elapsed_frames = started and (frame - start_frame) or -1
  local elapsed_seconds = started and (now_seconds() - start_time) or -1
  local a5_register = cpu.state["A5"] and (cpu.state["A5"].value & 0xffffff) or 0
  local out = assert(io.open(trace_dir .. "/trial.tsv", "w"))
  out:write("trial\tresult\treason\tstart_frame\tattach_frame\telapsed_frames\telapsed_seconds\telapsed_milliseconds\trecord\tplayer_state\tplayer_x\tplayer_y\tfg_x\tfg_y\tlives\ta5\tp1_port\tcheat_active\tinvincibility_word\n")
  out:write(string.format("%d\t%s\t%s\t%d\t%d\t%d\t%.9f\t%.3f\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%06X\t%02X\t%s\t%04X\n",
    trial, result, reason, start_frame, frame, elapsed_frames, elapsed_seconds,
    elapsed_seconds * 1000, r16(A5+0x013e), r16(A5+0x10e8),
    r16(A5+0x10be), r16(A5+0x10c0), r16(A5+0x10ae),
    r16(A5+0x10b0), r16(A5+0x0100), a5_register, r8(0x390001),
    invincibility_cheat and invincibility_cheat.get_enabled() and "YES" or "NO",
    r16(A5+0x0040)))
  out:close()
  machine:exit()
end

local function drive_inputs()
  -- A cold arcade boot is still initializing its input/attract state at the
  -- earlier Genesis harness cadence.  Insert after the title has settled;
  -- this pre-game delay is outside the measured semantic interval.
  set_input("Coin 1", frame >= coin_frame and frame <= coin_frame + 12)
  set_input("1 Player Start", frame >= start_press_frame and frame <= start_press_frame + 12)
  set_input("P1 Right", started)
end

emu.register_frame_done(function()
  frame = frame + 1
  drive_inputs()

  -- These are the original arcade fields retained by the Genesis benchmark:
  -- global state A5+0/2/4, scene byte A5+0x3865, player X A5+0x10BE,
  -- and player action state A5+0x10E8.
  local global_ready = r16(A5+0x0000) == 2 and
                       r16(A5+0x0002) == 3 and
                       r16(A5+0x0004) == 0
  local player_state = r16(A5+0x10e8)
  local credited_game_active = global_ready and r8(A5+0x3865) == 1 and
                               r16(A5+0x0100) > 0
  if not started and global_ready and r8(A5+0x3865) == 1 and
      r16(A5+0x10be) == 0x0020 and player_state >= 1 and player_state <= 3 then
    started = true
    start_frame = frame
    start_time = now_seconds()
    last_progress_frame = frame
  end

  if started then
    local progress_key = string.format("%04X/%04X/%04X/%04X/%04X/%04X",
      r16(A5+0x013e), player_state, r16(A5+0x10be), r16(A5+0x10c0),
      r16(A5+0x10ae), r16(A5+0x10b0))
    if progress_key ~= last_progress_key then
      last_progress_key = progress_key
      last_progress_frame = frame
    end
  end

  -- With no jump/attack input, the first state-4 transition after progression
  -- reaches record 2 is the original first-rope attachment/climbing state.
  if started and credited_game_active and r16(A5+0x013e) == 3 and
      player_state == 4 and (not use_invincibility or
      (invincibility_cheat.get_enabled() and (r16(A5+0x0040) & 0x0040) ~= 0)) then
    write_result("PASS", "first_rope_attached")
  elseif started and r16(A5+0x0100) == 0 and player_state == 8 then
    write_result("FAIL", "player_exhausted_before_rope")
  elseif started and frame - last_progress_frame >= 600 then
    write_result("FAIL", "no_jump_route_stalled")
  elseif frame >= max_frames then
    write_result("FAIL", "frame_budget_exhausted")
  end
end)
