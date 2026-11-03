# PROMPT RG-008 — Cody — Change-Driven Gameplay HUD Optimization

## Result

Accepted Build 0467 remains immutable and unchanged. Build 0468 was produced from source
`888716e0b8028610435b8c354d1bd89920712ae7`, but was rejected after its deterministic rope result
regressed from `798/798/798` to `804/804/804`. The cause was an extra fixed HUD finalizer-lane call.
The corrected one-lane implementation is Build 0469, produced from exact committed source
`0596622e33e2e67b4d8521f5de00590c646ebca3`.

Build 0469 normal ROM:

- path: `dist/rastan-direct/rastan_direct_video_test_build_0469.bin`
- SHA-256: `61956ae1418b9b3e066e79aec23570ad42712d9a24606694b9f74dfa0a315210`
- size: 2,739,896 bytes
- counter: 469
- real-Genesis acceptance: PENDING

No accepted ref was created or moved. `accepted/build-0467` remains the accepted baseline.

## Semantic cut and SAT ownership

The retained arcade score/state bytes, visibility rule, and RG-005 coordinates remain the semantic
authority. The output is still direct Genesis SAT presentation; no PC090OJ object RAM, scanner,
decoder, compatibility mirror, or chip-address tail was restored.

Gameplay calls `pc090oj_native_emit_pass` every frame. `.Lnq_gameplay` starts at record zero in one
of `staged_sprite_sat` / `staged_sprite_sat_b`, emits every native lane, closes the link chain, and
marks the frame ready. `vdp_commit_sprites` publishes that completed bank, flips
`pc090oj_sat_bank`, and `.Lvcs_sat_dma` copies the whole 80-record table: 320 words / 640 bytes to
VRAM `0xF800`.

Therefore an unchanged HUD cannot disappear from the frame or remain only in the previous staging
bank. Its records must be finalized into the current bank each frame. Caching final SAT bytes would
also be unsafe because tile-residency allocation supplies the current physical tile slot and the
finalizer owns link order. RG-008 caches the compact arcade-semantic queue instead, then runs the
unchanged finalizer over it. This safely reduces semantic reconstruction CPU and WRAM queue writes,
but does not reduce gameplay SAT emission or DMA.

## Simplified gameplay HUD

The presentation cache contains the last three packed-BCD bytes actually consumed by the accepted
projector, the persistent compact `native_queue_hud` records, their count, and a valid byte. The
arcade work RAM remains authoritative. On a miss, six nibbles are decoded with the accepted
leading-zero rule, then the immutable three-record 1/U/P template is copied behind the visible
digits so SAT order remains byte-identical to Build 0467. On a hit, the projector returns after the
three byte comparisons without changing the queue.

RG-005 geometry is hard-locked:

- score digits: Y `0x10`, X `0x08..0x30`;
- `1`: Y `0x10`, X `0x40`, code `0xD039`;
- `U`: Y `0x00`, X `0x28`, code `0xD048`;
- `P`: Y `0x00`, X `0x38`, code `0xD046`.

Calculated structural work (cycle counts were not invented or claimed):

| Frame | BCD comparisons | digit conversions | semantic queue writes | cached/template copies | SAT records emitted | SAT DMA |
|---|---:|---:|---:|---:|---:|---:|
| Build 0467, unchanged | 0 | 6 | 0–6 digits + 3 labels | 0 | visible digits + 3 | 640 B |
| Build 0469, unchanged | 3 | 0 | 0 | 0 | same visible digits + 3 | 640 B |
| Build 0469, score change | 1–3 | 6 | 0–6 digit records | 3 immutable template records | same visible digits + 3 | 640 B |
| Build 0469, first use/invalidation | valid test | 6 | 0–6 digit records | 3 immutable template records | same visible digits + 3 | 640 B |

The rejected Build 0468 split digits and labels into two per-frame finalizer calls. Build 0469
restores the original single HUD-lane call and retains the compact cached order.

## Full HUD classification

The current shared `FRONTEND_FULL` implementation already has the requested architecture, so RG-008
did not replace it:

- static: 11 label records plus fixed patterns/geometry; installed from `native_hud_static_sat` on
  activation, not revisited by the stable prepare path;
- change-driven: P1 score (3 BCD bytes / 6 records), P2 score (3 / 6), high score (3 / 6), and
  credit (1 byte / 1 record);
- stable frame: ten scalar-byte comparisons, zero digit conversion, zero SAT staging writes, and no
  SAT publication when there is no other frontend change;
- changed score group: only its six records are regenerated into both persistent banks and directly
  published; changed credit updates one record;
- truly per-frame gameplay status in the `_full_hud` variant: energy indicator/bar animation,
  low-energy blink, lifecycle, and sound transitions. Those semantics are not static and were not
  cached or bypassed.

The bounded verifier now explicitly protects this template/change-driven full-HUD contract.

## Invalidation

Cold boot clears BSS. `genesistan_hud_deactivate` now clears the simplified cache-valid byte before
its frontend-mode early exit. Existing scene ownership invokes that boundary on gameplay entry and
frontend restoration, covering new game, Continue/death return, and later gameplay re-entry.
Within a continuing gameplay scene, an arcade score change is detected at the presentation boundary.
Simplified/full selection is a build-time ROM-family option, so caches cannot cross modes at runtime.
No new HUD lifecycle state machine was introduced.

## Bounded equivalence verifier

`tools/translation/verify_native_hud.py` now proves:

- immutable label words and the RG-005 Y/X/code geometry;
- one finalizer call per native gameplay lane;
- initialization equivalence for 57 bounded cases covering every digit at every position,
  leading-zero boundaries, zero, and six-digit values;
- unchanged consecutive values do not rebuild;
- changed values produce the new accepted compact stream;
- invalidation forces an equivalent rebuild;
- `FRONTEND_FULL` retains its immutable static installation and field-level dynamic updates.

Result: `NATIVE_HUD_VERIFY_PASS ... cache_cases=57 unchanged_no_rebuild=PASS invalidation=PASS`.

## Validation

Build 0469 results:

- canonical gate and both boot guards: PASS;
- gameplay entry: PASS at 569 frames, 240 required post-entry frames, zero address/bus/illegal/crash
  events;
- seven production epochs and Plane A/fixed Plane B LUT checks: PASS;
- final-life semantic mapping: PASS (`0x03A3C0 -> 0x03B320`);
- HUD equivalence/change/invalidation verifier: PASS;
- fixed30 Genesis NTSC trace: PASS, 1,798 frames;
- final-life zero-input: PASS, GAME OVER at frame 3,588 after three death entries, tuple `2/4/6`;
- RG-004 Continue: PASS at tuple `2/4/8`, 83/83 staged/VRAM names, zero mismatches, zero outside-panel
  names, all staged CRAM equal to actual CRAM;
- RG-004 attract: PASS, natural demo/death and second title at frame 7,233; all four first-title,
  second-title, and terminal CRAM lines match;
- configured family: PASS for normal, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible`;
- deterministic `_invincible` rope: `799/799/799`, median 13,333.835 ms. This is five frames better
  than rejected 0468 and one frame slower than accepted 0467; it is reported as measured evidence,
  not presented as a cycle measurement.

No manual/AI gameplay navigation was used. Only established deterministic and bounded project
harnesses ran.

## Files and scope

Production source changed:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/hud_native.s` (existing lifecycle invalidation only)

Verifier changed: `tools/translation/verify_native_hud.py`.

No remap spec, gameplay logic, flying-enemy/bat path, finalizer bbox path, Plane A/B producer,
palette mapping, `Test.json`, audio, Phase D, or Phase E was changed. Concurrent Andy RG-006/RG-007,
audio, and Palette Composer work was preserved and not staged.

Hardware acceptance remains pending for normal Build 0469 and its `_full_hud` variant.

## Writer-triggered continuation and failed Builds 0470–0471

Tighe rejected Build 0469 on real Genesis hardware. The shared `native_queue_hud` was later
rewritten by the gameplay energy/status producer (count 8, records 0–7); an unchanged-score cache
hit then finalized those status records instead of score/1UP. This explains the blank first HUD,
temporary complete HUD after scoring, high-digit loss, and whole score/label disappearance. SAT-bank
alternation was not causal.

The active score is the packed BCD field `A5+0x011C..0x011E`, not the earlier assumed
`0x011E..0x0120`. Static/decompiler/disassembly proof bounded its mutation paths to cold-start WRAM
zero, the paid/new-game block clear, two active-player block restores, and centralized award routine
`0x03B726`. Source `c344cae051a0fa271ca66e52062f1c042983034a` therefore replaced polling with a presentation-only
dirty byte, an independent persistent reduced-HUD semantic queue, lifecycle dirtiness, and four
proper shift replacements. Ordinary frames perform one dirty test and no score-byte reads or BCD
comparisons. Full HUD behavior remains unchanged.

Build 0470 was published and is consumed/rejected. Normal ROM SHA-256 is
`8e76ea9b147dec0897d68f60d355a31be8657461d28971b0a7ac62159b88bdc9` (2,739,896 bytes).
Its gameplay-entry gate raised vector 4 at stacked PC `0x03AAAC`. The first wrong operation was
the outer frontend dispatcher (`0x03A052..0x03A06A`) loading the stale state-1 word `0x0840` from
undeclared table `0x03A06C` and landing at the old handler address. The two earlier +6-byte player
restore notifications had moved semantic handler `0x03A8AC` to Genesis `0x03AAB8`; `0x03AAAC` was
now twelve bytes inside the moved handler. This was a jump-table reflow ownership omission, not a
dirty-state or SAT failure.

Commit `266fea8898a876374945f2a6c7b8a7fbc661c42f` declares all three `0x03A06C` signed-word table
entries. The in-memory reflow proof resolves state targets `0x03A9FE`, `0x03A8AC`, and `0x03A15A`
exactly (`09A4/084C/00EE` after RG-008 shifts). The established gameplay-entry gate now records the
crash record when an exception occurs.

Build 0471 was then published and is also consumed/rejected. Normal ROM:

- path: `dist/rastan-direct/rastan_direct_video_test_build_0471.bin`
- SHA-256: `71479918f165b7e26a2d2bc0881aee03d9a713634d4dc46ffee0e74496d1338e`
- size: 2,739,896 bytes
- exact source: `266fea8898a876374945f2a6c7b8a7fbc661c42f`

The 0470 illegal jump is gone: credit and START are accepted and the gate records zero address,
bus, illegal-instruction, or crash-handler entries. However, state remains `2/0/0`, scene remains
frontend (`0`), and PCs cycle at `0x03B298/0x03B29C` through frame 1,000; Round 1, package install,
and gameplay are never reached. The gameplay-entry gate and epoch-0 gate therefore FAIL. The build
was interrupted immediately after those mandatory canonical gates: fixed30 completion, family,
final-life, RG-004, HUD runtime presentation, SAT-bank, and rope validation were not run.

Build 0472 is not authorized. The remaining proof gap is the first state/control-flow operation that
leaves Build 0471 at `2/0/0` after START despite eliminating the proven 0470 table jump. No claim is
made that the writer-triggered candidate is correct or faster. Build 0467 remains the accepted
baseline; hardware acceptance for 0470/0471 is not applicable.
