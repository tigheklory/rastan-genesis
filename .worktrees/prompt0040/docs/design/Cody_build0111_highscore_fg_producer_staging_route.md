# Cody — Build 0111 High-Score FG Producer Staging Route

**Date:** 2026-06-28
**Type:** Implementation + build + runtime validation
**Final ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0111.bin`
**SHA256:** `3e8977513586231bf83636ba9ce9b65852f2fe8f94f8772ad9fa7fa493442e23`
**Scope:** Implement the `0x03C5FE` high-score FG producer staging route from `docs/design/Andy_03C5FE_highscore_fg_staging_route_design.md`. No zero-table data changes. No sprite/window/HUD changes. No changes to `0x03C4E2`, `0x03BD48`, `0x03AD06`, or other OPEN-018/Class-B sites.

## Phase 0

Read before implementation:

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md` / OPEN-018 and KF-032 context
- `OPEN_ISSUES.md`
- latest `AGENTS_LOG.md` tail
- `docs/design/Andy_03C5FE_highscore_fg_staging_route_design.md`
- prior Build 0109 evidence docs for `0x03C5FE` / `0x00C09374`

Classification: **EXTENDING** OPEN-018 / KF-032. OPEN-001 and OPEN-005 are context only. OPEN-015 untouched.

Architecture compliance: the arcade high-score producer remains the program. The new Genesis helper is a function-level hardware-service replacement for the PC080SN FG producer entry and routes its tilemap output through the existing FG staging helper.

## Address Mapping

Address correlations were checked through `build/rastan-direct/address_map.json`.

- `runtime_genesis_pc 0x03C5FE` is now a `patched_site` for `arcade_pc 0x03C3FE..0x03C406`.
- The preserved post-replacement body/table region is represented by the following `arcade_copy` segment: `runtime_genesis_pc 0x03C606..0x03C6D2`, `arcade_pc 0x03C406..0x03C4D2`, `identity_offset=512`.
- The descriptor table remains at `runtime_genesis_pc 0x03C654` within that preserved `arcade_copy` segment; it corresponds to `arcade_pc 0x03C454` by the JSON segment row.

## Implementation

Changed `apps/rastan-direct/src/tilemap_hooks.s`:

- Added exported helper `genesistan_hook_highscore_fg_producer`.
- The helper reimplements the original descriptor loop:
  - saves original mode from input `D0`
  - indexes preserved table at `runtime_genesis_pc 0x03C654`
  - computes `A1 = HW_ADDRESS 0x00C08000 + dest_offset`
  - reads source bytes from the shifted high-ROM source base `0x0010C068 + src_offset`
  - preserves the original `0x3F -> 0x274B` and `0x21 -> 0x2744` substitutions
  - preserves signed-byte space mode (`mode < 0 -> code 0x0020`)
  - calls `genesistan_hook_tilemap_fg_fill` with `A0=dest`, `D0=(attr<<16)|code`, `D1=1`
  - advances destination by 4 bytes per original cell

Changed `specs/rastan_direct_remap.json`:

```json
{
  "arcade_pc": "0x03C3FE",
  "original_bytes": "3E3C000034000240",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_highscore_fg_producer}4E75"
}
```

This is byte-neutral at the arcade producer entry: original 8 bytes -> `JSR helper; RTS` 8 bytes. The descriptor table at `runtime_genesis_pc 0x03C654` is not modified.

Changed canonical invariants in both postpatch verification tools:

- `opcode_replace` count: `102 -> 103`
- `total_genesis_bytes_covered`: `0x17CDE4 -> 0x17CE4C`
- Mechanical delta: `+0x68` bytes from the new helper body

## Source-Base Correction

The first successful artifact, Build 0110 (`15bd2250ff40134bb4ca5c305598aee584e17e7592bafdcbe8bda694bdde0ffd`), exposed a validation mismatch: the helper initially used the stale literal source base `0x0010C000`, which read shifted high-ROM bytes (`0x44,0x11,0x11...`) instead of the Build 0109 producer stream (`0x18,0x01,0x34...`).

The cause was layout/order, not producer semantics: the new helper adds `+0x68` bytes before the high-ROM source region, so the source stream used by the copied producer is at `runtime_genesis_pc 0x0010C068 + src_offset` in this canonical layout. Build 0111 corrects the helper constant to `ARCADE_HIGHSCORE_SOURCE_BASE = 0x0010C068` and matches Build 0109 logical cell output.

## Static Verification

Build 0111 disassembly:

```asm
03c5fe: 4eb9 0007 07a0  jsr 0x707a0
03c604: 4e75            rts
```

Helper excerpt:

```asm
0707a0: movem.l d0-a6,-(sp)
0707a4: move.w  d0,d2
0707a6: andi.w  #0x007f,d0
0707aa: move.w  d0,d5
0707ac: mulu.w  #6,d0
0707b0: lea     0x3c654,a0
0707bc: movea.w 2(a0),a1
0707c0: adda.l  #0x00c08000,a1
0707c6: movea.w 4(a0),a2
0707ca: adda.l  #0x0010c068,a2
...
0707f8: bsr.w   0x7065e ; genesistan_hook_tilemap_fg_fill
```

ROM byte checks:

- `runtime_genesis_pc 0x03C5FE`: `4eb9000707a04e75...`
- `runtime_genesis_pc 0x03C654`: descriptor table preserved, begins `000313740157...`
- Old body bytes remain in dead body after the wrapper (`0x03C62A`, `0x03C646`, `0x03C64A`) but are not reached.

## Build Verification

Final release:

- Build: `0111`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0111.bin`
- SHA256: `3e8977513586231bf83636ba9ce9b65852f2fe8f94f8772ad9fa7fa493442e23`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Rolling SHA: same as numbered
- `cmp`: byte-identical
- `GATE_PASS`: yes
- Release trace: `states/traces/rastan_direct_video_test_build_0111_mame_30s_20260628_105214/`

## Runtime Validation

Primary trace:

`states/traces/build_0111_highscore_fg_producer_staging_route_20260628_105240/`

Files:

- `highscore_fg_route.cmd`
- `native_debug_trace.log`
- `events_only.log`
- `route_analysis.json`
- `route_analysis.md`
- `mame_stdout.log`
- `mame_stderr.log`

Staged-cell confirmation trace:

`states/traces/build_0111_highscore_fg_producer_staging_cells_20260628_105419/`

Results:

- `CALL_3C5FE_3B900`: 5
- `HOOK_ENTRY_707A0`: 5
- `HOOK_TABLE_707B8`: 5
- `HOOK_STAGE_CALL_707F8`: 15
- `UNEXPECTED_RAW_ATTR_3C62A`: 0
- `UNEXPECTED_RAW_CODE_3C646`: 0
- `UNEXPECTED_RAW_SPACE_3C64A`: 0
- `HIGH_TAIL_DONE_03AD52`: 1, with `s0=0002`, `s2=0000`, `s4=0002`, `cnt=00A0` in the primary trace

Build 0111 logical output matches Build 0109 raw output for all 15 cells:

| idx | cell | HW dest | source byte | Build 0109 raw code | Build 0111 hook code |
|---:|---:|---|---:|---:|---:|
| 0 | 0 | `0x00C09374` | `0x18` | `0x0018` | `0x0018` |
| 0 | 1 | `0x00C09378` | `0x01` | `0x0001` | `0x0001` |
| 0 | 2 | `0x00C0937C` | `0x34` | `0x0034` | `0x0034` |
| 1 | 0 | `0x00C09574` | `0x66` | `0x0066` | `0x0066` |
| 1 | 1 | `0x00C09578` | `0x84` | `0x0084` | `0x0084` |
| 1 | 2 | `0x00C0957C` | `0x00` | `0x0000` | `0x0000` |
| 2 | 0 | `0x00C09774` | `0x13` | `0x0013` | `0x0013` |
| 2 | 1 | `0x00C09778` | `0x18` | `0x0018` | `0x0018` |
| 2 | 2 | `0x00C0977C` | `0x46` | `0x0046` | `0x0046` |
| 3 | 0 | `0x00C09974` | `0x00` | `0x0000` | `0x0000` |
| 3 | 1 | `0x00C09978` | `0x01` | `0x0001` | `0x0001` |
| 3 | 2 | `0x00C0997C` | `0x34` | `0x0034` | `0x0034` |
| 4 | 0 | `0x00C09B74` | `0x14` | `0x0014` | `0x0014` |
| 4 | 1 | `0x00C09B78` | `0x00` | `0x0000` | `0x0000` |
| 4 | 2 | `0x00C09B7C` | `0x00` | `0x0000` | `0x0000` |

The second trace directly observed 15 high-score producer staged writes at the corresponding `staged_fg_buffer` addresses during the producer pass. The staged words are LUT-mapped Genesis nametable words, so they are not expected to equal the raw PC080SN codes byte-for-byte.

## BlastEm Smoke Check

A BlastEm debug-mode smoke run was launched with Build 0111. Captured output did not contain the prior strict-target failure string (`Illegal write to HV Counter port 8`) or a `0x00C09374` raw-write failure. BlastEm/WSL GUI timeout behavior did not produce a clean automatic exit, so this is recorded as a smoke check rather than a definitive long-run certification.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-018: advanced; the `0x03C5FE` high-score FG producer raw-write surface is now routed through FG staging and validated for the captured high-score pass. Do not close OPEN-018 here because other scoped raw-write classes may remain open.
- OPEN-001 / OPEN-005: context only.
- OPEN-015: untouched.
- KNOWN_FINDINGS: Option A for this task; no canonical update applied here.

## STOP

STOP triggered: **NO** for the final Build 0111 implementation.

Build 0110 is superseded by Build 0111 because validation caught the stale source-base literal before finalizing the task.
