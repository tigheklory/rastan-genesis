/* ORIGINAL ARCADE PC: 0x0004495A  actor -> A5+0x12C8 item/status EVENT-TYPE mapper.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Called by the collision manager 0x449B4 (pass 2/3, 0x44AFE) right after it sets an A5+0x12C8
 * record active (record pointer in a3). It computes the event TYPE word (rec[+2]) from the
 * overlapping actor (a4 in A5+0x02C8 pool):
 *     d0 = 0
 *     if actor +0x06 (rec_type) == 12:
 *         d0 = 1
 *         if actor +0x25 != 0:  d0 = 2
 *         if actor +0x25 != 3:  d0 = 3      (i.e. +0x25==3 keeps d0=2; else d0=3)
 *     rec[+2] = d0
 * So a rec_type-12 pickup actor emits weapon type 1/2/3 (1=FIRE default, +0x25 selects 2 vs 3);
 * any other eligible actor emits type 0 (hit/auxiliary). Producers of item/status types 4..13
 * (energy/life) are NOT this routine and remain the open H18 dependency. */
#include "raw_common.h"

/* rec = A5+0x12C8 event record (a3); actor = A5+0x02C8 pool record (a4). Writes rec[+2]=type. */
void arcade_4495a(uint8_t *rec, const uint8_t *actor){
    uint16_t d0 = 0;
    if (B(actor,0x06)==12){                 /* rec_type 12 = weapon/item pickup */
        d0 = 1;
        if (B(actor,0x25)!=0) d0 = 2;
        if (B(actor,0x25)!=3) d0 = 3;       /* +0x25==3 -> stays 2; else 3 */
    }
    W(rec,0x02) = d0;
}
