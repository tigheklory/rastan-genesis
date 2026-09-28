/* ORIGINAL ARCADE PC: 0x00054492  player body composer (FUN_00054492, 0x54492-0x54686).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE. Byte-faithful from build/maincpu.disasm.txt
 * (world_rev1). CHECKPOINT H24. Closes CF-01 (player frame cell extraction).
 *
 * Expands the selected body frame slot A5+0x1244 into 4 sprite pieces in the SAT staging buffer at
 * 0x10D1D2, then appends the weapon overlay (table selected by A5+0x12FA). This is the PLAYER SEMANTIC
 * FRAME -> PC090OJ sprite-record producer.
 *
 * FRAME TABLE FORMAT (0x5BD40) — PROVEN:
 *   0x5BD40[0..74]      : 75 word OFFSETS (relative to 0x5BD40), range 0x0096..0x070C.
 *   0x5BD40 + offset    : piece pool; the composer reads exactly 4 pieces (d2=4 fixed loop).
 *   piece record = 6 bytes: [tile:word][xoff:sbyte][yoff:sbyte][control:word].
 *   A piece with tile==0 emits a blank sprite (control 3, zeros). Player bodies use 3 visible cells
 *   (head at y=-32, two body cells at y=-16) + 1 blank; a few slots use up to 4 visible cells.
 *   All 75 slots decoded in analysis/actor_decompilation/h24_player_frame_cells.tsv (73 distinct).
 *
 * FACING / POSITION: A5+0x1114 selects facing (==2 keeps orientation; else hflip via |0x4000 and X
 *   negate/-16). Screen X = (sbyte xoff [flipped] + A5+0x10BE) & 0x1FF; screen Y = (sbyte yoff +
 *   A5+0x10C0 + 1) & 0x1FF. Palette line = control low nibble (player body = line 3, colbank 0x60;
 *   see specs/palette_decisions.json Rastan-player decision — NOT duplicated here).
 *
 * EXACT DISASSEMBLY:
 *   54492: moveal #0x10D1D2,%a1                       ; a1 = SAT staging output cursor
 *   54498: moveal #0x5BD40,%a0                        ; a0 = frame offset table
 *   5449e: movew %a5@(0x1244),%d0                     ; d0 = frame slot
 *   544a2: if state9 && A5@(0x1114)==3: subq #1,d0    ; death-frame adjust
 *   544b4: lslw #1,%d0 ; lea %a0@(0,d0:w),%a0 ; movew %a0@,%d0   ; d0 = offset[slot]
 *   544bc: moveal #0x5BD40,%a0 ; addaw %d0,%a0        ; a0 = &pieces = 0x5BD40 + offset
 *   544c4: movew #4,%d2                                ; 4 pieces
 *   544c8: movew %a0@,%d0 ; cmpi #0                     ; loop: tile==0 ?
 *   544d0:   -> emit blank {3,0,0,0}                    ;   yes: blank sprite
 *   544e2:   d0 = a0@(4) [control]; if A5@(0x1114)!=2: |0x4000 (hflip); -> a1+ (attr)
 *   544f4:   d0 = ext(a0@(3)) [yoff] + A5@(0x10C0) + 1; &0x1FF -> a1+ (screen Y)
 *   54506:   a1+ = a0@ [tile]                            ;   tile word
 *   5450c:   d0 = ext(a0@(2)) [xoff]; if A5@(0x1114)!=2: neg,-16; + A5@(0x10BE); &0x1FF -> a1+ (screen X)
 *   5452e:   a0 += 6                                     ;   next piece
 *   54532: subq #1,d2 ; bne 0x544c8                     ; 4 pieces
 *   -- weapon overlay table select by A5+0x12FA --
 *   54536: ==1 -> a0=0x5CD8A ; ==4 -> a0=0x5D068 ; ==2 -> a0=0x5D346 ; else -> 0x5D666 ; -> 0x54598
 *
 * TWO-HALF PLAYER SPRITE (H24 correction): 0x54492 renders ONLY the UPPER torso (cells at y=-32 head,
 *   y=-16 torso). 0x540CC ALSO composes the LOWER legs via a parallel path: lower frame slot A5+0x1246
 *   -> composer 0x546A8 (FUN_000546a8, structurally identical) -> offset table 0x5C466 (52 slots) ->
 *   SAT staging 0x10D1F2; leg cells sit at y=0 and y=+16. Full body = torso (0x5BD40[A5+0x1244]) over
 *   legs (0x5C466[A5+0x1246]) at the same origin, spanning y=-32..+32 (64 px), paired per animation
 *   index by the 18 a3/a4 pose-table pairs in 0x540CC (e.g. state-2 upper 0x5BB40 / lower 0x5BB80).
 *   Legs decoded in h24_player_leg_cells.tsv.
 */

extern short A5[];
extern const unsigned char MC[];                 /* maincpu.bin image; 0x5BD40 table lives here */
extern short *SAT_STAGE;                          /* 0x10D1D2 */

/* 0x54492 : expand frame slot A5+0x1244 into 4 sprite pieces + weapon overlay (byte-faithful shape). */
void body_compose_54492(void)
{
    unsigned short slot = (unsigned short)A5[0x1244/2];
    if (A5[0x10E8/2] == 9 && A5[0x1114/2] == 3) slot -= 1;
    const unsigned char *tbl = &MC[0x5BD40];
    unsigned short offset = (unsigned short)((tbl[slot*2] << 8) | tbl[slot*2+1]);
    const unsigned char *p = &MC[0x5BD40 + offset];
    short *out = SAT_STAGE;
    int flip = (A5[0x1114/2] != 2);
    for (int i = 0; i < 4; ++i, p += 6) {
        unsigned short tile = (p[0] << 8) | p[1];
        if (tile == 0) { *out++ = 3; *out++ = 0; *out++ = 0; *out++ = 0; continue; }
        unsigned short ctrl = (p[4] << 8) | p[5];
        if (flip) ctrl |= 0x4000;
        int yoff = (signed char)p[3];
        int xoff = (signed char)p[2];
        *out++ = (short)ctrl;                                    /* control/attr (palette = ctrl&0xF) */
        *out++ = (short)((yoff + A5[0x10C0/2] + 1) & 0x1FF);     /* screen Y */
        *out++ = (short)tile;                                    /* tile/cell */
        if (flip) xoff = -xoff - 16;
        *out++ = (short)((xoff + A5[0x10BE/2]) & 0x1FF);         /* screen X */
    }
    /* weapon overlay: table by A5+0x12FA (1->0x5CD8A, 4->0x5D068, 2->0x5D346, else 0x5D666) */
}
