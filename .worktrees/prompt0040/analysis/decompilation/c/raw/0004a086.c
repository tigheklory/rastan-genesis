/* ORIGINAL ARCADE PC: 0x0004A086 field-schedule installer. RECONSTRUCTED_FROM_68000. COMPLETE.
 * Installs one 8-byte schedule entry e[8] into a fresh (already-cleared) actor record and resolves
 * its template + palette. NOT written (rely on prior clear): +0x05 state(=0), +0x03 mode(=0), +0x0D,
 * +0x16, +0x02.
 *
 * Field decode (byte-faithful, 0x4A086..0x4A0D4):
 *     +0x04 = e[0]                         (class)
 *     +0x3E = e[1]                         (family)
 *     +0x38 = e[2] & 0x0F                  (compositor selector, low nibble)
 *     +0x752 = e[2] >> 4                   (VARIANT, high nibble)  <-- 0x4A09A lsrb #4 / 0x4A09C
 *     +0x36 = e[3]
 *     w = (e[4]<<8)|e[5]; if (w&1) +0x2A=1; +0x1C = w & ~1
 *     +0x34 = (e[6]<<8)|e[7]
 *     +0x00 = 1 (active) ; +0x1A = 0x180 (off-screen Y)
 *     jsr 0x4544E (template loader) ; jsr 0x45684 (palette resolver)
 *
 * H15: the VARIANT lives at the PARALLEL byte +0x752 (record-relative, OUTSIDE the 0x40-byte record
 * and outside the 0x20-byte companion cleared by 0x4092E), so it PERSISTS across retire/re-arm.
 * 0x4544E and 0x45684 both READ +0x752 directly (a4@(0x752)); it is NOT passed as an argument. */
#include "raw_common.h"
extern void arcade_4544e(uint8_t*);   /* reads +0x3E family, +0x752 variant, +0x38 comp */
extern void arcade_45684(uint8_t*);   /* reads +0x3E family, +0x752 variant, +0x38 comp, round */

void arcade_4a086(uint8_t *r, const uint8_t e[8]){
    B(r,0x04)=e[0]; B(r,0x3e)=e[1];
    uint8_t b2=e[2]; B(r,0x38)=b2&0x0f; B(r,0x752)=(uint8_t)(b2>>4);   /* variant -> parallel +0x752 */
    B(r,0x36)=e[3];
    uint16_t w=(uint16_t)((e[4]<<8)|e[5]); if(w&1) B(r,0x2a)=1; W(r,0x1c)=(uint16_t)(w&~1);
    W(r,0x34)=(uint16_t)((e[6]<<8)|e[7]); B(r,0x00)=1; W(r,0x1a)=0x180;
    arcade_4544e(r); arcade_45684(r);
}
