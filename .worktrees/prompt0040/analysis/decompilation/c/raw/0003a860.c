/* ORIGINAL ARCADE PC: 0x0003A860 — round-complete stage advance.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for the bounded stage mutation
 * at 0x3A86E..0x3A890; the existing transition tail is represented as a call. */
#include <stdint.h>

extern void arcade_55ddc(void);
extern void arcade_59d20(void);
extern void arcade_3a7ec_transition_tail(void);
extern uint8_t g_a5_bytes[];
extern uint16_t g_a5_words[];

void arcade_3a860_stage_advance(void)
{
    arcade_55ddc();
    if (g_a5_words[0x1394 / 2] != 0x00ff) return;

    g_a5_words[0x1242 / 2] = (uint16_t)(g_a5_words[0x013e / 2] + 1);
    g_a5_bytes[0x0118]++;
    g_a5_bytes[0x0117]++;
    if (g_a5_bytes[0x0118] == 7) {
        g_a5_bytes[0x0117] = 6; /* display mirror caps at final round */
        return;
    }

    arcade_59d20();
    g_a5_words[0x0238 / 2] = 1;
    g_a5_words[0x0c4e / 2] = 0x0011;
    g_a5_words[0x0004 / 2] = 8;
    arcade_3a7ec_transition_tail();
}
