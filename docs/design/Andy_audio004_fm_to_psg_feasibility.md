# Andy — AUDIO-004 / RG-004: FM-to-PSG Instrument Feasibility & Genesis Channel Allocation

> **AUDIO-009 CORRECTION NOTICE (2026-10-21, confirmed by Cody AUDIO-008):** (1) "No voice is naturally
> PSG-suitable" is an **engineering interpretation, UNVERIFIED acoustically** — it awaits a render/listen
> test, not a proven conclusion. (2) The six-voice discussion relies on a **sustained heuristic**; the
> raw evidence is keyed-channel occupancy (Scene 1 keys **6** channels concurrently, not 5), which does
> not by itself prove conversion capacity. The deep-FM register distribution {1:32,2:10,3:7,4:2,5:3}
> reproduces and stands as capture-derived. No production routing should be chosen before AUDIO-003 +
> audible comparison. See `Andy_AUDIO009_audio_foundation_corrections.md`.

**RG-004** · **Agent:** Andy (Opus) · **Date:** 2026-10-21 · **Issue:** OPEN-039 · **Type:** audio
research / static capture analysis / offline tooling. **No production Z80/68000 ASM, no ROM, no build
number, no driver/DAC/app change.** Baseline Build 0466 accepted (counter 472); untouched. Cody's
independent verification pending — nothing here is "independently verified." Evidence tags: **VERIFIED**
(ROM/capture/hardware doc) · **INFERRED** · **PROPOSED** · **UNRESOLVED**.

## 0. Prerequisite status & scope (STOP-condition handling)

**AUDIO-003 is NOT complete** (no sequence-opcode decoder, no ROM instrument-table inventory, no sample
map; only AUDIO-001 Ghidra + AUDIO-002 asset inventory exist). Per §0/§14, this task is therefore
**scoped to independent PSG hardware research + analysis supported by the existing 9 YM2151 register
captures** (`audio/rastan_music_dump/conversion_attempts/*_ym2151_writes.csv`). **Instrument identity
here is capture-derived** (the actual programmed per-channel FM patch state read from the register
stream), **not** read from the ROM instrument table — tagged accordingly. **Blocked:** a validated
original-YM2151 / YM2612 / PSG 3-way audio comparison (needs an emulator render + the un-decoded
instrument table); not fabricated (§6/§14).

## 1. Genesis SN76489 PSG hardware specification (hardware-standard; cite the SN76489/VDP-PSG doc)

- **3 square-wave tone channels + 1 noise channel.** Fixed **50% duty** square only — **no selectable
  duty** (distinct from the NES APU pulse channels, which have 12.5/25/50/75% duty). This is a hard
  limitation for timbre matching. **No triangle oscillator.**
- **Tone frequency:** 10-bit divider per channel; `f = PSG_clock / (32 × n)`, `n = 1..1023`. Genesis
  PSG clock = master/15 ≈ **3.579545 MHz** (NTSC) → `f ≈ 111860 / n` Hz. Tuning precision is coarse at
  high pitch (n small → large per-step jumps); good at low/mid pitch. (VERIFIED spec; exact Genesis
  clock division should be re-confirmed against the in-repo build/hardware when AUDIO-003 tooling lands.)
- **Attenuation:** 4-bit per channel, **2 dB/step**, 0 = full, 15 = off (16 levels). Coarser than FM TL.
- **Noise:** periodic or white LFSR; 3 fixed shift rates **plus** a mode where the noise clock is driven
  by **tone channel 3** — so using tuned noise **consumes tone channel 3**. (Resource-conflict rule, §8.)
- **Stereo:** the Genesis PSG is routed through the VDP/pin; per-channel L/R is coarse (hardware pan is
  limited vs the YM2612). Register writes are single-byte latch/data; update cadence must respect the
  Z80 bus and the existing sequencer tick.
- **No envelope hardware:** any attack/decay/vibrato must be done by the driver writing attenuation/tone
  per tick (software articulation) — a real per-tick CPU cost to budget.

## 2. Original FM instrument classification (VERIFIED from the 9 captures)

Per-channel patch state extracted by `tools/audio/fm_instrument_psg_analysis.py` (algorithm = YM2151
CONNECT; feedback; operator multipliers; TL activity; key-on/pitch activity). **Algorithm distribution
across all active music channels:**

| Algorithm | Count | Carrier ops | Character |
|---|---|---|---|
| **1** | **32** | 1 | deep 3-op FM (serial), typically **feedback 7 (max)** |
| 2 | 10 | 1 | deep 3-op FM, FB 4-7 |
| 3 | 7 | 1 | deep FM |
| 4 | 2 | 2 | dual-carrier FM |
| 5 | 3 | 3 | triple-carrier |
| 6/7 | **0** | 3/4 | **not used** |

**Headline (VERIFIED):** Rastan's music is **uniformly deep single-carrier FM (algorithm 1-2) with
maximum feedback** — rich, modulation-heavy timbres. **There are NO bright/additive (algo 6-7) patches**
that map naturally onto a 50%-duty PSG square wave. So by patch structure, **no voice is a "natural" PSG
candidate**; every voice moved to PSG loses its FM timbre.

## 3. Channel usage & the "~six music voices" hypothesis (VERIFIED from captures)

Distinguishing activity levels (not merely "received any write"):

| Track | Musical voices | Note |
|---|---|---|
| 01 Credit | 0 sustained (2 sparse) | short jingle |
| 02 Opening | 2 (+6 sparse) | intro texture |
| 03 Aggressive World (Scene 1) | **5** | gameplay |
| 04 Name Regist | 0 sustained (6 sporadic) | short |
| 05 Re-In-Carnation (Scene 2) | **6** | gameplay |
| 06 Devil Boss Carnival | **6** | boss |
| 07 Scene Clear | 3 | jingle |
| 08 Final Destroy (R6 Boss) | **6** | boss |
| 09 The Man Of Saga (Ending) | **7-8** | ending (all 8 active) |

**Hypothesis verdict (INFERRED, capture-backed): SUPPORTED WITH NUANCE.** The main gameplay/boss tracks
use **~6 sustained musical voices** (matching the Inglebard ~6-voice observation); the Ending uses
7-8. Short jingles use fewer. Crucially, **activity on all 8 channels does NOT mean 8 musical voices** —
most tracks have 5-7 sustained musical voices and 1-3 sparse/sporadic channels (likely SFX-shared or
doubling). **No YM2151 noise (reg 0x0F) use was observed in any track** — Rastan's music is pure FM; PSG
noise is free for SFX/percussion if needed.

## 4. FM→PSG suitability matrix

| Patch class (capture-observed) | PSG suitability | Rationale |
|---|---|---|
| algo 1, FB 7 (the dominant class) | **keep FM** | deep modulation + max feedback → PSG square loses all timbre |
| algo 2-3 | **keep FM** | still single-carrier deep FM |
| algo 4-5 (few) | **marginal** | partial carriers; a simple sustained line *might* tolerate PSG |
| monophonic bass / doubling line (any algo), low spectral complexity | **offload candidate** | least-critical to the mix; PSG square is an accepted compromise when FM slots are exhausted |
| percussion / noise | PSG noise OK | none present in the music captures (SFX only) |

**Conclusion (INFERRED):** suitability is **not** the driver — Rastan has no natural PSG voices. The PSG
assignment is **forced by the 5-FM limit** (below) and should target the **least timbrally-critical
voice per track** (bass or a harmony/doubling line), accepting a known timbre compromise.

## 5. Five-FM allocation (the real constraint)

Fixed architecture: YM2612 FM1-5 for music, FM6 = DAC (samples), PSG 3 tone + 1 noise. The ~6-voice
tracks (Scene 1 = 5, Scene 2 / Boss / Final Boss = 6) and the Ending (7-8) exceed 5 FM slots:

- **≤5-voice tracks (Credit, Name Regist, Scene Clear, Scene 1):** fit entirely on FM1-5; **PSG not
  required** (keep full FM timbre). Scene 1 = exactly 5 → FM1-5.
- **6-voice tracks (Scene 2, Boss, Final Boss):** **offload exactly 1 voice to PSG tone 1** — the
  least-critical (candidate: the bass or a doubling line; exact choice is a per-song listening decision,
  UNRESOLVED without the audio comparison). The other 5 stay FM.
- **Ending (7-8 voices):** **offload 2-3 voices to PSG tones 1-3** (and possibly accept dropping/merging
  a doubling voice). Highest-risk track for PSG fidelity.
- **SFX contention:** SFX (FM and/or ADPCM) competes for FM/PSG at runtime. If SFX reserves a PSG tone
  or an FM channel, the music's PSG offload must coexist — a per-track voice-priority/pre-emption policy
  is needed (ties to AUDIO-002's dispatch findings). **Do not** permanently fix one arcade channel
  number to PSG across all songs — the least-critical voice differs per track (VERIFIED: the musical
  channel set and algorithms differ per track).
- **PSG tone-3 / noise conflict:** if a track ever needs tuned PSG noise, it costs tone channel 3 — plan
  the offload to tones 1/2 first.

## 6. Python analysis tooling (authorized, read-only — produced here)

- `tools/audio/fm_instrument_psg_analysis.py` — extracts per-channel patch state (algorithm/feedback/
  operator MUL/TL), note activity (key-on/distinct pitches/span), role (musical/sporadic/idle),
  musical-voice count, and the PSG-candidacy heuristic → `build/audio/fm_psg_analysis/*.json` +
  `_summary.json`. **(Run; results in §2-§4.)**
- `tools/audio/analyze_ym2151_captures.py` (AUDIO-002) — channel activity / peak simultaneous voices.

## 7. Comparison audio — INCOMPLETE (blocked, not fabricated)

A validated **original-YM2151 / YM2612 / PSG** 3-way comparison is **not produced** because it requires
(a) an accurate YM2151 KC/KF→Hz model + an emulator FM render for the reference (the captures are
register streams, not audio), and (b) a hardware-accurate PSG render (a generic square synth is **not**
SN76489-accurate, §5 prompt). Per §6/§14 this is marked **INCOMPLETE** rather than fabricated. The
repeatable methodology (for when AUDIO-003 + an emulator render stage land): render each candidate voice
from its capture note-stream through (1) a validated YM2151 emulator, (2) a YM2612 patch conversion, (3)
an SN76489-accurate PSG model, at **identical pitch/timing/phrase**; measure pitch error (cents), timing
error (ms), attack/decay delta, spectral distance, and loudness; then subjective A/B listening. No new
notes, no rearrangement.

## 8. PSG resource-conflict rules (VERIFIED hardware)

1. Tuned PSG **noise consumes tone channel 3** → offload music voices to tones 1/2 first; reserve tone 3
   if the SFX layer needs tuned noise.
2. PSG has **no envelope/vibrato hardware** → every articulation is a per-tick register write (CPU
   budget on the shared Z80; ties to the AUDIO-002 cycle-budget UNRESOLVED).
3. PSG attenuation is 2 dB/step (16 levels) → match FM TL dynamics only coarsely.
4. **FM6 is DAC-only** (fixed) → never borrow it for music; 5 FM is the hard music ceiling.
5. SFX/music contention: a runtime voice-priority policy must arbitrate PSG tones + FM channels between
   the music offload and SFX.

## 9. JSON routing profile specification (PROPOSED)

```jsonc
{ "track_id": "03_aggressive_world_scene1",
  "arcade_command_byte": null,                 // UNRESOLVED (AUDIO-003 command->track map)
  "musical_voice_count": 5,
  "voices": [                                   // one per ORIGINAL YM2151 music channel in use
    { "arcade_ch": 0, "role": "lead",   "dest": "ym2612_fm1", "psg_articulation": null },
    { "arcade_ch": 5, "role": "bass",   "dest": "psg_tone1",  // example offload
      "psg_articulation": { "attack_ms": 0, "release_ms": 40, "vibrato": false } }
  ],
  "psg_noise": { "used": false, "costs_tone3": true },
  "dac_reserved": "ym2612_ch6",
  "conflicts": [] }
```
One profile per track; per-voice `dest` ∈ {ym2612_fm1..5, psg_tone1..3, psg_noise, mute}; DAC fixed; no
hardcoded universal arcade-channel→PSG mapping. Mirrors the existing registry discipline. The audio
management app (not built here) authors this + auditions original/FM/PSG + flags conflicts.

## 10. Original-data limitations / UNRESOLVED

- No ROM instrument-table inventory / sequence decoder / sample map (AUDIO-003 not done) → instrument
  identity is **capture-derived**, and the per-voice role (lead/bass/harmony) is inferred from note
  activity, not from the sequencer. **The exact least-critical voice per track is UNRESOLVED without the
  audio comparison.**
- No validated 3-way audio render (needs emulator). The YM2151 KC/KF→Hz model and an SN76489-accurate
  PSG model are prerequisites.
- Genesis PSG exact clock division should be reconfirmed against in-repo hardware/build when available.

## 11. Changed files

- New: `tools/audio/fm_instrument_psg_analysis.py`; generated `build/audio/fm_psg_analysis/*`; this
  report; `AGENTS_LOG.md` entry; OPEN-039 update.
- **Production files changed: NONE.** No ROM, no build number, no Z80/68000 ASM, no driver/DAC/app.
  (The `apps/rastan-direct/out/*` modified files in the tree are Cody's build outputs — left untouched.)

## 12. Recommended next milestone

**AUDIO-003 first** (decode the 0x0479 sequence opcodes + the ROM instrument table + the sample map) —
it is the hard prerequisite for a real instrument inventory and the per-voice roles. Then add an
**emulator audio-render stage** (validated YM2151 + YM2612 patch conversion + SN76489 PSG model) to
produce the §7 3-way comparison and resolve the per-track least-critical-voice offload. Only then is the
FM/PSG routing a listening-validated decision rather than a structural inference.
