# Andy — Build 0161: Sprite-Palette Source Population (bank 51 -> CRAM line 3) — PASSING CANDIDATE

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `acd6682` (pre-build), clean. Accepted Build 0160 ROM
`e9243ff0…`, counter 160, opcode_replace 137, coverage 0x182090. Candidate Build 0161 produced (see §17);
accepted build remains 0160 until visual acceptance (artifact rule). OPEN issue: OPEN-017.

## 2. Prior reverted-candidate summary
The prior candidate routed the sprite-bank memcpy (`0x045DEE`) to `hook_45dae` but was a no-op because the
memcpy source `0xFF1600` was empty. Reverted (preserved as analysis). This task fixes the empty source.

## 3. Artifact preservation compliance
The candidate ROM is preserved as the numbered artifact
`dist/rastan-direct/rastan_direct_video_test_build_0161.bin` (not deleted). It PASSES acceptance targets, so no
revert; it awaits Tighe's visual acceptance.

## 4. Arcade 0x10D600 producer trace
`states/traces/build_0161_srcpop/` (mame `rastan`). The bank-51 source (`0x10D660`) has two real writers:
`0x059D66` (palette fade, a3=ROM `0x04EB5A`) and **`0x03BA84` (F=190, final colors `0842 739C 429E…`, a3=ROM
`0x04FE86`) — inside arcade routine `0x3BA64`**. Three `0x3BA64` callers: Caller1 `a0=0x200000` (768w, banks
0-47 palette RAM), Caller2 `a0`→`0x200600` (16w, **bank 48** palette RAM → line 2), Caller3
`lea a5@(5632),a0` = the **source buffer** (`0x10D600`=Genesis `0xFF1600`). **Bank 51 is written ONLY to the
source buffer, never to palette RAM** — unlike bank 48.

## 5. Genesis 0xFF1600 source-buffer proof
Build 0160 at F=560: `0xFF1600..0xFF167F` = **all zero** (arcade `0x10D600` = populated). On Genesis, writes to
`0xFF1600` come only from `0x03B102` (startup zeroing) and `0x03A4D4` (memcpy of the empty source); the raw
`0x10D600` gets `0x059F66` (fade, ROM-dropped). Critically, **`hook_3ba64` (replacing arcade `0x3BA64`) never
writes the source buffer** — it only advances a0 and stages when `a0 ∈ 0x200000-0x200FFF`; for the bank-51
source write (Genesis a0=`0xFF1660`, rebased via a5-relative Caller3) it SKIPS. So line 3 (=bank 51) stayed
black.

## 6. Producer mapping to Genesis
`hook_3ba64` DOES run for the bank-51 source write (a0=`0xFF1660`) and DOES compute the converted bank-51 color
(same a3 ROM source, relocated), but discards it (skip). The fix reuses this: stage the converted color to
line 3.

## 7. State-causality answers
1. **What should exist?** Genesis CRAM line 3 should hold the converted arcade bank-51 colors before commit.
2. **Which code?** The palette hook that already processes the bank-51 write (`hook_3ba64`) should stage it to
   line 3 (rather than requiring the intermediate source buffer + memcpy).
3. **Why not?** `hook_3ba64` only stages `a0 ∈ 0x200000` (palette RAM); the bank-51 write goes to the source
   buffer (`0xFF1660`), which the hook skips — and no other producer routes it to a line.

## 8. Readiness classification: **B** (route directly from the arcade source into staged line 3) — implemented
Chose B over manufacturing the intermediate buffer: `hook_3ba64` already converts the bank-51 source words, so
stage them directly to line 3. Bounded, source-content proven (the hook has the colors), no hardcoded colors,
no second palette system, uses `staged_palette_words` + `vdp_commit_palette`.

## 9. Exact source change if built (`palette_hooks.s` only; no opcode_replace change)
In `genesistan_palette_hook_3ba64`, after `move.l %a0,%d4; addq.l #2,%a0`, added a range branch: if
`d4 ∈ [0x00FF1660, 0x00FF1680)` (bank-51 sprite-source-buffer write), set `moveq #3,%d6` and `bra.w
.L3ba64_line_ok` — reusing the existing xBGR→CRAM conversion and line-3 staging (the low-5-bits of d4 give the
entry). Otherwise fall through to the unchanged `a1==0x200000` palette-RAM path. Coverage 0x182090→0x1820A4
(+0x14, paired-updated in postpatch + verify). opcode_replace stays 137.

## 10. Static validation
GATE_PASS; boot guard PASS. opcode_replace 137 (unchanged); coverage 0x1820A4; disasm shows the new branch
(`0x719BC cmpil #0xFF1660,d4`; `0x719CC moveq #3,d6`). Selector `0x505CE=movel #0x0005116B` intact. Routes:
`0x5122E=movew 0xff0016` (0158), `0x3D24C=jsr 0x708ea` (0156), `0x3A92A=jsr 0x708b6` (0152). ROM SHA
`79c2c01610e153b813deef590de8a8cd631e02a80b2c59111ff2929b86f04a8f`, size 1,581,220, counter 161.

## 11. Runtime source-buffer validation
The intermediate `0xFF1600` buffer is bypassed (classification B stages directly), so it remains zero — expected
and irrelevant; the acceptance target is line 3, met in §12.

## 12. Runtime CRAM line-3 validation (deterministic, two identical runs; F540/560/580 stable)
| line | Build 0160 | Build 0161 |
|---|---|---|
| line 3 nonzero | **1** (`08AE 0000×15`) | **15** (`08AE 0000 0EEE 08AE 044A 0246 0008 0006 00EE 006E 0080 0060 0888 0666 0040 000E`) |
| line 2 nonzero | 15 (`0000 0642…`) | **15 (unchanged)** |
| line 0/1 | 0 / 0 | **0 / 0 (unchanged)** |
Line 3 = faithfully converted arcade bank 51 (entry15 `000E` ← arcade `001E`; near-black entries e.g. arcade
`0842`→CRAM `0000` are correct low-bit truncation). Entry 0 = `08AE` (from `hook_59ad4`, pre-existing; index 0 is
transparent for sprites). Populated from F230, stable through gameplay.

## 13. FG/sprite line-3 validation
Gameplay FG cells still reference line 3 (`605E…`), now POPULATED. Sprites/Rastan draw from line 3 (bank 51),
now populated. (Geometry/SAT not touched.)

## 14. Selector/staging regression
`a5@0x10A8=0x0000` (0159); `staged_fg=2016` (0160); `staged_bg=2048` (0154); command `a5@0x137A=0x00FF` (0158) —
all intact at F540/560/580.

## 15. Minimal visual validation
Runtime/state only: line 3 populated → gameplay FG and sprite/Rastan colors now have a non-black palette line
(previously black). BG (line 2) unchanged/visible. Title/story/BEST5/item-page frontend IDENTICAL to 0160
(title represented=15, staged_bg/fg=560/66, line3=0 at title — bank 51 unused there). No new fatal address
(clean 30s trace + two deterministic runs). **User to confirm pixels.**

## 16. Collision observation (unchanged)
Collision WRAM `0xFF1E00` nz=0 (empty); reader raw `0x0010DE00`; 2/3/0 active. Deferred.

## 17. Build artifact path/SHA/size/counter if built
`dist/rastan-direct/rastan_direct_video_test_build_0161.bin`, SHA
`79c2c01610e153b813deef590de8a8cd631e02a80b2c59111ff2929b86f04a8f`, 1,581,220 B, counter 161. PASSING CANDIDATE
(preserved). Builds 0142-0160 not overwritten.

## 18. Rejected candidate path/SHA if applicable
None — the candidate passed. (The prior no-op routing candidate was reverted earlier, before this task.)

## 19. Open/Closed Issues Impact
OPEN-017 advanced (build-verified): the gameplay sprite/FG palette (Genesis CRAM line 3 = arcade bank 51) is now
populated. Root: arcade bank 51 is written only to the sprite-palette source buffer (via `0x3BA64`), never to
palette RAM; `hook_3ba64` (replacing `0x3BA64`) skipped the source-buffer write. Fix stages the bank-51
source-buffer write directly to staged line 3. Remaining OPEN-017: visible-pixel confirmation; collision
producer; player/Rastan sprite geometry. Not closed.

## 20. KNOWN_FINDINGS impact
**KF-043** (build-verified): arcade sprite palette bank 51 is produced only into the sprite-palette source buffer
(`0x10D600` region, Genesis a5@0x1600=`0xFF1600`) by `0x3BA64`, then memcpy'd to arcade palette RAM `0x200660`
(unmapped on Genesis). `hook_3ba64` replaced `0x3BA64` but only staged the `0x200000` palette-RAM writes, so
Genesis CRAM line 3 was black. Fix: stage the bank-51 source-buffer writes (a0∈`0xFF1660..0xFF167F`) directly to
staged line 3 (Build 0161).

## 21. Architecture compliance
CONFIRMED. Single bounded `palette_hooks.s` change + paired coverage constant; no opcode_replace change; no NOP/
RTS scaffolding; no forced/hardcoded colors; no second palette system; uses `staged_palette_words` +
`vdp_commit_palette`; did not touch collision, selector, FG_SRC mapping, sprite/SAT geometry, PC090OJ, player/
camera/scroll, D00298, Exodus, audio, or lines 0-1. Candidate preserved (not deleted). Arcade is the reference.
