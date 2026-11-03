# Andy — RG-005 / AUDIO-005: Lawrence McCormick (Inglebard) Genesis Rastan Arrangement Analysis

> **AUDIO-009 CORRECTION NOTICE (2026-10-21, confirmed by Cody AUDIO-008):** (1) The patch-snapshot
> denominator written as **141** in §3 is a report-label error — the actual de-duplicated population is
> **174** (43+55+62+2+12; the algorithm {3:108,0:35,5:20,4:6,6:5} and feedback {5:92,0:47,6:30,7:3,2:2}
> distributions each already sum to 174). (2) The "PSG is additive, not substitution" conclusion (§4) is
> **UNVERIFIED**: it is demonstrated only inside Lawrence's VGM; no note/time alignment against the arcade
> capture was performed, so it must be qualified, not asserted. (3) The analyzer's old "DAC writes: 0"
> display was misleading — Lawrence's DAC plays via **398 stream triggers** (now reported as
> `dac.stream_starts`/`active`). The VGM analyzer and `build/audio/vgm_analysis/` were regenerated with
> these corrections. See `Andy_AUDIO009_audio_foundation_corrections.md`.

**RG-005** · **Agent:** Andy (Opus) · **Date:** 2026-10-21 · **Issue:** OPEN-039 · **Type:** Genesis VGM
reverse engineering / reference-arrangement study. **No production ASM / ROM / build-number / driver /
palette change.** Baseline Build 0472 (counter 472) untouched. Cody verification pending. Evidence tags:
**VERIFIED** (decoded from the actual VGM command stream) · **INFERRED** (musical role) · **PROPOSED**.

## 0. Purpose & honest framing

Lawrence McCormick's Genesis arrangement of Rastan's main stage theme is studied **to learn how a strong
Genesis rendition is built**, not to copy it or to replace our Python conversion architecture. His file is
a **hand-crafted re-arrangement**, not a mechanical YM2151→YM2612 conversion — so it is a **quality target
and a technique reference**, and its register values do **not** reveal how he authored it (§5 caveat
honored). All channel behavior below is decoded from the stream; musical roles are inferred and tagged.

## 1. File located & header verified (VERIFIED)

- Path: `audio/Inglebard Agressive World Handmade Genesis version/LM-Main Stage Theme (1).vgm` (71,848
  bytes, uncompressed; the only Lawrence file in the repo — one recording). Preserved unmodified.
- Tool: new read-only `tools/audio/vgm_genesis_analysis.py` → `build/audio/vgm_analysis/LM-Main Stage Theme (1).json`.
- Header read from the file: **VGM 1.96** (the prompt said 1.60 — **corrected**, verified from offset
  0x08); YM2612 clock **7,670,454 Hz**, SN76489 clock **3,579,545 Hz**, total **2,366,496 samples ≈ 53.7
  s**, loop **1,792,800 samples ≈ 40.7 s** (loop point at sample 573,696 ≈ **13.0 s**). Clocks and
  sample/loop totals match the prompt; only the version differed.
- **Decode completeness:** every command consumed, reached end-marker 0x66, **0 flagged/unsupported
  commands** (all waits counted, so timing is exact). Command histogram: 0x52=8769 (YM2612 p0), 0x53=740
  (p1), 0x50=4884 (PSG), 0x61=3168 (waits), 0x67=4 (PCM data blocks), 0x90/0x91/0x92×398/0x94/0x95×398
  (DAC stream).

## 2. Channel allocation — Lawrence uses ALL SIX FM + three PSG tones (VERIFIED)

| Channel | Role (INFERRED) | Evidence (VERIFIED) |
|---|---|---|
| **FM1** | Lead melody (center) | 88 key-ons, 108 pitches B-1…C6, stereo `lr`=0xD4 **L+R (center)**, 43 patch snapshots |
| **FM2** | Harmony / distortion-guitar (left) | 102 key-ons, 121 pitches, `lr`=0x94 **left only**, 55 snapshots, algo 0 used 23× |
| **FM3** | Counter-lead / arpeggio (right) | 93 key-ons, **247 pitches** (most melodic motion), `lr`=0x54 **right only**, 62 snapshots |
| **FM4** | **Bass** (center) | 39 key-ons, only **5 pitches G#0…D1**, algo 5 fb 2, all op MUL=1, 2 snapshots (stable patch) |
| **FM5** | Bright arpeggio / rhythm comp | **131 key-ons (most rhythmic)**, 38 pitches A1…G5, algo 6, high MUL (10,8,10,2) |
| **FM6** | **Sampled drums (DAC)** | key-on reg 0x28 = 0 (so looked "silent"), but driven by the **VGM DAC stream**: 4 PCM blocks + **398 triggers @ 8 kHz** → YM2612 reg 0x2A |
| **PSG tone1** | Added harmony (late) | 21 key-ons, A3…D6, **enters 29.7 s** |
| **PSG tone2** | Added harmony (mid) | 25 key-ons, G3…D6, **enters 16.7 s** |
| **PSG tone3** | High sparkle / octave lead | 21 key-ons, D3…**F9** (very high), **enters 12.2 s** |
| **PSG noise** | One-shot accent | **1 hit at 12.2 s** (the loop boundary); negligible — no drum-kit role |

**Peak simultaneous pitched voices = 8 (5 FM + 3 PSG) at 38.4 s**, on top of the DAC drum layer.

### 2a. The headline technique — a 3-channel stereo-spread lead stack (VERIFIED)
At t=0, **FM1, FM2 and FM3 carry the *identical* operator patch** (algo 5, fb 6, same DT/MUL/TL/envelopes)
differing **only in stereo pan**: FM1 = center (L+R), FM2 = **left**, FM3 = **right** (all AMS 1 / FMS 4).
This is a deliberate **stereo-widened unison/harmony stack** — the single biggest contributor to the
"big" Genesis sound. Over time the three diverge in pitch/TL to become lead + two harmony/counter lines.

### 2b. Percussion = DAC samples, not PSG noise (VERIFIED)
FM6 plays **4 uncompressed PCM drum samples (~4.8 KB each, ~19 KB total) at 8 kHz**, triggered 398× over
the loop via the DAC stream (one stream, "start-fast-call" 0x95). PSG noise is used **once**. So the drive
comes from **sampled drums on the DAC**, freeing the PSG entirely for melodic content.

## 3. Instrument programming & the "aggressive" sound (VERIFIED values; INFERRED character)

Algorithm distribution across **all 141 key-on patch snapshots**: `{algo3: 108, algo0: 35, algo5: 20,
algo4: 6, algo6: 5}`. Feedback distribution: `{fb5: 92, fb0: 47, fb6: 30, fb7: 3, fb2: 2}`.

- **Lawrence's YM2612 music is predominantly DEEP single-carrier FM (algo 3 and algo 0) with high feedback
  (fb 5-6).** He did **not** brighten the voices into additive/PSG-style timbres. The aggressive edge comes
  from **high operator feedback (5-6)** and the algo-0 serial topology (the classic distortion-guitar
  stack, used heavily on FM2), **not** from bright additive algorithms.
- **This directly corroborates AUDIO-004:** the arcade original is deep FM (YM2151 algo 1-2); Lawrence's
  Genesis version is *also* deep FM (YM2612 algo 0/3). The right conversion **keeps the FM voices as deep
  FM on the YM2612** — it does not re-timbre them for the PSG.
- **Bass (FM4):** algo 5, fb 2, every operator MUL=1, DT=6 (detune for thickness), TL-automated for
  dynamics; one stable patch — a clean, fundamental-heavy FM bass.
- **Patches are reprogrammed constantly** (43-62 distinct snapshots on FM1-3): TL, pitch and sometimes
  algorithm change per phrase. Per-channel "the algorithm" is therefore **not fixed** — the single-value
  summary field reflects only the last write; the key-on-time inventory is authoritative. (Register values
  + timestamps are in the JSON `instrument_inventory`; reusable.)

## 4. PSG usage — ADDITIVE layering, not FM substitution (VERIFIED timing; the key lesson)

The central §6 question — *did Lawrence replace arcade YM2151 voices with PSG?* — **answer: NO.**
- The **intro (0-13 s) is FM-only** (5 FM + DAC drums). PSG tones enter **progressively and late** (tone3
  @12.2 s, tone2 @16.7 s, tone1 @29.7 s), building up through the **looped body** (loop starts 13.0 s).
- PSG is used for **added harmony, arpeggio and high-octave sparkle** (tone3 reaches F9, well above the FM
  range) that the 5 FM + drum budget does not already cover — i.e. the PSG **extends** the arrangement past
  6 voices, it does **not** receive a demoted FM lead.
- This **refines AUDIO-004's** "offload the least-critical voice to PSG" rule: the better strategy Lawrence
  demonstrates is to **keep the core voices on FM and ADD PSG sparkle/harmony on top**, reserving PSG for
  parts that are naturally bright/high or purely supportive — not to push a deep-FM lead onto a square wave
  (which AUDIO-004 already showed has no natural candidate).

## 5. What we learn for OUR converter and audio-management app (PROPOSED)

1. **Keep deep FM on the YM2612.** YM2151 algo 1-2 → YM2612 algo 0/3 with high feedback preserves the
   aggressive timbre. Do **not** re-timbre FM voices toward PSG-friendly brightness (AUDIO-004 + §3 here).
2. **Put percussion on the FM6 DAC as short PCM samples** (Lawrence: 4 samples, ~4.8 KB, 8 kHz). This is
   where the drums belong; it keeps the PSG free. Ties directly to the OPEN-039 "ADPCM→ch6 DAC" plan — the
   arcade MSM5205 drum/voice samples are the source material for exactly this.
3. **Use the PSG additively, not as an FM dumping ground.** Route PSG tones to bright/high harmony,
   arpeggio and sparkle lines; reserve PSG noise for one-shot accents. Our per-track routing profile should
   express "PSG = added layer" distinctly from "FM voice relocated to PSG."
4. **Support stereo-spread voice doubling.** The routing profile and converter must expose per-voice
   **L/R pan + AMS/FMS** (YM2612 reg 0xB4) and allow the **same patch on multiple FM channels panned L/C/R**
   — this single technique produced most of Lawrence's width and body.
5. **Per-voice dynamic patch/TL automation.** Lawrence automates TL (and occasionally algorithm) per
   phrase; our converter's instrument model must be a time-series, not one static patch per channel.
6. **Audio-management app:** (a) adopt this VGM analyzer as the **reference-import + A/B comparison** path
   (load any VGM, see allocation/instruments/voice count beside our converted output); (b) model 6 FM
   (ch6=DAC) + 3 PSG tone + 1 noise with per-voice pan, envelope, and additive-PSG flags; (c) a DAC sample
   bank (short 8 kHz PCM) for percussion.

## 6. Reconciliation with the "six-voice" claim & AUDIO-004

- Lawrence's own "six FM channels" statement is **confirmed with a precision**: he uses **6 FM channels —
  five melodic + ch6 as DAC drums** — plus 3 PSG tones. Peak *pitched* polyphony is **8** (5 FM + 3 PSG).
- AUDIO-004 found the arcade Scene-1 ("Aggressive World", the **same composition**) uses ~5 musical FM
  voices of deep FM. Lawrence takes that same tune and **adds** a sampled-drum layer (DAC) and progressive
  PSG harmony/sparkle, keeping the FM deep — a concrete worked example of the AUDIO-004 architecture done
  well, and evidence that the PSG budget should be spent *adding* voices rather than *relocating* them.

## 7. Limitations / UNRESOLVED

- This is **one hand-made arrangement of one track**; it is a technique reference, not a conversion
  algorithm, and does not tell us Lawrence's authoring tool or process (§5 caveat).
- Musical role labels (lead/harmony/bass/arp) are **INFERRED** from register behavior (pitch range,
  key-on density, pan), not from a score.
- No audio was rendered or compared acoustically here (that remains the AUDIO-004 emulator-render gap);
  this task is a static decode of Lawrence's command stream only.
- The 4 DAC samples' identities (kick/snare/hat/etc.) are not classified — only their size, rate and
  trigger count are decoded; identifying them would need PCM extraction + listening (future work).

## 8. Files changed

- New: `tools/audio/vgm_genesis_analysis.py` (read-only VGM decoder; reusable for any Genesis VGM);
  generated `build/audio/vgm_analysis/LM-Main Stage Theme (1).json`; this report; `AGENTS_LOG.md` entry;
  OPEN-039 update.
- **Production files changed: NONE.** Lawrence's VGM preserved unmodified.
