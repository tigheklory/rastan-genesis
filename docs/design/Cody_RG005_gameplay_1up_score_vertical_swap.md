# PROMPT RG-005 — Cody — Fix Gameplay 1UP / Score Vertical Swap

## Result

Build 0467 corrects only the normal-gameplay vertical relationship between the `1UP` label and
the current-player score. Tighe tested the normal ROM on real Sega Genesis hardware on
2026-10-21 and confirmed that `1UP` and SCORE are now in the correct positions. Build 0467 is
accepted. Immutable annotated tag `accepted/build-0467` peels to exact ROM-producing source
`ae6179e33ad5a64672050bcbe7e03308c2a8570e`.

The accepted normal ROM is
`dist/rastan-direct/rastan_direct_video_test_build_0467.bin`, SHA-256
`8950c173471fc29ba326b8535a163c7265354e0c4c397de24668ac88a45e8e11`, size
2,739,896 bytes. The Makefile-owned counter advanced from accepted Build 0466 to Build 0467 and
remains 467. Build 0468 was not produced or consumed.

## Build-0466 acceptance lock

Before RG-005 production work, Tighe's real-hardware acceptance of Build 0466 was recorded,
accepted ROM SHA-256
`9ca337969058d206588d886dec6f38f6f2b73e3648c46ef25a01ae6a1e27c4f2` was verified, and
immutable tag `accepted/build-0466` was created at exact source
`3bd0166e7df19553ba8066f24d1f47b7cb2d5ea5`. Acceptance bookkeeping was committed separately as
`00c1f895`. The accepted tag was not moved or amended.

## Original arcade semantics and static proof

The canonical Ghidra exports, raw `build/maincpu.disasm.txt`, original `maincpu.bin`, and current
`build/rastan-direct/address_map.json` establish the producer chain:

- arcade `0x03B8B0` (current mapped runtime site `0x03BAB6`) initializes the fixed HUD records by
  feeding ROM tables to `0x03B930`;
- the P1 label table at arcade data `0x03B9B0` (current runtime `0x03BBB6`) assigns code `0x39`
  (`1`) X=`0x40`, Y=`0x10`; code `0x48` (`U`) X=`0x28`, Y=`0x00`; and code `0x46` (`P`)
  X=`0x38`, Y=`0x00`;
- arcade `0x03B802` (current mapped replacement site `0x03BA08`) emits packed-BCD score digits;
  its mode-0 descriptor at arcade data `0x03B87E` (current mapped site `0x03BA84`) specifies six
  digits, semantic Y=`0x10`, PC090OJ destination `HW_ADDRESS 0x00D00108`, and score source
  arcade work RAM `0x0010C11E`, represented as Genesis WRAM `0x00FF011E`.

Thus the original producer does not apply an arbitrary visual offset. It gives the score family
Y=`0x10`, gives the label's `1` piece Y=`0x10`, and gives the `U`/`P` pieces Y=`0x00`. The glyph
geometry plus those semantic coordinates produces `1UP` above SCORE.

## First wrong stage and root cause

Normal gameplay and the full frontend HUD use independent final producers. Normal gameplay enters
`.Lnq_gameplay` and `.Lnq_project_p1_hud` under the established
`RASTAN_GAMEPLAY_HUD_SPRITES == 2` mode. The accepted full HUD uses the generated
`FRONTEND_FULL` package in `hud_native.s` and generated final SAT assets.

The first wrong stage was the gameplay-only `.Lnq_project_p1_hud` coordinate realization. It did
not set D2/Y before emitting the six score digits, so they inherited an unrelated caller value. It
then forced all three fixed label pieces to Y=`0x10`, losing the original per-piece
`0x10/0x00/0x00` association. This was neither a row-index inversion nor a full-HUD transform; it
was two lost source-coordinate semantics in the independent reduced-gameplay producer.

## Correction

`apps/rastan-direct/src/pc090oj_hooks.s` now:

- explicitly sets score-digit semantic Y=`0x10` before the six packed-BCD emissions;
- retains code `0x39` (`1`) at Y=`0x10`;
- clears D2 so codes `0x48`/`0x46` (`U`/`P`) use Y=`0x00`.

`tools/translation/verify_native_hud.py` now provides the bounded static geometry gate. It verifies
the authoritative original score descriptor and label table, then verifies that the normal
gameplay producer encodes score Y=`0x10` and label Y=`0x10/0x00/0x00`.

No full-HUD source or generator changed. The generated frontend assets retain the accepted
Build-0466 hashes: patterns `2494a6db83781607e609208982e1cc2dcc1e111cbe3773b5035c60c81cd54edc`,
static SAT `570c766c5eac962574b09bf2b97fbee38e4bb1462b2df5f2892ca39b91662913`, and dynamic records
`6790134f9962f9c2d80017c2a6ed5d2cd78a263dee4f4ff0e419aa19a41514db`.

## Architecture

The semantic cut remains retained arcade HUD identity, live packed-BCD score state, visibility,
and original coordinate contract to direct Genesis native lane/SAT production. The legacy
PC090OJ object-record packing, object-RAM destination, record scan, and generic chip tail below
the already-established HUD cut remain retired. RG-005 removes no additional legacy subsystem; it
corrects final coordinate association inside the existing native gameplay realization. It adds no
shadow RAM, device emulation, scheduler, fallback, NOP, RTS bypass, or frame-time visual patch.

## Build and configured family

The ROM-producing source was committed before the default build as
`ae6179e33ad5a64672050bcbe7e03308c2a8570e`. The default Makefile pipeline produced Build 0467
with 228 byte-neutral opcode-replacement sites and 77 shift replacements; wrapper/Genesis coverage
ends at `0x29CEB8`. All seven same-number artifacts are present, configuration-verified, and
2,739,896 bytes:

| Artifact | SHA-256 |
|---|---|
| normal | `8950c173471fc29ba326b8535a163c7265354e0c4c397de24668ac88a45e8e11` |
| `_d` | `33e0cc6923450d1b30c9cbe3ee66bfe11ec454b03ef40462e8b415e44472e613` |
| `_s` | `6cdd14080a985929519d20e0e152cff9c8dcfad07410985303a6da65e380af93` |
| `_do` | `cd60ffd66749b4bc41a4b563336c34f2ef326dcf5e7b23bf682408f6056bfcc2` |
| `_c` | `9b6d4329776b2c65fcdc64b0c098ad1b991b21e5cbff206d14e12500760397e0` |
| `_full_hud` | `e51ea7a75151076bae9a5202a1ce1e1f4a6203b964bb3fe36963cc8ecc9b298e` |
| `_invincible` | `36455776e6803ffaeb154e4d44b29d20a2997228eb2544b257abcbd37d71da5b` |

## Validation

Static original-arcade meaning was established without a new decompilation project or new arcade
trace. Runtime checks used the MAME USA/NTSC Genesis driver; final visual acceptance used real Sega
Genesis hardware.

- canonical gate and pre/post boot guards: **PASS**;
- gameplay-entry gate: **PASS**, gameplay reached with 240 required post-entry frames and zero
  address/bus/illegal/crash-handler errors;
- Phase-1 seven-epoch gate: **PASS**, seven epochs tested with complete Plane-A and fixed Plane-B
  LUT checks;
- final-life semantic verifier: **PASS**, arcade `0x03A3C0` maps to generated target `0x03B320`;
- bounded native HUD geometry verifier: **PASS**, normal gameplay score Y=`0x10`, label
  Y=`0x10/0x00/0x00`; generated `FRONTEND_FULL` assets unchanged;
- fixed30 Genesis NTSC trace: **PASS**, 1,798 frames and zero live FG C-window writes;
- final-life zero-input regression: **PASS**, GAME OVER reached at frame 3,585 after three death
  entries, tuple `2/4/6`, zero lives;
- RG-004 Continue regression: **PASS**, tuple `2/4/8`, 83 distinct staged/actual panel names, zero
  mismatches, zero nonblank outside-panel cells, and staged CRAM equals actual CRAM;
- RG-004 attract regression: **PASS**, natural demo death and second title reached at frame 7,227;
  all second-title staged lines equal first-title lines and terminal CRAM;
- established `_invincible` rope benchmark: **PASS**, `798/798/798`, median 13,317.147 ms,
  deterministic **YES**;
- complete configured ROM-family verification: **PASS** for normal, `_d`, `_s`, `_do`, `_c`,
  `_full_hud`, and `_invincible`;
- Tighe real Genesis hardware: **ACCEPTED**; normal gameplay now shows `1UP` and SCORE in the
  correct positions, while the full HUD remains correct.

No AI gameplay navigation occurred. Existing deterministic and bounded project harnesses supplied
all runtime validation.

## Issue closure and boundaries

The previously deferred normal-gameplay `1UP`/SCORE vertical-swap defect is **CLOSED** by static
source-coordinate proof, bounded encoded-geometry verification, automated regression validation,
and Tighe's real-hardware acceptance. No broader HUD issue is closed. HUD performance optimization
is explicitly deferred to a separate prompt.

Palette decisions, `Test.json`, frontend/title/BEST-5 behavior, item presentation, gameplay
palettes, Demon and reward/death palette work, audio, scrolling, timing, SAT ownership, Phase D,
and Phase E were not changed.

Existing project tools reused: canonical Ghidra exports and disassembly; current address map;
`verify_native_hud.py`; Makefile canonical/gameplay/epoch/family gates; fixed30 trace;
`run_final_life_zero_input_regression.sh`; `rg004_frontend_probe.lua`; and
`run_rope_attach_performance_benchmark.sh`.

New tooling created: none. The existing native-HUD verifier was extended with the missing bounded
geometry contract because it already owned this subsystem.

Hardware acceptance target: completed. Tighe confirmed normal gameplay `1UP` above SCORE on real
Genesis hardware and no vertical exchange relative to the full HUD.

STOP status: RG-005 complete. Build 0467 accepted. Build 0468 not consumed.
