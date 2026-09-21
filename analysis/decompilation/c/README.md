# Rastan arcade reconstructed decompilation — C source

This tree is the **auditable C representation** of the actor decompilation done in
CHECKPOINTS A, B, C, and H (see `docs/design/Andy_actor_*_decompilation.md`). It exists so
another engineer, model, Cody, or a future Andy can read the code and challenge the interpretation
rather than trusting the Markdown conclusions.

> These files are derived from static analysis of the original Motorola 68000 program
> (`build/regions/maincpu.bin` + `build/maincpu.disasm.txt` + the Ghidra export). They are an
> auditable representation of program semantics, **NOT original Taito source**, and are **not**
> guaranteed to compile back into an identical ROM. The 68000 binary/disassembly remains the final
> authority.

## Layout
- `rastan_arcade_types.h` — `ActorRecord` (0x40-byte, proven offsets), `ActorTemplate` (8-byte),
  globals, and externs for hardware / not-yet-fully-decompiled helpers.
- `rastan_actor_tables.c` — the record-type (`0x45592`) and family (`0x45502`/`0x45562`/`0x454BA/D2/EA`) templates as real C data, with exact values.
- `rastan_actor_dispatch.c` — `0x40BAA` state dispatch (+ table), `0x40E74` recheck, `0x41064` find.
- `rastan_actor_creation.c` — allocators/initializers (CHECKPOINT C).
- `rastan_actor_helpers.c` — template/palette loaders (`0x4543E`/`0x4544E`/`0x45684`).
- `rastan_actor_behavior.c` — engines (`0x40CCC`/`0x47140`/`0x473B8`/`0x4684E`) + the 10 H5 handlers.
- `rastan_actor_materialization.c` — CHECKPOINT H6: state-0 scanner/hunter `0x41180`, the 28-route
  character-hunter materialization dispatch (`0x41362`), floor placement `0x41336`, the marker-chain
  transform states `0x40E88` (0x1E) / `0x40EDE` (0x20), retarget `0x4103A`, attr loader `0x45418`,
  light-source register `0x41BEE`.
- `rastan_actor_lifecycle.c` — CHECKPOINT H7: retire/clear `0x4092E`, retarget `0x4103A` (now
  COMPLETE), impact/child activate `0x447F0`/`0x448B2`, component-pool driver `0x43F4E`/`0x43F52`,
  phase-advance leaf `0x41F9C`, score award `0x3B726` (value = dying actor `+0x2C`), and the
  move+contact stepper `0x42E38` (PARTIAL — anim core `0x3CEB0` still STUB).
- `rastan_anim_motion_core.c` — CHECKPOINT H8: the shared animation-frame advance + motion
  integration core `0x3CEB0` and leaves `0x3CF40` (frame wrap) / `0x3CF52` (frame→velocity + axis
  locks, table `0x3CFD4`) / `0x3CFB0` (band test). Closes the H7 debt and makes `0x42E38` COMPLETE.
- `rastan_actor_collision.c` — CHECKPOINT H9: the enemy collision manager `0x449B4` (player boxes
  vs enemy hurtboxes, the scan H8 could not find), AABB primitive `0x44CBA` + hurtbox rect table
  `0x44CE0`, hurtbox-index selector `0x446BC`, one-hit reaction `0x447CE`/`0x448D8`. Fatal path is
  one-hit → state 0x0F death anim → score(+0x2C) → retire. (Per-kill item-drop creator still OPEN.)
- `rastan_actor_render.c` — CHECKPOINT H10: render selector dispatch `0x3D054` + selector thunks
  `0x3F0BC`/`0x4770E`/`0x3FFDC`/`0x3FFF0` (all funnel to the shared 0x3C902 interpreter).
- `rastan_actor_palette.c` — CHECKPOINT H10: palette-attribute resolver `0x45684` (non-fam2 table
  `0x45722`, family-2 table `0x456EC`; round/variant/comp → palette line → +0x27).
- `rastan_scene_map.c` — CHECKPOINT H11: scene/section resolver `0x503BC` (0x50EE0/0x50F6B →
  section kind), collision-grid column writer `0x559B2` (marker = column_record[20+…]),
  background decompressor `0x563A6`. Six Phase-2 castle starts proven.
- `raw/` — close-to-machine reconstructions (per arcade PC, e.g. `raw/00043840.c`), for auditing.
- `function_coverage.csv` — status/provenance index (guarded).

## Provenance classes (per function header)
`GHIDRA_RAW` (normalized from the preserved export), `RECONSTRUCTED_FROM_68000` (from
disasm/binary), `SEMANTIC_REWRITE` (cleaned from a raw reconstruction).

## Guard & syntax
- `python3 tools/analysis/check_actor_decompilation_coverage.py` — every COMPLETE function has a raw
  + semantic artifact; all 10 H5 handler PCs are covered. (Currently PASS.)
- `gcc -std=c11 -fsyntax-only` passes on the whole tree (semantic + raw). It is NOT meant to link or
  run the game; hardware / undecompiled helpers are `extern`.

## Standing rule (post-recovery)
A function is "decompiled" only when its raw+semantic C exists here, `function_coverage.csv` is
updated, and it passes the syntax check — THEN the Markdown interpretation is written/updated. No
future checkpoint may report a function "completely decompiled" without the C artifact.

## Second recovery pass (fidelity audit + historical backfill)
- `ActorRecord` is now byte-exact with `_Static_assert(sizeof==0x40)` + offsetof asserts; the
  polymorphic `+0x0E` is `field_0e[4]` with documented hunter (cell address) vs materialized
  (anim index) views; the `+0x28/+0x29` overlap is fixed (one word + low-byte accessor).
- Raw `0x40BAA` now uses the **true signed 16-bit self-relative** jump table (not a convenience
  absolute-PC table); `0x40E74`/`0x41064` use arcade **addresses** + `collision_word_at`, not host
  pointers, so the arcade mechanism is explicit.
- Surrounding subsystems backfilled (`rastan_actor_subsystems.c` + raw): scene-wipe `0x3A7D2`,
  collision-address `0x53A2E`, boss trigger `0x4449E`, config loader `0x41D08`, marker transition
  `0x40A60`/table `0x40A86` (COMPLETE); scripted dispatcher `0x4AB5C`, boss sync `0x42380`,
  `0x559B2/0x55A14` (PARTIAL, historically partial — not upgraded).
- `analysis/decompilation/c/historical_claim_audit.csv` audits every executable-arcade-code claim
  across the Andy docs vs the C tree, with explicit `DOWNGRADED` notes where old Markdown
  "complete" claims exceeded the preserved C (e.g. `0x559B2` FG "complete decompile" → PARTIAL,
  `0x3CEB0` → STUB).
- Guards: `tools/analysis/check_actor_decompilation_coverage.py` (now also consumes the audit) and
  `tools/analysis/check_decompilation_fidelity.py` (layout contract, no-ellipsis-in-COMPLETE, raw
  table widths, PARTIAL markers, audit consistency). Both PASS; `gcc -std=c11 -fsyntax-only` clean.
