# Translation Plan

## Goal

Run patched original Rastan arcade `68000` code on Genesis with the smallest possible semantic drift.

## Rules

- Patch at build time, not in hot runtime loops, wherever possible.
- Treat gameplay/state logic as original code to preserve.
- Treat hardware-facing accesses as remap points.
- Prefer deterministic manifests over ad-hoc handwritten patches.
- Do not add presentation-only stand-ins here. If a step does not survive into
  the final translation pipeline, it does not belong in a throwaway example.

## First deliverables

1. `maincpu` static patch manifest
   - absolute ROM->Genesis address rewrites
   - MMIO trap targets
   - known vector / startup redirections
2. text/title layer conversion
   - `pc080sn` data extraction
   - tile/glyph mapping for `0xC08000` shadow layer
3. startup/title execution slice
   - original code block copied and entered from Genesis
   - remapped reads/writes for input, text RAM, and status memory

## Initial patch classes

1. Absolute RAM remaps
   - arcade work RAM anchors
   - fixed hardware RAM windows
2. MMIO callouts
   - input ports
   - video chip registers / RAM windows
   - sound command ports
   - watchdog / board-control writes
3. Control-flow redirections
   - startup entry handoff
   - interrupt / exception vector handoff where Genesis must mediate
4. Asset-side rewrites
   - text/tile tables converted to Genesis-ready resources
   - sprite/tile indices remapped if the VDP tile layout demands it

## Persistent metadata that must be tracked

- stable origin-address symbols
- extracted object/slice membership
- fixups and their rationale
- runtime configuration such as software DIP defaults and control mapping
- graphics and palette conversion rules
- audio conversion rules
- validation checks tied to known arcade behavior

## Near-term blockers

- identify safe code slice boundaries for direct opcode execution
- classify absolute address loads in startup/title code
- decide how translated code calls Genesis shim routines
- classify pointer-table data that must be patched alongside executable code

## Immediate next proof target

The first honest execution slice should be the common startup and basic
hardware-test entry block that runs on every boot:

- `0x3AE86`
- `0x3B04E`
- `0x3B05C`

This block matters because it is literally the first substantial code the
arcade machine executes after the reset vector handoff, and it already proved
useful in the harness.

Important scope rule:

- include the common startup path and the normal/test split point
- do not treat the detailed DIP-selected test program at `0x0100` as the first
  target

## First post-startup target

Once that startup block is entering cleanly, the next narrow execution slice
should be the startup/title text path:

- `0x3B098`
- `0x3BB48`
- `0x3C2E2`

Those routines already proved valuable in the harness, and they are narrow
enough to validate text/tile writes without dragging the whole gameplay loop in
immediately.
