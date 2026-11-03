# PROJECT_STORY.md

## Rastan → Sega Genesis Opcode Translation Project

---

## 1. Purpose

This project aims to port the arcade version of **Rastan** to the Sega Genesis using an **opcode-level translation approach**, preserving original game logic, timing, and behavior while adapting graphics and hardware interactions to the Genesis platform.

The goal is not a traditional rewrite, but a **faithful execution of arcade code** with a translation layer that maps arcade hardware intent to Genesis capabilities.

---

## 2. Original Strategy

Initial approach:

- Run translated arcade opcodes directly on Genesis
- Preserve:
  - game logic
  - timing
  - memory structures
- Replace:
  - hardware interactions (graphics, sound, input)

### Assumption

> Direct opcode mapping would “mostly work” if hardware differences were patched.

### Reality

This assumption was incorrect.

---

## 3. Early Problems

Initial system behavior:

- Game booted
- No real graphics rendered
- CRAM often zero
- VRAM partially populated but unused
- Sprite system non-functional

### Key Issue

> Arcade graphics logic does not translate directly to Genesis hardware.

Arcade used:

- **PC0900J** → sprites
- **PC080SN** → tilemaps

Genesis uses:

- **VDP (Video Display Processor)**

There is no direct compatibility.

---

## 4. Key Realization: "Graphics Intent" vs "Graphics Execution"

We discovered:

> Arcade code expresses *graphics intent*, not final hardware commands.

Examples:

- Writes to sprite RAM ≠ draw sprite
- Writes to tile RAM ≠ display tile
- Palette writes ≠ CRAM updates

### Translation Requirement

We must convert:

```
Arcade intent → Genesis VDP operations
```

---

## 5. First Functional Pipeline

We built an initial pipeline:

```
Arcade producer
    ↓
Block-A (WRAM sprite descriptors)
    ↓
C renderer (genesistan_render_sprites_vdp)
    ↓
SAT staging (vdpSpriteCache)
    ↓
VDP DMA
```

### Achievements

- Block-A builder restored
- Valid sprite tuples observed
- SAT staging confirmed
- DMA confirmed
- VDP sprite table populated

### Result

> Pipeline works end-to-end, but no visible graphics yet

---

## 6. Major Debugging Milestones

### 6.1 Ordering Bug

Renderer executed before producer.

Fix:
- Swapped execution order in title init state

---

### 6.2 D-7 Missing Builder Logic

Block-A content generation was missing.

Fix:
- Restored full builder entry at `0x05A2B4`

---

### 6.3 Attribute Bug (Hidden Sprites)

Incorrect logic:

```c
if (word0 == 0) y = 0x0180;
```

Reality:
- `word0 = 0` is valid arcade data

Fix:
- Use full tuple validity check

---

### 6.4 SAT Publish Failure

Observed:

- SAT staging correct
- VRAM empty

Root cause:
- renderer only executed a few times

Fix:
- forced per-vblank execution (temporary)

---

## 7. Current State

### Confirmed Working

- Arcade vblank execution (level-5)
- Producer pipeline
- Block-A contents
- SAT staging
- VDP DMA
- Sprite table population

### Not Yet Working

- Visible sprite output
- Tile correctness
- Palette correctness
- Final rendering architecture

---

## 8. Architectural Shift

We transitioned from:

### ❌ Temporary Model

- C-based renderer owns graphics
- Mixed ownership (SGDK + arcade)

### ✅ Target Model

- Arcade vblank owns frame execution
- Opcode/ROM-side logic produces graphics state
- Genesis-specific commit happens inside vblank

---

## 9. Final Architecture Vision

### Frame Flow

```
Arcade vblank (level-5)
    ↓
Game logic + producers
    ↓
WRAM buffers (Block-A, tile queues, etc.)
    ↓
Genesis commit stage (inside vblank)
    ↓
VDP (DMA / registers)
```

### Key Principles

- Single frame owner: **arcade vblank**
- No SGDK post-launch rendering ownership
- No long-term C renderer
- Hardware abstraction via translation, not replacement

---

## 10. Role of genesistan_render_sprites_vdp()

Current role:

- Temporary bridge
- Validates pipeline
- Confirms sprite system works

Future:

> Must be removed

---

## 11. Migration Plan

### Phase 1 — Stabilization (DONE)

- Block-A → SAT → VDP pipeline proven
- Per-vblank execution stabilized

---

### Phase 2 — Responsibility Split (NEXT)

- Separate:
  - SAT formation
  - SAT publish
- Move publish into arcade-vblank-owned code

---

### Phase 3 — Opcode / ROM Migration

- Move:
  - Block scan
  - validity
  - SAT formation

Into:

- ROM-side / assembly / translated opcode paths

---

### Phase 4 — Remove C Renderer

- Delete `genesistan_render_sprites_vdp()`
- No helper-based rendering remains

---

## 12. Lessons Learned

### 12.1 Opcode Translation Alone Is Not Enough

- Hardware must be translated, not assumed

---

### 12.2 Graphics Is a Pipeline, Not a Call

- Producer → staging → commit

---

### 12.3 Frame Ownership Is Critical

- Dual ownership causes undefined behavior

---

### 12.4 Debugging Too Early Wastes Time

- Must build real pipeline before fine debugging

---

### 12.5 Temporary Systems Are Useful — But Dangerous

- Good for validation
- Must be removed deliberately

---

## 13. Comparison to Taito Ports (Rainbow Islands / Cadash)

Observed patterns:

- Logic preserved
- Hardware interactions rewritten
- Frame execution centralized
- Graphics staged before commit

### Key Insight

> Successful ports separate **intent generation** from **hardware execution**

This matches our architecture direction.

---

## 14. Crash Handling Strategy

- Custom exception system already implemented
- Captures:
  - registers
  - PC
  - stack
  - backtrace
- Disables interrupts safely
- Does not depend on SGDK

### Decision

> Keep existing system — no changes required

---

## 15. Current Focus

We are no longer:

- debugging individual sprite issues
- testing visibility hacks
- experimenting with hybrid systems

We are now:

> Implementing the real graphics architecture

---

## 16. Immediate Next Step

- Begin **first real replacement slice**
- Move responsibility out of C helper
- Extend arcade-vblank-owned commit path
- Keep scope tight and controlled

---

## 17. Long-Term Goal

A system where:

- Arcade code runs natively (translated opcodes)
- All graphics are produced via original logic
- Genesis hardware is driven via translated intent
- No dependency on temporary scaffolding

---

## 18. Final Vision

> A faithful, opcode-driven Rastan port on Genesis, where the original arcade game logic runs unmodified in spirit, and the Genesis hardware executes its intent through a clean, deterministic translation pipeline.

---