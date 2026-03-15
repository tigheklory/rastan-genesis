# ROM Source Reference

This project should document not only which filenames it expects, but also
which MAME-era set those files came from.

## Current provenance

The ROM files in this workspace were sourced from the user-provided Internet
Archive entry:

- `mame-0.221-roms-merged`
- set file: `rastan.zip`

Archive URL provided by the user:

- `https://ia803204.us.archive.org/view_archive.php?archive=/29/items/mame-0.221-roms-merged/rastan.zip`

So the current documented source set is:

- MAME `0.221`
- merged set style

## Important rule

Future builders should not trust the version label alone.

They should verify:

1. required filenames
2. per-file SHA-1 values
3. selected maincpu variant

The machine-readable source of truth is:

- [extraction_manifest.json](/home/tighe/projects/rastan-genesis/specs/extraction_manifest.json)

## Current support policy

- current target: `world_rev1`
- near-term alternate target: `us_rev1`
- reserved future target: `japan_rev1`

This means a builder using the same MAME-era merged set should still verify the
exact files for the chosen variant before assuming compatibility.
