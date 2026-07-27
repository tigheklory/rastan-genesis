# PC080SN Tilemap0 (0xC00000) Producers — canonical

Every proven path that writes or cursors `pc080sn_tilemap0_0xC00000` (0xC00000–0xC03FFF). Neutral names. Tilemap0 = background: X-scroll `0xC40000`←a5@0x10EC (half-rate parallax), Y-scroll `0xC20000`←a5@0x10EE; **no collision channel**. Streams VERTICALLY via 0x055B8E (below).

## Actual writers
| Arcade PC | Chain / caller | Cursor origin | Store routine | Source | Dest calc | Amount / orient | Class | Gameplay-active? |
|---|---|---|---|---|---|---|---|---|
| `0x55C7A` | `0x55C5E ← 0x55C4A ← 0x050438` (scene fill) | `a5@0x10F8` (=0xC00000, seeded 0x0503F6/0x05040C) | `0x55C7A` (64 sub-cells, +256, **no collision**) | src `0x10D104` + desc `0x10D100` | `*(a0)+`=word0; word1 @ `d2*32 + a5@0x10F6*2` | 64-cell strip × 64 cols (whole map) | **scene init** | no (fill loop only) |
| `0x55C7A` | `0x55C5E ← 0x55C4A ← **0x055B8E**` | `a5@0x10F8`=0xC00000+(a5@0x10F4<<6)+(a5@0x10F6<<2) | same | same | same | strip on VERTICAL 8px crossing | **gameplay vertical stream** | **YES** — the 0x055B60 routine streams tilemap0 rows on vertical crossings + commits half-rate parallax X-scroll |
| `0x0561B6` | C-window clear (also clears tilemap1) | immediate `#0xC00000` | inline `movel #0x20` ×4096 | constant `0x00000020` | linear | full quadrant (both maps) | clear | scene transition |

## Cursor setup only (no direct write here; feeds a writer)
| Arcade PC | Sets | Value | Feeds |
|---|---|---|---|
| `0x0503F6`,`0x05040C` | `a5@0x10F8` (0x10D0F8) | 0xC00000 | 0x55C7A (via 0x55C5E) |
| `0x050420` | `a5@0x10A4` (via d0) | **0xC0BF00** | tilemap1 strip_B cursor, `sel==1` scenes — tilemap1 **row 63** (0xC08000+0x3F00), fills tilemap1 upward. NOT 0xC04000, NOT tilemap0. |
| `0x055E54` | `a5@0x10A0` | 0xC00400 | tilemap1 publisher `0x055968`, guard `a5@0x13AA==2` — writes 0xC00xxx via the *tilemap1* cell path (one proven case of the tilemap1 publisher pointed at the 0xC00000 quadrant) |

## Shared primitives
- `0x0561B6` C-window clear (both maps) · `0x05A4DE` block-copy engine (frontend art) · boot clear `0x00054A` (2 tilemaps + 2 rowscroll/unused regions).

## Frontend / item-only (classify, do not reconstruct here)
| Arcade PC | Base | Note |
|---|---|---|
| `0x056032`,`0x05605C` | 0xC00xxx | item/status page sources |
| `0x0561C6` | 0xC00000 | C-window clear a1 (shared, above) |
| boot `0x00054A`,`0x03AF2C` | quadrants | init/frontend clears |

## Region notes (resolved)
- **0xC0C000–0xC0C1FF = FG rowscroll RAM** (`m_bgscroll_ram[1]`, verified used only on Topspeed); **0xC0C200–0xC0FFFF = unused**. Rastan uses global scroll and only clears this region (frontend 0x03AF62) — no tile content is ever streamed here. (Per official MAME `pc080sn.cpp` header + `word_w`.)

## Summary
Tilemap0 (background) is populated by its own publisher chain `0x55C4A→0x55C5E→0x55C7A` (64-cell strips, no collision, tables 0x10D100/0x10D104). It is filled at scene setup by the `0x0503E4` loop AND **streamed during gameplay on vertical crossings** by the `0x055B60` routine (calls 0x055B8E→0x55C4A), which also commits tilemap0's **half-rate parallax** horizontal scroll. So tilemap0 both initializes and updates during play; it is the parallax background, tilemap1 the full-rate playfield.
