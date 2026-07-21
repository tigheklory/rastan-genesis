    .include "pc090oj_config.inc"

    .section .text,"ax"

    .global vdp_boot_setup
    .global vdp_set_reg
    .global vdp_set_vram_write_addr
    .global sprite_dma_addr_high_bits_fix
    .global vdp_commit_tiles_if_dirty
    .global vdp_project_bg_tall_if_dirty
    .global vdp_project_fg_tall_if_dirty
    .global vdp_commit_bg_strips_if_dirty
    .extern vdp_commit_fg_narrow_strips
    .global vdp_commit_fg_strips_if_dirty
    .extern vdp_prepare_sprites
    .extern vdp_commit_sprites_vram
    .extern genesistan_current_scene_id
    .extern palette_route_lookup
    .global vdp_commit_palette
    .global vdp_reassert_fg_bank3_line
    .global vdp_commit_scroll
    .global bg_col_dirty
    .global fg_col_dirty
    .global bg_tall_project_base
    .global fg_tall_project_base
    .global _vblank_service
    .global fg_bank3_line_cache
    .global fg_bank3_cache_valid
    .global fg_bank3_route_seen
    .global pc090oj_bank36_line0_cache
    .global pc090oj_bank36_cache_valid

    .global palette_dirty
    .global tiles_dirty
    .global bg_row_dirty
    .global bg_tall_dirty
    .global bg_tall_project_base
    .global fg_row_dirty
    .global fg_tall_dirty
    .global fg_tall_project_base
    .global staged_dest_ptr_bg
    .global staged_dest_ptr_fg
    .global staged_scroll_x_bg
    .global staged_scroll_x_fg
    .global staged_scroll_y_bg
    .global staged_scroll_y_fg
    .global staged_bg_buffer
    .global staged_bg_tall_buffer
    .global staged_fg_buffer
    .global staged_fg_tall_buffer
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
    bsr     vdp_prepare_sprites

    /* N2: the display stays ON.  Plane updates are incremental (ring rows +
     * dirty columns) committed by bounded DMA; the display-off bracket that
     * produced the title and rolling black bars is deleted. */
    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_plane_service_bg
    bsr     vdp_plane_service_fg
    bsr     vdp_commit_fg_narrow_strips

    bsr     vdp_commit_sprites_vram     /* N1: DMA-only, display-on safe */

    bsr     vdp_reassert_fg_bank3_line
.if RASTAN_GAMEPLAY_HUD_SPRITES == 0
    bsr     vdp_reassert_bank36_line0
.endif
    tst.b   palette_dirty
    beq.s   .Lvs_skip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lvs_skip_palette:

    bsr     vdp_commit_scroll

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

/* ========================================================================= */
/* N2 native plane pipeline (Build 0224): vertical RING + incremental        */
/* projection + bounded display-on DMA.                                      */
/*                                                                           */
/* The 64-row tall buffers are the readable PC080SN C-window shadow (arcade  */
/* plane intent).  The Genesis 64x32 plane is a vertical ring of it:         */
/* plane_row = tall_row & 31, and VSRAM carries the FULL scroll value        */
/* (mod 256) instead of the old &7 residual + full-window reprojection.      */
/* Vertical scroll streams only the rows entering the window (128 B DMA per  */
/* row).  Horizontal streaming marks dirty COLUMNS (producer bitset); each   */
/* is projected through the ring, gathered, and committed as one 64 B DMA.   */
/* Scene entry forces a full 32-row projection streamed via row_dirty under  */
/* the same budget.  Frontend scenes run with base 0 (identity), so the      */
/* same paths serve them and the title glyph probes read the same shadow.    */
/* Register contract inside .Lplane_service: d0=base d7=VRAM base a0=tall    */
/* a1=staged a2=col_dirty a4=&project_base a6=&row_dirty are persistent.     */
/* ========================================================================= */
    .equ PLANE_ROWS_PER_FRAME, 16
    .equ PLANE_COLS_PER_FRAME, 24

/* Generic VRAM DMA.  in: d0=VRAM dest byte addr, d1=word count, d2=autoinc,
 * a0=68k source.  Restores autoinc 2.  Clobbers d1-d3, a3. */
.Lplane_dma:
    movea.l #VDP_CTRL, %a3
    move.w  %d2, %d3
    ori.w   #0x8F00, %d3
    move.w  %d3, (%a3)
    move.w  %d1, %d3
    andi.w  #0x00FF, %d3
    ori.w   #0x9300, %d3
    move.w  %d3, (%a3)
    move.w  %d1, %d3
    lsr.w   #8, %d3
    andi.w  #0x00FF, %d3
    ori.w   #0x9400, %d3
    move.w  %d3, (%a3)
    move.l  %a0, %d3
    lsr.l   #1, %d3
    move.w  %d3, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9500, %d1
    move.w  %d1, (%a3)
    move.l  %d3, %d1
    lsr.l   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9600, %d1
    move.w  %d1, (%a3)
    move.l  %d3, %d1
    lsr.l   #8, %d1
    lsr.l   #8, %d1
    andi.w  #0x007F, %d1
    ori.w   #0x9700, %d1
    move.w  %d1, (%a3)
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d3
    lsr.l   #8, %d3
    lsr.l   #6, %d3
    andi.l  #0x00000003, %d3
    ori.l   #0x40000080, %d1
    or.l    %d3, %d1
    move.l  %d1, (%a3)
    move.w  #0x8F02, (%a3)
    rts

/* Legacy mainline callers (item-page blit) forced an immediate FG strip
 * commit.  Under N2 the dirty bits they set are consumed by the next VBlank
 * plane service, so the entry survives as a no-op. */
vdp_commit_fg_strips_if_dirty:
    rts

vdp_plane_service_bg:
    movem.l %d0-%d7/%a0-%a4/%a6, -(%sp)
    moveq   #0, %d0
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lpsb_base_ok
    move.w  staged_scroll_y_bg, %d0
    neg.w   %d0
    addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
    andi.w  #0x01FF, %d0
    lsr.w   #3, %d0
    andi.w  #0x003F, %d0
.Lpsb_base_ok:
    lea     staged_bg_tall_buffer, %a0
    lea     staged_bg_buffer, %a1
    lea     bg_col_dirty, %a2
    lea     bg_tall_project_base, %a4
    lea     bg_row_dirty, %a6
    move.l  #VRAM_PLANE_B_BASE, %d7
    bsr     .Lplane_service
    movem.l (%sp)+, %d0-%d7/%a0-%a4/%a6
    rts

vdp_plane_service_fg:
    movem.l %d0-%d7/%a0-%a4/%a6, -(%sp)
    moveq   #0, %d0
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lpsf_base_ok
    move.w  staged_scroll_y_fg, %d0
    neg.w   %d0
    addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
    andi.w  #0x01FF, %d0
    lsr.w   #3, %d0
    andi.w  #0x003F, %d0
.Lpsf_base_ok:
    lea     staged_fg_tall_buffer, %a0
    lea     staged_fg_buffer, %a1
    lea     fg_col_dirty, %a2
    lea     fg_tall_project_base, %a4
    lea     fg_row_dirty, %a6
    move.l  #VRAM_PLANE_A_BASE, %d7
    bsr     .Lplane_service
    movem.l (%sp)+, %d0-%d7/%a0-%a4/%a6
    rts

.Lplane_service:
    move.w  (%a4), %d1                 /* old base (0xFFFF = force full) */
    move.w  %d0, (%a4)
    cmp.w   %d0, %d1
    beq     .Lps_cols
    cmpi.w  #0xFFFF, %d1
    beq     .Lps_full
    move.w  %d0, %d2
    sub.w   %d1, %d2
    cmpi.w  #32, %d2
    ble.s   .Lps_norm1
    subi.w  #64, %d2
.Lps_norm1:
    cmpi.w  #-32, %d2
    bge.s   .Lps_norm2
    addi.w  #64, %d2
.Lps_norm2:
    cmpi.w  #8, %d2
    bgt     .Lps_full
    cmpi.w  #-8, %d2
    blt     .Lps_full
    tst.w   %d2
    beq     .Lps_cols
    bgt.s   .Lps_down
    move.w  %d0, %d3                   /* scroll up: entering = new..old-1 */
    neg.w   %d2
    move.w  %d2, %d4
    bra.s   .Lps_stream
.Lps_down:
    move.w  %d1, %d3                   /* scroll down: entering = old+32.. */
    addi.w  #32, %d3
    move.w  %d2, %d4
.Lps_stream:
    andi.w  #0x003F, %d3
.Lps_stream_loop:
    bsr     .Lps_project_row
    move.w  %d3, -(%sp)
    andi.w  #0x001F, %d3
    bsr     .Lps_dma_row
    move.w  (%sp)+, %d3
    addq.w  #1, %d3
    andi.w  #0x003F, %d3
    subq.w  #1, %d4
    bne.s   .Lps_stream_loop
    bra.s   .Lps_cols
.Lps_full:
    move.w  %d0, %d3
    moveq   #32, %d4
.Lps_full_loop:
    bsr     .Lps_project_row
    addq.w  #1, %d3
    andi.w  #0x003F, %d3
    subq.w  #1, %d4
    bne.s   .Lps_full_loop
    move.l  #0xFFFFFFFF, (%a6)
.Lps_cols:
    moveq   #PLANE_COLS_PER_FRAME, %d5
    moveq   #0, %d3
.Lps_col_scan:
    move.w  %d3, %d2
    lsr.w   #3, %d2
    move.b  0(%a2,%d2.w), %d4
    bne.s   .Lps_col_check
    addq.w  #7, %d3
    bra.s   .Lps_col_next
.Lps_col_check:
    move.w  %d3, %d1
    andi.w  #7, %d1
    btst    %d1, %d4
    beq.s   .Lps_col_next
    bclr    %d1, 0(%a2,%d2.w)
    bsr     .Lps_col
    subq.w  #1, %d5
    beq.s   .Lps_rows
.Lps_col_next:
    addq.w  #1, %d3
    cmpi.w  #64, %d3
    blo.s   .Lps_col_scan
.Lps_rows:
    move.l  (%a6), %d6
    beq     .Lps_done
    moveq   #PLANE_ROWS_PER_FRAME, %d5
    moveq   #0, %d3
.Lps_row_scan:
    btst    %d3, %d6
    beq.s   .Lps_row_next
    bclr    %d3, %d6
    bsr     .Lps_dma_row
    subq.w  #1, %d5
    beq.s   .Lps_rows_out
.Lps_row_next:
    addq.w  #1, %d3
    cmpi.w  #32, %d3
    blo.s   .Lps_row_scan
.Lps_rows_out:
    move.l  %d6, (%a6)
.Lps_done:
    rts

/* d3 = tall row: staged[row & 31][0..63] = tall[row & 63][0..63] */
.Lps_project_row:
    movem.l %d0-%d1/%a0-%a1, -(%sp)
    move.w  %d3, %d0
    andi.w  #0x003F, %d0
    lsl.w   #7, %d0
    adda.w  %d0, %a0
    move.w  %d3, %d0
    andi.w  #0x001F, %d0
    lsl.w   #7, %d0
    adda.w  %d0, %a1
    moveq   #(16 - 1), %d1
.Lps_pr_loop:
    move.l  (%a0)+, (%a1)+
    move.l  (%a0)+, (%a1)+
    dbra    %d1, .Lps_pr_loop
    movem.l (%sp)+, %d0-%d1/%a0-%a1
    rts

/* d3 = plane row (0..31): DMA staged row -> plane row.  Uses a1, d7. */
.Lps_dma_row:
    movem.l %d0-%d3/%a0/%a3, -(%sp)
    move.w  %d3, %d1
    lsl.w   #7, %d1
    movea.l %a1, %a0
    adda.w  %d1, %a0
    moveq   #0, %d0
    move.w  %d1, %d0
    add.l   %d7, %d0
    move.w  #64, %d1
    moveq   #2, %d2
    bsr     .Lplane_dma
    movem.l (%sp)+, %d0-%d3/%a0/%a3
    rts

/* d3 = column: project 32 visible cells through the ring into staged while
 * gathering them into the bounce buffer, then one 64 B column DMA. */
.Lps_col:
    movem.l %d0-%d5/%a0/%a3, -(%sp)
    move.w  %d3, %d1
    add.w   %d1, %d1                   /* column byte offset */
    lea     plane_col_bounce, %a3
    moveq   #0, %d4
.Lps_col_gather:
    move.w  %d0, %d2
    add.w   %d4, %d2
    andi.w  #0x003F, %d2
    move.w  %d2, %d5
    lsl.w   #7, %d5
    add.w   %d1, %d5
    move.w  0(%a0,%d5.w), %d5
    move.w  %d5, (%a3)+
    andi.w  #0x001F, %d2
    lsl.w   #7, %d2
    add.w   %d1, %d2
    move.w  %d5, 0(%a1,%d2.w)          /* staged ring cell */
    addq.w  #1, %d4
    cmpi.w  #32, %d4
    blo.s   .Lps_col_gather
    lea     plane_col_bounce, %a0
    moveq   #0, %d2
    move.w  %d1, %d2
    move.l  %d7, %d0
    add.l   %d2, %d0
    move.w  #32, %d1
    move.w  #0x0080, %d2
    bsr     .Lplane_dma
    movem.l (%sp)+, %d0-%d5/%a0/%a3
    rts

vdp_commit_palette:
    move.l  #0xC0000000, VDP_CTRL

    lea     staged_palette_words, %a0
    move.w  #(64 - 1), %d7
.Lpal_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lpal_copy
    rts

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
    /* N2 ring: full vertical scroll value (plane wraps at 256). */
    move.w  %d0, VDP_DATA
    move.w  staged_scroll_y_bg, %d0
    neg.w   %d0
    addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
    /* N2 ring: full vertical scroll value. */
    move.w  %d0, VDP_DATA
    rts

/* Build 0175: FG bank-3 carrier re-assert (classification A).
 * The route table (palette_hooks.s) assigns arcade PC080SN FG bank 3 to Genesis
 * line 1 with the CARRIER flag for Stage 1 gameplay.  Evidence: nothing writes
 * that line during gameplay, but a pre-gameplay frontend write leaves it holding
 * a stale (non-bank-3) palette.  Each gameplay VBlank, look up the carrier line
 * and restore the cached converted bank 3 into it if it has drifted, then mark
 * palette dirty so the commit re-DMAs it.  Frontend line 1 (scene != 1) is never
 * touched; the palette hooks own it before gameplay. */
    .equ PR_SCENE_GAMEPLAY,   1
    .equ PR_OWNER_PC080SN_FG, 2
    .equ PR_FG_BANK,          3
vdp_reassert_fg_bank3_line:
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lrfb_done
    tst.b   fg_bank3_cache_valid
    beq.s   .Lrfb_done
    movem.l %d0-%d3/%a0-%a1, -(%sp)
    moveq   #PR_SCENE_GAMEPLAY, %d0
    moveq   #PR_OWNER_PC080SN_FG, %d1
    moveq   #PR_FG_BANK, %d2
    bsr     palette_route_lookup       /* d0 = line (or -1), d3 = flags */
    tst.l   %d0
    bmi.s   .Lrfb_restore_done         /* no matching route */
    btst    #0, %d3                     /* PROUTE_FLAG_CARRIER */
    beq.s   .Lrfb_restore_done
    lsl.w   #5, %d0                     /* line * 32 bytes */
    lea     staged_palette_words, %a1
    adda.w  %d0, %a1
    lea     fg_bank3_line_cache, %a0
    moveq   #(16 - 1), %d2
    moveq   #0, %d3
.Lrfb_cmp:
    move.w  (%a0)+, %d1
    cmp.w   (%a1)+, %d1
    beq.s   .Lrfb_cmp_next
    moveq   #1, %d3
.Lrfb_cmp_next:
    dbra    %d2, .Lrfb_cmp
    tst.b   %d3
    beq.s   .Lrfb_restore_done          /* line already holds bank 3 */
    lea     staged_palette_words, %a1
    adda.w  %d0, %a1
    lea     fg_bank3_line_cache, %a0
    moveq   #(16 - 1), %d2
.Lrfb_copy:
    move.w  (%a0)+, (%a1)+
    dbra    %d2, .Lrfb_copy
    move.b  #1, palette_dirty
.Lrfb_restore_done:
    movem.l (%sp)+, %d0-%d3/%a0-%a1
.Lrfb_done:
    rts

.if RASTAN_GAMEPLAY_HUD_SPRITES == 0
/* Build 0208: PC090OJ bank-0x36 (lizard men) line-0 carrier re-assert.
 * With gameplay HUD sprites suppressed, the shared route table assigns
 * (scene 1, PC090OJ, bank 0x36) -> line 0 with the CARRIER flag.  The arcade
 * writes bank 0x36 once at stage load (possibly while the frontend still owns
 * line 0), so the palette hooks only CACHE the converted bank; each gameplay
 * VBlank this routine looks up the carrier line and restores the cache into it
 * if it has drifted, then marks the palette dirty.  Non-gameplay scenes are
 * never touched (frontend keeps its line-0 HUD white). */
    .equ PR_OWNER_PC090OJ, 3
    .equ PR_BANK36,        0x36
vdp_reassert_bank36_line0:
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .Lrb36_done
    tst.b   pc090oj_bank36_cache_valid
    beq.s   .Lrb36_done
    movem.l %d0-%d3/%a0-%a1, -(%sp)
    moveq   #PR_SCENE_GAMEPLAY, %d0
    moveq   #PR_OWNER_PC090OJ, %d1
    moveq   #PR_BANK36, %d2
    bsr     palette_route_lookup       /* d0 = line (or -1), d3 = flags */
    tst.l   %d0
    bmi.s   .Lrb36_restore_done        /* no matching route */
    btst    #0, %d3                     /* PROUTE_FLAG_CARRIER */
    beq.s   .Lrb36_restore_done
    lsl.w   #5, %d0                     /* line * 32 bytes */
    lea     staged_palette_words, %a1
    adda.w  %d0, %a1
    lea     pc090oj_bank36_line0_cache, %a0
    moveq   #(16 - 1), %d2
    moveq   #0, %d3
.Lrb36_cmp:
    move.w  (%a0)+, %d1
    cmp.w   (%a1)+, %d1
    beq.s   .Lrb36_cmp_next
    moveq   #1, %d3
.Lrb36_cmp_next:
    dbra    %d2, .Lrb36_cmp
    tst.b   %d3
    beq.s   .Lrb36_restore_done         /* line already holds bank 0x36 */
    lea     staged_palette_words, %a1
    adda.w  %d0, %a1
    lea     pc090oj_bank36_line0_cache, %a0
    moveq   #(16 - 1), %d2
.Lrb36_copy:
    move.w  (%a0)+, (%a1)+
    dbra    %d2, .Lrb36_copy
    move.b  #1, palette_dirty
.Lrb36_restore_done:
    movem.l (%sp)+, %d0-%d3/%a0-%a1
.Lrb36_done:
    rts
.endif

    .section .bss
    .align 2

/* N2 plane pipeline state */
bg_col_dirty:
    .space 8
fg_col_dirty:
    .space 8
plane_col_bounce:
    .space 64
    .align 2
fg_bank3_line_cache:
    .space (16 * 2)
fg_bank3_cache_valid:
    .byte 0
fg_bank3_route_seen:
    .byte 0
    .align 2
/* Build 0208: converted arcade PC090OJ bank-0x36 palette (line-0 carrier). */
pc090oj_bank36_line0_cache:
    .space (16 * 2)
pc090oj_bank36_cache_valid:
    .byte 0
    .align 2

palette_dirty:
    .byte 0
tiles_dirty:
    .byte 0
    .align 2
bg_row_dirty:
    .long 0
bg_tall_dirty:
    .byte 0
    .align 2
bg_tall_project_base:
    .word 0
fg_row_dirty:
    .long 0
fg_tall_dirty:
    .byte 0
    .align 2
fg_tall_project_base:
    .word 0

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
staged_bg_tall_buffer:
    .space (4096 * 2)
staged_fg_buffer:
    .space (2048 * 2)
staged_fg_tall_buffer:
    .space (4096 * 2)
staged_palette_words:
    .space (64 * 2)
staged_tile_words:
    .space (48 * 2)
