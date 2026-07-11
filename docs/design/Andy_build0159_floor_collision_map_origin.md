# Andy — Build 0159: Floor/Collision Map Origin (Analysis Only, No Build)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `0581f55`, clean (only gitignored MAME trace churn). Accepted Build 0158
ROM `2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158. **No source edit, no
build, no spec/tool edit.** KNOWN_FINDINGS touched: **KF-039** (arcade WRAM base `0x0010C000` -> Genesis
`0x00FF0000`) and **KF-036** (raw work-RAM literal rebase class — same class as Build 0158). No CONFIRMED/STRONG
contradiction. OPEN issue: OPEN-017.

## 2. Address mapping method
`build/rastan-direct/address_map.json`: `relocation_delta = 0x000200`, `arcade_source = [0x0, 0x60000)`,
arcade_copy at Genesis `+0x200`. So arcade `0x53A2E` -> Genesis `0x53C2E`, arcade `0x53DA6` -> Genesis
`0x53FA6`, arcade `0x53E0C` -> Genesis `0x5400C` (all confirmed against `build/maincpu.disasm.txt` and
`build/genesis_postpatch.disasm.txt`; no guessed offsets). A5 work RAM: arcade `0x0010C000` -> Genesis
`0x00FF0000` (KF-039). Player fields (a5+off): X `+0x10BE`, Y `+0x10C0`, cmd `+0x137A`, mode `+0x10E8`,
contact `+0x10CE`; collision camera origin `+0x10AE` (X), `+0x10B0` (Y); staged BG scroll Y `0x00FF409A`.

## 3. Trace method
Static disasm of the collision classifier (`0x53E0C`-region) and its lookup (`0x53C2E`), plus a runtime
write-tap on the mode=0x0008 store `0xFF10E8` capturing `A0`, `*(A0)`, the KF-039-rebased WRAM equivalent, and
player/camera state; plus a frame-560 snapshot of the three candidate map regions. Same coin(F120-132)+start
(F175-187) route as prior Build 0159 passes. Evidence: `states/traces/build_0159_floor_collision/`
(`gen_collision.lua`, `gen_collision.txt`).

## 4. Arcade collision timeline (reference)
Arcade is the reference: its literal `0x0010DE00` is **work RAM**, holding the real collision map produced by
the same routines. Prior Build 0159 life-loss pass established the arcade reaches the type-8 dispatch only
~275 frames later than Genesis (2/4/0 at arcade F=895 vs Genesis F=846). The a0 arithmetic is identical to
Genesis; the difference is purely that `0x0010DE00` is populated WRAM on the arcade.

## 5. Genesis collision timeline (Build 0158)
At the mode=0x0008 write (F=698, PC=0x054012 = prefetch of the `move.w #8,%a5@(0x10E8)` at 0x5400C):
`A0 = 0x0010F20A`, `*(A0) = 0x1888`, `*(A0)&0x7F = 8` -> dispatch fires. Player `X=0x0020, Y=0x0070`
(correct), `cmd=0x00FF` (Build 0158 fix intact), camX(a5@0x10AE)=0x0000, camY(a5@0x10B0)=0x014B,
scrY_bg=0x014B. `A0 = base 0x0010DE00 + index(camY, Yprobe)`; because camY=0x014B shifts the row term, the
offset is ~0x140A -> `A0=0x0010F20A`, a **ROM address** (0x10xxxx is outside the 0x60000 arcade-copy, so it
reads cartridge ROM, not WRAM).

## 6. a0 computation path (fully traced, `0x53C2E`)
```
53c2e: clrl d0
53c30: movew a5@(0x10AE),d0      ; camera origin X
53c34-3a: d0 = (-(camX) mod 512)
53c3e: addw d1,d0                ; + Xprobe  (d1 = playerX +/- a5@0x112E +/- 3)
53c40: lsrw #1,d0 ; 53c42: addiw #8 ; 53c46: andiw #0xFC   -> column part
53c4a: movew a5@(0x10B0),d1      ; camera origin Y
53c4e-54: d1 = (-(camY) mod 512)
53c58: addw d2,d1                ; + Yprobe  (d2 = playerY + a5@0x1130 + d6)
53c5a: lslw #5,d1 ; 53c5c: andiw #0x3F00   -> row part
53c60: addw d1,d0 ; 53c62: lsrl #1,d0       -> index
53c64: moveal #0x0010DE00,a0    ; <== COLLISION-MAP BASE = raw arcade-WRAM literal (UN-REBASED)
53c6a: addal d0,a0              ; a0 = 0x0010DE00 + index
53c6c: rts
```
The classifier (`0x53E14`..`0x53FB8`, two-sided left/right probe) re-reads `*(a0)&0x7F` and dispatches:
type 1/3/4/6/7 set contact bits; **type 8 -> braw 0x54000 -> `move.w #8,%a5@(0x10E8)`** (gameplay-end);
type 126 -> 0x54014.

## 7. Collision-map base pointer proof
Genesis ROM bytes at `0x53C64` = `20 7C 00 10 DE 00` (`moveal #0x0010DE00,a0`) — **byte-identical to the
arcade** at `0x53A64`; the postpatch relocation did NOT rewrite it (0x0010DE00 is not in the code region
[0,0x60000), so it is copied verbatim; and there is no WRAM-literal rebase for it). The same raw literal
`0x0010DE00` appears at **~9 sites**, both reads and writes:
- reader:  `0x53C64` (`moveal #0x0010DE00,a0`) — the dispatch source.
- producers: `0x55BE4`, `0x55C5A`, `0x55C7A` (`addil #0x0010DE00,d7` -> `moveal d7,%fp; move.w %d0,%fp@` =
  writes cells), `0x52A82`, `0x5A4CE` (`addil`), `0x5A536` (`subil`).
- compares: `0x414E8`, `0x45F52` (`cmpal #0x0010DE00,%a0`).
Spec/postpatch review: `specs/rastan_direct_remap.json` + `tools/translation/postpatch_startup_rom.py` contain
**no** collision-map rebase — the only raw-WRAM-literal rebases are Build 0158's single site `0x05102E`
(0x10C016->0xFF0016) and the item-page hook `0x055E2E`. So `0x0010DE00` is entirely un-rebased.

## 8. Player-space X/Y comparison
Genesis player X=0x0020, Y=0x0070 at the trigger — **identical to the faithful arcade landing** (prior
drop/landing pass). The player is NOT dropped to a wrong position; the divergence is entirely in the collision
MAP the position is tested against.

## 9. World/camera-space comparison
Collision camera origin: camX(a5@0x10AE)=0x0000, **camY(a5@0x10B0)=0x014B** — equal to the extra Genesis BG
vertical scroll (`0x00FF409A=0x014B`). camY feeds the row term of the index, so the extra vertical scroll does
shift `A0`. But this is secondary: the base pointer itself points at ROM, so the map is garbage at any camY.

## 10. Collision-cell/index comparison
- **Reader's actual source (Genesis):** `ROM@0x0010DE00` (frame-560 snapshot) = 256 nonzero garbage words
  (graphics data: 5569 A8A8 5469 …), of which **3 words have `&0x7F==8`** plus many other spurious types
  (0x66/0x55/0x11/…). The reader lands on one (`A0=0x0010F20A`, word 0x1888, type 8) -> spurious gameplay-end.
- **Rebased WRAM target (KF-039):** `WRAM@0x00FF1E00` = **all zero** (0 nonzero over 0x200). The Genesis
  collision map is **never produced** — because the producers (`0x55BE4` etc.) compute
  `d7 = index + 0x0010DE00` and `move.w %d0,(d7)` write to `0x0010DExx`, which on Genesis is **ROM (read-only)
  -> the write is dropped.** (`WRAM@0x00FFDE00` is also empty, ruling out a naive FF0000+DE00 placement.)

## 11. JSON/spec/map-origin review
No JSON scene-origin, Stage-1 start, or map-dimension data is involved. This is not a scene/map-generation
issue — it is a memory-map literal defect in the copied arcade code: the collision buffer lives at arcade WRAM
`0x0010DE00`, and the ROM-wide copy preserves that literal for both producers and reader without the KF-039
WRAM rebase. `precompute_pc080sn_tile_lut.py`, scene manifests, and `address_map.json` are not implicated.

## 12. Relationship to BG vertical scroll 0x00FF409A
`staged_scroll_y_bg = 0x014B = camY(a5@0x10B0)` at the trigger. The extra vertical scroll shifts the collision
index (row term) and so changes WHICH garbage word is read, but is not the root: the base pointer is ROM
regardless of camY, and the WRAM map is empty. The vertical-scroll finding (prior pass) and this collision-base
finding are coupled through `a5@0x10B0` but the collision-base literal is the dominant, independent defect.

## 13. Relationship to mode=0x0008 / handler 0x05400C
Direct: the type-8 cell at `*(A0)` is the sole input that routes to `0x54000` -> `0x5400C` (`mode<-0x0008`),
which the stage controller (`0x051B98`) converts to `0xFF0002<-4` (gameplay end). The arcade_copy handler is
faithful; do NOT patch it. The fault is upstream — the collision buffer it consumes.

## 14. User hypothesis answer
**"Is the player being dropped from a different starting point?" — NO (position), YES (collision origin).**
- **visible/player-space X/Y:** correct (X=0x0020, Y=0x0070; identical to arcade). Not a drop-position error.
- **world/camera-space X/Y:** camY(a5@0x10B0)=0x014B (= extra BG vertical scroll); shifts the index but is
  secondary.
- **collision-map cell/index:** the reader looks the player up against a collision MAP at the WRONG memory —
  raw arcade-WRAM literal `0x0010DE00`, which on Genesis is cartridge ROM garbage (word 0x1888, type 8), while
  the correct WRAM location `0x00FF1E00` is empty (never produced, producers write to ROM). So the player is
  effectively "looked up against the wrong collision location" — the user's hypothesis is correct in mechanism.
- **JSON/spec/map-origin contribution:** none; it is a KF-039 raw-WRAM-literal defect in copied code.

## 15. State-causality answers
1. **Base pointer:** `0x0010DE00` (arcade WRAM literal; on Genesis = ROM). 2. **Index inputs:** camera origin
`a5@0x10AE`/`a5@0x10B0`, player X `a5@0x10BE` ± probe `a5@0x112E` ±3, player Y `a5@0x10C0` + `a5@0x1130` + d6.
3. **Arithmetic:** `a0 = 0x0010DE00 + ((col + row)/2)` (see §6). 4. **Different a0 than arcade?** The formula
and literal are identical; the effective memory differs — `0x0010DE00` is populated WRAM on arcade, ROM garbage
on Genesis. 5. **Cause of the difference:** the collision-map base literal `0x0010DE00` is **not rebased** to
Genesis `0x00FF1E00` (KF-039) at any of its ~9 producer/reader sites; producers write to ROM (dropped) so the
WRAM map is empty, and the reader reads ROM garbage. NOT player start/drop, NOT scene/map origin, NOT stride,
NOT sign; camera-Y is a secondary index shift. 6. **Numerically tied to vertical scroll?** camY=0x014B (=scroll)
shifts the index but the defect is present at any camY. 7. **Same cell as arcade?** No — arcade reads real WRAM
map; Genesis reads ROM garbage / an empty WRAM. 8. **Type 8 normal-later vs garbage?** **Garbage** — Genesis
reads uninitialized ROM as the collision map (the WRAM map is empty); it is not a legitimate later hazard tile.

## 16. Readiness classification: **A** (source cause proven and bounded) — with implementation caveats
The a0 computation and source cause are **proven and bounded**: the collision buffer at arcade WRAM
`0x0010DE00` is not KF-039-rebased to Genesis `0x00FF1E00`, so producers write to ROM (dropped, WRAM empty) and
the reader reads ROM garbage that intermittently yields type-8 -> early `mode=0x0008` -> early gameplay-end ->
the "burns lives / continue" cycle. Bounded to the enumerated ~9 literal sites in §7. **Caveats that keep this
short of a one-line ready patch:** (a) the fix is a **coordinated multi-site buffer rebase** (all producers +
reader + compares must move together), i.e. exactly the "raw-WRAM rebase" class Build 0158 deliberately scoped
down from — a single-site reader-only rebase would point the reader at the empty `0x00FF1E00` (all type-0),
removing collision entirely rather than fixing it; (b) the two `cmpal` sites (`0x414E8`/`0x45F52`) must be
confirmed to belong to the same buffer before inclusion; (c) camY(a5@0x10B0)=0x014B (extra vertical scroll)
independently shifts the index and may need its own resolution. **Do not implement in this task.**

## 17. Exact next implementation boundary if ready
A dedicated future build: KF-039-rebase the collision-map buffer literal `0x0010DE00 -> 0x00FF1E00` across all
verified producer/reader/compare sites (§7) as a coordinated set (byte-neutral operand rebases through the spec
`opcode_replace` pipeline), then verify runtime `0x00FF1E00` populates with a real map and the reader reads
type-appropriate cells (no early type-8). Prerequisite analysis: confirm the ~9 sites are one buffer + no
sibling collision buffers share the defect + settle camY(a5@0x10B0). Not this task.

## 18. Open/Closed Issues Impact
OPEN-017 advanced: the "burns lives / reaches continue" cycle is root-caused to the **collision-map base
literal `0x0010DE00` not being KF-039-rebased** — Genesis producers write the map to ROM (dropped, WRAM empty)
and the reader reads ROM garbage yielding spurious type-8 -> early `mode=0x0008`. Bounded to ~9 literal sites;
fix is a coordinated multi-site buffer rebase (deferred to a dedicated build). No new issue, none closed.

## 19. KNOWN_FINDINGS impact
Option A — no new finding indexed; this is a new **instance** of the existing KF-036/KF-039 raw work-RAM literal
rebase class (documented here). If pursued as a build, it warrants promoting KF-039 with the collision buffer
`0x0010DE00 -> 0x00FF1E00` (multi-site) as a named instance.

## 20. Architecture compliance
CONFIRMED. Analysis only — no source, build, or spec/tool edits; runtime evidence via MAME write-tap + static
disasm; arcade program remains the reference. No rendering/scroll/sprite/collision-source/continue/game-over/
D00298/Exodus/audio changes. The collision handler `0x5400C` is faithful and is NOT to be patched.
