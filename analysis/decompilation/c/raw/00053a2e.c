/* ORIGINAL ARCADE PC: 0x00053A2E collision-grid cell address. RECONSTRUCTED_FROM_68000. COMPLETE.
 * col=((~A5+0x10AE+1)&0x1FF + d1)>>1; col=(col+8)&0xFC; row=((~A5+0x10B0+1)&0x1FF + d2)<<5 &0x3F00;
 * return 0x10DE00 + col + row. (d1/d2 = caller scan indices.) */
#include "raw_common.h"
uint32_t arcade_53a2e(uint16_t d1, uint16_t d2){
    uint16_t col=(uint16_t)(((uint16_t)((g_scrX10ae^0x1ff)+1)&0x1ff)+d1);
    col=(uint16_t)((col>>1)+8)&0x00fc;
    uint16_t row=(uint16_t)(((uint16_t)((g_scrY10b0^0x1ff)+1)&0x1ff)+d2);
    row=(uint16_t)(row<<5)&0x3f00;
    return 0x0010de00u + col + row;
}
