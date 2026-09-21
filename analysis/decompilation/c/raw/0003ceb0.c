/* ORIGINAL ARCADE PC: 0x0003CEB0 shared animation-frame advance + motion integration core.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The engine core behind the ground/airborne actor engines and the 0x42E38 stepper. Per call:
 *   +0x07 init flag: if 0, seed +0x09 = +0x08 (frame duration), set +0x07=1, jump to frame-apply.
 *   else decrement +0x09 (frame countdown); if still nonzero -> rts (no change this frame).
 *   on frame boundary: reload +0x09 = +0x08; decrement +0x12 (anim subcount);
 *       if +0x12 != 0 -> motion step only.
 *       else decrement +0x0E[low] (sequence frames remaining); if it hit 0 -> +0x07=0 (restart) & rts;
 *            else advance frame index +0x0D = wrap(+0x0F step + +0x0D) via 0x3CF40.
 *   frame-apply: 0x3CF52 loads velocity (+0x14 vx / +0x18 vy) from the frame's table entry and the
 *       axis-lock flags (+0x13); then reload +0x12 from +0x10 or +0x11 selected by a +0x0D range test.
 *   motion step: +0x16 (X) += +0x14 (vx); +0x1A (Y) += +0x18 (vy).
 * NOTE: +0x0E low byte here is the animation sequence-remaining counter (the actor is materialized;
 * this is the anim-context view of the polymorphic +0x0E, distinct from the hunter cell-address). */
#include "raw_common.h"
extern uint8_t arcade_3cf40(uint8_t d0);   /* frame-index wrap */
extern void    arcade_3cf52(uint8_t d0, uint8_t *r); /* frame -> velocity + axis locks */

void arcade_3ceb0(uint8_t *r){
    if (B(r,0x07)==0){                       /* first frame */
        B(r,0x09)=B(r,0x08);
        B(r,0x07)=1;
        goto frame_apply;
    }
    if (--B(r,0x09)!=0) return;              /* still counting: no change */
    B(r,0x09)=B(r,0x08);                     /* reload frame countdown */
    if (--B(r,0x12)!=0) goto motion;         /* subcount not exhausted: move only */
    if (--B(r,0x0e)==0){ B(r,0x07)=0; return; } /* sequence ended -> restart next call */
    {   uint8_t nxt = (uint8_t)(B(r,0x0f) + B(r,0x0d));
        B(r,0x0d) = arcade_3cf40(nxt); }     /* advance + wrap frame index */
frame_apply:
    arcade_3cf52(B(r,0x0d), r);              /* set +0x14/+0x18 velocity + axis locks */
    {   /* reload +0x12 from +0x10 (even bands) or +0x11 (odd bands), 14-frame bands starting at 8.
         * Faithful to the subib #8; subib #14 x3 borrow ladder at 0x3CF06..0x3CF1C:
         *   frame<8 ->+0x10 ; [8,22)->+0x11 ; [22,36)->+0x10 ; [36,50)->+0x11 ; >=50 ->+0x10 */
        uint8_t f = B(r,0x0d);
        int use11 = 0;
        if      (f < 8)   use11 = 0;
        else if (f < 22)  use11 = 1;
        else if (f < 36)  use11 = 0;
        else if (f < 50)  use11 = 1;
        else              use11 = 0;
        B(r,0x12) = use11 ? B(r,0x11) : B(r,0x10);
    }
motion:
    W(r,0x16) = (uint16_t)(W(r,0x16) + W(r,0x14));   /* X += vx */
    W(r,0x1a) = (uint16_t)(W(r,0x1a) + W(r,0x18));   /* Y += vy */
}
