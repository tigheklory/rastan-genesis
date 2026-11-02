# R1-S2 scrolled Plane A metatile alignment — Build 0527

Date: 2026-11-02

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055`

Reference: Build 0526

Candidate: Build 0527, **not accepted pending Tighe's gameplay test**

## Result

The defect is stale entering rows, not a global horizontal offset and not another selector-axis
transpose. During ordinary selector-1/2 vertical scrolling, the original arcade calls the row
publisher before committing the new foreground Y value in `A5+$10B0`. The native helper tested the
selected row against the window derived from that pre-step Y value. The row was outside that old
window, so its visual product was discarded. When scrolling subsequently exposed the corresponding
32-row Genesis ring slot, it still contained the row exactly 32 logical rows earlier.

That stale row is independently authored data. Its architectural features occur at different
columns, so one feature can appear left of its intended position while another appears right. No
single X-scroll or destination-column error is required.

Build 0527 makes ordinary arcade-requested selector-1/2 publications always stage the exact selected
entering row. The bounded 64-row scene-reseed replay retains its residency filter because that caller
deliberately enumerates all 64 logical rows to select the final 32. Initial reconstruction therefore
keeps its prior behavior.

No coordinate adjustment, scene special case, new map, new buffer, new translation layer, additional
VRAM/DMA work, collision change, or gameplay change was introduced.

## Confirmed visual symptoms

Tighe's screenshots and elaboration establish:

- R1-S2 scenery is correct before vertical scrolling.
- Scenery introduced as Rastan climbs is horizontally miscomposed.
- One chain section appears about two metatiles left and another about one metatile right.
- Correct tile patterns exist; collision and traversal remain functional.
- Build 0526 made no visible improvement to this earlier vertical-scroll failure.

The offsets are observations, not correction constants.

## Original arcade geometry and row publication

The foreground hardware ownership is unambiguous:

| Field | Original commit | Meaning |
|---|---|---|
| `A5+$10B0` | `$055AC4 -> $C20002` | foreground/tilemap-1 Y |
| `A5+$10AE` | `$055ACC -> $C40002` | foreground/tilemap-1 X |

The PC080SN metatile is 4×4 8-pixel cells, or 32×32 pixels. Sixteen descriptor segments times four
subcells form a 64-cell row. Sixteen groups times four strips form the 64 logical rows.

For selector 1, original `$055696` forms destination row
`63 - (group*4 + strip)`; selector 2 at `$05572E` forms `group*4 + strip`. Original `$055A14` then
iterates descriptor segment `k=0..15` and subcell `i=0..3`:

```text
source row in metatile = ((~strip)&3) for selector 1, (strip&3) for selector 2
source byte offset      = source_row*8 + i*2
destination column      = k*4 + i
```

The rebuilt tables are parallel: `$10D040[k]` is the resolved metatile pointer and `$10D080[k]` is
its attribute word. The arcade writes the selected row into PC080SN name RAM and publishes collision,
then `$05570C..$055718` or `$055798..$0557A4` commits the new `A5+$10B0` Y value.

## Existing Genesis behavior and the actual mismatch

`genesistan_hook_tilemap_plane_a_selector12_native` already reproduced the source and destination
geometry above:

- descriptor segment `k` came from the rebuilt pointer/attribute tables;
- the metatile offset was `source_row*8 + i*2`;
- the logical destination column was `k*4+i`;
- selector 1 used reverse destination rows and selector 2 forward destination rows;
- collision was always published to the retained 64×64 collision grid.

The error occurred only after that correct selection. The helper computed visible top from live
`A5+$10B0` and rejected the visual unless `(logical_row - old_top) & 63 < 32`. On record 17,
selector 1 requests rows 63, 62, 61, ... before those rows enter the post-scroll display window.
Rejected logical row 63 aliases physical row 31, rejected row 62 aliases physical row 30, and so on.
The old physical content therefore survives.

### Representative source-derived mismatch

Record 17 is selector 1. For intended logical row 63, descriptor segment 2 (destination columns
8..11) uses original descriptor entry `$01B2DC`, metatile pointer `$50F4`, and subcell tile words
`$0824,$0825,$0826,$0827`. If the publication is rejected, physical row 31 instead retains logical
row 31. At the same columns that row comes from entry `$01B2FC`, pointer `$5534`, and words
`$0824,$0825,$08F7,$0827`.

At descriptor segment 14 (columns 56..59), intended row 63 uses entry `$0353DC`, pointer `$5574`,
and `$0824,$0825,$08F7,$0827`; stale row 31 uses entry `$0353FC`, pointer `$5034`, and
`$0824,$0825,$0826,$0827`.

The static row corpus also reproduces the visual displacement estimates:

- intended row 59 has distinctive tile `$08F7` at logical column 58; stale alias row 27 has it at
  column 50: eight cells, or two 4-cell metatiles, left;
- an architectural four-cell sequence at intended columns 8..11 occurs at stale-alias columns
  12..15: four cells, or one metatile, right.

Thus different offsets in opposite directions are expected when a different authored row is exposed.
They do not support an arbitrary global `+1/-1/-2` correction.

## Competing-hypothesis assessment

| Hypothesis | Assessment |
|---|---|
| A. Stale rows | **Proven.** The ordinary selected row can be discarded by the pre-step residency test, leaving its N-32 physical alias. |
| B. Wrong source columns | Rejected for this path. Original and native code select the same rebuilt segment and metatile subcell. |
| C. Wrong destination columns | Rejected. Both use `segment*4+subcell`; no column offset exists in the native row writer. |
| D. Incorrect selector/axis interpretation | Rejected here. Build 0387's extra-transpose change was user-rejected and reverted; the direct row writer already mirrors `$055A14`. |
| E. Mixed old/new content | Observed consequence of A across the 32-row ring, not a separate descriptor-generation rule. |

The previous old-window hypothesis was therefore directionally correct, but the correction is not to
apply an assumed post-step coordinate or remove every residency guard. The valid distinction is the
caller's semantic contract: ordinary `$055A14` has already selected exactly one entering row, while
scene reseed is a 64-row enumeration that still requires filtering.

## Minimal correction

Source commit: `eceb8a9c92dbfc50c0c716ddeeaced7b670b5914`.

Changed:

- `apps/rastan-direct/src/tilemap_hooks.s`
- existing gate `tools/translation/verify_plane_a_selector12_segment_hoist.py`

At the three former visual-residency gates (attribute resolution, visual resolution, and final staging):

- normal arcade publication (`plane_a_initial_ring_rebuild_active == 0`) consumes and stages the row;
- bounded scene replay (`plane_a_initial_ring_rebuild_active != 0`) preserves the existing 32-of-64
  residency predicate.

Collision remains unconditional and unchanged. Upward selector 1 and downward selector 2 share the
same corrected publication contract while retaining their independent source-row and destination-row
direction formulas.

Build 0526's record-17 selector-1 to record-18 selector-0 mixed-ring correction remains present and
unchanged in `.Lplane_a_publish_logical_row_native`.

## Architecture compliance

- **Semantic cut retained:** the arcade has selected the entering Plane A row, descriptor segment,
  metatile subrow, attributes, and collision product.
- **Chip tail removed below the cut:** original `$055990/$055A14` PC080SN destination/name-RAM walk is
  replaced by final Genesis Plane A staging plus the retained collision publication.
- **Transitional compatibility retained:** the existing rebuilt arcade semantic descriptor tables,
  staging buffer, dirty-row publication, and scene-reseed flag remain consumers/producers exactly as
  before. No chip-shaped name-RAM shadow, 64×64 visual shadow, projector, or new compatibility path was
  added. Their broader retirement boundaries are unchanged and outside this task.
- Arcade execution, frame progression, VBlank, scrolling, and gameplay remain arcade-owned.

## Verification

No task-specific MAME trace, first-divergence capture, automated traversal, or new diagnostic tooling
was created. Existing Ghidra exports, original disassembly, generated arcade-derived row assets, and
existing static gates were reused. The normal Makefile's mandatory Genesis NTSC 30-second trace ran as
part of publication.

Passed checks include:

- selector-1/2: 128 destination-row cases, 1,869,856 rebuilt-metatile/attribute cases, 1,869,856
  descriptor/subcell/context cases;
- 4,096 ordinary row/top cases all publish visuals;
- scene replay still filters 2,048 resident and 2,048 nonresident row/top cases;
- full-span background coherence, initial N/N+32 semantics, ring seams, source rebase, dirty gather,
  native metatiles, scene/pan maps, collision/visual independence, and selector relocation;
- canonical gate, gameplay-entry gate, seven-epoch/package gate, boot guards, and complete variant set;
- mandatory Genesis NTSC trace: 1,798 frames, final PC `$03B2C8`, SP `$00FEFFFC`, no unique unmapped
  addresses in the Makefile exit summary.

Existing project tools reused: Ghidra exports, `build/maincpu.disasm.txt`, arcade-derived PC080SN
compiler outputs, selector/static verification gates, boot/canonical/gameplay/epoch gates, and the
Makefile-owned release workflow.

New tooling created: **none**. One existing selector-1/2 verifier was updated to encode the corrected
ordinary-publication versus scene-reseed contract.

## Build 0527 artifacts

Counter and consumed ledger: `0527`, `canonical=PASS entry=PASS epoch=PASS`.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0527.bin` | 3,792,568 | `292c8f80d4f428bc06e56da33de1973a1e7b81a60ab58a0061af651d67fe54a8` |
| `dist/rastan-direct/rastan_direct_video_test_build_0527_S1-2.bin` | 3,792,568 | `e5cd193f51b6b09a9bf96a2b6c4f43dd4d51f0ae76831926336675492dbd76ec` |

The R1-S2 variant retains selector `$DF` and the existing direct-start command `$27` audio patch.

## Remaining uncertainty and acceptance

Static source proves that the intended row was discarded and that the stale N-32 row contains the
opposite-direction feature displacements seen in the screenshots. This task intentionally did not
run the natural R1-S2 climb. Build 0527 remains a candidate until Tighe verifies in gameplay:

1. initial R1-S2 scenery remains correct;
2. both chains remain horizontally continuous as rows enter during upward scrolling;
3. downward scrolling republishes coherent rows;
4. the record-17 to record-18 handoff still benefits from Build 0526's preserved correction;
5. R1-S1/R1-S2 checkpoint restoration, collision, traversal, Plane B, sprites, palettes, audio, and
   boss entry remain unchanged.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055`
