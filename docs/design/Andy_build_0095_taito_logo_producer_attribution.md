# Andy — Build 0095 TAITO Logo Producer Attribution

**Author:** Andy
**Date:** 2026-06-23
**Build:** 0095 (rastan-direct; the 3AD44 FG/BG dispatch-split baseline)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. No implementation. Addresses mapped via `build/rastan-direct/address_map.json` (JSON only). Labels: [STATIC] proven from ROM/source/JSON; [INFERENCE] reasoned, flagged for confirmation.

---

## Phase 0 — Baseline

**Relevant priors:** KF-014 (PC080SN tile-LUT pre-assigns VRAM slots for strip-table-reachable tile codes — STRONG; central to this dropout), KF-028 (title-text producer→staging — STRONG), KF-010 (FG→Plane A, BG→Plane B), KF-024 (Rastan DIP/region defaults), KF-004/006. **Classification:** EXTENDING (OPEN-001). **Issues:** OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch. **Contradiction:** NONE. **Architecture compliance:** CONFIRMED (recommended fix is a build-time tile-preload/manifest data change; no Genesis control-flow ownership). Build 0095 FG-clear fix is **not** reopened; missing logo/RASTAN/sword are pre-existing, not regressions.

---

## 1. Romset provenance — data-set difference RULED OUT [STATIC]

`address_map.json build_inputs.variant = "world_rev1"`; source chips `roms/b04-*`. The **same** `maincpu.bin` contains **both** copyright strings:
- `maincpu 0x3BD9C` `"@ TAITO AMERICA CORP. 1987"` → arcade `0x03BD9C` → **Genesis `0x03BF9C`** (SEG#107, arcade_copy).
- `maincpu 0x3BF26` `"@ 1987 TAITO CORPORATION JAPAN"` → arcade `0x03BF26` → **Genesis `0x03C126`** (SEG#107, arcade_copy).
Plus `0x3BF5C "ALL RIGHTS RESERVED"`, `0x3BCC4 "CREDIT"`, `0x3BD58/0x3BE8A "PUSH…"`.

**Conclusion:** "TAITO AMERICA" vs "TAITO CORPORATION JAPAN" is a **region/DIP runtime string selection within one ROM** (KF-024), not a different data set. Build 0095 selects the US copyright string; the MAME reference selects the JP string. **This explains the copyright *text* difference only — it does NOT explain the missing red-logo *tiles*.** Data-set difference is ruled out for the tile dropout. [STATIC]

---

## 2. Layer attribution — FG text vs tile-art graphics

- **FG text-writer output [STATIC]:** the scores (`1UP/HIGH SCORE/2UP`), copyright, `CREDIT`, `PUSH…` are ASCII strings (`maincpu 0x3BCC4..0x3BF5C`) rendered through the glyph/text-writer path (glyph renderer arcade `0x03BB48` → **Genesis `0x03BD48`**, SEG#106 patched_site → the FG staging hook). These reach `staged_fg_buffer`; the copyright renders correctly in Build 0095 (FG text path alive).
- **Tile-art graphics [STATIC mechanism / INFERENCE per element]:** the large red **TAITO logo**, **RASTAN** wordmark, and **sword** are PC080SN tile graphics (not font glyphs), requiring their 8×8 tile **patterns** to be present in Genesis VRAM. They are PC080SN tilemap cells (BG Plane B and/or FG Plane A — exact plane per element deferred to the trace in §7).

So the title is **mixed**: FG font text (works) + PC080SN tile-art graphics (partial/missing).

---

## 3. Alive path for the VISIBLE TAITO cells [STATIC]

The title producers run (master-state machine, producers JSON-mapped: arcade `0x03AA54`→Genesis `0x03AC54`, arcade `0x03AAAE`→Genesis `0x03ACAE`, SEG#27 arcade_copy) and write nametable cells; the FG-clear fix (Build 0095) is confirmed working; commit propagates. **Cells whose tile codes are present in the title VRAM preload render** → the partial red TAITO logo. The overlay confirms these align with the arcade logo (positions correct), so the nametable writes and commit are not the defect.

---

## 4. Dropout root cause — SCATTERED holes from incomplete tile-pattern preload

**Mechanism [STATIC]:** `load_scene_tiles` (`scene_load.s:27`) copies into VRAM only the PC080SN tiles listed in the active scene's preload manifest. For the title (scene id 0) that is `genesistan_scene_preload_title` = `build/pc080sn_scene_preload_title.bin` (**~840 tile pairs** of `tile_rom_index → vram_slot`, `0xFFFF`-terminated). `genesistan_pc080sn_tile_vram_lut` (`build/pc080sn_tile_vram_lut.bin`, 32768 bytes = 16384 entries) maps every PC080SN tile code (`0x0000–0x3FFF`) to a VRAM slot, but **only the ~840 preloaded codes have their patterns actually loaded** into VRAM. Genesis VRAM caps near ~2048 tiles total, so the title preload is a budgeted subset of the 16384-tile PC080SN ROM (`build/regions/pc080sn.bin`, 524288 bytes). `tools/audit_vram_tile_usage.py` exists precisely to compare the "Title/Attract union" tile set against the preloaded/strip-builder set.

**Consequence [STATIC mechanism + INFERENCE]:** a title-art cell whose tile code is **not** in the title preload references a VRAM slot whose pattern was never loaded → it renders **blank** (or a stale/fallback pattern). The TAITO logo's cells that use preloaded codes show; cells that use non-preloaded codes are holes — **scattered throughout the logo, not a trailing cut**. This matches the user's overlay (specific interior cells missing throughout) and is structurally **SCATTERED interior holes**, **not** trailing truncation (the producer/descriptor emits the full extent; the *patterns* are missing). RASTAN/sword being fully absent = their tile codes are not preloaded **at all**.

**Root-cause locus [STATIC]:** build-time — the **title scene preload manifest / tile-LUT coverage** (`pc080sn_scene_preload_title.bin` + `pc080sn_tile_vram_lut.bin` generation) does not cover the full title-artwork tile set. This is a data/tooling gap, **not** a runtime translation patch and **not** the FG-clear path. (Distinct from KF-014's strip-table coverage, which the title-specific logo art evidently falls outside of.)

---

## 5. Trailing vs scattered — determination

**SCATTERED interior holes.** [STATIC mechanism + overlay] Evidence: (a) the dropout mechanism is per-tile-code pattern availability (each unloaded code → an isolated blank cell wherever used), which produces scattered holes, not a clean trailing cut; (b) the visible cells align with arcade positions (no truncation/shift); (c) RASTAN/sword fully missing is consistent with whole sub-sets of art tiles being unpreloaded. A trailing-truncation cause (producer stops early / descriptor count cut) is **not** supported — that would drop a contiguous tail, not interior cells, and would not leave aligned interior survivors.

---

## 6. RASTAN / sword — same path or separate

**Same path [INFERENCE, strong].** RASTAN wordmark and sword are PC080SN tile-art on the title scene, sharing the same title preload + LUT mechanism as the TAITO logo. They are fully missing because their tile codes are entirely unpreloaded (vs the TAITO logo partially preloaded). One fix — completing the title preload/LUT to cover all title-artwork tiles — would address all three, **subject to the VRAM-slot budget**: if the full title art exceeds the ~2048-tile VRAM capacity, a slot-allocation strategy (title-specific preload, dedup, or staged swap) is required rather than a flat manifest extension. (Sprite-path (PC090OJ) involvement for the sword is possible but not indicated by this mechanism; the trace in §7 confirms.)

---

## 7. Recommended next step — confirm before fixing (NOT a blind handoff)

**Not safe to hand a fix to Cody yet** [INFERENCE]: the *mechanism* is proven static, but the *exact missing tile set* and *VRAM-budget feasibility* are not enumerated statically (they depend on the runtime title nametable tile usage). Bounded confirmation step (one of):
1. **Static data audit (preferred, no ROM run):** run `tools/audit_vram_tile_usage.py` to enumerate the title/attract unique tile-code set, intersect with the ~840-entry title preload and the VRAM-slot budget, and list the missing title-art tile codes (and whether the full set fits ~2048 slots).
2. **Runtime trace (if audit is insufficient):** capture the title nametable tile codes (Plane A/B) at the steady title state and cross-reference against preloaded VRAM slots, identifying which logo/RASTAN/sword cells resolve to unloaded patterns.

The fix that follows is a **build-time** completion of `pc080sn_scene_preload_title.bin` (+ LUT regeneration) to cover the title-artwork tiles — or, if over budget, a title VRAM-slot allocation strategy. It is **not** a runtime translation-code change and does **not** touch the FG-clear path.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — title-art dropout attributed to incomplete title tile-pattern preload, SCATTERED holes; not closed), OPEN-016 (context), OPEN-015 (not touched).
- New issues opened: NONE (the title-preload coverage gap is tracked via this attribution; open a formal OPEN entry if Tighe/Cody prefer). Issues closed: NONE.
- Intentionally deferred: throne (not proven to share path), Start crash/OPEN-015, BlastEm/Nomad/HV, the exact missing-tile enumeration (→ §7 audit/trace), implementation.

## KNOWN_FINDINGS impact

**Option C — proposed refinement to KF-014** (assess only; not edited; Tighe/Chad Sr. approve). Proposed addition:

> Build 0095 title-art dropout: the title scene preload (`pc080sn_scene_preload_title.bin`, ~840 tile pairs, loaded by `load_scene_tiles` `scene_load.s:27`) and `pc080sn_tile_vram_lut` do not cover the full title-artwork tile set within the ~2048-tile Genesis VRAM budget. Title-art cells (TAITO logo, RASTAN, sword) whose PC080SN tile codes are unpreloaded render blank → scattered interior holes (TAITO partial) / full absence (RASTAN/sword). Producer/nametable writes and the FG-clear path are correct; the gap is build-time tile-pattern coverage, not runtime translation. The "TAITO AMERICA" vs "TAITO CORPORATION JAPAN" copyright difference is a region/DIP string selection within one ROM (both at Genesis `0x03BF9C`/`0x03C126`), not a data-set difference.

Confidence: STRONG for the mechanism (proven); the exact missing-tile set is WORKING_HYPOTHESIS pending the §7 audit/trace.

## STOP triggered

NO.
