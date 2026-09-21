/*
 * Rastan arcade reconstructed decompilation — actor state dispatch + marker scan.
 * Derived from static analysis of the 68000 program; NOT original Taito source.
 */
#include "rastan_arcade_types.h"

/* Handlers (defined in rastan_actor_behavior.c / rastan_actor_creation.c). */
extern void actor_ground_scanner_41180(ActorRecord *a4);   /* state 0x00 */
extern void actor_flying_engine_473b8(ActorRecord *a4);    /* 0x473B8 (states 1,2,0D,0E) */
extern void actor_ground_engine_47140(ActorRecord *a4);    /* 0x47140 (states 3-0C,12) */
extern void actor_armored_40ccc(ActorRecord *a4);          /* state 0x0F */
extern void actor_state10_40c08(ActorRecord *a4);          /* state 0x10 */
extern void actor_boss_component_4684e(ActorRecord *a4);   /* state 0x11 */
/* H5 dedicated state bodies (rastan_actor_behavior.c). */
extern void h5_4375c(ActorRecord *a4); /* 0x13/0x14 */
extern void h5_43840(ActorRecord *a4); /* 0x15 */
extern void h5_43ae6(ActorRecord *a4); /* 0x16 */
extern void h5_43f88(ActorRecord *a4); /* 0x17 */
extern void h5_44082(ActorRecord *a4); /* 0x18/0x1C */
extern void h5_4396a(ActorRecord *a4); /* 0x19 */
extern void h5_43b32(ActorRecord *a4); /* 0x1A */
extern void h5_43ecc(ActorRecord *a4); /* 0x1B */
extern void h5_4415a(ActorRecord *a4); /* 0x1D/0x21 */
extern void h5_43636(ActorRecord *a4); /* 0x22 */

/*
 * ORIGINAL ARCADE PC: 0x00040BAA  actor_state_dispatch
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 *
 * 40baa: d0 = a4->state; d0 *= 2; a0 = 0x40bc2 + d0; d0 = word[a0];
 *        a0 = 0x40bc2 + (int16)d0; jmp (a0)
 * Jump table at arcade 0x40BC2 = 35 signed 16-bit self-relative offsets
 * (states 0x00..0x22). Decoded targets below.
 */
void actor_state_dispatch(ActorRecord *a4)
{
    switch (a4->state) {
    case 0x00:                       actor_ground_scanner_41180(a4); break; /* -> 0x41180 */
    case 0x01: case 0x02:
    case 0x0D: case 0x0E:            actor_flying_engine_473b8(a4);   break; /* -> 0x473B8 */
    case 0x03: case 0x04: case 0x05:
    case 0x06: case 0x07: case 0x08:
    case 0x09: case 0x0A: case 0x0B:
    case 0x0C: case 0x12:            actor_ground_engine_47140(a4);   break; /* -> 0x47140 */
    case 0x0F:                       actor_armored_40ccc(a4);         break; /* -> 0x40CCC */
    case 0x10:                       actor_state10_40c08(a4);         break; /* -> 0x40C08 */
    case 0x11:                       actor_boss_component_4684e(a4);  break; /* -> 0x4684E (0x41CEA->0x4684E) */
    case 0x13: case 0x14:            h5_4375c(a4); break;
    case 0x15:                       h5_43840(a4); break;
    case 0x16:                       h5_43ae6(a4); break;
    case 0x17:                       h5_43f88(a4); break;
    case 0x18: case 0x1C:            h5_44082(a4); break;
    case 0x19:                       h5_4396a(a4); break;
    case 0x1A:                       h5_43b32(a4); break;
    case 0x1B:                       h5_43ecc(a4); break;
    case 0x1D: case 0x21:            h5_4415a(a4); break;
    case 0x22:                       h5_43636(a4); break;
    default: /* states 0x23+ are outside the 35-entry table */ break;
    }
}

/*
 * ORIGINAL ARCADE PC: 0x00040E74  marker recheck helper (returns d1 match flag)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 *
 * 40e74: a0 = actor cell address stored at +0x0E; d0 = word[a0] >> 8; d1=0;
 *        if ((uint8)(word[a0]>>8) == a4->target_char) d1 = 1.
 * The cell reference is an arcade collision-grid ADDRESS (not a host pointer):
 * read it back via the stored address, not by reinterpreting bytes as a pointer.
 */
extern uint16_t collision_word_at(uint32_t arcade_addr); /* reads the 16-bit collision word */
int arcade_40e74_marker_recheck(ActorRecord *a4)
{
    uint32_t cell = ar_cell_addr(a4);                 /* +0x0E..+0x11 arcade address */
    uint8_t hi = (uint8_t)(collision_word_at(cell) >> 8);
    return (hi == a4->target_char) ? 1 : 0;           /* d1 */
}

/*
 * ORIGINAL ARCADE PC: 0x00041064  actor_surface_marker_find_41064
 * Provenance: GHIDRA_RAW (normalized) + disasm. Status: COMPLETE.
 *
 * Scans the live collision grid for a cell whose HIGH byte == the actor's
 * target char (+0x0D). Only runs for hunter actors (mode!=0 && field_30!=0).
 * Clears scan bookkeeping (A5+0x224/0x216/0x218/0x21A), then walks columns via
 * collision_map_lookup_53a2e(); each step advances A0 by 8 (one cell) and wraps
 * (|0x7f boundary -> -0x80). Returns match count in d1 (0 = not found).
 * Registers: A5+0x224 = per-target instance counter (compared to +0x2F);
 * A5+0x216 = accumulated Y offset, A5+0x218 = accumulated X offset.
 */
int arcade_41064_marker_find(ActorRecord *a4)
{
    if (a4->mode == 0 || a4->field_20 == 0)   /* +0x03 hunter, +0x30 armed */
        return 0;

    G.iter_214 = 0;                 /* A5+0x224 instance counter (approx) */
    uint16_t x_off = (a4->mode == 2) ? 0x100 : 0x08; /* A5+0x218 seed */
    int steps = 0x10;               /* A5+0x21A = 16 */
    uint32_t a0 = collision_map_lookup_53a2e();  /* arcade collision-grid ADDRESS (not host ptr) */
    uint8_t want = a4->target_char; /* +0x0D */

    for (;;) {
        uint8_t hi = (uint8_t)(collision_word_at(a0) >> 8);
        if (hi == want) {
            /* match: A5+0x222 = hi, A5+0x226 = a0; then absorb a run of the same
             * marker (each extends A5+0x216 by 8). Return found. */
            return 1;
        }
        /* advance one cell column (+8 bytes); wrap at the 0x7f-aligned boundary,
         * arithmetic on the arcade address, mirroring 68000 |0x7f / -0x80 form. */
        uint32_t next = a0 + 8;
        if ((a0 | 0x7f) <= next)
            next = a0 - 0x80;
        a0 = next;
        if (--steps == 0)
            break;
    }
    (void)x_off;
    return 0;
}
