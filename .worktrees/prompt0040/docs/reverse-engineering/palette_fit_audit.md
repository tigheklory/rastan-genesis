# Rastan Palette Fit Audit

This note is the first practical audit of how Rastan palette selection might
fit onto the Genesis VDP.

It is deliberately narrower than a full palette-RAM reconstruction.

What it answers:

- how repetitive the known gameplay-side palette selector tables are
- how many distinct attribute words the startup/title text path currently uses
- whether the Genesis `4 x 16` palette-line model looks plausible so far

What it does **not** answer yet:

- the final arcade palette RAM write path
- the final arcade palette RAM address map
- the exact per-scene RGB values active in gameplay

## Ground Truth

- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt)
- [4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt)
- [palette_application_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_application_reference.md)
- [startup_display_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/startup_display_reference.md)
- [mode_flow_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/mode_flow_reference.md)

## Genesis Constraint

The Genesis VDP:

- supports a `512`-color master space
- displays `64` palette entries at once
- arranges those as `4` palette lines of `16` colors each

So the real question is not whether Rastan exceeds Genesis RGB precision.

The real question is:

- how many distinct palette banks Rastan needs at once
- whether those banks can be packed into `PAL0..PAL3`

## Gameplay-Side Selector Table Audit

The clearest current selector tables are:

- `0x456ec`
- `0x45722`
- `0x4576a`

These are not final RGB tables.
They are table-driven palette / attribute selectors that feed `a4 + 0x27`
through `0x45684`.

### Default table `0x45722`

Rows in [4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt):

- players `1..4` are identical
- player `6` is also identical to `1..4`
- player `5` differs in only one entry

Distinct selector values used in the whole table:

- `01`
- `02`
- `04`
- `06`
- `07`
- `08`
- `0a`
- `0b`
- `0e`
- `0f`

Practical read:

- this is already highly repetitive
- it looks very consolidation-friendly

### Alternate table `0x4576a`

Rows in [4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt):

- all six rows are identical

Distinct selector values used:

- `01`
- `02`
- `04`
- `06`
- `07`
- `08`
- `0a`
- `0b`
- `0e`
- `0f`

Practical read:

- this is even cleaner than the default table
- it strongly suggests the alternate gameplay path is not exploding palette
  diversity

### Family-2 table `0x456ec`

This table is more varied, but it is still bounded.

Distinct selector values used:

- `00`
- `01`
- `02`
- `04`
- `05`
- `06`
- `07`
- `08`
- `0a`
- `0b`
- `0e`
- `0f`

Notable pattern:

- rows labeled `player 4`, `player 5`, and `player 6` are mostly built from the
  same repeating `12`-entry sequence blocks
- the first three rows are much sparser and contain many `00` entries

Practical read:

- even the more complicated special table is not showing runaway selector
  diversity
- current evidence still points toward a palette-bank model that may be
  tractable on Genesis

## Startup / Title Text Audit

The startup/title string writer:

- `0x3bb48`

uses records from the pointer table at:

- `0x3bb7c`

Each record includes:

- destination text RAM address
- attribute word
- message bytes

### Distinct attribute words in the first `71` message records

Current decoded set:

- `0x0000`
- `0x0001`
- `0x0002`
- `0x002e`
- `0x002f`

That is only `5` distinct attribute words across the whole startup/title text
message set.

Important clarification:

- these are startup/title text-record attribute words
- they are **not** palette RAM addresses
- they are **not** the full game's palette inventory

### Counts

- `0x0000`: `65` records
- `0x0001`: `2` records
- `0x0002`: `1` record
- `0x002e`: `2` records
- `0x002f`: `1` record

### Important front-end observations

All story/chronology attract lines currently checked use attribute `0x0000`:

- message ids `60..70`

Examples:

- `60`: `THIS IS A CHRONOLOGICAL`
- `61`: `HISTORY OF A BARBARIAN WHO`
- `62`: `DARED TO CHALLENGE.`
- `63..70`: story-page lines

Title/copyright-side examples also use `0x0000`:

- `12`: `@ TAITO AMERICA CORP. 1987`
- `30`: `@ 1987 TAITO CORPORATION JAPAN`
- `32`: `ALL RIGHTS RESERVED`

The non-zero attributes appear in a much smaller subset:

- `0x0001`
  - `SCORE ROUND NAME`
  - `ENTER YOUR INITIALS`
- `0x0002`
  - `SCORE  ROUND  NAME`
- `0x002e`
  - `TIME  09`
  - `INSERT COIN AND`
- `0x002f`
  - `TO CANCEL PUSH ATTACK BUTTON`

Practical read:

- the startup/title text side looks cheap in palette terms
- most of the visible text appears to share one attribute word
- the remaining front-end text variations look sparse enough that Genesis
  palette-line packing should be very plausible here

## What This Suggests About Consolidation

Good signs:

- gameplay-side selector tables are repetitive
- alternate table `0x4576a` is completely uniform across rows
- title/attract text uses only a small handful of attribute words
- attract/story text appears especially cheap in palette terms

Likely consolidation opportunities:

- identical selector rows in `0x45722`
- uniform rows in `0x4576a`
- repeated `12`-entry blocks in the family-2 table at `0x456ec`
- front-end text records sharing attribute `0x0000`

This matches the user observation that some enemies may be the same sprite art
with different palette application.

Current evidence is not enough to prove specific enemy families yet, but it is
consistent with that model.

## What We Still Do Not Have

We do **not** yet have:

- a full audit of final RGB colors per stage
- a full audit of title-screen object/background palette usage
- a proven palette RAM init/write trace for the custom hardware
- a scene-by-scene count of simultaneously live palette banks

So the current audit is:

- strong on selector-bank behavior
- weak on final hardware color state

For the first real color-table audit, also see:

- [palette_table_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_table_reference.md)

## Best Next Step

The next honest audit step is:

1. find the final arcade palette RAM write/init routines
2. tie those writes to:
   - title/front-end scenes
   - attract/story scenes
   - stage gameplay scenes
3. count simultaneously active palette banks per scene
4. then decide whether we can:
   - map them directly into Genesis `PAL0..PAL3`
   - or need dynamic repacking / scene-local consolidation
