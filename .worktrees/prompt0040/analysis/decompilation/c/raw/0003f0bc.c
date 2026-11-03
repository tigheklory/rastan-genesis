/* ORIGINAL ARCADE PC: 0x0003F0BC compositor selector-2 thunk (also 0x4770E/0x3FFDC/0x3FFF0).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The four non-zero compositor selectors are identical thunks: index the selector's program table
 * by the anim word offset (d0) and branch to the SHARED general interpreter 0x3C902.
 *   0x3F0BC (sel 2): a0=0x3F0CE; a0+=d0; d0=word[a0]; a0=0x3F0CE; a0+=d0; braw 0x3C902
 *   0x4770E (sel 1): table 0x4771C ; 0x3FFDC (sel 3): table 0x40004 ; 0x3FFF0 (sel 4): table 0x4002C
 * PROVES the selector is NOT a special rendering mode — it only chooses the program TABLE. The
 * materialized H5/H6 actors mostly use selector 2 (comp +0x38 = 2); they render through this thunk
 * into the same 0x3C902 general interpreter the offline VM implements. */
#include "raw_common.h"
extern void arcade_3c902(uint8_t *r, uint32_t program_addr);
extern uint16_t rom_be16(uint32_t addr);

/* selector -> program-table base (0x3F0BC is sel 2). */
uint32_t arcade_selector_thunk(uint8_t selector, uint8_t anim, uint8_t *r){
    static const uint32_t T[5]={0x03D09Eu,0x04771Cu,0x03F0CEu,0x040004u,0x04002Cu};
    uint32_t table=T[selector & 7 ? (selector<5?selector:0) : 0];
    uint32_t program=table + rom_be16(table + (uint16_t)((anim&0xff)*2));
    arcade_3c902(r, program);
    return program;
}
