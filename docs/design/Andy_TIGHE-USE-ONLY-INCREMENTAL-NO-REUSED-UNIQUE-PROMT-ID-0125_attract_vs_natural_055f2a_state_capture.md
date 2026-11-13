# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0125 — attract-vs-natural `$055F2A` state capture

**Author:** Andy · **Date:** 2026-11-11 · **Type:** analysis + diagnostic design. NO production behavior changed,
NO R2/LUT/scratch/audio/throne work. Build 0564 (Tighe-accepted throne/frontend recovery) is **untouched**. The
`.Lscene_scroll_reseed_rebuild_bad_ptr` invariant is **untouched**. (This session reached its working budget
before an instrumented diagnostic ROM could be built; the complete, ready-to-build diagnostic design is below so
the next session builds it directly. No guess at a production discriminator was made.)

## Phase 1 — static analysis result

**A semantic discriminator was NOT proven statically this session.**

- The prompt-listed retained fields do NOT distinguish the two routes: both natural next-subround teardown and
  attract-demo gameplay entry reach the same state-8 teardown, so `A5+0x13AA == 8` is identical, and `A5+0x13E`
  / `A5+0x13B8` / `A5+0x1242` are populated by the same teardown. [confirmed from 0123 binary + the state-8
  dispatch]
- The project Ghidra exports (`function_inventory.tsv`, `decompiler_export.c`) contain **no labelled**
  attract / demo / credit / game-mode function or field; the controllers are unnamed `FUN_*`. An A5-offset
  frequency scan did not surface an obvious binary mode flag. Arcade inputs are read from Taito I/O
  `0x390001 / 0x390007`; tracing the coin→start→play-vs-attract controller to a persistent retained mode field
  was not completed/proven within this session.

**Important new evidence from the Build-0564 attract crash screen (direct runtime, image supplied by Tighe):**
the crash handler captures `CRASH_GS_00/02/04/34/200` from `(%a0)` where `%a0 = 0x00FF1000` at the crash
(`crash_handler.s:216-220`). For the attract route it shows `+00=0002 +02=0002 +04=0006 +34=0000 +200=0000`,
i.e. the first descriptor longwords at `$FF1000` are `0x00020002`, `0x00060000`, … — **not** valid Plane-B
descriptor pointers (which must lie in `[0x0F08, 0x3A00C)`). This proves the attract `$FF1000` table is
stale/invalid at the reseed, consistent with the trap. **This is diagnostic evidence only; descriptor validity
must NOT be the production discriminator.**

## Candidate discriminators investigated (none proven)

| Candidate | Why considered | Status |
|---|---|---|
| `A5+0x13AA` substate | the teardown selector | REJECTED — both routes == 8 |
| `A5+0x13E / 0x13B8 / 0x1242` | record/stage | REJECTED — same teardown populates them |
| `genesistan_current_scene_id`, `fg_native_gameplay_owner` | Genesis-side owner | UNPROVEN at `$055F2A` for both routes (needs capture) |
| arcade game-mode / attract / credit flag | the real semantic difference | NOT ISOLATED statically (unlabeled Ghidra) — this is the field the diagnostic must find |
| `$FF1000` descriptor validity | observable difference | DIAGNOSTIC EVIDENCE ONLY — forbidden as the fix |

## Phase 2 — diagnostic ROM design (ready to build; isolated, trivially removable)

### Hook point
Instrument the `$055F2A` post-teardown publication cut — i.e. the Genesis native reseed entry that 0549's splice
calls (`0x70B38` = the reseed wrapper that sets the reseed-pending flag and `bsr`s the main reseed). Capture
BEFORE the reseed/rebuild runs. Gate everything behind a new build flag, e.g.
`RASTAN_DIAG_055F2A_CAPTURE` (default 0; the production path is byte-unchanged when 0). Keep it in one isolated
`.if RASTAN_DIAG_055F2A_CAPTURE … .endif` block so it is removable in one edit.

### Capture fields (write to a diagnostic buffer, then display + halt)
At the hook, with `A5 = 0x00FF0000`:
- `A5+0x13AA` (substate), `A5+0x13E` (current record), `A5+0x13B8` (saved next record), `A5+0x1242` (stage).
- `genesistan_current_scene_id` (byte), `fg_native_gameplay_owner` (byte).
- **Candidate game-mode bytes** to help find the discriminator: dump a small window of low A5 game-flow fields
  (e.g. `A5+0x02, 0x04, 0x14, 0x118, 0x13A, 0x214, 0x216, 0x218, 0x21A` — the most-referenced game-flow offsets)
  so the natural-vs-attract screenshots reveal which one differs.
- The 16 descriptor longwords at `$FF1000`: display a compact signature — first invalid-pointer index, count
  valid (in `[0x0F08,0x3A00C)`), count invalid, and a 32-bit XOR checksum of the 16 entries. (Reuse the same
  `[0x0F08,0x3A00C)` range the invariant uses, for the signature only — NOT as a control decision.)

### Display + halt
Reuse the existing crash/diagnostic screen infrastructure (`crash_handler.s` text/hex routines, or extend the
`CRASH_GS_*`/STATE rows) to render the captured fields, then `trap #0`-style halt (its own diagnostic halt — do
NOT route through / weaken `.Lscene_scroll_reseed_rebuild_bad_ptr`; the production invariant stays intact). A
single screenshot must contain every value.

### Two capture ROMs for Tighe
- **Capture A (attract):** the diagnostic normal ROM. Let the title/attract sequence naturally reach the
  gameplay demo; the diagnostic fires at `$055F2A` and halts with the state. No user input needed.
- **Capture B (natural R1-S2→R1-S3):** the easiest supported path is the **R1-S2 direct-start** variant of the
  diagnostic ROM, played with invincibility (already supported) through the real S2→S3 boundary so the retained
  `$055F2A` lifecycle fires for real. Do NOT fake it by writing the next record directly.

### Comparison goal
Diff Capture A vs Capture B. The field that is reliably different (expected: a low A5 game-mode/attract byte,
with the `$FF1000` signature valid in B and invalid in A) is the proven discriminator. The NEXT prompt
implements the production fix by gating the `$055F2A` reseed on that proven semantic field.

## Deliverable status this session
- Phase 1 analysis: done (no static discriminator proven; attract `$FF1000` invalidity confirmed from the
  existing crash dump).
- Phase 2 diagnostic ROM: **designed, not built this session** (budget). No source changed; Build 0564 and the
  throne repair untouched; the invariant untouched.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0125`
