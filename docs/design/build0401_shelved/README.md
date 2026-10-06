# Build 0401 — SHELVED OWNERSHIP PROTOTYPE

**Status: SHELVED OWNERSHIP PROTOTYPE — behaviorally playable, architecture useful,
performance intentionally temporary.** Tighe verified Build 0401 plays correctly but runs
~1/3–1/2 the speed of Build 0400, because it intentionally added a temporary full Plane-A +
Plane-B WORK→READY snapshot copy every frame. NOT rejected — shelved pending the
hardware-emulation cleanup, after which the ownership work can be reapplied cleanly.

## Preserved here (nothing needs reconstruction from memory)
- `build0401_ownership_source.patch` — exact source diff Build 0400 → 0401 for the four modified
  files (`vdp_comm.s`, `dma.s`, `tilemap_hooks.s`, `pc090oj_hooks.s`). Reapply with
  `git apply docs/design/build0401_shelved/build0401_ownership_source.patch` on the 0400 source.
- `build0401_hashes.txt` — sha256 of the four 0401-modified sources, the patch, and the 0401 ROM.
- ROM family preserved: `dist/rastan-direct/rastan_direct_video_test_build_0401{,_c,_d,_do,_s}.bin`
  (counter 401, canonical SHA aa6876b78540af6effcad9bee078dd3264cd753d2605098c0655033a04007b65).
- Full design + implementation notes + mechanical validation:
  `docs/design/Andy_build0401_immutable_frame_ownership.md` (locked decisions + IMPLEMENTED section).
- AGENTS_LOG.md Build 0401 entry.

## Architecture preserved (reapply after cleanup)
WORK / READY / DISPLAYED generation ownership; `work_/ready_/displayed_generation` counters;
READY publisher conversion (all six `vdp_commit_*` read READY); DISPLAYED sprite-residency concept
(`displayed_sprite_tile_resident_code`); `frame_promote_work_to_ready`; `frame_adopt_residency`;
no-new-READY hold gate. Build-0400 scheduling was retained in 0401 (worker still in IRQ6).

## Why shelved before continuing
The full two-plane snapshot (~40K cyc/frame) is a temporary ownership-isolation device. Before
re-applying ownership + doing the scheduling cut, we first audit and remove the remaining real
PC090OJ/PC080SN hardware-emulation remnants in Build 0400 (see the restore + audit task).
