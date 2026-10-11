# Cody Build 0406 — Native Sprite Completion Human-Validation Candidate

## Scope and status

Input baseline: Build 0405. Build 0406 is the first numbered ROM in the native
sprite completion campaign. It is issued at a genuine human-visual validation
boundary after static closure of the player table, all legal general compositor
selectors, and all nine specialized descriptor modes. It is **not** the final
zero-live-fallback completion candidate.

The semantic cut remains:

`retained actor state -> offline-expanded native frame -> final Genesis queue/SAT`

The generated-hit path does not parse arcade PC090OJ descriptor or piece
streams at runtime. Retained miss paths remain temporarily available for
full-game validation.

## Implemented closure

- Player BODY/weapon table: 1,200/1,200 reachable keys native, including all
  four flame-sword phases and both orientations; reachable `UNRESOLVED=0`.
- Universal compositor: 1,898 general records and 24 specialized dispatch
  records.
- Specialized subframe index: 682 bounded records covering modes `10`, `20`,
  `30`, `50`, `60`, `90`, `A0`, `B0`, and `C0`.
- Dense-index unresolved slots: 638, all `PROVEN_UNREACHABLE` (632 slots beyond
  signed table boundaries plus six orientations belonging to three invalid
  long-pointer entries).
- Gameplay contact reconstruction now consumes the same generated
  general/special geometry as the visual path on every native hit.
- Live-consumer manifest: 49 rows, 48 `NATIVE_COMPLETE`, one
  `NATIVE_PARTIAL`. The sole partial consumer is the fixed player FRONT
  producer because it still enters the `native_player_piece` tuple adapter.

Static proof and the exact nine mode contracts are maintained in
`docs/design/Cody_native_sprite_completion_campaign.md`.

Generated frame/index/residency artifacts are
`build/pc090oj_frame_table.bin`, `build/pc090oj_frame_index.bin`,
`build/pc090oj_generic_frame_index.bin`,
`build/pc090oj_universal_frame_index.bin`,
`build/pc090oj_special_frame_index.bin`,
`build/pc090oj_generic_base_lut.bin`,
`build/pc090oj_generic_usage_table.bin`,
`build/pc090oj_frame_residency.bin`, and
`build/pc090oj_frame_table.coverage.json`. The generated live-consumer
inventory is
`analysis/actor_decompilation/native_sprite_completion_manifest.tsv`.

## Validation counters

Build 0406 exports these lifetime counters:

| Counter | Address |
|---|---:|
| `native_player_fallback_count` | `0xFFBED8` |
| `native_generic_fallback_count` | `0xFFBEDA` |
| `native_specialized_hit_count` | `0xFFBEDC` |
| `native_player_piece_adapter_count` | `0xFFBEDE` |

The normal automated trace is not a full-game coverage run, so runtime
player/generic fallback totals are `NOT YET RUN`, not zero. Specialized hits
and FRONT adapter entries likewise require the human/full-game route.

## Mechanical gates

- Generated player frames: PASS — 1,200 native, zero player unresolved, 2,502
  unique payloads.
- Independent frame re-expansion: PASS — 38 exact Level-B records, 1,898
  universal general records, and 24 specialized dispatch records.
- Native completion manifest: PASS — 48 complete, one partial.
- Finalized-pattern/palette asset verification: PASS — 930 `(code, bank)`
  requirements, zero mismatches/incomplete/stray writes.
- Direct dispatch verifier: PASS — five Level-B usages, 38 direct records, no
  linear scan.
- Static reachable-unresolved gate: PASS — zero reachable unresolved.
- Residency/frame audit: PASS through the independent frame verifier and
  generated residency table.
- Assembler/link and both boot guards: PASS.
- Canonical ROM gate: PASS.
- Gameplay-entry gate: PASS.
- Gameplay-entry address errors / bus errors / illegal instructions /
  crash-handler entries: `0 / 0 / 0 / 0`.
- Mandatory 30-second GENESIS NTSC trace: 1,798 frames, no unmapped addresses.
- Full five-ROM variant-set verifier: PASS.
- Existing phase-one seven-epoch automated route: labeled `FAIL` warning. No
  PC080SN code was changed in this task.

## Required Tighe validation

Exercise representative normal and specialized actors, bosses/subobjects,
weapons including all flame-sword phases, player special/death states,
rope/contact behavior, both orientations, effects/projectiles/pickups/hazards,
and heavy scenes. Confirm visual geometry, ordering, flip state, contact
alignment, and absence of regressions. The follow-on full-game suite must read
the counters and establish zero generated-table fallback before retained miss
paths can be removed.

The burst first-frame palette defect and historical Segment-1 one-frame Rastan
glitch were not changed or adjudicated. Scheduling, Build-0401 ownership,
Phase D/E, IRQ6, controller sampling, H25, and unrelated PC080SN work were not
touched.

## Build artifacts

All artifacts are 1,994,424 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `6d83c02795abc9d1343acabba1873cfca7fa5226ae112815b8680f9c8371341c` |
| `_d` | `a622d2d28241cd2dc74f9551d5fce8883324475403465856ec1054dc84f36162` |
| `_s` | `33a92e16ed3ff9fa9a33f82810e901c1e0eed56edcaf48ec29e766abb226c777` |
| `_do` | `735d901be3781a41a39a2f7eb029181a115dc9d8e767fcece08285289777557a` |
| `_c` | `b6d77b20e5769106453a1ae94c3db8e20cad5c412b8a02675b77433e08eaa9a5` |

Counter: 406. Build ledger: canonical `PASS`, entry `PASS`, epoch warning
`FAIL`.
