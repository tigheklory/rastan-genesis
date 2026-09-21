/* ORIGINAL ARCADE PC: 0x0004449E boss trigger (rectype by round). RECONSTRUCTED_FROM_68000. COMPLETE.
 * clr A5+0x13AC; d0=round-1; a0=0x444E0+d0; if d0==5 block A5+0x648 comp2 else A5+0x708 comp1;
 * a4@6 = 0x444E0[round-1] {0E,13,14,15,10,17}; a4@1C=128; jsr 0x453A8; jsr 0x444E6. */
#include "raw_common.h"
extern const uint8_t rectype_444e0[6]; extern uint8_t *blk708_base,*blk648_base;
extern void arcade_453a8(uint8_t*); extern void arcade_444e6(uint8_t*);
void arcade_4449e(void){ g_a5_13ac=0; uint8_t d0=(uint8_t)(g_round-1);
    uint8_t *a4 = (d0==5)? blk648_base : blk708_base; B(a4,0x38)=(d0==5)?2:1;
    B(a4,0x06)=rectype_444e0[d0]; W(a4,0x1c)=128; arcade_453a8(a4); arcade_444e6(a4); }
