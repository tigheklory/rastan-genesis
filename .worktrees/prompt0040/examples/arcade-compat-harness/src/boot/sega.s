#include "task_cst.h"

.section .text.keepboot

    .globl  rom_header

    .org    0x00000000

_Start_Of_Rom:
_Vecteurs_68K:
        dc.l    __stack
        dc.l    _Entry_Point
        dc.l    _Bus_Error
        dc.l    _Address_Error
        dc.l    _Illegal_Instruction
        dc.l    _Zero_Divide
        dc.l    _Chk_Instruction
        dc.l    _Trapv_Instruction
        dc.l    _Privilege_Violation
        dc.l    _Trace
        dc.l    _Line_1010_Emulation
        dc.l    _Line_1111_Emulation
        dc.l     _Error_Exception, _Error_Exception, _Error_Exception, _Error_Exception
        dc.l     _Error_Exception, _Error_Exception, _Error_Exception, _Error_Exception
        dc.l     _Error_Exception, _Error_Exception, _Error_Exception, _Error_Exception
        dc.l    _Error_Exception
        dc.l    _INT
        dc.l    _EXTINT
        dc.l    _INT
        dc.l    hintCaller
        dc.l    _INT
        dc.l    _VINT
        dc.l    _INT
        dc.l    _trap_0
        dc.l    _INT,_INT,_INT,_INT,_INT,_INT,_INT
        dc.l    _INT,_INT,_INT,_INT,_INT,_INT,_INT,_INT
        dc.l    _INT,_INT,_INT,_INT,_INT,_INT,_INT,_INT
        dc.l    _INT,_INT,_INT,_INT,_INT,_INT,_INT,_INT

rom_header:
        .incbin "out/rom_head.bin", 0, 0x100

_Entry_Point:
        move    #0x2700,%sr
        move    %sp, %usp
        sub     #USER_STACK_LENGTH, %sp

        move.l  #0xA11100,%a0
        move.w  #0x0100,%d0
        move.w  %d0,(%a0)
        move.w  %d0,0x0100(%a0)

        tst.l   0xa10008
        bne.s   SkipInit

        tst.w   0xa1000c
        bne.s   SkipInit

        move.b  -0x10ff(%a0),%d0
        andi.b  #0x0f,%d0
        beq.s   NoTMSS

        move.l  #0x53454741,0x2f00(%a0)

NoTMSS:
        jmp     _start_entry

SkipInit:
        jmp     _reset_entry

_INT:
        movem.l %d0-%d1/%a0-%a1,-(%sp)
        move.l  intCB, %a0
        jsr    (%a0)
        movem.l (%sp)+,%d0-%d1/%a0-%a1
        rte

_EXTINT:
        movem.l %d0-%d1/%a0-%a1,-(%sp)
        move.l  eintCB, %a0
        jsr    (%a0)
        movem.l (%sp)+,%d0-%d1/%a0-%a1
        rte

_VINT:
        btst    #5, (%sp)
        bne.s   no_user_task

        tst.w   task_lock
        bne.s   1f
        move.w  #0, -(%sp)
        bra.s   unlock

1:
        bcs.s   no_user_task
        subq.w  #1, task_lock
        bne.s   no_user_task
        move.w  #1, -(%sp)

unlock:
        move.l  %a0, task_regs
        lea     (task_regs + UTSK_REGS_LEN), %a0
        movem.l %d0-%d7/%a1-%a6, -(%a0)

        move.w  (%sp)+, %d0
        move.w  (%sp)+, task_sr
        move.l  (%sp)+, task_pc
        movem.l (%sp)+, %d2-%d7/%a2-%a6

no_user_task:
        movem.l %d0-%d1/%a0-%a1,-(%sp)
        ori.w   #0x0001, intTrace
        addq.l  #1, vtimer
        btst    #3, VBlankProcess+1
        beq.s   no_xgm_task

        jsr     XGM_doVBlankProcess

no_xgm_task:
        btst    #1, VBlankProcess+1
        beq.s   no_bmp_task

        jsr     BMP_doVBlankProcess

no_bmp_task:
        move.l  vintCB, %a0
        jsr    (%a0)
        andi.w  #0xFFFE, intTrace
        movem.l (%sp)+,%d0-%d1/%a0-%a1
        rte
