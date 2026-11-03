/* ORIGINAL ARCADE PC: 0x00045418 materialized-state +0x29 attribute loader.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * a0 = table 0x4542E; d0 = (+0x05 state) - 0x13; +0x29 = table[state-0x13].
 * This is the ONLY field 0x45418 assigns; it does NOT set the visible base +0x1E (that is set by
 * the state handler / retarget chain). Table covers states 0x13..0x22 (16 entries). */
#include "raw_common.h"

/* arcade 0x4542E: per-state +0x29 attribute (palette/priority bank) byte. */
static const uint8_t attr_4542e[16] = {
 /*0x13*/0x03,0x03,0x00,0x1e,0x00,0x0c,0x02,0x02,
 /*0x1b*/0x00,0x00,0x0c,0x00,0x00,0x00,0x0c,0x03 };

void arcade_45418(uint8_t *r){
    uint8_t idx = (uint8_t)(B(r,0x05) - 0x13);
    B(r,0x29) = attr_4542e[idx & 0x0f];
}
