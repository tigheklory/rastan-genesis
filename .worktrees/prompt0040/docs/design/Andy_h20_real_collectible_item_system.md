# Andy — H20: Real Collectible-Item System (PARTIAL)

**Agent:** Andy · Static RE (arcade 68000). **No Genesis impl · no ROM build · runtime counter 377,
untouched.** Authoritative: `build/regions/maincpu.bin`.

> **Result: no live collectible-actor reward path found via the reward fields.** In world_rev1 the
> weapon-grant path is vestigial (H19), and energy is player-state + enemy-contact damage — not a
> collectible. One exact next dependency named.

## A. H19 dead-path result
A5+0x12C8 is vestigial (sole producer 0x449B4 emits only types 0/1/2/3; rec_type-12 never created;
types 4..13 never produced). H20 did not reopen it.

## B. Reward-field writer inventory (`h20_reward_field_writers.tsv`)
- **A5+0x12FA (weapon selector):** written to 2/3/4 **only** by the vestigial 0x54ED4/0x54EEA/0x54F00
  handlers; to 1 by respawn (0x504B6). **No computed/register writer exists.** So there is no live
  weapon-grant path outside the H19-proven-unreachable A5+0x12C8 route.
- **A5+0x013A (energy):** =12288 (full) by respawn/continue (0x504A2/0x51040/0x51222); +3072 by
  player-state (0x504F2, gated on `a5@(0x46)==2` at 0x50234); **drained** by the A5+0x12A8
  enemy-contact jump table 0x550A8 (0x551xx-0x554xx, per-type damage). Energy is a player gauge
  driven by state + damage, not a collectible.

## C. Real overlap consumer
The only player-vs-actor overlap that mutates reward/status is **0x449B4** (H18/H19) — enemy contact
+ the vestigial item events. No other overlap keyed on the reward fields grants a reward. **ABSENT.**

## D. Collectible storage
No dedicated collectible pool or live collectible record was found via the reward-field xref. (The
A5+0x02C8 actors that pass-2 detects emit only type-0 HIT_AUX.)

## E./F. Collectible state machine / reward writer
None proven — no collectible actor exists on the found paths.

## G./H./I. Creators / enemy-drop / fixed / scripted routes
No collectible creator identified; therefore no enemy-death drop, fixed, or scripted collectible
route (`h20_collectible_creation_routes.tsv`, `h20_collectible_drop_callgraph.tsv`). H9's
"no direct fatal-path creator" and H19's "A5+0x12C8 vestigial" now extend to: no reward-field-based
collectible grant exists at all in the code paths examined.

## J./K. Graphics / palettes
PENDING — no collectible actor proven, so no sprite/palette traced; `specs/palette_decisions.json`
unchanged (no new decision).

## L. Durable C changes
None new (the result is a proven negative on the reward-field paths). The reachable reward writers
(respawn 0x504A2, damage table 0x550A8, player-state 0x504F2) are documented here + in the TSVs; the
already-decoded event system is in `rastan_player_items.c` (H18/H19).

## M. Exact remaining dependency (single next step)
The classic Rastan weapon/shield pickups are not granted via A5+0x12FA/A5+0x013A on any live path, so
if functional collectibles exist in world_rev1 they must use an **equipment/inventory field** not yet
xref'd. **Next:** xref every writer of the player equipment/shield/state fields set at respawn
0x504A2 — specifically **A5+0x1302 (=1), A5+0x1390, A5+0x140C/0x140E/0x1410, and the player-mode
field A5+0x0046** — outside 0x504A2/0x5049A; a non-init writer of one of those is the most likely
real collectible/equipment grant. (Alternatively, world_rev1 may simply lack functional weapon
pickups — which this negative evidence already makes a live hypothesis.)
