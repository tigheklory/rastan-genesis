    .text
    .align 2

#ifndef RASTAN_ENABLE_STARTUP_HOOK
#define RASTAN_ENABLE_STARTUP_HOOK 1
#endif

    .globl genesistan_run_original_startup_common
    .globl genesistan_run_original_frontend_tick
    .globl genesistan_startup_common_continue_normal
    .globl genesistan_startup_common_exit_normal
    .globl genesistan_startup_common_exit_test
    .globl genesistan_sound_send_command
    .globl genesistan_sound_read_status
    .globl genesistan_hook_text_writer_3bb48
    .globl genesistan_hook_text_writer_3bb48_impl
    .globl genesistan_render_sprites_vdp
    .globl genesistan_render_sprites_vdp_bridge
    .globl genesistan_render_sprites_vdp_asm
    .globl genesistan_sprite_commit_asm
    .globl genesistan_palette_commit_asm
    .globl genesistan_asm_tilemap_commit_bg
    .globl genesistan_asm_tilemap_commit_fg
    .globl genesistan_bulk_tilemap_commit
    .globl genesistan_run_title_init_sequence
    .globl genesistan_run_arcade_tick_lean
    .globl arcade_vblank_active

#if RASTAN_ENABLE_STARTUP_HOOK

#define ARCADE_ROM_BASE 0x000200
#define FRONTEND_RUNTIME_SPRITE_LUT_OFFSET 0x28D0
#define FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET 0x28F4
#define PC080SN_DESC_LIST_OFFSET 0x1000
#define PC080SN_MAINCPU_MAX_ADDR 0x00060000
#define SPRITE_TILE_BASE 1024
#define SPRITE_TILE_BYTES 128
#define PC090OJ_CELL_COUNT 4096

genesistan_sound_send_command:
    move.b #0, genesistan_shadow_reg_3e0001
    move.b %d0, genesistan_sound_last_command
    move.b %d0, genesistan_sound_last_low_nibble
    move.b %d0, genesistan_shadow_reg_3e0003
    lsr.b #4, %d0
    move.b %d0, genesistan_sound_last_high_nibble
    move.b %d0, genesistan_shadow_reg_3e0003
    addq.w #1, genesistan_sound_command_count
    rts

genesistan_sound_read_status:
    move.b #4, genesistan_shadow_reg_3e0001
    moveq #0, %d0
    move.b genesistan_sound_status, %d0
    move.b %d0, genesistan_shadow_reg_3e0003
    rts

/*
 * 0x03BB48 replacement bridge:
 * keep arcade A5 workram base stable across the C hook.
 */
genesistan_hook_text_writer_3bb48:
    move.l %a5,-(%sp)
    jsr genesistan_hook_text_writer_3bb48_impl
    movea.l (%sp)+,%a5
    rts

/*
 * Sprite replacement bridge:
 * keep full arcade register state stable around the assembly sprite renderer.
 */
genesistan_render_sprites_vdp_bridge:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    bsr genesistan_render_sprites_vdp_asm
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

/*
 * Assembly palette commit: single per-frame CLCS -> CRAM owner.
 * Reads genesistan_palette_clcs[0..63], converts xRGB-444 to Genesis,
 * streams 64 colors to CRAM via VDP data port. Falls back to
 * genesistan_palette_rom_table if CLCS is empty.
 */
genesistan_palette_commit_asm:
    movem.l %d0-%d4/%a0-%a2,-(%sp)

    lea     genesistan_palette_clcs, %a0
    movea.l #0xC00004, %a1          /* VDP control port */
    movea.l #0xC00000, %a2          /* VDP data port */

    /* Check if CLCS has any data (test first entry) */
    tst.w   (%a0)
    bne.s   .Lpal_have_clcs

    /* Fallback: use ROM table */
    lea     genesistan_palette_rom_table, %a0
    /* ROM table is already in Genesis format, write directly */
    move.l  #0xC0000000, (%a1)      /* CRAM write addr 0 */
    moveq   #63, %d0
.Lpal_rom_loop:
    move.w  (%a0)+, (%a2)
    dbra    %d0, .Lpal_rom_loop
    bra.s   .Lpal_done

.Lpal_have_clcs:
    /* Set CRAM write address to 0 */
    move.l  #0xC0000000, (%a1)      /* CRAM write addr 0 */

    moveq   #63, %d0
.Lpal_clcs_loop:
    move.w  (%a0)+, %d1             /* raw CLCS xRGB-444 */

    /* Convert: genesis = ((raw>>1)&0x000E) | ((raw>>2)&0x00E0) | ((raw>>3)&0x0E00) */
    move.w  %d1, %d2
    lsr.w   #1, %d2
    andi.w  #0x000E, %d2            /* R component */

    move.w  %d1, %d3
    lsr.w   #2, %d3
    andi.w  #0x00E0, %d3            /* G component */
    or.w    %d3, %d2

    move.w  %d1, %d3
    lsr.w   #3, %d3
    andi.w  #0x0E00, %d3            /* B component */
    or.w    %d3, %d2

    move.w  %d2, (%a2)              /* write to CRAM */
    dbra    %d0, .Lpal_clcs_loop

.Lpal_done:
    movem.l (%sp)+,%d0-%d4/%a0-%a2
    rts

/*
 * Assembly sprite renderer: single per-frame sprite owner.
 * Called from the opcode-replace bridge during arcade tick.
 * Reads 2 sprite blocks from workram:
 *   Block-A: A5+0x11B2, 18 entries (title/logo sprites)
 *   Block-B: A5+0x0170, 4 entries (secondary sprites)
 * Each entry: word0=attr, word1=y, word2=code, word3=x
 *
 * Pass 1: DMA tile data from PC090OJ ROM to VRAM for each visible sprite.
 * Pass 2: Write SAT entries directly to VDP data port.
 */
genesistan_render_sprites_vdp_asm:
    movem.l %d0-%d7/%a0-%a6,-(%sp)

    lea     genesistan_arcade_workram_words, %a5
    movea.l #0xC00004, %a3          /* VDP control port */
    movea.l #0xC00000, %a4          /* VDP data port */
    move.w  #0x8F02, (%a3)          /* auto-increment = 2 */
    move.w  10*2(%a5), %d6          /* sprite_ctrl for colbank */

    /* --- Pass 1: DMA tile data for visible sprites --- */
    moveq   #0, %d5                 /* slot index (visible count) */

    /* Block-A: 18 entries at A5+0x11B2 */
    lea     0x11B2(%a5), %a0
    moveq   #17, %d7
.Lspr_tile_a:
    bsr     .Lspr_dma_tile
    adda.w  #8, %a0
    dbra    %d7, .Lspr_tile_a

    /* Block-B: 4 entries at A5+0x0170 */
    lea     0x0170(%a5), %a0
    moveq   #3, %d7
.Lspr_tile_b:
    bsr     .Lspr_dma_tile
    adda.w  #8, %a0
    dbra    %d7, .Lspr_tile_b

    move.w  %d5, %d4                /* total_visible for link calc */

    /* --- Pass 2: SAT commit --- */
    move.l  #0x78000003, (%a3)      /* VDP write VRAM 0xF800 (SAT) */
    moveq   #0, %d5                 /* reset slot index */

    /* Block-A SAT */
    lea     0x11B2(%a5), %a0
    moveq   #17, %d7
.Lspr_sat_a:
    bsr     .Lspr_write_sat
    adda.w  #8, %a0
    dbra    %d7, .Lspr_sat_a

    /* Block-B SAT */
    lea     0x0170(%a5), %a0
    moveq   #3, %d7
.Lspr_sat_b:
    bsr     .Lspr_write_sat
    adda.w  #8, %a0
    dbra    %d7, .Lspr_sat_b

    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

/* --- Subroutine: DMA one sprite's tiles to VRAM --- */
/* Entry: A0 = sprite entry, D5 = slot index (incremented on success) */
/* Uses: D0-D3, A1 */
.Lspr_dma_tile:
    move.w  2(%a0), %d0             /* y_raw */
    cmpi.w  #0x0180, %d0
    beq     .Lspr_dma_skip

    move.w  4(%a0), %d1             /* code */
    andi.w  #0x3FFF, %d1
    beq     .Lspr_dma_skip

    /* Check all-zero entry */
    tst.l   (%a0)
    bne.s   .Lspr_dma_go
    tst.l   4(%a0)
    beq     .Lspr_dma_skip

.Lspr_dma_go:
    /* Source: rastan_pc090oj + (code % PC090OJ_CELL_COUNT) * 128 */
    /* PC090OJ_CELL_COUNT = 4096, so code & 0x0FFF */
    andi.w  #0x0FFF, %d1
    move.w  %d1, %d0
    mulu.w  #SPRITE_TILE_BYTES, %d0 /* code * 128 */
    lea     rastan_pc090oj, %a1
    adda.l  %d0, %a1                /* source address in ROM */

    /* DMA source = address / 2 (68000 bus address for VDP DMA) */
    move.l  %a1, %d0
    lsr.l   #1, %d0

    /* DMA length = 64 words (128 bytes = 4 tiles) */
    move.w  #0x9340, (%a3)          /* length low = 0x40 */
    move.w  #0x9400, (%a3)          /* length high = 0x00 */

    /* DMA source address (3 registers) */
    move.w  %d0, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9500, %d1
    move.w  %d1, (%a3)

    move.l  %d0, %d1
    lsr.l   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9600, %d1
    move.w  %d1, (%a3)

    swap    %d0
    lsr.w   #1, %d0
    andi.w  #0x007F, %d0
    ori.w   #0x9700, %d0
    move.w  %d0, (%a3)

    /* VRAM destination = (SPRITE_TILE_BASE + slot*4) * 32 */
    move.w  %d5, %d0
    lsl.w   #2, %d0
    addi.w  #SPRITE_TILE_BASE, %d0
    lsl.l   #5, %d0                 /* * 32 bytes per tile */

    /* Build VDP DMA command word */
    move.w  %d0, %d1
    andi.w  #0x3FFF, %d1
    swap    %d1
    clr.w   %d1
    move.l  %d0, %d2
    swap    %d2
    andi.w  #0x0003, %d2
    or.w    %d2, %d1
    ori.l   #0x40000080, %d1        /* VRAM write + DMA trigger */
    move.l  %d1, (%a3)              /* trigger DMA */

    addq.w  #1, %d5
.Lspr_dma_skip:
    rts

/* --- Subroutine: Write one SAT entry --- */
/* Entry: A0 = sprite entry, D4 = total_visible, D5 = current index, D6 = sprite_ctrl */
/* Uses: D0-D3 */
.Lspr_write_sat:
    move.w  2(%a0), %d0             /* y_raw */
    cmpi.w  #0x0180, %d0
    beq     .Lspr_sat_skip

    move.w  4(%a0), %d1             /* code */
    andi.w  #0x3FFF, %d1
    beq     .Lspr_sat_skip

    /* Check all-zero */
    tst.l   (%a0)
    bne.s   .Lspr_sat_go
    tst.l   4(%a0)
    beq     .Lspr_sat_skip

.Lspr_sat_go:
    /* SAT word0: Y = (y_raw & 0x1FF) + 0x80 */
    andi.w  #0x01FF, %d0
    addi.w  #0x0080, %d0
    move.w  %d0, (%a4)

    /* SAT word1: size(2x2) + link */
    move.w  %d5, %d0
    addq.w  #1, %d0
    cmp.w   %d4, %d0
    bge.s   .Lspr_sat_last
    andi.w  #0x007F, %d0
    ori.w   #0x0500, %d0
    bra.s   .Lspr_sat_link_ok

.Lspr_sat_last:
    move.w  #0x0500, %d0            /* size 2x2, link=0 (end chain) */

.Lspr_sat_link_ok:
    move.w  %d0, (%a4)

    /* SAT word2: tile attr = priority | palette | vflip | hflip | tile_index */
    move.w  (%a0), %d0              /* word0: attr/flags */

    /* Extract flipy (bit 15) and flipx (bit 14) */
    move.w  %d0, %d2
    andi.w  #0x8000, %d2            /* flipy in bit 15 */
    lsr.w   #3, %d2                 /* -> bit 12 */
    move.w  %d0, %d3
    andi.w  #0x4000, %d3            /* flipx in bit 14 */
    lsr.w   #3, %d3                 /* -> bit 11 */

    /* palette_line = ((data & 0xF) | colbank) >> 4) & 3 */
    move.w  %d0, %d1
    andi.w  #0x000F, %d1
    move.w  %d6, %d0               /* sprite_ctrl */
    andi.w  #0x00E0, %d0
    lsr.w   #1, %d0                /* colbank = (ctrl & 0xE0) >> 1 */
    or.w    %d0, %d1               /* color = (data & 0xF) | colbank */
    lsr.w   #4, %d1
    andi.w  #0x0003, %d1           /* palette_line */
    lsl.w   #8, %d1
    lsl.w   #5, %d1                /* palette << 13 */

    or.w    %d2, %d1               /* | vflip << 12 */
    or.w    %d3, %d1               /* | hflip << 11 */
    ori.w   #0x8000, %d1           /* priority on */

    /* tile index = SPRITE_TILE_BASE + d5 * 4 */
    move.w  %d5, %d0
    lsl.w   #2, %d0
    addi.w  #SPRITE_TILE_BASE, %d0
    andi.w  #0x07FF, %d0
    or.w    %d0, %d1

    move.w  %d1, (%a4)             /* SAT word2 */

    /* SAT word3: X = (x_raw & 0x1FF) + 0x80 */
    move.w  6(%a0), %d0
    andi.w  #0x01FF, %d0
    addi.w  #0x0080, %d0
    move.w  %d0, (%a4)

    addq.w  #1, %d5

.Lspr_sat_skip:
    rts

/*
 * Legacy SAT commit (kept for reference, no longer called from hot path).
 *   - reads Block-A tuples from 0xE0FF11FE
 *   - reads per-entry VRAM tile indices from launcher WRAM LUT (18 entries)
 *   - skips hidden sentinel entries (word1 == 0x0180)
 *   - writes SAT entries directly to VDP data port at VRAM 0xF800
 */
genesistan_sprite_commit_asm:
    movem.l %d0-%d7/%a0-%a6,-(%sp)

    movea.l #0xC00004, %a1          /* VDP control port */
    movea.l #0xC00000, %a2          /* VDP data port */
    move.w  #0x8F02, (%a1)          /* auto-increment = 2 bytes */
    move.l  #0x78000003, (%a1)      /* VDP_WRITE_VRAM_ADDR(0xF800) */

    movea.l #0xE0FF11FE, %a0        /* Block-A base */
    lea     wram_overlay+FRONTEND_RUNTIME_SPRITE_LUT_OFFSET, %a3
    moveq   #17, %d7                /* 18 entries */
    moveq   #0, %d6                 /* valid/written entry count for link chain */

.Lsprite_count_loop:
    move.w  2(%a0), %d0             /* word1: y */
    cmpi.w  #0x0180, %d0
    beq.s   .Lsprite_count_skip

    move.w  (%a3), %d1              /* per-entry VRAM tile index from prepare step */
    tst.w   %d1
    beq.s   .Lsprite_count_skip

    addq.w  #1, %d6

.Lsprite_count_skip:
    adda.w  #8, %a0
    adda.w  #2, %a3
    dbra    %d7, .Lsprite_count_loop

    movea.l #0xE0FF11FE, %a0        /* Block-A base (write pass) */
    lea     wram_overlay+FRONTEND_RUNTIME_SPRITE_LUT_OFFSET, %a3
    lea     wram_overlay+FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET, %a4
    moveq   #17, %d7                /* 18 entries */
    moveq   #0, %d5                 /* current written SAT entry index */

.Lsprite_commit_loop:
    move.w  2(%a0), %d0             /* word1: y */
    cmpi.w  #0x0180, %d0
    beq.s   .Lsprite_commit_skip

    addi.w  #0x0080, %d0            /* SAT y bias */

    move.w  (%a3), %d1              /* per-entry VRAM tile index from prepare step */
    tst.w   %d1
    beq.s   .Lsprite_commit_skip
    andi.w  #0x07FF, %d1
    ori.w   #0x8000, %d1
    or.w    (%a4), %d1              /* per-entry pal/flip bits from prepare step */

    move.w  6(%a0), %d2             /* word3: x */
    addi.w  #0x0080, %d2            /* SAT x bias */

    move.w  %d0, (%a2)              /* SAT word0: Y */
    cmpi.w  #1, %d6
    ble.s   .Lsprite_link_last

    move.w  %d5, %d3
    addq.w  #1, %d3
    andi.w  #0x007F, %d3
    ori.w   #0x0500, %d3
    bra.s   .Lsprite_link_ready

.Lsprite_link_last:
    move.w  #0x0500, %d3

.Lsprite_link_ready:
    move.w  %d3, (%a2)              /* SAT word1: size/link */
    move.w  %d1, (%a2)              /* SAT word2: tile/attr */
    move.w  %d2, (%a2)              /* SAT word3: X */
    addq.w  #1, %d5
    subq.w  #1, %d6

.Lsprite_commit_skip:
    adda.w  #8, %a0
    adda.w  #2, %a3
    adda.w  #2, %a4
    dbra    %d7, .Lsprite_commit_loop

    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

/*
 * PC080SN BG tilemap hot path.
 * Args (C ABI, all promoted to 32-bit):
 *   4(%sp):  dest_ptr
 *   8(%sp):  strip_index
 *  12(%sp):  dest_row (raw 0..31)
 *  16(%sp):  dest_col (0..63)
 * Returns:
 *   %d0 = updated dest_ptr
 */
genesistan_asm_tilemap_commit_bg:
    movem.l %d2-%d7/%a2-%a6,-(%sp)

    movea.l #0xC00004, %a5          /* VDP control port */
    movea.l #0xC00000, %a6          /* VDP data port */
    move.w  #0x8F02, (%a5)          /* auto-increment = 2 bytes */

    lea     genesistan_arcade_workram_words+PC080SN_DESC_LIST_OFFSET, %a0
    lea     rastan_maincpu, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3

    move.l  48(%sp), %d5            /* dest_ptr accumulator */
    move.l  52(%sp), %d7            /* strip_index */
    move.l  56(%sp), %d1            /* dest_row (raw) */
    move.l  60(%sp), %d2            /* dest_col */
    andi.w  #0x001F, %d1
    andi.w  #0x003F, %d2

    moveq   #15, %d6                /* 16 descriptors */

.Lpc080sn_bg_desc_loop:
    move.l  (%a0)+, %d3             /* desc_addr */
    btst    #0, %d3
    bne     .Lpc080sn_bg_invalid
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lpc080sn_bg_invalid

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4              /* attr_word */
    move.w  2(%a4), %d3             /* table_base (u16) */
    cmpi.w  #0x7FE0, %d3
    bhi     .Lpc080sn_bg_invalid

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
    move.w  %d0, -(%sp)             /* attr partial */

    moveq   #3, %d4
.Lpc080sn_bg_row_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    cmpi.w  #4, %d0
    blo     .Lpc080sn_bg_skip_write

    subi.w  #4, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    addi.w  #0xC000, %d0

    move.w  %d4, -(%sp)
    move.w  %d0, %d4
    andi.w  #0x3FFF, %d0
    lsl.l   #8, %d0
    lsl.l   #8, %d0
    lsr.w   #8, %d4
    lsr.w   #6, %d4
    andi.w  #0x0003, %d4
    or.w    %d4, %d0
    ori.l   #0x40000003, %d0
    move.l  %d0, (%a5)
    move.w  %d3, (%a6)
    move.w  (%sp)+, %d4

.Lpc080sn_bg_skip_write:
    adda.w  #8, %a4
    addq.w  #1, %d1
    andi.w  #0x001F, %d1
    dbra    %d4, .Lpc080sn_bg_row_loop

    addq.l  #2, %sp
    bra     .Lpc080sn_bg_desc_done

.Lpc080sn_bg_invalid:
    addq.w  #4, %d1
    andi.w  #0x001F, %d1

.Lpc080sn_bg_desc_done:
    addi.l  #0x00000400, %d5
    dbra    %d6, .Lpc080sn_bg_desc_loop

    move.l  %d5, %d0
    movem.l (%sp)+,%d2-%d7/%a2-%a6
    rts

/*
 * PC080SN FG tilemap hot path.
 * Args/return contract matches genesistan_asm_tilemap_commit_bg.
 */
genesistan_asm_tilemap_commit_fg:
    movem.l %d2-%d7/%a2-%a6,-(%sp)

    movea.l #0xC00004, %a5          /* VDP control port */
    movea.l #0xC00000, %a6          /* VDP data port */
    move.w  #0x8F02, (%a5)          /* auto-increment = 2 bytes */

    lea     genesistan_arcade_workram_words+PC080SN_DESC_LIST_OFFSET, %a0
    lea     rastan_maincpu, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3

    move.l  48(%sp), %d5            /* dest_ptr accumulator */
    move.l  52(%sp), %d7            /* strip_index */
    move.l  56(%sp), %d1            /* dest_row (raw) */
    move.l  60(%sp), %d2            /* dest_col */
    andi.w  #0x0003, %d7
    andi.w  #0x001F, %d1
    andi.w  #0x003F, %d2

    moveq   #15, %d6                /* 16 descriptors */

.Lpc080sn_fg_desc_loop:
    move.l  (%a0)+, %d3             /* desc_addr */
    btst    #0, %d3
    bne     .Lpc080sn_fg_invalid
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lpc080sn_fg_invalid

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4              /* attr_word */
    move.w  2(%a4), %d3             /* table_base (u16) */
    cmpi.w  #0x7FE0, %d3
    bhi     .Lpc080sn_fg_invalid

    movea.l %a1, %a4
    move.w  %d3, %d0
    andi.l  #0x0000FFFF, %d0
    adda.l  %d0, %a4
    move.w  %d7, %d0
    lsl.w   #3, %d0
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
    move.w  %d0, -(%sp)             /* attr partial */

    moveq   #3, %d4
.Lpc080sn_fg_col_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    cmpi.w  #4, %d0
    blo     .Lpc080sn_fg_skip_write

    subi.w  #4, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    addi.w  #0xE000, %d0

    move.w  %d4, -(%sp)
    move.w  %d0, %d4
    andi.w  #0x3FFF, %d0
    lsl.l   #8, %d0
    lsl.l   #8, %d0
    lsr.w   #8, %d4
    lsr.w   #6, %d4
    andi.w  #0x0003, %d4
    or.w    %d4, %d0
    ori.l   #0x40000003, %d0
    move.l  %d0, (%a5)
    move.w  %d3, (%a6)
    move.w  (%sp)+, %d4

.Lpc080sn_fg_skip_write:
    adda.w  #2, %a4
    addq.w  #1, %d2
    cmpi.w  #64, %d2
    blo     .Lpc080sn_fg_no_wrap
    moveq   #0, %d2
    addq.w  #1, %d1
    andi.w  #0x001F, %d1

.Lpc080sn_fg_no_wrap:
    addi.l  #4, %d5
    dbra    %d4, .Lpc080sn_fg_col_loop

    addq.l  #2, %sp
    bra     .Lpc080sn_fg_desc_done

.Lpc080sn_fg_invalid:
    addi.l  #0x10, %d5
    addi.w  #4, %d2
    cmpi.w  #64, %d2
    blo     .Lpc080sn_fg_desc_done
    subi.w  #64, %d2
    addq.w  #1, %d1
    andi.w  #0x001F, %d1

.Lpc080sn_fg_desc_done:
    dbra    %d6, .Lpc080sn_fg_desc_loop

    move.l  %d5, %d0
    movem.l (%sp)+,%d2-%d7/%a2-%a6
    rts

/*
 * PC080SN block-write hot path (0x5A4DE replacement).
 * Entry register contract (arcade routine):
 *   d0.w = rows per column
 *   d1.w = columns
 *   d2.w = attr word
 *   a0   = source ROM words (tile indices)
 *   a1   = destination C-window pointer
 *
 * Common path:
 *   - assembly-only A0 range check vs current scene bounds
 *   - direct VDP nametable writes via LUT + attr LUT
 * Rare path:
 *   - call genesistan_bulk_preload_check(a0) only on range miss
 */
genesistan_bulk_tilemap_commit:
    movem.l %d2-%d7/%a2-%a6,-(%sp)

    cmp.l   genesistan_scene_a0_hi, %a0
    bhi     .Lbulk_scene_range_miss
    cmp.l   genesistan_scene_a0_lo, %a0
    blo     .Lbulk_scene_range_miss
    bra     .Lbulk_scene_range_ok

.Lbulk_scene_range_miss:
    movem.l %d0-%d2/%a0-%a1, -(%sp)
    move.l  %a0, -(%sp)
    jsr     genesistan_bulk_preload_check
    addq.l  #4, %sp
    movem.l (%sp)+, %d0-%d2/%a0-%a1

.Lbulk_scene_range_ok:
    move.l  %a1, %d7
    andi.l  #0x00FFFFFF, %d7

    cmpi.l  #0x00C00000, %d7
    blo     .Lbulk_exit
    cmpi.l  #0x00C04000, %d7
    blo     .Lbulk_bg_plane
    cmpi.l  #0x00C08000, %d7
    blo     .Lbulk_exit
    cmpi.l  #0x00C0C000, %d7
    blo     .Lbulk_fg_plane
    bra     .Lbulk_exit

.Lbulk_bg_plane:
    subi.l  #0x00C00000, %d7
    move.w  #0xC000, %d6
    bra     .Lbulk_dest_ready

.Lbulk_fg_plane:
    subi.l  #0x00C08000, %d7
    move.w  #0xE000, %d6

.Lbulk_dest_ready:
    btst    #0, %d7
    bne     .Lbulk_exit
    btst    #1, %d7
    bne     .Lbulk_exit

    lsr.l   #2, %d7
    move.w  %d7, %d4
    andi.w  #0x003F, %d4            /* row within column (column-major decode) */
    lsr.l   #6, %d7
    move.w  %d7, %d5
    andi.w  #0x003F, %d5            /* column index */
    andi.w  #0x001F, %d4            /* 32-row plane wrap */
    move.w  %d4, %a4                /* preserve row start */

    tst.w   %d0
    beq     .Lbulk_exit
    tst.w   %d1
    beq     .Lbulk_exit

    move.w  %d2, %d7                /* preserve incoming attr word */
    move.w  %d0, %d3                /* rows loop count */
    subq.w  #1, %d3
    move.w  %d1, %d2                /* columns loop count */
    subq.w  #1, %d2

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    movea.l #0xC00004, %a5
    movea.l #0xC00000, %a6
    move.w  #0x8F02, (%a5)

    move.w  %d7, %d4                /* attr LUT key */
    andi.w  #0x0003, %d4
    move.w  %d7, %d1
    lsr.w   #8, %d1
    lsr.w   #6, %d1                 /* hflip -> key bit2 */
    andi.w  #0x0001, %d1
    lsl.w   #2, %d1
    or.w    %d1, %d4
    move.w  %d7, %d1
    lsr.w   #8, %d1
    lsr.w   #7, %d1                 /* vflip -> key bit3 */
    andi.w  #0x0001, %d1
    lsl.w   #3, %d1
    or.w    %d1, %d4
    move.w  %d7, %d1
    lsr.w   #8, %d1
    lsr.w   #5, %d1                 /* priority -> key bit4 */
    andi.w  #0x0001, %d1
    lsl.w   #4, %d1
    or.w    %d1, %d4
    add.w   %d4, %d4
    move.w  0(%a3,%d4.w), %d7       /* attr partial */

.Lbulk_col_loop:
    move.w  %a4, %d0                /* row cursor */
    move.w  %d3, %d1                /* row loop counter */

.Lbulk_row_loop:
    move.w  (%a0)+, %d4
    andi.w  #0x3FFF, %d4
    add.w   %d4, %d4
    move.w  0(%a2,%d4.w), %d4
    or.w    %d7, %d4

    cmpi.w  #4, %d0
    blo.s   .Lbulk_skip_write

    move.w  %d1, -(%sp)
    move.w  %d4, -(%sp)
    move.w  %d0, %d1
    subi.w  #4, %d1
    lsl.w   #7, %d1
    add.w   %d5, %d1
    add.w   %d5, %d1
    add.w   %d6, %d1

    move.w  %d1, %d4
    andi.w  #0x3FFF, %d1
    lsl.l   #8, %d1
    lsl.l   #8, %d1
    lsr.w   #8, %d4
    lsr.w   #6, %d4
    andi.w  #0x0003, %d4
    or.w    %d4, %d1
    ori.l   #0x40000003, %d1
    move.l  %d1, (%a5)
    move.w  (%sp)+, (%a6)
    move.w  (%sp)+, %d1

.Lbulk_skip_write:
    addq.w  #1, %d0
    andi.w  #0x001F, %d0
    dbra    %d1, .Lbulk_row_loop

    addq.w  #1, %d5
    andi.w  #0x003F, %d5
    dbra    %d2, .Lbulk_col_loop

.Lbulk_exit:
    movem.l (%sp)+,%d2-%d7/%a2-%a6
    rts

genesistan_run_original_startup_common:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr (0x03AE86 + ARCADE_ROM_BASE)
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_run_original_frontend_tick:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    lea genesistan_arcade_workram_words, %a5
    moveq #0, %d0
    move.l #genesistan_frontend_tick_return, -(%sp)
    move.w %sr, -(%sp)
    jmp (0x03A008 + ARCADE_ROM_BASE)

genesistan_frontend_tick_return:
    move.l %a0, genesistan_arcade_last_a0   /* capture sprite ptr before restore (Build 109) */
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

/*
 * Lean arcade tick — called from _VINT_arcade_mode where registers are
 * already saved by the interrupt handler. Skips the redundant
 * movem.l save/restore that the full trampoline performs.
 */
genesistan_run_arcade_tick_lean:
    lea genesistan_arcade_workram_words, %a5
    moveq #0, %d0
    move.l #.Llean_tick_return, -(%sp)
    move.w %sr, -(%sp)
    jmp (0x03A008 + ARCADE_ROM_BASE)
.Llean_tick_return:
    move.l %a0, genesistan_arcade_last_a0
    rts

/*
 * C-callable title init sequence. Runs the arcade's title screen
 * initialization code that was never being reached through the V-Int
 * handler path. Sets up A5 (workram pointer) and calls the same
 * subroutines as genesistan_startup_common_continue_normal.
 */
genesistan_run_title_init_sequence:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    lea genesistan_arcade_workram_words, %a5
    move.w #1, genesistan_startup_result_code
    move.w #0x00EF, %d0
    jsr (0x03F084 + 24 + ARCADE_ROM_BASE)  /* +24 shift: 12 replacements before 0x3F084 */
    move.w #0x00AA, 74(%a5)
    jsr (0x03B8B0 + 18 + ARCADE_ROM_BASE)  /* +18 shift: 9 replacements before 0x3B8B0 */
    jsr (0x03B098 + 18 + ARCADE_ROM_BASE)  /* +18 shift: 9 replacements before 0x3B098 */
    jsr (0x03ADD8 + 18 + ARCADE_ROM_BASE)  /* +18 shift: 9 replacements before 0x3ADD8 */
    jsr (0x03AE28 + 18 + ARCADE_ROM_BASE)  /* +18 shift: 9 replacements before 0x3AE28 */
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_startup_common_continue_normal:
    move.w #1, genesistan_startup_result_code
    move.w #0x00EF, %d0
    jsr (0x03F084 + ARCADE_ROM_BASE)
    move.w #0x00AA, 74(%a5)
    jsr (0x03B8B0 + ARCADE_ROM_BASE)
    jsr (0x03B098 + ARCADE_ROM_BASE)
    jsr (0x03ADD8 + ARCADE_ROM_BASE)
    jsr (0x03AE28 + ARCADE_ROM_BASE)
    jmp genesistan_startup_common_exit_normal

genesistan_startup_common_exit_normal:
    addq.l #4,%sp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_startup_common_exit_test:
    addq.l #4,%sp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

#else

genesistan_run_original_startup_common:
    rts

genesistan_run_original_frontend_tick:
    rts

genesistan_run_arcade_tick_lean:
    rts

genesistan_startup_common_continue_normal:
    rts

genesistan_run_title_init_sequence:
    rts

genesistan_startup_common_exit_normal:
    rts

genesistan_startup_common_exit_test:
    rts

genesistan_sprite_commit_asm:
    rts

genesistan_palette_commit_asm:
    rts

genesistan_render_sprites_vdp_asm:
    rts

genesistan_asm_tilemap_commit_bg:
    move.l 4(%sp), %d0
    rts

genesistan_asm_tilemap_commit_fg:
    move.l 4(%sp), %d0
    rts

genesistan_bulk_tilemap_commit:
    rts

#endif

    .section .bss.patcher,"aw",@nobits
    .balign 2
arcade_vblank_active:
    .space 2
