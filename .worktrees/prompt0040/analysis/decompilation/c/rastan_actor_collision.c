/* rastan_actor_collision.c — CHECKPOINT H9
 * Semantic reconstruction of the ENEMY collision manager (player boxes vs enemy hurtboxes), the
 * hurtbox format, the one-hit damage model, and the fatal path into the H7/H8 death tail.
 * NOT original Taito source; byte-faithful control flow in raw/000449b4.c, raw/00044cba.c,
 * raw/000446bc.c, raw/000447ce.c. The 68000 binary is final authority.
 *
 * FRAME ORDER (top-level 0x41F0E): main loop 0x5100A -> actor update 0x40B66 ->
 *   >>> 0x449B4 enemy collision manager <<< -> 0x420E6 (A5+0x508 pool) -> 0x443E0 -> 0x450D8 spawn.
 *
 * THE ENEMY-HURTBOX SCAN (0x449B4), which H8 could not find:
 *   for each enemy in the A5+0x2C8 pool (29 slots), active & state!=0 & not hit-flashing (+0x3D==0):
 *     hurtbox index = select_hurtbox(0x446BC)  [by rec_type/family/state]
 *     rect = hurtbox_table_0x44CE0[index]  (4 signed bytes {x_left,x_right,y_top,y_bottom};
 *            variant 0x44FA8 when +0x38==2)
 *     player box = one of A5+0x28C (weapon) / 0x2B0 / 0x1248 / 0x1254 / 0x22C  (category dispatch)
 *     overlap = AABB via 0x44CBA on X then Y
 *     on overlap -> record hit {X,Y,pal} into A5+0x12A8/0x12C8 and start the death reaction.
 *
 * DAMAGE MODEL: ordinary enemies are ONE-HIT. There is no HP accumulator: the recorded overlap sets
 * the hit-flash flag +0x3D and (rec_type!=7) runs 0x448B2 -> state 0x0F death animation + sfx 0x10.
 * family-12 actors instead take score(+0x2C)+recycle immediately (0x448D8). rec_type 10/11/18 freeze.
 *
 * FATAL PATH (proven end-to-end): overlap -> +0x3D flash / state 0x0F death anim (0x448B2) ->
 *   death-anim complete (0x44804) -> score 0x3B726 (value +0x2C) -> retire 0x4092E.
 *
 * ITEM DROPS: no per-enemy-death item CREATOR is reached from this chain (the hit lists A5+0x12A8/
 * 0x12C8 feed death sparks/effects, not pickups). Item actors are produced by the scripted /
 * position-triggered spawner 0x450D8 -> 0x45248 (bases 0x0F4/0x224/0x548, gated by camera A5+0x2DE
 * and sub-sequence A5+0x21C) and by the H6 marker system. On current evidence Rastan's "item appears
 * when you kill an enemy" is scripted/positional placement (category B/C), possibly gated by a kill
 * flag; a dedicated per-kill drop creator (category A) was NOT located. See report §F/§G/§L.
 */
#include "rastan_arcade_types.h"

extern uint8_t  select_hurtbox(ActorRecord *a);              /* 0x446BC */
extern int      box_overlap_axis(const signed char *pbox, short pc,
                                 const signed char *ebox, short ec); /* 0x44CBA */
extern void     hit_reaction(ActorRecord *a);                /* 0x447CE */
extern void     score_award(unsigned short v);              /* 0x3B726 */

/* The 4-signed-byte hurtbox rectangle table 0x44CE0 (first entries; full table in ROM). */
const signed char hurtbox_rect_44ce0[][4] = {
 {-12, 12, -20, 16},   /* idx 0 */
 {-12, 12, -16, 24},   /* idx 1 */
 {-12, 12,  -8, 18},   /* idx 2 */
 { -3,  3,  -8,  8},   /* idx 3 */
 /* ... continues in ROM; indices selected by 0x446BC ... */
};

/* Semantic: is the killed enemy the one that starts a state-0x0F death animation? (one-hit) */
int enemy_is_one_hit(const ActorRecord *a){
    /* rec_type 10/11/18 freeze; family 12 = score+recycle; rec_type 7 = no death anim; else yes. */
    if (a->rec_type==10||a->rec_type==11||a->rec_type==18) return 0;
    if (a->family==12) return 0;
    if (a->rec_type==7) return 0;
    return 1;
}
