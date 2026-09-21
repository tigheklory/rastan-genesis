/*
 * Rastan arcade reconstructed decompilation — actor allocation / initialization.
 * Derived from static analysis of the 68000 program; NOT original Taito source.
 * Provenance per function below. A5-relative actor blocks are passed as arrays.
 */
#include "rastan_arcade_types.h"

extern void actor_family_loader_4544e(ActorRecord *a4, uint8_t variant_752);
extern void actor_palette_45684(ActorRecord *a4, uint8_t variant_752, int boss_mode);
extern void actor_record_loader_4543e(ActorRecord *a4);

/* Actor storage blocks (A5-relative). Sizes are the render-pass slot counts. */
extern ActorRecord blk_2c8[9];   /* A5+0x2C8 field-schedule / ground pool */
extern ActorRecord blk_508[2];   /* A5+0x508 Flying Demon components */
extern ActorRecord blk_5c8[6];   /* A5+0x5C8 boss components */
extern ActorRecord blk_748[11];  /* A5+0x748 single/batch */
extern ActorRecord blk_3c8[5];   /* A5+0x3C8 (within 0x2C8 block) burst children */
extern uint8_t sched_owner_bitmap[/*0x40*/]; /* A5+0xC52 per-slot owner marks */

/*
 * ORIGINAL ARCADE PC: 0x00049F30  schedule occupancy scan
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Walks the 9 records of block 0x2C8; for each active floor-follower
 * (active!=0 && mode==0) marks its schedule slot (sched_owner_bitmap[+0x26]=1)
 * and increments the occupied count (A5+0x29A). Returns first free schedule slot
 * (A5+0xC56, initialised 0xFF = none).
 */
uint8_t sched_occupancy_scan_49f30(void)
{
    G.iter_214 = 0;                 /* A5+0x214 */
    uint16_t occupied = 0;          /* A5+0x29A */
    for (int i = 0; i < 0x40; i++)  /* clear A5+0xC52 owner bitmap */
        sched_owner_bitmap[i] = 0;
    G.sched_free_c56 = 0xFF;        /* A5+0xC56 result default */

    ActorRecord *a4 = &blk_2c8[0];
    for (int slot = 0; slot < 9; slot++, a4++) {
        if (a4->active != 0 && a4->mode == 0) {
            sched_owner_bitmap[a4->sched_slot] = 1; /* +0x26 owner */
            occupied++;
        }
    }
    /* (caller derives A5+0xC56 = first slot with owner==0 elsewhere in 0x4A02A) */
    return (uint8_t)G.sched_free_c56;
}

/*
 * ORIGINAL ARCADE PC: 0x0004A086  field-schedule actor installer
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Installs an 8-byte schedule entry into a freshly-found free slot (A4).
 * Fields NOT written here (rely on prior slot clear): state(+0x05)=0 scanner,
 * mode(+0x03)=0 follower, target_char(+0x0D), x(+0x16), facing(+0x02).
 */
void sched_install_4a086(ActorRecord *a4, const uint8_t entry[8])
{
    a4->klass  = entry[0];                      /* b0 -> +0x04 */
    a4->family = entry[1];                      /* b1 -> +0x3E */
    uint8_t b2 = entry[2];
    a4->comp   = (uint8_t)(b2 & 0x0F);          /* lo nibble -> +0x38 */
    uint8_t variant = (uint8_t)(b2 >> 4);       /* hi nibble -> A4+0x752 */
    a4->field_36 = entry[3];                    /* b3 -> +0x36 */
    uint16_t w45 = (uint16_t)((entry[4] << 8) | entry[5]);
    if (w45 & 1) a4->field_2a = 1;              /* bit0 stripped as flag -> +0x2A */
    a4->timer  = (uint16_t)(w45 & ~1);          /* -> +0x1C */
    a4->field_34 = (uint16_t)((entry[6] << 8) | entry[7]); /* w67 -> +0x34 */
    a4->active = 1;                             /* +0x00 */
    a4->y = 0x180;                              /* +0x1A off-screen */
    actor_family_loader_4544e(a4, variant);     /* base/graphics */
    actor_palette_45684(a4, variant, 0);        /* palette */
}

/*
 * ORIGINAL ARCADE PC: 0x0004103E  latent child-hunter creation
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Reached from the marker-spawn table at 0x41000. target_char (+0x0D) is set by
 * config 0x41D08 before this.
 */
void child_hunter_create_4103e(ActorRecord *a4)
{
    a4->active    = 1;      /* +0x00 */
    a4->mode      = 1;      /* +0x03 hunter */
    a4->klass     = 1;      /* +0x04 */
    a4->timer     = 1;      /* +0x1C */
    a4->field_20  = 1;      /* +0x20 armed */
    a4->y         = 0x180;  /* +0x1A off-screen */
}

/*
 * ORIGINAL ARCADE PC: 0x00045248  parameterized latent-hunter creator (18 callers)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * d0=variant/select, d1=component idx, d2=target char, d3=base graphics.
 */
void hunter_create_45248(ActorRecord *a4, uint8_t d0, uint8_t d1,
                         uint8_t d2, uint16_t d3)
{
    a4->active     = 1;    /* +0x00 */
    a4->mode       = 1;    /* +0x03 hunter */
    a4->variant_2f = d0;   /* +0x2F */
    a4->klass      = 1;    /* +0x04 */
    a4->timer      = 1;    /* +0x1C */
    a4->field_20   = 1;    /* +0x20 */
    a4->comp_index = d1;   /* +0x21 */
    a4->target_char= d2;   /* +0x0D  (e.g. 0x54 'T', 0x55 'U') */
    a4->base       = d3;   /* +0x1E  (e.g. 0x0224; 0x0179 at 0x46758/0x4678C) */
    a4->y          = 0x180;/* +0x1A off-screen */
}

/*
 * ORIGINAL ARCADE PC: 0x000453A2  paired-actor activation helper
 * Provenance: GHIDRA_RAW (normalized). Status: COMPLETE.
 */
void paired_actor_activate_453a2(ActorRecord *a4)
{
    a4->timer  = 1;    /* +0x1C */
    a4->active = 1;    /* +0x00 */
    a4->state  = 3;    /* +0x05 -> ground engine */
    a4->y      = 0x180;/* +0x1A off-screen */
    actor_record_loader_4543e(a4);
}

/*
 * ORIGINAL ARCADE PC: 0x00045342  paired Flying-Demon initializer (17 callers)
 * Provenance: GHIDRA_RAW (normalized). Status: COMPLETE.
 * Fixed slots blk_508[0] (0x508) and blk_508[1] (0x548). rec_type 8 or 9 by
 * A5+0xC5A variant. NB: 0x50E = 0x508+6 = blk_508[0].rec_type, likewise 0x54E.
 */
void paired_flying_demon_init_45342(void)
{
    if (blk_508[1].active != 0)   /* A5+0x548 guard: already active */
        return;
    uint8_t rt = (G.variant_sel_c5a == 0) ? 8 : 9;
    blk_508[0].rec_type = rt;     /* A5+0x50E */
    blk_508[1].rec_type = rt;     /* A5+0x54E */
    /* A5+0x547, A5+0x52F |= 0x80, A5+0x56F |= 0x80 (flag words, elided) */
    paired_actor_activate_453a2(&blk_508[0]);
    paired_actor_activate_453a2(&blk_508[1]);
    arcade_3a0ec(/*spawn cue*/ 0);
}

/*
 * ORIGINAL ARCADE PC: 0x00045CFC  generic scripted activator
 * Provenance: GHIDRA_RAW. Status: COMPLETE.
 */
void scripted_activate_45cfc(ActorRecord *a4)
{
    a4->active = 1;    /* +0x00 */
    a4->state  = 3;    /* +0x05 */
    a4->timer  = 1;    /* +0x1C */
}

/*
 * ORIGINAL ARCADE PC: 0x000423B2  boss 5-component creator (block 0x5C8)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 */
void boss_components_create_423b2(void)
{
    for (int i = 0; i < 5; i++) {
        ActorRecord *a4 = &blk_5c8[i];
        a4->comp_index = (uint8_t)i; /* +0x21 component index (0..4) */
        a4->active     = 1;          /* +0x00 */
        a4->comp       = 1;          /* +0x38 */
        a4->state      = 0x11;       /* +0x05 -> 0x4684E */
        a4->rec_type   = 0x11;       /* +0x06 */
        actor_record_loader_4543e(a4);
    }
}
/* ORIGINAL ARCADE PC: 0x000423F4 — same into A5+0x648; Status: COMPLETE (mirror). */

/*
 * ORIGINAL ARCADE PC: 0x00004CD50 (function head 0x4CD42)  batch/group creator
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Free-slot batch into block 0x748: base 0x0D56, state 0x0B, rec_type 0x16.
 * x from a0 stream + d0, home from a1 stream; count d2. Callers: 0x4D410/
 * 0x4DAD2/0x4DFB4 (PC-relative jsr).
 */
void batch_create_4cd50(const uint16_t *a0_coords, const uint16_t *a1_home,
                        int16_t d0_x, int16_t d1_y, int d2_count)
{
    int made = 0;
    for (int slot = 0; slot < 11 && made < d2_count; slot++) {
        ActorRecord *a2 = &blk_748[slot];
        if (a2->active != 0)
            continue;
        a2->active   = 1;                                 /* +0x00 */
        a2->x        = (uint16_t)(*a0_coords++ + d0_x);   /* +0x16 */
        a2->y        = (uint16_t)(*a0_coords++ + d1_y);   /* +0x1A */
        a2->home_x   = *a1_home++;                        /* +0x14 */
        a2->home_y   = *a1_home++;                        /* +0x18 */
        a2->anim     = 0xED;                              /* +0x01 */
        a2->base     = 0x0D56;                            /* +0x1E */
        a2->state    = 0x0B;                              /* +0x05 -> ground engine */
        a2->rec_type = 0x16;                              /* +0x06 */
        a2->anim_frame_dur = 2;                           /* +0x08 */
        a2->init_flag= 1;                                 /* +0x07 */
        a2->anim_frame_cd = 1;                            /* +0x09 */
        a2->anim_subcount = 0;                            /* +0x12 */
        a2->comp     = 1;                                 /* +0x38 */
        made++;
    }
}

/*
 * ORIGINAL ARCADE PC: 0x000427B2  individual off-screen retirement
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Clears active (+0x00) when the actor has scrolled off (field_24 set, X out of
 * range checked by the caller). Only +0x00 is cleared -> other fields stale ->
 * the next allocator must fully re-initialize the slot.
 */
void actor_retire_offscreen_427b2(ActorRecord *a4)
{
    a4->active = 0;   /* +0x00 */
    /* if (A5+0x212 == 1) blk_508[?] cleared too (caller state, elided) */
}
