/* ORIGINAL ARCADE PC: 0x000563A6 PC080SN text/layout stream writer.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Walks an uncompressed ROM byte stream at A0 into the name-table destination A1. Byte stream:
 *   0x00        -> end (rts)
 *   0xFF        -> saved row base += 0x200 bytes; because a PC080SN row is 64 four-byte cells
 *                  (0x100 bytes), this advances TWO 8-pixel hardware rows
 *   otherwise   -> emit: a1[0] = d1 (attribute), a1[1] = glyph_alias(d0)
 * glyph_alias (0x563CE): a small remap for bytes 0x21/0x22/0x27/0x28/0x29/0x2C/0x2D/
 *   0x3F -> tile codes 0x2744..0x274B; other bytes pass through as the tile code.
 * Item-description callers are 0x56032 (A0=0x5672A, A1=0xC00828, D1=0) and 0x56056
 * (A0=0x5697E, A1=0xC00028, D1=0). Other callers also use this shared writer. */
#include "raw_common.h"
extern uint8_t rom_byte(uint32_t addr);

static uint16_t glyph_alias(uint8_t d0){
    switch(d0){
        case 0x21: return 0x2744; case 0x22: return 0x2745; case 0x27: return 0x2746;
        case 0x28: return 0x2747; case 0x29: return 0x2748; case 0x2C: return 0x2749;
        case 0x2D: return 0x274A; case 0x3F: return 0x274B;
        default:   return d0;     /* pass-through tile code */
    }
}

/* Write ROM text/layout into name-table dst; attr is the per-cell attribute word D1. */
void arcade_563a6(uint32_t src, uint16_t *dst, uint16_t attr){
    uint16_t *row = dst;
    for(;;){
        uint8_t d0 = rom_byte(src++);
        if (d0 == 0x00) return;                 /* end */
        if (d0 == 0xFF){ row += 0x100; dst = row; continue; }  /* next row (+0x200 bytes) */
        *dst++ = attr;
        *dst++ = glyph_alias(d0);
    }
}
