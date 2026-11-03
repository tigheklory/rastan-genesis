/* ORIGINAL ARCADE PC: 0x000453A2 paired-actor activate. GHIDRA_RAW(normalized). COMPLETE. */
#include "raw_common.h"
extern void arcade_4543e(uint8_t*);
void arcade_453a2(uint8_t *r){ W(r,0x1c)=1; B(r,0x00)=1; B(r,0x05)=3; W(r,0x1a)=0x180; arcade_4543e(r); }
