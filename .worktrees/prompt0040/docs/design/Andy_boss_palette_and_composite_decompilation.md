# Andy — Boss Palette-Load + Multi-Record Boss Decompilation

**Agent:** Andy · **Type:** Static RE (decompilation) + manifest/bestiary correction. **NO ROM/MAME/
Genesis.** Build counter 360. Cody files untouched. **Artifact:** republished (Version 7).

Mandatory RULES.md report. Two problems from the last review: (1) R3 boss colours wrong; (2) R6/R5
rendered body-only. This pass **decompiles** the palette-load and boss-component-creation code, and
**corrects the earlier false "PALETTE PROVEN" boss claim**. Authoritative source: `maincpu.bin`.

> **Honest scope:** the palette *loaders* and the boss *component structure* are decompiled to
> COMPLETE C. Two threads are **not** closed and are stated precisely: the exact boss line-F colour
> layout in the staged sprite palette, and the per-component relative-position math (0x43458). I did
> **not** guess purple colours or component offsets.

---

## A. Palette-load subsystem functions decompiled

- **0x3BA20 / 0x3BA56** (`raw/0003ba20.c`, COMPLETE): the scene sprite-palette load. For the current
  round it walks `0x3BA88 + (round-1)*32` (32 nibble→pool indices) and, per line, converts pool
  `0x4FD02 + pool*32`'s 16 ROM words into the working palette `A5+0x1600`. The ROM→CRAM conversion is
  the exact bit interleave `CRAM = (n0<<11)|(n1<<6)|(n2<<1)` (verified against 0x3BA56 **and**
  0x59ADE).
- **0x3B9FE** (COMPLETE): fills the staging buffer `0x200000` from the **master sprite palette
  `0x4EAF6`** (768 colours = 48 lines) plus pool 11 (`0x4FE62`).
- **0x45D7C** (COMPLETE): stages `0x200000 → A5+0x1600` in 8 fade steps.

## B. Boss palette-load functions decompiled

The working sprite palette is a **combination**: the per-round field table (0x3BA20) *and* the
master/staged source (0x3B9FE + 0x45D7C). Evidence: `analysis/actor_decompilation/boss_palette_loads.tsv`.

## C. Six boss palette ROM sources

The palette **line** for every boss body is **F** (proven: `0x3C9E8`, `+0x27=0`, and the compositor
program control bytes are all `0x0F`). The line-F **colours**, however, do **not** come from the
field pool `0x3BA88[round][0xF] → 0x4FD02`:

| Round | field pool at line F | field-pool colours | matches arcade boss? |
|---|---|---|---|
| R3 | pool 2 (0x4FD42) | teal/cyan ramp | **NO** (arcade boss is purple) |

So the field-pool source is **disproven** for the boss. The real colours arrive via the master/
staged path (`0x4EAF6 → 0x200000 → A5+0x1600`); the exact line-F slice within that staged buffer is
**not yet resolved** (0x4EAF6 line F read directly is grays/greens, so there is additional line
mapping/staging between `0x4EAF6` and the displayed CRAM line F).

## D. Round-3 palette explanation

The geometry/frame is correct (unchanged). The colours were wrong because the offline render used
`rom_field_palette(round, F)` = field pool 2 = teal, but the arcade boss's line F is supplied by the
sprite-palette staging path, not the field pool. **The fix is a real source change, not a screenshot
colour-match** — and the exact staged line-F content is the remaining blocker (§K), so R3 is rendered
**palette-neutral (grayscale) with colours PENDING** rather than with the wrong teal.

## E. Boss component-creation functions decompiled

- **0x423B2** (`raw/000423b2.c`, COMPLETE): Round-5 creates **5× rec_type 0x11** into `A5+0x5C8`
  (`+0x21=i`, `+0x00=1`, `+0x38=1`, `+0x05=0x11`, `+0x06=0x11`); `0x4543E` → base **0x0988** anim
  **0x89**.
- **0x423F4** (COMPLETE): Round-6 creates **4 records** into `A5+0x648`, `+0x06 = 0x17+i` → types
  0x17/0x18/0x19/0x1A → `0x4543E` bases **0x0B35 / 0x0AED / 0x0CCB / 0x0BEB** (anims 0x66/0x82/0x7C/
  0x30). Verified from the record-type table `0x45592`.

## F. Round-5 structural model

Five **identical** type-0x11 segments (base 0x0988, anim 0x89, compositor sel 1, state 0x11 → handler
0x4684E). They are structural body segments (not projectiles), positioned relative to the body by
`0x42380 → 0x43458`.

## G. Round-6 structural model

Four parts (`boss_structural_components.tsv`): type 0x17 = BODY (0x0B35, comp 2), type 0x18 = 0x0AED,
type 0x19 = 0x0CCB, type 0x1A = 0x0BEB. Together they compose the dragon. Body-only rendering was the
partial head/neck; the full dragon needs all four at their relative offsets.

## H. Component position/update semantics

`0x42380` (COMPLETE-read): copies body `+0x02` facing into each of the 5 (R5) parts and calls
`0x43458` with `d0 = 13 + index` — the **per-part relative positioner**. `0x43458`'s offset math (and
any position table it reads) is the remaining dependency for an exact offline composite; it is **not
yet decompiled** (§K). So component X/Y are PENDING; bases/anims/types are proven.

## I. Complete boss composite status 1–6

| Round | structure | body frame | palette colours | composite |
|---|---|---|---|---|
| R1 | single-record | proven (MAME-verified) | PENDING (staged source) | body only |
| R2 | single-record | static | PENDING | body only |
| R3 | single-record | static (geometry ok) | PENDING (field pool disproven) | body only |
| R4 | single-record | static | PENDING | body only |
| R5 | **multi (5× 0x11)** | proven | PENDING | parts decoded, positions PENDING |
| R6 | **multi (4 parts)** | static | PENDING | parts decoded, positions PENDING |

Complete normal-state composites rendered: **0/6** (structure + bases proven for the multi-record
bosses; positions and staged palette colours are the two open pieces).

## J. Raw / semantic C inventory

- `raw/0003ba20.c` (COMPLETE) — palette loader + convert + staging note.
- `raw/000423b2.c` (COMPLETE) — R5 + R6 component creators.
- `rastan_boss_composite.c` (semantic) — component model + palette-source correction.
- `function_coverage.csv` (+3 → 75 / 59 COMPLETE), `historical_claim_audit.csv` (+2 → 57), README.
- Evidence: `boss_palette_loads.tsv`, `boss_structural_components.tsv`.

## K. Remaining truly undecompiled functions

1. **The staged sprite-palette line-F layout** — how `0x4EAF6 → 0x200000 → A5+0x1600` maps to the
   displayed CRAM line F for the boss scene (the colour source). `0x3B9FE`/`0x45D7C` are lifted; the
   *line-index* of the boss's F within the staged buffer is the open piece.
2. **0x43458** — the per-component relative positioner (X/Y offset math / any position table).

Both are the exact next PCs; until then boss palette CONTENT and multi-record composites stay PARTIAL
(not fabricated). The false "PALETTE PROVEN (compositor F)" boss claim has been removed from the
manifest and bestiary (now "line F proven · colours PENDING"), and boss cards render palette-neutral.

## Validation

Coverage guard **PASS** (75 rows/59 COMPLETE); fidelity **PASS**; `gcc -fsyntax-only` **PASS** (78
files); manifest consistency **PASS**. No boss card claims field-pool colours as proven.
