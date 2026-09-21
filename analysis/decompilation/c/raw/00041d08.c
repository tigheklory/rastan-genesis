/* ORIGINAL ARCADE PC: 0x00041D08 spawner config loader (table 0x41D26). GHIDRA_RAW. COMPLETE.
 * 7-byte entry -> a4@(0x08),a4@(0x0d),a4@(0x0e),a4@(0x0f),a4@(0x10),a4@(0x11),a4@(0x13). */
#include "raw_common.h"
void arcade_41d08(uint8_t *r, const uint8_t e[7]){
    B(r,0x08)=e[0]; B(r,0x0d)=e[1]; B(r,0x0e)=e[2]; B(r,0x0f)=e[3];
    B(r,0x10)=e[4]; B(r,0x11)=e[5]; B(r,0x13)=e[6]; }
