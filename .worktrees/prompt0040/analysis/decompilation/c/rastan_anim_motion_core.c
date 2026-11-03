/* rastan_anim_motion_core.c — CHECKPOINT H8 (animation/motion core; closes H7 technical debt)
 * Semantic reconstruction of the shared animation-frame advance + motion integration core 0x3CEB0
 * and its leaves 0x3CF40 (frame wrap), 0x3CF52 (frame->velocity + axis locks), 0x3CFB0 (band test).
 * NOT original Taito source; byte-faithful control flow lives in raw/0003ceb0.c / 0003cf40.c /
 * 0003cf52.c. The 68000 binary is final authority.
 *
 * POLYMORPHIC FIELD USE IN THE ANIMATED-ACTOR CONTEXT (proven here):
 *   +0x0D (target_char)  = current animation FRAME index (1..56)
 *   +0x0E (field_0e[0])  = sequence frames remaining
 *   +0x0F (field_0e[1])  = frame step (added to the index each advance)
 *   +0x10 (field_0e[2])  = anim subcount reload for even 14-frame bands
 *   +0x11 (field_0e[3])  = anim subcount reload for odd 14-frame bands
 *   +0x13                = axis-lock flags (bit0 lock vy, bit1 lock vx, bit2 band-conditional vx
 *                          lock, bit3 mirror vx->vy)
 *   +0x14 vx  +0x18 vy  +0x16 X  +0x1A Y   +0x08 duration  +0x09 countdown  +0x12 subcount
 * These are the anim-context views of the same bytes that the hunter context (0x41180) uses as a
 * collision-cell address (+0x0E..0x11); do not assign one global meaning.
 */
#include "rastan_arcade_types.h"

extern uint8_t frame_wrap(uint8_t idx);                     /* 0x3CF40: 0->56, 57->1 */
extern void    frame_velocity(uint8_t idx, ActorRecord *a); /* 0x3CF52: idx -> +0x14/+0x18 */

/* +0x12 reload lane: +0x10 (even bands) or +0x11 (odd bands), 14-frame bands from 8. */
static int subcount_hi_band(uint8_t f){
    if (f<8) return 0; if (f<22) return 1; if (f<36) return 0; if (f<50) return 1; return 0;
}

/* 0x3CEB0: advance animation frame + integrate motion. */
void anim_motion_step(ActorRecord *a){
    uint8_t *frame  = &a->target_char;      /* +0x0D */
    uint8_t *seqrem = &a->field_0e[0];       /* +0x0E */
    uint8_t  step   =  a->field_0e[1];       /* +0x0F */

    if (a->init_flag==0){ a->anim_frame_cd=a->anim_frame_dur; a->init_flag=1; goto apply; }
    if (--a->anim_frame_cd != 0) return;                 /* mid-frame: no change */
    a->anim_frame_cd = a->anim_frame_dur;
    if (--a->anim_subcount != 0) goto motion;
    if (--(*seqrem) == 0){ a->init_flag=0; return; }     /* sequence end -> restart next call */
    *frame = frame_wrap((uint8_t)(step + *frame));       /* advance + wrap */
apply:
    frame_velocity(*frame, a);                           /* set +0x14/+0x18 velocity + axis locks */
    a->anim_subcount = subcount_hi_band(*frame) ? a->field_0e[3] : a->field_0e[2];
motion:
    a->x = (uint16_t)(a->x + a->home_x /*+0x14 vx*/);
    a->y = (uint16_t)(a->y + a->home_y /*+0x18 vy*/);
}
