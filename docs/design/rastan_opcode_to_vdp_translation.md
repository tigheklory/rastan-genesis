# Rastan Arcade → Genesis VDP Opcode Translation Templates

## 1. Purpose

Define explicit, repeatable opcode-level translation patterns for converting
arcade Rastan graphics intent into Genesis VDP operations.

This document is the bridge between:
- arcade hardware behavior (PC080SN / PC090OJ)
- Genesis VDP rendering model (VRAM / SAT / CRAM / VSRAM)

This is NOT a per-screen hack.
This is a systematic transformation layer.

## 2. Core Principle

Translate intent, not instructions.

Arcade:
- CPU writes to hardware memory windows

Genesis:
- CPU builds WRAM staging
- VBlank DMA pushes to VDP

## 3. Translation Classes

| Arcade Hardware | Intent | Genesis Target |
|----------------|--------|----------------|
| PC080SN | tilemap / text | Plane A / Plane B |
| PC090OJ | sprites | SAT (Sprite Attribute Table) |
| Palette RAM | colors | CRAM |
| Scroll registers | camera | VSRAM / VDP registers |

## 4. PC090OJ (SPRITES) → SAT

### Arcade Pattern
- move.w D0, 0xD00000(Ax)
- move.l D0, 0xD00000(Ax)
- lea 0xD00000, A0
- move.l Dn, (A0)+

### Intent
- Write sprite descriptors
- Each sprite = position + tile + attributes

### Genesis Translation
Write into SAT buffer:
- word 0: Y
- word 1: size + link
- word 2: tile + attributes
- word 3: X

### VBlank Commit
- DMA SAT buffer → VRAM address 0xF800
- Size: 640 bytes

## 5. PC080SN (TILEMAP / TEXT) → PLANES

### Arcade Pattern
- move.w D0, 0xC00000(Ax)
- move.w D0, 0xC08000(Ax)
- lea 0xC00000, A0

### Intent
- Write tile indices into tilemap
- Clear planes
- Write text characters

### Genesis Translation
- Write tile index + attributes into TEXT_SHADOW buffer

### VBlank Commit
- DMA tilemap → VRAM
  - Plane A → 0xE000
  - Plane B → 0xC000

## 6. TILE GRAPHICS (PATTERNS)

### Rule
If tile not in VRAM:
- DMA from ROM → VRAM

## 7. PALETTE → CRAM

### Translation
- WRAM palette buffer → CRAM via DMA

## 8. SCROLL / CONTROL → VDP

### Arcade Pattern
- move.w D0, 0xC20000
- move.w D0, 0xC40000
- move.w D0, 0xC50000

### Genesis Translation
- Stage SCROLL_X / SCROLL_Y

### VBlank Commit
- Write to VSRAM and VDP scroll registers

## 9. VBLANK EXECUTION MODEL

Genesis:
- Clear WRAM buffers
- Run producers
- Ensure tiles in VRAM
- DMA:
  - tiles
  - SAT
  - tilemap
  - palette
- Apply scroll

## 10. ORDER OF OPERATIONS

1. Clear WRAM buffers
2. Run producers
3. Resolve tile usage
4. DMA tiles → VRAM
5. DMA SAT → VRAM
6. DMA tilemap → VRAM
7. DMA palette → CRAM
8. Apply scroll

## 11. FINAL RULE

Every arcade graphics write must map to:
- WRAM state change
- OR VDP publish step
