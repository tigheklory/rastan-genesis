/* ORIGINAL ARCADE PC: 0x0003A7D2 scene-wipe / sub-round advance. RECONSTRUCTED_FROM_68000. COMPLETE.
 * if (A5+0x10E8==7){ A5+0x1242:=A5+0x13E; A5+0x46:=1; A5+0x04:=2; A5+0x104:=1; A5+0x02:=2; return; }
 * else jsr 0x469E8 (transition sequencer). */
#include "raw_common.h"
extern int arcade_469e8(void);
void arcade_3a7d2(void){
    if (g_micro10e8==7){ g_sec1242=g_prog13e; g_a5_46=1; g_a5_04=2; g_a5_104=1; g_a5_02=2; return; }
    arcade_469e8();
}
