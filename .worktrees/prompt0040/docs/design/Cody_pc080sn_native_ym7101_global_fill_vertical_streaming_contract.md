# Cody - PC080SN Native YM7101 Global Fill and Vertical-Streaming Contract

> **POLICY NOTICE (added 2026-07-28):** This document predates the canonical `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). It is retained as an active design reference and **defers to that policy**: where anything here conflicts, the canonical policy governs. Any 'shadow', 'mirror', 'virtual name-RAM', 'tall buffer', or 'projection' referenced here is **transitional compatibility only, never the final architecture** — the target is `arcade semantic decision → native Genesis VDP/SAT`. Agents must state the semantic cut and the chip tail removed before implementing.


**Date:** 2026-07-27  
**Type:** Standalone final implementation contract / documentation only  
**Authority:** Original arcade Rastan World Rev 1 execution and opcode-backed PC080SN references  
**Production source changes:** NO  
**Spec/Makefile changes:** NO  
**ROM/build/counter changes:** NO  
**Build:** NO

## 1. Purpose and Authority

This document defines the final native YM7101 implementation contract for replacing gameplay and gameplay-scene-fill PC080SN visual execution while retaining original arcade semantic ownership.

The arcade code remains the program. Genesis-side code may only execute arcade-owned rendering intent as hardware service. No Genesis-owned scene manager, scheduler, parser, lifecycle, or gameplay renderer is authorized.

Authority order:

1. Original arcade runtime behavior and opcode evidence.
2. Preserved original arcade trace evidence: `states/traces/original_arcade_scene_fill_stability_20260727_141526/`.
3. Canonical arcade references under `docs/arcade_reference/pc080sn/`.
4. Arcade-to-Genesis mappings from `build/rastan-direct/address_map.json`.
5. Build 0235 only as the accepted Genesis regression baseline, not as authority for original arcade producer behavior.

## 2. Accepted Baseline

Accepted regression baseline:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`
- SHA-256: `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`
- Observed counter: `238`

Artifact status:

- Builds 0236 and 0238 are rejected.
- Build 0237 is preserved as a duplicate.
- Numbered artifacts must never be deleted, overwritten, or reused.

## 3. Fixed Genesis VDP Layout

The native contract targets the fixed YM7101 layout already established for rastan-direct:

- VDP register 16 = `0x01`.
- Plane B nametable = `VRAM 0xC000`.
- Plane A nametable = `VRAM 0xE000`.
- SAT = `VRAM 0xF800`.
- H-scroll table = `VRAM 0xFC00`.
- Plane geometry = `64x32` cells.
- VBlank remains arcade-owned.
- No active-display VDP writes are allowed.

All hardware commits occur through the arcade-owned VBlank service path.

## 4. Original Arcade Fill Classes

The original arcade scene-fill routine is `arcade_pc 0x0503DC`. It has one direct caller: `arcade_pc 0x050206 bsr.w 0x0503DC` inside scene/reinit routine `arcade_pc 0x0501E2`.

The fill loop begins at `arcade_pc 0x0503E4` and runs exactly 64 publications before first display.

### Selector 0

Selector 0 is runtime-proven by the preserved original arcade MAME trace.

Path:

```text
arcade_pc 0x0503DC -> 0x050434 -> 0x055948 -> 0x055968
```

Contract:

- 64 publications.
- One logical column per publication.
- Stable authoritative scroll basis through first display.
- Plane A path `0x055968` executed 64 times.
- Plane A row path `0x055990` did not execute in the captured selector-0 fill.
- Design A valid.

### Selector 1

Selector 1 is opcode-bounded from original arcade code.

Path:

```text
arcade_pc 0x0503DC -> 0x050434 -> 0x055948 -> 0x055990
```

Contract:

- 64 publications.
- One complete 64-cell logical row per publication.
- Rows publish in order 63 -> 0.
- Exact Plane A / tilemap1 coverage: `HW_ADDRESS 0x00C08000..0x00C0BFFF`.
- No rowscroll/unused region is touched.
- No row overlap or mid-fill scroll retarget occurs in the opcode path.
- Design A valid.

### Selector 2

No live selector-2 scene-fill class is identified.

Selector 2 is a gameplay vertical-streaming direction. It appears in the map stream as a gameplay direction selector, not as a proven scene-fill class reaching `arcade_pc 0x0503DC`.

Do not invent a selector-2 scene-fill specialization.

## 5. Plane A Producer Contracts

Plane A corresponds to arcade PC080SN tilemap1 / foreground-playfield name RAM at `HW_ADDRESS 0x00C08000..0x00C0BFFF`.

Authoritative producer boundaries:

| Role | Arcade PC | Runtime Genesis PC | Notes |
|---|---:|---:|---|
| Dispatcher/post-publication owner | `0x055948` | `0x055B48` | Increments ring counters and advances map stream after publication |
| Column boundary | `0x055968` | `0x055B68` | Selector-0 column publisher |
| Row boundary | `0x055990` | `0x055B90` | Selector-1/2 row publisher |

Contract requirements:

- Descriptor/source/ring semantics are retained.
- Direction reversal semantics are retained.
- Collision publication is retained for all logical cells.
- Visual residency must not suppress collision writes.
- Native visual output may be residency-filtered only after the arcade logical cell and collision side effect have been represented correctly.

## 6. Plane B Producer Contract

Plane B corresponds to arcade PC080SN tilemap0 / background name RAM at `HW_ADDRESS 0x00C00000..0x00C03FFF`.

Authoritative producer boundaries:

| Role | Arcade PC | Runtime Genesis PC | Notes |
|---|---:|---:|---|
| Gameplay trigger | `0x055B60` / `0x055B8E` | `0x055D60` / `0x055D8E` | Vertical tilemap0 gameplay streamer |
| Bookkeeping owner | `0x055C4A` | `0x055E4A` | Strip wrapper/bookkeeping |
| Current strip boundary | `0x055C5E` | `0x055E5E` | Current tilemap0 strip hook boundary |
| Original per-cell tail | `0x055C7A` | `0x055E7A` | Original tilemap0 per-cell body |

Contract requirements:

- Scene fill publishes 64 rows.
- Gameplay publishes one entering row on an 8-pixel crossing.
- Plane B has no collision side channel.
- Item-page and frontend compatibility callers must be separated from the native gameplay route.

## 7. Publication Bounds

Ordinary gameplay frame bounds:

- Maximum ordinary Plane A columns per arcade frame: `1`.
- Maximum ordinary Plane A rows per arcade frame: `1`.
- Maximum combined ordinary Plane A publications per frame: `1`.
- Maximum ordinary Plane B rows per frame: `1`.

Scene-fill exception:

- `arcade_pc 0x0503DC` intentionally publishes 64 Plane A strips and 64 Plane B strips before first display.

Plane A and Plane B may both publish during the same ordinary frame. Plane A row and column publications are mutually exclusive in ordinary gameplay because the direction selector is mutually exclusive.

## 8. Logical Scroll Contracts

Plane A / tilemap1:

- X field: `a5+0x10AE`.
- Y field: `a5+0x10B0`.
- Hardware commits: `HW_ADDRESS 0x00C40002` / `HW_ADDRESS 0x00C20002`.

Plane B / tilemap0:

- X field: `a5+0x10EC`.
- Y field: `a5+0x10EE`.
- Hardware commits: `HW_ADDRESS 0x00C40000` / `HW_ADDRESS 0x00C20000`.
- Plane B X remains half-rate/parallax.

Both planes preserve the original 512-pixel logical wrap:

```text
512 pixels = 64 tiles = scroll mask 0x01FF
```

Native Genesis display requires the established `+8` vertical display-origin correction.

## 9. Native Resident Mapping

Plane A:

```text
A_native_scroll_y = (-A_y + 8) & 0x01FF
A_logical_top_row = (A_native_scroll_y >> 3) & 0x003F
A_fine_y = A_native_scroll_y & 0x0007
```

Plane B:

```text
B_native_scroll_y = (-B_y + 8) & 0x01FF
B_logical_top_row = (B_native_scroll_y >> 3) & 0x003F
B_fine_y = B_native_scroll_y & 0x0007
```

For each plane independently:

```text
delta = (logical_row - logical_top_row) & 0x003F
resident only when delta < 32
```

Only after the residency test succeeds:

```text
physical_row = logical_row & 0x001F
physical_col = logical_col & 0x003F
```

`logical_row & 31` is never permission to write a nonresident logical row. Residency is the authority; modulo is only the final physical placement after residency succeeds.

Logical row 63 -> 0 behavior:

- The original arcade ring is 64 rows deep.
- Scroll fields wrap at 512 pixels via `& 0x01FF`.
- Therefore logical row 63 -> 0 is the intended PC080SN wrap boundary.

Physical row 31 -> 0 behavior:

- Genesis physical planes are 32 rows high.
- Resident logical rows are projected by `logical_row & 0x001F`.
- Therefore logical row 31 -> 32 maps physical row 31 -> 0, and logical row 63 -> 0 also maps physical row 31 -> 0 at the 64-row logical wrap.
- The residency test prevents two logical rows separated by 32 from being authoritative in the same physical row.

## 10. Scene-Fill Native Contract

All identified live fill classes use Design A:

```text
stable original-arcade mapping
  -> native resident output during the 64 arcade publications
  -> first display
```

Selector-0 column fill behavior:

- Runtime-proven first-visible Stage 1 fill.
- 64 publications through `arcade_pc 0x055968`.
- One logical column per publication.

Selector-1 row fill behavior:

- Opcode-bounded original arcade fill.
- 64 publications through `arcade_pc 0x055990`.
- One complete logical row per publication.
- Rows 63 -> 0.

Plane B row fill behavior:

- Scene-fill loop calls `arcade_pc 0x055C4A` 64 times.
- The tilemap0 path publishes 64 rows in parallel with the Plane A scene fill.

Semantic ownership:

- Descriptor work remains arcade-owned.
- Ring work remains arcade-owned.
- Source selection remains arcade-owned.
- Collision work remains arcade-owned.
- Only resident visual cells are written to final Genesis staging.
- Complete 64x32 resident planes must be populated before first display.
- No post-fill Design-B redraw is required for any identified live fill class.

## 11. Ordinary Gameplay Native Contract

Ordinary gameplay updates are producer-local and strip-local:

- Selector 0 publishes a Plane A entering column.
- Selector 1 publishes a Plane A entering row.
- Selector 2 publishes a Plane A entering row with the original selector-2 direction semantics.
- Plane B publishes an entering row through the tilemap0 vertical streamer.
- Sub-tile movement updates scroll only.
- Unchanged cells are not reconverted or recopied.
- No gameplay full-window projection is authorized.
- No gameplay tall-buffer visual writes are authorized.
- No gameplay generic PC080SN visual range classification is authorized.

## 12. Native and Legacy Ownership

Gameplay and gameplay scene initialization own the final native Plane A and Plane B buffers.

Separately proven legacy compatibility remains for:

- frontend/title;
- text;
- HUD;
- score/high-score;
- glyph/number writers;
- item pages;
- shared block-copy paths;
- other audited unconverted producers.

No Genesis-owned scene manager or independent lifecycle machine is allowed.

Any minimal presentation-ownership field must be driven only by named arcade-owned transition boundaries. Such a field is not allowed to become a Genesis scheduler or parser.

## 13. Scaffolding Disposition

Intended gameplay disposition:

| Symbol / path | Disposition |
|---|---|
| `staged_bg_tall_buffer` | Retired from gameplay; removable only after complete producer-and-consumer proof |
| `staged_fg_tall_buffer` | Retired from gameplay; removable only after complete producer-and-consumer proof |
| `vdp_project_bg_tall_if_dirty` | Retired from gameplay |
| `vdp_project_fg_tall_if_dirty` | Retired from gameplay |
| `bg_tall_project_base` | Retired from gameplay |
| `fg_tall_project_base` | Retired from gameplay |
| `genesistan_hook_tilemap_bg_fill_tall` | Retired from gameplay native path; removable only after full proof no retained compatibility caller needs it |
| `genesistan_hook_tilemap_fg_fill_tall` | Retired from gameplay native path; removable only after full proof no retained compatibility caller needs it |
| `genesistan_stage_fg_src_column` | Retired from gameplay native path; source/descriptor/ring work must be arcade-owned |
| `genesistan_hook_itempage_strip_blit` | Retained for item-page and unconverted compatibility; must be separated from native gameplay route |
| `staged_bg_buffer` | Final native Plane B staging buffer |
| `staged_fg_buffer` | Final native Plane A staging buffer |

Removal is authorized only after complete producer-and-consumer proof. This contract defines gameplay intent; it does not by itself delete transitional compatibility structures.

## 14. VBlank Capacity Contract

Bounded ordinary capacity:

- one Plane A column job;
- one Plane A row job;
- one Plane B row job.

Rules:

- Plane A row and column are mutually exclusive in ordinary gameplay.
- Plane B may publish in the same frame as Plane A.
- No dropped jobs.
- No silent overwrite.
- No unbounded queue.
- All hardware commits occur during arcade-owned VBlank.

## 15. Prohibited Architecture

Explicitly prohibited:

- Genesis main loop.
- Genesis scheduler.
- Genesis scene manager.
- Genesis map parser.
- 64x64 VDP mode.
- 64x64 translated visual cache.
- Arcade-format name-RAM mirror.
- C-window shadow.
- Active-display VDP writes.
- Ongoing display-disable bracketing.
- Parallel gameplay renderers.
- Selector reinterpretation.
- Speculative selector-2 scene-fill handling.

## 16. Implementation Readiness

Remaining contract blockers: none.

Selector-2 direct scene fill is not identified and must not be special-cased.

Ready for coherent native Plane A and Plane B implementation: **YES**.
