# Build0292 — Exact Byte-for-Byte Reproduction of Build0287

**Baseline:** current tree after Build 0291. **No rollback**; all numbered ROMs 0286–0292 preserved. Labels:
**PROVEN / HYPOTHESIS / DISPROVEN**.

## PURPOSE
Hard reproducibility / isolation baseline: reconstruct the exact project state that produced preserved Build0287,
clean-rebuild deterministically, and prove the result is **byte-for-byte identical** to Build0287 — then number it
0292. All post-Build0287 variables (including the new screenshot-first crash handler) are removed so Tighe can test
a ROM whose content is provably Build0287.

## BUILD0287 ORACLE
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0287.bin`
- SHA-256: `a03094b046f3aeb66f3c31797081612d5ac73e1b4cfb67653938f9dd9015f12d`
- Size: 1,591,860 bytes. (Preserved, unmodified.)

## RECONSTRUCTION
**PROVEN.** The crash handler and the Makefile build-number plumbing were changed **only** at Build0288 (the
crash-handler task); across Builds 0284–0287 they were untouched. Therefore their Build0287 state equals git HEAD
(commit "Build 283"). `pc090oj_hooks.s`, `specs/rastan_direct_remap.json`, and the canonical-verifier constants
(`CANONICAL_OPCODE_REPLACE_COUNT=228`, `CANONICAL_TOTAL_GENESIS_BYTES_COVERED=0x184A34`) were last changed at
Build0287 and are already the Build0287 state in the tree. Reconstruction steps:
- `git checkout HEAD -- apps/rastan-direct/src/crash_handler.s apps/rastan-direct/Makefile` → restores the Build0287
  crash handler (the `moveq #vec,%d0` stubs, `crash_render_screen`, `crash_clear_plane_a`, the `BUILD 0038` footer)
  and the Build0287 Makefile (no `crash_build.inc` plumbing).
- Removed the generated `out/crash_build.inc` (not referenced by the old handler/Makefile).
- Kept everything else (already at Build0287 state).

## POST-0287 CRASH-HANDLER WORK REMOVED
**PROVEN.** The screenshot-first rewrite, enlarged font/report, redesigned entry (movem-first capture), VDP
clean-room, D2 numeric fix, `crash_build.inc` / automatic numbered-build string, and the associated Makefile
dependency and moved exception-vector targets are all removed for this baseline. (Not abandoned — the working tree is
temporarily at Build0287 state; the newer crash-handler work remains in git/report history for future restoration.)

## CLEAN REBUILD
**PROVEN.** `make clean` (removes `out/` and the local `dist/`; the numbered ROMs live in `$(ROOT)/dist/rastan-direct/`
and are untouched) plus removal of the generated `build/regions/*` and `build/pc080sn_*` / `build/pc090oj_*` inputs, so
every object and generated input is rebuilt from scratch. No stale `.o`/`.inc` reused (`FORCE_ASM_REBUILD` reassembles
all objects each build).

## BINARY IDENTITY GATE
**ALL YES.** An UNNUMBERED ROM was produced first (build objects → ELF → prepatch → `build_rastan_regions` →
`postpatch_startup_rom.py`) and compared to the oracle BEFORE consuming a number:
- Preserved Build0287 SHA: `a03094b0…` · Rebuilt unnumbered SHA: `a03094b0…` — **identical**.
- Size identical (1,591,860). `cmp`: **0 differing bytes**.

Then numbered as Build0292 (deterministic full rebuild via `make release`), and re-verified:

| Check | Result |
|---|---|
| SHA-256 0292 == 0287 | `a03094b0…` == `a03094b0…` ✓ |
| Size identical | 1,591,860 == 1,591,860 ✓ |
| `cmp 0287 0292` | **0 differences** ✓ |
| Vector table identical | YES |
| ROM header identical | YES |
| Boot/crash-handler region identical | YES |
| arcade_copy identical | YES |
| genesis_only identical | YES |
| **Entire ROM identical** | **YES** |
| `BUILD 0038` footer present (old handler) | YES @0xC86 |
| `BUILD 0292` string in ROM | **absent** (numbering injects nothing) ✓ |
| Counter | 292 (not 293) |

## ADDRESS-MAP / GENERATED ARTIFACT CHECK
**PROVEN.** The regenerated `address_map.json` for the reproduced ROM is internally consistent
(`genesis_rom_size_bytes = 0x184A34` = ROM size; `preserved_vectors` end / `arcade_copy` start = 0x117E, the Build0287
boundary with the smaller old handler). This is a clean Build0287-compatible mapping baseline, not the post-0290
(0x125C) layout. `symbol.txt`, patch manifest, and postpatch disassembly were regenerated from the reconstructed
state.

## FORENSIC NOTE (0287 vs 0290)
**PROVEN.** 0287 vs 0290 differ ONLY in 0x0–0x125B: vector table (68 bytes), header checksum (2), and boot/crash
handler (3415). **The region 0x125C→end (all arcade_copy + genesis_only, i.e. the gameplay/rendering code) is
byte-identical between 0287 and 0290.** The 0x117E–0x125B bytes are FF-padding in 0287 vs crash-handler tail in 0290;
the arcade program is spliced at a fixed 0x125C in both, so the crash-handler size did not move or re-relocate any
arcade/genesis code. Build0292 therefore has gameplay bytes identical to both 0287 and 0290; it differs from 0290
only in the crash-diagnostic subsystem (old handler + its vectors).

## KNOWN ITEM-PAGE CRASH PRESERVED
**PROVEN.** `tst.l %a5` (`0x4A8D`) at runtime 0x073212 (`.Lnq_transient_items_emit`) is present in 0292 (byte-unchanged)
— the scrolling item page is expected to crash. Not closed. PC090OJ retirement not advanced; no PC080SN work.

## BUILD / STOP
- **GATE_PASS**; numbered **Build 0292**, content byte-identical to Build0287.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0292.bin` · SHA-256 `a03094b0…` · Size 1,591,860 · Counter
  290→…→**292** (not 293).
- Makefile smoke: PASS (30s Genesis-NTSC, 933.45%, no crash). Boot guard PASS (pre+post).
- No further release run; all verification reads the existing 0292 artifact.

## INTERPRETATION FOR THE TEST
Because 0292 is byte-identical to 0287, if Build0287 was genuinely good then Build0292 IS good (same bytes). Testing
0292 on Tighe's same setup:
- **0292 good** → confirms 0287-good; since 0292 differs from 0290 only in the crash-diagnostic subsystem (gameplay
  bytes identical), the 0288–0290 "regression" is attributable to the new crash handler's runtime behavior (or was
  environmental), not gameplay code.
- **0292 also broken** → then 0287 was not actually good, and the regression is 0286→0287 (setup/priority retirement +
  GAME OVER emit into `.Lnq_gameplay`), which becomes the fix target.
