/* ORIGINAL ARCADE PC: 0x000453D6 actor-template difficulty adjustment.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source. */
#include "raw_common.h"

extern uint8_t g_difficulty_002f; /* A5+0x002F */

void arc_453d6(uint8_t *r)
{
    uint8_t hi;
    uint8_t lo;

    if (B(r, 0x06) == 12)
        return;

    hi = B(r, 0x28);
    lo = B(r, 0x29);
    if (g_difficulty_002f == 0) {
        if (hi >= 2)
            --hi;
        if (lo >= 2)
            --lo;
    } else if (g_difficulty_002f == 2) {
        ++lo;
    } else if (g_difficulty_002f >= 3) {
        ++hi;
        ++lo;
    }
    B(r, 0x28) = hi;
    B(r, 0x29) = lo;
}
