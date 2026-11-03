/* rastan_player_world_contact.c — semantic reconstruction of ORIGINAL ARCADE
 * 0x51AB6/0x51B04/0x51B74 and the Genesis-native semantic cut used by Build 0361.
 * NOT original Taito source. Byte-faithful control flow is in raw/00051ab6.c and
 * raw/00051b04.c.
 *
 * Arcade producer chain:
 *   actor marker O/P/Q -> 0x41BEE registration token
 *   -> PC090OJ renderer writes ten object records at D00460+actor*0x50
 *   -> 0x51AB6 extracts the first nine record Y/X pairs
 *   -> 0x51B04 compares those pairs with the player and classifies the third.
 *
 * Genesis semantic cut:
 *   retained actor + family/class mapping program
 *   -> the same first nine semantic Y/X pairs at A5+0x1134
 *   -> unchanged 0x51B04 consumer.
 * The retired PC090OJ record construction and readback are absent. */
#include <stdint.h>
#include <stddef.h>
#include "rastan_arcade_types.h"

typedef struct ContactXY { uint16_t y, x; } ContactXY;

enum {
    CONTACT_SOURCE_COUNT = 3,
    CONTACT_PIECES_PER_SOURCE = 9,
    CONTACT_PARKED = 0x01ff,
    PC090OJ_CONTACT_BASE = 0x00d00460,
    PC090OJ_CONTACT_STRIDE = 0x50
};

/* The long retained by the registration is semantic identity after the native
 * cut: the quotient selects the owning 0x40-byte actor. It is never dereferenced. */
static unsigned actor_index_from_registration(uint32_t token){
    return (unsigned)((token - PC090OJ_CONTACT_BASE) / PC090OJ_CONTACT_STRIDE);
}

static void park_remaining(ContactXY *dst, unsigned first){
    for (unsigned i = first; i < CONTACT_PIECES_PER_SOURCE; ++i)
        dst[i] = (ContactXY){ CONTACT_PARKED, CONTACT_PARKED };
}

/* Semantic form of the default 0x3C950 mapping-program coordinate expansion.
 * program entries are {control, signed_y, tile_code, signed_x}; 0xFF ends it. */
static void expand_default_contact_coordinates(const ActorRecord *actor,
                                               const uint8_t *program,
                                               ContactXY dst[CONTACT_PIECES_PER_SOURCE]){
    unsigned i = 0;
    for (; i < CONTACT_PIECES_PER_SOURCE; ++i){
        uint8_t control = *program++;
        if (control == 0xff) break;
        int16_t y = (int8_t)*program++;
        program++;                                      /* tile code */
        int16_t x = (int8_t)*program++;
        y = (int16_t)(y + actor->y);
        if ((control & 0xf0) == 0x70) y = (int16_t)(y + actor->home_y);
        if (actor->facing == 0) x = (int16_t)(-x - 16);
        x = (int16_t)(x + actor->x);
        dst[i] = (ContactXY){ (uint16_t)y, (uint16_t)x };
    }
    park_remaining(dst, i);
}

/* Runtime assembly resolves program from actor family/class using the same five
 * tables as the direct-native sprite producer, then calls the logic above. */
void genesis_contact_coordinate_contract(const ActorRecord *actors,
                                         uint32_t registration_token,
                                         const uint8_t *resolved_program,
                                         ContactXY dst[CONTACT_PIECES_PER_SOURCE]){
    const ActorRecord *actor = &actors[actor_index_from_registration(registration_token)];
    expand_default_contact_coordinates(actor, resolved_program, dst);
}

_Static_assert(sizeof(ContactXY) == 4, "contact pair must be two words");
