# Cody — Build 0365 rope-grab contact-geometry regression

## Result and acceptance boundary

Build 0365 preserves Build 0364's user-accepted rope rendering and corrects the first divergent
gameplay value: Build 0364's visual compositor used the restored three-field mirror predicate, but
`genesistan_native_contact_coords_51ab6` still chose its X transform from `actor+0x02` alone.
The two paths therefore described different rope positions on the corrected side of the swing.

Build 0365 factors the original predicate into one assembly helper used by both consumers.  It adds
no rope identity, base `0x00F4`, Segment-5, fixed coordinate, hitbox, SAT collision, object-RAM
mirror/shadow, or fallback.  User BlastEm validation remains required before the grab/ride/release
regression is declared solved.

## Semantic cut

The retained boundary remains actor state plus the selected mapping program.  That state now fans
out through one mapping/mirror decision into:

```text
retained actor + mapping program
           |
           +-- shared three-field branch predicate -- visual queue -> Genesis SAT
           |
           +-- shared three-field branch predicate -- A5+0x1134 contact coordinates
```

The original PC090OJ object-record production/readback tail remains retired.  Build 0361's removal
of the invalid `D00462` access is unchanged.

## First 0363 -> 0364 divergence

The exact stale Build-0361 contact code was:

```text
if actor+0x02 == 0:
    X = actorX - signed_mapping_X - 16
else:
    X = actorX + signed_mapping_X
```

Build 0364 changed only the visual branch decision to the original arcade predicate:

```text
if actor+0x20 bit0 != 0:
    normal = actor+0x03 != 0 || actor+0x02 == 0
else:
    normal = actor+0x02 != 0
```

Thus Build 0363 had mutually consistent but visually incorrect geometry: visual and contact both
used the simplified `+0x02` decision.  Build 0364 corrected visual geometry but left contact geometry
on the old decision.  This is failure class **B: coordinates reconstructed incorrectly**.

## Representative retained state and mapping

The right-side nine-piece output uniquely resolves to the following program in canonical arcade
ROM (the complete nine-record Y/tile/X signature has one match):

| Field | Value |
|---|---:|
| Actor X | `0x013B` |
| Actor Y | `0xFFED` (-19) |
| `actor+0x20 bit0` | `1` |
| `actor+0x03` | nonzero (`1` in retained rope initialization/state) |
| `actor+0x02` | `0` on the divergent side |
| Animation index | `0x44` |
| Family-0 mapping program | arcade `0x3DBA8` (relocated native `0x3DDA8`) |
| Mapping branch, Build 0363 visual/contact | mirror / mirror |
| Mapping branch, Build 0364 visual/contact | normal / mirror — **mismatch** |
| Mapping branch, Build 0365 visual/contact | normal / normal |

Program `0x3DBA8` contains nine `0x80` records with signed X deltas
`0,-1,-2,-3,-4,-5,-6,-7,-9`, signed Y deltas `11,21,32,43,53,64,75,85,96`,
and tile deltas `0,0,0,0,1,0,0,1,2`.  The `0x80` control supplies H flip on the normal path.
There is no V flip.

## Exact A/B coordinate replay

These are the words produced by the actual Build-0363/0364 formulas from the retained state above.
Queue coordinates are the semantic coordinates passed by the visual producer.  Normal gameplay
sprite control is `1`, so final SAT is `X=(queueX+0x80)&0x1FF`,
`Y=(queueY-8+0x80)&0x1FF`.

### Build 0363

Both paths take the old mirror branch, explaining why grabbing worked even though the rope looked
wrong.

| Piece | Visual rel X/Y | H/V | Queue X/Y | SAT X/Y | Contact A5+0x1134 Y/X |
|---:|---:|---|---:|---:|---:|
| 0 | 0/0 | 1/0 | `012B/FFF8` | `01AB/0070` | `FFF8/012B` |
| 1 | +1/10 | 1/0 | `012C/0002` | `01AC/007A` | `0002/012C` |
| 2 | +2/21 | 1/0 | `012D/000D` | `01AD/0085` | `000D/012D` |
| 3 | +3/32 | 1/0 | `012E/0018` | `01AE/0090` | `0018/012E` |
| 4 | +4/42 | 1/0 | `012F/0022` | `01AF/009A` | `0022/012F` |
| 5 | +5/53 | 1/0 | `0130/002D` | `01B0/00A5` | `002D/0130` |
| 6 | +6/64 | 1/0 | `0131/0038` | `01B1/00B0` | `0038/0131` |
| 7 | +7/74 | 1/0 | `0132/0042` | `01B2/00BA` | `0042/0132` |
| 8 | +9/85 | 1/0 | `0134/004D` | `01B4/00C5` | `004D/0134` |

### Build 0364

The visual path takes the arcade normal branch, while contact still takes the old mirror branch.
The actual contact points therefore do not occupy the displayed rope positions.

| Piece | Visual rel X/Y | H/V | Queue X/Y | SAT X/Y | Contact A5+0x1134 Y/X |
|---:|---:|---|---:|---:|---:|
| 0 | 0/0 | 1/0 | `013B/FFF8` | `01BB/0070` | `FFF8/012B` |
| 1 | -1/10 | 1/0 | `013A/0002` | `01BA/007A` | `0002/012C` |
| 2 | -2/21 | 1/0 | `0139/000D` | `01B9/0085` | `000D/012D` |
| 3 | -3/32 | 1/0 | `0138/0018` | `01B8/0090` | `0018/012E` |
| 4 | -4/42 | 1/0 | `0137/0022` | `01B7/009A` | `0022/012F` |
| 5 | -5/53 | 1/0 | `0136/002D` | `01B6/00A5` | `002D/0130` |
| 6 | -6/64 | 1/0 | `0135/0038` | `01B5/00B0` | `0038/0131` |
| 7 | -7/74 | 1/0 | `0134/0042` | `01B4/00BA` | `0042/0132` |
| 8 | -9/85 | 1/0 | `0132/004D` | `01B2/00C5` | `004D/0134` |

The first piece is already 16 pixels apart (`0x013B` visible versus `0x012B` contact), and the two
chains proceed in opposite X directions.  This is the first behavioral divergence, before the
unchanged `0x51B04` hit test or attachment transition can succeed.

### Build 0365

Both paths call `.Lnative_mapping_branch_is_normal`.  Contact now writes exactly the visible queue
geometry:

| Piece | Visual queue X/Y | Contact A5+0x1134 Y/X | Match |
|---:|---:|---:|---|
| 0 | `013B/FFF8` | `FFF8/013B` | yes |
| 1 | `013A/0002` | `0002/013A` | yes |
| 2 | `0139/000D` | `000D/0139` | yes |
| 3 | `0138/0018` | `0018/0138` | yes |
| 4 | `0137/0022` | `0022/0137` | yes |
| 5 | `0136/002D` | `002D/0136` | yes |
| 6 | `0135/0038` | `0038/0135` | yes |
| 7 | `0134/0042` | `0042/0134` | yes |
| 8 | `0132/004D` | `004D/0132` | yes |

The contact path also now applies the mapping type-`0x70` extra-Y term only on the normal branch,
matching the visual/original compositor for the complete general contract.  This does not affect
the representative rope program, whose records are type `0x80`.

## Alternatives ruled out

| Candidate | Result |
|---|---|
| A. source no longer registered | Ruled out. Build 0364 did not modify `0x41BEE`, A5+0x1282 registration storage, actor fields, or the registration lifecycle. The user still saw the same live rope. |
| B. coordinates reconstructed incorrectly | **Confirmed.** Exact pairs above diverge at A5+0x1134 because contact retained the old predicate. |
| C. coordinates correct but `0x51B04` fails | Ruled out as the first divergence: coordinates are already wrong before unchanged `0x51B04`. |
| D. contact succeeds but attachment transition fails | Ruled out as the first divergence: the mismatched coordinate list prevents the preceding contact selection; no attachment-state code changed in 0364. |

The following were unchanged across the regression: retained actor mutation/update code,
`0x41BEE`, the three registration records, token format and token-to-actor decode, the nine-pair
count per registration, original `0x51B04`/`0x51B74`, and rope attachment/release state code.

A separate diagnostic ROM retaining Build-0363 contact behavior was unnecessary: Build 0364 itself
already was that diagnostic combination—corrected visual output plus unchanged Build-0363 contact
behavior—and the user result plus the exact pair divergence isolates the fault.  Build 0365 changes
the shared semantic decision rather than installing a temporary rope-specific test.

## Preservation and automated validation

- Build 0361 `D00462` PC090OJ-readback retirement: preserved.
- Build 0362 animation-index-zero acceptance: preserved.
- Build 0363 visibility classifier: preserved.
- Build 0364 visual normal/mirror transforms and output: preserved.
- Direct-native queue/SAT architecture: preserved.
- Canonical gate: PASS.
- GENESIS NTSC gameplay-entry gate: PASS, 240 post-entry frames, zero address errors, bus errors,
  illegal instructions, or crash-handler entries.
- Standard 30-second GENESIS NTSC trace: 1,798 frames, no unmapped-memory exception; it does not
  reach Segment 5.
- Seven-epoch gate: remains FAIL; numbered artifact preserved for evaluation.
- Five-artifact set verification: PASS.

## Build artifacts

All artifacts are 1,719,992 bytes:

| Variant | SHA-256 |
|---|---|
| canonical | `b26da903cb851ec24764d18fe020de912712f34a79ae60bc7c6ca914f7208eb6` |
| `_d` | `e41af2e0e9650c17a87d7e04013746cd88ad1edf8b69f8851b3c193a50bd8880` |
| `_s` | `10046d2ebf2c6f359beb7d1f314ef534cb6e9a0b05f9c4e9ba8c69355b066a0e` |
| `_do` | `35da5923b4663be103569bb90464d4ed13f2a20211d017d964d0a8ea2b3875d6` |
| `_c` | `7418cf4012750ca5aeccbd62fc0c62941dd7c1f281bfaedc45d5869698c782fd` |

Counter advanced `364 -> 365`.  Cave-platform work remains stopped pending Tighe's BlastEm result
for visual direction, grab, ride, jump/release, and continued absence of the `D00462` crash.

