# Andy — 0xff60ff Input-Shim Audit vs Arcade 0x390007 (TC0040IOC Bit 2), Build 0077

**Author:** Andy
**Date:** 2026-06-13
**Build:** 0077 (canonical baseline SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** STATIC audit only, bounded to `0xff60ff` bit 2 and arcade `0x390007` bit 2. Documentation-only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No instrument/implementation design.

All addresses are Genesis runtime PC / ROM file offset (KF-004); arcade-source equivalents (`= Genesis − 0x200`, KF-006) are cross-reference.

---

## Phase 0 — Baseline statement

**Classification:** EXTENDING (touches KF-003). **Phase 0 STOP:** not triggered; no CONFIRMED/STRONG contradiction.

**Relevant priors:** KF-003 (chain + progression-failure framing; HIGH), KF-004 (runtime PC = ROM offset; CONFIRMED), KF-008 (WRAM split: arcade workram `0xFF0000..0xFF3FFF`, Genesis BSS `0xFF4000..`), KF-022 (TC0040IOC inputs active-low: idle/unpressed = 1; CONFIRMED), KF-023/KF-024 (TC0040IOC control / DIP context). HIGH-hazard touched: KF-003, KF-004. None contradicted.

**Open issues touched:** OPEN-001, OPEN-004 (context only; no status change).

---

## §0 — Smallest proven statement

**Proven prior to this task:** BM-007 reached `0x0003ADD6` (state-3 writer); the gate at `0x0003AD96` (`btst #2,0xff60ff; bnes 0x3ade0`) governs it; bit 2 == 1 → skip writer, bit 2 == 0 → execute writer; per KF-022 arcade `0x390007` bit 2 idle = 1.

**NOT proven (preserved):** that the shim "has a defect"; that arcade bit 2 is supposed to be 1 in this context; that the gate is supposed to be taken in arcade; that `%a5@(0)` is 3 every frame; that any fix is justified; that the `movew #3,%a5@(0)` ever executed in an uninstrumented build.

---

## Phase 1 — Genesis readers/writers of `0xff60ff`

**Writers (full-file grep `,0xff60ff`):** exactly **one** — `0x711ac: moveb %d5,0xff60ff` (`genesis_postpatch.disasm.txt:124040`). **STATICALLY_PROVEN.**

**Readers (7):** `0x3a690` (`moveb`), `0x3a9b8` (`btst #1`), `0x3ab1a` (`moveb`), **`0x3ad96` (`btst #2` — the gate)**, `0x3ae04` (`btst #0`), `0x3ae94` (`btst #5`), `0x3aefe` (`btst #6`). **STATICALLY_PROVEN.** These mirror the arcade `btst`/`moveb` sites on `0x390007` (Phase 2), confirming `0xff60ff` is the WRAM mirror of arcade port `0x390007`.

**The sole writer sits inside the controller-poll shim at `0x710ca.`** The shim (`genesis_postpatch.disasm.txt:123977-124041`) initializes the Genesis I/O control ports (`0xa10009/0xa1000b`), reads controller DATA ports (`0xa10003`, `0xa10005`), and builds the input-mirror bytes `0xff60fc`, `0xff60fd`, `0xff60fe`, `0xff6100`, and `0xff60ff`.

**Address domain:** `0xff60ff` is `> 0xff4000` → **Genesis BSS domain** per KF-008 (NOT translated arcade workram). The writer is Genesis-side shim code, as expected for a hardware-input translation. **STATICALLY_PROVEN.**

### Bit-2 derivation in the shim (the load-bearing detail)

`%d5` (written to `0xff60ff`) is built as (`genesis_postpatch.disasm.txt:124021-124040`):
```
7116e:  moveq #-1, %d5         ; d5 = 0xFF (all bits set)
71170:  btst #5,%d6 / bclr #3,%d5   ; conditionally clear bit 3
7117a:  btst #5,%d7 / bclr #4,%d5   ; conditionally clear bit 4
...     (coin logic) / bclr #5,%d5  ; conditionally clear bit 5
711ac:  moveb %d5, 0xff60ff
```
**Bit 2 of `%d5` is never cleared** — only bits 3, 4, 5 are. So the shim writes `0xff60ff` **bit 2 = 1 unconditionally**. Per KF-022 active-low, bit 2 = 1 = idle/unpressed — the correct value for the no-input title context. **STATICALLY_PROVEN.**

### Caller analysis (decisive)

Full-file search finds **no reference to the shim entry `0x710ca`** — no `jsr`/`bsr`/`jmp` immediate, and no pointer-table word `0007 10ca` (the only `710ca` hit besides the definition is unrelated high-ROM data at `0x1710ca`; all `10ca` hits are `%a5@(4298)` displacements). The shim entry is preceded by `rts` at `0x710c8`, so it is not reached by fall-through either. **STATICALLY_PROVEN: the shim entry `0x710ca` is unreferenced in the Build 0077 disassembly.**

→ **INFERRED (strongly corroborated):** the shim does not execute (a computed/indirect call cannot be statically excluded, but none is evident; corroborated by BM-007, where the gate fell through — i.e., `0xff60ff` bit 2 was 0, consistent with the mirror never being written to 1).

---

## Phase 2 — Arcade readers/writers of `0x390007`

**Reads (11):** `0x124`, `0x3a6`, `0x5cc`, `0x644`, `0x3a490`, `0x3a7b8`, `0x3a91a`, **`0x3ab96` (`btst #2` — the gate's arcade equivalent)**, `0x3ac04`, `0x3ac94`, `0x3acfe` (`maincpu.disasm.txt`). Bits 0,1,2,3,5,6 are all read across the game — `0x390007` is a live multi-bit input port.

**Writes: NONE.** No software write targets `0x390007`; it is a read-only TC0040IOC hardware input port (the hardware sets the bits each read). **STATICALLY_PROVEN / INFERRED (per KF-022).** Consequently the Genesis side, lacking that hardware, *must* run the shim to provide the equivalent value — there is no inline poll on the arcade-translated read sites (the Genesis reads at `0x3a690`/`0x3ad96`/… are plain mirror reads, not calls).

---

## Phase 3 — Translated-flow-equivalence at bit 2

- The shim's **value** for bit 2 (= 1, active-low idle) is **correct** and would make the gate at `0x3ad96` behave exactly as arcade `0x3ab96` (skip the state-3 writer, keep `%a5@(0)==0`, reach the title dispatcher `0x3abfe`). If the shim ran before the gate, the path would be translated-flow equivalent.
- But the shim **is unreferenced** (Phase 1) and `0xff60ff` is **not boot-initialized** (Phase 4). So at runtime the mirror is never set to the idle value; the gate reads the uninitialized byte. **The runtime equivalence fails not because the shim computes the wrong value, but because the value is never delivered.**

**Translated-flow equivalence at bit 2: NO.**

---

## Phase 4 — Absence / initialization analysis

`0xff60ff` initialization sources:
- **Arcade WRAM zero-fill** at `0x3b0ea` clears `0xFF0000..0xFF3FFF` only — does **not** cover `0xff60ff`. **STATICALLY_PROVEN.**
- **Boot BSS clears** (`genesis_postpatch.disasm.txt` `.data` `0x272..0x2ea`): the relevant loops clear `0xff601a..0xff60f9` (loop at `0x29a`, 48 words ending `0xff60f8`) and resume at `0xff6104` (loop at `0x2ca`). **The bytes `0xff60fa..0xff6103` are a gap — never cleared.** This gap is exactly where the shim's mirror bytes (`0xff60fc..0xff6100`) live. **STATICALLY_PROVEN.**

So `0xff60ff` is initialized by **neither** the WRAM zero-fill nor the BSS clears, and its sole writer (the shim) is unreferenced. **`0xff60ff` is never written in Build 0077.** It retains its power-on RAM state; at the gate, BM-007 establishes bit 2 read as 0 (fall-through), the active-low "asserted" value — the inverse of idle.

This is **a complete and consistent explanation of BM-007 Outcome A**: the gate at `0x3ad96` reads an uninitialized `0xff60ff` (bit 2 = 0) → falls through → `movew #3,%a5@(0)` → master dispatch routes to state 3 → `0x3ad6e → 0x3a180` (watchdog), the dominant observed cadence. (Cross-reference, not new proof: the master-dispatch-selector audit's A0=`0x0003AD6E` residue.)

---

## Phase 5 — Outcome classification

### Outcome: **A — Static defect found.**

**Defect mechanism:** The Genesis input mirror `0xff60ff` (translating arcade TC0040IOC port `0x390007`) is populated only by the controller-poll shim whose entry `0x710ca` is **unreferenced** in Build 0077, and the byte is **outside every boot-clear range** (gap `0xff60fa..0xff6103`). The shim, if run, would write the correct active-low idle value (bit 2 = 1); because it never runs and the byte is never initialized, the gate at `0x0003AD96` reads bit 2 = 0 and routes the master state machine to state 3 (watchdog) instead of the title dispatcher.

**Evidence categories:** sole writer / bit-2 value / unreferenced entry / boot-clear gap = STATICALLY_PROVEN; "shim never executes" = INFERRED (strongly corroborated by BM-007).

**Recommended Cody fix SCOPE (recommendation only — Andy does not draft code):** establish/restore the invocation of the input-poll shim at `0x710ca` on the Genesis per-frame input-servicing path so the mirror (`0xff60fc..0xff6100`, including `0xff60ff`) is populated **before** the arcade VBlank handler consumes it. Investigate first whether a call site existed and was dropped (possible regression) versus never wired. *Note:* merely BSS-initializing `0xff60ff` to the idle value would unblock this one gate but leave the entire input mirror stale/non-functional — not the real fix. This fix targets OPEN-004 (and likely unblocks OPEN-001 downstream).

---

## Phase 6 — KNOWN_FINDINGS impact

**Option B — proposed NEW KF entry.** Outcome A identifies a concrete, durable, non-obvious mechanism distinct from KF-003's dispatch-chain framing: the input-mirror subsystem wiring gap. Proposed entry (Cody applies after Tighe ack; Andy does not edit `KNOWN_FINDINGS.md`):

> **KF-028 (candidate) — Genesis input mirror `0xff60fc..0xff6100` is unpopulated in Build 0077.** Confidence: CONFIRMED (static facts) / STRONG (causal link to state-3 routing). Applicability: BUILD_SPECIFIC (Build 0077). Rediscovery Hazard: HIGH. **Finding:** The arcade TC0040IOC input port `0x390007` is mirrored on Genesis at WRAM `0xff60ff` (and neighbors `0xff60fc..0xff6100`), read by the arcade-translated code at `0x3a690/0x3a9b8/0x3ab1a/0x3ad96/0x3ae04/0x3ae94/0x3aefe`. The sole writer of `0xff60ff` is `0x711ac`, inside the controller-poll shim at `0x710ca`; that entry is unreferenced in Build 0077, and `0xff60ff` lies in the boot-clear gap `0xff60fa..0xff6103`, so the mirror is never initialized or updated. The shim, if run, writes `0xff60ff` bit 2 = 1 (KF-022 active-low idle). **Use as prior:** when arcade-translated code reads `0xff60xx` input-mirror bytes, do not assume they reflect controller state in Build 0077; the mirror is unpopulated until the `0x710ca` shim is wired in. Cross-ref KF-003, KF-022.

---

## Recommended next task

Cody implementation task (recommendation): **wire the input-poll shim `0x710ca` into the per-frame input-servicing path** ahead of the arcade VBlank handler; first determine whether the call site was dropped or never present. After the fix, re-run a reachability check on `0x0003ABFE` (title dispatcher) to confirm the master state now stays 0 and the title path is reached. This is the concrete forward step from Outcome A.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; root-cause localized to the input-mirror wiring gap; no status change pending fix verification).
- Closed issues touched: NONE. New issues opened: NONE. Issues closed: NONE. Deferred: NONE.

## STOP triggered

NO.
