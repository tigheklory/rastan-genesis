# Cody — PC080SN + PC090OJ Hardware Writer Audit

**Scope:** Read-only disassembly analysis. NO source file modifications. NO remap.json changes. NO builds.

**Context:** Build 0029 still crashes at 0xC09EA0. Runtime trace confirms the writer is at arcade PC 0x3C530, inside a function that was not identified in prior crash analysis. Before proposing any more patches, we need a COMPLETE inventory of every arcade code site that writes to the PC080SN C-window address range AND the PC090OJ sprite RAM range. No more whack-a-mole. No more partial audits. Both graphics chips are audited in one pass because they share the same architectural pattern (direct absolute writes to arcade hardware addresses that have no Genesis equivalent without translation).

**Chip address ranges:**
- **PC080SN** (tilemap chip): 0xC00000–0xC0FFFF (BG/FG tilemaps + rowscroll) plus 0xC20000 (yscroll) and 0xC40000 (xscroll)
- **PC090OJ** (sprite chip): 0xD00000–0xD03FFF (sprite attribute RAM)

**Design reference:** `docs/design/Andy_build_0028_fg_hook_failure_analysis.md`, `docs/design/Cody_build_0029_fg_cwindow_trace_report.md`

---

## OBJECTIVE

Produce a complete, verified inventory of every code site in the arcade ROM (`build/maincpu.disasm.txt` arcade PC range 0x000000–0x05FFFF) that can result in a write to any address in EITHER of these ranges:

- **PC080SN range**: 0xC00000–0xC0FFFF (tilemaps + rowscroll), plus 0xC20000 (yscroll) and 0xC40000 (xscroll)
- **PC090OJ range**: 0xD00000–0xD03FFF (sprite attribute RAM)

These are the ROOT address spaces for both graphics chips. Every writer gets classified — no exceptions, no "probably not relevant" skips.

---

## HARD RULES (FAIL CONDITIONS)

- DO NOT modify `main_68k.s`, `remap.json`, or any source file.
- DO NOT run any builds.
- DO NOT propose or write any patches.
- DO NOT skip any writer because "it looks unreachable" or "probably dead code" — classify EVERY finding.
- DO NOT guess at semantics. If a function's purpose is unclear, write "PURPOSE: UNKNOWN" and move on.
- DO NOT collapse multiple call sites into one entry. Every distinct PC gets its own row.
- DO NOT use approximate or rounded addresses. Every PC must be the exact byte offset of the writing instruction.

If any rule is violated: STOP, report the violation, DO NOT continue.

---

## METHOD (MANDATORY — follow exactly)

### Step 1 — Find all loads of chip base addresses

Scan `build/maincpu.disasm.txt` for every instruction in the arcade PC range 0x000000–0x05FFFF that loads any of these exact constants into a data or address register:

**PC080SN bases:**
- `0x00C00000` (BG tilemap base)
- `0x00C04000` (BG rowscroll base)
- `0x00C08000` (FG tilemap base)
- `0x00C0C000` (FG rowscroll base)
- `0x00C20000` (yscroll register)
- `0x00C40000` (xscroll register)

**PC090OJ bases:**
- `0x00D00000` (sprite RAM base)
- `0x00D01000`, `0x00D02000`, `0x00D03000` (sprite RAM mid-region entry points commonly used as loop bases)
- Any other constant in the range 0x00D00000–0x00D03FFF used as a load target

Search patterns (not exhaustive — cover all M68K addressing modes that can load a 32-bit immediate):

- `207C 00C0 xxxx` through `2E7C 00C0 xxxx` (MOVEA.L #imm, An for An = A0..A7)
- `207C 00D0 xxxx` through `2E7C 00D0 xxxx` (same, PC090OJ range)
- `41F9 00C0 xxxx` through `4FF9 00C0 xxxx` (LEA abs.l, An)
- `41F9 00D0 xxxx` through `4FF9 00D0 xxxx` (same, PC090OJ range)
- `203C 00C0 xxxx` / `203C 00D0 xxxx` through `2E3C ...` (MOVE.L #imm, Dn)
- `0680 00C0 xxxx` / `0680 00D0 xxxx` (ADDI.L #imm, Dn)
- `0480 00C0 xxxx` / `0480 00D0 xxxx` (SUBI.L #imm, Dn)
- `D1FC 00C0 xxxx` / `D1FC 00D0 xxxx` through `DFFC ...` (ADDA.L #imm, An)
- `91FC 00C0 xxxx` / `91FC 00D0 xxxx` through `9FFC ...` (SUBA.L #imm, An)
- Absolute-destination moves in both ranges

For completeness, also grep for literal hex bytes `00C0 8000`, `00C0 0000`, `00C0 4000`, `00C0 C000`, `00C2 0000`, `00C4 0000`, `00D0 0000`, `00D0 1000`, `00D0 2000`, `00D0 3000` appearing anywhere in the instruction stream.

### Step 2 — Find all direct-absolute writes to either chip range

Scan for every instruction that writes a word or longword to an absolute address in 0xC00000–0xC0FFFF OR 0xD00000–0xD03FFF WITHOUT going through a register first. These are instructions like:

- `MOVE.W Dn, abs.l` (opcode 33Cx)
- `MOVE.W (d16,An), abs.l` (opcode 33ED etc.)
- `MOVE.L Dn, abs.l` (opcode 23Cx)
- `CLR.W abs.l` (opcode 42B9)
- `CLR.L abs.l` (opcode 42B9 with .L form)
- `MOVE.W #imm, abs.l` (opcode 33FC)
- `MOVE.L #imm, abs.l` (opcode 23FC)

Capture every instruction where the absolute destination is any address in 0xC00000–0xC0FFFF or 0xD00000–0xD03FFF.

### Step 3 — Trace register flow to find indirect writes

For each register loaded with a PC080SN or PC090OJ base in Step 1, trace forward through the function to find where the register is used as a write destination. Capture:

- Every `MOVE.W Dn, (An)` / `MOVE.W Dn, (An)+` / `MOVE.W Dn, -(An)` / `MOVE.W Dn, (d16,An)` where An holds a C-window address
- Every `MOVE.L` variant of the above
- Every indirect write through An regardless of addressing mode

Be rigorous — if a register is copied (`MOVEA.L A0, A1`), track the copy. If a register is arithmetic-modified (`ADDQ.L #4, A0`), track that the register still points inside or near the chip range.

### Step 4 — Classify each writer

For every writer found in Steps 2 and 3, produce one row in the inventory with these columns:

1. **Arcade PC** — exact hex address of the writing instruction (e.g., `0x03C530`)
2. **Instruction** — full disassembly line (e.g., `movew %d0, %a1@(2)`)
3. **Base load PC** — the arcade PC where the destination register was last loaded with a C-window base (e.g., `0x03C418` for A1 base load)
4. **Destination range** — which chip region is being written: `BG_TILEMAP`, `BG_ROWSCROLL`, `FG_TILEMAP`, `FG_ROWSCROLL`, `YSCROLL_REG`, `XSCROLL_REG`, `SPRITE_RAM`, or `UNKNOWN` if the dest address can't be statically determined. Also include a column **Chip** with value `PC080SN` or `PC090OJ`.
5. **Write pattern** — one of: `SINGLE` (one write), `LOOP_FIXED` (loop with fixed iteration count), `LOOP_DESCRIPTOR` (descriptor-driven loop), `FILL` (bulk fill), `UNKNOWN`
6. **Purpose** — one-sentence description based ONLY on what can be inferred from the disassembly. If unclear: `UNKNOWN`
7. **Callers** — list of arcade PCs that call the enclosing function (find via BSR/JSR scan). Empty if the function appears to be a top-level entry point.
8. **Already hooked?** — check against current `specs/rastan_direct_remap.json`: YES if this PC is the target of an existing `opcode_replace` entry that redirects or neutralizes the write; NO otherwise.

### Step 5 — Cross-check against the runtime trace

Compare the inventory against the Build 0029 trace `fg_cwindow_live` entries. For every PC in the trace log that writes to 0xC08000–0xC0BFFF during the run, confirm it appears in the inventory. Report any trace PC that is NOT in the inventory — that means the audit missed a writer.

Additionally, scan the Build 0029 trace log for any writes to the PC090OJ range (0xD00000–0xD03FFF). Report the count, the list of unique PCs found, and confirm each appears in the inventory. If no PC090OJ writes appear in the trace, that is a valid finding — report it explicitly.

---

## DELIVERABLE

A single report file at:

```
docs/design/Cody_pc080sn_writer_audit_report.md
```

The report MUST contain:

1. **Section 1: Methodology** — confirmation that Steps 1–5 were executed in order, with the exact grep patterns used.

2. **Section 2: Full Inventory Table** — every writer as a markdown table row, sorted by arcade PC ascending. No exceptions. If a writer's purpose is unknown, the row still gets included with `UNKNOWN` in those columns.

3. **Section 3: Writer Count By Destination Range** — a summary table:
   ```
   PC080SN:
     BG_TILEMAP:    N writers
     BG_ROWSCROLL:  N writers
     FG_TILEMAP:    N writers
     FG_ROWSCROLL:  N writers
     YSCROLL_REG:   N writers
     XSCROLL_REG:   N writers

   PC090OJ:
     SPRITE_RAM:    N writers

   UNKNOWN destination: N writers
   ```

4. **Section 4: Already-Hooked Status Summary** — count of writers that are already hooked vs. not hooked, broken down by destination range.

5. **Section 5: Trace Cross-Check** — confirmation that every PC in the Build 0029 `fg_cwindow_live` trace is present in the inventory, or a list of any missing PCs.

6. **Section 6: Unclassified / Suspicious Cases** — any writer where the destination could not be statically determined, or where the flow analysis was inconclusive. Include the exact reason it could not be classified.

---

## VERIFICATION REQUIREMENTS

Before writing the report, verify the following and include a checkbox list at the top:

- [ ] Inventory includes arcade PC 0x055968 (BG strip producer — already hooked) — confirms BG path detection works
- [ ] Inventory includes arcade PC 0x055990 (FG strip producer — already hooked) — confirms FG path detection works
- [ ] Inventory includes arcade PC 0x03AD44 (BG fill hook site — already hooked) — confirms fill detection works
- [ ] Inventory includes arcade PC 0x0561C0–0x0561D2 (old C-window fill loop — now redirected in Build 0029) — confirms prior patch detection
- [ ] Inventory includes arcade PC 0x03C530 (known crash site from Build 0029 trace)
- [ ] Inventory includes arcade PC 0x03C544 (second write in the same loop)
- [ ] Inventory includes arcade PC 0x055AB4 range (scroll register writes — already rewritten)
- [ ] Inventory includes at least one known PC090OJ writer (search for any write to 0xD0xxxx in the arcade ROM — confirms PC090OJ detection works)
- [ ] Inventory includes arcade PC 0x03ADFE, 0x03AE06, 0x03AE16, 0x03AE1E (known PC090OJ/screen-flip NOP suppression sites — already hooked)
- [ ] Every PC listed in the Build 0029 `fg_cwindow_live` trace appears in the inventory
- [ ] All PC090OJ writes found in the Build 0029 trace (if any) appear in the inventory

If ANY checkbox cannot be checked: STOP, report what's missing, DO NOT submit the audit as complete.

---

## WHAT NOT TO DO

- Do NOT propose fixes. This is audit only. Design decisions come after the audit is reviewed.
- Do NOT try to "optimize" the output by grouping similar writers. Every PC gets its own row.
- Do NOT make assumptions about what code is "reachable" or "dead" — include every static writer regardless.
- Do NOT use approximate language ("around 0x3C5xx", "in the 0x3C4 range") — every PC is exact.
- Do NOT paraphrase the disassembly — copy it verbatim.

---

## AGENTS_LOG entry

```
[Cody - Audit, PC080SN + PC090OJ writer inventory]

* Step 1 complete (chip base loads identified for both chips): YES/NO
* Step 2 complete (direct absolute writes for both chips identified): YES/NO
* Step 3 complete (register flow indirect writes identified): YES/NO
* Step 4 complete (all writers classified with Chip column): YES/NO
* Step 5 complete (trace cross-check for both chips): YES/NO
* All verification checkboxes passed: YES/NO
* Total writers found: N
* PC080SN BG_TILEMAP writers: N
* PC080SN BG_ROWSCROLL writers: N
* PC080SN FG_TILEMAP writers: N
* PC080SN FG_ROWSCROLL writers: N
* PC080SN YSCROLL_REG writers: N
* PC080SN XSCROLL_REG writers: N
* PC090OJ SPRITE_RAM writers: N
* UNKNOWN destination writers: N
* Already-hooked writers: N
* Unhooked writers: N
* Every trace PC (PC080SN range) accounted for: YES/NO
* Every trace PC (PC090OJ range) accounted for: YES/NO
* No source files modified: YES/NO
* No remap.json modified: YES/NO
* No builds run: YES/NO
```
