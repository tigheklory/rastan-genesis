/* rastan_world_stream.c — CHECKPOINT H22
 * Semantic reconstruction of the ORIGINAL ARCADE PC080SN world streamer (scene descriptor -> visible
 * tilemap) and its relationship to the collision-grid producer. NOT original Taito source; byte-
 * faithful control flow in raw/00055c4a.c (+ the H13 collision sibling raw/000559b2.c). All PCs from
 * build/maincpu.disasm.txt (world_rev1). A5 = 0x10C000.
 *
 * SCENE DESCRIPTOR FORMAT (0x3951C, 12 bytes each — PROVEN, verified from maincpu.bin):
 *   struct scene_descriptor {                       // e.g. scene 0: 00 02 00 00 d1 1c | 00 02 00 00 d9 1c
 *     struct { uint16 count_flags; uint32 layout_ptr; } fg;   // foreground half (6 bytes)
 *     struct { uint16 count_flags; uint32 layout_ptr; } bg;   // background half (6 bytes)
 *   };
 *   count_flags observed = 0x0002; layout_ptr = 16-bit ROM offset (0x1cd1, 0x1cd9, 0x1cf1, ...).
 *   Scene index -> descriptor: A5+0x10FC = 0x3951C + scene*12 (0x503A0).
 *
 * PC080SN COLUMN STREAMER (0x55C4A/0x55C5E/0x55C7A — raw/00055c4a.c, COMPLETE):
 *   per streamed column:
 *     - dest cursor  A5+0x10F8 (into PC080SN foreground name table)
 *     - source base  [0x10D100] (layout source, selected from the descriptor)
 *     - staged hdr   [0x10D104]
 *     - scroll col   A5+0x10F6
 *   0x55C7A copies 64 tile words down the column: for row 0..0x3F,
 *       tile = layout_src[row*32 + scroll_col*2];  name_table[dest] = tile;  dest += 0xFE;
 *   then 0x55C4A advances A5+0x10F6 (scroll column) and runs post-column bookkeeping 0x55BEC.
 *
 * VISUAL + COLLISION COHERENCE (H22 section 14 — general architecture, NOT a special case):
 *   The SAME world descriptor drives two producers over the SAME strip/column state:
 *     0x55C7A  descriptor layout source -> 16-bit TILE word   -> PC080SN name table (visual)
 *     0x559B2  descriptor.word1 -> collision RECORD ->
 *              cw = (rec[0x20]==0x00FF) ? rec[0x22] : rec[0x14 + strip*2 + cell*8]   (H13)
 *              marker = cw >> 8                                  -> live collision grid 0x10DE00
 *   So one source scene record yields both the visible masonry and its collision/marker property.
 *   Build 0378's third-chain finding (visible masonry + uniform +0x22 property from one record) is
 *   one instance of this general rule and is used here only as corroboration; the arcade static code
 *   above is authority.
 *
 * PC080SN SEMANTIC CUT (H22 section 11) — the ReROM translation boundary:
 *     ARCADE WORLD DECISION           = descriptor -> layout source word chosen by (row*32 + col*2)
 *         -> FINAL SEMANTIC TILE/CELL = the 16-bit tile word (visual) / collision word (0x559B2)
 *             -> PC080SN-SPECIFIC     = 64-row name-table walk with +0xFE dest stride (0x55C7A) /
 *                                       0x10DE00 collision-ring store (0x559B2)
 *   Genesis realization keeps the source selection + tile/collision word and replaces only the
 *   chip-specific write (name-table +0xFE walk -> VDP plane; 0x10DE00 ring -> native collision grid).
 *   NO Genesis code is written here.
 */

/* semantic view; see raw/00055c4a.c for byte-faithful transcription */
typedef struct { unsigned short count_flags; unsigned long layout_ptr; } scene_half; /* 6 bytes packed */
typedef struct { scene_half fg; scene_half bg; } scene_descriptor;                   /* 12 bytes */

void world_stream_column(const unsigned short *layout_src, unsigned short scroll_col,
                         unsigned short *name_table_dest)
{
    unsigned char *d = (unsigned char *)name_table_dest;
    for (int row = 0; row < 0x40; ++row) {
        unsigned short tile = layout_src[(row * 32 + scroll_col * 2) / 2];
        *(unsigned short *)d = tile;
        d += 0xFE;
    }
}
