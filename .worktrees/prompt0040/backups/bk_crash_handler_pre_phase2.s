    .section .text.boot,"ax"

    /* ================================================================
     * Screenshot-first exception handler.
     *
     * PRIMARY artifact is the ON-SCREEN report (Tighe plays normally,
     * an exception occurs, he screenshots the screen).  The WRAM crash
     * record is supplemental only.
     *
     * Entry contract (Part 1): every vector stub writes ONLY the vector
     * number to WRAM (immediate -> memory) and branches.  No register is
     * touched before _crash_common's `movem.l %d0-%d7/%a0-%a6` snapshot,
     * so the ORIGINAL fault-time D0-D7 and A0-A6 are captured intact.
     * (The old design did `moveq #vec,%d0` in the stub -- destroying D0 --
     * and then clobbered D1-D5/A0/A1 in the common body before saving.)
     * ================================================================ */

    .global _crash_stub_bus_error
    .global _crash_stub_address_error
    .global _crash_stub_illegal
    .global _crash_stub_zero_divide
    .global _crash_stub_chk
    .global _crash_stub_trapv
    .global _crash_stub_privilege
    .global _crash_stub_trace
    .global _crash_stub_line_a
    .global _crash_stub_line_f
    .global _crash_stub_trap_00
    .global _crash_stub_trap_01
    .global _crash_stub_trap_02
    .global _crash_stub_trap_03
    .global _crash_stub_trap_04
    .global _crash_stub_trap_05
    .global _crash_stub_trap_06
    .global _crash_stub_trap_07
    .global _crash_stub_trap_08
    .global _crash_stub_trap_09
    .global _crash_stub_trap_10
    .global _crash_stub_trap_11
    .global _crash_stub_trap_12
    .global _crash_stub_trap_13
    .global _crash_stub_trap_14
    .global _crash_stub_trap_15
    .global _crash_stub_other
    .global _crash_common
    .global genesistan_crash_handler_end

    /* --- Supplemental WRAM crash record (secondary evidence) --------- */
    .equ CRASH_RECORD_BASE,       0x00FF6800
    .equ CRASH_ACTIVE_FLAG,       0x00FF6800   /* byte */
    .equ CRASH_EXCEPTION_TYPE,    0x00FF6802   /* word: vector number */
    .equ CRASH_STACKED_SR,        0x00FF6804   /* word */
    .equ CRASH_STACKED_PC,        0x00FF6806   /* long: GEN PC (runtime Genesis PC) */
    .equ CRASH_FRAME_SP,          0x00FF680C   /* long: exception-frame SSP at entry */
    .equ CRASH_USP,               0x00FF6810   /* long */
    /* movem.l %d0-%d7/%a0-%a6 target: 15 contiguous longs, D0..D7 then A0..A6 */
    .equ CRASH_D0,                0x00FF6814
    .equ CRASH_D1,                0x00FF6818
    .equ CRASH_D2,                0x00FF681C
    .equ CRASH_D3,                0x00FF6820
    .equ CRASH_D4,                0x00FF6824
    .equ CRASH_D5,                0x00FF6828
    .equ CRASH_D6,                0x00FF682C
    .equ CRASH_D7,                0x00FF6830
    .equ CRASH_A0,                0x00FF6834
    .equ CRASH_A1,                0x00FF6838
    .equ CRASH_A2,                0x00FF683C
    .equ CRASH_A3,                0x00FF6840
    .equ CRASH_A4,                0x00FF6844
    .equ CRASH_A5,                0x00FF6848
    .equ CRASH_A6,                0x00FF684C
    .equ CRASH_FAULT_ADDR,        0x00FF6850   /* long: bus/addr fault address */
    .equ CRASH_ACCESS_WORD,       0x00FF6854   /* word: bus/addr access/status word */
    .equ CRASH_INSTR_REG,         0x00FF6856   /* word: bus/addr instruction register */
    .equ CRASH_GS_00,             0x00FF6858   /* word: a5+0x00 */
    .equ CRASH_GS_02,             0x00FF685A   /* word: a5+0x02 */
    .equ CRASH_GS_04,             0x00FF685C   /* word: a5+0x04 */
    .equ CRASH_GS_34,             0x00FF685E   /* word: a5+0x34 */
    .equ CRASH_GS_200,            0x00FF6860   /* word: a5+0x200 */
    .equ CRASH_A5_VALID,          0x00FF6862   /* word: 1 if A5 == 0x00FF0000 */

    .equ EXPECTED_A5_BASE,        0x00FF0000

    /* --- Genesis-PC classification ranges (from address_map.json) ---
     * preserved_vectors 0x000000..0x00117E ; arcade_copy 0x00117E..0x0600F4 ;
     * genesis_only 0x0600F4..0x184A34 (ROM end). No arithmetic ARC PC is
     * fabricated; only a coarse SOURCE region is shown. */
    .equ MAP_ARCADE_START,        0x00117E
    .equ MAP_ARCADE_END,          0x0600F4
    .equ MAP_ROM_END,             0x184A34

    /* --- crash-screen VDP layout (self-contained, not the game's) --- */
    .equ CRASH_PLANE_A,           0x0000E000
    .equ CRASH_PLANE_B,           0x0000C000
    .equ CRASH_WINDOW,            0x0000F000
    .equ CRASH_SAT,               0x0000F800
    .equ CRASH_HSCROLL,           0x0000FC00
    .equ CRASH_FONT_VRAM,         0x00008000   /* tile index 0x400 */
    .equ CRASH_BLANK_CELL,        0x8400       /* priority + font tile 0x400 (space) */

/* ---- vector stubs: write vector number only, then branch ---------- */
_crash_stub_bus_error:      move.w #2, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_address_error:  move.w #3, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_illegal:        move.w #4, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_zero_divide:    move.w #5, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_chk:            move.w #6, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trapv:          move.w #7, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_privilege:      move.w #8, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trace:          move.w #9, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_line_a:         move.w #10, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_line_f:         move.w #11, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_00:        move.w #32, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_01:        move.w #33, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_02:        move.w #34, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_03:        move.w #35, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_04:        move.w #36, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_05:        move.w #37, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_06:        move.w #38, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_07:        move.w #39, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_08:        move.w #40, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_09:        move.w #41, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_10:        move.w #42, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_11:        move.w #43, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_12:        move.w #44, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_13:        move.w #45, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_14:        move.w #46, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_trap_15:        move.w #47, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common
_crash_stub_other:          move.w #63, CRASH_EXCEPTION_TYPE
                            bra.w  _crash_common

/* ---- common entry: capture ORIGINAL state before any reuse -------- */
_crash_common:
    tst.b   CRASH_ACTIVE_FLAG           /* re-entry guard: keep the FIRST report */
    bne.w   .Lminimal_halt
    movem.l %d0-%d7/%a0-%a6, CRASH_D0   /* snapshot: memory dest does not alter regs */
    move.b  #1, CRASH_ACTIVE_FLAG
    move.w  #0x2700, %sr                /* mask interrupts (does not affect stacked SR) */

    move.l  %sp, CRASH_FRAME_SP         /* SSP still points at the CPU exception frame */
    move.l  %usp, %a0
    move.l  %a0, CRASH_USP

    /* --- decode the 68000 exception frame ---------------------------
     * Normal (group 1/2): +0 SR (word), +2 PC (long).
     * Bus/Address error (group 0, vectors 2/3): +0 access/status word,
     * +2 access address (long), +6 instruction register (word),
     * +8 SR (word), +10 PC (long). */
    move.l  CRASH_FRAME_SP, %a0
    clr.l   CRASH_FAULT_ADDR
    clr.w   CRASH_ACCESS_WORD
    clr.w   CRASH_INSTR_REG
    move.w  CRASH_EXCEPTION_TYPE, %d0
    cmpi.w  #2, %d0
    beq.s   .Lgroup0_frame
    cmpi.w  #3, %d0
    beq.s   .Lgroup0_frame

    move.w  0(%a0), %d1
    move.l  2(%a0), %d2
    move.w  %d1, CRASH_STACKED_SR
    move.l  %d2, CRASH_STACKED_PC
    bra.s   .Lframe_done

.Lgroup0_frame:
    move.w  0(%a0), %d1
    move.w  %d1, CRASH_ACCESS_WORD
    move.l  2(%a0), %d2
    move.l  %d2, CRASH_FAULT_ADDR
    move.w  6(%a0), %d1
    move.w  %d1, CRASH_INSTR_REG
    move.w  8(%a0), %d1
    move.w  %d1, CRASH_STACKED_SR
    move.l  10(%a0), %d2
    move.l  %d2, CRASH_STACKED_PC

.Lframe_done:
    /* --- retained game-flow state (valid only if A5 is the WRAM base) */
    clr.w   CRASH_A5_VALID
    clr.w   CRASH_GS_00
    clr.w   CRASH_GS_02
    clr.w   CRASH_GS_04
    clr.w   CRASH_GS_34
    clr.w   CRASH_GS_200
    move.l  CRASH_A5, %d0
    cmpi.l  #EXPECTED_A5_BASE, %d0
    bne.s   .Lgamestate_done
    move.w  #1, CRASH_A5_VALID
    movea.l #EXPECTED_A5_BASE, %a0
    move.w  0x0000(%a0), CRASH_GS_00
    move.w  0x0002(%a0), CRASH_GS_02
    move.w  0x0004(%a0), CRASH_GS_04
    move.w  0x0034(%a0), CRASH_GS_34
    move.w  0x0200(%a0), CRASH_GS_200
.Lgamestate_done:

    lea     0x00FFF000, %sp             /* private handler stack, clear of the record */
    bsr     crash_present

.Lcrash_halt:
    stop    #0x2700
    bra.s   .Lcrash_halt

.Lminimal_halt:
    stop    #0x2700
    bra.s   .Lminimal_halt

/* ================================================================
 * crash_present: self-contained VDP clean-room + report.
 * No game VBlank/SAT/PC090OJ/PC080SN/tilemap/DMA/scroll staging.
 * ================================================================ */
crash_present:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* 1) display OFF while we rebuild everything */
    move.w  #0x8104, VDP_CTRL           /* reg1: display off, VINT off, DMA off */

    /* 2) crash-screen register layout */
    move.w  #0x8004, VDP_CTRL           /* reg0: no HINT */
    move.w  #0x8238, VDP_CTRL           /* reg2: plane A @ 0xE000 */
    move.w  #0x833C, VDP_CTRL           /* reg3: window @ 0xF000 */
    move.w  #0x8406, VDP_CTRL           /* reg4: plane B @ 0xC000 */
    move.w  #0x857C, VDP_CTRL           /* reg5: SAT @ 0xF800 */
    move.w  #0x8700, VDP_CTRL           /* reg7: backdrop = pal0/col0 */
    move.w  #0x8AFF, VDP_CTRL           /* reg10: hint counter */
    move.w  #0x8B00, VDP_CTRL           /* reg11: full-screen H+V scroll, no ext int */
    move.w  #0x8C81, VDP_CTRL           /* reg12: H40, no interlace/shadow */
    move.w  #0x8D3F, VDP_CTRL           /* reg13: hscroll table @ 0xFC00 */
    move.w  #0x8F02, VDP_CTRL           /* reg15: autoinc = 2 */
    move.w  #0x9001, VDP_CTRL           /* reg16: plane size 64x32 */
    move.w  #0x9100, VDP_CTRL           /* reg17: window X = 0 (disabled) */
    move.w  #0x9200, VDP_CTRL           /* reg18: window Y = 0 (disabled) */

    /* 3) zero ALL vertical scroll (VSRAM: 40 words) */
    move.l  #0x40000010, VDP_CTRL       /* VSRAM write, addr 0 */
    moveq   #0, %d0
    move.w  #39, %d7
.Lvsram_zero:
    move.w  %d0, VDP_DATA
    dbra    %d7, .Lvsram_zero

    /* 4) zero ALL horizontal scroll (HScroll table @ 0xFC00, whole screen) */
    move.l  #CRASH_HSCROLL, %d3
    moveq   #0, %d4
    move.w  #0x00E0, %d5                /* 224 words covers per-line H32/H40 */
    bsr     crash_vram_fill

    /* 5) clear Plane A / Plane B / Window name tables to a blank cell */
    move.l  #CRASH_PLANE_A, %d3
    move.w  #CRASH_BLANK_CELL, %d4
    move.w  #0x0800, %d5                /* 2048 cells (64x32) */
    bsr     crash_vram_fill

    move.l  #CRASH_PLANE_B, %d3
    move.w  #CRASH_BLANK_CELL, %d4
    move.w  #0x0800, %d5
    bsr     crash_vram_fill

    move.l  #CRASH_WINDOW, %d3
    move.w  #CRASH_BLANK_CELL, %d4
    move.w  #0x0800, %d5
    bsr     crash_vram_fill

    /* 6) clear the SAT: all sprites Y=0 (off-screen), link 0 */
    move.l  #CRASH_SAT, %d3
    moveq   #0, %d4
    move.w  #0x0140, %d5                /* 80 sprites * 4 words */
    bsr     crash_vram_fill

    /* 7) CRAM: deterministic, high-contrast (col0 black, col1 white) */
    move.l  #0xC0000000, VDP_CTRL
    move.w  #0x0000, VDP_DATA
    move.w  #0x0EEE, VDP_DATA

    /* 8) upload the self-contained crash font */
    bsr     crash_upload_font

    /* 9) draw the report */
    bsr     crash_render_report

    /* 10) NOW enable display (VINT still off: static screen) */
    move.w  #0x8144, VDP_CTRL
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

/* d3 = VRAM address, d4 = fill word, d5 = word count -------------- */
crash_vram_fill:
    move.l  %d3, %d0
    andi.l  #0x3FFF, %d0
    swap    %d0
    ori.l   #0x40000000, %d0
    move.l  %d3, %d1
    lsr.l   #7, %d1
    lsr.l   #7, %d1
    andi.l  #0x0003, %d1
    or.l    %d1, %d0
    move.l  %d0, VDP_CTRL
.Lvram_fill_loop:
    move.w  %d4, VDP_DATA
    subq.w  #1, %d5
    bne.s   .Lvram_fill_loop
    rts

crash_upload_font:
    move.l  #0x40000002, VDP_CTRL       /* VRAM write @ 0x8000 (tile 0x400) */
    lea     crash_font_1bpp(%pc), %a1
    move.w  #95, %d7
.Lfont_char_loop:
    move.w  #7, %d6
.Lfont_row_loop:
    moveq   #0, %d0
    move.b  (%a1)+, %d0
    moveq   #0, %d1
    moveq   #7, %d2
.Lexpand_bit:
    lsl.l   #4, %d1
    btst    %d2, %d0
    beq.s   .Lbit_zero
    ori.b   #1, %d1
.Lbit_zero:
    dbra    %d2, .Lexpand_bit
    move.l  %d1, VDP_DATA
    dbra    %d6, .Lfont_row_loop
    dbra    %d7, .Lfont_char_loop
    rts

/* ================================================================
 * crash_render_report -- draws the screenshot-first report.
 * ================================================================ */
crash_render_report:
    /* row 0: title + BUILD (automatic, generated build number) */
    moveq   #0, %d0
    moveq   #0, %d1
    lea     crash_title(%pc), %a1
    bsr     crash_puts_at
    moveq   #0, %d0
    moveq   #30, %d1                 /* "BUILD " cols 30-35 */
    lea     crash_lbl_build(%pc), %a1
    bsr     crash_puts_at
    moveq   #0, %d0
    moveq   #36, %d1                 /* 4-digit number cols 36-39 (fits H40) */
    lea     crash_build_number_str(%pc), %a1
    bsr     crash_puts_at

    /* row 2: exception name + vector */
    moveq   #0, %d0
    move.b  CRASH_EXCEPTION_TYPE+1, %d0
    bsr     crash_get_exception_name
    moveq   #2, %d0
    moveq   #0, %d1
    bsr     crash_puts_at
    moveq   #2, %d0
    moveq   #28, %d1
    lea     crash_lbl_vector(%pc), %a1
    bsr     crash_puts_at
    moveq   #2, %d0
    moveq   #35, %d1
    moveq   #0, %d2
    move.b  CRASH_EXCEPTION_TYPE+1, %d2
    bsr     crash_put_hex8_at

    /* row 3: GEN PC + SOURCE classification */
    moveq   #3, %d0
    moveq   #0, %d1
    lea     crash_lbl_genpc(%pc), %a1
    bsr     crash_puts_at
    moveq   #3, %d0
    moveq   #8, %d1
    move.l  CRASH_STACKED_PC, %d2
    bsr     crash_put_hex32_at
    moveq   #3, %d0
    moveq   #20, %d1
    lea     crash_lbl_src(%pc), %a1
    bsr     crash_puts_at
    moveq   #3, %d0
    moveq   #24, %d1
    bsr     crash_render_source

    /* row 4: ARC PC placeholder (never fabricated -- resolve offline) */
    moveq   #4, %d0
    moveq   #0, %d1
    lea     crash_lbl_arcpc(%pc), %a1
    bsr     crash_puts_at
    moveq   #4, %d0
    moveq   #8, %d1
    lea     crash_dashes8(%pc), %a1
    bsr     crash_puts_at
    moveq   #4, %d0
    moveq   #18, %d1
    lea     crash_lbl_arcpc_note(%pc), %a1
    bsr     crash_puts_at

    /* row 5: SR */
    moveq   #5, %d0
    moveq   #0, %d1
    lea     crash_lbl_sr(%pc), %a1
    bsr     crash_puts_at
    moveq   #5, %d0
    moveq   #8, %d1
    moveq   #0, %d2
    move.w  CRASH_STACKED_SR, %d2
    bsr     crash_put_hex16_at

    /* row 6: FAULT / ACCESS (only meaningful for bus/address error) */
    moveq   #0, %d6
    move.b  CRASH_EXCEPTION_TYPE+1, %d6
    cmpi.b  #2, %d6
    blo.s   .Lno_fault
    cmpi.b  #3, %d6
    bhi.s   .Lno_fault
    moveq   #6, %d0
    moveq   #0, %d1
    lea     crash_lbl_fault(%pc), %a1
    bsr     crash_puts_at
    moveq   #6, %d0
    moveq   #8, %d1
    move.l  CRASH_FAULT_ADDR, %d2
    bsr     crash_put_hex32_at
    moveq   #6, %d0
    moveq   #19, %d1
    lea     crash_lbl_access(%pc), %a1
    bsr     crash_puts_at
    moveq   #6, %d0
    moveq   #27, %d1
    moveq   #0, %d2
    move.w  CRASH_ACCESS_WORD, %d2
    bsr     crash_put_hex16_at
.Lno_fault:

    /* rows 8-10: data registers (original fault-time values) */
    moveq   #8, %d0
    lea     crash_lbl_d0(%pc), %a1
    move.l  CRASH_D0, %d2
    bsr     crash_reg_col0
    lea     crash_lbl_d1(%pc), %a1
    move.l  CRASH_D1, %d2
    bsr     crash_reg_col1
    lea     crash_lbl_d2(%pc), %a1
    move.l  CRASH_D2, %d2
    bsr     crash_reg_col2

    moveq   #9, %d0
    lea     crash_lbl_d3(%pc), %a1
    move.l  CRASH_D3, %d2
    bsr     crash_reg_col0
    lea     crash_lbl_d4(%pc), %a1
    move.l  CRASH_D4, %d2
    bsr     crash_reg_col1
    lea     crash_lbl_d5(%pc), %a1
    move.l  CRASH_D5, %d2
    bsr     crash_reg_col2

    moveq   #10, %d0
    lea     crash_lbl_d6(%pc), %a1
    move.l  CRASH_D6, %d2
    bsr     crash_reg_col0
    lea     crash_lbl_d7(%pc), %a1
    move.l  CRASH_D7, %d2
    bsr     crash_reg_col1

    /* rows 11-13: address registers (original fault-time values) */
    moveq   #11, %d0
    lea     crash_lbl_a0(%pc), %a1
    move.l  CRASH_A0, %d2
    bsr     crash_reg_col0
    lea     crash_lbl_a1(%pc), %a1
    move.l  CRASH_A1, %d2
    bsr     crash_reg_col1
    lea     crash_lbl_a2(%pc), %a1
    move.l  CRASH_A2, %d2
    bsr     crash_reg_col2

    moveq   #12, %d0
    lea     crash_lbl_a3(%pc), %a1
    move.l  CRASH_A3, %d2
    bsr     crash_reg_col0
    lea     crash_lbl_a4(%pc), %a1
    move.l  CRASH_A4, %d2
    bsr     crash_reg_col1
    lea     crash_lbl_a5(%pc), %a1
    move.l  CRASH_A5, %d2
    bsr     crash_reg_col2

    moveq   #13, %d0
    lea     crash_lbl_a6(%pc), %a1
    move.l  CRASH_A6, %d2
    bsr     crash_reg_col0

    /* row 14: frame SP + USP */
    moveq   #14, %d0
    moveq   #0, %d1
    lea     crash_lbl_framesp(%pc), %a1
    bsr     crash_puts_at
    moveq   #14, %d0
    moveq   #9, %d1
    move.l  CRASH_FRAME_SP, %d2
    bsr     crash_put_hex32_at
    moveq   #14, %d0
    moveq   #20, %d1
    lea     crash_lbl_usp(%pc), %a1
    bsr     crash_puts_at
    moveq   #14, %d0
    moveq   #24, %d1
    move.l  CRASH_USP, %d2
    bsr     crash_put_hex32_at

    /* rows 16-18: retained game-flow state */
    moveq   #16, %d0
    moveq   #0, %d1
    lea     crash_lbl_state(%pc), %a1
    bsr     crash_puts_at
    tst.w   CRASH_A5_VALID
    beq.w   .Lstate_invalid

    moveq   #17, %d0
    moveq   #0, %d1
    lea     crash_lbl_s00(%pc), %a1
    bsr     crash_puts_at
    moveq   #17, %d0
    moveq   #4, %d1
    moveq   #0, %d2
    move.w  CRASH_GS_00, %d2
    bsr     crash_put_hex16_at
    moveq   #17, %d0
    moveq   #10, %d1
    lea     crash_lbl_s02(%pc), %a1
    bsr     crash_puts_at
    moveq   #17, %d0
    moveq   #14, %d1
    moveq   #0, %d2
    move.w  CRASH_GS_02, %d2
    bsr     crash_put_hex16_at
    moveq   #17, %d0
    moveq   #20, %d1
    lea     crash_lbl_s04(%pc), %a1
    bsr     crash_puts_at
    moveq   #17, %d0
    moveq   #24, %d1
    moveq   #0, %d2
    move.w  CRASH_GS_04, %d2
    bsr     crash_put_hex16_at

    moveq   #18, %d0
    moveq   #0, %d1
    lea     crash_lbl_s34(%pc), %a1
    bsr     crash_puts_at
    moveq   #18, %d0
    moveq   #4, %d1
    moveq   #0, %d2
    move.w  CRASH_GS_34, %d2
    bsr     crash_put_hex16_at
    moveq   #18, %d0
    moveq   #10, %d1
    lea     crash_lbl_s200(%pc), %a1
    bsr     crash_puts_at
    moveq   #18, %d0
    moveq   #15, %d1
    moveq   #0, %d2
    move.w  CRASH_GS_200, %d2
    bsr     crash_put_hex16_at
    bra.s   .Lstate_done

.Lstate_invalid:
    moveq   #16, %d0
    moveq   #6, %d1
    lea     crash_lbl_a5invalid(%pc), %a1
    bsr     crash_puts_at
.Lstate_done:

    /* rows 20-23: small raw stack window from the frame SP (if in WRAM) */
    moveq   #20, %d0
    moveq   #0, %d1
    lea     crash_lbl_stack(%pc), %a1
    bsr     crash_puts_at

    move.l  CRASH_FRAME_SP, %d3
    andi.l  #0x00FFFFFE, %d3            /* force even; ignore high byte */
    move.l  %d3, %a2
    move.l  %a2, %d0
    cmpi.l  #0x00FF0000, %d0           /* only dump if SP is inside WRAM */
    blo.s   .Lstack_oor
    moveq   #0, %d7                     /* row counter */
.Lstack_row:
    moveq   #21, %d0
    add.w   %d7, %d0
    moveq   #0, %d1
    bsr     crash_set_cursor
    moveq   #0, %d6                     /* 3 longs per row */
.Lstack_col:
    move.l  (%a2)+, %d2
    bsr     crash_put_hex32_inline
    moveq   #' ', %d2
    bsr     crash_put_char_ascii
    addq.w  #1, %d6
    cmpi.w  #3, %d6
    blo.s   .Lstack_col
    addq.w  #1, %d7
    cmpi.w  #3, %d7
    blo.s   .Lstack_row
    bra.s   .Lreport_footer

.Lstack_oor:
    moveq   #21, %d0
    moveq   #0, %d1
    lea     crash_lbl_stack_oor(%pc), %a1
    bsr     crash_puts_at

.Lreport_footer:
    moveq   #26, %d0
    moveq   #0, %d1
    lea     crash_footer(%pc), %a1
    bsr     crash_puts_at
    rts

/* register-triple helpers: d0 = row (preserved), a1 = label, d2 = value */
crash_reg_col0:
    movem.l %d0/%d2, -(%sp)
    moveq   #0, %d1
    bsr     crash_puts_at
    movem.l (%sp)+, %d0/%d2
    move.l  %d0, -(%sp)
    moveq   #3, %d1
    bsr     crash_put_hex32_at
    move.l  (%sp)+, %d0
    rts
crash_reg_col1:
    movem.l %d0/%d2, -(%sp)
    moveq   #13, %d1
    bsr     crash_puts_at
    movem.l (%sp)+, %d0/%d2
    move.l  %d0, -(%sp)
    moveq   #16, %d1
    bsr     crash_put_hex32_at
    move.l  (%sp)+, %d0
    rts
crash_reg_col2:
    movem.l %d0/%d2, -(%sp)
    moveq   #26, %d1
    bsr     crash_puts_at
    movem.l (%sp)+, %d0/%d2
    move.l  %d0, -(%sp)
    moveq   #29, %d1
    bsr     crash_put_hex32_at
    move.l  (%sp)+, %d0
    rts

/* Draw the SOURCE token for CRASH_STACKED_PC at cursor (d0=row,d1=col). */
crash_render_source:
    move.l  CRASH_STACKED_PC, %d2
    lea     crash_src_genonly(%pc), %a1     /* < arcade_copy start => vectors/boot */
    cmpi.l  #MAP_ARCADE_START, %d2
    blo.s   .Lsrc_emit
    lea     crash_src_arcade(%pc), %a1      /* arcade-copied maincpu region */
    cmpi.l  #MAP_ARCADE_END, %d2
    blo.s   .Lsrc_emit
    lea     crash_src_genonly(%pc), %a1     /* native helper / wrapper region */
    cmpi.l  #MAP_ROM_END, %d2
    blo.s   .Lsrc_emit
    lea     crash_src_unknown(%pc), %a1     /* outside ROM (RAM/VDP/...) */
.Lsrc_emit:
    bsr     crash_puts_at
    rts

crash_get_exception_name:
    andi.w  #0x00FF, %d0
    cmpi.w  #63, %d0
    bhi.s   .Lexception_default
    lea     crash_vector_name_table(%pc), %a1
    lsl.w   #2, %d0
    move.l  0(%a1,%d0.w), %a1
    rts
.Lexception_default:
    lea     crash_name_other(%pc), %a1
    rts

/* --- shared text primitives (Plane A @ 0xE000, 64-cell rows) ------- */
crash_set_cursor:
    move.w  %d0, %d2
    mulu.w  #128, %d2
    move.w  %d1, %d3
    add.w   %d3, %d3
    add.w   %d3, %d2
    move.l  #CRASH_PLANE_A, %d0
    add.l   %d2, %d0
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1
    move.l  %d0, %d3
    lsr.l   #8, %d3
    lsr.l   #6, %d3
    andi.l  #0x00000003, %d3
    ori.l   #0x40000000, %d1
    or.l    %d3, %d1
    move.l  %d1, VDP_CTRL
    rts

crash_puts_at:
    bsr     crash_set_cursor
.Lputs_loop:
    moveq   #0, %d2
    move.b  (%a1)+, %d2
    beq.s   .Lputs_done
    bsr     crash_put_char_ascii
    bra.s   .Lputs_loop
.Lputs_done:
    rts

/* crash_set_cursor clobbers D2/D3 while computing the Plane-A VRAM address, but
 * D2 is ALSO the diagnostic value these wrappers must print.  Preserve D2 across
 * the cursor call so the value survives positioning (without this, every hex
 * field printed its own row/col cursor address instead of the captured value). */
crash_put_hex32_at:
    move.l  %d2, -(%sp)
    bsr     crash_set_cursor
    move.l  (%sp)+, %d2
    bsr     crash_put_hex32_inline
    rts
crash_put_hex16_at:
    move.l  %d2, -(%sp)
    bsr     crash_set_cursor
    move.l  (%sp)+, %d2
    bsr     crash_put_hex16_inline
    rts
crash_put_hex8_at:
    move.l  %d2, -(%sp)
    bsr     crash_set_cursor
    move.l  (%sp)+, %d2
    bsr     crash_put_hex8_inline
    rts

crash_put_hex32_inline:
    move.l  %d2, %d4
    moveq   #7, %d5
.Lhex32_loop:
    bsr     crash_extract_top_nibble
    bsr     crash_put_hex_nibble
    lsl.l   #4, %d4
    dbra    %d5, .Lhex32_loop
    rts
crash_put_hex16_inline:
    moveq   #0, %d4
    move.w  %d2, %d4
    swap    %d4
    moveq   #3, %d5
.Lhex16_loop:
    bsr     crash_extract_top_nibble
    bsr     crash_put_hex_nibble
    lsl.l   #4, %d4
    dbra    %d5, .Lhex16_loop
    rts
crash_put_hex8_inline:
    moveq   #0, %d4
    move.b  %d2, %d4
    lsl.w   #8, %d4
    swap    %d4
    moveq   #1, %d5
.Lhex8_loop:
    bsr     crash_extract_top_nibble
    bsr     crash_put_hex_nibble
    lsl.l   #4, %d4
    dbra    %d5, .Lhex8_loop
    rts

crash_extract_top_nibble:
    move.l  %d4, %d3
    swap    %d3
    lsr.w   #8, %d3
    lsr.b   #4, %d3
    move.b  %d3, %d2
    rts

crash_put_hex_nibble:
    andi.b  #0x0F, %d2
    cmpi.b  #9, %d2
    ble.s   .Lhex_digit
    addi.b  #7, %d2
.Lhex_digit:
    addi.b  #'0', %d2
    bsr     crash_put_char_ascii
    rts

crash_put_char_ascii:
    cmpi.b  #0x20, %d2
    blo.s   .Lchar_space
    cmpi.b  #0x7F, %d2
    bhi.s   .Lchar_space
    subi.b  #0x20, %d2
    bra.s   .Lchar_tile
.Lchar_space:
    moveq   #0, %d2
.Lchar_tile:
    andi.w  #0x00FF, %d2
    ori.w   #0x8400, %d2
    move.w  %d2, VDP_DATA
    rts

    .section .text.boot,"ax"
    .align 2

crash_title:            .asciz "RASTAN GENESIS CRASH"
crash_lbl_build:        .asciz "BUILD "
    /* crash_build_number_str is generated per build (Makefile) */
    .include "crash_build.inc"

crash_lbl_vector:       .asciz "VECTOR"
crash_lbl_genpc:        .asciz "GEN PC"
crash_lbl_arcpc:        .asciz "ARC PC"
crash_lbl_arcpc_note:   .asciz "MAP OFFLINE"
crash_lbl_src:          .asciz "SRC"
crash_lbl_sr:           .asciz "SR"
crash_lbl_fault:        .asciz "FAULT"
crash_lbl_access:       .asciz "ACCESS"
crash_dashes8:          .asciz "--------"

crash_src_arcade:       .asciz "ARCADE"
crash_src_genonly:      .asciz "GENONLY"
crash_src_unknown:      .asciz "UNKNOWN"

crash_lbl_d0: .asciz "D0"
crash_lbl_d1: .asciz "D1"
crash_lbl_d2: .asciz "D2"
crash_lbl_d3: .asciz "D3"
crash_lbl_d4: .asciz "D4"
crash_lbl_d5: .asciz "D5"
crash_lbl_d6: .asciz "D6"
crash_lbl_d7: .asciz "D7"
crash_lbl_a0: .asciz "A0"
crash_lbl_a1: .asciz "A1"
crash_lbl_a2: .asciz "A2"
crash_lbl_a3: .asciz "A3"
crash_lbl_a4: .asciz "A4"
crash_lbl_a5: .asciz "A5"
crash_lbl_a6: .asciz "A6"
crash_lbl_framesp: .asciz "FRAME SP"
crash_lbl_usp: .asciz "USP"

crash_lbl_state:     .asciz "STATE"
crash_lbl_a5invalid: .asciz "A5 INVALID (SEE A5 REG)"
crash_lbl_s00:  .asciz "+00"
crash_lbl_s02:  .asciz "+02"
crash_lbl_s04:  .asciz "+04"
crash_lbl_s34:  .asciz "+34"
crash_lbl_s200: .asciz "+200"

crash_lbl_stack:     .asciz "STACK"
crash_lbl_stack_oor: .asciz "SP OUT OF WRAM RANGE"
crash_footer:        .asciz "HALTED"

crash_name_other:           .asciz "OTHER EXCEPTION"
crash_name_bus_error:       .asciz "BUS ERROR"
crash_name_address_error:   .asciz "ADDRESS ERROR"
crash_name_illegal:         .asciz "ILLEGAL INSTR"
crash_name_zero_divide:     .asciz "ZERO DIVIDE"
crash_name_chk:             .asciz "CHK"
crash_name_trapv:           .asciz "TRAPV"
crash_name_privilege:       .asciz "PRIVILEGE"
crash_name_trace:           .asciz "TRACE"
crash_name_line_a:          .asciz "LINE 1010"
crash_name_line_f:          .asciz "LINE 1111"
crash_name_trap_00:         .asciz "TRAP #0"
crash_name_trap_01:         .asciz "TRAP #1"
crash_name_trap_02:         .asciz "TRAP #2"
crash_name_trap_03:         .asciz "TRAP #3"
crash_name_trap_04:         .asciz "TRAP #4"
crash_name_trap_05:         .asciz "TRAP #5"
crash_name_trap_06:         .asciz "TRAP #6"
crash_name_trap_07:         .asciz "TRAP #7"
crash_name_trap_08:         .asciz "TRAP #8"
crash_name_trap_09:         .asciz "TRAP #9"
crash_name_trap_10:         .asciz "TRAP #10"
crash_name_trap_11:         .asciz "TRAP #11"
crash_name_trap_12:         .asciz "TRAP #12"
crash_name_trap_13:         .asciz "TRAP #13"
crash_name_trap_14:         .asciz "TRAP #14"
crash_name_trap_15:         .asciz "TRAP #15"

    .align 2
crash_vector_name_table:
    .long crash_name_other
    .long crash_name_other
    .long crash_name_bus_error
    .long crash_name_address_error
    .long crash_name_illegal
    .long crash_name_zero_divide
    .long crash_name_chk
    .long crash_name_trapv
    .long crash_name_privilege
    .long crash_name_trace
    .long crash_name_line_a
    .long crash_name_line_f
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_trap_00
    .long crash_name_trap_01
    .long crash_name_trap_02
    .long crash_name_trap_03
    .long crash_name_trap_04
    .long crash_name_trap_05
    .long crash_name_trap_06
    .long crash_name_trap_07
    .long crash_name_trap_08
    .long crash_name_trap_09
    .long crash_name_trap_10
    .long crash_name_trap_11
    .long crash_name_trap_12
    .long crash_name_trap_13
    .long crash_name_trap_14
    .long crash_name_trap_15
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other

    .align 2
crash_font_1bpp:
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x00
    .byte 0x00, 0x66, 0x66, 0x66, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x66, 0xFF, 0x66, 0x66, 0xFF, 0x66, 0x00
    .byte 0x18, 0x3E, 0x60, 0x3C, 0x06, 0x7C, 0x18, 0x00
    .byte 0x00, 0x66, 0x6C, 0x18, 0x30, 0x66, 0x46, 0x00
    .byte 0x1C, 0x36, 0x1C, 0x38, 0x6F, 0x66, 0x3B, 0x00
    .byte 0x00, 0x18, 0x18, 0x18, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x0E, 0x1C, 0x18, 0x18, 0x1C, 0x0E, 0x00
    .byte 0x00, 0x70, 0x38, 0x18, 0x18, 0x38, 0x70, 0x00
    .byte 0x00, 0x66, 0x3C, 0xFF, 0x3C, 0x66, 0x00, 0x00
    .byte 0x00, 0x18, 0x18, 0x7E, 0x18, 0x18, 0x00, 0x00
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x30
    .byte 0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00
    .byte 0x00, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x40, 0x00
    .byte 0x00, 0x3C, 0x66, 0x6E, 0x76, 0x66, 0x3C, 0x00
    .byte 0x00, 0x18, 0x38, 0x18, 0x18, 0x18, 0x7E, 0x00
    .byte 0x00, 0x3C, 0x66, 0x0C, 0x18, 0x30, 0x7E, 0x00
    .byte 0x00, 0x7E, 0x0C, 0x18, 0x0C, 0x66, 0x3C, 0x00
    .byte 0x00, 0x0C, 0x1C, 0x3C, 0x6C, 0x7E, 0x0C, 0x00
    .byte 0x00, 0x7E, 0x60, 0x7C, 0x06, 0x66, 0x3C, 0x00
    .byte 0x00, 0x3C, 0x60, 0x7C, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x7E, 0x06, 0x0C, 0x18, 0x30, 0x30, 0x00
    .byte 0x00, 0x3C, 0x66, 0x3C, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x3C, 0x66, 0x3E, 0x06, 0x0C, 0x38, 0x00
    .byte 0x00, 0x00, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00
    .byte 0x00, 0x00, 0x18, 0x18, 0x00, 0x18, 0x18, 0x30
    .byte 0x06, 0x0C, 0x18, 0x30, 0x18, 0x0C, 0x06, 0x00
    .byte 0x00, 0x00, 0x7E, 0x00, 0x00, 0x7E, 0x00, 0x00
    .byte 0x60, 0x30, 0x18, 0x0C, 0x18, 0x30, 0x60, 0x00
    .byte 0x00, 0x3C, 0x66, 0x0C, 0x18, 0x00, 0x18, 0x00
    .byte 0x00, 0x3C, 0x66, 0x6E, 0x6E, 0x60, 0x3E, 0x00
    .byte 0x00, 0x18, 0x3C, 0x66, 0x66, 0x7E, 0x66, 0x00
    .byte 0x00, 0x7C, 0x66, 0x7C, 0x66, 0x66, 0x7C, 0x00
    .byte 0x00, 0x3C, 0x66, 0x60, 0x60, 0x66, 0x3C, 0x00
    .byte 0x00, 0x78, 0x6C, 0x66, 0x66, 0x6C, 0x78, 0x00
    .byte 0x00, 0x7E, 0x60, 0x7C, 0x60, 0x60, 0x7E, 0x00
    .byte 0x00, 0x7E, 0x60, 0x7C, 0x60, 0x60, 0x60, 0x00
    .byte 0x00, 0x3E, 0x60, 0x60, 0x6E, 0x66, 0x3E, 0x00
    .byte 0x00, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00
    .byte 0x00, 0x7E, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00
    .byte 0x00, 0x06, 0x06, 0x06, 0x06, 0x66, 0x3C, 0x00
    .byte 0x00, 0x66, 0x6C, 0x78, 0x78, 0x6C, 0x66, 0x00
    .byte 0x00, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00
    .byte 0x00, 0x63, 0x77, 0x7F, 0x6B, 0x63, 0x63, 0x00
    .byte 0x00, 0x66, 0x76, 0x7E, 0x7E, 0x6E, 0x66, 0x00
    .byte 0x00, 0x3C, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x00
    .byte 0x00, 0x3C, 0x66, 0x66, 0x66, 0x6C, 0x36, 0x00
    .byte 0x00, 0x7C, 0x66, 0x66, 0x7C, 0x6C, 0x66, 0x00
    .byte 0x00, 0x3C, 0x60, 0x3C, 0x06, 0x06, 0x3C, 0x00
    .byte 0x00, 0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00
    .byte 0x00, 0x66, 0x66, 0x66, 0x66, 0x66, 0x7E, 0x00
    .byte 0x00, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00
    .byte 0x00, 0x63, 0x63, 0x6B, 0x7F, 0x77, 0x63, 0x00
    .byte 0x00, 0x66, 0x66, 0x3C, 0x3C, 0x66, 0x66, 0x00
    .byte 0x00, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x00
    .byte 0x00, 0x7E, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00
    .byte 0x00, 0x1E, 0x18, 0x18, 0x18, 0x18, 0x1E, 0x00
    .byte 0x00, 0x40, 0x60, 0x30, 0x18, 0x0C, 0x06, 0x00
    .byte 0x00, 0x78, 0x18, 0x18, 0x18, 0x18, 0x78, 0x00
    .byte 0x00, 0x08, 0x1C, 0x36, 0x63, 0x00, 0x00, 0x00
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00
    .byte 0x00, 0x18, 0x3C, 0x7E, 0x7E, 0x3C, 0x18, 0x00
    .byte 0x00, 0x00, 0x3C, 0x06, 0x3E, 0x66, 0x3E, 0x00
    .byte 0x00, 0x60, 0x60, 0x7C, 0x66, 0x66, 0x7C, 0x00
    .byte 0x00, 0x00, 0x3C, 0x60, 0x60, 0x60, 0x3C, 0x00
    .byte 0x00, 0x06, 0x06, 0x3E, 0x66, 0x66, 0x3E, 0x00
    .byte 0x00, 0x00, 0x3C, 0x66, 0x7E, 0x60, 0x3C, 0x00
    .byte 0x00, 0x0E, 0x18, 0x3E, 0x18, 0x18, 0x18, 0x00
    .byte 0x00, 0x00, 0x3E, 0x66, 0x66, 0x3E, 0x06, 0x7C
    .byte 0x00, 0x60, 0x60, 0x7C, 0x66, 0x66, 0x66, 0x00
    .byte 0x00, 0x18, 0x00, 0x38, 0x18, 0x18, 0x3C, 0x00
    .byte 0x00, 0x06, 0x00, 0x06, 0x06, 0x06, 0x06, 0x3C
    .byte 0x00, 0x60, 0x60, 0x6C, 0x78, 0x6C, 0x66, 0x00
    .byte 0x00, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00
    .byte 0x00, 0x00, 0x66, 0x7F, 0x7F, 0x6B, 0x63, 0x00
    .byte 0x00, 0x00, 0x7C, 0x66, 0x66, 0x66, 0x66, 0x00
    .byte 0x00, 0x00, 0x3C, 0x66, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x00, 0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60
    .byte 0x00, 0x00, 0x3E, 0x66, 0x66, 0x3E, 0x06, 0x06
    .byte 0x00, 0x00, 0x7C, 0x66, 0x60, 0x60, 0x60, 0x00
    .byte 0x00, 0x00, 0x3E, 0x60, 0x3C, 0x06, 0x7C, 0x00
    .byte 0x00, 0x18, 0x7E, 0x18, 0x18, 0x18, 0x0E, 0x00
    .byte 0x00, 0x00, 0x66, 0x66, 0x66, 0x66, 0x3E, 0x00
    .byte 0x00, 0x00, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00
    .byte 0x00, 0x00, 0x63, 0x6B, 0x7F, 0x3E, 0x36, 0x00
    .byte 0x00, 0x00, 0x66, 0x3C, 0x18, 0x3C, 0x66, 0x00
    .byte 0x00, 0x00, 0x66, 0x66, 0x66, 0x3E, 0x0C, 0x78
    .byte 0x00, 0x00, 0x7E, 0x0C, 0x18, 0x30, 0x7E, 0x00
    .byte 0x00, 0x18, 0x3C, 0x7E, 0x7E, 0x18, 0x3C, 0x00
    .byte 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18
    .byte 0x00, 0x7E, 0x78, 0x7C, 0x6E, 0x66, 0x06, 0x00
    .byte 0x08, 0x18, 0x38, 0x78, 0x38, 0x18, 0x08, 0x00
    .byte 0x10, 0x18, 0x1C, 0x1E, 0x1C, 0x18, 0x10, 0x00

genesistan_crash_handler_end:
