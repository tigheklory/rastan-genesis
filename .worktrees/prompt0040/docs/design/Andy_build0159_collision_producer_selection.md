# Andy — Build 0159: Collision Producer Selection (Analysis Only, No Build)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `13b0e59`, clean (only gitignored MAME trace churn). Accepted Build 0158
ROM `2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158, opcode_replace 136.
**No source/spec/tool/ROM edit, no build.** KNOWN_FINDINGS touched: KF-039 and the shift/relocation class
(un-relocated code-pointer literal). OPEN issue: OPEN-017.

## 2. Meaning of a5@0x10A8
`a5@0x10A8` (= `a5+0x10A8` = arcade `0x10D0A8`, Genesis `0xFF10A8`; also the helper slot
`PC080SN_DESC_REBUILD_OUT`) is the **PC080SN tilemap pass/layer selector**. The dispatch `0x55948` reads it:
`==0` → BG producer pass (`0x55968`→`0x559B2`), `!=0` → FG producer pass (`0x55990`→`0x55A14`). Compares
elsewhere test 0/1/2/4/5/6. It is set from a **pass-sequence control byte**: `a4 = a5@0x10C6; d0 = *(a4);
a5@0x10A8 = d0`.

## 3. Arcade writer/timeline
Written by the descriptor-rebuild routine (`0x558F8` / `0x55940`, `movew d0,0x10D0A8`), value = `*(a5@0x10C6)`.
`a5@0x10C6` is initialized at **`0x503CE`**: `d0 = #0x00050F6B` (sequence-table base) `+ d1`, where
`d1 = *(0x00050EE0 + a5@0x13E)` (index table). Runtime (`states/traces/build_0159_selector/arc_sel.txt`, mame
`rastan`): **`a5@0x10A8` is ALWAYS 0x0000** (histogram `0000:20`); at the collision pass `srcptr=0x050F6B`,
`*ptr=0x00`. So the arcade builds Stage-1 collision on the **BG** pass (`a5@0x10A8==0`).

## 4. Genesis writer/timeline
`states/traces/build_0159_selector/gen_sel.txt`: `0xFF10A8` is written 0x0000 by startup/arcade paths, then
**`0x0080` by `genesistan_hook_pc080sn_descriptor_rebuild+0x5E` (PC 0x071728)** at F=470, `srcptr(0xFF10C6)=
0x050F6B`, `*ptr=0x80`; then `0x0000` by the arcade_copy writer `0x055AFE` at F=528. At the tilemap dispatch,
`a5@0x10A8=0x80` dominates (×80) vs `0x00` (×3) — Genesis runs the **FG** pass. The helper faithfully
reproduces the arcade read (`moveal a5@0x10C6,a4; moveb (a4),d0; movew d0,0xFF10A8`), so the divergence is in
the **pointer value**, not the code.

## 5. BG vs FG producer semantics
BG producer `0x559B2`: writes `collision = *(a2+20+strip*2+col*8)` or `*(a2+34)` to `0x10DE00+(vram−0xC08000)/2`.
FG producer `0x55A14`: same, **plus** a constant-`1` "solid-above" write to the cell one plane-row up, **plus**
a strip-order flip (`not.w; and.w #3` unless `a5@0x10A8==2`). The arcade Stage-1 collision map is the **BG**
map (FG producer never fired in the arcade trace). Emitting FG semantics would build a *different* map.

## 6. Descriptor/table comparison — the root cause
`a5@0x10C6` is set from two ROM-table literals in one routine (arcade `0x503BC`/`0x503CE`):
- `moveal #0x00050EE0, a1` (index table) — **address-register load → postpatch RELOCATED it** to Genesis
  `0x000510E0` (verified: Genesis `0x505BC` = `moveal #0x000510E0,a1`). Index table @0x0510E0 =
  `00 01 02 03 …` (correct).
- `movel #0x00050F6B, d0` (sequence-table base) — **data-register load → postpatch did NOT relocate it**
  (Genesis `0x505CE` still `movel #0x00050F6B,d0`; should be `#0x0005116B`).
ROM proof: Genesis `ROM[0x050F6B]=0x80` (what the raw pointer reads) vs `ROM[0x05116B]=0x00` (the correctly
relocated +0x200 location = arcade's data; arcade `ROM[0x050F6B]=0x00`). So the sequence pointer lands 0x200
too low and reads `0x80` instead of `0x00`. **The postpatch relocated the sibling address-register literal but
not the data-register literal — a relocation inconsistency.** This is the KF-039/shift class, same shape as
Build 0158's command source (`movel #imm,Dn` operands are not recognized as relocatable code pointers).

## 7. Whether the BG collision map can be reconstructed on Genesis
The cleaner path is **not** "reconstruct collision from the FG hook" — it is to **fix the un-relocated literal**
(`0x00050F6B → 0x0005116B` at arcade `0x503CE`, byte-neutral opcode_replace). That flips `a5@0x10A8` to `0x00`
(BG, arcade-equivalent), so the tilemap dispatch takes the BG branch. The descriptor tables are populated
(0xFF1040/0xFF1080), so the arcade BG collision producer's inputs exist. HOWEVER: flipping to the BG pass
changes which rendering hook runs (`genesistan_hook_tilemap_plane_a` instead of `genesistan_hook_tilemap_fg`),
i.e. it alters Build 0154/0155 tilemap staging. So it is **not a collision-only change** and its collision half
still isn't emitted by the BG hook — a subsequent collision-emit + 9-site rebase would still be needed. Replay
under the corrected pass is **not yet proven**.

## 8. Relationship to visible FG tile issue
**Strongly implicated, not merely neighboring.** The un-relocated literal makes Genesis run the **FG** tilemap
pass when the arcade runs the **BG** pass for Stage 1. Build 0155's FG staging was built to accommodate the
(buggy) `a5@0x10A8=0x80`. If the correct pass is BG, the Genesis FG staging is compensating for a
mis-selected pass, which plausibly explains missing/incorrect visible FG tiles. Confirming this requires a
rendering-domain check (out of this task's scope), but the selector bug is the leading candidate.

## 9. State-causality answers
1. **Who writes a5@0x10A8 on arcade?** desc-rebuild `0x558F8`/`0x55940`, value `*(a5@0x10C6)`; `a5@0x10C6` set
   at `0x503CE` (`#0x050F6B + index`). Always 0x00 at the Stage-1 collision pass.
2. **Who writes it on Genesis?** `genesistan_hook_pc080sn_descriptor_rebuild+0x5E` (0x071728) + arcade_copy
   `0x055AFE`, from the same `a5@0x10C6` pointer.
3. **Is 0x80 a bug/hook-control/valid?** **BUG** — an un-relocated sequence-table literal (`#0x050F6B` not
   shifted +0x200) makes the pointer read `ROM[0x050F6B]=0x80` instead of `ROM[0x05116B]=0x00`. Not intentional,
   not arcade-equivalent (arcade is always 0x00).
4. **Which producer semantics for Stage 1?** **BG** (`a5@0x10A8==0`) — matches the arcade.
5. **Can the BG map be reconstructed on Genesis?** Inputs exist (descriptors populated); the correct route is
   to fix the relocation (→BG pass) then emit collision — but this changes rendering-pass selection and the
   emit/rebase is still required; replay under the corrected pass is unproven.
6. **Relationship to visible FG issue?** Strongly implicated — wrong pass (FG vs BG) selection; needs a
   rendering check to confirm.
7. **Is a Build 0159 collision-production boundary proven?** The *selector* boundary is proven (relocate
   `#0x050F6B`→`#0x05116B`), but it is a rendering-pass-selection change, not a bounded collision build; more
   (rendering-aware) analysis is needed before implementing.

## 10. Readiness classification: **C** (selector understood; not a bounded collision build) — with a D reframe
The producer selector is fully understood: Genesis `a5@0x10A8=0x80` is a **postpatch relocation inconsistency**
(data-register literal `#0x00050F6B` not shifted +0x200 while its address-register sibling `#0x00050EE0` was),
and the arcade-correct value is `0x00` (BG). But this **reframes the boundary** away from "emit collision from
the FG hook": the actionable fix is the byte-neutral literal relocation `0x00050F6B → 0x0005116B` at arcade
`0x503CE`, which changes tilemap-pass selection (FG→BG) and therefore rendering (Build 0154/0155 staging). That
is not a bounded collision-only change, and the collision emit + 9-site rebase would still follow. **Not A/B**
(not a collision-emission build). **D aspect:** the true root is a pointer-relocation/pass-selection bug,
upstream of and distinct from collision-cell emission. STOP, no build (task is analysis-only).

## 11. Exact next implementation boundary if ready
A dedicated **pass-selector relocation** build (separate from collision emission): byte-neutral opcode_replace at
arcade `0x503CE` `203C00050F6B → 203C0005116B` (`movel #0x00050F6B,d0 → movel #0x0005116B,d0`; opcode 0x203C
preserved), original bytes validated against `maincpu`. Then re-observe at runtime: (a) `a5@0x10A8` → 0x00;
(b) the tilemap dispatch takes the BG branch; (c) whether Build 0154/0155 rendering still stages correctly (or
needs rework); (d) whether the visible FG tiles appear. ONLY after that: add BG collision-cell emission +
coordinated 9-site buffer rebase. Must be validated with full Build 0154/0155 rendering regression, since it
changes pass selection. Sibling check: confirm no other routine references `#0x050F6B` un-relocated.

## 12. Open/Closed Issues Impact
OPEN-017 advanced with a new root cause: the Stage-1 tilemap **pass selector** `a5@0x10A8` is `0x80` on Genesis
(FG) vs `0x00` on arcade (BG) because the pass-sequence table base literal `#0x00050F6B` at arcade `0x503CE` is
**not relocated +0x200** (its sibling `#0x00050EE0` at `0x503BC` was). Genesis reads `ROM[0x050F6B]=0x80`
instead of `ROM[0x05116B]=0x00`. This mis-selects the FG tilemap pass (Build 0155 accommodated it) and is the
upstream cause of the dead collision-BG pass; likely also the visible FG-tile issue. Next: a dedicated
relocation build (0x050F6B→0x05116B), rendering-regressed, then collision emit + rebase. No new issue, none
closed.

## 13. KNOWN_FINDINGS impact
Warrants a durable finding if confirmed by a build: **KF (new) — "arcade `0x503CE movel #0x00050F6B,d0`
pass-sequence table base is not postpatch-relocated (+0x200) while its sibling `moveal #0x00050EE0,a1` is;
Genesis Stage-1 tilemap pass selector `a5@0x10A8` becomes 0x80 (FG) instead of 0x00 (BG)."** Not indexed this
pass (analysis only; effect not yet build-verified).

## 14. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME (arcade `rastan` +
Genesis Build 0158) + static disasm + ROM byte inspection; arcade program remains the reference. Did not patch
a5@0x10A8, the reader, the handler, the stage controller, player, camera/scroll, sprites, rendering,
continue/game-over, D00298, Exodus, or audio. Did not rebase 0x0010DE00.
