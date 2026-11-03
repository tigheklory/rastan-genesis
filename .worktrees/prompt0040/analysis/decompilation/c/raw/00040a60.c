/* ORIGINAL ARCADE PC: 0x00040A60 floor-marker state transition scan (table 0x40A86).
 * RECONSTRUCTED_FROM_68000. COMPLETE. 4-byte records {cur,marker,next,term}; scan while
 * (cur!=state || marker!=found) && term!=0xFF; result new state (d2b). */
#include "raw_common.h"
struct mx { uint8_t cur, marker, next, term; };
static const struct mx mx_40a86[] = { /* arcade 0x40A86 */
 {1,0x31,5,0},{2,0x33,4,0},{1,0x34,2,0},{2,0x34,1,0},{2,0x35,6,0},{1,0x38,0x0A,0},
 {1,0x39,3,0},{2,0x3b,0x0B,0},{1,0x3c,0x0C,0},{2,0x32,8,0},{1,0x36,9,0},
 {1,0x3e,0x0D,0},{2,0x3e,0x0D,0},{1,0x3f,0x0D,0},{2,0x3f,0x0D,0},
 {1,0x40,0x0E,0},{2,0x40,0x0E,0},{1,0x41,0x0E,0},{2,0x41,0x0E,0},
 {0x0D,0x40,1,0},{0x0D,0x41,2,0},{0x0E,0x3e,1,0},{0x0E,0x3f,2,0},{2,0x37,7,0xFF} };
uint8_t arcade_40a60(uint8_t cur_state, uint8_t found){
    const struct mx *p=mx_40a86;
    while ((p->cur!=cur_state || p->marker!=found) && p->term!=0xff) p++;
    return p->next;
}
