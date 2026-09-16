# Andy — Build 0356 VBlank Budget Re-Audit (successor to the Build-0348 "VBlank Budget" study)

**Task:** ARCHITECTURE REVIEW / EVIDENCE RECONCILIATION. **Production code changed:** NO. **ROM:** NO.
**Build counter:** 356 (unchanged). **Best visual baseline:** Build 0353.

This updates the earlier study
[`Andy_sonic1_vs_rainbow_islands_plane_ab_architecture_and_title_completion.md`](Andy_sonic1_vs_rainbow_islands_plane_ab_architecture_and_title_completion.md)
(the "VBlank Budget" artifact, Build 0348 baseline). The original is preserved unchanged; this is a
successor, not an edit. All timing here is **Cody's physical-beam accounting** (authoritative);
**my retired 8-bit V-counter `%262` numbers are not used** — they were falsified (the NTSC V-counter
jumps `0xEA→0xE5`, so `%262` on that byte is invalid).

Evidence base: `Cody_build0354_vblank_accounting_independent_audit.md`,
`Cody_wram_ownership_repair.md`, `Cody_direct_palette_emit_performance.md`, and current source
(`dma.s`, `vdp_comm.s`, `tilemap_hooks.s`, `pc090oj_hooks.s`).

---

## Overall verdict on the original report

- **Aged well:** the diagnosis that Rastan's structural difference was *bulk plane publication*
  (whole 64-word rows ×N) versus Sonic/Rainbow's incremental/edge model; the recommendation to move
  horizontal Plane A to a Sonic column seam; the observation that `palette_pending` was the right
  gate; the note that the column-seam primitive already existed.
- **Now obsolete / implemented:** "Plane A horizontal = rows only, wrong axis" (implemented as a
  column publisher in Build 0350); "palette unconditional" (the CRAM DMA is gated by
  `palette_pending` today); and — most importantly — the *entire premise* that publication is the
  dominant frame cost. After Build 0356 the worst observed publication is ~63 lines (~24% of a
  frame), and the giant cost the study implicitly worried about (the sprite palette pass) is gone.
- **Was incorrect/incomplete at the time:** the study was explicitly "structural, not
  cycle-measured," and it conflated *control-flow ownership* with *physical VBlank timing*. Both are
  corrected below. It also had no visibility into the sprite palette-fixup cost, which turned out to
  be the real historical hotspot (48–96 lines), not plane publication.

---

## Control-flow ownership vs physical VBlank timing (must not be collapsed)

- **Logical owner:** unchanged and correct — `_vblank_service → dma_publish_frame → {palette, tiles,
  Plane B, Plane A, sprites, scroll}`, then the arcade tick resumes and only *stages* the next frame.
  Producers (arcade logic, Plane A/B, sprite prep, scroll, palette staging) run **outside**
  `dma_publish_frame`. Control-flow placement is as the original claimed.
- **Physical timing:** the publisher **frequently begins during active display**, not in VBlank —
  Cody measured **86.22%** of gameplay publications (Build 0356) *entering* during active display,
  and the publisher runs only ~1,009 times per 1,800 external frames. So a routine *owned by* the
  VBlank service routinely *executes* outside the physical VBlank interval, because the frame is
  already behind by the time it runs.
- **Revised wording:** *"Production is outside the publication phase (control-flow), and publication
  is logically the VBlank phase — but physically the publication phase usually starts mid-active-
  display because prior per-frame work has already overrun the VBlank window."*

---

## Claim-by-claim audit

### "Production is already outside VBlank" — **STILL TRUE (control-flow); MISLEADING (timing)**
Producers are outside `dma_publish_frame` (control-flow: STILL TRUE). But the physical-timing half is
new: publication enters active display 86% of the time. State both, never just the first.

### "Rastan can publish up to ~64 full rows/frame" — **PARTLY TRUE (per-plane, and it's 32 rows)**
The plane is 64 columns × **32** rows, so the true bulk ceiling is **32 rows × 64 words = 2048 words**
per plane (`vdp_commit_bg_strips_if_dirty` / `vdp_commit_fg_strips_if_dirty` loop `cmpi #32`). Audit:
- **Plane A horizontal:** NOT bulk — publishes the **entering column** (Build 0350 column PIO,
  `fg_col_dirty` → `vdp_commit_fg_columns_if_dirty`, ~32 words, autoinc 0x80). ~1.4 lines measured.
- **Plane A vertical:** entering **row(s)** via 64-word row DMA; a jump can dirty several rows at once
  (Cody's vertical rep = 13.162 lines of Plane A). Legitimate seam (a newly-exposed row is entirely
  new across all 64 columns).
- **Plane A/B full bulk (32 rows):** still reachable — `genesistan_hook_cwindow_clear`
  (tilemap_hooks.s:3428, a hook on the arcade C-window clear) sets `0xFFFFFFFF` on *both* dirty masks
  → a full 32-row refresh. This is the **only** path that still produces the old "many full rows"
  behavior, and it is **arcade-transition-driven, not per-frame**.
- **Plane B normal:** near-zero (fixed vocabulary since Build 0308; Cody median = 45 dots ≈ 0 rows).
So the old "64 rows every frame" fear is **falsified for steady state**; the bulk path survives only
as an exceptional transition refresh (see the 37.8-line event below).

### Plane A horizontal publication — **old P3-horizontal = IMPLEMENTED (Build 0350)**
Selector-0 emits one entering logical column into `staged_fg_buffer`, flags `fg_col_dirty`, and the
VBlank column writer PIOs ~32 words down the column (autoinc = plane row stride). No horizontal path
dirties full rows any more. Cost ~1.4 lines. This is exactly the study's "publish the entering
column" recommendation, and it is done.

### Plane A vertical publication — **seam-shaped, cost is real entering-row work**
Vertical motion publishes entering rows (selector-1/2 + pan-up/down, 64-word row DMA each). The
13.162-line vertical representative is **multiple entering rows on a jump**, each a legitimate 64-word
seam (the whole row is newly exposed). It is **not** redundant re-send of already-visible cells in the
steady case. Caveat: my Build 0353 report flagged a residual — at non-plane-aligned horizontal scroll
the vertical source needs a ring-rotation term; if that is wrong it could republish rows with slightly
wrong content (a *correctness* risk, not extra *volume*). That is a separate open item, not a budget
finding. **NEEDS MEASUREMENT:** whether any vertical frame re-DMAs rows whose content did not change.

### Plane B publication — **normal ≈ 0; the 37.8-line event is an exceptional transition bulk**
`vdp_commit_bg_strips_if_dirty` DMAs one 64-word row per set `bg_row_dirty` bit, up to 32. Cody's
distribution is bimodal: median 45 dots (≈0 rows) but p95/max 18,472 dots (37.852 lines = the full
32-row bulk). Trigger = `genesistan_hook_cwindow_clear` (arcade C-window clear at scene/transition).
So: **not a normal scroll event; a one-time-per-transition full-plane repaint.** Is it "resending more
than the exposed region requires"? For that event, yes in the seam sense — but there is nothing
resident to preserve across a clear, so a full repaint is legitimate. The actionable point is *timing*
(a transition bulk spilling into active display), not *volume waste*.

### Palette publication (old P1) — **ALREADY IMPLEMENTED**
`vdp_commit_palette` is gated: `tst.b palette_pending; beq .Lpal_none`. The 64-word CRAM DMA fires
only when `palette_pending` is set; Cody measures palette at 0.05–0.10 line. Note the important
distinction the task calls out: Build 0356 removed the sprite palette **semantic** pass
(`.Lnative_pal_fixup`) — that is *not* the CRAM DMA. The CRAM DMA (P1's subject) was already
flag-gated before 0356. **P1 would save nothing further.**

### Sprite publication — **transformed by Build 0356; palette pass gone**
Build 0356 replaced the per-emitted-sprite route search + second SAT palette pass with a
scene-selected 512-byte direct LUT (`current_sprite_palette_map[effective_bank]`, O(1) at emit).
Measured palette-pass cost fell from 48–96 lines to **0**. Current sprite cost:
- pattern DMA: worklist ≤ 12 entries, commonly 0; 128 bytes/entry; up to ~19 lines when full;
- fixed SAT DMA: 320 words / 640 bytes ≈ **1.0 line**;
- direct palette lookup: folded into emit, below the logger's resolution (sub-line).
**Classification now: conditional bottleneck** — only heavy when the pattern worklist is populated;
otherwise a ~1-line fixed SAT cost. (It was a *major* bottleneck through Build 0355.)

### Scroll publication — **STILL small/unconditional**
`vdp_commit_scroll` ≈ 0.93 line, every publication. Comparison with Sonic/Rainbow still holds; not a
concern.

### P2 — coalesce dirty rows — **LOW VALUE now (NEEDS MEASUREMENT to justify)**
Contiguous dirty rows are issued as separate 64-word DMAs, each with its own register-program setup.
But: Plane A steady state is a column (not rows); Plane A vertical is a bounded seam; Plane B steady
state is ~0 rows. The only place coalescing would matter is the exceptional 32-row transition bulk —
and there the cost is dominated by byte transfer during active display, not per-DMA setup. Cody's SAT
DMA (320 words, one DMA) ≈ 1 line and a 64-word row ≈ ~0.85–1 line suggest setup is a small fraction.
**Verdict: not worth it on current evidence; do not adopt merely because fewer DMAs sound tidier.**

### P3 — publish a seam, not the viewport — **mostly IMPLEMENTED**
- Plane A horizontal: **implemented** (column, 0350).
- Plane A vertical: **seam-shaped** (entering rows) — correct in shape; the only open item is the
  ring/source-correctness residual, not volume.
- Plane B horizontal/vertical: **near-zero in steady state** (fixed vocabulary); no seam work needed.
- Special/bulk: the transition C-window clear is a legitimate full repaint, not a seam candidate.
**Overall P3 verdict: substantially achieved.** The renderer already adopted the Sonic/Rainbow
incremental model for the hot paths; what remains "bulk" is transition-only and legitimate.

### P4 — display-off around publication — **conditionally attractive now, but not clean**
Publisher durations are now 6.2 (stationary/horizontal), 17.9 (vertical), 22.2 (sprite-heavy), 63.1
(worst). Since 86% of publications *enter during active display*, a display-off bracket would blank
part of the active picture whenever the publisher runs late — i.e. it would **hide** overrun as a
black band, not remove it, exactly what the `_do` variant shows today. Display-off is only safe once
the publisher reliably *fits* the VBlank window *and starts in VBlank*; neither is true (it starts in
active display 86% of the time). **Verdict: still diagnostic, not production-worthy. Do not enable.**
The real precondition is fixing *why the publisher starts so late* (upstream CPU), not bracketing it.

### P5 — per-frame publication budget / HBlank deferral — **UNNECESSARY now / future robustness**
The worst observed publication is ~63 lines (~24% of a frame) and is bounded by the (exceptional)
transition bulk + pattern DMA. There is no unbounded per-frame publication that needs a safety valve;
deferring plane publication would risk tearing and desync from arcade producer state for no current
benefit. **Verdict: unnecessary at Build 0356; revisit only if a genuinely unbounded case appears.**

### Rainbow Islands comparison — **still structurally valid (carried, not fully re-audited)**
The original read of `build/rainbow_islands_genesis.disasm.txt` (0x0380–0x041A): flag-gated
conditional DMA (tiles/tilemap-strip/palette), display-off bracket, SAT/scroll each frame. Rastan has
since matched the *flag-gated palette* and *incremental Plane A* pieces. I did **not** re-open the
Rainbow disasm byte-for-byte this task; the structural comparison stands, and a spot re-verify is a
cheap follow-up if you want the exact strip-word counts refreshed.

### Sonic 1 comparison — **still valid (re-read this session)**
`LoadTilesAsYouMove` / `DrawBlocks_TB`/`_LR` / `Calc_VRAM_Pos`: per-direction edge flags → draw only
the entering row/column with strided VDP writes. Rastan's Build 0350 column publisher is a direct
adaptation of `DrawBlocks_TB` (autoinc = row stride). Sonic-specific game-loop/PLC policy remains
correctly *not* imported. No correction needed.

---

## Build 0356 side-by-side (physical-beam; supersedes the structural table)

| Work type | Rastan 0356 | Rainbow Islands | Sonic 1 | Verdict |
|---|---|---|---|---|
| Game logic | arcade tick, outside publish | outside | outside | fine |
| Graphics production | outside publish (producers stage) | outside | outside | fine |
| CRAM publish | flag-gated (`palette_pending`), ~0.05–0.1 ln | flag-gated | fixed buffer | P1 already done |
| Scroll publish | ~0.93 ln, unconditional | each frame | each frame | fine |
| Sprite SAT publish | fixed 640B ≈ 1.0 ln | — | fixed | minor fixed cost |
| Sprite pattern load | ≤12 entries, often 0; ≤~19 ln full | — | bounded PLC | conditional |
| Sprite palette | **direct O(1) LUT at emit, ~0 ln** (was 48–96) | n/a | n/a | **fixed by 0356** |
| Plane A horizontal | column PIO ~1.4 ln (seam) | strip | column/edge | implemented |
| Plane A vertical | entering-row DMA; ~13 ln on jump | — | row/edge | seam; correctness residual open |
| Plane B normal | ≈0 (fixed vocab, 0308) | dirty strip | edge | fine |
| Plane B worst/bulk | 32-row refresh ~37.8 ln, transition-only | — | — | exceptional, legitimate |
| Display-off | diagnostic `_do` only | production | n/a | keep off (P4) |
| Publication budget | none needed | PLC-bounded | PLC/HBlank | unnecessary (P5) |

## Old-recommendation status

| Old rec | Build-0356 status | Evidence | Keep/change/remove |
|---|---|---|---|
| P1 flag-gate palette | **IMPLEMENTED** | `vdp_commit_palette` gated by `palette_pending`; ~0.05–0.1 ln | remove from backlog |
| P2 coalesce rows | **LOW VALUE / NEEDS MEASUREMENT** | steady state has ~no multi-row DMAs; setup is small vs transfer | do not adopt on current evidence |
| P3 seam publication | **MOSTLY IMPLEMENTED** | Plane A H=column(0350), V=row seam; Plane B≈0 steady | keep; only transition bulk remains |
| P4 display-off bracket | **NOT YET / diagnostic** | 86% of publications start in active display | keep off; fix upstream lateness first |
| P5 publication budget | **UNNECESSARY** | worst ~63 ln, bounded | drop unless an unbounded case appears |

## Then vs now

| | Original report (Build 0348, structural) | Build 0356 (measured) |
|---|---|---|
| Sprite palette pass | (invisible to the study) enormous — 48–96 ln | **gone (~0 ln)** |
| Plane A horizontal | rows only, wrong axis, whole 64-word rows ×N | entering column PIO ~1.4 ln |
| Plane A vertical | row-dirty→row-DMA (correct shape) | entering-row seam; ~13 ln on a jump |
| Plane B | up to 32 dirty 64-word rows | ≈0 steady; 37.8 ln transition bulk only |
| Palette (CRAM) | "unconditional" | flag-gated, ~0.05–0.1 ln |
| Worst publication | (estimated large) | **63.1 ln ≈ 24% of a frame** |

---

## Current Build 0356 bottlenecks (ranked, measured)
1. **Sprite pattern DMA when the worklist is populated** — up to ~19 lines (≤12 × 128 B), conditional.
2. **Plane B transition bulk** — ~37.8 lines, exceptional (C-window clear), spills into active display.
3. **Plane A vertical seam on jumps** — ~13 lines, legitimate entering-row work.
4. Fixed SAT DMA ~1 line; scroll ~0.93 line; palette ~0.05–0.1 line; the leftover **VC_MARK
   instrumentation ~0.78 line** (see below).

## The old "64 full rows" claim
Still true: **PARTLY.** Current maximum = **32 rows × 64 words per plane** via
`genesistan_hook_cwindow_clear`'s `0xFFFFFFFF` dirty set. Exact path: arcade C-window clear at
scene/transition, not per-frame. Steady-state Plane A horizontal is a column, not rows.

## The Plane B 37.8-line event
Cause: `genesistan_hook_cwindow_clear` full-plane repaint (32 rows). Rows/words: up to 32 × 64 = 2048
words. Normal or exceptional: **exceptional** (transition; median is ~0 rows). Redundant publication:
**PARTLY** — a full repaint re-sends the whole plane, but across a clear there is nothing resident to
keep, so it is legitimate; the only improvement would be bracketing it display-off since it is a
transition moment.

## Whole-game speed conclusion
**Does publication remain the primary proven cause of perceived slowness? NO (with a caveat).**
- The worst publication is ~63 lines (~24% of one 262-line NTSC frame); typical is 6–22 lines. Even
  the worst leaves ~76% of the frame. So publication *cannot* be consuming the whole frame.
- Yet the publisher runs only ~1,009 / 1,800 external frames and **starts in active display 86% of
  the time** — which means the frame is *already behind before publication starts*. That points the
  remaining slowness at **upstream per-frame CPU** (the arcade tick + native Plane A/B/sprite
  producers that run before `dma_publish_frame`), not at publication.
- **What this study cannot establish:** whole-game CPU attribution. This is a VBlank/publication
  audit; it does not profile the arcade tick or the producers. The next investigation should be a
  small read-only measurement of *pre-publication* per-frame CPU (arcade tick + producers), not more
  publisher work. That is where Tighe's "maybe a little" improvement is explained: 0356 removed a big
  chunk of publication cost, but publication was no longer the whole story.

## Frame/tick relationship
- Genesis external frames sampled: 1,800 (each capture). Publisher invocations: 1,123 (0354 cap 1),
  1,257 (0356). Gameplay publications: 875 / 1,009. So **publication ≠ once per external frame**
  (~62–70%).
- Authoritative **arcade ticks / gameplay advancements per 1,800 frames: NEEDS MEASUREMENT.** Cody's
  data proves the publisher is decoupled from external frames and notes gameplay "advanced
  differently in equal external time," but does not count arcade ticks directly. A publication is one
  `dma_publish_frame` call; it is *not* provably one arcade gameplay advancement. Mark NEEDS
  MEASUREMENT.

## D00462
Still reproducible in Build 0356 (Tighe, BlastEm, map segment 5). Build 0355 WRAM ownership repair did
**not** eliminate it; Build 0356 direct palette emit did **not** eliminate it. **Separate open issue**,
not conflated with performance or VBlank publication.

## Note on production hygiene (not a change, an observation)
The numbered Build 0356 ROM still carries my Build 0354 `VC_MARK`/`vblank_vc` instrumentation in
`dma_publish_frame` (7 V-counter reads/stores, ~0.78 line/publish). Cody's timing used the external
beam harness, so the in-ROM marks are now dead weight. They should be removed from the next clean
production build (small, but it is diagnostic scaffolding shipped in a numbered ROM).

## Updated priority
- **Investigate next:** upstream per-frame CPU (arcade tick + Plane A/B/sprite producers) via a small
  read-only measurement — that is where the remaining slowness now lives, and this study cannot see
  it. Secondary: sprite pattern-DMA volume when the worklist is populated.
- **Do NOT do yet:** P4 display-off (would mask overrun), P5 budget (unnecessary), P2 coalescing
  (unjustified), further palette/CRAM gating (already done). And do not re-attack the sprite palette
  path — 0356 already reduced it to ~0.

**Status: COMPLETE.** No production source, spec, ROM, or build-counter change.
