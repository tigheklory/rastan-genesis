; AUDIO-015 permanent Genesis Z80 audio engine.
; Command input is a bounded 16-byte ring owned jointly with the 68000 bridge.
; Music data is a cartridge-resident native YM2612/PSG tick stream, never VGM.

        org     $0000
        di
        jp      init

        org     $0038
        reti                            ; scheduler polls YM2612 Timer B

        org     $0066
        retn                            ; no arcade PC060HA/NMI exists on Genesis

YM0A    equ     $4000
YM0D    equ     $4001
YM1A    equ     $4002
YM1D    equ     $4003
BANK    equ     $6000
PSG     equ     $7F11

CUR_LO  equ     $1FA0
CUR_MI  equ     $1FA1
CUR_HI  equ     $1FA2
ACTIVE  equ     $1FA3
WIN_LO  equ     $1FA4
WIN_HI  equ     $1FA5
BANKV   equ     $1FA6
STARTP  equ     $1FC0
LOOPP   equ     $1FC3
QHEAD   equ     $1FD0
QTAIL   equ     $1FD1
QDATA   equ     $1FE0
STACK   equ     $1F80

init:
        ld      sp,STACK
        xor     a
        ld      (QHEAD),a
        ld      (QTAIL),a
        ld      (ACTIVE),a
        call    silence_all
        ld      a,$26                  ; YM2612 Timer B: ~61.09 Hz
        ld      e,$93
        call    ym0
        ld      a,$27                  ; load/enable B, clear B status
        ld      e,$2A
        call    ym0

main:
        call    command_pop
        ld      a,(YM0A)
        bit     1,a
        jr      z,main
        ld      a,$27
        ld      e,$2A
        call    ym0
        ld      a,(ACTIVE)
        or      a
        call    nz,music_tick
        jr      main

command_pop:
        ld      a,(QTAIL)
        ld      c,a
        ld      a,(QHEAD)
        cp      c
        ret     z
        ld      b,0
        ld      hl,QDATA
        add     hl,bc
        ld      a,(hl)
        inc     c
        ld      b,a
        ld      a,c
        and     $0F
        ld      (QTAIL),a
        ld      a,b
        or      a
        jp      z,music_stop            ; command $00: original all-channel stop
        cp      $19
        ret     nz                      ; unsupported authentic commands remain queued/consumed
music_start:
        ld      hl,STARTP
        call    load_pointer
        ld      a,1
        ld      (ACTIVE),a
        ret

music_stop:
        xor     a
        ld      (ACTIVE),a
        jp      silence_all

music_tick:
        call    stream_byte
        cp      $FF
        jr      nz,.count
        ld      hl,LOOPP
        call    load_pointer
        call    stream_byte
.count:
        ld      b,a
        or      a
        ret     z
.event:
        push    bc
        call    stream_byte
        cp      2
        jr      z,.psg
        ld      c,a
        call    stream_byte
        ld      d,a
        call    stream_byte
        ld      e,a
        ld      a,c
        or      a
        ld      a,d
        call    z,ym0
        ld      a,c
        or      a
        ld      a,d
        call    nz,ym1
        jr      .next
.psg:
        call    stream_byte
        ld      (PSG),a
.next:
        pop     bc
        djnz    .event
        ret

; HL points at a little-endian 24-bit 68000 ROM address in shared Z80 RAM.
load_pointer:
        ld      a,(hl)
        ld      (CUR_LO),a
        inc     hl
        ld      a,(hl)
        ld      (CUR_MI),a
        inc     hl
        ld      a,(hl)
        ld      (CUR_HI),a
        call    set_bank_from_current
        ret

set_bank_from_current:
        ld      a,(CUR_HI)
        add     a,a
        ld      c,a
        ld      a,(CUR_MI)
        rlca
        and     1
        or      c                       ; A = 68000 address >> 15
        ld      (BANKV),a
        push    af
        ld      bc,BANK
        ld      d,9
.bankbits:
        ld      (bc),a
        srl     a
        dec     d
        jr      nz,.bankbits
        pop     af
        ld      a,(CUR_MI)
        and     $7F
        or      $80
        ld      h,a
        ld      a,(CUR_LO)
        ld      l,a
        ld      (WIN_LO),hl
        ret

stream_byte:
        ld      hl,(WIN_LO)
        ld      a,(hl)
        push    af
        inc     hl
        bit     7,h
        jr      nz,.window_ok
        ld      h,$80                  ; crossed the 0xFFFF -> 0x8000 window edge
        ld      a,(BANKV)
        inc     a
        ld      (BANKV),a
        push    hl
        call    set_bank_value
        pop     hl
.window_ok:
        ld      (WIN_LO),hl
        ld      a,(CUR_LO)
        inc     a
        ld      (CUR_LO),a
        jr      nz,.done
        ld      a,(CUR_MI)
        inc     a
        ld      (CUR_MI),a
        jr      nz,.done
        ld      a,(CUR_HI)
        inc     a
        ld      (CUR_HI),a
.done:
        pop     af
        ret

set_bank_value:
        ld      bc,BANK
        ld      d,9
.bankbits:
        ld      (bc),a
        srl     a
        dec     d
        jr      nz,.bankbits
        ret

ym0:
        push    af
.busy0:
        ld      a,(YM0A)
        and     $80
        jr      nz,.busy0
        pop     af
        ld      (YM0A),a
        push    af
.busy1:
        ld      a,(YM0A)
        and     $80
        jr      nz,.busy1
        ld      a,e
        ld      (YM0D),a
        pop     af
        ret

ym1:
        push    af
.busy0:
        ld      a,(YM0A)
        and     $80
        jr      nz,.busy0
        pop     af
        ld      (YM1A),a
        push    af
.busy1:
        ld      a,(YM0A)
        and     $80
        jr      nz,.busy1
        ld      a,e
        ld      (YM1D),a
        pop     af
        ret

silence_all:
        ld      b,6
        ld      c,0
.fm:
        ld      a,$28
        ld      e,c
        call    ym0
        inc     c
        ld      a,c
        cp      3
        jr      nz,.cont
        inc     c                       ; YM2612 key selector skips value 3
.cont:
        djnz    .fm
        ld      a,$9F
        ld      (PSG),a
        ld      a,$BF
        ld      (PSG),a
        ld      a,$DF
        ld      (PSG),a
        ld      a,$FF
        ld      (PSG),a
        ld      a,$2B                  ; FM6 DAC disabled/reserved
        ld      e,0
        jp      ym0

driver_end:
