/* ORIGINAL ARCADE PC: 0x0004E7C6. RECONSTRUCTED_FROM_68000. Status: COMPLETE. */
#include "raw_common.h"
void arcade_4e7c6(uint8_t *part_a4, const uint8_t *primary_10c648)
{
    B(part_a4,0x02)=B(primary_10c648,0x02);
    W(part_a4,0x16)=W(primary_10c648,0x16);
    W(part_a4,0x1a)=W(primary_10c648,0x1a);
}
