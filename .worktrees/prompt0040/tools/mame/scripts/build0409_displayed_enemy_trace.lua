-- Build-0408 persistent enemy-body regression: displayed-frame audit.
-- Host-only deterministic controller input and read-only state capture.
-- No emulated-memory writes, save-state injection, or synthetic actors.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"], "missing Genesis main CPU")
local p = assert(cpu.spaces["program"], "missing Genesis program space")
local outdir = assert(os.getenv("DISPLAY_SPRITE_OUTDIR"), "DISPLAY_SPRITE_OUTDIR required")
local label = os.getenv("DISPLAY_SPRITE_LABEL") or "unknown"
local max_frames = tonumber(os.getenv("DISPLAY_SPRITE_MAX_FRAMES") or "2400")
os.execute('mkdir -p "' .. outdir .. '"')

local frames = assert(io.open(outdir .. "/display_frames.tsv", "w"))
local satout = assert(io.open(outdir .. "/published_sat.tsv", "w"))
local actors = assert(io.open(outdir .. "/target_actors.tsv", "w"))
local pubs = assert(io.open(outdir .. "/publication_events.tsv", "w"))
frames:write("build\tframe\tsnapshot\ttargets\tsat_entries\tmax_scanline_sprites\tmax_scanline_cells\tmax_scanline\thud\tfront_effect\tplayer_front\tmiddle\tplayer_body\tback_enemy\temitted\tdropped\tdma_count\tsat_front\tsat_ready\n")
satout:write("build\tframe\tsnapshot\tchain_order\tsat_index\tx\ty\twidth_tiles\theight_tiles\tpattern\tpalette\thflip\tvflip\tpriority\tlink\tresident_code\tinstall_frame\tpattern_hex\n")
actors:write("build\tframe\tsnapshot\tslot\tactor\tactive\tselector\torientation\tstate\tsubframe\tbase\tcompositor\tx\ty\n")
pubs:write("build\tframe\tevent\tbank_or_count\tdetail\n")

local function r8(space, a) return space:read_u8(a) & 0xff end
local function r16(space, a) return space:read_u16(a) & 0xffff end
local function signed16(v) return v >= 0x8000 and (v - 0x10000) or v end
local function bytes_hex(address, bytes)
  local out = {}
  for i = 0, bytes - 1 do out[#out + 1] = string.format("%02X", r8(p, address + i)) end
  return table.concat(out)
end

local fields = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  local field = fields[name]
  if field then field:set_value(on and 1 or 0) end
end

local A5 = 0x00ff0000
local TARGET_FIRST = A5 + 0x02c8
local TARGET_SLOTS = 9
local TARGET_STRIDE = 0x40
local SAT_A = 0x00ffb23c
local SAT_B = 0x00ffb4bc
local SAT_FRONT = 0x00ffb73e
local DMA_WORK = 0x00ffb7b8
local DMA_COUNT = 0x00ffb7e8
local counts = {0x00ffb7f4, 0x00ffb7f6, 0x00ffb7f8, 0x00ffb7fa, 0x00ffb7fc, 0x00ffb7fe}
local frame = -1
local shot = 0
local closed = false
local taps = {}
local published_words = {}
local resident = {}
local last_dma_key = ""

local function copy_published_bank(bank)
  local base = bank == 0 and SAT_A or SAT_B
  for i = 0, 319 do published_words[i] = r16(p, base + i * 2) end
end

local function reg(name)
  local e = cpu.state[name]
  return e and (e.value & 0xffffffff) or 0
end

do
  local tap = p:install_write_tap(SAT_FRONT, SAT_FRONT + 1, "display_sat_publication", function(_, data)
    local bank = data & 1
    copy_published_bank(bank)
    pubs:write(string.format("%s\t%d\tSAT_DMA_SOURCE\t%d\t640 bytes -> VRAM F800\n", label, frame, bank))
    pubs:flush()
    return data
  end)
  taps[#taps + 1] = tap
  tap = p:install_write_tap(DMA_COUNT, DMA_COUNT + 1, "display_pattern_publication", function(_, data)
    local old = r16(p, DMA_COUNT)
    if data == 0 and old > 0 then
      local detail = {}
      for i = 0, old - 1 do
        local slot = r16(p, DMA_WORK + i * 4)
        local code = r16(p, DMA_WORK + i * 4 + 2)
        if code ~= 0xffff then
          -- Semantic worklist observation only.  The exact VDP DMA tap below
          -- owns the actual installed source bytes and publication frame.
          local oldr = resident[slot] or {}
          oldr.code = code
          resident[slot] = oldr
          detail[#detail + 1] = string.format("%d:%04X", slot, code)
        end
      end
      pubs:write(string.format("%s\t%d\tPATTERN_DMA_COMMIT\t%d\t%s\n", label, frame, old, table.concat(detail, ";")))
      pubs:flush()
    end
    return data
  end)
  taps[#taps + 1] = tap
  tap = p:install_write_tap(0x00c00004, 0x00c00007, "display_exact_vdp_dma", function(_, data)
    -- dma_words_to_vram_noai emits its final 32-bit destination command at
    -- runtime PC 0x07034C in Builds 0406/0408.  At that instruction D0 is the exact VRAM byte
    -- destination and A0 remains the exact 68K byte source.
    local write_pc = reg("PC") & 0xffffff
    if write_pc == 0x07034c or write_pc == 0x070348 or write_pc == 0x07034a then
      local dest = reg("D0") & 0xffff
      local source = reg("A0") & 0xffffff
      local dma_key = string.format("%d:%04X:%06X", frame, dest, source)
      if dma_key == last_dma_key then return data end
      last_dma_key = dma_key
      if dest == 0xf800 then
        for i = 0, 319 do published_words[i] = r16(p, source + i * 2) end
        pubs:write(string.format("%s\t%d\tSAT_DMA_EXACT\t640\tsource=%06X dest=F800\n", label, frame, source))
      elseif dest >= 1339 * 32 and dest < (1339 + 49 * 4) * 32 then
        local slot = ((dest // 32) - 1339) // 4
        local rr = resident[slot] or {}
        rr.frame = frame
        rr.source = source
        rr.hex = bytes_hex(source, 128)
        resident[slot] = rr
        pubs:write(string.format("%s\t%d\tPATTERN_DMA_EXACT\t%d\tsource=%06X dest=%04X\n", label, frame, slot, source, dest))
      end
      pubs:flush()
    end
    return data
  end)
  taps[#taps + 1] = tap
end
-- MAME tap objects must remain strongly reachable after the autoboot chunk
-- returns; otherwise Lua GC silently removes them during the run.
_G.build0409_display_taps = taps

local function read_sat()
  local entries, seen = {}, {}
  local index = 0
  for order = 0, 79 do
    if seen[index] then break end
    seen[index] = true
    local wi = index * 4
    local wy = published_words[wi] or 0
    local sl = published_words[wi + 1] or 0
    local at = published_words[wi + 2] or 0
    local wx = published_words[wi + 3] or 0
    local width = ((sl >> 10) & 3) + 1
    local height = ((sl >> 8) & 3) + 1
    entries[#entries + 1] = {
      order=order,index=index,x=(wx & 0x1ff)-128,y=(wy & 0x1ff)-128,
      width=width,height=height,pattern=at & 0x07ff,palette=(at >> 13) & 3,
      hf=(at >> 11) & 1,vf=(at >> 12) & 1,priority=(at >> 15) & 1,
      link=sl & 0x7f,
    }
    if (sl & 0x7f) == 0 then break end
    index = sl & 0x7f
  end
  return entries
end

local function scanline_peak(entries)
  local best_n, best_cells, best_y = 0, 0, 0
  for y = 0, 223 do
    local n, cells = 0, 0
    for _, e in ipairs(entries) do
      if y >= e.y and y < e.y + e.height * 8 and e.x > -e.width * 8 and e.x < 320 then
        n = n + 1
        cells = cells + e.width
      end
    end
    if n > best_n or (n == best_n and cells > best_cells) then
      best_n, best_cells, best_y = n, cells, y
    end
  end
  return best_n, best_cells, best_y
end

local function target_rows(snapshot)
  local found = 0
  for slot = 0, TARGET_SLOTS - 1 do
    local a = TARGET_FIRST + slot * TARGET_STRIDE
    local base = r16(p, a + 0x1e)
    if base == 0x004b or base == 0x02e8 then
      found = found + 1
      actors:write(string.format("%s\t%d\t%d\t%d\t%06X\t%02X\t%02X\t%02X\t%02X\t%02X\t%04X\t%02X\t%d\t%d\n",
        label, frame, snapshot, slot, a, r8(p,a), r8(p,a+1), r8(p,a+2), r8(p,a+3),
        r8(p,a+0x0b), base, r8(p,a+0x38), signed16(r16(p,a+0x16)), signed16(r16(p,a+0x1a))))
    end
  end
  return found
end

local function close()
  if closed then return end
  closed = true
  frames:flush(); satout:flush(); actors:flush(); pubs:flush()
  frames:close(); satout:close(); actors:close(); pubs:close()
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

  local target_count = 0
  for slot = 0, TARGET_SLOTS - 1 do
    local a = TARGET_FIRST + slot * TARGET_STRIDE
    local base = r16(p, a + 0x1e)
    if base == 0x004b or base == 0x02e8 then target_count = target_count + 1 end
  end
  if target_count > 0 then
    shot = shot + 1
    pcall(function() m.video:snapshot() end)
    local entries = read_sat()
    local peak_n, peak_cells, peak_y = scanline_peak(entries)
    target_rows(shot)
    frames:write(string.format("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d",
      label, frame, shot, target_count, #entries, peak_n, peak_cells, peak_y))
    for _, a in ipairs(counts) do frames:write("\t", tostring(r16(p,a))) end
    frames:write(string.format("\t%d\t%d\t%d\t%d\t%d\n", r16(p,0x00ffbed4),
      r16(p,0x00ffbed6), r16(p,0x00ffb7e8), r16(p,0x00ffb73e), r16(p,0x00ffb740)))
    for _, e in ipairs(entries) do
      local cell = (e.pattern - 1339) // 4
      local rr = resident[cell]
      local code = rr and string.format("%04X", rr.code) or "UNKNOWN"
      local install = rr and tostring(rr.frame) or "UNKNOWN"
      local hex = rr and rr.hex or "UNKNOWN"
      satout:write(string.format("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%04X\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\n",
        label, frame, shot, e.order, e.index, e.x, e.y, e.width, e.height, e.pattern,
        e.palette, e.hf, e.vf, e.priority, e.link, code, install, hex))
    end
    frames:flush(); satout:flush(); actors:flush()
  end
  if frame >= max_frames then close(); m:exit() end
end)

pcall(function() emu.add_machine_stop_notifier(close) end)
print("[displayed_enemy_trace] READY -> " .. outdir)
