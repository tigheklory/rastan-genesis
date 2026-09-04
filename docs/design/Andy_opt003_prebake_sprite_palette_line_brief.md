# OPT-003 Brief — Prebake Per-Piece Sprite Palette Line (+ session findings)

**Author:** Andy · **Date:** 2026-09-02 · **Status:** proposal / ready-to-implement brief
**Purpose:** hand-off document for ChatGPT to author the next implementation prompt for Andy. Self-contained.
**Related:** [OPTIMIZATIONS.md](../../OPTIMIZATIONS.md) (OPT-003, OPT-004), CLAUDE.md palette + pipeline mandates.

---

## 1. Where we are (session summary)

### 1a. The lower-screen coloured pixels = CRAM writes during active display (CONFIRMED)
The "individual coloured pixels" in the lower-right of the frontend, and the dots over the gameplay
dirt welded to the top edge of the `_d` diagnostic green band, were investigated in **GENESIS NTSC via
Exodus** and identified by elimination + register read:

- **Not the Window plane.** VDP **reg $11 (17) = $00** and **reg $12 (18) = $00** → window has zero area
  on screen; nothing in our code re-enables it. Ruled out.
- **Not the CREDIT display.** CREDIT is **Layer B** (visible parked in the Plane-B viewer), not a sprite.
- **Not sprites.** Exodus draws no SAT bounding-box outline around the dots.
- **It is CRAM being written while the beam is in active display.** The VDP paints the *colour being
  written* as a dot at the beam position. The culprits are the Build-0336 unconditional **64-word
  68k→CRAM palette DMA** (`vdp_comm.s:177-183`, multicolour) and the `_d` bar's backdrop (CRAM 0)
  writes, executing before the beam has left active display. Visible in the Port Monitor as **code `03`
  (CRAM write)** rows whose **VCounter < $E0**. This is the same root as the vertical noise band.

**Consequence:** the dots/noise are a *symptom of the servicing overrunning vblank*. A V-counter gate on
the CRAM commit is only a belt-and-suspenders guard — while the frame still overruns, gating trades dots
for *dropped palette updates*. The real cure is to **shrink the frame** so essential VDP/CRAM work fits
inside blanking. That is the optimization program.

### 1b. Decisions taken this session
- **Drop the `_s` score-metric build.** Its only job (is it overrunning, by how much) is already answered
  visually by the `_d` bar. `_s` has cost two failed passes; the honest measurement investment is the
  scripted headless meter (OPT-007 pending), not more HUD-injection debugging. The `_d` bar is the
  before/after gauge for each cut.
- **Defer the palette-tool expansion** (authoring-side; does not serve the stated top priority = speed).
- **Proceed with optimizations, OPT-003 first** — the fattest *recurring* per-frame win, pure Bake+
  Optimize, and it directly shrinks the vblank frame.

### 1c. The three levers (framing for the whole program)
Every optimization is one of: **Schedule** (move essential/VDP code inside vblank), **Optimize** (fewer
cycles so it fits), **Bake** (precompute offline in the Python build step so runtime does an indexed load,
not a calculation). OPT-003 is Bake + Optimize.

---

## 2. OPT-003 target — current runtime implementation

Every emitted sprite piece's Genesis palette **line (0..3)** is computed **at runtime**, per piece, at
SAT commit time.

- **Caller:** `.Lnative_pal_fixup` (`pc090oj_hooks.s:1950`) loops over up to **80** emitted entries
  (`pc090oj_emitted_count`), calling `.Lnative_palsel` for each (unless a forced line is set).
- **`.Lnative_palsel`** (`pc090oj_hooks.s:1208`):
  - `d1` = piece bank nibble; `d7` = display-latched colbank = `(pc090oj_sprite_ctrl_shadow & $00E0) >> 1`.
  - `effective_bank = (d1 & $0F) | d7`.
  - Special case: `effective_bank == $30` → **Line 2** (death burst / effects), hardcoded.
  - Otherwise → `palette_route_lookup(scene_id, PROUTE_OWNER_PC090OJ, effective_bank)`.
  - Miss fallback: `line = (effective_bank >> 4) & 3`.
- **`palette_route_lookup`** (`palette_hooks.s:82`): **linear scan** of `palette_route_table`
  (`palette_hooks.s:49`), rows of 5 words (10 bytes), matching `(scene, owner, bank)`. ~10 rows today.

**Cost:** a linear table scan (up to ~10 rows × 3 word-compares) **per piece**, for ~28 pieces/frame
average (up to 72), every frame — one of the busiest per-frame loops. Pure overhead: the result is a
deterministic function of `(scene_id, effective_bank)`.

---

## 3. Proposed bake (behaviour-preserving)

**Recommended (safe first cut): a build-time flattened `(scene_id, effective_bank) → line` lookup.**
- Generate, in the Python build step, a small direct-index LUT that reproduces **exactly** what
  `.Lnative_palsel` + `palette_route_lookup` return today — including the `$30 → Line 2` special case and
  the `(effective_bank >> 4) & 3` miss-fallback — for every `(scene, effective_bank)` the runtime can ask.
- Runtime `.Lnative_palsel` becomes: bounds/scene index → **one indexed byte load** from the baked LUT.
  No compares loop, no per-piece scan. `palette_route_lookup`'s per-piece call disappears from the hot
  path (it may remain for any non-hot consumer, or be retired if it has none).
- Source of truth for the bake = the **existing authored `palette_route_table`** (plus the two hardcoded
  rules), so the generated LUT is a *derived artifact*, not a new registry.

**Deeper win (later, with the `(code,bank)` sprite architecture):** fold the line into the reindexed
sprite descriptor data (`code → line`), eliminating even the effective_bank compute. Only valid where the
line is invariant w.r.t. runtime colbank; not required for this first cut.

**Python home:** the offline reindexer is `tools/translation/reindex_graphics_for_palette.py` (currently
ANALYSIS-ONLY, not wired to production). The LUT generator can extend it or be a sibling generator; either
way it must be a **project-owned, reusable** build stage that emits a generated `.inc`/`.bin` consumed by
the assembler — not a hand-authored table and not a `/tmp` script.

---

## 4. Guardrails the prompt MUST encode (non-negotiable)

1. **STRICTLY BEHAVIOUR-PRESERVING.** The baked line for every `(scene, effective_bank)` must be
   **byte-identical** to what the current runtime computes. OPT-003 is a performance refactor only.
2. **Do NOT reconcile the JSON-vs-ASM discrepancy.** `specs/palette_decisions.json` records e.g. bank
   `0x33 → line 3`, `0x36 → line 0`; the live `palette_route_table` maps `0x33 → Line 0`, `0x36 → Line 1`.
   That divergence is **out of scope** and must not be "fixed" as a side effect. Bake the ASM route
   table's *current* behaviour. If the registry should change, that is a separate palette-decision task.
3. **Palette registry authority.** `specs/palette_decisions.json` is the only palette-decision registry;
   the generated LUT is a derived output and must not become a second registry (CLAUDE.md).
4. **No NOP/RTS/dead-write "fixes"** without explicit prior approval and scaffolding disclosure. Removing
   the per-piece scan by replacing it with a real indexed lookup is fine; stubbing is not.
5. **Canonical pipeline + size.** If any replacement changes byte length, use the established shift-table
   reflow path (`shift_replacements`) — "won't fit" is not a blocker. Go through the Makefile-owned
   production flow; never hand-edit generated maps/manifests.
6. **Audit trail.** Design note in `docs/design/` + AGENTS_LOG entry with scaffolding inventory/removal
   plan (project rule).
7. **Build numbering + triple-build.** Sequential auto-named numbered build; every `make` still emits
   `_NNNN.bin` / `_NNNN_d.bin` / `_NNNN_s.bin` (the `_s` build stays produced even though we've stopped
   debugging its display — do not remove the convention without asking).
8. **Target = GENESIS NTSC (`genesis`)**, not PAL `megadriv`.

---

## 5. Acceptance / validation

- **Equivalence:** prove the baked LUT reproduces the current selection for all reachable
  `(scene, effective_bank)` — offline diff against `palette_route_table` + the two hardcoded rules, and a
  runtime/visual check that sprite palettes are unchanged on the R1/P1 gameplay scene and frontend.
- **Perf:** the `_d` diagnostic green band should shrink (less per-frame servicing). Record the estimated/
  measured cycles/frame saved in the OPTIMIZATIONS.md **cumulative savings tracker** and move OPT-003 to
  the implementation log with Build number + ROM SHA.
- **No visual regression** on the confirmed-good scenes (title, attract throne, ROUND/READY, gameplay
  water + dirt) in GENESIS NTSC.

---

## 6. Open question for Tighe (optional, not blocking)
Whether to *also* stage the build-flagged CRAM V-counter guard (OPT-004(b)) in the same task so we can
watch the dots vanish once the frame is smaller — or keep OPT-003 pure and do the CRAM timing as its own
step. Default: keep OPT-003 pure.
