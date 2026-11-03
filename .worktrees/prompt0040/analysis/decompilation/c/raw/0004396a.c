/* ORIGINAL ARCADE PC: 0x0004396A  state 0x19 JUMPING attacker. RECONSTRUCTED_FROM_68000.
 * Status: PARTIAL — marker re-target COMPLETE; jump-arc tail (0x439CC: +0x18 vertical, +0x1C
 * timer, 0x41F9C, anim 0x8A->0x87->0x8B->0x8D, sound 0x12) faithfully summarized, not exhaustive. */
#include "raw_common.h"
void arcade_4396a(uint8_t *r){
    if (arc_40e74(r)){
        g_char22b=B(r,0x0d); arc_4103a(r);
        if (g_round==1){ W(r,0x1e)=0x0235;
            uint8_t d0=(uint8_t)g_char22b,d1=0; if (d0!=0x4b) d1=(uint8_t)(d0-86);
            B(r,0x2f)=d1; B(r,0x0d)=0x45; }
        else { W(r,0x1e)=0x09f6; B(r,0x0d)=(uint8_t)(0x65+(g_char22b==0x4b?0:1)); B(r,0x38)=2; }
        return;
    }
    arc_41f9c_arc(r);   /* PARTIAL: jump arc (0x439CC..0x43ACC) */
}
