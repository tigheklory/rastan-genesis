/* ORIGINAL ARCADE PC: 0x00045342 paired Flying-Demon init (17 callers). GHIDRA_RAW(normalized). COMPLETE.
 * Fixed slots 0x508/0x548; rec_type 8/9 by A5+0xC5A. */
#include "raw_common.h"
extern uint8_t *blk508_0,*blk508_1; extern uint16_t g_var_c5a; extern void arcade_453a2(uint8_t*);
void arcade_45342(void){ if (B(blk508_1,0x00)!=0) return; uint8_t rt=(g_var_c5a==0)?8:9;
    B(blk508_0,0x06)=rt; B(blk508_1,0x06)=rt; arcade_453a2(blk508_0); arcade_453a2(blk508_1); arc_3a0ec(0); }
