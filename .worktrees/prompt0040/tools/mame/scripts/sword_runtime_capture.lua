-- Bounded Build 0279 sword capture. Observational only: no input or memory writes.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local mem = assert(cpu.spaces["program"])
local trace_dir = os.getenv("TRACE_DIR") or "."

local A = {
  scene = 0x00ff78a8,
  action = 0x00ff10e8,
  variant = 0x00ff1116,
  attack_active = 0x00ff1108,
  facing = 0x00ff1114,
  phase = 0x00ff110a,
  sprite_ctrl = 0x00ff7794,
  hud_count = 0x00ff68b6,
  front_effect_count = 0x00ff68b8,
  player_front_count = 0x00ff68ba,
  middle_count = 0x00ff68bc,
  player_body_count = 0x00ff68be,
  back_enemy_count = 0x00ff68c0,
  player_body_queue = 0x00ff6bda,
  sat_a = 0x00ff61cc,
  sat_b = 0x00ff644c,
  sat_front = 0x00ff66ce,
  resident_codes = 0x00ff6782,
  emitted_count = 0x00ff77a8,
}

local EXPECTED = {
  {address = 0x0007391c, bytes = {0x48, 0xe7, 0xff, 0xf0}, label = "native_pal_fixup"},
  {address = 0x0007397a, bytes = {0x37, 0x41, 0x00, 0x04}, label = "native_pal_fixup_store"},
}

local PLAYER_BODY_BOUND = 20
local SAT_BOUND = 80
local RESIDENT_CELLS = 128
local SPRITE_TILE_BASE = 1024
local MAX_CONTEXT_FRAMES = 480

local frame = 0
local context_frames = 0
local thrust_frames = 0
local thrust_0104_rows = 0
local min_thrust_phase = nil
local max_thrust_phase = nil
local closed = false

local function r8(address)
  local ok, value = pcall(function() return mem:read_u8(address) end)
  return ok and (value & 0xff) or 0
end

local function r16(address)
  local ok, value = pcall(function() return mem:read_u16(address) end)
  return ok and (value & 0xffff) or 0
end

local function signed9(value)
  value = value & 0x01ff
  return value > 0x0140 and value - 0x0200 or value
end

local function cycle_count()
  local ok, value = pcall(function()
    if type(cpu.total_cycles) == "function" then return cpu:total_cycles() end
    return cpu.total_cycles
  end)
  return ok and tonumber(value) or nil
end

local function open_csv(name, header)
  local file = assert(io.open(trace_dir .. "/" .. name, "w"))
  file:write(header, "\n")
  return file
end

local frame_cycles = open_csv("frame_cycles.csv",
  "external_frame,cycles,scene,action,variant,attack_active,facing,phase,sprite_ctrl,colbank_bits")
local context = open_csv("attack_context.csv",
  "external_frame,cycles,trigger,scene,action,variant,attack_active,facing,phase,sprite_ctrl,colbank_bits,hud_count,front_effect_count,player_front_count,middle_count,player_body_count,back_enemy_count,emitted_count,sat_front")
local body = open_csv("thrust_player_body.csv",
  "external_frame,cycles,phase,index,word0,y_raw,screen_y,code,x_raw,screen_x,resident_cell,resident_tile")
local residency = open_csv("attack_residency.csv",
  "external_frame,cycles,cell,source_code,genesis_tile")
local sat = open_csv("thrust_displayed_sat.csv",
  "external_frame,cycles,phase,sat_front,sat_index,y_raw,screen_y,size_link,tile_word,genesis_tile,palette_line,hflip,vflip,x_raw,screen_x,resident_source_code")
local files = {frame_cycles, context, body, residency, sat}

local function resident_cell(code)
  local normalized = code & 0x1fff
  if normalized == 0 or normalized >= 0x1000 then return -1, -1 end
  local set = normalized & 0x1f
  for way = 0, 3 do
    local cell = set * 4 + way
    if r16(A.resident_codes + cell * 2) == normalized then
      return cell, SPRITE_TILE_BASE + cell * 4
    end
  end
  return -1, -1
end

local function source_for_tile(tile)
  if tile < SPRITE_TILE_BASE or tile >= SPRITE_TILE_BASE + RESIDENT_CELLS * 4 then
    return 0
  end
  local cell = math.floor((tile - SPRITE_TILE_BASE) / 4)
  return r16(A.resident_codes + cell * 2)
end

local function write_context(trigger, cycles)
  local sprite_ctrl = r16(A.sprite_ctrl)
  context:write(string.format(
    "%d,%s,%s,%d,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%d,%d,%d,%d,%d,%d,%d,%d\n",
    frame, tostring(cycles or ""), trigger, r8(A.scene), r16(A.action), r16(A.variant),
    r16(A.attack_active), r16(A.facing), r16(A.phase), sprite_ctrl,
    sprite_ctrl & 0x00e0, r16(A.hud_count), r16(A.front_effect_count),
    r16(A.player_front_count), r16(A.middle_count), r16(A.player_body_count),
    r16(A.back_enemy_count), r16(A.emitted_count), r16(A.sat_front)))
end

local function write_residency(cycles)
  for cell = 0, RESIDENT_CELLS - 1 do
    local code = r16(A.resident_codes + cell * 2)
    if code ~= 0 then
      residency:write(string.format("%d,%s,%d,%04X,%d\n",
        frame, tostring(cycles or ""), cell, code, SPRITE_TILE_BASE + cell * 4))
    end
  end
end

local function write_thrust(cycles, phase)
  local count = math.min(r16(A.player_body_count), PLAYER_BODY_BOUND)
  for index = 0, count - 1 do
    local address = A.player_body_queue + index * 8
    local word0 = r16(address)
    local y = r16(address + 2)
    local code = r16(address + 4)
    local x = r16(address + 6)
    local cell, tile = resident_cell(code)
    if code == 0x0104 then thrust_0104_rows = thrust_0104_rows + 1 end
    body:write(string.format("%d,%s,%d,%d,%04X,%04X,%d,%04X,%04X,%d,%d,%d\n",
      frame, tostring(cycles or ""), phase, index, word0, y, signed9(y - 0x80),
      code, x, signed9(x - 0x80), cell, tile))
  end

  local front = r16(A.sat_front)
  local sat_base = front == 0 and A.sat_a or A.sat_b
  for index = 0, SAT_BOUND - 1 do
    local address = sat_base + index * 8
    local y = r16(address)
    local size_link = r16(address + 2)
    local tile_word = r16(address + 4)
    local tile = tile_word & 0x07ff
    local x = r16(address + 6)
    sat:write(string.format(
      "%d,%s,%d,%d,%d,%04X,%d,%04X,%04X,%d,%d,%d,%d,%04X,%d,%04X\n",
      frame, tostring(cycles or ""), phase, front, index, y, signed9(y - 0x80),
      size_link, tile_word, tile, (tile_word >> 13) & 3, (tile_word >> 11) & 1,
      (tile_word >> 12) & 1, x, signed9(x - 0x80), source_for_tile(tile)))
  end
end

local preflight = assert(io.open(trace_dir .. "/instrumentation_preflight.txt", "w"))
preflight:write("logger=final_bounded_sword_runtime_build0279\n")
preflight:write("scripted_input=NO\nmanual_marker_keys=NO\nmemory_writes=NO\nheadless=NO\n")
preflight:write("action=0x00FF10E8\nvariant=0x00FF1116\nattack_active=0x00FF1108\n")
preflight:write("facing=0x00FF1114\nphase=0x00FF110A\n")
preflight:write("native_player_body_count=0x00FF68BE\n")
preflight:write("native_queue_player_body=0x00FF6BDA\n")
preflight:write("pc090oj_sat_front=0x00FF66CE\npc090oj_emitted_count=0x00FF77A8\n")
preflight:write("native_pal_fixup=runtime_genesis_pc_0x0007391C\n")
preflight:write("native_pal_fixup_store=runtime_genesis_pc_0x0007397A\n")
local preflight_ok = true
for _, check in ipairs(EXPECTED) do
  local actual = {}
  local match = true
  for offset, expected in ipairs(check.bytes) do
    local value = r8(check.address + offset - 1)
    actual[#actual + 1] = string.format("%02X", value)
    if value ~= expected then match = false end
  end
  preflight:write(string.format("%s_bytes=%s\n%s_match=%s\n",
    check.label, table.concat(actual), check.label, match and "YES" or "NO"))
  preflight_ok = preflight_ok and match
end
preflight:write("preflight_pass=" .. (preflight_ok and "YES" or "NO") .. "\n")
preflight:close()
if not preflight_ok then error("Build 0279 instrumentation preflight failed") end

local function flush_files()
  for _, file in ipairs(files) do file:flush() end
end

local function close_files()
  if closed then return end
  closed = true
  flush_files()
  for _, file in ipairs(files) do file:close() end
  local summary = assert(io.open(trace_dir .. "/capture_summary.txt", "w"))
  summary:write(string.format("external_frames=%d\n", frame))
  summary:write(string.format("attack_context_frames=%d\n", context_frames))
  summary:write(string.format("automatic_thrust_frames=%d\n", thrust_frames))
  summary:write(string.format("thrust_0104_queue_rows=%d\n", thrust_0104_rows))
  summary:write(string.format("thrust_phase_min=%s\n", tostring(min_thrust_phase or "NONE")))
  summary:write(string.format("thrust_phase_max=%s\n", tostring(max_thrust_phase or "NONE")))
  summary:write("scripted_input=NO\nmanual_marker_keys=NO\nmemory_writes=NO\nheadless=NO\n")
  summary:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  local cycles = cycle_count()
  local scene = r8(A.scene)
  local action = r16(A.action)
  local variant = r16(A.variant)
  local active = r16(A.attack_active)
  local phase = r16(A.phase)
  local sprite_ctrl = r16(A.sprite_ctrl)
  frame_cycles:write(string.format("%d,%s,%d,%04X,%04X,%04X,%04X,%04X,%04X,%04X\n",
    frame, tostring(cycles or ""), scene, action, variant, active, r16(A.facing),
    phase, sprite_ctrl, sprite_ctrl & 0x00e0))

  local attack_context = scene == 1 and (variant == 1 or variant == 4)
  local thrust = scene == 1 and (action == 2 or action == 3)
    and variant == 1 and active == 1
  if attack_context and context_frames < MAX_CONTEXT_FRAMES then
    context_frames = context_frames + 1
    write_context(thrust and "THRUST" or "ATTACK_CONTEXT", cycles)
    write_residency(cycles)
  end
  if thrust and thrust_frames < MAX_CONTEXT_FRAMES then
    thrust_frames = thrust_frames + 1
    min_thrust_phase = min_thrust_phase and math.min(min_thrust_phase, phase) or phase
    max_thrust_phase = max_thrust_phase and math.max(max_thrust_phase, phase) or phase
    write_thrust(cycles, phase)
  end
  flush_files()
end)

emu.register_stop(close_files)

