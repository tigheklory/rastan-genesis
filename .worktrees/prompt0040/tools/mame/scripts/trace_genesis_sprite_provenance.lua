-- GENESIS Build-0327 sprite PROVENANCE + workload trace (TOOLING, non-shipping instrumentation).
-- MAME Lua cannot tap 68000 opcode fetches (install_read_tap does not fire on fetches) and cpu.debug is
-- unavailable, so source (code,bank) is captured at the producer's PATTERN-DMA boundary instead:
--   * install_write_tap on pc090oj_tile_dma_worklist (0xFFB884, 12 x {word slot, word code}) records the
--     SOURCE artwork CODE for every pattern the native producer uploads (production-time, not SAT-only),
--     and maintains a persistent slot->code map.
--   * each frame reads staged_sprite_sat (0xFFB26C, 80 x 8B) for active sprite pieces: palette line, tile
--     slot, X, Y -> join slot->code -> per-piece (code, line, X). Duplication = same code at >=2 X.
--   * reads pc090oj_tile_dma_count (0xFFB8B4) and fg_row_dirty (0xFF404A) per frame for DMA / Plane-A
--     vertical-fill workload proxies.
-- Bank is resolved offline (code -> census family -> effective bank; palette line confirms 0/1). Output
-- dir from GEN_PROV_OUT: provenance_frames.csv (per-frame workload) + provenance_codes.csv (code first/last
-- frame + occurrence) + provenance_sat.log (per-frame active pieces: code,line,x,y throttled).
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local prog = assert(cpu.spaces["program"])
local out = os.getenv("GEN_PROV_OUT") or "."

local WL, WL_END = 0x00FFB884, 0x00FFB8B3   -- worklist 48 bytes
local SAT, NSAT = 0x00FFB26C, 80
local TILE_DMA_COUNT = 0x00FFB8B4
local FG_ROW_DIRTY = 0x00FF404A

local slot2code = {}                 -- persistent VRAM slot -> source code
local codeinfo = {}                  -- code -> {first, last, hits}
local frame = 0
local pending = {}                   -- worklist (slot,code) writes buffered within a frame

-- write tap: capture (slot,code) as the producer queues pattern uploads
prog:install_write_tap(WL, WL_END, "worklist", function(off, data, mask)
  local idx = (off - WL)
  local entry = idx // 4
  local w = idx % 4
  if w == 0 then pending[entry] = pending[entry] or {}; pending[entry].slot = data & 0xffff
  elseif w == 2 then pending[entry] = pending[entry] or {}; pending[entry].code = data & 0x0fff end
end)

local frames = assert(io.open(out .. "/provenance_frames.csv", "w"))
frames:write("frame,active,distinct_codes,dup_codes,tile_dma,fg_row_dirty,l0,l1,l2,l3\n")
local satlog = assert(io.open(out .. "/provenance_sat.log", "w"))
satlog:write("frame code line x y\n")
local sat_budget = 400000

_G._prov = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  -- fold pending worklist writes into the persistent slot->code map + code registry
  for _, e in pairs(pending) do
    if e.slot and e.code and e.code > 0 then
      slot2code[e.slot] = e.code
      local ci = codeinfo[e.code]
      if not ci then codeinfo[e.code] = {first=frame, last=frame, hits=1}
      else ci.last = frame; ci.hits = ci.hits + 1 end
    end
  end
  pending = {}
  -- read SAT: active pieces, palette-line histogram, per-code X positions (duplication)
  local active, l = 0, {0,0,0,0}
  local codeX = {}
  for i = 0, NSAT-1 do
    local b = SAT + i*8
    local y = prog:read_u16(b) & 0xffff
    if y ~= 0 then
      local attr = prog:read_u16(b+4) & 0xffff
      local line = (attr >> 13) & 3
      local slot = attr & 0x07FF
      local x = prog:read_u16(b+6) & 0xffff
      active = active + 1; l[line+1] = l[line+1] + 1
      local code = slot2code[slot]
      if code then
        codeX[code] = codeX[code] or {}
        codeX[code][x] = true
        if sat_budget > 0 then satlog:write(string.format("%d %d %d %d %d\n", frame, code, line, x, y)); sat_budget = sat_budget - 1 end
      end
    end
  end
  local distinct, dup = 0, 0
  for _, xs in pairs(codeX) do
    distinct = distinct + 1
    local nx = 0; for _ in pairs(xs) do nx = nx + 1 end
    if nx > 1 then dup = dup + 1 end
  end
  local tdma = prog:read_u16(TILE_DMA_COUNT) & 0xffff
  local frd = prog:read_u32(FG_ROW_DIRTY) & 0xffffffff
  local bits = 0; local v = frd; while v ~= 0 do bits = bits + (v & 1); v = v >> 1 end
  frames:write(string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
    frame, active, distinct, dup, tdma, bits, l[1], l[2], l[3], l[4]))
  frames:flush()
  if frame % 300 == 0 then
    satlog:flush()
    local cf = assert(io.open(out .. "/provenance_codes.csv", "w"))
    cf:write("code,first_frame,last_frame,hits\n")
    local ks = {}; for k in pairs(codeinfo) do ks[#ks+1] = k end; table.sort(ks)
    for _, k in ipairs(ks) do local c = codeinfo[k]; cf:write(string.format("%d,%d,%d,%d\n", k, c.first, c.last, c.hits)) end
    cf:close()
  end
end)
emu.print_info("SPRITE PROVENANCE TRACE ARMED (write-tap worklist + SAT read) -> " .. out)
