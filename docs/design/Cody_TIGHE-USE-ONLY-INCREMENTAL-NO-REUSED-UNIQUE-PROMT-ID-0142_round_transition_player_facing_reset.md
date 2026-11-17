TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0142

# Round-transition player-facing reset — stopped checkpoint

## Historical status at the end of PROMT-ID-0142

**BLOCKED ON HUMAN ARCADE ORACLE — NO FIX CLAIMED.**

PROMT-ID-0142 stopped at the correct evidence boundary. It did not establish the original arcade's exact LEFT-finish and RIGHT-finish behavior dynamically, so it did not change production gameplay code or produce a ROM. PROMT-ID-0143 created this missing historical checkpoint and initially corrected the arcade observer to be strictly passive. A subsequent explicit request from Tighe changed only the observer's initial conditions: it now selects R1-S3 and enables stock MAME invincibility so the human traces do not require replaying R1-S1/R1-S2.

## 1. Starting repository state for PROMT-ID-0142

- Branch: `rastan-direct-proposal`.
- Starting HEAD: `a823c07792d3f0c69cbcc6d9d653b1767787a5b2`.
- Makefile build counter: `573`.
- PROMT-ID-0141 source commit `579d1b4371dc35c7d4f39fb18f320bef0186579c` was present.
- Concurrent PROMT-ID-0135 audio source was already dirty and was preserved. Its recorded source SHA-256 was `08ab18d5491e4d561dca0ee4e93af31a14be39b619336cc491a5e882559826e9`.
- Existing dirty `AGENTS_LOG.md`, generated `apps/rastan-direct/out/*`, generated build maps/disassembly/trace/counter state, modified 0134 documentation, untracked 0135/0136 reports, and performance-roadmap documents were preserved.
- No reset, clean, rebase, rollback, broad restore, or push was performed.

## 2. Build 0573 baseline identity

Normal Build 0573 remains the visual/gameplay baseline:

- path: `dist/rastan-direct/rastan_direct_video_test_build_0573.bin`;
- size: `4,443,832` bytes;
- SHA-256: `1b396536f2a3543e42e6cab9b73e2f9bd67e40486ec3b070aa323223bc985b2f`.

Tighe's Build-0573 testing provides positive evidence that normal gameplay/presentation palettes, Plane-A initialization, READY, Stage Clear, Round-2 READY, and the tested R2-S1 palette path are correct. The artificial R2 direct-start no-human attract Layer-B mismatch is outside this task and is not blocking normal-game acceptance.

## 3. Observed normal-game defect

Tighe completed R1-S3 while Rastan faced LEFT. Through the complete natural sequence—boss completion, Stage Clear, ROUND 2 READY, then R2-S1—Rastan remained LEFT-facing. The expected behavior under investigation is that original arcade new-round initialization makes the R2-S1 player face RIGHT regardless of the R1-S3 finishing direction.

This report does not elevate that expectation into a proven reset mechanism. The original arcade dynamic oracle remains missing.

## 4. Authoritative facing-state inventory

| State | Arcade address / Genesis address | Meaning | Writers/readers established so far |
|---|---|---|---|
| player facing | `A5+$1114` = arcade `$0010D114`, Genesis `$00FF1114` | authoritative gameplay-facing word; `2` = visible LEFT, `3` = visible RIGHT | movement/action writers in `$051734/$051744`, `$051C66/$051C74`, `$051CFA/$051D08`, `$051E42/$051E4A`, `$051F7C/$051FC0`, `$0520F4/$052132`, `$0521A6/$0521E2`, `$05222A/$052268`, `$0522B0/$0522EE`, `$05231E/$05234C`, `$052376/$052382`, `$0524A6/$0524B2`, `$052580`, `$05262C`, `$05266A`, `$052718`; original compositor readers begin at `$0544AA/$0544E6`; native readers are in `native_player_frame_try` and `native_player_secondary_frame` |
| action state | `A5+$10E8` | idle/walk/jump/fall/death and related player action mode | reset to `3` by `$050562`; read throughout player update and by both native player-frame selectors |
| animation/movement selectors | `A5+$110E`, `A5+$1110` | retained player animation/directional substate used by left/right movement routines | `$050568` initializes `$110E` to `3`; `$052550..$05271E` uses these fields while selecting/writing facing |
| retained input | `A5+$10CE` plus original input word `$0010D37A` | active direction/action input, not a substitute facing default | player dispatcher `$051432..$0514EC` chooses left/right/idle paths; several action initializers update facing from direction bits |
| player position/motion family | `A5+$1262/$1264/$1266/$1268` | retained player coordinate/delta state consumed by movement and compositor paths | observed by the passive trace for lifecycle correlation; their exact individual velocity labels are not all proven here |
| native orientation key | derived directly from `A5+$1114` | orientation 0 when value is `2`; mirrored orientation otherwise | `apps/rastan-direct/src/pc090oj_hooks.s`, `native_player_frame_try` and `native_player_secondary_frame` |
| generated piece attributes / SAT HFlip | frame-table attribute selected by the native orientation key | final presentation consequence, not authoritative gameplay state | generated player frame index/piece tables feed final SAT words; existing KF-050 evidence confirms the player HFlip path, but 0142 did not capture a fresh transition-specific SAT row |

The semantic chain is therefore:

`A5+$1114` retained gameplay state → original/player-frame orientation choice → generated native frame/piece attribute → Genesis SAT HFlip.

There is no separate native cached-facing variable identified in this path. The native compositor reads the authoritative retained word each time.

## 5. Player initialization evidence

Original scene/player initialization begins at `$0501E2`. It calls:

- `$054052` player sprite-slot initialization;
- `$050248`, `$0502BA`, `$0502CC`, `$0503DC`, `$0504FA`;
- `$05053A` broad player-state initialization;
- conditionally `$05049A` round-start equipment initialization.

The broad `$05053A` block initializes many player fields, including `$10E8=3`, `$110E=3`, `$1108=$00FF`, multiple animation/equipment/state words, and player-coordinate defaults. It does **not** write `$1114`. `$05049A` also does not write `$1114`.

The right-movement family at `$05263A` reaches direct right-facing writes at `$05266A` or `$052718`; the analogous left family writes `2` at `$052580/$05262C`. The input dispatcher at `$0514C4..$0514EC` selects left, right, or idle behavior. Static evidence therefore proves multiple possible facing writers but does not yet prove which one constitutes the original new-round RIGHT default.

This is why adding `move.w #3,A5+$1114` to `$05053A`, READY, scene load, spawn, or a round-number test would be speculative and forbidden.

## 6. Original arcade compositor evidence

The original player compositor reads `$1114` at `$0544AA`, `$0544E6`, `$054512`, and corresponding primary/secondary piece paths. At `$0544E6`, facing other than `2` selects the mirrored PC090OJ attribute behavior. Thus `$1114` is not merely a Genesis convention; it is original arcade gameplay state driving original sprite intent.

No original-arcade dynamic left-finish or right-finish trace was completed in 0142. The exact reset writer PC, value, event, and call chain remain unproven.

## 7. Native Genesis realization

`native_player_frame_try` and `native_player_secondary_frame` read `0x1114(%a5)` directly. Value `2` selects one generated orientation key; every other value selects the mirrored key. The selected frame entry supplies final piece attributes, coordinates, tiles, and the SAT-facing result. The native path therefore faithfully displays the stale retained value seen in Build 0573; it does not independently choose LEFT at R2-S1.

The working defect class is consequently not proven to be a stale native flip cache. Current evidence favors a missing/different retained lifecycle writer or entry path, but classification A, D, E, or another source-backed mechanism must await the arcade oracle.

## 8. Automated Genesis evidence

The existing `round1_completion_runtime_gate.lua` was extended to log the authoritative facing word and executing PC alongside round, stage, record, end-state, and player state. It also accepts a controller-direction bias for the boss fight.

Using the preserved Build-0573 invincible derivative:

- `states/traces/promt0142_build0573_left_biased`: the existing pre-boss completion requests reached R1-S3; ordinary automated boss inputs completed the boss; facing was `2` at End-Round states 9, 10, 11, 12, 13 and at first R2 gameplay. The route passed at frame 3427.
- `states/traces/promt0142_build0573_alt_invincible`: the corresponding right-facing control retained `3` through states 9–13 and first R2 gameplay. The route passed at frame 1964.

These runs mechanically reproduce the Genesis retained-state behavior and agree with Tighe's Build-0573 observation. They do not prove what the original arcade does.

## 9. Rejected automated arcade route

An attempted arcade adaptation used a simple alternating controller loop with periodic attack and jump. It could not reliably defeat the original arcade boss or guarantee the orientation at the final hit. Earlier attempts also depended on invincibility/pre-boss memory mutations. Those runs were rejected as an oracle rather than being reclassified as natural gameplay.

The failed attempts establish no arcade-facing result. In particular, they do not prove that `$1114=0`, `2`, or `3` at any valid R1→R2 transition.

## 10. STOP condition

0142 stopped because the required authoritative fact was unavailable:

> No reliable original-arcade R1-S3 LEFT-finish and RIGHT-finish comparison had captured `$10D114`, its writer PC, and the surrounding round-entry state through R2-S1.

Production implementation was therefore not authorized by evidence. No facing fix was made and no build was produced.

## 11. Assisted human-trace handoff

PROMT-ID-0143 initially corrected the arcade observer to be strictly passive. Tighe subsequently requested two assisted initial conditions: start at R1-S3 and enable invincibility. The current launcher therefore uses the established stock MAME selector value `$F7` (`Round 1 Boss`) and the stock `Invincibility` cheat (`A5+$0040` debug gate).

It performs no input automation, boss-health write, forced boss completion, forced round transition, or synthetic facing write. Tighe owns the boss fight, the final blow, the finishing direction, and continuation into R2-S1. The trace observes the main CPU program space and exits after a stable R2-S1 retained tuple.

LEFT-facing oracle:

```bash
tools/mame/run_round_transition_facing_arcade.sh left states/traces/promt0142_arcade_left_human
```

Tighe plays the original arcade boss normally, delivers the final blow while facing LEFT, and continues until R2-S1 appears.

RIGHT-facing control:

```bash
tools/mame/run_round_transition_facing_arcade.sh right states/traces/promt0142_arcade_right_human
```

Tighe repeats the same process while facing RIGHT.

The LEFT/RIGHT argument labels the independent output and expected finishing case; it does not inject input or facing state. The direct R1-S3 start means these traces establish the original arcade's assisted R1-S3 boss-to-R2 lifecycle. If that differs from the previously observed natural Genesis route in a way that prevents identifying the authoritative facing writer, a full natural arcade traversal would remain necessary; no such equivalence is claimed in advance.

## 12. Fields and events recorded

The summary records `assisted_start=R1-S3`, selector `$F7`, and the active invincibility cheat. Each event row records:

- MAME frame and event label;
- current original 68000 PC;
- retained top-level states `A5+$0000/$0002/$0004`;
- round byte `A5+$0118`;
- subround marker/stage `A5+$1243/$1242`;
- record `A5+$013E`;
- end-round state/timer `A5+$13AA/$1392`;
- player action/animation/movement/input state `$10E8/$110E/$1110/$10CE`;
- player position/motion family `$1262/$1264/$1266/$1268`;
- authoritative facing `$1114`.

Events include every write to arcade `$0010D114` with the executing writer PC, frame-sampled facing changes, end-state changes, round changes, record changes, and terminal `ROUND2_GAMEPLAY`. R2-S1 entry requires 30 stable frames with round at least 2, stage and record at least `$17`, and end-state `$00FF`.

## 13. Evidence that will decide the next action

The two human traces must answer:

1. Does LEFT-finish arcade `$1114=2` become `3` before first R2-S1 gameplay?
2. Does RIGHT-finish remain `3` through the same event?
3. Which exact original PC performs the decisive write?
4. Is that writer part of broad player reconstruction, scripted R2 entrance movement, input-independent round entry, or another retained lifecycle path?
5. Which surrounding state first differs from Build 0573?

Only then can production choose between reinstating a skipped original opcode/path, correcting the natural new-round entry, restoring a broader player-object reconstruction, or—if the retained word already resets—correcting native presentation derivation. The fix must preserve subround transitions and death/respawn behavior rather than generalizing new-round semantics.

## 14. Files modified by PROMT-ID-0142/0143 checkpoint work

Tracing/tooling:

- `tools/mame/run_round1_completion_runtime_gate.sh`;
- `tools/mame/scripts/round1_completion_runtime_gate.lua`;
- `tools/mame/run_round_transition_facing_arcade.sh`;
- `tools/mame/scripts/round_transition_facing_arcade.lua` (subsequently updated at Tighe's request for R1-S3 start plus invincibility).

Documentation/process correction under PROMT-ID-0143:

- this report;
- `OPEN_ISSUES.md`;
- append-only `AGENTS_LOG.md` entry.

No file under `apps/rastan-direct/src/` was modified by 0142 or 0143. The independently dirty `apps/rastan-direct/src/sound/sound_comm.s` belongs to concurrent PROMT-ID-0135 work and was preserved.

## 15. Preserved subsystems and build discipline

- Production gameplay code changed: **NONE**.
- Numbered ROM produced: **NONE**.
- Build number consumed: **NONE**; counter remains `573`.
- Palette source/profile changed: **NONE**.
- Audio changed by this task: **NONE**.
- Plane A/B residency or publication changed: **NONE**.
- IRQ/performance scheduling changed: **NONE**.
- Player gameplay logic changed: **NONE**.

## 16. Open/Closed Issues impact at the 0142 checkpoint

- OPEN-041 records Tighe's positive Build-0573 normal presentation/palette evidence but remains open under its broader closure route.
- OPEN-042 records Tighe's positive Build-0573 Plane-A restoration evidence but remains open under its broader scene closure route.
- OPEN-043 was created to track the exact natural LEFT-finish carry into R2-S1 and the then-unresolved human-oracle blocker.
- CLOSED_ISSUES.md was unchanged at that checkpoint. No issue was silently closed.
- KNOWN_FINDINGS.md was unchanged at that checkpoint because the exact original new-round facing rule had not yet been proven.

## 17. Facts remaining unproven at the 0142 checkpoint

- The original arcade's exact `$1114` sequence for LEFT-finish and RIGHT-finish cases.
- The decisive original writer PC and call chain.
- Whether the right-facing result is an explicit facing reset, a broader player reconstruction, or scripted entrance movement.
- The first exact arcade-versus-Genesis lifecycle divergence.
- Death/respawn and subround-transition comparison under the eventual proposed fix.
- Transition-specific native SAT HFlip equality after correction.

At that checkpoint, no production correction could begin until human arcade evidence resolved the premise. The later LEFT and RIGHT controls disproved the force-right premise; a corrective writer and fix are therefore unnecessary rather than still pending.

## Historical final checkpoint

**BLOCKED ON HUMAN ARCADE ORACLE — NO FIX CLAIMED.**

That was the correct status when PROMT-ID-0142 stopped. It is preserved here as historical evidence and is superseded by the resolution below.

## Post-checkpoint human-oracle resolution — 2026-11-16 / PROMT-ID-0144

Tighe subsequently ran the assisted ORIGINAL ARCADE R1-S3 trace. The setup selected stock MAME `$F7` (`Round 1 Boss`) and enabled the stock invincibility cheat. Those conveniences did not inject input, synthesize facing, alter boss health, deliver the final blow, or force the R1→R2 transition.

Both human controls completed successfully:

- LEFT capture: Tighe finished R1-S3 facing LEFT; original arcade R2-S1 began with `A5+$1114=$0002` and remained visibly LEFT-facing. `states/traces/promt0142_arcade_left_human/summary.txt` reports `result=PASS`, `final_round=02`, `final_record=0018`, and `final_facing=0002`.
- RIGHT capture: Tighe finished R1-S3 facing RIGHT; original arcade R2-S1 began with `A5+$1114=$0003` and remained visibly RIGHT-facing. `states/traces/promt0142_arcade_right_human/summary.txt` reports `result=PASS`, `final_round=02`, `final_record=0018`, and `final_facing=0003`.

This resolves the original question. Build 0573 exhibits the same facing carry-over. The assumption that a new round should force Rastan to face RIGHT is disproven; there is no missing reset, no production bug, and no production correction to make.

The native Genesis realization is already faithful: `native_player_frame_try` and `native_player_secondary_frame` read retained `A5+$1114` directly and derive the generated orientation/SAT HFlip from it. No independent Genesis facing cache was identified. Do not add a new-round `face right` write, SAT/HFlip override, READY special case, scene special case, or round-number special case.

OPEN-043 is closed as **NOT A BUG — arcade-accurate behavior** under PROMT-ID-0144. This narrow result removes facing carry-over as a Build-0573 blocker; it does not accept Build 0573 against unrelated open conditions.

**RESOLVED — ORIGINAL ARCADE PRESERVES FACING; BUILD 0573 MATCHES; NO FIX REQUIRED.**

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0142
