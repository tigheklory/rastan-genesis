/* ORIGINAL ARCADE PC: 0x00043636  state 0x22. RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
void arcade_43636(uint8_t *r){
    if (arc_40e74(r)){
        if (g_round==3){
            if (B(r,0x0d)==0x73){ arc_4103a(r); W(r,0x1e)=0x00f4; B(r,0x0d)=0x4f; B(r,0x30)=1; arc_41bee(r); return; }
            if (B(r,0x0d)==0x74){ arc_4103a(r); W(r,0x1e)=0x0266; B(r,0x0d)=0x44; B(r,0x30)=1; return; }
            arc_4103a(r); W(r,0x1e)=0x0266; B(r,0x0d)=0x46; B(r,0x30)=1; return;
        }
        if (g_round==5 && B(r,0x0d)==0x73){
            arc_4103a(r); W(r,0x1e)=0x0224; B(r,0x01)=7; B(r,0x0d)=0x67; B(r,0x30)=2; B(r,0x38)=2; return; }
        arc_4092e(r); return;
    }
    if (B(r,0x09)!=0){ B(r,0x09)--; return; }         /* 0x436E0 anim machine */
}
