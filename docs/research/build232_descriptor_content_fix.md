# Build 232 Descriptor Content Fix

## 1) Change Made
- Implemented direct opcode-path descriptor-content updates for the live title/logo producer family rooted at `0x03AAF2 -> 0x05A174` via `specs/startup_title_remap.json`.
- Kept active ownership on renderer-consumed buffers and extended producer-side content path:
  - active target retargets for block-B builder bases/slots (`0x059F9A`, `0x059FDE`, `0x059FFC`, `0x05A014`, `0x05A032`, `0x05A04A`, `0x05A068`, `0x05A080`) to `0xFF0170/78/80/88`
  - active target retargets for block-A builder bases (`0x05A0AE`, `0x05A1EC`) to `0xFF11B2`
  - attr writes updated to nonzero (`0x05A11A`, `0x05A13E`, `0x05A188`, `0x05A1AC`, `0x05A1D0`: `0x0000 -> 0x0080`)
  - producer return path extension at `0x059F90` to execute additional descriptor builder calls before `RTS`.
- Build artifact produced in mode-1 path and copied to requested name: `dist/Rastan_232.bin`.

## 2) Exact Descriptor Content Before vs After
- Before (Build 231, proven):
  - block A (`0xFF11B2`) was all zero (`0/144` nonzero bytes)
  - block B (`0xFF0170`) held template-only records (`w0=0x0080`, `w1/w2/w3=0`) with minimal nonzero footprint (`4/32` bytes)
- After (Build 232 run window):
  - block A remains all zero (`0/144` nonzero bytes)
  - block B remains minimally/non-drawably populated (`3/32` nonzero bytes), with only residue-like nonzero in one entry (`w2/w3`) and no stable full drawable tuples.

## 3) Execution Proof
- Build command used:
  - `source tools/setup_env.sh && make -C apps/rastan release RASTAN_EXCEPTION_DUMPER_MODE=1`
- Runtime probe (START injected, 20s, `dist/Rastan_232.bin`):
  - started-path confirmed: `started=true`, `current_screen=0x00000004`
  - renderer still active: sprite renderer hit stream remains present (`0x20060C` family activity seen in probes)
  - title state seed remains live in run (`A5+0x0000/+0x0002/+0x0004` observed as `0001/0000/0000`).

## 4) Active Descriptor Population Proof
- Probe artifacts:
  - `/tmp/build232_descriptor_content_probe.txt`
  - `/tmp/build232_descriptor_content_probe2.txt`
  - `/tmp/build232_sprite_probe.txt`
- Observed write ownership in window:
  - block A writes: `106` total, all zero writes (`nonzero_writes=0`)
  - block B writes: `20` total, `nonzero_writes=3` (not full drawable tuples)
- Field-level snapshots:
  - block A: `word0=0 word1=0 word2=0 word3=0`
  - block B: one entry with nonzero `word2/word3`, but no consistent nonzero `word0/word1/word2/word3` tuple set for visible logo composition.

## 5) Visual Result Description
- Classification: **no change**.
- Title/logo sprites were not validated as meaningfully visible from descriptor evidence in this 20s started-path run window.

## 6) Remaining Issues
- Live active buffers remain mostly clear/template-level in this window despite direct-path content edits.
- Current started-path probes do not show a confirmed transition to fully populated drawable title/logo descriptor tuples in block A/B.
- Next blocker remains inside the descriptor-content generation chain after ownership correction, not in launcher handoff or text-dispatch remap.
