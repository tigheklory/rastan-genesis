    .section .text,"ax"

    .global load_scene_tiles
    .global genesistan_frontend_presentation_reset
    .global genesistan_frontend_owner_reset
    .global genesistan_presentation_mark_unsafe
    .global genesistan_presentation_mark_ready_after_publish
    .global genesistan_presentation_publish_complete
    .global genesistan_presentation_readiness
    .extern fg_cache_reset

    .global genesistan_pc080sn_tile_vram_lut
    .global genesistan_pc080sn_attr_lut
    .global genesistan_pc080sn_native_metatile_index
    .global genesistan_pc080sn_native_metatile_records
    .global genesistan_pc080sn_native_metatile_records_end
    .global genesistan_pc080sn_plane_b_visual_records
    .global genesistan_pc080sn_plane_b_visual_records_end
    .global genesistan_pc080sn_tile_rom
    .global genesistan_scene_preload_title
    .global genesistan_scene_preload_title_end
    .global genesistan_scene_preload_gameplay
    .global genesistan_scene_preload_gameplay_end
    .global genesistan_scene_preload_gameplay_cave
    .global genesistan_scene_preload_gameplay_cave_end
    .global genesistan_scene_preload_stage1_cave_s4
    .global genesistan_scene_preload_stage1_cave_s4_end
    .global genesistan_scene_preload_stage1_cave_s5
    .global genesistan_scene_preload_stage1_cave_s5_end
    .global genesistan_scene_preload_stage1_cave_s6
    .global genesistan_scene_preload_stage1_cave_s6_end
    .global genesistan_scene_preload_stage1_seg1
    .global genesistan_scene_preload_stage1_seg1_end
    .global genesistan_scene_preload_stage1_seg2
    .global genesistan_scene_preload_stage1_seg2_end
    .global genesistan_scene_preload_endround
    .global genesistan_scene_preload_endround_end
    .global genesistan_scene_a0_ranges

    .global genesistan_current_scene_id
    .global genesistan_current_pc080sn_tileset_id
    .global genesistan_scene_a0_lo
    .global genesistan_scene_a0_hi
    .global genesistan_scene_present_pending

    .extern vdp_set_reg
    .extern vdp_set_vram_write_addr
    .extern fg_native_gameplay_owner
    .extern vdp_install_test_lines
    .extern pc090oj_select_palette_map
    .extern genesistan_hud_deactivate
    .extern genesistan_hud_activate_frontend
    .extern staged_palette_words
    .extern palette_pending
    .extern genesistan_hook_cwindow_clear

    .equ VDP_DATA,              0x00C00000
    .equ VDP_REG_MODE2,         1
    .equ VDP_MODE2_DISPLAY_OFF, 0x34
    .equ VDP_MODE2_DISPLAY_ON,  0x74
load_scene_tiles:
    movem.l %d1-%d7/%a0-%a4, -(%sp)

    move.w  %d0, %d6
    andi.w  #0x00FF, %d6

    lea     genesistan_scene_preload_title, %a0
    cmpi.w  #1, %d6
    bne.s   .Lload_scene_check_endround
    lea     genesistan_scene_preload_gameplay, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_endround:
    cmpi.w  #2, %d6
    bne.s   .Lload_scene_check_gameplay_cave
    lea     genesistan_scene_preload_endround, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_gameplay_cave:
    cmpi.w  #3, %d6
    bne.s   .Lload_scene_check_stage1_cave_s4
    lea     genesistan_scene_preload_gameplay_cave, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_cave_s4:
    /* Build 0299: Stage-1 first-cave per-segment residencies (ids 4/5/6), runtime-selected by
     * arcade segment a5@0x13E.  Each loads the outdoor BG + that segment's cave FG. */
    cmpi.w  #4, %d6
    bne.s   .Lload_scene_check_stage1_cave_s5
    lea     genesistan_scene_preload_stage1_cave_s4, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_cave_s5:
    cmpi.w  #5, %d6
    bne.s   .Lload_scene_check_stage1_cave_s6
    lea     genesistan_scene_preload_stage1_cave_s5, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_cave_s6:
    cmpi.w  #6, %d6
    bne.s   .Lload_scene_check_stage1_seg1
    lea     genesistan_scene_preload_stage1_cave_s6, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_seg1:
    /* Build 0300: outdoor per-segment residencies (ids 7=seg1, 8=seg2). */
    cmpi.w  #7, %d6
    bne.s   .Lload_scene_check_stage1_seg2
    lea     genesistan_scene_preload_stage1_seg1, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_seg2:
    cmpi.w  #8, %d6
    bne.s   .Lload_scene_force_title
    lea     genesistan_scene_preload_stage1_seg2, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_force_title:
    moveq   #0, %d6
.Lload_scene_manifest_ready:
    move.w  %sr, -(%sp)
    ori.w   #0x0700, %sr

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

.Lload_scene_pair_loop:
    move.w  (%a0)+, %d2
    cmpi.w  #0xFFFF, %d2
    beq.s   .Lload_scene_pairs_done
    move.w  (%a0)+, %d3

    lea     genesistan_pc080sn_tile_rom, %a2
    moveq   #0, %d4
    move.w  %d2, %d4
    lsl.l   #5, %d4
    adda.l  %d4, %a2

    moveq   #0, %d0
    move.w  %d3, %d0
    lsl.l   #5, %d0
    bsr     vdp_set_vram_write_addr

    moveq   #15, %d7
.Lload_scene_tile_words:
    move.w  (%a2)+, VDP_DATA
    dbra    %d7, .Lload_scene_tile_words
    bra.s   .Lload_scene_pair_loop

.Lload_scene_pairs_done:
    move.b  %d6, genesistan_current_pc080sn_tileset_id
    move.w  %d6, %d5
    /* ids 3 (attr cave) and 4/5/6 (Stage-1 first-cave segments) are logically the gameplay
     * scene: they share the gameplay a0 source range and fg_native ownership. */
    cmpi.w  #3, %d5
    blo.s   .Lload_scene_logical_ready
    moveq   #1, %d5
.Lload_scene_logical_ready:
    move.b  %d5, genesistan_current_scene_id
    cmpi.w  #1, %d5
    bne.s   .Lload_scene_hud_ready
    bsr     genesistan_hud_deactivate
.Lload_scene_hud_ready:
    bsr     pc090oj_select_palette_map
    tst.w   %d5
    bne.s   .Lload_scene_palette_ready
    /* Scene 0 is a finite frontend ownership boundary. Restore the original
     * cold-start frontend base palette offline-generated from arcade banks
     * 0/1/48, and release gameplay's Test-owned Lines 0/2/3. Retained READY,
     * title, Continue and item producers may then overwrite their own lines. */
    lea     genesistan_frontend_base_palette, %a0
    lea     staged_palette_words, %a1
    moveq   #(64 - 1), %d2
.Lload_scene_frontend_palette_copy:
    move.w  (%a0)+, (%a1)+
    dbra    %d2, .Lload_scene_frontend_palette_copy
    move.b  #1, palette_pending
.Lload_scene_palette_ready:
    cmpi.w  #1, %d5
    beq.s   .Lload_scene_keep_fg_owner_state
    clr.b   fg_native_gameplay_owner
.Lload_scene_keep_fg_owner_state:
    lea     genesistan_scene_a0_ranges, %a3
    moveq   #0, %d4
    move.w  %d5, %d4
    lsl.w   #3, %d4
    adda.w  %d4, %a3
    move.l  (%a3)+, %d0
    move.l  (%a3), %d1
    move.l  %d0, genesistan_scene_a0_lo
    move.l  %d1, genesistan_scene_a0_hi

    /* Build 0301: reset the streaming tile cache on gameplay-scene entry (display still off). */
    /* Install the generated current-Test R1/P1 palette Lines 0/1/3 ONCE here, at the gameplay-scene
     * activation event.  This replaces the removed per-VBlank vdp_reassert_test_lines: Test ownership
     * is established at the semantic boundary and the arcade palette hooks are gated off Lines 0/1/3
     * during scene 1, so the Test lines stay static until the next scene-activation event. */
    cmpi.w  #1, %d5
    bne.s   .Lload_scene_no_cache_reset
    bsr     fg_cache_reset
    bsr     vdp_install_test_lines
.Lload_scene_no_cache_reset:

    /* Build 0394 / RG-015: a semantic scene fill or lifecycle transition keeps
     * the display off.  The completed producer boundary requests visibility;
     * only the following completed VBlank publication may enable it. */
    tst.b   genesistan_scene_present_pending
    bne.s   .Lload_scene_leave_display_off
    tst.b   genesistan_presentation_readiness
    bne.s   .Lload_scene_leave_display_off
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg
.Lload_scene_leave_display_off:

    move.w  (%sp)+, %sr
    movem.l (%sp)+, %d1-%d7/%a0-%a4
    rts

/* RG-003 native frontend ownership handoff.
 *
 * The retained arcade callers have already chosen a frontend/READY transition
 * and are invoking their original PC090OJ clear boundary.  Retire that chip
 * tail here: restore the generated scene-0 PC080SN pattern residency and
 * palette ownership, then replace the persistent Genesis SAT with the clean
 * FRONTEND_FULL package.  Deactivate first so activation always rebuilds both
 * staging banks and arms a real VBlank publication, even when the prior
 * frontend mode byte was still set.
 *
 * Plane contents remain owned by the retained arcade text/block producers.
 * This finite lifecycle operation clears the two final staged name tables,
 * not pattern VRAM, before those producers repopulate them; it neither invents
 * a state machine nor authors frontend content. */
genesistan_frontend_presentation_reset:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lfrontend_owner_reset_body
    /* The accepted lifecycle reset precedes all retained frontend plane
     * producers. Clear final Genesis name tables here so a scene-0 residency
     * reload cannot reinterpret 1,928 stale gameplay names around Continue. */
    bsr     genesistan_hook_cwindow_clear
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* The 0x056440 teardown retains its original scroll-zero-then-plane-clear
 * order, so it requests only the shared scene/palette/SAT owner handoff and
 * performs that retained clear consequence in its own bounded wrapper. */
genesistan_frontend_owner_reset:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lpresentation_mark_unsafe_body
    bsr     .Lfrontend_owner_reset_body
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* RG-015 presentation-only readiness latch.
 *
 * 0 = normal visible ownership
 * 1 = unsafe native-resource generation; force display off
 * 2 = all retained/native producers are complete; enable only after the next
 *     fixed-order VBlank publication has committed CRAM/planes/SAT/scroll.
 *
 * The retained arcade death, READY and respawn controllers remain the only
 * gameplay authority.  These helpers own only Genesis display safety. */
genesistan_presentation_mark_unsafe:
    movem.l %d0-%d2, -(%sp)
    bsr     .Lpresentation_mark_unsafe_body
    movem.l (%sp)+, %d0-%d2
    rts

.Lpresentation_mark_unsafe_body:
    move.b  #1, genesistan_presentation_readiness
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg
    rts

genesistan_presentation_mark_ready_after_publish:
    move.b  #2, genesistan_presentation_readiness
    rts

/* Called exactly at dma_publish_frame completion.  HOLD stays blank; READY is
 * consumed once and makes the just-published coherent generation visible. */
genesistan_presentation_publish_complete:
    cmpi.b  #2, genesistan_presentation_readiness
    beq.s   .Lpresentation_enable
    tst.b   genesistan_presentation_readiness
    beq.s   .Lpresentation_publish_done
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg
    bra.s   .Lpresentation_publish_done
.Lpresentation_enable:
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg
    clr.b   genesistan_presentation_readiness
.Lpresentation_publish_done:
    rts

.Lfrontend_owner_reset_body:
    moveq   #0, %d0
    bsr     load_scene_tiles
    bsr     genesistan_hud_deactivate
    bsr     genesistan_hud_activate_frontend
    rts


    .section .rodata,"a"

    .align 2
genesistan_pc080sn_tile_vram_lut:
    .incbin "../../build/pc080sn_tile_vram_lut.bin"

    .align 2
genesistan_frontend_base_palette:
    .incbin "../../build/rastan-direct/native_frontend_palette.bin"

    .align 2
genesistan_pc080sn_attr_lut:
    .incbin "../../build/pc080sn_attr_lut.bin"

    /* Build 0420: generated invariant Plane-A metatile semantics.  Runtime
     * camera/ring/descriptor selection remains arcade-owned; the selected
     * pointer indexes one 64-byte record: 16 tile codes + 16 collision words. */
    .align 2
genesistan_pc080sn_native_metatile_index:
    .incbin "../../build/pc080sn_native_metatile_index.bin"
genesistan_pc080sn_native_metatile_records:
    .incbin "../../build/pc080sn_native_metatile_records.bin"
genesistan_pc080sn_native_metatile_records_end:

    /* Build 0423: visual-only invariant Plane-B descriptor interpretation.
     * Dynamic descriptor, scroll, ring, package, and residency state remain
     * runtime-owned; records contain no collision data. */
    .align 2
genesistan_pc080sn_plane_b_visual_records:
    .incbin "../../build/pc080sn_plane_b_visual_records.bin"
genesistan_pc080sn_plane_b_visual_records_end:

    /* Build 0418: each PC080SN pattern is exactly 32 bytes.  Aligning the
     * corpus makes every code*32 upload 32-byte aligned; because 0x20000 is a
     * multiple of 32, no individual tile can straddle a VDP DMA source bank. */
    .balign 32
genesistan_pc080sn_tile_rom:
    /* Offline current Palette Composer Test Layer-A patterns (editor index-maps applied by
     * tools/graphics_editor/compile_editor_layera.py). Layer-B tile codes are disjoint from
     * Layer-A codes, so only editor-authored R1/P1 Layer-A patterns are reindexed here. */
    .incbin "../../build/regions/pc080sn_editor_layera.bin"

    .align 2
genesistan_scene_preload_title:
    .incbin "../../build/pc080sn_scene_preload_title.bin"
genesistan_scene_preload_title_end:

    .align 2
genesistan_scene_preload_gameplay:
    .incbin "../../build/pc080sn_scene_preload_gameplay.bin"
genesistan_scene_preload_gameplay_end:

    .align 2
genesistan_scene_preload_gameplay_cave:
    .incbin "../../build/pc080sn_scene_preload_gameplay_cave.bin"
genesistan_scene_preload_gameplay_cave_end:

    .align 2
genesistan_scene_preload_stage1_cave_s4:
    .incbin "../../build/pc080sn_scene_preload_stage1_cave_s4.bin"
genesistan_scene_preload_stage1_cave_s4_end:

    .align 2
genesistan_scene_preload_stage1_cave_s5:
    .incbin "../../build/pc080sn_scene_preload_stage1_cave_s5.bin"
genesistan_scene_preload_stage1_cave_s5_end:

    .align 2
genesistan_scene_preload_stage1_cave_s6:
    .incbin "../../build/pc080sn_scene_preload_stage1_cave_s6.bin"
genesistan_scene_preload_stage1_cave_s6_end:

    .align 2
genesistan_scene_preload_stage1_seg1:
    .incbin "../../build/pc080sn_scene_preload_stage1_seg1.bin"
genesistan_scene_preload_stage1_seg1_end:

    .align 2
genesistan_scene_preload_stage1_seg2:
    .incbin "../../build/pc080sn_scene_preload_stage1_seg2.bin"
genesistan_scene_preload_stage1_seg2_end:

    .align 2
genesistan_scene_preload_endround:
    .incbin "../../build/pc080sn_scene_preload_endround.bin"
genesistan_scene_preload_endround_end:

genesistan_scene_a0_ranges:
    .long 0x0005A7DA
    .long 0x0005B0B2
    .long 0x00056A22
    .long 0x000570C2
    .long 0x0005822A
    .long 0x00059614

    .section .bss
    .align 2

genesistan_current_scene_id:
    .byte 0
genesistan_current_pc080sn_tileset_id:
    .byte 0
    .align 2
genesistan_scene_a0_lo:
    .long 0
genesistan_scene_a0_hi:
    .long 0
genesistan_scene_present_pending:
    .byte 0
genesistan_presentation_readiness:
    .byte 0
