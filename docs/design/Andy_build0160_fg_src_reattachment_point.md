# Andy — Build 0160: Gameplay FG_SRC Reattachment Point (Analysis Only, No Build)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `382dd65`, clean. Accepted **Build 0159** ROM
`14138b825fa0dcbfea52d9a519574b615e11722ad41e73a0b56752d4f75b905a`, counter 159, opcode_replace 137.
**No source/spec/tool/ROM edit, no build.** KNOWN_FINDINGS touched: KF-042 (selector relocation, Build 0159).
OPEN issue: OPEN-017.

## 2. User visual correction
Acknowledged: gameplay FG was **never** visibly correct before Build 0159 either. This task does NOT frame the
work as restoring a known-good FG layer; it finds where the existing FG_SRC staging should ATTACH under the
corrected arcade-equivalent selector. Build 0159's selector fix (`a5@0x10A8=0x0000`) is accepted as the correct
upstream state and is not to be undone.

## 3. Build 0155 FG_SRC old attachment
`genesistan_hook_tilemap_fg` (0x703EA), gameplay path (tilemap_hooks.s:291–345), gated by `SCENE_GAMEPLAY_ID`.
It was reached from the arcade **FG branch** of the tilemap dispatch (arcade `0x55990`, opcode_replaced to
`jsr genesistan_hook_tilemap_fg`), which only fired because the (buggy) selector `a5@0x10A8=0x80` routed the
dispatch to the FG branch. The block reconstructs FG cells from the FG_SRC ROM model
(`FG_SRC_BASE_GEN`/`FG_SRC_STRIDE`, seg×row) and routes each cell through `genesistan_hook_tilemap_fg_fill`.

## 4. Build 0159 corrected selector effect
With `a5@0x10A8=0x0000` (BG), the dispatch takes the **BG branch** (arcade `0x55968` →
`jsr genesistan_hook_tilemap_plane_a`) for 100% of Stage-1 passes (histogram `0x0000 ×83`). The FG branch is
never taken, so `genesistan_hook_tilemap_fg` is not called during gameplay → the FG_SRC staging does not run
(gameplay `staged_fg` nonzero = 12, vs BG 2048). Confirmed at runtime
(`states/traces/build_0160_fg_reattach/gen_reattach.txt`).

## 5. Current Build 0159 Stage 1 hook owner
`genesistan_hook_tilemap_plane_a` (0x70248) — the BG hook — is the sole Stage-1 tilemap-pass owner now,
called per BG dispatch (~83×), staging BG into `staged_bg_buffer` (nonzero=2048). It reads
`ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5)` and **`ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` = `a5@0x10A0`**
(tilemap_hooks.s:114–115), runs the scene preamble (`load_scene_tiles`), then walks 16 BG descriptors advancing
`a5@0x10A0` by 0x400 each, and writes `a5@0x10A0` back on exit (line 272).

## 6. Hook input comparison
The FG_SRC staging block's **only external input is `a5@0x10A0`** (tilemap_hooks.s:294,
`ARCADE_PC080SN_DEST_BG_OFFSET`, masked `&0x3FFC` → dcol). Everything else is constants
(`ARCADE_PC080SN_CWINDOW_BASE_FG`, `FG_SRC_BASE_GEN`, `FG_PLANE_ATTR_HI`, `FG_PRODUCER_SEG/ROW_COUNT`), ROM reads,
and `genesistan_hook_tilemap_fg_fill` (which preserves d0–d7/a0–a6). It **reads** `a5@0x10A0` but does **not**
write it, and does not touch `a5@0x10A8`.
- **The BG hook has exactly this input** (`a5@0x10A0`, read at line 115). So the FG_SRC block is register/state
  self-contained and can execute inside `genesistan_hook_tilemap_plane_a` without new inputs. **PROVEN.**
- **Open point:** the *value/progression* of `a5@0x10A0` differs between contexts. Old FG-branch context (Build
  0158) presented one dcol sequence; the BG hook advances `a5@0x10A0` itself (runtime samples: dcol
  52,54,56,57,59,61,63,64… during setup F505–512). Whether the BG hook's `a5@0x10A0` progression drives the
  FG_SRC model to the correct FG columns is **not proven** (and Build 0158's FG was not visibly correct).

## 7. Proposed reattachment point
Fold the existing FG_SRC staging block (tilemap_hooks.s:291–345, minus its own `movem`/`rts` frame) into
`genesistan_hook_tilemap_plane_a`, **gated by `SCENE_GAMEPLAY_ID`**, reading the same `a5@0x10A0` the BG hook
already loads, and calling `genesistan_hook_tilemap_fg_fill` per FG cell. Candidate insertion: at BG-hook entry
(reads `a5@0x10A0` once per call → one FG column per call, matching the old per-dispatch granularity — the BG
hook is called ~83× like the old FG hook's ~80×). No new opcode_replace is needed (the arcade FG-branch
opcode_replace at 0x55990 can remain; it is simply not reached — or later removed as cleanup).

## 8. Preservation of a5@0x10A8=0x0000
**Preserved.** The reattached block only reads `a5@0x10A0` and writes `staged_fg` via `fg_fill`; it never
touches `a5@0x10A8` or the pass-sequence pointer. Build 0159's selector fix is untouched.

## 9. Preservation of BG staging
**Preserved.** The FG_SRC block is additive and self-contained: it reads `a5@0x10A0` (does not modify it), uses
`fg_fill` (register-preserving), and writes only `staged_fg_buffer` — disjoint from `staged_bg_buffer`. Folded
at BG-hook entry it runs before the BG descriptor loop and leaves the BG registers to be set up normally. BG
staging (2048) is not disturbed.

## 10. Frontend-path separation
Separate and unaffected. Frontend/non-gameplay scenes use the `.Lfg_not_gameplay` FG path and the BG hook's own
non-gameplay handling, all gated away from the `SCENE_GAMEPLAY_ID` block. Build 0159 already confirmed frontend
intact (title `represented=15`, `staged_bg/fg=560/66` identical to Build 0158). A gameplay-gated reattachment
does not touch frontend.

## 11. State-causality answers
1. **Branch/hook the FG_SRC depended on:** the arcade FG branch → `genesistan_hook_tilemap_fg` (fired only via
   the `a5@0x10A8=0x80` bug).
2. **Why Build 0159 bypassed it:** selector now 0x00 → dispatch takes the BG branch → FG hook not called.
3. **Branch/hook that now owns the Stage-1 pass:** `genesistan_hook_tilemap_plane_a` (BG), ~83× per scene.
4. **Enough inputs to run FG_SRC?** YES for the *input* (`a5@0x10A0` present, block self-contained); the
   *column-mapping correctness* under the BG hook's `a5@0x10A0` progression is unproven.
5. **Proposed reattachment point:** BG-hook entry, gated by `SCENE_GAMEPLAY_ID`, reusing `a5@0x10A0`,
   `fg_fill` per cell.
6. **Pure Genesis-side or alters arcade state?** Pure Genesis-side staging (no arcade state change; no
   `a5@0x10A8`, no `a5@0x10A0` write).
7. **Preserves `a5@0x10A8=0x0000`?** YES.
8. **Preserves BG staging?** YES (additive, disjoint buffer).
9. **Bounded for Build 0160?** Point + input + preservation are bounded; the column-mapping/coverage
   interaction is not yet proven → not a clean A.

## 12. Readiness classification: **C** (hook inputs proven; interaction with BG staging not proven)
The reattachment point (`genesistan_hook_tilemap_plane_a` entry) and its sole input (`a5@0x10A0`) are **proven**
present, and the FG_SRC block is self-contained (preserves the selector and BG staging). What is **not** proven
is the *interaction*: the BG hook's `a5@0x10A0` progression differs from the old FG-branch context, so whether
the FG_SRC model stages the *correct* FG columns under the BG hook is unverified (and the pre-0159 FG was not
visibly correct, so there is no known-good reference to match). Per the task, visual correctness is deferred to
the implementation build — but that unproven interaction keeps this short of a clean A. Not B (inputs ARE
proven). Not D (the FG_SRC staging *should* be reattached — it is the only gameplay FG producer).

## 13. Exact next implementation boundary if ready
A Build 0160 that folds the FG_SRC block into `genesistan_hook_tilemap_plane_a` (gated `SCENE_GAMEPLAY_ID`,
reusing `a5@0x10A0`, `fg_fill` per cell, additive/register-safe), then **validates the staged FG column
coverage/mapping at runtime and visually** (does `staged_fg` return to ~2020 and do the columns correspond to
the intended FG plane?). Because the pre-0159 FG was not visibly correct, the implementation must treat the
column mapping as something to verify, not assume. Must preserve `a5@0x10A8=0x0000` and BG staging (2048) and
not touch collision, `0x0010DE00`, sprites, or the selector.

## 14. Open/Closed Issues Impact
OPEN-017 advanced: the lost gameplay FG_SRC staging (bypassed by Build 0159's correct selector) should reattach
to `genesistan_hook_tilemap_plane_a` — the BG hook already carries the sole required input (`a5@0x10A0`), and a
gameplay-gated, register-safe fold preserves the selector and BG staging. Remaining unknown before a bounded
build: whether the BG hook's `a5@0x10A0` progression maps the FG_SRC model to the correct columns (visual
validation, deferred). Collision remains separately pending. No new issue, none closed.

## 15. KNOWN_FINDINGS impact
Option A — no new finding indexed (an attachment-point analysis, not a durable rule). Related: KF-042 (the
selector fix that removed the old FG-branch trigger).

## 16. Architecture compliance
CONFIRMED. Analysis only — no source/spec/tool/ROM edit, no build; runtime evidence via MAME (Build 0159) +
static source/disasm; arcade program remains the reference. Did not revert Build 0159, did not restore the 0x80
selector, did not touch collision/`0x0010DE00`/reader/sprites/PC090OJ/SAT/palettes/D00298/Exodus/audio/broad
rendering, did not change `a5@0x10A8`.
