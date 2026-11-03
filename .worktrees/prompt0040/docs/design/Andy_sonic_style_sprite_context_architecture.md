# Andy — Sonic-Style Rastan Sprite Context Architecture (offline-generated residency)

**Task:** architecture / static analysis / offline-compiler design. **No production code, no ROM, no
build.** Counter 356. Runtime target is 68000 assembly; Python only for offline generation/verification.

> ## ⚠ SUPERSEDING SUMMARY (current active design — read first)
> The VRAM/packing proof (Cody 58-cell ceiling + Andy packing, see
> `Andy_r1p1_sprite_semantic_completion_and_58cell_packing.md`) **overturns the pure-per-owner
> "Architecture C" this document originally recommended.** Corrections, authoritative:
> - **Pure per-owner fixed bases (old "Architecture C" / clean Sonic `obGfx`) is NOT viable** for
>   R1/P1: it needs ~100–126 cells vs a 58-cell physical envelope. Sections that say *"one fixed
>   phase-wide layout"*, *"SKIP B; target C directly"*, *"C is now UNBLOCKED"*, and the blanket
>   **DELETE** of all residency state (§4, §7, §8, §9) are **RETRACTED** — kept below only as history.
> - **Recommended design = MODEL 4 (HYBRID):** fixed offline-assigned bases for stable small owners
>   (player, HUD, common effects, hurry-up/Small-Bat) **+ a bounded O(1) reverse-index shared pool**
>   for the large co-present enemy families. This eliminates the 49-slot **linear search** (the #1
>   hotspot — still DELETE) while keeping the shared residency Rastan's enemy density genuinely
>   requires. Old "Model B (reverse index)" is **revived**, not skipped.
> - **58 cells FAIL**; within-frame floor is **61 (Genesis 80-SAT-constrained) / 63 (full arcade
>   producer)**; reaching it needs a Plane-A reduction of **12–20 patterns** (separate task).
> - **Frame maps:** the Palette Composer already supplies palette/reindex + represented poses and the
>   arcade dispatch chain is identified; remaining work is full animation-frame enumeration + runtime
>   selector binding, **not** graphics re-derivation.
> - **Readiness: BLOCKED** (VRAM floor > 58; frame-domain enumeration incomplete). A-13 Cody-owned.
>
> Read §5/§5e/§6a for the still-valid proofs (working set, section↔segment, demon one-shot spawns).

Follows the Build 0356 timing investigation. Cody proved the sprite finalizer's per-emitted-entry
49-slot residency search is the #1 steady hotspot (~137.9 ln median, r=0.90 with emitted count); I
classified it as Genesis-native compatibility work, not arcade gameplay. This designs its deletion.

**This is the reconciled, measurement-complete version.** The earlier vocabulary-union reasoning
(the retracted "player 30 + demon 25 = 55 > 49 ⇒ phase LUT fails") is gone; §5 replaces it with the
**proven peak simultaneous working set** computed offline from the arcade traces. Historical note:
that "55 > 49" conclusion was wrong because it summed *animation vocabularies* instead of *peak
co-resident cells* — §5a/§5b quantify exactly how wrong (vocabulary 734 vs peak working set 63).

**Residency is now modelled by real spawn/retirement LIFETIME, not segment membership** (§5e, §6a–§6d,
§7): variant identity == raw code (proven), internal section == human map segment (proven), Flying
Demon = one-instance scripted one-shot with two encounters reclaimed on death (proven), hurry-up bat =
tiny timer overlay reusing Small-Bat art (kept phase-resident), recurring enemies = phase-wide,
PHASE = hard reset. §7b is the exact VRAM-capacity audit. A second retraction lives in §5c: culling
distinct graphics to fit 49 is **not** proven arcade-faithful (the arcade has no residency cap).

---

## 1. Sonic 1 BuildSprites — why it needs no per-piece residency search

Source: `docs/reference/s1disasm/_inc/BuildSprites.asm`, `_incObj`/PLC system.

Responsibility separation:
- **Object traversal / AI / animation / mapping selection:** each object's own code sets `obFrame`
  (animation frame) and `obGfx` (its **art-tile VRAM base**). Not part of BuildSprites.
- **Art residency:** loaded ahead of time by the **PLC (Pattern Load Cue)** at level load (and a few
  scripted times), into **known VRAM tile offsets**. `obGfx` is that base. Residency is
  **predetermined**, not discovered.
- **SAT construction (BuildSprites):** iterates `v_spritequeue` **already grouped by priority layer**
  (§ `.priorityLoop`), bounds-checks, loads the object's mappings (`obMap`+`obFrame` → frame → piece
  count), and `BuildSpr_Draw` expands each 5-byte piece straight into `v_spritetablebuffer`.
- **The key line:** `add.w a3,d0` (BuildSprites.asm:198) — the piece's *relative* tile word is added
  to the object's `obGfx` **art base**. That is the entire "where is this pattern in VRAM" step: a
  single add of a predetermined base. **No search of a general VRAM pool per piece.**
- **SAT ordering / linking:** the queue is priority-ordered; links are written sequentially (`d5`
  counter). VBlank later DMAs the buffer to sprite VRAM (`writeVRAM v_spritetablebuffer`).

**Why no search:** Sonic never asks "where does this code currently live?" because the art was loaded
to a fixed base ahead of time and every object carries that base. Residency is a *load-time* fact, not
a *per-frame* computation.

We reuse only this **structure** (predetermined base + relative-piece add → SAT). We do **not** import
Sonic's object system, PLC policy, frame loop, level format, or animation system.

## 2. Rastan semantic cut

```
ARCADE PROGRAM (unchanged, authoritative):
  actor traversal, AI/state, animation/frame selection, mapping selection,
  piece count, piece coordinates, piece priority, piece flip/attributes, piece graphics code
        │  ← semantic cut (already where the native sprite emitter sits)
GENESIS-NATIVE:
  semantic piece (code [+ bank/variant])  →  DIRECT generated graphics mapping (resident base)
        →  combine dynamic X/Y/flip/priority  →  SAT append
```

The current native stage-dispatch + finalizer sit exactly at this cut already. The parts that exist
**only** because residency is dynamic:
- `.Lnq_lookup_loop` (the 49-cell code→slot search),
- `.Lnq_vloop` + `.Lnq_cell_free` (free-cell search on miss),
- `pc090oj_tile_dma_worklist` + `worklist_entry_for_slot` + `pc090oj_cell_used` (dynamic allocation +
  per-frame pattern upload of newly-needed cells),
- `sprite_tile_resident_code` (the "what's in each slot now" state the search reads).

All of that disappears if the code→resident-base mapping is **predetermined by context** (Sonic's
`obGfx`, supplied by an offline-generated LUT instead of carried per object).

## 3. The LUT is Rastan's `obGfx`, generated offline and selected by context

Rastan's arcade actors do not carry a Genesis art base. The generated LUT supplies it:
`current_sprite_graphics_map[key] → Genesis pattern base (resident cell)`. Selected once at a
context/epoch boundary (pointer swap, outside the hot path), exactly like the 0356 palette LUT
(`current_sprite_palette_map`) already does for the palette line.

### LUT key
The 0356 palette path already forms a 7-bit effective-bank key at emit. For **graphics**, the same
raw code can resolve to different physical patterns under different banks/reindex profiles (proven by
the offline `pc090oj_editor` reindex: identity is `(code, bank)`/reindex-profile, not code alone).
So:
- **Raw code alone is NOT sufficient** — it is ambiguous across bank/variant.
- **Recommended key:** the arcade graphics **code**, qualified by the resolved **graphics variant**
  the offline compiler already computes per `(code, bank)`. Concretely, offline the compiler enumerates
  every `(code, bank)` that can appear in the context, interns each to a **compact per-context cell
  index**, and emits a small map. At runtime the emitter forms the key it *already has* (code in d3,
  bank via `pc090oj_ctrl_shadow`) and indexes the map. Prefer the **compact interned index**, not a
  sparse Cartesian `(4096 codes × 128 banks)` table.

### Hot path (conceptual, final = 68000 asm)
```
; d3 = arcade code, bank already in the effective-bank key kX
    <form compact key kX from (code,bank)>            ; a few ops, already done today for palette
    movea.l current_sprite_graphics_map, a6
    move.w  0(a6, kX.w*2), d0                          ; resident pattern base  (== Sonic obGfx)
    ; ... combine dynamic flip/priority/palette-line, add relative piece tile ...
    move.w  d0, (satptr)+                              ; SAT append
```
One indexed read replaces the up-to-49-iteration `cmp.w 0(%a2,%d0.w),%d3` loop. This is the direct
structural analog of Sonic's `add.w a3,d0`.

## 4. Context lifetime — PROVEN against the peak working set (not vocabulary)

Verdicts below are now backed by the offline measurement in §5, not estimated.

| Lifetime | Verdict | Reason (proven) |
|---|---|---|
| Whole-game / full vocabulary residency | **NO** | per-segment coexisting **vocabulary** sums reach **734 cells** ≫ 49 (§5a) — full-art residency is impossible |
| **One fixed Round-1/Phase-1 layout (phase-wide), DPLC-streamed** | **YES for 99.56 % of R1 frames** | measured screen-wide working set median **9**, P95 **29**; exceeds 49 on only **47 / 10 782** frames (§5b) |
| Per-section enemy-set **epochs** | **NOT REQUIRED and do not help the peak** | the over-budget frames sit inside single sections (06/07/09 each individually peak > 49, §5c), so section-scoped epochs cannot bring those frames under 49 |

**Rule applied:** use the largest lifetime whose *peak simultaneous working set* fits 49 cells. That
lifetime is **one fixed phase-wide layout** (player + HUD + common effects + the round's enemy set),
with each animated actor **DPLC-streamed** to a fixed reserved region sized to its **largest single
frame**. The only thing that layout does *not* absorb is a ~0.44 % tail of peak frames whose working
set (up to 63) physically exceeds 49 cells — a hard VRAM-ceiling decision, not an epoch problem (§5c).

## 4a. Total vocabulary ≠ peak simultaneous residency — now PROVEN, not asserted

**This was the key correction (Tighe).** The 49-cell test must use the **peak simultaneous working
set** — the distinct cells displayed across all on-screen actors in the *worst single frame* — not the
union of every animation frame. §5 proves the gap is enormous: R1 vocabulary per segment reaches
**734 cells**, yet the actual per-frame working set is **median 9, peak 63** — vocabulary overstates
residency by **~12–80×**. Sonic's two offline-authored residency strategies, chosen per actor offline
by Python:

- **(i) Static full-art residency (PLC/SPLC):** load the actor's whole vocabulary once to a fixed
  base; `obGfx` = base; zero per-frame load. Use only when the vocabulary is genuinely small.
- **(ii) Dynamic per-frame residency (DPLC):** reserve a **fixed base sized to the actor's largest
  single frame** (its working set, *not* its vocabulary) and load only the **current frame's** tiles
  into it via an **offline-generated per-frame tile list** (a bounded, predetermined DMA). `obGfx`
  stays fixed; pieces index base+relative. Sonic's player works this way. §5d proves the Flying Demon
  needs strategy (ii): vocabulary **149** vs largest-frame working set **30**.

All layouts, per-actor strategy, per-frame DPLC lists, packages and deltas are **generated offline by
Python**. Runtime only: (a) `context → select generated LUT/package pointer`, (b) `piece → direct LUT
→ Genesis pattern → SAT append`, (c) execute the bounded offline-authored per-frame/epoch DMA. Runtime
never constructs a LUT, searches, evicts, or solves placement.

## 5. Round 1 / Phase 1 — PROVEN peak simultaneous working set

**Cell↔code identity used throughout:** the native finalizer keys residency by the emitted graphics
`code` — `.Lnq_lookup_loop` compares `code` against `sprite_tile_resident_code` across `NATIVE_CELLS`
= 49 slots — so **one resident code occupies exactly one cell slot**, and *distinct emitted codes per
frame = distinct resident cells required that frame*. (If a single arcade code ever expands to a
multi-cell block, the residency model still allots one slot per code, so distinct-codes is precisely
the 49-slot pool's own metric.) Method: offline Python over the original-arcade user-play traces in
`analysis/graphics_optimizer/round1_phase1_corpus/`; blank/placeholder codes `0000`/`FFFF` stripped;
Round 1 = trace `round` field `01`.

### 5a. Vocabulary (the *wrong* metric) — proves full-art residency is impossible
Per-segment sums of every coexisting producer's total vocabulary
(`sprite_census_captured.json` → `sections_records` + `cell_codes`, 21 producers):

| | seg 1 | seg 4 | seg 5 | seg 7 | **seg 9** | seg 13 |
|---|---:|---:|---:|---:|---:|---:|
| Σ vocabulary cells | 147 | 283 | 577 | 612 | **734** | 674 |

Every segment's vocabulary sum is **3–15× the 49-cell budget**. Since R1 renders on real hardware with
a 49-slot pool, the actors provably **cannot** be full-art resident — the game is already streaming.
This is the quantitative death of the vocabulary-union metric and of my retracted "55 > 49" claim.

### 5b. Peak simultaneous working set (the *correct* metric) — screen-wide, per frame
Distinct emitted codes per frame across **all** on-screen actors (player + HUD + enemies + effects +
projectiles), from `full_capture/full_observations.csv` (10 782 R1 frames, 131 006 piece observations):

| metric | distinct cells / frame |
|---|---:|
| median | **9** |
| mean | 10.9 |
| P95 | **29** |
| **max** | **63** |
| frames > 49 | **47 / 10 782 = 0.44 %** |
| frames > 40 | 154 |

**A single fixed R1/P1 49-cell layout holds the working set for 99.56 % of R1 frames.** The typical
frame uses **9** cells — under one-fifth of the budget.

### 5c. The 0.44 % over-budget tail — a hard VRAM ceiling, not an epoch failure
Per-section peak distinct-cell working set (blank-stripped):

| section | 04 | 05 | 06 | 07 | 08 | 09 | 0C | 0D | others |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| max distinct | 47 | 41 | **63** | **63** | 52 | **61** | 49 | 55 | ≤ 38 |

Over-budget frames occur in sections **06, 07, 08, 09, 0D** (all > 49; = segments 6/7/8/9/13, §5e),
and section 09 shows a **sustained** run (frames 7422–7429 at 54–61 distinct), not a one-frame
transient. Because each of these sections *individually* peaks > 49, **section-scoped epochs cannot
cure the tail** — there is no smaller coexistence boundary to split them on. 63 distinct cells exceed
49 slots (252 vs 196 sprite patterns).

**Fidelity note — four DIFFERENT limits, do not conflate (task requirement):**
1. **Pattern-residency capacity** (Genesis: 49 cells of shared VRAM). *The arcade PC090OJ has NO
   equivalent* — it addresses the whole sprite tile ROM (`pc090oj.bin`) directly, so it displays any
   number of *distinct* sprite tiles at once. The >49 distinct-code frames are graphics the arcade
   **does** show. Dropping distinct graphics to fit 49 is **NOT proven arcade-faithful** — it removes
   pixels the arcade displays. (My earlier "bounded degradation is plausibly arcade-faithful" default
   is **retracted**: it confused this Genesis-only residency cap with the arcade's sprite-*count* cap.)
2. **SAT-entry capacity** (Genesis 80; `NATIVE_SAT_MAX=80`). Max emitted **pieces**/frame reached
   **105** (§5b), so on the very densest frames the Genesis 80-entry SAT already truncates — and the
   arcade PC090OJ has its own sprite-count ceiling, so piece truncation at some level plausibly occurs
   on hardware too. Separate limit from pattern residency.
3. **Per-scanline sprite limit** (Genesis 20/line in H40) — a third, orthogonal limit.
4. **Arcade PC090OJ display limit** — the arcade's own sprite-count/line caps (exact number UNKNOWN
   here; not asserted without proof).

**Recommended handling:** prefer **(A) raise the sprite-pattern budget toward the true peak (63)** so
the residency cap stops removing arcade-visible graphics — *gated on the §7b VRAM audit* (whether the
plane-tile arena has free patterns below 1339; Plane A/B must not change in this task). Only if (A) is
impossible use **(C) offline O(1) priority-cull**, and even then it is a Genesis concession, not
"arcade fidelity." This is a **Build-0357 budget decision, not an architecture blocker** — the
direct-LUT + DPLC architecture is identical either way.

### 5d. Largest single actor — Flying Demon (proves DPLC sizing)
From the actor-tagged `flying_demon_trace/observations.csv` (12 493 demon frames, `piece_records`):

| Flying Demon | value |
|---|---:|
| **vocabulary** (census, body+form) | **149** |
| owned pieces / frame (median / P95 / max) | 10 / 19 / 19 |
| **distinct codes / frame** (median / P95 / **max**) | 5 / 16 / **30** |

The demon's **DPLC reserved region = its largest single frame = 30 cells**, not its 149-cell
vocabulary — a **5× reduction**, and the exact number Python reserves for it. The player is likewise
DPLC: its 30-cell vocabulary collapses to a small per-frame pose (bounded above by the median-9
screen-wide total), so its reserved region is a handful of cells, not 30.

### 5e. Graphics-variant identity, and internal section ↔ human map segment
Proven by `tools/graphics_optimizer/prove_r1p1_spawn_lifetime.py`:

- **Variant identity = raw code (within R1/P1).** The 7 enemy families' 43 codes are **bank-
  partitioned** — 0 cross-bank collisions (`enemies.json`: Lizardman 0x04F–0x066 bank 0x36, Insect
  0x2E8–0x2FD bank 0x3A, Valkyrie 0x241–0x252 bank 0x32, Chimera 0x1A6–0x1AF bank 0x34, Demon base
  0x129 bank 0x35, Small Bat 0x268 / Large Bat 0x3F6–0x3F9 bank 0x3E). So each emitted code resolves
  to exactly one `(code,bank)` physical variant, and **the §5b working-set numbers (9/29/63) computed
  on raw code ARE the true graphics-variant working set** — no re-computation changes the peak. (This
  is the refinement the prior pass flagged as pending.)
- **Internal section number == human map segment number.** `full_capture` writes the section in hex,
  the census writes `sections_records` in decimal, and they are the **same 1-indexed counter**: the
  demon's census `sections_records = ['9','13']` matches `full_capture` sections `09` and `0D` (=13).
  So section 08 = Segment 8, section 09 = Segment 9, section 0D = Segment 13. Report both notations;
  they are one scheme in two bases, **not** two different maps.
- **Adjacent segments co-exist on screen during scroll:** section 08's frame span (7035–10467)
  **overlaps** section 09's (7370–11375). This is the mechanism behind Tighe's observation that the
  first demon is *triggered as Segment 9 scrolls onto the right* yet the *fight is visible over
  still-on-screen Segment 8*.

## 6. Flying Demon + hurry-up bat: instance-aware, spawn-lifetime-aware case study

- **Working sets (proven):** Flying Demon largest frame **30 cells** (vocab 149); Large Bat vocab 4
  (trivially resident). The demon is the sizing driver and uses strategy (ii) DPLC.
- **Why it slows now:** the current dynamic pool searches all 49 cells **per emitted piece** — the
  demon emits up to **19 pieces/frame** — **and**, when co-displayed working sets approach the pool
  size (sections 09/13 reach 54–61 distinct with the demon present), it evicts/reloads: the worst
  measured chain hit **12/12 worklist entries** (churn) + drops. Both the search *and* the eviction
  churn scale with exactly the demon-heavy frames §5c flags.
- **Under architecture C:** the demon has a **fixed 30-cell base** (offline-assigned). Its current
  frame's ≤30 tiles are loaded by the bounded **offline-generated per-frame DPLC list** to that fixed
  base. **No per-piece search, no eviction, no runtime allocator.** Each piece is `base + relative →
  SAT`.
- **Acceptance test — answer: YES**, with one honest caveat: on the ~0.44 % tail frames where the
  *screen-wide* set exceeds 49 (§5c), the demon still renders search-free, but the 49-slot VRAM
  ceiling forces the §5c decision (budget ↑ / bounded cull). The per-frame cost that C removes — the
  search and the churn — is gone in **all** cases; only the physical VRAM ceiling on the tail remains,
  and that is a budget decision, not a per-frame algorithm.

### 6a. Instance-aware Flying Demon (proven)
`prove_r1p1_spawn_lifetime.py` over `flying_demon_trace/`:
- **One instance at a time.** The demon is the *special two-slot* actor `actor_508`: body slot
  `A5+0x10C508` (obj records 57–69) + wings slot `A5+0x10C548` (records 70–82), one semantic actor.
  Max simultaneously-active demon slots across the whole trace = **2** (= one body + one wings). There
  is never a second demon. Body/wings are two fixed slots of one actor, not two independent enemies.
- **Two encounters, no respawn.** Demon graphics appear in **exactly two sections: 09 and 0D (=
  Segments 9 and 13)** — 4 854 and 3 859 code-observations respectively, **zero** anywhere else. This
  is Tighe's "two total, second around Segment 13," proven. After a demon dies, none reappears until
  the *next scripted section* — the residency lifetime is the encounter, not the whole phase.
- **Outlives its spawn section.** Demon observations spill from section 09 into 0A (245 obs), and the
  demon's `world_x` sweeps leftward within an encounter (e.g. 180→15, and into negative X) — i.e. the
  live actor traverses across the segment boundary. **The residency-reclaim trigger must be the
  demon's death/retirement, never `current_section changed`.**
- **Shared DPLC region is valid.** Because there is only ever one demon (body+wings), one generated
  fixed region sized to the combined body+wings largest frame (**30 cells**, §5d) is instance-safe.
  Body and wings animate as two records but are one encounter and load into that one region.

### 6b. Spawn-policy taxonomy (the real residency input)
Static owners: spawn scheduler `actor_spawn_ground_and_activate_41180` (arcade 0x41180), keyed on the
scroll-progression counter **A5+0x13E** (0…0x87 across the phase) reading a ROM spawn table via A4;
stage counter **A5+0x118** (< 6); paired-actor init `paired_actor_init_45342` (demon); native emit
`FUN_00041dae`. Per family:

| Family | Spawn type | Eligibility (sections=segments) | Respawn | Max live | Residency lifetime |
|---|---|---|---|---|---|
| Lizardman (0x04F–0x066, bank 0x36) | RECURRING | segs 1–15 (≈ whole phase) | yes, region-continuous | few | **phase-wide** (another can always spawn) |
| Four-armed insect (0x2E8–0x2FD, 0x3A) | RECURRING | segs 4–15 | yes | few | phase-wide from seg 4 |
| Chimera (0x1A6–0x1AF, 0x34) | RECURRING | segs 5–15 | yes | few | phase-wide from seg 5 |
| Valkyrie (0x241–0x252, 0x32) | RECURRING (narrow) | segs 7–9 | yes, in-window | few | segs 7–9 window |
| Large Bat (0x3F6–0x3F9, 0x3E) | RECURRING | segs 2,5–8,13,14 | yes | few | its regions |
| Small Bat / **hurry-up bat** (0x268–0x26A, 0x3E) | **TIMER-TRIGGERED overlay** | whole phase (idle timer) | continuous while idle | swarm (§6d) | **phase-wide static** (see §6d) |
| **Flying Demon** (0x129, bank 0x35) | **SCRIPTED ONE-SHOT** | seg-9 trigger, seg-13 trigger | **NO** (per encounter) | **1** | preload before trigger → while alive (may cross into seg 8) → reclaim on death |
| projectiles/effects (sparkle, fireball, spear, burst) | PROJECTILE/EFFECT | with their owner | with owner | few | with owner family |

The three lifetimes the compiler must not collapse: **map presence** (where designated), **spawn
eligibility** (while new instances may still appear — this drives residency for recurring families),
**active actor lifetime** (one actor's birth→death — this drives reclaim for scripted actors).

### 6c. Phase transition = hard enemy/context reset
- **Behavioral proof (authoritative, Tighe + trace):** no enemy instance crosses a phase; the
  transition wipes the screen and retires all actors. In the corpus every demon encounter is bounded
  within gameplay and nothing enemy-side persists across a phase boundary.
- **Structural support (arcade static):** the actor blocks are *program state* re-initialized per
  stage — main enemy block `A5+0x2C8`, secondary `A5+0x748`, paired/special `A5+0x5C8`/`0x508` — under
  stage counter `A5+0x118` and progression `A5+0x13E`; the demon's paired slots are (re)initialized by
  `paired_actor_init_45342`. Empty slots are blanked at emit time by `FUN_00041dae`
  (off-screen y = 0x180 — implicit retirement, KF-063). *Honest scope:* the retirement is
  **distributed** across stage-init + per-frame blanking rather than a single memset; I did **not**
  isolate one "wipe" instruction/PC in this pass. The residency implication does not need it.
- **Residency implication (the point):** PHASE is a safe hard top-level boundary — at a phase switch
  Python-generated runtime data may discard the whole phase sprite context, load the next phase's
  static regions, and reset all encounter/overlay/DPLC state. No enemy carry-over handling ever.

### 6d. Hurry-up bat = timer overlay, reuses Small Bat art (tiny)
- **Proven family:** KF-068 (Build 0216) documents the *natural hurry-up bat swarm*; its records
  0x268/0x269/0x26A are the **Small Bat family** (base 0x0268, bank 0x3E) — a **1–3 cell** footprint.
- **Trigger:** an idle / delay / hurry-up timer (stay-too-long), independent of map spawn tables, so
  it can overlay *any* section's normal enemy set; it is a swarm (multiple bats) that keeps coming
  while the condition holds, retiring when Rastan moves on / they die. (Exact timer address and max
  simultaneous count: not isolated here — KF-068 establishes the family and swarm behavior; the count
  cap is UNKNOWN pending a targeted read, but the footprint is tiny either way.)
- **Recommendation:** because the art is ~1–3 cells and the trigger spans the whole phase,
  **keep the hurry-up/Small-Bat family permanently resident as a phase-wide static region.** This
  removes it from every coexistence question at negligible VRAM cost and avoids any runtime overlay
  transition for it — exactly the "prefer simplicity when VRAM cost is tiny" call.

## 7. Offline spawn-lifetime residency model (fixed + overlay regions, Python-decided)

§5/§6 fix the model: **one phase-wide sprite-VRAM layout per phase**, internally divided by *lifetime
class*, with mutually-exclusive encounter families **overlaid on shared physical cells** — all decided
offline. Not per-section epochs (§5c), not a runtime allocator.

- **Phase-wide static regions (loaded once at phase entry, never reloaded):** player (DPLC, small
  region), HUD, common effects, and — per §6d — the hurry-up/Small-Bat family.
- **Recurring-family regions (phase-resident because eligibility ≈ phase):** Lizardman, Four-armed
  insect, Chimera; each DPLC-streamed to a fixed region sized to its largest single frame. These
  **cannot** be epoch-freed because another instance can spawn anywhere in their eligibility window.
- **Narrow-window recurring (Valkyrie, segs 7–9):** may share physical cells with a family that is
  provably absent from segs 7–9, if the compiler finds one; otherwise phase-resident.
- **Scripted-encounter overlay (Flying Demon, 30 cells):** occupies a shared physical region that is
  **safe to reuse** because the demon exists only during its two encounters and exactly one demon
  lives at a time (§6a). The compiler may alias the demon's 30 cells onto cells owned by a family that
  is provably not co-displayed during the encounter. **Load trigger = the scripted seg-9/seg-13 spawn
  event; reclaim trigger = demon death/retirement** (never `section changed`, §6a).
- **Overlay alias table (offline):** `physical region → { families that may occupy it, mutually
  exclusive by proven lifetime }`. Runtime executes: encounter trigger → load generated package into
  the predetermined shared region → select generated mapping pointer. No allocator, no packing.
- **Transition/load size:** phase-entry load ≤ the full layout (≤ 63 cells × 4 × 32 B ≈ 8 KB),
  comparable to the existing display-off scene reload (`scene_load.s`/`fg_tile_cache.s`); the demon
  encounter overlay load is ≤ 30 cells ≈ 3.8 KB. Per-frame DPLC uploads ≤ the actor's largest frame —
  the bounded replacement for today's churn, not an addition.

## 7b. VRAM capacity audit — RESOLVED (Cody measured; Andy packed)

**Cody measured the arena occupancy** the prior pass left open and proved the exact physical ceiling
(`Cody_r1p1_sprite_vram_capacity_layout_and_semantic_hooks.md`; the old "1339 start" was 4 patterns
low — correct sprite start is pattern 1339 = 0xA760). Highest required non-sprite pattern = 1301;
first reusable = 1302; consecutive tail 1302..1535 = 234 patterns = **58 complete cells** (+2-pattern
fragment 1534..1535). Under proven zero-drop Plane A: **49/52/55 PASS; 61/63/64 FAIL** (conflict with
Plane A patterns ≤1301). So the physical envelope is **58 cells (patterns 1302..1533)**.

**Andy packed against it** (`Andy_r1p1_sprite_semantic_completion_and_58cell_packing.md`,
`analyze_r1p1_sprite_packing.py`). **58 FAILS**, and no offline model rescues it:

| Model | Peak cells | Verdict |
|---|---:|---|
| Per-owner fixed regions (clean Sonic `obGfx`) | **~126** | INFEASIBLE (Σ co-present owner unions at demon frame) |
| Shared frame-specific pool (minimal) | **61–63** | still FAIL by 3–5; needs per-frame placement |

The overflow is **within single frames** (61–63 distinct tiles displayed at one instant; §5c), so
time-based overlays/aliasing/epochs cannot reduce it. **Minimum proven cells = 63 (full fidelity),
61 after the 80-SAT cap both platforms impose** (the demon frames at 59–61 have <80 pieces → no SAT
relief; the two dense >80-piece frames reduce to 52/62). Reaching it needs a **Plane-A reduction of
12 patterns (61) to 20 patterns (63)** — precisely quantified, **out of scope** to perform here.

This **supersedes** the earlier §5c "prefer raise budget toward 63, gated on arena occupancy" as an
open item: the occupancy is now measured, the answer is that 58 is the ceiling under current Plane A,
and 61–63 requires an explicit Plane-A reduction. §5c's fidelity stance (culling ≠ arcade-faithful)
stands.

## 8. Current machinery disposition (architecture C)

| Structure | Disposition |
|---|---|
**REVISED for MODEL 4 (hybrid).** The blanket-delete column below was written for the retracted pure
per-owner "Architecture C"; under the hybrid, only the *linear search* and *blind allocation* go — the
reverse index and a bounded shared-residency state are **kept/added**.

| Structure | Disposition (hybrid) |
|---|---|
| `.Lnq_lookup_loop` (49-cell **linear** code→slot search) | **DELETE** — replace with an **O(1) `code→slot` reverse index** (the #1 hotspot; the one firm delete) |
| `.Lnq_vloop` + `.Lnq_cell_free` (linear free-cell search) | **REPLACE** with a bounded O(1) free-slot structure (free list / bitmap scan), not a linear scan |
| `pc090oj_tile_dma_worklist`, `worklist_entry_for_slot` | **KEEP (bounded)** — the hybrid's shared-pool upload queue; already bounded (12), commonly 0 |
| `pc090oj_cell_used` (allocation bitset) | **KEEP** — needed by the shared pool; consulted O(1) |
| `sprite_tile_resident_code` (what's resident now) | **KEEP** — the reverse index indexes it; do **not** delete |
| Stage dispatch (record → queue: coords/priority/code/flip) | **KEEP** (semantic extraction; may simplify) |
| Finalizer per-piece transform (X/Y wrap, flip, opaque-bbox clip) | **KEEP** |
| SAT append + priority/lane ordering | **KEEP** |
| Palette-map lookup (`current_sprite_palette_map`, 0356) | **KEEP** (already O(1)) |
| Fixed-owner static upload (player/HUD/effects/hurry-up bat) | **MOVE TO PHASE-LOAD** (offline-assigned fixed bases; once at phase entry) |
| Enemy-family current-frame upload | **DPLC into the shared pool** (offline frame→tile lists inform it) |
| New: reverse-index `code→slot` + offline frame maps + fixed-owner base table | **ADD** |
| `NATIVE_CELLS` physical layout | **KEEP**; budget is 58 today, 61–63 only after a Plane-A reduction (§7b, separate task) |

## 9. Architecture comparison A / B / C  → superseded by Model 1–4 (see packing report §11)

**RETRACTED recommendation.** The A/B/C framing below concluded "SKIP B; target C" — that predates the
58-cell packing proof. C (pure per-owner) is **not viable** (~100–126 cells). The correct comparison
is Models 1–4 in `Andy_r1p1_sprite_semantic_completion_and_58cell_packing.md` §11; the answer is
**Model 4 (hybrid)**, which *revives* B's O(1) reverse index as the shared-pool mechanism. The table
below is kept for history only.

| | A: Build 0356 O(49) | B: reverse-index O(1) | C: direct generated context |
|---|---|---|---|
| Hot path | per-piece 49-search + alloc | per-piece O(1) index into a *dynamic* residency map | per-piece O(1) index into a *generated* map (Sonic `obGfx`) |
| Steady CPU | high (search ∝ emitted×49) | search cost removed | search cost removed |
| Churn (demon) | evicts/reloads, worklist fills, drops | **still churns** (dynamic residency still evicts) | **no churn** (epoch pre-resident) |
| WRAM | resident-code + used-bitset + worklist | + reverse index | small map pointer (map in ROM) |
| ROM/gen data | none | none | generated per-epoch maps + packages |
| VRAM efficiency | dynamic, thrashes | dynamic, thrashes | curated per epoch, no thrash |
| Transition cost | per-frame (hidden as churn) | per-frame (churn) | bounded, once per boundary, display-off |
| Complexity | high runtime | medium runtime | low runtime + offline compiler |
| Semantic risk | — | low | low–medium (needs coexistence proof) |
| Handles Bat/Demon | poorly (churn+search) | search fixed, **churn remains** | **fully** (no search, no churn) |
| Maintenance | poor | medium | best (offline authority) |

**~~Recommendation: SKIP B; target C directly~~ — RETRACTED (see the superseding summary at the top
and packing report §11).** The reasoning here assumed a single fixed phase-wide layout fits VRAM; the
58-cell proof shows per-owner regions need ~100–126 cells, so C is not viable and **B's O(1)
reverse-index is revived** inside the recommended **Model 4 hybrid**. What survives from the analysis
below: A's 49-slot **linear search is the removable hotspot**, and the demon's churn must go — both
achieved by the hybrid's O(1) reverse index + fixed bases. Text retained for history only.

## 10. Performance estimate under C (bounded)

- **Definitely removable:** the per-piece 49-search (`.Lnq_lookup_loop`) — Cody's ~1,751 dots/entry ≈
  the search's `~36 cyc × ~24–49 iters`. At median 28 emitted, that is the bulk of the ~137.9-ln
  finalizer. Plus **all worklist churn/drops** on demon-heavy frames (the worst-chain spikes).
- **Probably removable:** the on-miss free-cell scan + allocation bookkeeping.
- **Must remain:** per-piece coordinate/flip/opaque-bbox transform + SAT write (~0.5 ln/entry), fixed
  setup (~11.7 ln) + HUD lane (~12.5 ln), and stage-dispatch semantic extraction (~44.3 ln).
- **Unknown split:** exactly how much of the ~3.59 ln/entry is search vs transform — this is
  OPEN_QUESTIONS **A-13** (the one reopened Cody measurement); it decides whether the estimate below
  is upper or lower.

**Estimate:** finalizer ~137.9 ln → **~35–45 ln** (transform+SAT+fixed only); saving ~95 ± ~25 ln.
Median chain 334.652 − ~95 ≈ **~240 ln → below one 262-line frame** for the median, with the churn
elimination additionally removing the worst-frame spikes. **Likely under 262: YES (bounded);
plausibly toward ~220–240** if the search is the dominant per-entry cost (A-13 confirms). This is the
architecture that plausibly restores ~60 Hz steady gameplay AND fixes the Bat/Demon case; B does not.

## 11. Preserved (unchanged) arcade execution
Actor update order, AI, collision, animation/state, spawn logic, death/retirement, piece priority,
piece coordinates, frame advancement, VBlank IRQ ownership, the arcade tick, and the final arcade RTE
all remain authoritative. We replace only the PC090OJ-specific representation tail with a Genesis-native
equivalent. No Genesis-owned actor scheduler, no reentrant gameplay, no frame-model redesign. No C
runtime code.

## 12. Offline generator output specification (Python, build-time)

The offline compiler consumes the R1/P1 corpus + the arcade mapping/DPLC source and the existing
reindex authority (Palette-Tool arrangement, **not** the stale `palette_decisions.json`), and emits
**only static data** linked into the ROM — no runtime construction:

| Output | Shape | Runtime use |
|---|---|---|
| **Context descriptor** | one R1/P1 record: layout id, cell budget, actor list | selected once at phase entry |
| **Graphics LUT** `current_sprite_graphics_map` | compact interned `key(code,bank) → resident pattern base` (§3) | O(1) indexed read per piece (`= obGfx`) |
| **Fixed VRAM layout** | per-actor `{base, cell_count}`; static regions + DPLC reserved regions (demon 30, player small, …) | defines bases the LUT points into |
| **DPLC tables** | per animated actor `obFrame → [ (src pattern, dest offset, count) ]`, bounded by largest frame | drives the bounded per-frame DMA |
| **Phase package** | the one-time phase-entry pattern upload (static regions) | display-off phase load |
| **(optional) epoch deltas** | not needed for R1 (§7); emitted only if a phase overflows | display-off boundary load |
| **(optional) tail cull list** | if §5c decision = (C), offline priority order for >49 frames | O(1) truncate at 49 |

**Runtime LUT key (unchanged from §3):** the emitter forms the compact interned key from `(code in
d3, bank via pc090oj_ctrl_shadow)` it already computes for the palette map, and does
`move.w 0(a6,key.w*2),d0` → resident base. One indexed read replaces the ≤49-iteration search.

## 13. Build 0357 readiness

**12-point checklist:**

| # | Prerequisite | Status |
|---:|---|---|
| 1 | Final graphics-residency identity | **PROVEN** — variant == raw code within R1/P1 (§5e) |
| 2 | Phase hard-reset semantics | **PROVEN behaviorally + structurally** (§6c); single wipe PC not isolated (not needed) |
| 3 | Spawn/lifetime classification | **PROVEN** — taxonomy §6b (recurring / scripted / timer) |
| 4 | Recurring-enemy eligibility | **PROVEN** — Lizardman/Insect/Chimera ≈ phase-wide (§6b) |
| 5 | Hurry-up bat overlay semantics | **PROVEN family + swarm** (§6d); exact timer/count UNKNOWN (footprint tiny → resident) |
| 6 | Scripted Flying Demon lifetime | **PROVEN** — 2 one-shot encounters, spawn PCs 0x0458C8/0x045970, flags A5@0x264/0x25A (§6a, packing doc §3) |
| 7 | Multi-instance correctness | **PROVEN** — max one demon; family unions computed (DEMON 25, INSECT 22, CHIMERA 19, LIZARD 18) |
| 8 | Fixed/DPLC/overlay VRAM packing | **PROVEN FAIL @58** — per-owner ~126 infeasible; shared pool 61–63 (packing doc §1) |
| 9 | Exact VRAM capacity | **RESOLVED** — 58-cell ceiling (Cody); min 61–63 needs +12–20 Plane-A patterns (§7b) |
| 10 | >49 arcade-fidelity decision | **RESOLVED** — culling NOT arcade-faithful; fidelity needs 61–63 → Plane-A reduction |
| 11 | Python generated-data format | **SPECIFIED** — §12 |
| 12 | Exact 68000 implementation boundary | **SPECIFIED** — §8 (delete list) + §3 (hot path) |

**Verdict: BLOCKED.** Two independent load-bearing blockers, both now precisely bounded (packing doc):
(1) **VRAM** — the physical ceiling is 58 but the within-frame floor is 61–63; closing it needs an
explicit Plane-A reduction of 12–20 patterns (out of scope), and even at 63 the clean per-owner
`obGfx` model (~126 cells) does not fit, so the residency model itself needs a decision (shared pool +
placement, or a retained bounded runtime step). (2) **Frame tables** — enemy/demon animation→piece
decode is incomplete, so the offline compiler cannot yet emit frame maps. Neither is an analysis gap
closable by another pass.

**Recommended next work**
1. **Tighe decision + Plane-A study:** whether to reduce Plane A by 12–20 patterns to reach 61–63
   cells (full fidelity), and choose the residency model (shared pool vs per-owner+bounded-runtime).
   This is the gating item; Plane-A redesign is a separate task.
2. **Build the offline compiler (§12)** — Python, emitting the LUT + fixed layout + DPLC tables +
   overlay alias table + phase/encounter packages as ROM data. Needs the arcade per-`obFrame` DPLC
   source decode (mapping tables behind each actor's frames, e.g. player 0x5BB40); working-set *sizes*
   are already proven, this step produces the *tile lists*.
3. **Runtime (Build 0357+, 68000 asm; Cody):** add `current_sprite_graphics_map` + phase-load +
   per-actor DPLC executor + encounter-trigger/death-reclaim for the demon overlay; convert
   `.Lnq_emit_entry` to the direct LUT read; delete the search/alloc/worklist machinery per §8.
   Preserve lane/SAT ordering, dynamic flips, palette-map, bbox clip. Sequential test builds 0357,
   0358, … as needed — do not conserve numbers.
4. Optionally run **A-13** (still Cody-owned) to tighten the §10 estimate; not blocking.
