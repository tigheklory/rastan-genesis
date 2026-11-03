/* ORIGINAL ARCADE PC: 0x0003B9F8. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Initializes CLCS palette RAM: 48 consecutive lines from 0x4EAF6, followed
 * by one line from 0x4FE62.  0x3BA64 converts each 0RGB source word. */
#include <stdint.h>
extern uint16_t rom_word(uint32_t address);
extern uint16_t *arcade_palette_ram_200000;
static uint16_t convert_3ba64(uint16_t w)
{
    return (uint16_t)(((w & 0x0f00u) >> 7) | ((w & 0x00f0u) << 2) |
                      ((w & 0x000fu) << 11));
}
void arcade_3b9f8(void)
{
    uint16_t *dst = arcade_palette_ram_200000;
    for (uint32_t i = 0; i < 768; ++i) *dst++ = convert_3ba64(rom_word(0x4eaf6u + i*2));
    for (uint32_t i = 0; i <  16; ++i) *dst++ = convert_3ba64(rom_word(0x4fe62u + i*2));
}
