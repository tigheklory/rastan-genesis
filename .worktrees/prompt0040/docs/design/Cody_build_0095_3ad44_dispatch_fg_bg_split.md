# Cody - Build 0095 3AD44 Dispatch FG/BG Split

**Date:** 2026-06-23
**Type:** Implementation + verification
**Scope:** Repair `genesistan_hook_3ad44_dispatch` so arcade attract/title page-fill calls to `0x03AD44` route BG C-window fills to BG staging and FG C-window fills to FG staging. No new boundary clear. No runtime scaffolding. No bookmark cycle. No exception/input/BG logo/sprite/palette/scroll work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (FG -> Plane A, BG -> Plane B), KF-011 (arcade VBlank owns progression; Genesis services hardware), KF-013 (text dispatch inside VBlank is expected), KF-029 (Build 0094 FG cell composition fixed), KF-030 (canonical coverage invariant semantics), KF-031 (stale object caution), OPEN-001, OPEN-016, and OPEN-015 as do-not-touch context. No CONFIRMED/STRONG contradiction detected.

Source documents loaded:
- `docs/design/Cody_original_arcade_attract_page_replacement_runtime.md`
- `docs/design/Cody_build_0094_fg_clear_boundary_pin.md`
- `docs/design/Andy_build_0094_3ad44_dispatch_hook_body.md`

## Baseline Facts

Original arcade attract/title page replacement clears both planes by calling arcade `0x03AD44` twice:
- BG: `A0=0x00C00100`, `D1=1900`, `D0=0x00000020`
- FG: `A0=0x00C08100`, `D1=1900`, `D0=0x00000020`

Genesis runtime `0x03AF44` is opcode-replaced to `JSR genesistan_hook_3ad44_dispatch`. The current hook correctly recognizes tilemap C-window addresses, but `.Lhook_3ad44_tilemap` unconditionally calls `genesistan_hook_tilemap_bg_fill`. That helper accepts only `0x00C00000..0x00C03FFF`, stages into `staged_bg_buffer`, and sets `bg_row_dirty`; therefore the FG call at `0x00C08100` is rejected and does not clear `staged_fg_buffer`.

## Pre-Declared Implementation Delta

Files expected to change:
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `docs/design/Cody_build_0095_3ad44_dispatch_fg_bg_split.md`
- `AGENTS_LOG.md` (append at end only)

Implementation form:
- Split `.Lhook_3ad44_tilemap` on `A0`/`D2` at `0x00C08000`.
- BG tilemap addresses below `0x00C08000` continue to call the existing `genesistan_hook_tilemap_bg_fill` unchanged.
- FG tilemap addresses at/above `0x00C08000` call a new mirror helper `genesistan_hook_tilemap_fg_fill`.
- `genesistan_hook_tilemap_fg_fill` mirrors the BG helper but uses:
  - base/range: `ARCADE_PC080SN_CWINDOW_BASE_FG` (`0x00C08000`) plus `ARCADE_PC080SN_CWINDOW_BYTES` (`0x4000`)
  - staging target: `staged_fg_buffer`
  - dirty flag: `fg_row_dirty`
- The existing `0x100` C-window offset and `D1=1900` extent are preserved because the helper walks from the original `A0` and decrements the original count exactly as the BG helper does.

Measured byte delta before edits:
- Dispatcher split: current tilemap dispatch is `bsrw genesistan_hook_tilemap_bg_fill` + `bras finish` = `0x06` bytes. New split is `cmpi.l #0x00C08000,%d2` + `blo.s bg` + `bsrw fg_fill` + `bras finish` + `bsrw bg_fill` + `bras finish` = `0x14` bytes. Dispatcher delta: `+0x0E`.
- New FG fill mirror helper assembled in isolation to `0xD6` bytes.
- Total declared ROM/code growth: `+0xE4` bytes.

Canonical invariant pre-declaration:
- `opcode_replace` patched-site count remains `95`.
- `total_genesis_bytes_covered` changes from `0x17CB58` to `0x17CC3C` (`+0xE4`).
- Address-map effect: helper-local growth after the opcode-replaced arcade blob shifts subsequent Genesis-native helper symbols by `+0xE4`; no opcode_replace entry is added, removed, or resized.

STOP rule: if the release build observes any invariant/opcode_replace/address-map delta other than the above, do not adjust gates and do not rerun the release target in this task.

## Implementation Status

Continuation completed: Build 0095 produced and bounded runtime validation passed for the scoped FG/BG split.

## Implementation Applied

Applied the predeclared source edits:
- `apps/rastan-direct/src/pc090oj_hooks.s`: `.Lhook_3ad44_tilemap` now splits at `0x00C08000`; below that routes to `genesistan_hook_tilemap_bg_fill`, at/above that routes to `genesistan_hook_tilemap_fg_fill`.
- `apps/rastan-direct/src/tilemap_hooks.s`: added `genesistan_hook_tilemap_fg_fill`, mirroring the BG helper with FG base `0x00C08000`, `staged_fg_buffer`, and `fg_row_dirty`.
- `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py`: predeclared canonical coverage updated to `0x17CC3C` with opcode_replace count left at `95`.

## Single Release Invocation

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **STOP before numbered artifact production**.

The postpatch canonical invariant gate failed:

```text
RuntimeError: Build 0029 invariant failure: expected total_genesis_bytes_covered=0x17CC3C and opcode_replace patched_site count=95; got total_genesis_bytes_covered=0x17CC40 opcode_replace patched_site count=95. build_context=canonical.
```

Observed delta:
- Expected/predeclared coverage: `0x17CC3C` (`0x17CB58 + 0xE4`)
- Observed coverage: `0x17CC40` (`0x17CB58 + 0xE8`)
- Difference from predeclaration: `+0x04`
- opcode_replace count: `95` as expected

Per the prompt STOP rule, the invariant gates were **not** adjusted to the observed value and the release target was **not** rerun.

## Artifact / Counter Status

- Pre-build counter: `94`
- Post-failure counter: `94` (unchanged)
- Numbered Build 0095 artifact: **not produced**
- Runtime validation: **not run** (no produced Build 0095 ROM)

## Verification Status

Static source verification before release confirmed the intended source shape, but produced-ROM verification and runtime validation could not proceed because the single allowed release invocation stopped at the invariant gate.

## STOP

STOP triggered: **YES** — observed `total_genesis_bytes_covered=0x17CC40` differed from the predeclared `0x17CC3C`. No gate adjustment, no second release invocation, no runtime validation.

## Continuation After Invariant STOP

### Revised Invariant Policy

The earlier STOP was caused by an over-strict exact-byte predeclaration. The continuation prompt authorizes category-based reconciliation if the build-measured value is explained and remains within the approved native/helper-growth category.

Category review:
- Source/helper files only: YES (`pc090oj_hooks.s`, `tilemap_hooks.s`)
- opcode_replace count remains `95`: YES
- No opcode_replace site added/removed/resized: YES
- Native/helper region grows; subsequent helper addresses shift: YES
- Address-map change limited to wrapper/native-helper growth: YES
- No unrelated lifecycle hooks touched: YES

### +0x04 Cause

One-line cause: the source/object instruction growth is exactly the approved `+0xE4`, but both edited assembler `.text` sections are 4-byte aligned and now end on halfword boundaries, so the linker inserts `+2` padding after `tilemap_hooks.o` and `+2` padding after `pc090oj_hooks.o` (`+0x04` total).

Evidence:
- Baseline object sizes from `HEAD`: `tilemap_hooks.o .text = 0x0FF0`, `pc090oj_hooks.o .text = 0x0950`.
- Edited object sizes: `tilemap_hooks.o .text = 0x10C6` (`+0xD6`), `pc090oj_hooks.o .text = 0x095E` (`+0x0E`). Raw source/object growth = `+0xE4`.
- Both sections declare `Algn 2**2`; edited sizes `0x10C6` and `0x095E` require `+2` bytes each to align the next linked section. Build-measured coverage therefore becomes `0x17CB58 + 0xE8 = 0x17CC40`.

### Constants Corrected

Updated the already-touched invariant constants from `0x17CC3C` to the build-measured, category-verified `0x17CC40` in:
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

### Continuation Release Build

Command run exactly once after constant reconciliation:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: PASS.

Build output:
- Build number: `0095`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0095.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `273508a23ddd7b37e10e7ba4a7355f78e95bbe539ba3145b4e844b59ace53ef6`
- Not byte-identical to prior `558c88b3...`: YES
- Build counter advanced: `94 -> 95`
- Release trace artifact: `states/traces/rastan_direct_video_test_build_0095_mame_30s_20260623_203249/`

### Static Produced-ROM Verification

Generated symbols/disassembly confirm the intended split:
- `0x03AF44`: `jsr 0x716F0` (`genesistan_hook_3ad44_dispatch`)
- `genesistan_hook_tilemap_bg_fill = 0x70574`
- `genesistan_hook_tilemap_fg_fill = 0x7064A`
- `genesistan_hook_3ad44_dispatch = 0x716F0`
- `genesistan_pc090oj_hook_init_priority_3ad84 = 0x717A0`

Produced dispatch excerpt:
```asm
71754: cmpil #0x00c08000,%d2
7175a: bcss 0x71762             ; BG branch
7175c: bsrw 0x7064a             ; FG fill
71760: bras 0x7179a
71762: bsrw 0x70574             ; BG fill
71766: bras 0x7179a
```

BG path unchanged in produced code:
- `0x70574` still gates `[0x00C00000,0x00C04000)`, uses `staged_bg_buffer` (`0xFF401A`), and sets `bg_row_dirty` (`0xFF4002`).

FG path present in produced code:
- `0x7064A` gates `[0x00C08000,0x00C0C000)`, uses `staged_fg_buffer` (`0xFF501A`), and sets `fg_row_dirty` (`0xFF4006`).

Address-map / relocation guard:
- Manifest `patch_counts`: `opcode_replace_and_rom_opcode_replace = 95`.
- Manifest expected coverage: `0x17CC40`.
- `address_map.json` wrapper segment ends at `0x17CC40`.
- `shift_deltas` remains empty; arcade-copy / patched-site segmentation was not changed by this helper-only edit.
- Absolute references into shifted helper addresses are re-relocated in produced disassembly (`0x03AF44 -> 0x716F0`, dispatch `bsrw 0x7064A` / `bsrw 0x70574`).

### Runtime Validation

Primary validation trace:
- Directory: `states/traces/build_0095_3ad44_fg_bg_split_validation_20260623_203427/`
- Report: `states/traces/build_0095_3ad44_fg_bg_split_validation_20260623_203427/fg_bg_split_validation_analysis.md`
- Crash halt events before validation endpoint: `0`
- `0x711AE` game-scene cwindow clear events: `0` (unchanged; not used for this attract boundary)

Fill dispatch observed:
- `DISPATCH_3AD44_ENTRY_716F0`: `11`
- `BG_FILL_ENTRY_70574`: `3`
- `FG_FILL_ENTRY_7064A`: `3`
- Captured boundary BG fill: `A0=0x00C00100`, `D0=0x20`, `D1=0x076C` (1900), followed by `1900` BG staging blank writes at post-PC `0x7062C`.
- Captured boundary FG fill: `A0=0x00C08100`, `D0=0x20`, `D1=0x076C` (1900), followed by `1900` FG staging blank writes at post-PC `0x70702`.

Primary boundary FG staging snapshots:
- Before `0x3AC82`: `62` nonzero cells
- After `0x3AC88`: `62` nonzero cells
- Before `0x3ACAE`: `8` nonzero cells
- After `0x3ACAE`: `143` nonzero cells

Interpretation:
- FG prior-page cells blanked before producer: YES (`62 -> 8` before `0x3ACAE`).
- Leading/preserved region remains: YES (`8` retained cells before producer, matching the expected partial-page clear rather than full-buffer clear).
- Pages replace rather than accumulate: YES (`8 -> 143`, not Build 0094's `62 -> 191` additive pattern).
- Producer redraw still executes: YES (`0x3ACAE`, `0x3ACB6`, and `0x3ACF8` all hit once).
- Producer emitted new FG cells: YES (`160` FG writes during `0x3ACB6..0x3ACF8`, `135` nonzero, `25` zero/space cells).

BG non-regression:
- BG fill still fires for the same captured attract boundary (`A0=0x00C00100`, `D1=1900`).
- BG snapshots for this boundary remain `0 -> 0 -> 0 -> 0`, consistent with the already-working BG clear path for this captured page.

Commit-boundary check:
- Directory: `states/traces/build_0095_3ad44_fg_bg_split_commit_after_3acfe_20260623_204048/`
- `0x3ACFE` after state write: `s0=0`, `s2=1`, `s4=2`, `fg_dirty=0x0AAAA100`, `fg_probe=0x001F`.
- Next FG commit entry `0x70182`: hit at `pc=0x70184`, `fg_dirty=0x0AAAA100`, `fg_probe=0x001F`.
- Dump at commit boundary: `143` nonzero FG cells.
- FG committed / reached commit boundary: YES.

Attract-path spot-check:
- Release target's built-in 30s MAME trace completed successfully.
- Bounded debug validation reached the expected producer and commit boundary with no crash halt.
- On-screen/manual visual verification remains for Tighe; this task proves runtime staging/commit boundary behavior, not final visual correctness for BG/logo/sword/game-start/red-fragment.

## Final Continuation Status

STOP continuation accepted: YES.

Implementation safely placeable: YES for this exact repair. The produced Build 0095 runtime now routes the translated arcade attract fill path to both BG and FG staging, preserving the original partial-page clear semantics (`0x100` offset / `D1=1900`) and replacing prior-page FG text before the producer redraws.

OPEN-001 remains open. This task repairs the additive FG text retention mechanism only; it does not address BG/logo/sword/game-start redraw, red fragment, Start/C/A exception, or OPEN-015.
