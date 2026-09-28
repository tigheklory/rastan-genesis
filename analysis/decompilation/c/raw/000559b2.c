/* ORIGINAL ARCADE PC: 0x000559B2 collision/marker grid producer (BG pass) + 0x00055A14 (FG pass).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE. Closes the H11/H12 blocker: the EXACT bytes of one
 * ROM descriptor that become the collision grid cell consumed as col_record[20 + strip*2 + cell*8].
 *
 * PROVEN CHAIN (all from build/maincpu.disasm.txt, authoritative arcade program):
 *   0x502CC  0x10D000[col] = 0x1691C + col*0x22C0 + (A5+0x13E)*0x40         (col 0..15)
 *   0x558A2  strip a5@(0x10CA) cycles 0..3; every 4 strips 0x558C6 advances ALL 16 descriptor
 *            pointers +4 (next 4-byte entry) and calls 0x55904 to rebuild records; 0x558E0
 *            advances scene a5@(0x13E) after 16 entries (16*4 = 0x40 = the per-scene page stride).
 *   0x55904  per column: word0 = @descriptor       -> 0x10D080[col]  (name-table tile word)
 *                        word1 = @(descriptor+2)    -> 0x10D040[col]  = 16-bit ROM pointer to the
 *                                                      collision RECORD ("col_record").
 *   0x55968  BG dispatch: a0 = a5@(0x10A0) dest cursor; for the 16 columns: a2 = 0x10D040[col];
 *            bsr 0x559B2; save advanced a0 back to a5@(0x10A0).
 *   0x559B2  per column, for cell d2 = 0..3:
 *              [a0] = word0                                            (0x559B4 tile to dest)
 *              if col_record[0x20] == 0x00FF:  cw = col_record[0x22]   (uniform-fill sentinel)
 *              else:                           cw = col_record[20 + strip*2 + cell*8]  (per cell)
 *              grid[0x10DE00 + (a0 - 0xC08000)/2] = cw                 (0x559EC: the collision word)
 *              a0 += 2; [a0] = col_record[0 + strip*2 + cell*8]; a0 += 254   (second dest word/row)
 *   0x41294  CONSUMER reads a grid word and takes MARKER = word >> 8 (high byte), classified by the
 *            0x41362 route table (see rastan_actor_materialization.c / H6). 20 == decimal, = 0x14
 *            hex; the control/sentinel word sits at hex offset 0x20, the uniform alternate at 0x22.
 *
 * So each col_record is a compact 4x4 grid: strip (a5@0x10CA) 0..3 selects the horizontal slice,
 * cell (d2) 0..3 the four rows in view; byte offsets 0x14..0x32. The 0x55A14 FG variant is the same
 * producer with a vertical/parity reflection of the strip index (0x55A36 notw/andi #3) selected by
 * a5@(0x10A8) != 2, and it also writes a companion word 0x100 bytes below the cell.
 *
 * This is arcade STATIC provenance for the marker source; on Genesis the 0x0010DExx grid and the
 * 0x0010D0xx descriptor mirror are KF-036 WRAM (A5=0xFF0000) — Cody's rebase, not arcade semantics. */
#include "raw_common.h"

extern uint16_t rom_u16(uint32_t addr);   /* big-endian ROM word */

/* one collision RECORD access (0x559B2 core): strip 0..3, cell 0..3 -> collision word. */
static uint16_t col_record_word(uint32_t rec, unsigned strip, unsigned cell){
    if (rom_u16(rec + 0x20) == 0x00FF)          /* 0x559B6/0x559BC sentinel */
        return rom_u16(rec + 0x22);             /* 0x559D4 uniform alternate */
    return rom_u16(rec + 20 + strip * 2 + cell * 8);   /* 0x559CE lea a2@(20,d7:w) */
}

/* 0x559B2 BG collision/marker producer for one column. dest = arcade tilemap cursor (a5@0x10A0);
 * rec = 0x10D040[col] (= descriptor.word1); word0 = 0x10D080[col]; strip = a5@(0x10CA). Returns the
 * advanced dest cursor. Writes the collision word (marker in high byte) into the 0x10DE00 grid. */
uint32_t arcade_559b2(uint32_t dest, uint32_t rec, uint16_t word0, unsigned strip,
                      uint16_t *grid /* 0x10DE00 base as word array */){
    for (unsigned cell = 0; cell < 4; cell++){          /* 0x559B4..0x55A10, d2 = 0..3 */
        /* tile word to dest (0x559B4 movew a1@, a0@) */
        /* (dest tilemap write is modeled by the caller's VRAM; omitted here) */
        uint16_t cw = col_record_word(rec, strip, cell);
        uint32_t gidx = (dest - 0xC08000u) >> 1;        /* 0x559DA..0x559E4 */
        grid[gidx] = cw;                                /* 0x559EC movew d0, (a6) */
        dest += 2;                                      /* 0x559EE */
        /* companion cell word: col_record[0 + strip*2 + cell*8] (0x559FC lea a2@(0,d7:w)) */
        (void)rom_u16(rec + 0 + strip * 2 + cell * 8);  /* written to dest by 0x55A02 */
        dest += 254;                                    /* 0x55A04 addal #254,a0 (next row) */
        (void)word0;
    }
    return dest;                                        /* 0x55A12 rts */
}

/* MARKER decode as the consumer 0x41294 performs it: grid word high byte. */
unsigned collision_marker_of(uint16_t grid_word){ return grid_word >> 8; }   /* 0x41296 lsrw #8 */
