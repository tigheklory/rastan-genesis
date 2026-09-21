/* ORIGINAL ARCADE PC: 0x00043F88  state 0x17 (0x13e-banded). RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
void arcade_43f88(uint8_t *r){
    if (!arc_40e74(r)) goto anim;
    if ((uint16_t)g_prog13e < 0x23){
        if (B(r,0x0d)==0x5c){ arc_4092e(r); return; }
        g_char22b=B(r,0x0d); arc_4103a(r);
        uint8_t d0=(uint8_t)(g_char22b+4); if (d0==0x61) d0--;
        B(r,0x0d)=d0; W(r,0x1e)=0x05e9; if (d0==0x5d) W(r,0x1e)=0x0546; return;
    }
    if ((uint16_t)g_prog13e < 0x66){
        g_char22b=B(r,0x0d); arc_4103a(r); B(r,0x0d)=(uint8_t)(g_char22b+9); W(r,0x1e)=0x09ea; return;
    }
    if (B(r,0x0d)==0x59){ arc_4103a(r); B(r,0x0d)=0x55; W(r,0x1e)=0x0224; return; }
    arc_4092e(r); return;
anim:
    if (B(r,0x09)!=0){ B(r,0x09)--; return; }
    B(r,0x01)=0xf0;                                     /* anim -16 */
}
