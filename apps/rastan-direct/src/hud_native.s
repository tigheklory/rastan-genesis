    .section .text,"ax"

    .global genesistan_hud_activate_frontend
    .global genesistan_hud_prepare_frontend
    .global genesistan_hud_deactivate
    .global genesistan_hud_link_transient
    .extern staged_sprite_sat
    .extern staged_sprite_sat_b
    .extern pc090oj_sat_frame_ready
    .extern pc090oj_sat_dirty
    .extern pc090oj_emitted_count
    .extern pc090oj_tile_dma_count
    .extern sprite_tile_resident_code
    .extern pc090oj_reverse_index_init
    .extern transient_items_active
    .extern gameplay_hud_score_dirty
    .extern vdp_set_vram_write_addr

    .equ VDP_DATA, 0x00C00000
    .equ HUD_MODE_OFF, 0
    .equ HUD_MODE_FRONTEND_FULL, 1
    .equ HUD_STATIC_LABELS, 11
    .equ HUD_SCORE_DIGITS, 18
    .equ HUD_CREDIT_POSITION, 18
    .equ HUD_SAT_RECORDS, 30
    .equ HUD_FIXED_CELLS, 20

/* Install the shared FRONTEND_FULL package.  The title package calls this same
 * owner used by every later frontend state; title_native owns no HUD records. */
genesistan_hud_activate_frontend:
    movem.l %d0-%d7/%a0-%a3, -(%sp)
    cmpi.b  #HUD_MODE_FRONTEND_FULL, native_hud_mode
    beq     .Lhud_activate_done

    lea     native_hud_patterns, %a2
.Lhud_pattern_next:
    move.w  (%a2)+, %d0
    cmpi.w  #0xFFFF, %d0
    beq.s   .Lhud_patterns_done
    lsl.l   #5, %d0
    bsr     vdp_set_vram_write_addr
    moveq   #15, %d7
.Lhud_pattern_words:
    move.w  (%a2)+, VDP_DATA
    dbra    %d7, .Lhud_pattern_words
    bra.s   .Lhud_pattern_next
.Lhud_patterns_done:
    /* FRONTEND_FULL reserves the first 20 four-pattern residency cells. */
    lea     sprite_tile_resident_code, %a0
    moveq   #-1, %d0
    moveq   #48, %d7
.Lhud_clear_resident:
    move.w  %d0, (%a0)+
    dbra    %d7, .Lhud_clear_resident
    clr.w   pc090oj_tile_dma_count
    bsr     pc090oj_reverse_index_init

    lea     native_hud_static_sat, %a0
    lea     staged_sprite_sat, %a1
    lea     staged_sprite_sat_b, %a2
    move.w  #159, %d7
.Lhud_copy_static:
    move.l  (%a0)+, (%a1)+
    move.l  -4(%a0), (%a2)+
    dbra    %d7, .Lhud_copy_static

    move.b  #1, native_hud_initializing
    clr.b   native_hud_cache_valid
    bsr     .Lhud_update_all
    clr.b   native_hud_initializing
    move.b  #HUD_MODE_FRONTEND_FULL, native_hud_mode
    clr.b   native_hud_transient_linked
    move.w  #HUD_SAT_RECORDS, pc090oj_emitted_count
    move.w  #1, pc090oj_sat_frame_ready
    move.w  #1, pc090oj_sat_dirty
.Lhud_activate_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a3
    rts

/* Stable frontend frames perform ten scalar-byte comparisons.  Only a changed
 * six-digit group (or the single credit record) is copied/published. */
genesistan_hud_prepare_frontend:
    cmpi.b  #HUD_MODE_FRONTEND_FULL, native_hud_mode
    beq.s   .Lhud_prepare_active
    bsr     genesistan_hud_activate_frontend
    rts
.Lhud_prepare_active:
    movem.l %d0-%d7/%a0-%a3, -(%sp)
    tst.b   native_hud_cache_valid
    beq     .Lhud_prepare_all
    bsr     .Lhud_resolve_score_ptrs
    lea     native_hud_cache, %a1
    bsr     .Lhud_group_changed
    tst.b   %d0
    beq.s   .Lhud_check_p2
    moveq   #0, %d6
    bsr     .Lhud_update_group
.Lhud_check_p2:
    bsr     .Lhud_resolve_score_ptrs
    movea.l %a2, %a0
    lea     native_hud_cache+3, %a1
    bsr     .Lhud_group_changed
    tst.b   %d0
    beq.s   .Lhud_check_high
    moveq   #6, %d6
    bsr     .Lhud_update_group
.Lhud_check_high:
    movea.l #0x00FF0142, %a0
    lea     native_hud_cache+6, %a1
    bsr     .Lhud_group_changed
    tst.b   %d0
    beq.s   .Lhud_check_credit
    moveq   #12, %d6
    bsr     .Lhud_update_group
.Lhud_check_credit:
    move.b  0x00FF0117, %d0
    cmp.b   native_hud_cache+9, %d0
    beq.s   .Lhud_check_transient_end
    move.b  %d0, native_hud_cache+9
    bsr     .Lhud_update_credit
.Lhud_check_transient_end:
    tst.w   transient_items_active
    bne.s   .Lhud_prepare_done
    tst.b   native_hud_transient_linked
    beq.s   .Lhud_prepare_done
    bsr     .Lhud_unlink_transient
    bra.s   .Lhud_prepare_done
.Lhud_prepare_all:
    bsr     .Lhud_update_all
.Lhud_prepare_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a3
    rts

genesistan_hud_deactivate:
    /* Scene ownership is also the gameplay presentation lifetime.  Dirtied
     * before the frontend-mode early-out so cold/new/Continue gameplay entry
     * constructs a complete score + 1UP lane before its first SAT publish. */
    move.b  #1, gameplay_hud_score_dirty
    cmpi.b  #HUD_MODE_OFF, native_hud_mode
    beq.s   .Lhud_deactivate_done
    movem.l %d0-%d1/%d7/%a0, -(%sp)
    clr.b   native_hud_mode
    clr.b   native_hud_cache_valid
    clr.b   native_hud_transient_linked
    lea     sprite_tile_resident_code, %a0
    moveq   #-1, %d0
    moveq   #48, %d7
.Lhud_deactivate_clear:
    move.w  %d0, (%a0)+
    dbra    %d7, .Lhud_deactivate_clear
    clr.w   pc090oj_tile_dma_count
    bsr     pc090oj_reverse_index_init
    movem.l (%sp)+, %d0-%d1/%d7/%a0
.Lhud_deactivate_done:
    rts

/* The transient frontend finalizer appends at SAT record 30. */
genesistan_hud_link_transient:
    move.w  #0x051E, staged_sprite_sat+(29*8)+2
    move.w  #0x051E, staged_sprite_sat_b+(29*8)+2
    move.b  #1, native_hud_transient_linked
    rts

.Lhud_unlink_transient:
    move.w  #0x0500, staged_sprite_sat+(29*8)+2
    move.w  #0x0500, staged_sprite_sat_b+(29*8)+2
    clr.b   native_hud_transient_linked
    move.l  #0x0000F8EA, %d0
    bsr     vdp_set_vram_write_addr
    move.w  #0x0500, VDP_DATA
    rts

.Lhud_update_all:
    bsr     .Lhud_resolve_score_ptrs
    moveq   #0, %d6
    bsr     .Lhud_update_group
    bsr     .Lhud_resolve_score_ptrs
    movea.l %a2, %a0
    moveq   #6, %d6
    bsr     .Lhud_update_group
    movea.l #0x00FF0142, %a0
    moveq   #12, %d6
    bsr     .Lhud_update_group
    move.b  0x00FF0117, native_hud_cache+9
    bsr     .Lhud_update_credit
    move.b  #1, native_hud_cache_valid
    rts

.Lhud_resolve_score_ptrs:
    tst.w   0x00FF002A
    bne.s   .Lhud_p2_active
    movea.l #0x00FF011E, %a0
    movea.l #0x00FF00DE, %a2
    rts
.Lhud_p2_active:
    movea.l #0x00FF009E, %a0
    movea.l #0x00FF011E, %a2
    rts

.Lhud_group_changed:
    move.b  (%a0), %d0
    cmp.b   (%a1), %d0
    bne.s   .Lhud_changed
    move.b  -1(%a0), %d0
    cmp.b   1(%a1), %d0
    bne.s   .Lhud_changed
    move.b  -2(%a0), %d0
    cmp.b   2(%a1), %d0
    bne.s   .Lhud_changed
    moveq   #0, %d0
    rts
.Lhud_changed:
    moveq   #1, %d0
    rts

/* a0=BCD MSB, d6=position base 0/6/12. */
.Lhud_update_group:
    lea     native_hud_cache, %a1
    move.w  %d6, %d2
    lsr.w   #1, %d2
    adda.w  %d2, %a1
    move.b  (%a0), (%a1)+
    move.b  -1(%a0), (%a1)+
    move.b  -2(%a0), (%a1)
    moveq   #0, %d7
.Lhud_digit_loop:
    move.w  %d7, %d0
    andi.w  #0x00FF, %d0
    move.w  %d0, %d1
    lsr.w   #1, %d1
    movea.l %a0, %a2
    suba.w  %d1, %a2
    moveq   #0, %d1
    move.b  (%a2), %d1
    btst    #0, %d0
    bne.s   .Lhud_low_nibble
    lsr.w   #4, %d1
.Lhud_low_nibble:
    andi.w  #0x000F, %d1
    btst    #8, %d7
    bne.s   .Lhud_visible
    tst.w   %d1
    bne.s   .Lhud_first
    cmpi.w  #4, %d0
    blo.s   .Lhud_variant_ready
.Lhud_first:
    bset    #8, %d7
.Lhud_visible:
    addq.w  #1, %d1
.Lhud_variant_ready:
    move.w  %d6, %d2
    add.w   %d0, %d2
    bsr     .Lhud_copy_dynamic_position
    addq.w  #1, %d7
    move.w  %d7, %d0
    andi.w  #0x00FF, %d0
    cmpi.w  #6, %d0
    blo     .Lhud_digit_loop
    rts

.Lhud_update_credit:
    moveq   #0, %d1
    move.b  0x00FF0117, %d1
    beq.s   .Lhud_credit_variant
    andi.w  #0x000F, %d1
    addq.w  #1, %d1
.Lhud_credit_variant:
    move.w  #HUD_CREDIT_POSITION, %d2
    bra     .Lhud_copy_dynamic_position

/* d2=dynamic position 0..18, d1=variant 0 hidden / 1..10 digit. */
.Lhud_copy_dynamic_position:
    move.w  %d2, %d3
    mulu.w  #88, %d3
    lsl.w   #3, %d1
    add.w   %d1, %d3
    lea     native_hud_dynamic_records, %a2
    adda.l  %d3, %a2
    addi.w  #HUD_STATIC_LABELS, %d2
    lsl.w   #3, %d2
    lea     staged_sprite_sat, %a1
    adda.w  %d2, %a1
    move.l  (%a2), (%a1)
    move.l  4(%a2), 4(%a1)
    lea     staged_sprite_sat_b, %a1
    adda.w  %d2, %a1
    move.l  (%a2), (%a1)
    move.l  4(%a2), 4(%a1)
    tst.b   native_hud_initializing
    bne.s   .Lhud_copy_done
    moveq   #0, %d0
    move.w  %d2, %d0
    addi.l  #0x0000F800, %d0
    bsr     vdp_set_vram_write_addr
    moveq   #3, %d3
.Lhud_publish_record:
    move.w  (%a2)+, VDP_DATA
    dbra    %d3, .Lhud_publish_record
.Lhud_copy_done:
    rts

    .section .rodata,"a"
    .align 2
native_hud_patterns:
    .incbin "../../build/rastan-direct/native_hud_patterns.bin"
native_hud_static_sat:
    .incbin "../../build/rastan-direct/native_hud_static_sat.bin"
native_hud_dynamic_records:
    .incbin "../../build/rastan-direct/native_hud_dynamic_records.bin"

    .section .bss,"aw",@nobits
    .align 2
native_hud_cache: .space 10
native_hud_cache_valid: .space 1
native_hud_initializing: .space 1
native_hud_mode: .space 1
native_hud_transient_linked: .space 1
    .align 2
