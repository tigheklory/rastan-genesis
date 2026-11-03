# Cody Build 55 Active Palette Producer Discovery

## Scope
- Type: read-only runtime trace + disassembly archaeology
- Build context: `rastan-direct` Build 0055
- Sources used:
  - `docs/design/Cody_build55_mame_palette_runtime_trace.md`
  - `states/traces/build55_palette_runtime_trace_20260504_134411/debug.log`
  - `states/traces/build55_active_palette_discovery_20260504_143202/debug.log`
  - `states/traces/build55_active_palette_chain_probe_20260504_150000/debug.log`
  - `build/genesis_postpatch.disasm.txt`
  - `build/maincpu.disasm.txt`
  - `specs/rastan_direct_remap.json`
  - `apps/rastan-direct/out/symbol.txt`

## §1.1 Non-reach result confirmation
Confirmed from prior runtime trace report:
- helper 59ad4 hit_count = 0 (`docs/design/Cody_build55_mame_palette_runtime_trace.md:39`)
- helper 03ab00 hit_count = 0 (`docs/design/Cody_build55_mame_palette_runtime_trace.md:40`)
- helper 45dae hit_count = 0 (`docs/design/Cody_build55_mame_palette_runtime_trace.md:41`)
- `vdp_commit_palette` hit_count = 0 (`docs/design/Cody_build55_mame_palette_runtime_trace.md:42`)
- `_vblank_service` hit_count = 255 (`docs/design/Cody_build55_mame_palette_runtime_trace.md:45`)
- staged palette writes were bootstrap clears only (`docs/design/Cody_build55_mame_palette_runtime_trace.md:49-67`)
- `palette_dirty` writes stayed zero (`docs/design/Cody_build55_mame_palette_runtime_trace.md:69-77`)

State: confirmed.

## §1.2 Arcade execution trajectory (PC histogram)
Primary histogram source: `states/traces/build55_active_palette_discovery_20260504_143202/debug.log`.

Event-derived PC histogram:
- Total logged PC events: `12539`
- Unique PCs: `6`
- Top PCs:
  - `0x03BC84`: `11760`
  - `0x03B102`: `480`
  - `0x0700C4`: `255`
  - `0x00022E`: `15`
  - `0x00024C`: `15`
  - `0x000204`: `14`

Symbol resolution via `apps/rastan-direct/out/symbol.txt`:
- No symbol-map entries for `0x03BC84`, `0x03B102`, `0x00022E`, `0x00024C`, `0x000204` (`rg` returned no matches).
- `0x0700C4` is inside `_vblank_service` (`_vblank_service` symbol at `0x000700C2`, `apps/rastan-direct/out/symbol.txt:155`).

0x100 bucket totals:
- `0x03BC00`: `11760`
- `0x03B100`: `480`
- `0x070000`: `255`
- `0x000200`: `44`

Requested range aggregates (same trace):
- `0x000200..0x0009FF`: `44`
- `0x03A000..0x03A3FF`: `0`
- `0x059000..0x059FFF`: `0`
- `0x03AD00..0x03ADFF`: `0`
- `0x045000..0x045FFF`: `0`
- `0x070000..0x071FFF`: `255`
- `0x0700C2..0x0700FF`: `255`
- `0x000280..0x0002FF`: `0`

Hot loops observed with disassembly back-edges:
- Loop A: `runtime_genesis_pc 0x03BC64..0x03BC84`
  - Back-edge: `0x03BC84: bnes 0x3bc64` (`build/genesis_postpatch.disasm.txt:74826`)
  - Loop body writes to palette RAM via `movew %d0,%a0@+` at `0x03BC80` (`build/genesis_postpatch.disasm.txt:74824`).
- Loop B: `runtime_genesis_pc 0x03B0FE..0x03B102`
  - Back-edge: `0x03B102: bnes 0x3b0fe` (`build/genesis_postpatch.disasm.txt:73901`).
- Loop C (bootstrap clear): `runtime_genesis_pc 0x000294..0x000296`
  - Back-edge: `0x000296: dbf %d7,0x294` (`build/genesis_postpatch.disasm.txt:218`).

## §1.3 Active writes to palette RAM and palette-source buffers

### Arcade palette RAM writes (`0x00200000..0x00200FFF`)
Observed in existing supplemental trace:
- Source: `states/traces/build55_active_palette_discovery_20260504_143202/debug.log`
- Total writes: `11760` (`^WP_PALETTE_RAM` count)
- Writer PC in all sampled lines: `pc=0x03BC84` (e.g., lines `158`, `160`, `162` ... `25132`)
- Sample writes:
  - `debug.log:158` addr=`0x200000` pre=`0x0000` post=`0x00FF` pc=`0x03BC84`
  - `debug.log:160` addr=`0x200002` pre=`0x7BDE` post=`0x0000` pc=`0x03BC84`
  - `debug.log:166` addr=`0x200008` pre=`0x4298` post=`0x0000` pc=`0x03BC84`
  - `debug.log:25132` addr=`0x20061E` pre=`0x0000` post=`0x7001` pc=`0x03BC84`

Relationship to patched sites:
- `0x03BC84` is outside patched runtime sites `0x059CD4`, `0x03AD00`, `0x045FB8`.

### `A5+5632` buffer probe (`0x00FF1600`)
Observed in same trace:
- Total writes: `480` (`^WP_FF1600` count)
- Writer PC: `0x03B102` (sample lines `94..108`, `23556..23564`)
- Sample writes are all zero in sampled events (`pre=0 post=0`).

### Other palette-related WRAM symbols from symbol map
`apps/rastan-direct/out/symbol.txt` palette-related symbols found:
- `palette_dirty` `0x00FF4000` (`line 244`)
- `staged_palette_words` `0x00FF601A` (`line 256`)
- `vdp_commit_palette` `0x000701CC` (`line 159`)
- palette helpers `0x000711E2`, `0x00071248`, `0x0007126C` (`lines 176-178`)

Write-count observations from prior runtime trace (already captured):
- `staged_palette_words`: `960` writes, bootstrap-clear only (`docs/design/Cody_build55_mame_palette_runtime_trace.md:49-67`)
- `palette_dirty`: `15` writes, all `0->0` (`docs/design/Cody_build55_mame_palette_runtime_trace.md:69-77`)

## §1.4 Caller chain analysis for patched sites

### §1.4.a `0x59AD4` callers (30)
Caller list and runtime breakpoints came from prior evidence and probe script; all 30 were checked in
`states/traces/build55_active_palette_discovery_20260504_143202/debug.log` and all had hit_count `0` (`^BP_CALLER_*` counts).

Static caller evidence exists in arcade disassembly (`build/maincpu.disasm.txt`), e.g.:
- `0x511BC: jsr 0x59ad4` (`line 102366`)
- `0x56136: jsr 0x59ad4` (`line 107909`)
- `0x575FE: bsrw 0x59ad4` (`line 109681`)
- `0x5A364: jsr 0x59ad4` (`line 113664`)

Reached callers: `0/30`.

Nearest reached predecessor in this 64s trace: NOT FOUND in the instrumented `0x59AD4` caller set.
Observed active producer path instead is `0x03B110 -> 0x03BBF8 -> 0x03BC64/0x03BC84` (supplemental chain probe, lines `48`, `50`, `52`, and looped `WP_PALETTE_RAM` events).

### §1.4.b `0x03AB00` caller analysis
Patched runtime site:
- `0x03AD00: jsr 0x71248` (`build/genesis_postpatch.disasm.txt:73574`)

Owning routine context:
- routine at `0x03AC90..0x03AD06` with branch to site at `0x03AC9C: bras 0x3ad00` (`build/genesis_postpatch.disasm.txt:73540-73575`).

Runtime reachability from chain probe:
- `BP_SITE_03AD00`: `0`
- `BP_FN_3AC90`: `0`
- `BP_BRAS_TO_3AD00`: `0`

Nearest reached predecessor in this trace: NOT FOUND among instrumented upstream nodes.

### §1.4.c `0x045DB8` caller analysis
Arcade/static chain evidence:
- `0x41F36: bsrw 0x45d72` (`build/maincpu.disasm.txt:83784`)
- `0x45D72` contains call path to `0x45DB8` (`build/maincpu.disasm.txt:88341-88361`)

Patched runtime site and parent in postpatch disassembly:
- `0x42136: bsrw 0x45f72` (`build/genesis_postpatch.disasm.txt:83939`)
- `0x45FB8: jsr 0x7126c` (`build/genesis_postpatch.disasm.txt:88525`)

Runtime reachability from chain probe:
- `BP_SITE_45FB8`: `0`
- `BP_CALL_45F72` (runtime parent equivalent): `0`
- `BP_FN_45F72`: `0`

Nearest reached predecessor in this trace: NOT FOUND among instrumented upstream nodes.

## §1.5 Targeted spec audit for palette caller chains
Target: entries within the three palette-chain areas (`0x59AD4` callers, `0x03AC90..0x03AD00` path, `0x41F36/0x45D72/0x45DB8` path).

Findings in `specs/rastan_direct_remap.json`:
- Palette-site entries present:
  - `0x059AD4` (Build 55 helper hook) (`line 694`)
  - `0x03AB00` (Build 55 helper hook) (`line 700`)
  - `0x045DB8` (Build 55 helper hook) (`line 706`)
- Nearby chain-area entry:
  - `0x03AC54` replacement bytes begin with `6012` and NOP padding (`line 268-271`), documented as crash-path bypass.
- No remap entry found at any of the 30 `0x59AD4` caller PCs.
- No remap entry found at `0x041F36` or `0x045D72` directly.

Suppressing entries conclusively inside the exact static call instructions to patched sites:
- Count: `0` observed at the exact caller instruction PCs (`0x03AC9C`, `0x041F36`, 30 `0x59AD4` caller PCs).

## §1.6 Bootstrap clear re-entry investigation
Observed repeated bootstrap entries from trace:
- `BP_BOOT_0202`: `14`
- `BP_BOOT_022C`: `15`
- `BP_BOOT_024A`: `15`
(from `states/traces/build55_active_palette_discovery_20260504_143202/debug.log` anchored counts)

Static call path:
- `0x022C: bsrw 0x24a` (`build/genesis_postpatch.disasm.txt:197`)
- clear routine starts at `0x024A` (`build/genesis_postpatch.disasm.txt:203`)
- clear-loop writes include `clrb 0xff4000` and staged palette zero loop (`build/genesis_postpatch.disasm.txt:211-219`)

Static caller search for `0x024A`:
- only direct static call found: `0x022C -> 0x024A` (`build/genesis_postpatch.disasm.txt:197`)

Trigger classification:
- Repeated entry to the startup path (`0x0202 -> 0x022C -> 0x024A`) is observed.
- Exact trigger source for re-entry (e.g., reset/exception/vector source) is UNKNOWN from current traces because no vector-origin/call-stack trace was collected.

## §1.7 Classification
Classification: **A. Active palette producer elsewhere**

Cited evidence:
1. All three Build 55 palette helpers remain unreached in 64s traces (`docs/design/Cody_build55_mame_palette_runtime_trace.md:39-42`; also anchored zero-hit counts in `build55_active_palette_discovery_20260504_143202/debug.log`).
2. Arcade palette RAM receives heavy runtime writes (`11760`) from `runtime_genesis_pc 0x03BC84` (`build55_active_palette_discovery_20260504_143202/debug.log:158..25132`).
3. Disassembly at `0x03BC64..0x03BC84` shows active conversion/write loop into `%a0@+` with `%a0` based at `0x200000` via caller `0x03BBF8` (`build/genesis_postpatch.disasm.txt:74785-74827`, especially `74786`, `74824`, `74826`).
4. Supplemental chain probe confirms this path executes (`BP_FN_3B110=15`, `BP_FN_3BBF8=15`, `BP_FN_3BC64=11760`) while patched site chains remain zero-hit (`build55_active_palette_chain_probe_20260504_150000/debug.log`, anchored counts).

## §2 Integrity
- §1.1 non-reach result confirmed: YES
- §1.2 PC histogram extracted: YES
  - Top PCs reported: YES (6 observed)
  - Aggregate ranges reported: YES
  - Hot loops identified: YES
- §1.3 palette RAM and source buffer writes traced: YES
  - New trace required: YES (supplemental chain-probe for upstream predecessor checks)
  - Writes to `0x00200000..0x00200FFF`: `11760`
  - Writes to `0x00FF1600..0x00FF163F`: `480`
- §1.4 caller chain analysis completed: YES
  - `0x59AD4` callers reached/not-reached: `0/30` reached, `30/30` not reached
  - `0x03AB00` owning routine reached: NOT REACHED
  - `0x045DB8` parent reached: NOT REACHED
- §1.5 spec-entry audit for palette chains: YES
  - suppressing entries found at exact caller instruction PCs: `0`
- §1.6 bootstrap re-entry investigation: completed with trigger-source UNKNOWN
- §1.7 classification: A
- All findings cited: YES
- No hypotheses beyond evidence: YES
- No fixes recommended: YES
- No external sources: YES
- No broad decompilation as authority: YES
- Existing trace reused where possible: YES
- NOT REACHED used within trace duration only: YES
- No source/spec/tool modifications: YES
