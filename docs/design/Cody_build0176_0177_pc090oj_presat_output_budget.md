# Cody - Build 0176/0177 PC090OJ Pre-SAT Output Budget

**Date:** 2026-07-15
**Type:** Analysis-first implementation + numbered build + runtime validation
**Baseline accepted build:** Build 0175, `dist/rastan-direct/rastan_direct_video_test_build_0175.bin`, SHA256 `555c4d6c013df77fe28ce1e44fc27f039b609a1e6ad014e858b3fb5590db947f`, size `1,582,580`, counter `175`
**Interrupted diagnostic build:** Build 0176, `dist/rastan-direct/rastan_direct_video_test_build_0176.bin`, SHA256 `e7ff34fa67f4d0dd9f15fa180d69e870a41dc0923a219cb65846068d6cf09d52`, size `1,582,700`, counter `176`
**Produced candidate build:** Build 0177, `dist/rastan-direct/rastan_direct_video_test_build_0177.bin`, SHA256 `b0db30f17a7d0d3453bf3a6c2bca23bd16694e72b7c050a874d3afb3fe921370`, size `1,582,740`, counter `177`

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (BG/FG staging and VBlank commit), KF-032 (raw PC080SN/PC090OJ writes route through staging), KF-038 (long PC080SN rows/tall representation), KF-043/KF-046 (gameplay palette and sprite-bank carrier context), OPEN-017 (active gameplay/hardware/timing thread), OPEN-024 (PC090OJ sprite subsystem incomplete), OPEN-001 (graphics context), and OPEN-015 (crash-handler caution, context only). Rediscovery-hazard findings touched: PC090OJ retained identity and VBlank ownership context; no contradiction detected.

Architecture compliance: **CONFIRMED**. Arcade code remains the program; Genesis-side code remains helper/staging/VDP service code. This task does not add a second sprite renderer, hardcode sprites/enemies, alter collision/input/player state, or drop arcade PC090OJ mirror records.

## Andy Build 0176 Evidence Preserved

- Build 0175 effective VINT/display service rate: `DISPLAY_OFF=481 / 1500` frames = `0.321/frame` (~19 Hz).
- Build 0175 timing: prep entry to display-off about `35.1 ms / 2.11 frames`; display-off to display-on about `6.24 ms / 0.37 frames`; post about `0.23 ms`; arcade+main about `22.4 ms / 1.34 frames`.
- Build 0176 added PC090OJ mirror-shadow memoization and built as a diagnostic/candidate only.
- Build 0176 did not materially fix the timing: `DISPLAY_OFF=524 / 1500` = `0.349/frame`; `vdp_prepare_sprites` stayed about `35.7 ms / 2.14 frames`.
- Build 0176 conclusion preserved: mirror changes happen often enough between slow services that a dirty-frame full resweep remains too expensive, and final SAT limiting alone does not protect pre-SAT decode/representation/tile work.

## Current Path Audit

### Mirror and Candidate State

- Full PC090OJ mirror remains `pc090oj_object_ram` at `0x00FFA9D8`, `.space 0x800`: **256 records x 8 bytes**.
- Build 0176 mirror shadow remains `pc090oj_mirror_shadow` at `0x00FFB1D8`, `.space 0x800`.
- Candidate bitset is `pc090oj_candidate_bitset` at `0x00FFB9D8`, 256 bits.
- Candidate count is `pc090oj_candidate_count` at `0x00FFB9FE`.
- `pc090oj_mirror_dirty` remains a coarse producer-side flag at `0x00FFB9FC`.

### Before Build 0177

Build 0176 effectively did:

```text
mirror_dirty or bootstrap_pending
  -> .Lpc090oj_set_all_candidates
  -> all 256 candidate bits set
  -> .Lpc090oj_process_candidates
  -> decode / represent / tile-work for far more records than can be emitted
```

The 80-sprite budget was enforced later, primarily in `.Lpc090oj_activate_record` and SAT/tile-DMA bounds, so the expensive candidate processing still ran too broadly.

### Build 0177 Change

Build 0177 keeps the full mirror but changes dirty handling:

```text
bootstrap_pending
  -> full 256-candidate sweep

mirror_dirty
  -> compare pc090oj_object_ram against pc090oj_mirror_shadow
  -> set candidates only for changed 8-byte records
  -> process candidates
  -> snapshot processed mirror to shadow

clean + no candidates
  -> skip processing
```

Implemented in `apps/rastan-direct/src/pc090oj_hooks.s`:

- `.Lpc090oj_candidate_set_d0` increments `pc090oj_candidate_count` only when a bit transitions clear -> set.
- `.Lpc090oj_candidate_clear_d6` decrements `pc090oj_candidate_count` only when a set bit is cleared.
- `vdp_prepare_sprites` handles bootstrap separately from dirty-frame processing.
- `.Lpc090oj_mark_changed_candidates_since_shadow` compares all 256 mirror tuples and marks only changed records.
- `.Lpc090oj_update_mirror_shadow` snapshots the mirror after a real processing pass.
- `.Lpc090oj_set_all_candidates` now also sets `pc090oj_candidate_count=256` for bootstrap/global reevaluation.
- `.Lpc090oj_process_candidates` clears candidates through `.Lpc090oj_candidate_clear_d6`.

## Primary Technical Classification

**A - Per-record dirty tracking can replace full-mirror dirty resweep.**

Interpretation: **F is also the architectural rule**: full mirror tracking is required, but full expensive output preparation is not. Build 0177 proves the earliest safe cut is after full mirror preservation and before candidate decode/representation: derive candidates from changed mirror records instead of turning every dirty frame into a full 256-record resweep.

## Build 0176 Source Decision

Classification: **C - Replace with a better per-record dirty/cache/output-worklist approach.**

Build 0176's mirror shadow is retained as useful infrastructure, but its ineffective behavior (`dirty -> all 256 candidates`) is replaced. The interrupted diagnostic build remains preserved as evidence, not accepted.

## Build 0177 Artifact

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS** after one expected invariant correction. The first release invocation observed the mechanical coverage value `0x182694`; the canonical invariants were corrected in both verification tools. The successful release produced:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0177.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `b0db30f17a7d0d3453bf3a6c2bca23bd16694e72b7c050a874d3afb3fe921370`
- Size: `1,582,740`
- Counter: `177`
- Numbered/rolling `cmp`: byte-identical
- `opcode_replace` count: `151`
- `total_genesis_bytes_covered`: `0x182694`

## Runtime Validation

Evidence path: `states/traces/build0177_presat_output_budget_20260715_222043/`

### Service Timing

| Build | DISPLAY_OFF / 1500 | Rate | Prep entry -> display-off |
|---|---:|---:|---:|
| 0175 | `481` | `0.321/frame` | `~35.1 ms / 2.11 frames` |
| 0176 | `524` | `0.349/frame` | `~35.7 ms / 2.14 frames` |
| 0177 | `703` | `0.469/frame` | `12.039 ms / 0.72 frames` |

Build 0177 section timing:

- VINT entry hits: `420`
- Arcade VBlank hits: `421`
- Complete services measured: `419`
- Prep (`_vblank_service` entry -> display-off): `12.129 ms / 0.73 frames`
- Commit (display-off -> display-on): `2.711 ms / 0.16 frames`
- Post (display-on -> arcade VBlank): `0.226 ms / 0.01 frames`
- Arcade VBlank + main until next entry: `22.226 ms / 1.33 frames`

### Candidate / Output Budget Evidence

At Build 0177 gameplay prepare entry, candidate pressure is small and bounded compared with the prior full 256 sweep:

- Candidate-flow averages (`F>=560`):
  - Entry: `candidate_count=14.00`, `candidate_bits=14.00`, `changed_tuples=6.04`
  - After mirror-diff marking: `candidate_count=20.04`, `candidate_bits=20.04`, `changed_tuples=6.04`
  - After processing: `candidate_count=0.00`, `candidate_bits=0.00`, `changed_tuples=0.00`
- Bootstrap full resweep in gameplay window: `set_all=0` hits.
- Sampled gameplay states:
  - `F=900`: `mirror_dirty=1`, `changed_tuples=6`, `mirror_coded=42`, `represented=24`, `active=24`, `tile_dma=18`, `enemy_records=14`, `enemy_represented=0`, `enemy_waiting=0`
  - `F=1300`: `mirror_dirty=1`, `changed_tuples=6`, `mirror_coded=42`, `represented=24`, `active=24`, `tile_dma=17`, `enemy_records=14`, `enemy_represented=0`, `enemy_waiting=0`

This proves `mirror_dirty` no longer marks all 256 records in steady gameplay. It derives about 6 changed records from the mirror shadow and combines them with about 14 live producer candidates, for about 20 candidates processed per service.

### Prompt Budget Questions

1. **Where is the 80-sprite cap enforced?**
   Before: late in `.Lpc090oj_activate_record` and final SAT/tile-DMA bounds. After: unchanged final cap remains in `.Lpc090oj_activate_record`; Build 0177 additionally prevents dirty-frame expansion to 256 pre-SAT candidates before decode/representation.
2. **How many PC090OJ mirror records are tracked?**
   `256` records x `8` bytes are retained in `pc090oj_object_ram`.
3. **How many records are changed/dirty this frame?**
   Runtime samples: about `6` changed mirror tuples; entry candidates from live producers average `14`.
4. **How many records are scanned before the 80-sprite output budget is applied?**
   Mirror-diff compare scans all `256` lightweight tuples when `mirror_dirty` is set, but only ~`20` candidates enter the expensive decode/sync path. This replaces the Build 0176 full `256` candidate decode/resync behavior.
5. **How many records are decoded before the 80-sprite output budget is applied?**
   Candidate-flow proves about `20` candidates/service are processed. Dynamic execute taps counted decode-related helper entries but may over-count function-entry reads; the bounded candidate count is the reliable budget measure.
6. **How many records are represented before the 80-sprite output budget is applied?**
   The retained represented set is `24` in the gameplay samples; only changed/new candidates adjust it.
7. **How many records reach tile-sync / sprite VRAM work before the 80-sprite budget is applied?**
   Tile-DMA worklist count is `17..18` in steady gameplay samples, bounded by represented changed slots and still defensively capped at `80`.
8. **How many records are converted into SAT entries?**
   `represented_count=24`; `staged_sprite_active_count=24` in steady samples.
9. **Final VDP SAT sprite count?**
   Approximate active SAT output is `24` represented/used slots in the sampled gameplay state; final SAT DMA remains clamped to <= `80` slots.
10. **Does mirror_dirty still cause all 256 candidates to be marked?**
   **No.** Gameplay `set_all` hits were `0`; candidate-flow after mirror marking averaged `20.04`, not `256`.
11. **Are unchanged records re-decoded/re-represented?**
   Not by dirty-frame processing. Unchanged represented records retain SAT slot/tile residency unless they are also live producer candidates.
12. **Can unchanged represented records be retained safely?**
   Yes for this path: the represent/decode/SAT state is a function of the mirror tuple and stable global PC090OJ control state. Bootstrap/global-control paths still request full reevaluation.
13. **Can records outside the visible/output budget be tracked but not tile-synced?**
   Yes. The mirror keeps all records, waiting/represented bitsets track output eligibility, and tile-DMA worklist is only populated from selected/represented slot work.

## Enemy Sprite Thread

Classification: **B / H**.

- Arcade Build 0176 baseline showed enemy-like coded records by later Stage 1 frames.
- Build 0177 Genesis samples show `enemy_records=14` in the PC090OJ mirror, so this is not classification A (`never spawn`).
- Those enemy-code records are not represented and not waiting in the sampled state: `enemy_represented=0`, `enemy_waiting=0`.
- Current evidence supports: enemy records exist in the mirror but are not selected/represented by the current output eligibility path. It does **not** yet prove whether they are rejected by offscreen/visibility, blank/unmapped decode, priority starvation, or mismatched gameplay progress. Therefore the precise sub-boundary remains **H - more evidence needed**.

Do not treat Build 0177 as an enemy-rendering fix. No fake enemy rendering or forced visibility was implemented.

## Visual / Regression Status

This task performed headless MAME timing/counter validation only. It did **not** capture a new gameplay screenshot or prove the black-bar visual result. Therefore:

- FG palette/route from Build 0175 was not intentionally touched.
- BG/sky/mountain/foreground staging paths were not intentionally touched.
- Input/control, sky-reset, D00298, continue/game-over, collision, and Exodus loop were not touched.
- Visual acceptance and real Genesis/BlastEm behavior remain Tighe verification items.

## Recommended Next Step

Use Build 0177 as a performance candidate for manual visual/hardware testing. If slowdown/black-bar remains materially visible, the next bounded task should compare Build 0177 gameplay VINT timing with rendered-frame visual evidence, then separately trace why the 14 enemy-code mirror records are not represented (`decode_record` rejection reason / output eligibility), without changing input/collision or forcing enemies.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024, OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: real Genesis/hardware acceptance, visual black-bar confirmation, enemy output eligibility sub-boundary, input/control, sky-reset, D00298, continue/game-over, collision, Exodus loop.

## KNOWN_FINDINGS Impact

Option **B** - proposed/add new KF for the durable PC090OJ pre-SAT budget mechanism: final SAT cap alone is too late; dirty mirror frames must derive a bounded changed-record candidate set while preserving full mirror state.

## STOP

STOP triggered: **NO**. Build 0177 was produced and timing-validated. Visual acceptance remains pending.
