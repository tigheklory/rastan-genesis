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

    .global vdp_commit_sprites
    .global genesistan_pc090oj_dma_self_test

    .global staged_sprite_sat
    .global staged_sprite_descriptor_table
    .global staged_sprite_dirty
    .global staged_sprite_active_count

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
    .extern genesistan_hook_tilemap_bg_fill
    .extern genesistan_hook_tilemap_fg_fill
    .extern genesistan_hook_pc080sn_bg_scroll_fill
    .extern genesistan_hook_pc080sn_fg_scroll_fill

    .equ VDP_DATA,      0x00C00000
    .equ VDP_CTRL,      0x00C00004
    .equ SPRITE_TILE_BASE, 1024
    .equ ARCADE_ROM_BASE, 0x00000200

/* ------------------------------------------------------------------------- */
/* Internal helpers                                                          */
/* ------------------------------------------------------------------------- */

/* d0=slot -> set dirty block bit (slot>>2) in staged_sprite_dirty */
.Lpc090oj_mark_dirty_slot:
    move.w  %d0, %d1
    lsr.w   #2, %d1
    moveq   #1, %d2
    lsl.l   %d1, %d2
    move.l  staged_sprite_dirty, %d3
    or.l    %d2, %d3
    move.l  %d3, staged_sprite_dirty
    rts

/* d0=slot,d1=word0,d2=y,d3=word2(tile),d4=x,d5=source_id,d6=ignored_input,d7=sprite_colbank
 * Clobbers: D1, D2, D3, D5, D6, A0, A1
 * Preserves: D0, D4, D7, A2..A6
 */
.Lpc090oj_emit_slot:
    /* descriptor ptr = staged_sprite_descriptor_table + slot*12 */
    move.w  %d0, %d6
    mulu.w  #12, %d6
    lea     staged_sprite_descriptor_table, %a0
    adda.l  %d6, %a0

    /* sat ptr = staged_sprite_sat + slot*8 */
    move.w  %d0, %d6
    lsl.w   #3, %d6
    lea     staged_sprite_sat, %a1
    adda.w  %d6, %a1

    move.w  8(%a0), %d6                /* old tile for changed-flag */

    /* persist semantic record */
    move.w  %d2, 2(%a0)
    move.w  %d4, 4(%a0)
    move.w  %d1, 6(%a0)
    move.w  %d3, 8(%a0)
    move.w  %d5, 10(%a0)

    /* invalid checks: y sentinel, all-zero tuple, tile zero */
    cmpi.w  #0x0180, %d2
    beq     .Lpc090oj_emit_invalid
    tst.w   %d3
    beq     .Lpc090oj_emit_invalid
    move.w  %d1, %d5
    or.w    %d2, %d5
    or.w    %d3, %d5
    or.w    %d4, %d5
    beq     .Lpc090oj_emit_invalid

    /* flags: valid + touched + extra; bit2 when tile changed */
    move.w  #0x8001, %d5
    or.w    %d6, %d5                    /* caller provided extra flags in d6 lower bits */
    cmp.w   8(%a0), %d6                 /* d6 currently old tile; refreshed below */
    /* old tile was clobbered by previous OR, reload */
    move.w  8(%a0), %d6
    cmp.w   %d3, %d6
    beq.s   .Lpc090oj_no_tile_change
    ori.w   #0x0004, %d5                /* tile-code-changed bit */
.Lpc090oj_no_tile_change:
    move.w  %d5, (%a0)

    /* SAT word0 (Y) */
    move.w  %d2, %d5
    andi.w  #0x01FF, %d5
    addi.w  #0x0080, %d5
    andi.w  #0x01FF, %d5
    move.w  %d5, (%a1)

    /* SAT word1 size/link deferred */
    move.w  #0x0500, 2(%a1)

    /* SAT word2 */
    move.w  #0x8000, %d5                /* priority */

    /* palette line */
    move.w  %d1, %d6
    andi.w  #0x000F, %d6
    or.w    %d7, %d6
    lsr.w   #4, %d6
    andi.w  #0x0003, %d6
    lsl.w   #8, %d6
    lsl.w   #5, %d6
    or.w    %d6, %d5

    /* flips */
    move.w  %d1, %d6
    andi.w  #0x8000, %d6
    lsr.w   #3, %d6
    or.w    %d6, %d5
    move.w  %d1, %d6
    andi.w  #0x4000, %d6
    lsr.w   #3, %d6
    or.w    %d6, %d5

    /* tile index from slot */
    move.w  %d0, %d6
    lsl.w   #2, %d6
    addi.w  #SPRITE_TILE_BASE, %d6
    andi.w  #0x07FF, %d6
    or.w    %d6, %d5

    move.w  %d5, 4(%a1)

    /* SAT word3 (X) */
    move.w  %d4, %d5
    andi.w  #0x01FF, %d5
    addi.w  #0x0080, %d5
    andi.w  #0x01FF, %d5
    move.w  %d5, 6(%a1)

    bsr     .Lpc090oj_mark_dirty_slot
    rts

.Lpc090oj_emit_invalid:
    move.w  #0x8000, (%a0)              /* touched, invalid */
    move.w  #0, (%a1)
    move.w  #0x0500, 2(%a1)
    move.w  #0, 4(%a1)
    move.w  #0, 6(%a1)
    bsr     .Lpc090oj_mark_dirty_slot
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

/* emit 22 slots from workram blocks at A5+0x11B2 (18) and A5+0x0170 (4) */
.Lpc090oj_emit_slots_0_21_from_workram:
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7

    lea     0x11B2(%a5), %a0
    moveq   #0, %d0
    moveq   #17, %d1
.Lpc090oj_block_a_loop:
    move.w  (%a0), %d2
    move.w  2(%a0), %d3
    move.w  4(%a0), %d4
    move.w  6(%a0), %d5
    move.w  %d2, %d1
    move.w  %d3, %d2
    move.w  %d4, %d3
    move.w  %d5, %d4
    moveq   #0, %d5
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    adda.w  #8, %a0
    addq.w  #1, %d0
    cmpi.w  #18, %d0
    blo.s   .Lpc090oj_block_a_loop

    lea     0x0170(%a5), %a0
    moveq   #18, %d0
.Lpc090oj_block_b_loop:
    move.w  (%a0), %d2
    move.w  2(%a0), %d3
    move.w  4(%a0), %d4
    move.w  6(%a0), %d5
    move.w  %d2, %d1
    move.w  %d3, %d2
    move.w  %d4, %d3
    move.w  %d5, %d4
    moveq   #0, %d5
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    adda.w  #8, %a0
    addq.w  #1, %d0
    cmpi.w  #22, %d0
    blo.s   .Lpc090oj_block_b_loop
    rts

/* ------------------------------------------------------------------------- */
/* 17 helpers                                                                */
/* ------------------------------------------------------------------------- */

genesistan_pc090oj_hook_target_3b902:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    tst.w   %d1
    bne.s   .Lhook_3b902_fill
    moveq   #0, %d0
.Lhook_3b902_clear_loop:
    bsr     .Lpc090oj_clear_slot
    addq.w  #1, %d0
    cmpi.w  #5, %d0
    blo.s   .Lhook_3b902_clear_loop
    bra.s   .Lhook_3b902_done
.Lhook_3b902_fill:
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
    moveq   #0, %d0
.Lhook_3b902_fill_loop:
    move.w  %d1, %d2
    moveq   #0, %d1
    moveq   #1, %d3
    moveq   #0, %d4
    moveq   #0, %d5
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    addq.w  #1, %d0
    cmpi.w  #5, %d0
    blo.s   .Lhook_3b902_fill_loop
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
    moveq   #14, %d0
    move.w  %d1, %d6
    cmpi.w  #4, %d6
    bls.s   .Lhook_3b930_count_ok
    moveq   #4, %d6
.Lhook_3b930_count_ok:
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
.Lhook_3b930_loop:
    tst.w   %d6
    beq.s   .Lhook_3b930_done
    moveq   #0, %d1
    moveq   #0, %d2
    move.b  (%a0)+, %d2
    moveq   #0, %d4
    move.b  (%a0)+, %d4
    move.w  (%a0)+, %d3
    moveq   #0, %d5
    move.w  %d6, -(%sp)              /* save loop counter */
    moveq   #0, %d6
    bsr     .Lpc090oj_emit_slot
    move.w  (%sp)+, %d6              /* restore loop counter */
    addq.w  #1, %d0
    subq.w  #1, %d6
    bra.s   .Lhook_3b930_loop
.Lhook_3b930_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_target_41dae:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lpc090oj_emit_slots_0_21_from_workram
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_target_41f5e:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lpc090oj_emit_slots_0_21_from_workram
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_pc090oj_hook_target_45dfa:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lpc090oj_emit_slots_0_21_from_workram
    movem.l (%sp)+, %d0-%d7/%a0-%a6
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

    /* PC090OJ branch: idx = (A0 - 0xD00000) >> 3 */
    move.l  %a0, %d2
    subi.l  #0x00D00000, %d2
    bmi     .Lhook_3ad44_finish
    lsr.l   #3, %d2
    cmpi.l  #255, %d2
    bhi     .Lhook_3ad44_finish

    lea     pc090oj_slot_lut, %a1
    move.b  0(%a1,%d2.l), %d0
    cmpi.b  #0xFF, %d0
    beq     .Lhook_3ad44_finish

    andi.w  #0x00FF, %d0
    move.w  %d1, %d3
.Lhook_3ad44_loop:
    tst.w   %d3
    beq.s   .Lhook_3ad44_finish
    cmpi.w  #80, %d0
    bhs.s   .Lhook_3ad44_finish
    bsr     .Lpc090oj_clear_slot
    addq.w  #1, %d0
    subq.w  #1, %d3
    bra.s   .Lhook_3ad44_loop

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
    movea.l #ARCADE_ROM_BASE+0x0003B87E, %a0
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
    /* Map arcade destination pointer progression to helper-owned slots 22..29 */
    move.l  %a4, %d3
    subi.l  #0x00D00000, %d3
    lsr.l   #3, %d3                   /* descriptor index */
    subi.w  #17, %d3
    bcs.s   .Lhook_3b802_next
    cmpi.w  #7, %d3
    bhi.s   .Lhook_3b802_next

    move.w  %d3, %d0
    addi.w  #22, %d0

    /* Preserve existing attr/x, update only word1 + tile as in original function */
    move.w  %d0, %d5
    mulu.w  #12, %d5
    lea     staged_sprite_descriptor_table, %a0
    adda.l  %d5, %a0
    move.w  6(%a0), %d5               /* attr word0 */
    move.w  4(%a0), %d4               /* x word3 */

    move.w  %d1, %d3                  /* tile word2 */
    move.w  %d5, %d1                  /* attr word0 */

    moveq   #0, %d5
    move.b  %d6, %d5
    andi.w  #0x00FF, %d5
    move.w  %d4, %d2                  /* vis flag from .Lhook_3b802_visflag */
    lsl.w   #8, %d2
    or.w    %d5, %d2                  /* word1 */

    moveq   #0, %d5                   /* source_id */
    moveq   #0, %d6                   /* extra flags */
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
    bsr     .Lpc090oj_emit_slot

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
/* VBlank sprite commit                                                      */
/* ------------------------------------------------------------------------- */

vdp_commit_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lvcs_link_chain_build
    bsr     .Lvcs_tile_dma
    bsr     .Lvcs_sat_dma
    bsr     .Lvcs_clear_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lvcs_link_chain_build:
    clr.w   staged_sprite_active_count
    moveq   #-1, %d6                 /* prev valid slot */
    moveq   #0, %d7                  /* slot */
.Lvcs_link_scan:
    cmpi.w  #80, %d7
    bhs.s   .Lvcs_link_done

    move.w  %d7, %d0
    mulu.w  #12, %d0
    lea     staged_sprite_descriptor_table, %a0
    adda.l  %d0, %a0
    btst    #0, (%a0)
    beq.s   .Lvcs_link_next

    /* if previous valid exists, set its link to current slot */
    cmpi.w  #-1, %d6
    beq.s   .Lvcs_no_prev

    move.w  %d6, %d0
    lsl.w   #3, %d0
    lea     staged_sprite_sat, %a1
    adda.w  %d0, %a1
    move.w  #0x0500, %d1
    move.w  %d7, %d0
    andi.w  #0x007F, %d0
    or.w    %d0, %d1
    move.w  %d1, 2(%a1)

.Lvcs_no_prev:
    move.w  %d7, %d6
    addq.w  #1, staged_sprite_active_count

.Lvcs_link_next:
    addq.w  #1, %d7
    bra.s   .Lvcs_link_scan

.Lvcs_link_done:
    cmpi.w  #-1, %d6
    beq.s   .Lvcs_link_end
    move.w  %d6, %d0
    lsl.w   #3, %d0
    lea     staged_sprite_sat, %a1
    adda.w  %d0, %a1
    move.w  #0x0500, 2(%a1)
.Lvcs_link_end:
    rts

.Lvcs_tile_dma:
    moveq   #0, %d7                  /* slot */
.Lvcs_tile_loop:
    cmpi.w  #80, %d7
    bhs     .Lvcs_tile_done

    move.w  %d7, %d0
    mulu.w  #12, %d0
    lea     staged_sprite_descriptor_table, %a0
    adda.l  %d0, %a0

    move.w  (%a0), %d1
    btst    #0, %d1                  /* valid */
    beq     .Lvcs_tile_next
    btst    #2, %d1                  /* tile-code-changed */
    beq     .Lvcs_tile_next

    move.w  8(%a0), %d2
    andi.w  #0x0FFF, %d2

    /* source = rastan_pc090oj + tile*128 */
    move.w  %d2, %d0
    mulu.w  #128, %d0
    lea     rastan_pc090oj, %a1
    adda.l  %d0, %a1

    /* DMA source address /2 */
    move.l  %a1, %d0
    lsr.l   #1, %d0

    movea.l #VDP_CTRL, %a3

    /* length 64 words */
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

    /* dest VRAM addr = (SPRITE_TILE_BASE + slot*4) * 32 */
    move.w  %d7, %d0
    lsl.w   #2, %d0
    addi.w  #SPRITE_TILE_BASE, %d0
    lsl.l   #5, %d0

    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1

    move.l  %d0, %d2
    lsr.l   #8, %d2                  /* Rule-23 inline */
    lsr.l   #6, %d2                  /* Rule-23 inline */
    andi.l  #0x00000003, %d2

    ori.l   #0x40000080, %d1
    or.l    %d2, %d1
    move.l  %d1, (%a3)

    /* clear tile-code-changed bit */
    andi.w  #0xFFFB, (%a0)

.Lvcs_tile_next:
    addq.w  #1, %d7
    bra     .Lvcs_tile_loop

.Lvcs_tile_done:
    rts

.Lvcs_sat_dma:
    movea.l #VDP_CTRL, %a3

    /* 640 bytes = 320 words */
    move.w  #0x9340, (%a3)
    move.w  #0x9401, (%a3)

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

.Lvcs_clear_dirty:
    clr.l   staged_sprite_dirty
    lea     staged_sprite_descriptor_table, %a0
    move.w  #(80 - 1), %d0
.Lvcs_clear_loop:
    move.w  (%a0), %d1
    andi.w  #0x7FFF, %d1             /* clear touched flag */
    move.w  %d1, (%a0)
    adda.w  #12, %a0
    dbra    %d0, .Lvcs_clear_loop
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
