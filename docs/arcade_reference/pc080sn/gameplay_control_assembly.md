# PC080SN Gameplay Control — Assembly Facts (authoritative)

`a5=0x10C000`; `0xC08000=12615680`, `0x3F00=16128`. Constants for the tables: `0x10D000=1101824`, `0x10D040=1101888`, `0x10D080=1101952`.

## Direction dispatcher (4 direction branches; each latches a pending bit when not the active selector)
Order in code: sel==1 (0x0556A6) → sel==2 (0x055738) → sel==0 (0x0557C4) → 4th path (0x055854). Each computes an 8px tile-cross, and on cross builds a ring dest and calls `0x055948`.

| Sel | Guard | Boundary accum (`+=` delta, `btst #3`) | Ring dest into | Offset formula (added to 0xC08000) | Scroll accum (`&511`) | Pending bit (a5@0x10D0) | dir code (a5@0x13D0) |
|---|---|---|---|---|---|---|---|
| **1** | `cmpiw #1,a5@(4264)` | `a5@0x10B4 += a5@0x10DA` | `a5@0x10A0`? → **`a5@0x10A4`** (4260) | `0x3F00 − ((a5@0x10CC<<10) + (a5@0x10CA<<8))` | `a5@0x10B0 += delta` | bit5 | 0 |
| **2** | `cmpiw #2,a5@(4264)` | `a5@0x10B6 += a5@0x10DA` | `a5@0x10A4` (4260) | `(a5@0x10CC<<10) + (a5@0x10CA<<8)` | `a5@0x10B0 −= delta` | bit4 | 1 |
| **0** | `cmpiw #0,a5@(4264)` | `a5@0x10B2 += a5@0x10D8` | `a5@0x10A0` (4256) | `(a5@0x10CC<<4) + (a5@0x10CA<<2)` | `a5@0x10AE −= delta` | bit6 | 3 |
| 4th | 0x055854 (`a5@(524)`, `a5@0x10B8`) | `a5@0x10B8` | — | (not fully reconstructed) | `a5@0x10AE += delta` | bit7 | — |

- Shift facts: sel-1/2 use `lslw #8; lslw #2` on the group (=`<<10`) and `lslw #8` on col (=`<<8`); sel-0 uses `lslw #4` on group and `lslw #2` on col. Verified from opcodes (0x0556DC-0x0556EA, 0x05576E-0x05577C, 0x05580A-0x055816).
- Each branch ends `movew #k,a5@(5072); movew #k,%d2; jsr 0x406a4` (k = 0/1/3), i.e. it forwards the direction code to `0x406a4` (a consumer outside this subsystem).
- Extra gates: 0x05572E `cmpiw #8,a5@(4282)` and 0x0557BA `cmpiw #160,a5@(4280)` guard the sel-2 and 4th paths (range limits before the direction check).

## Ring counter progression (a5@0x10CA, a5@0x10CC)
- `0x055948` increments `a5@0x10CA` by 1 after each strip publish (0x055954/0x05595E).
- `0x0558A2`: `if a5@0x10CA==4 { 0x558C6 ; 0x055904 ; a5@0x10CC++ ; if a5@0x10CC==16 { 0x558E0 } }`.
- `0x558C6`: `for 16: *(0x10D000 + i*4) += 4 ; then a5@0x10CA = 0` (advance the 16 base pointers a group at a time).
- `0x558E0`: `a5@0x10CC = 0 ; a5@0x10C6 += 1 ; a5@0x10A8 = *(byte)(a5@0x10C6) ; a5@0x136C = a5@0x10A8 ; a5@0x13E++`.
- **So: col `a5@0x10CA` 0→3, group `a5@0x10CC` 0→15 → 4×16 = 64 ring positions; the SELECTOR (direction) is refreshed from the map byte stream every 16 groups.**

## Selector source (proven)
`a5@0x10A8` is written ONLY at `0x0558F8 movew %d0,0x10d0a8`, where `d0 = *(byte) a5@0x10C6` (the map source pointer). Values seen: 0,1,2 (streaming dispatcher here) and 4,5,6 (in the scene-setup families 0x0512xx/0x0526xx-0x0528xx — different scenes; exact meaning unresolved). The dispatch `0x055948` tests only `==0` (strip_A) vs else (strip_B); the cell producer `0x055A14` tests `==2` to disable its sub-index reversal.

## Descriptor rebuild `0x055904` (authoritative)
```
a0=0x10D000 ; a1=0x10D040 ; a2=0x10D080 ; d0=16
loop: a4=*(a0) ; *(a2)+ = *(a4)       ; source word = word0 of base entry
      d1 = *(a4+2) ; a4 = (u16)d1 ; *(a1)+ = a4   ; descriptor ptr = zero-extended word1
      a0 += 4 ; d0-- ; bne
```
Publishers consume: `a3 = 0x10D040` (descriptor ptrs) and `a1 = 0x10D080` (source words). **These addresses (0x10D040/0x10D080/0x10D000) correct the earlier "0x10D1C0/0x10D200" slip.**

## Scroll commit `0x055AB4` (write-only)
`0xC20000 = a5@0x10EE` (layer-A X); `0xC40000 = a5@0x10EC` (layer-B X); `0xC20002 = a5@0x10B0` (layer-A Y); `0xC40002 = a5@0x10AE` (layer-B Y). The direction dispatcher maintains `a5@0x10AE` (sel-0) and `a5@0x10B0` (sel-1/2) with `&511` wrap; X scrolls (`a5@0x10EC/0x10EE`) are set outside this subsystem.

## Camera ↔ ring relationship (proven)
Per-frame camera step deltas `a5@0x10D8` (horizontal) / `a5@0x10DA` (vertical) accumulate into the boundary accums (`a5@0x10B2/0x10B4/0x10B6`); each 8-px (`btst #3`) crossing triggers one strip publish and advances the ring counters. The published strip's start cell is a pure function of the ring counters (`a5@0x10CC`,`a5@0x10CA`) per the offset formulas — no camera value enters the destination directly; the camera only gates *when* to publish and updates the hardware scroll registers (`&511` = 512 px = 64-tile wrap).
