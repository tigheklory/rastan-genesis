# Andy — Global Actor / Sprite-Graphics Semantic Map (Ghidra decompilation)

**Ghidra-first static recovery. No ROM, no Genesis implementation, counter 359.** Authority: the
original arcade 68000 program as decompiled in Ghidra (`analysis/ghidra/rastan_arcade/exports/` —
`decompiler_export.c`, `linear_disassembly.tsv`, `function_inventory.tsv`, `xrefs.tsv`,
`call_graph_edges.tsv`). Arcade PCs are authoritative; runtime Genesis PCs only via
`build/rastan-direct/address_map.json`. Supporting sources (census/traces/Composer) are used only to
corroborate, never to substitute for code.

> **Ghidra DB status:** headless Ghidra is not installed in this environment, so the DB was not
> mutated live. §12 is a **proven change-list** (renames/types/tables/comments) for a future agent to
> apply in the GUI/headless. Everything below is read from Ghidra's own exported decompilation.

> **CONSOLIDATION NOTE (correction).** An earlier draft of this map under-used prior work. This
> version **builds on the existing `analysis/enemy_sprite_lexicon/`** — the authoritative family model
> already recovered there (`corrected_semantic_families.json`, `static_actor_records.json`,
> `round_phase_presence.csv`) plus the **55 already-named actor/player functions in the Ghidra DB**.
> Per `SEMANTIC_STATUS.md`, that lexicon is **evidence, not a closed truth** (categories per selector
> not individually proven; `families.json`/`cody_provisional` are over-inflated and NOT used;
> `INVALID_pass2` excluded). The consolidated data lives in `rastan_actor_graphics_manifest.json`
> (schema 2).

## Authoritative family identity — actor+0x3E (the model I initially missed)

The real family key is **`actor+0x3E`**, selected by **`FUN_0004544e`** (selector logic ~0x45404–
0x45418, table ~0x4542E/0x45502), with per-family **palette bank from `FUN_00045684` table 0x45722**.
There are **12 identity slots (0–11) + a boss path (0x3E==2 via +0x752, boss base 0x033E)**:

| +0x3E | base | pal | present (rounds) | note |
|---:|---|---|---|---|
| 0 | 0x004B | 0x06 | R1/2/4/5/6 p1 | Stage-1 Lizardman |
| 1 | 0x00D0 | 0x04 | R1/3/4/5/6 | incl base 0x0179, aux 0x019D |
| 2 | (boss) | 0x07 | — | **boss path** (+0x752), base 0x033E |
| 3 | 0x02E8 | 0x0A | R3/4/6 p1 | four-armed insect cluster |
| 4 | 0x0420 | 0x07 | R3/5/6 p1 | |
| 5 | 0x01CB | 0x06 | R5/6 castle | |
| 6 | 0x03B3 | 0x08 | R1/4/5/6 p1 | incl aux 0x03F6 (large bat), 0x0275 |
| 7 | 0x043A | 0x0F | R1 p1 | incl aux 0x050B (spear proj) |
| 8 | 0x0241 | 0x02 | R1 p1, R3 castle | valkyrie + **hurry-up/small-bat (0x0268/0x0275)** |
| 9 | 0x06E2 | 0x01 | static | |
| 10 | 0x0889 | 0x0B | static | |
| 11 | 0x0400 | 0x0E | R2/5 p1 | |

**Bosses: 6, one per round** (`round1..6_boss_composite`), base 0x033E, seed table `mode2_variant_a`
at ROM 0x0454BA — **present-in-round PROVEN; semantic names UNRESOLVED**. **48 static actor seed
records** (`static_actor_records.json`) carry the spawn-seed data with ROM offsets.

Note the two distinct axes: **+0x3E = enemy identity/palette family** (this table); **compositor /
render-family table 0..4** (§F) = the *graphics expansion path*. A producer row carries both
(`hostile_baseXXXX_compositorN`).

---

## Overview — the sprite pipeline spine (MAPPED)

```
spawn: map collision markers (FUN_000559B2) + camera(0x10B8) + progression(0x13E) + stage(0x118)
   -> actor_spawn_ground_and_activate_41180 (0x41180)  [+ demon dispatcher 0x04580C for scripted pairs]
   -> actor_record_loader_4543e (0x4543E) fills an actor slot (block A5+0x2C8, 0x40-byte records)
      + palette_attr_loader 0x45684 -> actor+0x27

per-frame render:
   gameplay finalizer FUN_00041dae (0x41DAE)  /  frontend FUN_00045dfa (0x45DFA)
   -> actor_family0_render_3d054 (0x3D054)  [andi #255 composite index; select family table 0..4]
   -> actor_four_record_expand_3c902 (0x3C902)  [expand composite -> PC090OJ piece quartets]
   -> PC090OJ pieces  (effective bank = ((sprite_ctrl&0xE0)>>1)|(actor+0x27 & 0x0F))

player (separate composer, not the family renderer):
   player_body_constructor_540cc (0x540CC) -> FUN_00054326 (frame select -> 0x1244/0x1246)
   -> FUN_00054492 (expand; body ~0x5BD40; weapons 0x5CD8A/0x5D068/0x5D346/0x5D666) -> 0x546A8
```

## A. Actor families
(see manifest `families[]`.) Player body/weapon/aux, HUD; enemies Lizardman (family0, +0x3E=0, base
0x4B), Four-armed insect (+0x3E=3, 0x2E8), Valkyrie (+0x3E=8, 0x241), Chimera (0xD0), Large Bat
(0x3F6), Small Bat/hurry-up (748 block, 0x268); scripted Flying Demon (two-slot 508, 0x129); shared
base-0x0A73 form/death producer; projectiles (0x50B/0x2E8-proj/0x19D); hazards (block/rope/boulder);
**bosses UNRESOLVED**.

## B. Round/phase availability (MAPPED at family granularity — from the lexicon sweep)
Stage counter **A5+0x0118** (6 stages/rounds). In-stage progression **A5+0x013E** (0..0x87). Spawn
eligibility = a map collision marker present in the current progression window + the camera gate
(`cmpi #160,A5+0x10B8`). **Per-family presence across all 6 rounds × phase1/castle/boss is already
mapped** in `round_phase_presence.csv` (consolidated into the manifest `rounds_phases_present`) — see
the +0x3E table above. What remains UNRESOLVED is the exact **marker→family record data** per stage
(the mechanism, not the presence). Flying Demon = R1 segments 9 & 13 via one-shot flags 0x264/0x25A;
no enemy crosses a phase (screen wipe — established prior).

## C. Spawn routines / tables
| Routine | arcade_pc | Role | Confidence |
|---|---|---|---|
| phase-local collision publisher | 0x0559B2 | emits map markers 0x40/0x41/0x49/0x4F… | PARTIAL |
| recurring scheduler | 0x41180 `actor_spawn_ground_and_activate_41180` | marker/camera/progression spawn | MAPPED (mechanism) |
| record loader | 0x4543E `actor_record_loader_4543e` | spawn record → actor slot | MAPPED |
| palette attr loader | 0x45684 | writes actor+0x27 | MAPPED |
| demon dispatcher | 0x04580C (switch on d0) | routes scripted-pair spawns | MAPPED |
| demon spawn A / B | 0x0458C8 / 0x045970 | one-shot flags 0x264 / 0x25A | MAPPED |
| paired init / activate | 0x45342 / 0x453A2 | body+wings slot init/activate | MAPPED |
| progression advance | 0x558A2 → 0x558E0 | advances 0x13E/0x10C6/0x10CC | MAPPED |
| **per-stage spawn/marker data tables** | — | family selection data | **UNRESOLVED** |

## D. Update / state-machine routines
- Player: `player_body_constructor_540cc` (0x540CC), frame selector `FUN_00054326`, mode A5+0x10E8.
- Enemies: dispatched through the render family tables; **per-family AI/state-machine update routines
  are UNRESOLVED** (the render path is mapped, the behaviour/animation-advance routines per family are
  the next decode — they set the composite index that 0x3D054 masks).

## E. Animation sources
Frame/composite selection feeds a **composite index** into the render family tables. Player frame IDs
at A5+0x1244/0x1246. Enemy composite indices come from per-family state (field +0x3E/type + animation
counters) — **exact per-family animation tables UNRESOLVED** (queue).

## F. Graphics / composite source locations (MAPPED)
- Family renderer `actor_family0_render_3d054` @ **0x3D054** (masks index `andi #255`).
- Composite expander `actor_four_record_expand_3c902` @ **0x3C902** (quartet format
  `[control, signed_y, code_offset, signed_x]`, `0x00` terminator).
- Family descriptor tables: **0=0x03D09E, 1=0x04771C, 2=0x03F0CE, 3=0x040004, 4=0x04002C** (proven via
  selector helpers 0x3F0BC `lea 0x3F0CE`, 0x3FFDC `lea 0x40004`, 0x3FFF0 `lea 0x4002C`, 0x4770E
  `movew 0x4771C(,d0)`).
- Player body table ~**0x5BD40**; weapon tables **0x5CD8A / 0x5D068 / 0x5D346 / 0x5D666**.

## G. Shared art systems (MAPPED as shared; contents PENDING)
- **base-0x0A73 animation-form / death producer** — shared across enemy contexts; the single biggest
  source of "family" mis-attribution in naive census ranges. Represent once.
- burst effect (748_0275, 0x268/0x276), glow orb (0xA5A–0xAA2), shared projectile art.

## H. Unresolved areas (bosses now PARTIAL, not missing)
**Bosses ARE located** — 6 round bosses (base 0x033E, +0x3E==2 via +0x752, seed table 0x0454BA),
present-in-round proven; their **semantic names and per-boss animation/graphics remain UNRESOLVED**.
Still UNRESOLVED: per-family AI/state-machine update routines (they set the composite index feeding
0x3D054); per-family animation-table contents; exact per-stage marker→family record data; hurry-up
idle timer/threshold/count; items/pickups/drops semantic split; player weapon-state→table binding.

---

## Actor record structure (recovered)
0x40-byte record. Fields: +0x00 active, +0x03 family/type, +0x05 class/base-low, +0x0D
spawn/marker byte, +0x16 X, +0x1A Y, +0x1C timer, +0x27 palette attr, +0x30/+0x34/+0x38 flags, +0x3E
subtype/identity, +0x752 paired flag. Blocks: A5+0x2C8 primary (stride 0x40), A5+0x748 secondary,
A5+0x5C8 paired area, A5+0x508/0x548 demon body/wings.

## 12. Ghidra DB change-list (proven; apply in GUI/headless)

**Functions to rename** (all proven above): `FUN_0003d054 → actor_family_render` (already
`actor_family0_render_3d054`, keep); `FUN_0003c902 → composite_piece_expand` (keep
`actor_four_record_expand_3c902`); `FUN_0003f0bc → family2_table_select`; `FUN_0003ffdc →
family3_table_select`; `FUN_0003fff0 → family4_table_select`; `FUN_0004770e → family1_table_select`;
`FUN_0004543e → actor_record_loader` (keep existing); `FUN_00045684 → actor_palette_attr_loader`;
`FUN_000559b2 → phase_collision_marker_publish`; `FUN_000558e0 → progression_advance`;
`FUN_0004580c → scripted_pair_dispatch`.

**Data tables to define** (type: byte/quartet arrays, terminated 0x00): `family0_composite_table @
0x03D09E`, `family1_ptr_table @ 0x04771C` (word pointer table), `family2_composite_table @ 0x03F0CE`,
`family3_composite_table @ 0x040004`, `family4_composite_table @ 0x04002C`, `player_body_table @
0x05BD40`, `player_weapon_table_{0..3} @ 0x05CD8A/0x05D068/0x05D346/0x05D666`.

**Structure** `Actor` (size 0x40) with the fields above; apply to A5+0x2C8/0x748/0x5C8/0x508/0x548.

**Constants/labels**: `A5_STAGE=0x118`, `A5_PROGRESSION=0x13E`, `A5_CAMERA_X=0x10B8`,
`DEMON_FLAG_A=0x264`, `DEMON_FLAG_B=0x25A`, `PAIR_VARIANT=0xC5A`, `PLAYER_FRAME_ID=0x1244`.

**Comments**: annotate 0x3D054 ("family renderer; d0=composite index masked to byte; family table
chosen by +0x3E/type via 0x3F0BC/0x3FFDC/0x3FFF0/0x4770E"), 0x3C902 ("quartet piece expander
[control,signed_y,code_offset,signed_x], 0x00 term"), and the effective-bank formula at the emit site.
