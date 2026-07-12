# Andy — Build 0161: Gameplay FG/Sprite Palette CRAM Ownership — STOP (Classification C after finish attempt), NO BUILD
<!-- §1-19: initial audit (STOP-B). §20: bank-51 owner finish attempt -> STOP-C (owner found: arcade sprite-bank chunk load dropped; Genesis fix needs bank->line offset mapping, not trivially bounded). -->


## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `73492c6`, clean. Accepted Build 0160 ROM
`e9243ff028cdcd8f3776a51ffa54ea8438f1489bca61fd607bff0c268983e697`, counter 160, opcode_replace 137,
coverage 0x182090. **No source/spec/tool/ROM edit, no build.** OPEN issue: OPEN-017.

## 2. User palette observation
Exodus/BlastEm gameplay CRAM appears near-black except a light color; BG mountain/sky loads but sprite/FG
palette lines do not; FG cells are staged (Build 0160) but visually wrong; Rastan sprite absent. Directs a
palette/CRAM ownership audit before collision or sprite geometry.

## 3. Expected Genesis CRAM ownership
Palette producers (`palette_hooks.s`) map arcade palette **banks** → Genesis CRAM **lines**: arcade bank 0→line0,
bank 1→line1, bank 48→line2, bank 51→line3. `vdp_commit_palette` (`vdp_comm.s:284`) DMAs all 64 words of
`staged_palette_words` (0xFF609E) → CRAM every VBlank when `palette_dirty` is set. Genesis tilemap cells encode
the palette line in bits 13–14.

## 4. Palette producer audit
- `genesistan_palette_hook_59ad4` (0x718ce): arcade sprite-palette updater; bank 0x33(51)→line3; reads a
  `(a0)+` source with `0xFFFF`="no change" markers, converts, **writes `move.w d1,(a1)+`** (advances a1 only on
  write).
- `genesistan_palette_hook_3ba64` (0x71996): main arcade palette writer; banks 0,1→lines 0,1; bank 48→line2;
  bank 51→line3; **positional** write `move.w d2,0(a1,d1.w)`.
- `genesistan_palette_hook_45dae` (0x71962): copy from arcade 0x200000 (plane banks) → staged.
- `genesistan_palette_hook_03ab00` (0x7193e): single entry.
All set `palette_dirty`. Buffer `staged_palette_words`=0xFF609E; `palette_dirty`=0xFF4000.

## 5. Palette commit audit
`vdp_commit_vsync` calls `vdp_commit_palette` when `palette_dirty` (then clears it). Commit copies all 64
staged words to CRAM addr 0 verbatim. Runtime: `palette_dirty` set **124×** through gameplay F=560 → commit runs.
Only `vdp_commit_palette` writes CRAM in normal operation (crash-handler CRAM write excluded). So **CRAM ==
`staged_palette_words`** after commit.

## 6. FG cell palette-line proof
FG_SRC staging uses `FG_PLANE_ATTR_HI = 0x00030000` → (via `genesistan_pc080sn_attr_lut`) Genesis palette
**line 3**. Runtime sample (Build 0160, F=560, staged_fg row0): `605E/605F/603C/6000…` — all **palette line 3**
(bits 13–14 = 11).

## 7. Sprite/SAT palette-line proof
Arcade sprite banks 48,51 → Genesis lines 2,3. Gameplay sprites (incl. Rastan) draw from line 3 (bank 51). Since
line 3 is black (§8), sprite/Rastan colors are black — matching "Rastan sprite absent." (SAT geometry not
inspected; palette-line only, per scope.)

## 8. Build 0160 CRAM runtime dump (F=560, gameplay 2/3/0)
`staged_palette_words` (== CRAM):
- **line 0 nz=0** (BLACK) — arcade bank 0 source is populated (`7BDE 001E 29D0…`).
- **line 1 nz=0** (BLACK).
- **line 2 nz=15** (populated: `0642 0644 0868 0668…`) — arcade bank 48.
- **line 3 nz=1** (`08AE 0000×15`) — arcade bank 51 source is fully populated (`0842 739C 429E 2154…`, 15 colors).
Cell ownership: **staged_bg cells → line 2** (`4226…`, bits=10) → BG uses the populated line 2 → **BG appears**;
**staged_fg cells → line 3** (black) → **FG invisible**. Arcade gameplay banks 0/1/48/51 are ALL populated
(`arc_pal.txt`); only Genesis line 2 survived.

## 9. First proven break in palette chain
**Genesis palette line 3 (referenced by gameplay FG and sprites/Rastan) is never populated beyond entry 0**,
while its arcade source (bank 51) holds 15 colors. Line-3 nonzero-count over time (`gen_l3hist.txt`): 0 → **1 at
F=195**, then **constant at 1** through F=600 — it is never scrambled-from-populated; it is simply **never
filled**. The producer that writes line 3 during gameplay is `hook_59ad4` (PC 0x071928), which repeatedly writes
**only `line3[0]=0x08AE`** from ROM source `a0=0x059B38` (`gen_line3.txt`); `hook_3ba64`'s bank-51→line3 branch
did **not** fire in the traced run. So the arcade bank-51 → line-3 population path is **missing/non-running** on
Genesis gameplay — a producer-ownership gap, not a commit or scene-clear problem.

**Confirmed adjacent bug (not proven to be the cause):** `hook_59ad4` write is `move.w d1,(a1)+` (advance only on
write), whereas the arcade original `0x59ad4` writes **positionally** — `move.w d3,(a1)` (0x59b0a) then
`addq #2,a1` **unconditionally** (0x59b14), so `0xFFFF`-skipped entries keep their existing color and a1 still
advances. The Genesis `(a1)+` **compacts** scattered updates. This is a real correctness defect, but since line 3
is never populated at all (not scrambled), fixing `(a1)+` alone is not proven to fill line 3 — the missing
bank-51 gameplay load is the dominant unknown.

## 10. State-causality answers
1. **What state should exist?** Gameplay FG (line 3) and sprite (lines 2,3) cells should reference CRAM lines
   holding the converted arcade bank-48/51 colors.
2. **Which code should create it?** Arcade bank-51 writes should flow through a palette hook that populates
   staged line 3, and `vdp_commit_palette` (which runs) should load it.
3. **Why not?** The commit runs and line 2 (bank 48) is populated, but **line 3 (bank 51) is never filled** —
   the arcade bank-51 gameplay population does not reach staged line 3 (the hook that fires, `hook_59ad4`, only
   writes entry 0 from a single-entry source; `hook_3ba64`'s bank-51 branch doesn't fire). Owner of the bank-51
   gameplay load path (which arcade routine, and whether Genesis hooks it to line 3) is **not proven**.

## 11. Readiness classification: **B** (CRAM line black proven; producer/commit owner not proven) — STOP
The referenced CRAM line (3) is proven black; FG and sprite palette-line usage (line 3) is proven; the commit is
proven to run and to own line 2 correctly. But the **producer owner** that should populate line 3 from arcade
bank 51 during gameplay is **not conclusively proven** — line 3 is never filled (not scrambled), so it is a
missing/non-running producer path, and the confirmed `(a1)+` compaction bug in `hook_59ad4` is not proven to be
the cause (its sources only carry entry 0). A fix now would be speculative (fixing `(a1)+` may be a no-op for the
black line; forcing colors is forbidden). **Not A.** STOP per "producer/commit/mapping owner cannot be proven."

## 12. Exact source change if built
NONE (STOP).

## 13. Build 0161 CRAM validation if built
N/A (no build).

## 14. Minimal visual validation
Not run (no build). Observed state: BG (line 2) populated/visible; FG + sprites (line 3) black.

## 15. Collision observation (unchanged)
Collision WRAM `0xFF1E00` empty; reader raw `0x0010DE00`; unrelated to palette. Deferred.

## 16. Regression validation
N/A (no build). No accepted build modified.

## 17. Open/Closed Issues Impact
OPEN-017 advanced: the "gameplay palette near-black" is root-located to **Genesis CRAM line 3 never being
populated** (arcade bank 51 → line 3 path missing/non-running in gameplay), which blacks out gameplay FG (line 3)
and sprites/Rastan (line 3). BG appears because BG cells reference the populated line 2 (bank 48). Palette commit
and line-2 ownership are correct. A confirmed adjacent `hook_59ad4` `(a1)+` compaction bug exists (vs arcade
positional) but is not proven to be the cause. Next: prove which arcade routine populates bank 51 during
gameplay and whether/where Genesis hooks it to staged line 3 (and re-evaluate the `(a1)+` fix). Not closed.

## 18. KNOWN_FINDINGS impact
Option A — no new finding indexed (analysis; owner not yet build-verified). Candidate durable finding once
proven: "gameplay FG (FG_PLANE_ATTR_HI→line3) and sprites reference Genesis CRAM line 3 = arcade bank 51, which
is not populated during gameplay." Also flags the `hook_59ad4` `(a1)+`-vs-arcade-positional defect.

## 19. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME (Build 0160 +
arcade `rastan`) + static source/disasm; arcade is the reference. Did not touch collision, `0x0010DE00`, reader,
selector, FG_SRC mapping, sprite/SAT geometry, PC090OJ, mode/stage/player/camera/scroll, D00298, Exodus, audio;
did not hardcode colors or force a palette line.

---

## 20. Bank-51 Producer Owner — Finish Attempt (append; STOP C, no build)
Baseline unchanged (Build 0160, counter 160, opcode_replace 137). Arcade trace `arc_b51.txt`.

**Arcade bank-51 (0x200660) writers during gameplay (F179–307):**
- **PC=0x03A2D4 ×16 (F=190): the FULL LOAD** — generic memcpy `0x3A2D0` (`movew (a0)+,(a1)+`, d0 words) copies
  WRAM `a0=0x10D662` → palette RAM `a1=0x200660`, writing all 16 entries = the 15 colors (`0842 739C 429E…`).
- **PC=0x059B0E ×118: incremental** — the `0x59AD4` routine, updates only `b51[3]<-429E` (a0=0x059938 ROM).
So the **full bank-51 palette owner is the generic memcpy `0x3A2D0`**, not `0x59AD4` (which only pokes one entry).

**Genesis mapping:**
- `0x3A2D0` is **intact/unhooked** on Genesis (`0x3A4D0`, identical `movew (a0)+,(a1)+`) → writes to **unmapped
  `0x200660`** → dropped. (Source `0x10D662` is also a raw arcade-WRAM literal → ROM on Genesis.)
- The one hooked `0x3A2D0` caller is `hook_45dae` (arcade `0x045DB8`, `jsr 0x3a2d0`, **d0=64 words** = a 0x80-byte
  4-bank chunk). Its gate `cmpa.l #0x00200000,%a1; bne .L45_done` accepts **only the bank-0 chunk**
  (`a1==0x200000` → banks 0–3 → staged lines 0–3, frontend). The **sprite-bank chunk** (`a1=0x200600`, banks
  48–51) is **rejected** by the gate → banks 48–51 never reach staged. `hook_45dae` also writes staged
  **sequentially from the line-0 base** (`a2=staged_palette_words`), so it has no bank→line offset for a
  non-bank-0 chunk.

**Exact defect:** the arcade sprite-bank palette load (banks 48–51 → Genesis lines 2,3) is dropped on Genesis:
the generic memcpy path (`0x3A2D0`) is unhooked (writes unmapped `0x200660`), and the hooked chunk-copy
(`hook_45dae`) rejects everything except the bank-0 chunk and cannot address lines 2,3 (sequential from line 0).

**Why not a trivially-bounded fix (Classification C):** widening `hook_45dae`'s gate alone would make the
sprite-bank chunk write staged **lines 0–3** (sequential from the line-0 base) → **corrupt** the BG/plane lines.
A correct fix needs a **bank→staged-line offset mapping** (bank 48→line2, 51→line3) inside `hook_45dae` (or a
new dedicated sprite-bank hook), plus source-addressing correctness and frontend regression proof — beyond a
one-line change and beyond this VERY-LOW-budget session. Not A (owner is not `0x59AD4`; the `(a1)+` defect is
not the cause — the full load never reaches Genesis at all). **STOP.**

**Next (dedicated build):** add/extend a palette hook so the arcade sprite-bank chunk (`a1=0x200600`, banks
48–51) converts to staged **lines 2,3** at the correct offset (bank_index→line, entry offset preserved),
committed by the existing `vdp_commit_palette`. Validate line 3 gets 15 nonzero colors; no forced colors; no
frontend regression. The `hook_59ad4` `(a1)+`→positional fix is a separate, lower-priority correctness cleanup.
