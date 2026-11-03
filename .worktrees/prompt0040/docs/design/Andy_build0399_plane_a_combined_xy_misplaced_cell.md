# Andy — Plane-A Combined X/Y Misplaced 8×8 Cell — RESOLVED (Build 0399)

**Baseline:** Build 0398. **Counter:** 398 → **399**. Production source changed: **YES** (`tilemap_hooks.s`,
two operand changes). Andy gameplay verification: **NO** (authority: TIGHE). Build 0399 is a **candidate for
Tighe verification**, not a declared fix.

> This supersedes the earlier STATIC-NARROWING STOP version of this document. The investigation history is
> preserved in `AGENTS_LOG.md` (user-driven trace tooling → Exodus VRAM/RAM capture → Case-A proof → static
> root cause). The STOP was correct at the time: the first divergence was not yet proven. It now is.

## 1. Reproduction (from Tighe)
Horizontal-only scroll: clean. Vertical-only: generally clean. **Combined horizontal + vertical** camera
motion (jump off the Segment 2/3 climbable rope with a small horizontal component; jump up/down stepped
terrain; the repeatable **Segment 6** reproduction used for the Exodus capture): intermittently one valid 8×8
terrain cell appears where sky belongs, and scrolling the region out and back self-repairs it.

## 2. Captured first divergence (Exodus, Segment 6, Plane-A base 0xE000, 64×32)
Two isolated misplaced cells, both valid palette-3 terrain tiles dropped into sky (`0x6297`) cells:

| Physical cell | VRAM addr | VRAM (published) | staged_fg_buffer (intended) | Expected |
|---|---|---|---|---|
| row 22, col 46 | 0xEB5C | `0x62D7` | **`0x62D7`** | sky `0x6297` |
| row 28, col 44 | 0xEE58 | `0x6316` | **`0x6316`** | sky `0x6297` |

Staged values read directly from the `staged_fg_buffer` block (0xFF50A0) in Tighe's paused-state 68K RAM.

## 3. Case A proof (publication cleared)
`staged == VRAM` at both cells ⇒ the wrong terrain words were **already in `staged_fg_buffer` before
publication**. The VBlank publisher (`vdp_commit_fg_narrow_strips`) faithfully published the bad staged
state, so it is **not** the first divergence and was **not** modified.

## 4. Failure character → vertical source-row error
Each stray is the **phase-correct** terrain tile for its own column:
- col 46 cycles `…62D3,62E6,62D7,62C3…` (period 4); `62D7` falls on `row%4==2`; stray at **row 22** (`22%4==2`).
- col 44 has `6316` on `row%4==0`; stray at **row 28** (`28%4==0`).

Correct **column**, correct **vertical phase**, wrong (sky) **row** ⇒ a vertical source-ROW error while an
entering horizontal column is generated (not a column-mapping error, not random corruption).

## 5. Proven root cause (static, `tilemap_hooks.s`)
The two horizontal column producers and the vertical row/pan producers use the **same** visible-top
arithmetic (`neg; +8; &0x1FF; >>3; &0x3F`) but read the vertical scroll from **different timing domains**:

- Horizontal `genesistan_hook_tilemap_plane_a_selector0_native` (was line 261) and
  `…selector12_native` (was line 401): read **`staged_scroll_y_fg`** (0xFF409E) — a one-stage-latent Genesis
  copy written by the arcade staged-scroll writer (arcade_pc `0x055AB4`).
- Vertical `…pan_publish_entering_rows_up/down` (lines 499/535 → `.Lplane_a_visible_top_from_scroll_d0`):
  read the **live** arcade `ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5)` = `a5@0x10B0`.

During combined motion the live value leads the staged copy by the per-frame vertical delta, so an entering
column resolves its rows **one cell out of phase** with the resident rows the vertical path just streamed →
a phase-correct terrain tile lands in the adjacent sky row. This explains H-only clean / V-only clean /
combined broken, the single isolated cell per entering column, and self-repair on re-entry.

## 6. The fix (two source-operand changes)
In **both** horizontal producers, the vertical-scroll source operand only:

```
-    move.w  staged_scroll_y_fg, %d0
+    move.w  ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5), %d0
```

Now both axes derive their vertical window from the one live arcade-owned vertical front. `%a5` is
`0x00FF0000` at both sites (selector0: preserved across `fg_boundary_transition_step`, which saves only
`d0-d3/a0/a4`; selector12: no intervening call). The neg/+8/9-bit mask/`>>3`/row-wrap arithmetic is
unchanged.

**Explicitly unchanged:** `resolve_plane_a_cell` (Build-0353 ring-unwrap), `vdp_commit_fg_narrow_strips`,
`vdp_commit_scroll` (VSRAM output still uses `staged_scroll_y_fg` — the rendered scroll value and the
producer's world-row decision are different ownership questions), dirty-column/dirty-row mechanics, the
Sonic-style incremental staging, the residency/package system. No full-plane rebuild, no extra row/column
scans, no extra DMA, no runtime terrain/segment/rope special case.

## 7. Performance impact
Lower, not higher. At each of the two sites the operand changes from `move.w (abs32).L` (3 words, ~16 cyc) to
`move.w d16(%a5)` (2 words, ~12 cyc): −1 word and ~4 cycles per call, twice per combined-motion frame. No new
per-cell loop, no new per-frame workload. Sonic-style incremental scrolling performance is preserved.

## 8. Build 0399 (mechanical)
- Code-only change; `Test.json` unchanged (snapshot SHA `02d0122a…` identical to Build 0397/0398 input).
- Five-ROM family produced: `rastan_direct_video_test_build_0399{,_c,_d,_do,_s}.bin` (1,756,856 bytes each).
- Gates: **`[canonical=PASS entry=PASS epoch=FAIL]`** (epoch=FAIL is the expected pre-existing Phase-1
  seven-epoch condition on recent builds; ROM numbered and preserved).
- Canonical SHA: `8227d3458af5d9b51fe858e92bfd94492c4dbf1266eba97023ba580858dbc0ba`.
- Boot guards PASS before and after postpatch. The staged-scroll writer (arcade `0x055AB4`) relocated
  correctly (`jsr @0x073A9C → 0x055B44 [shifted]`).

## 9. Protected work preserved
No change to: Build 0391 (Phase-2 Plane-A population / first waterfall), 0395 (scene/ROUND-READY), 0397
(overlap package 8 / seg10→11), 0398 (overlap package 9 / record 12→13), horizontal-only and vertical Plane-A
scrolling, Flying-Demon whole-death, sprite/collision/palette/scene-loading behavior.

## 10. OPEN-028 relation
Not proven same. OPEN-028 (first-arrival stale sky names) may share the "stale cell during streaming" family,
but this defect has a distinct combined-H+V trigger and self-repairs; left separate unless Build-0399 testing
shows the same mechanism.

## 11. Status
**Build 0399 candidate — TIGHE MUST VERIFY.** Not declared FIXED on build/static evidence. Tighe test targets:
(A) Segment 2/3 climbable-rope combined-X/Y, (B) Segment 6 repeatable repro, (C) ascending/descending stepped
terrain, (D) horizontal-only control, (E) performance vs Build 0398.

---
Production source changed: **YES (tilemap_hooks.s, 2 operands)** · ROM built: **YES (0399 family)** ·
Counter after: **399** · User-visible status: **CANDIDATE, pending Tighe verification**.
