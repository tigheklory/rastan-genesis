# Andy — Build 0159: Collision Producer Pipeline Owner (Analysis Only, No Build)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `b6937d3`, clean (only gitignored MAME trace churn). Accepted Build 0158
ROM `2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158. **No source/spec/tool/ROM
edit, no build.** KNOWN_FINDINGS touched: KF-039 (WRAM rebase), KF-040/KF-041 (copied pipeline step not executed
on Genesis). OPEN issue: OPEN-017.

## 2. Address mapping method
`build/rastan-direct/address_map.json`: `relocation_delta = 0x000200`, arcade_source `[0,0x60000)`. Genesis =
arcade + 0x200. Confirmed byte-for-byte against `build/maincpu.disasm.txt` / `build/genesis_postpatch.disasm.txt`.
A5 WRAM: arcade `0x0010C000` → Genesis `0x00FF0000` (KF-039). Producer store PCs: arcade
`0x559EC / 0x55A62 / 0x55A82` → Genesis `0x55BEC / 0x55C62 / 0x55C82`.

## 3. Arcade producer execution timeline
`states/traces/build_0159_collision_producer/arc_buffer.txt` (arcade `rastan`, write-tap on the collision buffer
`0x0010DE00..0x0010FDFF`, boot→coin→start, F0..840): **8192 writes, frames 6..306**, from two writer PCs:
- **PC=0x03AF02 ×4096** — the **startup work-RAM zeroing loop** (`movea 0x10C000,a0; movea 0x10C002,a1;
  move.w #0,(a0); move.w #8191,d0; .L: move.w (a0)+,(a1)+; dbra` — a propagate-fill that zeros all of
  0x10C000..0x10FFFF; 4096 of those words land in the buffer range). This is initialization, **not** a
  content producer.
- **PC=0x0559F0 ×4096** — the **PC080SN BG tilemap producer** store `0x559EC` (reported +4 by m68k prefetch);
  it writes the real per-cell collision codes into the buffer. Reached via the tilemap dispatch `0x55948` on the
  **a5@0x10A8==0 (BG)** branch → `0x55968` → producer `0x559B2`. (The FG producer `0x55A14` / stores
  `0x55A62/0x55A82` did not fire in Stage 1.)
So the arcade builds the Stage-1 collision map from the **BG tilemap pass** as a side effect of PC080SN
tilemap population.

## 4. Genesis producer non-execution timeline
Prior probe (`states/traces/build_0159_collision_rebase/`): the producer stores `0x55BEC/0x55C62/0x55C82`
**never execute**, and there are **zero writes** to the raw buffer range `0x10DE00..0x10FDFF`. (The rebased
zeroing loop still runs — it is opcode_replaced to zero Genesis WRAM `0x00FF0000+` — which is why the mapped
buffer `0x00FF1E00` reads all-zero rather than garbage; the raw `0x10DExx` the reader uses is untouched ROM.)

## 5. Arcade caller/predecessor chain
`0x55948` (tilemap dispatch): `cmpiw #0,a5@0x10A8` → BG branch `bsrw 0x55968` (a5@0x10A8==0) or FG branch
`bsrw 0x55990` (a5@0x10A8!=0). `0x55968` loads `a0 = a5@0x10A0` (ARCADE_FIX_DEST_BG), loops `bsrw 0x559B2`
(BG producer, store `0x559EC`). `0x55990` loads `a0 = a5@0x10A4` (ARCADE_FIX_DEST_FG), loops `bsrw 0x55A14`
(FG producer, stores `0x55A62/0x55A82`). Both producer subroutines write the collision buffer via
`... move.l a0,d7; subil #0xC08000,d7; lsrl; addil #0x10DE00,d7; moveal d7,fp; move.w d0,fp@` — i.e. they
compute the collision cell from the VRAM (0xC08000) target and store the tile-derived code.

## 6. Genesis mapped caller/predecessor comparison
The dispatch `0x55B48` (arcade `0x55948`) is **intact and executes**, but both producer entry routines are
**wholesale-replaced** by opcode_replace (Builds 0154/0155):
- Genesis `0x55B68` (arcade `0x55968`, BG) = `jsr 0x70248` (`genesistan_hook_tilemap_plane_a`) + NOP block.
- Genesis `0x55B90` (arcade `0x55990`, FG) = `jsr 0x703EA` (`genesistan_hook_tilemap_fg`) + NOP block.
Consequently the `bsrw 0x559B2` / `bsrw 0x55A14` calls are gone, and the producer subroutines `0x55BB2` /
`0x55C14` have **no remaining callers** (grep of the postpatch disasm finds none — orphaned/dead). Additionally
Genesis `a5@0x10A8 = 0x80` (nonzero; Build 0155) routes the dispatch to the **FG** branch, so even the BG hook
`0x70248` is dynamically dead — only `genesistan_hook_tilemap_fg` runs.

## 7. First divergent PC/state
At tilemap dispatch `0x55B48`: (a) `a5@0x10A8 = 0x80` on Genesis vs `0` on arcade → FG branch instead of BG;
(b) both producer entry routines are replaced by `jsr <staging hook> + NOPs`. The staging hooks emit the VDP
tilemap (Genesis Plane A/B) but do **not** reproduce the collision-cell writes to `0x10DE00`. That omission is
the divergence: the arcade tilemap pass produces both VRAM tiles **and** collision cells; the Genesis hook
produces only VRAM tiles.

## 8. Relationship to PC080SN/FG/tilemap staging
Direct and causal. The collision-map producer is **the arcade PC080SN tilemap-population routine itself**
(double-duty: VRAM tiles + collision cells). Build 0154 (`genesistan_hook_tilemap_plane_a` @ arcade 0x55968) and
Build 0155 (`genesistan_hook_tilemap_fg` @ arcade 0x55990) replaced those routines to redirect tile output to
the Genesis VDP; the replacements intentionally implement only the rendering half and drop the collision-cell
half. This is a KF-040/KF-041 instance: a copied pipeline step (collision production) that no longer runs because
its host routine was replaced by a partial Genesis reimplementation.

## 9. State-causality answers
1. **Arcade path:** startup zeroes WRAM incl. buffer (loop @0x3AEFE); then the BG PC080SN tilemap producer
   `0x559B2` (store `0x559EC`) writes 4096 collision cells (F6..306) via dispatch `0x55948` (a5@0x10A8==0).
2. **First Genesis divergence:** dispatch `0x55B48` — `a5@0x10A8=0x80` (FG branch) and both producer entries
   replaced by `jsr genesistan_hook_tilemap_plane_a/fg` (opcode_replace @ arcade 0x55968/0x55990).
3. **Present/gated/bypassed/unreachable?** **Bypassed** — entry routines replaced by `jsr hook + NOPs`; producer
   subroutines `0x55BB2/0x55C14` orphaned (no callers). BG branch additionally gated off (a5@0x10A8!=0).
4. **Caused by prior Genesis tilemap/PC080SN staging work?** **YES, directly** — Builds 0154/0155 tilemap
   staging hooks replaced the double-duty arcade producers and implement only the VRAM half.
5. **State that should exist:** the collision buffer (zeroed by startup) filled with per-cell collision codes
   derived from the Stage-1 tilemap tiles.
6. **Earlier code that should create it:** the PC080SN tilemap producers `0x559B2`/`0x55A14` — now the Genesis
   staging hooks — should also emit collision cells.
7. **Why not on Genesis:** the staging hooks stage VDP tiles only and omit the collision-cell writes; the arcade
   producer subroutines are orphaned.
8. **Build 0159 boundary proven?** **Owner proven; not a bounded in-scope fix.** The remedy is to make the
   Genesis tilemap-staging path also emit collision cells (extend `genesistan_hook_tilemap_fg`/`_plane_a`, or add
   a dedicated collision producer) — i.e. generate the map elsewhere, in the tilemap-staging + collision domain
   (out of this analysis' scope).

## 10. Readiness classification: **D** (producer intentionally dead; collision map must be generated elsewhere)
The producer is not accidentally gated — it was **deliberately replaced** by the Build 0154/0155 PC080SN
tilemap-staging hooks, which implement only rendering. Reviving the arcade producer is wrong (it would raw-write
VRAM 0xC08000, which the hooks exist to avoid). The collision map must instead be **generated by the Genesis
staging path** (extend the tilemap hook to also emit collision cells into WRAM 0x00FF1E00, or add a collision-map
producer that runs alongside). The owner is proven; the fix lives in the tilemap-staging/collision domain and is
therefore a "generate elsewhere" boundary, not a bounded producer-revival. **Not A** (fix not bounded within this
task's non-rendering scope). Not B/C (caller, divergence, and source state are all proven).

## 11. Exact next implementation boundary if ready
Not in this task's scope. The next build (a tilemap-staging/collision task) should extend the Genesis PC080SN
tilemap staging hook(s) so that, for each staged Stage-1 cell, it also writes the arcade collision code into the
mapped collision buffer `0x00FF1E00 + (vram−0xC08000)/2` — reproducing the arcade producer's collision half —
and then (separately) rebase the collision READER (0x53C64/0x5A4CE) + compares/converters (the 9-site set) to
`0x00FF1E00` so the reader consumes the produced map. Reader-rebase alone remains unsafe until production exists.

## 12. Open/Closed Issues Impact
OPEN-017 advanced: the dead collision producer is owned by the **Build 0154/0155 PC080SN tilemap-staging hooks**
(`genesistan_hook_tilemap_plane_a` @0x55968, `genesistan_hook_tilemap_fg` @0x55990), which replaced the
double-duty arcade tilemap producers and implement only the VRAM/rendering half, dropping the collision-cell
writes to 0x10DE00. Fix = extend the staging path to emit collision cells (then the coordinated buffer rebase).
No new issue, none closed.

## 13. KNOWN_FINDINGS impact
Option A — no new finding indexed this pass. This is a concrete instance of KF-040/KF-041 (copied pipeline step
not executed because its host routine was replaced by a partial Genesis reimplementation). If pursued, warrants a
named finding: "PC080SN tilemap-staging hooks (0154/0155) drop the arcade collision-map producer; buffer 0x10DE00
never filled."

## 14. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME write-taps (arcade
`rastan` + Genesis Build 0158) + static disasm; arcade program remains the reference. Did not modify the tilemap
hooks, mode=0x0008 handler, stage controller, sprites, scroll, continue/game-over, D00298, Exodus, audio, or
rendering. Did not rebase 0x0010DE00 or patch the reader.
