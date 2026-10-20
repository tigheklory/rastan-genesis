# Cody Build 0462 — final-life semantic reflow fix

## Result and acceptance status

Build 0462 fixes the longstanding final-life hang present by Build 0446. The
retained arcade
terminal dispatcher reached subphase 9, but its hidden `BRA.W` at arcade `0x03A1C0` still carried
the original displacement `0x0F58` after a two-byte insertion between source and target. In Builds
0443–0461 that branch landed at Genesis `0x03B31A`, the `RTS` immediately before the mapped
high-score/final-life target at `0x03B31C`. It therefore returned without advancing terminal state.

The repair is owned by the existing semantic shift/reflow machinery. The spec now retains arcade
source `0x03A1C0` and arcade target `0x03B11A`; `fix_declared_relative_branches()` now supports and
validates both short and word-displacement 68000 branches, then derives the final displacement only
after source and target positions are known. Build 0462 encodes `60000F5A`, which decodes from final
source `0x03A3C0` to final mapped target `0x03B31C`. No final-ROM byte patch, generated-address
literal, historical delta, assembly workaround, NOP, RTS bypass, or gameplay rewrite was added.

Classification: **LONGSTANDING — PRESENT BY BUILD 0446**. This is not a Build-0461 palette
regression. Tighe accepted the normal ROM on real Sega Genesis hardware on 2026-10-20; OPEN-038 is
closed and `accepted/build-0462` identifies the exact ROM-producing source.

## Original arcade semantic path

The canonical Ghidra exports and raw `build/regions/maincpu.bin` establish this path:

| Meaning | Arcade PC / state |
|---|---|
| Player health test and death-state selection | `0x0517E6`; `0x0517EE` writes player state 8 at `A5+0x10E8` |
| Death animation terminal | `0x05198A`; after death step `0x38`, `0x051992` writes phase 4, `0x051998` clears subphase |
| Terminal dispatcher | `0x03A196`, word-displacement table at `0x03A1AC` |
| Life decrement and remaining-life test | `0x03A200`, `SUBQ.W #1,A5+0x0100`; zero selects phase/subphase 2 |
| Human-session final-life selection | `0x03A2D8`; nonzero `A5+0x0034` selects subphase 9 |
| Hidden phase-9 bridge | table entry 9 points to `0x03A1C0`, `BRA.W 0x03B11A` (`60000F58`) |
| High-score qualification / terminal continuation | `0x03B11A`; advances to subphase 3 and then GAME OVER flow |
| Human GAME OVER setup | `0x03A420`, selecting subphase 6 |
| GAME OVER dwell/exit | `0x03A450` and subphase-8 routine `0x03A478` |

The original branch target is therefore semantic arcade PC `0x03B11A`, not an inferred current
Genesis address. The dispatcher table is inline data. Canonical linear objdump decodes the tail of
that table as instructions, so automatic branch discovery did not see the instruction boundary at
`0x03A1C0`.

## Authorized bounded runtime evidence

One durable route was added:

- `tools/mame/scripts/final_life_zero_input_regression.lua`
- `tools/mame/run_final_life_zero_input_regression.sh`

It uses the established MAME field controls for coin/start, releases all gameplay controls, waits
through three natural deaths, and records only terminal/death state plus bounded PCs. No manual
gameplay, navigation, alternate route, save state, or broad instruction trace is involved.

The pre-fix Build 0461 run reached all three deaths, armed at frame 2541 with zero lives, entered
terminal tuple `outer=2 / phase=4 / subphase=9`, and remained there until the bounded stall detector
stopped it at frame 3449. The current ROM bytes proved the exact divergence:

- last correct instruction: Genesis `0x03A3C0`, mapped arcade `0x03A1C0`;
- encoded pre-fix bytes: `60000F58`;
- actual destination: Genesis `0x03B31A`, mapped arcade `0x03B118`, an `RTS`;
- expected destination: Genesis `0x03B31C`, mapped arcade `0x03B11A`.

After the production fix, the route advanced `9 -> 3 -> 8 -> 4 -> 6` and passed at frame 3522:

```text
result=PASS
reason=game_over_transition_reached
frames=3522
gameplay_seen=YES
death_entries=3
final_armed_frame=2541
outer=0002 phase=0004 subphase=0006 lives=0000
```

The first post-fix attempt exposed a diagnostic-only bound error: the original subphase-8 GAME
OVER dwell uses ten 96-frame countdown steps (about 960 frames), while the harness initially called
900 unchanged-state frames a stall. The bound was corrected to 1200 and the identical route was
rerun. This changed no ROM or production behavior.

Evidence:

- pre-fix: `states/traces/build0461_final_life_zero_input_20261020_111911/`;
- post-fix PASS: `states/traces/build0462_final_life_zero_input_20261020_112626/`.

## Historical boundary

Exact preserved artifacts show the structural boundary:

| Build | Source bytes at `0x03A3C0` | `0x03B31A` | `0x03B31C` | Classification |
|---|---|---|---|---|
| 0442 | `60000F58` | high-score routine begins | inside that routine | last structurally correct reference |
| 0443 | `60000F58` | `RTS` | high-score routine begins | first structurally bad build |
| 0444–0446 | `60000F58` | `RTS` | high-score routine begins | defect retained; Tighe proved 0446 runtime symptom |
| 0461 | `60000F58` | `RTS` | high-score routine begins | diagnostic route reproduces phase-9 stall |
| 0462 | `60000F5A` | `RTS` | high-score routine begins | correct mapped target |

Build 0443 introduced the first two-byte shift at arcade `0x03AA54`, between source `0x03A1C0`
and target `0x03B11A`. The source stays at `0x03A3C0`; the target moves from `0x03B31A` to
`0x03B31C`; the copied displacement did not. Exact ROM hashes and the existing 0442–0446 reports
were used. No historical address map was invented where one is not preserved. Build 0442 is the
last build with a proven structurally correct reference; its complete final-death route was not
rerun under this task's single-current-route authorization.

## Semantic correction and sibling audit

Changed production inputs/tooling:

- `specs/rastan_direct_remap.json`: declares the hidden word branch by original arcade source,
  target, width, and validated original bytes.
- `tools/translation/shift_table_patcher.py`: generically resolves declared 2-byte and 4-byte
  68000 relative branches after final shift layout.
- `tools/translation/test_declared_relative_branch_reflow.py`: semantic two-layout regression.
- `tools/translation/verify_final_life_transition.py`: read-only final-ROM/address-map verifier.
- `apps/rastan-direct/Makefile`: runs the semantic test and verifier for canonical plus all six
  configured variants.

The bounded same-class audit covered the existing declared short branch `0x0596FA -> 0x05976C`
and the pre-title-insertion terminal/reset/credit/title dispatch tables at `0x03A1AC`, `0x03A57C`,
`0x03A5D2`, `0x03A8CE`, and `0x03AA20`. Only the hidden word branch at `0x03A1C0` crossed the
`0x03AA54` insertion without semantic ownership. The existing short declaration remains correct;
`0x03AA20` already has explicit table ownership. No unrelated reference family was changed.

The graphics semantic boundary is unchanged: no PC080SN/PC090OJ producer or chip tail was touched.
This correction is retained arcade terminal control flow handled by the established opcode-reflow
delivery mechanism.

## Future-reflow proof and final-ROM proof

`test_declared_relative_branch_reflow.py` uses arcade source `S=0x20`, target `T=0x80`:

- Layout A decodes to `0x000080`.
- Layout B inserts six bytes between S and T and decodes to `0x000086`.
- The stale old displacement would still decode to `0x000080`.

Result:

```text
DECLARED_BRANCH_REFLOW_TEST_PASS layout_a=0x000080 layout_b=0x000086 stale_b=0x000080
```

The old implementation rejects the representative 4-byte branch and cannot generate Layout B,
so the regression fails against the old behavior.

The final-ROM verifier independently maps both semantic arcade PCs using the generated final map,
decodes the branch, and compares the two targets. It does not modify the ROM. Canonical, `_d`, `_s`,
`_do`, `_c`, `_full_hud`, and `_invincible` all report:

```text
FINAL_LIFE_TRANSITION_VERIFY_PASS source=0x03A3C0 generated_target=0x03B31C mapped_target=0x03B31C
```

## Build 0462 validation

ROM-producing source was committed before the build as
`faf55624` (`Fix final-life branch semantic reflow`). The Makefile-owned build consumed number 462
and completed successfully. Baseline was Build 0461; the build counter advanced `461 -> 462`.
The normal artifact is
`dist/rastan-direct/rastan_direct_video_test_build_0462.bin`.

| Validation | Result |
|---|---|
| Python semantic Layout A/B reflow test | PASS |
| Final-life final-ROM verifier, all seven variants | PASS |
| Assembly/link and normal translation/generation | PASS |
| Postpatch/reflow (`76` replacements, `3` jump tables, `7203` branches, `2` declared branches, `628` absolute-long) | PASS |
| Canonical gate and boot guards | PASS |
| Gameplay-entry gate | PASS |
| Seven-epoch gate | PASS |
| Build-0458 attract/ring verifier | PASS |
| Build-0456 selector verifier | PASS |
| Build-0455 item verifier | PASS |
| Native title, HUD, and BEST-5 verifiers | PASS |
| Complete canonical/`_d`/`_s`/`_do`/`_c`/`_full_hud`/`_invincible` family | PASS |
| Fixed 30-second Genesis NTSC trace | PASS, 1,798 frames, no unmapped address |
| `_invincible` configuration verifier | PASS, 66/66 damage dispatch entries, zero unrelated differences |
| Existing deterministic `_invincible` rope benchmark | PASS, `798/798/798`, 13,317.147 ms, deterministic YES |
| Authorized normal-ROM zero-input three-death route | PASS, GAME OVER subphase 6 reached |

Artifacts are 2,739,896 bytes each. Canonical SHA-256 is
`dede71fef20f40a829b07065dff3c3afd31c9f0d6623c30ba42caa7c7c7e5526`; `_invincible` SHA-256 is
`27481bca1a1065612aff28fd95f75117ecd97a3252a8775ef4dab3e173263de9`. Counter is 462.

Existing project tools reused: the canonical Ghidra exports/raw disassembly, current address map,
shift-table patcher, Makefile gates, fixed30 workflow, configured-family verifier, and established
rope benchmark. New tooling created: one durable zero-input final-life route, a semantic two-layout
declared-branch regression, and a read-only final-ROM target verifier. These were necessary because
the branch boundary is hidden after inline dispatch-table data, no existing route exercised three
natural deaths without gameplay navigation, and no existing verifier asserted this semantic target.

## Real-hardware acceptance

Tighe tested the **normal** ROM on real Sega Genesis hardware, allowed all lives to be lost naturally,
and confirmed final death no longer hangs and terminal/GAME OVER progression continues. `_invincible`
was not used for acceptance.

Build 0462 is the accepted production baseline. Ref `accepted/build-0462` points to exact
ROM-producing source `faf556241a4f1666245d3424dfa41a5c248fa85e`. Attract-loop actor cleanup,
reset/title stale actors, 1UP/score geometry, and Demon palette realization remain separate and
deferred. Phase D and Phase E were not started.
