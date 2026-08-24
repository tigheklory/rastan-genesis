# Cody — Offline Graphics Compiler Decoder Completion (proof work + exact remaining unknowns)

**Type:** static RE. No production runtime change, no ROM, Build 0302 not consumed. Compiler unchanged
(no fabricated decoders added). Stage-1 scope retained: **segments 0–15** (Andy M1B, arcade-derived).

## Honest status
Serious proof work was done; **real evidence was recovered** for gap 2, and gaps 1/3 were bounded to exact
missing structures. **None of the three decoders is fully closed**: each requires decompiling arcade routines
(not a trivial table read), and completing them from the current evidence would require inventing semantics —
which the source-of-truth rule and the task's STOP condition forbid. Reported precisely below.

## Gap 2 — arcade palette colours: PARTIAL (source + format + conversion found; ROM colour table NOT yet)
Proven from `analysis/ghidra/rastan_arcade/exports/{hw_refs.tsv,memory_map.md,decompiler_export.c}`:
- **Arcade palette RAM = `0x200000–0x200FFF`** (CLCS/Taito), **2048 words**, encoding **xBGR-555**
  (`x BBBBB GGGGG RRRRR`).
- `FUN_00000264` writes `0x200000` but is the **clear/init** (writes 0 / computed deltas), not the colour
  load.
- **Genesis conversion (derivable):** arcade 5-bit/channel → Genesis 3-bit/channel (`>>2`), Genesis CRAM word
  `0000 BBB0 GGG0 RRR0`.
- **Exact remaining unknown:** the **ROM palette colour table(s) + bank→offset arithmetic + the loader
  routine** that populates `0x200000` per scene/bank (which ROM address holds bank 0x33/0x36/FG/BG colours).
  Needs decompiling the palette-load routine(s) that read ROM and write `0x200000` — then the compiler can
  emit real `cram_epochs.bin` colour words via the conversion above. Until then CRAM colour contents remain
  `DECODER_SEMANTICS_UNPROVEN` (routing only, as M1B).

## Gap 1 — Plane-B stream: NOT CLOSED (exact unknown unchanged from M1B)
Missing: the tm0 (`0x3951C`→`0xD11C`) BG **tilemap column/row layout + scroll-position→visible-window
mapping** yielding the per-epoch BG working set (analogous to the FG strip-source walk). The whole-stage
854-tile set is decoded but doesn't fit as a constant. 320-slot placeholder retained.

## Gap 3 — PC090OJ coexistence: NOT CLOSED (exact unknown unchanged from M1B)
Missing: Stage-1 **object/enemy placement + spawn tables + object-availability↔map-position** decode (level/
enemy subsystem, `map_stream_format.md` §6 unresolved) → the *legal* per-epoch sprite palette-family set.
Registry provides banks 0x33 (Rastan/sword), 0x36 (lizardman), + unresolved families (bats/axe/four-armed).

## Why I did not fabricate
Adding a decoder that guessed the ROM palette table, the BG scroll mapping, or the legal sprite set would
inject invented semantics into the production compiler and produce wrong Genesis assets — worse than the
honest gap. Each of the three needs decompilation depth beyond this session; recommend a fresh RE session per
decoder, starting with the palette loader (highest visible value; palette RAM/format/conversion already
pinned above).

## Unchanged compiler results (Andy M1B, still valid): 7 epochs, Plane-A peak 552, combined 611/640,
patterns 64,960 B, largest transition 408/13,056 B, self-validation PASS, reproducible PASS, 0 trace deps.
