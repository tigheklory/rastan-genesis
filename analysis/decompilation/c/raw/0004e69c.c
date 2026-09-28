/* ORIGINAL ARCADE PC: 0x0004E69C.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The final 0x4E9A2 call computes arena-side globals and does not change x/y. */
#include "raw_common.h"
extern uint16_t arcade_4e976(uint16_t, uint16_t, uint16_t *);
extern void arcade_4e9a2(uint8_t *tail_a4);
static const int16_t right_4eac6[5][2]={{64,-48},{56,-64},{48,-80},{56,-32},{40,-8}};
static const int16_t left_4eada [5][2]={{-64,-48},{-56,-64},{-48,-80},{-56,-32},{-40,-8}};
void arcade_4e69c_position(uint8_t *tail_a4, const uint8_t *primary_10c648,
                           uint16_t boss_state_0272, uint16_t phase_0f42)
{
    if (boss_state_0272 == 0) return;
    B(tail_a4,0x02)=B(primary_10c648,0x02);
    uint16_t anim = 48;
    uint16_t i=arcade_4e976(phase_0f42,9,&anim);
    B(tail_a4,0x01)=(uint8_t)anim;
    const int16_t (*t)[2]=B(tail_a4,0x02)?right_4eac6:left_4eada;
    W(tail_a4,0x16)=(uint16_t)(W(primary_10c648,0x16)+t[i][0]);
    W(tail_a4,0x1a)=(uint16_t)(W(primary_10c648,0x1a)+t[i][1]);
    arcade_4e9a2(tail_a4);
}
