# Master Diagnostic Debt — Consolidated (Assistant Memory + Audit Synthesis)

## 1. Executive Summary

The current runtime is contaminated by multiple layers of diagnostic, suppression, and proof-only modifications.

These changes:

* alter memory state
* alter rendering state
* suppress execution paths
* inject artificial data
* break timing assumptions

Result:
The system is not currently a valid representation of the intended architecture.

---

## 2. Core Contamination Classes

### 2.1 FG Buffer Contamination

* Sentinel write to FG buffer index 0 every frame
* Debug overlay writing multiple rows into FG buffer

Impact:

* Plane A data is not trustworthy
* Text pipeline cannot be validated
* Tilemap correctness cannot be assessed

---

### 2.2 Execution Path Suppression

* Early returns in:

  * sprite renderer (ASM)
  * preload path
* Opcode remap NOP/RTS patches

Impact:

* Original arcade logic not executing fully
* Pointer flows may be broken
* State machines incomplete

---

### 2.3 VDP Pipeline Contamination

* Sprite SAT publish removed or altered
* Palette test injection after reset
* Palette commit altered (mirroring)
* Scroll commit experiments
* Window plane forced off earlier

Impact:

* No single source of truth for presentation
* Timing and ordering undefined
* Multiple test-era behaviors layered

---

### 2.4 Runtime Memory Mutation

* `sanitize_arcade_workram()` zeroing ranges each frame

Impact:

* Game logic altered every frame
* Pointer/state corruption masked or introduced
* Debug conclusions unreliable

---

### 2.5 Instrumentation Overload

* Commit counters
* Frame history tracking
* Pointer capture (`A0`)
* Debug overlays
* FG before/after capture

Impact:

* Timing changes
* Memory writes during VBlank
* Increased system noise

---

### 2.6 Visibility / Coordinate Hacks

* Row visibility filter disabled
* Coordinate decode changes during testing

Impact:

* Rendering no longer matches intended mapping
* Off-screen vs on-screen logic invalidated

---

## 3. Architectural Violations Introduced During Debugging

These are important:

### ❌ Multiple VDP writers (historically)

### ❌ Runtime VDP writes outside commit phase

### ❌ Mixed ownership of sprite publication

### ❌ Forced palette states

### ❌ Memory mutation during frame execution

---

## 4. What Was Being Proven (and is now stale)

You ran proofs for:

* FG buffer survival across tick
* VBlank execution ordering
* commit count per frame
* second VDP writer existence
* sprite DMA interference
* palette timing
* scroll behavior
* window plane coverage

👉 These proofs have served their purpose
👉 The scaffolding must now be removed

---

## 5. Current State Assessment

The system currently:

* does NOT reflect arcade behavior
* does NOT reflect intended Genesis pipeline
* contains multiple conflicting debug-era assumptions

---

## 6. Required Next Phase

### Phase Name:

**Diagnostic Debt Cleanup**

### Goal:

Return system to a **minimal, trustworthy baseline**

### Principle:

Remove ALL non-essential modifications before further debugging

---

## 7. Cleanup Strategy (to be executed later)

Order matters:

1. Remove FG buffer contamination (sentinel + overlay)
2. Remove runtime memory mutation (sanitize)
3. Restore execution paths (remove early returns / NOP patches where safe)
4. Remove palette test injection
5. Restore visibility filters
6. Remove instrumentation (counters, captures)
7. Re-establish clean VDP pipeline ownership

---

## 8. Final Statement

Until diagnostic debt is removed:

> Any debugging conclusions are unreliable

This system must be normalized before further work.
