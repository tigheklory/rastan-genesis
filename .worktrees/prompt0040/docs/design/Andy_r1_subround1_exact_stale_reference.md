# Andy — Pin Exact R1 Subround-1 Early-End Stale Reference (follow-up)

**Date:** 2026-10-19 · **Type:** READ-ONLY follow-up to
`Andy_build0442_0446_subround1_early_end_regression.md`. **No** production source/ROM/MAME/trace/
build-number change. Phase D/E not started. Output: this doc + AGENTS_LOG + refine OPEN-037. Evidence:
git history, preserved ROMs, remap spec, disassembly — no new runtime evidence. Cody's in-flight work
untouched; working tree not switched.

## CORRECTION (2026-10-19, after Tighe's hardware report)

Tighe played **0442, 0444, 0445, 0446 on real Genesis hardware**. That is authoritative dynamic
ground truth and **outranks every static inference in this document**. Two earlier claims that
contradicted it are **RETRACTED**:

1. ~~"0444/0445 crash before/at gameplay entry; 0446 is the first build to reach gameplay."~~ **FALSE.**
   Tighe reached and played gameplay on 0444 and 0445. The glyph literal issue did **not** prevent
   those builds from running gameplay on hardware; my "crash" conclusion was a static over-inference.
2. ~~"0445→0446 gameplay is byte-identical so the subround-1 endpoint cannot move between them."~~
   **RETRACTED as an authority claim.** Tighe observed the endpoint at **different positions** across
   these builds (e.g. the earlier 0445 "Seg11" / 0446 "Seg13" observations). If a 3-byte diff in my
   artifact comparison implies "cannot move" while hardware shows it moving, then **my premise is
   wrong** — most likely the build-number↔artifact mapping I diffed, the region I treated as
   "gameplay," or the diff itself — not his observation.

What survives this correction (pure ROM facts, not in conflict with hardware): the Build-0200
arc-table embedded pointers **do** relocate −30 between the 0442 and 0446 artifacts I diffed. That rules
those pointers out as the stale site, but it does **not** license any claim about which builds ran.

The rest of this document below is kept for the reasoning trail but is **subordinate to the hardware
observations above** wherever they conflict.

## EXACT ROOT SITE PINNED: **NO** — and the previous "gameplay stale reference" hypothesis is **REFUTED**.

This deeper pass set out to name the exact stale gameplay reference. Instead it **ruled out** the
suspected classes with direct byte proof: **the gameplay region is correctly reflowed by the
pipeline.** The only proven reflow stale reference remains the **frontend glyph helper literal**
(`0x03BD7C`, a Genesis-only helper source literal), which crashed 0444/0445 and was fixed in 0446 —
it is not in the gameplay path. The R1-Subround-1 early-end is therefore **not** explained by a
gameplay reflow stale reference on current static evidence.

## What was checked and ruled out (0442 `c7ca1439` vs 0446 `f9686893`)

1. **Arcade-copy embedded pointers (player jump/fall arc tables, the strongest suspect) — RELOCATED,
   NOT stale.** The 23 Build-0200 arc-table pointers resolve, in the actual ROMs:
   - 0442: `0x5B54C, 0x5B57E, 0x5B5A6, 0x5B5D8, 0x5B622, 0x5B664, …`
   - 0446: `0x5B52E, 0x5B560, 0x5B588, 0x5B5BA, 0x5B604, 0x5B646, …`
   Each 0446 target = its 0442 target **−30 bytes** = exactly the gameplay reflow delta. The
   postpatcher **recomputes** the embedded pointer through the current shift table (the spec's
   `replacement_bytes` `…0005B7EC…` is Build-0200 *documentation* of the value, not what is written
   verbatim — the verbatim `2B7C0005B7EC` is absent from both ROMs). **These track reflow correctly.**
   The same applies to the 24th entry (Build 0305 `0x0503CE → 0x51171`) and the declared embedded
   tables (enemy `0x550A8`, script `0x052C1C`/`0x5976E`).
2. **Genesis-only gameplay helper literals — NONE.** The 0442→0446 `tilemap_hooks.s` diff changed only
   the glyph renderer (the fixed frontend instance). The current and historical gameplay helpers carry
   **no** hardcoded arcade-ROM literal (grep clean), so there is no gameplay analog of the glyph bug.
3. **Postpatcher relocation logic — UNCHANGED.** `postpatch_startup_rom.py`/`verify_canonical_rom.py`
   changed only two **constants** (opcode count 232→231; coverage `0x292EB8 → 0x295EB8` for the three
   4 KiB title maps). No relocation-pass logic change → gameplay references are relocated by the same
   pipeline as 0442.
4. **`pc090oj_hooks.s` (43-line change) — TITLE-ONLY.** It converts the title sprite path to
   change-driven (`genesistan_title_sat_needs_update`, `native_title_sat.inc`); it does **not** touch
   `.Lnq_gameplay`, `.Lnq_emit_lane`, or the shared sprite finalizer.
5. **Attract→gameplay dispatch idiom — PC-relative (self-tracking).** The state dispatches at
   `0x3A052/0x3A16C/…/0x3AA10` use `lea %pc@(adjacent_table); jmp (a0)` — the table is adjacent and
   PC-relative, so it moves with the code across shifts. The one **absolute** sub-table (`0x03AA20`,
   3 entries) **was** declared in `jump_table_word_displacements` for the +2 title cut.

**Conclusion:** the native-title reflow is handled correctly across the gameplay region. The previous
audit proved the reflow *class* via the frontend glyph but over-generalized it to gameplay; this pass
shows the gameplay path does not share that defect.

## Arcade progression owner (re-verified, unchanged)

End-condition / auto-walk / Subround-2 transition are retained arcade progression driven by the record
index `A5+0x013E`, the Plane-B descriptor table at arcade **`0x3951C`** (which is **before** the
`0x03AA54` cut and therefore **unshifted** — references to it stay correct), the streaming walker
`A5+0x10FC`, and scroll column `A5+0x10F6`. Because the descriptor table and its map data are all below
`0x3AA54` (unshifted) and the gameplay code that reads them is correctly reflowed, the progression's
inputs are not corrupted by the title reflow.

## Smallest remaining candidate set (what still could cause it, with distinguishing evidence)

Since the reflow is handled, the early-end is one of:

- **C1 — An UNDECLARED absolute dispatch table / embedded pointer in the attract→gameplay path that
  crosses the `0x03AA54`/`0x03BB48` cuts.** The pipeline relocates *declared* tables (`0x03AA20`) and
  supported operands; an undeclared absolute table reaching the subround/progression handlers would
  mis-reflow silently (the exact reason `0x03AA20` needed a declaration). **Distinguishing evidence:**
  enumerate every absolute (non-PC-relative) jump/dispatch table and embedded code/data pointer in
  `0x3A000–0x3C000` and in the subround progression path, and verify each is either PC-relative,
  pipeline-relocated, or declared. Any undeclared absolute table whose entries cross a cut is the site.
- **C2 — The endpoint moves across builds that all reach gameplay on hardware.** Per Tighe's hardware
  play, 0442/0444/0445/0446 all run gameplay, and the subround-1 endpoint sits at **different**
  positions across them. This is the key fact to explain. Because the arc pointers relocate correctly,
  whatever reference is wrong is one my 0442-vs-0446 artifact diff did not capture — which points at
  either (a) my build-number↔artifact mapping being off (I may have diffed the wrong pair of files for
  the builds Tighe actually played), or (b) a reference in a region I did not treat as "gameplay."
  **Distinguishing evidence:** Tighe's per-build endpoint observations (below) anchored to the exact
  artifacts he ran, then a disassembly of the endpoint routine's inputs on *those* artifacts.
- **C3 — A non-reflow 0442→0446 change** (the only remaining production edits are the title sprite
  change-driven conversion and the Makefile wiring). **Distinguishing evidence:** none of the five
  changed files touches gameplay progression/collision/camera, so C3 is low-probability but recorded.

**Missing evidence to decide:** a **0442-vs-0446 disassembly dataflow trace of the actual
end-of-subround / camera-extent / auto-walk routine** (locate it from the retained scroll/stream
owner, follow every input), checking specifically for (a) any input that resolves to different bytes
between the two ROMs, and (b) any undeclared absolute dispatch table/pointer along that path crossing
the cuts. This is the one decisive step; it requires disassembling the gameplay progression code in
both preserved ROMs (bounded, static — not performed here to avoid over-scoping past "pin or STOP").

## Reflow cross-check (supporting)

| Build | gameplay-region reflow δ vs 0442 | arc pointers | verdict |
|---|---|---|---|
| 0446 | −30 | relocated −30 (track) | reflow handled |
| 0447 | −28 | (expected relocated −28) | reflow handled |

The arc pointers moving **exactly** with δ confirm the pipeline tracks reflow. If a stale reference
existed, it would **not** track δ; the arc tables prove the opposite. This is why the "stale pointer"
explanation of the moving endpoint does **not** hold for the gameplay path as originally framed.

## Failure class

**Not yet determined** (the proven reflow class applies to the frontend glyph only). The gameplay
early-end is **C1 (undeclared cross-cut dispatch/pointer)** or **C2 (pre-existing, surfaced at 0446)** —
neither proven. It is **not** class A/B/D for the gameplay path (arcade-copy pointers relocate; no
helper literal; postpatcher unchanged).

## Current Build 0455 correlation

- The gameplay reflow continues to be pipeline-handled (arc pointers relocate per build), so the
  defect is **not** a persistent gameplay stale pointer in 0455.
- **Defect status: UNKNOWN / UNRESOLVED** — the exact owner is not identified; whether it is C1 or C2
  is undecided. OPEN-037 is refined accordingly (it should **not** be left asserting a proven gameplay
  reflow stale reference).

## Future Cody fix

**Cannot specify a durable fix yet** because the exact site is not pinned. The next bounded step is the
decisive disassembly trace above (C1-vs-C2). If C1, the fix is to **declare the missing absolute
dispatch table/pointer** (`jump_table_word_displacements` / `absolute_long_pointer_tables`) so the
pipeline relocates it — durable across future ROM growth, no numeric hardcode. If C2, this is a
separate pre-existing progression/extent issue, not a native-title regression, and should be handled on
its own evidence. **No** segment-count/camera/auto-walk/scroll special-casing under any branch.

## Verification (once the site is pinned)

Static final-ROM proof that the reference resolves to the correct `address_map.json` target; 0442
semantic equivalence of the subround-end input; normal gates (canonical/boot/gameplay-entry/native-
title verifier); Tighe hardware acceptance: full R1 Subround-1 → true endpoint → auto-walk → Subround 2.

## OPEN/CLOSED issues impact

- **Issue updated:** OPEN-037 refined — the gameplay reflow stale-reference hypothesis is **refuted**
  (arc pointers relocate −30; no gameplay helper literal; postpatcher unchanged; title-sprite change is
  title-only); exact cause unresolved; candidate set narrowed to C1 (undeclared cross-cut
  dispatch/pointer) vs C2 (pre-existing, surfaced at 0446).
- **New issue:** NONE. **Closed issue:** NONE.

## FINAL STATUS

Production modified: NO. ROM built: NO. MAME run: NO. New trace: NO. Build number consumed: NO.
Build counter changed: NO. Phase D: NO. Phase E: NO.
