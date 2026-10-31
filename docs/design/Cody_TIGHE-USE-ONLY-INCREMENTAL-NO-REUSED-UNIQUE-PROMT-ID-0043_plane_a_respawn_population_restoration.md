# Plane A initialization and respawn population restoration

Prompt: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0043`

Continuation: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0044`

Candidate delivered: Build 0525 (not accepted until Tighe tests it)

## Result

Build 0525 restores complete native Plane A population at the retained post-camera boundary without
using the rejected static all-record Plane A images. The implementation replays the existing native
selector producers over the original finite 16-by-4 scene-fill sequence, reproduces the retained
descriptor-source advance/rebuild cadence, uses the completed-fill selector saved at `A5+$132C`, and
restores the retained post-fill source pointers, cursors, and next-record selector.

The final Build 0524 defect was not DMA or later camera settling. Fourteen R1-S2 cells were already
wrong at the exit of the `$050538` helper. Selector 0 loaded authored logical code `$1731`, then loaded
its valid authored attribute `$0000`; the following `BEQ` consumed the attribute load's zero flag and
skipped the active residency LUT. It therefore stored unresolved logical code `$1731` instead of the
LUT result `$0301`. Build 0525 inserts `TST.W D3` at that shared selector-0 boundary before the blank
test. There is no code-specific or coordinate-specific patch.

## Semantic cut and retired tail

The cut is the retained post-camera return at arcade `$050538`, after retained `$0504FA` has selected
the live record and installed all six camera words. The helper consumes retained descriptor/metatile,
authored visual, package-residency, selector, and camera semantics and produces final Genesis Plane A
name words directly in `staged_fg_buffer`. The PC080SN C-window/name-RAM tail remains retired. No
virtual chip RAM, C-window shadow, runtime chip-address translation, tall map, checkpoint map, fallback
renderer, trampoline, NOP, or RTS bypass was introduced.

The runtime links neither `scene_fill_maps.bin` nor `record_native_row_maps.bin` for Plane A. Their
offline compiler products remain available only as exhaustive build-time oracles. Plane B retains its
independent scene-entry artifact and was not redesigned by this task.

## Preserved investigation history

- Build 0521 was the accepted starting evidence, not modified or overwritten.
- Build 0522 is rejected and preserved. It replayed the final descriptor set and produced 1,387 wrong
  changes at `$050538`; staged Plane A and actual VRAM agreed, proving publication was not the fault.
- Build 0523 is rejected and preserved. It restored the 16 source pointers and four-strip rebuild
  cadence, but replayed the post-fill selector.
- Build 0524 is unaccepted and preserved. It uses the selector saved by retained `$0558E8` at
  `A5+$132C`; this reduced R1-S2 to the final 14 unresolved-code cells.
- Build 0525 is the current test candidate. It retains the descriptor cadence and saved-selector fixes
  and corrects the shared selector-0 residency decision.

All numbered artifacts remain in `dist/rastan-direct/`. Builds 0522 through 0525 are recorded in the
Makefile-owned consumed-number ledger.

## First-writer proof for the 14 cells

Observation-only evidence is under:

- `states/traces/prompt0043_build0524_r1s2_reseed_boundaries/`
- `states/traces/prompt0044_build0524_r1s2_pre_lut_registers/`
- `states/traces/prompt0044_build0525_r1s2_initial/`

Build 0524 helper entry/exit captures show all 14 `$1731` words first appear during the bounded
`$050538` replay and remain unchanged after settling and in actual Plane A VRAM. At runtime Build 0524:

- helper entry: `$070914`; helper exit: `$070A36`;
- selector-0 authored code load: `$07063E`;
- zero authored attribute load: `$070642`;
- stale-condition blank branch: `$070652`;
- final staging store: `$0706BC`;
- active LUT base: `$FF6294`; LUT `$1731 -> $0301` throughout helper entry and exit.

The focused register trace records low D3 `$1731`, authored attribute `$0000`, active limit `$2800`,
and LUT base `$FF6294` before the faulty test. (The printed upper word of D3 is stale because the
producer intentionally loads the logical code with `MOVE.W`; all comparisons and indexing are word
operations.) Static instruction flow then proves `BEQ` tested the intervening attribute load, not D3.

All affected cells use original arcade raw tile `$0840`, authored logical code `$1731`, authored
attribute `$0000`, and expected active slot/name word `$0301`:

| Physical row | Logical row | Columns | Descriptor entries | Metatile descriptors |
|---:|---:|---|---|---|
| 3 | 35 | 5 | `$28320` | `$3B20` |
| 7 | 39 | 5 | `$2A5E0` | `$55F4` |
| 15 | 47 | 5, 9, 25 | `$2EB60`, `$2EB64`, `$2EB74` | `$3B20` |
| 19 | 51 | 5, 33 | `$30E20`, `$30E3C` | `$3B20` |
| 23 | 55 | 5, 41, 45, 49, 53, 57 | `$330E0`, `$33104`..`$33114` | `$3B20` |
| 27 | 59 | 5 | `$353A0` | `$5634` |

Before `$050538`, these physical cells contained incomplete/previous-fill words such as `$62D7`,
`$62EC`, `$6341`, `$6386`, and `$6448`. Build 0524 wrote `$1731` at helper exit, after settling, and
in VRAM. Build 0525 writes `$0301` in both staging and VRAM at every listed coordinate.

The current R1-S2 active LUT maps authored code `$1731` to slot `$0301`. The referenced 32-byte
pattern in Genesis VRAM is byte-identical to the compiled authored source pattern; both have SHA-256
`771f941213185cde2207d0579debd9e019ff9516f90bfe95e8e333c4b38614a9`.

## Corrective changes

- `apps/rastan-direct/src/tilemap_hooks.s`
  - bounded post-camera replay with exact source-pointer rewind/advance and 16-by-4 rebuild cadence;
  - replay selector sourced from retained `A5+$132C`, with the next-record selector restored;
  - explicit `TST.W D3` before selector-0's residency blank check;
  - symbolized observation-only helper exit for future instruction-boundary captures.
- `specs/rastan_direct_remap.json`
  - authoritative `$050538` semantic-cut note now records cadence, saved-selector, state restoration,
    and the explicit logical-code residency decision.
- `apps/rastan-direct/Makefile`
  - measured authored-profile coverage delta is `$50000` after removal of `$40000` of duplicate
    Plane A payloads.
- `tools/translation/verify_plane_a_scene_fill_maps.py`
  - enforces live-producer replay, removal of runtime static Plane A images/checkpoint arms, and the
    explicit D3 test.
- MAME capture tools gained observation-only helper entry/exit, LUT, register, actual Plane A VRAM,
  and respawn publication evidence.

## Build 0525 verification

The Makefile-owned canonical gate, gameplay-entry gate, seven-epoch/package gate, mandatory 30-second
Genesis NTSC MAME trace, and complete standard variant set all pass. The normal ROM is 3,792,568 bytes,
below 4 MiB; no mapper support was added.

Initial spatial comparison uses the current compiler's authored final-name oracle, the active runtime
LUT, actual staging, actual VDP VRAM, and referenced pattern bytes. Presentation-owned physical row 0
and off-screen column 0 are reported separately rather than treated as stage-assembly cells.

| Scene | Consumed scene record | Visible top | Authored-oracle mismatches | Staging/VRAM mismatches | Unresolved `$1731` |
|---|---:|---:|---:|---:|---:|
| R1-S1 | 0 | 1 | 0 | 0 | 0 |
| R1-S2 | 16 | 33 | 0 | 0 | 0 |
| R1-S3 | 22 | 1 | 0 | 0 | 0 |

Plane A staging and VRAM SHA-256 values are identical per scene:

- R1-S1: `9b98f87c1542f3267fc96abf0bd5efc14bc1945a9ea00404c4bd5a47cd39e6b0`
- R1-S2: `f99a4157b352a4ea622ccf4c33f48396133d7d113bc04e59a20662d384ef6e99`
- R1-S3: `16a628f43a4ee8670fde863f65331619242f3347942c875dab5bc7b25ccf6605`

Additional runtime checks:

- R1-S2 reached selector 1, record 17, Y `$013F`; logical entering rows 25..32 have zero compiled-row,
  staging/VDP, Plane B, resident-pattern, LUT, and collision mismatches. Evidence:
  `states/traces/prompt0044_build0525_r1s2_y131/`.
- Zero-input death/respawn route passed through three deaths and two non-final restarts with zero unsafe
  visible frames. Both staged respawn rings and both actual VRAM rings equal the R1-S1 oracle hash above.
  Evidence: `states/traces/prompt0044_build0525_final_life_zero_input/`.
- Direct R1-S2 audio gate passed with command `$27`, Re-In-Carnation intro `$31A4EC`, loop `$31B054`,
  10,264 YM writes, 121 PSG writes, 21,112 banked reads, and zero bank mismatches. The `$40000`
  address reduction is exactly the removed Plane A payload region; the Re-In-Carnation intro bytes are
  byte-identical to Build 0521 and retain SHA-256
  `4b26249d8739857c1755d11b1e038c6a41899ca4e34aca66fe3b7c5eb000c4bf`. Evidence:
  `states/traces/prompt0044_build0525_r1s2_direct_audio_validated/`.
- Build-time gates exhaustively cover 1,138,688 authored descriptor cells, all scene-origin
  projections, selector-1/2 semantics, collision independence, and active package LUTs.

The automated natural route did not reach R1-S1 checkpoint record `$000B`; prior zero-input natural
progress stopped at record 3. The phase/package gate proves record `$000B` selects runtime package 10
with 673 required patterns and zero LUT mismatches, but it does not prove real checkpoint respawn
gameplay. Tighe must verify the actual record `$000B` checkpoint, later R1-S2 scrolling/climbing, and
R1-S3 behavior before accepting the build. This report does not claim that checkpoint is accepted.

## Delivered ROMs

All Build 0525 artifacts are 3,792,568 bytes:

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0525.bin` | `e5f9b01205ed4a7d535488ab8b5da88522f9df33eeae70ca7d0261a694cbf98d` |
| `rastan_direct_video_test_build_0525_S1-2.bin` | `12a90eb5c1b94d6a98742b26d2ccac3aa63de093d5d6aad75d0b51185d802491` |
| `rastan_direct_video_test_build_0525_S1-3.bin` | `a6da6793afc621eaf73f4242974abdee6aa8786e5037e171c3ffeae52dbd9194` |
| `rastan_direct_video_test_build_0525_d.bin` | `d4d9be724dd4d26c0d19dcb8336489518067fbe3a9712caba43a94e9f8707e33` |
| `rastan_direct_video_test_build_0525_s.bin` | `8a61d7b89e2aff4eeb6dbc132207f00fead7b5cc2e7ec58e1fa59711d784c8fa` |
| `rastan_direct_video_test_build_0525_do.bin` | `2aee98843941a4a5857f6c2895f77ad2a9ff64d1d4ae1e8f37ae3ba0ca6728ae` |
| `rastan_direct_video_test_build_0525_c.bin` | `d4ed76c916f97e36ecbbc938d09d788092fda8ed6e7750d22e82484cc6e8bfe6` |
| `rastan_direct_video_test_build_0525_full_hud.bin` | `e9e28ec9373e7732fab1ecd82cadcc434ff83dad477ead50f376e76acfbc001e` |
| `rastan_direct_video_test_build_0525_invincible.bin` | `a84bba9bb3423a7bc3cfeed054c651de3dc73bbc350d86f7a9318274e0168012` |

Build counter: `0525`. The failed pre-publication coverage check did not create a runnable ROM and did
not consume another number.

## Source history

- Preserved pre-task source snapshot: `4ee94e06`.
- First live-producer restoration commit: `c7ac1f1c` (cherry-pick of isolated-worktree commit
  `b7647061`).
- Final root-cause, cadence, saved-selector, coverage, and evidence-tool implementation commit:
  `59260a9e`.
