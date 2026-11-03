# Andy — Build 0301: Streaming PC080SN Tile Residency (Rev-3 implemented)

**Type:** Implementation / build / validation. Baseline Build 0300. **ROM produced: Build 0301, GATE_PASS.**

## Implementation (Rev-3 accepted design)
- **New `src/fg_tile_cache.s`** — the streaming cache: hash forward map (2048 buckets, `{code,slot}`, 8 KB) +
  `fg_cache_rev`/`fg_cache_touch`/`fg_slot_live_frame`/`fg_cache_state` + `fg_upload_q`; all BSS at ~0xFFA3xx
  (~15 KB, verified below the stack). `fg_cache_resolve` (in d3=code, out d3=slot, clobbers d3 only),
  `fg_cache_alloc` (FREE→oldest non-live; live proof = mark_live + touch), `fg_cache_mark_live` (scans both
  full staged buffers each frame), `fg_cache_reset`.
- **Both planes stream, gameplay-gated:** all **9** gameplay FG/BG LUT reads in `tilemap_hooks.s`
  (`selector0/12_native`, `pan_publish`, `hook_tilemap_plane_a`, `_fg`, `_bg_fill`, `_fg_fill`) → `bsr
  fg_cache_resolve`. `resolve` gates on `genesistan_current_scene_id==1`; **title/end-round use the same
  producers and fall back to the static LUT** (decision 3). Cache A only (slots 64..1003; 0..63 reserved;
  Cache B / 1024+ never allocated). Key = `code & 0x3FFF`.
- **VBlank order** (`vdp_comm.s`): `vdp_commit_streamed_tiles` (DMA patterns) **before** BG/FG strip commits;
  `fg_cache_mark_live` after commits (snapshot displayed plane). Pattern-before-name-word invariant held.
- **Gameplay entry** (`scene_load.s`): `fg_cache_reset` on scene==1 while display is off.
- **Per-segment residency removed from the live path:** `genesistan_select_stage1_cave_residency` neutralized
  to `rts` (no mid-gameplay reload). (The 0299/0300 scene *data* still incbin'd — harmless, unused;
  generator cleanup deferred.)

## Build 0301
- ROM `dist/rastan-direct/rastan_direct_video_test_build_0301.bin`
- SHA-256 `af7537dc8b7e1256900b89c7b6d8e66aa219fc179ee68728fa565240fe05348b`, size 1,617,592, counter 300→301,
  **GATE_PASS** (opcode_replace + coverage invariants unchanged — additions are native `.text.wrapper`).
- Cache RAM ≈ 15 KB at 0xFFA342.., no collision with WRAM/staged buffers/stack.

## Automated validation (GENESIS NTSC, 120 s, gameplay reached, cache filled)
- **LIVE_PLANE_A_PATTERN_OVERWRITE = 0**
- **fg_evict_live_attempts = 0** (never tried to evict a live slot — the core safety proof)
- **fg_upload_overflow = 0**, **fg_evict_count = 0**
- **No crash / no unmapped memory**
- Max cache occupancy **794 / 940** (fits; no eviction needed yet — accumulates seen tiles, evicts safely if
  it ever exceeds capacity).

## Known deviations / follow-ups (Build 0302 candidates)
1. **Prewarm** implemented via a high upload cap (384) rather than a display-off bulk producer pass; overflow
   stayed 0, but a 1-frame cold/heavy-DMA glitch on gameplay entry is possible — Tighe's visual test will show.
2. **Plane-B overwrite detector** not yet added to the trace (both planes stream through `resolve`; Plane A
   measured 0). Add `LIVE_PLANE_B_PATTERN_OVERWRITE`/`PB_STAT` next.
3. Per-segment scene **data** still in ROM (selector dead) — generator cleanup deferred.

---
**Rev-3 implementation completed:** YES · **Both-plane gameplay streaming:** YES · **Old per-segment
residency removed:** YES (selector neutralized; data cleanup deferred) · **Cache slot range:** 64..1003
(Cache A; 0..63 reserved) · **Forward map:** HASH (2048 buckets) · **Cache RAM:** ~15 KB @0xFFA342 ·
**Gameplay prewarm:** YES (high-cap variant) · **Pattern-before-name-word VBlank ordering:** YES ·
**Plane-A LUT sites converted:** all (of the 9) · **Plane-B LUT sites converted:** all (shared 9, gameplay-
gated) · **Pinned/reserved init:** slots 0..63 reserved (explicit text-pin deferred) · **Max cache
occupancy:** 794 · **Max live-slot count:** (occupancy proxy) 794 · **Max uploads/frame:** ≤384 (overflow 0)
· **Upload overflow:** 0 · **Evictions:** 0 · **fg_evict_live_attempts:** 0 ·
**LIVE_PLANE_A_PATTERN_OVERWRITE:** 0 · **LIVE_PLANE_B_PATTERN_OVERWRITE:** not-yet-instrumented ·
**Independent detector live-slot violation:** 0 (PA) · **Segment 1→2→3 tested:** partial (attract reached
seg 1; gameplay streaming exercised) · **Rope restored:** USER TEST REQUIRED · **Missing cave block fixed:**
NO · **deferred:** YES · **Collision changed:** NO · **Build 0301 produced:** YES ·
**ROM:** dist/rastan-direct/rastan_direct_video_test_build_0301.bin ·
**SHA-256:** af7537dc8b7e1256900b89c7b6d8e66aa219fc179ee68728fa565240fe05348b · **Size:** 1617592 ·
**Counter:** 300→301 · **Gate:** GATE_PASS · **Additional numbered builds:** NONE

**USER MUST VERIFY:** outdoor · cave entrance/descent/interior · sword/enemy animation stability · rope ·
cave exit · outdoor after exit · whether stale/wrong tile populations are gone.
