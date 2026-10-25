-- RG-023 bounded Genesis NTSC R1-S2 climb/collision probe.
-- Reuses the established Build-0378/0387 direct-castle input cadence.  It
-- records the retained player/camera state and actual head-probe collision
-- result while climbing; it does not alter map, collision, or progression.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local outdir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local states = assert(io.open(outdir .. "/climb_states.tsv", "w"))
local probes = assert(io.open(outdir .. "/head_probes.tsv", "w"))
local A5 = 0x00ff0000
local frame, phase2_at, blocked_at = -1, nil, nil
local stable_frames, last_scroll, last_y = 0, nil, nil
local closed, taps = false, {}
local debuglog = m.debugger and m.debugger.consolelog or nil
local debug_index = debuglog and #debuglog or 0

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function reg(name)
  local s = cpu.state[name]
  return s and (s.value & 0xffffffff) or 0
end
local fields = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  if fields[name] then fields[name]:set_value(on and 1 or 0) end
end

states:write("frame\tevent\tpc\trecord\tselector\tstrip\tgroup\tstate\tx\ty\treq_x\treq_y\tflags\tfg_x\tfg_y\taccum_y\tdelta_y\tinput_edge\traw_input\n")
probes:write("frame\tevent\tpc\ta0\tword\tlow7\tx\ty\tstate\tfg_x\tfg_y\trecord\tstrip\tgroup\n")

local function state_row(event)
  states:write(string.format(
    "%d\t%s\t%06X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
    frame, event, reg("PC") & 0xffffff, r16(A5+0x013e), r16(A5+0x10a8),
    r16(A5+0x10ca), r16(A5+0x10cc), r16(A5+0x10e8), r16(A5+0x10be),
    r16(A5+0x10c0), r16(A5+0x10dc), r16(A5+0x10de), r16(A5+0x10ce),
    r16(A5+0x10ae), r16(A5+0x10b0), r16(A5+0x10ba), r16(A5+0x10da),
    r16(A5+0x136e), r16(A5+0x137a)))
  states:flush()
end

local function probe_row(name)
  if not phase2_at then return end
  local a0 = reg("A0") & 0xffffff
  local word = r16(a0)
  probes:write(string.format(
    "%d\t%s\t%06X\t%06X\t%04X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
    frame, name, reg("PC") & 0xffffff, a0, word, word & 0x7f,
    r16(A5+0x10be), r16(A5+0x10c0), r16(A5+0x10e8), r16(A5+0x10ae),
    r16(A5+0x10b0), r16(A5+0x013e), r16(A5+0x10ca), r16(A5+0x10cc)))
end

local probe_pcs = {
  [0x053A90]="UP_MOVE_ENTRY",
  [0x053ABC]="HEAD_RESULT_FLAGS",
  [0x053AC4]="HEAD_BLOCK_BRANCH",
  [0x053AC6]="RETRY_SMALLER_MOVE",
  [0x053BB6]="HEAD_CENTER_RESULT",
  [0x053BEA]="HEAD_LEFT_RESULT",
  [0x053C1E]="HEAD_RIGHT_RESULT"
}

local function drain_debug_log()
  if not debuglog then return end
  for i = debug_index + 1, #debuglog do
    local line = tostring(debuglog[i])
    local payload = line:match("^(RG002,.*)")
    if payload then
      local v = {}
      for s in payload:gmatch("[^,]+") do v[#v+1] = s end
      if #v >= 13 then
        probes:write(table.concat({
          tostring(frame), v[2], v[3], v[4], v[5],
          string.format("%02X", (tonumber(v[5], 16) or 0) & 0x7f),
          v[6], v[7], v[8], v[9], v[10], v[11], v[12], v[13]
        }, "\t"), "\n")
      end
    end
  end
  debug_index = #debuglog
  probes:flush()
end

if type(p.install_execute_tap) == "function" then
  for pc, name in pairs(probe_pcs) do
    local event_name = name
    taps[#taps+1] = p:install_execute_tap(pc, pc, "rg023_" .. name,
      function() if not closed then probe_row(event_name) end end)
  end
else
  assert(debuglog, "launch with -debug -debugger none")
  for pc, name in pairs(probe_pcs) do
    local action = string.format(
      'printf "RG002,%s,%%06X,%%06X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\n",pc,a0,w@a0,w@FF10BE,w@FF10C0,w@FF10E8,w@FF10AE,w@FF10B0,w@FF013E,w@FF10CA,w@FF10CC; g',
      name)
    cpu.debug:bpset(pc, "w@FF013E>=10", action)
  end
  m.debugger:command("go")
end

local function dump_collision()
  local f = assert(io.open(outdir .. "/blocked_collision_map.bin", "wb"))
  for i = 0, 0x1fff do f:write(string.char(r8(0x00ff1e00+i))) end
  f:close()
end
local function close()
  if closed then return end
  drain_debug_log()
  closed = true
  state_row("END")
  if blocked_at then dump_collision() end
  states:close(); probes:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_debug_log()
  key("Coin 1", frame >= 120 and frame <= 132)
  key("P1 A", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187)
  key("P1 Start", frame >= 175 and frame <= 187)

  -- Established test survival setup only; no movement/collision/progression write.
  if frame >= 200 then
    p:write_u8(A5+0x0101, 3)
    p:write_u8(A5+0x013a, 0x30)
  end

  if not phase2_at and r16(A5+0x013e) >= 0x10 then
    phase2_at = frame
    state_row("PHASE2")
  end
  if phase2_at then
    local t = frame - phase2_at
    local left = (t < 1200) or (t >= 1800 and t < 3000)
    local right = (t >= 1200 and t < 1800) or t >= 3000
    local up = (t % 360) >= 120 and (t % 360) < 330
    local jump = (t % 90) < 12
    key("P1 Left", left); key("P1 Right", right)
    key("P1 Up", up); key("P1 Down", false)
    key("P1 B", jump); key("P1 C", jump)

    local scroll = r16(A5+0x10b0)
    local player_y = r16(A5+0x10c0)
    if r16(A5+0x10e8) == 4 and up and scroll == last_scroll and player_y == last_y then
      stable_frames = stable_frames + 1
    else
      stable_frames = 0
    end
    last_scroll = scroll
    last_y = player_y
    if not blocked_at and stable_frames >= 60 then
      blocked_at = frame
      state_row("CLIMB_BLOCKED")
      dump_collision()
    end
    if (t % 30) == 0 then state_row("SAMPLE") end
  end

  if frame >= 5600 or (blocked_at and frame-blocked_at >= 120) then
    close(); m:exit()
  end
end)

_G.rg023_s1_2_climb_collision_probe_stop = emu.add_machine_stop_notifier(close)
