# Andy — Post-0359 SAT Emit-Tail Analysis (next target for Build 0360)

**Analysis only. No production change, no ROM, counter 359.** Evidence:
`Cody_build0359_bbox_finalizer_performance.md`; `apps/rastan-direct/src/pc090oj_hooks.s`
(`.Lnq_emit_entry_cached` 1736+, `.Lnq_hit` 1975+, `.Lnq_done_scan` 2031+).

## 1. SAT emit-tail dissection (`.Lnq_hit`, per emitted entry ≈ 0.963 line)

Rough static apportionment of the ~58-instruction tail (0.963 line ≈ 470 dots):

| Component | Code | ~cost | Class |
|---|---|---:|---|
| `pc090oj_cell_used` bset (referenced-slot bitmap) | 1975–1983 | ~0.15 | **C-ish** — pure bookkeeping, but the miss/victim path needs it → keep |
| Y SAT word (mask + `SAT_Y_BIAS` + wrap) | 1984–1990 | ~0.12 | A/B mandatory |
| size+link word (`d5+1`, `ori #0x0500`) | 1991–1995 | ~0.10 | A mandatory (fixed 16×16 size, sequential link) |
| flip+priority compose (`ori #0x8000`, v/h flip) | 1996–2003 | ~0.12 | B mandatory (priority const, dynamic flip) |
| palette compose (`d1&0x0F` \| `(sprite_ctrl&0xE0)>>1` → `current_sprite_palette_map`) | 2004–2013 | ~0.22 | mostly B; **the `pc090oj_sprite_ctrl_shadow` read + `&0xE0/>>1` (~4 instr) is frame-hoistable (D)** |
| attr word merge + pattern (`slot*2 + SPRITE_TILE_BASE`) | 2014–2022 | ~0.16 | A mandatory (tile index) |
| X SAT word (mask + `SAT_X_BIAS` + wrap) | 2023–2028 | ~0.10 | A/B mandatory |
| `d5++`, stack shuffles, misc | — | ~0.06 | B |

**Verdict: the 0.963 line is mostly four mandatory SAT-word stores plus their required dynamic
bias/wrap/flip/palette — not software wrapped around trivial writes.** The only clearly removable
piece is the per-entry palette-bank read (`pc090oj_sprite_ctrl_shadow` is display-latch state, set by
the arcade *after* its producers, so it is constant across one gameplay-finalizer call — exactly the
condition 0359 used to hoist `pc090oj_ctrl_shadow`). Folding the frame-constant bank into a
per-frame-selected palette-map pointer removes ~0.07 line/entry. **Total realistically removable from
the tail: ≈0.07–0.10 line/entry ≈ 2–3 global lines at 26 entries. Small.**

## 2. Why back/enemy reaches 90–260 lines despite a 2.336-line normal hit

Two separate effects, and the second is the one that matters for the cave:

1. **Linear part (explained):** finalizer scales at a fitted **3.018 lines/emitted entry** (r=0.917),
   *above* the 2.336-line normal hit. The ~0.68 line/entry gap is work that correlates with emitted
   count but is **not** an emitted SAT entry: `.Lnq_emit_entry` is *called* for every queued piece,
   and clipped/off-screen pieces still pay pre-bbox + bbox + reverse-lookup (~1.37 lines) and produce
   nothing. So **calls ≫ emitted entries**, and each non-emitting call is ~1.37 wasted lines.
2. **Super-linear worst-frame excess (the black bars):** the worst Build 0359 frame (797) shows
   **259.8 back/enemy lines with only 41 emitted** → 41×3.018 ≈ 124 expected, leaving **~136 excess
   lines the linear model does not explain.** That excess is *not* emitted-SAT cost. It is some
   combination of a burst of **clipped/rejected calls**, **residency misses** (each still runs the
   untouched `.Lnq_vloop` linear ≤49 victim scan), and any expensive special cases. Current
   instrumentation reports emitted count and lane medians but **not** call count, clip-rejects, or
   per-frame miss count — so the exact split of that 136-line excess is **not provable from existing
   evidence.** ".Lnq_emit_entry calls" ≠ "emitted SAT entries", and the gap is where the cave time hides.

## 3. Common gameplay fast path — **NOT VIABLE (as a finalizer win)**

The emitted-hit path is *already* the common case, and §1 shows it is mostly mandatory SAT stores; a
specialized 16×16/ordinary-palette/no-HUD-tag fast path would skip only a couple of cheap branches
(~0.05 line). The real waste is in **non-emitting calls** (clipped/miss), which a hit fast path does
not touch. So a finalizer fast path is not worth it. The productive "fast path" would be **earlier,
coarser rejection of off-screen pieces/actors** so they never reach the full per-entry path — but that
lives at enqueue / stage-dispatch, and its payoff cannot be sized without the §2 measurement.

## 4. Largest remaining removable cost
Not the SAT tail (~0.07 line/entry). The largest lever is the **non-emitting `.Lnq_emit_entry` call
overhead in the back/enemy lane** — clipped pieces + miss victim-scans that dominate the worst (cave)
frames' ~136-line excess. Its exact size is **unmeasured**.

## 5. Pre-bbox block (0.535 line) — secondary
Code extract + `andi #0x1FFF` + range test + blank-bitset byte read/`btst` + HUD-tag `btst` + Y/X
coarse wrap. All small and mostly mandatory. The blank-code bitset test (~0.08 line) is the only
plausibly-foldable item for the gameplay lane, and it guards correctness. Not a material target.

## 6. Finalizer vs stage dispatch
The SAT tail and pre-bbox are near-irreducible (~2–5 global lines combined). **Stage dispatch (44
global / 82 heavy, untouched since 0356) is now the larger *reducible* block** than anything left in
the emitted-hit path. But the single biggest heavy/cave cost is still the finalizer's **non-emitting
call overhead** (§2), if it is as large as the worst-frame excess suggests. So the honest order is:
**measure §2 first**; if clipped/miss calls dominate the cave frames, attack that (highest cave
payoff); if not, the finalizer is done and Cody should move to **stage dispatch**.

## 7. Cave benchmark relevance
The stated failure case (first cave, Segment 1, no-kill, enemies alive) is precisely a **worst-frame /
super-linear** scenario — many alive enemies → many queued pieces, many partially/entirely off-screen
→ many non-emitting calls, plus more misses. The global median (which the SAT tail barely moves) is
**not** the right target; the §2 excess is. This is why chasing the 0.963-line tail would not shrink
the ~9–21 px cave bands, and the call/clip/miss characterization would.

---

## Required final response

1. **SAT tail breakdown:** ~0.15 cell_used bookkeeping (keep, miss path needs it); ~0.60 four SAT
   words + mandatory bias/wrap/flip/pattern (A/B, mandatory); ~0.22 palette compose of which ~0.07 is
   the frame-hoistable `sprite_ctrl_shadow` bank read (D, removable); ~0.06 misc. **Mostly mandatory;
   ≈0.07–0.10 line/entry removable.**
2. **Why 90–260 despite 2.336/hit:** calls ≫ emitted entries — clipped/off-screen pieces and
   residency misses each pay ~1.37 lines (or a ≤49 victim scan) and emit nothing; the worst cave frame
   has ~136 lines of excess beyond the emitted-count linear fit, from those non-emitting calls.
3. **Common gameplay fast path:** **NOT VIABLE** as a finalizer optimization (emitted-hit path is
   already common and mostly mandatory stores). Evidence: §1 apportionment + §2 excess is in
   non-emitting calls, which a hit fast path does not reduce.
4. **Largest remaining removable cost:** the back/enemy lane's **non-emitting call overhead**
   (clipped pieces + miss victim-scans), dominant in cave/worst frames; exact size **unmeasured**.
5. **Recommendation for Build 0360:** do **not** micro-optimize the SAT tail. **First take the §9
   measurement on the cave route**; if non-emitting calls dominate (expected), implement a **coarse
   off-screen actor/piece reject before the full per-entry path** (cheap whole-actor AABB at
   enqueue/lane-load), generic path as fallback — this directly attacks the cave excess. The one
   trivially-safe micro-win to bundle: fold the frame-constant palette bank into a per-frame palette
   pointer (removes the per-entry `sprite_ctrl_shadow` read).
6. **Expected global saving:** small — ~2–5 lines (palette-bank hoist + whatever coarse reject removes
   from median). The global median is not where the win is.
7. **Expected heavy/cave saving:** potentially large but **unproven** — up to the ~136-line worst-frame
   excess is theoretically in play if non-emitting calls dominate; realistic target tens of lines on
   the worst cave frames. This is the number that must be measured before committing.
8. **Stage dispatch should be:** **AFTER 0360** — it is the larger *reducible* block once the finalizer
   hit path is exhausted, but the cave black bars most likely live in the finalizer's non-emitting-call
   excess, which 0360 should address first. Reassess after the §9 measurement; if the excess is *not*
   in the finalizer, stage dispatch becomes NEXT immediately.
9. **Additional measurement required before Cody implements: YES.** Minimum: per-frame counters on the
   **first-cave no-kill route** of (a) `.Lnq_emit_entry` calls, (b) emitted entries (`d5`), (c)
   clip-rejects (`.Lnq_entry_skip` after a viewport test), (d) residency misses / `.Lnq_vloop`
   iterations, (e) queue-full drops — correlated with the worst back/enemy frames. This alone decides
   whether 0360 targets the reject/miss path or pivots to stage dispatch. Nothing broader is needed.
