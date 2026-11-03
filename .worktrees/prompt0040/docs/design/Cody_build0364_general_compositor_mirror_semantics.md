# Cody — Build 0364 general compositor mirror semantics

## Result and acceptance boundary

Build 0364 restores the original arcade's general default-compositor branch predicate in the
direct-native actor-to-SAT producer.  It does not special-case actor `0x00F4`, the rope, a swing
direction, a segment, or a left/right presentation.  Both existing transforms remain intact:

- normal: `X = actorX + signed_piece_x`, with the mapping record's `0x80` control selecting H flip;
- mirror: `X = actorX - signed_piece_x - 16`, with H flip set for the piece.

The automated canonical and GENESIS NTSC gameplay-entry gates pass, but their input path does not
reach Round 1 Segment 5.  Therefore the mirror defect is **not declared user-solved** until Tighe
validates Build 0364 in BlastEm.

## Architecture boundary

The retained semantic input is the actor record plus its selected mapping program.  The native
helper expands that state directly into the native sprite queue and final Genesis SAT.  The removed
chip-specific tail remains original arcade `0x41DAE -> 0x3D054 -> 0x3C902` PC090OJ record production
and PC090OJ hardware execution.  Build 0364 introduces no PC090OJ object RAM, D-window adapter,
mirror, shadow, scratch record, fallback, NOP, or bypass.

## Exact original predicate

Original arcade disassembly `0x3C954..0x3C95E` and `0x3CA26..0x3CA34` selects the normal
`0x3C960` path as follows:

```text
if (actor[0x20] & 1) != 0:
    normal = actor[0x03] != 0 || actor[0x02] == 0
else:
    normal = actor[0x02] != 0
mirror = !normal
```

Build 0364 implements that predicate literally at `.Lnea_default`.  The complete truth table is:

| `+0x20 bit0` | `+0x03 != 0` | `+0x02 != 0` | Arcade branch | Build 0364 branch |
|---:|---:|---:|---|---|
| 0 | 0 | 0 | mirror | mirror |
| 0 | 0 | 1 | normal | normal |
| 0 | 1 | 0 | mirror | mirror |
| 0 | 1 | 1 | normal | normal |
| 1 | 0 | 0 | normal | normal |
| 1 | 0 | 1 | mirror | mirror |
| 1 | 1 | 0 | normal | normal |
| 1 | 1 | 1 | normal | normal |

Build 0363 instead used only the last column's `+0x02` input (`0 => mirror`, `!=0 => normal`).

### What the fields are known to mean

| Field | Proven meaning used here |
|---|---|
| `actor+0x20 bit 0` | Raw bit passed by the caller in D6 and used by the compositor to select the alternate three-field branch rule. A broader semantic name is not proven. |
| `actor+0x03` | Raw actor state byte consulted only when `actor+0x20 bit 0` is set. It is nonzero for the captured Segment-5 rope; a broader semantic name is not assigned. |
| `actor+0x02` | Retained orientation byte passed by the caller in D7. Its value alone is not the general branch predicate. |

The rope's initialization/retained-state evidence has `+0x20 bit0=1` and `+0x03!=0`.  Consequently
the original predicate remains on the normal branch for either value of `+0x02`.  This is the
crucial correction: the spatial center crossing does **not** cause the original compositor to take
the mirror branch.  The selected rope mapping program itself changes signed X offsets and uses
control `0x80`, producing the observed `word0=0x4080`.  Build 0363 could take the mirror path from
`+0x02` alone and apply a second X/flip transform.  Build 0364 changes branch selection at exactly
the retained three-field condition, not at a guessed swing coordinate.

## Nine-piece comparison

Source rows are the existing ORIGINAL ARCADE capture
`analysis/graphics_optimizer/round1_phase1_corpus/full_capture/full_observations.csv`, records
140..148.  Relative coordinates below use piece 140 as `(0,0)`.  `N(code)` denotes the exact native
logical tile code presented to the residency resolver.  The final physical Genesis pattern index is
`1339 + 4*s(code)`, where `s(code)` is that code's current native 16x16 residency slot; slot identity
is intentionally dynamic, while the source code and four-pattern cell are exact.  Normal gameplay
has global sprite control `1`, so the SAT transform is `SAT X=(native X+0x80)&0x1FF` and
`SAT Y=(native Y-8+0x80)&0x1FF`.  The default compositor emits no V flip.

### Left of center — arcade frame 2639

| Piece | Arcade rel X/Y | Arcade code | Arcade H/V | Native rel X/Y | Native tile | Native H/V | Final SAT X/Y |
|---:|---:|---:|---|---:|---|---|---:|
| 140 | 0 / 0 | `00F4` | 0/0 | 0 / 0 | `N(00F4)` | 0/0 | `01D0/0070` |
| 141 | 1 / 10 | `00F4` | 0/0 | 1 / 10 | `N(00F4)` | 0/0 | `01D1/007A` |
| 142 | 2 / 21 | `00F4` | 0/0 | 2 / 21 | `N(00F4)` | 0/0 | `01D2/0085` |
| 143 | 3 / 32 | `00F4` | 0/0 | 3 / 32 | `N(00F4)` | 0/0 | `01D3/0090` |
| 144 | 4 / 42 | `00F5` | 0/0 | 4 / 42 | `N(00F5)` | 0/0 | `01D4/009A` |
| 145 | 5 / 53 | `00F4` | 0/0 | 5 / 53 | `N(00F4)` | 0/0 | `01D5/00A5` |
| 146 | 6 / 64 | `00F4` | 0/0 | 6 / 64 | `N(00F4)` | 0/0 | `01D6/00B0` |
| 147 | 7 / 74 | `00F5` | 0/0 | 7 / 74 | `N(00F5)` | 0/0 | `01D7/00BA` |
| 148 | 9 / 85 | `00F6` | 0/0 | 9 / 85 | `N(00F6)` | 0/0 | `01D9/00C5` |

### Center/straight transition — arcade frame 2632

| Piece | Arcade rel X/Y | Arcade code | Arcade H/V | Native rel X/Y | Native tile | Native H/V | Final SAT X/Y |
|---:|---:|---:|---|---:|---|---|---:|
| 140 | 0 / 0 | `00F4` | 0/0 | 0 / 0 | `N(00F4)` | 0/0 | `01DE/0070` |
| 141 | 0 / 10 | `00F4` | 0/0 | 0 / 10 | `N(00F4)` | 0/0 | `01DE/007A` |
| 142 | 0 / 21 | `00F4` | 0/0 | 0 / 21 | `N(00F4)` | 0/0 | `01DE/0085` |
| 143 | 0 / 32 | `00F4` | 0/0 | 0 / 32 | `N(00F4)` | 0/0 | `01DE/0090` |
| 144 | 0 / 42 | `00F4` | 0/0 | 0 / 42 | `N(00F4)` | 0/0 | `01DE/009A` |
| 145 | 0 / 53 | `00F4` | 0/0 | 0 / 53 | `N(00F4)` | 0/0 | `01DE/00A5` |
| 146 | 0 / 64 | `00F4` | 0/0 | 0 / 64 | `N(00F4)` | 0/0 | `01DE/00B0` |
| 147 | 0 / 74 | `00F4` | 0/0 | 0 / 74 | `N(00F4)` | 0/0 | `01DE/00BA` |
| 148 | 0 / 85 | `00F4` | 0/0 | 0 / 85 | `N(00F4)` | 0/0 | `01DE/00C5` |

### Right of center — arcade frame 2728

| Piece | Arcade rel X/Y | Arcade code | Arcade H/V | Native rel X/Y | Native tile | Native H/V | Final SAT X/Y |
|---:|---:|---:|---|---:|---|---|---:|
| 140 | 0 / 0 | `00F4` | 1/0 | 0 / 0 | `N(00F4)` | 1/0 | `01BB/0070` |
| 141 | -1 / 10 | `00F4` | 1/0 | -1 / 10 | `N(00F4)` | 1/0 | `01BA/007A` |
| 142 | -2 / 21 | `00F4` | 1/0 | -2 / 21 | `N(00F4)` | 1/0 | `01B9/0085` |
| 143 | -3 / 32 | `00F4` | 1/0 | -3 / 32 | `N(00F4)` | 1/0 | `01B8/0090` |
| 144 | -4 / 42 | `00F5` | 1/0 | -4 / 42 | `N(00F5)` | 1/0 | `01B7/009A` |
| 145 | -5 / 53 | `00F4` | 1/0 | -5 / 53 | `N(00F4)` | 1/0 | `01B6/00A5` |
| 146 | -6 / 64 | `00F4` | 1/0 | -6 / 64 | `N(00F4)` | 1/0 | `01B5/00B0` |
| 147 | -7 / 74 | `00F5` | 1/0 | -7 / 74 | `N(00F5)` | 1/0 | `01B4/00BA` |
| 148 | -9 / 85 | `00F6` | 1/0 | -9 / 85 | `N(00F6)` | 1/0 | `01B2/00C5` |

The native relative coordinates, logical tiles, and flip states are identical because Build 0364
uses the same retained mapping bytes and now selects the same normal/mirror transform as the arcade.
The finalizer independently maps PC090OJ semantic attr bit 14 to Genesis SAT H flip bit 11 and bit
15 to SAT V flip bit 12; it does not replace X mirroring with an attribute-only shortcut.

## Preservation and validation

- Build 0361 contact reconstruction and the `D00462` fix were not changed.
- Build 0362 animation-index-zero handling was not changed.
- Build 0363 visibility classification was not changed.
- No grab, release, jump-off, collision, tilemap, cave-platform, or palette code was changed.
- Canonical gate: PASS.
- GENESIS NTSC gameplay-entry gate: PASS, 240 required post-entry frames, zero address errors, bus
  errors, illegal instructions, or crash-handler entries.
- Seven-epoch automated gate: FAIL as before; the numbered ROM is preserved for evaluation.
- Standard 30-second trace: completed; it does not reach Segment 5.
- Required five-artifact set: PASS.

## Build artifacts

All artifacts are 1,719,992 bytes:

| Variant | SHA-256 |
|---|---|
| canonical | `60faefe8aca11173ea70fed0a42e95c09373bd171ff20bd0e335d9c674ab9411` |
| `_d` | `702226d4f46d7e2591bcc18a1f55f49cdc43adec62be7b62813d9387ddf1c0b9` |
| `_s` | `3666fc824372c9b67118b098627fc041a22d881b1601cee3d0a7968cd8fc234e` |
| `_do` | `71e21848199abddcf95d0e9dd58c7da0ffe78b98d800f6f20782127ab0873d5c` |
| `_c` | `418b8f9e9ea51ba52b724892d35133da8b91be7ee6b8bc05caa1f1fb8cf06202` |

Counter advanced `363 -> 364`.  The cave blocking-platform palette and collision contracts are
explicitly deferred to the next numbered build after Build 0364 user validation.

