/* ORIGINAL ARCADE PC: 0x00054B1E  A5+0x12C8 player ITEM/STATUS effect dispatcher + type handlers.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (dispatcher + type 0 and types 4..13 handlers).
 *
 * There are TWO player collision-event tables, each 4 records x 8 bytes {active.w, type.w, X.w, Y.w}:
 *   A5+0x12A8  enemy CONTACT / damage events   -> dispatched by 0x54A2C (jump table 0x550A8).
 *   A5+0x12C8  player ITEM / STATUS effects    -> dispatched HERE (0x54B1E), types 0..13 by if-chain.
 * Both are cleared and populated by the collision manager 0x449B4 (see raw/000449b4.c).
 *
 * 0x54B1E scan: for each of 4 records, if active.w==1, dispatch on type.w (low value):
 *   type 0  -> 0x5506C  hit/auxiliary event (activates A5+0x1296 aux)          [NOT an item]
 *   type 1  -> 0x54EF2  TIMED_WEAPON: sfx 0x0E, clr timer 0x1326, A5+0x12FA=4 (FIRE)   (weapon_state.c)
 *   type 2  -> 0x54EDC  TIMED_WEAPON: A5+0x12FA=2                                       (weapon_state.c)
 *   type 3  -> 0x54EC6  TIMED_WEAPON: A5+0x12FA=3                                       (weapon_state.c)
 *   type 4  -> 0x54F08  COMBO_STATE: sfx 0x0F, clr 0x138A, A5+0x1388=0
 *   type 5  -> 0x54F1E  COMBO_STATE: A5+0x1388=1
 *   type 6  -> 0x54F34  COMBO_STATE: A5+0x1388=2
 *   type 7  -> 0x54F4A  COMBO_STATE: A5+0x1388=3
 *   type 8  -> 0x54F60  LIFE/HEALTH: sfx 0x0F, A5+0x1390=15, A5+0x140E=1, adjust A5+0x110A/0x1108
 *   type 9  -> 0x54FD4  ENERGY_RESTORE: sfx 0x0F, A5+0x013A += 0x0400, A5+0x12FC=1
 *   type 10 -> 0x54FEC  ENERGY_RESTORE: A5+0x013A += 0x0800
 *   type 11 -> 0x54FA4  ENERGY_DRAIN:  A5+0x013A -= 0x0100, A5+0x12FC=1, A5+0x1366=1, clr 0x1368
 *   type 12 -> 0x54FBC  ENERGY_DRAIN:  A5+0x013A -= 0x0200, ...
 *   type 13 -> 0x55004  ENERGY_SET:    sfx 0x0F, A5+0x013A = 0x3000 (full)
 * FIRE/timed-weapon expiry is 0x54DD2 (raw/00054dd2.c, Cody build0368/0372).
 *
 * The event TYPE for records produced from the actor pool is computed by 0x4495A (raw/0004495a.c):
 * rec_type(+0x06)==12 -> 1/2/3 per +0x25; else 0. Producers of types 4..13 (energy/life pickups)
 * are not proven in this pass (see H18 report).  A5=0x10C000; offsets are A5-relative. */
#include "raw_common.h"
extern void arc_3a0ec(uint8_t sfx);
/* weapon handlers 1/2/3 live in rastan_player_weapon_state.c (0x54EF2/0x54EDC/0x54EC6). */
extern void arcade_54ef2(uint8_t *a5), arcade_54edc(uint8_t *a5), arcade_54ec6(uint8_t *a5);

/* 0x5506C: type-0 hit event -> activate auxiliary at A5+0x1296. */
void arcade_5506c(uint8_t *a5){
    if (W(a5,0x1296)==0x00FF){
        W(a5,0x1296)=1; W(a5,0x1298)=0;
        W(a5,0x129E) = (W(a5,0x1108)==1) ? 4 : 1;      /* aux subtype from A5+0x1108 */
    }
}
/* 0x54F08..0x54F4A: melee COMBO_STATE set (A5+0x1388), clears combo counter A5+0x138A. */
static void combo_state(uint8_t *a5, uint16_t s){ arc_3a0ec(0x0F); W(a5,0x138A)=0; W(a5,0x1388)=s; }
void arcade_54f08(uint8_t *a5){ combo_state(a5,0); }   /* type 4 */
void arcade_54f1e(uint8_t *a5){ combo_state(a5,1); }   /* type 5 */
void arcade_54f34(uint8_t *a5){ combo_state(a5,2); }   /* type 6 */
void arcade_54f4a(uint8_t *a5){ combo_state(a5,3); }   /* type 7 */

/* 0x54F60: type-8 LIFE/HEALTH restore. */
void arcade_54f60(uint8_t *a5){
    arc_3a0ec(0x0F); W(a5,0x1390)=15; W(a5,0x140E)=1;
    if (W(a5,0x1116)==1){ if (W(a5,0x110A)<15) W(a5,0x110A)=14; }
    else if (W(a5,0x110A)<15){ W(a5,0x110A)=0; W(a5,0x1108)=0x00FF; }
}
/* 0x54FD4/0x54FEC: type 9/10 ENERGY_RESTORE (A5+0x013A gauge). */
void arcade_54fd4(uint8_t *a5){ arc_3a0ec(0x0F); W(a5,0x013A)+=0x0400; W(a5,0x12FC)=1; }
void arcade_54fec(uint8_t *a5){ arc_3a0ec(0x0F); W(a5,0x013A)+=0x0800; W(a5,0x12FC)=1; }
/* 0x54FA4/0x54FBC: type 11/12 ENERGY_DRAIN + defense/status. */
void arcade_54fa4(uint8_t *a5){ W(a5,0x013A)-=0x0100; W(a5,0x12FC)=1; W(a5,0x1366)=1; W(a5,0x1368)=0; }
void arcade_54fbc(uint8_t *a5){ W(a5,0x013A)-=0x0200; W(a5,0x12FC)=1; W(a5,0x1366)=1; W(a5,0x1368)=0; }
/* 0x55004: type 13 ENERGY_SET full. */
void arcade_55004(uint8_t *a5){ arc_3a0ec(0x0F); W(a5,0x013A)=0x3000; }

/* 0x54B1E: scan the 4 item/status event records and dispatch by type. */
void arcade_54b1e(uint8_t *a5){
    uint8_t *rec = a5 + 0x12C8;
    for (int i=0;i<4;i++, rec+=8){
        if (W(rec,0)!=1) continue;                 /* active */
        uint16_t t = W(rec,2);                      /* type (X=rec[4], Y=rec[6] unused here) */
        switch(t){
          case 0:  arcade_5506c(a5); break;
          case 1:  arcade_54ef2(a5); break;         /* FIRE  (weapon_state.c) */
          case 2:  arcade_54edc(a5); break;
          case 3:  arcade_54ec6(a5); break;
          case 4:  arcade_54f08(a5); break;
          case 5:  arcade_54f1e(a5); break;
          case 6:  arcade_54f34(a5); break;
          case 7:  arcade_54f4a(a5); break;
          case 8:  arcade_54f60(a5); break;
          case 9:  arcade_54fd4(a5); break;
          case 10: arcade_54fec(a5); break;
          case 11: arcade_54fa4(a5); break;
          case 12: arcade_54fbc(a5); break;
          case 13: arcade_55004(a5); break;
          default: break;
        }
    }
}
