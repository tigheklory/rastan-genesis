# Andy — AUDIO-012: webVGM Playback + Authored-Genesis Rendering in the Rastan Audio Composer

**AUDIO-012** · **Agent:** Andy (Opus) · **Date:** 2026-10-22 · **Issue:** OPEN-039 (remains OPEN) ·
**Type:** Audio Composer implementation (browser playback + authored-routing rendering).
**Baseline Build 0473, build counter 477 — unchanged.** No production ROM/ASM/build/counter/tag, no
original capture/ROM/Lawrence-VGM modification, no Palette Composer change, no AUDIO-011 profile-integrity
change, no sound-driver change.

This document is the complete, consolidated record of the AUDIO-012 work (which went through several
stages in one session: a licensing review, then real playback via a local engine, then an authored-Genesis
renderer, then PSG/volume balancing).

---

## 1. What works now (summary)

The Composer (`tools/audio_composer/`, launched by `run.sh`) now produces real, in-browser chip-emulated
audio for three things:

1. **Original arcade music** — all 9 Rastan YM2151 captures, converted to standard VGM and played through
   the real webVGM/VGMPlay engine.
2. **Lawrence McCormick's reference** — his unmodified Genesis VGM, played through the same engine.
3. **Your authored Genesis arrangement** — a **▶ Play Genesis** button renders the routing *you* author
   (which original voice goes to which YM2612 FM / PSG channel, and at what volume) into a real
   **YM2612 + SN76489** register stream and plays it, so you can A/B it against the original.

All audio is produced by a real VGM chip emulator — **no oscillator approximations and no pre-recorded
WAV** anywhere. Audible acceptance is the user's; this environment cannot render audio headlessly.

**Per-song mappings (2026-10-22):** each song keeps its own independent routing/volume/noise mapping —
stored per track in `PROF.track_routings[track_id]` and swapped as you select tracks (persisted via the
server's existing unknown-field round-trip; no profile-schema change; legacy flat routings auto-migrate).
Selecting a track also points the playback source at the same song for A/B.

**UI trims (2026-10-22):** the Lawrence McCormick reference VGM was removed from the tool (dropped from the
source list, the `/api/lawrence` / `src=lawrence` / `engine_media/lawrence.vgm` endpoints, and the UI; the
raw VGM file and the RG-005 analysis on disk are left untouched). The right-hand column
(Conflicts/Instrument/PSG-model/Audition) is commented out per request (re-enable by uncommenting the
`<aside id="right">` block); the layout is now two columns.

---

## 2. How to launch and use

```
tools/audio_composer/run.sh            # http://localhost:8781 (Python standard library only)
```

**Hear the original / Lawrence:** Playback panel → pick a source in the dropdown → the embedded webVGM
player loads it → press ▶ Play. (Or "Open / Download VGM" to open it in a standalone webVGM.)

**Hear your authored Genesis version:**
1. Left panel: select a track (e.g. Scene 1 — Aggressive World).
2. Center: for each original YM2151 channel, pick a Genesis destination (FM1–5 / PSG tone 1–3 / PSG
   noise / Unassigned) and click **Approve**. Set each channel's **vol** slider to taste.
3. Playback panel: click **▶ Play Genesis (authored)**. It renders your routing to a YM2612+PSG VGM and
   plays it. Switch the source dropdown back to the original capture to A/B.

**The local engine** lives in the git-ignored `tools/audio_composer/engine/` (see §7). If it is ever
missing, run `tools/audio_composer/fetch_engine.sh` to re-fetch it locally.

---

## 3. Component inventory

| File | New/mod | Role |
|---|---|---|
| `tools/audio/ym2151_capture_to_vgm.py` | new | Deterministic first-party converter: a YM2151 capture CSV → standard VGM 1.51 (YM2151 `0x54` writes, exact sample-timed waits, 4 MHz clock). |
| `tools/audio/verify_capture_vgm.py` | new | Independent round-trip validator for the above (86/86). |
| `tools/audio/render_genesis_vgm.py` | new | **Authored-routing renderer:** YM2151 capture + your routing + per-channel volume → real **YM2612 (FM1–5) + SN76489 (PSG)** VGM. |
| `tools/audio_composer/player_adapter.js` | new | Engine-agnostic player contract + honest `NullEngine`; probes for a local engine. |
| `tools/audio_composer/engine/webvgm_player.html` | new (local, git-ignored) | Thin iframe host mirroring wothke's own webVGM init; plays a `.vgm` URL. |
| `tools/audio_composer/fetch_engine.sh` | new (committed) | Reproducibly fetches wothke's prebuilt webVGM into the git-ignored `engine/`. |
| `tools/audio_composer/verify_playback.py` | new | Playback + renderer regression suite (39 pass / 0 fail / 5 unavailable). |
| `tools/audio_composer/.gitignore` | new | Ignores `engine/` so the third-party engine is never committed. |
| `tools/audio_composer/server.py` | mod (additive, isolated) | Read-only playback endpoints + the authored-render endpoint; **no profile/approval/manifest/revision code touched**. |
| `tools/audio_composer/{index.html, app.js, style.css}` | mod | Playback panel, Play Genesis button, per-channel volume sliders, embedded engine iframe. |
| `build/audio/capture_vgm/*.vgm` (+`_manifest.json`) | generated | The 9 converted arcade VGMs. |

Server endpoints added (all read-only, isolated from profiles):
- `GET /api/playback_sources`, `GET /api/engine_status`
- `GET /api/vgm?src=lawrence|capture&id=…` and clean `GET /engine_media/lawrence.vgm` /
  `/engine_media/capture/<id>.vgm` (strict capture-id allowlist, no traversal)
- `GET /engine/<file>` — serves the local user-supplied engine if present
- `POST /api/render_genesis {track, approved_routing, noise_mode, levels}` → renders, caches in memory,
  returns `/engine_media/authored/<token>.vgm`; FM6 is rejected; routing comes from the request, never
  from a stored profile; nothing is persisted.

---

## 4. Original-capture → VGM conversion

The capture CSV's `sample` column is already in the 44 100 Hz VGM timebase (verified: sample 3 at
6.80 × 10⁻⁵ s = 3/44100). So the conversion is exact and lossless to what was captured: per-event sample
deltas become VGM waits, same-sample writes keep their order, each YM2151 write becomes a `0x54 reg val`,
clock = 4 MHz. All 9 tracks converted (Aggressive World = 16 189 writes, 52.4 s). The independent
validator re-parses each VGM and checks count, order, timing, header, clock, and end-marker against the
source CSV: **86/86**.

---

## 5. Authored-routing Genesis renderer (`render_genesis_vgm.py`)

This is what makes "Play Genesis" produce *your* arrangement. It walks the original YM2151 capture and,
per your `approved_routing`, re-emits each voice on its chosen Genesis channel:

**FM destinations (YM2612 FM1–5).** YM2151 (OPM) and YM2612 (OPN2) share bit-compatible **operator
parameter** registers, so these translate 1:1: DT/MUL, TL, KS/AR, AM/D1R, D2R, SL/RR, feedback, and
algorithm all pass through (with register/channel address remapping). The non-trivial parts:
- **Pitch** is converted OPM KC/KF → real Hz → OPN2 fnum/block using the YM2612 7.67 MHz clock.
- Algorithm/feedback move from OPM `0x20` to OPN2 `0xB0`; L/R to `0xB4` (defaulted on so the channel is
  audible).
- The key-on register is remapped (`0x08` → `0x28`) to the target channel.

**PSG destinations (SN76489 tone 1–3 / noise).** The voice becomes a 50 %-duty square: pitch → 10-bit
divider, key-on/off → attenuation, noise mode per the profile's noise selector.

**FM6 is never targeted** (DAC-reserved); unassigned/muted channels are dropped (silent). Your routing
determines the output — moving a voice FM↔PSG produces an audibly different render (test R6).

### Volume (the FM↔PSG balance)

- **FM volume** = the original carrier **TL**, passed straight through, so FM follows the original mix.
- **PSG volume** = derived from the *same* source carrier TL (FM 0.75 dB/step → PSG 2 dB/step) plus a
  tunable `PSG_HEADROOM` (default 3 steps ≈ 6 dB) so squares sit under the FM. This replaced an earlier
  bug where PSG was pinned to attenuation 0 (full blast). At the default per-channel volume this is the
  only thing setting PSG level — the "carried-over" behavior the user liked.
- **Per-channel volume slider (0–200, 100 = original)** in each routing row, stored in
  `instrument_overrides[ch].level` and sent to the renderer as `levels`. It is **additive on top of** the
  TL-derived level: 100 adds nothing (baseline preserved exactly); **<100 attenuates** (quieter), **>100
  boosts** (louder, by lowering carrier TL / attenuation toward the chip max — clamped at TL 0 / atten 0,
  so a voice already at max can't exceed it); **0 mutes**. The webVGM player's own `vol` slider is the
  master output level.

---

## 6. The embedded webVGM engine

Playback uses wothke's real **webVGM / VGMPlay 0.40.9** (`backend_vgm.js` self-contained asm.js +
`scriptprocessor_player.min.js` + `VGMPlay.ini`), the player the user confirmed renders Rastan correctly.
It is loaded in an isolated iframe host (`engine/webvgm_player.html`) that mirrors wothke's own `index.html`
initialization (`ScriptNodePlayer.createInstance(new VgmBackendAdapter(), …)` → `loadMusicFromURL` → play).
Musical timing comes from the engine + the Web Audio render clock — never `setInterval`/rAF.

---

## 7. Licensing — why the engine is LOCAL and git-ignored

The repo **redistributes none** of the engine. webVGM/VGMPlay's required chip cores — YM2151
(`ym2151.c`), YM2612/FM (`fm.c`/`fm2612.c`/`ym2612.c`), SN76489 (`sn76496.c`/`sn764intf.c`) — are
**MAME-derived** under the bundled MAME license, which says *"Redistributions may not be sold, nor may they
be used in a commercial product or activity"* (non-commercial, GPL-incompatible); the glue is GPL/"LGPL
2.1" (inconsistent wording). Those terms govern **distribution**, so they would block *committing* the
engine to the repo. They do **not** restrict Tighe's **private, local, non-redistributed** use of the tool.

Resolution: the engine is fetched into **`tools/audio_composer/engine/`, which is git-ignored** — it exists
only in this local working tree, is never committed or published, and `fetch_engine.sh` (committed)
re-creates it on demand. So real playback works locally while the repository itself ships no third-party
engine code. (An earlier pass in this task wrongly treated "can't redistribute" as "can't integrate" and
stopped; that was corrected once Tighe clarified the tool is personal and not redistributed.)

A fully redistributable alternative, if ever wanted: build **ymfm** (BSD, YM2151+YM2612) + a MIT SN76489
to WASM with emscripten (not present in this environment) and drive it from a first-party VGM sequencer.

---

## 8. Provisional limitations (labeled — this is a first stage, not the final converter)

- OPM operator **ordering** (M1,M2,C1,C2) vs OPN2 (S1,S3,S2,S4) is mapped by index; complex algorithms may
  differ in timbre.
- OPM **DT2** has no OPN2 equivalent → dropped.
- PSG per-note dynamics are a coarse carrier-TL estimate (not a full envelope).
- **Arcade pitch matching (now exact):** pitch uses the YM2151's own `phaseinc_rom[768]` table, copied
  verbatim from the same OPM core webVGM uses, evaluated at Rastan's real **4.0 MHz** clock
  (`Hz = phaseinc_rom[i]·clock·2^(octave−28)`). So the render lands on the *identical* frequency the
  emulator produces for the arcade capture — verified at 0.4 cents (FM) / 3.5 cents (PSG) error, limited
  only by each chip's frequency quantization. This replaced an earlier A440+clock-ratio approximation that
  was ~1 semitone off (it anchored A to the wrong semitone). `OCTAVE_OFFSET` remains a manual whole-octave
  override (0 = exact). `PSG_HEADROOM` tunes the global PSG level.
- The renderer works from the **captured register stream**, not decoded ROM sequences/instruments. The
  high-fidelity path still depends on **AUDIO-003** (sequence/instrument/sample decode). This preview is
  explicitly **not** the completed converter.
- Headless environments can't render audio, so engine-driven behaviors (pause/resume, stop/restart, loop)
  and audible fidelity are verified by **listening**, not by the automated suite.

---

## 9. Tests

`PYTHONDONTWRITEBYTECODE=1 python3 tools/audio_composer/verify_playback.py` → **39 passed, 0 failed,
5 unavailable** (HTTP-level, isolated temp profile dir). Coverage:
- Engine files + `.vgm` media routes serve; traversal/unknown-id rejection; duration == capture last
  sample; YM2151 4 MHz / YM2612 clocks; FM/PSG/DAC activity; same-timestamp ordering; repeated-load
  determinism.
- Authored renderer R1–R12: real YM2612 (`0x52/0x53`) + PSG (`0x50`) emission; routing determines output;
  FM↔PSG move changes the render; PSG-noise routing; FM6 rejected; **per-channel volume trims PSG (50 % =
  quieter)**; **volume 0 mutes**; **no profile or original-asset modification**.
- The 5 "unavailable" are browser-audio-only (pause/resume, stop/restart, loop, per-chip mute — wothke's
  engine exposes no per-chip mute API — and headless PCM render); marked honestly, never faked.
- Plus: the AUDIO-009 Composer suite still passes **37/37**; `verify_capture_vgm.py` **86/86**; Palette
  Composer untouched.

---

## 10. Next steps

1. **AUDIO-003** (decode ROM sequences, the instrument table, and the sample map) replaces the
   capture-driven OPM→OPN2 translation with validated per-instrument patches, proper operator ordering,
   and per-note PSG dynamics — the path to high fidelity.
2. Interactive instrument editing (adjust algorithm/TL/envelope per voice and re-audition) builds directly
   on this renderer and the existing `instrument_overrides` data model.
3. Optional: a fully redistributable engine (ymfm + MIT SN76489 to WASM) if the engine should ever ship
   with the repo.

---

## 11. Constraints honored

No 68000/Z80 production ASM, no sound driver, no ROM, no ROM build, no build-counter change (477 → 477),
no accepted-baseline/tag change, no modification of the original captures / ROMs / Lawrence's VGM, no
Palette Composer change, and no change to the AUDIO-011 profile-integrity code (approval/manifest/
revision). The third-party engine is local-only and git-ignored; the repo redistributes nothing. User
listening is the acceptance criterion; no audio fidelity is claimed.
