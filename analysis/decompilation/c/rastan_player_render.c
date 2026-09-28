/* rastan_player_render.c — CHECKPOINT H24
 * Semantic reconstruction of the ORIGINAL ARCADE player body composer (frame slot -> PC090OJ sprite
 * pieces). NOT original Taito source; byte-faithful in raw/00054492.c. PCs from maincpu.disasm.txt
 * (world_rev1). A5 = 0x10C000.
 *
 * BODY FRAME TABLE (0x5BD40) — PROVEN, all 75 slots decoded (h24_player_frame_cells.tsv):
 *   [0..74] : 75 word offsets (0x0096..0x070C) relative to 0x5BD40.
 *   0x5BD40 + offset[slot] : 4 piece records (fixed loop), 6 bytes each:
 *       [tile:word][xoff:sbyte][yoff:sbyte][control:word]
 *   tile==0 => blank sprite. 73 distinct composites of 75 (2 aliased). Player bodies = 3 visible
 *   cells (head y=-32, two body cells y=-16) + 1 blank; a few slots use up to 4 visible cells.
 *
 * SEMANTIC FRAME  ->  PC090OJ OUTPUT (the ReROM cut):
 *   PLAYER SEMANTIC FRAME = { slot, up to 4 cells, each (tile, signed xoff, signed yoff, control) }
 *     + facing A5+0x1114 + origin (A5+0x10BE screen X, A5+0x10C0 screen Y) + weapon overlay A5+0x12FA.
 *   PC090OJ-SPECIFIC OUTPUT = per piece, 4 SAT words written to 0x10D1D2:
 *     word0 control/attr (palette = control&0xF, hflip |0x4000 when facing), word1 screenY =
 *     (yoff + A5+0x10C0 + 1) & 0x1FF, word2 tile, word3 screenX = ((facing? -xoff-16 : xoff) +
 *     A5+0x10BE) & 0x1FF.
 *   ReROM keeps the semantic frame + origin + facing + palette line; only the 0x10D1D2 SAT word
 *   packing (and the &0x1FF wrap) is hardware realization. NO Genesis code here.
 *
 * PALETTE (H24 §14): 255/263 visible player pieces carry control 0x0003 -> palette LINE 3, colbank
 *   0x60 — the single shared player-body source recorded in specs/palette_decisions.json (Rastan
 *   player decision; NOT duplicated here). A small tail set (8 pieces on death/special slots) reads
 *   control low-nibble 0/8; enumerated in h24_player_frame_cells.tsv, treated as the same player
 *   palette identity pending per-slot confirmation. So a single player palette source maps to ALL
 *   reachable body frames.
 *
 * WEAPON OVERLAY: A5+0x12FA selects 0x5CD8A (1) / 0x5D068 (4) / 0x5D346 (2) / 0x5D666 (else); overlay
 *   pieces are appended after the 4 body pieces using the same 6-byte record format.
 */

typedef struct { unsigned short tile; signed char xoff, yoff; unsigned short control; } body_piece; /* 6 bytes */

/* semantic composite; byte-faithful packing in raw/00054492.c */
typedef struct { unsigned char slot; body_piece piece[4]; } player_body_frame;

/* palette line for a player piece = control low nibble (player body = line 3). */
unsigned char player_piece_palette_line(unsigned short control) { return control & 0x0F; }
