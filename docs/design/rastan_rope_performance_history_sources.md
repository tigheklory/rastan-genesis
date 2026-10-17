# Rastan Rope-Race Performance Report — Source & Annotation Manifest

**Date:** 2026-10-16 · **Type:** report/visualization only. No benchmarks rerun, no production source,
no ROM, no build number, no Phase D/E. Companion to `rastan_rope_performance_history.html`.

## Benchmark files used (authoritative, embedded as the chart dataset)

- `states/traces/historical_rope_benchmark/canonical_results.csv` / `.json` — 437 canonical builds;
  the benchmarkable era (0282–0437, 156 rows) is embedded in the HTML. Dataset generated
  **2026-10-17T04:04:43Z** (per `canonical_results.json`; builds 0420–0437 re-run with
  `--trials 3 --jobs 1 --force` on 2026-10-17, all deterministic).
- `states/traces/historical_rope_benchmark/full_hud_results.csv` / `.json` — `_full_hud` for
  0434/0435/0436/0437 (embedded).
- `states/traces/historical_rope_benchmark/summary.md`, `cache.json`, `runs/` — inspected; not
  directly embedded.
- Batch tool: `tools/mame/run_historical_rope_benchmarks.py` (NOT run).

**Data-correction verification:** the corrected sequential reruns (`--jobs 1 --force`) are already
present in the current aggregate CSV/JSON — verified: 0412=949, 0413=917, 0414=915, 0415=854,
0416=856, 0417=911, 0418=911, 0419=878, 0421=879 (0415 already 854). 0420=NO_GAMEPLAY (illegal
instruction). No rebuild from per-ROM cache was needed; no emulator was run.

## Arcade reference

- Rastan World Rev 1 — **771 frames / 12,850.000 ms** — `docs/design/Cody_arcade_rastan_rope_race_silver_standard.md`,
  evidence `states/traces/arcade_rastan_rope_attach_reference/`.

## Historical reports consulted (for annotations)

`AGENTS_LOG.md` (primary chronology) plus the per-build design reports named in the task prompt
(Cody_build0411/0412/0413/0415/0416/0417/0418/0419/0421/0422/0423/0424/0426/0428, death-effect,
vertical-scroll/HUD, 0435 HUD restoration, 0436 vertical-origin split) and my prior audits
(`Andy_build0415_bg_a_regression_forensic_review.md`, `Andy_build0421_native_background_independent_audit.md`,
`Andy_hud_suppression_history_audit.md`, `Andy_full_gameplay_hud_native_restoration_contract.md`,
`Andy_vertical_origin_history_and_buildtime_constantization.md`). Annotation text is sourced from
these; frame values are from the embedded dataset only.

## Dataset-computed facts (not hand-entered)

- First benchmarked (PASS): **B0282 = 1082 fr**. Current: **B0437 = 806 fr**. Best accepted:
  **B0428 = 803 fr** (gap +32). Current gap to arcade: **+35 fr**.
- First below 1200/1100 = B0282; below 1000 = B0407 (997); below 900 = B0415 (854, **rejected**);
  below 850 = B0424 (817).
- Largest single-build gain / regression are computed live from consecutive PASS builds (B300→301 is
  an early outlier +1737; flagged as such). The curated regression of note is **0401 (1061→1439,
  +378)**.

## Annotated builds & acceptance classifications

| Build | Acceptance | Evidence | One-line |
|---|---|---|---|
| 0401 | experiment | P | ownership snapshot; perf regression by design (1061→1439) |
| 0407 | accepted | P | pure-native sprite closeout; first big win (→997) |
| 0411 | accepted | P | SAT/residency; avg worker < 1 frame (→978) |
| 0412 | accepted | P | P1 HUD glyph fast queue (→949) |
| 0413 | accepted | P | probe MOVEM overhead removed (→917) |
| 0415 | **rejected** | P | fast but invalid (854; stale ring on hardware) |
| 0416 | intermediate | A | 41×29 repair attempt; not final (856) |
| 0417 | accepted | P | full 64-cell correctness restored (→911) |
| 0418 | accepted | P | 128-KiB DMA boundary fix; no rope change (911) |
| 0419 | accepted | P | fused visual+collision (→878) |
| 0420 | **rejected** | P | illegal TST.L A0; unbenchmarkable |
| 0421 | **rejected** | P | benchmarkable (879) but Segment-0 regression |
| 0422 | accepted | P | ring-seam correction (879) |
| 0423 | accepted | P | Plane-B native (→858) |
| 0424 | accepted | P | selector-0 four-row hoist (→817) |
| 0425 | accepted | A | selector 1/2 opt; off-route, no rope change (817) |
| 0426 | accepted | P | compact enemy/generic sprites (→806) |
| 0427 | consumed | P | same source as 0426 (806) |
| 0428 | accepted | P | player native; 803 plateau |
| 0429–0432 | **unknown** | U | 804/804/805/803 — cause not established in reviewed evidence |
| 0433 | accepted | P | death effects; off-route (803) |
| 0434 | accepted | P | vertical rows; off-route (803); `_full_hud` 803 NOT a valid HUD baseline |
| 0435 | accepted | P | upper-HUD restoration candidate; `_full_hud` 854 (+51/+6.35%) |
| 0436 | intermediate | A | vertical-origin split; 803→807 regression; root-cause pending |
| 0437 | intermediate | P | compile-time vertical-origin correction; 806 (−1 vs 0436); regression reduced, HW acceptance pending; `_full_hud` 859 |

Evidence legend: P = proven/measured, A = strongly associated, H = historical context, U = cause not
established.

## Unresolved attribution

- **0429–0432** (804/804/805/803): classification not established from the reviewed evidence —
  shown as acceptance "unknown"; annotate only when AGENTS_LOG/report proof is located.
- **Largest-regression auto-metric** surfaces B300→301 (+1737), an early benchmarkable outlier, not a
  code-caused regression of record; labeled "(early outlier)" in the UI.
- **0436** regression magnitude is measured/deterministic, but the RAM-backed active-origin mechanism
  is not instruction-by-instruction proven to account for all of it (wording kept conservative).
