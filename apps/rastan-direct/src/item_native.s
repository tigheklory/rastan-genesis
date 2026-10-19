    .section .text,"ax"

    .global genesistan_item_description_enter
    .global genesistan_item_ring_advance
    .global genesistan_item_emit_native

    .extern staged_bg_buffer
    .extern bg_row_dirty
    .extern staged_scroll_x_bg
    .extern staged_scroll_y_bg
    .extern staged_scroll_x_fg
    .extern staged_scroll_y_fg
    .extern transient_items_active
    .extern genesistan_hud_activate_frontend
    .extern vdp_set_vram_write_addr

    .equ VDP_DATA,                    0x00C00000
    .equ ITEM_LOGICAL_ROWS,           64
    .equ ITEM_PHYSICAL_ROWS,          32
    .equ ITEM_ROW_BYTES,              128
    .equ ITEM_INITIAL_TOP_ROW,        4
    .equ ITEM_INITIAL_LAST_ROW,       35
    .equ ITEM_PAGE_B_INSTALL_PIXEL,   96
    .equ ITEM_PAGE_A_ICON_COUNT,      17
    .equ ITEM_PAGE_B_ICON_COUNT,      3

/* Item-description presentation cut at arcade 0x5602C. The retained attract
 * dispatcher owns entry, dwell, Start/credit behavior and lifetime; this
 * helper replaces only the PC080SN decompression/C-window and PC090OJ copy
 * tails with final Genesis Plane-B/SAT assets. */
genesistan_item_description_enter:
    movem.l %d0-%d7/%a0-%a3, -(%sp)

    /* FRONTEND_FULL is the one shared HUD owner. Activate it before installing
     * icon cells 20+, because HUD activation owns/resets cells 0..19. */
    bsr     genesistan_hud_activate_frontend

    lea     native_item_plane_patterns, %a2
.Litem_plane_pattern_next:
    move.w  (%a2)+, %d0
    cmpi.w  #0xFFFF, %d0
    beq.s   .Litem_plane_patterns_done
    lsl.l   #5, %d0
    bsr     vdp_set_vram_write_addr
    moveq   #15, %d7
.Litem_plane_pattern_words:
    move.w  (%a2)+, VDP_DATA
    dbra    %d7, .Litem_plane_pattern_words
    bra.s   .Litem_plane_pattern_next
.Litem_plane_patterns_done:

    lea     native_item_icon_patterns, %a2
.Litem_icon_pattern_next:
    move.w  (%a2)+, %d0
    cmpi.w  #0xFFFF, %d0
    beq.s   .Litem_icon_patterns_done
    lsl.l   #5, %d0
    bsr     vdp_set_vram_write_addr
    moveq   #15, %d7
.Litem_icon_pattern_words:
    move.w  (%a2)+, VDP_DATA
    dbra    %d7, .Litem_icon_pattern_words
    bra.s   .Litem_icon_pattern_next
.Litem_icon_patterns_done:

    /* Arcade cursor C00400 means the initial 32-row resident window is logical
     * rows 4..35. Physical ownership is logical_row&31. */
    moveq   #ITEM_INITIAL_TOP_ROW, %d6
    moveq   #(ITEM_PHYSICAL_ROWS - 1), %d5
.Litem_initial_row:
    moveq   #0, %d0
    move.w  %d6, %d0
    lsl.l   #7, %d0
    lea     native_item_logical_map, %a0
    adda.l  %d0, %a0

    move.w  %d6, %d0
    andi.w  #(ITEM_PHYSICAL_ROWS - 1), %d0
    lsl.w   #7, %d0
    lea     staged_bg_buffer, %a1
    adda.w  %d0, %a1
    moveq   #31, %d7
.Litem_initial_row_copy:
    move.l  (%a0)+, (%a1)+
    dbra    %d7, .Litem_initial_row_copy
    addq.w  #1, %d6
    dbra    %d5, .Litem_initial_row

    move.l  #0xFFFFFFFF, bg_row_dirty
    move.w  0x10EC(%a5), staged_scroll_x_bg
    move.w  0x10EE(%a5), staged_scroll_y_bg
    move.w  0x10AE(%a5), staged_scroll_x_fg
    move.w  0x10B0(%a5), staged_scroll_y_fg
    move.w  #1, transient_items_active
    /* Preserve the original page-A copy's semantic end cursor. */
    move.l  #0x00D001F8, 0x141C(%a5)

    movem.l (%sp)+, %d0-%d7/%a0-%a3
    rts

/* Called only when the retained A5+0x10EE scroll reaches an 8-pixel boundary.
 * New progress k=(-scroll mod512)/8 assigns entering logical row 35+k to its
 * physical logical&31 owner. Exactly one 64-word row and one dirty bit. */
genesistan_item_ring_advance:
    movem.l %d0-%d7/%a0-%a1, -(%sp)
    move.w  0x10EE(%a5), %d6
    neg.w   %d6
    andi.w  #0x01FF, %d6
    lsr.w   #3, %d6
    addi.w  #ITEM_INITIAL_LAST_ROW, %d6
    andi.w  #(ITEM_LOGICAL_ROWS - 1), %d6

    moveq   #0, %d0
    move.w  %d6, %d0
    lsl.l   #7, %d0
    lea     native_item_logical_map, %a0
    adda.l  %d0, %a0

    andi.w  #(ITEM_PHYSICAL_ROWS - 1), %d6
    move.w  %d6, %d0
    lsl.w   #7, %d0
    lea     staged_bg_buffer, %a1
    adda.w  %d0, %a1
    moveq   #31, %d7
.Litem_crossing_copy:
    move.l  (%a0)+, (%a1)+
    dbra    %d7, .Litem_crossing_copy

    move.l  bg_row_dirty, %d0
    bset    %d6, %d0
    move.l  %d0, bg_row_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a1
    rts

/* Purpose-built native item sprites. Generated records contain base arcade Y,
 * final fixed Genesis tile word, final X, and source-code provenance. Static
 * patterns were installed at entry; runtime work is only semantic visibility
 * and scroll-relative Y. in/out: A3 SAT cursor, D5 emitted record count. */
genesistan_item_emit_native:
    move.w  0x10EE(%a5), %d6
    neg.w   %d6
    andi.w  #0x01FF, %d6              /* live arcade-owned pixel progress */

    lea     native_item_icon_records, %a0
    moveq   #ITEM_PAGE_A_ICON_COUNT, %d7
    cmpi.w  #ITEM_PAGE_B_INSTALL_PIXEL, %d6
    blo.s   .Litem_emit_a_loop
    adda.w  #(3 * 8), %a0             /* page B replaced page-A records 0..2 */
    moveq   #(ITEM_PAGE_A_ICON_COUNT - 3), %d7
.Litem_emit_a_loop:
    bsr     .Litem_emit_one
    adda.w  #8, %a0
    subq.w  #1, %d7
    bne.s   .Litem_emit_a_loop

    cmpi.w  #ITEM_PAGE_B_INSTALL_PIXEL, %d6
    blo.s   .Litem_emit_done
    lea     native_item_icon_records+(ITEM_PAGE_A_ICON_COUNT*8), %a0
    subi.w  #ITEM_PAGE_B_INSTALL_PIXEL, %d6
    moveq   #ITEM_PAGE_B_ICON_COUNT, %d7
.Litem_emit_b_loop:
    bsr     .Litem_emit_one
    adda.w  #8, %a0
    subq.w  #1, %d7
    bne.s   .Litem_emit_b_loop
.Litem_emit_done:
    rts

.Litem_emit_one:
    move.w  (%a0), %d2
    sub.w   %d6, %d2
    cmpi.w  #16, %d2                  /* exact arcade retirement threshold */
    ble.s   .Litem_emit_one_done
    cmpi.w  #232, %d2                 /* 224-line viewport plus 8-line origin */
    bge.s   .Litem_emit_one_done
    subi.w  #8, %d2
    addi.w  #0x0080, %d2
    move.w  %d2, (%a3)+
    move.w  %d5, %d0
    addq.w  #1, %d0
    ori.w   #0x0500, %d0
    move.w  %d0, (%a3)+
    move.w  2(%a0), (%a3)+
    move.w  4(%a0), %d0
    addi.w  #0x0080, %d0
    move.w  %d0, (%a3)+
    addq.w  #1, %d5
.Litem_emit_one_done:
    rts

    .section .rodata,"a"
    .align 2
native_item_logical_map:
    .incbin "../../build/rastan-direct/native_item_logical_map.bin"
native_item_plane_patterns:
    .incbin "../../build/rastan-direct/native_item_plane_patterns.bin"
native_item_icon_patterns:
    .incbin "../../build/rastan-direct/native_item_icon_patterns.bin"
native_item_icon_records:
    .incbin "../../build/rastan-direct/native_item_icon_records.bin"
