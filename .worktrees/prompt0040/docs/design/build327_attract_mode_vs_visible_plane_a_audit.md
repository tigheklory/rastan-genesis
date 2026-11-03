# Build 327 — Attract Mode vs. Visible Plane A Audit

## 1. Executive Summary

Build 326 confirmed that `pc080sn_fg_buffer[0]` = 0xFFFF both before and after the arcade tick (`B:FFFF A:FFFF`), proving the FG buffer is intact and correctly committed to VRAM 0xE000 (Plane A). Yet the `B:FFFF A:XXXX` debug text is visible in the Plane Viewer but **not on the actual screen**. The screen still shows rolling dots.

Root cause: **WINDOW_PLANE_FULL_SCREEN_COVERAGE**

`force_clean_vram_init()` (main.c:2130–2131) writes VDP registers 17 and 18 with value `0x00` each. In Genesis VDP, reg17=0x00 means Window right-of column 0 (full-screen width) and reg18=0x00 means Window below row 0 (full-screen height). The Window plane covers the entire display, hiding Plane A (FG) and Plane B (BG) entirely. The Window VRAM at 0xD000 is zero-filled by `force_clean_vram_init()` and is **never written** by `genesistan_pc080sn_commit_planes` (which only writes 0xC000 and 0xE000). The visible rolling dots are the sprite layer, which renders on top of all planes including the Window.

## 2. Evidence Chain

### 2.1 Build 326 Confirmed Buffer Survival

`B:FFFF A:FFFF` in Plane Viewer Layer A (VRAM 0xE000) proves:
- FG buffer is written correctly (sentinel + debug text reach WRAM buffer)
- `genesistan_pc080sn_commit_planes` executes and commits the buffer to VRAM
- The arcade tick does NOT zero the FG buffer

The FG pipeline is correct and functional. The problem is not in the write path.

### 2.2 Why Plane A Is Invisible — Window Register Analysis

**`force_clean_vram_init()` sets (main.c:2130–2131):**

```c
*ctrl = 0x9100; /* reg 17: window H pos = 0 */
*ctrl = 0x9200; /* reg 18: window V pos = 0 */
```

These write value `0x00` into VDP registers 17 and 18:

| Register | Written value | WD bit | Position field | Genesis VDP interpretation |
|----------|---------------|--------|----------------|---------------------------|
| Reg 17 (Window H) | 0x00 | WD=0 (right mode) | HP=0 | Window occupies cols 0–39 = **full screen width** |
| Reg 18 (Window V) | 0x00 | VD=0 (down mode) | VP=0 | Window occupies rows 0–27 = **full screen height** |

**Genesis VDP Window semantics:**
- Reg 17 bit7=0 (right mode): Window covers columns HP to 39. HP=0 → columns 0–39 = entire screen.
- Reg 17 bit7=1 (left mode): Window covers columns 0 to HP−1. HP=0 → 0 columns = **OFF**.
- Reg 18 bit7=0 (down mode): Window covers rows VP to 27. VP=0 → rows 0–27 = entire screen.
- Reg 18 bit7=1 (up mode): Window covers rows 0 to VP−1. VP=0 → 0 rows = **OFF**.

**Conclusion:** `force_clean_vram_init()` configures the Window to cover the entire screen. This is the complete and sole cause of Plane A (FG) being invisible.

### 2.3 Call Order — Window Off → Window On

The Window is turned off by `genesistan_sync_title_vdp_layout()` via `VDP_setWindowOff()` (main.c:1447), but `force_clean_vram_init()` runs **after** it (main.c:2147–2150) and overwrites the Window registers:

```
genesistan_sync_title_vdp_layout()   ← main.c:2147, calls VDP_setWindowOff() → reg17=0x80, reg18=0x80
force_clean_vram_init()              ← main.c:2150, writes reg17=0x00, reg18=0x00 → FULL SCREEN WINDOW
```

The Window-off state is never restored after `force_clean_vram_init()`. For the entire duration of arcade mode, the Window plane covers the full screen.

### 2.4 Window VRAM Is Never Written by Our Pipeline

VDP register 3 (`*ctrl = 0x8334`) sets Window VRAM base address:
```
0x34 × 0x400 = 0xD000
```

`genesistan_pc080sn_commit_planes` writes:
- 0xC000 — Plane B (BG) — 2048 words
- 0xE000 — Plane A (FG) — 2048 words
- **0xD000 (Window) — never written**

`force_clean_vram_init()` zero-fills all 64KB of VRAM at arcade handoff, including 0xD000. After that, Window VRAM stays zero for the entire arcade session. Every Window nametable entry is 0x0000: priority=0, palette=0, tile=0. Tile 0's pixel data at VRAM 0x0000 was also zero-filled. Palette entry 0 was zero-filled (black). The Window plane therefore displays solid black, covering Planes A and B entirely.

### 2.5 Source of the Visible Rolling Dots

The rolling dots originate from the **sprite layer**. Sprites render on top of all planes, including the Window. The arcade tick's sprite hooks populate WRAM sprite blocks; the commit pipeline writes them to SAT at VRAM 0xF800. These sprites are visible over the all-black Window. The Plane A content (FG buffer with debug text, game tiles) is unreachable by the display until the Window is disabled.

## 3. Root Cause

**WINDOW_PLANE_FULL_SCREEN_COVERAGE**

`force_clean_vram_init()` at main.c:2130–2131 sets VDP registers 17 and 18 to 0x00 (right-of-col-0, down-from-row-0), activating full-screen Window coverage. This overwrites the preceding `VDP_setWindowOff()` call. The Window plane at 0xD000 is never written by the arcade pipeline. It displays solid black over the entire screen, hiding Plane A (FG) and Plane B (BG). Only sprites (above all planes) are visible.

## 4. Single Next Implementation Target

Fix `force_clean_vram_init()` to disable the Window plane.

**Change required** in main.c lines 2130–2131:

```c
/* BEFORE (covers full screen): */
*ctrl = 0x9100; /* reg 17: window H pos = 0 */
*ctrl = 0x9200; /* reg 18: window V pos = 0 */

/* AFTER (Window OFF — bit7=1 = left/up mode with 0 columns/rows = no Window): */
*ctrl = 0x9180; /* reg 17: Window H OFF (left mode, 0 cols) */
*ctrl = 0x9280; /* reg 18: Window V OFF (up mode, 0 rows) */
```

This is the exact equivalent of `VDP_setWindowOff()` applied directly to the VDP control port. No other change is needed.

**Expected result after fix:**
- Window plane is disabled
- Plane A (VRAM 0xE000) is now the topmost plane
- `B:FFFF A:FFFF` debug text visible on screen
- Arcade FG content (tiles, text) visible on screen
- Rolling dots (sprites) continue to render correctly on top

## 5. Non-Goals

| Component | Changed? |
|-----------|----------|
| `force_clean_vram_init()` reg17/reg18 | YES (this build) |
| `genesistan_pc080sn_commit_planes` | NO |
| `text_writer_ptr_to_xy()` | NO |
| `genesistan_debug_fg_proof()` | NO |
| Build 326 sentinel / capture logic | NO |
| Any other function | NO |

## 6. Build 327 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_327.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same 5 pre-existing warnings)

### Expected visual
- **B:FFFF A:FFFF** text visible on actual game screen (row 1, cols 1–13): **USER MUST VERIFY**
- Plane A content (FG tiles from attract mode) visible: **USER MUST VERIFY**
- No regression on sprites/scrolling: **USER MUST VERIFY**
- No crash: **USER MUST VERIFY**

## 7. Final Verdict

The FG write pipeline works correctly end-to-end (confirmed by Build 326). The sole reason Plane A content is invisible is that `force_clean_vram_init()` enables full-screen Window coverage at arcade handoff and nothing ever disables it. Changing two words (0x9100→0x9180, 0x9200→0x9280) in `force_clean_vram_init()` disables the Window and exposes Plane A to the display.
