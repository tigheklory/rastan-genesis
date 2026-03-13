# Genesistan

`Genesistan` is the new work area for the stricter porting approach:

- keep original arcade `68000` opcodes wherever feasible
- patch absolute addresses and MMIO targets at build time
- convert graphics/tile data into Genesis VDP-ready assets ahead of runtime
- keep Genesis-side code focused on hardware shims, not gameplay rewrites

This directory exists specifically to avoid pushing the older harness further in
the wrong direction. `examples/arcade-compat-harness` remains useful as a
reverse-engineering notebook and display experiment, but `Genesistan` is where
the static translation pipeline should live.

## Intended flow

1. Extract canonical arcade regions into `build/regions/`.
2. Run the patch pipeline on the original arcade `maincpu` program.
3. Emit:
   - patched `68000` code blob
   - patch / relocation manifest
   - converted text / tile / sprite assets
4. Link the patched blob into a Genesis runtime that exposes remapped memory,
   VDP, input, and sound entry points.
5. Jump into original patched code instead of rebuilding behavior in C.

## Layout

- `docs/`: translation and memory-map notes specific to this approach
- `tools/`: patch/build-time translation scripts
- `runtime/`: Genesis-side loader / shim code for the translated blob
- `Makefile`: reproducible entry point for the patch pipeline

## Current status

This is still a scaffold, but it is now the canonical place for the
compile-time translation work. No original Rastan arcade opcodes are executing
from `Genesistan` yet.

## First command

```bash
make -C Genesistan patch-maincpu
```

That currently emits an unchanged copy of `build/regions/maincpu.bin` plus a
structured manifest proving the pipeline ran. The next step is to replace that
no-op pass with real address and MMIO patch rules.
