/* ORIGINAL ARCADE PC: 0x0003D054 sprite render-dispatch (compositor selector).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Entry from the per-actor render loops (0x41DAE etc.) with d0 = +0x01 (anim index).
 * d0 &= 0xFF; d0 *= 2 (word index). d1 = actor +0x38 (compositor SELECTOR). Dispatch:
 *     selector 1 -> jmp 0x4770E   (table 0x4771C)
 *     selector 2 -> jmp 0x3F0BC   (table 0x3F0CE)
 *     selector 3 -> jmp 0x3FFDC   (table 0x40004)
 *     selector 4 -> jmp 0x3FFF0   (table 0x4002C)
 *     selector 0 -> program = 0x3D09E + word[0x3D09E + d0]; jmp 0x3C902
 * PROVEN: every selector target simply indexes its own program table by anim and then jmps to the
 * SAME general compositor interpreter 0x3C902 (verified 0x4770E/0x3F0BC/0x3FFDC/0x3FFF0 all end in
 * `jmp/braw 0x3C902`). So the selector picks the PROGRAM TABLE; the interpreter is shared. This is
 * why the offline compositor VM renders all five selectors from COMPOSITOR_TABLES. */
#include "raw_common.h"
extern void arcade_3c902(uint8_t *r, uint32_t program_addr);   /* general compositor interpreter */
extern uint16_t rom_be16(uint32_t addr);                        /* big-endian word from maincpu */

/* compositor program-table bases, indexed by selector (+0x38). */
static const uint32_t COMPOSITOR_TABLE[5] = {
    0x03D09Eu, 0x04771Cu, 0x03F0CEu, 0x040004u, 0x04002Cu
};

void arcade_3d054(uint8_t *r, uint8_t anim){
    uint16_t idx = (uint16_t)((anim & 0xFF) * 2);
    uint8_t sel = B(r,0x38);
    if (sel > 4) sel = 0;                                       /* only 0..4 are dispatched */
    uint32_t table = COMPOSITOR_TABLE[sel];
    uint32_t program = table + rom_be16(table + idx);           /* program = table + word[table+anim*2] */
    arcade_3c902(r, program);                                    /* shared general interpreter */
}
