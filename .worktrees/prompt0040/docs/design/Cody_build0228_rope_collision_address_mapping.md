# Cody - Build 0228 Rope Collision Address Mapping

**Date:** 2026-07-21
**Type:** Hybrid verification/implementation gate, STOP before build
**Accepted baseline:** Build 0227
**Accepted ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0227.bin`
**Accepted SHA256:** `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`
**Counter before task:** `227`
**Build 0228:** not produced

## Phase 0

Classification: **EXTENDING**. This extends OPEN-017 / Stage-1 collision and cave/rope work.

Relevant priors loaded: KF-067 (collision row / ground-Y producer boundary), KF-072 (Build 0227 returned to the non-ring plane pipeline while preserving display-on behavior), KF-073 (Stage-1 cave/rope is downstream-blocked and collision authority is unresolved), plus address-discipline priors around JSON-derived mapping and the separation of code-PC mapping from data-pointer conversion.

Rediscovery hazard touched: HIGH for KF-067/KF-073. No contradiction of CONFIRMED or STRONG findings was found.

Open/closed issues touched: OPEN-017 and OPEN-001 context. OPEN-015 was not touched. No closed issue was reopened.

Architecture compliance: CONFIRMED. This task treats arcade data and arcade code as authoritative; Genesis-side logic is only a hardware/data translation boundary. No source/spec/tool/ROM changes were made.

## Baseline Verification

Verified before any edit:

- Build 0227 numbered ROM SHA256: `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`
- Rolling ROM SHA256: `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`
- Build counter: `227`
- `dist/rastan-direct/rastan_direct_video_test_build_0228.bin`: absent

## Authoritative Evidence Used

Existing proven native chain, not reinvestigated:

- Lethal collision cell: `Genesis-WRAM 0x00FF30DA = 0x0107`
- Native read: `runtime_genesis_pc 0x053D70/0x053DD0`, masked to code `0x07`
- Hazard flag path: `Genesis-WRAM 0x00FF10CE` bit set, followed by delayed native mode-8 write
- Mode write: `runtime_genesis_pc 0x0550BE`, writing mode 8 to `Genesis-WRAM 0x00FF10E8`
- Last writer of `0x00FF30DA`: Genesis-only `genesistan_stage_bg_collision_column`, reported as post-write `runtime_genesis_pc 0x07079C`, with source `runtime_data A2=0x00003A88`

Original arcade rope producer evidence:

- Arcade producer: `arcade_pc 0x0559EC`, BG/pass-0 path, `sel10A8=0`
- Documented rope-band samples in the preserved authority doc:
  - rows 37-39: `arcade_rom/data 0x00002648`, collision code `0x0008`
  - row 40: `arcade_rom/data 0x00001C14`, collision code `0x0006`

Source files inspected:

- `build/rastan-direct/address_map.json`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `specs/rastan_direct_remap.json`
- `build/genesis_postpatch.disasm.txt`
- `apps/rastan-direct/out/symbol.txt`
- `docs/design/Andy_fable_build0228_stage1_cave_map_collision_authority.md`
- `states/traces/build0228_rope_death_cody_proof_20260721_135322/cody_rope_death_proof_summary.md`
- `states/traces/build0228_rope_death_cody_proof_20260721_135322/arcade_rope_producer_events.log`
- `states/traces/build0228_stage1_cave_map_collision_authority_20260720_221041/rope_causality_run.txt`

## Address Spaces

Address labels used here:

- `arcade_pc`: original arcade code address.
- `runtime_genesis_pc`: translated Genesis code execution address.
- `arcade_rom/data`: original maincpu ROM data address used as a producer source pointer, not a PC.
- `genesis_rom_offset/runtime_data`: corresponding address inside the copied/relocated ROM image when the address is used as runtime read-only data.
- `Genesis-WRAM`: Genesis work RAM address.

This task keeps code-PC mapping separate from data-pointer mapping.

## JSON Mapping Segment

The authoritative `address_map.json` segment for the source-data addresses is:

```json
{
  "genesis_start": "0x0011B0",
  "genesis_end_exclusive": "0x03A20C",
  "kind": "arcade_copy",
  "arcade_start": "0x000FB0",
  "arcade_end_exclusive": "0x03A00C",
  "source": "whole_maincpu_copy",
  "identity_offset": 512
}
```

The mapping below is derived from this JSON segment, not from an assumed global offset.

## Correct Mapping Calculations

| Authoritative source | Address space | JSON range match | Correct Genesis address | Byte/data identity |
|---|---|---|---|---|
| `0x00002648` | `arcade_rom/data` | `0x000FB0..0x03A00C` | `genesis_rom_offset/runtime_data 0x00002848` | PASS |
| `0x00001C14` | `arcade_rom/data` | `0x000FB0..0x03A00C` | `genesis_rom_offset/runtime_data 0x00001E14` | PASS |
| `0x0000237C` | `arcade_rom/data` | `0x000FB0..0x03A00C` | `genesis_rom_offset/runtime_data 0x0000257C` | PASS |
| `0x00001970` | `arcade_rom/data` | `0x000FB0..0x03A00C` | `genesis_rom_offset/runtime_data 0x00001B70` | PASS |

The observed Genesis helper source pointer is:

| Observed pointer | Address space | JSON inverse mapping |
|---|---|---|
| `0x00003A88` | `genesis_rom_offset/runtime_data` | `arcade_rom/data 0x00003888` |

Therefore `0x00003A88` is **not** the correct mapped Genesis address for `arcade_rom/data 0x00002648` or `0x00001C14`. It is the correct JSON mapping of a different arcade source address, `arcade_rom/data 0x00003888`.

## Byte Identity Verification

Byte comparisons were performed between `build/regions/maincpu.bin` and Build 0227 ROM bytes at the JSON-derived Genesis addresses. All checked mappings were byte-identical.

Important checked examples:

- `arcade_rom/data 0x00002648 -> genesis_rom_offset/runtime_data 0x00002848`: PASS
- `arcade_rom/data 0x00001C14 -> genesis_rom_offset/runtime_data 0x00001E14`: PASS
- `arcade_rom/data 0x00003888 -> genesis_rom_offset/runtime_data 0x00003A88`: PASS

Observation: the observed `0x00003A88` pointer is a valid relocated copy address for `arcade_rom/data 0x00003888`. The current evidence therefore does not prove a simple arithmetic relocation error of `0x2648` or `0x1C14`; it proves that the Genesis path selected a different source block.

## Current Genesis Source Path

`genesistan_stage_bg_collision_column` in `apps/rastan-direct/src/tilemap_hooks.s` performs the current collision side-channel staging:

- It reads descriptor source entries from `Genesis-WRAM 0x00FF1000` via `ARCADE_PC080SN_DESC_BG_LIST_OFFSET`.
- It uses `ARCADE_MAINCPU_ROM_BASE = 0x00000200` when dereferencing the descriptor source entry and the descriptor second word.
- It reads `word 2(descriptor)` as the block pointer and then reads collision values from that block.
- It writes the final collision value to `Genesis-WRAM 0x00FF1E00..0x00FF3E00`.

The lethal trace reports the helper used `a2=0x00003A88`, and the preserved causality log reports `a0=0x00FF1028` after the source-table read for this descriptor-loop position. Because the helper post-increments `a0`, this points to the selected source-table vicinity around `Genesis-WRAM 0x00FF1024`, but the preserved trace does not prove the exact prior writer/control path that populated that source entry.

The descriptor-rebuild hook at `genesistan_hook_pc080sn_descriptor_rebuild` maps source pointers in `Genesis-WRAM 0x00FF1000` through the JSON-proven arcade-copy segment before reading descriptor words. Static inspection shows it can transform a selected source descriptor into the rebuilt pointer table, but the evidence does not prove that this hook is the first faulty source of `0x00003A88`; the unproven piece is which descriptor/source entry should have been selected for the rope-band column and why the current entry selects `arcade_rom/data 0x00003888` instead of the documented arcade sources.

## Expected Versus Observed

Expected from authoritative original arcade rope-band evidence:

- `arcade_rom/data 0x00002648` should map to `genesis_rom_offset/runtime_data 0x00002848`.
- `arcade_rom/data 0x00001C14` should map to `genesis_rom_offset/runtime_data 0x00001E14`.

Observed in Build 0227 Genesis helper:

- `runtime_data A2=0x00003A88`, which maps back to `arcade_rom/data 0x00003888`.

First proven divergence:

- The Genesis collision helper is reading from the source-block path for `arcade_rom/data 0x00003888`, not from the documented original-arcade rope-band source blocks `0x00002648` / `0x00001C14`.

What is **not** proven:

- The exact instruction, source-table writer, descriptor-table entry, or generated data entry that should change.
- Whether the wrong source is caused by a descriptor-source selection error, descriptor rebuild input error, row/column/progression mismatch, or another upstream table-control path.

## Correction Boundary

No patch-safe correction boundary was established.

A safe correction would need to prove, with write/read provenance, the exact source-table or descriptor-control path that causes the rope-band column to select `arcade_rom/data 0x00003888` in Genesis when the original arcade run selects `0x00002648` / `0x00001C14` for the corresponding rope-band samples.

Minimum missing evidence for a later task:

- Watch/log writes to `Genesis-WRAM 0x00FF1000..0x00FF1040` and `0x00FF1040..0x00FF1080` around the rope-band producer window.
- Log the selected descriptor slot, descriptor pointer, second-word block pointer, selector `Genesis-WRAM 0x00FF10A8`, strip index `Genesis-WRAM 0x00FF10CA`, and destination cursor.
- Compare that with original arcade descriptor/source-table provenance for the same rope-band column/row samples.

## Implementation Result

No implementation was performed.

Reasons:

- The documented arcade source addresses map cleanly and byte-identically through `address_map.json`.
- The observed `0x00003A88` pointer is a valid JSON mapping of a different original arcade data address, `0x00003888`.
- The exact source of the incorrect source-block selection was not identified.
- Any attempted fix would risk hardcoding a source block, synthesizing collision behavior, or changing unrelated descriptor/tilemap behavior without satisfying the state-causality rule.

## Build / Counter Outcome

- Build produced: **NO**
- Build 0228 consumed: **NO**
- Counter after task: `227`
- ROM path: N/A
- SHA256: N/A

## Open / Closed Issues Impact

- Open issues touched: OPEN-017; OPEN-001 context.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: final rope fix, cave/rope gameplay acceptance, unrelated enemy damage, sprites, palettes, DISPLAY_OFF, PC090OJ, cave art, and downstream collision/value semantics.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This pass establishes a STOP-level mapping contradiction and narrows the missing proof to source-block selection provenance. It does not yet prove a durable new mechanism or safe correction boundary beyond KF-073/KF-067 context.

## STOP

STOP triggered: **YES**.

Exact unresolved contradiction: the authoritative arcade rope sources map to `genesis_rom_offset/runtime_data 0x00002848` and `0x00001E14`, but Build 0227's helper used `runtime_data 0x00003A88`. `0x00003A88` is itself a correct JSON relocation of `arcade_rom/data 0x00003888`, so the evidence proves source-block selection divergence, not a patch-safe address-calculation fix. The exact source-table/descriptor writer that selects `0x00003888` has not been proven.

## Slot-Writer Provenance Continuation - 2026-07-21

### Scope

This continuation attempted the focused slot-writer provenance capture requested for the Build 0228 rope-collision gate. It remained diagnostic/evidence-only: no production source, spec, Makefile, ROM, invariant, or build artifact was changed. Build 0228 was not produced or consumed.

### Corrected Logger Artifacts

Two diagnostic trace directories now exist:

- `states/traces/build0228_rope_collision_slot_writer_provenance_20260721_172930/`
- `states/traces/build0228_rope_collision_slot_writer_provenance_20260721_173509/`

The first run (`20260721_172930`) is retained but not used as writer-proof evidence because its write-tap address formatting treated MAME's callback address as range-relative. This made write addresses/slot numbers invalid in the log. It is still preserved for historical context and its periodic table snapshots.

The second run (`20260721_173509`) used a corrected read-only MAME Lua logger:

- `genesis_slot_writer_logger.lua`
- `genesis_slot_writer_events.log`
- `README.md`

Corrections in the second logger:

- MAME write-tap callback addresses are logged directly as absolute `Genesis-WRAM` addresses.
- Tap handles are retained so MAME does not garbage-collect the watchpoints.
- The logger watches `Genesis-WRAM 0x00FF1000..0x00FF103F`, `0x00FF1040..0x00FF107F`, `0x00FF1080..0x00FF10A1`, selected PC080SN state fields, the rope-band collision-map write range, and player mode `Genesis-WRAM 0x00FF10E8`.

### Static Table Layout Reconfirmed

Genesis source-list and helper layout:

- Source descriptor list base: `Genesis-WRAM 0x00FF1000`
- Source descriptor list entry size: 4 bytes
- Slot 9 source field: `Genesis-WRAM 0x00FF1024`
- Slot 10 source field: `Genesis-WRAM 0x00FF1028`
- Rebuilt pointer table base: `Genesis-WRAM 0x00FF1040`
- Rebuilt pointer slot 9: `Genesis-WRAM 0x00FF1064`
- Rebuilt pointer slot 10: `Genesis-WRAM 0x00FF1068`
- Rebuilt word table base: `Genesis-WRAM 0x00FF1080`
- Rebuilt word slot 9: `Genesis-WRAM 0x00FF1092`
- Rebuilt word slot 10: `Genesis-WRAM 0x00FF1094`
- Selector/output field: `Genesis-WRAM 0x00FF10A8`

Relevant Genesis code:

- `runtime_genesis_pc 0x00055AC8`: patched `movea.l #0x00FF1000,%a0`
- `runtime_genesis_pc 0x00055ACE`: copied arcade `addq.l #4,(%a0)` source-list advance
- `runtime_genesis_pc 0x00055B04`: patched jump to `genesistan_hook_pc080sn_descriptor_rebuild`
- `runtime_genesis_pc 0x00071CB4`: `genesistan_hook_pc080sn_descriptor_rebuild`
- `runtime_genesis_pc 0x000706EE`: `genesistan_stage_bg_collision_column`
- `runtime_genesis_pc 0x00070798`: collision-map write instruction

Relevant arcade code:

- `arcade_pc 0x000558C8`: original source-list base load `#0x0010D000`
- `arcade_pc 0x000558CE`: original `addq.l #4,(%a0)` source-list advance
- `arcade_pc 0x00055904`: original descriptor rebuild path
- `arcade_pc 0x00055968..0x000559EC`: original producer path using rebuilt pointer/word tables

The static layout therefore remains proven. The writer candidate path is the source-list advance plus descriptor rebuild path, but the live rope-window write/control divergence is not proven by this continuation.

### Corrected Runtime Capture Result

Corrected trace:

`states/traces/build0228_rope_collision_slot_writer_provenance_20260721_173509/genesis_slot_writer_events.log`

Reduced result:

- Lines captured: `1956`
- Corrected absolute write addresses were confirmed for initial source-list and pointer-table clears, including `Genesis-WRAM 0x00FF1024` and `0x00FF1028`.
- The run did **not** capture any `COLL_WRITE_BAND` event.
- The run did **not** capture any `MODE_WRITE` or `DEATH_SEEN` event.
- The emulator was stopped after a long non-rope capture window; because SIGTERM did not close MAME, the exact capture process was force-stopped. The log had already flushed many events, but there is no stop-notifier `STOP` line in this second log.

Important limitation:

This corrected capture did not reproduce the rope-death window. It cannot prove the upstream Genesis writer that makes slot 9 select `runtime_data/genesis_rom_offset 0x00003A88`, nor can it normalize against the original arcade rope-window slot 9/10 construction events.

### Slot-Writer Provenance Status

Proven:

- Static table layout and effective slot addresses are known.
- The corrected logger can log absolute `Genesis-WRAM` table-write addresses correctly.
- Build 0228 remained unproduced and unconsumed.

Not proven:

- The exact Genesis runtime write/control event that populates `Genesis-WRAM 0x00FF1024` or the rebuilt slot state leading to `runtime_data/genesis_rom_offset 0x00003A88` during the rope-death window.
- The corresponding original arcade slot-population event that makes slot 9 select `arcade_rom/data 0x00002648` and slot 10 select `arcade_rom/data 0x00001C14` during the same normalized rope-region producer context.
- The first divergent input, index, descriptor field, table entry, selector, stale-entry condition, or translated instruction.

### Implementation Gate

The implementation gate remains closed.

No correction boundary is patch-safe from this evidence. A production fix now would still require guessing whether the divergence is caused by source-list advancement, descriptor rebuild input, descriptor rebuild output, selector/strip timing, stale table lifecycle, or another upstream control path.

Rejected as unsafe:

- hardcoding `0x2848` / `0x1E14`;
- replacing all `0x3A88` uses;
- clamping or synthesizing collision values `0x0006` / `0x0008`;
- coordinate-specific rope behavior;
- unrelated cave, display, PC090OJ, palette, or gameplay-state changes.

### STOP

STOP triggered: **YES**.

Exact unresolved boundary: the corrected logger did not capture the rope-window source-slot write/control event. The static candidate path is known (`runtime_genesis_pc 0x00055ACE` source-list advance and `0x00071CB4` descriptor rebuild), but the task requires a live normalized Genesis-versus-arcade rope-window writer/input divergence before Build 0228 can be safely implemented.

## Source-Selection Continuation - 2026-07-21

### Scope

This continuation follows the Build 0228 rope collision source-selection task. It is evidence/documentation only: no source, spec, ROM, Makefile, diagnostic-ROM, scaffold, or build-number-consuming change was made. Build 0228 remains unproduced.

### Phase 0 Classification

Classification: **EXTENDING**. This continues OPEN-017 / KF-073 rope and cave collision work using Build 0227 as the accepted baseline. Relevant priors: KF-067 (collision row/ground-band producer hazard), KF-072 (Build 0227 plane pipeline baseline), and KF-073 (Stage 1 cave/rope/collision authority unresolved). OPEN-017 is the primary issue touched; OPEN-001 is context. OPEN-015 was not touched. No contradiction of a CONFIRMED or STRONG finding was detected.

Architecture compliance: **CONFIRMED**. The arcade code/data remains authoritative. Genesis-side code is treated only as helper/opcode-replacement staging and VBlank service. No forced collision value, coordinate-specific workaround, synthetic rope state, or Genesis-owned gameplay control flow was introduced.

### Accepted Baseline

- Accepted ROM: `dist/rastan-direct/rastan_direct_video_test_build_0227.bin`
- SHA256: `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`
- Counter before/after this continuation: `227`
- Build 0228 status: not present / not consumed

### Evidence Inspected

- `docs/design/Andy_fable_build0228_stage1_cave_map_collision_authority.md`
- `docs/design/Cody_build0228_rope_collision_address_mapping.md`
- `states/traces/build0228_stage1_cave_map_collision_authority_20260720_221041/rope_causality_run.txt`
- `states/traces/build0228_rope_death_cody_proof_20260721_135322/native_events.log`
- `states/traces/build0228_rope_death_cody_proof_20260721_135322/arcade_rope_producer_events.log`
- `states/traces/build0228_rope_death_cody_proof_20260721_135322/cody_rope_death_proof_summary.md`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- `build/genesis_postpatch.disasm.txt`

### Genesis Source-Selection Provenance

The current Genesis collision helper is `genesistan_stage_bg_collision_column` at `runtime_genesis_pc 0x000706EE`. The collision write instruction is at `runtime_genesis_pc 0x00070798`; debugger watchpoint reports post-instruction `runtime_genesis_pc 0x0007079C`.

The lethal cell writer recorded in the preserved native trace is:

```text
EVENT COLL_WRITE_HELPER cyc=304251108 pc=07079C addr=00FF30DA size=16 data=00000107 post=0020 sr=2700 sel=0000 a0=00FF1028 a1=00000200 a2=00003A88 a3=0005B840 a4=0005B880 a5=00FF0000 a6=00FF1E00 d0=000012DA d1=00000100 d2=FFFF0107 d3=00023888 d4=00000001 d5=00C0A4B4 d6=00000006 d7=00020001 sp=00FEFF56
```

Interpretation of the directly observed helper state:

- `addr=Genesis-WRAM 0x00FF30DA`, `data=0x0107` is the lethal collision cell later read by native collision code.
- `a2=runtime_data/genesis_rom_offset 0x00003A88` is the source block selected by the Genesis helper for this write.
- `d3=0x00023888` is consistent with the helper having read descriptor second-word data `0x3888` and adding `ARCADE_MAINCPU_ROM_BASE = 0x200` before dereferencing.
- `a0=Genesis-WRAM 0x00FF1028` is post-increment after the helper read a descriptor/source-table slot. Given the helper's `move.l (%a0)+,%d3`, this points to the slot just read at `Genesis-WRAM 0x00FF1024`, i.e. descriptor/source slot 9 in the helper loop.
- `sel=0x0000` preserves the observed selector state for this helper event.
- `d5=HW_ADDRESS-like PC080SN cursor 0x00C0A4B4` and `d7` low word `0x0001` preserve the observed destination/strip context.

Address mapping discipline:

- `runtime_data/genesis_rom_offset 0x00003A88` maps through `address_map.json` back to `arcade_rom/data 0x00003888`.
- `runtime_genesis_pc 0x00070798/0x0007079C` is Genesis helper code and has no arcade-PC mapping.

### Arcade Source-Selection Provenance

The original arcade producer writes for the rope-band comparison were captured at `arcade_pc 0x000559EC` in the original `rastan` runtime. The representative rope-region samples include:

```text
EVENT ARCADE_COLL_WRITE_ROPE_BAND ... pc=0559EC ... row=37 col=44 data=00000008 ... sel10A8=0000 ... a1=0010D092 a2=00002648 a3=0010D064 ...
EVENT ARCADE_COLL_WRITE_ROPE_BAND ... pc=0559EC ... row=38 col=44 data=00000008 ... sel10A8=0000 ... a1=0010D092 a2=00002648 a3=0010D064 ...
EVENT ARCADE_COLL_WRITE_ROPE_BAND ... pc=0559EC ... row=39 col=44 data=00000008 ... sel10A8=0000 ... a1=0010D092 a2=00002648 a3=0010D064 ...
EVENT ARCADE_COLL_WRITE_ROPE_BAND ... pc=0559EC ... row=40 col=44 data=00000006 ... sel10A8=0000 ... a1=0010D094 a2=00001C14 a3=0010D068 ...
```

Interpretation of the original arcade producer state:

- `arcade_pc 0x000559EC` is inside the original BG/pass-0 collision producer path.
- `sel10A8=0x0000`, so this is not an FG-selector-vs-BG-selector mismatch.
- Rows 37-39 use `arcade_rom/data 0x00002648` and write collision code `0x0008`.
- Row 40 uses `arcade_rom/data 0x00001C14` and writes collision code `0x0006`.
- `a3=0x0010D064` corresponds to original arcade pointer-table slot 9 (`0x10D040 + 9*4`) for the rows using `0x2648`.
- `a3=0x0010D068` corresponds to original arcade pointer-table slot 10 for the row using `0x1C14`.
- `a1=0x0010D092` / `0x0010D094` correspond to the parallel original arcade word table slots for slots 9/10.

JSON-derived data mapping confirms:

- `arcade_rom/data 0x00002648 -> genesis_rom_offset/runtime_data 0x00002848`
- `arcade_rom/data 0x00001C14 -> genesis_rom_offset/runtime_data 0x00001E14`
- `arcade_rom/data 0x00003888 -> genesis_rom_offset/runtime_data 0x00003A88`

### First Divergence

The first proven divergence remains **source-block selection at the collision producer/helper surface**:

- Original arcade rope-region producer selects `arcade_rom/data 0x00002648` for rows 37-39 and `arcade_rom/data 0x00001C14` for row 40.
- Genesis Build 0227 helper selects `runtime_data/genesis_rom_offset 0x00003A88`, which maps back to a different valid arcade source block, `arcade_rom/data 0x00003888`.

This is **not** proven to be an address arithmetic error. `0x00003A88` is correctly mapped data for `arcade_rom/data 0x00003888`; the problem is that the Genesis path selected the wrong source block for the rope-region context.

### What Is Not Yet Proven

The preserved evidence does **not** prove the upstream state creator that makes slot 9 select `0x3888` on Genesis during the lethal rope window. Specifically, it does not prove which of these is first wrong:

- descriptor-source list selection into `Genesis-WRAM 0x00FF1000..0x00FF1040`, especially the slot read at `0x00FF1024`;
- descriptor rebuild at `runtime_genesis_pc 0x00071CB4` / patched site `runtime_genesis_pc 0x00055B04` for `arcade_pc 0x00055904`;
- selector or strip-index timing (`Genesis-WRAM 0x00FF10A8`, `0x00FF10CA`);
- progression/camera/destination cursor selecting the wrong descriptor slot at the rope boundary;
- stale table data surviving from an earlier valid `arcade_rom/data 0x00003888` phase;
- another source-list or pointer-table lifecycle divergence.

Because the original arcade trace also observes `a2=0x00003888` in earlier non-rope scroll phases, replacing `0x3888` globally or hardcoding rope blocks would be unsafe and would violate the state-causality rule.

### Correction Boundary

Correction boundary: **not established**.

A patch-safe fix requires proving the first upstream source-selection writer/control path that differs between original arcade and Genesis. The currently proven boundary is too late: by `genesistan_stage_bg_collision_column`, Genesis has already selected `runtime_data 0x00003A88`.

Smallest safe next capture:

- Run one focused rope-region source-selection trace comparing original arcade and Genesis Build 0227.
- Log writes to original arcade descriptor/source tables and Genesis rebuilt equivalents before and during the rope-band producer window.
- Required arcade addresses: `0x0010D040..0x0010D0A0`, `0x0010D080..0x0010D0A0`, and the source/list region feeding those tables, especially slots 9/10 (`0x0010D064`, `0x0010D068`, `0x0010D092`, `0x0010D094`).
- Required Genesis addresses: `Genesis-WRAM 0x00FF1000..0x00FF1080`, especially `0x00FF1024`, `0x00FF1028`, `0x00FF1064`, `0x00FF1068`, `0x00FF1092`, and `0x00FF1094` if mirrored/derived equivalents are active.
- Log breakpoints/events at `arcade_pc 0x00055904`, `0x00055968`, `0x0005597C`, `0x000559EC`, and Genesis `runtime_genesis_pc 0x00055B04`, `0x000706EE`, `0x00070798/0x0007079C`, plus any observed writer PCs for the table slots.
- For each slot 9/10 event, record frame, monotonic event number, selector, strip index, destination cursor, descriptor/list slot value, descriptor pointer, descriptor first word, descriptor second word/block pointer, source block pointer, row/column, and relevant registers.

### Implementation Result

- Root cause confirmed: **NO**
- Fix implemented: **NO**
- Build produced: **NO**
- Build 0228 consumed: **NO**
- Counter state: `227`

Reason: the helper-level source selection divergence is proven, but the first upstream source-selection writer/control path is not. Any fix now would be a source-block hardcode or guessed descriptor/table correction.

### Open / Closed Issues Impact

- Open issues touched: OPEN-017; OPEN-001 context.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: final rope collision fix, cave/rope acceptance, unrelated DISPLAY_OFF/VDP work, PC090OJ, sprites, enemy damage, palettes, audio, and downstream collision semantics.

### KNOWN_FINDINGS Impact

Option A - no new finding to index. This continuation narrows KF-073/KF-067 context but does not yet establish the durable upstream mechanism or a safe correction boundary.

### STOP

STOP triggered: **YES**.

Exact unresolved boundary: the upstream source-selection writer/control path that causes Genesis Build 0227 slot 9 to select `runtime_data/genesis_rom_offset 0x00003A88` (`arcade_rom/data 0x00003888`) during the lethal rope window, while original arcade slot 9/10 rope-region samples select `arcade_rom/data 0x00002648` / `0x00001C14`, has not been captured.

## Native Manual Rope-Death Slot Capture - 2026-07-21

### Trace Artifacts

- Trace directory: `states/traces/build0228_rope_collision_slot_writer_native_manual_20260721_202348/`
- Native debugger command file: `rope_slot_native_debug.cmd`
- Raw trace: `native_debug_trace.log`
- Extracted events: `native_events.log`
- Reduced relevant events: `rope_relevant_events.log`
- Reduced summary: `rope_slot_native_summary.md`

Tighe completed a manual run to the rope and jumped off to death. This reproduction was successful; the prior missed result was a logger/capture-surface problem, not a user-reproduction failure.

### Actual Rope-Window Event Captured

The native debugger trace contains the actual lethal rope-window collision write:

```text
EVENT COLL_WRITE_HELPER cyc=193876696 pc=07079C addr=00FF30DA size=16 data=00000107 post=0020 sr=2700 sel=0000 strip=0001 src9=0002A288 src10=0002C548 ptr9=00003A88 ptr10=0000257C word9=0005 word10=0006 a0=00FF1028 a1=00000200 a2=00003A88 d3=00023888
```

Proven facts:

- `runtime_genesis_pc 0x0007079C` is Genesis-only helper/wrapper code (`genesistan_stage_bg_collision_column` write-site post-PC), not an arcade PC.
- The written collision cell is `Genesis-WRAM 0x00FF30DA`.
- The written value is `0x0107`; later native reads mask this to collision code `0x07`.
- `sel=0`, `strip=1` at the write.
- The value read from `Genesis-WRAM 0x00FF1024` for slot 9 is `0x0002A288`. The logged `a0=0x00FF1028` is post-incremented after the slot-9 source read.
- Slot 9's rebuilt pointer is `Genesis-WRAM 0x00FF1064/0x00FF1066 = 0x00003A88`.
- Slot 9's rebuilt word is `Genesis-WRAM 0x00FF1092 = 0x0005`.

### Correct Descriptor / Pointer Chain

ROM verification for the slot-9 source field:

```text
genesis_rom_offset 0x0002A488: 0005 3888 0003 3408 0003 3008 0003 206C
```

Therefore:

- `Genesis-WRAM 0x00FF1024 = 0x0002A288` is the source-list/descriptor source value.
- The descriptor read at `genesis_rom_offset 0x0002A488` yields word `0x0005` and raw block pointer word `0x3888`.
- The helper state then contains `a1=0x00000200`, `d3=0x00023888`, and `a2=runtime_data/genesis_rom_offset 0x00003A88`.

Correction to earlier wording: do **not** describe this as `0x3888 + 0x200 = 0x23888`. The descriptor raw word, the base/tag value in `d3`, and the normalized runtime data pointer in `a2` are separate state values.

### Last Slot Writers Before The Lethal Write

The final observed slot writers before `cyc=193876696` were:

```text
00FF1024 @ line 45084: runtime_genesis_pc 0x055AD2, data=00000002, post=2A288 -> src9=0002A288
00FF1026 @ line 45083: runtime_genesis_pc 0x055AD2, data=0000A288 -> low half of src9
00FF1092 @ line 45085: runtime_genesis_pc 0x071CEA, data=00000005 -> word9=0005
00FF1064 @ line 45086: runtime_genesis_pc 0x071CFC, data=00000000
00FF1066 @ line 45087: runtime_genesis_pc 0x071CFC, data=00003A88 -> ptr9=00003A88
00FF1094 @ line 45088: runtime_genesis_pc 0x071CEA, data=00000006 -> word10=0006
00FF1068 @ line 45089: runtime_genesis_pc 0x071CFC, data=00000000
00FF106A @ line 45090: runtime_genesis_pc 0x071CFC, data=0000257C -> ptr10=0000257C
```

JSON-derived PC mapping:

- `runtime_genesis_pc 0x00055AD2 -> arcade_pc 0x000558D2` (`arcade_copy`).
- `runtime_genesis_pc 0x00071CEA`, `0x00071CFC`, and `0x0007079C` are Genesis-only wrapper/helper addresses.

Important label correction: the trace label `PRODUCER_559EC` came from a runtime breakpoint name. The logged `runtime_genesis_pc 0x000559EE` maps through `address_map.json` to `arcade_pc 0x000557EE`; it is not the same as the earlier original-arcade evidence point labelled `arcade_pc 0x000559EC`.

### Downstream Read-To-Mode Chain Reconfirmed

The same run contains later native reads of `0x00FF30DA = 0x0107` and mode-8 writes:

```text
EVENT COLL_READ_ROPE ... pc=053D70 addr=00FF30DA mem=0107 masked=07 mode=0002
EVENT COLL_READ_ROPE ... pc=053DD0 addr=00FF30DA mem=0107 masked=07 mode=0002
EVENT MODE_WRITE cyc=228425322 pc=0550C4 addr=00FF10E8 data=00000008 post=0002
EVENT MODE_WRITE cyc=228601100 pc=0550C4 addr=00FF10E8 data=00000008 post=0008
```

JSON-derived PC mapping:

- `runtime_genesis_pc 0x00053D70 -> arcade_pc 0x00053B70`.
- `runtime_genesis_pc 0x00053DD0 -> arcade_pc 0x00053BD0`.
- `runtime_genesis_pc 0x000550C4 -> arcade_pc 0x00054EC4`.

### First Divergence

The first proven divergence is now narrower and earlier than the helper write:

- Genesis Build 0227 source path: `Genesis-WRAM 0x00FF1024 = 0x0002A288 -> descriptor at genesis_rom_offset 0x0002A488 -> word 0x0005 / raw block pointer word 0x3888 -> rebuilt pointer 0x00003A88 -> collision value 0x0107`.
- Existing original arcade rope evidence: rope-region slot 9/10 samples select `arcade_rom/data 0x00002648` and `0x00001C14`, yielding collision values `0x0008` and `0x0006`.

This proves a source-list / descriptor-selection divergence upstream of `genesistan_stage_bg_collision_column`. It does not prove an arithmetic defect inside the helper.

### Implementation Gate

Patch-safe correction boundary: **not established**.

The remaining exact boundary is why `runtime_genesis_pc 0x00055AD2` / the surrounding source-list advance path leaves slot 9 as `0x0002A288` for this rope window instead of the original-arcade rope-region slot source(s). The current evidence proves the wrong source-list value and rebuilt pointer, but not the first control/state divergence that created that source-list value.

Build result:

- Fix implemented: **NO**
- Build produced: **NO**
- Build 0228 consumed: **NO**
- Counter remains: `227`

Reason: a fix now would still be a guessed source-list/table override or rope-specific hardcode, which violates the state-causality rule.

### Open / Closed Issues Impact

- Open issues touched: OPEN-017; OPEN-001 context.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: final rope collision fix, unrelated VDP/DISPLAY_OFF work, PC090OJ, sprites, palettes, audio, and enemy behavior.

### KNOWN_FINDINGS Impact

Option A - no new finding indexed. This is stronger evidence for the active rope-collision thread, but the durable upstream mechanism and safe correction boundary remain unproven.

### STOP

STOP triggered: **YES**.

Exact unresolved boundary: the source-list writer/control path around `runtime_genesis_pc 0x00055AD2` that causes `Genesis-WRAM 0x00FF1024` to contain `0x0002A288` during the rope death window instead of the original-arcade rope-region source selection.
