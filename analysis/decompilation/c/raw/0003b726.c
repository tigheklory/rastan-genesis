/* ORIGINAL ARCADE PC: 0x0003B726 score award (BCD).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * d0 = score increment as a packed BCD word: low byte staged at A5+0x119, high byte at A5+0x11A
 * (A5+0x11B stays 0). A 3-byte BCD chain adds the staged addend A5+0x119..0x11B into the score
 * accumulator A5+0x11C..0x11E (LSB-first: 0x119->0x11C, 0x11A->0x11D, 0x11B->0x11E) using abcd with
 * carry across the three bytes. If the final add carried out (overflow past 999999) the accumulator
 * is clamped to 0x99 0x99 0x99. Then the extra-life threshold at A5+0x306/0x307 is tested (skip if
 * already 0x9999): on crossing it awards a life (0x59EE0 + sfx 5 + A5+0x100/0x102 counters ++) and
 * refreshes the score digits (0x3B802). Guarded by A5+0x34 (rendering active).
 * Callers pass d0 = the dying actor's +0x2C (cfg_2c) = its per-actor score value. */
#include "raw_common.h"
extern void arcade_59ee0(void);
extern void arcade_3a0ec(uint8_t sfx);
extern void arcade_3b802(uint16_t which);
extern uint8_t  g_a5[];               /* A5-relative byte view for the score region */
extern uint16_t g_a5_34;              /* A5+0x34 render-active gate */
extern uint16_t g_life_100, g_life_102, g_a5_2a;

/* one BCD byte add with carry-in, returns carry-out (m68k abcd semantics, decimal). */
static uint8_t bcd_add(uint8_t *acc, uint8_t add, uint8_t cin){
    uint8_t lo = (uint8_t)((*acc & 0x0f) + (add & 0x0f) + cin);
    uint8_t hi = (uint8_t)((*acc >> 4)   + (add >> 4));
    uint8_t cout = 0;
    if (lo > 9){ lo = (uint8_t)(lo + 6); hi++; }
    if (hi > 9){ hi = (uint8_t)(hi + 6); cout = 1; }
    *acc = (uint8_t)(((hi & 0x0f) << 4) | (lo & 0x0f));
    return cout;
}

void arcade_3b726(uint16_t d0){
    if (g_a5_34 == 0) return;                       /* rendering inactive: ignore */
    g_a5[0x119] = (uint8_t)d0;                       /* stage low byte */
    g_a5[0x11a] = (uint8_t)(d0 >> 8);                /* stage high byte (0x11B stays 0) */

    uint8_t carry = 0;
    carry = bcd_add(&g_a5[0x11c], g_a5[0x119], carry);   /* LSB */
    carry = bcd_add(&g_a5[0x11d], g_a5[0x11a], carry);
    carry = bcd_add(&g_a5[0x11e], g_a5[0x11b], carry);   /* MSB */

    if (carry){                                      /* overflow -> clamp 999999 */
        g_a5[0x11c]=0x99; g_a5[0x11d]=0x99; g_a5[0x11e]=0x99;
        return;
    }
    /* extra-life threshold vs A5+0x306/0x307 (skip when already maxed 0x9999) */
    if (g_a5[0x307] > g_a5[0x11e]) { arcade_3b802(g_a5_2a?1:0); return; }
    if (g_a5[0x307] == g_a5[0x11e] && g_a5[0x11d] < g_a5[0x306]) { arcade_3b802(g_a5_2a?1:0); return; }
    if (g_a5[0x306]==0x99 && g_a5[0x307]==0x99) { arcade_3b802(g_a5_2a?1:0); return; }

    arcade_59ee0();                                  /* extra-life bonus setup */
    arcade_3a0ec(5);                                 /* extra-life jingle */
    g_life_100++; g_life_102++;                      /* life counters */
    arcade_3b802(4);
    arcade_3b802(g_a5_2a ? 1 : 0);                   /* refresh score digits */
}
