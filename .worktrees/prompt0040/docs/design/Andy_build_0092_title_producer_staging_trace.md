# Andy — Build 0092 Title Producer→Staging Trace

**Author:** Andy
**Date:** 2026-06-22
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin` (SHA `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. No bookmark cycle. No fix (fix locus only). Bounded P5 runtime spec where static is insufficient.

Address labels (Rule 3): `arcade_pc` / `runtime_genesis_pc` = code addresses (= `arcade_pc + 0x200`, KF-006); `HW` = hardware; `WRAM` = Genesis work RAM. The `build/genesis_postpatch.disasm.txt` and the ROM share mtime `2026-06-20 00:35` and the disasm contains the Build 0092 hook fix (`lea 0xff501a,%fp` at `0x70bd8`); it is the Build 0092 image.

---

## Phase 0 — Baseline statement

**Relevant priors:** KF-028 (input shim / title-text / OPEN-016 Part 2 — STRONG; this task tests the Build 0092 producer→staging path it created), KF-013 (text/producer dispatch inside the VBlank body — STRONG), KF-011 (arcade VBlank owns the lifecycle — STRONG), KF-010 (FG→Plane A — STRONG), KF-004/006 (PC↔offset — CONFIRMED), KF-001 (watchdog counter `%a5@(44)` — context).

**Rediscovery-Hazard HIGH touched:** KF-028, KF-013, KF-011, KF-010 — respected; none contradicted (the prior single-lifecycle audit established that empty staging at `0x70100` is real producer failure, not a sampling artifact — this task extends that).

**Deferred-appendix entries relevant:** none.

**Task classification:** EXTENDING (KF-028 / OPEN-016 producer→staging chain).

**Open/Closed issues touched:** OPEN-016 (active — Part-2 hook is the live thread; Part-1 relocation verified intact), OPEN-001 (active — root narrowed to producer→staging), OPEN-015 (context only).

**Contradiction of CONFIRMED/STRONG finding:** NONE.

**Architecture compliance:** CONFIRMED. The glyph renderer is an arcade-called hook returning via RTS; no Genesis-owned control flow proposed.

---

## Phase 1 — Title sub-state producer path reachability

Master dispatch at `runtime_genesis_pc 0x3A256` reads `%a5@(0)`. Cody's WRAM dump (steady no-input window) shows `WRAM 0xFF0000/0x0002/0x0004 = 0x0000 / 0x0001 / 0x0002`, i.e. `%a5@(0)=0` (title), `%a5@(2)=1`, `%a5@(4)=2`. STATICALLY_PROVEN control flow for that state:
`%a5@(0)=0` → title dispatcher `0x3ABFE` (gated `%a5@(44)==0`) → `%a5@(2)` table `0x3AC20[1]=0x0070` → `0x3AC90` → `%a5@(4)` dispatch:
- `=0` → `0x3AC9E` (setup `bsrw 0x3af4c`/`0x3b05a`; `movew #1,%a5@(4)`)
- `=1` → **`0x3ACAE` (the title glyph producer)**
- `=2` → `0x3AC9C bras 0x3AD00` → `jsr 0x712B4` (`genesistan_palette_hook_03ab00`) → `rts`

So the glyph producer `0x3ACAE` runs only at `%a5@(4)==1` (a one-shot transition); the steady `%a5@(4)==2` handler is `0x712B4`, which is **palette-only** (writes `WRAM 0xff603c`, sets `palette_dirty 0xff4000`; STATICALLY_PROVEN) and does **not** touch the tilemap staging buffers.

**Reachability caveat (EXPECTED_BUT_RUNTIME_DEPENDENT):** `%a5@(4)=2` is written by **five** distinct sites (`0x3a406`, `0x3a96a`, `0x3a9e6`, `0x3aa58`, `0x3acf8`). Only `0x3acf8` is the tail of `0x3ACAE`. The steady `(0,1,2)` state is *consistent* with the `0x3ACAE` path but does **not statically prove** `0x3ACAE` executed its render block this run — that is runtime sub-state history.

---

## Phase 2 — Producer inventory and execution

`0x3ACAE` (the title FG text producer), if executed, runs unconditionally (no skip branches):
```
3acae: jsr 0x5a5de
3acb4: moveq #17,%d0 ; 3acb6: bsrw 0x3bd48   <-- first glyph-render call
3acba: moveq #63 ... 64,65,66,67,68,69,70 → bsrw 0x3bd48 (each)
3acea: movew #0x2749,0xc09172   <-- direct one-shot writer (OUT OF SCOPE / deferred)
3acf2: movew #160,%a5@(44)      <-- kicks the watchdog counter
3acf8: movew #2,%a5@(4)         <-- advances to steady
3acfe: rts
```
The **first expected nonzero staging write** comes from the `d0=17` render at `0x3ACB6 bsrw 0x3bd48`. `0x3BD48` is the opcode-replaced renderer: `0x3BD48: jsr 0x70B8E` (`genesistan_hook_glyph_renderer_3bd48`) `; rts; nop…` — STATICALLY_PROVEN dispatch to the hook (this is the same path whose helper crashed in Build 0091, confirming reachability). The BG logo/artwork is produced by a separate path (not `0x3BD48`); Cody found `staged_bg_buffer` empty too, but this trace follows the FG glyph chain (the first-expected staging write).

---

## Phase 3 — Staging write precondition (Build 0092 hook)

`genesistan_hook_glyph_renderer_3bd48` per-cell store `.Lgr_store_cell` (`runtime_genesis_pc 0x70BC8`, `tilemap_hooks.s:1078`) **now establishes the helper preconditions** (Build 0091 triage fix, present in Build 0092):
```
70bc8: moveml save
70bcc: lea 0xf1f2c,%a3   ; genesistan_pc080sn_tile_vram_lut
70bd2: lea 0xf9f2c,%a5   ; genesistan_pc080sn_attr_lut
70bd8: lea 0xff501a,%fp  ; %a6 = staged_fg_buffer   <-- the Build 0091 fix
70bde: a2=a1+2; bsrw 0x707bc (shared FG store)
```
Matches the known-good `genesistan_hook_text_writer_3c550/3c586` precondition. **STATICALLY_PROVEN: when `.Lgr_store_cell` runs, it writes `staged_fg_buffer`** (no crash, correct base regs). "No crash" here additionally *is* "writes staging," because the precondition is satisfied.

---

## Phase 4 — Hook acceptance / routing

The shared store's FG-range gate (`runtime_genesis_pc 0x707E4`): `d0 = a2 & 0xFFFFFF`; reject if `< 0xC08000` or `>= 0xC0C000`. For `d0=65`, descriptor dest `a1=0x00C0914C`, `a2=0xC0914E` → inside `[0xC08000, 0xC0C000)` → **ACCEPTED**, proceeds to offset compute + `staged_fg_buffer` write. STATICALLY_PROVEN. (`cwindow_clear` at `0x710D6`, which *would* zero both staging buffers, is called only from `0x563B6` — the post-title game/sprite loop — not the steady title handler.)

---

## Phase 5 — Offset correctness

For an accepted dest, `0x70800` computes `(a2 - 0xC08000) >> 2` → cell index → row/col → `staged_fg_buffer + (row*128 + col*2)` written at `0x70794` (`move.w %d1,(%a6+%d2.w)`, `%a6=staged_fg_buffer`). For `a2=0xC0914E`: offset `0x114E>>2`-derived row/col lands well inside the 2048-word buffer. STATICALLY_PROVEN in-bounds.

---

## Phase 6 — Descriptor / table integrity (OPEN-016 Part 1)

Verified intact in Build 0092:
- `table[65] @ 0x3BE80 = 0x0003C446` (Part-1 `+0x200` relocation present); `table[17]@0x3BDC0=0x0003C00C`, `table[63]@0x3BE78=0x0003C416`. STATICALLY_PROVEN.
- Descriptor at `0x3C446`: `00 C0 91 4C | 00 00 | 4F 54 48 45 52 57…` = dest `0x00C0914C`, attr `0x0000`, glyph bytes `"OTHERW…"` — **non-empty**. STATICALLY_PROVEN.

So the consumed descriptors are valid and non-empty; the renderer would emit cells.

---

## Phase 7 — Classification: **P5 — static evidence insufficient**

**Every static link in the FG title producer→staging chain is verified correct:** producer `0x3ACAE` render block is unconditional and dispatches `0x3BD48 → 0x70B8E`; the hook precondition (`%a6=staged_fg_buffer`, `%a3`/`%a5` LUTs) is established (Phase 3); the descriptor table relocation is intact and descriptors non-empty (Phase 6); dests are accepted by the FG-range gate (Phase 4) and land in-bounds (Phase 5); and **nothing clears the tilemap staging in the steady title state** (steady handler `0x712B4` is palette-only; `cwindow_clear` is not reached). Therefore, *if* `0x3ACAE` executed its renders, `staged_fg_buffer` would be non-empty **and persist** (commits clear only dirty flags, never the staged buffers — prior audit), so a steady-state read would be non-empty.

It is empty. The contradiction cannot be resolved statically because it turns on **runtime execution history**: (a) whether the one-shot `0x3ACAE` render block actually executed at title entry (the steady `(0,1,2)` state does not prove it — `%a5@(4)=2` has five writers, Phase 1 caveat), and (b) Cody sampled **only** at the steady window (~frame 600), far after the one-shot entry, so the trace cannot observe the producer at the moment it runs. No static defect in the producer→staging path explains the emptiness; the failure is upstream in *whether/when the producer runs*, which is unobserved.

**Decisive answer to "what call should place the first nonzero staging word, and why did it not?":** the `d0=17` render at `0x3ACB6 → 0x3BD48 → 0x70B8E → … → 0x70794` (FG store) should write the first nonzero word into `staged_fg_buffer`. Statically it would. Why it doesn't appear cannot be determined without observing the producer at title entry — hence P5.

**P5 — exact bounded runtime measurement for Cody** (single MAME task, decides P1/P2/P3/P4; no broadening):
1. From reset through the title-entry transition into steady state (sample frames ~0-120, not only 600):
   - Breakpoint `runtime_genesis_pc 0x3ACAE` and `0x3ACB6` — count executions; at each hit log frame# and `%a5@(0)/%a5@(2)/%a5@(4)` (`WRAM 0xFF0000/0002/0004`).
   - Breakpoint `runtime_genesis_pc 0x70794` (the FG staging store) — count executions per frame and log `%a6` (`should = 0x00FF501A`), `%d2` (offset), `%d1` (cell value).
   - Write-watchpoint on `WRAM 0x00FF501A..0x00FF601A` (FG staging) and `0x00FF401A..0x00FF501A` (BG staging): log `(frame#, writing PC, offset, value)`.
2. Decision:
   - `0x3ACAE`/`0x3ACB6` **never execute** in the title window → **P1** (producer path not reached; investigate why `(0,1,2)` is entered without the render handler — which `%a5@(4)=2` writer fired).
   - `0x3ACAE` executes but `0x70794` **never executes** (or watchpoint sees no FG writes) → **P2/P3** (render emits nothing / store rejected); the range-gate log at `0x707E4` and the descriptor bytes distinguish them.
   - `0x70794` writes `staged_fg_buffer` at entry, then a **later** write fills it with the clear-cell (0x0000) → report that clearing PC (the fix locus is that clear, not the producer).
   - `0x70794` writes and the FG watchpoint shows persistence to the steady window → re-examine Cody's frame-600 read (address/timing).

**Fix locus (pending the measurement):** the title FG producer execution at title entry (the `0x3ABFE → 0x3AC90 → 0x3ACAE` path and which `%a5@(4)=2` writer actually fires), NOT the glyph hook (verified correct) and NOT the commit/clear placement (settled Classification C). Do not pre-blame the hook.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-016 (active — Part-1 relocation verified intact, Part-2 hook precondition verified correct; the live gap is producer execution at entry; not closed), OPEN-001 (active — narrowed; not closed), OPEN-015 (context only).
- New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: Start→C→A crash, OPEN-015 crash-handler fix, the `0x3ACEA` direct one-shot writer (`movew #0x2749,0xC09172`, out of scope), BG logo/artwork producer path, broader unhooked-writer survey.

## KNOWN_FINDINGS impact

**Option A — No new finding to index.** Rationale: this trace verifies existing structure (KF-028/OPEN-016 producer→staging chain) and lands at P5; no durable new system-behavior fact is established until the bounded runtime measurement resolves P1/P2/P3/P4.

## STOP triggered

NO.
