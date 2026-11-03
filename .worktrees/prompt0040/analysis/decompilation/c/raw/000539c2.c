/* ORIGINAL ARCADE PC: 0x000539C2 (vertical clamp controller) + 0x00051880 (step dispenser)
 * + 0x000504FA (scene scroll-init).  Status: PARTIAL.  RECONSTRUCTED_FROM_68000.
 *
 * These three routines sit in Ghidra-UNLISTED regions (no function entry), so they are not in the
 * game-wide function census denominator. They are the upstream drivers of the vertical scroll whose
 * downstream (0x557BA/0x55854/0x55AB4) is COMPLETE in raw/000557ba.c and raw/00055ab4.c. Documented
 * here PARTIAL because the byte-faithful control flow of the decision branches is transcribed, but
 * the full callee set (0x53956/0x53F26/0x53A1A/0x53A0C row-stream helpers) is not yet closed.
 *
 * PARTIAL: vertical scroll DRIVERS. Byte evidence below is exact; callee closure is the remaining work.
 *
 * -- 0x504FA : scene scroll-init (table 0x50850, indexed by A5+0x013E * 12) --
 *   504fa: 227c 00050850  moveal #0x50850,%a1
 *   50500: 322d 013e      movew  %a5@(0x013E),%d1
 *   50504: c2fc 000c      muluw  #12,%d1
 *   50508: 43f1 1000      lea    %a1@(0,%d1:w),%a1
 *   5050c: 3219 / 5050e   word0 -> A5+0x10AE (Y scroll init)
 *   50512:               word0 -> A5+0x10EC (X scroll init, same value)
 *   50518:               word1 -> A5+0x10B0 ; 5051c word1 -> A5+0x10EE
 *   50522:               word2 -> A5+0x10B8 (direction accumulator init)
 *   50528:               word3 -> A5+0x10BA
 *   5052e:               word4 -> A5+0x10BE (player screen-Y init)
 *   50534:               word5 -> A5+0x10C0
 *   Proven records: prog2/prog3 (R1 Phase-2 climb) => Y init 0x0160 (352), screen-Y 0x0078 (120).
 *
 * -- 0x51880 : vertical scroll step dispenser (cap 4 px/frame) --
 *   5188e: 302d 1266      movew  %a5@(0x1266),%d0       ; pending UP amount
 *   51892: 0c40 0004      cmpiw  #4,%d0
 *   51896: 6500a          bcss   0x518a2                ; <4 -> use as-is
 *   51898: 5940           subqw  #4,%d0                 ; else keep remainder in A5+0x126E, emit 4
 *   5189a: 3b40 126e      movew  %d0,%a5@(0x126E)
 *   5189e: 303c 0004      movew  #4,%d0
 *   518a2: 3b40 10dc      movew  %d0,%a5@(0x10DC)       ; per-frame delta (<=4)
 *   518a6: 6100 ...       bsrw   0x53956                ; scroll up
 *   (0x518ae mirrors for A5+0x1268 pending DOWN -> bsr 0x539C2)
 *
 * -- 0x539C2 : vertical clamp controller (keep player screen-Y A5+0x10BE in band) --
 *   539c2: 3c2d 10dc      movew  %a5@(0x10DC),%d6       ; requested delta
 *   539c6: tst d6 ; if 0 -> 0x53A2C (no scroll)
 *   539dc: 322d 10be      movew  %a5@(0x10BE),%d1       ; player screen-Y
 *   539e0: 0c41 0050      cmpiw  #80,%d1                ; center threshold 80
 *   539ee: d246 ; 539f0 cmpiw #80 ; band logic around 80
 *   53a0c: 0c6d 0020 10be cmpiw  #32,%a5@(0x10BE)       ; lower clamp 32
 *   53a14: 9d6d 10be      subw   %d6,%a5@(0x10BE)
 *   539a0: 0c6d 0130 10be cmpiw  #304,%a5@(0x10BE)      ; upper region 304 (0x130)
 *   539a8: dd6d 10be      addw   %d6,%a5@(0x10BE)
 *   539b6: 08c0 0003 ...  bset #3,A5+0x10D0 ; 539ba movew d1,A5+0x10D8  (arm step + flag)
 *   Thresholds 32 / 80 / 304 are HARD-CODED immediates (not table-driven).
 */

extern short A5[];

/* 0x51880 (partial): cap pending vertical motion at 4 px/frame into the delta field. */
unsigned short scroll_step_dispense_51880(unsigned short pending)
{
    return pending < 4 ? pending : 4;   /* remainder kept in A5+0x126E / A5+0x1270 */
}

/* 0x539C2 (partial): player screen-Y band clamp (center 80, [32,304]); arms step+flag. */
void scroll_clamp_539c2(void)
{
    /* thresholds 32 / 80 / 304 hard-coded; see disasm above. Full callee closure pending. */
}
