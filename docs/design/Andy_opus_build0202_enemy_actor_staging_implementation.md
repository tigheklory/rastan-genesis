# Andy/Opus — Build 0202 Enemy Actor Staging Implementation (Attempted, STOP — No Build)

**Date:** 2026-07-17
**Type:** Bounded implementation attempt in pc090oj_hooks.s + empirical bisect. **Reverted; no build shipped.**
**Baseline:** Build 0200/256 `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663`; comparison Build 0201/192 `7c89e96ddbb5070c4b6bf45aaca80d639e2ea6127514fe5c06c3c4cc0cf238b5`.
**Repo end-state:** counter 201, rolling dist restored to Build 0200/256, config 256, Makefile default 256, opcode_replace 214, coverage invariant 0x18271C. No Build 0202/0203. Source (pc090oj_hooks.s) and gate scripts reverted to Build 0200 state.

## What was implemented (and why it was reverted)
A faithful Genesis-side reimplementation of the arcade enemy writers 0x41DAE/0x45DFA was written in pc090oj_hooks.s (KF-060):
- A fixed 256-record (2048-byte) `pc090oj_actor_scratch` buffer (independent of the mirror cap so the 192 build cannot overflow).
- `pc090oj_stage_actor_41dae` / `pc090oj_stage_actor_45dfa`: reproduce the arcade block iteration exactly (blocks A5+0x508/0x5C8/0x2C8/0x748/0x8C8, counts 2/6/9/11/5, per-entry d2 budgets, active-flag and index-dependent d2 special cases, blank fill) into scratch.
- Active entries invoke the relocated arcade actor→sprite engine `0x0003D254` (writes records via `a1@+`); touched records are then copied to the mirror via `.Lpc090oj_family_apply_record` (OOB-guarded vs PC090OJ_MIRROR_RECORDS, candidate/dirty marking, Build 0193 fast path).
- The hooks call the new helpers instead of the old wrong player-block copy; the Build 0192 gameplay-skip is removed because the duplicate-Rastan copy is no longer performed.

It built GATE_PASS (256, source-only; opcode_replace count unchanged 214; coverage invariant +0x2A4). But runtime validation revealed a **severe regression** and the change was reverted.

## Empirical result (MAME, Build 0202 candidate vs Build 0200)
Identical input script (walk right F700-1000, jump F1050):

| Frame | Build 0200 (good) | Build 0202 engine-enabled | Build 0202 engine-DISABLED (bisect) |
|---|---|---|---|
| 690 | mode 0, pX 0x20, sX 0 | **mode 3, pX 0x20, sX 0** | mode 0, pX 0x20, sX 0 |
| 850 | mode 1, pX 0xA0, sX 0x1E6 | **mode 3, pX 0x20, sX 0** | mode 1, pX 0x89, sX 0 |
| 1000 | mode 1, sX 0x189 | **mode 3, pX 0x20, sX 0** | mode 1, pX 0xA0, sX 0x1CA |
| 1080 | mode 2 (jump) | **mode 3, pX 0x20, sX 0** | mode 2 (jump) |

**Engine-enabled Build 0202: the player is stuck in mode 3 (fall) from gameplay start, never gains control, never scrolls — the game is broken.**

## Bisect — root of the regression
Disabling only the `jsr 0x0003D254` engine call (blank-fill instead) while keeping the entire staging framework (scratch clear, block iteration, A5+0x214 counter usage, ~150-record flush via family_apply_record) **fully restores Build 0200 control** (mode 0→1→2, player walks, camera scrolls). Therefore:

- The staging framework (scratch buffer, block loops, candidate/dirty flush, hook rewiring, Build 0192 preservation) is **safe** — no regression, player records intact (record 120 real), represented count 18.
- **Calling the arcade actor→sprite expansion engine 0x3D254 from the hook is UNSAFE** — it corrupts player/collision state (mode locks at 3, fall never resolves).

## Why the engine call corrupts (and why enemies still don't appear)
The engine dispatches on and indexes ROM sprite-layout tables by the actor's fields (a4@(1) code, a4@(56) type). At the matched Genesis gameplay window the enemy actor blocks are **not populated with valid enemy structs** (records 46/57/96/140 blank-fill to `[0000 0180 0000 0000]`, no code!=0 in the enemy record range). Feeding the engine the Genesis actor blocks — whose "active-looking" entries carry code 0 / uninitialized dispatch fields — makes it index its tables with invalid data and touch shared/player-relevant WRAM (or take a wild dispatch), corrupting the fall/collision state. The blank-only variant produces **zero enemies** (nothing to stage), so it is no improvement over Build 0200.

This confirms the record-46 provenance pass's remaining unknown: **the true first divergence for enemies is upstream — the enemy-logic that populates the actor staging blocks (A5+0x508/0x5C8/0x2C8/0x748/0x8C8) does not run / does not produce valid actors on Genesis at the matched point.** The staging routine (this task) is necessary but not sufficient, and the expansion engine cannot be safely driven until it is fed valid actor data.

## Build decision — STOP, NO BUILD
- Engine call from hook: **proven unsafe** (regression bisected).
- Bounded clone of the expansion engine: **out of scope** — 0x3D254 → 0x3CB02 is a full multi-case Taito sprite-composition engine (9+ layout cases, sub-engines 0x4790E/0x3F2BC/0x401DC/0x401F0, coordinate transforms, ROM layout tables); a faithful clone is hundreds of instructions with high risk and could not be validated without valid actor data.
- Blank-only staging: **safe but useless** (zero enemies).

Per the task gate ("If neither [safe engine call nor bounded clone] is safe, STOP with evidence and no build"), no build was produced. Build 0200 remains the rolling candidate.

## Exact blocker / next step
The enemy fix requires, in order:
1. **Resolve upstream actor-block population** — find the arcade routine that fills A5+0x748 (and 0x508/0x5C8/0x2C8/0x8C8) with valid enemy actor structs at the matched point, and determine why the Genesis equivalent does not (spawn/progression/camera trigger, a NOPped enemy-logic routine, or a raw-WRAM-literal in the enemy update path). This needs the arcade romset for a live write-watch on A5+0x748 (0x10C748) vs Genesis 0xFF0748.
2. Only once valid actor structs exist can the staging helper (proven-safe framework from this task) drive the expansion — and even then the engine must be invoked on validated actors, or the expansion cloned for the specific record-46/57/96/140 sprite codes.

## Not regressed
Repo fully reverted to Build 0200: control/jump/attack/scroll/player-completeness/palette all intact (rolling SHA re-verified `bdba9bab`). No spec/opcode/mirror-size change persisted.
