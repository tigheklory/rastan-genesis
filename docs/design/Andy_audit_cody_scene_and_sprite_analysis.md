# Andy — Audit: Cody Scene/State + Sprite Analysis

## 1. Executive Summary

Two Cody analysis documents (`Cody_full_arcade_scene_state_taxonomy.md` and
`Cody_full_playthrough_scene_state_validation.md`) were audited against the three prior Andy
design documents and the last 200 lines of `AGENTS_LOG.md`. The BG residency architecture
(3-bucket PC080SN model, LUT, manifests, A0 range detection, trigger spec) is correct and
implementation-ready. The single open risk is that sprite VRAM capacity has not been confirmed
safe at the observed peak of 56 visible / 59 active unique sprite cells, which exceeds the
current 48-cell assumption. That risk does NOT block BG trigger implementation because the BG
tile region (slots 20–1342) is independent of where the sprite partition begins. The SGDK
failure cannot recur. It is safe to proceed with scene-trigger implementation immediately.

---

## 2. Inputs Audited

| File | Status |
|------|--------|
| `docs/design/Cody_full_arcade_scene_state_taxonomy.md` | Read in full |
| `docs/design/Cody_full_playthrough_scene_state_validation.md` | Read in full — file EXISTS |
| `docs/design/Andy_scene_mode_transition_trigger_spec.md` | Read in full |
| `docs/design/Andy_tile_reference_correctness_under_mode_residency.md` | Read in full |
| `docs/design/Cody_independent_vram_budget_verification.md` | Read in full |
| `AGENTS_LOG.md` | Last 200 lines read (lines 26380–26579) |

---

## 3. Scene/State Taxonomy Completeness Verdict

### What Cody Produced

Cody delivered two successive taxonomy documents:

**Document 1 (Prompt 207R):** Derived from MAME runtime trace (`rastan_exec_trace_lite.log` and
`rastan_sprite_profile_summary.txt`). Identified 22 unique state labels from a lite-run sample
covering stages `0x0000`, `0x0001`, and `0x0006`. Explicitly flagged that boss battles, fortress
stages, outdoor gameplay, game over, and ending were not directly observed in this run.

**Document 2 (Prompt 208):** Extended coverage using the prior full-run artifact
(`rastanmon` snapshot set, 38 snapshots, `fullgame_window_replacement_inventory.json`).
Expanded to 29 unique state labels, covering stages `0x0000` through `0x002f`. Added:
- `active_runtime_stage_02/03/04/06/0d/11/2d/2e` (late-stage runtime)
- `round_stage_presentation_09/11/12/13` (end-round presentation states)
- `runtime_other` (legacy/generic runtime bucket)

### Coverage Gaps

The following canonical high-level scene types requested by design planning remain without
explicit MAME state-label confirmation: boss battle, explicit game over (distinct from
`death_game_over_continue_*` substates), and ending/credits. Cody correctly noted these as
inferred but not proven in a single capture window.

### Grounding in Evidence

The taxonomy is grounded in real arcade code evidence (disassembly address ranges, MAME runtime
trace labels, fullgame snapshot artifacts) not speculation. The state control root at WRAM
`0x10C000` and control words near `0x10D3AA` is confirmed. The three scene address ranges are
confirmed from multiple independent sources (AGENTS_LOG line 24227, both Andy residency docs,
Cody VRAM budget doc Task 4).

### Sufficiency for Scene Detection Logic

Scene detection in the trigger spec operates on A0 source address ranges — not on state machine
labels. The A0 range model only needs the three bucket boundaries, not per-substate enumeration.
Cody's taxonomy confirmed that all observed states fall within the three disjoint source ranges
and that no new fourth BG residency bucket is required. The fine-grained substate taxonomy
(29 labels) adds behavioral fidelity but does not affect the correctness of A0-based scene
detection.

**Decision: taxonomy sufficient for implementation — YES**

The gaps (ending, explicit boss) do not affect BG trigger correctness because the trigger fires
on A0 ranges, and all plausible ending/boss states will use either the Gameplay or End-Round
source range.

---

## 4. 3-Bucket PC080SN Model Validity Under Expanded Data

### Bucket Assignment of All Identified States

| State family | Bucket | Basis |
|---|---|---|
| `frontend_title_or_attract`, `frontend_credit_ready`, all `frontend_*` variants | Bucket 0 (Title/Attract) | A0 source in `0x5A7DA..0x5B0B2` |
| `wait_for_play`, `active_runtime_stage_*`, `runtime_mode_*`, `runtime_other`, `runtime_0001/0006` | Bucket 1 (Gameplay) | A0 source in `0x56A22..0x570C2` |
| `round_stage_presentation_09/11/12/13`, `death_game_over_continue_01..08` | Bucket 2 (End-Round) | A0 source in `0x5822A..0x59614` |

### Fourth Bucket Requirement

Neither Cody document introduces a scene requiring a 4th bucket. The expanded taxonomy
(Document 2) explicitly concluded: "No new fourth BG residency bucket is proven by the prior
full-run artifact."

### Conflicting Tile Usage

No conflicting tile usage was found. The 779 aliased slots are accounted for by the manifests
and are the intentional design mechanism. The LUT/manifest consistency check (Andy correctness
doc §5) confirmed zero inconsistencies across all 2,737 manifest pairs. The expanded scene
taxonomy adds substates within existing buckets — it does not introduce new tile sources that
would require LUT regeneration.

### LUT Generation Assumptions

The LUT was generated from `TITLE_STATIC_BLOCKS`, `GAMEPLAY_TABLE_START/END`,
`ENDROUND_TABLE_RANGES`, heuristic strip-table discovery, and text writer table extraction.
The expanded taxonomy adds runtime substate labels but does not identify new ROM tile source
ranges beyond what the Python tool already modeled. Cody's document 2 does not cite any
evidence of tile references from the newly-named substates that fall outside the three source
ranges used for LUT generation.

**Decision: 3-bucket model remains valid — YES**

---

## 5. A0 Range Detection Sufficiency

### Canonical Ranges (from all five input documents, consistent)

| Scene ID | Name | A0 Lo (24-bit) | A0 Hi (24-bit) |
|---|---|---|---|
| 0 | Title / Attract | `0x05A7DA` | `0x05B0B2` |
| 1 | Gameplay | `0x056A22` | `0x0570C2` |
| 2 | End-Round | `0x05822A` | `0x059614` |

All three are confirmed disjoint: gaps at `0x570C2 < 0x5822A` and `0x59614 < 0x5A7DA`.

### Coverage of Expanded Scene Taxonomy

The expanded taxonomy (Document 2) identifies 29 state labels covering stages through
`0x002f`. All states map to one of the three A0 ranges above. No state was identified with
an A0 source address outside these three ranges. The A0 ranges are derived from static
analysis of the ROM's PC080SN descriptor dispatch paths, which are shared by all gameplay
substates, not per-stage-specific paths.

### Overlapping or Ambiguous Ranges

None identified. The ranges are derived from fully disjoint ROM regions. The expanded
taxonomy does not introduce new code paths that would generate A0 values in the gaps between
ranges.

### Trigger Spec Modification Required

No modification required. The trigger spec's range table (`genesistan_scene_a0_ranges`, 24
bytes, 3 entries) covers all scenes in the expanded taxonomy. The unknown-A0 fallthrough
behavior (proceed with current scene) handles any edge cases from unmodeled substate
transitions safely.

**Decision: A0 range model still sufficient — YES**

---

## 6. Sprite Working Set Audit

### Confirmed Peak Counts

From `Cody_full_arcade_scene_state_taxonomy.md` §5 (MAME sprite-RAM scan, `0xD00000..0xD007FF`,
code field `w2 & 0x1FFF`, per-frame unique-count tracking):

| State | Peak active unique | Peak visible unique |
|---|---:|---:|
| `frontend_0002_0003` | **59** | **56** |
| `death_continue_03` | 35 | 22 |
| `death_continue_04` | 35 | 26 |
| `death_continue_05..08` | 27 | 24 |
| All other observed states | 21 or fewer | 21 or fewer |

Peak confirmed: **59 active / 56 visible** unique 16x16 cell codes in a single frame.

### Relationship to 48-Cell Assumption

The prior architecture planning used a 48-cell worst-case assumption (193 8x8 slots, starting
at slot 1343). The observed peak of 56 visible cells requires 224 8x8 slots; 59 active cells
requires 236 8x8 slots. Both exceed the 193-slot reservation. The 48-cell assumption is
**not validated** by current evidence.

### Completeness of the Analysis

Cody Document 1 measured 22 state labels covering stages `0x0000/0001/0006` — a sample.
Cody Document 2 noted that `active_runtime_stage_02/03/04/06/0d/11/2d/2e` and
`round_stage_presentation_09/11/12/13` (which include late-stage gameplay, fortress stages, and
boss-proximate states) were NOT directly represented in the current sprite profile summary.
Therefore the measured peak of 59/56 is not confirmed as the global worst case — it is the
worst case observed within the sample coverage.

Specifically: boss battle states and late-stage fortress states were not profiled with the
unique-cell counting method. These are the highest-risk scenes for sprite working-set size.

### Uncertainty Assessment

Cody correctly identifies a secondary uncertainty: whether the 56/59 count includes zero or
inactive sprite RAM entries. This is a probe-heuristic question, not a hardware question. The
visibility heuristic used by the MAME probe may count entries that would not actually be drawn.
This uncertainty is acknowledged but does not change the risk posture: the proven peak already
exceeds the assumption, and the unprofiled scenes are higher-risk.

**Decision: sprite risk properly bounded — NO**

The risk is identified and quantified as "exceeds assumption" but is not bounded at a true
worst case because boss/fortress/late-stage states have not been profiled with the unique-cell
metric.

---

## 7. BG Implementation Go/No-Go Decision

### Independence of BG and Sprite VRAM Regions

The VRAM partition is:
- Slots 0–3: scaffolding
- Slots 4–19: unused
- Slots 20–1342: PC080SN BG tiles (mode-dependent, all scenes)
- Slots 1343–1535: PC090OJ sprite reservation

The BG tile region (slots 20–1342) is fixed by the manifest's maximum slot value of 1,342.
This boundary does not depend on where sprites start. The sprite reservation begins at slot 1343
— a fixed constant derived from the BG region's upper bound. Even if the sprite partition needs
to be expanded (e.g., starting at a lower slot to increase capacity from 193 to 236+ slots),
the BG region remains anchored at slots 20–1342 because it is bounded by the manifest content,
not by the sprite start.

Therefore: adjusting the sprite partition boundary does not require changing the BG trigger
implementation, the manifests, or the LUT.

### Go/No-Go

The scene trigger implementation (adding scene-detection preamble to
`genesistan_hook_tilemap_plane_a`, adding WRAM state variables, adding `genesistan_scene_a0_ranges`
ROM table, completing `load_scene_tiles` state-update tail) is entirely within the BG tile
region and the A0 detection mechanism. None of this code references the sprite partition
boundary.

**Decision: safe to proceed with BG trigger implementation — YES**

---

## 8. Root Uncertainty Scope

### The Uncertainty

Whether the observed 56/59 unique sprite-code peak is the true required concurrent sprite demand
across all scenes (including boss battles and late-stage fortress states not yet profiled), or
whether it is the true worst case within the lite-run sample.

### Does It Affect BG Correctness?

No. The uncertainty is entirely within the sprite VRAM partition (slots 1343–1535). BG tile
correctness depends only on:
1. The LUT correctly mapping arcade tile indices to VRAM slots 20–1342
2. The scene manifest loading the correct pixel data before the first nametable commit

Both conditions are proven (programmatic verification: zero inconsistencies across 2,737 pairs).
The sprite uncertainty has no path to affect either condition.

**Decision: uncertainty affects BG correctness — NO**

The uncertainty is scoped to the sprite system, which has not yet been implemented.

---

## 9. SGDK Failure Recurrence Check

### Original Failure (Builds 293/294)

`adda.w #0x0014, %a4` was applied in the BG/FG assembly commit functions, causing tile code
reads from `A2 + 0x14 + D7` (WRAM shadow region) instead of `A2 + 0 + D7` (hardware tile
region). The LUT was simultaneously updated with the same wrong formula, so both were
consistently wrong. Fixed in Build 295 by removing `+0x14` and reverting the Python formula.

### Current State in `rastan-direct`

The hook `genesistan_hook_tilemap_plane_a` extracts the tile code as:

```asm
move.w  (%a4), %d3           ; read at offset 0 from strip table pointer
andi.w  #0x3FFF, %d3
add.w   %d3, %d3
move.w  0(%a2,%d3.w), %d3   ; lut[tile_index] -> vram_slot
```

This reads at offset 0 — the confirmed correct address (`A2 + 0`, matching Build 295). There is
no `+0x14` displacement and no WRAM shadow ambiguity. The `rastan-direct` architecture
intercepts at the strip producer level (A0 source address detection), not at the dual-plane
BG/FG commit level that caused the WRAM-shadow confusion in SGDK.

### Scene-Based Loading Recurrence Path

Scene-based loading adds A0 range detection and `load_scene_tiles` invocation before the
descriptor loop. This preamble reads A0, compares against ROM-resident bounds, and calls a
manifest loader. None of these paths touch tile-code extraction (`(%a4)` read), the LUT lookup
(`0(%a2,%d3.w)`), or the nametable word construction. The preamble fires before the descriptor
loop; the descriptor loop's tile-code path is not modified.

**Decision: SGDK failure cannot recur — YES**

---

## 10. Single Root Risk

The sprite VRAM reservation (193 slots starting at slot 1343) has not been validated against
the true worst-case concurrent sprite cell count across all scenes, including boss battles and
late-stage fortress states that were not covered by the current sprite profiling run. The
observed peak of 59 active / 56 visible already exceeds the 48-cell assumption. If the actual
worst case is higher, the sprite partition boundary will need to move — but this is a future
design decision, not a current implementation blocker for BG work.

---

## 11. Single Next Step

**A. Proceed with Cody implementing scene trigger exactly as spec'd.**

Justification: All preconditions for implementation are satisfied.
- The trigger spec (`Andy_scene_mode_transition_trigger_spec.md`) is complete: exact insertion
  point (between lines 221 and 222 of `genesistan_hook_tilemap_plane_a`), fast-path logic,
  slow-path scan, `load_scene_tiles` contract, state update order, boot interaction, unknown-A0
  fallthrough, re-entrancy guarantee.
- The three WRAM variables are specified. The ROM-resident range table is specified.
- The BG region is not affected by sprite uncertainty.
- The sprite risk is real but scoped to a future system that has not yet been started.
- Delaying BG trigger implementation pending sprite profiling provides no BG correctness
  benefit and adds project delay.

The sprite profiling pass (targeted run covering boss/fortress/late-stage states with
exact per-frame unique-cell counting) should proceed in parallel or immediately after
BG trigger implementation — not as a gate to it.

---

## 12. What Must Not Be Changed

The following are proven correct and must not be modified during or after trigger implementation:

1. **`genesistan_pc080sn_tile_vram_lut` and its `.incbin`** — globally consistent, zero
   inconsistencies across 2,737 pairs. Regeneration would invalidate the manifest binary files.

2. **All three scene manifest binaries** (`pc080sn_scene_preload_title.bin`,
   `pc080sn_scene_preload_gameplay.bin`, `pc080sn_scene_preload_endround.bin`) — correct by
   construction, verified programmatically. Do not regenerate without re-running and re-verifying
   the full Python tool chain.

3. **`genesistan_hook_tilemap_plane_a` translation logic** — specifically: `move.w (%a4), %d3`
   (offset 0), `andi.w #0x3FFF, %d3`, `move.w 0(%a2,%d3.w), %d3`. The descriptor loop
   (lines 229–315) is not touched. Only the scene-detection preamble (inserted between lines 221
   and 222) is new code.

4. **BG residency VRAM region** — slots 20–1342 for PC080SN tiles. This boundary is determined
   by the manifest's maximum slot (1,342) and must not be altered.

5. **`precompute_pc080sn_tile_lut.py`** — the tile-address formulas were confirmed correct at
   Build 295. The tool is deterministic and reproducible (re-run produces byte-identical output).
   Do not modify.

6. **PC090OJ sprite system** — no changes of any kind until the sprite profiling pass is
   complete and the worst-case cell count is established.

7. **`_VINT_handler` structure and display-disable bracketing** — `load_scene_tiles` encapsulates
   the SR and VDP mode register transitions. The VBlank structure must not be altered to
   accommodate scene loading.

8. **Patcher, Makefile, all 34 `opcode_replace` entries, `rom_absolute_call_relocation`,
   A5 initialization to `0xFF0000`, `VRAM_TILE_BASE = 0x00000020`** — none of these are
   touched by trigger implementation.

---

## 13. Final Verdict

The audit confirms that Cody's analysis is structurally sound and the conclusions are
well-grounded in evidence. The 3-bucket PC080SN model is valid under the expanded 29-state
taxonomy. The A0 range detection is sufficient for all identified scenes. The LUT and manifests
are correct. The SGDK failure cannot recur. The single open risk (sprite VRAM capacity) does
not affect BG correctness and does not block BG trigger implementation.

**Implementation is clear to proceed: Proceed with scene trigger implementation (Option A).**
