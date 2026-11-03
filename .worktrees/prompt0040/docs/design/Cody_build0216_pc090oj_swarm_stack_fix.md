# Cody - Build 0216 PC090OJ Swarm Stack/Control Corruption Fix

**Date:** 2026-07-19  
**Type:** Targeted proof + implementation + build  
**Build context:** Build 0215/256 accepted; Build 0216/256 produced  
**Scope:** Fix only the first proven hurry-up swarm stack/control-flow corruption boundary. No bat suppression, no sprite skips, no SAT forcing, no palette/terrain/collision/cave/item/damage work.

## Baseline

- Input ROM: `dist/rastan-direct/rastan_direct_video_test_build_0215.bin`
- Build 0215 SHA256: `10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`
- Pre-build counter: `215`
- Required config: `PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=0`
- Output ROM: `dist/rastan-direct/rastan_direct_video_test_build_0216.bin`
- Build 0216 SHA256: `6e9ef28d9f44102e8a0312ff27e0efe6d04e5d7cb9d9393417355ae2a443d4a1`
- Post-build counter: `216`
- Size: `1,583,868` bytes

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-011 (arcade VBlank owns the frame lifecycle), KF-047 (PC090OJ retained representation/candidate model), KF-052/KF-053/KF-054 (VBlank timing/budget hazards), KF-064/KF-065/KF-067 (lizard-era PC090OJ load and stack-latch hazards), and KF-004/KF-006/address-map discipline. Open issues touched: OPEN-017 and OPEN-024; OPEN-001 context; OPEN-015 not touched. No contradiction of CONFIRMED/STRONG findings was detected.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. The fix keeps the existing Genesis helper service then arcade VBlank tail-chain architecture; it changes one copied arcade VBlank-tail instruction byte-neutrally and leaves the final `rte` intact.

## Files / Evidence Inspected

- `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`
- `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`
- `docs/design/Cody_build0216_hurryup_bat_cpu_lock.md`
- `docs/design/Cody_build0216_arcade_bat_path_genesis_lock.md`
- `docs/design/Cody_full_arcade_ghidra_disassembly.md`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `states/traces/build0216_hurryup_bat_cpu_lock_20260719_184124/native_full_repro_instruction_trace.log`
- `states/traces/build0216_hurryup_bat_cpu_lock_20260719_184124/native_crash_boundary_trace.log`

JSON provenance used for address discipline:

- `build/rastan-direct/address_map.json` SHA256 `78eef2c5702e209c920f9ea04d62a310c7247635fe53e0b28face9f04e63d417`
- `build/rastan-direct/rastan_direct_patch_manifest.json` SHA256 before the release attempt: `6c5454c1938c37fbf37d7d9ed93852dfc15e721671e652225c02e3d1d19f22c1`
- `address_map.json` maps `arcade_pc 0x0003A07A` to `runtime_genesis_pc 0x0003A27A` in an `arcade_copy` segment with `identity_offset 512`.

## Static Stack-Delta Audit

Artifact: `states/traces/build0216_pc090oj_swarm_stack_fix_20260719_201422/static_stack_delta_audit.csv`

Audited paths:

- `_vblank_service` (`runtime_genesis_pc 0x000700C2`)
- `vdp_prepare_sprites` (`runtime_genesis_pc 0x00072A86`)
- `.Lpc090oj_mark_changed_candidates_since_shadow`
- `.Lpc090oj_process_candidates`
- `.Lpc090oj_sync_record_from_mirror`
- `.Lpc090oj_decode_record`
- activation/deactivation helpers
- represented/waiting/SAT link management helpers
- `vdp_commit_sprites_vram`, `.Lvcs_tile_dma`, `.Lvcs_sat_dma`

Result: no local push/pop or early-return stack imbalance was found in the inspected Genesis PC090OJ helper paths. Visible `movem` frames restore their saved registers, and helper calls do not leave caller-cleaned stack arguments behind.

## First Proven Runtime Corruption Boundary

Build 0215 native traces showed repeated interrupt reentry at the arcade VBlank final-RTE boundary:

```text
runtime_genesis_pc 0x0003A27A: andi #0xF0FF,SR
runtime_genesis_pc 0x0003A27E: rte
```

During the natural hurry-up bat swarm, the combined Genesis `_vblank_service -> arcade VBlank` chain had grown long enough that IRQ6 was pending by the time the arcade VBlank tail reached `0x0003A27A`. The `andi #0xF0FF,SR` lowered IPM before the `rte`, allowing IRQ6 to interrupt at `0x0003A27E`, stack another frame, and re-enter `_vblank_service`. The older traces then show repeated `0x3A27E` stack material, falling SP, later impossible PCs, and eventually the illegal-instruction/crash-render path (`0x0000040E` / `0x000005F4`).

Interpretation: the first proven corrupting boundary is not a PC090OJ helper push/pop leak. It is the copied arcade VBlank tail lowering IPM in a Genesis-overrun context before the final `rte`.

## Implementation

Changed `specs/rastan_direct_remap.json` with one byte-neutral `opcode_replace`:

```json
{
  "arcade_pc": "0x03A07A",
  "original_bytes": "027CF0FF",
  "replacement_bytes": "007C0600"
}
```

Meaning:

- Before: `andi #0xF0FF,SR; rte`
- After: `ori #0x0600,SR; rte`

The patched instruction keeps IPM >= 6 until the following `rte` restores the stacked SR. No arcade control-flow return is removed or bypassed.

Canonical invariant delta:

- `opcode_replace_count`: `215 -> 216`
- `total_genesis_bytes_covered`: remains `0x182AFC`

First release attempt stopped before numbered artifact production because I initially used the runtime address in the `arcade_pc` field. The gate rejected the mismatch at `0x03A27A` (`expected 027cf0ff but found 3b7c0001`). No numbered build was produced or deleted. The spec was corrected to authoritative `arcade_pc 0x03A07A` per `address_map.json`, then the release succeeded.

## Build Verification

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=0
```

Results:

- `GATE_PASS`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0216.bin`
- SHA256: `6e9ef28d9f44102e8a0312ff27e0efe6d04e5d7cb9d9393417355ae2a443d4a1`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Rolling ROM byte-identical to numbered Build 0216: YES
- Build 0215 still preserved and unchanged: YES (`10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`)

Byte/disassembly proof:

```text
Build 0215 @ runtime_genesis_pc 0x0003A27A: 027cf0ff4e73303c
Build 0216 @ runtime_genesis_pc 0x0003A27A: 007c06004e73303c

0003a274: 4eb9 0005 5ea2  jsr 0x55ea2
0003a27a: 007c 0600       oriw #1536,%sr
0003a27e: 4e73            rte
```

## Runtime Validation

Evidence directory:

`states/traces/build0216_pc090oj_swarm_stack_fix_20260719_201422/`

Primary validation artifacts:

- `genesis_build0216_swarm_validate.lua`
- `run_genesis_build0216_validate.sh`
- `genesis_build0216_swarm_validate.csv`
- `genesis_build0216_swarm_validate_events.log`
- `build0216_swarm_validate_summary.md`
- snapshots under `snaps_build0216/`

The run starts the game with the same scripted A/Start input pattern and then leaves the game alone. It exits by scripted `MAX_FRAME_EXIT` at frame `8000`.

Reduced results:

- CSV rows: `320`
- Sampled frame range: `30..7980`
- Event log exit: `MAX_FRAME_EXIT frame=8000`
- Suspect sampled exception/impossible PCs: `0`
- `STABLE_SUSPECT_PC` event: `False`
- Former failure boundary frame `6030`: `pc=0x07234A`, `sr=0x2704`, `sp=0xFEFF68`, state `2/3/0`, scene `0x0100`, HP `0x3000`
- End-of-run near frame `7980`: `pc=0x07232E`, `sr=0x2700`, `sp=0xFEFF68`, state `2/3/0`, scene `0x0100`, HP `0x3000`
- Event-log snapshot bat-family records:
  - code `0x0269`: frames `5700..6160`
  - code `0x0268`: frame `6180`
  - code `0x026A`: frames `5900..8000`

This materially passes the former Build 0215 lock window and preserves natural bat-family PC090OJ activity.

## Native Debugger Note

Native debugger command/log artifacts were created:

- `genesis_build0216_sp_debug.cmd`
- `run_genesis_build0216_sp_debug.sh`
- `logs/genesis_build0216_sp_debug_stderr.log`
- `logs/genesis_build0216_sp_debug_offscreen_stderr.log`
- `logs/debugger_internal_probe_stderr.log`
- `logs/debugger_none_probe_stdout.log`

The Qt debugger failed without display (`xcb`), and the offscreen Qt run completed but did not surface debugger `printf` breakpoint output. Therefore this report does **not** claim a new runtime breakpoint-derived `vdp_prepare_sprites` entry/exit SP table for Build 0216. The reliable after-fix runtime evidence is the frame-8000 MAME validation plus byte/disassembly proof. The static stack-delta table supplies the local helper balance audit.

## Regression / Non-Actions

Preserved:

- Build 0215 numbered artifact remains present and SHA-identical.
- Build 0216 terrain progression inherits Build 0215 code; this task did not touch PC080SN terrain code.
- Lizard palette/alignment code was not touched.
- No bat suppression, timer delay, collision skip, actor/SAT forcing, watchdog patch, capacity increase, palette patch, or unrelated cave/lizard/splat/item/terrain work was performed.

Deferred:

- Bat palette and enemy damage/combat behavior.
- Remaining PC090OJ visual correctness.
- Real-hardware acceptance.
- Cave cover, foreground defects, lizard cave death, lizard damage, dropped item/splat palettes, terrain correctness, black bars, and record 132.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024; OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: remaining PC090OJ visual/combat correctness, bat palette/damage, real-hardware acceptance, terrain/cave/item/death issues, OPEN-015.

## KNOWN_FINDINGS Impact

Option B - new finding indexed as KF-068. Rationale: the VBlank-tail IPM reentry window is a durable mechanism and a rediscovery hazard for future VBlank/PC090OJ timing work.

## STOP

STOP triggered: **NO** for the final result. Build 0216 was produced and validated beyond the former failure window.
