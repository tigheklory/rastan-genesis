    .section .text,"ax"
    .global z80_init_and_start
    .global z80_write_command

    .extern z80_driver_start
    .extern z80_driver_end

    .equ Z80_RAM,      0x00A00000
    .equ Z80_MAILBOX,  0x00A01FF0
    .equ Z80_BUSREQ,   0x00A11100
    .equ Z80_RESET,    0x00A11200
    .equ Z80_RUNMARK,  0x00A01FF2
    .equ Z80_HEARTBEAT,0x00A01FF3
    .equ DIAG_LOG_PORT,0x00A14000

z80_request_bus:
    move.w  #0x0100, Z80_BUSREQ
.Lwait_bus:
    btst    #0, Z80_BUSREQ
    beq.s   .Lwait_bus
    rts

z80_release_bus:
    move.w  #0x0000, Z80_BUSREQ
    rts

z80_init_and_start:
    bsr     z80_request_bus

    move.w  #0x0000, Z80_RESET

    lea     z80_driver_start, %a0
    lea     z80_driver_end, %a2
    lea     Z80_RAM, %a1
.Lcopy_driver:
    cmpa.l  %a2, %a0
    beq.s   .Lcopy_done
    move.b  (%a0)+, (%a1)+
    bra.s   .Lcopy_driver
.Lcopy_done:

    clr.b   Z80_MAILBOX

    move.w  #0x0100, Z80_RESET

    bsr     z80_release_bus

    /* Bring-up probe: read Z80 run marker/heartbeat and emit a diagnostic log write. */
    move.l  #0x00003FFF, %d1
.Lwait_after_release:
    subq.l  #1, %d1
    bne.s   .Lwait_after_release

    bsr     z80_request_bus
    move.b  Z80_RUNMARK, %d0
    move.b  Z80_HEARTBEAT, %d2
    bsr     z80_release_bus

    cmpi.b  #0x5A, %d0
    bne.s   .Ldiag_fail
    move.w  #0xC0DE, DIAG_LOG_PORT
    move.w  %d2, DIAG_LOG_PORT+2
    bra.s   .Ldiag_done
.Ldiag_fail:
    move.w  #0xDEAD, DIAG_LOG_PORT
.Ldiag_done:
    rts

z80_write_command:
    bsr     z80_request_bus
    move.b  %d0, Z80_MAILBOX
    bsr     z80_release_bus
    rts
