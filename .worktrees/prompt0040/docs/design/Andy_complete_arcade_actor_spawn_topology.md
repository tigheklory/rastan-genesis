# Rastan Arcade Actor / Spawn Topology (structural enumeration from ROM)

**Static arcade decompilation. No ROM build, no Genesis, counter 359.** Goal: prove the *complete*
actor universe structurally from `maincpu.bin` + the Ghidra exports — the actor count is an OUTPUT.
This pass enumerates the storage, creation, and dispatch topology and, critically, **identifies the
un-decompiled region that holds the still-missing actors.** It does not yet claim a complete census.

## 1. Actor storage (enumerated)

Actors are one contiguous array of **0x40-byte records** in A5 WRAM. `lea a5@(N)` sites land on the
slot stride 0x40: 0x2C8, 0x308, 0x348, 0x388, 0x3C8, 0x408, 0x448, 0x488, 0x4C8, 0x508, 0x548, 0x588,
0x5C8, 0x608, 0x648, 0x688, 0x6C8, 0x708, 0x748 → **~19 slots from 0x2C8 to 0x748**. Fields (proven):
+0x00 active, +0x01 class, +0x03 type, +0x1C timer, +0x16/0x1A X/Y, +0x26 record-slot index,
+0x27 palette attr, +0x36 gfx, +0x38 compositor(0–4), +0x3E family, +0x752 variant. The demon uses the
0x508/0x548 pair inside this array. A separate small region at ~0xF10 exists (HUD/aux, unverified).

## 2. Actor creation / activation routes (all `active:=1` writers + spawners)

| Route | entry PC | what it creates | source | status |
|---|---|---|---|---|
| Marker/ground scheduler | `0x41180` (write 0x4103E) | field enemies at map markers | map collision markers (0x559B2) + progression | DECODED |
| Field schedule | `0x4A086` (write 0x4A0BA) via `0x4A0D8` / `0x49F30` | field enemies | spawn table 0x4A104 (per-round, §prev docs) | DECODED |
| Paired/scripted init | `0x45342` (write 0x45248/0x453A8) | **paired & scripted actors (bosses, mini-bosses, scripted encounters)** | **17 call sites** (below) | **PARTIAL — only the 5 demon sites decoded** |
| Scripted spawner | `0x4BBCA` (→0x4543E loader +0x45CFC activate) | scripted actor | called from 0x45FC2/0x45FFA | **UNDECODED** |
| Boss/frame owner | `0x41F30` → 0x55AB4 / 0x59882 / 0x5988C | boss render + components | — | **PARTIAL** |
| Alt activation (block a2) | `0x4CD50` | actor in the 0x4C subsystem | — | **UNDECODED** |
| State objects | writes to a5@0x1372 / 0x137C / 0x4978 / 0x4988 | non-array gameplay objects (boss state?) | 0x50632/0x52BF4/0x52C0E | UNDECODED |

**The 17 paired-init (`0x45342`) call sites:** `0x0458C8, 0x045970` (demon enc-A/B, DECODED),
`0x045FAC, 0x045FE4, 0x046124` (demon-adjacent), and **`0x04ABEC, 0x04ACE6, 0x04ADC2, 0x04B1EA,
0x04B20A, 0x04B31A, 0x04BA48, 0x04BB8E, 0x04BCA8, 0x04C440, 0x04C4EA, 0x04C610` — twelve sites in the
0x4A000–0x4C700 region that are NOT yet decompiled.** These are the strongest candidates for the
per-round bosses and scripted/phase-specific enemies missing from the bestiary.

## 3. The 0x4A000–0x4C700 region — DECODED (see Andy_4A000_4C700_scripted_actor_decompilation.md)

**RESOLVED as the scene-id-dispatched scripted-encounter subsystem** (bosses + scripted special
enemies like the Flying Demon). A `cmpiw #scene_id, d0` chain (scene ids 0x38/0x3A/0x3B/0x3C/0x3D/0x40/
0x41/0x58/0x71/0x86… = A5+0x13E progression positions across Rounds 2–6) routes to per-scene handlers;
each is `A5+0x10CC`-gated, one-shot (flag block A5+0x0208..0x026A), variant-selected (A5+0x0C5A), and
spawns a two-slot paired actor via `0x45342` (12 sites) or a direct scripted actor via
`0x4BBCA`→`0x4543E`+`0x45CFC` (1 site). With the 5 Flying-Demon sites this is **~18 scripted-encounter
triggers game-wide** = the round bosses + scripted enemies. It introduces **no new low-level creation
primitive** — it is the scripted trigger layer over `0x45342`/`0x4543E`. The **item/drop/power-up
system is NOT here** and remains unresolved elsewhere.

## 4. Update / render dispatch (enumerated)

- **Field update / scroll / collision:** `FUN_000406a4` (scroll-advance over the 0x2C8 array),
  `player_actor_collision_scan_449b4` (0x449B4, iterates 0x2C8), `actor_velocity_and_map_collision_42e38`.
- **Render:** gameplay `FUN_00041dae` + boss `FUN_00041f30` → `actor_family0_render_3d054` (0x3D054,
  compositor select by +0x38) → `actor_four_record_expand_3c902` (0x3C902 VM) → PC090OJ pieces.
- **No single "jmp table[actor_type]" update dispatcher was found** — actor behaviour is
  class/type-branched within the update functions rather than one master jump table, so completeness
  must be proven per creation route + per class table, not from one dispatcher.

## 5. Palette pipeline (PROVEN, from ROM — retained)

Per-round field palette: `pool_index = maincpu.bin[0x3BA88 + (round-1)*32 + (bank&0x0F)]`; palette =
pool `0x4FD02 + pool_index*32`; loader `FUN_0003BA20`. Family nibble from table `0x45722`. Validated
vs the known R1 colors. **This palette logic is proven for field families only** — special/boss/item
palette attributes (+0x27 via `FUN_00045684`, and the 0x4A–0x4C subsystem's own attributes) must be
traced per category (not yet done for the scripted subsystem).

## 6. Honest completeness audit (census OUTPUT)

- Actor storage blocks enumerated: **YES** (one 0x2C8..0x748 array + aux ~0xF10 unverified).
- Actor creation/activation routes enumerated: **YES (7 routes found)**; fully decoded: **3 / 7**
  (marker scheduler, field schedule, demon paired-init). **4 routes UNDECODED** (the 12-site scripted
  subsystem, 0x4BBCA, 0x41F30 components, 0x4CD50/state-object writers).
- Update dispatchers: field update DECODED; scripted/boss update UNDECODED.
- Distinct field enemies: **11** (+0x3E families, proven). Bosses: **≥6** but their true creation is in
  the undecoded subsystem, not just base 0x033E. Scripted/phase/item/projectile actors from
  0x4A–0x4C: **UNKNOWN COUNT (undecoded)**.
- Item / power-up / drop system: **NOT YET LOCATED as a system** (candidate: the 0x4A–0x4C subsystem +
  drop-on-death paths off the update functions) — UNDECODED.
- Compositor VM (`0x3C902`): control-nibble dispatch mapped; full command semantics NOT yet
  reimplemented (blocks static frames for uncaptured actors).

**Census status: NOT COMPLETE.** The remaining unresolved code paths are precisely: the twelve
`0x45342` call sites in 0x4A000–0x4C700 (+ `0x4BBCA`, `0x4CD50`, the `0x41F30` component chain), the
item/drop system, and the `0x3C902` compositor VM. These are named, not hand-waved.

## 7. Next decompilation targets (in order)

1. Decompile 0x4A000–0x4C700: turn the 12 paired-init call sites into functions; recover each site's
   gating (round/scene), actor identity, and graphics/palette source → the bosses + scripted/phase
   actors + likely the item system.
2. Finish the `0x3C902` compositor VM (offline Python reconstruction) → static legal frames for every
   actor, incl. the currently uncaptured 0x043A/0x06E2/0x0889.
3. Trace the item/drop/power-up system (death-drop paths + pickup collision) as its own category.
4. Only then rebuild the bestiary and re-run the completeness audit.

## Update: scene/phase state machine decoded (Andy_scene_phase_state_machine.md)

The outdoor/castle/boss transition is a proven state machine: A5+0x1394 (transition-active 1/0xFF),
A5+0x138A (sub-state sequencer 8..255 = screen-wipe/actor-clear/scene-load), A5+0x13B8 (0x13E
checkpoint), A5+0x1242 (master section index → 0x13E via 0x5073A). The scripted-encounter dispatch is
PROVEN 0x13E-driven (0x4AB5C), so scripted routes map to rounds; the R3 chain (0x13E 0x2F–0x41) is fully
extracted. **Rounds 6/6 and boss↔round-boundary 6/6 are proven; the OUTDOOR↔CASTLE sub-split remains
UNKNOWN** pending the per-section scene-type descriptor / map-stream scene commands. This does NOT add
a new creation primitive.
