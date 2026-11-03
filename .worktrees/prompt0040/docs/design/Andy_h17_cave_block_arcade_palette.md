# Andy — H17: Exact Original-Arcade Cave-Block Display Palette

**Agent:** Andy · **Type:** Static RE (arcade palette proof). **NO Genesis impl · NO ROM build · NO
MAME · runtime build counter 373, unchanged.** Authoritative: `build/regions/maincpu.bin`.

> **Result — PROVEN EXACT ARCADE DISPLAY.** The Round-1 cave block's original-arcade palette is
> **pool 35 at ROM 0x50162** (logical sprite line 0xC, physical PC090OJ bank 0x3C). The block is a
> **BLACK + BROWN rocky block** — its tiles use only pool indices **{1, 7, 8, 9, 12, 13, 14}**
> (black + a brown/orange ramp), which matches the arcade screenshot. Cody's arcade *sources* (bank
> 0x3C, 0x3BA88[12]=35, pool 0x50162) are **CONFIRMED**; his Genesis Line-3 muddy reindex is
> **SUPERSEDED** for arcade truth.
>
> **Correction:** an earlier draft of this report mischaracterized the palette as a "gray stone
> ramp." That was wrong — it described the shared 16-color pool as a whole. The cave-block *tiles*
> only reference the black + brown indices; the gray pool entries (2,3,4,5,6,10,11) belong to other
> sprites on the same line and are never drawn by the block.

## A. Independently-proven arcade display path

The cave block is the target-'H' actor (marker 0x48 → state 0x1E), rendering base **0x0179** via
compositor selector 0, anim 0x70 → program **0x3E1C0**. That program's four pieces (tiles
0x0179/0x017A/0x017B/0x017C, arranged 2×2 by x/y deltas 0/240) **all carry control byte 0x0C** →
embedded palette **nibble 0xC**. This was found independently in H15 before consulting Cody.

Palette finalisation (0x3C9E8): the cave block is **marker-materialized** (0x41180→0x41362), which
never calls the palette-attribute resolver 0x45684 (that runs only via the field-schedule 0x4A086).
So **+0x27 = 0 (bit6 clear)** and 0x3C9E8 keeps the program control nibble unchanged → **logical
palette line 0xC**. +0x27 does **not** override here.

Physical line: sprite working lines publish to physical PC090OJ banks 0x30+line (working line 15 →
bank 0x3F, per 0x3BA20/0x45D7C publish), so logical line 0xC → **physical bank 0x3C**.

Round pool: `0x3BA88[(R1)*32 + 0xC]` at 0x3BA94 = **35 (0x23)** → pool source `0x4FD02 + 35*0x20` =
**0x50162** → 16 ROM words (0RGB, 4-bit/channel).

## B. Verify Cody's 0x3C / 0x50162 claim

| Cody claim | Verdict |
|---|---|
| effective PC090OJ bank **0x3C** | **CONFIRMED** — physical = 0x30 + logical line 0xC |
| **0x3BA88[12] = 35** | **CONFIRMED** — 0x3BA88[R1][0xC] = 35 (0x23) |
| candidate pool **0x50162** | **CONFIRMED** — 0x4FD02 + 35*0x20 = 0x50162 |
| source nibble **0xC** | **CONFIRMED** — program 0x3E1C0 control byte 0x0C in all 4 pieces |
| Genesis reindex 1→5/7→2/8→1/9→3/12→3/13→3/14→1 | **SUPERSEDED** (Genesis Line-3 muddy-ground fit; not the arcade appearance; not visually accepted) |

Cody's arcade *sources* are correct; the wrong visible color came entirely from the Genesis-side
reindex that collapsed the cave cells into the resident Layer-A muddy ground (Line 3). The arcade
uses pool 35 directly, with no reindex.

## C. Colors the block draws (finding only — exact values live in the registry, not here)

Decoding the block's tiles (`pc090oj.bin` 0x0179..0x017C, 16×16 4bpp) proves they reference **only**
pool-35 indices **{1, 7, 8, 9, 12, 13, 14}**: index 1 is black and the other six form a brown/orange
ramp — i.e. a **BLACK + BROWN rocky block**, matching the arcade screenshot. The remaining pool-35
indices (2,3,4,5,6,10,11 grays and 15 warm hilite) are shared-line colors other sprites use and the
cave block never draws.

> **Registry authority (RULES.md line 335 / CLAUDE.md "Canonical Palette-Decision Registry"):** the
> exact per-index arcade color values are deliberately **NOT restated in this Markdown report** —
> `specs/palette_decisions.json` is the project's only palette-decision registry, and reports cite
> IDs, they do not duplicate the mapping. Authoritative values: decision
> **`PAL-PC090OJ-STAGE1-CAVE-BLOCK-001`** (`arcade_display_palette_PROVEN_H17` + `used_indices`).
> Machine-readable evidence: `analysis/actor_decompilation/h17_cave_block_palette.tsv`.

## D. Registry

`specs/palette_decisions.json` decision `PAL-PC090OJ-STAGE1-CAVE-BLOCK-001` updated (same task): added
`arcade_display_palette_PROVEN_H17` (status PROVEN EXACT ARCADE DISPLAY + `used_indices`; the color
values live in the registry, not in this report) and a `known_defect` recording that the
`genesis_realization` Line-3 reindex is the wrong (non-arcade) color deferred to Andy. The Genesis
realization must reproduce pool 35, not collapse into the ground line. The registry is the sole
palette authority; this report only cites its ID.

## E. Status & remaining dependency

**PROVEN EXACT ARCADE DISPLAY** (Round-1). The proof is fully static: the palette line is baked into
the compositor program (control nibble 0xC), +0x27 does not override, and the round pool resolves to
0x50162 (values recorded in the registry decision, not restated here). Static decompilation yields a single palette interpretation, so no
visual disambiguation was needed. (Per-round note: line 0xC is fixed; other rounds would use
`0x3BA88[round][0xC]` — but the Stage-1 cave block is the Round-1 instance proven here.)

Validation: runtime build counter 373 → 373; no ROM/MAME/Genesis; registry JSON valid; result is the
arcade palette path, not Cody's Genesis reindex.
