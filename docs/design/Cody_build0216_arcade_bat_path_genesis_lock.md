# Cody - Interactive Original-Arcade Bat Path and Genesis Build 0215 Lock Boundary

**Date:** 2026-07-19  
**Type:** Hybrid evidence continuation; implementation only if patch-safe  
**Baseline build:** Build 0215/256 accepted  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0215.bin`  
**Build 0215 SHA256:** `10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`  
**Scope:** Original arcade interactive bat-path evidence plus Genesis Build 0215 divergence analysis. No source/spec/tool/Makefile/ROM/invariant changes. No build produced. Build 0216 withheld because no patch-safe correction boundary was proven.

Address labels: `arcade_pc` = original arcade maincpu program counter; `runtime_genesis_pc` = translated Genesis runtime PC / patched-ROM offset where applicable; `arcade_WRAM` = original arcade work RAM; `Genesis_WRAM` = Genesis work RAM; `HW_ADDRESS` = hardware address.

---

## Phase 0

Classification: **EXTENDING** OPEN-017 / OPEN-024 gameplay sprite/runtime failure analysis from the Build 0215 accepted baseline and the prior Build 0216 STOP evidence.

Relevant priors loaded:

- KF-001 / KF-003: watchdog/timer and reset context, referenced but not redefined.
- KF-004 / KF-006: runtime PC and address-mapping discipline; JSON mapping is the authority where mapped correlation is required.
- KF-010 / KF-011 / KF-013: rendering and frame lifecycle remain arcade-owned, with Genesis VBlank as hardware service/helper path.
- KF-026 / KF-032: PC090OJ writes must route through staging/mirror/SAT commit rather than raw hardware writes.
- KF-036: mapped work-RAM base discipline.
- KF-038: tall PC080SN/tilemap window context, not the focus here.
- KF-063: PC090OJ expansion engine is safe only for validated actor/state inputs.
- KF-064 / KF-065 / KF-067: lizard/progression/composite sprite fixes are active context and must not be disturbed.
- KF-066: gameplay HUD sprite suppression/bank36 context.

Rediscovery-hazard findings touched: KF-011, KF-013, KF-026, KF-032, KF-063, KF-064/KF-065, KF-067. No contradiction found.

Open issues touched: OPEN-017 and OPEN-024 primary; OPEN-001 context; OPEN-015 context only. Closed issues touched: none.

Architecture compliance: **CONFIRMED**. The arcade runtime remains the program; Genesis-side code is considered only as helper/opcode-replacement/staging code. No Genesis-owned bat spawning, timer changes, damage forcing, collision bypass, watchdog recovery, or second renderer is proposed.

STOP status for implementation: **YES**. Evidence improved substantially, but the exact first Genesis corrupting instruction/control-path divergence was not proven.

---

## Evidence Inspected

Documents:

- `docs/design/Cody_build0216_hurryup_bat_cpu_lock.md`
- `docs/design/Cody_full_arcade_ghidra_disassembly.md`
- `docs/design/Cody_build0215_fg_progression_restoration.md`
- `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest relevant `AGENTS_LOG.md` entries

Original arcade/Ghidra exports:

- `analysis/ghidra/rastan_arcade/exports/function_inventory.tsv`
- `analysis/ghidra/rastan_arcade/exports/call_graph_edges.tsv`
- `analysis/ghidra/rastan_arcade/exports/full_listing.tsv`
- `analysis/ghidra/rastan_arcade/exports/address_correlation_report.json`

Build-specific provenance:

- `build/rastan-direct/address_map.json` SHA256 `78eef2c5702e209c920f9ea04d62a310c7247635fe53e0b28face9f04e63d417`
- `specs/rastan_direct_remap.json` SHA256 `8bf9962089f0d28aa16738356113cbd95d406f481f55e44aec2e2d60cbad9459`
- `build/rastan-direct/startup_common_relocations.json` SHA256 `b924bc93b3f784ed4ae80ea3734a218fbbd9e3388de3d0df61932cf5b0a9f5f7`
- `build/rastan-direct/rastan_direct_patch_manifest.json` SHA256 `6c5454c1938c37fbf37d7d9ed93852dfc15e721671e652225c02e3d1d19f22c1`
- `analysis/ghidra/rastan_arcade/exports/address_correlation_report.json` SHA256 `86a9e4a1bb806fa9ad45418c4262132baf695eb41c33694f48c0569419f51dd5`

Source/static files:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`

Runtime evidence:

- Prior Genesis STOP trace: `states/traces/build0216_hurryup_bat_cpu_lock_20260719_184124/`
- New original-arcade interactive trace: `states/traces/build0216_arcade_bat_path_genesis_lock_20260719_194524_interactive/`
- Reduced arcade note: `states/traces/build0216_arcade_bat_path_genesis_lock_20260719_194524_interactive/arcade_bat_reduced_analysis.md`

---

## Interactive Original Arcade Run

Tighe completed the requested original arcade run:

- **Environment:** MAME original arcade `rastan` / Rastan World Rev 1 ROM.
- **Control:** human-played by Tighe.
- **Cheats:** none used.
- **Life 1:** lizard-men killed Rastan before the hurry-up bats spawned; this is a lizard-damage comparison/control.
- **Life 2:** Tighe remained in place; hurry-up bat swarm spawned naturally; bats killed Rastan.
- **Life 3:** same stationary natural hurry-up bat test; bats again killed Rastan.

The run exited cleanly with MAME status `0`; all trace files were preserved. No numbered build artifact was deleted, overwritten, or reused.

### Capture Files

Trace directory: `states/traces/build0216_arcade_bat_path_genesis_lock_20260719_194524_interactive/`

- `arcade_bat_frames.csv` - `962,290` bytes
- `arcade_bat_events.log` - `1,299,581` bytes
- `arcade_bat_execs.csv` - `97` bytes, header only
- `arcade_bat_writes.csv` - `157` bytes, header only
- `arcade_bat_pc090oj_writes.csv` - `92` bytes, header only
- `snaps_arcade/arcade_bat_0000.png` through `arcade_bat_0012.png` - 13 snapshots
- `logs/arcade_mame_stdout.log` - `Average speed: 100.00% (133 seconds)`
- `logs/arcade_mame_stderr.log` - ALSA/Qt warnings only
- `logs/arcade_mame_exit_code.txt` - `0`

### Trace Limitation

The arcade Lua script successfully installed memory taps:

```text
EVENT TAP_OK STATE_TIMER 10C000-10C05F
EVENT TAP_OK PLAYER_ENERGY 10C13A-10C13B
EVENT TAP_OK PLAYER_CLUSTER 10C0B0-10C1FF
EVENT TAP_OK ACTOR_BLOCKS 10C2C8-10CB47
EVENT TAP_OK PC090OJ D00000-D007FF
EVENT TAP_OK PALETTE_RAM 200000-200FFF
```

But this MAME Lua environment does not expose `install_execute_tap`; all execute taps failed with:

```text
EVENT EXEC_TAP_FAIL ... attempt to call a nil value (method 'install_execute_tap')
```

Therefore the trace is **authoritative for state/actor/PC090OJ snapshots**, but **not authoritative for exact arcade writer PCs, exact allocation/damage writer instructions, or exact call/return provenance**.

---

## Arcade Three-Life Analysis

State-segment reduction from `arcade_bat_frames.csv`:

| Segment | Frames | State |
|---|---:|---|
| frontend/startup | `1-405` | boot/title/startup transitions |
| Life 1 gameplay | `406-993` | `2/3/0` |
| Life 1 death/restart | `994-1126` | begins `2/4/0`, then restart states |
| Life 2 gameplay | `1127-4368` | `2/3/0` |
| Life 2 death/restart | `4369-4501` | begins `2/4/0`, then restart states |
| Life 3 gameplay | `4502-7821` | `2/3/0` |
| Life 3 death sequence | `7822-8020` | begins `2/4/0`, continues through capture end |

Life summary:

| Life | Classification | Gameplay frames | Max active actors | Max coded PC090OJ records | Max code `0x0269` records | Outcome |
|---|---|---:|---:|---:|---:|---|
| 1 | lizard-damage comparison | `588` | `4` | `92` | `0` | death transition frame `994` |
| 2 | authoritative bat swarm | `3242` | `12` | `102` | `9` | bat-damage death transition frame `4369` |
| 3 | authoritative bat swarm | `3320` | `13` | `101` | `9` | bat-damage death transition frame `7822` |

### Life 2 Bat Evidence

- First active-actor jump consistent with natural hurry-up swarm: frame `3687`, sampled `arcade_pc 0x03B098`, active actors `10`, HP field `0x2400`.
- First PC090OJ code `0x0269` presence: frame `3692`, sampled `arcade_pc 0x03B080`, active actors `10`, coded PC090OJ records `101`, code `0x0269` count `9`.
- Pre-death sample: frame `4368`, state `2/3/0`, HP field `0xFF00`, active actors `4`.
- Death transition: frame `4369`, state `2/4/0`, HP field `0x0000`, no lock.

Representative actor changes:

```text
EVENT ACTOR_CHANGE frame=3687 idx=20 pc=03B098 sig=01B9000003:01F0:0000:00F0:0268:0009:0000:0000:0000
EVENT ACTOR_CHANGE frame=3687 idx=21 pc=03B098 sig=01B9000003:0148:0000:00F0:0268:0008:0000:0000:0000
EVENT ACTOR_CHANGE frame=3687 idx=28 pc=03B098 sig=01B9000003:005B:0000:00F8:0268:0001:0000:0000:0000
EVENT ACTOR_CHANGE frame=3689 idx=20 pc=039FAE sig=01B9010004:01F3:0001:00F1:0268:00AA:0000:0000:0000
```

### Life 3 Bat Evidence

- First active-actor jump consistent with natural hurry-up swarm: frame `7062`, sampled `arcade_pc 0x039FAE`, active actors `11`, HP field `0x3000`.
- First PC090OJ code `0x0269` presence: frame `7067`, sampled `arcade_pc 0x03B090`, active actors `11`, coded PC090OJ records `95`, code `0x0269` count `9`.
- Pre-death sample: frame `7821`, state `2/3/0`, HP field `0xFF00`, active actors `9`, code `0x0269` count `5`.
- Death transition: frame `7822`, state `2/4/0`, HP field `0x0000`, no lock.

Representative actor changes:

```text
EVENT ACTOR_CHANGE frame=7062 idx=20 pc=039FAE sig=01B9000003:01F0:0000:0030:0268:0009:0000:0000:0000
EVENT ACTOR_CHANGE frame=7062 idx=21 pc=039FAE sig=01B9000003:0148:0000:00E0:0268:0008:0000:0000:0000
EVENT ACTOR_CHANGE frame=7062 idx=28 pc=039FAE sig=01B9000003:0009:0000:00F8:0268:0001:0000:0000:0000
EVENT ACTOR_CHANGE frame=7064 idx=20 pc=03B086 sig=01B9010004:01F3:0001:0031:0268:00AA:0000:0000:0000
```

### Arcade Interpretation

**Proven:** natural hurry-up bat swarm behavior is valid original arcade behavior. The swarm can damage and kill Rastan, and the original arcade runtime transitions cleanly into death/restart handling.

**Not proven:** exact arcade allocation writer PC, exact bat update dispatch, exact damage writer PC, exact PC090OJ record writer PC, and exact call/return stack behavior. Those require debugger-side execute breakpoints/watchpoints or a MAME Lua environment with execute taps.

---

## Ghidra Static Context

Ghidra exports identify the broad original arcade gameplay/VBlank path, but not a captured exact bat writer path from this run:

- `arcade_pc 0x03A008` (`vector_1d_target_03a008`) calls `arcade_pc 0x041F30` during VBlank/gameplay service.
- `arcade_pc 0x041F30` calls `arcade_pc 0x041DAE`, `0x047004`, `0x05988C`, `0x059882`, `0x041F5E`, `0x045D72`, and `0x055AB4`.
- `arcade_pc 0x041DAE` calls `arcade_pc 0x03D054` and `0x041EDE`.
- `arcade_pc 0x045DFA` also calls `arcade_pc 0x03D054`.
- `arcade_pc 0x03D054` is the PC090OJ expansion/function region with many internal subroutine calls.

Representative export rows:

```text
function_inventory.tsv: 0x041F30 callers include 0x03A008; callees include 0x041DAE/0x045D72/0x055AB4
function_inventory.tsv: 0x041DAE callees include 0x03D054 and 0x041EDE
function_inventory.tsv: 0x045DFA callees include 0x03D054
call_graph_edges.tsv: 0x041F30 -> 0x041DAE
call_graph_edges.tsv: 0x041DAE -> 0x03D054
call_graph_edges.tsv: 0x045DFA -> 0x03D054
```

Because runtime execute taps failed, these static paths are **context**, not proof of the exact Life 2/3 bat writer/control path.

---

## Genesis Build 0215 Comparison

Prior Genesis evidence from `states/traces/build0216_hurryup_bat_cpu_lock_20260719_184124/` remains the reliable Build 0215 failure baseline.

Key samples from `genesis_build0215_native_driver.csv`:

| Frame | Sampled runtime_genesis_pc | SP | State | Scene sample | HP | mirror_coded | represented_count | Notes |
|---:|---:|---:|---|---:|---:|---:|---:|---|
| `5640` | `0x0007233A` | `0x00FEC37A` | `2/3/0` | `0x0100` | `0x3000` | `81` | `0x000A` | active gameplay |
| `5700` | `0x00072B1E` | `0x00FEC2CC` | `2/3/0` | `0x0100` | `0x3000` | `90` | `0x0011` | candidate compare path |
| `5910` | `0x000721F0` | `0x00FEC0EA` | `2/3/0` | `0x0100` | `0x3000` | `90` | `0x0013` | still coherent scene sample |
| `5940` | `0x00072B68` | `0x00FEC06A` | `2/3/0` | `0x0100` | `0x3000` | `90` | `0x0013` | mirror shadow copy path |
| `5970` | `0x00072DA6` | `0x00FEBFFE` | `2/3/0` | `0x39A2` | `0x3000` | `97` | `0x0022` | first sampled corrupt scene value |
| `6000` | `0x000721BA` | `0x00FEBFE0` | `2/3/0` | `0x00FF` | `0x3000` | `97` | `0x0022` | corrupted/suspect sample |
| `6030` | `0x008FB57A` | `0x00FEC04E` | `2/3/0` | `0xBDE0` | `0x3000` | `97` | `0x0022` | impossible/control-corrupt PC sample |

Prior STOP evidence also recorded:

- Native debugger stop at `runtime_genesis_pc 0x0000040E`, the illegal-instruction exception stub.
- Recurrent sampled stable crash path at `runtime_genesis_pc 0x000005F4`, a crash-renderer/minimal path, not the original faulting gameplay PC.
- Exception stack content was corrupt/unreliable; original Genesis faulting PC was not recovered.
- No hit on `genesistan_pc090oj_hook_audit_guard`; audit flag stayed `0`.
- Exact scene-id watch did not catch a non-`0x0100` gameplay write before the illegal stop.

### Genesis Static Path Around the Suspect Samples

Source inspection shows that the sampled Genesis PCs around the late pre-lock window are inside the Genesis-only PC090OJ helper/representation path:

- `apps/rastan-direct/src/vdp_comm.s:182`: `_vblank_service` calls `vdp_prepare_sprites` before display-off and sprite VRAM commit.
- `apps/rastan-direct/src/pc090oj_hooks.s:1243`: `vdp_prepare_sprites` consumes `pc090oj_mirror_dirty` through `.Lpc090oj_mark_changed_candidates_since_shadow`, then processes candidate records.
- `apps/rastan-direct/src/pc090oj_hooks.s:1311`: `.Lpc090oj_mark_changed_candidates_since_shadow` compares `pc090oj_object_ram` against `pc090oj_mirror_shadow` and marks changed candidates.
- `apps/rastan-direct/src/pc090oj_hooks.s:1447`: `.Lpc090oj_process_candidates` consumes candidate bits and calls `.Lpc090oj_sync_record_from_mirror` for each candidate.
- `apps/rastan-direct/src/pc090oj_hooks.s:1485`: `.Lpc090oj_decode_record` decodes the staged PC090OJ mirror record and performs code/bbox/viewport tests.
- `apps/rastan-direct/src/pc090oj_hooks.s:2039` and `:2156`: activation/deactivation manage represented records, SAT slots, links, waiting records, and record-to-slot state.
- `apps/rastan-direct/src/pc090oj_hooks.s:520`: gameplay `genesistan_pc090oj_hook_target_41dae` routes to `pc090oj_stage_block2c8` and the validated record-46 path.
- `apps/rastan-direct/src/pc090oj_hooks.s:601`: `pc090oj_stage_block2c8` stages the large A5+0x2C8 composite actor block into mirror records `140..238`, then flushes via `.Lpc090oj_family_apply_record`.

Symbol locations from `apps/rastan-direct/out/symbol.txt`:

```text
runtime_genesis_pc 0x00072412 genesistan_pc090oj_hook_target_41dae
runtime_genesis_pc 0x00072432 genesistan_pc090oj_hook_target_45dfa
runtime_genesis_pc 0x000724C4 pc090oj_stage_block2c8
runtime_genesis_pc 0x00072A86 vdp_prepare_sprites
Genesis_WRAM 0x00FFA9FC pc090oj_object_ram
Genesis_WRAM 0x00FFBC00 pc090oj_block2c8_scratch
```

---

## First Divergence Assessment

**First exact divergence:** not proven.

The first reliable sampled difference is that original arcade Lives 2/3 handle natural bat swarm damage and death cleanly, while Genesis Build 0215 remains at HP `0x3000`, enters a late heavy actor/PC090OJ-helper window, and by frame `5970` has a corrupt/suspect scene sample while executing inside the Genesis-only PC090OJ decode/representation helper region.

The earliest sampled Genesis corruption boundary is therefore:

- coherent sample: frame `5940`, `runtime_genesis_pc 0x00072B68`, scene sample `0x0100`, represented_count `0x0013`.
- first sampled corrupt scene value: frame `5970`, `runtime_genesis_pc 0x00072DA6`, scene sample `0x39A2`, represented_count `0x0022`.

This is **not** exact enough to patch. It proves the symptom lands inside/around the Genesis-only PC090OJ helper path during a heavy actor/swarm interval, but it does not identify the first bad instruction, wrong slot/link update, wrong candidate/record transition, or corrupting write.

---

## Patch-Safety Decision

Build 0216 was **not** produced.

Reason: the task authorized a build only if the arcade path and first Genesis divergence proved a safe correction boundary. The new arcade evidence proves that the bat swarm is normal arcade behavior, but it does not recover exact writer/control path because execute taps failed. The Genesis evidence still lacks the first corrupting instruction/control-flow divergence.

Forbidden-but-tempting fixes remain invalid:

- Do not disable or suppress bats.
- Do not change the hurry-up timer.
- Do not cap the swarm arbitrarily.
- Do not force actors or seed state.
- Do not skip bat collision/damage.
- Do not add a watchdog/crash recovery path.
- Do not patch bat colors as a proxy for this failure.
- Do not broadly rewrite PC090OJ representation without a pinned state-causality failure.

### Smallest Safe Next Diagnostic Boundary

The next narrow diagnostic should be Genesis-side, because the original arcade behavior is now established at the outcome level.

Recommended next task:

1. Use Build 0215/256 or the current rolling equivalent without source changes.
2. Focus only on the late Genesis window between the last coherent native-driver sample and first corrupt sample: roughly frames `5940-5970` from prior trace.
3. Set debugger-side watchpoints/breakpoints that stop **before** corruption on:
   - `Genesis_WRAM genesistan_current_scene_id` and adjacent scene/audit fields;
   - `record_to_slot`, `used_sat_slots`, `represented_records`, `waiting_records`, and `pc090oj_represented_count`;
   - stack low-water writes around `Genesis_WRAM 0x00FEBF00..0x00FEC100` if supported without overwhelming output;
   - runtime PCs inside `.Lpc090oj_activate_record`, `.Lpc090oj_deactivate_record`, `.Lpc090oj_free_slot`, `.Lpc090oj_place_record_in_slot`, and `.Lvcs_tile_dma` when `represented_count` jumps toward `0x22`.
4. Stop at the first invariant break, not at the later illegal-instruction handler.

Working hypothesis only: a Genesis-only PC090OJ representation/SAT/link/tile-residency transition under the late bat/lizard actor load corrupts control or BSS/stack-adjacent state. This is an inference, not a proven root cause.

---

## Open / Closed Issues Impact

Open issues touched:

- OPEN-017: primary gameplay/runtime failure context.
- OPEN-024: gameplay sprites/enemies context.
- OPEN-001: rendering/visual context only.
- OPEN-015: crash-handler reliability context only; not modified.

New issues opened: none.  
Issues closed: none.  
Issue ledgers edited: no.  
Issues intentionally deferred: exact Genesis corrupting PC, bat damage parity if separate from lock, lizard/cave/terrain/splats/items, broader PC090OJ representation rewrite, crash-handler display cleanup.

---

## KNOWN_FINDINGS Impact

Option A - no new finding indexed.

Rationale: this evidence proves natural arcade bat-swarm/damage/death behavior and narrows the Genesis divergence window, but it does not establish a durable root mechanism. A KF update should wait until the first corrupting Genesis instruction/control path is proven.

---

## STOP

STOP triggered: **YES** for implementation/build.

Build produced: **NO**.  
Build 0216 consumed: **NO**.  
Counter impact: **none intentionally changed by this task**.  
Source/spec/tool/Makefile/ROM/invariant changes: **none**.  
Numbered artifacts deleted or overwritten: **NO**.
