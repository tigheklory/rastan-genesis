# Cody — Full Arcade Scene/State Taxonomy + Sprite Validation (Prompt 207R)

## Executive Summary

I re-derived the current scene/state taxonomy from arcade-side evidence (disassembly + MAME runtime traces) and re-checked BG/Sprite VRAM assumptions.

Key result:
- The **3-bucket PC080SN residency model** (Title/Attract, Gameplay, End-Round) is still structurally correct for BG source ranges.
- The current **"48 unique 16x16 sprite cells worst-case"** assumption is **not validated** by current evidence. In one observed frontend substate (`frontend_0002_0003`), the MAME sprite-RAM probe measured **56 visible unique codes** in one frame.

So the architecture risk is now sprite-side validation, not BG bucket shape.

## Inputs Audited

- `build/maincpu.disasm.txt`
- `build/regions/pc090oj.bin`
- `build/regions/pc080sn.bin`
- `docs/design/Andy_scene_mode_transition_trigger_spec.md`
- `docs/design/Cody_independent_vram_budget_verification.md`
- `AGENTS_LOG.md` tail
- MAME runtime trace artifacts:
  - `build/mame/home/rastantrace_lite/rastan_exec_trace_lite.log`
  - `build/mame/home/rastantrace_lite/rastan_exec_summary_lite.txt`
  - fresh profiling run output:
    - `build/mame/home/rastantrace_lite/rastan_sprite_profile_summary.txt`

Note on MAME source files (`rastan.cpp`, `pc090oj.cpp`, `pc080sn.cpp`): direct network fetch was unavailable in this session. For source-level semantics, I used already-audited extracted facts in the existing local design notes plus live MAME behavior from runtime traces.

## 1. Residency Bucket vs True Arcade Scene (Task 1)

`residency bucket` and `scene/state` are different layers:

- Residency bucket (BG/PC080SN loading policy):
  - Scene 0: Title/Attract
  - Scene 1: Gameplay
  - Scene 2: End-Round
- True arcade runtime state taxonomy (state machine):
  - many frontend/runtime substates (`frontend_*`, `runtime_mode_*`, `death_continue_*`, etc.)

Conclusion: buckets are a coarse VRAM policy; runtime states are finer-grained control flow and behavior.

## 2. Arcade State Model (Task 2)

Disassembly and runtime labels show state control rooted in WRAM mode/state words around `0x10C000` + control words near `0x10D3AA`.

Evidence points:
- scene range ownership (from source-scene map and Andy trigger spec):
  - scene 0: `0x05A7DA..0x05B0B2`
  - scene 1: `0x056A22..0x0570C2`
  - scene 2: `0x05822A..0x059614`
- runtime labels from MAME trace (`rastan_exec_trace_lite.log`) include:
  - `frontend_title_or_attract`, `frontend_credit_ready`, `frontend_0002_0003`,
  - `wait_for_play`, `runtime_mode_0002/0003/0004/0008`, `runtime_0001`, `runtime_0006`,
  - `death_continue_01..08`.

This confirms multi-substate runtime behavior beneath the 3 BG residency buckets.

## 3. Full Candidate Scene/State List (Task 3)

### Proven observed states (trace)

- Frontend cluster:
  - `frontend_title_or_attract`
  - `frontend_credit_ready`
  - `frontend_0000_0001`
  - `frontend_0002_0000`
  - `frontend_0002_0002`
  - `frontend_0002_0003`
  - `frontend_0002_0004`
- Transition/wait:
  - `wait_for_play`
- Runtime/play substates:
  - `runtime_mode_0002`
  - `runtime_mode_0003`
  - `runtime_mode_0004`
  - `runtime_mode_0008`
  - `runtime_0001`
  - `runtime_0006`
- Continue/death sequence:
  - `death_continue_01` through `death_continue_08`

### Candidate inferred but not captured in this run

- `round_presentation_09..13` (exists in state-label logic, not seen in sampled run)
- Scene-level labels requested by design planning:
  - stage intro
  - outdoor gameplay
  - fortress gameplay
  - boss
  - game over
  - ending

These likely map onto combinations of runtime/death/frontend substates and stage words, but remain unproven in this capture window.

## 4. PC080SN Residency Classification by Scene (Task 4)

| Candidate scene | Classification | Basis |
|---|---|---|
| Title / attract / credit / frontend variants | A (distinct BG residency) | Source ranges and scene map place these under scene 0 |
| Gameplay (runtime modes, stage play) | A (distinct BG residency) | Source ranges for scene 1 are disjoint |
| End-round / continue sequence | A (distinct BG residency) | Source ranges for scene 2 are disjoint |
| Internal frontend/runtime substates within each bucket | B (reuse same bucket) | They vary logic/UI but not proven to require separate PC080SN preload buckets |
| Ending (if distinct ROM source not yet captured) | C (uncertain) | Not directly observed in this run |

## 5. PC090OJ Working Set Per Scene/State (Task 5)

Method used: MAME sprite-RAM scan (`0xD00000..0xD007FF`), code field `w2 & 0x1FFF`, per-frame unique-count tracking by runtime state label.

### Observed per-state peaks (unique 16x16 cell codes)

| State | Peak active unique | Peak visible unique | Observed code range |
|---|---:|---:|---|
| `frontend_title_or_attract` | 21 | 18 | 42..73 |
| `frontend_0000_0001` | 21 | 18 | 42..73 |
| `frontend_0002_0000` | 21 | 18 | 42..73 |
| `frontend_0002_0002` | 21 | 18 | 42..73 |
| `frontend_0002_0003` | **59** | **56** | 42..2722 |
| `wait_for_play` | 21 | 21 | 42..73 |
| `runtime_mode_0002` | 21 | 18 | 42..73 |
| `runtime_mode_0003` | 18 | 15 | 42..73 |
| `runtime_mode_0004` | 18 | 15 | 42..73 |
| `runtime_mode_0008` | 18 | 15 | 42..73 |
| `death_continue_01` | 21 | 18 | 42..73 |
| `death_continue_03` | 35 | 22 | 42..2672 |
| `death_continue_04` | 35 | 26 | 42..2672 |
| `death_continue_05` | 27 | 24 | 42..2665 |
| `death_continue_06` | 27 | 24 | 42..2665 |
| `death_continue_07` | 27 | 24 | 42..2665 |
| `death_continue_08` | 27 | 24 | 42..2665 |

Required checks:
- per-scene sprite working set derived: YES (for observed states)
- any scene exceeding 48 cells identified: YES (`frontend_0002_0003`, 56 visible / 59 active)

## 6. PC090OJ Tile Index Usage Per Scene (Task 6)

Observed usage is clustered, scene-dependent, and sparse (not dense full-range):

- Low cluster-heavy states (title/wait/runtime_mode small states): mostly `42..73`
- Expanded cluster states (`death_continue_*`, `frontend_0002_0003`): extend into `~2665..2722`
- Full observed range in this sample: `42..2722`

Cross-reference against allocation (`slots 1343..1535`):
- slot count determines concurrent residency capacity (193 8x8 slots = ~48 cells), independent of raw code value.
- because one observed state exceeds 48 unique 16x16 codes, current partition is not yet proven safe.

## 7. Sprite VRAM Budget vs Current Partition (Task 7)

Current partition assumption under review:
- sprite area equivalent capacity: ~48 unique 16x16 cells (193 slots)

Observed peak in this analysis:
- `frontend_0002_0003`: 56 visible unique / 59 active unique

Implication:
- 56 cells x 4 = 224 8x8 slots
- 59 cells x 4 = 236 8x8 slots
- both exceed 193-slot reservation

So the current sprite budget is **not validated safe** across all observed states.

## 8. 3-Bucket Sufficiency Check (Task 8)

- For PC080SN BG residency: **likely sufficient** (3 disjoint source ranges are well-supported).
- For full architecture safety: **insufficient alone**, because sprite working-set pressure varies by substate and can exceed assumed sprite capacity even when BG bucketing is correct.

## 9. MAME Correlation (Task 9)

### Proven

- Runtime-state labels and transitions are multi-substate, not just 3 states (`rastan_exec_trace_lite.log`).
- Sprite RAM activity is substantial and state-dependent (`d00000` window changes in summary, plus profiler output).
- Observed sprite code range spans far beyond minimal UI glyph range in at least one frontend substate.

### Inferred (needs one tighter confirmation pass)

- Whether the 56/59 peak is fully onscreen-required payload vs partial overcount from simplified visibility heuristic (still actionable as a risk indicator).
- Exact mapping of every inferred high-level scene name (outdoor/fortress/boss/ending) to specific runtime substate labels in this capture.

## 10. Rainbow Islands Comparison (Task 10)

- Rainbow Islands guidance in this repo is scene/bucket-aware for BG publication ownership.
- Rastan currently matches that at the coarse BG bucket level (three disjoint ranges),
- but sprite safety requires finer per-substate validation than a coarse bucket-only assumption.

Conclusion: Rastan aligns with Rainbow-style bucket discipline for BG, but needs tighter sprite working-set validation before declaring VRAM partition final.

## 11. Single Root Uncertainty (Task 11)

Whether the observed 56/59 unique sprite-code peak in `frontend_0002_0003` is the true required concurrent sprite set under exact PC090OJ visibility/priority semantics, or a conservative overcount from the current probe heuristic.

## 12. Single Verified Next Step (Task 12)

**Collect one additional dataset**: run one targeted MAME-side sprite profiler pass that mirrors `pc090oj` draw inclusion criteria exactly (same visibility/active rules as MAME draw path) for the high-risk substates (`frontend_0002_0003`, `death_continue_*`, runtime gameplay/boss transitions).

Reason: current evidence already disproves "48 is obviously safe", but this one precision pass is needed before choosing between partition redesign and keeping current split.

## Final Verdict

- Scene taxonomy correctness: partially proven at two levels:
  - coarse 3-bucket BG model: strong evidence
  - fine-grained runtime state machine: clearly richer than 3 states
- Sprite VRAM safety: **not yet validated**. Current observed data contains at least one state above the 48-cell assumption.

No implementation was performed.
