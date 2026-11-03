/* ORIGINAL ARCADE PC: 0x00043ECC  state 0x1B BURST SPAWNER. RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
void arcade_43ecc(uint8_t *r){
    if (arc_40e74(r)){ arc_4092e(r); return; }
    if (W(r,0x1c)!=0){ W(r,0x1c)--; return; }         /* +0x1C timer */
    if (B(r,0x08)==0){ B(r,0x01)=0x7a; B(r,0x08)=1; }
    if (W(r,0x16) >= 0x150) return;                   /* +0x16 X */
    if ((uint16_t)(W(r,0x16)+20) < g_cam10be) return;
    W(r,0x1c)=0x100; B(r,0x08)=2;
    arc_43f4e(r);                                     /* spawn 5 children (block A5+0x3C8) */
}
