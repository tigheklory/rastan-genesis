# Andy — AUDIO-009: Audio Foundation & Audio Composer Corrections

**AUDIO-009** · **Agent:** Andy (Opus) · **Date:** 2026-10-21 · **Issue:** OPEN-039 (remains OPEN) ·
**Type:** corrective implementation + regression testing · **Source of truth:** Cody's AUDIO-008 audit
(`docs/design/Cody_RG008_audio_foundation_independent_verification.md`). **No production ROM/ASM,
build-number, baseline, original capture, Lawrence VGM, or Palette Composer change.**

## 1. Baseline

Accepted baseline **Build 0472**, build counter **472** (unchanged; `build/rastan-direct/build_counter.txt`
= 472; `dist/.../build_0472.bin` present). No build target run. AUDIO-003 remains **NOT complete** (not
claimed otherwise anywhere in this task).

## 2. Correction matrix (linked to Cody's AUDIO-008 findings)

| AUDIO-008 finding (claim#) | Severity | Correction | Where |
|---|---|---|---|
| GET profile directory traversal (48) | HIGH | Strict allowlist profile-ID regex + realpath containment (`safe_profile_path`); GET/POST/revisions all use it | `server.py` |
| Invalid routing / fabricated approval persisted (47, 2) | HIGH | Server recomputes conflicts; **rejects any error-level conflict** (403, no write); approved+empty → draft | `server.py` |
| Destructive same-ID overwrite, non-atomic (49, 3) | HIGH | Immutable revisions `<id>.rN.json` + `os.replace` atomic writes; manifest atomic; `/api/revisions` | `server.py` |
| Client-mutable `arcade_evidence` (45, 4) | MED | `arcade_evidence` is **server-derived** from analysis artifacts on load+save; client value discarded | `server.py` |
| Genesis PSG per-channel stereo is false (42) | HIGH | PSG modeled **mono/center**; `stereo_per_channel:false` | `server.py`, `app.js` |
| Tone-3/noise coupling unconditional (41) | MED | Coupling warning **only** when `noise_mode == tone3_clocked`; fixed rates coexist with tone 3 | `server.py`, `app.js` |
| Divider-zero & noise taps unspecified (38, 40) | MED | Divider-zero documented; noise taps/period **labeled UNRESOLVED** (no false fidelity) | `server.py` |
| `$82` descriptor misparsed as count 130 (17) | HIGH | Verified `0x02AA-0x02FE`; lead `>=0x12` = channel/control identifier, not a count; inventory regenerated | `gen_music_command_inventory.py`, C, CSV |
| C/coverage overstate decompilation (54, 55) | HIGH | C relabeled a **declaration index (0 bodies)**; coverage vocabulary `INDEXED`/`CONTROL_FLOW_VERIFIED`/`UNRESOLVED`; none `SEMANTIC_C_COMPLETE` | C, CSV |
| Stale TC0140SYT; ADPCM latch roles swapped (10, 22) | MED/LOW | PC060HA terminology; `0xB000=addr, 0xC000=start, 0xD000=stop` | C, CSV |
| "All 8 FM channels used" inflation (24) | MED | Key-ON counted only when operator mask ≠ 0; separate key-off/KC/keyed/peak/sustained metrics | `analyze_ym2151_captures.py` |
| Key occupancy ≠ polyphony; heuristic labeled (25, 28, 29) | MED | Explicit occupancy-vs-audibility note; sustained heuristic defined; musical identity = null | analyzer, `server.py` |
| RG-005 denominator 141 → 174 (35) | MED | Report-label correction (analyzer already correct: 43+55+62+2+12) | RG-005 notice |
| VGM "DAC writes 0" misleading (33) | LOW | DAC reports `direct_sample_writes` **and** `stream_starts` (398) + `active` | `vgm_genesis_analysis.py` |
| VGM `$4F` length wrong (31) | LOW | `$4F` parsed as 2 bytes + regression test | `vgm_genesis_analysis.py` |
| Lawrence PSG "additive" unverified (36) | MED | Qualified as unverified (no arcade note/time alignment) | RG-005 notice |
| Overbroad `.js` routing (finding 6) | LOW | Only `/app.js` & `/style.css` served; unknown `.js` → 404 | `server.py` |
| AUDIO-003 absent (2); no audio RG-007 (3) | — | Not claimed complete anywhere; identifiers kept as AUDIO-### | all |

CONFIRMED-correct items from Cody's matrix (clocks, PC060HA device, banking, dispatch, 44-entry song
table, deep-FM distribution, 174 population, FM1-3 stereo stack, FM6 DAC, loopback bind, audition-honest,
FM6 rejection, proposal/approval separation, unknown-field round-trip) were **preserved unchanged**.

## 3. Before / after (key defects)

- **GET traversal:** before `/api/profile?p=../../../specs/palette_decisions` → **200 + disclosed JSON**;
  after → **400** "invalid profile id" (encoded `%2e%2e%2f…` also 400).
- **Invalid routing:** before invalid dest saved with **200**; after → **403**, no file written.
- **Fabricated approval:** before client `approval_status:"approved"` + bad routing persisted; after →
  **403** on any error conflict; approved-with-empty-routing downgraded to **draft**.
- **Versioning:** before same-ID overwrote the only file (rev→2 but rev1 lost); after rev1 **and** rev2
  snapshots both retained; manifest revision matches current (2); no `.tmp_` residue.
- **Evidence:** before client `arcade_evidence.command_id:"0xAB"/provenance:"FORGED"` stored; after the
  stored evidence is server-derived (`command_id:null`, provenance "server-derived…", real keyed set).
- **PSG stereo:** before "coarse per-channel L/R"; after mono/center, `stereo_per_channel:false`.
- **Tone-3/noise:** before any tone3+noise → warning; after warning only with `tone3_clocked`.
- **YM2151:** before "all 9 tracks use 8 FM"; after Credit 2 / Opening 8 / Scene1-FinalBoss 6 / Ending 8
  keyed (matches Cody's independent table).
- **`$82`:** before `count:130, form:single_subsequence`; after `form:channel_control_identifier,
  identifier:0x82` for commands 0x03/0x0A/0x0D/0x21/0x26.
- **VGM:** before "DAC writes: 0"; after `stream_starts:398, active:true`; `$4F` now 2 bytes (regression
  test); distinct-patch total **174**.
- **C/coverage:** before 11 `COMPLETE` implying semantic equivalence; after honest levels, 0
  `SEMANTIC_C_COMPLETE`, PC060HA + corrected latch roles + corrected `$82` note.

## 4. Files changed

- `tools/audio_composer/server.py` — `safe_profile_path` + `ProfileIdError`; schema v1→v2 + migration;
  server-derived `arcade_evidence`; reject error-conflict saves; atomic immutable revisions
  (`atomic_write_json`, `list_revisions`, `/api/revisions`); corrected PSG model (mono, noise selector,
  divider-zero doc, UNRESOLVED taps); conditional tone-3 coupling (`noise_mode`); tightened static routes;
  inventory reads corrected YM metrics.
- `tools/audio_composer/app.js` — corrected track-list metrics; PSG noise-mode selector; corrected PSG
  panel (mono, UNRESOLVED noise, divider-zero); sends `noise_mode`.
- `tools/audio_composer/verify_audio_composer.py` — **rewritten**: 37 checks (21 required scenarios +
  unit + HTTP-level), isolated temp storage, Palette Composer untouched check.
- `tools/audio/analyze_ym2151_captures.py` — corrected key-on/off/KC/keyed/peak/sustained metrics;
  regenerated `build/audio/ym2151_track_reports/*`.
- `tools/audio/vgm_genesis_analysis.py` — `$4F` 2-byte fix; DAC-stream trigger reporting; FM6 DAC via
  stream; regenerated `build/audio/vgm_analysis/*`.
- `tools/audio/gen_music_command_inventory.py` — **new** reusable generator with the verified descriptor
  grammar; regenerated `build/audio/music_command_inventory.json`.
- `analysis/decompilation/c/z80/rastan_z80_sound_driver.c` — relabeled declaration index; PC060HA; latch
  roles; `$1B`/bank; `$82` grammar.
- `analysis/decompilation/c/z80/z80_function_coverage.csv` — honest evidence vocabulary; terminology +
  descriptor + latch corrections.
- `analysis/audio/decision_profiles/{baseline_current.json,profile_manifest.json}` — regenerated v2 seed.
- Correction notices added to `Andy_RG005…`, `Andy_RG006…`, `Andy_audio001…`, `Andy_audio002…`,
  `Andy_audio004…`. This report; `AGENTS_LOG.md`; `OPEN_ISSUES.md`.

## 5. Test results

`PYTHONDONTWRITEBYTECODE=1 python3 tools/audio_composer/verify_audio_composer.py` → **37 passed, 0 failed**
(covers all 21 required scenarios + traversal/encoded-traversal/invalid-id, invalid-route & FM6 rejection,
server-derived evidence, fabricated-approval rejection, proposal/approval separation, immutable revisions,
atomic writes, manifest consistency, legacy v1 migration, unknown-field preservation, tone-3 fixed vs
tone3-clocked, PSG mono, corrected YM key-on counts, `$82` handling, VGM `$4F`, DAC-stream reporting, 174
population, unit validator/safe-path, audition-unavailable, tightened static routes, Palette Composer
compiles). Live HTTP smoke on the real server confirmed traversal→400, Scene-1 keyed=6,
`stereo_per_channel=false`, unknown `.js`→404.

## 6. Corrected output paths

`build/audio/ym2151_track_reports/*.json`, `build/audio/vgm_analysis/LM-Main Stage Theme (1).json`,
`build/audio/music_command_inventory.json`, `analysis/audio/decision_profiles/` (v2 seed).

## 7. Launch command

`tools/audio_composer/run.sh` → http://localhost:8781 (Python stdlib only).

## 8. Remaining unresolved (not in scope / gated by AUDIO-003)

- AUDIO-003 itself: sequence opcode grammar, `0x0348` full normalization, ROM instrument tables/banks,
  ADPCM sample table + trigger map, command→track proof, and per-note overlap timing.
- PSG noise exact taps/period and divider-zero edge behaviour: labeled UNRESOLVED pending an authoritative
  Genesis hardware/test-vector source (not asserted as fidelity).
- Audible YM2151/YM2612/PSG comparison: still requires a validated render stage (audition stays
  UNAVAILABLE; no fabrication).
- `0x0479` note-event encoding, `0x03E5` handler semantics: UNRESOLVED (control flow only).

## 9. No production / build changes — confirmation

No 68000/Z80 production ASM, no ROM, no build counter change (472→472), no accepted-baseline change, no
original capture/ROM/Lawrence-VGM modification, Palette Composer untouched (`server.py` still compiles; not
edited). All corrective writes are in tools/analysis/docs only.

## 10. Recommendation for independent correction verification

Cody should re-run the AUDIO-008 adversarial audit against the corrected tools: confirm GET/encoded
traversal now rejected, invalid/fabricated-approval saves rejected, immutable revisions + atomic writes,
server-derived evidence, PSG mono + conditional noise coupling, the regenerated `$82`/YM/VGM/inventory
outputs, and the relabeled C/coverage — then confirm OPEN-039 stays open pending AUDIO-003 and audible
comparison.
