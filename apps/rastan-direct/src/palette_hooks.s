    .section .text,"ax"

    .global genesistan_palette_hook_59ad4
    .global genesistan_palette_hook_03ab00
    .global genesistan_palette_hook_45dae
    .global genesistan_palette_hook_3ba64

    .extern palette_dirty
    .extern staged_palette_words

/* Convert xBGR-555 in D0 to Genesis CRAM (0000_BBB0_GGG0_RRR0) in D1.
 * Clobbers: D1, D2, D3
 */
.Lxbgr555_to_cram:
    move.w  %d0, %d1
    andi.w  #0x001F, %d1
    lsr.w   #2, %d1
    lsl.w   #1, %d1

    move.w  %d0, %d2
    lsr.w   #5, %d2
    andi.w  #0x001F, %d2
    lsr.w   #2, %d2
    lsl.w   #1, %d2
    lsl.w   #4, %d2
    or.w    %d2, %d1

    move.w  %d0, %d3
    lsr.w   #8, %d3
    lsr.w   #2, %d3
    andi.w  #0x001F, %d3
    lsr.w   #2, %d3
    lsl.w   #1, %d3
    lsl.w   #8, %d3
    or.w    %d3, %d1
    rts

/* 0x59AD4 replacement
 * in: A0=source base, D0=arcade bank, D1=source row
 */
genesistan_palette_hook_59ad4:
    movem.l %d0-%d7/%a0-%a2, -(%sp)

    cmpi.w  #4, %d0
    bcc.s   .L59_done

    move.w  %d1, %d2
    mulu.w  #32, %d2
    adda.w  %d2, %a0

    lea     staged_palette_words, %a1
    move.w  %d0, %d2
    lsl.w   #5, %d2
    adda.w  %d2, %a1

    moveq   #0, %d5
    moveq   #15, %d6
.L59_loop:
    move.w  (%a0)+, %d1
    cmpi.w  #0xFFFF, %d1
    beq.s   .L59_next

    move.w  %d1, %d2
    move.w  %d1, %d3
    andi.w  #0x0F00, %d1
    lsr.w   #7, %d1
    andi.w  #0x00F0, %d2
    lsl.w   #2, %d2
    andi.w  #0x000F, %d3
    lsl.w   #8, %d3
    lsl.w   #3, %d3
    add.w   %d1, %d3
    add.w   %d2, %d3

    move.w  %d3, %d0
    bsr     .Lxbgr555_to_cram
    move.w  %d1, (%a1)+
    moveq   #1, %d5
.L59_next:
    dbra    %d6, .L59_loop

    tst.b   %d5
    beq.s   .L59_done
    move.b  #1, palette_dirty
.L59_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a2
    rts

/* 0x03AB00 replacement
 * original: movew #1023,0x200022 (bank 1, entry 1), already xBGR-555
 */
genesistan_palette_hook_03ab00:
    movem.l %d0-%d3/%a0, -(%sp)

    move.w  #0x03FF, %d0
    bsr     .Lxbgr555_to_cram
    lea     staged_palette_words, %a0
    move.w  %d1, 34(%a0)
    move.b  #1, palette_dirty

    movem.l (%sp)+, %d0-%d3/%a0
    rts

/* 0x045DB8 replacement
 * replaces jsr 0x3A2D0 copy-call.
 * in: A0=source, A1=arcade destination (0x200000 + idx*0x80), D0=count(words)
 */
genesistan_palette_hook_45dae:
    movem.l %d0-%d4/%a0-%a2, -(%sp)

    cmpa.l  #0x00200000, %a1
    bne.s   .L45_done

    tst.w   %d0
    beq.s   .L45_done

    lea     staged_palette_words, %a2
    move.w  %d0, %d4
    subq.w  #1, %d4
.L45_loop:
    move.w  (%a0)+, %d0
    bsr     .Lxbgr555_to_cram
    move.w  %d1, (%a2)+
    dbra    %d4, .L45_loop

    move.b  #1, palette_dirty

.L45_done:
    movem.l (%sp)+, %d0-%d4/%a0-%a2
    rts

/* 0x03BA64 replacement (runtime 0x03BC64)
 * in: A0=arcade palette destination pointer, A3=arcade source pointer, D3=loop count (long)
 * out: matches original side effects: A0/A3 advanced by count*2, D3 exits as 0.
 * note: preserves Build 55 locked conversion path:
 *   raw 0RGB-444 -> xBGR-555 (original 0x03BA64 body) -> Genesis CRAM (via .Lxbgr555_to_cram).
 */
genesistan_palette_hook_3ba64:
    movem.l %d4-%d7/%a1, -(%sp)
    clr.l   %d5

.L3ba64_loop:
    /* Reproduce original 0x03BA64 conversion in D0/D1/D2. */
    move.w  (%a3)+, %d0
    move.w  %d0, %d2
    andi.w  #0x0F00, %d0
    lsr.w   #7, %d0
    move.w  %d2, %d1
    andi.w  #0x00F0, %d1
    lsl.w   #2, %d1
    andi.w  #0x000F, %d2
    ror.w   #5, %d2
    or.w    %d1, %d0
    or.w    %d2, %d0

    /* Preserve pointer side effect regardless of bank filtering. */
    move.l  %a0, %d4
    addq.l  #2, %a0

    /* Only map arcade palette RAM 0x200000..0x200FFF into Genesis staging. */
    cmpi.l  #0x00200000, %d4
    blo.s   .L3ba64_next
    cmpi.l  #0x00201000, %d4
    bhs.s   .L3ba64_next

    sub.l   #0x00200000, %d4
    move.l  %d4, %d6
    lsr.l   #5, %d6                  /* arcade bank index */
    cmpi.l  #4, %d6
    bhs.s   .L3ba64_next             /* high banks are intentionally skipped */

    move.l  %d4, %d7
    andi.l  #0x001F, %d7
    lsr.l   #1, %d7                  /* entry within bank: 0..15 */

    move.l  %d3, %d4                 /* preserve long loop counter across BSR */
    bsr     .Lxbgr555_to_cram
    move.l  %d4, %d3
    move.w  %d1, %d2                 /* keep converted color */
    move.w  %d6, %d1
    lsl.w   #4, %d1
    add.w   %d7, %d1
    lsl.w   #1, %d1                  /* byte offset in staged_palette_words */
    lea     staged_palette_words, %a1
    move.w  %d2, 0(%a1,%d1.w)
    moveq   #1, %d5

.L3ba64_next:
    /* Keep original long-word loop semantics (not DBRA). */
    subq.l  #1, %d3
    bne.s   .L3ba64_loop

    tst.l   %d5
    beq.s   .L3ba64_done
    move.b  #1, palette_dirty

.L3ba64_done:
    movem.l (%sp)+, %d4-%d7/%a1
    rts
