# Hello Rastan

Small SGDK sprite test using a ROM-derived `Rastan` family-1 frame.

## Build

```bash
source ../../tools/setup_env.sh
make
```

Output ROM:

```bash
out/rom.bin
```

## Controls

- D-pad: move Rastan
- Start: return to center

## Asset source

Generate the sample sprite from the arcade ROMs with:

```bash
python3 ../../tools/extract_family1_frame.py
```

This follows the program ROM path through the family-1 frame table and writes:

```bash
res/sprite/rastan_family1_state15.png
../../build/family1_frames.txt
```

The rendered sample still uses a placeholder grayscale palette. The graphics and placement now come from the arcade ROM data selected by the 68000 code.
