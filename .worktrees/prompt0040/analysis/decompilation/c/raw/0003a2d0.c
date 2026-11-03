/* ORIGINAL ARCADE PC: 0x0003A2D0. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * D0 word count; A0 source; A1 destination. */
#include <stdint.h>
void arcade_3a2d0(const uint16_t *a0, uint16_t *a1, uint16_t d0)
{
    do { *a1++ = *a0++; } while (--d0 != 0);
}
