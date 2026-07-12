# Andy — Build 0161: Sprite-Bank Palette Chunk Routing — STOP (B), BUILD REVERTED

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `56551e1`, clean. Accepted Build 0160 ROM
`e9243ff028cdcd8f3776a51ffa54ea8438f1489bca61fd607bff0c268983e697`, counter 160, opcode_replace 137,
coverage 0x182090. A candidate Build 0161 was built and then **reverted** (see §14); accepted build stays 0160.
OPEN issue: OPEN-017.

## 2. Prior STOP-C summary
Prior analysis: gameplay FG/sprites reference Genesis CRAM line 3 (=arcade bank 51), which is black. The arcade
full bank-51 load is a 64-word memcpy (`0x3A2D0`) WRAM->palette-RAM; on Genesis it is dropped.

## 3. Pre-edit verification
- `genesistan_palette_hook_45dae` gates `a1==0x200000` only (confirmed).
- The sprite chunk arrives as: arcade `0x045DEE` `jsr 0x3a2d0`, `a1=0x200600`, `d0=64` words (banks 48-51),
  source `a0=a5@0x1600` (Genesis `0xFF1600`). This is a **sibling** of the hooked bank-0 site `0x045DB8`; the
  `0x045DEE` site was NOT hooked (Genesis `0x045FEE` = raw `jsr 0x3a4d0`).
- **Source-content check (the failing precondition):** the source ADDRESS `0xFF1600` is valid WRAM, but its
  **CONTENT is all zero** on Genesis at gameplay (banks 48-51 = 0000) — while the arcade source `0x10D600` is
  populated (bank48 `0000 0000 0010 015E…`, bank51 `0000 0842 739C 429E…`). **The source is empty on Genesis.**

## 4. Sprite-bank chunk mapping proof
Intended: arcade bank 48 (source words 0-15) -> Genesis line 2; bank 51 (words 48-63) -> line 3; banks 49,50
unused (matches `hook_3ba64`). Layout confirmed against the arcade source dump.

## 5. State-causality answers
1. **What state should exist?** Genesis staged line 3 should hold the converted arcade bank-51 colors before the
   VBlank commit (which runs).
2. **Which code should create it?** A palette hook catching the sprite-bank memcpy and converting bank 51 ->
   line 3 — BUT only if the **source** `0xFF1600` holds the bank-51 data.
3. **Why not now?** Two layers: (a) the sprite-bank memcpy destination `0x200600` is unmapped on Genesis
   (dropped) — addressed by routing the `0x045DEE` jsr to the hook; (b) **the source `0xFF1600` is not
   populated** on Genesis (the arcade sprite-palette-source producer that fills `0x10D600` does not reach
   Genesis `0xFF1600` — a raw-WRAM-literal / unhooked-producer class, same as the collision buffer). Layer (b)
   was NOT known before this build.

## 6. Readiness classification: **B** (source content not proven valid — it is zero on Genesis) — STOP
The routing boundary is correct and bounded, and I implemented it (extend `hook_45dae` for `a1==0x200600` ->
line 3; opcode_replace at `0x045DEE`). It built cleanly (GATE_PASS) but is a **no-op**: the hook's sprite branch
ran (PC 0x0719C0, F=229) and wrote line 3, but with **all zeros**, because the source `0xFF1600` is empty. Line 3
stayed `08AE 0000…`. So the acceptance target ("line 3 receives bank-51 colors") is NOT met. Per the build rule,
the build was **reverted**. Root is one layer deeper (empty source) → more analysis needed. Not A.

## 7. Exact source change if built
Reverted. (Attempted: `hook_45dae` gains a `a1==0x200600` branch routing bank 51 -> staged line 3; +1
opcode_replace at `0x045DEE`. Correct routing, but no-op due to empty source.)

## 8. Static validation
The candidate build passed GATE_PASS/boot-guard; both `0x045FB8` and `0x045FEE` routed to `jsr 0x71962`
(`hook_45dae`); selector `0x505CE` intact; opcode_replace 138; coverage 0x1820C8. All reverted to 137/0x182090.

## 9. Runtime palette validation
Build 0160 vs candidate 0161 at F=560: **line 3 UNCHANGED** (`08AE 0000×15`, nz=1) — the fix did not populate
it. line 2 nz=15 (unchanged), lines 0/1 nz=0 (unchanged), staged_bg=2048, staged_fg=2016, selector=0x0000,
cmd=0x00FF — all preserved. The sprite branch wrote zeros (empty source).

## 10. FG/sprite line-3 validation
FG cells still reference line 3; line 3 still black. Not fixed.

## 11. Selector/staging regression
Selector `a5@0x10A8=0x0000`; staged_fg≈2016; staged_bg=2048; command intact — all preserved in the candidate
(so the routing itself was non-destructive), but reverted since it was a no-op.

## 12. Minimal visual validation
Not meaningful (no-op). FG/sprites remain black (line 3 unpopulated).

## 13. Collision observation (unchanged)
Collision WRAM `0xFF1E00` empty; reader raw `0x0010DE00`. Deferred.

## 14. Build artifact path/SHA/size/counter if built
Candidate Build 0161 (`fd4b8850…`, 1,581,256 B) was produced then **REVERTED** (no-op). Accepted build stays
Build 0160 (`e9243ff0…`, counter 160). Numbered 0161 ROM deleted; source/spec/tool changes reverted; counter
reset to 160.

## 15. Open/Closed Issues Impact
OPEN-017 advanced: the sprite-bank palette **routing** boundary is correct (route the `0x045DEE` memcpy jsr to a
hook; convert bank 51 -> line 3), but it is blocked by a deeper prerequisite — **the sprite-palette source
`0xFF1600` (=arcade `0x10D600`) is not populated on Genesis** (arcade shows bank51 `0842 739C…`; Genesis shows
0000). The producer that fills `0x10D600` must be rebased/hooked so Genesis `0xFF1600` receives it (KF-039 raw-
WRAM-literal class), THEN the sprite-bank routing populates line 3. Build reverted (no-op). Not closed.

## 16. KNOWN_FINDINGS impact
Option A — no new finding indexed (owner-of-empty-source not yet proven). Candidate: "gameplay sprite-palette
source at arcade `0x10D600` is not populated on Genesis `0xFF1600`, blocking bank-51 -> CRAM line 3."

## 17. Architecture compliance
CONFIRMED. Build reverted -> repo restored to Build 0160 (counter 160, opcode_replace 137, coverage 0x182090).
No forced colors; no second palette system; the attempted change was palette-only and non-destructive; did not
touch collision, selector, FG_SRC, sprite/SAT geometry, PC090OJ, player/camera/scroll, D00298, Exodus, audio.
Arcade remains the reference.
