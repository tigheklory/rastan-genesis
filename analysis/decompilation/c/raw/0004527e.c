/* ORIGINAL ARCADE PC: 0x0004527E — initial stage/round selection.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x4527E..0x4529A. */
#include <stdint.h>

extern uint16_t arcade_rom_word(uint32_t address);
extern uint8_t g_a5_bytes[];

void arcade_4527e_stage_init(void)
{
    uint16_t d1 = (uint16_t)(~arcade_rom_word(0x0005ff9e));
    d1 = (uint16_t)((d1 & 7) + 1); /* DIP-selected one-based start, 1..8 */
    if (g_a5_bytes[0x0104] == 0) {
        g_a5_bytes[0x0118] = (uint8_t)d1;
        g_a5_bytes[0x0117] = (uint8_t)d1;
    }
}
