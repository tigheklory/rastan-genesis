/* ORIGINAL ARCADE PC: 0x0004103E latent hunter RE-ARM. RECONSTRUCTED_FROM_68000. COMPLETE.
 *
 * Reached two ways: (a) as the fall-through tail of 0x4103A (marker consume: 0x4092E full clear ->
 * fall into 0x4103E re-arm), and (b) standalone to seed a fresh latent child-hunter. It writes ONLY
 * these fields, re-arming the record as an off-screen latent hunter that will re-materialize when it
 * next finds its target marker +0x0D:
 *     +0x00 = 1 (active)   +0x03 = 1 (mode = hunter)   +0x04 = 1 (class)
 *     +0x1C = 1 (timer)    +0x20 = 1                   +0x1A = 0x180 (off-screen Y)
 *
 * PALETTE-LIFETIME (H15 — proven): 0x4103E does NOT write the palette line +0x27 nor the variant
 * +0x752. When reached via 0x4103A, the preceding 0x4092E has just ZEROED the whole 0x40-byte record
 * (so +0x27, the creation-time palette line resolved by 0x45684, is reset to 0) AND a 0x20-byte
 * companion block at record+0x702/+0x4E2 -- but NEITHER clear covers the PARALLEL variant byte at
 * record+0x752, so the family-2 VARIANT PERSISTS across retire/re-arm. Because 0x45684 (the palette
 * resolver) runs only at creation (0x4A086) and is NOT re-run by the marker-chain transforms, a
 * re-armed/transformed actor carries +0x27 = 0 (its render palette then comes from the compositor
 * control byte via 0x3C9E8, bit6 clear) while its variant identity (+0x752) is intact. The durable
 * palette-relevant state a hunter preserves across a transform is therefore the VARIANT (+0x752),
 * not the palette line (+0x27). See raw/0004092e.c, raw/00045684.c, raw/0004a086.c. */
#include "raw_common.h"
void arcade_4103e(uint8_t *r){
    B(r,0x00)=1; B(r,0x03)=1; B(r,0x04)=1; W(r,0x1c)=1; B(r,0x20)=1; W(r,0x1a)=0x180;
    /* +0x27 (palette line) and +0x752 (variant) intentionally NOT touched: see header. */
}
