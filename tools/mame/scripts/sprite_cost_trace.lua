-- sprite_cost_trace.lua  (READ-ONLY; no ROM/WRAM modification)
-- Build 0400 sprite-count vs per-frame CPU-cost measurement.
--
-- Why: Tighe reports the game crawls as on-screen sprite count rises. The port runs the whole
-- per-frame chain (sprite producer + arcade gameplay tick + publication) inside the VBlank
-- interrupt (_vblank_service -> arcade VBlank body); when that chain overruns a frame the next
-- VINT is missed and a logic frame is dropped = the crawl. This trace samples, once per external
-- 60 Hz frame, the live sprite load and WHERE the 68000 is, and buckets both by sprite count. As
-- load rises, the CPU's idle/wait share should collapse and the producer/service share rise; the
-- 80-entry SAT cap (dropped>0) shows when the scene exceeds the hardware sprite limit.
--
-- Signals (no game frame-counter needed; external MAME frame clock per project guidance):
--   emitted = pc090oj_emitted_count (0xFFBED4, word)  -- SAT entries built THIS frame (move.w, per-frame)
--   dropped = pc090oj_dropped_count (0xFFBED6, word)  -- CUMULATIVE-SINCE-BOOT count of producer
--             overflow drops (addq only; cleared at boot). Two causes in pc090oj_hooks.s:
--             residency-cache-full (NATIVE_CELLS exhausted) and tile-DMA-worklist-full (>=12/frame).
--             We take the PER-FRAME DELTA here; the raw word is not a per-frame value.
--   PC      = 68000 program counter at frame end, classified by the Build-0400 helper map.

local mac  = manager.machine
local cpu  = mac.devices[":maincpu"]
local prog = cpu.spaces["program"]
local function r16(a) return prog:read_u16(a) & 0xFFFF end

local A_EMIT = 0x00FFBED4
local A_DROP = 0x00FFBED6
local A_SX   = 0x00FF409A
local A_SY   = 0x00FF409E

-- Build-0400 PC landmarks (from apps/rastan-direct/out/symbol.txt).
local function classify(pc)
  if pc >= 0x73382 and pc < 0x74800 then return "sprite-producer" end   -- native_sprite_emit / emit_pass / prepare
  if pc >= 0x70250 and pc < 0x72B9A then return "publication" end        -- dma_publish_frame
  if pc >= 0x72B9A and pc < 0x73382 then return "pkg-install" end        -- fg_boundary_install
  if pc >= 0x700C2 and pc < 0x70250 then return "vblank-service" end     -- _vblank_service head
  if pc >= 0x74800 and pc < 0x76000 then return "native-other" end
  if pc >= 0x3A200 and pc < 0x3A300 then return "arcade-vblank" end
  return "arcade/idle"                                                   -- arcade tick + the between-VINT wait
end

local NB = 9                              -- buckets 0..8 : 0-9,10-19,...,70-79, 80+
local function bucket(n) local b=math.floor(n/10); if b>=NB then b=NB-1 end; return b end
local B = {}
for i=0,NB-1 do B[i]={frames=0, dropsum=0, dropnz=0, pc={}, maxemit=0} end
local total_frames = 0
local overall_pc = {}
local prev_drop = nil                     -- for the per-frame drop delta (cumulative counter)

local outdir = (mac.options.entries.homepath:value():match("([^;]+)") or ".") .. "/sprite_cost"
os.execute('mkdir -p "' .. outdir .. '" 2>/dev/null')

local function add(tbl,label) tbl[label]=(tbl[label] or 0)+1 end

local dump   -- forward declaration (defined below; referenced by sample's periodic flush)
local function sample()
  local emit = r16(A_EMIT)
  local drop = r16(A_DROP)                 -- cumulative-since-boot; convert to a per-frame delta
  local dd = 0
  if prev_drop ~= nil then
    dd = (drop - prev_drop) & 0xFFFF       -- 16-bit wrap-safe
    if dd > 0x8000 then dd = 0 end         -- guard against a counter reset reading as a huge delta
  end
  prev_drop = drop
  local pc=0; pcall(function() pc = cpu.state["PC"].value & 0xFFFFFF end)
  local lab = classify(pc)
  local b = B[bucket(emit)]
  b.frames = b.frames + 1
  b.dropsum = b.dropsum + dd
  if dd > 0 then b.dropnz = b.dropnz + 1 end
  if emit > b.maxemit then b.maxemit = emit end
  add(b.pc, lab)
  add(overall_pc, lab)
  total_frames = total_frames + 1
  -- Rewrite the summary periodically so data survives any MAME exit (Esc, close, crash),
  -- not only a clean machine-stop notifier.
  if total_frames % 300 == 0 then dump() end
end

local function topn(tbl, n)
  local arr={}; for k,v in pairs(tbl) do arr[#arr+1]={k,v} end
  table.sort(arr, function(a,b) return a[2]>b[2] end)
  local out={}; for i=1,math.min(n,#arr) do out[#out+1]=arr[i] end; return out
end

dump = function()
  local path = outdir .. "/sprite_cost_summary.txt"
  local f = io.open(path, "w"); if not f then return end
  f:write("# Build 0400 sprite-cost trace  (external frames sampled: "..total_frames..")\n")
  f:write("# Per 60Hz frame: emitted SAT entries + PER-FRAME producer-overflow drops + PC region.\n")
  f:write("# Buckets = emitted SAT entries built that frame (0-9,10-19,...,70-79).\n")
  f:write("# dropPF = per-frame delta of pc090oj_dropped_count (residency-cache-full + tile-DMA-queue-full).\n")
  f:write("# A rising 'sprite-producer' share and rising dropPF as emitted climbs = the producer is the\n")
  f:write("#  crawl: it expands more candidate pieces than can fit, overrunning the VBlank frame.\n\n")
  f:write(string.format("%-10s %8s %7s %6s %9s %9s   %s\n",
    "emitted","frames","%sess","maxE","dropPF","%dropPF>0","top PC regions (share)"))
  for i=0,NB-1 do
    local b=B[i]
    if b.frames>0 then
      local lo=i*10; local rng = (i==NB-1) and (lo.."+") or (lo.."-"..(lo+9))
      local tp=topn(b.pc,3); local ts={}
      for _,e in ipairs(tp) do ts[#ts+1]=string.format("%s %d%%", e[1], math.floor(e[2]/b.frames*100+0.5)) end
      f:write(string.format("%-10s %8d %6.1f%% %6d %9.2f %8.1f%%   %s\n",
        rng, b.frames, b.frames/total_frames*100, b.maxemit, b.dropsum/b.frames, b.dropnz/b.frames*100,
        table.concat(ts, " | ")))
    end
  end
  f:write("\n# overall PC-region distribution:\n")
  for _,e in ipairs(topn(overall_pc, 8)) do
    f:write(string.format("#   %-16s %6.1f%%\n", e[1], e[2]/total_frames*100))
  end
  f:write("\n# Read: a rising 'sprite-producer' PC share AND rising dropPF as emitted climbs pin the cost to\n")
  f:write("# pc090oj_native_emit_pass/native_sprite_emit. dropPF>0 means the frame generated more candidate\n")
  f:write("# pieces than the residency cache / 12-entry tile-DMA queue could take = wasted producer work.\n")
  f:write("# 'arcade/idle' mixes the between-VINT wait with the arcade gameplay tick, so it is not pure slack.\n")
  f:close()
  print("[sprite_cost] wrote "..path.." ("..total_frames.." frames)")
end

if type(emu.register_frame_done)=="function" then emu.register_frame_done(sample)
else emu.add_machine_frame_notifier(sample) end
pcall(function() emu.add_machine_stop_notifier(function() dump() end) end)

print("[sprite_cost] READY (Build 0400). Play normally, then into a SPRITE-HEAVY room")
print("[sprite_cost]   (many lizard men / projectiles / effects). Quit MAME (Esc) when done;")
print("[sprite_cost]   summary -> "..outdir.."/sprite_cost_summary.txt")
