/* ORIGINAL ARCADE PC: 0x0004415A  states 0x1D/0x21. RECONSTRUCTED_FROM_68000.
 * Status: PARTIAL — +0x1A band gate + low-0x13e re-target COMPLETE; the high-0x13e char->char
 * matrix (0x441A2..0x442B8) captured representatively (full matrix in export). */
#include "raw_common.h"
void arcade_4415a(uint8_t *r){
    uint16_t y=W(r,0x1a);
    if (!(y>=472 && y<488)){ if (!arc_40e74(r)) return; }   /* 0x442BA anim tail */
    if (g_prog13e >= 0x2f){ arc_4092e(r); return; }         /* PARTIAL: char matrix at 0x441A2 */
    g_char22b=B(r,0x2f); arc_4103a(r); W(r,0x1e)=0x0224;
    B(r,0x0d)=(uint8_t)(g_char22b!=0 ? 0x52 : 0x4c);
}
