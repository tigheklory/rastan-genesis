# Round 1 rendering, Palette Composer coverage, and sprite-integrity audit

Identifier: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0045`
Author: Cody
Reference ROM: Build 0525
Scope: read-only investigation and implementation planning; R1-S1, R1-S2, and R1-S3 only
Status: no source, specification, profile, asset, tool, test, build output, ROM, or counter changed

## Executive conclusion

The R1-S2 Plane A defect is not a missing-pattern or palette failure. The first actionable finding is a
split in the current publication architecture:

1. scene/checkpoint reconstruction replays the retained producer across the complete ring;
2. selector-1 records 17 and 21 use an offline `pan_row_maps.bin` row;
3. the intervening records 18, 19, and 20 are selector 0 and use the live dynamic resolver.

That path sequence is an unusually close match for Tighe's observation: correct initialization/respawn,
displacement during the middle vertical traversal, and realignment near the end. It is the leading
root-cause hypothesis, not yet a proven first bad cell, because no existing runtime capture reaches the
natural 17 -> 18 -> 19 -> 20 -> 21 progression. The maintained verification explicitly stopped in record
17. It also compares the Genesis selector-1 result to a product of the same compiler model, which proves
internal consistency but not an independently rendered arcade coordinate.

The narrow next P0 task is therefore a synchronized original-arcade/Genesis capture at the last correct
frame and first wrong frame, with the current record and selector recorded. If the first divergence is at
17 -> 18, the dynamic selector-0 middle path is isolated. If it occurs while still in record 17, the
compiler's selector-1 axis transform/origin is wrong despite its self-consistency gate.

Palette Composer coverage is materially incomplete for the requested scope. `Test.json` exposes only two
contexts: R1-S1 and R1-S2 Plane A. R1-S3 Plane A already has a 219-usage source corpus (banks `$008` and
`$019`) but no authoring context or production realization. Plane B is deliberately absent from the
Composer and Line 2 is protected as arcade-owned. R1-S2 sprite coverage is only `SCHEDULE_ONLY`; the UI
warns that the shown R1/P1 sprite vocabulary is not the castle roster. The manifest proves armored bases
`$0A73/$0A5A`, but they are not registered as complete R1-S2 authoring objects. Wizard identity and the
marker-driven vocabulary remain unresolved. The R1 boss body/composite data exist (body `$061D`), but the
R1-S3 sprite scene is not a complete Composer context.

The intermittent armored-man corruption is downstream of gameplay logic: the actor remains active,
collidable, damaging, and killable. The leading presentation hypothesis is bounded native resource
truncation. The current finalizer silently skips pieces when its 12-entry per-frame tile-DMA worklist is
full, when 49 resident cells are exhausted, or after the 80-entry SAT limit; the back-enemy lane itself is
large enough (99 pieces). Two instances in different animation/orientation states can therefore behave
differently when one instance's patterns are already resident and the other's are not. This is not yet
proven. The existing `pc090oj_dropped_count`, `pc090oj_tile_dma_count`, semantic queues, actor records,
shadow SAT, actual VDP SAT, residency table, and generated frame tables are sufficient for the next
capture; no new sprite architecture is required to diagnose it.

## Evidence and method

### Governing boundary

This audit follows `RULES.md` and
`docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`. For future graphics work the required cuts
are:

- **P0 PC080SN cut:** retained arcade decision to publish an entering logical row or column, using the
  live selector, descriptor chain, and camera state, directly to final Genesis Plane A words. Retire the
  complete PC080SN row/column chip-address tail below that decision. Do not add name-RAM shadows, full-map
  projections, tall buffers, or generic chip-address translation.
- **P2 PC090OJ cut:** retained actor/piece-compositor decision (actor state, position, selected frame,
  palette, flips, and order) directly to final native SAT pieces. Retire the PC090OJ object-record tail.
  Do not reintroduce an object-RAM mirror or a chip-record decoder.

### Existing project tools reused

- Canonical Ghidra exports under `analysis/ghidra/rastan_arcade/exports/`, especially the call graph,
  xrefs, hardware references, and listing for `$055696/$05572E/$0558C6/$055904/$055A14`.
- `build/maincpu.disasm.txt` and `build/regions/maincpu.bin` for original record selectors and camera
  tuples.
- Existing reports and captures from PROMT-ID-0012, 0022, 0042, 0043, and 0044.
- Current generated PC080SN boundary artifacts and reports under `build/pc080sn_boundary/`.
- Current PC090OJ frame coverage, semantic profile, and actor graphics manifest.
- Existing Palette Composer corpus, profile, subround map, scene-coverage report, and canonical
  `specs/palette_decisions.json` registry.

New tooling created: **none**.
Why new tooling was necessary: **not applicable**.

Andy's currently available `docs/design/Andy_stripe_root_cause_build0046.md` describes an old staging
buffer/warm-restart architecture and does not contain PROMT-ID-0046's concurrent Round 1 research. It was
not treated as evidence for Build 0525. No current PROMT-ID-0046 report was available to coordinate.

### Screenshot evidence and limitations

The images were supplied in the conversation and have no repository path or persistent filename. To
reference them exactly without inventing filenames, this report uses these labels:

- **Tighe screenshot A — armored-man comparison:** the R1-S2 frame described in the assignment with two
  armored men simultaneously visible. The walking-away instance is complete; the other has only subsets
  of its graphics extending downward into the visually empty area below the floor. The corrupt instance
  remains active, damages Rastan, and can be killed by crouching and attacking.
- **Tighe screenshot series B — R1-S2 castle traversal:** the supplied 320x232 castle frames showing the
  player at different vertical positions, masonry, barred openings/windows, flame stands, floors, and
  door/opening landmarks.
- **Tighe screenshot series C — original arcade progression:** the supplied 320x232 original-Rastan
  sequence covering the outdoor/castle progression and its fixed architectural landmarks.
- **Tighe map images D:** the supplied 512x512 source/map images used as structural context, not as a
  direct screen-space oracle.

Screenshot A is authoritative for the *simultaneous good/bad instance* constraint. Series B/C prove a
visible placement discrepancy and supply landmarks, but the available images do not carry matched
camera words, record numbers, scroll values, or frame identities. Their camera and animation frames are
not guaranteed to match. A pixel-perfect overlay would therefore be fabricated. The valid comparison is
landmark order and world alignment; the exact first bad logical cell requires the capture specified
below.

## P0 — R1-S2 Plane A placement throughout vertical scrolling

### Observed symptom

Tighe confirms that Build 0525 has the correct Plane A artwork, correct checkpoint scenery, and correct
initial population. When vertical traversal begins and progresses, masonry/windows/platforms occupy
wrong positions. Near the end, the layout realigns. This overrides the earlier internal PASS claims.

### Current producer paths

`apps/rastan-direct/src/tilemap_hooks.s` currently contains three materially different paths:

- `genesistan_plane_a_scene_scroll_reseed_native` replays the saved fill selector from `A5+$132C` over
  all 64 strips after rewinding the 16 descriptor source pointers. This is why Build 0525 can initialize
  and respawn correctly.
- `genesistan_hook_tilemap_plane_a_selector12_native` implements the original selector-1 reverse
  destination row (`63-(group*4+strip)`) and selector-2 forward row.
- `.Lplane_a_publish_logical_row_native`, used by the camera pan hooks, does **not** always use that live
  producer. If the live selector is nonzero and `A5+$013E` has a compiled map, it copies a 64-word row
  from `genesistan_plane_a_pan_row_maps`. Otherwise it falls back to the selector-0 dynamic resolver.

The original arcade evidence supports the distinction. Ghidra's call graph shows `$055650` dispatching
to `$055696` and `$05572E`; the listing at `$055696` builds the reverse PC080SN destination from
`$3F00-(group*$400+strip*$100)`, while `$055904` rebuilds the parallel attribute and resolved pointer
tables. These are semantic inputs, not interchangeable chip-address formulas.

The original record stream is:

| R1-S2 record | selector | current Genesis incremental row path | existing runtime proof |
|---:|---:|---|---|
| 16 | 0 | full scene replay at entry | initial window only |
| 17 | 1 | precompiled selector-1 `pan_row_maps` | first seven entered rows only |
| 18 | 0 | dynamic live resolver | not naturally reached by maintained capture |
| 19 | 0 | dynamic live resolver | not naturally reached |
| 20 | 0 | dynamic live resolver | not naturally reached |
| 21 | 1 | precompiled selector-1 `pan_row_maps` | offline proof only; no natural runtime capture |

The camera tuples also change across these records; the middle is not merely one static map viewed
through a changing VSRAM offset. Existing PROMT-ID-0012/0022 reports explicitly say the bounded route
never reached records 18–21.

### Why the prior zero-mismatch gate is insufficient

`tools/mame/verify_r1s2_selector1_scroll.py` selects the current record's row from
`pan_row_maps.bin`, then compares that compiler product to Genesis staging/VRAM. The generation and the
offline gate both use the same reconstructed record model. That proves:

- the selected compiled row reached staging;
- staging reached VDP VRAM;
- resident pattern bytes agree with the chosen native slots.

It does **not** independently prove that the compiler assigned the original arcade world cell to the
same logical row/column, nor does it cover the natural selector transitions through records 18–20.

### Leading explanation for “correct, wrong, correct”

The best-supported answer is:

- **Correct at respawn:** the bounded full-ring replay uses the retained scene/checkpoint descriptor and
  final camera state.
- **Wrong during traversal:** incremental publication changes source-selection rules. The likely first
  divergence is the selector-1-to-selector-0 transition into record 18, after which the dynamic row
  resolver interprets the current front/descriptor phase differently from the original vertical
  producer. A second possibility is that the compiled selector-1 row transform is itself phase-shifted;
  the current gate would reproduce that same mistake.
- **Correct near the end:** record 21 returns to selector 1 and therefore returns to the independent
  precompiled selector-1 row path. That can make the displacement disappear without correcting any
  already-wrong middle-path formula.

The path sequence and missing runtime coverage are proven. The exact bad formula and first bad cell are
not proven without a matched transition capture.

### Hypotheses ranked

1. **Record 18–20 dynamic-path source/front phase differs from original selector semantics — high.** It
   exactly matches the path sequence and the untested interval. Check `plane_a_src_ref_block`,
   `A5+$10CA/$10CC`, live source pointers at `$FF1000`, and the seam rule when the record advances.
2. **Selector-1 compiled logical origin/axis transform is wrong — medium.** The compiler transforms
   selector 1 with `destination_row=(15-descriptor_column)*4+descriptor_row` and swaps the other axis.
   The gate is not independent, so a shared phase error remains possible. Realignment at record 21 is
   weaker evidence for this hypothesis.
3. **Logical-to-physical ring projection or VSRAM timing — medium/low.** The physical rule
   `logical&31` is internally consistent and staging-to-VRAM checks passed at reached states, but a
   one-frame mismatch between the scroll committed in VBlank and the row selected in the main loop must
   be captured at the first crossing before it can be excluded globally.
4. **Missing artwork/palette/residency — rejected as the primary defect.** Tighe sees the correct tile
   graphics in wrong places, and prior captures showed resident pattern bytes matching their staged
   names.

### Exact next diagnostic and first-divergence test

Use the existing original-arcade MAME and Genesis NTSC MAME harnesses. Do not add a new map oracle.
Capture the last visually correct frame and every frame until the first visible mismatch, including the
17 -> 18 and 20 -> 21 boundaries. For both machines record:

- `A5+$013E` progression record, selector `$10A8`, strip group/index `$10CC/$10CA`;
- live Plane A Y `$10B0`, delta/accumulator, Plane A X, and the final VSRAM values actually displayed;
- 16 live descriptor source pointers and rebuilt pointer/attribute tables (`$FF1000/$FF1040/$FF1080`
  on Genesis and their original arcade counterparts);
- original PC080SN Plane A names for the entering row/column and the 32-row visible window;
- Genesis `staged_fg_buffer`, dirty masks, VDP Plane A names, active LUT, and referenced VRAM patterns;
- screenshot plus one landmark coordinate list (floor edge, doorway/window corner, flame stand).

Normalize both outputs to `(world logical row, world logical column, raw arcade code, arcade attribute,
final Genesis word, physical row/column)`. Find the first cell where the original producer and Genesis
producer choose different world coordinates. The record/selector at that cell decides the repair:

- record 17: repair selector-1 logical source/origin;
- 17 -> 18 or records 18–20: repair transition/dynamic source-front phase;
- identical staging but different display: repair physical projection/scroll publication timing.

### Future implementation direction and acceptance

Replace the split incremental source rules with one semantic producer contract at the cut stated above:
the retained selector/descriptor/camera decision supplies the entering logical row/column and a native
helper emits final Plane A words. Remove the corresponding chip-address tail. Do not “fix” this by
adding another scene image or a coordinate exception.

Acceptance requires natural forward and reverse traversal through 16–21, all ring wraps, checkpoint
respawn, and matched arcade landmarks at multiple camera positions. It also requires unchanged R1-S1
checkpoint behavior, collision words, pattern residency, and VBlank publication bounds. A compiler-only
PASS is not acceptance.

## P1 — Palette Composer coverage for R1-S2 and R1-S3

### Current contexts and available Plane data

`analysis/graphics_optimizer/editor_policy/Test.json` has exactly two `context_policies`:

| context | present authoring | current count |
|---|---|---:|
| `context:gameplay.r01.p01` | R1-S1 Plane A plus shared sprite policy | 1,576 Plane A mappings |
| `PAL-R1-S2-PLANEA-CASTLE` | R1-S2 Plane A | 517 Plane A mappings |

The R1-S2 corpus itself has 520 usages across records 16–21 and 15 source banks (`$003`, `$008..$014`,
`$01F`). The difference between 520 corpus uses and 517 authored entries must be reviewed as individual
usage IDs; it must not be silently filled by a scene-wide guess.

R1-S3 source data are already partly available:

- `analysis/graphics_optimizer/subround_corpus/PAL-R1-S3-PLANEA-BOSS/plane_a_uses.json` contains 219
  usages/unique codes for record 22;
- its source banks are `$008` and `$019`;
- the native PC080SN compiler can decode both Plane A and Plane B record-22 graphics and already emits
  scene/map artifacts;
- no R1-S3 context exists in `Test.json`, and `AuthoredLayerA.SCENES` only realizes records 0–15 and
  16–21. Record 22 therefore falls back to unauthored/raw behavior.

Plane B has no Composer authoring path. `specs/palette_subround_map.json` declares `PLANEB` nonauthorable,
and the UI protects Genesis Line 2. Current runtime policy intentionally leaves Line 2 to the arcade
Plane-B palette producer. Thus “add R1-S3 Plane B” is not merely another Plane A context: a later task
must first expose a scene-scoped original Plane-B corpus and decision surface while preserving Line-2
ownership. Unlocking Line 2 or copying Plane A colors into it would violate the current contract.

### R1-S2 sprite inventory gap

The generated scene coverage currently says:

- status `SCHEDULE_ONLY`;
- roster `$033E` family-2 spawner variants (compositors 0/3/4);
- complete per-scene cell vocabulary not captured;
- displayed R1/P1 sprite vocabulary is explicitly not a substitute.

The corrected actor evidence proves the earlier `$0224/$00F4` R1-S2 attribution was wrong. Those bases
retire before R1-S2 materialization. The only current scene-tagged R1-S2 Composer item is marker `M`'s
five-child burst, and it is honestly marked incomplete with zero fabricated pieces.

Armored men are now identifiable in the actor manifest as bases `$0A73` and `$0A5A`, compositor 2, in
R1 castle presence. That evidence is newer and stronger than the old provisional roster, but the
Palette Composer does not expose a complete, scene-tagged R1-S2 animation vocabulary for them. The
generated death table covers `$0A73` selectors `$0B..$12` and `$0A5A` reward selectors `$13..$23`; that
is not by itself proof of every live armored-man walking/attack frame.

Wizard identity remains unresolved in the available static scene roster. It must be derived from the
now-maintained marker/collision chain (`$0502CC` population, marker grid production, materialization
dispatch, final base/compositor/palette selection) or an original-arcade actor sweep. No sprite should be
named “wizard” merely because it resembles one in a screenshot.

### R1-S3 sprite inventory gap

The actor manifest and enemy lexicon already contain the Round-1 boss body/composite source:

- body base `$061D`, record type `$0E`, compositor 1;
- auxiliary/type-15 pieces and a 17-piece observed boss composite;
- embedded compositor palette line `$F` is proven, while the exact scene color source/authoring remains
  partial in the existing boss-palette evidence.

None of that is registered as a complete `PAL-R1-S3-PC090OJ` editing context in `Test.json`. The current
scene coverage reports R1-S3 as `PENDING` and an empty roster. Boss body, auxiliary actors/projectiles,
effects, Rastan/weapons, HUD, and any scene-specific shared assets must be enumerated deliberately.

### Sharing without duplication

Reuse physical pattern identities and one object mapping where provenance is the same:

- Rastan body, weapons, HUD, common effects, reward/death assets, and any armored frame whose exact
  `(base, compositor, selector, orientation, effective bank, piece stream)` matches an existing object;
- R1-S3 Plane A tiles whose raw 32-byte pattern and source palette usage already exist elsewhere;
- boss pieces shared across boss substates only when the generated semantic key and source palette
  identity match.

Scene membership and palette decisions must remain separate even when pattern bytes are shared. A
shared physical tile is not permission to share a palette mapping across `$008`, `$019`, or a sprite
bank without evidence. Every palette-decision change must update `specs/palette_decisions.json` and cite
the affected decision IDs; no Markdown registry should duplicate it.

### Bounded later implementation plan

1. **Freeze a new editable profile derived from Test, with a unique profile ID.** Do not edit or
   overwrite `Test.json` while inventory and authoring are incomplete. Add profile-manifest metadata and
   preserve all existing context policies verbatim.
2. **Close the R1-S2 actor roster from original data.** Enumerate the marker set for records 16–21,
   follow each materialized actor to final base/compositor/selectors/effective banks, and reconcile it
   with the existing whole-game sweep. Explicitly close `$0A73/$0A5A` armored men and the actors Tighe
   calls wizards. Keep unresolved names technical.
3. **Register complete R1-S2 sprite objects additively.** Scene-tag each usage
   `PAL-R1-S2-PC090OJ`, include every legal frame and per-piece palette identity, and retain the existing
   incomplete marker-M entry until its children are proven. Verify no R1-S1 field enemy leaks into the
   castle filter.
4. **Add R1-S3 Plane A context.** Register the existing 219-use corpus and banks `$008/$019`; make the
   compiler consume record 22 only after all uses have explicit authored or intentionally provisional
   decisions.
5. **Design R1-S3 Plane B authoring as its own context.** First generate a source corpus from the
   original Plane-B descriptor/palette producer for record 22. Add a `PAL-R1-S3-PLANEB-BOSS` decision
   surface that previews original colors and final Line-2 output, but does not weaken Line-2 protection.
   Production export must remain a scene-bound native Line-2 asset/producer decision, not a general
   editable global line.
6. **Add R1-S3 sprite context.** Register the `$061D` boss composite and proven auxiliaries, then shared
   player/weapon/effect assets. Resolve the original boss palette source before authoring colors; do not
   substitute the field pool or screenshot sampling.
7. **Verify persistence and isolation.** Save/reload the new profile, compare hashes of `Test.json`, and
   prove R1-S1/R1-S2 contexts unchanged. Only after Tighe approves the authored profile should a separate
   production task deliberately select or merge it.

Acceptance is a Composer inventory report with zero unexplained live actors/usages, correct source-bank
previews, independent per-context save/reload, and original-arcade screenshots/captures for R1-S2 and
R1-S3. Incorrect current R1-S3 colors are expected because authoring is absent; they are not evidence of
a failed existing decision.

## P2 — intermittent R1-S2 armored-man corruption

### What Screenshot A establishes

The same frame contains one complete armored man and one corrupted armored man. The corrupt actor's
gameplay behavior survives. Therefore:

- collision/AI and actor lifetime are not globally lost;
- the PC090OJ source ROM is not globally corrupt;
- a universally wrong armored base, palette, or pattern mapping is unlikely;
- per-instance state/frame/orientation, queue order, residency pressure, or final SAT realization are
  the productive boundaries.

### Relevant current native path

`native_stage_dispatch_45dfa_retained_cut` walks six back-enemy actors at `A5+$05C8`, permits 10 or 20
pieces per actor, and calls `.Lnative_emit_actor_common`. Generated frame selection validates retained
base, discriminator, compositor, selector interval, attribute policy, effective bank, and orientation.
Pieces enter `native_queue_back_enemy`; the shared finalizer resolves patterns and writes SAT entries.

Important bounds and behavior in `apps/rastan-direct/src/pc090oj_hooks.s`:

- back-enemy semantic queue: 99 pieces;
- total Genesis SAT: 80 entries;
- resident sprite cells: 49;
- per-frame tile-DMA worklist: 12 cells;
- a full residency set or DMA worklist increments `pc090oj_dropped_count` and skips the piece;
- the finalizer stops emitting after 80 SAT entries;
- generated ordinary-death armored frames range from 1 to 9 pieces, depending on selector.

The 99-piece lane is unlikely to be the first limit for two armored men. The 12-new-cell DMA budget is
the strongest resource hypothesis: a walking actor can be fully resident while another instance changes
to a frame/orientation whose cells are not resident. Early pieces can load and later pieces can be
silently omitted. SAT order or the 80-entry total can produce a similar instance-order asymmetry.

### Ranked hypotheses

1. **Tile residency/DMA worklist saturation — high.** Explains intermittent, partial, per-instance
   corruption and why the other actor can remain normal. The decisive signal is a rise in
   `pc090oj_dropped_count` with `pc090oj_tile_dma_count==12` and missing expected keys from the resident
   table/worklist.
2. **SAT total/order truncation — medium.** A later back-enemy instance can lose a suffix of pieces when
   earlier lanes consume the 80-entry budget. Check `pc090oj_emitted_count`, semantic lane order, shadow
   SAT links, and actual VDP SAT.
3. **Per-instance selector/orientation or signed offset error — medium.** Two nominally identical enemies
   can be in different states. Compare their `+0x01/+0x1E/+0x20/+0x27/+0x38`, anchors, selected generated
   frame, piece count, and expected signed offsets. Downward fragments could be valid pieces with an
   incorrect Y anchor/offset.
4. **Stale/partial queue or SAT state — medium/low.** Double-buffering makes this possible, but the frame
   finalizer terminates the active chain. Prove by comparing the complete semantic queue to both shadow
   banks and the displayed bank.
5. **Genesis 20-sprites-per-scanline hardware limit — low but must be counted.** It normally causes
   sprites later on the same scanline to disappear, not pieces to acquire downward coordinates. Count
   actual per-line SAT load before excluding it.
6. **Global bad artwork/palette mapping — rejected as primary.** The simultaneous normal instance is
   direct contrary evidence.

### Narrowest follow-up capture

At the first bad frame, use the existing MAME/debug evidence methods to capture, without changing actor
logic:

- both armored actors' complete 64-byte retained records and actor indices;
- selected generated usage/frame-index entry and expected piece table for each;
- all six semantic lane counts and queue entries before finalization;
- `pc090oj_dropped_count`, `pc090oj_tile_dma_count`, DMA worklist, 49 resident keys, and used bitmap;
- `pc090oj_emitted_count`, both shadow SAT banks, `pc090oj_sat_front/bank/frame_ready`, and actual VDP SAT;
- referenced VRAM pattern bytes and a per-scanline sprite count;
- the corresponding original-arcade actor records and PC090OJ pieces at the same semantic states.

Diff expected pieces against queued pieces, then queued against shadow SAT, then shadow against VDP SAT.
That identifies the first presentation stage that drops or moves a piece. Do not patch collision, actor
state, or the enemy handler. Acceptance requires repeated two-armored-man encounters with zero missing,
misplaced, stale, residency-mismatched, or hardware-overflow pieces and unchanged damage/collision/death
behavior.

## Secondary issues

### R1-S1 gray borders — root cause isolated

VDP register 7 still selects palette 0/color 0. Build 0508's generated
`test_palette_line0.bin` normalized entry zero to `$0000` explicitly. The later per-scene palette path
introduced by commit `c8fd3e5d` copies `PAL-R1-S1-PLANEA-OUTDOOR.bin` verbatim; that file currently begins
with `$0888`, inherited from `Test.json` Line 0 entry 0. Because CRAM color 0 is also the backdrop, this
produces gray borders even when all visible tile pixels are otherwise correct.

This is a proven source-level regression mechanism and matches Tighe's Build 0508 boundary. The later
fix should restore the invariant that every exported scene palette normalizes all line index-zero entries
appropriately, especially CRAM[0], and add a gate comparing the scene asset's first word and runtime
CRAM[0]. It must not change unrelated CRAM colors or merely force register 7 to hide a bad export.

### R1-S3 boss music

The native audio library contains “The Devil Boss Carnival,” but `specs/audio_native_song_map.json`
currently maps only authentic commands `$04`, `$25`, and `$27`; the boss track is reachable only through
a diagnostic selector in that specification. Unmapped authentic commands are consumed without
interrupting current music. Therefore the appropriate future boundary is:

`retained arcade boss-entry music request and queue timing -> authentic command identity -> existing
Genesis track dispatch`.

Capture the original arcade command queue and Genesis retained queue at the R1-S2 -> R1-S3 transition,
including caller PC and ordering through `$03A0EC/$03A116`. Then match that command's original Z80
descriptor/subsequence to the already-present boss track before adding one command-map entry. Do not add
or duplicate song data, and do not synthesize a scene-number trigger.

### R1-S3 incorrect colors

This is part of P1. Record 22 has no authored context in `Test.json` or `AuthoredLayerA.SCENES`, and
R1-S3 sprite/Plane-B contexts are incomplete or absent. The visible colors are not a regression of a
completed R1-S3 authoring decision.

## Prioritized implementation roadmap

1. **P0-A: capture the first natural R1-S2 divergence.** Bounded to records 17–21 and the data listed
   above. Output: one durable arcade/Genesis cell-diff report. No rendering change.
2. **P0-B: unify the entering-row/column semantic producer.** Implement only after P0-A identifies the
   first bad source relationship. Remove the superseded PC080SN chip tail; validate natural forward and
   reverse play plus checkpoints.
3. **P1-A: close and register the R1-S2 sprite roster.** Armored bases `$0A73/$0A5A`, wizard identity,
   marker-M children, all effective banks/variants; use a new profile derived from Test.
4. **P1-B: add R1-S3 Plane A and sprite contexts.** Consume the existing 219-use corpus and proven boss
   composite, with source-palette provenance.
5. **P1-C: design the R1-S3 Plane B context.** Preserve Line-2 ownership and make the original Plane-B
   producer's scene result authorable/previewable without global unlock.
6. **P2-A: synchronized two-armored-man presentation capture.** Read existing counters/queues/SAT and
   prove the first dropped or displaced piece before changing capacity or geometry.
7. **Secondary-A: normalize per-scene CRAM entry zero.** Independently test Build 0508 versus the first
   per-scene-palette build and current runtime CRAM/register 7.
8. **Secondary-B: prove the authentic R1 boss music command and map it to the existing track.** No audio
   payload change.

Each task is independently testable. None authorizes a ROM build in this audit.

## Risks to preserved behavior

- Replacing a middle-record source rule without a first-divergence capture could regress the now-correct
  respawn replay or record-17 rows.
- Expanding scene palettes directly in `Test.json` could overwrite Tighe's accepted R1 work; use a new
  derived profile and explicit merge.
- Treating `$0A5A` only as an armored base can collide with its later reward/death semantic use; object
  identity must include actor state/selector, not base alone.
- Increasing sprite bounds before proving the first drop could exceed VBlank DMA or VRAM ownership and
  mask a signed-coordinate bug.
- Reassigning Line 2 for R1-S3 could break Plane B and shared sprite colors. Preserve the existing owner
  until a complete scene contract is approved.
- Mapping boss music by scene number instead of the retained request would change command ordering,
  death/retry behavior, or other rounds.

## Final status

This audit does not declare Build 0525 visually correct and does not accept it. It establishes the P0
path split and exact missing proof, inventories the P1 coverage gaps, ranks P2's presentation causes,
and isolates the gray-border regression mechanism. No ROM was built, no build number was consumed, and
no implementation file was changed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0045`
