# Andy — Build 0104 HV-Counter Cluster Decode (BlastEm "Illegal write to HV Counter port 8")

**Author:** Andy
**Date:** 2026-06-25
**Build context:** post-BM-011 MISS; canonical Build 0105 (`dist/rastan-direct/rastan_direct_video_test_build_0105.bin`, SHA `b8e16f7c…db72`, byte-identical to Build 0097, `cmp=0`; opcode_replace 96 / 0x17CD28; no bookmark, no HV fix). rastan-direct.
**Scope:** Static analysis only. No source/spec/tool/ROM/build changes. No bookmark insertion. No HV fix. No sanitizer. Disassembly from the canonical 0105 ROM via `m68k-elf-objdump` and the ELF symbol table; addresses are **runtime_genesis_pc = ROM file offset** (verified: `0x70244` bytes = `48e7 fffe 4bf9 00ff 0000`). Labels: **[OBS]** = observable disassembly/bytes/symbols (proven); **[INT]** = interpretation.

---

## Phase 0 — Baseline

**Relevant priors:** KF-028/KF-010/KF-013 (title render + 3AD44 dispatch), Build 0094 `genesistan_hook_3ad44_dispatch` body read, OPEN-005 (historical HV), Build-54-era HV notes. **Classification:** EXTENDING (OPEN-017). **Issues:** OPEN-017 active, OPEN-005 context, OPEN-015 not touched. **Contradiction:** NONE with priors; this report **corrects one Cody scan result** (see §1). **Architecture compliance:** the implicated code is a Genesis-side **diagnostic audit guard** (scaffolding), not arcade-owned control flow; any fix is a CANDIDATE for Tighe + carries the scaffolding-disclosure / audit-trail obligation.

**Crash-predates-scroll-fix acknowledged: YES.** The Build 0097 scroll/display-origin commit (`0x701F0`, the `move.l #0x40000010,0xC00004` VSRAM setup at `0x7021A`, etc.) is analyzed below **as context only** and is exonerated — every one of its accesses is a legal VDP write (§2). The actual mechanism (§3) is older scaffolding unrelated to the scroll fix.

---

## 1. Headline result (proven)

**The "Illegal write to HV Counter port 8" is the diagnostic AUDIT-GUARD's HV-counter READ, not any boot/init VDP write.**

- In the assumed bisection interval **0x70000–0x70244**, there is **NO access to 0xC00008** of any kind. Every VDP access is a legal control- or data-port write (full decode table, §2). [OBS]
- A literal scan of the **entire** `genesis_only` region (0x70000–0x17CD28) finds the HV-counter port `0xC00008` referenced by **exactly two instructions, both READS**: [OBS]
  ```
  7186C: 33f9 00c0 0008 00ff 678c   move.w (0x00C00008).l, (0x00FF678C).l   ; → audit_guard_vcount
  71BC6: 33f9 00c0 0008 00ff 678c   move.w (0x00C00008).l, (0x00FF678C).l   ; → audit_guard_vcount
  ```
- A scan of the **arcade-translated** region (0x200–0x70000) finds **no** `0xC00008` access (the lone `00c0 000b` byte-match at `0x4A728` is an `ori.l #0x00C0000B,(a1)` immediate operand — data, not a VDP access). [OBS]

Both reads live in **audit-guard scaffolding** ("Reuse §7.3 audit-guard capture + heartbeat halt loop", `pc090oj_hooks.s:408`/`:420` and the sibling `genesistan_pc090oj_hook_audit_guard`, `0x71BA6`). [OBS]

> **Correction to Cody's scan:** the prior report "NO instruction with effective address 0xC00008 in this window" is **incomplete** — two instructions DO target `0xC00008` (as the READ source). They were almost certainly missed because the scan looked for `0xC00008` as a write **destination**; here it is the **source** operand. The boot interval is genuinely clean; the HV access is just **above** the claimed upper bound. [OBS+INT]

---

## 2. VDP access table — interval 0x70000–0x70244 (every access; all legal) [OBS]

Decode of the control-port command words (`vdp_set_reg` builds `0x8000 | (reg<<8) | val`; `vdp_set_vram_write_addr` builds the 32-bit address command):

| runtime_pc | bytes | disasm | EA | size | command-word decode | legal? | port-8? |
|---|---|---|---|---|---|---|---|
| 0x70088 | `33c2 00c0 0004` | `move.w d2,0xC00004` | 0xC00004 | W | register-set `100R RRRR DDDD DDDD` (bits15-14=`10`); regs 0–18 written (`0x8004,0x8134,0x8238,0x833C,0x8406,0x857C,0x8700,0x8AFF,0x8B00,0x8C81,0x8D3F,0x8F02,0x9001,0x9100,0x9200`) | YES | NO |
| 0x700AE | `23c1 00c0 0004` | `move.l d1,0xC00004` | 0xC00004 | **L** | VRAM-write addr command (e.g. `0x60000003` for 0xE000): high word→0xC00004, low word→**0xC00006** (both control) | YES | NO |
| 0x70122 | `33d8 00c0 0000` | `move.w (a0)+,0xC00000` | 0xC00000 | W | VRAM data (tile commit) | YES | NO |
| 0x70160 | `33d8 00c0 0000` | `move.w (a0)+,0xC00000` | 0xC00000 | W | VRAM data (BG strip) | YES | NO |
| 0x701AE | `33d8 00c0 0000` | `move.w (a0)+,0xC00000` | 0xC00000 | W | VRAM data (FG strip) | YES | NO |
| 0x701D0 | `23fc C0000000 00c0 0004` | `move.l #0xC0000000,0xC00004` | 0xC00004 | **L** | CRAM-write addr command → 0xC00004 + 0xC00006 (both control) | YES | NO |
| 0x701E4 | `33d8 00c0 0000` | `move.w (a0)+,0xC00000` | 0xC00000 | W | CRAM data (palette) | YES | NO |
| 0x70204 | `33c0 00c0 0000` | `move.w d0,0xC00000` | 0xC00000 | W | VRAM data (HSCROLL word, X−16 bias) — *Build 0097 context* | YES | NO |
| 0x70214 | `33c0 00c0 0000` | `move.w d0,0xC00000` | 0xC00000 | W | VRAM data (HSCROLL word) — *context* | YES | NO |
| 0x7021A | `23fc 40000010 00c0 0004` | `move.l #0x40000010,0xC00004` | 0xC00004 | **L** | VSRAM-write addr command → 0xC00004 + 0xC00006 (both control) — *context* | YES | NO |
| 0x7022C | `33c0 00c0 0000` | `move.w d0,0xC00000` | 0xC00000 | W | VSRAM data (Y+8 bias) — *context* | YES | NO |
| 0x7023A | `33c0 00c0 0000` | `move.w d0,0xC00000` | 0xC00000 | W | VSRAM data — *context* | YES | NO |

**Every effective address is 0xC00000 (data) or 0xC00004 (control).** The three LONG writes target 0xC00004, so their second bus cycle lands on **0xC00006** — still the control-port mirror (BlastEm decodes offsets 4 and 6 both as control; HV region begins at offset 8). **No write spills to 0xC00008.** No command word is malformed; no register number is out of range; no DMA is triggered (MODE2=`0x34` sets the DMA-enable bit but nothing programs a DMA source/length/trigger). [OBS+INT]

**Boot vs interrupt path** [OBS+INT]: `vdp_boot_setup` (0x70000) `rts`-returns to **low ROM 0x22C** (`_bootstrap`: `jsr 0x70000` → `bsr _bootstrap_clear_staging` → `jsr load_scene_tiles 0x71EB8` → `jsr dma_self_test 0x71DAC` → `jmp 0x3A200`). During boot the only in-interval VDP accesses executed are `0x70088` (×15 register writes) and `0x700AE` (one VRAM-addr long). Everything from `0x700C2` onward is **`_vblank_service`**, reached only by the VBlank interrupt (masked `SR=0x2700` during boot) — i.e. the upper interval is **off the boot straight-line path**.

---

## 3. The real mechanism (proven) [OBS+INT]

`genesistan_hook_3ad44_dispatch` (`pc090oj_hooks.s:353`) routes by A0:
```
A0 ∈ [0x00C00000, 0x00C10000)  → tilemap  (BG/FG fill)
A0 ∈ [0x00D00000, 0x00D00800)  → PC090OJ
else                           → .Lhook_3ad44_audit   ← AUDIT FALL-THROUGH
```
`.Lhook_3ad44_audit` (`pc090oj_hooks.s:408`, disasm `0x71850`):
```
71850  move.l 60(sp),0xFF674A          ; audit_guard_caller_pc  = return PC of the caller
71860  (loop) snapshot 15 regs → 0xFF674E (audit_guard_register_snapshot)
7186C  move.w 0xC00008,0xFF678C         ; audit_guard_vcount = HV-counter read   ◄── the flagged access
71876  move.w #0x3AD4,0xFF678A          ; audit_guard_fired_flag = 0x3AD4 (this is the 3AD44 audit)
7187E  bra 0x71BD8                       ; → heartbeat halt loop
71BD8  (loop) inc.b 0xFF678E ; bra 0x71BD8   ; audit_guard_heartbeat — HANGS FOREVER
```
The sibling guard `genesistan_pc090oj_hook_audit_guard` (`0x71BA6`, flag `0x510E`) has the identical structure and the second HV read at `0x71BC6`. [OBS]

**Sequence:** the 0x3AD44 fill-dispatch is called (during arcade title rendering, **after** `jmp 0x3A200`) with an A0 outside both expected windows → falls to `.Lhook_3ad44_audit` → **reads the HV counter (0xC00008)** as a diagnostic vcount → sets fired-flag `0x3AD4` → **spins in the heartbeat halt**. [OBS+INT]

**This matches the cross-emulator behavior exactly** [INT]: BlastEm/Nomad (strict) treat the `0xC00008` access as an illegal HV-port touch → **fatal / blank**; MAME (tolerant) services the access and proceeds into the heartbeat halt → **shows nothing** (hung). The crash predating the Build 0097 scroll fix is consistent — the audit guard and the 3AD44 dispatch predate 0097.

**Bisection reconciliation** [OBS+INT]: the only reliable probes are **BM-008@0x70000 HIT** and **BM-009@0x7186C MISS** → the offending access is in `(0x70000, 0x7186C]`, and the **only** HV access in that span is **at 0x7186C itself**. The "< 0x70244" upper bound is an artifact: `0x70244`/`0x70C36` sit on the `_vblank_service`/non-boot paths (unreachable in straight-line boot), so their MISS does **not** bound the crash below them. **The proven offending access is 0x7186C, above the assumed interval.**

---

## Answers to the required questions

1. **Actual effective write to 0xC00008 in 0x70000–0x70244?** **NO.** And none anywhere in the ROM. The only `0xC00008` accesses are two **READS** at `0x7186C`/`0x71BC6` (audit guards), above the interval. [OBS]
2. **Which access is BlastEm labeling "HV Counter port 8," and why?** The audit-guard **HV-counter read** `move.w 0xC00008,audit_guard_vcount` at **0x7186C** (and/or its sibling 0x71BC6), executed when an audit guard fires. [OBS+INT] *Read-vs-write caveat:* the instruction is observably a **READ**; BlastEm's "write" wording is the one item not provable from bytes — most likely BlastEm's HV-port-violation message text, or report paraphrase. Confirm via BlastEm's logged PC (expected `0x7186C`).
3. **Before 0x70088 / at first control writes / in data writes?** **None of these.** The trigger is **not** in the boot init at all; it is the audit fall-through of `genesistan_hook_3ad44_dispatch`, reached during arcade title rendering. [OBS+INT]
4. **Classification:** Closest to **(C) — a genuine access prior scans missed** (the two audit-guard HV reads). It is **not** (A) malformed command word, **not** (B) mis-sequenced control-then-data, **not** (E) register/DMA — §2 proves all boot/init command words legal. Underlying nature: **Genesis-side diagnostic SCAFFOLDING** (audit guard) reading HV, reached because of an **unexpected A0** in the 3AD44 dispatch. **Genesis-bug, not arcade-intent** (the arcade program never reads the Genesis HV counter). [OBS+INT]
5. **Safe local fix CANDIDATE (not implemented):** **see §4 — CANDIDATE, two layers, named sites.** Symptom site: `.Lhook_3ad44_audit` HV read (`pc090oj_hooks.s:420`, runtime `0x7186C`) + sibling (`0x71BC6`). Root site: `genesistan_hook_3ad44_dispatch` A0 range logic (`pc090oj_hooks.s:353`).
6. **If decode inconclusive — next BM-012 target:** **Location no longer needs bisection** (it is `0x7186C`). Instead read the **WRAM audit record the scaffolding already captured** (§4). If a probe is still wanted, place BM-012 at `genesistan_hook_3ad44_dispatch` entry to log A0 per call and catch the offending caller.

---

## 4. Fix CANDIDATE only (NOT implemented; Tighe decision; scaffolding rules apply)

The audit guard **already recorded everything needed** — read these at the BlastEm/MAME halt (no new instrumentation, no rebuild): [OBS]
- `audit_guard_caller_pc` = **0xFF674A** — the PC that called the 3AD44 dispatch with the bad A0.
- `audit_guard_register_snapshot` = **0xFF674E** (15 longs) — includes the offending **A0** and **D1**.
- `audit_guard_fired_flag` = **0xFF678A** — `0x3AD4` (this guard) vs `0x510E` (sibling) tells you which dispatch fired.
- `audit_guard_vcount` = **0xFF678C**, `audit_guard_heartbeat` = **0xFF678E** (proves the halt was entered).

**Two layers — the symptom fix alone is insufficient:**
- *Symptom:* removing/neutralizing the HV read at `pc090oj_hooks.s:420` (and the sibling) stops BlastEm flagging `0xC00008`, **but the heartbeat halt still hangs** — so this only changes the failure from "fatal HV" to "silent hang." It does not restore execution.
- *Root:* the genuine defect is the **unexpected A0 reaching `genesistan_hook_3ad44_dispatch`** (A0 ∉ tilemap C-window ∪ PC090OJ). The real fix targets the caller / the A0 range logic, identified by the WRAM record above.

**Safe local fix candidate: NO** — not a one-line local change. The flagged access is intentional diagnostic scaffolding; the actionable defect is upstream (bad A0) and must be identified from the captured WRAM record first. The audit guard is **scaffolding**: any edit to it (or any NOP/RTS) requires explicit Tighe authorization + the scaffolding-disclosure / audit-trail obligation, and an inventory of the guard's removal.

---

## Open / Closed Issues Impact

- Open issues touched: **OPEN-017** (active — HV crash cluster mechanism PROVEN: audit-guard HV read at `0x7186C`, fired by an unexpected A0 in the 3AD44 dispatch; **not** a boot/init VDP write; bisection interval shown invalid; not closed pending the WRAM-record read of the real trigger). OPEN-005 (context — historical HV; this is a distinct, scaffolding-driven instance). OPEN-015 (not touched).
- New issues opened: NONE (recommend the team log "3AD44 dispatch unexpected-A0 audit fall-through" if not already tracked). Issues closed: NONE.
- Intentionally deferred: identity of the offending caller / A0 value (→ read the WRAM audit record, §4), the upstream A0-range fix, scaffolding removal plan, Start crash / OPEN-015.

## KNOWN_FINDINGS impact

**Option C — proposed new finding** (assess-only; not edited; Tighe/Chad Sr. approve):

> Build 0104/0105 HV-counter "Illegal write to HV Counter port 8" (BlastEm/Nomad fatal; MAME silent hang) is **not** a boot/init VDP write. Every VDP access in 0x70000–0x70244 is a legal control/data write (register-set words and address-command longs to 0xC00004→0xC00006, data words to 0xC00000); no access touches 0xC00008. The only `0xC00008` accesses in the ROM are two **HV-counter READS** in diagnostic audit-guard scaffolding — `.Lhook_3ad44_audit` (`pc090oj_hooks.s:420`, runtime `0x7186C`, fired-flag `0x3AD4`) and `genesistan_pc090oj_hook_audit_guard` (`0x71BC6`, flag `0x510E`) — each followed by an infinite heartbeat halt (`0x71BD8`). The guard fires from `genesistan_hook_3ad44_dispatch` when A0 ∉ [0xC00000,0xC10000)∪[0xD00000,0xD00800). Correction: the prior "no instruction targets 0xC00008" scan missed these (they target it as the READ source, not a write destination). The captured WRAM record (`audit_guard_caller_pc` 0xFF674A, `audit_guard_register_snapshot` 0xFF674E, `audit_guard_fired_flag` 0xFF678A) identifies the offending caller/A0.

Confidence: **STRONG/PROVEN** for: no HV write in the ROM; the only HV accesses are the two audit-guard reads; 0x7186C = BM-009 site; the dispatch fall-through condition; the heartbeat halt. **One item to confirm (not byte-provable):** BlastEm's "write" wording vs the observed READ — confirm via BlastEm's logged PC (expected 0x7186C).

## STOP triggered

NO.
