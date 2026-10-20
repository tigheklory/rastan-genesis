# Andy — Native Genesis Audio Architecture Research (Rastan ReROM)

**Agent:** Andy (Opus) · **Date:** 2026-10-20 · **Type:** Architecture research / static analysis /
design ONLY. **No implementation, no ROM build, no MAME run, no production/assembly change, no baseline
modification.** Evidence tags: **VERIFIED** (source/ROM/doc proven) · **INFERRED** (analysis, not
directly proven) · **PROPOSED** (prospective design) · **UNRESOLVED** (needs further investigation).

This single report carries the prompt's logical deliverables A–E as Parts A–E, plus Phase 0.

---

## PHASE 0 — BASELINE, PRIORS, AVAILABILITY (VERIFIED)

- **Accepted baseline:** `accepted/build-0458` (the newest `accepted/build-*` ref). `build_counter.txt`
  = 462; Builds 0459–0462 are Cody in-flight / not yet an accepted ref. **This research modifies no
  build and requires no ROM.** The research can proceed fully without touching the baseline — **YES**.
- **Original audio ROMs are present locally (VERIFIED):** `build/rom_inventory.json` + `build/regions/`:
  - `audiocpu.bin` = **b04-19.49**, 65536 B, sha1 `fa59dac2583a…` — the **Z80 sound program**.
  - `adpcm.bin` = **b04-20.76**, 65536 B, sha1 `b1682959521f…` — the **MSM5205 ADPCM sample ROM**.
  - `maincpu.bin` — arcade 68000 program (reconstructed; variant `world_rev1`).
  So no STOP-on-availability applies; real static analysis is possible.
- **Existing Genesis audio implementation (VERIFIED):** a **forced-tone Z80 bring-up stub** only.
  `apps/rastan-direct/src/sound/z80_driver.s` (96 lines) is a hand-assembled Z80 blob that programs a
  single YM2612 patch + key-on in a loop with a heartbeat marker (no mailbox-driven playback).
  `apps/rastan-direct/src/sound/sound_comm.s` (73 lines) is the 68000-side upload/mailbox shim:
  `Z80_RAM 0xA00000`, `Z80_MAILBOX 0xA01FF0`, `Z80_BUSREQ 0xA11100`, `Z80_RESET 0xA11200`, run/heartbeat
  markers `0xA01FF2/0xA01FF3`. **No real music/SFX/sample playback exists yet.**
- **Verified inherited prior work (reuse, do not re-derive):**
  - 68000→sound command path — `docs/design/Andy_rastan_sound_command_execution_verified.md`,
    `Andy_rastan_arcade_sound_and_rainbow_bridge.md`.
  - Genesis sound ownership reference model — `docs/design/Cody_rainbow_islands_sound_translation_analysis.md`.
  - Bring-up tone debug — `docs/design/Cody_rastan_direct_forced_z80_tone_debug.md`.
  - **Captured music** — `audio/rastan_music_dump/conversion_attempts/` holds per-track YM2151
    register-write CSVs + VGM conversion summaries for **9 named tracks**.
  - Findings **KF-027** (6-slot sound queue silently drops on full), **KF-055/056** (TC0140SYT status
    read busy-wait; Genesis has no TC0140SYT, redirected in Build 0194).
- **Unresolved assumptions requiring investigation (carried into the parts below):** the internal
  structure of the arcade Z80 driver (sequence decode, register-output routine, timers, sample
  triggers, the 0xA000/0xB000 port roles) — a full audit needs a **Z80 disassembler**, which the repo
  does not currently have (capstone has no Z80 backend). This is the single biggest tooling gap and the
  first recommended POC-tooling step; it is NOT a blocker for this architecture research.

**Governance note / correction to the prompt:** the prompt's preliminary table calls the 68000↔Z80
link a raw Z80 `$9000/$9001` mailbox. That is the **YM2151** mapping, not the CPU link. The actual
arcade inter-CPU chip is the **TC0140SYT** at 68000 `0x3E0001/0x3E0003` (VERIFIED, prior docs). The
YM2151 is at **Z80 `0x9000/0x9001`** (VERIFIED below). These are different buses; I keep them distinct.

---

## PART A — ORIGINAL ARCADE AUDIO ARCHITECTURE AUDIT

### A.1 Hardware (VERIFIED where tagged)

| Component | Arcade part | Evidence |
|---|---|---|
| Sound CPU | Z80 (~4 MHz) | INFERRED (Taito `rastan` board; clock exact value UNRESOLVED without the MAME `rastan.cpp` driver, which is not in-repo) |
| FM | Yamaha YM2151, 8 ch 4-op | VERIFIED mapping (below); chip identity INFERRED from board |
| Samples | MSM5205 4-bit ADPCM | VERIFIED ROM present (`adpcm.bin`, region `adpcm`); playback params UNRESOLVED (Z80 disasm) |
| Inter-CPU | TC0140SYT @ 68000 `0x3E0001/0x3E0003` | VERIFIED (prior docs + KF-055/056) |
| Main CPU | 68000 | VERIFIED |

### A.2 68000 → Z80 command path (VERIFIED — inherited)

- Single send helper **`arcade_pc 0x3F084`** (direct, no busy-wait): writes `0` to `0x3E0001`, then the
  command byte to `0x3E0003`, then `byte>>4` to `0x3E0003` — **nibble-pair** protocol; Z80 reconstructs
  `cmd = (write2&0x0F)<<4 | (write1&0x0F)`.
- Queued path via **`0x3A0EC`** (6-slot ring), flushed through `0x3F084`; status read at `0x3F0A4`
  (`moveb 0x3E0003,%d0`, bit 0 = busy). **KF-027:** queue silently drops on full. **KF-055/056:** on
  Genesis there is no TC0140SYT; the status read is redirected (Build 0194) so the busy-wait exits.
- Command byte is 8-bit; BGM (direct) and SFX (queued) share the byte space. **Exact command-byte →
  track/SFX-ID table is UNRESOLVED** (lives in the Z80 dispatch; needs Z80 disasm).

### A.3 Z80 chip I/O mapping (VERIFIED by direct byte-scan of `audiocpu.bin`)

Scanning the Z80 program for 16-bit immediate addresses in load/store opcodes:
- **YM2151 at `0x9000` (address/latch) and `0x9001` (data + status)** — **VERIFIED**: 14 `LD HL,0x9000`
  sites (e.g. Z80 offsets `0x15F, 0x1AC, 0x20C, 0x479, 0x793, 0x939, 0x95B, 0x983`) and one
  `LD A,(0x9001)` at `0x201` (the YM2151 status/timer read). This directly confirms the prompt's
  `$9000/$9001` assumption from the program itself.
- **`0xA000` — 23 `LD (0xA000),A` sites** (e.g. `0x6B, 0x73, 0xB7, 0x113, 0x11B, 0x132, 0x193, 0x1A4`):
  INFERRED to be the MSM5205/ADPCM data or sample-ROM bank latch (heavy, data-like traffic). Exact role
  UNRESOLVED (Z80 disasm).
- **`0xB000` — 1 `LD (0xB000),A`** at `0x1A31`: INFERRED MSM5205 reset/mode or bank control. UNRESOLVED.
- **`0x8000` — `LD HL,0x8000`** (`0x124, 0x480, 0x745, 0x748`): INFERRED Z80 work-RAM / ROM-bank window
  base. UNRESOLVED.

### A.4 Z80 driver internal structure (UNRESOLVED — needs a Z80 disassembler)

The YM2151 write sites above locate the register-output routine(s); a full audit of reset/init,
command dispatch, sequence decode, instrument/voice tables, pitch/detune math, envelope/volume, tempo
and YM2151-timer/interrupt dependency, sample address/playback, and channel priority **requires
disassembling `audiocpu.bin`**. Capstone has no Z80 backend; the repo has no Z80 disassembler. **This is
the first POC-tooling task (Part E).** Nothing here is fabricated: only the byte-scan-proven mappings
are tagged VERIFIED.

---

## PART B — COMPLETE AUDIO ASSET INVENTORY

### B.1 Music (VERIFIED tracks; captured register streams)

Nine tracks are captured in `audio/rastan_music_dump/conversion_attempts/` as YM2151 register-write
CSVs (`sample,seconds,register,value`) + VGM conversion summaries:

| # | Track (captured name) | Role | YM2151-write CSV rows | capture length |
|---|---|---|---|---|
| 01 | Credit | credit jingle | 156 | short |
| 02 | Broken The Promises (Opening) | opening/attract | 4,327 | ~ |
| 03 | Aggressive World (Scene 1) | Round-1 BGM | 16,189 writes | ~52.4 s (summary) |
| 04 | Bad Bible (Name Regist) | name-entry | 1,142 | short |
| 05 | Re-In-Carnation (Scene 2) | Round-2 BGM | 44,341 | long |
| 06 | The Devil Boss Carnival (Scene 3 Boss) | boss BGM | 12,144 | ~ |
| 07 | Scene Clear | round-clear jingle | 3,197 | short |
| 08 | Final Destroy (Scene 3 Round 6 Boss) | final-boss BGM | 37,680 | long |
| 09 | The Man Of Saga (Ending) | ending | 42,607 | long |

- **VERIFIED:** the track set, their names, and their complete YM2151 register-write streams (captured).
  Per-channel usage, peak simultaneous voices, tempo, and loop points are **derivable offline** from
  these CSVs (the Python tool in Part D does this — the register writes to `0x20-0x27` key-on/algorithm,
  `0x28-0x2F` KC, `0x30-0x37` KF, `0x60+` TL, `0x08` key-on per channel fully determine channel
  activity). I did **not** re-trace; these are the existing capture.
- **UNRESOLVED:** the **arcade sound-command byte → track ID** mapping (lives in the Z80 dispatch); the
  captures are named by musical identity, not yet tied to the 68000 command byte. Per the prompt, do
  NOT infer channel assignment from the command number.

### B.2 Sound effects + character voices / ADPCM (ROM VERIFIED; boundaries UNRESOLVED)

- `adpcm.bin` (64 KB) is present and parseable: 243 distinct byte values, 0xFF-dominant (14,630) —
  consistent with packed 4-bit MSM5205 ADPCM with 0xFF padding between samples. **VERIFIED present.**
- **UNRESOLVED (needs Z80 disasm of the sample-trigger/address table):** per-sample start/stop
  addresses, decode mode/clock, playback frequency, trigger command IDs, durations, restart/interrupt
  behavior, overlap/concurrency, and prioritization. Rastan's character grunts/screams live here and
  **must be preserved**; the inventory table is the Part-E "sample map" deliverable, blocked on the Z80
  sample table. Do not treat these as expendable.

---

## PART C — NATIVE GENESIS AUDIO FEASIBILITY

### C.1 Target hardware (VERIFIED from the existing Genesis sound path + Rainbow Islands reference)

Genesis Z80 drives: **YM2612** (6 FM ch) at Z80 `0x4000-0x4003`, **SN76489 PSG** (3 tone + 1 noise) at
`0x7F11`, **DAC** via YM2612 ch6 (register `0x2A` sample byte stream, enabled by `0x2B` bit 7). The
68000 uploads the Z80 driver to `0xA00000` and arbitrates via `0xA11100/0xA11200`. The ReROM already
has this upload/mailbox infrastructure (`sound_comm.s`); only the driver content is a stub.

### C.2 YM2151 → YM2612 FM conversion (INFERRED/PROPOSED)

- Both are 4-operator FM; operator ordering, algorithm/feedback, multiplier, DT1, TL, AR/DR/SR/RR, and
  key-scaling map **approximately**; register LAYOUT differs and must be re-encoded offline.
- **Convertible exactly (offline):** algorithm, feedback, MUL, TL, DT1, AR/D1R/D2R/RR/D1L (with
  range/curve re-mapping). **Approximate:** key-scaling (KS/RS curves differ), LFO/PMS/AMS (YM2151
  global LFO vs YM2612 per-chip), stereo (YM2151 per-channel L/R vs YM2612 L/R bits). **Not exact:**
  the YM2151 noise generator (ch8 NE) has no YM2612 equivalent.
- **Count mismatch:** YM2151 has **8** FM channels; YM2612 has **6** (and ch6 is reserved for DAC, see
  C.4) → effectively **5 FM** + PSG for the rest. This forces per-track routing (Part C.5 / the prompt's
  core requirement).

### C.3 Pitch conversion (PROPOSED — clock-correct, offline)

- YM2151 pitch = **KC (key code, octave+note) + KF (key fraction)**; YM2612 pitch = **Block (octave) +
  F-Number (11-bit)**. Convert by computing the **intended musical frequency** from the YM2151 KC/KF and
  the **YM2151 input clock**, then solving the YM2612 F-Num/Block from that frequency and the **YM2612
  input clock** (Genesis NTSC ≈ 7.67 MHz): `fnum = round(freq * 2^(20-Block) / (clock/144))` with Block
  chosen so F-Num is in range. **Do NOT scale by the ratio of the two chips' clocks** (the prompt's
  explicit prohibition) — that corrupts pitch. All of this is offline Python; a compact per-note F-Num
  table (12 notes × block, + fine KF interpolation) is the only runtime artifact, if any.
- **UNRESOLVED:** how much pitch is computed dynamically by the Z80 driver (pitch bends, vibrato via the
  YM2151 LFO) vs ROM-encoded — determines whether a tiny runtime pitch op is unavoidable. Needs Z80
  disasm.

### C.4 ADPCM → DAC (PROPOSED)

- Offline-convert MSM5205 4-bit ADPCM → unsigned 8-bit PCM in Python (MSM5205 step-table decoder).
  Play on **YM2612 ch6 DAC**: the Genesis Z80 writes each PCM byte to YM reg `0x2A` at the target rate.
  This is **software sample streaming, NOT hardware DMA** (per the prompt).
- **Concurrency constraint (INFERRED, must be measured):** one DAC stream reproduces one sample at a
  time. The arcade MSM5205 is likewise effectively one ADPCM voice, so **single-stream DAC is likely
  sufficient** for the original concurrency — but overlap/interruption behavior is UNRESOLVED until the
  Z80 sample logic is read. **Cycle budget for DAC streaming + sequencing on one Z80 is UNRESOLVED**
  (must be measured, not claimed).
- **DAC reservation:** YM2612 ch6 is reserved primarily for original sample/voice playback; music FM
  does not freely use DAC mode. Whole-song PCM is explicitly **rejected** (prompt §9 / failure cond.).

### C.5 Concurrency / routing feasibility (PROPOSED)

8 YM2151 FM voices → {5 usable YM2612 FM} + {3 PSG tone + 1 PSG noise} per track, with ch6=DAC. Static
analysis of each track's capture CSV can pre-compute peak simultaneous voices and channel occupancy, so
voice conflicts are **knowable in advance offline**. PSG is a square-wave tone generator and is **not
equivalent to 4-op FM** (prompt failure condition) — PSG routing is a deliberate per-voice approximation
for sustained/lead/bass lines the track can tolerate, chosen by the user per track, never automatic.

---

## PART D — CONFIGURABLE AUDIO COMPILER + MANAGEMENT TOOL DESIGN (PROPOSED)

### D.1 Offline Python compiler pipeline

Deterministic, traceable to source ROM:
1. Read `audiocpu.bin` + `adpcm.bin` (+ the captured CSVs as cross-check).
2. Parse the Z80 instrument/voice tables and sequence pointers (**blocked on Z80 disasm**; interim it
   can consume the captured register streams).
3. Convert YM2151 instruments → YM2612 patch data (C.2).
4. Convert note pitch → F-Num/Block table (C.3).
5. Generate PSG approximations for voices the routing profile assigns to PSG.
6. Convert MSM5205 ADPCM → 8-bit PCM (C.4).
7. Apply the user's per-track routing profile.
8. Emit translated instrument/sequence/sample artifacts + the **minimal** Z80 register-retarget
   (YM2151 reg/addr → YM2612 reg/channel or PSG), **preserving original sound-command IDs**.
9. Identify the smallest required Z80 opcode changes (retarget the `0x9000/0x9001` writes; add the DAC
   streamer; replace MSM5205 port writes). **Not a general YM2151 emulator** (failure condition).
10. Integrate as a build-time stage producing version-controlled artifacts.

### D.2 Per-track routing configuration (JSON schema, PROPOSED)

```jsonc
{ "track_id": "03_aggressive_world_scene1",
  "arcade_command_byte": null,               // UNRESOLVED until Z80 dispatch read
  "routing": { "ym2151_ch1": "ym2612_fm1", "ym2151_ch3": "psg_tone1", ... },
  "instrument_overrides": { "ym2151_ch5": "patch_id_or_inline" },
  "priority": { ... }, "mute": [], "dac_reserved": "ym2612_ch6" }
```
Repository-canonical, one profile per track, multiple alternative profiles allowed; **no universal
hardcoded mapping** (failure condition). Mirrors the project's existing registry discipline
(`palette_decisions.json`, the graphics editor's Test profile).

### D.3 Audio management application (PROPOSED — independent of `tools/graphics_editor/`)

Browser UI + Python backend (same conventions as the graphics editor, separate app): browse music/SFX/
voice inventory; per-track 8-channel view with instruments + activity timeline (derived from the capture
CSVs); channel routing selectors (YM2151 ch → YM2612 FM / PSG tone / PSG noise / mute); instrument-
profile editor; priority/sharing config; save per-track JSON; multiple profiles; sample previews;
original-vs-converted compare; **conflict warnings** when assignments exceed 5 FM / collide on PSG / use
ch6 against the DAC reservation.

**Preview methodology (honesty constraint):** a browser WebAudio synth is a convenience preview and is
**NOT evidence of Genesis fidelity**. Authoritative preview requires rendering the converted stream
through a **Genesis emulator (BlastEm / MAME `genesis`)** or hardware. The tool must label browser
previews as approximate and gate "fidelity" claims on emulator/hardware output.

---

## PART E — RECOMMENDED IMPLEMENTATION PLAN (PROPOSED — no implementation now)

Each milestone states acceptance criteria + evidence. **All are future, approval-gated.**

- **M0 — Z80 disassembler tooling (prerequisite).** Add a Z80 disassembler (e.g. `z80dasm` or a
  project-owned Python Z80 disasm) and produce `build/audiocpu.disasm.txt`. *Accept:* the YM2151 write
  routine, command dispatch, sequence reader, instrument tables, MSM5205 trigger/address table, and the
  0xA000/0xB000 roles are identified with offsets. *Evidence:* disassembly + cross-check against the
  byte-scan sites in A.3.
- **M1 — Asset inventory completion.** From M0 + the capture CSVs, produce the full music table (command
  byte → track, channel usage, tempo, loop, peak voices) and the ADPCM sample map (addresses, rates,
  triggers, durations). *Accept:* every track and sample enumerated with source offsets; no PENDING in
  the inventory. *Evidence:* generated inventory JSON traceable to ROM.
- **M2 — Offline instrument + pitch converter (Python).** YM2151→YM2612 patches + F-Num/Block table.
  *Accept:* round-trip a known track's instruments; pitch error < 1 cent vs intended musical frequency
  (computed, not clock-ratio). *Evidence:* converter unit tests + numeric comparison.
- **M3 — PROOF OF CONCEPT (the prompt's first experiment).** Can the **original Z80 sequencer drive
  native YM2612 output while preserving original music timing?** Port the arcade Z80 driver onto the
  Genesis Z80 with (a) offline-converted instruments/pitch loaded, (b) YM2151 register writes retargeted
  to YM2612 `0x4000-0x4003`, (c) one captured track (e.g. "Scene Clear", short) driven end-to-end.
  *Accept:* on BlastEm/MAME `genesis`, the track plays with tempo/length matching the arcade VGM within
  a small tolerance, no gameplay regression, DAC ch6 left free. *Evidence:* emulator capture vs arcade
  VGM timing diff. *This is a separate build task, NOT this research.*
- **M4 — DAC sample streamer + reservation.** Stream one converted ADPCM voice on ch6 concurrent with
  M3 music. *Accept:* a character-voice sample plays recognizably over music; measured Z80 cycle budget
  shows headroom (measured, not assumed). *Evidence:* emulator audio + cycle measurement.
- **M5 — Per-track routing profiles + management app.** JSON routing consumed by the compiler; app
  authors it. *Accept:* two alternative profiles for one track produce the expected channel outputs.
- **M6 — Full inventory conversion + build integration.** All tracks/SFX/voices through the pipeline.

---

## TECHNICAL RISKS / UNRESOLVED

1. **Z80 driver internals** — no in-repo Z80 disassembler (capstone lacks Z80). Blocks Parts A.4, B.1
   (command→track), B.2 (sample map), and the dynamic-vs-ROM pitch question. **Primary next step (M0).**
2. **Cycle budget** — single Z80 doing sequencing + register programming + DAC streaming concurrent with
   the ReROM graphics/gameplay 68000 workload: UNRESOLVED; must be **measured**, not claimed.
3. **8→5 FM + PSG routing** — musical acceptability is per-track and subjective; PSG ≠ 4-op FM.
4. **YM2151 LFO / noise (ch8)** — no exact YM2612 equivalent; approximation or PSG-noise substitution.
5. **MAME `rastan.cpp` driver not in-repo** — exact Z80 clock and MSM5205 clock/divisor are INFERRED;
   M1 should confirm against the driver or hardware docs (STOP if a conclusion depends on an unverified
   clock).

## REPOSITORY / ISSUE IMPACT

- Documentation added: this report. **No** production/assembly/ROM/baseline change; **no** Test.json or
  palette change; graphics/sprite/tilemap/gameplay untouched.
- Issue ledger: new **OPEN-039** (native Genesis audio architecture) opened, referencing KF-027 /
  KF-055 / KF-056 and this report. No settled issue reopened; nothing closed on speculative feasibility.

## IMPLEMENTATION STATUS

**No code implemented. No ROM built. No MAME run. No baseline modified.** This is research + design,
stopped for architectural review. Recommended first action after approval: **M0 (add a Z80 disassembler
and produce `build/audiocpu.disasm.txt`)**, which unblocks the inventory and the M3 proof-of-concept.
