# Andy — KF-028 Caller Trace: Source of Bad Glyph-Renderer Input at 0x3BD48

**Author:** Andy
**Date:** 2026-06-17
**Patched ROM:** `dist/rastan-direct/fixes/build_0077_kf028_input_shim_wiring/patched_rom.bin` (SHA `b63512abd4aa1e50a774442c44e0918233fc2d06625138c51f46f7125b5b5c1e`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No fix design (bounded recommendation at end only). No runtime probing.

Disassembly from `build/genesis_postpatch.disasm.txt` (PATCHED). Only the exception name, stack dump, and WRAM crash record are trusted (per prior triages).

---

## 1. Baseline statement

Prior triage `Andy_kf028_real_fault_triage.md` proved (from the WRAM crash record + IR `0x32C2`) that the fault is a word **write** at `0x0003BD66` (`movew %d2,%a1@+`) in the glyph renderer `0x3BD48`, with `a1 = descriptor[0] = 0x50205741`. The renderer + its table (`0x3BD7C`) + descriptors (`0x3BCxx–0x3C2xx`) are all below the `0x700C6` insertion point → unshifted, byte-identical patched-vs-baseline. This task closes the gap: which caller, what `d0`, and why the table/descriptor resolves to `0x50205741`.

---

## 2. Phase 1 — Callers/references of 0x3BD48

`0x3BD48` is reached only by direct `bsrw` (grep of `build/genesis_postpatch.disasm.txt`); no table/indirect/`pea`-`rts` route targets it. It is a heavily-used text routine — ~48 `bsrw 0x3bd48` sites across `0x3a534…0x3b8e4`. Each caller sets `d0` via an immediately-preceding `moveq #N,%d0` (a static constant). **STATICALLY_PROVEN.**

The title sub-state handler block (`0x3acae…0x3ace8`, reached from the title dispatcher) issues a run of them:
```
3acae: jsr 0x5a5de
3acb4: moveq #17,%d0 ; 3acb6: bsrw 0x3bd48   -> ret 3acba
3acba: moveq #63,%d0 ; 3acbc: bsrw 0x3bd48   -> ret 3acc0
3acc0: moveq #64,%d0 ; 3acc2: bsrw 0x3bd48   -> ret 3acc6
3acc6: moveq #65,%d0 ; 3acc8: bsrw 0x3bd48   -> ret 3accc   <-- matches stack breadcrumb
3accc: moveq #66,%d0 ; 3acce: bsrw 0x3bd48   -> ret 3acd2
... (67,68,69,70)
```

---

## 3. Phase 2 — Active caller for this crash

The renderer `0x3BD48` is a **leaf** (no internal `bsr`/`jsr`; `rts` at `0x3bd7a`). At the address-error fault, the SSP holds the 14-byte group-0 frame, and immediately above it is the return address pushed by the `bsrw` that called the renderer. The prior reliable stack dump shows **`0x0003ACCC`** as that return address.

`0x3ACCC` is the return address of the `bsrw 0x3bd48` at **`0x0003ACC8`**, whose `d0` was set by `moveq #65,%d0` at `0x3ACC6`. So the **active caller is `0x0003ACC8`, passing `d0 = 65 (0x41)`**. **STATICALLY_PROVEN** (caller instruction identified; return address matches the breadcrumb; renderer is a leaf so the top return address is the caller's). Path is consistent with the title sub-state handler at `0x3ACCC`/`0x3ACAE` (SR `0x2700` = inside VBlank ISR; KF-013).

---

## 4. Phase 3 — d0 source

`d0 = 65` comes directly from the hardcoded `moveq #65,%d0` at `0x3ACC6` — a **static immediate** in the arcade-translated title handler. It is **not** loaded from WRAM, not computed from title state/counters/flags, and not stale/uninitialized. The whole run `17, 63, 64, 65, 66, 67, 68, 69, 70` is a sequence of hardcoded `moveq` constants (this is the arcade's intended call sequence for drawing this title text row). **STATICALLY_PROVEN.**

Implication: this is **not** a "wrong/garbage `d0`" case (rules out U1). `d0 = 65` is exactly what the arcade code intends to pass.

---

## 5. Phase 4 — Table entry and descriptor

Renderer index path: `idx = d0 & 0x7F = 65`; entry address `= 0x3BD7C + 65*4 = 0x3BE80`.

- **`table[65]` @ `0x3BE80` = `0x0003C246`** (ROM long). **STATICALLY_PROVEN.**
- **Descriptor @ `0x3C246`:** first long (loaded into `a1` by `moveal %a0@+,%a1`) = bytes `50 20 57 41` = **`0x50205741`** — **exactly the recorded fault address.** **STATICALLY_PROVEN.** `0x50205741` is odd → the word write `movew %d2,%a1@+` address-errors.

`0x50205741` = ASCII `"P WA"`. The region `0x3C2xx` around it is plainly **text/string data** — e.g. `0x3C20A` = `53 45 4C 45 43 54` = `"SELECT"`, plus `"WARP"`, `"1P"`, `"2P"`, and runs of `0x20` spaces. So `table[65]` points **into the body of text data**, not at a descriptor header whose first long is a destination pointer.

This is not unique to index 65. The renderer's descriptor format (per the code) is `[long dest_ptr][word attr][glyph bytes…0]`, writing `(attr, glyph)` tilemap-word pairs to `(dest_ptr)+`. Checking other entries:
- `table[63]` @ `0x3BE78` = `0x0003C216`; first long there = `0x00003150` (even, but a low/invalid staging dest).
- `table[64]` @ `0x3BE7C` = `0x0003C232`; first long = `0x8C200000` (invalid dest).
- `table[0]` @ `0x3BD7C` = `0x0003BC98`; first long = `0x0B1E1E0C` (not a valid Genesis dest).

**None of the sampled descriptors carries a valid Genesis destination pointer in `descriptor[0]`.** Index 65 crashes only because its leading bytes happen to be odd; the others would write garbage to invalid even addresses without faulting. So the whole descriptor region is not in renderer-expected form (valid even Genesis staging/VRAM dest in `descriptor[0]`). **STATICALLY_PROVEN** (for the sampled entries).

---

## 6. Phase 5 — Upstream cause classification

### Primary: **U3 — Missing/incomplete translation** of the title/text-rendering descriptor subsystem.

The renderer at `0x3BD48` treats `descriptor[0]` as a destination pointer and writes `(attribute, glyph)` tilemap word-pairs there. For the title-string indices — and every sampled index — `descriptor[0]` is **not** a valid Genesis destination (it is ASCII text / encoded data). The descriptor table (`0x3BD7C`) and descriptor data (`0x3BCxx–0x3C2xx`) are arcade-origin, copied verbatim (unshifted), and have not been put into a Genesis-renderable form with valid destination pointers. The crash is the first hard manifestation, surfacing now that the KF-028 fix advanced execution into this title text path; index 65's leading bytes (`"P WA"`, odd) turn a latent garbage-write subsystem into an address error.

**This is not U1** (`d0 = 65` is the intended hardcoded constant, not a wrong/stale value) and **not a layout shift** (table/descriptors unshifted ROM, identical to baseline).

### Alternative: **U2 — Malformed/mis-targeted descriptors.** Framed differently, the table entries for these indices point into text-string bodies rather than at descriptor headers (so `descriptor[0]` is text). Distinguishing U3 ("dest pointers were never translated/built for Genesis") from U2 ("table mis-targets / descriptor data is wrong") cannot be settled from the patched binary alone — it needs the descriptor-build provenance or the arcade reference behavior (see §7).

(Both U3 and U2 are downstream-data problems in the newly-reached title text path — consistent with the prior triage's Outcome B. Neither is a fix-caused layout shift.)

---

## 7. Phase 6 — Bounded recommendation

**Determine the descriptor/table provenance for the title-string indices** (bounded to the `0x3BD7C` table + the `0x3BCxx–0x3C2xx` descriptor region):
1. In the build/translation tooling and any text/descriptor source or generator, find how the `0x3BD7C` table and its descriptors are produced, and specifically how `descriptor[0]` (the destination) is meant to be set for the Genesis port — i.e., whether a translation/relocation step that should convert arcade text-RAM destinations into Genesis staging/VRAM addresses exists and ran for this data.
2. Cross-check the arcade reference (`build/maincpu.disasm.txt` at arcade `0x3bb48` = Genesis `0x3bd48 − 0x200`, and the arcade table/descriptors) for how `descriptor[0]` resolves there — confirming whether the arcade has valid destinations that the Genesis port failed to translate (→ U3) or whether the table/descriptor bytes are themselves mis-targeted (→ U2).

This pins U3-vs-U2 and identifies the exact translation/data step to fix. Do **not** run a +4 absolute-reference audit (no Outcome-A evidence). Do **not** broaden into a general title-path survey.

(Separately, as already recommended: Cody should fix the two crash-handler defects — the `%d2`-clobber display bug and the register-save clobber — so future crash reports are trustworthy. Independent of this game-data bug.)

---

## 8. KNOWN_FINDINGS impact

**Option C — proposed KF-028 refinement** (the caller trace has now landed; full chain known). Andy proposes; Cody applies after Tighe ack. Proposed addition to KF-028:

> The KF-028 wiring advanced execution into the title text path, where the glyph renderer `0x3BD48` faults: title sub-state handler `0x3ACC8` calls it with `d0 = 65`; `table[65]` (`0x3BD7C+65*4 = 0x3BE80`) = `0x0003C246`, which points into ASCII text data; `descriptor[0]` there = `0x50205741` ("P WA"), loaded as the destination pointer, causing the odd-address word write at `0x3BD66`. The descriptor table/data (`0x3BD7C`, `0x3BCxx–0x3C2xx`) is unshifted arcade-origin ROM and carries no valid Genesis destination pointers — a missing/incomplete title-text translation (U3; possibly U2), not a layout shift. Exact U3-vs-U2 provenance pending the descriptor-build/arcade-reference check.

Confidence: the full fault chain (caller → `d0=65` → `table[65]=0x3C246` → `descriptor[0]=0x50205741` → fault) is **STATICALLY_PROVEN**; the U3-vs-U2 root is **WORKING_HYPOTHESIS** pending §7. BUILD_SPECIFIC. Cross-ref KF-013.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; the downstream title-text crash chain is now fully traced to a descriptor-data/translation gap; no status change pending the provenance check).
- Closed issues touched: NONE. New issues opened: NONE (title-text descriptor translation gap + the two crash-handler defects tracked via these triages; open formal issues if Tighe/Cody prefer). Issues closed: NONE. Deferred: NONE.

## STOP triggered

NO.
