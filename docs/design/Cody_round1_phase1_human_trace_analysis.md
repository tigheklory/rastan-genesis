# Cody - Independent Round 1 Phase 1 Human Trace Analysis

## 1. Phase 0

- **Classification:** INFRASTRUCTURE / TRACE + SOURCE FORENSICS.
- **Task scope:** independent analysis of the completed Build 0348 human trace. No build, ROM, production-source, specification, or generated-output change is authorized.
- **Relevant priors:** KF-010 (arcade FG is Genesis Plane A), KF-015 (raw-Y negation plus the established `+8` bias), KF-019 (frame sampling is not instruction-execution proof), KF-030 (address-map coverage is not semantic proof), KF-068 native-video semantic-leaf policy, and KF-072 (superseding the reverted Build 0226 ring guidance in KF-071).
- **Rediscovery-hazard findings touched:** the native semantic-cut rule and the distinction between runtime code mapping and runtime data-pointer conversion. This report does not infer a fixed relocation delta.
- **Deferred-appendix context:** older all-zero/blank-plane and transitional projector findings do not describe this Build 0348 failure. The current trace has changing Plane A staging checksums and active dirty-row publication.
- **Task relationship:** extends OPEN-001 and OPEN-018 evidence for native PC080SN/Plane A completion; it does not close either issue.
- **Open/closed issues touched:** OPEN-001 and OPEN-018. No closed issue is reopened and no issue ledger update is warranted by this analysis-only task.
- **Contradiction of a CONFIRMED or STRONG prior:** NONE. KF-072's warning against the reverted 0226 ring rewrite is preserved.
- **Independent evidence boundary:** the forensic conclusion and initial complete 24-section report were produced before reading `docs/design/Andy_round1_phase1_human_trace_analysis.md`, Andy's AGENTS_LOG entry for that analysis, or any message containing Andy's conclusion. A later final-validation pass occurred only after that independent report existed; all resulting refinements in this report are derived from the raw trace, authoritative arcade source formula, Build 0348 ROM bytes, current source, and generated maps rather than from Andy's conclusion. Permitted prior evidence included `docs/design/Andy_genesis_round1_phase1_human_trace_harness.md` and `docs/design/Cody_audit_andy_semantic_epoch_gate_stop.md`.

## 2. Raw Trace Identity And Hashes

Trace directory:

`states/traces/rastan_phase1_human_trace_20260907_220218/`

Metadata establishes:

- machine: Genesis NTSC
- ROM: Build 0348
- ROM SHA-256: `fac088eb0f8e9d374af80d9381aeecfe20be2ec6138ab688cfc6d0c45db1bf6b`
- capture start: `2026-09-08T02:02:21Z`
- capture end: `2026-09-08T02:06:04Z`
- external frames: 13,383
- duration: approximately 223 seconds, consistent with a normal human-play session
- marker key: `M`
- `USER_MARK` events: 15

Raw-file hashes:

| File | Bytes | SHA-256 |
|---|---:|---|
| `trace_metadata.txt` | 541 | `8c2255a2a88a010d1d8c37f0df93f785598969b49cdebe66662928e3a03cb9c0` |
| `phase1_frames.tsv` | 1,691,305 | `a938e10e9ce8e2d605e8ca37abd8ad8f962cd5bf38e30f421da6db954355ba69` |
| `phase1_events.tsv` | 115,109 | `30bda03f6f2f2c3206840e74aad32b6a312da054f579c4c84d44245cdb4915e1` |
| `SHA256SUMS.txt` | 253 | `09ba2cdd2bd2d2602e3fca5255d3086a8d8347e92f1bf9c80beffbc01486879a` |

`sha256sum -c SHA256SUMS.txt` passed for every listed raw artifact. The raw files were not modified.

## 3. Tighe's Visual Observations

Accepted first-hand observation:

1. Vertical scrolling visibly makes Layer A wrong.
2. Pressing `M` records the visible failure after it is noticed; the marker frame is not assumed to be causal.
3. Scrolling right causes newly entering Layer A tiles to be correct.
4. Those newly populated tiles remain correct until another vertical scroll makes Layer A wrong again.

This report leads with **Round 1 Phase 1 map segment N**. Internal `active_record` and residency-package IDs are included secondarily.

## 4. USER_MARK Inventory

All 15 marks occurred with selector 0. None coincided exactly with a map-segment or residency-package transition.

| Mark frame | Human map segment | Internal record | Package | FG X | FG Y | Plane A checksum |
|---:|---:|---:|---:|---:|---:|---:|
| 1546 | 1 | 1 | 0 | 394 | 261 | `03171322` |
| 2714 | 3 | 3 | 5 | 259 | 329 | `0316C357` |
| 3933 | 4 | 4 | 2 | 439 | 382 | `03175008` |
| 4190 | 4 | 4 | 2 | 384 | 489 | `0316C114` |
| 4592 | 5 | 5 | 2 | 36 | 425 | `03164223` |
| 4843 | 5 | 5 | 2 | 485 | 297 | `031695A9` |
| 5101 | 5 | 5 | 2 | 419 | 261 | `0316A03E` |
| 5274 | 5 | 5 | 2 | 394 | 261 | `03168B9F` |
| 5772 | 6 | 6 | 2 | 6 | 321 | `0317ACDC` |
| 6773 | 7 | 7 | 2 | 478 | 261 | `03186372` |
| 8693 | 11 | 11 | 3 | 326 | 350 | `031930E3` |
| 8977 | 11 | 11 | 3 | 265 | 489 | `03171F14` |
| 9792 | 12 | 12 | 3 | 326 | 402 | `031ABC50` |
| 11329 | 13 | 13 | 4 | 12 | 261 | `0317B99A` |
| 12627 | 15 | 15 | 4 | 290 | 336 | `031859E2` |

The trace contains 233 Y-boundary events, 981 X-boundary events, and 19 frames where both axes crossed. It contains no `DUAL_AXIS_PUBLICATION` event. That absence is not proof that no native publication occurred; the harness samples legacy publication counters at `frame_done`, while the current selector-0 native path writes staging directly.

## 5. Failure Timelines

For each mark, the table identifies the preceding Y-boundary event associated with the visible-failure regime. `fg_rows=0` on the event line is a sampling-phase observation, not a conclusion that the row producer did not run; the dirty mask is consumed and cleared during VBlank before many `frame_done` samples.

| Mark | Segment/package at mark | Preceding Y boundary | First later X boundary | First later Y boundary |
|---:|---|---:|---:|---:|
| 1546 | 1 / 0 | 1450 | 1603 | 2597 |
| 2714 | 3 / 5 | 2634 | 2796 | 3102 |
| 3933 | 4 / 2 | 3885 | 4126 | 3968 |
| 4190 | 4 / 2 | 4137 | 4245 | 4381 |
| 4592 | 5 / 2 | 4545 | 4647 | 4663 |
| 4843 | 5 / 2 | 4780 | 4893 | 4919 |
| 5101 | 5 / 2 | 4992 | 5148 | 5663 |
| 5274 | 5 / 2 | 4992 | 5381 | 5663 |
| 5772 | 6 / 2 | 5692 | 5843 | 6041 |
| 6773 | 7 / 2 | 6671 | 6883 | 7602 |
| 8693 | 11 / 3 | 8647 | 8871 | 8733 |
| 8977 | 11 / 3 | 8920 | 9020 | 9616 |
| 9792 | 12 / 3 | 9746 | 10044 | 9838 |
| 11329 | 13 / 4 | 11260 | 11363 | 12437 |
| 12627 | 15 / 4 | 12494 | 12673 | 13238 |

Marks 3933, 8693, and 9792 have another Y crossing before the first subsequent X crossing. They therefore contain recurrence before the later horizontal recovery opportunity. The other marks provide a direct `Y failure -> mark -> X recovery opportunity -> next Y` ordering.

The trace cannot label a prior frame as visually clean because it contains machine state rather than screenshots. The last clean-looking boundary is therefore constrained by Tighe's observation: it is before the preceding Y-driven visible failure, not an inferred checksum threshold.

## 6. Right-Scroll Recovery Timelines

In the trace convention, Tighe's rightward world progression usually appears as decreasing/wrapping Plane A scroll (`dx_fg < 0`); this is why a positive human direction does not require a positive numeric delta. Every mark is followed by an X-boundary event and then a Plane A checksum change.

| Mark | First X boundary after mark | First checksum change after X boundary | New checksum | First sampled dirty row after X boundary | Dirty mask |
|---:|---:|---:|---|---:|---|
| 1546 | 1603 | 1614 | `03171F27` | 1626 | `FFFFFFFF` |
| 2714 | 2796 | 2802 | `0316BCD6` | 2818 | `FFFFFFFF` |
| 3933 | 4126 | 4132 | `03168B9D` | 4132 | `FF000000` |
| 4190 | 4245 | 4259 | `0316CF82` | 4259 | `FFFE0000` |
| 4592 | 4647 | 4654 | `03164205` | 4654 | `FFFFFFFF` |
| 4843 | 4893 | 4904 | `03168FCD` | 4904 | `FFFFFFFF` |
| 5101 | 5148 | 5162 | `03169766` | 5162 | `00000FFF` |
| 5274 | 5381 | 5391 | `03168179` | 5391 | `007FFFFF` |
| 5772 | 5843 | 5854 | `0317AF0E` | 5863 | `FFFFFFFF` |
| 6773 | 6883 | 6894 | `03188261` | 6894 | `FFFFFFFF` |
| 8693 | 8871 | 8874 | `03179983` | 8875 | `00000020` |
| 8977 | 9020 | 9030 | `03173013` | 9030 | `FFFFFFFF` |
| 9792 | 10044 | 10061 | `031980CF` | 10061 | `FF80FFFF` |
| 11329 | 11363 | 11372 | `0317D9D2` | 11386 | `80000000` |
| 12627 | 12673 | 12690 | `03186C41` | not sampled within 30 frames | n/a |

The checksum correlation is complete (15/15). A dirty mask is sampled shortly afterward in 14/15 cases; frame 12627 still has the checksum change, but no nonzero dirty mask survives into the 30-frame sample window. The first later X boundary has numeric `dx_fg=-1` in 13 cases, `-2` after mark 3933, and `511` after mark 5772 (the 9-bit wrap representation of `-1`). Thus every listed event has the same human-rightward direction in this scroll convention. The trace does not encode visual correctness, so correctness of those entering cells comes from Tighe's observation; the machine evidence proves that the horizontal interval changes staged Plane A data.

## 7. Recurrence On Next Vertical Scroll

For each marked regime, the event table above identifies the next Y boundary. The user reports that vertical motion makes Layer A wrong again. The strongest repeated state-machine pattern is therefore:

```text
Y boundary / selector-0 no-publish pan route
    -> native row construction without the active-segment `* 0x40` source term
    -> visible failure noticed
    -> USER_MARK
    -> X boundary / selector-0 entering-column route
    -> live rebuilt descriptor-table data staged
    -> checksum changes and entering cells look correct
    -> next Y boundary
    -> segment-zero-relative row construction is used again
    -> visible failure recurs
```

The trace proves the sequence of state transitions and staging changes. The human observation supplies the visible good/bad classification.

## 8. Horizontal Path Static Trace

The active current helper is `genesistan_hook_tilemap_plane_a_selector0_native` at `runtime_genesis_pc 0x000703A0` (`tilemap_hooks.s:229`). It replaces the selector-0 chip-specific publish tail while preserving the arcade semantic strip state. This native-only PC comes from `apps/rastan-direct/out/symbol.txt` and is confirmed by the JMP operand in the preserved Build 0348 ROM at `genesis_rom_offset 0x00055A4A`; it is not presented as an arcade-PC mapping. The copied-program correlations below are resolved exactly through `build/rastan-direct/address_map.json`.

Path:

1. The original arcade selector-0 horizontal control path is rooted at `arcade_pc 0x0557C4` / exact mapped `runtime_genesis_pc 0x0558A4`, with the publish setup at `arcade_pc 0x055808` / `runtime_genesis_pc 0x0558E8`.
2. The helper computes logical column `((strip_group & 15) * 4 + (strip_index & 3)) & 63` (`tilemap_hooks.s:236-245`).
3. It invokes `fg_boundary_transition_step` at `runtime_genesis_pc 0x000725BE` and retains the source-subcolumn result (`tilemap_hooks.s:246-248`).
4. It derives the visible logical top from current staged FG Y scroll (`tilemap_hooks.s:250-256`).
5. Crucially, it consumes the live rebuilt descriptor pointer table at Genesis-WRAM `0x00FF1040` and source/attribute word table at Genesis-WRAM `0x00FF1080` (`tilemap_hooks.s:258-266`).
6. For 16 descriptor segments by four cells, it selects the current semantic metatile, resolves the tile with `fg_cache_resolve` at `runtime_genesis_pc 0x0007260E`, and composes the final Genesis name word (`tilemap_hooks.s:263-308`).
7. Resident cells are written directly to `staged_fg_buffer[(logical_row & 31) * 64 + logical_column]`, and the corresponding physical row bit is set in `fg_row_dirty` (`tilemap_hooks.s:310-325`).

There is no `fg_narrow_desc_table` creation in this current native path. The helper writes final staging directly. Therefore `fg_narrow=0` throughout this trace is expected and cannot be used to deny horizontal publication.

## 9. Vertical Path Static Trace

All marked failures have selector 0. Selector 0 has vertical camera motion that does not pass through the original selector-1/2 row publisher, so Build 0348 adds Genesis-native no-publish pan hooks:

- up: `genesistan_plane_a_pan_publish_entering_rows_up`, `runtime_genesis_pc 0x0007061A` (`tilemap_hooks.s:468`)
- down: `genesistan_plane_a_pan_publish_entering_rows_down`, `runtime_genesis_pc 0x00070672` (`tilemap_hooks.s:504`)

Exact mapped original control sites include:

- `arcade_pc 0x055704` -> `runtime_genesis_pc 0x0557E4` (down hook site)
- `arcade_pc 0x05570C` -> `runtime_genesis_pc 0x0557EC` (down continuation)
- `arcade_pc 0x055790` -> `runtime_genesis_pc 0x055870` (up hook site)
- `arcade_pc 0x055798` -> `runtime_genesis_pc 0x055878` (up continuation)

The hooks:

1. read arcade-owned current FG Y and delta from Genesis-WRAM under A5 (`tilemap_hooks.s:472-484`, `508-520`);
2. derive old/new visible tops with `(-scroll + 8) & 0x01FF`, then divide by eight and mask to 64 logical rows (`tilemap_hooks.s:538-544`);
3. enumerate every entering logical row (`tilemap_hooks.s:486-498`, `522-532`);
4. call `.Lplane_a_publish_logical_row_native`.

The row helper correctly derives a physical resident row as `logical_row & 31`, and row-within-metatile byte offset as `(logical_row & 3) * 8`. Its critical source choice is different from the horizontal helper: source row segment selects one of 16 fixed arcade ROM/data addresses in `.Lplane_a_strip_src_table` (`tilemap_hooks.s:592-603`, table at lines 655-659).

The authoritative original-arcade source formula is established by `map_select_pointers` at `arcade_pc 0x0502CC` and reconstructed in `docs/arcade_reference/pc080sn/map_stream_control.c:51-61` and `map_stream_format.md:43-46`:

```text
descriptor_entry = strip_src_table[row_segment]
                 + (a5@0x013E * 0x40)
                 + (source_group * 4)
```

The Build 0348 vertical helper implements only the first and third terms. It loads `strip_src_table[row_segment]` at `tilemap_hooks.s:592-595` and adds `source_group*4` at line 596, but never adds the current arcade-owned segment `a5@0x013E * 0x40`. Therefore it selects the segment-0 descriptor record for that row/group regardless of the active Round 1 Phase 1 map segment. This is more precise than merely saying the helper does not consult the rebuilt tables: the missing semantic input is exactly the segment displacement used to construct those tables.

Every `USER_MARK` is in a nonzero segment. A raw comparison against authoritative `build/regions/maincpu.bin` confirms that omitting the displacement changes real four-byte descriptor entries in every marked segment:

| Active segment | Entries differing from segment 0 (of 256 strip/group entries) |
|---:|---:|
| 1 | 62 |
| 3 | 70 |
| 4 | 128 |
| 5 | 105 |
| 6 | 80 |
| 7 | 66 |
| 11 | 179 |
| 12 | 179 |
| 13 | 149 |
| 15 | 158 |

For example, row-segment 0/group 0 reads descriptor bytes `000320FC` at arcade ROM/data `0x01691C` under the current helper, while active segment 1 requires bytes `00031000` at arcade ROM/data `0x01695C`. These are data addresses, not PCs.

The fixed arcade ROM/data addresses are converted through the declared descriptor-data range into Genesis runtime data addresses (`tilemap_hooks.s:598-603`). This is a **runtime data-pointer conversion**, not an arcade-PC/runtime-Genesis-PC mapping.

After selecting that fixed source, the helper resolves the tile, writes all 64 final cells for the physical row into `staged_fg_buffer`, and sets the row bit in `fg_row_dirty` (`tilemap_hooks.s:605-648`).

## 10. Source And Destination Coordinate Analysis

| Property | Horizontal selector-0 column | Selector-0 vertical entering row |
|---|---|---|
| Semantic state owner | arcade strip group/index plus live rebuilt descriptor state | arcade Y/delta determines entering row; current segment `a5@0x013E` is omitted from source selection |
| Source table | Genesis-WRAM `0x00FF1040` pointers + `0x00FF1080` words | `.Lplane_a_strip_src_table[row_segment] + source_group*4`; missing `a5@0x013E*0x40` |
| Axis coordinate | logical column from group/index; each descriptor supplies rows | logical row from visible-top crossing; X source from current scroll |
| Destination | `staged_fg_buffer[(row & 31), logical_column]` | `staged_fg_buffer[(logical_row & 31), 0..63]` |
| Dirty metadata | bit for every affected resident physical row | one bit for the entering physical row |
| Commit | centralized Plane A dirty-row DMA | same centralized Plane A dirty-row DMA |

The two paths share the same 32-row resident destination convention and the same VBlank commit. Their earliest concrete difference is the semantic source. The destination formula is internally coherent with the current resident-plane model; no trace evidence shows a wrong physical row calculation.

## 11. Row Dirty Lifecycle

`.Lplane_a_publish_logical_row_native` sets `fg_row_dirty` after writing all 64 row cells (`tilemap_hooks.s:645-648`). The horizontal helper sets bits for every resident row it modifies (`tilemap_hooks.s:323-325`).

`dma_publish_frame` at `runtime_genesis_pc 0x00070248` is the single VBlank publication phase. It calls `vdp_commit_fg_narrow_strips`, which always falls through/branches to `vdp_commit_fg_strips_if_dirty` (`tilemap_hooks.s:3703-3752`; `dma.s:69-74`). `vdp_commit_fg_strips_if_dirty` at `runtime_genesis_pc 0x0007014A` DMA-copies each dirty 64-word row from `staged_fg_buffer` to Plane A VRAM `0xE000 + physical_row * 128`, then clears that bit (`vdp_comm.s:313-345`).

Across the trace, `fg_rows` is nonzero in 1,053 sampled frames, including 1,007 gameplay frames; `FFFFFFFF` appears in 492 gameplay samples. The row-dirty mechanism is active. Zero masks on boundary/marker event rows reflect the frame callback's observation point and VBlank consumption, not a dead commit path.

There is nevertheless an axis-correlated sampling asymmetry worth preserving as a secondary observation. Only 1 of 233 exact `Y_BOUNDARY_CROSS` event frames samples a nonzero FG dirty mask. Looking forward no more than 60 external frames, 223 of 233 Y boundaries are followed by a sampled nonzero mask; 179 occur after 1-5 frames and 10 have no sampled mask in that window. Across all gameplay frames, only 5 of 895 frames with nonzero `dy_fg` sample `fg_rows>0`, while 887 stationary-X/Y frames do. This proves that `frame_done` usually does not observe vertical production metadata in the crossing frame. It does **not** prove that VBlank misses the row, because the same bit is set and consumed between callbacks. It also cannot explain why a generated row contains segment-0-relative descriptors; source selection has already diverged before publication timing matters.

## 12. Narrow Descriptor Lifecycle

The legacy narrow descriptor queue is consumed by `vdp_commit_fg_narrow_strips` and cleared after PIO publication (`tilemap_hooks.s:3703-3748`). It then reaches the dirty-row DMA regardless of whether its descriptor count was zero (`tilemap_hooks.s:3750-3752`).

Build 0348 selector-0 native horizontal publication bypasses descriptor creation and writes final staging directly. Consequently:

- `fg_narrow=0` and `fg_narrow_pend=0` throughout this trace do not mean horizontal publication is absent;
- the Plane A checksum changes after every marked interval's next X boundary;
- row masks, when sampled before VBlank consumes them, carry the direct-staging publication.

## 13. Combined-Axis Ordering

The trace has 19 dual-axis boundary frames but no sampled `DUAL_AXIS_PUBLICATION` event. Only three of the marked sequences encounter another Y boundary before the first later X boundary, and the fault is marked after pure/non-dual Y regimes as well. All 15 marks do not require a same-frame X/Y collision.

Thus a combined-axis ordering defect is not necessary to produce the symptom. It may affect individual frames, but it cannot explain the repeated general pattern. The zero dual-publication count is also weakened by the harness's legacy-counter sampling versus direct native staging.

## 14. Staging Versus Publication Classification

**First failing layer: SEMANTIC SOURCE (STRONG).**

The vertical helper constructs a row and writes final staging. Its source-selection input omits the active segment displacement before staging. The destination, dirty-bit, and VBlank DMA chain are present and active. Horizontal movement then changes `fg_sum` in every marked recovery interval through the live current-table source.

The trace is not a per-cell write trace and does not capture a screenshot at every frame. It therefore cannot pair each visible bad row with its exact descriptor word at instruction granularity. That prevents a `PROVEN` root-cause rating. It does not leave staging versus publication equally plausible: the original formula proves the missing `a5@0x013E*0x40` source term, raw data proves that term changes descriptors in every marked segment, and the shared downstream path works for horizontal updates. The delayed dirty-mask sampling remains a secondary timing observation rather than the earliest divergence.

## 15. Map-Segment And Package Dependence

- failures within a stable map segment/package at the `USER_MARK`: **15**
- failures exactly at a map-segment transition: **0**
- failures exactly at a residency-package transition: **0**

Marks span map segments 1, 3, 4, 5, 6, 7, 11, 12, 13, and 15 and packages 0, 2, 3, 4, and 5. Some marks are temporally near later transitions, but exact transition coincidence is not required. In particular, segment 5/package 2 contains four independent marks while the package stays stable.

This disproves a segment/residency transition as a necessary cause and supports a selector-0 vertical-streaming defect operating within stable segments.

## 16. Original Arcade Semantic Comparison

The original arcade exports establish separate axis-owned publishing semantics:

- `arcade_pc 0x0556A6` (exact mapped `runtime_genesis_pc 0x055786`) handles selector-1 vertical publication.
- `arcade_pc 0x055738` (exact mapped `runtime_genesis_pc 0x055818`) handles selector-2 vertical publication.
- `arcade_pc 0x0557C4`/`0x055808` (exact mapped `runtime_genesis_pc 0x0558A4`/`0x0558E8`) handle selector-0 horizontal publication.
- dispatcher `arcade_pc 0x055948` (exact mapped `runtime_genesis_pc 0x055A2A`) selects strip A at `arcade_pc 0x055968` (`runtime_genesis_pc 0x055A4A`) or strip B at `arcade_pc 0x055990` (`runtime_genesis_pc 0x055A72`).
- both original strip publishers consume the current rebuilt descriptor-pointer table at arcade work-RAM `0x0010D040` and source-word table at arcade work-RAM `0x0010D080`; in Genesis these arcade-work-RAM semantics reside at Genesis-WRAM `0x00FF1040` and `0x00FF1080`.
- descriptor rebuild at `arcade_pc 0x055904` (exact mapped `runtime_genesis_pc 0x0559E6`) refreshes those tables as map commands advance.

The original PC080SN could retain a 64x64 hardware tilemap while selector 0 changed camera Y without a new chip-tail row write. A native Genesis 32-row resident plane needs an entering-row realization for that case. Build 0348 provides such a native helper, but it omits the original source formula's current-segment term. The desired architecture remains `arcade semantic state -> final Genesis Plane A row`; no software PC080SN, C-window shadow, tall projection, or generic chip-address translation is required.

The horizontal path is consequently close to the desired native semantic architecture: it retains current arcade strip/map state and emits final Genesis name words. The vertical selector-0 adaptation is also direct output, not generic dirty-row scaffolding, but its **source contract** is incomplete because it evaluates the descriptor formula as though `a5@0x013E` were always zero.

## 17. Hypothesis Matrix H1-H8

| Hypothesis | Result | Evidence |
|---|---|---|
| H1 - vertical row producer missing/dead | **DISPROVEN** | Up/down pan hooks enumerate entering rows; the helper writes 64 cells and dirties a row. Trace has active row dirty/checksum changes around vertical activity. |
| H2 - vertical row source coordinate wrong | **SUPPORTED** | The authoritative formula requires `strip_base + a5@0x013E*0x40 + group*4`; the current helper omits the middle term. Raw data differs for 62-179 of 256 entries in every marked segment. |
| H3 - vertical destination/ring coordinate wrong | **DISPROVEN** | Both paths use `logical_row & 31`; vertical writes a full physical row and the same dirty-row commit consumes it. No trace evidence identifies a destination mismatch as the primary cause. |
| H4 - row dirty publication metadata lost/cleared | **DISPROVEN** | Dirty bits are set, sampled in 1,053 frames, and consumed by centralized row DMA. Same-frame Y sampling is sparse, but 223/233 Y events are followed by a sampled mask within 60 frames; callback phasing cannot erase the earlier deterministic source error. |
| H5 - combined X/Y ordering bug | **DISPROVEN** | Marks occur after non-dual Y activity across many stable intervals; only 19 dual-axis crossings exist and no dual crossing is required for the observed failure pattern. |
| H6 - horizontal publication repairs bad cells | **SUPPORTED** | All 15 marks are followed by X publication intervals and staging checksum changes; the horizontal path reads current rebuilt tables, and Tighe observes correct newly entering cells. |
| H7 - segment/residency interaction required | **DISPROVEN** | 15/15 marks are within stable segment/package state; 0 occur exactly at either transition. |
| H8 - segment/residency irrelevant to triggering | **SUPPORTED** | The symptom repeats in ten map segments and five packages while selector 0 vertical streaming remains the shared condition. Residency still determines tile availability but is not the trigger shown here. |

## 18. Exact Root Cause

**Root-cause confidence: STRONG.**

Build 0348's selector-0 no-publish vertical pan route computes the entering logical row correctly enough to invoke a full-row producer, but `.Lplane_a_publish_logical_row_native` evaluates the original descriptor-source formula incompletely. It computes:

```text
strip_src_table[row_segment] + source_group*4
```

instead of:

```text
strip_src_table[row_segment] + a5@0x013E*0x40 + source_group*4
```

Thus every marked nonzero segment can receive descriptors from segment 0 during vertical entering-row construction.

Horizontal selector-0 publication uses Genesis-WRAM `0x00FF1040`/`0x00FF1080`, which carry the current arcade-owned rebuilt descriptor state. That producer writes authoritative current-segment tiles into final Plane A staging. This source-contract difference explains why rightward entering columns look correct and why a later vertical row replacement reintroduces wrong content.

The exact earliest machine-state difference is therefore not `fg_row_dirty`, the physical row destination, or VDP commit. It is **the missing active-segment displacement in source-table selection before tile resolution and staging**.

## 19. Confidence And Evidence Limitations

What is proven by machine evidence:

- raw trace identity, duration, integrity, and Build 0348 provenance;
- all 15 marks' frame/state inventory;
- all marks use selector 0 and occur away from exact segment/package transitions;
- X and Y boundary ordering;
- a Plane A checksum change after every marked interval's next X boundary;
- active row-dirty lifecycle and VBlank row-DMA code;
- static horizontal use of live rebuilt tables;
- static vertical omission of the authoritative `a5@0x013E*0x40` descriptor displacement;
- raw descriptor differences for every nonzero segment represented by a marker.

What relies on Tighe's accepted direct observation:

- which frames look wrong;
- that the entering tiles after rightward motion are visually correct;
- that the next vertical movement visibly corrupts Layer A again.

What remains uncaptured:

- instruction-level execution taps (the harness deliberately uses frame sampling because of MAME DRC constraints);
- per-cell source pointer/value at each Y-row write;
- per-frame screenshots tied to each mark;
- a direct original-arcade versus Genesis row-value tuple for the same world coordinate.

Generated-output note: Build 0348 is the score variant. `apps/rastan-direct/out/address_map.json`, whose build input is the score patch manifest, matches the native helper destinations encoded in the numbered Build 0348 ROM. The separately present `build/rastan-direct/address_map.json` has identical copied-program arcade/runtime segment correlations used here but records native helper destinations from a non-score rolling variant shifted by `0x14`. No arcade/runtime correlation in this report is inferred from those native operands.

Those limitations justify STRONG rather than PROVEN confidence. They do not justify another broad trace before defining the narrow correction boundary.

## 20. Recommended Implementation Boundary

No implementation is performed here.

The narrow next boundary is the selector-0 no-publish entering-row producer only:

1. retain the existing arcade Y/delta detection, visible-top calculation, physical resident-row destination, direct final-name-word staging, dirty bit, and VBlank commit;
2. restore the authoritative producer formula by incorporating the current arcade-owned segment term `a5@0x013E*0x40` between the row-segment base and source-group offset; whether implemented directly or via an equivalent live-table derivation, prove equivalence for arbitrary X/Y before coding;
3. prove the row/column orientation against the original semantic tables before coding; do not blindly transpose or reuse the horizontal loop;
4. leave selector-0 horizontal publication unchanged;
5. add no C-window/name-RAM shadow, tall buffer, projector, software PC080SN device, generic dirty framework, or fallback path.

The semantic cut retained is arcade camera/map-descriptor state. The chip-specific tail to remain retired is PC080SN address/tilemap execution. The output remains direct Genesis Plane A staging followed by the existing VBlank commit.

## 21. Open/Closed Issues Impact

- **Open issues touched:** OPEN-001 and OPEN-018.
- **New issues opened:** none.
- **Issues closed:** none.
- **Issues intentionally deferred:** selector-1/2 behavior outside the marked selector-0 symptom, broader residency optimization, Plane B, sprites, palette, collision, audio, and frontend paths.
- **Ledger files modified:** none. This report refines the evidence boundary without changing issue status.

## 22. KNOWN_FINDINGS Impact

**Option A - No new finding to index.** This is a task-local STRONG root-cause analysis awaiting implementation/runtime validation. It is consistent with existing native replacement and Plane A findings. `KNOWN_FINDINGS.md` is not modified.

## 23. Build Status

- Build produced: NO.
- Build counter changed by this task: NO.
- Counter observed: 348.
- Production source changed: NO.
- Specification changed: NO.
- Raw trace changed: NO.

## 24. STOP Status

- Mandatory report completed: YES.
- Analysis scope completed: YES.
- STOP condition triggered: NO.
- Work stops here because implementation and a numbered build were explicitly unauthorized.

## 25. Clarification — USER_MARK is an approximate post-scroll symptom marker

This section amends the timing interpretation above without erasing the original analysis. Tighe
clarified the actual human procedure as:

```text
vertical scrolling occurs
    -> Layer A becomes visibly wrong
    -> vertical scrolling stops
    -> Rastan is usually stationary
    -> Layer A remains visibly wrong
    -> M is pressed sometime afterward
```

Accordingly, each `USER_MARK` is an **approximate symptom marker**: Layer A was visibly wrong at
the marked point after vertical scrolling. It is not the first bad frame, the exact causal Y
boundary, a marker taken during motion, or a controlled latency measurement. The elapsed time
between motion ending and the keypress is human reaction/gameplay time and has no fixed bound in
this capture. All 15 marker-frame samples have `dx_fg=0` and `dy_fg=0`, which is consistent with
the clarified procedure but does not measure how long the camera had been stationary.

### 25.1 Evidence that is unaffected

The following findings do not depend on marker timing:

- **Source/static proof:** the authoritative original-arcade descriptor formula is
  `strip_src_table[row_segment] + a5@0x013E*0x40 + source_group*4`. Build 0348's
  `.Lplane_a_publish_logical_row_native` omits the active-segment term. This is a proven static
  implementation discrepancy regardless of when `M` was pressed.
- **Raw descriptor-data proof:** segment-zero entries differ from the corresponding active-segment
  entries in every nonzero segment represented at a marker. Those byte comparisons are independent
  of frame timing.
- **Human visual correlation:** Tighe directly observed the repeated semantic sequence
  `vertical movement -> persistent wrong Layer A -> later rightward movement produces correct newly
  entering tiles -> another vertical movement makes Layer A wrong again`. The trace places the
  symptom markers in selector 0 and nonzero map segments, but the human observation, not the marker
  timestamp, supplies the visible good/bad classification.
- **Shared downstream path:** the source, staging, dirty-row, and VBlank commit code remains as
  described in Sections 8-11. The clarification changes no source-path fact.

### 25.2 Timing claims that are weakened

The "preceding Y boundary" column in Section 5 now means only the nearest sampled Y-boundary event
before a symptom marker. It must not be read as the necessarily corrupting publication. The listed
interval bounds a period in which the symptom arose according to the human procedure; the trace
does not locate onset within that interval.

Likewise:

- the three sequences with another Y crossing before a later X crossing do not identify which Y
  crossing first produced bad content;
- the Section 7 state-machine diagram is semantic ordering, not an exact frame-by-frame latency
  chain;
- "15 failures within stable segment/package state" means the symptom was visible at 15 stable-state
  marker samples. It does not prove that symptom onset could not have preceded the marker near an
  earlier transition;
- no number of frames between a listed Y crossing and `USER_MARK` is evidence for producer or DMA
  latency.

The earlier exact root-cause conclusion is therefore **refined**, not superseded: the omitted
segment term remains the earliest proven source-contract divergence and remains a **STRONG** cause
of the observed wrong-content behavior, but the trace does not prove that the nearest preceding Y
boundary is the exact instruction-time onset for any individual mark.

### 25.3 Stationary corruption

Persistent visible corruption after vertical movement stops **partially strengthens** the
wrong-content interpretation over a merely late entering-row update. A late row that subsequently
arrived with correct content would be expected to repair that row; instead, Tighe observed Layer A
remaining wrong while stationary until later rightward publication produced correct newly entering
tiles. This is consistent with the vertical helper having already staged and published the wrong
segment-relative content.

This is supporting human evidence, not a controlled duration test. The capture did not mark the
first stationary frame, did not define a settle interval, and did not take instruction-correlated
screenshots, so stationary persistence alone does not prove which write produced the content.

### 25.4 Dirty-mask and callback limits

`fg_rows=0` at `frame_done` does **not** prove absence or delay of row production. The harness reads
`fg_row_dirty` only inside `emu.register_frame_done`. Between two such callbacks, a native producer
can set a row bit and the VBlank commit can DMA that row and clear the bit. Same-frame or
boundary-centered statistics built from these samples therefore cannot establish that no row was
produced, that publication waited until motion settled, or how many emulated frames the operation
took.

The sparse same-sample overlap between `dy_fg != 0` and `fg_rows > 0` remains a callback-phase
observation only. It neither proves nor disproves an additional scheduling issue.

### 25.5 Horizontal recovery and `FFFFFFFF`

The selector-0 horizontal helper computes one semantic entering column from the arcade-owned strip
state and current rebuilt descriptor tables. It then walks the resident logical rows, changes the
one entering-column cell in each eligible physical row, and sets that physical row's bit in
`fg_row_dirty`.

Consequently, `fg_row_dirty=FFFFFFFF` means all 32 physical Plane A rows had at least one changed
cell pending publication. The VBlank consumer then performs one 64-word DMA for each dirty row.
It does **not** prove a full semantic Plane A rebuild: the semantic producer changed a column across
the resident rows, while the existing publication mechanism copied each affected row at 64-word
granularity. Tighe's observation establishes that the newly entering column tiles are correct; the
mask alone does not establish correctness or recomputation of every other cell.

### 25.6 Competing deferred-publication hypothesis

The hypothesis that the **primary** failure is vertical entering-row publication being deferred
until after movement settles is **NOT ESTABLISHED BY THIS TRACE**. Marker timing cannot test it, and
`frame_done` dirty-mask samples cannot observe every set/consume interval. The capture therefore
cannot responsibly classify a scheduling delay as either present or absent.

It remains possible that a separate timing issue exists, but no such issue is needed to explain the
known deterministic source discrepancy: whenever the vertical row helper executes in a nonzero
segment, it evaluates the descriptor source without the required active-segment displacement.
Thus deferred publication is not promoted to the primary root cause and may be revisited only if a
source-only correction leaves a residual timing symptom.

### 25.7 Recommended discriminating experiment

The clean first experiment remains one numbered test build that changes only the selector-0
vertical descriptor-source calculation to include the authoritative `a5@0x013E*0x40` term (or a
proven equivalent live-table derivation). It should leave timing, entering-row destination,
dirty-mask handling, VBlank commit, horizontal publication, and residency unchanged.

Tighe should then repeat the same observable sequence:

```text
vertical movement -> stationary inspection -> rightward movement -> another vertical movement
```

If the vertical corruption disappears without timing changes, that discriminates the missing
segment term as the visible cause. If corruption remains, the unchanged trace/commit machinery can
then be investigated as a secondary boundary without conflating source correction with scheduling.

Reassessment status:

- correct marker classification: **APPROXIMATE SYMPTOM MARKER**;
- source-formula evidence depends on precise marker timing: **NO**;
- missing active-segment term remains established: **YES**;
- current visible-root-cause confidence: **STRONG, not PROVEN**;
- prior root-cause conclusion: **REFINED**;
- production source changed: **NO**;
- raw trace modified: **NO**;
- build produced: **NO**;
- counter remains: **348**.
