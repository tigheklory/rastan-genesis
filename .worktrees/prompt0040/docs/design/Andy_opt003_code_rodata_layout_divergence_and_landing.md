# OPT-003 Code/ROData Layout Divergence — Investigation + STOP (first-op isolated, exact instruction not capturable)

**Agent:** Andy · **Date:** 2026-09-03 · **Status:** STOPPED (STOP condition 1). OPT-003 fails the
seven-epoch gate for a real, deterministic reason isolated to a single active_lut clobber at the
epoch-change install; the exact clobbering instruction could not be captured with the available tooling,
and the layout-isolation experiment was inconclusive. No OPT-003 numbered ROM published.

---

## 1. Phase 0
- **Classification: EXTENDING.** Contradiction: none new (the BSS theory was already withdrawn).
- Priors: OPT-003 palette equivalence (512, 0 mismatches) stands. Build-0341 BSS/workram root cause
  remains **withdrawn** (matched-config: 138/138 BSS symbols identical). Process finding stands: never
  diff symbol maps across `RASTAN_DIAG_*` configs.

## 2. Corrected baseline
- **BSS shift: NO.** Matched release-vs-release: `fg_boundary_active_lut`=0xFF6188 in both; all BSS delta 0.
- OPT-003 changes only ROM `.text`/`.rodata` layout.

## 3. Reference vs OPT-003 symbol diff (matched release)
- `fg_boundary_install`: 0x0726A2 (unshifted; it is *before* pc090oj_hooks in link order)
- `palette_route_lookup`: 0x072AF8 (unshifted)
- `pc090oj_native_emit_pass`: 0x07361A → 0x07360C (−14; palsel routine is shorter)
- `fg_boundary_packages`: 0x0741F0 → 0x0741E0 (−16)
- `pc090oj_palsel_lut`: new 512-byte `.rodata` object

## 4. The package containing code 0x034C
- Target case: record 3 → package 7 (epoch 1). Gate map index **308** = (code 0x034C, slot 0x04E0).
- `fg_boundary_packages` bytes (all **49732**) are **byte-identical** between the reference and OPT-003
  ROMs (content unchanged; only the base address moved −16).

## 5. Complete reference chain — all correct
- Package base pointer in the ROM: reference stores **0x0741F0** at ROM offsets 0x726C8/0x72A60; OPT-003
  stores **0x0741E0** at the same offsets. **No stale 0x0741F0 survives in the OPT ROM** — the pointer is
  correctly relocated.
- Installer `fg_boundary_install` code is at the same address and byte-identical **except** correctly
  -relocated operand low bytes (e.g. ROM 0x726CB: F0→E0, the package-pointer low byte).
- Native→native references are linker-resolved (always correct); arcade→native are regenerated from
  symbol.txt each build. Every reference checked resolves correctly.

## 6. First runtime divergence (the key evidence)
Per-frame read of `active_lut[0x034C]` (WRAM 0xFF6188+0x698 = **0xFF6820**), both ROMs, gate injection at
frame 324, drift-safe survival=8:

| frame | event | REF val | OPT val |
|---|---|---|---|
| 320–326 | (pre) | 0000 | 0000 |
| **327** | package-0 install writes it | **04E0** | **04E0** |
| **328** | package-7 **epoch change** (transitions 1→2, aPkg→7) | **04E0** | **0000** |
| 329–336 | stable on package 7 | 04E0 | 0000 |

**So: correctly WRITTEN (frame 327), then CLOBBERED at the frame-328 epoch-change install in OPT-003 only,
and never re-written.** In reference it survives/re-writes. This is Part B outcome **#5 (written then
clobbered)**. The clobber is in the epoch-change path `.Linstall_build_translation` (fg_tile_cache.s),
which is itself unshifted and byte-identical modulo correct relocation.

## 7. Why the exact instruction was not captured
- MAME's translated (DRC) 68000 **bypasses Lua `install_write_tap`** — a write tap on 0xFF6820 caught
  nothing in either ROM (consistent with CLAUDE.md).
- Headless MAME with `-debug -debugscript` (write watchpoint on 0xFF6820) + the autoboot injection lua did
  not fire the watchpoint (harness limitation under `-video none`).
- `cpu.debug` is unavailable. Frame-granular reads (used above) prove *when* but not *which instruction*.

## 8. Controlled layout experiment (Part C/D) — inconclusive
Pinned `pc090oj_palsel_lut` into a dedicated high-ROM `.palsel` section (after `.crash`) to remove the
+512 `.rodata` growth. Symbol diff: the LUT no longer grew `.text.wrapper`, **but 46 existing symbols
still shifted** (the palsel code is still −14 bytes), so the variant is **not layout-neutral**. Worse, the
postpatch **failed a canonical coverage invariant** (`total_genesis_bytes_covered` 0x197EB8 → 0x198200:
the LUT at 0x198000 lands past the arcade splice), so its gate result is on a broken ROM and is invalid.
Conclusion: high-pinning is not a clean fix without also revising the coverage invariant, and it does not
neutralize the code shift. Reverted.

## 9. Exact root cause — NOT fully isolated
Isolated to: *the epoch-change install re-populates `active_lut` differently in OPT-003 for code 0x034C,
despite byte-identical package data, a correctly-relocated package pointer, identical BSS, and identical
installer code.* The remaining candidates are (a) a native reference in the translation path whose
resolution is layout-sensitive in a way not visible in the pointer/data checks, or (b) a DRC/timing
interaction with the gate's synthetic installer injection. Neither could be proven with the available
tooling. **Because everything statically checked is correct, "moving the LUT works" was deliberately not
accepted as a root cause (per the Prime Directive) — and moving the LUT did not even work cleanly.**

## 10. Open question that changes the stakes
The gate reaches epoch 1 by a **synthetic installer injection**, not by natural gameplay. Tighe has
confirmed the real game (0338–0341) plays correctly to the waterfall and beyond, and OPT-003's palette is
proven identical. It is **not yet established** whether the 0x034C clobber occurs in **natural gameplay**
or only under the gate's injected install. That distinction determines whether OPT-003 has a real visual
defect or only trips a synthetic-injection gate sensitivity.

## 11. No production change made
No padding, no hardcoded address, no gate change, no BSS/WRAM change, no palette change. Gate lua restored
to original. Generator + link.ld restored. OPT-003 remains intact in the working tree (LUT in `.rodata`).

## 12. Builds
No numbered build produced (scratch reconstructions only). Counter unchanged = **341**. Ledger unchanged.

## 13. OPT-003 state
Restored/intact; palette equivalence 512/0; still blocked by the OPEN epoch-change clobber.

## 14. Deferred VRAM reclaim (preserved)
0xD000–0xDFFF (128) + unused Window 0xF000–0xF7FF (64) ≈ 192 pattern slots to widen Layer-A and cut
loaning. Next major perf task after OPT-003 is unblocked.

## 15. STOP + recommended next steps for Tighe
STOP condition 1 (first divergent *operation* isolated, but the exact reference/instruction not isolable
with available tooling). Options, cheapest first:
1. **Resolve the stakes (§10):** validate OPT-003 in **natural gameplay** (no injection) — does the
   epoch-1 Plane-A region render correctly? If yes, the gate's synthetic injection is the sensitivity and
   OPT-003 can land with a gate-injection fix rather than a ROM fix.
2. **DRC-capable trace:** run non-DRC MAME (interpreter core) or a proper debugger watchpoint on 0xFF6820
   to capture the clobbering PC — the one datum that would name the exact reference.
3. If a layout-sensitive native reference is then named, fix it at its ownership boundary (symbolic →
   regenerated address), not by moving the LUT.
