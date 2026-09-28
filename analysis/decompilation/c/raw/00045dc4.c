/* ORIGINAL ARCADE PC: 0x00045DC4. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Publishes all 32 working lines to physical CLCS lines 48..79 in 8 chunks. */
#include <stdint.h>
extern uint16_t g_a5_0c50;
extern uint16_t *g_working_palette_1600;
extern uint16_t *arcade_palette_ram_200000;
extern void arcade_3a2d0(const uint16_t *, uint16_t *, uint16_t);
void arcade_45dc4(void)
{
    if (g_a5_0c50 == 0) return;
    uint16_t chunk = (uint16_t)(g_a5_0c50 - 1);
    if (chunk >= 8) { g_a5_0c50 = 0; return; }
    arcade_3a2d0(g_working_palette_1600 + chunk*64,
                  arcade_palette_ram_200000 + 48*16 + chunk*64, 64);
    ++g_a5_0c50;
}
