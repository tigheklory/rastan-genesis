/* ORIGINAL ARCADE PC: 0x000502CC A5+0x10D000 column-descriptor populator (PC080SN column source).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE. Closes the H11 blocker (who fills A5+0x10D000).
 *
 * Fills the 16 live column-descriptor pointers at A5+0x1000 (arcade 0x10D000) from ROM, keyed by the
 * current progression A5+0x13E:
 *     d1 = A5+0x13E; d1 *= 0x40                       (per-scene stride 0x40 bytes)
 *     A5+0x1000 = 0x1691C + d1                        (column 0)
 *     A5+0x1004 = 0x18BDC + d1                        (column 1)
 *     A5+0x1008 = 0x1AE9C + d1                        (column 2)
 *     ...        = 0x1691C + col*0x22C0 + d1          (column col, stride 0x22C0 between columns)
 * i.e. descriptor(col, scene) = 0x1691C + col*0x22C0 + (A5+0x13E)*0x40, for col = 0..15.
 *
 * The pointed-to ROM data (e.g. 0x1691C) is the per-column PC080SN tilemap/collision column source
 * (word pairs). The collision/marker grid at 0x10DE00 is written from these columns by 0x55904 /
 * 0x559B2; the HIGH byte of the collision word = the materialization marker read by 0x41180. The
 * scanned descriptor data DOES contain markers in the H6 ranges (0x3A/0x3B/0x4F..0x51 etc.),
 * confirming this is the marker source.
 *
 * GENESIS NOTE (Cody Build 0116/0117, reconciled — NOT arcade semantics): on Genesis this table is
 * KF-036 WRAM at 0x00FF1000 (A5=0xFF0000); the raw-literal 0x0010D0xx accessors were rebased and the
 * ROM descriptor source-pointer values relocated (+0x200 arcade_copy delta). Arcade authority here
 * is the ORIGINAL address 0x10D000 / ROM base 0x1691C. */
#include "raw_common.h"
extern uint32_t *g_col_desc_1000;   /* A5+0x1000: 16 column-descriptor pointers */

/* per-column ROM base for the descriptor source (0x1691C + col*0x22C0). */
static uint32_t column_base(unsigned col){ return 0x1691Cu + (uint32_t)col * 0x22C0u; }

void arcade_502cc(uint16_t prog_13e){
    uint32_t scene = (uint32_t)prog_13e * 0x40u;
    for (unsigned col = 0; col < 16; col++)
        g_col_desc_1000[col] = column_base(col) + scene;
}
