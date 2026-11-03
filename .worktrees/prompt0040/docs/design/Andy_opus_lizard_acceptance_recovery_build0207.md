# Andy/Opus - Lizard Acceptance Recovery and Build 0207

## Emergency Correction - 2026-07-19

This document's original Build 0207 artifact/numbering statements were
incorrect. Per Tighe's correction and the emergency recovery audit in
`docs/design/Cody_emergency_build0207_artifact_recovery.md`, Build 0207 is
treated as **produced/consumed and then deleted/lost**, not as an available
number. The on-disk recovery search did not locate
`dist/rastan-direct/rastan_direct_video_test_build_0207.bin`, and the rolling
ROM currently hashes byte-identical to Build 0206. The authoritative build
counter is now `207`, so the next ROM-producing build must be Build 0208.

All statements below saying "Build 0207 was not produced", "counter remains
206", or equivalent are superseded by this correction. The evidence analysis
content remains historical context, but it must not be used to justify reusing
Build number 0207.

**Date:** 2026-07-19
**Type:** Evidence / implementation safety gate
**Build context:** Build 0206 accepted; Build 0207 number consumed, artifact lost
**Build 0206 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`
**Build 0206 SHA256:** `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`
**Counter after emergency correction:** `207`
**Scope:** Recover lizard acceptance only if palette and combat boundaries are safe. No forced actors, records, SAT entries, collision overlap, hurt state, HP loss, or lizard-specific damage rule.

## Phase 0

Classification: **EXTENDING**. This continues KF-064/KF-065 and the Build 0206 lizard activation progression work. Relevant priors read: `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `CURRENT_STATE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_lizard_visual_combat_acceptance_fix.md`, `docs/design/Cody_lizard_acceptance_completion.md`, and `docs/design/Cody_lizard_actor_activation_progression_fix.md`.

Relevant priors:

- KF-043 / KF-046: PC090OJ sprite representation and VBlank/SAT ownership remain Genesis helper responsibilities.
- KF-064 / KF-065: lizard actor activation/progression and PC090OJ representation are active known boundaries; Build 0206 restored the actor progression path for entries `4..7`.
- OPEN-017 / OPEN-024 remain active; OPEN-001 is context.

Rediscovery Hazard HIGH findings touched: PC090OJ sprite path, lizard actor activation, VBlank/SAT ownership. None contradicted.

Contradiction of CONFIRMED/STRONG finding: **NONE**.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. This task did not force actor state, direct HP damage, fabricated overlap, SAT records, or a second renderer.

## Evidence Artifacts

Trace directory:

- `states/traces/lizard_acceptance_recovery_20260719_111945/`

Primary files:

- `arcade_combat_backtrack.cmd`
- `genesis0206_combat_backtrack.cmd`
- `arcade_debug.log`
- `arcade_events_only.log`
- `arcade_nativebp_frames.csv`
- `genesis0206_debug.log`
- `genesis0206_events_only.log`
- `genesis0206_nativebp_frames.csv`
- `arcade_mode_watch.cmd`
- `genesis0206_mode_watch.cmd`
- `arcade_mode_debug.log`
- `arcade_mode_events_only.log`
- `arcade_mode_nativebp_frames.csv`
- `genesis0206_mode_debug.log`
- `genesis0206_mode_events_only.log`
- `genesis0206_mode_nativebp_frames.csv`
- `lizard0207_drive_summary.lua`

All four MAME runs completed with exit status `0`.

## Address Mapping Discipline

All arcade-to-Genesis code pairings below were resolved through `build/rastan-direct/address_map.json`, not by treating `+0x200` arithmetic as authority.

| arcade_pc | runtime_genesis_pc | Mapping kind |
|---:|---:|---|
| `0x00051332` | `0x00051532` | `arcade_copy` |
| `0x0005133A` | `0x0005153A` | `arcade_copy` |
| `0x000517E6` | `0x000519E6` | `arcade_copy` |
| `0x000517EE` | `0x000519EE` | `arcade_copy` |
| `0x0005194A` | `0x00051B4A` | `arcade_copy` |
| `0x000519AC` | `0x00051BAC` | `arcade_copy` |
| `0x00052064` | `0x00052264` | `arcade_copy` |
| `0x000524E8` | `0x000526E8` | `arcade_copy` |
| `0x00052712` | `0x00052912` | `arcade_copy` |
| `0x00052730` | `0x00052930` | `arcade_copy` |

## Baseline Observations

Original arcade MAME `rastan` and Genesis Build 0206 were compared with the same driver script family. The goal was not to prove general gameplay parity, only to recover the lizard acceptance boundary safely enough to justify Build 0207.

Final run summaries:

- Arcade: frame `2600`, HP `0x2400`, mode `0x0000`, move `0x0084`, valid actors `4`, visible lizards `34`, first record-190 code `0x006D`, x `234`, y `122`.
- Genesis Build 0206: frame `2600`, HP `0x3000`, mode `0x0000`, move `0x0000`, valid actors `4`, visible lizards `32`, represented `49`, active `49`.

Interpretation:

- Build 0206 is still good for natural lizard actor population and PC090OJ representation.
- Build 0206 does not show the natural lizard-to-Rastan HP/damage path in the captured run.
- The Genesis test drive also differs in player progression/contact: late gate samples show player x around `0x007F` with HP still `0x3000`, while the arcade path reaches damage-mode samples with player x around `0x00A0`.

## Combat Trace

Local gate flow:

```asm
; arcade_pc
5132a: bsrw 0x515b6
5132e: bsrw 0x51600
51332: cmpiw #8,%a5@(4328)
51338: bnes 0x51342
5133a: bsrw 0x5194a
5133e: braw 0x51514

; runtime_genesis_pc
5152a: bsrw 0x517b6
5152e: bsrw 0x51800
51532: cmpiw #8,%a5@(4328)
51538: bnes 0x51542
5153a: bsrw 0x51b4a
5153e: braw 0x51714
```

Mode-8 writer reached in original arcade:

```asm
; arcade_pc
517e6: cmpi.w #0,%a5@(314)
517ec: bhis 0x517f8
517ee: move.w #8,%a5@(4328)
517f4: clr.w %a5@(4852)
517f8: rts

; runtime_genesis_pc
519e6: cmpi.w #0,%a5@(314)
519ec: bhis 0x519f8
519ee: move.w #8,%a5@(4328)
519f4: clr.w %a5@(4852)
519f8: rts
```

Debugger watchpoint post-PC `0x0517F4` corresponds to the arcade write instruction at `arcade_pc 0x000517EE`. The mapped Genesis post-PC would be `0x0519F4`, but it was not observed.

Event counts:

| Event | Arcade | Genesis Build 0206 |
|---|---:|---:|
| Gate compare (`0x51332` / `0x51532`) | `2027` | `868` |
| Hurt call (`0x5133A` / `0x5153A`) | `114` | `0` |
| Hurt entry (`0x5194A` / `0x51B4A`) | `114` | `0` |
| HP subtract (`0x519AC` / `0x51BAC`) | `112` | `0` |

Mode watchpoint totals:

| Metric | Arcade | Genesis Build 0206 |
|---|---:|---:|
| `A5+0x10E8` watchpoint hits | `3835` | `1739` |
| Post-value `0x0000` | `2464` | `1085` |
| Post-value `0x0001` | `1090` | `444` |
| Post-value `0x0003` | `279` | `209` |
| Post-value `0x0008` | `2` | `0` |

Concrete arcade damage evidence:

- `EVENT WP_MODE_10D0E8 ... pc=0517F4 ... data=00000008 post=0001 hp=0000 ...`
- `EVENT GATE_CMP_51332 ... mode=0008 ...`
- `EVENT HP_SUB_519AC ... pc=0519AE ... mode=0008 ...`

Concrete Genesis non-damage evidence:

- Genesis Build 0206 repeatedly reaches the mapped gate compare at `runtime_genesis_pc 0x00051532`.
- Genesis Build 0206 never reaches `runtime_genesis_pc 0x0005153A`, `0x00051B4A`, `0x00051BAC`, or the mapped mode-8 writer `0x000519EE` in the captured run.
- Genesis Build 0206 HP remains `0x3000` through the run.

## Combat Classification

The trace did **not** stop at the old `A5+0x10E8` gate. It traced backward and found a downstream arcade writer that can set `A5+0x10E8` to `8`:

- `arcade_pc 0x000517EE`: `move.w #8,%a5@(4328)`
- `runtime_genesis_pc 0x000519EE`: mapped counterpart

That instruction is **not** a safe implementation target. It is guarded by a prior HP/state test:

- `cmpi.w #0,%a5@(314)`
- `bhis 0x517f8` / `0x519f8`

Forcing this writer or seeding `A5+0x10E8` would force gameplay/hurt/death state instead of restoring the missing causality. That violates the prompt and the project state-causality rule.

First exact divergence currently proven:

- Original arcade reaches the natural mode-8/hurt/HP-subtract chain.
- Genesis Build 0206 reaches populated visible lizards but does not reach the mapped mode-8/hurt/HP-subtract chain.
- The missing state creator is upstream of `runtime_genesis_pc 0x000519EE` and `0x00051BAC`, likely in the contact/damage condition that should make HP/state enter this path. It is not yet patch-safe.

## Palette Boundary

Palette fix was inspected but not safely accepted in this evidence pass. Build
0207's number is now treated as consumed/lost, so any future implementation
must use Build 0208 or later.

Current known palette boundary:

- Build 0206 lizard PC090OJ effective bank is `0x36`.
- `.Lpc090oj_place_record_in_slot` special-cases bank `0x30 -> line 2` and bank `0x33 -> line 3`.
- Other banks fall through to `(bank >> 4) & 3`, so bank `0x36` currently selects Genesis line 3.
- Current route table has PC090OJ bank `0x33` only.
- Prompt-authorized route remains plausible: suppress gameplay HUD sprite representation to free line 0, route PC090OJ bank `0x36` through the shared palette routing table to line 0, and stage converted arcade bank 36 into CRAM line 0.

No source change was made:

- No `RASTAN_GAMEPLAY_HUD_SPRITES` option was added.
- No bank `0x36` route row was added.
- No PC090OJ placement logic was changed.
- No CRAM line 0 bank-36 staging was added.

## Y Alignment Boundary

Tighe's Nomad observation that lizards appear around 8 pixels low remains recorded, but this task did not produce a safe pixel-level correction boundary.

No Y-origin correction was implemented. Unresolved Y alignment alone would not
have blocked the requested acceptance work, but Build 0207 is no longer an
available build number.

## Non-Actions

Original note said no source, spec, tool, Makefile, invariant, ROM, or build
artifact was intentionally modified and no Build 0207 release was invoked or
produced. That artifact/numbering claim is superseded: Tighe reports Build
0207 was produced and then deleted/lost. The emergency recovery audit found no
recoverable numbered Build 0207 ROM in the workspace. No actors, records, SAT
entries, collision overlap, hurt state, HP loss, or lizard-specific damage rule
were proven as an accepted fix from the available evidence.

## Recommended Next Boundary

The smallest safe next step is another narrow combat causality trace, not an implementation:

- Trace the state creator upstream of `runtime_genesis_pc 0x000519EE` / `0x00051BAC`.
- Focus on why original arcade enters mode `8` and the Genesis run does not, using matched player/lizard contact samples.
- Capture `A5+0x013A`, `A5+0x10E8`, `A5+0x12F4`, HP, player position, lizard position, and the branch condition leading to `0x519EE`.

Palette bank `0x36` route remains a separate patch candidate, but should be implemented with a full line-owner proof or after combat is no longer blocking acceptance.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024; OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: palette bank `0x36`, gameplay HUD suppression, bat colors, lizard Y alignment, black bar/VBlank/display instability, stale record 132, FG/sky/HUD, D00298, continue/game-over.

Issue ledgers were not edited by the original task because it did not produce
an accepted Build 0207 implementation or a new durable mechanism suitable for
canonicalization. Later emergency correction records Build 0207 as consumed
and lost.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. KF-064/KF-065 remain active priors. This
task extends the evidence trail but does not provide an accepted Build 0207
fix or a complete new mechanism. Build 0207's artifact is lost and its number
is consumed.

## STOP

STOP triggered: **YES**.

Original STOP text said Build 0207 was **not** produced. That statement is
superseded by the emergency correction: Build 0207 is treated as
produced/consumed and then deleted/lost. The combat path was traced past the
prior `A5+0x10E8` gate to the downstream mode-8 writer, but that writer is
guarded by gameplay state and is not a safe correction target. A forced write
would violate architecture and state causality.
