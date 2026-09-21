/* rastan_actor_lifecycle.c — CHECKPOINT H7
 * Semantic reconstruction of the active-actor RETIRE / CONTACT-IMPACT / DEATH-COMPONENT / SCORE
 * path anchored at 0x4092E, plus the component-pool driver, the jump phase leaf, and the score
 * routine. NOT original Taito source; byte-faithful control flow lives in the raw/ files named per
 * function. The 68000 binary is final authority.
 *
 * PROVEN CHAIN (H7):
 *   moving rec_type actor step (0x42E38): animate + move + probe collision grid
 *        -> solid cell  -> 0x447F0 impact  -> state 0x0F (0x40CCC) + sfx 0x10
 *   component/burst group (0x43F52 over a pool): each active member -> 0x447F0 (state 0) -> retire
 *   death-animation complete (0x44804 component stepper) / boss defeat (0x469E8):
 *        -> 0x3B726 score award, value = dying actor's +0x2C  (extra life at 999999)
 *        -> 0x4092E retire/clear (zero record + companion block) ; slot reusable
 *   latent-hunter retarget (0x4103A): 0x4092E clear -> re-arm hunter -> caller writes next base/char
 *
 * ITEM/DROP FINDING: no death-triggered drop/item creator is reached from any of these paths.
 * Rastan pickups/power-ups are PLACED in the level via the marker-materialization system (H6) and
 * the field schedule (checkpoints A/B/C), not dropped on kill. See report section E.
 */
#include "rastan_arcade_types.h"

extern void     block_fill(void *dst, const void *src, int words);  /* 0x3A2D0 */
extern uint16_t companion_delta(const ActorRecord *a);              /* pool -> 0x702 / 0x4E2 */
extern void     play_sfx(uint8_t id);                               /* 0x3A0EC */
extern void     score_award(uint16_t bcd_value);                    /* 0x3B726 */
extern uint32_t collision_cell_addr(uint16_t x, uint16_t y);        /* 0x53A2E */
extern uint16_t collision_word(uint32_t cell);                      /* word[cell] */
extern uint8_t  anim_index_resolve(uint8_t idx);                    /* 0x3CF40/0x3CF52 (STUB) */

/* --- 0x4092E: retire/clear primitive ------------------------------------------------------- */
/* Zero the whole 0x40-byte record, then zero the paired 16-word companion block at +delta. */
void actor_retire(ActorRecord *a){
    ((uint8_t*)a)[0]=0; ((uint8_t*)a)[1]=0;
    block_fill((uint8_t*)a+2, a, 31);                 /* propagating zero: 32 words */
    uint16_t d = companion_delta(a);
    uint8_t *comp = (uint8_t*)a + d;
    comp[0]=0; comp[1]=0;
    block_fill(comp+2, comp, 15);                     /* zero 16 words */
}

/* --- 0x447F0 / 0x448B2: impact/child activate ---------------------------------------------- */
void component_init(ActorRecord *a){                  /* 0x448B2 */
    a->init_flag=0; a->anim_frame_dur=0xff; a->field_3c=0;
    a->state=0x0f;                                    /* -> 0x40CCC handler */
    a->anim_frame_cd=1;
    play_sfx(0x10);
}
void actor_activate_component(ActorRecord *a){        /* 0x447F0 */
    a->field_3d=1;                                    /* live sub-component */
    if (a->rec_type != 7) component_init(a);          /* rec_type 7 keeps its state */
}

/* --- 0x43F52: component-pool driver (segmented enemy / burst group) ------------------------- */
void component_pool_step(ActorRecord *pool, int count){
    for (int i=0;i<count;i++){
        ActorRecord *a = pool + i;
        if (a->active){
            if (a->state==0) actor_retire(a);         /* state 0 -> retire */
            else { a->field_39=1; actor_activate_component(a); }
        }
    }
}

/* --- 0x41F9C: jump/anim phase advance (nibble-carry) --------------------------------------- */
uint8_t phase_advance(uint8_t d0){
    uint8_t d1=d0; d0=(uint8_t)(d0+1); d0=(uint8_t)((d0<<4)|(d0>>4));
    d0=(uint8_t)(d0&0xf0); d0=(uint8_t)(d0+1); return (uint8_t)(d0+d1);
}

/* --- 0x42E38: moving-actor step + contact -------------------------------------------------- */
/* PARTIAL upstream (anim-index core 0x3CEB0 STUB); the move + contact transition is complete. */
void actor_move_contact(ActorRecord *a){
    /* animation timing elided to anim_index_resolve() (0x3CEB0 family) */
    if (a->sched_slot /*+0x26 reused as frozen/attached flag here*/ == 0){
        a->x = (uint16_t)(a->x + a->home_x /*+0x14 vx*/);
        a->y = (uint16_t)(a->y + a->home_y /*+0x18 vy*/);
        if (a->rec_type < 5){
            uint32_t cell = collision_cell_addr((uint16_t)(a->x&0x1ff),(uint16_t)(a->y&0x1ff));
            if (collision_word(cell) & 0x0100)        /* solid cell */
                actor_activate_component(a);          /* CONTACT -> impact */
        }
    }
    (void)anim_index_resolve;
}

/* --- score: value source is the dying actor's +0x2C -------------------------------------- */
void award_actor_score(const ActorRecord *a){ score_award(a->cfg_2c); }  /* 0x3B726(+0x2C) */
