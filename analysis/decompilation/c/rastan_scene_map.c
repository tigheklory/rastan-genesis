/* rastan_scene_map.c — CHECKPOINT H11
 * Semantic reconstruction of the scene / map / collision-marker source chain. NOT original Taito
 * source; byte-faithful control flow in raw/000503bc.c, raw/000559b2.c, raw/000563a6.c.
 *
 * PROVEN CHAIN (H11):
 *   progression A5+0x13E
 *     -> scene index   = byte[0x50EE0 + 0x13E]                          (0x503BC)
 *     -> section kind  = byte[0x50F6B + scene index]   (0 outdoor / !=0 castle = PHASE 2)
 *     -> A5+0x10C6 = &section_stream[scene index]  (advanced per column)
 *   per-round BACKGROUND map:  table 0x562CA[round] -> (ptr0 ROM src, ptr1 name-table dst)
 *     -> 0x563A6 decompresses the metatile stream into the name table.
 *   COLLISION / MARKER grid (0x10DE00):
 *     16 column descriptors A5+0x10D000 -> records A5+0x10D040 (0x55904)
 *       -> 0x55968/0x559B2 write, per row: grid_word = column_record[20 + subcol*2 + row*8]
 *       -> MARKER = grid_word >> 8  (read by 0x41180 -> 0x41362 materialization)
 *
 * SIX PHASE-2 (CASTLE) STARTS — statically proven from the section stream (round windows use the
 * code-proven ends R1..R6 = 0x16/0x2D/0x44/0x5B/0x72/0x89):
 *     R1 0x13E 0x11 (kind 1)   R2 0x2B (1)   R3 0x41 (1)
 *     R4 0x5A (1)              R5 0x6E (2)   R6 0x85 (2)
 *
 * REMAINING BLOCKER: per-scene MARKER enumeration needs the ROM population of A5+0x10D000 (each
 * column's collision-record pointer) — that populator/table is the exact next dependency. Until it
 * is decoded the H10 materialized actors cannot be round-pinned, so they stay ROUND PENDING (not
 * fabricated). See docs/design/Andy_h11_phase2_marker_map_decompilation.md.
 */
#include "rastan_arcade_types.h"

extern unsigned char rom_u8(unsigned addr);

/* 0x503BC: 0x13E -> section kind (0 = outdoor phase 1, != 0 = castle phase 2). */
unsigned char scene_section_kind(unsigned prog_13e){
    return rom_u8(0x50F6B + rom_u8(0x50EE0 + prog_13e));
}

/* per-round Phase-2 (castle) start 0x13E, first nonzero section kind within the round window. */
unsigned phase2_start(unsigned round_start_13e, unsigned round_end_13e){
    for (unsigned p = round_start_13e; p <= round_end_13e; ++p)
        if (scene_section_kind(p) != 0) return p;
    return 0xFFFF;   /* none (all outdoor) */
}
