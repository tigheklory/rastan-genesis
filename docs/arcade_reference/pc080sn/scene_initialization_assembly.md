# PC080SN Scene Initialization & Tilemap0 — Assembly Facts (authoritative)

`a5=0x10C000`. Machine-verified constants: `0xC08000=12615680`, `0xC00000=12582912`, **`0xC0BF00=12631808`** (the 0x050420 immediate — NOT 0xC04000; a prior decimal→hex slip), `0x3FFC=16380`, `0x3F00=16128`, `0x100=256`; tilemap0 tables `0x10D100=1102080`, `0x10D104=1102084`. Disassembly re-derived from the original ROM opcodes (rastan maincpu, Capstone m68k).

## §1 Scene fill loop `0x0503E4`
```
0x0503E4 cmpiw #1,a5@(4264) ; beqs 0x5040c
  (sel!=1) 0x0503EC movel #0xC08000,0x10D0A0 ; 0x0503F6 movel #0xC00000,0x10D0F8 ; 0x050400 movel #0xC08000,0x10D0A4
  (sel==1) 0x05040C movel #0xC00000,0x10D0F8 ; 0x050416 movel #0xC08000,0x10D0A0 ; 0x050420 movel #0xC0BF00,%d0 ; 0x050426 movel %d0,0x10D0A4
0x05042C movew #64,0x10D0AA           ; loop counter
LOOP 0x050434:
  bsrw 0x55948                        ; publish tilemap1 strip (sel==0→strip_A 0x55968; else→strip_B 0x55990)
  bsrw 0x55c4a                        ; publish tilemap0 strip
  cmpiw #1,a5@(4264)/0x10A8
   (sel!=1) subil #0x3FFC,0x10D0A0 ; subil #0x3FFC,0x10D0F8
   (sel==1) a5@(4260)/0x10A4 -= 0x100 ; subil #0x3FFC,0x10D0F8
  subqw #1,0x10D0AA ; cmpiw #0 ; bne 0x050434
0x050482 rts
```
**Function entry = 0x0503DC** (`bsr 0x55904` descriptor rebuild; `bsr 0x55C2E`; then the fill above). **selector==1 seeds `a5@0x10A4 = 0xC0BF00`** (verified opcode `20 3C 00 C0 BF 00` = `move.l #$C0BF00,d0`), and each iteration decrements it by `0x100`. See §9 for the full destination geometry. Callers: see §11.

## §2 Tilemap0 publisher chain (parallel to tilemap1; **NO collision**)
```
0x055C4A movel a5@(4348)/0x10FC -> a5@(4390)/0x1126 ; bsrw 0x55c5e ; addqw #1,a5@(4342)/0x10F6 ; bsrs 0x55bec ; rts
0x055C5E moveal a5@(4344)/0x10F8,a0 ; a1=#0x10D104 ; a3=#0x10D100 ; a2=*(a3) ; bsrw 0x55c7a ; movel a0,a5@(4344) ; rts
0x055C7A cell producer:
   d2=0
   loop: movew *(a1),*(a0)+            ; word0 = source ; a0 += 2
         d7=d2<<5 ; d0=a5@(4342)<<1 ; a2off = d7+d0 ; movew *(a2+off),*(a0)  ; word1 = tile
         adda #254,a0                  ; +256 total
         d2++ ; cmpiw #64 ; bne        ; **64 sub-cells** (tilemap1's 0x0559B2 does 4)
   rts
```
- Cursor `a5@0x10F8` (0xC00000). Tables `0x10D100` (descriptor ptrs) / `0x10D104` (source words) — distinct from tilemap1's `0x10D040`/`0x10D080`.
- No `subil #0xC08000 ... addil #0x10DE00` sequence ⇒ tilemap0 produces **no collision**.
- **Callers of 0x55C4A: 0x050438 (scene fill loop) AND 0x055B8E (the gameplay VERTICAL tilemap0 streamer — 0x055B60 routine, publishes on 8px vertical crossings, dest 0xC00000+(a5@0x10F4<<6)+(a5@0x10F6<<2)).** Tilemap0 IS gameplay-active (vertical stream + half-rate parallax X-scroll).

## §3 C-window clear `0x0561B6` (both tilemaps → tile 0x0020)
```
0x0561B6 d1=#4096 ; d0=#32 (=0x00000020) ; a0=#0xC08000 ; a1=#0xC00000
loop: movel d0,(a0)+ ; movel d0,(a1)+ ; dbne
```
Each long = word0 `0x0000`, word1 `0x0020`. 4096 longs = one 0x4000 quadrant per map. This is the **clear-fill pair**: word0 `0x0000`, word1 `0x0020` (the `clear_fill_tile_0x0020`). It proves the clear-state word0 = `0x0000` (vs streamed word0 `0x0003`); it does **NOT** prove the tile's pixels are blank/transparent/all-pen-0 — that is a decoded-gfx-ROM detail not yet inspected (see §10).

## §4 Selectors 4/5/6 (non-publication map commands)
No immediate write to `a5@0x10A8` exists; the ONLY writer is `0x0558F8` (map byte). Values 4/5/6 are consumed by NON-PC080SN routines:
- `0x05127C`: `cmpiw #4` → if `a5@0x11DE < 216` set event flags `a5@0x1376/0x1384/0x13C6 = 1/1/1`; `cmpiw #5` → if `a5@0x11DE < 80` set `= 1/2/1`. (Position-gated event/spawn triggers.)
- `0x05274C`: `cmpiw #4/#5/#6` all → `0x527CC movew #7,a5@(4328)/0x10E8`, then continue; no tilemap write.
- The gameplay dispatcher `0x0556A6/0x055738/0x0557C4` matches only 0/1/2 ⇒ selector 4/5/6 → all pending bits set, **zero PC080SN publication**.

## §5 Scene-to-gameplay handoff (initial state)
After `0x0503E4` completes, both tilemaps hold 64 columns. Gameplay then runs the per-frame path (gameplay_control.c): the map pointer `a5@0x10C6` walks the map byte stream, `0x0558E0` loads each new selector, and the ring counters `a5@0x10CA`/`a5@0x10CC` advance. Tilemap1 cursors `a5@0x10A0`/`a5@0x10A4` are recomputed per crossing from the ring counters (they are NOT carried from the fill loop — the fill loop's decrementing values are overwritten by the triggers' `0xC08000 + off` computation). Descriptor tables `0x10D000/0x10D040/0x10D080` (tilemap1) and `0x10D100/0x10D104` (tilemap0) are the persistent source state. Scroll is committed by `0x055AB4`.

## §6 Tilemap roles + scroll wiring (runtime-verified; CORRECTED)
Scroll axes proven by behavior: horizontal movement changes **`0xC40000` and `0xC40002` = X-scroll**; `0xC20000/2` = Y-scroll (static in a horizontal-only test because Y didn't change). Offset 0 moves at HALF the rate of offset 2 (measured Δ −4 vs −9 over the same interval) ⇒ offset 0 = tilemap0 (parallax), offset 2 = tilemap1. Therefore:
- **tilemap1 @ 0xC08000 = foreground/playfield**: X `0xC40002`←a5@0x10AE, Y `0xC20002`←a5@0x10B0; **full-rate** scroll; collision.
- **tilemap0 @ 0xC00000 = background**: X `0xC40000`←a5@0x10EC (**half-rate parallax**, 0x055B92 `lsrw #1`), Y `0xC20000`←a5@0x10EE. **tilemap0 is NOT static** — it parallax-scrolls and streams vertically (0x055B8E).
(Earlier "tilemap0 static / layer-A" wording is retracted: it came from reading the Y register during a horizontal-only test.)

## §7 Quadrant use (CORRECTED — the earlier "sel==1 → 0xC04000" claim was an arithmetic error)
CPU→device mapping (device offset = `(addr−0xC00000)/2`; `pc080sn.cpp` header + `word_w`):
- **0xC00000–0xC03FFF** = tilemap0 (BG name RAM).
- **0xC04000–0xC041FF** = BG rowscroll RAM (`m_bgscroll_ram[0]`, only verified used on Topspeed); **0xC04200–0xC07FFF** = unused. **Rastan uses global scroll (0xC40000/0xC20000), never per-line — so it only ever CLEARS this region** (boot 0x00054A, frontend 0x03AF52). No tile content is ever streamed here.
- **0xC08000–0xC0BFFF** = tilemap1 (FG name RAM).
- **0xC0C000–0xC0C1FF** = FG rowscroll RAM; **0xC0C200–0xC0FFFF** = unused. Rastan only clears it (frontend 0x03AF62).

The scene-fill (`0x050420`) does **NOT** touch 0xC04000 — it seeds `a5@0x10A4 = 0xC0BF00` (tilemap1 row 63) and fills tilemap1 upward. See §9.

## §8 Name-RAM cell format (word0/word1) — SOURCE-CONFIRMED
Confirmed against official MAME `src/mame/taito/pc080sn.cpp` (`get_tile_info`). Each tile = **2 words**, `word0` (even addr) and `word1` (odd addr):
- **word1 = tile code, mask `0x3FFF`** (`code = ram[2*idx+1] & 0x3fff` — 14-bit code). Arcade codes seen (~0x06xx tilemap0 / 0x00xx tilemap1) all fit.
- **word0 = attribute** (`attr = ram[2*idx]`): **colour = `attr & 0x1FF`** (bits 0-8, 9-bit palette select); **flip = `(attr & 0xC000) >> 14`** via `TILE_FLIPYX` ⇒ **bit14 = X-flip, bit15 = Y-flip**.
- Streamed word0 `0x0003` ⇒ colour 3, no flip. Clear word0 `0x0000` ⇒ colour 0, no flip.

## §9 Selector-1 scene-fill destination geometry (re-derived from opcodes)
Full call chain traced from ROM opcodes: `0x0503DC → 0x050434 → 0x055948 → 0x055990 (strip_B) → 0x055A14 (cell producer)`.

**Cell producer 0x055A14** (`d2` loops 0→3, 4 cells): per cell writes `word0 → (a0)` (0x055A1C) then `word1 → (a0+2)` (0x055AA4), advancing `a0 += 4` per cell (0x055A82 `addq.l #2,a0` + 0x055AA6 `addq.l #2,a0`). Plus ONE collision store `word1 → 0x10DE00 + (a0−0xC08000)/2` (0x055A62). *(The second collision address computed at 0x055A64–0x055A80 is loaded into a6 but never stored — dead; confirms "no second collision store".)* → **4 cells × 4 bytes = 0x10 bytes / call.**

**strip_B 0x055990**: reads `a0 = a5@0x10A4`, loops **16×** calling 0x055A14 with `a0` carried → **16 × 0x10 = 0x100 bytes = 64 cells = one full 64-tile horizontal row.**

**Scene-fill loop (sel==1)**: `a5@0x10A4` starts at **0xC0BF00** and decrements by **0x100 (one row) per iteration**, for **64 iterations**:

| iter | strip start | strip end | tilemap1 row |
|---|---|---|---|
| 0 | 0xC0BF00 | 0xC0BFFF | 63 (bottom) |
| 1 | 0xC0BE00 | 0xC0BEFF | 62 |
| … | … | … | … |
| 63 | 0xC08000 | 0xC080FF | 0 (top) |

- **Formula:** iteration *k* writes `[0xC0BF00 − k·0x100, +0xFF]`, k = 0…63.
- **Displayed range touched:** `0xC08000–0xC0BFFF` **exactly** = 0x4000 bytes = 4096 cells = the whole 64×64 tilemap1.
- **Non-displayed writes:** NONE. No write reaches `0xC0C000+`. No write touches `0xC04000`.
- **Overlap/wrap:** none — 64 rows × 0x100 = 0x4000 distinct bytes, contiguous, bottom-to-top. No modular wrap in the code (plain subtract; the map is filled exactly once).
- **Meaning:** selector 1 = vertical-scroll stage; it fills full horizontal rows from the bottom row (63) up to the top (0). The start `0xC0BF00 = 0xC08000 + 0x3F00` equals the gameplay selector-1 dispatcher's initial destination (`0xC08000 + 0x3F00` when ring counters are 0) — an independent cross-check that 0xC0BF00 (not 0xC04000) is correct.

## §10 Draw order & visual roles — SOURCE-CONFIRMED
From official MAME `src/mame/taito/rastan.cpp` `screen_update` (back→front):
```
m_pc080sn->tilemap_draw(screen, bitmap, cliprect, 0, TILEMAP_DRAW_OPAQUE, 1);  // tilemap0: BACK, opaque, prio 1
m_pc080sn->tilemap_draw(screen, bitmap, cliprect, 1, 0, 2);                     // tilemap1: over tm0, transparent, prio 2
m_pc090oj->draw_sprites(screen, bitmap, cliprect);                             // sprites: FRONT
```
⇒ **tilemap0 = opaque background (drawn first, no transparency — fully covers the backdrop); tilemap1 = transparent playfield (pen 0 transparent, so tilemap0 shows through open cells); sprites frontmost.** Confirms the runtime roles (tm0 half-rate parallax background, tm1 full-rate playfield). gfx = `gfx_8x8x4_packed_msb`, 0x80 colour codes (8×8, 4bpp).
`clear_fill_tile_0x0020` (word1=0x0020, word0=0x0000): on tilemap1 (transparent layer) its open cells reveal the background; on tilemap0 it draws opaquely. Whether tile 0x20's own pixels are all pen-0 is a decoded-gfx-ROM detail (byte content not inspected), but its **layer behavior is now fully determined** by the draw order above.

## §11 Callers of the scene-fill routine 0x0503DC (containing 0x0503E4) — enumerated
ROM-wide branch/jsr scan (word-aligned, bsr.w/bsr.b/jsr.l/jmp.l):
- **0x0503DC** ← **one direct caller: `0x050206 bsr.w 0x503DC`**. (No other bsr/jsr/jmp targets 0x0503DC or 0x0503E4.)
- **0x050206** sits in scene-(re)init routine **0x0501E2**, as step 4 of a setup sequence: `0x0501FA bsr 0x50248`, `0x0501FE bsr 0x502BA`, `0x050202 bsr 0x502CC`, **`0x050206 bsr 0x503DC`** (the fill), `0x05020A bsr 0x504FA`, `0x05020E bsr 0x5053A`. The whole block is gated at `0x0501EA cmpi.w #1,a5@0x13E2 ; beq 0x50246` ⇒ **the 64-iteration fill runs on scene (re)initialization only (a5@0x13E2 ≠ 1), not per frame.**
- **0x0501E2** ← **`0x045316 jsr 0x0501E2`** (verified real code; context sets a5@0x2B8=0x28 and writes 0x380000 = the stage/scene entry handler).
- **Selector source:** the fill reads the current map selector `a5@0x10A8` (written only by `0x0558F8` from the map byte stream). `==1` selects the vertical row-fill geometry above; `!=1` uses the column geometry (`0x10A0/0x10A4 = 0xC08000`, decrement 0x3FFC).

## §12 Actual (independent) 0xC04000 accesses — classified separately
The two real immediate `0xC04000` references in the ROM (neither is 0x050420):
- **0x00054A (boot clear):** `lea 0xC00000,a0 ; lea 0xC04000,a1 ; bsr 0x57C` — boot-time clear pairing tilemap0 (0xC00000) with the 0xC04000 (BG rowscroll/unused) region.
- **0x03AF52 (frontend clear, in the 0x03AF2C family):** `lea 0xC04000,a0 ; move.w #0x2000,d1 ; clr.l d0 ; bsr 0x3AD3C` — zeros 0xC04000 for 0x2000 words (0xC04000–0xC07FFF); immediately followed by `0x03AF62 lea 0xC0C000,a0 ; #0x2000 ; clr d0` zeroing 0xC0C000–0xC0FFFF. The same routine just above fills the displayed tilemaps (0xC00000, 0xC08000) with tile 0x20.
Both are **clears of the BG/FG rowscroll + unused regions**; Rastan never streams tile content into 0xC04000 and never uses PC080SN per-line scroll.
