# Andy — Audit of Cody's Interrupted Build 0428 Work (read-only; documentation preservation)

**Date:** 2026-10-15 · **Type:** READ-ONLY AUDIT, preserved to required design documentation. No
source modified, no ROM, no MAME, no gameplay/profiling, no git state change, Cody's WIP untouched.
This file records findings already collected in the prior audit pass; it does not repeat the
investigation. Baseline under audit: HEAD `9982f7c "Build 426"`; working tree = uncommitted Build-0428
WIP (build counter advanced to 432).

> **Evidence discipline:** statements are tagged **[FACT]** (directly observed this pass),
> **[CLAIM]** (asserted in Cody's report, not independently verified here), or **[INFERENCE]**
> (reasoned from observed context, not line-by-line verified). Per the task, unsubstantiated prior
> statements are labelled rather than re-investigated.

---

## ⚠ Framing correction (FACT — the most important finding)

The task describes Cody's 0428 as a **death-effect / Flying Demon** presentation optimization. The
working tree shows otherwise: **the implemented Build-0428 code change is the Rastan PLAYER sprite
optimization.** [FACT]

- Cody's implementation report is titled *"Cody Build 0428 — Rastan **Player** Genesis-Native Sprite
  Optimization"* (`docs/design/Cody_build0428_rastan_player_genesis_native_optimization.md`). [FACT]
- Every `apps/rastan-direct/src/pc090oj_hooks.s` diff hunk is in the **player** compositor labels
  `native_player_frame_try` / `native_player_secondary_frame` (arcade primary `0x054492`, secondary
  `0x0546A8`) plus the `profile_native_levelb_success` / `profile_native_actor_entry` region. [FACT]
- The death-effect material in the tree is a **separate semantic-validation / decompilation
  document** (`docs/design/Cody_enemy_death_drop_semantic_validation.md`) that *corrects Andy's
  earlier death-effect taxonomy*. It is analysis, PROVEN statically — **not** an implemented renderer
  change. [FACT]
- The task's "shared fast route for fixed 16×16 geometry with frame-wide attributes / 24
  selector·orientation contexts" matches the **player** fast path (the player doc: "fixed 16×16 size,
  frame-level attribute in 1,172/1,200 primary keys and 416/416 secondary keys"). The banks
  0x30/0x35/0x3F cited in the task appear only in the death-effect **validation** doc's analysis
  (burst/demon/boss death palette banks), not in an implemented death-effect renderer. [FACT]

Consequence: **no death-effect / Flying-Demon presentation *optimization* exists in the tree.**
[FACT] The 0428 implementation is the player path (which, per the earlier project framing, is Cody's
assigned player task).

---

## 1. Executive summary

- **Implemented (player optimization):** Cody replaced the generalized per-piece work in the player
  primary/secondary compositors with a generated `pc090oj_player_piece_table` + direct bounded queue
  appends; the existing residency/SAT finalizer is reused and the unresolved-selector fallback
  remains. [FACT for the code locations; INFERENCE that integration is complete] His doc claims the
  5-ROM family passed mechanical gates and the rope benchmark improved 806→803 frames; real-Genesis
  acceptance is explicitly **USER MUST VERIFY**. [CLAIM]
- **Not implemented (death effects):** No death-effect/Flying-Demon optimization. What exists is
  **decompilation + semantic validation** (categories A/B/S/C1/C2/D mapped to bases/selectors/
  compositors, correcting Andy's taxonomy) plus two new raw decompiles — analysis only, no runtime
  delta. [FACT]
- **Baseline:** HEAD `9982f7c "Build 426"` is intact and recoverable. [FACT] Working tree is an
  uncommitted multi-build WIP (counter → 432). [FACT]

## 2. Complete modified-file inventory

**Cody's player implementation (attributable to his 0428 task):**
- `apps/rastan-direct/src/pc090oj_hooks.s` (+221): player primary/secondary fast path
  (`native_player_frame_try`, `native_player_secondary_frame`, `profile_native_levelb_success`
  region).
- `apps/rastan-direct/src/pc090oj_assets.s` (+8): incbin of new `pc090oj_player_piece_table.bin`.
- `tools/translation/precompute_pc090oj_frame_table.py` (+120): generates the player piece table
  (12-byte index record `>IBBHhh`; PLAYER_FORMAT_COMPACT / MIXED_ATTR).
- `tools/translation/verify_pc090oj_frame_table.py` (+95), `verify_pc090oj_direct_dispatch.py` (+58):
  player-table coverage; guards that the player loops no longer call the generalized emitter and that
  the common-enemy (`0x0A73`) and burst (`0x0275`) paths are **unchanged**.
- `tools/mame/scripts/native_sprite_cost_buckets.lua` (+3); `apps/rastan-direct/Makefile` (+11);
  `tools/translation/postpatch_startup_rom.py` (+2), `verify_canonical_rom.py` (+2).

**Cody's death-effect *analysis* (not an optimization):**
- `docs/design/Cody_enemy_death_drop_semantic_validation.md` (new); raw decompiles
  `analysis/decompilation/c/raw/00042abc.c`, `00044804.c` (new); edits to `raw/00040ccc.c`,
  `rastan_actor_behavior.c`, `rastan_actor_lifecycle.c`, `h16_burst_child_render.tsv`,
  `h16_burst_child_structure.json`, `function_coverage.csv`, `historical_claim_audit.csv`, `README.md`.

**Generated / build outputs (Cody's builds):** `apps/rastan-direct/out/*.o`, `rastan_direct_video_test.elf`,
`symbol.txt`, `*_patch_manifest.json`, `address_map.json`, `crash_build.inc`, `pc090oj_config.inc`;
`build/genesis_postpatch.disasm.txt`, `build/rastan-direct/address_map.json`, `build_counter.txt` (→432),
`rastan_direct_patch_manifest.json`, `build/rom_inventory.json`,
`build/mame/home/genesistrace/genesis_exec_trace.log`.

**Ownership-uncertain / NOT Cody's (Andy prior-task outputs intermingled):**
- `docs/design/Andy_enemy_death_effect_sprite_taxonomy.md` (untracked) — Andy's prior deliverable.
- `AGENTS_LOG.md` (+113) — contains **both** Andy's prior entries and Cody's; mixed ownership. A
  future commit must not attribute all of it to Cody.

## 3. Implementation status and technical findings

- **Player optimization:** COMPLETE per Cody's doc; **not independently diff-verified line-by-line in
  this audit** (tooling minimized per instruction). [CLAIM + INFERENCE] The new player table, the
  hook hunks in the player compositors, and the verifier guards are present and internally consistent;
  the guards keep the `0x0A73` (common enemy) and `0x0275` (burst) paths unchanged. No evidence in the
  diff of changes to gameplay logic, actor state, sprite ordering, DMA ownership, or SAT publication —
  the doc states the existing residency/SAT finalizer is reused. [FACT for guard tokens; INFERENCE for
  "no ownership change"]
- **Death-effect optimization:** NOT STARTED — analysis/validation only. [FACT]
- **Death-effect semantic validation content (reference, from Cody's doc):** it corrects Andy's
  taxonomy — e.g. the bat "rec_type 7" speculation is REJECTED (bats are rec_type 10/11, base `0x03F6`/
  `0x0268`, pop via specialized `0x42ABC`, base `0x0275` selector `0xA8`); the `0x0275`/`0x9E–0xA0`
  program is the `+0x39!=0` **child/burst** branch (`0x40DD8`), not the ordinary common-enemy death
  (which takes `0x40CCC`'s `0x0A73` default at `+0x03==0,+0x39==0`); Flying-Demon death is a paired
  specialized `0x42102→0x4213A[15]→0x42ABC` death (bank 0x35), boss (Round 5) bank 0x3F; and enemy
  death *does* leave a family-12 in-place reward via schedule byte `+0x36` (`0x40C0E`), base `0x0A5A`
  — i.e. a schedule-eligibility reward, not a RNG drop allocator. These are **[CLAIM] (Cody's static
  proofs)**; they revise Andy's prior taxonomy and should be reconciled when the death-effect work is
  actually scheduled. Not required for the player-optimization resume.

## 4. Existing validation evidence and missing checks

- **Mechanical frame-table / dispatch verifiers:** extended for the player table (present in the
  diff). Whether they were **run and passed** is **[CLAIM]** (Cody's doc); not executed/confirmed here
  (prohibited).
- **Death-effect categories A/B/S/C1/C2/D:** marked PROVEN in the validation doc — **static
  decompilation evidence**, verifiable against the raw decompiles; not a runtime test. [FACT that they
  are static]
- **Real-Genesis gameplay (player visuals):** NOT done — **USER MUST VERIFY**. [FACT, per doc]
- **Missing:** independent confirmation of the mechanical-gate PASS; byte-unchanged confirmation of the
  common/burst/death paths; real-Genesis player acceptance.

## 5. Available performance measurements

- **Player path:** rope benchmark **806 → 803 frames (13,450.653 → 13,400.588 ms)** — ~3-frame
  improvement. **[CLAIM]** in Cody's doc; `genesis_exec_trace.log` is modified but I did not confirm
  it backs this exact measurement. Treat as claimed, not independently verified.
- **Ordinary-death sprite presentation:** **Not established** (no death-effect optimization). [FACT]
- **Flying-Demon death-fountain presentation:** **Not established** (validation only). [FACT]

## 6. Risks and unresolved issues

1. **Task/premise mismatch (highest):** the implemented 0428 is the **player** optimization, not the
   death-effect optimization the task assumes. If Cody resumes on the task's premise, he may think
   death-effect work is in progress when it is not — risk of confusion/duplication.
2. **Uncommitted multi-build WIP:** `build_counter.txt` = 432 vs HEAD 426 → numbered builds 427–432
   consumed; tree is not a clean single build. (Consumed numbers are disposable per project
   discipline, but the state is messy.)
3. **Mixed doc ownership:** `AGENTS_LOG.md` and `Andy_enemy_death_effect_sprite_taxonomy.md` are
   Andy's prior outputs intermingled with Cody's WIP; a commit must separate them.
4. **Unverified claims:** mechanical-gate PASS and the rope delta are Cody-reported, not confirmed in
   this read-only pass.
5. **No line-by-line regression confirmation:** the player hunks were not exhaustively diffed; "no
   gameplay/DMA/SAT ownership change" rests on hunk context + the doc, not a full line review.
6. **Taxonomy reconciliation:** Cody's death validation revises Andy's taxonomy; the two documents
   disagree on several death-effect identities and must be reconciled before any death-effect
   optimization is scheduled (not needed for the player resume).

## 7. Minimal continuation instructions for Cody (automated engineering only)

For the **player** optimization (the actual 0428 work):
1. Re-run the mechanical frame-table + dispatch verifiers and the canonical ROM gate to confirm the
   claimed PASS.
2. Re-run the established **rope-race** automated benchmark to confirm 803 frames reproducibly (the
   one acceptable automated gameplay regression; no manual encounter navigation).
3. Diff-verify that the common-enemy (`0x0A73`) / burst (`0x0275`) / death paths are byte-unchanged
   (the verifier guards assert this; confirm).
4. Produce one clean numbered ROM family and hand to the **user** for real-Genesis visual/gameplay
   acceptance of the **player** sprites.

For **death effects:** treat them as analysis-only. Any optimization is a *new* task; do not treat the
validation doc as an implemented change, and first reconcile it against
`Andy_enemy_death_effect_sprite_taxonomy.md`. **Cody must not navigate gameplay to reproduce the
Flying Demon encounter** — nontrivial gameplay validation belongs to the user.

## 8. Workspace safety and preservation recommendations

**Preserve the current changes unchanged.** The accepted baseline (HEAD `9982f7c` Build 426) is intact
and recoverable; nothing needs reverting to recover it. The WIP is resumable. Before any future
commit: separate Andy's prior-task docs / AGENTS_LOG entries from Cody's 0428 player work, and label
the death-effect material as validation, not optimization. This audit modified no source, built no
ROM, ran no MAME, and made no git state change.

---

*Documentation preservation only. No new audit performed; findings reused from the prior read-only
pass. Do not represent the player optimization as user-accepted — real-Genesis acceptance is pending.*
