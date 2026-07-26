# PC080SN Core Publishers — Address Index

`a5 = 0x10C000`. Confidence: **P**=proven from opcodes, **R**=runtime-confirmed, **?**=deferred.

| Arcade PC | Name (neutral) | Destination layer | Role | Collision side effect | Conf | Ref |
|---|---|---|---|---|---|---|
| `0x055948` | `pc080sn_publish_dispatch` | tilemap1_0xC08000 | dispatch: `a5@0x10A8==0 → 0x055968` else `0x055990`; `a5@0x10CA++`; then `0x558A2` | none directly | P | asm §1, c §1 |
| `0x055968` | `pc080sn_publish_strip_A` | tilemap1_0xC08000 (cursor `a5@0x10A0`) | walk 16 descriptors (tbl `0x10D040`) + source `0x10D080`, call `0x0559B2` per cell; save cursor | via 0x0559B2 | P | asm §2, c §2 |
| `0x055990` | `pc080sn_publish_strip_B` | tilemap1_0xC08000 (cursor `a5@0x10A4`) | same walk, call `0x055A14` per cell; cursor NOT saved | via 0x055A14 | P | asm §3, c §3 |
| `0x0559B2` | `pc080sn_cell_forward` | tilemap1_0xC08000 | write cell (word0=`*(a1)`, word1=`desc[0+…]`), 4 sub-cells | **YES** → `0x10DE00+(dest−0xC08000)/2` | P/R | asm §4, c §4 |
| `0x055A14` | `pc080sn_cell_dir_aware` | tilemap1_0xC08000 | same, sub-index reversed (`notw` when `a5@0x10A8≠2`); sets `a5@0x1330` | **YES** → `0x10DE00 + (dest−0xC08000)/2` (one store) | P | asm §5, c §5 |
| `0x055904` | `pc080sn_descriptor_rebuild` | tbl `0x10D040`/`0x10D080` | (referenced) supplies the 16 descriptor pointers consumed above | none | P(partial) | asm §6 |
| `0x055E54` | (tilemap0 cursor set) | **tilemap0_0xC00000** (`=0xC00400`) | one proven tilemap0 cursor setup, guard `a5@0x13AA==2`; distinct from the core publishers | — | ? | unresolved |

**Layer proof summary:** the two gameplay triggers (`0x055808` horizontal → `a5@0x10A0`, `0x0556E0` vertical → `a5@0x10A4`) both compute `dest = 0xC08000 + …` → the core publishers documented in this checkpoint target **tilemap1_0xC08000**. `0x055E54` is **one proven** `pc080sn_tilemap0_0xC00000` cursor setup; the complete tilemap-0 producer set remains unresolved. Collision index `0x10DE00 + (dest−0xC08000)/2` is anchored to tilemap1.

## Scroll & readback sites (from access_inventory.md)
| Arcade PC | Op | R/W | Target | Subsystem |
|---|---|---|---|---|
| `0x055AB4`+3 | `movew a5@,0xc2/c40000/2` | W | scroll layer-A/B X/Y | gameplay scroll commit |
| `0x03ABBA`/`0x03B098` (+C0) | `clrl 0xc20000/c40000` | W | scroll | frontend scroll clear |
| `0x03A47E` | `cmpiw #73,0xc0883a` | **R** | tilemap1 cell | text/HUD compare-read |
| `0x03A552` | `cmpib #48,0xc09ea3` | **R** | tilemap1 cell | text/HUD compare-read |
| `0x03AC54` | `cmpib #67,0xc09e87` | **R** | tilemap1 cell | text/HUD compare-read |

Full direct/indirect/subsystem tables + the 77-site Genesis-lead reconciliation: **access_inventory.md**.

## Gameplay control / ring (from gameplay_control.c + state_fields.md)
| Arcade PC | Name | Role |
|---|---|---|
| `0x0556A6` | `dir_sel1_vertical` | selector==1 vertical publish; dest 0xC08000+(0x3F00−(0xCC<<10\|0xCA<<8)) → a5@0x10A4 |
| `0x055738` | `dir_sel2_vertical` | selector==2 vertical publish; dest 0xC08000+(0xCC<<10\|0xCA<<8) → a5@0x10A4 |
| `0x0557C4`/`0x055808` | `dir_sel0_horizontal` | selector==0 horizontal publish; dest 0xC08000+(0xCC<<4\|0xCA<<2) → a5@0x10A0 |
| `0x0558A2` | `post_advance` | CA 0→3 (rebuild@4), CC 0→15 (map-advance@16) |
| `0x0558C6` | `advance_source_ptrs` | +4 to each 0x10D000 base ptr; CA=0 |
| `0x0558E0` | `advance_map_group` | CC=0; a5@0x10C6++; **selector = *(map)** |
| `0x055904` | `descriptor_rebuild` | 0x10D000 base → 0x10D040 desc-ptrs + 0x10D080 source words |
| `0x055AB4` | `commit_scroll` | 0xC20000/2←a5@0x10EE/0x10B0; 0xC40000/2←a5@0x10EC/0x10AE (W-only) |

Ring: `a5@0x10CA` (col 0..3) × `a5@0x10CC` (group 0..15) = 64; selector from map bytes; scroll accums &511 (64-tile wrap). Full facts: gameplay_control_assembly.md; fields: state_fields.md.

## Scene init + tilemap0 (from scene_initialization.c / tilemap0_producers.md)
| Arcade PC | Name | Role |
|---|---|---|
| `0x0503E4` | `scene_fill` | 64-column loop; fills tilemap1 (0x055948) + tilemap0 (0x55C4A) at scene setup |
| `0x55C4A`/`0x55C5E`/`0x55C7A` | `tilemap0_publish` | tilemap0 strip (64 sub-cells, **no collision**); cursor a5@0x10F8; tbl 0x10D100/0x10D104 |
| `0x0561B6` | `cwindow_clear` | clears BOTH maps to tile 0x0020 (word0=0x0000) — proves 0x0020=blank/base |
| `0x05127C`/`0x05274C`/`0x527CC` | selector 4/5/6 handlers | **non-publication** map commands (event/scene control) |

Roles: tilemap1@0xC08000=layer B=playfield(+collision, streamed); tilemap0@0xC00000=layer A=background(scene-init). 0x0020=blank tile.
