# Andy — Build 0298: Plane-A Cave Fix (Stage-1 FG level-segment dimension)

**Type:** Hybrid analysis / implementation. Baseline: accepted Build 0297. **ROM produced: Build 0298.**

> **Scope honesty up front:** this build is a **partial** cave fix. It restores the Stage-1 **segment-5**
> cave FG tiles — including the three acceptance targets 0x07FC/0x0800/0x0806 (the cave floor, metatile
> 0x243C) — within the existing residency budget with **no runtime/selection change**. The **full** cave
> descent (segments 4 and 6) does **not** fit a single residency and is deferred to a segment-driven
> residency-partition task (§6). Calibrate visual testing accordingly.

## 1. Phase-0 baseline
- **Priors:** KF-010 (FG→Plane A base 0xE000), KF-014 (tile LUT, code 0x0000..0x3FFF), KF-015 (full-plane
  scroll +8), KF-011 (arcade VBlank owns progression) — all STRONG, all respected.
- **Task classification:** EXTENDING (fixes the existing native FG residency pipeline; no producer redesign).
- **Issues touched:** OPEN-001/018 (native FG/map completeness), OPEN-017 (FG source/residency).
- **Contradiction of a CONFIRMED/STRONG finding:** NONE.
- **Priors read:** the Part-2A checkpoint, cave Part 1/1B, PC080SN/PC090OJ native-replacement policy.

## 2. STEP 1 — Root cause (confirmed)

**Q1 — Does any OTHER current generator path supply the missing later-segment Plane-A tiles? — NO.**
`build/pc080sn_tile_vram_lut.bin` is the single global code→slot map, assembled (in
`precompute_pc080sn_tile_lut.py:main`) from the union of ALL scene tile sets (title, gameplay, end-round,
gameplay-cave), each of which is `block_scene_tiles ∪ fg_tiles ∪ text/strip`. A code with `LUT==0` is in
**none** of them. The three targets (and the 182-tile cave-4-6 set) read `LUT==0`, so no path supplied them.

**Q2 — What does the native Plane-A path do when LUT lookup returns 0?**
At [tilemap_hooks.s:307-311](apps/rastan-direct/src/tilemap_hooks.s#L307-L311) the selector-0 native producer
does: `d3 = arcade tile code (&0x3FFF); d3 = LUT[d3]; d3 |= attribute bits; staged_fg_buffer[cell] = d3`.
When `LUT[code] == 0`, the emitted Genesis name word = **VRAM tile slot 0 (the blank/reserved tile)** OR-ed
with the cell's palette/flip bits. **Exact behavior: the cave cell renders as blank VRAM tile 0** (a flat/empty
tile in the cell's palette), not the intended cave graphic. (Same lookup pattern in the selector-1/2 producer.)

**Q3 — Is the missing level-segment dimension the proven first cause of the Stage-1 cave visual corruption? —
YES.** The arcade Plane-A FG source address is
`0x1691C + strip*0x22C0 + level_segment*0x40 + group*4` (cave Part 1/1B). The Build-0155 collector
`collect_runtime_gameplay_fg_tiles()` used `0x1691C + strip*0x22C0 + group*4` — the `level_segment*0x40`
dimension was **absent** (pinned at segment 0). So Stage-1 later-segment FG tiles were absent from the LUT
except where shared with segment 0; the segment-5 cave floor family (metatile 0x243C → 0x07FC..0x0806) was
`LUT==0` → rendered as blank tile 0 per Q2.

## 3. STEP 2 — The fix (generator)

**File:** `tools/translation/precompute_pc080sn_tile_lut.py`.
Added the missing dimension: constants `FG_LEVEL_SEGMENT_STRIDE = 0x40` and `FG_LEVEL_SEGMENTS`, and made
`collect_runtime_gameplay_fg_tiles()` iterate `level_segment` with
`src = 0x1691C + strip*0x22C0 + level_segment*0x40 + group*4`. **No hardcoded tile IDs; no player
coordinates; no native renderer change; collision and Plane B untouched.**

**Residency budget (proven, gate = `assign_scene_aware_slots`, budget = 1004+160 = 1164 slots):**

| FG_LEVEL_SEGMENTS | SCENE_GAMEPLAY | largest scene | verdict |
|---|---|---|---|
| (0,) [old] | 962 | 1068 (end-round) | baseline |
| **(0, 5) [shipped]** | **1002** | **1067 (end-round)** | **FITS** |
| (0, 4, 5) | 1167 | 1167 | OVER by 3 |
| (0, 5, 6) | 1181 | 1181 | OVER by 17 |
| (0, 4, 5, 6) [full cave] | 1209 | 1209 | OVER by 45 |

The **full** cave descent (segments 4,5,6) does not fit the single gameplay residency (1209 > 1164). Since the
Stage-1 cave stays on the **gameplay** residency throughout (tm0/attr outdoor; cave Part 1 — the attr=0x0003
SCENE_GAMEPLAY_CAVE is never selected during the segment-driven descent), the cave tiles must live in
SCENE_GAMEPLAY, and only **segment 5** (which contains the acceptance floor targets) fits with headroom. That
is what Build 0298 ships. **No residency partition and no runtime selection change were required for this
increment.**

**Verification (regenerated production data):**
- `LUT[0x07FC] = 0x0080`, `LUT[0x0800] = 0x0084`, `LUT[0x0806] = 0x0089` — all nonzero.
- All three present in `build/pc080sn_scene_preload_gameplay.bin` manifest → their patterns are loaded into
  VRAM with the gameplay residency active during the Stage-1 cave.
- Generator reported: Gameplay 1002 / End-Round 1067 / VRAM max 1067/1164 / range overlap PASS.

## 4. STEP 3 — Build 0298

- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0298.bin`
- **SHA-256:** `ecb2b157328a891d0c072a8773d01dc8cf28b0fa6cff72ac7799b4bdccc4316d`
- **Size:** 1,597,112 bytes
- **Counter:** 297 → 298
- **Gate:** GATE_PASS (canonical); boot guard PASS pre+post; shift patcher 67 replacements / 7213 branch /
  630 abs-long fixes; genesis-only→maincpu relocations = 7.
- **opcode_replace count:** 227 (unchanged — this is a **generated-data-only** change; no opcode/spec edits).
- **Corrected Stage-1 FG residency:** SCENE_GAMEPLAY 962 → **1002** tiles (segment-5 FG added).
- **Residency solution:** FITS the existing gameplay residency (1067/1164); no new partition.

**GENESIS NTSC MAME (`genesis`) regression trace (release-run, 30 s):** ran to completion (1797 frames,
`genesistrace stop`), avg 979% speed, **no crash / no unmapped memory**; `fg_cwindow_live count=0` confirms
the native FG path is active (no legacy C-window regression). The 30 s attract window does not reach the cave
(the demo's cave descent is later — cave Part 1), so cave visual confirmation is Tighe's BlastEm/Exodus test.

## 5. Preserved boundaries
- **Plane B:** untouched. **Collision:** untouched (produced natively from metatile +0x22; independent of the
  tile LUT). **Native Plane-A renderer:** unchanged. **No NOP/RTS. No opcode/spec change.**

## 6. Deferred / follow-up (the complete cave fix)
The **full** Stage-1 cave (segments 4 and 6, ~207 additional tiles) exceeds the single gameplay residency. The
complete fix is a **segment-driven residency partition**: route cave segments 4–6 FG tiles to a dedicated
cave scene set (which fits, ~815/1164) and add a **runtime scene-selection driven by the level segment**
(a5@0x13E / strip base), because the existing cave selection keys on attr=0x0003 which provably never fires
during the segment-driven Stage-1 cave. That runtime selection change needs its own design + proof and is not
in this build. Also still deferred: **missing destructible cave-entrance block**; **rope single-cell
ownership** (candidate metatiles 0x2B08/0x2B48/0x2B88 are blank-filled).

## 7. Open/Closed issues + KNOWN_FINDINGS
- OPEN-001/018: partial progress (Stage-1 segment-5 cave FG now resident). OPEN-017: the LUT `level_segment`
  omission is identified and partially corrected. No issue closed; no new issue opened.
- **KNOWN_FINDINGS:** candidate finding for Tighe — "the Genesis PC080SN tile-LUT generator's Stage-1 FG
  collector must include the arcade `level_segment*0x40` dimension; a single residency cannot hold the full
  Stage-1 outdoor+cave FG set (1209 > 1164), so a segment-driven residency partition is required for the
  complete cave." Not written unilaterally.

---

**Root cause confirmed:** YES
**Another generator path supplied missing tiles:** NO
**LUT=0 consequence:** native producer emits Genesis name word = VRAM slot 0 (blank tile) OR cell palette/flip
bits → cave cell renders as blank tile 0 (tilemap_hooks.s:307-311)
**Missing level-segment dimension confirmed:** YES
**Generator fixed:** YES (added `level_segment*0x40`; FG_LEVEL_SEGMENTS = (0,5))
**Corrected Stage-1 FG tile count:** SCENE_GAMEPLAY 962 → 1002 (segment-5 FG added; full cave 4–6 = 1209, does
not fit — deferred to partition task)
**VRAM/residency:** FITS existing gameplay residency (max scene 1067/1164)
**0x07FC valid:** YES (→0x0080)
**0x0800 valid:** YES (→0x0084)
**0x0806 valid:** YES (→0x0089)
**Build 0298 produced:** YES
**ROM path:** dist/rastan-direct/rastan_direct_video_test_build_0298.bin
**SHA-256:** ecb2b157328a891d0c072a8773d01dc8cf28b0fa6cff72ac7799b4bdccc4316d
**Plane B preserved:** YES
**Collision preserved:** YES
**Missing cave block fixed:** NO
**Missing cave block deferred:** YES
**USER MUST VERIFY:** cave entrance, cave descent, cave interior, first rope area when reachable — and note
segments 4 & 6 cave tiles are NOT in this build (only segment 5 + the floor targets); expect the descent/floor
to improve, interior may still show gaps until the partition task.
