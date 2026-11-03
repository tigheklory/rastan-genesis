# AUDIO-010 — Cody: Independent Regression Verification of AUDIO-009

**Task:** AUDIO-010  
**Issue:** OPEN-039 (remains open)  
**Date:** 2026-10-22  
**Type:** independent verification / regression audit  
**Implementation:** not authorized and not performed  
**Verdict:** **AUDIO-009 REJECTED**

## 1. Executive result

AUDIO-009 correctly repaired the audio-analysis, PSG-model, path-containment, routing-validation,
server-derived-evidence, and Z80 C/coverage defects tested here. It did **not** fully repair the two
material Audio Composer guarantees it claims:

1. A client can submit a valid-looking `approved_routing` together with
   `approval_status:"approved"`; the generic profile-save endpoint returns 200 and persists the profile
   as approved. Conflict validation proves only that the route is structurally valid. It is not proof
   that a user approved it.
2. Revision snapshots are individually written with `os.replace()`, but the snapshot/current/manifest
   operation is not a transaction. Same-profile requests are not serialized. An interrupted save can
   leave an orphan snapshot which the next save silently overwrites, and a manifest-write failure remains
   unreconciled after server restart.

The corrected suite passes **37/37**. The independent AUDIO-010 suite passes **33/40** and exposes seven
failures omitted by that suite. Four are manifestations of the material approval/revision defects; the
other three show lexicographic revision ordering and the absence of revision retrieval/identifier
handling. Because the task specifically required secure approval and immutable crash-safe revisions,
passing unrelated corrections do not justify conditional acceptance.

No Audio Composer source, analyzer, canonical generated audio data, user profile, production ASM, ROM,
build counter, accepted tag, original ROM/capture/VGM, or Palette Composer file was changed by AUDIO-010.

## 2. Current project baseline

- Current accepted baseline: **Build 0473**.
- `accepted/build-0473^{}`: `f6e975b864af2aca7bdf24b0a40a9db43bd62f59`.
- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0473.bin`.
- Size: 2,739,896 bytes.
- SHA-256: `42cac0085a0078ffbc4293e493ece95280e854d4d2b5bf4512756bb095ded717`.
- Current build counter observed before and after this audit: **477**. This is concurrent repository state;
  Build 0477 is not an accepted baseline and AUDIO-010 did not run a build or alter the counter.
- Audit HEAD: `589aca5d6ffbd5fa5598a28ade5163a59c5d2d81` on `rastan-direct-proposal`.

This supersedes AUDIO-009's historical as-of statement that Build 0472/counter 472 were current. That
statement was accurate for its own report date, not for this audit.

## 3. Method and tool reuse

I read `RULES.md`, AUDIO-008, AUDIO-009, the AUDIO-008 independent harness/results/log, every
AUDIO-009 source/data path named in its report, and the current OPEN-039 record. I reused
`analysis/audio/verification/audio008_independent_audit.py` for independent raw Z80 ROM, YM-register CSV,
and VGM parsing. I did not import the AUDIO-009 analyzers to establish those facts.

The new harness exists because the 37-test suite does not test a plausible forged approval, numeric
revision ordering, revision retrieval, concurrent saves, write-boundary interruption, or restart
reconciliation. It uses real loopback HTTP requests, redirects `PROF_DIR` to a temporary directory, and
injects deterministic write failures only in that temporary store. It leaves no server running.

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/audio_composer/verify_audio_composer.py
PYTHONDONTWRITEBYTECODE=1 python3 analysis/audio/verification/audio010_independent_regression.py \
  --output analysis/audio/verification/audio010_results.json
```

Evidence:

- `analysis/audio/verification/audio010_audio009_suite_log.txt` — 37 passed, 0 failed.
- `analysis/audio/verification/audio010_test_log.txt` — 33 passed, 7 failed.
- `analysis/audio/verification/audio010_results.json` — structured observations and before/after hashes.
- `analysis/audio/verification/audio010_independent_regression.py` — reproducible audit harness.

The prior implementation is not independently addressable as a clean Git parent: commit
`4b3d711ed57f0022ae5d69a1a8eb4855bcc39974` bundled AUDIO-008/AUDIO-009 material with unrelated Build
0467 work and introduced several already-existing uncommitted audio artifacts. AUDIO-008's durable HTTP
results supply the pre-correction reproduction. This audit does not pretend the whole commit is an
AUDIO-009-only diff.

## 4. Correction verification matrix

| Original defect | Actual AUDIO-009 correction | Independent test | Result | Evidence | Remaining severity | Recommended action |
|---|---|---|---|---|---|---|
| GET traversal disclosed arbitrary JSON | strict ID allowlist plus realpath containment | plain and encoded traversal over HTTP | PASS | AUDIO-010 tests 1–2; `server.py:45-61,407-414` | none | none |
| Absolute/separator/invalid profile identifiers accepted | same containment helper | absolute path, `/`, `\\`, invalid-character requests | PASS | AUDIO-010 tests 3–6 | none | none |
| Symlink could escape profile root | realpath must equal expected in-root path | in-root `escape.json` symlink to external temp file | PASS | AUDIO-010 test 7 | none | none |
| Invalid/error routing could persist | server recomputes errors and rejects with 403 | unknown destination and FM6 requests, file-existence check | PASS | AUDIO-010 tests 8–9; `server.py:444-455` | none | none |
| Client could fabricate approval | errors rejected; empty approved route downgraded | plausible valid FM1 route with client `approval_status:"approved"` | **FAIL** | HTTP 200; reload remained `approved`; `server.py:466-483` | **HIGH** | approval must be a server-authorized transition, not an editable save field |
| Client could forge arcade evidence | evidence rebuilt from server analysis | forged command/provenance with known Scene 1 track | PASS | AUDIO-010 test 11; `server.py:457-480` | none | none |
| Baseline mutable | explicit POST rejection | POST `baseline_current`, hash before/after | PASS | AUDIO-010 test 12; `server.py:436-438` | none | none |
| Same-ID save destroyed history | revision snapshots plus atomic replacement | 12 sequential saves and r1/r12 content checks | PASS for clean sequential use | AUDIO-010 test 15 | none in sequential case | preserve behavior |
| Revision listing/retrieval incomplete | `/api/revisions` list only | 12 saves, list, then GET revision 1 | **PARTIAL** | list is `1,10,11,12,2…`; `/api/revision` is 404 | **MEDIUM** | numeric order and safe retrieval endpoint with validated revision ID |
| Atomic files described as crash-safe revisions | snapshot/current/manifest written separately | concurrent HTTP saves | **FAIL** | eight 200 responses yielded only 3 snapshots/current revision 3 instead of 9 | **HIGH** | per-profile serialization and collision-proof revision allocation |
| Interrupted writes should be recoverable | snapshot written first with `os.replace()` | inject failure before current; retry | **FAIL** | retry overwrote r1 and created no r2 | **HIGH** | never replace an existing revision; recover/advance from snapshots |
| Manifest should remain consistent | manifest atomically replaced last | inject manifest failure; restart server | **FAIL** | current revision 2, manifest revision 1 after restart | **HIGH** | journal/transaction or deterministic startup reconciliation |
| v1 migration might lose user fields | backfill v2 and preserve unknowns | load/save v1 notes, approved route, unknown field | PASS | AUDIO-010 test 23 | none | none |
| False Genesis PSG per-channel stereo | mono/center, `stereo_per_channel:false` | real `/api/psg_model` | PASS | AUDIO-010 test 25; `server.py:119-123` | none | none |
| PSG channel/divider model incomplete | 3 tones, 1 noise, 10-bit divider | inspect endpoint fields | PASS | AUDIO-010 tests 24–25 | none | none |
| Tone3/noise warning unconditional | explicit selector; warning only for selector 3 | `/api/validate` fixed vs tone3-clocked | PASS | AUDIO-010 tests 26, 28; `server.py:294,347-352` | none | none |
| Noise taps/divider-zero overclaim | both labeled unresolved | inspect endpoint text | PASS | AUDIO-010 test 27 | none | none |
| Composer could impose routing | empty defaults retained | fresh-profile GET | PASS | AUDIO-010 test 29 | none | none |
| `$82` parsed as count 130 | lead `>=0x12` classified as channel/control ID | independent ROM-table traversal plus generated JSON comparison | PASS | commands 03/0A/0D/21/26 all lead 82; AUDIO-010 test 30 | none | none |
| Ordinary counted descriptor could regress | grammar retains lead `<0x12` count | command 00 independently parses 17 two-byte records; generated JSON agrees | PASS | AUDIO-010 test 31 | none | none |
| Zero-mask YM writes inflated key-ons | explicit key-off branch and separate metrics | independent parse of all nine CSVs | PASS | no generated-count mismatch; Scene 1 = 6; AUDIO-010 test 32 | none | none |
| Occupancy/heuristic presented as identity | labels separated; identity remains unresolved | source/generated-field inspection | PASS | `analyze_ym2151_captures.py:30-32,85-103` | none | none |
| VGM `$4F` advanced 3 bytes | advances 2 bytes | independent synthetic stream walks 4F,50,66 | PASS | AUDIO-010 test 36; `vgm_genesis_analysis.py:283` | none | none |
| Stream DAC hidden as zero writes | direct writes and stream starts separated | independent VGM parse vs generated JSON | PASS | 4 blocks, 398 starts, `active:true`; AUDIO-010 tests 33,35 | none | none |
| Patch denominator mislabeled 141 | label corrected to actual 174 | independent VGM patch-state snapshots | PASS | 174; AUDIO-010 test 34 | none | none |
| Lawrence additive/substitution claim unsupported | report qualifies it unverified | source/report inspection; no note alignment claimed | PASS | AUDIO-009 report §2/§8; AUDIO-003 still absent | none | preserve qualification |
| C artifact called semantic decompilation | explicitly declaration index with zero bodies | declaration/body scan | PASS | 12 declarations, zero bodies; AUDIO-010 test 37 | none | none |
| Coverage `COMPLETE` overstated semantics | evidence vocabulary; no semantic-complete rows | CSV scan | PASS | 0 `SEMANTIC_C_COMPLETE` rows; AUDIO-010 test 38 | none | none |
| TC0140SYT/latch/$1B/$82 notes wrong or absent | PC060HA; B=address/C=start/D=stop; bank effect and grammar documented | C/CSV token and meaning inspection | PASS | AUDIO-010 test 39 | none | none |
| Overbroad `.js` fallback | exact static routes only | unknown JS over HTTP | PASS | 404; AUDIO-010 test 13 | none | none |

## 5. Profile security verdict

**PARTIAL / NOT ACCEPTABLE AS AN APPROVAL SYSTEM.** Traversal, symlink escape, invalid routes, FM6,
baseline immutability, server-derived evidence, malformed JSON, status codes, and static routing behave
correctly. The approval boundary does not: `approval_status` is copied directly from the request at
`server.py:466-470`, and only the special case of an empty approved route is downgraded. A structurally
valid route is therefore enough for an arbitrary client to mark itself approved.

The existing suite's two “fabricated approval” tests do not test this boundary. They exercise an invalid
FM6 route and an empty route, both rejected/downgraded for reasons independent of approval authority.

## 6. Versioning and crash-safety verdict

**FAIL.** `atomic_write_json()` makes one file replacement atomic. It does not make the three-file
operation atomic, reserve revision numbers, serialize requests, prevent replacing an existing revision,
or reconcile state after restart.

Observed through real HTTP in isolated storage:

- Eight concurrent saves all returned 200 but collapsed into only two additional snapshot numbers.
- Failure after writing r1 but before current left r1 orphaned; retry recomputed revision 1 and replaced
  that immutable file with different content.
- Failure after snapshot/current but before manifest left current at revision 2 and manifest at revision
  1; restarting the server did not reconcile them.
- Double-digit revisions list lexicographically.
- No revision-content retrieval endpoint exists, so valid retrieval and invalid revision-ID handling are
  both absent (404).

## 7. PSG verdict

**PASS.** The endpoint models three 10-bit-divider tone channels and one noise channel, exposes fixed
selectors 0/1/2 plus tone3-clocked selector 3, warns about tone3 dependency only in mode 3, reports the
Genesis PSG as mono, labels taps/period and divider-zero target behavior unresolved, and starts new
profiles without automatic proposals or approved routing.

## 8. Original-data/analyzer verdict

**PASS for the targeted AUDIO-009 corrections.** The independent parsers reproduce:

- `$82` at exactly commands `$03,$0A,$0D,$21,$26` as the special channel/control lead; ordinary counted
  descriptors still parse correctly.
- All nine generated keyed-channel totals; Scene 1 is 6.
- Lawrence VGM's four PCM blocks (4,818/4,814/4,817/4,813 bytes), 398 stream starts, and 174 distinct
  patch-state snapshots.
- Correct two-byte `$4F` behavior in a minimal independent stream.

The original inputs remained byte-identical during the run. Important hashes include:

- `build/regions/audiocpu.bin`: `db0e2d4954bcb0d558f6b6dd194badccdeb29c62282051ff47b687548701e478`
- `build/regions/adpcm.bin`: `65a82d3669a2d52b00e019dedef858e3778ecd1e8526326beaf0c100df29311f`
- Lawrence VGM: `b786794eedb319c71716bb481e0836647ecf002de7bb5bd8761d173fa948580d`

No additive-versus-substitution conclusion is established. AUDIO-003 sequence/instrument/sample/timing
work remains undone.

## 9. Z80 C and coverage verdict

**PASS.** `rastan_z80_sound_driver.c` is prominently a declaration index, contains 12 declarations and
zero bodies, and disclaims semantic equivalence. The coverage CSV has zero rows labeled
`SEMANTIC_C_COMPLETE`. PC060HA, the ADPCM B/C/D latch roles, YM `$1B` bank-selection side effect, and the
`$82` descriptor grammar are present. This remains an index, not a completed Z80-to-C translation.

## 10. Scope and regression protection

AUDIO-010 changed only the audit report, audit harness/results/logs, OPEN-039, and AGENTS_LOG. It did not
touch `apps/rastan-direct/src`, the production Z80 driver, remap specs, accepted ROMs/tags, the counter,
original ROM/capture/VGM inputs, `tools/graphics_editor`, or real decision profiles.

AUDIO-009's own report enumerates its task files. Its audio-specific changed-file set was:

- `tools/audio_composer/server.py`
- `tools/audio_composer/app.js`
- `tools/audio_composer/verify_audio_composer.py`
- `tools/audio/analyze_ym2151_captures.py`
- `tools/audio/vgm_genesis_analysis.py`
- `tools/audio/gen_music_command_inventory.py`
- `build/audio/ym2151_track_reports/*.json`
- `build/audio/vgm_analysis/LM-Main Stage Theme (1).json`
- `build/audio/music_command_inventory.json`
- `analysis/decompilation/c/z80/rastan_z80_sound_driver.c`
- `analysis/decompilation/c/z80/z80_function_coverage.csv`
- `analysis/audio/decision_profiles/baseline_current.json`
- `analysis/audio/decision_profiles/profile_manifest.json`
- correction notices in the AUDIO/RG reports named by AUDIO-009
- `docs/design/Andy_AUDIO009_audio_foundation_corrections.md`, `AGENTS_LOG.md`, and `OPEN_ISSUES.md`

The monolithic commit also contains unrelated project files, so those are not attributed to AUDIO-009.

## 11. Remaining HIGH and MEDIUM issues

### HIGH

1. Client-authored valid routing can self-assert approval.
2. Concurrent saves lose revision history despite all requests returning success.
3. Interrupted save retry can replace an existing “immutable” snapshot.
4. Failed manifest write remains inconsistent after restart.

### MEDIUM

1. Revision order is lexicographic rather than numeric.
2. Revision content has no retrieval API; invalid revision identifiers therefore have no defined safe
   endpoint behavior.

## 12. Minimum correction before proceeding

Bound the next work to the Composer profile subsystem:

1. Remove `approval_status` from generic editable fields. Add an explicit server-controlled approval
   transition which validates the saved revision and cannot be asserted by arbitrary save JSON.
2. Serialize saves per profile (or use an equivalent storage transaction), allocate a unique next
   revision without races, and create revision files with no-replace semantics.
3. Add a small journal/commit marker or deterministic startup reconciliation so snapshot, current, and
   manifest converge after every tested interruption boundary.
4. List revisions numerically and add safe immutable revision retrieval with strict integer validation.
5. Extend the official suite with the seven AUDIO-010 regressions before claiming correction.

After those bounded fixes pass both suites, AUDIO-009 may be re-audited. Do **not** proceed to AUDIO-003
on the basis of the current correction set; OPEN-039 remains open.

## 13. Exact AUDIO-010 changed files

- `docs/design/Cody_AUDIO010_audio009_regression_verification.md`
- `analysis/audio/verification/audio010_independent_regression.py`
- `analysis/audio/verification/audio010_results.json`
- `analysis/audio/verification/audio010_test_log.txt`
- `analysis/audio/verification/audio010_audio009_suite_log.txt`
- `OPEN_ISSUES.md`
- `AGENTS_LOG.md`

**AUDIO-010 final classification: AUDIO-009 REJECTED.**
