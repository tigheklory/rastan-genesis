# Rastan 68000 Opcode Patch Templates for Genesis VDP Translation

## Purpose

These are **template-level opcode replacement patterns** for converting arcade Rastan
graphics intent into Genesis-side staging and VBlank publish behavior.

They are **not final addresses for your current ROM build**.
They are meant to define the replacement *shape* Andy or Cody should implement
after validating the exact callsites and relocation context.

---

## 1. Replace direct PC090OJ descriptor writes with SAT staging writes

### Arcade intent
Write sprite/object descriptor data to PC090OJ / D-window.

### Typical arcade patterns
- `33C0 00D0 xxxx`  -> `move.w D0, 0xD0xxxx`
- `23C0 00D0 xxxx`  -> `move.l D0, 0xD0xxxx`
- `41F9 00D0 xxxx`  -> `lea 0xD0xxxx, A0`

### Genesis replacement strategy
Do **not** write to D-window.
Instead, redirect to WRAM SAT staging or sprite-descriptor staging.

### Template replacement shape
- direct absolute D-window write
  - before:
    - `33C0 00D0 0000`
  - after:
    - `4EB9 aa aa aa aa`
    - `4E71`
- meaning:
  - replace the direct write with `jsr translated_sprite_write`
  - pad if needed with `nop`

### Helper semantic contract
`translated_sprite_write` should:
1. interpret the descriptor field being written
2. update WRAM sprite staging
3. mark sprite state dirty for VBlank publish

---

## 2. Replace PC090OJ clear/fill loops with SAT buffer clear

### Arcade intent
Clear sprite RAM with off-screen sentinel values.

### Common shape
- setup:
  - `41F9 00D0 0000`  -> `lea 0xD00000, A0`
  - `323C nnnn`       -> count
  - `203C 0000 0100`  -> sentinel
- loop helper call:
  - `6100 xxxx`       -> `bsr fill_helper`

### Genesis replacement strategy
Replace the target buffer from D-window to SAT staging buffer in WRAM.

### Template replacement shape
- before:
  - `41F9 00D0 0000`
- after:
  - `43F9 e0 ff xx xx`
- meaning:
  - replace D-window base with named WRAM SAT buffer base

### Preferred rule
Use symbolized WRAM buffer addresses, not magic constants in the long term.

---

## 3. Replace direct PC080SN tilemap writes with WRAM tilemap shadow writes

### Arcade intent
Write tile/text cells into PC080SN C-window.

### Typical arcade patterns
- `33C0 00C0 xxxx` -> `move.w D0, 0xC0xxxx`
- `41F9 00C0 xxxx` -> `lea 0xC0xxxx, A0`

### Genesis replacement strategy
Write to plane shadow buffer in WRAM, not directly to C-window.

### Template replacement shape
- before:
  - `33C0 00C0 8100`
- after:
  - `33C0 e0 ff c8 4c`
- meaning:
  - redirect a specific text/tile shadow target to the Genesis plane shadow buffer

### Important warning
Do **not** hardcode one-off descriptor values to “pass compares.”
Only redirect actual target buffers, not semantic descriptor fields.

---

## 4. Replace PC080SN plane clear with WRAM text-shadow clear

### Arcade intent
Clear tile planes by filling C-window pages with `0x20`.

### Common shape
- `41F9 00C0 0100`
- `323C 076C`
- `7020`
- `6100 xxxx`

### Genesis replacement strategy
Keep the fill helper structure, but repoint the destination to the WRAM text shadow.

### Template replacement shape
- before:
  - `41F9 00C0 0100`
- after:
  - `43F9 e0 ff c8 4c`

This preserves the existing clear loop but moves ownership to Genesis-side shadow state.

---

## 5. Replace PC080SN scroll/control writes with Genesis scroll staging

### Arcade intent
Write X/Y scroll and control to PC080SN:
- `0xC20000`
- `0xC40000`
- `0xC50000`

### Typical patterns
- `33C0 00C2 0000`
- `33C0 00C4 0000`
- `33C0 00C5 0000`

### Genesis replacement strategy
Replace with WRAM scroll staging writes.

### Template replacement shape
- before:
  - `33C0 00C2 0000`
- after:
  - `33C0 e0 ff 11 3a`

- before:
  - `33C0 00C4 0000`
- after:
  - `33C0 e0 ff 11 38`

### Meaning
- stage scroll values in WRAM
- VBlank later publishes them to VSRAM / VDP scroll registers

---

## 6. Replace early/incorrect renderer call timing with later producer-valid timing

### Current proven issue
Consumer runs before producer-populated descriptor windows are live.

### Typical pattern
- before:
  - `4EB9 0020 05C4`  -> `jsr 0x2005C4`

### Template replacement strategy
Retarget the callsite so the same renderer is invoked after producer completion.

### Template replacement shape
- before:
  - `4EB9 00 20 05 C4`
- after:
  - `4EB9 bb bb bb bb`

Where `bbbbbbbb` is the validated later semantic target.

### Rule
Do **not** patch consumer internals first if the root problem is ordering.

---

## 7. Replace direct hardware-publish assumptions with VBlank dirty-flag set

### Arcade intent
Immediate write to hardware-visible state.

### Genesis replacement strategy
Instead of immediate VDP interaction, set dirty flags.

### Template replacement shape
- before:
  - direct hardware write instruction
- after:
  - `13FC 0001 e0 ff xx xx`  -> set dirty byte
  - `4E71` if needed for padding

### Example uses
- tilemap dirty
- SAT dirty
- palette dirty
- scroll dirty

---

## 8. Insert VBlank publish call into preserved arcade VBlank flow

### Goal
Keep arcade timing/input/state behavior, but add Genesis publish phase.

### Preferred insertion point
After producers have populated WRAM staging, before final cleanup / RTE.

### Template insertion shape
- before:
  - existing `jsr cleanup`
- after:
  - `jsr genesis_vblank_publish`
  - `jsr cleanup`

### Contract for `genesis_vblank_publish`
1. DMA palette if dirty
2. DMA tile patterns if dirty
3. DMA SAT if dirty
4. DMA plane/tilemap updates if dirty
5. publish scroll/control state

---

## 9. VBlank DMA helper call templates

### A. ROM → VRAM tile DMA
Inputs:
- A0 = ROM source
- D0 = VRAM destination word address
- D1 = length in words

Template call:
- `4EB9 cc cc cc cc`

### B. WRAM → SAT DMA
Inputs:
- A0 = SAT staging base
- D0 = VRAM destination `0xF800`
- D1 = length

Template call:
- `4EB9 dd dd dd dd`

### C. WRAM → CRAM DMA/write
Inputs:
- A0 = palette staging base
- D1 = length

Template call:
- `4EB9 ee ee ee ee`

---

## 10. Semantic relocation rules for all patches

Every patch must follow these rules:

1. Validate original bytes before applying replacement.
2. Use semantic anchors (function signature bytes + expected role), not only absolute addresses.
3. Recompute jump-table displacements after insertions.
4. Recompute absolute-long references after shifts.
5. Prefer named symbols for WRAM staging addresses.
6. Emit a post-patch manifest of:
   - callsites changed
   - signatures matched
   - relocated targets
   - jump-table fixes applied

---

## 11. What Andy is likely better at vs Cody

Andy is likely better for:
- architecture
- identifying correct semantic timing
- designing clean staging / VBlank publish
- keeping the whole system coherent

Cody is likely better for:
- grinding through opcode replacements once the architecture is locked
- generating repetitive spec entries
- testing and iterating quickly

Best workflow:
- Andy defines the architecture and exact semantic target
- Cody implements the agreed opcode/spec changes
