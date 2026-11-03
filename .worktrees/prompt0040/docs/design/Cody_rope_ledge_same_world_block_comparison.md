# Cody — Rope ledge same-world-block comparison

**Date:** 2026-09-24  
**Task type:** Corrected focused evidence analysis; no implementation  
**Genesis baseline:** Build 0373  
**Build produced:** None  
**Production source/spec changes:** None

## Result

Tighe's two `USER_MARK` events identify the same intended rope-side location. The earlier
conclusion that they represented different human locations is **retracted**.

At the ORIGINAL ARCADE marker, the relevant 4×4 terrain block is logical rows **36–39** and
columns **48–51**. At the GENESIS NTSC Build-0373 marker, that same world block is rows 36–39 and
columns 48–51—one complete 32-pixel block above the player's row-40 landing position. The
Genesis player being four 8-pixel rows lower is evidence of the reported missing ledge, not a
marker-location mismatch.

The existing evidence proves that the retained source entry, relocated runtime source entry,
descriptor, all 16 source tile words, and all 16 descriptor collision words agree. The human
Genesis trace directly captured only six of the target block's 16 live collision/staging cells;
all six agree with the descriptor and contain nonzero staged Plane-A words. It did not capture
the other ten target cells. Its exposed MAME VRAM reads are not a usable publication oracle,
because the same interface reports zero for visibly correct control terrain.

Consequently, the first failing source-to-publication boundary is **not proven by the existing
captures**. No patch or build is justified from this evidence.

## Scope and tool reuse

Existing project tools reused:

- `tools/mame/scripts/rastan_arcade_rope_ledge_human_trace.lua`
- `tools/mame/scripts/rastan_genesis_rope_ledge_human_trace.lua`
- the completed ORIGINAL ARCADE and GENESIS NTSC Build-0373 human captures
- canonical Ghidra exports in `analysis/ghidra/rastan_arcade/exports/`
- `build/regions/maincpu.bin` as the reconstructed original arcade ROM authority
- preserved Build-0373 ROM and its generated native symbols

New tooling created: **None**.

Why new tooling was necessary: **Not applicable**. The task explicitly prohibited a new trace
and was completed as far as the existing evidence permits.

No automated gameplay, new human trace, broad map investigation, production patch, or ROM build
was performed.

## USER_MARK normalization

| Field | ORIGINAL ARCADE | GENESIS NTSC Build 0373 | Interpretation |
|---|---:|---:|---|
| marker frame | 1845 | 1948 | capture-local frame numbers |
| `A5+0x013E` | `0x0003` | `0x0003` | equal |
| `A5+0x10A8` | `0x0000` | `0x0000` | equal |
| `A5+0x10CA` | `0x0000` | `0x0000` | equal |
| `A5+0x10CC` | `0x0003` | `0x0003` | equal |
| foreground X | `0x0107` | `0x0107` | equal |
| foreground Y | `0x0149` | `0x0129` | Genesis camera followed a player 32 pixels lower |
| raw player screen Y | `0x0070` | `0x0070` | equal before presentation normalization |
| player logical row | 36 | 40 | Genesis is four rows / 32 pixels lower |
| player logical column | 48 | 48 | same logical column |

The known Genesis eight-pixel vertical presentation adjustment applies only when comparing the
displayed screen positions. It is normalized as a presentation offset and is **not** added to or
subtracted from the world/map row. The same-world target remains rows 36–39, columns 48–51.

## Exact arcade support block

The arcade marker places the player in logical row 36, column 48. Aligning those coordinates to
the 4×4 terrain-block boundary selects:

```text
logical rows:       36, 37, 38, 39
logical columns:    48, 49, 50, 51
row group:          9
column block:       12
live row source:    0x02A2A8
source delta:       -7 records
source entry:       0x02A28C
descriptor word 0: 0x0003
metatile pointer:   0x3408
```

This is re-derived from the human arcade marker. Neither earlier candidate is treated as
authoritative.

## Correction to the arcade trace's `metatile_cell` field

The arcade TSV's `metatile_cell` values `0x01F6` through `0x0200` for this record are not the
descriptor's tile words. The trace script computed them as `0x200 + metatile + cell_offset`.
That relocation bias is valid when dereferencing the copied ROM in Genesis, but not in the
original arcade address space.

Canonical Ghidra static proof:

- arcade `0x055904` reads descriptor word 1, zero-extends it, builds `A4 = 0 + word1`, and stores
  that raw pointer;
- arcade `0x0559B2` reads visual words from `A2 + cell_offset` and collision words from
  `A2 + 0x20 + cell_offset`.

Therefore original descriptor `0x3408` points directly to arcade ROM `0x3408`. In the Genesis
copy it correctly resolves at runtime ROM `0x3608` (`PC080SN_DESC_SECOND_WORD_BASE = 0x200`).
The copied descriptor record itself is at runtime `0x02A48C`.

## All 16 source tile and collision words

The canonical original ROM and preserved Build-0373 copied ROM contain identical data:

| Logical row | Columns 48, 49, 50, 51 — source tile words | Columns 48, 49, 50, 51 — collision words |
|---:|---|---|
| 36 | `0164 0165 0166 0167` | `0000 0000 0000 0000` |
| 37 | `0168 0169 016A 01B5` | `0000 0000 0000 0000` |
| 38 | `016C 017B 0196 01B7` | `3A00 3A00 3A00 3A00` |
| 39 | `0170 017E 017F 018C` | `0000 0000 0000 0000` |

Byte checks:

- original source record at `0x02A28C`: `0003 3408`
- Genesis runtime copied record at `0x02A48C`: `0003 3408`
- original descriptor at `0x3408..0x3447`: identical to Genesis copied descriptor at
  `0x3608..0x3647`

Thus there is no divergence at source selection, source-record relocation, descriptor selection,
source visual data, or descriptor collision data.

## Existing Genesis live evidence for the same block

The Genesis human script sampled rows 38–42 and columns 46–50 around the lower landing point.
That window overlaps six cells of the target block:

| Cell | retained source | runtime source | source tile | live collision | staged Plane-A |
|---|---:|---:|---:|---:|---:|
| row 38, col 48 | `02A28C` | `02A48C` | `016C` | `3A00` | `6375` |
| row 38, col 49 | `02A28C` | `02A48C` | `017B` | `3A00` | `633F` |
| row 38, col 50 | `02A28C` | `02A48C` | `0196` | `3A00` | `6355` |
| row 39, col 48 | `02A28C` | `02A48C` | `0170` | `0000` | `6325` |
| row 39, col 49 | `02A28C` | `02A48C` | `017E` | `0000` | `639C` |
| row 39, col 50 | `02A28C` | `02A48C` | `017F` | `0000` | `633D` |

All six sampled source/collision pairs match the corrected descriptor. All six staged name words
are nonzero. The remaining cells were outside the bounded human-trace window:

```text
rows 36–37, columns 48–51: not captured live
rows 38–39, column 51:     not captured live
```

Their source and descriptor contents are proven, but their live staged/collision destinations
cannot be represented as measured values from this trace.

## Publication boundary limitation

The six sampled physical Plane-A rows are 6 and 7 for logical rows 38 and 39. The Genesis trace
logged `0x0000` from MAME's exposed `:gen_vdp` `videoram` space for these cells. Existing focused
Build-0374 evidence already established that this interface also returns zero for visibly correct
neighbor terrain. Those zeroes therefore cannot prove that publication failed, and are not used
as final-VRAM evidence.

No corresponding final name-table destination was validly available from the existing human
capture for all 16 cells.

## Upstream-to-downstream comparison and stop point

| Boundary | Comparison result |
|---|---|
| same world/map coordinate | **MATCH** — rows 36–39, columns 48–51 |
| live row-source pointer | **MATCH** — `0x02A2A8` |
| retained source entry | **MATCH** — `0x02A28C` |
| Genesis runtime source entry | **CORRECTLY RELOCATED** — `0x02A48C` |
| descriptor/metatile | **MATCH** — `0x0003 / 0x3408` |
| 16 source tile words | **MATCH** in original and copied ROM |
| 16 descriptor collision words | **MATCH** in original and copied ROM |
| live Genesis collision cells | **MATCH for 6 captured cells; 10 not captured** |
| live Genesis Plane-A staging | **NONZERO for 6 captured cells; 10 not captured** |
| VBlank/final name-table publication | **NOT ESTABLISHED by a valid existing oracle** |

**First divergence:** not proven. The last complete matching boundary is the copied 16-word
source/collision descriptor. The last live matching boundary is the six-cell overlap in Genesis
collision plus Plane-A staging. The visual/gameplay symptom exists, but assigning it to staging,
publication, VRAM, overwrite, or collision without the missing measurements would be a guess.

## Architecture and production status

The relevant semantic cut remains retained arcade map/source/descriptor and collision intent to
direct native Genesis Plane-A staging/publication. The retired PC080SN name-RAM/chip-address tail
was not changed or reintroduced.

- Root cause proven: **NO**
- Production changes: **NONE**
- Build: **NONE**
- STOP: **YES** — no semantic fix is proven by the authorized evidence

