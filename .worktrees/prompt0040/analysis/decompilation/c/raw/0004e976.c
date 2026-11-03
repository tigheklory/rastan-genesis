/* ORIGINAL ARCADE PC: 0x0004E976. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Converts R6 phase 0/3/6/9/other to D7 offset-table index 0/1/2/3/4 and
 * simultaneously advances D2 by D0 once per nonzero bucket crossed. */
#include <stdint.h>
uint16_t arcade_4e976(uint16_t phase, uint16_t d0, uint16_t *d2)
{
    if (phase == 0) return 0;
    *d2 = (uint16_t)(*d2 + d0); if (phase == 3) return 1;
    *d2 = (uint16_t)(*d2 + d0); if (phase == 6) return 2;
    *d2 = (uint16_t)(*d2 + d0); if (phase == 9) return 3;
    *d2 = (uint16_t)(*d2 + d0);
    return 4;
}
