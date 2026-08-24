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
    .global fg_boundary_transition_step
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
    .global fg_boundary_conflict_lut

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
    .equ FG_BOUNDARY_IDENTITY_SCRATCH, (FG_BOUNDARY_SCRATCH_WORD * 2)
    .equ FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH, (FG_BOUNDARY_IDENTITY_SCRATCH + FG_BOUNDARY_PATTERN_IDENTITIES * 2)
    /* Dense LUT words for codes 0x031A..0x034B alias the fixed crash record at
     * Genesis-WRAM 0xFF6800..0xFF6863. Keep this proven hole in a bounded side segment. */

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

/* Build 0311 generated overlap handoff. The selector-0 producer publishes one logical column at
 * a time. At column 45 the 40-column arcade viewport cannot reference the outgoing record, so the
 * bounded overlap package may become the stable incoming epoch. D0 = logical column. */
fg_boundary_transition_step:
    movem.l %d0-%d2/%a0, -(%sp)
    cmpi.w  #FG_BOUNDARY_TRANSITION_HANDOFF_COLUMN, %d0
    bne.s   .Ltransition_step_done
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Ltransition_step_done
    cmpi.w  #3, fg_boundary_active_record
    bne.s   .Ltransition_step_check_bc
    cmpi.w  #FG_BOUNDARY_TRANSITION_AB_PACKAGE, fg_boundary_active_package
    bne.s   .Ltransition_step_done
    moveq   #FG_BOUNDARY_TRANSITION_AB_STABLE_PACKAGE, %d2
    bsr     .Linstall_selected_package
    bra.s   .Ltransition_step_done
.Ltransition_step_check_bc:
    cmpi.w  #4, fg_boundary_active_record
    bne.s   .Ltransition_step_done
    cmpi.w  #FG_BOUNDARY_TRANSITION_BC_PACKAGE, fg_boundary_active_package
    bne.s   .Ltransition_step_done
    moveq   #FG_BOUNDARY_TRANSITION_BC_STABLE_PACKAGE, %d2
    bsr     .Linstall_selected_package
.Ltransition_step_done:
    movem.l (%sp)+, %d0-%d2/%a0
    rts

/* Compatibility name for surviving Plane-A call sites. */
fg_cache_resolve:
fg_boundary_resolve_a:
    movem.l %d0/%d2/%a0, -(%sp)
    andi.w  #0x3FFF, %d3
    beq.s   .Lresolve_a_done
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lresolve_a_static
    cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d3
    bhs.s   .Lresolve_a_miss
    move.w  %d3, %d0
    bsr     .Lactive_lut_address
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
    movem.l (%sp)+, %d0/%d2/%a0
    rts

fg_boundary_resolve_b:
    movem.l %d0/%d2/%a0, -(%sp)
    andi.w  #0x3FFF, %d3
    beq.s   .Lresolve_b_done
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lresolve_b_static
    cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d3
    bhs.s   .Lresolve_b_miss
    move.w  %d3, %d0
    bsr     .Lactive_lut_address
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
    movem.l (%sp)+, %d0/%d2/%a0
    rts

/* D0 = arcade code. Return A0 + D0.w as its writable active-LUT word address.
 * D2 is scratch. The alternate segment is a fixed WRAM-layout exclusion, not a cache/search. */
.Lactive_lut_address:
    move.w  %d0, %d2
    subi.w  #FG_BOUNDARY_CONFLICT_CODE_FIRST, %d2
    bcs.s   .Lactive_lut_address_dense
    cmpi.w  #FG_BOUNDARY_CONFLICT_CODE_COUNT, %d2
    bhs.s   .Lactive_lut_address_dense
    add.w   %d2, %d2
    move.w  %d2, %d0
    lea     fg_boundary_conflict_lut, %a0
    rts
.Lactive_lut_address_dense:
    add.w   %d0, %d0
    lea     fg_boundary_active_lut, %a0
    rts

/* Install the Plane-A epoch selected by persistent record a5+0x13E. Fixed Level-1
 * Plane B is installed exactly once at gameplay entry and remains resident in slots 1..854.
 * Record transitions within one epoch update semantic record state only: no display-off, LUT
 * rebuild, slot reassignment, name remap, or pattern DMA. */
fg_boundary_install:
    movem.l %d0-%d7/%a0-%a4, -(%sp)
    cmpi.b  #1, genesistan_current_scene_id
    bne     .Linstall_done
    moveq   #0, %d0
    move.w  0x013E(%a5), %d0
    cmpi.w  #FG_BOUNDARY_RECORDS, %d0
    bhs     .Linstall_disable
    move.w  %d0, fg_boundary_pending_record

    lea     fg_boundary_packages, %a4
    move.w  %d0, %d1
    lsl.w   #2, %d1
    lea     0(%a4,%d1.w), %a0
    moveq   #FG_BOUNDARY_RECORD_ENTRY_BYTES, %d0
    bsr     .Linstall_require_package_range
    moveq   #0, %d2
    move.w  (%a0)+, %d2                 /* first package */
    move.w  (%a0), %d3                  /* variant count */
    moveq   #0, %d1                     /* Build 0308 has no Plane-B Y variants. */
    add.w   %d1, %d2                    /* package index */
    move.w  %d1, fg_boundary_pending_variant
    move.w  %d2, fg_boundary_pending_package
    cmpi.w  #FG_BOUNDARY_PACKAGES, %d2
    bhs     .Linstall_package_index_fail

.Linstall_selected_package_ready:

    /* The complete epoch vocabulary is already resident. Preserve the arcade record advance but
     * perform no Genesis graphics operation until the record->epoch table selects a new package. */
    cmp.w   fg_boundary_active_package, %d2
    bne.s   .Linstall_epoch_change
    move.w  fg_boundary_pending_record, fg_boundary_active_record
    move.w  fg_boundary_pending_variant, fg_boundary_active_variant
    bra     .Linstall_done
.Linstall_epoch_change:

    move.l  %d2, %d0
    lsl.l   #4, %d0                     /* fixed 16-byte descriptor */
    addi.l  #FG_BOUNDARY_DESC_OFFSET, %d0
    lea     0(%a4,%d0.l), %a0
    moveq   #FG_BOUNDARY_DESC_BYTES, %d0
    bsr     .Linstall_require_package_range
    move.l  (%a0)+, %d4                 /* package-data offset */
    move.w  (%a0)+, %d5                 /* map pairs */
    move.w  (%a0)+, %d6                 /* upload pairs */
    move.w  (%a0)+, fg_boundary_pending_identity_count
    /* Remaining descriptor words are required-pattern diagnostics and reserved zeros. */

    /* Validate the complete per-epoch span once before any section walk. */
    movea.l %a4, %a0
    adda.l  %d4, %a0
    moveq   #0, %d0
    move.w  %d5, %d0
    moveq   #0, %d1
    move.w  %d6, %d1
    add.l   %d1, %d0
    move.w  fg_boundary_pending_identity_count, %d1
    add.l   %d1, %d0
    lsl.l   #2, %d0                     /* all package entries are generated 4-byte pairs */
    bsr     .Linstall_require_package_range

    move.w  %sr, -(%sp)
    ori.w   #0x0700, %sr
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    /* The first gameplay install reclaims frontend slots and installs the fixed Level-1
     * Plane-B vocabulary. This is the only residency/name-table work performed for Plane B. */
    cmpi.w  #0xFFFF, fg_boundary_active_package
    bne     .Linstall_build_translation

    lea     fg_boundary_active_lut, %a0
    move.w  #(FG_BOUNDARY_LUT_WORDS - 1), %d7
.Linstall_initial_clear_lut:
    clr.w   (%a0)+
    dbra    %d7, .Linstall_initial_clear_lut
    lea     fg_boundary_conflict_lut, %a0
    move.w  #(FG_BOUNDARY_CONFLICT_CODE_COUNT - 1), %d7
.Linstall_initial_clear_conflict_lut:
    clr.w   (%a0)+
    dbra    %d7, .Linstall_initial_clear_conflict_lut

    /* FG_BOUNDARY_FIXED_B_OFFSET is > signed d16 in Build 0308.  Use an explicit 68000
     * long add; a large displacement LEA lets GNU as emit a 68020 full extension word. */
    movea.l %a4, %a0
    adda.l  #FG_BOUNDARY_FIXED_B_OFFSET, %a0
    move.l  #FG_BOUNDARY_FIXED_B_TOTAL_BYTES, %d0
    bsr     .Linstall_require_package_range
    movea.l %a0, %a2
    move.w  #(FG_BOUNDARY_FIXED_B_MAP_COUNT - 1), %d7
.Linstall_fixed_b_map_loop:
    move.w  (%a2)+, %d0                 /* arcade code */
    move.w  (%a2)+, %d1                 /* fixed Genesis slot */
    bsr     .Lactive_lut_address
    move.w  %d1, 0(%a0,%d0.w)
    dbra    %d7, .Linstall_fixed_b_map_loop

    move.w  #(FG_BOUNDARY_FIXED_B_UPLOAD_COUNT - 1), %d7
.Linstall_fixed_b_upload_loop:
    moveq   #0, %d2
    move.w  (%a2)+, %d2                 /* representative arcade code */
    moveq   #0, %d0
    move.w  (%a2)+, %d0                 /* destination slot */
    lsl.l   #5, %d0
    lsl.l   #5, %d2
    lea     genesistan_pc080sn_tile_rom, %a0
    adda.l  %d2, %a0
    moveq   #16, %d1
    bsr     vdp_dma_words_to_vram
    dbra    %d7, .Linstall_fixed_b_upload_loop
    bra     .Linstall_maps

.Linstall_build_translation:
    /* Build exact old-A-slot -> identity -> new-A-slot translation. Plane-B slots are outside
     * this band and therefore cannot be moved or blanked by a Plane-A transition. */
    lea     fg_boundary_active_lut + FG_BOUNDARY_IDENTITY_SCRATCH, %a0
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
    move.w  fg_boundary_pending_identity_count, %d7
    beq.s   .Linstall_new_identities_done
    subq.w  #1, %d7
.Linstall_new_identity_loop:
    move.w  (%a3)+, %d0                 /* new slot */
    moveq   #0, %d1
    move.w  (%a3)+, %d1                 /* canonical exact-pattern identity */
    add.w   %d1, %d1
    lea     fg_boundary_active_lut + FG_BOUNDARY_IDENTITY_SCRATCH, %a0
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
    cmpi.w  #FG_BOUNDARY_PACKAGES, %d7
    blo.s   .Linstall_old_descriptor_index_ok
    move.l  %d7, %d2
    bra     .Linstall_package_index_fail
.Linstall_old_descriptor_index_ok:
    lsl.l   #4, %d7
    addi.l  #FG_BOUNDARY_DESC_OFFSET, %d7
    lea     0(%a4,%d7.l), %a0
    moveq   #FG_BOUNDARY_DESC_BYTES, %d0
    bsr     .Linstall_require_package_range
    move.l  (%a0)+, %d0                 /* old package-data offset */
    moveq   #0, %d1
    move.w  (%a0)+, %d1                 /* old map count */
    moveq   #0, %d7
    move.w  2(%a0), %d7                 /* old identity count (descriptor word 4) */
    move.w  (%a0)+, %d2                 /* old upload count */
    movea.l %a4, %a3
    adda.l  %d0, %a3
    move.l  %d1, %d0
    add.l   %d2, %d0
    add.l   %d7, %d0
    lsl.l   #2, %d0
    movea.l %a3, %a0
    bsr     .Linstall_require_package_range
    add.w   %d2, %d1
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
    lea     fg_boundary_active_lut + FG_BOUNDARY_IDENTITY_SCRATCH, %a0
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

    /* Remove only the previous package's Plane-A code mappings. Fixed-B mappings name slots
     * below FG_BOUNDARY_SLOT_FIRST and survive every ordinary transition. */
    moveq   #0, %d7
    move.w  fg_boundary_active_package, %d7
    cmpi.w  #FG_BOUNDARY_PACKAGES, %d7
    blo.s   .Linstall_clear_old_index_ok
    move.l  %d7, %d2
    bra     .Linstall_package_index_fail
.Linstall_clear_old_index_ok:
    lsl.l   #4, %d7
    addi.l  #FG_BOUNDARY_DESC_OFFSET, %d7
    lea     0(%a4,%d7.l), %a0
    moveq   #FG_BOUNDARY_DESC_BYTES, %d0
    bsr     .Linstall_require_package_range
    move.l  (%a0)+, %d0                 /* old package-data offset */
    move.w  (%a0), %d7                  /* old map count */
    movea.l %a4, %a3
    adda.l  %d0, %a3
    move.l  %d7, %d0
    lsl.l   #2, %d0
    movea.l %a3, %a0
    bsr     .Linstall_require_package_range
    tst.w   %d7
    beq.s   .Linstall_maps
    subq.w  #1, %d7
.Linstall_clear_old_a_map_loop:
    moveq   #0, %d0
    move.w  (%a3)+, %d0                 /* old arcade code */
    move.w  (%a3)+, %d1                 /* old Genesis slot */
    cmpi.w  #FG_BOUNDARY_SLOT_FIRST, %d1
    blo.s   .Linstall_clear_old_a_map_next
    bsr     .Lactive_lut_address
    clr.w   0(%a0,%d0.w)
.Linstall_clear_old_a_map_next:
    dbra    %d7, .Linstall_clear_old_a_map_loop

.Linstall_maps:
    lea     0(%a4,%d4.l), %a2
    move.w  %d5, %d7
    beq.s   .Linstall_maps_done
    subq.w  #1, %d7
.Linstall_map_loop:
    move.w  (%a2)+, %d0                 /* arcade code */
    move.w  (%a2)+, %d1                 /* Genesis slot */
    cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d0
    bhs.s   .Linstall_map_next
    bsr     .Lactive_lut_address
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
    cmpi.w  #0xFFFF, fg_boundary_active_package
    beq.s   .Linstall_upload_required
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

    /* Plane A changes atomically. Plane B name DMA occurs only on the initial gameplay install. */
    cmpi.w  #0xFFFF, fg_boundary_active_package
    bne.s   .Linstall_plane_a_name
    lea     staged_bg_buffer, %a0
    move.l  #VRAM_PLANE_B_BASE, %d0
    move.w  #PLANE_NAME_WORDS, %d1
    bsr     vdp_dma_words_to_vram
.Linstall_plane_a_name:
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

/* Install a compiler-selected stable package for the current semantic record. D2 is the package
 * index. This reuses the single validated package installer rather than adding a render path. */
.Linstall_selected_package:
    movem.l %d0-%d7/%a0-%a4, -(%sp)
    cmpi.b  #1, genesistan_current_scene_id
    bne     .Linstall_done
    moveq   #0, %d0
    move.w  fg_boundary_active_record, %d0
    cmpi.w  #FG_BOUNDARY_RECORDS, %d0
    bhs     .Linstall_disable
    cmpi.w  #FG_BOUNDARY_PACKAGES, %d2
    bhs     .Linstall_package_index_fail
    move.w  %d0, fg_boundary_pending_record
    clr.w   fg_boundary_pending_variant
    move.w  %d2, fg_boundary_pending_package
    lea     fg_boundary_packages, %a4
    bra     .Linstall_selected_package_ready

/* Generated-package invariant gate.
 * in: A0=start, D0=required bytes, A4=fg_boundary_packages.
 * A deterministic ILLEGAL reports D0=length, D2=bad pointer, D3='PKG\1' rather than
 * allowing a generated-contract defect to become an uncontrolled odd-address access. */
.Linstall_require_package_range:
    movem.l %d1-%d2/%a1-%a2, -(%sp)
    move.l  %a0, %d1
    btst    #0, %d1
    bne.s   .Linstall_package_range_fail
    btst    #0, %d0
    bne.s   .Linstall_package_range_fail
    cmpa.l  %a4, %a0
    blo.s   .Linstall_package_range_fail
    movea.l %a0, %a1
    adda.l  %d0, %a1
    cmpa.l  %a0, %a1
    blo.s   .Linstall_package_range_fail
    movea.l %a4, %a2
    adda.l  #FG_BOUNDARY_BINARY_LEN, %a2
    cmpa.l  %a2, %a1
    bhi.s   .Linstall_package_range_fail
    movem.l (%sp)+, %d1-%d2/%a1-%a2
    rts
.Linstall_package_range_fail:
    move.l  %a0, %d2
    move.l  #0x504B4701, %d3             /* 'PKG' + range/alignment error 1 */
    .word   0x4AFC                       /* ILLEGAL: deterministic crash-handler entry */

.Linstall_package_index_fail:
    move.l  %d2, %d0
    move.l  #0x504B4702, %d3             /* 'PKG' + package-index error 2 */
    .word   0x4AFC

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
fg_boundary_conflict_lut:               .space (FG_BOUNDARY_CONFLICT_CODE_COUNT * 2)
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
fg_boundary_pending_identity_count:     .space 2
fg_boundary_reseed_pending:             .space 1
    .align 2
