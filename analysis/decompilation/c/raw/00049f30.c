/* ORIGINAL ARCADE PC: 0x00049F30 schedule occupancy scan (block 0x2C8). RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
extern uint8_t *blk2c8_base; extern uint8_t sched_bitmap[]; extern uint16_t g_occ29a, g_free_c56;
void arcade_49f30(void){ g_iter214=0; g_occ29a=0; for(int i=0;i<0x40;i++) sched_bitmap[i]=0; g_free_c56=0xff;
    uint8_t*a4=blk2c8_base;
    for(int s=0;s<9;s++,a4+=0x40){ if(B(a4,0x00)!=0 && B(a4,0x03)==0){ sched_bitmap[B(a4,0x26)]=1; g_occ29a++; } } }
