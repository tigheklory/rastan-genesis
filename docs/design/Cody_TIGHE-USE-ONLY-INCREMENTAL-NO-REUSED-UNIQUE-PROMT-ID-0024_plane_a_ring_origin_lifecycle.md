# PROMPT-ID-0024 — Plane A ring origin lifecycle

Date: 2026-10-28  
Author: Cody  
Status: **Build 0515 candidate; Tighe acceptance and later-chain gameplay test required**

## Result

Build 0515 removes the spawn-specific Plane A scene image introduced in the rejected Build 0514.
There is now one generalized initialization path:

`retained camera/selector/descriptor decision -> camera-independent offline-native 64x64 logical map
-> live-scroll-derived 32-row physical ring -> VDP Plane A`.

The semantic cut remains above PC080SN execution. The retired tail is PC080SN C-window/name-RAM
storage, chip-address translation, and full-map projection. The implementation does not add a shadow
tilemap, virtual PC080SN, runtime descriptor interpreter, per-spawn precompiled ring, coordinate
hardcode, NOP, RTS bypass, fallback, or stability path.

This is a candidate, not an acceptance claim. The established automated R1-S2 route still does not
pass the later chain into records 18–21. Consequently, the exact later-chain symptom shown by Tighe
has exhaustive source/ring proof but not a complete natural runtime replay. Only Tighe can accept the
candidate.

## Arcade lifecycle and first divergence

Canonical Ghidra exports and the original disassembly establish this ordering:

1. arcade `0x050206` calls the retained fill at `0x0503DC`;
2. `0x0503DC` consumes the current descriptor/ring record and advances `A5+0x013E`;
3. arcade `0x05020A` calls `0x0504FA`;
4. `0x0504FA` indexes `0x050850 + (A5+0x013E * 12)` and installs the authoritative camera tuple:
   Plane-A X/Y at `A5+0x10AE/0x10B0`, Plane-B X/Y at `A5+0x10EC/0x10EE`, and limits/spawn data;
5. the post-scroll native replacement at arcade `0x050538` realizes the final Genesis rings.

The fill record being `final camera cursor - 1` is therefore deliberate lifecycle behavior. Build
0514 compiled that fill record into one physical 64x32 image using a build-time camera-table Y. At a
restart whose retained live camera origin differs, the first incorrect operation is Build 0514 runtime
PC `0x07096C`, `move.l (%a0)+,(%a6)+`: it copies physical row zero from the baked image before reading
the live `A5+0x10B0`. The failure is initialization, not later VDP publication.

Build 0515 instead keeps all 64 logical rows. After `0x0504FA`, it reads live `A5+0x10B0` and computes

`visible_top = ((-scroll_y + 8) & 0x01ff) >> 3`.

For each of 32 resident rows it copies logical `(visible_top + delta) & 63` to physical
`logical_row & 31`. All 64 columns are copied at their logical modulo-64 positions, so every legal X
origin is already resident and the live VDP H-scroll selects the viewport; X does not require a
spawn-specific rotation. This is the same coordinate invariant used by the selector-1/2 entering-row
publisher.

The retained rebuild/pan family remains authoritative: `0x055904` rebuilds the parallel descriptor
tables, `A5+0x10CA/0x10CC` owns strip/group progression, and `A5+0x10A8` owns selector behavior. The
new initializer consumes their final semantic result and does not replace that state machine.

## Implementation

- `tools/translation/compile_pc080sn_genesis.py`
  - emits six camera-independent Plane-A logical maps, each 64x64 final Genesis name words;
  - keeps code-to-slot resolution, authored palette line, and flip/orientation entirely offline;
  - emits no camera/spawn tuple in the Plane-A artifact;
  - leaves the independent Build-0514 Plane-B final map architecture intact.
- `apps/rastan-direct/src/tilemap_hooks.s`
  - selects the consumed fill record from live `A5+0x013E - 1`;
  - derives the resident top from live `A5+0x10B0` after the retained camera loader;
  - copies exactly 32 rows × 64 final words into the 32-row physical ring;
  - marks Plane A dirty, then performs the unchanged bounded Plane-B scene copy.
- `tools/translation/verify_plane_a_scene_fill_maps.py`
  - verifies all 24,576 logical Plane-A scene cells against retained semantic sources;
  - exercises all 512 nine-bit Y origins for each of six scene records (3,072 complete ring
    projections), including wrap, uniqueness, and complete 32-row destination coverage;
  - retains exhaustive checks for 12,288 Plane-B cells, 16,384 selector pan cells, 1,138,688 authored
    descriptor cells, and the no-shadow/no-runtime-resolver source contract.
- `tools/mame/scripts/final_life_zero_input_regression.lua`
  - adds observation-only dumps of the final 4 KiB staged Plane-A ring at first appearance and both
    retained-code non-final respawns; it does not write camera, graphics, or gameplay state.

## Runtime and exhaustive evidence

| Check | Result |
|---|---|
| Build/gate | `GATE_PASS`; gameplay-entry PASS; seven-epoch/package PASS |
| Mandatory Genesis NTSC trace | completed in `states/traces/rastan_direct_video_test_build_0515_mame_30s_20261028_131709/` |
| Generalized map gate | PASS: 24,576 A cells; 3,072 complete origin projections; 12,288 B cells; 16,384 pan cells |
| R1-S1 matched entry | record 1 / selector 0 / Y `$0000`; staged-to-VDP 0 mismatches, orientation 0, resident-pattern 0, Plane B 0, collision 0 |
| R1-S2 matched entry | record 17 / selector 1 / Y `$0100`; staged-to-VDP 0, orientation 0, resident-pattern 0, Plane B 0, collision 0 |
| R1-S2 reached Y `$0131` | logical rows 26–32: 0 compiled/staged mismatches and 0 staged/VDP mismatches; Plane B and collision all zero |
| Death/respawn lifecycle | PASS through 3 deaths, 2 non-final respawns, GAME OVER/Continue; no exception or unsafe visible generation |
| Initial + two respawn rings | record 1, live X/Y `$0000/$0000`; all three 4 KiB dumps SHA-256 `9b98f87c1542f3267fc96abf0bd5efc14bc1945a9ea00404c4bd5a47cd39e6b0` |
| One-time scene initializer | 65,882 M68000 cycles in host MAME; Build 0514 measured 62,008, delta +3,874 |

Evidence directories:

- `states/traces/rg0024_build0515_s1s1_entry/`
- `states/traces/rg0024_build0515_s1s2_entry/`
- `states/traces/rg0024_build0515_r17_y131_exact/`
- `states/traces/rg0024_build0515_scene_perf/`
- `states/traces/rg0024_build0515_plane_a_respawn_lifecycle/`

The raw arcade-code Plane-A comparison reports expected mismatches for authored synthetic carrier
codes; those are not resident-pattern or publication failures. The independent authored-row verifier
is the applicable Plane-A oracle and passes. Plane B remains directly comparable to original arcade
codes and passes.

The exact R1-S2 entry and Y=`$0131` staged Plane-A dumps are byte-identical to the rejected 0513/0514
behavior. That is expected because their table camera origin is `$0100`, already matching live entry
state. It also means these reached captures do **not** by themselves prove Tighe's later-chain symptom
fixed. The improvement is specifically that any later reinitialization/respawn now uses its live
origin rather than the one baked at build time. Records 17 and 21 are exhaustive offline-proven, but a
natural records 18–21 traversal remains Tighe's required manual acceptance test.

## Cost and non-regression boundary

`scene_fill_maps.bin` grows from 24,760 to 49,336 bytes (+24,576) and has SHA-256
`8cf53a5e57a66522e26980f3daac9b1c68f9e6ecc4e8064eeb39988556061dec`. Existing alignment absorbs
the growth, so the final ROM remains 3,825,336 bytes. The initializer still stages/publishes 4 KiB of
Plane A and 4 KiB of Plane B once per scene initialization. VDP transfer volume is unchanged; there is
no new per-frame work. Selector pan-row cost, collision production, and sound paths are unchanged.

No palette decision or object/pattern ownership was changed. The production `Test.json` SHA-256
remains `86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb`. Plane B, collision,
sprites, audio, packages, retained descriptor progression, and existing authored palette behavior are
outside this change.

## Artifacts

Build command:

```bash
source tools/setup_env.sh
make -C apps/rastan-direct RASTAN_PALETTE_TEST_PROFILE=1
make -C apps/rastan-direct test-subround ROUND=1 SUBROUND=2
```

| Artifact | Size | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0515.bin` | 3,825,336 | `cf7134bc4642e40c5741d86c93686126c3a974e7019a0093bcd4d341db268b01` |
| `dist/rastan-direct/rastan_direct_video_test_build_0515_S1-2.bin` | 3,825,336 | `877c5668669dbc9a8849f3e76451c169800ab8089b386afd69627bc10653f19c` |

The Makefile-owned counter is 515 and the consumed-number ledger records 0515 as
`canonical=PASS entry=PASS epoch=PASS`. The complete standard family (`_d`, `_s`, `_do`, `_c`,
`_full_hud`, `_invincible`) was also preserved under 0515. No runnable unnumbered candidate was
published.

