# Build 0461 — Updated Test Palette Candidate

**Agent/task:** Cody — build the next candidate from Tighe's current Test Palette Composer profile  
**Date:** 2026-10-20  
**Status:** CANDIDATE — PENDING TIGHE REAL-GENESIS VISUAL ACCEPTANCE  
**Palette issue:** OPEN-006  
**Accepted baseline:** Build 0458, source `e4545426`  
**ROM-producing source:** `ecab1f7e`  

## Outcome

Build 0461 consumes the complete live
`analysis/graphics_optimizer/editor_policy/Test.json` exactly as authored at SHA-256
`30dab473b12dd99e48db2528b2c3c634eefe4cb03f563c9b0ec25b0d1a43d755`. It adds generated
semantic production ownership for attract GAME OVER, gameplay P1/1UP, and gameplay score digits;
regenerates every existing object/usage mapping; and preserves the current Demon and bat mappings.
No palette decision was reassigned or optimized.

The normal visual-acceptance ROM is
`dist/rastan-direct/rastan_direct_video_test_build_0461.bin`, SHA-256
`6b18f419b2ae703d517825a683229945987bf15e9892749238131b03bd3b9629`, size 2,739,896 bytes.
The benchmark-only `_invincible` ROM is SHA-256
`5117967e821c2f357aa6b02179446a20221d3f02fed6e5fcc8db976aee56c87d`.

## Profile and generated-output proof

No snapshot is consumed. The Makefile reads the live Test profile directly. Its SHA is embedded
and checked in the generated palette-line LUT, PC090OJ reindex manifest, semantic-object asset
report, and CRAM report.

| Output | SHA-256 / result |
|---|---|
| Generated palette-line LUT `out/pc090oj_palsel_lut.inc` | `996d968ee78e2c1e2a1b94acb333b9879bcf1a77485277061121e0a601a47aa1` |
| Reindexed PC090OJ graphics | `12460aab49d2e4e0cd7b5ce05fd6b8f8cc22e4e1d775522201c2395dc2cfa32a` |
| Semantic PC090OJ profile slice | `cfff14aada0338903c62dfdd1e188fd43a0eea7cfcdd6d9dc52080ea141a1975` |
| CRAM line 0 | `273ab974ec8c85f4594878a39702d106614d4c7bbb601f667c7234165d99ecaf` |
| CRAM line 1 | `3cb995de81b06aa89d9ae3408a6953736c2b8e7437f0c134a222cf47afe2f4d5` |
| CRAM line 3 | `637a34db76429fc7c88917b1b7b0ef07da575f2d728238907aa0923d73f3714f` |

The generated LUT verifier tested 512 mappings and all 16,777,216 SAT word-2 cases with zero
mismatches. The reindexed-region verifier covered 930 `(code,bank)` requirements, 807 unique
codes, and 123 variant cells with zero mismatches, incomplete mappings, or stray writes.

## Exact semantic decisions

| Family | Current Test decision | Generated production decision |
|---|---|---|
| `object:attract.game_over` | line 0; `{1:7, 7:8}` | line 0; `{1:7, 7:8}` |
| `object:hud.p1_label` | line 0; `{5:12, 7:8}` | line 0; `{5:12, 7:8}` |
| `object:hud.score_digits` | line 0; `{7:8}` | line 0; `{7:8}` |
| `usage:flying_demon:bank0x35` | line 1; `{1:11,2:8,3:15,4:1,6:5,7:2,8:12,9:14,10:3,11:4,12:7,13:6,14:10,15:13}` | exact |
| `usage:small_bat:bank0x3E` | line 0; `{3:1,10:6,11:2,12:10,13:11,14:3}` | exact |
| `usage:large_bat:bank0x3E` | line 0; `{3:1,7:7,10:11,11:2,12:5,13:4,14:3}` | exact |

Compared with accepted Build 0458, these are exactly the three new semantic-object decisions plus
the changed small- and large-bat index maps. All other current Test usages are also regenerated,
not selectively copied.

GAME OVER now tags its semantic native asset and consumes the generated
`PC090OJ_GAMEOVER_PROFILE_LINE`; it does not use the bank-0x30 burst fallback. The gameplay P1
producer and score producer independently consume `PC090OJ_HUD_P1_PROFILE_LINE` and
`PC090OJ_HUD_SCORE_PROFILE_LINE`. Their patterns remain distinct even though Tighe currently maps
both to line 0. Assembly contains no per-object color maps.

There is no unrepresentable explicit decision and no silent reassignment. The Demon still shares
line 1 with other authored usages, so its final colors retain the already-documented shared-line
approximation; Build 0461 does not alter that authored result.

## Semantic cut and architecture

The retained semantic cut is object/usage identity and its authored Palette Composer decision,
resolved offline into native reindexed pixels, CRAM lines, and generated SAT palette-line
constants. The native runtime producers emit final Genesis SAT metadata for GAME OVER, P1, and
score. The retired chip tail remains bank-only PC090OJ palette inference/object-RAM execution; no
software PC090OJ device, runtime string comparison, shadow, fallback, or second palette system was
added.

No additional PC080SN/PC090OJ device code was removed in this task. Existing native sprite
producers and compatibility needed by unrelated unconverted families intentionally remain.

## Files changed

- `analysis/graphics_optimizer/editor_policy/Test.json` and
  `analysis/graphics_optimizer/editor_policy/profile_manifest.json` (Tighe/Andy-authored inputs)
- `specs/palette_decisions.json`
- `tools/graphics_editor/server.py`, `gen_reindexed_pc090oj.py`,
  `verify_palette_families.py`, `gen_test_palette_cram.py`
- `tools/translation/gen_pc090oj_palsel_lut.py`, `build_pc090oj_hud_white.py`
- `apps/rastan-direct/Makefile`
- `apps/rastan-direct/src/palette_hooks.s`, `pc090oj_hooks.s`, `pc090oj_assets.s`,
  `scene_load.s`

## Numbered-build record

The counter transitioned `458 -> 459 -> 460 -> 461`; no number was reused.

- Build 0459 was preserved and rejected: canonical gate detected that three 32-byte symbols used
  slices of one 96-byte generated artifact, so exact `.incbin` provenance could not be proven.
- Build 0460 was preserved and rejected: the three full 32-byte artifacts were correct, but the
  dependency auditor required their Make variables explicitly on the object rule rather than
  behind an aggregate variable.
- Build 0461 preserves identical authored values while giving every included symbol an exact
  whole-artifact hash and explicit dependency. It passes the canonical gate.

## Validation

| Check | Result |
|---|---|
| Palette-family/current-profile verifier | PASS; all generated profile SHAs equal current Test SHA |
| Generated palette/LUT verification | PASS; 512 LUT and 16,777,216 SAT cases, zero mismatches |
| Assembly/link and postpatch/reflow | PASS; 76 shift replacements, 7,203 branch fixes, 628 absolute-long fixes |
| Canonical gate | PASS; 229 opcode-replacement sites, coverage through `0x29CEB8` |
| Gameplay-entry gate, Genesis-driver MAME | PASS; 563 frames + 240 post-entry frames, no exceptions |
| Seven-epoch gate, Genesis-driver MAME | PASS; records 0/3/4/5/11/13, full A/B LUT checks |
| Build-0458 attract/ring verifier | PASS |
| Build-0456 selector verifier | PASS; operand `0x051155`, 157 bytes |
| Build-0455 item verifier | PASS; ROM+PC080SN oracle, 64 crossings, 27 plane patterns, 17+3 icons |
| Title verifier | PASS; 646 cells, 20 TAITO cells, 216 plane patterns |
| HUD verifier | PASS; 30 records, complete link chain, frontend-full/gameplay-reduced modes |
| BEST-5 verifier | PASS; 13 number and 8 name entries |
| Existing fixed30, Genesis-driver MAME | PASS; final PC `0x03B290`, SP `0x00FEFFFC`, no unmapped accesses |
| Complete seven-ROM family | PASS |
| `_invincible` verifier | PASS; 66/66 damage dispatch entries, no unrelated ROM differences |
| Existing rope benchmark, Genesis-driver MAME | PASS; 798/798/798 frames, median 13,317.147 ms, deterministic YES |

The rope result exactly matches accepted Build 0458, so no global performance regression is
detected. No new Lua route, save state, manual MAME play, palette benchmark, Phase D, or Phase E
was created or performed.

## Unresolved limitations

- Real-hardware palette appearance is not established by static/emulator gates.
- OPEN-006 remains open for broader sprite/high-bank palette work and the already-recorded Demon
  shared-line approximation.
- This task does not address OPEN-034/035/036 scene/palette lifecycle issues.

## USER MUST VERIFY

Use the **normal** Build 0461 ROM on real Genesis hardware and inspect: newly mapped sprites;
Flying Demon; gameplay P1/1UP; gameplay score digits; the large flashing attract GAME OVER; and
both small and large bats. Also verify attract Plane-B Segment 0, normal startup, death/next life,
R1 true endpoint/Subround 2, item screen, title, story, and BEST-5 remain unchanged. The
`_invincible` ROM is benchmark-only and is not the visual acceptance ROM.

## STOP status

Build 0461 is produced and mechanically validated. Real-hardware acceptance is pending Tighe.
Phase D and Phase E were not started. STOP.
