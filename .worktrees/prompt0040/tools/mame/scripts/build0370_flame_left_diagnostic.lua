-- Build 0370 diagnostic: reuse the established automated Stage-1 route, then
-- exercise the retained flame-sword horizontal attack in both directions at
-- map Segment 5.  The A5+0x12FA write is diagnostic state injection; this is
-- not evidence of legitimate pickup acquisition and is never a release fix.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local mem = assert(cpu.spaces["program"])
local out_dir = assert(os.getenv("TRACE_DIR"))
local max_frames = tonumber(os.getenv("MAX_FRAMES") or "7500")
local mode8_probe = os.getenv("MODE8_PROBE") == "1"
local timeout_probe = os.getenv("TIMEOUT_PROBE") == "1"
local arcade = os.getenv("ARCADE") == "1"
local wram_base = arcade and 0x10c000 or 0xff0000
local function W(offset) return wram_base + offset end
local out = assert(io.open(out_dir .. "/flame_left_frames.csv", "w"))
local events = assert(io.open(out_dir .. "/flame_left_events.csv", "w"))
local debuglog = assert(io.open(out_dir .. "/flame_left_debugger_events.txt", "w"))
local summary_path = out_dir .. "/flame_left_summary.txt"
local timeout_out = timeout_probe and assert(io.open(out_dir .. "/weapon_timeout.csv", "w")) or nil

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end
local function r16(a) return mem:read_u16(a) & 0xffff end
local function w16(a, v) mem:write_u16(a, v & 0xffff) end
local function reg(name)
  local item = cpu.state[name]
  return item and (item.value & 0xffffffff) or 0
end

local frame = 0
local seg5_frame = -1
local flame_injected = false
local left_attacks = 0
local right_attacks = 0
local mode16_injected = false
local mode8_trigger_frame = -1
local exception = false
local closed = false
local timeout_armed = false
local timeout_expired = false
local timeout_limit = -1
local timeout_last_index = r16(W(0x1418))
local vectors = {
  mem:read_u32(0x08) & 0xffffff,
  mem:read_u32(0x0c) & 0xffffff,
  mem:read_u32(0x10) & 0xffffff,
}

out:write("frame,pc,segment,player_x,player_y,mode,weapon,attack_active,phase,variant,facing,selector1244,aux0_type,aux0_x,aux0_y,aux0_phase,a0,a1,a2,a3,a4\n")
events:write("frame,label,pc,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,a5,mode,weapon,attack_active,phase,variant,facing,selector1244,event1360,event13ac,event13ba\n")
if timeout_out then
  timeout_out:write("frame,pc,weapon_12fa,timer_1326,index_1418,limit,event\n")
end

local taps = {}
if timeout_probe then
  taps[#taps + 1] = mem:install_write_tap(W(0x1418), W(0x1419), "build0372_timer_index_write",
    function(_, data, mask)
      timeout_out:write(string.format("%d,%06X,%04X,%04X,%04X,%04X,INDEX_WRITE_%08X_%08X\n",
        frame, reg("PC") & 0xffffff, r16(W(0x12fa)), r16(W(0x1326)),
        r16(W(0x1418)), timeout_limit & 0xffff, data & 0xffffffff, mask & 0xffffffff))
      timeout_out:flush()
      return data
    end)
end
local function add_tap(address, label)
  taps[#taps + 1] = mem:install_read_tap(address, address + 1, "build0370_" .. label,
    function(_, data, _)
      events:write(string.format(
        "%d,%s,%06X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X\n",
        frame, label, reg("PC") & 0xffffff, reg("D0"), reg("D1"), reg("D2"),
        reg("D3"), reg("D4"), reg("D5"), reg("D6"), reg("D7"), reg("A0"),
        reg("A1"), reg("A2"), reg("A3"), reg("A4"), reg("A5"), r16(W(0x10e8)),
        r16(W(0x12fa)), r16(W(0x1108)), r16(W(0x110a)), r16(W(0x1116)),
        r16(W(0x1114)), r16(W(0x1244)), r16(W(0x1360)), r16(W(0x13ac)),
        r16(W(0x13ba))))
      events:flush()
      return data
    end)
end
local bp = arcade and
  {0x51250, 0x51260, 0x51266, 0x5150c, 0x51510, 0x51514, 0x51518, 0x5151c,
   0x543b4, 0x543c0, 0x545b6, 0x545c4} or
  {0x5145c, 0x5146c, 0x51472, 0x51718, 0x5171c, 0x51720, 0x51724, 0x51728,
   0x544b2, 0x544be, 0x546a0, 0x546ae}
local labels = {"MODE16_SET", "SLOT_INIT_CALL", "FRONT_CLEAR_CALL",
  "AFTER_517E6", "AFTER_517FA", "AFTER_51556", "AFTER_51598", "BODY_ENTRY",
  "BODY_PHASE_INDEX", "BODY_SELECTOR_READ", "FLAME_OFFSET_READ", "FLAME_DESCRIPTOR_READ"}
for i = 1, #bp do add_tap(bp[i], labels[i]) end

local console = machine.debugger and machine.debugger.consolelog or nil
local console_index = 0
if cpu.debug then
  local points = {}
  for i = 1, #bp do points[i] = {bp[i], labels[i]} end
  for _, point in ipairs(points) do
    local action = string.format(
      'printf "B370,%s,%%06X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\\n",pc,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,w@ff10e8,w@ff12fa,w@ff1108,w@ff110a,w@ff1116,w@ff1114,w@ff1244,w@ff1360,w@ff13ac,w@ff13ba; g',
      point[2])
    if arcade then
      action = action:gsub("w@ff1", "w@10d")
    end
    cpu.debug:bpset(point[1], "1", action)
  end
end

local function drain_debugger_log()
  if not console then return end
  for index = console_index + 1, #console do
    local line = tostring(console[index])
    if line:match("^B370,") then debuglog:write(frame, ",", line, "\n") end
  end
  console_index = #console
  debuglog:flush()
end

local function close(reason)
  if closed then return end
  closed = true
  drain_debugger_log()
  out:flush(); out:close(); events:flush(); events:close(); debuglog:flush(); debuglog:close()
  if timeout_out then timeout_out:flush(); timeout_out:close() end
  local s = assert(io.open(summary_path, "w"))
  s:write("reason=" .. reason .. "\n")
  s:write("frames=" .. frame .. "\n")
  s:write("segment5_frame=" .. seg5_frame .. "\n")
  s:write("diagnostic_flame_injected=" .. (flame_injected and "YES" or "NO") .. "\n")
  s:write("left_attack_frames=" .. left_attacks .. "\n")
  s:write("right_attack_frames=" .. right_attacks .. "\n")
  s:write("diagnostic_mode16_event_injected=" .. (mode16_injected and "YES" or "NO") .. "\n")
  s:write("exception=" .. (exception and "YES" or "NO") .. "\n")
  s:write("timeout_probe_armed=" .. (timeout_armed and "YES" or "NO") .. "\n")
  s:write("timeout_expired=" .. (timeout_expired and "YES" or "NO") .. "\n")
  s:write(string.format("timeout_limit=%04X\n", timeout_limit & 0xffff))
  s:write(string.format("final_pc=%06X\n", reg("PC") & 0xffffff))
  s:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_debugger_log()
  if timeout_probe then
    if frame == 300 then
      taps[#taps + 1] = mem:install_write_tap(W(0x1418), W(0x1419),
        "build0372_timer_index_write_post_reset",
        function(_, data, mask)
          timeout_out:write(string.format("%d,%06X,%04X,%04X,%04X,%04X,INDEX_WRITE_POST_%08X_%08X\n",
            frame, reg("PC") & 0xffffff, r16(W(0x12fa)), r16(W(0x1326)),
            r16(W(0x1418)), timeout_limit & 0xffff, data & 0xffffffff, mask & 0xffffffff))
          timeout_out:flush()
          return data
        end)
    end
    local current_index = r16(W(0x1418))
    if current_index ~= timeout_last_index then
      timeout_out:write(string.format("%d,%06X,%04X,%04X,%04X,%04X,INDEX_CHANGE_FROM_%04X\n",
        frame, reg("PC") & 0xffffff, r16(W(0x12fa)), r16(W(0x1326)),
        current_index, timeout_limit & 0xffff, timeout_last_index))
      timeout_out:flush()
      timeout_last_index = current_index
    end
  end
  local coin_now = arcade and frame >= 120 and frame <= 132 or frame >= 60 and frame <= 66
  local start_now = arcade and frame >= 175 and frame <= 187 or frame >= 120 and frame <= 126
  set_input("Coin 1", coin_now)
  set_input("P1 A", coin_now)
  set_input("1 Player Start", start_now)
  set_input("P1 Start", start_now)

  local segment = r16(W(0x013e))
  if segment == 5 and seg5_frame < 0 then seg5_frame = frame end
  local since = seg5_frame >= 0 and frame - seg5_frame or -1

  if mode8_probe and frame >= 500 and mode8_trigger_frame < 0 and r16(W(0x10e8)) == 8 then
    mode8_trigger_frame = frame
  end
  local probe_since = mode8_trigger_frame >= 0 and frame - mode8_trigger_frame or -1
  local right = frame >= 180 and (seg5_frame < 0 or (mode8_probe and mode8_trigger_frame < 0) or
    (not mode8_probe and (since < 20 or (since >= 150 and since < 260))))
  local left = mode8_probe and mode8_trigger_frame >= 0 and probe_since < 100 or
    (not mode8_probe and seg5_frame >= 0 and since >= 20 and since < 130)
  local jump = frame >= 180 and (seg5_frame < 0 or (mode8_probe and mode8_trigger_frame < 0)) and (frame % 48) < 8
  local route_attack = frame >= 180 and seg5_frame < 0 and (frame % 26) < 4
  local left_attack = mode8_probe and mode8_trigger_frame >= 0 and probe_since < 60 and (probe_since % 20) < 5 or
    (not mode8_probe and left and since >= 32 and since < 90 and (since % 20) < 5)
  local right_attack = seg5_frame >= 0 and since >= 165 and since < 225 and (since % 20) < 5

  set_input("P1 Right", right)
  set_input("P1 Left", left)
  set_input("P1 C", jump)
  set_input("P1 B", route_attack or left_attack or right_attack)
  set_input("P1 Button 1", route_attack or left_attack or right_attack)
  set_input("P1 Button 2", jump)

  if timeout_probe and frame >= 500 and not timeout_armed and r16(W(0x12fa)) == 1 then
    local limits = {0x0bb8, 0x0e10, 0x1068, 0x12c0, 0x1518}
    local index = r16(W(0x1418))
    timeout_limit = limits[index + 1] or -1
    if timeout_limit > 3 then
      w16(W(0x12fa), 4)
      w16(W(0x1326), timeout_limit - 3)
      flame_injected = true
      timeout_armed = true
      timeout_out:write(string.format("%d,%06X,%04X,%04X,%04X,%04X,ARM\n",
        frame, reg("PC") & 0xffffff, r16(W(0x12fa)), r16(W(0x1326)), index,
        timeout_limit))
    end
  elseif ((mode8_probe and frame >= 500) or seg5_frame >= 0) and not flame_injected then
    w16(W(0x12fa), 4)
    flame_injected = true
  end
  if timeout_probe and timeout_armed then
    local weapon = r16(W(0x12fa))
    local timer = r16(W(0x1326))
    timeout_out:write(string.format("%d,%06X,%04X,%04X,%04X,%04X,%s\n",
      frame, reg("PC") & 0xffffff, weapon, timer, r16(W(0x1418)),
      timeout_limit & 0xffff, weapon == 1 and timer == 0 and "EXPIRE" or "TICK"))
    timeout_out:flush()
    if weapon == 1 and timer == 0 then timeout_expired = true end
  end
  -- Optional negative-control only.  Mode 0x10 is the round-completion state,
  -- not the reported Segment-5 fall, so normal diagnostics never inject it.
  if os.getenv("INJECT_MODE16") == "1" and seg5_frame >= 0 and since == 31 and not mode16_injected then
    w16(W(0x1360), 1)
    w16(W(0x13ac), 8)
    w16(W(0x13ba), 0x80)
    mode16_injected = true
  end
  if left_attack then left_attacks = left_attacks + 1 end
  if right_attack then right_attacks = right_attacks + 1 end

  local pc = reg("PC") & 0xffffff
  for _, v in ipairs(vectors) do
    if pc >= v and pc < v + 0x1000 then exception = true end
  end
  if seg5_frame >= 0 or exception then
    out:write(string.format(
      "%d,%06X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%08X,%08X,%08X,%08X,%08X\n",
      frame, pc, segment, r16(W(0x10be)), r16(W(0x10c0)), r16(W(0x10e8)),
      r16(W(0x12fa)), r16(W(0x1108)), r16(W(0x110a)), r16(W(0x1116)),
      r16(W(0x1114)), r16(W(0x1244)), r16(W(0x1338)), r16(W(0x133a)),
      r16(W(0x133c)), r16(W(0x133e)), reg("A0"), reg("A1"), reg("A2"),
      reg("A3"), reg("A4")))
    out:flush()
  end
  if exception then close("exception"); machine:exit()
  elseif timeout_probe and timeout_expired then close("weapon_timeout_probe_complete"); machine:exit()
  elseif mode8_probe and mode8_trigger_frame >= 0 and probe_since >= 120 then close("mode8_left_attack_probe_complete"); machine:exit()
  elseif not mode8_probe and seg5_frame >= 0 and since >= 280 then close("segment5_direction_test_complete"); machine:exit()
  elseif frame >= max_frames then close("maximum_frame_budget"); machine:exit() end
end)

_G.build0370_flame_left_stop = emu.add_machine_stop_notifier(function()
  close("machine_stop")
end)
