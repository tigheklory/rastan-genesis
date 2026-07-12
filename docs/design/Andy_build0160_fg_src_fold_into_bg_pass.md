# Andy — Build 0160: FG_SRC Fold Into Corrected BG Pass

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `884e4e5` (pre-build), clean. Accepted Build 0159 ROM
`14138b825fa0dcbfea52d9a519574b615e11722ad41e73a0b56752d4f75b905a`, counter 159, opcode_replace 137.
Task class: EXTENDING (reattach existing Genesis FG_SRC staging). OPEN issue: OPEN-017.

## 2. Pre-edit verification
- `genesistan_hook_tilemap_fg_fill` (tilemap_hooks.s:647) is `movem.l %d0-%d7/%a0-%a6`-wrapped → fully
  register-preserving. Inputs a0/d0/d1.
- The FG_SRC gameplay block (former tilemap_hooks.s:294–342) reads **only** `a5@0x10A0`
  (`ARCADE_PC080SN_DEST_BG_OFFSET`) as its external pass-position input; everything else is constants
  (`CWINDOW_BASE_FG`, `FG_SRC_BASE_GEN`, `FG_PLANE_ATTR_HI`, seg/row counts), ROM reads, and `fg_fill`. It writes
  only `staged_fg_buffer` (via `fg_fill`); never writes `a5@0x10A0` or `a5@0x10A8`.
- `genesistan_hook_tilemap_plane_a` (BG hook) runs during Stage-1 gameplay under Build 0159 (dispatch 100% BG),
  and reads `a5@0x10A0` at line 115 → the required input is valid at hook entry.
- Frontend/non-gameplay FG uses `.Lfg_not_gameplay` (unchanged) → separate.

## 3. State-causality answers
1. **State that should exist:** selector stays `a5@0x10A8=0` (BG owner); the Genesis FG_SRC model runs from the
   corrected BG pass; `staged_fg_buffer` gets gameplay FG cells; BG staging intact.
2. **Which code should create it:** `genesistan_hook_tilemap_plane_a` should run the FG_SRC staging as an
   additive Genesis-side side effect, gated to `SCENE_GAMEPLAY_ID`.
3. **Why not now:** Build 0155 put FG_SRC in `genesistan_hook_tilemap_fg`, reached only via the FG branch; Build
   0159's selector fix routes to the BG branch, so the FG hook no longer runs during Stage 1.

## 4. Readiness classification: **A** (bounded, input-safe, register-safe, preserves BG/selector)
The FG_SRC body's sole input (`a5@0x10A0`) is present in the BG hook; the staging is factored into a
`movem`-wrapped subroutine so it cannot disturb the BG hook's registers/CCR or `a0` input; it never touches the
selector or BG buffer. Implemented.

## 5. Exact source change (tilemap_hooks.s only; no spec/opcode_replace change)
1. Extracted the former FG_SRC gameplay body into a new `movem`-wrapped subroutine
   **`genesistan_stage_fg_src_column`** (self-contained: `lea 0x00FF0000,%a5`; reads `a5@0x10A0`; stages each FG
   cell via `genesistan_hook_tilemap_fg_fill`; preserves d0–d7/a0–a6).
2. `genesistan_hook_tilemap_plane_a`: after `lea 0x00FF0000,%a5`, added a gate + call —
   `cmpi.b #SCENE_GAMEPLAY_ID, genesistan_current_scene_id / bne.s .Lbg_skip_fg_stage /
   bsr genesistan_stage_fg_src_column / .Lbg_skip_fg_stage:`. Register-safe (subroutine preserves all regs incl.
   the a0 input); BG code unchanged below.
3. `genesistan_hook_tilemap_fg`: gameplay body replaced by `bsr genesistan_stage_fg_src_column` (dedupe); the
   `.Lfg_not_gameplay` frontend path is untouched. (This path is now dead during Stage 1 but harmless.)
Coverage grew 0x182070→0x182090 (+0x20, code added); paired-updated `CANONICAL_TOTAL_GENESIS_BYTES_COVERED` in
`postpatch_startup_rom.py` + `verify_canonical_rom.py`. **opcode_replace count unchanged (137).**

## 6. Static validation
GATE_PASS; boot guard PASS. opcode_replace=137 (unchanged); coverage 0x182090 (intentional); gaps/overlaps
clean. Source diff limited to `tilemap_hooks.s` + the two coverage constants (+ rebuilt out/*.o/.elf/symbol.txt,
rom_inventory). New symbol `genesistan_stage_fg_src_column` @ 0x703F8. ROM SHA
`e9243ff028cdcd8f3776a51ffa54ea8438f1489bca61fd607bff0c268983e697`, size 1,581,200, counter 160.

## 7. Runtime selector validation
- `a5@0x10A8` dispatch histogram = **`0x0000 ×83`** (100% BG) — Build 0159 selector preserved.
- Build 0159 pass-selector relocation intact: `0x505CE = movel #0x0005116B,d0`.
- `genesistan_hook_tilemap_fg` does not regain dominance (dispatch never routes to FG).

## 8. Runtime FG staging validation (Build 0159 → 0160 at F=560, deterministic)
| metric | Build 0159 | Build 0160 |
|---|---|---|
| gameplay `staged_fg` nonzero | 12 | **2016** |
| gameplay `staged_bg` nonzero | 2048 | **2048** (intact) |
| `fg_row_dirty` | (0) | 0x42284229 (dirty rows set) |
| command `a5@0x137A` | 0x00FF | 0x00FF |
FG staging returns to a substantial count (~2016, comparable to Build 0155's ~2020) without damaging BG staging.

## 9. Column-mapping validation — **good enough for Build 0160 acceptance**
1. `a5@0x10A0` progression in the BG hook provides an advancing dcol sequence (per-call), driving one FG column
   per BG call (~83 calls). 2. FG_SRC maps dcol → seg/group/colidx/row exactly as the proven Build 0155 model.
3. **FG column coverage = 63 of 64 columns (1..63)** — broad, not a single stuck column. 4. No wrap/aliasing
   collapse: rows 0..31 populated (`fg_row_dirty=0x42284229`). 5. Sampled cells vary per column
   (`fg[0,1]=605E` code94, `[0,2]=605F` code95, `[0,3]=603C` code60, `[0,4..8]=6000` blank) — **no
   stale/all-one-column overwrite**. The internal mapping is plausible and non-degenerate. **Not claimed as
   visibly correct** (pre-0159 FG was never visibly correct; visible correctness is a separate open question,
   §10).

## 10. Minimal visual validation
Runtime/state only (headless): gameplay FG cells are now staged (staged_fg≈2016, 63-column coverage), BG
(mountain/sky) staging intact (2048). Title/story/BEST5/item-page unchanged (title identical to 0158/0159:
`represented=15`, `staged_bg/fg=560/66`). Whether the staged FG is *visibly* the correct foreground is not
asserted here and needs a pixel-level check (deferred, per the task). Player/Rastan sprite absence unchanged
(out of scope). No new strict-target fatal address (clean 30s trace + two deterministic runs). "Falls/scrolls
into black": the earlier vertical-scroll behavior is unchanged by this staging fold.

## 11. Collision observation (unchanged — not this build)
Collision WRAM `0xFF1E00` still empty (nz=0). Reader still raw `0x0010DE00`. Early `mode=0x0008`/2-4-0 did not
fire within the 820-frame window (timing shifted later by the added setup work; the collision mechanism —
reading ROM garbage — is unchanged; 2/3/0 active from F=532). Collision remains deferred to the collision build.

## 12. Regression validation
- Build 0159 selector relocation intact (`0x505CE = movel #0x0005116B`).
- Build 0158 command-source rebase intact (`0x5122E = movew 0xff0016`; runtime `a5@0x137A=0x00FF`).
- Build 0157 PC090OJ SAT handoff intact (title `represented=15`).
- Build 0156 C08C66 route intact (`0x3D24C = jsr → genesistan_hook_inline_fg_write_3d04c`).
- Build 0152 C08C62 route intact (`0x3A92A = jsr → genesistan_hook_inline_fg_write_3a92a`).
- Build 0155 FG_SRC model accounted for (reattached; staged_fg≈2016). Build 0154 BG staging intact (2048).
- Frontend identical to 0158/0159. Canonical gate PASS; boot guard PASS; 30s trace clean; two deterministic
  MAME runs identical.

## 13. Open/Closed Issues Impact
OPEN-017 advanced (build-verified): the gameplay FG_SRC staging is reattached to the corrected BG pass
(`genesistan_hook_tilemap_plane_a`, gated `SCENE_GAMEPLAY_ID`, reusing `a5@0x10A0`), restoring
`staged_fg`≈2016 with 63-column coverage while preserving Build 0159's selector (`a5@0x10A8=0`) and BG staging
(2048). Remaining OPEN-017 work: (a) confirm the FG is *visibly* correct (pixel check); (b) the still-pending
collision producer/emit + 9-site rebase; (c) player/Rastan sprite absence. Not closed.

## 14. KNOWN_FINDINGS impact
Option A — no new finding (an implementation reattachment of the existing FG_SRC model, not a durable rule).
Related: KF-042 (the selector fix that necessitated the reattachment).

## 15. Architecture compliance
CONFIRMED. Single bounded source change to `tilemap_hooks.s` (extract + gated call), plus the paired coverage
constant. No new opcode_replace; no NOP/RTS scaffolding; no collision emission, no `0x0010DE00` rebase, no reader
patch, no selector change (a5@0x10A8=0 preserved), no sprite/PC090OJ/SAT/mode/stage-controller/player/camera/
scroll/frontend/D00298/Exodus/audio change. Builds 0142–0159 not overwritten; arcade remains the reference.
