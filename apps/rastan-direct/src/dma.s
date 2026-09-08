    .section .text,"ax"

/* ============================================================================
 * dma.s — Central Genesis VBlank DMA / VDP publication (Rainbow-Islands model)
 *
 * Build 0343: this module owns the ONE per-frame VDP publication PHASE. During
 * normal display-on runtime, `dma_publish_frame` is the single point at which
 * the completed staged Genesis state reaches the VDP. It runs at the start of
 * the native VBlank service (`_vblank_service`), before the game/arcade tick
 * resumes; the arcade tick then only *stages* the next frame's state and issues
 * NO DMA of its own.
 *
 * Rainbow Islands retail-Genesis model (build/rainbow_islands_genesis.disasm.txt,
 * handler 0x0380-0x041A): final graphics state lives in WRAM; VBlank runs a
 * bounded publication phase; SAT + scroll published every frame; palette / tiles
 * / tilemap conditional. This is the consumer half of the project target shape:
 *   arcade decision -> native production -> staged buffers -> THIS publisher -> VDP.
 *
 * NOTE (Build 0343 scope): this first step centralizes the publication *phase*
 * and its ordering. The individual commit bodies still live in their producer
 * files and are invoked ONLY from here (no other site calls them during runtime),
 * so DMA timing is centralized now; physically relocating each commit body into
 * dma.s (for static single-owner enforcement) and the palette flag / plane
 * coalescing / display-off bracket are the subsequent builds in this task.
 * ============================================================================ */

    .include "pc090oj_config.inc"

    .equ VDP_CTRL_PORT,        0x00C00004
    .equ VDP_CTRL,             0x00C00004
    .equ VDP_DATA,             0x00C00000
    .equ VDP_REG1_DISPLAY_OFF, 0x8134   /* reg1: display OFF, VINT on, DMA on, M5 */
    .equ VDP_REG1_DISPLAY_ON,  0x8174   /* reg1: display ON */

    /* Commit routines still living in their producer subsystems, invoked ONLY from here.
     * Each computes source/dest/length for the completed frame and issues its DMA through the
     * dma.s-owned primitives below (vdp_dma_words_to_vram); the CRAM palette DMA body itself now
     * lives here.  No production source outside dma.s issues a VDP DMA trigger during normal runtime
     * (crash_handler.s / bk_crash_handler.s are error-path exceptions, not normal runtime). */
    .extern vdp_commit_tiles_if_dirty
    .extern vdp_commit_bg_strips_if_dirty
    .extern vdp_commit_fg_narrow_strips
    .extern vdp_commit_sprites_vram
    .extern vdp_commit_scroll

    .extern staged_palette_words
    .extern palette_pending

    .global dma_publish_frame
    .global dma_words_to_vram
    .global dma_words_to_vram_noai
    .global vdp_dma_words_to_vram    /* legacy symbol name kept for existing callers */
    .global vdp_commit_palette

/* dma_publish_frame — the single VBlank publication phase.
 * Preconditions: every staged buffer (palette/tiles/planes/SAT/scroll) holds the
 * completed frame; the SAT has been staged (the caller runs the producer guard
 * `vdp_prepare_sprites` first). Publishes them to the VDP in a fixed order and
 * returns. After this returns, NO further runtime DMA may occur this frame. */
/* Build 0354: VBlank per-commit accounting.  DIAG_VBLANK_ACCOUNT samples the VDP V-counter
 * (0xC00008 high byte) before and after each commit into vblank_vc[0..6], so a read-only trace can
 * attribute the publication cost per commit (consecutive deltas = scanlines that commit consumed,
 * V wraps 0..261).  Negligible cost (one word read + byte store per point); no rendering effect. */
.macro VC_MARK n
    move.w  0x00C00008, %d0
    lsr.w   #8, %d0
    move.b  %d0, vblank_vc + \n
.endm

dma_publish_frame:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
.if RASTAN_VBLANK_DISPLAY_OFF
    /* Build 0344 display-off variant (Rainbow model): blank the display for the publication phase so
     * VRAM/CRAM writes run at full forced-blank bandwidth and cannot touch active scanlines.  SAFE only
     * once the whole phase fits the vblank window; before that it visibly blanks part of the picture
     * (a useful overrun diagnostic).  Display-ON variant leaves this out (current behaviour). */
    move.w  #VDP_REG1_DISPLAY_OFF, VDP_CTRL_PORT
.endif
    VC_MARK 0
    bsr     vdp_commit_palette              /* CRAM */
    VC_MARK 1
    bsr     vdp_commit_tiles_if_dirty       /* VRAM tile PIO (dirty) */
    VC_MARK 2
    bsr     vdp_commit_bg_strips_if_dirty   /* Plane B rows (DMA, dirty) */
    VC_MARK 3
    bsr     vdp_commit_fg_narrow_strips     /* Plane A narrow PIO + column PIO + dirty rows (DMA) */
    VC_MARK 4
    bsr     vdp_commit_sprites_vram         /* sprite pattern DMA + SAT DMA */
    VC_MARK 5
    bsr     vdp_commit_scroll               /* HScroll / VSRAM */
    VC_MARK 6
.if RASTAN_VBLANK_DISPLAY_OFF
    move.w  #VDP_REG1_DISPLAY_ON, VDP_CTRL_PORT
.endif
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

    .section .bss
    .align 2
    .global vblank_vc
vblank_vc:
    .space 8
    .section .text,"ax"

/* ============================================================================
 * DMA hardware-programming primitives — the SINGLE owner of VDP DMA triggers.
 *
 * Build 0345: relocated here from vdp_comm.s so every normal-runtime DMA that
 * reaches the VDP is programmed by code in this file.  Producer subsystems
 * (plane strips, FG narrow cache, sprite pipeline, palette staging) compute the
 * source/dest/length for the completed frame and call these primitives; they do
 * not write DMA registers or issue a DMA trigger themselves.
 * ============================================================================ */

/* VRAM word DMA.  in: d0 = VRAM byte dest, d1 = word count, a0 = 68k source.
 * Triggers a 68k->VRAM DMA.  Clobbers d1-d3, a1.
 *
 * Two entry points, same body:
 *   vdp_dma_words_to_vram / dma_words_to_vram  -- also forces autoinc=2 first
 *       (plane strips + FG cache: defensive, in case the arcade tick left a
 *        different autoinc during its own PIO writes).
 *   dma_words_to_vram_noai                      -- skips the autoinc set for
 *       callers that run after a plane DMA has already set autoinc=2 (the sprite
 *       cell + SAT commits, which historically issued no autoinc write of their
 *       own).  This keeps the sprite publication byte-for-byte / cycle-for-cycle
 *       identical to Build 0344 so it does not perturb epoch-transition timing. */
dma_words_to_vram_noai:
    movea.l #VDP_CTRL, %a1
    bra.s   .Ldwtv_len
dma_words_to_vram:
vdp_dma_words_to_vram:
    movea.l #VDP_CTRL, %a1
    move.w  #0x8F02, (%a1)
.Ldwtv_len:
    move.w  %d1, %d2
    andi.w  #0x00FF, %d2
    ori.w   #0x9300, %d2
    move.w  %d2, (%a1)
    move.w  %d1, %d2
    lsr.w   #8, %d2
    ori.w   #0x9400, %d2
    move.w  %d2, (%a1)
    move.l  %a0, %d3
    lsr.l   #1, %d3
    move.w  %d3, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9500, %d1
    move.w  %d1, (%a1)
    move.l  %d3, %d1
    lsr.l   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9600, %d1
    move.w  %d1, (%a1)
    move.l  %d3, %d1
    moveq   #16, %d2
    lsr.l   %d2, %d1
    andi.w  #0x007F, %d1
    ori.w   #0x9700, %d1
    move.w  %d1, (%a1)
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d3
    lsr.l   #8, %d3
    lsr.l   #6, %d3
    andi.l  #0x00000003, %d3
    ori.l   #0x40000080, %d1
    or.l    %d3, %d1
    move.l  %d1, (%a1)
    rts

/* CRAM palette DMA (Build 0336 model, relocated Build 0345): publish the full 64-word staged
 * palette to CRAM by ONE 68k->CRAM DMA.  Source = staged_palette_words (WRAM), length = 64 words,
 * destination = CRAM word 0, autoinc 2.  Called unconditionally, early, each VBlank -- no
 * palette_dirty.  Clobbers d1-d3/a1. */
vdp_commit_palette:
    tst.b   palette_pending
    beq.s   .Lpal_none
    movea.l #VDP_CTRL, %a1
    move.w  #0x8F02, (%a1)              /* reg 0x0F: autoincrement 2 */
    move.w  #0x9340, (%a1)              /* reg 0x13: DMA length low  = 64 words */
    move.w  #0x9400, (%a1)              /* reg 0x14: DMA length high = 0 */
    move.l  #staged_palette_words, %d3
    lsr.l   #1, %d3                     /* DMA source = word address */
    move.w  %d3, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9500, %d1
    move.w  %d1, (%a1)                  /* reg 0x15: source low */
    move.l  %d3, %d1
    lsr.l   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9600, %d1
    move.w  %d1, (%a1)                  /* reg 0x16: source mid */
    move.l  %d3, %d1
    moveq   #16, %d2
    lsr.l   %d2, %d1
    andi.w  #0x007F, %d1
    ori.w   #0x9700, %d1
    move.w  %d1, (%a1)                  /* reg 0x17: source high + mode 00 (68k->VDP) */
    move.l  #0xC0000080, (%a1)          /* CRAM write addr 0 + DMA trigger */
    clr.b   palette_pending
.Lpal_none:
    rts
