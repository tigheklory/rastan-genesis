# Performance Push — OPT-003 landing, VRAM reclaim legality, Layer-A recompile plan

**Agent:** Andy · **Date:** 2026-09-03 · **Status:** OPT-003 **blocked** (real defect, not fragility;
tooling-limited); VRAM-reclaim **legality audited** (pattern-reclaim legal, nametable repack illegal);
Layer-A recompile is a **bounded, ready-to-execute** compiler/runtime change (not yet built).

---

## 1. Architecture compliance
Arcade remains execution authority; no new software chip mirrors / allocator / LRU / visibility scan
introduced. Normal-frame lookup stays O(1). All proposed changes are offline-compiler + fixed-boundary.

## 2. Phase 0 classification
**EXTENDING.** Priors: OPT-003 palette equivalence (512/0) stands; Build-0341 BSS/workram root cause is
**withdrawn** (matched-config: 0 BSS shift); the KF/OPTIMIZATIONS records already carry the corrected state.
No contradiction beyond the one already logged. VRAM map (0xD000 gap + unused Window) is from the prior
VRAM analysis and re-verified here against the VDP alignment rules.

## 3. OPT-003 landing — BLOCKED (Stage A premise refuted)
Stage A directs a "narrow settle-condition gate fix" on the belief that OPT-003's cell fails because the
sample precedes settling. **That is disproven by direct frame-by-frame evidence** (prior task, re-confirmed):
- `active_lut[0x034C]` (WRAM 0xFF6820) is written **0x04E0 at frame 327**, then **clobbered to 0x0000 at
  the frame-328 epoch-change install** in OPT-003 only, and stays 0 through frame 336 (8+ stable frames).
- The settle-condition fix was already tested (assert at install+8 and install+200) — OPT-003 still FAILS.
  So no "one completed production boundary" condition lands it.
- Package data is byte-identical (49732 B), the package pointer is correctly relocated (no stale address
  survives), BSS is identical, installer code is identical modulo correct operand relocation.
- The exact clobbering instruction is **not capturable** here: DRC bypasses Lua write-taps; a headless
  `-debug -debugscript` watchpoint didn't fire; the `-nodrc` interpreter is too slow to reach the frame in
  budget (timed out / X-server kill). `cpu.debug` is unavailable.

Therefore OPT-003 cannot be landed without either weakening the gate to ignore code 0x034C (the prompt
forbids this) or fixing the real clobber (whose instruction the available tooling cannot reveal). **No fake
landing was performed.** The open, decisive question remains: does the clobber occur in *natural gameplay*
or only under the gate's *synthetic installer injection*? Answering it needs either interpreter-speed
tracing or scripted natural-scroll input — both currently tooling-blocked.

## 4. VRAM reclaim — legality audit (Stage B)
Target regions: `0xD000–0xDFFF` (4 KB / 128 slots) + unused Window `0xF000–0xF7FF` (2 KB / 64 slots) =
**192 pattern slots**.

- **Nametable repack is ILLEGAL.** Plane A base (reg 2) is **8 KB-aligned** in H40 (bits 5–3 «0x38» << 10),
  so its only legal bases near here are 0xC000 and 0xE000 — **not** 0xD000. The `0xD000` gap therefore
  cannot be closed by moving a nametable. (Plane B reg 4 is also 8 KB-aligned; Window reg 3 is 2 KB-aligned;
  SAT reg 5 is at 0xF800; HScroll reg 13 at 0xFC00.)
- **Pattern reclaim is LEGAL.** Tile patterns are 32-byte addressable (11-bit tile index 0–2047). The holes
  map to tile slots **1664–1791** (0xD000–0xDFFF) and **1920–1983** (0xF000–0xF7FF), both < 2048 and both
  disjoint from every nametable/SAT/HScroll region. They can hold Layer-A (or sprite) patterns referenced by
  normal tile indices. So the reclaim is real, but as **disjoint pattern slots**, not a contiguous window.
- Do **not** enlarge SAT (80-sprite hardware cap; no benefit) — confirmed.

Net: Layer-A pattern capacity 484 → **676** (484 + 128 + 64), as **three disjoint ranges**
[855–1338] ∪ [1664–1791] ∪ [1920–1983].

## 5. Sprite same-code residency sharing — confirmed YES
The native emit (`.Lnq_emit_entry` → `.Lnq_lookup_loop`) scans `sprite_tile_resident_code` for the piece's
code; on a match it **reuses the resident slot** (`.Lnq_hit`), else reserves a new one via
`worklist_entry_for_slot`. So artwork residency is **code-keyed**: two lizard men sharing one artwork code
reference **one** resident 16×16 cell from multiple SAT entries. Actor count does **not** imply duplicate
pattern storage. Current sprite pattern capacity: slots 1339–1535 = 197 8×8 slots / 49 complete 16×16 cells.
No duplicated-by-actor VRAM allocation observed. **No sprite-residency redesign needed.**

## 6. Layer-A recompile — ready-to-execute plan (Stage C), NOT yet built
The offline compiler `tools/translation/compile_pc080sn_genesis.py` currently models Plane-A capacity as ONE
contiguous range with hard assertions:
- `BOUNDARY_PHASE1_EPOCH_CAPACITY = 484` (line 102)
- `a_slot_first = b_last+1` (855); assert `(a_slot_first,a_slot_last)==(855,1338)` (line 366) and
  `a_slot_last < SPRITE_TILE_BASE=1339` (line 368)
- free-slot pool `range(a_slot_first, a_slot_last+1)` (line 545)

Exact change points to use the 676-slot disjoint capacity:
1. Compiler: replace the single `[855,1338]` window with the disjoint slot **set** `[855–1338] ∪ [1664–1791]
   ∪ [1920–1983]`; raise the epoch capacity to 676; relax the (855,1338)/sprite-overlap asserts to validate
   the disjoint set instead; drive epoch selection + free-pool from the set.
2. Runtime/constants: `FG_BOUNDARY_SLOT_FIRST/COUNT` and the epoch gate's slot-validity check
   (`slot >= SLOT_FIRST+SLOT_COUNT` ⇒ invalid) assume a contiguous window — update them to accept the
   disjoint valid-slot set (the installer already writes `active_lut[code]=slot` for arbitrary slots; the
   tile-DMA computes VRAM addr = slot·0x20, valid for slots < 2048).
3. Re-verify: transition-retention gate + seven-epoch gate must pass with the new packing; expect fewer /
   lighter transition uploads (union 1294 through a 676 window vs 484 → fewer swaps), which is the actual
   DMA-halt reduction. Within-epoch DMA must remain 0; runtime allocator/search/LRU must remain false.

This is a bounded multi-file change (compiler + a few constants + re-verify), independent of the OPT-003
blocker. It is the real performance win (fewer semantic transition DMAs → shorter VBlank servicing → less
active-display CRAM-dot spill). It was **not** started in this task to avoid a large speculative surgery at
the tail of an already-long investigation without Tighe's go-ahead on scope.

## 7. Builds produced
None. Counter unchanged at 341. No numbered artifact; nothing faked.

## 8. Performance evidence
None measured (no landed build). The expected win is structural (Layer-A window +40% → fewer transition
DMAs), to be measured via `_d` band + transition totals once Stage C builds.

## 9. Deferred / next
Stage C (Layer-A 676-slot recompile) is the highest-value next cut and is ready. OPT-003 remains blocked on
tooling for the clobber-PC / natural-gameplay question.
