/* rastan_actor_palette.c — CHECKPOINT H10
 * Semantic reconstruction of the palette-attribute resolver 0x45684 (sets actor +0x27 palette line).
 * NOT original Taito source; byte-faithful control flow in raw/00045684.c. 68000 is final authority.
 *
 * PROVEN PALETTE CHAIN (H10):
 *   0x45684 : family(+0x3E) != 2 -> nibble = tbl_0x45722[(round-1)*12 + family]
 *             family(+0x3E) == 2 -> nibble = tbl_0x456EC[variant(+0x752)*18 + (round-1)*3 + comp_adj]
 *                                    comp_adj = (+0x38 >= 3) ? +0x38-2 : +0x38
 *   -> +0x27 |= (nibble | 0x40)          (bit6 tells the compositor to use +0x27's low nibble)
 *   -> final 16 colours = per-round ROM palette: 0x3BA88[round-1][nibble] -> pool -> 0x4FD02
 *      (identical to rom_field_palette(round, nibble) used by the field actors).
 *
 * CONSEQUENCE FOR MATERIALIZED ACTORS: everything the 0x033E hunter materializes is family-2, so its
 * palette line comes from the family-2 table 0x456EC and is ROUND + VARIANT + COMP specific. The
 * in-place base transforms (H5/H6, e.g. 0x40E9C/0x40F82) rewrite +0x1E but do NOT re-run 0x45684, so
 * the palette line (+0x27) is RETAINED from the actor's creation-time family-2 resolution — the
 * transformed sprite keeps the hunter's palette line, only its graphics base changes.
 */
#include "rastan_arcade_types.h"

/* 0x45722 non-family-2 nibble table (per-round rows of 12 families). */
extern const unsigned char pal_nib_45722[72];
/* 0x456EC family-2 nibble table (variant*18 + (round-1)*3 + comp_adj). */
extern const unsigned char pal_nib_456ec[72];
extern unsigned char g_round;      /* A5+0x118 */

unsigned char resolve_palette_line(ActorRecord *a, unsigned char variant_752){
    unsigned char nibble;
    if (a->family != 2){
        nibble = pal_nib_45722[(g_round-1)*12 + a->family];
    } else {
        unsigned char comp_adj = (a->comp >= 3) ? (unsigned char)(a->comp - 2) : a->comp;
        nibble = pal_nib_456ec[variant_752*18 + (g_round-1)*3 + comp_adj];
    }
    a->pal_attr |= (unsigned char)(nibble | 0x40);
    return (unsigned char)(nibble & 0x0F);      /* the PC090OJ palette line (0..15) */
}
