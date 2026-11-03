/* Build 0368 semantic reconstruction of the original arcade melee-weapon state.
 * NOT original Taito source. The raw reconstructions and 68000 binary are authority. */
#include <stdint.h>

enum {
    RASTAN_MELEE_SWORD = 1,
    RASTAN_MELEE_FIRE_SWORD = 4
};

typedef struct RetainedMeleeWeaponState {
    uint16_t selector_12fa;
    uint16_t timer_1326;
} RetainedMeleeWeaponState;

typedef struct RetainedItemEvent {
    uint16_t active, subtype_and_flags, x, y;
} RetainedItemEvent;

void rastan_start_with_normal_sword(RetainedMeleeWeaponState *weapon)
{
    weapon->selector_12fa = RASTAN_MELEE_SWORD;
    weapon->timer_1326 = 0;
}

int rastan_item_event_grants_fire_sword(const RetainedItemEvent *event)
{
    return event->active == 1 && (event->subtype_and_flags & 0xff) == 1;
}

void rastan_grant_fire_sword(RetainedMeleeWeaponState *weapon)
{
    weapon->timer_1326 = 0;
    weapon->selector_12fa = RASTAN_MELEE_FIRE_SWORD;
}

void rastan_expire_melee_weapon(RetainedMeleeWeaponState *weapon)
{
    weapon->timer_1326 = 0;
    weapon->selector_12fa = RASTAN_MELEE_SWORD;
}

/* selector_12fa is shared authority. The retained compositor chooses one of
 * 0x5CD8A/0x5D068/0x5D346/0x5D666 and the retained collision producer chooses
 * one of 0x5C9EA/0x5CAC6/0x5CBA2/0x5CC7E. Native SAT emission consumes the
 * already-selected pieces; it does not maintain a separate weapon flag. */
