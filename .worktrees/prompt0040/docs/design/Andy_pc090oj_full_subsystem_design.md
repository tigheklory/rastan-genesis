# Andy — PC090OJ Full Subsystem Design

**Agent:** Andy
**Type:** Design / Architecture (analysis only)
**Build context:** `rastan-direct` Build 0052
**Architecture compliance:** CONFIRMED (no source / spec / tool modifications).

**Outcome: STOP.** Two explicit STOP conditions from the prompt are triggered:

- *"Runtime sprite-update surface cannot be identified from static arcade disassembly evidence"* (confirmed: arcade uses pointer-based indirect addressing — the primary write path does not carry `0x00D0xxxx` literals at the write site itself but instead stores PC090OJ pointers into work-RAM at `arcade_pc 0x41BFC` for consumption by unidentified downstream code).
- *"Descriptor field semantics are so unclear that no safe translation rule can be designed"* (confirmed: static init evidence gives entry stride = 8 bytes and per-field initial values only, with no ground-truth for what each field encodes; multiple candidate formats remain indistinguishable from static evidence alone).

A complete subsystem design — staging model, SAT lowering, hook strategy for runtime, VBlank commit — cannot be produced without guessing descriptor semantics and runtime write patterns. The prompt's Global Rules 1, 9, 10 and task-specific Rules 16-18 explicitly forbid proceeding with a speculative design. What follows is the portion of the work that CAN be established from static evidence, the STOP declaration, and the specific follow-up evidence tasks required before a complete design can be produced.

---

## Phase 1 — PC090OJ write-surface enumeration

### 1.1 Method

`grep -in 'lea 0xd0[0-9a-f]{4}|movew.*0xd00[0-9a-f]{3}|movel.*0xd00[0-9a-f]{3}|movel.*0xd01[0-9a-f]{3}'` on [build/maincpu.disasm.txt](build/maincpu.disasm.txt). Results enumerate arcade code sites whose operand immediates are literal `0x00D0xxxx` addresses within the arcade PC090OJ sprite-RAM region (`0x00D00000..0x00D03FFF`).

### 1.2 Static enumeration

| arcade_pc | bytes                    | instruction                     | write class        | current spec coverage |
| --------- | ------------------------ | ------------------------------- | ------------------ | --------------------- |
| `0x0056A` | `41 F9 00 D0 00 00`      | `lea 0x00D00000, %a0`           | **boot-header / pre-_start** — part of arcade ROM-header area at file offset `0x56A`; re-examine in call-graph context if it becomes reachable (may be dead on Genesis). | none |
| `0x00570` | `43 F9 00 D0 10 00`      | `lea 0x00D01000, %a1`           | same boot-header region | none |
| `0x03AD50` | `41 F9 00 D0 00 00`      | `lea 0x00D00000, %a0`           | **INIT** — fill-primitive dest setup inside function at `arcade_pc 0x03AD4C`; fills 8 longs with `#0x100` via `arcade_pc 0x03AD44`. See [Andy_d00778_write_path_analysis.md](docs/design/Andy_d00778_write_path_analysis.md). | 0x03AD44 hook range-gated to PC080SN; PC090OJ writes silently dropped |
| `0x03AD62` | `41 F9 00 D0 01 70`      | `lea 0x00D00170, %a0`           | **INIT** — fill dest for 386-long region `0x00D00170..0x00D00778` via `0x03AD44`. | same range-gating drop |
| `0x03AD76` | `41 F9 00 D0 00 00`      | `lea 0x00D00000, %a0`           | **INIT** — second function `0x03AD72..0x03ADBA` pre-fills `0x00D00000..0x00D00780` (480 longs) with `#0x100` via `0x03AD44`. | same drop |
| `0x03AD86` | `41 F9 00 D0 07 78`      | `lea 0x00D00778, %a0`           | **INIT** — 17-entry structured init loop dest (per Andy_d00778_write_path_analysis.md). The write itself is at `arcade_pc 0x03ADAA`. | **UNHANDLED** — no opcode_replace covers 0x03ADAA |
| `0x03AE06` | `33 FC 00 01 00 D0 1B FE` | `movew #1, 0x00D01BFE`         | **INIT** — PC090OJ DMA-trigger register (not sprite-RAM); distinct role from descriptor writes. | **SUPPRESSED** by opcode_replace at `0x03AE06` |
| `0x03AE1E` | `33 FC 00 00 00 D0 1B FE` | `movew #0, 0x00D01BFE`         | **INIT** — DMA-trigger register. | **SUPPRESSED** by opcode_replace at `0x03AE1E` |
| `0x03AE8E` | `33 FC 00 00 00 D0 1B FE` | `movew #0, 0x00D01BFE`         | **INIT (startup_common)** — DMA-trigger register. | **SUPPRESSED** by opcode_replace at `0x03AE8E` |
| `0x03B8B4` | `43 F9 00 D0 00 20`      | `lea 0x00D00020, %a1`           | **INIT** (helper) — sub-function called during startup_common per arcade caller chain; full write body not yet traced. | none |
| `0x03B8CC` | `43 F9 00 D0 00 E0`      | `lea 0x00D000E0, %a1`           | **INIT** (helper) | none |
| `0x03B8DC` | `43 F9 00 D0 01 28`      | `lea 0x00D00128, %a1`           | **INIT** (helper) | none |
| `0x03B902` | `43 F9 00 D0 00 88`      | `lea 0x00D00088, %a1`           | **INIT** (helper) | none |
| `0x03B926` | `43 F9 00 D0 01 28`      | `lea 0x00D00128, %a1`           | **INIT** (helper) — duplicate of 0x03B8DC target | none |
| `0x41BFC` | `41 F9 00 D0 04 60`      | `lea 0x00D00460, %a0`           | **RUNTIME** — stride-80 indexing function (see §1.3 below). Does not itself write to sprite RAM; stores pointer into work-RAM at `arcade_pc 0x41C18`. | none |
| `0x41DB2` | `43 F9 00 D0 01 C8`      | `lea 0x00D001C8, %a1`           | **RUNTIME** (gameplay function body) — purpose not yet identified. | none |
| `0x41DEC` | `43 F9 00 D0 03 00`      | `lea 0x00D00300, %a1`           | **RUNTIME** | none |
| `0x41E2A` | `43 F9 00 D0 04 60`      | `lea 0x00D00460, %a1`           | **RUNTIME** | none |
| `0x41E7A` | `43 F9 00 D0 01 70`      | `lea 0x00D00170, %a1`           | **RUNTIME** | none |
| `0x41F64` | `43 F9 00 D0 03 C0`      | `lea 0x00D003C0, %a1`           | **RUNTIME** | none |
| `0x41F74` | `43 F9 00 D0 02 E0`      | `lea 0x00D002E0, %a1`           | **RUNTIME** | none |
| `0x45DFE` | `43 F9 00 D0 04 60`      | `lea 0x00D00460, %a1`           | **RUNTIME** (gameplay function body) | none |
| `0x45E44` | `43 F9 00 D0 01 70`      | `lea 0x00D00170, %a1`           | **RUNTIME** | none |
| `0x45E80` | `43 F9 00 D0 03 00`      | `lea 0x00D00300, %a1`           | **RUNTIME** | none |
| `0x510EA` | `33 FC 00 02 00 D0 06 98` | `movew #2, 0x00D00698`         | **RUNTIME** — single-word direct write to sprite-RAM byte offset `0x698`. | **UNHANDLED** |
| `0x510F4` | `33 FC 00 00 00 D0 06 98` | `movew #0, 0x00D00698`         | **RUNTIME** — pair to 0x510EA. | **UNHANDLED** |

### 1.3 Evidence of pointer-based indirect addressing (runtime surface not statically enumerable)

At [build/maincpu.disasm.txt:83548-83559](build/maincpu.disasm.txt) (`arcade_pc 0x41BF8..0x41C1C`):

```
0x41BF8:  moveq #80, %d1
0x41BFA:  muluw %d1, %d0               ; D0 *= 80 (80-byte indexing stride — DIFFERENT from init 8-byte stride)
0x41BFC:  lea 0x00D00460, %a0          ; A0 = sprite-RAM base for this table
0x41C02:  addal %d0, %a0                ; A0 += D0 (indexed sprite record)
0x41C04:  lea %a5@(4738), %a1           ; A1 = work-RAM entry
0x41C08:  clrw %d0
0x41C0A:  moveb %a4@(47), %d0
0x41C0E:  muluw #6, %d0
0x41C12:  addaw %d0, %a1
0x41C14:  movew #1, %a1@                ; *A1 = 1 (work-RAM)
0x41C18:  movel %a0, %a1@(2)            ; *(A1+2) = A0 (store PC090OJ pointer INTO work-RAM)
0x41C1C:  rts
```

This function **does not write to arcade PC090OJ sprite RAM**. It computes a pointer into sprite RAM, stores that pointer in work-RAM at `A5@(4738) + 6*index + 2`, and returns. The subsequent actual writes to sprite RAM happen elsewhere via an `A1`-register (or similar) that gets loaded from that work-RAM slot.

**Consequence for enumeration:** grep for literal `0x00D0xxxx` immediates does NOT find the sites where sprite-RAM writes actually happen at runtime. Those sites use computed addressing `(Ax)` or `(Ax)+` where `Ax` was previously loaded from work-RAM, from another register, or from an ROM table. Enumerating them exhaustively requires full arcade flow analysis — specifically, resolving every `(Ax)` addressing-mode write whose `Ax` can be traced back (via data-flow) to a PC090OJ base pointer.

**Stride discrepancy:** the init loop at `0x03AD84..0x03ADBA` uses **8-byte entry stride**; the indexing function at `0x41BFC` uses **80-byte stride**. That is strong evidence that arcade stores more than one logical table format inside the PC090OJ sprite-RAM address range. Either (a) different regions of sprite RAM carry different record formats, or (b) the 80-byte records are "sprite-control" records separate from actual PC090OJ descriptors. Without seeing a complete record-by-record write pattern, this cannot be resolved from static evidence.

### 1.4 Phase 1 classification

```
Static LEA-based write-site count:                   25
  INIT sites (reachable from startup_common):        10
  RUNTIME sites (reachable from gameplay code):      12 LEA + 2 direct-absolute writes
  Pre-_start / boot-header region:                    2 (may be dead on Genesis)
  DMA-trigger writes (already suppressed):            3

Runtime writes enumerable statically:                  NO
  Evidence: arcade_pc 0x41BFC (and likely other gameplay functions)
  computes pointers into sprite RAM and stores them into work-RAM
  rather than writing directly. The real write sites use (Ax) /
  (Ax)+ addressing with Ax loaded from work-RAM or derived from
  other registers. These sites do not carry 0x00D0xxxx literals
  and cannot be enumerated by any straightforward static search.

Phase 1 status:  INCOMPLETE — "Runtime surface not statically enumerable"
  (per prompt's explicit handling instruction)
```

---

## Phase 2 — Descriptor model

### 2.1 What is establishable from static init evidence

From the 17-entry structured init at `arcade_pc 0x03AD84..0x03ADBA` (analysed in [Andy_d00778_write_path_analysis.md](docs/design/Andy_d00778_write_path_analysis.md)):

```
Entry stride at the init site:    8 bytes (arcade_pc 0x03ADB0 is `addql #8, %a0`)
Per-entry writes:                  `movel %d0, %a0@`     (+0 .. +3, 4 bytes)
                                   `movel %d7, %a0@(4)`  (+4 .. +7, 4 bytes)
Init values across 17 iterations:
  outer loop 1 (14 iter): (D0, D7) = (8, 352), (24, 352), (40, 352), ..., (216, 352)
                          D0 increments by 16 (`addiw #16, %d0`)
                          D7 constant `#352 = 0x0160`
  outer loop 2 (3 iter):  (D0, D7) = (200, 352), (216, 352), (232, 352)
                          D0 reset to 200, increments by 16
                          D7 constant 352
```

### 2.2 Field-by-field classification

The longword writes `movel %d0, %a0@` and `movel %d7, %a0@(4)` span 4 bytes each. On the real PC090OJ chip, sprite descriptors are word-aligned. The 8-byte entry could therefore be interpreted as:

- **Interpretation A (4 × 16-bit words per entry):** offsets `+0`, `+2`, `+4`, `+6`. The two longword writes would encode (hi=0, lo=value) pairs at (`+0`, `+2`) and (`+4`, `+6`).
- **Interpretation B (2 × 32-bit longwords per entry):** offsets `+0` and `+4`, each a 32-bit value. PC090OJ chip itself does not use 32-bit fields, but arcade software might use the long-word form for efficiency while the chip sees the low 16 bits of each.

Both interpretations are consistent with the init evidence. No static disassembly inside `0x03AD84..0x03ADBA` disambiguates them.

| field (tentative offset) | init value at entry 1 | init value at entry 14 | init value at entry 17 | KNOWN / PARTIAL / UNKNOWN | evidence |
| ------------------------ | --------------------: | ---------------------: | ---------------------: | ------------------------- | -------- |
| offset `+0` word         | `0x0000`              | `0x0000`               | `0x0000`               | **PARTIAL** — value is constant zero across 17 init entries; arcade code sets the upper 16 bits of the longword `D0` to 0 (`D0 = 8, 24, ..., 232`, all fit in low 16 bits). Real meaning requires runtime evidence. |
| offset `+2` word         | `0x0008`              | `0x00D8` (=216)        | `0x00E8` (=232)        | **UNKNOWN** — pattern is "index × 16 + 8" for entries 1..14, then reset pattern for entries 15..17. Could be Y position, sprite code, or any other arcade-meaningful monotone field. |
| offset `+4` word         | `0x0000`              | `0x0000`               | `0x0000`               | **PARTIAL** — constant zero across 17 entries; arcade `D7 = 0x160` upper half is zero. |
| offset `+6` word         | `0x0160` (=352)       | `0x0160`               | `0x0160`               | **UNKNOWN** — constant across all entries. Could be attribute, palette bits, priority, sprite-size bits, or link. |

Alternate interpretation (2 × 32-bit longwords):

| field (tentative offset) | init value | KNOWN / PARTIAL / UNKNOWN | evidence |
| ------------------------ | ---------- | ------------------------- | -------- |
| offset `+0` longword     | `0x00000008..0x000000E8` across entries | **UNKNOWN** — whatever this encodes, it varies by entry index. |
| offset `+4` longword     | `0x00000160` constant | **UNKNOWN** — whatever this encodes, it's table-wide constant. |

### 2.3 Countervailing evidence against a simple 8-byte model

- The runtime function at `arcade_pc 0x41BFC` uses **80-byte stride** (`moveq #80, %d1; muluw %d1, %d0`) when indexing `0x00D00460+`. That is incompatible with uniform 8-byte descriptors across the entire PC090OJ region.
- Multiple LEA sites in Phase 1 target distinct offsets (`0xD00020`, `0xD00088`, `0xD000E0`, `0xD00128`, `0xD00170`, `0xD001C8`, `0xD002E0`, `0xD00300`, `0xD003C0`, `0xD00460`, `0xD00698`, `0xD00778`). Some of these offsets are not multiples of 8, 16, or 80 simultaneously — they cannot all be aligned sprite-descriptor slots under any single uniform stride.
- Conclusion: arcade uses the PC090OJ 16 KB region as a **heterogeneous memory pool** with multiple data types sharing the same address range. A "single descriptor model" cannot capture this.

### 2.4 Phase 2 classification

```
Descriptor fields KNOWN:     0
Descriptor fields PARTIAL:   2 (offset +0 and +4 upper words, constant zero in init)
Descriptor fields UNKNOWN:   2 (offset +2 and +6 words) — under one interpretation
                             2 (offset +0 and +4 longwords) — under the other interpretation
Multiple-format evidence:    YES — at least two entry strides in use (8-byte init, 80-byte runtime
                             at 0x41BFC), plus scattered direct single-word writes.

Phase 2 status:  INSUFFICIENT for safe translation rule design.
  Init evidence alone cannot disambiguate 4-word vs 2-long interpretation,
  cannot identify any specific field as Y / code / X / attribute without
  runtime evidence of the same fields being written with game-state-
  derived values, and cannot reconcile the observed multiple-stride
  arcade usage of the sprite-RAM region.
```

---

## Phase 3 — STOP: cannot proceed beyond Phase 2

Per prompt STOP conditions:

- **"Runtime sprite-update surface cannot be identified from static arcade disassembly evidence"** — confirmed in Phase 1 §1.3 (arcade uses pointer-based indirect addressing; real writes are not enumerable from static literal-grep).
- **"Descriptor field semantics are so unclear that no safe translation rule can be designed"** — confirmed in Phase 2 §2.2-§2.4 (all field meanings UNKNOWN or PARTIAL; multiple plausible record formats).

Phases 3-8 (staging model, SAT lowering, hook strategy, VBlank commit, init walkthrough, runtime behaviour) all depend on:

1. An authoritative descriptor model (Phase 2) — **unavailable**.
2. A complete runtime write-surface enumeration (Phase 1 §1.3) — **unavailable**.

Proceeding to design staging and SAT lowering under these gaps would require:
- Guessing field semantics (forbidden by Rule 9 / Rule 10).
- Inventing a plausible stride and field layout from pattern-matching to other Taito F2 titles (forbidden by Rule 10: "NO HEURISTIC MAPPING").
- Designing runtime hook points against an unenumerated write surface (forbidden by Rule 12: "TOTAL COVERAGE REQUIRED").
- Committing to a SAT lowering whose field translations cannot be verified against arcade's actual usage patterns (forbidden by Rule 1: "NO GUESSING").
- Producing an init-only design with runtime hand-waved (forbidden by Rule 17).

Any speculative design in Phases 3-8 would violate at least four numbered rules simultaneously. The prompt's explicit instruction under these conditions is to STOP.

---

## Phase 9 — Required follow-up evidence

Before a complete PC090OJ subsystem design can be produced, the following evidence-gathering tasks are required. Each is scoped to resolve a specific gap identified in Phases 1-2.

### E1. Runtime write-site enumeration via execution trace

**Goal:** identify all arcade_pc addresses that perform writes to `HW_ADDRESS 0x00D00000..0x00D03FFF` during runtime (not static disassembly).

**Method:** MAME watchpoint on the full PC090OJ region (`wp 0xD00000, 0x4000, w`) over a multi-second gameplay run. Log every hitting arcade_pc, filter unique sites, correlate with surrounding disassembly to identify the addressing-mode pattern at each site.

**Expected output:** a complete table of runtime write instructions, their A-register values at write time, and their source data register (D0/D1/etc.). This resolves the Phase 1 §1.3 gap.

### E2. Descriptor-field usage audit

**Goal:** determine what each byte-offset within a descriptor encodes.

**Method:** once E1 identifies runtime write sites, correlate the data values at each offset with concurrent game state:
- Writes whose source is derived from player / enemy screen position are Y / X fields.
- Writes whose source is a small monotonically-incremented byte are likely palette or link fields.
- Writes whose source is an ROM table index are likely sprite-code fields.
- Writes that take values in the range 0..511 decimal with specific bit patterns are likely attribute / flip fields.

**Expected output:** field-by-field table with confirmed semantics backed by specific runtime writes. This resolves the Phase 2 §2.2 gap.

### E3. Table-boundary identification

**Goal:** identify the boundaries between the different record formats within PC090OJ sprite RAM.

**Method:** combine E1 site list with the strides observed at each site (e.g., 8-byte stride at `0x03ADAA`, 80-byte stride at `0x41BFC`, single-word stride at `0x510EA`). Partition the 16 KB region into sub-ranges each serving a specific record type.

**Expected output:** a memory-map diagram of PC090OJ sprite RAM showing which byte ranges are (a) real PC090OJ chip-interpreted sprite descriptors, (b) arcade software bookkeeping records, (c) unused / padding. This resolves the Phase 2 §2.3 multiple-format gap.

### E4. DMA-trigger interaction audit

**Goal:** determine the relationship between the PC090OJ DMA-trigger register writes (currently suppressed at `arcade_pc 0x03AE06`, `0x03AE1E`, `0x03AE8E`) and arcade's expectation of when sprite RAM contents reach the sprite chip.

**Method:** audit the arcade_pc sites that write `0x00D01BFE` during gameplay (if any; may require E1 trace). Determine if arcade assumes a DMA cycle occurs after the register write or if writes to sprite RAM take effect immediately on the chip.

**Expected output:** a commit-timing model that informs the Genesis VBlank-commit design (Phase 6 equivalent in the next design task).

### E5. Sprite-count overflow handling

**Goal:** determine how many sprites arcade expects to display simultaneously and how it handles overflow.

**Method:** from E1 trace, count active descriptors per frame during a dense gameplay moment (multiple enemies, projectiles, effects). Correlate with Genesis SAT maximum of 80 sprites (NTSC). Determine if arcade ever exceeds Genesis capacity.

**Expected output:** a culling / priority strategy requirement for the eventual Genesis SAT lowering, or confirmation that arcade stays within Genesis limits.

### E6. Pattern-index translation requirement

**Goal:** determine how arcade sprite-code indices map to Genesis VRAM tile indices.

**Method:** once E2 identifies the sprite-code field, correlate arcade codes with the content of sprite ROMs (at `arcade_pc 0x00050000+` per prior docs) and determine the Genesis VRAM slot allocation needed to render those tiles. May require integration with the existing PC080SN tile-LUT framework at [tools/translation/precompute_pc080sn_tile_lut.py](tools/translation/precompute_pc080sn_tile_lut.py).

**Expected output:** a sprite-tile LUT analogous to the existing `genesistan_pc080sn_tile_vram_lut`.

---

## Phase 10 — Integrity

- Phase 1 write surface enumeration complete (init + runtime): **NO** (init partial; runtime not statically enumerable). Explicitly reported as the evidence gap per prompt instruction.
- Phase 2 descriptor model complete: **NO** (all fields UNKNOWN or PARTIAL).
- Phase 3 staging model justified: **NO** — STOP.
- Phase 4 SAT lowering rules complete: **NO** — STOP.
- Phase 5 hook strategy covers init AND runtime: **NO** — STOP.
- Phase 6 VBlank commit defined without scaffolding: **NO** — STOP.
- Phase 7 init-path walkthrough demonstrates correctness: **NO** — STOP (cannot demonstrate correctness without Phase 2 semantics).
- Phase 8 runtime behaviour defined, not deferred: **NO** — STOP (runtime evidence unavailable).
- Phase 9 risks and unknowns listed with follow-up evidence requirements: **YES** (E1-E6).
- No suppression, no scaffolding, no init-only design: **YES** — no design proposed that would require any of these.
- Every claim cited to arcade_pc, file:line, or prior doc: **YES**.
- No source / spec / tool modifications: **YES**.

---

## Summary

```
Write surfaces enumerated:                 25 static LEA-based sites
                                           (10 init + 12 runtime LEA + 2 direct-abs + 3 DMA-trigger
                                            suppressed + minor boot-header).
                                           Runtime pointer-based indirect writes:
                                           NOT STATICALLY ENUMERABLE
                                           (evidence: arcade_pc 0x41BFC stores PC090OJ
                                            pointer into work-RAM; actual writes happen
                                            elsewhere via (Ax) without 0x00D0xxxx literal).

Descriptor fields classified:              0 KNOWN / 2 PARTIAL / at least 2 UNKNOWN
                                           (multiple plausible entry sizes: 8-byte init,
                                            80-byte runtime at 0x41BFC, single-word directs).

Staging model:                             NOT DESIGNED — STOP (depends on Phase 2).
SAT lowering defined:                      NO — STOP.
Hook strategy covers init:                 NOT DESIGNED — STOP.
Hook strategy covers runtime:              NOT DESIGNED — STOP.
VBlank commit defined:                     NOT DESIGNED — STOP.
Init walkthrough complete:                 NOT POSSIBLE (Phase 2 incomplete).
Runtime behaviour defined:                 NO — STOP (Phase 1 §1.3 gap).
Suppression proposed:                      NO.
Design scales to full game:                NOT ESTABLISHABLE — STOP.

STOP triggered:                            YES
  Reasons (both mandatory STOP conditions from the prompt, both satisfied):
    1. "Runtime sprite-update surface cannot be identified from
       static arcade disassembly evidence" (Phase 1 §1.3).
    2. "Descriptor field semantics are so unclear that no safe
       translation rule can be designed" (Phase 2 §2.2-§2.4).

Follow-up evidence required (specified in Phase 9):
  E1. Runtime write-site enumeration via MAME watchpoint trace.
  E2. Descriptor-field usage audit correlating writes with game state.
  E3. Table-boundary identification resolving multi-format layout.
  E4. DMA-trigger interaction audit.
  E5. Sprite-count overflow handling measurement.
  E6. Pattern-index translation requirement.
```
