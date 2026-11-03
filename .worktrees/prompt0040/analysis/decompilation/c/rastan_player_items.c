/* rastan_player_items.c — H18 semantic model of the player ITEM / STATUS effect system.
 * NOT original Taito source; byte-faithful control flow is in raw/00054b1e.c, raw/0004495a.c,
 * raw/000449b4.c and (weapon types 1/2/3) rastan_player_weapon_state.c. A5 = 0x10C000.
 *
 * PROVEN ARCHITECTURE (H18):
 *   The player has TWO transient collision-event tables, each 4 x 8-byte {active,type,X,Y}:
 *     A5+0x12A8  enemy CONTACT/damage events  -> dispatcher 0x54A2C (jump table 0x550A8).
 *     A5+0x12C8  ITEM/STATUS effect events    -> dispatcher 0x54B1E (this module).
 *   Collision manager 0x449B4 clears both, then in three passes over actor pool A5+0x02C8:
 *     pass1: mode-0 enemies -> A5+0x12A8 damage event (type = actor +0x29).
 *     pass2: rec_type {3,8,15,22} (idx<9) -> A5+0x12C8 event, type via 0x4495A.
 *     pass3: family(+0x3E)==12 && rec_type(+0x06)==12 -> A5+0x12C8, type via 0x4495A.
 *   0x4495A: rec_type-12 pickup -> type 1/2/3 (weapon; +0x25 selects); else type 0.
 *
 * NOTE: these tables are transient per-frame EFFECT-EVENT queues, NOT item-actor pools. A "pickup"
 * is a rec_type-12 actor in A5+0x02C8; the event record is only the contact effect it emits. */
#include <stdint.h>

/* technical effect class of each A5+0x12C8 event type (0..13). */
typedef enum {
    ITEM_EFFECT_HIT_AUX = 0,     /* type 0  -> 0x5506C activate aux A5+0x1296 (not an item) */
    ITEM_EFFECT_TIMED_WEAPON,    /* types 1,2,3 -> A5+0x12FA = 4(FIRE)/2/3, timer A5+0x1326 */
    ITEM_EFFECT_COMBO_STATE,     /* types 4..7 -> A5+0x1388 = 0..3 */
    ITEM_EFFECT_LIFE,            /* type 8  -> A5+0x110A/0x1108/0x1390/0x140E */
    ITEM_EFFECT_ENERGY_RESTORE,  /* types 9,10,13 -> A5+0x013A += / = */
    ITEM_EFFECT_ENERGY_DRAIN     /* types 11,12 -> A5+0x013A -=, defense A5+0x1366 */
} PlayerItemEffectClass;

/* proven type -> effect-class map for the A5+0x12C8 dispatcher (0x54B1E). */
PlayerItemEffectClass rastan_item_event_effect_class(unsigned type)
{
    switch (type) {
        case 0:                     return ITEM_EFFECT_HIT_AUX;
        case 1: case 2: case 3:     return ITEM_EFFECT_TIMED_WEAPON;
        case 4: case 5: case 6:
        case 7:                     return ITEM_EFFECT_COMBO_STATE;
        case 8:                     return ITEM_EFFECT_LIFE;
        case 9: case 10: case 13:   return ITEM_EFFECT_ENERGY_RESTORE;
        case 11: case 12:           return ITEM_EFFECT_ENERGY_DRAIN;
        default:                    return ITEM_EFFECT_HIT_AUX; /* >=14 unused */
    }
}

/* 0x4495A actor -> event type: rec_type 12 pickup -> weapon 1/2/3 (+0x25 selects), else 0. */
unsigned rastan_pickup_actor_event_type(unsigned actor_rec_type_06, unsigned actor_field_25)
{
    if (actor_rec_type_06 != 12) return 0;
    if (actor_field_25 == 3) return 2;
    if (actor_field_25 != 0) return 3;   /* !=0 && !=3 */
    return 1;                            /* +0x25==0 -> FIRE (selector 4) */
}

/* H19 REACHABILITY (proven from a full static xref sweep of the arcade world_rev1 code):
 *   - The A5+0x12C8 table has EXACTLY ONE producer: the collision manager 0x449B4 (via 0x4495A).
 *   - 0x449B4/0x4495A can only ever write event types 0, 1, 2, 3.
 *   - Event type 1/2/3 requires an overlapping actor with rec_type(+0x06)==12, but NO actor creator
 *     in the ROM ever sets +0x06 = 12 (writers produce 1/8/9/10/11/13/15/17/18/23-26/27; boss table
 *     0x444E0 = {0e,13,14,15,10,17}; 0x41362 does not set +0x06; no seed record has it). Therefore
 *     the weapon-pickup event (types 1/2/3) is UNREACHABLE by a legitimate actor in this revision.
 *   - Event types 4..13 (COMBO/LIFE/ENERGY) are NEVER written to A5+0x12C8 by any producer; their
 *     handlers 0x54F08..0x55004 are called ONLY from the 0x54B1E dispatcher. (The COMBO handlers
 *     0x54F08/1E/34 are ALSO reachable from the A5+0x12A8 enemy-contact jump table 0x550A8 as combat
 *     types 26/28/30 -- i.e. enemy contact, not item pickup.)
 *   - Net: the only A5+0x12C8 event actually produced in normal play is type 0 (HIT_AUX) from pass-2
 *     rec_type-{3,8,15,22} enemies. The item/weapon/energy pickup effects via this table are
 *     VESTIGIAL. The game's visible item pickups (if any) must use a mechanism outside this table --
 *     the exact open H19/H20 dependency. */
int rastan_item_event_type_is_producible(unsigned type)
{
    return type <= 3;   /* only 0,1,2,3 are ever written by 0x449B4; and 1/2/3 need rec_type-12
                           actors that are never created -> in practice only type 0 occurs. */
}
