-- Focused native-stage semantic snapshot.  Originally introduced for the
-- Build 0419/0421 Segment-0 comparison; current symbols are supplied by the
-- wrapper so the same bounded capture remains valid as ROM/BSS layout grows.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local screen = assert(machine.screens:at(1), "missing screen")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local capture_x = tonumber(os.getenv("SEGMENT0_CAPTURE_X") or "0x20")
local capture_record = tonumber(os.getenv("CAPTURE_RECORD") or "")
local capture_selector = tonumber(os.getenv("CAPTURE_SELECTOR") or "")
local capture_scroll_y_min = tonumber(os.getenv("CAPTURE_SCROLL_Y_MIN") or "")
local r1s2_route = os.getenv("R1S2_ROUTE") == "1"
local scene_addr = assert(tonumber(os.getenv("SCENE_ADDR")), "SCENE_ADDR is required")
local active_lut_addr = assert(tonumber(os.getenv("ACTIVE_LUT_ADDR")), "ACTIVE_LUT_ADDR is required")
local staged_bg_addr = assert(tonumber(os.getenv("STAGED_BG_ADDR")), "STAGED_BG_ADDR is required")
local staged_fg_addr = assert(tonumber(os.getenv("STAGED_FG_ADDR")), "STAGED_FG_ADDR is required")
local tileset_addr = tonumber(os.getenv("TILESET_ADDR") or "")
local active_record_addr = tonumber(os.getenv("ACTIVE_RECORD_ADDR") or "")
local active_package_addr = tonumber(os.getenv("ACTIVE_PACKAGE_ADDR") or "")

-- Optional host-only cycle probes.  Addresses come from the matching ELF;
-- ordinary captures install no debugger breakpoints and production ROM state
-- is never modified by this instrumentation.
local perf_scene_entry = tonumber(os.getenv("STAGE_PERF_SCENE_ENTRY") or "", 16)
local perf_scene_exit = tonumber(os.getenv("STAGE_PERF_SCENE_EXIT") or "", 16)
local perf_scene_pending = tonumber(os.getenv("STAGE_PERF_SCENE_PENDING") or "", 16)
local perf_row_entry = tonumber(os.getenv("STAGE_PERF_ROW_ENTRY") or "", 16)
local perf_row_copy_done = tonumber(os.getenv("STAGE_PERF_ROW_COPY_DONE") or "", 16)
local debug_log, debug_log_index = nil, 0
local scene_start, row_start = nil, nil
local scene_cycles, row_cycles = {}, {}
if (perf_scene_entry and perf_scene_exit) or (perf_row_entry and perf_row_copy_done) then
  debug_log = assert(machine.debugger and machine.debugger.consolelog,
    "cycle probes require -debug -debugger none")
  if perf_scene_entry and perf_scene_exit then
    local scene_condition = perf_scene_pending and
      string.format("b@%x==1", perf_scene_pending) or "1"
    cpu.debug:bpset(perf_scene_entry, scene_condition,
      'printf "RG12,SCENE_ENTRY,%d,%d\\n",totalcycles,frame; g')
    cpu.debug:bpset(perf_scene_exit, "1",
      'printf "RG12,SCENE_EXIT,%d,%d\\n",totalcycles,frame; g')
  end
  if perf_row_entry and perf_row_copy_done then
    cpu.debug:bpset(perf_row_entry, "w@ff10a8!=0",
      'printf "RG12,ROW_ENTRY,%d,%d\\n",totalcycles,frame; g')
    cpu.debug:bpset(perf_row_copy_done, "w@ff10a8!=0",
      'printf "RG12,ROW_COPY_DONE,%d,%d\\n",totalcycles,frame; g')
  end
end

local function drain_cycles()
  if not debug_log then return end
  for index = debug_log_index + 1, #debug_log do
    local tag, cycles = tostring(debug_log[index]):match("^RG12,([A-Z_]+),(%d+),%d+")
    cycles = tonumber(cycles)
    if tag == "SCENE_ENTRY" then scene_start = cycles
    elseif tag == "SCENE_EXIT" and scene_start then
      scene_cycles[#scene_cycles + 1] = cycles - scene_start; scene_start = nil
    elseif tag == "ROW_ENTRY" then row_start = cycles
    elseif tag == "ROW_COPY_DONE" and row_start then
      row_cycles[#row_cycles + 1] = cycles - row_start; row_start = nil
    end
  end
  debug_log_index = #debug_log
end

local function write_cycles()
  if not debug_log then return end
  drain_cycles()
  local out = assert(io.open(trace_dir .. "/native_stage_cycles.tsv", "w"))
  out:write("kind\tsample\tcycles\n")
  for index, cycles in ipairs(scene_cycles) do
    out:write(string.format("scene_reseed\t%d\t%d\n", index, cycles))
  end
  for index, cycles in ipairs(row_cycles) do
    out:write(string.format("selector_pan_row\t%d\t%d\n", index, cycles))
  end
  out:close()
end

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

local function dump_vram_names(path, base)
  -- Read the real Mega Drive VRAM through the VDP data port.  The MAME
  -- :gen_vdp Lua videoram space is only the 16-KiB Mode-4 compatibility view.
  program:write_u16(0x00c00004, 0x8f02)
  program:write_u16(0x00c00004, base & 0x3fff)
  program:write_u16(0x00c00004, (base >> 14) & 3)
  local out = assert(io.open(path, "wb"))
  for _ = 0, 2047 do
    local word = program:read_u16(0x00c00000) & 0xffff
    out:write(string.char((word >> 8) & 0xff, word & 0xff))
  end
  out:close()
end

local function dump_vram(path)
  -- The spatial verifier must validate the pattern bytes named by Plane A/B,
  -- not merely that staged and hardware name words agree.
  program:write_u16(0x00c00004, 0x8f02)
  program:write_u16(0x00c00004, 0x0000)
  program:write_u16(0x00c00004, 0x0000)
  local out = assert(io.open(path, "wb"))
  for _ = 0, 32767 do
    local word = program:read_u16(0x00c00000) & 0xffff
    out:write(string.char((word >> 8) & 0xff, word & 0xff))
  end
  out:close()
end

local frame = 0
local stable = 0
local captured = false
local captured_frame = nil

local function drive_inputs()
  set_input("Coin 1", frame >= 120 and frame <= 132)
  set_input("P1 A", frame >= 120 and frame <= 132)
  set_input("1 Player Start", frame >= 175 and frame <= 187)
  set_input("P1 Start", frame >= 175 and frame <= 187)
  if r1s2_route and r16(0xff013e) >= 0x10 then
    local t = frame - 360
    local left = (t < 1200) or (t >= 1800 and t < 3000)
    local right = (t >= 1200 and t < 1800) or t >= 3000
    local up = (t % 360) >= 120 and (t % 360) < 330
    local jump = (t % 90) < 12
    set_input("P1 Left", left)
    set_input("P1 Right", right)
    set_input("P1 Up", up)
    set_input("P1 B", jump)
    set_input("P1 C", jump)
    -- Established bounded-route survival setup.  It does not alter graphics,
    -- movement, collision, record progression, or camera state.
    program:write_u8(0xff0101, 3)
    program:write_u8(0xff013a, 0x30)
  else
    set_input("P1 Right", capture_x ~= 0x20 and frame >= 360)
  end
end

emu.register_frame_done(function()
  frame = frame + 1
  drain_cycles()
  drive_inputs()

  local player_x = r16(0xff10be)
  local x_ready = capture_x == 0x20 and player_x == capture_x or player_x >= capture_x
  local semantic_ready = (not capture_record or r16(0xff013e) == capture_record) and
    (not capture_selector or r16(0xff10a8) == capture_selector) and
    (not capture_scroll_y_min or r16(0xff10b0) >= capture_scroll_y_min)
  local initial = r16(0xff0000) == 2 and r16(0xff0002) == 3 and
    r16(0xff0004) == 0 and r8(scene_addr) == 1 and x_ready and semantic_ready
  stable = initial and (stable + 1) or 0
  local required_stable = capture_x == 0x20 and 15 or 1
  if not captured and stable >= required_stable then
    captured = true
    captured_frame = frame
    dump(trace_dir .. "/staged_plane_b.bin", staged_bg_addr, 0x1000)
    dump(trace_dir .. "/staged_plane_a.bin", staged_fg_addr, 0x1000)
    dump(trace_dir .. "/collision_map.bin", 0xff1e00, 0x2000)
    dump(trace_dir .. "/descriptor_state.bin", 0xff1000, 0x0100)
    dump(trace_dir .. "/active_lut.bin", active_lut_addr, 0x5000)
    local snapshot_ok,snapshot_error=pcall(function() machine.video:snapshot() end)
    local snapshot_status=assert(io.open(trace_dir .. "/snapshot_status.txt","w"))
    snapshot_status:write(snapshot_ok and "PASS\n" or (tostring(snapshot_error).."\n"))
    snapshot_status:close()
    dump_vram_names(trace_dir .. "/vram_plane_b.bin", 0xc000)
    dump_vram_names(trace_dir .. "/vram_plane_a.bin", 0xe000)
    dump_vram(trace_dir .. "/vram.bin")
    local out = assert(io.open(trace_dir .. "/state.tsv", "w"))
    out:write("frame\tstate0\tstate2\tstate4\tscene\ttileset\tactive_record\tactive_package\tplayer_x\tplayer_y\trecord\tselector\tscroll_a_x\tscroll_a_y\tscroll_b_x\tscroll_b_y\tstrip_index\tstrip_group\tbg_subcol\tbg_walker\tbg_table_index\tstage_byte\tphase3_enable\tphase3_tick\n")
    out:write(string.format("%d\t%04X\t%04X\t%04X\t%02X\t%02X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%08X\t%04X\t%02X\t%04X\t%04X\n",
      frame, r16(0xff0000), r16(0xff0002), r16(0xff0004), r8(scene_addr),
      tileset_addr and r8(tileset_addr) or 0xff,
      active_record_addr and r16(active_record_addr) or 0xffff,
      active_package_addr and r16(active_package_addr) or 0xffff,
      r16(0xff10be), r16(0xff10c2), r16(0xff013e), r16(0xff10a8),
      r16(0xff10ae), r16(0xff10b0), r16(0xff10ec), r16(0xff10ee),
      r16(0xff10ca), r16(0xff10cc), r16(0xff10f6),
      program:read_u32(0xff10fc) & 0xffffffff, r16(0xff1386),
      r8(0xff0118), r16(0xff1360), r16(0xff1362)))
    out:close()
  elseif captured_frame and frame >= captured_frame + 2 then
    write_cycles()
    machine:exit()
  elseif frame >= (r1s2_route and 6000 or 1200) then
    local out = assert(io.open(trace_dir .. "/capture_failed.txt", "w"))
    out:write("initial Segment-0 state not reached\n")
    out:close()
    write_cycles()
    machine:exit()
  end
end)
