/*
 * Rastan ARCADE Z80 sound driver — PROTOTYPE / DECLARATION INDEX (AUDIO-001 / M0; corrected AUDIO-009).
 *
 * *** THIS IS NOT A SEMANTIC C DECOMPILATION. ***  (Cody AUDIO-008 finding, confirmed.)
 * It is an INDEX of function entry points with prose summaries: declarations only, ZERO function bodies.
 * Register lifetimes, flags, stack effects, alternate paths, indirect control flow, and return behaviour
 * are NOT translated to C. Control-flow verification lives in build/audio/audiocpu.disasm.txt; the
 * instruction-backed coverage with honest evidence levels is z80_function_coverage.csv. Do not cite this
 * file as a completed decompilation or as semantic equivalence.
 *
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

/* 0x010B  main entry / init + main loop (control flow VERIFIED; no C body).
 * DI; IM 1; clear RAM 0x8000-0x8FFF; PC060HA init (a000=4,a001=0); init 8 channel blocks (0x80x0=0x0F);
 * run YM2151 init tables via writer FUN_158c; EI; then FOREVER:
 *   DI -> write YM reg 0x1B = (0x8F23 | 0x40)  [this YM port-write ALSO selects a ROM bank via
 *         sound_bankswitch_w(data&3); it is NOT a generic "refresh"]  -> FUN_0254(command dispatch)
 *         -> EI -> FUN_01c2(per-frame). (Cody AUDIO-008 claim 12: the bank-select side effect was omitted.)
 */
void z80_main_010b(void);

/* 0x0066  NMI_ISR = PC060HA command receive (control flow VERIFIED; no C body).
 * (Cody AUDIO-008 claim 10: the inter-CPU device is the PC060HA, NOT the TC0140SYT.)
 * PC060HA handshake a001=5,a000=0; read the command byte; enqueue (<0xF0) via FUN_00c0 into the
 * 0x8F02 ring and via FUN_00e9 into the 0x8E82 ring; PC060HA ack a000=6,a001=6. */
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

/* 0x02AA  BGM song select (control flow VERIFIED; corrected AUDIO-009; no C body).
 * ptr = *(word*)(0x2300 + cmd*2)         // COMMAND -> DESCRIPTOR POINTER TABLE at ROM 0x2300
 * lead = *(u8*)ptr                        // FIRST descriptor byte, tested at 0x02C3: CP 0x12
 *   lead == 0        -> empty (RET Z).
 *   lead <  0x12     -> ORDINARY COUNTED form: lead is a COUNT of N two-byte records; each record
 *                       {low, high}: high==0 -> DIRECT command byte (FUN_00c0); high!=0 -> little-endian
 *                       sub-sequence pointer (installed via FUN_02fe for sub-descriptors >= 0x12).
 *   lead >= 0x12     -> NOT a count: it is a CHANNEL/CONTROL IDENTIFIER passed straight to FUN_02fe
 *                       (0x02C7 CALL 0x02fe). The five commands 0x03,0x0A,0x0D,0x21,0x26 use descriptors
 *                       whose lead byte is 0x82 (= 130); 0x82/0x83 special-case the 0x8E00 ADPCM state
 *                       and the 0x0348 channel table.
 * (Cody AUDIO-008 claim 17: AUDIO-002's "count>=0x12 single-subseq / count 130" reading was WRONG.) */
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

/* 0x1A00 region  MSM5205 ADPCM sample trigger (control flow VERIFIED; latch roles corrected AUDIO-009).
 * Computes a sample length (repeated SBC HL,DE by 0x41) into 0x8E0F; drives the MSM5205 latches with
 * their CORRECT roles (matching the VERIFIED map above and MAME): 0xB000 = sample ADDRESS(-high) latch,
 * 0xC000 = START, 0xD000 = STOP. (Cody AUDIO-008 claim 22: the previous comment swapped these — it wrongly
 * called 0xD000 addr/trigger, 0xB000 bank/start, 0xC000 reset/stop.) The MSM5205 then streams 4-bit ADPCM
 * from adpcm.bin autonomously (VCK-clocked). */
void z80_adpcm_trigger_1a00(void);

/* 0x01F9  (callers=0) INFERRED YM2151-timer IRQ (RST 0x38 / IM1) service — per-tick sequence advance.
 * 0x01C2  per-frame update called from the main loop (VERIFIED call site). */
void z80_irq_01f9_INFERRED(void);
void z80_perframe_01c2(void);
