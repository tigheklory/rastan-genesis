/* ORIGINAL ARCADE PC: 0x00040E74 marker recheck. RECONSTRUCTED_FROM_68000. COMPLETE.
 * a0 = actor cell ADDRESS at +0x0E..+0x11; d0 = word[a0]>>8; d1 = (d0==B(r,0x0d))?1:0.
 * The cell reference is an arcade address; read via collision_word_at, not a host cast. */
#include "raw_common.h"
static uint32_t cell_addr(const uint8_t *r){ const uint8_t*p=r+0x0e;
    return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3]; }
int arcade_40e74(uint8_t *r){ uint32_t a0=cell_addr(r);
    return ((uint8_t)(collision_word_at(a0)>>8)==B(r,0x0d))?1:0; }
