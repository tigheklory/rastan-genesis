# Andy — KF-028 Re-triage with Real Crash Record: PC 0x0003BD68 / Fault Addr 0x50205741

**Author:** Andy
**Date:** 2026-06-17
**Patched ROM:** `dist/rastan-direct/fixes/build_0077_kf028_input_shim_wiring/patched_rom.bin` (SHA `b63512abd4aa1e50a774442c44e0918233fc2d06625138c51f46f7125b5b5c1e`)
**Baseline:** Build 0077 (SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No fix design (bounded recommendation at end only). No runtime probing.

Disassembly cited from `build/genesis_postpatch.disasm.txt` (PATCHED image; `0x700c6: bsrw 0x710ce` present).

---

## 1. Baseline statement

This re-triage supersedes the fault-location analysis in `Andy_kf028_patched_rom_address_error_triage.md` (which proved the on-screen numeric fields are display artifacts and reclassified to Outcome C). The reliable WRAM crash record has now been read from Exodus, giving the real fault values. Only the exception **name**, the **stack dump**, and the **WRAM crash record** are trusted; the on-screen numeric fields (`0x116`/`0x196`/`C8`/etc.) remain bogus and are not used.

---

## 2. Real crash record (from WRAM `0xFF6800`)

| Field | Value | Source |
|---|---|---|
| Exception | ADDRESS ERROR (type 3) | reliable name |
| Stacked SR | `0x2700` (supervisor, IPM 7) | `FF6804` |
| Stacked PC | `0x0003BD68` | `FF6806` |
| Fault address | `0x50205741` (odd → address error) | `FF6854` |
| IR (instruction reg, from frame) | `0x32C2` | recorded as "D3" |
| SSW | `0x000D` → R/W=0 (**write**), I/N=1, FC=5 (supervisor data) | recorded as "D5" low word |

**Register-record caveat (second crash-handler bug).** `_crash_common` decodes the group-0 frame into `d1–d5` and sets `a0=sp`, and does `lea .Lhandler_pc_marker,%a1` — all *before* saving registers. So the saved "registers" are mostly **frame/handler values, not the at-fault registers**: `D0`=exception type (3), `D1`=SR, `D2`=stacked PC, `D3`=IR, `D4`=fault addr, `D5`=SSW, `A0`=SP, `A1`=`0x442` (handler marker). Only **`D6/D7/A2–A6` are genuine at-fault registers**: `D6=D7=0xFFFFFFFF`, `A2=0x00C01C18`, `A3=0x00050082`, `A4=A6=0xFFFFFFFF`, `A5=0x00FF0000`. The real `a1` (the faulting destination pointer) is lost; the fault address `0x50205741` comes from the frame and is reliable.

**SR=0x2700** (supervisor, IPM 7) confirms the fault occurred **inside the VBlank interrupt handler** — consistent with KF-013 (text dispatch fires inside VBlank).

---

## 3. Disassembly around PC 0x0003BD68 (patched, unshifted)

`0x3bd68 < 0x700c6`, so this is arcade-translated code, **byte-identical patched-vs-baseline** (the +4 growth is at/after `0x700c6` only). Routine entry is `0x3bd48`:

```
3bd48:  3200       movew %d0,%d1          ; d1 = input char/string-id
3bd4a:  0240 007f  andiw #127,%d0         ; d0 = char & 0x7F
3bd4e:  e548       lslw  #2,%d0           ; d0 = idx*4
3bd50:  41fa 002a  lea %pc@(0x3bd7c),%a0  ; a0 = descriptor-pointer TABLE (ROM)
3bd54:  d0c0       addaw %d0,%a0          ; a0 = table + idx*4
3bd56:  2050       moveal %a0@,%a0        ; a0 = table[idx]  (-> a descriptor)
3bd58:  2258       moveal %a0@+,%a1       ; a1 = descriptor[0] = DEST pointer
3bd5a:  3418       movew %a0@+,%d2        ; d2 = descriptor[1] = attribute word
3bd5c:  4a01       tstb %d1
3bd5e:  6b0c       bmis 0x3bd6c
3bd60:  1018       moveb %a0@+,%d0        ; d0 = next source byte (glyph/char)
3bd62:  6716       beqs 0x3bd7a           ; 0 terminator -> rts
3bd64:  4880       extw %d0
3bd66:  32c2       movew %d2,%a1@+        ; <-- FAULTING write (IR=0x32C2 matches)
3bd68:  32c0       movew %d0,%a1@+        ; <-- stacked PC (imprecise "next instr")
3bd6a:  60f4       bras 0x3bd60
...
3bd7c:  0003bc98 0003bca6 0003bcbe ...    ; TABLE: 128 ROM descriptor pointers (0x3bcxx)
```

**Routine semantics:** a glyph/string renderer. Input char/id in `d0` → index a 128-entry ROM pointer table at `0x3bd7c` → load a per-entry descriptor whose layout is `[long dest_ptr][word attr][byte glyph data…]` → copy attribute+glyph words to `(dest_ptr)+`. (This is in the text-producer territory KF-013/§stack identify; reached from the title sub-state handlers.)

**Faulting instruction:** the IR in the crash frame is `0x32C2` = the opcode of `0x3bd66 (movew %d2,%a1@+)`. The 68000 group-0 (address-error) frame stacks an **imprecise PC advanced past the fault**, so the recorded stacked PC `0x3bd68` is the *next* instruction; the actual fault is the word write at **`0x3bd66`** through `a1`. SSW confirms a **write**. Address error because `a1` was odd.

---

## 4. The faulting operation and the source of 0x50205741

The write at `0x3bd66` targets `(a1)+`. `a1` was loaded at `0x3bd58` from `descriptor[0]` (`moveal %a0@+,%a1`), where `a0 = table[idx]` (`0x3bd56`). The fault address `0x50205741` is therefore the value `a1` held = **`descriptor[0]`**.

`0x50205741` = ASCII `"P WA"` (`50 20 57 41`). It is **text/glyph data being read as a destination pointer.** So `table[idx]` did not resolve to a well-formed descriptor (whose first long would be a valid even VRAM/buffer address); it resolved to a location whose first 4 bytes are text. Either:
- the input `d0` (char/string-id) selected a table entry that points into glyph/text data rather than a real descriptor, or
- the descriptor region for that id is malformed/misindexed.

Crucially, the **renderer, the table (`0x3bd7c`), and the descriptors (`0x3bcxx`) are all ROM, all below `0x700c6`, all unshifted by the +4** — byte-identical to baseline. So the bad value is not produced by a layout shift of this code/data; it is produced by **this path being driven with an input that makes it dereference text as a pointer.** That input arrives from the title text-producer path that the KF-028 fix newly enabled.

(`A2=0x00C01C18`, a VDP-region address, and `A3=0x00050082`, a ROM pointer, are consistent with real text-rendering state at the time — corroborating that genuine text rendering was in progress.)

---

## 5. Stack/call-context consistency

Reliable stack dump (2-byte-aligned arcade addresses) + SR:
- `0x3A274` — VBlank master-dispatch return (`pea %pc@(0x3a274)`)
- `0x3A27E` — VBlank handler tail
- `0x3ACCC` — title sub-state handler
- `0x3BD68` — confirmed stacked PC, inside the glyph renderer `0x3bd48`
- `0x3B292` — interrupted main-loop return
- SR `0x2700` — inside the VBlank ISR

**Consistent.** Path: main loop interrupted → Level-6 VBlank → master dispatch (state 0 → title) → title sub-state handler → glyph/string renderer `0x3bd48` → address-error write at `0x3bd66`. This matches KF-013 (text dispatch inside VBlank) and the predecessor-chain model. The fix advanced execution from the pre-fix watchdog-state-3 block into this title text path.

---

## 6. Outcome classification

### Outcome: **B — Fix-revealed downstream issue.**

- The KF-028 input-shim wiring is architecturally correct; execution advanced (per stack + SR + live PC) into the **newly-reached title text-producer path**, unreachable pre-fix.
- The crash is an address-error **write** at `0x3bd66` (`movew %d2,%a1@+`, IR `0x32C2`) because the glyph renderer's destination pointer `a1` = `0x50205741` ("P WA"), i.e. **text data dereferenced as a pointer**.
- The faulting routine, its 128-entry pointer table (`0x3bd7c`), and its descriptors (`0x3bcxx`) are **ROM, unshifted by the +4** (all `< 0x700c6`) → byte-identical to baseline. The defect is in how this newly-exercised path is driven, not a layout-shift corruption.
- **Outcome A is not supported** by current evidence: the faulting machinery and data are unshifted; nothing points to a stale absolute reference here. (Not exhaustively excluded — see §7 — but no evidence makes A plausible, so a speculative +4 audit is not warranted.)

---

## 7. Bounded next recommendation

**Trace the caller of the glyph renderer `0x3bd48` from the title sub-state handler (`0x3accc`) path**, bounded to:
1. What `d0` (char/string-id) the caller passes, and what WRAM/ROM state computes it — to determine whether the id is wrong (e.g. uninitialized or wrong title-state field in the newly-reached code) vs in-range.
2. Read the ROM bytes of the table at `0x3bd7c` for the implicated index and the descriptor it points to — to confirm whether `descriptor[0] = 0x50205741` is reached via an out-of-range/garbage id or a genuinely malformed descriptor.

That pins the exact source of `0x50205741` and confirms B (downstream title-text bug), or surfaces an upstream cause. Do **not** run a +4 absolute-reference audit yet — no evidence supports Outcome A.

**Secondary (crash-handler reliability, separate from the game bug):** the crash handler has **two** defects that should be fixed before relying on any future crash screen — (a) the `%d2`-clobber display bug (prior triage), and (b) the register-save clobber documented in §2 (`D0–D5/A0/A1` hold frame/handler values, not at-fault registers). Recommend Cody fix both so the on-screen report and saved registers are trustworthy.

---

## 8. KNOWN_FINDINGS impact

**Option C — proposed refinement to KF-028** (now that A-vs-B is classified as B; Andy proposes, Cody applies after Tighe ack). Proposed addition to KF-028:

> Wiring the input shim (`build_0077_kf028`) changed the failure mode from watchdog-state-3 routing to normal main-loop + Level-6 VBlank + title-state execution, advancing into the title text-producer path. In that newly-reached path the glyph/string renderer at `0x0003BD48` faults with an ADDRESS ERROR (write at `0x0003BD66`, `movew %d2,%a1@+`) because its destination pointer is loaded with text data (`0x50205741`, "P WA") from a descriptor reached via the `0x3bd7c` table — a downstream title-text bug, not a layout-shift artifact (the renderer/table/descriptors are unshifted ROM below the +4 insertion point). Exact source of the bad index/descriptor pending the `0x3bd48` caller trace.

Confidence: STRONG (fault locus, write, text-as-pointer, unshifted machinery all proven); the precise upstream root (bad id vs malformed descriptor) is WORKING_HYPOTHESIS pending §7. BUILD_SPECIFIC. Cross-ref KF-013.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; failure mode advanced into the title text path; downstream address-error localized to the `0x3bd48` glyph renderer; no status change pending the caller trace).
- Closed issues touched: NONE. New issues opened: NONE (downstream title-text bug + the two crash-handler defects tracked via this triage; open formal issues if Tighe/Cody prefer). Issues closed: NONE. Deferred: NONE.

## STOP triggered

NO.
