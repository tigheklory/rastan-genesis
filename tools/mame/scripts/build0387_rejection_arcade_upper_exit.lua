-- Build 0387 rejection analysis: bounded ORIGINAL ARCADE third-chain upper-exit trace.
--
-- Reuses the established Build-0378 Round-1 Castle route and input cadence up to
-- the third-chain top.  Unlike the older exit experiment, it keeps UP held after
-- the first state-4/Y<=0x40 event so the arcade's natural top-of-chain decision is
-- observed.  It records only the retained player/scroll fields and the three
-- head probes used by player_collision_probe_family_53a6e.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local main_region = machine.memory.regions[":maincpu"]
local outdir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local states = assert(io.open(outdir .. "/arcade_upper_exit_states.tsv", "w"))
local probes = assert(io.open(outdir .. "/arcade_upper_exit_head_probes.tsv", "w"))

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  if fields[name] then fields[name]:set_value(on and 1 or 0) end
end

local A5 = 0x10c000
local frame = -1
local phase2_at, top_at, exit_at = nil, nil, nil
local stable_scroll_frames, last_top_scroll = 0, nil
local last_state, last_prog = -1, -1
local closed = false
local taps = {}
local debuglog = machine.debugger and machine.debugger.consolelog or nil
local debug_index = debuglog and #debuglog or 0

states:write(table.concat({
  "frame", "event", "pc", "progression", "map_stream_ptr", "selector",
  "strip", "group", "player_state", "player_substate", "player_x", "player_y",
  "requested_x", "requested_y", "velocity_x", "velocity_y", "collision_flags",
  "ground_property", "contact_ptr", "fg_scroll_x", "fg_scroll_y", "input_edge",
  "raw_input"
}, "\t"), "\n")
probes:write(table.concat({
  "frame", "event", "pc", "probe", "probe_x", "probe_y", "d6_pending",
  "a0", "collision_word", "collision_low7", "player_state", "player_x",
  "player_y", "collision_flags", "fg_scroll_x", "fg_scroll_y"
}, "\t"), "\n")

local function state_row(event)
  states:write(string.format(
    "%d\t%s\t%06X\t%04X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%08X\t%04X\t%04X\t%04X\t%04X\n",
    frame, event or "", cpu.state["PC"].value & 0xffffff,
    r16(A5+0x013e), r32(A5+0x10c6), r16(A5+0x10a8), r16(A5+0x10ca),
    r16(A5+0x10cc), r16(A5+0x10e8), r16(A5+0x10ea), r16(A5+0x10be),
    r16(A5+0x10c0), r16(A5+0x10dc), r16(A5+0x10de), r16(A5+0x10d4),
    r16(A5+0x10d6), r16(A5+0x10ce), r16(A5+0x1132), r32(A5+0x111c),
    r16(A5+0x10ae), r16(A5+0x10b0), r16(A5+0x136e), r16(0x10d37a)))
  states:flush()
end

local function reg(name)
  local s = cpu.state[name]
  return s and (s.value & 0xffffffff) or 0
end
local function postprobe(name)
  local a0 = reg("A0") & 0xffffff
  local word = r16(a0)
  local x = r16(A5+0x10be)
  if name == "HEAD_LEFT_RESULT" then x = (x-r16(A5+0x112e)+3) & 0xffff end
  if name == "HEAD_RIGHT_RESULT" then x = (x+r16(A5+0x112e)-3) & 0xffff end
  local d6 = reg("D6") & 0xffff
  local y = (r16(A5+0x10c0)-r16(A5+0x1130)-d6) & 0xffff
  probes:write(string.format(
    "%d\t%s\t%06X\t%s\t%04X\t%04X\t%04X\t%06X\t%04X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
    frame, name, reg("PC") & 0xffffff, name:gsub("HEAD_", ""):gsub("_RESULT", ""):lower(), x, y,
    d6, a0, word, word & 0x7f, r16(A5+0x10e8), r16(A5+0x10be),
    r16(A5+0x10c0), r16(A5+0x10ce), r16(A5+0x10ae), r16(A5+0x10b0)))
  probes:flush()
end

local function drain_debug_log()
  if not debuglog then return end
  for i = debug_index + 1, #debuglog do
    local line = tostring(debuglog[i])
    local payload = line:match("^(UP387,.*)")
    if payload then
      local v = {}
      for s in payload:gmatch("[^,]+") do v[#v+1] = s end
      if #v >= 15 then
        local name, d6 = v[2], tonumber(v[5], 16) or 0
        local px, py = tonumber(v[8], 16) or 0, tonumber(v[9], 16) or 0
        local ex, ey = tonumber(v[10], 16) or 0, tonumber(v[11], 16) or 0
        local x = px
        if name == "HEAD_LEFT_RESULT" then x = (px-ex+3) & 0xffff end
        if name == "HEAD_RIGHT_RESULT" then x = (px+ex-3) & 0xffff end
        local y = (py-ey-d6) & 0xffff
        local word = tonumber(v[7], 16) or 0
        probes:write(table.concat({
          tostring(frame), name, v[3], name:gsub("HEAD_", ""):gsub("_RESULT", ""):lower(),
          string.format("%04X", x), string.format("%04X", y), string.format("%04X", d6),
          v[6], v[7], string.format("%02X", word & 0x7f), v[12],
          string.format("%04X", px), string.format("%04X", py), v[13], v[14], v[15]
        }, "\t"), "\n")
      end
    end
  end
  debug_index = #debuglog
  probes:flush()
end

local function arm_probes()
  if type(p.install_execute_tap) == "function" then
    for pc, name in pairs({
      [0x053a90]="HEAD_CENTER_RESULT", [0x053ac4]="HEAD_LEFT_RESULT",
      [0x053af8]="HEAD_RIGHT_RESULT"
    }) do
      local event_name = name
      taps[#taps+1] = p:install_execute_tap(pc, pc, "upper_" .. name,
        function() if top_at and not closed then postprobe(event_name) end end)
    end
  else
    assert(debuglog, "launch with -debug -debugger none")
    for pc, name in pairs({
      [0x053a90]="HEAD_CENTER_RESULT", [0x053ac4]="HEAD_LEFT_RESULT",
      [0x053af8]="HEAD_RIGHT_RESULT"
    }) do
      local action = string.format(
        'printf "UP387,%s,%%06X,%%08X,%%08X,%%06X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\\n",pc,d0,d6,a0,w@a0,w@10D0BE,w@10D0C0,w@10D12E,w@10D130,w@10D0E8,w@10D0CE,w@10D0AE,w@10D0B0; g',
        name)
      cpu.debug:bpset(pc, "1", action)
    end
    machine.debugger:command("go")
  end
end
arm_probes()

local function close()
  if closed then return end
  drain_debug_log()
  closed = true
  state_row("END")
  states:close()
  probes:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_debug_log()
  if frame <= 300 then
    pcall(function() main_region:write_u8(0x05ff9f, 0xdf) end)
    pcall(function() p:write_u8(0x05ff9f, 0xdf) end)
  end
  key("Coin 1", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187)
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

    if not top_at and r16(A5+0x013e) == 0x11 and
       r16(A5+0x10e8) == 4 and r16(A5+0x10c0) <= 0x0060 and
       r16(A5+0x10b0) ~= 0x0100 then
      top_at = frame
      state_row("THIRD_CHAIN_FINAL_CLIMB")
    end
    if top_at then
      up = true
      left = false
      right = false
      jump = false
      local scroll = r16(A5+0x10b0)
      if r16(A5+0x10e8) == 4 and scroll == last_top_scroll then
        stable_scroll_frames = stable_scroll_frames + 1
      else
        stable_scroll_frames = 0
      end
      last_top_scroll = scroll
      if not exit_at and stable_scroll_frames >= 90 then
        exit_at = frame
        state_row("UPPER_EXIT_INPUT")
      end
      if exit_at then
        local e = frame-exit_at
        up = false
        right = true
        jump = e < 12
      end
    end

    key("P1 Left", left)
    key("P1 Right", right)
    key("P1 Up", up)
    key("P1 Down", false)
    key("P1 Button 2", jump)
  end

  local state = r16(A5+0x10e8)
  if state ~= last_state then state_row("STATE_CHANGE"); last_state = state end
  local prog = r16(A5+0x013e)
  if prog ~= last_prog then state_row("PROGRESSION"); last_prog = prog end
  if top_at and ((frame-top_at) % 10) == 0 then state_row("SAMPLE") end

  if frame >= 7000 or (top_at and frame-top_at >= 720) then
    close()
    machine:exit()
  end
end)

_G.build0387_rejection_arcade_upper_exit_stop = emu.add_machine_stop_notifier(close)
