/* ORIGINAL ARCADE PC: 0x00054DD2 — per-frame power-up timers.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for melee weapon expiry
 * 0x54E58..0x54E80. This is not original Taito source. */
#include <stdint.h>

static const uint16_t melee_duration_by_raw_1418[5] = {
    0x0bb8, 0x0e10, 0x1068, 0x12c0, 0x1518
};

typedef struct PowerupTimerFields54dd2 {
    uint16_t raw_1418;
    uint16_t melee_weapon_12fa;
    uint16_t melee_weapon_timer_1326;
} PowerupTimerFields54dd2;

void arcade_54dd2_update_melee_weapon_timer(PowerupTimerFields54dd2 *s)
{
    uint16_t limit = melee_duration_by_raw_1418[s->raw_1418];
    if (s->melee_weapon_timer_1326 == limit) {
        s->melee_weapon_timer_1326 = 0;
        s->melee_weapon_12fa = 1;       /* expire to normal SWORD */
    } else {
        ++s->melee_weapon_timer_1326;
    }
}
