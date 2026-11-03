# Andy/Fable — Build 0192 Bounded Cycle Optimization Pass (Build 0193)

**Date:** 2026-07-16
**Type:** Measured cycle-reduction audit + one bounded candidate. Files audited: pc090oj_hooks.s, pc090oj_assets.s, vdp_comm.s.
**Baseline:** Build 0192 `42f0b662…`, 26.554 ms/service (1.59 frames), rate 0.588.
**Produced:** **Build 0193** `dist/rastan-direct/rastan_direct_video_test_build_0193.bin`, SHA `ee3d236e30db81ba490ce2b42d2e59b93bdfef702b3fe940f2b73dd85bff31de`, size 1,582,876, counter 193, GATE_PASS (deterministic; metadata regen byte-identical).

## Primary classification — **A** (safe micro-optimization in PC090OJ prep path, proven and built), with **E** (VBlank ordering) ranked as the recommended next candidate.

## Hotspot audit (measured, Build 0192, gameplay)
| Routine | Bucket | Per-service cost | Runs | Notes |
|---|---|---:|---|---|
| hook_target_41f5e → block_sprites_41f5e → 22× family_apply_record (pc090oj_hooks.s) | arcade VINT/main-loop | **6.541 ms** | every service | 22 unconditional inline syncs (decode+SAT under 15-reg movem + SR mask) — 42% of the 15.5 ms arcade bucket |
| .Lpc090oj_mark_changed_candidates_since_shadow | prepare | **4.171 ms** | every dirty service (= every service; family set mirror_dirty) | 256-record × 8-byte compare |
| .Lpc090oj_process_candidates (decode/represent/SAT/worklist) | prepare | **4.094 ms** | every dirty service | re-syncs the same family records a second time (~8 SAT writes/service) |
| .Lpc090oj_update_mirror_shadow | prepare | **1.999 ms** | after every process | full 0x800 copy |
| vdp_commit_sprites_vram | display-off commit | 0.273 ms | every service | already cheap (0178/0180/0192) |
| everything else in vdp_comm.s | commit/post | ≤0.163 ms each | dirty-gated | not worth touching |
| pc090oj_assets.s | — | none | — | pure incbin data; no hot CPU path; no change |

## vdp_prepare_sprites sub-breakdown (measured via shadow/SAT data taps)
| Sub-bucket | 0192 ms | % of prepare | 0193 ms |
|---|---:|---:|---:|
| gate (dirty checks) | 0.045 | 0.4% | 0.045 |
| mirror scan (256-rec compare) | 4.171 | 40.3% | 4.164 |
| process_candidates (decode+represent+SAT+worklist) | 4.094 | 39.6% | 3.833 |
| update_mirror_shadow (0x800 copy) | 1.999 | 19.3% | 1.999 |
| tail | 0.043 | 0.4% | 0.043 |
| SAT writes/service | 8.0 | — | 4.0 |
(Record decode vs SAT assembly vs residency inside "process" not separable without internal-label taps; the whole bucket is bounded by the numbers above.)

## Arcade VINT/main-loop attribution — classification **B/C** (Genesis helper work inside arcade flow)
The 15.523 ms bucket contained **6.541 ms of Genesis helper work at one site**: arcade PC 0x041F5E → runtime jsr @0x4215E → `genesistan_pc090oj_hook_target_41f5e` (pc090oj_hooks.s), 1 call/service, 22 inline record syncs. The remaining ~9 ms is original arcade game logic + the other (cheap, dirty-gated) hooks — original arcade code untouched per rules.

## The double-sync defect (root of the candidate)
`family_apply_record` synced every record inline (arcade bucket) AND set `mirror_dirty`, whose VBlank shadow-scan re-marked the same records so `process_candidates` synced them a SECOND time (prepare bucket) — plus a 256-record scan + 0x800 shadow copy triggered every service. The inline syncs were also **unconditional**, running even for value-identical tuples.

## Candidate built (Build 0193): family_apply deferred single-sync + unchanged-tuple fast path
`.Lpc090oj_family_apply_record` now: (1) compares the incoming 4-word tuple against the mirror and **exits early when identical** (the Build 0177 shadow-compare invariant: identical bytes ⇒ identical decoded output); (2) for changed tuples, writes the mirror and **sets the record candidate like every other producer** (emit_slot/mirror_write/3ad44 all do this) instead of syncing inline + clearing the candidate. The proven Build 0157/0177 VBlank path (mark→process) then converts the record **exactly once**, before the same service's sprite commit — so the VRAM-visible SAT/tile state per service is unchanged. SR mask and full movem retained (atomicity + caller-contract safety). Build 0181 OOB guard retained.

**Equivalence argument:** commits consume staged SAT/worklist only during `_vblank_service`, after `vdp_prepare_sprites`; whether a record was staged inline mid-frame or at prepare, the committed snapshot is identical. Order of representation inserts converges to the same record-ordered chain. Multiple writes between services collapse to one sync (same final state).

## Before/after (measured; same harness, gameplay ≥F560)
| Metric | Build 0192 | Build 0193 |
|---|---:|---:|
| total VINT service | 26.554 ms (1.59 fr) | **21.669 ms (1.30 fr)** |
| VINT-service rate | 0.588 (~35 Hz) | **0.769 (~46 Hz)** |
| arcade VINT + main loop | 15.523 ms | **10.989 ms** |
| — of which 41f5e hook | 6.541 ms | **1.762 ms** |
| vdp_prepare_sprites | 10.299 ms | 10.035 ms |
| display-off window | 0.401 ms | **0.312 ms** |
| SAT writes/service in prepare | 8 | 4 |
| represented / SAT chain / player slots | 15 / 15 / 6 | 17 / 17 / 9 (game-moment variance at faster rate; not corruption) |
| Rastan / title / READY / BG / FG / palette | correct | **correct (screenshots states/traces/fable0192/snap93/)** |

## Rejected / deferred optimizations (ranked)
1. **[deferred — recommended next] VBlank reorder (commit-first):** commit window is only 0.31 ms; committing the previous service's prepared output at VINT entry puts display-off/on entirely inside VBlank, killing the black band even while over budget. One-frame-late presentation is consistent (SAT+tiles defer together; staged buffers already act as the buffer — no new double-buffering). Needs its own state-causality validation pass; not built (one-clear-candidate discipline).
2. **[deferred] Eliminate the 256-record scan + 0x800 copy (6.2 ms):** all five mirror writers now set candidates directly, making the scan theoretically redundant — but it is the safety net for any future writer; removing it is an architectural invariant change, not a micro-optimization. Candidate for a later pass with a debug-gated assertion.
3. **[rejected] movem trimming in family/emit paths (~0.7 ms):** register-contract risk across producer loops outweighs the gain.
4. **[rejected] pc090oj_assets.s layout changes:** pure incbin data, no measured CPU cost.
5. **[rejected] removing diagnostic counters:** single addq each, negligible; not worth debug-flag machinery.

## VBlank ordering answers
1. Would commit-at-VBlank-entry eliminate the band even over budget? **Yes** (0.31 ms window fits VBlank ~40×over).
2. Commit current prepared output first, then prepare next? **Yes — structurally supported today.**
3. One-frame-late presentation safe? **Consistent by construction (SAT+tiles defer as a pair); needs a validation pass.**
4. Double-buffering needed? **No** — staged SAT/worklist already decouple produce/commit.
5. Higher value than instruction-level work? **For the black band specifically, yes — recommended next bounded candidate.**

## Structured metadata
Owner: `specs/rastan_direct_remap.json` → 0x041F5E `note` gained a Build 0193 clause (helper semantics change); regenerated into `rastan_direct_patch_manifest.json` + `address_map.json`; ROM SHA unchanged (deterministic).

## Not touched
Build 0192 suppression (41dae/45dfa gates intact), Build 0180 SAT gating, Build 0178 tile-DMA cache, Build 0175 palette route, 0171/0172 projections, mirror default 256, input/collision/enemies/sky/D00298/continue/Exodus.
