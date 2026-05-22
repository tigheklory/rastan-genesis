# Andy — BM-002 Activator Runtime Failure Investigation

**Agent:** Andy (Claude Code)
**Type:** Investigation/classification (analytical only — read-only inspection of preserved evidence; no implementation; no builds; no ROM changes; no evidence-file changes)
**Build:** rastan-direct, post-BM-002-Revert. Canonical baseline Build 0070, SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`. Diagnostic Build 0069 frozen on disk, SHA `e206d3cf3f50639727119ceded4271e95d8f3c1fb93f44eb6607dfc865aaf96a`.
**Date:** 2026-05-17
**Naming:** descriptive output filename per OPEN-002 extended policy.

---

## 0. Executive verdict

**Root cause: Classification (A) — address-space / translation mismatch in the bookmark target-selection workflow.**

Cody equated the trace's observed `pc=03a19c` value (which is a runtime Genesis 68000 PC after the `+0x200` arcade-ROM relocation) with the spec's `arcade_pc` field (which is in arcade-source coordinates, before relocation). These spaces differ by `identity_offset = 0x200` per `address_map.json`. The activator bytes were correctly placed at ROM file offset `0x03A39C` (= `arcade_pc 0x03A19C + 0x200`), but the CPU executing at runtime PC `0x03A19C` never reaches that location — it fetches from file offset `0x03A19C` (= arcade source `0x039F9C`), which contains an entirely different arcade routine (a delay loop + soft-reset preamble).

The activator at file offset `0x03A39C` was zero-hit during the trace window. The trace's seven hits at `pc=03a19c` were the CPU running the original `bnes 0x3a192` delay loop preserved verbatim in Build 0069 — the activator was never executed.

**BM-001 has the same fault.** Cody's BM-001 used `arcade_pc 0x055948`, patching file offset `0x055B48`. The trace observed runtime PC `0x055948`, which executes from file offset `0x055948` (= arcade source `0x055748`). Different arcade routines. BM-001's "helper not reached" result is therefore **not** a statement about arcade source `0x055948`'s reachability — it tells us the CPU never reached runtime PC `0x055B48` in the BM-001 trace window. The strip-producer-dispatcher's reachability question that motivated BM-001 is **still open**.

**Span safety is NOT the primary fault.** Phase 4 analysis confirms `41FA 000E D0C0 3010` is a coupled PC-relative sequence with downstream `A0`/`D0` dependencies. If the activator JMP had fired and parked at the helper, the span damage would never have mattered (helper is `bra .`). Classification (B) is contributory if the activator is ever placed correctly on a PC-relative span without firing — but it's not what caused BM-002's runtime failure.

**Recommendations (not implemented in this task):**
- **OPEN-012** (new) — track the address-space-translation workflow fault. Workflow must translate trace `pc=X` → `arcade_pc = X - identity_offset(X)` via `address_map.json` before populating the spec.
- BM-001 result invalidated; re-run after the fix produces meaningful evidence.
- BM-002's chosen runtime target (the delay-loop / soft-reset code at runtime PC `0x03A19C`) is excellent positive-control material; re-issue as BM-003 (or whatever next BM-NNN) with `arcade_pc = 0x039F9C`.
- Target-selection criteria should also screen for PC-relative spans (Class B preventive), even though the BM-002 failure was not span-related.

---

## §1 Phase 1 — Address translation resolved from address_map.json

### §1.1 arcade_pc 0x03A19C → ROM file offset

From `build/rastan-direct/address_map.json` (Global Rule 13 authority), the segment containing arcade_pc `0x03A19C`:

```json
{
  "genesis_start": "0x03A2C8",
  "genesis_end_exclusive": "0x03A3D8",
  "size_bytes": 272,
  "kind": "arcade_copy",
  "arcade_start": "0x03A0C8",
  "arcade_end_exclusive": "0x03A1D8",
  "source": "whole_maincpu_copy",
  "identity_offset": 512
}
```

`arcade_pc 0x03A19C` falls in `[0x03A0C8, 0x03A1D8)` → ROM file offset = `0x03A19C + 0x200 = 0x03A39C`. **This is where Cody placed the activator.**

### §1.2 Runtime Genesis PC for that ROM file offset

The Genesis maps cartridge ROM directly into the 68000 address space starting at address `0x000000`. When the CPU fetches an instruction with PC = `N`, it reads bytes from file offset `N` of the cartridge ROM. So:

- File offset `0x03A39C` → runtime Genesis PC `0x03A39C`
- File offset `0x03A19C` → runtime Genesis PC `0x03A19C`

These are different runtime PCs. The activator at file offset `0x03A39C` is reached only when the 68000's PC = `0x03A39C`, NOT when PC = `0x03A19C`.

### §1.3 Trace's pc=03a19c is the runtime Genesis PC

The MAME trace records the 68000's literal PC value. When the trace shows `pc=03a19c`, the CPU's PC register held the value `0x03A19C`, which fetches from file offset `0x03A19C`.

**This is decisive:** Cody equated trace `pc=03a19c` (runtime PC) with the spec's `arcade_pc 0x03A19C` (arcade-source PC). They differ by `identity_offset = 0x200`. The correct correspondence:
- Trace `pc=03a19c` → runtime PC `0x03A19C` → arcade source `0x03A19C - 0x200 = 0x039F9C`
- Spec `arcade_pc 0x03A19C` → runtime PC `0x03A19C + 0x200 = 0x03A39C`

To patch the code executing at trace `pc=03a19c`, the spec's `arcade_pc` should have been `0x039F9C` (NOT `0x03A19C`).

---

## §2 Phase 2 — Activator bytes verified by direct ROM inspection

### §2.1 Bytes at ROM file offset 0x03A39C (Build 0069)

```
dd if=Build_0069 bs=1 skip=0x03A39C count=16 → 4ef9 0007 1c78 4e71 41fa 0006 d0c0 4ed0
```

First 8 bytes: `4E F9 00 07 1C 78 4E 71` = `JMP $00071C78` + `NOP`. Activator IS correctly placed at file offset `0x03A39C`. The trailing `41fa 0006 ...` is the next-instruction arcade code (the LEA at arcade source `0x03A1A4`).

### §2.2 Bytes at ROM file offset 0x03A19C (Build 0069)

```
dd if=Build_0069 bs=1 skip=0x03A19C count=16 → 66f4 2e78 0000 2078 0004 4ed0 6502 60e0
```

These are the **original arcade-copied bytes**, identical between Build 0069 (diagnostic) and Build 0070 (canonical revert). Confirmed by `dd if=Build_0070 bs=1 skip=0x03A19C count=16 → 66f4 2e78 0000 2078 0004 4ed0 6502 60e0` (byte-identical to Build 0069).

The bytes at file offset `0x03A19C` are NOT the activator. They are the original delay-loop / soft-reset preamble:

```
0x03A19C: 66F4         bnes 0x3A192    ; delay loop back-edge
0x03A19E: 2E78 0000    moveal 0x0, %sp ; reload SP from address 0x0000
0x03A1A2: 2078 0004    moveal 0x4, %a0 ; load reset vector from address 0x0004
0x03A1A6: 4ED0         jmp %a0@        ; jump to reset entry point
0x03A1A8: 6502         bcss 0x3A1AC
0x03A1AA: 60E0         bras 0x3A18C
```

This matches the postpatch disasm at lines 72727-72731. The reset vector at file offset `0x0000 0004` = `00000202` (verified by hex dump), so the `jmp (a0)` jumps to `0x00000202` — the `_bootstrap` entry point per `verify_rastan_direct_boot_guard.py:11`.

### §2.3 Helper resolution

`4EF9 00 07 1C 78` resolves to `JMP $00071C78` — the helper address. Verified against `apps/rastan-direct/out/symbol.txt` `0x00071c78 T genesistan_diag_bookmark` (per BM-002 insert_meta line and prior Build 0067 BM-001 evidence). Resolution is correct. Classification (C) helper-resolution-fault is **ruled out**.

### §2.4 The decisive comparison

When the trace records `pc=03a19c`, the CPU is fetching from file offset `0x03A19C` — which contains the **original bnes/jmp sequence**, NOT the activator. The activator at file offset `0x03A39C` is reached only if the CPU's PC = `0x03A39C`, which the trace never observed (verified by `grep "pc=03a3" mame_run_log.txt` → zero matches).

---

## §3 Phase 3 — Control flow to crash reconstructed

### §3.1 Trace observation (top observed PCs)

Top 10 PCs in `mame_run_log.txt`:

| Count | PC | Disasm at file offset = PC |
|---:|---|---|
| 17 | `pc=03a196` | `subil #1, %d1` (delay-loop decrement) |
| 16 | `pc=03a19e` | `moveal 0x0, %sp` (post-loop SP reload) |
| 11 | `pc=03a198` | (interior of `subil #1, %d1` instruction) |
| 7 | `pc=03a19c` | `bnes 0x3a192` (delay-loop back-edge) |
| 5 | `pc=071314` | (inside helper region, near `genesistan_palette_hook_3ba64` at `0x712A0`) |
| 5 | `pc=00030a` | (low memory; near bootstrap re-entry chain) |
| 4 | `pc=03b0c6` | (early arcade startup) |
| 3 | `pc=03af40` | (early arcade startup) |
| 3 | `pc=03af3e` | (early arcade startup) |
| 3 | `pc=03a194` | (delay-loop entry; just before `subil`) |

The trace is dominated by the delay loop at `0x03A192..0x03A19C` cycling repeatedly. This matches OPEN-004's bootstrap re-entry pattern.

### §3.2 The control-flow narrative

1. CPU enters the delay loop at runtime PC `0x03A192` (`movel 0x0, %d0; subil #1, %d1; bnes 0x3a192`).
2. After many iterations, the `bnes` falls through (condition fails).
3. CPU executes `moveal 0x0, %sp` (`0x03A19E`) — reloads SP from address `0x0000`.
4. CPU executes `moveal 0x4, %a0` (`0x03A1A2`) — loads `A0` with the reset vector at address `0x00000004` = `0x00000202`.
5. CPU executes `jmp (a0)` (`0x03A1A6`) → jumps to `0x00000202` = `_bootstrap` entry.
6. Bootstrap re-entry per OPEN-004 begins again; eventually some path takes execution to other PCs (Tighe observed `0x00070628`, then `0x00000518`, then crash at `0x00000116`).

### §3.3 Identifying the intermediate PCs Tighe observed

**`0x00070628`** — between symbols `0x00070570 T genesistan_hook_tilemap_bg_fill` and `0x00070646 T genesistan_hook_text_writer_3c4d2` per `apps/rastan-direct/out/symbol.txt`. PC `0x00070628` is inside the body of `genesistan_hook_tilemap_bg_fill`. This is consistent with `Andy_nametable_composition_path_classification.md` — the polymorphic dispatch at `0x03AD44` can route to this hook from the bootstrap transit region.

**`0x00000518`** — disasm at line 371 shows `518: 60fa bras 0x514`. Hex bytes at file offset `0x0518`: `60fa 4e72 2700 60fa 33fc 8004 00c0 0004` — `bras 0x514` followed by `STOP #$2700` and another `bras 0x514`. This is a crash-trap loop pattern; likely part of an exception or watchdog handler in low memory.

**Crash at `0x00000116`** — file offset `0x0116` contains `20 32 30 32 36 2E 41 50` = ASCII bytes ` 2026.AP` (ROM-header / cartridge-title region). When the CPU tries to fetch from `0x0116` as an instruction, it interprets `2032 3032` as `movel %a2@(32, %d3:w), %d0` — accessing an unaligned data location via `%a2 + 32`, which would trigger Address Error if `%a2 + 32` is misaligned or in invalid memory. Tighe's "Vector C8" notation is Exodus-specific; Address Error semantically matches this scenario.

### §3.4 Verdict on control flow

The crash chain Tighe observed (`0x03A19C → 0x00070628 → 0x00000518 → 0x00000116`) is consistent with: **OPEN-004 bootstrap re-entry under stress, eventually crashing on ROM-header bytes interpreted as code.** The activator at `0x03A39C` plays no role because it was never executed.

The Build 0069 visible crash is plausibly a longer-running variant of the same bootstrap-re-entry pathology already documented in OPEN-004, possibly with slight timing differences from the helper bytes occupying space at `0x00071C78` (helper introduction was Build 0060+, after the original OPEN-004 observations). This is speculation — what's certain is that the activator did not cause the crash.

---

## §4 Phase 4 — Span safety assessment

### §4.1 The replaced span

Cody replaced 8 bytes at arcade source `0x03A19C` (file offset `0x03A39C`):

```
0x03A19C: 41FA 000E    lea %pc@(0x3A1AC), %a0   ; PC-relative LEA — loads address into A0
0x03A1A0: D0C0         addaw %d0, %a0           ; A0 += D0
0x03A1A2: 3010         movew (%a0), %d0         ; D0 = word at (A0)
```

The disasm at lines 72909-72911 confirms this is a **jump-table lookup pattern**: LEA loads the base of an inline table; ADD scales by an index (`D0`); MOVE reads the offset entry. This is followed by another LEA + ADD + JMP at `0x03A3A4..0x03A3AA` (lines 72912-72914) — a second-stage indirection.

### §4.2 Downstream dependency

If the activator JMP fires (helper reaches park), the LEA-ADD-MOVE sequence never executes; downstream code that would have used `A0` and `D0` after this sequence is irrelevant because the helper parks forever. **Span safety is not a problem if the JMP fires.**

If the activator JMP does NOT fire (the scenario observed in BM-002), the issue isn't "the span runs wrongly" — it's that the CPU never even reaches the span (per Phase 2). So in this BM-002 case, the span replacement at file offset `0x03A39C` is inert.

### §4.3 Hypothetical: if BM-002 had landed at the right offset

Suppose Cody had used `arcade_pc = 0x039F9C` (correct target for runtime PC `0x03A19C`). The CPU would have hit the activator on the first delay-loop iteration, jumped to the helper, parked. The replaced bytes at file offset `0x03A19C` would have been `bnes 0x3a192` → activator. The delay loop would have been broken (no more `bnes` to re-iterate), but execution would never reach the now-broken code because the helper parks.

So the LEA-ADD-MOVE PC-relative coupling Cody worried about is NOT inherently unsafe for activator replacement — it's safe **conditional on the JMP firing**. The mechanism's whole design assumes the JMP fires.

### §4.4 Verdict on target-selection criteria

PC-relative-instruction screening is a **good preventive criterion** but not the primary cause of BM-002's failure. Recommend adding it as a target-selection criterion (Class B preventive), because:

1. If a future BM-NNN cycle picks a target whose JMP doesn't fire for some other reason (timing, branch around it, etc.), a PC-relative span left in NOP-padding territory could produce undefined behavior.
2. PC-relative instructions have implicit dependencies on the instruction's PC; replacing them is fragile in edge cases.

But this is a **secondary recommendation**. The primary fix is the address-space translation workflow (Classification A).

---

## §5 Phase 5 — Root cause classification

### §5.1 Primary classification: (A) Address-space / translation mismatch

**Decisive evidence:**
- `address_map.json` shows `identity_offset = 512` for the segment containing arcade_pc `0x03A19C`. arcade_pc and runtime PC differ by `+0x200`.
- Build 0069 file offset `0x03A19C` contains original bnes/jmp bytes (per Phase 2.2). File offset `0x03A39C` contains the activator (per Phase 2.1). The trace's `pc=03a19c` fetches from file offset `0x03A19C` (per Phase 1.3) — the original bytes, NOT the activator.
- Trace shows zero hits on `pc=03a39c` (`grep "pc=03a3" mame_run_log.txt` → 0).
- Trace shows 7 hits on `pc=03a19c` — all executing the delay loop, NOT the activator.

The trace's PC value is in runtime/Genesis space. Cody used it as if it were arcade-source space. Different arcade routines.

### §5.2 Alternative classifications ruled out

**(B) Unsafe span / target-selection fault — NOT primary.** The replaced span is PC-relative LEA-ADD-MOVE (objectively coupled), but the activator was never executed (per Phase 2). The span's PC-relative nature didn't matter because nothing ran. PC-relative screening would be a worthwhile preventive criterion (§4.4) but does not explain BM-002's failure.

**(C) Helper or activator resolution fault — RULED OUT.** §2.3 confirms `4EF9 00 07 1C 78` resolves to the helper address `0x00071C78`; helper bytes `60 FE` are at that address with correct SHA `20825b36...`. Resolution is correct.

**(D) Genuine mechanism failure — RULED OUT.** The mechanism would have worked correctly if the activator had been placed at the offset the CPU actually executes from. The 13-test synthetic matrix in OPEN-011's verification used scenarios that didn't exercise this specific translation workflow on a real positive-control target. The mechanism itself is sound; the workflow that selects targets is faulty.

**(E) Something else — N/A.**

### §5.3 Contributory factors

- The bookmark target-selection workflow's documentation (Cody's combined-task NOTES.md Phase 3) did not explicitly flag the trace-PC vs arcade-PC distinction. Cody's reasoning "pc=03a19c is provably executed → use arcade_pc 0x03A19C" treated them as the same space.
- §2.7 gate check verified activator bytes are correctly placed in the ROM **at the offset the spec asserts**, not "at the offset the CPU actually executes from." The §2.7 check passed because the bytes ARE at file offset `0x03A39C` (which is where `arcade_pc 0x03A19C + identity_offset` lands). The check didn't have visibility into whether `0x03A39C` is the offset the CPU reaches when the trace says `pc=03a19c`.

---

## §6 Phase 6 — BM-001 reassessment

### §6.1 BM-001 has the same fault

Cody's BM-001 used `arcade_pc 0x055948`. Per BM-001 insert_meta.txt:
- Pre-activator bytes at arcade_pc `0x055948` (Build 0062 @ ROM offset `0x055B48`): `0c6d000010a8660a`
- Post-activator bytes at arcade_pc `0x055948` (Build 0067 @ ROM offset `0x055B48`): `4ef900071c784e71`

Cody patched file offset `0x055B48` (= `0x055948 + 0x200`).

**Postpatch disasm comparison:**
- Runtime PC `0x055948` (file offset `0x055948`): `3b41 10d0` `movew %d1, %a5@(4304)` (line 107489)
- Runtime PC `0x055B48` (file offset `0x055B48`): `0c6d 0000 10a8` `cmpiw #0, %a5@(4264)` (line 107626; the dispatcher Cody intended to patch)

So the BM-001 trace observing `pc=055948` was the CPU at runtime PC `0x055948` executing `movew %d1, %a5@(4304)` (a different routine) — not the dispatcher at `0x055948` arcade-source.

### §6.2 BM-001 Outcome B is NOT trustworthy

BM-001's "helper not reached" result means: the CPU never reached runtime PC `0x055B48` during the trace window. It does **not** mean the strip-producer-dispatcher at arcade source `0x055948` was unreachable. The latter question — which motivated BM-001 in the first place — is **still open**.

The strip producers Andy classified in `Andy_nametable_composition_path_classification.md` (called from arcade source `0x055948`) are still the most-likely unreached code path for OPEN-001/OPEN-004. BM-001 didn't test that hypothesis.

### §6.3 Re-run requirement

After the workflow fix lands, BM-001 should be re-run with `arcade_pc = 0x055748` (= runtime PC `0x055948 - 0x200`) to test the original hypothesis (was runtime PC `0x055948` reached?), AND a separate cycle should test arcade source `0x055948` itself with a known-reached trace PC equivalent.

Both BM-001 (re-test runtime PC `0x055948`) and a fresh cycle (re-test arcade source `0x055948`) are needed to fully unblock OPEN-001/OPEN-004 evidence collection.

---

## §7 Phase 7 — Recommended next steps

### §7.1 Primary fix (Classification A)

The bookmark target-selection workflow must translate trace PCs to arcade_pc using `address_map.json` BEFORE writing them to the spec. Concretely:

- Given trace observation `pc=X` (a runtime PC), the workflow computes `arcade_pc = X - identity_offset(X)` where `identity_offset(X)` is looked up from the `address_map.json` segment containing `genesis_start <= X < genesis_end_exclusive`.
- For X in the `arcade_copy` whole_maincpu_relocated range (`0x000200..0x060200`), `identity_offset = 0x200`, so `arcade_pc = X - 0x200`.
- For X outside arcade-copy range (preserved-vectors region, helper region, etc.), `arcade_pc` may not be meaningful and the workflow should refuse (these are Genesis-native code locations, not arcade ROM).

The workflow change is documentation + procedure, not necessarily a tool change. Cody's combined-task NOTES.md target-selection section (Phase 3) needs an explicit address-space translation step.

**Optional supplementary check at gate time:** add a §2.7+ verification that for each `bookmark_cycle`-tagged opcode_replace entry, the trace artifact (if present) shows the CPU reaching the runtime PC `= arcade_pc + identity_offset`. If the trace shows zero hits at that runtime PC AND the bookmark cycle expected a positive control, the gate could warn (not fail — Insert builds may legitimately produce traces without the helper hit if the target is genuinely unreached).

### §7.2 Secondary fix (Classification B preventive)

Add PC-relative-instruction screening to target-selection criteria. A target span containing any of:
- `41FA xxxx` `lea %pc@(...), %a0` (and all 8 register variants `4xFA`)
- `4xFB` `lea %pc@(...,xx.w/l), %ax`
- `4Exx` related PC-relative jumps and BSRs (some forms)
- Other PC-relative addressing modes

should be flagged. Currently Cody's Phase 3 only screened for "no branch targets into the span." PC-relative screening is a separate criterion.

### §7.3 OPEN-001 / OPEN-004 implications

The bookmark mechanism cannot be trusted for OPEN-001/OPEN-004 evidence until §7.1 lands. After the fix:
- Re-run BM-001 with corrected target (arcade_pc `0x055748` for trace pc=055948, OR arcade_pc `0x055948` for trace pc=055B48 if BM-001's original intent was actually arcade source 0x055948)
- Then BM-002 can be re-issued as a positive control at the corrected target (arcade source `0x039F9C` for trace pc=03a19c delay-loop code)
- Once positive-control confirms the mechanism, real evidence cycles for OPEN-001 (strip producers) and OPEN-004 (bootstrap re-entry sources) can proceed

### §7.4 New positive-control target recommendation

For the next positive control (call it BM-003 or whatever next BM-NNN), recommended target = arcade source `0x039F9C` (= delay-loop code at runtime PC `0x03A19C`). Properties:
- Provably executed in the BM-002 trace (7 hits in 30 seconds)
- In the early bootstrap region (executes before any OPEN-004 re-entry stabilization)
- The span at arcade source `0x039F9C` is the `bnes 0x3a192` instruction — only 2 bytes. Would need to be widened to an 8-byte span; Cody must verify the wider span has no internal branch targets and no PC-relative dependencies.

This makes the next positive control test BOTH the corrected translation workflow AND the mechanism's behavior in a known-executed location.

### §7.5 Validation of any fix

Before declaring the workflow fix complete:
1. Apply the §7.1 translation step to BM-002's original observation. Compute `arcade_pc = 0x03A19C - 0x200 = 0x039F9C`. Verify against `address_map.json` that this falls in `arcade_copy` with identity_offset 0x200.
2. Document the fix in `docs/design/Andy_diagnostic_bookmark_postpatch_invariant_design.md` (cross-reference) or a new design doc covering target-selection workflow.
3. Re-run BM-002 as the positive control (target arcade source `0x039F9C`).
4. Expected outcome: helper park, `helper_hits` > 0, target_hit_count drops to 1 (single execution before park).

---

## §8 Phase 8 — New OPEN issue

**Recommend opening OPEN-012.**

- Title: "Bookmark target-selection: arcade_pc vs trace runtime PC translation workflow fault"
- Status: OPEN
- Priority: HIGH
- Discovered by: Andy (BM-002 runtime failure investigation)
- Observed in build/artifact: BM-002 cycle (Build 0069 diagnostic, Build 0070 canonical revert). BM-001 (Build 0067) has same fault retroactively.
- Summary: The bookmark target-selection workflow equates trace's observed `pc=X` (runtime Genesis PC) with the spec's `arcade_pc` field (arcade-source space). These differ by `identity_offset` (typically 0x200 for `arcade_copy` segments per `address_map.json`). The activator gets placed at the wrong ROM offset; the CPU never executes it; the helper is never reached. BM-001 and BM-002 both hit this fault.
- Evidence: `docs/design/Andy_BM002_runtime_failure_investigation.md`
- Suspected area: bookmark target-selection workflow (documentation + procedure); no implementation change to postpatcher or gate required for the primary fix; optional supplementary gate check possible
- Next required task: per §7.1 of investigation report. Andy or Tighe revises the target-selection workflow with explicit `arcade_pc = trace_pc - identity_offset(trace_pc)` translation step using `address_map.json`. Cody re-runs BM-002 with corrected target (arcade source `0x039F9C`) as fresh positive control.
- Closure condition: workflow fix documented; re-run positive-control bookmark produces helper park (Outcome A); BM-001 re-run scoped for OPEN-001/OPEN-004 evidence.
- Cross-references: OPEN-001, OPEN-004 (blocked pending fix), Rule 10 + helper design + postpatch invariant design (all sound; only the target-selection workflow has the fault), CLOSED-008 (gate design — §7.1 optional supplementary check would extend), CLOSED-009 (postpatch invariant design — unaffected; mechanism is sound).

This is the cleanest tracked-remediation path. The fix is documentation/procedure-level; new infrastructure (postpatcher, gate) is not required for the primary fix.

---

## §9 Surfaced ambiguities

### Ambiguity 1 — Is the trace's pc value documented as runtime PC anywhere?

I am confident `pc=03a19c` is the 68000's literal PC value (runtime/Genesis space) based on standard MAME conventions and the cross-check with disassembly. However, I don't have an explicit project document stating "MAME trace `pc=X` is runtime/Genesis PC, NOT arcade_pc." If such documentation exists somewhere and was Cody's reference, this investigation's conclusion still holds — Cody made the wrong equation regardless. If no such documentation exists, that's another remediation item for OPEN-012's documentation portion.

**Chosen interpretation:** MAME trace `pc=X` is the 68000's literal PC value. The evidence in this investigation (postpatch disasm at runtime PC `0x03A19C` showing the bnes/jmp soft-reset code, file offset `0x03A19C` matching those bytes byte-for-byte, file offset `0x03A39C` containing the activator, trace showing zero hits at `pc=03a39c`) makes this unambiguous.

### Ambiguity 2 — Was Cody aware of the +0x200 relocation?

Cody used `arcade_pc 0x03A19C` in the spec, which correctly mapped to file offset `0x03A39C` (= arcade_pc + identity_offset). So Cody knew about the relocation for the WRITE side. But Cody also used the trace's `pc=03a19c` as the basis for choosing `arcade_pc 0x03A19C`, equating the values across spaces. So Cody knew identity_offset existed but applied it inconsistently. This is documentation/procedural, not a knowledge gap.

**Chosen interpretation:** the workflow documentation didn't make the asymmetry explicit. Fix is to document explicitly: "If you observe trace `pc=X`, the arcade_pc to put in the spec is `X - identity_offset(X)`. The address_map.json segment containing X tells you identity_offset."

### Ambiguity 3 — Did Build 0069's diagnostic context contribute to the crash?

Tighe observed a crash at `0x00000116` not seen in canonical Build 0062/0070. Build 0069's helper region differs slightly from canonical (extra helper bytes since Build 0060), and the postpatcher invariant grew by +1 site / +8 bytes. The crash itself might be Build 0069-specific OR might be a general bootstrap-re-entry pathology that just happens to manifest as a crash on this particular ROM state.

**Chosen interpretation:** the crash is a downstream consequence of OPEN-004 bootstrap re-entry, not caused by the activator (because the activator was never executed). Whether the specific crash signature (Vector C8, Fault PC `0x00000116`) is new to Build 0069 vs. canonical is out of scope — Tighe's evidence shows the crash on Build 0069; whether canonical Build 0062 also crashes given long enough is unknown without separate observation.

### Ambiguity 4 — Should §2.7 gate check be extended?

§2.7 verified activator bytes are at the spec's claimed offset. It did NOT verify "the offset is where the CPU actually executes from when the trace's pc matches the cycle's intent." Adding such a check requires the gate to read trace artifacts, which couples gate behavior to trace availability/format — a scope expansion.

**Chosen interpretation:** OPEN-012's optional supplementary check is documented but not required for primary fix. The workflow change (translate trace_pc → arcade_pc before populating spec) is sufficient. Cody/Tighe can decide separately whether to add the gate check.

---

## §10 Phase 10 — Integrity

- Phase 1 address translation resolved from address_map.json: YES (segment `genesis_start 0x03A2C8 .. genesis_end_exclusive 0x03A3D8`, identity_offset 512)
- Phase 2 Build 0069 activator bytes verified by direct ROM inspection: YES (file offset `0x03A39C` contains `4ef9 0007 1c78 4e71`; file offset `0x03A19C` contains original `66f4 2e78 0000 2078 0004 4ed0`)
- Phase 2 CPU-executed-offset vs patched-offset comparison: YES — different offsets; CPU at `pc=03a19c` fetches from file offset `0x03A19C` (original bytes), activator at `0x03A39C` never reached (zero `pc=03a3*` hits in trace)
- Phase 3 control flow to crash reconstructed: YES — delay loop → soft-reset to `0x00000202` → OPEN-004 bootstrap re-entry → eventual crash at `0x00000116`
- Phase 4 span safety assessed (PC-relative analysis): YES — `41FA 000E D0C0 3010` is coupled PC-relative; would be safe if JMP fires (helper parks), is irrelevant in BM-002 case (JMP never executed)
- Phase 5 root cause classified with cited evidence: YES — primary (A) address-space/translation mismatch; (B) contributory preventive concern only; (C) and (D) ruled out
- Phase 6 BM-001 reassessed: YES — same fault, BM-001 Outcome B not trustworthy for arcade source 0x055948 reachability question; re-run required
- Phase 7 recommendations provided: YES (primary workflow fix + secondary PC-relative screening + BM-001/BM-002 re-run plan + new positive-control target candidate)
- Phase 8 new OPEN issue decision documented: YES — OPEN-012 recommended
- No source/spec/tool/build/ROM modifications: YES
- No evidence-file modifications: YES
- No fixes implemented: YES
- Ambiguities surfaced: 4 (§9)
- All STOP conditions either passed or documented: YES (no STOP triggered)
