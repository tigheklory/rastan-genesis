    .section .text,"ax"
    .global main_68k
    .global _VINT_handler
    .global sprite_dma_addr_high_bits_fix
    .global genesistan_hook_tilemap_plane_a
    .global genesistan_hook_tilemap_fg
    .global genesistan_hook_cwindow_clear
    .global genesistan_hook_tilemap_bg_fill
    .global genesistan_hook_text_writer_3c4d2
    .global genesistan_hook_text_writer_3c550
    .global genesistan_hook_text_writer_3c586
    .global genesistan_hook_text_writer_3c636
    .global genesistan_hook_text_writer_3c6dc
    .global genesistan_hook_text_writer_3c75c
    .global genesistan_hook_text_writer_3c7a4
    .global genesistan_hook_text_writer_3c830
    .global genesistan_hook_text_writer_3c950
    .global genesistan_hook_number_renderer_3c2e2
    .global genesistan_shadow_input_390001
    .global genesistan_shadow_input_390003
    .global genesistan_shadow_input_390005
    .global genesistan_shadow_input_390007
    .global genesistan_shadow_dip1
    .global genesistan_shadow_dip2
    .global rastan_direct_arcade_tick_entry

    .equ VDP_DATA,              0x00C00000
    .equ VDP_CTRL,              0x00C00004
    .equ IO_PAD1_DATA,          0x00A10003
    .equ IO_PAD2_DATA,          0x00A10005
    .equ IO_PAD1_CTRL,          0x00A10009
    .equ IO_PAD2_CTRL,          0x00A1000B

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

    .equ ARCADE_FIX_DEST_BG,    0x00FF10A0
    .equ ARCADE_FIX_DEST_FG,    0x00FF10A4
    .equ ARCADE_PC080SN_DESC_BG_LIST_OFFSET, 0x1000
    .equ ARCADE_PC080SN_DESC_FG_LIST_OFFSET, 0x1000
    .equ ARCADE_PC080SN_DEST_BG_OFFSET,      0x10A0
    .equ ARCADE_PC080SN_DEST_FG_OFFSET,      0x10A4
    .equ ARCADE_PC080SN_STRIP_INDEX_OFFSET,  0x10CA
    .equ ARCADE_PC080SN_STRIP_INDEX_FG_OFFSET, 0x10CA
    .equ ARCADE_PC080SN_CWINDOW_BASE_BG,     0x00C00000
    .equ ARCADE_PC080SN_CWINDOW_BASE_FG,     0x00C08000
    .equ ARCADE_PC080SN_CWINDOW_BYTES,       0x00004000
    .equ ARCADE_MAINCPU_ROM_BASE,            0x00000200
    .equ rastan_direct_arcade_tick_entry, 0x0003A208

    .equ VDP_MODE2_DISPLAY_OFF, 0x34
    .equ VDP_MODE2_DISPLAY_ON,  0x74

main_68k:
    move.w  #0x2700, %sr

    bsr     vdp_boot_setup
    moveq   #0, %d0
    bsr     load_scene_tiles
    bsr     init_staging_state

    move.w  #0x2000, %sr

.Lmain_loop:
    move.w  frame_counter, %d0
.Lwait_vblank:
    cmp.w   frame_counter, %d0
    beq.s   .Lwait_vblank

    bsr     arcade_tick_logic
    bra.s   .Lmain_loop

_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  VDP_CTRL, %d0

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_strips_if_dirty

    tst.b   palette_dirty
    beq.s   .Lskip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lskip_palette:

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_scroll

    addq.w  #1, frame_counter

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rte

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

genesistan_hook_tilemap_plane_a:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d7
    move.l  ARCADE_PC080SN_DEST_BG_OFFSET(%a5), %d5

    move.l  %d5, %d0
    andi.l  #0x00FFFFFF, %d0
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d0
    blo     .Lbg_hook_dest_invalid
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d0
    bhs     .Lbg_hook_dest_invalid

    move.l  %d0, %d4
    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d4
    move.l  %d4, %d0
    andi.l  #0x00000003, %d0
    bne     .Lbg_hook_dest_invalid

    lsr.l   #2, %d4
    move.w  %d4, %d1
    andi.w  #0x003F, %d1
    andi.w  #0x001F, %d1
    move.w  %d4, %d2
    lsr.w   #6, %d2
    andi.w  #0x003F, %d2

.Lscene_preamble_fast_path:
    move.l  %a0, %d0
    andi.l  #0x00FFFFFF, %d0

    cmp.l   genesistan_scene_a0_lo, %d0
    blo.s   .Lscene_slow_path

    cmp.l   genesistan_scene_a0_hi, %d0
    bhi.s   .Lscene_slow_path

    bra.s   .Lscene_preamble_done

.Lscene_slow_path:
    lea     genesistan_scene_a0_ranges, %a1
    move.l  %d5, %d6
    moveq   #0, %d3

.Lscene_loop:
    move.l  (%a1)+, %d4
    move.l  (%a1)+, %d5

    cmp.l   %d4, %d0
    blo.s   .Lnext_scene

    cmp.l   %d5, %d0
    bls.s   .Lscene_match

.Lnext_scene:
    addq.w  #1, %d3
    cmpi.w  #3, %d3
    blt.s   .Lscene_loop

    move.l  %d6, %d5
    bra.s   .Lscene_preamble_done

.Lscene_match:
    move.l  %d3, %d0
    bsr     load_scene_tiles
    move.l  %d6, %d5
    bra.w   .Lscene_preamble_done

.Lscene_preamble_done:
    lea     ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0
    movea.l #ARCADE_MAINCPU_ROM_BASE, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_bg_buffer, %a6

    moveq   #15, %d6
.Lbg_hook_desc_loop:
    move.l  (%a0)+, %d3
    btst    #0, %d3
    bne     .Lbg_hook_invalid_desc
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lbg_hook_invalid_desc

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4
    move.w  2(%a4), %d3
    cmpi.w  #0x7FE0, %d3
    bhi     .Lbg_hook_invalid_desc

    movea.l %a1, %a4
    move.w  %d3, %d0
    andi.l  #0x0000FFFF, %d0
    adda.l  %d0, %a4
    move.w  %d7, %d0
    lsl.w   #1, %d0
    adda.w  %d0, %a4

    move.w  %d4, %d0
    andi.w  #0x0003, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #6, %d3
    andi.w  #0x0001, %d3
    lsl.w   #2, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #7, %d3
    andi.w  #0x0001, %d3
    lsl.w   #3, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #5, %d3
    andi.w  #0x0001, %d3
    lsl.w   #4, %d3
    or.w    %d3, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0
    move.w  %d0, -(%sp)

    moveq   #3, %d4
.Lbg_hook_row_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    add.w   %d7, %d0
    add.w   %d7, %d0
    move.w  %d3, 0(%a6,%d0.w)
    move.l  bg_row_dirty, %d0
    bset    %d1, %d0
    move.l  %d0, bg_row_dirty

    adda.w  #8, %a4
    addq.w  #1, %d1
    andi.w  #0x001F, %d1
    dbra    %d4, .Lbg_hook_row_loop

    addq.l  #2, %sp
    bra.s   .Lbg_hook_desc_done

.Lbg_hook_invalid_desc:
    addq.w  #4, %d1
    andi.w  #0x001F, %d1

.Lbg_hook_desc_done:
    addi.l  #0x00000400, %d5
    addq.w  #4, %d2
    andi.w  #0x003F, %d2
    subq.w  #4, %d1
    andi.w  #0x001F, %d1
    dbra    %d6, .Lbg_hook_desc_loop

    move.l  %d5, ARCADE_PC080SN_DEST_BG_OFFSET(%a5)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lbg_hook_dest_invalid:
    addi.l  #0x00004000, %d5
    move.l  %d5, ARCADE_PC080SN_DEST_BG_OFFSET(%a5)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_tilemap_fg:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.w  ARCADE_PC080SN_STRIP_INDEX_FG_OFFSET(%a5), %d7
    move.l  ARCADE_PC080SN_DEST_FG_OFFSET(%a5), %d5

    move.l  %d5, %d0
    andi.l  #0x00FFFFFF, %d0
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d0
    blo     .Lfg_hook_dest_invalid
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d0
    bhs     .Lfg_hook_dest_invalid

    move.l  %d0, %d4
    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d4
    move.l  %d4, %d0
    andi.l  #0x00000003, %d0
    bne     .Lfg_hook_dest_invalid

    lsr.l   #2, %d4
    move.w  %d4, %d1
    andi.w  #0x003F, %d1
    andi.w  #0x001F, %d1
    move.w  %d4, %d2
    lsr.w   #6, %d2
    andi.w  #0x003F, %d2

.Lfg_scene_preamble_fast_path:
    move.l  %a0, %d0
    andi.l  #0x00FFFFFF, %d0

    cmp.l   genesistan_scene_a0_lo, %d0
    blo.s   .Lfg_scene_slow_path

    cmp.l   genesistan_scene_a0_hi, %d0
    bhi.s   .Lfg_scene_slow_path

    bra.s   .Lfg_scene_preamble_done

.Lfg_scene_slow_path:
    lea     genesistan_scene_a0_ranges, %a1
    move.l  %d5, %d6
    moveq   #0, %d3

.Lfg_scene_loop:
    move.l  (%a1)+, %d4
    move.l  (%a1)+, %d5

    cmp.l   %d4, %d0
    blo.s   .Lfg_next_scene

    cmp.l   %d5, %d0
    bls.s   .Lfg_scene_match

.Lfg_next_scene:
    addq.w  #1, %d3
    cmpi.w  #3, %d3
    blt.s   .Lfg_scene_loop

    move.l  %d6, %d5
    bra.s   .Lfg_scene_preamble_done

.Lfg_scene_match:
    move.l  %d3, %d0
    bsr     load_scene_tiles
    move.l  %d6, %d5
    bra.w   .Lfg_scene_preamble_done

.Lfg_scene_preamble_done:
    lea     ARCADE_PC080SN_DESC_FG_LIST_OFFSET(%a5), %a0
    movea.l #ARCADE_MAINCPU_ROM_BASE, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_fg_buffer, %a6

    moveq   #15, %d6
.Lfg_hook_desc_loop:
    move.l  (%a0)+, %d3
    btst    #0, %d3
    bne     .Lfg_hook_invalid_desc
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lfg_hook_invalid_desc

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4
    move.w  2(%a4), %d3
    cmpi.w  #0x7FE0, %d3
    bhi     .Lfg_hook_invalid_desc

    movea.l %a1, %a4
    move.w  %d3, %d0
    andi.l  #0x0000FFFF, %d0
    adda.l  %d0, %a4
    move.w  %d7, %d0
    lsl.w   #1, %d0
    adda.w  %d0, %a4

    move.w  %d4, %d0
    andi.w  #0x0003, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #6, %d3
    andi.w  #0x0001, %d3
    lsl.w   #2, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #7, %d3
    andi.w  #0x0001, %d3
    lsl.w   #3, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #5, %d3
    andi.w  #0x0001, %d3
    lsl.w   #4, %d3
    or.w    %d3, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0
    move.w  %d0, -(%sp)

    moveq   #3, %d4
.Lfg_hook_row_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    add.w   %d7, %d0
    add.w   %d7, %d0
    move.w  %d3, 0(%a6,%d0.w)
    move.l  fg_row_dirty, %d0
    bset    %d1, %d0
    move.l  %d0, fg_row_dirty

    adda.w  #8, %a4
    addq.w  #1, %d1
    andi.w  #0x001F, %d1
    dbra    %d4, .Lfg_hook_row_loop

    addq.l  #2, %sp
    bra.s   .Lfg_hook_desc_done

.Lfg_hook_invalid_desc:
    addq.w  #4, %d1
    andi.w  #0x001F, %d1

.Lfg_hook_desc_done:
    addi.l  #0x00000400, %d5
    addq.w  #4, %d2
    andi.w  #0x003F, %d2
    subq.w  #4, %d1
    andi.w  #0x001F, %d1
    dbra    %d6, .Lfg_hook_desc_loop

    move.l  %d5, ARCADE_PC080SN_DEST_FG_OFFSET(%a5)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lfg_hook_dest_invalid:
    addi.l  #0x00004000, %d5
    move.l  %d5, ARCADE_PC080SN_DEST_FG_OFFSET(%a5)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_tilemap_bg_fill:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    movea.l %a0, %a4
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2
    blo     .Lbg_fill_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lbg_fill_done

    move.w  %d1, %d6
    tst.w   %d6
    beq     .Lbg_fill_done

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_bg_buffer, %a6

    move.w  %d0, %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3

    move.l  %d0, %d4
    swap    %d4
    move.w  %d4, %d5
    andi.w  #0x0003, %d5

    move.w  %d4, %d7
    lsr.w   #8, %d7
    lsr.w   #6, %d7
    andi.w  #0x0001, %d7
    lsl.w   #2, %d7
    or.w    %d7, %d5

    move.w  %d4, %d7
    lsr.w   #8, %d7
    lsr.w   #7, %d7
    andi.w  #0x0001, %d7
    lsl.w   #3, %d7
    or.w    %d7, %d5

    move.w  %d4, %d7
    lsr.w   #8, %d7
    lsr.w   #5, %d7
    andi.w  #0x0001, %d7
    lsl.w   #4, %d7
    or.w    %d7, %d5

    add.w   %d5, %d5
    move.w  0(%a3,%d5.w), %d5
    or.w    %d5, %d3

.Lbg_fill_loop:
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lbg_fill_done

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2
    lsr.l   #2, %d2

    move.w  %d2, %d4
    andi.w  #0x003F, %d4
    move.w  %d2, %d5
    lsr.w   #6, %d5
    andi.w  #0x001F, %d5

    move.w  %d5, %d0
    lsl.w   #7, %d0
    add.w   %d4, %d0
    add.w   %d4, %d0
    move.w  %d3, 0(%a6,%d0.w)

    move.l  bg_row_dirty, %d0
    bset    %d5, %d0
    move.l  %d0, bg_row_dirty

    adda.l  #4, %a4
    subq.w  #1, %d6
    bne.s   .Lbg_fill_loop

.Lbg_fill_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_text_writer_3c4d2:
    movem.l %d1/%d5/%d6/%a3/%a5/%a6, -(%sp)

    movea.l %a1, %a2
    adda.w  #0x0050, %a2
    movea.l 2(%a0), %a0

    move.b  11(%a4), %d0
    ext.w   %d0

    move.l  %a1, %d4
    addq.l  #2, %d4
    move.l  %d4, %d1
    andi.l  #0x00FFFFFF, %d1
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d1
    blo     .Ltw_finish
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d1
    bhs     .Ltw_finish

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d1
    lsr.l   #2, %d1
    move.w  %d1, %d6
    andi.w  #0x003F, %d6
    move.w  %d1, %d5
    lsr.w   #6, %d5
    andi.w  #0x001F, %d5

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    cmpi.w  #0x0020, %d0
    bne.s   .Ltw_slow_path

    move.w  #0x0180, %d1
    andi.w  #0x3FFF, %d1
    add.w   %d1, %d1
    move.w  0(%a3,%d1.w), %d0

    moveq   #0, %d2
    bsr     .Ltw_translate_attr

    move.w  %d0, %d1
    or.w    %d2, %d1
    moveq   #9, %d4
.Ltw_fast_loop:
    bsr     .Ltw_store_cell
    addq.w  #2, %d6
    cmpi.w  #64, %d6
    blo.s   .Ltw_fast_next
    subi.w  #64, %d6
    addq.w  #1, %d5
    andi.w  #0x001F, %d5
.Ltw_fast_next:
    dbra    %d4, .Ltw_fast_loop
    bra.s   .Ltw_finish

.Ltw_slow_path:
    mulu.w  #5, %d0
    adda.w  %d0, %a0

    moveq   #0, %d4
.Ltw_slow_loop:
    move.b  (%a0)+, %d1
    ext.w   %d1
    move.w  %d1, %d0
    add.w   26(%a4), %d0
    add.w   24(%a4), %d0
    andi.w  #0x3FFF, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0

    move.w  22(%a4), %d2
    andi.w  #0x01FF, %d2
    bsr     .Ltw_translate_attr
    move.w  %d0, %d1
    or.w    %d2, %d1
    bsr     .Ltw_store_cell
    bsr     .Ltw_advance_cell

    cmpi.b  #0x50, %d3
    bne.s   .Ltw_half1_emit
    cmpi.w  #4, %d4
    beq.s   .Ltw_after_half1
.Ltw_half1_emit:
    move.w  22(%a4), %d2
    addi.w  #-16, %d2
    andi.w  #0x01FF, %d2
    bsr     .Ltw_translate_attr
    move.w  %d0, %d1
    or.w    %d2, %d1
    bsr     .Ltw_store_cell
    bsr     .Ltw_advance_cell
.Ltw_after_half1:
    addq.w  #1, %d4
    cmpi.w  #5, %d4
    blt.s   .Ltw_slow_loop

.Ltw_finish:
    movea.l %a2, %a1
    movem.l (%sp)+, %d1/%d5/%d6/%a3/%a5/%a6
    rts

.Ltw_translate_attr:
    move.w  %d2, %d1
    andi.w  #0x0003, %d1

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #6, %d7
    andi.w  #0x0001, %d7
    lsl.w   #2, %d7
    or.w    %d7, %d1

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #7, %d7
    andi.w  #0x0001, %d7
    lsl.w   #3, %d7
    or.w    %d7, %d1

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #5, %d7
    andi.w  #0x0001, %d7
    lsl.w   #4, %d7
    or.w    %d7, %d1

    add.w   %d1, %d1
    move.w  0(%a5,%d1.w), %d2
    rts

.Ltw_store_cell:
    move.w  %d5, %d2
    lsl.w   #7, %d2
    move.w  %d6, %d7
    add.w   %d7, %d2
    add.w   %d7, %d2
    move.w  %d1, 0(%a6,%d2.w)
    move.l  fg_row_dirty, %d2
    bset    %d5, %d2
    move.l  %d2, fg_row_dirty
    rts

.Ltw_advance_cell:
    addq.w  #1, %d6
    cmpi.w  #64, %d6
    blo.s   .Ltw_advance_done
    subi.w  #64, %d6
    addq.w  #1, %d5
    andi.w  #0x001F, %d5
.Ltw_advance_done:
    rts

.Ltw_store_from_components_at_a2:
    bsr     .Ltw_compose_d1_from_d0_d2
    bsr     .Ltw_store_d1_at_a2
    rts

.Ltw_compose_d1_from_d0_d2:
    move.w  %d0, %d7
    andi.w  #0x3FFF, %d7
    add.w   %d7, %d7
    move.w  0(%a3,%d7.w), %d7

    move.w  %d2, %d1
    andi.w  #0x01FF, %d1
    move.w  %d1, %d2
    bsr     .Ltw_translate_attr

    move.w  %d7, %d1
    or.w    %d2, %d1
    rts

.Ltw_store_d1_at_a2:
    movem.l %d2/%d5-%d7, -(%sp)

    move.l  %a2, %d0
    andi.l  #0x00FFFFFF, %d0
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d0
    blo.s   .Ltw_store_d1_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d0
    bhs.s   .Ltw_store_d1_done

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d0
    lsr.l   #2, %d0
    move.w  %d0, %d6
    andi.w  #0x003F, %d6
    move.w  %d0, %d5
    lsr.w   #6, %d5
    andi.w  #0x001F, %d5
    bsr     .Ltw_store_cell

.Ltw_store_d1_done:
    movem.l (%sp)+, %d2/%d5-%d7
    rts

.Ltw_write_pair_same:
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    movea.l %a1, %a2
    adda.w  #6, %a2
    bsr     .Ltw_store_from_components_at_a2
    rts

genesistan_hook_text_writer_3c950:
    movem.l %d4/%d6/%a2/%a3/%a5/%a6, -(%sp)

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    clr.w   %d0
    clr.w   %d5

    btst    #0, %d6
    bne.s   .L3c950_dispatch_d6
    tst.b   %d7
    beq     .L3c950_alt_loop
    bra     .L3c950_primary_loop

.L3c950_dispatch_d6:
    tst.b   3(%a4)
    bne     .L3c950_primary_loop
    tst.b   %d7
    beq     .L3c950_primary_loop
    bra     .L3c950_alt_loop

.L3c950_primary_loop:
    bsr     .L3c950_read_opcode
    tst.w   %d5
    bne     .L3c950_sentinel_primary

    clr.w   %d7
    cmpi.b  #0x40, %d3
    bne.s   .L3c950_primary_check_80
    addq.w  #1, %d7
.L3c950_primary_check_80:
    cmpi.b  #0x80, %d3
    bne.s   .L3c950_primary_attr
    ori.w   #0x4000, %d0
.L3c950_primary_attr:
    bsr     .L3c950_apply_attr_gate
    move.w  %d0, %d4

    move.b  (%a0)+, %d1
    ext.w   %d1
    add.w   26(%a4), %d1
    cmpi.b  #0x70, %d3
    bne.s   .L3c950_primary_tile_ready
    add.w   24(%a4), %d1
.L3c950_primary_tile_ready:
    move.w  %d1, %d0
    move.w  %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2

    bsr     .L3c950_compute_next_attr

    move.b  (%a0)+, %d7
    ext.w   %d7
    add.w   22(%a4), %d7
    move.w  %d7, %d0
    move.w  %d4, %d2
    movea.l %a1, %a2
    adda.w  #6, %a2
    bsr     .Ltw_store_from_components_at_a2

    adda.w  #8, %a1
.L3c950_primary_iter_done:
    subq.l  #1, %d2
    bne     .L3c950_primary_loop
    bra     .L3c950_done

.L3c950_alt_loop:
    bsr     .L3c950_read_opcode
    tst.w   %d5
    bne     .L3c950_sentinel_primary

    clr.w   %d7
    cmpi.b  #0x40, %d3
    bne.s   .L3c950_alt_attr
    addq.w  #1, %d7
.L3c950_alt_attr:
    ori.w   #0x4000, %d0
    bsr     .L3c950_apply_attr_gate
    move.w  %d0, %d4

    move.b  (%a0)+, %d1
    ext.w   %d1
    add.w   26(%a4), %d1
    move.w  %d1, %d0
    move.w  %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2

    bsr     .L3c950_compute_next_attr

    move.b  (%a0)+, %d7
    ext.w   %d7
    neg.w   %d7
    sub.w   0x0010, %d7
    add.w   22(%a4), %d7
    move.w  %d7, %d0
    move.w  %d4, %d2
    movea.l %a1, %a2
    adda.w  #6, %a2
    bsr     .Ltw_store_from_components_at_a2

    adda.w  #8, %a1
.L3c950_alt_iter_done:
    subq.l  #1, %d2
    bne     .L3c950_alt_loop
    bra     .L3c950_done

.L3c950_sentinel_primary:
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .L3c950_store_blank_tile_preserve_attr
    adda.w  #8, %a1
    bra     .L3c950_primary_iter_done

.L3c950_read_opcode:
    move.b  (%a0)+, %d0
    move.b  %d0, %d3
    andi.b  #0xF0, %d3
    cmpi.b  #0xFF, %d0
    bne.s   .L3c950_read_done
    moveq   #1, %d5
.L3c950_read_done:
    rts

.L3c950_apply_attr_gate:
    btst    #6, 39(%a4)
    beq.s   .L3c950_apply_done
    move.b  39(%a4), %d0
.L3c950_apply_done:
    rts

.L3c950_compute_next_attr:
    clr.w   %d0
    move.b  (%a0)+, %d0
    tst.w   %d7
    beq.s   .L3c950_next_add
    neg.w   %d0
.L3c950_next_add:
    add.w   30(%a4), %d0
    move.w  %d0, %d4
    clr.w   %d0
    rts

.L3c950_store_blank_tile_preserve_attr:
    movem.l %d0/%d1/%d4-%d7, -(%sp)

    move.l  %a2, %d4
    andi.l  #0x00FFFFFF, %d4
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d4
    blo.s   .L3c950_blank_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d4
    bhs.s   .L3c950_blank_done

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d4
    lsr.l   #2, %d4
    move.w  %d4, %d6
    andi.w  #0x003F, %d6
    move.w  %d4, %d5
    lsr.w   #6, %d5
    andi.w  #0x001F, %d5

    move.w  %d5, %d7
    lsl.w   #7, %d7
    add.w   %d6, %d7
    add.w   %d6, %d7

    move.w  0(%a6,%d7.w), %d1
    andi.w  #0xF800, %d1

    move.w  #0x0180, %d0
    andi.w  #0x3FFF, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0
    or.w    %d0, %d1

    move.w  %d1, 0(%a6,%d7.w)

    move.l  fg_row_dirty, %d1
    bset    %d5, %d1
    move.l  %d1, fg_row_dirty

.L3c950_blank_done:
    movem.l (%sp)+, %d0/%d1/%d4-%d7
    rts

.L3c950_done:
    movem.l (%sp)+, %d4/%d6/%a2/%a3/%a5/%a6
    rts

genesistan_hook_number_renderer_3c2e2:
    movem.l %d0-%d7/%a0/%a2-%a6, -(%sp)

    move.w  %d0, %d6
    mulu.w  #10, %d6
    movea.l #0x0003C57C, %a0
    adda.w  %d6, %a0

    move.w  (%a0), %d3
    movea.l 2(%a0), %a1
    move.l  6(%a0), %d2
    move.w  %d3, %d7

    move.l  %a1, %d6
    andi.l  #0x00FFFFFF, %d6
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d6
    blo     .Lnr3c2e2_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d6
    bhs     .Lnr3c2e2_done

    move.l  %a1, %d4

    movea.l %a5, %a4
    andi.l  #0x0000FFFF, %d2
    adda.l  %d2, %a4

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    clr.w   %d5

    cmpi.w  #-1, %d3
    beq     .Lnr3c2e2_all_handler
    bra     .Lnr3c2e2_digit_loop

.Lnr3c2e2_all_handler:
    moveq   #0, %d1
    move.b  (%a4), %d1
    andi.w  #0x000F, %d1
    cmpi.w  #0x0007, %d1
    bne.s   .Lnr3c2e2_all_single_digit

    movea.l %d4, %a1
    suba.w  #8, %a1

    move.w  #0x0041, %d0
    move.w  %d5, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    adda.w  #4, %a1

    move.w  #0x004C, %d0
    move.w  %d5, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    adda.w  #4, %a1

    move.w  #0x004C, %d0
    move.w  %d5, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2

    movea.l %d4, %a1
    adda.w  #2, %a1
    bra     .Lnr3c2e2_done

.Lnr3c2e2_all_single_digit:
    movea.l %d4, %a1
    moveq   #1, %d3

.Lnr3c2e2_digit_loop:
    btst    #0, %d3
    beq.s   .Lnr3c2e2_high_nibble

    moveq   #0, %d1
    move.b  (%a4), %d1
    andi.w  #0x000F, %d1
    ori.w   #0x0030, %d1
    subq.l  #1, %a4
    bra.s   .Lnr3c2e2_emit_digit

.Lnr3c2e2_high_nibble:
    moveq   #0, %d1
    move.b  (%a4), %d1
    lsr.w   #4, %d1
    andi.w  #0x000F, %d1
    ori.w   #0x0030, %d1

.Lnr3c2e2_emit_digit:
    move.w  %d1, %d0
    move.w  %d5, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    adda.w  #4, %a1

    subq.w  #1, %d3
    bne     .Lnr3c2e2_digit_loop

    cmpi.w  #6, %d7
    bne     .Lnr3c2e2_done

    moveq   #6, %d3
    movea.l %d4, %a1

    move.w  #0x0030, %d0
    andi.w  #0x3FFF, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d6

.Lnr3c2e2_suppress_loop:
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Lnr3c2e2_read_staged_cell_at_a2
    cmpi.w  #-1, %d1
    beq     .Lnr3c2e2_done

    move.w  %d1, %d0
    andi.w  #0x07FF, %d0
    cmp.w   %d6, %d0
    bne     .Lnr3c2e2_done

    move.w  #0x0020, %d0
    move.w  %d5, %d2
    bsr     .Ltw_store_from_components_at_a2

    adda.w  #4, %a1
    subq.w  #1, %d3
    bne     .Lnr3c2e2_suppress_loop

.Lnr3c2e2_done:
    movem.l (%sp)+, %d0-%d7/%a0/%a2-%a6
    rts

.Lnr3c2e2_read_staged_cell_at_a2:
    movem.l %d2/%d5-%d7, -(%sp)

    move.l  %a2, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
    blo.s   .Lnr3c2e2_read_oob
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs.s   .Lnr3c2e2_read_oob

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
    lsr.l   #2, %d2

    move.w  %d2, %d6
    andi.w  #0x003F, %d6
    move.w  %d2, %d5
    lsr.w   #6, %d5
    andi.w  #0x001F, %d5

    move.w  %d5, %d7
    lsl.w   #7, %d7
    add.w   %d6, %d7
    add.w   %d6, %d7
    move.w  0(%a6,%d7.w), %d1
    bra.s   .Lnr3c2e2_read_done

.Lnr3c2e2_read_oob:
    move.w  #-1, %d1

.Lnr3c2e2_read_done:
    movem.l (%sp)+, %d2/%d5-%d7
    rts

genesistan_hook_text_writer_3c550:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    adda.w  %d0, %a0

    move.b  (%a0), %d7
    ext.w   %d7

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    moveq   #4, %d3
    clr.w   %d4
.L3c550_loop:
    move.w  %d7, %d2
    add.w   22(%a4), %d2
    add.w   %d4, %d2
    move.w  26(%a4), %d0
    bsr     .Ltw_write_pair_same
    adda.w  #8, %a1
    addi.w  #16, %d4
    dbra    %d3, .L3c550_loop

    adda.w  #48, %a1

    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

genesistan_hook_text_writer_3c586:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    mulu.w  #3, %d0
    adda.w  %d0, %a0

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    cmpi.b  #6, 1(%a4)
    beq.s   .L3c586_alt

    moveq   #3, %d3
    clr.w   %d4
    bsr     .L3c586_inner_606

    clr.w   %d6
    clr.w   %d7
    bsr     .L3c586_helper_742
    adda.w  #8, %a1

    suba.w  #3, %a0
    moveq   #3, %d3
    move.w  #-16, %d4
    bsr     .L3c586_inner_606

    clr.w   %d6
    move.w  #-16, %d7
    bsr     .L3c586_helper_742
    adda.w  #24, %a1
    bra.s   .L3c586_done

.L3c586_alt:
    clr.w   %d6
    clr.w   %d7
    bsr     .L3c586_helper_742
    adda.w  #8, %a1

    moveq   #3, %d3
    clr.w   %d4
    bsr     .L3c586_inner_606

    suba.w  #3, %a0
    clr.w   %d6
    move.w  #-16, %d7
    bsr     .L3c586_helper_742
    adda.w  #8, %a1

    moveq   #3, %d3
    move.w  #-16, %d4
    bsr     .L3c586_inner_606

    adda.w  #16, %a1

.L3c586_done:
    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

.L3c586_inner_606:
    move.b  (%a0)+, %d0
    ext.w   %d0
    cmpi.b  #-1, %d0
    bne.s   .L3c586_emit_pair

    move.w  #0x0180, %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    bra.s   .L3c586_inner_advance

.L3c586_emit_pair:
    move.w  %d0, %d2
    add.w   22(%a4), %d2

    move.w  26(%a4), %d0
    add.w   %d4, %d0
    andi.w  #0x01FF, %d0
    bsr     .Ltw_write_pair_same

.L3c586_inner_advance:
    adda.w  #8, %a1
    dbra    %d3, .L3c586_inner_606
    rts

.L3c586_helper_742:
    move.w  26(%a4), %d0
    add.w   %d6, %d0
    andi.w  #0x01FF, %d0

    move.w  22(%a4), %d2
    add.w   %d7, %d2
    bsr     .Ltw_write_pair_same
    rts

genesistan_hook_text_writer_3c636:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    moveq   #0, %d7
    cmpi.b  #2, 280(%a5)
    beq.s   .L3c636_include
    cmpi.w  #98, 318(%a5)
    bcs.s   .L3c636_exclude
    cmpi.w  #100, 318(%a5)
    bcs.s   .L3c636_include
    bra.s   .L3c636_exclude
.L3c636_include:
    moveq   #1, %d7
.L3c636_exclude:

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    lsl.w   #2, %d0
    adda.w  %d0, %a0

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    tst.w   %d7
    beq.s   .L3c636_no_prelude

    clr.w   %d6
    clr.w   %d4
    bsr     .L3c636_helper_742
    adda.w  #8, %a1

    clr.w   %d6
    move.w  #-16, %d4
    bsr     .L3c636_helper_742
    adda.w  #8, %a1

.L3c636_no_prelude:
    moveq   #2, %d3
    clr.w   %d4
    bsr     .L3c636_inner_6ac

    moveq   #2, %d3
    move.w  #-16, %d4
    bsr     .L3c636_inner_6ac

    tst.w   %d7
    beq.s   .L3c636_post48
    adda.w  #32, %a1
    bra.s   .L3c636_done
.L3c636_post48:
    adda.w  #48, %a1

.L3c636_done:
    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

.L3c636_inner_6ac:
    move.b  (%a0)+, %d0
    ext.w   %d0
    cmpi.b  #-1, %d0
    bne.s   .L3c636_emit_pair

    move.w  #0x0180, %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    bra.s   .L3c636_advance

.L3c636_emit_pair:
    move.w  %d0, %d1
    add.w   26(%a4), %d1
    move.w  %d1, %d0

    move.w  22(%a4), %d2
    add.w   %d4, %d2
    bsr     .Ltw_write_pair_same

.L3c636_advance:
    adda.w  #8, %a1
    dbra    %d3, .L3c636_inner_6ac
    rts

.L3c636_helper_742:
    move.w  26(%a4), %d0
    add.w   %d6, %d0
    andi.w  #0x01FF, %d0

    move.w  22(%a4), %d2
    add.w   %d4, %d2
    bsr     .Ltw_write_pair_same
    rts

genesistan_hook_text_writer_3c6dc:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    mulu.w  #9, %d0
    adda.w  %d0, %a0

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    move.w  #-48, %d1
    move.w  #16, %d4
    moveq   #6, %d3
    bsr     .L3c6dc_inner_70a

    move.w  #-48, %d1
    clr.w   %d4
    moveq   #3, %d3
    bsr     .L3c6dc_inner_70a

    adda.w  #8, %a1

    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

.L3c6dc_inner_70a:
    move.b  (%a0)+, %d2
    ext.w   %d2
    tst.w   %d2
    bne.s   .L3c6dc_emit_pair

    move.w  #0x0180, %d0
    move.w  22(%a4), %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    bra.s   .L3c6dc_after_pair

.L3c6dc_emit_pair:
    move.w  %d1, %d0
    add.w   26(%a4), %d0

    move.w  22(%a4), %d2
    add.b   (%a0,-1), %d2
    bsr     .Ltw_write_pair_same

    add.w   %d4, %d1

.L3c6dc_after_pair:
    adda.w  #8, %a1
    dbra    %d3, .L3c6dc_inner_70a
    rts

genesistan_hook_text_writer_3c75c:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    mulu.w  #7, %d0
    adda.w  %d0, %a0

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    move.w  #-16, %d6
    move.w  #-8, %d7
    bsr     .L3c75c_helper_742
    adda.w  #8, %a1

    moveq   #1, %d3
    move.w  #-8, %d4
    bsr     .L3c75c_inner_7d2

    moveq   #1, %d3
    clr.w   %d4
    bsr     .L3c75c_inner_7d2

    moveq   #1, %d3
    move.w  #-16, %d4
    bsr     .L3c75c_inner_7d2

    moveq   #4, %d3
    move.w  #-8, %d4
    bsr     .L3c75c_inner_7d2

    adda.w  #16, %a1

    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

.L3c75c_inner_7d2:
    move.b  (%a0)+, %d0
    ext.w   %d0
    cmpi.b  #-1, %d0
    bne.s   .L3c75c_emit_pair

    move.w  #0x0180, %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    bra.s   .L3c75c_advance

.L3c75c_emit_pair:
    add.w   26(%a4), %d0
    move.w  %d0, %d1
    move.w  %d1, %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    bsr     .Ltw_write_pair_same

.L3c75c_advance:
    adda.w  #8, %a1
    dbra    %d3, .L3c75c_inner_7d2
    rts

.L3c75c_helper_742:
    move.w  26(%a4), %d0
    add.w   %d6, %d0
    andi.w  #0x01FF, %d0
    move.w  22(%a4), %d2
    add.w   %d7, %d2
    bsr     .Ltw_write_pair_same
    rts

genesistan_hook_text_writer_3c7a4:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    mulu.w  #6, %d0
    adda.w  %d0, %a0

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    moveq   #2, %d3
    clr.w   %d4
    bsr     .L3c7a4_inner_804

    moveq   #2, %d3
    move.w  #-16, %d4
    bsr     .L3c7a4_inner_804

    moveq   #6, %d3
    move.w  #-8, %d4
    bsr     .L3c75c_inner_7d2

    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

.L3c7a4_inner_804:
    move.w  #-32, %d0
    cmpi.w  #2, %d3
    beq.s   .L3c7a4_tile_ready
    move.w  #-48, %d0
.L3c7a4_tile_ready:
    add.w   26(%a4), %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    bsr     .Ltw_write_pair_same
    adda.w  #8, %a1
    dbra    %d3, .L3c7a4_inner_804
    rts

genesistan_hook_text_writer_3c830:
    movem.l %d1-%d7/%a2-%a6, -(%sp)

    move.b  56(%a4), %d7
    move.b  280(%a5), %d6
    move.w  318(%a5), %d5

    movea.l 2(%a0), %a0
    move.b  11(%a4), %d0
    ext.w   %d0
    lsl.w   #2, %d0
    adda.w  %d0, %a0

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    tst.b   %d7
    bne.s   .L3c830_alt_path

    moveq   #5, %d3
    move.w  #-8, %d4
    bsr     .L3c830_inner_85e

    suba.l  #4, %a0
    moveq   #5, %d3
    move.w  #-24, %d4
    bsr     .L3c830_inner_85e
    bra.s   .L3c830_done

.L3c830_alt_path:
    clr.w   %d0
    clr.w   %d2
    bsr     .Ltw_write_pair_same
    adda.w  #8, %a1

    move.w  22(%a4), %d2
    addi.w  #-16, %d2
    move.w  26(%a4), %d0
    bsr     .Ltw_write_pair_same
    adda.w  #8, %a1

    moveq   #2, %d3
    move.w  #-8, %d4
    bsr     .L3c830_inner_85e

    moveq   #2, %d3
    move.w  #-16, %d4
    bsr     .L3c830_inner_85e

    suba.l  #2, %a0
    moveq   #2, %d3
    clr.w   %d4
    bsr     .L3c830_inner_85e

    adda.w  #16, %a1

.L3c830_done:
    movem.l (%sp)+, %d1-%d7/%a2-%a6
    rts

.L3c830_inner_85e:
    clr.w   %d0
    clr.w   %d2

    cmpi.w  #5, %d3
    bne.s   .L3c830_not_first

    move.w  22(%a4), %d2
    add.w   %d4, %d2
    cmpi.b  #3, %d6
    bne.s   .L3c830_first_tile
    move.w  #0x0A0D, %d2
    cmpi.w  #-8, %d4
    bne.s   .L3c830_check_318
    addq.w  #1, %d2
.L3c830_check_318:
    cmpi.w  #63, %d5
    bcs.s   .L3c830_first_tile
    addq.w  #7, %d2
    bsr     .L3c830_store_left_with_special_attr
    bra.s   .L3c830_emit_right

.L3c830_not_first:
    move.b  (%a0)+, %d0
    ext.w   %d0
    tst.w   %d0
    bne.s   .L3c830_first_tile
    move.w  #0x0180, %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    bra.s   .L3c830_emit_right

.L3c830_first_tile:
    add.w   26(%a4), %d0
    move.w  22(%a4), %d2
    add.w   %d4, %d2
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2

.L3c830_emit_right:
    movea.l %a1, %a2
    adda.w  #6, %a2
    bsr     .Ltw_store_from_components_at_a2

    adda.w  #8, %a1
    dbra    %d3, .L3c830_inner_85e
    rts

.L3c830_store_left_with_special_attr:
    move.w  26(%a4), %d0
    movea.l %a1, %a2
    adda.w  #2, %a2
    bsr     .Ltw_store_from_components_at_a2
    rts

genesistan_hook_cwindow_clear:
    movem.l %d0-%d3/%a0-%a3, -(%sp)

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    move.w  #0x0020, %d0
    add.w   %d0, %d0
    move.w  0(%a2,%d0.w), %d3

    lea     genesistan_pc080sn_attr_lut, %a3
    moveq   #0, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0
    or.w    %d0, %d3

    lea     staged_bg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lcw_clear_bg:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_bg

    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lcw_clear_fg:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_fg

    move.l  #0xFFFFFFFF, bg_row_dirty
    move.l  #0xFFFFFFFF, fg_row_dirty

    movem.l (%sp)+, %d0-%d3/%a0-%a3
    rts

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
    bsr     vdp_set_vram_write_addr

    lea     staged_bg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #(64 - 1), %d7
.Lbg_row_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lbg_row_copy

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
    bsr     vdp_set_vram_write_addr

    lea     staged_fg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #(64 - 1), %d7
.Lfg_row_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lfg_row_copy

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

    move.w  staged_scroll_x_fg, VDP_DATA
    move.w  staged_scroll_x_bg, VDP_DATA

    move.l  #0x40000010, VDP_CTRL
    move.w  staged_scroll_y_fg, VDP_DATA
    move.w  staged_scroll_y_bg, VDP_DATA
    rts

rastan_direct_update_inputs:
    move.b  #0x40, IO_PAD1_CTRL
    move.b  #0x40, IO_PAD2_CTRL

    move.b  #0x00, IO_PAD1_DATA
    nop
    move.b  IO_PAD1_DATA, %d1
    move.b  %d1, %d6
    move.b  #0x40, IO_PAD1_DATA
    nop
    move.b  IO_PAD1_DATA, %d0

    move.b  %d0, %d2
    ori.b   #0xC0, %d2
    btst    #4, %d1
    bne.s   .Lp1_a_done
    bclr    #6, %d2
.Lp1_a_done:
    move.b  %d2, genesistan_shadow_input_390001

    move.b  #0x00, IO_PAD2_DATA
    nop
    move.b  IO_PAD2_DATA, %d1
    move.b  %d1, %d7
    move.b  #0x40, IO_PAD2_DATA
    nop
    move.b  IO_PAD2_DATA, %d0

    move.b  %d0, %d3
    ori.b   #0xC0, %d3
    btst    #4, %d1
    bne.s   .Lp2_a_done
    bclr    #6, %d3
.Lp2_a_done:
    move.b  %d3, genesistan_shadow_input_390003

    moveq   #-1, %d4
    btst    #6, %d2
    bne.s   .Lp1_coin_done
    bclr    #4, %d4
    bclr    #6, %d4
.Lp1_coin_done:
    btst    #6, %d3
    bne.s   .Lp2_coin_done
    bclr    #5, %d4
    bclr    #6, %d4
.Lp2_coin_done:
    move.b  %d4, genesistan_shadow_input_390005

    moveq   #-1, %d5
    btst    #5, %d6
    bne.s   .Lp1_start_sys_done
    bclr    #3, %d5
.Lp1_start_sys_done:
    btst    #5, %d7
    bne.s   .Lp2_start_sys_done
    bclr    #4, %d5
.Lp2_start_sys_done:

    moveq   #0, %d0
    btst    #6, %d2
    bne.s   .Lp1_a_state_ready
    moveq   #1, %d0
.Lp1_a_state_ready:
    tst.b   prev_coin_p1_a_pressed
    bne.s   .Lcoin_prev_pressed
    tst.b   %d0
    beq.s   .Lcoin_prev_store
    bclr    #5, %d5
.Lcoin_prev_store:
    move.b  %d0, prev_coin_p1_a_pressed
    bra.s   .Lsys_store_done
.Lcoin_prev_pressed:
    move.b  %d0, prev_coin_p1_a_pressed
.Lsys_store_done:
    move.b  %d5, genesistan_shadow_input_390007

    rts

arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    lea     0x00FF0000, %a5
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts

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
    bne.s   .Lload_scene_force_title
    lea     genesistan_scene_preload_endround, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_force_title:
    moveq   #0, %d6
.Lload_scene_manifest_ready:
    move.w  #0x2700, %sr

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
    move.b  %d6, genesistan_current_scene_id
    lea     genesistan_scene_a0_ranges, %a3
    moveq   #0, %d4
    move.w  %d6, %d4
    lsl.w   #3, %d4
    adda.w  %d4, %a3
    move.l  (%a3)+, %d0
    move.l  (%a3), %d1
    move.l  %d0, genesistan_scene_a0_lo
    move.l  %d1, genesistan_scene_a0_hi

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    move.w  #0x2000, %sr
    movem.l (%sp)+, %d1-%d7/%a0-%a4
    rts

init_staging_state:
    lea     0x00FF0000, %a5
    clr.w   frame_counter
    clr.w   tick_counter

    move.l  #0x00C00000, staged_dest_ptr_bg
    move.l  #0x00C08000, staged_dest_ptr_fg

    move.l  #0x00C00000, ARCADE_FIX_DEST_BG
    move.l  #0x00C08000, ARCADE_FIX_DEST_FG

    move.b  #1, palette_dirty
    move.b  #1, tiles_dirty
    clr.l   bg_row_dirty
    clr.l   fg_row_dirty

    lea     palette_init_words, %a0
    lea     staged_palette_words, %a1
    move.w  #(64 - 1), %d7
.Lpal_init:
    move.w  (%a0)+, (%a1)+
    dbra    %d7, .Lpal_init

    lea     tile_init_words, %a0
    lea     staged_tile_words, %a1
    move.w  #(48 - 1), %d7
.Ltile_init:
    move.w  (%a0)+, (%a1)+
    dbra    %d7, .Ltile_init

    lea     staged_bg_buffer, %a0
    moveq   #31, %d6
.Lbg_row:
    moveq   #63, %d5
.Lbg_col:
    move.w  %d6, %d0
    eor.w   %d5, %d0
    andi.w  #0x0001, %d0
    bne.s   .Lbg_tile_two
    move.w  #0x0001, (%a0)+
    bra.s   .Lbg_next
.Lbg_tile_two:
    move.w  #0x0002, (%a0)+
.Lbg_next:
    dbra    %d5, .Lbg_col
    dbra    %d6, .Lbg_row

    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lfg_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lfg_clear

    move.l  #VRAM_PLANE_A_BASE, %d0
    bsr     vdp_set_vram_write_addr
    move.w  #(2048 - 1), %d7
.Lplane_a_clear:
    move.w  #0x0000, VDP_DATA
    dbra    %d7, .Lplane_a_clear

    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    /* ------------------------------------------------------------------ */
    /* Arcade workram factory defaults at 0xFF0000                         */
    /* Equivalent to startup_common / genesistan_init_workram_direct       */
    /* Called on every warm restart; re-initializes all factory state      */
    /* ------------------------------------------------------------------ */

    /* Step 1: zero first 0x100 bytes (0xFF0000..0xFF00FF) */
    lea     0x00FF0000, %a0
    moveq   #(64-1), %d7
.Larcade_wram_clear:
    clr.l   (%a0)+
    dbra    %d7, .Larcade_wram_clear

    /* Step 2: write factory defaults */
    lea     0x00FF0000, %a0

    /* Coinage defaults: 1 coin = 1 credit */
    move.w  #1,      0x0008(%a0)    /* A5@(8)  coin1 */
    move.w  #1,      0x000A(%a0)    /* A5@(10) coin2 */
    move.w  #1,      0x000E(%a0)    /* A5@(14) */
    move.w  #1,      0x0010(%a0)    /* A5@(16) */

    /* Display control mirror */
    move.w  #0x0060, 0x0014(%a0)    /* A5@(20) = 0x0060 */

    /* DIP mirrors: active-low; hardcoded 0xFF = all switches off (factory) */
    move.w  #0x0001, 0x0018(%a0)    /* A5@(24) = ~DIP1 */
    move.w  #0x0000, 0x001C(%a0)    /* A5@(28) = ~DIP2 */

    /* Init flag */
    move.w  #1,      0x0026(%a0)    /* A5@(38) = 1 */

    /* Delay countdown: 160 ticks before warm restart (startup_common default) */
    move.w  #160,    0x002C(%a0)    /* A5@(44) = 160 = 0xA0 */

    /* Mode, cabinet, monitor from DIP defaults (ndip=0xFF) */
    move.w  #0,      0x002E(%a0)    /* A5@(46) mode = ndip2 & 3 = 3 */
    move.w  #1,      0x0030(%a0)    /* A5@(48) cab  = ndip1 & 1 = 1 */
    move.w  #0,      0x0032(%a0)    /* A5@(50) mon  = ndip1 & 2 = 2 */

    /* Bonus and difficulty (DIP defaults: max table indices, capped at 3) */
    move.w  #6,      0x0036(%a0)    /* A5@(54) bonus = bonus_table[3] = 6 */
    move.w  #0x2500, 0x0038(%a0)    /* A5@(56) diff  = diff_table[3]  = 0x2500 */

    /* Sprite init marker */
    move.w  #0x00AA, 0x004A(%a0)    /* A5@(74) = 0x00AA */

    /* Transition buffer block A seeding (from arcade 0x03A9E6 init helper) */
    move.w  0x0036(%a0), 0x0080(%a0)  /* A5+0x80 = A5+0x36 (bonus) */
    move.w  0x0038(%a0), 0x00B2(%a0)  /* A5+0xB2 = A5+0x38 (difficulty) */
    move.b  #1, 0x0097(%a0)           /* A5+0x97 = 1 */
    move.b  #1, 0x0098(%a0)           /* A5+0x98 = 1 */

    /* Copy block A (A5+0x80..0xBF) → block B (A5+0xC0..0xFF) */
    lea     0x0080(%a0), %a1
    lea     0x00C0(%a0), %a2
    moveq   #(16-1), %d7              /* 16 longwords = 64 bytes */
.Lblock_b_copy:
    move.l  (%a1)+, (%a2)+
    dbra    %d7, .Lblock_b_copy

    /* Restore A0 to workram base */
    lea     0x00FF0000, %a0

    /* Title init flag */
    move.w  #1,      0x0100(%a0)    /* A5@(256) = 1 */

    /* Config table: 39 bytes from ROM at Genesis 0x3B2D4 (arcade 0x3B0D4) */
    /* to A5@(320) = workram byte offset 0x0140 */
    lea     0x0003B2D4, %a1
    lea     0x0140(%a0), %a2
    moveq   #(39-1), %d7
.Larcade_cfg_copy:
    move.b  (%a1)+, (%a2)+
    dbra    %d7, .Larcade_cfg_copy

    rts

    .section .rodata,"a"

palette_init_words:
    .word 0x0000,0x000E,0x00E0,0x0E00,0x00EE,0x0E0E,0x0EE0,0x020C
    .word 0x0022,0x0046,0x006A,0x008C,0x00A2,0x00C6,0x00EA,0x002E
    .word 0x0200,0x0400,0x0600,0x0800,0x0A00,0x0C00,0x0E00,0x0C20
    .word 0x0202,0x0404,0x0606,0x0808,0x0A0A,0x0C0C,0x0E0C,0x0C0E
    .word 0x0002,0x0004,0x0006,0x0008,0x000A,0x000C,0x000E,0x020A
    .word 0x0220,0x0440,0x0660,0x0880,0x0AA0,0x0CC0,0x0EE0,0x0AC2
    .word 0x0020,0x0040,0x0060,0x0080,0x00A0,0x00C0,0x00E0,0x0A20
    .word 0x0204,0x0406,0x0608,0x080A,0x0A0C,0x0C0A,0x0E08,0x0C06

tile_init_words:
    .rept 16
    .word 0x1111
    .endr
    .rept 16
    .word 0x2222
    .endr
    .rept 8
    .word 0x3030
    .word 0x0303
    .endr

    .align 2
genesistan_pc080sn_tile_vram_lut:
    .incbin "../../build/pc080sn_tile_vram_lut.bin"

    .align 2
genesistan_pc080sn_attr_lut:
    .incbin "../../build/pc080sn_attr_lut.bin"

    .align 2
genesistan_pc080sn_tile_rom:
    .incbin "../../build/regions/pc080sn.bin"

    .align 2
genesistan_scene_preload_title:
    .incbin "../../build/pc080sn_scene_preload_title.bin"
genesistan_scene_preload_title_end:

    .align 2
genesistan_scene_preload_gameplay:
    .incbin "../../build/pc080sn_scene_preload_gameplay.bin"
genesistan_scene_preload_gameplay_end:

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

frame_counter:
    .word 0
tick_counter:
    .word 0

palette_dirty:
    .byte 0
tiles_dirty:
    .byte 0
    .align 2
bg_row_dirty:
    .long 0
fg_row_dirty:
    .long 0
    .align 2
genesistan_current_scene_id:
    .byte 0
    .align 2
genesistan_scene_a0_lo:
    .long 0
genesistan_scene_a0_hi:
    .long 0
genesistan_shadow_input_390001:
    .byte 0
genesistan_shadow_input_390003:
    .byte 0
genesistan_shadow_input_390005:
    .byte 0
genesistan_shadow_input_390007:
    .byte 0
prev_coin_p1_a_pressed:
    .byte 0
genesistan_shadow_dip1:
    .byte 0
genesistan_shadow_dip2:
    .byte 0

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
