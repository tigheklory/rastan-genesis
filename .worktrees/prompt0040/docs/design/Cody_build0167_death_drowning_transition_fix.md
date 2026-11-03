# Cody - Build 0167 Death/Drowning Transition Fix Attempt

**Date:** 2026-07-13
**Type:** Issue-ledger update + analysis-first runtime/static evidence. No implementation.
**Baseline build:** Build 0166, `dist/rastan-direct/rastan_direct_video_test_build_0166.bin`
**Baseline SHA256:** `a74365146eef4fdf0e9b429d7e66d63186023e3541f36fc1fa9b2703eed62ff5`
**Scope:** Update the missing Build 0166 issue ledger, then inspect only the first death/drowning transition and immediate hardware-lock context. No source/spec/tool/Makefile/ROM edits. No build.

## Phase 0

Classification: **EXTENDING**. This continues OPEN-017 gameplay-entry/death/collision work after Build 0166's bounded vertical-scroll fix.

Relevant priors loaded:

- KF-010: BG/FG staging and VDP plane mapping.
- KF-011: arcade VBlank owns gameplay progression; Genesis VBlank is service/commit.
- KF-015: PC080SN vertical scroll conversion is `-raw + 8`, verified by Build 0166.
- KF-026: PC090OJ write surfaces are not fully statically enumerable.
- KF-032: copied arcade hardware writes must be routed through staging.
- KF-036/KF-039 class: arcade work-RAM literals require disciplined mapped-base handling.
- KF-042: data-register literal relocation misses can alter pass selection.
- KF-044: raw arcade-WRAM immediate destination literals require targeted proof; systemic rebases can regress control flow.

Rediscovery Hazard HIGH findings touched: KF-011, KF-015, KF-036/KF-039, KF-044. No contradiction detected.

Relevant open issues: OPEN-017 primary; OPEN-024 context for sprites/header/flicker only. OPEN-018/019/020/021 and D00298 were intentionally not pursued.

Closed issues touched: none.

## Issue Ledger Update

`OPEN_ISSUES.md` was updated before analysis with a new OPEN-017 addendum for Build 0166 real-hardware observations:

- Build 0166 fixed vertical scroll direction per Tighe, but real Genesis locks at the first visible drowning-animation frame.
- Build 0165 also locked on real Genesis earlier, before the visible burning/death animation.
- The earlier `lava/fire` wording is refined: after Build 0166, the visible death appears to be water/drowning, not a proven fire/lava surface.
- The addendum keeps BG/FG composition, ground tiles, FG palette, READY flicker/header sprites, VBlank/slowdown, input, continue/game-over, D00298, Exodus pre-gameplay loop, and records `132..134` as separate deferred observations unless directly causal.

No issue was opened or closed.

## Evidence Artifacts

Trace directory:

- `states/traces/build0167_death_drowning_transition_20260713_232205/`

Primary files:

- `arcade_death_trace.csv`
- `arcade_death_events.log`
- `genesis_death_trace.csv`
- `genesis_death_events.log`
- `genesis_death_snapshot.txt`
- `arcade_pc_boundary_events.log`
- `genesis_pc_boundary_events.log`
- `reduced_summary.md`

Both MAME runs exited `0`. MAME did **not** reproduce the real Genesis hardware lock.

Important trace limitation: the headless Lua binding used here did not expose/accept `install_execute_tap`; PC boundary installs recorded `ok=false`. Read/write taps also did not capture the exact current collision read/mode write despite state changes being observed. Therefore this task separates:

- current Build 0166 runtime state timeline: **observed**;
- exact collision/death PC mechanism: **static Build 0166 verification plus prior Build 0159 proven mechanism, unchanged**.

## Current Runtime Timeline

### Arcade Reference

Scripted route: coin around frame 120, 1P start around frame 175.

Observed arcade `rastan` timeline:

- Frame 307: enters gameplay state `2/3/0`.
- Frame 820: still `2/3/0`, player `X=0x0020`, `Y=0x0070`, mode `0x0000`, flags `0x0004`, camY `0x0149`.
- Frame 895: enters death/respawn state `2/4/0` with mode `0x0008`.

### Genesis Build 0166

Observed Build 0166 timeline:

- Frame 534: enters gameplay state `2/3/0`.
- Frame 620: player `X=0x0020`, `Y=0x0070`, mode `0x0003`, camY/staged scroll `0x01E0`.
- Frame 700: still mode `0x0003`, camY `0x0183`, staged scroll `0x0187`.
- Frame 760: still state `2/3/0`, but mode has become `0x0008`, flags `0x0200`, camY `0x013F`, staged scroll `0x0143`.
- Frame 900: still state `2/3/0` with mode `0x0008`.

First current-runtime divergence: Build 0166 reaches player mode `0x0008` during active gameplay far earlier than arcade. Arcade is still normal gameplay at frame 820 and only reaches its death/respawn state at frame 895.

## Static Build 0166 Boundary Verification

Build 0166 still contains the same collision-map reader/death-handler structure documented in the Build 0159 collision analyses.

ROM byte verification from `dist/rastan-direct/rastan_direct_video_test_build_0166.bin`:

- `runtime_genesis_pc 0x053C64`: bytes `207c0010de00`, instruction `movea.l #0x0010DE00,%a0`.
- `runtime_genesis_pc 0x05400C`: bytes `3b7c000810e8`, instruction `move.w #0x0008,%a5@(0x10E8)`.
- `runtime_genesis_pc 0x051B98`: bytes begin `426d0004...`, stage-controller transition code remains present.

Address-map-derived correlations from `build/rastan-direct/address_map.json`:

- `runtime_genesis_pc 0x053C2E -> arcade_pc 0x053A2E` (`arcade_copy`).
- `runtime_genesis_pc 0x053C64 -> arcade_pc 0x053A64` (`arcade_copy`).
- `runtime_genesis_pc 0x053FA6 -> arcade_pc 0x053DA6` (`arcade_copy`).
- `runtime_genesis_pc 0x054000 -> arcade_pc 0x053E00` (`arcade_copy`).
- `runtime_genesis_pc 0x05400C -> arcade_pc 0x053E0C` (`arcade_copy`).
- `runtime_genesis_pc 0x051B98 -> arcade_pc 0x051998` (`arcade_copy`).

Per prior proven Build 0159 analysis, the unchanged mechanism is:

1. Collision lookup uses `A0 = 0x0010DE00 + index`.
2. On arcade, `0x0010DE00` is work RAM containing the collision map.
3. On Genesis, `0x0010DE00` is not mapped Genesis WRAM and remains a raw arcade-WRAM literal.
4. The dispatch around `runtime_genesis_pc 0x053FA6` checks `*(A0) & 0x7F`.
5. Type `8` branches to the handler at `runtime_genesis_pc 0x054000`; `runtime_genesis_pc 0x05400C` writes mode `0x0008`.

Current Build 0166 did not change those bytes or the collision-map ownership model.

## Hardware-Lock Context

MAME did not reproduce the real Genesis lock. The real-hardware lock is therefore recorded as **user-observed** only in this task.

Genesis snapshot at frame 720, before the sampled mode-8 state:

- State `2/3/0`, player `X=0x0020`, `Y=0x0070`, mode `0x0003`.
- `pc090oj_tile_dma_count = 0x0012`.
- `pc090oj_represented_count = 0x0018`.
- `staged_sprite_active_count = 0x0018`.
- Player-cluster records 120..131 are populated and staged.
- Records 132..134 contain suspicious non-player-looking values, but this task did not prove them causal and the prompt explicitly deferred them unless directly tied to the first death/hardware lock.

No invalid VDP/DMA write was captured in MAME after the sampled transition. Because the real Genesis lock was not reproduced, no source-line hardware-lock fix is bounded here.

## Classification

Death/drowning transition classification: **A - wrong collision/surface value class**, with an evidence caveat.

- Observed current Build 0166 behavior: player mode becomes `0x0008` far earlier than arcade.
- Static current Build 0166 proof: the collision base literal and mode-8 writer remain the same as the already-proven collision-map mechanism.
- Caveat: this run did not freshly capture the exact current `*(A0)&0x7F` value or PC due MAME tap limitations. The exact surface value is therefore not newly proven in this task; it is carried from prior Build 0159 evidence and static unchanged-code verification.

Hardware-lock classification: **G - more evidence needed**.

- Real Genesis lock is user-observed at the first drowning frame.
- MAME did not reproduce the lock.
- No invalid VDP/DMA anomaly was captured.
- No bounded hardware-lock source line is proven.

## State-Causality Answers

1. **What state should exist?** The collision lookup should read a produced collision map in arcade work RAM semantics. On Genesis, the mapped equivalent would need a populated collision map at the correct Genesis WRAM location, not raw ROM/VDP/unmapped space.
2. **Which earlier code creates it?** Prior Build 0159 analysis tied collision-map population to the PC080SN tilemap/collision producer path; that path remains unresolved/deferred.
3. **Why did the state not get created?** Prior evidence shows the Genesis collision-map producer/reader ownership is incomplete: raw `0x0010DE00` collision-map literals remain, and simple literal rebasing was previously rejected as unsafe because the target buffer was empty until producer ownership is fixed.

## Fix Decision

No Build 0167 was produced.

Reason: the logical death/drowning transition points back to the known collision-map production/rebase boundary, not to a small death-handler or animation fix. Patching `runtime_genesis_pc 0x05400C`, forcing mode, forcing safe ground, disabling death/drowning, or hardcoding invulnerability would violate state causality and the task guardrails.

Smallest safe next boundary:

- A dedicated collision-map producer/rebase design pass, starting from the Build 0159 collision producer findings, or
- A debugger-side current Build 0166 trace that captures the exact `runtime_genesis_pc 0x053FA6` / `0x05400C` collision read and mode write if the team wants fresh same-build proof before reopening the collision-map implementation boundary.

The real Genesis hardware lock needs a separate proof if it persists after the collision/surface transition is corrected, or a hardware-side trace that captures the lock-causing VDP/DMA/SAT condition exactly at the drowning frame.

## Open / Closed Issues Impact

Open issues touched:

- OPEN-017: updated with missing Build 0166 issue ledger and advanced with current death-transition evidence.
- OPEN-024: context only for sprite/header/records observations; not edited in this task.

New issues opened: none.

Issues closed: none.

Issues intentionally deferred: BG/FG composition, missing ground tiles, FG palette, READY/header flicker, VBlank budget/rolling bar, input/control, continue/game-over, D00298, Exodus pre-gameplay loop, suspicious records 132..134, and broader collision-map implementation.

## KNOWN_FINDINGS Impact

Option A - no new finding to index.

Rationale: this task records Build 0166 observations and confirms the live symptom still aligns with the existing collision-map/raw-WRAM-literal class. It does not prove a new durable mechanism beyond prior Build 0159/KF-036/KF-039/KF-044 context.

## Architecture Compliance

CONFIRMED.

No source/spec/tool/Makefile/ROM/invariant changes were made. No build was produced. The arcade code remains the program; Genesis-side code was not modified. No bypass, no forced safe state, no hardcoded invulnerability, no hardcoded animation, no second renderer, no VDP rewrite.

## STOP

STOP triggered: **YES**.

Reason: no bounded implementation was proven. Current evidence identifies the first divergence as the early mode-8 death/drowning transition, but the safe fix boundary is the broader collision-map producer/rebase problem, not an isolated death-handler patch.
