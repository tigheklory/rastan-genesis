# Cody - Build 0242 Selector-0 Route Fix -> Build 0243

**Agent:** Cody  
**Date:** 2026-07-28  
**Classification:** EXTENDING OPEN-001 / native PC080SN Plane A selector-0 route  
**Accepted input candidate:** Build 0242, `dist/rastan-direct/rastan_direct_video_test_build_0242.bin`, SHA `823c3ab0021111265070063beb01083a0665decce894933ff1375915132932c2`  
**Produced candidate:** Build 0243, `dist/rastan-direct/rastan_direct_video_test_build_0243.bin`, SHA `9c39607a4964fb0f69e9ea91fdcc2a839427a90dbc190fc1a5e2762f55a39155`, size `1588444`, counter `243`

## Phase 0

Relevant priors: KF-010/KF-011 for staged rendering and VBlank ownership, KF-072 / `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` for native replacement discipline, and the Build 0240-0242 selector-0 documents/logs for the current Plane A route. Rediscovery hazard touched: HIGH for PC080SN Plane A staging and native helper route. Task classification: EXTENDING. Open issues touched: OPEN-001. Open issues context only: broader Plane B, selector-1/2, PC090OJ, rope/collision gameplay defects. Contradiction of CONFIRMED/STRONG finding: NONE.

Architecture compliance: CONFIRMED. The arcade dispatch remains the program. The Build 0242 byte-neutral route preserves the copied-program `BSR.W` at `runtime_genesis_pc 0x055B50`; the patched strip-tail body at `runtime_genesis_pc 0x055B68` jumps to a Genesis helper that returns through RTS to the original BSR continuation. The helper writes staging/collision state and never writes VDP directly.

## Evidence Preserved

Build 0242 source snapshot and production diff were preserved before this fix under:

- `states/traces/build0242_selector0_route_fix_20260728_173622/source_snapshot_0242/`
- `states/traces/build0242_selector0_route_fix_20260728_173622/build0242_current_production_diff_vs_git.diff`

Focused evidence and regenerated raw debug logs are under:

- `states/traces/build0242_selector0_route_fix_20260728_173622/evidence/`
- `build0242_route_trace_debug_regenerated.log`
- `build0242_srcslot_watch_debug_regenerated.log`
- `build0243_route_trace_debug.log`
- `build0243_srcslot_watch_debug.log`
- `build0243_route_trace_summary.txt`
- `build0243_srcslot_watch_summary.txt`

Numbered artifacts preserved:

- Build 0241 SHA `42fdc60d988c2bb2753ac0cf1b2033103c13a7e5402e0bb272ef3377aff74c47`
- Build 0242 SHA `823c3ab0021111265070063beb01083a0665decce894933ff1375915132932c2`
- Build 0243 SHA `9c39607a4964fb0f69e9ea91fdcc2a839427a90dbc190fc1a5e2762f55a39155`

## Static Route Proof

Final ROM disassembly proves the byte-neutral route remains intact:

```asm
runtime_genesis_pc 0x055B48: cmpiw #0,%a5@(4264)
runtime_genesis_pc 0x055B50: bsrw 0x55b68
runtime_genesis_pc 0x055B68: jmp 0x704a4
runtime_genesis_pc 0x0704A4: genesistan_hook_tilemap_plane_a_selector0_native
runtime_genesis_pc 0x070602: rts
```

`address_map.json` resolves:

- `runtime_genesis_pc 0x055B48` / `0x055B50`: `arcade_copy`, mapped from `arcade_pc 0x055946..0x055968`.
- `runtime_genesis_pc 0x055B68`: `patched_site`, mapped from `arcade_pc 0x055968..0x05598E`, origin `opcode_replace`.
- `runtime_genesis_pc 0x0704A4`, `0x070602`, `0x071E14`: `genesis_only` helper range.

The audited original 38-byte span at `arcade_pc 0x055968..0x05598D` is the selector-0 strip-tail body. Build 0242/0243 replace that body byte-neutrally with the `JMP` route; the original caller/continuation around `0x055B50 -> 0x055B54` remain copied-program code.

## Build 0242 Runtime Failure

Regenerated Build 0242 route trace summary:

- `DISPATCH_55B48`: `4`
- `BSR_SEL0_55B50`: `4`
- `ROUTE_ENTRY_55B68`: `4`
- `HELPER_ENTRY_704A4`: `4`
- `RETURN_CONT_55B54`: `4`
- `FILL_COUNT_WRITE`: `6`
- `COLLISION_WRITE`: `4112`, including `16` helper writes reported at `runtime_genesis_pc 0x070598`
- `FG_STAGE_WRITE`: `16430`, including `128` helper writes reported at `runtime_genesis_pc 0x0705CE`
- `EXCEPTION_COMMON`: `1`

This resolves the prior contradiction: the helper did run. The earlier zero helper counters were a verification/trace-target artifact, not runtime truth.

Regenerated Build 0242 source-slot watch summary:

- `SRC_SLOT8_9_WRITE`: `20`
- Source-slot writes by selector-0 helper: `runtime_genesis_pc 0x070598`, count `4`
- Ring-advance source-slot writes: `runtime_genesis_pc 0x055AD2`, count `4`
- `EXCEPTION_COMMON`: `1`

The Build 0242 watch proves the selector-0 helper wrote into `Genesis-WRAM 0xFF1020..0xFF1027`, corrupting descriptor source slots 8/9 before descriptor rebuild. After ring advance, descriptor rebuild entered with corrupted pointers and the exception common handler captured `frame_pc=0x00010205` with `a4=0x00010205`.

## Root Cause

The selector-0 helper attempted to write collision cells with this source form:

```asm
move.w %d2, 0x1E00(%a5,%d3.w)
```

On 68000 indexed addressing, the brief extension displacement is 8-bit, not 16-bit. The intended `0x1E00` displacement did not produce a safe indexed write to `0xFF1E00 + d3`; high logical rows instead wrapped into nearby `a5`-relative WRAM, including descriptor rebuild/source table space at `0xFF1000..`. The downstream descriptor rebuild crash was a consequence of this source-slot corruption, not a failed route or missing helper invocation.

First exact divergence: Build 0242 `genesistan_hook_tilemap_plane_a_selector0_native` collision store at reported `runtime_genesis_pc 0x070598` corrupts descriptor source slots. Original/correct behavior is to write collision cells into the collision map, not into descriptor source slots.

## Fix Implemented

Fix class: bounded native helper encoding correction.

Changed [tilemap_hooks.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/tilemap_hooks.s):206 to use an explicit collision-map base register:

```asm
movea.l #ARCADE_COLLISION_MAP_BASE, %a6
move.w  %d2, 0(%a6,%d3.w)
lea     staged_fg_buffer, %a6
```

The local cell-loop branch was widened from `blo.s` to `blo.w` because the corrected store sequence grew the loop body beyond the short-branch range. No control-flow condition changed.

Changed canonical coverage constants in:

- [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py):78
- [verify_canonical_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/verify_canonical_rom.py):90

Coverage moved from `0x183CD0` to `0x183CDC`; opcode replacement site count remains `216`.

## Build 0243 Verification

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result:

- `GATE_PASS`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0243.bin`
- SHA: `9c39607a4964fb0f69e9ea91fdcc2a839427a90dbc190fc1a5e2762f55a39155`
- Size: `1588444`
- Counter: `243`
- Rolling artifact SHA matches numbered artifact.
- Numbered Builds 0241/0242/0243 are present; no numbered artifact was deleted or overwritten.

Final ROM disassembly around the fixed store:

```asm
runtime_genesis_pc 0x070594: moveal #0x00ff1e00,%fp
runtime_genesis_pc 0x07059A: movew %d2,%fp@(0,%d3:w)
runtime_genesis_pc 0x07059E: lea 0xff70ea,%fp
runtime_genesis_pc 0x0705EC: bcsw 0x7056c
runtime_genesis_pc 0x070602: rts
```

Built-in 30-second trace:

- `states/traces/rastan_direct_video_test_build_0243_mame_30s_20260728_180023/`
- `frames=1798`
- `fg_cwindow_live count=0`
- no unmapped hardware summary hits reported by the trace summary.

Focused Build 0243 route trace summary:

- `DISPATCH_55B48`: `64`
- `BSR_SEL0_55B50`: `64`
- `ROUTE_ENTRY_55B68`: `64`
- `HELPER_ENTRY_704A4`: `64`
- `HELPER_RTS_70602`: `64`
- `RETURN_CONT_55B54`: `64`
- `FILL_COUNT_WRITE`: `67`
- `COLLISION_WRITE`: `8192`, including `4096` helper writes reported at `runtime_genesis_pc 0x07059E`
- `FG_STAGE_WRITE`: `65454`, including `2048` helper writes reported at `runtime_genesis_pc 0x0705D8`
- actual `EXCEPTION_COMMON` events: `0`

Focused Build 0243 source-slot watch summary:

- `RING_ENTRY_55AA2`: `64`
- `ADVANCE_SRC_55AC6`: `16`
- `REBUILD_CALL_55B04`: `17`
- `REBUILD_ENTRY_71E08`: `17` (actual PC after breakpoint is `0x071E16`; symbol entry is `0x071E14`)
- `SRC_SLOT8_9_WRITE`: `76`
- Source-slot write PCs: `0x03A4D4`, `0x03B102`, `0x050548`, `0x050554`, and legitimate ring advance at `0x055AD2`.
- Source-slot writes by selector-0 helper: `0`
- actual `EXCEPTION_COMMON` events: `0`

## Open / Closed Issues Impact

Open issues touched: OPEN-001.  
New issues opened: none.  
Issues closed: none.  
Intentionally deferred: Plane B, selector-1/2 final native tails, broader gameplay visual correctness, rope/collision behavior, PC090OJ work, and non-selector-0 rendering defects.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This task fixes a Build 0242 implementation encoding defect and validates the existing selector-0 route; it does not establish a new durable architecture finding beyond the existing native replacement/Plane A work.

## STOP Status

STOP not triggered. The first divergence was exact, the correction was bounded, Build 0243 was produced, and focused validation proved the corrupted source-slot writes no longer occur.
