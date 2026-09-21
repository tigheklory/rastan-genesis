/* ORIGINAL ARCADE PC: 0x00040C08 state 0x10 anim-param setup (0x40C0E). RECONSTRUCTED_FROM_68000.
 * Status: PARTIAL — sets +0x29 from table 0x40C2E[+0x36-1] and +0x2C from 0x40C40; full
 * state-0x10 lifecycle (who enters/leaves) not traced. */
#include "raw_common.h"
extern const uint8_t t40c2e[]; extern const uint16_t t40c40[];
void arcade_40c08(uint8_t *r){ uint8_t d0=(uint8_t)(B(r,0x36)-1); B(r,0x29)=t40c2e[d0]; W(r,0x2c)=t40c40[d0]; }
