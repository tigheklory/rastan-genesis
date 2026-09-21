# Andy — Actor Decompilation C-Source Recovery + Fidelity Audit

**Agent:** Andy · **Type:** Analysis / preservation (no new gameplay research) ·
**Build context:** rastan-direct, counter 360 (NO ROM built, NO Genesis change, NO MAME).
**Manifest/bestiary/`build_bestiary.py`:** intentionally NOT modified. Cody verification files
untouched.

This is the standalone RULES.md report for the two C-source recovery passes. It documents a
process correction: too much reverse engineering had been preserved only as Markdown/JSON/Python,
so the actor decompilation is now preserved as **auditable, syntactically-valid C** that another
engineer/model/Cody can read and challenge. The 68000 binary/disassembly remains final authority;
this C is **NOT** original Taito source and is not guaranteed to rebuild an identical ROM.

## Why this exists (the process failure)
A function was being reported "completely decompiled" when only its Markdown description existed.
New rule (now enforced by guards): a function is "decompiled" only when raw + semantic C exist,
`function_coverage.csv` is updated, and it passes the syntax check — **then** the Markdown
interpretation is written.

## What was produced

### C source tree — `analysis/decompilation/c/`
- `rastan_arcade_types.h` — `ActorRecord` (byte-exact 0x40) + `ActorTemplate` (8) + globals +
  externs. Compile-time contract: `_Static_assert(sizeof(ActorRecord)==0x40)` and `offsetof`
  asserts (active@0x00, mode@0x03, state@0x05, rec_type@0x06, target_char@0x0D, field_0e@0x0E,
  x@0x16, y@0x1A, timer@0x1C, base@0x1E, comp_index@0x21, sched_slot@0x26, pal_attr@0x27,
  cfg_28@0x28, variant_2f@0x2F, comp@0x38, family@0x3E).
- `rastan_actor_tables.c` — record-type `0x45592`, family `0x45502`/`0x45562`, boss
  `0x454BA/D2/EA`, `0x444E0`, and the `0x40A86` marker-transition table, as real C data with exact
  values.
- `rastan_actor_dispatch.c` — `0x40BAA` state dispatch, `0x40E74` recheck, `0x41064` find.
- `rastan_actor_creation.c` — allocators/initializers (CHECKPOINT C).
- `rastan_actor_helpers.c` — template/palette loaders (`0x4543E`/`0x4544E`/`0x45684`).
- `rastan_actor_behavior.c` — engines (`0x40CCC`/`0x47140`/`0x473B8`/`0x4684E`) + the 10 H5
  state handlers.
- `rastan_actor_subsystems.c` — scene-wipe `0x3A7D2`, collision-addr `0x53A2E`, boss trigger
  `0x4449E`, config `0x41D08`, marker transition `0x40A60`, boss sync `0x42380`, scripted
  dispatcher `0x4AB5C`.
- `raw/` — 39 close-to-machine per-PC reconstructions (`raw/00040baa.c` etc.) + `raw_common.h`.
- `function_coverage.csv` — 58 rows (31 COMPLETE / 12 PARTIAL / 13 STUB_ONLY).
- `historical_claim_audit.csv` — 37 rows auditing every executable-arcade-code claim across the
  Andy docs vs the preserved C, with explicit `DOWNGRADED` notes.
- `README.md` — the tree's own contract/index.
- `raw_snapshots/decompiler_export_pre_actor_backfill.c` — the historical Ghidra export preserved
  byte-identical (never overwritten).

### Guards / tools — `tools/analysis/`
- `check_actor_decompilation_coverage.py` — every COMPLETE function has raw+semantic; all 10 H5
  handler PCs covered; also consumes the historical audit (fails if an old COMPLETE/DECODED claim
  has no C and no `DOWNGRADED` note). **PASS.**
- `check_decompilation_fidelity.py` — ActorRecord layout contract compiles; every COMPLETE raw has
  an `ORIGINAL ARCADE PC:` annotation and no ellipsis/TODO/SUMMARIZED body; PARTIAL bodies are
  marked; `0x40BAA` raw uses the true 16-bit self-relative table; audit consistency. **PASS.**
- `gcc -std=c11 -fsyntax-only` — clean on all 6 semantic + 39 raw files.

## Fidelity fixes made in the second pass
- Fixed the false global name `marker_cell` at `+0x0E`: it is **polymorphic** — a collision-cell
  **address** in the hunter context (`0x41180`/`0x40E74`) and an **anim/sequence index** in the
  materialized engines (`0x47140`/`0x4684E`). Now `field_0e[4]` with `ar_cell_addr()` /
  `ar_anim_index_0e()` accessors, so a convenient name never becomes false architecture.
- Fixed the `+0x28`/`+0x29` struct overlap (one word + low-byte accessor `ar_cfg29()`).
- `raw/00040baa.c` now preserves the arcade's **signed 16-bit self-relative** jump table (was a
  convenience absolute-PC `uint32` table) — the raw tree shows what the 68000 actually did.
- `0x40E74`/`0x41064` operate on arcade **addresses** + `collision_word_at()` instead of casting a
  stored value to a host pointer.

## Status downgrades (honest; enforced by the audit guard)
- `0x559B2`/`0x55A14` FG/BG column builders — the `Andy_pc080sn_arcade_fg_complete_decompile_*`
  docs said "complete decompile" → **PARTIAL** (arcade producers not re-lifted; historically partial).
- `0x3CEB0` shared anim/motion core → **STUB_ONLY** (field semantics proven; body not traced).
- Pass-1 downgrades preserved: `0x473B8`, `0x4396A`, `0x43B32`, `0x4415A`, `0x40C08`.
  (`0x41180` was pass-1 PARTIAL but is now **COMPLETE** — closed by CHECKPOINT H6, see
  `docs/design/Andy_h6_marker_materialization_decompilation.md`.)

## What remains REFERENCED_ONLY (Markdown knows it; C does not yet lift it)
`0x53FA6`/`0x54038` (0x7E door / mode-8), `0x55DFE`/`0x469E8` (transition sequencer), `0x450D8`/
`0x4580C` (spawn dispatcher/preprocessor), `0x4AF1A` (boss sub-phase dispatcher), master VBlank
dispatch `0x3A256`, sound queue `a5+0x292..0x297`, scene descriptor `0x3951C` decode. These are
tracked in `historical_claim_audit.csv` and are the honest next-lift targets — none is claimed
COMPLETE.

## USER MUST VERIFY / review
Read `analysis/decompilation/c/` (start at `README.md`, then `function_coverage.csv` and
`historical_claim_audit.csv`), and challenge any raw reconstruction against
`build/maincpu.disasm.txt`. The two guards + `gcc -fsyntax-only` are the mechanical acceptance
gate. No H6/H7 was started; awaiting your review before further gameplay decompilation.

## Related documents
`docs/design/Andy_actor_state_machine_decompilation.md`,
`docs/design/Andy_actor_allocation_initialization_decompilation.md`,
`docs/design/Andy_actor_behavioral_identity_decompilation.md` (each now carries a "C SOURCE
BACKFILL" section pointing here and recording its own downgrades).
