/* Build 0302: boundary-loaded Stage-1 PC080SN pattern residency experiment.
 *
 * The Build-0301 hash, allocator, eviction state, upload queue, and per-frame plane scans are
 * retired from active gameplay.  A semantic record transition selects one precompiled package,
 * rebuilds this direct LUT, and DMA-loads its patterns.  Ordinary publication is one indexed read;
 * an absent code maps to blank slot 0 and increments a lane-specific counter.  It never loads.
 */

    .include "../../build/pc080sn_boundary/boundary_constants.inc"

    .section .text,"ax"

    .global fg_cache_reset
    .global fg_cache_resolve
    .global fg_boundary_resolve_a
    .global fg_boundary_resolve_b
    .global fg_boundary_advance_segment
    .global fg_boundary_install_post_reseed
    .global fg_boundary_install
    .global fg_boundary_epoch_transitions
    .global fg_boundary_variant_selections
    .global fg_boundary_miss_a
    .global fg_boundary_miss_b
    .global fg_boundary_pattern_dma_transitions
    .global fg_boundary_name_remap_a
    .global fg_boundary_name_remap_b
    .global fg_boundary_name_unmapped_a
    .global fg_boundary_name_unmapped_b
    .global fg_boundary_slots_retained
    .global fg_boundary_slots_reassigned
    .global fg_boundary_active_record
    .global fg_boundary_active_variant

    .extern genesistan_current_scene_id
    .extern genesistan_pc080sn_tile_vram_lut
    .extern genesistan_pc080sn_tile_rom
    .extern staged_bg_buffer
    .extern staged_fg_buffer
    .extern bg_row_dirty
    .extern fg_row_dirty
    .extern vdp_set_reg
    .extern vdp_dma_words_to_vram

    .equ VDP_REG_MODE2,         1
    .equ VDP_MODE2_DISPLAY_OFF, 0x34
    .equ VDP_MODE2_DISPLAY_ON,  0x74
    .equ VRAM_PLANE_B_BASE,     0x0000C000
    .equ VRAM_PLANE_A_BASE,     0x0000E000
    .equ PLANE_NAME_WORDS,      2048
    /* Package installation owns the active LUT until the final code->slot rebuild.
     * Reuse that storage for both temporary maps instead of extending BSS through
     * the retained arcade A5+0xC242 gameplay state. */
    .equ FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH, (FG_BOUNDARY_PATTERN_IDENTITIES * 2)

/* Scene-entry boundary.  load_scene_tiles invokes this while display is already off. */
fg_cache_reset:
    movem.l %d0-%d1, -(%sp)
    tst.b   fg_boundary_reseed_pending
    bne.s   .Lcache_reset_done
    clr.l   fg_boundary_epoch_transitions
    clr.l   fg_boundary_variant_selections
    clr.l   fg_boundary_miss_a
    clr.l   fg_boundary_miss_b
    clr.l   fg_boundary_pattern_dma_transitions
    clr.l   fg_boundary_name_remap_a
    clr.l   fg_boundary_name_remap_b
    clr.l   fg_boundary_name_unmapped_a
    clr.l   fg_boundary_name_unmapped_b
    clr.l   fg_boundary_slots_retained
    clr.l   fg_boundary_slots_reassigned
    move.w  #0xFFFF, fg_boundary_active_record
    move.w  #0xFFFF, fg_boundary_active_variant
    move.w  #0xFFFF, fg_boundary_active_package
    bsr     fg_boundary_install
.Lcache_reset_done:
    movem.l (%sp)+, %d0-%d1
    rts

/* Exact semantic progression replacement for arcade_pc 0x0558FE.  Preserve the original state
 * write first, then install once; the original routine's following RTS remains in arcade flow. */
fg_boundary_advance_segment:
    addq.w  #1, 0x013E(%a5)
    movem.l %d0-%d1, -(%sp)
    moveq   #0, %d0
    move.w  0x013E(%a5), %d0
    cmpi.w  #32, %d0
    bhs.s   .Ladvance_install_now
    move.l  #FG_BOUNDARY_RESEED_MASK, %d1
    btst    %d0, %d1
    beq.s   .Ladvance_install_now
    move.b  #1, fg_boundary_reseed_pending
    movem.l (%sp)+, %d0-%d1
    rts
.Ladvance_install_now:
    movem.l (%sp)+, %d0-%d1
    bsr     fg_boundary_install
    rts

/* Event records 15->16 and 21->22 reseed the descriptor cursor and Plane-B Y through the
 * outer controller after the raw segment increment.  The scene-fill return at arcade_pc 0x050482
 * calls here only after that authoritative state and its 64 publications are complete. */
fg_boundary_install_post_reseed:
    tst.b   fg_boundary_reseed_pending
    beq.s   .Lpost_reseed_done
    clr.b   fg_boundary_reseed_pending
    bsr     fg_boundary_install
.Lpost_reseed_done:
    rts

/* Compatibility name for surviving Plane-A call sites. */
fg_cache_resolve:
fg_boundary_resolve_a:
    movem.l %d0/%a0, -(%sp)
    andi.w  #0x3FFF, %d3
    beq.s   .Lresolve_a_done
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lresolve_a_static
    cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d3
    bhs.s   .Lresolve_a_miss
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     fg_boundary_active_lut, %a0
    move.w  0(%a0,%d0.w), %d3
    bne.s   .Lresolve_a_done
.Lresolve_a_miss:
    addq.l  #1, fg_boundary_miss_a
    moveq   #0, %d3
    bra.s   .Lresolve_a_done
.Lresolve_a_static:
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     genesistan_pc080sn_tile_vram_lut, %a0
    move.w  0(%a0,%d0.w), %d3
.Lresolve_a_done:
    movem.l (%sp)+, %d0/%a0
    rts

fg_boundary_resolve_b:
    movem.l %d0/%a0, -(%sp)
    andi.w  #0x3FFF, %d3
    beq.s   .Lresolve_b_done
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lresolve_b_static
    cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d3
    bhs.s   .Lresolve_b_miss
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     fg_boundary_active_lut, %a0
    move.w  0(%a0,%d0.w), %d3
    bne.s   .Lresolve_b_done
.Lresolve_b_miss:
    addq.l  #1, fg_boundary_miss_b
    moveq   #0, %d3
    bra.s   .Lresolve_b_done
.Lresolve_b_static:
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     genesistan_pc080sn_tile_vram_lut, %a0
    move.w  0(%a0,%d0.w), %d3
.Lresolve_b_done:
    movem.l (%sp)+, %d0/%a0
    rts

/* Install package selected from persistent record a5+0x13E and current proven Plane-B Y
 * a5+0x10EE.  Ordinary records have 8 variants (Y>>6); vertical records 17/21 have one 64-row
 * package.  No caller invokes this from VBlank or the normal frame loop. */
fg_boundary_install:
    movem.l %d0-%d7/%a0-%a4, -(%sp)
    cmpi.b  #1, genesistan_current_scene_id
    bne     .Linstall_done
    moveq   #0, %d0
    move.w  0x013E(%a5), %d0
    cmpi.w  #FG_BOUNDARY_RECORDS, %d0
    bhs     .Linstall_disable

    lea     fg_boundary_packages, %a4
    move.w  %d0, %d1
    lsl.w   #2, %d1
    lea     0(%a4,%d1.w), %a0
    moveq   #0, %d2
    move.w  (%a0)+, %d2                 /* first package */
    move.w  (%a0), %d3                  /* variant count */
    moveq   #0, %d1
    cmpi.w  #1, %d3
    beq.s   .Linstall_variant_ready
    move.w  0x10EE(%a5), %d1            /* Plane-B Y, 0..511 */
    andi.w  #0x01FF, %d1
    lsr.w   #6, %d1                     /* 8 classes around the 64-row ring */
.Linstall_variant_ready:
    add.w   %d1, %d2                    /* package index */
    move.w  %d0, fg_boundary_pending_record
    move.w  %d1, fg_boundary_pending_variant
    move.w  %d2, fg_boundary_pending_package

    move.l  %d2, %d0
    lsl.l   #4, %d0                     /* fixed 16-byte descriptor */
    addi.l  #FG_BOUNDARY_DESC_OFFSET, %d0
    lea     0(%a4,%d0.l), %a0
    move.l  (%a0)+, %d4                 /* package-data offset */
    move.w  (%a0)+, %d5                 /* map pairs */
    move.w  (%a0)+, %d6                 /* upload pairs */
    /* Remaining descriptor words are diagnostics: dropped A/B, row start/count. */

    move.w  %sr, -(%sp)
    ori.w   #0x0700, %sr
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    /* Build identity->new-slot from compiler-emitted exact-pattern IDs. Package data is
     * {code,slot} maps, {representative-code,slot} uploads, then {slot,identity} pairs. */
    lea     fg_boundary_active_lut, %a0
    move.w  #(FG_BOUNDARY_PATTERN_IDENTITIES - 1), %d7
.Linstall_clear_identity_lut:
    clr.w   (%a0)+
    dbra    %d7, .Linstall_clear_identity_lut

    lea     0(%a4,%d4.l), %a2
    movea.l %a2, %a3
    moveq   #0, %d0
    move.w  %d5, %d0
    add.w   %d6, %d0
    lsl.l   #2, %d0
    adda.l  %d0, %a3
    move.w  %d6, %d7
    beq.s   .Linstall_new_identities_done
    subq.w  #1, %d7
.Linstall_new_identity_loop:
    move.w  (%a3)+, %d0                 /* new slot */
    moveq   #0, %d1
    move.w  (%a3)+, %d1                 /* canonical exact-pattern identity */
    add.w   %d1, %d1
    lea     fg_boundary_active_lut, %a0
    move.w  %d0, 0(%a0,%d1.w)
    dbra    %d7, .Linstall_new_identity_loop
.Linstall_new_identities_done:

    lea     fg_boundary_active_lut + FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH, %a0
    move.w  #(FG_BOUNDARY_SLOT_COUNT - 1), %d7
.Linstall_clear_slot_translation:
    clr.w   (%a0)+
    dbra    %d7, .Linstall_clear_slot_translation

    /* Exact old slot -> canonical identity -> new slot translation. */
    moveq   #0, %d7
    move.w  fg_boundary_active_package, %d7
    cmpi.w  #0xFFFF, %d7
    beq.s   .Linstall_translation_done
    lsl.l   #4, %d7
    addi.l  #FG_BOUNDARY_DESC_OFFSET, %d7
    lea     0(%a4,%d7.l), %a0
    move.l  (%a0)+, %d0                 /* old package-data offset */
    moveq   #0, %d1
    move.w  (%a0)+, %d1                 /* old map count */
    moveq   #0, %d7
    move.w  (%a0)+, %d7                 /* old identity/upload count */
    lea     0(%a4,%d0.l), %a3
    add.w   %d7, %d1
    lsl.l   #2, %d1
    adda.l  %d1, %a3
    tst.w   %d7
    beq.s   .Linstall_translation_done
    subq.w  #1, %d7
.Linstall_old_identity_loop:
    moveq   #0, %d0
    move.w  (%a3)+, %d0                 /* old slot */
    moveq   #0, %d1
    move.w  (%a3)+, %d1                 /* canonical exact-pattern identity */
    add.w   %d1, %d1
    lea     fg_boundary_active_lut, %a0
    move.w  0(%a0,%d1.w), %d2           /* exact new slot, or blank */
    subi.w  #FG_BOUNDARY_SLOT_FIRST, %d0
    bcs.s   .Linstall_old_identity_next
    cmpi.w  #FG_BOUNDARY_SLOT_COUNT, %d0
    bhs.s   .Linstall_old_identity_next
    add.w   %d0, %d0
    lea     fg_boundary_active_lut + FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH, %a0
    move.w  %d2, 0(%a0,%d0.w)
.Linstall_old_identity_next:
    dbra    %d7, .Linstall_old_identity_loop
.Linstall_translation_done:

    lea     staged_fg_buffer, %a0
    lea     fg_boundary_name_remap_a, %a1
    lea     fg_boundary_name_unmapped_a, %a2
    bsr     .Linstall_remap_plane
    lea     staged_bg_buffer, %a0
    lea     fg_boundary_name_remap_b, %a1
    lea     fg_boundary_name_unmapped_b, %a2
    bsr     .Linstall_remap_plane

    lea     fg_boundary_active_lut, %a0
    move.w  #(FG_BOUNDARY_LUT_WORDS - 1), %d7
.Linstall_clear_lut:
    clr.w   (%a0)+
    dbra    %d7, .Linstall_clear_lut

    lea     0(%a4,%d4.l), %a2
    move.w  %d5, %d7
    beq.s   .Linstall_maps_done
    subq.w  #1, %d7
.Linstall_map_loop:
    move.w  (%a2)+, %d0                 /* arcade code */
    move.w  (%a2)+, %d1                 /* Genesis slot */
    cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d0
    bhs.s   .Linstall_map_next
    add.w   %d0, %d0
    lea     fg_boundary_active_lut, %a0
    move.w  %d1, 0(%a0,%d0.w)
.Linstall_map_next:
    dbra    %d7, .Linstall_map_loop
.Linstall_maps_done:

    move.w  %d6, %d7
    beq.s   .Linstall_uploads_done
    subq.w  #1, %d7
.Linstall_upload_loop:
    moveq   #0, %d2
    move.w  (%a2)+, %d2                 /* representative arcade code */
    moveq   #0, %d0
    move.w  (%a2)+, %d0                 /* destination slot */
    move.w  %d0, %d1
    subi.w  #FG_BOUNDARY_SLOT_FIRST, %d1
    bcs.s   .Linstall_upload_required
    cmpi.w  #FG_BOUNDARY_SLOT_COUNT, %d1
    bhs.s   .Linstall_upload_required
    add.w   %d1, %d1
    lea     fg_boundary_active_lut + FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH, %a0
    cmp.w   0(%a0,%d1.w), %d0
    bne.s   .Linstall_upload_required
    addq.l  #1, fg_boundary_slots_retained
    bra.s   .Linstall_upload_next
.Linstall_upload_required:
    addq.l  #1, fg_boundary_slots_reassigned
    lsl.l   #5, %d0                     /* VRAM byte destination */
    lsl.l   #5, %d2                     /* ROM byte source offset */
    lea     genesistan_pc080sn_tile_rom, %a0
    adda.l  %d2, %a0
    moveq   #16, %d1
    bsr     vdp_dma_words_to_vram
.Linstall_upload_next:
    dbra    %d7, .Linstall_upload_loop
.Linstall_uploads_done:
    addq.l  #1, fg_boundary_pattern_dma_transitions

    /* The new package owns both final staged tables atomically before display returns. */
    lea     staged_bg_buffer, %a0
    move.l  #VRAM_PLANE_B_BASE, %d0
    move.w  #PLANE_NAME_WORDS, %d1
    bsr     vdp_dma_words_to_vram
    lea     staged_fg_buffer, %a0
    move.l  #VRAM_PLANE_A_BASE, %d0
    move.w  #PLANE_NAME_WORDS, %d1
    bsr     vdp_dma_words_to_vram
    clr.l   bg_row_dirty
    clr.l   fg_row_dirty

    move.w  fg_boundary_pending_record, fg_boundary_active_record
    move.w  fg_boundary_pending_variant, fg_boundary_active_variant
    move.w  fg_boundary_pending_package, fg_boundary_active_package
    addq.l  #1, fg_boundary_epoch_transitions
    addq.l  #1, fg_boundary_variant_selections
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg
    move.w  (%sp)+, %sr
    bra.s   .Linstall_done

.Linstall_disable:
    move.w  #0xFFFF, fg_boundary_active_record
    move.w  #0xFFFF, fg_boundary_active_variant
    move.w  #0xFFFF, fg_boundary_active_package
.Linstall_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a4
    rts

/* in: A0=2048-word final staged plane, A1=processed counter, A2=blanked counter.
 * Only the 11-bit Genesis pattern field changes; priority/palette/H/V bits are exact. */
.Linstall_remap_plane:
    movem.l %d0-%d4/%a0-%a3, -(%sp)
    move.w  #(PLANE_NAME_WORDS - 1), %d4
.Linstall_remap_plane_loop:
    move.w  (%a0), %d0
    move.w  %d0, %d1
    andi.w  #0x07FF, %d1
    beq.s   .Linstall_remap_plane_next
    cmpi.w  #FG_BOUNDARY_SLOT_FIRST, %d1
    blo.s   .Linstall_remap_plane_next   /* system/frontend slots retain their identity */
    moveq   #0, %d2
    cmpi.w  #(FG_BOUNDARY_SLOT_FIRST + FG_BOUNDARY_SLOT_COUNT), %d1
    bhs.s   .Linstall_remap_plane_store
    subi.w  #FG_BOUNDARY_SLOT_FIRST, %d1
    add.w   %d1, %d1
    lea     fg_boundary_active_lut + FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH, %a3
    move.w  0(%a3,%d1.w), %d2
.Linstall_remap_plane_store:
    andi.w  #0xF800, %d0
    or.w    %d2, %d0
    move.w  %d0, (%a0)
    addq.l  #1, (%a1)
    tst.w   %d2
    bne.s   .Linstall_remap_plane_next
    addq.l  #1, (%a2)
.Linstall_remap_plane_next:
    addq.l  #2, %a0
    dbra    %d4, .Linstall_remap_plane_loop
    movem.l (%sp)+, %d0-%d4/%a0-%a3
    rts

    .section .rodata,"a"
    .align 2
fg_boundary_packages:
    .incbin "../../build/pc080sn_boundary/boundary_packages.bin"

    .section .bss
    .align 2
fg_boundary_active_lut:                 .space (FG_BOUNDARY_LUT_WORDS * 2)
fg_boundary_epoch_transitions:          .space 4
fg_boundary_variant_selections:         .space 4
fg_boundary_miss_a:                     .space 4
fg_boundary_miss_b:                     .space 4
fg_boundary_pattern_dma_transitions:    .space 4
fg_boundary_name_remap_a:               .space 4
fg_boundary_name_remap_b:               .space 4
fg_boundary_name_unmapped_a:            .space 4
fg_boundary_name_unmapped_b:            .space 4
fg_boundary_slots_retained:             .space 4
fg_boundary_slots_reassigned:           .space 4
fg_boundary_active_record:              .space 2
fg_boundary_active_variant:             .space 2
fg_boundary_active_package:             .space 2
fg_boundary_pending_record:             .space 2
fg_boundary_pending_variant:            .space 2
fg_boundary_pending_package:            .space 2
fg_boundary_reseed_pending:             .space 1
    .align 2
