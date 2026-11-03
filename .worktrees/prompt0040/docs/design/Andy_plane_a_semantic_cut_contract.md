# Plane A Semantic Cut Contract (research; no source/build) — CORRECTED

**Type:** architecture research. **Production source / build / counter:** unchanged (240).
**Authority:** original arcade opcodes + `docs/arcade_reference/pc080sn/` + `address_map.json`.
**Governs:** `RULES.md` §11 + `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`.
Scope: Plane A / tilemap1 only (four operations). **No Plane B.**

> **Correction note (rev 2):** this revision (a) corrects the Build 0240 root cause and (b)
> re-evaluates the cut. The earlier "select 0x0559B2/0x055A14, recommend a Cody task"
> conclusion is **withdrawn**: those points still consume PC080SN-shaped state, so they are a
> *transitional interception*, not the final semantic cut. The final cut is **not yet
> selectable** on current evidence — see §5 STOP.

`a5 = 0x10C000`. Chip constants: `0xC08000` (C-window base, 12615680), `0x10DE00` (collision,
1105408), `0x100`/row C-window stride, `0x3FFC` fill back-step, `0x4000` C-window column span.

---

## 1. Build 0240 root cause — CORRECTED

**Proven root:** the native cell helper `.Lfg_native_convert_cell` (tilemap_hooks.s) **clobbers
live caller registers** — it freely uses `d3, d4, d5, d7, a2, a3` and returns with **no
save/restore** (`rts` with no `movem`). The arcade publication/segment loop that calls it holds
its loop counter and table pointers in registers (the driver 0x055968 uses `d1`=16, `a1`, `a3`;
the Genesis-relocated caller chain likewise). Clobbering `a2/a3`/`d`-registers across the call
corrupts the caller's loop control, so **the loop never terminates → the READY-screen hang.**

The observed `a5@0x10A0 = 0xC08004` and `a5@0x10AA = 0x003F` were **symptoms of the hung loop**
(it stopped after ~one iteration), **not** a bookkeeping fault. **Do NOT** attribute the stall to
`fg_native_owner`, cursor-advance suppression, or "+4 vs +0x4000" arithmetic — no evidence shows
those were faults. (The +0x4000-then-−0x3FFC = +4/column arithmetic in 0x050444 is a *real*
arcade mechanism, but it was not the 0240 failure.) **Lesson:** any native helper called inside
an arcade loop must preserve every caller register it does not own (movem save/restore).

## 2. Control flow

### 2a. Retained arcade semantic side (map/source/ring/direction/scroll/collision-timing)
```
scene-init 0x0501E2 → 0x0502CC : segment idx a5@0x13E, strip-source bases 0x10D000,
                                 map-stream ptr 0x10C6                                  [semantic]
  fill 0x0503DC : bsr 0x55904 (rebuild desc ptrs 0x10D040 + source words 0x10D080;
                               load first selector a5@0x10A8)                            [semantic]
                 seed C08000 cursors a5@0x10A0/0x10A4  (0x0503EC/0x050400/0x050426)      [CHIP seed]
  fill loop 0x050434 ×64 : bsr 0x55948 ; (Plane B 0x55C4A) ;
                           C08000 back-step  a5@0x10A0 -= 0x3FFC / a5@0x10A4 -= 0x100     [CHIP arith]
gameplay 0x0556xx/0x0557xx : 8px tile-cross triggers; scroll accums a5@0x10AE X /
                             a5@0x10B0 Y ; pending-dir latch a5@0x10D0 → bsr 0x55948      [semantic]
dispatch 0x055948 : sel=a5@0x10A8 → 0x55968|0x55990 ; a5@0x10CA += 1 ;
                    bsr 0x558A2 (0x10CA==4→base +=4 & rebuild 0x55904 ; group 0x10CC ;
                    0x558E0 map-stream +1, next selector, a5@0x13E +1)                    [semantic]
drivers 0x055968/0x055990 : a0 = a5@0x10A0/0x10A4 ; ×16 seg over a3=0x10D040/a1=0x10D080  [MIXED]
```

### 2b. PC080SN chip tail (the geometry the final architecture must REMOVE, not reproduce)
```
cell producers 0x0559B2 / 0x055A14 :
   movew a1@, a0@                        ; WORD0 attr  → C08000 name-RAM
   movew tile, a0@                       ; WORD1 tile  → C08000 name-RAM
   a0 += 0x100/cell                      ; C-window row stride
   *((a0-0xC08000)>>1 + 0x10DE00) = coll ; collision indexed THROUGH the chip address
   (0x055A14: notw/andi #3 strip complement when sel≠2)
```

## 3. Boundary ladder classification

| Boundary | Class | Why |
|---|---|---|
| **0x050434** scene-fill publication | **MIXED** | the "publish one strip" decision is semantic, but it is wrapped by C08000 cursor seeding (0x0503EC) and the fill-loop C08000 back-step (−0x3FFC) — chip-geometry bookkeeping. |
| **0x055948** dispatch | **SEMANTIC** (highest purely-semantic point) | decides selector/direction, advances ring sub-index 0x10CA, runs source/ring progression 0x558A2. Touches **no** C08000 itself. But it *delegates* position to the C08000-cursor driver below. |
| **0x055968 / 0x055990** drivers | **MIXED semantic/chip** | semantic: 16-segment descriptor walk (a1/a3 over 0x10D040/0x10D080), ring. Chip: `a0 = a5@0x10A0` C08000 cursor load, save-back, and the C-window stride it carries. |
| **0x0559B2 / 0x055A14** cell producers | **FULLY PC080SN-specific** | C08000 name-RAM word writes, word0/word1 cell layout, +0x100 stride, collision indexed through the chip address. |

## 4. 0x0559B2 / 0x055A14 disposition

**Transitional cell-write interception boundaries — NOT the final native semantic cut.** A
helper placed here still *consumes* PC080SN-shaped state: the C08000 destination cursor `a0`,
the word0/word1 cell layout, the `+0x100` C-window stride, and collision indexed as
`(a0−0xC08000)>>1 + 0x10DE00`. Per `PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` §2 litmus,
consuming a chip-shaped cursor/address is transitional, not final. Intercepting here can produce
correct visuals, but it reproduces the chip geometry rather than removing it.

## 5. Final semantic cut — NOT YET SELECTABLE (STOP)

The final native architecture must **remove, not reproduce**: C08000 cursor seeding + range
arithmetic; word0/word1 name-RAM representation; C-window row/column strides and back-steps;
and collision indexed through a PC080SN address. Collision must instead be indexed from **logical
row/column** (the collision map 0x10DE00 is in fact logically addressed:
`(a0−0xC08000)>>1 = (row·64+col)·2`, so `coll_addr = 0x10DE00 + (row·64+col)·2` — a *logical*
index that does not require `a0`).

The arcade **semantic decision** ("publish an entering column/row, from these descriptor
sources, this selector/strip, with this logical terrain+collision") is complete at/above
**0x055948**. **But the arcade does not currently expose the logical `(row, col)` of the
published cells independently of the C08000 cursor `a5@0x10A0/0x10A4`** — that cursor *is* the
arcade's position source of truth, and every downstream position/collision index is derived from
it. The ring counters (0x10CA/0x10CC) + scroll accumulators (0x10AE/0x10B0) + selector are the
*inputs* that produce the cursor, and in principle logical `(row,col)` is recoverable from them
(fill: publication n ⇒ column n; gameplay: entering column = `(scroll_x/8)&63`, row = cell
iteration) — **but proving that recovery matches the arcade's a0-derived position exactly across
scene-fill, gameplay, all selectors, selector-2 reversal, and the 63→0 ring wrap is not
established by current evidence.**

**Therefore: STOP on selecting the final semantic cut.** Per the task's stop condition, "the
original arcade evidence does not yet expose semantic row/column sources without reconstructing
PC080SN geometry." Choosing 0x055948/driver as the final cut today would require re-deriving the
geometry the C08000 cursor encodes — which is exactly what must be *proven*, not assumed.

## 6. State classification (semantic tables vs chip-format cursors)

| State | Class |
|---|---|
| descriptor base ptrs 0x10D000 (adv 0x558C6) | **semantic source structure — RETAIN** |
| descriptor-ptr table 0x10D040 (rebuilt 0x55904, `a3`) | **semantic source structure — RETAIN** |
| source-word table 0x10D080 (rebuilt 0x55904, `a1`) | **semantic source — RETAIN** |
| strip index 0x10CA, group 0x10CC | **semantic ring position — RETAIN** |
| selector 0x10A8 | **semantic direction — RETAIN** |
| scroll accums 0x10AE / 0x10B0 (+ 0x10B2/B4/B6) | **semantic camera — RETAIN** |
| collision source (block+20/34) | **semantic terrain — RETAIN** |
| collision *destination* index | must become **logical** `0x10DE00 + (row·64+col)·2` (REMOVE chip-address indexing) |
| **a5@0x10A0 / a5@0x10A4** | **chip-format cursor — REMOVE (target)**; C08000 seed/stride/back-step/dereference are chip geometry. Its logical position must be supplied by ring+scroll semantics, once proven. |
| word0/word1 name-RAM cell pairing | **chip representation — REMOVE**; convert descriptor tile+attr → final Plane A name word |

Distinction: 0x10D000/40/80 are **semantic map-source tables** (which ROM blocks/tiles) and are
kept; `a5@0x10A0/0x10A4` is a **chip-format destination cursor** and is a removal target — not a
semantic field to retain.

## 7. Build 0240 disposition

**Reusable:** arcade descriptor tables (0x10D040/0x10D080) + rebuild 0x55904; the tile+attr → name
word LUT conversion math in `.Lfg_native_convert_cell` (the *conversion* is fine; its **register
discipline** must be fixed — save/restore every non-owned register). **Retire:** the register
clobber (proven 0240 root); and any assumption that the C08000 cursor / word0-word1 / C-window
stride is the target representation (it is transitional interception, §4).

## 8. Unresolved proof blockers (must be resolved before a final cut can be selected)

1. **Logical (row,col) exposure independent of the C08000 cursor**, for each of the four
   operations, proven to match the arcade's a0-derived position across: scene-fill (column &
   row), gameplay entering-column, gameplay entering-row, **selector-2 reversal**, and the 63→0
   ring wrap. Sources to prove: ring counters 0x10CA/0x10CC, scroll 0x10AE/0x10B0, selector.
2. **Logical collision indexing** `0x10DE00 + (row·64+col)·2` proven equal to the arcade's
   `(a0−0xC08000)>>1 + 0x10DE00` for all cells (incl. block+32==0xFF alt).
3. **Gameplay entering-strip identity:** which logical column/row enters on an 8px cross, from
   scroll state alone (no a0).
4. **Plane A residency** logical→physical mapping (policy §9) applied to the derived logical rows,
   while still writing collision for all 64 logical cells.

Until #1–#3 are proven from arcade evidence, the logical position is only available via the
C08000 cursor, and no boundary above the cell producers can publish natively without
reconstructing chip geometry.

## 9. Recommendation

**Cody implementation recommended: NO.** The final semantic cut is not yet proven (§5). Next
research step: prove blockers §8 #1–#3 (derive and validate logical (row,col) + logical collision
index from ring+scroll semantics against a runtime a0 comparison), which would either expose a
true semantic cut at/above 0x055948 or confirm that the arcade only expresses position through
the chip cursor.

A **transitional cell-producer experiment** at 0x0559B2/0x055A14 may be documented and attempted
**separately and labeled transitional** (it intercepts chip-format cell writes and must
save/restore all caller registers per §1) — but it **must not be called the target architecture**
and does not substitute for proving the final cut.

## STOP status

**STOP triggered:** YES, on final-cut selection — arcade evidence does not yet expose semantic
row/column sources without reconstructing PC080SN geometry (§5, §8). No final boundary selected;
no Cody implementation recommended.
