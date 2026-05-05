# Andy — Build 53 `rastan_direct_update_inputs` Root Cause Classification

**Agent:** Andy (Claude Code)
**Type:** Root cause classification (analytical synthesis only — no implementation, no new evidence collection)
**Build:** rastan-direct Build 0053 (post-v3.2 dispatch)
**Date:** 2026-04-29
**Architecture compliance:** CONFIRMED for `rastan_direct_update_inputs`. The function complies with `RULES.md` and `ARCHITECTURE.md`. The architectural concern raised by the function's name does not survive source inspection.

---

## 0. Executive verdict

**Read 4 (control-flow escape into legitimate function) with mandatory Read 2 caveat (symbol-coverage illusion).**

The function `rastan_direct_update_inputs` is a fully-compliant, passive RTS-returning helper that polls Genesis controller hardware and stores results into shadow bytes for arcade-side reads. Its source body is 78 lines of input polling ([tilemap_hooks.s:1598-1675](apps/rastan-direct/src/tilemap_hooks.s#L1598-L1675)), it ends with `rts`, and the runtime disassembly at `0x000710CA..0x000711B2` matches it exactly. **It is not the failing function.**

PC `0x000711CE` is NOT inside the actual body of `rastan_direct_update_inputs`. The body ends at `0x000711B2` (rts). The bytes from `0x000711B4..0x0007133E` are `.L`-local helper subroutines from `pc090oj_hooks.s` (specifically `.Lpc090oj_set_dirty`-style at `0x000711B4` and `.Lpc090oj_emit_slot`-style at `0x000711CC`), which are **invisible to the global symbol table** (`apps/rastan-direct/out/symbol.txt`). Because the next global symbol after `rastan_direct_update_inputs` is `genesistan_pc090oj_hook_target_3b902` at `0x00071340`, an `nm`-style symbol-coverage check attributes any address in `[0x000710CA, 0x00071340)` to `rastan_direct_update_inputs`. This is a **reporting illusion**, not a real boundary.

PC `0x000711CE` is the second instruction of `.Lpc090oj_emit_slot` (`muluw #12, %d6`). Frame 108's register state shows D0 = D6 = 0x00000AA4 (= 2724) — **invalid slot index** for a helper whose contract expects D0 ∈ [0, 80). Some upstream caller set D0 to 0xAA4 and BSR'd to `.Lpc090oj_emit_slot` with that bad value, OR control reached `0x000711CC` via a chained-RTS path that bypassed normal call-site setup. The wild PC `0x008F831C` (popped by the RTS at frame 108→109) is a corrupted return address that was already on the stack at A7 = `0x00FEFFB0` before the failing call sequence.

Both helpers (`rastan_direct_update_inputs` and `.Lpc090oj_emit_slot`) are architecturally compliant. **The fix is upstream — identify which caller set D0 = 0xAA4 and/or what corrupted the stack frame at `0x00FEFFB0`.** No spec change. No `rastan_direct_update_inputs` change. No `.Lpc090oj_emit_slot` change. The fix lives in whichever PC090OJ hook helper provided the wrong slot index.

---

## §1.1 Source identification

`rastan_direct_update_inputs` is defined in [apps/rastan-direct/src/tilemap_hooks.s:1598-1675](apps/rastan-direct/src/tilemap_hooks.s#L1598-L1675). Declaration line: [tilemap_hooks.s:17](apps/rastan-direct/src/tilemap_hooks.s#L17) (`.global rastan_direct_update_inputs`). No docstring/header comment.

Function body summary (full source span, 78 lines, ends with `rts` at line 1675):

```asm
rastan_direct_update_inputs:
    move.b  #0x40, IO_PAD1_CTRL          ; configure pad 1 ctrl pin direction
    move.b  #0x40, IO_PAD2_CTRL          ; configure pad 2 ctrl pin direction
    move.b  #0x00, IO_PAD1_DATA          ; select pad 1 high half
    nop
    move.b  IO_PAD1_DATA, %d1            ; read pad 1 high
    move.b  %d1, %d6
    move.b  #0x40, IO_PAD1_DATA          ; select pad 1 low half
    nop
    move.b  IO_PAD1_DATA, %d0            ; read pad 1 low
    ; ... bit translation to arcade input encoding ...
    move.b  %d2, genesistan_shadow_input_390001    ; arcade-side P1 shadow
    ; ... same pattern for pad 2 ...
    move.b  %d3, genesistan_shadow_input_390003    ; arcade-side P2 shadow
    ; ... coin-bit derivation ...
    move.b  %d4, genesistan_shadow_input_390005    ; arcade-side coin shadow
    ; ... start/system-bit derivation with coin-edge tracking ...
    move.b  %d5, genesistan_shadow_input_390007    ; arcade-side system shadow
    rts
```

Where `IO_PAD1_CTRL = 0x00A10009`, `IO_PAD2_CTRL = 0x00A1000B`, `IO_PAD1_DATA = 0x00A10003`, `IO_PAD2_DATA = 0x00A10005` — the standard Genesis controller register addresses (per [tilemap_hooks.s:26-29](apps/rastan-direct/src/tilemap_hooks.s#L26-L29)).

Function purpose per source: poll Genesis controllers via the `0xA1000x` I/O ports, translate the read bits into the arcade's expected `IN0`/`IN1`/`IN2`/`IN3` encoding, and store results into four `genesistan_shadow_input_390xxx` bytes that arcade code reads via opcode-replaced shadow lookups (see `specs/rastan_direct_remap.json` entries that reference `genesistan_shadow_input_390001/3/5/7`).

The function is NOT auto-generated. It is hand-written assembly in `tilemap_hooks.s`.

---

## §1.2 Source-vs-disassembly comparison

Runtime disassembly at `0x000710CA..0x000711B2` ([genesis_postpatch.disasm.txt:123970-124034](build/genesis_postpatch.disasm.txt#L123970-L124034)):

```text
710ca: 13fc 0040 00a1 0009    moveb #64, 0xa10009          ; IO_PAD1_CTRL
710d2: 13fc 0040 00a1 000b    moveb #64, 0xa1000b          ; IO_PAD2_CTRL
710da: 13fc 0000 00a1 0003    moveb #0, 0xa10003           ; IO_PAD1_DATA = 0
710e2: 4e71                   nop
710e4: 1239 00a1 0003         moveb 0xa10003, %d1
710ea: 1c01                   moveb %d1, %d6
710ec: 13fc 0040 00a1 0003    moveb #64, 0xa10003          ; IO_PAD1_DATA = 0x40
710f2: 4e71                   nop
710f6: 1039 00a1 0003         moveb 0xa10003, %d0
710fc: 1400                   moveb %d0, %d2
710fe: 0002 00c0              orib #-64, %d2
71102: 0801 0004              btst #4, %d1
71106: 6604                   bnes 0x7110c
71108: 0882 0006              bclr #6, %d2
7110c: 13c2 00ff 60fc         moveb %d2, 0xff60fc          ; shadow_input_390001
71112: 13fc 0000 00a1 0005    moveb #0, 0xa10005           ; IO_PAD2_DATA = 0
   ... pattern continues for pad 2, coin derivation, system derivation ...
711ac: 13c5 00ff 60ff         moveb %d5, 0xff60ff          ; shadow_input_390007
711b2: 4e75                   rts                          ; ◄─ FUNCTION EXIT
```

**Source-disassembly match: YES, exactly.** The runtime body at `[0x000710CA, 0x000711B2]` is the assembled version of the source at [tilemap_hooks.s:1598-1675](apps/rastan-direct/src/tilemap_hooks.s#L1598-L1675). The destination addresses in the runtime disassembly (`0xff60fc`, `0xff60fd`, `0xff60fe`, `0xff60ff`) are the linker-resolved addresses for `genesistan_shadow_input_390001` / `390003` / `390005` / `390007` (declared in `.bss` at [tilemap_hooks.s:1681-1688](apps/rastan-direct/src/tilemap_hooks.s#L1681-L1688)).

**Actual symbol body size:** `0x000711B4 - 0x000710CA = 0xEA = 234 bytes`. The function ends at `0x000711B2` (the rts), so the inclusive byte range is `[0x000710CA, 0x000711B2]` = `0xE9` bytes; aligning to 2-byte boundary makes it 234 bytes total.

**Reported `nm`-style symbol coverage:** `0x00071340 - 0x000710CA = 0x276 = 630 bytes` (per [Cody_build53_rts_caller_chain.md §1.8](docs/design/Cody_build53_rts_caller_chain.md)). This is **not the actual function size** — it is the gap between this global and the next global (`genesistan_pc090oj_hook_target_3b902`).

The `0x18C = 396 bytes` of code between `0x000711B4` and `0x00071340` are NOT part of `rastan_direct_update_inputs`. Per the runtime disassembly:

- `0x000711B4..0x000711CA` (22 bytes): a small helper that reads `D0`, computes `1 << (D0/4)`, ORs into `0xff6744` (= `staged_sprite_dirty` per Andy v3.2 §1.1). Pattern matches `.Lpc090oj_set_dirty` semantics. RTS at `0x000711CA`.
- `0x000711CC..0x0007133E`: a larger helper starting `movew %d0, %d6 / muluw #12, %d6 / lea 0xff6384, %a0 / addal %d6, %a0 / ...` — sets `A0 = staged_sprite_descriptor_table + D0*12` and `A1 = staged_sprite_sat + D0*8`, then writes 5 words to `(A0+2..+10)` (semantic descriptor record per Andy v3.2 §1.2 layout: `+2..+3 arcade y_raw`, `+4..+5 arcade x_raw`, `+6..+7 arcade word0`, `+8..+9 arcade word2`, `+10..+11 source-id`). This is **`.Lpc090oj_emit_slot`** — the local helper defined in [pc090oj_hooks.s:67](apps/rastan-direct/src/pc090oj_hooks.s#L67) (`grep` evidence: 11 internal `bsr .Lpc090oj_emit_slot` references in pc090oj_hooks.s). Note that local labels prefixed `.L` are stripped from the global symbol table by GAS by design.

**Conclusion:** Source-vs-disassembly match for the actual function body is YES. The discrepancy in apparent function size is a property of how `nm` reports symbols (only globals, with implicit "size = next-global-start - this-symbol-start") and is not a real boundary. The code at `0x000711B4+` is `.L`-local helpers from `pc090oj_hooks.s` linked into the same `.text.wrapper` section.

---

## §1.3 Architecture compliance verdict

**`rastan_direct_update_inputs` is COMPLIANT** with `RULES.md` and `ARCHITECTURE.md`.

Citing `RULES.md`:

- §4 ("Helper Functions Only"): the function is "called by arcade code (JSR/JMP), performs a hardware translation or operation, returns immediately via RTS." No loops waiting for events, no blocking, no scheduling, no control-flow ownership. ✓
- §1 ("Arcade Code Owns Execution"): the function does not own a game loop. It is a leaf helper. ✓
- §2 ("No Separate Genesis Runtime"): the function does not own frame progression, does not schedule gameplay. ✓
- §3 ("VBlank Ownership"): the function is not invoked from VBlank by Genesis-side scheduling. Per §1.4 below, NO call sites reference the function in the postpatch ROM at all — the function is in fact orphaned (see Read 2 caveat in §1.7).
- §5 ("No Test Code"): the function would exist in a final production ROM. Polling Genesis controllers and translating to arcade input encoding is exactly the kind of helper RULES.md mandates for I/O hardware bridging. ✓
- §8 ("Arcade Intent → Genesis Execution"): arcade code expresses input-read intent via reads of `390001/3/5/7`; Genesis-side translates by polling the actual Genesis controllers. This is the canonical Rule 8 helper pattern. ✓

Citing `ARCHITECTURE.md`:

- "Genesis code performs hardware operations only" — function performs hardware reads from Genesis controller hardware. ✓
- "Helper Functions ... Be explicitly called from arcade code, perform a specific hardware task, return immediately (RTS)" — function ends with `rts` at line 1675. ✓
- The function does not introduce a Genesis-side lifecycle, does not re-enter boot/init during gameplay, does not maintain hidden state machines (the `prev_coin_p1_a_pressed` byte is per-call edge tracking for coin-press debouncing, identical to arcade input-edge handling).

**Read 3 (architecture violation) is RULED OUT by source inspection.** The function name "update_inputs" suggested a possible Genesis-side update routine, but the source shows it is a passive controller-polling helper with the standard arcade-shadow-byte output pattern. No structural fix is required for `rastan_direct_update_inputs`.

The actual code at PC `0x000711CE` (`.Lpc090oj_emit_slot`) is also COMPLIANT: it is a passive helper that reads inputs from registers, writes to staging buffers, and ends with rts. It complies with v3.2 §1.1 staging-write contract.

---

## §1.4 Caller chain for `rastan_direct_update_inputs`

`grep` over `build/genesis_postpatch.disasm.txt` for any reference to address `0x000710CA`:

```
123970:   710ca: 13fc 0040 00a1     moveb #64,0xa10009     ← function definition (1 result)
460608:  1710ca: ffff               .short 0xffff          ← unrelated address in different range
```

**Zero callers in postpatch ROM.** No `jsr 0x710ca`, no `bsr 0x710ca`, no `jmp 0x710ca`, no other branch lands at `0x000710CA`. The function is **declared `.global` and present in ROM, but is not referenced from any executed code path.**

The function is also NOT in `specs/rastan_direct_remap.json` — `grep -nE "rastan_direct_update_inputs" specs/rastan_direct_remap.json` returns zero matches, so no opcode_replace entry uses `{symbol:rastan_direct_update_inputs}`.

The function is also NOT referenced in any source `.s` file outside its own definition — `grep` returned only the declaration line at [tilemap_hooks.s:17](apps/rastan-direct/src/tilemap_hooks.s#L17) and the definition line at [tilemap_hooks.s:1598](apps/rastan-direct/src/tilemap_hooks.s#L1598).

**Expected return-address sequence at any RTS inside `rastan_direct_update_inputs`:** UNDEFINED. There is no caller, so the function should never be entered. If it were entered, the return-address state would depend on whatever pushed onto the stack — which is not from a normal call path.

This evidence is consistent with the symbol-coverage illusion in §1.2: PC `0x000711CE` is NOT actually inside `rastan_direct_update_inputs`'s body; it is inside a different (unnamed-in-symbol-table) helper that happens to be linked between the input-polling RTS at `0x000711B2` and the next global symbol at `0x00071340`.

---

## §1.5 RTS analysis inside the symbol's `nm`-coverage range

Under the `nm`-style coverage (`[0x000710CA, 0x00071340)` = 630 bytes), the RTS instructions within this range are (per `grep "4e75" build/genesis_postpatch.disasm.txt` filtered to this range, plus the disassembly read in §1.2):

| RTS arcade_pc | Belongs to (per source mapping) | Role |
|---------------|-----------------------------------|------|
| `0x000710C8` | (immediately BEFORE `rastan_direct_update_inputs`) | rts of preceding function (`genesistan_hook_cwindow_clear`); NOT in coverage range |
| `0x000711B2` | `rastan_direct_update_inputs` (line 1675 source) | function exit; ONLY rts that belongs to `rastan_direct_update_inputs` |
| `0x000711CA` | `.Lpc090oj_set_dirty`-style helper at `0x000711B4` (`pc090oj_hooks.s` `.L`-local) | exit of the dirty-bit setter |
| (others at `0x000712xx..0x0007133x`) | `.Lpc090oj_emit_slot` helper at `0x000711CC` (`pc090oj_hooks.s` `.L`-local) | exit(s) of the emit-slot helper |

Cody §1.8 of `Cody_build53_wildpc_evidence.md` reported only 2 RTS in the ±128-byte window around `0x000711CE`: at `0x000711B2` and `0x000711CA`, both BEFORE `0x000711CE`. This is correct for the ±128-byte window. Beyond +128 bytes there are additional RTS instructions inside `.Lpc090oj_emit_slot`'s body (the helper has multiple early-exit paths and one final exit), but I do not need to enumerate them precisely — the load-bearing observation is that:

- The RTS at `0x000711B2` is the exit of the **input-polling helper** (`rastan_direct_update_inputs`).
- The RTS at `0x000711CA` is the exit of the **dirty-bit setter** (`.Lpc090oj_set_dirty`-style; not part of `rastan_direct_update_inputs`).
- All RTSes ≥ `0x000711CC` belong to `.Lpc090oj_emit_slot`-style helper(s); NOT part of `rastan_direct_update_inputs`.

**Most consistent RTS for the frame 108 → 109 transition:** an RTS within `.Lpc090oj_emit_slot` (somewhere ≥ `0x000711CE` after frame 108's PC) — the helper finishes its body, hits its terminating RTS, and pops `0x008F831C` from the stack.

(Frame 108 captures PC = `0x000711CE` at the start of the helper's body; frame 109 captures PC = `0x008F831C` at the top of stack. Between frame 108 and frame 109, multiple instructions of `.Lpc090oj_emit_slot` execute — the helper's body is significantly longer than one frame's instruction count — and eventually one of the helper's RTS instructions fires, popping the corrupted stack value. The exact RTS within `.Lpc090oj_emit_slot` cannot be pinned down without an instruction-by-instruction trace between frames 108 and 109; that level of detail is not necessary for root-cause classification.)

---

## §1.6 RTS-to-`0x008F831C` transition explanation

**Frame 108 → 109 stack delta:** A7 changed from `0x00FEFFB0` to `0x00FEFFB4` (+4 bytes). Exactly one 32-bit RTS occurred. The popped longword equals frame 109's PC = `0x008F831C`.

**What was at `*(0x00FEFFB0)`?** The longword `0x008F831C`. This is what frame 108's RTS popped.

**Was this a legitimate return address?** NO. Per §1.4, no caller of `rastan_direct_update_inputs` exists in the ROM. Per the actual containing helper (`.Lpc090oj_emit_slot`, which is called from PC090OJ hook helpers), the legitimate return addresses would be the post-BSR PCs of its callers — observed call sites at `0x000712CC`, `0x000712FE`, `0x0007132E`, `0x00071370`, `0x000713C8`, `0x000714F6` (`grep "bsrw 0x711cc" genesis_postpatch.disasm.txt` evidence). Their post-BSR return PCs would be `0x000712D0`, `0x00071302`, `0x00071332`, `0x00071374`, `0x000713CC`, `0x000714FA` — none of which equal `0x008F831C`.

**Where did `0x008F831C` come from?** Cody §1.6 (`Cody_build53_wildpc_evidence.md`) confirms `0x008F831C` does not appear anywhere in the ROM artifacts (zero matches in `address_map.json`, `manifest.json`, both disassemblies, `symbol.txt`, spec, source). It is also classified by §1.7 as "Other unmapped space" — outside ROM (`[0x000000, 0x3FFFFF]`), outside WRAM (`[0xFF0000, 0xFFFFFF]`), outside VDP I/O, outside Z80. This is consistent with the value being **stack garbage written there by some prior code path**, not a real return address.

**Hypothesis for the corruption** (consistent with available evidence; CONFIRMING this is downstream Cody work, see §1.8 fix plan):

Frame 108's register state shows D0 = 0x00000AA4 = 2724 (`Cody_exodus_frame_extraction_build_53_2.md:218`). At PC `0x000711CC`, `.Lpc090oj_emit_slot` reads `D0` and uses it as the slot index (`movew %d0, %d6; muluw #12, %d6`). Valid slot index range is `[0, 80)` per Andy v3.2 §1.1 staging-buffer dimensioning. **D0 = 0xAA4 is far outside the valid range.** With D0 = 0xAA4, the helper would compute:

- `A0 = 0xFF6384 + 0xAA4 * 12 = 0xFF6384 + 0x7FB0 = 0xFFE334` (high WRAM, near stack)
- `A1 = 0xFF6104 + 0xAA4 * 8 = 0xFF6104 + 0x5520 = 0xFFB624` (also high WRAM)

The helper then writes 5 words to `A0+2..+10` (= `0xFFE336..0xFFE33E`), then continues executing the rest of its body, including subsequent writes to `A0`, `A1`, and possibly to addresses computed from these bases.

Live A7 = `0x00FEFFB0`. Stack frames live at `<A7`. The helper's writes to `A0` (`0xFFE334+`) and `A1` (`0xFFB624+`) are in WRAM but not in the immediate stack region. However, the bytes at `*(0x00FEFFB0)` were already corrupt at frame 108 — i.e., before the failing RTS — meaning the corruption was placed there BEFORE this helper was entered.

The cause is therefore upstream: either (a) some earlier code wrote `0x008F831C` into `*(0x00FEFFB0)` as part of a stack overflow or wild write, or (b) the call chain reached `0x000711CC` via an RTS that already had `0x008F831C` on top of stack from a corrupted prior frame, or (c) `D0` was set to `0xAA4` by some code that legitimately calls `.Lpc090oj_emit_slot` but with a wrong slot input — and the bad slot's `A0/A1` computation, plus other writes within the helper's body, have a side effect on the stack region we have not yet traced.

**This level of resolution requires a Cody follow-up** that traces the stack contents at frames 100..107 (just before frame 108) and identifies the earliest frame where `*(0x00FEFFB0) == 0x008F831C` becomes true. Without that trace, the upstream defect cannot be definitively pinned to a single arcade_pc.

---

## §1.7 Read classification

**Primary: Read 4 — Control-flow escape into legitimate function.**

Execution reached PC `0x000711CE` (inside `.Lpc090oj_emit_slot`, a fully-compliant Genesis-side passive helper) via an upstream defect. The helper itself is correct; its caller provided invalid input (`D0 = 0xAA4`); a corrupted return address (`0x008F831C`) was already on the stack at A7 = `0x00FEFFB0` before the failing RTS fired. The fix is upstream of `.Lpc090oj_emit_slot`.

**Mandatory caveat: Read 2 — Symbol-coverage illusion (not a build error, but an attribution error).**

The original premise of this investigation — "PC `0x000711CE` is inside `rastan_direct_update_inputs`" — is true under `nm`-style global-symbol coverage but FALSE under actual function-body extent. `rastan_direct_update_inputs` ends at `0x000711B2` (rts at line 1675). The code at `0x000711CC..0x0007133E` is `.L`-local helpers from `pc090oj_hooks.s`. No source file or build pipeline change is required to fix this attribution; it's a property of the GAS toolchain stripping `.L`-local labels by design.

The Read 2 caveat is mandatory because the original reasoning (architectural concern about a function named "update_inputs") was based on the misleading attribution. Once the attribution is corrected, both involved helpers (`rastan_direct_update_inputs` for the input-polling body and `.Lpc090oj_emit_slot` for the actual PC `0x000711CE` body) are confirmed compliant.

**Reads 1, 3, 5 ruled out:**

- Read 1 (legitimate helper, upstream stack corruption): partially overlaps with Read 4 but is too narrow. The function is correct AND the stack is corrupted AND the input register state is invalid — Read 4 captures the full picture.
- Read 3 (architecture violation): RULED OUT — `rastan_direct_update_inputs` complies with all relevant RULES.md and ARCHITECTURE.md sections per §1.3.
- Read 5 (other category): not needed; Read 4+2 covers the evidence.

**Evidence supporting the classification:**

- Source body at [tilemap_hooks.s:1598-1675](apps/rastan-direct/src/tilemap_hooks.s#L1598-L1675) ends with `rts`; corresponding runtime disassembly at `[0x000710CA, 0x000711B2]` matches exactly per §1.2.
- Zero call sites for `0x000710CA` in the postpatch ROM per §1.4 (`grep "710ca" build/genesis_postpatch.disasm.txt` evidence).
- 11 internal references to `.Lpc090oj_emit_slot` inside `pc090oj_hooks.s` per `grep` evidence.
- Multiple BSR call sites (`0x000712CC, 0x000712FE, 0x0007132E, 0x00071370, 0x000713C8, 0x000714F6`) target `0x000711CC` per `grep "bsrw 0x711cc" build/genesis_postpatch.disasm.txt` evidence.
- Frame 108 D0 = `0x00000AA4` per `Cody_exodus_frame_extraction_build_53_2.md:218`; this is invalid as slot index for the emit-slot helper.
- `0x008F831C` is unmapped (Cody `wildpc_evidence` §1.7) and absent from all ROM artifacts (Cody §1.6).

---

## §1.8 Fix plan

### 1.8.1 Categorization (per Chad's framework)

- Remove the call to `rastan_direct_update_inputs`? **NO** — there is no call to remove (§1.4: zero callers). The function is a passive helper waiting to be wired up by a future opcode_replace; the spec already expects it to be invoked via shadow-byte reads triggered by arcade input-port reads, but no such opcode_replace currently invokes it directly. This is a separate orphaned-symbol observation, not the failing-execution root cause.
- Replace `rastan_direct_update_inputs` with a passive helper? **NO** — it is already a passive helper.
- Intercept the caller (opcode_replace upstream)? **NOT YET** — the upstream caller responsible for D0 = 0xAA4 has not been identified. Cody follow-up needed first.
- Delete/disable an old Genesis lifecycle path? **NO** — there is no Genesis lifecycle path here.
- **OTHER: identify the upstream PC090OJ-helper caller path that set D0 = 0xAA4 and corrupted `*(0x00FEFFB0)`, then fix THAT caller.** This is the actual fix — but it requires Cody binary-evidence work to identify before any code or spec change is possible.

### 1.8.2 Concrete steps for downstream Cody work

The fix plan **requires a Cody follow-up to identify the upstream caller** before any source change can be specified. Andy CANNOT identify that caller without binary evidence Andy was instructed not to collect (Rule 20). Specifically, the following Cody binary-evidence task is required as the next step:

**Cody follow-up task (specification for prompt-drafting):**

> Inputs:
> - Build 53 ROM at `dist/rastan-direct/rastan_direct_video_test_build_0053.bin`
> - Exodus extraction window: capture frames covering t=17.50s..17.60s (the 100ms before and including frame 108)
> - Exodus may need to be reset and re-run with frame trace from boot to t=17.6s
>
> Outputs:
> - For frames 100..108: full register snapshot (especially D0, D1..D7, A0..A7, PC, SR), top-of-stack longword at A7
> - The PC and instruction at the moment D0 first became 0xAA4
> - The PC and instruction at the moment `*(0x00FEFFB0)` first became 0x008F831C
> - The most recent BSR/JSR call path from a known PC090OJ helper entry (e.g., `genesistan_hook_3ad44_dispatch` at 0x71434, `genesistan_pc090oj_hook_target_3b902` at 0x71340, etc.) leading into 0x000711CC
>
> Deliverable: `docs/design/Cody_build53_emit_slot_caller_trace.md` documenting the upstream call chain and the exact instruction that set D0 = 0xAA4.

Once Cody produces this evidence, Andy can perform a follow-up classification task that designs the fix at the identified upstream site. The fix at that point will be one of:

- **Bounds check in the calling helper** — caller computes a slot index that overflows; add a clamp or skip path to ensure D0 ∈ [0, 80) before BSR'ing to `.Lpc090oj_emit_slot`.
- **Helper-internal bounds check** — alternatively, harden `.Lpc090oj_emit_slot` itself with an early-exit when D0 ≥ 80, so any caller bug fails safely. (NOTE: this is structurally identical to the `bhi.s .Lhook_3ad44_done` guard already present in `genesistan_pc090oj_hook_init_clear_3ad44`/`_3ad44_dispatch` per [pc090oj_hooks.s:355-356](apps/rastan-direct/src/pc090oj_hooks.s#L355-L356) — the pattern is established.)
- **Spec-level helper-contract clarification** — add a §2.1.X note to Andy v3.2 stating that all helpers calling `.Lpc090oj_emit_slot` MUST validate `D0 < 80` before BSR, and document the helper's bounds-check obligation in its source comments.

These are all bounded, non-architecture-violating fixes. None require a v3.3 spec revision until the upstream caller is identified — the choice between caller-side bounds and helper-side bounds depends on which helper's contract should bear the validation burden.

### 1.8.3 What this fix plan does NOT touch

- v3.1 closures (Resolution B for 0x54052, LUT MUST NOT consultation, jsr-not-bsr): UNTOUCHED.
- v3.2 dispatch contract (`genesistan_hook_3ad44_dispatch` polymorphic-utility A0 dispatch): UNTOUCHED.
- `opcode_replace` at arcade_pc 0x3AF04 (relocated from arcade 0x3AD44): UNTOUCHED.
- `_bootstrap` ending with `jmp (0x3A200).l`: UNTOUCHED.
- `_vblank_service` ending with `jmp (0x3A208).l`: UNTOUCHED.
- `rastan_direct_update_inputs` source body: UNTOUCHED (compliant; no fix needed there).
- 18-entry opcode_replace count (Andy v3.2 final = 90): UNTOUCHED.

### 1.8.4 Orphaned-symbol observation (separate concern; not part of this fix plan)

§1.4 evidence shows `rastan_direct_update_inputs` is a `.global` symbol with zero callers in the postpatch ROM. This is potentially a separate concern — the function is intended to be called when arcade code reads an input port (which would be opcode_replaced to read the shadow byte the function populates), but if no opcode_replace currently TRIGGERS the function's invocation, the shadow bytes are stale or zero-initialized at runtime. This may or may not be intentional (the shadow bytes might be populated by a different code path, or the function might be invoked via a future spec entry not yet implemented). **This observation is NOT the Build 53 crash root cause** (the crash involves `.Lpc090oj_emit_slot`, not `rastan_direct_update_inputs`). It is logged here as an audit-trail finding for the user to triage separately.

---

## §1.9 Architecture compliance verification of the fix

(Verified for both proposed fix variants — caller-side bounds check OR helper-side bounds check.)

| Invariant | Compliance | Reasoning |
|-----------|------------|-----------|
| No Genesis-side lifecycle introduced | YES | Both fix variants add a single conditional branch / cmp instruction inside an existing helper. No loop, no scheduler, no main loop. |
| Helpers RTS-return | YES | The bounds-check addition does not change the RTS-return contract. The helper still ends with rts on all paths (including the new "skip on out-of-range D0" path). |
| No memory shadowing | YES | Bounds checks read from registers, not from memory. |
| No scaffolding | YES | Bounds-check code is production-intent — protects against a real defect class (helper-contract violation). It would exist in a final shipping ROM. |
| v3.1 Resolution B preserved | YES | No changes to `genesistan_pc090oj_hook_slot_init_54052` or its text-RAM behavior. |
| v3.2 dispatch contract preserved | YES | `genesistan_hook_3ad44_dispatch` body unchanged; A0 ranges unchanged; tilemap branch unchanged. |
| `opcode_replace` at 0x3AF04 preserved | YES | Spec entry untouched. |
| `_bootstrap` closure preserved | YES | Boot sequence ([boot.s:160](apps/rastan-direct/src/boot/boot.s#L160) `jmp (0x00003A200).l`) untouched. |
| `_vblank_service` closure preserved | YES | VBlank service exit ([vdp_comm.s:179](apps/rastan-direct/src/vdp_comm.s#L179) `jmp (0x00003A208).l`) untouched. |
| Arcade owns execution | YES | Arcade still drives all calls into the fixed helper; the helper still returns control via RTS. |

All 10 invariants pass for either fix variant. The structural decision (caller-side vs helper-side bounds) is a tactical choice tied to which helper's contract gains the validation responsibility; both options preserve the architecture.

---

## Phase 2 integrity

| Check | Status |
|-------|--------|
| §1.1 source location identified | YES — `apps/rastan-direct/src/tilemap_hooks.s:1598-1675` |
| §1.2 source-vs-disassembly compared | YES; match: YES (function body matches; `nm`-coverage discrepancy explained as `.L`-local helpers in same `.text` section) |
| §1.3 architecture compliance verdict | COMPLIANT (cited RULES §1, §2, §3, §4, §5, §8 and ARCHITECTURE.md helper contract) |
| §1.4 caller chain for `rastan_direct_update_inputs` traced | YES — zero callers (`grep` evidence) |
| §1.5 RTS analysis inside symbol body | YES — only `0x000711B2` belongs to the actual function; `0x000711CA` and beyond belong to `.L`-local helpers |
| §1.6 RTS-to-`0x008F831C` transition explained | PARTIAL — corrupted top-of-stack identified; upstream cause requires Cody follow-up (Rule 20 prevents Andy collection) |
| §1.7 Read classified | Read 4 (primary) + Read 2 (caveat) |
| §1.8 fix plan produced | YES with explicit downstream Cody dependency for upstream caller identification |
| §1.9 architecture compliance of fix verified | YES (10/10 invariants pass) |
| All conclusions cited | YES (Rule 17): every conclusion references a source line, disassembly line, Cody evidence section, or RULES/ARCHITECTURE rule |
| No new evidence collection | YES (Rule 20): all evidence cited is from existing Cody packages, source files, symbol map, disassembly, address map, spec, RULES.md, ARCHITECTURE.md |
| No source/spec/tool modifications | YES |
| STOP conditions | NONE TRIGGERED — source was found; function is compliant; Read classification distinguishes definitively; fix plan has bounded downstream Cody dependency (not a STOP, an explicit follow-up specification). |

---

## Cross-reference

- `RULES.md` (Rules 1, 2, 3, 4, 5, 8) — architectural compliance check
- `ARCHITECTURE.md` — helper-function contract
- [apps/rastan-direct/src/tilemap_hooks.s:1598-1675](apps/rastan-direct/src/tilemap_hooks.s#L1598-L1675) — source of `rastan_direct_update_inputs`
- [apps/rastan-direct/src/pc090oj_hooks.s:67](apps/rastan-direct/src/pc090oj_hooks.s#L67) — `.Lpc090oj_emit_slot` definition
- [apps/rastan-direct/src/pc090oj_hooks.s:347-377](apps/rastan-direct/src/pc090oj_hooks.s#L347-L377) — `genesistan_pc090oj_hook_init_clear_3ad44` (renamed `_dispatch` per v3.2)
- [build/genesis_postpatch.disasm.txt:123970-124034](build/genesis_postpatch.disasm.txt#L123970-L124034) — runtime body of `rastan_direct_update_inputs`
- [build/genesis_postpatch.disasm.txt:124042+](build/genesis_postpatch.disasm.txt#L124042) — runtime body of `.Lpc090oj_set_dirty` and `.Lpc090oj_emit_slot`
- `docs/design/Cody_build53_rts_caller_chain.md` — primary input
- `docs/design/Cody_build53_wildpc_evidence.md` — secondary input
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md` — register trajectory
- `docs/design/Andy_pc090oj_implementation_spec.md` v3.2 — spec authority
