    .text
    .align 2

    .globl genesistan_Bus_Error
    .globl genesistan_Address_Error
    .globl genesistan_Illegal_Instruction
    .globl genesistan_Zero_Divide
    .globl genesistan_Chk_Instruction
    .globl genesistan_Trapv_Instruction
    .globl genesistan_Privilege_Violation
    .globl genesistan_Trace
    .globl genesistan_Line_1010_Emulation
    .globl genesistan_Line_1111_Emulation
    .globl genesistan_Error_Exception

    .globl genesistan_panic_code
    .globl genesistan_panic_original_sp
    .globl genesistan_panic_frame_words
    .globl genesistan_panic_entered
    .globl genesistan_exception_stack
    .globl genesistan_exception_enter

genesistan_Bus_Error:
    moveq #1, %d0
    bra.s genesistan_exception_common

genesistan_Address_Error:
    moveq #2, %d0
    bra.s genesistan_exception_common

genesistan_Illegal_Instruction:
    moveq #3, %d0
    bra.s genesistan_exception_common

genesistan_Zero_Divide:
    moveq #4, %d0
    bra.s genesistan_exception_common

genesistan_Chk_Instruction:
    moveq #5, %d0
    bra.s genesistan_exception_common

genesistan_Trapv_Instruction:
    moveq #6, %d0
    bra.s genesistan_exception_common

genesistan_Privilege_Violation:
    moveq #7, %d0
    bra.s genesistan_exception_common

genesistan_Trace:
    moveq #8, %d0
    bra.s genesistan_exception_common

genesistan_Line_1010_Emulation:
    moveq #9, %d0
    bra.s genesistan_exception_common

genesistan_Line_1111_Emulation:
    moveq #10, %d0
    bra.s genesistan_exception_common

genesistan_Error_Exception:
    moveq #15, %d0

genesistan_exception_common:
    move.w  #0x2700, %sr
    movel   #0xC0000000,0x00C00004
    movew   #0x000E,0x00C00000
    move.l  %sp, %a0
    move.w  %d0, genesistan_panic_code
    move.l  %a0, genesistan_panic_original_sp
    lea     genesistan_panic_frame_words, %a1
    moveq   #7, %d1

genesistan_exception_copy_loop:
    move.w  (%a0)+, (%a1)+
    dbra    %d1, genesistan_exception_copy_loop

    move.w  #1, genesistan_panic_entered
    lea     genesistan_exception_stack+512, %sp
    jsr     genesistan_exception_enter

genesistan_exception_halt:
    bra.s   genesistan_exception_halt
