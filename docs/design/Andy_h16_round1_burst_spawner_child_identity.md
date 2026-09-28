# Andy — CHECKPOINT H16: Round-1 0x1B Burst-Spawner Child Identity

**Agent:** Andy · **Type:** Static RE (arcade). **NO Genesis impl · NO ROM build · NO MAME ·
runtime build counter 373, unchanged.** Authoritative: `build/maincpu.disasm.txt`.

> **Result:** The Round-1 marker-0x4D → state-0x1B route is a **burst CONTROLLER**, and the
> "five children" are **up to five independent TRANSIENT burst/impact EFFECTS** — not five enemy
> species, not one composite. Their visible identity is **assigned by state 0x0F** (base 0x0275,
> expanding, self-retiring), **not inherited** from the preloaded pool slot. §0 stale H15
> status text is corrected.

Bookkeeping (§0): `architecture_status._synced_through` → **H15**; the stale
"exact per-round instance PENDING" / "per-round placement of the materialized cast" lines are
replaced; bestiary regenerated, verified free of "synced through H14" and those strings.

## A. H14/H15 starting point

H14 established 0x43ECC (state 0x1B) as a burst controller that (after a timer + X gate) sets
`a5@0x286=5` and calls 0x43F4E over the A5+0x3C8 pool; children reach state 0x0F via 0x447F0/0x448B2
with `+0x39=1` and sfx 0x10; child base/anim were left PENDING. H15 proved the display-palette rule
(`+0x27` bit6 clear → compositor control nibble).

## B. A5+0x3C8 block ownership

`A5+0x3C8..A5+0x4C8` is a **shared 5-slot × 0x40-byte pool** (extent confirmed: 0x43F52 and 0x4516A
iterate exactly `a5@0x286`=5 records, stride 0x40). It is accessed by many routes: the burst
(0x43F4E), char-route activators (0x41652 char 'f', 0x41A88), scripted positional spawns (0x451xx),
and boss component handlers (0x46xxx). It is **not a dedicated burst-child block**.

## C. All pre-burst writers

Every writer that *populates* pool records does so through **0x45248** (the parameterized creator):
it sets `+0x00=1, +0x03=1 (hunter mode), +0x04=1, +0x1C=1, +0x20=1, +0x2F, +0x21, +0x0D (target
char), +0x1E (base), +0x1A=0x180` — and **does NOT set +0x05 (state)**. Callers (all scene-X gated)
supply base+char: 0x451AC (A5+0x3C8, char 'S', base 0x0224), 0x451D8 (A5+0x488, char 'P', base
0x00F4), 0x45204 (A5+0x408, char 'T', base 0x0224), 0x45230 (A5+0x448, char 'U', base 0x0224),
0x464BA (A5+0x3C8, char 'Z', base 0x0546). Full list:
`analysis/actor_decompilation/h16_burst_child_initialization.tsv`. **No writer sets a state at
creation** — pool records are latent hunters until they materialize.

## D. Template / initialization format

There is **no data-driven five-record template**. Pool records are individually created as latent
hunters (§C). A record only gains a state (+0x05) by materializing through the marker system
(0x41362). This is the crux the checkpoint asked for: *the pool is populated by independent
creators, not by a burst-specific template owner.*

## E. 0x43F4E semantics (COMPLETE, `raw/00043f4e.c`)

`0x43F4E` (`0x43F52`) walks `a5@0x286` (=5) records from A5+0x3C8, stride 0x40:
- `+0x00==0` (inactive) → **skip** (counted only);
- `+0x00!=0 && +0x05==0` (active, no state = un-materialized hunter) → **RETIRE (0x4092E)**;
- `+0x00!=0 && +0x05!=0` (active, materialized) → `+0x39=1` then **0x447F0**.
So it activates only the materialized occupants; it does not itself build or copy any record.

## F. 0x447F0 / 0x448B2 activation (COMPLETE)

`0x447F0` sets `+0x3D=1` and, unless rec_type 7, calls `0x448B2`: `+0x07=0, +0x08=0xFF, +0x3C=0,
+0x05=0x0F, +0x09=1`, sfx 0x10. **It writes only state/flags/sfx — never +0x1E/+0x01/+0x38/+0x27.**
So activation itself preserves the slot's graphics fields; the *visible* identity is then decided by
the state-0x0F handler (§H). The prior "IDENTITY PENDING" note is now **RESOLVED** in
`raw/000447f0.c`.

## G. Five-record relationship

**Up to five INDEPENDENT transient effect instances** — one per activated slot. Not one composite
(no root/component hierarchy; each slot is walked and activated independently, each self-retires on
its own +0x08 counter) and not five persistent enemies. `h16_burst_child_slots.tsv` +
`h16_burst_child_structure.json`.

## H. State-0x0F first-visible behavior (`raw/00040ccc.c`)

State 0x0F (0x40CCC) branches by `+0x03` and `+0x39`:
- `+0x03==0, +0x39!=0` → **0x40DD8**: `+0x38=0`, **`+0x1E=0x0275`**, anim `0x08+0x9D` = **0x9E/0x9F/
  0xA0**, and **self-retires at `+0x08>=4` (0x4092E)** — an expanding impact/burst effect.
- `+0x03!=0` → **0x40E0E**: preserves the inherited base, sfx 0x17 at +0x08==1, anim 0x70..0x73,
  self-limited at `+0x08>=4`.
- (`+0x39==0` non-child → the "armored man" base 0x0A73→0x0A5A path, unrelated to the burst.)
The burst child (`+0x39=1`) therefore takes 0x40DD8 or 0x40E0E; **both are short-lived
self-retiring EFFECTS** (~4 frames). Identity is **assigned by state 0x0F, not inherited**.

## I. Exact rendered graphics + palette

For the primary +0x39/+0x03==0 path (`h16_burst_child_render.tsv`): base **0x0275**, selector 0,
programs 0x3E732/0x3E753/0x3E778 for anim 0x9E/0x9F/0xA0, **8→9→10 pieces** (expanding).
`+0x27=0` (0x45248 never set it) → **display palette line 0** (control-byte nibble, per H15) →
`0x3BA88[1][0] = pool 0x0B → 0x4FD02+0x0B*32 = 0x04FE62` (16 raw words recorded). The +0x03!=0
alternate renders with its inherited base + sfx 0x17 (palette per its own +0x27).

## J. Round-1 Phase-2 ownership

Round 1, Phase-2 castle scene **0x15**, entry marker **0x4D** → state 0x1B → 0x43ECC → 0x43F4E. The
effect base 0x0275 is fixed; **which** pool slots hold an active-materialized actor at burst time
(and thus how many effects appear, 0..5) is runtime-dependent on the shared pool's contents. Not
generalized to other rounds (0x43F4E has many callers, but the base-0x0275 identity is the state-0x0F
child path, independent of round).

## K. Manifest / Bestiary update

Added **one** entry `effect_0x0275_burst` (category `EFFECT_TRANSIENT`) — a transient burst/impact
effect, R1 Phase-2, marker 0x4D, creator path, base 0x0275, VM frame (anim 0x9E), display palette
line 0. **No five species cards.** A minimal "Transient Effect Gallery" renders it. `_synced_through`
= H15 (H16 status carried in the entry + dashboard). Bestiary regenerated; consistency PASS.

## L. Durable C changes

- **UPDATED RAW C:** `raw/00040ccc.c` (state 0x0F: added the +0x39 burst-child frame gate +
  self-retire; documented it as the R1 marker-0x4D burst-effect identity, base 0x0275);
  `raw/000447f0.c` (IDENTITY PENDING → RESOLVED: identity assigned by state 0x0F, not preloaded).
- **NEW RAW C:** none (0x43ECC/0x43F4E/0x447F0/0x448B2/0x40CCC were already COMPLETE).
- **NEW / UPDATED SEMANTIC C:** none required — the semantic modules
  (`rastan_actor_lifecycle.c`, `rastan_actor_behavior.c`) already own these; the raw refinements
  carry the H16 semantics.
- **FUNCTIONS PROMOTED COMPLETE:** none (all were already COMPLETE; refined in place).
- `historical_claim_audit.csv`: +1 H16 row.

## M. Remaining exact dependencies

- **Which +0x03 sub-path** a given R1 burst instance takes (0x40DD8 base 0x0275 vs 0x40E0E
  inherited-base) depends on the activated slot's inherited `+0x03`, which is runtime pool state.
- **How many / which slots** are active-materialized at the R1 0x4D burst is runtime-dependent (the
  shared pool is written by scene-X-gated creators).
- These are genuinely dynamic; the *effect identity* (base 0x0275, self-retiring, palette line 0)
  and the *mechanism* (controller → pool-activate → state-0x0F effect) are statically proven.

## Validation

- All five slots accounted for; every renderer-relevant field of the effect has provenance; base/
  anim not inferred merely from "state 0x0F" (taken from the exact 0x40DD8 writes); the effect
  reaches the renderer (VM legal, 8–10 pieces); controller not mislabeled as child species; palette
  follows +0x27=0 → control nibble; no duplicate species cards for components.
- `gcc -fsyntax-only` **PASS** (100/100); coverage guard **PASS**; fidelity guard **PASS**; manifest
  consistency **PASS**; stale H14/H15 bestiary status strings **absent**; counter **373 → 373**.
- Evidence: `h16_burst_child_initialization.tsv`, `h16_burst_child_slots.tsv`,
  `h16_burst_child_render.tsv`, `h16_burst_child_structure.json`.
