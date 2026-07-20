# Cody - Build 0216 Hurry-Up Bat CPU Lock Evidence STOP

**Date:** 2026-07-19
**Type:** Hybrid evidence / implementation gate
**Accepted baseline:** Build 0215/256
**ROM inspected:** `dist/rastan-direct/rastan_direct_video_test_build_0215.bin`
**ROM SHA256:** `10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`
**Counter before/after:** `215` / `215`
**Build 0216 produced:** NO
**Scope:** Natural timed hurry-up bat swarm CPU-lock investigation. Evidence only after the exact root cause could not be proven. No source/spec/tool/Makefile/ROM/build/invariant changes. No numbered build deleted or overwritten.

## Phase 0

Relevant priors loaded from `KNOWN_FINDINGS.md`:

- KF-001 / KF-003: watchdog/timer routines are context; not enough by themselves to explain this lock.
- KF-004: runtime PC equals ROM offset for copied/patched code where applicable.
- KF-006: identity offset is a prior, but address correlation must still use generated mapping artifacts where required.
- KF-010: BG/FG staging and VBlank commit ownership.
- KF-011: arcade VBlank owns gameplay progression; Genesis VBlank is a hardware-service wrapper and tail-jumps back to the arcade VBlank body.
- KF-013: dispatch inside VBlank is expected and not itself a violation.
- KF-026 / KF-032: PC090OJ writes must route through Genesis staging/mirror paths rather than raw hardware writes.
- KF-036: mapped work-RAM base discipline.
- KF-038: long/tall PC080SN staging caveats remain context only.
- KF-063: PC090OJ expansion is safe only for validated actors.
- KF-064 / KF-065 / KF-066 / KF-067: lizard/block actor ownership, activation/progression, HUD suppression/palette, and collision/Y alignment are prior gameplay context and were not modified.

Rediscovery-hazard HIGH findings touched: KF-011, KF-013, KF-026/KF-032, KF-063, KF-064/KF-065. No contradiction detected.

Task classification: **EXTENDING** (OPEN-017 / OPEN-024 gameplay-sprite/runtime stability evidence).

Open issues touched: OPEN-017, OPEN-024, OPEN-001 context, OPEN-015 context only. Closed issues touched: none.

Architecture compliance: **CONFIRMED**. No Genesis-owned gameplay flow, actor forcing, sprite hardcoding, timer delay, bat suppression, watchdog patch, or bypass was introduced.

## Build-Specific Provenance

- `build/rastan-direct/address_map.json`: SHA256 `78eef2c5702e209c920f9ea04d62a310c7247635fe53e0b28face9f04e63d417`
- `specs/rastan_direct_remap.json`: SHA256 `8bf9962089f0d28aa16738356113cbd95d406f481f55e44aec2e2d60cbad9459`
- `build/rastan-direct/startup_common_relocations.json`: SHA256 `b924bc93b3f784ed4ae80ea3734a218fbbd9e3388de3d0df61932cf5b0a9f5f7`
- `build/rastan-direct/rastan_direct_patch_manifest.json`: SHA256 `6c5454c1938c37fbf37d7d9ed93852dfc15e721671e652225c02e3d1d19f22c1`
- `analysis/ghidra/rastan_arcade/exports/address_correlation_report.json`: SHA256 `86a9e4a1bb806fa9ad45418c4262132baf695eb41c33694f48c0569419f51dd5`

## Evidence Artifacts

Trace directory:

`states/traces/build0216_hurryup_bat_cpu_lock_20260719_184124/`

Representative files:

- `genesis_build0215_hurryup_trace.lua`
- `genesis_build0215_hurryup_trace.csv`
- `genesis_build0215_hurryup_events.log`
- `genesis_build0215_hurryup_trace_v2.lua`
- `genesis_build0215_hurryup_trace_v2.csv`
- `genesis_build0215_hurryup_events_v2.log`
- `genesis_build0215_hurryup_trace_v3.lua`
- `genesis_build0215_hurryup_trace_v3.csv`
- `genesis_build0215_hurryup_events_v3.log`
- `genesis_build0215_native_crash_boundary.cmd`
- `genesis_build0215_native_crash_boundary_notrace.cmd`
- `genesis_build0215_native_driver.lua`
- `genesis_build0215_native_driver.csv`
- `genesis_build0215_native_driver_events.log`
- `native_crash_boundary_trace.log`
- `native_full_repro_instruction_trace.log`
- `native_nt_stop_stack_illegal.bin`
- `native_nt_stop_state_illegal.bin`
- `native_nt_stop_pc090oj_illegal.bin`
- `native_full_stop_stack_address.bin`
- `genesis_build0215_scene_corruption_watch.cmd`
- `scene_corruption_stack.bin`
- `scene_corruption_state.bin`
- `scene_corruption_bss_tail.bin`
- `genesis_build0215_scene_id_corruption_watch.cmd`
- `scene_id_watch_stop_stack_illegal.bin`
- `scene_id_watch_stop_state_illegal.bin`
- `arcade_hurryup_reference_trace.lua`
- `arcade_hurryup_reference_trace.csv`
- `arcade_hurryup_reference_events.log`
- `snaps_build0215/`

Large preserved traces:

- `native_crash_boundary_trace.log`: `433499156` bytes
- `native_full_repro_instruction_trace.log`: `1537323656` bytes

No evidence artifacts were deleted.

## Address / Symbol Context

Selected symbols from `apps/rastan-direct/out/symbol.txt`:

- `genesistan_pc090oj_hook_audit_guard = 0x00072A42`
- `genesistan_current_scene_id = 0x00FFBFF0`
- `genesistan_scene_a0_lo = 0x00FFBFF2`
- `genesistan_scene_a0_hi = 0x00FFBFF6`
- `pc090oj_object_ram = 0x00FFA9FC`
- `pc090oj_candidate_bitset = 0x00FFB9FC`
- `pc090oj_mirror_dirty = 0x00FFBA20`
- `staged_sprite_sat = 0x00FFA1D4`

JSON-derived address classifications used in this task:

- `runtime_genesis_pc 0x000040E`: `preserved_vectors` crash/exception-vector region.
- `runtime_genesis_pc 0x00005F4`: `preserved_vectors` crash-renderer/minimal-halt region.
- `runtime_genesis_pc 0x00072412`, `0x00072426`, `0x000724C4`, `0x000721BA`, `0x00072DA6`: Genesis-only helper/wrapper region.
- `runtime_genesis_pc 0x0003A23E`: maps by `address_map.json` segment to `arcade_pc 0x0003A03E`.
- `runtime_genesis_pc 0x0003A27E`: maps by `address_map.json` segment to `arcade_pc 0x0003A07E`.
- `runtime_genesis_pc 0x00041FB4`: patched-site/function-body replacement area for the PC090OJ Strategy A function-body replacement target around arcade `0x041DAE`; segment-relative mapping lands at `arcade_pc 0x00041DB4` for that runtime address.
- `runtime_genesis_pc 0x0004215C`: maps by `address_map.json` segment to `arcade_pc 0x00041F5C`.
- `runtime_genesis_pc 0x08FB57A`: no exact mapping hit; outside valid ROM/runtime mapping and treated as corrupted/unreliable state.

## Original Arcade Reference Attempt

The user requested exact MAME cheat usage if needed. The local user cheat directory `/home/tighe/mame/cheat` was empty, but the repository archive `tools/mame/cheat/cheat.7z` contains an exact Rastan cheat:

- Cheat name: `Infinite Energy`
- Exact MAME action found in `rastan.xml`: `maincpu.pb@10C13A=30`

A bounded original-arcade reference script attempted to run the original `rastan` ROM with only that exact HP write and normal coin/start/input progression. It did not produce useful runtime frame evidence:

- `arcade_hurryup_reference_events.log`: `TRACE_START rom=rastan coin=true start=true b1=true`
- `arcade_hurryup_reference_trace.csv`: `0` bytes

Therefore the original arcade hurry-up/bat call path was **not established** in this task. No arcade-side control-flow proof is claimed.

## Ghidra Static Reference

The full arcade Ghidra export under `analysis/ghidra/rastan_arcade/exports/` was available and consulted for static context. Searches over exported listing/function/xref material did not produce a named or exact hurry-up/bat/swarm call path sufficient to identify the arcade writer/control path.

Result: Ghidra did not provide an exact patchable root cause in this task.

## Genesis Build 0215 Runtime Evidence

The Build 0215 Genesis run was no-cheat and stationary after reaching gameplay. Lua/video-independent sampling showed the run reached gameplay and later entered a locked/crash state.

Important samples from `genesis_build0215_hurryup_events.log`:

- Frame 600: `runtime_genesis_pc 0x00072B64`, state `2/3/0`, scene `0x0100`, HP `0x3000`, scroll X `0x0020`, scroll Y `0x0002`.
- Frame 1200: `runtime_genesis_pc 0x00040D94`, state `2/3/0`, scene `0x0100`, HP `0x3000`; stack already contains repeated `0x0003A27E / 0x2004`-style VBlank-return frames.
- Frame 2400: `runtime_genesis_pc 0x00072B64`, state `2/3/0`, scene `0x0100`.
- Frame 3600: `runtime_genesis_pc 0x000724DC`, state `2/3/0`, scene `0x0100`; actor entry e6 has `b1=0x9D`, `b5=0x0F`.
- Frame 4800: `runtime_genesis_pc 0x0007231C`, state `2/3/0`, scene `0x0100`; actor entry e8 has `b1=0x9F`, `b5=0x0F`. This is the last clearly healthy gameplay sample before the late corruption/lock window.
- Frame 6000: `runtime_genesis_pc 0x000721BA`, state `2/3/0`, sampled scene `0x00FF` (suspect/corrupt or timing artifact), actor e7 has `b1=0x9E`, `b5=0x0F`, and nonstandard represented records r48..r55 all show code `0x0269` with varied positions. This is the last pre-lock sampled state but is not classified as healthy.
- Frame 6168: stable lock/crash path sampled at `runtime_genesis_pc 0x000005F4`, `SR=0x2700`, `SP=0x00FEC048`, `A5=0x01800000`, sampled scene `0xBDE0`.

The first Lua script also reported `FIRST_LOCK_OR_CRASH frame=339`, but that was derived from a stale/nonzero crash flag and is rejected as a false early crash marker.

## Exact Lock / Exception Classification

Native MAME debugger evidence stopped at the illegal-instruction exception stub:

- Reliable stop: `runtime_genesis_pc 0x0000040E` (illegal-instruction vector stub).
- Recurring sampled stable crash/halt path: `runtime_genesis_pc 0x000005F4` (crash renderer / minimal crash path), not original gameplay code.

The exception stack at the native illegal stop begins:

```text
FEC048: 2708 01A0 0002 0004 1FB4 0180 215C 0003
FEC058: A23E 0180 0003 A27E 2004 0180 A27E 2004
```

The stacked exception PC is nonsensical/corrupted, and the stack contains repeated VBlank/RTE-looking frames such as `0x0003A27E / 0x2004`. This supports a corrupted stack/control-flow classification, but it does **not** identify the first corrupting instruction.

Do not treat formatted exception-screen PC/address/vector values as reliable here; the reliable evidence is the debugger-side illegal-stub stop and preserved stack dump.

## Paths Ruled Out Or Not Proven

- Audit guard not proven: `genesistan_pc090oj_hook_audit_guard` / `.Lhook_3ad44_audit` did not produce a captured hit; sampled audit flag stayed `0`.
- Direct scene-id corruption not proven: a broad watch around `0x00FFBFF0` caught an adjacent scene-range update, not a write corrupting `genesistan_current_scene_id` itself. The exact scene-id watch for non-`0x0100` gameplay writes did not catch before the illegal stop.
- The crash is not proven to be a raw PC090OJ hardware write in this task.
- The crash is not proven to be VBlank starvation or display timing in this task.
- The crash is not proven to be caused by the Stage 1 FG progression fix in this task.

The broad BSS watch dump shows `WRAM 0x00FFBFF0 = 0x0100` at the watch stop and adjacent range values `0x00056A22..0x000570C2`, consistent with a range/update write rather than first scene-id corruption.

## Root Cause Status

Root cause confirmed: **NO**.

The evidence narrows the failure to a late-gameplay/natural-swarm correlated corrupted control-flow or stack path that reaches the illegal-instruction vector and then the crash-renderer/minimal path. Bat-like actor entries and extra represented records are present before the lock, but the exact arcade writer/control path and first Genesis divergence are not proven.

## Implementation Boundary

Patch implemented: **NO**.

Build 0216 produced: **NO**.

No safe implementation boundary is available yet. Any change made from this evidence would be a guess or a workaround and would violate the state-causality and no-bypass rules.

Smallest responsible next diagnostic boundary:

- Capture the first stack/control-flow corruption before `runtime_genesis_pc 0x0000040E` by watching the active supervisor stack window around `0x00FEC000..0x00FEFFFF` during the late actor-swarm window, or by trapping the first jump/return to an unmapped/nonsensical PC before the exception vector runs.
- In parallel or before patch design, complete an original-arcade reference run using the exact `Infinite Energy` action `maincpu.pb@10C13A=30` to identify whether the actor entries with b1 `0x9D..0xA0` are the intended hurry-up bat/swarm path and what control path owns them.

These are recommendations only; no implementation is authorized by this evidence.

## Non-Actions

No source, spec, tool, Makefile, ROM, invariant, counter, or numbered artifact was intentionally modified. No build was run to completion for Build 0216. No existing build was deleted, overwritten, or reused.

Explicitly not performed:

- No bat suppression or delay.
- No hurry-up timer patch.
- No attack/collision skip.
- No actor seeding or forced records/SAT.
- No watchdog or crash-handler patch.
- No PC090OJ capacity increase.
- No color/palette patch.
- No cave/lizard/splat/item/terrain work.

## Open / Closed Issues Impact

Open issues touched: OPEN-017, OPEN-024, OPEN-001 context, OPEN-015 context only.

New issues opened: none.

Issues closed: none.

Issues intentionally deferred: cave cover/foreground defects, lizard cave death, lizard damage, bat palette, dropped item/splat palettes, terrain correctness, broader sprite semantics, crash-handler display reliability.

Issue ledgers were not edited because no root-cause fix or durable issue transition was proven.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed.

Rationale: the task established useful negative and boundary evidence, but not a durable root mechanism. A future KF update should wait for an exact first corrupting writer/control path or a completed arcade-vs-Genesis divergence proof.

## STOP

STOP triggered: **YES**.

Reason: exact root cause and patch-safe implementation boundary were not proven. Build 0216 was therefore not produced.
