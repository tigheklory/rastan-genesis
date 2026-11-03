/* ORIGINAL ARCADE PC: 0x0004543E record-type template loader. GHIDRA_RAW(normalized). COMPLETE. */
#include "raw_common.h"
extern const uint8_t rt_45592[]; extern void arc_453d6(uint8_t*);
void arcade_4543e(uint8_t *r){ int i=(int)(int16_t)(int8_t)(B(r,0x06)-8)*8; const uint8_t*t=rt_45592+i;
    W(r,0x1e)=*(const uint16_t*)t; B(r,0x3a)=t[2]; B(r,0x01)=t[3];
    W(r,0x28)=*(const uint16_t*)(t+4); W(r,0x2c)=*(const uint16_t*)(t+6); arc_453d6(r); }
