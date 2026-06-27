# Cody - High Score State Entry Evidence: Original Arcade vs Build 0108

**Date:** 2026-06-27  
**Type:** Runtime evidence / analysis only  
**Build:** 0108  
**Build ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0108.bin`  
**Build SHA256:** `bd0c7faa187f6d9aded904638e8d7cb8c9e3df6304c5178a36ec02e6c8bbad09`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/bookmark changes. No implementation. No fix design.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded from `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `AGENTS_LOG.md`, and the required design docs:

- `docs/design/Andy_class_b_parens_taito_coverage_design.md`
- `docs/design/Cody_class_b_taito_0x563ce_runtime_evidence.md`
- `docs/design/Andy_build_0107_validation_and_class_b_remaining_status.md`

No contradiction of a CONFIRMED/STRONG prior was identified. OPEN-001 remains the active visual-output context. OPEN-018/Class B context was respected but not re-derived. OPEN-015 was not touched.

## Address Mapping Discipline

All arcade-to-Genesis code correlations below were checked against `build/rastan-direct/address_map.json`; no arithmetic offset is used as proof.

| Arcade PC | Build 0108 runtime Genesis PC | Map segment kind | Note |
|---|---:|---|---|
| `arcade_pc 0x0003A8AC` | `runtime_genesis_pc 0x0003AAAC` | `arcade_copy` | master-state-1 handler entry |
| `arcade_pc 0x0003A8D2` | `runtime_genesis_pc 0x0003AAD2` | `arcade_copy` | state-1 substate-0 producer body |
| `arcade_pc 0x0003A912` | `runtime_genesis_pc 0x0003AB12` | `arcade_copy` | state-1 substate advance to `%a5@(2)=1` |
| `arcade_pc 0x0003A91A` | `runtime_genesis_pc 0x0003AB1A` | `patched_site` | input read patched from `0x390007` to `0xff60ff` |
| `arcade_pc 0x0003A9DE` | `runtime_genesis_pc 0x0003ABDE` | `arcade_copy` | state-1 route to master state 2 |
| `arcade_pc 0x0003AC76` | `runtime_genesis_pc 0x0003AE76` | `arcade_copy` | candidate route to master state 1 |
| `arcade_pc 0x0003AE76` | `runtime_genesis_pc 0x0003B076` | `arcade_copy` | alternate candidate route to master state 1 |

## Evidence Artifacts

Primary runtime attempts created under:

- `states/traces/original_arcade_high_score_state_entry_20260627_144044/`
- `states/traces/original_arcade_high_score_state_entry_20260627_144044_eventonly/`
- `states/traces/original_arcade_high_score_state_entry_20260627_144044_dump/`
- `states/traces/build_0108_high_score_state_entry_20260627_144044/`
- `states/traces/build_0108_high_score_state_entry_20260627_144044_eventonly/`
- `states/traces/build_0108_high_score_state_entry_20260627_144044_dump/`
- `states/traces/build_0108_high_score_state1_direct_20260627_144044/`

Most useful reduced logs:

- `states/traces/original_arcade_high_score_state_entry_20260627_144044/events.log`
- `states/traces/original_arcade_high_score_state_entry_20260627_144044_dump/lua_state_only.log`
- `states/traces/build_0108_high_score_state_entry_20260627_144044_dump/lua_state_only.log`

## Runtime Results

### Original arcade bounded state-only observation

The original arcade Lua observer reached only the early title countdown window before the run ended/interrupted:

```text
START target=original_arcade_rastan rom=rastan
FRAME 0001 pc=03AEC6 STATE_CHANGE s0=0000 s2=0000 s4=0000 s12=0000 cnt=0000
FRAME 0014 pc=03B08E STATE_CHANGE s0=0000 s2=0001 s4=0000 s12=0000 cnt=00D0
...
FRAME 0139 pc=039FAA STATE_CHANGE s0=0000 s2=0001 s4=0000 s12=0000 cnt=0053
```

A prior full-instruction debugger run produced `states/traces/original_arcade_high_score_state_entry_20260627_144044/events.log`, but it also only reached early title/state-2 setup before it was stopped. It did not reach `arcade_pc 0x0003A8AC` or `arcade_pc 0x0003A8D2`.

### Build 0108 bounded state-only observation

The Build 0108 Lua observer likewise reached only the early title countdown window:

```text
START target=build_0108 rom=genesis
FRAME 0001 pc=000308 STATE_CHANGE s0=0000 s2=0000 s4=0000 s12=0000 cnt=0000
FRAME 0040 pc=07016A STATE_CHANGE s0=0000 s2=0000 s4=0001 s12=0000 cnt=0000
FRAME 0045 pc=071D30 STATE_CHANGE s0=0000 s2=0001 s4=0000 s12=0000 cnt=00CF
...
FRAME 0129 pc=071D2E STATE_CHANGE s0=0000 s2=0001 s4=0000 s12=0000 cnt=007B
```

A direct Build 0108 debugger breakpoint at `runtime_genesis_pc 0x0003AAD2` did **not** hit within the practical run window and produced no state dump:

- Script: `states/traces/build_0108_high_score_state1_direct_20260627_144044/mame_build0108_state1_direct.cmd`
- Expected dump if hit: `build0108_state1_sub0_hit_state.bin`
- Result: dump absent; process stopped manually after no hit.

This is **not** evidence that Build 0108 cannot reach the state. It is only evidence that this bounded capture did not reach it.

## Static Cross-Check

The high-score/interstitial candidate handler is structurally present in Build 0108 at the JSON-mapped runtime PCs:

- `runtime_genesis_pc 0x0003AAAC` mirrors `arcade_pc 0x0003A8AC` as the master-state-1 handler entry.
- `runtime_genesis_pc 0x0003AAD2` mirrors `arcade_pc 0x0003A8D2` as the substate-0 producer region.
- The route contains the same state-1 substate progression structure: producer, then `%a5@(2)=1` at `runtime_genesis_pc 0x0003AB12`, then input/high-score path at `runtime_genesis_pc 0x0003AB1A`.

Static presence does **not** prove runtime entry.

## Classification

### D - INCONCLUSIVE

The task question was: does Build 0108 enter the same high-score/interstitial attract-loop state as original arcade?

This evidence pass did **not** produce a decisive runtime comparison. The bounded original-arcade and Build 0108 captures both stopped/ended during the early title countdown (`%a5@(0)=0`, `%a5@(2)=1`, `%a5@(4)=0`, counter decrementing). Neither capture reached master state `1` (`%a5@(0)=1`) or the state-1 producer breakpoint.

Therefore:

- **STATE ENTRY BLOCKED (A):** not proven.
- **WRONG STATE / WRONG ROUTE (B):** not proven.
- **STATE ENTRY OK, RENDER/CLEAR BROKEN (C):** not proven for Build 0108 by this task.
- **INCONCLUSIVE (D):** proven as the correct classification for this evidence pass.

## Secondary Render/Clear Notes

Because state entry was not proven for Build 0108 in this pass, the requested secondary render/clear classification is intentionally limited:

- No Build 0108 state-1 render/clear event was captured.
- No Build 0108 state-1 sprite producer/clear event was captured.
- No Build 0108 state-1 palette/page timing event was captured.
- No Build 0108 state-1 VBlank commit event was captured.

Existing user-observed symptoms remain valid context only: the high-score/interstitial screen does not display, the screen is not fully cleared during attract transition, a yellow stale area appears between Rastan's legs when the high-score screen should appear, and a lone unexpected sprite appears in Exodus. This task did not localize those symptoms.

## Recommended Next Evidence Step

A decisive follow-up should avoid long Qt-debugger windows and use a purpose-built MAME Lua observer that runs to the full attract-loop duration and logs only coarse state changes, or a debugger breakpoint known to hit after fast-forwarding to the relevant attract phase. The key proof remains:

- original arcade: first frame/cycle where `%a5@(0)=1` and `arcade_pc 0x0003A8AC/0x0003A8D2` executes;
- Build 0108: first frame/cycle where `%a5@(0)=1` and `runtime_genesis_pc 0x0003AAAC/0x0003AAD2` executes;
- if Build 0108 reaches that state, capture staging/clear/sprite evidence immediately there.

No fix should be inferred from this pass.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: context only; not closed.
- OPEN-018/Class B: context only; not re-derived.
- OPEN-015: not touched.
- New issues opened: none.
- Issues closed: none.
- `KNOWN_FINDINGS.md`: no update recommended; no durable mechanism was proven.

## STOP

STOP triggered: **NO** for scope compliance.  
Evidence classification: **D - INCONCLUSIVE** because the runtime capture did not reach the target state.
