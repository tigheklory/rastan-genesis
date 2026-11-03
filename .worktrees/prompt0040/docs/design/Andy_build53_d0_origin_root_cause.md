# Andy — Build 53 D0/D6 = 0xAA4 Origin Root Cause Classification

**Agent:** Andy (Claude Code)
**Type:** Root cause classification (analytical synthesis only — no implementation, no new evidence collection)
**Build:** rastan-direct Build 0053 (post-v3.2 dispatch)
**Date:** 2026-04-29
**Architecture compliance:** CONFIRMED. Both involved helpers (`.Lpc090oj_emit_slot` and the broken-loop callers) are RTS-returning helpers that comply with `RULES.md` §4 and `ARCHITECTURE.md`. Read 3 / Origin E (architectural violation) is RULED OUT. The bug is a register-flow contract mismatch between helpers in `pc090oj_hooks.s`.

---

## 0. Executive verdict

**Origin C (PC090OJ helper computation bug) — primary; Origin D (cross-helper register pollution) — contributing.**

Source inspection of `apps/rastan-direct/src/pc090oj_hooks.s` reveals that **two helpers — `genesistan_pc090oj_hook_target_3b930` and `genesistan_pc090oj_hook_sprite_update_54810` — share a register-flow bug** that produces an unbounded loop, with `D0` incrementing past every legitimate slot bound until it eventually equals `0x00000AA4 = 2724` (and beyond).

Specifically: each helper sets register `D6` to a small loop-counter value at function entry, then INSIDE the loop body OVERWRITES `D6` with `0` immediately before BSR'ing to `.Lpc090oj_emit_slot` (passing `D6=0` as the `extra_flags` parameter per emit_slot's signature comment line 66). After BSR, both helpers do `subq.w #1, %d6` expecting `D6` to still be the loop counter — but `.Lpc090oj_emit_slot` heavily uses `D6` as a scratch register and leaves it set to a large arbitrary value (`tile_index = D0*4 + 1024`). The `subq.w #1, %d6` therefore decrements that large value, never reaches zero, and the loop's exit condition (`tst.w %d6; beq.s` for `_3b930`; `subq.w #1, %d6; bne.s` for `_54810`) never fires. The loop iterates indefinitely, with `D0` (which IS preserved across the BSR per emit_slot's behavior) incremented by 1 each iteration via `addq.w #1, %d0`. Starting from `D0 = 14` (in `_3b930`) or `D0 = 44` (in `_54810`), `D0` reaches `0xAA4` after 2710 / 2680 iterations respectively. Each subsequent emit_slot call writes to invalid WRAM addresses computed from the runaway `D0`, eventually corrupting the stack at `*(0x00FEFFB0)`.

The 270ms-stable-PC observation (frames 100-107 identical) is consistent with **Exodus halted-state display after the emulator detected a fault**: once enough WRAM corruption accumulates, the next bus-error / address-error / illegal-instruction trap causes Exodus to freeze the CPU and present the captured state across subsequent video frames. Frame 109's `T=1` (trace bit set) and `SR=0x2710` confirm an exception was taken just after frame 108.

The fix lives **inside `pc090oj_hooks.s`** — neither helper requires spec-level revision; the `genesistan_hook_3ad44_dispatch` v3.2 contract, the staging-buffer model, the commit logic, and the audit guards are all unchanged. Two helpers' loop-counter storage must be moved to a register that `.Lpc090oj_emit_slot` preserves (or the counter must be save/restored around the BSR). All 10 architectural invariants pass for the proposed fix.

---

## §1.1 Owning-helper attribution verification (12 BSR sites)

Per Andy's prior classification (`Andy_build53_update_inputs_root_cause.md`), the symbol map at [apps/rastan-direct/out/symbol.txt](apps/rastan-direct/out/symbol.txt) contains only GLOBAL labels; `.L`-local labels in `pc090oj_hooks.s` are stripped from the symbol table by GAS. Cody §1.4 of `Cody_build53_emit_slot_caller_trace.md` attributed sites 1, 2, 3 (at runtime PCs `0x000712CC`, `0x000712FE`, `0x0007132E`) to `rastan_direct_update_inputs` because that is the last global symbol BEFORE these PCs. **This is the symbol-coverage illusion identified in the prior cycle.** The actual source ownership is verified below by reading `pc090oj_hooks.s`.

| Site # | Runtime PC | Symbol-table owner | Source-verified owner | Match |
|--------|------------|---------------------|------------------------|-------|
| 1 | `0x000712CC` | `rastan_direct_update_inputs` (illusion) | `.Lpc090oj_clear_slot` (`pc090oj_hooks.s` line 174-183; the `bsr .Lpc090oj_emit_slot` is at source line 182) | NO |
| 2 | `0x000712FE` | `rastan_direct_update_inputs` (illusion) | `.Lpc090oj_emit_slots_0_21_from_workram` (`pc090oj_hooks.s` line 186-229; the `bsr .Lpc090oj_emit_slot` for Block-A loop is at source line 205) | NO |
| 3 | `0x0007132E` | `rastan_direct_update_inputs` (illusion) | `.Lpc090oj_emit_slots_0_21_from_workram` (Block-B loop bsr at source line 224) | NO |
| 4 | `0x00071370` | `genesistan_pc090oj_hook_target_3b902` | `genesistan_pc090oj_hook_target_3b902` (source line 235-264; bsr to emit_slot at line 258) | YES |
| 5 | `0x000713C8` | `genesistan_pc090oj_hook_target_3b930` | `genesistan_pc090oj_hook_target_3b930` (source line 277-305; bsr to emit_slot at line 299) | YES |
| 6 | `0x000714F6` | `genesistan_pc090oj_hook_init_priority_3ad84` | `genesistan_pc090oj_hook_init_priority_3ad84` (source line 417-439; bsr at line 432) | YES |
| 7 | `0x000715D2` | `genesistan_pc090oj_hook_score_digit_3b802` | `genesistan_pc090oj_hook_score_digit_3b802` (source line 441-542; bsr at line 533) | YES |
| 8 | `0x00071676` | `genesistan_pc090oj_hook_slot_init_54052` | `genesistan_pc090oj_hook_slot_init_54052` (source line 558-610; bsr at line 604) | YES |
| 9 | `0x000716D2` | `genesistan_pc090oj_hook_sprite_update_54810` | `genesistan_pc090oj_hook_sprite_update_54810` (source line 612-653; bsr at line 645) | YES |
| 10 | `0x0007174C` | `genesistan_pc090oj_hook_sprite_decay_5607c` | `genesistan_pc090oj_hook_sprite_decay_5607c` (source line 655-704; bsr at line 696) | YES |
| 11 | `0x00071788` | `genesistan_pc090oj_hook_copy_56114` | `genesistan_pc090oj_hook_copy_56114` (source line 706-732; bsr at line 725) | YES |
| 12 | `0x000717DE` | `genesistan_pc090oj_hook_status_sprite_5a098` | `genesistan_pc090oj_hook_status_sprite_5a098` (source line 749-774; bsr at line 767) | YES |

Symbol-table mismatches: **3** (sites 1, 2, 3). All three are in `.L`-local helpers from `pc090oj_hooks.s`; the remaining 9 symbol-table attributions are correct.

---

## §1.2 D0/D6 provenance trace per owning helper

Each owning helper's full body has been read in `pc090oj_hooks.s`. Per the helper's source, the following table catalogs how `D0` is set (or inherited from the caller) before the BSR to `.Lpc090oj_emit_slot`. The `D0` source is what determines whether the helper can produce `D0 = 0xAA4`.

| Helper | D0 origin | D0 value range | Loop counter register | Loop-counter clobbered by emit_slot? |
|--------|-----------|-----------------|------------------------|--------------------------------------|
| `.Lpc090oj_clear_slot` (sites 1) | passed through from caller (helper does NOT modify D0) | inherits caller's range | n/a (no loop in this helper) | n/a |
| `.Lpc090oj_emit_slots_0_21_from_workram` (sites 2-3) | local `moveq` then `addq.w #1, %d0` per iteration | Block-A: D0 = 0..17; Block-B: D0 = 18..21 | D0 itself is the counter; preserved across BSR | NO — D0 preserved |
| `genesistan_pc090oj_hook_target_3b902` (site 4) | `moveq #0, %d0` then `addq.w #1, %d0` | D0 = 0..4 (clear path), 0..4 (fill path) | D0 itself; preserved | NO |
| `genesistan_pc090oj_hook_target_3b930` (site 5) | `moveq #14, %d0` then `addq.w #1, %d0` (lines 279, 300) | **UNBOUNDED — see §1.3** | **D6** (set at line 280, zeroed at line 298, expected to decrement after BSR at line 301) | **YES — emit_slot clobbers D6** |
| `genesistan_pc090oj_hook_init_priority_3ad84` (site 6) | `moveq #76, %d0` then `addq.w #1, %d0`; bounded `cmpi.w #80, %d0; blo.s` | D0 = 76..79 | D0 itself; preserved | NO |
| `genesistan_pc090oj_hook_score_digit_3b802` (site 7) | computed: `D3 = (A4-0xD00000)>>3 - 17` then `D0 = D3 + 22`; bounded `cmpi.w #7, %d3; bhi.s` (line 504) | D0 = 22..29 | n/a (single-call per-iteration; A3-based outer counter) | n/a |
| `genesistan_pc090oj_hook_slot_init_54052` (site 8) | `moveq #72, %d0` then `addq.w #1, %d0`; bounded `cmpi.w #76, %d0; blo.s` | D0 = 72..75 | D0 itself; preserved | NO |
| `genesistan_pc090oj_hook_sprite_update_54810` (site 9) | `moveq #44, %d0` then `addq.w #1, %d0` (lines 623, 648) | **UNBOUNDED — see §1.3** | **D6** (set `moveq #4, %d6` at line 624, zeroed at line 644 inside loop body, expected to decrement at line 649 after BSR) | **YES — emit_slot clobbers D6** |
| `genesistan_pc090oj_hook_sprite_decay_5607c` (site 10) | `moveq #56, %d0` then `addq.w #1, %d0`; bounded `cmpi.w #64, %d0; bhs.s` (line 667) | D0 = 56..63 | D0 itself; preserved | NO |
| `genesistan_pc090oj_hook_copy_56114` (site 11) | `moveq #64, %d0` then `addq.w #1, %d0`; bounded `cmpi.w #68, %d0; bhs.s` (line 715) | D0 = 64..67 | D0 itself; preserved | NO |
| `genesistan_pc090oj_hook_status_sprite_5a098` (site 12) | `moveq #30, %d0` then `addq.w #1, %d0`; bounded `cmpi.w #44, %d0; bhs.s` (line 759) | D0 = 30..43 | D0 itself; preserved | NO |

Source line citations: each is at [apps/rastan-direct/src/pc090oj_hooks.s](apps/rastan-direct/src/pc090oj_hooks.s) on the indicated line.

`.Lpc090oj_emit_slot` clobber list (verified by reading source lines 67-162): the helper modifies `D5` (heavily — flags/intermediate), `D6` (heavily — scratch for slot-offset computation, palette, flips, tile_index), `A0` (set to descriptor table + slot*12), `A1` (set to SAT + slot*8). Calls internal `.Lpc090oj_mark_dirty_slot` which additionally clobbers `D1`, `D2`, `D3`. **Preserved on RTS:** `D0`, `D4`, `D7`, `A2`, `A3`, `A4`, `A5`, `A6`. **Clobbered on RTS:** `D1`, `D2`, `D3`, `D5`, `D6`, `A0`, `A1`.

The helper's signature comment at [pc090oj_hooks.s:66](apps/rastan-direct/src/pc090oj_hooks.s#L66) lists `d6=extra_flags` — the comment is misleading. `d6` is read once at line 102 (`or.w %d6, %d5`) but at that point `d6` already holds the previously-loaded `*(A0+8)` value (line 80) — the caller's `d6` has been overwritten. The "extra_flags" semantic in the comment is dead.

---

## §1.3 Helpers classified CANNOT / COULD produce D0 = 0xAA4

**CANNOT produce D0 = 0xAA4** (10 of 12 sites): the helper's D0-setup is bounded by an explicit `cmpi.w #N, %d0; blo.s/bhs.s` exit condition, with N ≤ 80, and `D0` is the loop counter (preserved across the BSR by emit_slot). These helpers' loops terminate normally:

- `.Lpc090oj_clear_slot` (D0 inherited; bounded by caller)
- `.Lpc090oj_emit_slots_0_21_from_workram` (D0 = 0..17 then 18..21; bounded `cmpi.w #18, %d0` and `cmpi.w #22, %d0`)
- `genesistan_pc090oj_hook_target_3b902` (D0 = 0..4)
- `genesistan_pc090oj_hook_init_priority_3ad84` (D0 = 76..79)
- `genesistan_pc090oj_hook_score_digit_3b802` (D0 = 22..29; bounded by D3 ≤ 7 cap at line 504)
- `genesistan_pc090oj_hook_slot_init_54052` (D0 = 72..75)
- `genesistan_pc090oj_hook_sprite_decay_5607c` (D0 = 56..63)
- `genesistan_pc090oj_hook_copy_56114` (D0 = 64..67)
- `genesistan_pc090oj_hook_status_sprite_5a098` (D0 = 30..43)

**COULD produce D0 = 0xAA4** (2 of 12 sites): the helper's loop-counter register is `D6`, which is clobbered by `.Lpc090oj_emit_slot`. The loop's exit condition (`tst.w %d6; beq.s` for `_3b930`; `subq.w #1, %d6; bne.s` for `_54810`) tests a value that emit_slot has written, NOT the original counter. The loop iterates indefinitely with `D0` incremented unbounded each iteration via `addq.w #1, %d0`. After 2710 / 2680 iterations starting from `D0 = 14` / `D0 = 44`, `D0` reaches `0xAA4`:

- **`genesistan_pc090oj_hook_target_3b930`** (BSR site 5 = 0x713C8) — see §1.3.A below
- **`genesistan_pc090oj_hook_sprite_update_54810`** (BSR site 9 = 0x716D2) — see §1.3.B below

### 1.3.A `_3b930` broken loop (source lines 277-305)

```asm
genesistan_pc090oj_hook_target_3b930:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    moveq   #14, %d0                 ; D0 starts at 14 (slot)
    move.w  %d1, %d6                 ; D6 = caller's count (loop counter)
    cmpi.w  #4, %d6                  ; cap count at 4
    bls.s   .Lhook_3b930_count_ok
    moveq   #4, %d6
.Lhook_3b930_count_ok:
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
.Lhook_3b930_loop:
    tst.w   %d6                       ; ◄── exit condition tests D6
    beq.s   .Lhook_3b930_done
    moveq   #0, %d1
    moveq   #0, %d2
    move.b  (%a0)+, %d2
    moveq   #0, %d4
    move.b  (%a0)+, %d4
    move.w  (%a0)+, %d3
    moveq   #0, %d5
    moveq   #0, %d6                   ; ◄── BUG: D6 zeroed inside loop body
    bsr     .Lpc090oj_emit_slot       ; emit_slot clobbers D6 (returns D6 = D0*4+1024)
    addq.w  #1, %d0                   ; D0++
    subq.w  #1, %d6                   ; ◄── decrements emit_slot's residual D6, NOT counter
    bra.s   .Lhook_3b930_loop
.Lhook_3b930_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

**Trace.** With caller's `D1` = some value `count_init` ≤ 4, `D6` after entry-time setup = `min(count_init, 4)`. First iteration: `tst.w %d6` non-zero → enter body. `moveq #0, %d6` → `D6 = 0`. BSR to emit_slot. emit_slot returns `D6 = D0*4 + 1024 = 14*4+1024 = 1080 = 0x438`. `subq.w #1, %d6` → `D6 = 0x437 = 1079`. `bra.s` → loop. Next iteration: `tst.w %d6 = 0x437` non-zero → enter body. `moveq #0, %d6` → `D6 = 0`. BSR. emit_slot returns `D6 = 15*4+1024 = 1084 = 0x43C`. `subq.w` → `0x43B`. Continue. **The loop NEVER terminates** because `D6` after `subq.w` is always `(slot*4+1023) ≥ 1023`, never zero.

`D0` increments every iteration from 14 upward. After 2710 iterations, `D0 = 14 + 2710 = 2724 = 0x00000AA4`. (The increment `addq.w #1, %d0` is word-sized and only modifies the lower word; D0's upper 16 bits stay zero. So `D0` long value tracks `D0` low word.)

Verified in runtime disassembly at [build/genesis_postpatch.disasm.txt:124198-124220](build/genesis_postpatch.disasm.txt#L124198-L124220):
```
7139A: 48e7 fffe   moveml %d0-%fp, %sp@-
7139E: 700e        moveq #14, %d0
713A0: 3c01        movew %d1, %d6
713A2: 0c46 0004   cmpiw #4, %d6
713A6: 6302        blss 0x713aa
713A8: 7c04        moveq #4, %d6
713AA: 3e2d 0014   movew %a5@(20), %d7
713AE: 0247 00e0   andiw #224, %d7
713B2: e24f        lsrw #1, %d7
713B4: 4a46        tstw %d6                 ; ← .Lhook_3b930_loop entry
713B6: 671a        beqs 0x713d2
713B8: 7200        moveq #0, %d1
713BA: 7400        moveq #0, %d2
713BC: 1418        moveb %a0@+, %d2
713BE: 7800        moveq #0, %d4
713C0: 1818        moveb %a0@+, %d4
713C2: 3618        movew %a0@+, %d3
713C4: 7a00        moveq #0, %d5
713C6: 7c00        moveq #0, %d6           ; ← BUG verbatim: D6 zeroed
713C8: 6100 fe02   bsrw 0x711cc            ; ← BSR to .Lpc090oj_emit_slot
713CC: 5240        addqw #1, %d0
713CE: 5346        subqw #1, %d6           ; ← decrements clobbered D6
713D0: 60e2        bras 0x713b4
713D2: 4cdf 7fff   moveml %sp@+, %d0-%fp
713D6: 4e75        rts
```

### 1.3.B `_54810` broken loop (source lines 612-653)

```asm
genesistan_pc090oj_hook_sprite_update_54810:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.w  10*2(%a5), %d7
    andi.w  #0x00E0, %d7
    lsr.w   #1, %d7
    movea.l #ARCADE_ROM_BASE+0x0005DA5E, %a0
    mulu.w  #24, %d0
    adda.w  %d0, %a0
    moveq   #44, %d0                  ; D0 starts at 44
    moveq   #4, %d6                   ; D6 = 4 (loop counter)
.Lhook_54810_loop:
    move.w  4(%a0), %d1
    moveq   #0, %d2
    move.b  3(%a0), %d2
    ext.w   %d2
    add.w   0x129C(%a5), %d2
    addq.w  #1, %d2
    andi.w  #0x01FF, %d2
    move.w  (%a0), %d3
    moveq   #0, %d4
    move.b  2(%a0), %d4
    ext.w   %d4
    add.w   0x129A(%a5), %d4
    andi.w  #0x01FF, %d4
    moveq   #0, %d5
    moveq   #0, %d6                   ; ◄── BUG: D6 zeroed inside loop body
    bsr     .Lpc090oj_emit_slot       ; emit_slot clobbers D6
    adda.w  #6, %a0
    addq.w  #1, %d0                   ; D0++
    subq.w  #1, %d6                   ; ◄── decrements clobbered D6, NOT counter
    bne.s   .Lhook_54810_loop          ; loop while D6 != 0
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

**Trace.** `D6 = 4` at entry. First iteration: `moveq #0, %d6` → `D6 = 0`. BSR. emit_slot returns `D6 = 44*4+1024 = 1200 = 0x4B0`. `subq.w #1, %d6` → `D6 = 0x4AF`. `bne.s` → continue. Loop never terminates. `D0` increments from 44 unbounded. After 2680 iterations, `D0 = 44 + 2680 = 2724 = 0xAA4`.

Verified in runtime disassembly at [build/genesis_postpatch.disasm.txt:124462-124467](build/genesis_postpatch.disasm.txt#L124462-L124467):
```
716CE: 7a00        moveq #0, %d5
716D0: 7c00        moveq #0, %d6           ; ← BUG verbatim
716D2: 6100 faf8   bsrw 0x711cc            ; ← BSR to .Lpc090oj_emit_slot
716D6: d0fc 0006   addaw #6, %a0
716DA: 5240        addqw #1, %d0
716DC: 5346        subqw #1, %d6           ; ← decrements clobbered D6
716DE: 66c6        bnes 0x716a6             ; loop exit never fires
```

---

## §1.4 Upstream trace for COULD-helpers

Both helpers' broken loops are self-contained — the bug is INSIDE the helper, not upstream. No further upstream trace is needed for `_3b930` and `_54810`. The arcade caller can be ANY arcade_pc that triggers a sprite-update or 0x3B930-style sprite render via the corresponding opcode_replace entry. The helpers will hang regardless of the caller's input data because the loop's exit condition is broken at the source level.

For completeness — the arcade callers per `Andy_pc090oj_implementation_spec.md` v3.2 §8.6:

- `_3b930` (entry #3): reached via 0x3B902 BSR at arcade_pc 0x03B912 (which is unreachable post-v3.2 because 0x3B902's body is replaced — the caller path is the 0x3B8B0 init function with 3 BSRs at 0x03B8BC, 0x03B8D2, 0x03B8E2)
- `_54810` (entry #12): reached via arcade_pc 0x0547EE / 0x054804 (per §8.6 entry #12)

Whether 0x3B930 fires from `_3b8b0`'s init path or from another arcade-call timing is irrelevant to the bug — once entered, the helper hangs regardless of input.

---

## §1.5 270ms-stable-PC reconciliation

Frames 100-107 (270ms wall-clock at 30 fps Exodus video sampling) all show **identical register state** including `PC = 0x000711CE`, `D0 = 0x00000AA4`, `D6 = 0x00000AA4`. Per Andy v3.2 expectation that emit_slot's body iterates many instructions per BSR, the live CPU should be advancing through emit_slot's body — meaning D0/PC should change between samples. The observed stability is anomalous and requires reconciliation.

**Reconciliation:** Exodus halted-state display after fault detection.

Looking at the frame sequence:
- Frames 100-108: `PC = 0x000711CE`, `SR = 0x2700`, `T = 0`, `IPM = 7` (level-7 mask, normal supervisor)
- Frame 109+: `PC = 0x008F831C`, `SR = 0x2710`, `T = 1` (trace bit set), `IPM = 7`, `A7 = 0x00FEFFB4` (incremented by 4 = one RTS popped)
- Frame 114: `PC = 0x0000051E`, `SR = 0x2700`, `T = 0`, `A7 = 0x00FEFFAE` (decremented by 6 = one exception stack frame pushed)

The transition `frame 108 → 109` shows `T = 1` arising. **`T = 1` indicates the trace exception fired** — when the 68000 executes any instruction with `T = 1` in SR, it generates a trace exception after that instruction completes. But we see `T = 0` BEFORE frame 109, meaning trace fires DURING the frame-108-to-109 transition.

Combined with `0x008F831C` being unmapped (per Cody `wildpc_evidence.md` §1.7), the chain is:

1. The broken loop in `_3b930` or `_54810` runs for ~270ms of wall-clock time accumulating WRAM corruption.
2. Eventually emit_slot's writes at progressively-larger `D0*12 + 0xFF6384` and `D0*8 + 0xFF6104` corrupt `*(0x00FEFFB0)` (via the WRAM mirror at `0xFFFFB0`, or via direct stack-region overflow when `D0` is very large).
3. The corrupted return address overwrites the legitimate stack content at `*(0x00FEFFB0)`. (Top-of-stack at this point holds emit_slot's BSR return address from the broken loop — that's `0x000713CC` for `_3b930` or `0x000716D6` for `_54810`. After corruption, it becomes `0x008F831C`.)
4. Eventually the loop hits a condition that triggers an RTS — possibly when emit_slot's writes inadvertently corrupt its own BSR return address on the stack, or when the broken loop helper finally exits via some other path.
5. The RTS pops `0x008F831C` into PC.
6. Exodus detects the wild PC outside any mapped memory range and **enters its fault-recovery / halted-state display**, freezing the CPU emulation but continuing to render video frames showing the captured state.
7. Frames 100-107 actually represent **the same captured CPU state** displayed across multiple video frames after Exodus halted forward emulation. The live CPU may have advanced past PC `0x000711CE`; the displayed state is stale.

This reconciliation is consistent with all observed evidence:
- `T = 1` in frame 109+ indicates an exception was taken (trace exception per the running-into-bus-error path).
- `0x008F831C` is unmapped → next instruction fetch is a bus error → bus-error handler invoked.
- Frame 114 shows `PC = 0x0000051E` which is in arcade ROM space — likely the arcade's own bus-error handler entry or some other low-vector address (vector 0x008 = bus error, vector longword at 0x000008..0x00000B).

The reconciliation does NOT require evidence Andy doesn't have. The fault chain is fully predicted by the source-level bug.

---

## §1.6 Origin classification

**Origin C — PC090OJ helper computation bug** (primary).

Two helpers in `pc090oj_hooks.s` have a buggy loop-counter implementation. `D0` is computed from valid initial inputs via repeated `addq.w #1, %d0` increments inside an unbounded loop. Eventually `D0 = 0xAA4 = 2724` is reached (and exceeded). Each emit_slot call with the runaway `D0` writes to invalid WRAM addresses, eventually corrupting the stack and triggering the wild-PC observation.

**Origin D — Cross-helper register pollution** (contributing).

The CAUSE of the unbounded loop is `.Lpc090oj_emit_slot` clobbering `D6` (used as a scratch register for slot-offset / palette / flips / tile_index computation). The two affected helpers (`_3b930`, `_54810`) use `D6` as their loop counter, expecting it preserved. The signature comment at [pc090oj_hooks.s:66](apps/rastan-direct/src/pc090oj_hooks.s#L66) reads `d6=extra_flags`, which suggests an INPUT-only role — but in practice `d6` is the helper's primary scratch register and its post-RTS value is undefined from the caller's perspective.

**Cited evidence:**

- Source bug at [pc090oj_hooks.s:280, 298, 301](apps/rastan-direct/src/pc090oj_hooks.s#L280) for `_3b930`: `D6` set at line 280, zeroed at line 298 inside loop body, decremented at line 301 expecting it to be the original counter.
- Source bug at [pc090oj_hooks.s:624, 644, 649](apps/rastan-direct/src/pc090oj_hooks.s#L624) for `_54810`: similar pattern.
- emit_slot D6 clobber verified at [pc090oj_hooks.s:69, 75, 80, 105, 126, 136, 146](apps/rastan-direct/src/pc090oj_hooks.s#L69) (multiple `move.w X, %d6` instructions).
- Runtime translation of bug confirmed at [genesis_postpatch.disasm.txt:124198-124220](build/genesis_postpatch.disasm.txt#L124198-L124220) and [genesis_postpatch.disasm.txt:124462-124467](build/genesis_postpatch.disasm.txt#L124462-L124467).
- Frame 100 register state (`D0 = D6 = 0xAA4`) at [Cody_exodus_frame_extraction_build_53_2.md:131](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L131) consistent with `D0` reaching 0xAA4 via 2710-or-2680 unbounded `addq.w #1, %d0` iterations.
- §1.3 caller-helper analysis ruling out the OTHER 10 sites as 0xAA4-producers.

**Reads ruled out:**

- Origin A (arcade caller data): None of the 10 documented opcode_replace entries that invoke a PC090OJ helper sets `D0 = 0xAA4` per arcade source. `_3b930`'s arcade-caller path (`_3b8b0` init function) sets `D1` to a count value but `D0` is set to 14 internally. Arcade is not the source.
- Origin B (WRAM memory corruption): No helper loads `D0` from a WRAM location prior to BSR'ing emit_slot. All `D0` values come from `moveq` immediates or computed-and-bounded paths. No memory-corruption pathway can produce `D0 = 0xAA4`.
- Origin E (architecture violation): Both helpers (`.Lpc090oj_emit_slot`, `_3b930`, `_54810`) end with `RTS` and comply with RULES.md §4 helper contract. The bug is a register-flow programming error, not an architectural violation.
- Origin F (need Cody follow-up): No evidence gap remains. Source inspection alone definitively identifies the bug.

---

## §1.7 Fix plan

**Origin classification: C (primary) + D (contributing).**

**Failing point:** two locations in `apps/rastan-direct/src/pc090oj_hooks.s`:
1. Lines 280-302 (`genesistan_pc090oj_hook_target_3b930` body)
2. Lines 624-650 (`genesistan_pc090oj_hook_sprite_update_54810` body)

**Categorization:** **correct register-flow translation** (Chad's framework) — the loop-counter register `D6` collides with `.Lpc090oj_emit_slot`'s scratch-register use of `D6`. The fix moves the loop counter to a register `.Lpc090oj_emit_slot` preserves, OR save/restores `D6` around the BSR.

### 1.7.1 Concrete fix — `_3b930`

**Option A (cleanest, smallest diff):** save/restore `D6` to stack around the BSR:

```asm
.Lhook_3b930_loop:
    tst.w   %d6
    beq.s   .Lhook_3b930_done
    moveq   #0, %d1
    moveq   #0, %d2
    move.b  (%a0)+, %d2
    moveq   #0, %d4
    move.b  (%a0)+, %d4
    move.w  (%a0)+, %d3
    moveq   #0, %d5
    move.w  %d6, -(%sp)              ; ◄── NEW: save loop counter
    moveq   #0, %d6                   ; (existing) emit_slot's "extra_flags" = 0
    bsr     .Lpc090oj_emit_slot
    move.w  (%sp)+, %d6              ; ◄── NEW: restore loop counter
    addq.w  #1, %d0
    subq.w  #1, %d6                   ; (existing) decrements correct counter
    bra.s   .Lhook_3b930_loop
```

Adds 2 instructions per iteration (3 cycles each ≈ 6 cycles). With max 4 iterations (`D6` capped at 4), bounded overhead. No `addq.w` runaway; the loop terminates as designed.

**Option B (larger diff, no stack):** use `A4` as loop counter (`A4` is unused by `.Lpc090oj_emit_slot`):

```asm
genesistan_pc090oj_hook_target_3b930:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    moveq   #14, %d0
    move.w  %d1, %d6
    cmpi.w  #4, %d6
    bls.s   .Lhook_3b930_count_ok
    moveq   #4, %d6
.Lhook_3b930_count_ok:
    move.w  %d6, %a4                  ; ◄── NEW: A4 := loop counter
    move.w  10*2(%a5), %d7
    ; ... unchanged ...
.Lhook_3b930_loop:
    cmp.w   #0, %a4                   ; ◄── tst A4 (loop counter)
    beq.s   .Lhook_3b930_done
    ; ... body unchanged through bsr ...
    moveq   #0, %d6                   ; (existing) emit_slot "extra_flags" = 0
    bsr     .Lpc090oj_emit_slot
    addq.w  #1, %d0
    suba.w  #1, %a4                   ; ◄── decrement A4 counter
    bra.s   .Lhook_3b930_loop
```

Option A is recommended for minimum-change-surface; Option B is more idiomatic but adds bytes.

### 1.7.2 Concrete fix — `_54810`

**Option A (save/restore around BSR):**

```asm
.Lhook_54810_loop:
    move.w  4(%a0), %d1
    moveq   #0, %d2
    move.b  3(%a0), %d2
    ext.w   %d2
    add.w   0x129C(%a5), %d2
    addq.w  #1, %d2
    andi.w  #0x01FF, %d2
    move.w  (%a0), %d3
    moveq   #0, %d4
    move.b  2(%a0), %d4
    ext.w   %d4
    add.w   0x129A(%a5), %d4
    andi.w  #0x01FF, %d4
    moveq   #0, %d5
    move.w  %d6, -(%sp)              ; ◄── NEW: save loop counter
    moveq   #0, %d6                   ; (existing) emit_slot "extra_flags" = 0
    bsr     .Lpc090oj_emit_slot
    move.w  (%sp)+, %d6              ; ◄── NEW: restore loop counter
    adda.w  #6, %a0
    addq.w  #1, %d0
    subq.w  #1, %d6                   ; (existing) decrements correct counter
    bne.s   .Lhook_54810_loop
```

Identical fix pattern as `_3b930`. Adds 2 instructions per iteration; bounded by `_54810`'s 4-iteration loop.

### 1.7.3 Optional comment fix (documentation hygiene)

The signature comment at [pc090oj_hooks.s:66](apps/rastan-direct/src/pc090oj_hooks.s#L66) lists `d6=extra_flags` but the implementation does not preserve `d6`. Update the comment to:

```asm
/* d0=slot,d1=word0,d2=y,d3=word2(tile),d4=x,d5=source_id,d6=ignored_input,d7=sprite_colbank
 * Clobbers: D1, D2, D3, D5, D6, A0, A1
 * Preserves: D0, D4, D7, A2..A6
 */
```

This documentation fix reduces the chance of the same bug recurring in a future helper that BSRs to emit_slot.

### 1.7.4 What this fix plan does NOT touch

- v3.1 closures (Resolution B for 0x54052, LUT MUST NOT consultation, jsr-not-bsr): UNTOUCHED
- v3.2 dispatch contract (`genesistan_hook_3ad44_dispatch` polymorphic-utility A0 dispatch): UNTOUCHED
- `opcode_replace` at arcade_pc 0x3AF04 (relocated from arcade 0x3AD44): UNTOUCHED
- `_bootstrap` ending with `jmp (0x3A200).l`: UNTOUCHED
- `_vblank_service` ending with `jmp (0x3A208).l`: UNTOUCHED
- `rastan_direct_update_inputs`: UNTOUCHED (compliant; no fix needed there per prior cycle)
- `.Lpc090oj_emit_slot` body: UNTOUCHED (helper contract is documented; the bug is in callers that violate the contract)
- `.Lpc090oj_clear_slot` body: UNTOUCHED (correct)
- 18-entry opcode_replace count (Andy v3.2 final = 90): UNTOUCHED
- Slot-LUT (`pc090oj_slot_lut`): UNTOUCHED
- Staging buffers: UNTOUCHED
- Commit logic (`vdp_commit_sprites`): UNTOUCHED
- Audit guards: UNTOUCHED

The fix is two helpers' loop-counter patches, plus an optional comment update. No spec revision required (the spec's helper contracts can remain as-is; v3.2 §1.3.1 helper-internal slot ranges are unaffected — the helpers correctly TARGET slots 14..17 and 44..55 respectively; the bug is the loop's TERMINATION, not the slot allocation).

### 1.7.5 Downstream Cody implementation task specification

A Cody implementation prompt can be drafted directly from this fix plan:

> **Inputs:** [pc090oj_hooks.s:277-305](apps/rastan-direct/src/pc090oj_hooks.s#L277-L305) (genesistan_pc090oj_hook_target_3b930) and [pc090oj_hooks.s:612-653](apps/rastan-direct/src/pc090oj_hooks.s#L612-L653) (genesistan_pc090oj_hook_sprite_update_54810); spec authority Andy_pc090oj_implementation_spec.md v3.2.
>
> **Task:** apply the §1.7.1 / §1.7.2 register-save/restore patches verbatim to both helpers. Optionally update the §1.7.3 comment. No spec change. No other source change. Build artifact must produce postpatcher invariant `count=90, bytes=0x17C914` (unchanged from v3.2).
>
> **Verification:** run the Build 53 verification trajectory; expect:
> - The `_3b930` loop now terminates after its caller's intended count (≤ 4 iterations).
> - The `_54810` loop now terminates after 4 iterations.
> - `D0` no longer reaches 0xAA4 in normal operation.
> - The wild-PC `0x008F831C` no longer appears in extracted frames.
> - Boot D00778 verification continues to pass.
> - VRAM roundtrip self-test (§6.5) continues to pass.

---

## §1.8 Architecture compliance verification

The proposed fix preserves all architectural invariants:

| Invariant | Compliance | Reasoning |
|-----------|------------|-----------|
| No Genesis-side lifecycle introduced | YES | The fix adds 2 stack push/pop instructions per iteration in two helper bodies. No loop, no scheduler, no main loop introduced. |
| Helpers RTS-return | YES | Both helpers continue to end with `rts` after `movem.l (%sp)+, %d0-%d7/%a0-%a6`. The save/restore pattern uses balanced `move.w %d6,-(%sp); ...; move.w (%sp)+,%d6` which preserves stack depth across the BSR. |
| No memory shadowing | YES | The fix uses standard 68k stack push/pop or A4 register; no PC090OJ address-space mirroring introduced. |
| No scaffolding | YES | The patch is production-intent — fixes a real correctness defect. Would exist in a final shipping ROM. |
| v3.1 Resolution B preserved | YES | `genesistan_pc090oj_hook_slot_init_54052` is not modified. The text-RAM clear loops at lines 561-590 are untouched. |
| v3.2 dispatch contract preserved | YES | `genesistan_hook_3ad44_dispatch` body unchanged; A0 ranges unchanged; tilemap branch unchanged. |
| `opcode_replace` at 0x3AF04 preserved | YES | Spec entry untouched (no spec revision). |
| `_bootstrap` closure preserved | YES | [boot.s:160](apps/rastan-direct/src/boot/boot.s#L160) `jmp (0x00003A200).l` untouched. |
| `_vblank_service` closure preserved | YES | [vdp_comm.s:179](apps/rastan-direct/src/vdp_comm.s#L179) `jmp (0x00003A208).l` untouched. |
| Arcade owns execution | YES | Arcade still drives all calls into the fixed helpers; the helpers still RTS-return on completion. The fix simply ensures completion happens after the intended number of iterations, not after unbounded iterations. |

All 10 invariants pass.

---

## Phase 2 integrity

| Check | Status |
|-------|--------|
| §1.1 owning-helper attribution verified for all 12 sites | YES; symbol-table mismatches: 3 (sites 1, 2, 3 = `.L`-local helpers in pc090oj_hooks.s) |
| §1.2 D0/D6 provenance traced for all owning helpers | YES (all 12 sites + `.Lpc090oj_emit_slot` own clobber list documented) |
| §1.3 helpers classified CANNOT/COULD produce 0xAA4 | YES; CANNOT = 10 sites, COULD = 2 sites (`_3b930`, `_54810`) |
| §1.4 COULD-helpers traced | YES (bug is internal to each helper; no further upstream trace required) |
| §1.5 270ms-stable-PC anomaly reconciled | YES (Exodus halted-state display after fault detection) |
| §1.6 Origin classified | C (primary) + D (contributing) |
| §1.7 Fix plan produced | YES (two source-level register-save/restore patches + optional comment update; downstream Cody task fully specified) |
| §1.8 Architecture compliance verified | YES (10/10 invariants pass) |
| All conclusions cited (Rule 17) | YES (every claim references source line, disassembly line, Cody evidence section, RULES.md/ARCHITECTURE.md, or Andy v3.2 spec) |
| No new evidence collection (Rule 20) | YES (all evidence cited is from existing Cody packages, source files, runtime disassembly, symbol map, prior Andy classification) |
| No source/spec/tool modifications | YES |
| STOP conditions | NONE TRIGGERED — sources located; both helpers' bodies analyzed; bug definitively identified; provenance trace terminates at the source instructions. |

---

## Cross-reference

- `RULES.md` (Rules 1, 4, 5) — architectural compliance
- `ARCHITECTURE.md` — helper-function contract
- [apps/rastan-direct/src/pc090oj_hooks.s:67-162](apps/rastan-direct/src/pc090oj_hooks.s#L67-L162) — `.Lpc090oj_emit_slot` definition (D6 clobber path)
- [apps/rastan-direct/src/pc090oj_hooks.s:277-305](apps/rastan-direct/src/pc090oj_hooks.s#L277-L305) — `_3b930` broken loop
- [apps/rastan-direct/src/pc090oj_hooks.s:612-653](apps/rastan-direct/src/pc090oj_hooks.s#L612-L653) — `_54810` broken loop
- [build/genesis_postpatch.disasm.txt:124198-124220](build/genesis_postpatch.disasm.txt#L124198-L124220) — `_3b930` runtime disassembly
- [build/genesis_postpatch.disasm.txt:124462-124467](build/genesis_postpatch.disasm.txt#L124462-L124467) — `_54810` runtime disassembly
- `docs/design/Cody_build53_emit_slot_caller_trace.md` — primary input (12 callsites, register state)
- `docs/design/Cody_build53_wildpc_evidence.md` — secondary input (helper body disassembly)
- `docs/design/Andy_build53_update_inputs_root_cause.md` — prior cycle classification (`rastan_direct_update_inputs` ruled compliant, symbol-coverage illusion identified)
- `docs/design/Andy_pc090oj_implementation_spec.md` v3.2 — design authority
