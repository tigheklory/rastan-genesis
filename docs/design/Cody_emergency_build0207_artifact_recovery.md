# Cody - Emergency Build 0207 Artifact Recovery and Ledger Correction

**Date:** 2026-07-19
**Type:** Infrastructure / artifact recovery / ledger correction
**Build context:** Build 0207 number consumed; artifact deleted/lost; Build 0208 is the next allowed ROM-producing build
**Scope:** Recovery and correction only. No source gameplay fix, no ROM rebuild, no ordinary Build 0207 or Build 0208 production.

## Phase 0

Classification: **INFRASTRUCTURE**. Required priors read: `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `CURRENT_STATE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, and `docs/design/Andy_opus_lizard_acceptance_recovery_build0207.md`.

Relevant priors:

- `RULES.md` Numbered ROM Artifact Preservation Rule: numbered builds are evidence; do not delete, overwrite, silently replace, or reuse consumed numbers.
- OPEN-002: build numbering and artifact identity must remain strictly sequential and unambiguous.
- KF-064/KF-065: lizard evidence context only; no gameplay mechanism was modified in this task.
- OPEN-017/OPEN-024: lizard/gameplay context only.

Contradiction of CONFIRMED/STRONG finding: **NONE**. The contradiction is in task/ledger history, not in curated hardware/gameplay findings.

Architecture compliance: **CONFIRMED**. No ROM, gameplay source, hardware translation source, or runtime behavior change was made.

## Recovery Trigger

Tighe reported that Build 0207 was produced/consumed and then deleted/lost. Therefore the previous Cody/Andy/Opus statements that Build 0207 was not produced are treated as false/superseded for build-number accounting.

Authoritative correction:

- Build number `0207` is **consumed**.
- `0207` must not be rebuilt over, reused, or reported as available.
- If a later ROM is produced, it must be Build `0208`.

## Evidence Artifacts

Recovery directory:

- `states/traces/build0207_artifact_recovery_20260719_114926/`

Files created in that directory:

- `build0207_location_search.tsv`
- `build0207_reference_search.txt`
- `rom_candidate_hashes.tsv`
- `recovery_audit_summary.md`

One recovery search command emitted `/bin/bash: line 16: 206: command not found` because a shell search pattern accidentally contained unescaped Markdown backticks around `206`. This was a quoting issue in the audit command, not a state mutation. The broader location/hash searches still completed and no Build 0207 ROM candidate was found.

## Recovery Search Result

No recoverable `dist/rastan-direct/rastan_direct_video_test_build_0207.bin` was located.

Current numbered ROM inventory around the incident:

```text
0201: dist/rastan-direct/rastan_direct_video_test_build_0201.bin
0203: dist/rastan-direct/rastan_direct_video_test_build_0203.bin
0204: dist/rastan-direct/rastan_direct_video_test_build_0204.bin
0205: dist/rastan-direct/rastan_direct_video_test_build_0205.bin
0206: dist/rastan-direct/rastan_direct_video_test_build_0206.bin
0207: missing / not recoverable from workspace search
```

Current rolling ROM:

```text
apps/rastan-direct/dist/rastan_direct_video_test.bin
SHA256 98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae
```

Build 0206 ROM:

```text
dist/rastan-direct/rastan_direct_video_test_build_0206.bin
SHA256 98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae
```

The rolling ROM is byte-identical to Build 0206, not a recoverable Build 0207 artifact.

## Sequence Reconstruction

Supported facts:

1. Prior accepted/rolling baseline before the contested 0207 work was Build 0206, SHA `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`.
2. Tighe reports that Build 0207 was produced/consumed.
3. The Build 0207 numbered artifact is no longer present in `dist/rastan-direct/` or app-local `dist/`.
4. Current rolling ROM hashes to Build 0206.
5. Before correction, `build/rastan-direct/build_counter.txt` had been restored to `206`, which would have made the next release reuse `0207`.
6. Prior documentation/log statements incorrectly reported Build 0207 as not produced and counter `206` as authoritative.
7. This task corrected counter semantics to consumed number `207`, making Build 0208 the next allowed ROM-producing build.

Not recoverable from available evidence:

- Exact Build 0207 SHA256.
- Exact Build 0207 size.
- Exact Build 0207 ROM bytes.
- Exact source/spec/tool diff used to produce Build 0207, if any, beyond currently dirty workspace context.

Because exact source/spec/config state is not recovered, deterministic reconstruction is **not permitted** in this task.

## Ledger / Counter Correction

Corrected files:

- `build/rastan-direct/build_counter.txt` now contains `207`.
- `build/rastan-direct/consumed_build_numbers.txt` now records `0207 CONSUMED_ARTIFACT_LOST`.
- `CURRENT_STATE.md` records Build 0207 as consumed/lost and Build 0208 as next.
- `OPEN_ISSUES.md` OPEN-002 records the incident and guard.
- `docs/design/Andy_opus_lizard_acceptance_recovery_build0207.md` now has an emergency correction section superseding its false Build 0207 numbering statements.
- `AGENTS_LOG.md` receives an append-only correction entry.

`KNOWN_FINDINGS.md` was not edited. This is artifact/process evidence, not a durable arcade/Genesis hardware behavior finding.

## Release Guard Added

`apps/rastan-direct/Makefile` now adds a narrow release guard:

- Reads a consumed-build ledger at `build/rastan-direct/consumed_build_numbers.txt`.
- Computes the highest seen consumed build from existing numbered ROMs plus the ledger.
- Fails release if `build_counter.txt` is behind that consumed build.
- Refuses to overwrite an existing numbered ROM artifact.
- Copies and verifies the numbered artifact before writing the advanced counter.

This specifically prevents silently reusing `0207`, overwriting an existing numbered ROM, or advancing the counter before the numbered artifact exists.

## Classification

Result: **produced, consumed, and artifact lost**.

Build 0207 is not recovered and was not reconstructed. Build 0208 is the next allowed build number.

## Open / Closed Issues Impact

- Open issues touched: OPEN-002; OPEN-017/OPEN-024 context only.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: lizard visual/combat fixes, palette route, Y alignment, damage/contact, all gameplay implementation work.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. No `KNOWN_FINDINGS.md` edit was made.

## STOP

STOP triggered: **YES (artifact not recoverable)**.

The recovery task cannot produce or reconstruct Build 0207 exactly. The safe state is corrected ledger/counter/tooling discipline: Build 0207 consumed/lost, next build Build 0208.
