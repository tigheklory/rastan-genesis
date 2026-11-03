# Scripted-Encounter Actor Identity Map (round assignment)

**Static arcade decompilation. No ROM/Genesis/VM/bestiary, counter 359.** Ties the 0x4A000–0x4C700
scripted-encounter routes (decoded in `Andy_4A000_4C700_scripted_actor_decompilation.md`) to rounds
via the proven `A5+0x13E` dispatch (`Andy_scene_phase_state_machine.md`).

## Selector proof
The main scripted dispatcher's selector is **`A5+0x13E`** (proven at 0x4AB5C `movew A5+0x13E,d0`), so a
route's dispatch value IS a progression position → round via boundaries {0x16,0x2D,0x44,0x5B,0x72,0x89}.
A separate dispatcher at 0x4AF1A uses `A5+0x288` (boss sub-phase selector) — flagged, not assumed to be
0x13E.

## Route → round (proven for the R3 chain; others by dispatch family)

| route (0x45342 site) | dispatch 0x13E | round | one-shot flag | variant 0xC5A | 0x10CC gate | phase (O/C/Boss) |
|---|---|---|---|---|---|---|
| 0x4ABEC | 0x41 | 3 | A5+0x20A | 0 | <1 | round-tail → **Boss/late** |
| 0x4AC.. (0x40/0x3D/0x3C handlers) | 0x3C–0x40 | 3 | (various) | — | — | mid/late R3 — O/C UNKNOWN |
| 0x4ACE6 | 0x3B | 3 | A5+0x268 | 1 | — | mid R3 — O/C UNKNOWN |
| 0x4ACF4/0x4AD.. (0x3A/0x38/0x36/0x34/0x33) | 0x33–0x3A | 3 | (various) | — | — | mid R3 — O/C UNKNOWN |
| 0x4ADC2 | (0x30 area) | 3 | A5+0x260 | 0 | <9 | mid R3 — O/C UNKNOWN |
| 0x4B1EA / 0x4B20A | 0x58 family | 4 | A5+0x26A / 0x208 | 0/1 | <1 | R4 — tail/mid |
| 0x4B31A / 0x4BB8E | (0x10CC<10 / <3) | 4–5 | A5+0x262 | 1 | yes(0x45D10) | R4/R5 — mid |
| 0x4BA48 | 0x71 family | 5 | A5+0x208 | 0 | <1 | R5 — tail |
| 0x4BCA8 | — | 5–6 | A5+0x25A | 0 | — | UNKNOWN |
| 0x4C440 | 0x86 family | 6 | A5+0x208 | 1 | <13 | R6 — tail (near end path 0x5725A) |
| 0x4C4EA / 0x4C610 | (0x0C / <1) | — | A5+0x260 / 0x258 | 1 | — | UNKNOWN |
| Flying Demon 0x0458C8/0x045970 | R1 seg 9/13 (0x45xxx dispatch) | 1 | A5+0x264 / 0x25A | — | — | R1 (Demon) |

## Boss route → round
Bosses are the **round-tail** scripted paired actors (0x13E near each round boundary): R3 via 0x41,
R4 via 0x58, R5 via 0x71, R6 via 0x86; R1/R2 boss routes are in the R1/R2 dispatch families (Demon is
a distinct R1 scripted enemy, not the R1 boss). **All 6 rounds have a boss route region proven;** the
exact per-boss seed→base-graphics (which mode2_variant) is still PARTIAL.

## Honest status
- Scripted routes assigned to **round: proven** (via 0x13E dispatch) for the R3 chain in full; R4–R6
  by dispatch value/family; R1 demon proven.
- Scripted routes assigned to **outdoor vs castle: UNKNOWN** (needs the section-type decode).
- Boss route → round: **6/6**; boss identity (base graphics): PARTIAL.
