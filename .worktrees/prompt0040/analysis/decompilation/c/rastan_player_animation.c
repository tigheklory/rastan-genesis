/* rastan_player_animation.c — CHECKPOINT H24
 * Semantic reconstruction of the ORIGINAL ARCADE player frame-selection chain (state/sub-state ->
 * body frame slot). NOT original Taito source; byte-faithful in raw/00054326.c. PCs from
 * build/maincpu.disasm.txt (world_rev1). A5 = 0x10C000.
 *
 * RENDER CHAIN:  0x540CC player_body_constructor (loads per-state pose table a3/a4)
 *             -> 0x54326 frame selector (this file) -> A5+0x1244 body slot
 *             -> 0x54492 body composer (rastan_player_render.c) -> 4 pieces + weapon overlay
 *             -> SAT staging 0x10D1D2.
 *
 * PLAYER STATE FIELD A5+0x10E8 (legal values {0,1,2,3,4,5,6,7,8,9,16}, from all writers):
 *   0/1  spawn / init            2  grounded (walk/stand; most-written)   3  crouch/guard (proposed)
 *   4    climb (rope; H23 third-chain climb state)                        5  attack (selector default idx)
 *   6    airborne/jump (proposed)  7  door/scene-transition (H22: tile 0x7E -> 7)
 *   8    death (energy A5+0x013A==0 -> 8; uses A5+0x12F4 index)            9  special/attack-9 (frame -1 adjust)
 *   16   round-complete (0x51250)
 *   (Handlers are cmp/branch chains, not a single jump table. Movement dispatch region 0x515xx-0x520xx;
 *    render dispatch 0x540CC. Deep collision helpers deliberately left as frontier per H24 scope.)
 *
 * FRAME-SELECTION KEYS (0x54326):
 *   default: slot = a3[A5+0x10EA]                     (a3 = per-state pose table from 0x540CC)
 *   state 8: slot = a3[A5+0x12F4]                     (death anim index)
 *   weapon anim (A5+0x12F0==1): slot = a3[A5+0x12F2]
 *   attack (A5+0x1108==1, state!=5,!=9-with-sub4): slot = poseTbl[A5+0x110A*2],
 *          poseTbl = (A5+0x1116==0) ? 0x5BAE0 : 0x5BB10
 *   -> A5+0x1244 = body slot (0..74), then 0x54492.
 *
 * ANIMATION SEQUENCES: pose tables index the 75-slot torso table 0x5BD40. The UPPER-body slot is
 * selected through THREE registers set per state in 0x540CC (H24 correction — all three matter for
 * "is this frame used"):
 *   a2 = WEAPON-VARIANT upper table (used when weapon anim active, A5+0x12F0==1) — e.g. 0x5BA38
 *        references the WEAPON-SWING torso slots 44/46/48/50/52/54 (odd companions 43/45/47/49/51/53);
 *        0x5B6A0 -> slots 0-5, 0x5B978 -> 6-11, 0x5B8A8 -> 19-24.
 *   a3 = NORMAL upper table (idle/walk/run/jump/death), 17 tables 0x5B640..0x5BCC0.
 *   attack tables 0x5BAE0 / 0x5BB10 (word-stride) — e.g. 0x5BAE0 references the UP-THRUST slots 12/13/14.
 * With all three registers, ALL 75 torso slots are referenced (h24_player_frame_reference_map.tsv).
 * Sequence timing is driven by the animation index fields (A5+0x10EA / A5+0x110A / A5+0x12F2 /
 * A5+0x12F4). Grouping in analysis/actor_decompilation/h24_player_animation_sequences.tsv.
 * (An earlier H24 pass wrongly labelled frames "unused" by scanning only a3; it missed a2 and the
 * attack tables. Corrected: no player torso frame is unused.)
 *
 * FACING: A5+0x1114 (==2 = face right / no flip; else hflip). Weapon overlay: A5+0x12FA selects one
 * of the four weapon tables (0x5CD8A/0x5D068/0x5D346/0x5D666) appended after the 4 body pieces.
 */

extern short A5[];
enum player_state { PS_SPAWN0=0, PS_SPAWN1, PS_GROUND=2, PS_CROUCH=3, PS_CLIMB=4, PS_ATTACK=5,
                    PS_AIR=6, PS_DOOR=7, PS_DEATH=8, PS_SPECIAL9=9, PS_ROUND_DONE=16 };

/* semantic selector; byte-faithful control flow in raw/00054326.c */
unsigned char player_frame_slot(const unsigned char *a3_pose,
                                const unsigned char *pose_5bae0, const unsigned char *pose_5bb10)
{
    unsigned short st = (unsigned short)A5[0x10E8/2];
    if (st == PS_DEATH)                    return a3_pose[A5[0x12F4/2]];
    if (st != PS_SPECIAL9 && A5[0x12F0/2] == 1) return a3_pose[A5[0x12F2/2]];
    if (st != PS_SPECIAL9 && A5[0x1108/2] != 1 && st != PS_ATTACK) return a3_pose[A5[0x10EA/2]];
    const unsigned char *pt = (A5[0x1116/2] == 0) ? pose_5bae0 : pose_5bb10;
    return pt[A5[0x110A/2] * 2];
}
