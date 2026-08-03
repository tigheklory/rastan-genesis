# Cody Build 0251 Rastan PLAYER_BODY Visibility Fix

## Baseline

- Rejected visual symptom in Build 0250: Rastan is physically present and interactive in gameplay, but is absent from the BlastEm VDP Sprite Viewer / final Genesis SAT.
- User VDP evidence: lizard men appear as real VDP/SAT sprites; Rastan does not appear in the sprite viewer at all.
- Interpretation: this is not primarily a palette/CRAM issue and not likely a tile-art decode issue. Rastan's `PLAYER_BODY` lane was not reaching final SAT emission.
- Accepted source baseline for this task: Build 0250.
- Build 0250 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0250.bin`.
- Build 0250 SHA-256: `ca2f60ac94a76e0e26c2a3c8fd92ffb8a8335c2e09689c6c256ac70fe2f05426`.

## Architecture Compliance

- Semantic cut retained: arcade gameplay sprite producer state remains arcade-owned; native helpers only stage final Genesis SAT lanes and return.
- Chip tail removed/preserved boundary: Build 0250 native gameplay paths continue to bypass the old gameplay PC090OJ mirror/scanner/decoder/fill/copy flow for converted gameplay lanes.
- This fix does not re-enable the old gameplay PC090OJ scanner/decoder path.
- No Plane A/B, palette/CRAM, collision, rope, audio, tile-art decode, or frontend behavior was intentionally changed.

## Evidence Inspected

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/genesis_postpatch.disasm.txt`
- Build 0250 lifecycle trace:
  - `states/traces/build0251_rastan_player_body_lifecycle_20260803_173235/native_debug_events.log`
- Build 0251 post-fix lifecycle trace:
  - `states/traces/build0251_rastan_player_body_lifecycle_20260803_173235/build0251_postfix/native_debug_events_0251.log`
- Build 0251 release smoke trace:
  - `states/traces/rastan_direct_video_test_build_0251_mame_30s_20260803_174331/`

## Build 0250 Measured Order and Root Cause

Debugger event trace on Build 0250 proved this gameplay order:

1. `genesistan_pc090oj_hook_target_41f5e` executes.
2. `native_stage_player_blocks_41f5e` queues `PLAYER_BODY` entries.
3. `genesistan_pc090oj_hook_target_41dae` executes.
4. `native_sprite_frame_begin` clears all native lane counts, including `native_player_body_count`.
5. `pc090oj_native_emit_pass` finalizes SAT with `PLAYER_BODY` count zero.

Representative Build 0250 trace excerpt:

```text
EVENT PLAYER_BLOCKS_RTS ... scene=01 pb=000C ... b0=4003/0009/009E/0010 b1=4003/0019/009F/0010
EVENT HOOK_41DAE ... scene=01 ... pb=000C ...
EVENT FRAME_BEGIN_ENTRY ... scene=01 pb=000C ...
EVENT FRAME_BEGIN_RTS ... scene=01 pb=0000 ...
EVENT FINALIZER_ENTRY ... scene=01 pb=0000 ...
EVENT BODY_LANE_BEFORE_SCAN ... scene=01 d6=0000 pb=0000 ...
EVENT FINALIZER_RTS ... scene=01 ... emit=0003 ...
```

Aggregate Build 0250 debugger counts:

- `PLAYER_BLOCKS_RTS` with nonzero `PLAYER_BODY`: `1557`
- `BODY_LANE_BEFORE_SCAN` with nonzero `d6`: `0`
- `BODY_LANE_BEFORE_SCAN` with `d6=0`: `1559`

Root cause: the native sprite frame reset lived in the dispatcher/finalizer hooks (`41DAE` / `45DFA`) instead of the earliest gameplay sprite producer (`41F5E`). Since `41F5E` runs before `41DAE` in the observed gameplay path, the dispatcher reset erased queued Rastan body sprites before the finalizer consumed the queues.

## Fix

Smallest production fix in `apps/rastan-direct/src/pc090oj_hooks.s`:

- Removed `native_sprite_frame_begin` from gameplay `genesistan_pc090oj_hook_target_41dae`.
- Removed `native_sprite_frame_begin` from gameplay `genesistan_pc090oj_hook_target_45dfa`.
- Added `native_sprite_frame_begin` at the start of gameplay `genesistan_pc090oj_hook_target_41f5e`, immediately before `native_stage_player_blocks_41f5e`.

This makes `41F5E` the frame opener and player producer, while `41DAE` / `45DFA` remain mode-selected dispatch/finalize hooks. All gameplay producers now contribute before exactly one finalizer consumes the queues.

## Build 0251 Post-Fix Proof

Build 0251 symbols / disassembly confirm the new order:

- `genesistan_pc090oj_hook_target_41f5e` at runtime Genesis PC `0x072C62`:
  - calls `native_sprite_frame_begin` at `0x072C96`
  - calls `native_stage_player_blocks_41f5e` at `0x072DA6`
  - returns
- `genesistan_pc090oj_hook_target_41dae` at runtime Genesis PC `0x072C38`:
  - no longer calls `native_sprite_frame_begin`
  - calls `native_stage_dispatch_41dae` or `native_stage_dispatch_45dfa`
  - calls `pc090oj_native_emit_pass` at `0x07367C`
- `genesistan_pc090oj_hook_target_45dfa` at runtime Genesis PC `0x072C7C`:
  - no longer calls `native_sprite_frame_begin`
  - dispatches and finalizes only

Representative Build 0251 trace excerpt:

```text
EVENT FRAME_BEGIN_ENTRY ... scene=01 pb=0000 ...
EVENT FRAME_BEGIN_RTS ... scene=01 pb=0000 ...
EVENT PLAYER_BLOCKS_ENTRY ... scene=01 ... a5body=4003/0009/009E/0010
EVENT PLAYER_BLOCKS_RTS ... scene=01 pb=000C ... b0=4003/0009/009E/0010 b1=4003/0019/009F/0010
EVENT HOOK_41DAE ... scene=01 ... pb=000C ...
EVENT FINALIZER_ENTRY ... scene=01 pb=000C ...
EVENT BODY_LANE_BEFORE_SCAN ... scene=01 d5=0003 d6=000C pb=000C b0=4003/0009/009E/0010 b1=4003/0019/009F/0010
EVENT BODY_LANE_AFTER_SCAN ... scene=01 d5=000E ...
EVENT FINALIZER_STORE ... scene=01 d5=000E pb=000C ...
EVENT FINALIZER_RTS ... scene=01 pb=000C ... emit=000E ... satready=0001
```

Aggregate Build 0251 post-fix debugger counts:

- `PLAYER_BLOCKS_RTS` with nonzero `PLAYER_BODY`: `276`
- `BODY_LANE_BEFORE_SCAN` with nonzero `d6`: `276`
- `BODY_LANE_BEFORE_SCAN` with `d6=0`: `3` initial/non-player frames

Verdict: Rastan's `PLAYER_BODY` queue now survives into `pc090oj_native_emit_pass` and contributes to the final SAT count.

## Validation

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release RASTAN_GAMEPLAY_HUD_SPRITES=2
```

Build output:

- Build produced: `0251`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0251.bin`
- SHA-256: `985889dee869892a8f023f60103366a3debf3e2c3732bb727aa6a66d16022d7b`
- Size: `1592460`
- Counter: `251`
- Rolling artifact SHA matches numbered artifact.
- `GATE_PASS`
- Opcode replace site count: `218`
- Canonical coverage: `0x184C8C`
- HUD mode: `RASTAN_GAMEPLAY_HUD_SPRITES=2`

Automated Genesis MAME release smoke:

- Trace: `states/traces/rastan_direct_video_test_build_0251_mame_30s_20260803_174331/`
- Completed the standard 30-second smoke trace.
- No unique unmapped memory addresses reported by the release trace.

Focused lifecycle validation:

- Trace: `states/traces/build0251_rastan_player_body_lifecycle_20260803_173235/build0251_postfix/native_debug_events_0251.log`
- Proved nonzero `PLAYER_BODY` queue survives into the finalizer body-lane scan.
- Proved first body queue entries before finalization:
  - body0: `word0=0x4003`, `Y=0x0009`, `code=0x009E`, `X=0x0010`
  - body1: `word0=0x4003`, `Y=0x0019`, `code=0x009F`, `X=0x0010`

Manual/user verification still required in BlastEm VDP tools:

- Rastan visible in gameplay.
- Rastan appears in the VDP Sprite Viewer / SAT.
- Lizard men still visible.
- Hurry-up bats still visible.
- Axe item still visible.
- No duplicate Rastan.
- No stale bat corpse regression.
- No major speed regression.
- Frontend/title/throne still render.

## Build 0250 Speed and Native Path Preservation

The Build 0250 native speed improvement is preserved: the fix only changes the order of native lane reset relative to existing native gameplay producers. It does not reintroduce legacy gameplay PC090OJ mirror scanning or decoding, and it does not add another finalizer.

Old compatibility code remains physically present for frontend/non-gameplay and later retirement boundaries, but the inspected gameplay hooks still route scene `1` through native lane staging and `pc090oj_native_emit_pass`.

## Open/Closed Issues Impact

- Open issues touched: OPEN-024-adjacent native PC090OJ gameplay sprite architecture.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: palette/CRAM, Plane A/B, collision, rope/reset, audio, frontend, and full BlastEm visual acceptance.

## KNOWN_FINDINGS Impact

Option A: no new finding to index.
