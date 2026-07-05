# Cody - PC080SN Operation Census from User-Controlled Arcade MAME Capture

**Date:** 2026-07-04  
**Type:** Evidence-only runtime census + static ownership correlation  
**Arcade runtime:** original MAME `rastan` / `Rastan (World Rev 1)`  
**MAME executable:** `/usr/games/mame` (`0.276`)  
**Trace directory:** `states/traces/pc080sn_operation_census_20260704_132001/`  
**Genesis comparison baseline:** Build 0138 (`dist/rastan-direct/rastan_direct_video_test_build_0138.bin`, SHA `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`)  
**Scope:** Evidence and analysis only. No production source/spec/tool/Makefile/ROM/build changes. No diagnostics inserted into a ROM. No BlastEm work.

## Executive Conclusion

The capture is usable for a preliminary PC080SN operation census and for selecting a defensible first replacement target, with one important coverage limitation: the user-controlled gameplay covers startup/frontend and part of Stage 1 only, not a complete stage. The later attract-mode activity is preserved and summarized separately, but is not mixed into the manual-gameplay frequency ranking.

The dominant PC080SN gameplay traffic observed in the partial Stage 1 window is vertical strip streaming into PC080SN tile RAM:

| Manual gameplay family | Raw writes | Manual gameplay pct | Primary observed arcade PCs |
|---|---:|---:|---|
| `FG_VERTICAL_STRIP_STREAM` | 163,072 | 36.273% | `arcade_pc 0x0559B8/0x055A06` |
| `BULK_SCENE_FILL_CLEAR_MIRROR` | 129,200 | 28.739% | `arcade_pc 0x03AD48` |
| `BG_VERTICAL_STRIP_STREAM` | 106,368 | 23.660% | `arcade_pc 0x055C80/0x055C94` |
| `SCROLL_LATCH_X/Y` combined | 48,788 | 10.852% | `arcade_pc 0x055ABA/0x055AC2/0x055ACA/0x055AD2` plus title scroll clears |
| Other / unknown tile writes | 193 | 0.043% | sparse sites |

**Recommended first implementation target:** operation-level buffering for the gameplay vertical-strip stream family, starting with the already-known `arcade_pc 0x055968/0x055990` producer path that emits the captured `0x0559B8/0x055A06` writes. This is the largest manual-gameplay PC080SN traffic family, has a clear routine-level boundary already present in `specs/rastan_direct_remap.json`, writes complete tile state as attribute/code word pairs, and is safer than scene-clear/fill because it targets normal-frame streaming rather than broad scene lifecycle behavior.

**Second-best candidate:** the BG vertical strip stream path around `arcade_pc 0x055C7A` / observed write PCs `0x055C80/0x055C94`. It covers 23.660% of partial Stage 1 writes and appears semantically similar, but Build 0138 currently maps these PCs as `arcade_copy`, so it needs a tighter caller/entry audit before implementation.

## Primary Playthrough Coverage

Tighe reported that the run included manual play from boot through the frontend and into the first zone of Stage 1, then post-gameplay attract-mode activity. The user did not complete the full stage because keyboard play was too difficult, and the XInput controller was not recognized through WSL.

Trace-inferred segmentation, corroborated by that ordering:

| Segment | Frames | Approx time @60fps | Role | Use in ranking |
|---|---:|---:|---|---|
| Frontend/startup | `0..1439` | 24.00s | boot/title/story/coin/start lead-in | frontend only |
| Manual stage-load boundary | `1440..1499` | 1.00s | first Stage 1 load/transition | stage-load evidence |
| Manual gameplay, partial Stage 1 | `1500..15179` | 228.00s | user-controlled first-zone gameplay | primary gameplay ranking |
| Post-gameplay attract | `15180..24425` | 154.10s | attract/frontend/automated activity after manual session | supplementary only |

The manual gameplay window is long enough to identify dominant normal-frame PC080SN operation families and a first replacement target. It is not sufficient to claim comprehensive rare-operation, later-stage, or end-of-stage coverage.

## Capture Completeness

- Raw PC080SN write events: `775,009`
- Frame markers: `24,428`
- Raw trace size: `121,822,368` bytes
- MAME runtime metadata: `final_frame=24428`, `final_seq=775009`
- MAME stdout: `Average speed: 99.52% (406 seconds)`
- Trace stop status: clean stop; metadata contains `stop_time=2026-07-04T17:29:16Z`

The trace appears complete for the captured session. It is incomplete relative to the originally requested complete-stage coverage.

## PC080SN Memory And Register Ranges

Captured ranges:

| HW address range | Runtime meaning |
|---|---|
| `HW_ADDRESS 0x00C00000..0x00C03FFF` | PC080SN tile RAM page 0, captured here as BG page 0 |
| `HW_ADDRESS 0x00C04000..0x00C07FFF` | PC080SN tile RAM page 1 |
| `HW_ADDRESS 0x00C08000..0x00C0BFFF` | PC080SN tile RAM page 2, captured here as FG page 2 |
| `HW_ADDRESS 0x00C0C000..0x00C0FFFF` | PC080SN tile RAM page 3 |
| `HW_ADDRESS 0x00C20000..0x00C20003` | PC080SN Y scroll registers |
| `HW_ADDRESS 0x00C40000..0x00C40003` | PC080SN X scroll registers |
| `HW_ADDRESS 0x00C50000..0x00C50003` | PC080SN control registers |

## Operation-Family Definitions

- `FG_VERTICAL_STRIP_STREAM`: complete tile-state writes to FG C-window page 2, alternating attr/code words; observed address stride is `0x100` between same-half writes, meaning one logical column/strip across rows.
- `BG_VERTICAL_STRIP_STREAM`: same pattern into BG page 0.
- `BULK_SCENE_FILL_CLEAR_MIRROR`: broad longword fill/copy helper at `arcade_pc 0x03AD44`, observed via post-instruction PC `0x03AD48`, used for broad scene/plane lifecycle clears or fills.
- `FULL_PLANE_CLEAR_OR_INIT`: PC080SN C-window clear loop at `arcade_pc 0x0561B6`, observed via `0x0561D0/0x0561D2` in original arcade trace.
- `TITLE_OR_FRONTEND_BG_ROW_COPY`: block-copy engine at `arcade_pc 0x05A4DE`, observed via `0x05A4E6/0x05A4E8`; writes adjacent attr/code words across rows/rectangles.
- `FG_TEXT_GLYPH_STREAM`: title/text/number renderer attr/code pair writers (`0x03BB48`, `0x03C2E2`, related PCs).
- `BG_VERTICAL_COLUMN_STREAM`: gameplay/attract BG column fill/update at `arcade_pc 0x0560DA`, observed via `0x0560FC`.
- `BG_BLOCK_OR_COLUMN_UPDATE`: shared text/block update path at `arcade_pc 0x0563A6`, observed via `0x0563BC/0x0563C2`.
- `SCROLL_LATCH_X/Y`: PC080SN scroll register writes.
- `CONTROL_LATCH`: PC080SN control register writes.
- `OTHER_TILE_OR_UNKNOWN`: sparse writes whose operation family is not safely identified from this capture alone.

## Runtime Frequency Tables

### Manual Gameplay, Partial Stage 1

| Family | Raw writes | Pct | Notes |
|---|---:|---:|---|
| `FG_VERTICAL_STRIP_STREAM` | 163,072 | 36.273% | dominant observed normal gameplay tile traffic; stride `0x100` between same-half writes |
| `BULK_SCENE_FILL_CLEAR_MIRROR` | 129,200 | 28.739% | scene/lifecycle broad operations during gameplay window; not normal per-frame streaming |
| `BG_VERTICAL_STRIP_STREAM` | 106,368 | 23.660% | second dominant normal gameplay tile streaming family |
| `SCROLL_LATCH_Y` | 24,394 | 5.426% | frequent scroll register traffic |
| `SCROLL_LATCH_X` | 24,394 | 5.426% | frequent scroll register traffic |
| `TITLE_OR_FRONTEND_BG_ROW_COPY` | 1,088 | 0.242% | small frontend-style block copies during gameplay window |
| `FG_TEXT_GLYPH_STREAM` | 847 | 0.188% | text/number glyph writes |
| `OTHER_TILE_OR_UNKNOWN` | 193 | 0.043% | unknown residual traffic |
| `CONTROL_LATCH` | 13 | 0.003% | rare control register writes |

### Frontend / Startup

| Family | Raw writes | Pct |
|---|---:|---:|
| `BULK_SCENE_FILL_CLEAR_MIRROR` | 39,184 | 67.646% |
| `BULK_SCENE_WORD_COPY` | 16,384 | 28.285% |
| `TITLE_OR_FRONTEND_BG_ROW_COPY` | 1,792 | 3.094% |
| `FG_TEXT_GLYPH_STREAM` | 526 | 0.908% |
| Other / scroll / control | 39 | 0.067% |

### Manual Stage-Load Boundary

| Family | Raw writes | Pct |
|---|---:|---:|
| `BULK_SCENE_FILL_CLEAR_MIRROR` | 15,200 | 98.115% |
| Scroll latches | 172 | 1.110% |
| Text/other/control | 120 | 0.775% |

### Post-Gameplay Attract, Supplementary Only

| Family | Raw writes | Pct |
|---|---:|---:|
| `BULK_SCENE_FILL_CLEAR_MIRROR` | 83,600 | 33.172% |
| `FG_VERTICAL_STRIP_STREAM` | 54,016 | 21.433% |
| `FULL_PLANE_CLEAR_OR_INIT` | 49,152 | 19.503% |
| `BG_VERTICAL_STRIP_STREAM` | 31,104 | 12.342% |
| Scroll latches | 19,376 | 7.688% |
| `BG_VERTICAL_COLUMN_STREAM` | 5,900 | 2.341% |
| `TITLE_OR_FRONTEND_BG_ROW_COPY` | 3,664 | 1.454% |
| `BG_BLOCK_OR_COLUMN_UPDATE` | 2,900 | 1.151% |
| `FG_TEXT_GLYPH_STREAM` | 2,082 | 0.826% |
| Other/control | 229 | 0.091% |

## Per-Routine Producer Index

All Genesis mappings below are from `build/rastan-direct/address_map.json`, not arithmetic offsets.

| Family | Arcade routine / observed PCs | runtime_genesis_pc mapping | Current Build 0138 handling |
|---|---|---|---|
| `FG_VERTICAL_STRIP_STREAM` | entry path `arcade_pc 0x055968/0x055990`; observed write PCs `0x0559B8/0x055A06` | entries map to `0x055B68/0x055B90` patched sites; observed inner PCs map to `0x055BB8/0x055C06` arcade-copy bytes but are entry-bypassed by replacement | function-level hooks `genesistan_hook_tilemap_plane_a` / `genesistan_hook_tilemap_fg`; likely still per-cell/row dirty staging, not operation-buffered |
| `BG_VERTICAL_STRIP_STREAM` | `arcade_pc 0x055C7A`; observed write PCs `0x055C80/0x055C94` | `0x055E7A/0x055E80/0x055E94`, `arcade_copy` | no matching opcode_replace found for `0x055C7A`; candidate compatibility/raw path risk requires follow-up before implementation |
| `BULK_SCENE_FILL_CLEAR_MIRROR` | `arcade_pc 0x03AD44`, observed `0x03AD48` | `0x03AF44/0x03AF48`, patched site | `genesistan_hook_3ad44_dispatch`, polymorphic PC090OJ/tilemap dispatch |
| `SCROLL_LATCH_X/Y` | `arcade_pc 0x055AB4`, observed `0x055ABA/0x055AC2/0x055ACA/0x055AD2` | `0x055CB4..0x055CD2`, patched site | direct rewrite to `staged_scroll_*` variables |
| `FULL_PLANE_CLEAR_OR_INIT` | `arcade_pc 0x0561B6`, observed `0x0561D0/0x0561D2` | `0x0563B6/0x0563D0/0x0563D2`, patched site | `genesistan_hook_cwindow_clear` |
| `TITLE_OR_FRONTEND_BG_ROW_COPY` | `arcade_pc 0x05A4DE`, observed `0x05A4E6/0x05A4E8` | `0x05A6DE` patched entry; observed internal PCs include patched/arcade-copy bytes after entry replacement | `genesistan_hook_tilemap_bg_blockcopy` |
| `FG_TEXT_GLYPH_STREAM` | `arcade_pc 0x03BB48`, `0x03C2E2` | `0x03BD48`, `0x03C4E2`, patched sites | glyph and number staging hooks |
| `BG_BLOCK_OR_COLUMN_UPDATE` | `arcade_pc 0x0563A6`, observed `0x0563BC/0x0563C2` | `0x0565A6` patched entry | `genesistan_hook_textwriter_dispatch` |
| `BG_VERTICAL_COLUMN_STREAM` | `arcade_pc 0x0560DA`, observed `0x0560FC` | `0x0562DA/0x0562FC`, arcade-copy | supplementary attract/gameplay-scrolling candidate; not primary ranking driver |

## Per-Caller Distinctions

- `0x03AD44` is a generic longword utility, not a PC080SN-only graphics routine. It is safe only through the existing A0-range dispatch style; a callee-level replacement without range dispatch would affect PC090OJ and non-tilemap behavior.
- `0x055AB4` is a scroll-register writer with four fixed hardware destinations; its current same-contract rewrite to staged scroll variables is appropriate.
- `0x0563A6` is a shared text writer; caller/destination determines BG vs FG routing. The current dispatcher style remains appropriate.
- `0x05A4DE` is a BG block-copy engine with explicit dimensions in `d0/d1`, source in `a0`, destination in `a1`, attr in `d2`.
- The vertical strip stream family is a better operation-buffering candidate than generic fill/copy utilities because it is frequent in normal gameplay and has a predictable attr/code pair plus stride pattern.

## Mirror And Readback Dependency Table

| Family | Reads old PC080SN tile RAM before writing? | Writes complete tile state? | Mirror requirement |
|---|---|---|---|
| `FG_VERTICAL_STRIP_STREAM` | No old PC080SN read observed in cited static loop; source comes from descriptor/table data | Yes: attr/code pair | Preserve canonical PC080SN mirror/staging effects until readback audit proves bypass-safe |
| `BG_VERTICAL_STRIP_STREAM` | No old PC080SN read observed in cited static loop | Yes: attr/code pair | Preserve mirror/staging effects |
| `BULK_SCENE_FILL_CLEAR_MIRROR` | No read in fill loop | Yes for fill/clear | Preserve mirror because it is broad lifecycle state |
| `TITLE_OR_FRONTEND_BG_ROW_COPY` | No old PC080SN read observed | Yes: attr/code pair | Preserve mirror/staging effects |
| `FG_TEXT_GLYPH_STREAM` | Descriptor reads, not destination read | Yes: attr/glyph word pairs | Preserve mirror/staging effects |
| `SCROLL_LATCH_X/Y` | Not tile RAM | N/A | Preserve staged final scroll values; repeated same-frame writes can be last-value-latched later if proven |
| `CONTROL_LATCH` | Not tile RAM | N/A | Preserve hardware-equivalent control state where used |
| `OTHER_TILE_OR_UNKNOWN` | Unknown | Unknown | Compatibility fallback required |

## Current Genesis-Path Amplification

Exact current helper-call and VBlank-commit counts were not measured in this arcade trace; they are therefore labeled as static/estimated, not measured facts.

Observed operation shape implies likely amplification in the current staged-row model:

- Vertical strip streams write one logical column/strip across many rows (`0x100` byte stride between same-half words). A row-dirty staging model tends to mark many rows dirty for a narrow visual update, causing broad Plane A/B row commits during VBlank.
- Scroll latch traffic occurs every gameplay frame but is already condensed to staged scroll variables in Build 0138; only final per-frame values are likely presentation-relevant.
- Scene fills and block copies are high volume but occur at lifecycle boundaries; optimizing them may improve load/transition cost but is less important for normal-frame gameplay traffic.

## Proposed Future Operation Mapping

| Observed family | Best future operation type | Payload | DMA/commit implication | Mirror/readback note |
|---|---|---|---|---|
| `FG_VERTICAL_STRIP_STREAM` | `VERTICAL_RUN` / strip operation | plane, start cell, count, attr/code cells | likely multiple row writes or strided VDP update; not one plain contiguous DMA | update canonical mirror/staging |
| `BG_VERTICAL_STRIP_STREAM` | `VERTICAL_RUN` / strip operation | same | same | update mirror/staging |
| `BULK_SCENE_FILL_CLEAR_MIRROR` | `FILL` / `CLEAR` / `BULK_SCENE_LOAD` | plane/page, fill word, extent | broad DMA-friendly if complete page/rows | preserve broad mirror |
| `TITLE_OR_FRONTEND_BG_ROW_COPY` | `RECTANGLE_ROWS` | width, height, source, attr, dest | row DMAs possible | preserve mirror |
| `FG_TEXT_GLYPH_STREAM` | `HORIZONTAL_RUN` / text run | text/glyph sequence, attr, dest | row write/DMA possible | preserve mirror |
| `SCROLL_LATCH_X/Y` | `SCROLL_LATCH` | final x/y values | commit once per VBlank | no tile mirror |
| `CONTROL_LATCH` | `CONTROL_LATCH` | control register value | state latch | no tile mirror |
| unknown sparse writes | `COMPATIBILITY_FALLBACK` | raw write | existing staging path | required |

Minimum semantic operation types that cover most observed traffic: `VERTICAL_RUN`, `FILL/CLEAR`, `RECTANGLE_ROWS`, `HORIZONTAL_RUN`, `SCROLL_LATCH`, `CONTROL_LATCH`, and `COMPATIBILITY_FALLBACK`.

## First Replacement Recommendation

**Selected family:** gameplay vertical strip streaming, starting with the `arcade_pc 0x055968/0x055990` producer path whose original inner writes appear as `0x0559B8/0x055A06` in the arcade trace.

**Why this first:**

- Covers the largest single manual-gameplay PC080SN traffic family: `163,072` raw writes, `36.273%` of partial Stage 1 traffic.
- Emits complete tile state as attr/code pairs.
- Destination progression is stable and narrow: same-half word stride `0x100` across rows.
- Entry-level patch points already exist in Build 0138 at `runtime_genesis_pc 0x055B68/0x055B90`, reducing patch-boundary risk.
- More relevant to normal gameplay than scene clear/fill, which is high volume but lifecycle-bound.
- Safer than immediately targeting the `0x055C7A` BG sibling because the `0x055C7A` path still maps as `arcade_copy` and needs a fresh entry/caller audit before implementation.

**Estimated traffic/helper/commit coverage:**

- Observed raw traffic coverage: 36.273% of partial Stage 1 PC080SN writes.
- If paired with the BG sibling later, combined vertical strip traffic would cover 59.933% of partial Stage 1 writes.
- Current helper-call and VBlank commit reduction are not exactly measured in this trace. Expected impact is high because a narrow vertical strip can dirty many rows in a row-based commit model.

**Required mirror behavior:** preserve canonical PC080SN/mirror/staging effects for every logical cell written. Do not bypass mirror/state updates unless a later readback audit proves it safe.

**Proposed buffered Genesis operation:** queue a bounded `VERTICAL_RUN` operation containing destination plane/page, start cell/column, count, and composed Genesis cells, then commit it during controlled VBlank presentation.

**Acceptance criteria for a later implementation build:**

- Runtime trace shows the selected arcade producer still executes and updates the canonical mirror/staging state.
- No raw PC080SN hardware writes are introduced on Genesis.
- Plane rows/VRAM updates are no broader than the operation requires, or any broad commit remains explicitly justified.
- Title/attract and partial Stage 1 visuals do not regress.
- Unknown sparse writes remain handled by compatibility fallback.

## Second-Best Candidate

**Family:** `BG_VERTICAL_STRIP_STREAM` around `arcade_pc 0x055C7A`, observed write PCs `0x055C80/0x055C94`.

**Why second:** covers 23.660% of partial Stage 1 raw traffic and has the same complete-tile vertical-strip shape. It is deferred because the current address map reports this path as `arcade_copy`, so an implementation task needs to pin callers and replacement scope first.

## Unknown And Uncovered Operations

- Unknown residual tile writes in manual gameplay: `193` raw writes, `0.043%` of manual gameplay traffic.
- The primary gameplay capture covers only part of Stage 1. Later Stage 1, end-of-stage transition, boss/state transitions, and later-stage PC080SN operation families are not comprehensively covered.
- The attract portion is supplementary and should not be used to rank normal gameplay frequency.
- Minimum additional runtime state needed later: targeted capture of the specific missing state being evaluated, such as late Stage 1/end-of-round if optimizing transition operations, or a focused `0x055C7A` caller trace before replacing that BG sibling. A generic full replay is not required for the first vertical-strip target because the dominant family is already strongly represented.

## Evidence File Index

- Raw writes: `states/traces/pc080sn_operation_census_20260704_132001/playthrough_pc080sn_raw_writes.log`
- Frame markers: `states/traces/pc080sn_operation_census_20260704_132001/playthrough_frame_markers.log`
- Capture metadata: `states/traces/pc080sn_operation_census_20260704_132001/playthrough_capture_metadata_runtime.log`
- Final inventory: `states/traces/pc080sn_operation_census_20260704_132001/phase2_final_capture_inventory.txt`
- Reduced 60-frame bins: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_60frame_bins.tsv`
- Burst records: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_burst_records.tsv`
- Segmented census: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_segmented_census.md`
- Segmented census JSON: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_segmented_census.json`
- Address-map xref: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_address_map_xref.md`
- Capture script: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_capture.lua`
- MAME config/version/listxml: `states/traces/pc080sn_operation_census_20260704_132001/config/`

## STOP Status

STOP not triggered. The audit completed with a coverage limitation: primary gameplay is partial Stage 1, so rankings for rare/later-stage behavior are provisional.
