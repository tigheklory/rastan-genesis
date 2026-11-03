# Andy — R1/P1 Sprite Semantic Completion + 58-Cell Packing Proof

**Task:** architecture / targeted Ghidra / actor-lifetime / offline packing. **No production code, no
ROM, counter 356.** Cody handed off after proving the 58-cell physical VRAM ceiling; this closes the
semantic/packing question on top of it. Companion to
`Andy_sonic_style_sprite_context_architecture.md`. Machine-readable outputs under
`analysis/graphics_optimizer/round1_phase1_corpus/generated/`.

## 0. Baseline
EXTENDING · Baseline Build 0356 · counter 356 · next 0357 · production NO · ROM NO ·
Cody 58-cell ceiling **ACCEPTED** · observed raw peak **63** · readiness **BLOCKED** ·
A-13 **OPEN / CODY-OWNED**.

## 1. Headline result — 58 FAILS, and per-owner regions are infeasible

Two candidate residency models, both computed from the original-arcade trace
(`analyze_r1p1_sprite_packing.py`), both exceed 58:

| Model | Peak cells | vs 58 | vs 63 raw | Verdict |
|---|---:|---|---|---|
| **Shared frame-specific pool** (minimal — pool holds exactly the on-screen distinct tiles) | **61–63** | FAIL by 3–5 | = raw peak | needs per-frame placement |
| **Per-owner fixed regions** (clean Sonic `obGfx`, each family a permanent base) | **~126** | FAIL by ~68 | ~2× | **INFEASIBLE** |

**Why time-based tricks cannot rescue 58.** Overlays/aliasing/epoch reuse only reclaim cells across
*time* — between owners that are never simultaneously on screen. The R1/P1 overflow is **within single
frames**: at the peak, 61–63 *distinct* codes are displayed *at the same instant*, and one displayed
code = one resident 16×16 cell (proven §5e of the companion doc). No offline remapping reduces a
single frame's simultaneous distinct-tile count. So **the physical floor is the peak single-frame
displayed-distinct-tile count**, not a packing artifact.

**Why per-owner regions blow up.** A family's region must hold its *multi-instance union* (all live
instances' current frames). Summed over the owners co-present at the demon peak frame (frame 7428,
section 09): CORE(player/HUD/weapons/effects) + FLYING_DEMON 25 + INSECT 22 + CHIMERA 19 + VALKYRIE 8
+ boulder/proj ≈ **126 cells**. The clean Sonic-style per-object-base model simply does not fit
Rastan's simultaneous large-vocabulary enemy density. This is a real structural difference from Sonic
(which never co-displays this many distinct large sprite families).

**Consequence for the "pure offline, zero runtime decision" goal:** it is **not achievable for R1/P1
within feasible VRAM**. Per-owner regions (fully offline, O(1)) need ~126 cells; the minimal shared
pool (61–63) inherently needs per-frame placement that cannot be fully offline-enumerated
(actor × frame combinatorics) without either per-context maps or a bounded runtime residency step.
The current build's bounded residency pool is therefore solving a *real* problem, not merely legacy
cruft.

## 2. Minimum proven cells and the Plane-A cost

- **Full-fidelity minimum: 63 cells** (raw peak, sections 06/07 = segments 6/7).
- **After the 80-entry SAT cap that BOTH platforms impose** (max emitted pieces/frame = 105): the two
  >80-piece dense frames reduce to 52 and 62 distinct among the first 80 pieces, but the **demon
  frames (section 09, ≤61 pieces) get no SAT relief — 59–61 distinct tiles are all displayed**. So the
  SAT-limited irreducible floor is **61**.
- **Additional Plane-A patterns to reach it** (growing the sprite base down from pattern 1302):
  61 cells → **12 patterns** (1290..1301); 62 → 16; 63 → **20 patterns** (1282..1301) = 640 B. All of
  1282..1301 are currently Plane-A package patterns (Cody). **Plane-A reduction is OUT OF SCOPE here**
  — but the requirement is now exact.

## 3. Flying Demon — RESOLVED (was UNRESOLVED in Cody's pass)

Traced the dispatcher Cody could not classify. Switch on `d0` at **arcade_pc 0x04580C**, gated by
camera `A5@0x10B8 ≥ 160`, branches for d0 ∈ {2,3,5,6,7,9,10,13,17}. Two branches call the demon
paired-init `0x45342`, each **one-shot guarded**:

| Encounter | Spawn PC (jsr 0x45342) | One-shot flag | Proof of no-respawn |
|---|---|---|---|
| A | **0x0458C8** | sets `A5@0x264 = 1` | gated by `bsrw 0x45D10` nonzero; flag set before init |
| B | **0x045970** | sets `A5@0x25A = 1` | **`tstw A5@0x25A / bnes 0x45994`** skips if already set |

Both clear variant selector `A5@0xC5A` before init. `paired_actor_init_45342` guards on
`A5@0x548 == 0`, activates body (`A5@0x508`, recs 57–69) and wings (`A5@0x548`, recs 70–82) via
`0x453A2`, loading records via `0x4543E` (Cody's chain). Runtime PCs via `address_map.json`:
0x45342→0x045542, 0x453A2→0x0455A2, 0x4543E→0x04563E.

- **Max semantic demon instances: 1** (two fixed slots = one body + one wings; proven in companion §6a).
- **Preload-safe:** on entering the dispatcher branch before the jsr. **Spawn-committed:** the jsr.
- **Release-safe:** both paired slots inactive (`actor+0 == 0`) after being active; the one-shot flags
  (0x264/0x25A) guarantee no respawn. **Exact death-writer PC: UNRESOLVED** (paired cleanup fragmented
  in export), but the *safe release condition* is defined and does not use `section changed`.
- **May cross segment: YES** (companion §6a); **may cross phase: NO**.
- **Overlay recommendation:** the 30-cell demon region may alias onto an owner proven absent during
  *both* encounters — but see §5: no such alias is currently *proven*, and even with it the packing
  fails on the within-frame floor, so the demon overlay does not rescue 58.

## 4. Other semantics (status, honest)

- **Phase reset:** hard boundary **PROVEN behaviorally + structurally** (companion §6c): actor blocks
  A5@0x2C8/0x748/0x5C8/0x508 are per-stage program state; progression event `FUN_000558e0`
  (0x0558E0→0x0559C0) increments A5@0x13E at 0x0558FE. **Single wipe instruction NOT isolated**
  (distributed stage-init + per-frame blanking `FUN_00041dae`). The residency implication — phase is a
  safe hard reset, no enemy carry-over — does not need the exact PC.
- **Hurry-up bats: PARTIAL.** Family = Small Bat (748 block, codes 0x268–0x26A, bank 0x3E; KF-068
  swarm). **Timer/threshold/max-count UNRESOLVED** (no named function; A5@0x21C "wave" is set by the
  scheduler). Recommendation: keep the 1–3-cell Small-Bat family **permanently phase-resident**, which
  removes it from every coexistence question and makes the exact trigger irrelevant to packing.
- **Recurring families:** eligibility windows from the census `sections_records`: Lizardman ~segs
  1–15, Insect 4–15, Chimera 5–15 → **phase-resident** (another can always respawn); Valkyrie 7–9
  (narrow); Large/Small Bat scattered. Scheduler `actor_spawn_ground_and_activate_41180` (0x41180)
  is marker/camera/progression-driven; map collision markers (0x40/0x41/…) route spawns
  (`arcade_object_semantic_domain.json`).

## 5. Interference graph (empirical) and multi-instance unions

`sprite_interference_graph.json` + `sprite_multi_instance_unions.json`. Multi-instance unions (max
distinct family codes in any one frame — already includes several instances on different animation
frames): FLYING_DEMON 25, INSECT 22, CHIMERA 19, LIZARDMAN 18, VALKYRIE 8, HAZARD_ROPE 6,
LARGE_BAT/BLOCK/BOULDER 4, PROJ_SPEAR 3, effects/other small. Proven-empirical mutual exclusions
(never co-observed) include LIZARDMAN⊥VALKYRIE, VALKYRIE⊥{most projectiles/bats/effects},
HAZARD_BLOCK⊥almost everything, FLYING_DEMON⊥{COMMON_EFFECT, HAZARD_ROPE}. **These are single-capture
exclusions and must be backed by spawn/lifetime semantics before use as aliases** (task rule); most
lack that backing today, so **zero aliases are production-proven** — consistent with Cody. Aliasing
does not change the verdict because the overflow is within-frame.

## 6. DPLC model and budget

**Model: FRAME-SPECIFIC GENERATED MAP** (confirmed). Frame unchanged ⇒ no DMA. Transfer proxy
(new distinct codes vs previous trace frame; `sprite_dplc_budget.json`): median **2 cells/update**
(256 B), P95 15 (60 patterns), MAX 49 (196 patterns ≈ 6.3 KB, a context transition). Steady-state DMA
is small; transition spikes are bounded and display-off-able. So removing the runtime search does
**not** trade into excessive DMA. (Trace frames are scroll-sampled → this is an upper bound.)

## 7. Actor/frame decode status

Player path proven (Cody: 0x0540CC→0x054326→0x054492, frame IDs A5@0x1244/0x1246, body ~0x05BD40,
weapon tables 0x05CD8A/0x05D068/0x05D346/0x05D666) but table entries not fully extracted; **all enemy
+ demon frame tables UNRESOLVED**. **Python cannot yet deterministically generate frame maps** — this
is the single largest remaining offline-compiler prerequisite, independent of the VRAM blocker.

## 8. Readiness — BLOCKED

Two independent load-bearing blockers:
1. **VRAM:** minimum 61 (SAT-limited) / 63 (full) > 58; needs a Plane-A reduction of 12–20 patterns
   (out of scope) — and even at 63, per-owner regions (~126) don't fit, so the residency model itself
   needs resolution (shared pool + placement, or a retained bounded runtime step).
2. **Frame tables:** enemy/demon animation→piece decode incomplete, so the offline compiler cannot
   emit frame maps.

Neither is closed by re-analysis; both need decisions/decode, not another broad pass. See the
companion doc §13 for the checklist and the required final-response section for the full structured
result. A-13 remains Cody-owned; FINAL_CONSENSUS.md untouched; no production changes; no Test Build.

---

## 9. Palette Composer coverage (corrects the "Python can't generate frame maps" overstatement)

The **Palette Composer (Rastan Palette Composer v0.4)** is the authority for Genesis palette/reindex
and for the graphics of every pose it represents. Its repo data
(`analysis/graphics_optimizer/round1_phase1/sprite_families.json`, `sprite_frames.json`,
`sprite_class_coverage.json`) proves the split: it holds **palette/reindex + exact per-pose piece
maps** (`sprite_frames.json` gives `code, x, y, flip_h/v, pattern_hash` per composite), and the arcade
**family-dispatch chain is already identified** — `actor_family0_render_3d054` (0x3D054), family
descriptor tables at ROM `0x03D09E / 0x04771C / 0x03F0CE / 0x040004 / 0x04002C`, piece format
`[control, signed_y, code_offset, signed_x]` quartets terminated by `0x00`, effective palette bank
`((sprite_ctrl & 0xE0)>>1) | (actor_attr & 0x0F)`. So graphics + palette + the decode *mechanism* are
**not** the blocker.

What the Composer does **not** yet hold is the **complete animation-frame domain** — most families
carry only 1–4 representative composites:

| Family (repo snapshot id) | class | graphics | composites/frames | Coverage class (Part 2) |
|---|---|---|---:|---|
| rastan_player_body | resolved | resolved | 2 poses (26 cells) | **B** — palette+poses done; full walk/jump/attack domain + weapon states missing |
| gameplay_hud | resolved | resolved | 1 (43 cells) | **A/B** — HUD static; effectively complete |
| player_auxiliary | resolved | resolved | 1 (3 cells) | B |
| stage1_lizardman | resolved | resolved | 1 (35 cells) | **C** — palette+one pose; animation domain from arcade tables |
| hurry_up_bat | resolved | resolved | 4 (3 cells) | **A/B** — small, well covered |
| family0_class70_actor, family2_round1_actor_cluster | unresolved class | resolved gfx | 1 each | C |
| normal_small_bat, large_bat, four_armed_enemy, projectile_weapon, transient_effect, axe/item routes, collision-marker routes | unresolved | unresolved | 0 | **C/D** — need arcade decode |

The live v0.4 tool (per Tighe) additionally carries **Flying Demon (body+wings), bank 0x35**, with
palette/reindex + arcade source colors + a decoded true-arcade composite of **one 25-piece pose** —
authoritative for demon *appearance/palette/reindex*, **not** its full animation sequence (contrast
Rastan body's explicit poses). So for the demon: **palette/reindex = COMPLETE; one representative pose
= YES; complete animation domain = NO** — remaining work is enumerating the encounter's animation
frames + the body/wings frame selector, **never** re-deriving demon colors/reindex.

**Corrected DPLC prerequisite:** Python can already emit the piece→pattern map for **every represented
composite**, and the decode mechanism (dispatch + descriptor tables + quartet format) is known.
The remaining offline work is (a) enumerating each family's **full legal frame set** and (b) binding
the **runtime frame-selector** state — not graphics/palette reconstruction. This is narrower than
"frame tables unresolved."

## 10. The eight >58 frames (explicit proof)

| frame | seg | pieces | first-80 | distinct (all) | distinct (first-80) | demon? |
|---:|---:|---:|---:|---:|---:|---|
| 3201 | 6 | 105 | 80 | 63 | 52 | no |
| 6485 | 7 | 87 | 80 | 63 | 62 | no |
| 7428 | 9 | 61 | 61 | 61 | 61 | **yes** |
| 7423–7429 (run) | 9 | 59 | 59 | 59 | 59 | **yes** |

- **Full arcade-producer requirement:** up to **63** distinct graphics identities (frames 3201/6485).
- **Genesis 80-SAT-constrained requirement:** frames with >80 emitted pieces (only 2) are truncated by
  *the Genesis renderer's own* 80-entry SAT, dropping their distinct-in-first-80 to 52 and 62. The
  demon frames have <80 pieces, so no Genesis truncation applies — **61 distinct tiles are all
  genuinely displayed** → **irreducible Genesis floor = 61**.
- **SAT-limit caveat (Part 7):** this "first-80" is the *Genesis* SAT cap only. PC090OJ's own object
  limit is **not** proven numerically equal; do **not** claim identical hardware culling. The correct
  reading: full arcade producer emits up to 63 distinct; our Genesis renderer after its own 80-SAT
  truncation still needs **61**.

## 11. Residency-model comparison (the real decision)

| Model | Peak VRAM | Runtime | Verdict |
|---|---:|---|---|
| **1. Permanent per-owner bases** (pure Sonic `obGfx`) | ~100–126 (est., §5 caveat) | simplest, O(1), no search | **NOT VIABLE** — far exceeds 58/63 |
| **2. Offline context/package maps** | fits stable owners only | select layout pointer, O(1) | insufficient alone — enemy combinations are combinatorial, and any single context still peaks 61–63 |
| **3. Bounded reverse-index shared pool** | 58 (as today) | **O(1) `code→slot`** + bounded deterministic replacement/upload | **VIABLE** — kills the linear-search hotspot, keeps residency Rastan needs |
| **4. HYBRID** (fixed bases for player/HUD/effects/hurry-up + small stable families; bounded reverse-index shared region for the large co-present enemy families) | 58 (or 61–63 with Plane-A reduction) | O(1) throughout; offline fixes the stable part and informs enemy replacement | **RECOMMENDED** |

**The ~126 per-owner figure is a bounded architectural estimate, not exact** — owner attribution
covered 477/842 observed codes; player/HUD/weapons were lumped (CORE≈46) and ambiguous codes counted
conservatively. But even the *attributed enemy families alone*, co-present at the demon frame
(DEMON 25 + INSECT 22 + CHIMERA 19 + VALKYRIE 8 = 74) plus a realistic player/HUD/effects core
(~25–30), give **~100+ cells** — robustly proving Model 1 does not fit any feasible sprite VRAM. Treat
126 as an upper-ish estimate; the load-bearing claim ("permanent per-owner ≫ capacity") holds at the
conservative ~100 lower bound too.

**Recommendation: Model 4 (hybrid).** It is the only model that both (a) eliminates the measured
49-slot linear-search hotspot (the primary performance goal) and (b) fits Rastan's proven simultaneous
enemy density. The pure Sonic per-owner analogy (old "Architecture C") is **retired** for R1/P1.
