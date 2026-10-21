/*
 * Rastan ARCADE Z80 sound driver — curated C reference reconstruction (AUDIO-001 / M0).
 * SOURCE binary: build/regions/audiocpu.bin (ROM b04-19.49, 65536 B, sha1 fa59dac2583a…).
 * Ghidra project: tools/ghidra rastan_audio_z80 (z80:LE:16:default, base 0x0000).
 * Raw Ghidra export: build/audio/z80_decomp.c ; disasm: build/audio/audiocpu.disasm.txt ;
 *                    function map: build/audio/z80_functions.tsv (63 functions).
 * NOT original Taito source. The original Z80 BINARY remains authoritative; this C is reference only
 * and is NOT compiled into any ROM. Evidence: VERIFIED (from instructions) / INFERRED / UNRESOLVED.
 *
 * ===========================================================================================
 * VERIFIED Z80 MEMORY / HARDWARE MAP (from decoded instructions)
 * -------------------------------------------------------------------------------------------
 *   0x0000-0x3FFF  fixed program ROM (code; data tables incl. the 0x2300 song table + sub-sequences).
 *   0x4000-0x7FFF  BANKED ROM window — 4 x 16KB banks of the 64KB ROM (MAME: bankr(m_audiobank),
 *                  configure_entries(0,4,base,0x4000)); bank select = sound_bankswitch_w(data&3) wired
 *                  to the YM2151 PORT-WRITE handler (no explicit bank store in Z80 code). bank0=file
 *                  0x0000, bank1=0x4000, bank2=0x8000 (the file 0x8000-0x8EDE blob), bank3=0xC000.
 *   0x8000-0x8FFF  work RAM (cleared at init 0x010B; SP top = 0x9000).
 *     0x80x0..0x87x0 : 8 per-FM-channel state blocks (0x100 stride; inited to 0x0F at 0x010B).
 *     0x8E80 head / 0x8E81 tail / 0x8E82+  : 32-slot secondary ring (NMI, FUN_00e9).
 *     0x8E0F..0x8E14 : ADPCM sample length/addr scratch (0x1A00 trigger routine).
 *     0x8F00 head / 0x8F01 tail / 0x8F02+  : 16-slot command ring (NMI enqueue, dispatch pop).
 *     0x8F26/0x8F27/0x8F28 : mode/mute/current-song state. 0x8FFE : writer source pointer.
 *   0x9000  YM2151 register-address port   (VERIFIED: FUN_158c, 14 LD HL,0x9000 sites).
 *   0x9001  YM2151 data / status (bit7 polled as write-ready) (VERIFIED: LD A,(0x9001) @0x0201).
 *   0xA000/0xA001  PC060HA (Taito CIU) inter-CPU port (MAME-VERIFIED; prior docs' "TC0140SYT" is the
 *                    wrong chip name — same addresses/protocol). NMI_ISR + every dispatch handshake.
 *   0xB000 = MSM5205 sample-address latch, 0xC000 = start, 0xD000 = stop (MAME-VERIFIED; matches 0x19A8).
 *                    The MSM5205 reads its own sample ROM b04-20.76/adpcm.bin (8 kHz, 4-bit).
 *   Interrupts: IM 1 (RST 0x38) = YM2151 timer IRQ line; NMI = PC060HA command strobe.
 *   CLOCKS (MAME PCB-verified): Z80 = 16MHz/4 = 4.000 MHz; YM2151 = 16MHz/4 = 4.000 MHz;
 *     MSM5205 = 384 kHz, prescaler S48_4B = 8 kHz 4-bit ADPCM.
 * ===========================================================================================
 */
#include <stdint.h>

/* 0x0000 RST0: reset vector -> JP 0x010B (VERIFIED). */

/* 0x010B  main entry / init + main loop (VERIFIED).
 * DI; IM 1; clear RAM 0x8000-0x8FFF; SYT init (a000=4,a001=0); init 8 channel blocks (0x80x0=0x0F);
 * run YM2151 init tables via writer FUN_158c; EI; then FOREVER:
 *   DI -> FUN_158c(YM2151 refresh) -> FUN_0254(command dispatch) -> EI -> FUN_01c2(per-frame) .
 */
void z80_main_010b(void);

/* 0x0066  NMI_ISR = TC0140SYT command receive (VERIFIED).
 * SYT handshake a001=5,a000=0; read the command byte from the SYT; enqueue (<0xF0) via FUN_00c0
 * into the 0x8F02 ring and via FUN_00e9 into the 0x8E82 ring; SYT ack a000=6,a001=6. */
void z80_nmi_cmd_receive_0066(void);

/* 0x00C0  ring enqueue (16-slot, 0x8F00 head/0x8F01 tail, mask 0xF) for cmd<0xF0 (VERIFIED). */
void z80_ring16_enqueue_00c0(uint8_t cmd);
/* 0x00E9  ring enqueue (32-slot, 0x8E80 head/0x8E81 tail, mask 0x1F) (VERIFIED). */
void z80_ring32_enqueue_00e9(uint8_t v);

/* 0x0254  COMMAND DISPATCH (VERIFIED).
 * Pops the 16-slot ring; per command byte c:
 *   c < 0x2C  (and not muted, 0x8F27 bit0==0) -> FUN_02aa  (BGM song select)
 *   0xE0..0xEF                                -> FUN_0368  (control: 0xEE/0xEF toggle flag 0x8F26)
 *   0xF0..0xFE                                -> FUN_03e5  (SFX/channel class; see UNRESOLVED)
 *   0xFF                                      -> skip
 * SYT busy/ack a000/a001 = 5/5 then 6/6 around the pop. */
void z80_dispatch_0254(void);

/* 0x02AA  BGM song select (VERIFIED structure).
 * ptr = *(word*)(0x2300 + cmd*2)         // COMMAND -> SEQUENCE POINTER TABLE at ROM 0x2300
 * desc = {count; (channel_id, seq_ptr)[count]}   // count <= 0x11 channel-tracks per song
 * installs each channel-track's sub-sequence (FUN_02fe) / re-enqueues (FUN_00c0). */
void z80_song_select_02aa(void);

/* 0x0368  control commands 0xE0-0xEF (VERIFIED partial): 0xEE -> a001=0,0x8F26=0; 0xEF -> a001=1,
 *          0x8F26=1 (a sound-enable / attract-mute mode flag). Other 0xE0-0xED: no-op here. */
void z80_control_0368(void);

/* 0x03E5  SFX / channel class 0xF0-0xFE — UNRESOLVED.
 * Ghidra decompile FAILED here (pcode constructor error at 0x03E5; also at 0x57D8/0x7EE7, data-as-code
 * at the banked tail). Requires manual disassembly; it is the FM-SFX / stop / ADPCM-trigger dispatch
 * candidate. DO NOT GUESS its behavior. */
void z80_sfx_class_03e5_UNRESOLVED(void);

/* 0x158C  YM2151 REGISTER WRITE PRIMITIVE (VERIFIED, 18 callers).
 *   wait while (*(0x9001) & 0x80);  *(0x9000) = reg;        // address port
 *   wait while (*(0x9001) & 0x80);  *(0x9001) = data;       // data port
 * This is the single hardware-output chokepoint for all FM. */
void z80_ym2151_write_158c(uint8_t data, uint16_t reg_in_hi, uint8_t *addr_port /*=0x9000*/);

/* 0x1A00 region  MSM5205 ADPCM sample trigger (VERIFIED sites).
 * Computes a sample length (repeated SBC HL,DE by 0x41) into 0x8E0F; loads the MSM5205 latches
 * 0xD000 (addr/trigger), 0xB000 (bank/start-hi from 0x8E12), 0xC000 (reset/stop). The MSM5205 then
 * streams 4-bit ADPCM from adpcm.bin autonomously (VCK-clocked). */
void z80_adpcm_trigger_1a00(void);

/* 0x01F9  (callers=0) INFERRED YM2151-timer IRQ (RST 0x38 / IM1) service — per-tick sequence advance.
 * 0x01C2  per-frame update called from the main loop (VERIFIED call site). */
void z80_irq_01f9_INFERRED(void);
void z80_perframe_01c2(void);
