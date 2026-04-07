    .section .text.boot,"ax"
    .global _start
    .extern main_68k
    .extern _VINT_handler

    .equ HW_VERSION,  0x00A10001
    .equ TMSS_REG,    0x00A14000

    .org 0x000000
    .long 0x00FF0000
    .long _start
    .rept 28
    .long _default_handler
    .endr
    .long _VINT_handler
    .long _default_handler
    .rept 32
    .long _default_handler
    .endr

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
_default_handler:
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
