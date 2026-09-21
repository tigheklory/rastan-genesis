/* ORIGINAL ARCADE PC: 0x00004CD50 (head 0x4CD42) batch/group creator (block 0x748).
 * Callers 0x4D410/0x4DAD2/0x4DFB4. base 0x0D56, state 0x0B, rec_type 0x16. RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
extern uint8_t *blk748_base;
void arcade_4cd50(const uint16_t*a0,const uint16_t*a1,int16_t d0,int16_t d1,int d2){ int made=0;
    uint8_t*a2=blk748_base;
    for(int s=0;s<11 && made<d2;s++,a2+=0x40){ if(B(a2,0x00)!=0) continue;
        B(a2,0x00)=1; W(a2,0x16)=(uint16_t)(*a0++ + d0); W(a2,0x1a)=(uint16_t)(*a0++ + d1);
        W(a2,0x14)=*a1++; W(a2,0x18)=*a1++; B(a2,0x01)=0xed; W(a2,0x1e)=0x0d56; B(a2,0x05)=0x0b;
        B(a2,0x06)=0x16; B(a2,0x08)=2; B(a2,0x07)=1; B(a2,0x09)=1; B(a2,0x12)=0; B(a2,0x38)=1; made++; } }
