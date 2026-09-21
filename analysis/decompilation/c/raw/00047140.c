/* ORIGINAL ARCADE PC: 0x00047140 ground-actor engine (states 3-0C,12). RECONSTRUCTED_FROM_68000. COMPLETE.
 * first frame -> 0x41CFA config; -> 0x3CEB0 shared core; per-family anim. */
#include "raw_common.h"
extern void arc_41cfa(uint8_t*),arc_3ceb0(uint8_t*);
void arcade_47140(uint8_t *r){
    if (B(r,0x07)==0) arc_41cfa(r);
    arc_3ceb0(r);
    uint8_t fam=B(r,0x3e);
    if (fam==0){ uint8_t d0=((W(r,0x0e)&0xff)<2)?4:3; B(r,0x01)=(uint8_t)(d0+23); }
    else if (fam==1){ uint8_t d1=B(r,0x0d),d0=3; if(d1>=14)d0=5; if(d1>=16)d0=4; if(d1>=42)d0=5; if(d1>=44)d0=3;
        if((uint8_t)B(r,0x0e)>=3)d0=6; B(r,0x01)=(uint8_t)(d0+35); }
    else if (fam==2){ uint8_t d0=0; if((uint8_t)B(r,0x0e)<3)d0=1; if((uint8_t)B(r,0x0e)<5)d0=3; B(r,0x01)=(uint8_t)(d0+0x93); }
}
