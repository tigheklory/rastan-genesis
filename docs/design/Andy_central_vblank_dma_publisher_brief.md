# Central VBlank DMA Publisher — Design Brief (handoff for the next build)

**Author:** Andy · **Date:** 2026-09-04 · **Status:** proposal / brief for ChatGPT to author the first
implementation prompt. Self-contained.
**Related:** OPTIMIZATIONS.md (OPT-004 DMA-halt, OPT-005 essential-VBlank split), CLAUDE.md target-shape
mandate, `docs/design/Andy_clean_vram_repack_676_contiguous_layerA.md` (current VRAM map).

---

## 1. Purpose
Make the next architectural task a **single Genesis VDP publication engine (`dma.s`)** that is the sole
owner of all runtime DMA. Today five graphics subsystems each program the VDP independently during VBlank;
this brief consolidates them into one bounded, coalescing, publish-first VBlank publisher — the proven
Sonic-1 / Mega-Drive idiom — and sequences it as low-risk incremental numbered builds. This should
**supersede** the piecemeal per-subsystem DMA cuts (they become trivial *inside* the engine).

## 2. Current state — the hodgepodge (measured)
All runtime DMA is triggered inside native `_vblank_service` (vdp_comm.s:173) before it `jmp`s to the
arcade handler 0x3A208. Five independent DMA-trigger sources, each with its own setup + CPU-halt:

| # | Source (file) | Trigger | Count/VBlank | Note |
|---|---|---|---|---|
| 1 | `vdp_commit_palette` (vdp_comm.s) | 1 CRAM DMA, **unconditional** | 1 | 64 words even when unchanged (0325→0336 regression) |
| 2 | `vdp_commit_bg_strips_if_dirty` | 1 DMA **per dirty Plane-B row** | 0–32 | full 64-word row even if ~1 cell changed |
| 3 | `vdp_commit_fg_narrow_strips`→`fg_strips_if_dirty` (tilemap_hooks.s) | PIO narrow cols **+** 1 DMA per dirty Plane-A row | 0–32 | mixed PIO+DMA |
| 4 | `.Lvcs_tile_dma` (pc090oj_hooks.s) | 1 DMA **per sprite pattern uploaded** | 0–12 | worklist `.space (12*4)` |
| 5 | `.Lvcs_sat_dma` | 1 SAT DMA, **unconditional** | 1 | fixed 80 slots / 640 B |

`vdp_commit_tiles_if_dirty` (48-word), the fg narrow cols, and `vdp_commit_scroll` are **PIO** (CPU→VDP),
not DMA. **Per-VBlank DMA count: MIN 2, MAX ~78, typical scroll ~10–40.** Each DMA pays ~7 control-port
setup writes (`vdp_dma_words_to_vram`: autoinc 0x8F02 + length 0x93/0x94 + source 0x95/0x96/0x97 + trigger)
before the transfer. Worse, production (`vdp_prepare_sprites` builds the SAT) is **interleaved** with the
commits inside VBlank, so the transfers slip past the vblank window into active display → CPU-halt on
visible lines **and** the CRAM-dot noise.

The **producer side is already correct** (CLAUDE.md target shape: arcade decision → mapping → compact
native production → **staged** SAT/Plane/palette buffers → arcade-owned VBlank commit). The staged buffers
already exist: `staged_sprite_sat`/`_b` (double-buffered), `staged_bg_buffer`, `staged_fg_buffer`,
`staged_palette_words`, `staged_scroll_*`, `pc090oj_tile_dma_worklist`. We only ever finished the producer
half; the five consumers were never unified.

## 3. Target architecture — one publisher, producer/consumer pipeline
Exactly the Sonic-1 `VintSub` model:
```
Frame N: arcade logic + native producers -> write final staged buffers + set bounded dirty metadata
VINT (N+1): dma.s runs FIRST, owns the VDP:
    publish sprite pattern uploads actually required (coalesced)
    publish Plane-A/Plane-B pattern uploads actually required
    publish changed Plane-B nametable spans (coalesced contiguous)
    publish changed Plane-A nametable spans (coalesced contiguous)
    publish whole SAT (640 B, unconditional -- Sonic + Rainbow both do this)
    publish palette (whole 64-word CRAM) ONLY when the palette producer set its change flag (Rainbow model)
    publish scroll/registers
  -> VDP-critical section DONE, still inside vblank
then: ordinary arcade VBlank/frame logic resumes (may spill into active display harmlessly = CPU/WRAM only)
```
Producers only: write staged output, set bounded dirty metadata, enqueue pattern descriptors, record
active lengths/ranges. **No producer initiates DMA.** `dma.s` consumes the completed previous-frame state.

**Publication descriptors are tiny and fixed** (source addr, VRAM dest, word count, optional type) over the
**already-staged buffers** — NOT new shadow copies, NOT a runtime allocator/LRU/search/job-system.

## 4. Why this is right (the three references)
- **Sonic 1 IS this design.** `VintSub` runs first at VINT and is the sole VDP owner: full-palette DMA,
  full sprite-table DMA, scroll, and edge-tile loads — all from RAM buffers the *previous* frame built.
  Game logic runs after VInt returns. Producer→(one-frame)→publisher. (Confirmed in the local s1disasm:
  `writeCRAM` macro DMAs the whole palette every frame; `VintSub` at sonic.asm:729+.)
- **Rainbow Islands = the same Taito PC080SN/PC090OJ arcade hardware** as Rastan (CLAUDE.md cites its MD
  implementation as a structural reference). The faithful-port lesson for that hardware: **hardware scroll
  + upload only the newly-revealed seam (one edge column/row) per frame** — never re-DMA whole nametable
  rows. Our sources #2/#3 do full-row DMAs (up to 64/frame during scroll); the central publisher first
  coalesces them, and the deeper follow-up is migrating the plane path to a **seam/column update**.
- **It finishes the project's own stated target shape** (the consumer half of "…→ staged data → arcade-
  owned VBlank commit"). This is completing existing architecture, not adding a new layer.

## 4a. VERIFIED reference — the Rainbow Islands *retail Genesis ROM* (NOT our SGDK builds)
The valid structural reference is the **actual Rainbow Islands retail Genesis ROM** — a separate shipped
game with no SGDK — captured in-repo:
- **`build/rainbow_islands_genesis.disasm.txt`** — the retail ROM disassembly.
- The RAINBOW-ISLANDS portions of `docs/design/build316_vs_rainbow_islands_genesis_vblank_noninterrupt_vdp_report.md`
  document Rainbow's VBlank handler **0x0380–0x041A**: ack VBlank → request Z80 bus → **display off** → DMA
  tiles → **DMA SAT (unconditional)** → copy dirty tilemap rows → upload palette → **display on** → write
  scroll. Request flags: tile `0xFFFFF690`, tilemap `0xFFFFF63C`, palette `0xFFFFF680`; SAT + scroll
  unconditional. **That is the concrete template for `dma.s`.**

> **DO NOT use the old SGDK/C Genesis *port of Rastan* (`apps/rastan/`, `main.c`, builds 316/317) as the
> vblank template.** That port had **SGDK's hardcoded built-in vblank handler fighting the arcade vblank**,
> so its Genesis-side vblank/commit behavior is confounded and unreliable as a model — even though 317 was
> nominally a "single VBlank commit." This is about *our old Rastan SGDK port*, NOT the Rainbow Islands
> retail ROM (a separate game, no SGDK, still valid). SGDK/C-era Rastan material is trustworthy **only for
> arcade-side facts**, not for the Genesis publication design.
> The current **assembly** era (`apps/rastan-direct`) has no SGDK vblank; it is the **clean slate** on which
> to apply the Rainbow retail-ROM model. (The producer staging — staged_bg/fg_buffer, staged_palette_words,
> staged_scroll_*, staged_sprite_sat — already exists in the ASM era and is reused as-is.)

## 4b. Display-off is the TARGET, coupled to publish-first (Build 0227 was a workaround)
Rainbow's commit runs **display OFF → transfers → display ON** inside VBlank. Rastan currently runs display
**ON** — but that was a **workaround, not a principle**: the graphics/DMA ran *after* the servicing overran
vblank, so display-off would have blanked the *active picture*. Once publish-first puts every transfer at
the **start** of vblank and they complete before active scanout, **display-off during the commit is correct
again** (and faster — forced blank gives full VRAM bandwidth, and it's inherently CRAM-safe → no dots). So:
- **Adopt display-off bracketing as the target**, together with publish-first — this is the Rainbow model.
- **Make it a build flag (Tighe): every build emits both a display-ON and a display-OFF ROM**, at least
  initially, so the two can be A/B-tested on hardware/emulator and the winner becomes the release default.
  Add a compile-time flag (e.g. `RASTAN_VBLANK_DISPLAY_OFF ?= 0`) in the same style as the existing
  `RASTAN_DIAG_*` flags, producing an extra numbered variant (suffix e.g. `_do`) alongside `_NNNN`/`_d`/`_s`.
- **Sequencing/expectation:** display-off produces a *correct* picture only once the entire commit provably
  fits the ~38-line NTSC vblank window. With today's per-row plane DMAs (up to 64 rows) it may NOT fit, so a
  display-off variant built *before* publish-first + bounded plane transfers will **blank part of the active
  picture** — which is itself a useful diagnostic (the blanked band = how far the commit overruns, like the
  `_d` bar). So the flag is worth adding early for measurement, but display-off only becomes the *shippable*
  config after publish-first (step 6) + the plane transfers are bounded (coalesced → seam model).
- Rainbow's Z80-bus request and VDP-reg-1 shadow (`0xFFFFF624`) are still **audit-vs-transplant** against our
  current sound/VDP setup — adopt if they fit, don't copy blindly.

## 5. Three refinements to bake into the prompt (my analysis)
1. **Lead with publish-first ordering, not coalescing.** The dominant cost is production interleaved with
   commits pushing DMA into active display. Publishing the *already-complete previous frame* immediately at
   VINT (fast, inside vblank) and moving next-frame CPU production after the VDP-critical section is the
   biggest win (OPT-005) and it also fixes the CRAM dots. Coalescing (fewer setups) is a real but secondary
   win.
2. **Keep the Rainbow-Islands seam model in view for planes.** Coalescing contiguous rows reduces the DMA
   *count*; the per-row *full-row rebuild* is the deeper inefficiency during horizontal scroll. Plane
   migration should aim at hardware-scroll + bounded edge-seam updates, not just coalescing oversized rows.
3. **Migrate incrementally, byte-identical per step, behind the gates.** This touches every producer's
   commit path, and this codebase hides coupling (OPT-003 clobber; VRAM gate assumptions). No big-bang.

## 6. Migration sequence (numbered builds; each byte-identical-output + gate-verified)
**Buffer policy (Rainbow model, adopted after the ChatGPT review):** SAT + scroll = **whole buffer, every
frame, unconditional** (both Sonic and Rainbow do this; tiny, fixed, zero metadata). Palette = **whole
64-word CRAM transfer, but only when the palette producer set a single change flag** (Rainbow's
`0xFFFFF680`-style flag) — Rastan's palette is mostly static, so most frames do zero CRAM work. This is a
*single semantic flag the producer already knows to set* (waterfall/sunset/scene-load), NOT a per-entry
dirty tracker. The colored dots are a *timing* problem fixed by publish-first ordering (step 6), not by the
flag. **Only the scrolling planes transfer a subset** (dirty rows now → edge seam later) — a 4 KB plane
can't be re-DMA'd whole; that's the scrolling model, not a gate.

1. **`dma.s` skeleton** — one owner of DMA-register programming: `dma_vram` / `dma_cram` / `dma_vsram` /
   `dma_upload_block` (display-off bulk loader for scene_load). `_vblank_service` calls these instead of
   inline triggers. **No behavior change.** Prove output identical (byte-identical VDP output) — this is the
   verifiable waypoint before any reordering.
2. **Palette** — migrate into `dma.s` as a single whole-palette (64-word) CRAM transfer, published only when
   the palette producer's change flag is set (Rainbow model). SAT stays whole-table.
3. **SAT** — migrate into `dma.s` as a single whole-table (640 B) transfer every frame, unconditional
   (Sonic + Rainbow). No active-prefix / no length tracking.
4. **Sprite pattern uploads** — coalesce contiguous slots into single DMAs; leave non-contiguous separate.
5. **Planes** — the real scroll cost. Coalesce contiguous dirty rows now; then migrate toward the
   Rainbow-Islands / Sonic model: hardware scroll + upload only the newly-revealed edge seam (column/row),
   not full-row rebuilds.
6. **Flip to publish-first ordering** (publish the completed previous frame at the top of VBlank, before
   any next-frame CPU production) + enforce the invariant "`dma.s` is the sole runtime DMA owner." This is
   the biggest single win: it moves all VDP-critical transfers safely inside vblank (fixing the CRAM dots
   and the halt-during-active-display cost) and lets next-frame CPU work spill harmlessly into active
   display.

**Note on ordering of value:** steps 2–3 are near-free simplifications (fewer owners, no new cost). The
real performance comes from **step 6 (publish-first)** and **step 5 (plane seam)**. Steps 2–4 exist mainly
to make `dma.s` the single owner so step 6 can reorder the whole frame cleanly.

## 7. Guardrails (must be in the prompt)
- **No generic runtime allocator / LRU / residency search / visibility scan / virtual VDP / job system.**
  Fixed, concrete descriptors over existing staged buffers only.
- **Byte-identical VDP output at every step** except where a step is an explicitly documented behavior
  change (palette flag-conditional publish) — and that must be proven equivalent to what actually reaches CRAM.
- **Arcade authority preserved.** Producers = arcade semantics, untouched. `dma.s` is the consumer only. It
  is `_vblank_service` restructured (already runs before `jmp 0x3A208`), not a new owner of the VBlank.
- **One-frame latency** is accepted (staged double-buffers already imply it); verify input→display feel on a
  real R1/P1 playthrough (Sonic ships with exactly this).
- **Display-off scene load** stays the one exception, but routed through `dma.s` (`dma_upload_block`), so DMA
  mechanics live in exactly one place.
- Every build: seven-epoch + canonical + gameplay-entry gates; `_d` overrun bar before/after; triple-build
  `_NNNN`/`_d`/`_s` convention; sequential numbering; GENESIS NTSC.
- OPT-003 stays deferred; it is reverted from the tree (its 0x034C clobber fails the epoch gate).

## 8. Acceptance / performance evidence
- Per step: gates PASS; VDP output equivalent; the `_d` servicing band should shrink as production leaves
  the VDP-critical window and DMAs are gated/coalesced.
- Report per build: DMA count/VBlank (min/typical/max) before vs after; SAT bytes; CRAM commits/frame;
  plane DMA count; and the qualitative `_d` band. Structural reduction (fewer/lighter DMAs, no active-
  display spill) is sufficient evidence per the cumulative-savings policy — no minimum threshold.

## 9. What ChatGPT should author first
A single build prompt for **step 1 + step 2 (+ optionally step 3)**: create `dma.s` as the sole DMA owner
(mechanics moved, **no behavior change**, VDP output byte-identical — the verifiable waypoint), then migrate
the **palette** (whole 64-word CRAM, published only on the producer's change flag — Rainbow model) and
optionally the **SAT** (whole 640-byte table, unconditional). This is a pure ownership consolidation that
lands a real ROM and establishes the engine steps 4–6 plug into, without a big-bang refactor and without
inventing per-subsystem change-tracking. Read §4a (build 316/317 + Rainbow RE) first and reuse it; heed §4b
(display-off bracketing is the eventual target with publish-first, but adopted only once the commit fits
vblank — NOT in this first build; keep display-on for now). Keep the descriptor set tiny and
concrete; do not build the allocator monster. **Note:** this first build does NOT fix the CRAM dots by
itself — the dots are resolved by step 6's publish-first ordering; do not add a gate
to chase them here.
