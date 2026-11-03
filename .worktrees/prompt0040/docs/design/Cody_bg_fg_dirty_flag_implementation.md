# Cody - BG/FG Dirty Flag Implementation (Build 0033, rastan-direct)

## 1. Summary
STOP condition triggered in Phase 1 per directive rule (`If ANY = NO -> STOP`).

The implementation spec (`docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md`, §16) requires editing functions named `vdp_commit_bg` and `vdp_commit_fg` in `apps/rastan-direct/src/main_68k.s`.

Direct file inspection shows those symbols are not present in the current source. The current code path uses:
- `vdp_commit_bg_strips_if_dirty`
- `vdp_commit_fg_strips_if_dirty`

Because the required target functions do not exist, the requested exact 4-change implementation cannot be executed as written without deviating from the directive.

No source implementation was performed.

## 2. Phase 1 Verification Results
Required files read:
- `AGENTS_LOG.md` (latest entries)
- `docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md` (full)
- `apps/rastan-direct/src/main_68k.s` (full)

### 2.1 Design doc verification
- 4 required changes in §16 identified: YES
  1. Add `.bss` bytes `bg_dirty`, `fg_dirty` alongside `palette_dirty`
  2. Initialize both in `init_staging_state`
  3. Add `tst/beq/clr` guard wrapper in `vdp_commit_bg`
  4. Add `tst/beq/clr` guard wrapper in `vdp_commit_fg`

- `.bss` location of `palette_dirty`: confirmed at `main_68k.s:1146`
- `init_staging_state` `palette_dirty` init location: confirmed at `main_68k.s:947`
- `vdp_commit_tiles_if_dirty` guard pattern location: starts at `main_68k.s:667`

Exact guard instruction sequence (current source):
```asm
vdp_commit_tiles_if_dirty:
    tst.b   tiles_dirty
    beq.s   .Ltiles_done
    [existing commit loop]
    clr.b   tiles_dirty
.Ltiles_done:
    rts
```

- Exact names `vdp_commit_bg` and `vdp_commit_fg` in `main_68k.s`: NOT FOUND
  - Evidence: symbol search returns only `vdp_commit_bg_strips_if_dirty` and `vdp_commit_fg_strips_if_dirty`

### 2.2 Source verification
- `palette_dirty` declared: line `1146`
- `palette_dirty` initialized in `init_staging_state`: line `947`
- `vdp_commit_tiles_if_dirty` guard starts: line `667` (`tst.b tiles_dirty` at line `668`)
- `vdp_commit_bg` begins: NOT FOUND
- `vdp_commit_fg` begins: NOT FOUND
- Current related commit functions:
  - `vdp_commit_bg_strips_if_dirty`: line `684`
  - `vdp_commit_fg_strips_if_dirty`: line `721`
- Confirm neither `vdp_commit_bg` nor `vdp_commit_fg` currently has a guard: NO (functions absent)

### 2.3 Phase 1 confirmation
- Phase 1 complete: NO
- 4 required changes identified: YES
- palette_dirty location confirmed: YES — line `1146`
- init_staging_state location confirmed: YES — line `947`
- guard pattern confirmed: YES — `tst.b / beq.s / ... / clr.b / label: rts`
- vdp_commit_bg location confirmed: NO — line: NOT FOUND
- vdp_commit_fg location confirmed: NO — line: NOT FOUND
- neither function has existing guard: NO (cannot evaluate absent symbols)
- Safe to proceed to implementation: NO

## 3. Exact changes made (required section)
No code changes were made due STOP condition.

## 4. Guard pattern used (required section)
No implementation performed.

Reference guard pattern confirmed in source (`vdp_commit_tiles_if_dirty`):
- `tst.b flag`
- `beq.s done_label`
- commit body
- `clr.b flag`
- `done_label: rts`

## 5. Validation results (required section)
Validation did not run because implementation did not proceed.

- V1 Build verification: NOT RUN
- V2 Disassembly verification: NOT RUN
- V3 MAME trace verification: NOT RUN
- V4 Regression check: NOT RUN

## 6. Regression confirmation
No source changes were applied; no functional regression introduced by this task.

## 7. Expected VBlank budget impact per Andy analysis
Per Andy analysis, intended effect (if implemented as specified in §16) is:
- ~59,268 cycles worst steady-state before gating
- ~200 cycles steady-state after gating

This impact was not realized in this task due STOP condition.

## 8. Next-step impact
Implementation is blocked until directive and current source are reconciled.

Blocking mismatch:
- Directive targets `vdp_commit_bg` / `vdp_commit_fg`
- Current source contains `vdp_commit_bg_strips_if_dirty` / `vdp_commit_fg_strips_if_dirty`

Missing requirement needed to proceed:
- Explicit instruction confirming whether to apply §16 guard changes to the existing `*_strips_if_dirty` functions, or updated source containing the targeted `vdp_commit_bg` / `vdp_commit_fg` symbols.
