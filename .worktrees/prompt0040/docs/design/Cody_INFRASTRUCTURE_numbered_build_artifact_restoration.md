# Cody — INFRASTRUCTURE Numbered Build Artifact Restoration

**Date:** 2026-06-19
**Type:** Infrastructure
**Scope:** Restore numbered artifact convention for the OPEN-016 Part 2 ROM. No source/spec/tool/Makefile changes. No build. No ROM byte changes beyond copying the existing ROM to the numbered artifact path.

## Phase 0

Classification: **INFRASTRUCTURE**. No KNOWN_FINDINGS entries directly apply; KF-028 is context only because this restores the artifact path for the OPEN-016 Part 2 ROM. No HIGH-hazard finding is extended. No deferred appendix entry is relevant. OPEN-016 is context only; OPEN-001 and OPEN-015 are deferred context. No contradiction detected.

## Prior Convention

The rastan-direct Makefile already supports numbered artifacts. Target `make -C apps/rastan-direct release` builds `apps/rastan-direct/dist/rastan_direct_video_test.bin`, runs the canonical gate, increments `build/rastan-direct/build_counter.txt`, and copies the ROM to `dist/rastan-direct/rastan_direct_video_test_build_%04d.bin`.

Relevant Makefile block: `apps/rastan-direct/Makefile` lines 140-163.

## Drift Cause

Root cause: procedural workflow drift. OPEN-016 Part 2 used the no-runtime/manual build path and produced the rolling ROM, but skipped the Makefile numbered-copy/counter block. The Makefile workflow is not broken and no infrastructure edit is required.

## Restoration

- Source rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Expected SHA: `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`
- Authoritative prior counter: `90`
- Assigned build number: `0091`
- Restored numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0091.bin`
- Restored artifact SHA: `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`
- Byte-identical to rolling ROM: YES
- Counter after restoration: `91`
- Rebuild performed: NO

## OPEN-016 Part 1 Status

OPEN-016 Part 1 SHA `c9fab1b47ccd3dd7dff76dbd4fe8776521287697a9e6824917a1b7a10131b390` was not found in workspace `.bin` artifacts. It was not restored because this task forbids unnecessary rebuilds and no byte-identical source artifact remains to copy.

## Going Forward

Use `make -C apps/rastan-direct release` for ROM-producing builds that should emit numbered artifacts. No extra flag is required. If a future task intentionally uses a manual no-runtime path, it must still perform the same post-gate numbered-copy/counter step or explicitly document why no runtime-testable numbered artifact is produced.

## KNOWN_FINDINGS Impact

Option A — No new finding to index. This is INFRASTRUCTURE work only.
