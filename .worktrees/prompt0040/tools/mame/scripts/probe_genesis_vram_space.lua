-- Terminal read of the actual Mega Drive VDP's 64 KiB VRAM.
--
-- MAME's :gen_vdp "videoram" Lua address space is the inherited 16 KiB
-- Mode-4 compatibility space (mask 0x3FFF), not sega315_5313_device::m_vram.
-- There is therefore no Lua-space alias for CPU-visible MD VRAM 0xF800.
-- This probe snapshots one displayed frame, reads the real VRAM through the
-- 68000 VDP data port, writes the evidence, and exits without resuming.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local vdp = assert(m.devices[":gen_vdp"])
local compat = assert(vdp.spaces["videoram"])
local outdir = assert(os.getenv("VDP_READ_OUTDIR"), "VDP_READ_OUTDIR required")
local target = tonumber(os.getenv("VDP_READ_FRAME") or "525")
os.execute('mkdir -p "' .. outdir .. '"')

local fields = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  local f = fields[name]
  if f then f:set_value(on and 1 or 0) end
end

local function vdp_read_command(address)
  p:write_u16(0x00c00004, address & 0x3fff)
  p:write_u16(0x00c00004, (address >> 14) & 3)
end

local function dump_actual_vram()
  local meta = assert(io.open(outdir .. "/vdp_mapping.txt", "w"))
  meta:write(string.format("compat_address_mask=0x%X\n", compat.address_mask))
  meta:write(string.format("compat_data_width=%d\n", compat.data_width))
  meta:write(string.format("compat_endianness=%s\n", tostring(compat.endianness)))
  meta:write("compat_space_role=Mode-4 compatibility VRAM; not Mega Drive m_vram\n")
  meta:write("actual_md_vram_access=68000 VDP data port terminal read\n")
  meta:write(string.format("display_frame=%d\n", target))
  meta:close()

  p:write_u16(0x00c00004, 0x8f02)
  vdp_read_command(0)
  local raw = assert(io.open(outdir .. "/actual_vram.bin", "wb"))
  local words = {}
  for i = 0, 0x7fff do
    local w = p:read_u16(0x00c00000) & 0xffff
    words[i] = w
    raw:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  raw:close()

  local sat = assert(io.open(outdir .. "/actual_published_sat.tsv", "w"))
  sat:write("chain_order\tsat_index\ty\tsize\twidth_tiles\theight_tiles\tpattern\tpalette\thflip\tvflip\tpriority\tx\tlink\n")
  local index, seen = 0, {}
  for order = 0, 79 do
    if seen[index] then break end
    seen[index] = true
    local wi = (0xf800 >> 1) + index * 4
    local y, size, attr, x = words[wi], words[wi+1], words[wi+2], words[wi+3]
    local width = ((size >> 10) & 3) + 1
    local height = ((size >> 8) & 3) + 1
    local link = size & 0x7f
    sat:write(string.format("%d\t%d\t%d\t%04X\t%d\t%d\t%04X\t%d\t%d\t%d\t%d\t%d\t%d\n",
      order,index,(y & 0x1ff)-128,size,width,height,attr & 0x7ff,(attr >> 13)&3,
      (attr >> 11)&1,(attr >> 12)&1,(attr >> 15)&1,(x & 0x1ff)-128,link))
    if link == 0 then break end
    index = link
  end
  sat:close()
end

local function dump_native_state()
  local state = assert(io.open(outdir .. "/native_state.tsv", "w"))
  state:write("field\tvalue\n")
  state:write(string.format("sat_front\t%d\n", p:read_u16(0x00ffb73e) & 0xffff))
  state:write(string.format("sat_ready\t%d\n", p:read_u16(0x00ffb740) & 0xffff))
  state:write(string.format("dma_count\t%d\n", p:read_u16(0x00ffb7e8) & 0xffff))
  state:write(string.format("emitted\t%d\n", p:read_u16(0x00ffbed4) & 0xffff))
  state:write(string.format("dropped_cumulative\t%d\n", p:read_u16(0x00ffbed6) & 0xffff))
  state:write(string.format("back_enemy_count\t%d\n", p:read_u16(0x00ffb7fe) & 0xffff))
  state:close()

  local queue = assert(io.open(outdir .. "/back_enemy_queue.tsv", "w"))
  queue:write("index\tattr\ty\tkey\tx\n")
  local count = p:read_u16(0x00ffb7fe) & 0xffff
  for i = 0, count - 1 do
    local a = 0x00ffbbb8 + i * 8
    queue:write(string.format("%d\t%04X\t%d\t%04X\t%d\n", i,
      p:read_u16(a) & 0xffff, p:read_u16(a + 2) & 0xffff,
      p:read_u16(a + 4) & 0xffff, p:read_u16(a + 6) & 0xffff))
  end
  queue:close()

  local actors = assert(io.open(outdir .. "/enemy_actors.tsv", "w"))
  actors:write("slot\tactive\tselector\tfield02\tfield03\tfield20\tattr27\tbase\tx\ty\n")
  for slot = 0, 8 do
    local a = 0x00ff02c8 + slot * 0x40
    actors:write(string.format("%d\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\t%04X\t%d\t%d\n",
      slot, p:read_u8(a) & 0xff, p:read_u8(a + 1) & 0xff,
      p:read_u8(a + 2) & 0xff, p:read_u8(a + 3) & 0xff,
      p:read_u8(a + 0x20) & 0xff, p:read_u8(a + 0x27) & 0xff,
      p:read_u16(a + 0x1e) & 0xffff, p:read_u16(a + 0x16) & 0xffff,
      p:read_u16(a + 0x1a) & 0xffff))
  end
  actors:close()
end

local frame = -1
local qfull_log
local qfull_tap
local enqueue_log
local enqueue_tap
local table_log
local table_tap
if os.getenv("VDP_TRACE_QFULL") == "1" then
  qfull_log = assert(io.open(outdir .. "/residency_qfull.tsv", "w"))
  qfull_log:write("frame\tpc\tworklist_count\tkey\tattr\ty\tx\temitted\n")
  qfull_tap = p:install_write_tap(0x00ffbed6, 0x00ffbed7,
    "terminal_residency_drop", function(_, data)
      local pc = cpu.state["PC"].value & 0xffffff
      qfull_log:write(string.format("%d\t%06X\t%d\t%04X\t%04X\t%d\t%d\t%d\n",
        frame, pc, p:read_u16(0x00ffb7e8) & 0xffff,
        cpu.state["D3"].value & 0xffff, cpu.state["D1"].value & 0xffff,
        cpu.state["D2"].value & 0xffff, cpu.state["D4"].value & 0xffff,
        cpu.state["D5"].value & 0xffff))
      qfull_log:flush()
      return data
    end)
  _G.build0409_terminal_qfull_tap = qfull_tap
end
if os.getenv("VDP_TRACE_ENQUEUE") == "1" then
  enqueue_log = assert(io.open(outdir .. "/back_enemy_enqueues.tsv", "w"))
  enqueue_log:write("frame\tpc\tnew_count\tactor\td7\tattr\ty\tkey\tx\n")
  enqueue_tap = p:install_write_tap(0x00ffb7fe, 0x00ffb7ff,
    "terminal_back_enemy_enqueue", function(_, data)
      local pc = cpu.state["PC"].value & 0xffffff
      local count = data & 0xffff
      local actor = cpu.state["A4"].value & 0xffffff
      local entry = 0x00ffbbb8 + math.max(0, count - 1) * 8
      enqueue_log:write(string.format("%d\t%06X\t%d\t%06X\t%d\t%04X\t%d\t%04X\t%d\n",
        frame, pc, count, actor, cpu.state["D7"].value & 0xffff,
        p:read_u16(entry) & 0xffff, p:read_u16(entry + 2) & 0xffff,
        p:read_u16(entry + 4) & 0xffff, p:read_u16(entry + 6) & 0xffff))
      enqueue_log:flush()
      return data
    end)
  _G.build0409_terminal_enqueue_tap = enqueue_tap
end
if os.getenv("VDP_TRACE_LIZARD_TABLE") == "1" then
  table_log = assert(io.open(outdir .. "/lizard_table_reads.tsv", "w"))
  table_log:write("frame\tpc\taddress\tdata\tactor\td7\ta0\ta2\ta3\ta6\n")
  table_tap = p:install_read_tap(0x001122be, 0x0011230d,
    "terminal_lizard_frame_reads", function(offset, data)
      table_log:write(string.format("%d\t%06X\t%06X\t%04X\t%06X\t%d\t%06X\t%06X\t%06X\t%06X\n",
        frame, cpu.state["PC"].value & 0xffffff, offset & 0xffffff,
        data & 0xffff, cpu.state["A4"].value & 0xffffff,
        cpu.state["D7"].value & 0xffff, cpu.state["A0"].value & 0xffffff,
        cpu.state["A2"].value & 0xffffff, cpu.state["A3"].value & 0xffffff,
        cpu.state["A6"].value & 0xffffff))
      table_log:flush()
      return data
    end)
  _G.build0409_terminal_table_tap = table_tap
end
emu.register_frame_done(function()
  frame = frame + 1
  key("P1 A", frame >= 120 and frame <= 132)
  key("Coin 1", frame >= 120 and frame <= 132)
  key("P1 Start", frame >= 175 and frame <= 187)
  key("1 Player Start", frame >= 175 and frame <= 187)
  key("P1 Right", frame >= 360)
  key("P1 C", frame >= 360 and frame % 90 < 12)
  key("P1 B", frame >= 360 and frame % 30 < 6)
  if frame == target then
    pcall(function() m.video:snapshot() end)
    dump_native_state()
    dump_actual_vram()
    if qfull_log then qfull_log:close() end
    if enqueue_log then enqueue_log:close() end
    if table_log then table_log:close() end
    m:exit()
  end
end)

print(string.format("[probe_genesis_vram_space] terminal actual-VRAM read at frame %d", target))
