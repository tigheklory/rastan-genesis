# Andy — Master Dispatch Selector Audit: 0x0003A256 → 0x0003ABFE (Build 0077)

**Author:** Andy
**Date:** 2026-06-12
**Build:** 0077 (canonical baseline SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** STATIC audit only, bounded to master state selector `%a5@(0)` and the master dispatch table. Documentation-only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No instrument design. No runtime probing.

All addresses are Genesis runtime PC / ROM file offset (KF-004). Arcade-source equivalents (`= Genesis − 0x200`, KF-006) are cross-reference only.

---

## Phase 0 — Baseline statement

**Classification:** EXTENDING (touches KF-003). **Phase 0 STOP:** not triggered; no CONFIRMED/STRONG contradiction.

**Relevant priors:** KF-001 (watchdog routine `0x3A180`; HIGH), KF-003 (predecessor chain + `%a5@(44)` dual-use; HIGH; EXTENDING target), KF-004 (runtime PC = ROM offset; CONFIRMED), KF-005 (target-space mismatch; HIGH), KF-007 (bookmarks_v2 verbatim trace PC; HIGH), KF-019 (Exodus authority / MAME sampling gap; HIGH), KF-022 (TC0040IOC inputs active-low; CONFIRMED). HIGH-hazard touched: KF-001/003/004/005/007/019. None contradicted.

**Open issues touched:** OPEN-001, OPEN-004 (context only; no status change).

---

## §0 — Smallest proven statement

**Proven by BM-005 + BM-006:**
- Execution reaches `0x0003A256` (BM-005 Outcome A, clean).
- `0x0003ABFE` was not observed in the 33.067 s BM-006 Exodus window (Outcome B, clean).
- Live runtime boundary lies between the two.

**NOT proven (preserved throughout):** `%a5@(0)` is non-zero; the selector/title-dispatcher is "broken"; VBlank is broken or healthy; the state machine is globally non-functional; `0x0003AF40` is causally related; Outcome B is permanent (window-scoped to 33 s).

---

## Phase 1 — Master dispatch sequence and table

Verified byte-for-byte against `build/genesis_postpatch.disasm.txt:72799-72809`:

```
3a252:  pea %pc@(0x3a274)      ; push handler-return addr
3a256:  302d 0000  movew %a5@(0), %d0   ; READ master selector   [STATICALLY_PROVEN]
3a25a:  d040       addw %d0, %d0        ; ×2
3a25c:  lea %pc@(0x3a26c), %a0 ; table base
3a260:  addaw %d0, %a0
3a262:  movew %a0@, %d0        ; table word
3a264:  lea %pc@(0x3a26c), %a0
3a268:  addaw %d0, %a0         ; a0 = 0x3a26c + word
3a26a:  jmp %a0@               ; computed dispatch
3a26c:  [0992][0840][00ee][0b02]   ; master jump table (4 entries)
```
The read at `0x3a256` is byte-identical to arcade `0x3a056` (`movew %a5@(0),%d0`). The table at `0x3a26c` is byte-identical to arcade `0x3a06c` (`0992 0840 00ee 0b02`). **STATICALLY_PROVEN.**

**Computed targets** (`target = 0x3a26c + word`; one-line disassembly of each):

| `%a5@(0)` | word | Genesis target | What it is | Label |
|---|---|---|---|---|
| 0 | `0x0992` | `0x3abfe` | title dispatcher (`tstw %a5@(44)` …) | STATICALLY_PROVEN |
| 1 | `0x0840` | `0x3aaac` | counter-gated sub-dispatcher (`tstw %a5@(44)` …) | STATICALLY_PROVEN |
| 2 | `0x00ee` | `0x3a35a` | counter-gated sub-dispatcher (`tstw %a5@(44)` …) | STATICALLY_PROVEN |
| 3 | `0x0b02` | `0x3ad6e` | `braw 0x3a180` → **watchdog routine** (KF-001) | STATICALLY_PROVEN |

(`build/genesis_postpatch.disasm.txt:72885, 73398, 73496, 73599`.) **Only `%a5@(0)==0` reaches the BM-006 target `0x3abfe`.** Master state 3 branches straight into the KF-001 watchdog routine `0x3a180` — the routine whose `0x3a192/0x3a196/0x3a19c` delay loop dominates the BM-006 observation window.

---

## Phase 2 — `%a5@(0)` writer audit + translated-flow-equivalence

Seven direct writers of `%a5@(0)` exist (grep `,%a5@(0)` destinations, excluding the read/`tstw`/`cmpiw` forms). Each has an identical-encoding arcade counterpart at `−0x200`:

| # | Genesis | Op | Arcade | Encoding match | Equiv? |
|---|---|---|---|---|---|
| 1 | `0x3a4ea` | `clrw %a5@(0)` → 0 | `0x3a2ea` | `426d 0000` | YES |
| 2 | `0x3a650` | `clrw %a5@(0)` → 0 | `0x3a450` | `426d 0000` | YES |
| 3 | `0x3a65a` | `movew #1,%a5@(0)` | `0x3a45a` | `3b7c 0001 0000` | YES |
| 4 | `0x3abde` | `movew #2,%a5@(0)` | `0x3a9de` | `3b7c 0002 0000` | YES |
| 5 | `0x3ad48` | `movew #2,%a5@(0)` | `0x3ab48` | `3b7c 0002 0000` | YES |
| 6 | `0x3add6` | `movew #3,%a5@(0)` | `0x3abd6` | `3b7c 0003 0000` | YES |
| 7 | `0x3ae7a` | `movew #1,%a5@(0)` | `0x3ac7a` | `3b7c 0001 0000` | YES |

All seven are **translated-flow equivalent** (`genesis_postpatch.disasm.txt:73005,73096,73099,73488,73590,73626,73679`; arcade counterparts confirmed at `−0x200`). No writer is suppressed, relocated out of flow, or value-changed. (Caveat, per KF-026 pattern: pointer-aliased writes to `0xFF0000` via another register are not statically enumerable; the seven above are the direct selector accesses.)

### Writer #6 (`0x3add6`, the state-3 writer) — the load-bearing one

Writer #6 sits inside the routine at `0x3ad7c`, which the VBlank handler calls at `0x3a23e` (`bsrw 0x3ad7c`) **before** the master dispatch read at `0x3a256`. So this routine can set `%a5@(0)` on the same VBlank that then dispatches. The routine (`genesis_postpatch.disasm.txt:73604-73628`), with arcade side-by-side (`maincpu.disasm.txt:73763-73787`):

```
3ad7c:  tstw %a5@(7184)
3ad84:  cmpiw #256, %a5@(18)
3ad8a:  bsrw 0x3a1a8           ; watchdog wrapper  (arcade: bsrw 0x39fa8)
3ad8e:  cmpiw #3, %a5@(0)      ; already state 3?
3ad94:  beqs 0x3ade0           ;   yes → return (idempotent)
3ad96:  btst #2, 0xff60ff      ; GATE  (arcade: btst #2, 0x390007)
3ad9e:  bnes 0x3ade0           ;   bit set → return WITHOUT setting state 3
3ada0:  ... setup (bsrw 0x3f284 / movew #31,%a5@(74) / bsrw 0x3afd8/0x3b050/0x3af72)
3adba:  clrl 0xff4016          ; (arcade: clrl 0xc20000)
3adc0:  clrl 0xff4012          ; (arcade: clrl 0xc40000)
3adc6:  bsrw 0x3b064 / moveq #14 / bsrw 0x3bd48
3add0:  movew #16, %a5@(44)    ; reload shared counter
3add6:  movew #3, %a5@(0)      ; ← SET MASTER STATE = 3
3addc:  clrw %a5@(2)
3ade0:  rts
```

**Translated-flow-equivalence test on this routine:** control flow is identical to arcade `0x3ab7c`; every byte difference is a standard hardware-address redirect:
- **Gate operand:** arcade `btst #2,0x390007` → Genesis `btst #2,0xff60ff`. Arcade `0x390007` is a TC0040IOC input port (KF-022, active-low: idle/unpressed = 1). Genesis redirects it to a WRAM input-mirror byte at `0xff60ff` (adjacent to `0xff60fe`, used by the input routine at `0x3a2a8`). This is the same hardware-input-redirect pattern used elsewhere in translation.
- `clrl 0xc20000/0xc40000` → `clrl 0xff4016/0xff4012` (hardware → WRAM redirect); `bsrw` targets relocated `+0x200`.

The redirect passes the translated-flow-equivalence test **at the level of the master-state machinery**: the gate branch structure is preserved; only the *source of the gate bit* is translated. Whether the Genesis mirror `0xff60ff` bit 2 holds the value arcade `0x390007` bit 2 would hold (active-low idle = 1) depends on the input-shim that populates `0xff60ff` — code **outside this audit's bounded scope** and **runtime-dependent**.

**Causal logic of the gate (STATICALLY_PROVEN structure / EXPECTED_BUT_RUNTIME_DEPENDENT value):**
- If gate bit 2 == **1** → `bnes` taken → state-3 write skipped → `%a5@(0)` stays 0 → master dispatch routes to title dispatcher `0x3abfe`. (Arcade idle expectation under KF-022 active-low.)
- If gate bit 2 == **0** → fall through → `%a5@(0)` set to **3** → master dispatch routes to `0x3ad6e → 0x3a180` (watchdog); `0x3abfe` never reached.

---

## Phase 3 — Initialization chain

- `%a5@(0)` = `0xFF0000` (A5 base, KF-008 arcade-workram domain `0xFF0000..0xFF3FFF`).
- **BSS-cleared: YES.** Boot zero-fill at `0x3b0ea` (`lea 0xff0000,%a0; movew #0,%a0@; movew #8191,%d0; movew %a0@+,%a1@+` loop) zeroes `0xFF0000..0xFF3FFF`, covering `%a5@(0)`. **STATICALLY_PROVEN** (`genesis_postpatch.disasm.txt:73892-73898`).
- **Explicit init writers before main loop: NONE.** All seven writers live in the VBlank/state-handler region (`0x3A4xx..0x3AExx`), dispatched from the VBlank handler — none on the boot path before interrupts enable.
- **Therefore at the first VBlank, `%a5@(0)` enters as 0.** But the prologue routine `0x3ad7c` runs (at `0x3a23e`) *before* the dispatch (at `0x3a256`) within that same VBlank, so the value actually read at `0x3a256` is 0 **only if the gate bit keeps the state-3 write skipped**. The first-frame dispatch can already see state 3. **EXPECTED_BUT_RUNTIME_DEPENDENT.**

---

## Phase 4 — Static possibilities + observation cross-reference

- If `%a5@(0)==0` at the dispatch read, the translated code **necessarily** reaches `0x3abfe` (computed `jmp`, STATICALLY_PROVEN). Non-reach therefore implies `%a5@(0)!=0` at every dispatch in the window.
- Non-title targets for non-zero values: state 1 → `0x3aaac`, state 2 → `0x3a35a`, state 3 → `0x3ad6e→0x3a180` (watchdog).

**Observation cross-reference (NOT semantic classification):** BM-006 register samples during the dominant watchdog loop (frames 128/132/140, PCs `0x3a196/0x3a192/0x3a19c`) show **`A0 = 0x0003AD6E`**. The master dispatch leaves `A0 = 0x3a26c + table_word`; for state 3 that is exactly `0x3a26c + 0x0b02 = 0x3ad6e`. The residual `A0` value is consistent with the master dispatch having routed via **state 3** into the watchdog. This is corroboration, **not proof** — `A0` could in principle be set elsewhere, and the watchdog is also reachable from the main loop (`0x3b292 → 0x3a1a8`), though that path does not compute `A0=0x3ad6e`. The expected-if-gate-clear value (3) matches the observation.

*Observed but not classified:* `0x0003AF40` (8 frames) and other excursion PCs are not investigated per scope.

---

## Phase 5 — Outcome classification

### Outcome: **B — Static path translated-flow equivalent; runtime evidence needed.**

The complete master-state machinery — the dispatch read (`0x3a256`), the table (`0x3a26c`), and all seven `%a5@(0)` writers — is translated-flow equivalent arcade↔Genesis. The only arcade↔Genesis differences are standard hardware-address redirects, the load-bearing one being the **state-3 gate**: arcade `btst #2,0x390007` (TC0040IOC) → Genesis `btst #2,0xff60ff` (WRAM mirror). No static divergence in the master-state machinery itself is causally established; whether `%a5@(0)` holds 0 vs 3 at dispatch hinges on the runtime value of the gate mirror `0xff60ff` bit 2, populated by a shim outside this bounded scope.

**Smallest runtime evidence needed:** the value of `%a5@(0)` at the master dispatch read `0x0003A256` (expected, if the cross-reference holds: 3). Capture point named; instrument **not** designed (per directive).

---

## Phase 6 — KNOWN_FINDINGS impact

**Option A — no KF update proposed.** Per the task's Chad-Jr. default, Outcome B does not justify a KF update; the load-bearing claim (the input-gate routing state to the watchdog) is still a runtime-dependent hypothesis pending the `0xff60ff` value. The STATICALLY_PROVEN master-table target map (state 0→title, 1→`0x3aaac`, 2→`0x3a35a`, 3→watchdog `0x3a180`) is documented here in Phase 1 as a candidate for a future KF-003 refinement once the runtime value is confirmed; promoting it now would canonize an unverified runtime interpretation.

---

## Recommended next task

**BM-007 parked-helper bookmark on Genesis runtime PC `0x0003ADD6`** (writer #6, the state-3 write) — reuses the existing bookmark instrument (no state-capture design needed) and is decisive:
- **Reached** → the prologue gate at `0x3ad96` fell through → `%a5@(0)` is being set to 3 → routes master dispatch to the watchdog → explains the non-reach of state-0 target `0x3abfe`. The investigation then moves to the **next bounded task: audit the Genesis input-shim that populates `0xff60ff` bit 2 vs arcade `0x390007`** (TC0040IOC, KF-022 active-low) — the suspected polarity/population defect.
- **Not reached** → the gate is taken (bit 2 set) → `%a5@(0)` stays 0 → the non-reach of `0x3abfe` needs a different explanation (re-examine whether the VBlank handler reaches `0x3a256` every frame).

Because `0x3add6` is reached at most a few times (the routine early-returns once `%a5@(0)==3`), a parked-helper bookmark there cleanly catches the single state-3 transition. *Alternative, if a value (not reachability) is preferred:* a direct `%a5@(0)` state-capture at `0x0003A256` (instrument design deferred to a separate task).

This is an evidence-capture handoff, not implementation. No Outcome-A divergence exists, so no Cody fix is proposed.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; localization sharpened to the state-3 input gate; no status change).
- Closed issues touched: NONE. New issues opened: NONE. Issues closed: NONE. Deferred: NONE.

## STOP triggered

NO.
