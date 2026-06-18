# Andy — KF-028 Title Text Descriptor Provenance: U3 vs U2

**Author:** Andy
**Date:** 2026-06-18
**Patched ROM:** `dist/rastan-direct/fixes/build_0077_kf028_input_shim_wiring/patched_rom.bin` (SHA `b63512abd4aa1e50a774442c44e0918233fc2d06625138c51f46f7125b5b5c1e`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No fix design (bounded recommendation only). No runtime probing. No +4 absolute-reference audit.

Disassembly from `build/genesis_postpatch.disasm.txt` (PATCHED) and `build/maincpu.disasm.txt` (ARCADE). Genesis↔arcade map: Genesis = arcade + 0x200 (KF-006, `whole_maincpu_relocated`).

---

## 1. Baseline statement

Prior caller trace proved the crash chain (caller `0x3ACC8` `d0=65` → `table[65]=0x3C246` → `descriptor[0]=0x50205741` → odd-address write fault at `0x3BD66`). The open question was U3 (missing Genesis translation) vs U2 (malformed/mis-targeted data). This task resolves it by comparing arcade vs Genesis data and checking the relocation tooling.

---

## 2. Proven caller-to-fault chain (recap)

`0x3ACC6 moveq #65,%d0` → `0x3ACC8 bsrw 0x3bd48` → renderer indexes `table @ 0x3BD7C`, `idx=65`, `table[65] @ 0x3BE80 = 0x0003C246` → `a1 = *(0x3C246) = 0x50205741` → `0x3BD66 movew %d2,%a1@+` address-errors (odd a1). All STATICALLY_PROVEN.

---

## 3. Phase 1 — Genesis table/data provenance

The renderer (`0x3BD48`), table (`0x3BD7C`), and descriptors (`0x3BCxx–0x3C4xx`) are all part of the arcade ROM blob copied to Genesis at +0x200 (`whole_maincpu_relocated`). The descriptors **were** relocated correctly:
- Genesis `0x3BE98` (= arcade `0x3BC98` + 0x200) = `00 C0 8F 4C | 00 00 | "BEST…"` → `descriptor[0] = 0x00C08F4C`. STATICALLY_PROVEN.
- Genesis `0x3C446` (= arcade `0x3C246` + 0x200) = `00 C0 91 4C | 00 00 | "OTHERW…"` → `descriptor[0] = 0x00C0914C`. STATICALLY_PROVEN.

Both relocated descriptors are **well-formed**: a valid even `0x00C0xxxx` destination, a `0x0000` attribute word, then ASCII text — exactly the `[long dest][word attr][bytes…0]` format the renderer expects.

**But the descriptor-pointer table at `0x3BD7C` was NOT relocated.** Its entries are absolute longwords still holding **arcade** descriptor addresses (`0x0003BC98`, `0x0003BCA6`, … `0x0003C246`, …) — identical to the arcade table (Phase 2). So `table[65] = 0x0003C246` points 0x200 **below** the real relocated descriptor at `0x3C446`. Dereferencing Genesis `0x3C246` instead reads the relocation of arcade `0x3C046` — which is the text body `…"P WA"…` (`0x50205741`, odd) → fault. STATICALLY_PROVEN.

**Tooling gap:** `tools/translation/postpatch_lenient.py` performs `rom_absolute_call_relocation` / `absolute_rom_target_relocation` — it relocates absolute targets found in **instruction operands** (jsr/jmp), rewriting `source_target → source_target + relocation_delta`. It does **not** relocate absolute longword pointers embedded in **data tables**. The descriptor-pointer table at `0x3BD7C` is such a data table, so its entries were left at their pre-relocation arcade values. DOCUMENTED (tool source) + INFERRED (the table is data, outside the operand-scan path).

(The arcade code finds the table via PC-relative `lea %pc@(0x3bd7c),%a0`, which relocates automatically — which is why the renderer reaches the table at all. Only the table's absolute *contents* are stale.)

---

## 4. Phase 2 — Arcade reference comparison

Arcade renderer `0x3BB48` is byte-identical in structure to Genesis `0x3BD48` (same `andiw #127`/`lslw #2`/`lea`/`moveal`/write loop). Arcade table at `0x3BB7C`:
- Arcade `table[0]` (`0x3BB7C`) = `0x0003BC98`; Genesis `table[0]` (`0x3BD7C`) = `0x0003BC98`. **IDENTICAL.**
- Arcade `table[65]` (`0x3BC80`) = `0x0003C246`; Genesis `table[65]` (`0x3BE80`) = `0x0003C246`. **IDENTICAL.**

Arcade descriptors (at the addresses the arcade table points to):
- Arcade `0x3BC98` = `0x00C08F4C | 0x0000 | "BEST…"` (valid dest).
- Arcade `0x3C246` = `0x00C0914C | 0x0000 | "OTHER…"` (valid dest) — the real idx-65 descriptor.

So in the **arcade**, `table[65] = 0x3C246` correctly points to a well-formed descriptor (dest `0x00C0914C`). In the **Genesis** image, that same descriptor content was relocated to `0x3C446`, but the table still says `0x3C246` → it reads the wrong (un-relocated-target) location. The arcade data is valid; the Genesis defect is purely the un-relocated table pointers.

---

## 5. Phase 3 — Descriptor format interpretation

Confirmed identical on both sides: `descriptor = [long dest_ptr][word attr][byte glyph/text … 0]`. The renderer writes `(attr, glyph)` word-pairs to `(dest_ptr)+`. `dest_ptr` is an even `0x00C0xxxx` address (VDP/tilemap-region destination), **not** text and **not** a ROM address. Because `dest_ptr` is a hardware-region address (outside the `0x0–0x5FFFF` ROM relocation window), it correctly is **not** +0x200-relocated and is identical arcade↔Genesis. Only the table's ROM-range pointers (`0x3Bxxxx–0x3C2xx`) require +0x200 relocation, and that is what was missed.

(Whether writing to `0x00C0xxxx` renders correctly on Genesis — VDP port vs the arcade PC080SN/text path — is a separate downstream rendering-correctness question; it is not this crash. This crash is solely the odd-address fault from the stale table pointer.)

---

## 6. Phase 4 — U3 vs U2 classification

### **U3 — Missing/incomplete Genesis translation.**

The table and descriptors are **valid arcade-origin data**: the descriptors are well-formed with valid even destinations, and the table is a correct absolute-pointer list. The descriptors were relocated +0x200 with the blob. The **only** defect is that the absolute descriptor-pointer table at Genesis `0x3BD7C` was **not** relocated by the +0x200 identity offset — a gap in `postpatch_lenient.py`, which relocates absolute *instruction-operand* targets but not absolute pointers embedded in *data tables*.

This is **not U2** (data is not malformed/mis-targeted; arcade and relocated-Genesis descriptors are valid and correctly placed). It is **not** a +4 layout shift, and **not** U1 (`d0=65` is the intended hardcoded immediate). STATICALLY_PROVEN for the data; DOCUMENTED+INFERRED for the tool gap.

---

## 7. Phase 5 — Bounded recommendation

**Exact fix locus:** the absolute descriptor-pointer table at Genesis ROM offset `0x3BD7C` — its entries (each an absolute arcade descriptor address in `0x0003Bxxx–0x0003C2xx`, indexed up to `idx 127` → table spans `0x3BD7C..~0x3BF7C`, 128 longwords) must be relocated by **+0x200** so each points to the already-relocated descriptor (e.g. `table[65]: 0x0003C246 → 0x0003C446`, dest `0x00C0914C`, even → no fault).

**Recommended next task (Cody, investigation→implementation, do not over-design here):**
1. Relocate the `0x3BD7C` descriptor-pointer table by +0x200 per entry, via the `rastan_direct_remap.json` / postpatch mechanism (a data-pointer-table relocation entry), or by extending the relocation pass to cover this table. Determine the exact table length first (entry count / terminator).
2. **Survey for other absolute data-pointer tables** in the relocated arcade blob with the same un-relocated-pointer gap — since `postpatch_lenient.py` relocates only instruction operands, any other embedded absolute-pointer data table is similarly stale and a latent crash. This is the higher-leverage half: the title-text table is one instance of a general translation gap.

(Separately, still outstanding from prior triages: Cody fix the two crash-handler defects — `%d2`-clobber display bug and register-save clobber.)

---

## 8. KNOWN_FINDINGS impact

**Option C — proposed KF-028 refinement** (root now classified; Andy proposes, Cody applies after Tighe ack). Proposed addition to KF-028:

> Root cause of the KF-028 patched-ROM address-error crash: the absolute descriptor-pointer table at Genesis ROM offset `0x3BD7C` (used by the glyph/string renderer `0x3BD48`) was not relocated by the +0x200 identity offset. Its entries still hold arcade descriptor addresses (e.g. `table[65]=0x0003C246`), pointing 0x200 below the correctly-relocated descriptors (real idx-65 descriptor at Genesis `0x3C446`, dest `0x00C0914C`). The renderer therefore dereferences text data (`0x50205741`) as a destination and faults. The descriptors themselves are valid arcade-origin data, correctly relocated; only the table pointers are stale. Mechanism: `postpatch_lenient.py` relocates absolute instruction-operand targets but not absolute pointers embedded in data tables (U3, missing-translation). Classification: STRONG/CONFIRMED (data proven; tool-gap documented).

Consider (do not create here) whether the **general** finding — "absolute data-pointer tables in the relocated arcade blob are not +0x200-relocated by the postpatch" — warrants its own GLOBAL KF, pending the §7 survey of other tables.

---

## 9. Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; the title-text crash root cause is fully identified as an un-relocated descriptor-pointer table — a translation-tool gap; no status change pending the fix + broader table survey).
- Closed issues touched: NONE. New issues opened: NONE (translation-relocation gap + the two crash-handler defects tracked via these triages; open formal issues if Tighe/Cody prefer). Issues closed: NONE. Deferred: NONE.

## 10. STOP triggered

NO.
