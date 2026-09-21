/* ORIGINAL ARCADE PC: 0x000563A6 background tilemap decompressor.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Decompresses a per-round map stream (a0 = ROM source from the per-round table 0x562CA[round]:
 * ptr0) into the name-table destination (a1 = 0xC00Cxx region, ptr1). Byte stream:
 *   0x00        -> end (rts)
 *   0xFF        -> next column: a2 += 0x200; a1 = a2
 *   otherwise   -> emit: a1[0] = d1 (attribute), a1[1] = metatile_to_tile(d0)
 * metatile_to_tile (0x563CE): a small remap for control bytes 0x21/0x22/0x27/0x28/0x29/0x2C/0x2D/
 *   0x3F -> tile codes 0x2744..0x274B; other bytes pass through as the tile code.
 * This produces the BACKGROUND graphics only; the collision/MARKER grid is written separately by
 * 0x559B2 from the per-scene column records. The per-round source pointers are:
 *   R1 0x0565xx  R2 0x0565xx  ...  (table 0x562CA, ptr0 per round). */
#include "raw_common.h"
extern uint8_t rom_byte(uint32_t addr);

static uint16_t metatile_to_tile(uint8_t d0){
    switch(d0){
        case 0x21: return 0x2744; case 0x22: return 0x2745; case 0x27: return 0x2746;
        case 0x28: return 0x2747; case 0x29: return 0x2748; case 0x2C: return 0x2749;
        case 0x2D: return 0x274A; case 0x3F: return 0x274B;
        default:   return d0;     /* pass-through tile code */
    }
}

/* decompress from ROM src into name-table dst; attr = the per-cell attribute word (d1). */
void arcade_563a6(uint32_t src, uint16_t *dst, uint16_t attr){
    uint16_t *col = dst;
    for(;;){
        uint8_t d0 = rom_byte(src++);
        if (d0 == 0x00) return;                 /* end */
        if (d0 == 0xFF){ col += 0x100; dst = col; continue; }  /* next column (+0x200 bytes) */
        *dst++ = attr;
        *dst++ = metatile_to_tile(d0);
    }
}
