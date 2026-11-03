/* ORIGINAL ARCADE PC: 0x00043AE6  state 0x16. RECONSTRUCTED_FROM_68000. COMPLETE (marker path). */
#include "raw_common.h"
void arcade_43ae6(uint8_t *r){
    if (!arc_40e74(r)) return;   /* 0x43B14 scroll/pos tail uses g_scr200/g_iter214 */
    g_char22b = B(r,0x0d);
    if (B(r,0x0d)==0x60){ arc_4103a(r); W(r,0x1e)=0x00f4; B(r,0x0d)=0x4f; return; }
    arc_4092e(r);
}
