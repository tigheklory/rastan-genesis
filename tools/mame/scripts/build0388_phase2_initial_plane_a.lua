-- Build 0388 bounded GENESIS NTSC evidence trace.
--
-- Reuses the established six-button MODE transition and MAME VRAM/program-space
-- interfaces.  It records only the R1 Phase-2 entry ordering, the final Plane-A
-- staging/VRAM/collision summaries, and the first later foreground-Y change.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"], "missing :maincpu")
local p = assert(cpu.spaces["program"], "missing program space")
local vdp = assert(m.devices[":gen_vdp"], "missing :gen_vdp")
local vram = assert(vdp.spaces["videoram"], "missing Genesis VRAM space")
local outdir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local summary = assert(io.open(outdir .. "/phase2_initial_state.tsv", "w"))
local events = assert(io.open(outdir .. "/phase2_initial_events.tsv", "w"))
local cells = assert(io.open(outdir .. "/phase2_initial_cells.tsv", "w"))

local A5 = 0x00ff0000
local STAGE = 0x00ff50a0             -- Build 0386 staged_fg_buffer
local COLLISION = 0x00ff1e00
local ACTIVE_RECORD = 0x00ffb22c
local ACTIVE_PACKAGE = 0x00ffb230
local PENDING_RECORD = 0x00ffb232
local PENDING_PACKAGE = 0x00ffb236
local RESEED_PENDING = 0x00ffb23a
local MISS_A = 0x00ffb208
local EPOCH = 0x00ffb200
local FG_DIRTY = 0x00ff4006
local frame = -1
local taps = {}
local fields = {}
local phase2_frame, phase2_candidate_frame, stable_frame, first_y_frame = nil, nil, nil, nil
local previous_record, previous_y = nil, nil
local initial_y, last_y_change_frame = nil, -1
local closed = false
local published_plane_a = {}
local vdp_autoinc, vdp_addr, vdp_ctrl_first = 2, nil, nil
local dma_len_lo, dma_len_hi = 0, 0
local dma_src_lo, dma_src_mid, dma_src_hi = 0, 0, 0
local plane_a_publication_words = 0
local before_stage_words = nil
local before_vram_words = nil
local first_stage_change_frame = nil
local raw_vdp_controls = 0

for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
assert(fields["P1 Mode"], "P1 Mode unavailable: launch with -ctrl1 md6button")
local function key(name, on)
  if fields[name] then fields[name]:set_value(on and 1 or 0) end
end
local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function direct_v16(a) return vram:read_u16(a) & 0xffff end
local function pc()
  local s = cpu.state["CURPC"] or cpu.state["PC"]
  return s and (s.value & 0xffffff) or 0
end
local function h(v, n) return string.format("%0" .. n .. "X", v) end

summary:write(table.concat({
  "frame", "event", "pc", "phase_state", "record", "selector", "stream_ptr",
  "strip", "group", "fg_x", "fg_y", "scroll_req_x", "scroll_req_y",
  "active_record", "active_package", "pending_record", "pending_package",
  "reseed_pending", "miss_a", "epoch", "fg_dirty", "source_ptrs_valid",
  "stage_nonblank", "stage_sum", "vram_nonblank", "vram_sum",
  "collision_nonzero", "collision_sum"
}, "\t"), "\n")
events:write("frame\tevent\tpc\taddress\tvalue\trecord\tselector\tactive_package\tmiss_a\n")
cells:write("frame\tevent\trow\tcol\tsource_descriptor\tstaged_word\tvram_word\tcollision_word\n")

local function aggregate(space, base, words, mask)
  local nz, sum = 0, 0
  for i = 0, words - 1 do
    local w = space:read_u16(base + i * 2) & 0xffff
    local value = mask and (w & mask) or w
    if value ~= 0 then nz = nz + 1 end
    sum = (sum + w) & 0xffffffff
  end
  return nz, sum
end
local function aggregate_vram(byte_base, words, mask)
  local nz, sum = 0, 0
  for i = 0, words - 1 do
    local w = published_plane_a[i] or 0
    local value = mask and (w & mask) or w
    if value ~= 0 then nz = nz + 1 end
    sum = (sum + w) & 0xffffffff
  end
  return nz, sum
end
local function source_ptrs_valid()
  for i = 0, 15 do
    local q = r32(A5 + 0x1000 + i * 4) & 0xffffff
    if q < 0x01691c or q >= 0x03951c or (q & 1) ~= 0 then return false end
  end
  return true
end
local function state_row(event)
  local sn, ss = aggregate(p, STAGE, 2048, 0x07ff)
  local vn, vs = aggregate_vram(0xe000, 2048, 0x07ff)
  local cn, cs = aggregate(p, COLLISION, 4096, nil)
  summary:write(string.format(
    "%d\t%s\t%06X\t%04X\t%04X\t%04X\t%08X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%02X\t%08X\t%08X\t%08X\t%s\t%d\t%08X\t%d\t%08X\t%d\t%08X\n",
    frame, event, pc(), r16(A5+0x0002), r16(A5+0x013e), r16(A5+0x10a8),
    r32(A5+0x10c6), r16(A5+0x10ca), r16(A5+0x10cc), r16(A5+0x10ae),
    r16(A5+0x10b0), r16(A5+0x10dc), r16(A5+0x10de), r16(ACTIVE_RECORD),
    r16(ACTIVE_PACKAGE), r16(PENDING_RECORD), r16(PENDING_PACKAGE), r8(RESEED_PENDING),
    r32(MISS_A), r32(EPOCH), r32(FG_DIRTY), source_ptrs_valid() and "YES" or "NO",
    sn, ss, vn, vs, cn, cs))
  summary:flush()
end

local function cell_rows(event)
  -- Bounded 40x28 visible window under the current initial scroll.  The trace
  -- records a representative 5x5 grid; the binary dumps preserve all cells.
  local base_row = (r16(A5+0x10b0) >> 3) & 31
  local base_col = ((-r16(A5+0x10ae)) >> 3) & 63
  for dr = 0, 24, 6 do
    for dc = 0, 36, 9 do
      local row, col = (base_row + dr) & 31, (base_col + dc) & 63
      local desc = r32(A5 + 0x1000 + (((row >> 2) & 15) * 4))
      local idx = row * 64 + col
      cells:write(string.format("%d\t%s\t%d\t%d\t%08X\t%04X\t%04X\t%04X\n",
        frame, event, row, col, desc, r16(STAGE + idx*2),
        published_plane_a[idx] or 0, r16(COLLISION + idx*2)))
    end
  end
  cells:flush()
end

local function dump(path, space, base, bytes)
  local f = assert(io.open(outdir .. "/" .. path, "wb"))
  for i = 0, bytes - 1 do f:write(string.char(space:read_u8(base+i) & 0xff)) end
  f:close()
end
local function dump_vram(path, byte_base, words)
  local f = assert(io.open(outdir .. "/" .. path, "wb"))
  for i = 0, words - 1 do
    local w = published_plane_a[i] or 0
    f:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  f:close()
end
local function snapshot(label)
  state_row(label)
  cell_rows(label)
  dump(label .. "_stage.bin", p, STAGE, 0x1000)
  dump_vram(label .. "_vram.bin", 0xe000, 2048)
  dump(label .. "_collision.bin", p, COLLISION, 0x2000)
  dump(label .. "_sources.bin", p, A5+0x1000, 0x40)
end

local function event(name, addr, value)
  events:write(string.format("%d\t%s\t%06X\t%06X\t%08X\t%04X\t%04X\t%04X\t%08X\n",
    frame, name, pc(), addr & 0xffffff, value & 0xffffffff, r16(A5+0x013e),
    r16(A5+0x10a8), r16(ACTIVE_PACKAGE), r32(MISS_A)))
  events:flush()
end

local function tap16(first, last, name)
  taps[#taps+1] = p:install_write_tap(first, last, name, function(off, data, mask)
    event(name, off, data & 0xffff)
    return data
  end)
end
local function publish_word(byte_addr, word)
  if byte_addr >= 0xe000 and byte_addr < 0xf000 then
    local index = (byte_addr - 0xe000) >> 1
    published_plane_a[index] = word & 0xffff
    plane_a_publication_words = plane_a_publication_words + 1
  end
end
local function accept_vdp_command(cmd)
  local addr = ((cmd >> 16) & 0x3fff) | ((cmd & 3) << 14)
  local dma = (cmd & 0x80) ~= 0
  vdp_addr = addr
  if dma and addr >= 0xe000 and addr < 0xf000 then
    local len = (dma_len_hi << 8) | dma_len_lo
    if len == 0 then len = 0x10000 end
    -- Plane-A publications are bounded to one 2048-word plane or shorter
    -- row/column jobs.  Ignore unrelated VDP DMA commands here.
    if len > 2048 then return end
    local src = ((dma_src_hi << 16) | (dma_src_mid << 8) | dma_src_lo) * 2
    for i = 0, len - 1 do
      publish_word((addr + i*vdp_autoinc) & 0xffff, r16((src + i*2) & 0xffffff))
    end
  end
end
local runtime_taps_installed = false
local function install_runtime_taps()
  if runtime_taps_installed then return end
  runtime_taps_installed = true
  tap16(A5+0x013e, A5+0x013f, "RECORD_WRITE")
  tap16(A5+0x1000, A5+0x103f, "SOURCE_PTR_WRITE")
  tap16(ACTIVE_RECORD, ACTIVE_RECORD+1, "ACTIVE_RECORD_WRITE")
  tap16(ACTIVE_PACKAGE, ACTIVE_PACKAGE+1, "ACTIVE_PACKAGE_WRITE")
  tap16(RESEED_PENDING, RESEED_PENDING+1, "RESEED_WRITE")
  tap16(STAGE, STAGE+0x0fff, "STAGE_WRITE")
  tap16(COLLISION, COLLISION+0x1fff, "COLLISION_WRITE")
  taps[#taps+1] = p:install_write_tap(0xc00004, 0xc00007, "phase2_vdp_control",
  function(_, data, mask)
    if raw_vdp_controls < 80 then
      raw_vdp_controls = raw_vdp_controls + 1
      events:write(string.format("%d\tVDP_CTRL_RAW\t%06X\tC00004\t%08X\t%04X\t%04X\t%04X\t%08X\n",
        frame, pc(), data & 0xffffffff, r16(A5+0x013e), r16(A5+0x10a8),
        r16(ACTIVE_PACKAGE), r32(MISS_A)))
    end
    if mask == 0xffffffff then
      accept_vdp_command(data & 0xffffffff)
    else
      local w = data & 0xffff
      if (w & 0xff00) == 0x8f00 then vdp_autoinc = w & 0xff; vdp_ctrl_first = nil
      elseif (w & 0xff00) == 0x9300 then dma_len_lo = w & 0xff; vdp_ctrl_first = nil
      elseif (w & 0xff00) == 0x9400 then dma_len_hi = w & 0xff; vdp_ctrl_first = nil
      elseif (w & 0xff00) == 0x9500 then dma_src_lo = w & 0xff; vdp_ctrl_first = nil
      elseif (w & 0xff00) == 0x9600 then dma_src_mid = w & 0xff; vdp_ctrl_first = nil
      elseif (w & 0xff00) == 0x9700 then dma_src_hi = w & 0x7f; vdp_ctrl_first = nil
      elseif not vdp_ctrl_first then vdp_ctrl_first = w
      else accept_vdp_command((vdp_ctrl_first << 16) | w); vdp_ctrl_first = nil end
    end
    return data
  end)
  taps[#taps+1] = p:install_write_tap(0xc00000, 0xc00001, "phase2_vdp_data",
  function(_, data, _)
    if vdp_addr then
      publish_word(vdp_addr, data & 0xffff)
      vdp_addr = (vdp_addr + vdp_autoinc) & 0xffff
    end
    return data
  end)
end

local function close()
  if closed then return end
  closed = true
  summary:close(); events:close(); cells:close()
end

emu.register_frame_done(function()
  frame = frame + 1
  if frame == 250 then install_runtime_taps() end
  key("Coin 1", frame >= 120 and frame <= 132)
  key("P1 A", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187)
  key("P1 Start", frame >= 175 and frame <= 187)
  key("P1 Mode", frame >= 600 and frame <= 612)

  local rec, y = r16(A5+0x013e), r16(A5+0x10b0)
  if previous_record ~= rec then state_row("RECORD_CHANGE"); previous_record = rec end
  if previous_y ~= y then
    event("FG_Y_CHANGE", A5+0x10b0, y)
    previous_y = y
    last_y_change_frame = frame
  end
  -- Record 16 is the transition/reseed operation.  The user-visible Phase-2
  -- entry is stable record 17 / selector 1 after its own Y initialization has
  -- stopped; only then begin the required no-input interval.
  if rec == 0x11 and r16(A5+0x10a8) == 1 then
    if not phase2_candidate_frame then phase2_candidate_frame = frame end
  else
    phase2_candidate_frame = nil
  end
  if not phase2_frame and phase2_candidate_frame and
     frame-phase2_candidate_frame >= 30 and frame-last_y_change_frame >= 30 then
    phase2_frame = frame
    initial_y = y
    snapshot("phase2_entry")
  end
  if phase2_frame and not stable_frame and frame - phase2_frame >= 120 then
    stable_frame = frame
    snapshot("before_scroll")
    before_stage_words = {}
    for i = 0, 2047 do before_stage_words[i] = r16(STAGE+i*2) end
    before_vram_words = {}
    for i = 0, 2047 do before_vram_words[i] = published_plane_a[i] or 0 end
  end

  -- After the no-movement entry snapshot, reuse the established Phase-2 route cadence.
  if stable_frame then
    local t = frame - stable_frame
    key("P1 Left", (t < 1200) or (t >= 1800 and t < 3000))
    key("P1 Right", (t >= 1200 and t < 1800) or t >= 3000)
    key("P1 Up", (t % 360) >= 120 and (t % 360) < 330)
    key("P1 Button 2", (t % 90) < 12)
    key("P1 C", (t % 90) < 12)
  end
  if stable_frame and frame > stable_frame and not first_stage_change_frame and before_stage_words then
    local changed = 0
    for i = 0, 2047 do
      if r16(STAGE+i*2) ~= before_stage_words[i] then changed = changed + 1 end
    end
    if changed ~= 0 then
      first_stage_change_frame = frame
      event("FIRST_VERTICAL_STAGE_CHANGE", STAGE, changed)
    end
  end
  if first_stage_change_frame and not first_y_frame and before_vram_words then
    local changed = 0
    for i = 0, 2047 do
      if (published_plane_a[i] or 0) ~= before_vram_words[i] then changed = changed + 1 end
    end
    if changed ~= 0 then
      first_y_frame = frame
      event("FIRST_VERTICAL_VDP_CHANGE", 0xe000, changed)
      snapshot("first_vertical_scroll")
    end
  end
  if frame >= 5000 or (first_y_frame and frame-first_y_frame >= 30) then
    snapshot("final")
    close()
    m:exit()
  end
end)

_G.build0388_phase2_initial_plane_a_stop = emu.add_machine_stop_notifier(close)
