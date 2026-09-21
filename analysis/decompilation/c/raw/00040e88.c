/* ORIGINAL ARCADE PC: 0x00040E88 materialized-actor state 0x1E handler (0x40BAA[0x1E]).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * This is a MARKER-CHAIN transform state: it rechecks the stored +0x0E cell (0x40E74). While the
 * marker char still equals +0x0D it does nothing (stays). When the marker is gone/changed it
 * ADVANCES the chain by progress band (A5+0x13E):
 *   prog<0x18 : 0x4103A consume/re-arm, base +0x1E=0x0F4, retarget +0x0D='O' (0x40E9C)
 *   0x18..0x2E: 0x4092E step, then spawn a 5-part linked object (0x43F52 @ A5+0x308)
 *   prog>=0x2F: 0x4092E step only
 * PROVES 0x40E9C is not a standalone fn: it is the base/retarget tail of this state.  */
#include "raw_common.h"
extern int  arc_40e74(uint8_t *r);      /* d1 = (word[+0x0E]>>8 == +0x0D) ? 0 : 1 */
extern void arc_4103a(uint8_t *r);      /* consume/retire + re-arm as latent hunter */
extern void arc_4092e(uint8_t *r);      /* generic step/retire (H7) */
extern void arcade_43f52(uint8_t *r);   /* linked-part activator */
extern uint16_t g_a5_286; extern uint8_t *g_a5_ptrbase;

void arcade_40e88(uint8_t *r){
    if (arc_40e74(r)==0) return;                 /* 0x40E8A marker still present: stay */
    uint16_t prog = g_prog13e;                   /* 0x40E8E */
    if (prog < 0x18){                            /* 0x40E98..0x40EA2 */
        arc_4103a(r);
        W(r,0x1e)=0x00f4;                        /* base 0x0F4 */
        B(r,0x0d)=0x4f;                          /* retarget char 'O' */
        return;
    }
    if (prog < 0x2f){                            /* 0x40EAA..0x40ED2 */
        arc_4092e(r);
        g_a5_286=5; arcade_43f52(g_a5_ptrbase);  /* 5-part linked object at A5+0x308 */
        return;
    }
    arc_4092e(r);                                /* 0x40ED4 prog>=0x2F: step only */
}
