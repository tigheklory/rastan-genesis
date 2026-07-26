# PC080SN Core Publishers — Assembly Facts (authoritative)

Facts the C-like reconstruction obscures. Opcodes are authoritative; constants: `0xC08000=12615680`, `0x10DE00=1105408`, `0x10D200=1101952`, `0x10D1C0=1101888`, `0x3FF00=16128... (0x3F00=16128)`, `0x3FFF=16383`.

## §1 `0x055948` dispatch
```
0x055948 cmpiw #0,a5@(4264)   ; selector a5@0x10A8
0x05594E bnes 0x5595a         ; !=0 -> strip_B
0x055950 bsrw 0x55968         ; ==0 -> strip_A
0x055954 addqw #1,a5@(4298)   ; a5@0x10CA++
0x055958 bras 0x55962
0x05595A bsrw 0x55990         ; strip_B
0x05595E addqw #1,a5@(4298)   ; a5@0x10CA++
0x055962 bsrw 0x558a2         ; post-advance (next checkpoint)
0x055966 rts
```

## §2 `0x055968` strip_A — inputs a0=a5@0x10A0, a1=0x10D200, a3=0x10D1C0, d1=16
Loop `0x5597C`: `a2=*(a3)`; `bsr 0x559b2`; `a5@(4256)=a0` (**saves cursor**); `a3+=4`; `a1+=2`; `d1--; bne`. Registers: destroys d0-d2/d7/a0-a3/fp per callee; returns via rts. Destination range is whatever `a5@0x10A0` holds — set to **0xC08000+off** by the horizontal trigger (§7).

## §3 `0x055990` strip_B — inputs a0=a5@0x10A4, a1=0x10D200, a3=0x10D1C0, d1=16
Identical loop but `bsr 0x55a14` and **no cursor write-back**. Cursor `a5@0x10A4` set to **0xC08000+off** by the vertical trigger (§7).

## §4 `0x0559B2` cell_forward (4 sub-cells, d2=0..3)
```
*(a0) = *(a1)                                  ; word0 (even) = source word
if *(a2+32)==255: cw=*(a2+34)
else: d7=a5@0x10CA<<1 ; d0=d2<<3 ; cw=*(a2+20+d7+d0)
*(0x10DE00 + ((a0-0xC08000)>>1)) = cw          ; collision (subil 0xC08000; lsrl 1; addil 0x10DE00)
a0 += 2
d7=d2<<3 ; d0=a5@0x10CA<<1 ; *(a0)=*(a2+0+d7+d0) ; word1 (odd) = tile
a0 += 254                                      ; net +256 per sub-cell (0x055A04 adda #254)
d2++ ; cmp #4 ; bne
```
Collision-index arithmetic: `20 + (a5@0x10CA<<1) + (d2<<3)`. Tile-index: `0 + (d2<<3) + (a5@0x10CA<<1)`.

## §5 `0x055A14` cell_dir_aware
```
a5@(4912)=1                                    ; side flag a5@0x1330
loop d2=0..3:
  *(a0)=*(a1)                                  ; word0
  d7=a5@0x10CA ; if a5@0x10A8 != 2: d7 = ~d7 & 3   ; DIRECTION REVERSAL (notw; andi #3)
  if *(a2+32)==255: cw=*(a2+34)
  else: d7<<=3 ; d0=d2<<1 ; cw=*(a2+20 + d7 + d0)   ; NB order: sub<<3 + d2<<1 (differs from §4)
  *(0x10DE00 + ((a0-0xC08000)>>1)) = cw        ; collision #1
  *(0x10DE00 + ((((a0-0xC08000)-256) & 0x3FFF) >>1)) = 1   ; collision #2 (wrapped marker '1')
  a0 += 2
  (re-derive d7 same way) ; *(a0)=*(a2+0 + d7<<3 + d2<<1)   ; word1 = tile
  a0 += 254
```
Two differences vs §4: (a) sub-index is reversed unless `a5@0x10A8==2`; (b) a **second** collision write of constant `1` at a wrapped (−256, &0x3FFF) index. Index order is `sub<<3 + d2<<1` (vs §4's `col<<1 + d2<<3`).

## §6 `0x055904` (descriptor rebuild — partial, scope-limited)
Builds the 16-long descriptor-pointer table at `0x10D1C0` and the source table `0x10D200` consumed above. Each descriptor `a2` provides: `+0` tile field, `+20..` collision/tile sub-array, `+32` sentinel (255 ⇒ use `+34`), `+34` fallback collision. Full rebuild logic deferred to the next checkpoint.

## §7 Cursor/selector setup (proof of layer ownership)
- **Horizontal trigger `0x055808`:** `d0=(a5@0x10CC<<4)+(a5@0x10CA<<2)`; `d0 += 0xC08000`; `a5@(4256)=d0` → strip_A cursor = **0xC08000+off**; then `bsr 0x55948`; updates scroll accum `a5@0x10AE (&511)`.
- **Vertical trigger `0x0556E0`:** `d1 = 0x3F00 − ((a5@0x10CC<<10)+(a5@0x10CA<<8))`; `d1 += 0xC08000`; `a5@(4260)=d1` → strip_B cursor = **0xC08000+off**; then `bsr 0x55948`; updates scroll accum `a5@0x10B0 (&511)`.
- **Both gameplay triggers therefore target `pc080sn_tilemap1_0xC08000`.**
- **Separate path `0x055E54`** (guard `a5@0x139A==2`): `movel #0xC00400, a5@(4256)` → sets the strip_A cursor to **`pc080sn_tilemap0_0xC00000`**. This is NOT one of the gameplay triggers; it establishes that tilemap0 is written by a different, state-gated caller (deferred).
- Selector `a5@0x10A8` is compared against 0/1/2/4/5/6 across the map code (`0x0503E4/0x05043C/0x05127C/0x055738/0x0557C4/…`); the dispatch (§1) only tests `==0`. Its exact write sites are in `unresolved.md`.
