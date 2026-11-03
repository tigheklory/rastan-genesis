/* ORIGINAL ARCADE PC: 0x00055C4A / 0x00055C5E / 0x00055C7A  PC080SN name-table column streamer.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (three adjacent Ghidra functions). Byte-faithful from
 * build/maincpu.disasm.txt (variant world_rev1). CHECKPOINT H22.
 *
 * This is the ARCADE side of "scene descriptor -> visible PC080SN tilemap": it copies one column of
 * 64 tile words from the selected layout source into the PC080SN foreground name table, advancing the
 * scroll column. It is the sibling of the collision-grid producer 0x559B2 (raw/000559b2.c, H13):
 * both walk the same descriptor/strip state; 0x55C7A emits the *visual* tile word, 0x559B2 emits the
 * *collision* word for the same world cell. That shared source is the visual+collision coherence
 * point (H22 section 14).
 *
 * WORLD STATE READ (A5, byte offsets):
 *   A5+0x10FC  scene descriptor pointer      (produced by 0x503A0)
 *   A5+0x10F8  current name-table dest cursor (a0)
 *   A5+0x10F6  scroll column counter          (advanced per streamed column)
 *   A5+0x1126  saved descriptor pointer copy
 *   0x10D0FC / 0x10D100 / 0x10D104  retained per-frame stream pointers (a0/a1/a2 staging)
 *
 * EXACT DISASSEMBLY:
 *   -- 0x55C4A : stream one descriptor column, then advance --
 *   55c4a: 202d 10fc      movel  %a5@(0x10FC),%d0        ; d0 = scene descriptor ptr
 *   55c4e: 2b40 1126      movel  %d0,%a5@(0x1126)        ; save it
 *   55c52: 6100 000a      bsrw   0x55c5e                 ; stream the column
 *   55c56: 526d 10f6      addqw  #1,%a5@(0x10F6)         ; scroll column += 1
 *   55c5a: 6190           bsrs   0x55bec                 ; post-column bookkeeping
 *   55c5c: 4e75           rts
 *   -- 0x55C5E : set up source/dest and call the 64-row copy --
 *   55c5e: 206d 10f8      moveal %a5@(0x10F8),%a0        ; a0 = name-table dest cursor
 *   55c62: 227c 0010d104  moveal #0x10D104,%a1           ; a1 = staged tile word source
 *   55c68: 267c 0010d100  moveal #0x10D100,%a3
 *   55c6e: 2453           moveal %a3@,%a2                ; a2 = layout source base (from 0x10D100)
 *   55c70: 6100 0008      bsrw   0x55c7a                 ; copy 64 rows down the column
 *   55c74: 2b48 10f8      movel  %a0,%a5@(0x10F8)        ; save advanced dest cursor
 *   55c78: 4e75           rts
 *   -- 0x55C7A : copy 64 tile words down one name-table column --
 *   55c7a: 4242           clrw   %d2                     ; d2 = row 0..0x3F
 *   55c7c: 30d1           movew  %a1@,%a0@+              ; [dest]=staged header word; dest+=2
 *   55c7e: 3e02           movew  %d2,%d7
 *   55c80: eb4f           lslw   #5,%d7                  ; d7 = row*32 (strip stride)
 *   55c82: 302d 10f6      movew  %a5@(0x10F6),%d0
 *   55c86: e348           lslw   #1,%d0                  ; d0 = scroll_col*2
 *   55c88: de40           addw   %d0,%d7                 ; d7 = row*32 + col*2
 *   55c8a: 4df2 7000      lea    %a2@(0,%d7:w),%fp       ; fp = &layout_source[row*32 + col*2]
 *   55c8e: 3016           movew  %fp@,%d0                ; d0 = tile word
 *   55c90: 3080           movew  %d0,%a0@                ; store into name table (no post-inc here)
 *   55c92: d1fc 000000fe  addal  #0xFE,%a0               ; dest += 254 (next row in name-table column)
 *   55c98: 5242           addqw  #1,%d2
 *   55c9a: 0c42 0040      cmpiw  #0x40,%d2
 *   55c9e: 66dc           bnes   0x55c7c                 ; loop 64 rows
 *   55ca0: 4e75           rts
 *
 * PC080SN SEMANTIC CUT (H22 section 11): the world DECISION is the layout-source word chosen by
 *   (descriptor -> a2 base) + row*32 + scroll_col*2. The final SEMANTIC tile datum is that 16-bit
 *   tile word. The PC080SN-SPECIFIC EXECUTION is the name-table geometry: 64 rows per column with a
 *   +0xFE dest stride into PC080SN foreground memory. A native Genesis realization keeps the source
 *   selection and the tile word, and replaces only the +0xFE name-table walk with a VDP plane write.
 */

extern short A5[];
extern unsigned short *g_stream_src_10D100;   /* [0x10D100] layout source base */
extern unsigned short *g_stream_hdr_10D104;   /* [0x10D104] staged header word */
extern void stream_post_column_55bec(void);

/* 0x55C7A : copy 64 tile words down one PC080SN name-table column (dest stride 0xFE). */
void pc080sn_stream_column_55c7a(unsigned short *dest, const unsigned short *hdr,
                                 const unsigned short *layout_src)
{
    unsigned short scroll_col = (unsigned short)A5[0x10F6/2];
    *dest = *hdr;                                          /* 0x55C7C header word */
    unsigned char *d = (unsigned char *)dest + 2;
    for (int row = 0; row < 0x40; ++row) {                 /* 64 rows */
        unsigned short tile = layout_src[(row * 32 + scroll_col * 2) / 2]; /* row*32 + col*2 bytes */
        *(unsigned short *)d = tile;                       /* 0x55C90 */
        d += 0xFE;                                         /* 0x55C92 next row down the column */
    }
}

/* 0x55C5E : bind dest/source and copy the column. */
void pc080sn_stream_setup_55c5e(void)
{
    unsigned short *dest = (unsigned short *)(unsigned long)(unsigned)A5[0x10F8/2];
    pc080sn_stream_column_55c7a(dest, g_stream_hdr_10D104, g_stream_src_10D100);
    /* A5+0x10F8 = advanced dest cursor (dest after 64 rows) */
}

/* 0x55C4A : stream one descriptor column and advance the scroll column. */
void pc080sn_stream_advance_55c4a(void)
{
    A5[0x1126/2] = A5[0x10FC/2];              /* save descriptor ptr (longword in situ) */
    pc080sn_stream_setup_55c5e();
    A5[0x10F6/2] += 1;                        /* scroll column += 1 */
    stream_post_column_55bec();
}
