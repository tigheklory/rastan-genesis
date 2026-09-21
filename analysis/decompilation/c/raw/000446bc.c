/* ORIGINAL ARCADE PC: 0x000446BC enemy hurtbox-index selector.
 * RECONSTRUCTED_FROM_68000. Status: PARTIAL.
 * Returns d3 = the index into the 4-signed-byte hurtbox rectangle table 0x44CE0 (variant 0x44FA8
 * when +0x38==2). Selection is by pool index, rec_type (+0x06), family (+0x3E), state and override
 * bytes (+0x37/+0x55/+0x02/+0x30):
 *   pool index >= 9 (secondary pool): if +0x03 -> fixed 82; else index the family table 0x44796 by
 *       family (+0x3E), overridden by +0x37 when nonzero.
 *   rec_type < 12: base via 0x446B0; rec_type 8/9 with +0x3F==0 -> 2.
 *   rec_type 22: use +0x37 (else base).
 *   rec_type 17/23/24/25: base + (+0x30 << 1) + facing(+0x02) adjust.
 *   +0x26 set -> 83.
 * The exact 0x446B0 base helper and the family table 0x44796 values are referenced but not fully
 * enumerated here (hence PARTIAL); the index-to-rectangle mapping and the rectangle table itself are
 * complete (see raw/00044cba.c and the 0x44CE0 dump in the H9 report). */
#include "raw_common.h"
extern uint8_t arcade_446b0(uint8_t *r);          /* base index helper (referenced) */
extern uint8_t hurtbox_family_44796[];            /* family-indexed table (referenced) */
extern uint16_t g_idx_214;

uint8_t arcade_446bc(uint8_t *r){
    uint8_t d3 = 0;
    if (g_idx_214 >= 9){                            /* secondary pool */
        if (B(r,0x03)) return 82;
        d3 = hurtbox_family_44796[B(r,0x3e)];
        if (B(r,0x37)) d3 = B(r,0x37);
        return d3;
    }
    uint8_t rt = B(r,0x06);
    if (rt < 12){
        d3 = arcade_446b0(r);
        if ((rt==8||rt==9) && B(r,0x3f)==0) d3 = 2;
        return d3;
    }
    if (B(r,0x26)) return 83;                        /* +0x26 -> 83 */
    if (rt==22){ if (B(r,0x37)) return B(r,0x37); return arcade_446b0(r); }
    if (rt==17 || rt==23 || rt==24 || rt==25){
        d3 = arcade_446b0(r);
        d3 = (uint8_t)(d3 + (B(r,0x30)<<1));
        if (B(r,0x02)==0) d3++;                      /* facing adjust */
        return d3;
    }
    return arcade_446b0(r);
}
