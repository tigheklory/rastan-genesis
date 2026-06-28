# Cody - Shared PC080SN Text Writer 0x0565A6 Caller Destination Census, Build 0112

**Date:** 2026-06-28  
**Type:** Evidence / analysis only  
**Baseline ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0112.bin`  
**SHA256:** `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`  
**Scope:** Caller/destination census for the shared PC080SN text writer at `runtime_genesis_pc 0x000565A6` / `arcade_pc 0x000563A6`. No source/spec/tool/Makefile/ROM/build changes. No bookmark. No diagnostics inserted into ROM. No dispatcher design or implementation.

## Phase 0

Read: `RULES.md`, `ARCHITECTURE.md`, recent `AGENTS_LOG.md`, `KNOWN_FINDINGS.md` / `OPEN_ISSUES.md` / `CLOSED_ISSUES.md` context, `docs/design/Andy_C00828_itemdesc_bg_producer_route_design.md`, and `docs/design/Cody_build0112_blastem_C00828_bg_raw_write_evidence.md`.

Architecture compliance: PASS. This task records arcade-code intent and generated-ROM behavior only. It does not alter execution.

Address discipline: PASS. Every `runtime_genesis_pc` / `genesis_rom_offset` to `arcade_pc` correlation below is an exact lookup through `build/rastan-direct/address_map.json`. No `+0x200` arithmetic is used as proof.

Relevant priors:

- KF-032: raw copied PC080SN writes must route through Genesis staging, not VDP mirror.
- KF-036: arcade work-RAM helper reads must use mapped Genesis WRAM base. No text source consumed by this writer surface is work-RAM; two table-selecting callers read a selector byte at literal `0x0010C118`, noted separately below.
- OPEN-022: `HW_ADDRESS 0x00C00828` BG raw-write freeze.
- OPEN-018: broader raw copied PC080SN write class remains open.

## Evidence Artifacts

Runtime evidence reused from the prior C00828 watchpoint:

- `states/traces/build_0112_c00828_bg_raw_write_evidence_20260628_164543/`
- Key result: `runtime_genesis_pc 0x0005623C` reached the writer with `%a1=0x00C00828`, `%a0=0x0005692A`, `%d1=0`.

Additional census attempts / static artifacts created this task:

- `states/traces/build_0112_text_writer_0565A6_caller_census_20260628_172120/` - native-debug attempt; the accidental full instruction trace was discarded because it was oversized and not used as evidence.
- `states/traces/build_0112_text_writer_0565A6_caller_census_printf_20260628_172827/` - native-debug `printf` attempt; no usable rows.
- `states/traces/build_0112_text_writer_0565A6_caller_census_lua*/` / `..._window_.../` - MAME Lua observer attempts; scripts loaded but frame/exec callbacks did not tick in this environment, so no runtime rows were used from them.

Manual input note: the windowed MAME attempt is excluded from evidence. It produced only `SCRIPT_LOADED`, no caller rows, so any user input during that window did not contaminate the census.

## Caller List Completeness

Full generated-disassembly search for direct calls to `runtime_genesis_pc 0x000565A6` finds exactly six call sites:

```text
0x0005623C  bsr.w 0x565A6
0x00056266  bsr.w 0x565A6
0x000563F8  bsr.w 0x565A6
0x00056420  bsr.w 0x565A6
0x000576FC  bsr.w 0x565A6
0x0005A6CE  jsr   0x565A6
```

No additional direct `bsr/jsr/jmp` call sites were found in `build/genesis_postpatch.disasm.txt`.

Exact `address_map.json` mappings:

| runtime_genesis_pc | arcade_pc | kind |
|---|---|---|
| `0x0005623C` | `0x0005603C` | `arcade_copy` |
| `0x00056266` | `0x00056066` | `arcade_copy` |
| `0x000563F8` | `0x000561F8` | `arcade_copy` |
| `0x00056420` | `0x00056220` | `arcade_copy` |
| `0x000576FC` | `0x000574FC` | `arcade_copy` |
| `0x0005A6CE` | `0x0005A4CE` | `arcade_copy` |
| writer `0x000565A6` | `0x000563A6` | `arcade_copy` |

## Shared Writer Shape

The writer is uniform for all callers:

```asm
runtime_genesis_pc 0x000565A6: movea.l %a1,%a2
0x000565AA: move.b (%a0)+,%d0
0x000565AC: cmpi.b #0,%d0       ; terminate
0x000565B2: cmpi.b #0xFF,%d0    ; row/page advance
0x000565B8: move.w %d1,(%a1)+   ; attr word
0x000565BA: bsr.w 0x565CE       ; punctuation substitution, d0 -> d0
0x000565BE: move.w %d0,(%a1)+   ; code word
0x000565C2: adda.l #0x200,%a2   ; 0xFF advance
0x000565C8: movea.l %a2,%a1
0x000565CC: rts
```

Write shape: per non-control byte, one attr word from `%d1` followed by one code word from `%d0` after `0x565CE` substitution. `0x00` terminates; `0xFF` advances destination by `0x200` bytes. No caller uses a different write shape.

Plane decode used for the census:

- BG C-window: `HW_ADDRESS 0x00C00000..0x00C03FFF`
- FG C-window: `HW_ADDRESS 0x00C08000..0x00C0BFFF`
- `cell = (addr - base) >> 2`, `col = cell & 0x3F`, `row = (cell >> 6) & 0x1F`

## Per-Caller Census

| caller runtime / arcade | destinations | plane / row-col | attr handling | source | fixed/varying | no-input runtime observed | dispatcher route | staging-safe |
|---|---|---|---|---|---|---|---|---|
| `0x0005623C` / `0x0005603C` | `HW_ADDRESS 0x00C00828` | BG row 8 col 10 | fixed `0x0000` | ROM `runtime 0x0005692A` / `arcade 0x0005672A`; item text starts `AXE INCREASES YOUR...` | fixed | YES, prior C00828 watchpoint | BG | YES |
| `0x00056266` / `0x00056066` | `HW_ADDRESS 0x00C00028` | BG row 0 col 10 | fixed `0x0000` | ROM `runtime 0x00056B7E` / `arcade 0x0005697E`; item text starts `RING WEAPON SPEED UP...` | fixed | not observed in available no-input runtime rows | BG | YES |
| `0x000563F8` / `0x000561F8` | table `runtime 0x000564CA`: `0x00C00C64` for entries 0-3 and 5; `0x00C00A64` for entry 4 | BG row 12 col 25, or BG row 10 col 25 | fixed `0x0000` | table ROM pointers `0x5653E,0x56580,0x565C2,0x56604,0x56646,0x56688`; exact mapped entries mostly `arcade_copy`, one patched-site source at `0x56646` | varying by selector byte read at literal `0x0010C118` | not observed in available no-input runtime rows | BG | YES |
| `0x00056420` / `0x00056220` | table `runtime 0x000564FA`: all entries `0x00C00C48` | BG row 12 col 18 | fixed `0x0000` | table ROM pointers `0x566CA,0x566DA,0x566EA,0x566FA,0x5670A,0x5671A`, all mapped `arcade_copy` | varying by selector byte read at literal `0x0010C118` | not observed in available no-input runtime rows | BG | YES |
| `0x000576FC` / `0x000574FC` | table literal pair at `runtime 0x00057B08`: `0x00C0095C` | BG row 9 col 23 | fixed `0x0000` | ROM pointer `runtime 0x00057910` / `arcade 0x00057710`; first source byte is `0x00`, so static decode emits no cells if called in this image | fixed table pair | not observed in available no-input runtime rows | BG | YES / no-op if source remains `0x00` |
| `0x0005A6CE` / `0x0005A4CE` | table `runtime 0x0005A7AC`, 13 entries, all BG C-window: `0xC0074C`, `0xC00A20`, `0xC00A74`, `0xC00C1C`, `0xC00C30`, `0xC00E24`, `0xC0101C`, `0xC0103C`, `0xC01224`, `0xC01234`, `0xC01270`, `0xC01430`, `0xC01634` | BG rows 7,10,12,14,16,18,20,22; cols 7-29 | table-driven attr: `0x0003`, `0x0004`, `0x0005` | table ROM pointers `0x5A630..0x5A6E8`, all mapped `arcade_copy` | varying table entries until `attr=0x00FF` terminator | not observed in available no-input runtime rows | BG | YES, if dispatcher preserves nonzero attr composition |

### Table Details

`0x563F8` table (`runtime 0x564CA`, selected by byte at literal `0x0010C118` minus 1):

| idx | source runtime | source map kind | dest | plane row-col | attr |
|---:|---|---|---|---|---|
| 0 | `0x05653E` | `arcade_copy` | `0x00C00C64` | BG r12 c25 | `0x0000` |
| 1 | `0x056580` | `arcade_copy` | `0x00C00C64` | BG r12 c25 | `0x0000` |
| 2 | `0x0565C2` | `arcade_copy` | `0x00C00C64` | BG r12 c25 | `0x0000` |
| 3 | `0x056604` | `arcade_copy` | `0x00C00C64` | BG r12 c25 | `0x0000` |
| 4 | `0x056646` | `patched_site` | `0x00C00A64` | BG r10 c25 | `0x0000` |
| 5 | `0x056688` | `arcade_copy` | `0x00C00C64` | BG r12 c25 | `0x0000` |

`0x56420` table (`runtime 0x564FA`, selected by byte at literal `0x0010C118` minus 1):

| idx | source runtime | source map kind | dest | plane row-col | attr |
|---:|---|---|---|---|---|
| 0 | `0x0566CA` | `arcade_copy` | `0x00C00C48` | BG r12 c18 | `0x0000` |
| 1 | `0x0566DA` | `arcade_copy` | `0x00C00C48` | BG r12 c18 | `0x0000` |
| 2 | `0x0566EA` | `arcade_copy` | `0x00C00C48` | BG r12 c18 | `0x0000` |
| 3 | `0x0566FA` | `arcade_copy` | `0x00C00C48` | BG r12 c18 | `0x0000` |
| 4 | `0x05670A` | `arcade_copy` | `0x00C00C48` | BG r12 c18 | `0x0000` |
| 5 | `0x05671A` | `arcade_copy` | `0x00C00C48` | BG r12 c18 | `0x0000` |

`0x5A6CE` attr/dest/source table (`runtime 0x5A7AC`, terminates at attr `0x00FF`):

| idx | attr | source runtime | source map kind | dest | plane row-col |
|---:|---:|---|---|---|---|
| 0 | `0x0004` | `0x05A630` | `arcade_copy` | `0x00C0074C` | BG r7 c19 |
| 1 | `0x0003` | `0x05A638` | `arcade_copy` | `0x00C00A20` | BG r10 c8 |
| 2 | `0x0004` | `0x05A64E` | `arcade_copy` | `0x00C00A74` | BG r10 c29 |
| 3 | `0x0004` | `0x05A658` | `arcade_copy` | `0x00C00C1C` | BG r12 c7 |
| 4 | `0x0003` | `0x05A662` | `arcade_copy` | `0x00C00C30` | BG r12 c12 |
| 5 | `0x0003` | `0x05A67C` | `arcade_copy` | `0x00C00E24` | BG r14 c9 |
| 6 | `0x0003` | `0x05A698` | `arcade_copy` | `0x00C0101C` | BG r16 c7 |
| 7 | `0x0005` | `0x05A6A0` | `arcade_copy` | `0x00C0103C` | BG r16 c15 |
| 8 | `0x0003` | `0x05A6B8` | `arcade_copy` | `0x00C01224` | BG r18 c9 |
| 9 | `0x0005` | `0x05A6BC` | `arcade_copy` | `0x00C01234` | BG r18 c13 |
| 10 | `0x0003` | `0x05A6CC` | `arcade_copy` | `0x00C01270` | BG r18 c28 |
| 11 | `0x0003` | `0x05A6D4` | `arcade_copy` | `0x00C01430` | BG r20 c12 |
| 12 | `0x0004` | `0x05A6E8` | `arcade_copy` | `0x00C01634` | BG r22 c13 |

## Work-RAM Source Check

No text source consumed by the writer surface is a work-RAM source. All decoded `%a0` source pointers are ROM/runtime addresses covered by `address_map.json` as `arcade_copy` or, for one static table entry, a `patched_site` runtime address.

Two table-driven callers (`0x563F8` and `0x56420`) use `move.b 0x0010C118,%d0` as a selector before loading table source/dest pointers. That selector read is not a text source. It is recorded as a separate static observation and is not treated as a KF-036 text-source-base issue in this census.

## Dispatcher Feasibility Assessment

- All destinations BG/FG C-window? YES. More specifically, all resolved destinations are BG C-window (`HW_ADDRESS 0x00C00000..0x00C03FFF`). No FG destinations were found in this writer surface.
- Non-C-window destinations? NO.
- Table-driven attr handling at `0x5A6CE`: YES, attrs `0x0003`, `0x0004`, and `0x0005` occur. A future dispatcher would need to preserve `%d1` as the attr half of the composed cell. This is still the same attr/code text-producer shape.
- Any non-text-producer caller? NO. All six callers enter the same writer and therefore share the same `attr word -> substitution -> code word`, `0xFF` advance, `0x00` terminate behavior.

## Classification

**A - ALL CALLERS BG/FG C-WINDOW TEXT.**

The static destination census is complete for all six direct callers and every resolved destination is BG C-window. A single `%a1`-range dispatcher at the writer entry is feasible from the destination/write-shape evidence: BG range routes to BG staging; no FG/other special case was found. The `0x5A6CE` table-driven attr path is not a divergent write shape, but it requires preserving nonzero attr composition.

Runtime caveat: only `0x5623C` was runtime-observed in available no-input evidence. MAME Lua observer attempts in this environment did not tick frame/exec callbacks, and a user input occurred during a windowed attempt that produced no event rows; those attempts are not used as runtime evidence. The four indirect callers are resolved by static table decode, not by no-input reachability proof.

## Recommendation (Scoping Only)

Dispatcher viability evidence is positive: a future Andy design can consider a writer-entry dispatcher keyed by `%a1` destination range, with BG C-window calls routed to BG staging and attr/code composition preserved, including nonzero attrs from `0x5A6CE`.

No dispatcher design or implementation is made here. No issue is closed here.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-022: extended with full shared-writer caller/destination evidence; remains open.
- OPEN-018 / KF-032: context; this writer is another raw PC080SN class surface; remains open.
- OPEN-001: context only.
- OPEN-015: not touched.
- CLOSED-015/016/017: not reopened.
- `KNOWN_FINDINGS.md`: no update in this evidence-only task.

## STOP

STOP triggered: NO. The requested evidence was produced without source/spec/tool/ROM/build changes. Runtime no-input reachability is limited to the previously observed `0x5623C` path; unresolved runtime reachability is labeled explicitly rather than inferred.
