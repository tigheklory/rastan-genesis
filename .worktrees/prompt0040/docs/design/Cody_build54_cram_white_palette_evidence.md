# [Cody — Build 54 CRAM All-White Palette Root Cause Evidence]

Type: Read-only evidence collection
Build context: rastan-direct Build 0054

## §1.1 — `vdp_boot_setup` CRAM initialization

Source-verified findings:

- `vdp_boot_setup` in `vdp_comm.s` sets VDP registers via `vdp_set_reg` and returns; no CRAM fill loop appears in this function body.
  - `vdp_boot_setup` body: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:62)
  - last instruction in function: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:123)
- `_bootstrap` calls `vdp_boot_setup`, then `_bootstrap_clear_staging`, then `load_scene_tiles`, then jumps to relocated arcade reset at `0x00003A200`.
  - call chain: [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:160), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:161), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:163), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:166)
- `_bootstrap_clear_staging` explicitly clears `staged_palette_words` (64 words) and clears `palette_dirty`.
  - clear loop: [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:175), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:180), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:183)
- The explicit `0x0EEE` CRAM write appears in `crash_init_cram` (included from `crash_handler.s` via `vdp_comm.s` include), not in `vdp_boot_setup`.
  - include: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:60)
  - `crash_init_cram`: [crash_handler.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/crash_handler.s:285)
  - writes: [crash_handler.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/crash_handler.s:286), [crash_handler.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/crash_handler.s:288)

Verbatim snippet (`crash_init_cram`):

```asm
crash_init_cram:
    move.l  #0xC0000000, VDP_CTRL
    move.w  #0x0000, VDP_DATA
    move.w  #0x0EEE, VDP_DATA
    rts
```

## §1.2 — Arcade palette-load routine identification (static)

Search evidence in arcade disassembly (`build/maincpu.disasm.txt`) found a hardware-write block at arcade PCs `0x03ADFE`, `0x03AE06`, `0x03AE16`, `0x03AE1E`, `0x03AE86`, `0x03AE8E`:

- `0x03ADFE: movew #0,0xc50000`
- `0x03AE06: movew #1,0xd01bfe`
- `0x03AE16: movew #1,0xc50000`
- `0x03AE1E: movew #0,0xd01bfe`
- `0x03AE86: movew #0,0xc50000`
- `0x03AE8E: movew #0,0xd01bfe`

Citations:
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73947)
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73949)
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73953)
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73955)
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73984)
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73986)

Routine window containing the first four writes:
- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73934)

Opcode-replace coverage for these six arcade PCs is present in `specs/rastan_direct_remap.json` (see §1.4).

Palette source data address in arcade ROM from this routine body: `NOT IDENTIFIED` in this pass.

## §1.3 — Genesis-side palette helper inventory

Source-level helpers/paths with palette/CRAM behavior:

1. `vdp_commit_palette` (direct CRAM target command + 64-word write from staged buffer)
- definition: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:274)
- CRAM command: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:275)
- data copy loop: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:279)
- staging source: `staged_palette_words` at [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:329)

2. `_vblank_service` palette gate
- checks `palette_dirty`, calls `vdp_commit_palette`, clears `palette_dirty`: [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:168), [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:170), [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s:171)

3. `_bootstrap_clear_staging` (staging clear, not CRAM write)
- clears palette staging array and `palette_dirty`: [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:175), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:180), [boot.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s:183)

4. `crash_init_cram` (direct CRAM write path with `0x0EEE`)
- [crash_handler.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/crash_handler.s:285)

`specs/rastan_direct_remap.json` entries referencing a palette helper symbol target: `NONE FOUND` for `genesistan_hook_*palette*`-style symbol names in this pass.

## §1.4 — `opcode_replace` coverage check for palette-related arcade candidates

For the six candidate arcade write sites from §1.2:

- `0x03ADFE` -> replacement bytes `4E714E714E714E71`
- `0x03AE06` -> replacement bytes `4E714E714E714E71`
- `0x03AE16` -> replacement bytes `4E714E714E714E71`
- `0x03AE1E` -> replacement bytes `4E714E714E714E71`
- `0x03AE86` -> replacement bytes `4E714E714E714E71`
- `0x03AE8E` -> replacement bytes `4E714E714E714E71`

Citations:
- [rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json:313)
- [rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json:319)
- [rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json:325)
- [rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json:331)
- [rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json:343)
- [rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json:349)

Postpatch disassembly check for these absolute-write instructions:
- literal `movew #...,0xc50000` / `movew #...,0xd01bfe` at those PCs: `NOT PRESENT` in `build/genesis_postpatch.disasm.txt` search pass.

## §1.5 — Runtime CRAM write log (MAME)

MAME runtime trace artifact used:
- `/tmp/build54_cram_trace4.debug.log`

Trace setup recorded in log:
- watchpoint on `0xC00004` writes with condition `(wpdata & 0xF000) == 0xC000`
- watchpoint on `0xC00006` writes with same condition
- data-port watchpoints on `0xC00000` / `0xC00002` when armed
- emulation interval: `gtime 30000`

Trace output lines:
- `CRAMTRACE_START pc=204 cyc=34`
- `CRAMTRACE_TIMEOUT pc=3A19E cyc=1508072460`
- no runtime lines beginning with `CRAM_CTRL4`, `CRAM_CTRL6`, `CRAM_DATA0`, or `CRAM_DATA2`

Citations:
- [/tmp/build54_cram_trace4.debug.log](/tmp/build54_cram_trace4.debug.log:4)
- [/tmp/build54_cram_trace4.debug.log](/tmp/build54_cram_trace4.debug.log:18)

## §1.6 — Arcade ROM palette source identification

Searches performed in current artifact set:
- symbol search (`apps/rastan-direct/out/symbol.txt`) for palette-like symbols (`pal`, `palette`, `color`, `cram`, `clut`)
- disassembly search (`build/maincpu.disasm.txt`) for the candidate hardware-write addresses from §1.2
- build artifact inventory under `build/regions/`

Observed artifacts:
- `build/regions/` contains: `maincpu.bin`, `pc080sn.bin`, `pc090oj.bin`, `audiocpu.bin`, `adpcm.bin`, `variant.json`
  - directory listing: [build/regions](/home/tighe/projects/rastan-genesis/build/regions)
- no dedicated palette file named `palette*`/`clut*` found in `build/regions/` in this pass
- source-like symbols for Genesis staging side exist (`vdp_commit_palette`, `palette_dirty`, `staged_palette_words`) in symbol map:
  - [symbol.txt](/home/tighe/projects/rastan-genesis/apps/rastan-direct/out/symbol.txt:159)
  - [symbol.txt](/home/tighe/projects/rastan-genesis/apps/rastan-direct/out/symbol.txt:241)
  - [symbol.txt](/home/tighe/projects/rastan-genesis/apps/rastan-direct/out/symbol.txt:253)

Arcade ROM palette source address result: `NOT IDENTIFIED` in this pass.

## Phase 2 — Integrity

- §1.1 `vdp_boot_setup` CRAM init analyzed: `YES`; init value in `vdp_boot_setup`: `NO DIRECT CRAM WRITE`; `0x0EEE` write observed in `crash_init_cram`.
- §1.2 arcade palette-load candidates identified: `6 instruction sites` (within one routine window).
- §1.3 Genesis-side palette helpers identified: `4` (`vdp_commit_palette`, `_vblank_service` palette gate, `_bootstrap_clear_staging` palette-stage clear, `crash_init_cram`).
- §1.4 opcode_replace coverage classified for each candidate: `YES` (all 6 have explicit entries).
- §1.5 runtime CRAM write log captured: `YES`; CRAM-target runtime watchpoint matches observed: `0` in captured interval.
- §1.6 arcade ROM palette source identified: `NO` (`NOT IDENTIFIED` in this pass).
- All findings cited from artifacts (Rule 21): `YES`.
- No analysis (Rule 16): `YES`.
- No diagnosis (Rule 17): `YES`.
- No hypotheses (Rule 18): `YES`.
- No recommendations (Rule 19): `YES`.
- No source/spec/tool modifications: `YES`.

