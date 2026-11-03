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
 *   COLLISION / MARKER grid (0x10DE00) — H13 EXACT mapping (blocker CLOSED, see raw/000559b2.c):
 *     0x502CC   0x10D000[col] = 0x1691C + col*0x22C0 + (A5+0x13E)*0x40         (col 0..15)
 *     0x55904   per descriptor entry: word0 (@base)   -> 0x10D080[col] (tile word to name table)
 *                                     word1 (@base+2) -> 0x10D040[col] = 16-bit ROM pointer to the
 *                                                        collision RECORD ("col_record")
 *     0x558A2   strip a5@(0x10CA) cycles 0..3; every 4 strips the 16 pointers advance +4 (next
 *               4-byte entry) and 0x55904 rebuilds; scene a5@(0x13E)++ after 16 entries (0x40 page)
 *     0x559B2   grid_word = (col_record[0x20]==0x00FF) ? col_record[0x22]                (uniform)
 *                                                      : col_record[20 + strip*2 + cell*8]
 *               strip = a5@(0x10CA) 0..3, cell = d2 0..3   (20 == decimal 0x14; each record = 4x4)
 *       -> MARKER = grid_word >> 8  (read by 0x41294/0x41180 -> 0x41362 materialization)
 *
 * SIX PHASE-2 (CASTLE) STARTS — statically proven from the section stream (round windows use the
 * code-proven ends R1..R6 = 0x16/0x2D/0x44/0x5B/0x72/0x89):
 *     R1 0x13E 0x11 (kind 1)   R2 0x2B (1)   R3 0x41 (1)
 *     R4 0x5A (1)              R5 0x6E (2)   R6 0x85 (2)
 *
 * H13 CLOSED the H11 blocker: the descriptor->record->grid-cell mapping is fully proven (above),
 * and tools/analysis/decode_rastan_scene_markers.py now emits the record-accurate per-round marker
 * enumeration + rosters. See docs/design/Andy_h13_collision_cell_layout_phase2_rosters.md.
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

/* ===== CHECKPOINT H12: A5+0x10D000 column-descriptor populator (0x502CC) ===================
 * Closes the H11 blocker: descriptor(col, scene) = 0x1691C + col*0x22C0 + (A5+0x13E)*0x40, for
 * col 0..15. These ROM pointers feed 0x55904/0x559B2, which write the collision/marker grid at
 * 0x10DE00 (marker = collision word high byte, read by 0x41180). The descriptor data is confirmed
 * to contain H6-range markers (0x3A/0x3B/0x4F..0x51). Reconciled with Cody Build 0116/0117 (the
 * same table is Genesis WRAM 0x00FF1000; arcade authority = 0x10D000 / ROM base 0x1691C). */
extern unsigned char rom_u8(unsigned addr);
unsigned column_descriptor_addr(unsigned col, unsigned prog_13e){
    return 0x1691Cu + col*0x22C0u + prog_13e*0x40u;   /* 0x502CC */
}

/* ===== CHECKPOINT H13: exact ROM-descriptor -> collision-record -> grid marker ==================
 * The 0x40-byte descriptor page for (col, scene) holds 16 four-byte entries {word0, word1}. word1
 * (at entry+2) is a 16-bit ROM pointer to the collision RECORD read by 0x559B2. */
extern unsigned short rom_u16(unsigned addr);

/* word1 of descriptor entry `e` (0..15) = ROM pointer to that column's collision record. */
unsigned collision_record_ptr(unsigned col, unsigned prog_13e, unsigned entry){
    unsigned base = column_descriptor_addr(col, prog_13e) + entry*4;   /* 0x558CE +4 advance */
    return rom_u16(base + 2);                                          /* 0x55904 movew a4@(2) */
}

/* 0x559B2 record read: strip (a5@0x10CA) 0..3, cell (d2) 0..3 -> collision word; MARKER = high byte.
 * Sentinel col_record[0x20]==0x00FF selects the uniform alternate col_record[0x22]. */
unsigned collision_grid_word(unsigned rec, unsigned strip, unsigned cell){
    if (rom_u16(rec + 0x20) == 0x00FF) return rom_u16(rec + 0x22);      /* 0x559B6/0x559D4 */
    return rom_u16(rec + 20 + strip*2 + cell*8);                       /* 0x559CE (20 = 0x14) */
}
unsigned collision_marker(unsigned rec, unsigned strip, unsigned cell){
    return collision_grid_word(rec, strip, cell) >> 8;                 /* 0x41296 lsrw #8 */
}
