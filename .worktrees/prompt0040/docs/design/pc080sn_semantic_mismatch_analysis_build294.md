# PC080SN Semantic Mismatch Analysis — Build 294

## SECTION 1 — ROOT CAUSE

The primary failure in Build 294 is that the `adda.w #0x0014, %a4` correction applied to both BG and FG assembly in Build 294 reads from the wrong memory position. The arcade BG inner loop at `0x559B2` and FG inner loop at `0x55A14` each write **two distinct values per C-window cell**:

1. A tile number (hardware-rendered) read from `A2 + D7` (**no +0x14**) → written to the PC080SN C-window as word 1.
2. A WRAM shadow value read from `A2 + 0x14 + D7` → written to game WRAM at `(A0 - 0xC08000)/2 + 0x10DE00`. This is game-logic metadata only; the PC080SN hardware chip does not render from it.

The Build 293 analysis incorrectly identified the +0x14 location as the tile code source. Build 294 applied `adda.w #0x0014, %a4` to both BG and FG inner loop base pointers, causing the assembly to read WRAM-shadow values as tile codes instead of the true C-window tile number. The Python LUT was simultaneously updated to discover tiles from `table_base + 0x14 + ...`, collecting the same wrong set of tile codes. Both changes are consistently wrong in the same direction: every tile index emitted by the assembly and every tile preloaded by Python is shifted +0x14 bytes forward relative to the correct position.

---

## SECTION 2 — EXACT MISMATCH LIST

- **mismatch #1 (BG + FG, PRIMARY):** `adda.w #0x0014, %a4` added to both assembly inner-loop base pointers in Build 294 (`startup_trampoline.s:214` for BG, `startup_trampoline.s:340` for FG). Arcade BG inner loop (`build/maincpu.disasm.txt:107424`, `0x559FC`) reads the C-window tile number via `lea %a2@(0,%d7:w),%fp` (zero displacement). Arcade FG inner loop (`build/maincpu.disasm.txt:107476`, `0x55A9E`) reads the C-window tile number via `lea %a2@(0,%d7:w),%fp` (zero displacement). In both planes the +0x14 displacement is used only for the WRAM shadow write (`0x559CE`/`0x55A44`: `lea %a2@(20,%d7:w),%fp`), not for the hardware-rendered tile index. Current assembly reads WRAM-shadow bytes as tile codes on every VDP write.

- **mismatch #2 (BG + FG, Python LUT):** `precompute_pc080sn_tile_lut.py` tile discovery was updated in Build 294 to use `addr = table_base + PC080SN_TABLE_TILE_OFFSET + (strip<<1) + (row<<3)` for BG and `addr = table_base + PC080SN_TABLE_TILE_OFFSET + (strip<<3) + (col<<1)` for FG, where `PC080SN_TABLE_TILE_OFFSET = 0x14`. The correct tile codes are at `table_base + 0 + (strip<<1) + (row<<3)` (BG) and `table_base + 0 + (strip<<3) + (col<<1)` (FG). The LUT now maps WRAM-shadow byte sequences to VRAM slots, not the true arcade tile codes. Assembly and Python are consistently wrong together, so no "unmapped tile" fault occurs at runtime — the assembly writes shifted indices, the LUT happens to have entries for those shifted indices, producing coherent but graphically wrong output (wrong tiles displayed for every cell).

---

## SECTION 3 — VERIFIED ARCADE BEHAVIOR

**Source: `build/maincpu.disasm.txt`**

**BG inner loop** (`0x559B2`, lines 107397–107431), per row (0..3):
1. Writes attr_word from workram[0x10D080+i*2] to C-window word 0 at A0.
2. Checks sentinel at `A2+0x20`.
3. Computes D7 = `(strip_raw<<1) + (row<<3)`.
4. Reads WRAM shadow tile from `A2 + 0x14 + D7` (`0x559CE: lea %a2@(20,%d7:w),%fp; movew %fp@,%d0`) → writes to game WRAM at `(A0-0xC08000)/2 + 0x10DE00`. This is game logic metadata.
5. Reads **C-window tile number** from `A2 + 0 + D7` (`0x559FC: lea %a2@(0,%d7:w),%fp; movew %fp@,%d0`) → writes to C-window word 1 at A0 (`0x55A02: movew %d0,%a0@`). **No +0x14 displacement.**
6. Advances A0 by 256 bytes to next row.

**FG inner loop** (`0x55A14`, lines 107432–107483), per col (0..3):
1. Writes attr_word to C-window word 0 at A0.
2. Checks sentinel at `A2+0x20`.
3. Computes D7 = `(strip_index<<3) + (col<<1)`, where strip_index = `~strip_raw & 3` (mode≠2) or `strip_raw & 3` (mode==2).
4. Reads WRAM shadow tile from `A2 + 0x14 + D7` (`0x55A44: lea %a2@(20,%d7:w),%fp`) → writes to game WRAM. Game logic metadata.
5. Reads **C-window tile number** from `A2 + 0 + D7` (`0x55A9E: lea %a2@(0,%d7:w),%fp; movew %fp@,%d0`) → writes to C-window word 1 at A0 (`0x55AA4: movew %d0,%a0@`). **No +0x14 displacement.**
6. Advances A0 by 4 bytes to next col.

**Key distinction**: The PC080SN C-window cell format is word 0 = attr, word 1 = tile number (14-bit, hardware-rendered). The arcade code maintains a parallel WRAM shadow copy for game-logic queries (e.g., collision by tile), but this shadow is not the source of hardware tile rendering. The +0x14 region is the shadow; the +0x00 region is the hardware tile source.

---

## SECTION 4 — CURRENT IMPLEMENTATION BEHAVIOR (BUILD 294)

**BG assembly** (`startup_trampoline.s:207–214`):
- Computes `A4 = rastan_maincpu + table_base + strip<<1`.
- Line 214: `adda.w #0x0014, %a4` — **incorrect addition; A4 now points into WRAM-shadow region**.
- Inner row loop (`startup_trampoline.s:241–276`): reads `(%a4)` with stride 8 per row. Source is `table_base + strip<<1 + 0x14 + row*8`. Wrong.

**FG assembly** (`startup_trampoline.s:333–340`):
- Computes `A4 = rastan_maincpu + table_base + strip<<3`.
- Line 340: `adda.w #0x0014, %a4` — **incorrect; same class of error**.
- Inner col loop (`startup_trampoline.s:366–408`): reads `(%a4)` with stride 2 per col. Source is `table_base + strip<<3 + 0x14 + col*2`. Wrong.

**Python LUT** (`precompute_pc080sn_tile_lut.py:80–97`):
- BG: `addr = table_base + PC080SN_TABLE_TILE_OFFSET + (strip<<1) + (row<<3)` where `PC080SN_TABLE_TILE_OFFSET = 0x14`.
- FG: `addr = table_base + PC080SN_TABLE_TILE_OFFSET + (strip<<3) + (col<<1)`.
- Both use wrong +0x14 offset. LUT contains VRAM slot assignments for WRAM-shadow byte values, not for true arcade tile codes.

**Runtime effect**: Assembly and Python are consistently wrong — the same shifted codes are both written and looked up in the LUT. No unmapped-tile faults occur. The tile codes emitted correspond to different tiles than the arcade intended, producing wrong-tiles-displayed-in-correct-cells pattern rather than blank tiles.

---

## SECTION 5 — MINIMAL CORRECTION REQUIRED

**Remove `adda.w #0x0014, %a4` from both BG and FG assembly.**

In `startup_trampoline.s`, in `genesistan_asm_tilemap_commit_bg` (line 214):
```
/* DELETE this line: */
adda.w  #0x0014, %a4
```

And in `genesistan_asm_tilemap_commit_fg` (line 340):
```
/* DELETE this line: */
adda.w  #0x0014, %a4
```

**Revert Python tile discovery to zero offset, keeping expanded strip range.**

In `precompute_pc080sn_tile_lut.py`, `collect_tiles_from_tables()`:
```python
# BG — was:
addr = table_base + PC080SN_TABLE_TILE_OFFSET + (strip << 1) + (row << 3)
# BG — correct:
addr = table_base + (strip << 1) + (row << 3)

# FG — was:
addr = table_base + PC080SN_TABLE_TILE_OFFSET + (strip << 3) + (col << 1)
# FG — correct:
addr = table_base + (strip << 3) + (col << 1)
```

The `PC080SN_TABLE_TILE_OFFSET` constant (`0x14`) and `MAX_STRIP_RANGE = 64` remain in the file. `MAX_STRIP_RANGE` for the BG strip scan loop is correct and must be kept. `PC080SN_TABLE_TILE_OFFSET` is still used in `descriptor_valid()` bounds checking and must not be removed.

These are two deletions (assembly) and two address formula edits (Python). No new systems, no restructuring, no C changes.

---

## SECTION 6 — DO NOT DO LIST

- Do not add any new offset to the tile read — the correct displacement from table_base is zero; the final address is `A2 + D7` exactly as the arcade computes it.
- Do not remove `PC080SN_TABLE_TILE_OFFSET` from `precompute_pc080sn_tile_lut.py` — it is still needed in `descriptor_valid()` for bounds checking.
- Do not revert the BG strip range expansion (`range(MAX_STRIP_RANGE)`) — that part of Build 294 was correct.
- Do not change the FG strip range (`PC080SN_FG_STRIP_RANGE = 4`) — FG strip IS masked to 0..3 in the arcade.
- Do not change the FG strip masking (`andi.w #0x0003, %d7`) in the assembly — FG strip masking is correct arcade behavior.
- Do not re-add BG strip masking (`andi.w #0x0003, %d7`) removed in Build 294 — BG strip_raw is unmasked in the arcade.
- Do not change the attr_lut, attr key extraction, or TILE_ATTR_FULL bit mapping — attr decode is correct.
- Do not change the VRAM destination address computation (row bias, plane bases, stride) — those are correct.
- Do not modify the scroll system (`genesistan_scroll_from_workram_vdp`) — scroll is confirmed correct.
- Do not change FG dest_ptr behavior — the FG no-writeback fix from Build 294 is correct and must stay.
- Do not redesign the C dispatchers, Python preprocessing, or assembly structure.
