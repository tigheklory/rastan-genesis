# PROMPT-ID-0038 — Arcade Actor C Decompilation + Bestiary & Composer Correction

**Author:** Andy · **Date:** 2026-10-29 · **Method:** static source-code analysis (NO traces).
**Order honored:** SOURCE CODE → BESTIARY → EDITOR. No Genesis ROM/runtime/compiler change, no build
number, **`Test.json` and authored palettes byte-identical** (verified by hash). No new source-of-truth
DB — the manifest remains authoritative; the Bestiary was improved in place.

---

## A. Existing C decompilation coverage before this task
`analysis/decompilation/c/` — **141 maintained C files, 16,659 lines**; `function_coverage.csv` 151 rows
(141 COMPLETE / 10 PARTIAL). The actor subsystem was substantially decompiled: state dispatch (0x40BAA),
state handlers (`rastan_actor_behavior.c`), marker materialization architecture
(`rastan_actor_materialization.c`), the template tables (`rastan_actor_tables.c`), and most creation
helpers (`rastan_actor_creation.c`: installer 0x4A086, scan 0x49F30, hunter 0x45248, scripted 0x45CFC/
0x45B18). **Gap:** the top-level routines that *choose* scene actors — the field-schedule **dispatcher**
0x4A02A, scene-kind selection 0x050F6B/0x050EE0, and scripted dispatch 0x0450D8 — were not in C.

## B. Original function decompiled this task
**`sched_dispatch_4a02a` (ORIGINAL ARCADE PC 0x0004A02A)** — the per-scene FIELD (Phase-1) actor-schedule
dispatcher — added to `analysis/decompilation/c/rastan_actor_creation.c`, COMPLETE, provenance
RECONSTRUCTED_FROM_68000 (disasm 0x4a02a..0x4a084). It computes the per-round scene index from
`a5@0x13E`/`a5@0x118`, indexes the 40-byte-per-scene table at **0x4A104**, selects a sub-record via
**0x49F30**, finds a free field-pool slot (`a5@0x4C8` downward, nine 0x40-byte records), and installs the
8-byte entry via **0x4A086**. Coverage ledger updated (`function_coverage.csv` +1).

**Connected actor-creation call graph (field path):**
`a5@0x13E/0x118 → sched_dispatch_4a02a (0x4A02A) → sched_occupancy_scan_49f30 (0x49F30) →
sched_install_4a086 (0x4A086) → actor_family_loader_4544e (0x4544E, base ← family table 0x45502/0x45562)
→ actor_palette_45684 (0x45684)`.

## C. R1-S2 contradiction — resolved from source (§3)
**Finding:** `$0224`/`$00F4` are **absent from R1-S2**; the prior PROMPT-0029 R1-S2 assignment was
incorrect (possibility #4, with #3). Proven by **excluding both reachable R1 creation paths**:

1. **Marker path:** handler **0x44082** (`h5_44082`, state 0x18, marker 'E') retires via
   `if (progress_13e < 0x18) arcade_4092e()`. R1-S2 progress is `0x11..0x16` (< 0x18), so the R1 'E'
   marker retires without writing `+0x1E`. H14 row: Round 1 prog 0x15 'E' → "prog<0x18 → 4092e", base `-`.
2. **Field-schedule path:** the newly-decompiled **0x4A02A** sets only FAMILY (`+0x3E`)/VARIANT (`+0x752`);
   the base (`+0x1E`) is resolved by **0x4544E from the family table**, whose 12 bases do **not** include
   `0x0224`/`0x00F4`. So the schedule cannot place these bases **by construction**.
3. Record-type/boss (0x45592) and scripted (0x45248/0x45CFC) paths do not write these bases either.

**Correct membership (H14, now in the manifest):** `0x0224` → **R2, R4**; `0x00F4` → **R4, R5, R6**;
`0x09EA` → R5; `0x0179` → R6. The **only** R1 Phase-2 marker actor is the **'M' burst** (`0x4d` →
state 0x1B/0x43ECC; H14 R1 prog 0x11) — children identity PENDING (coordinate-only), kept INCOMPLETE.
*A legal compositor frame / graphics base is NOT scene membership* — exactly the §3 caution.

## D. Manifest changes (§8)
Added `phase2_marker_round_membership` to `docs/design/rastan_actor_graphics_manifest.json` (indent-1,
clean diff): authoritative `by_round` map, `round1_note` (source-cited exclusion), `excluded_bases_r1`,
`exclusion_scope` (proven absent from both reachable R1 paths), and `evidence_c` (the C files/functions).
No historical evidence erased; the wrong R1 implication is corrected with source citations.

## E. Bestiary generator correction (§9)
`tools/graphics_optimizer/build_bestiary.py` previously **hardcoded** the round→base membership
(`_pins={2:['0x0224'],...}`). Replaced it to **read from the manifest**
(`M["phase2_marker_round_membership"]["by_round"]`). The generator now renders membership rather than
deciding it. Layout/sections/graphics/palettes unchanged.

## F. HTML Bestiary (§7/§9)
Regenerated in place: `docs/design/rastan_actor_bestiary.html` (719,654 bytes; `consistency_check: PASS`;
actors=38 field=11 bosses=6 scripted=10). R1 now renders "no materialized base writes … (H14)"; R2 renders
`0x0224`, etc., sourced from the manifest.

## G. Palette Composer changes (§10)
- Server: each sprite usage now carries `membership` — `field_phase1` for enemies (field schedule →
  family table), `shared` for player/weapons/items/effects/hazards. (Marker-chain castle actors keep
  their `scene_key`, corrected to R2/R4/R5/R6 under the prior commit `44f83ebe`.)
- Client (`app.js`): the Objects list filter is membership-aware — scene-tagged actors show only in their
  subround; **field enemies show only in field/S1 scenes, not the castle/S2**; shared assets always show;
  an **"All Assets (research)"** toggle reveals everything. Existing mixed-bank per-piece rendering
  (PROMPT-0028) and the frame browser are unchanged.

## H. Verification (§13)
- `verify_r1s2_castle_browser.py` **15/15**: R1-S2 shows ONLY the 'M' burst; `0x0224`=R2/R4,
  `0x00F4`=R4/R5/R6 (and NOT in the excluded rounds); multi-bank `0x91` composite uses both banks 3+12;
  per-round palette round-sensitive; enemies tagged `field_phase1`, shared tagged `shared`; **R1-S2 Castle
  view hides Lizardman etc.**; R1-S1 field view shows them; **Test.json unchanged**.
- `verify_r1s2_actor_roster.py` 5/5 (roster v2 cross-check points at the manifest). `verify_per_piece_palette.py` 6/6.
- Bestiary generator `consistency_check: PASS`; manifest valid JSON; `app.js` `node --check` OK.
- C semantics checked against the independent H14 marker-chain table (agreement) and the disassembly PCs
  (cited inline), not against a table derived from the same source.

## I. Remaining incomplete original-code paths (honest)
- **NOT decompiled this task:** scene-kind selection **0x050F6B/0x050EE0** (field↔castle↔boss partition),
  scripted dispatcher **0x0450D8**, and the full subround S1/S2/S3 boundary logic (§7). The partition
  evidence still rests on the prior `scene_phase_state_machine` analysis; a full C decode of 0x050F6B is
  the next step to make §7 source-complete for all six rounds.
- **'M' burst children identity** remains PENDING (coordinate-only child presentation not statically
  decodable as one composite).
- **Per-round FIELD rosters** are classed as `field_phase1` (field vs castle), not yet per-(round,subround)
  exact — that needs decoding each round's 0x4A104 schedule record set. The §10 filter is therefore
  correct at the field/castle granularity, not yet per-round-exact for field enemies.
- These are documented limitations, not claimed completions. **Not all six rounds are fully decoded.**

## J. Updated coverage & no-change confirmation
`function_coverage.csv`: +1 (0x4A02A, COMPLETE). No Genesis ROM built; no native/runtime/audio/compiler
change; `Test.json` and authored palette decisions byte-identical (hash-verified in the test).

## Files changed
- `analysis/decompilation/c/rastan_actor_creation.c` (sched_dispatch_4a02a)
- `analysis/decompilation/c/function_coverage.csv`
- `docs/design/rastan_actor_graphics_manifest.json` (phase2_marker_round_membership)
- `tools/graphics_optimizer/build_bestiary.py` (read membership from manifest)
- `docs/design/rastan_actor_bestiary.html` (regenerated)
- `tools/graphics_editor/server.py` (membership tags) · `tools/graphics_editor/app.js` (membership filter + All Assets)
- `tools/graphics_editor/verify_r1s2_castle_browser.py` · this report · `AGENTS_LOG.md`

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0038`
