# Andy — Build 0091 Helper Crash Triage (OPEN-016 Part 2)

**Author:** Andy
**Date:** 2026-06-19
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0091.bin` (SHA `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No runtime probing. No implementation. Bounded recommendation only.

Address-space labels (Rule 3): `runtime_genesis_pc` = patched-ROM file offset / runtime PC (KF-004); `HW` = hardware address; `WRAM` = Genesis work RAM.

---

## Phase 0 — Baseline statement

**Relevant priors from KNOWN_FINDINGS:**
- KF-028 (input shim / title-text U3 arc; OPEN-016 Part 1 relocated the descriptor table; Part 2 added the glyph hook).
- KF-013 (text dispatch fires inside VBlank — consistent with `SR=0x2700`, IPM 7).
- KF-010 (FG → Plane A; the staging target here is `staged_fg_buffer`).
- KF-004 (runtime PC = ROM file offset), KF-006 (identity_offset 0x200).

**Rediscovery Hazard HIGH findings touched:** KF-028, KF-013, KF-004 — none contradicted.

**Deferred-appendix entries relevant:** none.

**Task classification:** EXTENDING (refines KF-028 / OPEN-016 with the Build 0091 immediate-crash mechanism).

**Open/Closed issues touched:** OPEN-016 (active — this triage informs whether the Part 2 hook needs revision), OPEN-015 (context — crash-handler display + register-save defects; the WRAM record was the reliable source), OPEN-001 (context — rendering).

**Contradiction of CONFIRMED/STRONG finding:** NONE.

**Architecture compliance:** CONFIRMED. The glyph hook is a helper (arcade-called body replacement of arcade `0x03BB48` / runtime `0x03BD48`, returns RTS, translates a hardware destination PC080SN→FG staging). The recommended fix adds register setup matching existing helpers — production-intent, no scaffolding, no Genesis-owned lifecycle.

(Reliable crash data is the WRAM record; the on-screen numeric fields are OPEN-015 cursor-offset artifacts and are not used.)

---

## Phase 1 — Faulting instruction

WRAM crash record: `CRASH_STACKED_SR=0x2700`, `CRASH_STACKED_PC=0x00070796`, `IR=0x00003D81`, `SSW=0x000D` (write, supervisor data), `CRASH_FAULT_ADDRESS=0x00000F41` (odd).

`IR=0x3D81` decodes as `move.w %d1, (0,%a6,%d2.w)` — MOVE.W (opcode `0011`), dest reg `A6`, dest mode `110` (address-register-indirect with index), source `D1`; extension word `0x2000` selects index `D2.w`, displacement 0. This matches the disassembly exactly at **`runtime_genesis_pc 0x00070794`** (`build/genesis_postpatch.disasm.txt`):

```
70794:  3d81 2000   movew %d1, %fp@(0,%d2:w)      ; %fp = %a6 ; FAULTING WRITE (IR=0x3D81)
70798:  2439 00ff 4006  movel 0xff4006, %d2       ; (next) load fg_row_dirty
```

The stacked PC `0x00070796` points at the second word of the faulting 4-byte instruction (`2000` extension) — consistent with the m68k group-0 imprecise-PC convention. The faulting instruction is at **`0x00070794`**, confirmed by IR match (not assumed). **STATICALLY_PROVEN.**

- Addressing/registers: `move.w %d1, (%a6 + %d2.w)` — destination base `%a6`, index `%d2.w`, source `%d1`.
- Computed destination = `%a6 + sign_extend(%d2.w)` = `0x00000F41` (the recorded fault address).

---

## Phase 2 — Operation producing fault address 0x00000F41

The staging-write helper (`runtime_genesis_pc 0x7078A..0x707A6`) computes the cell offset in `%d2` and writes through base `%a6`:

```
7078a:  movew %d5,%d2        ; d2 = row (d5)
7078c:  lslw #7,%d2          ; d2 = row*128
7078e:  movew %d6,%d7
70790:  addw  %d7,%d2        ; d2 += col
70792:  addw  %d7,%d2        ; d2 += col   (d2 = row*128 + col*2)
70794:  movew %d1,(%a6+%d2.w) ; staged_fg_buffer[offset] = cell word   <-- FAULT
70798:  movel 0xff4006,%d2 / bset %d5,%d2 / movel %d2,0xff4006   ; set fg_row_dirty bit
```

The destination is `%a6 + (row*128 + col*2)`. **`%a6` is required to be `staged_fg_buffer` (`WRAM 0x00FF501A`, per `out/symbol.txt`).** With `%a6 = 0x00FF501A`, the write address would be `~0x00FF5xxx`. The recorded fault address is `0x00000F41` — a **low** address — so **`%a6` did not hold `staged_fg_buffer`**; it held a stale/garbage value (`0x00000F41 − %d2.w`). The bare-offset-like low odd address is exactly what results when the staging base register is never loaded. **STATICALLY_PROVEN** (fault address = `%a6+%d2`, and `0x00000F41` is incompatible with `%a6 = 0x00FF501A`).

The helper chain reaching this write (the glyph hook's path): `0x70BC8` (per-cell) → `0x707BC` (`.Ltw_store_from_components_at_a2`) → `0x707E4` (validates `%a2` in `HW 0xC08000..0xC0C000`, subtracts `0xC08000`) → `0x70816` → `0x7078A` → `0x70794`. The chain also reads via `%a3` (tile LUT, `0x707CE: movew %a3@(0,%d7:w),%d7`) and `%a5` (attr LUT, `0x70784: movew %a5@(0,%d1:w),%d2`). **STATICALLY_PROVEN.**

---

## Phase 3 — Hook vs existing text-writer calling convention

The shared store helper requires the caller to preload three base registers: `%a3 = genesistan_pc080sn_tile_vram_lut`, `%a5 = genesistan_pc080sn_attr_lut`, `%a6 = staged_fg_buffer`.

**Existing text-writer hooks satisfy this.** E.g. `genesistan_hook_text_writer_3c550` (`tilemap_hooks.s:1090`) and `…_3c586` (`:1122`):
```
lea  genesistan_pc080sn_tile_vram_lut, %a3
lea  genesistan_pc080sn_attr_lut, %a5
lea  staged_fg_buffer, %a6          ; lines 1101-1103 / 1131-1133
```
Every `lea staged_fg_buffer,%a6` site in the patched disasm (`0x70486, 0x706a0, 0x70846, 0x70a48, 0x70c02, 0x70c52, 0x70d5c, 0x70e18`) lives inside these text-writer hooks. **DOCUMENTED (source) / STATICALLY_PROVEN (disasm).**

**The glyph hook does NOT.** `genesistan_hook_glyph_renderer_3bd48` (`tilemap_hooks.s:1046`), per-cell path `.Lgr_store_cell` (`:1078`):
```
.Lgr_store_cell:
    movem.l %d0-%d7/%a2-%a6, -(%sp)   ; saves a2-a6 (but never loads them)
    movea.l %a1, %a2
    adda.w  #2, %a2                    ; a2 = a1 + 2  (descriptor dest + 2)
    move.w  %d3, %d0
    bsr     .Ltw_store_from_components_at_a2   ; = 0x707bc — calls helper...
    movem.l (%sp)+, %d0-%d7/%a2-%a6
    adda.w  #4, %a1
    rts
```
It calls the shared helper **without** `lea …,%a3` / `lea …,%a5` / `lea staged_fg_buffer,%a6`. So at the staging write `0x70794`, `%a6` holds whatever the arcade renderer / VBlank context left in it → the write targets `0x00000F41` (odd) → address error. (`%a3`/`%a5` are likewise unset; with garbage bases the LUT reads at `0x707CE`/`0x70784` would also be wrong, but the `%a6` write faults first.) **STATICALLY_PROVEN.**

**Difference:** the glyph hook omits the three `lea` base-register loads that the shared FG-staging store helper requires and that every text-writer hook performs.

---

## Phase 4 — Classification

### **A — Hook behavior bug.**

`genesistan_hook_glyph_renderer_3bd48.Lgr_store_cell` calls the shared FG-staging store helper (`.Ltw_store_from_components_at_a2` / `0x707BC`) without establishing the helper's required precondition: `%a6 = staged_fg_buffer` (the immediate fault), and also `%a3 = genesistan_pc080sn_tile_vram_lut` and `%a5 = genesistan_pc080sn_attr_lut`. The helper is correctly designed and works for the text-writer hooks, which set all three before calling it; the glyph hook simply omits the setup. The faulting write `move.w %d1,(%a6+%d2.w)` at `0x70794` therefore targets `%a6`'s stale value (`0x00000F41`, odd) → address error.

Not C (the helper is not incompatible with the renderer's pattern — it is reused successfully elsewhere; the precondition is just not met). Not B (the fault is inside the helper due to a bad base register, not bad staged data). Not D (statically resolved).

---

## Phase 5 — Bounded recommendation

**Single fix locus, in the hook, matching the established convention:** in `genesistan_hook_glyph_renderer_3bd48`, load the three base registers the shared store helper requires before calling it — identical to `genesistan_hook_text_writer_3c550/3c586`:
```
lea  genesistan_pc080sn_tile_vram_lut, %a3
lea  genesistan_pc080sn_attr_lut, %a5
lea  staged_fg_buffer, %a6
```
Place them at hook entry (they are loop-invariant) **or** inside `.Lgr_store_cell` after its `movem.l` save (which already preserves `%a2-%a6`, so the loads are self-contained per cell). `%a6` is the load that fixes THIS crash; `%a3`/`%a5` are required for correct rendered output (else the glyph/attr LUT lookups read from garbage bases). Do not modify the shared helper. This is a production-intent register-setup fix — no scaffolding, no helper rewrite, no broadening.

(Whether the rendered title then displays correctly — descriptor `dest` C-window math, palette/patterns — is a separate downstream verification, not this crash.)

---

## KNOWN_FINDINGS impact

**Option C — proposed KF-028 refinement** (do NOT update `KNOWN_FINDINGS.md` here; Andy proposes, Cody applies after Tighe ack). Proposed addition:

> OPEN-016 Part 2 added `genesistan_hook_glyph_renderer_3bd48` to route the title glyph renderer's PC080SN FG writes into `staged_fg_buffer`. Build 0091 crashes (ADDRESS ERROR write at `runtime_genesis_pc 0x70794`, fault addr `0x00000F41`, IR `0x3D81`) because the hook's `.Lgr_store_cell` calls the shared FG-staging store helper (`0x707BC`) without preloading `%a6=staged_fg_buffer` (and `%a3`/`%a5` LUT bases) — the precondition every `genesistan_hook_text_writer_*` satisfies. A hook register-setup bug, not a helper/staging-data fault.

STRONG/CONFIRMED (instruction, IR match, fault-address arithmetic, and the source-level convention difference all proven). Cross-ref KF-013, KF-010, OPEN-016, OPEN-015.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-016 (active — Part 2 hook needs the register-setup fix above before it can be validated; not closed), OPEN-001 (context — rendering), OPEN-015 (context — WRAM record was the reliable source; the on-screen fields are still artifacts).
- Closed issues touched: NONE. New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: Start→C→A crash, broader unhooked-writer survey, broader embedded data-pointer-table survey.

## STOP triggered

NO.
