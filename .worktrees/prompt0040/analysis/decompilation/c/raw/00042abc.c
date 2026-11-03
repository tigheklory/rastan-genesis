/* ORIGINAL ARCADE PC: 0x00042ABC specialized state-0x0F presentation.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source.
 *
 * The record type at +0x06 selects one of three complete phase programs:
 * low types use base 0x019D; type 5 uses base 0x09DC when +0x3D bit 7 is
 * present; the remaining supported types use base 0x0275. Types 10-13, 18,
 * and 28 take the short A8 branch (type 12 also offsets its coordinates).
 * Flying Demon types 8/9 and other supported 0x0275 types take the
 * 0x9D..0xA0 branch. Retirement is the
 * normal record clear at 0x4092E; no child record is allocated here.
 */
#include "raw_common.h"

extern void arcade_4092e(uint8_t *r);

static const uint8_t seq_42bb8[16]={
    0x0b,0x00,0x01,0x02,0x03,0x04,0x05,0x06,
    0x07,0x08,0x09,0x0a,0x03,0x02,0x01,0x00
};

void arcade_42abc(uint8_t *r){
    if(--B(r,0x09)!=0) return;
    B(r,0x38)=0;
    ++B(r,0x08);
    uint8_t type=B(r,0x06);

    if(type==4) goto retire;
    if(type==5){
        if((B(r,0x3d)&0x80)==0) goto retire;
        B(r,0x38)=1; B(r,0x09)=6; W(r,0x1e)=0x09dc;
        if(B(r,0x08)>=16) goto retire;
        B(r,0x01)=(uint8_t)(seq_42bb8[B(r,0x08)]+0xc2);
        return;
    }
    if(type<8){
        B(r,0x09)=4; W(r,0x1e)=0x019d;
        if(B(r,0x08)>=3) goto retire;
        B(r,0x01)=(uint8_t)(B(r,0x08)*2+0x2a+(type==3));
        return;
    }

    B(r,0x09)=4; W(r,0x1e)=0x0275;
    if((type>=10 && type<14) || type==18 || type==28){
        if(type==12){ W(r,0x16)=(uint16_t)(W(r,0x16)-0x16); W(r,0x1a)+=0x0e; }
        /* Original 0x42BD8 performs a second phase increment.  With the
         * lethal initializer's phase 0xFF, bats (types 10/11) display A8 and
         * retire on the following gated update. */
        B(r,0x09)=4;
        if(++B(r,0x08)>=3) goto retire;
        B(r,0x01)=(uint8_t)(B(r,0x08)+0xa7);
        return;
    }
    if(type==22) goto retire;
    if(B(r,0x08)>=4) goto retire;
    B(r,0x01)=(uint8_t)(B(r,0x08)+0x9d);
    return;

retire:
    arcade_4092e(r);
}
