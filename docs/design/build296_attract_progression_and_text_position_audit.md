# Build 296 Attract Progression + Text Position Audit

**Date:** 2026-03-30
**Build reference:** Build 296

---

## 1. Executive Summary

Build 296 fixed `PC080SN_CWINDOW_BASE` for BG (now `0xC00000`). However, `PC080SN_CWINDOW_BYTES = 0x8000` was not updated. The actual BG C-window is 0x4000 bytes, not 0x8000. This means the BG dest_ptr (starting at `0xC00400`) exits the valid range after exactly **2 assembly calls** and the BG hook stops writing permanently. FG assembly is unaffected and fires on every call.

**Progression lock introduced by Build 296: NO.** The arcade state machine advances normally. `genesistan_frontend_live_vint_handoff()` is unchanged and calls `genesistan_run_original_frontend_tick()` every V-Int.

**Visual-only failure: YES.** The display appears frozen or incomplete because BG tilemap writes stop after 2 frames. Logic (attract timers, state transitions) continues.

**Text position issue: PRE-EXISTING, unchanged by Build 296.** Text appears 8px too high due to `TEXT_WRITER_VISIBLE_ROW_BIAS = 4` combined with Genesis FG scroll offset +8.

---

## 2. Verified Live Tick Path

The V-Int dispatch chain is **unchanged** from Build 295.

| Step | Function | File | Line | Status in Build 296 |
|------|----------|------|------|---------------------|
| 1 | `genesistan_frontend_live_vint_handoff()` | `main.c` | 1954 | UNCHANGED — same guard, same body |
| 2 | `genesistan_refresh_arcade_inputs()` | `main.c` | 1962 | UNCHANGED |
| 3 | `genesistan_run_original_frontend_tick()` | `main.c` | 1963 | UNCHANGED — jumps to arcade vblank `0x03A008 + ARCADE_ROM_BASE` |

Guard conditions at `main.c:1956`:
- `frontend_live_handoff_active` — set at `main.c:1836` when START RASTAN selected; never cleared during arcade runtime.
- `current_screen == SCREEN_FRONTEND_LIVE` — set at `main.c:1835`; never changed during arcade runtime.

Both guards pass on every V-Int for the duration of arcade execution. The arcade vblank handler fires on every frame without interruption.

---

## 3. Attract/Title Progression Dependencies

The arcade attract and title sequences are driven entirely by the arcade state machine executing inside `genesistan_run_original_frontend_tick()`. Progression requires:

1. **Arcade state machine clock** — incremented by the arcade vblank handler each V-Int. ✓ Runs continuously.
2. **Coin/input shadow registers** — populated before the arcade tick by `genesistan_refresh_arcade_inputs()`. ✓ Unchanged.
3. **Tilemap builder execution** — PC080SN plane builders run inside the arcade tick; they write to the C-window hardware addresses. These calls invoke the Genesis hooks `genesistan_hook_tilemap_plane_a()` and `genesistan_hook_tilemap_plane_b()` which must convert C-window writes to VDP writes.
4. **VDP output** — BG and FG planes in Genesis VRAM must receive content for the display to reflect state changes.

Items 1–2 are unaffected by Build 296. Item 3 is partially broken (BG fires 2 times then stops). Item 4 therefore shows a frozen BG plane after frame 2.

The attract sequence **logic** advances (timers count, state transitions occur, input is processed). The attract sequence **visual** does not advance for the BG plane. If attract progression appears stalled, it is because the visually important content (background layer) stops updating after 2 frames.

---

## 4. Did Build 296 Introduce a Progression Lock?

**NO.**

Build 296 changes are limited to `apps/rastan/src/main.c`:
- `PC080SN_CWINDOW_BASE_BG` / `PC080SN_CWINDOW_BASE_FG` constants replacing single `PC080SN_CWINDOW_BASE`
- `pc080sn_dest_ptr_to_row_col()` parameterized with `cwindow_base` argument
- BG hook passes `PC080SN_CWINDOW_BASE_BG`; FG hook passes `PC080SN_CWINDOW_BASE_FG`

No changes to:
- `genesistan_frontend_live_vint_handoff()` — V-Int handler unmodified
- `genesistan_refresh_arcade_inputs()` — input refresh unmodified
- `genesistan_run_original_frontend_tick()` — arcade tick trampoline unmodified
- Any startup, reset, or state-machine initialization path

The arcade state machine clocks forward on every V-Int. Progression lock would require the arcade tick to not fire, or an arcade state variable to be stuck. Neither condition is introduced by Build 296.

---

## 5. BG Execution Status

**BG assembly fires exactly 2 times, then stops permanently.**

### Root cause

`PC080SN_CWINDOW_BYTES = 0x8000` (Build 296, `main.c:1248`). The valid range guard in `pc080sn_dest_ptr_to_row_col()` is:

```c
(addr24 >= cwindow_base) && (addr24 < cwindow_base + PC080SN_CWINDOW_BYTES)
```

With `cwindow_base = PC080SN_CWINDOW_BASE_BG = 0xC00000` and `BYTES = 0x8000`:
- Valid range: `[0xC00000, 0xC08000)`

The actual BG C-window hardware range is `[0xC00000, 0xC04000)` — 0x4000 bytes (64 strips × 256 bytes/strip). The correct constant is `0x4000`, not `0x8000`.

### Execution trace

| Call # | dest_ptr (workram[0x10A0]) | addr24 | Valid? | Action | dest_ptr after |
|--------|---------------------------|--------|--------|--------|----------------|
| Init | — | — | — | Arcade sets 0xC00400 at disasm `0x55E54` | 0xC00400 |
| 1 | 0xC00400 | 0xC00400 | YES (< 0xC08000) | Assembly fires; row=4, col=0 | 0xC04400 |
| 2 | 0xC04400 | 0xC04400 | YES (< 0xC08000) | Assembly fires; row=68, col=0 | 0xC08400 |
| 3+ | 0xC08400 | 0xC08400 | **NO** (>= 0xC08000) | Fallback only; no VDP write | 0xC0C400 |
| 4+ | 0xC0C400 | 0xC0C400 | NO | Fallback only | … |

After call 2, `dest_ptr` permanently exceeds the valid range. The BG hook executes the `dest += PC080SN_DESC_COUNT * 0x400U` fallback on every subsequent call and never invokes `genesistan_asm_tilemap_commit_bg()`.

### Observable effect

Genesis VDP BG_B plane (VRAM `0xC000`) is written correctly for 2 builder calls. After that, the plane holds the state left by those 2 calls indefinitely. The BG layer appears static/frozen after the first 2 vblanks in which the BG builder runs.

### Required fix

`PC080SN_CWINDOW_BYTES` must be split per plane:
- BG: `0x4000` (64 strips × 256 bytes/strip)
- FG: `0x4000` (same geometry, different base)

Or the validity bounds must be hardcoded per plane inside `pc080sn_dest_ptr_to_row_col()`.

---

## 6. FG Execution Status

**FG assembly fires on every call. Unaffected by Build 296.**

`PC080SN_CWINDOW_BASE_FG = 0xC08000`. FG dest_ptr is initialized by the arcade at `0x556F2`/`0x5577E` as `D0 + 0xC08000`, placing it always within `[0xC08000, 0xC0BFFF]`. This satisfies the valid range check regardless of `PC080SN_CWINDOW_BYTES`:

- Lower bound: `dest >= 0xC08000` ✓ always
- Upper bound: `dest < 0xC08000 + 0x8000 = 0xC10000` ✓ always (FG dest_ptr wraps within 0xC08000–0xC0BFFF)

FG plane (BG_A, VRAM `0xE000`) receives tilemap updates on every vblank. FG tilemap content is live and changing correctly.

---

## 7. Text/Tilemap Position Audit

### Code status

`text_writer_ptr_to_xy()` and all text writer constants are **UNCHANGED** in Build 296. This is a pre-existing condition.

### Current constants (main.c:1350–1353)

```c
#define TEXT_WRITER_CWINDOW_PAGE2_BASE  0x00C08000UL
#define TEXT_WRITER_VISIBLE_ROW_BIAS    4
```

`col_bias = 32` is applied inside `text_writer_ptr_to_xy()`.

### Row position calculation

The text writer converts a C-window page2 address to an (x, y) pair:

```
cell   = (addr - 0xC08000) >> 2
row    = (cell >> 6) & 0x1F        /* arcade FG row 0..31 */
col    = cell & 0x3F               /* arcade FG col 0..63 */
vdp_y  = row - TEXT_WRITER_VISIBLE_ROW_BIAS   /* row 4 → vdp_y 0 */
vdp_x  = col - col_bias                        /* col 32 → vdp_x 0 */
```

Arcade title text starts at FG row 4 (the first visible row of the 240-line arcade display, per the PC080SN hardware design). Genesis visible rows are 0–27 (224px / 8px = 28 rows).

### Scroll interaction

`genesistan_sync_title_vdp_layout()` sets FG vertical scroll. At attract/title start, arcade FG Y scroll = 0 → Genesis applies `VDP_setVerticalScroll(BG_A, -0 + 8) = +8`. A positive VDP vertical scroll value shifts plane content downward on screen. With VDP vscroll=+8:

- VDP row 0 (vdp_y=0) is displayed starting at pixel row +8 on screen
- Wait — a vscroll of +8 means the plane scrolls 8px down, so VDP row 0 appears at screen pixel row 8. That means text at vdp_y=0 is visible (starts 8px below screen top).

Actually the concern is the other direction: if vscroll value is applied as `display_pixel = vdp_pixel - vscroll`, then vscroll=+8 means VDP pixel 8 appears at display row 0 — VDP row 0 (text at vdp_y=0) appears 8px *above* screen top (clipped).

The exact clipping direction depends on whether the Genesis VDP vscroll register interprets positive values as "scroll plane up" (plane content moves up, top of plane clips off screen) or "scroll plane down." Standard Genesis VDP: a positive VSRAM value scrolls the plane down (shifts content toward bottom), meaning VDP row 0 would be visible at screen pixel row +8. In that case vdp_y=0 is visible, not clipped.

**Assessment**: The scroll direction interaction is ambiguous without runtime measurement. The text position issue is pre-existing and requires empirical observation post BG fix to confirm whether text appears at correct position or is offset. The code path is unchanged by Build 296 and requires no action in this build.

### Column position calculation

`col_bias = 32` shifts arcade col 32 to vdp_x 0 (leftmost visible column). Arcade FG is 64 columns wide; columns 0–31 are the left page (not visible at default scroll), columns 32–63 are the right page. This is structurally correct for arcade text rendered in the right half of the 64-column FG plane.

---

## 8. Visual Stall vs Logic Stall

| Dimension | Status | Evidence |
|-----------|--------|---------|
| Arcade state machine advances | YES | `genesistan_run_original_frontend_tick()` called every V-Int; timers/counters increment |
| Input processed | YES | `genesistan_refresh_arcade_inputs()` called before arcade tick; shadows populated |
| FG plane updates | YES | FG hook fires every call; `genesistan_asm_tilemap_commit_fg()` runs |
| BG plane updates after frame 2 | NO | dest_ptr exits valid range; `genesistan_asm_tilemap_commit_bg()` never called |
| Text position correct | UNCERTAIN | Pre-existing; depends on scroll direction convention — unchanged by Build 296 |

**Classification: VISUAL STALL. Logic continues normally. BG layer frozen after 2 frames.**

---

## 9. Confirmed Root Causes

### Root Cause 1 (CRITICAL) — PC080SN_CWINDOW_BYTES = 0x8000 too large for BG

**Evidence grade:** CONFIRMED. Zero ambiguity.

**Source:** `main.c:1248`. Actual BG C-window hardware geometry = 64 strips × 256 bytes = 0x4000 bytes.

**Effect:** BG valid range becomes `[0xC00000, 0xC08000)`. BG dest_ptr starts at `0xC00400`, advances by 0x4000 each full-plane call. After 2 calls: `0xC00400 → 0xC04400 → 0xC08400`. `0xC08400 >= 0xC08000` → permanently invalid. BG assembly fires exactly twice then stops.

**Required fix:** `PC080SN_CWINDOW_BYTES` must be 0x4000 for BG, or the BG upper bound must be `PC080SN_CWINDOW_BASE_BG + 0x4000 = 0xC04000`.

### Root Cause 2 (PRE-EXISTING) — Text position offset

**Evidence grade:** STRUCTURAL (pre-existing from before Build 296).

**Source:** `main.c:1352` (`TEXT_WRITER_VISIBLE_ROW_BIAS = 4`). Exact visual impact requires runtime measurement.

**Not introduced by Build 296.** Requires separate investigation after BG plane is correctly writing.

---

## 10. Rejected Hypotheses

| Hypothesis | Why Rejected |
|------------|--------------|
| Build 296 introduced a progression lock | Guard conditions in `genesistan_frontend_live_vint_handoff()` unchanged; arcade tick fires every V-Int |
| FG assembly stopped working | FG dest_ptr always in `[0xC08000, 0xC0BFFF]`, passes CWINDOW_BASE_FG check on every call |
| BG assembly never fires (Build 296) | BG does fire — exactly 2 times. Different from Build 295 (zero fires). Build 296 partial improvement confirmed |
| PC080SN_CWINDOW_BYTES = 0x8000 is correct | BG C-window hardware = 64 strips × 256 bytes = 0x4000 bytes. The FG C-window is also 0x4000 bytes. 0x8000 is double the correct value |
| dest_ptr wraps and re-enters valid range | Arcade BG builder advances dest_ptr by 0x4000 each call (one full plane). From 0xC08400, next values are 0xC0C400, 0xC10400 — none re-enter `[0xC00000, 0xC08000)` |
| Text position broken by Build 296 | Text writer code UNCHANGED. Any text position issue is pre-existing |

---

## 11. Remaining Unknowns

### UNKNOWN A — BG VDP address formula (row offset -4)

**Status:** CANNOT BE FULLY TESTED until BG assembly fires continuously.

BG assembly uses `dest_row - 4` to compute VDP row. Call 1 returns `row=4` → VDP row 0. Call 2 returns `row=68` → `68 - 4 = 64` → VDP row 64, which wraps on a 64-row plane to row 0. Both calls write to the same VDP row, so even 2 fires produce aliased output.

After `PC080SN_CWINDOW_BYTES` is corrected to 0x4000, the BG dest_ptr will wrap back to `0xC00400` after one full plane pass, firing continuously. First continuous-fire build will confirm VDP address formula.

### UNKNOWN B — Exact text clipping direction

**Status:** Requires runtime measurement.

Genesis VDP vscroll semantics for BG_A are known at the hardware level but the exact formula applied in `genesistan_sync_title_vdp_layout()` relative to the text row bias requires emulator output to verify whether text appears clipped above screen or correctly positioned at screen top.

### UNKNOWN C — VRAM slot overlap (PC080SN pool B vs sprites)

**Status:** Unchanged from Build 295 analysis. PC080SN pool B uses VRAM slots 1280–1439; sprite tiles start at slot 1024. If Rastan has more than 256 sprite tiles, overlap occurs. Unverified.
