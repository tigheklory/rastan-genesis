# Cody - Build 0115 Item-Description ADDRESS ERROR + Scroll-Position Evidence

**Date:** 2026-06-29  
**Type:** Runtime evidence / analysis only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0115.bin`  
**ROM SHA256:** `5af34e440a79f2d9d447a767592ea903d026edea3f174a97d446b03ed23026e3`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark cycle. No diagnostics inserted. No fix design or implementation.

## Phase 0

Classification: **EXTENDING**. This task extends the Build 0115 shared text-writer dispatcher evidence with runtime crash and scroll/staging observations from the item-description page.

Relevant priors loaded: OPEN-015 (crash-handler on-screen numeric fields are unreliable; WRAM crash record is authoritative), KF-010 (Genesis BG/FG staging and full-plane scroll commit), KF-032 / OPEN-022 (raw PC080SN writes routed through staging), KF-036 (mapped work-RAM base discipline), OPEN-023 (Window absent expected), and OPEN-024 (PC090OJ incomplete expected). No contradiction detected.

Address discipline: runtime-to-arcade correlations below use exact `build/rastan-direct/address_map.json` segments. No arithmetic offset is used as proof.

## Evidence Artifacts

- Main trace directory: `states/traces/build_0115_itemdesc_crash_scroll_evidence_20260629_090111/`
- Main event log: `states/traces/build_0115_itemdesc_crash_scroll_evidence_20260629_090111/native_events.log`
- Main staging dumps:
  - `staged_bg_before_item_5622c.bin`
  - `staged_fg_before_item_5622c.bin`
  - `staged_bg_before_writer_5623c.bin`
  - `staged_bg_after_writer_56240.bin`
  - `staged_bg_before_sprite_56314.bin`
  - `staged_bg_after_sprite_5631a.bin`
  - `dump_summary.json`
- Crash trace directory: `states/traces/build_0115_itemdesc_crash_longcheck_20260629_090635/`
- Crash record: `states/traces/build_0115_itemdesc_crash_longcheck_20260629_090635/crash_record_ff6800.bin`
- Crash-time BG staging: `states/traces/build_0115_itemdesc_crash_longcheck_20260629_090635/staged_bg_at_crash.bin`
- Stack/WRAM trace directory: `states/traces/build_0115_itemdesc_crash_stackdump_20260629_090832/`
- Stack dump: `states/traces/build_0115_itemdesc_crash_stackdump_20260629_090832/stack_region_feff80.bin`
- WRAM state dump: `states/traces/build_0115_itemdesc_crash_stackdump_20260629_090832/wram_state_ff0000.bin`

## Part A - ADDRESS ERROR Evidence

### Crash Record

Reliable debugger/WRAM crash-record values:

- Exception type: `3` = ADDRESS ERROR. The stored byte appears in the high byte of the word record; the on-screen value is not used because of OPEN-015.
- `CRASH_STACKED_SR`: `0x2700`
- `CRASH_STACKED_PC`: `runtime_genesis_pc 0x00055B1C`
- `CRASH_FAULT_ADDRESS`: `0x0000000F`
- `CRASH_ACCESS_TYPE` / frame word: `0x34D5`
- Instruction register from group-0 frame: `0x34D4`
- Genuine saved address registers include `%a4 = 0x0000000F`, `%a5 = 0x00FF0000`, `%a6 = 0x00FF0298`, `%a2 = 0x0010D080`, `%a3 = 0x00059B50`. Per OPEN-015, `D0-D5/A0/A1` are not treated as true at-fault registers.

Group-0 frame bytes at the stack boundary include:

```text
34D5 0000 000F 34D4 2700 0005 5B1C
```

Interpreted as frame/access word `0x34D5`, fault address `0x0000000F`, IR `0x34D4`, stacked SR `0x2700`, and stacked PC `0x00055B1C`.

### Faulting Instruction

`IR=0x34D4` matches the first word of this copied-arcade instruction:

```asm
runtime_genesis_pc 0x00055B1A: 34d4    movew %a4@,%a2@+
runtime_genesis_pc 0x00055B1C: 4281    clrl %d1
```

Observable fact: the faulting operation is a word read from `(%a4)` where `%a4 = 0x0000000F`, an odd address. The instruction would then write to `(%a2)+`, but the address error is explained by the odd source read.

Exact address-map results:

| Runtime Genesis PC | Segment | Arcade PC | Meaning |
|---|---|---|---|
| `0x00055B1A` | `arcade_copy` segment 164 | `0x0005591A` | faulting `movew %a4@,%a2@+` |
| `0x00055B1C` | `arcade_copy` segment 164 | `0x0005591C` | stacked PC / following `clrl %d1` |

This is copied arcade logic, not a Genesis-only helper and not a patched-site dispatcher.

### Path and Breadcrumbs

The stack region contains return-address breadcrumbs consistent with the crash occurring during the item/attract update path after the item-description text producer has run:

| Runtime Genesis PC | Mapping result | Local disassembly line |
|---|---|---|
| `0x000505E0` | mapped arcade-copy breadcrumb | `bsrw 0x55e2e` |
| `0x0005040A` | mapped arcade-copy breadcrumb | `bsrw 0x506fa` |
| `0x0004551C` | mapped arcade-copy breadcrumb | `movew %a5@(4674),%d0` |
| `0x0003A85C` | mapped arcade-copy breadcrumb | `movew #5,%a5@(4)` |
| `0x0003A274` | mapped arcade-copy breadcrumb | VBlank tail call region |
| `0x0003A1AC` | mapped arcade-copy breadcrumb | watchdog/reset routine return boundary |
| `0x0003B296` | mapped arcade-copy breadcrumb | main-loop branch region |

Because a raw stack scan can include data-like longwords, this is recorded as breadcrumb evidence, not a fully reconstructed call graph. The faulting PC/instruction and item-page state are exact.

### Item State at Crash

The crash-time WRAM state begins with:

```text
FF0000: 0002 0002 0004 ...
```

So the crash occurs with:

- `%a5@(0) = 0x0002`
- `%a5@(2) = 0x0002`
- `%a5@(4) = 0x0004`
- `%a5@(44) = 0x0000` from `WRAM 0xFF002C`

The text page entry earlier in the trace occurred at `runtime_genesis_pc 0x0005622C` with `%a5@(0)=2`, `%a5@(2)=2`, `%a5@(4)=6`; the later crash is after the page has advanced to sub-state `4`.

### Classification

**Classification: D - scroll/tilemap mechanism fault.**

Reasoning:

- The faulting instruction is copied arcade code at `runtime_genesis_pc 0x00055B1A` / `arcade_pc 0x0005591A`.
- It dereferences an invalid odd pointer value in `%a4 = 0x0000000F` while using arcade scratch/table bases around `0x10D000/0x10D040/0x10D080`.
- It is not the shared text-writer dispatcher (`0x565A6 -> 0x714C8`) and not the item sprite helper (`0x56314 -> 0x71CE2`).
- Rebase of the shared text writer is not implicated; the text-writer dispatcher had already returned, and the fault is in a later copied arcade table/scroll/tilemap update routine.

This is a downstream copied-arcade state/path fault, not evidence that the Build 0115 text-writer dispatcher is the immediate faulting site.

## Part B - Scroll / Vertical Position Evidence

### Item-Page Scroll Writes

During the item-page window, staged scroll writes go to zero values:

```text
pc=055CC2 -> WRAM 0xFF4012 staged_scroll_x_bg = 0x0000
pc=055CCA -> WRAM 0xFF4018 staged_scroll_y_fg = 0x0000
pc=055CD2 -> WRAM 0xFF4014 staged_scroll_x_fg = 0x0000
```

No raw PC080SN scroll writes were observed in the trace:

- `RAW_PC080SN_YSCROLL_WRITE`: `0`
- `RAW_PC080SN_XSCROLL_WRITE`: `0`

### VDP Scroll Commit

In the item state (`%a5@(0)=2`, `%a5@(2)=2`, `%a5@(4)=6`), the VBlank scroll commit fires repeatedly with staged scroll values still zero:

- `vdp_commit_scroll` entry `runtime_genesis_pc 0x000701F0`: 1300 observed entries total.
- In the item state, sampled commits show `x_bg=0`, `x_fg=0`, `y_bg=0`, `y_fg=0`.
- HSCROLL FG write at `0x70204`: `raw_x_fg=0x0000`, committed value after Genesis bias `0xFFF0`.
- HSCROLL BG write at `0x70214`: `raw_x_bg=0x0000`, committed value after Genesis bias `0xFFF0`.
- VSRAM control setup at `0x7021A`.
- VSCROLL FG write at `0x7022C`: `raw_y_fg=0x0000`, committed value after bias `0x0008`.
- VSCROLL BG write at `0x7023A`: `raw_y_bg=0x0000`, committed value after bias `0x0008`.

Observable conclusion: the Genesis scroll commit path is alive and uses full-plane scroll values. This trace does not show line-scroll behavior. The item-page scroll values are zero, so vertical placement issues are not explained by a nonzero scroll offset in this capture.

### Scroll vs Staging Geometry

The item-description text is routed through BG staging. The cells are produced at PC080SN BG C-window destinations such as `HW_ADDRESS 0x00C00828` and `0x00C01428`. The staging conversion maps the PC080SN address to the 32-row Genesis BG staging buffer.

The important behavior is not a scroll register change; it is **staging geometry aliasing**: later PC080SN rows map to the same 32-row Genesis staging addresses as earlier rows and overwrite cells.

## Part C - Missing `F` in `FIRE SWORD`

### Correct Row / Cell Address

The live dispatcher evidence establishes the item-description rows. The `FIRE SWORD` line is emitted at:

- `HW_ADDRESS 0x00C01428`
- PC080SN BG C-window row corresponding to Genesis staging row `20`, column `10`
- Genesis staging address `WRAM 0x00FF4A2E`

This supersedes any earlier rough row guess for `FIRE SWORD`.

### Producer and Staging Evidence

The dispatcher emits the `F` cell:

```text
EVENT DISPATCH_BG_ROUTE_7150C ... dest=00C01428 composed=00000046 code=0046 attr=0000
```

The BG staging store writes a nonzero cell for that `F`:

```text
EVENT BG_STAGING_STORE_7063C ... src_dest=00C01428 off=00000A14 eff=00FF4A2E cell=001C
```

Then a later emitted row aliases to the same staging address and overwrites it with zero:

```text
EVENT BG_STAGING_STORE_7063C ... src_dest=00C03428 off=00000A14 eff=00FF4A2E cell=0000
```

Final staging dumps confirm the result:

- After writer: `WRAM 0x00FF4A2E = 0x0000`
- After writer: `WRAM 0x00FF4A30 = 0x001F` (`I` in `IRE SWORD` remains present)
- Crash-time BG staging preserves the same result: `F` cell zero, `I` cell nonzero.

### Classification for Missing `F`

The missing `F` is **overwritten later**, not:

- not-staged,
- clipped by scroll,
- lost by VDP commit,
- missing from the LUT.

The concrete mechanism is PC080SN row aliasing/wrap into the 32-row Genesis staging buffer: the later row destination `HW_ADDRESS 0x00C03428` maps to the same staging cell as earlier `HW_ADDRESS 0x00C01428` and clears it.

## Summary Answers

- Exact ADDRESS ERROR PC/instruction: **faulting instruction `runtime_genesis_pc 0x00055B1A`, `movew %a4@,%a2@+`; stacked PC `0x00055B1C`; exact map to `arcade_pc 0x0005591A/0x0005591C` via `address_map.json`.**
- Fault address/access: **word source read from odd `0x0000000F` through `%a4`; group-0 frame word `0x34D5`; SR `0x2700`; IR `0x34D4`.**
- Item state: **crash at `%a5@(0)=2`, `%a5@(2)=2`, `%a5@(4)=4`, `%a5@(44)=0`.**
- Rebase check: **not implicated; the fault is copied arcade code, not the shared text-writer dispatcher or a Genesis-only helper.**
- Crash classification: **D - scroll/tilemap mechanism fault.**
- Scroll evidence: **scroll commit alive; staged scroll values zero; full-plane HSCROLL/VSRAM writes only; no raw PC080SN scroll writes observed.**
- Missing `F`: **producer emits and stages it, then later row alias overwrites it with zero.**
- Current implementation implication: **Build 0115 text writer routed the item page into BG staging, but long PC080SN item-description layout aliases in Genesis 32-row staging; the later crash is a separate copied-arcade table/scroll/tilemap fault.**

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: touched; rendering/positioning evidence extended.
- OPEN-022: context; shared text-writer dispatcher is not the immediate crash site.
- OPEN-024: context; item sprite helper path remains outside this evidence task.
- OPEN-015: context; WRAM crash record used instead of on-screen numeric fields.
- Issues opened: NONE.
- Issues closed: NONE.
- `KNOWN_FINDINGS.md`: Option A - no update from this evidence-only task. The evidence should inform the next scoped diagnostic/fix prompt, but no canonical finding was edited here.

## Non-Actions

No source, spec, tool, Makefile, ROM, build artifact, invariant, bookmark, or diagnostic ROM changes were made. No fix was designed or implemented.

## STOP

STOP triggered: **NO**. The faulting instruction, mapped address, scroll evidence, and missing-`F` staging mechanism were captured. The exact higher-level call graph remains represented as stack breadcrumbs rather than overclaimed as a fully decoded call chain.
