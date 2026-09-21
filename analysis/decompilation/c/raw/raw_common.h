/* Raw reconstruction helpers. Record is a raw uint8_t* with explicit offsets,
 * mirroring 68000 A4-relative access. NOT original Taito source. */
#ifndef RASTAN_RAW_COMMON_H
#define RASTAN_RAW_COMMON_H
#include <stdint.h>
#define B(r,o)   (*(uint8_t  *)((r)+(o)))                 /* byte  field */
#define W(r,o)   (*(uint16_t *)(void*)((r)+(o)))          /* word  field */
/* globals (A5-relative), by offset */
extern uint8_t  g_round;      /* A5+0x118 */
extern uint16_t g_prog13e;    /* A5+0x13E */
extern uint16_t g_cam10be;    /* A5+0x10BE */
extern uint16_t g_scr10cc;    /* A5+0x10CC */
extern uint16_t g_char22b;    /* A5+0x22B */
extern uint16_t g_scr200;     /* A5+0x200 */
extern uint16_t g_iter214;    /* A5+0x214 */
/* helpers (see semantic tree / externs) */
extern int  arc_40e74(uint8_t *r);   /* marker recheck -> d1 */
extern void arc_4103a(uint8_t *r);   /* marker consume/advance */
extern void arc_4092e(uint8_t *r);   /* generic step / retire */
extern void arc_41bee(uint8_t *r);
extern void arc_4382e(uint8_t *r);
extern void arc_41f9c_arc(uint8_t *r);
extern void arc_43f4e(uint8_t *r);
extern void arc_3a0ec(uint8_t id);
extern uint32_t collision_map_lookup_53a2e(void); /* returns arcade collision cell ADDRESS */
extern uint16_t collision_word_at(uint32_t arcade_addr); /* reads 16-bit collision word */
extern uint16_t g_micro10e8;  /* A5+0x10E8 */
extern uint16_t g_sec1242;    /* A5+0x1242 */
extern uint16_t g_a5_46,g_a5_04,g_a5_104,g_a5_02,g_a5_13ac;
extern uint16_t g_scrX10ae;   /* A5+0x10AE */
extern uint16_t g_scrY10b0;   /* A5+0x10B0 */
#endif
