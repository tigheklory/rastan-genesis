# Andy — Text Writer Hook Specification (0x03C3FE)

**Status:** SPEC INCOMPLETE — CRITICAL INCONSISTENCY FLAGGED

---

## STOP — Function-vs-Crash Mismatch

The prompt requests a spec for `genesistan_hook_text_writer_3c3fe` where the original function "writes using (A1)+ → addresses in range 0xC09EA0–0xC09EA6."

**Disassembly evidence shows these two facts are inconsistent:**

1. **0x03C3FE DOES use (A1)+ post-increment writes** — this part matches.
2. **0x03C3FE's ROM table at 0x03C454 does NOT produce destination 0xC09EA0.**

The 0x03C3FE function uses a 6-byte ROM table at 0x03C454 with 8 entries. Decoded from ROM bytes (verified via `xxd -s 0x3C484` before the palette function starts at 0x03C484):

| Entry | Count | dst_off | src_off | Final A1 destination |
|-------|-------|---------|---------|----------------------|
| 0 | 3 | 0x1374 | 0x0157 | 0xC09374 |
| 1 | 3 | 0x1574 | 0x015A | 0xC09574 |
| 2 | 3 | 0x1774 | 0x015D | 0xC09774 |
| 3 | 3 | 0x1974 | 0x0160 | 0xC09974 |
| 4 | 3 | 0x1B74 | 0x0163 | 0xC09B74 |
| 5 | 1 | 0x0D6C | 0x0166 | 0xC08D6C |
| 6 | 1 | 0x0D70 | 0x0167 | 0xC08D70 |
| 7 | 1 | 0x0D74 | 0x0168 | 0xC08D74 |

**None of these produce 0xC09EA0.** The function at 0x03C3FE is not the source of the Build 0029 crash.

### Actual crash producer (identified from Build 0029 trace)

From Cody's `Cody_build_0029_fg_cwindow_trace_report.md`:
- `first_pc: 03C52A`, `last_pc: 03C518`
- `first_addr: C09EA0`, `last_addr: C09EA6`
- `count: 8`

PC 0x03C52A is **inside** subroutine **0x03C516**, which is called via BSR from function **0x03C4D2** at `bsrw 0x3C516` sites 0x03C502 and 0x03C50E. The write instructions are:
- `0x03C530: movew %d0, %a1@(2)` — write to A1+2
- `0x03C544: movew %d7, %a1@(6)` — write to A1+6

This uses **indexed addressing (A1+2, A1+6) with 8-byte stride**, NOT `(A1)+` post-increment. The prompt's description of the write pattern also doesn't match 0x03C3FE's actual write pattern.

### The two functions are architecturally different

| Property | 0x03C3FE | 0x03C4D2 (crash source) |
|----------|----------|--------------------------|
| Write addressing | `(A1)+` post-increment | `A1@(2)`, `A1@(6)` indexed |
| Stride per iteration | 4 bytes (2 words) | 8 bytes |
| A1 initialization | `addal #0xC08000, A1` inside function | A1 passed in by caller |
| Table lookup | 6-byte entries at 0x03C454 | No table; parameters from A0, A4 |
| Crash destinations | 0xC08Dxx, 0xC09xxx (8 fixed entries) | Dynamic, runtime-computed |

---

## REQUIRED DECISION BEFORE SPEC CAN BE WRITTEN

One of the following must be chosen:

### Option A — Spec 0x03C3FE as originally named (documented here)
- Hook at 0x03C3FE does NOT resolve the Build 0029 crash at 0xC09EA0.
- Text output at 0xC08D6C/0xC09374/0xC09574/etc. routes through VDP.
- Crash remains; additional hook still required for 0x03C4D2.

### Option B — Rename to `genesistan_hook_text_writer_3c4d2`
- Hook at 0x03C4D2 addresses the Build 0029 crash source directly.
- Uses 5-byte-per-entry source format (see `moveb %a0@+, %d0` loops in 0x03C516).
- More complex: takes A1 as input parameter, iterates via inner subroutine 0x03C516.

### Option C — Hook both 0x03C3FE and 0x03C4D2
- Each is a distinct text-writer intent class.
- Two separate spec docs, two separate Cody prompts.
- Fully covers the text-writer intent class per Rainbow Islands template.

---

## Recommended Action

**Option C is the correct architectural answer** per the documented intent-class hook strategy in `docs/design/Andy_final_pc080sn_hook_strategy.md` — both functions are text writers to C-window FG, both need hooks.

**However, for immediate crash resolution, Option B is the minimum fix.** The Build 0029 BlastEm crash at 0xC09EA0 is caused by 0x03C4D2 → 0x03C516, not by 0x03C3FE. Hooking 0x03C3FE alone will not change the crash signature.

### My recommendation

Issue a revised prompt that either:
1. Targets **0x03C4D2** (renaming the hook to `genesistan_hook_text_writer_3c4d2`), which is the function that produces 0xC09EA0 writes, OR
2. Requests a spec for **both** functions (0x03C3FE AND 0x03C4D2), producing two separate hook specifications.

The current prompt's target (0x03C3FE) is a valid text-writer function worth hooking eventually, but its spec cannot honestly claim to address the Build 0029 crash at 0xC09EA0.

---

## Conflict Resolution Note

The prompt's HARD RULE states: *"If ANY part of the behavior cannot be fully determined: STOP and explicitly state what is missing and why."*

What is missing: a consistent mapping between the function named in the prompt (0x03C3FE) and the crash behavior described in the prompt (writes to 0xC09EA0–0xC09EA6). These come from two different functions based on disassembly evidence.

What is not missing: the disassembly of 0x03C3FE itself is fully decoded, its table is fully enumerated, and its write pattern is fully understood. A complete spec for 0x03C3FE CAN be written — it just won't fix the current crash.

Awaiting decision on Options A/B/C before finalizing the spec.
