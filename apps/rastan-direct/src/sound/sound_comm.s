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

z80_request_bus:
    move.w  #0x0100, Z80_BUSREQ
.Lwait_bus:
    btst    #0, Z80_BUSREQ
    bne.s   .Lwait_bus
    rts

z80_release_bus:
    move.w  #0x0000, Z80_BUSREQ
    rts

z80_init_and_start:
    /* At cold boot the Z80 is held in reset and therefore cannot acknowledge
       a bus request.  Assert reset first, then request the bus without using
       the live-Z80 acknowledgement loop used by command writes. */
    move.w  #0x0000, Z80_RESET
    move.w  #0x0100, Z80_BUSREQ

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
    rts

z80_write_command:
    bsr     z80_request_bus
    move.b  %d0, Z80_MAILBOX
    bsr     z80_release_bus
    rts
