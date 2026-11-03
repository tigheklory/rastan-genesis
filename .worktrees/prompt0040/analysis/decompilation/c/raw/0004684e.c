/* ORIGINAL ARCADE PC: 0x0004684E state 0x11 boss component. RECONSTRUCTED_FROM_68000. COMPLETE (head/anim). */
#include "raw_common.h"
extern void arc_41cfa(uint8_t*),arc_3ceb0(uint8_t*),arc_468d0(uint8_t*);
static const uint8_t t468c8[4]={0x09,0x0d,0x0d,0x0c};
void arcade_4684e(uint8_t *r){
    if (B(r,0x3e)!=2 && B(r,0x3e)!=8) return;
    if (B(r,0x07)==0){ arc_41cfa(r); arc_468d0(r); }
    arc_3ceb0(r);
    if (B(r,0x3e)==2){ uint8_t d0=2; if((uint8_t)B(r,0x0e)<23)d0=3; if((uint8_t)B(r,0x0e)<3)d0=1; B(r,0x01)=(uint8_t)(0x93+d0); }
    else { if(B(r,0x01)==0x59) W(r,0x22)=0x3a; B(r,0x01)=(uint8_t)(0x4d+t468c8[(uint8_t)B(r,0x0e)>>2]); }
}
