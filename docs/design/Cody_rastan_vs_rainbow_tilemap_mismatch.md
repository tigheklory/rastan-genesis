# Cody Rastan vs Rainbow Tilemap Mismatch

## 1. Executive Summary
This audit compares the tilemap write pipeline step-by-step between Rainbow Islands Genesis and current Rastan implementation. The first structural divergence is destination-pointer setup. Rainbow initializes destination commit state before VBlank consumption; Rastan does not initialize PC080SN destination pointers at work RAM offsets `0x10A0` and `0x10A4`. The hook path executes, but tilemap writer calls are skipped by invalid-destination gating, leaving tilemap staging buffers effectively unpopulated for normal runtime.

## 2. Rainbow Islands Tilemap Pipeline
Rainbow Islands uses WRAM-staged tilemap commit state and a VBlank consumer.
- Staging memory contract:
  - request/commit mode flag: `0xFFFFF63C`
  - source pointer: `0xFFFFF644`
  - destination command/base: `0xFFFFF648`
- Initialization and progression:
  - producer-side code sets request mode and destination/source fields before VBlank consumption.
  - VBlank routine at `0x000380` calls tilemap dispatcher at `0x00073C`, which calls writer `0x001A70`.
  - writer advances destination and source state as strips are emitted.
- Consumption:
  - VBlank tilemap writer emits tilemap data to VDP control/data ports using staged fields.

Rainbow tilemap pipeline fully defined: YES.

## 3. Rastan Tilemap Pipeline
Current Rastan pipeline uses hook-based commit entrypoints and WRAM buffers.
- PC080SN tilemap hooks:
  - `genesistan_hook_tilemap_plane_a` (`apps/rastan/src/main.c`)
  - `genesistan_hook_tilemap_plane_b` (`apps/rastan/src/main.c`)
- Fields and sources:
  - descriptor list base: `0x1000`
  - BG dest_ptr offset: `0x10A0`
  - FG dest_ptr offset: `0x10A4`
  - strip index offset: `0x10CA`
- Dest pointer contract:
  - hooks read dest_ptr, validate address range against C-window region, and only call assembly writer when valid.
  - invalid dest_ptr path advances dest numerically and skips assembly tilemap commit.
- Commit dependency:
  - `genesistan_asm_tilemap_commit_bg/fg` in `apps/rastan/src/startup_trampoline.s` perform actual buffer population and require valid decoded row/col from dest_ptr.

Rastan tilemap pipeline fully defined: YES.

## 4. Side-by-Side Comparison Table

| Stage | Rainbow Islands | Rastan | Match |
| --- | --- | --- | --- |
| Staging memory | WRAM request/source/dest contract (`F63C/F644/F648`) | WRAM descriptor/dest contract (`0x1000/0x10A0/0x10A4`) + BG/FG staging buffers | YES |
| Source pointer setup | Producer sets source pointer before VBlank tilemap consume | Descriptor list and strip index are read by hook/writer path | YES |
| Destination pointer setup | Producer initializes destination command/base before consume | Dest pointers at `0x10A0/0x10A4` are not initialized by active setup path | NO |
| Per-frame update progression | Destination/source progression occurs from valid staged start | Progression starts from invalid zero state; invalid branch skips writer | NO |
| Commit trigger mechanism | VBlank tilemap dispatcher gated by request flag | Hook entrypoints are invoked by patched tilemap callsites | YES |
| VBlank consumption | VBlank consumes staged tilemap state and emits writes | VBlank commit path consumes BG/FG buffers; hook-side buffer population depends on valid dest_ptr | YES |

## 5. Destination Pointer Analysis
Rainbow destination model:
- Destination state is explicitly staged before VBlank tilemap consume.
- Tilemap writer uses valid destination state and advances it during commit.
- Commit behavior depends on valid destination state.

Rastan destination model:
- BG/FG hooks read destination from work RAM `0x10A0/0x10A4`.
- Validation rejects values outside BG `0xC00000-0xC03FFF` and FG `0xC08000-0xC0BFFF` windows.
- Current startup and active producer path do not initialize these fields; initial value remains zero.
- Invalid branch path skips assembly tilemap writers that fill staging buffers.

Destination pointer model matches: NO.

## 6. First Divergence Point
The first divergence is destination-pointer setup: Rainbow sets a valid destination staging field before commit consumption, while Rastan enters hook processing with uninitialized destination pointers (`0x10A0/0x10A4`), causing immediate invalid-destination branching.

## 7. Validation of Andy Root Cause
Andy root cause `DEST_PTR_NEVER_INITIALIZED` is correct.
- Blank/invalid planes: explained by repeated invalid-destination branch skipping assembly tilemap writers.
- No WRAM buffer writes in normal path: explained because buffer writes occur in `genesistan_asm_tilemap_commit_bg/fg`, which are bypassed on invalid destination.
- Commit writer path not executing: hook functions execute, but assembly tilemap commit branch does not execute while destination remains invalid.

Andy root cause correct: YES.

## 8. Single Root Cause
Rastan does not initialize tilemap destination pointers at work RAM `0x10A0`/`0x10A4`, so the hook pipeline continuously takes the invalid-destination branch and does not execute the assembly tilemap writers that populate BG/FG staging buffers.

## 9. Final Verdict
Pipeline comparison is complete. The structural mismatch is destination-pointer initialization, and Andy’s `DEST_PTR_NEVER_INITIALIZED` root cause is validated as the single correct explanation.
