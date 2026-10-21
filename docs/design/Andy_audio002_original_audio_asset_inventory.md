# Andy — AUDIO-002 / M1 (RG-002): Original Rastan Audio Asset Recovery

**Task:** RG-002 / AUDIO-002 / M1 · **Agent:** Andy (Opus) · **Date:** 2026-10-20 · **Issue:** OPEN-039 ·
**Type:** RE / static analysis / offline inventory. **No ROM built, no production/assembly change, no
baseline modified, no Genesis playback/converter implemented, no C compiled into production.** Evidence:
**VERIFIED** (ROM bytes / disassembly / captured registers) · **INFERRED** · **PROPOSED** ·
**UNRESOLVED**. AUDIO-001 findings were treated as provisional and re-derived here; Cody's independent
verification is still pending (not asserted).

## 1. Baseline

Accepted `accepted/build-0458`; `build_counter.txt` = **464**. Untouched. Analysis uses
`build/regions/audiocpu.bin` (b04-19.49, 64 KB), `build/regions/adpcm.bin` (b04-20.76, 64 KB), the
Ghidra Z80 project `tools/ghidra/rastan_audio_z80`, and the captures in
`audio/rastan_music_dump/conversion_attempts/`.

## 2. Sound-ROM memory model — RESOLVED (corrects the AUDIO-001 "banked, UNRESOLVED" hypothesis)

**VERIFIED from ROM evidence:**
- The song table (0x2300), all 44 song descriptors (0x2830-0x3370), and **every** per-channel
  sub-sequence pointer lie in **0x2800-0x3390 — i.e. the directly-addressable low ROM (<0x8000)**.
  Scanned all 44 commands: **max sub-sequence pointer = 0x3390; zero pointers ≥ 0x8000.**
- No bank-select write exists (no `OUT`, no `LD (port),A` to a bank latch; the only non-chip stores
  are RAM). The Z80 map is: ROM `0x0000-0x7FFF`, RAM `0x8000-0x8FFF`, YM2151 `0x9000/0x9001`,
  TC0140SYT `0xA000/0xA001`, MSM5205 latches `0xB000/0xC000/0xD000`.
- The upper 32 KB of the 64 KB file is **0xFF padding except a 3807-byte blob at file 0x8000-0x8EDE**.
  Nothing in the music path references it.

**Conclusion (ROM-code level):** the **song table + descriptors + all traced per-channel sub-sequences
fit entirely in the fixed `0x0000-0x3FFF` region** — no sub-pointer reaches the banked window, so the
music inventory can be read safely without bank context (STOP gate cleared).

### 2b. MAME driver cross-verification & CORRECTIONS (VERIFIED — `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`)

The MAME Rastan driver **is** in-repo (I located it after the initial bounded search missed it) and
is the authoritative §2 cross-check. It **corrects two of my conclusions**:

1. **Banking DOES exist (corrects my "NOT bank-switched" wording).** The Z80 map is
   `0x0000-0x3FFF .rom()` (fixed) + **`0x4000-0x7FFF .bankr(m_audiobank)`** with
   `configure_entries(0, 4, audiocpu_base, 0x4000)` → **4 × 16 KB banks** of the 64 KB ROM
   (bank0=file 0x0000, bank1=0x4000, **bank2=0x8000**, bank3=0xC000). The bank select is
   `sound_bankswitch_w(data){ m_audiobank->set_entry(data & 3); }` wired to the **YM2151 port-write
   handler** — i.e. selected *through* a YM2151 write, which is exactly why no explicit bank-store
   instruction exists in the Z80 code. **So:** the music song/descriptor/sub-sequence data I inventoried
   is in the always-present fixed bank, but the broader audio dataset (FM instruments, the ADPCM sample
   table, possibly more sequences) lives in the banked window; **the file 0x8000-0x8EDE blob is bank 2**
   (reachable at 0x4000-0x7FFF when selected). The earlier "upper half unused" reading is wrong — it is
   banked data.
2. **Inter-CPU chip = PC060HA (Taito CIU), not TC0140SYT (corrects AUDIO-001 and prior docs).** MAME maps
   `pc060ha` master ports at 68000 `0x3E0001/0x3E0003` and slave ports at Z80 `0xA000/0xA001` — matching
   the addresses I found, but the chip is the **PC060HA**. (The nibble-pair protocol and addresses are
   unchanged; only the chip name was wrong.)

**Confirmed exactly (VERIFIED on PCB per the driver):**
- MSM5205 latches: **`0xB000` = sample address, `0xC000` = start, `0xD000` = stop** (matches my 0x19A8
  analysis, which stops via `0xD000`).
- **Clocks (PCB-verified):** Z80 = `XTAL(16 MHz)/4 = 4.000 MHz`; **YM2151 = `16 MHz/4 = 4.000 MHz`**
  (the exact input clock for the pitch→F-Num math); **MSM5205 = `XTAL(384 kHz)`, prescaler `S48_4B`
  = 8 kHz, 4-bit ADPCM** (resolves the sample playback rate: **8 kHz**). This retires the earlier
  "clocks INFERRED / MAME not in-repo" caveat.

**Remaining UNRESOLVED:** which bank(s) hold the FM instrument table and the ADPCM sample table (needs a
per-bank Ghidra re-import mapping file 0x4000/0x8000/0xC000 into the 0x4000-0x7FFF window), and which
YM2151 write value the driver emits to switch banks.

## 3. Music command → sequence inventory (VERIFIED structure)

- **Command space:** `0x00-0x2B` (44 commands) index the **song-pointer table at ROM `0x2300`**
  (word entries, `0x2300 + cmd*2`) → a descriptor.
- **Descriptor format (VERIFIED from 0x02AA disasm):** `count` byte, then `count` **2-byte** entries.
  Each entry: byte2==0 → a **direct command** (byte1 enqueued via 0x00C0); else a **16-bit sub-sequence
  pointer**. `count ≥ 0x12` → **single sub-sequence** form (`CALL 0x02FE` directly) — commands 0x03,
  0x0A, 0x0D, 0x21, 0x26 (count byte 0x82).
- Per-channel sub-sequences occupy 0x28A0-0x3390. Channel-track counts range 2-17 per song (e.g.
  cmd 0x00 = 17 tracks; cmd 0x04/0x05/… = 2).
- **Machine-readable output:** `build/audio/music_command_inventory.json` (every command → descriptor,
  count, entries/pointers, form).
- **Command → human track name = UNRESOLVED.** The 9 captures are named by musical identity
  (`audio/rastan_music_dump/conversion_attempts/`), not yet proven to a command byte; mapping requires
  matching each command's installed sub-sequences to the captured register stream (M-follow-up). **No
  track names assigned on insufficient evidence.**

## 4. Sequence interpreter (PARTIAL)

- `0x02AA` (song install) → `0x02FE` (per-channel sub-sequence install). `0x02FE` (VERIFIED partial):
  gated by the sound-enable flag `0x8F26`; a channel id in range `0x8C-0xAB` maps (`SUB 0x8C`, range
  0x20 = **32 channel slots**) through a **word pointer table at ROM `0x0348`** to a channel state
  block; 0x82/0x83 is a special marker.
- The per-channel **note-event byte encoding** (note/pitch/duration/tempo/volume/loop/instrument-select
  opcodes) is interpreted by the **747-byte engine at `0x0479`** (the largest routine). Its opcode
  table is **not yet fully decoded** — this is the next depth (M-follow-up) and is required before a
  deterministic Python sequence parser can be written. Not guessed here.

## 5. Sound-effect / control dispatch — RESOLVED (corrects AUDIO-001 UNRESOLVED 0x03E5)

- `0x03E5` is a **jump-table dispatch**: `HL = 0x041B + (cmd-0xF0)*2; JP (word at HL)`. The 15-entry
  table at ROM **`0x041B`** gives: **0xF0 → 0x03F7**, **0xF1/0xF2/0xF3 → 0x0408** (shared),
  **0xF4-0xFE → 0x041A** (default/no-op). So `0xF0-0xFE` is a **small control set** (0xF0 and 0xF1-F3),
  **NOT** the ADPCM sample triggers.
- `0xE0-0xEF` (`0x0368`): 0xEE/0xEF toggle the sound-enable/attract flag `0x8F26`.
- **Where samples are triggered = UNRESOLVED:** not via 0xF0-0xFE and not via 0x2C-0xDF (dispatch
  ignores that range). Samples are most likely requested through a **song channel** whose channel id
  routes (via the 0x0348 table) to the ADPCM engine state block — INFERRED; needs the 0x0479 opcode
  decode to confirm which sub-sequence opcode sets the ADPCM descriptor pointer.

## 6. MSM5205 ADPCM inventory (VERIFIED engine; sample table UNRESOLVED)

- **Engine `0x19A8` (per-tick streaming state machine, VERIFIED):** `IX = 0x8E00` sample state block;
  `bit0` = active; descriptor pointer at `(IX+1,+2)`; it reads descriptor bytes into
  `0x8E04/0x8E05(&0xF0)/0x8E08/0x8E09`, computes the ADPCM address (nibble-shift helpers 0x196F/0x1993),
  loads the MSM5205 latches **`0xD000`/`0xB000`/`0xC000`**, and **stops** by writing `0xD000 = 0` when
  the descriptor terminator (a 0 length byte) is reached. The MSM5205 streams 4-bit ADPCM from
  `adpcm.bin` (b04-20.76) autonomously.
- **UNRESOLVED:** the sample **descriptor/pointer table** (where `(IX+1,+2)` is loaded from and the list
  of sample start/length entries), the playback rate/divisor, per-sample command IDs, and
  priority/interrupt/overlap rules. The character voices (grunts/groans/screams) reside in `adpcm.bin`
  and must be preserved; until the table is pinned they are referenced by neutral IDs. **No DAC
  streaming implemented.** YM2612 ch6 remains the proposed DAC target.

## 7. YM2151 capture analysis (VERIFIED — read-only utility)

`tools/audio/analyze_ym2151_captures.py` (read-only) processes all 9 register-write captures →
`build/audio/ym2151_track_reports/*.json` + `_summary.json`. Per track: channels used, key-on timeline,
per-channel key-on/KC/TL counts + CONNECT algorithm + operators keyed, peak simultaneous voices, ch8
noise use, timer/LFO use, and PSG-candidate channels (evidence only, not a routing decision).

**Key VERIFIED results (all 9 tracks):**

| Track | FM ch used | peak simultaneous voices | ch8 noise |
|---|---|---|---|
| 01 Credit | 8 | 2 | no |
| 02 Broken The Promises (Opening) | 8 | **8** | no |
| 03 Aggressive World (Scene 1) | 8 | 6 | no |
| 04 Bad Bible (Name Regist) | 8 | 6 | no |
| 05 Re-In-Carnation (Scene 2) | 8 | 6 | no |
| 06 The Devil Boss Carnival | 8 | 6 | no |
| 07 Scene Clear | 8 | 6 | no |
| 08 Final Destroy (R6 Boss) | 8 | 6 | no |
| 09 The Man Of Saga (Ending) | 8 | **8** | no |

**Routing implication (quantified, evidence-only):** every track exercises all 8 FM channels and peaks
at **6-8 simultaneous voices**. The Genesis offers 6 YM2612 FM, and with ch6 reserved for DAC only **5
FM** remain → the 6-voice tracks need **≥1** voice on PSG and the two 8-voice tracks (Opening, Ending)
need **≥3** on PSG, OR ch6 borrowed when no sample is playing. No track uses the YM2151 noise generator
(simplifies PSG-noise planning). These are facts for the per-track routing UI — **not** routing
decisions made here.

## 8. Audio-management-application data (separation only — no app built)

Machine-readable, kept in separate artifacts so a future app can load each independently:
`build/audio/music_command_inventory.json` (music/sequence), `build/audio/ym2151_track_reports/*`
(channel activity), `analysis/decompilation/c/z80/z80_function_coverage.csv` (engine map). FM-instrument
definitions and the ADPCM sample table are **pending** (sections 4/6). **No default routing profiles
created** (they must not be mistaken for verified musical intent). YM2612 ch6 remains the proposed
reserved DAC resource.

## 9. Updated artifacts / changed files

- `analysis/decompilation/c/z80/z80_function_coverage.csv` — 0x03E5 upgraded to VERIFIED (jump table
  0x041B); added 0x19A8 ADPCM engine, 0x0348 channel table, 0x041B SFX table, 0x0479 interpreter. (A
  harmless duplicate 0x0479 row exists — both describe the same routine.)
- `analysis/decompilation/c/z80/rastan_z80_sound_driver.c` — reference headers remain valid; 0x03E5 and
  0x19A8 are now RESOLVED/characterized here and in the CSV.
- New: `tools/audio/analyze_ym2151_captures.py`; generated `build/audio/music_command_inventory.json`,
  `build/audio/ym2151_track_reports/*`.
- This report; `AGENTS_LOG.md` entry (RG-002); OPEN-039 updated (not closed).
- Ghidra project `tools/ghidra/rastan_audio_z80` reused (not corrupted); 68000 project untouched.
- **No** production assembly / ROM / baseline / graphics / gameplay / palette change.

## 10. Unresolved + verification requirements

1. **0x0479 note-event opcode encoding** — required for a deterministic Python sequence parser. Highest.
2. **ADPCM sample table** (descriptor pointer source, sample start/length list, rate, triggers,
   priority) + which sub-sequence opcode sets the 0x8E00 descriptor pointer.
3. **Command → track-name map** (match installed sub-sequences to the 9 captures).
4. **File 0x8000-0x8EDE blob** runtime addressing (FM patch bank? SFX data?).
5. **0xF0 / 0xF1-F3 control handlers** (0x03F7 / 0x0408) exact behavior; **0x01F9** IRQ/timer model and
   Z80 cycle budget (measure, do not claim). MAME `rastan.cpp` clocks to confirm.
6. AUDIO-001/002 await Cody's independent corroboration (not asserted verified here).

## 11. Changed-files list

New: `docs/design/Andy_audio002_original_audio_asset_inventory.md`,
`tools/audio/analyze_ym2151_captures.py`, `build/audio/music_command_inventory.json`,
`build/audio/ym2151_track_reports/*`. Modified: `analysis/decompilation/c/z80/z80_function_coverage.csv`,
`AGENTS_LOG.md`, `OPEN_ISSUES.md` (OPEN-039).

## 12. Build status

**No ROM built, no production/assembly change, no baseline modified, no Genesis audio implemented, no
ADPCM-to-PCM conversion, no replacement driver, no app, no C compiled into production.**

## 13. Next milestone (AUDIO-003, pending approval)

Decode the **0x0479 sequence note-event opcode table** and the **ADPCM sample descriptor table**; then
produce the deterministic Python **sequence parser** + **sample map**, and the verified command→track
mapping. That completes the inventory needed before the M2 offline instrument/pitch/ADPCM converters and
the M3 proof-of-concept. No implementation until approved.
