/* ORIGINAL ARCADE PC: 0x0004382E state-0x13 animation countdown reload.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source. */
#include "raw_common.h"

void arc_4382e(uint8_t *r)
{
    B(r, 0x09) = (g_round == 2) ? 4 : 0;
}
