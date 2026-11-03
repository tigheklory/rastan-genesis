# Andy — Diagnostic Debt Audit

## 1. Executive Summary

This audit inventories every temporary, proof-only, suppression, instrumentation, or diagnostic change currently present in the Rastan Genesis project source files. Sources: current source code state, AGENTS_LOG.md, and design documents. 11 items are active. 2 items are historical (reverted or superseded). 5 items are HIGH-RISK contaminants that affect runtime behavior and could invalidate debugging conclusions.

---

## 2. Active Temporary / Diagnostic Changes Still Present

### Item 1 — FG Buffer Sentinel Force Write
- **Category**: `TEMPORARY_SENTINEL_TEST`
- **File**: `apps/rastan/src/boot/sega.s`
- **Location**: `_VINT_arcade_mode`, line 266
- **Exact code**: `move.w #0xFFFF, pc080sn_fg_buffer`
- **Current behavior**: Forces FG buffer word 0 to 0xFFFF every VBlank before the arcade tick executes. Overwrites whatever the arcade tick would have written to cell (x=0, y=0).
- **Why added**: Build 325 — prove whether the arcade tick zeroes the FG buffer or whether the buffer is simply never populated.
- **Meant to be temporary**: YES — labeled "TEMP SENTINEL PROOF TEST"
- **Still present**: YES
- **Changes runtime behavior**: YES — forces a nametable entry at Plane A position (0,0) that the arcade code never writes
- **Changes visible output**: YES — tile 0x7FF (all bits set) at top-left of Plane A
- **Can contaminate debugging conclusions**: YES — any analysis of FG buffer content at index 0 is unreliable while this is active

### Item 2 — FG Buffer Before/After Capture (fg_debug_before / fg_debug_after)
- **Category**: `INSTRUMENTATION`
- **File**: `apps/rastan/src/boot/sega.s`
- **Location**: `_VINT_arcade_mode`, lines 268–273
- **Exact code**:
  ```asm
  move.w  pc080sn_fg_buffer, %d0
  move.w  %d0, fg_debug_before
  jsr     genesistan_run_arcade_tick_lean
  move.w  pc080sn_fg_buffer, %d0
  move.w  %d0, fg_debug_after
  ```
- **Current behavior**: Captures FG buffer[0] into BSS variables before and after the arcade tick on every VBlank frame.
- **Why added**: Build 326 — capture numeric proof of sentinel survival across the tick.
- **Meant to be temporary**: YES
- **Still present**: YES
- **Changes runtime behavior**: YES — adds 5 memory read/write instructions per VBlank; does not affect game state
- **Changes visible output**: NO
- **Can contaminate debugging conclusions**: LOW — counters are passive captures, no side effects on game logic

### Item 3 — Debug FG Proof Overlay (genesistan_debug_fg_proof)
- **Category**: `DEBUG_OVERLAY`
- **File**: `apps/rastan/src/main.c`, `apps/rastan/src/boot/sega.s`
- **Location**: `genesistan_debug_fg_proof()` (main.c ~1846); called from `_VINT_arcade_mode` line 276
- **Current behavior**: Every VBlank, renders debug text at FG buffer rows 1–5 (cols 1–13): "B:XXXX A:XXXX" (sentinel before/after), "P:XXXXXXXX" (bulk read pointer), "M:XXXX XXXX XXXX" (workram words 0–4), "I:XXXX" (raw input), "K:UDLR12SC" (button state). Writes directly to `pc080sn_fg_buffer` via `rastan_draw_tile_xy()`.
- **Why added**: Build 326/330 — on-screen proof of FG buffer state and arcade input activity.
- **Meant to be temporary**: YES
- **Still present**: YES
- **Changes runtime behavior**: YES — overwrites FG buffer cells at rows 1–5, cols 1–13 every frame with debug tile data. This permanently clobbers any attract-mode text that would appear in those cells.
- **Changes visible output**: YES — visible debug overlay on screen if Plane A is visible
- **Can contaminate debugging conclusions**: YES — HIGH. The overlay occupies 5 rows × 13 cols of FG buffer. Any analysis of attract-mode text content in those positions is invalid while this is active. Also, the `jsr genesistan_debug_fg_proof` executes BEFORE `jsr genesistan_pc080sn_commit_planes`, so the overlay is committed every frame.

### Item 4 — Build 336 VDP Commit Counter 3-Frame History Instrumentation
- **Category**: `INSTRUMENTATION`
- **File**: `apps/rastan/src/boot/sega.s`
- **Location**: `_VINT_arcade_mode`, lines 225–256
- **Current behavior**: Every VBlank entry: rolls 3-frame history of frame ID + per-function commit counts (planes, palette, scroll), then resets per-frame counters. Consumes 30 instructions per VBlank frame (24 `move.w` + 4 `addq/clr`).
- **Why added**: Build 336 — count VDP commit executions per frame to prove double-commit theory.
- **Meant to be temporary**: YES
- **Still present**: YES
- **Changes runtime behavior**: YES — adds ~30 instructions at VBlank entry before any game logic; timing impact is measurable but small on 68000 at 7.67 MHz
- **Changes visible output**: NO
- **Can contaminate debugging conclusions**: LOW — passive instrumentation; no effect on game logic or VDP state

### Item 5 — VDP Commit Counter Increments (planes, palette, scroll)
- **Category**: `INSTRUMENTATION`
- **Files**: `startup_trampoline.s` (lines 881, 96), `main.c` (line 1780)
- **Location**: Top of `genesistan_pc080sn_commit_planes`, `genesistan_palette_commit_asm`, `genesistan_scroll_commit_vdp`
- **Current behavior**: Each commit function increments its dedicated word counter (`vdp_commit_planes_count`, `vdp_commit_palette_count`, `vdp_commit_scroll_count`) on every call.
- **Why added**: Build 336 — count commit executions per frame.
- **Meant to be temporary**: YES
- **Still present**: YES
- **Changes runtime behavior**: YES — 3 extra `addq.w` instructions per frame total; negligible timing impact
- **Changes visible output**: NO
- **Can contaminate debugging conclusions**: NO

### Item 6 — Row Visibility Filter Disabled (text_writer_ptr_to_xy)
- **Category**: `TEMPORARY_SUPPRESSION`
- **File**: `apps/rastan/src/main.c`
- **Location**: `text_writer_ptr_to_xy()`, lines 1407–1409
- **Exact code**:
  ```c
  /* TEMP DEBUG: disable row visibility filtering to diagnose empty plane */
  /* if (row_val < TEXT_WRITER_VISIBLE_ROW_BIAS)
      return FALSE; */
  ```
- **Current behavior**: Allows all text rows (including rows 0–3 which are technically off-screen per original `TEXT_WRITER_VISIBLE_ROW_BIAS`) to pass through to `rastan_draw_tile_xy()`. Without this filter, cells in rows 0–3 are placed at negative or near-zero Y coordinates on the FG plane.
- **Why added**: Build 324 — after the row-major fix caused an empty Plane A, the filter was disabled to determine whether any text was reaching the FG buffer at all.
- **Meant to be temporary**: YES — labeled "TEMP DEBUG"
- **Still present**: YES
- **Changes runtime behavior**: YES — text cells in rows 0–3 that would normally be rejected now get written to the FG buffer
- **Changes visible output**: YES — may produce off-screen or unexpected tile placements for text items in rows 0–3
- **Can contaminate debugging conclusions**: YES — MEDIUM. Row 0 text items will appear at Y=0 on Plane A instead of being filtered. Any analysis of what text content is present at the top of the FG buffer is affected.

### Item 7 — Sprite Renderer Assembly Early Return (Build 329)
- **Category**: `TEMPORARY_EARLY_RETURN`
- **File**: `apps/rastan/src/startup_trampoline.s`
- **Location**: `genesistan_render_sprites_vdp_asm`, line 214
- **Exact code**: `rts` (first instruction after label, before any register save)
- **Current behavior**: Entire assembly sprite renderer is suppressed. No sprite tile DMA, no SAT writes via this path. The C-side `genesistan_render_sprites_vdp()` still executes via the hook, but `genesistan_render_sprites_vdp_asm` itself returns immediately.
- **Why added**: Build 329 — isolate Plane A visibility by suppressing sprite layer output.
- **Meant to be temporary**: YES — labeled "Build 329 proof-only"
- **Still present**: YES
- **Changes runtime behavior**: YES — this is one of two sprite paths. The assembly path is fully disabled.
- **Changes visible output**: YES — sprites normally rendered through this path are absent
- **Can contaminate debugging conclusions**: YES — HIGH. Any analysis of sprite behavior, visible sprite count, SAT state, or sprite DMA activity is unreliable while this early return is active.

### Item 8 — Sprite SAT DMA Suppression in C Function (Build 339)
- **Category**: `TEMPORARY_SUPPRESSION`
- **File**: `apps/rastan/src/main.c`
- **Location**: `genesistan_render_sprites_vdp()`, lines 2057–2059
- **Exact code**:
  ```c
  /* Build 339 proof-only: keep sprite path logic active, suppress only SAT DMA commit. */
  /* VDP_updateSprites(sprite_count, DMA); */
  /* VDP_waitDMACompletion(); */
  ```
- **Current behavior**: All sprite processing logic executes (workram reads, coordinate transforms, palette maps, `VDP_setSpriteFull()` shadow writes), but the final `VDP_updateSprites(DMA)` that would commit the SAT shadow to VRAM 0xF800 is commented out. No DMA occurs. SAT VRAM is never updated via this path.
- **Why added**: Build 339 — suppress the uncounted DMA writer path (identified in census audit) as a proof test.
- **Meant to be temporary**: YES — labeled "Build 339 proof-only"
- **Still present**: YES
- **Changes runtime behavior**: YES — sprites are processed but never committed to SAT. Combined with Item 7 (assembly rts), all sprite SAT writes are completely suppressed.
- **Changes visible output**: YES — no sprites visible at all when both Item 7 and Item 8 are active
- **Can contaminate debugging conclusions**: YES — HIGH. No sprite content is visible. Any analysis of rolling dots, sprite rendering, or SAT state is invalid.

### Item 9 — Bulk Preload Check Early Return (Build 335)
- **Category**: `TEMPORARY_EARLY_RETURN`
- **File**: `apps/rastan/src/main.c`
- **Location**: `genesistan_bulk_preload_check()`, lines 1649–1659
- **Exact code**: `(void)source_addr; return;`
- **Current behavior**: All tick-phase scene preload DMA calls are suppressed. The function returns immediately without triggering `genesistan_preload_scene_tiles()` or any DMA. Tile preload during the arcade tick never happens.
- **Why added**: Build 335 — remove the non-VBlank DMA writer path identified as a VDP contaminant.
- **Meant to be temporary**: YES
- **Still present**: YES
- **Changes runtime behavior**: YES — no scene tile updates happen during the arcade tick. Tiles must be preloaded at init time only.
- **Changes visible output**: YES — if the arcade tick expects to swap tile VRAM during scene transitions, those transitions will be silent (no tile data change)
- **Can contaminate debugging conclusions**: MEDIUM — suppresses a VDP write path; any analysis of scene-transition tile loading behavior is invalid.

### Item 10 — Test Palette Active at Arcade Handoff (Build 331)
- **Category**: `TEMPORARY_PALETTE_TEST`
- **File**: `apps/rastan/src/main.c`
- **Location**: `apply_post_reset_test_palette()` called from `request_start_rastan()`, line 2261
- **Exact code**: Writes a 16-color rainbow test palette to all 4 CRAM lines (64 entries) immediately after `force_clean_vram_init()` clears CRAM.
- **Current behavior**: At arcade handoff, after CRAM is zeroed, it is immediately overwritten with a known test palette (0x0EEE, 0x00EE, 0x0E0E, etc.). The runtime CLCS palette commit then begins overwriting this each VBlank. On frame 0 the test palette is visible.
- **Why added**: Build 331 — validate that the post-reset black period transitions to a known visible state before runtime CLCS palette flow takes over.
- **Meant to be temporary**: YES — labeled "Build 331 proof-only"
- **Still present**: YES
- **Changes runtime behavior**: YES — inserts a one-frame write to CRAM at handoff with a non-zero test palette
- **Changes visible output**: YES — potentially one frame of test palette colors visible at scene start
- **Can contaminate debugging conclusions**: LOW — effect is confined to frame 0 at handoff; runtime palette commit overrides it immediately

### Item 11 — BSS Diagnostic Variable Block (sega.s)
- **Category**: `INSTRUMENTATION`
- **File**: `apps/rastan/src/boot/sega.s`
- **Location**: `.section .bss`, lines 491–532
- **Symbols**: `fg_debug_before`, `fg_debug_after`, `bulk_debug_pre_read_a0`, `vdp_commit_frame_id`, `vdp_commit_planes_count`, `vdp_commit_palette_count`, `vdp_commit_scroll_count`, `vdp_commit_last_frame_id_0/1/2`, `vdp_commit_last_planes_count_0/1/2`, `vdp_commit_last_palette_count_0/1/2`, `vdp_commit_last_scroll_count_0/1/2` (18 words + 1 long = 38 bytes)
- **Current behavior**: BSS storage for all instrumentation. Zero-initialized at startup. Accessed by Items 1–5.
- **Why added**: Multiple builds (325–336) — storage for diagnostic captures.
- **Meant to be temporary**: YES
- **Still present**: YES
- **Changes runtime behavior**: NO — BSS allocation; no active execution
- **Changes visible output**: NO
- **Can contaminate debugging conclusions**: NO

---

## 3. Temporary / Diagnostic Changes Found in History But Not Active Now

### History Item A — Build 314 Mode Gate on genesistan_pc080sn_commit_planes
- **Exact change**: `cmpi.w #2, 4(%a0)` gate at top of `genesistan_pc080sn_commit_planes`; routine returned early (`.Lcommit_skip: rts`) unless `arcade_mode4 >= 2`. This prevented plane commits during attract/title mode.
- **Source**: `AGENTS_LOG.md` Build 314 entry; design doc `build322_fg_text_coordinate_transpose_audit.md`
- **Still present**: NO — removed; commit runs unconditionally in current code
- **May have affected later reasoning**: YES — removing this gate was the direct cause of the "empty Plane A" investigation (builds 322–327), because the gate removal exposed that attract-mode content was never being written to the FG buffer.

### History Item B — Unconditional Zero Scroll (Build 322)
- **Exact change**: `genesistan_scroll_commit_vdp()` was temporarily changed to write zero to all four scroll values unconditionally, removing any mode gate.
- **Source**: `AGENTS_LOG.md` Build 322 entry; design doc `build322_unconditional_zero_scroll_proof_fix.md`
- **Still present**: NO — current `genesistan_scroll_commit_vdp()` reads `staged_scroll_*` variables instead of forcing zeros.
- **May have affected later reasoning**: NO — current scroll behavior uses staged values from hooks as intended.

---

## 4. High-Risk Contaminants

| Item # | Short Name | Risk Reason | Severity |
|--------|-----------|-------------|----------|
| 1 | FG Sentinel Force Write | Forces 0xFFFF into FG buffer[0] every frame — corrupts any arcade-generated nametable data at cell (0,0); renders analysis of attract-mode tile content at that position invalid | HIGH |
| 3 | Debug FG Proof Overlay | Overwrites 5 rows × 13 cols of FG buffer every VBlank before the plane commit — permanently clobbers attract-mode FG content in that region; any analysis of what the arcade ROM writes to those cells is invalid | HIGH |
| 7 | Sprite Assembly Early Return | Completely disables `genesistan_render_sprites_vdp_asm`; sprite tile DMA and SAT writes via assembly path never occur; combined with Item 8, all sprite output is suppressed | HIGH |
| 8 | Sprite SAT DMA Suppression | Comments out `VDP_updateSprites(DMA)` — SAT VRAM never updated via C path; combined with Item 7, zero sprites appear on screen | HIGH |
| 6 | Row Visibility Filter Disabled | Allows rows 0–3 text cells (normally filtered) to be written to FG buffer at Y=0; analysis of top-of-screen FG content includes rows that should not appear | MEDIUM |
| 9 | Bulk Preload Early Return | Suppresses all tick-phase tile DMA; scene tile preload behavior during arcade tick is entirely absent; analysis of tile-update behavior is invalid | MEDIUM |

---

## 5. Master Cleanup Candidates

| Item # | Short Name | Category | Status | Cleanup Priority |
|--------|-----------|----------|--------|-----------------|
| 1 | FG Sentinel Force Write | `TEMPORARY_SENTINEL_TEST` | ACTIVE | IMMEDIATE |
| 2 | FG Before/After Capture | `INSTRUMENTATION` | ACTIVE | IMMEDIATE |
| 3 | Debug FG Proof Overlay | `DEBUG_OVERLAY` | ACTIVE | IMMEDIATE |
| 6 | Row Visibility Filter Disabled | `TEMPORARY_SUPPRESSION` | ACTIVE | IMMEDIATE |
| 7 | Sprite Assembly Early Return | `TEMPORARY_EARLY_RETURN` | ACTIVE | VERIFY_FIRST |
| 8 | Sprite SAT DMA Suppression | `TEMPORARY_SUPPRESSION` | ACTIVE | VERIFY_FIRST |
| 9 | Bulk Preload Early Return | `TEMPORARY_EARLY_RETURN` | ACTIVE | VERIFY_FIRST |
| 4 | VDP Commit 3-Frame History | `INSTRUMENTATION` | ACTIVE | SOON |
| 5 | Commit Counter Increments | `INSTRUMENTATION` | ACTIVE | SOON |
| 10 | Test Palette at Handoff | `TEMPORARY_PALETTE_TEST` | ACTIVE | SOON |
| 11 | BSS Diagnostic Variable Block | `INSTRUMENTATION` | ACTIVE | LATER |

VERIFY_FIRST items (7, 8, 9): these suppress runtime paths that are still under investigation. They should not be reverted until the behavior they were isolating is either understood or no longer needed.

---

## 6. Single Most Important Next Non-Code Step

`BUILD_MASTER_DIAGNOSTIC_DEBT_DOCUMENT`

A single consolidated document listing all 11 active items with their cleanup priority, current status, and dependencies between items is needed before any further debugging. Items 1, 3, 7, and 8 are all HIGH-RISK contaminants that are simultaneously active and each masks different aspects of the arcade runtime. Their interaction makes current debug results ambiguous — for example, Items 7+8 suppress all sprite output, making it impossible to distinguish sprite-layer behavior from plane-layer behavior in screenshots.

---

## 7. Final Verdict

11 active temporary/diagnostic/suppression changes are present. 4 are HIGH-RISK (items 1, 3, 7, 8) and are simultaneously active, each masking a different layer of the rendering pipeline. Any screenshot taken with the current build reflects a significantly altered runtime:
- FG buffer cell (0,0) is always 0xFFFF (Item 1)
- FG buffer rows 1–5, cols 1–13 are always debug overlay text (Item 3)
- All sprites are suppressed (Items 7+8)
- Row 0–3 text is not filtered (Item 6)
- Tick-phase tile DMA never runs (Item 9)

No screenshot of the current ROM reflects the arcade ROM's intended rendering behavior. A cleanup pass removing or reverting non-essential items is required before further rendering analysis.
