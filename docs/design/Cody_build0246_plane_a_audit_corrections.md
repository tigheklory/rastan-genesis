# Build 0246 Plane A Audit Corrections

**Agent:** Cody  
**Date:** 2026-07-31  
**Scope:** focused analysis/documentation correction only  
**Production source changed:** NO  
**ROM produced:** NO  
**Counter changed:** NO, remains Build 0246 / counter 246

## Baseline

- Forward-development build reviewed: Build 0246
- Build 0246 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0246.bin`
- Build 0246 SHA-256: `52919fe447698baf309350217d83ad972d474b96b8f9f7fb361d365c1d97d83e`
- Prior report corrected here: `docs/design/Andy_build0246_initial_plane_a_fill_audit.md`
- Primary trace evidence retained: `states/traces/build0245_plane_a_review_20260730_150627/`
- Address authority: `build/rastan-direct/address_map.json`

This document does not replace Andy's report. It records the conclusions that remain proven and corrects overclaims or unsupported address translations.

## Architecture Compliance

The native replacement policy remains authoritative:

- Preserve the original arcade semantic graphics decision.
- Cut before PC080SN-specific destination/name-RAM execution where safely proven.
- Produce final Genesis Plane A name words through bounded native helpers and the existing VBlank commit.
- Do not use `0xC08000` / PC080SN C-window geometry, virtual name RAM, full-window projectors, or chip-shaped shadows as final production authority.

No production source was edited for this correction.

## Proven Conclusions Retained

The following findings from Andy's initial-fill audit remain accepted:

- Build 0246 initially seeds the 32-row Plane A ring for `visible_top=1`.
- Gameplay begins at `visible_top=23`.
- The scripted camera pan publishes no Plane A rows.
- Logical rows `33..54` are absent from their required physical ring slots after the pan.
- Horizontal selector-0 edge streaming later repairs the screen column-by-column.
- Palette routing is correct for the audited Stage 1 foreground path.
- The defect is not caused by a clear, overwrite, Plane B writer, legacy FG writer, or palette route.

The retained root cause is still: **the arcade can pan vertically inside a 64-row PC080SN window without publishing rows, while the Genesis native Plane A implementation has only a 32-row resident ring and therefore needs explicit entering-row publication or a valid semantic reseed.**

## Address-Map Corrections

Andy’s report included explanatory language equivalent to `Genesis PC = arcade PC + 0x200`. That arithmetic must not be used as proof. The following addresses are resolved through `build/rastan-direct/address_map.json`.

| Arcade PC | Runtime Genesis PC | Segment | Kind | Notes |
|---:|---:|---:|---|---|
| `0x05020A` | `0x05040A` | 170 | `arcade_copy` | scene-init caller context |
| `0x0503DC` | `0x0505DC` | 172 | `arcade_copy` | scene-fill entry |
| `0x050434` | `0x050634` | 182 | `arcade_copy` | fill loop / publication call context |
| `0x0504FA` | `0x0506FA` | 189 | `arcade_copy` | camera-init seed context |
| `0x0508D0` | `0x050AD0` | 191 | `arcade_copy` | camera-init table reference |
| `0x0556A6` | `0x0558A6` | 347 | `arcade_copy` | selector-1 vertical arm |
| `0x05572E` | `0x05592E` | 347 | `arcade_copy` | selector-2 vertical arm entry cited by Andy |
| `0x0556C2` | `0x0558C2` | 347 | `arcade_copy` | selector-1 crossing logic |
| `0x055754` | `0x055954` | 347 | `arcade_copy` | selector-2 crossing logic |
| `0x0556D8` | `0x0558D8` | 347 | `arcade_copy` | selector-1 row cursor setup range start |
| `0x0556F8` | `0x0558F8` | 347 | `arcade_copy` | selector-1 row cursor setup range end |
| `0x05576A` | `0x05596A` | 347 | `arcade_copy` | selector-2 row cursor setup range start |
| `0x055784` | `0x055984` | 347 | `arcade_copy` | selector-2 row cursor setup range end |
| `0x0556FC` | `0x0558FC` | 347 | `arcade_copy` | selector-1 dispatch call to `0x055948` |
| `0x055788` | `0x055988` | 347 | `arcade_copy` | selector-2 dispatch call to `0x055948` |
| `0x055948` | `0x055B48` | 357 | `arcade_copy` | publication dispatcher |
| `0x055704` | `0x055904` | 347 | `arcade_copy` | selector-1 no-publication scroll path |
| `0x055790` | `0x055990` | 347 | `arcade_copy` | selector-2 no-publication scroll path |
| `0x05570C` | `0x05590C` | 347 | `arcade_copy` | selector-1 Y-scroll update range start |
| `0x055718` | `0x055918` | 347 | `arcade_copy` | selector-1 Y-scroll update range end |
| `0x055798` | `0x055998` | 347 | `arcade_copy` | selector-2 Y-scroll update range start |
| `0x0557A4` | `0x0559A4` | 347 | `arcade_copy` | selector-2 Y-scroll update range end |
| `0x055968` | `0x055B68` | 358 | `patched_site` | selector-0 native route site |
| `0x055990` | `0x055B90` | 360 | `patched_site` | selector-1/2 native route site |
| `0x0559B2` | `0x055BB2` | 361 | `arcade_copy` | selector-0 cell producer body after route site |
| `0x055A14` | `0x055C14` | 363 | `arcade_copy` | selector-1/2 cell producer body after route site |
| `0x0558A2` | `0x055AA2` | 347 | `arcade_copy` | post-publication advance |
| `0x0558C6` | `0x055AC6` | 347 | `arcade_copy` | source pointer advance |
| `0x055904` | `0x055B04` | 352 | `patched_site` | descriptor rebuild route site |

No required arcade PC was unmapped in the JSON map. Unsupported `+0x200` reasoning is removed from this correction; where the numeric result matches, it is treated as a JSON-derived fact only.

## Corrected Conclusions

### 1. Shared Vertical Publisher

**Prior overclaim:** one unified trigger cannot cover both initial pan and normal gameplay.

**Corrected classification:** **UNPROVEN.**

What is proven is narrower:

- During the scripted pan, the current selector-1/2 descriptor path is not active.
- Trace evidence shows `selector=0`, `10CA=0`, `10CC=0`, `cursorWr=0`, `fg_writes=0`, while `10B0` and staged Plane A Y scroll move toward the gameplay value.
- Therefore the current selector-1/2 row-publisher path cannot publish the initial-pan entering rows in its existing form.

What is not proven:

- That no higher semantic Rastan map source exists above the PC080SN destination tail.
- That an arbitrary logical Plane A row cannot be derived from scene/stage map state, segment index, source base tables, descriptor structures, and original tile/attribute data.
- That a shared semantic row renderer is architecturally impossible.

A shared row renderer remains a candidate only if it consumes original semantic/source structures and emits final Genesis Plane A rows without using PC080SN C-window geometry as output authority.

### 2. Fall / Upward / Reversal Coverage

**Prior overclaim:** ordinary falls, upward motion, and reversal are covered by the existing selector-1/2 dispatch.

**Corrected classification:** **UNPROVEN / PARTIAL.**

The source docs and disassembly model show selector-1 and selector-2 publication arms:

- selector-1 arm: `arcade_pc 0x0556A6`, JSON mapped to `runtime_genesis_pc 0x0558A6`.
- selector-2 arm: `arcade_pc 0x05572E`, JSON mapped to `runtime_genesis_pc 0x05592E`.
- publication dispatches: `arcade_pc 0x0556FC -> 0x055948` and `arcade_pc 0x055788 -> 0x055948`.
- descriptor rebuild can occur through `arcade_pc 0x055904`, JSON mapped to `runtime_genesis_pc 0x055B04`.

However, there are also no-publication scroll paths:

- selector-1 no-publication path: `arcade_pc 0x055704`, JSON mapped to `runtime_genesis_pc 0x055904`.
- selector-2 no-publication path: `arcade_pc 0x055790`, JSON mapped to `runtime_genesis_pc 0x055990`.

The current evidence does not align every ordinary Genesis `visible_top` tile crossing with an arcade row publication. Therefore the existing evidence is insufficient to claim that downward movement, upward movement, or reversal always supplies every entering row required by the 32-row Genesis resident ring.

### 3. Selector-1/2 Semantic Source

**Current status:** unresolved.

The current Build 0246 selector-1/2 helper consumes:

- semantic-ish arcade state: selector `a5@0x10A8`, strip index `a5@0x10CA`, strip group `a5@0x10CC`, scroll state, and descriptor/source data.
- transitional descriptor tables: `PC080SN_DESC_REBUILD_PTR_TABLE` and `PC080SN_DESC_REBUILD_WORD_TABLE`, which are valid when the arcade descriptor rebuild/publication path has run.
- original source blocks and tile/attribute LUTs to produce final Genesis Plane A words.

This is reusable only for active selector-1/2 publication events after descriptor/source tables are current. It does not yet prove an arbitrary-row renderer for the scripted pan, because the scripted pan does not rebuild or advance the row descriptors.

Unresolved selector-1/2 facts:

- exact entering logical-row formula across selector-1, selector-2, and reversal;
- exact logical column formula for all 64 cells in the row;
- source tile address formula for all 64 cells independent of `0xC08000`;
- direction/reversal behavior beyond the local `sel != 2` sub-index inversion;
- whether the required arbitrary row can be derived without relying on a chip-shaped intermediate.

`0xC08000` may remain an oracle for proof comparisons, but it must not become production authority.

### 4. Initial-Pan Solution Classification

The available options should be classified as follows:

| Option | Status | Notes |
|---|---|---|
| One-time 32-row reseed | diagnostic/fallback candidate only | Could fix the observed symptom if derived from semantic map sources, but risks becoming a symptom patch if it bypasses original producer causality. |
| Native entering-row publication during scripted pan | unresolved | Needs a semantic row source for arbitrary logical rows `33..54` during the pan. |
| Shared semantic row renderer for pan and normal movement | unresolved, not disproven | Architecturally preferred if one semantic source can derive arbitrary rows and active movement rows without C-window authority. |
| Separate native producers | possible but unproven | Only justified if original semantic sources genuinely differ between scene fill/pan and movement publication. |

## No-Publication Path Assessment

For the scripted initial pan, starvation is **proven**:

- `10B0` moves from `0x01FF` toward `0x0149`.
- `staged_scroll_y_fg` follows the pan.
- `fg_writes=0` throughout the pan trace.
- `selector=0`, `10CA=0`, `10CC=0`, `cursorWr=0` stay static.
- Therefore the Genesis 32-row ring does not receive entering rows for the new `visible_top`.

For ordinary selector-1/2 no-publication paths (`0x055704`, `0x055790`), starvation is **not yet fully proven or ruled out**:

- The paths are real no-publication scroll paths.
- Whether they starve the Genesis ring depends on whether `visible_top` crosses an 8-pixel tile boundary without a corresponding `0x055948` dispatch/native helper execution.
- Existing evidence does not yet provide a complete per-crossing table of old/new scroll Y, old/new `visible_top`, selector, dispatch, descriptor rebuild, helper execution, and row staging for down/up/reversal.

## Required Next Boundary

The smallest safe next task is **not implementation**. It is a narrow selector-1/2 and no-publication alignment proof:

1. Use JSON-mapped runtime PCs for `0x0556A6`, `0x05572E`, `0x055704`, `0x055790`, `0x055948`, `0x055904`, `0x055990`, and the native selector-1/2 helper.
2. Trace ordinary downward movement, upward movement, reversal, and one no-publication scroll path.
3. For each relevant frame/event, record:
   - old/new `10B0` and staged Plane A Y scroll;
   - old/new `visible_top`;
   - whether a Genesis ring boundary crossed;
   - selector `10A8`;
   - whether `0x055948` dispatched;
   - whether descriptors rebuilt through `0x055904`;
   - whether `genesistan_hook_tilemap_plane_a_selector12_native` executed;
   - whether the entering logical row reached `staged_fg_buffer` at `logical_row & 31`.
4. In parallel, prove or reject an arbitrary-row semantic source from retained Rastan map/source structures, without final reliance on `0xC08000`.

## STOP Status

STOP is triggered for implementation, not for this documentation checkpoint:

- The semantic arbitrary-row source remains unresolved.
- Ordinary vertical crossings cannot yet be aligned comprehensively with Genesis `visible_top` requirements.
- Existing evidence supports more than one architecture: shared semantic row renderer, separate native producers, or a bounded semantic reseed.

No implementation should be attempted until those facts are distinguished.

## Final Correction Summary

- Initial-fill root cause retained: YES.
- Address-map authority used: YES, `build/rastan-direct/address_map.json`.
- Unsupported `+0x200` mappings removed: YES.
- Shared publisher impossible: UNPROVEN.
- Higher semantic row source found: NO; unresolved in inspected evidence.
- `0xC08000` required as production authority: NO; forbidden as final authority.
- Downward crossings fully covered: UNPROVEN.
- Upward crossings fully covered: UNPROVEN.
- Reversal crossings fully covered: UNPROVEN.
- No-publication paths starve Genesis ring: PROVEN for scripted initial pan; UNRESOLVED for ordinary selector-1/2 paths.
- Selector-1/2 logical row proven: NO.
- Selector-1/2 source mapping proven: NO.
- Current helper reusable: PARTIAL, only for active selector-1/2 publications with current descriptor/source tables.
- First remaining unresolved fact: whether arbitrary logical Plane A rows can be derived from semantic Rastan map/source structures without PC080SN C-window authority.
