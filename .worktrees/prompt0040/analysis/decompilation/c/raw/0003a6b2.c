/* ORIGINAL ARCADE PC: 0x0003A6B2 — ROUND/READY transition presentation.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x3A6B2..0x3A754.
 *
 * This is the one-shot PC080SN text overlay, not the persistent PC090OJ
 * lower-HUD ROUND producer.  This is an auditable reconstruction, not
 * original Taito source. */
#include <stdint.h>

extern void arcade_55ddc(void);
extern void arcade_3b902_lower_hud_visibility(uint16_t y_high);
extern void arcade_59d20(void);
extern void arcade_3ae5a(void);
extern void arcade_3bb48_text(uint16_t selector);
extern void arcade_4527e_stage_init(void);
extern void arcade_pc080sn_write(uint32_t address, uint16_t value);
extern uint8_t g_a5_bytes[];
extern uint16_t g_a5_words[];

void arcade_3a6b2_round_ready_transition(void)
{
    arcade_55ddc();
    if (g_a5_words[0x1394 / 2] != 0x00ff) return;

    arcade_3b902_lower_hud_visibility(1); /* hide records 17..21 */
    if (g_a5_words[0x0034 / 2] == 0) {
        arcade_59d20();
        g_a5_words[0x0238 / 2] = 1;
        g_a5_words[0x0c4e / 2] = 0x0011;
        g_a5_words[0x0004 / 2] = 8;
        return;
    }

    arcade_3ae5a();
    uint16_t text = 56; /* READY */
    if (g_a5_words[0x0028 / 2] != 0) {
        text = (g_a5_words[0x002a / 2] == 0) ? 4 : 5; /* PLAYER 1/2 READY */
        arcade_pc080sn_write(0x00c08e7a, 0x2744);
    } else {
        arcade_pc080sn_write(0x00c08e66, 0x2744);
    }
    arcade_3bb48_text(text);

    if (g_a5_bytes[0x0104] == 0) {
        arcade_3bb48_text(55); /* descriptor C08C48, attr 0, "ROUND" */
        arcade_pc080sn_write(0x00c08c62,
            (uint16_t)(0x0030 | g_a5_bytes[0x0117]));
    }
    arcade_3bb48_text(0x0082); /* blank selector 2's string span */
    arcade_4527e_stage_init();
    arcade_59d20();
    g_a5_words[0x0238 / 2] = 1;
    g_a5_words[0x0c4e / 2] = 0x0070;
    g_a5_words[0x0004 / 2] = 7;
}
