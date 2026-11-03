# Cody — Build 55 Palette Pipeline Runtime Localization

## Scope
- Read-only localization of the first broken link in:
  - arcade reaches helper -> helper writes staging -> `palette_dirty` set -> `_vblank_service` runs -> `vdp_commit_palette` runs -> CRAM updated.
- Artifacts used: local project files only.

## §1.1 PCs mapped to symbols
- PC `0x0003A192` (sec 20):
  - Source frame observation: `docs/design/Cody_build55_video_30fps_debug_windows.md:85-90`.
  - Instruction at PC: `movel 0x0,%d0` at `build/genesis_postpatch.disasm.txt:72725`.
  - Symbol resolution: no matching symbol in `apps/rastan-direct/out/symbol.txt` (nearest code symbols begin at `0x070000`), so this PC is in relocated arcade code, not in palette helper / vblank helper symbols.
  - Classification: unrelated to `genesistan_palette_hook_*`, `_vblank_service`, `vdp_commit_palette`.

- PC `0x00070162` (sec 50):
  - Source frame observation: `docs/design/Cody_build55_video_30fps_debug_windows.md:93-98`.
  - Instruction at PC: `dbf %d7,0x7015c` at `build/genesis_postpatch.disasm.txt:122765`.
  - Function context: inside `vdp_commit_bg_strips_if_dirty` body (`build/genesis_postpatch.disasm.txt:122748-122790`), symbolized from `apps/rastan-direct/out/symbol.txt:155,159`.
  - Classification: in vblank commit path (BG strips), not in palette helpers.

## §1.2 Build 55 helper/symbol addresses
- `genesistan_palette_hook_59ad4`: `0x000711E2` (`apps/rastan-direct/out/symbol.txt:176`)
- `genesistan_palette_hook_03ab00`: `0x00071248` (`apps/rastan-direct/out/symbol.txt:177`)
- `genesistan_palette_hook_45dae`: `0x0007126C` (`apps/rastan-direct/out/symbol.txt:178`)
- `staged_palette_words`: `0x00FF601A` (`apps/rastan-direct/out/symbol.txt:256`)
- `palette_dirty`: `0x00FF4000` (`apps/rastan-direct/out/symbol.txt:244`)
- `vdp_commit_palette`: `0x000701CC` (`apps/rastan-direct/out/symbol.txt:159`)
- `_vblank_service`: `0x000700C2` (`apps/rastan-direct/out/symbol.txt:155`)

## §1.3 Opcode-replace patch confirmation
- Runtime target for `arcade_pc 0x059AD4` -> `runtime 0x059CD4`:
  - Observed: `jsr 0x711e2` at `build/genesis_postpatch.disasm.txt:113271`.
  - Result: `PATCHED-CORRECTLY` (target matches `genesistan_palette_hook_59ad4` at `0x711E2`).

- Runtime target for `arcade_pc 0x03AB00` -> `runtime 0x03AD00`:
  - Observed: `jsr 0x71248` at `build/genesis_postpatch.disasm.txt:73574`.
  - Result: `PATCHED-CORRECTLY` (target matches `genesistan_palette_hook_03ab00` at `0x71248`).

- Runtime target for `arcade_pc 0x045DB8` -> `runtime 0x045FB8`:
  - Observed: `jsr 0x7126c` at `build/genesis_postpatch.disasm.txt:88525`.
  - Result: `PATCHED-CORRECTLY` (target matches `genesistan_palette_hook_45dae` at `0x7126C`).

- Spec alignment:
  - `arcade_pc` entries present at `0x059AD4`, `0x03AB00`, `0x045DB8` in `specs/rastan_direct_remap.json:694,700,706`.
  - `opcode_replace_count` = `93` at `specs/rastan_direct_remap.json:714`.

## §1.4 Helper reachability from available frame evidence
- Available explicit PC observations in the existing video evidence are:
  - sec 20: `0x0003A192` (`docs/design/Cody_build55_video_30fps_debug_windows.md:90`)
  - sec 50: `0x00070162` (`docs/design/Cody_build55_video_30fps_debug_windows.md:98`)
- Helper address ranges from symbols:
  - `genesistan_palette_hook_59ad4`: `0x711E2..0x71247` (next symbol at `0x71248`, `apps/rastan-direct/out/symbol.txt:176-177`)
  - `genesistan_palette_hook_03ab00`: `0x71248..0x7126B` (next symbol at `0x7126C`, `apps/rastan-direct/out/symbol.txt:177-178`)
  - `genesistan_palette_hook_45dae`: `0x7126C..0x7142B` (next symbol at `0x7142C`, `apps/rastan-direct/out/symbol.txt:178-179`)
- Observed reachability status from current sampled-PC evidence:
  - `genesistan_palette_hook_59ad4`: `NOT OBSERVED`
  - `genesistan_palette_hook_03ab00`: `NOT OBSERVED`
  - `genesistan_palette_hook_45dae`: `NOT OBSERVED`

Note: this is `NOT OBSERVED` in available sampled-PC evidence, not proof of never reached.

## §1.5 WRAM palette-pipeline visibility
- `staged_palette_words` (`0x00FF601A`) and `palette_dirty` (`0x00FF4000`) are symbol-resolved (`apps/rastan-direct/out/symbol.txt:244,256`).
- Existing captured debug windows document CRAM/VRAM/port monitor/registers, but no WRAM watch window for these addresses (`docs/design/Cody_build55_video_30fps_debug_windows.md:44-109`).
- Result:
  - `staged_palette_words`: `NOT VISIBLE`
  - `palette_dirty`: `NOT VISIBLE`
- Addresses needed next recording session:
  - `0x00FF4000` (`palette_dirty`)
  - `0x00FF601A` (`staged_palette_words` base; inspect at least 64 words)

## §1.6 VBlank commit path evidence
- `_vblank_service` body includes palette gate:
  - `tst.b palette_dirty`, `bsr vdp_commit_palette`, `clr.b palette_dirty` at `apps/rastan-direct/src/vdp_comm.s:168-171`.
- `vdp_commit_palette` symbol address is `0x000701CC` (`apps/rastan-direct/out/symbol.txt:159`) and disassembly body starts at `build/genesis_postpatch.disasm.txt:122800`.
- From sampled PC evidence:
  - `_vblank_service`: `REACHED` (sec 50 PC `0x70162` is inside its called commit routine during vblank service flow; disassembly context `build/genesis_postpatch.disasm.txt:122748-122790` plus `_vblank_service` call chain `build/genesis_postpatch.disasm.txt:122722-122732`).
  - `vdp_commit_palette`: `NOT OBSERVED` in sampled PCs.
- Port monitor:
  - Existing sampled entries show control/data activity but no explicit CRAM-target write was captured in sampled lines (`docs/design/Cody_build55_video_30fps_debug_windows.md:64-75`).
  - CRAM panel remains `0x0EEE` in sampled times (`docs/design/Cody_build55_video_30fps_debug_windows.md:46`).
  - CRAM-target writes in sampled evidence: `NOT OBSERVED`.

## §1.7 First broken-link classification
- Classification: **I — evidence insufficient**.

Cited basis:
- Patches are confirmed present and correct (§1.3).
- `_vblank_service` path is observed active via sec 50 PC in commit flow (§1.1, §1.6).
- Helper entry was not observed in available sampled-PC evidence (§1.4).
- WRAM values for `staged_palette_words` and `palette_dirty` are not visible in the captured windows (§1.5).
- `vdp_commit_palette` PC and CRAM-target writes were not observed in sampled evidence (§1.6).

Required additional evidence for definitive A..H localization:
- Runtime watch/trace for:
  - `PC` hits at helper ranges (`0x711E2..0x7142B`) and `vdp_commit_palette` (`0x701CC`)
  - writes/values at `0x00FF4000` (`palette_dirty`)
  - writes/values at `0x00FF601A` (`staged_palette_words`, 64 words)
- CRAM write trace (control-port commands that target CRAM + corresponding data-port writes).

## Integrity
- §1.1 PCs mapped to symbols: YES
- §1.2 helper/symbol addresses identified: YES
- §1.3 opcode_replace patching confirmed: YES (all 3 `PATCHED-CORRECTLY`)
- §1.4 helper reachability: NOT OBSERVED (from available sampled-PC evidence)
- §1.5 WRAM visibility: NO (`NOT VISIBLE`)
- §1.6 VBlank commit path:
  - `_vblank_service`: REACHED
  - `vdp_commit_palette`: NOT OBSERVED
  - CRAM-target writes: NOT OBSERVED
- §1.7 first broken link classification: I

