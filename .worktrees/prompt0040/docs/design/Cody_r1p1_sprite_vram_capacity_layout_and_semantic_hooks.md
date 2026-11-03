# Cody R1/P1 Sprite VRAM Capacity, Layout, and Semantic-Hook Proof

## Scope and baseline

- Task classification: **EXTENDING**.
- Baseline: **Build 0356**; counter `356`; next valid Test Build `0357`.
- Production Sonic-style runtime implementation: **not authorized**.
- Test builds produced: **none**.
- Target: offline-generated direct sprite mapping plus static/DPLC packages; no runtime
  allocator, packing, eviction choice, or per-piece residency search.
- D00462 and Palette Tool expansion: unchanged/deferred.

## Phase 0

The authority files and requested prior reports were reviewed. This work extends KF-068
(native semantic cuts) and KF-074 (gameplay semantic lanes/final SAT ownership) and touches
OPEN-017 and OPEN-024 only as context. No CONFIRMED/STRONG prior was contradicted. The high
rediscovery hazard is treating captured vocabulary, a nominal address range, or one trace as
proof of physical coexistence. This report instead uses the zero-drop PC080SN package result,
the conservative sprite graph, the original-arcade trace corpus, and `address_map.json`.

## Authorities and generated proof

The deterministic analysis tool is
`tools/graphics_optimizer/prove_r1p1_vram_tail.py`. It writes
`analysis/graphics_optimizer/round1_phase1_corpus/generated/r1p1_vram_capacity.json`.
The JSON records SHA-256 hashes for every input, candidate assertions, exact VRAM ranges,
working-set counts, and the packing gate. Re-running the tool produces byte-identical output.

Principal inputs:

- `build/pc080sn_boundary/boundary_constants.inc`
- `build/pc080sn_boundary/boundary_report.json`
- `analysis/graphics_optimizer/round1_phase1/summary.json`
- `analysis/graphics_optimizer/round1_phase1/coexistence_graph.json`
- `analysis/graphics_optimizer/round1_phase1_corpus/full_capture/full_observations.csv`

The compiler report is zero-drop for both planes. Its five stable Plane A packages require
`282, 333, 639, 583, 639` patterns; the two transition packages require `394, 478`.
The maximum simultaneously installed package is therefore exactly `639` patterns. This is a
production package result, not the finer, uninstalled seven-epoch analysis estimate of `483`.

## Exact VRAM ownership

One Genesis pattern is 32 bytes. “May reuse” means reuse without changing the currently proven
zero-drop package semantics.

| Owner | Patterns | VRAM bytes | Bytes | Lifetime | Simultaneous with R1/P1 sprites | May reuse | Evidence |
|---|---:|---:|---:|---|---|---|---|
| Transparent pattern | 0 | `0x0000..0x001F` | 32 | Always | Yes | No | compiler convention |
| Fixed Plane B vocabulary part 1 | 1..662 | `0x0020..0x52DF` | 21,184 | R1/P1 | Yes | No | 854-pattern fixed B map |
| Plane A selected package arena | 663..1301 | `0x52E0..0xA2BF` | 20,448 | One stable/transition package | Yes | No | max package = 639, zero drop |
| Sprite physical envelope | 1302..1535 | `0xA2C0..0xBFFF` | 7,488 | R1/P1 | Yes | Yes, for sprites only | this proof |
| Plane B nametable | 1536..1663 | `0xC000..0xCFFF` | 4,096 | Always | Yes | No | VDP layout |
| Fixed Plane B vocabulary part 2 | 1664..1791 | `0xD000..0xDFFF` | 4,096 | R1/P1 | Yes | No | fixed B map |
| Plane A nametable | 1792..1919 | `0xE000..0xEFFF` | 4,096 | Always | Yes | No | VDP layout |
| Fixed Plane B vocabulary part 3 | 1920..1983 | `0xF000..0xF7FF` | 2,048 | R1/P1 | Yes | No | fixed B map |
| SAT | 1984..2015 | `0xF800..0xFBFF` | 1,024 | Always | Yes | No | VDP layout |
| HScroll | 2016..2047 | `0xFC00..0xFFFF` | 1,024 | Always | Yes | No | VDP layout |

The nominal Window region is not a free Window nametable during this gameplay configuration:
patterns 1920..1983 hold the third fixed Plane B vocabulary bank. Frontend patterns 1..63 are
reclaimed when gameplay begins, but are already consumed by the fixed Plane B allocation and do
not add another free tail.

### Address correction

Pattern 1339 starts at `1339 * 32 = 0xA760`, not `0xA6E0`. `0xA6E0` is pattern 1335.
The old report's current sprite start address was therefore four patterns (128 bytes) low.

## Free tail and capacity candidates

- Highest simultaneously required non-sprite pattern: **1301**.
- First safely reusable pattern: **1302**.
- Consecutive tail through pattern 1535: **234 patterns / 7,488 bytes**.
- Complete 16x16 sprite cells: **58**, with **2 spare patterns**.

| Cells | Patterns | Base | VRAM start | Extra below current base | Exact conflict | Verdict |
|---:|---:|---:|---:|---:|---|---|
| 49 | 196 | 1339 | `0xA760` | 0 | none | **PASS** |
| 52 | 208 | 1328 | `0xA600` | 11 | none after Plane A compaction | **PASS** |
| 55 | 220 | 1316 | `0xA480` | 23 | none after Plane A compaction | **PASS** |
| 61 | 244 | 1292 | `0xA180` | 47 | Plane A patterns 1292..1301 (10) | **FAIL** |
| 63 | 252 | 1284 | `0xA080` | 55 | Plane A patterns 1284..1301 (18) | **FAIL** |
| 64 | 256 | 1280 | `0xA000` | 59 | Plane A patterns 1280..1301 (22) | **FAIL** |

The exact physical maximum is 58 cells at pattern 1302 (`0xA2C0`), using patterns
1302..1533; patterns 1534..1535 remain as an unusable two-pattern fragment. Reaching 61, 63,
or 64 requires a separately proven Plane A reduction of 10, 18, or 22 patterns. No Plane A,
Plane B, or HUD semantic loss is authorized or used here.

## Working-set fidelity

The corrected Round-1 trace has 10,781 sampled frames: median 9 cells, P95 29, maximum 63.
It has 47 frames over 49 and 8 frames over 58. A 58-cell region therefore leaves a five-cell
shortfall at the observed peak. The original PC090OJ has no equivalent graphics-residency cap,
so dropping those identities is not proven arcade-equivalent. Pattern-residency fidelity is
**not closed** by this capacity result.

## Concrete physical packing result

The only concrete assignment currently justified is the physical envelope:

| Logical cells | Patterns | VRAM | Owner |
|---:|---:|---:|---|
| 0..57 | 1302..1533 | `0xA2C0..0xBFBF` | generated R1/P1 sprite layout, owners not yet assignable |
| n/a | 1534..1535 | `0xBFC0..0xBFFF` | two-pattern fragment |

An actor-by-actor assignment would be false precision. The current optimizer reports 23 legal
sprite classes, 4 resolved and 19 unresolved; the semantic domain is not fully enumerated or
resolved. Its conservative graph explicitly treats every unproven exclusion as coexistence and
sets `complete_sprite_clique=true`. Consequently:

- player, HUD/common, hurry-up bats, Lizardman, Four-Armed Insect, Chimera, Valkyrie,
  Large Bat, Flying Demon, projectiles, and effects have **no proven physical subrange yet**;
- no Flying Demon overlay or other alias is currently legal;
- multi-instance frame unions are not decoded for the material recurring families;
- safe aliases proven: **zero**.

This is the exact remaining blocker for C1-C5, not a request to infer owners from screenshots.

## DPLC model and budget

The selected target representation remains **FRAME-SPECIFIC GENERATED MAP**, because the proven
player chain selects a frame before expanding semantic pieces and the Flying Demon vocabulary
(`149` identities) is much larger than its observed maximum frame (`30` cells). Runtime should
index generated frame data and add predetermined bases; unchanged graphics frames should request
no graphics DMA.

That is an architecture selection, not a completed DPLC artifact:

- Player reservation: **unknown**, all legal frames/weapon combinations not extracted.
- Flying Demon reservation: observed upper frame bound **30 cells / 120 patterns / 3,840 bytes**;
  exact transition deltas remain unknown.
- Lizardman, Large Bat, Four-Armed Insect, Chimera, Valkyrie: **unknown** multi-instance unions.
- Future maximum aggregate DPLC/update and P95: **unknown** until all frame tables and concurrent
  transitions are decoded.
- Current Build 0356 worklist is separately bounded at 12 cell uploads, i.e. 48 patterns /
  1,536 bytes, and is commonly zero. That bound cannot be silently reused as the future DPLC bound.

## Targeted semantic proof summary

The full address-disciplined table is in
`docs/design/Cody_r1p1_sprite_arcade_semantic_hooks.md`. The targeted static pass proved:

- `arcade_pc 0x041180` (`runtime_genesis_pc 0x041380`) is a marker/camera/progression-driven
  recurring actor scheduler using actor-local timer `A4+0x1C`, progression `A5+0x013E`, stage
  `A5+0x0118`, and active-slot state. It does not alone prove family entry/exit windows.
- `arcade_pc 0x045342` / `0x0453A2` (`runtime_genesis_pc 0x045542` / `0x0455A2`) initializes
  and activates the fixed paired actor slots around `A5+0x0508` and `A5+0x0548`. Calls at
  `0x045FAC`, `0x045FE4`, and `0x046124` reach this routine, but the present exports do not prove
  which calls are the two Flying Demon triggers or the preload/retirement semantics.
- `arcade_pc 0x0558E0` (`runtime_genesis_pc 0x0559C0`) advances progression through
  `A5+0x10C6`, source state `A5+0x10A8`, descriptor state `0x10D0A8`, and `A5+0x013E` after the
  `A5+0x10CC == 0x10` gate. It is not proof of the distributed phase wipe/reset sequence.
- The player frame path is exact: `0x0540CC -> 0x054326 -> 0x054492` maps to current runtime
  `0x054236 -> 0x05446E -> 0x0545DA`. It selects frame IDs in `A5+0x1244/0x1246`, indexes
  the body table rooted around `0x05BD40` and weapon tables `0x05CD8A/0x05D068/0x05D346/
  0x05D666`, then expands four six-byte descriptors per body/weapon list into player piece state.

The exact phase-reset chain, hurry-up timer/threshold/spawn/reset/count, Flying Demon semantic
preload/spawn/release hooks, per-family recurring windows, and material enemy frame tables remain
unresolved. No Ghidra project or export was modified.

## A-13

Status: **STILL OPEN**. Source and existing measurements establish the finalizer as the dominant
sprite cost and identify `.Lnq_lookup_loop` plus `.Lnq_vloop` as removable search work, but they
do not separate hit iteration counts, miss/free-cell iterations, rest-of-emitter dots, and fixed
overhead over the same chains. A measurement build would be required for that exact split. A-13
was optional here and did not block the capacity proof.

## Readiness gate

**BLOCKED.** Exact VRAM capacity is resolved, but final runtime implementation is not ready because:

1. the maximum safe region is 58 while the trace peak is 63;
2. 19 legal classes remain semantically unresolved and no alias is proven;
3. actor/frame tables and multi-instance unions are incomplete;
4. phase, hurry-up, and Flying Demon semantic load/release hooks are incomplete;
5. future aggregate DPLC DMA is unbounded;
6. A-13 remains open (not itself a blocker to A/B/C).

No production `.Lnq_*`, residency, allocator, worklist, or sprite-lifecycle machinery was removed
or installed. `FINAL_CONSENSUS.md` was not modified.

## Project impact

- Production source/spec/ROM/build number changed: **no**.
- Test builds: **none**; highest remains 0356; next valid is 0357.
- Open/Closed Issues: OPEN-017 and OPEN-024 referenced; none opened or closed.
- KNOWN_FINDINGS: no new indexed finding; this report refines the implementation boundary under
  KF-068/KF-074 without contradicting them.

