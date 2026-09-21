/* ORIGINAL ARCADE PC: 0x00043F4E / 0x00043F52 component-pool driver (linked multi-part object).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * 0x43F4E is the fixed entry (a4 = A5+0x3C8 component block); 0x43F52 is the reusable entry (caller
 * sets a4 to the pool base, count in A5+0x286). It walks A5+0x286 consecutive 0x40-byte records:
 *   - inactive (+0x00==0): skipped (just counted)
 *   - active with state (+0x05)==0 : 0x4092E retire/clear it
 *   - active otherwise            : +0x39=1, then 0x447F0 activate/step it (-> state 0x0F)
 * This drives segmented enemies / burst-explosion component groups (H5 state 0x1B, H6 linked spawns).
 * The per-component identity was written by the parent that filled the pool before this call. */
#include "raw_common.h"
extern void arcade_4092e(uint8_t *r);
extern void arcade_447f0(uint8_t *r);
extern uint16_t g_a5_286;          /* A5+0x286 component count */
extern uint16_t g_a5_232;          /* A5+0x232 loop index */

/* 0x43F52 with pool base supplied by caller. 0x43F4E == arcade_43f52(A5+0x3C8). */
void arcade_43f52(uint8_t *pool){
    g_a5_232 = 0;
    uint8_t *a4 = pool;
    do {
        if (B(a4,0x00)!=0){
            if (B(a4,0x05)==0) arcade_4092e(a4);      /* state 0 -> retire */
            else { B(a4,0x39)=1; arcade_447f0(a4); }  /* else activate component */
        }
        a4 += 0x40;
        g_a5_232++;
    } while (g_a5_286 != g_a5_232);
}
