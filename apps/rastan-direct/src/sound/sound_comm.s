    .section .text,"ax"
    .global z80_init_and_start
    .global z80_write_command

    .extern z80_driver_start
    .extern z80_driver_end
    .extern genesistan_audio_aggressive_start
    .extern genesistan_audio_aggressive_loop

    .equ Z80_RAM,      0x00A00000
    .equ Z80_BUSREQ,   0x00A11100
    .equ Z80_RESET,    0x00A11200
    .equ Z80_MUSIC_START, 0x00A01FC0
    .equ Z80_MUSIC_LOOP,  0x00A01FC3
    .equ Z80_QHEAD,       0x00A01FD0
    .equ Z80_QTAIL,       0x00A01FD1
    .equ Z80_QDATA,       0x00A01FE0

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
    /* The Genesis bus controller only acknowledges BUSREQ after Z80 reset is
       released.  Request, release reset, and wait for the grant.  BUSREQ then
       holds the Z80 while its RAM is replaced. */
    move.w  #0x0100, Z80_BUSREQ
    move.w  #0x0100, Z80_RESET
.Lwait_initial_bus:
    btst    #0, Z80_BUSREQ
    bne.s   .Lwait_initial_bus

    lea     z80_driver_start, %a0
    lea     z80_driver_end, %a2
    lea     Z80_RAM, %a1
.Lcopy_driver:
    cmpa.l  %a2, %a0
    beq.s   .Lcopy_done
    move.b  (%a0)+, (%a1)+
    bra.s   .Lcopy_driver
.Lcopy_done:
    lea     genesistan_audio_aggressive_start, %a0
    lea     Z80_MUSIC_START, %a1
    bsr     .Lstore_z80_pointer
    lea     genesistan_audio_aggressive_loop, %a0
    lea     Z80_MUSIC_LOOP, %a1
    bsr     .Lstore_z80_pointer
    clr.b   Z80_QHEAD
    clr.b   Z80_QTAIL

    move.w  #0x0000, Z80_RESET
    bsr     z80_release_bus

    /* Hold reset across a short delay after releasing the bus, then start. */
    move.w  #0x0020, %d0
.Lreset_delay:
    dbra    %d0, .Lreset_delay
    move.w  #0x0100, Z80_RESET
    rts

.Lstore_z80_pointer:
    move.l  %a0, %d0
    move.b  %d0, (%a1)+
    lsr.l   #8, %d0
    move.b  %d0, (%a1)+
    lsr.l   #8, %d0
    move.b  %d0, (%a1)
    rts

z80_write_command:
    movem.l %d1-%d2/%a0, -(%sp)
    bsr     z80_request_bus
    moveq   #0, %d1
    move.b  Z80_QHEAD, %d1
    move.b  %d1, %d2
    addq.b  #1, %d2
    andi.b  #0x0F, %d2
    cmp.b   Z80_QTAIL, %d2
    beq.s   .Lqueue_full
    lea     Z80_QDATA, %a0
    move.b  %d0, (%a0,%d1.w)
    move.b  %d2, Z80_QHEAD
.Lqueue_full:
    bsr     z80_release_bus
    movem.l (%sp)+, %d1-%d2/%a0
    rts
