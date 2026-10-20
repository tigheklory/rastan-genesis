# Andy — Bestiary + Palette Composer: Gameplay Items, Weapon Power-Ups, Enemy Death Families

**Date:** 2026-10-20 · **Type:** Tooling / provenance / decomp-expansion ONLY. No ROM, no build
number, no MAME, no gameplay trace, no production/runtime code change. Cody's Build 0459–0462 in-flight
work (semantic-object palette integration + its `verify_palette_families.py`) preserved and untouched.
Authority: the ORIGINAL arcade program via the EXISTING decompilation tree (H16/H18/H19/H20/H21 +
`rastan_actor_behavior.c`/`raw/`), consumed — not re-derived.

---

## CONTINUATION UPDATE (2026-10-20 part 2 — Parts A/B/C completed)

The two previously-open parts are now finished from the existing decomp (`raw/00040ccc.c` reward
transform + reward tables 0x40C2E/0x40C40; `raw/00042abc.c` specialized-death branches) plus the
compositor VM for the per-piece palette nibble (H15 rule). **No new Ghidra decompilation project; no
function redone.** The lethal-init 0x448B2 was read (sets state 0x0F → 0x40CCC) to confirm routing.

**PART A + B — visible gameplay pickup = the item-drop reward presentation (RESOLVED, was "open"):**
the visible gameplay collectible/weapon-power-up is **not** a separate marker/scripted sprite and
**not** the vestigial rec_type-12 path (PROVEN ABSENT) — it is the **family-12 reward presentation the
dying enemy transforms into** (`0x40CCC` phase-10 `0x40D32`), base **0x0A5A**, gated by schedule
`+0x36`. **17 reward kinds**, anim selector `(kind-1)+0x13` (**0x13..0x23**), **one static presentation
per kind**, in three palette-bank groups (compositor control nibble, H15): **kinds 1-4 → bank 0x30,
kinds 5-13 → bank 0x31, kinds 14-17 → bank 0x37**, each colored from the per-round pool
(`0x3BA88[round]+nibble → 0x4FD02`). Reward identity `+0x29` = `0x40C2E[kind-1]`; score `+0x2C` =
`0x40C40[kind-1]`. Scripted creators (`0x450D8→0x45248`) make **enemies** (rec_types 8/9/11/13/15/18),
never collectibles — so there is no separate collectible-sprite open dependency. Exposed as three
authorable Composer families on their REAL banks (no bank-0x30 backdrop): `object:effect.item_drop_death`
(0x30), `object:item.gameplay_reward_b31` (0x31), `object:item.gameplay_reward_b37` (0x37). Registry:
item-drop decision upgraded to **decided**; added `PAL-PC090OJ-GAMEPLAY-REWARD-B31-001` / `-B37-001`.
The item-screen items (AXE/HAMMER/FIRE SWORD/SHIELD/MANTLE/ARMATURE/MEDICINE/POISON/GOLD SHEEP/JEWEL)
are the identity reference for the 17 reward kinds (exact per-kind name mapping via `+0x29` identity is
PENDING; the graphics/palette families are proven and authorable now).

**PART C — complete death-family tool coverage:**
- **ordinary_enemy_death** (0x0A73): confirmed it is colored via the **owning enemy's** palette family
  (its cells belong to `usage:lizardman:bank0x36` etc.), so it needs **no separate editable family** —
  documented as sufficient (editing the enemy edits its death).
- **specialized_death_019d** (base 0x019D, `0x42ABC` type<8): bank **0x34**, anim 0x2A/0x2C/0x2E
  (3 frames), **reachable** (actor 0x019D observed rec_type 0/3). Exposed:
  `object:effect.specialized_death_019d` + `PAL-PC090OJ-SPECIALIZED-DEATH-019D-001`. Human identity PENDING.
- **specialized_death_09dc** (base 0x09DC, `0x42ABC` type5, +0x3D bit7): bank **0x33**, 16-phase run.
  Exposed: `object:effect.specialized_death_09dc` + `PAL-PC090OJ-SPECIALIZED-DEATH-09DC-001`. Exact
  rec_type-5 enemy identity + independent reachability confirmation PENDING.
- **transient_alt_effect** (anim 0x70-0x73, mode!=0): **NOT a standard enemy death** — reached in the
  death-state handler only for mode!=0 "hunter" (family-2 controller, base 0x033E) actors; classified
  non-death, NOT given a Composer palette family and NOT counted toward enemy-death coverage.
- **bat_death** / **generic_burst**: unchanged (preserved).

Verifier `verify_death_item_families.py` extended to **14/14 PASS**. Bestiary regenerated + republished
(Version 25). No Test.json / item-screen / production change; no colors authored by Andy. The
"collectible graphics unresolved" Bestiary frontier is now RESOLVED (it is the 0x0A5A reward family).

---

## TASK TYPE

Tooling only: **YES** · Production code changed: **NO** · ROM built: **NO** · Build number consumed:
**NO** · MAME run: **NO** · Gameplay trace: **NO**.

## ARCADE DECOMP

- Existing decomp used: **YES**. New decomp project created: **NO**. Previously decompiled functions
  redecompiled: **NO**.
- Missing functions added via Ghidra: **NONE required** — the state-0x0F death taxonomy was already
  present in the existing tree (`rastan_actor_behavior.c` `actor_armored_40ccc` 0x40CCC +
  `actor_specialized_death_42abc` 0x42ABC with `raw/00042abc.c`; `h16_burst_child_structure.json`;
  H18/H19/H20 item/drop results). No arcade function needed new decompilation.
- Existing C decomp tree expanded: **NOT NEEDED** (consumed as-is). Raw 68000 reconciled: **N/A** (the
  raw reconstructions `raw/00040ccc`, `raw/00042abc` already carry the instruction-faithful branches).
- New consolidating data file: `analysis/actor_decompilation/h25_death_and_effect_families.tsv`
  (derived entirely from the proven PCs above; no new semantics invented).

## SCROLLING ITEM SCREEN

Status: **ACCEPTED / UNCHANGED**. Graphics changed: **NO** · Palette changed: **NO** · Geometry
changed: **NO** · Generator changed: **NO**. Used as gameplay color/provenance reference: **YES**
(the item screen is PC080SN; the gameplay families here are PC090OJ sprites — different subsystem).

## GAMEPLAY ITEM DROPS / VISIBLE COLLECTIBLES (FINAL — mechanism RESOLVED)

The visible gameplay collectible/reward is the **family-12 reward presentation** the dying enemy
transforms into in place: `0x40CCC` phase-10 → `0x40D32`, base **0x0A5A**, gated by schedule field
`+0x36`. This is the proven gameplay-pickup graphics mechanism. It is **not** created by the enemy
fixed-marker (`0x41180/0x41362`) or scripted-positional (`0x450D8→0x45248`) routes — those create
**enemies** (rec_types 8/9/11/13/15/18), never collectibles — and it is **not** the `rec_type-12`
TIMED_WEAPON actor path, which remains **vestigial / NOT CREATED** (`A5+0x12C8` producer 0x449B4 only
ever writes types 0/1/2/3; H19/H20). There is therefore **no separate collectible-sprite open
dependency**.

- **Reward kinds:** **17**. Animation selector `(kind-1)+0x13` = range **0x13..0x23**; **one static
  presentation per kind**.
- **Palette-bank groups (compositor control nibble, H15 rule):** kinds **1-4 → bank 0x30**, kinds
  **5-13 → bank 0x31**, kinds **14-17 → bank 0x37**. Palette source = per-round pool
  `0x3BA88[round]+nibble → 0x4FD02`.
- **Reward identity** `+0x29` = `0x40C2E[kind-1]`; **reward score** `+0x2C` = `0x40C40[kind-1]`.
- **Accepted item-screen counterpart (reference only):** AXE/HAMMER/FIRE SWORD/SHIELD/MANTLE/ARMATURE/
  MEDICINE/POISON/GOLD SHEEP/JEWEL. The **exact kind 1..17 → human item name** mapping is **PENDING**
  through the `+0x29` identity semantics — that is the only remaining pickup problem; the graphics /
  palette mechanism is fully resolved.
- **Composer families (authorable now, on their REAL banks — no backdrop):**
  `object:effect.item_drop_death` (bank 0x30, kinds 1-4), `object:item.gameplay_reward_b31`
  (bank 0x31, kinds 5-13), `object:item.gameplay_reward_b37` (bank 0x37, kinds 14-17). Existing user
  palette changed: **NO**.

## GAMEPLAY WEAPON POWER-UPS (FINAL)

The visible ground weapon power-up is **the same family-12 reward presentation** (base 0x0A5A) — the
subset of the 17 reward kinds whose `+0x29` identity is a weapon (e.g. FIRE SWORD). It is NOT a
separate sprite and NOT the vestigial `rec_type-12` actor. So its graphics are resolved (base 0x0A5A,
anim 0x13..0x23, banks 0x30/0x31/0x37); the per-kind weapon name is part of the PENDING `+0x29` mapping.

- **Held Rastan weapon modified: NO** — the held weapon is the separate `object:weapon.{sword,axe,
  hammer,fire_sword}` family (bank 0x33) already in the Composer; it is explicitly NOT the ground
  reward pickup and was not touched (read-only provenance only).

## ENEMY DEATH COVERAGE (FINAL)

Enemies audited: the full H21 roster (Lizardman 0x004B, Chimera 0x00D0, Four-Armed 0x02E8, Valkyrie
0x0241, Horned 0x0420, family5 0x01CB, Skeleton 0x03B3, Serpent 0x0400, 0x043A, 0x06E2, 0x0889, Flying
Demon 0x0129, Small Bat 0x0268, Large Bat 0x03F6, bosses R1–R6, materialized actors).

Death is **polymorphic state 0x0F** (handlers `0x40CCC` `actor_armored_40ccc` and `0x42ABC`
`actor_specialized_death_42abc`; the lethal initializer `0x448B2` sets state 0x0F → `0x40CCC`).

| Enemy class | Death family | Base / anim | Frames | Palette bank | Composer family |
|---|---|---|---|---|---|
| Field enemies (Lizardman/Chimera/Four-Armed/Valkyrie/Horned/Skeleton/Serpent/…) | **ordinary_enemy_death** | 0x0A73, table 0x40DCE (0x0B..0x12) | 10 | owning enemy bank (0xA73 cells owned by Lizardman bank 0x36) | via the owning enemy family (no separate family needed) |
| Dying enemy when `+0x36` set (reward drop) | **item_drop_death** (reward) | 0x0A5A, anim 0x13..0x23 (17 kinds) | 1 per kind | 0x30 / 0x31 / 0x37 | item_drop_death · gameplay_reward_b31 · gameplay_reward_b37 |
| Flying Demon (types 8/9), selected bosses, projectile burst | **generic_burst** | 0x0275, 0x9D..0xA0 | 4 | 0x30 (0x04FE62) | object:effect.burst |
| Small Bat 0x0268 + Large Bat 0x03F6 (types 10/11) | **bat_death** | 0x0275, 0xA8 | 1 | 0x30 (shares burst) | object:effect.bat_death |
| actor 0x019D (rec_type 0/3, <8) | **specialized_death_019d** | 0x019D, 0x2A/0x2C/0x2E | 3 | 0x34 | object:effect.specialized_death_019d |
| rec_type-5 lethal actor (identity PENDING) | **specialized_death_09dc** | 0x09DC, seq+0xC2 | 16 | 0x33 | object:effect.specialized_death_09dc |

Bestiary linked: **YES** ("Enemy Death / Effect Families" section, data-driven from h25, with the
Composer key per family). Palette Composer linked: **YES** for every reachable death family.

## GENERIC / DEMON / BOSS BURST (preserved)

- `object:effect.burst` / `PAL-PC090OJ-ENEMY-DEATH-BURST-001` — base **0x0275** anim 0x9D..0xA0, bank
  0x30 (0x04FE62). Users: generic enemy burst, **Flying Demon death (types 8/9)**, **selected boss
  death types**, projectile burst — the SAME base 0x0275 family (`0x42ABC` default / `0x40DD8`).
- Correctly shared: YES. Not split (no new evidence to split). Existing Tighe decisions preserved:
  **YES** (`usage:burst:bank0x30` intact; no Test.json change).

## ITEM-DROP DEATH = THE REWARD PRESENTATION (FINAL — PINNED)

- Semantic keys: `PAL-PC090OJ-ENEMY-ITEM-DROP-DEATH-001` (status **decided**), + the two bank-group
  decisions `PAL-PC090OJ-GAMEPLAY-REWARD-B31-001` / `-B37-001`.
- Owner/state: state 0x0F, `0x40CCC` phase-10 **transform `0x40D32`** → family 0x0C.
- Base **0x0A5A**; **exact animation program** = selector `(kind-1)+0x13` → **0x13..0x23**;
  **frame count = 1 static presentation per kind**, **17 kinds**.
- **Reward-dependent variants: YES** — each kind has its own anim selector, palette nibble, identity
  (`0x40C2E[kind-1]`) and score (`0x40C40[kind-1]`).
- **Palette bank: 0x30 (kinds 1-4) / 0x31 (kinds 5-13) / 0x37 (kinds 14-17).** **Palette source:**
  per-round pool `0x3BA88[round]+nibble → 0x4FD02`.
- **Composer family fully authorable: YES** — rendered on the real banks (no bank-0x30 backdrop); no
  color authored by Andy.
- This IS the visible gameplay collectible (same object); it is NOT a created rec_type-12 pickup actor
  (PROVEN ABSENT) and is distinct from the generic burst (0x0275) and the ordinary death (0x0A73).

## BAT DEATH (preserved)

- `object:effect.bat_death` / `PAL-PC090OJ-BAT-DEATH-001` — base 0x0275 anim **0xA8**, **1 frame**
  (compositor VM = 1 piece), shared by **Small Bat 0x0268 + Large Bat 0x03F6** (one family), bank
  **0x30** (shares the burst palette; distinct PATTERN cell from 0x9D..0xA0).

## SPECIALIZED DEATH 0x019D

- `object:effect.specialized_death_019d` / `PAL-PC090OJ-SPECIALIZED-DEATH-019D-001` — base **0x019D**,
  `0x42ABC` type<8 branch, anim **0x2A/0x2C/0x2E**, **3 frames**, bank **0x34** (per-round pool nibble
  4). **Reachability PROVEN** — actor 0x019D observed rec_types **0 and 3** (both <8) in the
  whole-game sweep. Human actor identity **PENDING**.

## SPECIALIZED DEATH 0x09DC

- `object:effect.specialized_death_09dc` / `PAL-PC090OJ-SPECIALIZED-DEATH-09DC-001` — base **0x09DC**,
  `0x42ABC` type-5 branch (+0x3D bit7), **16 phases**, bank **0x33** (per-round pool nibble 3). The
  type-5 branch is PROVEN; the **exact rec_type-5 enemy identity and independent reachability remain
  PENDING / LIKELY** — not overstated.

## TRANSIENT ALT EFFECT (non-death)

- Base **0x033E**, anim **0x70..0x73**, reached in the death-state handler only for mode!=0
  "hunter"/controller actors (`0x40CCC` `0x40E0E`, sfx 0x17). **Classified NOT a standard enemy-death
  family**; NOT counted toward enemy-death palette coverage and given **no** Composer palette family.

## BESTIARY (FINAL)

Pickup/reward identities resolved: the **17** reward kinds (base 0x0A5A, anim 0x13..0x23, banks
0x30/0x31/0x37). Weapon power-up: resolved as the weapon subset of those kinds. Enemy death families
fully linked per family with Composer keys. Dashboard reconciled: it no longer states or implies
"visible pickups unresolved", "pickup mechanism outside the death system", "reward graphics
unidentified" or "0 proven gameplay pickup presentations"; it now shows the proven reward mechanism and
limits remaining uncertainty to the per-kind human name and the 0x09DC user identity. Second database:
**NO**. The overall Bestiary is **not** marked complete merely because this subsystem is resolved.

## PALETTE COMPOSER (FINAL)

- Gameplay reward families (authorable): `object:effect.item_drop_death` (0x30),
  `object:item.gameplay_reward_b31` (0x31), `object:item.gameplay_reward_b37` (0x37).
- Death families: `object:effect.burst`, `object:effect.bat_death`,
  `object:effect.specialized_death_019d` (0x34), `object:effect.specialized_death_09dc` (0x33);
  ordinary death colored via the owning enemy family.
- Registry: **21 decisions**. Existing Test decisions / Tighe mappings / item-screen mappings / GAME
  OVER + HUD work / Cody production integration: **unchanged**. New colors authored by Andy: **NO**.

## STATIC TOOL VERIFICATION (`verify_death_item_families.py`, 14/14 PASS)

Pickup coverage · weapon-powerup coverage · held-weapon separation · item-screen untouched ·
death-family coverage · item-drop death distinction (from burst + ordinary death) · bat death · generic
burst preservation · no semantic duplicates · Bestiary→Composer links · Test-profile preservation ·
item-drop reward on real banks 0x30/0x31/0x37 · item-drop palette PINNED (decided) · specialized deaths
0x019D (0x34) + 0x09DC (0x33) exposed · transient_alt non-death — **all PASS**. Cody's
`verify_palette_families.py` was not modified or run.

## CODY HANDOFF

Families ready for Tighe mapping: `object:effect.item_drop_death`, `object:item.gameplay_reward_b31`,
`object:item.gameplay_reward_b37`, `object:effect.bat_death`, `object:effect.specialized_death_019d`,
`object:effect.specialized_death_09dc`.

Production integration required AFTER Tighe maps: wire these families' per-object `index_map` through
the semantic-object system Cody built (`gen_reindexed_pc090oj.py` / the semantic profile), analogous to
GAME OVER/HUD, so the native gameplay emitter colors the reward/death presentations. No runtime change
by Andy.

Remaining semantic dependencies (identity only — the graphics mechanism is resolved):
1. **Reward kind 1..17 → human item name** via the `+0x29` identity table (`0x40C2E`) cross-referenced
   to the accepted item-screen identities.
2. **Specialized 0x09DC exact rec_type-5 enemy identity** + independent reachability confirmation.

Runtime changes made by Andy: **NONE**. ROM candidate needed now: **NO**; only after Tighe maps.

## ISSUES

Updated: **OPEN-006** (sprite/high-bank palette mapping) — final reward/death taxonomy, the reward
mechanism resolution, and the remaining identity-only dependencies. Closed: **NONE** (no production ROM
made/tested). Phase D: **NO**. Phase E: **NO**.

STOP.
