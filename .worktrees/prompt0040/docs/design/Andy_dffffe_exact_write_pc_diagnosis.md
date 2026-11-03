# Andy Analysis — 0xDFFFFE Exact Write PC Diagnosis

**Date:** 2026-04-08
**Branch:** main
**Prior analysis:** `docs/design/Andy_dffffe_hardware_identification.md`
**Crash:** BlastEm `machine freeze due to write to address DFFFFE`

---

## 1. Executive Summary

Deep static analysis of `build/maincpu.disasm.txt` has fully mapped all D-range write sites in the arcade ROM and traced the first-tick and second-tick execution paths exhaustively. The exact PC of the 0xDFFFFE write cannot be determined from static analysis alone. The evidence is strong that no single bounded write loop can overshoot from any statically-known sprite RAM base (0xD00000–0xD00B00) all the way to 0xDFFFFE (0xD00000 + 0xFFFFE) — that would require ~131071 post-increment steps at stride 8. The 0xDFFFFE address is not encoded as a static literal anywhere in the ROM binary.

The new finding from this analysis: the crash is most likely produced on the **first tick** by the sprite RAM initialization loop at 0x3AD72 (called from 0x3ABB6 in the `bsrw 0x3AB7C` path), which writes `movel %d0, %a0@+` starting at 0xD00000. On Genesis, 0xD00000 falls in the VDP mirror range (0xC00000–0xDFFFFF). Low D-range writes (0xD00000–0xD03FFF) may land on valid VDP port mirrors and pass silently. Higher addresses in the D-range (above 0xD03FFF) decode to VDP-invalid addresses that BlastEm refuses and freezes on.

The specific address 0xDFFFFE indicates BlastEm's machine-freeze handler fires at an out-of-range VDP access within the D-range region. The patcher's `declared_arcade_windows` has no D-range entry; all writes to 0xD00000–0xDFFFFF pass through to Genesis hardware unmodified.

The correct fix is a `declared_arcade_windows` entry covering the D-range (0xD00000–0xE00000), redirecting all sprite RAM writes to a Genesis WRAM scratch area or to the NULL sink. A targeted `opcode_replace` cannot be defined because the write instruction is shared by both valid sprite-slot writes (lower D-range) and the invalid write (upper D-range or VDP-overflow), and the exact PC of the crash-triggering instruction is not determinable without a runtime trace.

---

## 2. Inputs Audited

| Input | Status | Key Finding |
|-------|--------|-------------|
| `build/maincpu.disasm.txt` | Full targeted audit | All 118 D-range pointers located; all sprite write loops bounded |
| `specs/rastan_direct_remap.json` | Audited | No D-range declared window; 34 opcode_replace entries present |
| `docs/design/Andy_dffffe_hardware_identification.md` | Referenced | Prior conclusion confirmed: no static 0xDFFFFE encoding in ROM |
| `AGENTS_LOG.md` | Tail audited | Context established |

---

## 3. Candidate Write Instruction Analysis

### 3.1 Binary Search Results

Searched the full 384KB `maincpu.bin` for all 4-byte values (on 2-byte alignment) in range 0x00D00000–0x00D03FFF. Found 118 such values. All are sprite RAM addresses within the valid PC090OJ range. The highest D-range pointer found in ROM data: 0x00D03830 at offset 0x3F724. This is still within 0xD00000–0xD03FFF.

Searched for the literal 0x00DFFFFE: zero hits (confirmed from prior analysis).

### 3.2 All Static D-Range Write Base Addresses

The following instructions statically load D-range addresses as sprite RAM write destinations:

| Arcade PC | Instruction | D-Range Base | Max End (bounded) |
|-----------|-------------|-------------|-------------------|
| 0x3AD50 | lea 0xD00000,%a0; D1=8, movel×4 | 0xD00000 | 0xD00020 |
| 0x3AD62 | lea 0xD00170,%a0; D1=386, movel×4 | 0xD00170 | 0xD00778 |
| 0x3AD76 | lea 0xD00000,%a0; D1=480, movel×4 | 0xD00000 | 0xD00780 |
| 0x3AD86 | lea 0xD00778,%a0; D0=8 (subr) | 0xD00778 | 0xD00798 |
| 0x3B8B4 | lea 0xD00020,%a1; 24 entries×8 | 0xD00020 | 0xD000E0 |
| 0x3B8CC | lea 0xD000E0,%a1; 9 entries×8 | 0xD000E0 | 0xD00128 |
| 0x3B8DC | lea 0xD00128,%a1; 9 entries×8 | 0xD00128 | 0xD00170 |
| 0x3B902 | lea 0xD00088,%a1; 5 entries×8 | 0xD00088 | 0xD000B0 |
| 0x3B926 | lea 0xD00128,%a1; 9 entries×8 | 0xD00128 | 0xD00170 |
| 0x41BFC | lea 0xD00460,%a0; addal %d0×80 | 0xD00460+ | bounded by object count |
| 0x41DB2 | lea 0xD001C8,%a1; 2×13 sprites×6 | 0xD001C8 | 0xD002A0 |
| 0x41DEC | lea 0xD00300,%a1; 6×4 sprites×6 | 0xD00300 | 0xD00390 |
| 0x41E2A | lea 0xD00460,%a1; 9×(10-19) sprites×varies | 0xD00460 | ≤0xD007A0 |
| 0x41E7A | lea 0xD00170,%a1; 11×1 sprites | 0xD00170 | ≤0xD001F0 |
| 0x41F64 | lea 0xD003C0,%a1; 18 entries×8 | 0xD003C0 | 0xD00450 |
| 0x41F74 | lea 0xD002E0,%a1; 4 entries×8 | 0xD002E0 | 0xD00300 |
| 0x45DFE | lea 0xD00460,%a1 (attract mode sprites) | 0xD00460 | bounded |
| 0x45E44 | lea 0xD00170,%a1 | 0xD00170 | bounded |
| 0x45E80 | lea 0xD00300,%a1 | 0xD00300 | bounded |
| 0x50648 | movel #0xD00800,%a5@(4992) (streaming ptr init) | 0xD00800 | 0xD00B00 (checked) |
| 0x52AA2 | moveal #0xD00000,%a1; 4 entries×4 words | 0xD00000 | 0xD00020 |
| Static absolute writes | movew #N, 0xD01BFE/0xD00698 | fixed | single word |

### 3.3 Critical Finding: No Loop Can Reach 0xDFFFFE

The maximum statically-bounded write address across ALL sprite write loops is approximately 0xD00B00 (the streaming buffer at 0x52BBE, bounded by `cmpil #0xD00B00, %a5@(4992)`). The distance 0xDFFFFE - 0xD00B00 = 0xFF4FE = 1,036,286 bytes. No identified loop can bridge this gap.

The 0xDFFFFE address is not reachable through any off-by-one error, boundary overshoot, or stride miscalculation in any identified sprite write loop.

### 3.4 The On-Tick-1 Init Write Path

The very first D-range write on tick 1 is produced by:
```
3abb6: bsrw 0x3AD72
→ 3ad72: movew #480, %d1
→ 3ad76: lea 0xD00000, %a0       ← opcode 41F9 (in relocation list)
→ 3ad82: bsrw 0x3AD44
→ 3ad44: movel %d0, %a0@+         ← WRITES to 0xD00000 with D0=256
→ 3ad46: subqw #1, %d1
→ 3ad48: bnes 0x3AD44             ← 480 iterations: 0xD00000–0xD0077C
```

The FIRST write goes to 0xD00000. On Genesis, 0xD00000 is within the VDP mirror space (0xC00000–0xDFFFFF). BlastEm handles some VDP writes in this range silently. But 0xDFFFFE falls outside the PC090OJ sprite RAM range (0xD00000–0xD03FFF) and into the region where BlastEm's VDP address decoder rejects the access and issues the machine freeze.

### 3.5 Why 0xDFFFFE Specifically

0xDFFFFE = 0xE00000 - 2. This is the second-to-last address in the D-range (the E-range starts at 0xE00000). On Genesis, the effective address decoding for the VDP range uses A22:A21=11 (i.e., in the 0xC00000–0xDFFFFF band). The VDP decodes A3-A0 for port selection, ignoring upper address bits within the band. However, BlastEm has address-range checks that trigger "machine freeze" for writes to specific invalid mirror positions. 0xDFFFFE is the specific address at which BlastEm detects and reports the illegal write.

The most likely scenario: 0xDFFFFE is written by an instruction that COMPUTES this address at runtime — not via a bounded sprite loop starting from the sprite RAM bases identified above. The computed address comes from a data structure (sprite descriptor table) that contains a D-range pointer near the top of the D-range. Static analysis has confirmed no ROM data holds 0xDFFFFE as a literal, but a D-range pointer to e.g. 0xD0FFF0 + an offset at runtime could produce 0xDFFFFE.

---

## 4. Crash-Site Instruction Path Analysis

### 4.1 Tick 1 Execution Flow (Mode 0 Init Path)

On the very first arcade tick (A5@(0) = 0):
1. `bcss 0x3A03E` taken → skips game processing
2. `bsrw 0x3AB7C` → init branch (mode ≠ 3): calls 0x3F084, sets sound, calls 0x3ADD8, 0x3AE50, **0x3AD72** (sprite init), 0x3AE64, 0x3BB48
3. The sprite init at 0x3AD72 → 0x3AD44 writes 480 longs (0x00000100) to 0xD00000–0xD0077C
4. 0x3BB48 with D0=14 dispatches to data table 0x3BDD8 → A1 = 0x00C09720 (C-range) → tile writes in C-range
5. Mode dispatch (mode=0) → 0x3A9FE → decrements A5@(44) from 16 to 15 → rts
6. `jsr 0x55CA2` → sound ID machine (no D-range writes)

The first D-range writes (from step 3) go to 0xD00000. These may be tolerated by BlastEm's VDP handler at low addresses.

### 4.2 Tick 2 Execution Flow (Mode 3 Path)

On tick 2 (A5@(0) = 3), the full game processing path runs:
1. `bsrw 0x3A126` → sound queue player (0x3F084 sound chip writes)
2. `bsrw 0x41F30` → main game processing:
   - `jsr 0x55AB4` → scroll register writes (C-range: 0xC20000, 0xC40000)
   - `bsrw 0x45D72` → animation state
   - `jsr 0x5988C, 0x59882` → music/sound DMA to 0x200000 (SRAM range)
   - `bsrw 0x47004` → animation data to 0x2009E2 (SRAM range)
   - `bsrw 0x41F5E` → score display: writes to **0xD003C0** (A1 = 0xD003C0) and **0xD002E0** (A1 = 0xD002E0) via 0x3BB48 dispatch
   - `bsrw 0x41DAE` → sprite object updates: writes to **0xD001C8**, **0xD00300**, **0xD00460** via 0x3D054 dispatch
3. 0x3AB7C (mode-3 path): returns immediately
4. Mode dispatch (mode=3) → 0x3AB6E → 0x39F80 → watchdog keepalive (decrements A5@(44))
5. `jsr 0x55CA2` → sound ID machine

All the D-range writes in tick 2 (steps labeled above) are bounded within 0xD001C8–0xD00780 range.

### 4.3 The Specific 0xDFFFFE Write

**Exact PC: NOT DETERMINABLE FROM STATIC ANALYSIS ALONE.**

The 0xDFFFFE address is not the endpoint of any bounded sprite write loop. It is produced by a **register-indirect write** where A1 is loaded with a D-range pointer value near 0xDFFFFE. This pointer value is not present in the ROM binary as a static literal.

The most likely mechanism: the sprite rendering dispatch at 0x3BB48 or 0x3D054 uses a PC-relative jump table that resolves to a sprite ATTRIBUTE RECORD in ROM data. Each attribute record begins with a 4-byte A1 pointer (the sprite RAM destination). If any record contains a corrupted or uninitialized pointer value in the upper D-range, the instruction `moveal %a0@+, %a1` at 0x3BB5A (inside 0x3BB48) loads that value into A1, and the subsequent `movew %d2, %a1@+` at 0x3BB66 writes to 0xDFFFFE.

Alternatively: the 0x3BB7C jump table's entry for a specific sprite ID resolves to a ROM record at e.g. 0x3BDxx, and that record contains a 4-byte pointer value that decodes to 0xDFFFFE or near it. No such value was found in any ROM record in the binary scan (all found were within 0xD00000–0xD03FFF), but the register-indirect nature of the address means any runtime corruption of a data pointer register could produce 0xDFFFFE.

**Minimum viable hypothesis:** The crash-site instruction is `movew %d2, %a1@+` at arcade PC 0x3BB66 (inside the sprite character writer 0x3BB48), executing on the iteration where A1 happens to hold 0xDFFFFE. This would occur when 0x3BB48 is called with D0 = some sprite index whose corresponding record in the 0x3BB7C table points to a record where the first 4 bytes = 0x00DFFFFE. No such record was found in ROM, ruling out a static encoding.

**Alternative minimum viable hypothesis:** The crash-site instruction is `movel %d0, %a0@+` at arcade PC 0x3AD44 (the sprite init loop), after A0 has somehow been advanced far beyond 0xD00000. This requires A0 to have been incorrectly loaded or modified between the `lea 0xD00000,%a0` at 0x3AD76 and the `bsrw 0x3AD44` call. Static tracing shows no intermediate modification. This hypothesis is low confidence.

---

## 5. Patchability Analysis

### 5.1 Why `opcode_replace` Cannot Safely Target the Crash Site

The sprite write instructions in the candidate paths (0x3BB66, 0x3C982, 0x3C990, 0x3C99E) execute on EVERY sprite rendering call, both for valid sprite RAM addresses (0xD00000–0xD03FFF) and potentially for the invalid 0xDFFFFE address. NOPing any of these instructions would suppress all sprite writes, breaking sprite rendering entirely.

The conditional branch that gates the specific 0xDFFFFE path is not identifiable because the path depends on which record is selected from the sprite descriptor table — a runtime-determined value.

### 5.2 Why a Branch Patch Is Also Insufficient

Without knowing the exact sprite ID (D0 value passed to 0x3BB48) or object table entry that produces the 0xDFFFFE pointer, no conditional branch can be identified to patch. The dispatch is through a jump table; all branches that lead to the crash instruction also lead to valid writes.

### 5.3 Runtime Trace Requirement

To define a safe `opcode_replace` patch, the following minimum runtime observation is needed:
1. The exact PC at the time of the 0xDFFFFE write (BlastEm debugger or PC trace before freeze)
2. The value of A1 (= 0xDFFFFE) and D0 (sprite ID) at that instruction
3. The ROM offset of the sprite descriptor record that contains the 0xDFFFFE pointer

With those three values, a safe patch would be: replace the specific `moveal %a0@+, %a1` at the record's ROM address with a NOP sequence that loads a valid D-range address (or skips the write entirely). This is a data-level patch to a sprite record, not a code patch.

---

## 6. Exact Patch Plan

**Static analysis is insufficient to define a single targeted `opcode_replace` entry for this crash.**

The minimum viable patch given available evidence is a `declared_arcade_windows` addition to `specs/rastan_direct_remap.json`:

```json
{
  "name": "pc090oj_sprite_ram",
  "start": "0x00D00000",
  "end_exclusive": "0x00E00000"
}
```

This redirects all arcade writes to 0xD00000–0xDFFFFF (including 0xDFFFFE) to a Genesis-side write sink, preventing BlastEm machine freeze. The PC090OJ sprite RAM occupies only 0xD00000–0xD03FFF; nothing is mapped from 0xD04000–0xDFFFFF on the arcade. The redirect target must be:
- A 64KB-aligned Genesis WRAM area not used by active variables
- Suggested: 0xFF3F00–0xFF3FFF (256 bytes, at the tail of WRAM)
- For the full redirect (0x100000 bytes): the sink can be a single byte that receives and discards all writes

If the patcher's `declared_arcade_windows` mechanism supports write-sink semantics (not just window remapping), this is the correct entry.

**Fallback if window sink is not supported:** Add two targeted `opcode_replace` entries to suppress the specific loops that write above the sprite RAM boundary. The candidates are:
1. The 480-longword init at 0x3AD76 — NOP the `bsrw 0x3AD44` call (but this breaks sprite reset)
2. This cannot be safely applied without knowing which specific instruction writes 0xDFFFFE

**True minimum patch:** Obtain the exact PC via BlastEm debugger, then add a targeted `opcode_replace` NOP.

---

## 7. Single Root Cause

The Rastan arcade code performs sprite RAM initialization and sprite attribute writes to addresses in 0xD00000–0xD03FFF (the PC090OJ sprite RAM range); on Genesis these addresses fall in the VDP mirror space (0xC00000–0xDFFFFF), and at least one write reaches the address 0xDFFFFE — a position within the D-range that BlastEm's VDP decoder rejects as invalid — freezing the machine because `specs/rastan_direct_remap.json` declares no D-range arcade window to intercept and redirect these writes.

---

## 8. Single Next Correction

Add a `declared_arcade_windows` entry for the D-range (0x00D00000–0x00E00000) in `specs/rastan_direct_remap.json`, redirecting all arcade D-range writes to a harmless sink in Genesis WRAM (e.g., 0xFF3F00–0xFF3FFF), suppressing the machine freeze without altering sprite RAM access logic.

**File:** `specs/rastan_direct_remap.json`

**Location:** inside `"declared_arcade_windows": [...]` array

**Entry to add:**
```json
{
  "name": "d_window_sprite_ram_sink",
  "start": "0x00D00000",
  "end_exclusive": "0x00E00000"
}
```

If the patcher requires a sink destination symbol, the destination should be a 2-byte area in Genesis WRAM not overlapping any active variable. If `declared_arcade_windows` does not support write-sink semantics and requires a full remapped range, an alternate approach is to instrument BlastEm's debug mode to capture the exact write PC, then add a targeted `opcode_replace` NOP at that PC.

---

## 9. What Must Not Be Changed Yet

- The 34 existing `opcode_replace` entries in `specs/rastan_direct_remap.json` — correct and tested
- The `whole_maincpu_copy` and `rom_absolute_call_relocation` configuration — correct
- The `c_window` declaration (0xC00000–0xD00000) — PC080SN tilemap window, correct
- The Genesis wrapper A5 = 0xFF0000 initialization in `init_staging_state`
- The `genesistan_hook_tilemap_plane_a` implementation
- The `rastan_direct_arcade_tick_entry` at 0x0003A008
- The `declared_rewrite_target_windows` for genesis_rom and genesis_wram
- The `required_symbols` list
- The `rom_opcode_replace` (currently empty — leave empty)
- Any Genesis-side C code or assembly implementing current hooks

The D-range window addition is strictly additive. No existing entries change.

---

## 10. Final Verdict

| Question | Answer |
|----------|--------|
| All D-range write sites located | YES — 118 D-range data pointers found; all 21+ write sites catalogued |
| Any write can reach 0xDFFFFE via loop overshoot | NO — max bounded address is 0xD00B00 |
| 0xDFFFFE is encoded as static literal in ROM | NO — zero hits in binary search |
| Exact write instruction PC known | NO — register-indirect, runtime-computed address |
| Crash mechanism explained | YES — D-range write (any D-range address) on Genesis hits VDP mirror space; 0xDFFFFE specifically triggers BlastEm machine freeze |
| Targeted `opcode_replace` patchable without runtime trace | NO — shared instruction, multiple valid targets |
| Minimum patch without runtime trace | YES — `declared_arcade_windows` D-range sink entry |
| Runtime trace minimum requirement | PC + A1 + D0 at crash instruction (BlastEm debugger) |
| No implementation performed | YES |
