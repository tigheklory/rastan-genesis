/* ORIGINAL ARCADE PC: 0x00055AB4 (scroll HW commit) + 0x00055B3C (X-scroll update).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (two Ghidra functions). Byte-faithful from
 * build/maincpu.disasm.txt (world_rev1). CHECKPOINT H23.
 *
 * 0x55AB4 is the PC080SN scroll-register commit; 0x55B3C is the horizontal (X) sibling of the
 * vertical scroll updater 0x557BA (raw/000557ba.c). Included here to document the full scroll write
 * path and the X axis so the vertical contract is unambiguous about which field is which.
 *
 * SCROLL-REGISTER COMMIT (0x55AB4):
 *   55ab4: 33ed 10ee 00c20000  movew %a5@(0x10EE),0xC20000   ; text/attr layer scroll
 *   55abc: 33ed 10ec 00c40000  movew %a5@(0x10EC),0xC40000   ; FG X scroll
 *   55acc: 33ed 10ae 00c40002  movew %a5@(0x10AE),0xC40002   ; FG Y scroll  <-- vertical (H23)
 *   (55ab4-55ad4)
 *
 * X-SCROLL UPDATE (0x55B3C, mirror of 0x557BA for the horizontal axis):
 *   55b3c: 322d 10b8      movew  %a5@(0x10B8),%d1
 *   55b40: 0c41 00a0      cmpiw  #0xA0,%d1              ; same 160 accumulator limit
 *   55b44: 6d4c           blts   0x55b92
 *   55b50: 322d 10f2      movew  %a5@(0x10F2),%d1       ; X sub-column accumulator (cf. Y's 0x10B2)
 *   ...
 *   55b92: 322d 10ec      movew  %a5@(0x10EC),%d1       ; X scroll
 *   55b96: 302d 10d8      movew  %a5@(0x10D8),%d0       ; step
 *   55b9a: d06d 10f0      addw   %a5@(0x10F0),%d0       ; + half-step fraction accumulator
 *   55b9e: 3400           movew  %d0,%d2
 *   55ba0: e248           lsrw   #1,%d0                 ; d0 = (step + frac) / 2  (half-rate X)
 *   55ba2: 0242 0001      andiw  #1,%d2
 *   55ba6: 3b42 10f0      movew  %d2,%a5@(0x10F0)       ; keep the fraction bit
 *   55baa: 9240           subw   %d0,%d1                ; X scroll -= half-step
 *   55bac: 0241 01ff      andiw  #0x1FF,%d1             ; wrap mod 512
 *   55bb0: 3b41 10ec      movew  %d1,%a5@(0x10EC)
 *   (the 0x55B8E path also calls the column streamer 0x55C4A, raw/00055c4a.c)
 *
 * So: A5+0x10EC = FG X scroll (column streaming, half-rate sub-pixel via 0x10F0) -> 0xC40000;
 *     A5+0x10AE = FG Y scroll (row streaming, full step)                          -> 0xC40002.
 */

extern short A5[];
extern volatile unsigned short PC080SN_C20000;  /* 0xC20000 */
extern volatile unsigned short PC080SN_C40000;  /* 0xC40000 FG X */
extern volatile unsigned short PC080SN_C40002;  /* 0xC40002 FG Y */

/* 0x55AB4 : commit the staged scroll fields to PC080SN scroll registers. */
void pc080sn_scroll_commit_55ab4(void)
{
    PC080SN_C20000 = (unsigned short)A5[0x10EE/2];
    PC080SN_C40000 = (unsigned short)A5[0x10EC/2];   /* FG X */
    PC080SN_C40002 = (unsigned short)A5[0x10AE/2];   /* FG Y (vertical, H23) */
}

/* 0x55B3C : horizontal (X) scroll update, half-rate; wrap mod 512 (see raw/000557ba.c for Y). */
void x_scroll_update_55b3c(void)
{
    if ((short)A5[0x10B8/2] >= 0xA0 && A5[0x10A8/2] != 0) return;
    unsigned short step = (unsigned short)A5[0x10D8/2] + (unsigned short)A5[0x10F0/2];
    A5[0x10F0/2] = (short)(step & 1);                 /* keep fraction */
    unsigned short half = step >> 1;
    unsigned short v = (unsigned short)A5[0x10EC/2];
    A5[0x10EC/2] = (short)((v - half) & 0x1FF);        /* wrap mod 512 */
}
