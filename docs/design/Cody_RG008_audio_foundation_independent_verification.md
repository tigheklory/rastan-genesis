# AUDIO-008 — Cody — Audio foundation independent verification

**Date:** 2026-10-21  
**Issue:** OPEN-039 (remains open)  
**Scope:** adversarial, read-only verification of AUDIO/RG-001 through RG-006  
**Verdict:** **PARTIALLY TRUSTWORTHY — CORRECTIONS REQUIRED BEFORE CONVERSION**

The original-hardware map, PC060HA correction, clocks, core command dispatch, most capture-derived
FM statistics, and Lawrence VGM allocation reproduce. They are a useful foundation. The work is not
ready to authorize conversion or user profile authoring: AUDIO-003 is absent, the C file is an index of
prototypes rather than a semantic decompilation, the special descriptor form is misdescribed, “all eight
FM channels used” is analyzer inflation, Lawrence's additive-PSG conclusion lacks an arcade alignment,
the Genesis PSG stereo claim is false, and the Composer has confirmed path-disclosure and profile-
integrity defects.

No production source or ROM was changed or built. All Composer writes below were redirected to a
temporary directory.

## 1. Baseline, scope, and authoritative inputs

- Accepted baseline: **Build 0472**. `accepted/build-0472^{}` resolves to exact ROM-producing source
  `4d5aadb0e92387617594404f9e757597c87517a3`.
- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0472.bin`, 2,739,896 bytes,
  SHA-256 `5b855e163a572c3a511a76470199c9cb13324f6ea0739bbd0f6834b80092dc7a`.
- Build counter before and after: **472**. No build target was run.
- Audit worktree HEAD: `84f74ae81be2b6363e99e5184d69cf83fc65ef12` on
  `rastan-direct-proposal`; the pre-existing dirty tree was preserved.
- `build/regions/audiocpu.bin`: 65,536 bytes, SHA-256
  `db0e2d4954bcb0d558f6b6dd194badccdeb29c62282051ff47b687548701e478`.
- `build/regions/adpcm.bin`: 65,536 bytes, SHA-256
  `65a82d3669a2d52b00e019dedef858e3778ecd1e8526326beaf0c100df29311f`.
- Lawrence VGM: 71,848 bytes, SHA-256
  `b786794eedb319c71716bb481e0836647ecf002de7bb5bd8761d173fa948580d`.

Actual AUDIO artifacts are the five Andy reports in `docs/design/`, the Ghidra project and exports,
the two Z80 reference files, ROM/capture/VGM analyzers and generated JSON, the Phase-1 Composer, and
its baseline profile. **AUDIO-003 has not been completed. There is no audio RG-007**; the repository's
RG-007 concerns bat/airborne decompilation. Consequently the sequence opcode grammar, ROM instrument
identity, command-to-track names, ADPCM sample table/trigger map, and exact overlap timeline remain
open. The older AUDIO-001 TC0140SYT wording is stale; later evidence correctly identifies PC060HA.

## 2. Independent Z80 architecture and control verification

The original ROM bytes, independently inspected disassembly, and
`docs/reference/mame/rastan/src/mame/taito/rastan.cpp` agree on:

- Z80 `$0000-$3FFF` fixed ROM; `$4000-$7FFF` 16-KiB bank window. MAME configures four entries from
  file offsets `$0000/$4000/$8000/$C000`; runtime `$4000+x` in bank *n* maps to file `n*$4000+x`.
- `$8000-$8FFF` RAM; YM2151 `$9000/$9001`; PC060HA `$A000/$A001`; MSM5205 address/start/stop
  latches `$B000/$C000/$D000`.
- Bank selection is `data & 3` from the YM2151 port-write callback. It is not an ordinary Z80 memory
  latch, so the lack of a literal bank register store in disassembly is not evidence of no banking.
- Reset `$0000 -> JP $010B`; IM1/RST `$0038 -> JP $01F9`; NMI `$0066` receives the PC060HA nibble
  protocol, reconstructs the command byte, and feeds the two rings.
- The `$010B` main loop writes YM register `$1B` with `$8F23|$40` (thereby selecting a ROM bank),
  dispatches commands, then runs the per-frame path. `$01F9` polls YM status and calls `$0479` and
  `$19A8` on timer state. Exact cycle budget is not yet established.
- `$158C` is the busy-waited YM address/data writer. Z80 and YM clocks are 4 MHz. The MSM5205 is
  384 kHz in S48/4-bit mode, yielding the 8-kHz nibble clock.
- `$03E5` indexes 15 little-endian handler words at `$041B`: F0 -> `$03F7`, F1-F3 -> `$0408`, and
  F4-FE -> `$041A`. This proves a small control dispatcher, not meanings for every handler.
- `$19A8` uses the `$8E00` state, writes `$D000` to stop, `$B000` for high address, `$C000` to start,
  and `$D000` to stop. The separate ADPCM ROM is consumed by the MSM5205-side circuit. Sample names,
  exact table, boundaries, and originating trigger commands remain unresolved.

The hardware-device conclusion is strong. Behavioral names above the proven byte/control flow are
kept qualified where AUDIO-003 is still needed.

## 3. Song table and descriptor cross-check

The independent parser reads 44 little-endian words at `$2300`. Descriptor addresses span `$2830`
through `$3370`; referenced subsequences span `$28A0` through `$3390`. There are zero invalid table
pointers and zero invalid referenced subsequences under the verified grammar; no direct-command pair
occurs in this data set.

For lead bytes below `$12`, the descriptor is `count` followed by `count` two-byte records. A zero
high byte is a direct command; otherwise the word is a little-endian subsequence pointer. The five
descriptors used by commands `$03,$0A,$0D,$21,$26` begin with `$82`. Code `$02C3-$02CA` passes `$82`
directly to `$02FE`; **it is a channel/control identifier, not a count of 130**. AUDIO-002's
`count>=0x12 single-subseq` wording and inventory label are contradicted.

All observed subsequences lie below the fixed/bank boundary `$4000`, but that proves only this
referenced sequence set. It does not prove instruments or all musical assets are unbanked. Table
`$0348` has 16 little-endian pointers (32 bytes); how every legal identifier is normalized and how
all channel state is installed remains only partially decoded.

## 4. Z80 reference C and coverage audit

`analysis/decompilation/c/z80/rastan_z80_sound_driver.c` contains **12 declarations and zero function
bodies**. The Ghidra export lists 63 functions. `z80_function_coverage.csv` has 20 rows but only 17
unique function entry points (one repeated `$0479`, plus data tables). Its 11 `COMPLETE` labels mean
that a comment/index entry exists; they cannot mean C semantic equivalence. Register lifetimes, flags,
stack effects, alternate paths, indirect control flow, and return behavior are not translated into C.

Function-by-function audit of the C declarations:

| Entry | Declared role | Result | Evidence / discrepancy |
|---|---|---|---|
| `$010B` | init/main loop | PARTIALLY VERIFIED | Entry and broad flow match; comment calls `$158C` a “refresh” and omits the `$1B` port/bank consequence; no body. |
| `$0066` | NMI command receive | PARTIALLY VERIFIED | Entry/rings/handshake supported; comment still names TC0140SYT rather than PC060HA; no body. |
| `$00C0` | 16-slot enqueue | VERIFIED | Ring addresses/mask and entry agree with instructions. |
| `$00E9` | 32-slot enqueue | VERIFIED | Ring addresses/mask and entry agree with instructions. |
| `$0254` | command dispatch | VERIFIED | Range branches and destinations reproduce; handler semantics remain separately scoped. |
| `$02AA` | song select | INCORRECT | Ordinary counted form exists, but declaration presents it as universal and omits the `$82` single-descriptor path. |
| `$0368` | E0-EF control | PARTIALLY VERIFIED | EE/EF path supported; the other meanings are not decoded. |
| `$03E5` | F0-FE class | PARTIALLY VERIFIED | It is no longer wholly unresolved: jump table is known; handler semantics remain unresolved. |
| `$158C` | YM writer | VERIFIED | Busy polling and address/data writes match instructions. Signature is illustrative, not ABI-accurate C. |
| `$1A00` | ADPCM trigger region | INCORRECT | Comment swaps latch roles: D is stop, B is address-high, C is start, not D address/trigger, B bank/start, C reset/stop. |
| `$01F9` | IRQ/timer | PARTIALLY VERIFIED | Vector and called engines supported; full flag/timing semantics unresolved. |
| `$01C2` | per-frame update | UNRESOLVED | Call site exists; no translated body or complete semantics. |

Coverage must be rebuilt around instruction ranges and semantic evidence. It must distinguish
`INDEXED`, `CONTROL_FLOW_VERIFIED`, and `SEMANTIC_C_COMPLETE`; no current entry qualifies for the last
category because there are no bodies.

## 5. YM2151 capture verification

The independent parser treats register `$08` as key-on only when its operator mask is nonzero and as
key-off when zero. Andy's first analyzer increments `keyon_events` for every `$08` write, including
key-offs, and declares a channel “used” on either those writes or any key-code write. That is why its
“all nine tracks use all eight FM channels” statement is false.

Independently keyed channel counts / peak simultaneously keyed counts are:

| Capture | Keyed | Peak |
|---|---:|---:|
| Credit | 2 | 2 |
| Opening | 8 | 8 |
| Scene 1 | 6 | 6 |
| Name register | 6 | 6 |
| Scene 2 | 6 | 6 |
| Scene 3 boss | 6 | 6 |
| Scene clear | 6 | 6 |
| Final boss | 6 | 6 |
| Ending | 8 | 8 |

No capture enables YM2151 noise. The final algorithm distribution over keyed channel/capture states
reproduces `{1:32, 2:10, 3:7, 4:2, 5:3}`; all algorithm-register writes are
`{0:2, 1:108, 2:66, 3:36, 4:22, 5:7}` with no algorithm 6/7.

The “sustained musical” result is a heuristic (`>=20` key-ons, `>=3` distinct KC values, span >2 s),
not a sequencer-derived role. Scene 1 channel 4 has 402 key-ons over 52.2 s but only two KC values and
is therefore labeled sporadic; nevertheless six channels are keyed concurrently. Thus “Scene 1 needs
only five sustained FM voices” and role/SFX labels are not sufficient capacity proof. Deep-FM register
usage is confirmed; “no natural PSG candidate” is an engineering interpretation, not an independently
verified acoustic conclusion. No production route should be selected before sequence/timing decode and
audible comparison.

## 6. Lawrence VGM verification

Independent byte parsing and a clean replay of Andy's analyzer agree:

- VGM 1.96; YM2612 7,670,454 Hz; SN76489 3,579,545 Hz.
- 2,366,496 total samples parsed/header; loop 1,792,800 samples; end marker reached; no command in this
  file was unsupported.
- Commands: `$50` 4,884; `$52` 8,769; `$53` 740; `$61` 3,168; `$67` 4; `$90/$91/$94` one each;
  `$92` 398; `$95` 398; `$66` one.
- Four PCM blocks of 4,818/4,814/4,817/4,813 bytes, stream rate 8 kHz, 398 stream starts, and DAC
  enable. The tool's displayed “DAC writes: 0” counts only direct `$2A`/`$8n` writes and is misleading
  for stream-command playback; it does not invalidate the 398-trigger conclusion.
- FM key-ons: 88/102/93/39/131 on FM1-5; none on FM6. PSG tone key-ons 21/25/21 and one noise event.
  This confirms five pitched FM channels + three PSG tones + FM6 DAC.
- Initial FM1/2/3 patch state is equal and pan bytes `$D4/$94/$54` establish center/left/right.
- De-duplicated consecutive patch-state snapshots are FM1 43, FM2 55, FM3 62, FM4 2, FM5 12:
  **174 total**. Algorithm `{3:108,0:35,5:20,4:6,6:5}` and feedback
  `{5:92,0:47,6:30,7:3,2:2}` also total 174. RG-005's denominator 141 is a report-label error, not
  a duplicate-counting bug.

PSG first activity at roughly 12.196/16.719/29.677 s (plus the noise event) is demonstrated only
inside Lawrence's handmade VGM. No note/time alignment against the arcade capture was performed.
Therefore “PSG is additive, not substitution” and detailed musical-role names remain **unverified**.
The VGM remains a technique reference, not an authoritative conversion map.

The generic analyzer also advances `$4F` as a three-byte command even though it is two bytes. This VGM
contains no `$4F`, so the current output is unaffected; it is a latent parser defect.

## 7. Genesis PSG hardware model

The Sega technical overview supports three tone generators plus noise, independent 4-bit attenuation
in 2-dB steps, a 10-bit tone divider, fixed noise selections, and tone-3 clocking only when the noise
frequency selector is 3. It also documents stereo control for the YM2612 FM/DAC path, not a Genesis
VDP-PSG per-channel stereo latch.

- Three fixed-duty square channels and one noise channel: supported.
- `clock/(32*n)`: supported for ordinary nonzero divider values; the Composer excludes divider zero
  without documenting its chip-specific edge behavior.
- Genesis 16-bit versus classic TI 15-bit noise distinction: plausible and consistent with the cited
  model, but exact taps/period behavior still need a selected authoritative hardware/test-vector source.
- The validator warns whenever tone 3 and noise are both assigned. This is wrong without a noise-mode
  field: fixed noise rates coexist with tone 3 without the selector-3 pitch dependency.
- `server.py`'s “coarse per-channel L/R via Genesis stereo latch” is false for the Genesis VDP PSG.
  Treat PSG as mono/center unless a different target extension is explicitly introduced.

## 8. Audio Composer code, security, persistence, and limitations

Confirmed positive behavior: it binds `127.0.0.1`; expected read APIs respond; malformed JSON returns
400; POST profile IDs are sanitized; `baseline_current` cannot be overwritten through POST; FM6 music
returns 403 and writes no file; proposals and approvals remain separate in an ordinary round trip;
unknown fields survive; `/api/audition` honestly says unavailable; no renderer or automatic routing is
present; names are not used as command IDs; evidence/VGM files are loaded read-only.

Confirmed defects from an isolated HTTP server:

1. **GET traversal:** `/api/profile?p=../../../specs/secret` joins the query value directly to
   `PROF_DIR`; the test returned 200 and disclosed a JSON file outside the profile directory.
2. **Invalid profiles saved as approved:** an invalid destination produced an `invalid_dest` error but
   POST still returned 200 and wrote the file. The client can also submit `approval_status`, routing,
   and `arcade_evidence`; the server recomputes conflicts but rejects only FM6. “Server-authoritative
   validation” is therefore incomplete.
3. **Destructive pseudo-versioning:** saving the same ID overwrites the only profile file, then rewrites
   the manifest separately. Revision increments to 2 but revision 1 is not preserved. Neither write is
   atomic, so a crash can split profile/manifest state.
4. **Evidence snapshot is mutable:** `arcade_evidence` is kept separate structurally but accepted from
   the client. This cannot alter original captures, but it can make a profile's purported factual basis
   false.
5. **Tone-3/noise warning is unconditional** because the schema contains no noise-frequency selector.
6. Any unknown `.js` path returns `app.js` with 200. This is not filesystem traversal, but routing and
   status behavior are overbroad.

The profile schema has fields for future instrument and time-dependent decisions, but field presence is
not implementation. There are no editing controls or render validation for those features. The only
repository profile observed was the baseline/manifest seed; the audit did not modify it.

## 9. Test execution and reproducibility

Existing suite command:

```sh
PYTHONPYCACHEPREFIX=/tmp/audio008_pycache PYTHONDONTWRITEBYTECODE=1 \
  python3 tools/audio_composer/verify_audio_composer.py
```

Result: **26 passed, 0 failed**. These tests accurately exercise their narrow helper-level assertions,
but do not cover GET traversal, invalid-profile rejection, atomic/version preservation, immutable
evidence, actual PSG noise modes/stereo, or audio fidelity.

Independent command (requires local loopback socket permission; all profile state is temporary):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  analysis/audio/verification/audio008_independent_audit.py \
  --output analysis/audio/verification/audio008_results.json
```

It covered inventory, hardware model, Lawrence data, audition status, list/load/valid save/reload,
proposal/approval persistence, FM6 rejection, invalid destinations, duplicate destinations,
tone3+noise, malformed JSON, GET/POST traversal, future fields, same-ID revisions, and static routes.
The preserved log is `analysis/audio/verification/audio008_test_log.txt`; machine results are
`analysis/audio/verification/audio008_results.json`.

Analyzer replay:

```sh
python3 tools/audio/vgm_genesis_analysis.py \
  'audio/Inglebard Agressive World Handmade Genesis version/LM-Main Stage Theme (1).vgm' \
  --outdir /tmp/audio008_vgm_replay
```

The replay JSON equals the existing generated JSON. No server remained running after the audit.

## 10. Claim-by-claim matrix (RG-001 through RG-006)

Confidence is high unless qualified. File/line and ROM-address evidence appears in the reproduction
sections above.

| # | Claim / source | Independent result | Status | Recommendation |
|---:|---|---|---|---|
| 1 | 0472/472 is baseline | Tag, ROM hash, counter reproduce | CONFIRMED | Preserve |
| 2 | AUDIO-003 is missing | No required decoder/map/report exists | CONFIRMED | Complete next |
| 3 | Audio RG-007 exists | Repository RG-007 is unrelated bats work | CONTRADICTED | Do not cite as audio work |
| 4 | Fixed ROM `$0000-$3FFF` | ROM/MAME agree | CONFIRMED | Preserve |
| 5 | Bank window `$4000-$7FFF` | MAME map agrees | CONFIRMED | Preserve |
| 6 | Four 16-KiB banks | `configure_entries(0,4,...,0x4000)` | CONFIRMED | Preserve |
| 7 | YM port selects bank | callback/data&3 reproduce | CONFIRMED | Preserve |
| 8 | Reset `$0000->$010B` | Original bytes agree | CONFIRMED | Preserve |
| 9 | IRQ/NMI high-level semantics complete | Vectors/flow known; timing incomplete | PARTIALLY CONFIRMED | Finish AUDIO-003/timing |
| 10 | PC060HA, not TC0140SYT | MAME device/map agree | CONFIRMED | Remove stale wording |
| 11 | 4 MHz/4 MHz/384 kHz S48 | MAME config agrees | CONFIRMED | Preserve |
| 12 | Main loop fully characterized | Loop exists; bank-select side effect omitted | PARTIALLY CONFIRMED | Correct description |
| 13 | `$158C` YM writer | Instruction flow agrees | CONFIRMED | Preserve |
| 14 | 44 song table entries | Independent parse = 44 | CONFIRMED | Preserve |
| 15 | Song pointers little-endian | Independent parse agrees | CONFIRMED | Preserve |
| 16 | Ordinary counted records | Reproduced for lead `<$12` | CONFIRMED | Qualify grammar |
| 17 | Lead `$82` means count 130/single subsequence | Code passes it as channel/control ID | CONTRADICTED | Fix parser/report |
| 18 | Observed sequences are in fixed ROM | `$28A0-$3390`, none invalid | CONFIRMED | Do not generalize to instruments |
| 19 | `$0348` installation fully understood | Table verified; complete normalization not | PARTIALLY CONFIRMED | Decode in AUDIO-003 |
| 20 | `$03E5/$041B` dispatch shape | 15 entries and three targets reproduce | CONFIRMED | Avoid invented handler names |
| 21 | B/C/D are address/start/stop | MAME and code agree | CONFIRMED | Preserve |
| 22 | C comment's D/B/C latch roles | Roles are swapped/misnamed | CONTRADICTED | Correct after audit approval |
| 23 | ADPCM sample map/trigger meanings complete | Required data absent | UNVERIFIED | AUDIO-003 |
| 24 | All tracks use all 8 FM channels | Key-off/KC writes inflate “used” | CONTRADICTED | Redefine metrics |
| 25 | Peak key occupancy 6/8 | Independent parser reproduces | CONFIRMED | Label keyed, not necessarily sounding |
| 26 | No YM2151 noise in captures | No enable writes | CONFIRMED | Preserve |
| 27 | Deep-FM algorithm distribution | `{1:32,2:10,3:7,4:2,5:3}` reproduces | CONFIRMED | Preserve as capture-derived |
| 28 | Scene 1 requires only five sustained FM voices | Heuristic says 5; six key concurrently | PARTIALLY CONFIRMED | Do not use as capacity proof |
| 29 | No voice is naturally PSG-suitable | Timbre judgment not acoustically validated | UNVERIFIED | Render/listen test |
| 30 | Lawrence VGM 1.96/clocks/times | Header and samples reproduce | CONFIRMED | Preserve |
| 31 | Lawrence command stream clean | Current file parsed to `$66`, none unsupported | CONFIRMED | Fix latent `$4F` handling |
| 32 | Five FM + three tones + FM6 DAC | Registers/streams reproduce | CONFIRMED | Preserve as reference only |
| 33 | Four blocks/8 kHz/398 triggers | Independent parse reproduces | CONFIRMED | Clarify “DAC writes 0” UI |
| 34 | Initial FM1-3 shared patch C/L/R | Patch state/pan bytes reproduce | CONFIRMED | Preserve |
| 35 | Patch-snapshot denominator 141 | Actual de-duplicated population is 174 | CONTRADICTED | Correct denominator |
| 36 | Lawrence PSG is additive vs arcade FM | No arcade note/time alignment exists | UNVERIFIED | Align before claiming |
| 37 | PSG has 3 tone + noise channels | Sega docs agree | CONFIRMED | Preserve |
| 38 | Divider model is complete | Formula/range mostly right; zero omitted | PARTIALLY CONFIRMED | Specify/test zero |
| 39 | 4-bit, 2-dB attenuation | Sega docs agree | CONFIRMED | Preserve |
| 40 | Exact 16-bit noise model/taps proven | Family difference supported; taps not audited | PARTIALLY CONFIRMED | Add authoritative vectors |
| 41 | Tone3+noise always has coupling conflict | Only selector 3 couples pitch | CONTRADICTED | Add noise mode to schema/rule |
| 42 | Genesis PSG has coarse per-channel stereo | Genesis VDP PSG has no such latch | CONTRADICTED | Remove stereo claim |
| 43 | Composer loopback-only | Binds `127.0.0.1` | CONFIRMED | Preserve |
| 44 | Audition unavailable/honest | API/UI do not fake playback | CONFIRMED | Preserve |
| 45 | Evidence/proposal/approval separation | Fields separate; evidence client-mutable | PARTIALLY CONFIRMED | Make evidence server-derived |
| 46 | FM6 assignment is rejected | 403, no file written | CONFIRMED | Preserve |
| 47 | Server-authoritative invalid-route validation | Invalid destination saved with 200 | CONTRADICTED | Reject all error conflicts |
| 48 | Profile paths are traversal-safe | GET traversal disclosed JSON | CONTRADICTED | Canonicalize/allowlist IDs |
| 49 | Profiles are versioned/preserved | Same ID overwrites; no old revision | CONTRADICTED | Atomic immutable revisions |
| 50 | Unknown future fields round-trip | Isolated save/reload preserved field | CONFIRMED | Add compatibility policy |
| 51 | Audio tools isolated from production | Reads evidence; profile writes confined by design | CONFIRMED | Fix traversal before trust |
| 52 | Existing suite is 26/26 | Rerun = 26/26 | CONFIRMED | Expand suite |
| 53 | Existing tests substantiate security claims | Material HTTP paths are uncovered | CONTRADICTED | Add adversarial tests |
| 54 | Curated C is a decompilation | 12 prototypes, zero bodies | CONTRADICTED | Relabel or implement bodies |
| 55 | Coverage CSV represents semantic completeness | 20 rows/17 entries vs 63 functions | CONTRADICTED | Redesign coverage vocabulary |

Matrix totals: **32 CONFIRMED, 7 PARTIALLY CONFIRMED, 13 CONTRADICTED, 3 UNVERIFIED,
0 NOT IMPLEMENTED** (55 material claims).

## 11. Severity-ranked findings

### BLOCKER (0)

No defect writes production ASM/ROM automatically. Conversion remains gated by missing AUDIO-003 and
the high-severity issues below rather than an active production-corruption path.

### HIGH (6)

1. GET profile directory traversal discloses JSON outside the profile tree.
2. Invalid routing and client-fabricated approval/evidence can be persisted despite error conflicts.
3. Same-ID saves destructively overwrite profiles; profile/manifest writes are non-atomic and revisions
   are not retained.
4. Genesis PSG stereo capability is falsely modeled.
5. The special `$82` descriptor is materially misparsed/misdocumented.
6. The C/coverage artifacts materially overstate decompilation and semantic completeness.

### MEDIUM (9)

1. “All eight FM channels used” counts key-offs/initialization as use.
2. Five-sustained-voice and musical/SFX labels are heuristic, not conversion-capacity proof.
3. Tone3+noise warning ignores fixed-frequency noise modes.
4. Lawrence PSG-additive conclusion is unsupported by arcade alignment.
5. RG-005 denominator says 141 rather than 174.
6. VGM UI reports zero DAC writes despite 398 stream starts.
7. Profile `arcade_evidence` is client-mutable.
8. Divider-zero and exact noise taps are unspecified/untested.
9. ADPCM table, trigger mapping, and sequence grammar remain missing (AUDIO-003).

### LOW (4)

1. VGM `$4F` length handling is wrong but unexercised by this input.
2. Unknown `.js` routes return app.js/200.
3. Stale TC0140SYT and “below `$8000` fixed ROM” wording persists in historical/current summaries.
4. “DAC writes” terminology conflates direct data writes with stream-trigger playback.

## 12. Change isolation

Audit-created files are only:

- `analysis/audio/verification/audio008_independent_audit.py`
- `analysis/audio/verification/audio008_results.json`
- `analysis/audio/verification/audio008_test_log.txt`
- `docs/design/Cody_RG008_audio_foundation_independent_verification.md`
- this task's narrowly scoped additions to `AGENTS_LOG.md` and `OPEN_ISSUES.md`

No production 68000/Z80 assembly, ROM, counter, tag, accepted baseline, graphics/Palette Composer,
original capture, Lawrence VGM, or user audio profile was modified. Existing unrelated dirty files and
concurrent Andy/Cody work were neither staged nor reverted. Final isolation hashes remained:
`baseline_current.json` `e368f7027ef582293fceed0bf53e424157ab60ae0d8c47703d4681d9d0c13d77`,
`profile_manifest.json` `d4d615f0c5d432ff61500517b60586fbedb7152e1cebfafafda68b8929f4d3e9`, and
Palette Composer `server.py` `4e39af55614fd4787a08aff06cbceda167725e1822816f6fc61a2c49a8fec40a`.

## 13. Required correction and development order

1. Fix Composer GET path containment, reject every error-level validation conflict, make evidence
   server-derived, and implement atomic immutable revisions; add HTTP regression tests.
2. Correct the PSG model: mono Genesis PSG, explicit noise selector, conditional tone-3 coupling,
   divider-zero behavior, and authoritative noise test vectors.
3. Complete AUDIO-003 from ROM: sequence opcode grammar, `$0348` installation semantics, instrument
   tables/banks, ADPCM table/trigger map, command-to-track proof, and timing/overlap evidence.
4. Correct the `$82` descriptor model, YM key-on metrics, VGM 174 denominator, stream-DAC display, and
   `$4F` parser length. Regenerate derived JSON only after review.
5. Replace the prototype-only “C decompilation” with instruction-range-backed bodies or relabel it as
   an index; rebuild coverage with honest evidence levels.
6. Only then build validated YM2151/YM2612/PSG render comparison and author routing. No original
   instrument receives a default FM/PSG assignment; Lawrence remains a secondary technique reference.

OPEN-039 must remain open. **AUDIO-008 is complete as an audit, not as audio implementation approval.**
