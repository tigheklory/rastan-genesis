# Authoritative Round Actor Roster (static arcade decompilation — PROVEN)

**Analysis only. No ROM, no Genesis, counter 359.** Decoded from the original arcade
`build/regions/maincpu.bin` + existing Ghidra analysis. Original arcade PCs authoritative. This is the
**proven** version; the earlier phase-boundary heuristic (family-2-majority, "Round 7", "18/18",
"cumulative") is superseded by the progression proof in
`Andy_round_phase_progression_decompilation.md`. Builds on `corrected_semantic_families.json`,
`static_actor_records.json`, the +0x3E family model, and the Palette Composer R1 identities.

## Proven spawn model

- **Spawn schedule** table at arcade **0x4A104**, 66 blocks × (5 records × 8 bytes), extent
  0x4A104..0x4AB54 (proven via max block index 65).
- **Index:** `block = (A5@0x13E − A5@0x118) >> 1`; within a block, record = `A4@0x26` /
  `FUN_00049F30`. Record byte1 → `actor+0x3E` family; `FUN_0004544e` maps +0x3E → base-code seed.
- **A5@0x13E** = global progression 0x00..0x89; **A5@0x118** = round 1..6; round boundaries from ROM
  table **0x502AC** = {0x16,0x2D,0x44,0x5B,0x72,0x89}.
- **Structure:** 6 rounds × {field-enemies, boss}. The **boss** (family 2, base 0x033E) is the tail
  blocks of each round. **Outdoor vs castle is scene state, not a spawn boundary** — they share the
  round's field blocks. There is no 18-way spawn split and no Round 7.
- **The 5 records per block are up to 5 concurrent, refillable enemy slots** (`FUN_00049F30`).

## Per-round roster (PROVEN)

| Round | 0x13E range | blocks (field / boss) | Field enemy families (+0x3E → base) | Boss |
|---|---|---|---|---|
| **1** | 0x00–0x16 | 0–7 / 8–10 | Lizardman 0x004B, Chimera 0x00D0, Four-Armed Insect 0x02E8, Valkyrie 0x0241 | family 2 · base 0x033E |
| **2** | 0x16–0x2D | 11–18 / 19–21 | + 0x0420, 0x0400 | 0x033E |
| **3** | 0x2D–0x44 | 22–29 / 30–32 | + 0x03B3 | 0x033E |
| **4** | 0x44–0x5B | 33–40 / 41–43 | + 0x06E2, 0x0889 (0x0420 absent) | 0x033E |
| **5** | 0x5B–0x72 | 44–51 / 52–54 | + 0x043A (0x0420 returns) | 0x033E |
| **6** | 0x72–0x89 | 55–61 / 62–65 | + 0x01CB (full late set) | 0x033E |

Full per-round field family sets (+0x3E ids): R1 {0,1,3,8}; R2 {0,1,3,4,8,11}; R3 {0,1,3,4,6,8,11};
R4 {0,1,3,6,8,9,10,11}; R5 {0,1,3,4,6,7,10,11}; R6 {0,1,3,4,5,6,10,11}. First record address of block
g = `0x4A104 + g*40`.

**Names:** R1's four are Composer-proven (Lizardman/Chimera/Insect/Valkyrie; palettes 0x36/0x34/0x3A/
0x32). Families 4,5,6,7,9,10,11 (bases 0x0420/01CB/03B3/043A/06E2/0889/0400) are **identity-proven
(base code + spawn), names PENDING** (resolve via the Composer palette decode for their debut round).
All six bosses use base **0x033E**, differentiated per round by variant (+0x38/+0x752) and per-round
palette — a later task.

## Special / aux spawns (separate layer — NOT in this schedule)

The `selector_08_1c` seed table (0x45592) holds spawns not driven by the +0x3E family schedule —
**Flying Demon 0x0129, Large Bat 0x03F6, Small Bat 0x0268, spear 0x050B, boulder 0x0D5F, fireball
0x019D** — triggered by the map-marker path (`0x0559B2 → 0x41180`). Their per-round trigger set is a
later decode (do not start yet).

## Reconciliation vs the old runtime sweep (`round_phase_presence.csv`)

The ROM proves the Palette Composer's R1 identities and **supersedes the sweep**: Four-Armed Insect,
Chimera, and Valkyrie all spawn from **Round 1** (sweep wrongly said R3/R5/unresolved). Flying Demon
and the bats are `selector_08_1c` special spawns (sweep miscategorized them). The six "distinct boss"
rows are one base 0x033E, differentiated by variant + palette.
