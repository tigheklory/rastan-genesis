# Andy/Fable — N2 Native PC080SN Plane Pipeline (0224/0225 rejected, **Build 0226 = N2 candidate**)

**Date:** 2026-07-20 · **Evidence:** `states/traces/n2_native_pc080sn_plane_pipeline_20260720_202430/` · **JSON hashes:** address_map `2ddc7ad2…`, manifest `859f38fb…`, spec `318f3469…` (json_hashes.txt; no fixed offsets)

## User acceptance recorded
0223 = successful N1 baseline (stable sprites, speed retained). Remaining: title/attract black bar + rolling gameplay bar + direct captures showing large partial-frame loss — all pre-existing plane-path defects, now the N2 target.

## Root cause of the black bars (proven from code + A/B capture)
The old pipeline, per vertical 8px crossing: **full 2×4KB tall→staged reprojection, all 32 rows marked dirty, then 8,192 PIO word writes** to VRAM inside a DISPLAY_OFF bracket. Whenever that overran VBlank the disabled display ate scanlines → the title bar (frontend row bursts) and the rolling gameplay bar. A/B proof at a matched fall-frame: **0223 renders a mostly-BLACK screen** (the user's capture class); **0224+ renders the complete scene**.

## Architecture implemented
- **Vertical RING:** the Genesis 64×32 plane is a ring of the 64-row tall shadow: plane_row = tall_row & 31; **VSRAM carries the full scroll value** (the old &7 residual + window reprojection deleted). The tall buffers are retained deliberately: they are the readable PC080SN C-window shadow (arcade plane intent — category-2 state), not dead middleware; the staged 4KB pair is retained as the ring-ordered DMA source and readable shadow (title glyph probes unchanged).
- **Incremental projection:** vertical scroll streams only the rows entering the window (1 row = 128 B DMA); horizontal streaming marks **dirty columns** at the producer cell-writes (bitset; replaces the coarse tall-dirty flag) — each column is projected through the ring, gathered to a 64 B bounce, and committed as one DMA. Scene entry forces a full 32-row projection streamed via row-dirty under budget.
- **Bounded display-on commits:** per plane per frame ≤16 row DMAs + ≤24 column DMAs (worst ≈5 KB, inside the display-on VBlank DMA budget with N1's 640 B SAT + patterns). **The DISPLAY_OFF bracket is deleted; the display never turns off.**
- Frontend scenes run the same paths with base 0 (identity) — one code path for title/attract/gameplay.
- Legacy mainline force-commit callers stubbed (dirty bits serve them next VBlank).

## Builds
| Build | SHA | Status |
|---|---|---|
| 0224 | `0cd5b7e895143db1…` | **REJECTED** — narrow-strip descriptor rows misread as viewport-relative; my +base remap misplaced 4-row FG bands (descriptors already carry ring rows). Also the initial budgets (10/12). Preserved. Display-on proof established here (clean title, full fall-frame). |
| 0225 | `058ff0e17b76ee3c…` | **REJECTED** — budget raise only (16/24); seam persisted, superseded same session. Preserved. |
| **0226** | `67017c78746fed2f…` (1,584,264, counter 226, GATE_PASS) | **N2 candidate = rolling.** Narrow remap reverted (ring rows native). One documented residual below. |
opcode 216 unchanged; coverage paired per build.

## Validation (MAME; 0223 = old-plane baseline)
- **Title/READY/attract-entry: clean, no horizontal bar, display on** (0224+0226 captures vs the user's barred captures).
- **Gameplay: complete frames during the fall and scroll** (vs 0223's near-black fall frame); no rolling bar in any captured frame; scrolling advances with streamed columns (terrain progresses, platforms/pits render); Rastan + lizards stable and correct (N1 unregressed in every frame); HUD suppression unchanged.
- **Residual (documented, next iteration):** a single-row artifact line at a fixed plane row during gameplay scrolling (garbage attributes — a remaining producer/ring addressing mismatch under investigation) and possible brief right-edge column staleness. Absent at title/READY/story. This is a bounded correctness defect in one row-addressing path, not a return of the display-off architecture.
- Collision/KF-067: untouched — the collision side-channel remains RAM gameplay state; the lizard −8 compensation retained; the joint map/player retune deferred (documented as unsafe to couple into N2).
- Cave/terrain-progression defects: inherited, unchanged in scope, for Cody per the mandate.

## Resource before/after (plane path)
| Metric | 0223 (old) | 0226 (N2) |
|---|---|---|
| Per-vertical-crossing work | 8 KB WRAM copy + 8,192 PIO words, display OFF | ≤2 row projections (256 B) + 2 row DMAs (256 B), display ON |
| Per-streamed-column work | full reproject + 32-row dirty | 32-cell project + one 64 B DMA |
| Display-off bracket | required every frame with dirty planes | **deleted** |
| Frontend row bursts | PIO under display-off (the title bar) | budgeted DMA, display on |
| WRAM | tall 16 KB + staged 8 KB | same buffers, re-purposed as shadow/ring (deletion of staged deferred to the follow-up once DMA-from-tall lands); +80 B (col bitsets + bounce) |
| VBlank plane cost | unbounded (the bar) | bounded ≈5 KB DMA worst case |

## USER MUST VERIFY (BlastEm / Exodus / Nomad / direct capture)
1. Title, throne, BEST-5, READY: no horizontal black bar anywhere. 2. Gameplay: no rolling bar; no large blank/partial frames (the capture-device class). 3. The residual thin seam line during scrolling — report visibility on hardware (fix queued). 4. Sprites remain stable (N1). 5. Speed retained or improved.

## STOP status
NOT triggered — the display-off architecture is removed and proven by A/B capture; the residual seam is a concrete, correctable addressing defect queued for the next sequential build.
