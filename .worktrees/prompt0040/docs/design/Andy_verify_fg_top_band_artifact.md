# Andy — Verify FG Top-Band Artifact

## 1. Executive Summary

Cody's interpretation is confirmed correct. The blue band near the top of the display that
moves over time is caused by two facts acting together:

1. `init_staging_state` fills FG (Plane A) row 0 with 64 entries of `0x2003` (tile 3, palette
   line 1). Palette line 1 entry 3 = `0x0800` = blue in Genesis CRAM format.
2. `arcade_tick_logic` drives `staged_scroll_y_fg` with `(tick_counter >> 1) & 0x001F`,
   producing values 0–31 that cycle every 64 frames. When the value returns to 0, row 0 of the
   FG plane is at the top of the visible display and the blue stripe is visible.

The BG plane, VBlank commit order, dirty flag logic, and CRAM stability are all correct. No
deeper render pipeline issue is required to explain the artifact.

---

## 2. Inputs Audited

| File | Purpose |
|------|---------|
| `apps/rastan-direct/src/main_68k.s` | Full source — init_staging_state, arcade_tick_logic, VBlank handler, palette table |
| `apps/rastan-direct/src/boot/boot.s` | Boot stub, vector table |
| `docs/design/Cody_bss_vma_wram_fix.md` | .bss WRAM VMA fix record |
| `docs/design/Cody_bg_fg_dirty_guard_fix.md` | Dirty-flag guard implementation record |
| `docs/design/Cody_diagnostic_palette_replacement.md` | Palette replacement record |
| `docs/design/Andy_rastan_direct_video_bringup_plan.md` | Bring-up architecture, VBlank commit order, WRAM contracts |

---

## 3. BG Plane Verification

### What init_staging_state writes to BG

```
lea     staged_bg_buffer, %a0
moveq   #31, %d6           ; row counter 31..0
.Lbg_row:
  moveq   #63, %d5         ; col counter 63..0
  .Lbg_col:
    move.w  %d6, %d0
    eor.w   %d5, %d0
    andi.w  #0x0001, %d0
    bne.s   .Lbg_tile_two
    move.w  #0x0001, (%a0)+
    bra.s   .Lbg_next
  .Lbg_tile_two:
    move.w  #0x0002, (%a0)+
  .Lbg_next:
    dbra    %d5, .Lbg_col
  dbra    %d6, .Lbg_row
```

When `(row XOR col) & 1 == 0`: writes `0x0001` (tile 1, palette 0, no priority, no flip).
When `(row XOR col) & 1 == 1`: writes `0x0002` (tile 2, palette 0, no priority, no flip).

This produces a 32×64 alternating tile-1/tile-2 checkerboard across all of Plane B.

### Tile content

`tile_init_words`:
- Tile 1 (words 0–15): `0x1111` × 16. Every pixel = 1. With palette 0 entry 1 = `0x000E`
  (Genesis CRAM: R=7, G=0, B=0 → red), tile 1 renders solid red.
- Tile 2 (words 16–31): `0x2222` × 16. Every pixel = 2. With palette 0 entry 2 = `0x00E0`
  (Genesis CRAM: R=0, G=7, B=0 → green), tile 2 renders solid green.

### Result

The BG produces a red/green checkerboard exactly as described. Palette 0 entry 0 = `0x0000`
(transparent/black background), entry 1 = `0x000E` = red, entry 2 = `0x00E0` = green.

### Is BG involved in the blue artifact?

No. BG uses palette 0 only. Palette 0 contains no blue entries in the diagnostic palette.
The BG is stable and is not the source of the blue artifact.

**BG plane correct: YES**

---

## 4. FG Plane Verification

### What init_staging_state writes to FG

```
; Step 1 — clear entire FG buffer to zero
lea     staged_fg_buffer, %a0
move.w  #(2048 - 1), %d7
.Lfg_clear:
  clr.w   (%a0)+
  dbra    %d7, .Lfg_clear

; Step 2 — overwrite row 0 with 0x2003 × 64
lea     staged_fg_buffer, %a0
move.w  #(64 - 1), %d7
.Lfg_row0:
  move.w  #0x2003, (%a0)+
  dbra    %d7, .Lfg_row0
```

After init:
- Rows 1–31: all `0x0000` = tile 0, palette 0 = fully transparent.
- Row 0 (cols 0–63): `0x2003` = tile index 3, palette line 1 (bits 14-13 = `01`), priority 0,
  no flip.

### Decoding 0x2003

Genesis nametable word format (bits 15-0):
- Bit 15: priority
- Bits 14-13: palette select (0-3)
- Bit 12: vertical flip
- Bit 11: horizontal flip
- Bits 10-0: tile index

`0x2003` = `0010 0000 0000 0011`:
- Priority = 0
- Palette = `01` = palette line 1
- Vflip = 0, Hflip = 0
- Tile index = 3

### Palette line 1, entry 3

`palette_init_words` layout (64 words total, 16 per line):

```
Palette 0 (words  0-15): 0x0000,0x000E,0x00E0,0x0E00,0x00EE,0x0E0E,0x0EE0,0x020C,
                          0x0022,0x0046,0x006A,0x008C,0x00A2,0x00C6,0x00EA,0x002E
Palette 1 (words 16-31): 0x0200,0x0400,0x0600,0x0800,0x0A00,0x0C00,0x0E00,0x0C20,
                          0x0202,0x0404,0x0606,0x0808,0x0A0A,0x0C0C,0x0E0C,0x0C0E
```

Palette 1 entry 3 = `0x0800`.

Genesis CRAM format: `0000 BBB0 GGG0 RRR0` (3 bits each, bit 0 of each channel unused).
`0x0800` = `0000 1000 0000 0000`:
- B = bits 11-9 = `100` = 4
- G = bits 7-5 = `000` = 0
- R = bits 3-1 = `000` = 0

B=4, G=0, R=0 = blue.

### Tile 3 pixel content

Tile 3 occupies words 32–47 of `tile_init_words`:
```
.rept 8
.word 0x3030
.word 0x0303
.endr
```
Each word encodes 4 pixels (4 bits each). `0x3030` = pixels 3,0,3,0. `0x0303` = pixels 0,3,0,3.
Alternating rows of `3030` / `0303` gives a fine checker where non-zero pixels = 3 = palette
entry 3 = blue, and zero pixels = palette entry 0 = `0x0200` (R=1, G=0, B=0 = dim red for
palette 1 entry 0).

Row 0 of FG thus renders as a stripe of blue/dim-red fine checkerboard pixels, visually
dominated by the blue component.

### Is the rest of FG transparent?

Yes. Rows 1–31 are all `0x0000` = tile 0, palette 0. Tile 0 is VRAM offset 0 = blank/zero
pixels. These entries render as fully transparent, allowing the BG plane to show through.

**FG plane correct for current bring-up target: NO**

Row 0 contains a deliberate blue stripe. For the bring-up target (transparent FG over
checkerboard BG), row 0 should be `0x0000` like all other rows. The `.Lfg_row0` fill loop
is the defect.

---

## 5. FG Scroll Verification

### Formula

From `arcade_tick_logic` (lines 265–268):
```
move.w  tick_counter, %d0
lsr.w   #1, %d0
andi.w  #0x001F, %d0
move.w  %d0, staged_scroll_y_fg
```

`staged_scroll_y_fg = (tick_counter >> 1) & 0x001F`

### Values produced over time

`tick_counter` starts at 0 and increments by 1 each frame (each call to `arcade_tick_logic`).

| tick_counter | tick >> 1 | & 0x001F | staged_scroll_y_fg |
|-------------|-----------|----------|--------------------|
| 0           | 0         | 0        | 0                  |
| 1           | 0         | 0        | 0                  |
| 2           | 1         | 1        | 1                  |
| 3           | 1         | 1        | 1                  |
| ...         | ...       | ...      | ...                |
| 62          | 31        | 31       | 31                 |
| 63          | 31        | 31       | 31                 |
| 64          | 32        | 0        | 0  (wraps)         |

The FG vertical scroll cycles through values 0–31, spending 2 frames at each value, then
returning to 0 after 64 frames.

### What the scroll does to row 0

The Genesis VDP interprets `staged_scroll_y_fg` as an upward scroll offset for Plane A. When
`staged_scroll_y_fg = 0`, Plane A row 0 (the blue stripe) is exactly at the top of the visible
screen. As the value increases from 0 to 31, row 0 scrolls downward off the top edge (in pixel
terms, the plane shifts down), and then at value 32 (masked to 0) it wraps back to the top.

In the Genesis VDP, vertical scroll is applied as: the first row shown on screen = row
`staged_scroll_y_fg` of the nametable (in 8-pixel units for coarse scroll). At scroll=0, row 0
is at the top. At scroll=1, row 1 is at the top and row 0 has scrolled off the top edge.

The blue stripe at row 0 is therefore visible at the top of the display for 2 frames per
64-frame cycle (at tick 0–1), then scrolls progressively downward and off-screen, then
re-appears at the top after 64 frames (~1.07 seconds at 60Hz).

This matches the observed behavior: "blue band near the top that moves over time."

**Scroll behavior explains moving blue band: YES**

---

## 6. Whether a Deeper Commit/Timing Problem Is Still Required

### VBlank commit order (from source lines 53–80)

1. Registers saved.
2. VDP status read (interrupt acknowledge).
3. Display OFF (`0x34` = mode2 display-off).
4. `vdp_commit_bg` — guarded by `bg_dirty`; full 2048-word BG nametable write; clears flag.
5. `vdp_commit_fg` — guarded by `fg_dirty`; full 2048-word FG nametable write; clears flag.
6. Palette commit — guarded by `palette_dirty`; clears flag.
7. Display ON (`0x74` = mode2 display-on).
8. `vdp_commit_scroll` — unconditional; writes FG X, BG X to HScroll table; writes FG Y, BG Y
   to VSRAM via `0x40000010` command; executed after display ON.
9. `frame_counter` incremented.
10. Registers restored, RTE.

### Dirty flag behavior

Both `bg_dirty` and `fg_dirty` are set to 1 in `init_staging_state`, cleared after the first
VBlank commit. Neither is re-set after init. After frame 1, VBlank executes only the scroll
commit and frame counter increment — the 2048-word nametable loops do not execute again.

This means the blue row-0 content is committed to VRAM exactly once and persists there
permanently. The scroll animation then periodically brings row 0 into view.

### Palette stability

`palette_dirty` is set once in init, cleared after first VBlank. Palette is stable from
frame 1 onward. Palette line 1 entry 3 = `0x0800` = blue is in CRAM from frame 1 and does
not change.

### Evidence for deeper issues

None. The BG is described as stable and correct (confirming the `.bss` fix and dirty flag fix
are both working). The commit order is correct. CRAM is stable. No overrun is present — after
the first frame, VBlank is doing only scroll+counter, well within budget.

The artifact is fully accounted for by the FG row-0 content and the scroll animation.
A deeper render pipeline explanation is not required and is not supported by the evidence.

**Deeper rendering/commit issue still required to explain artifact: NO**

---

## 7. Single Root Cause

`init_staging_state` contains a `.Lfg_row0` fill loop that writes `0x2003` to the first 64
words of `staged_fg_buffer` (FG row 0). `0x2003` selects tile 3 with palette line 1, and
palette line 1 entry 3 = `0x0800` = blue. The tile 3 pixel pattern (`0x3030/0x0303`) renders
blue pixels on all non-zero pixel positions. `arcade_tick_logic` drives `staged_scroll_y_fg`
with `(tick_counter >> 1) & 0x001F`, cycling 0–31 every 64 frames. When the scroll value is 0,
FG row 0 is at the top of the visible display and the blue stripe is visible. The combination
of a blue-filled FG row 0 in VRAM and a periodic scroll animation that returns the scroll offset
to 0 every 64 frames produces the moving blue top-band artifact.

---

## 8. Single Next Correction for Cody

**File**: `apps/rastan-direct/src/main_68k.s`

**Location**: `init_staging_state`, the `.Lfg_row0` fill loop (lines 324–328):
```asm
    lea     staged_fg_buffer, %a0
    move.w  #(64 - 1), %d7
.Lfg_row0:
    move.w  #0x2003, (%a0)+
    dbra    %d7, .Lfg_row0
```

**Change**: Delete these 4 lines (the `lea`, `move.w #(64-1)`, `.Lfg_row0:` label, and
`dbra` loop) in their entirety. The `.Lfg_clear` loop immediately above already zeroes all
2048 words of `staged_fg_buffer`. After that loop completes, no additional write to row 0 is
needed. With the `.Lfg_row0` block removed, the entire FG plane is `0x0000` = transparent,
the blue stripe is never written to VRAM, and the artifact is eliminated.

No other change is required.

---

## 9. Final Verdict

| Task | Result |
|------|--------|
| BG plane verified correct | YES — red/green checkerboard from tile-1/tile-2 alternation, palette 0, no blue involvement |
| FG plane verified for bring-up target | NO — row 0 is filled with blue (0x2003) instead of transparent (0x0000) |
| FG scroll behavior explains moving band | YES — (tick_counter >> 1) & 0x001F cycles 0-31 every 64 frames, periodically scrolling row 0 to top |
| Deeper timing/commit issue required | NO — commit order correct, dirty flags working, palette stable |
| Cody's interpretation confirmed | YES — FG row-0 blue fill + scroll animation is the complete and correct explanation |
| Single correction identified | YES — delete the .Lfg_row0 fill loop in init_staging_state |
