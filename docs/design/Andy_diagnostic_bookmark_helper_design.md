# Andy — Diagnostic Bookmark Helper Design

**Agent:** Andy (Claude Code)
**Type:** Design (analytical only — no implementation, no source/spec/tool/build/ROM modifications)
**Build:** rastan-direct, post-Rule-10 (canonical ROM `dist/rastan-direct/rastan_direct_video_test_build_0057.bin` and successors)
**Date:** 2026-05-07
**Naming:** descriptive output filename per OPEN-002 extended policy
**Scope:** define the diagnostic bookmark helper as project infrastructure per `RULES.md` Rule 10. After this design lands and Tighe approves, the first Cody bookmark cycle becomes implementable as a tightly-bounded insert + revert task pair.

---

## 0. Executive verdict

**The bookmark helper is a 2-byte ROM-resident self-loop named `genesistan_diag_bookmark`, lives in a new file [`apps/rastan-direct/src/diag_bookmark.s`](apps/rastan-direct/src/diag_bookmark.s), is linked into `.text.wrapper` at link-time (resolved address in `out/symbol.txt`), and is referenced by activators via the existing `{symbol:genesistan_diag_bookmark}` postpatch template.**

The activator is an `opcode_replace` entry in [`specs/rastan_direct_remap.json`](specs/rastan_direct_remap.json) using the form `4EF9{symbol:genesistan_diag_bookmark}` (JMP absolute long, 6 bytes) plus NOP padding to fill the target span. Insertion swaps a production entry (if one exists at the target arcade_pc) for the bookmark entry; revert restores the production entry exactly.

Verification is byte-comparison at the symbol address against the canonical 2-byte sequence `60 FE`, with SHA256 backing per Rule 10. The canonical SHA256 is recorded in `AGENTS_LOG.md` on the first build that ships the helper (deterministic for a fixed 2-byte input).

The design satisfies Rule 9 (helper IS final-build infrastructure: immutable, harmless if never reached, ships in the production ROM) and Rule 10 (observation-only, default body is self-loop, ROM not WRAM, byte-verifiable, scoped task discipline).

---

## §1.1 Helper specification

### Byte sequence

```
60 FE
```

Two bytes. Encoded:
- `0x60` — `BRA short` opcode
- `0xFE` — 8-bit signed displacement of `-2`

Effect: branches to the BRA itself. PC stays at the BRA forever; no register, memory, or hardware state changes.

### Why `BRA self`, not `STOP`

Per Rule 10:
- `STOP #$2700` is privileged on the 68000. In user mode it triggers a privilege-violation exception (vector 8), which would transfer control to the exception handler — defeating the bookmark's purpose of halting execution at a knowable point.
- `BRA self` is unprivileged, executes identically in user and supervisor mode, and produces a clean infinite loop visible in any debugger as "PC stuck at this address." That is the entire signal the bookmark exists to produce.

### Why 2 bytes, not 4 or 6

- The 2-byte `BRA short` is the smallest possible self-loop on 68000.
- A 6-byte `JMP absolute long` to self would also work but adds no value over `BRA short` and makes byte-comparison more verbose.
- Smaller helper = less scrutiny load on every revert byte-verification.

### Symbol name

```
genesistan_diag_bookmark
```

Follows existing project convention (`genesistan_*` for hooks/helpers — see [`apps/rastan-direct/out/symbol.txt`](apps/rastan-direct/out/symbol.txt) for naming precedents like `genesistan_palette_hook_*`, `genesistan_pc090oj_hook_*`, `genesistan_hook_tilemap_*`).

The `_diag_bookmark` suffix makes the diagnostic-only nature visible to anyone scanning symbol exports.

### Source file location

New file: [`apps/rastan-direct/src/diag_bookmark.s`](apps/rastan-direct/src/diag_bookmark.s) (does not exist yet; created by Cody on first build that ships the helper).

Contents (canonical, immutable):

```asm
    .section .text,"ax"

    .global genesistan_diag_bookmark

genesistan_diag_bookmark:
    bra     genesistan_diag_bookmark
```

Rationale for new file vs. inline addition to an existing helper file:
- **Separation of concerns.** Bookmark infrastructure is structurally distinct from palette/PC090OJ/tilemap hooks. A separate file makes that boundary readable.
- **Diff-friendly.** Future bookmark-related changes (if any) touch one file, not multiple.
- **Audit-friendly.** Reviewers searching for "is the bookmark infrastructure intact?" can `ls` one file rather than grepping multiple.

### ROM location

Linked as part of `.text.wrapper` per [`apps/rastan-direct/link.ld:14-19`](apps/rastan-direct/link.ld#L14-L19):

```
. = 0x00070000;

.text.wrapper :
{
  *(.text .text.*)
  *(.rodata .rodata.*)
  *(.data .data.*)
}
```

`.text.wrapper` begins at ROM offset `0x00070000`. The helper's exact resolved address is determined at link time and recorded in `out/symbol.txt`. The address may shift between builds as other helpers grow or shrink; this is acceptable because:
- Activators reference the helper via `{symbol:genesistan_diag_bookmark}`, resolved at postpatch time per the existing template mechanism in [`tools/translation/postpatch_startup_rom.py:16`](tools/translation/postpatch_startup_rom.py#L16) (`SYMBOL_TOKEN_PATTERN`).
- The HELPER BYTES (`60 FE`) are immutable regardless of address; SHA256 covers the bytes, not the address.

### Safety claim for the chosen ROM region

Evidence that `.text.wrapper` (>= `0x00070000`) is safe for the bookmark helper:
- **Outside arcade ROM copy:** [`specs/rastan_direct_remap.json:18-22`](specs/rastan_direct_remap.json#L18-L22) defines `whole_maincpu_copy` as `source_start=0x000000, source_end_exclusive=0x060000, dest_start=0x000200`. Arcade ROM occupies Genesis ROM `0x000200..0x060200`. The helper region (`0x70000+`) is strictly outside this range.
- **Outside opcode_replace target ranges:** every `opcode_replace` entry I inspected in the spec uses `arcade_pc` values < `0x060000` (production patches target the arcade ROM copy region, never the helper region). Verified by grep over [`specs/rastan_direct_remap.json`](specs/rastan_direct_remap.json) for `arcade_pc` values; all targets fall in arcade ROM range.
- **Existing project precedent:** all current Genesis-side helpers (`vdp_boot_setup` at `0x70000`, `_vblank_service` at `0x700C2`, `genesistan_palette_hook_3ba64` at `0x712A0`, etc. per [`apps/rastan-direct/out/symbol.txt:151-180`](apps/rastan-direct/out/symbol.txt)) live in this region without conflict. The bookmark helper joining them is structurally identical to existing precedent.
- **Reachable from anywhere via JMP absolute long:** `4EF9` opcode addresses the full 24-bit address space; any arcade-pc target can JMP to any helper-region address.
- **Persists in canonical ROM:** the helper ships in every build's prepatch and post-patch ROM. Rule 9 satisfied: the helper IS final-build infrastructure.

The activator side (which target arcade_pc gets the JMP) is per-cycle scope and is NOT defined here.

---

## §1.2 Build pipeline integration

### Step-by-step (matches existing helper integration)

1. **Source file:** [`apps/rastan-direct/src/diag_bookmark.s`](apps/rastan-direct/src/diag_bookmark.s) created with the body shown in §1.1. Bytes are immutable.
2. **Makefile addition:** [`apps/rastan-direct/Makefile`](apps/rastan-direct/Makefile) gets a new `OBJS` entry:
   ```
   $(OUT_DIR)/diag_bookmark.o
   ```
   plus the assemble rule:
   ```
   $(OUT_DIR)/diag_bookmark.o: $(SRC_DIR)/diag_bookmark.s | $(OUT_DIR)
       $(AS) $(ASFLAGS) -o $@ $<
   ```
3. **Link:** `m68k-elf-ld` links `diag_bookmark.o` into `.text.wrapper` per existing link.ld (no link.ld change needed).
4. **Symbol:** `m68k-elf-nm` exports `genesistan_diag_bookmark` to [`apps/rastan-direct/out/symbol.txt`](apps/rastan-direct/out/symbol.txt) — mechanically identical to how all other hook symbols are exported.
5. **Postpatcher:** when a bookmark activator entry is in `specs/rastan_direct_remap.json`, [`tools/translation/postpatch_startup_rom.py`](tools/translation/postpatch_startup_rom.py) resolves `{symbol:genesistan_diag_bookmark}` to the link-time address per its existing `SYMBOL_TOKEN_PATTERN` mechanism — mechanically identical to how production hooks are resolved.

**No new build infrastructure is required.** The bookmark helper integrates exactly like every other Genesis helper. Adding the helper is a one-time infrastructure change (new source file + 4-line Makefile addition); subsequent bookmark cycles reuse it.

### First-build sequencing

Cody's first task that ships the helper:
1. Add the source file with the canonical 2-byte body.
2. Add the Makefile entries.
3. Build. Capture `out/symbol.txt` line for `genesistan_diag_bookmark`.
4. Compute SHA256 of the 2 bytes at the resolved address in the canonical ROM. Record in `AGENTS_LOG.md` as the canonical reference for all subsequent verifications.
5. NO activator inserted in this first build. The first build only ships the helper; the helper is dormant (never JMPed to) and harmless. This is the canonical no-bookmark-active baseline.
6. Bookmark cycles begin in subsequent builds, each one inserting an activator (immediate next ROM-producing build reverts).

This first build is sequential per OPEN-002 (next number after `0057.bin` / current latest sequential) and is also clean-build #1 of 3 toward OPEN-002 closure (per current OPEN-002 progress).

---

## §1.3 Activator specification

### Activator form

An `opcode_replace` entry in [`specs/rastan_direct_remap.json`](specs/rastan_direct_remap.json):

```json
{
  "arcade_pc": "0xXXXXXX",
  "original_bytes": "<canonical pre-insertion bytes at target — see §1.4 'Canonical ROM' baseline>",
  "replacement_bytes": "4EF9{symbol:genesistan_diag_bookmark}<NOP padding>",
  "note": "DIAGNOSTIC BOOKMARK ACTIVATOR — temporary. Inserted to answer reachability question: <question>. Reverts in immediately-following ROM-producing build per RULES.md Rule 10. Cycle ID: BM-NNN."
}
```

Where:
- `4EF9` = JMP absolute long opcode (6-byte instruction)
- `{symbol:genesistan_diag_bookmark}` = 4-byte address resolved at postpatch time
- NOP padding (`4E71` × N) fills any remaining bytes in the original target span

Total replacement is 6 bytes (JMP) + 2N bytes of NOPs to match the original span length.

### Production-entry conflict handling

If the target arcade_pc is already covered by a production `opcode_replace` entry (e.g., `0x055968` is currently the `genesistan_hook_tilemap_plane_a` activation site), the bookmark cycle MUST handle the conflict explicitly:

**Insert task:**
- The production entry at the target is **commented out** (or removed) in the spec edit.
- The bookmark activator entry is added at the same `arcade_pc` with `original_bytes` matching the production entry's `replacement_bytes` (the bytes currently in the canonical ROM at that address).
- Build sequential ROM. AGENTS_LOG records: production entry suspended; bookmark activator inserted; canonical bytes captured before/after.

**Revert task:**
- The bookmark activator entry is removed from the spec.
- The production entry is restored (uncommented or re-added) exactly as it was.
- Build sequential ROM (immediately-next per Rule 10). AGENTS_LOG records: bookmark activator removed; production entry restored; canonical bytes verified to match pre-insertion baseline.

**No-conflict case:** if the target is NOT covered by any production entry, the bookmark cycle simply adds a new entry on insert and removes it on revert; no production-entry juggling needed.

### Why JMP not JSR

`JSR` (`4EB9`) pushes a return address onto the stack and would let execution resume after the bookmark. Bookmarks halt; resumption is exactly what we don't want. `JMP` (`4EF9`) discards the would-be return address; the helper's `BRA self` produces an unrecoverable loop. This is the intended observation primitive.

---

## §1.4 Verification mechanics

### "Canonical ROM" baseline (per Rule 10)

The canonical baseline for byte verification is the **current canonical post-patch ROM artifact** — currently `dist/rastan-direct/rastan_direct_video_test_build_0057.bin` and its sequential successors per OPEN-002. This baseline includes any production `opcode_replace` patches that were in effect when that ROM was built; it does NOT mean raw arcade bytes.

When a bookmark activator overlays a production entry, the activator's `original_bytes` field captures the production entry's `replacement_bytes` as they appear in the canonical ROM, NOT the underlying arcade-original bytes.

### Helper byte verification (every build that ships the helper)

```
Procedure:
  1. Read out/symbol.txt; locate line for genesistan_diag_bookmark.
  2. Parse the resolved address (e.g., 0x000XXXXX).
  3. Read 2 bytes from the canonical ROM at that offset.
  4. Compare bytes against the canonical sequence: 60 FE.
  5. Compute SHA256 of those 2 bytes.
  6. Compare SHA256 against canonical reference (recorded in AGENTS_LOG entry of the first build that shipped the helper).
  7. Match → continue. Mismatch → STOP per Rule 10.
```

Implementation note: Cody's first bookmark cycle implements `tools/translation/verify_diagnostic_bookmark.py` (or equivalent shell snippet) following this procedure. The tool takes `--rom <path>`, `--symbols <path>`, `--expected-bytes 60FE`, `--expected-sha256 <hash>` as arguments. Mismatch returns non-zero exit; build aborts.

Equivalent shell-only check (for ad-hoc verification):
```bash
addr=$(grep "genesistan_diag_bookmark" out/symbol.txt | awk '{print "0x"$1}')
bytes=$(dd if=ROM_PATH bs=1 skip=$((addr)) count=2 2>/dev/null | xxd -p)
test "$bytes" = "60fe" && echo OK || echo FAIL
```

### Activator byte verification (every insert task)

```
Procedure:
  1. After build completes (sequential ROM produced), parse the activator entry in specs/rastan_direct_remap.json for the cycle.
  2. Resolve {symbol:genesistan_diag_bookmark} to its postpatch address X.
  3. Read 6 bytes from the ROM at the activator's arcade_pc.
  4. Compare to expected: 4EF9 followed by X encoded as 4-byte big-endian.
  5. Read the NOP-padding bytes (if any) following the JMP; verify all 4E71.
  6. Read 2 bytes from the ROM at address X; verify 60 FE (helper bytes intact).
  7. All match → activator correctly installed. Mismatch → STOP per Rule 10.
```

### Activator byte verification (every revert task)

```
Procedure:
  1. After revert build completes, read the bytes at the cycle's target arcade_pc.
  2. Compare to the cycle's recorded pre-insertion canonical bytes (logged in AGENTS_LOG insert entry).
  3. Match → revert successful. Mismatch → STOP per Rule 10.
  4. Verify helper SHA256 still matches canonical reference (helper is immutable; this is a smoke test for the helper itself).
  5. Verify the bookmark activator entry is REMOVED from specs/rastan_direct_remap.json.
  6. Verify the production entry (if any was suspended on insert) is RESTORED in the spec, byte-for-byte identical to its pre-insertion state.
```

### Mismatch as STOP condition

Per Rule 10: any byte-verification mismatch is a STOP condition. Build aborts. AGENTS_LOG records the failure. No ROM ships with verification failure.

---

## §1.5 AGENTS_LOG required fields

### Insert task entry

```markdown
## [Cody — Diagnostic Bookmark Insert: BM-NNN]

* files changed:
  - specs/rastan_direct_remap.json (production entry at 0xXXXXXX commented; bookmark activator added)
  - apps/rastan-direct/Makefile (no change after first-build introduction)
  - dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin (sequential ROM produced)
  - AGENTS_LOG.md (this append)
* build produced: YES
* ROM path: dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin
* root cause confirmed: N/A (evidence-collection cycle)
* fix implemented: NO (diagnostic, not a fix)
* no unrelated changes: YES

Floor (bookmark cycle BM-NNN insert):
- Cycle ID: BM-NNN
- Target arcade_pc: 0xXXXXXX
- Evidence question: "<the question this cycle answers>"
- Hypothesis: "<expected outcome — reached / not reached / inconclusive>"
- Helper symbol: genesistan_diag_bookmark
- Helper resolved address: 0x000XXXXX (from out/symbol.txt)
- Helper bytes: 60 FE (2 bytes)
- Helper SHA256: <hash> (matches canonical reference in [Cody — Diagnostic Bookmark Helper First-Build Reference])
- Canonical pre-insertion bytes at target: <hex string>
- Activator replacement bytes: 4EF9 <resolved-address-bytes> <NOP padding>
- Production entry suspended: YES/NO (if YES, cite the entry's note field for traceability)
- Build number: NNNN (sequential per OPEN-002; no letter suffix)
- Verification: insert byte-verification PASS at target arcade_pc and at helper address
- STOP triggered: NO

Open/Closed Issues Impact:
- Open issues touched: <list>
- New issues opened: NONE (unless cycle reveals new issue)
- Issues closed: NONE
- Issues intentionally deferred: <list>

REVERT REQUIREMENT: this activator MUST be reverted in the immediately-following ROM-producing build per RULES.md Rule 10. Revert task is `Cody — Diagnostic Bookmark Revert: BM-NNN`.
```

### Revert task entry

```markdown
## [Cody — Diagnostic Bookmark Revert: BM-NNN]

* files changed:
  - specs/rastan_direct_remap.json (bookmark activator removed; production entry restored if applicable)
  - dist/rastan-direct/rastan_direct_video_test_build_NNNN+1.bin (sequential ROM produced)
  - AGENTS_LOG.md (this append)
* build produced: YES
* ROM path: dist/rastan-direct/rastan_direct_video_test_build_NNNN+1.bin
* root cause confirmed: N/A
* fix implemented: NO
* no unrelated changes: YES (no change beyond the activator removal and any production-entry restoration)

Floor (bookmark cycle BM-NNN revert):
- Cycle ID: BM-NNN (matches insert)
- Target arcade_pc: 0xXXXXXX (matches insert)
- Pre-revert bytes at target (matches insert's replacement_bytes): <hex string>
- Post-revert bytes at target: <hex string>
- Pre-revert bytes match insert's recorded post-insertion bytes: YES (or STOP)
- Post-revert bytes match insert's recorded pre-insertion canonical bytes: YES (or STOP)
- Helper symbol: genesistan_diag_bookmark (still present in symbol map; never removed)
- Helper SHA256: <hash> (matches canonical reference; helper is immutable)
- Production entry restored (if applicable): YES (cite original production entry note field)
- Build number: NNNN+1 (sequential per OPEN-002; immediately-next per Rule 10)
- Evidence outcome:
  - Reached: YES/NO/INCONCLUSIVE
  - How determined: <e.g., MAME breakpoint at helper address shows N hits in T seconds; OR Exodus PC sample shows execution stuck at helper address; OR no evidence captured>
- Next step: <what's done with this evidence>
- Verification: revert byte-verification PASS at target arcade_pc; helper SHA256 still PASS
- STOP triggered: NO

Open/Closed Issues Impact:
- Open issues touched: <list — including any whose evidence base advanced from this cycle>
- New issues opened: NONE (unless cycle revealed new issue)
- Issues closed: NONE (unless evidence outcome justifies closure of an existing open issue)
- Issues intentionally deferred: <list>
```

### First-build helper-introduction entry (one-time, before any cycle)

```markdown
## [Cody — Diagnostic Bookmark Helper First-Build Reference]

* files changed:
  - apps/rastan-direct/src/diag_bookmark.s (new)
  - apps/rastan-direct/Makefile (added diag_bookmark.o to OBJS + assemble rule)
  - apps/rastan-direct/out/symbol.txt (regenerated; includes genesistan_diag_bookmark line)
  - dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin (sequential ROM with helper present, no activator)
  - AGENTS_LOG.md (this append)
* build produced: YES
* ROM path: dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin
* root cause confirmed: N/A (infrastructure introduction)
* fix implemented: NO
* no unrelated changes: YES

Floor (bookmark helper first build):
- Helper symbol: genesistan_diag_bookmark
- Helper resolved address: 0x000XXXXX (from out/symbol.txt)
- Helper bytes: 60 FE (2 bytes)
- Helper SHA256 (CANONICAL REFERENCE; all subsequent verifications compare to this): <computed hash>
- No activator inserted; helper is dormant in this build
- ROM produces same visible behavior as prior sequential ROM (helper is never JMPed to)
- Build number: NNNN (sequential per OPEN-002; clean-build #2 of 3 if first OPEN-002 clean build is the previous sequential ROM)
- Verification: helper byte-comparison PASS; helper SHA256 recorded as canonical reference
- STOP triggered: NO

Open/Closed Issues Impact:
- Open issues touched: OPEN-002 (this is one of the 3 consecutive clean ROM-producing builds toward closure), OPEN-008 (continued convention use)
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: <list>
```

---

## §1.6 Rule 9 + Rule 10 compliance

### Rule 9 — "If It Doesn't Belong in Final Build, It Doesn't Belong Here"

The helper IS final-build infrastructure:
- It ships in every ROM (the prepatch binary contains `60 FE` at the helper symbol address; the postpatch ROM preserves it; production ROMs distributed to end users contain the same 2 bytes at the same address).
- It is harmless if never reached: `BRA self` cannot fall through, cannot side-effect anything, cannot be triggered by accident. The only way it executes is via an explicit JMP from an activator.
- It is immutable: the bytes never change across builds; the symbol is permanent.

The activator is a transient infrastructure element governed by Rule 10's revert obligation. Its presence in any single build is defensible (one half of a two-build cycle) and its absence after revert is provable (revert byte-verification + AGENTS_LOG revert entry). Rule 9 is satisfied because the activator is reverted before it can ship in a second consecutive ROM.

### Rule 10 — Diagnostic Bookmarks

| Rule 10 constraint | Compliance in this design |
|---|---|
| Helper in safe high-ROM region | YES — `.text.wrapper` (>= `0x00070000`); cited evidence in §1.1 "Safety claim" |
| Bytes immutable across builds | YES — source file body is canonical; `60 FE` is the only correct content |
| SHA256-verifiable | YES — verification mechanics in §1.4; canonical SHA256 recorded in first-build entry per §1.5 |
| Default body self-loop, NOT STOP | YES — `BRA self` (`60 FE`); rationale in §1.1 "Why `BRA self`, not `STOP`" |
| Helper inert when not jumped to | YES — `BRA self` cannot fall through; no side effects; only reachable via explicit activator JMP |
| Helper persists as project infrastructure | YES — source file, Makefile entry, symbol, integration are all permanent |
| Activator reverted in immediately-following ROM-producing build | YES — Rule 10's clock measured in ROM-producing builds (per Rule 10 explicit text); revert task pattern in §1.5 enforces this |
| Activator persistence across two consecutive ROM builds forbidden | YES — revert task is the immediate next sequential ROM; non-revert intermediate ROMs would violate Rule 10 |
| Insert + revert logged in AGENTS_LOG | YES — required-fields specs in §1.5 |
| Byte-verified against canonical ROM | YES — verification mechanics in §1.4; mismatch → STOP |
| ROM, not WRAM | YES — helper lives in `.text.wrapper`; addresses `>= 0x00070000` are ROM, not WRAM (WRAM is at `0xFF0000+` per [`apps/rastan-direct/link.ld:21`](apps/rastan-direct/link.ld#L21)) |
| Scoped task | YES — insert task contains only spec edit + build; revert task contains only spec edit + build; no other source/spec/tool changes mixed in |
| At most one bookmark cycle in flight at any time | YES — single-task discipline per Rule 10; design's task patterns enforce this |
| Observation only | YES — helper produces no side effects; activator is a JMP that diverts execution to halt point |
| STOP conditions cited | YES — verification mismatches at insert, helper, revert all trigger STOP per §1.4 |

All 14 Rule 10 constraints are addressed.

---

## §1.7 Surfaced ambiguities

### Ambiguity 1 — Helper address stability

**Question:** Should the helper's resolved address be **pinned** (link.ld modified to fix the helper at e.g. `0x0007FFFE`) or allowed to **shift** with normal link-order behavior?

**Chosen interpretation:** **Allow to shift; rely on symbol-table indirection for stability.**

**Reasoning:**
- The activator references the helper via `{symbol:genesistan_diag_bookmark}`, resolved at postpatch time. Address shifts between builds don't break the activator; the symbol resolution catches them.
- Pinning would require a link.ld modification (one-time but invasive). Symbol indirection requires zero infrastructure beyond what already exists.
- Rule 10 specifies bytes are immutable, not address. The bytes (`60 FE`) are immutable regardless of where they land.
- Trade-off: pinned addresses produce more diff-readable spec entries (literal addresses visible in `replacement_bytes` post-resolution); symbol-indirection keeps spec entries symbol-templated until postpatch. The project already favors symbol-templated entries for every other helper, so consistency wins.

**Alternative considered:** pin to `0x0007FFFE` via custom link section. Rejected because the cost (link.ld change + special-section discipline) outweighs the benefit (slight diff-readability gain).

### Ambiguity 2 — When the bookmark target is itself currently opcode_replaced

**Question:** If a bookmark cycle targets an arcade_pc that is already covered by a production `opcode_replace` entry, what's the canonical baseline for byte verification, and how is the production entry handled?

**Chosen interpretation:** **Canonical baseline = the production entry's `replacement_bytes` (the bytes currently in the canonical ROM at that address). Production entry is suspended on insert and restored on revert.**

**Reasoning:**
- Rule 10's "Canonical ROM" language defines the baseline as the current canonical post-patch artifact. Production patches ARE post-patch state. Treating them as baseline preserves the meaning of "canonical" and matches how byte verification will actually work in practice.
- Suspending the production entry on insert (commenting it out in the spec, not deleting from history) keeps the spec edit auditable; restoring on revert is provably exact (byte-for-byte identical to the suspended block).
- Alternative (preserve production entry alongside bookmark entry at same arcade_pc) would create a duplicate-key conflict in the postpatcher and is not supported by the existing tooling.
- Documented as the standard cycle pattern in §1.3 "Production-entry conflict handling."

### Ambiguity 3 — Multi-target bookmark cycles

**Question:** What if a single evidence question requires multiple simultaneously-active bookmarks (e.g., "did execution reach EITHER A OR B?")?

**Chosen interpretation:** **Out of scope for this design. Each cycle handles one target. Multi-target evidence questions are answered by sequential single-target cycles.**

**Reasoning:**
- Rule 10 "Scoped task" + "At most one bookmark cycle in flight at any time" effectively forbid multi-target cycles. A single ROM build cannot insert two activators.
- Sequential cycles are slower but simpler. Each cycle's revert byte-verification is a clean, single-target check. Multi-target cycles would require a more complex verification protocol.
- If multi-target proves necessary in practice (e.g., reachability of A is meaningful only relative to B, requiring simultaneous instrumentation), a separate Rule 10 amendment would relax the single-cycle constraint. For now, the constraint stands.
- This design declines to invent the multi-target protocol speculatively.

### Ambiguity 4 — First-build helper introduction

**Question:** Does the first build that ships the helper count as a "bookmark cycle" requiring the same insert/revert discipline?

**Chosen interpretation:** **No. The first-build helper introduction is an infrastructure-introduction task, not a bookmark cycle. It ships the helper without an activator. No revert is required because there is no transient state to revert.**

**Reasoning:**
- Rule 10's revert obligation applies to activators, not to the helper itself. The helper is permanent infrastructure.
- The first build adds the helper source file and Makefile entry; this is a one-time introduction. Subsequent bookmark cycles reuse the same helper.
- The first-build task does count as a clean ROM-producing build under OPEN-002 (sequential numbering, no letter suffix, descriptive task name). It contributes to OPEN-002 closure progress.
- Documented as `[Cody — Diagnostic Bookmark Helper First-Build Reference]` template in §1.5.

---

## §1.8 What this design does NOT do

- It does NOT add the helper to source. That's a Cody first-build task.
- It does NOT insert any activator. That's a Cody bookmark insert task.
- It does NOT specify which arcade_pc the first cycle targets. That's a separate decision based on which evidence question takes priority (most likely the strip producer at `0x055968` to test the OPEN-001/OPEN-004 dependency hypothesis from `Andy_nametable_composition_path_classification.md`, but that's not decided here).
- It does NOT implement `tools/translation/verify_diagnostic_bookmark.py`. That's a Cody task accompanying the first cycle.
- It does NOT modify `RULES.md` Rule 10's "Out of scope for this rule" subsection. See §1.9 below.

---

## §1.9 RULES.md update decision

**Decision: Rule 10's "Out of scope for this rule" subsection IS updated** to cite this design document, replacing the placeholder "Until that task lands, no bookmark cycle may begin."

**Reasoning:**
- The placeholder was specifically a gating sentence pending this exact task.
- Future agents reading Rule 10 should immediately know where the helper specifics live, without having to grep AGENTS_LOG.
- The citation is one line; the cost is minimal.
- Without the citation, a future agent could read Rule 10 and not know the helper has been designed; they might needlessly re-author or hesitate to start a cycle.

The replacement text is one short paragraph pointing at `docs/design/Andy_diagnostic_bookmark_helper_design.md`. See §1.9-applied below for the exact diff.

### Applied edit (Phase 2 of this task)

`RULES.md` Rule 10's "Out of scope for this rule" subsection is updated as follows:

**Before (current text):**
> The specific helper address, byte sequence, and symbol name are assigned in a separate documentation task. Until that task lands, no bookmark cycle may begin.

**After (post-edit text):**
> The specific helper bytes, symbol name, and build-pipeline integration are defined in `docs/design/Andy_diagnostic_bookmark_helper_design.md`. Bookmark cycles may begin once Tighe approves that design and Cody ships the first build introducing the helper. The helper's resolved address is recorded in `out/symbol.txt` after the first build.

This replaces the placeholder while preserving Rule 10's intent and adding a forward citation that any future agent will find immediately upon reading Rule 10.

---

## Phase 4 Integrity

- Helper design document produced: YES — this document
- All §OBJECTIVE items resolved with cited evidence:
  - Helper location: §1.1 (`.text.wrapper >= 0x00070000`, cited via link.ld and existing helper precedent)
  - Helper byte sequence: §1.1 (`60 FE` = `BRA self`, with reasoning)
  - Symbol name: §1.1 (`genesistan_diag_bookmark`)
  - Source file: §1.1 ([`apps/rastan-direct/src/diag_bookmark.s`](apps/rastan-direct/src/diag_bookmark.s))
  - Build integration: §1.2 (Makefile + link.ld unchanged + symbol export)
  - SHA256 verification mechanics: §1.4 (procedure, canonical baseline, mismatch → STOP)
  - Activator-to-helper reference form: §1.3 (`4EF9{symbol:genesistan_diag_bookmark}` + NOP padding)
  - AGENTS_LOG insert/revert required fields: §1.5 (three template entries)
  - Byte-verification mechanics: §1.4 (insert + revert + helper, all with mismatch → STOP)
- Safe high-ROM region selected with cited evidence: YES (§1.1 "Safety claim")
- Rule 9 + Rule 10 compliance demonstrated: YES (§1.6 14-row table)
- No forbidden modifications by Andy: YES (this task is documentation only)
- Ambiguities surfaced: 4 (§1.7)
- All STOP conditions either passed or documented: YES (no STOP triggered; all required §OBJECTIVE items resolved)
