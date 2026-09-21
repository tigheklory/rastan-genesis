/* ORIGINAL ARCADE PC: 0x000447CE enemy hit reaction (one-hit kill) + 0x448D8 score/recycle.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * 0x447CE: called when the collision manager records a hit on an enemy.
 *   rec_type (+0x06) 10/11/18  -> 0x447B6: freeze (copy camera to +0x32/+0x30, +0x0C=-1, +0x07=0)
 *   else (pool index < 18): clear the hit-list type byte a3@(2), set +0x3D=1 (hit-flash), and unless
 *        rec_type==7 run 0x448B2 -> state 0x0F death/impact animation + sfx 0x10.
 * There is NO HP field for ordinary enemies: the recorded overlap directly starts the death anim.
 * 0x448D8: for family (+0x3E)==12 actors, award score (0x3B726, value +0x2C) and recycle (0x40A1E)
 *   immediately (these do not run the state-0x0F death animation). */
#include "raw_common.h"
extern void arcade_448b2(uint8_t *r);   /* -> state 0x0F death anim + sfx 0x10 */
extern void arcade_3b726(uint16_t v);   /* score award */
extern void arcade_40a1e(uint8_t *r);   /* schedule-preserving recycle/retire */
extern uint16_t g_cam_x_10be, g_cam_y_10c0, g_idx_214;

/* 0x447B6: freeze reaction for rec_type 10/11/18. */
static void freeze_447b6(uint8_t *r){
    W(r,0x32)=g_cam_x_10be; W(r,0x30)=g_cam_y_10c0;
    B(r,0x0c)=0xff; B(r,0x07)=0;
}

void arcade_447ce(uint8_t *r, uint8_t *a3){
    uint8_t rt = B(r,0x06);
    if (rt==10 || rt==11 || rt==18){ freeze_447b6(r); return; }
    if (g_idx_214 >= 18) return;                 /* pool-index gate (0x447E4) */
    B(a3,2)=0;                                    /* clear hit-list type */
    B(r,0x3d)=1;                                  /* hit-flash flag */
    if (rt!=7) arcade_448b2(r);                   /* -> state 0x0F death anim + sfx 0x10 */
}

void arcade_448d8(uint8_t *r){
    if (B(r,0x3e)==12){                           /* family 12 */
        arcade_3b726(W(r,0x2c));                  /* score = +0x2C */
        arcade_40a1e(r);                          /* recycle */
    }
}
