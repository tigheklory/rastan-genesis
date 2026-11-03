# Watchdog Caller Enumeration

Status: **STOP triggered** — Ghidra headless xref script execution became unavailable (`GhidraScriptLoadException: Failed to get OSGi bundle containing script`) during this run. Partial enumeration below is derived from static disassembly and ROM-byte verification only.

- Source binary: `build/regions/maincpu.bin` (arcade reference ROM)
- Address space: all addresses below are **arcade_pc**.
- Target range: `arcade_pc 0x039F80..0x039FAC` inclusive.

## Enumerated Reference Sites

### Targeting arcade_pc 0x039F80 (watchdog entry)
Count: **1**

| site_arcade_pc | instruction (disasm) | resolved_target_arcade_pc | enclosing_function | context_disasm |
|---|---|---|---|---|
| 0x03AB6E | `braw 0x39f80` | 0x039F80 | `<no_function>` | 0x03AB68: clrw %a5@(4)<br>0x03AB6C: rts<br>0x03AB6E: braw 0x39f80<br>0x03AB72: beqs 0x3ab7a<br>0x03AB74: subqw #1,%a5@(44) |

### Targeting arcade_pc 0x039F82..0x039F8B (interior of watchdog body)
Count: **0**

No references found in this sub-range.

### Targeting arcade_pc 0x039F8C (delay loop entry)
Count: **2**

| site_arcade_pc | instruction (disasm) | resolved_target_arcade_pc | enclosing_function | context_disasm |
|---|---|---|---|---|
| 0x039F84 | `beqs 0x39f8c` | 0x039F8C | `warm_restart_watchdog_gate` | 0x039F7E: .short 0xffff<br>0x039F80: tstw %a5@(44)<br>0x039F84: beqs 0x39f8c<br>0x039F86: subqw #1,%a5@(44)<br>0x039F8A: rts |
| 0x039FAA | `bras 0x39f8c` | 0x039F8C | `warm_restart_watchdog_gate` | 0x039FA6: jmp %a0@<br>0x039FA8: bcss 0x39fac<br>0x039FAA: bras 0x39f8c<br>0x039FAC: rts<br>0x039FAE: .short 0xffff |

### Targeting arcade_pc 0x039F8E..0x039FA7 (interior)
Count: **1**

| site_arcade_pc | instruction (disasm) | resolved_target_arcade_pc | enclosing_function | context_disasm |
|---|---|---|---|---|
| 0x039F9C | `bnes 0x39f92` | 0x039F92 | `warm_restart_watchdog_gate` | 0x039F92: movel 0x0,%d0<br>0x039F96: subil #1,%d1<br>0x039F9C: bnes 0x39f92<br>0x039F9E: moveal 0x0,%sp<br>0x039FA2: moveal 0x4,%a0 |

### Targeting arcade_pc 0x039FA8 (conditional gate entry)
Count: **2**

| site_arcade_pc | instruction (disasm) | resolved_target_arcade_pc | enclosing_function | context_disasm |
|---|---|---|---|---|
| 0x03AB8A | `bsrw 0x39fa8` | 0x039FA8 | `warm_restart_gate_caller_a` | 0x03AB82: bras 0x3ab82<br>0x03AB84: cmpiw #256,%a5@(18)<br>0x03AB8A: bsrw 0x39fa8<br>0x03AB8E: cmpiw #3,%a5@(0)<br>0x03AB94: beqs 0x3abe0 |
| 0x03B092 | `bsrw 0x39fa8` | 0x039FA8 | `warm_restart_gate_caller_b` | 0x03B08A: bras 0x3b08a<br>0x03B08C: cmpiw #256,%a5@(18)<br>0x03B092: bsrw 0x39fa8<br>0x03B096: bras 0x3b07e<br>0x03B098: clrl 0xc20000 |

### Targeting arcade_pc 0x039FAA..0x039FAC (bra/rts tail)
Count: **1**

| site_arcade_pc | instruction (disasm) | resolved_target_arcade_pc | enclosing_function | context_disasm |
|---|---|---|---|---|
| 0x039FA8 | `bcss 0x39fac` | 0x039FAC | `warm_restart_watchdog_gate` | 0x039FA2: moveal 0x4,%a0<br>0x039FA6: jmp %a0@<br>0x039FA8: bcss 0x39fac<br>0x039FAA: bras 0x39f8c<br>0x039FAC: rts |

### Ambiguous / computed jumps
Count: **0**

No computed-jump reference was resolved into `0x039F80..0x039FAC` by this static pass.

## Verification Pass

Strict byte-scan performed across ROM for:
- `BSR.W` opcode pattern `61 00 xx xx` (PC-relative target)
- `JSR abs.l` opcode pattern `4E B9 00 03 9F xx`
- `JMP abs.l` opcode pattern `4E F9 00 03 9F xx`

- Byte-scan strict total: **2**
- Extracted strict total (`BSR.W/JSR/JMP` rows): **2**
- Verification result: **PASS**

| kind | site_arcade_pc | resolved_target_arcade_pc |
|---|---|---|
| `BSR.W` | 0x03AB8A | 0x039FA8 |
| `BSR.W` | 0x03B092 | 0x039FA8 |

Short conditional/unconditional branch coverage (`BRA.S/Bcc.S/Bcc.W`) came from disassembly parsing in this partial run.

## Totals

- Total enumerated reference sites into `0x039F80..0x039FAC`: **7**
- All addresses reported in arcade_pc space: **YES**

## STOP Reason

Ghidra project could be opened, but headless script execution for new/edited extraction scripts failed with `GhidraScriptLoadException` (class load / OSGi bundle resolution), so direct xref-database querying could not be completed in this run.
