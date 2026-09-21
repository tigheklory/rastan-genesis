/* ORIGINAL ARCADE PC: 0x00044082  states 0x18/0x1C. RECONSTRUCTED_FROM_68000. COMPLETE (marker path). */
#include "raw_common.h"
void arcade_44082(uint8_t *r){
    if (!arc_40e74(r)) return;   /* 0x440F8 anim tail */
    uint16_t p=g_prog13e;
    if (B(r,0x05)==0x18){
        if (p<0x18){ arc_4092e(r); return; }
        if (p<0x2f){ if (B(r,0x0d)==0x45){ arc_4092e(r); return; }
            g_char22b=B(r,0x0d); arc_4103a(r); B(r,0x0d)=(uint8_t)(g_char22b-23); W(r,0x1e)=0x0224; return; }
        arc_4103a(r); W(r,0x1e)=0x0224; B(r,0x0d)=0x55; return;
    }
    if (p<0x18){ arc_4092e(r); return; }
    arc_4103a(r); W(r,0x1e)=0x00f4; B(r,0x0d)=0x4f;
}
