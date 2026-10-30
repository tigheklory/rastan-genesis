# Build 0519 ROM audit and six-round feasibility

Prompt continuation: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0035`

## Outcome

Build 0519 is **4,054,712 bytes**, leaving **139,592 bytes** below the 4 MiB limit of 4,194,304. Its SHA-256 is `ab34fc39a1cf635e0cdd1c69a37b6e0d46eab90f4ec1104bf7e2962eced43706`.

The current asset behavior cannot scale to a complete six-round game within 4 MiB. The central current-behavior projection is **7,673,400 bytes**. Applying proven compact descriptor indexes and measured low-risk deduplication reduces the central projection to **5,207,896 bytes**, still **1,013,592 bytes over 4 MiB**. A shared-library design projects **3,969,176 bytes centrally**, with a range of **3,749,176–4,319,176**. Therefore 4 MiB is feasible only if scene growth is converted to shared indexed libraries and the high-side uncertainty is closed before later-round authoring.

This was a read-only audit. It produced no ROM, consumed no build number, and changed no production file.

## Semantic boundary

The audit observes the established boundary `arcade semantic producer -> native Genesis VDP/SAT assets`. It does not propose restoring any PC080SN/PC090OJ chip tail, shadow RAM, virtual chip address space, or runtime chip emulation. Recommended compaction remains build-time preparation plus native lookup of final plane/SAT resources.

## Evidence and method

- Audited ROM: `/home/tighe/projects/rastan-genesis/dist/rastan-direct/rastan_direct_video_test_build_0519.bin`.
- Exact-build source/output snapshot: `/tmp/rastan-prompt0033-isolated`, commit `ca8b333`.
- A map-only relink generated `build0519_link.map` and `build0519_relinked.elf` in this audit directory. The relinked ELF SHA-256, `7861de42a486b0ffa051fe635bd64c485720c1f7bf3ff59c517ea5775e719f7b`, exactly equals the preserved Build 0519 ELF SHA-256. This establishes the section/symbol ownership used below without building or publishing another ROM.
- Exact physical accounting is non-overlapping and reconciles to 4,054,712 bytes. Logical subround references are many-to-many; shared corpora are not falsely multiplied by 18.
- Exact duplicates use byte identity. Theoretical identity-remap ceilings are separated from directly removable copies.
- Projections are estimates, not measured future assets. Every formula and uncertainty range is recorded below and in the machine-readable outputs.

## 1. Exact ROM byte accounting

| Category | Exact bytes | Share |
|---|---:|---:|
| Maps/descriptors/preload data | 1,519,770 | 37.48% |
| Graphics patterns | 1,081,998 | 26.68% |
| Audio (driver/catalog/9 streams) | 610,558 | 15.06% |
| Retained relocated arcade code/data | 388,826 | 9.59% |
| Sprite metadata | 311,960 | 7.69% |
| Padding/alignment | 84,400 | 2.08% |
| Native/bootstrap/crash code | 28,906 | 0.71% |
| Front-end/HUD/item metadata | 27,048 | 0.67% |
| Palettes/LUTs | 1,246 | 0.03% |
| **Total** | **4,054,712** | **100.00%** |

Top-level address layout:

| ROM range | Exact bytes | Owner |
|---|---:|---|
| `0x000000–0x000372` | 882 | Genesis bootstrap/header |
| `0x000372–0x00117E` | 3,596 | preserved-low fill |
| `0x00117E–0x060058` | 388,826 | retained relocated arcade content |
| `0x060058–0x070000` | 65,448 | low-ROM gap |
| `0x070000–0x344650` | 2,967,120 | native wrapper executable and asset libraries |
| `0x344650–0x348000` | 14,768 | audio alignment |
| `0x348000–0x3DCDCA` | 609,738 | all nine native audio streams |
| `0x3DCDCA–0x3DD000` | 566 | crash-section alignment |
| `0x3DD000–0x3DDEB8` | 3,768 | crash/diagnostic executable |

Important exact asset owners inside the wrapper include:

- PC080SN pattern corpus: **524,288 bytes**, all 16,384 8x8 tile codes.
- PC090OJ editor corpus: **540,032 bytes** = 524,288-byte 4,096-cell base corpus + 15,744 bytes of 123 palette-variant cells.
- Gamewide sprite tables/metadata: **311,960 bytes**.
- All-round native metatile index + unique records: **695,614 bytes**; Plane-B visual records add **2,802 bytes**.
- R1/R2 Plane-A/Plane-B scene, row, pan, and boundary packages: **412,280 bytes**.
- Two authored visual contexts: **340,096 bytes**.
- Nine audio streams plus driver/catalog: **610,558 bytes**; later rounds do not require another soundtrack corpus.

The complete 76-row physical ledger with address, owner, references, and source is [rom_assets.csv](../../analysis/rom_audits/build_0519_prompt0035/rom_assets.csv).

### Exact Build 0517 -> 0519 growth

The measured delta is **+327,680 bytes**:

| Change | Bytes |
|---|---:|
| Executable palette installer | +200 |
| Authored descriptor visual asset | +340,096 |
| Row map | +2,304 |
| Boundary package | +2,896 |
| Alignment/padding reduction | -17,816 |
| Pattern corpus growth | 0 |
| Palette-table growth | 0 |
| **Net** | **+327,680** |

The audio image is byte-identical and merely moved by `+0x50000`. There is no second 512 KiB PC080SN corpus: the fixed corpus is reindexed in place.

## 2. Eighteen-subround inventory

All subrounds use the already-linked 524,288-byte PC080SN corpus, 540,032-byte PC090OJ corpus, gamewide player/HUD/frame tables, retained logic, and complete soundtrack. Those shared dependencies must be counted once, not once per row.

| Subround | Native maps | Authored visual/palette context | Records | Actor/effect coverage or gap |
|---|---|---|---:|---|
| R1-S1 | present | present | 16 | Lizardman `004B`, Chimera `00D0`, Four-Armed Insect `02E8`, Valkyrie `0241`; map-trigger split unknown |
| R1-S2 | present | present | 6 | same R1 field families; map-trigger split unknown |
| R1-S3 | present | missing | 1 | boss base `033E`, R1 variant/palette |
| R2-S1 | present | missing | 16 | R1 common + `0420`, `0400`; map-trigger split unknown |
| R2-S2 | present | missing | 6 | same R2 field set; map-trigger split unknown |
| R2-S3 | present | missing | 1 | boss base `033E`, R2 variant/palette |
| R3-S1 | absent | missing | 16 | R2 field + `03B3`; map-trigger split unknown |
| R3-S2 | absent | missing | 6 | same R3 field set; map-trigger split unknown |
| R3-S3 | absent | missing | 1 | boss base `033E`, R3 variant/palette |
| R4-S1 | absent | missing | 16 | `004B,00D0,02E8,03B3,06E2,0889,0400`; map-trigger split unknown |
| R4-S2 | absent | missing | 6 | same R4 field set; map-trigger split unknown |
| R4-S3 | absent | missing | 1 | boss base `033E`, R4 variant/palette |
| R5-S1 | absent | missing | 16 | `004B,00D0,02E8,0420,03B3,043A,0889,0400`; map-trigger split unknown |
| R5-S2 | absent | missing | 6 | same R5 field set; map-trigger split unknown |
| R5-S3 | absent | missing | 1 | boss base `033E`, R5 variant/palette |
| R6-S1 | absent | missing | 16 | `004B,00D0,02E8,0420,01CB,03B3,0889,0400`; map-trigger split unknown |
| R6-S2 | absent | missing | 6 | same R6 field set; map-trigger split unknown |
| R6-S3 | absent | missing | 1 | boss base `033E`, R6 variant/palette |

Special Flying Demon `0129`, Large Bat `03F6`, Small Bat `0268`, spear `050B`, boulder `0D5F`, and fireball `019D` are map-marker triggered. Existing evidence does not resolve their exact S1/S2 allocation; it is deliberately recorded as **UNKNOWN** rather than invented. All six bosses share base `033E`, but each round still needs variant/palette proof.

The detailed [subround_inventory.csv](../../analysis/rom_audits/build_0519_prompt0035/subround_inventory.csv) includes shared pattern dependencies, native status, map/descriptor gaps, palettes, actors, and VRAM implications for every row. Its per-row existing-allocation proxies are allocation aids only; exact physical ownership remains in [rom_assets.csv](../../analysis/rom_audits/build_0519_prompt0035/rom_assets.csv) because compact aggregate tables have many-to-many consumers.

## 3. Exact duplication and savings

### Direct or structurally proven opportunities

| Opportunity | Measured potential | Qualification |
|---|---:|---|
| Auxiliary pattern records already present in PC080/PC090 corpora | **14,048** | exact byte identity, each stored auxiliary record counted once even if found in both corpora |
| Scene/Plane-B/pan map rows shared through one dictionary | **30,720** | 832 stored rows, 579 unique; 32,384 duplicate bytes less a 1,664-byte u16 index |
| Current two authored dense indexes -> live-band u32 pointers | **262,144** | 284,672 -> 22,528 bytes; native lookup shape change |
| Current two authored dense indexes -> live-band u16 record IDs | **273,408** | 284,672 -> 11,264 bytes; alternative to the u32 scheme, not additive |

The 55,424-byte authored descriptor payload already consists of 866 globally unique 64-byte records and is not duplicate waste. The existing deduplicated native row maps similarly must not be counted as an uncompressed duplicate store.

Pairwise auxiliary-to-corpus matches total 17,408 bytes, but that number double-counts records found in both base corpora. The deletion ceiling is the non-overlapping **14,048 bytes** used in all projections.

### Identity-remap ceilings, not direct deletions

| Corpus | Stored units | Unique units | Raw repeated bytes | Meaning |
|---|---:|---:|---:|---|
| PC080SN, 32-byte tiles | 16,384 | 10,705 | 181,728 | requires a tile-code identity remap |
| PC090OJ, 128-byte cells | 4,219 | 3,550 | 85,632 | requires sprite-code/frame identity remap |
| PC090OJ, 32-byte subtiles | 16,876 | 9,800 | 226,432 | alternative finer-grained redesign; cannot be added to cell savings |

These repeated-byte ceilings are not safe to realize by deleting patterns in place: semantic tile/cell codes and native consumers must be redirected. Only the shared-library scenario uses the mutually compatible PC080 tile + PC090 cell ceilings, totaling **267,360 bytes**.

## 4. Why the authored context grew so sharply

Each current authored context has a dense u32 pointer for the full 35,584-entry arcade descriptor address span: **142,336 bytes per context**. Only two contexts exist, R1-S1 and R1-S2, producing a 284,672-byte index plus the 55,424-byte deduplicated payload.

Current live addressability is only:

- R1-S1: 4,096 entries = 16 records x 16 strip tables x 16 columns.
- R1-S2: 1,536 entries = 6 records x 16 strip tables x 16 columns.
- Combined: 5,632 entries.

This is why the correct current u32 band index is 22,528 bytes, not 284,672. Across all 18 contexts, blindly retaining this dense shape would consume **2,562,048 bytes** of index alone. Exact live-band u32 indexes for the six `16/6/1` record groups consume **141,312 bytes**, a **2,420,736-byte** six-round structural saving.

## 5. Six-round projections

| Scenario | Low | Central | High | Central vs 4 MiB |
|---|---:|---:|---:|---:|
| Current behavior | 7,593,400 | **7,673,400** | 7,833,400 | +3,479,096 |
| Conservative proven dedup | 5,127,896 | **5,207,896** | 5,367,896 | +1,013,592 |
| Shared indexed library | 3,749,176 | **3,969,176** | 4,319,176 | -225,128 |

### Projection formulas

Current behavior:

- Begin at exact Build 0519 size 4,054,712.
- Missing authored contexts use the measured current average: 142,336-byte dense index + 27,712-byte half-share of the current deduplicated payload = 170,048 per context.
- Every absent R3–R6 scene adds 12,288 bytes of A/B scene maps plus proportional measured row-map and boundary-package growth by its `16/6/1` record count.
- The resulting missing-scene/context sum is 3,478,688 bytes.
- Add 60,000 / 140,000 / 300,000 bytes for unresolved later-round preloads, palette variants, and executable growth.

Conservative proven dedup:

- Start with each current-behavior bound.
- Subtract the exact all-context live-band u32 structural saving, 2,420,736.
- Subtract measured row dictionary savings, 30,720.
- Subtract non-overlapping exact cross-library copies, 14,048.
- Do not assume base corpus identity remapping.

Shared indexed library:

- Start from Build 0519.
- Compact the current authored index to live u16 IDs, measured saving 273,408.
- Apply the measured 30,720-byte row-dictionary and 14,048-byte cross-library opportunities.
- Apply the 267,360-byte PC080-tile + PC090-cell identity-remap ceiling.
- Add a bounded 280,000 / 500,000 / 850,000 bytes for all missing compact maps, record IDs, palettes, preload lists, variants, and code.

The shared-library bounds have the greatest model risk because later-round semantic authoring is incomplete. Its central case fits with **225,128 bytes** spare; its high case exceeds 4 MiB by **124,872 bytes**. Thus “4 MiB feasible” is conditional, not proven.

## 6. VRAM and runtime implications

- The ROM corpora are shared libraries; they do not imply simultaneous VRAM residency.
- Scene-scoped residency/preload lists remain necessary. Do not attempt to load the 512 KiB PC080SN or 527.4 KiB PC090OJ libraries wholesale into Genesis VRAM.
- Index compaction trades small native lookup work for large ROM savings. It does not require shadow RAM or runtime PC080SN/PC090OJ emulation.
- Identity-remapping the PC080SN/PC090OJ corpora requires consumer-complete translation of semantic tile/cell IDs. The raw duplicate counts are ceilings until that proof exists.
- u16 descriptor record IDs are preferable to u32 pointers only if payload-base resolution and all consumers are verified; otherwise the u32 live-band scheme is the lower-risk first step.

## 7. Ranked recommendations

1. **Replace dense authored descriptor indexes with record-band indexing before authoring another context.** This is the gating change. The exact current u32 saving is 262,144 bytes, and the projected all-context saving is 2,420,736 bytes. Preserve offline compilation and final native VDP realization.
2. **Make future contexts reference one globally deduplicated 64-byte descriptor-record pool.** The current pool is already deduplicated; extend it rather than emitting per-context payload copies.
3. **Unify scene-fill, Plane-B-fill, and pan rows behind one exact row dictionary.** The present data proves a net 30,720-byte saving after its u16 index.
4. **Eliminate the 14,048 bytes of non-overlapping auxiliary patterns already available in a canonical corpus**, after validating every slot consumer and preload route.
5. **Build an explicit PC080SN tile-identity remap.** Its 181,728-byte ceiling is valuable, but it is not a deletion-only optimization and must cover all map/preload consumers.
6. **Then evaluate PC090OJ whole-cell identity remapping.** The compatible whole-cell ceiling is 85,632 bytes. Do not simultaneously claim the alternative 226,432-byte subtile ceiling.
7. **Require a size budget at every remaining authored context.** Use the shared-library high bound as the stop gate; 124,872 bytes still needs removal or tighter measurement.
8. **Resolve actor/effect S1/S2 map-marker provenance before per-subround sprite-variant budgeting.** The base corpus and gamewide frame tables exist, but later-round variant/palette demand remains uncertain.
9. **Do not optimize audio first.** The complete nine-stream audio package is already shared and stable; current scaling failure is dominated by descriptor/index behavior.

## 8. Charts and machine-readable outputs

- [chart_A_rom_usage.png](../../analysis/rom_audits/build_0519_prompt0035/chart_A_rom_usage.png): exact Build 0519 ROM ownership.
- [chart_B_subrounds.png](../../analysis/rom_audits/build_0519_prompt0035/chart_B_subrounds.png): all 18 subrounds, shared dependencies, allocation proxies, and estimated gaps.
- [chart_C_duplication.png](../../analysis/rom_audits/build_0519_prompt0035/chart_C_duplication.png): direct, structural, and theoretical savings separated by class.
- [chart_D_projection.png](../../analysis/rom_audits/build_0519_prompt0035/chart_D_projection.png): three six-round scenarios with low/high bounds.
- [chart_E_cumulative.png](../../analysis/rom_audits/build_0519_prompt0035/chart_E_cumulative.png): current-behavior cumulative growth through Round 6.
- [rom_assets.csv](../../analysis/rom_audits/build_0519_prompt0035/rom_assets.csv): exact non-overlapping physical ledger.
- [subround_inventory.csv](../../analysis/rom_audits/build_0519_prompt0035/subround_inventory.csv): complete 18-subround logical inventory.
- [duplication_opportunities.csv](../../analysis/rom_audits/build_0519_prompt0035/duplication_opportunities.csv): savings, compatibility, and required mechanism.
- [projection_scenarios.csv](../../analysis/rom_audits/build_0519_prompt0035/projection_scenarios.csv): low/central/high numeric results.
- [audit_summary.json](../../analysis/rom_audits/build_0519_prompt0035/audit_summary.json), [duplication_analysis.json](../../analysis/rom_audits/build_0519_prompt0035/duplication_analysis.json), and [projection.json](../../analysis/rom_audits/build_0519_prompt0035/projection.json): full machine-readable evidence.
- [build_audit.py](../../analysis/rom_audits/build_0519_prompt0035/build_audit.py): reproducible read-only analysis/generation script. Set `RASTAN_AUDIT_SOURCE_ROOT` to the exact Build 0519 source/output checkout when regenerating.

## Final feasibility decision

**No:** the established current asset behavior will not fit a complete six-round game in 4 MiB.

**Conditionally yes:** a complete game can plausibly fit if dense per-context descriptor indexing is retired immediately, future scenes share global descriptor/row/pattern libraries, and later-round maps/palettes/variants remain within the measured shared-library budget. The central shared-library estimate has 225,128 bytes of headroom, but the high estimate is 124,872 bytes over; one more evidence-driven budget pass is required before treating 4 MiB completion as guaranteed.
