# Build 0246 Initial Plane A Fill Audit (analysis; no source/build)

**Type:** runtime audit. **Production / build / counter:** unchanged (246).
**Authority:** original arcade opcodes + `docs/arcade_reference/pc080sn/` + Build 0246 source +
`Andy_build0245_native_plane_a_review.md`. **Evidence:** `states/traces/build0246_initial_fill_*/`
(`fill.txt`, `scroll.txt`, `trans.txt`). Palette is now correct (0246); coordinate ring +
full VSRAM applied (`physical_row = logical_row & 31`, VSRAM `& 0x01FF`). Scope: Plane A initial
seed only.

---

## 1. Arcade initialization contract (Phase 1)

- Scene-fill `0x0503DC/0x050434`: **64 publications** (selector-0 columns), each writing all 64
  logical rows of one C-window column; ring counters 10CA(0-3)/10CC(0-15) cycle once
  (0x0558A2/0x0558C6 progression); descriptor rebuild `0x055904`.
- The arcade C-window is **64 rows** (512px). The fill seeds **all 64 logical rows** of every
  column — **scroll-independent**. Runtime: the fill runs with arcade Y-scroll `a5@0x10B0 = 0`.
- The camera then **pans** to the gameplay position (`a5@0x10B0`: 0 → 0x1FF → **0x149**), a smooth
  vertical settle. **No second fill and no clear follow** — the arcade relies on the seeded
  64-row C-window and just scrolls the view.
- Highest safe native seed boundary: the same selector-0 producer boundary already used — the
  issue is **not** the boundary; it is the 64→32 vertical fold (§4).

## 2. Build 0246 boot→first-control trace (Phase 2)

- **Initial fill:** ~64 selector-0 publications across frames **F182–197**, `arc scroll_y = 0`,
  `staged_scroll_y_fg = 0` → **`visible_top = 1`**. All 32 physical rows seeded (cumRowMask =
  0xFFFFFFFF, ~512 cols/row). No selector-1/2 in the fill.
- **Camera pan F397–480:** `a5@0x10B0` ramps 0x1FF → 0x149; **`fg_writes = 0` the entire pan** —
  no selector-0/1/2 publication (the native helpers are never dispatched).
- **First control ≈ F700+:** `staged_scroll_y_fg = 0x149` → **`visible_top = 23`**;
  `fg_native_gameplay_owner = 1`. No FG writes between the fill and gameplay streaming.
- **Live Plane A writers after the fill:** none until ordinary horizontal selector-0 streaming.
  Legacy paths (`genesistan_stage_fg_src_column` 0x070916, `..._fg_fill/_tall`,
  `genesistan_hook_cwindow_clear` 0x071D44) did **not** re-write staged_fg_buffer after the native
  fill (owner=1 gates them; write tap shows no post-fill activity). **No clear, no overwrite.**

## 3. Bad column vs later correct edge load (Phase 3)

Take any physical row `1..22` of any column:

| | Initial fill (F~190) | Later gameplay streaming |
|---|---|---|
| dispatch | selector-0 (fill loop) | selector-0 (horizontal edge) |
| `visible_top` | **1** (scroll_y=0) | **23** (scroll_y=0x149) |
| residency accepts logical | **[1..32]** | [23..54] |
| physical row `r` (1..22) holds logical | **`r`** (from window [1..32]) | **`r+32`** (33..54) |
| final Plane A word | tile of logical `r` | tile of logical `r+32` |
| staged offset | `r*128 + col*2` | same physical cell |

**First differing input:** the residency gate's `visible_top` (1 vs 23) — the **only** differing
input; the tile/descriptor/collision/placement math is otherwise identical. **First exact
divergence:** the fill accepts logical window `[1..32]` and places `logical r → physical r`, while
gameplay needs logical `[23..54]`; physical rows `1..22` therefore hold logical `1..22` instead of
`33..54`. Cause among the enumerated options: **"camera/VSRAM changed after fill without reseeding
required cells"** — specifically, the resident window's `visible_top` moved from 1 to 23 during a
vertical pan in which the arcade published nothing.

## 4. Coverage proof (Phase 4)

At first control: **all 32 physical rows and all 64 columns are seeded** (not blank). But the seed
is for `visible_top = 1` (logical [1..32]); gameplay's `visible_top = 23` needs logical [23..54].
Overlap = logical [23..32] → physical [23..31]+[0] (**correct**); the other **22 rows** (logical
[33..54] → physical [1..22]) were **never published** and hold the fill's logical [1..22]
(**wrong**). So the **64-publication fill is NOT sufficient** for the Genesis 64×**32** resident
ring when the gameplay camera differs from the fill camera: the arcade's 64-row C-window absorbs
the pan; the Genesis 32-row ring cannot, and nothing re-publishes the newly-resident rows.

## 5. Root cause (proven)

The initial scene-fill seeds the Genesis 32-row ring at the **fill-time camera** (`visible_top=1`,
scroll_y=0). The arcade then **pans the camera vertically** ~23 rows to the gameplay position
(scroll_y=0x149, `visible_top=23`) **without publishing any tilemap1 rows** — correct for its
full 64-row C-window, but the Genesis 32-row ring is left holding the fill's rows. The 22 logical
rows revealed by the pan (33..54) were never published. This is the **vertical counterpart** of
the (now-fixed) horizontal case: horizontally the ring is 64 = full match so streaming keeps up;
vertically the ring is 32 vs the arcade's 64, and the arcade's no-publish-during-pan behavior
starves the smaller ring. Not a producer/palette/preload/clear/overwrite bug — it is a
**coordinate/initialization** bug: the 64→32 vertical fold has no publisher to track vertical
camera motion that the arcade doesn't publish.

## 6. Smallest safe correction (Phase 4 conclusion)

The divergence is a **missing native vertical-crossing publisher** for the 32-row ring. The
arcade's horizontal streaming already keeps the X ring (64=64) correct; the Y ring (32 vs 64)
needs the Genesis to publish **entering rows on its own vertical-tile crossings** — the Sonic
`DrawBlocks_TB` dual-ring vertical counterpart — even though the arcade doesn't (its C-window is
full). Two scoped options, smallest first:

1. **Minimal (fixes the reported symptom):** when the resident window's `visible_top` changes
   without a covering publication (e.g. detected at gameplay entry / camera settle), **re-publish
   the 32 resident rows** at the current `visible_top` (a one-time resident-ring reseed using the
   existing selector-0/1/2 producer over the current descriptor/source state). This corrects the
   initial pan discrepancy directly.
2. **General (also fixes vertical falls):** a native vertical-crossing trigger that publishes the
   entering row(s) into the ring whenever `visible_top` advances — the true dual-ring Y publisher.

Both consume the existing native producers; neither adds a shadow/mirror/projection/compat layer.
Recommend option 1 as the smallest safe Cody step (isolated, testable at the reported symptom),
with option 2 as the follow-up for vertical gameplay (falls). This is **"needs a native
producer/trigger,"** not merely fixing an existing helper's math — the existing helpers are
correct; what's missing is a Genesis-side vertical-crossing publication that the arcade never
performs.

## 7. Distinctions

- **Proven:** the initial fill seeds at `visible_top=1` while gameplay needs `visible_top=23`; the
  arcade publishes nothing during the vertical settle pan (`fg_writes=0`); 22 physical rows hold
  the wrong logical rows; horizontal streaming repairs them.
- **Not the cause:** producer math, palette (correct), tile preload/residency, a clear, a legacy
  overwrite, or a late dirty commit — all excluded by the trace.
- **Expected consequence of incomplete work:** vertical falls will show the same starvation until
  the general vertical publisher (option 2) lands (this is the review's Y-axis follow-up).
- **Inherited/out of scope:** Plane B (unrelated — still tall projection), selector-1/2 fall
  behavior, first-rope, collision, sprites, palette routing.

## STOP

Not triggered on the root cause. The bad initial column is matched to its later correct
publication (§3); writer ordering is proven (fill at F~190 → no writes during the pan → horizontal
streaming repairs, no overwrite/clear); a single path explains the final word. **Plane B not
implicated.** (See §9 for a *scoped* STOP on the initial-pan source-derivation.)

---

# Final Native Vertical-Publisher Boundary

Evidence added this pass: `states/traces/build0245_plane_a_review_20260730_150627/`
(`pan.txt`, `scroll.txt`, `trans.txt`) + arcade disassembly (`linear_disassembly.tsv`).

## 8. Arcade vertical camera-Y producer (mapped)

**Function:** the map-stream vertical scroll handler. Two symmetric arms, each: accumulate an 8px
tile-boundary counter, on a crossing compute the entering-row C08000 cursor and dispatch, then
advance the Y-scroll accumulator `a5@0x10B0` (4272). Relocation +0x200 (Genesis PC = arcade+0x200).

| item | Down (into map) | Up (out of map) |
|---|---|---|
| arm entry (arcade PC) | `0x0556A6` | `0x05572E` |
| direction gate | `cmpiw #1,a5@0x10A8` (sel==1) | `cmpiw #2,a5@0x10A8` (sel==2) |
| not-active → latch+return | `bset #5,a5@0x10D0` → rts | `bset #4,a5@0x10D0` → rts |
| **8px crossing state** | `a5@0x10B4 += a5@0x10DA; btst #3` (`0x0556C2`) | `a5@0x10B6 += a5@0x10DA; btst #3` (`0x055754`) |
| entering-row cursor | `a5@0x10A4 = 0xC08000 + 0x3F00 − (10CC·1024+10CA·256)` (`0x0556D8‑F8`) | `a5@0x10A4 = 0xC08000 + (10CC·1024+10CA·256)` (`0x05576A‑84`) |
| **publish dispatch (arcade PC)** | `0x0556FC bsr 0x055948` | `0x055788 bsr 0x055948` |
| **Y-scroll update** | `a5@0x10B0 += a5@0x10DA & 511` (`0x05570C‑18`) | `a5@0x10B0 −= a5@0x10DA & 511` (`0x055798‑A4`) |
| publish **gate** counter | `a5@0x10BA` — publish only when `≥256` (`0x0556A0 blt 0x55704`) | `a5@0x10BA` — publish only when `<8` (`0x05572E cmp #8 bge 0x55790`) |
| no-publish scroll path | `0x055704` (advance 10BA, scroll 10B0) | `0x055790` (retard 10BA, scroll 10B0) |

- **Direction:** selector `a5@0x10A8` (1=down, 2=up); pending-dir latch `a5@0x10D0`.
- **Entering-row identity:** the cursor is a pure function of the ring counters `10CC/10CA`
  (`10CC·4+10CA` = the proven selector-0 logical **column** index), NOT scroll. The **entering
  logical row → source-tile** mapping for selector-1/2 is **NOT yet proven** — the selector-0
  proof (`Andy_plane_a_selector0_logical_coordinate_proof.md`) resolved **columns only**; the
  semantic-cut contract §8 #1 still lists selector-1/2 as unproven.
- **Descriptor/tile source:** the dispatch `0x055948 → 0x558A2 → 0x55904` **rebuilds** the
  descriptor tables (`0x10D040`/`0x10D080`) for the entering strip. So on a *real vertical
  dispatch* the entering row's tiles are present in the current tables; without a dispatch they
  are not.

## 9. Camera-init table and the two-case split

Scene-init calls a **camera-init table @0x0508D0** (seed routine `0x0504FA`, caller `0x05020A`,
**before** the fill `0x0503DC`). 12 bytes/scene: `{ [0]=X(10AE), [1]=Y(10B0), [2]=10B8,
[3]=10BA, [4]=10BE, [5]=10C0 }`. Scene 0 = `{0x78, 0x80, 0x160, 0x00, 0xA0, 0x100}`. **But
gameplay `10B0 = 0x149 ≠ 0x80`** — the camera pans/settles *after* the seed, so the gameplay Y
(hence gameplay `visible_top=23`) is **not a simple pre-fill constant**. This closes the
"seed the fill at the gameplay window" shortcut.

**Two distinct cases, proven different in trace (`pan.txt`):**

- **(A) Ordinary vertical gameplay — falls / upward / reversal.** Driven by §8: selector 1/2,
  10BA past its threshold → `bsr 0x055948` → descriptors rebuilt → **the existing native
  selector-1/2 helper publishes the entering row** using arcade-supplied row descriptors.
- **(B) Initial settling pan.** Trace: `selector=0`, `10CA=10CC=0` (**ring static**),
  `cursorWr=0` (**no dispatch/publish**), `10B0` ramps `0x1FF→0x149` via a *scripted* selector-0
  camera move (not the ±`10DA` map-stream arm). The descriptor tables stay **column-oriented from
  the fill**; no row-descriptor/source state ever exists for the pan's entering rows.

## 10. Can ONE native trigger cover both? — proven NO

A general vertical entering-row publisher fired on the Genesis's own 8px crossings can cover **(A)**
because the arcade rebuilds row descriptors on those dispatches. It **cannot** cover **(B)**: during
the pan the arcade never dispatches, the ring is static, and the descriptor/source tables are
column-oriented — so a helper "using current descriptor/source tables" has **no entering-row
source** to read. Obtaining it would require (i) reading the C08000 chip window (the fill *did*
populate all 64 rows there — but consuming C08000 is exactly the PC080SN geometry the policy
forbids), or (ii) reconstructing the arcade's per-row source addressing independently (a §8-#1/#3
unproven reconstruction). **Per the resume task's own condition ("unless you prove the same
trigger cannot safely cover both"), this is that proof.**

## 11. Proposed native helper contract (case A — recommended path)

`genesistan_plane_a_publish_entering_row(entering_logical_row)`:
writes final Genesis Plane A words directly to `staged_fg_buffer`; `physical_row = logical_row & 31`;
all 64 logical columns; marks the final physical row dirty; existing corrected palette route;
`movem` save/restore of every non-owned register (0240 lesson); bounded to one row; no
`staged_fg_tall_buffer`, no C-window/C08000 authority. **Reuse of the existing
`genesistan_hook_tilemap_plane_a_selector12_native` is viable** — it already consumes the
row-oriented descriptor tables the dispatch supplies; the refactor is (a) a clean
`entering_logical_row` semantic entry instead of forcing selector-1/2 chip state, and (b) applying
the same ring placement/residency as selector-0. **Collision:** do **not** duplicate — the arcade
collision producer already writes `0x10DE00 + (row·64+col)·2` for all 64 logical rows during its
own producer pass; the visual row publisher should write Plane A words only.

## 12. Initial-pan disposition (case B)

The general trigger cannot supply case-B data (§10). A **one-time resident-ring reseed at settle**
is a legitimate *diagnostic/fallback* but is **not** clean either: at settle the descriptors
describe a single strip, so a faithful reseed must progress all 64 columns — which is exactly what
the observed horizontal streaming already does column-by-column. The correct final fix for case B
requires first **proving the selector-1/2 (vertical-row) logical-source mapping** — the vertical
analog of the selector-0 column proof — so the Genesis Y-ring can read an entering *row's* tiles
from semantic map state (`0x10D000` bases + logical row/col) **without** the arcade's
per-publication rebuild or the C08000 window. Until that proof exists, no byte-neutral pan
publisher can be selected.

## 13. Not a PC080SN compatibility layer

The case-A publisher writes **final Genesis Plane A name words** to `staged_fg_buffer` from the
retained semantic descriptor/source tables via the proven attribute conversion, placed by the
native `logical_row & 31` ring, committed by the existing arcade-owned VBlank path to native
VSRAM/HSCROLL. It introduces no software PC080SN, no C-window mirror, no 64×64 map, no full-window
projector, no Genesis-owned renderer/camera loop. It is the Genesis-native Y-ring counterpart of
the already-working X-ring horizontal streaming — required because the physical Y ring is 32 while
the arcade's C-window is 64.

## 14. Scoped STOP (initial-pan publisher only)

**STOP on selecting the initial-pan (case B) native publisher boundary.** Reason (a listed
condition): the entering logical **row's source** cannot be derived during the pan without
reconstructing PC080SN source addressing or reading the C08000 window — selector-1/2 vertical
logical-source is unproven (§8 #1). This is **not** a STOP "because the arcade performs no
publication during the pan" (that absence is precisely why the Genesis Y-ring trigger is needed);
it is a STOP because the *source* for the entering row is not yet exposed semantically. Case A
(falls/up/reversal) is **not** stopped — its boundary is proven (§8, §11).

## 15. Recommended next Cody task

**Prove selector-1/2 vertical logical coordinates + source mapping at runtime** (the vertical
analog of `Andy_plane_a_selector0_logical_coordinate_proof.md`): tap the arcade selector-1/2
producer during a fall, derive `entering_logical_row` and each cell's source tile from ring/scroll
+ descriptor state, and match against the C08000/collision oracle across down, up, and selector-2
reversal. That proof unblocks the case-A native publisher (§11) **and** is the prerequisite for any
case-B pan solution (§12). Do **not** implement the vertical publisher before that mapping is
proven — the same unproven-coordinate gate that held the selector-0 work applies here.
