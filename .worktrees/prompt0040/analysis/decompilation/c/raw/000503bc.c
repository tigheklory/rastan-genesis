/* ORIGINAL ARCADE PC: 0x000503BC map-column source resolver (0x13E -> section -> map ptr).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Resolves the current progression (A5+0x13E) to the map-column source pointer A5+0x10C6, via a
 * double-indirection through two ROM tables:
 *     a1 = 0x50EE0 + A5+0x13E ;  idx = byte[a1]           (0x50EE0 = per-0x13E scene index)
 *     A5+0x10C6 = 0x50F6B + idx                            (0x50F6B = section-kind stream base)
 * byte[A5+0x10C6] (i.e. byte[0x50F6B + idx]) is the per-column SECTION KIND consumed by 0x558F0 /
 * 0x55938 into A5+0x10D0A8: 0 = outdoor (phase 1), != 0 = castle / interior (phase 2). The
 * per-round Phase-2 (castle) start is therefore the first 0x13E in the round whose section kind is
 * nonzero (see the enumerator tools/analysis/decode_rastan_scene_markers.py). This is the proven
 * static Phase-1 -> Phase-2 selector; it complements the 0x7E collision-door trigger. */
#include "raw_common.h"
extern uint8_t rom_byte(uint32_t addr);      /* byte from maincpu image */

/* returns the map-column source pointer stored to A5+0x10C6. */
uint32_t arcade_503bc(uint16_t prog_13e){
    uint8_t scene_index = rom_byte(0x50EE0u + prog_13e);
    return 0x50F6Bu + scene_index;           /* A5+0x10C6 = &section_kind_stream[scene_index] */
}
/* the section kind (0 outdoor / !=0 castle) for a given 0x13E. */
uint8_t section_kind_for_13e(uint16_t prog_13e){
    return rom_byte(0x50F6Bu + rom_byte(0x50EE0u + prog_13e));
}
