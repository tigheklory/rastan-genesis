# Andy — Build 0159: Tilemap Staging Collision Producer — STOP (Classification C), NO BUILD

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `318e7bd`, clean (only gitignored MAME trace churn). Accepted Build 0158
ROM `2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158, opcode_replace 136.
**No source/spec/tool/ROM edit, no build** (STOP at the Phase-2 gate). KNOWN_FINDINGS touched: KF-039 (WRAM
rebase), KF-040/KF-041 (host routine replaced by partial reimplementation). OPEN issue: OPEN-017.

## 2. Hook inspection
`apps/rastan-direct/src/tilemap_hooks.s`. `genesistan_hook_tilemap_fg` (0x703EA) gameplay path
(`SCENE_GAMEPLAY_ID`, lines 291–345) reconstructs FG tiles from the **Build 0155 FG_SRC ROM model**
(`FG_SRC_BASE_GEN=0x16B1C`, seg×row iteration; `block=ROM_word(SRC+2)+0x200`, `code=ROM_word(block+colidx*2+
row*8)`), composes `D0 = attr<<16|code`, computes cell dest `a0 = CWINDOW_BASE_FG + dcol*4 + plane_row*0x100`,
and calls `genesistan_hook_tilemap_fg_fill` (LUT + attr + VDP staging). `genesistan_hook_tilemap_plane_a`
(0x70248, BG) is dynamically dead at gameplay.
- **What the hook HAS:** the arcade VRAM cell dest `a0` (0xC08000-based) — exactly the input the arcade
  collision formula needs (`0x10DE00 + (a0−0xC08000)/2`) — and the tile code.
- **What the hook LACKS:** the arcade **collision code**, which is a *separate* word read from the `a2`
  descriptor (see §3), not derivable from the tile code, and not accessed by the FG_SRC model. The hook walks
  seg×row from FG_SRC; the arcade producer walks 16 descriptors indexed by strip/col. The two iteration models
  are different.

## 3. Arcade producer semantics
Callers `0x55968` (BG) / `0x55990` (FG): `a1 = 0x10D080` (tile-source table), `a3 = 0x10D040` (descriptor-ptr
table), `a2 = *(a3)` per iteration (16 iterations). Producer `0x559B2` (BG) / `0x55A14` (FG), per cell:
- write tile to VRAM (`move.w (a1),(a0)`) — the rendering half (hooks already do this differently).
- **collision code** `d0 = *(a2 + 20 + strip*2 + col*8)`, OR `d0 = *(a2 + 34)` when `*(a2+32)==0xFF`.
- write `d0` to `0x10DE00 + (a0−0xC08000)/2`.
- **FG variant only (`0x55A14`):** a second write of constant **`1`** to the cell one plane-row above
  (`0x10DE00 + ((a0−0xC08000−0x100)/2 & 0x1FFF)`) — a "solid-above" marker — and a strip-order **flip**
  (`not.w d7; and.w #3` when `a5@0x10A8 != 2`). The BG variant has neither.
Descriptor layout confirmed at runtime (descriptor[0]@0x1200): `+20..+30 = 0x0020` (blank), `+32 = 0x00FF`
(flag), `+34 = 0x0000` (alt collision code), `+36+ = tile codes`. So real Stage-1 collision codes are
**0x0020 / 0x0000** (`&0x7F` = 0x20 / 0x00), i.e. passable/blank — **never type-8**. (Type-8 is purely the
ROM-garbage artifact of the un-rebased reader.)

## 4. State-causality answers
1. **What state should exist?** `0x00FF1E00..0x00FF3DFF` zeroed at startup (already true — the rebased startup
   loop zeros it), then filled during tilemap population with the arcade collision codes (0x0020/0x0000/…).
2. **Which code should create it?** The Genesis tilemap staging path, replacing the collision half of the
   arcade producer (0x559B2 / 0x55A14).
3. **Why not now?** The staging hooks implement only rendering; and — critically — the *running* Genesis hook is
   the **FG** hook (`a5@0x10A8=0x80`, taken 80× at the dispatch), while the **arcade builds the Stage-1
   collision map with the BG producer** (`a5@0x10A8==0`; arcade trace: only the BG store `0x0559F0` fired,
   4096×). So the producer *variant* diverges (state `a5@0x10A8` differs arcade-0 vs Genesis-0x80), and the FG
   variant carries extra semantics (solid-above marker + order-flip) that the BG map does not.

## 5. Readiness classification: **C** (source exists, safe reproduction needs more analysis) — STOP, no build
The descriptor collision source **exists and is populated** on Genesis (`0xFF1040`/`0xFF1080`, §3), and the
arcade formula is known. But a *safe, arcade-equivalent* implementation is **not yet bounded**, because:
- **(a) Producer-variant divergence.** The arcade builds Stage-1 collision via the **BG** producer
  (`a5@0x10A8==0`), but the Genesis dispatch runs the **FG** hook (`a5@0x10A8=0x80`). Emitting from the FG hook
  with FG semantics would produce a *different* map than the arcade BG map (FG adds the solid-above marker and
  order-flip). Which producer/semantics is correct for the Genesis Stage-1 map is unresolved — it hinges on the
  `a5@0x10A8` arcade-0 vs Genesis-0x80 state divergence (a Build-0155-flagged open item), not on the hook alone.
- **(b) Iteration-model mismatch.** The hook uses the FG_SRC seg×row model; the arcade collision producer uses
  a 16-descriptor strip/col walk. Bridging the hook's per-cell context to the descriptor collision code
  (including the `a2+34` alt path and descriptor-pointer addressing — ptrs like 0x1200 are low-ROM and need
  their addressing validated) is unvalidated.
- **(c) No-guess rule.** Implementing without resolving (a)/(b) would guess collision values or the producer
  variant — forbidden, and risks a *wrong* map (new gameplay bugs) worse than the current ROM-garbage type-8.
Not A/B (the hook cannot cheaply/safely emit arcade-equivalent cells today). Not D (the owner and source are
proven; it is producible, just not yet safely bounded). **STOP** per "arcade collision-cell semantics cannot be
reproduced [safely without more analysis]" and "implementation would guess collision values."

## 6. Exact hook changes
**NONE** — STOP before edit.

## 7. Exact opcode/spec changes
**NONE.** opcode_replace count stays 136; canonical coverage 0x182070; no rebase applied.

## 8. Static validation
N/A (no edit). Hook/producer semantics verified against `maincpu.disasm.txt`; descriptor tables/layout verified
at runtime.

## 9. Runtime collision production proof
`states/traces/build_0159_tsc_producer/gen_desc.txt`: at F=560 (2/3/0) the descriptor tables ARE populated
(`0xFF1040` ptrs 0x1200/0x2C88/0x2224/0x2248; `0xFF1080` all 0x0003; descriptor[0]@0x1200 collision region
0x0020/0x00FF/0x0000). `gen_which_hook.txt`: at the tilemap dispatch, `a5@0x10A8=0x0080 ×80` (FG) and
`0x0000 ×3` (BG) — Genesis runs the FG hook. Arcade (`build_0159_collision_producer/arc_buffer.txt`): BG
producer store `0x0559F0` ×4096 (a5@0x10A8==0). Confirms the producer-variant divergence.

## 10. Runtime collision reader proof
Unchanged from prior analysis: reader (0x53C64) uses raw `0x0010DE00` → reads ROM garbage (type-8). No build,
so no "after."

## 11. Early type-8 before/after
No build. Before: type-8 at F≈698 from ROM. (Note: the *real* collision codes are 0x20/0x00, so a faithful map
would eliminate the early type-8 — but only if reproduced correctly.)

## 12. 2/3/0 duration before/after
No build. Before: Genesis ≈313 vs arcade ≈588 frames.

## 13. Visible validation
Not run (no build).

## 14. Regression validation
Not run (no build). No accepted build modified; Builds 0142–0158 untouched; canonical constants unchanged.

## 15. Open/Closed Issues Impact
OPEN-017 advanced: the collision map IS producible on Genesis (descriptor source populated at 0xFF1040/0xFF1080;
real codes 0x20/0x00), but a safe build is blocked by two items: (a) the **producer-variant/state divergence**
`a5@0x10A8` arcade-0 (BG) vs Genesis-0x80 (FG) — the arcade builds the Stage-1 collision map with the BG
producer while Genesis runs the FG hook; and (b) reconciling the FG_SRC hook iteration model with the arcade
16-descriptor strip/col collision walk (incl. the `a2+34` alt path, FG solid-above marker/order-flip, and
descriptor-pointer addressing). Next step: resolve (a) then validate (b) offline before emitting cells. No new
issue, none closed.

## 16. KNOWN_FINDINGS impact
Option A — no new finding indexed. Reinforces the KF-040/KF-041 instance (tilemap hook is a partial
reimplementation) and surfaces the `a5@0x10A8` arcade-vs-Genesis producer-selection divergence as the gating
sub-problem.

## 17. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME (arcade `rastan` +
Genesis Build 0158) + static disasm; arcade program remains the reference. Did not revive the arcade producer,
did not raw-write VRAM, did not rebase 0x0010DE00, did not patch the reader, handler, stage controller, player,
camera/scroll, sprites, continue/game-over, D00298, Exodus, audio, or broad rendering.
