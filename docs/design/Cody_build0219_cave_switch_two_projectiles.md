# Cody - Build 0219 Cave Runtime Residency Switch / Two Projectile Gate

**Date:** 2026-07-20  
**Type:** Hybrid prompt started; evidence capture STOP before implementation/build  
**Baseline:** Build 0218/256 rejected by user visual verification for cave; next authorized build would be Build 0219/256  
**Build 0218 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0218.bin`  
**Build 0218 SHA256:** `30a84f86cc34e8dc9861f945138e7aafabe6f072b466fa6d161b8b0e8ed60a95`  
**Evidence directory:** `states/traces/build0219_cave_switch_two_projectiles_20260720_171819/`  
**Scope actually completed:** non-ROM capture harness plus one incomplete Build 0218 manual-capture attempt. No source/spec/tool/Makefile/ROM/invariant changes. No Build 0219 produced.

## Phase 0

Classification: **EXTENDING** (OPEN-017 / Stage 1 PC080SN cave visual correctness and PC090OJ stale projectile follow-up). Relevant priors loaded: KF-010 (BG/FG plane mapping), KF-011 (arcade VBlank owns lifecycle), KF-038 (long PC080SN row-depth/tall staging), KF-040 (gameplay PC080SN output routed through producer/helper paths), KF-041 (Stage 1 runtime PC080SN source/residency model; Build 0218 cave split materialized but user/matched cave acceptance required), KF-047/KF-052/KF-053/KF-054 (PC090OJ representation/timing/residency context), KF-064/KF-065/KF-066/KF-067 (lizard and record-family context), and KF-068 (Build 0216 VBlank-tail IPM fix to preserve).

Rediscovery Hazard HIGH findings touched: KF-038, KF-040, KF-041, KF-068. No contradiction of a CONFIRMED/STRONG finding was detected.

Open issues touched: OPEN-017 primary; OPEN-001/OPEN-024 context. OPEN-015 not touched. Closed issues touched: NONE. Deferred appendix entries relevant: none identified.

Architecture compliance: **CONFIRMED** for work performed. The only new executable artifact is a MAME Lua observer under `states/`; no Genesis code, source behavior, ROM, or build artifact was modified.

## Required Gate From Prompt

The prompt required this task to **begin with a matched Build 0218 cave capture** and explicitly forbade returning an outdoor-only validation as cave evidence.

User-provided observation accepted as task context:

- Tighe manually reached the cave in Build 0218.
- The cave still displayed the wrong repeating horizontal brick pattern.
- Two unwanted gray fire-sword/projectile-like objects were visible.
- Projectile A pre-existed before Build 0218.
- Projectile B was introduced by Build 0218.

However, for implementation, the task required debugger/runtime evidence at the matched cave state: PC080SN source/tileset/LUT/staging/VDP state and separate PC090OJ ownership histories for Projectile A and Projectile B.

## Capture Harness Created

Created in the evidence directory:

- `states/traces/build0219_cave_switch_two_projectiles_20260720_171819/build0218_manual_cave_capture.lua`
- `states/traces/build0219_cave_switch_two_projectiles_20260720_171819/README_CAPTURE.txt`

The harness logs:

- Runtime state `%a5@(0)/(2)/(4)` via `WRAM 0xFF0000/0xFF0002/0xFF0004`.
- Logical scene and PC080SN tileset: `WRAM 0xFFBFF0/0xFFBFF1`.
- PC080SN scene range values: `WRAM 0xFFBFF2/0xFFBFF6`.
- Gameplay strip destination/source state: `WRAM 0xFF10A0`, `0xFF10CA`, `0xFF10CC`, `0xFF1100`, `0xFF1104`.
- BG/FG normal/tall staging nonzero counts.
- Player/camera words used in prior traces.
- PC090OJ active/represented/candidate/dirty counts.
- Periodic nonzero PC090OJ mirror records from `pc090oj_object_ram`.
- Periodic staged SAT entries from `staged_sprite_sat`.
- Periodic and event screenshots.

## Manual Capture Attempt

Command run with GUI MAME for human-assisted capture:

```bash
TRACE_DIR="$PWD/states/traces/build0219_cave_switch_two_projectiles_20260720_171819" \
TRACE_PREFIX=build0218_manual \
mame genesis \
  -cart "$PWD/dist/rastan-direct/rastan_direct_video_test_build_0218.bin" \
  -window -nothrottle -sound none -skip_gameinfo \
  -autoboot_script "$PWD/states/traces/build0219_cave_switch_two_projectiles_20260720_171819/build0218_manual_cave_capture.lua"
```

The attempt was stopped after it failed to reach the required cave source family. The MAME process was terminated by PID after normal Ctrl-C/TERM did not exit; no evidence files were deleted.

## Captured Files

- `build0218_manual_runtime.csv` - 678 lines, last sampled frame `38220`.
- `build0218_manual_pc090oj_records.csv` - 33193 lines.
- `build0218_manual_sat.csv` - 5665 lines.
- Periodic screenshots through `build0218_manual_frame_037800_periodic.png`.

The late screenshot `build0218_manual_frame_037800_periodic.png` shows outdoor Stage 1 with lizards and a gray projectile/sphere-like object, not the cave.

## Capture Result

The capture did **not** satisfy the required matched-cave gate:

- Last sampled frame: `38220`.
- Cave source pointer rows: `0`.
- Tileset `3` rows: `0`.
- Observed tilesets in runtime log: `00` during frontend/bootstrap, `01` during gameplay.
- Observed nonzero strip pointers in runtime log:
  - `0x0000D31C` (outdoor family): `601` rows.
  - `0x0000DB1C`: `5` rows.
  - `0x0000F31C`: `10` rows.
- Required cave range `0x0000FB1C..0x00010B1C`: **never observed**.
- Final sampled state stayed gameplay `2/3/0`, logical scene `1`, PC080SN tileset `1`, strip pointer `0x0000D31C`.

Representative final runtime row:

```text
38220,sample,0731FE,0002/0003/0000,01,01,01806A22,000570C2,C08100,0000,0000,0000D31C,0002,2048,4096,2016,4032,0020,0000,0004,0000,0018,0018,0007,7,0000
```

## Cave Switch Determination

**Not determined.** The exact cave residency switch boundary remains unproven in this task because the required Build 0218 matched cave source family was not captured.

What remains unknown from this attempt:

- Whether Build 0218 requests tileset `3` at the user-observed cave state.
- Whether the source pointer is transformed too early.
- Whether attr `0x0003` is lost.
- Whether the cave LUT is loaded but staging still uses outdoor-resident VDP tiles.
- Whether cave residency loads and is immediately replaced by an outdoor reload.
- Whether logical scene ID and residency ID are conflated at the manual cave state.

## Projectile A / Projectile B Determination

**Not determined.** The outdoor capture shows a gray projectile/sphere-like symptom, but the task requires cave-matched classification of two specific objects:

- Projectile A: pre-existing before Build 0218.
- Projectile B: introduced by Build 0218.

This attempt cannot classify either projectile because it did not capture the matched cave state with both unwanted projectiles visible, and it did not compare Build 0216/0217/0218 at that cave state.

No claim is made that both projectiles are Build 0218 regressions. No owner, SAT slot, PC090OJ record, actor source, lifecycle, or retirement cause is proven here.

## Implementation / Build Decision

No implementation was performed. No Build 0219 was produced.

Reason: the required first proof gate failed. Applying a cave-switch or projectile fix without matched cave runtime data would violate the State Causality Rule and the prompt's explicit instruction to begin from a matched Build 0218 cave capture.

## Recommended Next Step

Repeat the same harness, or a debugger-watchpoint variant of it, with the MAME window confirmed focused and with manual play to the user-observed Build 0218 cave state. Hold the cave screen for several seconds once both unwanted projectiles are visible, then close MAME. Only after that capture should the implementation portion resume.

Suggested rerun command:

```bash
TRACE_DIR="$PWD/states/traces/build0219_cave_switch_two_projectiles_20260720_171819" \
TRACE_PREFIX=build0218_manual_retry \
mame genesis \
  -cart "$PWD/dist/rastan-direct/rastan_direct_video_test_build_0218.bin" \
  -window -nothrottle -sound none -skip_gameinfo \
  -autoboot_script "$PWD/states/traces/build0219_cave_switch_two_projectiles_20260720_171819/build0218_manual_cave_capture.lua"
```

A successful capture should contain at least one of:

- `strip_ptr1100` in `0x0000FB1C..0x00010B1C`.
- `tileset=03`.
- Event rows `cave_source_ptr`, `first_cave_ptr`, or `tileset3_periodic`.
- Screenshots showing the wrong cave and both projectiles.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017 primary; OPEN-001 and OPEN-024 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: cave-switch fix, Projectile A lifecycle/ownership, Projectile B Build 0218 regression root, Build 0219 production, legitimate projectile regression testing, BlastEm/Exodus cave visual verification.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This task produced a useful capture harness and an incomplete outdoor runtime attempt, but no new durable mechanism or correction was proven.

## STOP

STOP triggered: **YES**. Required matched Build 0218 cave capture was not obtained; therefore no source change or Build 0219 is safe from this evidence.
