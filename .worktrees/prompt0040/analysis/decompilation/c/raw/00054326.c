/* ORIGINAL ARCADE PC: 0x00054326  player frame selector (FUN_00054326, 0x54326-0x54490).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE. Byte-faithful from build/maincpu.disasm.txt
 * (world_rev1). CHECKPOINT H24.
 *
 * Selects the player body FRAME SLOT (A5+0x1244) from player state and animation sub-fields, then
 * calls the body composer 0x54492. Called from the render constructor 0x540CC (which pre-loads the
 * base pose table a3 per state). Player state field = A5+0x10E8.
 *
 * INPUT FIELDS (verified):
 *   A5+0x10E8  player state (0..9, 16); selector cases 8, 9, 5
 *   A5+0x10EA  default animation index (into a3 pose table)
 *   A5+0x12F0  weapon-anim active flag; A5+0x12F2 weapon anim index
 *   A5+0x12F4  state-8 (death) anim index
 *   A5+0x1108  attack-active flag
 *   A5+0x1116  attack sub-state (0 -> table 0x5BAE0, else 0x5BB10); ==4 special
 *   A5+0x110A  body-pose index into 0x5BAE0 / 0x5BB10 (word entries)
 *   a3         per-state base pose table (byte entries), set by 0x540CC
 * OUTPUT: A5+0x1244 = selected body frame slot (0..74) -> 0x54492.
 *
 * EXACT DISASSEMBLY:
 *   54326: cmpiw #8,%a5@(0x10E8); beq 0x54376        ; state 8 (death) -> use A5+0x12F4 index
 *   5432e: cmpiw #9,%a5@(0x10E8); beq 0x5433e        ; state 9 -> attack-flag path
 *   54336: cmpiw #1,%a5@(0x12F0); beq 0x5435e        ; weapon-anim active -> A5+0x12F2 index
 *   5433e: cmpiw #1,%a5@(0x1108); beq 0x5438e        ; attack active -> pose-table path
 *   54346: movew %a5@(0x10EA),%d0                     ; DEFAULT: index = A5+0x10EA
 *          lea %a3@(0,%d0:w),%a0 ; moveb %a0@,%d0     ;   slot = a3[index]
 *          movew %d0,%a5@(0x1244) ; bsrw 0x54492      ;   A5+0x1244 = slot ; compose
 *   5435e: (weapon)  slot = a3[A5@(0x12F2)] -> A5+0x1244 ; compose
 *   54376: (death)   slot = a3[A5@(0x12F4)] -> A5+0x1244 ; compose
 *   5438e: cmpiw #4,%a5@(0x1116); beq 0x543b4         ; attack sub-state 4 -> keep a2
 *   54396: cmpiw #5,%a5@(0x10E8); beq 0x54346         ; state 5 -> default index path
 *   5439e: cmpiw #0,%a5@(0x1116); bne 0x543ae
 *   543a6: moveal #0x5BAE0,%a2                          ; sub-state 0 -> pose table 0x5BAE0
 *   543ae: moveal #0x5BB10,%a2                          ; else          -> pose table 0x5BB10
 *   543b4: movew %a5@(0x110A),%d0 ; lslw #1,%d0         ; index = A5+0x110A * 2 (word table)
 *          lea %a2@(0,%d0:w),%a0 ; moveb %a0@,%d0       ; slot = a2[index]
 *          movew %d0,%a5@(0x1244) ; bsrw 0x54492        ; compose
 *   543ca: (post) further state-8/9 handling continues to 0x5445E ...
 */

extern short A5[];
extern const unsigned char *a3_pose_table;      /* set by 0x540CC per state */
extern const unsigned char POSE_5BAE0[];         /* 0x5BAE0 word-indexed pose table */
extern const unsigned char POSE_5BB10[];         /* 0x5BB10 */
extern void body_compose_54492(void);            /* 0x54492 */

/* 0x54326 : select player body frame slot -> A5+0x1244, then compose. */
void player_frame_select_54326(void)
{
    unsigned short st = (unsigned short)A5[0x10E8/2];
    if (st == 8) {                                   /* death */
        A5[0x1244/2] = a3_pose_table[A5[0x12F4/2]];
        body_compose_54492(); return;
    }
    if (st != 9 && A5[0x12F0/2] == 1) {              /* weapon anim */
        A5[0x1244/2] = a3_pose_table[A5[0x12F2/2]];
        body_compose_54492(); return;
    }
    if (st != 9 && A5[0x1108/2] != 1 && st != 5) {   /* not attack -> default index */
        A5[0x1244/2] = a3_pose_table[A5[0x10EA/2]];
        body_compose_54492(); return;
    }
    /* attack / pose-table path (state 9 attack, or A5+0x1108==1) */
    const unsigned char *a2;
    if (A5[0x1116/2] != 4 && st != 5) {
        a2 = (A5[0x1116/2] == 0) ? POSE_5BAE0 : POSE_5BB10;
    } else if (st == 5) {                            /* state 5 uses default index path */
        A5[0x1244/2] = a3_pose_table[A5[0x10EA/2]]; body_compose_54492(); return;
    } else a2 = POSE_5BAE0;                          /* sub-state 4 keeps prior a2 (approx) */
    A5[0x1244/2] = a2[A5[0x110A/2] * 2];             /* word-indexed pose table */
    body_compose_54492();
}
