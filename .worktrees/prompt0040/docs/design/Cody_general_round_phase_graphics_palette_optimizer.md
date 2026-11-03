# Cody - General Round / Scene / Phase Graphics Analyzer + Optimizer

**Task type:** infrastructure / static reverse engineering / graphics compiler analysis  
**Validation scope:** original arcade Round 1, Phase 1, scene 1  
**Production source changed:** NO  
**ROM/build produced:** NO  
**Build counter:** 313 (unchanged)

## Outcome

A reusable original-arcade graphics analyzer now exists under
`tools/graphics_optimizer/`. It generates a machine-readable graphics/color/pattern
dataset and an HTML viewer for a requested round/phase/scene. The first generated
dataset is:

`analysis/graphics_optimizer/round1_phase1/`

The tooling is deliberately fail-closed. Round-1 Phase-1 sprite semantic discovery
currently records a 23-row conservative discovered-route ledger, partitioned exactly
into 4 resolved classes and 19 explicitly unresolved classes. Several unresolved rows
are still route-level or producer-category buckets, so this is **not** claimed as a
complete enumeration of every legal arcade class. Those unresolved classes are included
as feasibility blockers; they are never treated as zero-cost. Consequently:

- the analyzer machinery is usable and repeatable;
- the tile-plane inventories are complete for the selected scope;
- only proven sprite palette relationships contribute colored data;
- the Round-1 Phase-1 sprite corpus is **not** semantically closed;
- neither the palette model nor the sprite VRAM model is production-ready;
- candidate asset emission is blocked.

This distinction preserves the required invariant without claiming that the known
Lizardman/bat vocabulary is the complete legal sprite superset.

## Phase 0

- **Classification:** INFRASTRUCTURE, extending existing palette and native graphics
  findings.
- **Relevant priors:** the native PC080SN/PC090OJ replacement policy, Build-0313
  residency evidence, prior original-arcade sprite provenance, and Andy's partial
  Round-1 Phase-1 color audit.
- **Rediscovery hazards:** original arcade data remains authoritative; generated
  assets must not depend on Genesis CRAM, screenshots, videos, or playthrough traces;
  unknown palette banks must not be guessed.
- **Open/closed issues touched:** existing graphics/palette/residency work only; no
  issue was opened or closed.
- **Contradiction of a confirmed/strong finding:** NONE. The new result corrects the
  partial sprite inventory and explicitly preserves unknown bat palettes.

## Source Authority

Generated analysis inputs are only:

| Input | SHA-256 |
|---|---|
| `build/regions/maincpu.bin` | `4f30b9e7aa946aa33d20e125a1726ff094f9615980107d0842efe1721cf32063` |
| `build/regions/pc080sn.bin` | `a33372eb4f768136cbb5311125e65da7587d31bb1d91a72d32775d22eb44059b` |
| `build/regions/pc090oj.bin` | `080e341433333164b00f4c2230cf2810ebf6082910b18018808f922eb7c0e2d9` |

Original-arcade MAME traces are cited only to prove dynamic semantics. Deleting those
traces does not change generated assets. Genesis data is not an analyzer input.

## General Data Model

The analyzer accepts `--round`, `--phase`, `--scene`, and a palette-policy ID. Its
generated model separates:

- game scope and semantic records/segments;
- graphics owner (`sprites`, `plane_a`, `plane_b`);
- logical use versus physical pattern identity;
- original palette bank and xBGR-555 color;
- exact Genesis quantization;
- semantic liveness/coexistence state;
- class, graphics, and palette resolution independently;
- exact, near-color, pattern, and VRAM feasibility results.

Unknown sprite palette candidates are metadata only. They do not become color data.

## Original Arcade Sprite Semantic Domain

### Producer chain

The reusable sprite model records this original-arcade chain:

1. Map/collision publication: `arcade_pc 0x0559B2` (`FUN_000559B2`).
2. Spawn/class selection: `arcade_pc 0x041180`
   (`actor_spawn_ground_and_activate_41180`).
3. Record loading: `arcade_pc 0x04543E` (`actor_record_loader_4543e`),
   using the 8-byte table at `arcade_rom/data 0x045592`.
4. Palette attribute: `arcade_pc 0x045684` writes actor byte `+0x27`.
5. Family dispatch: `arcade_pc 0x03D054`, with family descriptor tables at
   `arcade_rom/data 0x03D09E`, `0x04771C`, `0x03F0CE`, `0x040004`, and
   `0x04002C`.
6. Default pieces: `[control, signed_y, code_offset, signed_x]` quartets,
   terminated by zero control.
7. Effective palette bank:
   `((sprite_ctrl & 0xE0) >> 1) | (actor_attr & 0x0F)`.

### Phase-local map routes

The analyzer reconstructs collision words from the same original descriptors that
provide Plane-A visual words. Round-1 Phase-1 contains these map-driven routes:

| Marker | Cells | Collision words | Classification |
|---|---:|---|---|
| `0x40` | 1 | `0x4000` | explicit unresolved route |
| `0x41` | 5 | `0x4100` | explicit unresolved route |
| `0x48` | 2 | `0x4800` | family 0, class `0x70`, behavior `0x1E` |
| `0x49` | 2 | `0x4901`, `0x497E` | special calls through `0x03A2D0` / `0x04092E`; unresolved |
| `0x4F` | 2 | `0x4F00` | `0x041C1E` / `0x041C60` / `0x041BEE`, behavior `0x20`; unresolved |

The decoded actor-record table rows 8 through 12 are also represented separately:

| Record | Base | Family | Class | Resolution |
|---:|---:|---:|---:|---|
| 8 | `0x0129` | 2 | `0x30` | unresolved |
| 9 | `0x02AF` | 1 | `0x57` | unresolved |
| 10 | `0x03F6` | 1 | `0xB6` | unresolved |
| 11 | `0x0268` | 1 | `0xB9` | unresolved |
| 12 | `0x050B` | 1 | `0xBC` | unresolved |

The generated `arcade_object_semantic_domain.json` verifies that every currently decoded
marker and record row has a declared class ID. That route-coverage proof is distinct from
complete class enumeration: the latter remains false while route-level/category buckets
have not been expanded through state, animation, composer, pieces, and palette.

### Legal class partition

The current conservative ledger has **23** rows:

**Resolved (4):**

- Rastan player BODY;
- Stage-1 Lizardman;
- sword/player auxiliary;
- gameplay HUD/status sprites.

**Explicitly unresolved (19):**

- map-marker routes `0x40`, `0x41`, `0x49`, and `0x4F`;
- family-0 class `0x70` actor identity;
- family-2 Round-1 actor cluster identity;
- actor-record rows 8, 9, 10, 11, and 12;
- Hurry-up Bat palette;
- normal/small bat;
- large bat;
- four-armed enemy;
- Axe item/drop;
- other item/drop classes;
- other projectile/weapon classes;
- transient effect classes.

The original-arcade dispatch proof records 17 live family/class pairs: family 0
classes `0x17`, `0x18`, `0x19`, `0x1C..0x1F`, `0x70`, and family 2 classes
`0x0B..0x13`. The family-0 Lizardman states are resolved as one proven semantic
producer. The unnamed family-0/class-`0x70` and family-2 groups remain separate
blockers despite their proven art/palette observations.

The complete machine-readable partition is
`sprite_class_coverage.json`. It proves:

- legal domain equals resolved plus explicitly unresolved: **YES**;
- all decoded marker/record routes occur in the legal domain: **YES**;
- complete legal graphics-bearing class enumeration: **NO**;
- semantic resolution complete: **NO**;
- optimization closed: **NO**.

## Bat Palette Correction

The Hurry-up Bat art codes `0x0268..0x026A` and death art `0x0276` are known, but
the object palette nibble is not. Its legal Round-1 effective-bank range remains
`0x30..0x3F`.

Therefore:

- the sprite contact sheet renders Hurry-up Bat art in grayscale;
- every bat row is labeled `PALETTE UNKNOWN; NEUTRAL RENDER`;
- no candidate bank is selected;
- no bat colors enter `colors.json` or `color_usage.json`;
- no bat colors enter coexistence pressure or the two-sprite-line solver;
- no guessed bat mapping is written to `specs/palette_decisions.json`.

This same rule applies to every non-proven object-to-palette relationship. Validation
found zero non-proven family IDs in the colored sprite records.

## Palette Decoder

Static source reconstruction resolves:

- scene records at `arcade_rom/data 0x03BA88`, stride 32;
- palette pool at `arcade_rom/data 0x04FD02`;
- staging at arcade work RAM `a5+0x1600`;
- producer `arcade_pc 0x03BA20`;
- low-bank publisher `arcade_pc 0x045D7C`, banks `0..31`;
- sprite-bank publisher `arcade_pc 0x045DC4`, banks `48..79`.

For Round 1, `sprite_ctrl=0x0060`; therefore effective sprite banks are only
`0x30..0x3F`. Banks `0x40..0x7F` cannot be selected in this scope. Colored sprite
data currently uses only proven relationships to `0x30`, `0x33`, and `0x36`.

## Round-1 Phase-1 Results

### Plane A

- logical pattern/palette uses: **1,581**;
- exact physical patterns: **1,315**;
- exact dedup savings: **266**;
- flip-equivalent candidates: **69** (not automatically applied);
- palette banks: `0x003`, `0x004`, `0x005`, `0x006`, `0x007`, `0x017`,
  `0x018`, `0x01A`, `0x01B`, `0x01C`, `0x01D`;
- source colors: **85**;
- Genesis-quantized colors: **64**;
- semantic epoch maximum: **483 patterns** against capacity **484**.

All seven current Plane-A semantic epochs fit individually. The global vocabulary is
not simultaneous.

### Plane B

- logical uses / physical patterns: **854 / 854**;
- palette bank: `0x002`;
- palette-state events: **16**;
- distinct phase-local state: **1**;
- source and Genesis-quantized colors: **15**;
- fixed capacity: **854**, exact fit.

### Sprites

- class rows: **23**;
- generated frame/composite records: **11**;
- known source cells: **80**;
- known exact cells: **72**;
- known 8x8 pattern lower bound: **288**;
- current native sprite capacity: **196 8x8 patterns**;
- semantic coverage complete: **NO**.

The known lower bound already exceeds the current sprite allocation by 92 patterns.
Unresolved classes can only increase pressure; they are not treated as empty.

## Exact Color Optimization

Policy `2sprite-1b-1a` provides 15 nontransparent entries per line:

- sprites: 2 lines / 30 entries;
- Plane B: 1 line / 15 entries;
- Plane A: 1 line / 15 entries.

Known exact pressure is:

| Owner | Exact Genesis colors | Capacity | Deficit |
|---|---:|---:|---:|
| Sprites | 32 | 30 | 2 |
| Plane A fixed union | 64 | 15 | 49 |
| Plane B | 15 | 15 | 0 |

Every current semantic epoch also fails the exact one-line Plane-A color constraint
(23 to 53 exact colors per epoch). Because sprite coverage is incomplete, the final
exact verdict remains fail-closed regardless of these known-subset deficits.

- fixed exact feasibility: **FAIL**;
- semantic-state exact feasibility: **FAIL**;
- exact assets emitted: **NO**;
- dry-run manifest status: `dry-run-blocked`.

## Near-Color and Reuse Analysis

Near colors are advisory only; no approximate merge is implemented or emitted.

| CIEDE2000 threshold | Candidate pairs |
|---:|---:|
| 1 | 0 |
| 2 | 0 |
| 3 | 4 |
| 5 | 13 |
| 8 | 59 |

Exact reuse diagnostics:

- exact source colors shared by multiple proven sprite families: **16**;
- arcade color groups collapsing to one Genesis value: **16**;
- sprite/Plane-A exact reuse: **37**;
- sprite/Plane-B exact reuse: **4**;
- Plane-A/Plane-B exact reuse: **4**;
- exact colors shared by all three owners: **4**.

These values are decision support, not authorization to change palette ownership.

## Outputs

Primary viewer:

`analysis/graphics_optimizer/round1_phase1/index.html`

Key machine-readable outputs:

- `scope.json`
- `arcade_object_semantic_domain.json`
- `sprite_class_coverage.json`
- `sprite_families.json`
- `sprite_frames.json`
- `plane_a_uses.json`
- `plane_b_uses.json`
- `palette_states.json`
- `colors.json`
- `near_color_clusters.json`
- `coexistence_graph.json`
- `semantic_states.json`
- `pattern_inventory.json`
- `pattern_equivalence.json`
- `optimization/policy_2sprite_1b_1a_exact.json`
- `candidate_assets/manifest.json`

Contact sheets:

- `sprites/contact_sheet.png`
- `plane_a/contact_sheet.png`
- `plane_b/contact_sheet.png`
- `plane_b/state_00.png`

## Reusable Tooling

- `tools/graphics_optimizer/analyze_graphics.py`: scope decoder, semantic-domain
  checker, sprite/tile/palette decoder, contact-sheet renderer, exact/near-color
  analysis, coexistence solver, and pattern/VRAM analysis.
- `tools/graphics_optimizer/scope_manifest.json`: declarative semantic and target
  policy input.
- `tools/translation/reindex_graphics_for_palette.py`: existing exact-only dry-run
  reindexer, cited by the candidate manifest; not wired into production.

Example:

```bash
python3 tools/graphics_optimizer/analyze_graphics.py \
  --round 1 --phase 1 --scene 1 \
  --output analysis/graphics_optimizer/round1_phase1
```

## Validation

Executed successfully:

```bash
python3 -m json.tool tools/graphics_optimizer/scope_manifest.json
python3 -m py_compile tools/graphics_optimizer/analyze_graphics.py
python3 tools/graphics_optimizer/analyze_graphics.py \
  --round 1 --phase 1 --scene 1 \
  --output analysis/graphics_optimizer/round1_phase1
```

Additional checks proved:

- legal class partition exact: YES;
- decoded marker/record routes represented: YES;
- complete legal class enumeration: NO (fail-closed blocker);
- non-proven palette families in colored data: ZERO;
- Hurry-up Bat contact-sheet rendering: grayscale/neutral;
- candidate asset bytes emitted: NO;
- production source/spec/remap changed: NO;
- `specs/palette_decisions.json` changed: NO;
- ROM/build/counter changed: NO.

## Next Production Boundary

No production palette model should be approved from this dataset yet. The next
graphics-compiler work must resolve the explicit sprite blockers from original arcade
state/class semantics through animation, composer, pieces, and palette nibble, then
rerun the same analyzer. In particular, the bat palette nibble must be proven before
any colored bat asset or solver input is legal.

Once semantic coverage is complete, the measured exact color and pattern deficits can
drive a Tighe-approved epoch/variant/residency design. Until then, the correct
recommendation is **no production graphics package**.

## Architecture Compliance

This task adds offline analysis only. It does not add a PC080SN/PC090OJ software
device, shadow/projection path, runtime renderer, remap, or ROM behavior. It consumes
original arcade ROM semantics and prepares evidence for a future native Genesis
realization at a separately approved semantic cut.
