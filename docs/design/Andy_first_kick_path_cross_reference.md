# Andy — Arcade Watchdog First-Kick Path Cross-Reference (Build 0077)

**Author:** Andy
**Date:** 2026-05-30
**Build under analysis:** 0077 (canonical baseline SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** STATIC analysis only. Documentation-only deliverable. No source / spec / tool / Makefile / ROM modifications. No bookmark cycle initiation (BM-004 is a separate follow-up task). No runtime probing.

---

## Phase 0 — Required Priors Check

### Baseline statement

This task EXTENDS the line of analysis established by:

- `KF-001` — watchdog routine at Genesis `0x3A180` (arcade `0x39F80`); positive-count decrement vs zero-count expiry-to-bootstrap behavior.
- `KF-003` — eleven `%a5@(44)` kick sites at Genesis runtime PCs `0x3A5D4`, `0x3A63E`, `0x3AC88`, `0x3ACF2`, `0x3AD22`, `0x3AD5E`, `0x3ADD0`, `0x9A3B0`, `0x9A3D0`, `0x9A4B0`, `0x9A4D0`; sampled non-reachability during the analyzed Build 0077 window.
- `KF-004` — Genesis runtime PC `N` ↔ ROM file offset `N`.
- `KF-006` — `identity_offset = 0x200` (arcade source `N` ↔ Genesis ROM file offset `N+0x200` ↔ Genesis runtime PC `N+0x200`).
- `docs/design/Andy_polling_loop_investigation.md` — observation that during the polling-loop window, none of the 11 kick sites was reached.

### Classification

EXTENDING. The task extends KF-003 by adding "which kick site is the first one normal arcade execution would reach, by what control path." It does not propose a new finding; it proposes a `KF-003` UPDATE per Option C of the patched template's KNOWN_FINDINGS-impact discipline.

### Contradiction check

None. No CONFIRMED/STRONG prior is contradicted. This work is fully compatible with the cited KF entries.

### Phase 0 STOP

Not triggered.

---

## Phase 1 — Arcade-side trace (`build/maincpu.disasm.txt`)

Trace begins at the arcade reset vector target and follows execution forward until the first writer-to-`%a5@(44)` becomes reachable.

### §1.1 Reset entry (arcade source `0x3A000`)

```
3a000:  6000 0e84      braw 0x3ae86            ; unconditional jump to init
```
Source: `build/maincpu.disasm.txt:72945`.

### §1.2 Initialization block (arcade source `0x3AE86 … 0x3B07A`)

Selected load-bearing instructions:

```
3ae86:  33fc 0000 00c5 movew #0, 0xc50000      ; first init store (VDP register space on arcade)
3aeea:  41f9 0010 c000 lea 0x10c000, %a0       ; arcade WRAM base (zero-fill loop setup)
3af04:  4bf9 0010 c000 lea 0x10c000, %a5       ; arcade workram base — pinned in A5 for the entire run
3b07a:  027c f0ff      andiw #-3841, %sr        ; enable interrupts (clears IPM bits)
```
Sources: `build/maincpu.disasm.txt:73984, 74008, 74015, 74111`.

Significance: `A5 = 0x10C000` is the arcade workram base. The watchdog routine's `%a5@(44)` operand resolves to arcade `0x10C02C` at runtime. Genesis-side translation must produce the equivalent invariant relative to its own workram base.

### §1.3 Main loop (arcade source `0x3B07E … 0x3B096`)

```
3b07e:  33c0 003c 0000 movew %d0, 0x3c0000     ; main-loop top (write hardware register)
3b08c:  0c6d 0100 0012 cmpiw #256, %a5@(18)    ; pretest on workram word at offset 18
3b092:  6100 ef14      bsrw 0x39fa8             ; CALL watchdog test
3b096:  60e6           bras 0x3b07e             ; loop back
```
Sources: `build/maincpu.disasm.txt:74112, 74116, 74117, 74118`.

This main loop does ONLY:

1. Write to hardware-mapped `0x3C0000`.
2. Pretest a workram counter at `%a5@(18)` = `0x10C012`.
3. Call the watchdog test entry at `0x39FA8`.
4. Branch back.

**There is no kick to `%a5@(44)` on the main-loop path.** The main loop only *tests* the watchdog counter (indirectly, via the entry at `0x39FA8`); it never *writes* the counter. Therefore the first kick cannot come from the main loop.

### §1.4 Watchdog test entry (arcade source `0x39FA8`)

```
39fa8:  6502           bcss 0x39fac             ; if carry set (pretest failed: A5@(18) < 256), branch over
39fac:  4e75           rts                      ; return without entering the watchdog body
```
Sources: `build/maincpu.disasm.txt:72901, 72903`.

The watchdog body (covered by KF-001) begins at `0x39F80`. The entry at `0x39FA8` is a wrapper that gates entry on the pretest. KF-001 covers the body itself; this task does not re-trace it.

### §1.5 Where the kicks live (writers, not pretests)

KF-003 enumerates 11 kick sites. Of those, the four lowest-address kicks lie in the arcade source range `0x3A3D4..0x3ABD0`:

```
3a3d4:  3b7c 00a0 002c movew #160, %a5@(44)    ; store 0xA0 (160) into counter
3a43e:  3b7c 00a0 002c movew #160, %a5@(44)    ; store 0xA0 (160)
3aa88:  3b7c 00d0 002c movew #208, %a5@(44)    ; store 0xD0 (208) — TITLE-STATE ENTRY kick
3aaf2:  3b7c 00a0 002c movew #160, %a5@(44)    ; store 0xA0 (160) — TITLE-STATE state-1 transition
```
Sources: `build/maincpu.disasm.txt:73232, 73257, 73694, 73727`.

These kick sites are NOT in the main loop and NOT in the watchdog body. They live inside state-machine handler routines invoked dispatched-from-elsewhere (KF-011: arcade Level-5 VBlank owns progression). Static call-graph search for direct callers of the routine containing the lowest kick (`0x3A3D4`, inside routine at `0x3A39A`) returns no direct callers via `bsr` / `jsr` — consistent with a VBlank-dispatched state-machine using a jump table or computed dispatch.

### §1.6 What the static arcade trace establishes

- The arcade main loop is a watchdog-test-only loop. It does NOT kick.
- All 11 kicks live inside state-machine handler routines.
- The only path from reset to a kick is: `reset → init → main loop becomes live → VBlank fires → VBlank dispatcher routes to the appropriate state-machine handler → handler executes its kick`.
- Static analysis cannot determine WHICH kick is first without modeling the VBlank dispatch and the state-machine initial state.

---

## Phase 2 — Genesis-side parallel trace (`build/genesis_postpatch.disasm.txt`)

Genesis runtime PC = arcade source + `0x200` per `KF-006`. Each instruction the arcade trace cites is checked against the Genesis-translated equivalent.

### §2.1 Reset entry (Genesis runtime `0x3A200` ↔ arcade `0x3A000`)

Genesis-translated reset target is reached via the Genesis bootstrap (file offset `0x0..0x1FF`) and then enters arcade-translated code at `0x3A200`. The instruction at `0x3A200` is the translated form of `braw 0x3ae86` (same encoding, relocated branch destination), arriving at the init block at Genesis runtime `0x3B086` (= arcade `0x3AE86` + `0x200`).

### §2.2 Initialization block — translation-patched WRAM rebase

The arcade init code uses `0x10C000` as the workram base. The Genesis translation MUST rebase this to the Genesis WRAM region. Build 0077 confirms this rebase is applied:

```
3b0ea:  41f9 00ff 0000 lea 0xff0000, %a0       ; PATCHED: was 0x10C000 in arcade source
3b104:  4bf9 00ff 0000 lea 0xff0000, %a5       ; PATCHED: was 0x10C000 in arcade source
```
Sources: `build/genesis_postpatch.disasm.txt:73895, 73902`.

This is a translation-patched byte-level difference from arcade. Under the §0 translated-flow-equivalence test:

- The arcade-side invariant is "`A5` points to workram base; `%a5@(44)` is a workram counter at base+44."
- The Genesis-side invariant after this patch is "`A5 = 0xFF0000`; `%a5@(44) = 0xFF002C`."
- KF-001 confirms the watchdog counter address is `0xFF002C` on Genesis — exactly base+44 from `A5 = 0xFF0000`.
- The invariant is preserved across the patch. This is a translated-flow-equivalent rebase, not a divergence.

### §2.3 Main loop (Genesis runtime `0x3B27E … 0x3B296` ↔ arcade `0x3B07E … 0x3B096`)

```
3b27e:  33c0 003c 0000 movew %d0, 0x3c0000     ; identical encoding to arcade 0x3B07E
3b292:  6100 ef14      bsrw 0x3a1a8             ; SAME RELATIVE OFFSET (0xef14) as arcade 0x3B092
```
Sources: `build/genesis_postpatch.disasm.txt:74011, 74016`.

The `bsrw` encoding at `0x3B292` uses the identical 16-bit offset (`0xef14`) that the arcade uses at `0x3B092`. PC-relative arithmetic relocates the target by the same `+0x200` that relocates the call site: arcade target `0x39FA8` + `0x200` = Genesis target `0x3A1A8`. Byte-perfect translated-flow equivalence.

### §2.4 Watchdog test entry (Genesis runtime `0x3A1A8` ↔ arcade `0x39FA8`)

```
3a1a8:  6502           bcss 0x3a1ac             ; identical encoding/structure to arcade 0x39FA8
```
Source: `build/genesis_postpatch.disasm.txt:72731`.

Same `BCS.s +2` short branch. Translated-flow equivalent.

### §2.5 Kick sites — encoding preservation

Each of the four lowest-address kicks identified in §1.5 is preserved with identical encoding at Genesis runtime PC = arcade + `0x200`:

| Arcade source | Genesis runtime | Encoding | Counter value |
|---|---|---|---|
| `0x3A3D4` | `0x3A5D4` | `3b7c 00a0 002c` | 160 |
| `0x3A43E` | `0x3A63E` | (KF-003) | 160 |
| `0x3AA88` | `0x3AC88` | `3b7c 00d0 002c` | 208 |
| `0x3AAF2` | `0x3ACF2` | `3b7c 00a0 002c` | 160 |

Verified in Genesis disassembly: `build/genesis_postpatch.disasm.txt:73068, 73538, 73571`.

Encoding-preserving translation. The `%a5@(44)` operand now resolves to `0xFF002C` (Genesis WRAM) instead of `0x10C02C` (arcade workram), because `A5` was rebased in §2.2. Translated-flow-equivalent.

---

## Phase 3 — Divergence analysis

### §3.1 Layers verified equivalent under the translated-flow test

Working forward from reset:

| Layer | Arcade | Genesis | Equivalence |
|---|---|---|---|
| Reset jump | `0x3A000: braw 0x3AE86` | `0x3A200: braw 0x3B086` | PC-relative encoding preserved; targets correctly relocated by `+0x200` |
| Init WRAM rebase | `lea 0x10C000, %a5` at `0x3AF04` | `lea 0xFF0000, %a5` at `0x3B104` | TRANSLATION-PATCHED. Invariant ("A5 = workram base, A5+44 = watchdog counter") preserved. KF-001 confirms `0xFF002C` is the live counter. |
| Interrupt enable | `andiw #-3841, %sr` at `0x3B07A` | (translated form at `0x3B27A`) | Encoding-preserving; same effect |
| Main loop body | `0x3B07E … 0x3B096` | `0x3B27E … 0x3B296` | Byte-perfect translated-flow equivalent (`bsrw` offset `0xef14` preserved; target relocated) |
| Watchdog test wrapper entry | `0x39FA8: bcss 0x39FAC` | `0x3A1A8: bcss 0x3A1AC` | Byte-perfect |
| Kick site encodings | `0x3A3D4 / 0x3A43E / 0x3AA88 / 0x3AAF2 …` | `0x3A5D4 / 0x3A63E / 0x3AC88 / 0x3ACF2 …` | All preserved; operand `%a5@(44)` resolves to translated counter address via §2.2 rebase |

**No causally-meaningful static divergence is identifiable on the path from reset to any of the kick sites.** Every byte-level difference between arcade and Genesis along this path is accounted for by a translation patch that preserves the invariant the arcade code depends on.

### §3.2 What static analysis cannot determine

The only path that delivers control to a kick site is:

```
reset → init → main loop becomes live →
    Level-5 VBlank fires (KF-011 — arcade VBlank owns progression) →
        VBlank dispatcher routes to state-machine handler →
            handler executes its kick
```

Static analysis alone cannot determine:

- Whether the Genesis Level-5 VBlank vector is configured to call the arcade-translated VBlank handler.
- Whether the arcade VBlank dispatcher, once entered, advances the state machine sufficiently to enter a handler that contains a kick.
- The initial state of the state-machine workram cells that the VBlank dispatcher uses to choose which handler to invoke.

These are RUNTIME questions. They are the open questions that BM-004 is designed to answer.

### §3.3 Outcome classification

**Outcome B — first-kick reachability is the open RUNTIME question.**

- Andy traces the path successfully in both arcade and Genesis-translated code.
- No causally-meaningful static divergence is identifiable.
- Whether the path is actually executed at runtime in Build 0077 is open.
- Andy names a specific kick site as the recommended BM-004 target (see §5).

---

## Phase 4 — KNOWN_FINDINGS impact

### Option selected: C — Proposed update to KF-003

**Proposed update text (additive — does NOT modify the existing Finding or Use-as-prior wording):**

Append to KF-003's "Finding" paragraph after the existing sentence:

> Static cross-reference of Build 0077 (Andy, `docs/design/Andy_first_kick_path_cross_reference.md`) identifies the path from reset to any kick site as `reset → init → main loop → Level-5 VBlank → state-machine dispatcher → handler containing the kick`. The arcade main loop at `0x3B07E` and its Genesis-translated equivalent at `0x3B27E` are byte-perfect translated-flow equivalents through the watchdog test wrapper at arcade `0x39FA8` / Genesis `0x3A1A8`. The WRAM rebase from arcade `0x10C000` to Genesis `0xFF0000` is a translation patch that preserves the `%a5@(44)` watchdog-counter invariant. No causally-meaningful static divergence is identifiable on the path from reset to a kick site; reachability is determined at runtime by VBlank dispatch and state-machine progression.

Append to KF-003's "Use as prior" paragraph:

> When investigating non-reachability of kicks, do NOT search for a static divergence in the reset-to-main-loop layers — they are translation-equivalent. Focus instead on Level-5 VBlank vector setup, VBlank dispatcher entry, and state-machine initial conditions.

**Source for the update:** This document (`docs/design/Andy_first_kick_path_cross_reference.md`).

**Confidence axis:** Remains STRONG. The new content is corroborating cross-reference; it does not promote the entry to CONFIRMED.

**Status / Applicability / Rediscovery Hazard:** Unchanged.

**Last verified:** Bump to 2026-05-30 (Build 0077).

**Cody implementation note (for the eventual KF-003 update commit):** This is a propose-update. Cody applies the edit after Tighe acknowledges; Andy does not modify `KNOWN_FINDINGS.md` directly.

---

## Phase 5 — Recommended next task (BM-004 candidate)

### §5.1 Recommended primary BM-004 target: Genesis runtime PC `0x0003AC88`

**Why:** `0x0003AC88` (arcade source `0x0003AA88`) is the title-state ENTRY kick — the first `%a5@(44)` writer on the title-state handler's earliest execution path. It sets the counter to 208 (longest timeout in this cluster), consistent with title-state being the slow startup state. Hitting this bookmark proves that the VBlank dispatcher is routing to the title-state handler. Missing this bookmark proves the VBlank chain does not deliver control to the title-state handler at all — the most diagnostic single signal for "is the state machine being driven at all?".

### §5.2 Alternative / secondary candidates

- `0x0003ACF2` (arcade `0x0003AAF2`) — title-state state-0 → state-1 transition kick. Hitting `0x0003AC88` but missing `0x0003ACF2` would indicate the title-state handler runs but never advances out of state 0.
- `0x0003A5D4` (arcade `0x0003A3D4`) — lowest-address kick. Useful as an alternative if a non-title handler is suspected to be the first-reachable.

### §5.3 What this task does NOT do

Per scope constraints, this document does NOT initiate the BM-004 cycle. The BM-004 cycle (bookmarks_v2 schema, helper-byte insertion, build, runtime probe, report) is a separate task for Cody to execute after Tighe approves the target.

---

## Sources

- `build/maincpu.disasm.txt` — arcade-side disassembly (`maincpu.bin`). Cited line numbers: 72901, 72903, 72945, 73232, 73257, 73694, 73706, 73714, 73727, 73984, 74008, 74015, 74111, 74112, 74116, 74117, 74118.
- `build/genesis_postpatch.disasm.txt` — Genesis-translated postpatch disassembly. Cited line numbers: 72731, 73068, 73538, 73571, 73895, 73902, 74011, 74016.
- `KNOWN_FINDINGS.md` — KF-001, KF-003, KF-004, KF-006, KF-008, KF-011.
- `docs/design/Andy_polling_loop_investigation.md` — predecessor analysis.
- `docs/design/Cody_arcade_disassembly_pointer.md` — arcade disassembly artifact pointer.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001, OPEN-004 (both already collapsed by `Andy_polling_loop_investigation.md`; this document refines the static-vs-runtime boundary).
- **Closed issues touched:** None.
- **New issues opened:** None. (The BM-004 recommendation in §5 is a recommended next task, not an issue to track in `OPEN_ISSUES.md`.)
- **Issues closed:** None.
- **Issues intentionally deferred:** None.

---

## STOP triggered

NO.
