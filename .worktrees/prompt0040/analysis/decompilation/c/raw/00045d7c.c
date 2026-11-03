/* ORIGINAL ARCADE PC: 0x00045D7C. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * IMPORTANT: 0x3A2D0 copies A0 -> A1.  Thus this publishes A5+0x1600 to
 * palette RAM 0x200000, not the reverse. */
#include <stdint.h>
extern uint16_t g_a5_0238, g_a5_13b0, g_a5_0c50;
extern uint16_t *g_working_palette_1600;
extern uint16_t *arcade_palette_ram_200000;
extern void arcade_3a2d0(const uint16_t *, uint16_t *, uint16_t);
extern void arcade_3ba20(void);
void arcade_45d7c(void)
{
    if (g_a5_0238 == 0) return;
    uint16_t chunk = (uint16_t)(g_a5_0238 - 1);
    if (chunk >= 8) {
        g_a5_0238 = 0; g_a5_13b0 = 1; arcade_3ba20(); g_a5_0c50 = 1; return;
    }
    arcade_3a2d0(g_working_palette_1600 + chunk*64,
                  arcade_palette_ram_200000 + chunk*64, 64);
    ++g_a5_0238;
}
