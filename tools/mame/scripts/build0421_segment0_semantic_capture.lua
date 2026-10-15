-- Focused Build 0419/0421 Segment-0 semantic snapshot.
-- Captures once the same initial gameplay state has remained stable for 15 frames,
-- before the established input driver begins moving the player.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local capture_x = tonumber(os.getenv("SEGMENT0_CAPTURE_X") or "0x20")

local function r8(address) return program:read_u8(address) & 0xff end
local function r16(address) return program:read_u16(address) & 0xffff end

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function set_input(name, active)
  if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local function dump(path, address, size)
  local out = assert(io.open(path, "wb"))
  for offset = 0, size - 1 do out:write(string.char(r8(address + offset))) end
  out:close()
end

local frame = 0
local stable = 0
local captured = false

local function drive_inputs()
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
  set_input("P1 Right", capture_x ~= 0x20 and frame >= 360)
end

emu.register_frame_done(function()
  frame = frame + 1
  drive_inputs()

  local player_x = r16(0xff10be)
  local x_ready = capture_x == 0x20 and player_x == capture_x or player_x >= capture_x
  local initial = r16(0xff0000) == 2 and r16(0xff0002) == 3 and
    r16(0xff0004) == 0 and r8(0xff3865) == 1 and x_ready
  stable = initial and (stable + 1) or 0
  local required_stable = capture_x == 0x20 and 15 or 1
  if not captured and stable >= required_stable then
    captured = true
    dump(trace_dir .. "/staged_plane_b.bin", 0xff40a0, 0x1000)
    dump(trace_dir .. "/staged_plane_a.bin", 0xff50a0, 0x1000)
    dump(trace_dir .. "/collision_map.bin", 0xff1e00, 0x2000)
    dump(trace_dir .. "/descriptor_state.bin", 0xff1000, 0x0100)
    local out = assert(io.open(trace_dir .. "/state.tsv", "w"))
    out:write("frame\tstate0\tstate2\tstate4\tscene\tplayer_x\tplayer_y\trecord\tscroll_a_x\tscroll_a_y\tstrip_index\tstrip_group\tbg_subcol\tbg_walker\tbg_table_index\n")
    out:write(string.format("%d\t%04X\t%04X\t%04X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%08X\t%04X\n",
      frame, r16(0xff0000), r16(0xff0002), r16(0xff0004), r8(0xff3865),
      r16(0xff10be), r16(0xff10c2), r16(0xff013e), r16(0xff10ae),
      r16(0xff10b0), r16(0xff10ca), r16(0xff10cc), r16(0xff10f6),
      program:read_u32(0xff10fc) & 0xffffffff, r16(0xff1386)))
    out:close()
    machine:exit()
  elseif frame >= 1200 then
    local out = assert(io.open(trace_dir .. "/capture_failed.txt", "w"))
    out:write("initial Segment-0 state not reached\n")
    out:close()
    machine:exit()
  end
end)
