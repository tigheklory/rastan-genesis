-- GENESIS NTSC Line-2 (Layer-B) partial-dynamic progression tracer (TOOLING, non-shipping).
-- Coins/starts via the established input method, then holds P1 Right to walk Rastan through R1/P1
-- segment crossings. Logs, on any change (or heartbeat), the segment/tileset id, scene id,
-- palette_dirty, and all 16 staged Line-2 words (0xFF6124 = staged_palette_words + 0x40). Also
-- keeps a running checksum of Lines 0/1/3 (Test-owned) to prove they stay static during scene 1.
-- Addresses from apps/rastan-direct/out/symbol.txt (BSS stable across 0328..0331).
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")
local out = os.getenv("GEN_L2_OUT") or "."
local STAGED = 0x00FF60E4
local L2  = STAGED + 0x40            -- Line 2 = words 32..47
local SCENE = 0x00FFC0AC             -- genesistan_current_scene_id
local TILESET = 0x00FFC0AD           -- genesistan_current_pc080sn_tileset_id (per-segment id)
local PDIRTY = 0x00FF4044            -- palette_dirty
local RUN_FRAMES = tonumber(os.getenv("GEN_L2_FRAMES") or "2600")

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local function line2_words()
  local t = {}
  for i = 0, 15 do t[i+1] = program:read_u16(L2 + i*2) & 0xffff end
  return t
end
local function line2_str(t)
  local parts = {}
  for i = 1, 16 do parts[i] = string.format("%04X", t[i]) end
  return table.concat(parts, " ")
end
local function checksum(base, nwords)
  local s = 0
  for i = 0, nwords-1 do s = (s + (program:read_u16(base + i*2) & 0xffff)) & 0xffffffff end
  return s
end

local csv = assert(io.open(out .. "/line2_progression.csv", "w"))
csv:write("frame,reason,tileset,scene,pdirty,l013_sum,line2_words\n")

local prev_l2 = nil
local prev_tileset = -1
local commits = 0
local seg_crossings = 0
local frame = 0
_G._l2_trace = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  -- Genesis pad: P1 A = coin (per rastan_direct_update_inputs), P1 Start = start.
  set_input("P1 A", frame >= 120 and frame <= 150)
  set_input("Coin 1", frame >= 120 and frame <= 150)
  set_input("P1 Start", frame >= 180 and frame <= 210)
  set_input("1 Player Start", frame >= 180 and frame <= 210)
  set_input("P1 Right", frame >= 260)          -- walk right through segments

  local t = line2_words()
  local tileset = program:read_u8(TILESET) & 0xff
  local scene = program:read_u8(SCENE) & 0xff
  local pd = program:read_u8(PDIRTY) & 0xff
  -- Lines 0,1,3 = words 0..15, 16..31, 48..63
  local l013 = (checksum(STAGED, 32) + checksum(STAGED + 0x60, 16)) & 0xffffffff

  local changed = false
  if prev_l2 == nil then changed = true else
    for i = 1, 16 do if t[i] ~= prev_l2[i] then changed = true break end end
  end
  local reason = nil
  if tileset ~= prev_tileset then reason = "SEG"; seg_crossings = seg_crossings + 1 end
  if changed then reason = (reason and (reason.."+L2")) or "L2" end
  if reason == nil and frame % 300 == 0 then reason = "hb" end

  if reason then
    csv:write(string.format("%d,%s,%d,%d,%d,0x%08X,%s\n", frame, reason, tileset, scene, pd, l013, line2_str(t)))
    csv:flush()
  end
  prev_l2 = t
  prev_tileset = tileset

  if frame >= RUN_FRAMES then
    csv:close()
    emu.print_info(string.format("LINE2 TRACE done: %d frames, %d seg-id changes -> %s", frame, seg_crossings-1, out))
    machine:exit()
  end
end)
emu.print_info("LINE2 PROGRESSION TRACE ARMED -> " .. out)
