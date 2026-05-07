# Cody Build 58c Visible-State VRAM Acquisition

Date: 2026-05-06  
Type: Evidence-only continuation (state-validation gate first)

## Scope
- Target: OPEN-001 Hypothesis B (nametable index offset)
- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0057.bin`
- Canonical SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`
- No source/spec/tool/build/ROM modifications

## §1 State Validation Gate

Validation source attempted first: **MAME** (`genesis` driver), canonical `0057.bin`.

Validation artifact:
- `states/dumps/build58c_20260506_132350/validation.txt`

Timestamps (frame-based at 60 fps equivalent):
- `sec_5` (frame 300)
- `sec_10` (frame 600)
- `sec_20` (frame 1200)
- `sec_30` (frame 1800)
- `sec_60` (frame 3600)
- `sec_120` (frame 7200)

Sentinel results at every timestamp above:
- `VRAM 0x029A = 0x0000`
- `VRAM 0x02AA = 0x0000`
- `VRAM 0x02C0 = 0x0000`
- `VRAM 0xC000 (Plane B first cell) = 0x0000`
- `VRAM 0xE000 (Plane A first cell) = 0x0000`
- `VRAM 0x0280..0x037F` non-zero words = `0`
- `VRAM 0xC000..0xCFFF` non-zero words = `0`
- `VRAM 0xE000..0xEFFF` non-zero words = `0`
- Gate decision per sample line: `gate=FAIL`

CPU/SR context sampled:
- frame 300: `PC=0x071A48`, `SR=0x2600`, `IPM=6`
- frames 600..7200: `PC` remains in `0x03A19x`, `SR=0x2700`, `IPM=7`

### §1.2 Gate Decision
- **Validation gate result: FAILED**
- Reason: all sentinel conditions remained blank/zero at all required timestamps.

## §1.3 Alternate Evidence Paths After MAME Failure

Path (b) Exodus dump/export:
- Status: **NOT AVAILABLE in this environment**
- Evidence: no `exodus` executable present in PATH (`which exodus` returned none).

Path (c) manual Exodus Memory Editor capture:
- Status: **NOT AVAILABLE to this agent in current session**
- Existing repository screenshots are historical captures and do not provide newly captured 5-range synchronized bytes for this task's required ranges.

Final source for Phase 2 dump:
- **NONE (STOP)**  

Conclusion:
- MAME did not reproduce a validated visible-state capture for OPEN-001 evidence at canonical `0057.bin` across the required timestamps.
- This is a meaningful negative finding for OPEN-003 context (MAME vs Exodus state divergence).

## §2 Dump Capture
- Skipped due to failed validation gate.
- No 5-range Build 58c nametable dump files were produced.

## §3/§4 Nametable Decode
- Not run (gate failed).

## §5 Hypothesis B Classification
- Status: **N/A (gate failed)**  
- Build 58b Hypothesis B remains **INSUFFICIENT**; Build 58c did not yield a validated visible-state byte capture to resolve it.

## Next Evidence Required
- Acquire validated visible-state bytes from Exodus-side capture path (dump/export or synchronized manual Memory Editor capture) for:
  - `VRAM 0x0000..0x1FFF`
  - `VRAM 0x0C000..0x0CFFF`
  - `VRAM 0x0E000..0x0EFFF`
  - `VRAM 0x0F000..0x0FFFF`
  - `VDP regs 0x00..0x17`

No fix proposed or implemented.
