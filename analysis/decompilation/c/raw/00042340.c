/* ORIGINAL ARCADE PC: 0x00042340. RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * A4 is A5+0x648. 0x3A2D0's forward overlapping copy repeats this 0x40-byte
 * primary record into A5+0x688, +0x6C8, and +0x708. */
#include "raw_common.h"
extern void arcade_3a2d0(const uint16_t *, uint16_t *, uint16_t);
extern void arcade_423f4(void);
extern uint16_t g_a5_026e;
void arcade_42340(uint8_t *primary_648)
{
    W(primary_648,0x16)=304; W(primary_648,0x1a)=232; B(primary_648,0x05)=0x10;
    arcade_3a2d0((const uint16_t *)primary_648,(uint16_t *)(void *)(primary_648+0x40),0x60);
    arcade_423f4();
    g_a5_026e=1;
}
