# Cody - PC080SN Native YM7101 Boundary Implementation Audit

> **POLICY NOTICE (added 2026-07-28):** This document predates the canonical `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). It is retained as an active design reference and **defers to that policy**: where anything here conflicts, the canonical policy governs. Any 'shadow', 'mirror', 'virtual name-RAM', 'tall buffer', or 'projection' referenced here is **transitional compatibility only, never the final architecture** — the target is `arcade semantic decision → native Genesis VDP/SAT`. Agents must state the semantic cut and the chip tail removed before implementing.


> **Canonical contract notice:** This file remains the cumulative research/audit history. The standalone canonical final implementation contract is now `docs/design/Cody_pc080sn_native_ym7101_global_fill_vertical_streaming_contract.md`. Do not delete or rewrite this historical audit content when using the standalone contract.


**Date:** 2026-07-26  
**Type:** Boundary audit / implementation gate  
**Baseline ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`  
**Baseline SHA256:** `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`  
**Build counter observed:** `238`  
**Scope:** Native YM7101 realization of Rastan PC080SN intent. No PC090OJ, palette, HUD, score, input, or Build-0235 code-zero decoder changes.

## Result

STOP before implementation/build.

The production source and Makefile match the accepted Build 0235 functional baseline, and the candidate arcade boundaries map exactly through `build/rastan-direct/address_map.json`. However, the current evidence does not yet establish a safe complete native replacement contract for both live gameplay tilemaps without preserving the current projection layer. The known recent 0238 attempt already proved that a partial retarget can preserve FG while breaking BG, and the current source still has an active gameplay dependency on `vdp_project_bg_tall_if_dirty` / `vdp_project_fg_tall_if_dirty`.

The safe conclusion is: the strip-level boundaries are identified, but the native YM7101 replacement is not yet buildable without either guessing the BG producer/window contract or breaking frontend/unconverted producers that still legitimately use the 32-row staging paths.

## Baseline Confirmation

- `apps/rastan-direct/src/` and `apps/rastan-direct/Makefile`: no dirty production changes observed.
- Expected documentation/log dirtiness was present only in `AGENTS_LOG.md` and `docs/design/Andy_pc080sn_native_ym7101_current_state_handoff.md`.
- Build 0235 ROM SHA matched exactly: `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`.
- Build counter was `238`, consistent with the preserved Build 0237 duplicate and rejected Build 0238 history.
- No numbered ROM artifacts were deleted, overwritten, or reused.

## Authoritative PC Mapping

All address mappings below are from `build/rastan-direct/address_map.json`; no arithmetic offset is used as authority.

| Arcade PC | Runtime Genesis PC | Map kind / current status |
|---:|---:|---|
| `arcade_pc 0x0503DC` | `runtime_genesis_pc 0x0505DC` | `arcade_copy`, scene-fill caller side |
| `arcade_pc 0x0503E4` | `runtime_genesis_pc 0x0505E4` | `arcade_copy`, scene-fill loop |
| `arcade_pc 0x055904` | `runtime_genesis_pc 0x055B04` | `patched_site`, descriptor rebuild hook |
| `arcade_pc 0x055948` | `runtime_genesis_pc 0x055B48` | `arcade_copy`, tilemap1 dispatcher/post-advance owner |
| `arcade_pc 0x055968` | `runtime_genesis_pc 0x055B68` | `patched_site`, current Plane-A/tilemap1 branch hook |
| `arcade_pc 0x055990` | `runtime_genesis_pc 0x055B90` | `patched_site`, current FG/tilemap1 branch hook |
| `arcade_pc 0x0559B2` | `runtime_genesis_pc 0x055BB2` | `arcade_copy`, original per-cell producer body |
| `arcade_pc 0x055A14` | `runtime_genesis_pc 0x055C14` | `arcade_copy`, original per-cell producer body |
| `arcade_pc 0x055AB4` | `runtime_genesis_pc 0x055CB4` | `patched_site`, scroll register staging |
| `arcade_pc 0x055B8E` | `runtime_genesis_pc 0x055D8E` | `arcade_copy`, tilemap0 gameplay vertical-stream caller |
| `arcade_pc 0x055C4A` | `runtime_genesis_pc 0x055E4A` | `arcade_copy`, tilemap0 strip wrapper/bookkeeping |
| `arcade_pc 0x055C5E` | `runtime_genesis_pc 0x055E5E` | `patched_site`, current tilemap0/item-page strip blit hook |
| `arcade_pc 0x055C7A` | `runtime_genesis_pc 0x055E7A` | `arcade_copy`, original tilemap0 per-cell body |
| `arcade_pc 0x0561B6` | `runtime_genesis_pc 0x0563B6` | `patched_site`, C-window clear hook |

## Fixed YM7101 Layout

Confirmed from `apps/rastan-direct/src/vdp_comm.s`:

- VDP plane size register 16 is set to `0x01`, i.e. `64x32`.
- Plane B nametable base is `VRAM 0xC000`.
- Plane A nametable base is `VRAM 0xE000`.
- SAT base is `VRAM 0xF800`.
- HScroll table base is `VRAM 0xFC00`.
- `_vblank_service` commits via staged WRAM buffers and then tail-jumps to arcade VBlank.

This matches the fixed-layout constraint in the prompt.

## Boundary Proof

### Tilemap1 / Plane A Playfield

`arcade_pc 0x055948` (`runtime_genesis_pc 0x055B48`) is the correct owner for dispatch and post-advance semantics. It must be retained because it owns the selector branch, ring-counter advance, descriptor lifecycle, and eventual call to the post-advance logic documented in `docs/arcade_reference/pc080sn/gameplay_control.c` and `core_publishers.c`.

The two high-level strip entry boundaries are:

- `arcade_pc 0x055968` -> `runtime_genesis_pc 0x055B68`
- `arcade_pc 0x055990` -> `runtime_genesis_pc 0x055B90`

These are the highest safe strip-level candidate boundaries currently supported by the source. They replace the original 16-descriptor strip walks and leave the dispatcher/post-advance owner intact.

The lower per-cell bodies:

- `arcade_pc 0x0559B2` -> `runtime_genesis_pc 0x055BB2`
- `arcade_pc 0x055A14` -> `runtime_genesis_pc 0x055C14`

are not preferred final patch boundaries. They are too late to avoid re-entering PC080SN-specific per-cell address math, and the collision side effects must be recreated coherently at the strip level rather than by partially walking raw PC080SN hardware destinations.

Current Build 0235 does not yet use a native YM7101 strip publisher here. Instead, `runtime_genesis_pc 0x055B68` calls `genesistan_hook_tilemap_plane_a`, which still writes `staged_bg_buffer` and invokes gameplay-only helper side paths; `runtime_genesis_pc 0x055B90` calls `genesistan_hook_tilemap_fg`, whose gameplay path stages through `genesistan_stage_fg_src_column` and the tall FG buffer.

### Tilemap0 / Plane B Background

`arcade_pc 0x055B8E` (`runtime_genesis_pc 0x055D8E`) is the gameplay tilemap0 vertical-stream caller. It is not a final replacement boundary because it belongs to the controlling arcade flow and must continue to own the decision that a tilemap0 strip is needed.

`arcade_pc 0x055C4A` (`runtime_genesis_pc 0x055E4A`) is the tilemap0 wrapper/bookkeeping boundary. It copies/updates tilemap0 cursor state and participates in scene-fill as well as gameplay streaming. It should not be bypassed without a complete proof that its side effects have been preserved.

`arcade_pc 0x055C5E` (`runtime_genesis_pc 0x055E5E`) is the currently patched tilemap0 strip-entry site. It is the highest safe current replacement point for the actual 64-cell tilemap0 strip body, while retaining `0x055C4A` wrapper semantics.

`arcade_pc 0x055C7A` (`runtime_genesis_pc 0x055E7A`) is too late as a final boundary because it is the original raw per-cell body and would keep PC080SN-style destination walking in the ordinary gameplay path.

Current Build 0235 does not yet have a native YM7101 tilemap0 producer either. `runtime_genesis_pc 0x055E5E` calls `genesistan_hook_itempage_strip_blit`, which conditionally routes gameplay sources through `genesistan_hook_tilemap_bg_fill_tall` and otherwise through `genesistan_hook_tilemap_bg_fill`. Therefore, ordinary gameplay tilemap0 output still depends on the tall-buffer projection path.

## Native Contract That Must Be Preserved

A future implementation may use the proven strip boundaries above only if it preserves all of these arcade-owned side effects:

- `0x055948` dispatch and post-advance ownership.
- `0x055904` descriptor rebuild semantics and the tables at Genesis WRAM `0x00FF1000`, `0x00FF1040`, and `0x00FF1080`.
- Ring counters at the mapped A5 fields, especially `a5+0x10CA` and `a5+0x10CC`.
- Tilemap1 collision side effect into mapped Genesis WRAM collision buffer `0x00FF1E00`.
- Tilemap0 source/cursor fields at the mapped A5 fields around `0x10F4`, `0x10F6`, `0x10F8`, `0x10FC`, `0x10D100`, and `0x10D104`.
- Scroll staging from `arcade_pc 0x055AB4` to `staged_scroll_*`, and the existing display-origin bias behavior.
- The three accepted PC080SN readback bypass treatments at `arcade_pc 0x03A47E`, `0x03A552`, and `0x03AC54`; these are existing accepted readback substitutions, not proof that new C-window storage can be removed for all frontend paths.

## Current Versus Native Work Counts

Current Build 0235 gameplay work:

- Tall gameplay writes update 64-row backing buffers.
- `vdp_project_bg_tall_if_dirty` copies 32 rows x 64 words from `staged_bg_tall_buffer` into `staged_bg_buffer` whenever the projected base or dirty state changes.
- `vdp_project_fg_tall_if_dirty` does the same for FG.
- Projection marks all 32 row dirty bits, so the row-DMA commits may rewrite full 64-word rows even when the arcade update was a strip.

Desired native work:

- Tilemap1 strip publisher should emit only the entering row/column cells needed by the arcade publication event, plus collision side effects.
- Tilemap0 strip publisher should emit only the entering 64-cell strip needed by the arcade tilemap0 publication event.
- No 32-row full-window reprojection should run during ordinary gameplay scrolling.
- Final-format staging may still exist as bounded VBlank DMA input, but it should contain physical YM7101 plane rows, not projected PC080SN virtual-window state.

## Scaffolding Classification

| Structure / helper | Classification | Reason |
|---|---|---|
| `staged_bg_tall_buffer` | still-used-by-unconverted-producer | Gameplay tilemap0 currently routes through `genesistan_hook_tilemap_bg_fill_tall`; removing it breaks Build 0235 BG. |
| `staged_fg_tall_buffer` | still-used-by-unconverted-producer | Gameplay FG_SRC currently routes through `genesistan_hook_tilemap_fg_fill_tall`; removing it before a native strip publisher breaks FG. |
| `vdp_project_bg_tall_if_dirty` | superseded-by-target, not safe to remove yet | The target architecture retires it, but Build 0235 still requires it for visible gameplay BG. |
| `vdp_project_fg_tall_if_dirty` | superseded-by-target, not safe to remove yet | The target architecture retires it, but Build 0235 still requires it for visible gameplay FG. |
| `bg_tall_project_base` | superseded-by-target, not safe to remove yet | State for current BG projection. |
| `fg_tall_project_base` | superseded-by-target, not safe to remove yet | State for current FG projection. |
| `staged_bg_buffer` | required-native-staging / frontend-compatible | This is the current final Plane-B row-DMA source and is also used by frontend/blockcopy/text-dispatch paths. |
| `staged_fg_buffer` | required-native-staging / frontend-compatible | This is the current final Plane-A row-DMA source and is used by title, HUD, score, text, high-score, glyph, and inline FG routes. |
| `genesistan_hook_tilemap_bg_fill` | still-used-by-unconverted-producer | Used by textwriter dispatch, blockcopy, item-page non-gameplay path, PC090OJ polymorphic dispatch, and frontend-compatible BG paths. |
| `genesistan_hook_tilemap_fg_fill` | still-used-by-unconverted-producer | Used by inline FG writers, score/number/high-score/text/glyph hooks, textwriter dispatch, and non-gameplay FG paths. |
| `genesistan_hook_tilemap_bg_fill_tall` | superseded-by-target, not safe to remove yet | Intended to be retired for gameplay, but currently required by `genesistan_hook_itempage_strip_blit` for gameplay strip sources. |
| `genesistan_hook_tilemap_fg_fill_tall` | superseded-by-target, not safe to remove yet | Intended to be retired for gameplay, but currently required by `genesistan_stage_fg_src_column`. |
| `genesistan_hook_cwindow_clear` | still-used-by-unconverted-producer | Current clear hook resets multiple staging buffers and dirty flags. A native replacement must preserve frontend and gameplay clear semantics separately before removal. |
| `genesistan_hook_tilemap_bg_blockcopy` | frontend-only-out-of-scope | Used by frontend/title block-copy style PC080SN content, not ordinary gameplay scrolling. |
| `genesistan_hook_textwriter_dispatch` | still-used-by-unconverted-producer | Routes shared PC080SN text writer to BG/FG staging. Not safe to remove as part of gameplay-only native streaming. |
| text/number/glyph/highscore/inline FG hooks | frontend/HUD/unconverted out-of-scope | These use `staged_fg_buffer` and existing VBlank row commit. They are outside the ordinary gameplay scrolling replacement unless separately converted. |
| item-page strip helpers | still-used-by-unconverted-producer | `genesistan_hook_itempage_strip_blit` is currently also the tilemap0 gameplay strip route; it cannot be removed without separating gameplay from item-page semantics. |
| scene-fill helpers at `0x0503DC` / `0x0503E4` | required semantic path | Scene init fills both tilemaps and must remain arcade-owned. Native scene-fill requires a separate proof, not a blind deletion. |
| PC080SN scroll-fill stubs | already-dead for visible global-scroll output | The no-op row-scroll clear stubs match Rastan's global-scroll usage, but they are unrelated to ordinary gameplay strip conversion. |

## Scene-Init Side-Effect Treatment

Scene initialization is not optional. `arcade_pc 0x0503E4` fills both tilemaps through the same publication ecosystem before gameplay streaming begins. The scene-fill path must either:

1. call the same native strip publishers with scene-init-safe state, or
2. have its own native scene-fill publisher that writes final YM7101 plane state while preserving descriptor, source, collision, and scroll initialization order.

Build 0235 still implements scene-fill through the translated staging/projection ecosystem. Retiring the projection layer without a scene-init replacement risks reproducing the prior BG under-population failure.

## Readback Treatment

The accepted readback behavior in Build 0235 is not C-window storage. It is three explicit existing branch substitutions in `specs/rastan_direct_remap.json`:

- `arcade_pc 0x03A47E`
- `arcade_pc 0x03A552`
- `arcade_pc 0x03AC54`

This means ordinary gameplay native strip publishing does not need to preserve a complete PC080SN readable name-RAM mirror for those accepted paths. It does not mean frontend/unconverted paths can lose their final staging buffers without separate proof.

## STOP Rationale

STOP triggered because the implementation boundary is not yet safe.

The prompt asks to retire ordinary gameplay full-window projection and PC080SN-specific translation/projection, but the current Build 0235 source proves the following active dependencies:

- `_vblank_service` unconditionally calls both gameplay projection helpers before row commits.
- `genesistan_hook_itempage_strip_blit` still routes gameplay source ranges through `genesistan_hook_tilemap_bg_fill_tall`.
- `genesistan_stage_fg_src_column` still routes through `genesistan_hook_tilemap_fg_fill_tall`.
- The final 32-row staging helpers are still used by frontend, text, score, glyph, blockcopy, item-page, and PC090OJ polymorphic dispatch paths.
- Recent preserved Build 0238 evidence already showed that disabling/rewiring projection without the correct BG producer contract leaves severe BG under-population.

Therefore, producing a ROM now would require guessing either the BG native strip/window contract or the scene-init replacement contract. That violates the state-causality and patch-discipline rules.

## Verification Performed

- Build 0235 ROM SHA verified against the accepted SHA.
- Build counter verified as `238`.
- Production source dirtiness checked for `apps/rastan-direct/src/`, `apps/rastan-direct/Makefile`, `specs/rastan_direct_remap.json`, and `build/rastan-direct/address_map.json`.
- Candidate PC mappings verified through `address_map.json`.
- Current helper dependencies verified through `apps/rastan-direct/src/tilemap_hooks.s`, `apps/rastan-direct/src/vdp_comm.s`, and `apps/rastan-direct/out/symbol.txt`.
- Arcade reference cross-checks used `docs/arcade_reference/pc080sn/` files, especially `core_publishers.c`, `gameplay_control.c`, `scene_initialization.c`, `tilemap0_producers.md`, and `map_stream_format.md`.

No build was run. No ROM was produced. No source was edited.

## Recommended Next Single Task

Before implementation, capture or statically prove the exact Build 0235 scene-init and gameplay tilemap0 producer-to-final-plane contract needed to replace `genesistan_hook_tilemap_bg_fill_tall` and `vdp_project_bg_tall_if_dirty` without BG under-population.

The next implementation prompt should be limited to one of these:

1. Convert only the proven FG path from `genesistan_stage_fg_src_column` / `genesistan_hook_tilemap_fg_fill_tall` to final 64x32 Plane-A row/column staging, keeping BG projection intact.
2. Or, first prove and convert the tilemap0/BG gameplay and scene-init producer paths together, with a measured equivalence check against Build 0235 before disabling BG projection.

Do not remove frontend/unconverted staging helpers as part of ordinary gameplay PC080SN work.

---

## 2026-07-27 - Plane A Native Strip Implementation Gate

**Task:** Native Plane A gameplay strip producer and VBlank jobs, Build 0235 baseline.  
**Classification:** EXTENDING existing PC080SN native-YM7101 boundary work.  
**Result:** STOP before implementation/build. The authorized Plane A producer boundary is not yet safe to convert in isolation.

### Baseline Confirmed

Accepted functional ROM remains Build 0235:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`
- SHA-256: `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`
- Build counter observed before this task: `238`
- Numbered ROMs 0235-0238 were preserved; none were deleted or overwritten.
- No source/spec/Makefile/ROM/build changes were made by this task.

### Files/Evidence Inspected

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md`
- `docs/design/Cody_pc080sn_native_ym7101_boundary_implementation.md`
- `docs/arcade_reference/pc080sn/core_publishers.c`
- `docs/arcade_reference/pc080sn/gameplay_control.c`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- Targeted trace artifacts under `states/traces/build0235_plane_a_strip_cadence_20260727_005217/`

### Plane A Contract Recorded

Authoritative arcade producer boundary:

- `arcade_pc 0x055948` / `runtime_genesis_pc 0x055B48`: dispatcher/post-publication path retained.
- `arcade_pc 0x055968` / `runtime_genesis_pc 0x055B68`: tilemap1/Plane A entering-column path.
- `arcade_pc 0x055990` / `runtime_genesis_pc 0x055B90`: tilemap1/Plane A entering-row path.

From `core_publishers.c` and current Genesis hooks:

- Both strip paths publish tilemap1 / Plane A logical addresses rooted at `HW_ADDRESS 0x00C08000`.
- Strip A (`0x055968`) uses destination cursor `a5+0x10A0`, saves/restores the cursor, and calls the common cell producer.
- Strip B (`0x055990`) uses destination cursor `a5+0x10A4`, is direction-aware through the `a5+0x10A8` selector, and uses reversed sub-index ordering when selector is not `2`.
- Each strip ultimately emits 64 logical cells (`16 segments x 4 rows`) for tilemap1.
- Collision publication is part of the native arcade contract and must continue for all logical cells, including visually nonresident cells.
- Current Build 0235 Genesis path preserves collision through `genesistan_stage_bg_collision_column` and visual FG through `genesistan_stage_fg_src_column`, which currently writes `staged_fg_tall_buffer` via `genesistan_hook_tilemap_fg_fill_tall`.

### Targeted Build 0235 Runtime Cadence Trace

Primary trace directory:

`states/traces/build0235_plane_a_strip_cadence_20260727_005217/`

Important files:

- `capture_plane_a_cadence.lua` - attempted Lua execute-tap harness; MAME Lua API in this environment did not expose `install_execute_tap`.
- `plane_a_cadence_debug.cmd` - native-debugger fallback breakpoints.
- `native_debug_trace.log` - raw native debugger output (`1,091,138,321` bytes).
- `native_events.log` - extracted `EVENT` lines.
- `plane_a_cadence_summary.txt` - parsed event cadence summary.
- `plane_a_cadence_state_summary.txt` - per-state cadence summary.

Runtime event totals:

- VBlank boundaries: `1158`
- `runtime_genesis_pc 0x055B68` hits: `227`
- `runtime_genesis_pc 0x055B90` hits: `0`
- `0x055B68` hits with master state `s0=0002`: `226`

Ordinary steady gameplay subset (`scene=01`, `s0=0002`, `s2=0003`, `s4=0000`):

- `0x055B68` publications: `99`
- Maximum publications between VBlank boundaries: `1`
- Histogram: `0:1059`, `1:99`
- `0x055B90` was not observed.

Stage-entry/setup-like subset (`scene=01`, `s0=0002`, `s2=0002`, `s4=0004`):

- `0x055B68` publications: `127`
- Maximum publications between VBlank boundaries: `64`
- Histogram: `0:1156`, `63:1`, `64:1`

Representative ordinary event:

```text
EVENT ENTRY_055B68 cyc=94160706 pc=055B6A sr=2704 s0=0002 s2=0003 s4=0000 scene=01 sel=0000 strip=0000 group=0000 destA=00C08000 destB=00C08000 sxFG=015F syFG=0149 fgbase=0017 fgdirty=00 sp=00FEFFD6
```

Representative burst/setup event:

```text
EVENT ENTRY_055B68 cyc=153031784 pc=055B6A sr=2704 s0=0002 s2=0002 s4=0004 scene=01 sel=0000 strip=0000 group=0000 destA=00C08000 destB=00C08000 sxFG=0189 syFG=0120 fgbase=001D fgdirty=00 sp=00FEFFDA
```

### Resident-Origin Equation Status

Current Build 0235 projection derives the visible/resident logical row base as:

```text
resident_origin = (((-staged_scroll_y_fg + 8) & 0x01FF) >> 3) & 0x003F
```

A candidate native conversion would classify a logical row as resident when:

```text
physical_delta = (logical_row - resident_origin) & 0x003F
resident if physical_delta < 32
physical_row = physical_delta
```

However, Build 0235 commits gameplay Plane A vertical scroll as residual-only:

```text
VSRAM Plane A = (-staged_scroll_y_fg + 8) & 7
```

The full 64-row logical-to-32-row physical projection is therefore currently owned by `vdp_project_fg_tall_if_dirty`, not by the VDP scroll register. If converted producers stop writing `staged_fg_tall_buffer`, later projection-base changes can re-copy stale tall-buffer data into `staged_fg_buffer` and overwrite any native final-format Plane A rows/columns.

### Native/Legacy Ordering Status

Current VBlank order in `_vblank_service` is:

1. `vdp_project_bg_tall_if_dirty`
2. `vdp_commit_bg_strips_if_dirty`
3. `vdp_project_fg_tall_if_dirty`
4. `vdp_commit_fg_narrow_strips`
5. Broad dirty-row commits and remaining VBlank work

Same-frame native Plane A jobs could be made to commit after `vdp_project_fg_tall_if_dirty`, but this only makes same-frame ordering deterministic. It does not make later frames safe, because any later `vdp_project_fg_tall_if_dirty` execution can repopulate `staged_fg_buffer` from stale `staged_fg_tall_buffer`. Writing both native final-format jobs and tall-buffer cells would violate this task's conversion goal; disabling the projector without a complete resident-window migration would break the current residual-scroll model.

### Implementation Gate

The requested isolated conversion is not safe yet for three evidence-backed reasons:

1. The authorized `0x055B68` boundary is not exclusively a one-strip steady-gameplay path. The same boundary produced up to `64` publications between VBlank boundaries in the sampled stage-entry/setup state `2/2/4`.
2. `0x055B90` row publication was not observed in the targeted Build 0235 run, so the runtime row-job demand and direction behavior remain unmeasured.
3. Current gameplay Plane A visibility depends on tall-buffer projection plus residual VSRAM. A native final-format Plane A job would need either a full resident-window migration or a proven state-gated coexistence boundary. Neither was proven by this task.

### STOP

STOP triggered: **YES**.

No source changes, generated-data changes, ROM build, counter advance, or issue-ledger edits were performed. The safe next boundary is one of:

- prove and implement a complete Plane A resident-window migration, including initial fill, scroll/resident-origin ownership, projector disabling, and deterministic coexistence with unconverted frontend/scene-init paths; or
- prove a narrower state-gated steady-gameplay-only conversion boundary while preserving the burst/setup path on the legacy tall projection path; plus separately capture `0x055B90` vertical row behavior before implementing row jobs.

---

## 2026-07-27 - Complete Plane A Resident-Window Migration Gate

**Task:** Complete native Plane A resident-window migration proof gate.  
**Classification:** EXTENDING the accepted Build 0235 PC080SN native-YM7101 boundary work.  
**Result:** STOP before source implementation/build. The requested all-gameplay Plane A migration is not yet safely placeable.

### Baseline Confirmed

Accepted functional ROM remains Build 0235:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`
- SHA-256: `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`
- Build counter observed: `238`
- Numbered artifacts preserved: Build 0235, 0236, 0237, and 0238 all remain present; none were deleted or overwritten.
- No source/spec/Makefile/ROM/counter changes were made.

### New Focused Trace

Additional trace directory:

`states/traces/build0235_plane_a_resident_window_gate_20260727_013143/`

Artifacts:

- `resident_window_debug.cmd` - native debugger breakpoint logger.
- `input_only.lua` - copied from the prior Build 0235 cadence trace.
- `native_debug_trace.log` - raw trace, `414,115,392` bytes.
- `native_events.log` - extracted `EVENT` lines, `422,384` bytes / `2,048` lines.
- `exit_code.txt` - `124`; the bounded run timed out, but the required setup/caller evidence was captured before timeout.

### Phase 1.1 Setup Burst Proof

The sampled setup state was captured at `scene=01 s0=0002 s2=0002 s4=0004`. It is the scene-fill chain, not a steady one-strip gameplay path.

Address-map confirmed mappings:

- `arcade_pc 0x0503DC -> runtime_genesis_pc 0x0505DC`
- `arcade_pc 0x050434 -> runtime_genesis_pc 0x050634`
- `arcade_pc 0x055948 -> runtime_genesis_pc 0x055B48`
- `arcade_pc 0x055968 -> runtime_genesis_pc 0x055B68`
- `arcade_pc 0x055990 -> runtime_genesis_pc 0x055B90`
- `arcade_pc 0x055AB4 -> runtime_genesis_pc 0x055CB4`

Runtime event counts in the focused trace:

- `SCENE_FILL_ENTRY_0505DC`: `2`
- `SCENE_FILL_LOOP_050634`: `128`
- `DISPATCH_055B48`: `187`
- `STRIP_A_055B68`: `187`
- `STRIP_B_055B90`: `0`
- `SCROLL_COMMIT_055CB4`: `710`
- `ARCADE_VBLANK_RTE`: `833`

Stack/caller proof for the setup fill:

- At `runtime_genesis_pc 0x050634`, stack words were consistently `stack0=0005040A stack1=0004551C stack2=0003A85C` across all `128` setup-loop hits.
- At dispatcher `runtime_genesis_pc 0x055B48`, setup-stack signature was consistently `stack0=00050638 stack1=0005040A stack2=0004551C` across `128` setup hits.
- At strip body `runtime_genesis_pc 0x055B68`, setup-stack signature was consistently `stack0=00055B54 stack1=00050638 stack2=0005040A` across `128` setup hits.

Representative first setup chain:

```text
EVENT SCENE_FILL_LOOP_050634 cyc=38982312 pc=050636 sr=2700 s0=0002 s2=0002 s4=0004 scene=00 sel=0000 strip=0000 group=0000 destA=00C08000 destB=00C08000 sxFG=0000 syFG=0000 fgbase=0000 fgdirty=00 sp=00FEFFE6 stack0=0005040A stack1=0004551C stack2=0003A85C
EVENT DISPATCH_055B48 cyc=38982330 pc=055B4A sr=2700 s0=0002 s2=0002 s4=0004 scene=00 sel=0000 strip=0000 group=0000 destA=00C08000 destB=00C08000 sxFG=0000 syFG=0000 fgbase=0000 fgdirty=00 sp=00FEFFE2 stack0=00050638 stack1=0005040A stack2=0004551C
EVENT STRIP_A_055B68 cyc=38982372 pc=055B6A sr=2704 s0=0002 s2=0002 s4=0004 scene=00 sel=0000 strip=0000 group=0000 destA=00C08000 destB=00C08000 sxFG=0000 syFG=0000 fgbase=0000 fgdirty=00 sp=00FEFFDE stack0=00055B54 stack1=00050638 stack2=0005040A
```

Representative final captured setup row/column publication:

```text
EVENT SCENE_FILL_LOOP_050634 cyc=162203978 pc=050636 sr=2700 s0=0002 s2=0002 s4=0004 scene=01 sel=0000 strip=0003 group=000F destA=00C080FC destB=00C08000 sxFG=0189 syFG=0120 fgbase=001D fgdirty=01 sp=00FEFFE2 stack0=0005040A stack1=0004551C stack2=0003A85C
EVENT DISPATCH_055B48 cyc=162203996 pc=055B4A sr=2700 s0=0002 s2=0002 s4=0004 scene=01 sel=0000 strip=0003 group=000F destA=00C080FC destB=00C08000 sxFG=0189 syFG=0120 fgbase=001D fgdirty=01 sp=00FEFFDE stack0=00050638 stack1=0005040A stack2=0004551C
EVENT STRIP_A_055B68 cyc=162204038 pc=055B6A sr=2704 s0=0002 s2=0002 s4=0004 scene=01 sel=0000 strip=0003 group=000F destA=00C080FC destB=00C08000 sxFG=0189 syFG=0120 fgbase=001D fgdirty=01 sp=00FEFFDA stack0=00055B54 stack1=00050638 stack2=0005040A
```

Interpretation from the focused trace:

- The captured `2/2/4` setup burst is a scene-fill burst through `0x0505DC -> 0x050634 -> 0x055B48 -> 0x055B68`.
- For this Build 0235 Stage 1 capture, selector was `0`, so the fill used strip_A (`0x055B68`), not strip_B (`0x055B90`).
- The scene-fill burst still carries semantic/collision obligations because the same strip hook currently calls `genesistan_stage_fg_src_column` and `genesistan_stage_bg_collision_column` in gameplay scene context.
- The resident origin is not stable throughout the captured setup interval: `fg_tall_project_base` changed from `0x0000` at the first setup fill to `0x001D` by the second setup fill, while `sxFG/syFG` also changed (`0x0000/0x0000` to `0x0189/0x0120`). This rules out blindly writing setup publications into final physical rows without a post-setup origin proof.

### Phase 1.2 `0x055990 / 0x055B90` Status

`runtime_genesis_pc 0x055B90` was not observed in either Build 0235 trace:

- Prior cadence trace: `0` hits.
- Focused resident-window trace: `0` hits.

Static source/reference evidence says `0x055B90` is selected when `a5@0x10A8 != 0` and covers vertical direction rows (`selector 1/2`) plus selector-1 scene-fill geometry. However, the current Build 0235 runtime evidence still does not capture a live `0x055B90` row event under the accepted ROM. The prompt allowed a complete static bound if runtime was insufficient, but that static bound is not complete enough for implementation because the map-stream/event-transition path and post-setup resident timing remain unresolved for whole-game gameplay demand.

### Phase 1.3 Total Gameplay Publication Demand

Known static caller set to the shared tilemap1 dispatcher in Build 0235:

- `runtime_genesis_pc 0x050634`: scene-fill loop.
- `runtime_genesis_pc 0x0558FC`: selector-1 vertical gameplay trigger.
- `runtime_genesis_pc 0x055988`: selector-2 vertical gameplay trigger.
- `runtime_genesis_pc 0x055A22`: selector-0 horizontal gameplay trigger.

The whole-game demand gate remains incomplete:

- Horizontal ordinary gameplay was sampled and bounded at `<=1` publication/VBlank for the captured window.
- Setup scene-fill was proven to burst `64` publications per fill pass.
- Vertical `0x055B90` demand was not runtime-observed in accepted Build 0235.
- The current map-stream references explicitly retain unresolved event-completion/re-seed behaviour and record-boundary questions; therefore rare/later vertical/transition demand cannot be claimed comprehensively covered.

### Phase 2 VSRAM / Resident-Window Equation Status

Current Build 0235 code proves only the legacy tall-projection equation:

```text
resident_origin = (((-staged_scroll_y_fg + 8) & 0x01FF) >> 3) & 0x003F
VSRAM Plane A = (-staged_scroll_y_fg + 8) & 7   ; gameplay residual-only path
```

This is not the requested native full-scroll ownership proof. A likely native equation would use the same signed/bias source as full VSRAM value and derive final physical rows from the resident origin, but the prompt explicitly forbids blind `logical_row & 31` and requires proof of the full coarse+fine Plane A vertical scroll equation. That proof was not established here.

### Phase 3 Scene-Init Design Selection

Neither allowed scene-init design is safe yet:

- **Design A** (origin valid throughout setup) is rejected by the trace: setup begins with `fg_tall_project_base=0x0000` and later setup occurs with `fg_tall_project_base=0x001D`, so final physical placement is not proven stable throughout setup.
- **Design B** (origin final only after setup) is plausible, but the earliest authoritative post-setup boundary and required 32-row redraw contract were not proven.

### STOP

STOP triggered: **YES**.

The implementation gate failed before source edits. The exact remaining blockers are:

1. Runtime capture or complete proof of `0x055B90` row-path semantics and demand in accepted Build 0235 or a successor baseline.
2. Full Plane A VSRAM ownership proof: coarse+fine value, sign/wrap/+8 bias, and logical-to-physical row relation.
3. Earliest authoritative post-setup resident-origin boundary if choosing a Design-B initial redraw.
4. Whole-game publication demand proof beyond the captured Stage 1 horizontal/setup sample.

No ROM was produced, no counter was consumed, and no numbered build was deleted or overwritten.

## Original Arcade Scene-Fill Stability Proof

**Date:** 2026-07-27  
**Type:** Narrow original-arcade research and trace pass  
**Target:** MAME arcade `rastan` / Rastan World Rev 1  
**Scope:** Original arcade execution only. No Genesis production source/spec/Makefile/ROM/counter changes. No build. No Build 0235 tall-buffer/projector audit.

### Phase 0

Relevant priors: KF-010 (BG->Plane B, FG->Plane A), KF-011 (arcade VBlank owns frame progression), KF-038 (long PC080SN row-depth hazards in translated staging), KF-068 (native leaf-boundary video redesign context), and KF-071 (Build 0226 native plane pipeline/ring-row context). OPEN-001 and OPEN-017 are touched as graphics/native-video context only. No closed issue is changed. No contradiction of a CONFIRMED or STRONG finding was detected.

Classification: **EXTENDING**. This pass extends the native PC080SN boundary proof by using original arcade runtime as authority for scene-fill timing and stability.

### Evidence Artifacts

- Trace directory: `states/traces/original_arcade_scene_fill_stability_20260727_141526/`
- Debug script: `arcade_scene_fill_debug.cmd`
- Input/autostart script: `arcade_scene_fill_input.lua`
- Native trace: `native_debug_trace.log`
- Extracted events: `native_events.log`
- External frame log: `arcade_frame_events.tsv`
- Reduced summaries: `scene_fill_stability_summary.md`, `scene_fill_stability_summary.json`

The MAME run completed with exit status `0`. The native debugger trace is approximately `237 MB` and contains a complete instruction trace for the requested scene-fill window.

### Captured Fill IDs

One original-arcade scene-fill call reached `arcade_pc 0x0503DC` before the first Stage 1 gameplay-visible state.

| Fill ID | Entry | Loop | Publication call | Iterations | Selector `a5+0x10A8` | Plane A path | Plane B path | Exit | Displayed |
|---|---:|---:|---:|---:|---:|---|---|---:|---|
| Fill 1 | `0x0503DC` | `0x0503E4` | `0x050434` | `64` | `0x0000` | `0x055948 -> 0x055968` | `0x055C4A -> 0x055C5E -> 0x055C7A` | `0x050482` | Yes, first gameplay state |

Raw instruction counts in the trace:

```text
0x0503DC: 1
0x0503E4: 1
0x050482: 1
0x055948: 64
0x055968: 64
0x055990: 0
0x055C4A: 64
0x055C5E: 64
0x055C7A: 64
0x055AB4: 704
```

The row-path publisher `0x055990` did not execute in this captured final visible Stage 1 fill because the selector was `0`. Therefore selector-1/selector-2 row-path stability is not runtime-proven by this pass; it remains outside this specific Design-A verdict unless separately proven or bounded by static contract.

### Fill 1 State Samples

At the fill loop top:

```text
EVENT FILL_LOOP_TOP cyc=36420445 pc=0503E6 sr=2700 a5=0010C000 sel_10a8=0000 c0_10a0=00000000 c1_10a4=00000000 rc_10ca=0000 rc_10cc=0000 t0src_10fc=0003951C t0cur_1126=00000000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
```

First publication call:

```text
EVENT FILL_ITER_CALL cyc=36420583 pc=050436 sr=2700 a5=0010C000 d0=00000000 d1=00000000 d2=00000000 d7=00000128 sel_10a8=0000 c0_10a0=00C08000 c1_10a4=00C08000 rc_10ca=0000 rc_10cc=0000 t0src_10fc=0003951C t0cur_1126=00000000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
```

Last publication call:

```text
EVENT FILL_ITER_CALL cyc=38046531 pc=050436 sr=2700 a5=0010C000 d0=00000000 d1=00000000 d2=00001000 d7=001007FC sel_10a8=0000 c0_10a0=00C080FC c1_10a4=00C08000 rc_10ca=0003 rc_10cc=000F t0src_10fc=0003952E t0cur_1126=0003952E bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
```

Expected progression occurred: the Plane A destination cursor `a5+0x10A0` advanced from `0x00C08000` to `0x00C080FC` across the 64 publications, while the selector and all four authoritative scroll fields remained stable.

### Scroll Stability And Writer PCs

Authoritative scroll fields:

- Plane A / tilemap1 X scroll: `a5+0x10AE`
- Plane A / tilemap1 Y scroll: `a5+0x10B0`
- Plane B / tilemap0 X scroll: `a5+0x10EC`
- Plane B / tilemap0 Y scroll: `a5+0x10EE`

For Fill 1, all four scroll fields were `0x0000` at fill loop top, every logged publication, and the first gameplay-display VBlank return.

The only executed scroll-field writer PCs in the interval from fill entry through the first gameplay-display VBlank return were:

| Arcade PC | Instruction | Field | Observed effect in this run |
|---:|---|---|---|
| `0x05050E` | `move.w D1,($10ae,A5)` | Plane A X | wrote `0x0000` |
| `0x050512` | `move.w D1,($10ec,A5)` | Plane B X | wrote `0x0000` |
| `0x050518` | `move.w D1,($10b0,A5)` | Plane A Y | wrote `0x0000` |
| `0x05051C` | `move.w D1,($10ee,A5)` | Plane B Y | wrote `0x0000` |

No scroll-field writer was observed during the 64-iteration fill body itself. The post-fill writers above preserved the same zero mapping basis before first display.

The first scroll-register commit after the fill also wrote zero values for both tilemaps:

```text
EVENT HW_YSCROLL_WRITE cyc=38078239 pc=055ABA addr=00C20000 data=00000000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
EVENT HW_XSCROLL_WRITE cyc=38078263 pc=055AC2 addr=00C40000 data=00000000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
EVENT HW_YSCROLL_WRITE cyc=38078287 pc=055ACA addr=00C20002 data=00000000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
EVENT HW_XSCROLL_WRITE cyc=38078311 pc=055AD2 addr=00C40002 data=00000000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
```

### First Display Relation

The fill completed before the first frame that can display the Stage 1 gameplay state.

- Last captured fill publication: `cyc=38046531`
- First scroll commit after fill: `cyc=38078239..38078311`, all zero scroll values
- First arcade VBlank RTE with gameplay state `2/3/0`: `cyc=38092209`
- External frame log first reports state `2/3/0` at MAME frame `307`

First gameplay VBlank return:

```text
EVENT ARCADE_VBLANK_RTE_03A07E cyc=38092209 pc=03A080 sr=2004 a5=0010C000 s0=0002 s2=0003 s4=0000 bgx_10ec=0000 bgy_10ee=0000 fgx_10ae=0000 fgy_10b0=0000
```

No later fill replaced or invalidated Fill 1 before this first gameplay-visible frame.

### Plane A Verdict

For the captured final visible Stage 1 fill, Plane A is **Design A valid**.

Evidence:

- The mapping basis was established before the first publication call: selector `0`, cursor `a5+0x10A0=0x00C08000`, scrolls all zero.
- The selector remained `0` for all 64 publications.
- The active Plane A publisher was `0x055948 -> 0x055968`, hit 64 times.
- The Plane A row-path publisher `0x055990` did not execute in this fill.
- Plane A scroll fields `a5+0x10AE` and `a5+0x10B0` remained `0x0000` throughout the fill and through first display.
- The only executed Plane A scroll writers before first display were `0x05050E` and `0x050518`, both preserving zero in this start case.

Design B is **not required** for this captured Plane A fill. The evidence does not show a mid-fill or post-fill/pre-display mapping change.

Caveat: this verdict is for the selector-0 final visible Stage 1 fill. It does not by itself runtime-prove selector-1/selector-2 `0x055990` row-path fills.

### Plane B Verdict

For the captured final visible Stage 1 fill, Plane B is **Design A valid**.

Evidence:

- The tilemap0 source/bookkeeping basis was established before and during the fill: `a5+0x10FC` began at `0x0003951C`, and `a5+0x1126` advanced to `0x0003952E` by the final logged publication.
- The tilemap0 fill path `0x055C4A -> 0x055C5E -> 0x055C7A` executed 64 times.
- Plane B scroll fields `a5+0x10EC` and `a5+0x10EE` remained `0x0000` throughout the fill and through first display.
- The only executed Plane B scroll writers before first display were `0x050512` and `0x05051C`, both preserving zero in this start case.
- The hardware scroll commit at `0x055AB4` wrote zero values for both BG and FG scroll registers before the first gameplay frame.

Design B is **not required** for this captured Plane B fill. The evidence does not show a mid-fill or post-fill/pre-display mapping change.

### Arcade Visual Ownership Check

At first Stage 1 visibility, the completed fill immediately preceding the frame is Fill 1. The original arcade draw model remains:

- tilemap0 / BG owns the opaque background plane, corresponding to Genesis Plane B in the native contract.
- tilemap1 / FG owns the transparent foreground/playfield plane, corresponding to Genesis Plane A in the native contract.
- sprites draw in front of the tilemaps.

The first visible Stage 1 frame in this capture is the opening outdoor window. Cave and rope components are not visually present in that first window, so this pass does not claim a runtime visual proof of cave/rope correctness. It does prove that the original arcade's first displayed Stage 1 tilemap result is filled before display from a stable selector-0 mapping basis.

### Design Choice

**Design choice: A, for the captured original-arcade final visible Stage 1 scene-fill.**

Direct native generation during the arcade fill is supported for this observed fill because:

1. authoritative scroll values were known before publication;
2. scroll values remained fixed through all 64 iterations;
3. cursor/ring progression was deterministic and expected;
4. scroll/mapping remained fixed through the first display frame;
5. both Plane A and Plane B publication paths executed 64 times;
6. no later fill invalidated the result before display.

**Ready for native implementation contract:** YES for the selector-0 first-visible Stage 1 fill contract. A whole-game/native-global contract still needs either separate runtime proof or a static contract for selector-1/selector-2 `0x055990` row-path fills and later lifecycle fills.

### STOP Status

STOP triggered: **NO** for the requested original-arcade first-visible scene-fill stability proof.

No production source, spec, Makefile, ROM, counter, or numbered build artifact was changed.

## Original Arcade Global Fill and Vertical-Streaming Contract

**Date:** 2026-07-27  
**Agent:** Cody  
**Scope:** Original arcade authority / contract proof only. No production source, spec, Makefile, ROM, build, or counter changes. Build 0235 is preserved only as the accepted reference artifact; Build 0235 tall-buffer/projector behavior is not used as authority.

### Accepted Build Reference Preserved

- Accepted Build 0235 reference ROM: `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`
- SHA-256: `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`
- Current counter observed: `238`
- Production source changed: **NO**
- ROM/build/counter changed: **NO**

### Original Arcade Evidence Used

Runtime artifact preserved from the prior original-arcade MAME run:

- `states/traces/original_arcade_scene_fill_stability_20260727_141526/`
- `arcade_frame_events.tsv`
- `native_events.log`
- `scene_fill_stability_summary.md`
- `scene_fill_stability_summary.json`

No new uncontrolled instruction trace was produced in this pass. The selector-0 runtime fill proof reuses the preserved targeted event extraction. The selector-1/selector-2 and gameplay-streaming contract below is opcode/static-backed by the original arcade reference files:

- `docs/arcade_reference/pc080sn/scene_initialization_assembly.md`
- `docs/arcade_reference/pc080sn/gameplay_control_assembly.md`
- `docs/arcade_reference/pc080sn/map_stream_format.md`
- `docs/arcade_reference/pc080sn/README.md`

### Fill Classes Identified

The original arcade scene-fill routine `arcade_pc 0x0503DC` has one direct caller: `arcade_pc 0x050206 bsr.w 0x0503DC` inside the scene/reinit routine `arcade_pc 0x0501E2`. The fill loop body starts at `arcade_pc 0x0503E4` and runs exactly 64 iterations.

The selector value is `a5+0x10A8`, loaded from the map stream by `arcade_pc 0x0558F8` / `0x055940`.

| Fill class | Evidence type | Path | Verdict |
|---|---|---|---|
| selector `0` | runtime captured | `0x0503DC -> 0x050434 -> 0x055948 -> 0x055968` | **Design A valid** for captured first-visible Stage 1 fill |
| selector `1` | opcode/static bounded | `0x0503DC -> 0x050434 -> 0x055948 -> 0x055990 -> 0x055A14` | **Design A valid** as a full 64-row bottom-to-top fill |
| selector `2` | map-stream/static bounded | selector `2` exists in gameplay stream records, but no stage-LUT scene-fill target with first selector `2` is identified | **No live selector-2 scene-fill class proven; selector-2 is a gameplay vertical-streaming selector** |

#### Selector-0 Fill Verdict

The preserved original-arcade runtime trace captured the first visible Stage 1 fill with selector `0`:

- `0x0503DC`: `1`
- `0x0503E4`: `1`
- `0x050434`: `64`
- `0x055948`: `64`
- `0x055968`: `64`
- `0x055990`: `0`
- `0x055C4A/0x055C5E/0x055C7A`: `64` each

The mapping basis was stable before the first publication and remained stable through first display: Plane A scroll fields `a5+0x10AE/0x10B0` and Plane B scroll fields `a5+0x10EC/0x10EE` stayed zero through the fill and first gameplay-visible VBlank. This is a runtime **Design A** fill class.

#### Selector-1 Fill Verdict

The selector-1 fill is opcode-bounded. At `arcade_pc 0x0503E4`, selector `1` takes the special fill setup:

- `a5+0x10F8 = 0x00C00000` for tilemap0 / Plane B.
- `a5+0x10A0 = 0x00C08000`.
- `a5+0x10A4 = 0x00C0BF00`.
- Loop counter `a5+0x10AA = 64`.

Each iteration calls `0x055948`, which dispatches selector `1` to `0x055990`. `0x055990` emits 16 descriptor cells through `0x055A14`; `0x055A14` emits 4 cells per descriptor. One `0x055990` call therefore publishes 64 cells = `0x100` bytes = one full 64-tile row.

After each selector-1 iteration, the scene-fill loop decrements `a5+0x10A4` by `0x100`. Therefore:

- Iteration 0 writes row 63: `0x00C0BF00..0x00C0BFFF`.
- Iteration 63 writes row 0: `0x00C08000..0x00C080FF`.
- The fill touches exactly `0x00C08000..0x00C0BFFF`.
- No rowscroll/unused region is used.
- No row overlap or mid-fill scroll retarget is present in the opcode path.

This is a static/original-opcode **Design A** fill class.

#### Selector-2 Fill Verdict

Selector `2` appears in the original map stream as a vertical gameplay direction selector, but the machine-enumerated map-stream table does not identify a stage-LUT scene-fill target whose first selector is `2`. The selector-2 rows in the stream table are non-stage-LUT targets, so they are reached through the gameplay stream walk rather than the scene-init `0x0503DC` fill re-seed.

Additionally, the scene-fill setup has only a selector-1 special branch. A hypothetical selector-2 direct scene-fill would dispatch to `0x055990`, but it would not take the selector-1 row-cursor decrement path that advances `a5+0x10A4`. Because no live selector-2 scene-fill class is identified, native implementation should not invent one. Selector `2` belongs to the gameplay vertical-streaming contract below.

### `0x055990` Scene-Fill Evidence

For selector `1`, `0x055990` is a scene-fill row publisher:

- Entry cursor: `a5+0x10A4`.
- Cell publisher: `0x055A14`.
- Per call: 16 descriptor iterations x 4 cells = 64 cells.
- Fill geometry: one full logical row per call.
- Scene fill: 64 calls, rows 63 -> 0.

This proves that selector-1 fill is not a post-fill projection problem; the original arcade fills the full logical Plane A map with a stable row basis before display.

### `0x055990` Gameplay Evidence

During gameplay, selector `1` and selector `2` both use `0x055990`, but as vertical strip/row streamers triggered by 8-pixel vertical crossings.

Selector `1` path (`arcade_pc 0x0556A6`):

- Accumulates `a5+0x10B4 += a5+0x10DA`.
- On bit-3 crossing, computes `a5+0x10A4 = 0x00C08000 + (0x3F00 - ((a5+0x10CC << 10) + (a5+0x10CA << 8)))`.
- Calls `0x055948 -> 0x055990`.
- Updates Plane A logical Y scroll `a5+0x10B0 = (a5+0x10B0 + a5+0x10DA) & 0x01FF`.

Selector `2` path (`arcade_pc 0x055738`):

- Accumulates `a5+0x10B6 += a5+0x10DA`.
- On bit-3 crossing, computes `a5+0x10A4 = 0x00C08000 + ((a5+0x10CC << 10) + (a5+0x10CA << 8))`.
- Calls `0x055948 -> 0x055990`.
- Updates Plane A logical Y scroll `a5+0x10B0 = (a5+0x10B0 - a5+0x10DA) & 0x01FF`.

Thus `0x055990` has two roles: selector-1 full-map scene-fill row publisher, and selector-1/2 gameplay vertical row streamer.

### Publication Limits

For ordinary gameplay frames, the original direction dispatcher is mutually exclusive by selector. Only the active selector publishes; inactive selectors latch pending bits and do not publish. Each active selector branch has one 8-pixel crossing test and one publication call path.

- Maximum Plane A columns per gameplay frame: `1` (`selector 0 -> 0x055968`).
- Maximum Plane A rows per gameplay frame: `1` (`selector 1/2 -> 0x055990`).
- Maximum combined Plane A publications per gameplay frame: `1` ordinary gameplay publication, because direction selectors are mutually exclusive.
- Scene-fill exception: `0x0503DC` intentionally publishes `64` Plane A strips during scene initialization before first display.

### Plane B Gameplay Path

Plane B / tilemap0 uses the path `0x055C4A -> 0x055C5E -> 0x055C7A` during scene fill, and the gameplay vertical tilemap0 streamer caller at `arcade_pc 0x055B8E` inside the `0x055B60` routine.

The gameplay tilemap0 path streams rows on vertical 8-pixel crossings, using tilemap0 state fields and destination:

- `a5+0x10F4` / `a5+0x10F6` as tilemap0 row/sub-index state.
- Destination basis: `0x00C00000 + (a5+0x10F4 << 6) + (a5+0x10F6 << 2)`.
- No collision production occurs on tilemap0.
- Plane B X scroll is half-rate parallax via `0x055B92 lsr.w #1`, stored at `a5+0x10EC`.
- Plane B Y scroll is stored at `a5+0x10EE`.

Maximum Plane B gameplay rows per frame: `1` ordinary gameplay row publication, bounded by the same bit-3 crossing style as the tilemap0 vertical streamer.

### Logical Scroll Equations

The arcade PC080SN stores scroll fields in WRAM and commits them through `arcade_pc 0x055AB4`:

Plane A / tilemap1:

- `A_x = a5+0x10AE`, committed to `HW_ADDRESS 0x00C40002`.
- `A_y = a5+0x10B0`, committed to `HW_ADDRESS 0x00C20002`.
- Selector `0`: `A_x = (A_x - a5+0x10D8) & 0x01FF` on horizontal crossings.
- Selector `1`: `A_y = (A_y + a5+0x10DA) & 0x01FF` on vertical crossings.
- Selector `2`: `A_y = (A_y - a5+0x10DA) & 0x01FF` on vertical crossings.

Plane B / tilemap0:

- `B_x = a5+0x10EC`, committed to `HW_ADDRESS 0x00C40000`.
- `B_y = a5+0x10EE`, committed to `HW_ADDRESS 0x00C20000`.
- `B_x` is the half-rate parallax field maintained by the `0x055B60` family.
- `B_y` advances with the tilemap0 vertical streamer.

MAME PC080SN treats the committed scroll as device scroll input with the PC080SN internal sign convention. The native YM7101 contract should express the Genesis visible scroll in terms of the arcade logical scroll field plus the established Genesis display-origin correction.

### Native Mapping Equations

For native YM7101 representation, Plane A and Plane B should each be a resident 32-row physical projection of the original PC080SN 64-row logical map. The corrected display-origin bias is `+8` pixels.

Plane A / tilemap1 native mapping:

```text
A_native_scroll_y = ((-A_y + 8) & 0x01FF)
A_logical_top_row = (A_native_scroll_y >> 3) & 0x003F
A_fine_y = A_native_scroll_y & 0x0007
A_physical_row(logical_row) = logical_row & 0x001F
A_physical_col(logical_col) = logical_col & 0x003F
```

Plane B / tilemap0 native mapping:

```text
B_native_scroll_y = ((-B_y + 8) & 0x01FF)
B_logical_top_row = (B_native_scroll_y >> 3) & 0x003F
B_fine_y = B_native_scroll_y & 0x0007
B_physical_row(logical_row) = logical_row & 0x001F
B_physical_col(logical_col) = logical_col & 0x003F
```

Residency rule for both planes:

```text
resident if ((logical_row - logical_top_row) & 0x003F) < 32
```

Within that resident window, the logical row is written to `logical_row & 31` in the YM7101 32-row plane. This is the native equivalent of keeping the original 64-row PC080SN logical ring while projecting only the currently resident 32 rows into Genesis VRAM.

### Logical And Physical Wrap Proofs

Logical 63 -> 0 proof:

- The original arcade ring is 64 rows/columns deep: `a5+0x10CA` runs `0..3`, `a5+0x10CC` runs `0..15`, for `4 * 16 = 64` publications per direction byte.
- Arcade scroll fields are masked with `& 0x01FF`, exactly 512 pixels = 64 tiles.
- Therefore logical row 63 -> 0 is the intended PC080SN wrap boundary.

Physical 31 -> 0 proof for native YM7101:

- Genesis Plane A/B physical nametables in this contract are 64 x 32 cells.
- A resident 32-row projection maps `logical_row & 0x001F`.
- Therefore logical rows 31 -> 32 map physical rows 31 -> 0, and logical rows 63 -> 0 also map physical rows 31 -> 0 at the 64-row logical wrap.
- The residency window prevents simultaneous authoritative use of two logical rows separated by 32 within the same physical row.

### Design-A / Design-B Fill Classes

Design A fill classes identified:

- selector-0 Plane A scene fill: runtime-proven for first-visible Stage 1.
- selector-1 Plane A scene fill: opcode-bounded full-row fill from row 63 to row 0.
- Plane B scene fill: runtime-proven for first-visible Stage 1 and statically parallel through `0x055C4A` for the scene fill loop.

Design B fill classes identified:

- **None** from the original arcade evidence in this pass.

Selector-2 is not classified as a scene-fill Design A or Design B class because no live selector-2 `0x0503DC` fill entry was identified. It is instead part of the gameplay vertical-streaming contract.

### Architecture Compliance

CONFIRMED. The arcade code remains the program. The native YM7101 contract above is a rendering/hardware-service interpretation of original PC080SN publications and scroll fields; it does not introduce Genesis-owned gameplay flow, second renderers, hardcoded coordinates, or state forcing.

### Open / Closed Issues Impact

- Open issues touched: OPEN-001 and OPEN-017 as native-video / graphics architecture context only.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: rope/collision behavior, PC090OJ sprites, enemy damage, audio, Build 0235 runtime behavior.

### KNOWN_FINDINGS Impact

Option A - no new finding to index. This pass consolidates the PC080SN native Plane A/Plane B implementation contract from original arcade evidence, but does not by itself close or supersede an indexed finding.

### Remaining Blockers

No blocker remains for a coherent Plane A/Plane B native implementation contract that uses:

- original arcade 64-row logical maps;
- a 32-row YM7101 resident projection;
- producer-local strip publication;
- the `+8` Genesis display-origin correction;
- per-plane logical scroll fields from the original arcade state.

Selector-2 direct scene-fill remains unproven as a live class and should not be implemented as a special fill path unless future original-arcade evidence shows it can reach `0x0503DC`. This is not a blocker for gameplay vertical streaming, where selector-2 is already opcode-bounded.

**Ready for coherent Plane A/Plane B native implementation:** YES.
