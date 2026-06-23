# Cody - Build 0094 FG Clear Boundary Pin

**Date:** 2026-06-23  
**Type:** Runtime diagnostic / evidence capture only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`  
**ROM SHA256:** `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`  
**Scope:** Existing Build 0094 ROM only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No bookmark cycle. No exception/input/BG/sprite/palette/logotype work.

## Phase 0

Classification: **EXTENDING** (OPEN-001). Required architecture/rule files were loaded: `RULES.md` and `ARCHITECTURE.md`. Relevant priors loaded from `KNOWN_FINDINGS.md`: KF-010, KF-011, KF-013, KF-028, KF-029, KF-030, KF-031. Issue context loaded from `OPEN_ISSUES.md` / `CLOSED_ISSUES.md`; OPEN-001 is active, OPEN-016 is context, OPEN-015 remains do-not-touch. Latest `AGENTS_LOG.md` entries were read, including Cody's additive-FG classification and Andy's static lifecycle map.

Architecture compliance: **CONFIRMED**. This task used MAME/debugger observation against the existing Build 0094 ROM. No production code or ROM artifact was changed.

## Evidence Artifacts

Trace directory: `states/traces/build_0094_fg_clear_boundary_pin_20260623_163748/`

Primary artifacts:
- `mame_fg_clear_boundary_pin.cmd`
- `native_events.log`
- `native_debug_trace.log.gz`
- `fg_before_page_start_transition_3ac82.bin`
- `fg_after_page_start_transition_3ac88.bin`
- `fg_before_3acae.bin`
- `fg_after_3acae.bin`
- `fg_clear_boundary_pin_analysis.json`
- `fg_clear_boundary_pin_analysis.md`

Post-state-write confirmation artifacts:
- `mame_fg_clear_boundary_pin_post3acf8.cmd`
- `native_events_post3acf8.log`
- `native_debug_trace_post3acf8.log.gz`
- `fg_after_3acae_before_state4_3acf8.bin`
- `fg_after_3acae_post_state4_3acfe.bin`

The post-state-write rerun exists only to confirm the final `%a5@(4)=2` write at `0x3ACF8`; it does not change the primary boundary classification.

## State-Write Timeline

MAME watchpoints report the PC after the write instruction has executed. Exact writing PCs below are therefore labeled from the disassembly / breakpoint site, with the watchpoint PC noted in the reduced analysis.

| Frame | Exact write PC | State write | Values / result |
|---:|---|---|---|
| 0 | `0x3AC4C` | `%a5@(4) <- 1` | starts the first title inner producer phase after `0x3AC40` |
| 1 | `0x3AC7E` | `%a5@(4) <- 0` | clears producer phase at the tail of `0x3AC54` |
| 1 | **`0x3AC82`** | **`%a5@(2) <- 1`** | **page-start transition for the page containing `0x3ACAE`; `%a5@(0)=0`, `%a5@(2)=1`, `%a5@(4)=0` after the transition** |
| 210 | `0x3ACA6` | `%a5@(4) <- 1` | setup phase for the `0x3ACAE` producer after the `%a5@(44)` countdown |
| 212 | `0x3ACF8` | `%a5@(4) <- 2` | tail of `0x3ACAE`; post-confirmed at `0x3ACFE` as `%a5@(4)=2` |

**Exact page-start transition PC:** `runtime_genesis_pc 0x0003AC82`, the `movew #1,%a5@(2)` instruction. It changes the title sub-page from `0` to `1` while the master page remains `%a5@(0)=0`. The next page's draw does not occur until later, when `0x3ACA6` sets `%a5@(4)=1` and the dispatcher reaches `0x3ACAE`.

## Four FG Staging Snapshots

| Snapshot | Capture point | Nonzero cells |
|---|---|---:|
| before page-start transition | immediately before `0x3AC82` writes `%a5@(2)=1` | `62` |
| after page-start transition | at `0x3AC88`, after `%a5@(2)=1` is established | `62` |
| immediately before `0x3ACAE` writes | at `0x3ACAE` entry | `62` |
| after `0x3ACAE` completes | at `0x3ACF8`, before `%a5@(4)=2`; post-`0x3ACFE` confirmation also `191` | `191` |

## Stale-Cell Survival

`staged_fg_buffer` already contains stale prior-page data before the page-start transition at `0x3AC82`, and that content survives unchanged through the transition and into the later producer.

Comparisons:

| Window | Before nonzero | After nonzero | Retained nonzero | Retained same | Cleared | Added |
|---|---:|---:|---:|---:|---:|---:|
| before `0x3AC82` -> after `0x3AC82` | `62` | `62` | `62` | `62` | `0` | `0` |
| after `0x3AC82` -> before `0x3ACAE` | `62` | `62` | `62` | `62` | `0` | `0` |
| before `0x3ACAE` -> after `0x3ACAE` | `62` | `191` | `62` | `56` | `0` | `129` |
| before `0x3AC82` -> after `0x3ACAE` | `62` | `191` | `62` | `56` | `0` | `129` |

Conclusion: stale cells survive the state transition and the counter-gated delay. The producer adds new cells over that existing staging state rather than replacing it.

## Clear Hook Check

`runtime_genesis_pc 0x000710D8` (`genesistan_hook_cwindow_clear`) did **not** fire before `0x3ACAE`.

Event counts:
- `CWINDOW_CLEAR_ENTRY_710D8`: `0`
- `FG_COMMIT_ENTRY_70182`: `212`
- `FG_STORE_70794`: `258`

FG commits occurred, but they did not clear the WRAM staging buffer; they only committed dirty rows and cleared dirty flags. The clear absence is therefore a staging-lifecycle fact, not a VBlank commit timing artifact.

## CLEAR vs OVERWRITE Determination

Verdict: **CLEAR-needed**, not emitted-but-lost overwrite.

Runtime evidence from the captured `0x3ACAE` page:
- Stores from first render (`0x3ACB6`) through producer end: `160`.
- Nonzero stores: `135`.
- Zero stores: `25`.
- Distinct store offsets: `160`, bounded to `0x0420..0x0DD2`.
- The zero stores are per-glyph/per-string cell stores inside the glyph renderer output, not a full-page blank/fill pattern.
- No full-page or blank-tile sweep over `staged_fg_buffer` occurred.
- No `0x710D8` clear occurred.
- No old cells were cleared in the four-snapshot comparison.

Current translated runtime behavior for this page replacement is therefore: **bounded glyph-cell emission additively into persistent staging**. It is not a full-page overwrite whose blank cells failed to affect staging.

## Recommended Insertion Point and Granularity

**Recommended insertion point:** the `0x3AC82` page-start state transition site, after preserving the arcade state write `%a5@(2) <- 1` and before the next page's producers draw. In practical placement terms, the clear belongs immediately after the `0x3AC82` transition write (or an equivalent production helper call at that same semantic boundary), not at `0x3ACAE` as a producer-local fallback.

**Granularity:** per-sub-page (`%a5@(2)`) for the captured boundary, not per-master-page (`%a5@(0)`). `%a5@(0)` remains `0`; the visible replacement boundary is the transition from `%a5@(2)=0` to `%a5@(2)=1`. This does not prove every master 0/1/2 transition uses exactly the same insertion PC; it pins the exact boundary for the page containing `0x3ACAE`.

**Why not `0x3ACAE`:** `0x3ACAE` is the producer, not the page boundary. Clearing there would be a minimal local mitigation for this producer only, but it would not represent the arcade state transition that begins the page. The boundary evidence points earlier: `0x3AC82`.

**Why not only the dispatcher immediately after it:** the dispatcher reaches `0x3AC90` repeatedly while `%a5@(44)` counts down, and `0x3AC9E` is a setup phase before the actual producer. The staging is already stale during the whole countdown window. The semantic page-start transition has already occurred at `0x3AC82`.

Implementation is safely placeable for this captured page boundary: **YES**, at `0x3AC82` / `%a5@(2)` transition granularity. A global all-attract-pages clear policy still needs separate runtime proof for each additional page transition before broadening beyond this boundary.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active), OPEN-016 (context), OPEN-015 (do-not-touch context)
- Closed issues touched: NONE
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: implementation, other attract page boundaries, game-start redraw full trace, Start/C/A exception, OPEN-015 crash-handler fix, BG/sprites/palette/logo/sword/HV-counter/real-hardware work

## KNOWN_FINDINGS Impact

Option C candidate only. This diagnostic strengthens the Build 0094 additive-FG finding by pinning the exact captured page-start boundary (`0x3AC82`) and proving current runtime behavior is CLEAR-needed rather than emitted-but-lost overwrite. `KNOWN_FINDINGS.md` was not edited in this task.

## STOP

STOP triggered: **NO**. The exact captured boundary was pinned, `0x710D8` non-fire was confirmed, and clear-vs-overwrite was resolved for the page containing `0x3ACAE`.
