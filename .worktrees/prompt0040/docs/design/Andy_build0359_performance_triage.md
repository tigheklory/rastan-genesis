# Andy — Post-0357 Performance Triage: The Next Speed Target (Build 0359)

**Analysis only. No production change, no ROM.** Baseline Build 0357 (counter 358, next 0359).
Evidence: `Cody_build0357_sprite_reverse_index_performance.md`, the joint 0356 timing investigation,
and `apps/rastan-direct/src/pc090oj_hooks.s` (`.Lnq_emit_lane`/`.Lnq_emit_entry`, lines 1709–1917).

## 1. Remaining native-sprite cost decomposition (as far as evidence allows)

0357 removed the per-piece 49-slot **hit** search. What remains, per emitted entry
(`.Lnq_emit_entry`, straight-line, no loop):

| Component | Where | Cost character |
|---|---|---|
| code extract + blank-bitset test + HUD tag | 1728–1750 | small fixed/entry |
| Y/X coarse wrap | 1752–1761 | small/entry |
| flip handling (`ctrl_shadow` read + X/Y flip terms) | 1762–1774 | small/entry; **`ctrl_shadow` is frame-invariant but re-read every entry** |
| **opaque-bbox viewport clip** (4 bbox byte reads + per-flip `neg/addi/exg` orient + 4 viewport compares) | **1776–1816** | **largest straight-line block/entry** |
| reverse-index **hit** lookup (1 directory + 1 leaf byte, branch) | 1818–1840 | **now cheap O(1)** |
| SAT construction / lane store | `.Lnq_hit` | moderate/entry |
| miss/victim path (`.Lnq_vloop` **linear ≤49** + `.Lnq_reverse_replace`) | 1841–1917 | **only on miss**; still contains a 49-iteration scan |
| fixed finalizer setup + 6 `.Lnq_emit_lane` calls | 1596–1611 | fixed/frame |
| stage dispatch (arcade record → lane queues) | separate | ~44/75/80 lines; **unchanged by 0357** |

**The dominant term is now per-emitted-entry hit-path work.** Cody's fitted finalizer slope is
**3.116 physical lines per emitted entry** (correlation 0.909). Finalizer = ~fixed + entries×3.116;
the **back/enemy lane** carries the most entries, so it scales worst (stationary 41.6, horizontal 88,
worst frame 232.5). The search is gone — the residual 3.116 lines/entry is transform + **bbox clip** +
SAT, and by inspection the **bbox viewport clip (1776–1816) is the single largest straight-line block**
in that path.

## 2. Is the 4.27% miss path the priority? — **No.**
1,441 misses over 33,709 lookups in 1,800 frames ≈ **~0.8 misses/frame** (worklist median 0, max 12,
73 queue-full drops). Each miss still runs the untouched `.Lnq_vloop` linear ≤49 scan + replace, so it
is a **rare spike** contributor to worst-frame finalizers, **not** a meaningful aggregate median cost.
Leave it for now; it becomes worth an O(1) free-slot structure only after the per-entry hit path is
addressed.

## 3. Why heavy scenes still explode
Finalizer and back/enemy-lane time scale **linearly with emitted-entry count** (slope 3.116,
r=0.909). What scales: the whole per-entry hit path (bbox clip + transform + SAT), applied to every
piece, concentrated in the back/enemy lane. What does **not** scale: fixed finalizer setup, publisher
(~6 lines), and the now-O(1) hit lookup. Worst frame 796 (38 entries, back/enemy 232.5, finalizer
305.6) is the per-entry cost × a large back/enemy population, not a search or miss artifact.

## 4. Stage dispatch as a candidate
~44 global / 75 horizontal / 80 sprite-heavy lines, essentially untouched by 0357. It is arcade
record→lane extraction. Most is **necessary semantic extraction**, but its heavy-scene growth
(44→80) suggests per-record recomputation that offline-generated data could hoist. **Second-tier
candidate** — but choosing it confidently needs a short decomposition it does not yet have.

## 5. A-13 revisited
Cody left A-13 **PARTIALLY RESOLVED**: the search half is isolated, but the residual 3.116
lines/entry is **not** split into {transform, bbox-clip, SAT, lane}. That specific split **is**
decision-relevant here (it decides how much the #1 target can recover), so the one worthwhile
measurement is a **bracket of the bbox-clip block (1776–1816) vs the rest of the per-entry path** over
the same gameplay chains — not a full completeness sweep. Recommend Cody bracket it as step 0 of 0359.

## 6. Copied-core 0x05100A
Not now. Native sprite work still offers the clearest recovery, and touching copied arcade logic needs
semantic proof this task did not pursue.

## 7. Top-2 candidates, ranked

| Rank | Change | Expected median saving | Heavy-scene saving | Impl risk | Semantic risk | Helps black bars |
|---|---|---|---|---|---|---|
| **1** | **Cut per-entry hit cost:** move opaque-bbox **flip orientation** to an offline pre-oriented per-code table (runtime does add+compare only — drop the per-entry `neg/addi/exg`/byte-shuffle), and **hoist the frame-invariant `ctrl_shadow` flip read** out of the per-entry loop | **~11–20 lines** (0.4–0.7 ln/entry × ~28 median; bounded, pending the §5 bracket) | **~19–34 lines** (×~48 entries) | low–med (bbox table already exists as `pc090oj_opaque_bbox`; pre-orient offline) | low (identical clip result) | **yes — finalizer/back-enemy is the overrun bulk** |
| 2 | **Stage dispatch:** replace repeated per-record arcade recomputation with generated lane data | ~10–20 lines global; more horizontal/heavy | larger in horizontal (75) | med | med (must preserve arcade extraction) | yes (heavy/horizontal frames) |

Estimates are **bounded, not exact** — the per-component split (A-13 §5) is not yet measured; the
slope (3.116 ln/entry) and lane medians are the firm inputs.

## Deliverables

1. **#1 measured bottleneck:** the **per-emitted-entry finalizer hit path** (3.116 lines/entry,
   r=0.909), concentrated in the **back/enemy lane** — with the **opaque-bbox viewport clip** the
   largest straight-line block in it. Not the search (gone), not the miss path (rare).
2. **Build 0359 change:** streamline the per-entry hit path — **offline pre-oriented per-code bbox
   table** (eliminate runtime flip `neg/addi/exg`) + **hoist the frame-invariant `ctrl_shadow` read**
   out of `.Lnq_emit_entry`. Precede it with the short bbox-clip-vs-rest bracket (A-13 §5).
3. **Expected savings:** ~11–20 median lines (more in heavy/horizontal scenes), bounded pending the
   bracket. Target is ~24+ median → this likely closes most of it and clearly shrinks the worst-frame
   overrun; margin may need #2.
4. **Leave alone:** the miss/victim path, copied-core 0x05100A, Plane A capacity / 49→58+ expansion,
   full DPLC / animation-frame extraction, Palette Composer, larger-sprite actor recomposition (future
   only), D00462, VBlank lifecycle.
5. **Second optimization after 0359 likely required: YES.** 286→~266–275 median after #1 is marginal
   against 262 and heavy-scene/P95 chains still exceed a frame; **stage dispatch (#2)** is the probable
   follow-on for comfortable margin.
