-- RG-018 subround start probe (GENESIS NTSC).
-- Boots a starting-subround test ROM, runs the normal coin/start sequence, and
-- reads the round value the original stage decoder computes from the patched
-- selector byte: round = (~0x5FF9F & 7) + 1, stored at a5@0x117/0x118, and the
-- stage index at a5@0x1242 (A5 = 0x00FF0000 on Genesis).  It does NOT assert
-- playability (Tighe validates gameplay); it only observes that the patched
-- selector reaches the game's own stage-init decode.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local prog = assert(cpu.spaces["program"])
local trace_dir = assert(os.getenv("TRACE_DIR"))
local expect_round = tonumber(os.getenv("SUBROUND_EXPECT_ROUND") or "0")
local max_frames = tonumber(os.getenv("SUBROUND_MAX_FRAMES") or "520")

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(n, a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local function r8(a) return prog:read_u8(a) & 0xff end
local function r16(a) return prog:read_u16(a) & 0xffff end

local frame = 0
local round_seen, stage_seen = {}, {}

emu.register_frame_done(function()
  frame = frame + 1
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
  if frame >= 300 then
    local rnd = r8(0x00FF0118)
    local stage = r16(0x00FF1242)
    if rnd ~= 0 then round_seen[rnd] = (round_seen[rnd] or 0) + 1 end
    stage_seen[stage] = (stage_seen[stage] or 0) + 1
  end
  if frame >= max_frames then
    local out = assert(io.open(trace_dir .. "/subround_start_probe.tsv", "w"))
    out:write("platform\tGENESIS NTSC\n")
    out:write(string.format("expect_round\t%d\n", expect_round))
    local best, bestc = 0, -1
    for r, c in pairs(round_seen) do if c > bestc then best, bestc = r, c end end
    out:write(string.format("observed_round\t%d\n", best))
    out:write("round_histogram\t")
    for r, c in pairs(round_seen) do out:write(string.format("%d:%d ", r, c)) end
    out:write("\nstage_index_values\t")
    for s, c in pairs(stage_seen) do out:write(string.format("0x%04X:%d ", s, c)) end
    out:write("\nresult=" .. ((expect_round == 0 or best == expect_round) and "PASS" or "FAIL") .. "\n")
    out:close()
    machine:exit()
  end
end)
