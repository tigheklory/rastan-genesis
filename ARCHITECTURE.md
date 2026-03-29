# ARCHITECTURE.md

## System Overview

The system is designed around preserving arcade execution while translating hardware behavior to the Sega Genesis.

### Core Principle

Arcade code produces intent. Genesis executes it.

---

## Frame Ownership

- Single owner: Arcade level-5 vblank
- No SGDK post-launch ownership

---

## Pipeline

Arcade logic → WRAM buffers → VBlank commit → VDP

---

## Key Components

- Block-A: sprite descriptors
- VDP: Genesis graphics hardware
- DMA: transfer mechanism

---

## Goals

- Deterministic execution
- Minimal abstraction leakage
