/* ORIGINAL ARCADE PC: 0x0003CF40 animation frame-index wrap.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Wraps the cycling 1..56 frame index: 0 -> 56 (0x38); 57 (0x39) -> 1; otherwise unchanged. */
#include "raw_common.h"
uint8_t arcade_3cf40(uint8_t d0){
    if (d0==0)    return 56;
    if (d0==0x39) return 1;
    return d0;
}
