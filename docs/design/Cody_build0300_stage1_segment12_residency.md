# Build 0300 Stage-1 Segment 1/2 Residency

## Scope and Baseline

- Agent: Cody
- Task: finish Andy's in-progress Build 0300 implementation without restarting the investigation.
- Baseline ROM: Build 0299.
- Build configuration: `RASTAN_GAMEPLAY_HUD_SPRITES=2 make -C apps/rastan-direct release`.
- Result: Build 0300 extends segment-aware Stage-1 foreground residency coverage to segments 1 and 2.
- This report does **not** claim that the visible cave corruption is fixed. Visual acceptance remains with Tighe.

The current Andy working tree was preserved. The expected diagnostic-only change to
`tools/mame/scripts/genesistrace.lua`, Andy's reports and scripts, and generated build
evidence were not reverted or discarded. No materially unexpected production change was
found during the pre-build audit.

## Architecture Compliance

The retained arcade semantic decision is the Stage-1 segment value at arcade work-RAM
field `a5+0x013E` (Genesis-WRAM `0x00FF013E`). The native selector uses that semantic value
to choose a precomputed Genesis tile residency set before the existing native Plane A
publisher runs. It does not infer the segment from player coordinates.

The selected path remains:

`arcade semantic segment state -> native Genesis residency selection -> native Plane A output`

It does not restore a software PC080SN device, C-window projection, or generic chip-address
translation. Plane B, collision, PC090OJ, palette, sound, and rope behavior were not changed.

## Existing Changes Audited

The unfinished Build 0300 tree contained the expected work in these areas:

- `tools/translation/precompute_pc080sn_tile_lut.py`
  - Adds `SCENE_GAMEPLAY_STAGE1_SEG1 = 7` and `SCENE_GAMEPLAY_STAGE1_SEG2 = 8`.
  - Generates independent segment-1 and segment-2 foreground residency sets.
  - Retains segment-4/5/6 residency generation.
- `apps/rastan-direct/Makefile`
  - Generates and links both new preload manifests.
- `apps/rastan-direct/src/scene_load.s`
  - Exposes and dispatches the new manifests while preserving logical gameplay scene state.
- `apps/rastan-direct/src/tilemap_hooks.s`
  - Reads `0x013E(a5)` and selects residency IDs 7 and 8 for segments 1 and 2.
  - Retains IDs 4, 5, and 6 for segments 4, 5, and 6.
  - Compares the requested ID with `genesistan_current_pc080sn_tileset_id`, avoiding a reload while the segment is unchanged.
- `tools/mame/scripts/genesistrace.lua`
  - Contains Andy's read-only watches for segment and residency state; it is not production ROM code.
- `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py`
  - Their mirrored coverage invariants were updated only after the coverage proof below.

Generated objects, manifests, disassembly, trace logs, and the counter changed as normal
outputs of the authorized release build.

## Coverage Proof

The canonical Build 0299 coverage was `0x188EB8`; the linked Build 0300 coverage is
`0x18AEB8`:

```text
0x18AEB8 - 0x188EB8 = 0x2000
```

The two new generated preload blocks are:

| Block | File size | Residency entries |
| --- | ---: | ---: |
| Stage-1 segment 1 | `0x103A` (4,154 bytes) | 1,038 plus terminator |
| Stage-1 segment 2 | `0x11FA` (4,602 bytes) | 1,150 plus terminator |
| Raw total | `0x2234` (8,756 bytes) | 2,188 entries plus terminators |

The linked symbols place the blocks at:

- Segment 1: `[0x186838, 0x187872)`, size `0x103A`.
- Segment 2: `[0x187872, 0x188A6C)`, size `0x11FA`.

The raw block total exceeds the net ROM growth by `0x0234`. The fixed crash section is
aligned to a `0x1000` boundary: it begins at `0x18A000` in Build 0300 and has size `0x0EB8`.
Build 0299's same-size tail therefore began at the preceding aligned address `0x188000`.
The two blocks consume prior alignment padding before moving that tail by exactly two pages.
Consequently, the intended blocks account for the complete net `0x2000` coverage increase;
there are no unexplained bytes in the delta.

The invariant remains enabled and was updated in both owners:

```text
0x188EB8 -> 0x18AEB8
```

## Static Residency Verification

Generator and linked-output verification produced these budgets:

| Residency scene | Tiles | Budget result |
| --- | ---: | --- |
| Title | 845 | fits |
| General gameplay (combined base residency) | 1,002 | fits |
| End-round | 1,067 | fits |
| Gameplay cave base | 608 | fits |
| Stage-1 segment 4 | 1,123 | fits |
| Stage-1 segment 5 | 1,002 | fits |
| Stage-1 segment 6 | 1,153 | fits |
| Stage-1 segment 1 | 1,038 | fits |
| Stage-1 segment 2 | 1,150 | fits |

Maximum generated residency is `1,153 / 1,164` tiles.

The task's semantic per-segment census lists Stage-1 segment 0 alone as `962 / 1,164`.
The generated 1,002-tile general gameplay scene is a combined base residency (the source
comments identify base segment 0 plus the retained descent segment-5 acceptance tiles), so
it must not be mislabeled as the standalone segment-0 census value.

The new foreground source checks found:

- Segment 1: 124 unique nonblank foreground source tiles, 0 dark mappings, 0 wrong-pattern mappings.
- Segment 2: 236 unique nonblank foreground source tiles, 0 dark mappings, 0 wrong-pattern mappings.

Final linked-code inspection confirms that the selector reads `0x013E(a5)`, requests ID 7
for segment 1 and ID 8 for segment 2, retains the segment-4/5/6 cases, and calls
`load_scene_tiles` only when the requested residency ID differs from the cached ID.

Segment 3 is intentionally deferred: its naive working set is `1,246 / 1,164` and does not
fit. No attempt was made to solve it in Build 0300.

## Build and Gate Result

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0300.bin`
- SHA-256: `6954ef6eee2b73716ead4960a67b4b3b9d4ac1a1effe478ec832f473f8c087b6`
- Size: 1,617,592 bytes.
- Counter: 299 -> 300.
- Rolling artifact matches the numbered artifact: yes.
- Canonical gate: `GATE_PASS`.
- `opcode_replace`: 227.
- Genesis-only to maincpu continuation references: 7.
- `total_genesis_bytes_covered`: `0x18AEB8`.

## Genesis NTSC Smoke Test

The Makefile's mandatory smoke trace ran against MAME machine `genesis`, not `megadriv`:

- Trace: `states/traces/rastan_direct_video_test_build_0300_mame_30s_20260820_122706/`
- External frames: 1,798.
- VDP live writes: 47,350.
- Unique unmapped memory addresses: none.
- Final PC: `runtime_genesis_pc 0x00073038`.
- Final stack pointer: `0x00FEFF6E`.

The smoke confirms boot/frontend execution, active VDP traffic, and no new exception or
unmapped-memory failure in the sampled interval. It did not reach gameplay, so it cannot
provide runtime observations for segments 1/2 or visual proof for outdoor/cave presentation.
Those dispatches and the unchanged-ID reload guard are established here by final linked-code
inspection. Tighe must perform the visual gameplay acceptance test.

## Deferred and Unchanged Work

- Segment 3: deferred; `1,246 / 1,164`, does not fit.
- Rope: not fixed; deferred.
- Missing destructible cave-entrance block: not fixed; deferred.
- Plane B: unchanged.
- Collision: unchanged.
- Visible cave correctness: not claimed.

## Tool Reuse

- Existing tools reused: the PC080SN preload generator, project Makefile, canonical patch/gate verifiers, address map, linker symbols, and mandatory Genesis MAME trace.
- New durable tooling created: none.
- Reason new tooling was necessary: not applicable.

## User Verification Required

Tighe must inspect Build 0300 in BlastEm/Exodus at:

- beginning of descent;
- repeated purple/green regions;
- dark/block regions;
- cave interior;
- cave exit;
- rope visibility.

## Stop Status

No STOP condition was triggered. Build 0300 was produced exactly once, Build 0299 was
preserved, and the counter is 300.
