# Cody - Lizard-Man Visual and Combat Acceptance Fix Attempt

**Date:** 2026-07-18  
**Type:** Analysis-first acceptance task, STOP before implementation  
**Build context:** Build 0206/256, `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`  
**Build 0206 SHA256:** `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`  
**Scope requested:** prove and implement lizard/enemy palette, lizard vertical alignment, and lizard damage/combat corrections, then produce Build 0207.  
**Outcome:** STOP. Build 0207 was not produced because the task's required three-correction acceptance set is not safely implementable from the evidence captured here.

## Phase 0

Classification: **EXTENDING**. This continues KF-064/KF-065 and OPEN-017/OPEN-024 after Build 0206. The arcade program remains authoritative; Genesis code may only translate hardware intent through helper/opcode-replacement paths and must not force actors, records, SAT entries, health loss, collision overlap, or per-enemy visual overrides.

Priors read: `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `CURRENT_STATE.md`, latest `AGENTS_LOG.md`, and the prior lizard evidence/implementation notes:

- `docs/design/Cody_lizard_composite_pc090oj_staging_implementation.md`
- `docs/design/Cody_lizard_acceptance_divergence_trace.md`
- `docs/design/Cody_lizard_actor_activation_progression_fix.md`
- `docs/design/Cody_lizard_b5_activation_writer_provenance.md`

Relevant confirmed priors:

- KF-064: first visible Stage-1 lizard men are actor block `A5+0x02C8` composite records, not record 46.
- KF-065: Build 0206 restores natural activation progression for multiple lizard actors by correcting the collision-buffer upper bound at `runtime_genesis_pc 0x000414CC`; remaining palette, feet/ground, and damage/contact behavior are separate acceptance items.
- KF-063: PC090OJ expansion engine fixes must remain actor/producer-faithful and must not force records/SAT.
- KF-043/KF-046: palette-line routing and line ownership are existing shared mechanisms.
- KF-058: player HP/control context; player HP is `A5+0x013A`, initialized to `0x3000`, and death check is at arcade `0x0517E6` / Genesis `0x0519E6`.

Contradiction of CONFIRMED/STRONG finding: **NONE**.

## Baseline

- Counter before task: `206`
- Build 0206 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Build 0206 and rolling SHA256: `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`
- Size: `1,583,440` bytes
- opcode_replace count: `215`
- total_genesis_bytes_covered: `0x182950`
- Build 0207 produced: **NO**

## Evidence Artifacts

Trace directory:

`states/traces/lizard_visual_combat_acceptance_fix_20260718_232843/`

Key files:

- `lizard0207_probe.lua` - arcade vs Build 0206 lizard/PC090OJ/palette/Y sampler.
- `arcade_summary.csv`, `arcade_records.csv`, `arcade_palette.csv`
- `genesis0206_summary.csv`, `genesis0206_records.csv`, `genesis0206_palette.csv`
- `lizard0207_hp_tap.lua` - narrow HP/mode write tap attempt.
- `arcade_damage_wide_hp_writes.csv`, `arcade_damage_wide_hp_summary.csv`
- `genesis0206_damage_wide_hp_writes.csv`, `genesis0206_damage_wide_hp_summary.csv`
- `lizard_visual_combat_reduced.md`, `lizard_visual_combat_reduced.json`
- `snaps/` - arcade and Build 0206 MAME snapshots at sampled frames.

Test ROMs/environments:

- Original arcade MAME `rastan` / Rastan World Rev 1, used as authoritative behavior/palette/position reference.
- Genesis Build 0206 in MAME Genesis driver, SHA above.
- Genesis Build 0207: **not run**, because no Build 0207 was produced.

## JSON Address Mappings Used

All paired code addresses below were resolved through `build/rastan-direct/address_map.json`, not arithmetic offset assumptions:

- `arcade_pc 0x000412CC -> runtime_genesis_pc 0x000414CC` (`patched_site`) for the Build 0206 collision-buffer upper-bound fix.
- `arcade_pc 0x00041320 -> runtime_genesis_pc 0x00041520` (`arcade_copy`) for the actor `b5` activation writer.
- `arcade_pc 0x000504A2 -> runtime_genesis_pc 0x000506A2` (`arcade_copy`) for player HP init.
- `arcade_pc 0x000517E6 -> runtime_genesis_pc 0x000519E6` (`arcade_copy`) for player HP death check.
- `arcade_pc 0x000519AC -> runtime_genesis_pc 0x00051BAC` (`arcade_copy`) for one static HP decrement candidate.
- `arcade_pc 0x00054EA0 -> runtime_genesis_pc 0x000550A0` (`arcade_copy`) for one static HP decrement candidate.
- `arcade_pc 0x00054FA4 -> runtime_genesis_pc 0x000551A4` (`arcade_copy`) for one static HP decrement candidate.
- `arcade_pc 0x00054FBC -> runtime_genesis_pc 0x000551BC` (`arcade_copy`) for one static HP decrement candidate.

Genesis-only helper symbols from `apps/rastan-direct/out/symbol.txt`:

- `palette_route_lookup = runtime_genesis_pc 0x00071DBC`
- `palette_route_table = runtime_genesis_pc 0x000737D0`
- `pc090oj_sprite_ctrl_shadow = Genesis WRAM 0x00FFB9FA`

## Objective A - Palette Route

### Existing LUT

`apps/rastan-direct/src/palette_hooks.s` defines the shared route table and lookup:

- `palette_route_table` at source lines 48-54, symbol `0x000737D0`.
- `palette_route_lookup` at source lines 58-85, symbol `0x00071DBC`.
- Input semantics: `D0=scene_id`, `D1=owner`, `D2=arcade_bank`.
- Output semantics: `D0=Genesis line 0..3`, `D3=flags`; miss returns `D0=-1`.
- Current rows include Stage-1 FG bank `3 -> line 1`, BG bank `48 -> line 2`, PC090OJ bank `51/0x33 -> line 3`, HUD bank `0 -> line 0`.

Positive-control usage:

- Foreground bank 3 is routed to line 1 with carrier semantics in `palette_hooks.s`.
- Sprite/Rastan bank `0x33` is routed to line 3 by palette staging hooks and by `pc090oj_hooks.s` special-case SAT line selection.

### Current PC090OJ SAT Palette Selection

`apps/rastan-direct/src/pc090oj_hooks.s` source lines 1758-1808 implement `.Lpc090oj_place_record_in_slot` and choose the SAT palette line directly:

- Decode supplies `d7 = (pc090oj_sprite_ctrl_shadow & 0x00E0) >> 1` at lines 1535-1538.
- Placement computes `effective_arcade_bank = (word0 & 0x000F) | d7` at lines 1789-1792.
- It special-cases bank `0x30 -> line 2` and `0x33 -> line 3` at lines 1793-1801.
- Every other bank uses fallback `(bank >> 4) & 3` at lines 1802-1804.
- It does **not** call `palette_route_lookup`.

Build 0206 lizard evidence:

- Lizard tuple word0: `0x4046`.
- `pc090oj_sprite_ctrl_shadow = 0x0060` in gameplay.
- Effective bank: `0x36`.
- Current SAT line: `3`, by fallback `(0x36 >> 4) & 3`.
- Build 0206 visible lizard rows in the trace: `5346`; all visible lizard rows reported bank `0x36` and current line `3`.

Arcade palette evidence:

- Original arcade bank `0x36` at frame 1080: `0000 4318 00C0 0246 01C0 030E 2948 318A 6356 6B9A 10D2 2996 210A 380E 01CE 39CE`.
- Converted to Genesis CRAM format: `0000 08CC 0020 0082 0060 00C6 0444 0664 0CCA 0CEC 0228 046A 0444 0606 0066 0666`.
- Build 0206 staged line 3 at frame 1080 instead contains the bank-`0x33`/Rastan-like palette: `08AE 0000 0EEE 08AE 044A 0246 0008 0006 00EE 006E 0080 0060 0888 0666 0040 000E`.

Interpretation: **palette root is strongly narrowed**. PC090OJ lizard bank `0x36` bypasses the shared route table and falls through the legacy SAT fallback to line 3, which is already occupied by bank `0x33`/Rastan. A likely implementation boundary would be the shared PC090OJ palette-line selection inside `.Lpc090oj_place_record_in_slot`, not per-lizard/per-record constants and not raw CRAM patching.

Safety note: this task still cannot proceed to Build 0207 because Objectives B and C are not implementation-ready. Also, exact CRAM line ownership for bank `0x36` must be designed carefully because Genesis has only four CRAM lines and the current resident lines are already used by HUD/FG/BG/Rastan.

## Objective B - Vertical Position

User hardware evidence from a real Nomad reports lizard men appearing approximately 8 pixels too low. That observation is recorded as real hardware evidence and remains unresolved.

MAME evidence captured here does **not** support changing the global PC090OJ Y offset:

- `PC090OJ_TO_GENESIS_Y_OFFSET = -8` is defined in `pc090oj_hooks.s` line 155 and applied in `.Lpc090oj_decode_record` line 1484.
- Arcade and Build 0206 matched lizard Y samples line up in MAME after the existing offset:

| Frame | Arcade visible lizard Y | Build 0206 visible lizard Y |
|---:|---|---|
| 720 | `89..122` (`32` records) | `89..121` (`16` records) |
| 840 | `90..122` (`34`) | `89..121` (`16`) |
| 960 | `89..122` (`34`) | `89..122` (`26`) |
| 1080 | `90..122` (`16`) | `90..122` (`32`) |
| 1500 | `89..121` (`24`) | `90..122` (`18`) |
| 1680 | `89..121` (`32`) | `89..122` (`16`) |

Interpretation: **no safe vertical correction is proven**. A global Y change would contradict the matched MAME evidence and could regress Rastan, record 46, bats, projectiles, and other PC090OJ families. A record-specific or lizard-only displacement is explicitly forbidden by the prompt unless proven, and it was not proven here.

STOP reason for Objective B: the only available vertical action from this evidence would be an unproven displacement. That is a prompt-defined STOP condition.

## Objective C - Lizard Damage / Combat

Arcade MAME summary evidence proves the player HP value changes during the no-attack/right-walk lizard contact run:

- Original arcade HP sampled values include `0x3000`, then progressive decrements such as `0x2400`, `0x1800`, `0x1400`, `0x1000`, `0x0C00`, `0x0800`, `0x0400`, and wrap/terminal values.
- Genesis Build 0206 HP remained `0x3000` throughout gameplay samples, then `0x0000` in later state samples; it did not show the same progressive lizard-contact damage pattern.

However, the debugger-side HP write taps did not capture the later HP writers in either the two-byte or widened `A5+0x0138..0x013B` range. They only captured early initialization/clear writes:

- Arcade wide tap events: `3` rows, all initial clear/mode events around post-PC `0x03AF02`.
- Genesis wide tap events: `3` rows, all initial clear/mode events around post-PC `0x03B102`.

Static HP writer candidates exist and map cleanly through JSON, including arcade `0x0519AC -> runtime_genesis_pc 0x051BAC`, but this task did **not** capture a natural lizard attack/contact writer PC, lizard attack state, hitbox/hurtbox overlap, damage dispatch, or player hurt-state gate.

Interpretation: Genesis failing to damage Rastan is real user hardware evidence and is consistent with the MAME sampled HP comparison, but the required original gameplay path is not proven. A direct HP decrement, forced hurt state, or fabricated overlap would violate the prompt and architecture.

STOP reason for Objective C: combat can only be changed safely after a reliable runtime trace captures the original arcade damage writer/control path and the first Build 0206 divergence. That evidence is missing here.

## STOP Classification

Build 0207 was **not** produced.

Concrete safety blockers remain after bounded evidence collection:

- Objective B: vertical correction is not proven; MAME matched lizard Y ranges agree with the existing `-8` offset, so changing global or lizard-specific Y would be unsafe.
- Objective C: natural lizard damage path is not proven; HP changes are sampled in arcade but writer/control-path capture failed, so any implementation would be direct health manipulation or speculative collision/hurt-state work.

Objective A has a strong candidate implementation boundary, but producing Build 0207 with only the palette leg would not satisfy the task's required three-correction acceptance set.

## Recommended Next Task

Run a dedicated combat-path trace, not an implementation task:

- Use debugger breakpoints on the JSON-mapped static HP decrement candidates and player hurt-mode writers, not only memory write taps.
- Drive original arcade and Build 0206/rolling Build 0206 into the same no-attack lizard-contact window.
- Log actor entry/window, lizard attack state, player hurtbox fields, overlap result, branch decisions, HP writer PC, player mode writer PC, and mapped Genesis counterpart execution.
- Stop at the first arcade/Genesis divergence and only then design the smallest gameplay-path fix.

For palette, a later implementation can separately route PC090OJ effective bank selection through the shared palette route table after CRAM line ownership for bank `0x36` and bat banks is decided.

## Non-Actions

No source, spec, tool, Makefile, invariant, ROM, build-counter, or build-artifact changes were made. No Build 0207 was produced. No actor seeding, SAT forcing, collision fabrication, direct HP decrement, per-enemy palette constant, or Y-offset patch was applied.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017 and OPEN-024; OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: black bar/display instability, hurry-up bat spawning/timing/combat, record 132, FG/sky/HUD/D00298/continue/game-over, and the combat-path trace described above.

No issue ledger edit was made because this task stopped before an implementation or durable new accepted mechanism.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. The palette route is strongly narrowed but Build 0207 was not implemented/accepted, and the vertical/combat mechanisms are not proven enough for canonicalization.

## Architecture Compliance

CONFIRMED. The task remained evidence-only after STOP; no Genesis-owned gameplay path, second renderer, direct SAT/health manipulation, forced actors, or bypass was introduced.

## STOP

STOP triggered: **YES**. Build 0207 not produced.
