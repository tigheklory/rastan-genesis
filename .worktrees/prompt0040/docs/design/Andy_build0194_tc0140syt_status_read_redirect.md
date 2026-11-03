# Andy/Opus — Build 0194: TC0140SYT Sound Status-Read Redirect (Exodus READY Lock Fix)

**Date:** 2026-07-16
**Type:** Bounded opcode-replace fix + validation.
**Baseline:** Build 0193 `ee3d236e…`. **Produced Build 0194** `09f21d404e86aa0cf0aca888b603dfe9d0f6fd6a7b8ef3b189f7fd786207d19e`, size 1,582,876, counter 194, GATE_PASS.

## Root cause (from KF-055)
The arcade sound-command dispatcher busy-waits on the TC0140SYT master-status register:
```
3a33e: bsr 0x3f29c          ; 3f29c: moveb #4,0x3E0001 (port sel); 3f2a4: moveb 0x3E0003,%d0 (status)
3a342: btst #0,%d0          ; busy bit
3a346: bne 0x3a33e          ; wait while busy
```
Genesis has no TC0140SYT; 0x3E0003 is out-of-physical-ROM cartridge space (ROM 1.58 MB; addr ~3.87 MB) → emulator open-bus. MAME/BlastEm read bit 0 = 0 → loop exits → gameplay. Exodus reads bit 0 = 1 → spins forever at 0x3A342/0x3A346. The existing spec suppressed the TC0140SYT *writes* but left the status *read* unredirected.

## Fix — single 6-byte opcode replacement (no NOP, no branch change)
- **Arcade PC:** 0x03F0A4 (runtime 0x0003F2A4)
- **Original:** `1039 003E 0003` = `moveb 0x3E0003,%d0` (read TC0140SYT status)
- **Replacement:** `0280 FFFF FFFE` = `andi.l #0xFFFFFFFE,%d0` (force bit 0 clear = sound ready)
- **Replacement type:** inline immediate (Option A), byte-exact 6→6, single instruction.

**Why this shape:** the status subroutine 0x3F29C has exactly ONE caller (0x3A33E), which uses only bit 0 of d0 (`btst #0`) and overwrites d0 immediately after the wait (`moveb %fp@,%d0`). So clearing only bit 0 is sufficient and safe; `andi.l #0xFFFFFFFE` preserves all other bits (faithful to the original byte-move's register footprint), needs no padding, uses no NOP, and does not touch the loop, the branch, A5, SR, or the stack. The TC0140SYT port-select WRITE at 0x3F09C (`moveb #4,0x3E0001`) is left intact (dropped harmlessly on Genesis).

## Structured metadata
`specs/rastan_direct_remap.json` opcode_replace += one entry (arcade_pc 0x03F0A4, original/replacement bytes, full note incl. build number, PCs, action, returned behavior, reason, Exodus proof, relationship to write suppression, safety, Z80 follow-up). `expectations.opcode_replace_count` 151→152. CANONICAL_OPCODE_REPLACE_COUNT 151→152 in both gate scripts. Regenerated `rastan_direct_patch_manifest.json` + `address_map.json` (both now carry the Build 0194 note).

## Validation
- **ROM:** runtime 0x3F2A4 = `0280fffffffe` (was `1039003e0003`). ✓
- **MAME loop behavior:** at 0x3A342, D0 bit 0 = clear 3/3, set 0/3; 0x3A346 bne not taken; 0x3A348 reached 3/3 → **loop deterministically exits.** ✓
- **MAME gameplay:** reached (represented=17). VINT rate 0.771 (Build 0193 was 0.769) → **no regression;** Build 0193 family-apply optimization + Build 0192 duplicate gates intact.
- **Visuals (screenshots states/traces/exodus0193/snap94/):** title RASTAN/TAITO ✓; READY ROUND 1 ✓; Stage 1 gameplay: Rastan left/coherent barbarian, BG/FG/palette correct ✓.
- **BlastEm:** not run by Andy; the fix makes the exit deterministic (bit 0 always clear) independent of open-bus, so BlastEm (already passing) stays correct.
- **Exodus:** Andy cannot run Exodus. The fix removes the open-bus dependency entirely, so the loop must exit in Exodus too. See checklist.

## Exodus checklist for Tighe (confirm the fix)
1. Break at **0x0003A342** (`btst #0,%d0`). Inspect **D0** low byte → **bit 0 = 0** (was set/spinning before).
2. Branch at **0x0003A346** (`bne`) → **not taken**.
3. Next PC → **0x0003A348** (`moveb %fp@,%d0`) → dispatcher sends the command and returns.
4. READY proceeds to Stage 1 (no spin).
(If you still see a spin at 0x3A342 after this build, capture D0 + the byte at 0x3F2A4 — it should read `0280fffffffe`, not the old read.)

## Not touched
Loop and branch untouched; no A5/READY/VBlank/palette change; PC090OJ/PC080SN unchanged; Build 0192 suppression + Build 0193 family-apply optimization intact; mirror default 256. TC0140SYT write suppression unchanged.
