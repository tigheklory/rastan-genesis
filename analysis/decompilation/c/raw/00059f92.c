/* ORIGINAL ARCADE PC: 0x00059F92 — four gameplay bottom-HUD icon descriptors.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x59F92..0x5A096.
 *
 * A5 = 0x10C000.  The destination literals 0x10C170..0x10C188 are four
 * eight-byte PC090OJ staging records {attribute, y, code, x}.  This routine
 * does not write PC090OJ hardware directly; the records are the chip-shaped
 * output contract consumed by the later sprite path.
 *
 * For A5+0x1388, values 0..3 are the only non-hidden values established by
 * the known writers.  The intentionally sequential stores below preserve an
 * original malformed-record edge case if another non-0xFF value is supplied:
 * no code word is stored, so the X word lands in the code position.
 * This is an auditable reconstruction, not original Taito source. */
#include <stdint.h>

typedef struct ArcadeHudIconRecord {
    uint16_t attribute;
    uint16_t y;
    uint16_t code;
    uint16_t x;
} ArcadeHudIconRecord;

typedef struct ArcadeHudIconState {
    uint16_t hud_slot_selector_1388;
    uint16_t hud_item_state_140c;
    uint16_t hud_item_state_140e;
    uint16_t hud_item_state_1410;
} ArcadeHudIconState;

static void arcade_59f92_fixed_icon(ArcadeHudIconRecord *record,
                                    uint16_t source, uint16_t code,
                                    uint16_t x)
{
    if (source != 0x00ff) {
        record->attribute = 0x0080;
        record->y = 0x00e8;
        record->code = code;
        record->x = x;
    } else {
        record->attribute = 0x0001;
        record->y = 0;
        record->code = 0;
        record->x = 0;
    }
}

void arcade_59f92(const ArcadeHudIconState *state,
                   ArcadeHudIconRecord records_170_188[4])
{
    if (state->hud_slot_selector_1388 != 0x00ff) {
        uint16_t *out = (uint16_t *)(void *)&records_170_188[0];
        *out++ = 0x0003;
        *out++ = 0x00e8;
        if (state->hud_slot_selector_1388 == 0) *out++ = 0x0a6a;
        if (state->hud_slot_selector_1388 == 1) *out++ = 0x0a6b;
        if (state->hud_slot_selector_1388 == 2) *out++ = 0x0a6c;
        if (state->hud_slot_selector_1388 == 3) *out++ = 0x0a6d;
        *out++ = 0x00a0;
    } else {
        records_170_188[0] = (ArcadeHudIconRecord){0x0003, 0, 0, 0};
    }

    arcade_59f92_fixed_icon(&records_170_188[1],
                            state->hud_item_state_140e, 0x0a68, 0x00b0);
    arcade_59f92_fixed_icon(&records_170_188[2],
                            state->hud_item_state_1410, 0x0a66, 0x00c0);
    arcade_59f92_fixed_icon(&records_170_188[3],
                            state->hud_item_state_140c, 0x0a64, 0x00d0);
}
