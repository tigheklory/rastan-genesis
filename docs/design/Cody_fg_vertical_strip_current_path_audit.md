# Cody - FG Vertical Strip Current-Path Contract and Cost Audit

**Date:** 2026-07-04  
**Type:** Evidence-only static + runtime audit  
**Build:** 0138  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0138.bin`  
**ROM SHA256:** `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`  
**Primary prior:** `docs/design/Cody_pc080sn_operation_census.md` and `states/traces/pc080sn_operation_census_20260704_132001/`  
**New evidence path:** `states/traces/fg_vertical_strip_current_path_audit_20260704_140335/`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No BlastEm. No VBlank order, DISPLAY_ON/OFF, frame-pipeline, semantic queue, or one-frame-lag changes.

Address labels: `arcade_pc` and `runtime_genesis_pc` are code addresses. `HW_ADDRESS` is hardware-visible address. `Genesis-WRAM` is Genesis work RAM. All arcade-to-Genesis mappings in this report are from `build/rastan-direct/address_map.json`, not arithmetic offsets.

## 1. Executive Conclusion

**Outcome B: target is valid, but one dependency is unresolved.**

The `arcade_pc 0x055968/0x055990` vertical-strip family remains a valid first optimization target from the PC080SN census: in the original arcade manual partial Stage-1 capture, the observed inner write PCs `arcade_pc 0x0559B8/0x055A06` accounted for `163,072` raw PC080SN writes, or `36.273%` of manual-gameplay PC080SN traffic. Those raw writes split exactly into `1,274` strip-sized units at `128` raw words each.

For current Build 0138, the entry points are already replaced:

- `arcade_pc 0x055968 -> runtime_genesis_pc 0x055B68`, `patched_site`, calls `genesistan_hook_tilemap_plane_a` at `runtime_genesis_pc 0x070248`.
- `arcade_pc 0x055990 -> runtime_genesis_pc 0x055B90`, `patched_site`, calls `genesistan_hook_tilemap_fg` at `runtime_genesis_pc 0x0703EA`.

For the selected FG path (`0x055990`), static generated-code proof shows one hook invocation writes up to `64` composed Genesis Plane-A staging cells (`16 descriptors * 4 cells`), marks `4` unique current staging rows dirty, and the current `vdp_commit_fg_strips_if_dirty` row model commits `64` Plane-A words per dirty row. Therefore one fully valid FG strip invocation currently causes up to `256` Plane-A words to be committed for `64` logical cells: **4.0x presentation amplification vs composed cells**, or **2.0x vs the original arcade raw attr+code word count**.

The blocker is runtime isolation: the fresh Build 0138 MAME Genesis-driver run with coin/start automation reached state `2/3/0` but did **not** hit `runtime_genesis_pc 0x055B90` / `genesistan_hook_tilemap_fg`. Thus exact current-runtime per-frame overlap, repeated-cell writes, and same-frame dirty-row sharing for a real Build 0138 gameplay invocation were not measured. A future implementation should not proceed until a narrow Build 0138 gameplay-state replay/save-state trace hits `0x055B90` and confirms whether other producers share the same dirty rows before VBlank.

## 2. Build 0138 Current Frame Model

Build 0138 still uses the current immediate staging plus same-frame VBlank presentation model. This audit did not alter it.

`_vblank_service` calls, in order:

1. `rastan_direct_update_inputs`
2. `vdp_prepare_sprites`
3. DISPLAY_OFF
4. `vdp_commit_tiles_if_dirty`
5. `vdp_commit_bg_strips_if_dirty`
6. `vdp_commit_fg_strips_if_dirty`
7. sprite VRAM commit
8. DISPLAY_ON
9. palette commit if dirty
10. scroll commit
11. jump to the arcade VBlank handoff path

The current producer path therefore writes staging before VBlank commit; there is no front/back buffer, no new semantic queue, and no one-frame-lag pipeline assumed here.

## 3. Address Mapping

| Address | JSON-derived mapping | Kind | Role |
|---|---|---|---|
| `arcade_pc 0x055968` | `runtime_genesis_pc 0x055B68` | `patched_site` | BG/plane-B strip entry in current spec wording; replacement calls `genesistan_hook_tilemap_plane_a` |
| `arcade_pc 0x055990` | `runtime_genesis_pc 0x055B90` | `patched_site` | FG/Plane-A strip entry; replacement calls `genesistan_hook_tilemap_fg` |
| `arcade_pc 0x0559B8` | `runtime_genesis_pc 0x055BB8` | `arcade_copy` | Original inner attr-write post-PC observed in arcade trace; bypassed when entry replacement is used |
| `arcade_pc 0x055A06` | `runtime_genesis_pc 0x055C06` | `arcade_copy` | Original inner code-write post-PC observed in arcade trace; bypassed when entry replacement is used |
| `runtime_genesis_pc 0x0703EA` | no arcade mapping | `genesis_only` | `genesistan_hook_tilemap_fg` helper body |
| `runtime_genesis_pc 0x070532` | no arcade mapping | `genesis_only` | current FG staging store instruction |
| `runtime_genesis_pc 0x07053E` | no arcade mapping | `genesis_only` | current FG dirty-row store instruction |
| `runtime_genesis_pc 0x0701B2` | no arcade mapping | `genesis_only` | current Plane-A VDP data-port row-copy instruction |

## 4. Static Routine Contracts

### 4.1 Shared caller/dispatcher

Original arcade code around `arcade_pc 0x055948` selects between the two entries using `%a5@(4264)`:

```asm
55948: cmpi.w #0,%a5@(4264)
5594e: bne    0x5595a
55950: bsrw   0x55968
55954: addq.w #1,%a5@(4298)
55958: bra    0x55962
5595a: bsrw   0x55990
5595e: addq.w #1,%a5@(4298)
55962: bsrw   0x558a2
55966: rts
```

Build 0138 preserves this dispatch shape at the mapped runtime addresses, but replaces each entry body with a Genesis helper call plus return.

### 4.2 `arcade_pc 0x055968`

Original contract:

- Input state: `%a5@(4256)` destination pointer, `%a5@(4298)` strip index, descriptor/list state rooted around `0x0010D080` and `0x0010D040`.
- Loop count: `16` outer descriptor iterations.
- Inner helper: `arcade_pc 0x0559B2`.
- Tile formation: one attribute word and one code word per logical PC080SN tile.
- Completion: stores updated `%a0` back to `%a5@(4256)`, then returns.

Current Build 0138 replacement at `runtime_genesis_pc 0x055B68`:

```asm
55b68: jsr 0x70248     ; genesistan_hook_tilemap_plane_a
55b6e: nop ...
55b8e: rts
```

Current helper state:

- Uses `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` and `ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5)`.
- Writes `staged_bg_buffer` and `bg_row_dirty`, not the FG/Plane-A buffer.
- Same generated shape as the FG hook: `16 * 4` composed cells per fully valid invocation.

This report focuses on the FG/Plane-A entry below because the requested current-path cost is for FG vertical strips and Plane A.

### 4.3 `arcade_pc 0x055990`

Original contract:

- Input state: `%a5@(4260)` destination pointer, `%a5@(4298)` strip index, `%a5@(4264)` mode/control word, descriptor/list state rooted around `0x0010D080` and `0x0010D040`.
- Loop count: `16` outer descriptor iterations.
- Inner helper: `arcade_pc 0x055A14`.
- Original tile formation: one PC080SN attribute word and one PC080SN code word per logical tile. The original arcade runtime trace observes the post-PC write pair `0x0559B8/0x055A06` for this family, with `128` raw writes per strip-sized unit in the normal case.
- Destination progression: original raw PC080SN writes progress through FG C-window addresses, with a repeated `0x100` byte stride between same-half writes in the arcade trace.

Current Build 0138 replacement at `runtime_genesis_pc 0x055B90`:

```asm
55b90: jsr 0x703ea     ; genesistan_hook_tilemap_fg
55b96: nop ...
55bb0: rts
```

Current hook input/output/clobber behavior:

- Saves/restores `%d0-%d7/%a0-%a6`; caller-visible registers are preserved by `movem`.
- Reloads `%a5 = Genesis-WRAM 0x00FF0000` internally.
- Reads `%a5@(4298)` as strip index into `%d7`.
- Reads `%a5@(4260)` as FG destination into `%d5`.
- Validates destination in `HW_ADDRESS 0x00C08000..0x00C0BFFF` and 4-byte alignment.
- Uses descriptor list at `%a5@(4096)` and ROM base `0x00000200`.
- Uses `genesistan_pc080sn_tile_vram_lut` and `genesistan_pc080sn_attr_lut` to compose Genesis nametable words.
- Writes `staged_fg_buffer` and `fg_row_dirty`.
- On valid completion, stores updated `%d5` to `%a5@(4260)`.

## 5. Complete-Tile Formation

Original arcade evidence establishes that this family writes complete PC080SN tile state as two raw words:

- observed attr-like write post-PC: `arcade_pc 0x0559B8`
- observed code-like write post-PC: `arcade_pc 0x055A06`
- first captured pair in original arcade manual gameplay:
  - `HW_ADDRESS 0x00C08000`, data `0x0003`, post-PC `0x0559B8`
  - `HW_ADDRESS 0x00C08002`, data `0x041C`, post-PC `0x055A06`

Current Build 0138 does not preserve the two raw PC080SN words as two presentation words. It consumes descriptor attr/code inputs and immediately composes a single Genesis Plane-A nametable word per logical cell. Therefore each complete Genesis word is available immediately inside the hook before the staging store at `runtime_genesis_pc 0x070532`.

## 6. Current Genesis Hook Path

Selected path:

```text
runtime_genesis_pc 0x055B90
  -> jsr runtime_genesis_pc 0x0703EA genesistan_hook_tilemap_fg
     -> validate HW_ADDRESS 0x00C08000..0x00C0BFFF destination
     -> load descriptor list from Genesis-WRAM %a5@(4096)
     -> translate tile code through genesistan_pc080sn_tile_vram_lut
     -> translate attributes through genesistan_pc080sn_attr_lut
     -> compose one Genesis nametable word
     -> runtime_genesis_pc 0x070532: move.w %d3,%fp@(0,%d0.w)
     -> runtime_genesis_pc 0x07053E: move.l %d0,fg_row_dirty
  -> later VBlank runtime_genesis_pc 0x070186 vdp_commit_fg_strips_if_dirty
     -> runtime_genesis_pc 0x0701B2: move.w (%a0)+,HW_ADDRESS 0x00C00000
```

The hook does not call a per-cell store helper. The replacement entry performs one helper call to `genesistan_hook_tilemap_fg`; the hook then performs the per-cell work inline. It may call `load_scene_tiles` on the scene-preamble slow path, but that is not the normal per-cell strip-store mechanism.

## 7. Staging And Dirty-Row Ownership

Current owner states for this path:

| State | Address / symbol | Current role |
|---|---|---|
| FG presentation staging | `Genesis-WRAM 0x00FF501A`, `staged_fg_buffer` | composed Genesis Plane-A nametable words; source for `vdp_commit_fg_strips_if_dirty` |
| Dirty rows | `Genesis-WRAM 0x00FF4006`, `fg_row_dirty` | 32-bit row mask; one bit per current staging row |
| Plane-A presentation | VDP Plane A base `VRAM 0xE000` | row-committed from `staged_fg_buffer` during VBlank |
| Raw PC080SN attr/code mirror | none proven for this hook | current hook does not maintain a separate two-word PC080SN C-window mirror for the selected path |

The current port's effective readback/presentation state for this path is `staged_fg_buffer`. A future optimization must not bypass updates to this buffer unless a later readback audit proves no downstream code depends on it. With current evidence, the safe assumption is: update the current staging/mirror state and optimize only the presentation transfer.

## 8. Runtime Evidence

### 8.1 Original arcade manual-gameplay census

From `states/traces/pc080sn_operation_census_20260704_132001/playthrough_pc080sn_raw_writes.log` and `docs/design/Cody_pc080sn_operation_census.md`:

- Manual partial Stage-1 FG vertical-strip raw writes: `163,072`.
- Share of manual-gameplay PC080SN writes: `36.273%`.
- Top observed PCs: `arcade_pc 0x0559B8` (`81,536`) and `arcade_pc 0x055A06` (`81,536`).
- Raw writes divide exactly into `1,274` strip-sized units at `128` raw words each.
- Common per-frame count in the manual gameplay window: `128` raw writes, i.e. one strip-sized unit; some frames contain several units.

This proves the original arcade operation family is frequent and complete-tile-based.

### 8.2 Fresh Build 0138 Genesis run

New trace path: `states/traces/fg_vertical_strip_current_path_audit_20260704_140335/`.

Method: MAME Genesis driver, existing Build 0138 ROM, coin/start automation, write taps on `staged_fg_buffer`, `fg_row_dirty`, VDP data/control ports, and raw FG C-window. No ROM diagnostics.

Result:

- Run completed cleanly to frame `3600`.
- Input fields found: coin/A `true`, start `true`.
- State reached `2/3/0` in frame markers.
- The run did **not** hit `runtime_genesis_pc 0x055B90` / `genesistan_hook_tilemap_fg`.
- Captured events were boot/other-path events only: `148` FG staging writes at `runtime_genesis_pc 0x0002C8`, `2` dirty writes at `0x00028C`, and `15` VDP control writes at `0x07008E`.

This is coverage-limited negative evidence. It cannot be used as the selected-producer runtime measurement.

## 9. Per-Invocation Measurements

Because the fresh Build 0138 run did not hit the selected producer, the following current Build 0138 invocation costs are **static/generated-code measurements**, not isolated runtime measurements:

| Quantity | Value | Evidence |
|---|---:|---|
| Replacement entry helper calls | `1` | `runtime_genesis_pc 0x055B90: jsr 0x0703EA` |
| Per-cell helper calls inside hook | `0` | generated hook body stores inline at `0x070532` |
| Logical composed Genesis cells per full valid invocation | `64` | `16` descriptor loop iterations * `4` row-loop iterations |
| Staging words written | `64` | one `move.w %d3,%fp@(0,%d0.w)` per row-loop iteration |
| Dirty-row flag writes | up to `64` writes | hook reads/bsets/stores `fg_row_dirty` per cell; repeated rows collapse in final mask |
| Unique current staging rows dirtied | `4` | row loop increments `%d1` four times; descriptor loop subtracts `4` to return to the same base row |
| Plane-A commit operations caused | up to `4` row commits | `fg_row_dirty` has four row bits if no prior overlap/suppression |
| Plane-A words committed | up to `256` | `4` rows * `64` words per row |
| Unchanged same-row cells also committed | yes | row commit streams all 64 words for each dirty row |

If a descriptor is invalid or the destination is rejected, these are upper-bound valid-path values; the normal selected gameplay family is expected to use valid descriptors based on the original arcade census, but the fresh Build 0138 trace did not isolate one runtime invocation.

## 10. Per-Frame Measurements

Original arcade manual gameplay proves multiple strip-sized units can occur in one frame:

- Manual partial Stage-1 units: `1,274` strip-sized units.
- Frames with this family: `968` frames.
- Common frame count: `128` raw writes, equivalent to one strip-sized unit.
- Some frames show several strip-sized units; example high counts include `640` raw writes (`5` units) and larger mixed counts where the frame boundary cuts through operation clusters.

Current Build 0138 per-frame row overlap and VBlank commit attribution are **not isolated** because the fresh Genesis run did not hit `0x055B90`. The expected upper-bound current presentation cost is:

```text
N full valid FG strip invocations in one frame:
  logical cells = 64 * N
  dirty rows = at most 4 * N, but less if invocations share rows
  Plane-A commit words = 64 * unique_dirty_rows
```

Exact same-frame overlap/overwrite requires a trace that reaches the selected gameplay producer in Build 0138.

## 11. Plane-A Commit Measurements

Static generated-code proof for Build 0138 `vdp_commit_fg_strips_if_dirty`:

```asm
70186: move.l fg_row_dirty,%d6
70190: btst %d5,%d6
7019a: move.l #0xE000,%d0
701a2: bsr vdp_set_vram_write_addr
701a6: lea staged_fg_buffer,%a0
701ae: move.w #63,%d7
701b2: move.w (%a0)+,0x00C00000
701b8: dbf %d7,0x701b2
701c2: move.l %d6,fg_row_dirty
```

Each dirty row commits exactly `64` Plane-A words by CPU writes to `HW_ADDRESS 0x00C00000`; it is not DMA in the current path. VDP destination starts at `VRAM 0xE000 + row*0x80` for each dirty row.

## 12. Amplification Calculation

For one full valid current FG strip invocation:

```text
64 logical Genesis cells produced
4 current staging rows dirtied
4 row commits
256 Plane-A words committed
amplification vs composed logical cells = 256 / 64 = 4.0x
amplification vs original raw attr+code words = 256 / 128 = 2.0x
```

This is a static/generated-code amplification calculation. A runtime trace that actually hits `0x055B90` is still required to measure lower/upper bounds under same-frame overlap with other producers.

## 13. Mirror / Readback Analysis

Current Build 0138 selected path does not maintain a separate raw PC080SN two-word mirror for the FG strip. It writes the composed Genesis word to `staged_fg_buffer` and marks rows dirty. Therefore:

- The current authoritative state for later Genesis presentation is `staged_fg_buffer`.
- A future optimized strip path must still update `staged_fg_buffer` unless a readback audit proves it can become a pure presentation queue.
- No evidence in this task proves later arcade logic reads a raw two-word PC080SN mirror for this producer.
- No evidence in this task proves it is safe to remove or bypass the current staging representation.

Safe future rule: preserve the current staging state first; optimize only the broad row presentation commit.

## 14. Strided VDP Transfer Feasibility

A single vertical strip can potentially be represented by Genesis VDP autoincrement, but only for the vertical sub-runs after the current hook has composed contiguous source words for that sub-run.

Current project configuration:

- Plane A base: `VRAM 0xE000`.
- Plane A row width: `64` cells.
- One nametable cell: `1` word = `2` bytes.
- Vertically adjacent same-column cells are `64 * 2 = 0x80` bytes apart in VRAM.
- Current normal autoincrement is the sequential-word setting used for row commits; a strided transfer would need VDP autoincrement `0x80` and then restoration to the normal setting afterward.

Genesis VDP memory-to-VRAM DMA uses contiguous source data while VDP autoincrement controls destination address progression. Therefore a strided DMA/CPU write shape is plausible for a same-column vertical run. However, the current hook's full invocation is `16` four-cell sub-runs across columns, not one single 64-cell same-column run in current staging coordinates. A future efficient presentation path would likely emit multiple short strided transfers or a small operation list, not one plain contiguous row DMA.

Feasibility caveats:

- Must restore VDP autoincrement after the strip transfer.
- Must avoid duplicating the existing broad dirty-row commit for the same cells.
- Must fit current same-frame VBlank timing; this audit does not authorize timing or frame-pipeline changes.

## 15. Duplicate-Commit Prevention Requirements

Current dirty-state mechanism is one bit per row in `fg_row_dirty`. If a future optimized strip transfer uploads the strip but leaves the same row bits set, `vdp_commit_fg_strips_if_dirty` will also upload full rows later in the same VBlank.

To avoid duplicate narrow + broad upload, a future implementation must do one of the following, with runtime proof:

- not set `fg_row_dirty` for cells handled by the optimized strip path, while still updating `staged_fg_buffer`; or
- consume/clear row bits only when no other producer has dirtied other cells in those rows; or
- replace row dirty with a more precise dirty representation that can distinguish strip-handled cells from other same-row writes.

The unresolved dependency is same-frame producer overlap: Build 0138 runtime evidence must prove whether other FG producers write the same rows before VBlank in the target gameplay state.

## 16. Outcome B

**Outcome B: target is valid but one dependency is unresolved.**

The vertical-strip family remains the safest first implementation target from the census because it is the largest normal-gameplay PC080SN operation family and emits complete tile state. Static Build 0138 analysis proves a real current-path amplification: one valid FG strip invocation writes `64` logical cells but can force `256` Plane-A words through row commits.

The unresolved dependency is **runtime same-frame dirty-row attribution for Build 0138 gameplay**. The fresh automated Genesis run did not hit `runtime_genesis_pc 0x055B90`, so this task could not measure:

- exact selected-producer invocations per current Build 0138 gameplay frame;
- repeated writes to the same staging cell in current runtime;
- whether other FG producers share the same dirty rows before VBlank;
- the exact lower/upper Plane-A commit words attributable only to the selected producer.

Smallest follow-up audit: run a Build 0138 Genesis-driver trace from a gameplay save state/replay point that hits `runtime_genesis_pc 0x055B90`, with the same taps used here plus a breakpoint/log on `0x055B90`. This is not a generic full-stage replay request; it needs only a short state where the selected producer executes repeatedly.

## 17. Implementation Readiness

Implementation is **not safely placeable yet**.

A future narrow implementation can likely remain within the current Build 0138 frame model if it updates `staged_fg_buffer`, emits an optimized presentation operation in the same VBlank phase, and suppresses/consumes the corresponding broad row dirty work without losing other same-row updates. That last clause is the unresolved runtime dependency.

No one-frame-lag pipeline is required by the static contract, but this audit does not prove the duplicate-commit suppression rule for mixed same-frame producer traffic.

## 18. Evidence Index

- Prompt source: `/home/tighe/.codex/attachments/63e83eac-94a4-4900-b0fa-f597594b584f/pasted-text.txt`
- Primary census report: `docs/design/Cody_pc080sn_operation_census.md`
- Original arcade PC080SN raw writes: `states/traces/pc080sn_operation_census_20260704_132001/playthrough_pc080sn_raw_writes.log`
- Original arcade segmented census: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_segmented_census.json`
- Address-map xref from prior census: `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_address_map_xref.md`
- New Build 0138 runtime trace directory: `states/traces/fg_vertical_strip_current_path_audit_20260704_140335/`
- New trace script: `states/traces/fg_vertical_strip_current_path_audit_20260704_140335/capture_fg_vertical_strip_build0138.lua`
- New trace events: `states/traces/fg_vertical_strip_current_path_audit_20260704_140335/fg_vertical_strip_events.log`
- New trace reduction: `states/traces/fg_vertical_strip_current_path_audit_20260704_140335/runtime_trace_reduction.md`
- Generated disassembly source: `build/genesis_postpatch.disasm.txt`
- Original disassembly source: `build/maincpu.disasm.txt`
- Current hook source inspected: `apps/rastan-direct/src/tilemap_hooks.s`
- Current VBlank commit source inspected: `apps/rastan-direct/src/vdp_comm.s`

## STOP Status

STOP not triggered for documentation/evidence production. Implementation is blocked by the Outcome B runtime dependency above.
