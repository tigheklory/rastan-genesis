/* ORIGINAL ARCADE PC: 0x0004375C  states 0x13/0x14. Source: maincpu.bin.
 * Reconstruction: 68000 static decompilation. Provenance: RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
void arcade_4375c(uint8_t *r){
    if (g_prog13e==0x29 && g_round==2){ if (g_scr10cc>=13) goto anim; goto retgt3; }
    if (!arc_40e74(r)) goto anim;
    if (g_round==3 && B(r,0x0d)==0x65){ /* 'e' */
retgt3: arc_4103a(r); B(r,0x0d)=0x69; W(r,0x1e)=0x0224; B(r,0x01)=7; B(r,0x38)=2; return; }
    arc_4092e(r); return;
anim:
    if (B(r,0x09)!=0){ B(r,0x09)--; return; }        /* +0x09 wait */
    /* +0x08 phase machine, anim = 0x29+phase (helper 0x4382E) */
    arc_4382e(r);
}
