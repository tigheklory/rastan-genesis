/*
 * Rastan arcade PC080SN — gameplay publication core (documentation reconstruction).
 * Reconstructed from the original 68000 opcodes; the opcodes remain authoritative.
 * Not original Taito source. a5 = 0x10C000. Neutral tilemap names (ownership: tilemap1_0xC08000).
 * See core_publishers_assembly.md for register/mask/increment facts this C obscures.
 */

/* A5-relative fields used here (absolute = 0x10C000 + offset):
 *   a5@0x10A0 (4256)  cursor for strip_A  (set 0xC08000-based by horizontal trigger 0x055808)
 *   a5@0x10A4 (4260)  cursor for strip_B  (set 0xC08000-based by vertical trigger 0x0556E0)
 *   a5@0x10A8 (4264)  selector (observed values 0,1,2,4,5,6; ==0 picks strip_A)
 *   a5@0x10CA (4298)  column sub-index (advanced each publish; used in descriptor offset)
 *   a5@0x1330 (4912)  set to 1 by cell_dir_aware
 * Tables: 0x10D1C0 = descriptor-pointer table (16 longs); 0x10D200 = per-cell source words.
 * Collision WRAM base 0x10DE00; name-RAM base of this layer 0xC08000. */

/*
 * Arcade PC: 0x055948
 */
static void pc080sn_publish_dispatch(void)
{
    if (a5_w(0x10A8) == 0) pc080sn_publish_strip_A();   /* 0x055968 */
    else                   pc080sn_publish_strip_B();   /* 0x055990 */
    a5_w(0x10CA) += 1;                                  /* both branches */
    pc080sn_post_advance();                             /* 0x558A2 (descriptor advance; next checkpoint) */
}

/*
 * Arcade PC: 0x055968  — strip_A (forward). Writes tilemap1_0xC08000; saves cursor.
 */
static void pc080sn_publish_strip_A(void)
{
    u16 *a0 = (u16 *) a5_l(0x10A0);         /* dest cursor into 0xC08xxx */
    u16 *a1 = (u16 *) 0x10D200;             /* per-cell source words */
    u32 *a3 = (u32 *) 0x10D1C0;             /* descriptor-pointer table */
    for (int d1 = 16; d1 != 0; d1--) {
        u16 *a2 = (u16 *) *a3;              /* descriptor for this cell */
        pc080sn_cell_forward(&a0, a1, a2);  /* 0x0559B2 ; advances a0 */
        a5_l(0x10A0) = (u32) a0;            /* strip_A saves updated cursor */
        a3 += 1;                            /* += 4 bytes */
        a1 += 1;                            /* += 2 bytes */
    }
}

/*
 * Arcade PC: 0x055990  — strip_B (direction-aware). Writes tilemap1_0xC08000; cursor NOT saved.
 */
static void pc080sn_publish_strip_B(void)
{
    u16 *a0 = (u16 *) a5_l(0x10A4);         /* dest cursor into 0xC08xxx */
    u16 *a1 = (u16 *) 0x10D200;
    u32 *a3 = (u32 *) 0x10D1C0;
    for (int d1 = 16; d1 != 0; d1--) {
        u16 *a2 = (u16 *) *a3;
        pc080sn_cell_dir_aware(&a0, a1, a2);/* 0x055A14 ; advances a0 */
        a3 += 1;
        a1 += 1;
        /* note: a5@0x10A4 is not written back inside the loop */
    }
}

/*
 * Arcade PC: 0x0559B2  — one cell (4 sub-cells), forward orientation.
 * Cell word layout at the dest: word0(even)=*(a1) [attr; runtime shows 0x0003],
 *                               word1(odd) =desc-tile.  Parallel collision word per sub-cell.
 */
static void pc080sn_cell_forward(u16 **pa0, const u16 *a1, const u16 *a2)
{
    u16 *a0 = *pa0;
    for (int d2 = 0; d2 < 4; d2++) {
        *a0 = *a1;                                      /* word0 = source (attr) */
        u16 cw;                                         /* collision word */
        if (a2[16] /*+32*/ == 255) cw = a2[17] /*+34*/;
        else cw = *(u16 *)((u8 *)a2 + 20 + (a5_w(0x10CA) << 1) + (d2 << 3));
        *(u16 *)(0x10DE00 + (((u32)a0 - 0xC08000) >> 1)) = cw;   /* collision */
        a0 = (u16 *)((u8 *)a0 + 2);
        *a0 = *(u16 *)((u8 *)a2 + 0 + (a5_w(0x10CA) << 1) + (d2 << 3));  /* word1 = tile */
        a0 = (u16 *)((u8 *)a0 + 254);                   /* +256 total per sub-cell */
    }
    *pa0 = a0;
}

/*
 * Arcade PC: 0x055A14  — one cell, direction-aware. Reverses the sub-index when a5@0x10A8 != 2.
 * Produces the same collision plus a second, wrapped collision marker.
 */
static void pc080sn_cell_dir_aware(u16 **pa0, const u16 *a1, const u16 *a2)
{
    a5_w(0x1330) = 1;                                   /* 0x055A14 side flag */
    u16 *a0 = *pa0;
    for (int d2 = 0; d2 < 4; d2++) {
        *a0 = *a1;                                      /* word0 = source */
        u16 sub = a5_w(0x10CA);
        if (a5_w(0x10A8) != 2) sub = (~sub) & 3;        /* notw ; andi #3  (direction reversal) */
        u16 cw;
        if (a2[16] == 255) cw = a2[17];
        else cw = *(u16 *)((u8 *)a2 + 20 + (sub << 3) + (d2 << 1));   /* NB reversed field order vs 0x0559B2 */
        *(u16 *)(0x10DE00 + (((u32)a0 - 0xC08000) >> 1)) = cw;        /* collision #1 */
        /* collision #2: wrapped marker '1' one row (256 bytes) back, masked to 0x3FFF */
        *(u16 *)(0x10DE00 + (((((u32)a0 - 0xC08000) - 256) & 0x3FFF) >> 1)) = 1;
        a0 = (u16 *)((u8 *)a0 + 2);
        *a0 = *(u16 *)((u8 *)a2 + 0 + (sub << 3) + (d2 << 1));        /* word1 = tile */
        a0 = (u16 *)((u8 *)a0 + 254);
    }
    *pa0 = a0;
}
