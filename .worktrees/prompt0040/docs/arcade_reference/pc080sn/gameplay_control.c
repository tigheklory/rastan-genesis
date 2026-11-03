/*
 * Rastan arcade PC080SN — gameplay control / ring logic (documentation reconstruction).
 * Reconstructed from original 68000 opcodes; opcodes authoritative. a5 = 0x10C000.
 * Publishes tilemap1 @ 0xC08000 via 0x055948 (see core_publishers.c). Field roles in state_fields.md.
 *
 * MODEL: the map is a byte stream. Each map byte is a SELECTOR/DIRECTION (a5@0x10A8),
 * loaded by pc080sn_advance_map_group() from *(a5@0x10C6). A per-direction dispatcher
 * accumulates the camera step, and on each 8px tile-boundary crossing computes a ring
 * destination in 0xC08000 and calls 0x055948 to publish one 16-cell strip.
 * Ring counters: a5@0x10CA (col 0..3) and a5@0x10CC (group 0..15) -> 64 positions.
 */

/*
 * Arcade PC: 0x0556A6  (selector==1 branch of the direction dispatcher)
 * Vertical direction A. If not the active selector, latch pending bit5 and skip.
 */
static void pc080sn_dir_sel1_vertical(void)
{
    if (a5_w(0x10A8) != 1) { a5_w(0x10D0) |= (1<<5); return; }          /* not active -> defer */
    u16 acc = a5_w(0x10B4) + a5_w(0x10DA);  a5_w(0x10B4) = acc;         /* accumulate vertical step */
    if (acc & 0x08) {                                                   /* crossed an 8px tile boundary */
        a5_w(0x10B4) = acc & ~0x08;
        /* ring dest = 0xC08000 + (0x3F00 - (group<<10 | col<<8)) */
        u16 off = 0x3F00 - (((a5_w(0x10CC) << 8) << 2) + (a5_w(0x10CA) << 8));
        a5_l(0x10A4) = 0xC08000 + off;
        pc080sn_publish_dispatch();                                     /* 0x055948 -> strip_B/cells */
    }
    a5_w(0x10B0) = (a5_w(0x10B0) + a5_w(0x10DA)) & 0x1FF;               /* layer scroll accum -> 0xC20002 */
    a5_w(0x13D0) = 0;  call_0x406a4(/*d2=*/0);
}

/*
 * Arcade PC: 0x055738  (selector==2 branch)
 * Vertical direction B (opposite ring offset + opposite scroll sign).
 */
static void pc080sn_dir_sel2_vertical(void)
{
    if (a5_w(0x10A8) != 2) { a5_w(0x10D0) |= (1<<4); return; }
    u16 acc = a5_w(0x10B6) + a5_w(0x10DA);  a5_w(0x10B6) = acc;
    if (acc & 0x08) {
        a5_w(0x10B6) = acc & ~0x08;
        u16 off = ((a5_w(0x10CC) << 8) << 2) + (a5_w(0x10CA) << 8);     /* group<<10 | col<<8 */
        a5_l(0x10A4) = 0xC08000 + off;
        pc080sn_publish_dispatch();
    }
    a5_w(0x10B0) = (a5_w(0x10B0) - a5_w(0x10DA)) & 0x1FF;
    a5_w(0x13D0) = 1;  call_0x406a4(/*d2=*/1);
}

/*
 * Arcade PC: 0x0557C4 / 0x0557DC / 0x055808  (selector==0 branch)
 * Horizontal direction. Note the small stride (group<<4 | col<<2) vs the vertical (<<10/<<8).
 */
static void pc080sn_dir_sel0_horizontal(void)
{
    if (a5_w(0x10A8) != 0) { a5_w(0x10D0) |= (1<<6); return; }
    if (a5_w(0x132C) == 0) { /* 0x0557DC: gate on PREVIOUS selector==0; 0x0557E4 reads a5@0x10CA (nop) */ }
    u16 acc = a5_w(0x10B2) + a5_w(0x10D8);  a5_w(0x10B2) = acc;
    if (acc & 0x08) {
        a5_w(0x10B2) = acc & ~0x08;
        u16 off = (a5_w(0x10CC) << 4) + (a5_w(0x10CA) << 2);            /* group<<4 | col<<2 */
        a5_l(0x10A0) = 0xC08000 + off;
        pc080sn_publish_dispatch();
    }
    a5_w(0x10AE) = (a5_w(0x10AE) - a5_w(0x10D8)) & 0x1FF;               /* layer scroll accum -> 0xC40002 */
    a5_w(0x13D0) = 3;  call_0x406a4(/*d2=*/3);
    /* 0x055854+: a 4th-direction path (uses a5@0x10B8, latches pending bit7) follows. */
}

/*
 * Arcade PC: 0x0558A2  — post-publication advance (called by 0x055948 after each publish).
 * a5@0x10CA counts 0..3 (one descriptor group). Every 4 -> advance source + rebuild descriptors,
 * bump the group index. Every 16 groups -> wrap, advance the map pointer, load the next selector.
 */
static void pc080sn_post_advance(void)
{
    if (a5_w(0x10CA) != 4) return;
    pc080sn_advance_source_ptrs();   /* 0x558C6: +4 to each 0x10D000 base ptr; a5@0x10CA = 0 */
    pc080sn_descriptor_rebuild();    /* 0x055904 */
    a5_w(0x10CC) += 1;
    if (a5_w(0x10CC) != 16) return;
    pc080sn_advance_map_group();     /* 0x558E0 */
}

/*
 * Arcade PC: 0x0558C6
 */
static void pc080sn_advance_source_ptrs(void)
{
    u32 *base = (u32 *)0x10D000;                 /* 16 base pointers */
    for (int i = 16; i != 0; i--) { *base += 4; base += 1; }
    a5_w(0x10CA) = 0;
}

/*
 * Arcade PC: 0x0558E0  — group wrap + next map command.
 */
static void pc080sn_advance_map_group(void)
{
    a5_w(0x10CC) = 0;
    a5_l(0x10C6) += 1;                           /* 0x0558E4: advance map-stream pointer +1 byte */
    a5_w(0x132C) = a5_w(0x10A8);                 /* 0x0558EC: save PREVIOUS selector (before overwrite) */
    a5_w(0x10A8) = *(u8 *)a5_l(0x10C6);          /* 0x0558F8: NEXT SELECTOR from map stream */
    a5_w(0x13E) += 1;                            /* 0x0558FE: segment index++ (see map_stream_format.md) */
}

/*
 * Arcade PC: 0x055904  — rebuild the descriptor-pointer and source-word tables.
 * For each of 16 base pointers at 0x10D000: source word = *(base), descriptor ptr = *(base+2).
 */
static void pc080sn_descriptor_rebuild(void)
{
    u32 *base = (u32 *)0x10D000;                 /* base-pointer array */
    u32 *dptr = (u32 *)0x10D040;                 /* descriptor-pointer table (publisher a3) */
    u16 *src  = (u16 *)0x10D080;                 /* source-word table (publisher a1) */
    for (int i = 16; i != 0; i--) {
        u16 *b = (u16 *)*base;
        *src++ = b[0];                           /* source/control word */
        *dptr++ = (u32)(u16)b[1];                /* descriptor address (zero-extended word) */
        base += 1;
    }
}

/*
 * Arcade PC: 0x055AB4  — scroll-register publication (write-only).
 */
static void pc080sn_commit_scroll(void)
{
    *(u16 *)0xC20000 = a5_w(0x10EE);   /* tilemap0 Y-scroll */
    *(u16 *)0xC40000 = a5_w(0x10EC);   /* tilemap0 X-scroll (half-rate parallax) */
    *(u16 *)0xC20002 = a5_w(0x10B0);   /* tilemap1 Y-scroll (vertical accum) */
    *(u16 *)0xC40002 = a5_w(0x10AE);   /* tilemap1 X-scroll (horizontal accum) */
}
