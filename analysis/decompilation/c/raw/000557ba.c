/* ORIGINAL ARCADE PC: 0x000557BA / 0x00055854  foreground vertical (Y) scroll update + row stream.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (two adjacent Ghidra functions). Byte-faithful from
 * build/maincpu.disasm.txt (variant world_rev1). CHECKPOINT H23.
 *
 * This is the per-frame VERTICAL foreground scroll updater. It advances the FG Y-scroll value
 * A5+0x10AE by the scroll step A5+0x10D8 (mod 512), driven by the direction accumulator A5+0x10B8,
 * and triggers a new map ROW stream (0x406A4, direction A5+0x13D0 = 2 up / 3 down) each 8-px step.
 * Its X sibling is 0x55B3C (raw/00055ab4.c); the HW commit is 0x55AB4.
 *
 * KEY FIELDS (A5, verified from writers/readers):
 *   A5+0x10AE  FG Y scroll value    -> PC080SN 0xC40002 (0x55ACC), wrap mod 512 (&0x1FF)
 *   A5+0x10B8  scroll dir accumulator (>=0 up branch, <0 down); UPPER LIMIT 160 (0xA0) at 0x557BE
 *   A5+0x10B2  sub-row (8-px) accumulator; bit3 set => one 8-px row boundary crossed
 *   A5+0x10D8  scroll step (px/frame; <=4, see 0x51880 / 0x539BA)
 *   A5+0x10D0  scroll flags: bit6 = up-limit reached (A5+0x10A8 section-kind gate), bit7 = down flag
 *   A5+0x13D0  row-stream direction mode (2 = up, 3 = down)
 *   A5+0x10A8  section-kind gate (0 => allow further up scroll past the accumulator limit)
 *
 * EXACT DISASSEMBLY:
 *   -- 0x557BA : dispatcher on direction accumulator + upper limit --
 *   557ba: 322d 10b8      movew  %a5@(0x10B8),%d1
 *   557be: 0c41 00a0      cmpiw  #0xA0,%d1              ; 160 = vertical scroll upper limit
 *   557c2: 6d66           blts   0x5582a               ; accumulator < 160 -> keep scrolling (down/normal)
 *   557c4: 0c6d 0000 10a8 cmpiw  #0,%a5@(0x10A8)        ; at limit: section-kind gate
 *   557ca: 6710           beqs   0x557dc               ; kind 0 -> continue accumulating
 *   557cc: 322d 10d0      movew  %a5@(0x10D0),%d1
 *   557d0: 08c1 0006      bset   #6,%d1                 ; else set up-LIMIT flag (bit6)
 *   557d4: 3b41 10d0      movew  %d1,%a5@(0x10D0)
 *   557d8: 6000 0078      braw   0x55852                ; done (limited)
 *   -- 0x557DC..0x557FC : accumulate 8-px sub-row; every 8 px -> stream a new row --
 *   557dc: 0c6d 0000 132c cmpiw  #0,%a5@(0x132C)
 *   557e2: 6708           beqs   0x557ec
 *   557e4: 0c6d 0000 10ca cmpiw  #0,%a5@(0x10CA)        ; strip
 *   557ec: 322d 10b2      movew  %a5@(0x10B2),%d1
 *   557f0: d26d 10d8      addw   %a5@(0x10D8),%d1       ; sub-row += step
 *   557f4: 3b41 10b2      movew  %d1,%a5@(0x10B2)
 *   557f8: 0801 0003      btst   #3,%d1                 ; crossed an 8-px row?
 *   557fc: 6734           beqs   0x55832                ; no -> just wrap the Y scroll value
 *   557fe: 0881 0003      bclr   #3,%d1                 ; yes -> clear the row bit ...
 *   55802: 3b41 10b2      movew  %d1,%a5@(0x10B2)
 *   5580a: 302d 10cc      movew  %a5@(0x10CC),%d0       ; ... compute name-table row base ...
 *   5580e: e948           lslw   #4,%d0                 ;     A5+0x10A0 = 0xC08000 + (0x10CC<<4)+(0x10CA<<2)
 *   55810: 322d 10ca      movew  %a5@(0x10CA),%d1
 *   55814: e549           lslw   #2,%d1
 *   55816: d041           addw   %d1,%d0
 *   55818: 0680 00c08000  addil  #0xC08000,%d0
 *   5581e: 2b40 10a0      movel  %d0,%a5@(0x10A0)
 *   55822: 6100 0124      bsrw   0x55948                ; build the row's tile words
 *   -- 0x55832 : DOWN branch : Y scroll -= step, wrap mod 512, mode=3, stream row down --
 *   55832: 322d 10ae      movew  %a5@(0x10AE),%d1
 *   55836: 926d 10d8      subw   %a5@(0x10D8),%d1       ; Y scroll -= step
 *   5583a: 0241 01ff      andiw  #0x1FF,%d1             ; wrap mod 512
 *   5583e: 3b41 10ae      movew  %d1,%a5@(0x10AE)
 *   55842: 3b7c 0003 13d0 movew  #3,%a5@(0x13D0)        ; direction mode 3 (down)
 *   55848: 343c 0003      movew  #3,%d2
 *   5584c: 4eb9 000406a4  jsr    0x406A4                ; stream one map row (down)
 *   55852: 4e75           rts
 *   -- 0x55854 : UP branch (FUN_00055854) --
 *   55854: 0c6d 0001 020c cmpiw  #1,%a5@(0x020C)        ; mode flag
 *   5585a: 670c           beqs   0x55868
 *   5585c: 302d 10b8      movew  %a5@(0x10B8),%d0
 *   55860: 0c40 0000      cmpiw  #0,%d0
 *   55864: 6c00 0012      bgew   0x55878               ; accumulator >= 0 -> up
 *   55868: 322d 10d0      movew  %a5@(0x10D0),%d1       ; else set bit7 flag + return
 *   5586c: 08c1 0007      bset   #7,%d1
 *   55870: 3b41 10d0      movew  %d1,%a5@(0x10D0)
 *   55874: 6000 002a      braw   0x558a0
 *   55878: 322d 10d8 ...  (0x5587c) subw step from A5+0x10B8
 *   55880: 322d 10ae      movew  %a5@(0x10AE),%d1
 *   55884: d26d 10d8      addw   %a5@(0x10D8),%d1       ; Y scroll += step
 *   55888: 0241 01ff      andiw  #0x1FF,%d1             ; wrap mod 512
 *   5588c: 3b41 10ae      movew  %d1,%a5@(0x10AE)
 *   55890: 3b7c 0002 13d0 movew  #2,%a5@(0x13D0)        ; direction mode 2 (up)
 *   55896: 343c 0002      movew  #2,%d2
 *   5589a: 4eb9 000406a4  jsr    0x406A4                ; stream one map row (up)
 */

extern short A5[];
extern void stream_row_406a4(unsigned short dir);   /* 0x406A4 */
extern void build_row_tiles_55948(void);             /* 0x55948 */

/* 0x55832 : scroll DOWN one step (Y scroll -= step, wrap 512, stream row down). */
static void y_scroll_down(void)
{
    unsigned short v = (unsigned short)A5[0x10AE/2];
    v = (unsigned short)((v - (unsigned short)A5[0x10D8/2]) & 0x1FF);
    A5[0x10AE/2] = (short)v;
    A5[0x13D0/2] = 3;
    stream_row_406a4(3);
}

/* 0x557BA : per-frame vertical scroll dispatcher (accumulate + limit + down). */
void y_scroll_update_557ba(void)
{
    if ((short)A5[0x10B8/2] >= 0xA0) {                 /* upper limit reached */
        if (A5[0x10A8/2] != 0) { A5[0x10D0/2] |= (1 << 6); return; } /* up-limit flag */
    }
    unsigned short acc = (unsigned short)A5[0x10B2/2] + (unsigned short)A5[0x10D8/2];
    A5[0x10B2/2] = (short)acc;
    if (acc & (1 << 3)) {                              /* crossed an 8-px row boundary */
        A5[0x10B2/2] = (short)(acc & ~(1 << 3));
        /* A5+0x10A0 = 0xC08000 + (A5+0x10CC<<4) + (A5+0x10CA<<2); build_row_tiles_55948(); */
        build_row_tiles_55948();
    }
    y_scroll_down();                                   /* falls to 0x55832 */
}

/* 0x55854 : scroll UP branch (Y scroll += step when direction accumulator >= 0). */
void y_scroll_up_55854(void)
{
    if (A5[0x020C/2] != 1 && (short)A5[0x10B8/2] < 0) { A5[0x10D0/2] |= (1 << 7); return; }
    A5[0x10B8/2] -= A5[0x10D8/2];
    unsigned short v = (unsigned short)A5[0x10AE/2];
    v = (unsigned short)((v + (unsigned short)A5[0x10D8/2]) & 0x1FF);
    A5[0x10AE/2] = (short)v;
    A5[0x13D0/2] = 2;
    stream_row_406a4(2);
}
