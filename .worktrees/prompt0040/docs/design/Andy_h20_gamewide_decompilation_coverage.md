# Andy — H20: Game-Wide 68000 Decompilation Coverage Census

**Agent:** Andy · Static census. **No Genesis impl · no ROM build · runtime counter 377, untouched.**

> **Headline: OVERALL 13.9% of the arcade main-68000 executable code is fully decompiled**
> (byte-weighted), 21.4% touched. 334 Ghidra-identified functions, 40,392 code bytes; 53 COMPLETE,
> 3 PARTIAL, 1 STUB, 277 NOT_DECOMPILED. This is a deliberately conservative, defensible number.

## A. Denominator definition
ALL Ghidra-identified Motorola 68000 functions in `build/regions/maincpu.bin`, from
`analysis/ghidra/rastan_arcade/exports/function_inventory.tsv` (334 functions). Untracked functions
remain in the denominator as NOT_DECOMPILED. This is **68000 executable-code coverage**, not ROM-byte
coverage (data/tables/graphics ROM are excluded).

## B. Ghidra function inventory method
Each function's byte span = `body_max - body_min`. Output per function in
`analysis/decompilation/gamewide_function_inventory.csv` (pc, name, span, status, subsystem, tracked).

## C. Byte-overlap handling
Per-function spans are summed for subsystem/overall byte totals (each function has one primary owner,
so subsystem sums = the span-sum denominator exactly, verified by the guard). The **union** of ranges
(33,274 B, vs 40,392 B span-sum) is also reported: the difference is Ghidra overlaps/thunks. The
displayed % uses the per-function span-sum so each function is weighted once.

## D. Status rules
COMPLETE = the function's **entry PC** is a durable-C COMPLETE routine in `function_coverage.csv`
**with both raw and semantic artifacts** (enforced by the guard). PARTIAL/STUB likewise by entry
match. A tracked routine that is only an *internal* PC of a larger Ghidra function does **not** credit
the whole function (anti-overstatement). PARTIAL receives **no** fractional completion credit.

## E. Subsystem classifier
Tracked functions are owned by their durable-C semantic file's subsystem; untracked functions by a
documented PC-range heuristic (17 buckets incl. UNCLASSIFIED). Full mapping in
`tools/analysis/build_gamewide_coverage.py`.

## F. Overall percentage
Fully decompiled **13.9%** (5,620 / 40,392 B); touched **21.4%** (8,650 / 40,392 B).

## G. Subsystem percentages (fully-decompiled, byte-weighted)
Top by size (see `gamewide_subsystem_coverage.csv`): PC090OJ sprite/compositor and actor
core/lifecycle are the most-covered large subsystems; enemy AI, collision/damage, map/scene,
HUD/score, interrupts/system, and input/attract are largely NOT_DECOMPILED. The single largest
undecompiled subsystem by executable bytes is reported by the summary JSON.

## H. Touched vs fully-decompiled
"Touched" adds PARTIAL+STUB bytes; kept strictly separate from fully-decompiled so partial lifts do
not inflate the headline.

## I. Known limitations
Byte spans are Ghidra body extents (small end-of-function rounding possible); the PC-range classifier
for untracked functions is a heuristic (UNCLASSIFIED is shown, not hidden); the census reflects the
current Ghidra export.

## J. Non-68000 processor coverage
Rastan's audio is a **separate Z80 + YM2151/MSM5205 program ROM** — **NOT included** in this 68000
denominator (measured separately / not yet inventoried). The headline % is main-68000 only.

## K. Validation
`tools/analysis/check_gamewide_decompilation_coverage.py` verifies: all Ghidra functions classified;
no duplicate owner; subsystem bytes = inventory span-sum; status partition = total; percentage
arithmetic; every COMPLETE has durable-C raw+semantic evidence; NOT_DECOMPILED remain visible.
**GAME-WIDE COVERAGE GUARD: PASS.** Outputs: `gamewide_function_inventory.csv`,
`gamewide_subsystem_coverage.csv`, `gamewide_coverage_summary.json`; chart rendered in the living
Bestiary ("Arcade 68000 Decompilation Coverage", data-driven from the summary JSON).
