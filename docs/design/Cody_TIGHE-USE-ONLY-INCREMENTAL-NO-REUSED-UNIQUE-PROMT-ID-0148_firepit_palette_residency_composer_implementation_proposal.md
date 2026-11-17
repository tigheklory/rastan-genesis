# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0148

# R1-S2 Fire-Pit Palette Residency — Independent Composer Implementation Proposal

## Status and scope

This is Cody's independent completion of the research begun under historical
`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0145`. PROMT-ID-0145 ended only because the
agent usage limit was reached. Its valid repository reading and source findings were preserved rather than
restarted. PROMT-ID-0148 is the active completion prompt.

This report is research and proposed architecture only. Production changes: **NONE**. Palette Composer
changes: **NONE**. Test 2.0/profile changes: **NONE**. ROM produced: **NONE**. Build number consumed:
**NONE**. No push was performed. The two later independent proposals named in the prompt were not read.

## 1. Recovered PROMT-ID-0145 state

At recovery:

- branch: `rastan-direct-proposal`;
- HEAD: `a823c07792d3f0c69cbcc6d9d653b1767787a5b2`;
- Makefile-owned counter: `573`;
- no PROMT-ID-0145 task report or temporary fire-pit output existed; the similarly named
  `Andy_build_0145_bank51_line3_delivery.md` is an old build-number document, not this task;
- the worktree already contained concurrent modifications to the issue ledgers, generated build/output
  files, `apps/rastan-direct/src/sound/sound_comm.s`, Round-1 completion trace tools, and unrelated design
  reports. They were not modified, cleaned, staged, or reverted by this task;
- two forbidden later fire-pit proposal files were present as untracked files. They were identified by name
  only and not opened.

The interrupted run had already read the required project policy/architecture files and the relevant
ledgers. Relevant durable priors were KF-046, KF-074, KF-089, OPEN-006, OPEN-036, OPEN-041, and
CLOSED-023; the work is classified **NEW** and does not contradict them. The high rediscovery hazard is
the established Line-2/Layer-B ownership and sparse-retain contract.

## 2. Current architecture and exact implementation inspected

The current path is:

```text
Test_2_0.json authoring policy
        |
        +-- context_policies[scene].tpl                       CRAM Lines 0/1/3
        +-- context_policies[scene].plane_usage_palette_mappings
        +-- usage_palette_mappings                            PC090OJ
        |
        +--> compile_pc080sn_genesis.py / gen_reindexed_region.py
        |       offline Plane-A nibble reindex + native record packages
        +--> gen_reindexed_pc090oj.py
        |       offline sprite nibble reindex + (code,bank) variants
        +--> gen_test_palette_cram.py / export_subround_palette_manifest.py
                static authored CRAM assets and provenance

retained arcade palette/progression decisions
        +--> palette_hooks.s --> staged_palette_words
        +--> palette_pending --> dma.s VBlank CRAM DMA
        +--> fg_tile_cache.s record/package transitions
```

The profile SHA-256 inspected was
`4339688ebe07bc121d5108d464f57b320a6628f4c36cdd71a95cfe5ea8c964cf`. The palette-decision
registry SHA-256 was
`9fdd8f928b08cffbacb3536495204a761893889cd79ddd4f692a52a44aa8f0e3`.

Files inspected directly for this proposal include:

- `analysis/graphics_optimizer/editor_policy/Test_2_0.json`;
- `specs/palette_decisions.json`, `specs/palette_subround_map.json`, and
  `specs/rastan_direct_remap.json`;
- `tools/graphics_editor/server.py`, `index.html`, and `app.js`;
- `tools/graphics_editor/gen_reindexed_region.py`, `compile_editor_layera.py`,
  `gen_reindexed_pc090oj.py`, `gen_test_palette_cram.py`, and
  `export_subround_palette_manifest.py`;
- `tools/translation/compile_pc080sn_genesis.py`,
  `gen_pc080sn_plane_b_visual_records.py`, and
  `verify_pc080sn_plane_b_visual_records.py`;
- `apps/rastan-direct/Makefile`;
- `apps/rastan-direct/src/palette_hooks.s`, `dma.s`, `vdp_comm.s`, `scene_load.s`,
  `fg_tile_cache.s`, `tilemap_hooks.s`, and `pc090oj_hooks.s`;
- `analysis/graphics_optimizer/subround_corpus/PAL-R1-S2-PLANEA-CASTLE/plane_a_uses.json` and
  `plane_palette_banks.json`;
- `analysis/graphics_optimizer/round1_phase1/plane_b_uses.json` and the current Layer-B display
  palette evidence;
- `analysis/ghidra/rastan_arcade/exports/full_listing.tsv`, `xrefs.tsv`,
  `scalar_constants.tsv`, `call_graph_edges.tsv`, and `decompiler_export.c`;
- `build/regions/maincpu.bin`, `build/regions/pc080sn.bin`, and
  `build/rastan-direct/pc080sn_plane_b_visual_report.json`;
- the historical, pre-independent-proposal reports
  `Andy_r1s2_traps_proven_authorable.md` and `Andy_r1s2_trap_graphics_sources.md`.

The current Composer has a read-only arcade oracle, per-usage pixel decoding, per-tile MRD, context-local
Plane-A mappings, target Lines 0/1/3, and a protected read-only Line-2 display. It does **not** model a
progression interval, a shared palette domain spanning multiple usages, a temporary line owner, or an
explicit approved MRD exception. The Segment Map and Tile Library can identify and render the constituent
Plane-A tiles, but they cannot preview a complete Plane-A/Plane-B/effect composite across palette phases.

## 3. Exact fire-pit asset proof

### 3.1 Record, section, geometry, and visibility

The pit belongs to R1-S2 **section 3, retained record 18**. “Segment 18” in the working hypothesis means
the retained record number; the current map labels it `SECTION 3 (record 18)`. Record 17 is section 2.

The sixteen usages are all record 18 and form a repeated 4x4 unit:

| Usage | Tile | Record-local position |
|---|---:|---|
| LA-0479..LA-0482 | `$093A..$093D` | row 28, columns 8..55, period 4 |
| LA-0483..LA-0486 | `$093E..$0941` | row 29, columns 8..55, period 4 |
| LA-0487..LA-0490 | `$0942..$0945` | row 30, columns 8..55, period 4 |
| LA-0491..LA-0494 | `$0946..$0949` | row 31, columns 8..55, period 4 |

The corpus expresses X as `record * 64 + local_column`, hence global X `$488..$4B7` (1160..1207).
A 40-cell viewport entering record 18 at local X=0 already intersects the pit at local X=8. The pit is
therefore potentially visible immediately on record-18 presentation. It is entirely behind the progression
boundary on entry to record 19. The safe coarse residency is consequently **record 18 only**: activate
before record 18 is published and release on record 19. Record 17 is a conservative but unnecessary early
preload point; a 32-byte CRAM line already resident in ROM needs no runtime “preload.” If a future design
separates preparation from activation, record 17 may prepare, but it must not change visible CRAM.

This record interval is safer than a camera-coordinate timer and naturally handles a reverse transition
19→18. It is deliberately coarser than the exact last pixel leaving the viewport.

### 3.2 Plane-A source

The effect is exactly PC080SN fixed Plane-A tiles `$093A..$0949`, palette bank `$014`. All source indices
1..15 occur; index 0 is absent from these sixteen patterns. Aggregate pixel counts in one 4x4 source unit
are:

| Source index | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pixels | 7 | 2 | 34 | 83 | 209 | 214 | 179 | 6 | 13 | 45 | 70 | 13 | 14 | 55 | 80 |

Thus this cannot be analyzed as “four colors are used.” A four-to-seven-color version is an intentional
reduction of a real fifteen-index domain.

The static arcade bank-`$014` RGB8 row is:

```text
0 black;
1 (247,115,0); 2 (247,132,0); 3 (247,165,0); 4 (247,214,0);
5 (247,247,132); 6 (247,231,132); 7 (247,247,247); 8 (247,247,214);
9 (247,247,181); 10 (247,247,165); 11 (247,247,148);
12 (247,165,0); 13 (247,181,0); 14 (247,214,0); 15 (247,247,0)
```

### 3.3 Sprite proof: zero R1-S2 pit-flame sprites

The working mixed-consumer hypothesis is disproven. R1-S2 has **no PC090OJ sprite cap or animated flame
sprite belonging to this pit**. The PC090OJ base `$0224` actor is a separate R2/R4 marker actor and is
retired on the R1-S2 progress range. The one R1-S2 marker burst is an unrelated “M” effect. The apparent
upper flame motion is the fixed Plane-A pattern changing color.

Therefore the R1-S2 source-index overlap between Plane A and fire sprites is the empty-set question: the
Plane-A set is `{1..15}` and the fire-sprite set is `{}`. One Genesis allocation can represent the complete
effect because there is only one graphics consumer. A generic future Effect Group should still support both
consumer types, but this fire group must not invent sprite members or sprite constraints.

### 3.4 Palette animation proof

`FUN_00059962` checks mode 8, advances a 0..23 counter, and calls `$059AD4` every eighth tick. That selects
three 16-word rows at `$59B1A`; stage 1 selects destination arcade line `$14` through `$59A98`. The tile
patterns never change.

After the project's established arcade-to-Genesis conversion, the three phase rows are:

```text
phase 0: KEEP 006E 008E 00AE 00CE KEEP 08EE 0EEE 0CEE 0AEE 0AEE 08EE 00AE 00AE 00CE 00EE
phase 1: KEEP 00AE 00AE 00CE 00EE KEEP 0AEE 0CEE 006E 008E 00AE 00CE 0CEE 0AEE 0AEE 08EE
phase 2: KEEP 0CEE 0AEE 0AEE 08EE KEEP KEEP KEEP 00AE 00AE 00CE 00EE 006E 008E 00AE 00CE
```

`KEEP` is the original `$FFFF` semantic: do not replace that entry. The animation changes palette entries,
not sprite/pattern frames. Any design that emits only one static reindexed palette cannot reproduce it.

## 4. Current Genesis mapping and why it is poor

All sixteen current fire usages select protected Genesis Line 2. Their maps collectively use Line-2
indices `{1,2,3,4,9,10,11,12,13,14,15}`. The mapping is independently optimized per 8x8 usage; the same
arcade source index therefore maps to different target indices in different flame tiles. This is legal under
the current per-tile MRD rule, but it destroys the shared palette identity needed for coherent animation.

The exact saved Test 2.0 maps (`source>target`) are:

| Usage | Map |
|---|---|
| LA-0479 | `1>11 3>3 4>14 5>2 7>13 12>4 13>9 14>15 15>1` |
| LA-0480 | `1>4 2>3 3>2 4>15 5>1 6>14 7>13 15>9` |
| LA-0481 | `3>3 5>14 6>15 7>13 14>2 15>1` |
| LA-0482 | `4>14 6>2 7>13 10>3 11>9 14>15 15>1` |
| LA-0483 | `4>12 5>15 6>2 7>13 10>10 11>9 12>3 13>4 14>14 15>1` |
| LA-0484 | `3>2 4>15 5>1 6>14 7>13` |
| LA-0485 | `5>1 6>14 7>13 11>9 14>2 15>15` |
| LA-0486 | `6>15 7>13 8>9 9>2 10>1 11>14` |
| LA-0487 | `5>15 6>14 7>9 8>3 9>2 10>13 11>1 15>4` |
| LA-0488 | `4>2 5>1 6>9 7>13 12>4 13>3 14>14 15>15` |
| LA-0489 | `5>2 6>1 7>13 11>9 12>4 13>3 14>14 15>15` |
| LA-0490 | `1>11 3>3 4>14 5>1 6>15 7>13 9>4 10>9 11>2` |
| LA-0491 | `1>11 3>3 4>15 5>1 6>14 7>13 10>9 11>2 15>4` |
| LA-0492 | `3>12 4>15 5>1 6>14 7>13 10>10 11>9 13>4 14>3 15>2` |
| LA-0493 | `4>4 5>1 6>14 7>13 9>11 10>10 11>9 12>12 13>3 14>15 15>2` |
| LA-0494 | `1>3 3>15 4>14 5>1 6>2 7>13` |

Current R1 Line 2 is:

```text
index:  0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15
CRAM : 0000 00EE 08AE 068E 046A 0046 0024 0A60 0620 0AAC 0668 002E 004A 0EEE 00CE 008A
```

More importantly, `genesistan_palette_hook_59ad4` recognizes the current round's Layer-B bank as the sole
gameplay owner of Line 2 and rejects other gameplay bank writes. Bank `$14` falls through the `bank >= 4`
exit, so its mode-8 phases never reach Genesis CRAM. The result is a static, tile-local approximation using
unrelated Layer-B colors. That is the source-backed reason the Genesis pit is much poorer than arcade.

## 5. Line-2 occupancy and writer analysis

The current evidence does not contain a z-composited, per-record “this Plane-B index is fully occluded”
manifest. It would be unsafe to manufacture one from the scene-wide vocabulary. The correct classification
is therefore conservative:

| L2 index | Current value | Visible/other use | Writer/retain status | Classification | Lease? |
|---:|---:|---|---|---|---|
| 0 | `0000` | backdrop/transparent invariant | invariant | USED + STATIC | no |
| 1 | `00EE` (captured states also `0000`) | Plane B; current fire mappings | observed R1 dynamic entry | USED + DYNAMIC | no |
| 2 | `08AE` | Plane B; current fire | full Layer-B loader and sparse retain | USED + STATIC* | no |
| 3 | `068E` | Plane B; current fire | same | USED + STATIC* | no |
| 4 | `046A` | Plane B; current fire | same | USED + STATIC* | no |
| 5 | `0046` | Plane B | same | USED + STATIC* | no |
| 6 | `0024` | Plane B | same | USED + STATIC* | no |
| 7 | `0A60` | Plane B | same | USED + STATIC* | no |
| 8 | `0620` | Plane B | same | USED + STATIC* | no |
| 9 | `0AAC` | Plane B; current fire | same | USED + STATIC* | no |
| 10 | `0668` | Plane B; current fire | same | USED + STATIC* | no |
| 11 | `002E` | Plane B; current fire | same | USED + STATIC* | no |
| 12 | `004A` | Plane B; current fire | same | USED + STATIC* | no |
| 13 | `0EEE` | Plane B; current fire | same | USED + STATIC* | no |
| 14 | `00CE` | Plane B; current fire | same | USED + STATIC* | no |
| 15 | `008A` | Plane B; current fire | same | USED + STATIC* | no |

`*` means no color change appeared in the four current display snapshots, not that the entry is free.
Every real gameplay Plane-B name word is forced to Line 2. The retained Layer-B producer can load the whole
line, and `$59AD4` preserves any `$FFFF` entry by retaining the resident value. That makes writer history
part of correctness even when a particular index is momentarily occluded. FRONTEND_FULL also multiplexes a
different Line 2 at its presentation boundary, but it is not a simultaneous R1-S2 gameplay consumer.

Consequently the number of **proven `UNUSED + STABLE` entries is zero**. This is not a claim that every
Plane-B index is visible in every fire frame; it is the stricter and relevant finding that no current
artifact proves an entry both unused and safe from writer/retain dependencies. A future analyzer may improve
that answer. Until it does, slot leasing is not source-backed.

## 6. Strategy A — existing resident colors only

The following are illustrative global source-index mappings, not approved art. They were calculated over
all three fire phases, weighted by actual pixels, using simple RGB RMS against resident L2 colors. RMS is
only a comparative indicator; it is not a perceptual acceptance metric.

| Target count | L2 entries | Source index → L2 index | RGB RMS | Consequence |
|---:|---|---|---:|---|
| 4 | 1,2,13,14 | `1>2 2>14 3>14 4>1 5>2 6>2 7>13 8>2 9>14 10>14 11>1 12>2 13>14 14>14 15>1` | 45.6 | strong merges; one white |
| 5 | 1,2,3,13,14 | `1>3 2>14 3>14 4>1 5>2 6>2 7>13 8>3 9>14 10>14 11>1 12>3 13>14 14>14 15>1` | 45.4 | small improvement |
| 6 | 1,2,3,12,13,14 | five-color map, except `2>12` | 45.5 | forced rare sixth color; no quality gain |
| 7 | 1,2,3,11,12,13,14 | six-color map, except `1>11` | 46.1 | forced seventh color worsens fit |

Every row intentionally violates the current within-tile injective MRD rule because the source has fifteen
used indices. These merges must be explicit Tighe decisions, never an automatic relaxation of MRD. The
maps work technically for Plane A and have no sprite compatibility issue, but they remain static. Merely
using more resident colors does not restore flicker because the resident targets do not follow the mode-8
phase values. This is a low-risk fallback, not an arcade-faithful solution.

## 7. Strategy B — lease safe L2 entries

No L2 index is presently proven `UNUSED + STABLE`, so the safe lease set is empty. In particular, entries
5..8 are absent from the current fire maps but are not thereby free: Plane B owns them and sparse rows may
retain them.

If a future generated visibility/writer analyzer proves slots free, leasing would require:

1. a single global fire map, not sixteen unrelated maps;
2. record-18 activation before publication;
3. exact restoration on 18→19 and reactivation on 19→18;
4. the same lifecycle on death/respawn, direct start, and attract;
5. proof that no active Layer-B writer targets a leased slot, including `$FFFF` history.

Without those proofs, a lease would reproduce the same class of resident-palette destruction already fixed
elsewhere in the project. Strategy B is therefore **not currently feasible**.

## 8. Strategy C — record-scoped composite L2

The complete desired fire phase vocabulary has nine distinct Genesis colors:

```text
006E 008E 00AE 00CE 00EE 08EE 0AEE 0CEE 0EEE
```

Only `00EE` exactly overlaps the current fifteen-entry L2 row. If all fifteen Layer-B entries remain
required, a lossless composite needs `15 + 9 - 1 = 23` nontransparent entries: eight over capacity. A
four-color desired fire subset with one exact overlap still needs 18 entries (three merges); seven desired
colors need 21 (six merges). Thus a lossless full-fidelity composite is impossible unless record-local
analysis proves enough Layer-B entries unnecessary.

That missing analysis must use the real record-18 Plane-A transparency mask, Plane-B record, viewport
envelope, and palette-writer history. It must report the actual visible Layer-B source-index set, then exact
deduplication against the chosen fire phase colors. The compiler can then solve:

```text
required = visible Layer-B colors U approved fire colors
capacity = 15
minimum approved merges = max(0, |exact-deduplicated required| - 15)
```

If the analyzer produces at most 15 after approved merges, Strategy C is the best visual architecture:
compile one coherent record-18 L2 allocation, reindex the relevant Plane-B patterns and all sixteen fire
patterns offline, and compile three complete phase rows. No runtime color matching is allowed.

The important stop condition is Layer-B activity. A regional composite may be activated only if the
analyzer proves the Layer-B source state is stable for the whole interval, or if every legitimate semantic
Layer-B phase is compiled as a corresponding composite state. Silently blocking or partially overlaying a
Layer-B write is not acceptable. A saved 16-word “old L2” alone is insufficient if Layer B changes while
the region is active; maintaining a hidden live duplicate would become the palette-emulation layer this
proposal forbids.

## 9. Strategy D — another complete CRAM line

No alternate line is safely free over the interval:

- Line 0 owns Rastan, player weapons/effects, HUD/gameplay labels, and other Test 2.0 sprite consumers.
- Line 1 owns gameplay enemy consumers and later the R1 boss/daggers.
- Line 3 is the R1-S2 authored Plane-A master palette. Replacing it would recolor the castle, traps, and
  other simultaneous Plane-A cells. Its entries 14/15 also participate in the existing water-animation
  realization where applicable.

Build 0573's current authored ownership must be preserved. A full-line lease would therefore require
moving/reindexing more simultaneous consumers than the fire effect and is higher risk than a proven
composite L2. Strategy D is rejected for R1-S2.

## 10. Generic Palette Residency Region design

The feature should be generic, not named for the pit. The semantic cut is:

> retained arcade progression/record decision and retained palette-cycle/effect identity → generated native
> region/phase selection → final Genesis CRAM words and already-reindexed native patterns.

The retired chip tail is any consumer-specific interpretation that assumes arcade physical palette bank
`$14` can directly exist on Genesis, plus runtime color conversion/matching below that boundary. No
PC080SN/PC090OJ device, palette RAM emulator, screen inspection, pixel test, timer, or full backing map is
introduced. No chip tail is changed by this research-only task.

A Palette Residency Region associates a context and retained record interval with a target CRAM line,
participating usages, approved merges, and authored phase colors. The generated schedule, reindexed patterns,
and final complete phase rows are derived outputs.

### Effect Group

An Effect Group is an authoring selection domain, not a new runtime object. It may contain Plane-A usage
IDs and PC090OJ usage IDs, and it enforces a coherent source-index domain when members share a source
palette. For this effect:

```text
group: r1s2-pit-fire
Plane A: LA-0479..LA-0494
sprites/effects: []
source bank: 0x014
used source indices: 1..15
phases: 3, original cadence every 8 retained ticks
```

The generic mixed-consumer facility remains useful later, but the UI must visibly say “0 sprite members”
here so the disproven sprite hypothesis cannot return as implementation lore.

## 11. Palette Composer UX

### Palette Regions view

Add a view beside Sprites/Layer A/Contexts/Palettes that shows round/subround progression horizontally:
record, section label, active package, residency regions, preload/activation/release boundaries, target
line, phase count, and validation status. Protected lines remain visibly protected; a region does not make
Line 2 generally editable.

### Create Palette Region

From the Segment Map or selected Tile Library usages, “Create Palette Region” should:

1. bind to the current context;
2. propose the min/max retained records from the actual usage corpus;
3. distinguish ROM preparation from visible activation;
4. collect selected Plane-A and sprite/effect usages into an Effect Group;
5. run the visibility/writer analyzer before exposing any protected-line target;
6. refuse to call a slot free without `UNUSED + STABLE` evidence.

For this pit it should propose activation `[18,18]`, preparation at 18 (optionally 17), release at 19.

### CRAM occupancy

Show 4x16 cells with owner, current CRAM, visible consumers, dynamic writers, `$FFFF` retain dependence,
region owner, and classification. States should include `USED+DYNAMIC`, `USED+STATIC`,
`UNUSED+DYNAMIC`, `UNUSED+STABLE`, and `TEMPORARILY LEASED`. Clicking a cell opens the exact usages and
writer evidence, not just a color swatch.

### Intentional reduction

Keep ordinary MRD strict. A separate “Approve lossy merge” action records the exact source indices,
target entry, affected usages/phases, measured error, reason, and Palette Decision ID. The preview and
validation remain warning/red until Tighe approves it. An approval applies only to that Effect Group and
region; it must not weaken MRD globally or for unrelated objects.

### Preview

Existing individual Plane-A renderers can render the sixteen source tiles and their mapped targets. Add a
region compositor that draws the actual Plane-B record, Plane-A transparency/priority, and any sprite
members for each phase and representative viewport. Controls should scrub record/camera and phase and show
arcade, current Test 2.0, proposed Genesis, and difference views. For this effect no new sprite renderer is
needed, but the generic compositor can reuse the current PC090OJ composite renderer when a future group has
sprite members.

## 12. Persistent schema

Store deliberate authoring in a top-level `palette_regions` collection in the existing profile. Do not put
it inside one usage map: the region spans multiple usages and progression. `context_policies` remains the
authority for static context colors/maps. `specs/palette_decisions.json` remains the only approval/decision
registry; it records the decision and applicability, while the profile owns the editable mapping details
and cites the decision ID.

Proposed authoring example (illustrative values remain unapproved):

```json
{
  "palette_regions": {
    "PR-R1S2-RECORD18-FIRE": {
      "context_id": "PAL-R1-S2-PLANEA-CASTLE",
      "round": 1,
      "subround": 2,
      "records": [18, 18],
      "prepare_record": 18,
      "activate_record": 18,
      "release_record": 19,
      "target_line": 2,
      "effect_groups": [
        {
          "id": "EG-R1S2-PIT-FIRE",
          "source_palette_banks": ["0x014"],
          "plane_a_usage_ids": [
            "LA-0479", "LA-0480", "LA-0481", "LA-0482",
            "LA-0483", "LA-0484", "LA-0485", "LA-0486",
            "LA-0487", "LA-0488", "LA-0489", "LA-0490",
            "LA-0491", "LA-0492", "LA-0493", "LA-0494"
          ],
          "sprite_usage_ids": [],
          "source_index_map": {
            "1": 3, "2": 14, "3": 14, "4": 1, "5": 2,
            "6": 2, "7": 13, "8": 3, "9": 14, "10": 14,
            "11": 1, "12": 3, "13": 14, "14": 14, "15": 1
          },
          "phase_source": {
            "arcade_table": "0x059B1A",
            "phase_count": 3,
            "cadence_ticks": 8,
            "keep_word": "0xFFFF"
          }
        }
      ],
      "authored_fire_cram": {
        "1": "0x00EE", "2": "0x08AE", "3": "0x068E",
        "13": "0x0EEE", "14": "0x00CE"
      },
      "intentional_merges": [
        {
          "source_indices": [4, 11, 15],
          "target_index": 1,
          "decision_id": "PAL-PC080SN-R1S2-PIT-FIRE-REDUCTION-001"
        }
      ],
      "decision_ids": ["PAL-PC080SN-R1S2-PIT-FIRE-REDUCTION-001"]
    }
  }
}
```

The example demonstrates shape, not a recommended five-color selection. `authored_fire_cram`, the global
source map, boundaries, group membership, and approved merge references are persisted choices. The following
are derived and must not be persisted in the profile: visible Layer-B index set, composite target row,
per-phase complete rows, transformed pattern bytes, record lookup table, exact-dedup result, capacity/error
metrics, and provenance hashes.

The new registry decision would use one of the established statuses (`provisional`, `decided`, `proven`,
or `unknown`) and explicit scene applicability. It must not duplicate the index map.

## 13. Python implementation proposal

If approved later:

| Module | Current responsibility | Proposed addition / output |
|---|---|---|
| `server.py` | oracle, usages, renderers, solver, policy API | region/effect-group API; occupancy evidence; explicit-merge validation; phase extraction; no protected-line bypass |
| `app.js` / `index.html` | current Composer UI | Palette Regions view, creation flow, occupancy grid, merge approval, composite phase preview |
| `compile_pc080sn_genesis.py` | current per-record Plane-A native packages and authored reindex | consume generated region usage maps; emit region-specific Plane-A and, if proven necessary, Plane-B variants |
| `gen_reindexed_region.py` / `compile_editor_layera.py` | offline Plane-A nibble reindex/proof | factor their transform logic into a shared library; require one group-wide source map for region members |
| `gen_reindexed_pc090oj.py` | offline `(code,bank)` sprite variants | consume Effect Group sprite members when nonempty; no change needed for this pit |
| `export_subround_palette_manifest.py` | context palette/decision contract | cite region decision IDs and generated region artifact, without exporting protected L2 as an ordinary scene override |
| new `analyze_palette_residency.py` | — | z-composited visibility, source-index occupancy, writer/retain classification, capacity and exact-dedup report |
| new `compile_palette_regions.py` | — | validate profile+registry, compile complete phase rows, record lookup, descriptors, reindex maps, provenance manifest |

Adding two coherent modules is preferable to extending the static palette exporter until it has unrelated
runtime-schedule responsibilities. Shared decode/conversion helpers should be imported from current tools,
not copied.

Validation must reject: unknown usage IDs; usages outside the context/record interval; index zero remaps;
unapproved MRD merges; protected-line regions without occupancy proof; overlapping owners of the same line;
unresolved dynamic Layer-B writers; bad release/reversal coverage; decision IDs absent or inapplicable;
nonlegal CRAM words; phase maps that omit used source indices; and nondeterministic output.

## 14. Generated artifacts and binary contract

Suggested deterministic outputs under `build/rastan-direct/palette_regions/`:

- `record_region_id.bin`: one byte per supported retained record (46 bytes for R1/R2 now; `$FF` = none);
- `region_descriptors.bin`: fixed 12-byte rows containing target line, flags, phase count, phase-row offset,
  base/restore-row offset, and decision/provenance index;
- `region_cram_rows.bin`: 16 big-endian words per complete row. One static base plus three fire phases is
  128 bytes maximum for this region; if base is already one phase, 96 bytes;
- `region_plane_index_maps.bin`: compact derived maps used at build time, not necessarily linked at runtime;
- region-specific reindexed pattern/package outputs through the existing PC080SN compiler;
- `palette_region_manifest.json`: input SHAs, decision IDs, members, occupancy proof, exact colors, merges,
  output offsets/hashes, and validation results.

No runtime JSON parsing is introduced. The record table makes selection O(1); no arbitrary interval scan is
needed.

## 15. Runtime contract

The useful existing boundary is `fg_boundary_install`, reached from normal record progression,
post-reseed scene fills, direct/reseed descriptor reconstruction, and scene entry. After it derives
`fg_boundary_pending_record`, a generic `palette_region_select(record)` can index one byte and compare it to
the active region ID. One lookup and one comparison occur only at an existing record/install event, not per
frame.

On a region change:

1. select the generated complete CRAM row;
2. copy exactly 16 words into the target portion of `staged_palette_words`;
3. set `palette_pending`;
4. let the existing fixed-order VBlank DMA publish it.

While the fire region is active, the retained mode-8 `$59AD4` event is still authoritative for timing.
`genesistan_palette_hook_59ad4` may recognize `(active_region, arcade bank $14, source phase)` and copy the
corresponding **precomputed complete 16-word row**. It must not convert colors, inspect pixels, or solve a
palette at runtime. This is one event every eight retained ticks, not a per-frame optimizer.

Normal ownership coexists only if compile-time analysis proves all Layer-B semantic states for the interval
are represented. A legitimate Layer-B update must never be dropped. If one can occur, the compiler must
emit the Cartesian set of required Layer-B state × fire phase rows and the semantic producer must select
them, or the region is rejected. Do not build a second live L2 shadow.

On release, install the generated nonregion Layer-B state selected by the same retained semantic state. A
blind static “restore R1 palette” is insufficient where `$FFFF` retain history matters. If the exact release
state cannot be generated or re-established by the authoritative Layer-B producer, implementation must
stop.

Lifecycle requirements:

- **death/respawn:** scene activation/`fg_boundary_install` recomputes region from the restored record; no
  stale active-region flag survives scene reset;
- **reverse traversal:** record 19→18 activates, 18→17 releases; selection is record-derived, not direction
  derived;
- **direct start:** the first install selects record 18 before visibility and installs the correct phase/base;
- **attract:** identical retained progression path; no input-specific branch;
- **scene/READY/Stage Clear/inter-round:** no region for those scene IDs, so the current ownership paths and
  PROMT-ID-0141 frontend Line-2 multiplex remain unchanged;
- **sparse retain:** compiled entry and release rows must be computed from the actual semantic resident
  state; `$FFFF` is never interpreted as black or “free.”

## 16. Strategy matrix and independent recommendation

| Strategy | Fidelity | Runtime/ROM | Composer/Python | Layer-B risk | Reversal/death | Future value |
|---|---|---|---|---|---|---|
| A existing colors | low; static, severe merges | minimal / none | small | low | naturally safe | low |
| B slot lease | potentially medium | small | high proof burden | **unacceptable now: 0 proven slots** | fragile without exact restore | medium |
| C composite regional L2 | highest possible within 15 entries; preserves phase timing | event copies; ~100–200 ROM bytes plus pattern variants | substantial but coherent | manageable only after writer/visibility proof | strong with record schedule | **high** |
| D alternate full line | potentially high fire fidelity | small palette cost, large consumer reindex cost | high | moves risk to player/enemy/castle owners | complex | low for this scene |

**Independent recommendation:** implement the generic analyzer and Palette Residency Region architecture,
then use Strategy C only if the generated record-18 report proves a closed Layer-B state and an acceptable
15-entry composite after explicit Tighe-approved merges. Strategy A is the safe fallback if Tighe wants an
immediate static improvement. Do not implement Strategy B from current evidence and do not lease another
complete line.

The recommendation is conditional because current evidence proves the fire side exactly but does not prove
record-18 z-composited Layer-B index occupancy or absence of every in-window Layer-B update. Guessing those
facts would violate the very residency semantics the feature is intended to protect.

## 17. Validation and staged implementation roadmap

1. **Analyzer/evidence:** generate record-18 viewport/occlusion, L2 source-index, writer, and `$FFFF`
   dependency evidence; compare against original arcade MAME.
2. **Schema:** add `palette_regions` and decision references with validation; no runtime change.
3. **Composer UX:** Palette Regions, Effect Groups, occupancy grid, explicit merges, and phase preview.
4. **Offline compiler:** emit global effect maps, region pattern variants, complete phase rows, schedule, and
   manifest; prove deterministic rebuilds.
5. **Runtime support:** select only at existing record/scene semantic boundaries and retained mode-8 events;
   stage through the existing palette buffer/DMA.
6. **Fire authoring:** Tighe chooses and approves the reduction/composite; update Test 2.0 and
   `specs/palette_decisions.json` together only then.
7. **Automated verification:** schema/decision coverage; zero unapproved MRD violations; every used source
   index mapped; exact region interval; no overlap owner; all dynamic states covered; source/profile/output
   hashes; R1-S2 package/Plane-A/Plane-B differential outside record 18 is zero.
8. **Runtime validation:** original arcade and Genesis NTSC phase cadence/screenshots; entry from 17, exit to
   19, both reversals, death at/beside the pit, checkpoint/respawn, direct R1-S2, natural R1-S1→R1-S2,
   attract, READY, Stage Clear, and Round-2 entry. Tighe remains the visual acceptance authority.
9. **Generalization:** only after acceptance, use the same region mechanism for another proven effect; do not
   generalize from an invented R1-S2 sprite member.

## 18. Unresolved evidence and explicit stop conditions

- The current corpus proves record 18 and exact fire geometry, but does not provide a full camera-route
  timestamp for the last visible fire pixel. Record `[18,18]` is the safe semantic envelope.
- No generated z-composited record-18 Layer-B index-usage artifact exists. Therefore no L2 lease is proven
  and the exact minimum composite merges remain unresolved.
- The current display evidence shows L2 index 1 changing and 2..15 stable in sampled frames; it does not
  prove that no legitimate Layer-B writer occurs during the complete fire interval.
- The exact Tighe-approved fire reduction and its palette decision do not yet exist. The sample maps are
  analysis only.
- Whether the final composite should preserve all nine distinct phase colors or a four-to-seven-color
  artistic subset is a Tighe decision after combined preview.

Any future implementation must stop if it cannot prove record-local L2 occupancy, cover every active
Layer-B semantic state, restore sparse-retained state, or obtain explicit approval for every MRD merge.

## Delivery declaration

- Production changes: **NONE**
- Palette Composer changes: **NONE**
- Test 2.0/profile changes: **NONE**
- Palette decision changes: **NONE**
- Generated runtime/build artifacts: **NONE**
- ROM produced: **NONE**
- Build number consumed: **NONE**
- Push: **NONE**

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0148`
