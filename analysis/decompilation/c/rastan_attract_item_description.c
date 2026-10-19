/* rastan_attract_item_description.c — the SCROLLING ITEM-DESCRIPTION attract screen.
 * Semantic reconstruction. NOT original Taito source; byte-faithful control flow in raw/0005607c.c.
 * The 68000 binary is final authority.
 *
 * ATTRACT STATE: A5@(0)=2, A5@(2)=2, A5@(4) in {4,6} (two sub-pages of the same screen).
 *
 * WHAT IT IS: a continuously, vertically SCROLLING list of item descriptions (AXE / HAMMER /
 * FIRE SWORD / SHIELD / MANTLE / ARMATURE / MEDICINE / POISON / GOLD SHEEP / JEWEL ...). The list is
 * a tall logical BG tilemap; the viewport scrolls up through it and loops.
 *
 * COMPOSITION (proven):
 *   - BG text/layout (Plane B / PC080SN BG): written ONCE per loop from an uncompressed byte stream
 *     by 0x563A6 (raw/000563a6.c; 0xFF=next row, 0=end) into the C-window
 *     (0xC00828 / 0xC00028). Item-description TEXT is ROM-sourced from 0x0005672A / 0x0005697E
 *     through the shared PC080SN text writer 0x563A6 (glyph-alias subroutine 0x563CE:
 *     0x21->0x2744 ... 0x3F->0x274B). Static content; NOT regenerated per frame. The previously
 *     cited original PCs 0x565A6/0x565CE are data, not these routines; those names came from a
 *     historical shifted Genesis correspondence.
 *     The exact destinations are 0xC00828 = row 4 / column 10 for page A and 0xC00028 = physical
 *     row 0 / column 10 for page B. Page B is installed after 12 row crossings and therefore owns
 *     logical ring rows 32..38, not logical rows 0..6.
 *   - Item ICONS (PC090OJ sprites): copied as 8-byte descriptor records by 0x56114 from a ROM table
 *     (0x56226 / 0x562B0) to object RAM 0xD00170 at (re)build time. Attribute nibbles 3/0 combine
 *     with sprite-control colbank 0x30 (control 0x0060) as effective banks 0x33/0x30.
 *   - SCROLL: the shared gameplay PC080SN scroll/stream machinery. Per tick (0x5607C), every 4th
 *     frame: BG vertical scroll A5+0x10EE -= 1 (wrap mod 512); every 8 units a new row-region is
 *     advanced/blanked (0x560DA) and the dest cursor A5+0x10A0 wraps in the C-window; at the wrap
 *     boundary (cursor == 0xC00F00) the page is re-decompressed (0x56056). The scroll is committed to
 *     the PC080SN scroll registers by 0x55AB4 (A5+0x10EC->0xC40000 FG X, A5+0x10AE->0xC40002 FG Y,
 *     A5+0x10EE->0xC20000 BG Y). FG scroll accumulators (A5+0x10AE/0x10B0) are held 0 on this screen.
 *   - A per-item dwell timer walks the 8-byte sprite descriptors at 0xD00170 (countdown field +2;
 *     at 16, clear field +4) up to the live cursor A5+0x141C.
 *
 * ENTRY vs PER-FRAME:
 *   ENTRY-ONLY / PER-LOOP: BG text/layout write (0x563A6), icon sprite copy (0x56114) — once per
 *     screen entry and once per scroll-loop wrap.
 *   PER-FRAME SEMANTIC: scroll decrement + scroll-register commit (0x55AB4) + dwell timer.
 *   PER-SCROLL-STEP (every 8 units): one new BG row-region (0x560DA).
 *   There is NO per-frame text re-render and NO per-frame full-plane rebuild in the ARCADE: most
 *     frames are a scroll-register write + timer. (The Genesis translation currently re-stages/re-DMAs
 *     the streamed rows through genesistan_hook_tilemap_bg_fill, and translates the 0xC20000/0xC40000
 *     scroll writes to native VDP scroll — see the design report.)
 *
 * This screen's scroll/stream/decompress functions are SHARED with gameplay (H22 world_stream,
 * H23 world_scroll, H11 scene_map). Only arcade_5607c / 0x560DA / 0x56114 / the 0x56032/0x56056
 * entries are attract-item-specific. See
 * docs/design/Cody_build0454_arcade_exact_item_description.md.
 */
#include "rastan_arcade_types.h"
