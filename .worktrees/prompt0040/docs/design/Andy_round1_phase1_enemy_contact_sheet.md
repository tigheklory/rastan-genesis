# Andy — Round 1 / Phase 1 Seven-Enemy Arcade Contact Sheet (CORRECTED 2026-08-25)

Analysis / artifact only. NO production change, NO ROM, Build counter 313, Build 0314 not consumed.
**ARCADE-ONLY evidence boundary:** original arcade Ghidra/ROM (`build/regions/maincpu.bin`, `pc090oj.bin`),
real emitted PC090OJ records, MAME `rastan` reference source (`docs/reference/mame/rastan/`). NO Genesis ROM/MAME/
Exodus/BlastEm, NO Genesis CRAM/VRAM/SAT/palette-staging/renderer. No base+n, no screenshot colors, no Genesis colors.
This revision **corrects the rejected direct-bank palette assumption** (§7) and adds PC090OJ priority + MAME RGB proofs.

Preserved (NOT added to this enemy sheet; next task): Axe power-up, Boulder hazard, animated swinging rope.

## 1. Phase 0 priors
- **Relevant KNOWN_FINDINGS:** **KF-1214/KF-1220** (exact arcade sprite bank 0x36 = green Lizardman, sprite
  palette reaches WRAM source buffer `A5+0x1600+(bank-0x30)*0x20`; `color=(word0&0x0f)|colbank`) — the ground-truth
  anchor that validated the palette-source decode. KF-043/KF-006 (source-buffer→palette-RAM path), KF-028/153
  (gameplay *plane* palette source, distinct from sprite banks). KF-050/051, OPEN-026/027 (Genesis-side, deferred).
- **HIGH rediscovery hazards:** the sprite-cell format (`preconvert_pc090oj_tiles.py`) and the family-0 compositor
  (`extract_rastan_idle_family0.py`) already exist — reused. Reused the existing renderer `render_r1p1_enemy_contact.py`.
- **Task classification:** EXTENDING.
- **Open/Closed Issues Impact:** none changed. OPEN-026/027 remain deferred. palette_decisions.json updated with
  newly-proven facts (required by CLAUDE.md sole-authority mandate).
- **Contradiction status:** No CONFIRMED/STRONG contradiction. (Corrected the old summary's compositor-table
  addresses fam1=0x4771C/fam3=0x40004 — verified WRONG; real emitted records used instead.)

## 2. Baseline
Prior task closed 4/7 identities + composites in a debug index palette. This task closes the remaining
3 identities (Valkyrie, Small Bat, Large Bat) and decodes the TRUE arcade 16-color palettes for all seven.

## 3–5. The three missing enemies (identity proofs)
Method: prove the actor is a live R1/P1 actor in the saved trace → extract its REAL emitted PC090OJ records →
render from `pc090oj.bin` with its real arcade palette → identify appearance.
- **Valkyrie** = `actor_2c8`, **+0x3E=8 / base 0x0241** (records 7-9), bank **0x32**. Renders as an armored
  female warrior with a weapon. (Ordinary +0x3E family; the remaining unidentified 2c8 humanoid.)
- **Small Bat** = `actor_748`, **base 0x0268**, bank **0x3E**. Single 16×16 cell; renders as a small purple bat.
- **Large Bat** = `actor_5c8`, **base 0x03F6**, bank **0x3E**. Multi-cell; renders as a larger purple winged bat.
Non-enemy hazards seen among candidates and NOT included: `actor_2c8 base 0x00F4` (teal rope/whip),
`actor_5c8 0x050B` / `actor_748 0x019D` (spear/fireball projectiles). The three enemy names are arcade-render
visual IDs — **USER MUST VERIFY** the names (structural ownership + composite + palette all proven from arcade evidence).

## 6. Real emitted compositor method
For all seven enemies the composite is the actual arcade PC090OJ output captured in the trace: per piece
`code / x / y`, `flipx=word0&0x4000`, `flipy=word0&0x8000`, `color=word0&0x0F`. Flying Demon = two co-located
`actor_508` components (A @0x10C508 records 57-69 = BODY; B @0x10C548 records 70-82 = WINGS, PROVEN by render).
No base+n; physical cell SHA-1s in `enemy_patterns.json`.

## 7. Correction — the palette source is INDIRECT (round-indexed), not direct-bank
An earlier pass assumed `palette_source(bank) = 0x4FDE2 + (bank-0x30)*0x20`. **That was wrong** and matched only
Lizardman by coincidence. The real original-arcade loader (traced from `FUN_0003ba20 / FUN_0003ba56 / FUN_0003ba64`):
- `FUN_0003ba20` reads round byte `A5+0x118`, computes row `= 0x3BA88 + (round-1)*0x20`, iterates the 32 sprite
  source-buffer banks, reads one **pool-index byte** per bank, and calls `FUN_0003ba56`.
- `FUN_0003ba56`: `A3 = 0x4FD02 + pool_index*0x20`, 16 colors, then `FUN_0003ba64` converts and writes to `A5+0x1600`.
So for hardware bank `0x30+k`: `pool_index = maincpu[0x3BA88 + (round-1)*0x20 + k]`, source `= 0x4FD02 + pool_index*0x20`.
Round-1 index row (re-read from ROM, not hardcoded): `0B 0B 0F 0C 12 10 0D 0B 0B 14 16 0B 23 00 24 0B 0B 1E 1E 0C 1E 10 0D 0B 0B 14 16 0B 23 01 24 02`.
Lizardman (bank 0x36, k=6) → pool index 13 → `0x4FEA2` = KF-1214 green (validation intact); every other bank now
resolves to a **different** pool entry than the rejected direct-bank formula. `FUN_0003ba64` bit math proves 5-bit
channel = nibble*2. **MAME display RGB** = `xBGR_555` `pal5bit(v)=(v<<3)|(v>>2)` applied to each 5-bit channel
(rastan.cpp `set_format(xBGR_555)`), i.e. `RGB8 = pal5bit(nibble*2)`.

## 8. Seven palette banks (corrected, round-1 indirect)
| Enemy | Bank | k | pool idx | Source | 16-color |
|-------|------|---|----------|--------|----------|
| Lizardman | 0x36 | 6 | 13 | 0x4FEA2 | PROVEN (=KF-1214, green) |
| Four-armed insect | 0x3A | 10 | 22 | 0x4FFC2 | PROVEN |
| Valkyrie | 0x32 | 2 | 15 | 0x4FEE2 | PROVEN |
| Chimera | 0x34 | 4 | 18 | 0x4FF42 | PROVEN |
| Flying Demon | 0x35 | 5 | 16 | 0x4FF02 | PROVEN (attr 0x80 but emitted nibble 5) |
| Small Bat | 0x3E | 14 | 36 | 0x50182 | PROVEN |
| Large Bat | 0x3E | 14 | 36 | 0x50182 | PROVEN |
Rejected WRONG sources: Four-armed 0x4FF22, Valkyrie 0x4FE22, Chimera 0x4FE62, Flying Demon 0x4FE82, bats 0x4FFA2.
Full raw 0RGB words + converted xBGR555 + MAME-display RGB8 in `enemy_palettes.json` (the `genesis_quantized_3bit`
field was removed — Genesis optimization data does not belong in the arcade-reference corpus). Registry corrected in
`specs/palette_decisions.json`.

### 8a. PC090OJ overlap priority (proven from MAME pc090oj.cpp)
`draw_sprites` non-priority path iterates `start=(SIZE/2)-4 … inc=-4` (high record → low) with painter's-algorithm
`transpen`, and the header states **"First sprite has *highest* priority"** → **lowest record number draws on top
(foreground)**. `color = (data & 0x000f) | sprite_colbank` confirms the bank derivation. The offline renderer paints
higher records first, lower records last. Flying Demon: body = records 57-69 (front), wings = 70-82 (behind) →
**WINGS BEHIND BODY**, matching the arcade.

### 8b. Palette stability (static writer census)
No routine writes sprite-bank palette RAM `0x200640..0x2007DF` directly; the banks are populated once at stage-load
(`FUN_00045d7c → FUN_0003ba20`, round-indexed) and delivered by whole-buffer copy. No gameplay routine rewrites
banks 0x32/0x34/0x35/0x36/0x3A/0x3E during R1/P1 → palettes STABLE (static proof; no runtime capture needed).

## 9. Contact-sheet generation
`contact_sheets/r1p1_enemies.png` — 7 panels, true arcade palettes, 16 swatches + bank per enemy, nearest-neighbor,
no filtering. `contact_sheets/r1p1_enemies_diagnostic.png` — Flying Demon A/B/combined at bank 0x35.
`contact_sheets/r1p1_enemies.html`. Tool: `tools/graphics_optimizer/render_r1p1_enemy_contact.py`.

## 10. Zero-guess validation
Palette decode validated against KF-1214 ground truth (bank 0x36 green Lizardman, unchanged); every enemy now renders
as a recognizable, correctly-coloured arcade sprite via the corrected round-1 indirect loader (green lizardman, blue
four-armed insect, blonde/red Valkyrie, orange chimera, blue sword-wielding demon with wings behind body, gold-brown
bats). PC090OJ overlap priority proven from MAME. Guessed composites 0, screenshot colors 0, Genesis colors 0. Enemy
names are arcade-render visual IDs (USER VERIFY the names and the seven palettes vs the original arcade).

## 11. Open/Closed Issues Impact
None changed. OPEN-026 (duplicate Lizardman composites) and OPEN-027 (Flying Demon component split on Genesis)
remain deferred — arcade source of truth unaffected.

## 12. Closure
Semantic 7/7 · real composite 7/7 · effective bank 7/7 · **exact 16-color palette 7/7 (corrected, round-1 indirect)** ·
palette stability PROVEN · PC090OJ priority PROVEN · MAME RGB `pal5bit(nibble*2)` · guessed 0 · screenshot colors 0 ·
Genesis evidence 0 · panels 7/7. **R1/P1 SEVEN-ENEMY CONTACT SHEET = CORRECTED/COMPLETE**, pending Tighe's visual
acceptance of the seven palettes and the Valkyrie / Small Bat / Large Bat names.

**KNOWN_FINDINGS:** the bad direct-bank generalization was never written to `KNOWN_FINDINGS.md` (verified), so nothing
to retract there. Proposed durable finding (not self-promoted): *R1/P1 sprite palettes load via `FUN_0003ba20` using
the round-specific 32-byte index row at `0x3BA88+(round-1)*0x20`; each source-buffer bank selects a pool record at
`0x4FD02+pool_index*0x20`, converted by `FUN_0003ba64` (5-bit=nibble*2), displayed by MAME `xBGR_555 pal5bit`.*

## Next boundary
Expand this proven pipeline (real emitted records → pc090oj.bin composite + arcade source-table palette) to ALL
R1/P1 sprites (Rastan, sword, Axe, Flame Sword, Flail, boulder, cave block, rope, projectiles, effects, HUD). Not this task.
