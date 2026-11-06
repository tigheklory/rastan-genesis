-- PROMT-ID-0095 ORIGINAL ARCADE evidence capture.
-- Starts stock Rastan at Round 1 Boss using the established ROM selector,
-- records every CLCS palette-RAM write with its 68000 writer PC, and records
-- frame-boundary palette/actor state.  This is tooling only; it does not patch
-- gameplay code or modify a Genesis artifact.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")
local region = assert(machine.memory.regions[":maincpu"], "missing maincpu region")
local screen = assert(machine.screens:at(1), "missing screen")
local out = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local max_frames = tonumber(os.getenv("MAX_FRAMES") or "2600")

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end
local function r8(a) return program:read_u8(a) & 0xff end
local function r16(a) return program:read_u16(a) & 0xffff end
local function hex_line(bank)
  local words = {}
  for i = 0, 15 do words[#words + 1] = string.format("%04X", r16(0x200000 + bank * 32 + i * 2)) end
  return table.concat(words, " ")
end

-- Established MAME cheat selector: F7 = Round 1 Boss.  Keep restoring the
-- source-region byte because MAME may repopulate the region during reset.
region:write_u8(0x05ff9f, 0xf7)

local writes = assert(io.open(out .. "/palette_writes.tsv", "w"))
writes:write("frame\tpc\taddress\tphysical_line\tentry\told_value\tnew_value\tmask\n")
local frames = assert(io.open(out .. "/frames.tsv", "w"))
frames:write("frame\tpc\tmode0\tmode2\tround\tstage\tsubround\tplayer_state\tplayer_x\tpal_counter_0238\tpal_counter_0c50\ttransition_13b0\tboss_fade_enable_026e\tboss_fade_step_0270\tsprite_ctrl_380000\tline25\tline63\tline79\n")
local actors = assert(io.open(out .. "/actors.tsv", "w"))
actors:write("frame\tslot\tactive\ttype\tanim\tbase\tpal_attr\tcomp\tx\ty\n")

local frame = 0
local appeared = nil
local write_count = 0
local palette_shadow = {}
for address = 0x200000, 0x200ffe, 2 do palette_shadow[address] = r16(address) end
local tap = program:install_write_tap(0x200000, 0x200fff, "r1boss_palette", function(address, data, mask)
  local rel = address - 0x200000
  local old = palette_shadow[address] or r16(address)
  local new = ((old & (~mask & 0xffff)) | (data & mask)) & 0xffff
  writes:write(string.format("%d\t%06X\t%06X\t%d\t%d\t%04X\t%04X\t%04X\n",
    frame, cpu.state["PC"].value & 0xffffff, address, rel >> 5, (rel & 0x1f) >> 1,
    old, new, mask & 0xffff))
  palette_shadow[address] = new
  write_count = write_count + 1
end)

local function record_actor_pool()
  -- Main + boss auxiliary records: A5+0x288 through A5+0xA08, 0x40
  -- bytes each.  The Round-1 type-15 pool begins at A5+0x748.
  local a5 = cpu.state["A5"].value & 0xffffff
  if a5 == 0 then return end
  for slot = 0, 30 do
    local a = a5 + 0x288 + slot * 0x40
    local active = r8(a)
    local typ = r8(a + 6)
    if active ~= 0 or typ == 0x0e or typ == 0x0f then
      actors:write(string.format("%d\t%d\t%02X\t%02X\t%02X\t%04X\t%02X\t%02X\t%04X\t%04X\n",
        frame, slot, active, typ, r8(a + 1), r16(a + 0x1e), r8(a + 0x27),
        r8(a + 0x38), r16(a + 0x16), r16(a + 0x1a)))
    end
  end
end

emu.register_frame_done(function()
  frame = frame + 1
  region:write_u8(0x05ff9f, 0xf7)
  input("Coin 1", frame >= 600 and frame <= 612)
  input("1 Player Start", frame >= 655 and frame <= 667)
  -- Established stock invincibility bit; keeps the trace alive without
  -- changing boss/palette code or actor identity.
  if frame >= 655 then
    program:write_u16(0x10c040, 0x0040 | (r16(0x10c040) & 0xffbf))
    program:write_u8(0x10c13a, 0x30) -- established infinite-energy cheat
    program:write_u8(0x10c101, 0x03) -- established infinite-lives cheat
  end

  local mode0, mode2 = r16(0x10c000), r16(0x10c002)
  local pstate = r16(0x10d0e8)
  if not appeared and mode0 == 2 and mode2 == 3 and pstate >= 1 and pstate <= 3 then appeared = frame end
  input("P1 Right", appeared ~= nil)
  -- Do not attack: the boss must remain alive long enough to expose its own
  -- projectile lifecycle.  Invincibility preserves observation without
  -- perturbing the boss's normal state machine.
  input("P1 Button 1", false)

  local a5 = cpu.state["A5"].value & 0xffffff
  local p238, pc50, p13b0, p26e, p270 = 0, 0, 0, 0, 0
  if a5 ~= 0 then
    p238, pc50, p13b0 = r16(a5 + 0x238), r16(a5 + 0x0c50), r16(a5 + 0x13b0)
    p26e, p270 = r16(a5 + 0x26e), r16(a5 + 0x270)
  end
  frames:write(string.format("%d\t%06X\t%04X\t%04X\t%02X\t%04X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%s\t%s\t%s\n",
    frame, cpu.state["PC"].value & 0xffffff, mode0, mode2, r8(0x10c118),
    r16(0x10d242), r8(0x10d243), pstate, r16(0x10d0be), p238, pc50, p13b0,
    p26e, p270, r16(0x380000), hex_line(25), hex_line(63), hex_line(79)))
  record_actor_pool()

  if frame % 120 == 0 then
    writes:flush(); frames:flush(); actors:flush()
    if appeared then pcall(function() screen:snapshot(string.format("%s/frame_%04d.png", out, frame)) end) end
  end
  if frame >= max_frames then
    tap = nil
    writes:flush(); writes:close(); frames:flush(); frames:close(); actors:flush(); actors:close()
    local meta = assert(io.open(out .. "/metadata.txt", "w"))
    meta:write("platform=ORIGINAL ARCADE MAME rastan\n")
    meta:write("selector_address=0x05FF9F\nselector_value=0xF7\n")
    meta:write(string.format("frames=%d\nappeared_frame=%s\npalette_write_count=%d\n", frame, tostring(appeared), write_count))
    meta:close()
    machine:exit()
  end
end)
