/* ORIGINAL ARCADE PC: 0x00040BAA actor state dispatcher. RECONSTRUCTED_FROM_68000. COMPLETE.
 * FAITHFUL raw form: the arcade uses a table of SIGNED 16-bit SELF-RELATIVE offsets based at
 * 0x40BC2, indexed by state (a4+0x05). 40baa: d0=B(r,5); d0+=d0; a0=0x40bc2+d0; d0=(int16)word[a0];
 * a0=0x40bc2+d0; jmp (a0). The offsets below are the actual ROM words at 0x40BC2 (35 entries). */
#include "raw_common.h"
#define TBL_BASE 0x40bc2u
static const int16_t jt16[0x23] = {  /* self-relative offsets from 0x40BC2 */
 0x05be,0x1132,0x1132,0x112c,0x112c,0x112c,0x112c,0x112c,0x112c,0x112c,
 0x112c,0x112c,0x112c,0x1132,0x1132,0x010a,0x0046,0x1128,0x112c,0x028a,
 0x028a,0x028e,0x0292,0x0296,0x029a,0x029e,0x02a2,0x02a6,0x02ae,0x02aa,
 0x02c6,0x0318,0x031c,0x02aa,0x0286 };
extern void arcade_dispatch_by_pc(uint8_t *r, uint32_t handler_pc);
void arcade_40baa(uint8_t *r){
    uint8_t st = B(r,5);
    if (st >= 0x23) return;                    /* outside the 35-entry table */
    uint32_t target = TBL_BASE + (int32_t)jt16[st];  /* self-relative, sign-extended */
    arcade_dispatch_by_pc(r, target);          /* jmp (a0) */
}
