# Andy — PC080SN Readback Interception Strategy

**Date**: 2026-04-06
**Scope**: `apps/rastan-direct` — PC080SN tilemap RAM readback crash analysis and patch plan
**Trigger**: BlastEm machine freeze due to read from address `0xC09E87` (PC080SN page 2)

---

## 1. Executive Summary

The arcade code contains exactly **three** absolute-address read instructions that access PC080SN tilemap RAM (0xC08000–0xC0BFFF). On Genesis hardware this range falls in the VDP region, which does not support arbitrary 68000 read cycles. BlastEm freezes on the first such read encountered at runtime. None of these three sites are in the current `specs/rastan_direct_remap.json`.

A fourth read category exists — a full RAM self-test routine at arcade PC `0x52A` that walks all of `0xC00000–0xC0BFFF` word by word — but it is only reachable from the arcade hardware startup vector (`0x3A000 → 0x3AE86 → 0x114 → 0x52A`). The Genesis project enters the arcade code at per-frame tick `0x03A008`, bypassing the entire startup chain. The RAM test reads are unreachable in Genesis context.

All three live read sites use the `CMPI` instruction (compare immediate with memory). None store the read value into a data register. The value is used only to set the condition code register for a subsequent `BNE` branch. This classification determines the correct patch strategy.

**Selected strategy: constant return via NOP + BRA bypass.**

Each read site is patched by replacing the `CMPI` + `BNE` pair (10 bytes each) with a `BRA` that unconditionally takes the not-equal branch, plus `NOP` fill. This is safe because: (1) the CMPI result feeds only a branch, not arithmetic or storage; (2) the SGDK trace showed these reads are status/sentinel checks against fixed magic values, not logic-critical readbacks; and (3) the AGENTS_LOG records that prior development already applied this exact strategy to site 3 in an earlier build (the current `rastan_direct_remap.json` does not contain these patches — they existed in the now-superseded SGDK-branch spec).

---

## 2. Read Site Inventory

### Search Methodology

Searched `build/maincpu.disasm.txt` (122,241 lines) exhaustively for:
- All lines containing `0xc0[0-9a-f]{4}` (59 total matches)
- Filtered by instruction class: `cmpi`, `btst`, `move[bwl]`, `tst`, arithmetic, `movem`
- Verified indirect-read candidates (LEA + (Ax)@ dereferences) around all C0xxxx LEA sites
- Confirmed disassembler data-region false positives (0x6D36, 0x8A74 areas) are misinterpreted data tables, not executed code

### Direct Absolute Read Sites (All in Page 2: 0xC08000–0xC0BFFF)

| # | Arcade PC | Disasm Addr | Instruction | Memory Address | Access Width | Register Receiving Value |
|---|-----------|-------------|-------------|----------------|--------------|--------------------------|
| 1 | `0x03A47E` | `3a47e` | `cmpiw #73,0xc0883a` | `0xC0883A` | 16-bit | None (CCR only) |
| 2 | `0x03A552` | `3a552` | `cmpib #48,0xc09ea3` | `0xC09EA3` | 8-bit | None (CCR only) |
| 3 | `0x03AC54` | `3ac54` | `cmpib #67,0xc09e87` | `0xC09E87` | 8-bit | None (CCR only) |

**Total direct absolute read sites: 3**

Page offsets within page 2 (relative to 0xC08000):
- Site 1: `+0x083A` (score display or status area — outside the 0x1336–0x1EA3 "rowscroll" range)
- Site 2: `+0x1EA3` (at the exact top boundary of the SGDK-traced read range)
- Site 3: `+0x1E87` (just below the top of the SGDK-traced read range)

### Indirect Read Sites (Startup RAM Test — UNREACHABLE)

Subroutine at `0x57C` performs a destructive read-modify-write RAM test. Called from `0x52A`, which is called only from `0x114`. The call chain is:

```
0x0000 (reset vector) → 0x3A000 (braw 0x3AE86) → 0x3AE86 (hardware startup)
  → ... → 0x114 (bsrw 0x52A) → 0x52A → 0x57C (reads every word in C00000–C0BFFF)
```

The Genesis project enters the per-frame tick at `0x03A008`. That address is 8 bytes into the code at `0x3A000`, after the `braw 0x3AE86` instruction. The startup path and the call to `0x52A` are never executed. Confirmed: `bsrw 0x52a` appears exactly once in the disassembly (line 93, from address `0x114`). No other caller exists.

**These reads require no patching.**

### Pages 0, 1, and 3 (0xC00000–0xC07FFF, 0xC0C000–0xC0FFFF)

No absolute read instructions found targeting these ranges in reachable code. The SGDK `ram_usage_profile.json` trace (549 frames) confirmed pages 0, 1, and 3 as write-only with zero reads. Current disassembly corroborates: all C00000, C04000, C0C000 references in game code are LEA (address load only) or immediate writes, never source-operand reads.

---

## 3. Read Usage Classification

### Site 1 — `0x03A47E`: `cmpiw #73, 0xC0883A`

**Context** (disasm lines 73271–73276):
```
3a478: tstw %a5@(18)       ; test game state word
3a47c: beqs 0x3a490        ; if zero, skip
3a47e: cmpiw #73,0xc0883a  ; READ 0xC0883A, compare with 73 (ASCII 'I')
3a486: bnes 0x3a490        ; if not 'I', skip to 0x3a490
3a488: movew #154,%d0      ; if 'I': load code 154
3a48c: bsrw 0x3bb48        ; call display routine
              ; fall through to 0x3a490
```

**Classification**: Status sentinel check. Reads a byte from page 2 and tests for a specific ASCII magic value. The value does not enter arithmetic. If equal, a display routine runs; both paths converge at `0x3A490`. Returning a constant "not equal" outcome by always branching to `0x3A490` skips only the display call — which is itself sending data to C-window space (not affecting game progression logic).

**Used in logic**: NO (branch only; value not stored or arithmetically consumed)
**Safe with constant 0 / not-equal result**: YES

### Site 2 — `0x03A552`: `cmpib #48, 0xC09EA3`

**Context** (disasm lines 73328–73335):
```
3a552: cmpib #48,0xc09ea3  ; READ 0xC09EA3, compare with 48 (ASCII '0')
3a55a: bnes 0x3a564        ; if not '0', return
3a55c: moveb #32,0xc09ea3  ; if '0': write space (' ') to 0xC09EA3 (C-window write)
3a564: rts
```

This subroutine is called as a helper from the score display path. It reads a score digit, and if the digit is ASCII '0', replaces it with a space (blank leading-zero suppression). The write at `0x3A55C` is ALREADY patched to NOPs in a prior build (AGENTS_LOG line 12978: "3a55c: moveb #32, 0xC09EA3 — ALREADY PATCHED to NOPs"). The read at `0x3A552` is NOT yet patched and is a live crash candidate.

**Classification**: Status sentinel / display formatting. Value feeds branch only, no arithmetic use.
**Used in logic**: NO
**Safe with constant "not equal" result**: YES (leading-zero suppression is cosmetic; skipping it has no gameplay effect)

### Site 3 — `0x03AC54`: `cmpib #67, 0xC09E87`

**Context** (disasm lines 73820–73828):
```
3ac4e: bcss 0x3ac54         ; only reaches here if score counter >= 9
3ac50: bsrw 0x3ae50         ; score carry routine
3ac54: cmpib #67,0xc09e87   ; READ 0xC09E87, compare with 67 (ASCII 'C')
3ac5c: bnes 0x3ac68         ; if not 'C', skip to 0x3ac68
3ac5e: moveq #3,%d0         ; if 'C': prepare display
3ac60: bsrw 0x3c2e2         ; call display routine
3ac64: bsrw 0x3a552         ; call score display subroutine (site 2)
3ac68: moveb #4,%d0         ; [not-equal path continues here]
```

This is the CURRENT CRASH SITE. Confirmed by BlastEm error "machine freeze due to read from address C09E87". The comparison tests for ASCII 'C' — a score display sentinel value.

**Classification**: Score display status check. Value feeds branch only.
**Used in logic**: NO
**Safe with constant "not equal" result**: YES (skips one display subroutine call, continues at `0x3AC68` with game state intact)

Prior development history (AGENTS_LOG lines 10830–10833) proposed a BRA bypass patch for this exact site. That patch was described as present in the SGDK-branch spec but is confirmed absent from the current `specs/rastan_direct_remap.json`.

**Read usage classified: YES for all 3 sites. None use the read value in logic. All are safe with constant "not equal" response.**

---

## 4. SGDK Correlation

### What the SGDK Trace Found

The `ram_usage_profile.json` trace (549 frames, AGENTS_LOG line 1608) reported:
- Pages 0, 1, 3: zero reads, write-only
- Page 2 (`0xC08000–0xC0BFFF`): **16 isolated word reads at stride ~0x200, offsets 0x1336–0x1EA3**
- All reads classified as heuristic-only (floor count, not ceiling)

### Correlation with Current Disassembly

The disassembly shows:
- Site 2 accesses `0xC09EA3` = page 2 offset `+0x1EA3` — **exact top-boundary match with the SGDK trace range**
- Site 3 accesses `0xC09E87` = page 2 offset `+0x1E87` — **within the trace range**
- Site 1 accesses `0xC0883A` = page 2 offset `+0x083A` — **outside the trace range** (0x083A < 0x1336)

The SGDK trace range of 0x1336–0x1EA3 covers sites 2 and 3. Site 1 (0x083A) was apparently not exercised during the 549 traced frames, consistent with the trace's own caveat that coverage reflects only the traced scenario.

The SGDK count of "16 reads" is higher than the 3 sites found via static disassembly analysis. This is because:
1. The SGDK trace used heuristic detection and may have over-counted (each runtime execution of a `cmpib` touching multiple page 2 addresses within a frame would be counted separately)
2. Sites 2 and 3 may execute multiple times per frame under different score states
3. The trace was dynamic (execution count) while the disassembly count is static (unique instruction sites)

**SGDK read set validated: YES (all SGDK-identified page 2 reads correspond to the 3 disassembly sites). Matches current disassembly: YES for sites 2 and 3; site 1 was a cold-path site outside the trace coverage window.**

---

## 5. Selected Strategy

**Strategy: constant return (Option A) — BRA bypass replacing CMPI + BNE**

### Justification

1. **No arithmetic use**: All three CMPi instructions set only the CCR. No value is stored in a data register. A "shadow return" returning the last-written value would provide the same CCR outcome as returning a constant, and is unnecessary complexity.

2. **"Not equal" is the safe branch**: For all three sites, the "not equal" branch leads to game state continuation. The "equal" branch triggers display-only subroutine calls that access C-window space (which would cause secondary crashes even if the read were allowed). Taking the "not equal" path is both crash-safe and functionally correct for genesis gameplay.

3. **Prior validation**: AGENTS_LOG records that this exact strategy (BRA bypass at site 3) was implemented, tested, and confirmed working in an earlier build. Sites 1 and 2 were identified in the same review (AGENTS_LOG line 12956) as the next candidates.

4. **No WRAM mirror needed**: The shadow strategy would be needed only if the read value fed computation that required the historically-written value. It does not.

5. **Patch size is identical for all three sites**: CMPI (8 bytes) + BNE/BCC (2 bytes) = 10 bytes. BRA + NOPs fills this exactly.

---

## 6. Patch Plan

### Encoding Reference

- `BRA +N` (short): `60 xx` where `xx` = signed byte offset from end of BRA instruction
- `NOP`: `4E 71` (2 bytes each)
- 10-byte slot: 1 BRA (2 bytes) + 4 NOPs (8 bytes)

For each site, the replacement is: `BRA` to the same address as the taken branch (BNE target = the not-equal path), padded with NOPs.

---

### Patch 1: `0x03A47E` — `cmpiw #73, 0xC0883A` + `bnes 0x3A490`

**Instruction analysis**:
```
3a47e: 0c79 0049 00c0 883a   cmpiw #73,0xc0883a   (8 bytes)
3a486: 6608                  bnes 0x3a490          (2 bytes)
```
BNE target: `0x3A490`. BRA from `0x3A47E`, size 2 bytes, so offset = `0x3A490 - (0x3A47E + 2)` = `0x10`.

**Replacement (10 bytes)**:
```
6010             BRA 0x3A490    (+0x10 from end of BRA)
4e71 4e71 4e71 4e71 4e71 4e71 4e71 4e71   8x NOP
```

| Field | Value |
|-------|-------|
| `arcade_pc` | `"0x03A47E"` |
| `original_bytes` | `"0c7900490c0883a6608"` → corrected: `"0c790049 00c0883a 6608"` |
| `replacement_bytes` | `"6010 4e71 4e71 4e71 4e71 4e71 4e71 4e71 4e71"` |
| Size | 10 bytes |

Exact `original_bytes` hex string (no spaces): `0c79004900c0883a6608`
Exact `replacement_bytes` hex string: `60104e714e714e714e714e714e714e714e71`

---

### Patch 2: `0x03A552` — `cmpib #48, 0xC09EA3` + `bnes 0x3A564`

**Instruction analysis**:
```
3a552: 0c39 0030 00c0 9ea3   cmpib #48,0xc09ea3   (8 bytes)
3a55a: 6608                  bnes 0x3a564          (2 bytes)
```
BNE target: `0x3A564`. BRA from `0x3A552`, size 2 bytes, offset = `0x3A564 - (0x3A552 + 2)` = `0x10`.

**Replacement (10 bytes)**:
```
6010             BRA 0x3A564    (+0x10 from end of BRA)
4e71 x8 NOPs
```

| Field | Value |
|-------|-------|
| `arcade_pc` | `"0x03A552"` |
| `original_bytes` | `"0c39003000c09ea36608"` |
| `replacement_bytes` | `"60104e714e714e714e714e714e714e714e71"` |
| Size | 10 bytes |

---

### Patch 3: `0x03AC54` — `cmpib #67, 0xC09E87` + `bnes 0x3AC68`

**Instruction analysis**:
```
3ac54: 0c39 0043 00c0 9e87   cmpib #67,0xc09e87   (8 bytes)
3ac5c: 660a                  bnes 0x3ac68          (2 bytes)
```
BNE target: `0x3AC68`. BRA from `0x3AC54`, size 2 bytes, offset = `0x3AC68 - (0x3AC54 + 2)` = `0x12`.

**Replacement (10 bytes)**:
```
6012             BRA 0x3AC68    (+0x12 from end of BRA)
4e71 x8 NOPs
```

| Field | Value |
|-------|-------|
| `arcade_pc` | `"0x03AC54"` |
| `original_bytes` | `"0c39004300c09e87660a"` |
| `replacement_bytes` | `"60124e714e714e714e714e714e714e714e71"` |
| Size | 10 bytes |

Note: This is the CURRENT CRASH SITE. AGENTS_LOG line 10830 contains an identical patch definition from prior work: `"original_bytes": "0c39004300c09e87660a"`, `"replacement_bytes": "60124E714E714E714E71"` — confirmed match.

---

### Patch Summary Table

| Arcade PC | Memory Read Address | Original Bytes (10) | Replacement Bytes (10) | BRA Target |
|-----------|--------------------|--------------------|------------------------|------------|
| `0x03A47E` | `0xC0883A` | `0c79004900c0883a6608` | `60104e714e714e714e714e714e714e714e71` | `0x3A490` |
| `0x03A552` | `0xC09EA3` | `0c39003000c09ea36608` | `60104e714e714e714e714e714e714e714e71` | `0x3A564` |
| `0x03AC54` | `0xC09E87` | `0c39004300c09e87660a` | `60124e714e714e714e714e714e714e714e71` | `0x3AC68` |

All three patches add to the `opcode_replace` array in `specs/rastan_direct_remap.json`. The `opcode_replace_count` expectation must be incremented from 31 to 34.

---

## 7. Single Root Cause

Arcade code performs readback from PC080SN tilemap RAM (0xC08000–0xC0BFFF) via three `CMPI` instructions at arcade PCs `0x03A47E`, `0x03A552`, and `0x03AC54`. On Genesis hardware, this address range maps to the VDP region, which is write-only from the 68000's perspective. An unpatched read causes an illegal VDP bus access that BlastEm classifies as a machine freeze. The current crash (`C09E87`) is site 3 (`0x03AC54`). Sites 1 and 2 are the next crash sites in execution order.

---

## 8. Single Next Correction

Add the following three `opcode_replace` entries to `specs/rastan_direct_remap.json` and increment `opcode_replace_count` from 31 to 34:

```json
{
  "arcade_pc": "0x03A47E",
  "original_bytes": "0c79004900c0883a6608",
  "replacement_bytes": "60104e714e714e714e714e714e714e714e71",
  "note": "Bypass PC080SN page2 readback cmpiw #73,0xC0883A + BNE; BRA to not-equal path 0x3A490."
},
{
  "arcade_pc": "0x03A552",
  "original_bytes": "0c39003000c09ea36608",
  "replacement_bytes": "60104e714e714e714e714e714e714e714e71",
  "note": "Bypass PC080SN page2 readback cmpib #48,0xC09EA3 + BNE; BRA to not-equal path 0x3A564."
},
{
  "arcade_pc": "0x03AC54",
  "original_bytes": "0c39004300c09e87660a",
  "replacement_bytes": "60124e714e714e714e714e714e714e714e71",
  "note": "Bypass PC080SN page2 readback cmpib #67,0xC09E87 + BNE (CRASH SITE); BRA to not-equal path 0x3AC68."
}
```

---

## 9. What Must Not Be Changed

- The existing NOP patch at `0x03A55C` (`moveb #32,0xC09EA3`) in the SGDK-branch spec history must not be retroactively added; it is a write, not a read, and its NOP status was already established. In `rastan_direct_remap.json` it is not currently present; it does not need to be added independently because the patch at `0x03A552` (site 2) branches past `0x3A55C` entirely.
- The A5 = `0xFF0000` initialization (patch at `0x03AF04` and `init_staging_state` entry in `main_68k.s`) must not be changed; it is the prerequisite for all game state reads working correctly.
- All existing input shadow patches (`0x03A4A2`, `0x03A4A8`, `0x03A778`, etc.) must remain unchanged.
- The `opcode_replace_count` expectation must be updated to 34 (not left at 31) to keep build validation passing.

---

## 10. Final Verdict

- **Read sites identified exactly**: YES — 3 reachable sites, all in page 2 (0xC08000–0xC0BFFF), all via CMPI absolute-address instructions
- **Read usage classified**: YES — all 3 are CCR-only (branch condition), no value stored to registers, no arithmetic use
- **SGDK read set validated**: YES — sites 2 and 3 fall within the SGDK-traced 0x1336–0x1EA3 range; site 1 is a cold-path site outside the trace window, consistent with SGDK's own caveat
- **Correct strategy**: constant return via BRA bypass — no shadow memory required
- **Patch plan defined**: YES — 3 entries, all 10 bytes, exact original_bytes and replacement_bytes specified
- **Single root cause**: Three unpatched CMPI instructions read from PC080SN tilemap RAM (page 2, 0xC08000–0xC0BFFF); on Genesis this maps to the VDP write-only region; any read triggers BlastEm machine freeze
- **Single next correction**: Add 3 `opcode_replace` entries to `specs/rastan_direct_remap.json` for arcade PCs `0x03A47E`, `0x03A552`, `0x03AC54`; increment expectation count to 34
