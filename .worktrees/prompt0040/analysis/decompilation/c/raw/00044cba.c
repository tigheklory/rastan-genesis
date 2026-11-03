/* ORIGINAL ARCADE PC: 0x00044CBA one-axis box overlap primitive (AABB, called per axis).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * a0 = player box (2 signed bytes: near_off, far_off), d1 = player coord on this axis.
 * a1 = enemy hurtbox (2 signed bytes: near_off, far_off), d4 = enemy coord on this axis.
 *   p_near = a0[0]+d1 ; p_far = a0[1]+d1
 *   e_near = a1[0]+d4 ; e_far = a1[1]+d4   (NOTE: arcade adds a1[1] to d4 in place)
 *   overlap(d0=1) unless p_far < e_near OR e_far < p_near.
 * The caller (0x44C76) selects the 4-byte hurtbox entry (index*4) from table 0x44CE0 (or 0x44FA8
 * when +0x38==2), pre-adds 0x80 to all coords, and invokes this for X then Y (0x44CB0 swaps in d2).
 * Hurtbox entry = {x_left, x_right, y_top, y_bottom} as 4 signed bytes. */
#include "raw_common.h"
/* returns 1 on overlap for this axis. a0/a1 advance by 2 (post-inc in the arcade). */
int arcade_44cba(const int8_t *pbox, int16_t pcoord, const int8_t *ebox, int16_t ecoord){
    int16_t p_near = (int16_t)(pbox[0] + pcoord);
    int16_t p_far  = (int16_t)(pbox[1] + pcoord);
    int16_t e_near = (int16_t)(ebox[0] + ecoord);
    int16_t e_far  = (int16_t)(ebox[1] + ecoord);
    if (p_far < e_near) return 0;
    if (e_far < p_near) return 0;
    return 1;
}
