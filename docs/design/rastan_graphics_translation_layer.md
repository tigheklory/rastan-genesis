# Rastan Graphics Translation Layer

## Scope
Design-only architecture for translating Rastan arcade graphics intent into Genesis VDP-visible output using relocation-safe opcode-replacement workflows.

This document is intentionally limited to graphics translation design contracts and validation criteria.

## Section 1 - Full Graphics Pipeline Model
### Arcade Model (producer-side intent)
Arcade graphics behavior is intent-driven by 68000 writes into chip-owned windows.

- Tile/tilemap intent:
  - CPU writes PC080SN tile RAM windows (`0xC00000-0xC0FFFF`) as tile+attribute cell updates.
  - CPU writes PC080SN control/scroll words (`0xC20000`, `0xC40000`, `0xC50000`).
- Sprite intent:
  - CPU writes PC090OJ object RAM (`0xD00000-0xD03FFF`) as descriptor/object-list content.
- Palette intent:
  - CPU writes palette RAM window (`0x200000-0x200FFF`).
- Clear/fill intent:
  - CPU bulk-clears chip-owned graphics windows before compose/update phases.
- Ownership rule:
  - CPU produces graphics intent data; hardware chips own final composition.

### Genesis Model (consumer-side execution)
Genesis output is unified through VDP ownership.

- VRAM:
  - pattern/tile data store and plane nametable storage.
- SAT (sprite attribute table):
  - sprite descriptor table consumed by VDP sprite engine.
- Plane A / Plane B:
  - nametable cell outputs (tile index + attrs).
- CRAM:
  - palette color output data.
- VDP registers/control:
  - scroll modes, table bases, DMA setup, plane/sprite control.
- DMA:
  - bulk transfer path for VRAM/CRAM/VSRAM/SAT populations.

### End-to-end ownership contract
Arcade producer classes must terminate in Genesis VDP-owned resources:

- tile intent -> plane nametable + referenced tile patterns in VRAM
- sprite intent -> SAT entries + referenced tile patterns in VRAM
- palette intent -> CRAM entries
- scroll/control intent -> VDP register state
- clear/fill intent -> active VDP-visible owners only

## Section 2 - Translation Layers
### TILE layer
- Input (arcade): PC080SN cell updates and tile attribute words.
- Output (Genesis): Plane A/B nametable writes + ensured tile pattern residency in VRAM.
- Required transformation:
  - decode arcade cell format into Genesis cell format (tile index, palette line, priority, flip bits)
  - resolve arcade tile index to VRAM slot (cache/allocator contract)
  - guarantee tile pattern upload before cell references become visible

### SPRITE layer
- Input (arcade): PC090OJ-style sprite/object descriptor updates.
- Output (Genesis): SAT entries + referenced sprite pattern data in VRAM.
- Required transformation:
  - decode source object fields into Genesis SAT-compatible tuples
  - maintain ordering/priority semantics
  - enforce descriptor validity (non-empty tile id, valid X/Y, valid link flow)
  - guarantee sprite pattern residency before SAT publication

### PALETTE layer
- Input (arcade): palette RAM writes and palette update bursts.
- Output (Genesis): CRAM line/entry updates.
- Required transformation:
  - convert source color encoding to Genesis CRAM format
  - preserve line/index ownership
  - coalesce and publish deterministic non-stale palette state

### SCROLL layer
- Input (arcade): scroll/control register writes.
- Output (Genesis): VDP register/scroll state (H/V scroll modes and values).
- Required transformation:
  - map per-layer scroll semantics into Genesis register model
  - preserve write ordering relative to tile/plane publication

### CLEAR layer
- Input (arcade): chip-RAM clears/fills used for prep/reset.
- Output (Genesis): active-owner clears (VRAM plane regions, SAT region, staging blocks, CRAM where applicable).
- Required transformation:
  - map source clear scope to equivalent Genesis-visible ownership scope
  - avoid clearing legacy/non-consumer buffers
  - preserve temporal order (clear before produce; never clear after publish in same phase)

## Section 3 - Opcode Patch Architecture
No patch proposal is made here; only transformation architecture requirements.

### Instruction classes requiring transformation support
- Absolute-address write instructions targeting arcade graphics windows:
  - `MOVE.[B/W/L]` forms writing to `0xC00000/0xC20000/0xC40000/0xC50000/0xD00000/0x200000` families
- Address-setup instructions feeding graphics writes:
  - `LEA`, `MOVEA`, `PEA` forms that seed pointers into graphics windows
- Control-flow instructions that dispatch graphics producers:
  - `JSR/JMP` absolute targets
  - relative branches (`BSR/BRA/Bcc`) into transformed producer paths
- Data-driven jump-table references used by graphics dispatch

### Memory-write category model
- Category A: direct register/control writes (scroll/control)
- Category B: descriptor/object writes (sprite producers)
- Category C: cell/tilemap writes (text/tile layers)
- Category D: palette writes
- Category E: bulk clear/fill loops

### Transformation rules
- Semantic preservation:
  - transformed sequence must preserve producer intent, ordering, and state-causality.
- Ownership preservation:
  - transformed writes must terminate only in active Genesis consumers.
- Visibility preservation:
  - any published cell/SAT reference must have corresponding non-empty tile/palette backing.
- Relocation safety:
  - transformed blocks may grow/shrink while preserving full control-flow correctness.

### Shift-table patcher requirements
- Must relocate all affected reference classes after insertions:
  - absolute targets, relative displacements, jump-table offsets, pointer literals.
- Must validate preimage bytes (`original_bytes`) before rewrite.
- Must emit a post-transform manifest of:
  - source producer identity
  - transformed consumer targets
  - relocation adjustments applied
- Must support semantic-entry anchoring:
  - transformed targets map to function entry semantics, not accidental mid-body offsets.

## Section 4 - DMA Strategy
### DMA role
DMA is the bulk publication mechanism for graphics payloads once translated producers have generated valid data.

### DMA usage model
- Tile/pattern publication:
  - transfer non-zero tile pattern data into VRAM pattern regions before plane/SAT reference.
- Plane publication:
  - transfer/stream nametable updates to Plane A/B regions.
- SAT publication:
  - upload validated sprite descriptor blocks to SAT region.
- Palette publication:
  - transfer converted palette blocks to CRAM.

### Required DMA data guarantees
- Non-zero payload guarantee for drawable assets:
  - pattern uploads and SAT payloads must not be clear-only traffic.
- Layout guarantee:
  - VRAM destinations match configured plane/SAT/pattern bases.
- Temporal guarantee:
  - data upload precedes visibility-enabling references.

### Why current DMA activity is insufficient
Observed DMA/register activity alone does not produce visuals when producers emit zero or stale payload; design requires producer-valid data contracts before DMA publication.

## Section 5 - First Minimal Working Path
Smallest valid visible path: one title text string.

- Source:
  - title text dispatch intent (`D0` text-id class from title init producer path).
- Transformation:
  - text-id -> descriptor decode -> glyph/tile index resolution
  - ensure referenced glyph tile patterns exist in VRAM
  - write non-space cells to active plane nametable with valid attrs/palette
- Expected VDP result:
  - at least one visible non-space string on active title plane with matching palette.

(Alternative valid minimal path is one sprite with a valid SAT entry + valid pattern tile in VRAM.)

## Section 6 - Validation Rules
All conditions are required concurrently.

- VRAM content validity:
  - referenced tile indices resolve to non-zero pattern data in VRAM.
- SAT validity:
  - SAT contains drawable entries (valid tile id + valid coordinates + valid attrs).
- Plane-write validity:
  - active plane nametables receive non-space/non-clear cell writes for intended content.
- DMA payload validity:
  - DMA transfers for pattern/SAT/plane carry non-zero drawable payload where expected.
- Producer-to-consumer continuity:
  - each producer class has proven downstream consumer writes in the same frame phase.
- Visual confirmation:
  - pixels appear for the targeted minimal working element.

Any missing condition is a translation failure, even if VDP registers/DMA are active.

## Section 7 - Current Failure Analysis
Current no-visibility condition is explained by a broken producer chain plus empty payload publication.

- Wrong dispatch at first text producer handoff:
  - `0x03BD5E` routes to `0x2027C0` instead of semantic text producer path `0x202A4C -> 0x20034C`.
  - consequence: text producer does not execute.
- Missing producers:
  - plane writer paths are not executing in observed title runs.
- Zero data flow despite active VDP:
  - VDP + DMA are active, but uploads are dominated by clear/zero payload traffic for geometry paths.
- Broken descriptor content:
  - sprite descriptor buffers are empty/invalid (no stable drawable tuples).

Net result:
- graphics intent is not translated into VDP-visible content ownership; activity exists at control/pipeline level, but drawable payload continuity is broken.

## Section 8 - What Must Not Be Done
- no shims
- no trampolines
- no wrappers as bypass architecture
- no fake/injected graphics data
- no per-screen hacks
- no partial “VDP active therefore good” conclusions
- no equal-length workaround logic that bypasses proper translation contracts

Design success criterion:
- deterministic arcade-intent -> Genesis-consumer translation with relocation-safe opcode replacement and validated visible payload continuity.
