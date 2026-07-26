# PC080SN Tilemap0 (0xC00000) Producers — canonical

Every proven path that writes or cursors `pc080sn_tilemap0_0xC00000` (0xC00000–0xC03FFF). Neutral names. Tilemap0 = layer A (`0xC20000/2` scroll) = background; **no collision channel**.

## Actual writers
| Arcade PC | Chain / caller | Cursor origin | Store routine | Source | Dest calc | Amount / orient | Class | Gameplay-active? |
|---|---|---|---|---|---|---|---|---|
| `0x55C7A` | `0x55C5E ← 0x55C4A ← 0x050438` (scene fill) | `a5@0x10F8` (=0xC00000, seeded 0x0503F6/0x05040C) | `0x55C7A` (64 sub-cells, +256, **no collision**) | src `0x10D104` + desc `0x10D100` | `*(a0)+`=word0; word1 @ `d2*32 + a5@0x10F6*2` | 64-cell strip × 64 cols (whole map) | **scene init** | no (fill loop only) |
| `0x55C7A` | `0x55C5E ← 0x55C4A ← **0x055B8E**` | `a5@0x10F8` | same | same | same | strip | **UNRESOLVED** (see below) | ? — MAME shows layer-A scroll static in gameplay |
| `0x0561B6` | C-window clear (also clears tilemap1) | immediate `#0xC00000` | inline `movel #0x20` ×4096 | constant `0x00000020` | linear | full quadrant (both maps) | clear | scene transition |

## Cursor setup only (no direct write here; feeds a writer)
| Arcade PC | Sets | Value | Feeds |
|---|---|---|---|
| `0x0503F6`,`0x05040C` | `a5@0x10F8` (0x10D0F8) | 0xC00000 | 0x55C7A (via 0x55C5E) |
| `0x050420` | `a5@0x10A4` (via d0) | 0xC04000 | tilemap1 publisher (0xC04000 quadrant), `sel==1` scenes |
| `0x055E54` | `a5@0x10A0` | 0xC00400 | tilemap1 publisher `0x055968`, guard `a5@0x13AA==2` — writes 0xC00xxx via the *tilemap1* cell path (one proven case of the tilemap1 publisher pointed at the 0xC00000 quadrant) |

## Shared primitives
- `0x0561B6` C-window clear (both maps) · `0x05A4DE` block-copy engine (frontend art, any quadrant) · boot clear `0x00054A` (all four quadrants).

## Frontend / item-only (classify, do not reconstruct here)
| Arcade PC | Base | Note |
|---|---|---|
| `0x056032`,`0x05605C` | 0xC00xxx | item/status page sources |
| `0x0561C6` | 0xC00000 | C-window clear a1 (shared, above) |
| boot `0x00054A`,`0x03AF2C` | quadrants | init/frontend clears |

## Unresolved candidates
1. **`0x055B8E` → 0x55C4A activation.** Second caller of the tilemap0 publisher; whether it runs during gameplay (and thus streams tilemap0) is unproven. MAME evidence: layer-A (tilemap0) scroll stayed static (0x0149) during Stage-1 movement, suggesting tilemap0 is not scrolled/streamed there — but 0x055B8E may run in other scenes or update content without scroll. Next: reconstruct 0x055B8E's caller/guard, or MAME-tap writes to 0xC00000 during gameplay.
2. **0xC0C000 quadrant content.** No scene-fill/gameplay cursor targets it; boot-clear only. Next: confirm from taito/pc080sn.cpp whether it is a hardware mirror/auxiliary region.

## Summary
Tilemap0 (background, layer A) is populated by its own publisher chain `0x55C4A→0x55C5E→0x55C7A` (64-cell strips, no collision, tables 0x10D100/0x10D104), driven by the scene fill loop `0x0503E4` at scene setup. The gameplay triggers drive only tilemap1. Whether `0x055B8E` ever streams tilemap0 in gameplay is the one open producer question.
