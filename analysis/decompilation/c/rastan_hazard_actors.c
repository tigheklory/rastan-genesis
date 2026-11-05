/*
 * Rastan arcade reconstructed decompilation — environmental HAZARD actor chains.
 * Provenance: static analysis of the 68000 program (maincpu.bin + H14 marker-chain
 * evidence analysis/actor_decompilation/h14_marker_chain_transitions.tsv). NOT original
 * Taito source. This file is a SEMANTIC EXPLAINER: it ties together the already-COMPLETE
 * per-state transform handlers that produce the two Tighe-identified hazard bases, and
 * records the proven creation/round/marker facts as durable C data. It does NOT
 * reimplement those handlers (see raw/00044082.c, raw/00043840.c, raw/00040ede.c,
 * raw/00043b32.c, raw/0004415a.c and rastan_actor_tables.c for the executable form).
 *
 * TWO distinct hazard identities, both produced by the marker-chain materialization
 * system (classifier 0x41362 -> per-state transform handler -> 0x4103A retarget ->
 * writes actor base +0x1E), NOT by the field-schedule spawn path (0x4A086):
 *
 *   base 0x0224  = PIT FLAME / pit-fire hazard        (Tighe visual identity)
 *   base 0x09EA  = SPIKE / SPEAR / STALAGMITE family  (Tighe visual identity)
 *
 * CONFIDENCE DISCIPLINE: HUMAN IDENTITY (what it looks like) is PROVEN by Tighe. The
 * engineering dimensions below that are source-backed are marked PROVEN; those that still
 * require source are marked PENDING and are NOT invented here.
 */
#include "rastan_arcade_types.h"

/* ------------------------------------------------------------------ base 0x0224 ----- */
/* PIT FLAME. Not present in any base template table (record_type_45592 / family tables);
 * it exists ONLY as a marker-chain transform product, which is why it is never
 * schedule-spawned (see rastan_actor_creation.c: "base 0x0224 not schedulable").
 *
 * PROVEN writers (each already COMPLETE durable C):
 *   - 0x44082  actor state 0x18 ("high" band), R4 scene 0x5A marker 0x45 -> base 0x0224 next 0x55.
 *   - 0x4415A  actor state 0x1C/0x1D/0x21, R2 scene 0x2C marker 0x4D -> base 0x0224
 *              (low band next 0x4C/0x52; high (marker x band) matrix, mostly 0x0224).
 *   - 0x43B32  actor state 0x1A band handler: 0x0224 is one of its {0x01FC,0x0224,0x0236,
 *              0x0266,0x09EA,0x0546,0x00F4} per-band products.
 * PROVEN round reachability: Round 2 and Round 4 (next_in_scene == latent: the transformed
 *   record goes dormant until its marker band is entered).
 * PENDING (source still required, DO NOT fabricate): the per-state frame/animation program
 *   driving the flame cycle, its timer, activation/deactivation window, collision/hurtbox
 *   rect, player-damage branch, and palette-selection path for this base specifically. */
typedef struct {
    uint8_t  round;        /* 1-based arcade round */
    uint16_t scene_prog;   /* A5@0x13E scene-progression value at materialization */
    uint8_t  entry_marker; /* marker char that enters the transform */
    uint8_t  state;        /* actor state (+0x03) handled */
    uint32_t handler_pc;   /* transform handler that writes the base */
    uint8_t  next_char;    /* marker chain continuation written to +0x0D */
} HazardTransform;

const HazardTransform pit_flame_0224_writers[] = {
    { 2, 0x2C, 0x4D, 0x1C, 0x0004415A, 0x52 }, /* +0x2F!=0 -> 0x52, else 0x4C */
    { 4, 0x5A, 0x45, 0x18, 0x00044082, 0x55 },
    /* 0x43B32 state 0x1A contributes 0x0224 within its band matrix (see raw/00043b32.c). */
};

/* ------------------------------------------------------------------ base 0x09EA ----- */
/* SPIKE / SPEAR / STALAGMITE family. Unlike 0x0224 this base DOES have a static template:
 * record-type 0x1B in record_type_45592 = {0x09EA,0x9F,0xFC,0x0003,0x0004} ("common
 * projectile / thrown"). field_3a 0x9F marks the shared projectile/terrain-hazard class.
 * It is additionally produced by marker-chain transform in Round 5:
 *   - 0x43840  actor state 0x15 ("n generic"), R5 scene 0x6E marker 0x6E -> base 0x09EA
 *              next 0x71, anim 0x27, compositor 2.
 *   - 0x40EDE  actor state 0x20 (torch retarget, prog>=0x54), R5 scene 0x70 marker 0x4F ->
 *              base 0x09EA next 0x71, compositor 2.
 *   - 0x43B32  state 0x1A band handler also lists 0x09EA among its per-band products.
 * PROVEN round reachability: Round 5 (plus the rec-type-0x1B thrown/projectile class, which
 *   is round-agnostic and selected by the creator, not pinned to one round here).
 * Tighe's gallery shows at least spear-style, floor/wall spike, and stalagmite forms. The
 * project already established 0x09EA is a marker-chain TRANSFORM base, i.e. a single base
 * whose visual/behavioral FORM is selected by the entering marker + band + compositor index
 * (comp 2 above), NOT several distinct projectile bases.
 * PENDING (source still required, DO NOT fabricate): the exact branch structure that selects
 *   floor-spear vs wall-spear vs stalagmite form (orientation / placement / rise cycle),
 *   per-form animation program, retraction, collision map interaction, player damage and
 *   knockback. The compositor index (comp 2) and anim 0x27 above are the proven handles. */
const HazardTransform spike_09ea_writers[] = {
    { 5, 0x6E, 0x6E, 0x15, 0x00043840, 0x71 }, /* anim 0x27, comp 2 */
    { 5, 0x70, 0x4F, 0x20, 0x00040EDE, 0x71 }, /* comp 2 */
    /* record-type 0x1B template {0x09EA,...} in record_type_45592 is the thrown/projectile
     * class instance of the same base (see rastan_actor_tables.c). */
};
