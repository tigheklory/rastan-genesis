    .include "pc090oj_config.inc"

    .section .text,"ax"

    .global vdp_boot_setup
    .global vdp_set_reg
    .global vdp_set_vram_write_addr
    .extern vdp_dma_words_to_vram          /* Build 0345: DMA primitive now lives in dma.s */
    .global sprite_dma_addr_high_bits_fix
    .global vdp_commit_tiles_if_dirty
    .global vdp_commit_bg_strips_if_dirty
    .extern genesistan_pc080sn_tile_rom
    .extern vdp_commit_fg_narrow_strips
    .global vdp_commit_fg_strips_if_dirty
    .extern vdp_prepare_sprites
    .extern vdp_commit_sprites_vram
    .extern genesistan_current_scene_id
    .extern vdp_commit_palette             /* Build 0345: CRAM palette DMA now lives in dma.s */
    .global vdp_install_test_lines
    .extern editor_layera_palette
    .extern test_sprite_line0
    .extern test_sprite_line1
    .global vdp_commit_scroll
    .extern dma_publish_frame
    .global _vblank_service

    .global tiles_dirty
    .global palette_pending
    .global bg_row_dirty
    .global fg_row_dirty
    .global fg_native_gameplay_owner
    .global staged_dest_ptr_bg
    .global staged_dest_ptr_fg
    .global staged_scroll_x_bg
    .global staged_scroll_x_fg
    .global staged_scroll_y_bg
    .global staged_scroll_y_fg
    .global staged_bg_buffer
    .global staged_fg_buffer
    .global fg_narrow_desc_table
    .global fg_narrow_desc_count
    .global fg_narrow_pending_rows
    .global staged_palette_words
    .global staged_tile_words

    .equ VDP_DATA,              0x00C00000
    .equ VDP_CTRL,              0x00C00004

    .equ VDP_REG_MODE1,         0
    .equ VDP_REG_MODE2,         1
    .equ VDP_REG_PLANE_A,       2
    .equ VDP_REG_WINDOW,        3
    .equ VDP_REG_PLANE_B,       4
    .equ VDP_REG_SAT,           5
    .equ VDP_REG_BG_COLOR,      7
    .equ VDP_REG_HINT,          10
    .equ VDP_REG_MODE3,         11
    .equ VDP_REG_MODE4,         12
    .equ VDP_REG_HSCROLL,       13
    .equ VDP_REG_AUTOINC,       15
    .equ VDP_REG_PLANESIZE,     16
    .equ VDP_REG_WINDOW_X,      17
    .equ VDP_REG_WINDOW_Y,      18

    .equ VRAM_PLANE_B_BASE,     0x0000C000
    .equ VRAM_PLANE_A_BASE,     0x0000E000
    .equ VRAM_HSCROLL_BASE,     0x0000FC00
    .equ VRAM_TILE_BASE,        0x00000020
    .equ FG_NARROW_DESC_CAP,    64

    .equ ARCADE_FIX_DEST_BG,    0x00FF10A0
    .equ ARCADE_FIX_DEST_FG,    0x00FF10A4

    .equ VDP_MODE2_DISPLAY_OFF, 0x34
    .equ VDP_MODE2_DISPLAY_ON,  0x74
    .equ VDP_DISPLAY_ORIGIN_X_BIAS, 16
    .equ VDP_DISPLAY_ORIGIN_Y_BIAS, 8

    .include "src/crash_handler.s"
    .section .text,"ax"
vdp_boot_setup:
    moveq   #VDP_REG_MODE1, %d0
    moveq   #0x04, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_PLANE_A, %d0
    moveq   #0x38, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_WINDOW, %d0
    moveq   #0x3C, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_PLANE_B, %d0
    moveq   #0x06, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_SAT, %d0
    moveq   #0x7C, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_BG_COLOR, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_HINT, %d0
    move.w  #0x00FF, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_MODE3, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_MODE4, %d0
    move.w  #0x0081, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_HSCROLL, %d0
    moveq   #0x3F, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_AUTOINC, %d0
    moveq   #0x02, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_PLANESIZE, %d0
    moveq   #0x01, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_WINDOW_X, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_WINDOW_Y, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    rts

vdp_set_reg:
    move.w  %d0, %d2
    lsl.w   #8, %d2
    or.w    %d1, %d2
    ori.w   #0x8000, %d2
    move.w  %d2, VDP_CTRL
    rts

vdp_set_vram_write_addr:
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1

    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.l  #0x00000003, %d2

    ori.l   #0x40000000, %d1
    or.l    %d2, %d1
    move.l  %d1, VDP_CTRL
    rts

sprite_dma_addr_high_bits_fix:
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.w  #0x0003, %d2
    rts


_vblank_service:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     rastan_direct_update_inputs

    /* Build 0343: producer GUARD (no DMA).  Ensure the SAT is staged before the publication phase
     * (cheap no-op in gameplay when the arcade sprite dispatcher already emitted).  This is the only
     * production that runs inside the VBlank service; it does not touch the VDP. */
    bsr     vdp_prepare_sprites

.if RASTAN_DIAG_CPU_BAR
    /* Build 0337 diagnostic CPU-load bar ON: set the VDP backdrop (CRAM entry 0) bright, bracketing the
     * single publication phase below.  The coloured band = the VBlank publication cost; if it reaches
     * into the active picture the publication overran vblank. */
    move.l  #0xC0000000, VDP_CTRL       /* CRAM write addr 0 */
    move.w  #0x00E0, VDP_DATA           /* bright green = publishing */
.endif

    /* Build 0343: THE single Genesis VBlank publication phase (dma.s).  All normal-runtime DMA/VDP
     * publication for the completed frame happens here, in one contiguous phase at the top of the
     * VBlank service.  After this returns, NO further runtime DMA occurs before the arcade tick
     * resumes to stage the next frame. */
    bsr     dma_publish_frame

.if RASTAN_DIAG_CPU_BAR
    /* Build 0337 diagnostic CPU-load bar OFF: restore backdrop to black. */
    move.l  #0xC0000000, VDP_CTRL
    move.w  #0x0000, VDP_DATA           /* black = publication done */
.endif

.if RASTAN_DIAG_SCORE_METRIC
    /* Build 0338 diagnostic numeric metric: read the VDP V-counter at the end of the Genesis VBlank
     * servicing.  V >= 0xE0 -> still in vblank -> overran 0 active scanlines; V < 0xE0 -> servicing
     * bled into active display line V -> overran V scanlines.  Keep the running MAX (self-init: a
     * value > 223 is impossible/garbage -> reset), convert to 3-digit BCD, and write it as the P1
     * score (0xFF011E) so the 1UP HUD shows a stable readable NUMBER.  Diagnostic build only. */
    move.w  0x00C00008, %d0            /* VDP HV counter: high byte = V */
    lsr.w   #8, %d0
    andi.w  #0x00FF, %d0
    cmpi.w  #0x00E0, %d0
    blo.s   .Lsm_active                /* V < 0xE0 -> active line V -> overran */
    moveq   #0, %d0                    /* V >= 0xE0 -> finished in vblank -> 0 */
.Lsm_active:
    move.w  diag_servicing_peak, %d1
    cmpi.w  #223, %d1
    bls.s   .Lsm_peak_valid
    moveq   #0, %d1                    /* garbage/init guard */
.Lsm_peak_valid:
    cmp.w   %d1, %d0
    bls.s   .Lsm_store_peak
    move.w  %d0, %d1                   /* new worst-case max */
.Lsm_store_peak:
    move.w  %d1, diag_servicing_peak
    andi.l  #0x0000FFFF, %d1           /* 0..223 -> 3-digit BCD */
    divu.w  #100, %d1                  /* d1.lo=hundreds, d1.hi=rem */
    move.w  %d1, %d2                   /* d2.lo = hundreds */
    clr.w   %d1
    swap    %d1                        /* d1 = rem (0..99) */
    divu.w  #10, %d1                   /* d1.lo=tens, d1.hi=ones */
    move.w  %d1, %d0                   /* d0.lo = tens */
    swap    %d1                        /* d1.lo = ones */
    andi.w  #0x000F, %d2
    andi.w  #0x000F, %d0
    andi.w  #0x000F, %d1
    lsl.w   #4, %d0
    or.w    %d1, %d0                   /* d0 = tens<<4 | ones */
    /* Publish 3-byte BCD into diag_score_bcd.  The P1 HUD emitter (pc090oj_hooks) copies it into the
     * live score (0xFF011E) at the exact moment it renders, so it wins over the arcade score update
     * (writing 0xFF011E here directly gets clobbered by the arcade handler before the HUD reads it). */
    lea     diag_score_bcd, %a0
    move.b  #0, (%a0)+                 /* digits 5-6 = 00 */
    move.b  %d2, (%a0)+                /* digits 3-4 = 0 hundreds */
    move.b  %d0, (%a0)                 /* digits 1-2 = tens ones */
.endif

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    jmp     (0x00003A208).l

vdp_commit_tiles_if_dirty:
    tst.b   tiles_dirty
    beq.s   .Ltiles_done

    move.l  #VRAM_TILE_BASE, %d0
    bsr     vdp_set_vram_write_addr

    lea     staged_tile_words, %a0
    move.w  #(48 - 1), %d7
.Ltile_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Ltile_copy

    clr.b   tiles_dirty
.Ltiles_done:
    rts

/* Build 0256: the dead PC080SN tall-projector stubs vdp_project_bg_tall_if_dirty
 * / vdp_project_fg_tall_if_dirty (no-op RTS since Build 0253, zero readers of
 * their tall-project-base globals) and their _vblank_service call sites were
 * retired.  Native Plane A/B producers + strip commits own tilemap output. */

/* Build 0345: the VRAM row DMA primitive (vdp_dma_words_to_vram/.Lplane_dma_row) was relocated
 * to dma.s so DMA-register programming has a single owner.  The strip commits below now call the
 * dma.s-owned `vdp_dma_words_to_vram` (same in: d0 VRAM byte dest, d1 word count, a0 source;
 * clobbers d1-d3, a1). */

vdp_commit_bg_strips_if_dirty:
    move.l  bg_row_dirty, %d6
    beq.s   .Lbg_done

    moveq   #0, %d5
.Lbg_row_scan:
    btst    %d5, %d6
    beq.s   .Lbg_next_row

    moveq   #0, %d4
    move.w  %d5, %d4
    lsl.l   #7, %d4

    move.l  #VRAM_PLANE_B_BASE, %d0
    add.l   %d4, %d0

    lea     staged_bg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #64, %d1
    bsr     vdp_dma_words_to_vram

    move.l  %d6, %d0
    bclr    %d5, %d0
    move.l  %d0, %d6
    move.l  %d6, bg_row_dirty
    beq.s   .Lbg_done

.Lbg_next_row:
    addq.w  #1, %d5
    cmpi.w  #32, %d5
    blo.s   .Lbg_row_scan
.Lbg_done:
    rts

vdp_commit_fg_strips_if_dirty:
    move.l  fg_row_dirty, %d6
    beq.s   .Lfg_done

    moveq   #0, %d5
.Lfg_row_scan:
    btst    %d5, %d6
    beq.s   .Lfg_next_row

    moveq   #0, %d4
    move.w  %d5, %d4
    lsl.l   #7, %d4

    move.l  #VRAM_PLANE_A_BASE, %d0
    add.l   %d4, %d0

    lea     staged_fg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #64, %d1
    bsr     vdp_dma_words_to_vram

    move.l  %d6, %d0
    bclr    %d5, %d0
    move.l  %d0, %d6
    move.l  %d6, fg_row_dirty
    beq.s   .Lfg_done

.Lfg_next_row:
    addq.w  #1, %d5
    cmpi.w  #32, %d5
    blo.s   .Lfg_row_scan
.Lfg_done:
    rts

/* Build 0345: vdp_commit_palette (the CRAM palette DMA) was relocated to dma.s so DMA-register
 * programming has a single owner.  It is invoked only from dma_publish_frame. */

vdp_commit_scroll:
    move.l  #VRAM_HSCROLL_BASE, %d0
    bsr     vdp_set_vram_write_addr

    move.w  staged_scroll_x_fg, %d0
    subi.w  #VDP_DISPLAY_ORIGIN_X_BIAS, %d0
    move.w  %d0, VDP_DATA
    move.w  staged_scroll_x_bg, %d0
    subi.w  #VDP_DISPLAY_ORIGIN_X_BIAS, %d0
    move.w  %d0, VDP_DATA

    move.l  #0x40000010, VDP_CTRL
    move.w  staged_scroll_y_fg, %d0
    neg.w   %d0
    addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lscroll_fg_y_ready
    /* Native gameplay Plane A producers place resident logical rows at
     * logical_row&31, so VSRAM must carry the full YM7101 9-bit vertical scroll
     * rather than the old projector-era 8-pixel phase. */
    andi.w  #0x01FF, %d0
.Lscroll_fg_y_ready:
    move.w  %d0, VDP_DATA
    move.w  staged_scroll_y_bg, %d0
    neg.w   %d0
    addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lscroll_bg_y_ready
    /* Native gameplay Plane B now uses the same logical_row&31 resident window
     * contract as Plane A, so it needs the same full 9-bit vertical scroll. */
    andi.w  #0x01FF, %d0
.Lscroll_bg_y_ready:
    move.w  %d0, VDP_DATA
    rts

/* Build 0329/0336: ONE-SHOT R1/P1 Test-palette installer (event-driven).  Called from
 * load_scene_tiles at the gameplay-scene activation event (genesistan_current_scene_id just set to
 * 1) - NOT every frame.  Installs the frozen-Test static R1/P1 palettes onto Genesis Lines 0/1/3.
 * Line 2 (Layer B) is never touched.  The arcade palette hooks are gated off Lines 0/1/3 during
 * scene 1 (palette_hooks.s), so the Test lines stay static until the next scene-activation event.
 * The unconditional VBlank CRAM DMA (Build 0336) publishes the staged buffer; no palette_dirty.
 * Offsets: staged_palette_words is 4 lines x 16 words; line N at +N*32 bytes. */
vdp_install_test_lines:
    movem.l %d2/%a0-%a1, -(%sp)
    lea     staged_palette_words, %a1          /* Line 0 */
    lea     test_sprite_line0, %a0
    moveq   #(16 - 1), %d2
.Liti_l0:
    move.w  (%a0)+, (%a1)+
    dbra    %d2, .Liti_l0
    lea     staged_palette_words + 32, %a1     /* Line 1 */
    lea     test_sprite_line1, %a0
    moveq   #(16 - 1), %d2
.Liti_l1:
    move.w  (%a0)+, (%a1)+
    dbra    %d2, .Liti_l1
    lea     staged_palette_words + 96, %a1     /* Line 3 */
    lea     editor_layera_palette, %a0
    moveq   #(16 - 1), %d2
.Liti_l3:
    move.w  (%a0)+, (%a1)+
    dbra    %d2, .Liti_l3
    move.b  #1, palette_pending
    movem.l (%sp)+, %d2/%a0-%a1
    rts

/* Build 0336: the dead PC080SN/PC090OJ palette carrier re-asserts (vdp_reassert_fg_bank3_line,
 * vdp_reassert_bank36_line0) were removed.  They had no callers since Build 0325 and existed only
 * to repair CRAM after the old dirty-gated PIO commit; the unconditional VBlank CRAM DMA + the
 * event-driven producers make them obsolete.  Their carrier caches were removed with them. */

    .section .bss
    .align 2

/* Build 0336: removed palette scaffolding BSS -- fg_bank3_line_cache, fg_bank3_cache_valid,
 * fg_bank3_route_seen, pc090oj_bank36_line0_cache, pc090oj_bank36_cache_valid (dead carrier caches)
 * and palette_dirty (publication is now an unconditional VBlank CRAM DMA). */
.if RASTAN_DIAG_SCORE_METRIC
    .align 2
diag_servicing_peak:                    /* Build 0338 diagnostic: peak servicing overrun scanlines */
    .word 0
    .global diag_score_bcd
diag_score_bcd:                         /* 3-byte BCD of the metric, copied into the P1 score by the HUD emit */
    .byte 0, 0, 0
    .align 2
.endif
tiles_dirty:
    .byte 0
palette_pending:
    .byte 0
    .align 2
bg_row_dirty:
    .long 0
fg_row_dirty:
    .long 0
fg_native_gameplay_owner:
    .byte 0

    .align 2
fg_narrow_desc_table:
    .space (FG_NARROW_DESC_CAP * 2)
fg_narrow_desc_count:
    .word 0
fg_narrow_pending_rows:
    .word 0

    .align 2
staged_dest_ptr_bg:
    .long 0
staged_dest_ptr_fg:
    .long 0

staged_scroll_x_bg:
    .word 0
staged_scroll_x_fg:
    .word 0
staged_scroll_y_bg:
    .word 0
staged_scroll_y_fg:
    .word 0

    .align 2
staged_bg_buffer:
    .space (2048 * 2)
staged_fg_buffer:
    .space (2048 * 2)
staged_palette_words:
    .space (64 * 2)
staged_tile_words:
    .space (48 * 2)
