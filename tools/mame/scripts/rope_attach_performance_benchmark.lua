-- Deterministic Genesis NTSC gameplay-start -> first-rope-attach benchmark.
-- Input route: COIN, START, then RIGHT continuously from the semantic start.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local trial = tonumber(os.getenv("ROPE_BENCH_TRIAL") or "1")
local max_frames = tonumber(os.getenv("ROPE_BENCH_MAX_FRAMES") or "12000")

-- Optional exact-cycle instrumentation for the existing deterministic route.
-- Addresses are supplied by the caller from the matching ROM's symbols/
-- disassembly; ordinary benchmark runs install no debugger breakpoints.
local column_entry = tonumber(os.getenv("ROPE_BENCH_COLUMN_ENTRY") or "", 16)
local column_return = tonumber(os.getenv("ROPE_BENCH_COLUMN_RETURN") or "", 16)
local injected_entry = tonumber(os.getenv("ROPE_BENCH_INJECT_ENTRY") or "", 16)
local injected_limit = tonumber(os.getenv("ROPE_BENCH_INJECT_SAMPLES") or "0")
local injected_only = os.getenv("ROPE_BENCH_INJECT_ONLY") == "1"
local injected_count = 0
local debug_log = nil
local debug_log_index = 0
local column_start = nil
local column_cycles = {}
if column_entry and column_return and cpu.debug then
  debug_log = assert(machine.debugger and machine.debugger.consolelog,
    "exact column cycles require debugger console log")
  cpu.debug:bpset(column_entry, "1",
    'printf "PBC,E,%d,%d\\n",totalcycles,frame; g')
  cpu.debug:bpset(column_return, "1",
    'printf "PBC,R,%d,%d\\n",totalcycles,frame; g')
end

local function drain_column_cycles()
  if not debug_log then return end
  for index = debug_log_index + 1, #debug_log do
    local tag, cycles = tostring(debug_log[index]):match("^PBC,([ER]),(%d+),%d+")
    if tag == "E" then
      column_start = tonumber(cycles)
    elseif tag == "R" and column_start then
      column_cycles[#column_cycles + 1] = tonumber(cycles) - column_start
      column_start = nil
    end
  end
  debug_log_index = #debug_log
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
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame = 0
local started = false
local start_frame = -1
local start_time = 0
local finished = false

local function write_result(result, reason)
  if finished then return end
  finished = true
  drain_column_cycles()
  local elapsed_frames = started and (frame - start_frame) or -1
  local elapsed_seconds = started and (now_seconds() - start_time) or -1
  local out = assert(io.open(trace_dir .. "/trial.tsv", "w"))
  out:write("trial\tresult\treason\tstart_frame\tattach_frame\telapsed_frames\telapsed_seconds\telapsed_milliseconds\trecord\tplayer_state\tplayer_x\tplayer_y\n")
  out:write(string.format("%d\t%s\t%s\t%d\t%d\t%d\t%.9f\t%.3f\t%04X\t%04X\t%04X\t%04X\n",
    trial, result, reason, start_frame, frame, elapsed_frames, elapsed_seconds,
    elapsed_seconds * 1000, r16(0xff013e), r16(0xff10e8),
    r16(0xff10be), r16(0xff10c2)))
  out:close()
  if debug_log then
    local cycle_out = assert(io.open(trace_dir .. "/plane_b_column_cycles.tsv", "w"))
    cycle_out:write("sample\tcycles\n")
    for index, cycles in ipairs(column_cycles) do
      cycle_out:write(string.format("%d\t%d\n", index, cycles))
    end
    cycle_out:close()
  end
  machine:exit()
end

local function drive_inputs()
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
  set_input("P1 Right", started)
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_column_cycles()
  if injected_only and injected_limit > 0 and #column_cycles >= injected_limit then
    write_result("PASS", "matched_injected_samples_complete")
    return
  end
  drive_inputs()

  local global_ready = r16(0xff0000) == 2 and r16(0xff0002) == 3 and r16(0xff0004) == 0
  local player_state = r16(0xff10e8)
  if not started and global_ready and r8(0xff3865) == 1 and
      r16(0xff10be) == 0x0020 and player_state >= 1 and player_state <= 3 then
    started = true
    start_frame = frame
    start_time = now_seconds()
  end

  -- Optional matched producer microbenchmark.  The default rope race never
  -- enters this block.  At a stable gameplay frame, emulate a normal JSR by
  -- pushing the current PC and entering the requested native producer; its RTS
  -- resumes the game.  This permits an exact bracket when the natural route
  -- does not execute the isolated producer.
  if started and injected_entry and injected_count < injected_limit and
      (frame - start_frame) >= 30 and ((frame - start_frame) % 4) == 0 then
    local pc_state = assert(cpu.state["PC"], "PC state unavailable")
    local sp_state = assert(cpu.state["SP"] or cpu.state["A7"], "SP state unavailable")
    local return_pc = pc_state.value & 0xffffff
    local stack = (sp_state.value - 4) & 0xffffff
    program:write_u32(stack, return_pc)
    sp_state.value = stack
    pc_state.value = injected_entry
    injected_count = injected_count + 1
  end

  -- With no jump/attack input, the first state-4 transition after progression
  -- reaches record 2 is the retained arcade rope-attachment semantic state.
  if started and r16(0xff013e) >= 2 and player_state == 4 then
    write_result("PASS", "first_rope_attached")
  elseif frame >= max_frames then
    write_result("FAIL", "frame_budget_exhausted")
  end
end)
