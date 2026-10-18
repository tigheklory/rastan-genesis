    .include "pc090oj_config.inc"
    .section .text,"ax"

    .global genesistan_title_present_once
    .global genesistan_title_prepare_dynamic
    .global genesistan_title_is_active
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
    .extern staged_sprite_sat
    .extern staged_sprite_sat_b
    .extern pc090oj_sat_bank
    .extern pc090oj_sat_front
    .extern pc090oj_sat_frame_ready
    .extern pc090oj_sat_dirty
    .extern pc090oj_emitted_count
    .extern sprite_tile_resident_code
    .extern pc090oj_reverse_index_init
    .extern pc090oj_tile_dma_count
    .extern vdp_set_vram_write_addr

    .equ VDP_DATA, 0x00C00000
    .equ TITLE_STATIC_LABELS, 11
    .equ TITLE_DYNAMIC_RECORDS, 18
    .equ TITLE_SAT_RECORDS, 29

genesistan_title_is_active:
    cmpi.b  #0, genesistan_current_scene_id
    bne.s   .Lnot_title
    tst.w   0x00FF0118
    bne.s   .Lnot_title
    moveq   #1, %d0
    rts
.Lnot_title:
    clr.b   native_title_cache_valid
    moveq   #0, %d0
    rts

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

    /* The title temporarily owns the shared sprite pattern band.  Empty the
     * normal residency contract now so later frontend/gameplay users cannot
     * mistake title glyph bytes for their former resident patterns. */
    lea     sprite_tile_resident_code, %a0
    moveq   #-1, %d0
    moveq   #48, %d7
.Lclear_resident:
    move.w  %d0, (%a0)+
    dbra    %d7, .Lclear_resident
    clr.w   pc090oj_tile_dma_count
    bsr     pc090oj_reverse_index_init

    lea     staged_sprite_sat, %a1
    tst.w   pc090oj_sat_bank
    beq.s   .Lsat_back_selected
    lea     staged_sprite_sat_b, %a1
.Lsat_back_selected:
    movea.l %a1, %a3
    lea     native_title_static_sat, %a0
    move.w  #159, %d0
.Lcopy_sat:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Lcopy_sat
    move.b  #1, native_title_initializing
    clr.b   native_title_cache_valid
    bsr     .Lupdate_all_groups
    clr.b   native_title_initializing
    move.w  #TITLE_SAT_RECORDS, pc090oj_emitted_count
    move.w  #1, pc090oj_sat_frame_ready
    move.w  #1, pc090oj_sat_dirty

    movem.l (%sp)+, %d0-%d7/%a0-%a3
    clr.w   0x0004(%a5)
    move.w  #1, 0x0002(%a5)
    move.w  #0x00D0, 0x002C(%a5)
    rts

/* VBlank title service. Stable title: nine byte compares and no writes.  A
 * changed semantic field copies six prebuilt records into the live SAT bank
 * and publishes only those six records (48 bytes), never the complete SAT. */
genesistan_title_prepare_dynamic:
    movem.l %d0-%d7/%a0-%a3, -(%sp)
    lea     staged_sprite_sat, %a3
    tst.w   pc090oj_sat_front
    beq.s   .Lfront_ready
    lea     staged_sprite_sat_b, %a3
.Lfront_ready:
    tst.b   native_title_cache_valid
    beq.s   .Lall_live
    bsr     .Lresolve_score_ptrs
    lea     native_title_cache, %a1
    moveq   #0, %d7
    bsr     .Lgroup_changed
    tst.b   %d0
    beq.s   .Lp2_check
    moveq   #0, %d6
    bsr     .Lupdate_group
.Lp2_check:
    bsr     .Lresolve_score_ptrs
    movea.l %a2, %a0
    lea     native_title_cache+3, %a1
    bsr     .Lgroup_changed
    tst.b   %d0
    beq.s   .Lhigh_check
    moveq   #6, %d6
    bsr     .Lupdate_group
.Lhigh_check:
    movea.l #0x00FF0142, %a0
    lea     native_title_cache+6, %a1
    bsr     .Lgroup_changed
    tst.b   %d0
    beq.s   .Lprep_done
    moveq   #12, %d6
    bsr     .Lupdate_group
    bra.s   .Lprep_done
.Lall_live:
    bsr     .Lupdate_all_groups
.Lprep_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a3
    rts

.Lupdate_all_groups:
    bsr     .Lresolve_score_ptrs
    moveq   #0, %d6
    bsr     .Lupdate_group
    bsr     .Lresolve_score_ptrs
    movea.l %a2, %a0
    moveq   #6, %d6
    bsr     .Lupdate_group
    movea.l #0x00FF0142, %a0
    moveq   #12, %d6
    bsr     .Lupdate_group
    move.b  #1, native_title_cache_valid
    rts

/* a0=P1 MSB, a2=P2 MSB.  Arcade keeps the active player's score at +0x11E
 * and preserves inactive P1/P2 at +0x09E/+0x0DE. */
.Lresolve_score_ptrs:
    tst.w   0x00FF002A
    bne.s   .Lp2_active
    movea.l #0x00FF011E, %a0
    movea.l #0x00FF00DE, %a2
    rts
.Lp2_active:
    movea.l #0x00FF009E, %a0
    movea.l #0x00FF011E, %a2
    rts

/* a0 source MSB, a1 cache. d0.b=1 and cache refreshed when changed. */
.Lgroup_changed:
    move.b  (%a0), %d0
    cmp.b   (%a1), %d0
    bne.s   .Lchanged
    move.b  -1(%a0), %d0
    cmp.b   1(%a1), %d0
    bne.s   .Lchanged
    move.b  -2(%a0), %d0
    cmp.b   2(%a1), %d0
    bne.s   .Lchanged
    moveq   #0, %d0
    rts
.Lchanged:
    move.b  (%a0), (%a1)
    move.b  -1(%a0), 1(%a1)
    move.b  -2(%a0), 2(%a1)
    moveq   #1, %d0
    rts

/* a0 source MSB, d6 position base 0/6/12, a3 live/back SAT. */
.Lupdate_group:
    movea.l %a0, %a1
    lea     native_title_cache, %a2
    move.w  %d6, %d2
    lsr.w   #1, %d2
    adda.w  %d2, %a2
    move.b  (%a1), (%a2)+
    move.b  -1(%a1), (%a2)+
    move.b  -2(%a1), (%a2)
    moveq   #0, %d7                 /* digit index; bit 8 = seen nonzero */
.Ldigit_loop:
    move.w  %d7, %d0
    andi.w  #0x00FF, %d0
    move.w  %d0, %d1
    lsr.w   #1, %d1
    movea.l %a0, %a2
    suba.w  %d1, %a2
    moveq   #0, %d1
    move.b  (%a2), %d1
    btst    #0, %d0
    bne.s   .Llow_nibble
    lsr.w   #4, %d1
.Llow_nibble:
    andi.w  #0x000F, %d1
    btst    #8, %d7
    bne.s   .Lvisible_digit
    tst.w   %d1
    bne.s   .Lfirst_digit
    cmpi.w  #4, %d0                 /* arcade score display retains final 00 */
    blo.s   .Lvariant_ready          /* variant 0 = hidden */
.Lfirst_digit:
    bset    #8, %d7
.Lvisible_digit:
    addq.w  #1, %d1                 /* variants 1..10 = digits 0..9 */
.Lvariant_ready:
    move.w  %d6, %d2
    add.w   %d0, %d2                /* dynamic position 0..17 */
    move.w  %d2, %d3
    mulu.w  #88, %d3
    lsl.w   #3, %d1
    add.w   %d1, %d3
    lea     native_title_dynamic_records, %a2
    adda.l  %d3, %a2
    move.w  %d2, %d4
    addi.w  #TITLE_STATIC_LABELS, %d4
    move.w  %d4, %d5
    lsl.w   #3, %d5
    lea     0(%a3,%d5.w), %a1
    move.l  (%a2)+, (%a1)+
    move.l  (%a2), (%a1)
    tst.b   native_title_initializing
    bne.s   .Lnext_digit
    move.w  %d4, %d0
    lsl.w   #3, %d0
    addi.l  #0x0000F800, %d0
    bsr     vdp_set_vram_write_addr
    lea     0(%a3,%d5.w), %a1
    moveq   #3, %d1
.Lpublish_record:
    move.w  (%a1)+, VDP_DATA
    dbra    %d1, .Lpublish_record
.Lnext_digit:
    addq.w  #1, %d7
    move.w  %d7, %d0
    andi.w  #0x00FF, %d0
    cmpi.w  #6, %d0
    blo     .Ldigit_loop
    rts

    .section .rodata,"a"
    .align 2
    .global native_title_bg_map
    .global native_title_fg_map
    .global native_title_fg_map_invincible
    .global native_title_palette
    .global native_title_patterns
    .global native_title_static_sat
    .global native_title_dynamic_records
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
native_title_static_sat:
    .incbin "../../build/rastan-direct/native_title_static_sat.bin"
native_title_dynamic_records:
    .incbin "../../build/rastan-direct/native_title_dynamic_records.bin"

    .section .bss,"aw",@nobits
    .align 2
native_title_cache: .space 9
native_title_cache_valid: .space 1
native_title_initializing: .space 1
    .align 2
