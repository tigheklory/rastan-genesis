# Andy — CHECKPOINT H19: Pickup Actor Creators + Type-4..13 Producers + Enemy-Drop Link

**Agent:** Andy · **Type:** Static RE (arcade 68000). **NO Genesis impl · NO ROM build · runtime
build counter 376, untouched.** Authoritative: `build/regions/maincpu.bin`. Durable C first.

> **Close state: PARTIAL — but with a decisive PROVEN-ABSENT result.** The A5+0x12C8 item/status
> event path is **vestigial** in the rastan world_rev1 arcade code: rec_type-12 (weapon) pickup
> actors are **never created**, event types **4..13 are never produced**, and there is **no
> enemy-death drop** through this table. The game's visible item pickups (if any) must use a
> mechanism **outside** A5+0x12C8 — the single exact open dependency.

## A. H18 starting state
H18 proved the two event tables + the A5+0x12C8 dispatcher (0x54B1E, types 0..13) + the sole known
producer 0x449B4/0x4495A (types 0/1/2/3), and left the rec_type-12 creator, the types-4..13 producer,
and the enemy-drop link open.

## B. rec_type-12 creator inventory (`h19_rec_type12_creators.tsv`)
**PROVEN ABSENT.** A full sweep of every writer of actor `+0x06` found values 1, 8, 9, 10, 11, 13,
15, 17, 18, 23-26, 27 (immediates at 0x41B3A/0x45356/0x45364/0x4565A/0x457DC/0x45AA6/0x4B2A6/0x4B3CA;
computed at 0x42406 R6-boss=23..26 and 0x45B4A=18/10) and the boss rectype table 0x444E0 =
{0e,13,14,15,10,17}. **No writer, template, seed, or the marker path 0x41362 ever sets +0x06 = 12.**
The seven `cmpib #12,a4@(6)` sites are all consumers.

## C. A5+0x12C8 complete writer inventory (`h19_12c8_writer_inventory.tsv`)
**SOLE writer = 0x449B4** (via 0x4495A). A full xref sweep of the table address (0x10D2C8) and its
record offsets found only 0x449BE (producer `lea`) and 0x54B1E (reader). No other producer exists.
0x449B4 can only ever write types 0/1/2/3.

## D. Type 4..13 producers
**ABSENT.** No producer writes an A5+0x12C8 record with type ≥ 4. The handlers 0x54F08..0x55004 are
called **only** from the 0x54B1E dispatcher (verified by xref). The COMBO handlers 0x54F08/1E/34 are
additionally reachable from the A5+0x12A8 enemy-contact jump table 0x550A8 as combat types 26/28/30 —
i.e. **enemy contact resets the combo**, not an item pickup.

## E. Pickup actor state machines (`h19_pickup_actor_roster.tsv`)
No weapon/energy pickup actor exists via this table. The only actors that produce an A5+0x12C8 event
are the pass-2 rec_type-{3,8,15,22} enemies, which emit **type 0 (HIT_AUX)** — not an item grant.

## F/G. Pickup graphics / palettes
**PENDING** — no pickup actor is proven via this path, so no base/anim/program/palette was traced and
no palette decision was created (`h19_pickup_graphics.tsv`, `h19_pickup_palettes.tsv`).
`specs/palette_decisions.json` unchanged.

## H. Fixed / map routes
0x41180/0x41362 exists but does not set rec_type and never yields rec_type-12 — **ABSENT** for the
weapon pickup.

## I. Scripted routes
0x450D8→0x45248 and the 0x453xx-0x45Bxx creators set rec_types 8/9/11/13/15/18 — **none is 12**, so
no weapon pickup is created scripted either.

## J. Creator call graph (`h19_enemy_drop_callgraph.tsv`)
The A5+0x12C8 producer 0x449B4 is a **per-frame collision manager** (SYSTEM_EVENT), not death-driven.
There is no rec_type-12 creator to enumerate callers for (it does not exist).

## K. Enemy-death drop linkage
**PROVEN ABSENT via this path.** No rec_type-12 creator exists to be called on enemy death; the
producer is per-frame, not death-triggered. (H9's "no direct fatal-path call" is now upgraded to a
positive absence for the A5+0x12C8 mechanism.)

## L. Drop eligibility / selection
**N/A** to this path (no drop occurs here). No RNG/deterministic drop selector feeds A5+0x12C8.

## M. Durable C changes
- **UPDATED SEMANTIC:** `rastan_player_items.c` — added the proven reachability finding + helper
  `rastan_item_event_type_is_producible()` (only types 0..3 are ever written; 1/2/3 need
  never-created rec_type-12 actors → in practice only type 0 occurs).
- **Coverage:** 0x449B4 note updated to "sole A5+0x12C8 producer; item path vestigial". Audit +1
  (H18 "NOT FOUND" refined to H19 "PROVEN ABSENT"). No new COMPLETE routine (the result is a proven
  negative; the reachable producer/dispatcher C already exists from H18). gcc -std=c11 PASS (103/103);
  coverage guard PASS; fidelity guard PASS.

## N. Manifest / Bestiary changes
Dashboard item rows updated to the H19 vestigial finding; `_synced_through`→H19; regenerated +
republished (artifact **Version 11**, verified online: "synced through H19", "PROVEN VESTIGIAL",
"PROVEN ABSENT via the A5+0x12C8"). **No pickup actor cards added** (none exist via this path).

## O. Exact remaining dependency (single next step)
The A5+0x12C8 table is a dead end for pickups, so the visible arcade item pickups (fire sword, axe,
shield, jewels — if present in world_rev1) must be created and consumed by a **separate mechanism**.
**Next:** identify the collectible-item actor path that is NOT the A5+0x12C8 event table — concretely,
find the code that grants the player weapon/score/energy on contact with a placed object **without**
going through 0x449B4/0x54B1E (candidate entry points: the player-vs-object overlap in the player
update loop around the weapon selector A5+0x12FA and score A5+0x013A writers that are NOT the 0x54Fxx
handlers). Start by xref-ing every writer of A5+0x12FA and A5+0x013A outside `rastan_player_items.c`.
