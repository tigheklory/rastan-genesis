# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0132 — R2-S1 L2 palette-content root cause and fix

**Author:** Andy · **Date:** 2026-11-12 · **Baseline:** Build 0566 (0131 Part-1 tile fix accepted by Tighe).
MAME environment-blocked in this sandbox. Tighe's natural-gameplay observation is authoritative.

## 0. Correction of the 0131 Part-2 conclusion
Tighe tested Build 0566 in **natural** gameplay: the L2/L3 tile split is gone (Part 1 accepted), but R2-S1 L2
colours are wrong. This **disproves** my 0131 "direct-start harness artifact" hypothesis — there IS a real
production defect. The error in 0131 was a wrong premise: I claimed the per-stage palette loader writes arcade
**bank 2 for every round**. It does not. Re-derived below.

## 1. Starting state
HEAD `f8b07a84`, branch `rastan-direct-proposal`, counter 566. Preserved 0113–0131 working tree. 0566 tile
fix preserved (confirmed: `gen_pc080sn_plane_b_visual_records.py` unchanged by this task).

## 2. The contradiction, resolved (items 5–8)
- **R1 Plane-B tile `attr&3` = 2; R2 = 3** (measured from `maincpu.bin`). PC080SN `attr&3` selects which of
  the chip's palette banks each Plane-B tile reads: R1 tiles read **bank 2**, R2 tiles read **bank 3**.
- **The per-stage palette loader writes the round's Layer-B palette INTO that same bank.** Proven from the
  retained arcade loader `FUN_00059de8`: at its hook call (`jsr 0x59ad4`, arcade 0x59E06), `D0` (destination
  bank) = `word at 0x59E8C[D5*2 + (round-1)*8]` (returned by `FUN_00059e50`), NOT a constant. Dumped values:

  | round | loop_count (0x59EBC) | Layer-B dest bank (0x59E8C, D5=0) | source (0x59EC8) |
  |---|---|---|---|
  | R1 | 1 | **2** | 0x5DB4E |
  | R2 | 1 | **3** | 0x5DC4E |
  | R3 | 1 | 9 | 0x5DD4E |
  | R4 | 1 | 8 | 0x5DE4E |
  | R5 | 1 | 1 | 0x5DF4E |
  | R6 | 2 | 4 (then 3) | 0x5E04E |

- **So the two hardware domains are the SAME bank namespace:** the loader's destination bank == the tiles'
  `attr&3` bank, per round. R1: palette→bank 2, tiles read bank 2. R2: palette→bank 3, tiles read bank 3. No
  contradiction — my 0131 "bank 2 always" claim was simply wrong (it described only R1). `D0=2` at `0x59AD4`
  is the R1 destination bank, not a round-invariant one.

## 3/4. Original arcade R1-S1 and R2-S1 Layer-B palette chains
```
player_main_update_51090
  -> FUN_00059de8 (gated a5@0x13b0==1, set by FUN_00055c22 at scene/round entry)
       loop (count = 0x59EBC[round-1]):
         FUN_00059e6c: A0 = (0x59EC8[round-1]) + D5*256        (source: R1=0x5DB4E, R2=0x5DC4E)
         FUN_00059e50: D0 = 0x59E8C[D5*2+(round-1)*8]          (dest bank: R1=2, R2=3)
         D1 = a5@0x13ae  ( = 0x5E24E[a5@0x13e], the palette row )
         jsr 0x59ad4  -> genesistan_palette_hook_59ad4
  -> staged_palette_words (Genesis Line) -> VBlank CRAM publication @0x200000
```
Identical mechanism both rounds; only the destination bank (2 vs 3) and source (0x5DB4E vs 0x5DC4E) differ.

## 9. All R2-S1 Layer-B palette writes (execution order)
Round-entry sequence `FUN_00051156` (a5@0x1414==1, counter a5@0x1416):
1. frame 1 → `FUN_0003a0ec`.
2. **frame 0x50** → `FUN_00051190` loads bank 4 (→Line 0, gameplay-rejected) and **bank 3** from source
   0x511DA (a transition/FG palette). (Round counter a5@0x118 is still the previous round here.)
3. **frame 0x70** → sets `a5@0x13b0 = 1`, which triggers `FUN_00059de8` → loads R2 Layer-B palette (bank 3,
   source 0x5DC4E) — the authoritative Layer-B load; last Layer-B write to the bank.
4. frame 0x300 → sequence ends.
Steady R2 gameplay: no further Line-2 writes (water animation touches Line-3 entries 14/15 only).

## 10/11. What the wrong Build-0566 L2 actually is
Because R2's bank-3 Layer-B write is dropped by the Genesis hook (see §13), Genesis Line 2 is never populated
with the R2 palette. It retains the **authored Test-2.0 Line-2 default** installed at scene activation (and/or
a stale earlier value) — consistent with Tighe's bright cyan/yellow screenshot, which is neither the R2
brown/green forest nor R1's palette. **The exact 16 words are not runtime-captured here (MAME blocked); this
is inferred from the drop mechanism. The fix does not depend on the exact stale bytes** — it ensures the R2
palette reaches L2. (If Tighe wants the exact words, a bookmark capture of Line 2 at R2-S1 can confirm.)

## 12. Correct original R2 effective Layer-B colours
The R2 forest palette = arcade source **0x5DC4E** (16 words) loaded into bank 3, converted xBGR→CRAM by the
existing runtime path. Oracle only; NOT hardcoded.

## 13. First proven arcade-vs-Genesis divergence
At `genesistan_palette_hook_59ad4`:
- **R1:** D0=2 → not matched by any special branch → falls through (`d0=2`) → gameplay gate `cmpi #2,d0`
  passes → staged to **Line 2**. Correct.
- **R2:** D0=3 → hits `cmpi.w #3,%d0; moveq #1,%d0` → **Line 1** ([palette_hooks.s](../../apps/rastan-direct/src/palette_hooks.s) bank-3 branch) → gameplay gate `cmpi #2,d0; bne .L59_done` (d0=1≠2) → **REJECTED**. The R2 Layer-B palette never reaches L2.

**Root cause:** the hook only recognised arcade **bank 2** as the Layer-B→Line-2 owner (an R1-only
interpretation, from the Build-0174 "bank 3 = Stage-1 FG → Line 1" assumption). For R2+, the Layer-B palette
arrives in a different physical bank (3, 9, 8, 1, 4) and was misrouted/rejected. (The FG carrier that
originally justified bank 3→Line 1 is dead — `vdp_comm.s:496`, removed Build 0336.)

## 14. Production fix (smallest faithful correction)
`apps/rastan-direct/src/palette_hooks.s` only. Two additions:
1. `genesistan_layerb_bank_by_round: .word 2,3,9,8,1,4` — a mirror of arcade `0x59E8C[(round-1)*4]`
   (bank-**routing** metadata, NOT colour data; verifiable against the ROM).
2. At the hook entry, in the authored gameplay scene (`scene_id==1`): if the incoming arcade bank `D0` equals
   `genesistan_layerb_bank_by_round[a5@0x118 - 1]`, route to **Line 2** (`moveq #2,%d0; bra .L59_dest_ok`).

This routes **whichever physical bank the current round assigns to Layer-B** to the single Genesis Layer-B
owner, Line 2 — not just bank 2. It is round-general (fixes R2/R3/R4/R5; R1 unchanged since bank 2 already →
Line 2), NOT an `if round==2`. R1's FG bank-3 write does **not** match round 1's Layer-B bank (2), so R1 is
unaffected. Allowed category: "correct the translation of an original palette bank/domain into the Genesis
semantic L2 owner."

**Residual disclosed:** in R2 the frame-0x50 transition write (bank 3, source 0x511DA) could match the
round-2 bank if `a5@0x118` were already 2 and `scene_id==1` at that instant; it is then overwritten by the
authoritative BG load at frame 0x70, so steady-state L2 is correct. The round counter is very likely still the
prior round at frame 0x50, so no collision is expected. If Tighe sees a brief READY-screen flash, the clean
follow-up is a caller/flag discriminator on the per-stage loader.

## 15. No hardcoded R2 palette
No `$5DC4E` copy, no colour values, no `if round==2`, no Composer asset, no frozen L2. Only a 6-entry
bank-number routing table + a bank-match branch. Colours still come from the retained arcade loader + runtime
conversion.

## 16. R1 dynamic L2 preserved
R1 Layer-B path unchanged (bank 2 → Line 2, same outcome as before — the match short-circuits to the identical
Line-2 staging). Water/progression routes untouched. R1 Plane-B tiles byte-identical (0566 generator unchanged).

## 17. L0/L1/L3 preserved
The fix only ever sets destination Line **2**; the gameplay gate still rejects non-Line-2 writes for other
banks (bank 4 → Line 0 rejected, etc.). Test-2.0 Lines 0/1/3 remain protected. Throne/frontend routing not
touched (scene_id==1 gate; frontend is scene_id!=1).

## 18/19. Candidate + test instructions
Build **0567** — see artifacts/SHAs below.
- **Test first:** `rastan_direct_video_test_build_0567.bin` in **natural** progression → reach R2-S1, verify
  Layer-B shows the brown/green forest palette (not cyan/yellow). Also check R1-S1 unchanged (colours,
  progression, water), Lines 0/1/3, throne/frontend, R2 Plane A.
- Secondary: `..._0567_R2-S1.bin` direct-start (convenience; natural is authority).

## 20. Report path
This file. 0131 report updated with the correction note. AGENTS_LOG appended.

## 21. Follow-up status (PROMT-ID-0134, 2026-11-13)
- **Initial-entry R2 palette fix ACCEPTED** by Tighe: on normal R2-S1 scene entry the 0132 bank routing puts
  the correct brown/green forest on Genesis Line 2. The 0131 tile fix is also accepted.
- **Death/respawn regression discovered:** after dying and respawning in R2-S1, Line 2 shows the wrong colours
  (geometry/tiles still correct and still on L2).
- **Proven respawn lifecycle (0134):** the substate-8 READY/death teardown routes through Genesis `scene_id=0`,
  where `load_scene_tiles` copies `genesistan_frontend_base_palette` across ALL four staged lines, clobbering
  Line 2 (the wrong colours are an EXACT match of that palette's Line 2). Respawn rebuilds `scene_id=1` but the
  scene-0 copy is skipped, `vdp_install_test_lines` owns only Lines 0/1/3, and the retained round-entry sequence
  that arms the Layer-B reload (`a5@0x13b0`) does not re-run on a same-stage respawn — so `FUN_00059de8` never
  repaints Line 2. This is the normal scene-load Layer-B path being bypassed on respawn (Model 1). The 0132
  bank-3 routing is NOT at fault and was NOT narrowed. Fix (Build 0568): re-arm `a5@0x13b0` at gameplay-scene
  activation so the retained loader restores the current round's Layer-B. See
  `Andy_...PROMT-ID-0134_r2s1_respawn_bypassed_layerb_reload.md`.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0132`

### Artifacts
Build 0567, GATE_PASS `[canonical=PASS entry=FAIL epoch=FAIL]` (MAME env-blocked as always).
- Normal: `dist/rastan-direct/rastan_direct_video_test_build_0567.bin`
  SHA-256 `d2fc5a64d5c66837edc2ae7205916a42357c157054ca1351f0229ae47590277f`
- R2-S1 direct-start: `dist/rastan-direct/rastan_direct_video_test_build_0567_R2-S1.bin`
  SHA-256 `7382320eaddb192b653ce804f6e24e449ce884210583e12454d04707f9096994`
- Build 0564/0565/0566 artifacts untouched on disk; 0566 tile generator unchanged (0131 Part 1 preserved).
