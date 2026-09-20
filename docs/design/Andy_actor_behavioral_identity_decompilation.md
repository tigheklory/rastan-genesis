# Rastan Arcade Actor Behavioral Identity — Decompilation (CHECKPOINT H)

**Static decompilation of `build/regions/maincpu.bin` + Ghidra exports. No MAME, no Genesis, no
build; counter 360.** Manifest/bestiary/`build_bestiary.py` intentionally NOT touched (per task).
Evidence: `analysis/actor_decompilation/actor_templates.json`, decoders under `tools/analysis/`.
`A5 = 0x10C000`. Terminology SUB-ROUND 1/2/BOSS. Behavioral identity (not human names) is the goal;
unknown human names are `IDENTITY PENDING`.

Status this pass: **H0 done, H1 done, H2/H3 substantially done, field-semantics partial. H4
(`0x4684E`), H5 (per-state 0x13–0x22 bodies), H6 (full marker routes), H7 (damage/death) are the
documented next targets.**

---

## H0 — CHECKPOINT-C loose ends closed

**`0x45248` — parameterized latent-hunter creator (18 callers).** A general sibling of `0x4103E`:
`+0x00=1, +0x03=1 (hunter), +0x2F=d0 (variant/select), +0x04=1, +0x1C=1, +0x20=1, +0x21=d1
(component idx), +0x0D=d2 (target marker char), +0x1E=d3 (base graphics, set directly),
+0x1A=0x180`. It is the primary **scripted enemy placement** helper: callers pass a fixed block
slot in A4, a target marker char, and a base. Sample callers: `0x45212` (char 0x54 'T', base
0x0224, block-0x2C8 slot), `0x4523E` (char 0x55 'U', base 0x0224, gated by wave `A5+0x2DE` in
[20,28)). 18 call sites across the scripted region `0x45154–0x46848` + `0x4B604/0x4B626`.

**`0x4CD50` owner resolved.** The batch creator `0x4CD42` is called via PC-relative `jsr` from
three scripted handlers **`0x4D410`, `0x4DAD2`, `0x4DFB4`** (deep scripted-encounter region). It
free-slots up to 11 records in block `0x748`, base **`0x0D56`**, state `0x0B`, record type `0x16`,
comp 1, positions from `a0` (per-actor coord stream) + `d0/d1` base and `a1` (home coords),
count `d2`; bounded by an on-screen check (`0x4CD26`). **Role of base 0x0D56:** a group/batch-spawned
**ground actor** (state 0x0B → `0x47140` ground engine); it is a hostile swarm/group, not a
projectile or effect (it runs the standard ground engine and has home coords).

## H1 — complete template tables (`analysis/actor_decompilation/actor_templates.json`)

All templates are 8 bytes: `{word→+0x1E base, byte→+0x3A, byte→+0x01 anim, word→+0x28, word→+0x2C}`.

**Record-type table `0x45592`, legal range type 0x08–0x1D** (0x1E+ is code):

| type | base | anim | role (creator) |
|---|---|---|---|
| 0x08 | 0x0129 | 0x30 | Flying Demon component A (`0x45342`) |
| 0x09 | 0x02AF | 0x57 | Flying Demon component B (`0x45342`) |
| 0x0A | 0x03F6 | 0xB6 | bat |
| 0x0B | 0x0268 | 0xB9 | — |
| 0x0C | 0x050B | 0xBC | scripted actor (`0x45CFC`, state 3) |
| 0x0D / 0x1D | 0x0D5F | 0xC5 | scripted (`0x45AA0`) |
| **0x0E** | **0x061D** | 0x00 | **R1 boss body** |
| 0x0F | 0x061D | 0x14 | R1 boss (variant anim) |
| **0x10** | **0x0988** | 0x82 | **R5 boss body** |
| 0x11 | 0x0988 | 0x89 | boss component (`0x423B2`, state 0x11) |
| 0x12 | 0x0400 | 0xB1 | — (= family 11 base) |
| **0x13** | **0x0753** | 0xD6 | **R2 boss body** |
| **0x14** | **0x082C** | 0x24 | **R3 boss body** |
| **0x15** | **0x07BF** | 0xE0 | **R4 boss body** |
| 0x16 | 0x0D56 | 0xD6 | batch-swarm (`0x4CD50`, state 0x0B) |
| **0x17** | **0x0B35** | 0x66 | **R6 boss body** |
| 0x18 | 0x0AED | 0x82 | boss-related |
| 0x19 | 0x0CCB | 0x7C | boss-related |
| 0x1A | 0x0BEB | 0x30 | boss-related |
| 0x1B | 0x09EA | 0xFC | **common projectile / thrown** |
| 0x1C | 0x0547 | 0xBA | — |

**Per-round boss bodies** (trigger `0x45330→0x4449E`, table `0x444E0[round-1] = {0E,13,14,15,10,17}`):
R1=0x061D, R2=0x0753, R3=0x082C, R4=0x07BF, R5=0x0988, R6=0x0B35. Exact match to the prior boss map.

**Family tables `0x45502` (variant 0) — matches `corrected_semantic_families.json`:**
f0=0x004B, f1=0x00D0, f2=0x033E, f3=0x02E8, f4=0x0420, f5=0x01CB, f6=0x03B3, f7=0x043A, f8=0x0241,
f9=0x06E2, f10=0x0889, f11=0x0400. `0x45562` (variant≠0): f0–f5 same bases (harder `+0x28/+0x2C`),
**f6–f11 alias the record-type bases** (0x0129/0x02AF/0x03F6/0x0268/0x050B/0x0D5F) — a table overlap;
variant≠0 for families 6–11 is not produced by the observed schedule and is flagged as a quirk.

**Family-2 boss tables `0x454BA/D2/EA` — ALL variants resolve to base `0x033E`** (anim 0x93) with only
`+0x28/+0x2C` differing. This **confirms 0x033E is universally the scanner identity**; the visible
boss is the separate record-type body (0x0E/13/14/15/10/17), created by the boss trigger, NOT the
family-2 template.

## H2/H3 — the two common update engines and the shared core

- **`0x47140` (ground/standard actor engine)** — states 0x03–0x0C, 0x12: first frame calls `0x41CFA`
  (loads motion/config from `0x41D26[state]`), then **`0x3CEB0`** (core), then per-family animation
  selection (family 0 → anim 0x17+phase; family 1 → 0x23+walk-cycle from `+0x0D` thresholds
  14/16/42/44; family 2 → 0x93 base).
- **`0x473B8` (airborne actor engine)** — states 0x01/0x02/0x0D/0x0E: same `0x41CFA` setup, plus
  family-specific vertical/hover setup (`0x4734A`; family 1 → `+0x08=4,+0x0A=8`; family 0x0A →
  `+0x08=2 or 7` by `+0x2E`), then **`0x3CEB0`** (same core), then per-state animation.
- **`0x3CEB0` (SHARED core: animation-frame advancer + motion stepper).** Manages `+0x07` (init/first
  flag), `+0x08` (frame duration), `+0x09` (frame countdown), `+0x0E` (sequence index), `+0x12`
  (sub-counter), and steps position. **§15 verification:** "walking" vs "flying" is NOT two separate
  movement engines — both wrap the one physics core `0x3CEB0`; the flying engine only adds a
  vertical/hover pre-step (`0x4734A`). Accurate names: `0x47140` = *ground-actor engine*, `0x473B8` =
  *airborne-actor engine (vertical pre-step + same core)*.

## Field semantics newly proven (H12 partial)
| offset | meaning | evidence |
|---|---|---|
| +0x07 | init / first-frame flag | `0x47140`/`0x473B8`/`0x3CEB0` gate |
| +0x08 | animation frame duration | `0x3CEB0` reloads +0x09 from it |
| +0x09 | animation frame countdown | `0x3CEB0` decrements |
| +0x0E | animation sequence index | `0x3CEB0`/anim selection |
| +0x12 | animation sub-counter | `0x3CEB0` |
| +0x21 | component/sibling index | `0x423B2` sets 0..4 |
| +0x2F | difficulty / variant select | `0x453D6`, `0x45248` |
| +0x0D | target marker char (hunter) | `0x41064`/`0x41D08`/`0x45248` |
(Polymorphic across classes where noted; not forced to a single global name.)

## Behavioral classification (proven so far)
- **Flying Demon** = two-component actor (record types 0x08/0x09, bases 0x0129/0x02AF), created as a
  fixed pair by `0x45342`, state 3 → ground engine (cf OPEN-027 co-locked components).
- **Boss bodies** = record types 0x0E/13/14/15/10/17 (bases per round), single record via trigger.
- **Boss components** = record type 0x11 (base 0x0988), 5-part via `0x423B2`, state 0x11 → `0x4684E`.
- **Common projectile / thrown** = record type 0x1B, base 0x09EA (recurs across many update routines
  as the emitted attack — H7 will confirm the emit sites).
- **Batch-swarm ground actor** = record type 0x16, base 0x0D56, via `0x4CD50` (state 0x0B ground).
- **Scripted placed enemies** = via `0x45248` (parameterized hunters, e.g. base 0x0224 at chars 'T'/'U').
- **Families f0–f11** = the ambient roaming enemies; the family template fixes graphics identity, and
  the *movement class* (ground vs airborne) is set by the materialization **state** (from the floor
  marker via `0x40a86`, or the letter marker via `0x41180`), both sharing core `0x3CEB0`. Human names
  IDENTITY PENDING except f0=Lizardman (prior KF-064).

## H4 — `0x4684E` boss-component update (state 0x11)
Gated on family `+0x3E ∈ {2,8}` (else → `0x468E8`). First frame: `0x41CFA` config + `0x468D0`
(compares `+0x16` X to camera `A5+0x10BE` → facing/side). Then the **shared core `0x3CEB0`**, then
boss anim: family 2 → `0x93` + phase (from `+0x0E` thresholds 23/3); else → anim table `0x468C8`
indexed by `+0x0E>>2` (base 0x4D), with `+0x01==0x59 → +0x22=0x3A` special. Each of the 5 components
(`0x423B2`) is an **independent ActorRecord** (individually hittable — relevant to OPEN-027 wing
separation); position/facing sync is performed by the boss body's update loop `0x42380`, which
iterates the 5 by `+0x21` and copies `+0x02` facing. So a boss uses one body record + 5 component
records, all running `0x3CEB0`, synced by `0x42380`.

## H5 — dedicated state handlers 0x13–0x22 (evidence: `analysis/actor_decompilation/h5_state_handlers.json`)

**Key finding: states 0x13–0x22 are NOT ten distinct enemy species — they are one architecture,
the *materialized ground-actor marker-chain state machine*.** Every handler
(`0x4375C`/`0x43840`/`0x43AE6`/`0x43F88`/`0x44082`/`0x4396A`/`0x43B32`/`0x43ECC`/`0x4415A`/`0x43636`)
begins with `0x40E74` (recheck the actor's own target letter marker `+0x0D` at its cell `+0x0E`):
- **marker present** → consume/advance it (`0x4103A`) and **re-target `+0x0D` to the next char while
  rewriting its own base graphics `+0x1E`** (and often `+0x38` comp, `+0x01` anim, `+0x30`), selected
  by round (`A5+0x118`), global progress (`0x13E`), and current char. The actor thus walks a *chain*
  of collision-map letter markers, changing identity at each.
- **marker absent** → run the actor's anim/movement/attack tail; the generic step/retire is `0x4092E`
  (off-screen clear at `0x427B2`).

So the **visible species = the transient `+0x1E` base** cycled during the chain, drawn from a shared
pool: `0x0224, 0x0266, 0x00F4, 0x09EA, 0x0179, 0x0235, 0x09F6, 0x01FC, 0x0236, 0x0546, 0x05E9,
0x0D5F`. Per-state behavioral classes:

| state | PC | class | notable bases | attack/emission |
|---|---|---|---|---|
| 0x13/0x14 | 0x4375C | ground chain-walker | 0x0224 | anim tail (`0x4382E`) |
| 0x15 | 0x43840 | ground chain-walker | 0x0224, **0x0179**, 0x09EA | R6 char 'n'/`0x13E≥0x80` → base **0x0179** (cave-block), char 'H', anim 0x70 |
| 0x16 | 0x43AE6 | ground, scroll/pos-triggered | 0x00F4 | uses `A5+0x200` scroll |
| 0x17 | 0x43F88 | ground chain-walker | 0x05E9, 0x0546, 0x09EA, 0x0224 | `0x13E`-banded base select |
| 0x18/0x1C | 0x44082 | ground chain-walker | 0x0224, 0x00F4 | anim tail; sound 0x18/0x24 |
| 0x19 | 0x4396A | **JUMPING/LEAPING attacker** | 0x0235 (R1), 0x09F6 | arc via `0x41F9C`, `+0x18` vertical, anim 0x8A→0x87→0x8B→0x8D, sound 0x12 |
| 0x1A | 0x43B32 | **master chain dispatcher** (largest, `0x13E`-position-gated) | 0x0224/0x0266/0x00F4/0x09EA/0x01FC/0x0236/0x0546 | primary placed-enemy chain across a stage; sound 0x25 |
| 0x1B | 0x43ECC | **BURST SPAWNER** | (child-dependent) | when player in range (`+0x16` vs camera `A5+0x10BE`) spawns **5 children** via `0x43F4E` → block `A5+0x3C8`, activate `0x447F0` |
| 0x1D/0x21 | 0x4415A | ground chain-walker | 0x0224/0x0266/0x00F4 | `+0x1A` vertical band gate 472..488 |
| 0x22 | 0x43636 | ground chain-walker | 0x00F4/0x0266/0x0224 | anim tail (`0x436E0`), anim 0x29+phase |

**`0x0179` sweep (per sentinel):** directly written by exactly one H5 handler — **state 0x15,
`0x438B6`** (R6, char 'n', `0x13E≥0x80`). Everywhere else `0x0179` is loaded into `d3` as the base
argument to the scripted hunter-creator `0x45248` (`0x46758`, `0x4678C`, `0x4B860`, `0x4C70C`).
**Therefore the R1-Sub-Round-1 destroyable cave-entrance block is a scripted `0x45248` placement
(CHECKPOINT-C creator territory), NOT an H5 dedicated state.** Its creation/destruction path is left
for a later focused checkpoint; H5 only owns the R6 `0x438B6` reuse.

**Child creation from H5:** state 0x1B (`0x43ECC`) → `0x43F4E` bursts 5 actors into block `A5+0x3C8`
(activate `0x447F0`, child `+0x39=1`). This is a new emission path beyond the CHECKPOINT-C allocators.

**H7 targets exposed:** `0x4092E` (generic step/contact/retire body), `0x447F0` (state-0x1B child
init), `0x41F9C` (jump arc); a score/drop hook was not reached in the H5 tails.

## Unresolved / exact next PCs
- **H6:** full marker→state→base materialization route table from `0x41180` (every branch).
- **H7:** damage/death + projectile/child emission (base 0x09EA emit sites), score/drop calls.
- `0x3CEB0` full body (motion/collision detail) and `0x40C08` state 0x10.
