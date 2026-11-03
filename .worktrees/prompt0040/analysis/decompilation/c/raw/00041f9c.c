/* ORIGINAL ARCADE PC: 0x00041F9C animation/arc phase-advance leaf.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * A 7-instruction leaf used by the jumping/leaping attacker (state 0x19) and other cyclic actors.
 * Input d0 = current packed phase byte (from +0x21 / +0x33). It advances the low nibble and carries
 * into the high nibble via a nibble swap, returning the recombined packed phase:
 *     d1 = d0
 *     d0 = d0 + 1
 *     d0 = rol8(d0, 4)        (swap nibbles)
 *     d0 = d0 & 0xF0
 *     d0 = d0 + 1
 *     d0 = d0 + d1
 * The caller (0x41FAC arc updater) masks the result &0x30 to derive the arc phase (up/apex/down)
 * and steps +0x1A (Y) accordingly; the launch/landing/contact live in that caller, not here. */
#include "raw_common.h"

uint8_t arcade_41f9c(uint8_t d0){
    uint8_t d1 = d0;
    d0 = (uint8_t)(d0 + 1);
    d0 = (uint8_t)((d0 << 4) | (d0 >> 4));   /* rolb #4 */
    d0 = (uint8_t)(d0 & 0xf0);
    d0 = (uint8_t)(d0 + 1);
    d0 = (uint8_t)(d0 + d1);
    return d0;
}
