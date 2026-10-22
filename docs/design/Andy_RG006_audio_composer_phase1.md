# Andy — RG-006 / AUDIO-006: Rastan Audio Composer (Phase 1)

> **AUDIO-009 CORRECTION NOTICE (2026-10-21, confirmed by Cody AUDIO-008 and now FIXED):** the Phase-1
> Composer had real defects, all corrected under AUDIO-009 (schema bumped `v1`→`v2`): **(1)** GET
> `/api/profile` directory traversal — now a strict allowlisted, containment-checked profile ID; **(2)**
> invalid routing / client-fabricated approval could persist — the server now recomputes conflicts and
> **rejects any error-level conflict**; **(3)** destructive same-ID overwrite — now **atomic immutable
> revisions** (`<id>.rN.json`) with a manifest kept consistent; **(4)** client-mutable `arcade_evidence`
> — now **server-derived** from the analysis artifacts; **(5)** false Genesis PSG per-channel stereo — now
> **mono/center**; **(6)** unconditional tone-3/noise coupling — now **only** when the noise selector is
> `tone3_clocked`. The regression suite was expanded (37 checks incl. HTTP-level). PSG noise taps/period
> and divider-zero are labeled UNRESOLVED (no false fidelity). See
> `Andy_AUDIO009_audio_foundation_corrections.md`.

**RG-006** · **Agent:** Andy (Opus) · **Date:** 2026-10-21 · **Issue:** OPEN-039 · **Type:** development
tool (browser-based audio routing editor + Python backend). **No production Z80/68000 ASM, ROM,
build-number, driver, or Palette Composer change; nothing rebuilt.** Baseline Build 0472 (counter 472)
untouched. Arcade captures and Lawrence's VGM are READ-ONLY. Cody verification pending.

## 1. Baseline

Accepted baseline **Build 0472** (`build/rastan-direct/build_counter.txt` = 472; last consumed 0472
canonical=PASS entry=PASS epoch=PASS). No build produced; counter unchanged.

## 2. Architecture (modeled on `tools/graphics_editor/`)

Same shape as the Palette Composer: a stdlib `ThreadingHTTPServer` on `127.0.0.1` serving a static
HTML/JS/CSS UI plus small JSON APIs; a **read-only evidence oracle** (here: the arcade captures + prior
AUDIO analysis) and **editable, versioned per-track JSON decision profiles** (baseline immutable, branch
to edit), with **generated profile data kept separate from source** (`analysis/audio/decision_profiles/`,
mirroring the palette editor's `editor_policy/`). The music editor is **not coupled** to palette editing.

```
tools/audio_composer/
  server.py    HTTP server: inventory / psg_model / lawrence / audition / profiles APIs; conflict
               validator; profile load/save with server-authoritative guards (FM6, proposal≠approval).
  index.html   3-column editor: track browser | arcade channels + Genesis routing | conflicts/instr/PSG/audition.
  app.js       vanilla JS: track select, per-channel routing, propose→approve, live validate, save/branch.
  style.css    utilitarian dark editor styling, responsive to phone width.
  run.sh       launcher.
  verify_audio_composer.py   26 automated checks (all pass).
analysis/audio/decision_profiles/   generated profiles (baseline_current.json + profile_manifest.json seed).
```

Data sources (read-only): `build/audio/fm_psg_analysis/*` + `build/audio/ym2151_track_reports/*`
(capture-derived per-channel data), `build/audio/music_command_inventory.json` (44 decoded command
descriptors), `build/audio/vgm_analysis/*` (RG-005 Lawrence reference), and the 9 YM2151 capture CSVs.

## 3. Launch

```
tools/audio_composer/run.sh            # defaults to http://localhost:8781
tools/audio_composer/run.sh 8785       # or any port
# equivalently: python3 tools/audio_composer/server.py 8781
```
Dependencies: **Python 3 standard library only** (no pip installs, no external/cloud services). Any modern
browser.

## 4. Implemented working features (Phase 1)

- **Track browser** — all 9 original tracks with musical name, capture availability, capture-derived
  musical-voice count and peak simultaneous voices.
- **Original YM2151 channel panel** — 8 channels per track with role (musical / sporadic / sparse / idle),
  key-on count, distinct pitches, algorithm/feedback, and the AUDIO-004 PSG-fit heuristic. Each is clearly
  **capture-derived**; **command-ID shown as UNRESOLVED and never inferred from the filename**.
- **Genesis routing editor** — per original channel, a destination picker: FM1–5, PSG tone 1–3, PSG noise,
  Unassigned. **FM6 appears as a reserved DAC slot and is NOT selectable for music.** A destination-slot
  grid shows which arcade channels are approved to each Genesis voice, highlighting over-subscription.
- **Propose → approve** — a picked destination is a **proposal**; **Approve** promotes it to an approved
  decision. The two are stored and displayed separately; the server refuses to treat a proposal as an
  approval, and `approval_status:"approved"` is downgraded to `draft` if nothing is actually approved.
- **Live conflict validator** (see §6).
- **Genesis PSG model panel** (see §8) and an **instrument data-model** panel (fields present; editing
  deferred, §10).
- **Lawrence McCormick reference** — optional, read-only: his per-FM/PSG channel usage, algo/fb, DAC
  activity and peak voices, with attribution. **Not loaded as converter defaults.**
- **Profiles** — load / branch / save / reload; versioned JSON; baseline immutable.

## 5. Features deferred due to missing AUDIO-003 data (honestly surfaced)

- **Per-note / time-dependent instrument evidence** — AUDIO-003 is not decoded (no sequence event stream,
  no ROM instrument-table identity, no sample map). The UI shows a standing banner stating this; per-channel
  data is capture-derived summary only. `time_dependent_routing` and `instrument_overrides` exist in the
  schema (so later work needs no format change) but their editing UI is deferred.
- **Instrument-level (sub-channel) routing** — data model supports it; Phase-1 UI exposes channel-level
  routing only, per the prompt.
- **Audition / playback / A-B** — deferred; see §9.

## 6. Routing & conflict validation behavior

The validator (`validate_routing`) runs live on every change and on save (server-authoritative), and
**never discards a voice to make an assignment fit**. Rules:

| Conflict | Severity / certainty | Trigger |
|---|---|---|
| `reserved_fm6` | error / structural | any music routed to FM6/DAC |
| `invalid_dest` | error / structural | destination not in the allowed set |
| `fm_budget` | error / structural | more than 5 arcade channels routed to FM (only FM1–5 exist) |
| `monophonic_collision` | **warning / potential** (or error/proven) | ≥2 channels share one FM/PSG voice |
| `tone3_noise_coupling` | warning / structural | psg_tone3 and psg_noise both used (freq-select-3 couples them) |

Because AUDIO-003 timing is absent, a shared-channel collision is reported as a **POTENTIAL** conflict, not
proven — the code only escalates to "proven" given positive overlap evidence, which the current
capture-summary data cannot supply, so it stays "potential". Structural conflicts (FM6, FM budget) are
reported as certain. FM6-music is rejected both in the validator and again as a hard 403 on save.

## 7. JSON schema & profile locations

Schema `audio_composer/v1`, one profile per file in `analysis/audio/decision_profiles/<id>.json`, indexed
by `profile_manifest.json`. **Three layers are kept strictly separate:** `arcade_evidence` (read-only
snapshot), `proposals` (unapproved, with rationale/evidence), `approved_routing` (user-approved only).
Also: `instrument_overrides` (YM2612 + PSG parameter model), `time_dependent_routing` (list of time-windowed
routings), `conflicts` (last validation), `notes`, `approval_status` (draft/proposed/approved), `source`
(ROM + capture + analysis-version provenance), `reserved_dac`. The immutable `baseline_current` cannot be
overwritten; saving a profile writes only under `decision_profiles/` and **never** touches a capture, the
VGM, the ROM, or the build.

## 8. Genesis PSG model (for validation + the future audition engine)

`/api/psg_model` returns: SN76489-class Sega-VDP PSG @ 3,579,545 Hz; **3 × 50%-duty square (no duty
select — explicitly contrasted with the NES APU)**; 10-bit tone divider (n 1–1023) → f = clock/(32·n)
(~109 Hz–~112 kHz); 4-bit attenuation @ 2 dB/step (16 levels); **16-bit LFSR noise** (noted as differing
from the TI 15-bit), white + periodic; noise freq-select 0/1/2 fixed and **3 = tone-channel-3-driven
(couples tone 3 and noise pitch)**; coarse L/R stereo; no hardware envelope. Values are tagged with
provenance (Sega Retro + TI manual, modeled, not yet hardware-reverified here) so the UI does not
over-claim. The model does **not** assert independent tone-3/noise control in the coupled mode.

## 9. Audition functionality actually available

**None — and that is reported honestly.** `/api/audition` returns `available:false` with the reason, and
the UI shows a dashed "Playback UNAVAILABLE (Phase 1)" box. No oscillator audio is produced or labeled as a
faithful YM2151/YM2612/PSG reference; there are **no decorative dead play buttons**; no acoustic comparison
is fabricated. The future contract (endpoints `/api/render/{original,ym2612,psg,full,lawrence_vgm}`,
requiring AUDIO-003 + a validated emulator render stage) is declared so later work slots in without a
redesign.

## 10. Instrument-editing data model (persisted now, edited later)

Profiles carry per-channel `instrument_overrides` for **YM2612** (algorithm, feedback, operator MUL, detune,
TL, AR/decay/sustain/RR, AMS, FMS, stereo pan, time-series) and **PSG** (tone divider, attenuation, volume
envelope, note attack/decay, pitch articulation, vibrato, arpeggio, periodic/white noise). Phase 1 does not
implement the editing controls, but persistence already holds the fields, so later implementation will not
require replacing the profile format.

## 11. Validation performed

`tools/audio_composer/verify_audio_composer.py` — **26/26 pass**: inventory (9 tracks, AUDIO-003 flagged,
no filename→command-ID inference, 8 channels/track, capture detection); PSG model (3 tones, 50%-duty-vs-NES,
16-bit LFSR, tone-3 coupling, 10-bit divider); validator (FM6 error, >5-FM budget error, monophonic
collision flagged POTENTIAL, tone-3/noise coupling, clean routing → no conflict); profile round-trip
(approved routing, proposals/approvals separated, notes, schema, three layers, future-proof fields);
sources read-only present; **Palette Composer server.py still compiles (untouched)**. Plus a live HTTP smoke
test: all GET/POST endpoints serve; a legit save round-trips and updates the manifest; an FM6-music save is
rejected 403 and writes no file; the rejected save left the profile directory clean. **No audio fidelity
testing is claimed** (no rendered audio exists).

## 12. Files created / modified

**Created:** `tools/audio_composer/{server.py, index.html, app.js, style.css, run.sh,
verify_audio_composer.py}`; this report; seed `analysis/audio/decision_profiles/{baseline_current.json,
profile_manifest.json}` (generated tool state). **Reused (new):** `tools/audio/vgm_genesis_analysis.py`
output from RG-005. **Modified (docs):** `AGENTS_LOG.md`, `OPEN_ISSUES.md` (OPEN-039).
**No production files changed.** The Palette Composer, all captures, the arcade ROMs, Lawrence's VGM, the
build counter, and all assembly are untouched.

## 13. No production changes / no ROM build — confirmation

No 68000/Z80 assembly edited, no sound driver written, no YM2151→YM2612 or PSG conversion implemented, no
DAC mixing, no sequencer replacement, no PCM song build, no ROM generated, no build number consumed, no
accepted baseline modified, Palette Composer not modified.

## 14. Unresolved & recommended next milestone

- **AUDIO-003** (decode the sequence opcodes + ROM instrument table + sample map) is the gating
  prerequisite for per-note timing, true instrument identity, proven (vs potential) overlap conflicts, and
  the command-ID↔track mapping. **Recommended next.**
- Then an **emulator render stage** (validated YM2151 + YM2612 patch conversion + SN76489 PSG model) to
  turn the declared audition contract into real playback and A/B comparison.
- Later Audio Composer phases: instrument-editing controls, time-dependent routing UI, and Lawrence VGM
  import as a live comparison track.
