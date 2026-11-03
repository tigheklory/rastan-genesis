# Build 0400 Sprite-Pipeline Root Cause + Native-Genesis Redesign

Status: ANALYSIS + DESIGN. No production source change, no ROM, counter 400. This records everything
found after the Build-0400 timing-instrument finalization: the authoritative HEAVY gameplay measurement,
why the slowdown is NOT scheduling and NOT inherent to the Genesis, the exact root cause in the current
sprite pipeline, the Sonic 1 native model studied as the target, and the resident/transient redesign.

Evidence labels: **[M]** exact measured (debugger cycles), **[S]** static source/disasm proof,
**[REF]** external reference (Sonic 1 disasm), **[HYP]** hypothesis needing a follow-up measurement.

Continues: `Andy_build0400_timing_instrument_repair.md` (UPDATE 3/3b), `Andy_arcade_frame_worker_semantics_and_genesis_map.md`,
`Andy_build0400_irq6_decomposition_and_reorder_plan.md`.

---

## 1. Authoritative HEAVY-gameplay measurement [M]

Controlled run (press-M-armed, scene-1 gameplay), 3,573 complete worker pairs, 0 rejected, GATE PASS.
Frame budget = **128,009 cycles = 16.68 ms** (68000 7.6705 MHz / 59.922 Hz).

Overall: worker median **208,746** cyc (1.63 fr), p95 257,488 (2.01 fr), max 347,316 (2.71 fr);
publication median 3,831 cyc (0.5 ms); IRQ-total median 214,063; worker frame-wraps med 2;
**85.1% of ticks exceed one frame budget**; tick/display = **0.6249** (~62% speed).

**Worker cycles rise monotonically and tightly with emitted-sprite count** [M]:

| emitted | samples | worker med (cyc) | ms med | frame-mult med | %>1 frame |
|---|---|---|---|---|---|
| 10–19 | 261 | 95,606 | 12.5 | 0.75 | 18.8% |
| 20–29 | 441 | 117,378 | 15.3 | 0.92 | 29.5% |
| 30–39 | 217 | 146,242 | 19.1 | 1.14 | 94.9% |
| 40–49 | 267 | 177,340 | 23.1 | 1.39 | 100% |
| 50–59 | 749 | 201,044 | 26.2 | 1.57 | 100% |
| 60–69 | 1383 | 222,498 | 29.0 | 1.74 | 100% |
| 70–79 | 255 | 250,750 | 32.7 | 1.96 | 100% |

Least-squares over the 7 bucket medians (near-perfect linear fit, within ~2%):

> **worker ≈ 55,600 cycles (baseline, sprite-count-independent) + 2,609 cycles × emitted_sprites**

So at ~75 sprites, ~196 K of the ~251 K worker (77%) is the sprite-count-driven term; ~55.6 K
(≈ 0.43 frame) is the baseline. Publication is a minor term (median 0.5 ms; p95 1.65 ms, just over the
~1.5 ms physical VBlank — a secondary "fit the commit in VBlank" goal).

**Caveat [M→HYP]:** emitted count co-varies with active-enemy count, so the 2,609/sprite slope conflates
(a) native sprite production and (b) the retained arcade AI/collision/actor tick. A worker-internal
split profile (arcade tick vs sprite production) is still owed to size each half exactly.

---

## 2. The slowdown is CPU saturation — scheduling cannot fix it [M]

The current architecture runs the whole gameplay tick inside IRQ6 at IPL7, overrunning VBlank into
active display. Event-stream evidence (HEAVY last-events): the gap between a worker's RTE (WR) and the
next IRQ6's publication entry (PE) is only **~827 cycles** (RTE + input + prepare). Everything else is
worker + publication. So at heavy load the CPU runs ticks **back-to-back with <0.5% idle**; the coalesced
VINT fires immediately when the worker RTEs.

Full tick period (PE→PE) ≈ 236,000 cyc ≈ 1.84 frames → max tick rate 128,009/236,000 ≈ 0.54–0.62, and
the trace measured 0.625. **The game is already running at the CPU ceiling for this workload.**

Therefore **moving the worker out of IRQ6 to the mainline will NOT make it faster** — the CPU is a single
core already executing those cycles during active display; relocating them changes privilege/context,
not cycle count. 208 K cycles cannot fit a 128 K-cycle frame by rescheduling. **Speed is restored only by
reducing worker CPU cost.**

> **CORRECTION / SUPERSEDED ORDER (per the Build-0401 directive).** The earlier text here and in §8
> implied the worker must first be optimized to fit one display frame *before* it can move out of IRQ6.
> **That order is superseded and wrong.** The selected architecture explicitly supports arbitrarily long
> ticks as preemptible mainline code: mainline runs Tick N; VBlank may interrupt it at any instruction;
> IRQ6 publishes the most recent COMPLETE immutable READY frame (or holds the previously displayed
> complete frame if none is newer), sets saturating `tick_pending = 1`, and RTEs; Tick N resumes at the
> exact interrupted PC and finishes; `WORK N -> READY N` atomically; then the next sequential tick begins
> when ownership permits. **No tick is skipped; no catch-up burst; a tick taking 2–3+ display frames is
> acceptable slowdown.** The worker does NOT need to fit one frame to run safely as mainline code. What
> stays true: moving it out of IRQ6 does not by itself reduce its cycle count. The corrected
> implementation order is: **(1) make publication state preemption-safe with WORK/READY/DISPLAYED
> ownership [Build 0401]; (2) move the complete worker out of IRQ6 to preemptible mainline [next build];
> (3) verify correct sequential slowdown / frame-hold; (4) THEN reengineer/optimize the sprite pipeline
> using the Sonic/Rainbow findings below (which remain BANKED for that later phase).** The IRQ6/mainline
> restructure is also expected to fix the likely **tearing** from committing at mid-screen V≈143 today.

At light load the mainline does spin (idle) but the game is already 60 fps there, so there is no hidden
headroom to reclaim. The overload is genuine.

---

## 3. It is NOT inherent to the Genesis, and NOT the clock [M/REF]

Clock: arcade 68000 8 MHz vs Genesis 7.67 MHz ≈ 4% — cannot explain a 184% overrun.

Why the arcade doesn't saturate: dedicated Taito co-processors — **PC080SN** (tilemap + scroll) and
**PC090OJ** (sprite generator). On the arcade the CPU writes a sprite list to object RAM (0xD00000) and
the chip renders autonomously in parallel (~O(1), ~tens of cycles per sprite), with sprite pixels in
dedicated sprite ROM (no per-frame pattern upload). The Genesis VDP needs the CPU to build the 80-entry
SAT and manage 64 KB VRAM pattern residency.

**But that is not why we are slow.** Retail/native Genesis ports of comparable games (Rastan Saga 2,
Rainbow Islands) run full-speed, and a native Genesis SAT write is ~tens of cycles/sprite. Our
**2,609 cyc/sprite is ~17× a native per-sprite cost**, so the cost is our implementation, not the
hardware. (Correcting an earlier overstatement that framed it as an "irreducible missing-chip tax" — the
*need* for software SAT building is real, but the *magnitude* is ours.)

---

## 4. Root cause: runtime residency resolve + arcade→Genesis translation, per piece, every frame [S]

PC090OJ **object-RAM emulation is already retired for gameplay** [S] (pc090oj_hooks.s: "The PC090OJ
D-range 0x00D00000..0x00D007FF is fully retired… no pc090oj_object_ram, no 0xD00000, no object-RAM scan"
for scene-1). So the cost is NOT legacy object-RAM scanning.

The cost is in the **native** path. Per gameplay frame:
`arcade sprite dispatch → genesistan_pc090oj_hook_target_41dae/45dfa → native_stage_dispatch_* →
pc090oj_native_emit_pass → per-piece .Lnq_emit_entry → staged SAT + tile-DMA worklist`.

Two expensive retained layers [S]:

1. **native_stage_dispatch_41dae/45dfa** still reproduces the full arcade **per-actor visibility
   classifier** — walks fixed actor slots (players/middle/enemies) and, per enemy, runs the arcade
   visibility predicates (states 0x17/0x1A/0x20/0x13/0x22/0x15 = arcade 0x3EFC8/0x3EFEC/0x3F01E/0x3F03C/
   0x3F064), several reads + branches each, before piece expansion.

2. **.Lnq_emit_entry does a per-piece arcade→Genesis translation every frame** that a native engine bakes
   offline:
   - per-piece viewport clip via `pc090oj_opaque_bbox` (4 byte reads + 4 compares) — native engines cull
     once per *object*;
   - **reverse residency resolve** — a 2-level directory+leaf lookup to find where this arcade tile lives
     in VRAM (this is the big one);
   - **variant remap** — `pc090oj_variant_group_base` / `pc090oj_variant_bank_slot` table lookups
     (chimera/four-armed/burst/flying-demon variants);
   - blank-bitset test, HUD-white tag, 0x200 Y/X wrap, palette-line lookup;
   - residency **MISS** → allocate cell + queue pattern DMA (the ~41%-of-publication pattern-VRAM churn).

**Crucial subtlety:** even for tiles that are *already resident* (no DMA), we still pay the per-piece
**resolve** (directory+leaf + variant + translate) every frame. That is the dominant ~2,600 cyc/sprite —
it happens whether or not a DMA fires. The DMA churn is extra on top for non-resident art.

---

## 5. The Sonic 1 native model (the target) [REF]

Source: `docs/reference/s1disasm/_inc/BuildSprites.asm`.

Pipeline: `object code → DisplaySprite (queue object pointer into one of N priority buckets) →
BuildSprites (once/frame) → per-object: ONE on-screen bounds cull, read obMap + obFrame, per-piece
buildsprite macro → sprite buffer → VBlank DMA to SAT`.

The `buildsprite` macro (no-flip) is **~20 instructions ≈ ~150 cycles per piece**:
- read relative Y, `ext.w`, `add.w d2` (object Y), write Y;
- copy size byte, write link byte;
- read the piece's 2 VRAM-setting bytes, **`add.w a3,d0`** where `a3 = obGfx` (the object's **base art
  tile**), write it;
- read relative X, `add.w d3` (object X), wrap 512px, write X; `dbf` next piece.

The decisive line is **`add.w a3,d0`**: the mapping stores a **relative** tile number and BuildSprites
adds the object's **resident base art tile**. **No residency lookup, no format translation, no per-piece
clip, no per-frame pattern DMA.** Art is loaded once per zone and resident; mappings (ROM) encode each
frame's pieces {Y-off, size, link, tile+flip+palette, X-off}; dynamic art uses a small **bounded DMA
queue**, not per-sprite streaming.

### Side-by-side (per piece)
| step | Sonic (~150 cyc) | Ours (~2,600 cyc/sprite) |
|---|---|---|
| bounds cull | once per object | **per piece** (bbox table) |
| tile number | `add a3,d0` (baked, resident) | **reverse residency resolve** (2-level table) |
| variants | none | **variant remap** (2 table lookups) |
| format/palette | baked in mapping | runtime translate + blank-bitset + HUD tag + 0x200 wrap + palette lookup |
| missing art | resident (never misses) | residency MISS → alloc + queue DMA |

**Root difference: Sonic resolves residency + format OFFLINE (baked mappings, resident art). We resolve
them AT RUNTIME, per piece, every frame.** That is the entire ~17× gap.

---

## 6. Redesign: resident/transient two-tier + baked mappings [design]

Organizing principle (Tighe): **classify sprite art by spawn pattern — that is the residency tier.**

| spawn pattern | examples | VRAM strategy | mapping baking |
|---|---|---|---|
| continuous / common | lizard men, hurry-up bats, player, HUD | **resident** — loaded once per level/segment, never re-streamed | **fully baked** absolute resident tile numbers (zero runtime resolve) |
| one-time / placed | Flying Demon, segment-specific enemies, bosses | **transient** — loaded once on activation into a reserved streaming window; freed when gone | baked **relative**; base resolved **once at load/spawn time**, then renders like resident |

This explains the field symptoms [HYP, consistent with §4]:
- **Flying Demon** (one-time, large/animated, likely not kept resident) → per-frame miss/DMA + resolve
  churn while on screen. New model: load once into the transient window, then cheap.
- **Hurry-up bats** (continuous, many) → should be resident; if flowing through the generic cache they
  thrash it, and even resident they pay the per-piece resolve today. New model: resident + baked → cheap.

### The actual fix: move residency resolution out of the per-frame per-piece path
- **Resident tier:** tiles at fixed VRAM addresses for the whole segment → bake absolute tile numbers
  into mappings → **no resolve ever**, Sonic-style `add base + relative`.
- **Transient tier:** base unknown until the enemy activates → resolve the base **once per spawn** (set
  its `obGfx`-equivalent base tile when loading its art into the window), then every frame is a cheap add.
- Net: residency resolution moves from **per-piece-per-frame** to **per-segment (resident) / per-spawn
  (transient)**. The per-piece emit collapses toward the ~150-cyc Sonic cost.

### Native BuildSprites-shaped per-frame path (replacing .Lnq_emit_entry's translation)
Per visible actor: one bounds cull → pick the baked mapping frame for its current animation → per piece:
`write Y = actorY + relY`, `write size/link`, `write tile = baseTile + relTile (|flip|palette)`,
`write X = actorX + relX`. Keep the existing double-buffered SAT; commit SAT + the bounded DMA queue in a
short VBlank. Retained arcade gameplay logic (movement/AI/collision/state) stays; only the render tail is
replaced — matching CLAUDE.md's target shape: *arcade semantic decision → mapping/piece selection →
compact native production → staged SAT → arcade-owned VBlank commit*.

### VRAM budget is the real constraint to design around
64 KB VRAM shared with planes/tiles. Per segment: reserve a **resident sprite-art block** (common/
continuous enemies + player + HUD) sized to fit alongside the planes, plus a **transient window** sized
for the worst-case simultaneous one-offs, plus the DMA-queue staging. This is a per-segment budgeting
exercise the offline baker performs.

### Data sources (consume existing work — do not re-derive)
- **Arcade spawn tables** / census (8-byte spawn records at arcade 0x4A086; families; per-round;
  `project_actor_identity_and_census`) → classify each family as continuous vs one-time per segment.
- Existing **enemy sprite lexicon / `corrected_semantic_families.json` / `enemy_palettes.json`** →
  art/palette per family (`feedback_build_on_existing_work`).
- The offline baker then: classifies tiers per segment, computes resident/transient VRAM budgets, and
  bakes per-family mappings (arcade code/frame → native SAT-ready pieces with resident or base-relative
  tiles), done once offline via the established JSON/Python translation pipeline.

---

## 7. Expected impact [HYP, bounded by §1 + §5]
Cutting per-sprite from ~2,609 → ~150–300 cyc would take the 75-sprite sprite term from ~196 K to
~15–25 K; the whole worker drops to ~70–80 K cyc ≈ 0.6 frame → **fits a frame → ~60 fps**. Exact gain
depends on the §1 caveat (how much of 2,609 is rendering vs the retained arcade tick), which the
worker-internal split profile resolves.

---

## 8. Implementation order (SELECTED — supersedes any earlier ordering in this doc)
1. **Build 0401 — WORK/READY/DISPLAYED immutable frame ownership.** Make publication state
   preemption-safe without changing scheduling (worker stays in IRQ6 for 0401). Spec + mechanical
   validation: `Andy_build0401_immutable_frame_ownership.md`.
2. **Next build — scheduling cut.** Move the complete retained Rastan worker to preemptible arcade-owned
   mainline (RTS semantics; IRQ6 becomes bounded publication + hardware service + `tick_pending` + RTE;
   input sampled at new-tick start). Verify correct sequential slowdown / frame-hold under overload.
3. **Then — sprite-pipeline optimization campaign** using the Sonic/Rainbow findings in §5–§6 (BANKED):
   baked mappings, resident/transient tiers keyed on spawn pattern, cheap BuildSprites-style SAT build.
   Profiling is CLOSED for the ownership/scheduling phase; the Build-0400 baseline above is the BEFORE.

Profiling-era open items (Pearson fix, Flying-Demon-vs-bats split, arcade-tick/producer internal split)
are **deliberately NOT pursued** — the Build-0400 measurements are sufficient as the baseline.

## Corrections recorded here
- Earlier "inherent/irreducible missing-chip tax" framing is **downgraded**: the cost is our runtime
  translation, not a Genesis limit (native ports run full-speed).
- "Scheduling rewrite will make it faster" is **false** — CPU-bound, back-to-back, <0.5% idle (§2).
- PC090OJ object-RAM emulation is **already retired for gameplay** (§4); the remaining cost is the
  retained arcade per-actor classifier + the per-piece runtime residency resolve/translation.
