/* ORIGINAL ARCADE PC: 0x000473B8 airborne-actor engine (states 1,2,0D,0E). RECONSTRUCTED_FROM_68000.
 * Status: PARTIAL (setup + shared-core call proven; per-state anim tail 0x47414+ summarized). */
#include "raw_common.h"
extern void arc_41cfa(uint8_t*),arc_3ceb0(uint8_t*),arc_4734a(uint8_t*);
void arcade_473b8(uint8_t *r){
    if (B(r,0x07)==0){ arc_41cfa(r);
        if (B(r,0x3e)==1){ B(r,0x08)=4; arc_4734a(r); B(r,0x0a)=8; }
        else if (B(r,0x3e)==0x0a){ B(r,0x08)=(B(r,0x2e)!=0)?2:7; arc_4734a(r); }
        else arc_4734a(r); }
    arc_3ceb0(r);                 /* SAME core as 0x47140 */
    B(r,0x20)&=(uint8_t)~0x01;    /* bclr #0,+0x20 ; per-state anim tail follows */
}
