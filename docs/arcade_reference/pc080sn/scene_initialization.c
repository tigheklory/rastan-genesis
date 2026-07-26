/*
 * Rastan arcade PC080SN — scene initialization + tilemap0 producers (documentation reconstruction).
 * Reconstructed from original 68000 opcodes; opcodes authoritative. a5 = 0x10C000.
 * Neutral names: tilemap0 @ 0xC00000, tilemap1 @ 0xC08000. Fields in state_fields.md.
 *
 * MODEL: at scene setup a 64-iteration loop (0x0503E4) fills BOTH tilemaps by calling the
 * gameplay publisher 0x055948 (tilemap1) and the tilemap0 publisher 0x55C4A once per column.
 * After init, only tilemap1 streams per-frame (gameplay_control.c); tilemap0 is not driven by
 * the gameplay triggers (its layer scroll stays static in MAME).
 */

/*
 * Arcade PC: 0x0503E4  — scene fill loop (populate both tilemaps, 64 columns).
 * Selector (a5@0x10A8, from the map) chooses the cursor layout; the loop counter is a5@0x10AA=64.
 */
static void pc080sn_scene_fill(void)
{
    if (a5_w(0x10A8) != 1) {                    /* 0x0503EC */
        a5_l(0x10A0) = 0xC08000;                /* tilemap1 cursor A */
        a5_l(0x10F8) = 0xC00000;                /* tilemap0 cursor */
        a5_l(0x10A4) = 0xC08000;                /* tilemap1 cursor B */
    } else {                                    /* 0x05040C (selector==1) */
        a5_l(0x10F8) = 0xC00000;
        a5_l(0x10A0) = 0xC08000;
        a5_l(0x10A4) = 0xC04000;                /* NB uses the 0xC04000 quadrant */
    }
    a5_w(0x10AA) = 64;                           /* 0x05042C loop counter */
    do {
        pc080sn_publish_dispatch();             /* 0x055948  -> tilemap1 strip */
        pc080sn_tilemap0_publish_col();         /* 0x55C4A   -> tilemap0 strip */
        if (a5_w(0x10A8) != 1) {                /* 0x05043C */
            a5_l(0x10A0) -= 0x3FFC;             /* advance to prev column (−16380) */
            a5_l(0x10F8) -= 0x3FFC;
        } else {
            a5_l(0x10A4) -= 256;
            a5_l(0x10F8) -= 0x3FFC;
        }
    } while (--a5_w(0x10AA) != 0);               /* 0x050472..0x050480 : 64 columns */
}

/*
 * Arcade PC: 0x55C4A  — publish one tilemap0 column (parallel to 0x055968). NO collision.
 * Also reached from 0x055B8E (activation during gameplay not proven; see tilemap0_producers.md).
 */
static void pc080sn_tilemap0_publish_col(void)
{
    a5_l(0x1126) = a5_l(0x10FC);                 /* 0x055C4A/4E */
    pc080sn_tilemap0_strip();                    /* 0x55C5E */
    a5_w(0x10F6) += 1;                           /* tilemap0 column index */
    pc080sn_tilemap0_post();                     /* 0x55BEC */
}

/*
 * Arcade PC: 0x55C5E  — walk 16 descriptors into tilemap0. cursor a5@0x10F8; tables 0x10D100/0x10D104.
 */
static void pc080sn_tilemap0_strip(void)
{
    u16 *a0 = (u16 *) a5_l(0x10F8);              /* tilemap0 cursor (0xC00xxx) */
    u16 *a1 = (u16 *) 0x10D104;                  /* source words */
    u32 *a3 = (u32 *) 0x10D100;                  /* descriptor-pointer table */
    /* (loop count per strip mirrors the 16-descriptor structure; each descriptor -> 0x55C7A) */
    u16 *a2 = (u16 *) *a3;
    pc080sn_tilemap0_cells(&a0, a1, a2);         /* 0x55C7A */
    a5_l(0x10F8) = (u32) a0;                     /* save cursor */
}

/*
 * Arcade PC: 0x55C7A  — tilemap0 cell producer. 64 sub-cells, NO collision, +256/sub-cell.
 * word0 = *(a1) (source/control word), word1 = descriptor tile (offset d2*32 + a5@0x10F6*2).
 */
static void pc080sn_tilemap0_cells(u16 **pa0, const u16 *a1, const u16 *a2)
{
    u16 *a0 = *pa0;
    for (int d2 = 0; d2 < 64; d2++) {            /* cmpiw #64 (vs tilemap1's #4) */
        *a0++ = *a1;                             /* word0 = source ; a0 += 2 (post-inc) */
        *a0 = *(u16 *)((u8 *)a2 + (d2 << 5) + (a5_w(0x10F6) << 1));  /* word1 = tile */
        a0 = (u16 *)((u8 *)a0 + 254);            /* +256 total */
    }
    *pa0 = a0;
}

/*
 * Arcade PC: 0x0561B6  — C-window clear: fill BOTH tilemaps with tile 0x0020 (word1) / 0x0000 (word0).
 * 4096 longs each ( = one 0x4000 quadrant per map). Proves 0x0020 is the blank/base tile.
 */
static void pc080sn_cwindow_clear(void)
{
    u32 *a0 = (u32 *) 0xC08000;                  /* tilemap1 */
    u32 *a1 = (u32 *) 0xC00000;                  /* tilemap0 */
    for (int d1 = 4096; d1 != 0; d1--) {
        *a0++ = 0x00000020;                      /* word0=0x0000, word1=0x0020 */
        *a1++ = 0x00000020;
    }
}

/*
 * Arcade PC: 0x05127C / 0x05274C  — selector 4/5/6 handling (NOT PC080SN publication).
 * 4/5/6 are non-streaming map commands consumed by scene/event logic:
 *  - 0x05127C: value 4 -> if a5@0x11DE < 216 set event flags; value 5 -> if a5@0x11DE < 80 set flags.
 *  - 0x05274C: value 4/5/6 -> 0x527CC sets a5@0x10E8 = 7, then continues (no tilemap write).
 * The gameplay direction dispatcher (0x0556A6) matches only 0/1/2, so a 4/5/6 selector publishes
 * NOTHING (all pending bits set, no direction guard matches).
 */
