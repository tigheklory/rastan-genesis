/* ORIGINAL ARCADE PC: 0x000427B2 off-screen retire. RECONSTRUCTED_FROM_68000. COMPLETE.
 * Only +0x00 cleared -> stale fields remain (allocators must full re-init). */
#include "raw_common.h"
void arcade_427b2(uint8_t *r){ B(r,0x00)=0; }
