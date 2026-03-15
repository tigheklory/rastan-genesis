# Variant Reference

This note documents the maincpu program variants currently identifiable from the
ROM files in `roms/`.

## Current default

The project currently builds from:

- `world_rev1`
- title: `Rastan`

Near-term support policy:

- keep `world_rev1` as the active target
- keep `us_rev1` easy to build from the same pipeline
- reserve `japan_rev1` for future explicit work without assuming it is trivial

This is the set assembled from:

- `b04-38.19`
- `b04-37.7`
- `b04-40.20`
- `b04-39.8`
- `b04-42.21`
- `b04-43-1.9`

## Identified program variants

The current folder supports at least these six cleanly assembled `maincpu`
variants:

- `world_rev1`
- `world`
- `us_rev1`
- `us`
- `japan_rev1`
- `japan_earlier`

The machine-readable source of truth is:

- [variants.json](/home/tighe/projects/rastan-genesis/specs/variants.json)
- [extraction_manifest.json](/home/tighe/projects/rastan-genesis/specs/extraction_manifest.json)

## How extensive are the differences?

### World Rev 1 vs World earlier

- only `2` bytes differ
- both differences sit in the `0x40000..0x4FFFF` bank

This looks like a minimal revision bump, not a broad code divergence.

### US Rev 1 vs US earlier

- only `2` bytes differ
- same shape as the World revision pair

This also looks like a minimal revision bump.

### World Rev 1 vs US Rev 1

- `26` bytes differ total
- `25` bytes are in `0x30000..0x3FFFF`
- `1` byte is at `0x05FFFF`

The major visible difference is a title/copyright string swap:

- World Rev 1 contains `1987 TAITO CORPORATION JAPAN`
- US Rev 1 contains `TAITO AMERICA CORP. 1987`

So World vs US is currently a very small code/data delta, not a distinct code
base.

Important correction:

- `2` bytes is the size of the revision delta within World or within US
- `26` bytes is the size of the World Rev 1 vs US Rev 1 delta

### Japan Rev 1 vs Japan earlier

- `282` bytes differ
- all measured differences are in `0x30000..0x3FFFF`

This is still relatively small, but it is much more substantial than the
2-byte World/US revision bumps.

### World Rev 1 vs Japan Rev 1

- `131,796` bytes differ
- about `33.5%` of the assembled `maincpu` program image differs

This is a major divergence. The Japanese program is not just a renamed title
screen.

## Known behavior differences

External reference material reports that `Rastan Saga` (Japan) differs in
at least some attract/gameplay presentation:

- item descriptions in the attract mode are replaced by an intro screen
- the game spawns fewer bats when the player stalls

This was noted in GamesDatabase's MAME entry for the Japanese set.

Sources:

- World/US/Japan clone pages in the MAME/GameDB ecosystem:
  - https://www.gamesdatabase.org/game/arcade/rastan
  - https://www.gamesdatabase.org/Media/SYSTEM/Arcade/Title/big/Rastan_Saga_-_1987_-_Taito_Corporation.jpg

These are useful hints, but the local binary deltas above are the stronger
evidence for build planning.

## Translation policy implication

The port should support variants explicitly rather than assuming one program
fits all.

Practical consequence:

- keep `world_rev1` as the current default
- make all extraction/build steps variant-aware
- treat `us_rev1` as the first alternate target to keep working
- do not mix rules derived from `world_rev1` into `japan_rev1` without marking
  the variant scope
- allow shared rules where the byte-identical ranges justify it
