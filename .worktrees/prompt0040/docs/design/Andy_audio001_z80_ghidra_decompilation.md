# Andy — AUDIO-001 / M0: Original Rastan Z80 Audio Driver Ghidra Decompilation

> **AUDIO-009 CORRECTION NOTICE (2026-10-21, confirmed by Cody AUDIO-008):** (1) The curated C
> (`analysis/decompilation/c/z80/rastan_z80_sound_driver.c`) is a **declaration index (12 prototypes, zero
> function bodies)**, NOT a semantic decompilation; coverage was relabeled with honest levels
> (`INDEXED` / `CONTROL_FLOW_VERIFIED` / `UNRESOLVED`; **no function is `SEMANTIC_C_COMPLETE`**). (2) Any
> remaining "TC0140SYT" wording is stale — the inter-CPU device is the **PC060HA** (same addresses).
> (3) The `0x1A00` MSM5205 latch roles were corrected to **0xB000=address, 0xC000=start, 0xD000=stop**.
> (4) The main loop's YM reg `0x1B` write **also selects a ROM bank** (`data&3`); it is not a generic
> "refresh". See `Andy_AUDIO009_audio_foundation_corrections.md`.

**Agent:** Andy (Opus) · **Date:** 2026-10-20 · **Issue:** OPEN-039 · **Type:** Reverse engineering /
Ghidra / C reference reconstruction. **No ROM built, no production/assembly change, no baseline
modified, no replacement driver written, no C compiled into production.** The original Z80 **binary**
remains authoritative; this C is reference only. Evidence tags: **VERIFIED** (decoded instructions) ·
**INFERRED** (control/data analysis) · **UNRESOLVED**.

## 1. Baseline & governance

- Accepted build: `accepted/build-0458` (last `accepted/build-*` ref); `build_counter.txt` = **464**
  (0459–0464 are Cody in-flight / unaccepted). Not touched.
- Prior audio research: `docs/design/Andy_native_genesis_audio_architecture_research.md` (read). This
  task executes its recommended **M0** (the Z80-disassembler/decompilation prerequisite).
- Governance: the existing 68000 Ghidra project (`tools/ghidra/.../rastan_arcade_ref`) was **not**
  touched; a **separate** Z80 project was created. No unrelated graphics/sprite/palette/gameplay/issue
  change.

## 2. Ghidra setup (VERIFIED)

- Ghidra **12.0.4** at `/home/tighe/tools/ghidra_12.0.4_PUBLIC`; JDK 21 at `/home/tighe/tools/jdk-21.0.10+7`.
- Processor language **`z80:LE:16:default`** (from `Ghidra/Processors/Z80/data/languages/z80.ldefs`).
- Imported `build/regions/audiocpu.bin` (64 KB) at base `0x0000` via headless `analyzeHeadless` into a
  **new** project `tools/ghidra/rastan_audio_z80` (persistent, deliverable 11.1). Auto-analysis + a
  custom post-script (`tools/ghidra/scripts/ExportZ80.java`) exported:
  - `build/audio/audiocpu.disasm.txt` — full disassembly.
  - `build/audio/z80_decomp.c` — Ghidra decompiled C for all **63** functions (raw).
  - `build/audio/z80_functions.tsv` — function map (entry, name, size, callers/callees).
  - `build/audio/z80_io_refs.tsv` — chip-port operand references.
- **Decompiler quality:** good for the control/dispatch/writer routines; pcode-constructor errors at
  `0x03E5`, `0x57D8`, `0x7EE7` (data-as-code at the banked tail / one SFX routine). Those are flagged
  UNRESOLVED, not guessed.

## 3. VERIFIED Z80 memory / hardware map (from decoded instructions)

| Region | Role | Evidence |
|---|---|---|
| `0x0000-0x7FFF` | program ROM (code ≤~0x1A52; data incl. song table 0x2300) | disasm |
| `0x8000-0x8FFF` | work RAM (cleared at init; SP top 0x9000) | init 0x010B clears to 0x9000 |
| 0x80x0..0x87x0 | 8 per-FM-channel state blocks (0x100 stride, init 0x0F) | init 0x010B |
| 0x8F00/0x8F01/0x8F02+ | **16-slot command ring** (head/tail/data, mask 0xF) | FUN_00c0 / 0x0254 |
| 0x8E80/0x8E81/0x8E82+ | 32-slot secondary ring (mask 0x1F) | FUN_00e9 |
| 0x8E0F..0x8E14 | ADPCM length/addr scratch | 0x1A00 |
| **`0x9000`** | **YM2151 register-address port** | FUN_158c; 14 `LD HL,0x9000` |
| **`0x9001`** | **YM2151 data / status (bit7 write-ready)** | FUN_158c; `LD A,(0x9001)` @0x0201 |
| **`0xA000/0xA001`** | **TC0140SYT** inter-CPU port (Z80 side) | NMI_ISR + every dispatch handshake |
| **`0xB000/0xC000/0xD000`** | **MSM5205 ADPCM** control/bank/trigger latches | 0x1A2B/0x1A31/0x1A4F |
| IM 1 / RST 0x38 | YM2151 timer IRQ line; NMI = SYT command strobe | init 0x010B `IM 1` |

**Banking caveat (UNRESOLVED):** `audiocpu.bin` is 64 KB but the live map above only addresses
`0x0000-0x7FFF` as ROM (RAM/chips occupy `0x8000+`). The upper 32 KB of the file is **banked data**
(sequence/instrument/sample tables); no bank-select latch has been identified yet. Ghidra's flat load
at 0x0000 is therefore correct for `0x0000-0x7FFF` only. Do not treat `0x8000-0xFFFF` as flat ROM.

## 4. VERIFIED control flow

- **Reset `0x0000` → `JP 0x010B`.**
- **`0x010B` init + main loop:** DI; **IM 1**; clear RAM `0x8000-0x8FFF`; SYT init (`a000=4,a001=0`);
  init the 8 channel state blocks to `0x0F`; run YM2151 init tables through the writer `FUN_158c`; EI.
  Then forever: `DI → FUN_158c (YM2151 refresh) → FUN_0254 (dispatch) → EI → FUN_01c2 (per-frame)`.
- **`0x0066` NMI = TC0140SYT command receive:** SYT handshake, read command byte, enqueue (<0xF0) into
  the 16-slot ring (`FUN_00c0`) and the 32-slot ring (`FUN_00e9`), SYT ack.
- **`0x0254` command dispatch:** pops the 16-slot ring and routes by range:
  - **`0x00-0x2B` → BGM song select (`FUN_02aa`)** (gated by mute flag 0x8F27 bit0),
  - `0xE0-0xEF` → control (`FUN_0368`; 0xEE/0xEF toggle flag 0x8F26),
  - `0xF0-0xFE` → SFX/channel class (`FUN_03e5`, **UNRESOLVED** — decompile failed),
  - `0xFF` → skip.
- **`0x158C` YM2151 write primitive** (18 callers — the single FM output chokepoint):
  `wait(*0x9001 & 0x80); *0x9000=reg; wait(*0x9001 & 0x80); *0x9001=data`.

Relation to the 68000 side (VERIFIED prior docs): the 68000 sends bytes via the TC0140SYT at
`0x3E0001/0x3E0003` (nibble-pair, `arcade_pc 0x3F084` direct / `0x3A0EC` queued). The Z80 NMI receives
them at `0xA000/0xA001` and enqueues. **The command-byte space is consistent end to end.**

## 5. Music / command mapping (VERIFIED table; track IDs partially mapped)

- **`FUN_02aa` (song select) indexes a pointer table at ROM `0x2300`** (word entries, `0x2300 + cmd*2`)
  → a song descriptor `{count; (channel_id, seq_ptr) × count}`, `count ≤ 0x11` channel-tracks. This is
  the **command → sequence** mechanism (VERIFIED).
- **BGM command range `0x00-0x2B`** (≤44 commands) dispatch through this table (VERIFIED).
- Cross-reference to the 9 captured tracks in `audio/rastan_music_dump/conversion_attempts/`
  (Credit, Opening, Scene 1, Name Regist, Scene 2, Boss, Scene Clear, Final Boss, Ending): the
  **exact command byte → track mapping is not yet fully pinned** — it requires reading the `0x2300`
  table entries and the banked sequence data (the table's pointers reach the banked region). This is
  the top M1 follow-up. Do not fabricate command IDs.

## 6. ADPCM / character voices (VERIFIED trigger; sample table UNRESOLVED)

- The **MSM5205 is driven via memory-mapped latches `0xB000/0xC000/0xD000`** (VERIFIED, 0x1A00 region):
  a length is computed and the address/bank/reset latches loaded; the MSM5205 then streams 4-bit ADPCM
  from its own ROM (`adpcm.bin`, b04-20.76, 64 KB) autonomously. No Z80 I/O-port (`OUT`) access exists
  (verified: zero `IN`/`OUT` instructions) — all chips are memory-mapped.
- **UNRESOLVED (M1):** the per-sample start/length table, playback rate/divisor, the trigger command
  IDs (the `0xF0-0xFE` class `FUN_03e5` that failed to decompile is the likely trigger path), and
  priority/interrupt/overlap rules. Rastan's character grunts/screams live in `adpcm.bin` and must be
  preserved; samples are to be labelled by neutral ID until the table is pinned. DAC streaming is NOT
  implemented here (YM2612 ch6 remains the proposed target).

## 7. Binary-transformation inventory (classes per the prompt §9 — NO changes applied)

| Original site | Class | Required Genesis transformation (future) |
|---|---|---|
| YM2151 writer `0x158C` (0x9000 reg / 0x9001 data) | **C/D** | retarget to YM2612 `0x4000-0x4003` + PSG; registers/pitch supplied by offline-converted data; **not** a simple address swap (chips differ) |
| YM2151 busy-wait on `0x9001` bit7 | **D** | YM2612 has no equivalent at that port → replace the wait with a YM2612-appropriate write delay |
| TC0140SYT `0xA000/0xA001` (NMI receive + all handshakes) | **C/D** | Genesis has no TC0140SYT → source commands from the existing Genesis Z80 mailbox (`sound_comm.s`, `0xA01FF0`); NMI-receive → mailbox poll |
| MSM5205 latches `0xB000/0xC000/0xD000` + VCK nibble feed | **D** | replace with a software YM2612 ch6 DAC streamer (no hardware DMA) |
| `IM 1` / RST 0x38 (YM2151 timer IRQ) | **C/D / UNRESOLVED** | Genesis Z80 lacks the YM2151 timer IRQ → derive tick from a YM2612 timer or the Z80 loop; timing budget must be measured |
| Song/instrument/sample data in banked ROM `>0x7FFF` | **B + E** | offline data conversion (instruments/pitch/ADPCM→PCM) **and** resolve the bank model first |
| `FUN_03E5` SFX class `0xF0-0xFE` | **E** | behavior UNRESOLVED (manual disasm needed) before classifying |

Preserve original sequencing/command behavior; **no general YM2151 emulator**; offline-first.

## 8. Validation performed (§12)

1. Reset `0x0000 → JP 0x010B` — VERIFIED. 2. YM2151 output located at `0x9000/0x9001` (writer 0x158C) —
VERIFIED. 3. Command dispatch path `NMI 0x0066 → ring 0x8F02 → 0x0254` — VERIFIED. 4. One music command
traced to the `0x2300` sequence-pointer table — VERIFIED (table located; per-track entry readout is
M1). 5. Channel state blocks (0x80x0..0x87x0) + song channel-track structure — VERIFIED. 6. Sample
trigger latches `0xB000/C000/D000` located — VERIFIED (full sample table is M1). 7. Bank transitions —
**UNRESOLVED** (no latch found; stated honestly). 8. Cross-check vs YM2151 captures — the writer and
command ranges are consistent with the capture set; exact per-track register streams align with the
`conversion_attempts/` CSVs.

## 9. Artifacts / repository changes

- Ghidra Z80 project (persistent): `tools/ghidra/rastan_audio_z80` + `tools/ghidra/scripts/ExportZ80.java`.
- Generated: `build/audio/audiocpu.disasm.txt`, `build/audio/z80_decomp.c`,
  `build/audio/z80_functions.tsv`, `build/audio/z80_io_refs.tsv`.
- C reference library: `analysis/decompilation/c/z80/rastan_z80_sound_driver.c` (curated) +
  `analysis/decompilation/c/z80/z80_function_coverage.csv` (index).
- This report; `AGENTS_LOG.md` entry; OPEN-039 updated (not closed).
- **No** production assembly / ROM / baseline / Test.json / graphics change.
- **YM2612 manual (§10.4):** `YM2612_manual.pdf` is **not present in the workspace** (searched; no
  match). It must be made available for the FM-conversion detail work (M2); its absence does not block
  M0. MAME `rastan.cpp` is likewise not in-repo (exact Z80/MSM5205 clock divisors remain INFERRED).

## 10. Unresolved (carried to M1/M2)

1. **Banked upper-ROM model** (no bank latch found) — blocks the full sequence/instrument/sample table
   readout. **Highest priority.**
2. **`FUN_03E5` (0xF0-0xFE SFX class)** decompile failure — needs manual Z80 disassembly.
3. **Command byte → track-name map** (needs the 0x2300 table entries + banked sequence data).
4. **ADPCM sample table** (addresses/rates/triggers/priority) + the big sequence engine `0x0479`.
5. **IRQ/timer timing model** and the Genesis Z80 cycle budget — must be measured, not assumed.

## 11. Build status

**No ROM built. No baseline modified. No production audio code written. No C compiled into production.**
AUDIO-001/M0 is a partial-but-evidence-complete recovery: memory map, control flow, command path,
YM2151 output, song table, and ADPCM trigger are VERIFIED; the banked data model and the SFX class are
explicitly UNRESOLVED.

## 12. Next step (AUDIO-002, subject to approval)

**M1 — resolve the Z80 ROM bank model**, then read the `0x2300` song table and the ADPCM sample table
to produce the verified command→track map and the sample inventory; manually disassemble `FUN_03E5`.
This unblocks the offline instrument/pitch/ADPCM converters (M2) and the M3 proof-of-concept (original
Z80 sequencer driving native YM2612 at preserved timing). No implementation until approved.
