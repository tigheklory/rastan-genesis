# Andy/Fable — N2 Native Plane Correctness Follow-Up (**Build 0227 = candidate**)

**Date:** 2026-07-20 · **Mode:** Andy/Fable (Opus) · **Evidence:** `states/traces/n2_plane_correctness_followup_20260720_211217/`
**Recovered state:** counter 226, rolling = 0226 (`67017c78746fed2f…`, 1,584,264) byte-identical. opcode_replace 216. coverage(0226) 0x182C88.
**JSON hashes (re-read this task):** address_map `96b4d0bd989a7321…`, patch manifest `aae69e76bec2c636…`, spec `318f3469b1d53f14…` (no fixed offsets; all Genesis targets resolved through current mapping).
**Artifacts preserved:** 0219–0227 all present and unchanged.

## User hardware evidence (Build 0226, direct capture — authoritative)
N1/N2 wins confirmed on hardware: dramatically faster, no sprite flicker, lizard components stable, title/attract bar gone, rolling gameplay black bar gone. **Remaining N2 plane defects:** (1) a prominent cyan/white horizontal terrain band across gameplay; (2) FG vertically displaced ~half a screen after horizontal movement; (3) incorrect terrain blocks upper/right; (4) possible right-edge column staleness. Deferred (recorded, NOT fixed here): gray orb/star projectile, sword hitbox, lizard/Rastan damage, projectile ownership/palette, audio, N3.

## First exact divergence — PROVEN
Instrumented Genesis 0226 at steady gameplay (`probe226.txt`): `scYfg = scYbg = 0x0149` **constant**, `fgBase = bgBase = 0x17 (=23)` **constant**, both tall buffers fully populated (64 rows). The cyan band is present **before any horizontal scroll** (scXfg=0) at a **fixed screen row ≈ 9** — exactly the row where the 0226 ring wraps (plane row 31→0, since base=23 ⇒ i=9 ⇒ plane row 0).

The 0226 ring model changed two things vs the proven 0223 model:
- **VSRAM = full (−scY+BIAS)** instead of the `&7` residual, so the plane display origin became `base&31`.
- **staged[(base+i)&31] = tall[base+i]** (ring-row remap) instead of `staged[i] = tall[base+i]` (window).

But the **existing producers were never converted to ring coordinates**: the live gameplay BG producer (`genesistan_hook_tilemap_plane_a`) writes `staged_bg_buffer` at **arcade-row&31** and the frontend/narrow writers use **viewport rows 0..31**. With VSRAM now carrying the full value while content sat in the 0223 window/viewport convention, screen top no longer mapped to `tall[base]`:
- **Cyan band** = the ring **wrap seam** at plane row 31→0 (screen row 9) — a *placement* artifact, **not** wrong tile data and **not** DMA corruption (the identical tall/staged bytes render correctly under the 0223 coordinate model — proven by 0227 below).
- **Half-screen FG displacement** = a **32-row-domain coordinate-space error**: VSRAM carried the full scroll value while FG content was placed in the 0223 window convention; the two frames differ by `base`≈16–23 rows ⇒ the ~half-screen offset that appears once scrolling exercises the mismatch.

Conclusion: **0223's plane coordinates were correct; the *only* 0223 plane defect was the display-off bracket (the black bar). The 0226 ring rewrite was the over-reach that introduced the band and displacement.**

## Correction (smallest durable fix within native N2)
Reverted `vdp_comm.s` and `tilemap_hooks.s` to the proven **0223 coordinate pipeline verbatim** (window→staged[0..31], VSRAM `&7` residual, unchanged producers/projection/dirty-tracking), then applied the **single architectural change that removes the bar**:
- **Deleted the per-frame DISPLAY_OFF/ON bracket** in `_vblank_service` — the display now stays enabled through every frontend and gameplay commit. (The one-time `vdp_boot_setup` display-off at cold boot is unrelated and retained.)
- **Converted the two heavy full-row committers** (`vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`) from PIO to **bounded 68k→VRAM DMA** (new `.Lplane_dma_row`, autoinc 2, 64-word rows) so display-on commits are fast and tear-free. The low-volume frontend narrow-strip PIO is left as-is (static screens commit almost nothing).

No producer coordinate changed; no ring, no col-dirty bitsets, no VSRAM change, no second renderer, no display-off, no hard-coded camera/terrain. The ring machinery is fully removed (static gate: 0 residual ring symbols).

## Data flow (old 0226 ring → new 0227)
- **0226:** producers (arcade-row&31 / viewport) → staged → ring projection re-placed rows at (base+i)&31 + VSRAM full ⇒ seam + displacement; commits via ring row/col DMA.
- **0227:** producers (unchanged) → `vdp_project_*_tall_if_dirty` (0223) → staged[0..31] + \*_row_dirty ⇒ VSRAM `&7` ⇒ screen row 0 = tall[base]; dirty rows committed via bounded DMA, display on.

## Structures deleted (vs 0226) / added
Deleted: ring engine (`vdp_plane_service_bg/fg`, `.Lplane_service`, `.Lps_*`), `bg_col_dirty`/`fg_col_dirty`, `plane_col_bounce`, producer col-dirty marking, full-VSRAM scroll. Added: `.Lplane_dma_row` (row DMA helper). Net: −196 bytes ROM vs 0226 (1,584,264 → 1,584,068).

## Collision / KF-067
Untouched. Collision side-channel remains RAM gameplay state (`genesistan_stage_bg_collision_column` → 0xFF1E00); lizard −8 compensation retained. This task changed only the VRAM commit path, not the coordinate model or collision, so KF-067 disposition is unchanged and no joint retune was attempted (correctly out of scope for a commit-path fix).

## Title glyph readbacks
Unchanged — the 0223 staged buffers and their readable content are restored verbatim; the two title glyph probes read the same shadow they did in 0223. Title renders clean (`snap227/0000.png`).

## Full-game coverage model
By construction: the fix is coordinate-and-commit-path only, identical for every scene/producer/tileset the 0223 pipeline already served (frontend base-0, gameplay base-N, cave tileset selection unchanged). No stage-specific layer added or removed.

## Validation (all MAME; labeled)
- **MAME Genesis 0226 (N2 fault baseline):** cyan band at screen row 9 with scXfg=0; FG tears after scroll (`probe226/0003.png`).
- **MAME Genesis 0227 (candidate):** title clean, no bar (`snap227/0000`); gameplay pre-scroll **no cyan band** (`snap227/0001`); sustained horizontal scroll coherent BG+FG, **no band, no displacement, no wrong blocks, right edge streams** (`snap227/0003,0004`); jump/vertical-scroll coherent (`stress227/0002,0004`); frontend throne/story + BEST 5 clean, no bar (`frontend227/0002,0003`). N1 sprites unregressed throughout (Rastan complete; lizards complete & green; no pop-in; clean retirement).
- **Performance (`dma227b.txt`, tap held):** steady plane DMA ~0; per-frame DMA usually 640 B (N1 SAT only); **peak 4,736 B/frame** (a full 2,048-word plane reproject on jump + 640 B SAT) — **within the ~7,600 B/frame VBlank DMA budget** with headroom. DMA ≤ 0223's PIO volume (same data, faster path), display never disabled ⇒ speed preserved/improved.

## Builds
| Build | SHA | Size | Status |
|---|---|---|---|
| 0226 | `67017c78746fed2f…` | 1,584,264 | N2 fault baseline (band + displacement); preserved |
| **0227** | `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0` | 1,584,068 | **candidate = rolling; GATE_PASS; counter 227** |
opcode 216 unchanged; coverage 0x182C88 → 0x182BC4 (source shrank; paired in both gate scripts). No numbered build rejected this task (the first candidate was correct).

## Deferred defects still reproducing in 0227 (recorded, NOT fixed — for Cody/Tighe)
Gray orb/star in the FG floor (visible bottom-center of gameplay shots); sword hitbox alignment; lizard/Rastan damage; projectile ownership/palette; audio; N3 composite merging.

## USER MUST VERIFY (BlastEm / Exodus / Sega Nomad / direct capture)
1. Gameplay: **no cyan/white horizontal band** anywhere, at rest or scrolling. 2. **No half-screen FG displacement** after walking right. 3. No wrong terrain blocks upper/right; right edge streams without stale strips. 4. Title/throne/story/BEST 5/READY: **no black bar**, display never blanks. 5. Sustained horizontal + vertical (jump) scroll stays coherent. 6. N1 sprites stable (Rastan/lizards complete, green, no pop-in). 7. Speed retained or better. 8. Pit/platform transitions stream correctly (automation stayed on Stage-1 outdoor; if you can reach the cave, confirm the source-family transition).

## Compliance / STOP
Arcade owns execution; helpers RTS; no second renderer, no display-off per frame, no hard-coded terrain/camera, no ring. **STOP: not triggered** — a patch-safe boundary was proven and the first candidate passed.
