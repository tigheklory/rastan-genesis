/* ORIGINAL ARCADE PC: 0x00041064 marker find (hunter). RECONSTRUCTED_FROM_68000. COMPLETE.
 * Only for mode!=0 && +0x30!=0. a0 = 0x53A2E() collision-grid ADDRESS; step +8/cell; wrap at the
 * 0x7f-aligned column boundary (|0x7f -> -0x80); match when (word[a0]>>8)==B(r,0x0d). d1=0 if none. */
#include "raw_common.h"
int arcade_41064(uint8_t *r){
    if (B(r,0x03)==0 || B(r,0x30)==0) return 0;
    int steps=0x10; uint32_t a0=collision_map_lookup_53a2e(); uint8_t want=B(r,0x0d);
    for(;;){ if((uint8_t)(collision_word_at(a0)>>8)==want) return 1;
        uint32_t nx=a0+8; if((a0|0x7f)<=nx) nx=a0-0x80; a0=nx;
        if(--steps==0) break; }
    return 0;
}
