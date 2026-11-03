# Cody - Lizard-Man Acceptance Completion Attempt

**Date:** 2026-07-19  
**Type:** Acceptance completion attempt / runtime evidence + static analysis, STOP before implementation  
**Build context:** Build 0206/256, `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`  
**Build 0206 SHA256:** `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`  
**Scope requested:** complete lizard-man visual and combat acceptance and produce Build 0207 only if the shared enemy palette route, reported 8-pixel lizard alignment error, and lizard-to-Rastan damage failure can be fixed through proven arcade-faithful boundaries.  
**Outcome:** STOP. Build 0207 was not produced.

Address labels: `arcade_pc` and `runtime_genesis_pc` are code addresses mapped through `build/rastan-direct/address_map.json`; `arcade_WRAM` is original arcade work RAM; `Genesis-WRAM` is Genesis work RAM; PC090OJ means the arcade sprite/object hardware contract translated through the Genesis mirror/candidate/SAT pipeline.

## Phase 0

Classification: **EXTENDING**. This continues KF-064/KF-065 and OPEN-017/OPEN-024 after Build 0206. The arcade code remains the program; Genesis code may only translate hardware intent through helper/opcode-replacement paths and must not force actors, PC090OJ records, SAT entries, collision overlap, hurt state, or health loss.

Priors read: `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `CURRENT_STATE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest relevant `AGENTS_LOG.md`, and the recent lizard evidence/implementation notes:

- `docs/design/Cody_lizard_visual_combat_acceptance_fix.md`
- `docs/design/Cody_lizard_actor_activation_progression_fix.md`
- `docs/design/Cody_lizard_b5_activation_writer_provenance.md`

Relevant priors:

- KF-064: the first visible Stage-1 lizard men are actor block `A5+0x02C8` composite records ~140..229, not record 46.
- KF-065: Build 0206 restores natural activation progression for multiple lizard actors by correcting the collision-buffer upper bound at `runtime_genesis_pc 0x000414CC`; remaining palette, visual-Y, and combat acceptance are separate.
- KF-063: PC090OJ expansion must remain actor/producer faithful; no forced records/SAT.
- KF-043/KF-046: palette-line routing and route-table ownership are existing shared mechanisms.
- KF-058: player HP/control context; HP is `A5+0x013A`, initialized to `0x3000`, with death check at `arcade_pc 0x000517E6` / `runtime_genesis_pc 0x000519E6`.

Rediscovery Hazard HIGH findings touched: KF-064/KF-065 and related PC090OJ ownership/staging findings. Contradiction of CONFIRMED/STRONG finding: **NONE**.

## Baseline

- Branch: `rastan-direct-proposal`.
- Current HEAD while this task ran: `1c63bf6`.
- Counter before task: `206`.
- Build 0206 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`.
- Build 0206 SHA256: `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`.
- Build 0206 size: `1,583,440` bytes.
- opcode_replace count: `215`.
- total_genesis_bytes_covered: `0x182950`.
- Build 0207 produced: **NO**.

## Evidence Artifacts

Trace directory:

`states/traces/lizard_acceptance_completion_20260719_002717/`

Key files:

- `pc090oj_observed_index_usage.json` - PC090OJ pixel-index usage audit from observed Build 0206 player/lizard records.
- `lizard0207_exec_damage_trace.lua` - attempted MAME Lua execution-tap damage trace; execute taps were unavailable in this MAME build.
- `lizard0207_drive_summary.lua` - frame/field sampler used with native debugger breakpoint scripts.
- `arcade_damage_bp.cmd`, `genesis0206_damage_bp.cmd` - native MAME debugger breakpoint scripts.
- `arcade_bpqt2_debug.log`, `genesis0206_bpqt2_debug.log` - native debugger logs captured with `-debugger qt -debuglog`.
- `arcade_bpqt2_events_only.log`, `genesis0206_bpqt2_events_only.log` - reduced event-only debugger logs.
- `arcade_bpqt2_nativebp_frames.csv`, `genesis0206_bpqt2_nativebp_frames.csv` - per-frame field summaries.
- `lizard_acceptance_completion_reduced.md`, `lizard_acceptance_completion_reduced.json` - reduced runtime summary.

Test environments:

- Original arcade MAME `rastan` / Rastan World Rev 1, used as authoritative original behavior.
- Genesis Build 0206 MAME, SHA above.
- Genesis Build 0207 MAME: **not run**, because Build 0207 was not produced.

## JSON Address Mappings Used

All paired code addresses below were resolved through segment containment in `build/rastan-direct/address_map.json`, not by offset arithmetic:

| arcade_pc | runtime_genesis_pc | Kind | Use |
|---:|---:|---|---|
| `0x000412CC` | `0x000414CC` | `patched_site` | Build 0206 collision-buffer upper-bound fix |
| `0x00041320` | `0x00041520` | `arcade_copy` | actor `b5` activation writer |
| `0x000504A2` | `0x000506A2` | `arcade_copy` | player HP init |
| `0x0005133A` | `0x0005153A` | `arcade_copy` | caller of player hurt/damage progression |
| `0x000517E6` | `0x000519E6` | `arcade_copy` | player HP death check |
| `0x000517EE` | `0x000519EE` | `arcade_copy` | player death-mode write candidate |
| `0x0005194A` | `0x00051B4A` | `arcade_copy` | player hurt/damage progression entry |
| `0x000519AC` | `0x00051BAC` | `arcade_copy` | HP subtract in hurt/damage progression |
| `0x00054EA0` | `0x000550A0` | `arcade_copy` | alternate static HP decrement candidate |
| `0x00054EBE` | `0x000550BE` | `arcade_copy` | mode write candidate |
| `0x00054FA4` | `0x000551A4` | `arcade_copy` | alternate static HP decrement candidate |
| `0x00054FBC` | `0x000551BC` | `arcade_copy` | alternate static HP decrement candidate |

## Objective A - Shared Enemy Palette Routing

Static source facts:

- `palette_route_lookup` and `palette_route_table` exist in `apps/rastan-direct/src/palette_hooks.s:48` and `:64`.
- Gameplay route rows currently include PC080SN FG bank 3 to line 1, PC080SN BG bank 48 to line 2, PC090OJ bank 51 to line 3, and HUD bank 0 to line 0 (`palette_hooks.s:49-54`).
- PC090OJ placement does not call `palette_route_lookup`. `.Lpc090oj_place_record_in_slot` derives effective arcade bank and only special-cases `0x30 -> line 2` and `0x33 -> line 3`; every other bank falls through `(bank >> 4) & 3` (`pc090oj_hooks.s:1784-1808`).
- Build 0206 lizard tuples use effective PC090OJ bank `0x36`, so current code routes them to Genesis line 3 by fallback, colliding with the established player/Rastan line.

Observed pixel-index audit from `pc090oj_observed_index_usage.json`:

- Rastan player records 120..137, bank `0x33`, line 3: observed nonzero pixel indices `1..15`.
- Lizard records 140..238, bank `0x36`, line 3 by current fallback: observed nonzero pixel indices `1..12`.
- Record 46 and hurry-up/bat-class evidence were not present in this pixel-index sample.
- No safe carrier line was proven for bank `0x36`. Line 3 specifically cannot safely carry both current Rastan bank `0x33` and lizard bank `0x36` by only filling unused entries because Rastan already uses all nonzero indices `1..15`.

Verdict: **not implementation-safe in this task**. The correct direction is still shared PC090OJ palette routing through the existing route-table mechanism or a justified extension, but the current evidence does not prove a safe CRAM carrier/remap for bank `0x36` without corrupting existing owners. A per-lizard or per-record palette constant would violate the task.

## Objective B - 8-Pixel Lizard Alignment

Current implementation facts:

- PC090OJ sprite Y alignment uses `PC090OJ_TO_GENESIS_Y_OFFSET = -8` (`pc090oj_hooks.s:155`).
- Decode applies the same display-origin alignment used to align sprites with the background (`pc090oj_hooks.s:1480-1484`).

Evidence status:

- Tighe's direct Sega Nomad Build 0206 observation reports lizards appear about 8 pixels too low.
- The prior MAME tuple/sample evidence did not reproduce a safe patch boundary: sampled lizard final screen Y aligned after the existing `-8` conversion, and the prior STOP document already warned that a global or lizard-specific offset was not justified from those samples.
- This continuation did not obtain a pixel-level arcade-vs-Genesis MAME measurement tying the visible feet/ground mismatch to a specific origin, height, bias, or clipping instruction.

Verdict: **not implementation-safe in this task**. The rendered alignment discrepancy remains a user-reported visual issue, but it is not safely tied to a general code boundary. No arbitrary global offset, record-range offset, or per-component adjustment is allowed.

## Objective C - Lizard Attack Damage

Native debugger breakpoint evidence produced the strongest new result in this continuation.

Original arcade MAME:

- Event lines: `2031`.
- `HP_SUB_519AC`: `112` hits.
- `HP_DEATH_CHECK_517E6`: `1913` hits.
- `HP_INIT_504A2`: `3` hits.
- HP values observed across the run: `0000, 0400, 0800, 0C00, 1000, 1400, 1800, 1C00, 2000, 2400, 2C00, 3000, FF00`.
- First visible lizard frame: frame `375`, HP `3000`, first lizard `rec=220 code=0066 x=299 y=196`.
- First frame with visible lizard and changed HP: frame `645`, HP `2400`, first lizard `rec=190 code=006D x=234 y=122`.
- Representative breakpoint path: `arcade_pc 0x000519AC` is the HP subtract instruction `subi.w #0x0100,%a5@(314)` inside the hurt/damage progression routine at `0x5194A`.

Genesis Build 0206 MAME:

- Event lines: `870`.
- `HP_DEATH_CHECK_519E6`: `868` hits.
- `HP_INIT_506A2`: `1` hit.
- `HP_SUB_51BAC`: `0` hits.
- Alternate static HP candidates `0x550A0`, `0x551A4`, and `0x551BC`: `0` hits in the captured window.
- HP values observed across the run: `0000, 3000` only.
- First visible lizard frame: frame `550`, HP `3000`, first lizard `rec=220 code=0066 x=318 y=202`.
- First valid actor count >=4: frame `1035`, HP `3000`, first lizard `rec=200 code=0066 x=151 y=122`.
- Last sampled frame `2600`: HP still `3000`, valid actors `4`, visible lizards `32`, represented/active count `49`.

Static local flow:

- `arcade_pc 0x0005133A` calls `arcade_pc 0x0005194A` only when `A5+0x10E8 == 8`; its Genesis counterpart is `runtime_genesis_pc 0x0005153A -> 0x00051B4A`.
- `0x5194A` / `0x51B4A` is a hurt/damage progression routine controlled by `A5+0x12F4`; unless the counter is exactly `56`, it advances the counter and subtracts HP at `0x519AC` / `0x51BAC`.
- Original arcade reaches the HP subtract routine during the driven lizard/contact run. Genesis Build 0206 does not reach the mapped HP subtract routine in the same driven visible-lizard window.

First exact divergence proven:

- **Proven:** original arcade reaches `arcade_pc 0x000519AC`; Genesis Build 0206 does not reach mapped `runtime_genesis_pc 0x00051BAC` while lizards are visible and actor state is populated.
- **Not yet proven:** which upstream collision/contact/hurt-state branch should set `A5+0x10E8 == 8` or otherwise call `runtime_genesis_pc 0x00051B4A` in Genesis and why it does not.

Verdict: **combat root is narrowed but not safely fixable**. A direct HP decrement, forced hurt state, forced overlap, or synthetic damage trigger would violate the architecture and task constraints.

## STOP Decision

Build 0207 was not produced because the requested acceptance task required all three corrections, and each still lacks a safe implementation boundary:

- Palette: bank `0x36` line-3 collision is proven, but no safe carrier/remap is proven for shared enemy palettes without owner corruption.
- Vertical alignment: reported 8-pixel error was not reproduced/tied to an exact general code boundary.
- Combat: original arcade reaches the natural damage subtract routine, Genesis does not; the first divergence is one call-level upstream of the HP subtract, not yet the exact patch boundary.

## Recommended Next Narrow Tasks

1. Palette route design/evidence: prove a safe shared PC090OJ enemy bank `0x36` carrier or index remap using full owner coverage for HUD, BG, FG, Rastan, lizard, bats, and record46 before implementation.
2. Combat backtrack: place native breakpoints around `runtime_genesis_pc 0x00051532..0x0005153A` and `0x00051B4A`, with fields `A5+0x10E8`, `A5+0x10D0`, `A5+0x12F4`, HP, player/lizard positions, and collision flags, comparing against original arcade `0x51332..0x5133A` / `0x5194A`.
3. Visual-Y proof: capture pixel-level original arcade MAME vs Genesis Build 0206 MAME feet/ground rows before changing `PC090OJ_TO_GENESIS_Y_OFFSET` or clipping/origin math.

## Non-Actions

No source, spec, tool, Makefile, invariant, ROM, or build artifact changes were made for Build 0207. No actor, record, SAT, collision, HP, or hurt-state forcing was performed. Build 0207 does not exist from this task.

Explicitly deferred: rolling black bar/display instability, HUD suppression, white-only HUD, window HUD, hurry-up bat timing/combat, record 132, FG layout, sky, HUD layout, D00298, continue, game-over.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017 and OPEN-024; OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issue ledgers edited: NO.
- Issues intentionally deferred: black bar/VBlank/display instability, record 132, bat timing/combat, FG/sky/HUD/D00298/continue/game-over.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. The combat path is narrowed, and the palette conflict is evidence-backed, but no durable new fix mechanism or accepted Build 0207 behavior exists yet. KF-064/KF-065 remain the active priors.

## Architecture Compliance

CONFIRMED. This task remained evidence/analysis only after STOP. No forced actors, no direct SAT injection, no HP/hurt manipulation, no second renderer, no per-enemy constants, no Genesis-owned gameplay control flow, and no bypass/stability patch were introduced.

## STOP

STOP triggered: **YES**. The first exact combat divergence is proven, but the safe implementation boundary for Build 0207 is not; palette carrier/remap and visual-Y boundaries are also not safely proven.
