# Cody - PC090OJ Gameplay Sprite Tile DMA / VRAM Residency Trace

**Date:** 2026-07-13  
**Type:** Runtime evidence / analysis only  
**Build context:** Build 0162, `dist/rastan-direct/rastan_direct_video_test_build_0162.bin`  
**Scope:** Trace one accepted gameplay PC090OJ record from object RAM through Genesis SAT staging and tile-DMA residency. No source/spec/ROM/build changes. No VINT, collision, palette, PC080SN/FG_SRC, player state, camera/scroll, D00298, Exodus/audio, hardcoded sprite, or second-renderer work.

## Phase 0

Classification: **EXTENDING**. This continues the Build 0162 gameplay sprite path after the VINT frequency trace and PC090OJ gameplay representation activation work.

Relevant priors loaded:

- `docs/design/Cody_pc090oj_gameplay_representation_activation.md`
- `docs/design/Cody_build0162_vint_timing_trace_classification.md`
- `docs/design/Andy_gameplay_sat_link_management.md`
- `docs/design/Andy_gameplay_sprite_path_ownership.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- latest relevant `AGENTS_LOG.md` entries

Relevant settled facts respected:

- VINT frequency is not the current boundary.
- `vdp_prepare_sprites` runs from VBlank.
- Candidate/representation path accepts gameplay records that current decode can represent.
- Build 0162 stable gameplay frames contain 14 represented/reachable PC090OJ records.
- Record 64 (`code=0x0513`, slot 1, decoded x/y 56/80) and record 65 (`code=0x0512`, slot 2, decoded x/y 40/80) are accepted gameplay records.

Contradiction of CONFIRMED/STRONG prior: **NONE**.

Architecture compliance: **CONFIRMED**. This task observed the existing arcade-code-to-helper path and did not add a renderer, scaffolding, source behavior change, or ROM change.

## Files And Evidence Inspected

Source/static:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/genesis_postpatch.disasm.txt`
- `build/rastan-direct/address_map.json`

Runtime/evidence artifacts produced:

- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/mame_devices.txt`
- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/frame_0637_records_slots.csv`
- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/frame_0891_records_slots.csv`
- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/frame_1498_records_slots.csv`
- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/sprite_dma_command_trace.csv`
- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/sprite_dma_command_summary.txt`
- `states/traces/pc090oj_gameplay_tile_dma_vram_residency_20260713_000000/probe_vdp_vram_space_frame_637.txt`

## Static Contract

`vdp_prepare_sprites` is symbolized at `runtime_genesis_pc 0x0007219C` and is called unconditionally from `_vblank_service` before sprite VRAM/SAT commit.

`vdp_commit_sprites_vram` is symbolized at `runtime_genesis_pc 0x000721E0` and is called from `_vblank_service` after sprite preparation.

Important symbols:

| Symbol | Address |
|---|---:|
| `rastan_pc090oj` | `0x00072F5C` |
| `staged_sprite_sat` | `0x00FF6188` |
| `staged_sprite_active_count` | `0x00FF67CC` |
| `sprite_tile_resident_code` | `0x00FF67CE` |
| `pc090oj_tile_dma_worklist` | `0x00FF686E` |
| `pc090oj_tile_dma_count` | `0x00FF69AE` |
| `pc090oj_object_ram` | `0x00FF69B0` |
| `record_to_slot` | `0x00FF71F0` |
| `represented_records` | `0x00FF72F0` |
| `pc090oj_represented_count` | `0x00FF7390` |
| `pc090oj_sat_dirty` | `0x00FF7392` |
| `worklist_entry_for_slot` | `0x00FF7340` |

`.Lpc090oj_place_record_in_slot` places a represented PC090OJ record into a Genesis SAT slot. For each slot it:

- writes the 4-word Genesis SAT entry in `staged_sprite_sat`;
- writes the SAT tile attribute as `SPRITE_TILE_BASE + slot*4`;
- queues the tile-DMA worklist through `.Lpc090oj_worklist_set` using `code & 0x0FFF`;
- records `record_to_slot`, represented bit, used slot bit, and `pc090oj_sat_dirty=1`.

`.Lpc090oj_worklist_set` queues a slot/code pair only when the slot's resident code differs from the requested code. It reserves or updates `pc090oj_tile_dma_worklist`, increments `pc090oj_tile_dma_count` on first reservation, and leaves no work if the resident code already matches.

`.Lvcs_tile_dma` consumes `pc090oj_tile_dma_count` entries. For each non-cancelled entry it computes:

- source: `rastan_pc090oj + ((code & 0x0FFF) * 128)`;
- DMA length: `128` bytes / `64` words / 4 Genesis tiles;
- destination tile: `SPRITE_TILE_BASE + slot*4`;
- destination VRAM byte address: `(SPRITE_TILE_BASE + slot*4) * 32`;
- resident cache update: `sprite_tile_resident_code[slot] = code`;
- final cleanup: clears `worklist_entry_for_slot` and resets `pc090oj_tile_dma_count`.

`.Lvcs_sat_dma` then DMAs `staged_sprite_sat` to Genesis SAT VRAM base `0xF800`.

## Target Records

The trace focused on the two accepted gameplay records called out by the prior representation activation evidence.

| Record | Code | Slot | Decoded X/Y | Expected tile index | Expected VRAM byte address |
|---:|---:|---:|---:|---:|---:|
| 64 | `0x0513` | `1` | `56/80` | `0x0404` | `0x8080` |
| 65 | `0x0512` | `2` | `40/80` | `0x0408` | `0x8100` |

The source graphics in `build/pc090oj_genesis.bin` are nonblank:

- code `0x0513`: `26` nonzero bytes in its 128-byte source block.
- code `0x0512`: `43` nonzero bytes in its 128-byte source block.

This rules out a blank source asset for these two target records.

## Runtime Evidence

At gameplay frame 637, state was `2/2/6`, and both records were present in `pc090oj_object_ram` and staged into SAT:

| Record | Object fields | Staged SAT slot | Resident code | Worklist slot entry |
|---:|---|---|---:|---:|
| 64 | `w0=0003 y=0050 code=0513 x=0038` | slot 1: `00C8 0502 E404 00B8` | `0513` | `FF` |
| 65 | `w0=0003 y=0050 code=0512 x=0028` | slot 2: `00C8 0503 E408 00A8` | `0512` | `FF` |

The same object/SAT/residency relationship persisted at frames 891 and 1498.

A separate command-level Lua trace captured a mid-commit state at frame 637:

- `pc090oj_tile_dma_count=0004`
- `pc090oj_sat_dirty=0001`
- `resident_slot1=0513`
- `resident_slot2=0512`
- `work_slot1=00`
- `work_slot2=01`
- staged slot 1: `00C8 0502 E404 00B8`
- staged slot 2: `00C8 0503 E408 00A8`

By frame 638 and frame 700:

- `pc090oj_tile_dma_count=0000`
- `pc090oj_sat_dirty=0000`
- `resident_slot1=0513`
- `resident_slot2=0512`
- `work_slot1=FF`
- `work_slot2=FF`
- staged SAT entries still matched the expected record/slot relationship.

Observed interpretation: the worklist for these target slots existed during the sprite commit window, was consumed/cleared afterward, and the residency cache reported the expected codes for slots 1 and 2.

## VDP VRAM / SAT Read Limitation

MAME exposed a `:gen_vdp` device with a `videoram` space, but direct Lua reads from that space were not usable in this environment. Probe reads returned zero for all tested addresses and full scans:

- `0x0000`
- `0x8080`
- `0x8100`
- `0xF800`
- broad `0x0000..0xFFFF` and `0x0000..0x7FFF` scans

Because the same Lua path reported all VDP VRAM as zero, the zero bytes reported for slot VRAM and VDP-visible SAT are treated as **measurement invalid**, not as evidence of missing tile DMA or missing SAT DMA.

Debugger-side breakpoint capture for the DMA command PCs was attempted but did not produce usable breakpoint event output in this run. Therefore this evidence package proves WRAM/SAT staging and residency state, but does **not** independently prove the VDP-visible VRAM bytes after DMA.

## Classification

Primary classification: **H - more analysis needed**.

Rationale:

- **A: tile DMA not queued** is not supported. Static placement calls `.Lpc090oj_worklist_set`, and frame 637 showed reserved worklist entries for slots 1 and 2 with nonzero DMA count.
- **B: queued not consumed** is not supported. By frame 638/700 the worklist was idle, count was zero, and resident codes matched the target records.
- **C: wrong source** is not supported by static evidence. The source expression is `rastan_pc090oj + code*128`, and codes `0x0512/0x0513` have nonblank converted source data.
- **D: wrong destination** is not supported by static evidence. SAT attributes and the DMA destination calculation agree: slot 1 uses tile `0x0404` / VRAM `0x8080`; slot 2 uses tile `0x0408` / VRAM `0x8100`.
- **E: bad residency cache** remains possible but unproven. Resident codes match the expected records, but current evidence cannot prove whether the reported residency matches VDP-visible VRAM contents.
- **F: SAT commit mismatch** is not proven. Staged SAT is correct and `sat_dirty` clears after commit, but direct VDP SAT reads are invalid through the current Lua `videoram` path.
- **G: no bug found** is too strong because the downstream visual failure remains and VDP-visible VRAM/SAT could not be verified.

Therefore the responsible result is H: the WRAM-side path reaches queued/consumed/resident state for the target records, but the VDP-visible tile/SAT boundary still needs a stronger measurement path.

## Smallest Next Diagnostic Recommendation

Do not change code yet. The next narrow diagnostic should prove the VDP-visible boundary, not re-open candidate/representation logic.

Recommended next target:

- Capture debugger-side events at `.Lvcs_tile_dma` around `runtime_genesis_pc 0x72BD6`, `0x72C30`, and `0x72C3C` to log source, destination command words, slot, and code for slots 1 and 2.
- Capture `.Lvcs_sat_dma` around `runtime_genesis_pc 0x72CA4` / `0x72D0A` to prove SAT DMA command and completion.
- If debugger-side command capture remains unavailable, use an emulator/debugger path that can read Genesis VDP VRAM after DMA, specifically VRAM bytes at `0x8080..0x817F` and SAT bytes at `0xF808..0xF817`.

The next fix should only proceed if that measurement proves one of A-F at the VDP command or VRAM boundary.

## Build / Change Status

Build produced: **NO**.  
Build 0163 produced: **NO**.  
Source/spec/tool/ROM changes: **NO**.  
Trace scripts and evidence under `states/traces/` only.  
Documentation only.

## Open / Closed Issues Impact

Open issues touched: OPEN-001, OPEN-017, OPEN-024 contextually through gameplay sprite rendering.  
New issues opened: NONE.  
Issues closed: NONE.  
Issues intentionally deferred: VINT, collision, palette, PC080SN/FG_SRC, player state, camera/scroll, D00298, Exodus/audio, hardcoded sprites, second renderer, offscreen filter.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This is a bounded evidence package that narrows the sprite path to the VDP-visible DMA/SAT boundary, but it does not prove a durable new mechanism yet.

## STOP

STOP triggered: **YES (bounded measurement gap)**. The current MAME Lua path could not provide reliable VDP VRAM/SAT reads, and debugger-side DMA event capture did not emit usable breakpoint logs. No implementation is justified from this evidence alone.
