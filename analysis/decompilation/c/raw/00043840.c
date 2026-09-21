/* ORIGINAL ARCADE PC: 0x00043840  state 0x15. Source: maincpu.bin.
 * OWNS base 0x0179 at 0x438B6 (R6 char 'n', 0x13e>=0x80). RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
void arcade_43840(uint8_t *r){
    if (!arc_40e74(r)) goto anim;
    if (g_round==2){ arc_4092e(r); return; }
    if (g_round==5 && B(r,0x0d)==0x61){ arc_4103a(r); W(r,0x1e)=0x0224; B(r,0x0d)=0x4c; return; }
    if (g_round==6 && B(r,0x0d)==0x6e){                 /* 'n' */
        if (g_prog13e < 0x80){ arc_4103a(r); B(r,0x0d)=0x7b; }
        else { arc_4103a(r); B(r,0x0d)=0x48; W(r,0x1e)=0x0179; B(r,0x01)=0x70; return; } /* 0x438B6 */
        B(r,0x38)=2; W(r,0x1e)=0x09ea; B(r,0x01)=0x27; return;
    }
    if (B(r,0x0d)==0x6e){ arc_4103a(r); B(r,0x0d)=0x71; B(r,0x38)=2; W(r,0x1e)=0x09ea; B(r,0x01)=0x27; return; }
    arc_4092e(r); return;
anim:
    if (B(r,0x09)!=0){ B(r,0x09)--; return; }
    B(r,0x01)=0xf6;                                     /* anim -10 */
}
