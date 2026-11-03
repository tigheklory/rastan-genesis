# Cody: Original Arcade Player Attack Hitbox Semantic Model

Baseline: Build 0281, SHA-256
`8f4997566386f30c0c3dd37f922762d7f6b0677f8bbd9c4a8995046dfb9ab790`.
This is an original-arcade semantic analysis. It makes no production change, produces no
ROM, and leaves the build counter at 281.

Status vocabulary in this report:

- **PROVEN**: established directly by original arcade instructions/data or by exact
  `address_map.json` correlation.
- **HYPOTHESIS**: consistent with the evidence but requiring one named dynamic fact.
- **DISPROVEN**: contradicted by the original arcade instructions/data or current static
  Build 0281 correlation.

## GOVERNANCE / ADDRESS SOURCES

**PROVEN:** `RULES.md`, `AGENTS.md`, `CLAUDE.md`, and `ARCHITECTURE.md` were read before
this audit. The original arcade program and data are authoritative. Build 0281 code
correlations below come only from `build/rastan-direct/address_map.json`; no fixed-offset
arithmetic is used as proof.

Address labels are kept distinct:

- `arcade_pc`: original executable address.
- `arcade ROM/data`: original table/data address.
- `runtime_genesis_pc`: executable address in Build 0281.
- `Genesis-WRAM`: A5-relative game state with Build 0281's A5 base `0x00FF0000`.

Primary evidence:

- `analysis/ghidra/rastan_arcade/exports/decompiler_export.c`
- `analysis/ghidra/rastan_arcade/exports/full_listing.tsv`
- `build/maincpu.disasm.txt`
- `build/regions/maincpu.bin`
- `build/rastan-direct/address_map.json`
- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `docs/design/Cody_arcade_sword_thrust_lizardman_semantic_model.md`
- `docs/design/Andy_build0280_sword_club_piece_rendering_fix.md`

## GHIDRA COVERAGE AUDIT

**PROVEN:** The established Ghidra seed/export was extended to include the previously
unbounded collision functions and data:

| Role | `arcade_pc` / `arcade ROM/data` |
|---|---:|
| actor hurtbox base selector | `0x0446B0` |
| actor hurtbox selector | `0x0446BC` |
| player/actor collision scan | `0x0449B4` |
| player offensive-overlap entry | `0x044C5A` |
| signed-extent interval overlap | `0x044CBA` |
| player collision-box producer | `0x054864` |
| player attack-enable producer | `0x054982` |
| actor type-to-hurtbox selector table | `0x044778` |
| normal actor hurtbox extent table | `0x044CE0` |
| alternate actor hurtbox extent table | `0x044FA8` |
| player body/contact extent table | `0x05C90E` |
| Stage-1/2/3/4 player attack extent tables | `0x05C9EA`, `0x05CAC6`, `0x05CBA2`, `0x05CC7E` |

The headless export completed successfully and decompiled 289 seeded/discovered functions.
Raw listing instructions were used where the decompiler did not preserve D3 accumulation
inside the actor selector.

**PROVEN:** Coverage is complete for the semantic questions in this report: player attack
enablement, phase-to-box selection, facing transform, actor hurtbox selection, two-axis
overlap, and hit dispatch are all identified. No visual sprite record, tile, or pixel test
participates in this collision decision.

## PLAYER OFFENSIVE COLLISION PRODUCER

### State and production order

**PROVEN:** The retained player path calls BODY at `arcade_pc 0x05151C`, then calls the
collision-box producer at `arcade_pc 0x051522 -> 0x054864`. Relevant arcade WRAM state is:

| A5-relative field | Meaning |
|---:|---|
| `+0x10BE`, `+0x10C0` | player X and Y anchors |
| `+0x10E8` | broad action: standing `0`, downward-motion `2/3`, crouch `5`, death `8` |
| `+0x1108` | attack-active flag (`1` active); not the crouch flag |
| `+0x110A` | attack phase, initialized to zero and advanced by `arcade_pc 0x051D32` |
| `+0x1114` | facing (`2` is visually left) |
| `+0x1116` | attack variant (`1` downward thrust, `4` normal horizontal attack) |
| `+0x1244` | BODY/frame selector used to index collision extents |
| `+0x1248..+0x124B` | player body/contact rectangle signed extents |
| `+0x1254..+0x1257` | player offensive rectangle signed extents: X min/max, Y min/max |
| `+0x12F0` | global player-collision disable gate |
| `+0x12F8` | offensive-box enable (`1`) or disable (`0x00FF`) |
| `+0x12FA` | stage/scene number selecting the attack-extent table |
| `+0x1310` | attack damage class/strength |

**PROVEN:** `arcade_pc 0x054326` selects the BODY/frame table from broad action. For this
scope it chooses:

- standing action 0: `arcade ROM/data 0x05B6A0`;
- crouch action 5: `arcade ROM/data 0x05B978`;
- downward-thrust variant 1: `arcade ROM/data 0x05BB10`.

At `arcade_pc 0x0543B4`, the program indexes `table + phase * 2` and writes the first byte
to A5+0x1244. Each table word repeats its selector in both bytes. The active-variant-4 path
at `arcade_pc 0x05438E` deliberately retains A2, the broad-action-selected table pointer
established earlier in the same BODY call.

### Enable gate and extents

**PROVEN:** `arcade_pc 0x054864` first calls `arcade_pc 0x054982`, which writes A5+0x12F8.
For ordinary standing/crouching variant-4 attacks, the offensive rectangle is active only
for phases 3 through 13 inclusive. Variant 1 bypasses that phase window while attack-active.
The box is disabled when A5+0x12F0 is 1. An inactive attack normally disables the box, with
the original action-2 special case retained by the code.

**PROVEN:** A5+0x1244 indexes four signed bytes in the stage-specific player attack table.
For Stage 1, the source is `arcade ROM/data 0x05C9EA`. The tuple is:

`[x_min, x_max, y_min, y_max]`

There is exactly one offensive rectangle. A5+0x1248 is a separate body/contact rectangle
and is not used by the sword attack-overlap entry.

### Consumption and hit result

**PROVEN:** `arcade_pc 0x0449B4` scans 29 actor records of 0x40 bytes from A5+0x02C8. It
first performs body/contact processing into A5+0x12A8, then, only when A5+0x12F8 equals 1,
performs offensive processing with A5+0x1254 through `arcade_pc 0x044C5A`.

`arcade_pc 0x044C5A` selects A5+0x1254. `arcade_pc 0x044C76` selects an actor hurtbox and
normalizes player/actor anchors into the 9-bit coordinate domain by adding `0x80` and
masking with `0x01FF`. `arcade_pc 0x044CBA` sign-extends each extent byte and performs the
two interval tests. X and Y must both overlap.

The endpoint rule is inclusive:

`player_max >= actor_min && actor_max >= player_min`

Thus touching endpoints count as a hit. At most four offensive contacts are recorded in
A5+0x12C8 per scan. A successful overlap calls `arcade_pc 0x044804`, the actor hit/damage
response.

**PROVEN:** `arcade_pc 0x0549DE` writes A5+0x1310. Ordinary standing/crouching horizontal
attacks use class 2; downward-thrust variant 1 uses class 8. `arcade_pc 0x044804` maps class
2 to a +1 actor damage accumulator change, class 4 to +2, and other classes (including 8)
to +3.

## STANDING SWORD HITBOX MODEL

**PROVEN:** Broad action 0, attack-active, variant 4 uses selector table
`arcade ROM/data 0x05B6A0`. Coordinates below are source-facing (visible left), relative to
the player anchor. Width/height are inclusive. Inactive rows show the source tuple but are
not offered to the offensive overlap scan.

| Phase | Selector | Active | X min..max | Width | Y min..max | Height |
|---:|---:|:---:|---:|---:|---:|---:|
| 0 | `00` | no | `7..10` | 4 | `-40..-16` | 25 |
| 1 | `01` | no | `16..30` | 15 | `-24..-21` | 4 |
| 2 | `02` | no | `16..32` | 17 | `-9..-7` | 3 |
| 3 | `03` | yes | `0..9` | 10 | `-5..0` | 6 |
| 4-5 | `04` | yes | `-19..-8` | 12 | `-8..3` | 12 |
| 6-13 | `05` | yes | `-56..-24` | 33 | `-10..-8` | 3 |
| 14-15 | `04` | no | `-19..-8` | 12 | `-8..3` | 12 |
| 16-17 | `03` | no | `0..9` | 10 | `-5..0` | 6 |
| 18-19 | `02` | no | `16..32` | 17 | `-9..-7` | 3 |
| 20-21 | `01` | no | `16..30` | 15 | `-24..-21` | 4 |
| 22-23 | `00` | no | `7..10` | 4 | `-40..-16` | 25 |

**PROVEN:** Maximum standing reach is selector 05: 56 pixels from the anchor toward the
attack direction, spanning offsets 24 through 56. For the opposite facing it mirrors to
`24..56`; it does not shrink to one tile.

## CROUCHING SWORD HITBOX MODEL

**PROVEN:** Broad action 5, attack-active, variant 4 uses selector table
`arcade ROM/data 0x05B978`.

| Phase | Selector | Active | X min..max | Width | Y min..max | Height |
|---:|---:|:---:|---:|---:|---:|---:|
| 0 | `06` | no | `7..10` | 4 | `-26..-2` | 25 |
| 1 | `07` | no | `16..30` | 15 | `-10..-7` | 4 |
| 2 | `08` | no | `16..32` | 17 | `5..7` | 3 |
| 3 | `09` | yes | `0..9` | 10 | `9..14` | 6 |
| 4-5 | `0A` | yes | `-19..-8` | 12 | `6..17` | 12 |
| 6-13 | `0B` | yes | `-56..-24` | 33 | `4..6` | 3 |
| 14-15 | `0A` | no | `-19..-8` | 12 | `6..17` | 12 |
| 16-17 | `09` | no | `0..9` | 10 | `9..14` | 6 |
| 18-19 | `08` | no | `16..32` | 17 | `5..7` | 3 |
| 20-21 | `07` | no | `16..30` | 15 | `-10..-7` | 4 |
| 22-23 | `06` | no | `7..10` | 4 | `-26..-2` | 25 |

**PROVEN:** Every crouching horizontal extent is identical to the corresponding standing
extent. Every crouching vertical extent is the corresponding standing extent plus 14
pixels. Crouching changes attack height, not horizontal reach.

## DOWNWARD-THRUST HITBOX MODEL

**PROVEN:** Broad action 2/3 with attack-active variant 1 uses selector table
`arcade ROM/data 0x05BB10`. Variant 1 remains enabled throughout its active sequence rather
than using the ordinary phase-3-through-13 gate.

| Phase | Selector | Active | X min..max | Width | Y min..max | Height |
|---:|---:|:---:|---:|---:|---:|---:|
| 0-1 | `00` | yes | `7..10` | 4 | `-40..-16` | 25 |
| 2-5 | `19` | yes | `-19..13` | 33 | `-10..-8` | 3 |
| 6-9 | `1A` | yes | `-9..10` | 20 | `0..22` | 23 |
| 10-23 | `1B` | yes | `-9..10` | 20 | `8..40` | 33 |

**PROVEN:** The late thrust reaches 40 pixels below the player Y anchor. It remains one
rectangle; there is no second collision box dedicated to the sword-tip sprite. The
offensive collision producer does not add a tile-size correction or derive geometry from
the visible tip piece.

## FACING / MIRROR COLLISION SEMANTICS

**PROVEN:** Source attack tuples are oriented for A5+0x1114 equal to 2, the visible-left
facing established by the original BODY model. For facing 2, X extents are copied. For the
other facing, `arcade_pc 0x054864` computes:

`mirrored_x_min = -source_x_max`

`mirrored_x_max = -source_x_min`

Y extents are unchanged. Examples:

| Source tuple | Opposite-facing tuple |
|---|---|
| standing/crouch selector 05/0B `-56..-24` | `24..56` |
| selector 04/0A `-19..-8` | `8..19` |
| thrust selector 19 `-19..13` | `-13..19` |
| thrust selector 1A/1B `-9..10` | `-10..9` |

**DISPROVEN:** Collision mirroring depends on PC090OJ flip bits, SAT H-flip, sprite-piece
X positions, or visible sword art. Those are rendering semantics and are not read here.

## ENEMY HURTBOX / OVERLAP CONTRACT

**PROVEN:** The actor-side rectangle is independent of the player attack rectangle and of
rendered PC090OJ composition. Each active 0x40-byte actor record contributes an X anchor at
A4+0x16 and a Y anchor at A4+0x1A. `arcade_pc 0x0446BC` derives hurtbox selector D3 from
actor index/state/type. `arcade_pc 0x044C76` normally indexes signed extent table
`arcade ROM/data 0x044CE0`; A4+0x38 equal to 2 selects alternate table `0x044FA8`.

For actor indices 9 and above, the normal offensive pass accepts type 3 or types above 7,
except types 15 and 22. It rejects actor index 9, inactive records, records with byte +5
zero, and records with byte +0x3D nonzero. Indices below 9 use their original state gate.

**PROVEN representative example, not an actor-identity claim:** Actor type 17 first loads
its base selector from the original type table, adds `2 * unsigned(A4+0x30)`, then chooses
the directional member of the pair from A4+2. A representative directional pair in the
normal extent table is:

- selector `0x9A`: `[24,48,-22,14]`;
- selector `0x9B`: `[-48,-24,-22,14]`.

This demonstrates the normal Stage-1-capable actor contract: an actor-specific signed AABB
is anchored independently and compared to the player's offensive AABB on both axes.

**HYPOTHESIS:** A particular rendered Stage-1 Lizardman instance uses the representative
type-17 pair above. This report does not equate a visual Lizardman composition class with
collision actor type 17 without an actor-scoped runtime identity proof. That identity is
not needed to establish the hitbox producer or standing/crouch differential.

## BUILD 0281 STATIC CORRELATION

### Exact code mappings

**PROVEN through `address_map.json`:**

| Role | `arcade_pc` | `runtime_genesis_pc` | Segment status |
|---|---:|---:|---|
| actor hurtbox base selector | `0x0446B0` | `0x0448B0` | `arcade_copy` |
| actor hurtbox selector | `0x0446BC` | `0x0448BC` | `arcade_copy` |
| hit/damage response | `0x044804` | `0x044A04` | `arcade_copy` |
| player/actor collision scan | `0x0449B4` | `0x044BB4` | `arcade_copy` |
| offensive overlap entry | `0x044C5A` | `0x044E5A` | `arcade_copy` |
| actor table selection | `0x044C76` | `0x044E76` | `arcade_copy` |
| interval overlap | `0x044CBA` | `0x044EBA` | `arcade_copy` |
| BODY call | `0x05151C` | `0x051722` | `arcade_copy` |
| collision-box update call | `0x051522` | `0x051728` | `arcade_copy` |
| attack initialize | `0x051CA0` | `0x051EA6` | patched input literal only |
| attack advance | `0x051D32` | `0x051F38` | `arcade_copy` |
| BODY entry | `0x0540CC` | `0x0542CC` | native shift replacement |
| broad-action selector | `0x054326` | `0x054504` | `arcade_copy` |
| active variant selector | `0x05438E` | `0x05456C` | `arcade_copy` |
| phase selector read | `0x0543B4` | `0x054592` | `arcade_copy` |
| collision-box producer | `0x054864` | `0x054A1A` | `arcade_copy` |
| attack-enable producer | `0x054982` | `0x054B38` | `arcade_copy` |
| damage-class producer | `0x0549DE` | `0x054B94` | `arcade_copy` |

### Exact data mappings

**PROVEN through `address_map.json`:**

| Data | `arcade ROM/data` | Build 0281 `genesis_rom_offset` |
|---|---:|---:|
| actor type selector table | `0x044778` | `0x044978` |
| normal actor hurtbox table | `0x044CE0` | `0x044EE0` |
| alternate actor hurtbox table | `0x044FA8` | `0x0451A8` |
| standing phase selector table | `0x05B6A0` | `0x05B870` |
| crouch phase selector table | `0x05B978` | `0x05BB48` |
| downward-thrust selector table | `0x05BB10` | `0x05BCE0` |
| player body/contact extents | `0x05C90E` | `0x05CADE` |
| Stage-1 attack extents | `0x05C9EA` | `0x05CBBA` |
| Stage-2 attack extents | `0x05CAC6` | `0x05CC96` |
| Stage-3 attack extents | `0x05CBA2` | `0x05CD72` |
| Stage-4 attack extents | `0x05CC7E` | `0x05CE4E` |

**PROVEN:** Build 0281 retains the collision consumer, selector path, enable gate, facing
transform, and attack tables. The attack-initialize replacement at
`runtime_genesis_pc 0x051EA6` rebases its absolute work-RAM input to Genesis-WRAM; it does
not alter attack geometry. The BODY entry replacement preserves D3/D4/D6, and
`native_sprite_emit` saves/restores D0-D7/A0-A2, so the retained active-variant path's A2
table pointer is not clobbered by native rendering helpers.

**PROVEN:** No raw arcade absolute work-RAM address remains in the identified offensive
box producer/consumer path. The Build 0281 sword-mirror correction changes rendering-side
register use for BODY pieces; it does not change A5+0x1244, A5+0x1254, A5+0x12F8, or the
collision routines.

## STANDING-vs-CROUCH DIFFERENTIAL

**PROVEN original arcade differential:**

| Property | Standing | Crouching | Difference |
|---|---|---|---|
| broad action | 0 | 5 | separate semantic state |
| selector family | `00..05` | `06..0B` | separate table |
| active phase window | 3..13 | 3..13 | none |
| horizontal extents | phase-dependent | same phase-dependent values | none |
| vertical extents | phase-dependent | standing values +14 | crouch lower by 14 px |
| maximum directional reach | 56 px | 56 px | none |
| ordinary damage class | 2 | 2 | none |
| facing transform | signed X mirror | signed X mirror | none |

**DISPROVEN:** The original arcade crouching sword has a much larger horizontal hitbox than
the standing sword. It does not: their X extents are byte-for-byte equal per corresponding
phase.

**DISPROVEN:** The original arcade standing sword is intended to reach only one small tile
near the body. Its maximum active tuple reaches 56 pixels from the player anchor.

**DISPROVEN:** A standing/crouching reach difference can be explained by different enemy
hurtbox logic. Both states enter the same offensive consumer and actor hurtbox selection.

## ROOT-CAUSE STATUS

### Proven boundaries

- **PROVEN:** The arcade attack geometry is a phase-selected, stage-selected signed AABB,
  anchored to player X/Y, mirrored arithmetically by facing, and tested inclusively against
  an actor-specific signed AABB.
- **PROVEN:** Standing and crouching have equal horizontal reach; crouching only lowers the
  box by 14 pixels.
- **PROVEN:** Build 0281 statically retains these selectors, tables, and overlap routines.
- **PROVEN:** Visual sword displacement, PC090OJ piece composition, SAT flip, tile art, and
  palette routing do not determine offensive collision geometry.

### Disproven static causes

- **DISPROVEN:** standing and crouching tables are statically swapped in Build 0281;
- **DISPROVEN:** the crouch table encodes a wider horizontal box;
- **DISPROVEN:** the standing table encodes a one-tile maximum box;
- **DISPROVEN:** Build 0281 uses unsigned attack extent bytes;
- **DISPROVEN:** Build 0281 uses body/contact extents instead of attack extents at
  `runtime_genesis_pc 0x044E5A`;
- **DISPROVEN:** the Build 0281 rendering mirror fix changes collision-facing semantics;
- **DISPROVEN:** a stale raw arcade absolute WRAM literal in the identified collision path
  explains the observed reach differential.

### Remaining boundary

**HYPOTHESIS:** The user-observed standing-tiny/crouch-huge behavior requires a live-state
divergence not visible in the static collision code, most plausibly the selector or the
state that selects it.

The one irreducible dynamic fact is:

> Whether, on the exact user-observed standing and crouching frames, live
> `Genesis-WRAM 0x00FF1244` at `runtime_genesis_pc 0x054A1A` equals the selector mandated
> by the live `(broad action, attack phase)` pair: Build 0281 standing table
> `genesis_rom_offset 0x05B870` versus crouching table `genesis_rom_offset 0x05BB48`.

No runtime capture is requested by this task. If that selector matches, the extent bytes
written immediately afterward are deterministic and the reported behavior must be sought
outside this attack-AABB producer (for example, observation/timing or actor identity). If it
does not match, the first divergence is above `runtime_genesis_pc 0x054A1A`, in the retained
BODY/state path that creates A5+0x1244.

**HYPOTHESIS:** Standing and crouching could share one upstream live-state/selector defect,
but static evidence does not prove a shared cause.

**PROVEN:** No exact bounded production correction is established. Patching collision
extents, widening standing reach, clamping crouch reach, or deriving hitboxes from visible
sprites would be symptom-level and is not authorized by this evidence.

Final gate:

- Arcade offensive-hitbox code sufficiently decompiled: **YES**
- Standing hitbox fully known: **YES**
- Crouching hitbox fully known: **YES**
- Down-thrust hitbox fully known: **YES**
- Facing transform fully known: **YES**
- Enemy overlap contract sufficiently known: **YES**
- Build0281 collision path correlated through address_map.json: **YES**
- Standing tiny-reach cause statically proven: **NO**
- Crouching huge-reach cause statically proven: **NO**
- Shared root cause: **NO**
- Exact bounded correction available: **NO**
- ONE exact irreducible dynamic fact stated: **YES**, live
  `Genesis-WRAM 0x00FF1244` selector agreement at `runtime_genesis_pc 0x054A1A`, as
  specified above.
- No MAME: **YES**
- No user gameplay requested: **YES**
- No implementation changes: **YES**
- Build produced: **NO**
- Counter: **281**
- Report: `docs/design/Cody_arcade_player_attack_hitbox_semantic_model.md`
