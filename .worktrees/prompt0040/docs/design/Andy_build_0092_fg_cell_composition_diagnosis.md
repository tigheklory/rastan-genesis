# Andy — Build 0092 FG Cell-Composition Diagnosis

**Author:** Andy
**Date:** 2026-06-22
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin` (SHA `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. Fix locus + shape only; no implementation.

Address labels (Rule 3): `runtime_genesis_pc` = patched-ROM offset / runtime PC; `WRAM` = Genesis work RAM. `build/genesis_postpatch.disasm.txt` shares the ROM mtime and is the Build 0092 image.

---

## Phase 0 — Baseline statement

**Relevant priors:** KF-028 (input shim / title-text / OPEN-016 producer→staging — STRONG; this task diagnoses the now-runtime-proven zero-cell output of that chain), KF-013/KF-011/KF-010 (VBlank producer/plane structure — STRONG, context), KF-004/006 (PC↔offset — CONFIRMED).
**Rediscovery-Hazard HIGH touched:** KF-028 (extended), KF-013/011/010 (respected). None contradicted.
**Deferred-appendix:** none.
**Task classification:** EXTENDING (KF-028 / OPEN-016 — refines to the proven compose defect).
**Open/Closed issues touched:** OPEN-016 (active — live gap = zero-cell composition), OPEN-001 (active — graphics still fail), OPEN-015 (context).
**Contradiction of CONFIRMED/STRONG KF:** NONE. (The "text-writer hooks reported working" premise is a task premise, not a KNOWN_FINDINGS entry; static analysis refutes it — invited by the prompt, not a §0.4 KF contradiction.)
**Architecture compliance:** CONFIRMED. The fix is a register-preservation correctness change in an arcade-called helper; no Genesis control-flow ownership.

---

## Phase 1 — Disassembly of the helper region (`0x707BC..0x70816` + subhelpers)

```
; .Ltw_store_from_components_at_a2  (glyph hook AND text writers enter here)
707bc: 6100 0008      bsrw 0x707c6        ; .Ltw_compose_d1_from_d0_d2  -> d1 = composed cell
707c0: 6100 0022      bsrw 0x707e4        ; .Ltw_store_d1_at_a2         -> store d1
707c4: 4e75           rts

; .Ltw_compose_d1_from_d0_d2
707c6: 3e00           movew %d0,%d7
707c8: 0247 3fff      andiw #0x3fff,%d7
707cc: de47           addw  %d7,%d7
707ce: 3e33 7000      movew %a3@(0,%d7:w),%d7   ; %d7 = tile_vram_lut[d0]  <-- TILE half loaded into d7
707d2: 3202           movew %d2,%d1
707d4: 0241 01ff      andiw #0x1ff,%d1
707d8: 3401           movew %d1,%d2            ; d2 = raw attr (& 0x1ff)
707da: 6100 ff76      bsrw 0x70752            ; .Ltw_translate_attr   <-- CLOBBERS %d7, sets d2=attr_lut[...]
707de: 3207           movew %d7,%d1            ; d1 = %d7  <-- reads CLOBBERED d7 (tile gone)   *** LOSS ***
707e0: 8242           orw   %d2,%d1            ; d1 = (clobbered d7) | attr
707e2: 4e75           rts

; .Ltw_translate_attr  (attr lookup) — uses %d7 as scratch, no save/restore
70752: 3202           movew %d2,%d1
70754: 0241 0003      andiw #3,%d1
70758: 3e02           movew %d2,%d7   ; \
7075a: e04f / 7075c: ec4f / 7075e: 0247 0001 / 70762: e54f / 70764: 8247   ;  } attr bit -> d1
70766: 3e02           movew %d2,%d7   ; \  (clobbers d7 again)
... 70772: 8247                       ;  }
70774: 3e02           movew %d2,%d7   ; \  (final d7 = ((d2>>13)&1)<<4)
... 70780: 8247                       ;  }
70782: d241           addw  %d1,%d1
70784: 3435 1000      movew %a5@(0,%d1:w),%d2  ; d2 = attr_lut[composed attr index]
70788: 4e75           rts                       ; on exit %d7 = attr residue, NOT the tile

; .Ltw_store_d1_at_a2  (range check + offset + store)
707e4: 48e7 2700      moveml %d2/%d5-%d7,%sp@-  ; saves d2,d5,d6,d7 (does NOT touch d1)
707e8..707fe          ; %d0=a2&0xFFFFFF; reject if <0xC08000 or >=0xC0C000  (FG range gate)
70800: 0480 00c08000  subil #0xc08000,%d0
70806: e488           lsrl #2,%d0
70808..70812          ; %d6 = col (&0x3F) ; %d5 = row (>>6 &0x1F)
70816: 6100 ff72      bsrw 0x7078a            ; .Ltw_store_cell
7081a: 4cdf 00e4      moveml %sp@+,%d2/%d5-%d7
7081e: 4e75           rts

; .Ltw_store_cell
7078a: 3405 / 7078c: ef4a   ; d2 = row<<7
7078e: 3e06 / 70790: d447 / 70792: d447   ; d2 += col*2
70794: 3d81 2000      movew %d1,%fp@(0,%d2:w)  ; STORE composed cell d1 into staged_fg_buffer[%a6]
70798..707a0          ; set fg_row_dirty bit
707a6: 4e75           rts
```

`%d1` carries the composed cell from `.Ltw_compose_d1_from_d0_d2` (0x707c6) unchanged through `.Ltw_store_d1_at_a2`/`.Ltw_store_cell` to the store at `0x70794`. So the stored cell == the value `%d1` held at `0x707e2`.

---

## Phase 2 — Register lifecycle (one cell)

| Reg | At compose entry (`0x707c6`) | After `0x707ce` | After `.Ltw_translate_attr` (`0x707da`) | At store (`0x70794`) |
|---|---|---|---|---|
| `%d0` | tile/glyph index (caller) | index*2 scratch | (saved/restored by store) | — |
| `%d2` | raw attr word (caller) | masked attr (`&0x1ff`) | **attr_lut[idx]** (overwritten, 0x70784) | offset scratch |
| `%d7` | — | **tile_vram_lut result (TILE)** | **CLOBBERED** → `((d2>>13)&1)<<4` | (restored copy of clobbered value) |
| `%d1` | — | — | — (set at `0x707de`) | **composed cell** = clobbered‑`%d7` \| `%d2` |
| `%a2`/`%a3`/`%a5`/`%a6` | dest / tile-LUT / attr-LUT / staged_fg_buffer | preserved | preserved | used |

The tile value lives in `%d7` from `0x707ce` (source line 638) and is required at `0x707de` (source line 645). `.Ltw_translate_attr` overwrites `%d7` in between.

---

## Phase 3 — Pinpoint the loss

**Loss instruction: `runtime_genesis_pc 0x707DE` — `movew %d7,%d1` (`3207`)** = `tilemap_hooks.s:645` `move.w %d7, %d1`.

Proof (disassembly + register lifecycle, not symptom):
- `0x707ce` (`tilemap_hooks.s:638`) loads the tile half into `%d7` (`tile_vram_lut[d0]`).
- `0x707da` (`tilemap_hooks.s:643`) calls `.Ltw_translate_attr`, whose body (`0x70752`, `tilemap_hooks.s:578-605`) uses `%d7` as scratch three times (`move.w %d2,%d7` at lines 582/589/596) with **no save/restore** (entry has no `movem`; exit `%d7 = ((d2>>13)&1)<<4`).
- `0x707de` (`tilemap_hooks.s:645`) then reads `%d7` into `%d1` — the **clobbered** attr-residue, not the tile.
- `0x707e0` (line 646) ORs in `%d2` = `attr_lut[...]`. The stored cell = `attr_residue | attr_lut_value`; the tile-index bits are absent. The runtime probe (`d7_tile=0x001F` at `0x707d2` → `0x00` at `0x707e0`) corroborates exactly this clobber. STATICALLY_PROVEN.

---

## Phase 4 — Glyph-hook vs known-good text-writer contract comparison (MANDATORY)

**Both call sites reach the identical compose path.** From `tilemap_hooks.s`:
- Glyph hook `.Lgr_store_cell:1088` → `bsr .Ltw_store_from_components_at_a2`.
- `.Ltw_write_pair_same:672` → `bsr .Ltw_store_from_components_at_a2` (×2, lines 675/678).
- Text writers `genesistan_hook_text_writer_3c550:1116` and `_3c586:1209/1223` → `bsr .Ltw_write_pair_same`.
- `.Ltw_store_from_components_at_a2:629` → `.Ltw_compose_d1_from_d0_d2:634` → `.Ltw_translate_attr:578` (the `%d7` clobber).

**Helper register contract** at `.Ltw_store_from_components_at_a2` entry: `%d0`=tile/glyph index, `%d2`=raw attr word, `%a3`=`genesistan_pc080sn_tile_vram_lut`, `%a5`=`genesistan_pc080sn_attr_lut`, `%a6`=`staged_fg_buffer`, `%a2`=dest C-window address. The tile is carried internally in `%d7` and the contract **assumes `%d7` survives the `.Ltw_translate_attr` call** — which it does not.

**Do the two hooks enter at the same label?** YES — both via `.Ltw_store_from_components_at_a2` → `.Ltw_compose_d1_from_d0_d2`. The glyph hook does not take a different/wrong path; its register setup (`%a3`/`%a5`/`%a6`, `%d0`, `%d2`) matches the text-writer setup (Build 0091 fix verified).

**Would the known-good hooks survive the glyph hook's path?** NO. They take the identical path. `.Ltw_translate_attr` clobbers `%d7` for every caller, so the tile half is lost for the text writers too. **The "text-writer hooks reported working" premise is refuted by static analysis**: per the code they cannot render correct tiles through this path. (They may *appear* to show output only where their `attr_lut` value is nonzero, producing visible-but-wrong cells; the glyph hook's `attr_lut` value is zero, yielding fully-zero cells = invisible.) USER MUST VERIFY the text-writer visual output against this — they are not immune to the defect.

This is therefore not a glyph-hook-specific contract mismatch (F1), not a wrong entry label (F2), not a register the caller failed to load (P-class for the prior task). It is a register-preservation defect in the shared compose, triggered by the attr lookup clobbering the tile register.

---

## Phase 5 — Fix-locus classification: **F4 — attr lookup clobbers the tile register**

`.Ltw_translate_attr` (`0x70752`, `tilemap_hooks.s:578`) overwrites `%d7` — the tile-carrying register — before `.Ltw_compose_d1_from_d0_d2` reads it at `0x707de` (`tilemap_hooks.s:645`). Because the compose path is shared, this is simultaneously a shared-body defect (the F3 clause), and per Phase 4 the text-writer hooks are **not** exempt — the claim that they work is revised. The precise mechanism is F4 (attr-helper clobbers the tile register before compose).

---

## Phase 6 — Fix shape (no implementation)

**Fix locus:** `.Ltw_compose_d1_from_d0_d2` (`tilemap_hooks.s:634` / `0x707C6`) and/or `.Ltw_translate_attr` (`tilemap_hooks.s:578` / `0x70752`).

**Minimal corrective shape — two options:**
- **Option A (byte-neutral, preferred): register swap.** Change `.Ltw_translate_attr` to use a scratch register other than `%d7` (e.g. `%d3`) for the three `move.w %d2,%dN` bit-extractions (lines 582/589/596 and their shifts), leaving `%d7` (the tile) intact. The follow-on fix MUST first confirm the chosen scratch register is free across every `.Ltw_store_from_components_at_a2` caller's contract (the glyph hook saves `%d0-%d7`; the text-writer hooks' saved-register sets must be checked). If a free register exists, this is a pure register rename → **0 byte delta → no invariant shift.**
- **Option B (fallback): preserve `%d7` across the call.** In `.Ltw_compose_d1_from_d0_d2`, push the tile before `bsr .Ltw_translate_attr` and pull it into `%d1` after — e.g. `move.w %d7,-(%sp)` before line 643; replace line 645 `move.w %d7,%d1` with `move.w (%sp)+,%d1`. **+2 to +4 bytes** in the Genesis-native helper region.

**Expected byte-size / invariant impact:** Option A: none. Option B: a +2/+4-byte growth in the `0x70xxx` helper region shifts all subsequent `runtime_genesis_pc` addresses and the `total_genesis_bytes_covered` invariant (currently `0x17CAF0`) by the delta, and any absolute references into shifted helpers must be re-relocated (same class as the OPEN-016 / KF-028 relocation). The follow-on Cody fix should prefer Option A (byte-neutral register swap) to avoid invariant churn, falling back to Option B with invariant pre-authorization if no free scratch register exists. Do not modify the shared store/range/offset code (verified correct).

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-016 (active — zero-cell root cause proven; fix locus named; not closed), OPEN-001 (active — narrowed to this compose defect; not closed), OPEN-015 (context only).
- New issues opened: NONE (the text-writer-hooks-also-affected finding is folded into this diagnosis; propose a formal OPEN entry only if Tighe/Cody prefer to track the text-writer visual re-verification separately).
- Issues closed: NONE.
- Intentionally deferred: Start→C→A crash, OPEN-015 crash-handler fix, BG producer path, the `0x3ACEA` direct writer, sprites/palette/scroll.

## KNOWN_FINDINGS impact

**Option C — Proposed update to KF-028.** Cited entry: KF-028 (input-shim/title-text/OPEN-016 producer→staging). Proposed edit (refinement; conservative confidence; Tighe/Chad Sr. approve before merge):

> Build 0092 zero-cell root cause: the shared FG cell-composition helper `.Ltw_compose_d1_from_d0_d2` (`runtime_genesis_pc 0x707C6`) loads the tile into `%d7` then calls `.Ltw_translate_attr` (`0x70752`), which uses `%d7` as scratch with no save/restore; the compose then reads the clobbered `%d7` at `0x707DE` (`tilemap_hooks.s:645`), so the tile half is lost and stored cells = attr-residue|attr_lut (observed 0x0000). This shared path is used by both `genesistan_hook_glyph_renderer_3bd48` and the `genesistan_hook_text_writer_*` hooks (via `.Ltw_write_pair_same`), so the text writers are not exempt. Fix: preserve the tile register across the attr lookup (byte-neutral register swap preferred). Confidence STRONG (disassembly + register lifecycle proven; runtime-corroborated).

## STOP triggered

NO.
