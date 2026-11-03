/* ORIGINAL ARCADE PC: 0x54EC6, 0x54EDC, 0x54EF2 — melee weapon grants.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for all three leaf routines.
 * Canonical names for states 2/3 remain unproven here; state 4 is FIRE SWORD.
 * This is an auditable reconstruction, not original Taito source. */
#include <stdint.h>

typedef struct MeleeWeaponFields54ec6 {
    uint16_t melee_weapon_12fa;
    uint16_t melee_weapon_timer_1326;
} MeleeWeaponFields54ec6;

extern void arcade_3a0ec_sound_command(uint16_t command);

static void grant(MeleeWeaponFields54ec6 *s, uint16_t state)
{
    arcade_3a0ec_sound_command(0x000e);
    s->melee_weapon_timer_1326 = 0;
    s->melee_weapon_12fa = state;
}

void arcade_54ec6_grant_weapon_state3(MeleeWeaponFields54ec6 *s) { grant(s, 3); }
void arcade_54edc_grant_weapon_state2(MeleeWeaponFields54ec6 *s) { grant(s, 2); }
void arcade_54ef2_grant_fire_sword_state4(MeleeWeaponFields54ec6 *s) { grant(s, 4); }
