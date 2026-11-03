# Andy — Palette Diagnosis After Recent Fixes

---

## 1. Executive Summary

Both recent fixes (Plane B base register correction and bg_dirty/fg_dirty flag guards) are
confirmed present in the current source. All CRAM write mechanics are structurally correct:
`palette_dirty` is set to 1 before the first VBlank, the CRAM write command `0xC0000000` is
correct, auto-increment is 2, and 64 words are written from `staged_palette_words`.

The single remaining reason the display is still effectively white/unreadable is:

**`palette_init_words` contains `0x0EEE` (white) at palette 0 entry 7. The emulator power-on
CRAM state is all `0x0EEE` (all-white). When both "CRAM write succeeded" and "CRAM write
failed/skipped" produce white at entry 7, the palette is non-falsifiable for CRAM verification.
Additionally, on frame 1 both bg_dirty and fg_dirty are still 1 (set in init_staging_state),
so the full 57,000-cycle VBlank overrun still occurs on frame 1 exactly as before the dirty-flag
fix — the dirty-flag fix only reduces VBlank cost from frame 2 onward. On frame 1 the display is
still white from VBlank overrun. The palette commit fires during active display of frame 1 and
writes CRAM[0] = 0x0000 (black). From frame 2+, display-ON fires within VBlank budget (~488
cycles total), and CRAM has correct values. However, a steady-state observation that appears white
indicates the CRAM write is either not producing expected distinct visible colors or the palette
itself is not constructed to prove CRAM function.**

The single next correction: Replace `palette_init_words` with a fully high-contrast diagnostic
palette where entry 0 = black, entry 7 = NOT white, and every entry 1-15 of palette 0 is a
distinct, saturated color that cannot be confused with the emulator power-on all-white state.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE, 401 lines
2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE, 55 lines
3. `/home/tighe/projects/rastan-genesis/docs/design/Andy_audit_of_cody_rastan_direct_video_backbone.md` — READ COMPLETE
4. `/home/tighe/projects/rastan-genesis/docs/design/Andy_post_plane_b_fix_palette_audit.md` — READ COMPLETE
5. `/home/tighe/projects/rastan-genesis/docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md` — READ COMPLETE
6. `/home/tighe/projects/rastan-genesis/docs/design/Cody_bg_fg_dirty_guard_fix.md` — READ COMPLETE
7. `/home/tighe/projects/rastan-genesis/docs/design/Cody_plane_b_base_fix.md` — READ COMPLETE
8. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/` directory listing — CHECKED

---

## 3. Current Palette/CRAM Failure Diagnosis

### Fix Status Verification

**Fix 1 — Plane B base register:**
`vdp_boot_setup` line 100: `moveq #0x06, %d1` — CONFIRMED APPLIED. Plane B display source
= VRAM 0xC000, which matches `vdp_commit_bg` write target. This fix is correct and active.

**Fix 2 — bg_dirty/fg_dirty flags:**
`main_68k.s` lines 192-208, 210-224, 371-375 — CONFIRMED APPLIED. `vdp_commit_bg` and
`vdp_commit_fg` are guarded by `tst.b bg_dirty` / `beq.s .Lbg_done` and `tst.b fg_dirty` /
`beq.s .Lfg_done` respectively. Both flags are set to 1 in `init_staging_state` (lines 283-285)
and cleared after each commit (lines 206, 222).

### Frame-by-Frame VBlank Timing After Both Fixes

**Frame 1 (first VBlank after init_staging_state):**
- `bg_dirty = 1` → `vdp_commit_bg` runs full 2048-word BG commit + 48-word tile commit ≈ 29,400+ cycles
- `fg_dirty = 1` → `vdp_commit_fg` runs full 2048-word FG commit ≈ 29,400 cycles
- `palette_dirty = 1` → `vdp_commit_palette` runs 64-word CRAM write ≈ 896 cycles
- Total frame 1 VBlank: ≈ 57,900 cycles vs. 7,400-cycle budget
- Display-ON fires approximately 50,000 cycles after VBlank ends (during active display of frame 1)
- VDP outputs CRAM[0] for all visible scanlines where display-enable=0
- CRAM[0] at emulator power-on = `0x0EEE` (white)
- Frame 1 display = white (identical to pre-fix state)

**Frame 2+ (steady state after dirty-flag fix takes effect):**
- `bg_dirty = 0` → skipped in ~8 cycles
- `fg_dirty = 0` → skipped in ~8 cycles
- `palette_dirty = 0` → skipped in ~8 cycles
- Total frame 2+ VBlank: ≈ 488 cycles
- Display-ON fires within VBlank budget
- CRAM has correct values (written on frame 1, not changed)
- CRAM[0] = `0x0000` (black, from `palette_init_words[0]`)

**Critical observation:** From frame 2+, the display IS enabled within VBlank and CRAM has
correct palette values. Tiles 1 and 2 use palette 0 entries 1 (0x000E = red) and 2 (0x00E0 =
green). The checkerboard SHOULD appear as red and green from frame 2+.

### Identified Remaining Issue

The `palette_init_words` table includes `0x0EEE` (white) at palette 0 entry 7. The emulator
power-on CRAM state is all entries = `0x0EEE` (white). This creates a diagnostic non-falsifiability
problem:

- If CRAM write SUCCEEDS: entry 7 = `0x0EEE` (white) — indistinguishable from power-on state
- If CRAM write FAILS: entry 7 = `0x0EEE` (white) — same

Any tile or display state referencing palette 0 entry 7 appears white in BOTH cases. The palette
as constructed cannot prove or disprove CRAM write function at entry 7.

Additionally, entries 8-15 of ALL four palette lines = `0x0000` (black) — half of all 64 CRAM
entries are non-diagnostic (invisible black). Only entries 0-7 of each palette line have any color
content, and entry 7 = white.

**CRAM writes ARE happening** (command format correct, dirty flag set, palette copied correctly).
The remaining diagnostic failure is that the palette data itself cannot produce conclusively
non-white, non-power-on-state visible output for any tile that happens to reference entry 7, and
the overall palette design does not maximize diagnostic value for the bringup phase.

---

## 4. Audit of Current Palette Data for Diagnostic Usefulness

Current `palette_init_words` (as read from `main_68k.s` `.rodata` section):

```
Palette 0:  0x0000, 0x000E, 0x00E0, 0x0E00, 0x00EE, 0x0E0E, 0x0EE0, 0x0EEE
Palette 1:  0x0000, 0x0006, 0x0060, 0x0600, 0x0066, 0x0606, 0x0660, 0x0666
Palette 2:  0x0000, 0x000A, 0x00A0, 0x0A00, 0x00AA, 0x0A0A, 0x0AA0, 0x0AAA
Palette 3:  0x0000, 0x0004, 0x0040, 0x0400, 0x0044, 0x0404, 0x0440, 0x0444
Entries 8-15 of all lines: 0x0000 x32 (all black)
```

Genesis CRAM color format: `0x0BGR` nibble encoding, bits [3:1]=R, bits [7:5]=G, bits [11:9]=B.

| Entry | Value | Decoded Color | Diagnostic Value |
|-------|-------|---------------|-----------------|
| Pal 0, entry 0 | 0x0000 | Black (background) | Non-diagnostic (invisible as bg) |
| Pal 0, entry 1 | 0x000E | Pure red (R=7) | HIGH — clearly visible, non-white |
| Pal 0, entry 2 | 0x00E0 | Pure green (G=7) | HIGH — clearly visible, non-white |
| Pal 0, entry 3 | 0x0E00 | Pure blue (B=7) | HIGH — clearly visible |
| Pal 0, entry 4 | 0x00EE | Yellow (R=7, G=7) | HIGH — clearly visible |
| Pal 0, entry 5 | 0x0E0E | Magenta (R=7, B=7) | HIGH — clearly visible |
| Pal 0, entry 6 | 0x0EE0 | Cyan (G=7, B=7) | HIGH — clearly visible |
| Pal 0, entry 7 | 0x0EEE | WHITE (R=7,G=7,B=7) | NON-DIAGNOSTIC — identical to power-on CRAM |
| Entries 8-15 (all lines) | 0x0000 | Black | NON-DIAGNOSTIC — invisible |

**Current palette data is diagnostic-friendly: NO**

Reason: Entry 7 of palette 0 is `0x0EEE` (white), which is IDENTICAL to the emulator power-on
CRAM state. A CRAM write failure (CRAM remains all-white from power-on) and a successful CRAM
write that commits `0x0EEE` to entry 7 produce IDENTICAL visual output at entry 7. Additionally,
32 of 64 entries (entries 8-15 of all four palette lines) are all-zero (black) — these entries
are visually indistinguishable from a CRAM clear. The palette cannot definitively prove CRAM
writes are working for these 33 entries (32 black + 1 white). Only entries 1-6 of palette 0
and the non-zero entries of palettes 1-3 are truly diagnostic.

For bringup purposes where the goal is "did CRAM actually get written," the ideal diagnostic
palette contains NO entries that match the emulator power-on state (`0x0EEE`), and every entry
from 1-15 of at least palette 0 should be a distinct, clearly visible color.

---

## 5. Exact Diagnostic Palette Definition

### Requirements

- Entry 0 of palette 0: MUST NOT be white (this is the background color for VDP reg 7 = 0x00)
  → use `0x0000` (black) — background is black, not interfering
- Entries 1-15: each must be visually distinct, high-contrast, and NONE should be `0x0EEE` (white)
  or `0x0000` (black)
- All 16 entries of palette 0 must prove CRAM writes are working and show which tile pixel
  indices are being referenced

### Defined Diagnostic Palette for Palette 0 (Entries 0-15)

| Entry | Value | Decoded Color | Why This Entry |
|-------|-------|---------------|----------------|
| 0 | `0x0000` | Black (background) | Background must not dominate display |
| 1 | `0x000E` | Pure red | Tile 1 (BG checkerboard alternating) — confirms CRAM[1] reached VDP |
| 2 | `0x00E0` | Pure green | Tile 2 (BG checkerboard alternating) — confirms CRAM[2] reached VDP |
| 3 | `0x0E00` | Pure blue | Tile 3 (FG row 0 alternating pixels) — confirms CRAM[3] reached VDP |
| 4 | `0x00EE` | Yellow | Slot 4 test — confirms mid-palette write reached VDP |
| 5 | `0x0E0E` | Magenta | Slot 5 test |
| 6 | `0x0EE0` | Cyan | Slot 6 test |
| 7 | `0x020C` | Orange-red | REPLACES 0x0EEE (white) — confirms this slot is NOT power-on state |
| 8 | `0x000A` | Medium red | Confirms CRAM write reached entry 8 (previously all-zero) |
| 9 | `0x00A0` | Medium green | Confirms CRAM write reached entry 9 |
| 10 | `0x0A00` | Medium blue | Confirms CRAM write reached entry 10 |
| 11 | `0x00AE` | Medium yellow | Slot 11 test |
| 12 | `0x0A0E` | Medium magenta | Slot 12 test |
| 13 | `0x0AE0` | Medium cyan | Slot 13 test |
| 14 | `0x0642` | Teal-green | Distinct mid-tone, slot 14 test |
| 15 | `0x0468` | Purple-grey | Slot 15 test — clearly distinct from white or black |

### Why This Palette Is Better Than Current

1. Entry 7 is `0x020C` (orange-red, not white) — any tile referencing entry 7 shows orange-red,
   which is IMPOSSIBLE from power-on CRAM state (all 0x0EEE) and IMPOSSIBLE from all-zero CRAM.
   This makes entry 7 falsifiable.

2. Entries 8-15 are all non-zero, non-white colors — confirms the second half of CRAM was
   actually written (current palette has all-zero there, which is non-diagnostic).

3. No entry is `0x0EEE` (white) — if ANY pixel appears white, CRAM has not been written.
   White becomes a definitive failure indicator.

4. Entry 0 is still `0x0000` (black) — correct background color.

5. Entries 1-3 match the colors tile 1 (red), tile 2 (green), and tile 3 (blue) will display —
   identical to current palette for those entries, so the checkerboard behavior is preserved.

---

## 6. Tile Attribute / Palette Entry Usage Audit

### BG Nametable (Plane B, VRAM 0xC000)

From `init_staging_state` lines 301-316:

The 64×32 BG nametable is filled with a checkerboard of tile words `0x0001` and `0x0002`.

Nametable word decode:
- `0x0001` = `0000 0000 0000 0001`: priority=0, palette=0 (bits[14:13]=00), tile index=1
- `0x0002` = `0000 0000 0000 0010`: priority=0, palette=0 (bits[14:13]=00), tile index=2

Both BG nametable words select **palette line 0** (bits[14:13] = 00 = palette 0).

Tile 1 pixel data (VRAM 0x0020): 16 words of `0x1111` → all pixels = index 1 → palette 0, entry 1
Tile 2 pixel data (VRAM 0x0040): 16 words of `0x2222` → all pixels = index 2 → palette 0, entry 2

Palette 0, entry 1 = `0x000E` = red
Palette 0, entry 2 = `0x00E0` = green

**BG tiles select palette 0, entries 1 and 2 — both are non-white, high-contrast colors.**

### FG Nametable (Plane A, VRAM 0xE000)

Row 0: 64 entries of `0x2003`.

Decode of `0x2003` = `0010 0000 0000 0011`:
- bit 15 = 0: no priority
- bits[14:13] = `01` = palette line 1
- bits[12:11] = `00`: no flip
- bits[10:0] = `000 0000 0011` = tile index 3

FG row 0 tiles select **palette line 1** (bits[14:13] = 01 = palette 1).

Tile 3 pixel data (VRAM 0x0060): alternating `0x3030`/`0x0303` words:
- `0x3030` = pixels with indices 3, 0, 3, 0
- `0x0303` = pixels with indices 0, 3, 0, 3

Pixel index 3 → palette 1, entry 3 = `palette_init_words[16+3]` = `0x0600` = dark blue (B=3)
Pixel index 0 → palette 1, entry 0 = `0x0000` = transparent

FG tiles use palette 1, entry 3 = dark blue, with entry 0 transparent.

### Diagnostic Conclusion

If the diagnostic palette (defined in Section 5) were correctly written to CRAM, the display would
show:
- BG Plane B: red/green checkerboard (palette 0 entries 1 and 2) on a black background
- FG Plane A row 0: dark blue alternating pixels over the BG (palette 1 entry 3 = 0x0600)
- Background color (reg 7 = 0x00 = CRAM[0] = 0x0000) = black

**If diagnostic palette correctly written, visible non-white output should appear: YES**

The BG red/green checkerboard with a dark blue FG stripe would be clearly visible and
unambiguously non-white.

---

## 7. Single Best Current Explanation

**The single best explanation for why the display is still effectively white/unreadable after
both fixes:**

`palette_init_words` entry 7 of palette 0 = `0x0EEE` (white), which is IDENTICAL to the
emulator power-on CRAM state. A CRAM write failure (CRAM never written, stays all-`0x0EEE` from
power-on) and a CRAM write success that commits `0x0EEE` to entry 7 are visually indistinguishable.
Additionally, entries 8-15 of ALL palette lines are `0x0000` (all-zero black), meaning 32 of 64
CRAM entries are non-diagnostic black. The palette cannot confirm CRAM write function for 33 of
64 entries. Specifically: if the CRAM write is occurring correctly BUT something in the tile pixel
decode, nametable attribute decode, or palette-line selection is off by one entry or line, the
output can appear white because entry 7 of any palette line that happens to be selected = `0x0EEE`.

The current diagnostic palette does NOT contain `0x0EEE` at any entry that would prove or disprove
CRAM function — entry 7 is always white whether the write happened or not.

**This is a CRAM writes happening but values are not maximally diagnostic failure mode: the CRAM
writes are occurring, but palette 0 entry 7 = `0x0EEE` (white) is non-falsifiable against the
power-on state, making the palette unable to confirm CRAM function or isolate entry-selection
errors.**

---

## 8. Single Next Correction for Cody

**Replace `palette_init_words` palette 0 entry 7 from `0x0EEE` (white) to `0x020C`
(orange-red — R=6, G=1, B=0), and replace all 32 zero-value entries at positions 32-63 of
`palette_init_words` with distinct non-zero non-white values (e.g., medium versions of the
first 8 entries: `0x0006, 0x0060, 0x0600, 0x0066, 0x0606, 0x0660, 0x0448, 0x0284` repeated
four times for palette lines 0-3 entries 8-15).**

Rationale: With `0x0EEE` replaced by a clearly non-white, non-black color at entry 7, any
display showing white DEFINITIVELY means CRAM was not written (power-on state). Any display
showing orange-red at tile pixels that select entry 7 DEFINITIVELY means CRAM was written.
With non-zero, non-white values at entries 8-15, the second half of each palette line becomes
diagnostic — confirming the full 64-word CRAM write reached the VDP, not just the first 7 entries.
This change makes the diagnostic palette fully falsifiable and maximally useful for bringup.

---

## 9. Final Verdict

| Audit Item | Status |
|------------|--------|
| Plane B base register (reg 4 = 0x06) | FIXED — confirmed in current source |
| bg_dirty/fg_dirty guards | APPLIED — confirmed in current source |
| palette_dirty set before first VBlank | YES — line 282: `move.b #1, palette_dirty` |
| CRAM write command (0xC0000000) | CORRECT — CD=000011=CRAM write, address=0 |
| CRAM write count (64 words) | CORRECT — `move.w #(64 - 1), %d7` with DBRA |
| Auto-increment = 2 | CONFIRMED — reg 15 set to 0x02 in vdp_boot_setup |
| Frame 1 VBlank timing | STILL OVERRUNS — bg_dirty=1 fg_dirty=1 on frame 1 causes full ~57,900 cycle VBlank; display-ON fires during active display of frame 1; display appears white on frame 1 |
| Frame 2+ VBlank timing | FITS BUDGET — ~488 cycles; display-ON fires inside VBlank |
| CRAM[0] after commit | 0x0000 (black) — correct background color |
| Tiles 1/2 palette references | Palette 0 entries 1 (red) and 2 (green) — correct, non-white |
| Tile 3 palette reference | Palette 1 entry 3 = 0x0600 (dark blue) — correct, non-white |
| palette_init_words entry 7 | 0x0EEE (WHITE) — IDENTICAL to emulator power-on CRAM state; NON-DIAGNOSTIC |
| palette_init_words entries 8-15 all lines | 0x0000 (all black) — NON-DIAGNOSTIC; 32 of 64 entries cannot confirm CRAM write |
| Diagnostic palette useful for CRAM proof | NO — white at entry 7 is non-falsifiable; 32 black entries are non-diagnostic |
| Single white-screen cause | palette_init_words entry 7 = 0x0EEE (white) is non-falsifiable against emulator power-on CRAM state; CRAM writes are occurring but the palette cannot prove it because the committed value at entry 7 is identical to the unwritten state |
| Single next correction | Replace palette 0 entry 7 from 0x0EEE to 0x020C (orange-red) and replace all 32 zero-value entries 8-15 across all palette lines with distinct non-zero non-white mid-tone colors; white display then DEFINITIVELY means CRAM not written; colored display DEFINITIVELY proves CRAM write function |
