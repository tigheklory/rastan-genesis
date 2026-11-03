/* ORIGINAL ARCADE PC: 0x00054A2C — retained player item/status dispatcher.
 * RECONSTRUCTED_FROM_68000. Status: PARTIAL for the full function; COMPLETE
 * for the A5+0x12C8 weapon-event scan at 0x54B1E..0x54BF4 and its grants.
 * This is an auditable reconstruction, not original Taito source. */
#include <stdint.h>

typedef struct ItemEventRecord54a2c {
    uint16_t active;
    uint16_t subtype_and_flags;
    uint16_t x;
    uint16_t y;
} ItemEventRecord54a2c;

extern void arcade_5506c_item_subtype0(void);
extern void arcade_54ec6_grant_weapon_state3(void);
extern void arcade_54edc_grant_weapon_state2(void);
extern void arcade_54ef2_grant_fire_sword_state4(void);
extern void arcade_54f08_item_subtype4(void);
extern void arcade_54f1e_item_subtype5(void);
extern void arcade_54f34_item_subtype6(void);
extern void arcade_54f4a_item_subtype7(void);
extern void arcade_54f60_item_subtype8(void);
extern void arcade_54fd4_item_subtype9(void);
extern void arcade_54fec_item_subtype10(void);
extern void arcade_54fa4_item_subtype11(void);
extern void arcade_54fbc_item_subtype12(void);
extern void arcade_55004_item_subtype13(void);

void arcade_54b1e_dispatch_weapon_events(ItemEventRecord54a2c records[4])
{
    for (unsigned i = 0; i < 4; ++i) {
        if (records[i].active != 1) continue;
        switch (records[i].subtype_and_flags & 0x00ff) {
        case 0: arcade_5506c_item_subtype0(); break;
        case 1: arcade_54ef2_grant_fire_sword_state4(); break;
        case 2: arcade_54edc_grant_weapon_state2(); break;
        case 3: arcade_54ec6_grant_weapon_state3(); break;
        case 4: arcade_54f08_item_subtype4(); break;
        case 5: arcade_54f1e_item_subtype5(); break;
        case 6: arcade_54f34_item_subtype6(); break;
        case 7: arcade_54f4a_item_subtype7(); break;
        case 8: arcade_54f60_item_subtype8(); break;
        case 9: arcade_54fd4_item_subtype9(); break;
        case 10: arcade_54fec_item_subtype10(); break;
        case 11: arcade_54fa4_item_subtype11(); break;
        case 12: arcade_54fbc_item_subtype12(); break;
        case 13: arcade_55004_item_subtype13(); break;
        default: break;
        }
    }
}

/* PARTIAL: the independent A5+0x12A8 status-event half is outside Build 0368. */
