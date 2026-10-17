# Cody Build 0438 — Restore Accepted Build-0434 Production Implementation

Date: 2026-10-17  
Agent/task: Cody — preserve the complete post-0437 deferred state, then forward-rebaseline production to the accepted Build-0434 implementation  
Accepted gameplay baseline: Build 0434  
Produced candidate: Build 0438 (real-hardware acceptance pending Tighe)

## Result

The complete 0427–0437 working state was preserved on
`archive/deferred-hud-framing-0437`. The original full-state preservation commit is
`8b0d8659f5a62a70b11af0c92af0d57fee0e527b`; the final archive HEAD, which adds only the
secondary safety patch, is `5a886bb4cbd9e9b5f45bf1c5496d17d480201b83`.

Production was then reconstructed selectively from that preserved state. All accepted 0427–0434
player, sprite, background, and Build-0434 paired-row vertical work remains. The Build-0435 Mode-1
full-gameplay-HUD implementation and the Build-0436/0437 frontend/gameplay split-origin machinery
were removed from active production. Later reports, decompilation, verifiers, benchmark history,
ROMs, traces, and research remain available.

## Preservation

- Authoritative recovery source: archive branch and commits above.
- Secondary inspectable artifact:
  `docs/design/deferred_hud_framing_preserved_state.patch`.
- Patch meaning: exact binary Git diff from actual committed Build-0426 base
  `9982f7cd70581d1e1196cc02f33831c3af2be006` to the original complete deferred-state commit
  `8b0d8659f5a62a70b11af0c92af0d57fee0e527b`; it is not mislabeled as a true 0434-to-0437 commit
  diff because no Build-0434 commit existed.
- Patch SHA-256: `ce1c69d896fb7780cf2af3fe5c0b1ec8ff5a6b205693832bda13ecb89c4b4033`.
- Reverse `git apply --check` validation: PASS.
- Canonical and `_full_hud` ROMs for Builds 0434–0437, benchmark/isolation evidence, and all
  post-0437 research were verified in the archive commit.

## Production reconstruction

Changed production inputs:

- `apps/rastan-direct/src/pc090oj_hooks.s`: restored the common
  `PC090OJ_TO_GENESIS_Y_OFFSET=-8` finalizer, the nine-entry HUD queue, accepted Mode-2-only HUD
  palette/residency handling, and the direct gameplay dispatch; removed the deferred Mode-1 full HUD
  projector/status reservation and split-origin paths.
- `apps/rastan-direct/src/vdp_comm.s`: restored the fixed
  `VDP_DISPLAY_ORIGIN_Y_BIAS=8` and the original `ADDQ.W` Plane-A/Plane-B VSRAM realization.
- `apps/rastan-direct/Makefile`: retained the pre-existing six-ROM comparison family and all
  0427–0434 build work, removed only the 0436/0437 origin variables/config receipts, and restored
  the pre-0435 Mode-1 coverage expectation of `-0x1000`.

Intentionally retained production source includes the accepted Build-0434 changes in
`tilemap_hooks.s` and `fg_tile_cache.s`, all accepted 0427–0433 sprite/player/background work, and
the earlier reduced Mode-2 P1 HUD. `native_active_y_origin` remains absent.

Semantic subsystem changed: production configuration and native sprite/scroll presentation were
returned to the already-accepted Build-0434 behavior. No new PC080SN/PC090OJ semantic cut was
introduced. No arcade chip tail was newly removed; the already-native semantic cuts and retired
chip tails remain unchanged. No legacy dependency was restored.

## Static proof

- Forbidden deferred symbols/paths absent: both split-origin constants, `native_active_y_origin`,
  fixed-HUD origin override, Mode-1 full-HUD projector, Mode-1 status-valid state, and widened HUD
  queue.
- Accepted paths present: sprite Y immediate `-8`; Plane-A/Plane-B VSRAM `ADDQ.W #8`; Mode-2 P1
  HUD; Build-0434 paired-row background producer and verifier.
- Canonical Build 0438 versus accepted Build 0434 differs at exactly two bytes: ROM offset
  `0x18F` (header checksum) and `0x2928DB` (`0434` to `0438` build string).
- Build 0438 `_full_hud` versus preserved Build 0434 `_full_hud` likewise differs at exactly those
  two bytes. This proves the reconstructed executable/payload behavior is otherwise byte-identical.
- Opcode replacement sites: 231. Canonical expected Genesis-byte coverage: `0x292EB8`.

## Build and validation

- Counter: 437 -> 438. Builds 0435–0437 remain consumed.
- Canonical ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0438.bin`
- Size: 2,698,936 bytes.
- SHA-256: `a262fbb4cab529c1b23b3e85e4b87d927587bf2507b492611598d6ba3057a0dc`.
- Canonical gate: PASS.
- Gameplay-entry gate: PASS; address/bus/illegal/crash-handler counts all zero.
- Known phase-epoch result: the same preserved warning at target record/epoch 0 documented for
  accepted Builds 0433/0434; the ROM remained numbered per project policy.
- Complete canonical/`_d`/`_s`/`_do`/`_c`/`_full_hud` family verification: PASS.
- Standard fixed 30-second GENESIS NTSC MAME trace: PASS, 1,798 frames, 46,949 live VDP-port
  writes; evidence:
  `states/traces/rastan_direct_video_test_build_0438_mame_30s_20261017_102702/`.
- Existing unchanged deterministic GENESIS NTSC MAME rope benchmark: 803, 803, 803 frames;
  deterministic YES; median 13,400.588 ms. Evidence:
  `states/traces/build0438_rope_attach_benchmark/`.
- Original arcade MAME, BlastEm, Exodus, and real hardware were not run in this task.

Existing project tools reused: the Makefile-owned build/gates/fixed trace,
`tools/mame/run_rope_attach_performance_benchmark.sh`, its existing Lua route and summarizer,
generated manifests/address map, Git branch/commit/diff/apply verification, and the preserved
Build-0434 ROM. New tracing/debugging/gameplay tooling created: none. Why necessary: not applicable.

## Regressions and limitations

Automated checks cover boot, canonical policy, gameplay entry, static graphics contracts, family
configuration isolation, the fixed trace, and the deterministic rope route. The target 803-frame
accepted-baseline result is restored. No horizontal-scrolling audit, HUD/framing continuation,
Phase D, or Phase E work was started.

The build is a candidate, not an accepted baseline. Real-Genesis behavior and presentation remain
outside automated proof.

## USER MUST VERIFY

On real Genesis hardware, Tighe should verify that Build 0438 matches accepted Build 0434 during
normal Round-1 play: player/rope control, vertical and horizontal scrolling, background rendering,
reduced 1UP/current-score HUD, and absence of the deferred full upper-HUD/framing behavior. Also
confirm previously accepted 0427–0434 sprite, enemy, death/drop, and background behavior remains
intact.

STOP status: Build 0438 reconstructed, mechanically validated, benchmarked, and ready for Tighe's
real-hardware acceptance. No Build 0439 work may begin until this exact candidate commit's acceptance
status is resolved and, if accepted, recorded as the production baseline.
