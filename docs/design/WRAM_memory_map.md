# WRAM Memory Map — rastan-direct

**Last updated:** 2026-04-12  **Build:** 0025

## Address Space Overview

| Range              | Owner          | Size   | Notes |
|--------------------|----------------|--------|-------|
| 0xFF0000-0xFF3FFF  | Arcade workram | 16 KB  | A5 base = 0xFF0000 |
| 0xFF4000-0xFF60CB  | Genesis BSS    | ~8.2 KB | `GENESIS_BSS_BASE` in `apps/rastan-direct/link.ld` |
| 0xFF60CC+          | Available      | N/A    | Future expansion headroom |

## Arcade Workram Fields (0xFF0000+)

Derived from:
- startup_common path and design references
- `genesistan_init_workram_direct` reference logic
- current rastan-direct hooks and init writes

| Offset (hex) | Address   | Width | Description | Factory default |
|--------------|-----------|-------|-------------|-----------------|
| 0x0000 | 0xFF0000 | word | Main state machine state | 0 |
| 0x0002 | 0xFF0002 | word | Sub-state | 0 |
| 0x0008 | 0xFF0008 | word | Coinage 1 | 1 |
| 0x000A | 0xFF000A | word | Coinage 2 | 1 |
| 0x000E | 0xFF000E | word | Coinage/config field | 1 |
| 0x0010 | 0xFF0010 | word | Coinage/config field | 1 |
| 0x0014 | 0xFF0014 | word | Display control mirror | 0x0060 |
| 0x0018 | 0xFF0018 | word | DIP1 mirror (active-low; ndip1) | 0x0001 |
| 0x001C | 0xFF001C | word | DIP2 mirror (active-low; ndip2) | 0x0000 |
| 0x0026 | 0xFF0026 | word | Init flag | 1 |
| 0x002C | 0xFF002C | word | Warm-restart delay countdown | 160 |
| 0x002E | 0xFF002E | word | Mode (ndip2 & 3) | 0 |
| 0x0030 | 0xFF0030 | word | Cabinet config (ndip1 & 1) | 1 |
| 0x0032 | 0xFF0032 | word | Monitor config / screen flip (ndip1 & 2) | 0 |
| 0x0036 | 0xFF0036 | word | Bonus setting | 6 |
| 0x0038 | 0xFF0038 | word | Difficulty setting | 0x2500 |
| 0x004A | 0xFF004A | word | Sprite init marker | 0x00AA |
| 0x0080 | 0xFF0080 | word | Transition buffer seed A | copied from 0x0036 |
| 0x00B2 | 0xFF00B2 | word | Transition buffer seed B | copied from 0x0038 |
| 0x0097 | 0xFF0097 | byte | Transition control flag | 1 |
| 0x0098 | 0xFF0098 | byte | Transition control flag | 1 |
| 0x0100 | 0xFF0100 | word | Title init flag | 1 |
| 0x0100..0x013F | 0xFF0100..0xFF013F | bytes | Post-copy initialized range | mixed |
| 0x0140 | 0xFF0140 | byte[] | Config table destination (39 bytes) | ROM copy |
| 0x10A0 | 0xFF10A0 | long | BG destination pointer (`ARCADE_FIX_DEST_BG`) | 0x00C00000 |
| 0x10A4 | 0xFF10A4 | long | FG destination pointer (`ARCADE_FIX_DEST_FG`) | 0x00C08000 |
| 0x10CA | 0xFF10CA | word | Strip index consumed by BG hook | runtime |

## Genesis BSS Symbols (0xFF4000+)

Source: `apps/rastan-direct/out/symbol.txt` (post-build)

| Symbol | Address | Width | Description |
|--------|---------|-------|-------------|
| frame_counter | 0xFF4000 | word | VINT tick counter |
| tick_counter | 0xFF4002 | word | Arcade tick-side counter |
| palette_dirty | 0xFF4004 | byte | Palette dirty flag |
| tiles_dirty | 0xFF4005 | byte | Tile dirty flag |
| bg_row_dirty | 0xFF4006 | long | BG row dirty bitmask |
| genesistan_current_scene_id | 0xFF400A | byte | Current scene id |
| genesistan_scene_a0_lo | 0xFF400C | long | Current scene low bound |
| genesistan_scene_a0_hi | 0xFF4010 | long | Current scene high bound |
| genesistan_shadow_input_390001 | 0xFF4014 | byte | Shadow input P1 |
| genesistan_shadow_input_390003 | 0xFF4015 | byte | Shadow input P2 |
| genesistan_shadow_input_390005 | 0xFF4016 | byte | Shadow coin input |
| genesistan_shadow_input_390007 | 0xFF4017 | byte | Shadow system input |
| staged_dest_ptr_bg | 0xFF401C | long | Genesis staged BG pointer |
| staged_dest_ptr_fg | 0xFF4020 | long | Genesis staged FG pointer |
| staged_bg_buffer | 0xFF402C | 4096 bytes | Staged BG nametable words |
| staged_fg_buffer | 0xFF502C | 4096 bytes | Staged FG buffer |
| staged_palette_words | 0xFF602C | 128 bytes | Palette staging words |
| staged_tile_words | 0xFF60AC | 96 bytes | Tile staging words |

## Write Ownership Matrix

Genesis writes inside arcade ownership zone (`0xFF0000-0xFF3FFF`):

| Address | Genesis writer | Purpose |
|---------|----------------|---------|
| 0xFF0000-0xFF00FF | `init_staging_state` factory init block | Re-apply arcade factory defaults every warm restart |
| 0xFF0100 | `init_staging_state` factory init block | Title init flag seed |
| 0xFF0140-0xFF0166 | `init_staging_state` factory init block | Config table copy (39 bytes) |
| 0xFF10A0 | `init_staging_state` | BG destination pointer seed |
| 0xFF10A4 | `init_staging_state` | FG destination pointer seed |
| 0xFF10A0 | `genesistan_hook_tilemap_plane_a` | Runtime BG dest pointer advance write-back |

Arcade-owned writes/readers in same zone:

| Address | Primary owner | Purpose |
|---------|----------------|---------|
| 0xFF10CA | Arcade writer, BG hook reader | Strip index |
| 0xFF0000+ offsets | Arcade tick entry (`A5=0xFF0000`) | Main state machine fields |

## Change Log

| Date | Build | Change | Author |
|------|-------|--------|--------|
| 2026-04-12 | 0025 | Initial map with BSS relocation from 0xFF0000 to 0xFF4000 and restored arcade workram ownership at 0xFF0000 | Cody |
| 2026-04-12 | 0025 | Corrected factory defaults: DIP1 raw=0xFE (injected by remap.json), not 0xFF. ndip1=NOT(0xFE)=0x01; ndip2=NOT(0xFF)=0x00. Updated A5@(24)=0x0001, A5@(28)=0x0000, A5@(46)=0, A5@(50)=0 | Andy |
