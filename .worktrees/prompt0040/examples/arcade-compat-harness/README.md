# Arcade Compat Harness

This sample is the first Genesis-side compatibility scaffold for running slices
of the arcade `68000` code.

What it does now:

- boots on Genesis with SGDK
- loads the real Rastan main `68000` ROM region into the Genesis build
- allocates a shadow RAM window for arcade work RAM
- exposes arcade-style `read8/read16/write8/write16` helpers
- classifies accesses into ROM, RAM, input, sound, video, and unknown regions
- shows live counters, startup vectors, and watched startup globals on screen
- lets you exercise the known stage-start slice:
  - `A`: apply known stage-entry defaults
  - `B`: load the scripted drop coordinates (`160,128`)
  - `C`: copy staged drop coordinates into live player coordinates
  - `START`: reset shadow RAM and counters

What it does not do yet:

- execute original arcade `68000` code
- translate arcade sprite/tile state to the Genesis VDP
- emulate arcade interrupts or sound CPU behavior

Build:

```bash
source /home/tighe/projects/rastan-genesis/tools/setup_env.sh
make -C /home/tighe/projects/rastan-genesis/examples/arcade-compat-harness
```

Output ROM:

- [rom.bin](/home/tighe/projects/rastan-genesis/examples/arcade-compat-harness/out/rom.bin)

The build depends on `build/regions/maincpu.bin`, which the `Makefile`
regenerates automatically from the local `roms/` set.
