# Cody — Build 0175 Arcade Palette-Bank → Genesis Palette-Line Route LUT

**Date:** 2026-07-15
**Type:** Implementation-first, bounded build + runtime evidence
**Baseline:** Build 0174 `dist/rastan-direct/rastan_direct_video_test_build_0174.bin`
SHA `faca6b14b18add340828db00b1c080f602b227d5db05b2ee46b38d4d3c30d7aa` (visually rejected, evidence only)
**Produced:** Build 0175 `dist/rastan-direct/rastan_direct_video_test_build_0175.bin`
SHA `555c4d6c013df77fe28ce1e44fc27f039b609a1e6ad014e858b3fb5590db947f`, 1,582,580 bytes, counter 175. GATE_PASS.
**Scope:** PC080SN FG Stage 1 palette-bank → CRAM-line routing + carrier lifetime only. No input, slowdown, sky-reset, or FG-horizontal fix.

## Phase 0
Classification **EXTENDING**. Priors: KF-010 (BG/FG staging + full-plane commit), KF-043 (bank-51/line-3 sprite ownership), KF-045 (Stage 1 FG palette carrier). Architecture compliance CONFIRMED — arcade code remains the program; changes are palette-routing helper + carrier re-assert only. No second renderer, no forced colors, no hardcoded tile/sprite palettes.

## User visual rejection recorded
- Build 0172 proved FG 64-row projection was the right direction.
- Build 0173 changed FG to the wrong palette family.
- Build 0174 changed FG again, still wrong — FG now looks like raw steak / red-orange-white.
- FG **tiles** are still the right tiles. Problem is palette routing / carrier lifetime / arcade bank mapping — NOT tile source.
- Do not patch collision/input; do not address slowdown here.

## Primary question — answered: classification A
**A. Existing Genesis line 1 can carry arcade FG bank 3 during gameplay, but must be restored at a gameplay boundary after frontend overwrites.**

Proof from the Build 0174 trace (`states/traces/build0174_fg_palette_source_20260715_195606`) plus Build 0175 validation (`states/traces/build0175_validate`):
- FG cells already select Genesis **line 1** (Build 0174: 2016/4032 cells; Build 0175: 996/996 FG cells on line 1).
- Genesis **nothing writes line 1 during gameplay** (all line-1 writers — PCs 0x071CEE/0x071E0A palette hooks — fire before frame ~350; zero nonzero line-1 writes at frames ≥500).
- Line 1 is **scene-dependent**: frontend (scene 0) uses it for the title/story plane palette; gameplay (scene 1) uses it for FG. So it is *free* to carry FG bank 3 in scene 1.
- The only reason Build 0174 failed: at gameplay entry line 1 still held the **stale pre-gameplay frontend/story palette** (`0000 0000 08AE 068E …`), never re-loaded with bank 3. That stale palette is the "raw steak / red-orange" the FG showed.

So no line needs to be freed (rules out B/C), no dynamic multi-owner swap is required (rules out D beyond the single carrier restore), and the four-line budget suffices (rules out E): line 1 simply needs the bank-3 palette (re)asserted for scene 1.

## Active Stage 1 CRAM ownership inventory (Build 0175)
Converted CRAM words per Genesis line, arcade owner in ( ):

| Point (frame, scene) | L0 | L1 | L2 | L3 |
|---|---|---|---|---|
| Title (F90, s0) | bank0 HUD white | frontend title bank | bank48 (BG) | empty |
| Story (F300, s0) | bank0 | story plane bank | bank48 | bank51 sprites |
| READY/transition (F520, s1) | bank0 | (transient story bank) | BG bank | bank51 |
| Gameplay first (F571, s1) | bank0 | **bank3 FG ✓** | BG bank | bank51 |
| Gameplay populated (F900, s1) | bank0 | **bank3 FG ✓** | BG bank | bank51 |
| Sky/sunset change | deferred (see below) — route table has no phase entry, unchanged by this task |

Active tile users at gameplay (F900): BG cells = **2048 on line 2**; FG cells = **996 on line 1**; sprites nominally line 3. HUD/text = line 0. No plane cells use line 0 or line 3. Line-1 safety at each point: safe to reuse for FG bank 3 during scene 1 only (frontend owns it in scene 0) — this is exactly what the carrier flag enforces.

## Arcade bank / source inventory (Stage 1)
Converted Genesis CRAM words (from `arcade_palette_banks.csv`):
- **bank 0** (HUD/frontend) `0000 0EEE 000E 0468 08AC 046A 0246 0EEE …` → Genesis line 0. Not overwritten pre-gameplay in a harmful way.
- **bank 1** (frontend plane) `0000 000E ×15` → frontend line 1 in scene 0 (writer: 59ad4/45dae/3ba64 low-bank paths).
- **bank 3** (PC080SN FG terrain) `0000 0868 0846 0646 0624 0424 0402 0202 0202 028C 044C 0226 0004 0002 0222 0424` → **Genesis line 1 for gameplay** (writers: hook_3ba64 `.L3ba64_to_line1`, hook_59ad4 bank-3 branch). Overwritten before gameplay by the frontend line-1 write → the defect Build 0174 left.
- **bank 48** (PC080SN BG) → Genesis line 2 (BG cells).
- **bank 51** (PC090OJ sprites) `… 08AE 044A 0246 0008 …` → Genesis line 3 (KF-043). Preserved.

## Chosen FG bank-3 carrier line: **line 1**, carrier-restored (route flag).

## Implementation (route table + carrier lifetime)
1. **Route table** (`palette_hooks.s`, `.rodata palette_route_table`) — single source of truth for `(scene_id, owner, arcade_bank) → (genesis_line, flags)`:
   ```
   scene 1, PC080SN_FG, bank 3  -> line 1, CARRIER
   scene 1, PC080SN_BG, bank 48 -> line 2
   scene 1, PC090OJ,    bank 51 -> line 3
   scene 1, HUD,        bank 0  -> line 0
   ```
   with helper `palette_route_lookup(scene,owner,bank) -> line/flags`.
2. **Carrier cache population** — hook_3ba64 and hook_59ad4 set `fg_bank3_route_seen` when they route arcade bank 3 → staged line 1, and on exit snapshot the freshly-staged line 1 into `fg_bank3_line_cache` (16 words) + set `fg_bank3_cache_valid`. This captures the converted bank 3 the moment the arcade produces it, before any frontend clobber. No global suppression of 59ad4.
3. **Carrier re-assert** — `vdp_reassert_fg_bank3_line` runs each VBlank in `_vblank_service` before the palette commit: gated on `scene_id == 1`, it looks up the FG route line via the table and, if that line has drifted from the cached bank 3, restores it and sets `palette_dirty`. Frontend (scene 0) is never touched.

FG tile-attribute line bits (FG_PLANE_ATTR_HI → line 1) and the Build 0172 64-row FG projection are **unchanged** — this task only fixes the carrier the FG attr already points at.

## Carrier-lifetime proof
Build 0175 validation (`states/traces/build0175_validate/val.txt`):
- Gameplay F571/F900/F1400 (scene 1): **line 1 == `0000 0868 0846 0646 0624 0424 0402 0202 0202 028C 044C 0226 0004 0002 0222 0424`** — byte-exact arcade bank 3. `fg_bank3_cache_valid=1`, cache == bank 3.
- FG cells on line 1: 996/996; BG cells on line 2: 2048/2048.

## Frontend preservation proof
- Title F90 (scene 0): line 1 = `0000 08EE 00CE 008C …` (title palette) — untouched.
- Story F300 (scene 0): line 1 = `0000 0000 08AE 068E …` (story palette) — untouched.
- Line 0 (bank 0 HUD) and line 3 (bank 51 sprites) identical to Build 0174 across all points. The re-assert only fires in scene 1, so title/story/READY frontend line 1 is owned by the arcade palette hooks as before.

## FG attr / CRAM before → after
- FG attr line bits: unchanged (line 1) — before and after 0175.
- CRAM line 1 at gameplay: **before (0174)** `0000 0000 08AE 068E 046A 0046 0024 0A60 …` (stale frontend); **after (0175)** `0000 0868 0846 0646 0624 0424 0402 0202 …` (arcade bank 3).

## Visual result (expected)
FG tile shapes unchanged; FG colors move from raw-steak/red-orange toward arcade brown/rock/ground (bank 3). Sky (line 2 BG) unchanged/correct. Mountains unchanged. Left wall unchanged. FG vertical population unchanged (Build 0172 preserved). Title/story/READY unchanged. Sprites/HUD unchanged. No frontend palette regression. (Pixel confirmation pending Tighe screenshot.)

## Sky palette-change / level-reset — classification **D (unrelated / deferred), NOT A**
Documented: in arcade the overworld sky palette shifts for time/sunset without resetting; on Genesis the sky change happens but Rastan is reset to level start. This task's palette route is **CRAM-only and gameplay-gated**; it mutates no gameplay/scroll/level state and adds no phase entry, so it **cannot cause the reset** (rules out classification A = palette route/hook corrupts gameplay state). The route table sees **no** phase change at the sky point (phase_id unused). Best remaining hypothesis is B (sky phase shares state with level restart/checkpoint) or C (scroll/event trigger coincides), but that needs a dedicated arcade-vs-Genesis trace at the first sky-change scroll position — deferred, not fixed here.

## FG horizontal update — classification **B (FG horizontal source/window not updating), deferred**
Documented: after Build 0172 FG vertical row-depth is much better, but as the screen scrolls right the FG tiles do not update horizontally to match arcade. The Stage 1 FG replay (`genesistan_stage_fg_src_column`) replays a fixed FG_SRC family/window from ROM; it does not advance the horizontal source window with scroll. Not touched here (route-table work did not expose this boundary). Deferred to a dedicated FG horizontal-source task.

## Input / slowdown
- Rastan remains uncontrollable — not patched (out of scope).
- Game still runs slow — slowdown is not new, deferred, not patched.

## Exact source change
- `apps/rastan-direct/src/palette_hooks.s`: route table + `palette_route_lookup`; bank-3 line-1 cache snapshot in hook_3ba64 and hook_59ad4 (`fg_bank3_route_seen` gate).
- `apps/rastan-direct/src/vdp_comm.s`: `.bss` `fg_bank3_line_cache`/`fg_bank3_cache_valid`/`fg_bank3_route_seen`; `vdp_reassert_fg_bank3_line` (route-driven, scene-1 gated, compare-then-restore); call added in `_vblank_service` before the palette commit.
- `tools/translation/postpatch_startup_rom.py` + `verify_canonical_rom.py`: coverage invariant 0x1824A4 → 0x1825F4 (paired). opcode_replace count unchanged (151).

## Files changed
palette_hooks.s, vdp_comm.s, postpatch_startup_rom.py, verify_canonical_rom.py, docs/design/Cody_build0175_palette_route_lut_candidate.md, OPEN_ISSUES.md, AGENTS_LOG.md, KNOWN_FINDINGS.md, build artifacts.
