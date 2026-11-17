-- PROMT-ID-0142 original-arcade oracle for the Round-1 -> Round-2
-- player-facing lifecycle.  At Tighe's request this assisted capture selects
-- the original arcade's R1-S3 start and enables the stock invincibility cheat.
-- The human still owns every input, the boss fight, final facing, and the
-- transition; the script never writes facing or transition state.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local main_region = assert(machine.memory.regions[":maincpu"], "missing :maincpu ROM region")
local outdir = assert(os.getenv("R1FACE_OUTDIR"), "R1FACE_OUTDIR required")
local finish_facing = os.getenv("R1FACE_FINISH_FACING") or "left"
local max_frames = tonumber(os.getenv("R1FACE_MAX_FRAMES") or "30000")
assert(finish_facing == "left" or finish_facing == "right")

-- Established stock MAME semantics:
--   ROM selector $05FF9F = $F7 -> Round 1 Boss (R1-S3)
--   Invincibility -> original A5+$0040 debug/invincibility gate
local start_selector_address = 0x05ff9f
local start_selector_value = 0xf7
main_region:write_u8(start_selector_address, start_selector_value)

local cheat_api = assert(emu.plugin and emu.plugin.cheat,
  "MAME cheat plugin unavailable; launch with -cheat")
local invincibility = nil
for index, description in pairs(cheat_api.list()) do
  if description == "Invincibility" then
    invincibility = assert(cheat_api.get(index), "Invincibility cheat unavailable")
    invincibility.set_enabled(true)
  end
end
assert(invincibility, "stock rastan Invincibility cheat not found")
local function r8(address) return p:read_u8(address) & 0xff end
local function r16(address) return p:read_u16(address) & 0xffff end
local A5 = 0x0010c000
local function round() return r8(A5 + 0x0118) end
local function record() return r16(A5 + 0x013e) end
local function stage() return r16(A5 + 0x1242) end
local function facing() return r16(A5 + 0x1114) end

os.execute('mkdir -p "' .. outdir .. '"')
local out = assert(io.open(outdir .. "/events.tsv", "w"))
out:write("frame\tevent\tpc\tstate0\tstate2\tstate4\tround\tmarker\tstage\trecord\tend_state\tend_timer\tplayer_state\tanimation_facing\tmovement_facing\tinput_state\tx\ty\tx_aux\ty_aux\tfacing\n")
local frame, finished, r2_stable = 0, false, 0
local last_facing, last_end_state, last_round, last_record = -1, -1, -1, -1
local end_states = {}
local function event(name)
  out:write(string.format("%d\t%s\t%06X\t%04X\t%04X\t%04X\t%02X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
    frame, name, cpu.state["PC"].value & 0xffffff,
    r16(A5), r16(A5 + 2), r16(A5 + 4), round(), r8(A5 + 0x1243),
    stage(), record(), r16(A5 + 0x13aa), r16(A5 + 0x1392),
    r16(A5 + 0x10e8), r16(A5 + 0x110e), r16(A5 + 0x1110),
    r16(A5 + 0x10ce), r16(A5 + 0x1262), r16(A5 + 0x1264),
    r16(A5 + 0x1266), r16(A5 + 0x1268), facing()))
  out:flush()
end

local taps = {}
taps[#taps + 1] = p:install_write_tap(A5 + 0x1114, A5 + 0x1115, "r1face_arcade_facing",
  function(_, data, _)
    event(string.format("FACING_WRITE_%04X", data & 0xffff))
    return data
  end)

local function finish(reason)
  if finished then return end
  finished = true
  event(reason)
  local pass = round() >= 2 and record() >= 0x17
  local summary = assert(io.open(outdir .. "/summary.txt", "w"))
  summary:write("result=" .. (pass and "PASS" or "FAIL") .. "\n")
  summary:write("reason=" .. reason .. "\n")
  summary:write("finish_facing=" .. finish_facing .. "\n")
  summary:write("assisted_start=R1-S3\n")
  summary:write("start_selector=F7\n")
  summary:write("invincibility=" .. (invincibility.get_enabled() and "YES" or "NO") .. "\n")
  summary:write(string.format("frames=%d\nfinal_round=%02X\nfinal_record=%04X\nfinal_facing=%04X\n",
    frame, round(), record(), facing()))
  for state = 9, 13 do
    summary:write(string.format("end_state_%d=%s\n", state, end_states[state] and "YES" or "NO"))
  end
  summary:close(); out:close(); machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  local current_facing, current_end = facing(), r16(A5 + 0x13aa)
  if current_facing ~= last_facing then event("FACING_CHANGE"); last_facing = current_facing end
  if current_end ~= last_end_state then
    event("END_STATE_CHANGE"); last_end_state = current_end
    if current_end >= 9 and current_end <= 13 then end_states[current_end] = true end
  end
  if round() ~= last_round then event("ROUND_CHANGE"); last_round = round() end
  if record() ~= last_record then event("RECORD_CHANGE"); last_record = record() end

  if round() >= 2 and stage() >= 0x17 and record() >= 0x17 and current_end == 0x00ff then
    r2_stable = r2_stable + 1
  else
    r2_stable = 0
  end
  if r2_stable >= 30 then finish("ROUND2_GAMEPLAY")
  elseif frame >= max_frames then finish("MAX_FRAMES") end
end)

print(string.format("[round_transition_facing_arcade] assisted_start=R1-S3 invincibility=yes finish=%s out=%s",
  finish_facing, outdir))
