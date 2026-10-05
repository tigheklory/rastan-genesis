# Build 0400 Provisional NOP Inventory (machine-derived support artifact)

Status: SUPPORT ARTIFACT for Cody's independent audit. No cleanup, no production change, no ROM,
counter 400. **Provisional — Cody must independently verify every number.** Nothing here authorizes
removing anything (see Part 19 cautions below).

Method: decoded-instruction count from `build/genesis_postpatch.disasm.txt` (lines decoding to `nop`
= 0x4E71), NOT a raw byte scan (data can contain 0x4E71). Grouped into consecutive 2-byte runs.
Provenance cross-referenced against `specs/rastan_direct_remap.json` and the semantic-remap pipeline.

## Totals [M, machine-derived]
- **Total decoded NOP instructions: 1499** (2998 bytes) in **85 runs**.
- Single NOPs: 39 runs. Multi-NOP runs: 46.
- Spec entries that introduce NOPs: `opcode_replace` 12 of 231, `shift_replacements` 3 of 76.

## Confirmed introduced (semantic-remap) [M]
- **0x3A20C x6 (12 bytes)** — the arcade Level-5 watchdog/IO kick (`clr.w 0x350008` + `move.w %d0,0x3C0000`,
  two instructions / 12 bytes) replaced by six 2-byte NOPs. Execution class: **EVERY GAMEPLAY TICK**
  (the VBlank worker runs them every serviced handler). This is the canonical example of NOP scaffolding
  the target conversion must eliminate via semantic reflow, not preserve.

## Largest NOP runs (provenance UNKNOWN pending per-run manifest cross-ref) [provisional]
| runtime addr | NOP count | bytes | region | provisional class |
|---|---|---|---|---|
| 0x05A11A | 245 | 490 | arcade PC090OJ status/frontend area | UNKNOWN (retired-producer stub? or data) |
| 0x041FB6 | 172 | 344 | arcade gameplay/sprite area | UNKNOWN |
| 0x046002 | 125 | 250 | arcade | UNKNOWN |
| 0x03CB58 | 112 | 224 | arcade | UNKNOWN |
| 0x03BA0A | 83 | 166 | arcade | UNKNOWN |
| 0x03C4EA | 73 | 146 | arcade | UNKNOWN |
| 0x03C78E | 60 | 120 | arcade | UNKNOWN |
| 0x054176 | 57 | 114 | arcade | UNKNOWN |
| 0x03C83E | 55 | 110 | arcade | UNKNOWN |
| 0x056114 | 43 | 86 | arcade frontend (0x56114 = retired transient-item producer per source comments) | UNKNOWN (likely retired-producer stub) |

These large runs are in retained **arcade** address space. They are most likely either (a) retired
arcade producers the remap stubbed to NOP, or (b) original-arcade padding/data the disassembler decoded
as NOP. **Distinguishing (a) from (b) requires per-run cross-reference against the remap manifest and
the original arcade disassembly, which this provisional pass did not complete.** Do not assume they are
removable scaffolding without that proof.

## Provenance buckets (provisional — NOT fully resolved)
- Original arcade/Taito NOPs: UNKNOWN count (needs arcade-disasm cross-ref).
- JSON/Python-remapper-introduced NOPs: at least the 0x3A20C x6; the 12+3 nop-mentioning spec entries
  bound the rest, but their exact runtime footprints were not individually mapped here.
- Genesis-native assembly NOPs: UNKNOWN (e.g. controller TH-transition delays — see Part 19).
- Unknown provenance: the large arcade-region runs above.

## Execution-class notes [provisional]
- **EVERY GAMEPLAY TICK:** 0x3A20C x6 (watchdog replacement) — confirmed.
- **CONDITIONAL GAMEPLAY / FRONTEND / SCENE / STARTUP / UNREACHABLE-RETIRED:** the large arcade-region
  runs are candidates for RETIRED (stubbed dead producers) but are marked UNKNOWN until reachability is
  proven. Do not make uncertain reachability claims.

## Part 19 — NOT every NOP is bad scaffolding
Some NOPs may be REQUIRED HARDWARE TIMING (e.g. Genesis controller TH-transition settle delays in the
input-read path) or ALIGNMENT/STRUCTURAL. These must be classified separately and NOT removed. This
pass did not classify by hardware-timing requirement; that is required before any removal is considered.
Suggested classes for the eventual (separate, authorized) cleanup: REMOVE-VIA-SEMANTIC-REFLOW /
REQUIRED-HARDWARE-TIMING / UNREACHABLE-ZERO-COST / ALIGNMENT-STRUCTURAL / UNKNOWN.

## Target rule (Part 15)
The frame-worker conversion must NOT solve obsolete arcade instructions by leaving permanent NOP
padding, RTS+NOP padding, branch-around-NOP, equal-length dead replacement, or a new trampoline where
the semantic mapper can remove/reflow code. The future normal mainline worker should simply NOT CONTAIN
the obsolete arcade-only hardware operations (watchdog/IO kick, IRQ-only IPL wrapper, RTE glue) in its
semantic execution path — removed/shortened through the JSON spec → Python postpatcher → shift-table
reflow → automatic reference repair pipeline (see the semantic-remapper section of
`Andy_build0400_timing_instrument_repair.md`).
