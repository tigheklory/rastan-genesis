    .section .text,"ax"

    .global genesistan_hook_tilemap_plane_a
    .global genesistan_hook_tilemap_fg
    .global genesistan_hook_cwindow_clear
    .global genesistan_hook_tilemap_bg_fill
    .global genesistan_hook_tilemap_fg_fill
    .global genesistan_hook_inline_fg_write_3a550
    .global genesistan_hook_inline_fg_write_3a8fe
    .global genesistan_hook_inline_fg_write_3a908
    .global genesistan_hook_inline_fg_write_3acea
    .global genesistan_hook_pc080sn_bg_scroll_fill
    .global genesistan_hook_pc080sn_fg_scroll_fill
    .global genesistan_hook_tilemap_bg_blockcopy
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
    .global genesistan_hook_glyph_renderer_3bd48
    .global genesistan_hook_highscore_fg_producer
    .global genesistan_hook_textwriter_dispatch
    .global genesistan_hook_pc080sn_descriptor_rebuild
    .global rastan_direct_update_inputs

    .global genesistan_shadow_input_390001
    .global genesistan_shadow_input_390003
    .global genesistan_shadow_input_390005
    .global genesistan_shadow_input_390007
    .global genesistan_shadow_dip1
    .global genesistan_shadow_dip2

    .equ IO_PAD1_DATA,          0x00A10003
    .equ IO_PAD2_DATA,          0x00A10005
    .equ IO_PAD1_CTRL,          0x00A10009
    .equ IO_PAD2_CTRL,          0x00A1000B

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
    .equ ARCADE_HIGHSCORE_SOURCE_BASE,       0x00FF0000
    .equ PC080SN_DESC_REBUILD_SRC_TABLE,      0x00FF1000
    .equ PC080SN_DESC_REBUILD_PTR_TABLE,      0x00FF1040
    .equ PC080SN_DESC_REBUILD_WORD_TABLE,     0x00FF1080
    .equ PC080SN_DESC_REBUILD_OUT,            0x00FF10A8
    .equ PC080SN_DESC_ARCADE_START,           0x00000F08
    .equ PC080SN_DESC_ARCADE_END,             0x0003A00C
    .equ PC080SN_DESC_GENESIS_START,          0x00001108
    .equ PC080SN_DESC_SECOND_WORD_BASE,       0x00000200
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

genesistan_hook_tilemap_fg_fill:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    movea.l %a0, %a4
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
    blo     .Lfg_fill_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lfg_fill_done

    move.w  %d1, %d6
    tst.w   %d6
    beq     .Lfg_fill_done

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_fg_buffer, %a6

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

.Lfg_fill_loop:
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lfg_fill_done

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
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

    move.l  fg_row_dirty, %d0
    bset    %d5, %d0
    move.l  %d0, fg_row_dirty

    adda.l  #4, %a4
    subq.w  #1, %d6
    bne.s   .Lfg_fill_loop

.Lfg_fill_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_inline_fg_write_3a550:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08A50, %a0
    move.l  #0x00000032, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_inline_fg_write_3a8fe:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08E78, %a0
    move.l  #0x00002744, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_inline_fg_write_3a908:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08E64, %a0
    move.l  #0x00002744, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_inline_fg_write_3acea:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C09170, %a0
    move.l  #0x00002749, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_highscore_fg_producer:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  %d0, %d2
    andi.w  #0x007F, %d0
    move.w  %d0, %d5
    mulu.w  #6, %d0

    lea     0x0003C654, %a0
    adda.w  %d0, %a0
    move.w  (%a0), %d3
    beq.s   .Lhighscore_done

    movea.w 2(%a0), %a1
    adda.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %a1
    movea.w 4(%a0), %a2
    adda.l  #ARCADE_HIGHSCORE_SOURCE_BASE, %a2

.Lhighscore_cell_loop:
    clr.w   %d4
    move.b  (%a2)+, %d4
    move.w  %d4, %d0

    cmpi.b  #0x3F, %d4
    bne.s   .Lhighscore_check_bang
    move.w  #0x274B, %d0
    bra.s   .Lhighscore_apply_mode

.Lhighscore_check_bang:
    cmpi.b  #0x21, %d4
    bne.s   .Lhighscore_apply_mode
    move.w  #0x2744, %d0

.Lhighscore_apply_mode:
    tst.b   %d2
    bpl.s   .Lhighscore_stage_cell
    move.w  #0x0020, %d0

.Lhighscore_stage_cell:
    movea.l %a1, %a0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill

    adda.w  #4, %a1
    subq.w  #1, %d3
    bne.s   .Lhighscore_cell_loop

.Lhighscore_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_tilemap_bg_blockcopy:
    movem.l %d3/%d5-%d7/%a3-%a6, -(%sp)

    move.w  %d0, %d4
    movea.l %a1, %a2

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a4
    lea     staged_bg_buffer, %a6

.Lbg_blockcopy_row_loop:
    move.w  %d4, %d0

.Lbg_blockcopy_cell_loop:
    move.l  %a1, %d6
    andi.l  #0x00FFFFFF, %d6
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d6
    blo     .Lbg_blockcopy_consume_cell
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d6
    bhs     .Lbg_blockcopy_consume_cell

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d6
    lsr.l   #2, %d6

    move.w  %a0@, %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a3,%d3.w), %d5

    move.w  %d2, %d3
    andi.w  #0x0003, %d3

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #6, %d7
    andi.w  #0x0001, %d7
    lsl.w   #2, %d7
    or.w    %d7, %d3

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #7, %d7
    andi.w  #0x0001, %d7
    lsl.w   #3, %d7
    or.w    %d7, %d3

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #5, %d7
    andi.w  #0x0001, %d7
    lsl.w   #4, %d7
    or.w    %d7, %d3

    add.w   %d3, %d3
    move.w  0(%a4,%d3.w), %d3
    or.w    %d3, %d5

    move.w  %d6, %d7
    andi.w  #0x003F, %d7
    move.w  %d6, %d3
    lsr.w   #6, %d3
    andi.w  #0x001F, %d3

    move.w  %d3, %d6
    lsl.w   #7, %d6
    add.w   %d7, %d6
    add.w   %d7, %d6
    move.w  %d5, 0(%a6,%d6.w)

    move.l  bg_row_dirty, %d5
    bset    %d3, %d5
    move.l  %d5, bg_row_dirty

.Lbg_blockcopy_consume_cell:
    addq.l  #2, %a0
    addq.l  #4, %a1
    subq.w  #1, %d0
    cmpi.w  #0, %d0
    bne     .Lbg_blockcopy_cell_loop

    adda.l  #0x00000100, %a2
    movea.l %a2, %a1
    move.w  %d4, %d0
    subq.w  #1, %d1
    cmpi.w  #0, %d1
    bne     .Lbg_blockcopy_row_loop

    movem.l (%sp)+, %d3/%d5-%d7/%a3-%a6
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
    move.w  %d7, -(%sp)
    bsr     .Ltw_translate_attr

    move.w  (%sp)+, %d1
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

genesistan_hook_glyph_renderer_3bd48:
    move.w  %d0, %d1
    andi.w  #0x007F, %d0
    lsl.w   #2, %d0
    movea.l #0x0003BD7C, %a0
    adda.w  %d0, %a0
    movea.l (%a0), %a0
    movea.l (%a0)+, %a1
    move.w  (%a0)+, %d2
    tst.b   %d1
    bmi.s   .Lgr_space_mode

.Lgr_glyph_loop:
    move.b  (%a0)+, %d0
    beq.s   .Lgr_done
    ext.w   %d0
    move.w  %d0, %d3
    bsr     .Lgr_store_cell
    bra.s   .Lgr_glyph_loop

.Lgr_space_mode:
    move.w  #0x0020, %d1
.Lgr_space_loop:
    move.b  (%a0)+, %d0
    beq.s   .Lgr_done
    move.w  %d1, %d3
    bsr     .Lgr_store_cell
    bra.s   .Lgr_space_loop

.Lgr_done:
    rts

.Lgr_store_cell:
    movem.l %d0-%d7/%a2-%a6, -(%sp)

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    movea.l %a1, %a2
    adda.w  #2, %a2
    move.w  %d3, %d0
    bsr     .Ltw_store_from_components_at_a2

    movem.l (%sp)+, %d0-%d7/%a2-%a6
    adda.w  #4, %a1
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

/* PC080SN per-line scroll-RAM fill/clear translation homes.
 * IN: A0 = arcade target, D0 = fill word, D1 = word count.
 * These preserve the arcade operands for a future per-line scroll translation
 * (Genesis HSCROLL table, or uniform clear folded into staged full-plane scroll).
 * Under the current KF-015 full-plane model there is no visible per-line output,
 * and these handlers must not raw-write the PC080SN/VDP mirror space.
 */
genesistan_hook_pc080sn_bg_scroll_fill:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_pc080sn_fg_scroll_fill:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts


    .section .text.zzz_textwriter_dispatch,"ax"

/* Shared PC080SN text writer replacement for runtime 0x0565A6.
 * Replays the arcade source loop but routes each composed cell through
 * BG/FG staging instead of writing raw PC080SN words into Genesis VDP space. */
genesistan_hook_textwriter_dispatch:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    movea.l %a0, %a3
    movea.l %a1, %a2
    move.w  %d1, %d3

.Ltw_dispatch_loop:
    clr.w   %d0
    move.b  (%a3)+, %d0
    cmpi.b  #0x00, %d0
    beq.s   .Ltw_dispatch_done
    cmpi.b  #0xFF, %d0
    beq.s   .Ltw_dispatch_advance

    jsr     0x000565CE

    move.w  %d3, %d4
    swap    %d4
    move.w  %d0, %d4

    move.l  %a1, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2
    blo.s   .Ltw_dispatch_check_fg
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs.s   .Ltw_dispatch_check_fg

    movea.l %a1, %a0
    move.l  %d4, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_bg_fill
    adda.l  #4, %a1
    bra.s   .Ltw_dispatch_loop

.Ltw_dispatch_check_fg:
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
    blo.s   .Ltw_dispatch_fail
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs.s   .Ltw_dispatch_fail

    movea.l %a1, %a0
    move.l  %d4, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    adda.l  #4, %a1
    bra.s   .Ltw_dispatch_loop

.Ltw_dispatch_advance:
    adda.l  #0x200, %a2
    movea.l %a2, %a1
    bra.s   .Ltw_dispatch_loop

.Ltw_dispatch_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Ltw_dispatch_fail:
    move.l  64(%sp), %d0
    move.l  %d0, audit_guard_caller_pc
    lea     audit_guard_register_snapshot, %a0
    move.l  %a1, (%a0)+
    move.l  %d2, (%a0)+
    move.l  %d4, (%a0)+
    move.w  0x00C00008, audit_guard_vcount
    move.w  #0x565A, audit_guard_fired_flag

.Ltw_dispatch_fail_loop:
    move.b  audit_guard_heartbeat, %d0
    addq.b  #1, %d0
    move.b  %d0, audit_guard_heartbeat
    bra.s   .Ltw_dispatch_fail_loop


    .section .text.zzz_pc080sn_descriptor_rebuild,"ax"

/* Rebuilds the PC080SN descriptor pointer table at runtime 0x055B04.
 * Source pointers in 0x00FF1000 remain arcade addresses because the table is
 * runtime-built in mapped WRAM; relocate each dereference through the JSON
 * arcade_copy segment before reading descriptor words from Genesis ROM.
 */
genesistan_hook_pc080sn_descriptor_rebuild:
    movea.l #PC080SN_DESC_REBUILD_SRC_TABLE, %a0
    movea.l #PC080SN_DESC_REBUILD_PTR_TABLE, %a1
    movea.l #PC080SN_DESC_REBUILD_WORD_TABLE, %a2
    moveq   #16, %d0

.Lpc080sn_desc_loop:
    movea.l (%a0), %a4
    cmpa.l  #PC080SN_DESC_ARCADE_START, %a4
    blo.s   .Lpc080sn_desc_bad_ptr
    cmpa.l  #PC080SN_DESC_ARCADE_END, %a4
    bhs.s   .Lpc080sn_desc_bad_ptr

    suba.l  #PC080SN_DESC_ARCADE_START, %a4
    adda.l  #PC080SN_DESC_GENESIS_START, %a4

    move.w  (%a4), (%a2)+
    clr.l   %d1
    move.w  2(%a4), %d1
    movea.l #PC080SN_DESC_SECOND_WORD_BASE, %a4
    lea     0(%a4,%d1.l), %a4
    move.l  %a4, (%a1)+

    adda.l  #4, %a0
    subq.w  #1, %d0
    bne.s   .Lpc080sn_desc_loop

    movea.l 4294(%a5), %a4
    clr.w   %d0
    move.b  (%a4), %d0
    move.w  %d0, PC080SN_DESC_REBUILD_OUT
    rts

.Lpc080sn_desc_bad_ptr:
    trap    #0


    .section .bss
    .align 2

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
