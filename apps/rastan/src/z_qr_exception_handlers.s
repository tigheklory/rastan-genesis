#ifndef RASTAN_EXCEPTION_DUMPER_MODE
#define RASTAN_EXCEPTION_DUMPER_MODE 0
#endif

#if RASTAN_EXCEPTION_DUMPER_MODE != 0

    .section .text
    .align 2

    .globl _Rastan_EX_Bus_Error
    .globl _Rastan_EX_Address_Error
    .globl _Rastan_EX_Illegal_Instruction
    .globl _Rastan_EX_Zero_Divide
    .globl _Rastan_EX_Chk_Instruction
    .globl _Rastan_EX_Trapv_Instruction
    .globl _Rastan_EX_Privilege_Violation
    .globl _Rastan_EX_Trace
    .globl _Rastan_EX_Line_1010_Emulation
    .globl _Rastan_EX_Line_1111_Emulation
    .globl _Rastan_EX_Error_Exception

    .extern rastan_exception_render

    .extern rastan_qr_exc_type
    .extern rastan_qr_exc_d
    .extern rastan_qr_exc_a
    .extern rastan_qr_exc_ssp
    .extern rastan_qr_exc_usp
    .extern rastan_qr_exc_frame_words

    .equ RASTAN_QR_EX_BUS,      1
    .equ RASTAN_QR_EX_ADDR,     2
    .equ RASTAN_QR_EX_ILL,      3
    .equ RASTAN_QR_EX_ZDIV,     4
    .equ RASTAN_QR_EX_CHK,      5
    .equ RASTAN_QR_EX_TRAPV,    6
    .equ RASTAN_QR_EX_PRIV,     7
    .equ RASTAN_QR_EX_TRACE,    8
    .equ RASTAN_QR_EX_LINE1010, 9
    .equ RASTAN_QR_EX_LINE1111, 10
    .equ RASTAN_QR_EX_ERROR,    11

.macro QR_HANDLER label, id
\label:
    move.w  #\id,rastan_qr_exc_type
    bra.w   _Rastan_EX_Exception_Common
.endm

_Rastan_EX_Exception_Common:
    move    #0x2700,%sr

    move.l  %d0,rastan_qr_exc_d+0
    move.l  %d1,rastan_qr_exc_d+4
    move.l  %d2,rastan_qr_exc_d+8
    move.l  %d3,rastan_qr_exc_d+12
    move.l  %d4,rastan_qr_exc_d+16
    move.l  %d5,rastan_qr_exc_d+20
    move.l  %d6,rastan_qr_exc_d+24
    move.l  %d7,rastan_qr_exc_d+28

    move.l  %a0,rastan_qr_exc_a+0
    move.l  %a1,rastan_qr_exc_a+4
    move.l  %a2,rastan_qr_exc_a+8
    move.l  %a3,rastan_qr_exc_a+12
    move.l  %a4,rastan_qr_exc_a+16
    move.l  %a5,rastan_qr_exc_a+20
    move.l  %a6,rastan_qr_exc_a+24
    move.l  %a7,rastan_qr_exc_a+28

    move.l  %a7,rastan_qr_exc_ssp
    move.l  %usp,%a0
    move.l  %a0,rastan_qr_exc_usp

    movea.l %a7,%a0
    lea     rastan_qr_exc_frame_words,%a1
    moveq   #15,%d1
1:
    move.w  (%a0)+,(%a1)+
    dbra    %d1,1b

    jsr     rastan_exception_render

2:
    bra.s   2b

QR_HANDLER _Rastan_EX_Bus_Error, RASTAN_QR_EX_BUS
QR_HANDLER _Rastan_EX_Address_Error, RASTAN_QR_EX_ADDR
QR_HANDLER _Rastan_EX_Illegal_Instruction, RASTAN_QR_EX_ILL
QR_HANDLER _Rastan_EX_Zero_Divide, RASTAN_QR_EX_ZDIV
QR_HANDLER _Rastan_EX_Chk_Instruction, RASTAN_QR_EX_CHK
QR_HANDLER _Rastan_EX_Trapv_Instruction, RASTAN_QR_EX_TRAPV
QR_HANDLER _Rastan_EX_Privilege_Violation, RASTAN_QR_EX_PRIV
QR_HANDLER _Rastan_EX_Trace, RASTAN_QR_EX_TRACE
QR_HANDLER _Rastan_EX_Line_1010_Emulation, RASTAN_QR_EX_LINE1010
QR_HANDLER _Rastan_EX_Line_1111_Emulation, RASTAN_QR_EX_LINE1111
QR_HANDLER _Rastan_EX_Error_Exception, RASTAN_QR_EX_ERROR

#endif
