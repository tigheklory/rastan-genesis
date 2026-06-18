# Andy — KF-028 Patched ROM Crash Triage: Address Error Exception Screen

**Author:** Andy
**Date:** 2026-06-17
**Patched ROM:** `dist/rastan-direct/fixes/build_0077_kf028_input_shim_wiring/patched_rom.bin` (SHA `b63512abd4aa1e50a774442c44e0918233fc2d06625138c51f46f7125b5b5c1e`)
**Baseline:** Build 0077 (SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** Static + runtime-evidence analysis only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No fix design (bounded recommendation at end only). No runtime probing.

Disassembly cited from `build/genesis_postpatch.disasm.txt`, confirmed to be the PATCHED image (`0x700c6: bsrw 0x710ce` present).

> **CORRECTION (full-resolution crash-image review).** An earlier draft of this triage trusted the on-screen `FAULT PC=0x116` / `FAULT ADDR=0x196` as the real fault location and dismissed `VECTOR: C8` as a transcription artifact. Reviewing the full-resolution crash image disproved that: **every numeric field on the crash screen equals `row*128 + col*2` — the VRAM cursor offset of the field's own screen position — not the intended value.** This is a `crash_handler.s` display bug (below). The fault-location conclusion is withdrawn; the outcome is reclassified to **C**.

---

## 1. Baseline statement

The KF-028 patched build **materially changed the observed failure mode.** Pre-fix (BM-004/005/006) the cadence was watchdog-delay-loop-dominant (`0x3a192/6/c`, master state 3). This recording shows main-loop + VBlank-service + title-handler execution instead, then an address-error crash. Runtime proof of title-dispatch reachability remains pending, but the **stack dump** (the one reliable numeric region) places execution inside the arcade VBlank handler / title sub-state handler — newly reached vs pre-fix.

The run ends in an address error. **The crash screen does not tell us where the fault occurred**, because its numeric fields are display artifacts (§3).

---

## 2. Smallest proven facts

- Crash handler is `crash_handler.s`. The exception **name** is rendered from a string pointer (`crash_get_exception_name` → `crash_puts_at`), independent of the broken hex path, so it is reliable: **the exception is genuinely an ADDRESS ERROR** (type 3; vector offset `0x0C` = `0x00000334` = `_crash_stub_address_error: moveq #3,%d0`). **STATICALLY_PROVEN.**
- `_crash_common` *correctly populates* the WRAM crash record (group-0 frame decode: `CRASH_STACKED_PC`←frame+10, `CRASH_FAULT_ADDRESS`←frame+2, `CRASH_STACKED_SR`←frame+8). The record in WRAM (`0xFF6806`, `0xFF6854`, `0xFF6804`) holds the real values — **but the display routine does not show them** (§3). **STATICALLY_PROVEN.**
- Runtime: actual ROM exec begins frame 115 (`0x71CE0`); ~4 s of execution; crash render begins frame 237; halted at `0x518` (`.Lcrash_halt: stop #0x2700`) from frame 240. **Runtime evidence.**

---

## 3. Crash-screen decoding — the numeric fields are cursor offsets, not values

`crash_set_cursor` computes the plane-A byte offset and **leaves it in `%d2`**, clobbering it:
```
move.w %d0,%d2 / mulu.w #128,%d2 / move.w %d1,%d3 / add.w %d3,%d3 / add.w %d3,%d2   ; %d2 = row*128 + col*2
... (base goes into %d0/%d1 for the VDP control word; %d2 unchanged) ... rts
```
Every value-printing wrapper calls it **after** the caller loaded the value into `%d2`:
```
crash_put_hex32_at:  bsr crash_set_cursor   ; <-- clobbers %d2
                     bsr crash_put_hex32_inline  ; prints %d2 (now = cursor offset)
```
(`crash_put_hex16_at` / `crash_put_hex8_at` are identical.) So **every `*_at` numeric field prints `row*128 + col*2`, not the value.** Verified against the full-res image:

| Field | Row,Col | `row*128+col*2` | On screen |
|---|---|---|---|
| VECTOR (hex8 of type) | 1, 36 | `0xC8` | `C8` ✓ |
| FAULT PC | 2, 11 | `0x116` | `00000116` ✓ |
| SR (hex16) | 2, 30 | `0x13C` | `013C` ✓ |
| FAULT ADDR | 3, 11 | `0x196` | `00000196` ✓ |
| D0 | 5, 3 | `0x286` | `00000286` ✓ |
| D1 | 5, 15 | `0x29E` | `0000029E` ✓ |
| D2 | 5, 27 | `0x2B6` | `000002B6` ✓ |
| … D3–USP, DEST_BG/FG, BG/FG_DIRTY, PAL_D, TILE_D, FRAME | … | … | all match `row*128+col*2` ✓ |

(e.g. `DEST_BG` r12c8 = `0x610` ✓; `FRAME` r14c29 = `0x73A` ✓; `PAL_D` r14c6 low-byte = `0x0C` ✓.) **Every numeric field is its own screen position.** STATICALLY_PROVEN + image-confirmed.

**Reliable fields:**
- **EXCEPTION name** — string-based (`crash_puts_at` reloads `%d2` from the string each char). → ADDRESS ERROR. Reliable.
- **STACK DUMP** — the only reliable numbers. Here `crash_set_cursor` is called once per row, then `move.l (%a2)+,%d2` loads the actual stack word **after** the cursor set, and `crash_put_hex32_inline` prints it. So the stack dump is genuine memory from `CRASH_SP_AT_ENTRY`. Reliable.

**Unreliable (all artifacts): VECTOR, FAULT PC, FAULT ADDR, SR, D0–USP, DEST_BG/FG, BG/FG_DIRTY, PAL_D, TILE_D, FRAME.** The real fault PC/address exist in WRAM but are not displayed.

---

## 4. What the reliable evidence shows

**Exception:** genuine ADDRESS ERROR (name reliable). The real fault PC and access address are **unknown from this screen** (they are in WRAM `0xFF6806` / `0xFF6854`, not shown).

**Stack dump** (read as a byte stream — the on-screen longword grouping is offset; clean arcade addresses emerge at 2-byte alignment):
- `0x0003A274` — exactly the return address the VBlank master dispatch pushes (`pea %pc@(0x3a274)`); proves the master dispatch ran.
- `0x0003A27E` — VBlank handler tail (`rte` region).
- `0x0003ACCC` — title sub-state handler (near the `0x3ac88` title-entry kick).
- `0x0003BD68` — text-producer dispatch region (called from title handlers).
- `0x0003B292` — arcade main-loop watchdog-dispatch return.
- Plus data words (`0x000D5020`, `0x574132C2` = "WA2.", small constants).

**Live PC run segments (register panel, not the crash screen — reliable):** frames 115–235 cycle through the arcade main loop (`0x3B284/28C/292`) and the Level-6 VBlank-service helper tree (`0x700AE`, `0x719F0/71A1C/71A1E`, IPM 6) — **not** the pre-fix watchdog-delay-loop.

Together these (stack + live PC) are solid evidence that **the fix advanced execution into the arcade VBlank master-dispatch → title sub-state machine**, which was unreachable pre-fix (BM-006: `0x3abfe` never hit). That conclusion does **not** depend on the broken crash-screen fields.

---

## 5. Patched-vs-baseline comparison

The fix inserted one `bsr` at `0x700c6`, growing the image **+4 bytes from `0x700c6` onward** (`_vblank_service` stays at `0x700c2`; shim moves `0x710ca → 0x710ce`). Any address **below** `0x700c6` is byte-identical patched-vs-baseline; the crash handler (`0x334`/`0x514`/`0xA16`) and the header (`0x100–0x1FF`) are unchanged. **STATICALLY_PROVEN.**

This is now of limited relevance to fault attribution, because we no longer have a real fault PC to compare. It does mean the crash handler's display bug is **pre-existing** (not introduced by the +4 fix) — the bug is in baseline `crash_handler.s` and would mis-render any crash.

---

## 6. Outcome classification

### Outcome: **C — Crash-report decoding issue.**

The exception screen's numeric fields (FAULT PC, FAULT ADDR, SR, VECTOR, all registers, the DEST/DIRTY/FRAME block) are **display artifacts equal to each field's `row*128 + col*2` cursor offset**, caused by `crash_set_cursor` clobbering `%d2` before `crash_put_hexN_inline` reads the value. The reported `FAULT PC=0x116` / `FAULT ADDR=0x196` **do not identify the failing instruction** (they are the screen positions of those two fields). Only the exception **name** and the **stack dump** are trustworthy.

Consequently:
- **Confirmed (reliable evidence):** the exception is an ADDRESS ERROR; the fix changed the failure mode and advanced execution into the arcade VBlank master-dispatch / title sub-state machine (stack dump + live PC).
- **Unresolved:** the real fault PC and access address (needed to localize the bad control transfer and to decide fix-revealed-downstream (B) vs fix-caused-layout-shift (A)). These cannot be read off this screen.

The earlier B-vs-A reasoning is therefore **suspended pending recovery of the real fault values**; the "execution ran into the cartridge header" narrative is withdrawn (it rested on the bogus `0x116`).

---

## 7. KNOWN_FINDINGS impact

**Option A — no finding update now.** Hold the KF-028 refinement: the patched build's *failure mode change* and *title-state reachability* are supported by reliable evidence, but the crash itself is unattributed because the fault location is undecodable. No durable system-behavior fact is settled yet beyond "the crash handler's hex display is broken," which is better captured as a code defect to fix (§9) than as a KF entry at this stage. Once the real fault PC/addr are recovered and A-vs-B is decided, KF-028 can be refined accordingly.

---

## 8. Recommended next task

**Two concrete steps, in order:**

1. **Fix the crash-handler display bug (Cody, bounded).** In `crash_handler.s`, the `crash_put_hexN_at` wrappers print `%d2` after `crash_set_cursor` has overwritten it. Recommended fix scope (not drafted here): make `crash_set_cursor` preserve `%d2` (e.g. save/restore around it), or restructure the `*_at` wrappers to set the cursor first and load the value into `%d2` afterward. This is a **pre-existing** baseline bug that blinds all crash triage; fixing it is prerequisite to trusting any crash screen. Then rebuild and reproduce the crash to read the **real** FAULT PC / FAULT ADDR / SR / registers.

   *Interim alternative if a rebuild is undesirable:* dump WRAM crash record at the halt — `CRASH_STACKED_PC=0xFF6806`, `CRASH_FAULT_ADDRESS=0xFF6854`, `CRASH_STACKED_SR=0xFF6804`, `CRASH_D0..A6=0xFF6816..0xFF684E` — via the emulator memory viewer. `_crash_common` populates these correctly; only the renderer is broken.

2. **Re-triage with the real fault values.** With the genuine fault PC, decide fix-revealed-downstream (B) vs fix-caused-layout-shift (A); if a layout-shift is suspected, run the patched-vs-baseline absolute-reference integrity audit (94 `opcode_replace` targets + absolute `jsr`/`jmp` to Genesis-native helpers ≥`0x700c6` + level vectors).

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; failure mode advanced past the watchdog-state-3 block per reliable stack/PC evidence; a downstream address error occurred but is not yet localized; no status change).
- Closed issues touched: NONE. New issues opened: NONE (the crash-handler display bug and the unlocalized address error are tracked via this triage; open formal issues if Tighe/Cody prefer). Issues closed: NONE. Deferred: NONE.

## STOP triggered

NO.
