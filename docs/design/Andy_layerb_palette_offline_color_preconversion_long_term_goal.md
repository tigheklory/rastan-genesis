# Layer-B palette offline color pre-conversion — long-term goal

**FUTURE WORK — NOT IMPLEMENTED BY PROMT-ID-0131.**

**Author:** Andy · **Date:** 2026-11-12 · **Type:** design intent only. No production code in this build
implements any of the following. The current runtime arcade→Genesis color conversion is retained unchanged.

## Current runtime color-conversion path (what exists today)

The retained original arcade program decides *which* Layer-B palette is active, *when* it changes, and
*which* row/frame is selected. The Genesis port keeps that decision logic and translates only the resulting
color write:

```
original arcade palette selector / sequencer   (retained: FUN_00059de8 gated on a5@0x13b0, indexed a5@0x118;
        |                                        FUN_00055c22 sets the reload flag; water/anim sequencers)
        v
per-stage / per-frame arcade color source       (ROM tables, e.g. the per-stage outdoor palette pointers)
        |
        v
genesistan_palette_hook_59ad4                    (apps/rastan-direct/src/palette_hooks.s)
   - routes arcade bank -> Genesis CRAM line (Layer-B bank -> Line 2)
   - converts each entry xBGR-555 -> Genesis CRAM via .Lxbgr555_to_cram  (per-entry 68000 arithmetic)
   - change-detected stage into staged_palette_words (Line 2)
        |
        v
VBlank CRAM publication                           (staged_palette_words -> 0x200000 / CRAM)
```

Every palette update therefore re-runs the `.Lxbgr555_to_cram` channel conversion on the 68000, per entry,
per update, for the life of the game — including for color rows whose values are fixed ROM data that never
change at runtime.

## The optimization goal

For Layer-B palette rows/frames whose color values are **finite and known from ROM data at build time**,
Python should pre-convert those color values to Genesis-native CRAM words once, offline:

```
arcade palette ROM tables  --(Python, build time)-->  pre-converted Genesis-native CRAM rows
```

Runtime would then preserve ONLY the original arcade **selection / timing / state** semantics and replace the
per-entry conversion with a copy:

```
original arcade logic selects palette / row / frame   (unchanged)
        |
        v
look up the corresponding pre-converted Genesis-native CRAM row   (no per-entry xBGR conversion)
        |
        v
copy / stage Genesis-native words -> Line 2 -> VBlank publication
```

This removes repeated color-depth/channel arithmetic from the 68000 while preserving identical visible
behavior, because the *selection and timing* stay in the retained arcade program.

### Candidate deterministic sequences to cover
- R1-S1 progression / sky palette changes (segment/progression-dependent, deterministic).
- Fixed-cadence water-animation palette frames (the type-9 waterfall route in `palette_hooks.s`, arcade water
  banks 0x1A–0x1D, frame index supplied by the arcade timing).
- Analogous later-round Layer-B palette sequences where the source colors are ROM-defined.

## Important distinction — not everything can be pre-converted

Do **not** assume every palette operation reduces to a ROM table lookup. If the original game
mathematically **synthesizes / interpolates / fades** colors at runtime (e.g. a fade-to-black over N frames),
the source colors are not finite ROM rows and a naive pre-conversion is wrong. Options for those cases,
analyzed separately when the time comes:
- pre-computed fade/interpolation tables **when the state space is genuinely finite** (e.g. a fixed-length
  fade with known endpoints → N pre-converted rows);
- a Genesis-native translation of the arcade color arithmetic **when it is truly dynamic**.

A fade such as the Plane-A loader's `0x45d7c` path is an example that needs this separate analysis before any
pre-conversion is attempted.

## Why this is deferred
Pre-converting color contents is an efficiency change to the live palette system. It must not be bundled with
a correctness fix, and it requires per-sequence proof that each candidate row set is finite ROM data (not
runtime-synthesized). Doing it now would risk freezing a dynamic sequence or mis-translating a fade. The
current build (PROMT-ID-0131) deliberately retains the existing runtime conversion and changes only the
offline **tile attribute** (palette-line selection) artifact — a separate system from palette color contents.

## Scope boundary (explicit)
- This document records intent only.
- No change in this build pre-converts any palette color row.
- The runtime `genesistan_palette_hook_59ad4` conversion remains the authority for Layer-B color contents.

`FUTURE WORK — NOT IMPLEMENTED BY PROMT-ID-0131.`
