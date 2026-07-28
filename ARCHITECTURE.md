# ARCHITECTURE.md

## System Overview

The system preserves arcade execution while translating hardware behavior to the Sega Genesis.

The arcade program is not wrapped, replaced, or controlled by a separate system.

It is transformed to run on Genesis hardware.

---

## Core Principle

Arcade code produces intent. Genesis executes it.

- Arcade code owns execution and timing
- Genesis code performs hardware operations only
- No dual-runtime model exists

---

## Execution Model

### Cold Boot

- Genesis initializes hardware
- Arcade program begins execution
- Control is handed to the arcade flow permanently

This happens once.

---

### Runtime

- Arcade code runs continuously
- All gameplay logic remains in arcade code
- Genesis code is invoked only when needed via helpers

There is no Genesis-owned loop.

---

## Frame Ownership

- Single owner: Arcade Level-5 VBlank
- Arcade code determines frame progression
- Genesis does not schedule frames

---

## VBlank Behavior

- Arcade VBlank is the controlling interrupt
- Genesis VBlank is used only to:
  - commit staged graphics data
  - execute DMA transfers

Genesis VBlank must not:
- run gameplay logic
- control execution flow

---

## Rendering Pipeline

```
arcade semantic decision
  → final Genesis-format staging or bounded VDP/SAT job
  → arcade-owned VBlank commit
  → Genesis VDP
```

### Steps

1. The arcade program makes the semantic decision (what graphics operation is required).
2. A native Genesis helper produces **final Genesis-format** staging or a bounded VDP/SAT
   job directly from that arcade semantic state.
3. Dirty flags / bounded job metadata indicate the pending commit.
4. The arcade-owned VBlank commits the staged final-format data / DMA jobs to the VDP.

### Permitted WRAM staging contents

Staging may hold only **final Genesis-format** data and bounded job metadata:

- final Genesis Plane A / Plane B name words;
- final Genesis SAT entries;
- final CRAM words;
- Genesis scroll values;
- bounded VDP/DMA job metadata.

It must **not** hold PC080SN/PC090OJ-shaped virtual hardware state, name-RAM / object-RAM
mirrors, generic chip-address writes, or projected chip state as the final architecture.
(Such structures may exist only as isolated, labeled, removable transitional compatibility —
see the Native PC080SN/PC090OJ Replacement section and
`docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`.)

---

## Key Components

### Arcade Code
- Owns logic, timing, and control flow
- Calls helper routines for hardware interaction

---

### WRAM Buffers
- Staging area for **final Genesis-format** graphics data + bounded job metadata
  (Plane A/B name words, SAT entries, CRAM words, scroll values, VDP/DMA job metadata)
- Written by native helpers from arcade semantic state; not a chip-shaped mirror
- Read during the arcade-owned VBlank commit

---

### VDP (Video Display Processor)
- Genesis graphics hardware
- Receives committed data only

---

### DMA
- Transfers data to VDP efficiently
- Triggered during VBlank

---

### Block-A
- Sprite descriptor structure from arcade
- Translated for Genesis sprite system

---

## Helper Functions

Genesis-side functions must:

- Be explicitly called from arcade code
- Perform a specific hardware task
- Return immediately (`RTS`)

They must not:
- loop
- block
- own control flow

---

## Design Goals

### Deterministic Execution
- Arcade logic must behave consistently
- No hidden scheduling layers

---

### Minimal Abstraction Leakage
- Arcade structures remain intact
- Translation is direct and explicit

---

### Hardware Fidelity
- Behavior should reflect original arcade intent
- Timing and sequencing must remain accurate

---

## Native PC080SN / PC090OJ Replacement

The graphics tail is made **native**, not emulated. The arcade program keeps the
high-level semantic decisions (scene/map/camera/scroll/source/descriptor/ring, the decision
to publish an entering row/column, logical cell identity, collision, and — for sprites —
actor lifecycle/position/priority/palette/flip/order). The Genesis helper cuts **before**
any PC080SN/PC090OJ-specific execution and generates **final Plane A/B name-table data or
final SAT entries directly** from that arcade semantic state.

The pipeline is `arcade semantic decision → native Genesis VDP/SAT realization`. It is
**not** `arcade chip operation → software chip representation → helper projects it → VDP`.
No software PC080SN/PC090OJ device, virtual chip RAM, C-window/name-RAM shadow, object-RAM
mirror, generic chip-address translation, or full-map projection is the final architecture;
any such structure is transitional compatibility only (isolated, labeled, removable).

**Canonical policy:** `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
(see also `RULES.md` §11).

---

## Forbidden Patterns

- Genesis-owned main loop
- Re-entry into boot/init during gameplay
- Separate lifecycle systems
- Test scaffolding
- Control-flow wrappers around arcade logic
- Software PC080SN/PC090OJ emulation, virtual chip RAM, C-window/name-RAM or object-RAM
  shadows/mirrors, generic chip-address translation, or full-map projection as the final
  design (see the Native PC080SN/PC090OJ Replacement section)

---

## Summary

The arcade code is the system.

The Genesis executes it.

No separation of ownership is allowed.