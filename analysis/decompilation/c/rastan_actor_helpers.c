/*
 * Rastan arcade reconstructed decompilation — actor graphics/template helpers.
 * Derived from static analysis of the 68000 program; NOT original Taito source.
 * Provenance: SEMANTIC_REWRITE of GHIDRA_RAW functions (see raw/ for close form).
 */
#include "rastan_arcade_types.h"

/*
 * ORIGINAL ARCADE PC: 0x0004543E  actor_record_loader_4543e
 * Provenance: GHIDRA_RAW (normalized). Status: COMPLETE.
 * Record-type graphics template loader: template = 0x45592[(rec_type-8)].
 */
void actor_record_loader_4543e(ActorRecord *a4)
{
    const ActorTemplate *t = &record_type_45592[(int16_t)(int8_t)(a4->rec_type - 8)];
    a4->base     = t->base;      /* +0x1E */
    a4->field_3a = t->field_3a;  /* +0x3A */
    a4->anim     = t->anim;      /* +0x01 */
    a4->cfg_28   = t->cfg_28;    /* +0x28 */
    a4->cfg_2c   = t->cfg_2c;    /* +0x2C */
    arcade_453d6(a4);            /* difficulty tune of +0x28/+0x29 */
}

/*
 * ORIGINAL ARCADE PC: 0x0004544E  FUN_0004544e
 * Provenance: GHIDRA_RAW (normalized). Status: COMPLETE.
 * Family graphics template loader. family==2 -> boss tables selected by comp
 * (+0x38) indexed by variant (A4+0x752); else family table by +0x3E.
 */
void actor_family_loader_4544e(ActorRecord *a4, uint8_t a4_variant_752)
{
    const ActorTemplate *t;

    if (a4->family == 0x02) {
        const ActorTemplate *tbl = boss_comp0_454ba;      /* comp 0 */
        if (a4->comp != 0x00) {
            tbl = boss_comp3_454d2;                        /* comp 3 */
            if (a4->comp != 0x03)
                tbl = boss_else_454ea;                     /* else */
        }
        t = &tbl[a4_variant_752 & 3];
    } else {
        const ActorTemplate *tbl = family_var0_45502;
        if (a4_variant_752 != 0)
            tbl = family_varN_45562;
        t = &tbl[a4->family];
    }
    a4->base     = t->base;
    a4->field_3a = t->field_3a;
    a4->anim     = t->anim;
    a4->cfg_28   = t->cfg_28;
    a4->cfg_2c   = t->cfg_2c;
    arcade_453d6(a4);
}

/*
 * ORIGINAL ARCADE PC: 0x00045684  FUN_00045684  palette attribute resolver.
 * Provenance: GHIDRA_RAW (normalized). Status: COMPLETE.
 * CORRECTION (boss-palette-source): 0x45684 is the FIELD-SCHEDULE path (sole caller 0x4A086@0x4A0CE);
 * it is NOT on the boss-body creation path. family==2 -> family-2 FIELD palette 0x456EC
 * (by comp/variant/round); else 0x45722 / 0x4576A by family per round. Writes +0x27 |= 0x40.
 * Boss BODY records (+0x3E=0, record-type path 0x45330->0x4449E->0x453A8->0x4543E) keep +0x27=0,
 * so their palette comes from the EMBEDDED compositor control nibble via 0x3C9E8 (see 0x3C9E8).
 */
extern const uint8_t pal_456ec[];   /* family-2 FIELD palette table (0x45684 path; NOT boss) */
extern const uint8_t pal_45722[];   /* per-family per-round palette table */
extern const uint8_t pal_4576a[];   /* 0x45684 alt table (A5+0x2A2 set); NOT boss-specific */
void actor_palette_45684(ActorRecord *a4, uint8_t a4_variant_752,
                         int a5_boss_mode /* A5+0x2A2 */)
{
    const uint8_t *p;
    if (a4->family == 0x02) {
        uint8_t b = a4->comp;
        if (b > 2) b -= 2;
        p = &pal_456ec[(int16_t)b
                     + (int16_t)((G.round - 1) * 3)
                     + (int16_t)(a4_variant_752 * 0x12)];
    } else {
        const uint8_t *base = a5_boss_mode ? pal_4576a : pal_45722;
        p = &base[(int16_t)a4->family + (int16_t)((G.round - 1) * 0x0C)];
    }
    a4->pal_attr = (uint8_t)(*p | 0x40 | a4->pal_attr);
}
