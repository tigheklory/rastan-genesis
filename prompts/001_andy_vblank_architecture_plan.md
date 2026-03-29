# Prompt 001 — Andy — VBlank Architecture Replacement Plan

## [Andy - SYSTEM DESIGN, ARCADE VBLANK → GENESIS VDP COMMIT ARCHITECTURE]

### Objective
Design the correct long-term graphics architecture by preserving arcade vblank control flow while replacing arcade hardware behavior with Genesis-compatible VDP/DMA commit logic.

This is a system-level design task, not debugging.

You are NOT implementing anything.
You are NOT modifying code.
You are NOT focusing on a single sprite/logo issue.

---

## CONTEXT (LOCKED — DO NOT RE-ARGUE)

Already proven:

- Patch pipeline works
- Builder execution restored
- Block-A is populated with valid data
- Renderer can consume block-A
- Renderer guard bug was fixed
- Still no correct visible graphics output

Conclusion:

The system is alive, but the graphics architecture is incomplete/misaligned.

---

## CORE DIRECTION (MANDATORY)

We are moving to this model:

- Arcade code remains the authoritative frame controller
- Arcade vblank interrupt remains the single owner of frame timing
- Genesis-specific logic is inserted inside arcade vblank
- NO separate SGDK/C renderer should own display after launch

---

## TASK 1 — IDENTIFY ARCADE VBLANK OWNERSHIP

You MUST:

1. Identify the arcade vblank routine(s):
   - entry point(s)
   - call structure
   - major phases inside vblank

2. Determine what it controls:
   - frame progression
   - animation timing
   - input timing
   - graphics preparation
   - graphics commit

Output:

- list of functions / addresses
- execution order inside vblank

---

## TASK 2 — IDENTIFY HARDWARE-DEPENDENT BEHAVIOR

Within arcade vblank, identify:

Which parts are tied to:
- PC0900J (sprite hardware)
- PC080SN (tilemap hardware)
- palette RAM writes
- scroll registers
- direct hardware I/O

Classify each as:

- KEEP (logic only)
- REPLACE (hardware-specific)

Output:

- table of routines:
  - address
  - purpose
  - keep/replace classification

---

## TASK 3 — DEFINE WRAM GRAPHICS BUFFERS

Define canonical WRAM structures:

- Block-A → sprite descriptors
- Block-B → text/tile descriptors
- Tile upload queue
- Tilemap update buffer
- Scroll state buffer

For each:

- memory location
- structure layout
- producer
- consumer

---

## TASK 4 — DEFINE GENESIS VBLANK COMMIT PHASE

Design the Genesis commit phase (inside arcade vblank):

Must:

1. Upload tiles (DMA)
2. Update SAT
3. Apply tilemap updates
4. Set scroll registers
5. Handle palette updates

Constraints:

- Must run entirely during vblank
- Must avoid redundant writes
- Must operate on WRAM buffers

Output:

Ordered step-by-step sequence.

---

## TASK 5 — DEFINE REPLACEMENT STRATEGY

For each hardware-dependent section:

- original arcade behavior
- Genesis replacement behavior

Example:

Arcade: write sprite RAM → PC0900J  
Genesis: read Block-A → build SAT → DMA to VDP

Apply to:

- sprites
- tilemaps
- scroll
- palette

---

## TASK 6 — DEFINE IMPLEMENTATION ORDER

Define phases:

1. Sprite pipeline
2. Tile upload system
3. Tilemap updates
4. Scroll handling
5. Palette handling

Each phase must be independently testable.

---

## TASK 7 — DEFINE WHAT TO REMOVE

Identify:

- SGDK/C rendering paths to remove
- temporary scaffolding to retire
- components that should not exist in final system

---

## OUTPUT FILE

docs/design/vblank_graphics_architecture_plan.md

---

## AGENTS_LOG.md

Append:

## [Andy - VBlank Architecture Plan]

Include:

- architecture summary
- vblank ownership decision
- commit phase
- implementation phases

---

## REQUIRED FINAL LINE

"The arcade vblank remains the authoritative frame controller; Genesis VDP/DMA commit replaces all hardware-facing behavior within that flow."