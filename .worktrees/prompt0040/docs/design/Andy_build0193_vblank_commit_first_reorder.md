# Andy/Opus — Build 0193 VBlank Commit-First Reorder (State-Causality Analysis)

**Date:** 2026-07-16
**Type:** Analysis-only. **STOP — no build.** The commit-first reorder is architecturally unsafe (breaks sprite/plane/scroll coherence) without a full double-buffered snapshot, which is a broad renderer change (explicit STOP condition). Repo stays at Build 0193.
**Baseline:** Build 0193 `ee3d236e…`, 21.669 ms/service (1.30 frames), rate 0.769, display-off window 0.312 ms.

## Primary classification — **B** (Unsafe: the current service must prepare sprites immediately before commit)
The current order's visual coherence *depends on* `vdp_prepare_sprites` running right before the commit, because that is the only moment the in-service-produced SAT and the arcade-VINT-produced planes/scroll refer to the same arcade game frame.

## Current `_vblank_service` order (read from vdp_comm.s)
1. VBlank entry (movem)
2. `rastan_direct_update_inputs`
3. **`vdp_prepare_sprites`** — produces staged_sprite_sat + sprite tile worklist (reads the PC090OJ mirror)
4. DISPLAY_OFF
5. `vdp_commit_tiles_if_dirty`
6. `vdp_project_bg_tall_if_dirty` → `vdp_commit_bg_strips_if_dirty`
7. `vdp_project_fg_tall_if_dirty` → `vdp_commit_fg_narrow_strips`
8. `vdp_commit_sprites_vram` (sprite tile DMA + SAT DMA)
9. DISPLAY_ON
10. `vdp_reassert_fg_bank3_line`; `vdp_commit_palette` (if dirty)
11. `vdp_commit_scroll` (HSCROLL + VSRAM)
12. `jmp (0x3A208)` → **arcade VINT + main loop** (RTE; no return to _vblank_service)

## Data-lifetime trace (who produces each class, and when)
| Data class | Producer | When produced | Complete at VBlank entry? | Overwritten before next VBlank? |
|---|---|---|---|---|
| staged_sprite_sat | `vdp_prepare_sprites`/`process_candidates` | **inside _vblank_service** (before commit) | holds *previous* service's prepare | rewritten by next prepare (after the commit-first commit) |
| sprite tile worklist / residency (`sprite_tile_resident_code`) | prepare / commit_sprites_vram | inside _vblank_service | previous service's | paired with SAT |
| staged_bg_tall_buffer + bg_tall_dirty | `genesistan_hook_tilemap_*` (tilemap_hooks.s) | **arcade VINT** (after tail jump) | latest = arcadeVINT_{N-1} | rewritten by each arcade VINT during gameplay |
| staged_bg_buffer | `vdp_project_bg_tall_if_dirty` (in commit) | in commit | derived at commit time | — |
| staged_fg_tall/fg_buffer | tilemap_hooks + project | arcade VINT / commit | latest | rewritten by arcade VINT |
| staged_palette_words + palette_dirty | palette_hooks.s (3ba64/45dae/59ad4) + reassert | **arcade VINT** | latest | rewritten by arcade VINT |
| staged_scroll_x/y_bg/fg | arcade scroll write (redirected; scroll-fill hooks are no-ops under KF-015) | **arcade VINT** | latest | rewritten by arcade VINT |
| mirror (pc090oj_object_ram) | PC090OJ producers | **arcade VINT** | latest | rewritten by arcade VINT |

**Key structural fact:** only the SAT is produced *inside* `_vblank_service`; every plane/palette/scroll class is produced by the **arcade VINT**, which runs *after* the tail jump (between services). The `jmp (0x3A208)` is a tail call ending in RTE — nothing in _vblank_service runs after it.

## Coherence proof
- **Current order:** `prepare_N` reads the mirror left by `arcadeVINT_{N-1}`; the plane/palette/scroll staging at `commit_N` is also `arcadeVINT_{N-1}` (arcadeVINT_N hasn't run yet). ⇒ SAT and planes/scroll all reflect **arcadeVINT_{N-1}** — one coherent arcade game frame. ✓
- **Commit-first:** at entry N the SAT is `prepare_{N-1}` (⇐ `arcadeVINT_{N-2}` mirror), while planes/palette/scroll are `arcadeVINT_{N-1}`. ⇒ **SAT lags planes/scroll by one arcade frame** — the sprites are drawn for a camera/scroll one frame behind the background. ✗ (violates the explicit STOP condition "previous-frame commit mixes current scroll with previous pixels").
- A *uniform* one-frame-late presentation (everything lagged together) would be safe, but is unachievable by reordering alone: the coherent {SAT + planes + scroll} snapshot exists only momentarily (right after prepare) and is destroyed by the next arcade VINT before the next VBlank. Preserving it requires **double-buffering** the whole snapshot.

## Per-data-class safety classification
| Data | One-frame-late via reorder? | Class | Reason |
|---|---|---|---|
| sprite SAT | only as part of whole snapshot | **B** | produced in-service; alone it lags the arcade-VINT planes |
| sprite tile worklist/residency | with SAT | **B** | must commit with its SAT |
| BG plane (tall/buffer) | needs prev snapshot | **C** | arcade-VINT-produced; prev value overwritten → needs double buffer to pair with lagged SAT |
| FG plane | needs prev snapshot | **C** | same |
| palette | needs prev snapshot | **C** | arcade-VINT-produced; current palette + previous tiles ⇒ transient wrong colors |
| scroll (HSCROLL/VSRAM) | needs prev snapshot | **C/D** | arcade-VINT-produced; current scroll + previous sprites/pixels ⇒ position mismatch |
| CRAM line reassert | with palette | **C** | pairs with palette/tiles |
| frontend (title/story/READY) sprites | n/a (scene≠1) | A | not gameplay; unaffected |

## Buffering analysis
1. staged_sprite_sat + worklist preserved to next VBlank? **Yes** (only prepare rewrites them; nothing between prepare and the next entry touches them).
2. Does prepare overwrite SAT before a commit-first commit would read it? In commit-first the commit runs *before* prepare, so it reads the previous SAT — but that SAT is coherent with `arcadeVINT_{N-2}`, not the current planes.
3. Is commit-before-prepare enough to avoid overwrite? For the SAT alone, yes; for coherence, no.
4/5/6. **BG/FG/palette/scroll staging IS overwritten every arcade VINT during motion** — so the coherent previous snapshot does not survive to the next VBlank.
7. One-frame-late commit safe with existing single staging? **No** (incoherent under motion).
8. Minimum double buffer for a coherent commit-first: snapshot {SAT, tile worklist, staged_bg_buffer (2048w), staged_fg_buffer (2048w), staged_palette_words (64w), scroll (4w)} — ~4.2K words. A copy-based snapshot costs ~0.4 frame (defeats the perf budget); a pointer-swap requires every tilemap/palette/scroll hook to write a swappable destination (broad change). **Not bounded.**

## Empirical note (why a naive reorder would *look* safe now)
Measured over 900 gameplay frame-samples on Build 0193: **scroll changed 0×, SAT head-X changed 0×** — the game is fully static during gameplay (Rastan frozen at screen-X 0x80, scroll frozen x=0/y=0x149; the known no-progression state). While frozen, `arcadeVINT_{N-2}` state == `arcadeVINT_{N-1}` state, so the one-frame SAT/plane mismatch is invisible and a commit-first reorder would appear to fix the band with no downside. **This is not a valid basis to ship it:** the moment gameplay progression is fixed (scroll/sprite motion), the reorder tears (sprites lag the background by one frame). Shipping a change that is safe only because a separate bug freezes the game is a latent defect, and the prompt explicitly forbids accepting "looks fine"/"runs faster" as success.

## Options evaluated
1. **Full-snapshot commit-first:** requires double-buffering (broad renderer change / ~0.4-frame copy) → STOP condition. Rejected.
2. **Sprites-only commit-first:** sprites lag planes → mixes current scroll with previous sprites → STOP. Rejected.
3. **Planes/palette/scroll-only commit-first:** planes lag sprites → mixes current sprites with previous pixels → STOP. Rejected.
4. **No display-off / narrow:** window is only 0.312 ms, but it lands at ~line 124 (mid-screen); removing display-off replaces a 5-line black band with a 5-line DMA-glitch band at the same position, and VRAM/SAT DMA during active display is a real-hardware artifact risk (BlastEm/Kega/MAME model it) — not a clear win, not safe. Rejected.
5. **No build.** ✓ Chosen.

## The black band's true root and the coherent fix
The band is not caused by the display-off itself being wrong-ordered per se — it is caused by the **service overrunning one frame** (21.67 ms > 16.667 ms). Because `vdp_prepare_sprites` (~10 ms) runs before the commit, DISPLAY_OFF is issued ~10 ms into the service, landing ~line 124 (mid-screen), and rolls because the 1.30-frame service period is non-integer. The **coherence-preserving** fixes, ranked:
1. **Reduce `vdp_prepare_sprites` below ~2 ms** so prepare+commit finish inside VBlank (~2.4 ms). The remaining prepare cost is the 256-record shadow scan (4.16 ms) + 0x800 shadow copy (2.0 ms) — the KF-053-flagged follow-up: every mirror writer now sets candidates directly, so the full scan is near-redundant and can be replaced by a tracked changed-record set (with a debug-gated invariant). This eliminates the band **coherently** and pushes toward 60 Hz.
2. Failing that, getting total service < 16.667 ms (60 Hz, no missed VINTs) at least makes the band **stable at a fixed line instead of rolling** — a materially better artifact — without any coherence change.
3. A properly-designed **double-buffered snapshot** commit-first is the only way to move the commit into VBlank while lagging *everything* uniformly; it is a separate, larger bounded task requiring its own validation, not a micro-reorder.

## State-causality answers (summary)
1. Staged at VBlank entry: previous SAT (in-service) + latest planes/palette/scroll (arcade VINT). 2. Previous-completed output = the SAT (prepare_{N-1}). 3. Later-produced = none in-service except the next prepare. 4. Committed one late = the SAT relative to planes. 5. Yes — planes/palette/scroll depend on the arcade VINT that runs after entry historically, and their staging is current at entry. 6. SAT+tiles pair yes; SAT vs planes no. 7. Committing previous BG/FG/palette/scroll together would need the double-buffered snapshot. 8. One-frame-late alters only display timing, not arcade game state — but non-uniform lag tears. 9. Failure proof: under scroll/sprite motion, sprites render one frame behind the background (visible tearing/positional lag).

## Not touched
No source change. Build 0192 suppression, Build 0193 family-apply optimization, Build 0175 palette route, 0171/0172 projections, Build 0178 tile-DMA, Build 0180 SAT gating, mirror default 256 — all intact. No structured-metadata owner exists for VBlank/presentation-ordering behavior (the spec tracks opcode/hook replacements, not _vblank_service instruction order); this is stated rather than inventing a registry.
