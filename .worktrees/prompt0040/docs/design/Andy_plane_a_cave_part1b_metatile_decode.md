# Andy — Plane-A Cave Part 1B: Static Metatile → 8×8 Tile Decode

**Type:** Analysis / static reverse-engineering. **No production changes. No ROM. Build counter 297 unchanged.**
Baseline: Build 0297. Authority: original arcade Ghidra decompile (`analysis/ghidra/rastan_arcade/exports/`) +
arcade ROM (`build/regions/maincpu.bin`). MAME used only to confirm the cave is reached (Part 1).

## 1. Phase-0 baseline
- **Priors:** KF-014 (tile-LUT, tile-code domain 0x0000..0x3FFF) STRONG — applies (metatile tile codes are in
  that domain); KF-010 (FG→Plane A) STRONG; KF-011 (arcade owns progression) STRONG.
- **HIGH hazards:** KF-011 (respected).
- **Task classification:** EXTENDING (completes the cell-level piece the Part-1 oracle deferred).
- **Issues touched:** OPEN-001/018 (native FG/map), OPEN-017 (FG/collision, rope).
- **Contradiction:** NONE.

## 2. Scope
Statically decode: Stage-1 Plane-A strip-source entry → metatile → individual arcade 8×8 tile codes + collision,
reaching the terminal PC080SN FG writer. Cell-level oracle for outdoor + cave.

## 3. Proven Part-1 starting state
Stage-1 cave is segment-driven (tm0 stays 0). 16 strip-source tables at `arcade_rom 0x1691C..0x3725C`
(0x22C0 apart); strip[i] base = `0x1691C + i*0x22C0 + seg*0x40`, stored in `a5@0x1000+i*4` (= abs 0x10D000),
advanced `+4`/group by `FUN_000558c6`. Cave = segments 4–6 (runtime-confirmed, vertical descent).

## 4. Static decode chain (arcade_pc, from decoded disassembly)
```
a5@0x1000+i*4 (=0x10D000[i])  strip-source pointer  (seed 0x0502E4; +4/group @0x0558CE; page-wrap seed 0x558E0)
   │ dereference
FUN_00055904 @0x055904:
   a4 = *(0x10D000[i])              ; a4 = current strip-source ENTRY address
   0x10D080[i] = *(a4)              ; word0  (movew %a4@,%a2@+ @0x05591A)
   0x10D040[i] = *(a4+2)            ; word1  (movew %a4@(2),%d1 @0x05591E; stored long @0x05592C)
FUN_00055968 @0x055968 (selector 0, loops #16 @0x05596C):
   a1 = 0x10D080 (+2/iter)          ; word0 stream
   a3 = 0x10D040 (+4/iter); a2 = *(a3)   ; a2 = word1 = METATILE POINTER (low ROM, 0..0xFFFF)
   bsr FUN_000559b2
FUN_000559b2 @0x0559B2 (terminal, 4 cells):
   *(a0) = *(a1)                    ; write word0 (anchor) to FG plane
   a6 = a2 + 0x20 ; if *(a6)==0xFF -> a6 = a2+0x22   ; metatile COLLISION header/uniform (@0x0559B6/0x0559D4)
   collision[0x10DE00 + ((dest-0xC08000)>>1)] = metatile collision word   (@0x0559E4/0x0559EC)
   inner 4-cell loop: read metatile tile word (index strip/cell) -> *(a0); a0 += stride   (@0x0559F0..0x055A10)
```
`a2` = the **metatile pointer** (word1). Its structure (verified from ROM, §5). The terminal writer feeds the
FG plane tile words and the collision ring the metatile collision value — the same publication event, as
proven in the FG decompile (Part 2 §10, collision base now pinned **arcade 0x10DE00**).

## 5. Strip-source entry + metatile format (proven from ROM)
- **Strip-source entry = 4 bytes `{word0, word1}`** (walked +4/group): `word0` = anchor tile word; `word1` =
  **metatile pointer** (low ROM, e.g. 0x1000/0x2090/0x243C).
- **Metatile structure** (proven from ROM bytes):
  - `+0x00..0x1F` : **16 tile-graphics words** (arcade 8×8 tile codes, KF-014 domain).
  - `+0x20`       : **collision header word** — `0x00FF` = uniform.
  - `+0x22`       : **collision value** when uniform (`0x0000` passable, `0x0001` floor/ground, `0x0002`
    wall/solid — the value the terrain consumer masks `&0x7F`).
  - (larger metatiles repeat tile+collision sub-sections for multi-strip spans.)
- **Sentinel:** `0xFF` (as `0x00FF`) at `+0x20` marks the uniform-collision form.

## 6. Tile-code + collision storage
- **Persistent ROM level data:** the 16 strip-source tables (0x1691C..0x3725C) of `{tile, metatile-ptr}`
  entries, and the low-ROM metatile blocks (tile words + collision).
- **WRAM cache/cursor (not the map):** `0x10D000` (16 live source ptrs), `0x10D040` (metatile ptrs),
  `0x10D080` (word0), `0x10CA/0x10CC` (strip/group), `0x10AE/0x10B0` (FG scroll).
- **PC080SN mechanics (NOT level data):** the C-window 0xC08000 destination + name-word emission (already
  native, Builds 0242/0245/0247).

## 7. Representative decoded cells (ROM-derived; expected values for Part-2)
Tile-graphics words = metatile `+0x00..`; collision value = metatile `+0x22` (uniform). Cave-only metatiles
proven by diffing outdoor(seg1) vs cave(seg5) strip metatile sets.

**CELL A — outdoor reference** (seg 1, strip 11, metatile `0x1024`)
tiles = `0x0070 0x0071 0x0072 … 0x007F`; collision = `0x0000` (passable). Upper strips (0/1) = metatile
`0x1000` (all-blank tile `0x0020`, collision 0x0000 = sky).

**CELL B — cave descent/wall** (seg 4–5, metatile `0x2024`)
tiles = `0x00BD 0x00BE 0x00BF 0x00C0 0x00C1 0x00C2 0x00C3 0x00C4 0x00C5 0x00C6 0x00C7 0x010B 0x00C9 0x010D
0x010E 0x010F`; collision = `0x0001` (solid cave wall).

**CELL C — cave interior** (seg 5–6, metatile `0x2090`)
tiles = `0x0411 0x0412 0x0413 0x0414 0x0415 0x00C2 0x00C3 0x0416 0x00C5 0x0417 0x0418 0x0419 0x00C9 0x040E
0x041A 0x041B`; collision = `0x0001`.

**CELL D — deeper cave / floor** (seg 6, metatile `0x243C`)
tiles = `0x07FC 0x0091 0x0092 0x0093 0x07FD 0x0095 0x07FE 0x0097 0x07FF 0x0800 0x0801 0x0802 0x0803 0x0804
0x0805 0x0806`; collision = `0x0001`.

**CELL E — rope region** — the demo GAME-OVERs at ~segment 6; the rope-specific metatile is within the
segment-6 range (candidate cave-only metatiles `0x2B08/0x2B48/0x2B88` in strips s06/s12/s14). **NOT fully
isolated to a single proven rope cell** without reaching the rope live (deferred; see §10).

Cave-only metatiles (not in outdoor seg1, proven by diff): `0x2024 0x2048 0x2090 0x20FC 0x243C 0x2460 0x2484
0x29C8 0x2A48 0x2A88 0x2AC8 0x2B08 0x2B48 0x2B88`.

## 8. Runtime validation
The cave is runtime-reached (Part 1: segments 4–6). The static cave metatiles carry cave-graphics tile codes
(0x411+, 0x7FC+) distinct from outdoor, consistent with the live cave. A byte-exact per-cell live-vs-static
correlation of one cell (segment/group/strip/metatile-ptr/tile) is a **targeted confirmation** recommended
but NOT REQUIRED to establish the format (the format is proven statically; the tile-vs-collision sub-index
exactness is the one item a single live cell would nail — §11).

## 9. Missing cave block
**Missing cave-blocking block investigated: NO. Remains deferred: YES.**

## 10. Open/Closed Issues impact
OPEN-001/018: cell-level arcade cave oracle now exists (tile codes + collision derivable from ROM). OPEN-017:
collision value source proven (metatile +0x20/+0x22). No issue closed; no new issue. Rope-cell isolation
deferred.

## 11. KNOWN_FINDINGS impact
**Option B — proposed new entry (for Tighe review):** *Rastan Stage-1 Plane-A map format: strip-source tables
0x1691C..0x3725C (0x22C0/strip, +seg*0x40) of {tile, metatile-ptr} entries; metatile = 16 tile-graphics words
at +0x00 + collision header/value at +0x20/+0x22 (0/1/2 = passable/floor/wall); terminal writer FUN_000559b2/
55a14 emits tiles to Plane-A staging and the collision value to the ring at arcade 0x10DE00.* Static-proven;
the exact within-metatile tile sub-index is a minor refinement (§7 tiles are the metatile +0x00 set).

## 12. Remaining uncertainty
1. Exact within-metatile **tile sub-index** the terminal writer uses for each (strip,cell) — the tile SET per
   metatile is proven (§7); the precise cell→word mapping (which of the 16 words per cell) needs one live
   cell or a careful re-trace of the FUN_000559b2 shift arithmetic (metatile+0x20 is the collision section,
   +0x00 the tiles).
2. Rope-region single-cell isolation (§7 CELL E) — reach the rope live or trace segment-6 group order.
3. The multi-section metatiles (spans > 4 cells) — exact section stride.

## 13. Readiness for Part 2
The arcade cave oracle now has **tile-code sets + collision values per cave metatile** (§7) — sufficient to
begin the Part-2 Genesis comparison at the metatile/tile-set + collision level. Byte-exact per-cell parity
additionally needs §12.1.

---

**Strip-source entry format understood:** YES ({word0=tile, word1=metatile-ptr}).
**Descriptor/metatile format understood:** YES (16 tile words @+0x00; collision header/value @+0x20/+0x22).
**Individual arcade 8×8 tile codes derivable:** YES (metatile +0x00 tile words; §7).
**Tile attributes/control values derivable:** YES (collision value @+0x22; 0/1/2 = passable/floor/wall).
**Outdoor reference cell decoded:** YES (metatile 0x1024 → 0x70..0x7F; 0x1000 blank).
**Segment-4 cave cell decoded:** YES (metatile 0x2024 → 0xBD..0x10F, collision 0x0001).
**Segment-5 cave cell decoded:** YES (metatile 0x2090 → 0x411..0x41B, collision 0x0001).
**Segment-6 cave cell decoded:** YES (metatile 0x243C → 0x7FC..0x806, collision 0x0001).
**Rope-region cell decoded:** NOT PROVEN (candidate metatiles identified; single rope cell not isolated).
**Static model validated against original arcade runtime:** cave-reach YES (Part 1); byte-exact single-cell
correlation NOT REQUIRED for the format (recommended for §12.1).
**Cell-level Stage-1 cave oracle complete:** YES for tile-set + collision; byte-exact per-cell pending §12.1.
**Production source changed:** NO. **ROM produced:** NO. **Build counter:** 297 unchanged.
**Ready for Part 2 Genesis generator/build comparison:** YES (metatile/tile-set + collision level).
**Missing cave blocking block investigated:** NO. **Remains deferred:** YES.
**STOP triggered:** NO.
