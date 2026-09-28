# Andy — CHECKPOINT H18: Item / Power-Up System + Enemy-Drop Link (PARTIAL)

**Agent:** Andy · **Type:** Static RE (arcade 68000). **NO Genesis impl · NO ROM build · runtime
build counter 376, untouched.** Authoritative: `build/regions/maincpu.bin`. Durable C first.

> **Close state: PARTIAL.** The player item/status **effect architecture is fully proven** — both
> collision-event tables, the A5+0x12C8 dispatcher, all 14 effect types, and the type-0/1/2/3
> producer. The **pickup-actor graphics/creator and the energy/life (types 4–13) producer + the
> enemy-death drop link remain open.** No pickup identities were fabricated; no bestiary item cards
> were added.

## A. H9 starting gap
H9 proved the fatal chain (hit → state 0x0F → 0x44804 → score 0x3B726 → retire 0x4092E) but found
**no drop creator on that forward path**. H18 deliberately did not repeat that walk.

## B. Cody post-H9 evidence reconciliation (§21)
- A5+0x12C8 is a real 4×8-byte {active,type,X,Y} event list — **CONFIRMED IN ARCADE STATIC CODE**.
- 0x54A2C dispatches an event table — **REFINED**: 0x54A2C scans **A5+0x12A8** (enemy-contact damage,
  jump table 0x550A8); the **A5+0x12C8** item/status scan+dispatch is the sibling **0x54B1E**.
- type 0 → 0x5506C — **CONFIRMED** (activates auxiliary A5+0x1296; a hit event, not an item).
- types 1..3 → melee grants (0x54EF2/0x54EDC/0x54EC6) — **CONFIRMED** (selector A5+0x12FA=4/2/3; FIRE=4).
- 0x54EF2 grants FIRE; 0x54DD2 owns FIRE/timed-weapon expiry — **CONFIRMED**.

## C. 0x54B1E complete dispatcher (A5+0x12C8, types 0..13)
4 records; active==1 → dispatch by type. Full effect classes in
`analysis/actor_decompilation/h18_item_effect_dispatch.tsv` (raw/00054b1e.c):
0=HIT_AUX(0x5506C); 1/2/3=TIMED_WEAPON(A5+0x12FA=4/2/3, timer A5+0x1326, expiry 0x54DD2);
4-7=COMBO_STATE(A5+0x1388=0..3); 8=LIFE(A5+0x110A/0x1108/0x1390/0x140E);
9/10=ENERGY_RESTORE(A5+0x013A += 0x400/0x800); 13=ENERGY_SET(A5+0x013A=0x3000);
11/12=ENERGY_DRAIN(A5+0x013A -= 0x100/0x200, defense A5+0x1366).

## D. Event-table producers (`h18_item_event_producers.tsv`)
Collision manager **0x449B4** clears both tables, then 3 passes over actor pool A5+0x02C8:
pass1 (mode-0 enemies) → A5+0x12A8 damage (type=actor+0x29); pass2 (rec_type {3,8,15,22}) and
pass3 (family+0x3E==12 && rec_type+0x06==12) → A5+0x12C8 via overlap (0x44C5A/0x44CBA) + type via
**0x4495A**: rec_type-12 pickup → type 1/2/3 (+0x25 selects), else type 0. **Producer of types
4–13 (energy/life) is NOT REACHED in this pass** — the open dependency.

## E. Pickup actor pool / state machine
The weapon pickups are **rec_type-12 (family-12) actors in the ordinary pool A5+0x02C8** (not a
dedicated pool). They emit weapon types 1/2/3 on player overlap. Their state/motion/creator and
graphics were NOT traced this pass (`h18_pickup_actor_records.tsv`, PARTIAL).

## F. Pickup creators (`h18_item_creation_routes.tsv`)
Marker (0x41180/0x41362) and scripted (0x450D8→0x45248) mechanisms exist; whether a rec_type-12
pickup is produced by either — or dropped on enemy kill — is not yet confirmed. **NOT collapsed.**

## G. Enemy-death drop linkage (`h18_enemy_drop_link.tsv`)
CONFIRMED: no direct creator call on the fatal path (H9). **NOT FOUND**: a rec_type-12 pickup
creator whose callers originate from enemy death/retirement. Not claimed absent — just not yet
traced. This is the central H18 question, still open.

## H. Fixed vs scripted vs drop routes
Kept as three separate categories in the TSVs; none yet resolved to the rec_type-12 pickup actor.

## I. Item graphics
Not resolved — the rec_type-12 pickup's base/anim/selector were not traced, so no legal sprite was
reconstructed. (No screenshots/wiki used, per rules.)

## J. Item effects
Fully classified technically (§C). Human names left PENDING except a PROPOSED "Fire Sword pickup"
for the type-1 (selector-4) weapon grant (`h18_pickup_effects.tsv`).

## K. Palette-decision IDs / provenance
No pickup graphics proven → **no palette decision created or cited**; `specs/palette_decisions.json`
unchanged. `h18_item_palette_instances.tsv` = PENDING. (No palette mapping duplicated in this report,
per RULES.md line 335 / CLAUDE.md registry rule.)

## L. Durable C additions
- **NEW RAW:** `raw/00054b1e.c` (A5+0x12C8 dispatcher + type-0 and types-4..13 handlers),
  `raw/0004495a.c` (actor→event-type).
- **NEW SEMANTIC:** `rastan_player_items.c` (effect-class model + producer overview).
- **REUSED (not duplicated):** weapon types 1/2/3 (0x54EF2/0x54EDC/0x54EC6) + expiry 0x54DD2 in
  `rastan_player_weapon_state.c` (Cody build0368/0372).
- Coverage +8 COMPLETE; audit +1; gcc -std=c11 PASS (103/103); coverage guard PASS; fidelity PASS.

## M. Manifest / Bestiary changes
Dashboard item rows updated to the proven effect-architecture status; `_synced_through`→H18;
regenerated + republished (artifact Version 10, verified online). **No pickup actor cards added**
(none proven — honest PARTIAL).

## N. Exact remaining dependency (single next step)
**Find the writer of A5+0x12C8 records with type ≥ 4** (energy/life/combo pickups) — i.e. the
producer sibling to 0x449B4 pass 2/3 that sets `rec[+2] >= 4` — and the **creator of rec_type-12
pickup actors** whose callers reveal the enemy-death drop link. Concretely: enumerate all writers of
`A5+0x12C8` records beyond 0x449B4, and all creators that set actor `+0x06 (rec_type)=12` in pool
A5+0x02C8, then trace their callers back to enemy death/retirement.
