/* ORIGINAL ARCADE PC: 0x00041BEE light/fire-source register (state 0x20 materialization tail).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Called by 0x41BCA after assigning state 0x20 to an 'O'/'P'/'Q' torch actor. Registers a light
 * source in the A5+0x1282 table (word stride 6, slot index = +0x2F):
 *     A5+0x1280 = 1                          (global "torches active" flag)
 *     slot->word[0] = 1                      (light active)
 *     slot->long[+2] = 0xD00460 + 0x50*A5+0x214   (per-instance light graphics pointer)
 * 0xD00460 is a fixed ROM/graphics table base; 0x214 is the scene/iteration index. */
#include "raw_common.h"
extern uint16_t g_a5_1280;
extern uint8_t *g_a5_lightbase_1282;   /* A5+0x1282 record array base */

void arcade_41bee(uint8_t *r){
    g_a5_1280 = 1;
    uint32_t gfx = 0x00d00460u + 0x50u * (uint32_t)g_iter214;
    uint8_t *slot = g_a5_lightbase_1282 + 6u * (uint8_t)B(r,0x2f);
    W(slot,0) = 1;
    *(uint32_t*)(slot+2) = gfx;
}
