    .section .text.boot,"ax"
    .global _start
    .extern main_68k
    .extern _VINT_handler
    .extern _crash_stub_bus_error
    .extern _crash_stub_address_error
    .extern _crash_stub_illegal
    .extern _crash_stub_zero_divide
    .extern _crash_stub_chk
    .extern _crash_stub_trapv
    .extern _crash_stub_privilege
    .extern _crash_stub_trace
    .extern _crash_stub_line_a
    .extern _crash_stub_line_f
    .extern _crash_stub_trap_00
    .extern _crash_stub_trap_01
    .extern _crash_stub_trap_02
    .extern _crash_stub_trap_03
    .extern _crash_stub_trap_04
    .extern _crash_stub_trap_05
    .extern _crash_stub_trap_06
    .extern _crash_stub_trap_07
    .extern _crash_stub_trap_08
    .extern _crash_stub_trap_09
    .extern _crash_stub_trap_10
    .extern _crash_stub_trap_11
    .extern _crash_stub_trap_12
    .extern _crash_stub_trap_13
    .extern _crash_stub_trap_14
    .extern _crash_stub_trap_15
    .extern _crash_stub_other

    .equ HW_VERSION,  0x00A10001
    .equ TMSS_REG,    0x00A14000

    .org 0x000000
    .long 0x00FF0000
    .long _start
    .long _crash_stub_bus_error         /*  2 */
    .long _crash_stub_address_error     /*  3 */
    .long _crash_stub_illegal           /*  4 */
    .long _crash_stub_zero_divide       /*  5 */
    .long _crash_stub_chk               /*  6 */
    .long _crash_stub_trapv             /*  7 */
    .long _crash_stub_privilege         /*  8 */
    .long _crash_stub_trace             /*  9 */
    .long _crash_stub_line_a            /* 10 */
    .long _crash_stub_line_f            /* 11 */
    .long _crash_stub_other             /* 12 */
    .long _crash_stub_other             /* 13 */
    .long _crash_stub_other             /* 14 */
    .long _crash_stub_other             /* 15 */
    .long _crash_stub_other             /* 16 */
    .long _crash_stub_other             /* 17 */
    .long _crash_stub_other             /* 18 */
    .long _crash_stub_other             /* 19 */
    .long _crash_stub_other             /* 20 */
    .long _crash_stub_other             /* 21 */
    .long _crash_stub_other             /* 22 */
    .long _crash_stub_other             /* 23 */
    .long _crash_stub_other             /* 24 */
    .long _crash_stub_other             /* 25 */
    .long _crash_stub_other             /* 26 */
    .long _crash_stub_other             /* 27 */
    .long _crash_stub_other             /* 28 */
    .long _crash_stub_other             /* 29 */
    .long _VINT_handler
    .long _crash_stub_other             /* 31 */
    .long _crash_stub_trap_00           /* 32 */
    .long _crash_stub_trap_01           /* 33 */
    .long _crash_stub_trap_02           /* 34 */
    .long _crash_stub_trap_03           /* 35 */
    .long _crash_stub_trap_04           /* 36 */
    .long _crash_stub_trap_05           /* 37 */
    .long _crash_stub_trap_06           /* 38 */
    .long _crash_stub_trap_07           /* 39 */
    .long _crash_stub_trap_08           /* 40 */
    .long _crash_stub_trap_09           /* 41 */
    .long _crash_stub_trap_10           /* 42 */
    .long _crash_stub_trap_11           /* 43 */
    .long _crash_stub_trap_12           /* 44 */
    .long _crash_stub_trap_13           /* 45 */
    .long _crash_stub_trap_14           /* 46 */
    .long _crash_stub_trap_15           /* 47 */
    .long _crash_stub_other             /* 48 */
    .long _crash_stub_other             /* 49 */
    .long _crash_stub_other             /* 50 */
    .long _crash_stub_other             /* 51 */
    .long _crash_stub_other             /* 52 */
    .long _crash_stub_other             /* 53 */
    .long _crash_stub_other             /* 54 */
    .long _crash_stub_other             /* 55 */
    .long _crash_stub_other             /* 56 */
    .long _crash_stub_other             /* 57 */
    .long _crash_stub_other             /* 58 */
    .long _crash_stub_other             /* 59 */
    .long _crash_stub_other             /* 60 */
    .long _crash_stub_other             /* 61 */
    .long _crash_stub_other             /* 62 */
    .long _crash_stub_other             /* 63 */

    .org 0x000100
    .ascii "SEGA MEGA DRIVE "
    .ascii "(C)CDX 2026.APR"
    .ascii "RASTAN DIRECT VIDEO TEST                      "
    .ascii "RASTAN DIRECT VIDEO TEST                      "
    .ascii "RDVD00000000  "
    .word  0x0000
    .ascii "J               "
    .long  0x00000000
    .long  0x0003FFFF
    .long  0x00FF0000
    .long  0x00FFFFFF
    .ascii "            "
    .ascii "                                        "
    .ascii "JUE             "

    .org 0x000200
_boot_guard_legacy_rte:
    rte

_start:
    move.w  #0x2700, %sr
    lea     0x00FF0000, %sp

    move.b  HW_VERSION, %d0
    andi.b  #0x0F, %d0
    beq.s   .Ltmss_done
    move.l  #0x53454741, TMSS_REG
.Ltmss_done:

    jsr     main_68k

.Lhang:
    bra.s   .Lhang
