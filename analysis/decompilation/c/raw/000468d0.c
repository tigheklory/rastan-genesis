/* ORIGINAL ARCADE PC: 0x000468D0 component facing relative to camera X.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source. */
#include "raw_common.h"

void arc_468d0(uint8_t *r)
{
    uint16_t x = (uint16_t)(W(r, 0x16) & 0x01FF);
    B(r, 0x02) = (x < g_cam10be) ? 1 : 0;
}
