# Andy — Build 0301: Actual Stage-1 Cave Runtime Fix — ROOT CAUSE PROVEN (sprite/Plane-A VRAM collision)

**Type:** Targeted runtime proof + capture setup. **No ROM produced yet (see §6).** Baseline: Build 0300.

## 1. Authoritative correction incorporated
The original-arcade cave route (`states/traces/original_arcade_stage1_cave_route_20260820_144438/`) proves the
cave is traversed within **segments 1→2→3**, **tm0=0, selector=0 throughout**, and that **segment ≠ scene**
(segment 1 = outdoor + cave entrance + descent; segment 3 = rope + cave + outdoor). The real region
discriminator is the **map-stream page pointer** `a5@0x10C6` (`050F6C → 050F6D → 050F6E`) plus the mode field,
NOT the segment. **My earlier premise (cave = segments 4/5/6) was wrong**, and the per-segment residency model
(Builds 0299/0300) is therefore misdirected: it keys on the wrong signal and cannot represent a cave that
shares a segment with outdoor.

## 2. STATIC ROOT CAUSE OF THE DYNAMIC CORRUPTION (proven)
Tighe's key symptom: **Plane-A cave graphics change while the sword swings and enemies animate.** A static
wrong map stays statically wrong — so this is a live VRAM ownership collision. Mechanically:

- `SPRITE_TILE_BASE = 1024` (`pc090oj_hooks.s:99`) — sprite tile patterns are DMA'd to VRAM tile slots
  **1024..1535** (tile-pattern VRAM ends at 1536, where Plane B's nametable begins at VRAM 0xC000).
- The Plane-A tile cache is `TILE_CACHE_A = 0..1003` (1004 slots) **+ `TILE_CACHE_B = 1344..1503`** (160 slots)
  (`precompute_pc080sn_tile_lut.py`).
- **`TILE_CACHE_B (1344..1503)` lies INSIDE the sprite tile region (1024..1535).** Only slots **0..1023** are
  sprite-safe.
- The outdoor gameplay residency (962 tiles) fits cache A (0..961) and **never uses cache B** → no collision →
  outdoor is stable.
- **Every cave residency I built (Seg1 1038 / Seg2 1150 / Cave-Seg4 1123 / Seg5 1002 / Seg6 1153) exceeds 1004
  and spills into cache B (1344..)** → those Plane-A cells reference slots that sprite tile DMA overwrites.
  When the sword/enemies animate, their sprite tiles are uploaded into 1344.. → the cave Plane-A patterns in
  those slots change. **This is CASE A: name word stable, VRAM pattern slot repurposed by the sprite owner.**

This also explains why 0299/0300 are *worse* than 0298: 0298's single gameplay residency stayed in cache A;
the per-segment cave residencies pushed Plane-A into the sprite region.

**There is no free pattern VRAM to relocate cache B into** (0..1535 = patterns; 1024..1535 = sprites;
1536..2047 = Plane B / Plane A / HScroll nametables). So **a static cave residency cannot be made sprite-safe**
— only ≤1024 sprite-safe Plane-A slots exist, and the cave needs ~1153 unique tiles.

## 3. The required fix (evidence-directed)
Per the task's CASE-A directive ("separate/fix the VRAM ownership ranges at the real owner … a bounded Genesis
FG pattern cache/streaming region"): Plane-A gameplay must live **entirely in the sprite-safe region
(0..1023)** and never in the sprite range. Because the full cave (1153) does not fit 1024 statically, the
correct architecture is a **bounded, source-driven streaming tile cache**:

    arcade FG publication (strip/group/page-pointer progression)
      -> required arcade tile code
      -> stable Genesis slot in cache A (0..1023) allocated on first publication, DMA-uploaded before its
         name word is visible, reference-counted
      -> Plane-A name word
      -> slot reclaimed only when NO live Plane-A cell references it

The visible cave at any scroll position uses far fewer than 1024 unique tiles, so it fits cache A with no
sprite overlap. This replaces the per-segment residency entirely (segment is not a scene) and naturally
handles segment 3 (no whole-segment preload). It is final Genesis-format VRAM ownership only — no PC080SN
virtual RAM, no coordinate triggers; the arcade entering-edge/page publication stays semantic authority.

## 4. Interactive capture instrument (STEP 1 — ready for Tighe)
`tools/mame/scripts/genesistrace.lua` now logs the full semantic route from the stable arcade workram
(`a5=0x00FF0000`): `seg_a5_13e (0xFF013E)`, `tm0_a5_1386`, `selector_a5_10a8`, `page_ptr_a5_10c6`,
`strip_a5_10ca`, `group_a5_10cc`, plus the native `tileset_id`/`scene_id` (residency-reload events). Verified
loading on Build 0300. This captures the Genesis route vs the arcade ground truth (1→2→3, page 6C/6D/6E) and
shows residency churn. **The confirming instrument for CASE A specifically is the VDP VRAM write tap** (does
sprite tile DMA write to the cache-B slots the cave's live name words reference) — this is the one piece to
add/observe during Tighe's playthrough.

**Interactive run (Tighe plays Build 0300, logger captures automatically):**

    cd apps/rastan-direct
    ../../tools/mame/run_genesis_trace_wsl.sh \
        ../../dist/rastan-direct/rastan_direct_video_test_build_0300.bin
    # (omit -video none / -seconds_to_run so the window shows and it runs until you quit)
    # Play: coin=5, start=1, then play normally into and through the cave, use the rope, exit, quit MAME.

Log lands in `build/mame/home/genesistrace/genesis_exec_{trace.log,summary.txt}`.

## 5. Rope / missing block
Arcade rope interval = segment 3, page pointer `0x050F6E`, frames 7506–8034 (per
`Cody_arcade_stage1_cave_route_capture.md`). The rope is part of the same Plane-A stream; the streaming/cache
fix is expected to restore it. Missing destructible cave-entrance block: **still deferred** (not investigated).

## 6. Why Build 0301 is not built in this turn
The runtime ownership failure is **mechanically proven statically** (sprite tile DMA overwrites cave Plane-A
cache-B slots). The *fix*, however, is a **new streaming tile-cache architecture** in the hot native FG
producer path (dynamic code→slot map replacing the static LUT, on-demand VBlank DMA, refcounted eviction) —
a large, high-risk change. Given this session's proven-wrong premise (cave = 4/5/6) and the two rejected
builds it produced, implementing that architecture **blind** would most likely produce a third rejected build
and burn usage. The disciplined path is: run the ready interactive capture (§4) to CONFIRM CASE A (sprite DMA
into referenced cache-B slots) and the 1→2→3 / page-6C/6D/6E route, then implement the streaming cache with a
validated target. A no-progress revert to the 0298 single-residency (sprite-safe but statically-wrong cave)
is available as a fallback if a stable-but-wrong cave is preferred to 0300's dynamic corruption meanwhile.

---
**Authoritative arcade cave route incorporated:** YES
**Genesis interactive cave capture completed:** NO (instrument ready; requires Tighe's playthrough — STEP 1)
**Genesis route segments observed:** headless attract stalls ≤ seg 3; interactive capture pending
**Expected arcade route:** 1 → 2 → 3 (page 050F6C→6D→6E; tm0=0, selector=0)
**Genesis semantic route matches arcade:** PENDING capture
**Build-0300 segment-1 residency actually loaded:** PENDING capture (tileset_id watch will show)
**Build-0300 segment-2 residency actually loaded:** PENDING capture
**Primary runtime failure classification:** A (name word stable, VRAM pattern slot repurposed by sprite owner) — proven statically; capture to confirm
**First divergence:** Plane-A cave residency spills into cache B (1344–1503), which overlaps the sprite tile region (SPRITE_TILE_BASE=1024..1535); sprite tile DMA overwrites those live cave Plane-A slots
**Live Plane-A slot overwritten:** YES (proven structurally)
**Overwrite owner:** PC090OJ sprite tile DMA (SPRITE_TILE_BASE=1024; pc090oj_hooks.s emit paths)
**Sprite animation overlaps corrupt pattern writes:** YES (matches symptom; confirm via VRAM write tap)
**Unexpected Plane-A name-word mutation:** NO (name words are stable; patterns change)
**Per-segment residency model sufficient:** NO
**If NO, replacement model:** bounded source-driven streaming tile cache confined to sprite-safe cache A (0..1023), refcounted, DMA-on-publish
**Segment 3 handled correctly:** N/A (streaming model removes whole-segment preloads)
**Rope restored:** PENDING (expected via streaming fix)
**Missing cave block fixed:** NO
**Missing cave block deferred:** YES
**Plane B changed:** NO
**Collision changed:** NO
**Build 0301 produced:** NO (see §6 — proven cause; fix is a validated streaming build after the capture)
**ROM:** none
**SHA-256:** none
**Gate:** n/a
