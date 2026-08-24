# Cody Final Stage-1 Offline Graphics Compiler Pass

## Baseline and scope

- ROM baseline: Build 0301.
- Build counter: 301.
- Build 0302 was not produced or consumed.
- This was a static arcade-data/compiler pass. It made no Genesis production-runtime change.
- The accepted conservative Plane-B camera-machine envelope from
  `docs/design/Andy_pc080sn_plane_b_static_decoder.md` was used unchanged. No further
  terrain-exact Plane-B reachability investigation was performed.
- Compiler inputs are arcade ROM regions plus `specs/palette_decisions.json`. Runtime traces,
  screenshots, and recorded routes are not compiler inputs.

This pass tests the proposed global pattern range, VDP tile slots 64 through 1535 inclusive.
Slots 0 through 63 remain reserved. Plane and sprite ownership is not a VDP hardware restriction:
both Plane name words and SAT attributes carry the same 11-bit VDP pattern index. The fixed
`SPRITE_TILE_BASE = 1024` is therefore a software convention, not a hardware boundary.

## Static semantic inputs

### Plane A and Plane B

The limiting accepted safety-model interval is Stage-1 record 11:

| Owner | Arcade codes |
|---|---:|
| Plane A | 484 |
| Plane B | 854 |
| Shared A/B codes | 0 |
| Plane code union | 1,338 |
| Byte-distinct Plane patterns | 1,337 |

The one reduction from 1,338 codes to 1,337 patterns is a byte-identical pattern deduplication.
No conservative Plane-B row was discarded to improve fit.

### PC090OJ coexistence subset

The capacity-decisive legal coexistence subset is:

| Family | Source PC090OJ 16x16 cell codes | Unique cells | Unique 8x8 patterns |
|---|---|---:|---:|
| Rastan/player | `0x008A..0x009F` | 22 | 66 |
| Stage-1 Lizard-man | `0x004B..0x006D` | 35 | 89 |
| Hurry-up bat | `0x0268`, `0x0269`, `0x026A`, `0x0276` | 3 | 12 |
| Deduplicated union | | 60 | 166 |

The player and Lizard-man families legally coexist in ordinary Stage-1 gameplay. The hurry-up
family is timer-driven and can join that interval without a map-record residency transition.
Consequently all three are included in record 11's conservative coexistence set.

The player/front semantic producer also owns sword/player-weapon presentation. The known
Rastan/player cell union is the capacity input; any additional sword-only cell omitted from this
optimistic lower bound can only increase demand. Axe/item, large-bat, small-bat, four-armed-enemy,
and other optional-family unions were not added after the lower-bound allocation had already
failed. This is an intentional fail-fast proof, not a claim that the whole Stage-1 placement and
spawn system was exhaustively decoded.

HUD score patterns occupy the reserved/system range and are outside slots 64..1535; the full
status HUD is not an additional sprite-pool family in the accepted configuration.

## Global pattern-capacity result

The audit grants a stronger capability than the real native renderer: it independently
deduplicates all four 8x8 quadrants of each PC090OJ 16x16 cell. The real SAT producer requires the
four patterns of a 16x16 cell to occupy four consecutive VDP tile slots. Independent quadrant
deduplication is therefore a strict optimistic lower bound. A failure in this model cannot be
fixed by a conventional allocator that also honors cell contiguity.

Record 11 arithmetic:

```text
Plane A/B code union                         1338
- duplicate byte pattern within Plane set      1
+ deduplicated sprite 8x8 pattern union       166
- byte-identical Plane/Sprite pattern           1
-------------------------------------------------
optimistic total unique lower bound          1502
global VDP pattern capacity                  1472
exact lower-bound deficit                      30
```

| Metric | Result |
|---|---:|
| Global allocatable range | 64..1535 |
| Capacity | 1,472 patterns |
| Limiting record | 11 |
| Plane A | 484 codes |
| Plane B | 854 codes |
| Plane byte-distinct patterns | 1,337 |
| PC090OJ byte-distinct 8x8 patterns | 166 |
| Cross-owner byte-identical patterns | 1 |
| Total optimistic lower bound | 1,502 |
| Minimum free slots | -30 |

This proves architectural outcome **B: GLOBAL OFFLINE MODEL DOES NOT FIT**. Thirty is the exact
deficit of the allocator-independent optimistic model at the limiting record. It is a lower bound
on the real deficit, not a claim that unresolved optional families need zero patterns. Enforcing
native 16x16 contiguity and adding any omitted legal family can only make the actual deficit
larger.

Because fit failed, the compiler did not create final epochs, globally allocate slots, generate
final Plane/Sprite LUTs, or generate final DMA/CRAM transitions. The transitional 320-slot Plane-B
placeholder and fixed Plane/Sprite compiler partition were not retired. Existing diagnostic
compiler products remain transitional and are not Build-0302-ready output.

## Sprite palette source

The original arcade scene palette path is statically resolved:

1. The 32-byte scene-1 record is at `arcade_ROM/data 0x03BA88`.
2. Record index `i` selects effective arcade palette bank `48+i`.
3. The record byte selects a 16-color block at
   `arcade_ROM/data 0x04FD02 + block_id * 32`.
4. The arcade transform creates xBGR-555 words.
5. Genesis conversion is `0000 BBB0 GGG0 RRR0`, taking the top three bits of each arcade channel.

### Effective bank 0x33 / 51

- Scene record index: 3 at `arcade_ROM/data 0x03BA8B`.
- Block: 12 at `arcade_ROM/data 0x04FE82`.
- Policy: `PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001`, status `proven`, Genesis CRAM line 3.

Arcade xBGR-555:

```text
0000 0842 739C 429E 2154 190C 0012 000C
03DE 01DE 0240 0180 4A52 318C 0100 001E
```

Genesis CRAM:

```text
0000 0000 0EEE 08AE 044A 0246 0008 0006
00EE 006E 0080 0060 0888 0666 0040 000E
```

### Effective bank 0x36 / 54

- Scene record index: 6 at `arcade_ROM/data 0x03BA8E`.
- Block: 13 at `arcade_ROM/data 0x04FEA2`.
- Policy: `PAL-PC090OJ-STAGE1-LIZARDMAN-001`, status `decided`, Genesis CRAM line 0 via the
  documented carrier/reassertion policy.

Arcade xBGR-555:

```text
0000 4318 00C0 0246 01C0 030E 2948 318A
6356 6B9A 10D2 2996 210A 380E 01CE 39CE
```

Genesis CRAM:

```text
0000 08CC 0020 0082 0060 00C6 0444 0664
0CCA 0CEC 0228 046A 0444 0606 0066 0666
```

Effective bank `0x30` / 48 is scene record index 0 at
`arcade_ROM/data 0x03BA88`, block 11 at `arcade_ROM/data 0x04FE62`. Its source colors are decoded,
but this pass does not invent a PC090OJ family assignment for it.

The registry intentionally leaves these contextual decisions unknown:

- `PAL-PC090OJ-GAMEPLAY-LARGE-BAT-001`
- `PAL-PC090OJ-GAMEPLAY-SMALL-BAT-001`
- `PAL-PC090OJ-GAMEPLAY-AXE-ITEM-001`
- `PAL-PC090OJ-GAMEPLAY-FOUR-ARMED-ENEMY-001`

Thus full sprite palette coexistence is not resolved and `CRAM_POLICY_REQUIRED` applies to those
families if they participate in the selected Stage-1 experiment. No extracted colors or guessed
routes were added to `specs/palette_decisions.json`. Pattern capacity fails before a valid final
CRAM epoch can be generated.

## Compiler implementation and verification

`tools/translation/compile_pc080sn_genesis.py` now contains:

- corrected effective-bank 48..79 scene-palette addressing;
- a generic static decoder for effective banks `0x30`, `0x33`, and `0x36`;
- explicit global range constants for slots 64..1535;
- a `--pc090oj-genesis` input;
- a fail-fast `--final-capacity-audit` mode that writes only
  `final_capacity_report.json` and returns nonzero when the global model cannot fit;
- the conservative record-11 Plane-B set and the capacity-decisive sprite lower bound.

Validation results:

- Python syntax check: PASS.
- Two independent final-capacity audit outputs: byte-identical.
- `final_capacity_report.json` SHA-256:
  `69c5200d1663d3c8c7b876429481efd433ac860968e0ed0c958e3e613d99ff80`.
- Two independent normal diagnostic compiler generations: byte-identical.
- Existing diagnostic compiler self-validation: PASS (`23` records, `8` transitional epochs,
  peak `627/640`).
- Production trace dependencies: 0.
- Canonical generated assets were not regenerated because the final global allocation failed.

## Architecture decision boundary

The sole blocker is the exact record-11 optimistic lower-bound deficit: 1,502 patterns required
versus 1,472 available, a deficit of 30 before unresolved optional families and real sprite-cell
contiguity are imposed.

No further terrain-exact Plane-B analysis is requested or authorized by this result. Build 0302
requires Tighe's explicit architectural decision about accepting a different graphics-residency
or hardware-compromise experiment. The compiler does not silently choose that compromise.

## Architecture compliance

- Semantic cut retained: arcade map/scene and actor-family graphics decisions.
- Chip-specific tail targeted for eventual removal: PC080SN destination execution and PC090OJ
  object-RAM/SAT realization below those semantic decisions.
- Transitional compatibility still present: the existing diagnostic 320-slot Plane-B placeholder
  and fixed Plane/Sprite compiler partition. They were not presented as final architecture.
- No runtime cache, per-frame residency manager, software PC080SN/PC090OJ device, production
  runtime patch, ROM, or counter change was introduced.
