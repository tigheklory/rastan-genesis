# PC080SN Scene Initialization & Tilemap0 — Assembly Facts (authoritative)

`a5=0x10C000`. Constants: `0xC08000=12615680`, `0xC00000=12582912`, `0xC04000=12631808`, `0x3FFC=16380`; tilemap0 tables `0x10D100=1102080`, `0x10D104=1102084`.

## §1 Scene fill loop `0x0503E4`
```
0x0503E4 cmpiw #1,a5@(4264) ; beqs 0x5040c
  (sel!=1) 0x0503EC movel #0xC08000,0x10D0A0 ; 0x0503F6 movel #0xC00000,0x10D0F8 ; 0x050400 movel #0xC08000,0x10D0A4
  (sel==1) 0x05040C movel #0xC00000,0x10D0F8 ; 0x050416 movel #0xC08000,0x10D0A0 ; 0x050420 d0=#0xC04000 ; movel d0,0x10D0A4
0x05042C movew #64,0x10D0AA           ; loop counter
LOOP 0x050434:
  bsrw 0x55948                        ; publish tilemap1 strip (gameplay publisher)
  bsrw 0x55c4a                        ; publish tilemap0 strip
  cmpiw #1,a5@(4264)
   (sel!=1) subil #16380,0x10D0A0 ; subil #16380,0x10D0F8
   (sel==1) a5@(4260) -= 256 ; subil #16380,0x10D0F8
  subqw #1,0x10D0AA ; cmpiw #0 ; bne 0x050434
0x050482 rts
```
Callers of 0x0503E4: (per-scene setup) — not enumerated here (scene checkpoint). Fills BOTH tilemaps' 64 columns at setup.

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
- **Callers of 0x55C4A: 0x050438 (scene fill loop) AND 0x055B8E.** The 0x055B8E path's gameplay activation is not proven here (MAME shows layer-A/tilemap0 scroll static during gameplay). See tilemap0_producers.md / unresolved.

## §3 C-window clear `0x0561B6` (both tilemaps → tile 0x0020)
```
0x0561B6 d1=#4096 ; d0=#32 (=0x00000020) ; a0=#0xC08000 ; a1=#0xC00000
loop: movel d0,(a0)+ ; movel d0,(a1)+ ; dbne
```
Each long = word0 `0x0000`, word1 `0x0020`. 4096 longs = one 0x4000 quadrant per map. **Proves the blank/base tile = `0x0020`** and the clear-state word0 = `0x0000` (vs streamed word0 `0x0003`).

## §4 Selectors 4/5/6 (non-publication map commands)
No immediate write to `a5@0x10A8` exists; the ONLY writer is `0x0558F8` (map byte). Values 4/5/6 are consumed by NON-PC080SN routines:
- `0x05127C`: `cmpiw #4` → if `a5@0x11DE < 216` set event flags `a5@0x1376/0x1384/0x13C6 = 1/1/1`; `cmpiw #5` → if `a5@0x11DE < 80` set `= 1/2/1`. (Position-gated event/spawn triggers.)
- `0x05274C`: `cmpiw #4/#5/#6` all → `0x527CC movew #7,a5@(4328)/0x10E8`, then continue; no tilemap write.
- The gameplay dispatcher `0x0556A6/0x055738/0x0557C4` matches only 0/1/2 ⇒ selector 4/5/6 → all pending bits set, **zero PC080SN publication**.

## §5 Scene-to-gameplay handoff (initial state)
After `0x0503E4` completes, both tilemaps hold 64 columns. Gameplay then runs the per-frame path (gameplay_control.c): the map pointer `a5@0x10C6` walks the map byte stream, `0x0558E0` loads each new selector, and the ring counters `a5@0x10CA`/`a5@0x10CC` advance. Tilemap1 cursors `a5@0x10A0`/`a5@0x10A4` are recomputed per crossing from the ring counters (they are NOT carried from the fill loop — the fill loop's decrementing values are overwritten by the triggers' `0xC08000 + off` computation). Descriptor tables `0x10D000/0x10D040/0x10D080` (tilemap1) and `0x10D100/0x10D104` (tilemap0) are the persistent source state. Scroll is committed by `0x055AB4`.

## §6 Tilemap roles + scroll wiring (MAME-confirmed)
Runtime (arcade, Stage 1 movement): **layer B `0xC40000/2` scrolls with the playfield** (X 0x01B3.., Y 0x0166.. change with movement); **layer A `0xC20000/2` stays static** (0x0149). The gameplay stream (tilemap1) updates `a5@0x10AE → 0xC40002`. Therefore:
- **tilemap1 @ 0xC08000 ↔ layer B (`0xC40000/2`) = scrolling foreground/playfield** (streamed + collision).
- **tilemap0 @ 0xC00000 ↔ layer A (`0xC20000/2`) = background** (filled at scene-init, static scroll in the tested segment).

## §7 Quadrant use
- **0xC04000** IS content-written: the `sel==1` scene-fill path (`0x050420`) uses it as the tilemap1 cursor `a5@0x10A4` — so some scenes render from 0xC04000. Not a dead mirror.
- **0xC0C000**: only boot-lea'd / cleared; no scene-fill or gameplay cursor targets it. Likely mirror/auxiliary (unconfirmed content — unresolved).
