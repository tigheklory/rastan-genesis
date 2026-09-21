/* ORIGINAL ARCADE PC: 0x000449B4 ENEMY COLLISION MANAGER (player boxes vs enemy hurtboxes).
 * RECONSTRUCTED_FROM_68000. Status: PARTIAL.
 * Runs once per frame from the top-level actor sequence (0x41F0E) right after the actor-update loop
 * (0x40B66). This is the enemy-hurtbox scan H8 could not find. It makes multiple passes over the
 * A5+0x2C8 enemy pool (29 slots) with different player box categories and records hits into small
 * lists, and triggers the one-hit death reaction.
 *
 * Per pass, per enemy (active +0x00, state +0x05 != 0, NOT hit-flashing +0x3D == 0):
 *   0x446BC  build enemy hurtbox INDEX d3 (by rec_type/family/state)
 *   0x44930/0x44C5A.. overlap test (dispatch by pool index/state) -> d0
 *   on hit (d0!=0), up to 4 per list: record {active=1, type, pal/+0x28, X=+0x16, Y=+0x1A} into
 *       the hit list (A5+0x12A8 body / A5+0x12C8 secondary), then apply the reaction:
 *         0x4498C set hit-type code ; 0x448D8 (family 12 -> score +0x2C + recycle 0x40A1E) ;
 *         0x447CE hit reaction: +0x3D=1 (hit flash) and (rec_type!=7) 0x448B2 -> state 0x0F death
 *         animation + sfx 0x10.  Also steps the death animation via 0x44804.
 * Enemies are effectively ONE-HIT (no HP accumulator): the overlap directly starts the death anim.
 * Pass 4 (0x44BA6+) tests a weapon/projectile box list at A5+0x1338 vs enemies.
 *
 * PARTIAL: the four box-category dispatch arms (0x44C66/0x44C6C/0x44C72/0x44C5A/0x44C60) and the
 * per-pass filters are captured structurally; the exhaustive per-pass predicate ladder and the
 * pass-4 A5+0x1338 producer are not all reproduced line-for-line here (the primitives 0x44CBA and
 * the hurtbox tables ARE complete). */
#include "raw_common.h"
extern uint8_t  arcade_446bc(uint8_t *r);                 /* -> hurtbox index d3 */
extern int      arcade_44930(uint8_t *r, uint8_t *a3);    /* overlap dispatch -> d0 */
extern void     arcade_4498c(uint8_t *r, uint8_t *a3);    /* set hit-type code */
extern void     arcade_448d8(uint8_t *r);                 /* family-12 score+recycle */
extern void     arcade_447ce(uint8_t *r, uint8_t *a3);    /* hit reaction -> state 0x0F */
extern void     arcade_44804(uint8_t *r);                 /* death-anim stepper */
extern uint16_t g_hitcount_21e;                            /* A5+0x21E hits recorded this pass */
extern uint16_t g_idx_214;                                 /* A5+0x214 slot index */
extern uint8_t *g_pool_2c8;                                /* A5+0x2C8 enemy pool */
extern uint8_t *g_hitlist_12a8;                            /* A5+0x12A8 body-hit list (8-byte entries) */

/* Pass 1 (0x449E4): mode==0 enemies vs the player body box; records to A5+0x12A8. */
void arcade_449b4_pass1(void){
    g_hitcount_21e = 0;
    uint8_t *a3 = g_hitlist_12a8;
    for (unsigned i=0;i<29;i++){
        uint8_t *r = g_pool_2c8 + 0x40u*i;
        if (B(r,0x00)==0 || B(r,0x05)==0 || B(r,0x3d)!=0) continue;
        if (B(r,0x03)!=0) continue;                        /* mode!=0 handled in another arm */
        (void)arcade_446bc(r);
        if (!arcade_44930(r, a3)) continue;                /* overlap vs player */
        if (g_hitcount_21e >= 4) continue;                 /* max 4 recorded hits */
        W(a3,0)=1;                                          /* active */
        W(a3,4)=W(r,0x16);                                  /* hit X */
        W(a3,6)=W(r,0x1a);                                  /* hit Y */
        B(a3,2)=1; B(a3,3)=B(r,0x29);                       /* type + palette attr */
        arcade_4498c(r,a3); arcade_448d8(r); arcade_447ce(r,a3);
        g_hitcount_21e++; a3 += 8;
    }
}
