/* ORIGINAL ARCADE PC: 0x0004A086 field-schedule installer. RECONSTRUCTED_FROM_68000. COMPLETE.
 * NOT written (rely on prior clear): +0x05 state(=0), +0x03 mode(=0), +0x0D, +0x16, +0x02. */
#include "raw_common.h"
extern void arcade_4544e(uint8_t*,uint8_t); extern void arcade_45684(uint8_t*,uint8_t,int);
void arcade_4a086(uint8_t *r, const uint8_t e[8]){
    B(r,0x04)=e[0]; B(r,0x3e)=e[1]; uint8_t b2=e[2]; B(r,0x38)=b2&0x0f; uint8_t var=b2>>4; B(r,0x36)=e[3];
    uint16_t w=(uint16_t)((e[4]<<8)|e[5]); if(w&1) B(r,0x2a)=1; W(r,0x1c)=(uint16_t)(w&~1);
    W(r,0x34)=(uint16_t)((e[6]<<8)|e[7]); B(r,0x00)=1; W(r,0x1a)=0x180;
    arcade_4544e(r,var); arcade_45684(r,var,0); }
