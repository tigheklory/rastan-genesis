# Andy — Static Sub-Round-2 Actor Decompilation

**Agent:** Andy · **Type:** Analysis (static RE) · **Build context:** rastan-direct, counter 360
(NO ROM built, NO Genesis change, NO MAME used in this pass).

## Scope

Statically identify the sub-round-2 hostile-actor architecture and roster for all six rounds from
the original arcade program (`build/regions/maincpu.bin` + Ghidra
`analysis/ghidra/rastan_arcade/exports/`). The number and identity of actors are OUTPUTS of the
decompilation, not inputs. No screenshots, cheats, MAME samples, or supplied enemy lists were used
as authority.

## What was proven (code)

### Sub-round state machine
- Round-end boundaries `0x502AC` = **{0x16, 0x2D, 0x44, 0x5B, 0x72, 0x89}** (`A5+0x1360:=1`,
  `A5+0x118` advances). Sub-round-1→2 within a round is data-driven by a `0x7E` collision tile →
  `A5+0x10E8:=7` → wipe → scene reload (R1 door proven at map col 0x0F).
- **Sub-round-2 windows derived from the field schedule** (family-2 region at round end):
  R1 `0x11–0x16`, R2 `0x28–0x2D`, R3 `0x3F–0x44`, R4 `0x56–0x5B`, R5 `0x6D–0x72`, R6 `0x7E–0x89`.
  These corroborate the earlier MAME-cheat castle_start values (±1–2), now code-grounded.

### Field schedule `0x4A104` (installer `0x4A086`) — fully decoded
`block=(0x13E−round)>>1`; 40-byte block = 5 refillable 8-byte slots (`0x49f30` picks free slot,
tracks `+0x26`, counts `+0x03==0`). Slot record →
`[class(+0x04), family(+0x3E), lo-nibble comp(+0x38)/hi-nibble variant(+0x752), +0x36,
timer(+0x1C, bit0→flag +0x2A), +0x34]`; class seeds `+0x05 = class+1`. Base via `0x4544E`
(`0x45502` var0 / `0x45562` var≠0; family-2 → `0x45494` → `0x454ba/0x454d2/0x454ea`), palette via
`0x45684` (`0x45722`). Family bases match `corrected_semantic_families.json` exactly.

### Ground-marker / char-targeted spawner (`0x41180`, `0x40baa`, `0x40a86`, `0x41d08`) — decoded
- `+0x03==0`: floor-marker follower — scans `0x10DE00` HIGH-byte markers `0x31..0x3c`; `0x40a86`
  4-byte table `(cur_state, marker, new_state, term=0xFF)` transitions `+0x05`; `0x41d26`(`0x41d08`)
  loads `+0x0D` target char.
- `+0x03!=0`: char-targeted — scans for own `+0x0D` (`0x45..0x7b`); large `0x13E`-gated dispatch
  sets state/anim/position/base. Proven direct bases: armored man `0x0A73`/`0x0A5A` (comp 2);
  `0x0275/0x00F4/0x0DAB/0x09EA`.
- Collision grid builders `0x559B2`/`0x55A14`: per-column source record, collision word from
  `@(0x14+row*8+col*2)` or `@0x22` when `@0x20==0xFF`; written to `0x10DE00`; **HIGH byte = marker**.

### Key result — the schedule does NOT list sub-round-2 hostiles directly
Every round's sub-round-2 schedule region is dominated by **family-2 (`0x033E`, comp 0/3/4, anim
`0x93`) spawner entries**; the variant advances per round-group. Direct hostile families scheduled
in sub-round-2: R1 none; R2–R4 `0x01CB` (f5); R5 `0x01CB`+`0x03B3` (f6); R6 a mix
(`0x00D0,0x01CB,0x02E8,0x03B3,0x0400,0x0889`). The visible sub-round-2 enemies (e.g. R1 armored
men) are materialized through the char-targeted path, whose marker chars live in the sub-round-2
scene's map-column data. Per-round detail in `Andy_phase2_actor_roster.md` and the manifest
`subround2_static_rosters`.

## Corrected prior claims
- Removed the universal "FIELD_SCHEDULE = outdoor only" / "GROUND_MARKER = castle" framing; these
  are mechanisms, not sub-round definitions.
- Replaced "castle" visible terminology with SUB-ROUND 1/2/BOSS in the architecture doc, roster
  doc, and bestiary headings.
- The prior "phase-2 field-schedule roster" retraction stands and is now explained by the family-2
  spawner mechanism.

## Remaining static blockers (exact next targets)
1. **Per-scene letter-marker set** → char-spawned identities. Decode
   `0x507C5[0x13E] → 0x3951C+scene*12 descriptor → column-layout long → column-record format loaded
   by 0x56128/0x561A0 → collision `@(0x14+row*8+col*2)` high byte`.
2. **`0x033E` family-2 semantic role** — decode its update routine + compositor program (anim
   `0x93`): visible enemy vs child-spawner.
3. Human names for families `0x00D0/0x01CB/0x02E8/0x0420/0x03B3/0x043A/0x0241/0x06E2/0x0889/0x0400`.

## Artifacts produced
- `tools/analysis/decode_field_schedule.py` (durable offline decoder).
- `analysis/actor_subround2/field_schedule_decode.txt`, `.../subround2_schedule_rosters.json`.
- Updated: `Andy_actor_system_architecture.md`, `Andy_phase2_actor_roster.md`,
  `rastan_actor_graphics_manifest.json` (`enemy_creation_systems`, `phase_partition`,
  `subround2_static_rosters`), regenerated `rastan_actor_bestiary.html`.

## Tool reuse
Existing project tools reused: Ghidra exports (`decompiler_export.c`), `build/maincpu.disasm.txt`,
existing lexicon (`corrected_semantic_families.json` for family↔base cross-check).
New tooling created: `tools/analysis/decode_field_schedule.py` (durable, project-owned offline
ROM-table decoder; no equivalent existed). Why necessary: to enumerate the 0x4A104 schedule per
`0x13E`/round statically. No MAME/trace tooling created or used.

## STOP status
Analysis complete for the schedule-level sub-round-2 model. The exact char-spawned per-scene roster
is bounded by blocker (1) above and is the next static task. No ROM/Genesis/build changes.
