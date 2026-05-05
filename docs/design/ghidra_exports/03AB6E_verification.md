# 0x03AB6E Verification

Address space for all values in this document: **arcade_pc**.

## Phase 1 — Byte Pattern Verification

- Probe command: `xxd -s 0x03AB6E -l 4 build/regions/maincpu.bin`
- Actual bytes at `0x03AB6E`: `60 00 F4 10`
- Opcode `60 00` (`bra.w`) match: **YES**
- Displacement raw: `0xF410`
- Displacement signed 16-bit: `-0x0BF0` (`-3056`)
- PC at site+2: `0x03AB70`
- Computed branch target: `0x03AB70 + (-0x0BF0) = 0x039F80`
- Target equals `0x039F80`: **YES**
- Byte-pattern verification: **PASS**

## Phase 2 — Function Containment Query

Primary attempt:
- Method attempted: Ghidra headless script calling `getFunctionContaining(0x03AB6E)`
- Result: failed with `GhidraScriptLoadException` / `Failed to get OSGi bundle containing script`

Fallback method used:
- Method: existing export metadata scan (`function_entry`, `function_body`) in `docs/design/ghidra_exports/*.txt`
- Export files consulted:
  - `039F9E_warm_restart_trampoline.txt`
  - `03A000_startup_common_entry.txt`
  - `03A008_level5_handler_entry.txt`
  - `03A0EC_coin_credit_logic_site.txt`
  - `03AB22_seed_defaults_site.txt`
  - `03AB84_reset_gate_cmp_site.txt`
  - `03AB8A_reset_gate_bsr_site.txt`
  - `03AE86_startup_common_body.txt`
  - `03AF04_a5_init_site.txt`
  - `03B092_reset_gate_bsr_site_b.txt`

Containment result:
- Enclosing function: `<no_function>`
- Function entry: `N/A`
- Function body ranges: `N/A`
- Nearest preceding function entry (from consulted exports):
  - `0x03A0EC` (`FUN_0003a0ec`) from `03A0EC_coin_credit_logic_site.txt`

## Phase 3 — Context Disassembly

8-instruction block (4 before, and 4 at/after including `0x03AB6E`):

```asm
0x03AB5E: movew #512,%a5@(44)
0x03AB64: clrw %a5@(2)
0x03AB68: clrw %a5@(4)
0x03AB6C: rts
0x03AB6E: braw 0x39f80
0x03AB72: beqs 0x3ab7a
0x03AB74: subqw #1,%a5@(44)
0x03AB78: rts
```
