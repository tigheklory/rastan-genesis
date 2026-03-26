# Graphics Translation Mapping Design

## 1) Objective
Design a reusable graphics translation mapping system that converts recurring arcade graphics operations into Genesis-native VDP operations, with focus on the live title/frontend path and without per-screen fake rendering hacks.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest entries, especially Builds 230-232 and Title Screen Forward Progress Trace)
- `docs/research/title_screen_forward_progress_trace.md`
- `docs/research/build230_text_dispatch_fix.md`
- `docs/research/build231_descriptor_content_trace.md`
- `docs/research/build232_descriptor_content_fix.md`
- `apps/rastan/src/main.c`
- `specs/startup_title_remap.json`
- Note: `docs/research/graphics_pipeline_gap_analysis.md` was not present in the workspace during this pass.

## 3) Recurring Arcade Graphics Operation Classes

### Class A: Text Emission
- Source callsites/functions: title path IDs through `0x03BD5E`; secondary writer family at `0x03C3FE`; hooks `genesistan_hook_text_writer_3bb48_impl`, `genesistan_hook_text_writer_3c3fe`.
- Arcade-side effect: writes text attributes/glyphs into C-window page cells.
- Expected visible result: HUD/title/copyright/credit text on visible foreground plane.

### Class B: Sprite/Logo Descriptor Emission
- Source callsites/functions: title logo trigger `0x03AAF2 -> 0x05A174`; renderer entry `genesistan_render_sprites_vdp` and sprite callsite redirects in `shift_replacements`.
- Arcade-side effect: populate PC090OJ descriptor buffers and stream to sprite hardware window.
- Expected visible result: RASTAN logo/sword-T and other frontend sprites.

### Class C: Tile Plane Update
- Source callsites/functions: `0x055968` and `0x055990` replaced to `genesistan_hook_tilemap_plane_a/b`.
- Arcade-side effect: tile/attribute updates in PC080SN C-window pages.
- Expected visible result: BG/FG tilemap content updates.

### Class D: Scroll Update
- Source callsites/functions: scroll writes (`0x055AB4/BC/C4/CC`, boot/setup writes) redirected to `genesistan_scroll_from_workram_vdp`.
- Arcade-side effect: write X/Y scroll registers for two planes.
- Expected visible result: correct plane positioning/motion.

### Class E: Palette Update
- Source callsites/functions: palette conversion/capture path plus runtime `load_arcade_palette()`.
- Arcade-side effect: CLCS palette RAM writes.
- Expected visible result: correct colors in CRAM.

### Class F: Clear/Fill Prep
- Source callsites/functions: title prep families (`0x03AD44`, `0x03AD4C`, `0x03AE64`, `0x03AF5E`, `0x03B076`) and renderer-side clears.
- Arcade-side effect: clear descriptor/text staging regions before composition.
- Expected visible result: deterministic clean frame start before text/sprite producers run.

## 4) Genesis-Native Equivalents By Class
- Text emission -> decode text descriptor -> write to active plane via `VDP_setTileMapXY` with tile-cache-derived tile index and mapped attributes.
- Sprite/logo descriptors -> build active descriptor tuples (attr,y,tile,x) in renderer-owned WRAM blocks -> `VDP_setSpriteFull` + `VDP_updateSprites`.
- Tile plane updates -> map arcade tile+attr to VRAM tile through cache -> write plane entries on BG_A/B with correct priority/flip/palette bits.
- Scroll updates -> consume workram scroll words -> `VDP_setHorizontalScroll`/`VDP_setVerticalScroll`.
- Palette updates -> convert/copy CLCS/ROM palette lines -> `PAL_setColors`/`PAL_setColor` to CRAM.
- Clear/fill -> clear only active owner buffers and/or direct plane clears (`VDP_clearPlane`) required by the current phase.

## 5) Translation Table Design (Intent-First)

### Proposed schema
```json
{
  "graphics_translation_map": [
    {
      "op_id": "TEXT_EMIT_PRIMARY",
      "intent": "text_emit",
      "sources": [{"arcade_pc": "0x03BB48"}],
      "entry_contract": {"input_reg": "D0", "state_owner": "A5 workram"},
      "target": {"kind": "hook_symbol", "symbol": "genesistan_hook_text_writer_3bb48_impl"},
      "output_owner": {"plane": "BG_A", "shadow": "text page2 mirror"},
      "required_outputs": ["plane_cell_write"],
      "validators": ["entry_signature_match", "exec_hit", "non_space_tile_cells"]
    }
  ]
}
```

### Key design rules
- Group mappings by graphics intent first, then attach callsite groups.
- Each mapping must define output owner and required output artifacts.
- Each mapping must carry validators that prove visible-output production, not only function execution.
- Keep callsite list expandable, but avoid per-screen bespoke logic branches.
- Enforce semantic-entry correctness on mapped callsites (match entry vs inside-body vs wrong-function).

### Recommended operation IDs for initial system
- `TEXT_EMIT_PRIMARY`
- `TEXT_EMIT_SECONDARY`
- `SPRITE_DESC_BUILD_TITLE`
- `SPRITE_RENDER_FRONTEND`
- `TILEMAP_WRITE_BG`
- `TILEMAP_WRITE_FG`
- `SCROLL_SYNC_WORKRAM`
- `PALETTE_SYNC_CLCS`
- `TITLE_PREP_CLEAR`

## 6) Existing Evidence Fit (What Exists vs Missing)

### Already present in partial form
- Intent-level hooks already exist for text (`3BB48`, `3C3FE`), tilemap (`plane_a/b`), scroll, palette, and sprite rendering.
- Shift-table and semantic-entry validation infrastructure already exists and has caught real wrong-entry issues.
- Started-path evidence confirms active VDP port writes and active frontend frame loop.

### Missing or inconsistent pieces
- Intent routing integrity is incomplete: proven stale/wrong-function remap cases can still strand producer paths.
- Sprite descriptor content generation intent is not fully realized: ownership is active, but descriptor tuples remain empty/template in Build 231/232 evidence.
- Title-visible proof validators are not yet formalized as required pass/fail gates per intent.

### Why earlier “correct text” observations fit
- Partial text visibility in earlier builds is consistent with some text intents being mapped correctly while other intents (tilemap/sprite content generation) remained incomplete or intermittently misrouted.

## 7) First Practical Mapping Set For Title Screen
- `TEXT_EMIT_PRIMARY` (`0x03BB48` family): must produce non-space visible cells on active plane.
- `TEXT_EMIT_SECONDARY` (`0x03C3FE` family): must produce additional title text lines where used.
- `SPRITE_DESC_BUILD_TITLE` (`0x03AAF2 -> 0x05A174` family): must output drawable tuples into active descriptor owners.
- `SPRITE_RENDER_FRONTEND` (renderer callsite group): must consume non-empty descriptor content and upload necessary tile data.
- `TITLE_PREP_CLEAR`: must clear only active owners and avoid wiping produced tuples post-build.
- `TITLE_TILEMAP_UPDATE` (if title path requires explicit plane updates): must execute required plane writes before/with text visibility.

Minimum validation artifacts for this set:
- nonzero, non-space text cells written to visible plane addresses;
- at least one drawable sprite tuple (nonzero tile, valid x/y, active attr) in active descriptor blocks;
- corresponding tile data upload for referenced sprite codes.

## 8) Display DIP Normalization (Locked/Console-Safe)
Display-orientation DIP behaviors should be normalized to factory/default console-safe behavior and not treated as user-facing runtime variants on Genesis.

Lock/normalize:
- Cabinet orientation variants that imply mirrored/flipped presentation paths.
- Monitor reverse/flip display orientation variants.

Reason:
- They increase graphics translation surface area without meaningful console value.
- They add divergent visual ownership paths that hinder deterministic title/frontend validation.
- Factory/default orientation is sufficient and aligns with the locked platform decision.

## 9) Uncertainties
- `docs/research/graphics_pipeline_gap_analysis.md` was unavailable in this workspace; this design relies on available Build 230-232 evidence and current source/spec state.
- Exact final descriptor-content source table flow for title/logo sprites still needs dedicated follow-up once mapping validators are in place.

## 10) Conclusion
A reusable intent-based graphics translation map is the correct next architecture: it matches the project’s direct-opcode replacement direction, scales across screens better than callsite-by-callsite hacks, and creates explicit producer-to-visible-output validation gates needed to finish title/frontend correctness.
