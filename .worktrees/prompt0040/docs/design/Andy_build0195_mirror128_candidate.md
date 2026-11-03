# Andy/Opus — Build 0195: Build 0194 + PC090OJ Mirror 128 (Candidate)

**Date:** 2026-07-17
**Type:** Config candidate (mirror cap only). No code change vs Build 0194.
**Baseline:** Build 0194 `09f21d40…` (256). **Produced Build 0195** `758b7c26d95de8ead72e1daddcf977108316432c117470aca7d9ce58b4b4723d`, size 1,582,876, counter 195, GATE_PASS.

## What changed
Only `PC090OJ_MIRROR_RECORDS = 128`, applied via the existing configurable mirror mechanism:
```
make release PC090OJ_MIRROR_RECORDS=128
```
- No hand-edited assembly constants; the value flows through the generated `out/pc090oj_config.inc` (KF-048).
- **Makefile default remains `?= 256`** (unchanged) — the 256/reference build is still the default; 128 is this candidate artifact only.
- Reusable resize mechanism intact (256/128/80/… all still buildable).
- All Build 0175/0178/0180/0192/0193/0194 behavior carried forward unchanged.

## Repo state at end
- Rolling dist = Build 0195 (128).
- Makefile default = 256.
- `out/pc090oj_config.inc` = `PC090OJ_MIRROR_RECORDS, 128`.
- opcode_replace count = 152 (unchanged; mirror count is orthogonal to opcode_replace).

## Validation (MAME)
| Check | Result |
|---|---|
| GATE_PASS | yes |
| generated config | 128 |
| opcode_replace count | 152 |
| Build 0194 TC0140SYT fix present | yes — 0x3F2A4 = `0280fffffffe` (`andi.l #-2,d0`) |
| READY sound busy loop (0x3A342) | D0 bit 0 clear 3/3, set 0/3; 0x3A348 exit 3/3 → **loop exits (Exodus-safe)** |
| Title | RASTAN/TAITO renders |
| Story/READY | ROUND 1 READY renders |
| READY → Stage 1 | reached (no lock) |
| Rastan position/composition | LEFT, coherent barbarian (5 player SAT slots = arcade-faithful records 120,121,124,125,126) — **no 80-record right-side corruption** |
| BG/FG/palette | correct (sky/mountains/terrain/palette intact) |
| Build 0192 duplicate suppression | intact (hook_41dae/45dfa gates present) |
| Build 0193 family_apply fast path | intact |
| represented / SAT chain / player slots | 12 / 12 / 5 |
| VINT-service rate (F≥560) | **0.963 (~58 Hz)** vs Build 0194/256 ≈ 0.771 |
| new lock/crash before gameplay | none |

## Notable observation — 128 cap further improves the rate
The mirror scan + process cost scales with the record count (KF-052/053/054). Progression:
- Build 0181 (256, pre-0193): 0.477; (128): 0.569.
- Build 0194 (256, with 0193 family-apply fix): 0.771.
- **Build 0195 (128, with all fixes): 0.963 (~58 Hz).**
Capping to 128 roughly halves the per-VBlank shadow scan (128-record vs 256-record) and the candidate/process work, pushing the effective update rate close to 60 Hz — combining the KF-053 family-apply saving with the smaller mirror. 128 preserves the canonical player anchor (120..121) and core cluster (120..126), so Rastan renders correctly (screenshots states/traces/build0195/snap/).

## Safety (128 vs the 80 floor)
Prior findings (KF-049): 80/96/112/116/118/120 unsafe (drop the player anchor 120..121); 122 is the measured floor; 128 preserves 120..127. This build confirms 128 is safe: Rastan left/coherent, no flip/blob corruption. No regression versus Build 0194/256 except the expected slightly-lower represented/SAT counts (the >=128 records are dropped) and the higher VINT rate.

## Structured metadata
The mirror count is not an opcode_replace; its owner is the Makefile variable → generated `pc090oj_config.inc` (KF-048), plus the build_counter/rom_inventory recording Build 0195. No opcode_replace/manifest change needed for the mirror cap; no new registry created. The TC0140SYT redirect (opcode_replace 0x03F0A4) is unchanged and present.

## Candidate status
Build 0195 is a candidate; accepted build unchanged. Build 0194 and Build 0195 artifacts both preserved in dist/rastan-direct/. If Tighe finds any visual regression vs Build 0194/256, preserve 0195 as rejected diagnostic and keep the default at 256.

## Not touched
No code optimization, graphics, sound, VBlank, gameplay, palette, PC080SN, or TC0140SYT change. Only the mirror record count.
