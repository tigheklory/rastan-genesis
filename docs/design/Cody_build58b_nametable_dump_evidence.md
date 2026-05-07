# Cody Build 58b Nametable Dump Evidence

Date: 2026-05-05  
Type: Evidence-only continuation (read-only dump)

## Scope
- Primary target: OPEN-001 Hypothesis B (Plane A/B nametable index offset)
- No source/spec/tool/build/ROM modifications
- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0057.bin`
- Canonical SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`

## Dump Capture

Stable-state capture used for required range set:
- Emulator: MAME `genesis`
- Dump directory: `states/dumps/build58b_20260505_175403/`
- Capture metadata (`meta.txt`):
  - `reason=pc_3A19x`
  - `frame=900`
  - `pc=0x03A198`
  - `sr=0x2700`
  - `ipm=7`
  - `sentinel_029A=0x0000`
  - `sentinel_02AA=0x0000`

Required dump files and sizes:
- `vram_0000_1fff.bin` = 8192 bytes
- `vram_c000_cfff.bin` = 4096 bytes
- `vram_e000_efff.bin` = 4096 bytes
- `vram_f000_ffff.bin` = 4096 bytes
- `vdp_regs_00_17.txt` = 228 bytes

Additional late-state confirmation run:
- `states/dumps/build58b_20260505_175922/meta.txt`
  - `frame=5000`
  - `pc=0x03A194`
  - `sr=0x2700`
  - `s029A=0x0000`
  - `s02AA=0x0000`
- Same four VRAM ranges were also all-zero in this run.

## VDP Registers (0x00..0x17)

From `states/dumps/build58b_20260505_175403/vdp_regs_00_17.txt`:
- `R00=0x04`
- `R01=0x74`
- `R02=0x38`
- `R03=0x3C`
- `R04=0x06`
- `R05=0x7C`
- `R06=UNKNOWN`
- `R07=0x00`
- `R08=UNKNOWN`
- `R09=UNKNOWN`
- `R10=0xFF`
- `R11=0x00`
- `R12=0x81`
- `R13=0x3F`
- `R14=UNKNOWN`
- `R15=0x02`
- `R16=0x01`
- `R17=0x00`
- `R18=0x00`
- `R19=0x40`
- `R20=0x01`
- `R21=0x82`
- `R22=0xB0`
- `R23=0x7F`

## Plane B Nametable Decode (`VRAM 0xC000..0xCFFF`)

Source: `states/dumps/build58b_20260505_175403/vram_c000_cfff.bin`

Cell decode fields:
- tile index = bits `10..0`
- h-flip = bit `11`
- v-flip = bit `12`
- palette line = bits `14..13`
- priority = bit `15`

First row cells 0..15:
- All words are `0x0000`
- Decoded per cell: `index=0`, `hflip=0`, `vflip=0`, `pal=0`, `prio=0`

First column cells (0, 64, ..., 1984):
- 32/32 cells decoded to index `0`

Statistics across all 2048 cells:
- min index: `0`
- max index: `0`
- zero-index cells: `2048`
- cells `< 0x14`: `2048`
- cells `>= 0x14`: `0`

## Plane A Nametable Decode (`VRAM 0xE000..0xEFFF`)

Source: `states/dumps/build58b_20260505_175403/vram_e000_efff.bin`

First row cells 0..15:
- All words are `0x0000`
- Decoded per cell: `index=0`, `hflip=0`, `vflip=0`, `pal=0`, `prio=0`

First column cells (0, 64, ..., 1984):
- 32/32 cells decoded to index `0`

Statistics across all 2048 cells:
- min index: `0`
- max index: `0`
- zero-index cells: `2048`
- cells `< 0x14`: `2048`
- cells `>= 0x14`: `0`

## Cross-Reference to Build 58 Baseline

Build 58 baseline established:
- preload scene tile base starts at slot `0x14`
- LUT lookups are active and aligned for checked samples

Observed dump state here:
- both Plane A and Plane B nametable ranges are all-zero
- low VRAM sentinel words used in prior screenshot evidence (`0x029A`, `0x02AA`) are both `0x0000` in this capture

Result:
- This dump state is non-diagnostic for validating a constant nametable index offset.
- The specific `+0x14` vs no-offset Hypothesis B test cannot be decided from all-zero nametables.

## Hypothesis B Classification

- Classification: **INSUFFICIENT**
- Reason: required dump was captured, but both target nametable ranges were uniformly zero in capture state; no real tile-index stream was present to classify offset.

## Next Evidence Needed

To resolve Hypothesis B decisively:
- capture the same five ranges at a timestamp where nametable words in `0xC000..0xEFFF` are non-zero in the active offset-graphics state (same canonical ROM), or
- produce an equivalent read-only dump from the Exodus state where offset graphics are visibly present.

No fix proposed or implemented in this task.
