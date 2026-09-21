/* ORIGINAL ARCADE PC: 0x00043B32  state 0x1A MASTER 0x13e-banded chain dispatcher (largest).
 * Status: PARTIAL. The full 0x13e-range branch matrix (0x43B4E..0x43E8C) re-targets +0x0D and
 * rewrites +0x1E among {0x0224,0x0266,0x00F4,0x09EA,0x01FC,0x0236,0x0546} per 0x13e band and
 * current char; sound 0x25 at char 'U'; anim tail 0x43E8E uses +0x0D + g_scr200. The exhaustive
 * band table is preserved in the Ghidra export snapshot; this reconstruction captures the shape. */
#include "raw_common.h"
void arcade_43b32(uint8_t *r){
    /* edge guard on self-flag +0x742/+0x744 (0x43B4E..0x43BAE) elided in this PARTIAL form */
    if (!arc_40e74(r)) goto anim;
    g_char22b = B(r,0x0d);
    if (B(r,0x0d) < 0x53){ arc_4092e(r); return; }   /* below-'S' chars: plain update */
    /* >= 'S': 0x13e-banded re-target matrix -> base in the pool above (see export) */
    arc_4103a(r); W(r,0x1e)=0x0224;                  /* representative default re-base */
    return;
anim:
    /* 0x43E8E: anim = base + (g_scr200&12)>>2 keyed on +0x0D bands */
    B(r,0x01) = (uint8_t)(0x07 + ((g_scr200 & 0x0c) >> 2));
}
