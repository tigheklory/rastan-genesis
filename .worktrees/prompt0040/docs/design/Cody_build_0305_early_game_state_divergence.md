# Cody Build 0305 Early-Game State Divergence

## Scope and Baselines

This report continues the Build 0304 directional-isolation result recorded in
`AGENTS_LOG.md`: Build 0304 restored the original directional dispatcher call but retained
the early Stage-1 false-collision/world mismatch. The active scope is only that early
regression. Later gameplay, castle behavior, and deferred visual issues were not examined.

Compared artifacts:

| Build | SHA-256 | Role |
|---|---|---|
| 0302 | `990644b2bb2fadefdc20cd03322294caf438754d9b2fd11abdd7666ec12768e6` | playable comparison baseline |
| 0304 | `adeea49a86611ec6b58cfdc1bfe85b76ed3bf75e1761417b9cb8bf6e3284bce7` | directional-dispatch isolation |
| 0305 | `e36f8d370e27613e85e378164774e8db0ee3199ca1fa5b1d779fa0e24165e177` | WRAM scratch-overlap correction; still reproduces 0304 state |

The deterministic harness is
`states/traces/build0305_early_game_state_diff/early_state_diff.lua`. It applies the same
coin/start/right/jump sequence and records an external MAME frame number, retained arcade
state, package state, staged-plane hashes, and the complete Genesis collision-ring hash.
The matched 1,800-frame CSVs are in that directory.

## Proven First Divergence

At frame 309 all three observed representations still match:

| State | Build 0302 | Build 0304 | Build 0305 |
|---|---:|---:|---:|
| Stage-1 record (`a5+0x013E`) | `0x0000` | `0x0000` | `0x0000` |
| Plane B hash | `D2063DC5` | `D2063DC5` | `D2063DC5` |
| Plane A hash | `B5DDACDE` | `B5DDACDE` | `B5DDACDE` |
| collision-ring hash | `76EFDDC5` | `76EFDDC5` | `76EFDDC5` |

The first differing sampled event is frame 310, while the current record remains zero and
before any package boundary:

| State | Build 0302 | Build 0304 | Build 0305 |
|---|---:|---:|---:|
| record / player mode | `0 / 0` | `0 / 0` | `0 / 0` |
| player world X/Y | `0 / 0` | `0 / 0` | `0 / 0` |
| origin X/Y | `0 / 0` | `0 / 0` | `0 / 0` |
| BG/FG X scroll | `0 / 0` | `0 / 0` | `0 / 0` |
| BG/FG Y scroll | `0 / 0` | `0 / 0` | `0 / 0` |
| Plane B hash | `D2063DC5` | `D2063DC5` | `D2063DC5` |
| Plane A hash | `6A561F2A` | `2E32164A` | `2E32164A` |
| collision-ring hash | `8F62BDC5` | `AD36E205` | `AD36E205` |

No player collision query exists at this point: the player record and coordinates are still
zero, and the harness reports zero collision reads. Therefore an exact queried ring address
and result are **not applicable at the first divergence**. Inventing a consumer query here
would misclassify an earlier producer divergence.

The collision writer trace proves the producer difference:

- Both builds first clear all 4,096 words of the collision ring at
  `runtime_genesis_pc 0x0003B102`.
- Both have the same initial descriptor words (`0x0003`) and source pointer
  `runtime_data 0x0003971C`.
- Build 0302 writes `Genesis-WRAM 0x00FF10A8 = 0x0000`; its first nonzero collision
  writer is the selector-0 column producer at `runtime_genesis_pc 0x000704F6`, writing
  `0x00FF1E00`, `0x00FF1E80`, `0x00FF1F00`, `0x00FF1F80`, ...
- Builds 0304 and 0305 write `Genesis-WRAM 0x00FF10A8 = 0x0095`; their first nonzero
  writer is the row producer at `runtime_genesis_pc 0x0007063C`, writing
  `0x00FF1F80`, `0x00FF1F82`, `0x00FF1F84`, ...

Thus collision data and Plane A diverge together at the first sampled publication. Plane B
is still identical at frame 310 and diverges shortly afterward. The displayed world does
not diverge before the collision producer.

## Root Cause

The retained arcade descriptor-rebuild helper at `runtime_genesis_pc 0x00072288`
(`genesistan_hook_pc080sn_descriptor_rebuild`) performs:

```asm
movea.l (0x10c6,a5),a4
clr.w   d0
move.b  (a4),d0
move.w  d0,$ff10a8
```

The state-causality questions resolve as follows:

1. **Required state:** the initial Stage-1 pass selector at
   `Genesis-WRAM 0x00FF10A8` must be `0x0000`.
2. **State owner:** the pass-sequence pointer loaded at `arcade_pc 0x000503CE` supplies
   the descriptor-rebuild source byte. The authoritative table begins at
   `arcade_rom/data 0x00050F6B` and its first selector byte is zero.
3. **Why it was not created:** Build 0303 inserted six bytes at
   `arcade_pc 0x00050482` for the post-reseed hook. That point precedes the pass table,
   but the explicit data-register immediate retained its previous Build 0159 relocation
   `runtime_data 0x0005116B`. Exact current `address_map.json` mapping places the table at
   `runtime_data 0x00051171`. In Builds 0304/0305, ROM byte `0x5116B` is `0x95`, while
   ROM byte `0x51171` is `0x00`.

The first divergence is therefore a missed shift-table relocation of a **data immediate**,
not a directional-dispatch error, package-allocation error, collision-consumer error, or
collision classification error.

## WRAM Ownership Audit

Build 0303 had introduced two temporary package-install arrays after the boundary counters:

| Range before Build 0305 | Purpose | Size |
|---|---|---:|
| `Genesis-WRAM 0x00FF61CC..0x00FFB1CB` | active code-to-slot LUT | 20,480 bytes |
| `Genesis-WRAM 0x00FFB206..0x00FFB985` | temporary slot translation | 1,920 bytes |
| `Genesis-WRAM 0x00FFB986..0x00FFCEAD` | temporary identity-to-slot map | 5,416 bytes |
| from `Genesis-WRAM 0x00FFCEB0` | staged SAT and later native state | downstream BSS |

The identity map crossed retained arcade state such as `A5+0xC242` at
`Genesis-WRAM 0x00FFC242`. This was a real ownership defect. It did **not** overlap the
collision ring (`Genesis-WRAM 0x00FF1E00..0x00FF3DFF`), and no out-of-bounds loop was
found: the loops remain bounded to 960 slots, 2,708 identities, and 2,048 plane words.

Build 0305 removed the two dedicated scratch allocations and reuses the active LUT during
the display-off package installation. The identity map starts at the LUT base and the slot
translation starts after 2,708 words; together they consume 3,668 of the LUT's 10,240
words. The permanent counters now end at `Genesis-WRAM 0x00FFB204`, staged SAT starts at
`Genesis-WRAM 0x00FFB208`, and the audited native BSS ends below
`Genesis-WRAM 0x00FFC242`.

This correction is retained as a valid safety fix, but deterministic Build 0305 hashes and
state remain identical to bad Build 0304 through the false-wall state. It is not the cause
of this regression.

## Post-Reseed Hook and Initial Package

The post-reseed call at exact mapped `runtime_genesis_pc 0x00050682` is reached after the
initial collision divergence. It enters `fg_boundary_install_post_reseed` with pending zero
and returns without installing a package. There is no unexpected initial install and it is
not causal.

The replacement uses `tst.b` on the pending byte, so the original caller-visible CCR
contract of the replaced `rts` is not preserved. That is a separate contract concern, but
cannot cause frame-310 state because execution reaches it later.

The initial package is semantic record 0 / variant 0. The generated package model preserves
Build 0302's semantic source membership while assigning canonical stable slots: 23 records,
170 packages, 2,708 exact pattern identities, and 1,354 legal transition edges. Record 0
variant 0 contains 49 Plane-A and 771 Plane-B identities (820 total) with zero drops. No
old-to-new package transition has occurred at the first divergence, so package remapping is
not its cause.

## Exact Correction and Validation

The causal correction is staged in `specs/rastan_direct_remap.json`:

```text
arcade_pc:        0x0503CE
original bytes:  203C00050F6B
old replacement: 203C0005116B
new replacement: 203C00051171
```

Only the `move.l #immediate,d0` data address changes. This does not force selector zero,
modify collision values, patch a collision consumer, change package allocation, restore
per-frame residency, or use a NOP/RTS bypass.

Because Build 0305 had already been consumed, the exact six-byte-immediate correction was
validated without creating or overwriting a numbered artifact. A copy of Build 0305 at
`/tmp/rastan_build0305_pointer51171_probe.bin` was changed only at the immediate operand.
Its SHA-256 is
`af41e1890a66a6294c6f340a3492b853545a0f6727281984c553e6738fa1f881`.

The diagnostic probe restores the decisive Build 0302 observations:

| Frame | Build 0302 | Build 0304/0305 | corrected probe |
|---|---|---|---|
| 310 collision / Plane A | `8F62BDC5 / 6A561F2A` | `AD36E205 / 2E32164A` | `8F62BDC5 / 6A561F2A` |
| 379 collision | `2B745D65` | `F4324C65` | `2B745D65` |
| 800 player Y / collision | `0x0070 / 961C0BC5` | `0x00ED / F4324C65` | `0x0070 / 961C0BC5` |
| 1200 record | `2` | `1` | `2` |
| 1800 record/mode | `3 / 4` | `1 / 1` | `3 / 4` |

The probe removes the early false-wall/stuck progression and preserves the canonical
pattern identity, stable-slot allocator, and boundary name-table coherence architecture.
Later hash differences reflect timing/package state and were not used as evidence of exact
whole-run identity.

## Build and Test Status

- Build 0305 exists at
  `dist/rastan-direct/rastan_direct_video_test_build_0305.bin`.
- SHA-256:
  `e36f8d370e27613e85e378164774e8db0ee3199ca1fa5b1d779fa0e24165e177`.
- Size: 3,022,520 bytes.
- Counter: 305.
- Canonical gate: PASS.
- Mandatory MAME smoke:
  `states/traces/rastan_direct_video_test_build_0305_mame_30s_20260822_094243`,
  1,798 frames, average 494.58%, no unique unmapped address/fatal/error.
- Build 0305 contains the WRAM scratch correction but **does not contain** the subsequently
  proven pass-table pointer correction. It is not ready for Tighe's early-stage acceptance
  test.
- Additional numbered builds: NONE. No numbered artifact was deleted or overwritten.
- The next authorized numbered build must materialize the already-staged
  `runtime_data 0x00051171` correction; this task did not authorize or produce it.

## Preserved Evidence

- `states/traces/build0305_early_game_state_diff/build0302_frames_1800.csv`
- `states/traces/build0305_early_game_state_diff/build0304_frames_1800.csv`
- `states/traces/build0305_early_game_state_diff/build0305_frames_1800.csv`
- `states/traces/build0305_early_game_state_diff/build0302_collision_events.log`
- `states/traces/build0305_early_game_state_diff/build0305_collision_events.log`
- `states/traces/build0305_early_game_state_diff/pointer51171_probe/buildprobe_frames.csv`

## Required Classification Summary

- Collision data itself diverges: **YES**.
- Collision query coordinates diverge at the first event: **NO / not yet applicable**.
- Collision result diverges at the first event: **NO / no player query yet**.
- Graphics/world representation diverges first: **NO**; Plane A and collision production
  diverge together, while Plane B remains identical at frame 310.
- Directional dispatcher is the early regression cause: **NO**.
- Collision code modified: **NO**.
- Per-frame residency: **NONE**.

