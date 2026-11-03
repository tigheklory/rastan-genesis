/* ORIGINAL ARCADE PC: 0x0005A098 — gameplay energy/status descriptor producer.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x5A098..0x5A242, direct
 * helper 0x5A244..0x5A288, and data table 0x5A28A..0x5A298.
 *
 * A5 = 0x10C000.  Output begins at PC090OJ object RAM 0xD00048 (record 9).
 * Each record is {attribute, y, code, x}.  Skipped leading output advances the
 * record pointer, preserving the original semantic hole.
 * This is an auditable reconstruction, not original Taito source. */
#include <stdint.h>

typedef struct ArcadeStatusRecord {
    uint16_t attribute;
    uint16_t y;
    uint16_t code;
    uint16_t x;
} ArcadeStatusRecord;

typedef struct ArcadeEnergyStatusState {
    uint16_t energy_013a;
    uint16_t indicator_bits_12a4;
    uint16_t indicator_selector_12a6;
    uint16_t status_refresh_gate_12fc;
    uint16_t indicator_phase_1306;
    uint16_t frame_counter_1308;
    uint16_t indicator_code_bits_130a;
    uint16_t low_energy_flag_1328;
    uint16_t remembered_first_cell_code_132a;
    uint16_t sound_suppression_12f4;
    uint16_t low_energy_lifecycle_13ce;
    uint16_t low_energy_event_13d2;
} ArcadeEnergyStatusState;

extern void arcade_sound_3a0ec(uint16_t command);
extern void arcade_sound_3a116(uint16_t command);

void arcade_5a244_energy_lifecycle(ArcadeEnergyStatusState *state)
{
    if (state->low_energy_flag_1328 == 1) {
        state->low_energy_event_13d2 =
            (state->low_energy_lifecycle_13ce == 0x00ff) ? 0x0011 : 1;
        state->low_energy_lifecycle_13ce = 1;
    } else {
        state->low_energy_event_13d2 =
            (state->low_energy_lifecycle_13ce == 1) ? 0x00fe : 0x00ff;
        state->low_energy_lifecycle_13ce = 0x00ff;
    }
}

void arcade_5a098(ArcadeEnergyStatusState *state,
                   ArcadeStatusRecord pc090oj_record9[8])
{
    static const uint16_t partial_code[8] = {
        0x03d5, 0x03d4, 0x03d3, 0x03d2,
        0x03d1, 0x03d0, 0x03cf, 0x03ce
    };
    ArcadeStatusRecord *out = pc090oj_record9;
    uint16_t x = 0x0010;
    const uint16_t y = 0x00e8;

    if (state->energy_013a & 0x8000) state->energy_013a = 0;

    state->indicator_selector_12a6 =
        (uint16_t)((((state->energy_013a >> 8) >> 3) & 7) | 8);
    state->indicator_bits_12a4 += 0x0010;

    uint16_t bit = state->indicator_selector_12a6;
    if (bit > 12) bit = 12;
    bit -= 2;
    const unsigned selected =
        (unsigned)((state->indicator_bits_12a4 >> bit) & 1);
    const unsigned phase = state->indicator_phase_1306 & 1;
    if ((!phase && !selected) || (phase && selected)) {
        const uint16_t code_bit = (bit < 7) ? 6 : 7;
        const unsigned alternate =
            (unsigned)((state->indicator_code_bits_130a >> code_bit) & 1);
        state->indicator_code_bits_130a += 0x0010;
        if (!alternate) state->indicator_phase_1306++;
        *out = (ArcadeStatusRecord){0, y,
                                   (uint16_t)(0x03ca + alternate), x};
    }
    out++;
    x += 0x0010;

    if (state->status_refresh_gate_12fc == 1) {
        *out++ = (ArcadeStatusRecord){0, y, 0x03cc, x};
        x += 0x0010;

        uint16_t energy_units = state->energy_013a >> 8;
        if (energy_units >= 48) energy_units = 48;
        uint16_t full_cells = energy_units >> 3;
        const uint16_t remainder = energy_units & 7;
        uint16_t cells_left = 6;

        state->low_energy_flag_1328 = 0x00ff;
        if (full_cells == 0) state->low_energy_flag_1328 = 1;

        while (full_cells != 0) {
            *out++ = (ArcadeStatusRecord){0, y, 0x03cd, x};
            x += 0x0010;
            full_cells--;
            cells_left--;
        }
        if (remainder != 0) {
            state->remembered_first_cell_code_132a = partial_code[remainder];
            *out++ = (ArcadeStatusRecord){
                0, y, state->remembered_first_cell_code_132a, x
            };
            x += 0x0010;
            cells_left--;
        } else {
            state->remembered_first_cell_code_132a = 0x03d5;
        }
        while (cells_left != 0) {
            *out++ = (ArcadeStatusRecord){0, y, 0x03d5, x};
            x += 0x0010;
            cells_left--;
        }
    }

    if (state->low_energy_flag_1328 == 1) {
        pc090oj_record9[2].code =
            ((state->frame_counter_1308 >> 1) & 1)
                ? state->remembered_first_cell_code_132a : 0x03d5;
    }

    arcade_5a244_energy_lifecycle(state);
    if (state->sound_suppression_12f4 == 0 &&
        state->low_energy_event_13d2 == 0x0011) {
        arcade_sound_3a0ec(6);
    } else if (state->low_energy_event_13d2 == 0x00fe) {
        arcade_sound_3a116(0x0029);
    }
}
