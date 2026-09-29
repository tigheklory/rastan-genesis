# Cody — Phase-2 Initial Plane-A Population

## Scope and semantic cut

This task resumed from rejected Build 0387 with the Build-0386 selector-1/2 resolver restored. It did not revisit the third-chain exit, palette, H25, or the rejected final-resolver change. The semantic cut is the retained arcade record/source/descriptor and scene-fill decision into final native Genesis Plane-A names. The retired PC080SN C-window/name-RAM tail remains retired.

## Original arcade initial-fill contract

The original order is:

1. `0x050248` selects the record and writes `A5+0x013E`.
2. `0x0502BA` resets strip/group state.
3. `0x0502CC..0x050398` initializes all 16 live source pointers.
4. `0x0503BC..0x0503DA` selects the stream descriptor.
5. `0x050206` calls the 64-publication scene fill at `0x0503DC`.
6. `0x0503DC` calls setup at `0x055904/0x055C2E`, then performs 64 `0x055948/0x055C4A` publications and returns at `0x050482`.

This fill precedes the separate steady-state row/column streamer.

## Evidence and tooling

The bounded trace is `tools/mame/scripts/build0388_phase2_initial_plane_a.lua`. It extends the established six-button MODE route and MAME write-tap method. A bounded script was necessary because MAME's direct Genesis `videoram` reads returned non-authoritative zeros; it reconstructs final Plane-A VRAM from actual VDP PIO/DMA commands.

- Baseline: `states/traces/build0388_phase2_initial_baseline0386c_settled/`
- Corrected: `states/traces/build0390_phase2_initial_fixed0390c/`

## Build-0386-semantics baseline

At frame 741 the trace reached record `0x0011`, selector `0x0001`, stream pointer `0x00051183`, strip/group `0/0`, FG Y `0x0100`, active record/package `0x0011/0x0005`, and 16 valid sources.

| Contract | Phase-2 entry | 120 idle frames later |
|---|---:|---:|
| source pointers valid | YES | YES |
| staged nonblank words | 128 | 128 |
| staged sum | `0x03014B80` | `0x03014B80` |
| VDP nonblank words | 128 | 128 |
| VDP sum | `0x03014B80` | `0x03014B80` |
| collision nonzero words | 1735 | 1735 |
| collision sum | `0x00225958` | `0x00225958` |
| residency misses | 3648 | 3648 |

Entry and idle staging/VDP binaries are identical. No asynchronous initial population occurs during the 120 idle frames.

## Baseline first vertical publication

The first staged change is frame 2576 (40 changed cells). The first VDP change is frame 2578 (56 observed changed cells after publication coalescing). At frame 2578 staging and reconstructed VDP match at 184 nonblank words and sum `0x030202AA`. Source and collision binaries are unchanged. The steady-state vertical producer works, but repairs cells that should have existed at entry.

## First divergence and classification

Record, selector, stream pointer, and all 16 sources are correct; collision is populated. The initial 64-publication fill runs, but package 5 is installed only after it completes and record 17 is entered. During record-16 fill, package 0 remains active, producing 3648 misses and mostly blank final names.

This is **CASE D: sources valid, staging blank, collision populated**. The first divergence is native residency ordering before initial fill, not VDP publication: VDP faithfully publishes the incomplete staged table.

## MODE and natural path

MODE directly writes record 16 and reaches retained outer initialization, but bypasses `fg_boundary_advance_segment`, the earlier install boundary. This is not a MODE-specific tile defect: the general scene-fill producer can run after valid source selection but before record-selected native residency exists.

## Repair

`genesistan_hook_pc080sn_descriptor_rebuild`, the existing native replacement at arcade `0x055904`, now calls the existing general `fg_boundary_install` before rebuilding descriptors. The retained record, all 16 source pointers, and stream descriptor are valid there, while the first fill publication has not occurred. Repeated same-package rebuilds use the installer's existing no-op path.

There is no record, MODE, phase, tile, selector, or coordinate test; no fake scroll; no repeated steady-state streaming; no C-window/name-RAM restoration; no final-resolver or palette change.

## Rejected intermediate artifacts

Build 0388 encoded the call as a zero-byte insertion at `0x050206`. Downstream immediate map-data pointers did not receive the six-byte delta, so the stream cursor read six bytes early and selector 1 became 0. Build 0388 is preserved and rejected.

Build 0389 used a normal 4-to-10-byte shift replacement, but static disassembly proved `MOVE.L #map_data,Dn` operands are outside the current automatic ROM-operand relocation class, leaving the same pointer unshifted. Build 0389 is preserved and rejected without user evaluation.

Build 0390 removes that copied-ROM insertion and puts the call inside the existing native helper. `0x050206` and inline data retain their prior layout. Address-map proof maps arcade `0x055904` to patched Genesis `0x055994`, which jumps to helper `0x07254A`.

## Corrected Build 0390 trace

At frame 742 Build 0390 reaches the same record `0x0011`, selector `0x0001`, stream `0x00051183`, active package 5, and 16 valid sources.

| Contract | Phase-2 entry | 120 idle frames later |
|---|---:|---:|
| staged nonblank words | 2048 | 2048 |
| staged sum | `0x0319CFB9` | `0x0319CFB9` |
| VDP nonblank words | 2048 | 2048 |
| VDP sum | `0x0319CFB9` | `0x0319CFB9` |
| collision nonzero words | 1735 | 1735 |
| collision sum | `0x00225958` | `0x00225958` |
| residency misses | 0 | 0 |

Entry stage and VDP binaries are byte-identical and remain stable for 120 no-input frames. The first later staging change is frame 2577, followed by VDP at frame 2579; one cell differs at that first sampled boundary, and stage/VDP match (`2048`, sum `0x0319CF2F`). Source and collision binaries remain unchanged.

## Representative source → stage → VDP → collision cells

The descriptor is a bounded sample, not a selector-1 resolver oracle.

| row,col | source descriptor | staged | VDP | collision |
|---|---:|---:|---:|---:|
| 0,0 | `0x00016D5C` | `0x639F` | `0x639F` | `0x0001` |
| 0,18 | `0x00016D5C` | `0x6390` | `0x6390` | `0x0001` |
| 6,9 | `0x0001901C` | `0x6303` | `0x6303` | `0x0000` |
| 12,27 | `0x0001D59C` | `0x62FC` | `0x62FC` | `0x0000` |
| 18,18 | `0x0001F85C` | `0x6297` | `0x6297` | `0x3A00` |
| 24,36 | `0x00023DDC` | `0x6300` | `0x6300` | `0x0000` |

All 25 sampled entry cells match. Complete 2048-word binary equality proves full stage/VDP equality.

## Expected initial viewport

The retained fill produces the complete 64×32 resident Plane-A table (2048 words); H40 displays its current 40×28 subset. The viewport should therefore appear immediately from record-17 selector-1 state, not grow with motion. Build 0390 proves immediate resident staging/publication; visual composition still requires Tighe's comparison.

## Collision contract

Collision was already populated in baseline and is unchanged: 1735 nonzero words, sum `0x00225958`, with identical before-scroll and first-vertical binaries. This is graphics-residency ordering only.

## OPEN-028 and registry impact

OPEN-028 remains open. Earlier residency could be related, but its stray cell was not captured across first arrival/scroll-away/return, so a shared cause is not proven. OPEN-018 and OPEN-029 are unchanged. KF-078 records the durable initial-fill ordering contract and rejected insertion lesson.

## Build and gates

Build 0390 is the first testable corrected family because 0388 and 0389 were consumed by rejected intermediate encodings. Canonical, `_d`, `_s`, `_do`, and `_c` exist; counter is 390.

- canonical gate: PASS
- gameplay-entry gate: PASS; zero address/bus/illegal/crash-handler events
- five-variant set: PASS
- mandatory 30-second MAME trace: PASS; no unmapped addresses
- Phase-1 seven-epoch gate: FAIL/WARNING, pre-existing and preserved for evaluation

## User verification

Automated evidence proves source validity, complete initial staging, matching VDP publication, stable idle state, preserved collision, and later streaming. Tighe must confirm the intended Phase-2 visual composition. Build 0390 is not accepted until then.
