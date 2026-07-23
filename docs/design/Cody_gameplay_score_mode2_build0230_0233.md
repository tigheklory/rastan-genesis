# Cody - Gameplay Score Mode 2 Build 0230-0233

**Date:** 2026-07-22  
**Agent:** Cody  
**Build produced:** Build 0233  
**Baseline:** Build 0232, `dist/rastan-direct/rastan_direct_video_test_build_0232.bin`, SHA256 `e4dc57ec056f9a02f8db8ee6d6305797700b1b648c295a819b326a39ba935cf0`, size `1,588,176`  
**Output ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0233.bin`, SHA256 `43c385fe0f1e6e20cddcdde898c14363c6f9e68bfb03a9c76496188a7d18723d`, size `1,588,388`  
**Counter:** `233`  
**Config:** `RASTAN_GAMEPLAY_HUD_SPRITES=2`, `PC090OJ_MIRROR_RECORDS=256`

## Scope

This task corrects only the gameplay HUD Mode 2 P1 score/`1UP` representation introduced across Builds 0230-0232. It preserves the Build 0232 white HUD glyph path and the KF-066 PC090OJ bank-`0x36` line-0 lizard palette carrier route.

No PC080SN map loading, cave/rope/collision/death behavior, lizard positioning, enemy damage, non-HUD sprite mapping, palette algorithm redesign, audio, or rejected Build 0228 scene-4 work was intentionally changed.

No numbered builds were deleted or overwritten; Builds 0230, 0231, 0232, and 0233 all remain present under `dist/rastan-direct/`.

## Phase 0

Relevant priors:

- KF-036: arcade A5 work-RAM pointers map to Genesis by subtracting `0x0010C000` and adding Genesis A5 `0x00FF0000`.
- KF-047/KF-048/KF-053/KF-061: PC090OJ object records are arcade-owned state represented through the Genesis helper path; do not hardcode sprites or bypass the object/SAT pipeline.
- KF-066: gameplay HUD sprite suppression frees line 0/SAT pressure, and PC090OJ bank `0x36` must continue through the shared line-0 carrier/cache/reassert path for lizard colors.
- Build 0231/0232 log entries: Mode 2 kept P1 score/`1UP` only; Build 0232 added white HUD glyph residency and forced SAT line 3 for retained HUD records.

Task classification: **EXTENDING** existing OPEN-017 / gameplay rendering work.  
Open issues touched: OPEN-017 primary, OPEN-001 context.  
Closed issues touched: none.  
Contradiction of CONFIRMED/STRONG findings: **NONE**.  
Architecture compliance: **CONFIRMED**. The fix leaves arcade score state intact and only changes Genesis helper-side PC090OJ representation.

## Static Producer Facts

The packed-BCD score producer is the original arcade PC090OJ numeric renderer at `arcade_pc 0x0003B802`. `build/rastan-direct/address_map.json` maps it to `runtime_genesis_pc 0x0003BA02`, where the current translated ROM uses the helper `genesistan_pc090oj_hook_score_digit_3b802`.

The function's local table starts at `arcade_pc/data 0x0003B87E`, entry size `10` bytes. The mode-0 P1 score entry describes:

| Field | Value |
|---|---:|
| Count | `6` digits |
| Y | `0x0010` |
| PC090OJ destination | `HW_ADDRESS 0x00D00108` |
| Arcade score source | `arcade_workram 0x0010C11E` |
| Genesis score source | `Genesis-WRAM 0x00FF011E` |

The Genesis source is `0x00FF011E`, not `0x00FFC11E`, because arcade work-RAM pointers are relative to A5 base `0x0010C000` per KF-036.

The P1 score is packed BCD:

| Digit | Source nibble | Meaning |
|---|---|---:|
| 100000s | `Genesis-WRAM 0x00FF011E` high nibble | digit 0 |
| 10000s | `Genesis-WRAM 0x00FF011E` low nibble | digit 1 |
| 1000s | `Genesis-WRAM 0x00FF011D` high nibble | digit 2 |
| 100s | `Genesis-WRAM 0x00FF011D` low nibble | digit 3 |
| 10s | `Genesis-WRAM 0x00FF011C` high nibble | digit 4 |
| 1s | `Genesis-WRAM 0x00FF011C` low nibble | digit 5 |

For score `008100`, the bytes are `FF011E=00`, `FF011D=81`, `FF011C=00`; the visible score should therefore be `8100`, with only the two highest zero digits hidden.

The static setup block at `arcade_pc 0x0003B8C6` uses table data at `arcade_pc/data 0x0003B9B0` to initialize P1 setup records `28..36`:

| Record | Purpose | Code | X |
|---:|---|---:|---:|
| 28 | score digit setup | `0x002A` | `0x0030` |
| 29 | score digit setup | `0x002A` | `0x0028` |
| 30 | score digit setup | `0x002A` | `0x0020` |
| 31 | score digit setup | `0x002A` | `0x0018` |
| 32 | score digit setup | `0x002A` | `0x0010` |
| 33 | score digit setup | `0x002A` | `0x0008` |
| 34 | `1` label | `0x0039` | `0x0040` |
| 35 | `U` label | `0x0048` | `0x0028` |
| 36 | `P` label | `0x0046` | `0x0038` |

## Build 0232 Failure Classification

The user's hypothesis was correct in effect: Build 0232 could show only the `81` part of an `8100` score because the low-order digit records were not surviving as score records.

The score storage was not the bug. Runtime probing of Build 0232 showed the authoritative score bytes at `Genesis-WRAM 0x00FF011E..0x00FF011C` were correct, while the wrong address window `0x00FFC11E..0x00FFC11C` remained zero.

The actual representation failure was record ownership. Build 0232's Mode 2 retained original setup records `28..36`, but gameplay object population reuses much of that range. At gameplay steady state, records `30..43` were overwritten by gameplay sprite records (`0x03E8..0x03F5` family), leaving only a broken subset of the intended score/label setup. Therefore the failure boundary was the translated Genesis PC090OJ representation record range, not arcade score arithmetic.

## Build 0233 Implementation

Build 0233 adds a gameplay-Mode-2-only projection helper in `apps/rastan-direct/src/pc090oj_hooks.s`:

- `.Lpc090oj_mode2_project_p1_hud` runs only when `RASTAN_GAMEPLAY_HUD_SPRITES == 2` and `genesistan_current_scene_id == PC090OJ_SCENE_GAMEPLAY_ID`.
- It reads the authoritative packed-BCD P1 score bytes from `Genesis-WRAM 0x00FF011E..0x00FF011C`.
- It projects six score digits into helper-owned PC090OJ records `0..5`, preserving the original digit significance order: 100000s, 10000s, 1000s, 100s, 10s, 1s.
- It hides leading zeros with `word1=0x0110` but forces a zero-score floor of `00` by making records `4` and `5` visible when all six digits are zero.
- It projects `1UP` into helper-owned PC090OJ records `6..8` using codes `0x0039`, `0x0048`, `0x0046`.
- The native emit pass admits records `0..8` during gameplay Mode 2 and suppresses records `9..45`, avoiding the Build 0232 clobbered range.
- White HUD tagging now applies to records `0..8` only. Tagged HUD records still flow through the normal object decode, tile-residency, SAT staging, tile-DMA, and commit-time palette fixup path.

This is not a direct SAT hardcode and does not change arcade scoring state.

## White HUD Path

The existing Build 0232 white glyph path is preserved:

- `tools/translation/build_pc090oj_hud_white.py` maps every opaque nibble in the HUD glyph slice to palette index `2`.
- `apps/rastan-direct/src/pc090oj_assets.s` includes the generated `build/pc090oj_hud_white_genesis.bin` as `rastan_pc090oj_hud_white`.
- Runtime tagged HUD records force SAT palette line `3` through `pc090oj_sat_force_line`.
- Palette probe confirmed line 3 index 2 is pure white: `0x0EEE`.

## Verification

Build command:

```bash
source tools/setup_env.sh && RASTAN_GAMEPLAY_HUD_SPRITES=2 make -C apps/rastan-direct release
```

Result: **PASS / GATE_PASS**. Boot guard passed pre/post patch. Opcode replace count remains `216`; canonical coverage was updated to `0x183CA4` for the additional production helper bytes.

### Build 0233 Artifact

| Item | Value |
|---|---|
| ROM | `dist/rastan-direct/rastan_direct_video_test_build_0233.bin` |
| SHA256 | `43c385fe0f1e6e20cddcdde898c14363c6f9e68bfb03a9c76496188a7d18723d` |
| Size | `1,588,388` bytes |
| Counter | `233` |
| Rolling ROM | `apps/rastan-direct/dist/rastan_direct_video_test.bin` byte-identical by SHA |

### Standard Smoke Trace

`states/traces/rastan_direct_video_test_build_0233_mame_30s_20260722_145909/`

- `frames=1798`
- `fg_cwindow_live count=0`
- Unique unmapped memory addresses: none

### Injected `008100` Score Trace

`states/traces/build0233_score_mode2_validation_20260722_150015/score_mode2_probe.log`

At `frame=406`, scene `01`, state `2/3/0`, the trace shows `score_ff011c=008100` and object records:

| Record | Word1 | Code | X | Meaning |
|---:|---:|---:|---:|---|
| 0 | `0x0110` | `0x002A` | `0x0008` | hidden 100000s zero |
| 1 | `0x0110` | `0x002A` | `0x0010` | hidden 10000s zero |
| 2 | `0x0010` | `0x0032` | `0x0018` | visible `8` |
| 3 | `0x0010` | `0x002B` | `0x0020` | visible `1` |
| 4 | `0x0010` | `0x002A` | `0x0028` | visible `0` |
| 5 | `0x0010` | `0x002A` | `0x0030` | visible `0` |
| 6 | `0x0010` | `0x0039` | `0x0040` | visible `1` label |
| 7 | `0x0000` | `0x0048` | `0x0028` | visible `U` label |
| 8 | `0x0000` | `0x0046` | `0x0038` | visible `P` label |

The same records persist at `frame=900`. SAT entries for the retained HUD records have forced line `03` and `attr=E...`, proving the line-3 white path is applied.

### Zero-Score Floor Trace

`states/traces/build0233_score_mode2_zero_validation_20260722_150100/score_mode2_probe.log`

At `frame=500`, scene `01`, state `2/3/0`, score `000000` projects records `0..3` as hidden leading zeros and records `4..5` as visible zero digits. `1UP` records `6..8` are present. The first HUD SAT entries have `force=03`.

### Palette Line Probe

`states/traces/build0233_palette_line3_probe_20260722_150258/palette_line3_probe.log`

At `frame=500`, scene `01`, the line probe reports:

```text
line3_index2=0EEE
line3=08AE 0000 0EEE 08AE 044A 0246 0008 0006 00EE 006E 0080 0060 0888 0666 0040 000E
```

This confirms the forced line-3 HUD glyph index `2` resolves to pure white `0x0EEE`.

### KF-066 / Bank-0x36 Carrier Verification

`apps/rastan-direct/out/pc090oj_config.inc` confirms `RASTAN_GAMEPLAY_HUD_SPRITES=2`. `apps/rastan-direct/out/symbol.txt` includes `vdp_reassert_bank36_line0`, `pc090oj_sat_force_line`, and `rastan_pc090oj_hud_white`; the source guard is `RASTAN_GAMEPLAY_HUD_SPRITES != 1`, so Mode 2 uses the same bank-`0x36` carrier route as accepted HUD-suppression mode rather than Build 0228/diagnostic fallback behavior.

No rejected scene-4 after-rope implementation is active: `GAMEPLAY_STRIP_SRC_HI` remains `0x00010B1C` and no `SCENE_GAMEPLAY_AFTER_ROPE` symbol is present in active source/tool output.

## Files Changed

Intentional source/tool changes:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Generated/build artifacts include updated `apps/rastan-direct/out/*`, `build/rastan-direct/*`, `build/genesis_postpatch.disasm.txt`, `build/rom_inventory.json`, and the numbered Build 0233 ROM. Documentation/log changes:

- `docs/design/Cody_gameplay_score_mode2_build0230_0233.md`
- `AGENTS_LOG.md`

## Open / Closed Issues Impact

Open issues touched: OPEN-017 primary, OPEN-001 context.  
New issues opened: none.  
Issues closed: none.  
Issues intentionally deferred: PC080SN map/cave/rope/collision/death, lizard positioning, enemy damage, non-HUD sprite mapping, audio, rejected Build 0228 scene-4, OPEN-015.

## KNOWN_FINDINGS Impact

Option A: no new finding to index. This is a bounded gameplay-HUD Mode 2 correction and preservation of existing KF-066 behavior, not a new durable architecture finding.

## User Test Scope

USER MUST VERIFY visually:

1. Start Stage 1.
2. Reach the first lizard-men and confirm their colors remain correct.
3. Confirm the gameplay HUD shows the retained white `1UP` and P1 score.
4. Confirm score `8100`-style values display all significant digits and trailing zeros, not just `81`.
5. Confirm no unrelated gameplay behavior regressed from Build 0232/accepted current flow.

## STOP

STOP triggered: **NO**.
