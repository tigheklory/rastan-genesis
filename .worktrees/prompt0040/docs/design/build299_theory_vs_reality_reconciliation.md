# Build 299 — Theory vs Reality Reconciliation

## 1. Executive Summary

- **Prior conclusion was INCOMPLETE and INCORRECT.** The row/col inversion fix (Build 298) addressed ONE of at least FOUR active failures. The claim that "all remaining issues are visual-only due to BG row/col inversion" was wrong.
- **Text writer `text_writer_ptr_to_xy()` has the IDENTICAL row/col inversion bug** that was fixed in `pc080sn_dest_ptr_to_row_col()` — it was never touched by Build 298. ALL text via `0x3BB48` and `0x3C3FE` hooks renders at transposed X/Y positions, mostly off-screen. This ALSO corrupts the FG tilemap plane with misplaced tiles.
- **`load_arcade_palette()` is dead code — never called.** Tilemap tiles render with stale launcher palette, not arcade game palette. This is the primary cause of "purple-dominant" screen.
- **`sync_arcade_scroll_to_vdp()` is dead code — never called.** VDP scroll registers are never updated from arcade workram. Both planes are locked at scroll position (0,0).
- **`sanitize_arcade_workram()` is dead code — never called.** C-window address-range pointers (0xC0xxxx) remain in workram, risking bad descriptor reads.

---

## 2. Expected vs Actual — Per Attract Phase

### Title Screen (State 0, sub-state 0 inner 1)

| Element | Expected | Actual | Explanation |
|---------|----------|--------|-------------|
| Background art (mountains/sky) | BG plane shows scrolling landscape via PC080SN plane 0 | Solid purple/orange fill — no recognizable terrain | BG tiles placed at correct VDP cells (post Build 298 fix), but `load_arcade_palette()` never called → tiles render with launcher palette (PAL0–PAL3 contain font/UI colors, not arcade terrain colors). Additionally, `sync_arcade_scroll_to_vdp()` never called → BG viewport locked at (0,0) regardless of arcade scroll state. |
| "INSERT COIN(S)" text | Centered horizontal text on FG plane, readable | Partially visible, truncated characters | `text_writer_ptr_to_xy()` has row/col inversion: X derived from row-within-column, Y from column-index. Characters with C-window row < `col_bias` (32) compute negative X → off-screen. Only tail characters appear, at wrong Y. |
| "PUSH 1 OR 2 PLAYER BUTTON" | Horizontal text on FG plane below coin prompt | "TON" or similar fragment visible, mispositioned | Same text writer inversion. A string starting at C-window column ~36, row ~27 produces: X = (row − 32), Y = (col − 4). First ~5 characters have X < 0 (clipped). Remaining appear in a vertical column at wrong Y. |
| Credits display ("CREDIT 00") | Bottom of screen, FG text | Absent or single garbled character | Text writer inversion places it off-screen or at wrong position |
| RASTAN logo | Combination of tilemap tiles and/or sprites | Moving pixels / noise | If logo uses FG tilemap: correct tile placement but wrong palette + text writer corruption overwrites cells. If logo uses sprites: sprite rendering and palette ARE active (V-Int calls `refresh_frontend_sprite_palettes` + `genesistan_sprite_commit_asm`), so sprite elements may partially render but with imprecise palette mapping. |

### Story Screen (State 0, sub-state 1 inner 1)

| Element | Expected | Actual | Explanation |
|---------|----------|--------|-------------|
| Story text panel | Multi-line horizontal text describing Rastan's quest | Not visually distinct from title screen | Text writer inversion makes all story text render at wrong X/Y. Palette never loaded means background behind text is wrong color. |
| Background change | Different BG art or scroll position | No visible change | BG tiles may update correctly in VDP, but without palette sync the color difference is invisible. Without scroll sync the viewport doesn't shift. |

### High Score Screen / Demo Gameplay / Player-Select

All phases share the same compound failure: arcade logic advances state correctly (confirmed in Prompt 042), but visual output is broken by the same four failures. Screen transitions produce no distinguishable visual change because:
1. Text changes are invisible (text writer inversion)
2. Background tile changes are invisible (wrong palette)
3. Scroll changes are invisible (scroll never synced)
4. Only sprite rendering is partially functional (V-Int calls sprite pipeline)

---

## 3. Command-Level Rendering Analysis

### `0x3BB48` Text Writer Hook (`genesistan_hook_text_writer_3bb48_impl`)

**What it SHOULD render:** Named text strings (coin prompt, credits, story text, high scores) at predetermined FG C-window positions.

**Coordinate conversion in `text_writer_ptr_to_xy()` (main.c:1371–1424):**

```
cell = offset >> 2                     (C-window cell index)
row  = (cell >> 6) & 0x1F             ← actually column_index (WRONG LABEL)
col  = cell & 0x3F                    ← actually row_within_column (WRONG LABEL)
out_x = col - col_bias (32)           ← X = row_within_column - 32
out_y = row - VISIBLE_ROW_BIAS (4)    ← Y = column_index - 4
```

**For C-window column-major layout:** `cell = column × 64 + row`. Therefore `cell >> 6 = column`, `cell & 0x3F = row`. The function labels these backwards.

**Concrete trace — "INSERT COIN(S)" at column 36, row 27:**

| Character | Cell | cell>>6 (=col) | cell&0x3F (=row) | out_x (row−32) | out_y (col−4) | Visible? |
|-----------|------|-----------------|-------------------|-----------------|----------------|----------|
| I | 2331 | 36 | 27 | −5 | 32 | NO (x<0) |
| N | 2332 | 36 | 28 | −4 | 32 | NO |
| S | 2333 | 36 | 29 | −3 | 32 | NO |
| E | 2334 | 36 | 30 | −2 | 32 | NO |
| R | 2335 | 36 | 31 | −1 | 32 | NO |
| T | 2336 | 36 | 32 | 0 | 32 | BARELY (y=32 may be off-screen on 32-row VDP plane) |

Characters with row ≥ 32 get non-negative X but are placed at Y = column_index − 4, which is VERTICAL position derived from the HORIZONTAL origin. The string renders as a vertical column fragment, not horizontal text.

**Side effect:** Every `rastan_draw_tile_xy(tile, x, y)` call that passes bounds check (`0 ≤ x < 64, 0 ≤ y < 32`) writes a glyph tile to BG_A (FG VDP plane) at the WRONG cell. This overwrites correct FG tilemap data placed by `genesistan_asm_tilemap_commit_fg`.

### `0x3C3FE` Text Writer Hook (`genesistan_hook_text_writer_3c3fe`)

Same coordinate path through `text_writer_ptr_to_xy()`. Same inversion. Writes to BG_A with transposed coordinates. Same FG plane corruption.

### `0x3F084` — DMA/Hardware Setup

Called during `genesistan_startup_common_continue_normal` (startup_trampoline.s:450). This is a one-time init call, not a per-frame renderer. It sets up hardware registers. Not directly responsible for per-frame visual issues.

### Tilemap Strip Commits (BG + FG hooks)

After Build 298 fix, `pc080sn_dest_ptr_to_row_col()` correctly decodes:
- `out_row = cell & 0x3F` (row within column)
- `out_col = (cell >> 6) & 0x3F` (column index)

Assembly VDP formula `base + (row−4)×128 + col×2` produces correct VDP addresses. **Tile placement is correct. The tiles themselves render with wrong colors because `load_arcade_palette()` is never called.**

---

## 4. FG vs BG Visibility Analysis

### Element-to-Plane Assignment (Arcade)

| Element | Plane | Rendering Path |
|---------|-------|----------------|
| Background art (mountains, sky, castle) | BG (PC080SN plane 0) → Genesis BG_B (VRAM 0xC000) | Tilemap strip hook → `genesistan_asm_tilemap_commit_bg` |
| Foreground terrain overlay | FG (PC080SN plane 1) → Genesis BG_A (VRAM 0xE000) | Tilemap strip hook → `genesistan_asm_tilemap_commit_fg` |
| "INSERT COIN(S)" | FG (text on C-window page 2) → Genesis BG_A | Text writer hook → `text_writer_ptr_to_xy` → `rastan_draw_tile_xy` |
| "PUSH 1 OR 2 PLAYER BUTTON" | FG (text) → Genesis BG_A | Same text writer path |
| Credits display | FG (text) → Genesis BG_A | Same text writer path |
| RASTAN logo | Likely sprites + FG tiles | Sprites via V-Int; FG tiles via strip or text writer |

### What SHOULD Be Visible with FG Rendering Only (BG Broken)

If BG were completely broken but FG were correct:
- **Visible:** All text strings, foreground terrain, logo elements on FG plane
- **Missing:** Background mountains/sky/castle art
- **Screen appearance:** Black background (empty BG) with correctly placed, correctly colored FG elements and text

### What SHOULD Be Visible with BG Rendering Only (FG Broken)

If FG were completely broken but BG were correct:
- **Visible:** Background scenery tiles
- **Missing:** All text, foreground overlays
- **Screen appearance:** Background art visible but no readable text, no UI

### What SHOULD Be Visible if Only Palette is Wrong

If tile placement were correct on both planes but palette were wrong:
- **Visible:** All elements present at correct positions, but with garbled/wrong colors
- **Screen appearance:** Recognizable shapes (mountains, text letterforms) but in wrong color scheme

### Current Screen Matches NONE of These Clean Failure Modes

The current screen shows:
- Solid color fills (not recognizable terrain) → wrong palette + possibly wrong scroll viewport
- Truncated/mispositioned text fragments → text writer inversion
- Logo as noise → FG plane corruption from misplaced text tiles + wrong palette
- No visual state transitions → all three failures compound to make changes invisible

**This is a COMPOUND FAILURE across at least three independent systems.**

---

## 5. Failure Classification Matrix

| # | Failure Class | Location | Affected Elements | Status | Severity |
|---|--------------|----------|-------------------|--------|----------|
| 1 | **MAPPING ERROR** — Text writer row/col inversion | `text_writer_ptr_to_xy()` main.c:1408–1422 | ALL text (coin prompt, credits, story, scores) + FG plane corruption | ACTIVE — not fixed in Build 298 | CRITICAL |
| 2 | **INITIALIZATION ERROR** — Arcade palette never loaded | `load_arcade_palette()` main.c:610 — defined but never called | ALL tilemap tiles (BG + FG) render with wrong colors | ACTIVE — dead code | CRITICAL |
| 3 | **SCROLL ERROR** — VDP scroll never synced from arcade workram | `sync_arcade_scroll_to_vdp()` main.c:1949 — defined but never called | Both BG and FG viewport locked at (0,0) | ACTIVE — dead code | HIGH |
| 4 | **DATA ERROR** — Workram sanitization never runs | `sanitize_arcade_workram()` main.c:1917 — defined but never called | Descriptor pointers may contain invalid C-window addresses (0xC0xxxx) | ACTIVE — dead code, stability risk | MEDIUM |
| 5 | **MAPPING ERROR** — BG row/col inversion | `pc080sn_dest_ptr_to_row_col()` main.c:1282–1283 | BG + FG tilemap strips | FIXED in Build 298 | — |

### V-Int Handler Gap Analysis

The V-Int handler (`genesistan_frontend_live_vint_handoff`, main.c:1954–1969) calls:

```
genesistan_refresh_arcade_inputs();          ✓ Input handling
genesistan_run_original_frontend_tick();     ✓ Arcade logic + hook-invoked tilemap commits
genesistan_sprite_tile_prepare();            ✓ Sprite tile DMA
refresh_frontend_sprite_palettes();          ✓ Sprite palette update
genesistan_sprite_commit_asm();              ✓ Sprite SAT commit
```

**MISSING from V-Int handler:**

```
load_arcade_palette();                       ✗ NEVER CALLED — tilemap colors wrong
sync_arcade_scroll_to_vdp();                 ✗ NEVER CALLED — viewport frozen
sanitize_arcade_workram();                   ✗ NEVER CALLED — stale C-window pointers
```

---

## 6. Root Cause Reassessment — FINAL VERDICT

### Is "row/col inversion" STILL the primary root cause?

**NO.** It is ONE of FOUR active failures. The Build 298 fix corrected inversion for tilemap strip rendering only. Two critical instances of the same conceptual bug remain unfixed, plus two entirely separate failure classes.

### Classification of row/col inversion (Build 298 fix):

**PARTIAL CAUSE.** The fix was necessary and correct for tilemap strip VDP mapping. But it addressed only `pc080sn_dest_ptr_to_row_col()`. The identical inversion in `text_writer_ptr_to_xy()` was not identified or fixed.

### Complete root cause ranking:

| Priority | Root Cause | Impact |
|----------|-----------|--------|
| 1 | **Palette never loaded** (dead code `load_arcade_palette`) | All tiles show with wrong colors → screen appears as solid color blocks instead of recognizable art. This is the single largest contributor to "purple-dominant" screen. |
| 2 | **Text writer row/col inversion** (`text_writer_ptr_to_xy`) | All text invisible or truncated + active FG plane corruption. This explains "TON" fragment, missing coin feedback, and indistinguishable attract phases. |
| 3 | **Scroll never synced** (dead code `sync_arcade_scroll_to_vdp`) | Viewport locked at (0,0) → BG art may be correct in VRAM but the visible window doesn't track the arcade's camera. Attract screen transitions that rely on scroll changes produce no visible difference. |
| 4 | **Workram sanitization missing** (dead code `sanitize_arcade_workram`) | C-window pointers (0xC0xxxx) persist in workram descriptor lists → assembly code may read descriptor addresses that point into Genesis SRAM range instead of ROM, producing garbage tile data or crashes. |

### Prior analysis failure:

My previous audits (Prompts 036, 038, 039, 042) focused exclusively on the tilemap commit pipeline: dest_ptr decoding, VDP address formula, C-window bounds. I traced the MAPPING path thoroughly but **never audited the DISPLAY path** — whether palette, scroll, and text rendering were actually being called in the live V-Int loop. I also failed to check `text_writer_ptr_to_xy()` for the same inversion pattern I had identified in `pc080sn_dest_ptr_to_row_col()`.

**The conclusion that "all remaining issues are visual-only due to BG row/col inversion" was WRONG.** The correct conclusion is: **four independent failures across mapping, palette, scroll, and data integrity systems compound to produce a screen that bears no visual resemblance to the arcade attract mode.**

---

## 7. Proof — If BG Were the ONLY Broken System, Would the Screen Look Like This?

**NO.**

If BG (background plane) were the only broken system:
- FG text would be correctly positioned and readable (text writer is on FG)
- FG tilemap tiles would be correctly placed with correct palette
- Sprites would render correctly (sprite pipeline is functional)
- Screen would show: black/empty background + correct foreground text + correct sprites
- State transitions would be visually distinguishable (text changes between phases)

The actual screen shows:
- No readable text → text writer bug (FG system failure, not BG)
- Wrong colors everywhere → palette never loaded (system-wide failure, not BG-specific)
- No scroll tracking → scroll never synced (system-wide failure, not BG-specific)
- No recognizable shapes → compound of all four failures

**A BG-only failure cannot produce the observed symptoms. QED.**
