# Cody - Complete Native Plane A Migration Only

> **HISTORICAL BUILD REPORT (banner added 2026-07-28):** This is preserved build/failure evidence. Its facts (builds, SHAs, results) are **unchanged**. The graphics architecture it describes is governed and, where it conflicts, **superseded** by the canonical `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). Read the policy before using this as an architecture reference.


**Date:** 2026-07-27
**Task type:** Focused implementation + verification
**Accepted production baseline:** Build 0235
**Build 0235 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`
**Build 0235 SHA-256:** `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`
**Rejected/preserved prior build:** Build 0239, SHA-256 `f1d6075c801f8a0326084edec79c2850decc26f8569abc2a7eb1328b8677813b`
**Candidate produced:** Build 0240
**Build 0240 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0240.bin`
**Build 0240 SHA-256:** `42be8e9ca41267606b46e3bbe0cb0a3de0d9bfcaba692d0785fa5c2c392e89a2`
**Build 0240 size:** `1588804` bytes
**Counter after build:** `240`

## Result

Build 0240 was produced mechanically and passed the canonical build gate, but it is **not validated as an accepted gameplay candidate**. A bounded scripted comparison shows Build 0240 fails to leave the Stage-1 scene-fill/setup state where Build 0235 reaches steady gameplay.

Checkpoint status: **NO**.

## Phase 0 / Baseline

- Read repository rules and architecture before implementation.
- Build 0235 ROM SHA-256 matched `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`.
- Build 0239 ROM was present and preserved with SHA-256 `f1d6075c801f8a0326084edec79c2850decc26f8569abc2a7eb1328b8677813b`.
- Production paths were restored to Build 0235 state before the Plane A-only edits.
- Counter before this task was `239`; Build 0240 consumed the next number.

## Scope Boundary

Implemented Plane A-only native ownership. Plane B production behavior was intentionally left equivalent to Build 0235:

- `_vblank_service` still calls `vdp_project_bg_tall_if_dirty`.
- `staged_bg_tall_buffer` remains present and live.
- `vdp_project_bg_tall_if_dirty` remains present and active.
- Plane B scroll still uses the Build-0235 residual `& 0x0007` in gameplay.
- No Plane B native producer rewrite was introduced in this task.

## Plane A Changes

Production files changed:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/boot/boot.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Generated/build outputs also changed as part of producing Build 0240.

### Native Plane A ownership state

Added WRAM state:

- `fg_native_owner`
- `fg_native_column_pending`
- `fg_native_column_byte`

These are cleared during bootstrap and C-window clear paths.

### Column path

`genesistan_stage_fg_src_column` now converts gameplay selector-0 Plane A cells directly into `staged_fg_buffer` resident rows instead of using `staged_fg_tall_buffer`. It computes:

- `native_y = (-a5@0x10B0 + 8) & 0x01FF`
- `logical_top = (native_y >> 3) & 0x003F`
- `delta = (logical_row - logical_top) & 0x003F`
- resident iff `delta < 32`
- physical row = `logical_row & 0x001F`

For non-scene-fill gameplay publications, it queues a bounded native Plane A column commit through `fg_native_column_pending` / `fg_native_column_byte`.

### Row path

`genesistan_stage_fg_src_row` was added for selector-1/selector-2 row publication. It preserves collision publication for all 64 logical columns/rows and stages only resident visual rows into `staged_fg_buffer`.

### FG tall projector ownership

`vdp_project_fg_tall_if_dirty` now skips projection while gameplay Plane A native ownership is active, preventing stale `staged_fg_tall_buffer` from overwriting native `staged_fg_buffer`.

### Scroll

Gameplay Plane A vertical scroll now commits full native `& 0x01FF` instead of the Build-0235 residual-only `& 0x0007`. Plane B remains residual-only.

### VBlank commit

`vdp_commit_fg_narrow_strips` first services one pending native Plane A column job using autoincrement `0x80`, then falls through to the legacy narrow-strip commit path. Existing legacy compatibility remains for frontend/text/HUD/item-page routes.

## Canonical Build Result

Build 0240 was produced by the normal Makefile.

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0240.bin`
- SHA-256: `42be8e9ca41267606b46e3bbe0cb0a3de0d9bfcaba692d0785fa5c2c392e89a2`
- Size: `1588804`
- Counter: `240`
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Rolling SHA-256 matched the numbered Build 0240 ROM.
- Build output reported `GATE_PASS`.
- Canonical opcode_replace count remained `216`.
- Canonical coverage was updated to `0x183E44` after the first build attempt reported this mechanical coverage delta.

Scene tile budget from the successful build:

- Title: `845`
- Gameplay: `962`
- End-Round: `1067`
- Gameplay-Cave: `568`
- Total unique: `3165`
- VRAM max: `1067 / 1164`
- Range overlap: PASS

## Automatic Trace

Normal Makefile automatic trace artifact:

- `states/traces/rastan_direct_video_test_build_0240_mame_30s_20260727_224317/`
- `genesis_exec_summary.txt`: `1798` frames
- no unmapped memory addresses in the MAME exit summary
- final PC: `0x072F74`
- SP: `0x00FEFF78`

This trace is no-input/frontend coverage and does not prove gameplay entry correctness.

## Scripted Gameplay Validation

Trace directory:

- `states/traces/build0240_plane_a_scripted/`

Scripts/files:

- `plane_a_validation.lua`
- `plane_a_validation_long.lua`
- `build0240_plane_a_frame_samples.csv`
- `build0240_plane_a_long_frame_samples.csv`
- `build0240_plane_a_validation_summary.txt`
- `build0240_plane_a_long_validation_summary.txt`
- `compare_0235_state.lua`
- `build0235_compare_state.csv`

The script used the existing project convention:

- `P1 A` / `Coin 1` pulse at frames 120-132
- `P1 Start` / `1 Player Start` pulse at frames 175-187
- `P1 Right` held after frame 700

### Build 0235 comparison

Build 0235 reached steady Stage-1 gameplay by frame 600:

```text
frame 600: state=0002/0003/0000 scene=6A s10aa=0000 s10a0=00C08100 s10b0=0149 bg_tall_dirty=00 fg_tall_dirty=00
frame 5000: state=0002/0003/0000 scene=6A s10aa=0000 s10a0=00C08100 s10b0=0149
```

### Build 0240 result

Build 0240 entered Stage-1 setup/fill but did not leave it by frame 5000:

```text
frame 360: state=0002/0002/0004 scene=01 s10aa=003F s10a0=00C08004 s10a4=00C08000 fg_native_owner=01 bg_tall_dirty=01
frame 5000: state=0002/0002/0004 scene=01 s10aa=003F s10a0=00C08004 s10a4=00C08000 fg_native_owner=01 bg_tall_dirty=01
```

Observed facts:

- Native Plane A owner becomes active (`fg_native_owner=01`).
- Native column pending is clear at sample points (`fg_native_pending=00`), consistent with scene-fill mode not queuing gameplay column jobs.
- Legacy FG tall dirty is suppressed (`fg_tall_dirty=00`).
- BG tall dirty remains set (`bg_tall_dirty=01`).
- The state remains `2/2/4`; Build 0235 reaches `2/3/0` under the same input script.

Interpretation:

The Build 0240 Plane A migration is live but fails the required gameplay-entry preservation test. The first measured divergence is the Stage-1 scene-fill/setup path not completing in the bounded comparison after native Plane A ownership is activated. This is sufficient to reject Build 0240 as an accepted candidate until the setup-fill path is fixed or bounded differently.

## Plane B Unchanged Proof

Source inspection and symbol output show Plane B retained Build-0235-style tall projection:

- `vdp_project_bg_tall_if_dirty` symbol exists at `0x00070138`.
- `_vblank_service` calls `vdp_project_bg_tall_if_dirty` before `vdp_commit_bg_strips_if_dirty`.
- `staged_bg_tall_buffer` symbol remains present at `0x00FF50EE`.
- `vdp_commit_scroll` still masks gameplay BG vertical scroll with `0x0007`.

## Not Accepted / Remaining Boundary

Build 0240 should not be treated as visually or gameplay accepted. It is mechanically useful evidence for the next pass, but the migration currently fails the required comparison against Build 0235.

Smallest next investigation boundary:

1. Measure the scene-fill loop around runtime PCs `0x0704B8..0x07080E` in Build 0240.
2. Determine whether the fill countdown `a5@0x10AA` remains at `0x003F` because the hook is over-budget, re-entered, or no longer advancing the original scene-fill loop.
3. Compare the same loop in Build 0235 at frames 360-600.
4. Only then decide whether selector-0 scene-fill needs a cheaper bulk/fill path, a one-time ownership transition, or narrower state gating.

## Architecture Compliance

Confirmed with caveat: the implementation keeps arcade code as the program and routes rendering through staging and VBlank commit. However, the validation failure means the current implementation is not accepted as a correct migration.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 / PC080SN native rendering context.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: Plane B native migration, rope/collision, PC090OJ, palette, score/HUD.

## KNOWN_FINDINGS Impact

Option A: no new finding to index yet. This is a failed implementation checkpoint rather than a durable system behavior finding.

## STOP Status

STOP triggered for acceptance: YES. Build 0240 was produced, but scripted validation failed versus Build 0235. No further speculative implementation was performed.
