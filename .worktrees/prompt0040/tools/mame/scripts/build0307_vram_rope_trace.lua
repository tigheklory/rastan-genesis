-- Build 0307 bounded observation: actual VRAM ownership and Stage-1 rope visibility.
-- Evidence only. This script does not modify emulated memory or ROM behavior.

local outdir = assert(os.getenv("BUILD0307_TRACE_DIR"), "BUILD0307_TRACE_DIR is required")
local cpu = assert(manager.machine.devices[":maincpu"], "Genesis main CPU unavailable")
local prog = assert(cpu.spaces["program"], "Genesis program space unavailable")
local vdp = assert(manager.machine.devices[":gen_vdp"], "Genesis VDP unavailable")
local vram = assert(vdp.spaces["videoram"], "Genesis VRAM space unavailable")

local frames = assert(io.open(outdir .. "/frames.csv", "w"))
local slots = assert(io.open(outdir .. "/slot_ownership.csv", "w"))
local events = assert(io.open(outdir .. "/events.tsv", "w"))
local metadata = assert(io.open(outdir .. "/metadata.txt", "w"))

local frame = 0
local snapshot_index = 0
local dump_index = 0
local closed = false
local previous = {}
local initial_fp = {}
local ever_changed = {}

local function r8(space, address)
  return space:read_u8(address) & 0xff
end

local function r16(space, address)
  return space:read_u16(address) & 0xffff
end

local function r16v(address)
  return ((r8(vram, address) << 8) | r8(vram, address + 1)) & 0xffff
end

local function r32(space, address)
  return space:read_u32(address) & 0xffffffff
end

local function pattern_fp(slot)
  local address = slot * 32
  return (r32(vram, address) ~ r32(vram, address + 8) ~
          r32(vram, address + 16) ~ r32(vram, address + 28)) & 0xffffffff
end

local function add_range(set, first, count)
  for slot = first, first + count - 1 do
    if slot >= 0 and slot <= 1535 then set[slot] = true end
  end
end

local function read_plane(base)
  local set = {}
  local cells = 0
  for index = 0, 2047 do
    local word = r16v(base + index * 2)
    local slot = word & 0x07ff
    if slot ~= 0 then
      set[slot] = true
      cells = cells + 1
    end
  end
  return set, cells
end

local function read_sat()
  local set = {}
  local entries = 0
  local index = 0
  local visited = {}
  while entries < 80 and not visited[index] do
    visited[index] = true
    local address = 0xf800 + index * 8
    local size_link = r16v(address + 2)
    local attr = r16v(address + 4)
    local width = ((size_link >> 10) & 3) + 1
    local height = ((size_link >> 8) & 3) + 1
    add_range(set, attr & 0x07ff, width * height)
    entries = entries + 1
    local link = size_link & 0x007f
    if link == 0 then break end
    index = link
  end
  return set, entries
end

local function set_count(set)
  local count = 0
  for _ in pairs(set) do count = count + 1 end
  return count
end

local function set_ranges(set)
  local out = {}
  local first = nil
  local last = nil
  for slot = 0, 1535 do
    if set[slot] then
      if not first then first = slot end
      last = slot
    elseif first then
      out[#out + 1] = first == last and tostring(first) or (tostring(first) .. "-" .. tostring(last))
      first, last = nil, nil
    end
  end
  if first then
    out[#out + 1] = first == last and tostring(first) or (tostring(first) .. "-" .. tostring(last))
  end
  return table.concat(out, ";")
end

local function union(a, b, c)
  local out = {}
  for slot in pairs(a) do out[slot] = true end
  for slot in pairs(b) do out[slot] = true end
  for slot in pairs(c) do out[slot] = true end
  return out
end

local function used_cell_set()
  local out = {}
  for cell = 0, 127 do
    local byte = r8(prog, 0x00ffb7ae + (cell >> 3))
    if (byte & (1 << (cell & 7))) ~= 0 then out[1024 + cell * 4] = true end
  end
  return out
end

local function resident_cell_count()
  local count = 0
  for cell = 0, 127 do
    if r16(prog, 0x00ffb7be + cell * 2) ~= 0 then count = count + 1 end
  end
  return count
end

local function dump_vram(reason)
  dump_index = dump_index + 1
  local path = string.format("%s/vram_%04d_frame_%06d.bin", outdir, dump_index, frame)
  local file = assert(io.open(path, "wb"))
  local chunk = {}
  for address = 0, 0xffff do
    chunk[#chunk + 1] = string.char(r8(vram, address))
    if #chunk == 4096 then file:write(table.concat(chunk)); chunk = {} end
  end
  if #chunk ~= 0 then file:write(table.concat(chunk)) end
  file:close()
  events:write(string.format("%d\tVRAM_DUMP\t%s\t%s\n", frame, reason, path))
end

local function changed(name, value)
  local old = previous[name]
  previous[name] = value
  return old ~= nil and old ~= value
end

local function sample()
  frame = frame + 1
  local scene = r8(prog, 0x00ff707c)
  local segment = r16(prog, 0x00ff013e)
  local selector = r16(prog, 0x00ff10a8)
  local page = r32(prog, 0x00ff10c6) & 0xffffff
  local player_x = r16(prog, 0x00ff10be)
  local player_y = r16(prog, 0x00ff10c0)
  local fg_x = r16(prog, 0x00ff10ae)
  local fg_y = r16(prog, 0x00ff10b0)
  local bg_x = r16(prog, 0x00ff10ec)
  local bg_y = r16(prog, 0x00ff10ee)
  local player_mode = r16(prog, 0x00ff10e8)
  local active_record = r16(prog, 0x00ffb1f8)
  local active_variant = r16(prog, 0x00ffb1fa)
  local active_package = r8(prog, 0x00ffb1fc)

  local plane_a, plane_a_cells = read_plane(0xe000)
  local plane_b, plane_b_cells = read_plane(0xc000)
  local sat, sat_entries = read_sat()
  local all = union(plane_a, plane_b, sat)
  local used_cells = used_cell_set()

  if frame == 1 then
    for slot = 0, 1535 do initial_fp[slot] = pattern_fp(slot) end
  end
  if frame % 10 == 0 then
    for slot = 0, 1535 do
      if pattern_fp(slot) ~= initial_fp[slot] then ever_changed[slot] = true end
    end
  end

  local relevant = scene == 1 and segment >= 2 and segment <= 3
  local state_change = false
  if changed("scene", scene) then state_change = true end
  if changed("segment", segment) then state_change = true end
  if changed("page", page) then state_change = true end
  if changed("mode", player_mode) then state_change = true end
  if changed("record", active_record) then state_change = true end
  if changed("variant", active_variant) then state_change = true end

  local shot = ""
  if relevant and frame % 5 == 0 then
    snapshot_index = snapshot_index + 1
    shot = tostring(snapshot_index)
    pcall(function() manager.machine.video:snapshot() end)
  end
  if relevant and (state_change or frame % 30 == 0) then
    dump_vram(state_change and "STATE_CHANGE" or "PERIODIC")
  end

  frames:write(table.concat({
    tostring(frame), string.format("%02X", scene), string.format("%04X", segment),
    string.format("%04X", selector), string.format("%06X", page),
    string.format("%04X", player_x), string.format("%04X", player_y),
    string.format("%04X", fg_x), string.format("%04X", fg_y),
    string.format("%04X", bg_x), string.format("%04X", bg_y),
    string.format("%04X", player_mode), string.format("%04X", active_record),
    string.format("%04X", active_variant), string.format("%02X", active_package),
    tostring(plane_a_cells), tostring(set_count(plane_a)), tostring(plane_b_cells),
    tostring(set_count(plane_b)), tostring(sat_entries), tostring(set_count(sat)),
    tostring(set_count(all)), tostring(set_count(used_cells)), tostring(resident_cell_count()),
    set_ranges(plane_a), set_ranges(plane_b), set_ranges(sat), set_ranges(used_cells), shot,
  }, ","), "\n")

  if relevant and (state_change or frame % 5 == 0) then
    for slot = 0, 1535 do
      if all[slot] or ever_changed[slot] then
        slots:write(table.concat({
          tostring(frame), tostring(slot), plane_a[slot] and "1" or "0",
          plane_b[slot] and "1" or "0", sat[slot] and "1" or "0",
          ever_changed[slot] and "1" or "0", string.format("%08X", pattern_fp(slot)),
        }, ","), "\n")
      end
    end
  end

  if frame % 60 == 0 then frames:flush(); slots:flush(); events:flush() end
end

local function close_files()
  if closed then return end
  closed = true
  metadata:write("finished=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
  metadata:write("frames=" .. tostring(frame) .. "\n")
  metadata:write("snapshots=" .. tostring(snapshot_index) .. "\n")
  metadata:write("vram_dumps=" .. tostring(dump_index) .. "\n")
  metadata:write("ever_changed_ranges=" .. set_ranges(ever_changed) .. "\n")
  frames:flush(); slots:flush(); events:flush(); metadata:flush()
  frames:close(); slots:close(); events:close(); metadata:close()
end

frames:write("frame,scene,segment,selector,page,player_x,player_y,fg_x,fg_y,bg_x,bg_y,player_mode,active_record,active_variant,active_package,plane_a_cells,plane_a_slots,plane_b_cells,plane_b_slots,sat_entries,sat_patterns,all_live_patterns,used_sprite_cells,resident_sprite_cells,plane_a_ranges,plane_b_ranges,sat_ranges,used_sprite_cell_bases,snapshot_index\n")
slots:write("frame,slot,plane_a,plane_b,sat,changed_since_boot,fingerprint\n")
events:write("frame\tevent\treason\tpath\n")
metadata:write("build=0306\n")
metadata:write("rom_sha256=7d3ab8daae92712636a1593e8bbad77341c38834dc35ad89a8413618313c2c08\n")
metadata:write("started=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
metadata:write("plane_b_nametable=VRAM 0xC000\n")
metadata:write("plane_a_nametable=VRAM 0xE000\n")
metadata:write("sat=VRAM 0xF800\n")
metadata:write("pattern_slots=0..1535 (VRAM 0x0000..0xBFFF)\n")
metadata:flush()

_G.build0307_vram_rope_frame = emu.add_machine_frame_notifier(function()
  local ok, message = pcall(sample)
  if not ok then emu.print_error("Build0307 VRAM/rope trace: " .. tostring(message)) end
end)
_G.build0307_vram_rope_stop = emu.add_machine_stop_notifier(close_files)

emu.print_info("Build0307 bounded VRAM/rope trace ACTIVE: " .. outdir)
