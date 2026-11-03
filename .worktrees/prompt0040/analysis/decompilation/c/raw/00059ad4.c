/* ORIGINAL ARCADE PC: 0x00059AD4. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * A0 table base, D1 source row, D0 physical CLCS destination line. 0xffff
 * preserves the existing destination entry; exactly 16 entries are visited. */
#include <stdint.h>
extern uint16_t *arcade_palette_ram_200000;
static uint16_t convert_59ade(uint16_t w)
{
    return (uint16_t)(((w & 0x0f00u) >> 7) | ((w & 0x00f0u) << 2) |
                      ((w & 0x000fu) << 11));
}
void arcade_59ad4(const uint16_t *table, uint16_t source_row, uint16_t dest_line)
{
    const uint16_t *src = table + source_row*16;
    uint16_t *dst = arcade_palette_ram_200000 + dest_line*16;
    for (unsigned i = 0; i < 16; ++i)
        if (src[i] != 0xffffu) dst[i] = convert_59ade(src[i]);
}
