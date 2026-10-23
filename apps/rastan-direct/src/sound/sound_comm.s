    .section .text,"ax"
    .global z80_init_and_start
    .global z80_write_command

    .extern z80_driver_start
    .extern z80_driver_end
    .extern genesistan_audio_song_dispatch_count
    .extern genesistan_audio_song_dispatch

    .equ Z80_RAM,      0x00A00000
    .equ Z80_BUSREQ,   0x00A11100
    .equ Z80_RESET,    0x00A11200
    .equ Z80_SONG_COUNT,  0x00A01DFF
    .equ Z80_SONG_TABLE,  0x00A01E00
    .equ Z80_QHEAD,       0x00A01FD0
    .equ Z80_QTAIL,       0x00A01FD1
    .equ Z80_QDATA,       0x00A01FE0
    .equ ARCADE_OUTER_STATE,  0x00FF0000
    .equ ARCADE_PHASE_STATE,  0x00FF0002
    .equ ARCADE_PLAYER_STATE, 0x00FF10E8

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
    /* Convert the link-resolved 68000 catalog pointers into the packed
       command/start24/loop24 table consumed from Z80 RAM. */
    moveq   #0, %d2
    move.b  genesistan_audio_song_dispatch_count, %d2
    move.b  %d2, Z80_SONG_COUNT
    beq.s   .Lsong_table_done
    subq.w  #1, %d2
    lea     genesistan_audio_song_dispatch, %a0
    lea     Z80_SONG_TABLE, %a1
.Lcopy_song_entry:
    move.b  (%a0)+, (%a1)+             /* wire command */
    addq.l  #3, %a0                    /* song id + alignment word */
    move.l  (%a0)+, %d0                /* cartridge intro pointer */
    bsr     .Lstore_z80_pointer
    addq.l  #1, %a1
    move.l  (%a0)+, %d0                /* cartridge loop pointer */
    bsr     .Lstore_z80_pointer
    addq.l  #1, %a1
    dbra    %d2, .Lcopy_song_entry
.Lsong_table_done:
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
    move.b  %d0, (%a1)+
    lsr.l   #8, %d0
    move.b  %d0, (%a1)+
    lsr.l   #8, %d0
    move.b  %d0, (%a1)
    rts

z80_write_command:
    movem.l %d1-%d2/%a0, -(%sp)

    /* Original command $25 is emitted both at the genuine player-appearance
       boundary and by the phase-4 death transition.  The arcade sound driver
       distinguished those events internally; the native command ring must
       preserve that semantic distinction.  Consume only the proven death
       form (2/4, player state 8).  Initial appearance and post-READY
       reappearance retain $25 and therefore deliberately start/restart the
       current stage song. */
    cmpi.b  #0x25, %d0
    bne.s   .Lpublish
    cmpi.w  #0x0002, ARCADE_OUTER_STATE
    bne.s   .Lpublish
    cmpi.w  #0x0004, ARCADE_PHASE_STATE
    bne.s   .Lpublish
    cmpi.w  #0x0008, ARCADE_PLAYER_STATE
    beq.s   .Lcommand_consumed
.Lpublish:
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
.Lcommand_consumed:
    movem.l (%sp)+, %d1-%d2/%a0
    rts
