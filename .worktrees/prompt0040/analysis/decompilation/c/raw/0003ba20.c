/* ORIGINAL ARCADE PC: 0x0003BA20 scene sprite-palette load (+ 0x3BA56 line convert).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 *
 * 0x3BA20: loads the 32-line working sprite palette (A5+0x1600) for the current round:
 *     a1 = 0x3BA88 + (round-1)*32   (per-round nibble->pool index table, 32 entries)
 *     for line 0..31: pool = a1[line]; 0x3BA56(pool) converts pool's 16 ROM colours -> A5+0x1600.
 * 0x3BA56: a3 = 0x4FD02 + pool*32; for 16 colours convert the ROM word to the hardware CRAM word:
 *     CRAM = (nibble0 << 11) | (nibble1 << 6) | (nibble2 << 1)      (bit interleave; see 0x59ADE)
 *     where the ROM word is 0x0RGB with nibble2=R, nibble1=G, nibble0=B (channels preserved).
 *
 * 0x3B9F8 is a separate cold-start CLCS initializer, represented in raw/0003b9f8.c.
 * 0x45D7C/0x45DC4 copy in the opposite direction from the prior prose: 0x3A2D0 is
 * A0(source)->A1(destination), so they publish this working table to physical CLCS lines
 * 0..31 and 48..79. PC090OJ bank 0x3F therefore receives working line 15 exactly. */
#include "raw_common.h"
extern uint8_t g_round;                     /* A5+0x118 */
extern uint16_t rom_pal_word(uint32_t addr);/* big-endian ROM palette word */
extern uint16_t *g_sprite_pal_1600;         /* A5+0x1600 working sprite palette (32 lines x 16) */

/* ROM palette word -> hardware CRAM word (exact 0x3BA56/0x59ADE interleave). */
static uint16_t rom_to_cram(uint16_t w){
    uint16_t n2 = (w >> 8) & 0xF, n1 = (w >> 4) & 0xF, n0 = w & 0xF;
    return (uint16_t)((n0 << 11) | (n1 << 6) | (n2 << 1));
}
/* 0x3BA56: convert one pool's 16 colours into working palette line `line`. */
void arcade_3ba56(uint16_t line, uint8_t pool){
    uint32_t src = 0x4FD02u + (uint32_t)pool*32;
    for (int i=0;i<16;i++)
        g_sprite_pal_1600[line*16 + i] = rom_to_cram(rom_pal_word(src + i*2));
}
/* 0x3BA20: load all 32 lines for the round from the per-round pool-index table. */
void arcade_3ba20(void){
    uint32_t tbl = 0x3BA88u + (uint32_t)(g_round-1)*32;
    for (uint16_t line=0; line<32; line++){
        uint8_t pool = (uint8_t)rom_pal_word(tbl + line) >> 8; /* byte read */
        arcade_3ba56(line, pool);
    }
}
