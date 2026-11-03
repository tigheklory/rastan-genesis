-- Build 0393 bounded GENESIS NTSC READY-name lifetime probe.
--
-- Reuses the established gameplay-entry input timing.  It locates three
-- representative cells from the already-proven READY name sequences, then
-- records only teardown entry, completion of the Build-0392 clear, and the
-- first subsequent display-enable command.  The probe exits at that command.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"], "missing :maincpu")
local p = assert(cpu.spaces["program"], "missing maincpu program space")
local vdp = assert(m.devices[":gen_vdp"], "missing :gen_vdp")
local vram = assert(vdp.spaces["videoram"], "missing Genesis VRAM space")
local outdir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local out = assert(io.open(outdir .. "/ready_name_lifetime.tsv", "w"))

local STAGED_BG = 0x00ff40a0
local PLANE_B = 0x0000c000
local ACTIVE_PACKAGE = 0x00ffb230
local RESEED_PENDING = 0x00ffb23a
local SCENE_ID = 0x00ffc554
local TEARDOWN_PC = 0x000564d0

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function v16(a)
  return (((vram:read_u8(a) & 0xff) << 8) | (vram:read_u8(a + 1) & 0xff)) & 0xffff
end
local function reg(name)
  local item = cpu.state[name] or cpu.state[name == "PC" and "CURPC" or name]
  return item and (item.value & 0xffffffff) or 0
end

-- Resolve the canonical native target from the final ROM rather than from the
-- last-linked variant symbol file.  Build 0392's helper ends with RTS after
-- CLR.W abs.l + BSR.W; validate that exact production sequence.
assert(r16(TEARDOWN_PC) == 0x4eb9, "translated teardown is not JSR abs.l")
local teardown_helper = r32(TEARDOWN_PC + 2) & 0xffffff
assert(r16(teardown_helper) == 0x4279, "unexpected teardown-helper prefix")
assert(r16(teardown_helper + 6) == 0x6100, "missing generic-clear BSR")
assert(r16(teardown_helper + 10) == 0x4e75, "missing teardown-helper RTS")
local clear_done_pc = teardown_helper + 10

local fields = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local frame = 0
local taps = {}
-- The established text-writer census proves the ROUND/READY destination is
-- arcade C-window 0x00C00C48 = Plane B row 12, column 18.  The writer advances
-- two native columns per character and 0x200 arcade bytes (two native rows) at
-- the 0xFF line marker.  Track fixed producer-owned cells, not value matches.
local cells = {
  (12 * 64) + 18, -- first 'R' in ROUND
  (12 * 64) + 26, -- 'D' in ROUND
  (14 * 64) + 24, -- 'A' in READY
}
local stop_pending = false
local closed = false
local ready_seen = false
local stage_change_logged = false
local vram_change_logged = false
local last_state_key = nil
local cell_writes = 0

out:write("frame\tevent\tpc\tdisplay_word\tstate0\tstate2\tstate4\tscene\tactive_package\treseed_pending\tcell0\tstage0\tvram0\tcell1\tstage1\tvram1\tcell2\tstage2\tvram2\n")

local function log(event, display_word)
  local values = {
    frame, event, string.format("%06X", reg("PC") & 0xffffff),
    display_word and string.format("%04X", display_word) or "-",
    string.format("%04X", r16(0xff0000)),
    string.format("%04X", r16(0xff0002)),
    string.format("%04X", r16(0xff0004)),
    string.format("%02X", r8(SCENE_ID)),
    string.format("%04X", r16(ACTIVE_PACKAGE)),
    string.format("%02X", r8(RESEED_PENDING)),
  }
  for i = 1, 3 do
    local cell = cells and cells[i] or 0xffff
    values[#values + 1] = string.format("%04X", cell)
    if cells then
      values[#values + 1] = string.format("%04X", r16(STAGED_BG + cell * 2))
      values[#values + 1] = string.format("%04X", v16(PLANE_B + cell * 2))
    else
      values[#values + 1] = "----"
      values[#values + 1] = "----"
    end
  end
  out:write(table.concat(values, "\t"), "\n")
  out:flush()
end

local function inspect_vdp_word(word)
  if (word & 0xff00) ~= 0x8100 then return end
  log((word & 0x0040) ~= 0 and "DISPLAY_ON" or "DISPLAY_OFF", word)
  if stage_change_logged and (word & 0x0040) ~= 0 then stop_pending = true end
end
local function vdp_control_write(_, data, _)
  local raw = data or 0
  if raw > 0xffff then
    inspect_vdp_word((raw >> 16) & 0xffff)
    inspect_vdp_word(raw & 0xffff)
  else
    inspect_vdp_word(raw & 0xffff)
  end
  return data
end
taps[#taps + 1] = p:install_write_tap(0x00c00004, 0x00c00007,
  "build0393_ready_vdp_reg1", vdp_control_write)
for i = 1, #cells do
  local address = STAGED_BG + cells[i] * 2
  taps[#taps + 1] = p:install_write_tap(address, address + 1,
    "build0393_ready_cell_" .. i, function(_, data, _)
      if cell_writes < 48 then
        cell_writes = cell_writes + 1
        log("CELL" .. i .. "_WRITE_" .. string.format("%04X", data & 0xffff))
      end
      return data
    end)
end
local function state_write(address, last, name)
  taps[#taps + 1] = p:install_write_tap(address, last, "build0393_" .. name,
    function(_, data, _)
      log(name .. "_WRITE_" .. string.format("%08X", data & 0xffffffff))
      return data
    end)
end
state_write(RESEED_PENDING, RESEED_PENDING + 1, "RESEED")
state_write(ACTIVE_PACKAGE, ACTIVE_PACKAGE + 1, "ACTIVE_PACKAGE")
state_write(SCENE_ID, SCENE_ID + 1, "SCENE")

local function close()
  if closed then return end
  closed = true
  out:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
  set_input("P1 Right", frame >= 360)

  local s0, s2, s4 = r16(0xff0000), r16(0xff0002), r16(0xff0004)
  local state_key = string.format("%04X/%04X/%04X", s0, s2, s4)
  if s0 == 2 and state_key ~= last_state_key then
    last_state_key = state_key
    log("STATE_" .. state_key)
  end
  if not ready_seen and s0 == 2 and s2 == 2 and (s4 == 6 or s4 == 7) and
      r16(STAGED_BG + cells[1] * 2) ~= 0 then
    ready_seen = true
    log("READY_CELLS_OBSERVED")
  end

  if ready_seen and not stage_change_logged and
      (r16(STAGED_BG + cells[1] * 2) & 0x07ff) ~= 0x0027 then
    stage_change_logged = true
    log("FIRST_STAGE_CHANGE_AFTER_READY")
  end

  if stage_change_logged and not vram_change_logged then
    if (v16(PLANE_B + cells[1] * 2) & 0x07ff) ~= 0x0027 then
      vram_change_logged = true
      log("FIRST_VRAM_CHANGE_AFTER_READY")
      stop_pending = true
    end
  end

  if stop_pending then
    close()
    m:exit()
  elseif frame >= 1000 then
    log("TIMEOUT")
    close()
    m:exit()
  end
end)

_G.build0393_ready_stop = emu.add_machine_stop_notifier(function() close() end)
