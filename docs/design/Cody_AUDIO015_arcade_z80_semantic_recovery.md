# AUDIO-015 — Original arcade Z80 semantic recovery

## Result

Targeted instruction-level recovery removed the blocker that stopped AUDIO-014. The maintained C
reference now contains evidence-backed bodies for bounded command reception, both rings, startup,
PC060HA housekeeping, the IM1 timer service, dispatch, song selection, channel installation, SFX
computed dispatch, paired music/SFX orchestration, YM2151 writes, and the established ADPCM contract.
Complex per-control synthesis arithmetic remains explicitly `CONTROL_FLOW_VERIFIED`; it is not
misrepresented as a complete source reconstruction.

## Artifact reconciliation and authority

The preserved Build 0483 normal ROM hashes to
`aefad54c6494db7af916764c1e745edf1ef2b1c0f56db29d34ec7c16290202fb`, matching AUDIO-013 and exact
source `e0b122fca18d942a3ccd28ed246fdcee94192580`. The AUDIO-015 statement that AUDIO-014 reported another
hash refers to no durable AUDIO-014 report: that interrupted task created neither report nor build.
Artifact integrity is unaffected. Counter 483 and the Build-0478 acceptance tag were unchanged at
the start of AUDIO-015.

The original authority is `build/regions/audiocpu.bin`, corroborated by
`build/audio/audiocpu.disasm.txt`, the existing Ghidra project/exports, and retained 68000 code. The C
file is readable reference material only.

## Commands 00 and 19

The retained R1-S1 producer is byte-exact:

- `0x055E26`: load `0x00`; `0x055E2A`: call producer `0x03A0EC`;
- `0x055E30`: load `0x19`; `0x055E34`: call the same producer.

The Z80 path is NMI `0x0066` -> primary ring -> dispatcher `0x0254` -> song selector `0x02AA` -> table
`0x2300 + 2*command`.

Command `0x19` selects table entry `0x2332`, descriptor `0x2DF0`, count 8, and subdescriptors
`0x2E10, 0x2E20, 0x2E30, 0x2E40, 0x2E50, 0x2E60, 0x2E70, 0x2E80`. Those install identifiers
`8E,92,96,9A,9E,A2,A6,AA` with sequence pointers
`38C5,38D7,38F6,3930,3968,39A0,39D8,3A68`. It is the authentic R1-S1 music selection and reconciles
with the Aggressive World capture. Therefore **command 19 is Aggressive World**.

Command `0x00` selects `0x2300 -> 0x2830`, count 17, whose descriptors `0x28A0..0x29A0` cover the
music/SFX channel blocks and ADPCM identifier `0x82`; their termination controls stop/reset all
owners. It is the authentic all-channel stop/reset before the R1-S1 selection. Reissuing `0x19`
reinstalls pointers/state and retriggers from the start; `0x00` stops hardware and sequencing before a
change. The Genesis implementation preserves these semantic commands rather than inventing a scene
trigger.

## Timing and sequence grammar

Reset vector `0003` jumps to `010B`; IM1 vector `0038` jumps to `01F9`; `0066` is the PC060HA NMI.
Initialization writes YM2151 timer registers `10=00`, `11=00`, `12=C0`, `14=35`. Timer A therefore
ticks at `4,000,000/(64*1024) = 61.03515625 Hz`. On timer-A status, `01F9` writes `14=15`, calls
sequencer `0479`, calls ADPCM service `19A8`, and applies any pending timer reload. `01C2` is PC060HA
housekeeping, not the musical clock. Capture gaps near 721/724 samples corroborate, but do not define,
the recovered timer.

`0479` owns eight 0x100-stride music blocks (`8000..8700`) paired with eight SFX blocks
(`8080..8780`). `0764` decrements per-channel durations and calls `09A6`; state `+0B/+0C` is the
sequence pointer, `+13` duration, and `+15` gate time. In `0A56`, bit 7 clear is a note/event return;
bit 7 set with low nibble below C indexes the twelve-entry pitch table at `0B2C`; values C and above
dispatch through computed table `0AEC`. Its handlers own pointer movement, instrument/volume/pitch,
branches/loops, key state, and termination. Individual control-opcode names remain partial; the
recovered timing, state ownership, and loop-capable grammar are sufficient to choose an event-driven
permanent engine. Aggressive World's canonical intro/loop boundary is retained as separate generated
assets and agrees with the source VGM metadata (loop start sample 576,473; loop length 1,735,526).

## SFX and ADPCM constraints

`03E5` dispatches F0..FE through table `041B`: F0 -> `03F7`, F1..F3 -> `0408`, remaining entries use
the table default. `0395` and `0479` prove paired music/SFX channel takeover: music state continues
advancing during ownership, and the ending SFX marks music registers dirty for restoration. Thus the
permanent format cannot consume all hardware state irreversibly; it must retain sequencer state and
explicit owners/priorities.

`19A8` advances on the same timer tick and owns state at `8E00`; sample metadata is rooted at `2400`.
The hardware contract is `B000=address`, `C000=start`, `D000=stop`. Future Genesis PCM therefore has
a reserved FM6 DAC service and its own timed state. AUDIO-015 does not fabricate sample identities or
placeholder PCM.

## Coverage outcome

`SEMANTIC_C_COMPLETE` is now used only for bounded routines whose material paths have bodies:
`0066`, `00C0`, `00E9`, `01C2`, `01F9`, `0254`, `02AA`, and `158C`. Startup `010B`, install `02FE`,
SFX dispatch `03E5`, orchestration `0479`, channel tick `0764`, duration/event service `09A6`, control
decode `0A56`, and ADPCM `19A8` remain `CONTROL_FLOW_VERIFIED` where their deeper callees or opcode
families are still partial. No function is promoted merely because it now has explanatory C.
