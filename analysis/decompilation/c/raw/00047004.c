/* ORIGINAL ARCADE PCs: 0x00047004, 0x0004703C, 0x00047076.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 *
 * R1 boss entrance palette writer.  The frame spine calls 0x47004 at
 * 0x41F46.  When A5+0x26E is nonzero it selects one of six 15-word 0RGB
 * targets at 0x4708C by (round-1)*30, expands entries 1..15 through the
 * 16*8 byte component LUT at 0x46F84, converts each faded nibble to CLCS
 * xBGR-555, and writes 0x2009E2..0x2009FE.  Entry 0 at 0x2009E0 is retained.
 * The write instruction is 0x4706E; MAME's post-write callback observes PC
 * 0x47072 after the instruction has completed.
 */
#include "raw_common.h"

extern uint16_t g_boss_fade_enable_026e;
extern uint16_t g_boss_fade_step_0270;
extern uint8_t g_round_0118;
extern uint16_t rom_word(uint32_t address);
extern uint8_t rom_byte(uint32_t address);
extern void clcs_write_word(uint32_t address, uint16_t value);

/* 0x47076: D2 is a component nibble on entry and a faded nibble on return. */
uint16_t arcade_47076(uint16_t component)
{
    return rom_byte(0x46F84u + (uint32_t)(component & 0x0f) * 8u
                    + g_boss_fade_step_0270);
}

/* 0x4703C, represented with its caller-established A3/A0/D3 contract. */
void arcade_4703c(uint32_t source, uint32_t destination, uint32_t count)
{
    while (count-- != 0) {
        uint16_t rgb = rom_word(source); source += 2;
        uint16_t r = arcade_47076((uint16_t)((rgb >> 8) & 0x0f));
        uint16_t g = arcade_47076((uint16_t)((rgb >> 4) & 0x0f));
        uint16_t b = arcade_47076((uint16_t)(rgb & 0x0f));
        /* Exact 0x47048..0x4706E interleave: xBGR-555 with nibble*2. */
        clcs_write_word(destination,
            (uint16_t)((b << 11) | (g << 6) | (r << 1)));
        destination += 2;
    }
}

/* 0x47004.  Clearing the enable flag at step 7 does not skip that final
 * publication: the routine falls through and renders the step once. */
void arcade_47004(void)
{
    if (g_boss_fade_enable_026e == 0) return;
    if (g_boss_fade_step_0270 >= 7) g_boss_fade_enable_026e = 0;
    arcade_4703c(0x4708Cu + (uint32_t)(g_round_0118 - 1u) * 30u,
                 0x2009E2u, 15u);
}
