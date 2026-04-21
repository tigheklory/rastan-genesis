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

Arcade logic → WRAM buffers → VBlank commit → VDP

### Steps

1. Arcade code writes to WRAM buffers (translated intent)
2. Dirty flags indicate changes
3. VBlank triggers commit
4. Genesis writes to VDP

---

## Key Components

### Arcade Code
- Owns logic, timing, and control flow
- Calls helper routines for hardware interaction

---

### WRAM Buffers
- Staging area for graphics and state
- Written by arcade code
- Read during VBlank commit

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

## Forbidden Patterns

- Genesis-owned main loop
- Re-entry into boot/init during gameplay
- Separate lifecycle systems
- Test scaffolding
- Control-flow wrappers around arcade logic

---

## Summary

The arcade code is the system.

The Genesis executes it.

No separation of ownership is allowed.