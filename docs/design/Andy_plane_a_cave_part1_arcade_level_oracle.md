# Andy — Plane-A Cave Part 1: Arcade Level Oracle (CORRECTED)

**Type:** Analysis / verification. **No production changes. No ROM. Build counter 297 unchanged.** Baseline:
Build 0297.

> **CORRECTION NOTICE.** An earlier draft of this report wrongly concluded the arcade attract demo does not
> reach the cave and STOPped. That was wrong (Tighe provided a screenshot of the attract demo IN the cave with
> GAME OVER). Two errors: (1) I defaulted to attract and gave up instead of confirming; (2) I detected "cave"
> via the Build-0217 `attr 0x0003 / tm0 56..111` descriptor, which does NOT signal the Stage-1 demo cave. This
> corrected report supersedes that draft.

## 1. Phase-0 baseline
- **Priors:** KF-010 (FG→Plane A), KF-014 (tile LUT, code 0x0000..0x3FFF), KF-011 (arcade VBlank owns
  progression), KF-015 (full-plane scroll +8) — all STRONG.
- **HIGH hazards:** KF-011.
- **Task classification:** EXTENDING (extends the canonical map-stream model toward the Stage-1 cave).
- **Issues touched:** OPEN-001/018 (native map/FG), OPEN-017 (FG/collision/rope, missing cave block).
- **Contradiction:** NONE with a KF; but the Build-0217 "cave = attr 0x0003" model is corrected as NOT the
  Stage-1 demo cave (§4).

## 2. Scope
Establish an arcade-ROM-derived oracle for the Stage-1 Plane-A level data through outdoor→cave, and validate it
against live original-arcade execution.

## 3. Arcade map-selection chain (canonical, re-verified)
Per `docs/arcade_reference/pc080sn/map_stream_format.md` (A5 = 0x10C000, **runtime-confirmed A5=0x10C000**):
stage `a5@0x1242` → `0x5073A` → segment `a5@0x13E`; segment → `0x50EE0` → `0x50F6B` selector stream (re-seed
`a5@0x10C6` @0x0503D6); segment → 16 strip-source tables `0x1691C..0x3725C` at `+seg*0x40` → `a5@0x1000..0x103C`;
segment → `0x507C5` → tm0 idx `a5@0x1386` → `0x3951C` descriptor. The map-stream byte pointer behaviour is
MAME-verified in the canonical doc.

## 4. CORRECTED cave model — the Stage-1 cave is SEGMENT-driven (tm0 stays 0)
**Runtime (ORIGINAL ARCADE `rastan`, `cave_diag.lua`, 200 s / 12001 frames):** A5=0x10C000 (11994/12001);
`a5@0x1386` (tm0) = **0 for the entire demo**; the tm0 descriptor at `a5@0x10FC`=0x3951C had attr **0x0002
(outdoor) throughout** — it NEVER became 0x0003. **Therefore the Build-0217 static extract (`0x3951C` entries
56..111, attr 0x0003, sources 0x00F91C/0x01011C) is a DIFFERENT / later cave, NOT the Stage-1 demo cave.** The
Stage-1 cave FG is produced by the **segment-indexed strip-source tables** (`0x1691C+seg*0x40`), with the tm0
descriptor (BG residency) staying outdoor.

## 5. Stage-1 segment → strip-source map (runtime, `seg_src_map.lua`, 130 s)
The demo walks **7 segments (0..6)**, tm0=0 throughout. Strip-0 base per segment (= `0x1691C + seg*0x40`,
confirming the model):
| seg | first_frame | fgx | fgy | strip0 base | interpretation |
|---|---|---|---|---|---|
| 0 | 8 | 0 | 0 | 0x000000 | pre-gameplay (title/attract) |
| 1 | 2587 | 0 | 0 | 0x01695C | outdoor start |
| 2 | 3807 | 360 | 261 | 0x01699C | outdoor |
| 3 | 4435 | 360 | 261 | 0x0169DC | outdoor |
| 4 | 4875 | 360 | **349** | 0x016A1C | **descent begins (fgy climbing)** |
| 5 | 5575 | 360 | **489** | 0x016A5C | **cave descent (rope/drop into cave)** |
| 6 | 6169 | 360 | 489 | 0x016A9C | cave interior (demo GAME-OVERs here) |
**OBSERVATION:** FG vertical scroll `fgy` (a5@0x10B0) climbs 261→349→489 across segments 4–6.
**INTERPRETATION:** the vertical descent into the first cave. Matches Tighe's screenshot (cave interior, GAME
OVER). **STATIC CORRELATION:** strip bases advance `+0x40`/segment from `0x1691C` (seg1=0x1695C … seg6=0x16A9C),
exactly the canonical `0x1691C..0x3725C` strip-source-table model.

## 6. Cave source data (identified; cell-level decode pending)
The Stage-1 cave FG source data is the strip-source content at the **segment 4–6 bases** (16 strip tables,
strip0 = 0x016A1C / 0x016A5C / 0x016A9C, +0x40/seg; the other 15 strips at +0x22C0 spacings). These pointers
are the arcade FG source for the cave, runtime-confirmed live. **What is NOT yet done:** the metatile→8×8
tile-code decode (the format that expands a strip-source entry → individual arcade tile identities +
attributes). Producing per-cell tile codes for the cave requires reverse-engineering that decode; it is the
one remaining piece for a cell-level oracle.

## 7. Original arcade MAME validation — CAVE REACHED (corrected)
The attract demo reaches the cave (Tighe screenshot + runtime: segments 4–6 vertical descent). The
segment→strip-source selection model is therefore **runtime-validated** against live arcade execution. Tools
(read-only, non-production): `tools/mame/scripts/cave_diag.lua`, `seg_src_map.lua`, `cave_reach_sampler.lua`,
`cave_walk_sampler.lua`. Evidence: `build/mame/home/{cave_diag,seg_src_map}/summary.txt`.

## 8. Semantic-map vs PC080SN-mechanics boundary
Semantic map = the ROM tables (§3) + arcade cursor/state; the strip sources are the FG map content. PC080SN
mechanics (C-window 0xC08000 dest + name-word emission) are already replaced natively (Builds 0242/0245/0247);
the native producers write `staged_fg_buffer` + collision (0x00FF1E00 = arcade 0x10DE00). **Semantic cut:**
retain the arcade map/selection/cursor/scroll machine; the chip tail (FUN_00055968/55990/559b2/55a14 +
C-window dest) is already replaced. **Transitional compatibility:** unreached physical chip-writer bytes;
Build-0217 cave *tile-residency* split (for the later/attr-0x0003 cave, build-time manifest, not a virtual
chip).

## 9. Missing cave-block deferral
**Missing cave-blocking block: DEFERRED** (recorded, not investigated). Arcade has a destructible square block
over the first cave entrance; Build 0297 does not. Ownership unresolved (PC080SN tilemap vs PC090OJ object vs
actor→tilemap mutation). Tracked under OPEN-001/017.

## 10. Open/Closed Issues impact
OPEN-001/018: the Stage-1 arcade FG segment→strip-source oracle is now runtime-validated; the cell-level tile
decode remains. OPEN-017: missing-cave-block recorded. No issue closed; no new issue.

## 11. KNOWN_FINDINGS impact
**Option C — proposed update** to the map-stream reference model (subject to Tighe review): record that the
**Stage-1 cave is segment-driven (tm0 stays 0, tm0-descriptor attr 0x0002) via the strip-source tables**, and
that the Build-0217 `attr 0x0003 / tm0 56..111` descriptor is a DIFFERENT (later) cave — not the Stage-1 demo
cave. This corrects a latent misattribution. (Not written unilaterally.)

## 12. Remaining uncertainty
1. **Metatile→8×8 tile-code decode format** (§6) — needed for per-cell cave tile codes.
2. Exact segment↔visual-area pinning (segment 4/5/6 = entrance/descent/interior) — a screenshot would confirm;
   `fgy` descent strongly indicates it.
3. Rope region — the demo GAME-OVERs at ~segment 6; the rope may be segment 6+ (beyond the demo death).
4. The event-completion→progression route (canonical §6/§8 downgrade) — unchanged.

## 13. Readiness for Part 2
The **selection/segment/strip-source oracle is validated** and ready to anchor a Genesis comparison at the
segment→strip-source level. A full **cell-level** comparison additionally needs the §6 metatile decode.

---

**Original arcade Plane-A level-data model understood:** YES for selection/segment/strip-source; the
metatile→tile-code decode is NOT yet done.
**Stage-1 cave progression understood:** YES — segment-driven (segments 4–6 vertical descent), runtime-validated.
**Persistent ROM map structures identified:** YES (0x5073A/0x50EE0/0x50F6B/0x507C5/0x3951C/0x1691C..0x3725C).
**WRAM cursor/cache structures identified:** YES.
**PC080SN destination mechanics separated from semantic level data:** YES.
**Cave oracle produced:** PARTIAL — segment→strip-source level validated; cell-level tile codes pending §6.
**Cave oracle runtime-validated in original arcade MAME:** YES (segment/strip-source selection; cave reached
segments 4–6).
**Representative cave tile codes/attributes available for Genesis comparison:** cave strip-source POINTERS yes
(0x016A1C..); individual tile CODES NOT yet (metatile decode pending).
**Missing cave blocking block investigated:** NO. **Remains deferred:** YES.
**Production source changed:** NO. **ROM produced:** NO. **Build counter:** 297 unchanged.
**Ready for Part 2 Genesis generator/build comparison:** YES at segment→strip-source level; cell-level needs §6.
**STOP triggered:** NO.
