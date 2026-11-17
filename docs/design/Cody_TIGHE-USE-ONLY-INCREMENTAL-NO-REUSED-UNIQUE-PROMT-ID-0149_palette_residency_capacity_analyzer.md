# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0149

# Offline Palette Residency Capacity Analyzer

## 1. Starting state

- Branch: `rastan-direct-proposal`.
- HEAD: `275e2e35e65e46dab46ce685c035e554dea4110d` (`Checkpoint facing resolution and firepit research before analyzer`).
- Makefile counter at entry: `573`.
- The worktree already contained concurrent generated `apps/rastan-direct/out/*`, build manifests/disassembly/trace output, `tools/mame/cheat/output.json`, `apps/rastan-direct/src/sound/sound_comm.s`, Andy 0134–0136 documentation, and unrelated proposal documents. They were preserved.
- The three current inputs were read in full: Andy 0146, Antigravity 0147, and Cody 0148.
- Existing Palette Composer/editor work was preserved; no API, UI, save path, profile, or production exporter was changed.

## 2. Reconciliation of 0146, 0147, and 0148

All three proposals correctly pointed toward offline residency/capacity analysis. The live corpus confirms Andy/Cody's no-sprite, bank `$014`, mode-8, fixed-tile conclusions. Antigravity's specific sprite members, Line-1 lease, six-color allocation, and record-only safety conclusion were rejected because they lack a complete consumer/writer proof. Andy's Line-3 preference remained conditional and is disproven losslessly by the new viewport arithmetic. Cody's conservative writer/visibility gates were retained.

## 3. Antigravity facts accepted/rejected

Accepted: a read-only occupancy view, explicit lifecycle/writer evidence, offline boundary compilation, and treating intentional merges as authored decisions.

Rejected for this effect: actor `$0224`, any flame sprite, Line-1 slots 9–14 as safe, the six-color palette, runtime schedule details, and a selected Line-1 host. The R1-S2 actor evidence retires `$0224`; the record-local lifetime of other PC090OJ actors remains incomplete.

## 4. Andy facts accepted/gated

Accepted: Plane-A tiles `$093A–$0949`, usages `LA-0479..LA-0494`, bank `$014`, `$059962 -> $059AD4`, table `$59B1A`, no sprite component, and Line 2 as protected dynamic Layer B.

Gated/revised: Line 3 does not fit losslessly. Andy's claimed tenth word, `0x08CE` for source index 6 (`#F7E784`, raw `$0FE8`), is a conversion error. The current production conversion and the analyzer both produce `0x08EE`, already shared by indices 5/11. The correct initial count is nine.

## 5. Cody-0148 facts retained

The fire uses every source index 1–15; current Test 2.0 maps its tiles independently onto protected Line 2; bank `$014` has no live gameplay route; no R1-S2 flame sprite exists; `$FFFF` means retain; and neither visible non-use nor a scene-wide color count proves a slot lease.

## 6. Analyzer architecture

`tools/graphics_editor/analyze_palette_residency.py` is a generic read-only CLI. It accepts scene, retained record, neighboring record count, effect usages, source bank, optional candidate line/color limit, profile, viewport dimensions/top, and output path. It reuses the current Composer's selector-aware `layera_map()` decoder rather than inventing map geometry. It reads the profile/corpora/ROM regions, reconstructs phases and viewport demand, assigns slot classifications, evaluates Lines 0–3, and emits sorted deterministic JSON. Missing evidence is explicit and `UNKNOWN` is never leaseable.

No optional Composer endpoint was added; keeping the analyzer headless avoided changing current server behavior.

## 7. Files changed

- `tools/graphics_editor/analyze_palette_residency.py`
- `tools/graphics_editor/test_analyze_palette_residency.py`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0149_palette_residency_capacity_analyzer.md`
- Generated, ignored analysis output: `build/analysis/palette_residency/r1s2_firepit_capacity.json`

## 8. Exact fire effect definition

- Scene: `PAL-R1-S2-PLANEA-CASTLE`.
- Retained record: 18.
- Effect members: `LA-0479..LA-0494`.
- Tiles: `$093A..$0949`.
- Source bank: `$014`.
- Sprite members: none; the R1-S2 sprite-flame hypothesis is disproven.
- Source indices: all 1–15; index 0 is absent.
- The repeated map band occupies record-local X 8–55 and rows 28–63 (1,728 decoded cells). The visible fire lip in the normal horizontal 28-row viewport is row 28; the deeper repetition supplies the below-screen pit.

## 9. Fire animation lifecycle

Initial bank `$014` is followed by three `$59B1A` rows. `FUN_00059962` advances a 0..23 counter and calls `$059AD4` when `(counter & 7) == 0`, selecting phase 0, 1, then 2. Each `$FFFF` keeps the previously resident entry. The JSON contains all sixteen raw and converted words for initial, phase 0, phase 1, and phase 2.

## 10. Initial-versus-phase color-count resolution

- Initial bank: **9** distinct nontransparent Genesis words.
- Resolved phases 0/1/2: **9 / 8 / 8**.
- Complete lifecycle union: **9**.
- Maximum simultaneous requirement: **9**.
- Quantization-only merges: six of fifteen arcade source indices collapse without artistic loss.

The exact lifecycle vocabulary is `006E 008E 00AE 00CE 00EE 08EE 0AEE 0CEE 0EEE`. There is no `08CE`. This resolves the 0146/0148 discrepancy: Cody's animated count of nine was correct, and the static bank also has nine after applying the actual conversion.

## 11. Visibility window

The Genesis H40 viewport is 40×28 cells. The live Plane-A producer derives visible top as `((-A5+$10B0 + 8) & $1FF) >> 3`; the analyzed horizontal state uses logical top row 1. Fire pixels occupy global X 9280..9663. A single fire pixel can therefore intersect the viewport for camera-left pixel 8961..9663. Tile-aligned critical views span global cell-left 1121..1207 (87 views), straddling decoded records 17, 18, and 19. Forward and reverse traversal use the same envelope.

Preparation may occur over records 17..19 without altering CRAM. Activation must occur before record-18 Plane-A presentation. Release requires proof that record 18 has left the viewport, not merely a retained-record increment. Reverse entry 19→18 must reactivate; reverse exit toward record 17 must restore only after the effect leaves.

## 12. Checkpoint/respawn evidence

R1-S2 has stage/checkpoint seed 16 and begins live play at retained record 17 (the established direct-start observation is stage `$0010`, record `$0011`). `A5+$13E` is monotone and has no same-stage respawn rewind writer. A death at record 18 can therefore respawn while record 18 remains selected, so the fire can be immediately relevant after scene reconstruction. A later implementation must re-evaluate residency and install the correct initial/current phase before visibility; this task does not implement that behavior.

## 13. Line-0 capacity result

Rastan and his default held weapon are proven live consumers. Their Test 2.0 mappings require all 15 Line-0 indices. Two fire words (`006E`, `00EE`) already match, but the lossless union is 22 colors: **7 over capacity**. Result: `REQUIRES_ARTISTIC_MERGES`. No merge is authorized.

## 14. Line-1 capacity result

The Plane-A corpus proves no host demand on Line 1, but it does not prove the record-local PC090OJ actor lifetime or all sprite writers. Slots 9–14 are therefore `UNKNOWN`, not `UNUSED_STABLE`. Result: `INSUFFICIENT_VISIBILITY_PROOF`. Antigravity's lease is not established.

## 15. Line-2 capacity result

The current-round `$059AD4` Layer-B producer owns the protected line, index 1 is time-of-day animated, and sparse `$FFFF` rows depend on retained history. The compiler itself documents its selector-0 player-driven Plane-B Y envelope as incomplete, so exact pixel-visible L2 demand is not fabricated. The full resident row plus fire has a 21-color union (three exact overlaps), six over 15, but dynamic ownership already decides the candidate: `UNSAFE_DYNAMIC_WRITER`.

## 16. Line-3 capacity result

Across all 87 critical views, up to **13 distinct non-fire castle colors** must remain correct. The nine fire colors have **zero exact overlap** with them. Combined lossless demand is **22**, or **7 over capacity**. Result: `REQUIRES_ARTISTIC_MERGES`.

The JSON identifies all 164 affected non-fire usage IDs and 70 source tile codes that a hypothetical regional composite would have to reindex. Because no lossless composite exists, no composite palette is emitted.

## 17. Slot writer classifications

Every line/index has one of the required classifications plus evidence:

- Line 0: index 0 backdrop/transparent; 1–15 `USED_STATIC` by the proven player/weapon lower bound.
- Line 1: 1–15 `UNKNOWN` because actor/writer lifetime is incomplete; not leaseable.
- Line 2: index 0 reserved; 1–15 `USED_DYNAMIC` by protected Layer-B ownership, animation, and retain history.
- Line 3: simultaneously referenced castle entries are `USED_STATIC`; 14/15 are `UNUSED_DYNAMIC` in this viewport because the R1 mode-9 waterfall writer can update them; no dynamic slot is leaseable.

## 18. Exact lossless composite palettes

None. No candidate line is both proven safe and within 15 nontransparent entries. The analyzer intentionally persists no approved host choice.

## 19. Exact over-capacity counts

| Line | Proven/current host colors | Exact overlap | Lossless union | Over 15 | Result |
|---:|---:|---:|---:|---:|---|
| 0 | 15 | 2 | 22 | 7 | `REQUIRES_ARTISTIC_MERGES` |
| 1 | incomplete | unknown | lower bound 9 | unknown | `INSUFFICIENT_VISIBILITY_PROOF` |
| 2 | 15 resident/writer-owned | 3 | 21 | 6 | `UNSAFE_DYNAMIC_WRITER` |
| 3 | 13 | 0 | 22 | 7 | `REQUIRES_ARTISTIC_MERGES` |

## 20. Generated JSON

Path: `build/analysis/palette_residency/r1s2_firepit_capacity.json`.

SHA-256: `03083fc46b9109751a20e5fb6db657e48dd6cdc033787691eec6a2ef785436d6`.

Provenance includes the Test 2.0 SHA (`4339688ebe07bc121d5108d464f57b320a6628f4c36cdd71a95cfe5ea8c964cf`), both corpus SHAs, `maincpu.bin`, `pc080sn.bin`, all inputs, exact phases, critical views, demand, writers, slot classes, candidate arithmetic, boundaries, and unresolved facts.

## 21. Deterministic tests

`python3 -m unittest tools/graphics_editor/test_analyze_palette_residency.py`

Result: **10 tests passed**. Coverage includes fire membership, no sprites, bank `$014`, all source indices, conversion/quantization, exact phases, KEEP history, viewport and reverse envelope, host demand, writer classes, Line-3 arithmetic, Line-1 non-lease, L2 writer rejection, and byte-identical repeated JSON serialization.

## 22. Unresolved evidence

- Exact record-local PC090OJ actor lifetime remains incomplete, so Line 1 cannot be leased.
- Exact selector-0 Plane-B pixel visibility remains incomplete in the production compiler, so L2 cannot receive a falsely precise visible-index subset.
- A later compiler/runtime design must bind activation/release/rearm to retained camera and lifecycle boundaries. This analyzer does not prescribe that implementation.

## 23. Recommended host line

**None.** No host line is mechanically proven safe and lossless. This is the required valid negative result.

## 24. Production source changed

**NONE.** `apps/rastan-direct/src/*` was not modified by this task.

## 25. Profile/registry changed

**NONE.** `Test_2_0.json` and `specs/palette_decisions.json` retain SHA-256 values `4339688e...c964cf` and `9fdd8f92...8f0e3` respectively.

## 26. ROM produced

**NONE.** No build was run.

## 27. Build number consumed

**NONE.** The counter remains 573.

## Open/Closed Issues Impact

No issue was closed and no runtime acceptance claim was made. This evidence narrows the open fire-pit palette-residency problem: lossless L0/L3 composites fail, L2 is writer-unsafe, and L1 remains unproven rather than safe.

## Smallest next action

Obtain the missing record-18 PC090OJ consumer/writer lifetime census for Line 1 and complete the existing Plane-B Y-envelope model only if L2 remains a serious candidate. Then rerun this same analyzer. If neither yields a lossless safe host, Tighe must author an explicit artistic reduction/merge in Palette Composer before any runtime residency implementation.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0149
