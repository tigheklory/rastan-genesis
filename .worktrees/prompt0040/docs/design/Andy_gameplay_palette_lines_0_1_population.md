# Andy — Gameplay Palette Lines 0/1 Source Population — PASSING CANDIDATE (Build 0162)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `ed44176` (pre-build), clean. Working candidate baseline Build 0161
(`79c2c016…`, counter 161, opcode_replace 137, coverage 0x1820A4). Accepted build (repo policy) remains 0160
until Tighe accepts; this task continues from Build 0161's line-3 result. New candidate Build 0162 produced (§16).

## 2. User correction: line 3 only is not enough
Build 0161 populated only CRAM line 3. Gameplay must populate lines 0 and 1 too (arcade-owned), not by any
means but from the correct arcade banks. Exodus showing "only line 3" is a timing/view artifact, not the target.

## 3. Current Build 0161 palette state
At gameplay F=560: line 2 nz=15, line 3 nz=15 (Build 0161), **line 0 nz=0, line 1 nz=0**.

## 4. Arcade bank 0/1 ownership trace
`states/traces/lines01/arc_b01.txt` (mame `rastan`): arcade bank 0 = `0000 7BDE 001E 29D0 4298 29D4 194C 7BDE…`,
bank 1 = `0000 001E 001E…` — both populated, written **directly to palette RAM 0x200000/0x200020 by 0x03BA84
(inside 0x3BA64)** at F=7 (a3=ROM 0x04EAFA; Caller 1 a0=0x200000, 768 words = banks 0-47). These are DIRECT
palette-RAM writes (unlike bank 51's source-buffer-only path).

## 5. Genesis line 0/1 failure proof
`states/traces/lines01/gen_l01.txt` (Build 0161): lines 0/1 ARE populated by `hook_3ba64` at F=14 (nz=15/15,
correct converted banks 0/1) and persist through F=131 — then at **F=211 they are ZEROED**. Writer of the zeros:
**`hook_45dae` (PC 0x071986) writes lines 0/1 = 0000 at F=210**. Its bank-0 chunk (a1=0x200000) copies the
sprite-palette SOURCE buffer `a5@0x1600 = 0x00FF1600` -> staged lines 0..3; on Genesis that source buffer is
never populated (all zero, per Build 0161 analysis), so the unconditional write clobbered lines 0/1 (and 2/3)
with black. Lines 2/3 get re-populated after F=210 (line 2 = hook_3ba64 bank 48; line 3 = Build 0161 bank-51
fix), but lines 0/1 are not re-populated (banks 0/1 are written only once, at F=7) -> they stay black.

## 6. Producer mapping to Genesis
Lines 0/1 have a correct producer (`hook_3ba64` staging the direct palette-RAM writes of banks 0/1). The
blocker is `hook_45dae` clobbering them with the empty Genesis source buffer. Same empty-source-buffer root as
KF-043, but here it manifests as a destructive overwrite, not a missing write.

## 7. State-causality answers
1. **What should exist?** Staged lines 0/1 hold the converted arcade banks 0/1 during gameplay (alongside 2/3).
2. **Which code?** `hook_3ba64` already stages them; `hook_45dae` must stop clobbering them with the empty
   source buffer.
3. **Why not now?** `hook_45dae`'s bank-0 chunk unconditionally writes converted words from the empty
   `0x00FF1600` source, zeroing lines 0/1 that `hook_3ba64` correctly staged.

## 8. Readiness classification: **B** (existing hook, bounded fix) — implemented
`hook_45dae` already runs; its unconditional write from the empty source is the bug. Bounded fix: skip writing
ZERO converted values (advance the staged slot positionally regardless), so an empty source no longer clobbers
the real palette, while a populated source still writes normally.

## 9. Exact source change if built (`palette_hooks.s` only; no opcode_replace change)
In `genesistan_palette_hook_45dae` `.L45_loop`: after `bsr .Lxbgr555_to_cram`, `tst.w %d1; beq .L45_skip_write;
move.w %d1,(%a2)`; `.L45_skip_write: addq.l #2,%a2` (positional advance, skip zero writes). Coverage
0x1820A4 -> 0x1820AC (+8, paired-updated in postpatch + verify). opcode_replace stays 137.

## 10. Static validation
GATE_PASS; boot guard PASS. opcode_replace 137; coverage 0x1820AC. Selector `0x505CE=movel #0x0005116B` (0159)
and command `0x5122E=movew 0xff0016` (0158) intact. ROM SHA `7bcb31790b2c6db44425655d486c0b74bf3a286a23e77b912594e7e78a9674b9`, size 1,581,228, counter 162. Build 0161
candidate preserved (1,581,220 B).

## 11. Runtime lines 0-3 validation (deterministic, two identical runs; F540/560/580 stable)
| line | Build 0161 | Build 0162 |
|---|---|---|
| line 0 | nz=0 | **nz=15** `0000 0EEE 000E 0468 08AC 046A 0246 0EEE…` |
| line 1 | nz=0 | **nz=14** `0000 0000 08AE 068E 046A 0046 0024 0A60…` |
| line 2 | nz=15 | **nz=15 (unchanged)** |
| line 3 | nz=15 | **nz=15 (unchanged, Build 0161 preserved)** |
Line 0 is the faithfully converted arcade bank 0 (entry1 arcade `7BDE`->CRAM `0EEE` white; entry2 `001E`->`000E`).

## 12. Cross-emulator note
This changes palette POPULATION (lines 0/1 now non-black during gameplay), not the commit path/timing
(`vdp_commit_palette` unchanged, still the only CRAM commit). Effect: all four gameplay lines are populated
throughout, so any debugger view (BlastEm/MAME/Exodus) that reaches gameplay should now show lines 0-3
populated rather than a subset. No Exodus-specific behavior added.

## 13. Selector/staging regression
`a5@0x10A8=0x0000` (0159); `staged_fg=2016` (0160); `staged_bg=2048` (0154); Build 0161 line 3 intact (nz=15);
command `a5@0x137A=0x00FF` (0158) — all confirmed at F540/560/580.

## 14. Minimal visual validation
Runtime/state only: all gameplay CRAM lines 0-3 internally populated with arcade-owned converted colors. BG
(line 2) unchanged/visible. Frontend title/story/BEST5/item-page IDENTICAL to 0160/0161 (title represented=15,
staged_bg/fg=560/66, line3=0 at title). No new fatal address; deterministic. **User to confirm pixels.**

## 15. Collision observation (unchanged)
Collision WRAM `0xFF1E00` nz=0 (empty); reader raw `0x0010DE00`; 2/3/0 active. Deferred.

## 16. Build artifact path/SHA/size/counter if built
`dist/rastan-direct/rastan_direct_video_test_build_0162.bin`, SHA `7bcb31790b2c6db44425655d486c0b74bf3a286a23e77b912594e7e78a9674b9`, 1,581,228 B, counter 162. PASSING
CANDIDATE (preserved). Builds 0142-0161 not overwritten (Build 0161 preserved at 1,581,220 B).

## 17. Rejected candidate path/SHA if applicable
None — this candidate passed.

## 18. Open/Closed Issues Impact
OPEN-017 advanced (build-verified): all four gameplay CRAM palette lines are now populated from arcade-owned
data — lines 0/1 (banks 0/1) via `hook_3ba64`'s direct-write staging, no longer clobbered by `hook_45dae`'s
empty-source copy; line 2 (bank 48) and line 3 (bank 51, Build 0161) intact. Remaining OPEN-017: visible-pixel
confirmation; collision producer; player/Rastan sprite geometry. Not closed.

## 19. KNOWN_FINDINGS impact
Reinforces KF-043 (sprite-palette source buffer `0xFF1600` unpopulated on Genesis): here it caused
`hook_45dae`'s bank-0 chunk to CLOBBER the correctly-staged lines 0/1 with black. Fix: `hook_45dae` skips
zero converted values so the empty source cannot clobber. Documented in KF-043's follow-ups.

## 20. Architecture compliance
CONFIRMED. Single bounded `palette_hooks.s` change + paired coverage constant; no opcode_replace change; no
NOP/RTS scaffolding; no forced/hardcoded colors; no second palette system; uses `staged_palette_words` +
`vdp_commit_palette`; did not touch collision, selector, FG_SRC mapping, sprite/SAT geometry, PC090OJ, player/
camera/scroll, D00298, Exodus, audio; lines 2/3 preserved. Candidate ROMs preserved (0161 + 0162). Arcade is
the reference.
