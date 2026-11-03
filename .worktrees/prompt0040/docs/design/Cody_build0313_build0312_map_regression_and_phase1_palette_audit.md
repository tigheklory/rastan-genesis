# Cody Build 0313: Build-0312 Map Regression Rollback and Phase-1 Palette Audit

## Outcome

Build 0312 is preserved and rejected. Build 0313 removes only its three-instruction
Plane-A publication experiment and restores the exact tracked Build 0311 production
source. The canonical gate, gameplay-entry gate, all seven Phase-1 residency-package
gates, and the Build 0311 overlap contract pass. No collision, Plane B, sprite,
or palette implementation changed.

The four-way audit closes the visual-attribution error: representative cave,
waterfall, exterior, rope, ledge, bridge, and fortress patterns match the original
32-byte PC080SN pattern data and are resident in their required packages. The
systemic remaining defect is palette routing. Gameplay Plane A has an explicit
route only for arcade bank `0x003`; other banks fall back to `bank & 3` and borrow
CRAM lines owned by unrelated graphics. A route-only fix is not safe under the
current four-line ownership, so no Build 0314 was produced.

The enemy-density investigation is classification **C**: three comparable semantic
encounters did not show excess Genesis logical actors or duplicated top-level
native composites.

## Phase 0

Relevant priors:

- KF-010 establishes PC080SN BG to Plane B and FG to Plane A.
- KF-035 requires original arcade data, not Genesis LUT state, as tile intent.
- KF-046 governs scene-gated palette routes and shared CRAM ownership.
- KF-068 and KF-072 govern the native semantic cut and accepted Plane coordinates.
- KF-074 governs native gameplay sprite ownership.

Rediscovery Hazard HIGH findings touched: KF-068, KF-072, and KF-074. Their
contracts are preserved. Deferred-appendix entries used as canonical evidence:
none. Classification: **EXTENDING** OPEN-001/OPEN-006/OPEN-024. CLOSED-018
collision grounding was not reopened. Contradiction of a CONFIRMED or STRONG
finding: **NONE**.

## Architecture Compliance

Semantic cut retained: original arcade selector, logical row/column, source group,
tile code, and tile attribute decisions. Removed chip tail: PC080SN destination
publication remains direct final Genesis Plane-A staging plus VBlank commit.
Transitional compatibility added: none. Fixed Plane B, seven coarse Plane-A
epochs, Build 0311 overlap retention, native PC090OJ, zero runtime LRU/cache, and
zero software PC080SN device all remain intact.

## Evidence Classes

- **HARDWARE OBSERVATION:** Tighe's Build 0311/0312 real Genesis captures. They
  locate visible defects and semantic areas only. They have no synchronized WRAM,
  actor, SAT, or emulator state.
- **MAME GENESIS REPRODUCTION:** deterministic package installation, complete LUT,
  staged-name-word, palette staging, and DMA-transition gates for Build 0313. These
  are independent reproductions, not synchronized to hardware video frames.
- **ORIGINAL ARCADE REFERENCE:** decoded PC080SN map words and original 32-byte
  pattern data from `build/regions/pc080sn.bin`.

MAME's direct `:gen_vdp` videoram byte view returned zero-filled data. It is marked
unavailable and is not presented as a physical VRAM hash. Pattern identity is
instead proven end-to-end at the production boundary by exact original source
hash = generated upload source hash, generated code-to-slot mapping, complete LUT
PASS, staged name words, and an observed package pattern-DMA transition.

## Build 0312 Rejection

Build 0312 is preserved:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0312.bin`
- SHA-256: `c57ce5d9ad6294aed6671ee736d584a31b7b3083c4f9e1fdd0f1693e3f236d28`

Real-hardware observation: later Section-2 cave/green-wall graphics appeared at
the right of the first exterior screen while collision remained the correct
exterior geometry. This isolates the regression to visual Plane-A publication.

The only meaningful Build-0311-to-0312 production delta was added inside
`.Lplane_a_publish_logical_row_native`:

```asm
move.w  0x013E(%a5), %d1
lsl.w   #6, %d1
adda.w  %d1, %a0
```

Build 0313 removes only this adjustment. `git diff --exit-code --
apps/rastan-direct/src/tilemap_hooks.s` passes, proving the tracked production file
is exactly restored to its Build 0311 state. Build 0312 and all older numbered ROMs
remain preserved.

### Why it regressed

The original arcade calculation does contain a `segment_index * 0x40` term. That
fact did not establish that the term belonged in this native helper. The helper
already receives a native logical-row/source-group publication context. Adding the
arcade subexpression locally advanced only visual source selection while collision
and world progression remained unchanged. The first proven divergence is therefore
the helper-local adjustment itself: it is misplaced or double-applied at this
semantic boundary.

The exact complete runtime descriptor tuple was not captured at a hardware-video
frame and is not invented. The bounded comparison is:

| Effective-address component | Original arcade semantic formula | Build 0311 native helper | Build 0312 native helper |
|---|---|---|---|
| row segment | selects `strip_src_table[row_segment]` | represented by incoming native source context | same as Build 0311 |
| segment index | `A5+0x013E * 0x40` | no local addition | added locally |
| source group | `source_group * 4` | added locally | added locally after segment term |
| incoming base/prior adjustments | original unadjusted table base | already-native context; complete equivalence still open | same incoming context as Build 0311 |
| helper adjustment | original formula's segment and group terms | group term | segment term plus group term |
| effective descriptor/block | arcade event-specific value not captured in this task | correct Build 0311 hardware progression | visibly early cave family on first exterior screen |

Correct semantic placement/state remains **OPEN**. No replacement map arithmetic is
authorized until the complete original and native effective addresses are captured
at equivalent semantic events. This uncertainty does not weaken the rollback:
real hardware directly rejected the Build 0312 placement, and Build 0313 restores
the accepted source boundary.

## Build 0313 Artifact

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0313.bin`
- SHA-256: `b018dae1085c5e7b6566e9ad427718218a92f2538d79ad0296cd037145c8dc2b`
- Size: 1,670,840 bytes
- Counter: 312 -> 313
- Rolling artifact: byte-identical
- Canonical gate: PASS
- Opcode replacement and coverage: unchanged from the accepted architecture

The bounded gameplay MAME route installed package 0, remained on package 0 through
the first screen, reached controlled gameplay, and did not switch to a later cave
package. Thus the Build 0312 early-cave behavior was absent in the automated route.
Real-hardware visual acceptance remains required.

## Pattern, Geometry, Palette, Residency Audit

The machine-readable evidence is:

- `states/traces/build0313_plane_a_pattern_palette_audit_20260824_140000/pattern_palette_hash_evidence.json`
- `analysis/build0311_phase1_hardware_visual_audit/metadata/section_audit.json`
- `analysis/build0311_phase1_hardware_visual_audit/issues.json`

Eleven representative exact samples were audited:

| Family | Record | Arcade code/bank | Genesis slot | Source/upload SHA-256 | Pattern | Geometry | Palette | Residency |
|---|---:|---|---:|---|---|---|---|---|
| exterior rock | 0 | `0x0420/0x003` | 1048 | `fd2b4c19...16c149ce` | CORRECT | CORRECT | CORRECT | CORRECT |
| rope | 2 | `0x0110/0x005` | 961 | `557acb4b...5a9a96c8` | CORRECT | CORRECT in original map use | WRONG/unsupported | CORRECT |
| waterfall body A | 10 | `0x026D/0x01A` | 860 | `c975b657...d7b8c455` | CORRECT | CORRECT | WRONG | CORRECT |
| waterfall body B | 10 | `0x02B9/0x01B` | 884 | `43f75e3f...43cec37` | CORRECT | CORRECT | WRONG | CORRECT |
| waterfall edge | 10 | `0x02F8/0x01C` | 886 | `f2a77092...2e1125c1` | CORRECT | CORRECT | WRONG | CORRECT |
| dark cave rock | 5 | `0x00BD/0x003` | 1031 | `b27a76c4...08d2ca6` | CORRECT | CORRECT | CORRECT | CORRECT |
| cave wall | 5 | `0x07FC/0x004` | 874 | `6bca4e26...0de2d3e` | CORRECT | CORRECT | WRONG | CORRECT |
| vertical cave/drop | 11 | `0x0110/0x005` | 1117 | `557acb4b...5a9a96c8` | CORRECT | CORRECT | WRONG/unsupported | CORRECT |
| cave ledge | 11 | `0x01B0/0x003` | 1021 | `60d98d70...6755c9` | CORRECT | CORRECT | CORRECT | CORRECT |
| bridge | 15 | `0x095A/0x017` | 868 | `0a9c0c76...f57710` | CORRECT | CORRECT | WRONG/unsupported | CORRECT |
| fortress approach | 15 | `0x09C3/0x017` | 1115 | `243af0af...266aa` | CORRECT | CORRECT | WRONG/unsupported | CORRECT |

The full source/upload SHA-256 values, world row/column, package, and gate paths are
in the JSON artifact. Every sample has `source_to_upload_exact_match=true`, full
Plane-A LUT PASS, and observed pattern-DMA transition. The compiler preserves
attributes per map use; physical pattern deduplication does not canonicalize
`pattern + palette` and does not lose a logical use's full 9-bit bank before route
selection.

## Cave-Wall Palette Root Cause

Hardware observation: **right geometry, wrong color**.

The native attribute helper preserves the full PC080SN bank with `word & 0x01FF`
and calls `palette_route_lookup(scene=1, owner=PC080SN_FG, bank)`. The route table
contains only one gameplay FG row: bank `0x003` -> Genesis line 1. Cave-wall bank
`0x004` misses. The fallback computes `0x004 & 3 = 0`, so final name words select
CRAM line 0.

Line 0 is not random or transiently corrupt. It is intentionally owned and
reasserted each gameplay VBlank by the PC090OJ bank-`0x36` Lizardman carrier.
The captured staged line begins:

`0000 0EEE 000E 0468 08AC 046A 0246 ...`

Therefore the first divergence is classification **A, wrong name-word palette
bits** due to route miss and fallback. Classification **C** describes the resulting
ownership collision: the selected line correctly contains another owner's palette;
there is no evidence of an accidental overwrite. Pattern, geometry, and residency
are correct.

## Waterfall Re-audit

Waterfall patterns and residency are correct. Banks `0x01A`, `0x01B`, `0x01C`, and
`0x01D` have no explicit FG route and fall back respectively to lines 2, 3, 0, and
1. Those lines belong to BG bank `0x48`, Rastan/sprite bank `0x51`, Lizardman bank
`0x36`, and FG bank `0x003`. The RGB mismatch is therefore a palette-route defect,
not evidence of wrong waterfall tiles. Build 0311's 12-rope and 224-waterfall
overlap retention remains unchanged and passes its static gate (peaks 394/479,
missing 0, moved retained slots 0).

## Palette Implementation Boundary

No Build 0314 was produced. A simple additional route cannot safely solve this:
all four gameplay CRAM lines already have live owners and multiple Plane-A banks
coexist in the same phase. Assigning bank `0x004`, `0x005`, `0x017`, or
`0x01A..0x01D` to an existing line would merely move the corruption.

The smallest honest follow-up boundary is an offline palette/index consolidation
or an explicitly proven CRAM ownership/multiplex design that preserves original
per-use bank semantics. That task must identify all affected Palette Decision IDs,
inspect consumers, and update `specs/palette_decisions.json` in the same change.
The current registry contains no decision authorizing these Plane-A banks, so this
task does not invent one.

## Enemy-Density Investigation

The hardware video was used as a locator for three semantic encounter classes:

1. Segment 1: cave entrance / initial descent.
2. Segment 2: lower cave.
3. Segment 3: rope / upper cave.

Independent 5,000-frame MAME captures used the same deterministic coin/start/right
with periodic attack/jump control profile for Build 0313 Genesis and original
arcade. Exact RNG and frame synchronization were neither required nor claimed.

| Encounter | Genesis logical actors | Genesis eligible top-level native composites | Genesis SAT cells | Arcade logical actors |
|---|---:|---:|---:|---:|
| cave entrance / initial descent | 3 | 3 | 44 | 4 |
| lower cave | 4 | 3 | 36 | 4 |
| rope / upper cave | 4 | 4 | 51 | 4 |

The lower-cave fourth Genesis logical record was ineligible for native emission;
it did not create an extra composite. No same-family duplicate logical actors were
stacked at the same or near-identical coordinates in the selected maxima. Native
composite count never exceeded eligible logical count. SAT totals are expected
multi-cell composition counts and must not be interpreted as enemy counts.

Classification: **C, no excess enemy density found in the tested encounters**.
This does not claim every Round-1 random encounter is globally exhaustive. It does
answer the assigned minimum question: the three audited suspicious semantic areas
did not show extra Genesis logical enemies or native top-level duplication. Root
cause remains OPEN globally because the reported visual condition was not
reproduced; no enemy production fix or build was made.

Evidence:

- `states/traces/build0313_enemy_density_compare_20260824_143000/build0313_enemy_density.csv`
- `states/traces/build0313_enemy_density_compare_20260824_143000/arcade_enemy_density.csv`

## Validation

| Gate | Result |
|---|---|
| canonical gate | PASS |
| gameplay entry/control | PASS, 564 frames, 240 post-entry |
| all seven Phase-1 packages | PASS (`0,7,8,3,4,5,6`) |
| additional package 2 / record 5 | PASS |
| Build 0311 overlap contract | PASS, rope 12 / waterfall 224 / peaks 394 and 479 |
| A required counts | `282,333,444,368,483,433,349` |
| Plane-A drops | 0 |
| Plane-B required patterns | 854 |
| Plane-B drops | 0 |
| address errors | 0 |
| bus errors | 0 |
| illegal instructions | 0 |
| standard MAME smoke | PASS, no unique unmapped address |

## Files and Artifacts

Production source change relative to tracked Build 0311: none. Build 0313 was made
after removing the rejected uncommitted Build 0312 helper-local delta.

Task-specific durable changes:

- `docs/design/Cody_build0313_build0312_map_regression_and_phase1_palette_audit.md`
- `analysis/build0311_phase1_hardware_visual_audit/issues.json`
- `analysis/build0311_phase1_hardware_visual_audit/metadata/section_audit.json`
- `analysis/build0311_phase1_hardware_visual_audit/index.html`
- `analysis/build0311_phase1_hardware_visual_audit/make_storyboard.py`
- `tools/mame/scripts/build0310_epoch_gate.lua` (optional evidence dumps only)
- `AGENTS_LOG.md`
- Makefile-generated outputs and counter

Reusable traces:

- `states/traces/build0313_gameplay_entry_gate_20260824_133037/`
- `states/traces/build0313_phase1_epoch_gate_20260824_133040/`
- `states/traces/build0313_plane_a_pattern_palette_audit_20260824_140000/`
- `states/traces/build0313_enemy_density_compare_20260824_143000/`
- `states/traces/rastan_direct_video_test_build_0313_mame_30s_20260824_133050/`

## User Verification

1. Start Round 1 and confirm no Section-2 cave art appears on the first screen.
2. Confirm collision remains correct.
3. Reach Section 2 and confirm cave geometry appears at its proper location.
4. Judge map geometry separately from color; the bank-`0x004` color defect is still open.
5. Check rope/waterfall physical persistence separately from their known color-route defect.
6. Continue observing enemy density; the three MAME encounters were classification C,
   not a global proof over every RNG sequence.
