/* ORIGINAL ARCADE PC: 0x00042380 boss body->component sync. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * fp=A5+0x5C8; 5 iters: if component active, copy body word +0x02
 * (facing+mode) and enter 0x43458. */
#include "raw_common.h"
extern uint8_t *blk5c8_base;
extern void arcade_43458(uint8_t *parent, uint8_t *child, uint16_t index);
void arcade_42380(uint8_t *body){ uint8_t *c=blk5c8_base;
    for(int i=0;i<5;i++,c+=0x40){ if(B(c,0x00)==0) continue; W(c,0x02)=W(body,0x02); arcade_43458(body,c,(uint16_t)(i+13)); } }
