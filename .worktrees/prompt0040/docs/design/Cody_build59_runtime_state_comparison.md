# Cody Build 59 Runtime State Comparison

Date: 2026-05-07  
Type: Evidence-only continuation (state-validation gate first)

## Scope
- Target: OPEN-001 transformed symptom and OPEN-003 divergence evidence
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0059.bin`
- ROM SHA256: `1135e1aaa2e2c39d64a8390c024dd8e67a998b53f829f2cd7e4eabea2d02ec23`
- No source/spec/tool/build/ROM modifications

## §1 State Validation Gate (MAME, Build 59)

Validation artifact:
- `states/dumps/build59_runtime_state_20260507_142931/validation.txt`

MAME run artifacts:
- `states/dumps/build59_runtime_state_20260507_142931/mame_stdout.log`
- `states/dumps/build59_runtime_state_20260507_142931/mame_stderr.log`

Sampling schedule (60 fps equivalent):
- `sec_5` (`frame=300`)
- `sec_10` (`frame=600`)
- `sec_20` (`frame=1200`)
- `sec_30` (`frame=1800`)
- `sec_60` (`frame=3600`)
- `sec_120` (`frame=7200`)

Observed values from `validation.txt`:
- `sec_5`: `pc=0x03A198`, `sr=0x2700`, `ipm=7`, `s0020=0x0000`, `s029A=0x0000`, `s02AA=0x0000`, `s02C0=0x0000`, `pB0=0x0000`, `pA0=0x0000`, `nz0000_1FFF=0`, `nzC000_CFFF=0`, `nzE000_EFFF=0`, `gate=FAIL`
- `sec_10`: `pc=0x03A19C`, `sr=0x2700`, `ipm=7`, all sentinels zero, all non-zero counts zero, `gate=FAIL`
- `sec_20`: `pc=0x03A196`, `sr=0x2700`, `ipm=7`, all sentinels zero, all non-zero counts zero, `gate=FAIL`
- `sec_30`: `pc=0x071A48`, `sr=0x2600`, `ipm=6`, all sentinels zero, all non-zero counts zero, script line `gate=PASS` (PC-not-stuck condition only)
- `sec_60`: `pc=0x070610`, `sr=0x2700`, `ipm=7`, all sentinels zero, all non-zero counts zero, script line `gate=PASS` (PC-not-stuck condition only)
- `sec_120`: `pc=0x03A194`, `sr=0x2700`, `ipm=7`, all sentinels zero, all non-zero counts zero, `gate=FAIL`

### Build 59 validation interpretation

For the strategic question ("does MAME reach Exodus active VDP/CRAM state"), Build 59 MAME does **not** reach a validated active visual state in this run:
- VRAM sentinels for populated tile/nametable state remain zero at all six timestamps.
- Non-zero word counts in all sampled VRAM target ranges remain zero at all six timestamps.
- PC briefly leaves `0x03A19x` at `sec_30` and `sec_60`, but no accompanying VRAM-population evidence appears.

Therefore, this capture does not provide a valid populated-state basis for 5-range decode.

## §2 Dump Decision

- Full 5-range dump/decode was **skipped** for this pass.
- Reason: no timestamp showed the required populated-state VRAM evidence; decoding would repeat the prior non-diagnostic all-zero failure mode.

## §3 Composition Classification

- Status: **N/A (state validation failed for active visual-state comparison)**.
- No Plane A/B attribute classification was attempted from this non-populated state.

## §4 OPEN-001 / OPEN-003 Evidence Outcome

- OPEN-001: Build 59 MAME did not yield active populated nametable bytes for composition diagnosis.
- OPEN-003: Divergence remains meaningful post-CLOSED-007; Exodus shows active populated visual state while this MAME run does not produce populated VRAM sentinels.

## Next Evidence Path

- Exodus-side byte capture is now the required path for OPEN-001 composition diagnosis:
  - `VRAM 0x0000..0x1FFF`
  - `VRAM 0x0C000..0x0CFFF`
  - `VRAM 0x0E000..0x0EFFF`
  - `VRAM 0x0F000..0x0FFFF`
  - `VDP regs 0x00..0x17`

No fix proposed or implemented.
