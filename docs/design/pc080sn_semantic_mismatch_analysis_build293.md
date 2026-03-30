# PC080SN Semantic Mismatch Analysis — Build 293

## SECTION 1 — ROOT CAUSE

The primary failure is a **missing 0x14-byte offset in the tile code read** for both BG and FG planes. The tile-index data table embedded in each descriptor's strip table starts at byte offset 20 (`0x14`) from the table base address. The arcade BG inner loop reads tile codes from `A2 + 0x14 + (strip<<1) + (row<<3)` and the FG inner loop from `A2 + 0x14 + (strip<<3) + (col<<1)`. The current assembly in `startup_trampoline.s` reads from `A2 + 0 + strip_offset`, with no 0x14 displacement. This causes the assembly to read "tag words" (control metadata at the beginning of the table) as tile codes, producing entirely wrong tile indices on every VDP write for both planes.

---

## SECTION 2 — EXACT MISMATCH LIST

- **mismatch #1 (BG + FG, PRIMARY):** Tile code read missing 0x14 byte offset. Arcade BG reads tile at `table_base + 0x14 + (strip<<1) + (row<<3)`. Arcade FG reads tile at `table_base + 0x14 + (strip<<3) + (col<<1)`. Current BG assembly (`startup_trampoline.s:212-214`) computes `A4 = rastan_maincpu + table_base + strip<<1` then reads `(%a4)` with stride 8 per row — no 0x14 displacement. Current FG assembly (`startup_trampoline.s:337-339`) computes `A4 = rastan_maincpu + table_base + strip<<3` then reads `(%a4)` with stride 2 per col — no 0x14 displacement. The first 0x14 bytes of the table are tag/control words, not tile codes. Every VDP write in both planes uses wrong tile indices.

- **mismatch #2 (BG ONLY):** BG strip_index is masked to 0..3 in current assembly (`startup_trampoline.s:188, andi.w #0x0003, %d7`). Arcade BG inner loop at `0x559C2` reads `movew %a5@(4298), %d7` then `lslw #1, %d7` — raw strip counter, no mask. The strip counter increments monotonically at `0x55954` (`addqw #1, %a5@(4298)`) after each call to either builder. BG uses the raw value; the current mask wraps at 4, causing BG to loop through only 4 strip positions rather than streaming through the full table.

- **mismatch #3 (BG ONLY, SECONDARY TO #2):** Python tile LUT discovery (`precompute_pc080sn_tile_lut.py:62, for strip in range(4)`) scans only strips 0..3. Because BG strip_raw can exceed 3 without masking, tile codes at `table_base + 0x14 + strip<<1 + row<<3` for strip > 3 are never collected. Those tile codes receive `lut[tile] = 0` (unmapped) → rendered as blank/slot-0 tiles.

- **mismatch #4 (FG ONLY):** FG dest_ptr is incorrectly written back to workram after the assembly call. Arcade FG builder (`0x55990`, `build/maincpu.disasm.txt:107386-107396`) outer loop has no `movel %a0, %a5@(4260)` — A0 is not saved to workram[0x10A4] at any point during or after the outer loop. Current code (`main.c:1337, pc080sn_workram_write_u32(PC080SN_DEST_PTR_B_OFFSET, dest)`) writes the accumulated post-assembly dest back, causing the FG starting position to drift forward by 256 bytes on every frame.

---

## SECTION 3 — VERIFIED ARCADE BEHAVIOR

**Source: `build/maincpu.disasm.txt`**

**Descriptor list builder** (`0x55904`, lines 107346–107365):
- Reads 16 × 4-byte desc_addrs from workram[0x1000] (A5+0x1000).
- For each desc_addr: extracts word0 (attr_word) → stored at workram[0x1080 + i×2]; extracts word1 (table_base_u16) → zero-extends to u32 → stored as absolute ROM address at workram[0x1040 + i×4].
- Function: desc list pre-builder at 0x55904, called before BG/FG builders each frame.

**BG builder outer loop** (`0x55968`, lines 107374–107385):
- A0 = workram[0x10A0] (dest ptr). A3 = workram[0x1040] (pre-built tile table addr list). A1 = workram[0x1080] (pre-built attr word list).
- Per descriptor: A2 = `*A3` (absolute ROM addr of tile table); calls inner BG loop at `0x559B2`; **writes A0 back to workram[0x10A0] after each inner call** (`55982: movel %a0, %a5@(4256)`); advances A3 by 4, A1 by 2.

**BG inner loop** (`0x559B2`, lines 107397–107431), per row (0..3):
1. Writes attr_word from `*A1` to C-window at A0 (first word of cell).
2. Checks sentinel at `A2+0x20` (= 0xFF means blank tile → use `A2+0x22`).
3. Reads tile code from `A2 + 0x14 + (strip_raw<<1) + (row<<3)`, where strip_raw = workram[0x10CA] **unmasked**.
4. Writes tile code to WRAM shadow at `(A0 - 0xC08000)/2 + 0x10DE00`.
5. Reads tag word from `A2 + 0 + (strip_raw<<1) + (row<<3)` → writes to C-window at A0+2.
6. Advances A0 by 256 bytes (2 + 254) to next row.
- **Strip_raw for BG**: no masking applied. Source: `0x559C2: movew %a5@(4298), %d7; lslw #1, %d7`.

**FG builder outer loop** (`0x55990`, lines 107386–107396):
- A0 = workram[0x10A4] (dest ptr). Same A3/A1 tables.
- Per descriptor: A2 = `*A3`; calls inner FG loop at `0x55A14`; **does NOT write A0 back to workram[0x10A4]**; advances A3 by 4, A1 by 2.

**FG inner loop** (`0x55A14`, lines 107432–107483), per col (0..3):
1. Writes attr_word from `*A1` to C-window at A0.
2. Checks sentinel at `A2+0x20`.
3. Computes FG strip_index: if mode≠2, `strip_index = ~strip_raw & 3`; if mode==2, `strip_index = strip_raw & 3` (source: `0x55A2E–0x55A3C`). **FG strip IS masked to 0..3**.
4. Reads tile code from `A2 + 0x14 + (strip_index<<3) + (col<<1)`.
5. Writes tile code to WRAM shadow.
6. Reads tag word from `A2 + 0 + (strip_index<<3) + (col<<1)` → writes to C-window at A0+2.
7. Advances A0 by 4 bytes to next col.

**Rainbow Islands analog** (`docs/research/rainbow_islands_arcade_vs_genesis_graphics_comparison.md`, section 5.1):
- Arcade tile-plane intent = CPU writes PC080SN C-window words. Genesis implementation = compute VDP destination, stream converted words. The "tag+tile" dual-write pattern in PC080SN maps: first word → attr/control, second word → tile selector. Only the tile selector (at +0x14) is the VDP-visible tile code.

---

## SECTION 4 — CURRENT IMPLEMENTATION BEHAVIOR

**C dispatchers** (`main.c:1287–1338`):

`genesistan_hook_tilemap_plane_a()` reads `strip_index` raw from workram[0x10CA], reads `dest` from workram[0x10A0], decodes to (dest_row, dest_col) via `pc080sn_dest_ptr_to_row_col()`, calls `genesistan_asm_tilemap_commit_bg(dest, strip_index, dest_row, dest_col)`, writes result back to workram[0x10A0].

`genesistan_hook_tilemap_plane_b()` applies `(mode==2) ? strip_raw&3 : ~strip_raw&3` for FG strip_index, reads dest from workram[0x10A4], calls `genesistan_asm_tilemap_commit_fg(...)`, **writes result back to workram[0x10A4]** (incorrect per arcade behavior).

**BG assembly** (`startup_trampoline.s:172–291`):
- Line 188: `andi.w #0x0003, %d7` — **masks strip_index to 0..3** before any use.
- Lines 208–214: computes `A4 = rastan_maincpu + table_base + strip<<1`. **No +0x14 displacement.**
- Lines 241–276 (inner row loop): reads `(%a4)` per row, stride 8. Tile source = `table_base + strip<<1 + row*8`. **Missing 0x14.**
- VDP write (lines 248–269): computes VRAM address `0xC000 + (dest_row-4)*128 + dest_col*2`, applies row-bias skip for rows < 4.

**FG assembly** (`startup_trampoline.s:297–427`):
- Line 313: `andi.w #0x0003, %d7` — masks strip_index to 0..3 (correct for FG).
- Lines 333–339: computes `A4 = rastan_maincpu + table_base + strip<<3`. **No +0x14 displacement.**
- Lines 366–408 (inner col loop): reads `(%a4)` per col, stride 2. Tile source = `table_base + strip<<3 + col*2`. **Missing 0x14.**
- VDP write: computes VRAM address `0xE000 + (dest_row-4)*128 + dest_col*2`.

**Python LUT** (`precompute_pc080sn_tile_lut.py:62`):
- `for strip in range(4)` — collects tiles only from strips 0..3 for both BG and FG paths.
- BG tiles at strip_raw > 3 are not collected → `lut[code] = 0` → those tiles display as blank.

---

## SECTION 5 — MINIMAL CORRECTION REQUIRED

**Add `adda.w #0x0014, %a4` immediately after the strip-offset `adda.w` in both BG and FG outer loops.**

In `startup_trampoline.s`, in `genesistan_asm_tilemap_commit_bg` (after line 214):
```
adda.w  %d0, %a4        /* existing: A4 = maincpu + table_base + strip<<1 */
adda.w  #0x0014, %a4    /* ADD THIS: A4 = maincpu + table_base + strip<<1 + 0x14 */
```

And in `genesistan_asm_tilemap_commit_fg` (after line 339):
```
adda.w  %d0, %a4        /* existing: A4 = maincpu + table_base + strip<<3 */
adda.w  #0x0014, %a4    /* ADD THIS: A4 = maincpu + table_base + strip<<3 + 0x14 */
```

This is two identical one-line additions, one per plane, in the existing assembly file. No new systems, no restructuring, no changes to C or Python. The bounds check at line 205 (`cmpi.w #0x7FE0, %d3`) accommodates the additional offset without overflow into unmapped ROM (max access = `0x7FE0 + 0x14 + 6 + 24 = 0x8022`, well within the 0x60000-byte ROM).

---

## SECTION 6 — DO NOT DO LIST

- Do not change the attr_lut, attr key extraction, or TILE_ATTR_FULL bit mapping — the attr decode is correct.
- Do not change the desc_addr reading from workram[0x1000] — the source is correct.
- Do not change the FG strip_index masking (`andi.w #0x0003, %d7`) — the arcade FG IS masked to 0..3.
- Do not modify the VRAM destination address computation (row bias, plane bases, stride) — those are correct.
- Do not fix the BG strip masking (`andi.w #0x0003, %d7`) in the same step as the 0x14 fix — that is a separate subsequent fix after the tile offset is corrected and verified.
- Do not fix the FG dest_ptr writeback in the same step — that is a separate subsequent fix.
- Do not modify `precompute_pc080sn_tile_lut.py` strip scan range in the same step.
- Do not redesign the C dispatchers, Python preprocessing, or assembly structure.
- Do not introduce any buffering, shadow, or staging between the tile read and the VDP write.
- Do not modify the scroll system (`genesistan_scroll_from_workram_vdp`) — scroll is confirmed correct.
