    .include "pc090oj_config.inc"
    .section .text,"ax"

    .global genesistan_title_present_once
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
    .extern genesistan_hud_activate_frontend
    .extern genesistan_presentation_mark_ready_after_publish
    .extern vdp_set_vram_write_addr

    .equ VDP_DATA, 0x00C00000
/* Arcade 0x03AA54 presentation cut.  Patterns, maps, palette and fixed SAT
 * records are generated offline and installed once; arcade state/timing stays
 * above this presentation boundary. */
genesistan_title_present_once:
    movem.l %d0-%d7/%a0-%a3, -(%sp)

    /* Install generator-selected plane and sprite patterns. Package records
     * are {slot,32 bytes}; 0xFFFF terminates. */
    lea     native_title_patterns, %a2
.Lpat_next:
    move.w  (%a2)+, %d0
    cmpi.w  #0xFFFF, %d0
    beq.s   .Lpat_done
    lsl.l   #5, %d0
    bsr     vdp_set_vram_write_addr
    moveq   #15, %d7
.Lpat_words:
    move.w  (%a2)+, VDP_DATA
    dbra    %d7, .Lpat_words
    bra.s   .Lpat_next
.Lpat_done:

    lea     native_title_bg_map, %a0
    lea     staged_bg_buffer, %a1
    move.w  #1023, %d0
.Lcopy_bg:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Lcopy_bg
    lea     native_title_fg_map, %a0
    tst.w   0x0040(%a5)
    beq.s   .Lfg_selected
    lea     native_title_fg_map_invincible, %a0
.Lfg_selected:
    lea     staged_fg_buffer, %a1
    move.w  #1023, %d0
.Lcopy_fg:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Lcopy_fg
    lea     native_title_palette, %a0
    lea     staged_palette_words+32, %a1
    moveq   #7, %d0
.Lcopy_palette:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Lcopy_palette
    move.l  #0xFFFFFFFF, bg_row_dirty
    move.l  #0xFFFFFFFF, fg_row_dirty
    move.b  #1, palette_pending
    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    /* Title-specific art ends here.  The game-wide HUD owns labels, semantic
     * score digits, credit, SAT links, and its fixed pattern reservation. */
    bsr     genesistan_hud_activate_frontend

    movem.l (%sp)+, %d0-%d7/%a0-%a3
    clr.w   0x0004(%a5)
    move.w  #1, 0x0002(%a5)
    move.w  #0x00D0, 0x002C(%a5)
    /* RG-017: the title is now the complete presentation owner.  Override an
     * inherited gameplay/demo HOLD only after the native title planes,
     * palette, SAT/HUD state, scroll and retained dwell state are prepared.
     * The existing fixed-order VBlank publication remains the only code that
     * consumes this request and enables display output. */
    bsr     genesistan_presentation_mark_ready_after_publish
    rts

    .section .rodata,"a"
    .align 2
    .global native_title_bg_map
    .global native_title_fg_map
    .global native_title_fg_map_invincible
    .global native_title_palette
    .global native_title_patterns
native_title_bg_map:
    .incbin "../../build/rastan-direct/native_title_bg.bin"
native_title_fg_map:
    .incbin "../../build/rastan-direct/native_title_fg.bin"
native_title_fg_map_invincible:
    .incbin "../../build/rastan-direct/native_title_fg_invincible.bin"
native_title_palette:
    .incbin "../../build/rastan-direct/native_title_palette.bin"
native_title_patterns:
    .incbin "../../build/rastan-direct/native_title_patterns.bin"
