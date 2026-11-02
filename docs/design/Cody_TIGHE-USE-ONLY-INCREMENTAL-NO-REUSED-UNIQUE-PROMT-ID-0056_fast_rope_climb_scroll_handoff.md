# R1-S2 intermittent Plane A corruption during fast rope climbing — source-only handoff

Date: 2026-11-02  
Agent: Cody  
Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0056`  
Reference: Build 0528 / PROMT-ID-0055

## Scope and observed result

Tighe reports that Build 0528 mostly fixes R1-S2: an ordinary Up-only climb can complete without
corruption, while repeatedly jumping up a rope against an adjacent wall can intermittently corrupt
Plane A. Collision and traversal remain correct. This investigation made no production change, ROM,
trace, save state, test harness, or generated asset.

The source supports treating this as a sequence/publication problem before suspecting deterministic
offline row contents. It does **not** yet prove that jumping itself is the cause.

## Verified facts

### Movement and camera cadence

- Every player frame enters `player_main_update_51090`, which calls player/input state
  `$052732` first and scroll dispatcher `$055650` second (`$051090..$05109C`). Thus movement state
  establishes the scroll flags and delta before Plane A publication.
- `$052732` clears `A5+$10D0` at the start of the player update. The movement state then sets the
  current frame's direction flags; stale flags do not carry across frames.
- The wall/jump candidate branches at `$051F40..$051FC6` add 16 to a horizontal accumulator and 5
  to vertical accumulator `A5+$1262`. Ordinary rope motion at `$051FC8..$052008` adds one per frame
  to `A5+$1262` or `A5+$1264`. This proves different input techniques can create different movement
  accumulator cadence.
- The common movement consumer `$0517FA` cancels opposing vertical accumulators, consumes at most
  four units per frame, stores that step in `A5+$10DE`, and calls `$053850` or `$0538EA`.
  `$0538D6/$053942` then set scroll flag bit 0/1 and write the actual camera delta to `A5+$10DA`.
  Consequently the jump-assisted route can sustain more consecutive four-pixel camera steps, but
  no separate jump camera routine and no camera increment above four pixels is proven.
- `$055650` processes vertical flag bit 0 through `$055696` before bit 1 through `$05572E`.
  The movement accumulator cancellation supports one vertical direction per normal player frame,
  although direction may reverse on adjacent frames.

### Build 0528 no-publication path

- Hooks at arcade `$055704` and `$055790` enter
  `genesistan_plane_a_pan_publish_entering_rows_down/up` in
  `apps/rastan-direct/src/tilemap_hooks.s:945` and `:981`.
- Each helper derives old and new logical tops from `A5+$10B0`, iterates until they match, and calls
  `.Lplane_a_publish_logical_row_native` for every crossed row (`tilemap_hooks.s:963-975` and
  `:999-1009`). It therefore contains no single-row-only assumption. With the proven delta limit of
  four pixels, at most one eight-pixel boundary can be crossed in one player update anyway.
- The Build 0528 selector decision is at `tilemap_hooks.s:1407-1450`. It chooses among current
  dynamic geometry, `A5+$013E-1` precompiled predecessor rows, and the previous selector-0 pointer
  revolution using current selector `A5+$10A8`, completed selector `A5+$132C`, and record
  `A5+$013E`. This is stateless across calls and assumes that tuple completely describes the ring
  after every ordering of ordinary publication, record completion, and no-publication motion.
- The row is completely written to `staged_fg_buffer` before its physical bit is ORed into
  `fg_row_dirty` (`tilemap_hooks.s:1391-1558`). VBlank commits Plane A rows before committing scroll
  (`apps/rastan-direct/src/dma.s:81-92`), and `vdp_commit_fg_strips_if_dirty` performs the full
  64-word row DMA before clearing its dirty bit (`apps/rastan-direct/src/vdp_comm.s:323-354`). The
  source therefore does not support a simple expose-before-stage race inside this path.

### Offline rows

- The generated pan rows are immutable. Build 0528's static gates checked every cell of their
  declared records and 16,384 no-publication predecessor cells.
- Normal climbing can display the same scene correctly, while the fault is intermittent under a
  different movement sequence. No source evidence makes deterministic Python row generation vary
  by input or frame.
- The existing gates prove individual row values and the Build 0528 predecessor arithmetic; they do
  not prove every temporal sequence of `(10A8,132C,013E,10CA,10CC,10B0,10DA)` across consecutive
  frames. Runtime selection/publication remains the stronger hypothesis.

## Remaining hypotheses, ordered

1. **Temporal record/ring-state selection — strongest.** Rapid consecutive crossings can place a
   no-publication call immediately before or after ordinary `$055948`, group completion
   `$0558A2/$0558C6`, or record advance `$0558E0`. Build 0528 selects solely from the current tuple
   and uses the top-level current-selector test at `tilemap_hooks.s:1407` to decide whether the
   entire predecessor logic is considered. The tuple-to-retained-ring rule is proven for the
   initial record-16-to-17 case, not for every alternating boundary sequence.
2. **Later same-frame Plane A producer overwrite/coalescing — plausible, unproven.** Scroll
   publication occurs at `$051096`; player update then calls `$055AD6`, `$059DE8`, and the retained
   foreground animation producer `$0596F4`. Any later producer that addresses the same physical
   `logical_row&31` can replace staged words before VBlank while leaving one coalesced dirty bit.
   This is a content-order question, not a missing DMA bit.
3. **VBlank workload interaction — secondary, unproven.** Wall jumping can combine sustained
   vertical rows with horizontal Plane A work and sprite work. `dma_publish_frame` is display-on by
   default and publishes palette, tiles, Plane B, Plane A, sprites, then scroll. Source ordering is
   safe for row-before-scroll, but source alone does not prove the heaviest combined frame remains
   inside blanking. Do not elevate this over hypothesis 1 without existing accounting evidence.
4. **Skipped row from a large camera increment — not supported.** The movement path caps the step at
   four and the helper loops all crossed logical rows.
5. **Incorrect offline row asset — not supported.** Deterministic assets and their exhaustive cell
   checks do not explain intermittent dependence on movement cadence.

## Exact code to examine after reset

Original arcade:

- `$051F40..$052008`: wall/jump and ordinary rope accumulator producers.
- `$0517FA..$0518CA`: opposing-axis cancellation, four-unit cap, and movement calls.
- `$053850..$053954`: vertical movement threshold logic; `$0538D6/$053942` write flags and
  `A5+$10DA`.
- `$051090..$0510B8`: frame ordering around `$052732`, `$055650`, `$055AD6`, `$059DE8`, and
  `$0596F4`.
- `$055650..$0557B8`: bit-0/bit-1 ordering, no-publication versus ordinary-publication branches.
- `$0558A2/$0558C6/$0558E0`: group completion, pointer advance, saved selector, record advance.
- `$055948/$055990/$055A14`: ordinary row publication.
- `$0596F4`: later same-frame foreground animation destinations.

Genesis:

- `tilemap_hooks.s:945-1020`: up/down old-to-new top calculations and crossing loops.
- `tilemap_hooks.s:1391-1558`: current/predecessor selection, mixed-ring restoration, staging and
  dirty marking; especially branches at lines 1407, 1414, 1418, 1425-1428, and 1518-1534.
- Other `fg_row_dirty` writers in `tilemap_hooks.s`, especially the `$0596F4` native producer, for
  same-physical-row writes after scroll publication.
- `vdp_comm.s:323-354` and the wrapper `vdp_commit_fg_narrow_strips`: coalescing and clearing of
  dirty rows alongside narrow/column publications.
- `dma.s:71-99`: total publication order and existing V-counter accounting points.

## Smallest recommended next action

Extend the **existing** static Plane A verifier (not a new framework) with a short consecutive-frame
state model around `$0558A2/$0558E0`. Enumerate `A5+$10DA=1..4`, both directions, crossings just
before/after an eight-pixel boundary, and one-frame direction reversals across the record-16/17/18
transitions. For each no-publication call, derive the retained arcade ring generation and compare it
with the exact branch selected at `tilemap_hooks.s:1407-1534`.

If that finds a mismatch, the next implementation should correct only that state selection. If it
does not, inspect the already-existing later-writer and VBlank accounting evidence before requesting
any new trace. Preserve Build 0528 unchanged until one of those source relationships is disproven.

Handoff status: source investigation complete; root cause not yet proven; no STOP condition asserted.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0056`
