# Cody - Build 0095 Title BG Block-Copy Staging Diagnostic

**Date:** 2026-06-23  
**Type:** Prep-diagnostic / read-only evidence  
**Build context:** Build 0095, `rastan-direct`  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0095.bin`  
**ROM SHA256:** `273508a23ddd7b37e10e7ba4a7355f78e95bbe539ba3145b4e844b59ace53ef6`  
**Scope:** Determine why the confirmed original arcade title BG block-copy path remains absent from Genesis BG staging. No source/spec/tool/ROM/build changes. No instrumentation. No runtime probing.

## Phase 0

Classification: **EXTENDING** (OPEN-001 graphics-output failure; OPEN-016 context). Relevant priors loaded from `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, recent `AGENTS_LOG.md`, and the requested design notes:

- `docs/design/Cody_build_0095_arcade_title_tile_usage_audit.md`
- `docs/design/Andy_build_0095_taito_logo_producer_attribution.md`
- `docs/design/Cody_build_0095_3ad44_dispatch_fg_bg_split.md`

No contradiction detected. Architecture compliance preserved: arcade code remains the program; this diagnostic only identifies a missing translation/staging hook for a confirmed arcade BG block-copy path.

## Address Mapping Discipline

All arcade-to-Genesis addresses below were resolved through `build/rastan-direct/address_map.json`. No arithmetic offset is used as proof.

| Query | JSON segment | Segment kind | Segment arcade range | Segment Genesis range | Mapped address |
|---|---:|---|---|---|---|
| arcade `0x05A38E` | 171 | `arcade_copy` | `0x05A28A..0x060000` | `0x05A48A..0x060200` | Genesis `0x05A58E` |
| Genesis `0x05A58E` | 171 | `arcade_copy` | `0x05A28A..0x060000` | `0x05A48A..0x060200` | arcade `0x05A38E` |
| arcade `0x05A4DE` | 171 | `arcade_copy` | `0x05A28A..0x060000` | `0x05A48A..0x060200` | Genesis `0x05A6DE` |
| Genesis `0x05A6DE` | 171 | `arcade_copy` | `0x05A28A..0x060000` | `0x05A48A..0x060200` | arcade `0x05A4DE` |
| arcade table `0x05B0B2` | 171 | `arcade_copy` | `0x05A28A..0x060000` | `0x05A48A..0x060200` | Genesis table `0x05B2B2` |
| Genesis table `0x05B2B2` | 171 | `arcade_copy` | `0x05A28A..0x060000` | `0x05A48A..0x060200` | arcade table `0x05B0B2` |

Load-bearing point: the JSON map itself labels the currently produced Build 0095 block-copy site as `arcade_copy`, not as a patched/replaced site.

## Confirmed Runtime Path in Produced Build 0095

The generated disassembly shows the title-art block setup at mapped Genesis `0x05A58E`:

```asm
5a58e: movea.l #0x00c00328,%a1
5a594: lea     0x05b2b2,%a0
5a59a: move.w  #28,%d0
5a59e: move.w  #20,%d1
5a5a2: move.w  #1,%d2
5a5a6: bsrw    0x5a6de
5a5aa: rts
```

Source: `build/genesis_postpatch.disasm.txt:114087-114093`.

The mapped block-copy engine at Genesis `0x05A6DE` is still the original arcade-style loop:

```asm
5a6de: move.w  %d0,%d4
5a6e0: movea.l %a1,%a2
5a6e2: move.w  %d2,(%a1)+
5a6e4: move.w  (%a0)+,(%a1)+
5a6e6: subq.w  #1,%d0
5a6ec: bne     0x5a6e2
5a6ee: adda.l  #0x100,%a2
5a6f4: movea.l %a2,%a1
5a6f6: move.w  %d4,%d0
5a6f8: subq.w  #1,%d1
5a6fe: bne     0x5a6e2
5a700: rts
```

Source: `build/genesis_postpatch.disasm.txt:114161-114174`.

The produced ROM bytes at `0x05A6DE` begin with the original bytes:

```text
3800244932c232d853400c40000066f4d5fc00000100224a300453410c41000066e24e75...
```

That is the original block-copy routine, not a `JMP`/`JSR` to a Genesis staging helper.

## Spec / Manifest Comparison

`specs/startup_title_remap.json` contains a legacy/startup-scope replacement for arcade `0x05A4DE`:

```json
{
  "arcade_pc": "0x05A4DE",
  "original_bytes": "3800244932C232D85340",
  "replacement_bytes": "4ef9{symbol:genesistan_bulk_tilemap_commit}4e714e71"
}
```

Source: `specs/startup_title_remap.json:1069-1072`. That same spec lists `genesistan_bulk_tilemap_commit` as a required symbol (`specs/startup_title_remap.json:167-170`).

The current Build 0095 consumed rastan-direct spec does **not** contain that replacement:

- `specs/rastan_direct_remap.json` has `opcode_replace_count = 95` and no `0x05A4DE` entry.
- `specs/rastan_direct_remap.json` required symbols include `genesistan_hook_tilemap_bg_fill`, but not `genesistan_bulk_tilemap_commit` (`specs/rastan_direct_remap.json:80-85`).
- `build/rastan-direct/rastan_direct_patch_manifest.json` has no `0x05A4DE` / `0x05A6DE` hit.
- `apps/rastan-direct/out/symbol.txt` has no `genesistan_bulk_tilemap_commit` symbol.

Therefore this is **not** a patch-application failure inside the Build 0095 consumed spec. The replacement exists in `startup_title_remap.json`, but Build 0095 `rastan-direct` is governed by `specs/rastan_direct_remap.json`; the replacement was not ported into the current spec/helper set.

## FG-vs-BG Comparison

### Working FG / Text Paths

The title FG/text path has current rastan-direct coverage:

- `specs/rastan_direct_remap.json` includes the OPEN-016 descriptor table relocation (`absolute_long_pointer_tables`, `0x03BB7C`, entry count 71; `specs/rastan_direct_remap.json:728-734`).
- Build 0092/0095 glyph-renderer work routes `0x03BD48` through `genesistan_hook_glyph_renderer_3bd48`, which writes to `staged_fg_buffer` and sets `fg_row_dirty`.
- The Build 0095 `0x03AD44` dispatch fix routes tilemap fills through `genesistan_hook_tilemap_bg_fill` / `genesistan_hook_tilemap_fg_fill` as appropriate (`specs/rastan_direct_remap.json:313-316`; implementation source begins at `apps/rastan-direct/src/tilemap_hooks.s:389`).

### Missing BG Block-Copy Path

The title BG logo/art path is different. It is a rectangular source-table copy:

- Destination: `0x00C00328` (PC080SN BG C-window).
- Source table: Genesis `0x05B2B2`, JSON-mapped from arcade `0x05B0B2`.
- Size: `28 x 20`.
- Attribute/source pattern: write `%d2` then `(%a0)+` per cell.

Build 0095 reaches the original-style copy loop at `0x05A6DE`, which writes to the PC080SN-style destination pointer in `%a1`. No Genesis BG staging helper consumes those writes, so `staged_bg_buffer` and `bg_row_dirty` do not receive the complete TAITO / RASTAN / sword title-art table.

## Candidate Cause Resolution

| Candidate | Verdict | Evidence |
|---|---|---|
| 1. `0x05A4DE` replacement is in the consumed spec but did not apply to Build 0095 ROM | **NO** as a tooling/build application bug | The current consumed `specs/rastan_direct_remap.json` has no `0x05A4DE` entry. The legacy/startup spec has one, but that is not the Build 0095 rastan-direct spec. |
| 2. Replacement applies to a different site/copy | **NO** | JSON maps arcade `0x05A4DE` exactly to Genesis `0x05A6DE`, and the title setup at `0x05A58E` calls that exact site. The target address is correct; the current spec lacks the replacement. |
| 3. Block-copy helper exists but is not wired to this title BG path | **NO / not the primary current failure** | `genesistan_bulk_tilemap_commit` exists only as a required symbol in `startup_title_remap.json`; it is absent from rastan-direct symbols/source. Existing rastan-direct BG helpers cover strip/fill classes, not this source-table block-copy class. |
| 4. Path remains `arcade_copy` and writes arcade-style PC080SN memory that Genesis BG staging never consumes | **YES** | Address map segment 171 is `arcade_copy`; ROM/disasm at `0x05A6DE` is the original loop; no staging write/dirty path is present for this block-copy engine. |

Resolved classification: **Candidate 4 current-runtime behavior**, caused by a **rastan-direct spec/helper coverage gap**. The startup-title replacement was not migrated into the current rastan-direct remap system, and the current produced Build 0095 ROM therefore leaves the original arcade block-copy loop live.

## Fix Ownership and Class

**Owning spec file/site:** `specs/rastan_direct_remap.json` needs a new opcode replacement for arcade `0x05A4DE`, using JSON segment 171 to target runtime Genesis `0x05A6DE`.

**Owning helper file/site:** a production helper should live with the current tilemap staging helpers, most naturally `apps/rastan-direct/src/tilemap_hooks.s`. Do not blindly reference `genesistan_bulk_tilemap_commit`; that symbol is not present in rastan-direct. Either port/adapt that helper deliberately or implement a rastan-direct-native BG block-copy staging helper following current conventions.

**Fix class:** `arcade_copy -> BG staging-helper opcode_replace`.

The helper needs to preserve the original routine contract:

- Input registers: `%a1 = PC080SN destination`, `%a0 = source table`, `%d0 = width`, `%d1 = height`, `%d2 = attribute word`.
- Original cell behavior: per cell, emit attribute and source tile word; advance rows by `0x100` bytes in PC080SN address space.
- Genesis behavior: translate BG C-window destination offsets to `staged_bg_buffer`, compose Genesis cell words through the existing PC080SN tile/attribute LUT convention, set `bg_row_dirty` for touched rows, and return to the original caller without bypassing arcade control flow.

This must be a shift-table / proper redirected replacement per project rule. No NOP/RTS/equal-length workaround is acceptable as final justification.

## Safe-to-Implement Assessment

**Safe to implement:** YES, with a narrow implementation prompt.

Reason: arcade intent and current runtime gap are both pinned:

- Original arcade runtime established complete title-art use of the PC080SN BG title table.
- JSON maps the exact producer and table into Build 0095.
- Produced Build 0095 ROM demonstrably lacks the replacement at the mapped site.
- Existing FG and fill helpers show the staging/dirty pattern to match, but no existing rastan-direct helper covers this block-copy source-table class.

Implementation should remain bounded to the `0x05A4DE` block-copy engine and must not alter unrelated FG, sprite, palette, input, crash-handler, or exception paths.

## OPEN / CLOSED Impact

- OPEN-001: active; this directly explains the missing title BG art staging path.
- OPEN-016: context only; prior title text/glyph fixes are not contradicted.
- OPEN-015: not touched.
- New issues opened: none.
- Issues closed: none.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update in this read-only diagnostic. A KF refinement should wait until the rastan-direct block-copy staging helper is implemented and verified against Build 0095/next-build runtime output.

## STOP

STOP triggered: **NO**.

