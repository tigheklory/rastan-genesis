# 0x4A104 Spawn-Schedule Semantic Correction

**Static arcade decompilation. No ROM, no Genesis, counter 359.** Continues the 0x4A104 discovery;
corrects only the SEMANTIC layer on top of the ROM-derived facts. Source: original arcade
`build/regions/maincpu.bin` + existing Ghidra decompilation. Original arcade PCs authoritative.

## Confirmed low-level facts (unchanged)

`FUN_0004A0D8` / the sibling spawner at ~0x4A01E index the table at **0x4A104**; `A5+0x13E` and
`A5+0x118` form the block index; `A4+0x26` selects an 8-byte record; `FUN_0004A086` decodes it
(byte1→actor+0x3E, byte2→+0x38/+0x752); `FUN_0004544e` maps +0x3E→family seed. All confirmed.

## New PROVEN semantics (this task)

### Index formula (exact, from disasm)
```
block_index  = (A5@0x13E - A5@0x118) >> 1          ; 0x4A032..0x4A03E and 0x4A0DC..0x4A0EE
record_addr  = 0x4A104 + block_index*40 + record_index*8   ; block = 5 records × 8 bytes
record_index = A4@0x26   (= A5@0xC59, low byte of word A5@0xC58)   ; or FUN_00049F30 return
```

### A5+0x118 = ROUND counter (PROVEN, 6 rounds)
Round-transition routine at 0x3A860–0x3A88E: `addqb #1,A5@0x118` (0x3A878), then
`cmpib #7,A5@0x118` and cap a companion `A5@0x117` at 6 (0x3A880–0x3A888). So 0x118 counts rounds and
the game tops out at 6. Also written at 0x45292.

### A5+0x13E = in-round PROGRESSION counter (PROVEN behavior; range/reset partial)
Incremented at 0x558FE (inside `FUN_000558e0`, the progression-advance), (re)loaded at
0x5025A/0x55F26/0x56014. It is the map-progression position within a round. **Whether it resets to 0
per round is not yet proven** (see unresolved) — this is what maps block indices onto rounds.

### The 5 records per block = up to 5 CONCURRENT enemy slots (PROVEN — corrects my assumption)
`FUN_00049F30` (0x49F30) is the record selector. It:
1. scans the active enemy actor block `A5+0x2C8` (up to 9 slots, stride 0x40);
2. for each *active* enemy, reads its `+0x26` (its record index) and marks `C52[index]=1` (a 5-wide
   in-use bitmap at A5+0xC52);
3. returns the **first record index 0–4 whose slot is NOT currently alive**, or 0xFF if none free.

So each block's 5 records are **five enemies that can be simultaneously alive**; the spawner refills
whichever record-slot has died. **This proves the "union of the 5 records = the block's concurrent
roster" interpretation** — it was an assumption before; it is now proven. `A4+0x26` is *which of the
5 concurrent slots*, not a mutually-exclusive alternative.

### +0x3E == 2 is the BOSS/special seed path (PROVEN, not a heuristic)
`FUN_0004544e` (0x4544E) branches on `A4+0x3E==2` to the `mode2_variant_a/b/c` tables (base 0x033E),
selected by +0x38, indexed by +0x752. So family 2 *is* structurally the boss path — independent of any
table-contents heuristic.

## CORRECTED / RETRACTED claims from the previous roster report

| Previous claim | Status | Why |
|---|---|---|
| "18 / 18 slots statically decoded" | **RETRACTED** | phase (P1/castle/boss) boundaries were inferred from table contents, not proven from game/progression state |
| "6 boss runs delimit 6 rounds" (family-2-majority heuristic) | **RETRACTED** | the delimiter heuristic is not a proven game semantic. (family-2 = boss path IS proven, separately) |
| generated "Round 7" | **RETRACTED** | an artifact of the family-2-majority heuristic breaking down |
| "cumulative enemy introduction across rounds" | **RETRACTED** | depends on the unproven block→round mapping |
| "union all 5 records = simultaneous roster" | **CONFIRMED (now proven)** | `FUN_00049F30` proves 5 concurrent refillable slots |
| "66 groups, table 0x4A104..0x4AB54" | **CORRECTED to UNPROVEN** | extent was inferred from "byte1 looks like a valid family"; no terminator/count statically proven |
| index formula, record decode, +0x3E family map | **CONFIRMED** | direct disasm |
| A5+0x118 = round (6) | **CONFIRMED (now proven)** | 0x3A880 cmp #7 / cap 6 |

## Remaining unresolved semantics (honest)

1. **Block → round/phase mapping.** Needs `A5+0x13E`'s per-round reset/range and the outdoor/castle/
   boss game-state (progression code `FUN_000558e0` at 0x558E0, sub-phase, scene state). Until then,
   *which block indices belong to which round/phase is not proven*, so no per-phase roster is proven.
2. **Table extent.** Start 0x4A104 proven; end/count NOT — needs the max legal `(0x13E-0x118)>>1` and
   confirmation of neighboring data.
3. **A5+0xC58/0xC59 vs FUN_00049F30.** Two spawn entries select the record differently (a re-spawn of
   the caller's own +0x26 vs a free-slot search); their exact division of labor is only partly traced.

## Next exact static-decompilation target

Decode **`A5+0x13E`'s reset/range and the round/phase game-state** (progression `FUN_000558e0`
0x558E0 + sub-phase + scene fields) to map block indices → rounds/phases; and prove the **table extent**
via the maximum legal block index. Only then re-derive the per-phase roster.
