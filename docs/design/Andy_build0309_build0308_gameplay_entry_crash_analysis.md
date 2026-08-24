# Andy — Build 0309 Pre-Fix: Build-0308 Gameplay-Entry Crash Analysis

**Type:** root-cause analysis only. No production change, no ROM, Build 0309 not consumed.
Failing build 0308 (`32f7523f…67a65`); baseline 0307 (`c46ed6b8…b96ac9`).

## Fault (resolved, not inferred)
- **GEN PC 0x00072770** = **`fg_boundary_install` + 0x9a** (source `apps/rastan-direct/src/fg_tile_cache.s`;
  `SRC_GENONLY` = native helper, correct — no arcade PC).
- Instruction at 0x72770: **`movew %a2@+,%d1`** — a **word** read through a package-data pointer, inside
  `fg_boundary_install`'s residency-install loops. (The 68000 stacks an *imprecise* PC on an address
  error; the same `movew (An)+` pattern is used for both the fixed-B `%a2` loop at 0x7276e and the
  per-record `%a3` loops at 0x727d2/0x7282c. The captured registers pin the actual faulting pointer.)
- **Why ADDRESS ERROR (vector 3):** a 68000 **word** access to an **odd** address. Captured
  **A2 = 0x00074CC9 is odd**; **A3 = 0x001988B8 is wildly out of range** (z80 driver region, far past the
  59,564-byte package binary at `fg_boundary_packages` 0x74058..0x82904). Either read faults.

## Effective-address reconstruction
`fg_boundary_packages` base **A4 = 0x74058** (`lea 0x74058,%a4`, 0x726f4). The per-record install
(0x727b8+): `a2 = a4 + d4` (d4 = descriptor **data_offset**), `a3 = a2`, then
`a3 += (d5+d6)*4` (d5=map_pairs, d6=upload_pairs), then further section advances.
- **A2 = 0x74CC9 = A4 + 0x0C71.** `0x0C71` is **odd** and lands **mid-package-2 data** (pkg-2 region
  0x9EC..0x1150) — not any package's `data_offset` (all 23 are even; pkg-0 = 0x1CC). So the pointer is
  both **misaligned** and **mistargeted**.
- **A3 = 0x1988B8 = A4 + 0x124860** — a **massive overrun** far beyond the 0xE8AC-byte binary. `a3` can
  only reach there if a **section count/stride it accumulates is garbage/huge**.
- The crash screen's `ACCESS/FAULT 0x00391C3F` (= A4 + 0x31DBE7, odd) is the same failure class: a
  package pointer built from a bad section size, landing far out of range at an odd byte.

**First value that became wrong:** a **package-data section count/stride** (map/upload/identity/remap
counts consumed by the per-record install), producing odd + out-of-range `a2`/`a3`.
**Producer:** the Build-0308 `fg_boundary_install` package-walk arithmetic vs the Build-0308 compiler's
new multi-section package layout.

## SP OUT OF WRAM RANGE — false positive (Phase 3 closed)
`FRAME SP = 0x00FEFF48`. Genesis maps **0xE00000–0xFFFFFF as the 64 KB WRAM mirror**, so `0xFEFF48`
aliases WRAM offset `0xFF48` — **valid**. The crash handler's strict `0xFF0000–0xFFFFFF` check ignores
the mirror and mis-flags the normal arcade stack. **SP was not corrupt; not causal.** No upstream stack
corruption: the fault is a data-pointer read, and A5=0x00FF0000 (arcade base) is intact.

## Root cause
**Build-0308 `fg_boundary_install` computes package-data pointers from section counts/offsets that do not
match the Build-0308 compiler's emitted package layout, yielding an odd and out-of-range pointer that a
`movew (An)+` reads → ADDRESS ERROR at the first per-record install after gameplay entry.** This is a
**package-format / pointer-arithmetic disagreement** introduced by the Build-0308 layout change
(new fixed-B section `FG_BOUNDARY_FIXED_B_OFFSET=52732`, per-record map/upload sections, `484`/`854`
counts, `1854` identities, 49-cell sprite band, LUT scratch at word 5632). **Build 0307 survives** because
its package format and the runtime walk agreed (single per-record map/upload only, aligned). **Build 0308
fails** because the runtime section-stride/count arithmetic no longer matches the emitted multi-section
layout, so `a2`/`a3` leave their package (odd + far overrun).

## Suspects — status
- **Package layout / pointer-arithmetic mismatch:** **YES — primary** (a2 odd + a3 out-of-range prove it).
- **Odd/alignment bug:** YES (a2 odd) — a *symptom* of the section arithmetic; package data_offsets
  themselves are all even, so the odd byte comes from a mis-summed section stride, not an unaligned
  section base.
- **Stale generated pointer (relocation):** likely NO — A4=0x74058 matches the linked
  `fg_boundary_packages` symbol; the descriptor first-fields parse correctly. (Cody to confirm no
  absolute-immediate into the resized binary is stale.)
- **LUT scratch bug / frontend slot 1..63 / 49-cell sprite cache:** not the faulting instruction (fault
  is package-data walk). Sprite band relevant only if it feeds the same wrong count — Cody to check.
- **SP/stack corruption:** NO (mirror false positive).

## Remaining link (honest, bounded)
The exact mis-sized section field is localized to `fg_boundary_install`'s per-record walk
(fg_tile_cache.s: the `a2=a4+d4`, `a3=a2+(map+upload)*4`, and subsequent section advances near
runtime 0x727b8–0x72860) and the active-package index at WRAM `0x00FFB1FC`. Closing it needs a direct
diff of that runtime arithmetic against the compiler's emitted per-record section order/width/stride in
`compile_pc080sn_genesis.py` — a bounded, deterministic audit, not a guess.

## Cody Build-0309 fix (smallest correct)
1. **Reconcile the package section walk** in `fg_tile_cache.s` `fg_boundary_install` with the exact
   Build-0308 emitted layout in `compile_pc080sn_genesis.py`: every section count (map/upload/identity/
   remap), field width, and stride must match, and the active-record/package index (`0x00FFB1FC`) must be
   range-checked before use. Fix the mismatched stride/count (the one that overruns a3).
2. **Even-align every emitted package section** (pad map/upload/identity/remap to a 2-byte boundary) and
   have the compiler **assert** each `data_offset` and section base is even and within `len(binary)`.
3. **Runtime guard:** before each `movew (An)+` package read, assert the pointer is even and within
   `[fg_boundary_packages, fg_boundary_packages+FG_BOUNDARY_BINARY_LEN)`; on violation, fail deterministically
   rather than fault. (Diagnostic only — not a NOP/RTS of the real work.)
4. Files: `apps/rastan-direct/src/fg_tile_cache.s`, `tools/translation/compile_pc080sn_genesis.py`
   (emit layout + assertions). Binary layout changes (alignment padding) → regenerate boundary_packages.
   No no-black work, no scrolling, no collision, no B-design rollback.

## Do NOT roll back global-B
This is an **implementation defect** in the package walk, not a flaw in the fixed Level-1 854-B design
(proven from arcade semantics). Fix the arithmetic; keep single-load global-B, per-record A.

## Gameplay-entry regression gate (required for 0309+)
Build a project-owned MAME (`genesis`, not `megadriv`) harness that drives **boot → credit → Start →
READY → first residency install → controllable Level-1 gameplay** and survives N frames, asserting: no
Address/Bus Error, no crash handler, valid SP (mirror-aware), scene==1 gameplay reached, fixed-B install
completed, record-0 A install completed. Attract-only smoke is insufficient (it never reached the crash).
Inputs derived from the arcade FU1 playtrace / existing scripts — not requested from Tighe.
