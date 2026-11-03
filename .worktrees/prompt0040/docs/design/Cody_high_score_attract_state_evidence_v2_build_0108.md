# Cody - High Score Attract-State Evidence v2: Original Arcade vs Build 0108

**Date:** 2026-06-27  
**Type:** Runtime evidence / analysis only  
**Build:** 0108  
**Build ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0108.bin`  
**Build SHA256:** `bd0c7faa187f6d9aded904638e8d7cb8c9e3df6304c5178a36ec02e6c8bbad09`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/bookmark changes. No implementation. No fix design.

## Phase 0

Read before work:

- `RULES.md`
- `ARCHITECTURE.md`
- latest `AGENTS_LOG.md` tail

Architecture compliance: preserved. The arcade code remains the program; no Genesis-side control-flow change, helper change, diagnostic ROM, bookmark, or source modification was made.

## Correction Accepted

The prior candidate family is discarded for passive no-input high-score attribution:

- `runtime_genesis_pc 0x0003AAAC`
- `runtime_genesis_pc 0x0003AAD2`
- `runtime_genesis_pc 0x0003AE76`
- and their arcade equivalents from the prior report

These were not used as assumed high-score targets in this pass. The v2 attempt was built around no-input attract observation and state-field logging.

## Evidence Artifacts

Timestamp: `20260627_153132`

Original arcade artifacts:

- `states/traces/original_arcade_high_score_attract_v2_20260627_153132/arcade_attract_observer.lua`
- `states/traces/original_arcade_high_score_attract_v2_20260627_153132/state_snap_log.tsv`
- `states/traces/original_arcade_high_score_attract_v2_20260627_153132/arcade_state_only_full.lua`
- `states/traces/original_arcade_high_score_attract_v2_20260627_153132/state_full_log.tsv`
- `states/traces/original_arcade_high_score_attract_v2_20260627_153132/state_wp/arcade_master1_watch.cmd`
- `states/screenshots/original_arcade_high_score_attract_v2_20260627_153132/rastan/0000.png` through `0004.png` (early title only; not high-score)

Build 0108 artifacts:

- `states/traces/build_0108_high_score_attract_v2_20260627_153132/build0108_a5_base_probe.lua`
- `states/traces/build_0108_high_score_attract_v2_20260627_153132/a5_base_probe.tsv`
- `states/traces/build_0108_high_score_attract_v2_20260627_153132/build0108_state_short.lua`
- `states/traces/build_0108_high_score_attract_v2_20260627_153132/state_short_log.tsv`

## No-Input Constraint

No input was scripted or sent in this task: no coin, no start, no buttons. All observed state sequences are no-input attract/title startup sequences.

## Tooling Blocker

The required visual-anchored full attract capture could not be completed in this local MAME environment.

Observed failures:

- Repeated Lua `manager.machine.video:snapshot()` capture stalled after the fifth snapshot around frame `150`.
- `-aviwrite` failed with `Error creating movie, generic:30 Read-only file system` and did not produce a usable movie.
- Software-video and GUI MAME frame-notifier runs also stalled/crept around frame `150-200` before the passive high-score attract screen.
- A debugger watchpoint for original arcade master-state value `1` (`arcade-RAM-address 0x0010C000`) did not hit within a practical no-input window and was stopped manually. This supports the v2 correction that master state `1` is not a proven passive high-score target, but it is not itself a full high-score-state proof.

Because the arcade high-score/table screen was not visually reached in this evidence pass, no visual high-score screenshot path exists from this run.

## Observed Attract Sequence So Far

### Original arcade, no input

Source: `states/traces/original_arcade_high_score_attract_v2_20260627_153132/state_full_log.tsv`

```text
STATE_CHANGE frame=1   pc=03AEC6 a5=00000000 s0=0000 s2=0000 s4=0000 s12=0000 cnt=0000
STATE_CHANGE frame=14  pc=03B08E a5=0010C000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=00D0
SAMPLE       frame=30  pc=03B098 a5=0010C000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=00C0
SAMPLE       frame=60  pc=03B094 a5=0010C000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=00A2
SAMPLE       frame=90  pc=03B094 a5=0010C000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=0084
SAMPLE       frame=120 pc=03B08A a5=0010C000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=0066
SAMPLE       frame=150 pc=03B086 a5=0010C000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=0048
```

Arcade A5 base observed during active title/attract state: `arcade-RAM-address 0x0010C000`.

### Build 0108, no input

Source: `states/traces/build_0108_high_score_attract_v2_20260627_153132/state_short_log.tsv`

```text
STATE_CHANGE frame=1   pc=000308 a5=00000000 s0=0000 s2=0000 s4=0000 s12=0000 cnt=0000
SAMPLE       frame=30  pc=0706FC a5=00FF0000 s0=0000 s2=0000 s4=0000 s12=0000 cnt=0000
STATE_CHANGE frame=40  pc=07016A a5=00FF0000 s0=0000 s2=0000 s4=0001 s12=0000 cnt=0000
STATE_CHANGE frame=45  pc=071D30 a5=00FF0000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=00CF
SAMPLE       frame=60  pc=071D30 a5=00FF0000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=00C0
SAMPLE       frame=90  pc=071D2E a5=00FF0000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=00A2
SAMPLE       frame=120 pc=071D30 a5=00FF0000 s0=0000 s2=0001 s4=0000 s12=0000 cnt=0084
```

The early no-input sequence matches the same broad title countdown state signature: `%a5@(0)=0`, `%a5@(2)=1`, `%a5@(4)=0`, `%a5@(0x12)=0`, with the countdown decreasing.

## Build 0108 Absolute A5 Base

Source: `states/traces/build_0108_high_score_attract_v2_20260627_153132/a5_base_probe.tsv`

At frame `21`, Build 0108 had active A5:

```text
A5_ACTIVE frame=21 pc=070650 a5=00FF0000
```

Literal Genesis WRAM watch addresses:

| Field | Genesis-WRAM-address |
|---|---:|
| `A5+0x00` master state | `0x00FF0000` |
| `A5+0x02` substate | `0x00FF0002` |
| `A5+0x04` phase | `0x00FF0004` |
| `A5+0x12` secondary state/timer | `0x00FF0012` |
| `A5+0x44` reference field cleared by the coin/start-path site | `0x00FF0044` |

## High-Score State Signature

Not established.

The required visual anchor was not obtained because the original arcade run did not reach the visible high-score/table screen before the local MAME capture path stalled. Therefore no frame/screenshot can be cited as the high-score-table visual proof, and no `%a5` state tuple is assigned as the high-score signature.

## Transition Writer

Not established.

Because the actual visual-anchored high-score state signature was not established, this task did not identify a valid no-input high-score transition writer. Per prompt, no no-op/suppression check was run on the discarded coin/start candidates.

## No-Op / Suppression Check

Not applicable.

The real no-input high-score transition writer was not identified, so there is no authorized site for the suppression/no-op check. Running the check on the discarded `0x3AAAC/0x3AAD2/0x3AE76` family would violate the v2 prompt.

## Classification

### D - INCONCLUSIVE

Reason: local runtime capture could not reach and visually anchor the passive no-input arcade high-score/table screen. The observed sequence so far is included above.

What is proven:

- No input was used.
- Original arcade and Build 0108 both enter the early title countdown state in the observed window.
- Build 0108 live A5 base is `Genesis-WRAM-address 0x00FF0000`.
- The previous master-state-1 candidate family remains disqualified as an assumed no-input high-score target; this pass did not observe `%a5@(0)=1` during the practical no-input watch window.

What is not proven:

- The original arcade visual high-score-table frame.
- The high-score state signature.
- The transition writer PC.
- Whether Build 0108 reaches, diverges from, or blocks that state.
- Any render/clear/commit diagnosis for the high-score screen.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: context only; not closed.
- OPEN-018/Class B: context only; not touched.
- OPEN-015: not touched.
- New issues opened: none.
- Issues closed: none.
- `KNOWN_FINDINGS.md`: no update recommended.

## STOP

STOP triggered: **YES, evidence-limited**.

The task cannot safely answer A/B/C without a visual-anchored arcade high-score frame and matching state signature. The local MAME capture path stalled before that visual state. No fix or design is proposed.
