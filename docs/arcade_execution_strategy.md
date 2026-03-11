# Arcade 68000 Execution Strategy

This note captures the current pivot:

- stop treating the first milestone as "find the exact player sprite"
- start treating the first milestone as "get the arcade `68000` gameplay code
  executing inside a Genesis-side compatibility layer"

## Short version

The arcade `68000` program will not run unchanged on a Genesis just because the
CPU core is similar.

It still depends on:

- arcade memory map layout
- interrupt timing
- custom video hardware registers and RAM behavior
- sound CPU / latch behavior
- tilemap/sprite chip semantics
- startup/reset/vector assumptions

So the realistic target is not:

- "drop the arcade ROM in and execute it raw"

The realistic target is:

- relocate or reassemble the arcade `68000` code into a Genesis ROM image
- provide a compatibility layer that makes the code believe it is talking to
  the original hardware
- progressively replace or shim each hardware-facing path

## What should be treated as separate layers

### 1. Arcade logic layer

This is the original `68000` gameplay code and data:

- actor/state logic
- collision
- scoring
- stage progression
- animation/state selection

This is the part we want to preserve as much as possible.

### 2. Hardware shim layer

This is the translation layer that stands between arcade code and Genesis
hardware.

Its job is to emulate or translate:

- memory-mapped I/O reads/writes
- interrupts
- input ports
- video/tile/sprite RAM behavior
- sound commands

### 3. Genesis backend

This is the actual SGDK / Genesis-side implementation:

- VDP writes
- VRAM/CRAM/VSRAM management
- joypad reads
- Z80 sound communication
- DMA, frame pacing, vblank handling

## The right mental model

Treat the arcade `68000` program like a game-specific firmware blob that needs
an adapter board.

The Genesis is not "the same machine with different addresses."
It is "close enough in CPU family that a compatibility layer is plausible."

## What can probably stay close to original

- core `68000` gameplay logic
- many RAM-resident state machines
- object update code
- high-level animation selection
- map/object scripting

## What will definitely need translation

### Memory map

Arcade addresses used by the original code will need to map onto:

- Genesis work RAM
- compatibility-owned shadow RAM
- VDP command/data interfaces
- emulated hardware state blocks

### Video hardware

The arcade code expects dedicated tilemap/sprite hardware behavior.
Genesis has:

- VDP VRAM/CRAM/VSRAM
- sprite attribute table
- plane/tilemap model
- different DMA/update constraints

So we need shadow structures that look arcade-like to the game code, then a
translator that emits Genesis VDP state each frame.

### Audio

The arcade program expects:

- separate audio CPU behavior
- command latches / handshake rules

Genesis has:

- `68000 -> Z80` communication
- YM2612 + PSG through a different driver model

So we likely need a sound-command shim, not a direct hardware mapping.

### Interrupts / timing

Even if the gameplay logic is portable, timing-sensitive code may assume:

- original vblank/irq cadence
- watchdog or scheduler details
- hardware busy timing

This means the shim needs a deliberate frame model.

## Practical first milestone

Do **not** start with graphics-perfect output.

Start with a minimal execution harness that proves we can run selected arcade
logic safely on Genesis-side memory and observe hardware accesses.

That milestone should do this:

1. Boot on Genesis.
2. Initialize a compatibility-owned RAM map.
3. Load or embed a test slice of arcade `68000` code/data.
4. Expose stubbed read/write entry points for hardware-facing addresses.
5. Log or count which hardware regions the code touches.
6. Present a simple on-screen debug view.

If that works, then we know the approach is viable.

## Recommended implementation order

### Phase 1: compatibility map

Define:

- arcade ROM regions
- arcade RAM regions
- known MMIO ranges
- which ranges can be backed by Genesis RAM directly
- which ranges must be trapped/shimmed

### Phase 2: execution harness

Create a Genesis-side runtime that:

- owns a large shadow memory block
- exposes helper functions for emulated reads/writes
- can call selected translated arcade routines

### Phase 3: video shadow backend

Build arcade-style shadow state for:

- sprite attribute RAM
- tilemap RAM
- palette RAM or palette-like state

Then translate that shadow state into VDP writes.

### Phase 4: sound command shim

Trap the sound-facing arcade writes and forward them into:

- a placeholder Genesis sound command queue first
- then a real Z80/driver implementation later

### Phase 5: frame loop integration

Run the arcade update path once per frame under Genesis timing and confirm:

- stable state progression
- stable memory accesses
- deterministic hardware-shim behavior

## Immediate next coding target

The next useful code is:

- a Genesis compatibility harness
- not more sprite guessing

Specifically:

- create a new sample or runtime target that boots on Genesis
- allocate shadow RAM for the arcade-side state
- add a trap table / dispatch layer for known arcade MMIO regions
- render a debug HUD showing accessed addresses/counters

That will tell us very quickly whether "run the arcade code through a Genesis
shim" is practical for this project.
