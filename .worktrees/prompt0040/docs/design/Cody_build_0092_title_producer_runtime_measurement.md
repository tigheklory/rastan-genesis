# Cody - Build 0092 Title Producer Runtime Measurement

**Date:** 2026-06-22  
**Type:** Runtime measurement / evidence capture only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin`  
**ROM SHA256:** `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`  
**Scope:** Existing Build 0092 ROM only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No bookmark cycle. No diagnostic ROM. No source/ROM instrumentation. Start/C/A crash, OPEN-015, BG producer path, `0x3ACEA`, sprites/palette/scroll/general graphics are deferred.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028 (input shim/title text/OPEN-016 Part 2), KF-013 (text producer in VBlank), KF-011 (arcade VBlank owns frame lifecycle), KF-010 (FG -> Plane A), KF-004 (runtime PC = ROM file offset), KF-006 (`+0x200` identity), and KF-001 as context only. Rediscovery-Hazard HIGH findings touched: KF-028, KF-013, KF-011, KF-010. None contradicted.

Open issues touched: OPEN-016 and OPEN-001 active, OPEN-015 context only. Closed issues touched: none. Deferred-appendix entries relevant: none. Architecture compliance: confirmed.

## Method

ROM SHA was verified before measurement. Runtime observation used external emulator-side MAME debugger scripts only, via the existing `tools/mame/run_genesis_trace_wsl.sh` workflow.

Main trace artifacts:
- `states/traces/build_0092_title_producer_entry_window_trace_20260622_160411/`
- `mame_title_producer_entry_window.cmd`
- `native_debug_trace.log`
- `native_events.log`
- `title_producer_runtime_analysis.json`
- `title_producer_runtime_analysis.md`

An initial debugger `printf` attempt in `states/traces/build_0092_title_producer_entry_window_trace_20260622_160321/` produced no event lines, so the measurement switched to the proven `trace`/`tracelog` path.

Added narrow component probe:
- `states/traces/build_0092_title_producer_component_probe_20260622_160657/`
- `mame_title_producer_component_probe.cmd`
- `native_debug_trace.log`
- `native_events.log`

The component probe adds emulator-only breakpoints around the shared cell-composition helper to explain why the required `0x70794` stores write zero. It does not modify project source/tooling or ROM artifacts.

## Required Evidence

### 1. Producer Entry And First Render

`runtime_genesis_pc 0x0003ACAE` and `0x0003ACB6` both executed exactly once at derived frame 212. State at both points was the expected title-entry render state: `%a5@(0)=0`, `%a5@(2)=1`, `%a5@(4)=1`.

```text
EVENT PRODUCER_3ACAE cyc=31333256 pc=03ACB0 sr=2704 s0=0000 s2=0001 s4=0001 d0=00000000 d1=00000002 a5=00FF0000 sp=00FEFFE8
EVENT PRODUCER_FIRST_RENDER_3ACB6 cyc=31347428 pc=03ACB8 sr=2700 s0=0000 s2=0001 s4=0001 d0=00000011 d1=00000000 a5=00FF0000 sp=00FEFFE8
```

`d0=0x11` at `0x3ACB6`, confirming the first title glyph render ID 17.

### 2. FG Store Execution

`runtime_genesis_pc 0x00070794` executed 258 times. Every sampled store had `%a6=0x00FF501A` (`staged_fg_buffer`) and an in-buffer `%d2` offset. However, every store had `%d1=0x0000`, so every staged cell value was zero.

```text
EVENT FG_STORE_70794 cyc=3329434 pc=070796 sr=2700 a6=00FF501A d2=00000F42 d1=00000000 d5=0000001E d6=00000021 eff=00FF5F5C sp=00FEFF9C
EVENT FG_STORE_70794 cyc=3330572 pc=070796 sr=2700 a6=00FF501A d2=00000F44 d1=00000000 d5=0000001E d6=00000022 eff=00FF5F5E sp=00FEFF9C
```

### 3. FG Range Gate

`runtime_genesis_pc 0x000707E4` gate hit 258 times and `runtime_genesis_pc 0x00070816` accept path hit 258 times. No rejection or misroute was observed.

```text
EVENT FG_RANGE_GATE_707E4 cyc=3329206 pc=0707E6 sr=2704 a2=00C09E86 d0=00000043 d1=00000000 d2=00000000 a6=00FF501A sp=00FEFFB0
EVENT FG_RANGE_ACCEPT_70816 cyc=3329380 pc=070818 sr=2710 a2=00C09E86 d0=000007A1 d1=00000000 d2=00000000 d5=0000001E d6=00000021 a6=00FF501A sp=00FEFFA0
```

### 4. FG Staging Writes

FG staging write-watchpoint totals:
- Total `FG_STAGING_WRITE`: 2306
- Nonzero FG staging writes: 0

The store path writes the expected buffer, but it writes clear cells only.

### 5. BG Staging Observe-Only

BG staging write-watchpoint totals:
- Total `BG_STAGING_WRITE`: 9944
- Nonzero BG staging writes: 0

This was observe-only per scope. No BG producer investigation was performed.

### 6. `%a5@(4)=2` Writer Sites

Only the producer tail writer fired: `runtime_genesis_pc 0x0003ACF8`. The other known `%a5@(4)=2` writer sites (`0x3A406`, `0x3A96A`, `0x3A9E6`, `0x3AA58`) did not fire in this traced title-entry window.

```text
EVENT STATE4_WRITE_2_SITE_3ACF8 cyc=31531048 pc=03ACFA sr=2700 s0=0000 s2=0001 s4_before=0001 d0=00000000 a5=00FF0000 sp=00FEFFE8
```

This proves the steady `(0,1,2)` state came from the title producer tail, not a bypass writer.

## Resolved Classification

**P2 - producer emits no nonzero staged cells (zero-cell output).**

This is a narrowed P2 result. The producer path is reached, the first render call executes, the FG range gate accepts, and `0x70794` writes to `staged_fg_buffer`. The failure is that every composed cell value at the actual store is `0x0000`. This is not P1 (producer non-reach), not P3 (range rejection/misroute), and not P4 (later clear); no later nonzero-to-zero overwrite was observed because no nonzero FG staged cell was ever produced.

## Component Probe

The added component probe shows the value is lost inside the shared cell-composition path before the staging write. Tile LUT lookups produce nonzero tile IDs, but `%d7` is zero by the final composition point and `%d1_cell` becomes zero.

```text
EVENT TILE_LUT_AFTER_707D2 cyc=3333432 pc=0707D4 sr=2700 d0=00000049 d1=00000002 d2=00000000 d7_tile=0000001F a3=000F1F2C a5=000F9F2C a6=00FF501A sp=00FEFFB0
EVENT ATTR_LUT_AFTER_70788 cyc=3333700 pc=07078A sr=2704 d0=00000049 d1=00000000 d2_attr=00000000 a3=000F1F2C a5=000F9F2C a6=00FF501A sp=00FEFFAC
EVENT CELL_COMPOSE_AFTER_OR_707E0 cyc=3333720 pc=0707E2 sr=2704 d0=00000049 d1_cell=00000000 d2_attr=00000000 d7_tile=00000000 a3=000F1F2C a5=000F9F2C a6=00FF501A sp=00FEFFB0
EVENT FG_STORE_70794 cyc=3333986 pc=070796 sr=2700 a6=00FF501A d2=00000F4A d1=00000000 d5=0000001E d6=00000025 eff=00FF5F64 sp=00FEFF9C
```

Evidence-level conclusion: the title producer reaches staging, but cell composition produces zero cells. The immediate observed mechanism is that a nonzero tile LUT result exists after `0x707D2`, then is gone by `0x707E0` before the final cell value is stored.

## Assessment

The prompt's P5 question is resolved by runtime evidence. Title producer entry does happen; the title render path does reach the shared FG staging store; the accepted destination and `%a6` base are correct. The first failing layer is no longer producer reachability or range acceptance. It is cell-value composition before the FG staging write.

Recommended next task: a bounded implementation/verification task on the shared FG cell-composition path used by `genesistan_hook_glyph_renderer_3bd48`, specifically preserving or correctly composing the tile LUT result through the attr-helper portion before `0x707E0`. No fix is made here.

## Open / Closed Issues Impact

Open issues touched: OPEN-016 (active; live gap is now zero-cell composition output), OPEN-001 (active; graphics still fail), OPEN-015 (context only). Closed issues touched: none. New issues opened: none. Issues closed: none.

Intentionally deferred: Start/C/A crash, OPEN-015 crash-handler defects, BG producer path, `0x3ACEA` direct one-shot writer, sprites/palette/scroll/general graphics, broader unhooked-writer survey.

## KNOWN_FINDINGS Impact

**Option C - proposed KF-028 refinement.** Proposed addition:

> Build 0092 runtime entry-window trace resolves the title producer P5: `0x3ACAE` and first render `0x3ACB6` execute once at frame 212 with `%a5@(0/2/4)=0/1/1`; only `%a5@(4)=2` writer fired is `0x3ACF8`; FG range gate accepts and `0x70794` writes `staged_fg_buffer`, but every composed cell written is `0x0000`. Component probe shows tile LUT returns nonzero values (for example `d7_tile=0x001F`) before cell composition, but the value is gone by `0x707E0`, so `%d1_cell=0x0000`. Classification: P2 zero-cell output, not producer non-reach, not range rejection, not later clear.

`KNOWN_FINDINGS.md` was not modified in this task.

## STOP

STOP triggered: **NO**. The logs cover reset through the title-entry transition and support one resolved class: **P2 zero-cell output**.
