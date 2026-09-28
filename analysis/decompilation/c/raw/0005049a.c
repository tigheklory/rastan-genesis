/* ORIGINAL ARCADE PC: 0x0005049A — round/player equipment initialization.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x5049A..0x504F0.
 * This is an auditable reconstruction, not original Taito source. */
#include <stdint.h>

typedef struct PlayerEquipmentInitFields {
    uint16_t section_1242;
    uint16_t field_013a;
    uint16_t field_12a4, field_12a6;
    uint16_t field_1302;
    uint16_t melee_weapon_12fa;
    uint16_t melee_weapon_timer_1326;
    uint16_t field_1390;
    uint16_t front_weapon_1388;
    uint16_t field_140c, field_140e, field_1410, field_1412;
    uint16_t field_0034, field_1376;
} PlayerEquipmentInitFields;

void arcade_5049a_player_equipment_init(PlayerEquipmentInitFields *s)
{
    (void)s->section_1242;       /* 0x5049A compare has no surviving branch body */
    s->field_013a = 0x3000;
    s->field_12a4 = s->field_12a6 = 0;
    s->field_1302 = 1;
    s->melee_weapon_12fa = 1;   /* normal SWORD */
    s->melee_weapon_timer_1326 = 0;
    s->field_1390 = 0x18;
    s->field_140e = s->field_1410 = s->field_140c = 0x00ff;
    s->field_1412 = 0;
    s->front_weapon_1388 = 0x00ff;
    if (s->field_0034 == 0) s->field_1376 = 1;
}
