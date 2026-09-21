/* ORIGINAL ARCADE PC: 0x000423B2 boss 5-component create (block 0x5C8). RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
extern uint8_t *blk5c8_base; extern void arcade_4543e(uint8_t*);
void arcade_423b2(void){ uint8_t*a4=blk5c8_base;
    for(int i=0;i<5;i++,a4+=0x40){ B(a4,0x21)=(uint8_t)i; B(a4,0x00)=1; B(a4,0x38)=1; B(a4,0x05)=0x11; B(a4,0x06)=0x11; arcade_4543e(a4); } }
