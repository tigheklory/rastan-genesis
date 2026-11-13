# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0113 — Native R2 Plane-A integration

**Author:** Andy · **Date:** 2026-11-09 · **Scope:** `tools/translation/compile_pc080sn_genesis.py` investigation
(reverted). No numbered build produced — see **Local MAME Limitation** and **R1 non-regression** for why a
candidate was not shipped.

## Result

The **epoch-capacity blocker is solved**: giving Round 2 a finer per-segment epoch split makes every R2 Plane-A
residency fit the 676-pattern cap, and R1's generated output is semantically unchanged. But enabling native R2
Plane-A then exposes a **deeper shared code-space constraint** (the transition-scratch region of the native
Plane-A LUT) that cannot be resolved without changing structures R1's own transitions depend on — and I cannot
verify R1 survives that change in this sandbox (MAME is wedged). Per §10/§13 I did **not** ship an unverifiable
build that risks the accepted 0560 baseline. Progress + the exact remaining work is below so a working-MAME
session can finish it quickly.

## Build 0560 Baseline

HEAD `f8b07a84 Post Build 560`; counter 560; `EDITOR_PALETTE_PROFILE_ID ?= Test_2_0`. Tighe visually confirmed R1
Rastan correct. Preserved; the generator change was reverted so 0560 stays buildable.

## R2 Epoch Capacity Analysis

Arcade stage `a5@0x1242 = (round-1)*23 + 16*castle + 22*boss` (RG-019) → R2 owns records 23–45 (outdoor 23–38,
castle 39–44, boss 45). The earlier "683 > 676" was **not** a VRAM wall — it was R2's coarse 2-epoch default
(`range(23,34), range(34,46)`). The finer split below validated against the real authored/Test-2.0 synthetic
pattern counts.

## Final R2 Epoch Segmentation (validated)

| epoch | records | synthetic patterns | ≤ 676 |
|---|---|---|---|
| R2-a | 23–32 | **586** | yes |
| R2-b | 33–38 | **606** | yes |
| R2-c | 39–45 | **425** | yes |

Generator confirmed: `requested 9 epochs at cap 676; per-round minima 5/3`. R1 epoch unions unchanged
semantically `[283,366,665,634,640,593]`.

## Generator Extension (done, then reverted)

Extended `AuthoredLayerA.SCENES` with the three R2 contexts (`PAL-R2-S1-PLANEA-OUTDOOR` records 23–38,
`PAL-R2-S2-PLANEA-CASTLE` 39–44, `PAL-R2-S3-PLANEA-BOSS` 45) consuming Test 2.0's existing per-usage mappings
(789/234/200), and set `BOUNDARY_ROUND2_EPOCH_RECORDS = (range(23,33), range(33,39), range(39,46))`. Capacity
gate passed. Then the generator aborted at the **next** layer (below). Reverted to keep 0560 buildable.

## Blocker 1 — transition-scratch / LUT code-space (needs a shared-structure change)

`compile_pc080sn_genesis.py:1016` places the transition scratch at `0x1600` sized `len(pattern_id) + 676` within
the `0x2800`-word (`BOUNDARY_LUT_WORDS`) active LUT. With R2's authored patterns added, `len(pattern_id)` grows
and the scratch region runs into R2's **arcade FG codes 9403–9410** (`seg_fg_tiles` of R2 segments), tripping
`transition scratch overlaps legal LUT codes`. The scratch is **global** (R1 and R2 transitions share it), so
every candidate fix touches R1:
- Enlarge `BOUNDARY_LUT_WORDS` + relocate the scratch above the arcade-code range → changes R1 transition DMA.
- Refine `occupied_codes` to exclude native-replaced R2 codes → changes the check R1 relies on.
- Consolidate R2 near-duplicate patterns to shrink `len(pattern_id)` → §6 defers this, and only ~37 rough
  near-dups exist (1 exact dup already merged).

All three need runtime (`FG_BOUNDARY_SCRATCH_WORD` / `FG_BOUNDARY_LUT_WORDS`) changes and **visual verification**
that R1 transitions still work — unavailable here.

## Blocker 2 — 8 unmapped R2-S1 Plane-A uses (authoring gap, §8)

Test 2.0 maps 789 of R2-S1's 797 Plane-A uses; **8 are unmapped** (tile codes 0x0020 and 0x00AD across banks
3/4/5/6/9/14, records 23–38). §8 forbids me authoring R2 mappings. These would drop to raw (§27 "no dropped
usages") and need Tighe to author them in the Composer (or an explicit decision that they're intentionally
Plane-B/backdrop).

## R2 Native Pattern Residency / Scene-Asset Selection / Palette Integration / Descriptors / Transitions

**Not reached** — all gated behind Blocker 1 (the generator must emit valid R2 data before runtime wiring). The
full plan (scene-select assets 4/5/6, R2 CRAM blob embedding with Line 0 == player palette, R2 residencies,
descriptor-visual extension, R2-gated palette-gate lifts through stage 45, epoch-transition triggers at 23 /
32→33 / 38→39) is in `docs/design/Andy_r2_native_plane_a_port_plan.md`.

## Line-0 Rastan Preservation / Line-2 Reservation

Unchanged from 0560: Line 0 = player palette (the R2 CRAM blobs already carry the identical Line 0); Line 2
reserved for Plane B. No change was made, so no regression risk introduced.

## R1 Non-Regression

With R2 scenes added, R1 epoch record→epoch assignments and epoch unions were semantically unchanged (counts
shifted only by the documented editor-policy reindex that also affects 0560). Generator fully reverted → R1
byte-identical to 0560.

## Builds / SHA-256

**None produced.** The generator cannot emit valid R2 data until Blocker 1 is resolved, and resolving it blind
risks R1 (§10/§13). 0560 remains the deliverable: normal `59cf1031…`, invincible `0c08d0d7…`, R1-S2 `6521c647…`,
R1-S3 `00ac72be…`, plus R2 direct patches S2-1 `c1fd9056…` / S2-2 `f11a1f31…` / S2-3 `62eddd17…`.

## Local MAME Limitation

MAME wedges at init in this sandbox (0% CPU, ignores SIGTERM) — confirmed again this session. The remaining R2
work (scratch/LUT relocation + runtime residency/transition integration) changes shared transition behavior and
**must** be visually verified; shipping it unverified would gamble the accepted R1 baseline.

## Tighe Runtime Handoff

To finish efficiently in a working-MAME environment: (1) author the 8 missing R2-S1 Plane-A mappings in Test 2.0
(or rule them backdrop); (2) relocate/enlarge the transition scratch above the R2 arcade-code range and re-verify
R1 transitions in MAME; (3) wire the runtime per the plan doc, R2-gated, verifying R1 stays byte-identical;
(4) build 0561 and test R2-S1/S2/S3 direct ROMs.

## Deferred Issues

R2 boss AI/movement NOT TOUCHED · R2 post-boss softlock NOT TOUCHED · score/high-score NOT TOUCHED · R1-S3
torches NOT TOUCHED.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0113`
