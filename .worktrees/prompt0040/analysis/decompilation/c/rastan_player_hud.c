/* Gameplay bottom-HUD semantic model for original arcade 0x59F92, 0x5A098,
 * helper 0x5A244, their containing caller 0x5100A, and the lives/ROUND
 * producer family 0x3A64C/0x3B802.
 * NOT original Taito source.  The raw reconstructions and 68000 binary remain
 * authoritative.  No Genesis rendering design is expressed here. */
#include <stdint.h>

typedef struct HudPieceIntent {
    uint16_t attribute;
    uint16_t y;
    uint16_t code;
    uint16_t x;
    unsigned visible;
} HudPieceIntent;

typedef struct BottomHudIconInputs {
    uint16_t selector_1388;
    uint16_t state_140e;
    uint16_t state_1410;
    uint16_t state_140c;
} BottomHudIconInputs;

/* 0x59F92: four slots are independently gated and therefore may coexist.
 * 0x1388 is proven to be 0..3 or 0xFF by its known writers.  0x140E is tied
 * to the already-proven LIFE/HEALTH handler.  The bounded source evidence does
 * not safely name the gameplay concepts behind 0x1410 or 0x140C. */
void rastan_bottom_hud_icon_intents(const BottomHudIconInputs *in,
                                    HudPieceIntent out[4])
{
    static const uint16_t selector_codes[4] = {
        0x0a6a, 0x0a6b, 0x0a6c, 0x0a6d
    };
    out[0] = (HudPieceIntent){0x0003, 0x00e8, 0, 0x00a0,
                              in->selector_1388 != 0x00ff};
    if (in->selector_1388 <= 3) out[0].code = selector_codes[in->selector_1388];
    out[1] = (HudPieceIntent){0x0080, 0x00e8, 0x0a68, 0x00b0,
                              in->state_140e != 0x00ff};
    out[2] = (HudPieceIntent){0x0080, 0x00e8, 0x0a66, 0x00c0,
                              in->state_1410 != 0x00ff};
    out[3] = (HudPieceIntent){0x0080, 0x00e8, 0x0a64, 0x00d0,
                              in->state_140c != 0x00ff};
}

/* 0x5A098 energy-to-six-cell mapping.  Energy is the high byte of A5+0x013A,
 * clamped to 48; each full cell represents eight units. */
void rastan_energy_cell_intents(uint16_t energy_013a,
                                uint16_t cell_codes[6])
{
    static const uint16_t partial_code[8] = {
        0x03d5, 0x03d4, 0x03d3, 0x03d2,
        0x03d1, 0x03d0, 0x03cf, 0x03ce
    };
    uint16_t units = (energy_013a & 0x8000) ? 0 : (energy_013a >> 8);
    if (units >= 48) units = 48;
    unsigned full = units >> 3;
    unsigned remainder = units & 7;
    unsigned i = 0;
    while (i < full) cell_codes[i++] = 0x03cd;
    if (remainder != 0) cell_codes[i++] = partial_code[remainder];
    while (i < 6) cell_codes[i++] = 0x03d5;
}

/* Proven caller order inside 0x5100A, reached by 0x41F0E:
 *
 *   outer gates -> other pre-HUD work -> 0x5A098 -> A5+0x12FC=0xFF
 *   -> 0x59F92 -> surrounding gameplay work -> 0x5122A -> frame counter.
 *
 * 0x5122A conditionally invokes the already-decompiled 0x59F5E descriptor
 * clear only when A5+1360==1, A5+13AC==8, and A5+13BA==0x80.  Thus that clear
 * is later than both producers in this containing call, not their prelude.
 * The energy producer itself is gated only by the outer 0x5100A early returns;
 * 0x59F92 follows it unconditionally on the same admitted tick. */
int rastan_bottom_hud_tick_is_admitted(uint16_t gate_13e2,
                                       uint16_t delay_1260)
{
    return gate_13e2 != 1 && delay_1260 == 0;
}

/* The 0x3B802 selector table proves that selector 4 reads the low byte of the
 * active-player reserve word A5+0x0102 (address A5+0x0103).  A single-digit
 * configuration starts with leading-zero suppression disabled, so reserve 0
 * remains visible.  The fixed record template supplies control=0 and X=0. */
HudPieceIntent rastan_reserve_lives_intent(uint16_t reserve_lives_0102)
{
    return (HudPieceIntent){0, 0x00e4,
        (uint16_t)(0x002a + (reserve_lives_0102 & 0x000f)), 0, 1};
}

/* 0x3B984 + selector 3 form the persistent lower-right ROUND presentation.
 * The three label pieces are fixed.  The fourth code is the direct one-based
 * A5+0x0117 display mirror; there is no decimal/zero-base conversion. */
void rastan_round_hud_intents(uint8_t display_round_0117,
                              HudPieceIntent out[4])
{
    out[0] = (HudPieceIntent){0, 0x00e8, 0x0034, 0x0100, 1};
    out[1] = (HudPieceIntent){0, 0x00e8, 0x0035, 0x0110, 1};
    out[2] = (HudPieceIntent){0, 0x00e8, 0x0036, 0x0120, 1};
    out[3] = (HudPieceIntent){0, 0x00e8,
        (uint16_t)(0x002a + (display_round_0117 & 0x0f)), 0x0128, 1};
}

/* Stage ownership: A5+0x0118 is authoritative gameplay state.  A5+0x0117 is
 * the presentation mirror consumed by both the persistent sprite digit and
 * the ROUND/READY transition's direct ASCII cell.  Normal play is one-based;
 * reaching authoritative value 7 leaves the presentation capped at 6. */
void rastan_round_advance(uint8_t *authoritative_0118,
                          uint8_t *display_mirror_0117)
{
    (*authoritative_0118)++;
    (*display_mirror_0117)++;
    if (*authoritative_0118 == 7) *display_mirror_0117 = 6;
}
