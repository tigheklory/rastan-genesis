/* ORIGINAL ARCADE PC: 0x00045B18 scripted bat-group creator.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source.
 *
 * The caller supplies A4 and D0 for a leading rec_type-12 actor.  Unless
 * progression is 0x58, the routine clears and recreates one Large Bat in the
 * fixed A5+0x06C8 slot and one to three Small Bats in A5+0x09C8/0988/0948.
 * Round 2 substitutes rec_type 0x12/comp 1 in the 0x06C8 slot; every other
 * round uses rec_type 0x0A/comp 0.  Small-bat count grows at rounds 4 and 6.
 */
#include "raw_common.h"

extern void arcade_4092e(uint8_t *r);
extern void arcade_4543e(uint8_t *r);
extern void arcade_45cfc(uint8_t *r);
extern void arcade_3a0ec(uint8_t cue);

extern uint8_t *g_a5;

static void bat_place_45be8(uint8_t *r)
{
    W(r,0x16)=W(g_a5,0x071e); W(r,0x32)=W(g_a5,0x071e);
    W(r,0x1a)=(uint16_t)(W(g_a5,0x0722)+0x14);
    W(r,0x30)=W(r,0x1a);
    B(r,0x27)|=0x80;                 /* orientation bit only; bit 6 stays clear */
}

static void make_bat(uint8_t *r, uint8_t rec_type, uint8_t comp,
                     uint8_t comp_index)
{
    arcade_4092e(r);                 /* complete 0x40-byte identity clear */
    B(r,0x21)=comp_index;
    B(r,0x06)=rec_type;
    B(r,0x38)=comp;
    arcade_4543e(r);                 /* base/selector/config from 0x45592 */
    arcade_45cfc(r);                 /* active=1, state=3, timer=1 */
    bat_place_45be8(r);
}

void arcade_45b18(uint8_t *lead, uint16_t d0)
{
    W(lead,0x1a)=d0;
    B(lead,0x06)=0x0c; arcade_4543e(lead); B(lead,0x25)=B(g_a5,0x0254);
    B(lead,0x01)=(uint8_t)(B(lead,0x01)+B(lead,0x25)); B(lead,0x26)=1;
    arcade_45cfc(lead);
    if (W(g_a5,0x013e)==0x58) return;

    uint8_t round=B(g_a5,0x0118);
    uint16_t tick=W(g_a5,0x0200);
    make_bat(g_a5+0x06c8, round==2 ? 0x12 : 0x0a,
             round==2 ? 1 : 0, (uint8_t)tick);
    make_bat(g_a5+0x09c8, 0x0b, 0, (uint8_t)(tick+1));
    if (round>=4) make_bat(g_a5+0x0988, 0x0b, 0, (uint8_t)(tick+2));
    if (round>=6) make_bat(g_a5+0x0948, 0x0b, 0, (uint8_t)(tick+3));
    arcade_3a0ec(0x15);
}
