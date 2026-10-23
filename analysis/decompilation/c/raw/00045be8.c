/* ORIGINAL ARCADE PC: 0x00045BE8 fixed bat placement helper.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source. */
#include "raw_common.h"

extern uint8_t *g_a5;

void arcade_45be8(uint8_t *r)
{
    W(r,0x16)=W(g_a5,0x071e);
    W(r,0x32)=W(g_a5,0x071e);
    W(r,0x1a)=(uint16_t)(W(g_a5,0x0722)+0x14);
    W(r,0x30)=W(r,0x1a);
    B(r,0x27)|=0x80;
}
