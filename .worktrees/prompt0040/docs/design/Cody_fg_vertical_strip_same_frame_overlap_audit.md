# Cody - FG Vertical Strip Same-Frame Overlap Runtime Trace

**Date:** 2026-07-04  
**Type:** Runtime evidence / overlap classification only  
**Build:** 0138  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0138.bin`  
**ROM SHA256:** `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`  
**Evidence path:** `states/traces/fg_vertical_strip_same_frame_overlap_audit_20260704_142702/`  
**Primary prior:** `docs/design/Cody_fg_vertical_strip_current_path_audit.md`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No BlastEm. No VBlank-order, DISPLAY_ON/OFF, frame-pipeline, semantic-queue, one-frame-lag, BG, sprite, palette, or gameplay-rendering changes.

Address labels: `arcade_pc` and `runtime_genesis_pc` are code addresses. `HW_ADDRESS` is hardware-visible address. `Genesis-WRAM` is Genesis work RAM. Arcade-to-Genesis code mapping uses `build/rastan-direct/address_map.json`; no arithmetic offset is used as proof.

## 1. Executive Conclusion

**Outcome A: broad row-dirty suppression is safe for this selected producer in the observed Build 0138 frame.**

The selected FG vertical-strip producer at `arcade_pc 0x055990` / `runtime_genesis_pc 0x055B90` was reached during the short user-controlled Build 0138 MAME capture. It executed `64` times in one native VBlank frame (`1133`). Of those invocations, exactly one entered the valid 64-cell FG staging path; the other `63` were range-rejected by `genesistan_hook_tilemap_fg` and did not write FG staging.

For the valid invocation, the selected helper executed its own FG staging store at `runtime_genesis_pc 0x070532` exactly `64` times and its own `fg_row_dirty` update at `runtime_genesis_pc 0x07053E` exactly `64` times. The resulting dirty mask before the next VBlank was `0x0000000F`, and the next VBlank committed Plane-A rows `0,1,2,3`.

No other known FG/Plane-A staging-store PC executed between the selected producer's first entry and the next VBlank. The only additional high-count store PC in the selected interval was `runtime_genesis_pc 0x070640`, which is the BG blockcopy path and updates `staged_bg_buffer` / `bg_row_dirty`, not `staged_fg_buffer` / `fg_row_dirty`. Therefore the selected dirty rows were not shared with another FG producer in the observed frame.

Implementation implication for a future task, not performed here: the selected producer can keep its staging writes but suppress broad row-dirty marking for this producer and instead drive a narrow Plane-A transfer for the valid 64-cell strip shape. The future transfer must preserve current `staged_fg_buffer` state and frame timing; it should not change VBlank ordering or introduce a frame pipeline.

## 2. Capture Summary

The initial `-debugger none` attempt allowed Lua taps but did not execute the native debugscript. A smoke check showed MAME's Qt debugger did execute the native breakpoints, so the final interactive capture used MAME Genesis driver with `-debugger qt`. This was a host/debugger selection only; no ROM diagnostics or build changes were inserted.

| Item | Value |
|---|---|
| MAME mode | Genesis driver, Qt debugger, user-controlled short capture |
| Start time | `2026-07-04T18:35:54Z` |
| Stop time | `2026-07-04T18:38:09Z` |
| Lua frame range | `0..1351` |
| Native VBlank frame range | `0..1134` (`1135` entries total) |
| Final state in frame markers | `%a5@(0)=0x0002`, `%a5@(2)=0x0002`, `%a5@(4)=0x0005` |
| Clean stop | yes, MAME was stopped after user reported `SHORT FG CAPTURE COMPLETE` |

## 3. Evidence Artifacts

| Artifact | Size bytes | Purpose |
|---|---:|---|
| `native_debug_trace.log` | `381954197` | Raw native debugger trace / printf output |
| `native_events.log` | `461465` | Extracted breakpoint events (`4310` lines) |
| `fg_overlap_lua_events.log` | `28759` | Lua memory-write events; useful for bootstrap/metadata but under-reports selected stores |
| `frame_markers.log` | `205716` | Lua frame markers and state samples |
| `producer_invocation_table.tsv` | `5338` | Reduced selected-producer invocation table |
| `vblank_commit_table.tsv` | `702` | Plane-A row commits after the selected frame |
| `selected_frame_instruction_pc_counts.txt` | `592` | Native instruction-PC counts in the selected frame interval |
| `fg_overlap_reduction_summary.json` | `258` | Machine-readable reduced summary |
| `fg_overlap_ownership_summary.tsv` | generated | Ownership classification table |
| `per_frame_overlap_table.tsv` | generated | One-row selected-frame overlap table |
| `selected_frame_pc_classification.tsv` | generated | PC classification for selected interval |
| `evidence_index.tsv` | generated | Trace-file inventory |

## 4. Address Mapping

`build/rastan-direct/address_map.json` contains the selected patched site:

| Address space | Address | Mapping / role |
|---|---:|---|
| `arcade_pc` | `0x055990` | Original PC080SN FG strip producer entry |
| `runtime_genesis_pc` | `0x055B90` | `patched_site`, replacement calls `genesistan_hook_tilemap_fg` |
| `runtime_genesis_pc` | `0x0703EA` | Genesis-only helper `genesistan_hook_tilemap_fg` |
| `runtime_genesis_pc` | `0x070532` | Selected helper FG staging store |
| `runtime_genesis_pc` | `0x07053E` | Selected helper `fg_row_dirty` store |
| `runtime_genesis_pc` | `0x070640` | BG blockcopy store, excluded from FG ownership |

The selected replacement bytes in the mapping are `4eb9000703ea...`, i.e. a direct `jsr 0x0703EA` wrapper for the original `arcade_pc 0x055990` producer.

## 5. Runtime Selected-Frame Evidence

The first selected entry in the decisive interval:

```text
EVENT SELECTED_ENTRY_055B90 cyc=166472691 pc=055B92 sr=2700 a5=00FF0000 d0=00000080 d1=00002048 d5=00000000 d7=00000000 dest_fg=00C08000 strip=0000 s0=0002 s2=0002 s4=0004 sp=00FEFD16 stack0=00055B5E
```

The next VBlank entry after the selected interval:

```text
EVENT VBLANK_SERVICE_ENTRY_0700C2 cyc=170962245 pc=0700C4 sr=2604 fg_dirty=0000000F s0=0002 s2=0002 s4=0005
```

Selected segment counts from `selected_frame_instruction_pc_counts.txt`:

| Event / PC | Count | Classification |
|---|---:|---|
| `SELECTED_ENTRY_055B90` | `64` | selected producer wrapper entered |
| `SELECTED_HELPER_ENTRY_0703EA` | `64` | selected helper entered |
| `SELECTED_HELPER_VALID_DONE_070572` | `1` | one valid 64-cell strip path |
| `SELECTED_HELPER_INVALID_07057C` | `63` | range-rejected invocations |
| `SELECTED_RETURN_055B96` | `64` | selected wrapper returned |
| `runtime_genesis_pc 0x070532` | `64` | selected FG staging store |
| `runtime_genesis_pc 0x070536` | `64` | selected `fg_row_dirty` read |
| `runtime_genesis_pc 0x07053E` | `64` | selected `fg_row_dirty` store |
| `runtime_genesis_pc 0x070640` | `4096` | BG blockcopy store; excluded from FG overlap |

The one valid invocation had `dest_fg=0x00C08000`, `strip=0`, and ended with `fg_dirty_after=0x0000000F`. The remaining `63` invocations used progressively out-of-range destinations (`0x00C0C000` through `0x00D04000`) and were rejected before FG staging writes.

## 6. VBlank Commit Association

The next VBlank committed exactly the four selected rows:

| Native frame | Row | VRAM target | Dirty mask at row start | First word |
|---:|---:|---:|---:|---:|
| `1134` | `0` | `0xE000` | `0x0000000F` | `0x60D8` |
| `1134` | `1` | `0xE080` | `0x0000000E` | `0x60DC` |
| `1134` | `2` | `0xE100` | `0x0000000C` | `0x60E0` |
| `1134` | `3` | `0xE180` | `0x00000008` | `0x60E4` |

Current row-commit cost attributable to the selected producer in this observed frame:

| Quantity | Value |
|---|---:|
| Valid selected strip invocations | `1` |
| Logical cells written by selected valid strip | `64` |
| Current dirty rows marked | `4` (`0..3`) |
| Current Plane-A words committed | `256` (`4 rows * 64 words`) |
| Other FG producers sharing those rows before VBlank | `0` |
| Other BG producers in interval | yes, `0x070640`, but BG-only and excluded |

## 7. Overlap Classification

| Question | Result | Evidence |
|---|---|---|
| Did the selected producer run? | yes | `64` `SELECTED_ENTRY_055B90` events |
| Did a valid selected strip write FG staging? | yes | `0x070532` count `64`; `SELECTED_HELPER_VALID_DONE_070572` count `1` |
| Which FG rows did it dirty? | rows `0..3` | `fg_dirty=0x0000000F`; next VBlank row commits |
| Were those rows dirty before the selected producer? | no | first selected helper entry observed with `fg_dirty=0x00000000` |
| Did other known FG staging store PCs execute before next VBlank? | no | selected-frame PC classification |
| Were any same-row overlaps disjoint? | no | no other FG row owner observed |
| Were any same-row overlaps conflicting? | no | no other FG row owner observed |
| Were selected cells repeatedly overwritten by selected producer in the same frame? | no evidence of repeated selected-cell ownership | one valid 64-cell path; range-rejected calls did not write |
| Did VBlank row commit happen after selected dirtying? | yes | rows `0..3` committed in native frame `1134` |

Percentages for the observed selected frame:

| Metric | Value |
|---|---:|
| Selected rows exclusively owned | `4/4 = 100%` |
| Selected rows shared with other FG producers | `0/4 = 0%` |
| Conflicting same-row FG overlap | `0%` |
| Current row-commit amplification vs selected logical cells | `4.0x` |

## 8. CLEAR Result For Outcome B Dependency

The prior current-path audit left one dependency unresolved: whether `runtime_genesis_pc 0x055B90` shares same-frame dirty rows with other FG producers before VBlank.

This trace resolves it for the captured Build 0138 gameplay frame:

- The selected producer's valid strip wrote `64` FG staging cells.
- Those stores marked rows `0..3` dirty.
- No other FG/Plane-A staging writer touched those rows before the next VBlank.
- The next VBlank committed rows `0..3`.

Therefore the observed selected frame supports **Outcome A**, not Outcome B.

## 9. Safe Future Suppression Rule

No implementation was performed in this task. The evidence supports the following future narrow implementation rule for this producer:

- Keep `staged_fg_buffer` writes for `runtime_genesis_pc 0x055B90` intact, preserving readback/current staging state.
- Suppress only this producer's broad `fg_row_dirty` marking for the valid strip path.
- Present the selected operation with a narrow Plane-A transfer covering the exact valid strip output shape: `64` composed cells, spanning current rows `0..3`, rather than committing all `4 * 64 = 256` row words.
- Do not suppress or alter dirty bits from any other FG producer.
- Do not change VBlank order, DISPLAY_ON/OFF timing, frame pipeline, semantic queueing, or staging lifetime.
- Do not apply this conclusion to other FG producers without separate same-frame ownership evidence.

Implementation is now safely placeable for this selected producer's broad-row-dirty suppression/narrow-transfer path, subject to the above constraints. It is not a license for a global FG row-dirty policy change.

## 10. Limitations

- The Lua full-buffer write tap under-reported the selected stores: `mame_lua_metadata.log` still reports `selected_store_count=0`. That reflects the Lua tap path, not the native trace result.
- Old/new per-cell values for selected staging writes were therefore not captured by Lua.
- The ownership conclusion does not depend on those old/new values: the native debugger trace distinguishes writer PCs, proves selected store execution count, proves the absence of other known FG store PCs in the selected interval, and associates the resulting dirty rows with the next VBlank commit.
- The conclusion applies to the captured Build 0138 short gameplay window only. It does not prove later-stage or rare-operation ownership.

## 11. Non-Actions

No source code, specs, tools, Makefiles, ROM artifacts, build artifacts, invariants, bookmarks, BlastEm state, VBlank ordering, DISPLAY_ON/OFF timing, frame pipeline, semantic queue, BG path, sprite path, palette path, or gameplay rendering logic was changed.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 / PC080SN optimization context.
- Context: the previous Outcome B dependency in `docs/design/Cody_fg_vertical_strip_current_path_audit.md` is resolved for the selected producer and observed frame.
- New issues opened: NONE.
- Issues closed: NONE.
- Closed issues touched: NONE.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update. This is implementation-enabling runtime evidence for one selected producer, not a new durable architectural finding by itself. A finding update can wait for any production implementation or broader generalized policy.

## STOP

STOP triggered: NO.

Reason: The decisive runtime measurement reached the selected producer, distinguished selected FG writer PCs from other traffic, associated dirty rows with VBlank row commits, and resolved the same-frame overlap dependency. The Lua old/new tap limitation is recorded but does not block the ownership classification.
