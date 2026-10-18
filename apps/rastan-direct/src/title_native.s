    .include "pc090oj_config.inc"

    .section .text,"ax"

    .global genesistan_title_present_once
    .global genesistan_title_sat_needs_update
    .global genesistan_title_sat_cache_commit

    .extern staged_bg_buffer
    .extern staged_fg_buffer
    .extern staged_palette_words
    .extern bg_row_dirty
    .extern fg_row_dirty
    .extern palette_pending
    .extern staged_scroll_x_bg
    .extern staged_scroll_x_fg
    .extern staged_scroll_y_bg
    .extern staged_scroll_y_fg
    .extern genesistan_current_scene_id
    .extern pc090oj_native_emit_pass

/* Native title presentation boundary for arcade 0x03AA54.  The retired tail
 * was title palette load -> PC080SN 28x20 block copy -> five PC080SN text
 * renders.  These assets are translated offline into final Genesis name/CRAM
 * words; this helper publishes that complete presentation exactly once and
 * preserves the arcade state writes which finish 0x03AA54. */
genesistan_title_present_once:
    movem.l %d0-%d2/%a0-%a1, -(%sp)

    lea     native_title_bg_map, %a0
    lea     staged_bg_buffer, %a1
    move.w  #1023, %d0
.Ltitle_copy_bg:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Ltitle_copy_bg

    lea     native_title_fg_map, %a0
    tst.w   0x0040(%a5)
    beq.s   .Ltitle_fg_selected
    lea     native_title_fg_map_invincible, %a0
.Ltitle_fg_selected:
    lea     staged_fg_buffer, %a1
    move.w  #1023, %d0
.Ltitle_copy_fg:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Ltitle_copy_fg

    lea     native_title_palette, %a0
    lea     staged_palette_words+32, %a1
    moveq   #7, %d0
.Ltitle_copy_palette:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Ltitle_copy_palette

    move.l  #0xFFFFFFFF, bg_row_dirty
    move.l  #0xFFFFFFFF, fg_row_dirty
    move.b  #1, palette_pending
    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    /* Produce static labels plus the live score/high-score/credit digits once
     * at entry.  Later VBlanks rebuild only when those semantic scalars change. */
    bsr     pc090oj_native_emit_pass
    bsr     genesistan_title_sat_cache_commit

    movem.l (%sp)+, %d0-%d2/%a0-%a1
    clr.w   0x0004(%a5)
    move.w  #1, 0x0002(%a5)
    move.w  #0x00D0, 0x002C(%a5)
    rts

/* Return d0.b=1 only when the title SAT's semantic inputs changed.  All other
 * scenes retain their pre-existing per-frame native emit path. */
genesistan_title_sat_needs_update:
    cmpi.b  #0, genesistan_current_scene_id
    bne.s   .Ltitle_sat_other_scene
    tst.w   0x00FF0118
    bne.s   .Ltitle_sat_other_scene
    tst.b   native_title_sat_cache_valid
    beq.s   .Ltitle_sat_changed
    lea     native_title_sat_cache, %a0
    move.b  0x00FF011C, %d0
    cmp.b   (%a0)+, %d0
    bne.s   .Ltitle_sat_changed
    move.b  0x00FF011D, %d0
    cmp.b   (%a0)+, %d0
    bne.s   .Ltitle_sat_changed
    move.b  0x00FF011E, %d0
    cmp.b   (%a0)+, %d0
    bne.s   .Ltitle_sat_changed
    move.b  0x00FF0140, %d0
    cmp.b   (%a0)+, %d0
    bne.s   .Ltitle_sat_changed
    move.b  0x00FF0141, %d0
    cmp.b   (%a0)+, %d0
    bne.s   .Ltitle_sat_changed
    move.b  0x00FF0142, %d0
    cmp.b   (%a0)+, %d0
    bne.s   .Ltitle_sat_changed
    move.b  0x00FF0117, %d0
    cmp.b   (%a0), %d0
    bne.s   .Ltitle_sat_changed
    moveq   #0, %d0
    rts
.Ltitle_sat_changed:
    moveq   #1, %d0
    rts
.Ltitle_sat_other_scene:
    clr.b   native_title_sat_cache_valid
    moveq   #1, %d0
    rts

genesistan_title_sat_cache_commit:
    cmpi.b  #0, genesistan_current_scene_id
    bne.s   .Ltitle_cache_clear
    tst.w   0x00FF0118
    bne.s   .Ltitle_cache_clear
    lea     native_title_sat_cache, %a0
    move.b  0x00FF011C, (%a0)+
    move.b  0x00FF011D, (%a0)+
    move.b  0x00FF011E, (%a0)+
    move.b  0x00FF0140, (%a0)+
    move.b  0x00FF0141, (%a0)+
    move.b  0x00FF0142, (%a0)+
    move.b  0x00FF0117, (%a0)
    move.b  #1, native_title_sat_cache_valid
    rts
.Ltitle_cache_clear:
    clr.b   native_title_sat_cache_valid
    rts

    .section .rodata,"a"
    .align 2
native_title_bg_map:
    .incbin "../../build/rastan-direct/native_title_bg.bin"
native_title_fg_map:
    .incbin "../../build/rastan-direct/native_title_fg.bin"
native_title_fg_map_invincible:
    .incbin "../../build/rastan-direct/native_title_fg_invincible.bin"
native_title_palette:
    .incbin "../../build/rastan-direct/native_title_palette.bin"

    .section .bss,"aw",@nobits
    .align 2
native_title_sat_cache:
    .space 7
native_title_sat_cache_valid:
    .space 1
