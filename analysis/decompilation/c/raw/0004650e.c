/* ORIGINAL ARCADE PC: 0x0004650E
 * Ghidra 12 selected-function decompile, normalized inventory. PARTIAL.
 * Establishes the round branch; individual materialized-actor tails remain unresolved.
 */
#include <stdint.h>
extern uint8_t g_round;
extern void round1_materialized_dispatch(void),round2_materialized_dispatch(void);
extern void round3_materialized_dispatch(void),round4_materialized_dispatch(void);
extern void round5_materialized_dispatch(void),round6_materialized_dispatch(void);
void arcade_4650e_round_dispatch(void){switch(g_round){
case 1:round1_materialized_dispatch();break;case 2:round2_materialized_dispatch();break;
case 3:round3_materialized_dispatch();break;case 4:round4_materialized_dispatch();break;
case 5:round5_materialized_dispatch();break;case 6:round6_materialized_dispatch();break;
default:break;}}
