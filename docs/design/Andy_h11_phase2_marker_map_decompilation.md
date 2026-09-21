# Andy — CHECKPOINT H11: Phase-2 Marker Map Decompilation + Round Pinning

**Agent:** Andy · **Type:** Static reverse engineering (ORIGINAL ARCADE 68000) + report update.
**Build counter:** 360 (unchanged). **NO ROM, NO MAME, NO Genesis change.** Cody files untouched.
**Artifact:** republished (Version 5) at `https://claude.ai/artifact/Dopg3mwMHdUMsZJSQgXDVR`.

Mandatory RULES.md standalone report for CHECKPOINT H11. Authoritative source:
`build/regions/maincpu.bin`. Reconstructed C is auditable, NOT Taito source.

> **Honest result.** H11 **proved the scene→map→collision-marker architecture** and **statically
> pinned all six Phase-2 (castle) start points** from the arcade section stream. It did **not** close
> the per-scene *marker enumeration* — that needs one more sub-engine layer (the ROM populator of the
> collision-record pointer array `A5+0x10D000`), which is the exact next dependency. Per RULES/the
> session rule I stopped there rather than fabricate rosters: the 12 H10 materialized actors remain
> **ROUND PENDING** (not invented into rounds), and this report + C + tables preserve the proven work
> and name the precise blocker.

---

## A. Scene / map source architecture

Three parallel streams keyed off progression `A5+0x13E`:
1. **Section selector** (`0x503BC`): `scene_index = byte[0x50EE0 + 0x13E]`;
   `section_kind = byte[0x50F6B + scene_index]` (0 = outdoor / phase 1, ≠0 = castle / phase 2).
   `A5+0x10C6 = &section_stream[scene_index]`, advanced per column (`0x558E4`).
2. **Background tilemap** (`0x562CA[round]` → `0x563A6`): a per-round ROM metatile stream
   decompressed into the name table (byte 0x00 = end, 0xFF = next column, else metatile→tile).
3. **Collision / marker grid** at `0x10DE00` (`0x559B2`/`0x55A14`): written from per-scene column
   records; **marker = high byte of the collision word**.

## B. Section / progression → map pointer flow

`0x561D6`: `round (A5+0x118)` indexes the per-round table `0x562CA` (8 bytes/round = ROM src ptr +
name-table dst ptr) → `0x563A6` decompressor. The section stream (0x50EE0/0x50F6B) selects
outdoor-vs-castle per column independently of the round's background pointer.

## C. Collision / marker column record format

`0x559B2`, per on-screen column, 4 rows: `grid_word = column_record[20 + subcol*2 + row*8]`
(`subcol = A5+0x10CA` fine scroll; or `column_record[0x22]` when `column_record[0x20]==0xFF`), mapped
to the grid at `0x10DE00 + (name_addr − 0xC08000)/2`. The **marker byte 0x41180 reads is
`grid_word >> 8`**, sourced directly from the per-scene column record — not a tile-property lookup.
`0x55A14` mirrors the sub-column when section kind == 2 (interior variant). Now **COMPLETE** (was
historically PARTIAL).

## D. 0x7E transition source

Not required for the Phase-2 starts (the section stream already selects castle sections). The `0x7E`
door remains the separate in-scene wipe trigger proven earlier; H11 did not need to re-open it.

## E. Six statically proven Phase-2 start points

From the section stream over each round's code-proven `0x13E` window
(ends R1..R6 = 0x16/0x2D/0x44/0x5B/0x72/0x89):

| Round | Phase-2 start 0x13E | section kind |
|---|---|---|
| R1 | **0x11** | 1 |
| R2 | **0x2B** | 1 |
| R3 | **0x41** | 1 |
| R4 | **0x5A** | 1 |
| R5 | **0x6E** | 2 |
| R6 | **0x85** | 2 |

All 6 PROVEN (kind ≠ 0). Tool: `tools/analysis/decode_rastan_scene_markers.py` →
`analysis/actor_decompilation/h11_scene_markers.tsv` (per-0x13E section kinds + deterministic checks:
indices in range, every round has a phase-2 section).

## F. Marker enumeration method

The section layer is fully enumerable (above). The per-column **marker** layer is decoded structurally
(§C) but not yet *enumerable* offline: the column records come from `A5+0x10D040`, built by `0x55904`
from the 16 column descriptors at `A5+0x10D000`. The **ROM population of `A5+0x10D000`** (each column's
collision-record pointer, per scene) is the missing piece — the exact next PC/table to decode.

## G. Marker → state → handler → base mapping

Fully proven in **H6** (`0x41180`/`0x41362`, 28 routes) and **H10** (render/palette). H11 supplies the
*upstream* half (scene → grid → marker); the downstream half (marker → materialized actor → legal
frame + palette) is already closed. Only the middle link — *which marker bytes occur in which castle
scene* — is open (§F).

## H. Per-round Phase-2 roster

`analysis/actor_decompilation/h11_phase2_actor_rosters.tsv` records the six proven Phase-2 starts with
roster status **OPEN** and the exact blocker per round. **No actors were fabricated into the rosters.**
The number of Phase-2 actors per round is deliberately left as an OUTPUT to be produced once §F is
decoded.

## I. Enemy / hazard / effect classification

Deferred: classification is only meaningful once the per-scene markers are enumerated (a marker's
route/handler determines its class). H10's category field (`ENEMY_MATERIALIZED` / `CONTROLLER`) is
retained; no marker-route reclassification was possible without §F.

## J. Per-round palette instances

The palette math is proven (H10). Because the materialized actors are not yet round-pinned (§F/§H),
their exact per-round palette instance stays **PARTIAL** (round-representative). The moment §F pins an
actor to a round, `resolve_palette_line(round, …)` yields the exact instance with no new RE — the data
model already supports `palette_instances[]`.

## K. C files created / updated

- `raw/000503bc.c` (COMPLETE) — section resolver (0x50EE0/0x50F6B).
- `raw/000559b2.c` (COMPLETE, upgraded from PARTIAL) — collision-grid column writer.
- `raw/000563a6.c` (COMPLETE) — background tilemap decompressor.
- `rastan_scene_map.c` (semantic).
- `function_coverage.csv` (+3 → 73 rows / 57 COMPLETE), `historical_claim_audit.csv` (+2 → 54),
  `README.md`.
- Tool: `tools/analysis/decode_rastan_scene_markers.py`. Evidence: `h11_scene_markers.tsv`,
  `h11_phase2_actor_rosters.tsv`.

## L. Remaining exact blocker

**The ROM population of `A5+0x10D000`** — the 16 column descriptors `{word, collision-record-ptr}`
that supply each on-screen column's collision/marker record to `0x55904`/`0x559B2`. Decoding that
populator (and the per-scene table it reads) yields the offline per-castle-scene marker enumerator,
which then round-pins the H10 materialized cast and applies exact per-round palettes. That is the
precise next PC/table for a follow-up pass.

## Validation

- Enumerator: **PASS** (6/6 phase-2 starts, deterministic checks).
- Coverage guard: **PASS** (73 rows, 57 COMPLETE; H5 10/10). Fidelity guard: **PASS**.
- `gcc -std=c11 -fsyntax-only`: **PASS** (75 files). Manifest consistency guard: **PASS**.

## Related documents

`docs/design/Andy_h10_materialized_actor_render_palette_decompilation.md` (render/palette),
`docs/design/Andy_h6_marker_materialization_decompilation.md` (marker → actor),
`docs/design/Andy_scene_phase_state_machine.md` (0x7E door / section machine).
