# PROMPT-ID-0050 — Independent Review of Cody 0045, Bottom-Up Castle Scrolling, Rope Regression

**Author:** Andy · **Date:** 2026-11-01 · **Method:** READ-ONLY peer review from original-arcade 68000
instructions, maintained C, Ghidra exports, current Genesis source, and Tighe's arcade MAME screenshots.
Reference ROM: Build 0525. Concurrent: Cody PROMPT-ID-0049. Scope: Round 1.

**No implementation.** No Genesis ASM/C/remap/Composer/`Test.json`/palette/asset/audio/generated-data/
build-script/benchmark-script/save-state/ROM/counter change. No benchmark rerun. Deliverable: this report +
an append-only `AGENTS_LOG.md` entry. No new C decompilation was required (existing maintained corpus and raw
disassembly were sufficient).

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0050`

**Classification used throughout:** **PROVEN** (instruction/data-backed) · **SUPPORTED HYPOTHESIS** ·
**UNRESOLVED** · **CONTRADICTED**.

---

## 1. Executive verdict

- **The better P0 explanation is Cody's incremental source-selection hypothesis, not my 0046 ring-geometry
  hypothesis.** I **retract** my 0046 recommendation to consider a 64×64 plane. A 64×32 Genesis plane is
  **sufficient** for R1-S2: 28 visible rows (224 px NTSC) + a 4-row scroll margin fit within 32 physical
  rows, and **no physical-ring collision has been demonstrated**. The defect is far more likely the
  incremental *which-logical-row* selection / projection across the selector-path split Cody identified
  (records 17/21 precompiled selector-1 `pan_row_maps`; records 18–20 dynamic selector-0), with the likely
  first divergence at the 17→18 transition. **SUPPORTED HYPOTHESIS.**
- **Scroll ownership (dispute resolved from instructions):** `A5+0x10AE` **is** the FG/Plane-A Y scroll
  (`0x55ACC: movew %a5@(0x10AE),0xC40002`). `A5+0x10B0` is the **BG/text-layer** Y scroll
  (`0x55AC4: movew %a5@(0x10B0),0xC20002`). **Cody's "`A5+0x10B0` = live Plane A Y" is CONTRADICTED.** My
  0046 was correct on this field. **PROVEN.**
- **Wizard scope corrected:** wizards are later-round enemies and **do not appear in R1-S2**. My 0046
  wrongly listed wizard identification as an R1-S2 requirement. **Corrected here; removed from scope.**
- **Rope 795→799 (+4, deterministic):** factual and reproducible. It correlates with Build 0525's restored
  scene-entry Plane A replay, is **NOT proven** to be a CPU slowdown, and is most plausibly scene-entry
  replay/scheduling latency inside the measured interval. The benchmark *script* is unchanged since Build
  426, so test-script drift is ruled out; the *first-divergent-frame* cause is **UNRESOLVED** pending an
  observation-only differential capture. **SUPPORTED HYPOTHESIS + UNRESOLVED.**
- **Armored-man identity:** the arcade screenshots show the R1-S2 "armored men" as **green-armored sword
  knights**, full multi-piece walking warriors in groups. Their **living base is UNRESOLVED**; it is **not**
  `0x0A73`, which is the state-0x0F **death/impact** animation base. Cody and I agree this is unproven from
  the death base.

---

## 2. Cody 0045 findings that are PROVEN

- **R1-S2 Plane A defect is not missing-pattern/palette.** Agrees with arcade evidence and my 0046. **PROVEN.**
- **Producer-path split exists** in `tilemap_hooks.s`: full-ring replay at entry/respawn
  (`genesistan_plane_a_scene_scroll_reseed_native`, replaying the saved fill selector `A5+0x132C` over all
  strips after rewinding the 16 descriptor pointers); selector-1 records 17/21 copy a 64-word row from
  `genesistan_plane_a_pan_row_maps`; selector-0 records 18–20 use the dynamic resolver. I confirmed the
  `A5+0x132C` saved-selector replay against the arcade Y updater `0x557BA` (which reads `A5+0x132C` at
  `0x557DC`). **PROVEN (path structure).**
- **The prior zero-mismatch gate is not independent:** `verify_r1s2_selector1_scroll.py` compares the
  compiler product to itself. Correct critique. **PROVEN.**
- **No existing runtime capture reaches the natural 17→18→19→20→21 progression** (PROMT-0012/0022 stopped by
  record 17). **PROVEN** (consistent with the repo's capture inventory).
- **Gray-border mechanism:** per-scene palette export placed `0x0888` at CRAM[0]. **I independently verified:
  `build/palette_export/cram/PAL-R1-S1-PLANEA-OUTDOOR.bin` first word = `0x0888`; `test_palette_line0.bin`
  (Build 0508) first word = `0x0000`.** CRAM[0] is the VDP backdrop (reg 7 → palette 0 / color 0), so the
  gray border follows. **PROVEN.**
- **R1-S3 boss body `0x061D`, record type `0x0E`, compositor 1.** Matches `boss_round_rectype_444e0[0]=0x0E`
  → base via `0x45592[6]` = `0x061D`. **PROVEN** (agrees with my 0046).
- **R1-S3 Plane A has a 219-usage corpus (banks `$008/$019`), no `Test.json` context; `AuthoredLayerA.SCENES`
  realizes only records 0–15, 16–21.** **PROVEN** (consistent with my 0046 round-axis gap finding).
- **Line 2 is arcade-owned for Plane B** (`specs/palette_subround_map.json` marks PLANEB nonauthorable).
  **PROVEN.**

## 3. Cody 0045 findings that remain HYPOTHESES

- **First divergence at the selector-1→selector-0 transition into record 18** (hyp #1, "high"). Plausible and
  the best-supported, but the first bad cell is **not captured**. **SUPPORTED HYPOTHESIS.**
- **Selector-1 compiled logical origin/axis transform is itself phase-shifted** (hyp #2,
  `destination_row=(15−descriptor_column)*4+descriptor_row` with axis swap). Possible; the non-independent
  gate would hide it. **SUPPORTED HYPOTHESIS / UNRESOLVED.**
- **P2 tile-residency / 12-cell DMA-worklist saturation as the primary armored corruption** (hyp #1, "high").
  Plausible but unproven; see §13 for the discriminator. **SUPPORTED HYPOTHESIS.**
- **Boss music: "The Devil Boss Carnival" track present but reachable only via a diagnostic selector; no
  authentic command map.** **SUPPORTED HYPOTHESIS** (agrees with my 0046; exact command UNRESOLVED).

## 4. Cody 0045 findings CONTRADICTED by arcade source

- **"live Plane A Y `A5+0x10B0`"** (Cody §P0 "Exact next diagnostic", bullet "live Plane A Y `$10B0`"):
  **CONTRADICTED.** Instruction `0x55AC4` commits `A5+0x10B0 → 0xC20002` (BG/text layer Y), while
  `0x55ACC` commits `A5+0x10AE → 0xC40002` (FG/Plane A Y). The Plane-A Y that drives row streaming is
  `A5+0x10AE` (updated by `0x55832`/`0x55854`, 8-px trigger via `A5+0x10B2`). **A capture that reads
  `0x10B0` as the Plane-A scroll would read the wrong plane's scroll field** — this must be fixed in the
  §10 capture spec before it is run.
- Note: Cody's capture list also cites "`strip group/index $10CC/$10CA`" and "`$10A8` selector." `0x10CA` =
  strip (PROVEN, `0x558A2`); `0x10CC` = the companion used to form the name-table row base at `0x5580A`
  (PROVEN); `0x10A8` = **section-kind gate** (0 outdoor / ≠0 castle; `0x557C4`), which is *not* a 0/1/2
  "selector" — the selector-0/1/2 terms are the **Genesis** producer's categories, with no single arcade
  field of that name. Minor labeling, not a substantive error, but the capture should record `0x10A8` as the
  section-kind gate, not as "the selector."

## 5. Corrections to my previous Andy 0046 conclusions

- **RETRACT the 64×64 recommendation.** 0046 presented the 64-row-arcade vs 32-row-Genesis mismatch as the
  "single strongest divergence candidate" and floated promoting Plane A to 64×64. That was **not justified by
  a proven limitation**. 28 visible + ~4 margin ≤ 32 rows; incremental row replacement represents a taller
  world in 32 physical rows; no ring collision was ever demonstrated. The real suspect is incremental
  source-selection/projection (§2/§3). **This aligns me with Cody.**
- **RETRACT "phase doubling" as an inherent defect.** The arcade Y wraps mod 512 and a 64×32 Genesis plane's
  name lookup wraps mod 256; this is only a defect if the producer mismaps logical→physical, not inherently.
- **CORRECT the wizard scope** (§1). Wizards are later rounds; removed from R1-S2/R1-S3 requirements.
- **KEEP (vindicated):** `A5+0x10AE` = FG/Plane-A Y (§4); `0x0A73` = death/impact anim, not the living
  armored base (§12); R1-S3 boss `0x061D`, palette pool 11; R1-S3 round-axis authoring gap.

## 6. Bottom-left spawn and upward-progression coordinate analysis

**Prompt caution honored: a bottom-left *screen* spawn is not a bottom-left *world* origin.** Proven from the
68000:

- **FG Y init field owner is `A5+0x10AE`** (not assumed): `arcade_504fa` loads
  `table_50850[g_prog13e].word0 → A5+0x10AE` and `A5+0x10EC`; `0x10AE` is the field the commit `0x55ACC`
  writes to `0xC40002`. The reported init **`0x0160` (352 px)** is therefore the **FG Y scroll**, = **ring
  row 44 of 64** (`352/8`). **PROVEN.** So R1-S2 begins with the viewport *high* in the 512-px ring, **not**
  at row 0 — the world origin is not where the on-screen bottom-left spawn is.
- **Scroll direction (PROVEN):** up branch `0x55854` does `A5+0x10AE += step` and sets row-stream mode **2**
  (`0x55890`); down branch `0x55832` does `A5+0x10AE -= step` and sets mode **3** (`0x55842`); each fires one
  `0x406A4` row stream per 8-px crossing (`A5+0x10B2` bit3, `0x557F8`).
- **Newly exposed rows during a climb:** each 8-px crossing streams exactly one map row via `0x406A4`; the
  descriptor source for that row is rebuilt by `0x55904` through `0x558A2` (strip `0x10CA` 0..3; the 16
  column pointers advance +4 every 4 strips), with the name-table destination row base computed at
  `0x5580A` from `A5+0x10CC`/`A5+0x10CA`. The scene index `A5+0x013E` advances only after a full 0x40-byte
  descriptor page (16 entries) is consumed — i.e., **vertical row exposure is camera/scroll-driven, and
  progression advances downstream.** **PROVEN.**
- **Arcade screenshot corroboration (independent oracle):** Tighe's **second** screenshot set (ARCADE,
  ROUND-1 castle) shows the climb as bottom→top with a fixed **fire archway** that scrolls *downward* in
  screen space as Rastan climbs, consistent with newly exposed rows entering at the top. The arcade keeps the
  archway, the twin-flame candelabra, the stepped ledges, and the right-edge ladder/rope spatially coherent
  throughout — this is the authoritative placement reference (landmark-level; see §9/§10). The **first** set
  (GENESIS/BlastEm, Build 0525) renders the *same* landmarks (fire archway, candelabra, ladder, green
  sword-knights, gray+green masonry), i.e. the **artwork/palette is correct**; this is consistent with a
  *positional/intermittent* defect rather than wrong art, but the two sets are **not camera-matched**, so no
  specific misplacement is asserted from them.

**UNRESOLVED (the precise item the capture must settle):** the **sign that maps "player climbs up in the
world" to increment vs decrement of `A5+0x10AE`**, and therefore **which end of the descriptor sequence feeds
a climb-exposed row** (relevant to Cody's selector-1 reverse-row transform `63−(group*4+strip)`). The
player-motion → direction-accumulator (`0x51880 → A5+0x10B8`) sign is the deciding input and is not settled
statically here. This is exactly the axis/origin question that distinguishes Cody's hyp #1 from hyp #2.

## 7. Instruction-backed scroll-field ownership

| A5 field | Role | Proof (instruction) |
|---|---|---|
| `A5+0x10AE` | **FG / Plane-A Y scroll** (committed) | `0x55ACC movew %a5@(0x10AE),0xC40002`; updated `0x5583E`/`0x5588C` |
| `A5+0x10EC` | **FG / Plane-A X scroll** (half-rate) | `0x55ABC movew %a5@(0x10EC),0xC40000`; updated `0x55BB0` |
| `A5+0x10B0` | **BG / text-layer Y scroll** | `0x55AC4 movew %a5@(0x10B0),0xC20002` |
| `A5+0x10EE` | **BG / text-layer X scroll** | `0x55AB4 movew %a5@(0x10EE),0xC20000` |
| `A5+0x10B2` | FG sub-row (8-px) accumulator; bit3 ⇒ stream row | `0x557EC`–`0x557FC` |
| `A5+0x10B8` | direction accumulator (≥0 up / <0 down), limit 160 | `0x557BA`/`0x557BE` |
| `A5+0x10D8` | scroll step (≤4 px) | `0x557F0`/`0x5583A` |
| `A5+0x13D0` | row-stream direction mode (2 up / 3 down) | `0x55890`/`0x55842` |
| `A5+0x10A8` | section-kind gate (0 outdoor / ≠0 castle) | `0x557C4` |
| `A5+0x10CA` | descriptor strip 0..3 | `0x558A2`, `0x55810` |
| `A5+0x10CC` | name-table row-base companion | `0x5580A` |
| `A5+0x132C` | saved completed-fill selector (replayed at reseed) | `0x557DC` |
| `A5+0x013E` | progression record (scene index) | `0x503BC`, `0x504FA` |

**Errors identified:** my 0046 described `0x10B0` only as a vague "companion"; it is specifically the
**BG/text-layer Y** (`0xC20002`). Cody's report labels `0x10B0` as Plane-A Y — **wrong plane** (§4). The
X/Y and FG/BG ownership above is unambiguous from the commit block `0x55AB4–0x55AD4`.

## 8. Is a 64×32 Genesis ring sufficient?

**YES — PROVEN sufficient; no enlargement justified.**
- Simultaneously required rows: 28 visible (224 px) + scroll margin. The producer streams one new row per
  8-px crossing (≤4 px/frame ⇒ ≤1 row every 2 frames), so a 2–4 row margin suffices → ≤32 rows. Fits.
- Logical row 32 aliasing physical row 0 (`logical & 31`) is **correct** provided the producer replaces the
  outgoing row with the correct incoming logical row before it becomes visible. That replacement correctness
  — not the plane height — is the open question.
- **No physical-ring collision has been demonstrated** in any capture. The staging→VRAM checks passed at
  reached states; the unreached states (18–21) are a *source-selection* gap, not a capacity gap.
- The arcade's own FG plane is 64×64, but only ~28 rows are ever visible; the extra arcade rows are ring
  headroom, not simultaneously displayed content. Genesis does not need to mirror the ring size to mirror the
  visible window.

**Therefore my earlier 64×64 suggestion is withdrawn. Do not grow the tilemap to mask a logical-row
selection error.** If a future capture *does* show a genuine simultaneous >32-row requirement at some R1-S2
camera state, that would reopen it — but nothing in evidence shows that today.

## 9. Original-arcade vs Genesis record 16–21 producer comparison

| Record | Arcade governing state | Arcade descriptor source | Arcade row-expose rule | Genesis producer (0525) | Expected physical mapping | Review note |
|---:|---|---|---|---|---|---|
| 16 | scene entry; gate `0x10A8`≠0 (castle); `A5+0x132C` saved selector | full page rebuild `0x55904` | full-ring replay | `scene_scroll_reseed_native` full replay | all 32 phys rows seeded | **correct at entry — PROVEN path**, matches screenshots |
| 17 | selector-1 (reverse row at `0x55696`, dest `0x3F00−(group*0x400+strip*0x100)`) | reverse-ordered descriptor | 8-px crossing streams 1 row | precompiled `pan_row_maps` 64-word row | `logical&31` | row transform independence **unverified** (non-independent gate) |
| 18–20 | selector-0 dynamic; gate `0x10A8`≠0 | live `0x55904` rebuild via strip `0x10CA` | 8-px crossing, mode 2/3 | **dynamic live resolver** | `logical&31` | **not naturally captured**; likely first divergence at **17→18** — SUPPORTED HYPOTHESIS |
| 21 | selector-1 again | reverse-ordered descriptor | 8-px crossing | precompiled `pan_row_maps` | `logical&31` | realignment here can mask a middle-path error without fixing it |

**Invariant all producers must preserve (the semantic cut):** for the current `(A5+0x013E, A5+0x10AE,
strip A5+0x10CA, direction A5+0x13D0)`, the entering physical row `(A5+0x10AE/8) mod 32` must receive the
**same world logical row** that the arcade descriptor machine (`0x55904` page + `0x406A4` stream) would place
at that scroll value — including the correct descriptor-sequence **end/orientation** for the climb direction.
Selector-1 compiled rows and selector-0 dynamic rows must agree on that world-row identity across the 17→18
and 20→21 seams.

**Oracle note:** this comparison is **not** derived from Cody's native compiler. It is built from the arcade
instructions (§6/§7) plus the **second (arcade)** screenshot set as landmark truth. The **first (Genesis/
BlastEm)** set shows the same landmarks correctly rendered. Pixel-level alignment is **not** claimed — the two
sets are not camera/record/scroll-state matched (§10).

## 10. Independent placement-oracle requirements

**Available now:** the arcade source fully determines, for any `(0x013E, 0x10AE)`, the visible rows and their
descriptor-sourced tile words (§6/§7). Tighe's **second (arcade)** screenshot set supplies landmark truth:
fire archway, twin-flame candelabra, right-edge ladder/rope, stepped ledges, barred window recesses. The
**first (Genesis/BlastEm)** set shows the Build 0525 output of those same landmarks — enough to confirm the
artwork/palette is correct, **not** enough (no matched camera/record/scroll state) to localize a first bad
cell.

**Missing for a first-divergence proof (smallest additional observation-only capture):** a synchronized
last-correct / first-wrong pair across **17→18** and **20→21** recording, for both machines:
`A5+0x013E`, **`A5+0x10AE` (FG Y — NOT `0x10B0`)**, `A5+0x10B2`, `A5+0x10B8`, strip `A5+0x10CA`, row-base
companion `A5+0x10CC`, direction `A5+0x13D0`, section gate `A5+0x10A8`, the 16 live descriptor pointers
(`$FF1000`/`$FF1040`), arcade PC080SN FG names for the entering row + 32-row window, and Genesis
`staged_fg_buffer` + VDP Plane-A names + the actually-displayed VSRAM Y. Normalize both to
`(world row, world col, raw code, attribute, final word, physical row/col)` and find the first cell whose
world coordinate differs. **Do not** overlay arcade and Genesis pixels without equal camera words.
**This capture writes artifacts and is therefore out of scope for this read-only task** — specify it for a
later authorized assignment. (Cody's capture list is essentially this, with the `0x10B0`→`0x10AE`
correction.)

## 11. Rope benchmark 795→799 analysis

**Facts (PROVEN):** arcade reference = **771** (`states/traces/arcade_rastan_rope_attach_reference`,
771×5). Historical Genesis = 795; Build 0525 = **799**, deterministic ×3. The benchmark **script is unchanged
since Build 426** (`git log` on `run_rope_attach_performance_benchmark.sh` and the lua: last touch Build 426
`9982f7cd`; 0525 ≫ 426), so **test-config/script drift is ruled out** as the cause of the 795→799 delta.

**Detector semantics (PROVEN, from `rope_attach_performance_benchmark.lua`):** inputs are scripted by **fixed
frame number** (Coin 120–132, Start 175–187, P1 Right held once started). `start_frame` latches when
`globals ready ∧ r8(0xff3865)==1 ∧ r16(0xff10be)==0x0020 ∧ player_state(0xff10e8)∈[1,3]`. PASS/`attach_frame`
when `started ∧ r16(0xff013e) ≥ 2 ∧ player_state==4`. So **elapsed = attach − start = frames from
gameplay-start to the first state-4 (rope) at progression ≥ record 2.** CPU clock rate is not measured;
elapsed is a **gameplay-progression** count.

**Interpretation against the prompt's five possibilities:**
- **Test-configuration difference — REJECTED** (script identical since Build 426).
- **Benchmark-endpoint change — REJECTED for the 795→799 delta** (same detector; start and attach conditions
  unchanged).
- **CPU execution slowdown — NOT SUPPORTED as the framing.** elapsed is progression frames, not cycles; +4
  progression frames does not establish the CPU runs slower.
- **Gameplay/scheduling regression from the 0525 scene-entry Plane A replay — SUPPORTED HYPOTHESIS (leading).**
  Build 0525's restored `scene_scroll_reseed_native` full-ring replay runs at scene entry/respawn. The
  measured interval (start → progression ≥ 2) crosses scene/record boundaries where the replay (and its
  rewind of 16 descriptor pointers + 64-strip rebuild) executes. If that replay adds ~4 frames of latency
  before progression reaches record 2 / the first state-4, elapsed grows by 4 **without any CPU slowdown**.
  This is the only 0525-specific change in the path and matches the deterministic +4.
- **Camera/collision route divergence — POSSIBLE, UNRESOLVED.** If the restored replay slightly changes the
  camera/scroll state the player interacts with, the route to the first rope could advance differently.

**UNRESOLVED:** which of the two supported possibilities holds, and whether the replay mutates any *retained
arcade state* feeding gameplay (the reseed rewinds descriptor pointers and replays `A5+0x132C`; whether that
write-back perturbs a gameplay-visible field vs. only native staging is **not proven** here). **Decisive
observation-only test (do not run in this task — it writes artifacts):** capture per-frame
`(frame, 0xff013e, player_state 0xff10e8, 0xff10be, 0xff10ae)` for the historical 795 build and Build 0525
over the identical scripted route; the **first frame at which the two builds' `(0x013e, player_state)`
diverge** localizes it — a boundary-adjacent divergence implicates the replay latency; a mid-gameplay
divergence implicates route/state. **The +4 result is factual; its cause is UNRESOLVED.** Do not retune the
threshold or alter gameplay to reclaim 795.

## 12. R1-S2 and R1-S3 sprite / Composer inventory

**Agreement with Cody (from arcade source, not just Genesis-generated data):**
- R1-S2 Composer coverage is `SCHEDULE_ONLY`; only the marker-`M` five-child burst is scene-tagged
  (honestly incomplete). R1-S3 has a 219-use Plane A corpus but no authored context. Plane B is
  non-authorable with Line 2 arcade-owned. R1-S3 boss `0x061D`. **These are source/corpus-backed.**
- The old `0x0224/0x00F4` R1-S2 attribution was wrong (retire before R1-S2) — my PROMPT-0038 finding, which
  Cody cites. **PROVEN.**

**Which findings are source vs Genesis-generated-only:**
- **Source-backed:** boss `0x061D`/rectype `0x0E`/pool-11 palette route; `0x0A73/0x0A5A` death/reward bases;
  marker chain; the 219-use corpus provenance (banks `$008/$019`).
- **Genesis-generated-only (not arcade-authority):** the "517 authored vs 520 corpus" delta, the death-table
  selector ranges as a stand-in for live frames, and any `Test.json` count — these describe current editor
  state, not arcade truth.

**Armored-man identity reconciliation (independent):** the **arcade** (second) ROUND-1 castle set shows the
armored men as **green-armored sword knights** — multi-piece humanoid warriors, Rastan-scale, in groups of
2–4, walking and attacking; the **Genesis** (first) set renders the same enemy type. Therefore:
- **Living armored-man actor: UNRESOLVED base.** It is a walking enemy with its own base/compositor, reached
  via the R1-S2 marker/schedule chain (`0x0502CC` descriptor-grid population → marker → `0x40BAA` dispatch →
  final base). **Do not register `0x0A73` as the species.**
- `0x0A73` (comp 2) = state-0x0F **death/impact** presentation; `0x0A5A` = the family-12 **reward/drop**
  transform of that same path (`0x40CCC` `transform:`). These are **state presentations**, not the walking
  identity. Cody's own risk note ("treating `$0A5A` only as an armored base can collide with its reward/death
  use; object identity must include state/selector") agrees. **I and Cody concur the living base is unproven.**
- **R1-S3 (red throne room — Genesis/first set):** R1-S3 uses a **distinct red-brick Plane A/B vocabulary and
  palette** (reds/pinks), wholly different from the gray-green R1-S2 castle — reinforcing that R1-S3 needs its
  **own** authored contexts (Plane A, Plane B, sprite) and must **not** inherit R1-S2 colors. (Current Genesis
  R1-S3 colors are the unauthored fallback, not a regressed decision — agrees with Cody.)

**Composer integration recommendation (no implementation):** follow Cody's additive, new-derived-profile plan
— freeze a new profile (never edit `Test.json` in place), close the R1-S2 living-armored and marker rosters
from original data first, register complete scene-tagged objects additively, add R1-S3 Plane A from the
219-use corpus, and design R1-S3 Plane B as its **own** context that previews original Line-2 colors
**without unlocking Line 2**. Preserve `Test.json` and all authored decisions; every palette change updates
`specs/palette_decisions.json` by ID. I endorse this ordering.

## 13. Armored-man corruption hypothesis comparison

**What each failure predicts (the discriminators):**

| Hypothesis | Prediction at the corrupt instance | Owner |
|---|---|---|
| **Tile residency / 12-cell DMA worklist saturation** | **MISSING** pieces (blank) at otherwise-correct positions; `pc090oj_dropped_count` rises with `pc090oj_tile_dma_count==12`; missing resident keys | Cody #1 |
| **SAT total/order (80) truncation** | a **suffix** of pieces absent per queue order; `pc090oj_emitted_count` at limit | Cody #2 |
| **Signed piece-offset / Y-anchor error** | pieces **present but displaced** (wrong Y), e.g. extending below the floor; positions wrong, count right | Andy 0046 #3 |
| **Wrong animation/frame layout (state-specific)** | a **coherent but wrong** piece set for the actor's actual state/orientation | both |
| **Stale SAT/queue** | pieces from an **earlier state** persist | Cody #4 |

**Reading the screenshot honestly:** the corrupt instance shows **pieces extending downward into the empty
area below the floor** — i.e., **pieces present at wrong Y**, which is the *displacement* signature (favoring
the signed-offset / Y-anchor hypothesis) over pure *disappearance* (residency/SAT drop, which removes pieces
rather than relocating them). **However**, per Cody's valid caution, a residency/order effect can leave a
*subset* visible, and a subset at valid-but-partial positions can superficially resemble displacement. The
two are **not** decidable from the image alone: displacement predicts **same count, wrong Y**; residency/SAT
predicts **fewer pieces, correct Y where present**. **UNRESOLVED without the capture.**

**Recommended read-only capture (merges both our lists) at the first bad frame:** both armored actors' full
64-byte records + indices (`+0x01` anim, `+0x05` state, `+0x1E` base, `+0x20`, `+0x27`, `+0x38` comp,
`+0x39`); selected generated frame + **expected per-piece list with signed offsets**; all six semantic lane
counts + queue entries pre-finalize; `pc090oj_dropped_count`, `pc090oj_tile_dma_count`, DMA worklist, 49
resident keys/used bitmap; `pc090oj_emitted_count`, both shadow SAT banks, actual VDP SAT; referenced pattern
bytes; per-scanline sprite count; and the matching **original-arcade** actor records + PC090OJ pieces at the
same state. **Diff order:** expected pieces → queued → shadow SAT → VDP SAT. The first stage where **count**
drops ⇒ residency/SAT; where **positions** move with count intact ⇒ signed-offset/anchor. This single capture
discriminates all six hypotheses. No sprite-handling change.

## 14. Gray-border and boss-music findings

- **Gray border — PROVEN mechanism (verified §2):** per-scene export wrote `0x0888` to CRAM[0];
  `test_palette_line0.bin`=`0x0000`. CRAM[0] = backdrop. First regression is after Build 0508 at the
  per-scene palette path (`c8fd3e5d` per Cody). **Proof of first regression:** diff CRAM[0] / the scene
  asset's first word across Build 0508 vs the first per-scene-palette build (read-only); do not force reg 7
  to hide a bad export. Agrees with my 0046 (Genesis presentation, not metatile).
- **Boss music — SUPPORTED HYPOTHESIS, command UNRESOLVED:** native track exists ("The Devil Boss Carnival")
  but `specs/audio_native_song_map.json` maps only authentic commands `$04/$25/$27`; the boss track is
  diagnostic-only. The authentic boundary is `retained boss-entry music request → authentic command →
  existing track dispatch`, captured at the R1-S2→R1-S3 transition through `0x3A0EC/0x3A116` (caller PC +
  order). `0x3A0EC` handles SFX (e.g. #23 at `0x40E0E`); the **music command id is not yet located**. Agrees
  with my 0046. Do not duplicate song data or synthesize a scene-number trigger.

## 15. Prioritized next engineering actions (for Cody)

1. **P0 first-divergence capture (records 17→18, 20→21)** per §10 — **with `A5+0x10AE` as the FG Y field,
   not `0x10B0`.** Output one durable arcade/Genesis cell-diff. This decides whether the fix is selector-1
   transform (record 17), selector-0 dynamic phase (18–20), or projection/timing. **No ring enlargement.**
2. **P0 unify the entering-row producer** only after #1, at the stated semantic cut; preserve the working
   R1-S1 respawn and record-17 rows.
3. **Rope +4 differential capture** (§11): per-frame `(0x013e, player_state, 0x10be, 0x10ae)` for the 795
   build vs 0525 over the fixed script; localize the first divergent frame. Observation-only.
4. **P1** close the living armored-man + marker rosters from original data (not the death base), add R1-S3
   Plane A / Plane B / sprite contexts additively via a new derived profile; preserve Line 2 and `Test.json`.
5. **P2** run the §13 capture before any capacity/geometry change.
6. **Secondary:** normalize per-scene CRAM[0]; locate + map the authentic boss-music command.

**Risk emphasis:** growing the plane or raising sprite bounds before #1/#5 would mask the actual
logical-row / piece-anchor bug and risk VBlank/VRAM budget.

## 16. Missing evidence and required gameplay verification

- **BlastEm (Genesis) shots WERE supplied** (first set) but **without embedded camera/record/scroll state**
  and not camera-matched to the arcade set, so only a **landmark-level** arcade↔Genesis comparison was
  possible — **no pixel-level first-divergence**. **UNRESOLVED:** first divergent R1-S2 cell/frame (needs §10
  capture).
- **UNRESOLVED:** world-Y-up sign → descriptor-sequence end for a climb (§6); living armored-man base (§12);
  rope +4 precise cause (§11); authentic boss-music command (§14); selector-1 transform independence (§9).
- **Screenshots examined (attribution per Tighe):** **First set = GENESIS / BlastEm (Build 0525):** R1-S2
  gray+green castle (armored Rastan, fire archway, candelabra, right-edge ladder, green sword-knights,
  yellow-striped barriers); R1-S1 outdoor (purple/blue sky, brown rock, green enemies); R1-S3 **red-brick
  throne room** with a white figure. **Second set = ORIGINAL ARCADE (ROUND 1):** the R1-S2 vertical castle
  climb with the same landmarks and green sword-knight "armored men" in groups of 2–4. Used for landmark +
  sprite-appearance evidence only; the two sets are not state-matched, so they are not a pixel oracle. The
  Genesis set confirms correct R1-S2 artwork/palette (defect is positional); the arcade set is the placement
  authority.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0050`
