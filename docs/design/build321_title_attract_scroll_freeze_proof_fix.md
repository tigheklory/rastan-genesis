# Build 321 — Temporary Title/Attract Scroll Freeze Proof Fix

## 1. Executive Summary

Build 321 adds a temporary mode gate to `genesistan_scroll_commit_vdp()` that forces all scroll values (HScroll and VScroll for both planes) to zero during title/attract phase. This prevents the attract-mode arcade tick from shifting sparse text content around the screen, making the remaining display composition problem stationary and inspectable. Gameplay scroll behavior is preserved unchanged.

## 2. Prior Confirmed Scroll-Instability Finding

Per `docs/design/build320_vertical_text_and_screen_instability_audit.md`:

- Root cause: ACTIVE_SCROLL_MOVING_VALID_TEXT
- The attract-mode arcade tick updates scroll workram values (offsets 0x10AE, 0x10B0, 0x10EC, 0x10EE) every frame
- `genesistan_scroll_commit_vdp()` unconditionally wrote these changing values to VDP HScroll (VRAM 0xF000) and VSRAM
- Sparse text tiles in the FG nametable were scrolled around the screen, producing rapid vertical/horizontal motion
- The screen was mostly black because nametable buffers were ~98% zeros (tilemap hooks produce no content during title/attract)

## 3. Exact Code Change

**File**: `apps/rastan/src/main.c`, function `genesistan_scroll_commit_vdp()`, lines 1756-1785

**Before**: Staged scroll values written directly to VDP unconditionally.

**After**: Added mode gate that reads `genesistan_arcade_workram_words[2]` (inner step, A5 offset 4). When inner step < 2 (title/attract), all four scroll writes are forced to zero. When inner step >= 2 (gameplay), original staged values are written unchanged.

```c
const u16 inner_step = genesistan_arcade_workram_words[2];
const u16 title_attract = (inner_step < 2U) ? 1U : 0U;

/* HScroll writes */
*data = title_attract ? 0 : (u16)staged_scroll_x_fg;
*data = title_attract ? 0 : (u16)staged_scroll_x_bg;

/* VScroll writes */
*data = title_attract ? 0 : (u16)staged_scroll_y_fg;
*data = title_attract ? 0 : (u16)staged_scroll_y_bg;
```

No other code changed. Scroll staging (`genesistan_scroll_from_workram_vdp`) and all hook replacements are untouched.

## 4. Title/Attract Mode Gate Source and Condition

| Item | Value |
|------|-------|
| Source variable | `genesistan_arcade_workram_words[2]` |
| Arcade meaning | Inner step (A5 byte offset 4) |
| Title/attract condition | `inner_step < 2` |
| Gameplay condition | `inner_step >= 2` |

This is the same mode gate variable used by Build 314's PC080SN commit gate (`cmpi.w #2, 4(%a0)` in startup_trampoline.s). Values < 2 indicate the arcade state machine has not yet reached active gameplay.

## 5. Scroll Freeze Behavior

During title/attract (inner_step < 2):

| VDP Target | Value Written |
|-----------|---------------|
| VRAM 0xF000 word 0 (FG HScroll) | 0 |
| VRAM 0xF000 word 1 (BG HScroll) | 0 |
| VSRAM offset 0 (FG VScroll) | 0 |
| VSRAM offset 2 (BG VScroll) | 0 |

Both planes have zero horizontal and vertical scroll. Any nametable content is displayed at its natural nametable position without offset.

## 6. Preserved Non-Title Behavior

During gameplay (inner_step >= 2):

| VDP Target | Value Written |
|-----------|---------------|
| VRAM 0xF000 word 0 (FG HScroll) | `staged_scroll_x_fg` (from workram 0x10AE) |
| VRAM 0xF000 word 1 (BG HScroll) | `staged_scroll_x_bg` (from workram 0x10EC) |
| VSRAM offset 0 (FG VScroll) | `staged_scroll_y_fg` (from workram 0x10B0) |
| VSRAM offset 2 (BG VScroll) | `staged_scroll_y_bg` (from workram 0x10EE) |

Identical to Build 320 gameplay behavior. No change to scroll staging, conversion, or hook replacements.

## 7. Build 321 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_321.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same pre-existing warnings as prior builds)

### Scroll-freeze behavior
- Mode gate source: `genesistan_arcade_workram_words[2]` (inner step)
- Title/attract freeze condition: `inner_step < 2`
- Zero scroll forced during title/attract: **YES**
- Normal non-title scroll path preserved: **YES**

## 8. Visual Verification Status

**USER MUST VERIFY.** Expected behavior:
- Sparse text dots should now be stationary (no scrolling motion)
- Screen still mostly black (nametable content issue unchanged)
- Text content should appear at its natural nametable row/column position

## 9. Crash Verification Status

**USER MUST VERIFY.** The scroll freeze adds a read of workram_words[2] and conditional zeroing of scroll values. No new VDP register changes, no new memory access patterns.

## 10. Final Verdict

Temporary proof fix. Scroll is frozen at zero during title/attract phase. If the visible dots become stationary, this confirms active scroll was causing the visual instability. The remaining "screen mostly black" problem is a nametable population issue (tilemap hooks produce no content during title/attract), not a scroll or palette problem.
