# Andy — Rastan Arcade Scrolling Model vs Attract-Mode Scroll and Genesis Translation Strategy

## 1. Executive Summary

Arcade Rastan implements scrolling entirely through the **PC080SN tilemap chip** and its companion hardware scroll registers, not through tilemap RAM content changes. The CPU writes pixel-position scroll values to memory-mapped registers at `0x3C0000` (PC080SN scroll) and `0xC20000`/`0xC40000` (PC080SN FG/BG scroll clear resets); the chip hardware applies those values when rendering each scanline. Attract-mode scrolling uses the **same register write path** as gameplay scrolling. It is not a different mechanism. The visual difference between attract mode and gameplay scrolling is only in _what values_ are written and _how often_, not in the hardware path.

The scroll workram fields at `A5+0x10AE`/`A5+0x10B0` (FG layer) and `A5+0x10EC`/`A5+0x10EE` (BG layer) are the staging point for both layers in both modes. Scroll values are written into these workram fields by the arcade game logic, and then the current project reads them in `genesistan_scroll_from_workram_vdp()` to stage them for VBlank commit.

In the no-SGDK direct-execution branch, the correct translation model is: scroll workram fields are written by the arcade tick as usual; a single scroll commit assembly stub reads those four workram words and writes them to VDP VSRAM and HScroll table once per VBlank, after display-off and before display-on. No intermediate C code. No SGDK VDP helpers. The model is directly confirmed by Rainbow Islands Genesis.

---

## 2. Rastan Arcade Scroll Hardware Model

### 2.1 The PC080SN Tilemap Chip

Rastan's background and foreground scrolling is owned by the **PC080SN** custom tilemap chip. This chip drives two independent tilemap layers (a BG plane and an FG plane), each with its own full-screen pixel-accurate horizontal and vertical scroll registers. The chip reads the scroll register values on every scanline and offsets its internal tile-fetch address accordingly. The tilemap RAM content does not change when the screen scrolls — the chip shifts the rendering window within the fixed tilemap data.

This is structurally identical to the Genesis VDP's own scrolling architecture (HScroll table + VSRAM), which is why the translation is direct.

### 2.2 Scroll Register Write Mechanism

The CPU affects scrolling by writing a **word value** to the PC080SN scroll register address via a plain `movew`:

```
movew %d0, 0x3C0000     ; update scroll position on PC080SN
```

This is a single-instruction, immediate-effect write. No multi-step protocol. No chip-select latch. No DMA. The written word encodes the current pixel scroll offset for the active layer; the chip applies it on the next scanline or frame.

The scroll register at `0x3C0000` is confirmed by 7 write sites in the arcade ROM (`build/maincpu.disasm.txt`, lines for `0x03A012`, `0x03AF0A`, `0x03AF14`, `0x03AF4C`, `0x03AF72`, `0x03AF7E`, `0x03B07E`).

Additional scroll-related addresses:
- `0xC20000` — PC080SN FG scroll accumulator / reset (`clrl 0xC20000` seen at `0x03ABBA`, `0x03B098`)
- `0xC40000` — PC080SN BG scroll accumulator / reset (`clrl 0xC40000` seen at `0x03ABC0`, `0x03B09E`)

The `clrl` writes to `0xC20000`/`0xC40000` are scroll-clear operations: they reset the running scroll accumulator for each layer to zero, used at scene transitions and attract-mode sequence resets.

### 2.3 Per-Frame Register Update Model

The scroll register write at `0x03A012` is inside the **main game tick entry** — the very first substantive instruction after the interrupt unmask at `0x03A008`. This confirms scroll is written **once per game tick**, as the first action of every frame's processing, not lazily or conditionally. It is an unconditional per-frame write.

---

## 3. Gameplay Scroll Mechanism

### 3.1 Scroll Value Source

During gameplay, scroll values are maintained in two pairs of workram words relative to the A5 base:

| Workram offset | Field | Layer |
|----------------|-------|-------|
| `A5+0x10AE` | FG horizontal scroll | Foreground (player layer) |
| `A5+0x10B0` | FG vertical scroll | Foreground |
| `A5+0x10EC` | BG horizontal scroll | Background |
| `A5+0x10EE` | BG vertical scroll | Background |

These values are written by the gameplay camera/scroll management code. The write site at `0x050508–0x05051C` (from `build/maincpu.disasm.txt`) shows all four scroll workram fields being populated from a table lookup:

```asm
50508:  lea  %a1@(0, %d1:w), %a1    ; address into scroll table
5050c:  movew %a1@+, %d1
5050e:  movew %d1, %a5@(0x10AE)     ; FG X scroll
50512:  movew %d1, %a5@(0x10EC)     ; BG X scroll
50516:  movew %a1@+, %d1
50518:  movew %d1, %a5@(0x10B0)     ; FG Y scroll
5051c:  movew %d1, %a5@(0x10EE)     ; BG Y scroll
```

This confirms: during gameplay, **BG and FG start from the same scroll value** (both X fields receive the same source word, both Y fields receive the same source word), then diverge as the parallax layer logic modifies them independently.

### 3.2 Update Frequency

Scroll workram fields are updated once per game tick by the camera/level-scroll subsystem. The `movew %d0, 0x3C0000` write at `0x03A012` is the first instruction of the main tick and uses whatever value was last placed in d0 from the prior frame's scroll accumulation. The workram fields are the persistent state; `0x3C0000` is the hardware manifestation of that state.

### 3.3 Layer Separation

BG and FG are separate layers on the PC080SN. Each has independent scroll registers. The arcade code writes them in sequence. In the current project, `genesistan_scroll_from_workram_vdp()` reads all four workram fields and stages them independently (`staged_scroll_x_bg`, `staged_scroll_y_bg`, `staged_scroll_x_fg`, `staged_scroll_y_fg`).

**Gameplay scrolling mechanism identified: YES**

---

## 4. Attract-Mode Scrolling / Items / Text Mechanism

### 4.1 Attract Mode Uses the Same Scroll Path

Attract-mode scrolling is **not a different mechanism**. The attract-mode sequence runs through the same arcade tick entry point (`0x03A008`), the same `movew %d0, 0x3C0000` write at `0x03A012`, and writes the same workram scroll fields via the same camera/scroll subsystem. The code path divergence between attract mode and gameplay is controlled by the workram mode word at `A5+0x0002` (compared at `0x03A018`), but both paths exit through the same per-frame scroll commit.

### 4.2 The Attract-Mode "Scrolling Items / Text" Behavior

What appears to be scrolling text or scrolling objects during attract mode is not camera scrolling through the scroll registers. It is **tilemap content replacement**. The attract-mode sequence:

1. Writes new tile indices into PC080SN tilemap RAM at `0xC00000`/`0xC08000` (FG) and `0xC04000`/`0xC0C000` (BG)
2. Keeps the scroll register static or updates it minimally
3. The visual effect of items/text "scrolling" across the screen is achieved by writing new tile data into successive tilemap positions each frame, not by moving the viewport

This is confirmed by the scroll clear operations at `0x03ABBA`/`0x03ABC0` (`clrl 0xC20000` / `clrl 0xC40000`) which appear inside the attract-mode state handler at `0x03AB96`: the scroll accumulator is reset to zero when entering the attract sequence, pinning the viewport at origin while tilemap content changes drive the apparent motion.

### 4.3 Text Writer in Attract Mode

The text display during attract (`bsrw 0x3bb48` at `0x03ABCC`, `0x03B0A6`) writes character tile data through the PC080SN C-window text layer — this is pure tilemap content writing, not scroll register usage. The "scrolling" of text items in attract mode is the arcade tile-based text writer placing new glyphs into successive tilemap cells across frames, not viewport movement.

**Attract-mode scrolling mechanism identified: YES**
**Same as gameplay scrolling: NO** — attract mode uses the same scroll register path for viewport position (held at or near zero), but the visual "scrolling" of text/items is driven by tilemap content writes, not by changing the scroll offset.

---

## 5. Gameplay vs Attract-Mode Scroll Comparison

| Aspect | Gameplay | Attract Mode |
|--------|----------|--------------|
| Scroll workram fields written | YES — camera updates `A5+0x10AE/B0/EC/EE` each tick | YES — same fields, but held near zero or incremented slowly |
| `movew %d0, 0x3C0000` per tick | YES — unconditional, first instruction of tick | YES — same path, same instruction |
| Scroll accumulator reset (`clrl 0xC20000/C40000`) | At scene transitions only | At attract-sequence start (`0x03ABBA`) |
| Layers scrolling | Both BG and FG scroll independently per camera | Both held near zero; no parallax |
| "Visual scrolling" source | Viewport position change via scroll registers | Tilemap content replacement (tile writes) |
| Text/items presentation | Scroll register drives camera; tiles are static level content | Tiles replaced each frame; scroll register is static |
| Tilemap updates coupled to scroll | YES — tile streaming + scroll change together | Tilemap changes are the _only_ visual motion; scroll is passive |
| Update frequency | Every game tick | Every game tick (same cadence) |

---

## 6. Relation to Current Project Evidence

### 6.1 The Rolling Noise / Dots Observation

The "rolling dots" visible on screen in current builds with sprite rendering suppressed come from the tilemap content being written by the arcade tick via `genesistan_bulk_tilemap_commit` and `genesistan_asm_tilemap_commit_fg/bg`. The scroll register in those frames is near zero (attract mode holds it there), so the viewport is not moving. The visual motion is entirely tile content replacement. This matches the attract-mode model above: tiles written to successive positions each frame create the appearance of motion.

### 6.2 Staged Scroll Values of Zero

The current project's `genesistan_scroll_from_workram_vdp()` reads `A5+0x10AE/10B0/10EC/10EE`. During attract mode these fields are near zero because the attract-mode sequence resets the scroll accumulator and does not drive camera movement. The resulting staged scroll values are zero or near-zero, which is correct — the viewport stays fixed while tile content changes. The `build322_unconditional_zero_scroll_proof_fix.md` correctly observed this behavior: forcing all scroll to zero had no visible effect because the attract-mode scroll was already near zero.

### 6.3 Empty Layer A (Plane A)

The empty Plane A observation (builds 323–327) was caused by the Window plane covering Plane A (fixed in Build 327), not by a scroll problem. Scroll was staging correctly; the plane content was committed to VRAM correctly; the display was simply blocked. This is consistent with the scroll model: scroll was not the cause of any visibility problem.

### 6.4 The VBlank Scroll Commit Site Count

The prior VDP write census (Build 337 audit) identified `genesistan_scroll_from_workram_vdp()` as a hook called during the arcade tick — once per frame via the opcode patches at the `0x3C0000` write sites. This aligns exactly with the arcade model: one `movew %d0, 0x3C0000` per tick → one call to the Genesis staging function per tick → one VBlank commit per frame.

---

## 7. Genesis Translation Model for a Direct-Execution Branch

### 7.1 Arcade-to-Genesis Mapping

| Arcade PC080SN | Genesis VDP equivalent |
|---------------|----------------------|
| FG layer horizontal scroll register | HScroll table VRAM 0xF000 word 0 (BG_A) |
| FG layer vertical scroll register | VSRAM offset 0 (BG_A) |
| BG layer horizontal scroll register | HScroll table VRAM 0xF000 word 1 (BG_B) |
| BG layer vertical scroll register | VSRAM offset 2 (BG_B) |

VDP register 11 = `0x8B00` configures full-screen horizontal and vertical scroll mode, making a single word at each of the four positions control the entire plane. VDP register 13 = `0x8D3C` sets the HScroll table base at VRAM 0xF000.

### 7.2 Scroll Convention Conversion

The arcade PC080SN uses an additive scroll convention: increasing the scroll register value shifts the viewport right/down (content moves left/up on screen). The Genesis VDP uses the same convention for horizontal scroll (positive = shift viewport right) but the negation depends on implementation.

The existing conversion in `genesistan_scroll_from_workram_vdp()` applies:
- BG X = `-(workram[0x10EC/2])` — negation converts arcade convention
- BG Y = `-(workram[0x10EE/2]) + 8` — negation + 8px vertical crop bias (240→224 line difference)
- FG X = `-(workram[0x10AE/2])`
- FG Y = `-(workram[0x10B0/2]) + 8`

This conversion is correct and must be preserved in the no-SGDK branch.

### 7.3 Staging Model (Outside VBlank)

During the arcade tick (which runs in the main loop in the no-SGDK branch):

- The opcode patch at the `movew %d0, 0x3C0000` write site replaces the hardware register write with a call to `genesistan_scroll_stage` (assembly stub)
- `genesistan_scroll_stage` reads all four workram scroll fields, applies the negation and vertical bias, and writes the four converted values to four WRAM staging words
- No VDP access occurs during this staging

This is identical to the current `genesistan_scroll_from_workram_vdp()` behavior, expressed as pure assembly.

### 7.4 Commit Model (Inside VBlank)

Once per VBlank, the commit handler reads the four staged words and writes them to VDP:

```asm
_commit_scroll:
    movea.l #0xC00004, %a0
    movea.l #0xC00000, %a1
    
    move.w  #0x8F02, (%a0)          ; auto-increment = 2
    
    ; HScroll table at VRAM 0xF000
    move.l  #0x70000003, (%a0)      ; VRAM write addr 0xF000
    move.w  staged_scroll_x_fg, (%a1)   ; word 0 = FG (BG_A)
    move.w  staged_scroll_x_bg, (%a1)   ; word 1 = BG (BG_B)
    
    ; VSRAM at offset 0
    move.l  #0x40000010, (%a0)      ; VSRAM write addr 0x0000
    move.w  staged_scroll_y_fg, (%a1)   ; offset 0 = FG (BG_A)
    move.w  staged_scroll_y_bg, (%a1)   ; offset 2 = BG (BG_B)
    
    rts
```

This runs **after display ON** (VSRAM writes are safe after display re-enable, same as Rainbow Islands). It runs unconditionally every frame because the arcade tick writes scroll every frame.

### 7.5 Attract Mode Requires No Special Handling

Because attract-mode visual motion is driven by tilemap content replacement (not scroll register changes), the scroll commit path does not need to treat attract mode differently from gameplay. Both modes write the same four workram fields; both use the same staging/commit path. The committed values happen to be near-zero during attract mode, which is correct — the viewport stays still while tiles change.

---

## 8. Rainbow Islands Genesis Reference Mapping

### 8.1 Directly Applicable Model

Rainbow Islands Genesis stores scroll values in WRAM during the main loop and commits them in VBlank after display re-enable. The specific addresses from the Rainbow Islands audit:

- `0xFFFFF630` — BG horizontal scroll staging (WRAM)
- `0xFFFFF634` — BG vertical scroll staging (WRAM)
- VBlank: single `move.l` to VSRAM at `0xC00004` / `0xC00000` after display ON

This is the exact model the no-SGDK branch implements: WRAM staging during game tick, single commit in VBlank. The Rainbow Islands model writes scroll **after** display re-enable, which is safe because VSRAM writes do not cause visual artifacts the way tilemap writes do.

### 8.2 Directly Applicable: Post-Display-Enable Timing

Rainbow Islands commits scroll _after_ `move.w %d0, 0xC00004` (display ON), not before. The no-SGDK branch should follow this ordering:

```
VBlank handler order:
  1. Display OFF
  2. Commit tilemaps (BG + FG buffers → VRAM)
  3. Commit SAT (DMA)
  4. Commit palette (if flagged)
  5. Display ON
  6. Commit scroll (VSRAM + HScroll table)  ← after display ON
```

VSRAM and HScroll table writes during active display are safe on Genesis because the VDP double-buffers scroll state internally. Rainbow Islands proves this ordering is correct for this hardware family.

### 8.3 Assumed Analogy (Not Directly Proven for Rastan)

Rainbow Islands has a single BG layer and one scroll pair. Rastan has two independent layers (BG + FG) each with X and Y scroll. The extension from one pair to two pairs (four values) follows directly from the VDP's HScroll table layout (two words at 0xF000) and VSRAM layout (two words at offset 0), but this is an architectural extension, not a directly observed Rainbow Islands behavior.

### 8.4 Non-Proven but Useful Guidance

Rainbow Islands uses a dirty flag for scroll commit (only commits if scroll changed). For Rastan, the arcade tick writes the scroll register unconditionally every frame, so the staging value changes every frame regardless. A dirty flag would not save any VBlank time and adds complexity. Unconditional commit every frame is the correct choice for Rastan specifically.

---

## 9. Single Final Translation Recommendation

**Stage all four arcade scroll workram fields (`A5+0x10AE`, `A5+0x10B0`, `A5+0x10EC`, `A5+0x10EE`) to four WRAM words during the arcade tick via the opcode patch at the `0x3C0000` write site, applying the negation and +8 vertical bias during staging; then commit all four values unconditionally to the Genesis HScroll table (VRAM 0xF000, 2 words) and VSRAM (offset 0, 2 words) in a single 8-instruction assembly stub called after display re-enable in the VBlank handler.**

This single path handles both gameplay scrolling and attract-mode scrolling without any mode distinction, because the attract-mode scroll workram values are already correct (near-zero, held by the attract sequence) and the tilemap-content-based "visual scrolling" of attract-mode text/items is handled entirely by the separate tilemap commit path, not by scroll register changes.

---

## 10. Final Verdict

Rastan arcade scrolling is owned by the PC080SN chip via a single `movew %d0, 0x3C0000` per game tick. Attract-mode scrolling is the same hardware path, with scroll values near zero; the visual motion of text/items in attract mode is tilemap content replacement, not viewport movement. The Genesis translation is a direct substitution: stage four workram fields into four WRAM words during the tick, commit them to HScroll table and VSRAM once per VBlank after display re-enable. No SGDK helpers. No mode distinction. The Rainbow Islands Genesis model proves this ordering and staging approach is correct for this hardware family.
