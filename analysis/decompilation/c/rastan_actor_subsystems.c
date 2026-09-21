/*
 * Rastan arcade reconstructed decompilation — surrounding subsystems backfill
 * (scripted-encounter dispatch, scene/progression transition, collision address,
 * boss trigger/sync, and the actor helpers the A/B claims depend on).
 * Derived from static analysis of the 68000 program; NOT original Taito source.
 * Provenance per function. Several are intentionally PARTIAL (the historical docs
 * themselves marked these subsystems non-exhaustive).
 */
#include "rastan_arcade_types.h"

extern void actor_record_loader_4543e(ActorRecord *a4);
extern void paired_actor_activate_453a2(ActorRecord *a4);
extern uint16_t collision_word_at(uint32_t arcade_addr);
extern ActorRecord *blk_5c8_at(int i);   /* boss component block accessor */
extern void arcade_43458(ActorRecord *body, int idx_plus_13);

/* ---- actor helpers the CHECKPOINT A/B claims rely on ---- */

/*
 * ORIGINAL ARCADE PC: 0x00040A60 + table 0x40A86  floor-marker state transition
 * Provenance: GHIDRA_RAW/RECONSTRUCTED. Status: COMPLETE.
 * 4-byte records {cur_state, marker_char, new_state, term}; scan while
 * (cur_state != a4->state || marker != found) && term != 0xFF. Returns new_state.
 * Decoded entries (cur,marker->new): (1,0x31->5)(2,0x33->4)(1,0x34->2)(2,0x34->1)
 * (2,0x35->6)(1,0x38->0xA)(1,0x39->3)(2,0x3b->0xB)(1,0x3c->0xC)(2,0x32->8)
 * (1,0x36->9)(1/2,0x3e/0x3f->0xD)(1/2,0x40/0x41->0xE)(0xD,0x40->1)(0xD,0x41->2)
 * (0xE,0x3e->1)(0xE,0x3f->2); terminator flag 0xFF at (2,0x37->7).
 */
typedef struct { uint8_t cur, marker, next, term; } MarkerXlate;   /* 0x40A86 record */
const MarkerXlate marker_xlate_40a86[] = {           /* arcade 0x40A86, term 0xFF ends */
 {1,0x31,5,0},{2,0x33,4,0},{1,0x34,2,0},{2,0x34,1,0},{2,0x35,6,0},{1,0x38,0x0A,0},
 {1,0x39,3,0},{2,0x3b,0x0B,0},{1,0x3c,0x0C,0},{2,0x32,8,0},{1,0x36,9,0},
 {1,0x3e,0x0D,0},{2,0x3e,0x0D,0},{1,0x3f,0x0D,0},{2,0x3f,0x0D,0},
 {1,0x40,0x0E,0},{2,0x40,0x0E,0},{1,0x41,0x0E,0},{2,0x41,0x0E,0},
 {0x0D,0x40,1,0},{0x0D,0x41,2,0},{0x0E,0x3e,1,0},{0x0E,0x3f,2,0},{2,0x37,7,0xFF} };
uint8_t actor_marker_transition_40a60(uint8_t cur_state, uint8_t found_marker)
{
    const MarkerXlate *p = marker_xlate_40a86;
    while ((p->cur != cur_state || p->marker != found_marker) && p->term != 0xFF)
        p++;
    return p->next;
}

/*
 * ORIGINAL ARCADE PC: 0x00041D08  spawner config loader (from table 0x41D26)
 * Provenance: GHIDRA_RAW. Status: COMPLETE.
 * Loads a 7-byte config entry (indexed by state via 0x41336) into actor fields:
 * +0x08, +0x0D (next target char), +0x0E..+0x13.
 */
void actor_config_load_41d08(ActorRecord *a4, const uint8_t entry[7])
{
    a4->field_20 = entry[0];   /* +0x08 in arcade; here uses +0x08 group (see raw) */
    a4->target_char = entry[1];/* +0x0D next target marker char */
    a4->field_0e[0] = entry[2];/* +0x0E */
    a4->field_0e[1] = entry[3];/* +0x0F */
    a4->field_0e[2] = entry[4];/* +0x10 */
    a4->field_0e[3] = entry[5];/* +0x11 */
    a4->field_13 = entry[6];   /* +0x13 */
}

/* ---- scene / progression transition ---- */

/*
 * ORIGINAL ARCADE PC: 0x0003A7D2  scene-wipe / sub-round advance trigger
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * If micro-phase A5+0x10E8 == 7: checkpoint A5+0x1242 := A5+0x13E; A5+0x46 := 1;
 * master state A5+0x04 := 2; A5+0x104 := 1; sub-state A5+0x02 := 2. Else runs the
 * transition sequencer at 0x469E8. This is the proven 0x7E-door / mode-7 wipe path
 * (KF scene map): a collision tile of type 0x7E sets 0x10E8:=7 upstream.
 */
void scene_wipe_trigger_3a7d2(void)
{
    if (G.micro_10e8 == 7) {
        G.checkpoint_13b8 = G.progress_13e; /* A5+0x1242 := A5+0x13E (checkpoint) */
        /* A5+0x46 := 1; A5+0x04 (master state) := 2; A5+0x104 := 1; A5+0x02 := 2 */
        G.section_1242 = G.progress_13e;
        return;
    }
    /* else: jsr 0x469E8 transition sequencer (PARTIAL — see raw) */
}

/* ---- collision grid cell-address computation ---- */

/*
 * ORIGINAL ARCADE PC: 0x00053A2E  collision-grid cell address from indices
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Computes the arcade address into the 0x10DE00 grid from the current BG/FG scroll
 * (A5+0x10AE / A5+0x10B0, negated & masked to 0x1FF) plus the caller indices d1/d2.
 * Column: ((~scrollX+1)&0x1FF + d1)>>1 +8 &0xFC. Row: ((~scrollY+1)&0x1FF + d2)<<5
 * &0x3F00. addr = 0x10DE00 + col + row (the exact arithmetic is preserved in raw).
 */
uint32_t collision_cell_addr_53a2e(uint16_t scrollX_10ae, uint16_t scrollY_10b0,
                                   uint16_t d1, uint16_t d2)
{
    uint16_t col = (uint16_t)(((uint16_t)((scrollX_10ae ^ 0x1FF) + 1) & 0x1FF) + d1);
    col = (uint16_t)((col >> 1) + 8) & 0x00FC;
    uint16_t row = (uint16_t)(((uint16_t)((scrollY_10b0 ^ 0x1FF) + 1) & 0x1FF) + d2);
    row = (uint16_t)(row << 5) & 0x3F00;
    return COLLISION_GRID_BASE + col + row;
}

/* ---- boss trigger / component sync ---- */

/*
 * ORIGINAL ARCADE PC: 0x0004449E  boss trigger (record type by round)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Clears A5+0x13AC; selects boss record type = 0x444E0[round-1] = {0E,13,14,15,10,17};
 * round 6 -> block A5+0x648 comp 2, else block A5+0x708 comp 1; sets +0x06 rectype,
 * +0x1C=128, activates via 0x453A8, then setup 0x444E6.
 */
extern ActorRecord *blk_708(void);   /* A5+0x708 */
extern ActorRecord *blk_648(void);   /* A5+0x648 */
extern void boss_setup_444e6(ActorRecord *a4);
extern void paired_actor_activate_453a8(ActorRecord *a4);
void boss_trigger_4449e(void)
{
    uint8_t rt = boss_round_rectype_444e0[G.round - 1];
    ActorRecord *a4 = (G.round == 6) ? blk_648() : blk_708();
    a4->comp = (G.round == 6) ? 2 : 1;   /* +0x38 */
    a4->rec_type = rt;                   /* +0x06 */
    a4->timer = 128;                     /* +0x1C */
    paired_actor_activate_453a8(a4);
    boss_setup_444e6(a4);
}

/*
 * ORIGINAL ARCADE PC: 0x00042380  boss body -> component sync loop
 * Provenance: RECONSTRUCTED_FROM_68000. Status: PARTIAL.
 * Iterates the 5 boss components (block A5+0x5C8) and syncs facing (+0x02) from the
 * body, calling 0x43458 with (component_index + 13). The per-component motion detail
 * in 0x43458 is not fully traced.
 */
void boss_body_sync_42380(ActorRecord *body)
{
    for (int i = 0; i < 5; i++) {
        ActorRecord *c = blk_5c8_at(i);
        if (c->active == 0) continue;
        c->facing = body->facing;        /* +0x02 */
        arcade_43458(c, i + 13);         /* PARTIAL callee */
    }
}

/* ---- scripted-encounter dispatcher ---- */

/*
 * ORIGINAL ARCADE PC: 0x0004AB5C  scripted-encounter dispatcher (keyed on 0x13E)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: PARTIAL.
 * A cascade of `cmpiw #N, 0x13E; bcs default; beq handler` selecting a per-position
 * scripted handler; default (out of range) -> 0x4ABD8. The handler bodies (each a
 * one-shot flag + 0x45342/0x45CFC/0x4CD50-family spawn) are NOT all traced — the
 * historical Andy_4A000_4C700 doc marked this subsystem explicitly non-exhaustive.
 * Proven dispatch entries (0x13E -> handler PC):
 *   0x2F->0x4AE28, 0x30->0x4ADDC, 0x33->0x4ADAA, 0x34->0x4AD7C, 0x36->0x4AD5C,
 *   0x38->0x4AD2E, 0x3A->0x4ACF4, 0x3B->0x4ACDA, 0x3C->0x4AC6A, 0x3D->0x4AC4E,
 *   0x40->0x4AC14 ... (continues; deeper R4-R6 entries at 0x4B/0x4C not fully traced).
 */
void scripted_dispatch_4ab5c(void)
{
    switch (G.progress_13e) {          /* PARTIAL: representative proven entries */
    case 0x2F: /* -> 0x4AE28 */ break;
    case 0x30: /* -> 0x4ADDC */ break;
    case 0x33: /* -> 0x4ADAA */ break;
    case 0x34: /* -> 0x4AD7C */ break;
    case 0x36: /* -> 0x4AD5C */ break;
    case 0x38: /* -> 0x4AD2E */ break;
    case 0x3A: /* -> 0x4ACF4 */ break;
    case 0x3B: /* -> 0x4ACDA */ break;
    case 0x3C: /* -> 0x4AC6A */ break;
    case 0x3D: /* -> 0x4AC4E */ break;
    case 0x40: /* -> 0x4AC14 */ break;
    default:   /* -> 0x4ABD8 (no scripted encounter at this position) */ break;
    }
}
