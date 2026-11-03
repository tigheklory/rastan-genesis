/* ORIGINAL ARCADE PC: 0x0005607C ATTRACT ITEM-DESCRIPTION screen driver (tick + entry + stream wrap).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x5607C/0x560DA/0x56114 and the 0x56032/0x56056
 * entries. The 68000 binary (build/maincpu.disasm.txt) is final authority.
 *
 * This is the attract/frontend "scrolling item-description" screen (attract state
 * A5@(0)=2, A5@(2)=2, A5@(4) in {4,6}). It reuses the SHARED gameplay PC080SN scroll/stream
 * machinery (rastan_world_scroll.c 0x55AB4, rastan_world_stream.c 0x55C4A/0x55C5E/0x55C7A) and the
 * shared text/layout stream writer (raw/000563a6.c, arcade 0x563A6). Only the orchestration below is
 * attract-specific.
 *
 * A5 fields (A5 base arcade 0x10C000 -> Genesis WRAM 0xFF0000):
 *   A5+0x1392 (5010)  free-running phase counter (scroll acts when &3 == 0, i.e. every 4th frame)
 *   A5+0x10AE (4270)  FG scroll X accumulator (held 0 on this screen)
 *   A5+0x10B0 (4272)  FG scroll Y accumulator (held 0)
 *   A5+0x10EE (4334)  BG vertical scroll position (decremented; wraps mod 512)
 *   A5+0x10A0 (4256)  BG row-stream destination cursor (PC080SN C-window addr; wraps in 0xC00000..)
 *   A5+0x141C (5148)  current item sprite-descriptor cursor (end marker for the dwell loop)
 */
#include "raw_common.h"

extern void arcade_563a6(const uint8_t *src, uint32_t dest, uint16_t attr); /* BG text/layout writer */
extern void arcade_55ab4(void);   /* PC080SN scroll commit: A5+0x10EC->0xC40000, 0x10AE->0xC40002, 0x10EE->0xC20000 */
extern void arcade_56114(const uint16_t *recs, uint16_t *objram);           /* copy item-icon sprite records */

/* 0x56032 / 0x56056: screen (re)build entries. Write the item-description BG page into the
 * PC080SN C-window (0x563A6; 0xFF=row, 0=end text/layout stream) and (re)emit the
 * item-icon sprite descriptors (0x56114) to object RAM 0xD00170. Page A dest 0xC00828; page B
 * source ROM 0x0005697E, dest 0xC00028. (Page A's source register is set at 0x5602x, immediately
 * before 0x56032; not captured line-for-line here.) */
void arcade_56032_build_itemdesc_page_a(void){
    arcade_563a6((const uint8_t*)0x0005672A, /*dest*/0x00C00828, /*attr*/0);
    arcade_56114((const uint16_t*)0x00056226, (uint16_t*)0x00D00170);   /* A5+0x141C = returned cursor */
}
void arcade_56056_build_itemdesc_page_b(void){
    arcade_563a6(/*src ROM*/(const uint8_t*)0x0005697E, 0x00C00028, 0);
    arcade_56114((const uint16_t*)0x000562B0, (uint16_t*)0x00D00170);
}

/* 0x5607C: per-frame ATTRACT ITEM-DESCRIPTION tick. */
void arcade_5607c_itemdesc_tick(void){
    if ((A5w(0x1392) & 3) != 0) return;            /* 0x56088: act only every 4th frame */
    A5w(0x10AE) = 0;                               /* FG scroll X = 0 */
    A5w(0x10B0) = 0;                               /* FG scroll Y = 0 */
    uint16_t y = (A5w(0x10EE) - 1) & 0x01FF;       /* BG vertical scroll -= 1, wrap mod 512 */
    A5w(0x10EE) = y;
    if ((y & 7) == 0) arcade_560da_stream_row();   /* 0x560A6: every 8 scroll units, advance a row */
    arcade_55ab4();                                /* 0x560AA: commit scroll to PC080SN registers */
    /* 0x560B0: per-item dwell timer walk over the 8-byte sprite descriptors up to the live cursor */
    uint8_t *a0 = (uint8_t*)0x00D00170;
    uint8_t *end = (uint8_t*)A5l(0x141C);
    while (a0 != end){
        uint16_t t = (W(a0,2) - 1);
        W(a0,2) = t;                               /* dwell countdown */
        if (t == 16) W(a0,4) = 0;                  /* at 16, clear field +4 (item transition flag) */
        a0 += 8;
    }
}

/* 0x560DA: advance the BG row-stream cursor by one row-region, blanking it; at the wrap boundary
 * 0xC00F00 re-emit the page (0x56056). Cursor wraps within the BG C-window (&0xC03F00). */
void arcade_560da_stream_row(void){
    uint8_t *a0 = (uint8_t*)A5l(0x10A0);
    if (a0 == (uint8_t*)0x00C00F00) arcade_56056_build_itemdesc_page_b();  /* loop wrap: rebuild page */
    uint32_t *p = (uint32_t*)A5l(0x10A0);
    for (int i = 0; i < 50; i++) *p++ = 0x00000020;    /* blank 50 longs (= 100 blank cells) */
    uint32_t c = ((uint32_t)(uintptr_t)p + 0x100) & 0x00C03F00;  /* +256, wrap in BG C-window */
    A5l(0x10A0) = c;
}

/* 0x56114: copy item-icon PC090OJ sprite descriptor records (4 words each) to object RAM until
 * the first word is 0xFFFF. Returns the advanced object-RAM pointer in A5+0x141C (set by caller). */
void arcade_56114(const uint16_t *recs, uint16_t *objram){
    while (*recs != 0xFFFF){
        objram[0]=recs[0]; objram[1]=recs[1]; objram[2]=recs[2]; objram[3]=recs[3];
        recs += 4; objram += 4;
    }
}
