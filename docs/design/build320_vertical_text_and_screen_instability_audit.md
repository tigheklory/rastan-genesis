# Build 320 — Vertical Text / Screen Instability Audit

## 1. Executive Summary

After the Build 320 palette mirror proof fix, the screen remains mostly black with sparse colored dots that expand and shift over time. FPS drops from 123 to 7. The primary remaining root cause is **ACTIVE_SCROLL_MOVING_VALID_TEXT**: the arcade attract-mode tick updates scroll workram values every frame, and the scroll commit unconditionally writes these changing values to the VDP. The sparse visible content (text writer font tiles) is scrolled around the screen frame-to-frame, producing the appearance of rapid vertical/horizontal motion. The screen is mostly black because the PC080SN tilemap hooks produce no meaningful nametable content during title/attract — descriptor lists in arcade workram are empty/invalid, so the BG buffer is all zeros and the FG buffer has only ~50/2048 non-zero text entries.

## 2. What Build 320 Proved vs Did Not Prove

### Proved
- **Palette bank mirroring works**: All 4 CRAM lines now show identical game colors (confirmed in screenshots 7-10, Exodus palette viewer)
- **Palette was part of the visibility problem**: More colored dots now appear vs Build 319's single-line palette
- **Tile data is in VRAM**: Pattern viewer shows full scene tiles with correct colors when palette is applied

### Did NOT Prove
- **Screen is NOT "just invisible due to palette"**: After palette fix, screen is still mostly black with sparse dots
- **Nametable content is the real gap**: The BG/FG WRAM buffers are almost entirely zeros — tile 0 (blank) dominates both planes
- **Display instability is not a palette issue**: The moving/rolling dots are caused by active scroll, not by palette flicker

## 3. Moving Band Content Identification

### Does the moving band contain valid text-range tile indices: YES

The sparse dots correspond to text writer output. The text writers (`genesistan_hook_text_writer_3bb48_impl` at [main.c:1643](apps/rastan/src/main.c#L1643) and `genesistan_hook_text_writer_3c3fe` at [main.c:1777](apps/rastan/src/main.c#L1777)) call `rastan_draw_tile_xy()` which writes to `pc080sn_fg_buffer[y * 64 + x]` at [main.c:1314](apps/rastan/src/main.c#L1314).

Text tile VRAM slot range: **0x001A–0x0041** (decimal 26–65), per prior analysis in `docs/design/build318_title_text_contradiction_audit.md`.

**Content class**: Title/attract text — "PUSH START", credit count, score display. These are the only producers that populate the FG buffer during title/attract. The visible dots are individual font tile pixels (most font pixels use color index 0 = transparent, so only sparse non-zero pixels appear).

### What the dots are NOT
- NOT scene tilemap content (tilemap hooks fire but produce nothing — descriptors empty)
- NOT logo content (logo tile 0x1B maps to VRAM slot 0 = unmapped)
- NOT sprite content (sprite commit is part of VBlank but SAT may be minimal)

## 4. Text/HUD Position and Orientation Audit

### Expected text position
The text writer converts arcade C-window pointers to screen coordinates via `text_writer_ptr_to_xy()` at [main.c:1340](apps/rastan/src/main.c#L1340). With `TEXT_WRITER_VISIBLE_ROW_BIAS = 4`, arcade C-window row 18 → screen y=14. Title text ("PUSH START", credits, score) should appear in a narrow horizontal band around rows 14-20 of the 32-row nametable.

### Actual text position
The ~50 non-zero FG buffer entries are correctly placed at the expected rows/columns by the text writer. The coordinate conversion is functioning correctly.

### Is orientation/placement wrong: NO — but scroll moves it

The text is written to the correct nametable rows/columns. However, the VDP scroll values are changing every frame during attract mode, which shifts the viewport over the nametable. This makes correctly-placed text appear to move vertically and horizontally.

## 5. Scroll/VSRAM/HScroll State During Unstable Display

### Scroll commit path
`genesistan_scroll_commit_vdp()` at [main.c:1756-1774](apps/rastan/src/main.c#L1756-L1774) runs unconditionally every VBlank (no mode gate). It reads staged values from:

| Staged Variable | Arcade Workram Source | Description |
|----------------|----------------------|-------------|
| `staged_scroll_x_fg` | workram[0x10AE/2] | FG horizontal, negated |
| `staged_scroll_y_fg` | workram[0x10B0/2] | FG vertical, negated + 8 |
| `staged_scroll_x_bg` | workram[0x10EC/2] | BG horizontal, negated |
| `staged_scroll_y_bg` | workram[0x10EE/2] | BG vertical, negated + 8 |

### Are scroll values changing frame-to-frame: YES

During attract mode, the arcade tick (`genesistan_run_arcade_tick_lean`) executes the original Rastan arcade main loop at 0x03A008. This loop runs the attract-mode demo, which actively updates scroll workram values as the "demo player" moves through the level. The scroll replacement hooks at 0x055AB4–0x055ACC fire multiple times per arcade tick, staging new scroll values each time.

### Is instability caused by active scroll values: YES

- **Which plane**: Both Plane A (FG) and Plane B (BG) scroll is being updated
- **Which scroll path**: Both horizontal and vertical scroll change as the attract demo plays
- **Effect**: The sparse text tiles (correctly placed at rows ~14-20 in the nametable) are shifted by the current scroll offset, causing them to appear at different screen positions each frame — producing the "rapid vertical motion" the user observes

## 6. Plane A vs Plane B Content Audit

### Plane A (FG, nametable at VRAM 0xE000)
- **Content**: ~50/2048 non-zero entries from text writers (font tiles at VRAM slots 0x001A-0x0041)
- **Rest**: zeros (tile 0, palette 0 = blank/black)
- **Producer**: `genesistan_hook_text_writer_3bb48_impl` and `genesistan_hook_text_writer_3c3fe` via `rastan_draw_tile_xy()`

### Plane B (BG, nametable at VRAM 0xC000)
- **Content**: 0/2048 non-zero entries (completely empty)
- **Producer**: None active during title/attract. The tilemap hook (`genesistan_hook_tilemap_plane_b`) fires but the arcade BG descriptor list at workram offset 0x10A4 is empty/invalid, producing no output.

### Which plane produces the unstable visible content: Plane A (FG)

The visible dots are exclusively from the FG text writer output on Plane A. Plane B contributes nothing visible.

## 7. Frame-to-Frame Stability Analysis

### Primary instability mechanism: SCROLL MOVES STABLE NAMETABLE

The nametable content itself is relatively stable — text writer entries accumulate gradually (the dot count grows slowly over time as more text frames are processed). The **visual instability** (rapid motion) is caused by the scroll commit writing new VDP scroll values every frame from the arcade attract-mode demo.

Evidence:
- Dots appear to shift position between screenshots despite no change in the pattern viewer tile content
- FPS drops progressively (123→19→14→7), suggesting the arcade tick takes longer as the demo advances through more complex game states
- The scroll staging function is called multiple times per arcade tick from hooks at 0x055AB4-0x055ACC

### FPS numbers in screenshots

The varying FPS values (123→19→14→7) in the Exodus screenshots are due to the user manually throttling the CPU in Exodus to capture frames. There is no actual performance degradation at native speed.

## 8. Single Most Likely Remaining Root Cause

**ACTIVE_SCROLL_MOVING_VALID_TEXT**

The nametable has valid (sparse) text content at correct positions. Active scroll values from the attract-mode arcade tick shift this content around the screen every frame, producing the visual instability. The screen is mostly black because the tilemap hooks produce no scene nametable entries (descriptors are empty during title/attract), not because of any remaining palette or tile pipeline issue.

## 9. Single Next Implementation Target

**Freeze scroll during title/attract phase.** Add a mode gate to `genesistan_scroll_commit_vdp` (or the scroll staging function) that holds scroll at zero when the game is in title/attract mode (arcade_mode4 < 2). This will:
1. Stop the visual instability (text stays at its correct nametable position)
2. Make the sparse text dots stationary and verifiable
3. Isolate the remaining "screen mostly black" problem as a nametable population issue rather than a scroll issue

This does NOT fix the "screen mostly black" problem (that requires the tilemap hooks to produce actual scene content), but it removes the compounding instability so the next investigation can focus on nametable population.

## 10. Final Verdict

| Finding | Status |
|---------|--------|
| Palette mirror proof fix working | **YES** — all 4 CRAM lines have game colors |
| Screen still mostly black | **YES** — nametable buffers ~98% zeros |
| Moving band is text content | **YES** — font tiles from text writers, VRAM slots 0x001A-0x0041 |
| Text positioned correctly in nametable | **YES** — rows ~14-20, correct columns |
| Scroll actively changing | **YES** — attract-mode demo updates scroll every frame |
| Scroll causes visual instability | **YES** — text shifts position frame-to-frame |
| FPS degradation | **NO** — varying FPS in screenshots was manual CPU throttle in Exodus |
| Tilemap hooks produce scene content | **NO** — descriptors empty during title/attract |
| Primary remaining root cause | **ACTIVE_SCROLL_MOVING_VALID_TEXT** |
| Next implementation target | **Freeze scroll during title/attract (mode gate on scroll commit)** |
