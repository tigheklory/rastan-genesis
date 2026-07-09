    .section .text,"ax"

    .global genesistan_pc090oj_hook_target_3b902
    .global genesistan_pc090oj_hook_target_3b926
    .global genesistan_pc090oj_hook_target_3b930
    .global genesistan_pc090oj_hook_target_41dae
    .global genesistan_pc090oj_hook_target_41f5e
    .global genesistan_pc090oj_hook_target_45dfa
    .global genesistan_pc090oj_hook_target_59f5e
    .global genesistan_hook_3ad44_dispatch
    .global genesistan_pc090oj_hook_init_priority_3ad84
    .global genesistan_pc090oj_hook_score_digit_3b802
    .global genesistan_pc090oj_hook_slot_init_54052
    .global genesistan_pc090oj_hook_sprite_update_54810
    .global genesistan_pc090oj_hook_sprite_decay_5607c
    .global genesistan_pc090oj_hook_copy_56114
    .global genesistan_pc090oj_hook_zero_fill_56440
    .global genesistan_pc090oj_hook_status_sprite_5a098
    .global genesistan_pc090oj_hook_audit_guard
    .global genesistan_pc090oj_ctrl_set_1
    .global genesistan_pc090oj_ctrl_set_0
    .global genesistan_pc090oj_sprite_ctrl_write_d0
    .global genesistan_pc090oj_sprite_ctrl_clear

    .global vdp_prepare_sprites
    .global vdp_commit_sprites
    .global vdp_commit_sprites_vram
    .global genesistan_pc090oj_dma_self_test

    .global pc090oj_object_ram
    .global pc090oj_candidate_bitset
    .global pc090oj_ctrl_shadow
    .global pc090oj_sprite_ctrl_shadow
    .global pc090oj_mirror_dirty
    .global pc090oj_candidate_count
    .global pc090oj_decoded_count
    .global pc090oj_code_zero_skipped_count
    .global pc090oj_blank_skipped_count
    .global pc090oj_unmapped_skipped_count
    .global pc090oj_offscreen_skipped_count
    .global pc090oj_drawable_count
    .global pc090oj_emitted_count
    .global pc090oj_dropped_count
    .global pc090oj_scan_colbank
    .global pc090oj_scan_active
    .global pc090oj_producer_oob_count
    .global pc090oj_producer_write_count

    .global staged_sprite_sat
    .global staged_sprite_descriptor_table
    .global staged_sprite_dirty
    .global staged_sprite_active_count
    .global sprite_tile_resident_code
    .global pc090oj_tile_dma_worklist
    .global pc090oj_tile_dma_count

    /* Build 0142 retained-identity translation state */
    .global pc090oj_workram_block_sprites
    .global record_to_slot
    .global represented_records
    .global waiting_records
    .global used_sat_slots
    .global worklist_entry_for_slot
    .global pc090oj_represented_count
    .global pc090oj_sat_dirty
    .global pc090oj_bootstrap_pending

    .global audit_guard_caller_pc
    .global audit_guard_register_snapshot
    .global audit_guard_fired_flag
    .global audit_guard_vcount
    .global audit_guard_heartbeat

    .global pc090oj_dma_test_fired_flag
    .global pc090oj_dma_test_mismatch_offset
    .global pc090oj_dma_test_expected_word
    .global pc090oj_dma_test_actual_word
    .global pc090oj_dma_test_actual_buffer
    .global pc090oj_dma_test_heartbeat

    .extern rastan_pc090oj
    .extern pc090oj_slot_lut
    .extern pc090oj_blank_code_bitset
    .extern pc090oj_opaque_bbox
    .extern genesistan_hook_tilemap_bg_fill
    .extern genesistan_hook_tilemap_fg_fill
    .extern genesistan_hook_pc080sn_bg_scroll_fill
    .extern genesistan_hook_pc080sn_fg_scroll_fill

    .equ VDP_DATA,      0x00C00000
    .equ VDP_CTRL,      0x00C00004
    .equ SPRITE_TILE_BASE, 1024
    .equ ARCADE_ROM_BASE, 0x00000200
    .equ PC090OJ_HW_BASE, 0x00D00000
    .equ PC090OJ_HW_ACTIVE_END, 0x00D00800

    /* ------------------------------------------------------------------ *
     * Build 0147: PC090OJ viewport coordinate + opaque-clip constants.   *
     * Named so sprite/background alignment is easy to read and to tune   *
     * during later emulator, gameplay, and real-CRT testing.             *
     * ------------------------------------------------------------------ */
    /* 16x16 sprite cell geometry. */
    .equ PC090OJ_PATTERN_WIDTH,   16
    .equ PC090OJ_PATTERN_HEIGHT,  16
    .equ PC090OJ_PATTERN_MAX_ROW, 15    /* PC090OJ_PATTERN_HEIGHT - 1 */
    .equ PC090OJ_PATTERN_MAX_COL, 15    /* PC090OJ_PATTERN_WIDTH  - 1 */
    /* Arcade PC090OJ non-flipped coordinate inversion (MAME taito/pc090oj.cpp:
     * x = 320 - x - 16, y = 256 - y - 16 when the flip-screen ctrl bit is clear). */
    .equ PC090OJ_FLIP_X_TERM, 304       /* 320 - PC090OJ_PATTERN_WIDTH  */
    .equ PC090OJ_FLIP_Y_TERM, 240       /* 256 - PC090OJ_PATTERN_HEIGHT */
    /* Arcade -> Genesis display-origin alignment.  The background plane applies
     * VDP_DISPLAY_ORIGIN_Y_BIAS(=8) / _X_BIAS(=16) in vdp_comm.s so the arcade
     * visible-area origin (raster Y=8, per rastan.cpp set_visarea 8..247) maps to
     * Genesis display line 0.  Sprites use the SAME origin so sprite/background
     * stay vertically aligned; this also places the arcade top margin above the
     * Genesis viewport, where its records clip out naturally.  Configurable. */
    .equ PC090OJ_TO_GENESIS_Y_OFFSET, -8   /* = -VDP_DISPLAY_ORIGIN_Y_BIAS */
    .equ PC090OJ_TO_GENESIS_X_OFFSET,  0   /* frontend X already aligned; tune later */
    /* Effective sprite clip rectangle = intersection of the arcade visible area
     * (raster 8..247 -> Genesis 0..239 after the Y origin) and the Genesis output
     * viewport (0..223, 0..319).  The Genesis bounds bind; ends are exclusive. */
    .equ GENESIS_VIEWPORT_LEFT,   0
    .equ GENESIS_VIEWPORT_RIGHT,  320
    .equ GENESIS_VIEWPORT_TOP,    0
    .equ GENESIS_VIEWPORT_BOTTOM, 224
    /* Genesis SAT coordinate biases (SAT value = screen coord + bias). */
    .equ PC090OJ_SAT_Y_BIAS, 0x80
    .equ PC090OJ_SAT_X_BIAS, 0x80

/* ------------------------------------------------------------------------- */
/* Internal helpers                                                          */
/* ------------------------------------------------------------------------- */

/* d0=PC090OJ record index.  Candidate state is helper-derived; mirror remains truth. */
.Lpc090oj_candidate_set_d0:
    movem.l %d1-%d3/%a0, -(%sp)
    move.w  %d0, %d1
    andi.w  #0x00FF, %d1
    move.w  %d1, %d2
    lsr.w   #3, %d1
    andi.w  #0x0007, %d2
    lea     pc090oj_candidate_bitset, %a0
    move.b  0(%a0,%d1.w), %d3
    bset    %d2, %d3
    move.b  %d3, 0(%a0,%d1.w)
    movem.l (%sp)+, %d1-%d3/%a0
    rts

/* d2=byte offset inside the active 0x800-byte PC090OJ mirror. */
.Lpc090oj_candidate_set_offset_d2:
    move.l  %d0, -(%sp)
    move.w  %d2, %d0
    lsr.w   #3, %d0
    bsr     .Lpc090oj_candidate_set_d0
    move.l  (%sp)+, %d0
    rts

/* d6=PC090OJ record index.  Clear only after full-record code-zero decode. */
.Lpc090oj_candidate_clear_d6:
    movem.l %d0-%d3/%a0, -(%sp)
    move.w  %d6, %d1
    andi.w  #0x00FF, %d1
    move.w  %d1, %d2
    lsr.w   #3, %d1
    andi.w  #0x0007, %d2
    lea     pc090oj_candidate_bitset, %a0
    move.b  0(%a0,%d1.w), %d3
    bclr    %d2, %d3
    move.b  %d3, 0(%a0,%d1.w)
    movem.l (%sp)+, %d0-%d3/%a0
    rts

/* Legacy producer bridge (Build 0142): the unconverted per-site hooks publish
 * their arcade sprite record into the mirror and set the per-record candidate.
 * The staged SAT is no longer written here; it is rebuilt from the mirror by
 * .Lpc090oj_sync_record_from_mirror during VBlank (dirty candidates) so a single
 * retained renderer owns the SAT.  d0=record index; d1=word0,d2=Y,d3=code,d4=X.
 * Preserves d0-d4/d7 and a1..a6 for the calling producer loops.
 */
.Lpc090oj_emit_slot:
    movem.l %d5/%d6/%a0, -(%sp)
    move.w  %d0, %d6
    lsl.w   #3, %d6
    lea     pc090oj_object_ram, %a0
    adda.w  %d6, %a0
    move.w  %d1, (%a0)
    move.w  %d2, 2(%a0)
    move.w  %d3, 4(%a0)
    move.w  %d4, 6(%a0)
    bsr     .Lpc090oj_candidate_set_d0   /* d0 = record */
    addq.w  #1, pc090oj_producer_write_count
    move.w  #1, pc090oj_mirror_dirty
    movem.l (%sp)+, %d5/%d6/%a0
    rts

/* d0=slot clears slot */
.Lpc090oj_clear_slot:
    moveq   #0, %d1
    move.w  #0x0180, %d2
    moveq   #0, %d3
    moveq   #0, %d4
    moveq   #0, %d5
    moveq   #0, %d6
    moveq   #0, %d7
    bsr     .Lpc090oj_emit_slot
    rts

/* A1=PC090OJ HW address, D0=word value.  Writes only the active 0x800-byte mirror. */
.Lpc090oj_mirror_write_word_a1_d0:
    move.l  %a2, -(%sp)
    move.l  %a1, %d2
    cmpi.l  #PC090OJ_HW_BASE, %d2
    blo.s   .Lpc090oj_mirror_word_oob
    cmpi.l  #PC090OJ_HW_ACTIVE_END, %d2
    bhs.s   .Lpc090oj_mirror_word_oob
    subi.l  #PC090OJ_HW_BASE, %d2
    bsr     .Lpc090oj_candidate_set_offset_d2
    lea     pc090oj_object_ram, %a2
    adda.l  %d2, %a2
    move.w  %d0, (%a2)
    addq.w  #1, pc090oj_producer_write_count
    move.w  #1, pc090oj_mirror_dirty
    move.l  (%sp)+, %a2
    rts
.Lpc090oj_mirror_word_oob:
    addq.w  #1, pc090oj_producer_oob_count
    move.l  (%sp)+, %a2
    rts

/* A1=PC090OJ HW address, D0=byte value.  Used for 0x3B802 byte stores. */
.Lpc090oj_mirror_write_byte_a1_d0:
    move.l  %a2, -(%sp)
    move.l  %a1, %d2
    cmpi.l  #PC090OJ_HW_BASE, %d2
    blo.s   .Lpc090oj_mirror_byte_oob
    cmpi.l  #PC090OJ_HW_ACTIVE_END, %d2
    bhs.s   .Lpc090oj_mirror_byte_oob
    subi.l  #PC090OJ_HW_BASE, %d2
    bsr     .Lpc090oj_candidate_set_offset_d2
    lea     pc090oj_object_ram, %a2
    adda.l  %d2, %a2
    move.b  %d0, (%a2)
    addq.w  #1, pc090oj_producer_write_count
    move.w  #1, pc090oj_mirror_dirty
    move.l  (%sp)+, %a2
    rts
.Lpc090oj_mirror_byte_oob:
    addq.w  #1, pc090oj_producer_oob_count
    move.l  (%sp)+, %a2
    rts

/* Converted semantic family (Build 0142): the complete 22-object work-RAM block
 * shared by arcade 0x041DAE / 0x041F5E / 0x045DFA.  Block A = 18 records at
 * A5+0x11B2, block B = 4 records at A5+0x0170; tuple = {word0, Y, code, X}.
 * Each record is written once into the mirror (exact arcade store), then
 * synchronized directly from the mirror and its superseded candidate cleared.
 * It does NOT set a candidate; later unconverted writes to the same record
 * re-set the candidate and VBlank re-syncs it (§9-E.2/§9-E.3).
 */
pc090oj_workram_block_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x11B2(%a5), %a0
    moveq   #0, %d0
.Lwbs_block_a:
    move.w  (%a0), %d1
    move.w  2(%a0), %d2
    move.w  4(%a0), %d3
    move.w  6(%a0), %d4
    bsr     .Lpc090oj_family_apply_record
    adda.w  #8, %a0
    addq.w  #1, %d0
    cmpi.w  #18, %d0
    blo.s   .Lwbs_block_a

    lea     0x0170(%a5), %a0
    moveq   #18, %d0
.Lwbs_block_b:
    move.w  (%a0), %d1
    move.w  2(%a0), %d2
    move.w  4(%a0), %d3
    move.w  6(%a0), %d4
    bsr     .Lpc090oj_family_apply_record
    adda.w  #8, %a0
    addq.w  #1, %d0
    cmpi.w  #22, %d0
    blo.s   .Lwbs_block_b
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* d0=record, d1=word0, d2=Y, d3=code, d4=X.  Write the mirror once, then sync
 * from the mirror and clear the superseded candidate, inside a VINT-masked
 * critical section so a VBlank commit never observes a half-applied structural
 * change (§9-C interrupt safety).
 */
.Lpc090oj_family_apply_record:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.w  %sr, -(%sp)
    ori.w   #0x0700, %sr
    move.w  %d0, %d6                     /* record */
    move.w  %d6, %d5
    lsl.w   #3, %d5
    lea     pc090oj_object_ram, %a0
    adda.w  %d5, %a0
    move.w  %d1, (%a0)
    move.w  %d2, 2(%a0)
    move.w  %d3, 4(%a0)
    move.w  %d4, 6(%a0)
    addq.w  #1, pc090oj_producer_write_count
    move.w  #1, pc090oj_mirror_dirty
    bsr     .Lpc090oj_sync_record_from_mirror   /* d6 = record */
    bsr     .Lpc090oj_candidate_clear_d6        /* d6 = record */
    move.w  (%sp)+, %sr
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* ------------------------------------------------------------------------- */
/* 17 helpers                                                                */
/* ------------------------------------------------------------------------- */

/* Build 0146 faithful translation of arcade 0x03B902.
 * Arcade body: lea 0xD00088,%a1 (records 17..21); tst.w %d1; bne fill.
 *   clear path (d1==0): lea 0x3B984,%a0; moveq #5,%d1; bsr 0x3B930   -> copy the
 *     5-record table at arcade 0x3B984 (Genesis 0x3BB84) into records 17..21.
 *   fill path  (d1!=0): move.b %d1,2(%a1); addq.l #8,%a1  x5  -> write the byte
 *     d1 to the Y-high byte (offset 2) of records 17..21 only.
 * The prior Build 0142-era body wrote full descriptors to records 0..4, which
 * clobbered record 4 (the HIGH SCORE "GH" glyph) that the arcade never touches.
 * Registers are fully preserved (movem), matching the prior helper's contract.
 */
genesistan_pc090oj_hook_target_3b902:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    tst.w   %d1
    bne.s   .Lhook_3b902_fill
    /* clear path: table copy into records 17..21 via the faithful 0x3B930 helper */
    lea     0x00D00088, %a1
    lea     0x0003BB84, %a0                 /* arcade 0x3B984 table, +0x200 */
    moveq   #5, %d1
    bsr     genesistan_pc090oj_hook_target_3b930
    bra.s   .Lhook_3b902_done
.Lhook_3b902_fill:
    /* fill path: write byte d1 to the Y-high byte (offset 2) of records 17..21 */
    lea     0x00D0008A, %a1                 /* 0xD00088 + 2 (record 17 Y-high) */
    moveq   #5, %d5
.Lhook_3b902_fill_loop:
    move.w  %d1, %d0
    bsr     .Lpc090oj_mirror_write_byte_a1_d0
    adda.l  #8, %a1
    subq.w  #1, %d5
    bne.s   .Lhook_3b902_fill_loop
.Lhook_3b902_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_target_3b926:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    moveq   #5, %d0
.Lhook_3b926_loop:
    bsr     .Lpc090oj_clear_slot
    addq.w  #1, %d0
    cmpi.w  #14, %d0
    blo.s   .Lhook_3b926_loop
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_target_3b930:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.w  %d1, %d6
.Lhook_3b930_loop:
    tst.w   %d6
    beq.s   .Lhook_3b930_done

    moveq   #0, %d0                  /* word0 = 0 */
    bsr     .Lpc090oj_mirror_write_word_a1_d0
    addq.l  #2, %a1

    moveq   #0, %d0                  /* word1 = zero-extended Y byte */
    move.b  (%a0)+, %d0
    bsr     .Lpc090oj_mirror_write_word_a1_d0
    addq.l  #2, %a1

    moveq   #0, %d0                  /* word2 = zero-extended code byte */
    move.b  (%a0)+, %d0
    bsr     .Lpc090oj_mirror_write_word_a1_d0
    addq.l  #2, %a1

    move.w  (%a0)+, %d7              /* word3 = transformed X word */
    jsr     (0x0005B712).l
    move.w  %d7, %d0
    bsr     .Lpc090oj_mirror_write_word_a1_d0
    addq.l  #2, %a1

    subq.w  #1, %d6
    bra.s   .Lhook_3b930_loop
.Lhook_3b930_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_target_41dae:
    bsr     pc090oj_workram_block_sprites
    rts

genesistan_pc090oj_hook_target_41f5e:
    bsr     pc090oj_workram_block_sprites
    rts

genesistan_pc090oj_hook_target_45dfa:
    bsr     pc090oj_workram_block_sprites
    rts

genesistan_pc090oj_hook_target_59f5e:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    moveq   #0, %d0
.Lhook_59f5e_clear_slots:
    bsr     .Lpc090oj_clear_slot
    addq.w  #1, %d0
    cmpi.w  #8, %d0
    blo.s   .Lhook_59f5e_clear_slots

    /* preserve arcade workram tuple writes at A5+0x0170 */
    lea     0x0170(%a5), %a0
    moveq   #3, %d1
.Lhook_59f5e_workram_loop:
    move.w  #0x0080, (%a0)+
    move.w  #0x0000, (%a0)+
    move.w  #0x0000, (%a0)+
    move.w  #0x0000, (%a0)+
    dbra    %d1, .Lhook_59f5e_workram_loop

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* PC090OJ ctrl register (word offset 0x0DFF / HW 0x00D01BFE).
 * Bit 0 is the global-flip control (a change flips every sprite on/off screen),
 * so an actual change reevaluates all 256 records by requesting a full
 * candidate sweep processed at the next VBlank (§9-E.4).
 */
genesistan_pc090oj_ctrl_set_1:
    cmpi.w  #1, pc090oj_ctrl_shadow
    beq.s   .Lctrl_set_1_done
    move.w  #1, pc090oj_ctrl_shadow
    bsr     .Lpc090oj_set_all_candidates
.Lctrl_set_1_done:
    rts

genesistan_pc090oj_ctrl_set_0:
    tst.w   pc090oj_ctrl_shadow
    beq.s   .Lctrl_set_0_done
    clr.w   pc090oj_ctrl_shadow
    bsr     .Lpc090oj_set_all_candidates
.Lctrl_set_0_done:
    rts

/* External sprite_ctrl at HW 0x00380000.  D0 holds the arcade value; its colour
 * bank feeds sprite palette selection.  On an actual change, reevaluate (a full
 * sweep is a safe superset of the represented-only palette refresh).
 */
genesistan_pc090oj_sprite_ctrl_write_d0:
    cmp.w   pc090oj_sprite_ctrl_shadow, %d0
    beq.s   .Lsprite_ctrl_write_done
    move.w  %d0, pc090oj_sprite_ctrl_shadow
    bsr     .Lpc090oj_set_all_candidates
.Lsprite_ctrl_write_done:
    rts

genesistan_pc090oj_sprite_ctrl_clear:
    tst.w   pc090oj_sprite_ctrl_shadow
    beq.s   .Lsprite_ctrl_clear_done
    clr.w   pc090oj_sprite_ctrl_shadow
    bsr     .Lpc090oj_set_all_candidates
.Lsprite_ctrl_clear_done:
    rts

genesistan_hook_3ad44_dispatch:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* A0 dispatch:
     *   tilemap: [0x00C00000,0x00C10000)
     *   PC090OJ: [0x00D00000,0x00D00800)
     *   else:    audit fall-through
     */
    move.l  %a0, %d2
    cmpi.l  #0x00C00000, %d2
    blo.s   .Lhook_3ad44_check_pc090oj
    cmpi.l  #0x00C10000, %d2
    blo.s   .Lhook_3ad44_tilemap

.Lhook_3ad44_check_pc090oj:
    cmpi.l  #0x00D00000, %d2
    blo     .Lhook_3ad44_audit
    cmpi.l  #0x00D00800, %d2
    bhs     .Lhook_3ad44_audit

    /* PC090OJ branch: preserve the arcade long-fill into active object RAM. */
    move.l  %a0, %d2
    subi.l  #0x00D00000, %d2
    bmi     .Lhook_3ad44_finish
    cmpi.l  #0x00000800, %d2
    bhs     .Lhook_3ad44_finish

    lea     pc090oj_object_ram, %a1
    adda.l  %d2, %a1
    move.w  %d1, %d3
.Lhook_3ad44_pc090oj_long_fill_loop:
    tst.w   %d3
    beq     .Lhook_3ad44_finish
    cmpi.l  #0x00000800, %d2
    bhs     .Lhook_3ad44_finish
    swap    %d0
    move.w  %d0, (%a1)+
    swap    %d0
    bsr     .Lpc090oj_candidate_set_offset_d2
    addq.l  #2, %d2
    cmpi.l  #0x00000800, %d2
    bhs     .Lhook_3ad44_finish
    move.w  %d0, (%a1)+
    bsr     .Lpc090oj_candidate_set_offset_d2
    addq.l  #2, %d2
    move.w  #1, pc090oj_mirror_dirty
    subq.w  #1, %d3
    bra.s   .Lhook_3ad44_pc090oj_long_fill_loop

.Lhook_3ad44_tilemap:
    cmpi.l  #0x00C04000, %d2
    blo.s   .Lhook_3ad44_bg_names
    cmpi.l  #0x00C08000, %d2
    blo.s   .Lhook_3ad44_bg_scroll
    cmpi.l  #0x00C0C000, %d2
    blo.s   .Lhook_3ad44_fg_names
    bsr     genesistan_hook_pc080sn_fg_scroll_fill
    bra     .Lhook_3ad44_finish

.Lhook_3ad44_bg_names:
    bsr     genesistan_hook_tilemap_bg_fill
    bra     .Lhook_3ad44_finish

.Lhook_3ad44_bg_scroll:
    bsr     genesistan_hook_pc080sn_bg_scroll_fill
    bra     .Lhook_3ad44_finish

.Lhook_3ad44_fg_names:
    bsr     genesistan_hook_tilemap_fg_fill
    bra     .Lhook_3ad44_finish

.Lhook_3ad44_audit:
    /* Reuse §7.3 audit-guard capture + heartbeat halt loop. */
    move.l  60(%sp), %d0
    move.l  %d0, audit_guard_caller_pc

    lea     audit_guard_register_snapshot, %a1
    moveq   #(15 - 1), %d0
.Lhook_3ad44_snap:
    move.l  (%sp,%d0.w*4), %d1
    move.l  %d1, (%a1)+
    dbra    %d0, .Lhook_3ad44_snap

    move.w  0x00C00008, audit_guard_vcount
    move.w  #0x3AD4, audit_guard_fired_flag
    bra     .Lag_halt_loop

.Lhook_3ad44_finish:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_init_priority_3ad84:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7

    moveq   #76, %d0
    moveq   #0, %d1
    move.w  #0x00C8, %d2
    moveq   #0, %d3
    move.w  #0x0160, %d4
    moveq   #0, %d5
    moveq   #0x0002, %d6            /* priority-ladder gate bit */
.Lhook_3ad84_loop:
    bsr     .Lpc090oj_emit_slot
    addi.w  #0x0010, %d2
    addq.w  #1, %d0
    cmpi.w  #80, %d0
    blo.s   .Lhook_3ad84_loop

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_score_digit_3b802:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* Preserve arcade structure at 0x3B802: record = 10 bytes at 0x3B87E+mode*10 */
    clr.l   %d5
    movea.l %d5, %a6                 /* leading-zero state */

    mulu.w  #10, %d0
    lea     .Lhook_3b802_record_table, %a0
    adda.w  %d0, %a0

    clr.w   %d0
    move.b  (%a0), %d0               /* digit count */
    cmpi.w  #1, %d0
    bne.s   .Lhook_3b802_count_ready
    moveq   #1, %d5
    movea.l %d5, %a6
.Lhook_3b802_count_ready:
    move.b  1(%a0), %d6              /* Y low-byte source */
    movea.l 2(%a0), %a4              /* arcade PC090OJ destination pointer */
    movea.l 6(%a0), %a2              /* arcade score-data source pointer */

    /* 0x10xxxx table pointers are arcade workram; remap to A5-relative Genesis WRAM */
    move.l  %a2, %d2
    subi.l  #0x00100000, %d2
    movea.l %a5, %a2
    adda.l  %d2, %a2

    moveq   #0, %d3
    move.w  %d0, %d3
    movea.l %d3, %a3                 /* loop counter */

.Lhook_3b802_loop:
    move.l  %a3, %d2
    tst.w   %d2
    beq     .Lhook_3b802_done

    btst    #0, %d2
    beq.s   .Lhook_3b802_even_nibble

    moveq   #0, %d1
    move.b  (%a2), %d1
    andi.w  #0x000F, %d1
    bsr     .Lhook_3b802_visflag
    addi.w  #0x002A, %d1
    subq.l  #1, %a2
    bra.s   .Lhook_3b802_emit

.Lhook_3b802_even_nibble:
    moveq   #0, %d1
    move.b  (%a2), %d1
    lsr.b   #4, %d1
    andi.w  #0x000F, %d1
    bsr     .Lhook_3b802_visflag
    addi.w  #0x002A, %d1

.Lhook_3b802_emit:
    /* Preserve arcade destination writes: byte to +2/+3, digit word to +4. */
    movea.l %a4, %a1
    adda.w  #2, %a1
    move.w  %d4, %d0
    bsr     .Lpc090oj_mirror_write_byte_a1_d0

    movea.l %a4, %a1
    adda.w  #3, %a1
    moveq   #0, %d0
    move.b  %d6, %d0
    bsr     .Lpc090oj_mirror_write_byte_a1_d0

    movea.l %a4, %a1
    adda.w  #4, %a1
    move.w  %d1, %d0
    bsr     .Lpc090oj_mirror_write_word_a1_d0

.Lhook_3b802_next:
    subq.l  #8, %a4
    subq.l  #1, %a3
    bra     .Lhook_3b802_loop

.Lhook_3b802_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lhook_3b802_visflag:
    move.l  %a6, %d5
    bne.s   .Lhook_3b802_vis_nonzero
    tst.w   %d1
    bne.s   .Lhook_3b802_vis_nonzero
    moveq   #1, %d4                   /* leading zero */
    rts

.Lhook_3b802_vis_nonzero:
    moveq   #1, %d5
    movea.l %d5, %a6
    moveq   #0, %d4
    rts

.Lhook_3b802_record_table:
    .byte 0x06,0x10,0x00,0xD0,0x01,0x08,0x00,0x10,0xC1,0x1E
    .byte 0x06,0x10,0x00,0xD0,0x01,0x50,0x00,0x10,0xC1,0x1E
    .byte 0x06,0x10,0x00,0xD0,0x00,0xD8,0x00,0x10,0xC1,0x42
    .byte 0x01,0xE8,0x00,0xD0,0x00,0xA8,0x00,0x10,0xC1,0x17
    .byte 0x01,0xE4,0x00,0xD0,0x00,0x88,0x00,0x10,0xC1,0x03
    .align 2

genesistan_pc090oj_hook_slot_init_54052:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* Phase A text-RAM clear loops replicated verbatim */
    movea.l #0x0010D1D2, %a1
    move.w  #6, %d2
.Lhook_54052_loop1:
    move.w  #3, (%a1)+
    move.w  #0, (%a1)+
    move.w  #0, (%a1)+
    move.w  #0, (%a1)+
    subq.w  #1, %d2
    bne.s   .Lhook_54052_loop1

    move.w  #4, %d2
    movea.l #0x0010D1B2, %a1
.Lhook_54052_loop2:
    move.w  #3, (%a1)+
    move.w  #0, (%a1)+
    move.w  #0, (%a1)+
    move.w  #0, (%a1)+
    subq.w  #1, %d2
    bne.s   .Lhook_54052_loop2

    movea.l #0x0010D1F2, %a1
    move.w  #6, %d2
.Lhook_54052_loop3:
    move.w  #3, (%a1)+
    move.w  #0, (%a1)+
    move.w  #0, (%a1)+
    move.w  #0, (%a1)+
    subq.w  #1, %d2
    bne.s   .Lhook_54052_loop3

    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7

    moveq   #72, %d0
.Lhook_54052_emit:
    move.w  #0x0003, %d1
    move.w  #0x0000, %d2
    move.w  #0x0000, %d3
    move.w  #0x0000, %d4
    moveq   #0, %d5
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    addq.w  #1, %d0
    cmpi.w  #76, %d0
    blo.s   .Lhook_54052_emit

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_sprite_update_54810:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7

    movea.l #ARCADE_ROM_BASE+0x0005DA5E, %a0
    mulu.w  #24, %d0
    adda.w  %d0, %a0

    moveq   #44, %d0
    moveq   #4, %d6
.Lhook_54810_loop:
    move.w  4(%a0), %d1

    moveq   #0, %d2
    move.b  3(%a0), %d2
    ext.w   %d2
    add.w   0x129C(%a5), %d2
    addq.w  #1, %d2
    andi.w  #0x01FF, %d2

    move.w  (%a0), %d3

    moveq   #0, %d4
    move.b  2(%a0), %d4
    ext.w   %d4
    add.w   0x129A(%a5), %d4
    andi.w  #0x01FF, %d4

    moveq   #0, %d5
    move.w  %d6, -(%sp)              /* save loop counter */
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    move.w  (%sp)+, %d6              /* restore loop counter */

    adda.w  #6, %a0
    addq.w  #1, %d0
    subq.w  #1, %d6
    bne.s   .Lhook_54810_loop

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_sprite_decay_5607c:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  0x1392(%a5), %d0
    andi.w  #0x0003, %d0
    bne.s   .Lhook_5607c_done

    clr.w   0x10AE(%a5)
    clr.w   0x10B0(%a5)

    moveq   #56, %d0
.Lhook_5607c_loop:
    cmpi.w  #64, %d0
    bhs.s   .Lhook_5607c_done

    move.w  %d0, %d1
    mulu.w  #12, %d1
    lea     staged_sprite_descriptor_table, %a0
    adda.l  %d1, %a0

    btst    #0, (%a0)
    beq.s   .Lhook_5607c_next

    move.w  2(%a0), %d2
    subq.w  #1, %d2
    andi.w  #0x01FF, %d2
    move.w  %d2, 2(%a0)

    move.w  6(%a0), %d1
    move.w  8(%a0), %d3
    move.w  4(%a0), %d4
    cmpi.w  #0x0010, %d2
    bne.s   .Lhook_5607c_keep_tile
    clr.w   %d3
    move.w  %d3, 8(%a0)
.Lhook_5607c_keep_tile:
    moveq   #0, %d5
    moveq   #0, %d6
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
    bsr     .Lpc090oj_emit_slot

.Lhook_5607c_next:
    addq.w  #1, %d0
    bra.s   .Lhook_5607c_loop

.Lhook_5607c_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_copy_56114:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7

    moveq   #64, %d0
.Lhook_56114_loop:
    cmpi.w  #68, %d0
    bhs.s   .Lhook_56114_done
    move.w  (%a0), %d1
    cmpi.w  #-1, %d1
    beq.s   .Lhook_56114_done
    move.w  2(%a0), %d2
    move.w  4(%a0), %d3
    move.w  6(%a0), %d4
    moveq   #0, %d5
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    adda.w  #8, %a0
    addq.w  #1, %d0
    bra.s   .Lhook_56114_loop

.Lhook_56114_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_zero_fill_56440:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    moveq   #68, %d0
.Lhook_56440_loop:
    cmpi.w  #72, %d0
    bhs.s   .Lhook_56440_done
    bsr     .Lpc090oj_clear_slot
    addq.w  #1, %d0
    bra.s   .Lhook_56440_loop

.Lhook_56440_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_status_sprite_5a098:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7

    moveq   #30, %d0
    move.w  #0x0010, %d4
.Lhook_5a098_loop:
    cmpi.w  #44, %d0
    bhs.s   .Lhook_5a098_done
    moveq   #0, %d1
    move.w  #0x00E8, %d2
    move.w  %d0, %d3
    addi.w  #0x03CA, %d3
    moveq   #0, %d5
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    addi.w  #0x0010, %d4
    addq.w  #1, %d0
    bra.s   .Lhook_5a098_loop

.Lhook_5a098_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_audit_guard:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* return address for invoking site */
    move.l  60(%sp), %d0
    move.l  %d0, audit_guard_caller_pc

    /* snapshot registers (d0-d7,a0-a6 = 15 longs) */
    lea     audit_guard_register_snapshot, %a1
    moveq   #(15 - 1), %d0
.Lag_snap:
    move.l  (%sp,%d0.w*4), %d1
    move.l  %d1, (%a1)+
    dbra    %d0, .Lag_snap

    move.w  0x00C00008, audit_guard_vcount
    move.w  #0x510E, audit_guard_fired_flag

.Lag_halt_loop:
    move.b  audit_guard_heartbeat, %d0
    addq.b  #1, %d0
    move.b  %d0, audit_guard_heartbeat
    bra     .Lag_halt_loop

/* ------------------------------------------------------------------------- */
/* VBlank sprite prepare / commit split                                      */
/* ------------------------------------------------------------------------- */

vdp_prepare_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    tst.w   pc090oj_scan_active
    bne.s   .Lprep_inited
    bsr     .Lpc090oj_renderer_init
.Lprep_inited:
    tst.w   pc090oj_bootstrap_pending
    beq.s   .Lprep_no_bootstrap
    clr.w   pc090oj_bootstrap_pending
    bsr     .Lpc090oj_set_all_candidates
.Lprep_no_bootstrap:
    bsr     .Lpc090oj_process_candidates
    /* Expose represented count for logging / Build 0141 parity checks. */
    move.w  pc090oj_represented_count, %d0
    move.w  %d0, staged_sprite_active_count
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* Keep vdp_commit_sprites as a required-symbol alias, but make it VRAM-only. */
vdp_commit_sprites:
vdp_commit_sprites_vram:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lvcs_tile_dma
    tst.w   pc090oj_sat_dirty
    beq.s   .Lvcs_commit_done
    bsr     .Lvcs_sat_dma
    clr.w   pc090oj_sat_dirty
.Lvcs_commit_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* ------------------------------------------------------------------------- */
/* Build 0142 retained-identity translation engine                          */
/* ------------------------------------------------------------------------- */

/* One-time initialisation: record_to_slot / worklist_entry_for_slot = 0xFF,
 * every bitmap and counter cleared, staged SAT slot 0 hidden + terminating,
 * and a single 256-record bootstrap requested so pre-init mirror state is
 * captured exactly once without any recurring scan.  BSS zero at reset does
 * not cover the 0xFF defaults, so this must run before the first sync.
 */
.Lpc090oj_renderer_init:
    movem.l %d7/%a0, -(%sp)
    lea     record_to_slot, %a0
    move.w  #(256 - 1), %d7
.Lri_rts_loop:
    move.b  #0xFF, (%a0)+
    dbra    %d7, .Lri_rts_loop
    lea     represented_records, %a0
    move.w  #(32 - 1), %d7
.Lri_rep_loop:
    clr.b   (%a0)+
    dbra    %d7, .Lri_rep_loop
    lea     waiting_records, %a0
    move.w  #(32 - 1), %d7
.Lri_wait_loop:
    clr.b   (%a0)+
    dbra    %d7, .Lri_wait_loop
    lea     used_sat_slots, %a0
    move.w  #(16 - 1), %d7
.Lri_used_loop:
    clr.b   (%a0)+
    dbra    %d7, .Lri_used_loop
    lea     worklist_entry_for_slot, %a0
    move.w  #(80 - 1), %d7
.Lri_wef_loop:
    move.b  #0xFF, (%a0)+
    dbra    %d7, .Lri_wef_loop
    clr.w   pc090oj_represented_count
    clr.w   pc090oj_tile_dma_count
    move.w  #1, pc090oj_bootstrap_pending
    bsr     .Lpc090oj_write_empty_slot0
    move.w  #1, pc090oj_scan_active
    movem.l (%sp)+, %d7/%a0
    rts

/* Set every candidate bit (bootstrap / global reevaluation). */
.Lpc090oj_set_all_candidates:
    movem.l %d7/%a0, -(%sp)
    lea     pc090oj_candidate_bitset, %a0
    move.w  #(32 - 1), %d7
.Lsac_loop:
    move.b  #0xFF, (%a0)+
    dbra    %d7, .Lsac_loop
    movem.l (%sp)+, %d7/%a0
    rts

/* Reset the per-interval worklist reservation map to 0xFF (called post-commit). */
.Lpc090oj_worklist_reset_map:
    movem.l %d7/%a0, -(%sp)
    lea     worklist_entry_for_slot, %a0
    move.w  #(80 - 1), %d7
.Lwrm_loop:
    move.b  #0xFF, (%a0)+
    dbra    %d7, .Lwrm_loop
    movem.l (%sp)+, %d7/%a0
    rts

/* Staged SAT slot 0 hidden + self-terminating (empty chain, §9-D.3). */
.Lpc090oj_write_empty_slot0:
    lea     staged_sprite_sat, %a1
    move.w  #0x01E0, (%a1)              /* Y fully offscreen */
    move.w  #0x0500, 2(%a1)            /* link 0 -> terminator */
    move.w  #0x0000, 4(%a1)
    move.w  #0x0000, 6(%a1)
    move.w  #1, pc090oj_sat_dirty
    rts

/* Walk the per-frame dirty candidates in ascending record order; sync each set
 * record from the mirror and clear its candidate.  Zero candidate bytes skip an
 * entire 8-record group so a stable no-work frame performs no decode or relink.
 */
.Lpc090oj_process_candidates:
    moveq   #0, %d6
.Lpc_loop:
    cmpi.w  #256, %d6
    bhs     .Lpc_done
    move.w  %d6, %d0
    andi.w  #0x0007, %d0
    bne.s   .Lpc_test
    move.w  %d6, %d1
    lsr.w   #3, %d1
    lea     pc090oj_candidate_bitset, %a0
    tst.b   0(%a0,%d1.w)
    bne.s   .Lpc_test
    addq.w  #8, %d6
    bra     .Lpc_loop
.Lpc_test:
    move.w  %d6, %d1
    lsr.w   #3, %d1
    lea     pc090oj_candidate_bitset, %a0
    move.b  0(%a0,%d1.w), %d2
    move.w  %d6, %d0
    andi.w  #0x0007, %d0
    btst    %d0, %d2
    beq.s   .Lpc_next
    bsr     .Lpc090oj_sync_record_from_mirror   /* d6 = record, preserved */
    move.w  %d6, %d1
    lsr.w   #3, %d1
    lea     pc090oj_candidate_bitset, %a0
    move.w  %d6, %d0
    andi.w  #0x0007, %d0
    bclr    %d0, 0(%a0,%d1.w)
.Lpc_next:
    addq.w  #1, %d6
    bra     .Lpc_loop
.Lpc_done:
    rts

/* Decode PC090OJ mirror record d6 (0..255).
 *   Out: d0 = 1 drawable / 0 not.
 *   When drawable: d1=word0(post-flip), d2=Y(signed screen), d3=code(0..0x0FFF),
 *                  d4=X(signed screen), d7=colbank.
 *   Clobbers d5, a0, a1.  Preserves d6.
 */
.Lpc090oj_decode_record:
    move.w  %d6, %d0
    lsl.w   #3, %d0
    lea     pc090oj_object_ram, %a0
    adda.w  %d0, %a0
    move.w  (%a0), %d1
    move.w  2(%a0), %d2
    move.w  4(%a0), %d3
    move.w  6(%a0), %d4

    andi.w  #0x1FFF, %d3
    beq     .Ldecode_notdraw
    cmpi.w  #0x1000, %d3
    bhs     .Ldecode_notdraw
    move.w  %d3, %d5
    lsr.w   #3, %d5
    lea     pc090oj_blank_code_bitset, %a1
    move.b  0(%a1,%d5.w), %d5
    move.w  %d3, %d0
    andi.w  #0x0007, %d0
    btst    %d0, %d5
    bne     .Ldecode_notdraw

    andi.w  #0x01FF, %d2
    cmpi.w  #0x0140, %d2
    bls.s   .Ldecode_y_ok
    subi.w  #0x0200, %d2
.Ldecode_y_ok:
    andi.w  #0x01FF, %d4
    cmpi.w  #0x0140, %d4
    bls.s   .Ldecode_x_ok
    subi.w  #0x0200, %d4
.Ldecode_x_ok:
    move.w  pc090oj_ctrl_shadow, %d5
    btst    #0, %d5
    bne.s   .Ldecode_no_flip
    move.w  #PC090OJ_FLIP_X_TERM, %d5
    sub.w   %d4, %d5
    move.w  %d5, %d4
    move.w  #PC090OJ_FLIP_Y_TERM, %d5
    sub.w   %d2, %d5
    move.w  %d5, %d2
    eori.w  #0xC000, %d1
.Ldecode_no_flip:
    /* Arcade -> Genesis viewport origin: aligns sprites with the background
     * (which applies the matching bias in vdp_comm.s) and places the arcade top
     * margin above the Genesis viewport, where clipped records drop out. */
    addi.w  #PC090OJ_TO_GENESIS_X_OFFSET, %d4
    addi.w  #PC090OJ_TO_GENESIS_Y_OFFSET, %d2

    /* Opaque-geometry viewport clip.  A record is drawable only when at least
     * one opaque pixel of its post-flip pattern intersects the effective clip
     * rectangle; fully-clipped records return not-drawable, so they receive no
     * SAT slot, link entry, tile work, or scanline capacity.  d3 = code
     * (0..0x0FFF); box bytes = [min_row, max_row, min_col, max_col] (unflipped). */
    move.w  %d3, %d0
    andi.w  #0x0FFF, %d0
    lsl.w   #2, %d0
    lea     pc090oj_opaque_bbox, %a1
    adda.w  %d0, %a1
    /* vertical opaque span (post vertical-flip) vs [TOP, BOTTOM) */
    moveq   #0, %d0
    move.b  0(%a1), %d0                    /* min_row */
    moveq   #0, %d5
    move.b  1(%a1), %d5                    /* max_row */
    btst    #15, %d1                       /* vflip (post-flip word0 bit 15) */
    beq.s   .Ldecode_vrows_ok
    neg.w   %d0
    addi.w  #PC090OJ_PATTERN_MAX_ROW, %d0  /* MAX_ROW - min_row */
    neg.w   %d5
    addi.w  #PC090OJ_PATTERN_MAX_ROW, %d5  /* MAX_ROW - max_row */
    exg     %d0, %d5                       /* d0 = eff top row, d5 = eff bottom row */
.Ldecode_vrows_ok:
    add.w   %d2, %d0                       /* opaque top    (screen Y) */
    add.w   %d2, %d5                       /* opaque bottom (screen Y) */
    cmpi.w  #GENESIS_VIEWPORT_BOTTOM, %d0
    bge     .Ldecode_notdraw               /* opaque top at/below viewport bottom */
    cmpi.w  #GENESIS_VIEWPORT_TOP, %d5
    blt     .Ldecode_notdraw               /* opaque bottom above viewport top */
    /* horizontal opaque span (post horizontal-flip) vs [LEFT, RIGHT) */
    moveq   #0, %d0
    move.b  2(%a1), %d0                    /* min_col */
    moveq   #0, %d5
    move.b  3(%a1), %d5                    /* max_col */
    btst    #14, %d1                       /* hflip (post-flip word0 bit 14) */
    beq.s   .Ldecode_hcols_ok
    neg.w   %d0
    addi.w  #PC090OJ_PATTERN_MAX_COL, %d0  /* MAX_COL - min_col */
    neg.w   %d5
    addi.w  #PC090OJ_PATTERN_MAX_COL, %d5  /* MAX_COL - max_col */
    exg     %d0, %d5                       /* d0 = eff left col, d5 = eff right col */
.Ldecode_hcols_ok:
    add.w   %d4, %d0                       /* opaque left  (screen X) */
    add.w   %d4, %d5                       /* opaque right (screen X) */
    cmpi.w  #GENESIS_VIEWPORT_RIGHT, %d0
    bge     .Ldecode_notdraw               /* opaque left at/right of viewport right */
    cmpi.w  #GENESIS_VIEWPORT_LEFT, %d5
    blt     .Ldecode_notdraw               /* opaque right left of viewport left */
    andi.w  #0x0FFF, %d3
    move.w  pc090oj_sprite_ctrl_shadow, %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
    moveq   #1, %d0
    rts
.Ldecode_notdraw:
    moveq   #0, %d0
    rts

/* Generic bitmap scans (base-68000; a1=base, d5=total bits). */
/* First SET bit >= d0.  Returns d0 = bit or d5.  Clobbers d1-d3. */
.Lbmp_first_ge:
    movem.l %d1-%d3, -(%sp)
    cmp.w   %d5, %d0
    bhs.s   .Lbfg_none
    move.w  %d0, %d1
    lsr.w   #3, %d1
    move.w  %d0, %d2
    andi.w  #0x0007, %d2
.Lbfg_byte:
    move.b  0(%a1,%d1.w), %d3
.Lbfg_bit:
    move.w  %d1, %d0
    lsl.w   #3, %d0
    add.w   %d2, %d0
    cmp.w   %d5, %d0
    bhs.s   .Lbfg_none
    btst    %d2, %d3
    bne.s   .Lbfg_found
    addq.w  #1, %d2
    cmpi.w  #8, %d2
    blo.s   .Lbfg_bit
    moveq   #0, %d2
    addq.w  #1, %d1
    bra.s   .Lbfg_byte
.Lbfg_none:
    move.w  %d5, %d0
.Lbfg_found:
    movem.l (%sp)+, %d1-%d3
    rts

/* Last SET bit <= d0.  Returns d0 = bit or 0xFFFF.  Clobbers d1-d3. */
.Lbmp_last_le:
    movem.l %d1-%d3, -(%sp)
    cmpi.w  #0, %d0
    blt.s   .Lbll_none
    cmp.w   %d5, %d0
    blo.s   .Lbll_start_ok
    move.w  %d5, %d0
    subq.w  #1, %d0
.Lbll_start_ok:
    move.w  %d0, %d1
    lsr.w   #3, %d1
    move.w  %d0, %d2
    andi.w  #0x0007, %d2
.Lbll_byte:
    move.b  0(%a1,%d1.w), %d3
.Lbll_bit:
    move.w  %d1, %d0
    lsl.w   #3, %d0
    add.w   %d2, %d0
    btst    %d2, %d3
    bne.s   .Lbll_found
    subq.w  #1, %d2
    bpl.s   .Lbll_bit
    moveq   #7, %d2
    subq.w  #1, %d1
    bpl.s   .Lbll_byte
.Lbll_none:
    move.w  #0xFFFF, %d0
    movem.l (%sp)+, %d1-%d3
    rts
.Lbll_found:
    movem.l (%sp)+, %d1-%d3
    rts

/* Represented head (lowest record) -> d0, or 256. */
.Lrep_first_ge:
    movem.l %d5/%a1, -(%sp)
    lea     represented_records, %a1
    move.w  #256, %d5
    bsr     .Lbmp_first_ge
    movem.l (%sp)+, %d5/%a1
    rts

/* Represented last set <= d0 -> d0, or 0xFFFF. */
.Lrep_last_le:
    movem.l %d5/%a1, -(%sp)
    lea     represented_records, %a1
    move.w  #256, %d5
    bsr     .Lbmp_last_le
    movem.l (%sp)+, %d5/%a1
    rts

/* Waiting first set >= d0 -> d0, or 256. */
.Lwait_first_ge:
    movem.l %d5/%a1, -(%sp)
    lea     waiting_records, %a1
    move.w  #256, %d5
    bsr     .Lbmp_first_ge
    movem.l (%sp)+, %d5/%a1
    rts

/* Lowest free non-zero used slot in [1,79] -> d0, or 0xFFFF.  Clobbers d1-d3,a1. */
.Lused_lowest_free_nonzero:
    movem.l %d1-%d3/%a1, -(%sp)
    lea     used_sat_slots, %a1
    moveq   #1, %d0
.Lulf_loop:
    cmpi.w  #80, %d0
    bhs.s   .Lulf_none
    move.w  %d0, %d1
    lsr.w   #3, %d1
    btst    %d0, 0(%a1,%d1.w)          /* memory dest -> bit index mod 8 */
    beq.s   .Lulf_found
    addq.w  #1, %d0
    bra.s   .Lulf_loop
.Lulf_none:
    move.w  #0xFFFF, %d0
.Lulf_found:
    movem.l (%sp)+, %d1-%d3/%a1
    rts

/* Highest used slot (0..79) -> d0, or 0xFFFF.  Clobbers d1-d3,a1. */
.Lused_highest:
    movem.l %d1-%d3/%a1, -(%sp)
    lea     used_sat_slots, %a1
    move.w  #79, %d0
.Luh_loop:
    move.w  %d0, %d1
    lsr.w   #3, %d1
    btst    %d0, 0(%a1,%d1.w)          /* memory dest -> bit index mod 8 */
    bne.s   .Luh_found
    subq.w  #1, %d0
    bpl.s   .Luh_loop
    move.w  #0xFFFF, %d0
.Luh_found:
    movem.l (%sp)+, %d1-%d3/%a1
    rts

/* Reserve/overwrite/cancel this slot's single worklist entry.  d0=slot, d1=code.
 * count only ever increments on the 0xFF->index first reservation, at most once
 * per slot per interval, so pc090oj_tile_dma_count can never exceed 80.
 * Returning to the resident code cancels the entry (code = 0xFFFF).
 */
.Lpc090oj_worklist_set:
    movem.l %d2-%d4/%a0-%a1, -(%sp)
    move.w  %d0, %d2                    /* slot */
    move.w  %d2, %d3
    add.w   %d3, %d3
    lea     sprite_tile_resident_code, %a0
    move.w  0(%a0,%d3.w), %d3          /* resident[slot] */
    lea     worklist_entry_for_slot, %a1
    moveq   #0, %d4
    move.b  0(%a1,%d2.w), %d4          /* reserved idx (0xFF none) */

    cmp.w   %d3, %d1
    bne.s   .Lwls_differ
    cmpi.b  #0xFF, %d4
    beq.s   .Lwls_done
    move.w  %d4, %d0
    lsl.w   #2, %d0
    lea     pc090oj_tile_dma_worklist, %a0
    adda.w  %d0, %a0
    move.w  #0xFFFF, 2(%a0)            /* cancel */
    bra.s   .Lwls_done
.Lwls_differ:
    cmpi.b  #0xFF, %d4
    bne.s   .Lwls_have_idx
    move.w  pc090oj_tile_dma_count, %d4
    cmpi.w  #80, %d4
    bhs.s   .Lwls_done                 /* defensive: impossible under <=80 slots */
    move.b  %d4, 0(%a1,%d2.w)
    addq.w  #1, %d4
    move.w  %d4, pc090oj_tile_dma_count
    subq.w  #1, %d4
    move.w  %d4, %d0
    lsl.w   #2, %d0
    lea     pc090oj_tile_dma_worklist, %a0
    adda.w  %d0, %a0
    move.w  %d2, (%a0)
    move.w  %d1, 2(%a0)
    bra.s   .Lwls_done
.Lwls_have_idx:
    move.w  %d4, %d0
    lsl.w   #2, %d0
    lea     pc090oj_tile_dma_worklist, %a0
    adda.w  %d0, %a0
    move.w  %d2, (%a0)
    move.w  %d1, 2(%a0)
.Lwls_done:
    movem.l (%sp)+, %d2-%d4/%a0-%a1
    rts

/* Free a slot: clear used bit and cancel its pending worklist entry, keeping the
 * reservation map so re-allocation reuses the same physical entry.  d0=slot.
 */
.Lpc090oj_free_slot:
    movem.l %d1-%d2/%a0-%a1, -(%sp)
    move.w  %d0, %d2
    lea     used_sat_slots, %a1
    move.w  %d2, %d1
    lsr.w   #3, %d1
    bclr    %d2, 0(%a1,%d1.w)
    lea     worklist_entry_for_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d2.w), %d1
    cmpi.b  #0xFF, %d1
    beq.s   .Lfs_done
    lsl.w   #2, %d1
    lea     pc090oj_tile_dma_worklist, %a0
    adda.w  %d1, %a0
    move.w  #0xFFFF, 2(%a0)
.Lfs_done:
    movem.l (%sp)+, %d1-%d2/%a0-%a1
    rts

/* Regenerate destination slot from the mirror.  d6=record, scratch_slot=dest,
 * scratch_link=link target slot.  Derives the slot-keyed tile index, queues the
 * pattern DMA (or cancels on return-to-resident), and sets ownership + used +
 * represented + sat_dirty.  Assumes the record decodes drawable.  Preserves d6.
 */
.Lpc090oj_place_record_in_slot:
    bsr     .Lpc090oj_decode_record     /* d1=word0,d2=Y,d3=code,d4=X,d7=colbank */
    move.w  .Lscratch_slot, %d0
    lsl.w   #3, %d0
    lea     staged_sprite_sat, %a1
    adda.w  %d0, %a1
    /* word0 Y (+ Genesis SAT Y bias) */
    move.w  %d2, %d5
    andi.w  #0x01FF, %d5
    addi.w  #PC090OJ_SAT_Y_BIAS, %d5
    andi.w  #0x01FF, %d5
    move.w  %d5, (%a1)
    /* word1 = size | link */
    move.w  .Lscratch_link, %d5
    andi.w  #0x007F, %d5
    ori.w   #0x0500, %d5
    move.w  %d5, 2(%a1)
    /* word2 = priority | palette | flips | tile-index(dest slot)
     * Build 0144 frontend sprite-palette split: effective arcade sprite bank
     * 0x30 (48) selects Genesis palette line 2, bank 0x33 (51) selects line 3;
     * every other effective bank keeps the existing (bank >> 4) & 3 mapping.
     * effective_arcade_bank = (word0 & 0x0F) | sprite_colbank (d7). */
    move.w  #0x8000, %d5
    move.w  %d1, %d0
    andi.w  #0x000F, %d0
    or.w    %d7, %d0                 /* d0 = effective_arcade_bank */
    cmpi.w  #0x0030, %d0
    bne.s   .Lpc090oj_palsel_not48
    moveq   #2, %d0                  /* bank 48 -> line 2 */
    bra.s   .Lpc090oj_palsel_have
.Lpc090oj_palsel_not48:
    cmpi.w  #0x0033, %d0
    bne.s   .Lpc090oj_palsel_general
    moveq   #3, %d0                  /* bank 51 -> line 3 */
    bra.s   .Lpc090oj_palsel_have
.Lpc090oj_palsel_general:
    lsr.w   #4, %d0
    andi.w  #0x0003, %d0             /* all other banks: existing (bank>>4)&3 */
.Lpc090oj_palsel_have:
    lsl.w   #8, %d0
    lsl.w   #5, %d0
    or.w    %d0, %d5
    move.w  %d1, %d0
    andi.w  #0x8000, %d0
    lsr.w   #3, %d0
    or.w    %d0, %d5
    move.w  %d1, %d0
    andi.w  #0x4000, %d0
    lsr.w   #3, %d0
    or.w    %d0, %d5
    move.w  .Lscratch_slot, %d0
    lsl.w   #2, %d0
    addi.w  #SPRITE_TILE_BASE, %d0
    andi.w  #0x07FF, %d0
    or.w    %d0, %d5
    move.w  %d5, 4(%a1)
    /* word3 X (+ Genesis SAT X bias) */
    move.w  %d4, %d5
    andi.w  #0x01FF, %d5
    addi.w  #PC090OJ_SAT_X_BIAS, %d5
    andi.w  #0x01FF, %d5
    move.w  %d5, 6(%a1)

    /* descriptor[slot] for legacy readers (5607c decay) */
    move.w  .Lscratch_slot, %d0
    mulu.w  #12, %d0
    lea     staged_sprite_descriptor_table, %a1
    adda.l  %d0, %a1
    move.w  #0x8001, (%a1)
    move.w  %d2, 2(%a1)
    move.w  %d4, 4(%a1)
    move.w  %d1, 6(%a1)
    move.w  %d3, 8(%a1)
    move.w  %d6, 10(%a1)

    /* worklist: queue/cancel pattern DMA for this slot */
    move.w  .Lscratch_slot, %d0
    move.w  %d3, %d1
    andi.w  #0x0FFF, %d1
    bsr     .Lpc090oj_worklist_set

    /* record_to_slot[record] = slot */
    move.w  .Lscratch_slot, %d0
    lea     record_to_slot, %a1
    move.b  %d0, 0(%a1,%d6.w)
    /* represented[record] = 1 */
    lea     represented_records, %a1
    move.w  %d6, %d1
    lsr.w   #3, %d1
    bset    %d6, 0(%a1,%d1.w)
    /* used_sat_slots[slot] = 1 */
    move.w  .Lscratch_slot, %d0
    lea     used_sat_slots, %a1
    move.w  %d0, %d1
    lsr.w   #3, %d1
    bset    %d0, 0(%a1,%d1.w)
    move.w  #1, pc090oj_sat_dirty
    rts

/* Set slot d0's SAT link field (word1 low 7 bits) to target slot d1. */
.Lpc090oj_set_link:
    movem.l %d0-%d1/%a1, -(%sp)
    lsl.w   #3, %d0
    lea     staged_sprite_sat, %a1
    adda.w  %d0, %a1
    andi.w  #0x007F, %d1
    ori.w   #0x0500, %d1
    move.w  %d1, 2(%a1)
    movem.l (%sp)+, %d0-%d1/%a1
    rts

/* Synchronize one record from the completed mirror (§9-E.3).  d6 = record.
 * Reads the mirror, updates LUT / bitmaps / SAT links+fields / worklist; never
 * writes the mirror, never sets a candidate.  Preserves d6.
 */
.Lpc090oj_sync_record_from_mirror:
    movem.l %d0-%d7/%a0-%a1, -(%sp)
    tst.w   pc090oj_scan_active
    bne.s   .Lsync_inited
    bsr     .Lpc090oj_renderer_init
.Lsync_inited:
    move.w  %d6, .Lscratch_rec
    bsr     .Lpc090oj_decode_record
    move.w  %d0, .Lscratch_draw
    move.w  .Lscratch_rec, %d6
    move.w  %d6, %d1
    lsr.w   #3, %d1
    lea     represented_records, %a1
    btst    %d6, 0(%a1,%d1.w)
    bne     .Lsync_was_rep
    /* currently NOT represented */
    tst.w   .Lscratch_draw
    beq     .Lsync_notrep_notdraw
    bsr     .Lpc090oj_activate_record
    bra     .Lsync_done
.Lsync_notrep_notdraw:
    move.w  .Lscratch_rec, %d0
    lea     waiting_records, %a1
    move.w  %d0, %d1
    lsr.w   #3, %d1
    bclr    %d0, 0(%a1,%d1.w)
    bra     .Lsync_done
.Lsync_was_rep:
    tst.w   .Lscratch_draw
    beq     .Lsync_deactivate
    bsr     .Lpc090oj_field_update_record
    bra     .Lsync_done
.Lsync_deactivate:
    bsr     .Lpc090oj_deactivate_record
.Lsync_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a1
    rts

/* Field update: record already represented and still drawable.  Keep slot and
 * link, re-patch fields + tile index, queue pattern DMA on code change. */
.Lpc090oj_field_update_record:
    move.w  .Lscratch_rec, %d6
    lea     record_to_slot, %a1
    moveq   #0, %d0
    move.b  0(%a1,%d6.w), %d0
    move.w  %d0, .Lscratch_slot
    lsl.w   #3, %d0
    lea     staged_sprite_sat, %a1
    adda.w  %d0, %a1
    move.w  2(%a1), %d0
    andi.w  #0x007F, %d0
    move.w  %d0, .Lscratch_link
    bsr     .Lpc090oj_place_record_in_slot
    rts

/* Activate (insert) a newly drawable record at its ascending-index position. */
.Lpc090oj_activate_record:
    move.w  pc090oj_represented_count, %d0
    cmpi.w  #80, %d0
    blo     .Lact_room
    move.w  #255, %d0
    bsr     .Lrep_last_le               /* d0 = tail record */
    move.w  %d0, %d1
    move.w  .Lscratch_rec, %d0
    cmp.w   %d1, %d0
    bhs     .Lact_to_waiting            /* rec >= tail -> overflow to waiting */
    bsr     .Lpc090oj_evict_tail
.Lact_room:
    moveq   #0, %d0
    bsr     .Lrep_first_ge              /* d0 = head or 256 */
    cmpi.w  #256, %d0
    beq     .Lact_first
    move.w  %d0, %d1
    move.w  .Lscratch_rec, %d0
    cmp.w   %d1, %d0
    blo     .Lact_new_head
    bra     .Lact_ordinary
.Lact_first:
    clr.w   .Lscratch_slot
    clr.w   .Lscratch_link
    move.w  .Lscratch_rec, %d6
    bsr     .Lpc090oj_place_record_in_slot
    addq.w  #1, pc090oj_represented_count
    rts
.Lact_new_head:
    move.w  %d1, .Lscratch_b            /* old head record */
    bsr     .Lused_lowest_free_nonzero  /* d0 = s_H */
    move.w  %d0, .Lscratch_a
    move.w  staged_sprite_sat+2, %d0    /* old head link (slot 0) */
    andi.w  #0x007F, %d0
    move.w  %d0, .Lscratch_link
    move.w  .Lscratch_a, %d0
    move.w  %d0, .Lscratch_slot
    move.w  .Lscratch_b, %d6
    bsr     .Lpc090oj_place_record_in_slot   /* old head -> s_H (keep link) */
    clr.w   .Lscratch_slot
    move.w  .Lscratch_a, %d0
    move.w  %d0, .Lscratch_link
    move.w  .Lscratch_rec, %d6
    bsr     .Lpc090oj_place_record_in_slot   /* new head -> slot 0, link=s_H */
    addq.w  #1, pc090oj_represented_count
    rts
.Lact_ordinary:
    move.w  .Lscratch_rec, %d0
    subq.w  #1, %d0
    bsr     .Lrep_last_le               /* d0 = prev record */
    move.w  %d0, .Lscratch_b
    move.w  .Lscratch_rec, %d0
    addq.w  #1, %d0
    bsr     .Lrep_first_ge              /* d0 = next record or 256 */
    cmpi.w  #256, %d0
    beq.s   .Lact_ord_nonext
    lea     record_to_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d0.w), %d1
    move.w  %d1, .Lscratch_link
    bra.s   .Lact_ord_slot
.Lact_ord_nonext:
    clr.w   .Lscratch_link
.Lact_ord_slot:
    bsr     .Lused_lowest_free_nonzero  /* d0 = s_R */
    move.w  %d0, .Lscratch_slot
    move.w  .Lscratch_rec, %d6
    bsr     .Lpc090oj_place_record_in_slot
    move.w  .Lscratch_b, %d0            /* prev record */
    lea     record_to_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d0.w), %d1
    move.w  %d1, %d0                    /* prevslot */
    move.w  .Lscratch_slot, %d1        /* target = s_R */
    bsr     .Lpc090oj_set_link
    addq.w  #1, pc090oj_represented_count
    rts
.Lact_to_waiting:
    move.w  .Lscratch_rec, %d0
    lea     waiting_records, %a1
    move.w  %d0, %d1
    lsr.w   #3, %d1
    bset    %d0, 0(%a1,%d1.w)
    rts

/* Evict the tail (lowest-priority) record into waiting; frees a slot, count--. */
.Lpc090oj_evict_tail:
    move.w  #255, %d0
    bsr     .Lrep_last_le               /* d0 = tail */
    move.w  %d0, .Lscratch_a
    subq.w  #1, %d0
    bsr     .Lrep_last_le               /* d0 = prev (exists; count>=2) */
    lea     record_to_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d0.w), %d1          /* prevslot */
    move.w  %d1, %d0
    moveq   #0, %d1                     /* link 0 -> terminator */
    bsr     .Lpc090oj_set_link
    move.w  .Lscratch_a, %d6           /* tail record */
    lea     record_to_slot, %a1
    moveq   #0, %d0
    move.b  0(%a1,%d6.w), %d0          /* tailslot */
    bsr     .Lpc090oj_free_slot
    lea     represented_records, %a1
    move.w  %d6, %d1
    lsr.w   #3, %d1
    bclr    %d6, 0(%a1,%d1.w)
    lea     record_to_slot, %a1
    move.b  #0xFF, 0(%a1,%d6.w)
    lea     waiting_records, %a1
    move.w  %d6, %d1
    lsr.w   #3, %d1
    bset    %d6, 0(%a1,%d1.w)
    subq.w  #1, pc090oj_represented_count
    rts

/* Deactivate a represented record that is no longer drawable. */
.Lpc090oj_deactivate_record:
    moveq   #0, %d0
    bsr     .Lrep_first_ge              /* d0 = head */
    move.w  .Lscratch_rec, %d1
    cmp.w   %d1, %d0
    beq     .Ldeact_head
    /* ORDINARY delete */
    move.w  %d1, %d0
    subq.w  #1, %d0
    bsr     .Lrep_last_le               /* d0 = prev */
    move.w  %d0, .Lscratch_b
    move.w  .Lscratch_rec, %d0
    addq.w  #1, %d0
    bsr     .Lrep_first_ge              /* d0 = next or 256 */
    cmpi.w  #256, %d0
    beq.s   .Ldeact_ord_term
    lea     record_to_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d0.w), %d1
    move.w  %d1, .Lscratch_a           /* nextslot */
    bra.s   .Ldeact_ord_link
.Ldeact_ord_term:
    clr.w   .Lscratch_a
.Ldeact_ord_link:
    move.w  .Lscratch_b, %d0
    lea     record_to_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d0.w), %d1
    move.w  %d1, %d0                    /* prevslot */
    move.w  .Lscratch_a, %d1           /* -> nextslot / 0 */
    bsr     .Lpc090oj_set_link
    move.w  .Lscratch_rec, %d6
    lea     record_to_slot, %a1
    moveq   #0, %d0
    move.b  0(%a1,%d6.w), %d0
    bsr     .Lpc090oj_free_slot
    bra     .Ldeact_finish
.Ldeact_head:
    move.w  .Lscratch_rec, %d0
    addq.w  #1, %d0
    bsr     .Lrep_first_ge              /* d0 = next or 256 */
    cmpi.w  #256, %d0
    beq     .Ldeact_head_empty
    move.w  %d0, .Lscratch_b           /* next record */
    lea     record_to_slot, %a1
    moveq   #0, %d1
    move.b  0(%a1,%d0.w), %d1
    move.w  %d1, .Lscratch_a           /* nslot */
    lsl.w   #3, %d1
    lea     staged_sprite_sat, %a1
    adda.w  %d1, %a1
    move.w  2(%a1), %d0
    andi.w  #0x007F, %d0
    move.w  %d0, .Lscratch_link        /* nlink */
    clr.w   .Lscratch_slot             /* promote next into slot 0 */
    move.w  .Lscratch_b, %d6
    bsr     .Lpc090oj_place_record_in_slot
    move.w  .Lscratch_a, %d0
    bsr     .Lpc090oj_free_slot        /* free next's old slot */
    bra     .Ldeact_finish
.Ldeact_head_empty:
    move.w  .Lscratch_rec, %d6
    lea     record_to_slot, %a1
    moveq   #0, %d0
    move.b  0(%a1,%d6.w), %d0
    bsr     .Lpc090oj_free_slot
    lea     represented_records, %a1
    move.w  %d6, %d1
    lsr.w   #3, %d1
    bclr    %d6, 0(%a1,%d1.w)
    lea     record_to_slot, %a1
    move.b  #0xFF, 0(%a1,%d6.w)
    subq.w  #1, pc090oj_represented_count
    bsr     .Lpc090oj_write_empty_slot0
    bsr     .Lpc090oj_promote_from_waiting
    rts
.Ldeact_finish:
    move.w  .Lscratch_rec, %d6
    lea     represented_records, %a1
    move.w  %d6, %d1
    lsr.w   #3, %d1
    bclr    %d6, 0(%a1,%d1.w)
    lea     record_to_slot, %a1
    move.b  #0xFF, 0(%a1,%d6.w)
    subq.w  #1, pc090oj_represented_count
    bsr     .Lpc090oj_promote_from_waiting
    rts

/* A freed slot promotes the highest-priority still-renderable waiting record. */
.Lpc090oj_promote_from_waiting:
    move.w  pc090oj_represented_count, %d0
    cmpi.w  #80, %d0
    bhs     .Lpromo_done
    moveq   #0, %d0
.Lpromo_scan:
    bsr     .Lwait_first_ge             /* d0 = first waiting >= d0 or 256 */
    cmpi.w  #256, %d0
    bhs     .Lpromo_done
    move.w  %d0, .Lscratch_a
    move.w  %d0, %d6
    bsr     .Lpc090oj_decode_record
    tst.w   %d0
    bne.s   .Lpromo_activate
    /* no longer renderable -> drop from waiting, keep scanning */
    move.w  .Lscratch_a, %d0
    lea     waiting_records, %a1
    move.w  %d0, %d1
    lsr.w   #3, %d1
    bclr    %d0, 0(%a1,%d1.w)
    move.w  .Lscratch_a, %d0
    addq.w  #1, %d0
    bra.s   .Lpromo_scan
.Lpromo_activate:
    move.w  .Lscratch_a, %d0
    lea     waiting_records, %a1
    move.w  %d0, %d1
    lsr.w   #3, %d1
    bclr    %d0, 0(%a1,%d1.w)
    move.w  .Lscratch_a, %d0
    move.w  %d0, .Lscratch_rec
    bsr     .Lpc090oj_activate_record
.Lpromo_done:
    rts

/*
 * Precomputed tile-DMA worklist commit.  Bounded by pc090oj_tile_dma_count,
 * skips canceled entries (code 0xFFFF), updates slot residency only after the
 * DMA, and resets the reservation map + count at the end of the interval.
 */
.Lvcs_tile_dma:
    move.w  pc090oj_tile_dma_count, %d7
    beq     .Lvcs_tile_reset
    moveq   #0, %d5
.Lvcs_tile_loop:
    move.w  %d5, %d0
    lsl.w   #2, %d0
    lea     pc090oj_tile_dma_worklist, %a0
    adda.w  %d0, %a0
    move.w  (%a0), %d4                  /* slot */
    move.w  2(%a0), %d6                /* code (0xFFFF = canceled) */
    cmpi.w  #0xFFFF, %d6
    beq     .Lvcs_tile_next

    move.w  %d6, %d0
    andi.w  #0x0FFF, %d0
    mulu.w  #128, %d0
    lea     rastan_pc090oj, %a1
    adda.l  %d0, %a1
    move.l  %a1, %d0
    lsr.l   #1, %d0
    movea.l #VDP_CTRL, %a3
    move.w  #0x9340, (%a3)
    move.w  #0x9400, (%a3)
    move.w  %d0, %d3
    andi.w  #0x00FF, %d3
    ori.w   #0x9500, %d3
    move.w  %d3, (%a3)
    move.l  %d0, %d3
    lsr.l   #8, %d3
    andi.w  #0x00FF, %d3
    ori.w   #0x9600, %d3
    move.w  %d3, (%a3)
    move.l  %d0, %d3
    lsr.l   #8, %d3
    lsr.l   #8, %d3
    andi.w  #0x007F, %d3
    ori.w   #0x9700, %d3
    move.w  %d3, (%a3)
    move.w  %d4, %d0
    lsl.w   #2, %d0
    addi.w  #SPRITE_TILE_BASE, %d0
    lsl.l   #5, %d0
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.l  #0x00000003, %d2
    ori.l   #0x40000080, %d1
    or.l    %d2, %d1
    move.l  %d1, (%a3)
    move.w  %d4, %d0
    add.w   %d0, %d0
    lea     sprite_tile_resident_code, %a1
    move.w  %d6, 0(%a1,%d0.w)
.Lvcs_tile_next:
    addq.w  #1, %d5
    cmp.w   %d7, %d5
    blo     .Lvcs_tile_loop
.Lvcs_tile_reset:
    /* Reset only the slots actually reserved this interval (d7 = count, still
     * live), so a stable no-work frame (count 0) does zero reset work. */
    tst.w   %d7
    beq.s   .Lvcs_tile_reset_done
    moveq   #0, %d5
.Lvcs_tile_reset_loop:
    move.w  %d5, %d0
    lsl.w   #2, %d0
    lea     pc090oj_tile_dma_worklist, %a0
    adda.w  %d0, %a0
    moveq   #0, %d0
    move.w  (%a0), %d0                  /* reserved slot for this entry */
    lea     worklist_entry_for_slot, %a1
    move.b  #0xFF, 0(%a1,%d0.w)
    addq.w  #1, %d5
    cmp.w   %d7, %d5
    blo.s   .Lvcs_tile_reset_loop
.Lvcs_tile_reset_done:
    clr.w   pc090oj_tile_dma_count
    rts

/* SAT DMA: length = max(highest_used+1, 1) * 4 words, clamped to 80 slots. */
.Lvcs_sat_dma:
    movea.l #VDP_CTRL, %a3
    bsr     .Lused_highest
    cmpi.w  #0xFFFF, %d0
    bne.s   .Lsat_have
    moveq   #1, %d0
    bra.s   .Lsat_clamp
.Lsat_have:
    addq.w  #1, %d0
.Lsat_clamp:
    cmpi.w  #80, %d0
    bls.s   .Lsat_len
    move.w  #80, %d0
.Lsat_len:
    lsl.w   #2, %d0

    move.w  %d0, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9300, %d1
    move.w  %d1, (%a3)

    move.w  %d0, %d1
    lsr.w   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9400, %d1
    move.w  %d1, (%a3)

    move.l  #staged_sprite_sat, %d0
    lsr.l   #1, %d0

    move.w  %d0, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9500, %d1
    move.w  %d1, (%a3)

    move.l  %d0, %d1
    lsr.l   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9600, %d1
    move.w  %d1, (%a3)

    move.l  %d0, %d1
    lsr.l   #8, %d1
    lsr.l   #8, %d1
    andi.w  #0x007F, %d1
    ori.w   #0x9700, %d1
    move.w  %d1, (%a3)

    move.l  #0x0000F800, %d0
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.l  #0x00000003, %d2
    ori.l   #0x40000080, %d1
    or.l    %d2, %d1
    move.l  %d1, (%a3)
    rts

/* ------------------------------------------------------------------------- */
/* VRAM DMA self-test                                                        */
/* ------------------------------------------------------------------------- */

genesistan_pc090oj_dma_self_test:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* Stack buffer (128 bytes) */
    lea     -128(%sp), %sp
    movea.l %sp, %a6

    /* DMA source: rastan_pc090oj + 0x80, len 64 words, dest VRAM 0x8000 */
    lea     rastan_pc090oj+0x80, %a1
    move.l  %a1, %d0
    lsr.l   #1, %d0

    movea.l #VDP_CTRL, %a3
    move.w  #0x9340, (%a3)
    move.w  #0x9400, (%a3)

    move.w  %d0, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9500, %d1
    move.w  %d1, (%a3)

    move.l  %d0, %d1
    lsr.l   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9600, %d1
    move.w  %d1, (%a3)

    move.l  %d0, %d1
    lsr.l   #8, %d1
    lsr.l   #8, %d1
    andi.w  #0x007F, %d1
    ori.w   #0x9700, %d1
    move.w  %d1, (%a3)

    move.l  #0x00008000, %d0
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.l  #0x00000003, %d2
    ori.l   #0x40000080, %d1
    or.l    %d2, %d1
    move.l  %d1, (%a3)

    /* Read back VRAM 0x8000..0x807F into stack buffer */
    move.l  #0x00008000, %d0
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.l  #0x00000003, %d2
    or.l    %d2, %d1                 /* VRAM read command (no write/dma bits) */
    move.l  %d1, (%a3)

    movea.l #VDP_DATA, %a4
    move.w  #(64 - 1), %d0
.Lpc090oj_dma_read_loop:
    move.w  (%a4), (%a6)+
    dbra    %d0, .Lpc090oj_dma_read_loop

    /* Compare 64 words */
    lea     rastan_pc090oj+0x80, %a0
    movea.l %sp, %a1
    moveq   #0, %d6
    move.w  #(64 - 1), %d0
.Lpc090oj_dma_cmp_loop:
    move.w  (%a0)+, %d1
    move.w  (%a1)+, %d2
    cmp.w   %d1, %d2
    bne.s   .Lpc090oj_dma_fail
    addq.w  #1, %d6
    dbra    %d0, .Lpc090oj_dma_cmp_loop

    lea     128(%sp), %sp
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lpc090oj_dma_fail:
    move.w  %d6, pc090oj_dma_test_mismatch_offset
    move.w  %d1, pc090oj_dma_test_expected_word
    move.w  %d2, pc090oj_dma_test_actual_word

    /* copy full 128-byte snapshot */
    movea.l %sp, %a0
    lea     pc090oj_dma_test_actual_buffer, %a1
    move.w  #(128/2 - 1), %d0
.Lpc090oj_dma_copy_buf:
    move.w  (%a0)+, (%a1)+
    dbra    %d0, .Lpc090oj_dma_copy_buf

    move.w  #0x6F0E, pc090oj_dma_test_fired_flag

.Lpc090oj_dma_test_halt:
    move.b  pc090oj_dma_test_heartbeat, %d0
    addq.b  #1, %d0
    move.b  %d0, pc090oj_dma_test_heartbeat
    bra     .Lpc090oj_dma_test_halt

/* ------------------------------------------------------------------------- */
/* BSS                                                                        */
/* ------------------------------------------------------------------------- */

    .section .bss
    .align 2

staged_sprite_sat:
    .space (80 * 8)
staged_sprite_descriptor_table:
    .space (80 * 12)
staged_sprite_dirty:
    .long 0
staged_sprite_active_count:
    .word 0
/* Per-SAT-slot VRAM tile residency cache; 0 means cold/no resident tile. */
sprite_tile_resident_code:
    .space (80 * 2)
/* Precomputed pending tile-DMA worklist: 80 x {word slot, word code}. */
pc090oj_tile_dma_worklist:
    .space (80 * 4)
pc090oj_tile_dma_count:
    .word 0
pc090oj_object_ram:
    .space 0x800
/* 256-bit derived candidate mask; one bit per PC090OJ source record. */
pc090oj_candidate_bitset:
    .space 32
pc090oj_ctrl_shadow:
    .word 0
pc090oj_sprite_ctrl_shadow:
    .word 0
pc090oj_mirror_dirty:
    .word 0
pc090oj_candidate_count:
    .word 0
pc090oj_decoded_count:
    .word 0
pc090oj_code_zero_skipped_count:
    .word 0
pc090oj_blank_skipped_count:
    .word 0
pc090oj_unmapped_skipped_count:
    .word 0
pc090oj_offscreen_skipped_count:
    .word 0
pc090oj_drawable_count:
    .word 0
pc090oj_emitted_count:
    .word 0
pc090oj_dropped_count:
    .word 0
pc090oj_scan_colbank:
    .word 0
pc090oj_scan_active:
    .word 0
pc090oj_producer_oob_count:
    .word 0
pc090oj_producer_write_count:
    .word 0

    /* Build 0142 retained-identity translation state. */
    .align 2
record_to_slot:
    .space 256                  /* record -> SAT slot; 0xFF = unrepresented */
represented_records:
    .space 32                   /* 256-bit: record currently owns a SAT slot */
waiting_records:
    .space 32                   /* 256-bit: eligible but overflowed (>80) */
used_sat_slots:
    .space 16                   /* 80-bit slot occupancy (10 used, padded) */
worklist_entry_for_slot:
    .space 80                   /* reserved worklist index per slot; 0xFF none */
pc090oj_represented_count:
    .word 0
pc090oj_sat_dirty:
    .word 0
pc090oj_bootstrap_pending:
    .word 0
.Lscratch_rec:
    .word 0
.Lscratch_slot:
    .word 0
.Lscratch_link:
    .word 0
.Lscratch_draw:
    .word 0
.Lscratch_a:
    .word 0
.Lscratch_b:
    .word 0

    .align 2
audit_guard_caller_pc:
    .long 0
audit_guard_register_snapshot:
    .space (15 * 4)
audit_guard_fired_flag:
    .word 0
audit_guard_vcount:
    .word 0
audit_guard_heartbeat:
    .byte 0

    .section .bss.patcher
    .balign 2
pc090oj_dma_test_fired_flag:
    .word 0
pc090oj_dma_test_mismatch_offset:
    .word 0
pc090oj_dma_test_expected_word:
    .word 0
pc090oj_dma_test_actual_word:
    .word 0
pc090oj_dma_test_actual_buffer:
    .space 128
pc090oj_dma_test_heartbeat:
    .byte 0
