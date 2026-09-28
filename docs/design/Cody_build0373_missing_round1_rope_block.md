# Cody — Build 0373 missing Round-1 rope-area block

## Result

Build 0373 corrects the general resident-column ring transform used when a vertical Plane-A
row is rebuilt. At the supplied Round-1 rope view, the corrected transform selects the arcade
terrain descriptor at `0x02A290` instead of its right-hand neighbor at `0x02A294`. No map data,
tile art, palette, collision data, sprite, or object behavior was changed. BlastEm visual and
interactive acceptance remains user-required.

## Exact arcade location and source

- Round: 1, Phase-1 cave/rope section.
- Retained progression at the rope: `A5+0x013E = 3`; selector `A5+0x10A8 = 0`.
- The visible cell is trailing segment 2 terrain retained in the 64-column ring while the stream
  front has advanced into progression 3.
- Segment-local map position: rows `36..39`, columns `52..55`; metatile row/group `9`, column/block
  `13`. Global metatile block is 45 (world columns `180..183`).
- Arcade strip source entry: `0x02A290`, attribute `0x0003`, metatile descriptor `0x3008`.
- Tile codes by row:
  `01CF 01D0 01D1 00AD / 01D2 01D3 01D4 01D5 / 01D6 01D7 01D8 01D9 /
  01DA 01DB 01DC 01DD`.

At the representative retained state, row-group 9's live source pointer is `0x02A2A0`, the
stream front is physical column 4 (`group=1`, `strip=0`), and physical column 52 is four
metatile blocks behind that front across the ring wrap. Therefore:

```text
correct: 0x02A2A0 + (-4 * 4) = 0x02A290
0372:    0x02A2A0 + ((52/4 - 16) * 4) = 0x02A294
```

The Build-0372 entry `0x02A294` selects descriptor `0x206C` and codes
`0408 0409 040A 040B / 040C 00C2 00C3 00C4 / 040D 00C6 00C7 010B /
00C9 040E 040F 0410`. This is the first divergence; tile translation and residency occur only
after the wrong descriptor has already been selected.

## Collision classification

Classification: **C — collision correct, visual Layer-A metatile selected incorrectly**.

The arcade descriptor `0x3008` supplies `0x3100` at collision cells row 38, columns 53–54
(the other cells in this 4×4 block are zero). The retained selector-0 horizontal producer writes
those words from the correct live descriptor when the column enters. The faulty vertical visual
row rebuild does not write the collision grid, so Build 0373 does not alter collision. The
Build-0366 special-solid actor contract is also untouched.

## Fix and architecture

`resolve_plane_a_cell` now unwraps resident columns around the retained arcade streaming front
`{A5+0x10CC strip_group, A5+0x10CA strip_index}`. A physical column after the front belongs to the
preceding 64-column revolution and subtracts 16 metatile blocks. The horizontal entering-column
path retains its existing leading-edge calculation. This is one general decoder correction; it
contains no Round-1, rope, segment, row, column, tile, or actor special case.

Semantic cut: retain the arcade decision and state that publish a logical terrain cell, then emit
the final Genesis Plane-A name word. The retired tail remains the PC080SN name-RAM/address walk.
No C-window shadow, virtual chip RAM, projection, fallback renderer, or new transitional
compatibility was introduced. Existing collision WRAM remains the arcade gameplay-semantic
side channel, not graphics emulation.

## Validation

- Focused source-cell gate: PASS (`0x02A290`, attr `0x0003`, descriptor `0x3008`; old result
  `0x02A294/0x206C`).
- Final canonical disassembly at `0x07079A..0x0707CE` contains the group/strip ring comparison and
  wrapped `-16` block correction.
- Canonical gate: PASS.
- GENESIS NTSC gameplay-entry gate: PASS; 240 post-entry frames, zero address errors, bus errors,
  illegal instructions, or crash-handler entries.
- Standard GENESIS NTSC 30-second trace: completed 1,798 frames.
- Existing Phase-1 seven-epoch gate: known FAIL; unchanged and the artifact is preserved.
- Complete same-number artifact set: PASS.

Canonical artifact: `dist/rastan-direct/rastan_direct_video_test_build_0373.bin`, 1,719,992 bytes,
SHA-256 `4bece179504e3ce7a83bc7d2ca392ba4a4aba4cadb1386e2f4f72431b573c2cc`.

Existing project tools reused: original arcade Layer-A oracle in
`tools/graphics_editor/server.py`, retained route evidence, canonical map compiler, assembler,
postpatch/address-map pipeline, canonical gate, gameplay-entry gate, and GENESIS NTSC trace.

New tooling created: none.

Why new tooling was necessary: not applicable.

BlastEm validation: **USER REQUIRED**.

