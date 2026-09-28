/* ORIGINAL ARCADE PC: 0x000423B2 (R5) + 0x000423F4 (R6) boss structural-component creators.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Both build the multi-record boss (BODY + structural parts). Each component gets base/anim/comp
 * from the record-type template loader 0x4543E (table 0x45592, indexed by rec_type-8).
 *
 * 0x423B2 (Round 5): five records into the A5+0x5C8 component pool:
 *   for i in 0..4:  +0x21 = i (component index); +0x00 = 1 (active); +0x38 = 1 (compositor sel 1);
 *                   +0x05 = 0x11 (state 0x11 -> handler 0x4684E); +0x06 = 0x11 (rec_type);
 *                   0x4543E -> base 0x0988, anim 0x89 (type 0x11 template). slot += 0x40.
 *   => 5x identical type-0x11 segments (base 0x0988), the R5 boss's structural parts.
 *
 * 0x423F4 (Round 6): four records into the A5+0x648 component pool:
 *   for i in 0..3:  +0x06 = 0x17 + i (types 0x17/0x18/0x19/0x1A); 0x4543E -> per-type base/anim:
 *        type 0x17 base 0x0B35 anim 0x66  (BODY; comp 2, made by the boss trigger path)
 *        type 0x18 base 0x0AED anim 0x82
 *        type 0x19 base 0x0CCB anim 0x7C
 *        type 0x1A base 0x0BEB anim 0x30
 *   => the four structural records that compose the visible dragon.
 *
 * POSITION: 0x4543E does NOT set +0x16/+0x1A. The parts are positioned relative to the body each
 * frame by the boss body-sync 0x42380 (copies body +0x02 facing to each part, then calls the
 * per-part positioner 0x43458 with d0 = 13 + index). The 0x43458 relative-position math is the
 * remaining dependency for an exact offline composite. */
#include "raw_common.h"
extern void arcade_4543e(uint8_t *r);       /* record-type template loader (base/anim/+0x28/+0x2C) */
extern uint8_t *g_pool_5c8;                  /* A5+0x5C8 component pool */
extern uint8_t *g_pool_648;                  /* A5+0x648 component pool */

void arcade_423b2(void){                     /* R5: five type-0x11 segments */
    for (int i=0;i<5;i++){
        uint8_t *r = g_pool_5c8 + 0x40*i;
        B(r,0x21)=(uint8_t)i; B(r,0x00)=1; B(r,0x38)=1; B(r,0x05)=0x11; B(r,0x06)=0x11;
        arcade_4543e(r);
    }
}
void arcade_423f4(void){                     /* R6: four parts types 0x17..0x1A */
    for (int i=0;i<4;i++){
        uint8_t *r = g_pool_648 + 0x40*i;
        B(r,0x06)=(uint8_t)(0x17 + i);
        arcade_4543e(r);
    }
}
