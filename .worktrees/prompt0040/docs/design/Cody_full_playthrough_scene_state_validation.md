# Cody — Full Playthrough Scene/State Validation (Prompt 208)

## 1. Executive Summary

Using the prior cheat-assisted full-run artifact set (`rastanmon` + fullgame inventory) plus current lite profiling outputs, scene/state coverage is materially broader than the recent shorter profiling run. The coarse 3-bucket PC080SN model remains valid, but sprite safety is still not proven because several late-stage/full-run scenes are not directly represented in the current sprite profile summary.

## 2. Prior Full-Game Artifact(s) Located

Located from AGENTS_LOG references and repository artifacts:

- AGENTS_LOG references:
  - `## [Cody - Build 143 — HUD Trace + Validation Pass]` (cheat anchors noted, fullgame artifacts produced)
  - `## [Cody - Research, Title Screen Graphics Call Inventory]` (explicit `rastanmon` snapshot reference)
- Full-run/fullgame artifacts:
  - `docs/replacement_inventory/fullgame_window_replacement_inventory.json`
  - `docs/replacement_inventory/fullgame_window_replacement_inventory.csv`
  - `build/mame/home/rastanmon/rastan_monitor.log`
  - `build/mame/home/rastanmon/snapshots/` (38 snapshots)
- Recent comparison artifacts:
  - `build/mame/home/rastantrace_lite/rastan_exec_trace_lite.log`
  - `build/mame/home/rastantrace_lite/rastan_exec_summary_lite.txt`
  - `build/mame/home/rastantrace_lite/rastan_sprite_profile_summary.txt`

## 3. Coverage Difference vs Current Analysis

Direct comparison:

- Prior full-run (`rastanmon`) scene labels: 29 unique
- Recent lite run scene labels: 22 unique
- Prior full-run stages observed (from mode lines): `0x0000` through `0x002f` (including `0x000d`, `0x0011`, `0x002d`, `0x002e`, `0x002f`)
- Recent lite run stages observed: `0x0000`, `0x0001`, `0x0006`

High-value prior full-run-only scene families:

- `active_runtime_stage_02/03/04/06/0d/11/2d/2e`
- `round_stage_presentation_09/11/12/13`
- `runtime_other` (legacy/generic runtime bucket)

Conclusion: the prior full-run artifact materially improves scene/state coverage versus the recent shorter run.

## 4. Updated Scene/State Taxonomy

Updated taxonomy (evidence-backed labels):

- Frontend/title cluster:
  - `frontend_title_or_attract`
  - `frontend_credit_ready`
  - `frontend_page_0000_0001`
  - `frontend_page_0002_0000`
  - `frontend_page_0002_0002`
  - `frontend_page_0002_0003`
  - `frontend_page_0002_0004`
- Transition/wait:
  - `wait_for_play`
- Runtime gameplay cluster:
  - `active_runtime_stage_02/03/04/06/0d/11/2d/2e`
  - `runtime_other`
- End-round presentation cluster:
  - `round_stage_presentation_09/11/12/13`
- Death/continue cluster:
  - `death_game_over_continue_01` through `death_game_over_continue_08`

This closes the previously-inferred-but-not-proven round-presentation states and late-stage runtime labels.

## 5. PC080SN Bucket Revalidation

Revalidation result: the coarse 3-bucket BG model remains valid.

- Bucket 0 (Title/Attract): frontend/title states above
- Bucket 1 (Gameplay): `active_runtime_stage_*` / runtime gameplay states
- Bucket 2 (End-Round): `round_stage_presentation_*` states

No new fourth BG residency bucket is proven by the prior full-run artifact.

## 6. PC090OJ Peak Revalidation

Current measured sprite peak (from recent sprite profiler):

- `frontend_0002_0003`: peak active unique = 59, peak visible unique = 56 (already above the 48-cell assumption)

Strengthened by prior full-run evidence:

- The prior full-run includes additional late-stage/runtime/presentation states not directly represented in the current sprite profile summary output.
- Unprofiled (vs current sprite summary) high-coverage states include:
  - `active_runtime_stage_02/03/04/06/0d/11/2d/2e`
  - `round_stage_presentation_09/11/12/13`
  - `frontend_credit_ready`, `frontend_0002_0004`, `runtime_other`

Interpretation:

- The prior full-run does not provide direct per-frame unique sprite-code counts by itself.
- It does prove that current sprite peak measurements do not yet span all meaningful full-run states.
- Therefore, 48-cell safety is still unvalidated and likely optimistic.

## 7. Root Uncertainty Resolution Status

Status: **UNCHANGED (not resolved)**.

Original uncertainty: whether the observed 56/59 peak is true required concurrent sprite demand or a conservative overcount.

After incorporating prior full-run artifacts:

- The uncertainty is not resolved because the fuller artifact has wider state coverage but no direct per-scene sprite unique-count metric.
- Risk posture is stronger: there are additional high-value scenes beyond the currently measured sprite-profile subset.

## 8. Updated Verified Next Step

Selected next step: **D. gather one final precision dataset**.

Required dataset:

- Re-run sprite working-set profiling with the same unique-count metrics (`raw/active/visible`) while intentionally traversing the full-run scene set confirmed by `rastanmon` (including `active_runtime_stage_2d/2e` and `round_stage_presentation_*`).
- Output per-scene peak counts for those states so VRAM sprite reservation can be validated or redesigned with evidence.

## 9. Final Verdict

- Prior full-game artifact located and incorporated: YES
- Scene/state coverage improved substantially versus recent lite run: YES
- PC080SN 3-bucket model remains valid at coarse BG level: YES
- Sprite VRAM safety remains unproven; current 48-cell assumption is still at risk: YES
- One final precision sprite dataset across the full-run scene set is required before treating sprite reservation as safe.
