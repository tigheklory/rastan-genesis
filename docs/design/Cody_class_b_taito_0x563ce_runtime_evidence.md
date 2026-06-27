# Cody - Class B TAITO 0x563CE Runtime Evidence

**Date:** 2026-06-27  
**Type:** Original arcade runtime evidence / analysis only  
**Arcade target:** MAME `rastan` / `Rastan (World Rev 1)`  
**Trace directory:** `states/traces/original_arcade_taito_0x563ce_runtime_evidence_20260627_124127/`  
**Scope:** Evidence only. No source/spec/tool/ROM/build changes. No bookmark. No diagnostics inserted into ROM. No fix design.

## Phase 0

Read before work: `RULES.md`, `ARCHITECTURE.md`, latest `AGENTS_LOG.md` tail, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, and the requested prior design docs:

- `docs/design/Andy_build_0107_validation_and_class_b_remaining_status.md`
- `docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md`
- `docs/design/Cody_build_0106_taito_magenta_cell_arcade_intent.md`
- `docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md`

Classification: **EXTENDING** OPEN-019 / OPEN-020 / KF-033 evidence. No contradiction detected.

## Arcade Target Confirmation

ROM availability was verified with:

```bash
/usr/games/mame -verifyroms rastan -rompath /home/tighe/projects/rastan-genesis/roms
```

Result: `romset rastan is good`.

MAME identifies the set as:

```text
rastan  "Rastan (World Rev 1)"
```

`-listxml` reports sourcefile `taito/rastan.cpp`. The PC080SN device is reported from sourcefile `taito/pc080sn.cpp`.

Exact runtime invocation used for the trace:

```bash
QT_QPA_PLATFORM=offscreen /usr/games/mame rastan \
  -rompath /home/tighe/projects/rastan-genesis/roms \
  -debug -debugger qt \
  -debugscript /home/tighe/projects/rastan-genesis/states/traces/original_arcade_taito_0x563ce_runtime_evidence_20260627_124127/mame_taito_0x563ce_runtime_evidence.cmd \
  -debuglog -video none -sound none -nothrottle -skip_gameinfo
```

MAME exited via debugger with status `0`. The raw event log is `states/traces/original_arcade_taito_0x563ce_runtime_evidence_20260627_124127/debug_events.log` (`538` event lines).

## Address-Mapping Discipline

Instruction PC correlation used `build/rastan-direct/address_map.json`; no arithmetic offset was used as authority.

The runtime watchpoint reports MAME's post-instruction PC for the memory write. The actual code-word store is the arcade instruction at `arcade_pc 0x03BB68`:

```asm
3bb66: 32c2  movew %d2,%a1@+   ; attr word
3bb68: 32c0  movew %d0,%a1@+   ; code word
3bb6a: 60f4  bras 0x3bb60
```

`address_map.json` has an exact `patched_site` segment:

```text
arcade_pc 0x03BB48..0x03BB7C -> runtime_genesis_pc 0x03BD48..0x03BD7C
```

Within that JSON segment, the relevant PCs map exactly as:

| Arcade PC | Meaning | Runtime Genesis PC | Segment kind |
|---|---|---|---|
| `0x03BB66` | attr store | `0x03BD66` | `patched_site` |
| `0x03BB68` | code store | `0x03BD68` | `patched_site` |
| `0x03BB6A` | post-code-store branch | `0x03BD6A` | `patched_site` |
| `0x03BB6C` | watchpoint post-PC after write | `0x03BD6C` | `patched_site` |

Secondary routine mapping from JSON:

```text
arcade_pc 0x0563CE -> runtime_genesis_pc 0x0565CE, segment kind arcade_copy
```

## Arcade Tilemap Address Derivation

For the audited cells, PC080SN FG C-window base is `HW_ADDRESS 0x00C08000`. The cell layout used by the original renderer is two words per cell: attr word then code word. Therefore:

```text
attr HW_ADDRESS = 0x00C08000 + row * 0x100 + col * 4
code HW_ADDRESS = attr HW_ADDRESS + 2
```

| Cell | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Matches prior listed code address? |
|---|---:|---|---|---|
| A | row `23`, col `17` | `0x00C09744` | `0x00C09746` | YES |
| B | row `23`, col `22` | `0x00C09758` | `0x00C0975A` | YES |
| C | row `23`, col `24` | `0x00C09760` | `0x00C09762` | YES |
| D | row `24`, col `20` | `0x00C09850` | `0x00C09852` | YES |

## Watchpoints Used

Write watchpoints were set on the four confirmed arcade PC080SN FG code-word addresses:

```text
wp c09746,2,w
wp c0975a,2,w
wp c09762,2,w
wp c09852,2,w
```

Breakpoints also logged the original glyph renderer stores (`arcade_pc 0x03BB66/0x03BB68`) and the secondary `0x0563CE` routine.

## Destination-Cell Evidence

The watched cells first receive clear/space writes (`0x0020`) from `arcade_pc 0x03AD48`. Those clear/fill writes are not the TAITO glyph-intent writes. The decisive TAITO composition writes are the later `arcade_pc 0x03BB68` code-word stores, reported by MAME's watchpoint as post-PC `0x03BB6C`.

| Cell | Code HW_ADDRESS | Prior value | Runtime write value | MAME post-PC | Actual writer instruction | Source byte pointer | Classification |
|---|---|---:|---:|---|---|---|---|
| row 23 col 17 | `0x00C09746` | `0x0020` | `0x0022` | `0x03BB6C` | `arcade_pc 0x03BB68` | `a0=0x0003BE29` | RAW-LOW-CODE |
| row 23 col 22 | `0x00C0975A` | `0x0020` | `0x0027` | `0x03BB6C` | `arcade_pc 0x03BB68` | `a0=0x0003BE2E` | RAW-LOW-CODE |
| row 23 col 24 | `0x00C09762` | `0x0020` | `0x002C` | `0x03BB6C` | `arcade_pc 0x03BB68` | `a0=0x0003BE30` | RAW-LOW-CODE |
| row 24 col 20 | `0x00C09852` | `0x0020` | `0x003F` | `0x03BB6C` | `arcade_pc 0x03BB68` | `a0=0x0003BE3E` | RAW-LOW-CODE |

Raw evidence lines:

```text
EVENT WATCH_TAITO_A_ROW23_COL17 cyc=1801799 pc=03BB6C addr=00C09746 size=16 old=0020 data=00000022 sr=2700 d0=00000022 d1=00000012 d2=00000000 a0=0003BE29 a1=00C09746
EVENT WATCH_TAITO_B_ROW23_COL22 cyc=1802029 pc=03BB6C addr=00C0975A size=16 old=0020 data=00000027 sr=2700 d0=00000027 d1=00000012 d2=00000000 a0=0003BE2E a1=00C0975A
EVENT WATCH_TAITO_C_ROW23_COL24 cyc=1802121 pc=03BB6C addr=00C09762 size=16 old=0020 data=0000002C sr=2700 d0=0000002C d1=00000012 d2=00000000 a0=0003BE30 a1=00C09762
EVENT WATCH_TAITO_D_ROW24_COL20 cyc=1802535 pc=03BB6C addr=00C09852 size=16 old=0020 data=0000003F sr=2700 d0=0000003F d1=00000013 d2=00000000 a0=0003BE3E a1=00C09852
```

Later attract/title text activity clears or overwrites some of these same coordinates with spaces/story text. That later page activity does not change the evidence for the audited TAITO composition writes above.

## Secondary 0x563CE Evidence

The secondary `arcade_pc 0x0563CE` routine was watched but did **not** execute in the captured TAITO-composition window.

```text
ROUTINE_0563CE_ENTRY count: 0
```

Therefore no runtime transform from the low codes to the `0x274x` aliases was observed for these watched destination cells. This is corroborating only; the destination-cell watchpoint values above are the primary evidence.

## Pattern Comparison

Pattern bytes were compared from the original PC080SN graphics region `build/regions/pc080sn.bin` at `tile_code * 32` bytes. All low-code tiles and mapped-alias tiles are nonblank, but each pair differs byte-for-byte.

| Raw low code | Mapped alias | Identical? | First differing byte | Raw nonblank? | Mapped nonblank? |
|---:|---:|---|---:|---|---|
| `0x0022` | `0x2745` | NO | `1` | YES | YES |
| `0x0027` | `0x2746` | NO | `1` | YES | YES |
| `0x002C` | `0x2749` | NO | `4` | YES | YES |
| `0x003F` | `0x274B` | NO | `0` | YES | YES |

## Primary Classification

| Code | Classification |
|---:|---|
| `0x0022` | RAW-LOW-CODE |
| `0x0027` | RAW-LOW-CODE |
| `0x002C` | RAW-LOW-CODE |
| `0x003F` | RAW-LOW-CODE |

## Interpretation Boundary

Observable fact: the original arcade runtime writes raw low-code tile words `0x0022`, `0x0027`, `0x002C`, and `0x003F` to the audited TAITO FG code-word cells.

Observable fact: the mapped aliases `0x2745`, `0x2746`, `0x2749`, and `0x274B` are not byte-identical to those raw low-code tile patterns.

Interpretation: a later Genesis fix should preserve the raw low-code tile intent for these cells; treating the watched arcade runtime as if it emitted the `0x274x` aliases is not supported by this evidence. Actual implementation details are intentionally deferred.

## Artifacts

- Debugger command file: `states/traces/original_arcade_taito_0x563ce_runtime_evidence_20260627_124127/mame_taito_0x563ce_runtime_evidence.cmd`
- Raw filtered event log: `states/traces/original_arcade_taito_0x563ce_runtime_evidence_20260627_124127/debug_events.log`
- MAME stdout/stderr/status: `states/traces/original_arcade_taito_0x563ce_runtime_evidence_20260627_124127/mame_stdout.log`, `mame_stderr.log`, `mame_status.txt`
- PC080SN dumps captured after the later producer exit: `arcade_pc080sn_fg_after_03aaf8.bin`, `arcade_pc080sn_bg_after_03aaf8.bin`, `arcade_pc080sn_fg_after_03aafe.bin`

## OPEN / KNOWN_FINDINGS Impact

- OPEN-019 / OPEN-020: evidence supports the Class B raw low-code remaining-work classification. Issues remain open.
- KF-033: existing canonical finding is consistent with this runtime evidence. No `KNOWN_FINDINGS.md` edit was made in this task.
- No issues opened or closed.

## STOP Status

STOP triggered: **NO**. The original arcade ROM/driver was available, watchpoints fired, the required writer PC mapped exactly through `address_map.json`, and the task did not require source/spec/tool/ROM/build changes.
