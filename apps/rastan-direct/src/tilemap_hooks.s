    .section .text,"ax"

    .global genesistan_hook_tilemap_plane_a
    .global genesistan_hook_tilemap_plane_a_selector0_native
    .global genesistan_hook_tilemap_plane_a_selector12_native
    .global genesistan_plane_a_pan_publish_entering_rows_up
    .global genesistan_plane_a_pan_publish_entering_rows_down
    .global genesistan_hook_tilemap_fg
    .global genesistan_hook_cwindow_clear
    .global genesistan_hook_tilemap_bg_fill
    .global genesistan_hook_tilemap_bg_fill_tall
    .global genesistan_hook_tilemap_fg_fill
    .global genesistan_hook_tilemap_fg_fill_tall
    .global genesistan_hook_inline_fg_write_3a550
    .global genesistan_hook_inline_fg_write_3a8fe
    .global genesistan_hook_inline_fg_write_3a908
    .global genesistan_hook_inline_fg_write_3a92a
    .global genesistan_hook_inline_fg_write_3acea
    .global genesistan_hook_inline_fg_write_3d04c
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
    .global genesistan_hook_itempage_strip_populate
    .global genesistan_hook_itempage_strip_blit
    .global vdp_commit_fg_narrow_strips
    .global rastan_direct_update_inputs

    .extern vdp_set_reg
    .extern vdp_set_vram_write_addr
    .extern vdp_commit_fg_strips_if_dirty
    .extern genesistan_current_scene_id
    .extern genesistan_current_pc080sn_tileset_id
    .extern fg_native_gameplay_owner
    .extern palette_route_lookup

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
    .equ ARCADE_PC080SN_SELECTOR_OFFSET,     0x10A8
    .equ ARCADE_PC080SN_SCROLL_X_FG_OFFSET,  0x10AE
    .equ ARCADE_PC080SN_SCROLL_Y_FG_OFFSET,  0x10B0
    .equ ARCADE_PC080SN_SCROLL_X_BG_OFFSET,  0x10EC
    .equ ARCADE_PC080SN_SCROLL_Y_BG_OFFSET,  0x10EE
    .equ ARCADE_PC080SN_BG_GROUP_OFFSET,     0x10F4
    .equ ARCADE_PC080SN_BG_SUBCOL_OFFSET,    0x10F6
    .equ ARCADE_PC080SN_BG_WALKER_OFFSET,    0x10FC
    .equ ARCADE_PC080SN_BG_TABLE_INDEX_OFFSET, 0x1386
    .equ ARCADE_PC080SN_SCROLL_Y_ACCUM_OFFSET, 0x10BA
    .equ ARCADE_PC080SN_STRIP_INDEX_OFFSET,  0x10CA
    .equ ARCADE_PC080SN_STRIP_INDEX_FG_OFFSET, 0x10CA
    .equ ARCADE_PC080SN_STRIP_GROUP_OFFSET,  0x10CC
    .equ ARCADE_PC080SN_SCROLL_Y_DELTA_OFFSET, 0x10DA
    .equ ARCADE_PC080SN_CWINDOW_BASE_BG,     0x00C00000
    .equ ARCADE_PC080SN_CWINDOW_BASE_FG,     0x00C08000
    .equ ARCADE_PC080SN_CWINDOW_BYTES,       0x00004000
    .equ ARCADE_COLLISION_MAP_BASE,          0x00FF1E00
    /* Build 0215 / OPEN-017: Stage 1 FG plane replay (proven deterministic ROM model).
     * The live FG boundary is genesistan_hook_tilemap_fg (0x703EA), reached per-column from
     * the Stage 1 setup loop (0x50634); its native slot a5@0x10A4 is out of range so it bails,
     * while the real FG column dest is a5@0x10A0 = 0xC08000 + dcol*4 (mod plane). For each
     * cell: PTR[seg] comes from the arcade-owned rebuilt pointer table at 0x00FF1040;
     * code = ROM_word(PTR[seg] + colidx*2 + row*8), with colidx from a5@0x10CA.
     * Arcade attr/color bank 0x0003 is carried in Genesis CRAM line 1. */
    .equ FG_PLANE_ATTR_HI,                   0x00010000
    .equ FG_PRODUCER_SEG_COUNT,              16  /* 64 rows; gameplay FG now preserves rows 0-63 in staged_fg_tall_buffer. */
    .equ FG_PRODUCER_ROW_COUNT,              4
    .equ ARCADE_MAINCPU_ROM_BASE,            0x00000200
    .equ ARCADE_HIGHSCORE_SOURCE_BASE,       0x00FF0000
    /* Arcade A5 work-RAM base (KF-039).  The number-renderer descriptors store
     * absolute arcade work-RAM pointers (0x0010Cxxx); the mapped Genesis address
     * is a5(0x00FF0000) + (pointer - ARCADE_WORKRAM_A5_BASE).  Build 0150 fix:
     * the source was masked with 0x0000FFFF (keeping the 0xC000 A5-base bits),
     * so it read 0x00FFCxxx (all zero) -> SCORE/ROUND rendered as 0. */
    .equ ARCADE_WORKRAM_A5_BASE,             0x0010C000
    .equ PC080SN_DESC_REBUILD_SRC_TABLE,      0x00FF1000
    .equ PC080SN_DESC_REBUILD_PTR_TABLE,      0x00FF1040
    .equ PC080SN_DESC_REBUILD_WORD_TABLE,     0x00FF1080
    .equ PC080SN_DESC_REBUILD_OUT,            0x00FF10A8
    .equ PC080SN_ITEMPAGE_STRIP_COL_SLOT,     0x00FF10F6
    .equ PC080SN_ITEMPAGE_DEST_CURSOR_SLOT,   0x00FF10F8
    .equ PC080SN_ITEMPAGE_WALKER_SLOT,        0x00FF10FC
    .equ PC080SN_ITEMPAGE_STRIP_PTR_SLOT,     0x00FF1100
    .equ PC080SN_ITEMPAGE_STRIP_WORD_SLOT,    0x00FF1104
    /* Build 0217 / OPEN-017 / KF-041: producer-source gameplay scene identity.
     * The live Stage 1 BG producer reads its tile-column source from relocated
     * outdoor+cave blocks [0xD31C, 0x10B1C) (arcade 0xD11C..0x1011C source bases
     * plus the mapped copy delta), walked from arcade descriptor table 0x3951C.
     * A strip source inside this range identifies the gameplay scene; SCENE_GAMEPLAY_ID
     * matches the load_scene_tiles / genesistan_scene_a0_ranges gameplay index (1). */
    .equ GAMEPLAY_STRIP_SRC_LO,               0x0000D31C
    .equ GAMEPLAY_STRIP_SRC_CAVE_LO,          0x0000FB1C
    .equ GAMEPLAY_STRIP_SRC_HI,               0x00010B1C
    .equ SCENE_GAMEPLAY_ID,                   1
    .equ SCENE_GAMEPLAY_CAVE_TILESET_ID,      3
    .equ PLANE_A_NATIVE_OWNER_PC080SN_FG,     2
    .equ PC080SN_DESC_ARCADE_START,           0x00000F08
    .equ PC080SN_DESC_ARCADE_END,             0x0003A00C
    .equ PC080SN_DESC_GENESIS_START,          0x00001108
    .equ PC080SN_DESC_SECOND_WORD_BASE,       0x00000200
    .equ PLANE_B_DESC_TABLE_ARCADE_BASE,      0x0003951C
    .equ FG_NARROW_CAP,                       64
    .equ VDP_DATA,                            0x00C00000
    .equ VDP_REG_AUTOINC,                     15
    .equ VRAM_PLANE_A_BASE,                   0x0000E000
    .equ PLANE_A_PAN_UP_CONTINUATION,         0x00055998
    .equ PLANE_A_PAN_DOWN_CONTINUATION,       0x0005590C

/* Convert a native gameplay Plane A descriptor word into Genesis nametable
 * attribute bits.  The arcade semantic bank is the full PC080SN color bank, not
 * just low bits 0-1; route it through the established palette owner table so
 * Stage-1 FG bank 3 uses the carrier CRAM line already maintained by VBlank.
 *
 * in:  D0.W = PC080SN descriptor/attribute word
 * out: D0.W = Genesis nametable attribute bits (palette + proven H/V flip)
 * clobbers internally, but preserves D1-D3/A0 for producer loops
 */
.Lplane_a_native_attr_from_word:
    movem.l %d1-%d3/%a0, -(%sp)
    move.w  %d0, -(%sp)

    move.w  %d0, %d2
    andi.w  #0x01FF, %d2                /* full arcade PC080SN color bank */
    moveq   #SCENE_GAMEPLAY_ID, %d0
    moveq   #PLANE_A_NATIVE_OWNER_PC080SN_FG, %d1
    bsr     palette_route_lookup         /* d0 = line or -1; d3 = flags */
    tst.l   %d0
    bpl.s   .Lplane_a_native_attr_line_ready
    move.w  %d2, %d0                     /* conservative legacy fallback */
    andi.w  #0x0003, %d0
.Lplane_a_native_attr_line_ready:
    andi.w  #0x0003, %d0
    lsl.w   #8, %d0
    lsl.w   #5, %d0                      /* Genesis palette line bits 14:13 */

    move.w  (%sp), %d1
    btst    #14, %d1                     /* PC080SN H flip */
    beq.s   .Lplane_a_native_attr_no_h
    ori.w   #0x0800, %d0
.Lplane_a_native_attr_no_h:
    btst    #15, %d1                     /* PC080SN V flip */
    beq.s   .Lplane_a_native_attr_no_v
    ori.w   #0x1000, %d0
.Lplane_a_native_attr_no_v:
    addq.w  #2, %sp
    movem.l (%sp)+, %d1-%d3/%a0
    rts

/* Native gameplay Plane B uses the existing BG attr LUT path: the Rastan
 * semantic descriptor word is converted directly to final Genesis nametable
 * attribute bits without consulting PC080SN C-window/name-RAM state.
 *
 * in:  D0.W = PC080SN descriptor/attribute word
 * out: D0.W = Genesis nametable attribute bits
 */
.Lplane_b_native_attr_from_word:
    movem.l %d1-%d2/%a0, -(%sp)

    move.w  %d0, %d1
    andi.w  #0x0003, %d1

    move.w  %d0, %d2
    lsr.w   #8, %d2
    lsr.w   #6, %d2
    andi.w  #0x0001, %d2
    lsl.w   #2, %d2
    or.w    %d2, %d1

    move.w  %d0, %d2
    lsr.w   #8, %d2
    lsr.w   #7, %d2
    andi.w  #0x0001, %d2
    lsl.w   #3, %d2
    or.w    %d2, %d1

    move.w  %d0, %d2
    lsr.w   #8, %d2
    lsr.w   #5, %d2
    andi.w  #0x0001, %d2
    lsl.w   #4, %d2
    or.w    %d2, %d1

    add.w   %d1, %d1
    lea     genesistan_pc080sn_attr_lut, %a0
    move.w  0(%a0,%d1.w), %d0

    movem.l (%sp)+, %d1-%d2/%a0
    rts

genesistan_hook_tilemap_plane_a_selector0_native:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    suba.w  #16, %sp

    lea     0x00FF0000, %a5
    move.b  #1, fg_native_gameplay_owner

    moveq   #0, %d0
    move.w  ARCADE_PC080SN_STRIP_GROUP_OFFSET(%a5), %d0
    andi.w  #0x000F, %d0
    lsl.w   #2, %d0
    moveq   #0, %d1
    move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d1
    andi.w  #0x0003, %d1
    add.w   %d1, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, 0(%sp)             /* logical column */
    add.w   %d1, %d1
    move.w  %d1, 4(%sp)             /* source subcolumn offset */

    move.w  staged_scroll_y_fg, %d0
    neg.w   %d0
    addq.w  #8, %d0
    andi.w  #0x01FF, %d0
    lsr.w   #3, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, 2(%sp)             /* visible top logical row */

    lea     PC080SN_DESC_REBUILD_PTR_TABLE, %a3
    lea     PC080SN_DESC_REBUILD_WORD_TABLE, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     staged_fg_buffer, %a6

    moveq   #0, %d4                 /* descriptor segment */
.Lplane_a_sel0_segment_loop:
    move.l  (%a3)+, %d6
    move.w  (%a1)+, %d7
    btst    #0, %d6
    bne     .Lplane_a_sel0_next_segment
    cmpi.l  #0x00000200, %d6
    blo     .Lplane_a_sel0_next_segment
    cmpi.l  #0x0005FFFC, %d6
    bhi     .Lplane_a_sel0_next_segment
    move.w  %d7, %d0
    bsr     .Lplane_a_native_attr_from_word
    move.w  %d0, 6(%sp)             /* final Plane A attribute bits */
    movea.l %d6, %a0

    moveq   #0, %d5                 /* cell inside this segment */
.Lplane_a_sel0_cell_loop:
    move.w  %d5, %d0
    lsl.w   #3, %d0
    add.w   4(%sp), %d0

    cmpi.w  #0x00FF, 32(%a0)
    beq.s   .Lplane_a_sel0_collision_alt
    move.w  20(%a0,%d0.w), %d2
    bra.s   .Lplane_a_sel0_collision_ready
.Lplane_a_sel0_collision_alt:
    move.w  34(%a0), %d2
.Lplane_a_sel0_collision_ready:
    move.w  %d4, %d1
    lsl.w   #2, %d1
    add.w   %d5, %d1
    move.w  %d1, %d3
    lsl.w   #6, %d3
    add.w   0(%sp), %d3
    add.w   %d3, %d3
    /* 68000 indexed addressing only has an 8-bit displacement.  Use an
     * explicit collision-map base so high logical rows cannot wrap into
     * the descriptor rebuild/source table at 0xFF1000. */
    movea.l #ARCADE_COLLISION_MAP_BASE, %a6
    move.w  %d2, 0(%a6,%d3.w)
    lea     staged_fg_buffer, %a6

    move.w  0(%a0,%d0.w), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    6(%sp), %d3

    move.w  %d1, %d0
    sub.w   2(%sp), %d0
    andi.w  #0x003F, %d0
    cmpi.w  #32, %d0
    bhs.s   .Lplane_a_sel0_not_resident

    move.w  %d1, %d0
    andi.w  #0x001F, %d0
    move.w  %d0, %d2
    lsl.w   #7, %d2
    add.w   0(%sp), %d2
    add.w   0(%sp), %d2
    move.w  %d3, 0(%a6,%d2.w)
    move.l  fg_row_dirty, %d2
    bset    %d0, %d2
    move.l  %d2, fg_row_dirty

.Lplane_a_sel0_not_resident:
    addq.w  #1, %d5
    cmpi.w  #4, %d5
    blo.w   .Lplane_a_sel0_cell_loop

.Lplane_a_sel0_next_segment:
    addq.w  #1, %d4
    cmpi.w  #16, %d4
    blo     .Lplane_a_sel0_segment_loop

    adda.w  #16, %sp
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_tilemap_plane_a_selector12_native:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    suba.w  #16, %sp

    lea     0x00FF0000, %a5
    move.b  #1, fg_native_gameplay_owner
    move.w  #1, 0x1330(%a5)

    moveq   #0, %d1
    move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d1
    andi.w  #0x0003, %d1
    cmpi.w  #2, ARCADE_PC080SN_SELECTOR_OFFSET(%a5)
    beq.s   .Lplane_a_sel12_row_ready
    not.w   %d1
    andi.w  #0x0003, %d1
.Lplane_a_sel12_row_ready:
    move.w  %d1, %d0
    lsl.w   #3, %d0
    move.w  %d0, 4(%sp)             /* source row byte offset */

    moveq   #0, %d0
    move.w  ARCADE_PC080SN_STRIP_GROUP_OFFSET(%a5), %d0
    andi.w  #0x000F, %d0
    lsl.w   #2, %d0
    add.w   %d1, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, 0(%sp)             /* logical row */

    move.w  staged_scroll_y_fg, %d0
    neg.w   %d0
    addq.w  #8, %d0
    andi.w  #0x01FF, %d0
    lsr.w   #3, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, 2(%sp)             /* visible top logical row */

    lea     PC080SN_DESC_REBUILD_PTR_TABLE, %a3
    lea     PC080SN_DESC_REBUILD_WORD_TABLE, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     staged_fg_buffer, %a6

    moveq   #0, %d4                 /* descriptor segment */
.Lplane_a_sel12_segment_loop:
    move.l  (%a3)+, %d6
    move.w  (%a1)+, %d7
    btst    #0, %d6
    bne     .Lplane_a_sel12_next_segment
    cmpi.l  #0x00000200, %d6
    blo     .Lplane_a_sel12_next_segment
    cmpi.l  #0x0005FFFC, %d6
    bhi     .Lplane_a_sel12_next_segment
    move.w  %d7, %d0
    bsr     .Lplane_a_native_attr_from_word
    move.w  %d0, 6(%sp)             /* final Plane A attribute bits */
    movea.l %d6, %a0

    moveq   #0, %d5                 /* cell inside this segment */
.Lplane_a_sel12_cell_loop:
    move.w  %d5, %d0
    add.w   %d0, %d0
    add.w   4(%sp), %d0

    cmpi.w  #0x00FF, 32(%a0)
    beq.s   .Lplane_a_sel12_collision_alt
    move.w  20(%a0,%d0.w), %d2
    bra.s   .Lplane_a_sel12_collision_ready
.Lplane_a_sel12_collision_alt:
    move.w  34(%a0), %d2
.Lplane_a_sel12_collision_ready:
    move.w  %d4, %d1
    lsl.w   #2, %d1
    add.w   %d5, %d1                /* logical column */
    move.w  0(%sp), %d3
    lsl.w   #6, %d3
    add.w   %d1, %d3
    add.w   %d3, %d3
    movea.l #ARCADE_COLLISION_MAP_BASE, %a6
    move.w  %d2, 0(%a6,%d3.w)
    lea     staged_fg_buffer, %a6

    move.w  0(%a0,%d0.w), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    6(%sp), %d3

    move.w  0(%sp), %d0
    sub.w   2(%sp), %d0
    andi.w  #0x003F, %d0
    cmpi.w  #32, %d0
    bhs.s   .Lplane_a_sel12_not_resident

    move.w  0(%sp), %d0
    andi.w  #0x001F, %d0
    move.w  %d0, %d2
    lsl.w   #7, %d2
    add.w   %d1, %d2
    add.w   %d1, %d2
    move.w  %d3, 0(%a6,%d2.w)
    move.l  fg_row_dirty, %d2
    bset    %d0, %d2
    move.l  %d2, fg_row_dirty

.Lplane_a_sel12_not_resident:
    addq.w  #1, %d5
    cmpi.w  #4, %d5
    blo.w   .Lplane_a_sel12_cell_loop

.Lplane_a_sel12_next_segment:
    addq.w  #1, %d4
    cmpi.w  #16, %d4
    blo     .Lplane_a_sel12_segment_loop

    adda.w  #16, %sp
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* Native Plane A no-publication vertical-scroll route.
 *
 * The arcade no-publish arms update camera Y without invoking the normal row
 * publisher.  These byte-neutral hook targets reproduce the displaced 10BA
 * bookkeeping, derive the old/new visible top from arcade-owned 10B0, publish
 * every entering logical row through the semantic ROM row formula, then jump
 * back to the original scroll-store tail where arcade code writes 10B0.
 *
 * No C08000/name-RAM image, tall FG buffer, projection path, or collision write
 * is used here.
 */
genesistan_plane_a_pan_publish_entering_rows_up:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.w  ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5), %d6
    move.w  ARCADE_PC080SN_SCROLL_Y_DELTA_OFFSET(%a5), %d7
    sub.w   %d7, ARCADE_PC080SN_SCROLL_Y_ACCUM_OFFSET(%a5)

    move.w  %d6, %d0
    bsr     .Lplane_a_visible_top_from_scroll_d0
    move.w  %d0, %d4                         /* old visible_top */

    move.w  %d6, %d0
    sub.w   %d7, %d0
    andi.w  #0x01FF, %d0
    bsr     .Lplane_a_visible_top_from_scroll_d0
    move.w  %d0, %d5                         /* new visible_top */

.Lplane_a_pan_up_loop:
    cmp.w   %d5, %d4
    beq.s   .Lplane_a_pan_up_done
    addq.w  #1, %d4
    andi.w  #0x003F, %d4
    move.w  %d4, %d0
    addi.w  #31, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, %d3
    bsr     .Lplane_a_publish_logical_row_native
    move.w  %d3, %d0
    bsr     .Lplane_b_publish_logical_row_native
    bra.s   .Lplane_a_pan_up_loop

.Lplane_a_pan_up_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    jmp     PLANE_A_PAN_UP_CONTINUATION

genesistan_plane_a_pan_publish_entering_rows_down:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.w  ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5), %d6
    move.w  ARCADE_PC080SN_SCROLL_Y_DELTA_OFFSET(%a5), %d7
    add.w   %d7, ARCADE_PC080SN_SCROLL_Y_ACCUM_OFFSET(%a5)

    move.w  %d6, %d0
    bsr     .Lplane_a_visible_top_from_scroll_d0
    move.w  %d0, %d4                         /* old visible_top */

    move.w  %d6, %d0
    add.w   %d7, %d0
    andi.w  #0x01FF, %d0
    bsr     .Lplane_a_visible_top_from_scroll_d0
    move.w  %d0, %d5                         /* new visible_top */

.Lplane_a_pan_down_loop:
    cmp.w   %d5, %d4
    beq.s   .Lplane_a_pan_down_done
    subq.w  #1, %d4
    andi.w  #0x003F, %d4
    move.w  %d4, %d0
    move.w  %d0, %d3
    bsr     .Lplane_a_publish_logical_row_native
    move.w  %d3, %d0
    bsr     .Lplane_b_publish_logical_row_native
    bra.s   .Lplane_a_pan_down_loop

.Lplane_a_pan_down_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    jmp     PLANE_A_PAN_DOWN_CONTINUATION

.Lplane_a_visible_top_from_scroll_d0:
    neg.w   %d0
    addq.w  #8, %d0
    andi.w  #0x01FF, %d0
    lsr.w   #3, %d0
    andi.w  #0x003F, %d0
    rts

/* in: D0.W = logical row 0..63
 * Uses the original Rastan map-source formula proven against the arcade
 * C08000 oracle, but emits only final Genesis Plane A staging words.
 */
.Lplane_a_publish_logical_row_native:
    movem.l %d1-%d7/%a0-%a6, -(%sp)
    suba.w  #16, %sp

    move.b  #1, fg_native_gameplay_owner

    andi.w  #0x003F, %d0
    move.w  %d0, 0(%sp)                      /* logical row */
    move.w  %d0, %d1
    andi.w  #0x001F, %d1
    move.w  %d1, 2(%sp)                      /* physical resident row */
    move.w  %d0, %d1
    lsr.w   #2, %d1
    andi.w  #0x000F, %d1
    move.w  %d1, 4(%sp)                      /* source row segment */
    move.w  %d0, %d1
    andi.w  #0x0003, %d1
    lsl.w   #3, %d1
    move.w  %d1, 6(%sp)                      /* source row byte offset */

    move.w  ARCADE_PC080SN_SCROLL_X_FG_OFFSET(%a5), %d0
    neg.w   %d0
    andi.w  #0x01FF, %d0
    lsr.w   #3, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, 8(%sp)                      /* X-scroll-derived source column base */

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     staged_fg_buffer, %a6
    moveq   #0, %d4                          /* logical destination column */

.Lplane_a_row_col_loop:
    move.w  %d4, %d0
    add.w   8(%sp), %d0
    andi.w  #0x003F, %d0                     /* source column */
    move.w  %d0, %d5
    andi.w  #0x0003, %d5
    add.w   %d5, %d5
    move.w  %d5, 10(%sp)                     /* source column byte offset */
    lsr.w   #2, %d0
    lsl.w   #2, %d0                          /* source group * 4 */

    move.w  4(%sp), %d1
    lsl.w   #2, %d1
    lea     .Lplane_a_strip_src_table, %a0
    movea.l 0(%a0,%d1.w), %a0
    adda.w  %d0, %a0                         /* descriptor entry E */

    cmpa.l  #PC080SN_DESC_ARCADE_START, %a0
    blo.s   .Lplane_a_row_blank_cell
    cmpa.l  #PC080SN_DESC_ARCADE_END, %a0
    bhs.s   .Lplane_a_row_blank_cell
    suba.l  #PC080SN_DESC_ARCADE_START, %a0
    adda.l  #PC080SN_DESC_GENESIS_START, %a0

    move.w  (%a0), %d7                       /* semantic attribute word */
    moveq   #0, %d6
    move.w  2(%a0), %d6                      /* semantic metatile descriptor pointer */
    btst    #0, %d6
    bne.s   .Lplane_a_row_blank_cell
    cmpi.l  #0x0005FDFC, %d6
    bhi.s   .Lplane_a_row_blank_cell

    movea.l #PC080SN_DESC_SECOND_WORD_BASE, %a0
    adda.l  %d6, %a0

    move.w  %d7, %d0
    bsr     .Lplane_a_native_attr_from_word
    move.w  %d0, 12(%sp)

    move.w  6(%sp), %d0
    add.w   10(%sp), %d0
    move.w  0(%a0,%d0.w), %d3
    andi.w  #0x3FFF, %d3
    bra.s   .Lplane_a_row_tile_ready

.Lplane_a_row_blank_cell:
    moveq   #0, %d3
    clr.w   12(%sp)

.Lplane_a_row_tile_ready:
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    12(%sp), %d3

    move.w  2(%sp), %d0
    lsl.w   #7, %d0
    move.w  %d4, %d1
    add.w   %d1, %d1
    add.w   %d1, %d0
    move.w  %d3, 0(%a6,%d0.w)

    addq.w  #1, %d4
    cmpi.w  #64, %d4
    blo.w   .Lplane_a_row_col_loop

    move.w  2(%sp), %d0
    move.l  fg_row_dirty, %d1
    bset    %d0, %d1
    move.l  %d1, fg_row_dirty

    adda.w  #16, %sp
    movem.l (%sp)+, %d1-%d7/%a0-%a6
    rts

    .align 2
.Lplane_a_strip_src_table:
    .long 0x0001691C, 0x00018BDC, 0x0001AE9C, 0x0001D15C
    .long 0x0001F41C, 0x000216DC, 0x0002399C, 0x00025C5C
    .long 0x00027F1C, 0x0002A1DC, 0x0002C49C, 0x0002E75C
    .long 0x00030A1C, 0x00032CDC, 0x00034F9C, 0x0003725C

/* in: D0.W = logical row 0..63
 * Publishes one full native gameplay Plane B row directly from the original
 * Rastan semantic BG descriptor table rooted at arcade ROM/data 0x03951C.
 * C00000 and a5@0x10F8 remain oracle-only and are not production inputs.
 */
.Lplane_b_publish_logical_row_native:
    movem.l %d1-%d7/%a0-%a6, -(%sp)
    suba.w  #18, %sp

    andi.w  #0x003F, %d0
    move.w  %d0, 0(%sp)                      /* logical row */
    move.w  %d0, %d1
    andi.w  #0x001F, %d1
    move.w  %d1, 2(%sp)                      /* physical resident row */
    move.w  %d0, %d1
    lsl.w   #5, %d1
    move.w  %d1, 4(%sp)                      /* row byte offset in descriptor block */

    moveq   #0, %d0
    move.w  ARCADE_PC080SN_BG_TABLE_INDEX_OFFSET(%a5), %d0
    andi.l  #0x0000FFFF, %d0
    move.l  %d0, %d1
    lsl.l   #3, %d0
    lsl.l   #2, %d1
    add.l   %d1, %d0
    addi.l  #PLANE_B_DESC_TABLE_ARCADE_BASE, %d0
    move.l  %d0, 8(%sp)                      /* base = 0x3951C + tm0idx*0x0C */

    move.l  ARCADE_PC080SN_BG_WALKER_OFFSET(%a5), %d0
    sub.l   8(%sp), %d0
    andi.l  #0x0000FFFF, %d0
    moveq   #6, %d1
    divu.w  %d1, %d0                         /* G_r = (10FC - base) / 6 */
    andi.l  #0x0000FFFF, %d0
    lsl.w   #4, %d0
    add.w   ARCADE_PC080SN_BG_SUBCOL_OFFSET(%a5), %d0
    move.w  %d0, 6(%sp)                      /* AR = G_r*16 + F6 */

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     staged_bg_buffer, %a6
    moveq   #0, %d4                          /* ring destination column C */

.Lplane_b_row_col_loop:
    move.w  6(%sp), %d0
    sub.w   %d4, %d0
    andi.w  #0x003F, %d0
    move.w  6(%sp), %d5
    sub.w   %d0, %d5                         /* absC = AR - ((AR-C)&63) */
    move.w  %d5, %d6
    lsr.w   #4, %d6                          /* source_group */

    move.w  %d6, %d0
    add.w   %d0, %d0                         /* group * 2 */
    lsl.w   #2, %d6                          /* group * 4 */
    add.w   %d0, %d6                         /* group * 6 */

    movea.l 8(%sp), %a0
    adda.w  %d6, %a0
    cmpa.l  #PC080SN_DESC_ARCADE_START, %a0
    blo.s   .Lplane_b_row_blank_cell
    cmpa.l  #PC080SN_DESC_ARCADE_END, %a0
    bhs.s   .Lplane_b_row_blank_cell
    suba.l  #PC080SN_DESC_ARCADE_START, %a0
    adda.l  #PC080SN_DESC_GENESIS_START, %a0

    move.w  (%a0), %d7                       /* semantic attribute word */
    move.l  2(%a0), %d6                      /* semantic tile-block pointer */
    btst    #0, %d6
    bne.s   .Lplane_b_row_blank_cell
    cmpi.l  #0x0005FDFC, %d6
    bhi.s   .Lplane_b_row_blank_cell

    addi.l  #PC080SN_DESC_SECOND_WORD_BASE, %d6
    movea.l %d6, %a0

    move.w  %d7, %d0
    bsr     .Lplane_b_native_attr_from_word
    move.w  %d0, 12(%sp)

    move.w  %d4, %d0
    andi.w  #0x000F, %d0                     /* source_subcol = C & 15 */
    add.w   %d0, %d0
    add.w   4(%sp), %d0
    move.w  0(%a0,%d0.w), %d3
    andi.w  #0x3FFF, %d3
    bra.s   .Lplane_b_row_tile_ready

.Lplane_b_row_blank_cell:
    moveq   #0, %d3
    clr.w   12(%sp)

.Lplane_b_row_tile_ready:
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    12(%sp), %d3

    move.w  2(%sp), %d0
    lsl.w   #7, %d0
    move.w  %d4, %d1
    add.w   %d1, %d1
    add.w   %d1, %d0
    move.w  %d3, 0(%a6,%d0.w)

    addq.w  #1, %d4
    cmpi.w  #64, %d4
    blo.w   .Lplane_b_row_col_loop

    move.w  2(%sp), %d0
    move.l  bg_row_dirty, %d1
    bset    %d0, %d1
    move.l  %d1, bg_row_dirty

    adda.w  #18, %sp
    movem.l (%sp)+, %d1-%d7/%a0-%a6
    rts

/* in: D0.L = source attr/tile word, D2.W = logical row from producer loop.
 * Gameplay strips publish only resident rows directly into the final Plane B
 * staging buffer; frontend/non-gameplay routes keep the legacy 32-row helper.
 */
.Lplane_b_stage_gameplay_producer_cell_native:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    suba.w  #8, %sp

    lea     0x00FF0000, %a5
    move.l  %d0, %d7                         /* source attr/tile word */

    move.w  %d2, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, 0(%sp)                      /* logical row */

    move.w  ARCADE_PC080SN_SCROLL_Y_BG_OFFSET(%a5), %d0
    bsr     .Lplane_a_visible_top_from_scroll_d0
    move.w  0(%sp), %d1
    sub.w   %d0, %d1
    andi.w  #0x003F, %d1                     /* resident_delta */
    cmpi.w  #32, %d1
    bhs.s   .Lplane_b_stage_cell_done

    move.w  0(%sp), %d1
    andi.w  #0x001F, %d1
    move.w  %d1, 2(%sp)                      /* physical row */

    move.w  ARCADE_PC080SN_BG_GROUP_OFFSET(%a5), %d1
    andi.w  #0x0003, %d1
    lsl.w   #4, %d1
    move.w  ARCADE_PC080SN_BG_SUBCOL_OFFSET(%a5), %d2
    andi.w  #0x000F, %d2
    add.w   %d2, %d1
    andi.w  #0x003F, %d1
    move.w  %d1, 4(%sp)                      /* physical column */

    move.l  %d7, %d0
    swap    %d0
    bsr     .Lplane_b_native_attr_from_word
    move.w  %d0, 6(%sp)

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    move.w  %d7, %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    6(%sp), %d3

    lea     staged_bg_buffer, %a6
    move.w  2(%sp), %d0
    lsl.w   #7, %d0
    move.w  4(%sp), %d1
    add.w   %d1, %d1
    add.w   %d1, %d0
    move.w  %d3, 0(%a6,%d0.w)

    move.w  2(%sp), %d0
    move.l  bg_row_dirty, %d1
    bset    %d0, %d1
    move.l  %d1, bg_row_dirty

.Lplane_b_stage_cell_done:
    adda.w  #8, %sp
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_tilemap_plane_a:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    /* Build 0160 gameplay FG_SRC reattachment. After Build 0159 fixed the PC080SN
     * pass selector (a5@0x10A8=0), the Stage 1 tilemap dispatch takes the BG branch
     * (this hook) instead of the FG branch, so genesistan_hook_tilemap_fg no longer
     * runs during gameplay and the FG_SRC staging was lost. Re-run the same
     * Genesis-only FG_SRC per-column staging here, gated to the gameplay scene,
     * reusing the same a5@0x10A0 dcol input. genesistan_stage_fg_src_column and
     * genesistan_stage_bg_collision_column are movem-wrapped (preserve
     * d0-d7/a0-a6), so BG staging state and the a0 input are untouched. The FG
     * helper stages visible Plane-A cells; the BG collision helper separately
     * reproduces the original 0x559B2 collision-map side-channel from the BG
     * descriptor walk. Neither helper touches a5@0x10A8 (selector). */
    cmpi.b  #SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    bne.s   .Lbg_skip_fg_stage
    bsr     genesistan_stage_fg_src_column
    bsr     genesistan_stage_bg_collision_column
.Lbg_skip_fg_stage:

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

/* Genesis-only Stage 1 FG_SRC per-column staging. Extracted (Build 0160) from the
 * former genesistan_hook_tilemap_fg gameplay path so it can be shared. Replays the
 * proven Build 0155 FG model through the arcade-owned rebuilt pointer table
 * (0x00FF1040) using the real FG column dest a5@0x10A0, routing each cell through the gameplay-only tall FG backing helper
 * (LUT + attr conversion + tall staging + projection dirty). Collision is intentionally NOT authored here:
 * Stage 1 arcade collision is owned by the BG producer 0x559B2, not this FG_SRC
 * visual replay. movem-wrapped: preserves d0-d7/a0-a6 for the caller; reads
 * a5@0x10A0/a5@0x10CA and 0x00FF1040, never writes a5@0x10A8. Caller must gate
 * on SCENE_GAMEPLAY_ID. */
genesistan_stage_fg_src_column:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.l  ARCADE_PC080SN_DEST_BG_OFFSET(%a5), %d0   /* a5@0x10A0 = FG column dest */
    andi.l  #0x00003FFC, %d0                          /* dcol*4 (col offset within plane) */
    movea.l #ARCADE_PC080SN_CWINDOW_BASE_FG, %a4
    adda.l  %d0, %a4                                  /* a4 = base cell dest (plane row 0) */
    moveq   #0, %d2
    move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d2
    andi.w  #0x0003, %d2
    add.w   %d2, %d2                                  /* d2 = arcade colidx*2 */
    movea.l #PC080SN_DESC_REBUILD_PTR_TABLE, %a3      /* rebuilt block pointers, already Genesis-addressed */
    moveq   #0, %d4                                   /* d4 = seg */
.Lfgc_seg_loop:
    move.l  %d4, %d6
    lsl.l   #2, %d6                                   /* seg*4 */
    movea.l %a3, %a2
    adda.l  %d6, %a2
    move.l  (%a2), %d6                                /* rebuilt block pointer from 0x00FF1040 */
    cmpi.l  #0x00000200, %d6
    blo     .Lfgc_done
    cmpi.l  #0x00060000, %d6
    bhs     .Lfgc_done
    movea.l %d6, %a2
    adda.w  %d2, %a2                                  /* a2 = block base for this seg/col */
    moveq   #0, %d5                                   /* d5 = row */
.Lfgc_row_loop:
    move.w  %d5, %d6
    lsl.w   #3, %d6                                   /* row*8 */
    move.w  0(%a2,%d6.w), %d0                         /* code word */
    andi.w  #0x3FFF, %d0
    move.l  #FG_PLANE_ATTR_HI, %d1
    move.w  %d0, %d1                                  /* d1 = attr<<16 | code */
    move.l  %d4, %d0
    lsl.l   #2, %d0                                   /* seg*4 */
    add.l   %d5, %d0                                  /* + row = plane row */
    lsl.l   #8, %d0                                   /* plane row * 0x100 */
    movea.l %a4, %a0
    adda.l  %d0, %a0                                  /* a0 = cell dest */
    move.l  %d1, %d0                                  /* D0 = composed arcade cell */
    moveq   #1, %d1                                   /* D1 = count */
    bsr     genesistan_hook_tilemap_fg_fill_tall

    addq.w  #1, %d5
    cmpi.w  #FG_PRODUCER_ROW_COUNT, %d5
    bne     .Lfgc_row_loop
    addq.w  #1, %d4
    cmpi.w  #FG_PRODUCER_SEG_COUNT, %d4
    bne     .Lfgc_seg_loop

.Lfgc_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* Stage 1 BG collision-map side-channel. The original arcade BG producer
 * 0x559B2 writes collision from the rebuilt descriptor/table data before
 * writing the visible tile:
 *   if *(block+32) == 0x00FF: word = *(block+34)
 *   else: word = *(block+20 + row*8 + strip*2)
 *   dest = 0x10DE00 + ((a0 - 0xC08000) >> 1)
 * This helper mirrors only that collision half into mapped Genesis WRAM
 * 0x00FF1E00. It does not stage BG/FG tiles and does not advance a5@0x10A0;
 * the surrounding translated producer keeps owning the arcade cursor update. */
genesistan_stage_bg_collision_column:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d7
    move.l  ARCADE_PC080SN_DEST_BG_OFFSET(%a5), %d5
    move.l  %d5, %d0
    andi.l  #0x00FFFFFF, %d0
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d0
    blo     .Lbgc_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d0
    bhs     .Lbgc_done
    move.l  %d0, %d5

    lea     ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0
    movea.l #ARCADE_MAINCPU_ROM_BASE, %a1
    movea.l #ARCADE_COLLISION_MAP_BASE, %a6
    moveq   #15, %d6

.Lbgc_desc_loop:
    move.l  (%a0)+, %d3
    btst    #0, %d3
    bne     .Lbgc_desc_done
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lbgc_desc_done

    movea.l %a1, %a2
    adda.l  %d3, %a2
    move.w  2(%a2), %d3
    cmpi.w  #0x7FE0, %d3
    bhi     .Lbgc_desc_done

    movea.l %a1, %a2
    moveq   #0, %d0
    move.w  %d3, %d0
    adda.l  %d0, %a2

    moveq   #0, %d4
.Lbgc_row_loop:
    move.w  32(%a2), %d0
    cmpi.w  #0x00FF, %d0
    beq.s   .Lbgc_collision_alt

    move.w  %d4, %d0
    lsl.w   #3, %d0
    move.w  %d7, %d1
    add.w   %d1, %d1
    add.w   %d1, %d0
    move.w  20(%a2,%d0.w), %d2
    bra.s   .Lbgc_collision_have

.Lbgc_collision_alt:
    move.w  34(%a2), %d2

.Lbgc_collision_have:
    move.l  %d5, %d0
    moveq   #0, %d1
    move.w  %d4, %d1
    lsl.w   #8, %d1
    add.l   %d1, %d0
    andi.l  #0x00FFFFFF, %d0
    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d0
    lsr.l   #1, %d0
    andi.w  #0x1FFF, %d0
    move.w  %d2, 0(%a6,%d0.w)

    addq.w  #1, %d4
    cmpi.w  #4, %d4
    bne     .Lbgc_row_loop

.Lbgc_desc_done:
    addi.l  #0x00000400, %d5
    dbra    %d6, .Lbgc_desc_loop

.Lbgc_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

genesistan_hook_tilemap_fg:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    /* Build 0155 Stage 1 FG plane staging, now shared via genesistan_stage_fg_src_column
     * (Build 0160). NOTE: after Build 0159's selector fix this hook's gameplay path is no
     * longer reached during Stage 1 (dispatch takes the BG branch); the staging now runs
     * from genesistan_hook_tilemap_plane_a. Kept for any residual FG-branch invocation and
     * for the unchanged non-gameplay FG descriptor path below. */
    cmpi.b  #SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    bne     .Lfg_not_gameplay

    bsr     genesistan_stage_fg_src_column
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lfg_not_gameplay:
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

    suba.w  #12, %sp
    clr.l   0(%sp)
    move.w  %d1, 4(%sp)
    move.w  %d2, %d0
    add.w   %d7, %d0
    add.w   %d0, %d0
    move.w  %d0, 6(%sp)
    clr.w   8(%sp)

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
    move.w  %d0, 10(%sp)

    moveq   #3, %d4
.Lfg_hook_row_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    10(%sp), %d3

    move.w  %d1, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    add.w   %d7, %d0
    add.w   %d7, %d0
    move.w  %d3, 0(%a6,%d0.w)
    moveq   #1, %d0
    lsl.l   %d1, %d0
    or.l    %d0, 0(%sp)

    adda.w  #8, %a4
    addq.w  #1, %d1
    andi.w  #0x001F, %d1
    dbra    %d4, .Lfg_hook_row_loop

    bra.s   .Lfg_hook_desc_done

.Lfg_hook_invalid_desc:
    move.w  #1, 8(%sp)
    addq.w  #4, %d1
    andi.w  #0x001F, %d1

.Lfg_hook_desc_done:
    addi.l  #0x00000400, %d5
    addq.w  #4, %d2
    andi.w  #0x003F, %d2
    subq.w  #4, %d1
    andi.w  #0x001F, %d1
    dbra    %d6, .Lfg_hook_desc_loop

    tst.w   8(%sp)
    bne.s   .Lfg_hook_broad_fallback

    move.w  6(%sp), %d0
    addi.w  #120, %d0
    cmpi.w  #128, %d0
    bhs.s   .Lfg_hook_broad_fallback

    move.w  fg_narrow_desc_count, %d0
    cmpi.w  #FG_NARROW_CAP, %d0
    bhs.s   .Lfg_hook_broad_fallback

    move.w  %d0, %d3
    add.w   %d3, %d3
    lea     fg_narrow_desc_table, %a0
    adda.w  %d3, %a0

    move.w  4(%sp), %d3
    move.b  %d3, (%a0)
    move.w  6(%sp), %d3
    move.b  %d3, 1(%a0)

    addq.w  #1, %d0
    move.w  %d0, fg_narrow_desc_count
    bra.s   .Lfg_hook_decision_done

.Lfg_hook_broad_fallback:
    move.l  0(%sp), %d0
    beq.s   .Lfg_hook_decision_done
    move.l  fg_row_dirty, %d3
    or.l    %d0, %d3
    move.l  %d3, fg_row_dirty

.Lfg_hook_decision_done:
    move.l  %d5, ARCADE_PC080SN_DEST_FG_OFFSET(%a5)
    adda.w  #12, %sp
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

/* Build 0170 gameplay-only tall BG writer.  The item-page/Stage-1 strip
 * producer emits 64 PC080SN BG rows; the legacy 32-row staging helper aliases
 * rows 32..63 over rows 0..31.  This helper preserves all 64 rows in a virtual
 * backing buffer.  VBlank projects the currently visible 32-row half into the
 * existing staged_bg_buffer before the normal Plane-B commit. */
genesistan_hook_tilemap_bg_fill_tall:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    movea.l %a0, %a4
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2
    blo     .Lbg_tall_fill_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lbg_tall_fill_done

    move.w  %d1, %d6
    tst.w   %d6
    beq     .Lbg_tall_fill_done

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_bg_tall_buffer, %a6

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

.Lbg_tall_fill_loop:
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lbg_tall_fill_done

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2
    lsr.l   #2, %d2

    move.w  %d2, %d4
    andi.w  #0x003F, %d4
    move.w  %d2, %d5
    lsr.w   #6, %d5
    andi.w  #0x003F, %d5

    move.w  %d5, %d0
    lsl.w   #7, %d0
    add.w   %d4, %d0
    add.w   %d4, %d0
    move.w  %d3, 0(%a6,%d0.w)
    move.b  #1, bg_tall_dirty

    adda.l  #4, %a4
    subq.w  #1, %d6
    bne.s   .Lbg_tall_fill_loop

.Lbg_tall_fill_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* Build 0172 gameplay-only tall FG writer.  The Stage-1 FG_SRC replay has
 * 16 four-row segments (64 PC080SN FG rows). The legacy 32-row FG staging
 * helper aliases rows 32..63 over rows 0..31, so gameplay writes preserve all
 * rows here and VBlank projects the visible window into staged_fg_buffer. */
genesistan_hook_tilemap_fg_fill_tall:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    movea.l %a0, %a4
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
    blo     .Lfg_tall_fill_done
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lfg_tall_fill_done

    move.w  %d1, %d6
    tst.w   %d6
    beq     .Lfg_tall_fill_done

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_fg_tall_buffer, %a6

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

.Lfg_tall_fill_loop:
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_FG + ARCADE_PC080SN_CWINDOW_BYTES), %d2
    bhs     .Lfg_tall_fill_done

    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_FG, %d2
    lsr.l   #2, %d2

    move.w  %d2, %d4
    andi.w  #0x003F, %d4
    move.w  %d2, %d5
    lsr.w   #6, %d5
    andi.w  #0x003F, %d5

    move.w  %d5, %d0
    lsl.w   #7, %d0
    add.w   %d4, %d0
    add.w   %d4, %d0
    move.w  %d3, 0(%a6,%d0.w)
    move.b  #1, fg_tall_dirty

    adda.l  #4, %a4
    subq.w  #1, %d6
    bne.s   .Lfg_tall_fill_loop

.Lfg_tall_fill_done:
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

genesistan_hook_inline_fg_write_3a92a:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08C60, %a0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    tst.w   %d0
    rts

genesistan_hook_inline_fg_write_3acea:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C09170, %a0
    move.l  #0x00002749, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* Build 0156: sibling of genesistan_hook_inline_fg_write_3a92a. The raw single-digit FG
 * writer at runtime 0x03D24C (arcade 0x03D04C) issues `move.w %d1, 0xC08C66` (d1 = digit
 * tile 0x30..0x39 = 9 - d0 + 0x30), a raw PC080SN FG C-window store that strict-target
 * emulators fault on (BlastEm freeze at C08C66). Route the live code word through the
 * existing FG staging path instead (cell base 0xC08C64, code word at +2). Preserves
 * caller registers; reproduces the original move.w CCR effect via tst.w %d1. */
genesistan_hook_inline_fg_write_3d04c:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08C64, %a0
    move.l  %d1, %d0
    andi.l  #0x0000FFFF, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    tst.w   %d1
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

    /* 0x3C950 is shared by PC080SN text and the PC090OJ actor->sprite default
     * shape path.  The opcode replacement owns the PC080SN C-window case; any
     * non-C-window destination must preserve the original a1@+ sprite writes. */
    move.l  %a1, %d4
    andi.l  #0x00FFFFFF, %d4
    cmpi.l  #0x00C00000, %d4
    blo     .L3c950_sprite_direct
    cmpi.l  #0x00C10000, %d4
    bhs     .L3c950_sprite_direct

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

.L3c950_sprite_direct:
    clr.w   %d0
    clr.w   %d5

    btst    #0, %d6
    bne.s   .L3c950_sprite_dispatch_d6
    tst.b   %d7
    beq     .L3c950_sprite_alt_loop
    bra     .L3c950_sprite_primary_loop

.L3c950_sprite_dispatch_d6:
    tst.b   3(%a4)
    bne     .L3c950_sprite_primary_loop
    tst.b   %d7
    beq     .L3c950_sprite_primary_loop
    bra     .L3c950_sprite_alt_loop

.L3c950_sprite_primary_loop:
    bsr     .L3c950_read_opcode
    tst.w   %d5
    bne     .L3c950_sprite_sentinel_primary

    clr.w   %d7
    cmpi.b  #0x40, %d3
    bne.s   .L3c950_sprite_primary_check_80
    addq.w  #1, %d7
.L3c950_sprite_primary_check_80:
    cmpi.b  #0x80, %d3
    bne.s   .L3c950_sprite_primary_attr
    ori.w   #0x4000, %d0
.L3c950_sprite_primary_attr:
    bsr     .L3c950_apply_attr_gate
    move.w  %d0, (%a1)+

    move.b  (%a0)+, %d1
    ext.w   %d1
    add.w   26(%a4), %d1
    cmpi.b  #0x70, %d3
    bne.s   .L3c950_sprite_primary_y_ready
    add.w   24(%a4), %d1
.L3c950_sprite_primary_y_ready:
    move.w  %d1, (%a1)+

    bsr     .L3c950_compute_next_attr
    move.w  %d4, (%a1)+

    move.b  (%a0)+, %d7
    ext.w   %d7
    add.w   22(%a4), %d7
    move.w  %d7, (%a1)+

.L3c950_sprite_primary_iter_done:
    subq.l  #1, %d2
    bne     .L3c950_sprite_primary_loop
    bra     .L3c950_done

.L3c950_sprite_alt_loop:
    bsr     .L3c950_read_opcode
    tst.w   %d5
    bne     .L3c950_sprite_sentinel_primary

    clr.w   %d7
    cmpi.b  #0x40, %d3
    bne.s   .L3c950_sprite_alt_attr
    addq.w  #1, %d7
.L3c950_sprite_alt_attr:
    ori.w   #0x4000, %d0
    bsr     .L3c950_apply_attr_gate
    move.w  %d0, (%a1)+

    move.b  (%a0)+, %d1
    ext.w   %d1
    add.w   26(%a4), %d1
    move.w  %d1, (%a1)+

    bsr     .L3c950_compute_next_attr
    move.w  %d4, (%a1)+

    move.b  (%a0)+, %d7
    ext.w   %d7
    neg.w   %d7
    sub.w   0x0010, %d7
    add.w   22(%a4), %d7
    move.w  %d7, (%a1)+

.L3c950_sprite_alt_iter_done:
    subq.l  #1, %d2
    bne     .L3c950_sprite_alt_loop
    bra     .L3c950_done

.L3c950_sprite_sentinel_primary:
    move.w  #0x0180, 2(%a1)
    adda.w  #8, %a1
    bra     .L3c950_sprite_primary_iter_done

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
    /* Map the descriptor's absolute arcade work-RAM source pointer to Genesis
     * WRAM: a4 = a5 + (source - ARCADE_WORKRAM_A5_BASE)  (KF-039).  Was
     * andi.l #0x0000FFFF (kept the 0xC000 base bits) -> read 0x00FFCxxx zeros. */
    subi.l  #ARCADE_WORKRAM_A5_BASE, %d2
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

    /* Leading-zero suppression runs only for the 6-digit score fields.  The
     * original count was saved in %d7, but the digit-emit path
     * (.Ltw_compose_d1_from_d0_d2) clobbers %d7, so re-read the count from the
     * still-live descriptor pointer %a0 (Build 0151 fix: the clobbered %d7
     * check was always false, so leading zeros were never blanked). */
    cmpi.w  #6, (%a0)
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

    lea     staged_fg_tall_buffer, %a0
    move.w  #(4096 - 1), %d0
.Lcw_clear_fg_tall:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_fg_tall

    move.l  #0xFFFFFFFF, bg_row_dirty
    move.l  #0xFFFFFFFF, fg_row_dirty
    move.b  #1, fg_tall_dirty
    clr.b   fg_native_gameplay_owner

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


    .section .text.zzz_itempage_strip_populate,"ax"

/* Populates the item-page strip descriptor slots at runtime 0x055E2E.
 * The walker slot remains an arcade/source ROM pointer; relocate at
 * dereference through the JSON-proven arcade_copy segment, then relocate the
 * descriptor's strip-data pointer before storing it for the consumer.
 */
genesistan_hook_itempage_strip_populate:
    movea.l #PC080SN_ITEMPAGE_WALKER_SLOT, %a0
    movea.l (%a0), %a4
    cmpa.l  #PC080SN_DESC_ARCADE_START, %a4
    blo.s   .Litempage_strip_bad_ptr
    cmpa.l  #PC080SN_DESC_ARCADE_END, %a4
    bhs.s   .Litempage_strip_bad_ptr

    suba.l  #PC080SN_DESC_ARCADE_START, %a4
    adda.l  #PC080SN_DESC_GENESIS_START, %a4

    movea.l 2(%a4), %a2
    cmpa.l  #PC080SN_DESC_ARCADE_START, %a2
    blo.s   .Litempage_strip_bad_ptr
    cmpa.l  #PC080SN_DESC_ARCADE_END, %a2
    bhs.s   .Litempage_strip_bad_ptr

    suba.l  #PC080SN_DESC_ARCADE_START, %a2
    adda.l  #PC080SN_DESC_GENESIS_START, %a2

    movea.l #PC080SN_ITEMPAGE_STRIP_WORD_SLOT, %a1
    move.w  (%a4), (%a1)
    movea.l #PC080SN_ITEMPAGE_STRIP_PTR_SLOT, %a1
    move.l  %a2, (%a1)
    rts

.Litempage_strip_bad_ptr:
    trap    #0


    .section .text.zzz_itempage_strip_blit,"ax"

/* Routes the item-page BG strip producer at runtime 0x055E5E through
 * Genesis BG staging. The source-side slots remain the Build 0119 outputs:
 * 0xFF1100 = relocated strip source, 0xFF1104 = PC080SN attr word.
 */
genesistan_hook_itempage_strip_blit:
    movem.l %d1/%d6, -(%sp)

    /* Build 0217: producer-source PC080SN tileset selection.
     * The same arcade Stage 1 strip producer walks outdoor attr=0x0002 sources and
     * then cave attr=0x0003 sources. They do not fit together in the Genesis PC080SN
     * VRAM cache, so select the residency manifest from the producer-owned source
     * pointer while keeping the logical scene as gameplay. d0/a3 are reloaded below;
     * load_scene_tiles preserves d1-d7/a0-a4. */
    moveq   #0, %d6
    moveq   #0, %d1
    movea.l #PC080SN_ITEMPAGE_STRIP_PTR_SLOT, %a3
    move.l  (%a3), %d0
    andi.l  #0x00FFFFFF, %d0
    cmpi.l  #GAMEPLAY_STRIP_SRC_LO, %d0
    blo.s   .Litempage_blit_scene_ready
    cmpi.l  #GAMEPLAY_STRIP_SRC_HI, %d0
    bhs.s   .Litempage_blit_scene_ready
    moveq   #1, %d6
    moveq   #SCENE_GAMEPLAY_ID, %d1
    cmpi.l  #GAMEPLAY_STRIP_SRC_CAVE_LO, %d0
    blo.s   .Litempage_blit_tileset_selected
    moveq   #SCENE_GAMEPLAY_CAVE_TILESET_ID, %d1
.Litempage_blit_tileset_selected:
    cmp.b   genesistan_current_pc080sn_tileset_id, %d1
    beq.s   .Litempage_blit_scene_ready
    move.w  %d1, %d0
    bsr     load_scene_tiles
.Litempage_blit_scene_ready:

    movea.l #PC080SN_ITEMPAGE_DEST_CURSOR_SLOT, %a3
    movea.l (%a3), %a0
    movea.l #PC080SN_ITEMPAGE_STRIP_PTR_SLOT, %a3
    movea.l (%a3), %a2
    movea.l #PC080SN_ITEMPAGE_STRIP_WORD_SLOT, %a1

    move.w  (%a1), %d7
    swap    %d7
    clr.w   %d7

    clr.w   %d2
.Litempage_strip_blit_loop:
    move.w  %d2, %d1
    lsl.w   #5, %d1
    move.w  PC080SN_ITEMPAGE_STRIP_COL_SLOT, %d0
    lsl.w   #1, %d0
    add.w   %d0, %d1

    clr.l   %d0
    move.w  0(%a2,%d1.w), %d0
    or.l    %d7, %d0
    moveq   #1, %d1
    tst.w   %d6
    beq.s   .Litempage_strip_blit_32row
    bsr     .Lplane_b_stage_gameplay_producer_cell_native
    bra.s   .Litempage_strip_blit_after_fill
.Litempage_strip_blit_32row:
    bsr     genesistan_hook_tilemap_bg_fill
.Litempage_strip_blit_after_fill:

    adda.l  #0x00000100, %a0
    addq.w  #1, %d2
    cmpi.w  #64, %d2
    bne.s   .Litempage_strip_blit_loop

    movea.l #PC080SN_ITEMPAGE_DEST_CURSOR_SLOT, %a3
    move.l  %a0, (%a3)

    movem.l (%sp)+, %d1/%d6
    rts

vdp_commit_fg_narrow_strips:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  fg_narrow_desc_count, %d7
    beq.s   .Lfg_narrow_done
    subq.w  #1, %d7

    moveq   #VDP_REG_AUTOINC, %d0
    moveq   #0x08, %d1
    bsr     vdp_set_reg

    lea     fg_narrow_desc_table, %a5
.Lfg_narrow_desc_loop:
    moveq   #0, %d6
    move.b  (%a5)+, %d6
    moveq   #0, %d3
    move.b  (%a5)+, %d3

    moveq   #3, %d5
.Lfg_narrow_row_loop:
    move.w  %d6, %d4
    andi.w  #0x001F, %d4
    lsl.l   #7, %d4
    add.l   %d3, %d4

    move.l  #VRAM_PLANE_A_BASE, %d0
    add.l   %d4, %d0
    bsr     vdp_set_vram_write_addr

    lea     staged_fg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #(16 - 1), %d2
.Lfg_narrow_word_loop:
    move.w  (%a0), VDP_DATA
    adda.w  #8, %a0
    dbra    %d2, .Lfg_narrow_word_loop

    addq.w  #1, %d6
    dbra    %d5, .Lfg_narrow_row_loop

    dbra    %d7, .Lfg_narrow_desc_loop

    moveq   #VDP_REG_AUTOINC, %d0
    moveq   #0x02, %d1
    bsr     vdp_set_reg
    clr.w   fg_narrow_desc_count

.Lfg_narrow_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    bra.w   vdp_commit_fg_strips_if_dirty


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
