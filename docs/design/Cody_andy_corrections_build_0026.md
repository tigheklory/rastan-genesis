# Cody — Andy Corrections for Build 0026

**Andy session:** 2026-04-12  
**Prerequisite:** Build 0025 is already done. This document describes two independent
tasks Cody must implement.

---

## Task 1 — Fix factory defaults in `init_staging_state`

**Why:** The factory defaults block written in Build 0025 used wrong values for several
A5-relative workram fields. The error was: values were computed assuming DIP1 raw = 0xFF,
but `remap.json` injects DIP1 raw = **0xFE**. The correct computation is:

```
ndip1 = NOT(0xFE) = 0x01
ndip2 = NOT(0xFF) = 0x00   (DIP2 is not patched by remap.json)

A5@(24) = ndip1        = 0x0001  (was 0x00FF)
A5@(28) = ndip2        = 0x0000  (was 0x00FF)
A5@(46) = ndip2 & 3   = 0       (was 3)
A5@(50) = ndip1 & 2   = 0       (was 2)   ← this one causes the BlastEm crash
```

**File:** `apps/rastan-direct/src/main_68k.s`

**Location:** The factory defaults block inside `init_staging_state`. It contains a
comment block similar to `/* DIP mirrors: active-low */` followed by the four values
to correct.

**Exact changes — find these lines and replace with the corrected values:**

```asm
/* BEFORE (wrong) */
move.w  #0x00FF, 0x0018(%a0)    /* A5@(24) = ~DIP1 */
move.w  #0x00FF, 0x001C(%a0)    /* A5@(28) = ~DIP2 */
...
move.w  #3,      0x002E(%a0)    /* A5@(46) mode = ndip2 & 3 = 3 */
move.w  #1,      0x0030(%a0)    /* A5@(48) cab  = ndip1 & 1 = 1 */
move.w  #2,      0x0032(%a0)    /* A5@(50) mon  = ndip1 & 2 = 2 */

/* AFTER (correct) */
move.w  #0x0001, 0x0018(%a0)    /* A5@(24) = ndip1 = NOT(DIP1=0xFE) = 0x01 */
move.w  #0x0000, 0x001C(%a0)    /* A5@(28) = ndip2 = NOT(DIP2=0xFF) = 0x00 */
...
move.w  #0,      0x002E(%a0)    /* A5@(46) mode = ndip2 & 3 = 0x00 & 3 = 0 */
move.w  #1,      0x0030(%a0)    /* A5@(48) cab  = ndip1 & 1 = 0x01 & 1 = 1 */
move.w  #0,      0x0032(%a0)    /* A5@(50) mon  = ndip1 & 2 = 0x01 & 2 = 0 (Flip_Screen OFF) */
```

**Impact:** A5@(50) = 2 (wrong value) was causing the arcade screen-flip gate to take
`path_ON`, which writes 0x0001 to 0xC50000 (PC080SN screen flip register). BlastEm
freezes on that write. With A5@(50) = 0, the gate takes `path_OFF`, writes 0x0000 to
0xC50000 (which will also be NOP'd — see Task 2), and the crash is avoided.

---

## Task 2 — Add NOP patches for PC080SN and PC090OJ hardware writes

**Why:** Four instructions in the arcade ROM write to arcade hardware registers that do
not exist on Genesis. Two of these (`path_ON` at 0x03AE16) cause a BlastEm freeze. All
four must be NOP'd in `specs/rastan_direct_remap.json`.

**Hardware context (from MAME source `docs/reference/mame/rastan/`):**
- `0xC50000` = PC080SN `ctrl_word_w` — screen flip register. No PC080SN on Genesis.
- `0xD01BFE` = PC090OJ sprite RAM at offset 0x1BFE. No PC090OJ on Genesis.

**File:** `specs/rastan_direct_remap.json`

**Change:** Add four entries to the `opcode_replace` array. Insert them in arcade PC
order near the existing 0x03AExxx patches. Increment `opcode_replace_count` from **35
to 39**.

```json
{
  "arcade_pc": "0x03ADFE",
  "original_bytes": "33FC000000C50000",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC080SN ctrl_word_w MOVE.W #0, 0xC50000 (screen flip OFF, path_OFF). No PC080SN on Genesis."
},
{
  "arcade_pc": "0x03AE06",
  "original_bytes": "33FC000100D01BFE",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC090OJ sprite RAM MOVE.W #1, 0xD01BFE (sprite entry 0x07FF, path_OFF). No PC090OJ on Genesis."
},
{
  "arcade_pc": "0x03AE16",
  "original_bytes": "33FC000100C50000",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC080SN ctrl_word_w MOVE.W #1, 0xC50000 (screen flip ON, path_ON — BlastEm crash site). No PC080SN on Genesis."
},
{
  "arcade_pc": "0x03AE1E",
  "original_bytes": "33FC000000D01BFE",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC090OJ sprite RAM MOVE.W #0, 0xD01BFE (sprite entry 0x07FF, path_ON). No PC090OJ on Genesis."
}
```

**Verification:** After patching, confirm `original_bytes` match exactly against the
ROM bytes at each arcade PC offset. The `remap.json` build step will error if they do
not match.

---

## Build and Trace Requirements

After implementing both tasks, perform a standard build and 30-second MAME trace.

**Expected changes in `genesis_exec_summary.txt`:**
- `reg_c50000_live count=0` (was 1 in Build 0025 — crash eliminated)
- `title_init_block@000200 count > 0` (was 0 — game should advance further)

**Current `opcode_replace_count` before this change:** 35  
**Required `opcode_replace_count` after this change:** 39

---

## Files Modified by Cody in This Task

| File | Change |
|------|--------|
| `apps/rastan-direct/src/main_68k.s` | Factory defaults: 5 corrected values in init_staging_state |
| `specs/rastan_direct_remap.json` | 4 new opcode_replace entries; count 35 → 39 |

## Files NOT Modified by Cody (already updated by Andy)

| File | What changed |
|------|--------------|
| `docs/design/Andy_arcade_hw_io_stub_strategy.md` | Hardware identification corrected (C50000=PC080SN, D01BFE=PC090OJ), factory defaults path corrected |
| `docs/design/Andy_genesis_bss_relocation_and_wram_map_design.md` | Factory defaults assembly block corrected (4 values) |
| `docs/design/WRAM_memory_map.md` | Factory default column corrected for A5@(24), A5@(28), A5@(46), A5@(50) |
| `AGENTS_LOG.md` | Hardware I/O analysis entry updated with correct hardware IDs |

---

## AGENTS_LOG Entry for Cody

Append the following entry to `AGENTS_LOG.md` when done:

```
## [Cody - Implementation, Factory Defaults Correction + PC080SN/PC090OJ NOP Patches (rastan-direct, Build 0026)]

* task 1 factory defaults: corrected 5 values in init_staging_state factory defaults block
  - A5@(24) 0x00FF → 0x0001 (ndip1 = NOT(DIP1=0xFE) = 0x01)
  - A5@(28) 0x00FF → 0x0000 (ndip2 = NOT(DIP2=0xFF) = 0x00)
  - A5@(46) 3 → 0 (ndip2 & 3 = 0)
  - A5@(50) 2 → 0 (ndip1 & 2 = 0; Flip_Screen OFF — eliminates wrong path_ON trigger)
  - A5@(48) 1 → 1 (unchanged; was already correct)
* task 2 nop patches: added 4 entries to specs/rastan_direct_remap.json
  - 0x03ADFE: MOVE.W #0, 0xC50000 → 4x NOP (PC080SN screen flip, path_OFF)
  - 0x03AE06: MOVE.W #1, 0xD01BFE → 4x NOP (PC090OJ sprite RAM, path_OFF)
  - 0x03AE16: MOVE.W #1, 0xC50000 → 4x NOP (PC080SN screen flip, path_ON — crash site)
  - 0x03AE1E: MOVE.W #0, 0xD01BFE → 4x NOP (PC090OJ sprite RAM, path_ON)
* opcode_replace_count: 35 → 39
* build: [YES/NO]
* reg_c50000_live count: [value from trace]
* title_init_block@000200 count: [value from trace]
* design refs: docs/design/Andy_arcade_hw_io_stub_strategy.md, docs/design/Cody_andy_corrections_build_0026.md
```
