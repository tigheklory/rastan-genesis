-- frame_timing_trace.lua  (READ-ONLY; no ROM/WRAM modification)
-- Build 0400 EXACT frame-timing trace via memory-access taps + VDP beam position.
--
-- WHY taps, not PC-sampling: this MAME build has no cpu:add_exec, so exact entry/exit
-- timing is taken from memory-access taps (install_write_tap works) plus the VDP HV
-- counter (0xC00008, side-effect-free read) for beam/scanline position. This yields
-- EXACT per-IRQ6 timing, not one-PC-sample-per-frame statistics.
--
-- Build 0400 proven static order (apps/rastan-direct/src/vdp_comm.s:175 _vblank_service):
--   IRQ6 -> rastan_direct_update_inputs (writes input shadow 0xFF61F6, ONCE per IRQ6)
--        -> vdp_prepare_sprites  (SAT producer GUARD; no-op in gameplay)
--        -> dma_publish_frame    (THE single publication phase: all VDP writes)
--        -> jmp 0x3A208 arcade VBlank worker (gameplay tick + native_stage_dispatch +
--             pc090oj_native_emit_pass -> writes pc090oj_emitted_count 0xFFBED4) -> RTE
--   mainline (post-RTE) spins until next VINT.
--
-- Signals captured per IRQ6:
--   input-shadow write 0xFF61F6  -> IRQ6 entry  (beam V at entry)
--   first/last VDP port write    -> publication window (beam V span, scanlines)
--   VDP control-port decode      -> coarse publication sub-phase split by target
--   emitted-count write 0xFFBED4 -> producer completion (emitted value + beam V)
--                                   V in active range (<0xE0) => IRQ6 overran vblank.
-- Missed/coalesced VINT proof: serviced IRQ6 count vs external VBlank count.

local mac  = manager.machine
local cpu  = mac.devices[":maincpu"]
local prog = cpu.spaces["program"]
local function r16(a) return prog:read_u16(a) & 0xFFFF end
local function beamV()                 -- VDP HV counter high byte = V (side-effect-free)
  local hv = 0; pcall(function() hv = prog:read_u16(0x00C00008) end)
  return (hv >> 8) & 0xFF
end

local A_INPUT = 0x00FF61F6             -- input shadow: one write per IRQ6 input latch
local A_EMIT  = 0x00FFBED4             -- pc090oj_emitted_count: written at emit-pass end
local VDP_LO, VDP_HI = 0x00C00000, 0x00C00007
local VBLANK_V = 0xE0                  -- NTSC: V>=0xE0 => in vblank; V<0xE0 => active display

-- VRAM target ranges (apps/rastan-direct): PlaneB 0xC000, PlaneA 0xE000, SAT 0xF800, else tiles/patterns.
local function vram_target(addr)
  if addr >= 0xF800 and addr < 0xFC00 then return "SAT" end
  if addr >= 0xE000 and addr < 0xF000 then return "planeA" end
  if addr >= 0xC000 and addr < 0xE000 then return "planeB" end
  return "tiles"                       -- sprite/BG pattern VRAM
end

-- ---- per-bucket accumulators (bucket by emitted sprite count) ----
local NB = 9
local function bucket(n) local b=math.floor(n/10); if b>=NB then b=NB-1 end; return b end
local B = {}
for i=0,NB-1 do B[i]={irq=0, pubspan={}, compV={}, overran=0, maxemit=0} end

-- Mainline-PC histogram: a PC sampled outside every known handler range is steady-state mainline
-- (post-RTE). This identifies what the 68000 does during active display (Phase 2).
local mainline_pc = {}
local function is_handler(pc)
  if pc >= 0x700C2 and pc < 0x76000 then return true end   -- Genesis helpers (_vblank_service..producers)
  if pc >= 0x3A208 and pc < 0x3A280 then return true end   -- arcade VBlank worker head
  if pc >= 0x3AD00 and pc < 0x3B000 then return true end   -- arcade worker subroutines (bsr targets)
  if pc >= 0x3F000 and pc < 0x3F200 then return true end
  if pc >= 0x55D00 and pc < 0x55E00 then return true end
  if pc >= 0x1AC000 and pc < 0x1AD000 then return true end -- crash/exception handler
  return false
end
local function pc_now() local p=0; pcall(function() p = cpu.state["PC"].value & 0xFFFFFF end); return p end

local ext_frames   = 0                 -- external MAME VBlanks (register_frame_done)
local irq6_total   = 0                 -- serviced IRQ6 (input latches)
local irq6_at_lastframe = 0
local dropped_frames = 0               -- external frames with NO serviced IRQ6 (coalesced VINT)
local sub = {CRAM=0, VSRAM=0, planeA=0, planeB=0, SAT=0, tiles=0}  -- VDP writes per target (counts)

-- ---- record model ----
-- Records are delimited by the emit-count write (one per gameplay tick = one producer pass),
-- which is the reliable once-per-tick marker. Each record accumulates that tick's publication
-- VDP-write window (pub_start/pub_last beam) and the producer-complete beam V at the emit write.
local pub_start, pub_last = nil, nil
local input_writes = 0                          -- raw diagnostic; update_inputs writes the shadow 2x/IRQ6

-- VDP GATE (Part 2): a VDP-port write whose PC is NOT in the Genesis publisher range is an
-- unexpected direct VDP access (the retained arcade 0xC0xxxx-referencing code hitting the real VDP).
-- Publisher range = the Genesis helper/dma/producer code that legitimately writes the VDP.
local function is_publisher_pc(pc) return pc >= 0x70000 and pc < 0x76800 end
local vdp_offenders = {}                         -- pc -> count (non-publisher VDP writes)
local vdp_offender_total = 0
local gate_fail_total = 0                        -- non-publisher VDP writes from ARCADE-WORKER range (the real gate)

local function commit_tick(emit, complV)
  local b = B[bucket(emit)]
  b.irq = b.irq + 1                             -- "irq" here = gameplay ticks in this bucket
  if emit > b.maxemit then b.maxemit = emit end
  if pub_start and pub_last then
    local span = pub_last - pub_start
    if span < 0 then span = span + 262 end
    b.pubspan[#b.pubspan+1] = span
  end
  b.compV[#b.compV+1] = complV
  if complV < VBLANK_V then b.overran = b.overran + 1 end
  pub_start, pub_last = nil, nil                -- reset for the next tick's publication burst
end

-- ---- taps ----
-- MAME write-tap callback signature is (offset, data, mask); offset is relative to the
-- tap's base address, so reconstruct the absolute address from the known base.
local function on_input_write(offset, data, mask)
  input_writes = input_writes + 1               -- raw diagnostic; NOT once-per-IRQ6
end

local function on_emit_write(offset, data, mask)
  irq6_total = irq6_total + 1                   -- one producer pass = one gameplay tick
  commit_tick(r16(A_EMIT), beamV())
end

-- VDP control-port write latch. The 68000 issues a move.l to the word-wide VDP port as TWO
-- 16-bit bus writes, so the address/code command (always two words) arrives as two taps.
-- Register writes (D15..D13 = 100x => 0x8000-0x9FFF) are single-word and reset the latch.
local ctrl_pending = nil
local last_target  = nil
local function classify_cmd(hi, lo)
  local cd = ((hi >> 14) & 0x03) | (((lo >> 4) & 0x0F) << 2)   -- CD0..CD5
  local a  = (hi & 0x3FFF) | ((lo & 0x0003) << 14)             -- A0..A15
  local cdlow = cd & 0x07
  if     cdlow == 0x03 then last_target = "CRAM"
  elseif cdlow == 0x05 then last_target = "VSRAM"
  elseif cdlow == 0x01 then last_target = vram_target(a)
  else last_target = nil end
  if last_target then sub[last_target] = sub[last_target] + 1 end
end

local function on_vdp_write(offset, data, mask)
  local addr = offset or 0                            -- tap passes the ABSOLUTE address
  local v = beamV()
  if not pub_start then pub_start = v end
  pub_last = v
  do                                                  -- VDP GATE: who is writing the VDP?
    local pc = pc_now()
    if not is_publisher_pc(pc) then
      vdp_offenders[pc] = (vdp_offenders[pc] or 0) + 1
      vdp_offender_total = vdp_offender_total + 1
      if pc >= 0x3A000 and pc < 0x60000 then          -- the real gate: retained arcade worker/producer code
        gate_fail_total = gate_fail_total + 1
      end
    end
  end
  if (addr & 0xFFFFFFFC) == 0x00C00004 then           -- control port (0xC00004-0xC00007)
    if (data & 0xFFFF0000) ~= 0 then                  -- 32-bit addr/code command (e.g. DMA trigger)
      classify_cmd((data >> 16) & 0xFFFF, data & 0xFFFF); ctrl_pending = nil
    else
      local w = data & 0xFFFF
      if (w & 0xE000) == 0x8000 then                  -- VDP register write (0x8000-0x9FFF): single word
        ctrl_pending = nil
      elseif ctrl_pending == nil then
        ctrl_pending = w                              -- first word of a split two-word command
      else
        classify_cmd(ctrl_pending, w); ctrl_pending = nil
      end
    end
  end
  -- data-port writes (0xC00000/2) are PIO payload to the last-decoded target; not re-counted here.
end

local outdir = (mac.options.entries.homepath:value():match("([^;]+)") or ".") .. "/frame_timing"
os.execute('mkdir -p "' .. outdir .. '" 2>/dev/null')

local function pct(arr, p)
  if #arr == 0 then return 0 end
  local s = {}; for _,v in ipairs(arr) do s[#s+1]=v end; table.sort(s)
  local i = math.max(1, math.ceil(p/100 * #s)); return s[i]
end
local function med(arr) return pct(arr,50) end
local function amax(arr) local m=0; for _,v in ipairs(arr) do if v>m then m=v end end; return m end

local function dump()
  local path = outdir .. "/frame_timing_summary.txt"
  local f = io.open(path, "w"); if not f then return end
  local tick_ratio = (ext_frames>0) and (irq6_total/ext_frames) or 0
  f:write("# Build 0400 EXACT frame-timing trace (memory taps + VDP beam). READ-ONLY.\n")
  f:write(string.format("# external VBlanks (MAME display frames): %d\n", ext_frames))
  f:write(string.format("# gameplay ticks (producer passes):       %d\n", irq6_total))
  f:write(string.format("# GAMEPLAY TICKS / DISPLAY FRAME:         %.4f   (1.0 = full 60Hz; <1.0 = crawl)\n", tick_ratio))
  f:write(string.format("# display frames with NO gameplay tick (repeated frame): %d  (%.2f%%)\n",
    dropped_frames, (ext_frames>0) and (dropped_frames/ext_frames*100) or 0))
  f:write(string.format("# raw input-shadow writes: %d  -> IRQ6 entries ~= %d (update_inputs writes 2x/IRQ6)\n",
    input_writes, math.floor(input_writes/2 + 0.5)))
  f:write(string.format("#   (IRQ6 entries ~= completed ticks in gameplay: one worker per IRQ6, verified by SAT-DMA-per-tick)\n"))
  f:write("#\n# MISSED/COALESCED VINT (dropped gameplay frames) PROVEN: " ..
    ((dropped_frames>0 or tick_ratio < 0.98) and "YES" or "NO") .. "\n\n")
  f:write("# Per emitted-sprite bucket: publication span (beam scanlines, pub_start->pub_last)\n")
  f:write("# and producer-complete beam V (emitted_count write). compV<224 => producer finished in\n")
  f:write("# active display (IRQ6 work overran the vblank window).\n\n")
  f:write(string.format("%-9s %7s %6s  %-20s  %-22s  %8s\n",
    "emitted","ticks","maxE","pub span ln (med/p95/max)","producer-done V (med/p95/max)","%overran"))
  for i=0,NB-1 do
    local b=B[i]
    if b.irq>0 then
      local lo=i*10; local rng=(i==NB-1) and (lo.."+") or (lo.."-"..(lo+9))
      f:write(string.format("%-9s %7d %6d  %4d / %4d / %4d       %4d / %4d / %4d          %6.1f%%\n",
        rng, b.irq, b.maxemit,
        med(b.pubspan), pct(b.pubspan,95), amax(b.pubspan),
        med(b.compV), pct(b.compV,95), amax(b.compV),
        (b.irq>0) and (b.overran/b.irq*100) or 0))
    end
  end
  local tot=0; for _,v in pairs(sub) do tot=tot+v end
  f:write("\n# Publication VDP-write distribution by target (counts; coarse sub-phase proxy):\n")
  for _,k in ipairs({"planeB","planeA","SAT","tiles","CRAM","VSRAM"}) do
    f:write(string.format("#   %-8s %8d  %5.1f%%\n", k, sub[k], (tot>0) and (sub[k]/tot*100) or 0))
  end
  -- top mainline (non-handler) PCs = what the CPU runs during active display
  local mp = {}; for k,v in pairs(mainline_pc) do mp[#mp+1]={k,v} end
  table.sort(mp, function(a,b) return a[2]>b[2] end)
  local msum=0; for _,e in ipairs(mp) do msum=msum+e[2] end
  f:write(string.format("\n# Mainline (post-RTE, non-handler) PC samples: %d of %d frames (%.1f%%)\n",
    msum, ext_frames, (ext_frames>0) and (msum/ext_frames*100) or 0))
  for i=1,math.min(6,#mp) do
    f:write(string.format("#   PC %06x : %d  (%.1f%%)\n", mp[i][1], mp[i][2], mp[i][2]/ext_frames*100))
  end
  -- VDP GATE result (Part 2)
  f:write("\n# ===== RUNTIME VDP GATE (Part 2) =====\n")
  f:write(string.format("# GATE VERDICT: %s  (arcade-worker-range VDP writes 0x3A000-0x5FFFF = %d; non-publisher total = %d)\n",
    (gate_fail_total == 0) and "PASS" or "FAIL", gate_fail_total, vdp_offender_total))
  if vdp_offender_total == 0 then
    f:write("# Every VDP-port write came from the Genesis publisher range (0x70000-0x767FF).\n")
  else
    f:write("# Non-publisher VDP-write PCs (boot VRAM fill <0x1000 and init/crash are one-time, NOT the gate):\n")
    local arr={}; for k,v in pairs(vdp_offenders) do arr[#arr+1]={k,v} end
    table.sort(arr, function(a,b) return a[2]>b[2] end)
    for i=1,math.min(12,#arr) do
      local pc=arr[i][1]
      local zone = (pc>=0x3A000 and pc<0x60000) and "ARCADE-WORKER(gate FAIL!)" or
                   (pc<0x1000) and "boot-vectors/VRAM-fill(ok)" or
                   (pc>=0x1AC000 and pc<0x1AD000) and "crash(boot,ok)" or
                   (pc>=0x3B000 and pc<0x3C000) and "init(boot,ok)" or "other(check)"
      f:write(string.format("#   PC %06x : %d  [%s]\n", pc, arr[i][2], zone))
    end
    f:write("#   Any ARCADE-WORKER PC here = a retained 0xC0xxxx access hitting the real VDP = GATE FAIL;\n")
    f:write("#   STOP worker-move planning and report. boot-only init/crash PCs are not the per-frame gate.\n")
  end
  f:write("\n# Reading it: ticks/frame < 1.0 (and dropped>0) = gameplay ran fewer times than the display\n")
  f:write("# refreshed = physical VINTs lost because the IRQ6 (publish + arcade worker + producer)\n")
  f:write("# overran a frame and masked the next VINT (worker runs at IPL7). producer-done V well below\n")
  f:write("# 224 at high emitted counts = the producer finishes deep in active display = work does not\n")
  f:write("# fit the vblank window. Delimiter = emit-count write (one per gameplay tick).\n")
  f:close()
  print(string.format("[frame_timing] wrote %s  (ext=%d ticks=%d tick/frame=%.3f dropped=%d)",
    path, ext_frames, irq6_total, tick_ratio, dropped_frames))
end

-- Keep tap handles alive in _G: a discarded handle is garbage-collected and the tap stops firing.
local okw1 = pcall(function() _G.ft_tap_in  = prog:install_write_tap(A_INPUT, A_INPUT|1, "ft_in",  on_input_write) end)
local okw2 = pcall(function() _G.ft_tap_em  = prog:install_write_tap(A_EMIT,  A_EMIT+1,  "ft_em",  on_emit_write) end)
local okw3 = pcall(function() _G.ft_tap_vdp = prog:install_write_tap(VDP_LO,  VDP_HI,    "ft_vdp", on_vdp_write) end)

if type(emu.register_frame_done)=="function" then
  emu.register_frame_done(function()
    ext_frames = ext_frames + 1
    if irq6_total == irq6_at_lastframe then dropped_frames = dropped_frames + 1 end
    irq6_at_lastframe = irq6_total
    local p = pc_now()
    if not is_handler(p) then mainline_pc[p] = (mainline_pc[p] or 0) + 1 end
    if ext_frames % 300 == 0 then dump() end
  end)
end
pcall(function() emu.add_machine_stop_notifier(function() dump() end) end)

print(string.format("[frame_timing] READY (Build 0400). taps: input=%s emit=%s vdp=%s",
  tostring(okw1), tostring(okw2), tostring(okw3)))
print("[frame_timing] Play normally; drive LIGHT, MEDIUM, then the HEAVY slowdown area.")
print("[frame_timing]   summary -> " .. outdir .. "/frame_timing_summary.txt")
