# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0134 — R2-S1 respawn bypasses the Layer-B reload

**Author:** Andy · **Date:** 2026-11-13 · **Starting HEAD:** `f8b07a84` (`rastan-direct-proposal`), build counter 567,
working tree: 0131 tiles + 0132 initial-entry routing accepted (Build 0567). Only `apps/rastan-direct/src/scene_load.s`
changed by this task (plus docs/log). No spec, generated artifact, tile generator, or Plane-A code touched.

Root cause **statically proven** (exact colour identity + unique code path). Fix is the arcade-faithful
re-establishment of the retained Layer-B load at gameplay-scene activation. Tighe's gameplay test is authoritative.

---

## 1. Known-good normal R2-S1 scene-load palette path (Phase 1)
Correct L2 is produced solely by the retained per-stage Layer-B loader through the one Genesis hook:

- caller: `player_main_update_51090` → `FUN_00059de8` (0x59DE8) each gameplay frame, body gated `a5@0x13b0==1`.
- source: `A0 = 0x59EC8[a5@0x118-1] + D5*256` → R1=`0x5DB4E`, **R2=`0x5DC4E`** (disasm 0x59E6C).
- bank: `D0 = 0x59E8C[(a5@0x118-1)*8 + D5*2]` → R1=2, **R2=3** (disasm 0x59E50).
- row: `a5@0x13ae = byte[0x5E24E + a5@0x13e]` (fade/progression ramp; disasm 0x59E1E), consumed as `D1`.
- hook: `jsr 0x59ad4` @0x59E06 → `genesistan_palette_hook_59ad4`; 0132 routes the round's bank → **Line 2**.
- publication: staged `staged_palette_words + 2*32`, published by the VBlank CRAM DMA.

`a5@0x118` (round) and `a5@0x1242` (stage) are BOTH derived from the same selector `0x5FF9E/0x5FF9F`, gated by
`a5@0x104` (disasm 0x45278–0x452C0) — they cannot disagree.

## 2. Original arcade death/respawn (Phase 2) → classification C (preservation)
On the arcade each round's Layer-B palette lives in its own physical bank (R1=2, R2=3, …) and the round's
Plane-B tiles read that bank (`attr&3`). The substate-8 READY/death teardown returns presentation ownership to
the frontend, but it does **not** overwrite the gameplay Layer-B bank — arcade palette RAM is preserved, so
bank 3 still holds the R2 forest when gameplay resumes. The respawn therefore needs **no** Layer-B reload:
**Model C — palette preservation.** (`a5@0x118`/`a5@0x1242` stay R2; the respawn geometry proves it.)

## 3/4/5. Genesis Build 0567 respawn (Phase 3) — the first bad write, proven
The wrong post-respawn L2 is **exactly** `genesistan_frontend_base_palette` **Line 2**:
`#000000 #000000 #900000 #fc4800 #fc9000 #fcfc00 #fcfc90 #fcfcfc #0000b4 #0048fc #0090fc #00d8fc #b4fcfc …`
— red/orange canopy + yellow + blue→cyan columns = Tighe's respawn screenshot. The **only** code that copies
`frontend_base_palette` across Line 2 is `load_scene_tiles`'s scene-0 branch (scene_load.s:181–188, 64 words);
the other use (:333) copies 16 words = Line 0 only. Therefore:

- **First bad write:** death → substate-8 READY/death teardown sets `scene_id=0` → `load_scene_tiles(0)` copies
  `frontend_base_palette` across all four staged lines, **clobbering Line 2** with the frontend palette.
  caller=`load_scene_tiles` scene-0 copy; source=`genesistan_frontend_base_palette+0x40`; dest=Line 2.
- **Why it persists:** respawn rebuilds `scene_id=1` via `genesistan_gameplay_owner_reset → load_scene_tiles(1)`,
  which **skips** the scene-0 copy; `vdp_install_test_lines` owns Lines 0/1/3 only and never touches Line 2;
  and the retained round-entry sequence that normally arms `a5@0x13b0` (FUN_00051156 frame 0x70, gated
  `a5@0x13e∈[0x74,0x83]`) does **not** re-run on a same-stage respawn. So `FUN_00059de8` is never re-armed and
  **Line 2 is never restored.**
- **`a5@0x13B0` behaviour (Phase 3):** armed on normal entry (round-entry frame 0x70); **not re-armed on
  respawn** → the loader body never runs → no Layer-B restore. This is the divergence.
- **`FUN_00059de8` post-respawn:** does NOT execute its load body (flag unarmed) — root of the bug.
- **`FUN_00051190 / 0x511DA / bank3 / D1=1` (Phase 5):** that transition write touches only Line-2 entries
  9–15 with greyscale (`#444 #888 #ccc #aaa #055 #333`), which does **not** match the observed colours, and in
  any case is not the source of the full frontend palette seen. The 0132 bank-3 discriminator is **not** the
  cause; **do not** narrow it. (Every other `0x59ad4` caller's R2 bank — animated 0x0F, water 0x1A–0x1D
  rejected in R2 since the water path is `a5@0x1242<23`, sprite 0x33/0x43→Line 3 — was checked and cannot write
  the Layer-B colours to L2.)

**First exact divergence (item 12):** arcade preserves the Layer-B bank across the READY/death teardown (no
reload needed); Genesis collapses the four Layer-B banks onto Line 2 and the scene-0 teardown overwrites Line 2
with the frontend base palette, then the respawn never re-establishes it. **Model 1 (Tighe's leading
hypothesis) is confirmed:** the corrected normal scene-load Layer-B path is bypassed on respawn.

## Production fix
`apps/rastan-direct/src/scene_load.s`, gameplay-scene activation (`load_scene_tiles`, `scene_id==1`), all rounds,
after `fg_cache_reset`:

```asm
    move.w  #1, 0x13b0(%a5)   /* re-arm the retained arcade Layer-B reload */
```

This restores the arcade lifecycle: the retained loader `FUN_00059de8` repaints the **current** round's Layer-B
(current round `a5@0x118`, current progression row `a5@0x13e`) into Line 2 on the next player update — the same
semantic load as a normal scene entry. It matches the prompt's Model-1 remedy ("restore the missing original
semantic palette-restoration event … preserve the original arcade control-flow intent"): it re-arms the arcade's
own flag and reuses the arcade's own loader, not a Genesis-only helper.

- **No forbidden fix:** no hardcoded/copied R2 colours, no `$5DC4E` copy, no `if round==2 && respawn`, no death
  hook, no static/frozen L2, no state-machine replacement, no offline preconversion, no tile/Plane-A change.
- **Dynamic palette preserved:** the loader reads the **current** `a5@0x13e` row, so a later progression/water
  row at the respawn checkpoint is reconstructed, not forced to the stage-start row.

## Preservation / control (items 14–17)
- **14 no hardcode:** the fix sets a 1-word flag; colours still come from the retained loader source
  (`0x5DC4E` for R2) through the runtime xBGR→CRAM conversion.
- **15 initial-entry 0567 intact:** on normal entry the round-entry sequence already arms `a5@0x13b0`; the extra
  arm at activation is idempotent (loader runs once, self-clears to 0xFF). R2 initial L2 unchanged.
- **16 R1 control:** R1 Layer-B already flows from the same loader (bank 2 → Line 2). Re-arming at activation
  makes R1 respawn restore L2 too, using the current R1 row — so R1 progression/water (water = Line 3, untouched)
  and Layer-B remain correct; R1 respawn becomes equally robust. Verify in test.
- **17 L0/L1/L3:** the fix only arms the Layer-B (Line 2) loader; `vdp_install_test_lines` still owns Lines
  0/1/3, and the scene-1 hooks still reject non-Line-2 writes. Throne/frontend (scene_id≠1) unaffected.

## Candidate ROM / SHA (item 18)
Build **<NNNN>** (counter 567 → <NNNN>), see delivery block appended after the build.

## Tighe acceptance test (item 19)
Natural R2-S1 → confirm brown/green Layer-B; move around (all Plane-B stays L2); **die; respawn; confirm the
R2 Layer-B palette is restored**; die/respawn again; repeat at a later R2-S1 checkpoint; confirm no brief wrong
palette persists; verify R1 death/respawn, R1 progression/water, Lines 0/1/3, throne/frontend, R2 Plane A.

## Report path (item 20)
This file. 0132 report updated (initial-entry accepted; respawn regression + proven lifecycle). AGENTS_LOG appended.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0134`
