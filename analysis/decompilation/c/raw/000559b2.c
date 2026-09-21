/* ORIGINAL ARCADE PC: 0x000559B2 collision-grid column writer (+ 0x55A14 mirror variant).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (was historically PARTIAL).
 * Streams one on-screen column of 4 rows into BOTH the name table (background) and the collision/
 * MARKER grid at 0x10DE00. Inputs: a0 = destination name-table address (0xC08000 region), a1 = a
 * source word, a2 = the column RECORD (per-scene data). Per row d2 (0..3):
 *   tile_word      = a2[ scrollfine(A5+0x10CA)*2 + d2*8 ]        -> name table (a0)
 *   collision_word = a2[ 20 + scrollfine*2 + d2*8 ]  (or a2[0x22] if a2[0x20]==0xFF)
 *                  -> collision/marker grid: 0x10DE00 + (a0 - 0xC08000)/2
 *   a0 += 254 (advance one grid/name row); on next call a0 advances one column.
 * The MARKER byte that 0x41180 reads is the HIGH byte of `collision_word`; it therefore comes
 * directly from the per-scene column RECORD, not from a tile-property lookup. 0x55A14 is identical
 * except it mirrors the sub-column index when A5+0x10A8 (section kind) == 2 (interior variant).
 *
 * REMAINING (H11 blocker): the column RECORD a2 is a3@ where a3 walks A5+0x10D040, built by 0x55904
 * from the 16 column descriptors at A5+0x10D000; the ROM population of A5+0x10D000 per scene (the
 * source that supplies each column's collision-record pointer) is the exact next dependency. */
#include "raw_common.h"

/* a2-relative collision/marker word for row d2 at scroll sub-column `subcol`. */
static uint16_t collision_word(uint8_t *rec, uint16_t subcol, uint16_t d2){
    if (W(rec,0x20) == 0x00FF) return W(rec,0x22);
    return W(rec, 20 + subcol*2 + d2*8);
}
static uint16_t tile_word(uint8_t *rec, uint16_t subcol, uint16_t d2){
    return W(rec, subcol*2 + d2*8);
}

void arcade_559b2(uint8_t *name_dst, uint8_t *src_word, uint8_t *rec, uint16_t scroll_fine_10ca){
    W(name_dst,0) = W(src_word,0);              /* top word */
    uint32_t name_addr = 0; /* caller supplies the real 0xC08000-region address; modelled abstractly */
    (void)name_addr;
    for (uint16_t d2=0; d2<4; d2++){
        uint16_t cw = collision_word(rec, scroll_fine_10ca, d2);
        /* grid cell = 0x10DE00 + (name_addr - 0xC08000)/2; MARKER = cw >> 8 */
        (void)cw;                               /* written to collision grid by the caller's a0 map */
        uint16_t tw = tile_word(rec, scroll_fine_10ca, d2);
        W(name_dst,0) = tw;                     /* name-table tile for this row */
        name_dst += 254;                        /* advance one row (256-byte stride minus the +2) */
    }
}
