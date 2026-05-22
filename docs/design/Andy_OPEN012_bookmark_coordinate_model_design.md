# Andy — OPEN-012 Bookmark Coordinate Model Replacement Design

**Agent:** Andy (Claude Code)
**Type:** Design (analytical only — no implementation, no source/spec/tool/Makefile/build/ROM modifications)
**Build:** rastan-direct, post-BM-002-investigation. Canonical baseline Build 0070, SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`.
**Date:** 2026-05-18
**Naming:** descriptive output filename per OPEN-002 extended policy.
**Scope:** specify the replacement bookmark coordinate model — trace-derived diagnostic bookmarks targeted by final runtime Genesis PC, inserted post-relocation, on a spec path separate from `opcode_replace`. The coordinate-model decision is fixed by evidence; this design specifies, not re-deliberates.

---

## 0. Executive verdict

**Replacement model:** trace-derived diagnostic bookmarks use a new top-level spec field `diagnostic_bookmarks_v2` (or `bookmarks_v2`; Andy picks `bookmarks_v2` for brevity below) whose entries carry a single target coordinate field — `runtime_genesis_pc` — which is the literal 68000 PC value the trace reports. The activator byte-write happens **after all `opcode_replace` mutations**, inside the postpatcher, as a new dedicated stage. The write address is the file offset N where N = `runtime_genesis_pc`, exploiting the fixed 1:1 cartridge-ROM-to-CPU-address mapping that holds across all Genesis ROM regions.

**Why this eliminates the BM-001/BM-002 fault:** the trace reports `pc=03a19c` as the literal 68000 PC. With the new model, the bookmark spec stores exactly that value, and the postpatcher writes activator bytes at file offset `0x03A19C` — the byte position the CPU fetches when PC = `0x03A19C`. No translation, no `identity_offset` lookup, no per-segment arithmetic. Zero hand-performed cross-space conversion in the bookmark workflow.

**Deliverable 6 finding (recorded definitively):** `identity_offset` is a **global constant 0x200** across all 75 `arcade_copy` segments in the current build configuration (per `address_map.json` query: every `arcade_copy` segment carries `identity_offset: 512`; no other value appears). Other segment kinds (`genesis_only`, `patched_site`, `preserved_vectors`) have no `identity_offset` at all — they are Genesis-native or patch overlays, not translations. The BM-002 investigation's prose "differ by `identity_offset = 0x200`" is empirically correct for the current configuration; the function notation `identity_offset(trace_pc)` in §7.1 of that report is over-cautious — defensible as future-proofing but unnecessary in current state. **The design eliminates the question entirely:** under `runtime_genesis_pc` targeting, no part of the bookmark workflow needs to read `identity_offset` at all. If the constant ever changes (different build configuration, new segment kinds), the bookmark workflow is unaffected.

**CLOSED-009 ripple summary (§5 walks each mechanism):**
- Build-mode detection: REVISED (new schema; same trigger predicate)
- `expected_count = 94 + N` invariant: REVISED — opcode_replace count returns to strict canonical 94 always; N tracking moves to the bookmark-specific path
- `total_genesis_bytes_covered = 0x17CAEC + Σ`: REVISED — opcode_replace coverage returns to strict canonical 0x17CAEC always; activator overwrites are post-postpatcher direct writes outside the segment_coverage accounting
- `DIAGNOSTIC_SYMBOLS` allowlist: REVISED — same allowlist, different consumer (new bookmark resolver instead of generic `{symbol:...}` template resolver in opcode_replace)
- Cross-reference consistency check: OBSOLETE — single-entry bookmarks don't need it
- §2.7 activator integrity check: REPLACED by §5.6's new check
- §2.8 byte-identical revert: UNCHANGED
- `active_bookmark_baseline.json` state-file lifecycle: UNCHANGED

CLOSED-009's closure was validated against the old schema's 13-test matrix. The mechanisms (state file, byte-identical revert, helper integrity, postpatcher invariant honesty) are sound. The SCHEMA those mechanisms operate on is changing. This is a material substrate change warranting tracked re-verification — **OPEN-013 (new) tracks CLOSED-009 re-verification under the new schema**.

**Cycle ID retirement:** BM-001 and BM-002 are permanently retired. Corrected cycles resume at BM-003. BM-001/BM-002 evidence folders frozen as OPEN-012 evidence.

**`opcode_replace` untouched:** the new model is purely additive to the bookmark side. `opcode_replace` keeps `arcade_pc` and its existing arcade-source semantics. No bookmark-side field is ever named `arcade_pc`.

---

## §1 Deliverable 6 — identity_offset semantics, settled

### §1.1 Empirical finding from address_map.json

Query over `build/rastan-direct/address_map.json`:

```
arcade_copy segments: 75
distinct identity_offset values: [512]

Other kinds:
  genesis_only:        identity_offset absent (None)
  patched_site:        identity_offset absent (None)
  preserved_vectors:   identity_offset absent (None)
```

Every `arcade_copy` segment carries `identity_offset = 512 (= 0x200)`. No other value appears. There is exactly **one** translation mode in the current configuration, and it is constant.

### §1.2 Disposition of the BM-002 report's prose ambiguity

The BM-002 investigation (`docs/design/Andy_BM002_runtime_failure_investigation.md`) §2 cites a single segment showing `identity_offset 512` and prose refers to "differ by `identity_offset = 0x200`" (reads as constant). §7.1 writes `identity_offset(trace_pc)` (function notation, piecewise reading). Tighe's intuition was that the offset grows with depth.

**Definitive reading, recorded:** for the current build configuration, `identity_offset` for `arcade_copy` segments is a global constant `0x200`. Tighe's "grows with depth" intuition is empirically false for the current build. The function notation in §7.1 of the BM-002 report is over-cautious; the constant reading is accurate. Future builds COULD introduce piecewise offsets if multiple arcade ROMs are mapped or if the dest_start changes per segment — but that is speculative, not current state.

### §1.3 Why this finding does NOT change the design

The whole purpose of the `runtime_genesis_pc` model is to eliminate the bookmark workflow's dependency on `identity_offset` semantics — constant or piecewise. The trace reports runtime PCs; the spec stores runtime PCs; the postpatcher writes at file offset = runtime PC (using the fixed Genesis ROM-to-CPU mapping). At no point does the workflow need to know `identity_offset`. The constant-vs-piecewise question is settled for the record but is no longer load-bearing for the bookmark mechanism.

`opcode_replace` (translated arcade code) still depends on `identity_offset` semantics — that's its job. The postpatcher's existing translation of `arcade_pc → ROM file offset` for `opcode_replace` entries is unchanged.

---

## §2 Deliverables 1 & 8 — `bookmarks_v2` spec path

### §2.1 Top-level spec field

A new top-level field is added to `specs/rastan_direct_remap.json`:

```json
{
  "version": 1,
  ...existing fields including required_symbols, policy, whole_maincpu_copy, opcode_replace, expectations...,
  "bookmarks_v2": [
    {
      "cycle_id": "BM-003",
      "runtime_genesis_pc": "0x0003A19C",
      "span_length": 8,
      "pre_insert_canonical_bytes": "66f42e780000207800044ed0",
      "helper_symbol": "genesistan_diag_bookmark",
      "activator_pattern": "JMP_LONG_ABS",
      "nop_padding_byte": "0x4E71",
      "pre_insert_canonical_rom_sha256": "72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc",
      "note": "BM-003 reachability probe at runtime PC 0x03A19C (delay-loop / soft-reset preamble; was BM-002's intended target, corrected for coordinate model)."
    }
  ]
}
```

**Field definitions:**

| Field | Type | Semantics |
|---|---|---|
| `cycle_id` | string | Cycle identifier, format `BM-NNN`. BM-001 and BM-002 retired (§6.2). Sequential, no reuse. |
| `runtime_genesis_pc` | hex string (e.g., `"0x0003A19C"`) | The literal 68000 PC value the trace reports. Same coordinate space the trace uses. **This IS the file offset for the activator write** (fixed Genesis ROM-to-CPU 1:1 mapping). |
| `span_length` | integer (bytes) | Number of bytes the activator overwrites at `runtime_genesis_pc`. Must be >= 6 to hold `JMP_LONG_ABS` (6 bytes); NOP padding (`0x4E71`) fills any remainder. Recommend powers-of-2-byte multiples (4, 6, 8) for alignment. Cody picks per target. |
| `pre_insert_canonical_bytes` | hex string | The bytes currently at `runtime_genesis_pc` in the canonical baseline ROM, captured at Insert time. Used by §2.8 byte-identical revert verification (comparison reference). |
| `helper_symbol` | string | The helper to jump to. Must be in `DIAGNOSTIC_SYMBOLS` allowlist (currently `genesistan_diag_bookmark`). Postpatcher resolves to address via `out/symbol.txt`. |
| `activator_pattern` | string enum | The activator instruction pattern. `JMP_LONG_ABS` = `4EF9 <helper-address-4-bytes>` (6 bytes). Other patterns could be added later (BSR-based, etc.); only `JMP_LONG_ABS` initially supported. |
| `nop_padding_byte` | hex string | The NOP word used to fill `span_length - 6` trailing bytes. Default `0x4E71`. (Specified explicitly for diff readability and future flexibility.) |
| `pre_insert_canonical_rom_sha256` | string (64 hex chars) | SHA256 of the canonical baseline ROM before Insert. Used by §2.8 byte-identical revert verification. |
| `note` | string | Human-readable description, evidence question, target rationale. |

### §2.2 Hard lock: no `arcade_pc` field on the bookmark side

The new `bookmarks_v2` schema has NO field named `arcade_pc`. The schema is enforced by postpatcher: any field named `arcade_pc` in a `bookmarks_v2` entry is a STOP condition (`RuntimeError: bookmarks_v2 schema must not contain arcade_pc field`).

The hard lock prevents the BM-001/BM-002 fault from reoccurring: no future agent can paste a trace PC into a field labeled `arcade_pc`.

### §2.3 `opcode_replace` untouched

`opcode_replace` entries continue using the `arcade_pc` field. Its semantics (arcade-source coordinate, translated to file offset by adding `identity_offset` via `address_map.json` per Global Rule 13) are unchanged. The new `bookmarks_v2` path is purely additive.

To eliminate confusion permanently: the bookmark spec path is `bookmarks_v2` (not `diagnostic_bookmarks`). The old `diagnostic_bookmarks` field (per CLOSED-009 design) is **retired**. Postpatcher rejects any spec containing the old field name with a clear error pointing at the new schema. The old name is retained in the source-controlled history (BM-001/BM-002 design docs cite it) but is not a live spec construct.

(Andy considered keeping the `diagnostic_bookmarks` name with a revised schema. Rejected because: the old name has been used in CLOSED-009 design + Cody implementation + 13-test artifacts with a different schema. Re-using the name with a new schema would cause schema-version confusion in spec diffs and AGENTS_LOG searches. The "v2" suffix makes the change unambiguous in every project surface.)

### §2.4 Workflow population (no arithmetic)

How a Cody populates a `bookmarks_v2` entry from a trace:

1. Read trace (MAME, Exodus, or BlastEm) for a target evidence question (e.g., "is execution reaching PC X?")
2. Pick the runtime PC `X` from the trace's `pc=XXXXXXXX` field. Use the value VERBATIM — no subtraction, no lookup.
3. Read the canonical baseline ROM bytes at file offset `X` (e.g., `dd if=canonical.bin bs=1 skip=X count=span_length`) to populate `pre_insert_canonical_bytes`.
4. Compute `pre_insert_canonical_rom_sha256` over the full canonical baseline.
5. Pick `span_length` based on the target's first instruction (Cody must verify span doesn't have PC-relative ops per §6.1).
6. Write the spec entry.

Steps 2 and 3 use the verbatim trace PC. No arithmetic.

---

## §3 Deliverable 2 — post-relocation insertion stage

### §3.1 Pipeline stage placement

Per `apps/rastan-direct/Makefile:126-167`, the `$(BIN)` recipe applies these stages in order:

1. Boot guard on `$(PREPATCH_BIN)` (line 127)
2. Copy `$(PREPATCH_BIN)` → `$(BIN)` (line 128)
3. Build region files via `build_rastan_regions.py` (line 129)
4. **Postpatcher** (`tools/translation/postpatch_startup_rom.py`, line 130-136) — applies all `opcode_replace` mutations (and existing CLOSED-009 diagnostic-mode logic on `diagnostic_bookmarks`)
5. Boot guard on post-patch `$(BIN)` (line 137)
6. Generate post-patch disasm via `objdump` (line 139)
7. **Canonical gate** (`tools/translation/verify_canonical_rom.py`, line 145-158) — six existing checks plus §2.7/§2.8 from CLOSED-009
8. Increment counter, copy to numbered artifact (line 160-163)
9. MAME trace (line 164+)

**The bookmark activator byte-write happens INSIDE step 4 (the postpatcher), as a new sub-stage AFTER all `opcode_replace` mutations have been applied.** Concretely:

- Postpatcher applies `opcode_replace` entries (existing behavior).
- THEN postpatcher applies `bookmarks_v2` entries (NEW stage). For each entry, the postpatcher:
  1. Resolves `helper_symbol` to its file offset via `out/symbol.txt` (consulting `DIAGNOSTIC_SYMBOLS` allowlist).
  2. Computes activator bytes: `4E F9 <helper-address-big-endian-4-bytes>` (6 bytes for `JMP_LONG_ABS`) + `4E 71` × `((span_length - 6) / 2)` NOP padding.
  3. Writes these bytes into the ROM bytearray at file offset = `runtime_genesis_pc`. Direct overwrite. No translation. No segment lookup.
  4. Records the write in the postpatcher's per-cycle state (for state file write).

Step 5 (post-patch boot guard) runs after the activator write — this is intentional. Boot guard verifies low-ROM bootstrap bytes (`0x000004` reset vector, `0x000202` start prologue, etc.); it doesn't care about the bookmark activator at unrelated runtime PCs.

Step 7 (canonical gate) runs over the final ROM including the activator. The gate's new check (§4) verifies activator bytes are correctly placed.

### §3.2 The fixed ROM-to-CPU mapping

In Genesis: cartridge ROM is mapped starting at CPU address `0x000000`. The 68000 fetching from PC = N reads the cartridge byte at file offset N. This is fixed, 1:1, and covers all ROM regions in this project (cartridge size is `~1.6 MB`; Genesis maps cartridge up to `0x3FFFFF`).

**Therefore: runtime Genesis PC value = ROM file offset.** No translation required. This is the structural simplification the model exploits.

This contrasts with `opcode_replace`'s `arcade_pc → file offset` translation (which IS translation, adding `identity_offset`). The two models are different by design: `opcode_replace` patches translated arcade code identified in the source domain; `bookmarks_v2` patches the final ROM identified in the runtime domain.

### §3.3 Postpatcher can cleanly write at this stage

The postpatcher already maintains `rom_bytes = bytearray(rom_path.read_bytes())` (per `postpatch_startup_rom.py:965`) and writes patches into this bytearray throughout its execution. A byte-write at file offset N is `rom_bytes[N:N+span_length] = activator_bytes` — trivial. The bytearray is then written back to disk at the postpatcher's normal end-of-execution path.

No new infrastructure required — the bookmark write is one new stage inserted before the existing bytearray-flush.

### §3.4 Per-segment safety (write-target validity)

The postpatcher MUST verify the activator write stays within ROM bounds: `runtime_genesis_pc + span_length <= len(rom_bytes)`. Out-of-bounds is a STOP condition (`RuntimeError: bookmarks_v2 entry runtime_genesis_pc=X exceeds ROM bytes`).

The postpatcher SHOULD also verify the target doesn't fall in a sensitive region (e.g., not in the preserved-vectors region `0x000000..0x000400`, not in the helper region itself `[helper_address, helper_address + 2)`). Optional; can be a warning rather than STOP. Cody's call at implementation time.

---

## §4 Deliverable 3 — gate verification (mandatory)

### §4.1 New check §2.7 (replacing the old §2.7)

The gate gets a new mandatory check, designated §2.7 (re-using the slot vacated by the old activator-integrity check, which becomes obsolete per §5.6). Failure ID:

```
FAIL_2_7 = "GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES"
```

### §4.2 Procedure

```
For each entry E in bookmarks_v2:
  resolved_helper_addr = symbol_addresses[E.helper_symbol]
  span_length = E.span_length
  expected_activator_bytes = construct_activator(E.activator_pattern, resolved_helper_addr, span_length, E.nop_padding_byte)
  rom_bytes = read_rom(target_path)
  observed_bytes = rom_bytes[E.runtime_genesis_pc : E.runtime_genesis_pc + span_length]
  if observed_bytes != expected_activator_bytes:
    FAIL with GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES
      cycle_id=E.cycle_id
      runtime_genesis_pc=hex(E.runtime_genesis_pc)
      expected=hex(expected_activator_bytes)
      observed=hex(observed_bytes)
```

Where `construct_activator(pattern, addr, length, nop)`:
- For `JMP_LONG_ABS`: returns `b"\x4E\xF9" + struct.pack(">I", addr) + (b"\x4E\x71" * ((length - 6) // 2))`
- Asserts `length >= 6` and `(length - 6) % 2 == 0` (NOP word alignment)

### §4.3 Why it's mandatory, not optional

The BM-002 investigation surfaced that the old §2.7 check verified bytes at the spec's claimed offset BUT had no way to verify the offset is where the CPU actually executes — because the spec used `arcade_pc` which requires translation. With `runtime_genesis_pc`, the offset IS the runtime PC; the check verifies the bytes at the offset the CPU executes from. This is now a meaningful integrity check, not a near-tautology. Mandatory because skipping it would re-open the door to BM-002-class faults at a different layer (e.g., postpatcher bug writing to wrong offset).

### §4.4 Relation to old §2.7 (activator integrity)

The old §2.7 verified `bookmark_cycle`-tagged `opcode_replace` entries' replacement bytes at their post-translation file offsets. Under the new model, no `bookmark_cycle`-tagged opcode_replace entries exist; the old §2.7 has nothing to check. The slot is **renamed and repurposed** for the new check, not duplicated.

**Cody's implementation:** rename the old `check_activator_integrity` function (in `verify_canonical_rom.py`) to `check_bookmark_activator_bytes` (or similar); rewrite its logic to operate on `bookmarks_v2` entries; keep `FAIL_2_7` as the failure ID for continuity. Old `FAIL_2_7_ACTIVATOR_INTEGRITY` constant gets renamed to `FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES` (or kept under the old name as an alias — Cody's call; the test matrix in §5.7's re-verification will use whichever name is current).

---

## §5 Deliverable 4 — CLOSED-009 ripple walk

Every CLOSED-009 mechanism is walked individually. None is assumed unaffected.

### §5.1 Build-mode detection (canonical vs diagnostic)

**Old behavior:** `is_diagnostic = len(spec.get("diagnostic_bookmarks", [])) > 0`. Diagnostic mode also required cross-reference: every entry in `diagnostic_bookmarks` must match a `bookmark_cycle`-tagged opcode_replace entry.

**New behavior:** `is_diagnostic = len(spec.get("bookmarks_v2", [])) > 0`.

**Disposition: REVISED.** Same predicate shape (presence of bookmark entries → diagnostic mode); different spec field name; no cross-reference needed (single-entry self-contained bookmarks). Build-mode reporting strings (`"diagnostic"` / `"canonical"` / `"authorized_revert"`) unchanged in user-facing output.

### §5.2 `expected_count = canonical_count + N` invariant

**Old behavior:** Postpatcher's invariant check at `postpatch_startup_rom.py:1845-1858` does `expected_count = canonical_count; if is_diagnostic: expected_count += diagnostic_count`. Because bookmark activators lived as opcode_replace entries, each diagnostic bookmark added one opcode_replace site; the invariant accepted `94 + N`.

**New behavior:** Bookmark activators are NOT opcode_replace entries. opcode_replace count is always `94` (canonical). The `expected_count += diagnostic_count` adjustment becomes dead code under the new schema.

**Disposition: REVISED.** Remove the conditional adjustment. opcode_replace count invariant is strict canonical 94 in all build modes (canonical, diagnostic, authorized_revert). A separate (new) bookmark-count invariant tracks `bookmarks_v2` array length against the expected number of activator writes the postpatcher performed (consistency check; not strictly necessary but cheap).

### §5.3 `total_genesis_bytes_covered = canonical_coverage + Σ`

**Old behavior:** Postpatcher invariant accepted `0x17CAEC + Σ` where `Σ = sum(len(original_bytes)/2 for bookmark_cycle-tagged opcode_replace)`. Activator span lengths contributed to segment coverage.

**New behavior:** Activators are post-postpatcher direct overwrites; they are NOT part of `segment_coverage`. opcode_replace coverage stays exactly `0x17CAEC` always (in all build modes).

**Disposition: REVISED.** Remove the Σ adjustment. opcode_replace coverage invariant is strict `0x17CAEC` in all build modes. The activator bytes are real ROM mutations but are accounted for separately (postpatcher emits a `bookmarks_v2_applied` summary in the manifest listing each activator's `runtime_genesis_pc` and `span_length`; gate can sanity-check this summary against the spec).

### §5.4 `DIAGNOSTIC_SYMBOLS` allowlist

**Old behavior:** `DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)` was always merged into `symbol_addresses` so the `{symbol:genesistan_diag_bookmark}` template in opcode_replace `replacement_bytes` resolved.

**New behavior:** Bookmark activator bytes are constructed by the new postpatcher bookmark stage, NOT by the opcode_replace `{symbol:...}` template resolver. The new stage has its own helper-symbol lookup. The allowlist is consulted by the new stage: a `bookmarks_v2` entry's `helper_symbol` value must be in `DIAGNOSTIC_SYMBOLS`; otherwise STOP.

**Disposition: REVISED.** Same allowlist tuple; different consumer code path. The three-place friction governance (postpatcher source + design doc + AGENTS_LOG) for adding symbols is preserved. Cody can keep the same constant name and definition; only the resolver path changes.

### §5.5 Cross-reference consistency check

**Old behavior:** Postpatcher verified every `diagnostic_bookmarks` entry's `cycle_id` matched exactly one `bookmark_cycle`-tagged opcode_replace entry, and vice versa; verified `linked_opcode_replace_index` pointed at the correct opcode_replace array index; verified `target_arcade_pc` consistency.

**New behavior:** Bookmarks live in a single, self-contained `bookmarks_v2` array. No second location to cross-reference. The opcode_replace array has no `bookmark_cycle` field at all.

**Disposition: OBSOLETE.** The cross-reference validator (`_validate_diagnostic_bookmark_cross_references` or similar in postpatcher) is removed. Single-entry-per-cycle uniqueness within `bookmarks_v2` is still enforced (no duplicate `cycle_id` values; at most one entry per build, per Rule 10's single-cycle-in-flight constraint).

### §5.6 §2.7 activator integrity check (gate)

**Old behavior:** Gate's §2.7 verified `bookmark_cycle`-tagged opcode_replace entries had correctly resolved activator bytes at their post-translation file offsets, derived from `arcade_pc + identity_offset`.

**New behavior:** Replaced by the new §2.7 check defined in §4 above.

**Disposition: REPLACED.** Cody renames the implementation function and rewrites its logic. Failure ID retained as `FAIL_2_7` (with the descriptive name `GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES`).

### §5.7 §2.8 byte-identical revert

**Old behavior:** Gate's §2.8 verified the post-revert ROM SHA256 == `pre_insert_canonical_rom_sha256` from the state file. Used the byte-identical reversion property to confirm Rule 10's revert obligation.

**New behavior:** Same intent. Insert writes the state file (cycle_id, pre_insert_canonical_rom_sha256, pre_insert_build_counter, timestamp). Revert removes the bookmark from `bookmarks_v2`; rebuild; gate detects empty `bookmarks_v2` + state file present + explicit `--bookmark-revert BM-NNN` → authorized revert → verify ROM SHA == state's recorded SHA → delete state file.

**Disposition: UNCHANGED.** §2.8 check logic is independent of how the bookmark was represented in the spec; it only cares about ROM SHA comparison against the recorded baseline. The state file write (during Insert) and consumption (during Revert) work identically.

### §5.8 `active_bookmark_baseline.json` state-file lifecycle

**Old behavior:** Postpatcher writes the file on diagnostic Insert; gate consumes on authorized Revert; gate deletes after successful §2.8.

**New behavior:** Same lifecycle. Postpatcher's bookmark stage (§3.1 step 4) writes the state file alongside its activator-write. Same fields (cycle_id, pre_insert_canonical_rom_sha256, pre_insert_build_counter, timestamp).

**Disposition: UNCHANGED.** The state file contents are independent of the spec schema for `bookmarks_v2` vs `diagnostic_bookmarks`. The four fields stored (cycle ID, baseline SHA, baseline counter, timestamp) suffice for §2.8 regardless of spec representation.

### §5.9 Summary table

| CLOSED-009 mechanism | Disposition under new model |
|---|---|
| Build-mode detection | REVISED (new schema; same predicate) |
| `expected_count = 94 + N` invariant | REVISED (opcode_replace strict 94 always; N tracked separately) |
| `total_genesis_bytes_covered = 0x17CAEC + Σ` | REVISED (opcode_replace strict 0x17CAEC always; activator overwrites outside segment_coverage) |
| `DIAGNOSTIC_SYMBOLS` allowlist | REVISED (same allowlist; new consumer code path) |
| Cross-reference consistency check | OBSOLETE (single-entry bookmarks) |
| §2.7 activator integrity | REPLACED (new check per §4) |
| §2.8 byte-identical revert | UNCHANGED |
| `active_bookmark_baseline.json` lifecycle | UNCHANGED |

### §5.10 CLOSED-009 closure re-verification

CLOSED-009's closure rested on a 13-test matrix using the old schema. The mechanisms verified (state file lifecycle, byte-identical revert, helper integrity verification, postpatcher invariant honesty) are sound at the principle level. The SCHEMA on which those mechanisms operate is changing materially.

**Andy recommends opening OPEN-013 to track CLOSED-009 re-verification under the new schema.** The re-verification mirrors the existing 13-test matrix structure but uses `bookmarks_v2` entries instead of `diagnostic_bookmarks` + `bookmark_cycle`-tagged opcode_replace entries. Expected outcome: all 13 (or revised count) test scenarios still PASS under the new schema, including:
- Cross-reference consistency tests OBSOLETE (no longer applicable; their scenarios become "spec has stale `diagnostic_bookmarks` field" → postpatcher rejects)
- §2.7 tests rewritten for `bookmarks_v2` direct activator verification
- §2.8 tests UNCHANGED in essence
- New §3.4 tests for out-of-bounds `runtime_genesis_pc` (postpatcher STOP)
- New §2.2 tests for forbidden `arcade_pc` field in `bookmarks_v2` (postpatcher STOP)

This is sufficient ripple work to warrant a tracked issue rather than absorbing it silently into OPEN-012's closure.

---

## §6 Deliverables 5 & 7 — PC-relative screening + cycle ID retirement

### §6.1 PC-relative span-safety screening

**Criterion:** the span at `runtime_genesis_pc` (length = `span_length`) in the canonical baseline ROM must not begin with a PC-relative instruction.

**Procedure (workflow checklist for Cody at target-selection time):**

1. Read bytes from canonical baseline at file offset = `runtime_genesis_pc`, length = `span_length`.
2. Decode the FIRST instruction's opcode word.
3. Check against the PC-relative opcode patterns:
   - `41FA xxxx` / `43FA xxxx` / ... / `4FFA xxxx` — `LEA %pc@(displacement.W), %an` (16-bit displacement PC-relative LEA)
   - `41FB xx xx xx xx` / ... — LEA with extension-word PC-relative addressing
   - `4EFA xxxx` — `JMP %pc@(displacement.W)` (PC-relative jump)
   - `4EFB xx xx xx xx` — JMP with extension-word PC-relative
   - `6Bxx` series with PC-relative source modes (`xxFA`, `xxFB`) in any encoding
4. If first instruction is PC-relative: reject the target. Pick a different `runtime_genesis_pc` (perhaps the next instruction after the PC-relative one, if that doesn't span a branch target).
5. If first instruction is NOT PC-relative but a subsequent instruction in the span is: warn but allow (the JMP fires before the subsequent instruction would execute; if the JMP fails to fire, downstream behavior is undefined but the helper-not-reached signal still differentiates Outcome A from Outcome B).

**Where the check runs:** at target-selection time (Cody's pre-Insert workflow checklist), not at gate time. The gate verifies the bytes that were placed; it doesn't second-guess target selection.

**Why first-instruction is the strict cut:** the `JMP $00071C78` activator (6 bytes) overwrites the first 6 bytes of the span. If those bytes were originally a 4-byte PC-relative LEA, the LEA can't execute (it's been overwritten); the JMP runs cleanly. If the LEA is at byte 6+ of the span and the JMP fires before reaching it, no problem. If the JMP fails to fire and execution falls through NOP padding into the LEA, the LEA's PC value is now wrong (different by `span_length - 4` or similar). The strict cut on first-instruction is sufficient — subsequent PC-relative instructions are protected by the JMP-fires assumption.

**Documentation:** the screening criterion is published as a target-selection checklist in the bookmark workflow doc Cody produces after this design lands. Tighe approves before bookmarks resume.

### §6.2 Cycle ID retirement

**BM-001** (Build 0067) — RETIRED. Patched `arcade_pc 0x055948` → ROM offset `0x055B48`; CPU executes at `pc=055948` from ROM offset `0x055948` (different code). Helper-not-reached result not meaningful as evidence about arcade source `0x055948`. Evidence folder `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/` frozen as OPEN-012 evidence.

**BM-002** (Build 0069) — RETIRED. Patched `arcade_pc 0x03A19C` → ROM offset `0x03A39C`; CPU executes at `pc=03a19c` from ROM offset `0x03A19C` (delay-loop / soft-reset preamble). Helper-not-reached result reflects the address-space mismatch, not the question "is runtime PC `0x03A19C` reached." Evidence folder `dist/rastan-direct/bookmarks/build_0069_pc_0x03A19C/` frozen as OPEN-012 evidence.

**Resumption point: BM-003.** Sequential, no reuse. The first cycle under the new coordinate model picks an evidence question, populates a `bookmarks_v2` entry, builds Build 00NN (NN = next sequential build counter), expects the helper to park if the runtime PC is genuinely reached.

**Recommended first BM-003 target:** runtime PC `0x03A19C` — same trace observation that motivated BM-002. Properties:
- Provably executed (7 hits in the BM-002 trace's 30-second window).
- First instruction at file offset `0x03A19C` is `bnes 0x3a192` (`66 F4`, 2 bytes) — NOT PC-relative; passes §6.1 screening.
- 8-byte span starting at `0x03A19C` covers `bnes` + `moveal 0x0` + `moveal 0x4` — none PC-relative.
- Pre-insert canonical bytes (from Build 0070): `66f4 2e78 0000 2078 0004 4ed0` for the first 12 bytes; `span_length = 8` captures `66f4 2e78 0000 2078`.
- Expected outcome: helper park (Outcome A) on first delay-loop iteration. If Outcome A, the new model is positive-control validated. If Outcome B, deeper investigation required.

---

## §7 Surfaced ambiguities

### Ambiguity 1 — Field naming: `bookmarks_v2` vs alternatives

Andy chose `bookmarks_v2` over `diagnostic_bookmarks` (retain) or `runtime_bookmarks` or `bookmarks` (no suffix).

**Reasoning:**
- `diagnostic_bookmarks` retained-with-revised-schema risks schema-version confusion in spec diffs and AGENTS_LOG searches.
- `bookmarks_v2` is unambiguous about the schema change; the `_v2` suffix communicates "different from the v1 thing that existed."
- `runtime_bookmarks` overspecifies (couples the field name to the coordinate model rather than to the construct).
- `bookmarks` (no suffix) sets up future ambiguity if a v3 schema ever happens.

If Tighe prefers a different name, Andy can revise; the design is structurally sound regardless. Recommend `bookmarks_v2` as the working name.

### Ambiguity 2 — Whether the postpatcher should write the state file from the bookmark stage or elsewhere

Andy places the state-file write inside the postpatcher's new bookmark stage (§3.1 step 4). Alternative: write the state file from a separate Makefile-driven step.

**Reasoning:** the postpatcher is the only stage that has clean access to both the spec (for `pre_insert_canonical_rom_sha256` derivation from the `bookmarks_v2` entry) AND the build counter (for `pre_insert_build_counter`). Splitting the write across stages risks race conditions or stale data. The postpatcher is the natural single source of truth.

### Ambiguity 3 — Whether to support multiple activator patterns

Andy defines `activator_pattern: "JMP_LONG_ABS"` as an enum field with currently exactly one value. Alternative: hard-code `JMP_LONG_ABS` and don't expose it as a field.

**Reasoning:** the enum field is cheap (one extra string in each spec entry) and futures-proof for alternative patterns (e.g., BSR-based activators, hardware-jumps-to-low-memory, etc.). Tighe can decide to drop it as needless flexibility if Cody objects at implementation time.

### Ambiguity 4 — Whether out-of-arcade-copy targets are allowed

The `runtime_genesis_pc` model allows ANY file offset (cartridge size permitting). This means bookmarks can target Genesis-native code (helpers at `0x70000+`, `_bootstrap` at `0x202`, etc.), not just translated arcade code.

**Andy's interpretation: ALLOW.** Bookmarks are an instrumentation tool; they should be able to probe any code that runs on the 68000, regardless of whether it originated as arcade code. The PC-relative span-safety check applies uniformly (it screens the bytes at the target offset; the target's "kind" is irrelevant).

**Caveat:** targeting low-memory (vectors, bootstrap entry) is risky — overwriting reset vectors or the bootstrap prologue would brick the build. Recommend a postpatcher warning (not STOP) if `runtime_genesis_pc < 0x00000400` (preserved-vectors region) or `runtime_genesis_pc + span_length > 0x000F1DBC` (helper data region). Cody decides whether to gate or just warn.

---

## §8 Deliverable 4 / §7 — New OPEN issue

**Recommend opening OPEN-013.**

**Title:** "CLOSED-009 re-verification under `bookmarks_v2` schema"

**Status:** OPEN

**Priority:** HIGH

**Discovered by:** Andy (OPEN-012 design walk of CLOSED-009 ripple)

**Observed in build/artifact:** N/A — re-verification work, not a regression

**Summary:** CLOSED-009 (postpatch invariant model + diagnostic symbol allowlist + gate context-awareness) was verified end-to-end against the `diagnostic_bookmarks` + `bookmark_cycle`-tagged opcode_replace schema. The OPEN-012 design replaces that schema with a separate `bookmarks_v2` path. The CLOSED-009 mechanisms (build-mode detection, count invariant, coverage invariant, allowlist consumer, cross-reference, §2.7, §2.8, state file) are revised, replaced, obsoleted, or unchanged per `Andy_OPEN012_bookmark_coordinate_model_design.md` §5. End-to-end re-verification on the new schema mirrors the CLOSED-009 13-test matrix structure but uses the new spec construct.

**Evidence:** `docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md` §5 (CLOSED-009 ripple walk).

**Suspected area:** `tools/translation/postpatch_startup_rom.py` (bookmark stage; invariant reversion), `tools/translation/verify_canonical_rom.py` (new §2.7; obsolete cross-reference removal), spec format documentation.

**Next required task:** Cody implements OPEN-012 design (postpatcher + gate edits + spec format). Then Cody runs the re-verification test matrix on the new schema (analog of CLOSED-009 13-test matrix). Tighe verifies.

**Closure condition:** new schema's test matrix passes end-to-end including a positive-control BM-003 cycle producing Outcome A (helper park).

**Cross-references:** OPEN-012 (parent; OPEN-012 closure requires OPEN-013 closure); CLOSED-009 (substrate being re-verified); Rule 10 + helper design (unchanged); CLOSED-008 determinism gate (gate's §2.7 slot reused).

---

## §9 Implementation summary (Cody implements after this design lands)

### §9.1 Spec schema changes (`specs/rastan_direct_remap.json`)

- Add top-level `bookmarks_v2` array (empty in canonical state).
- Remove `diagnostic_bookmarks` field (was empty in canonical state already; no live entries).
- Existing `opcode_replace` array unchanged.

### §9.2 Postpatcher changes (`tools/translation/postpatch_startup_rom.py`)

- Add new `_apply_bookmarks_v2` stage after `opcode_replace` application.
- Validate each `bookmarks_v2` entry's schema (no `arcade_pc` field, `helper_symbol` in `DIAGNOSTIC_SYMBOLS`, `runtime_genesis_pc + span_length <= len(rom_bytes)`, `span_length >= 6` and `(span_length - 6) % 2 == 0`).
- Construct activator bytes (`4EF9 <addr> 4E71...`); write into `rom_bytes` at file offset = `runtime_genesis_pc`.
- Write `active_bookmark_baseline.json` state file (cycle_id, pre_insert_canonical_rom_sha256, pre_insert_build_counter, timestamp).
- Revert invariant: `opcode_replace count` strict `94` always; `total_genesis_bytes_covered` strict `0x17CAEC` always (remove `+ N` / `+ Σ` conditional adjustments per §5.2 / §5.3).
- Reject specs containing legacy `diagnostic_bookmarks` field with a clear error.

### §9.3 Gate changes (`tools/translation/verify_canonical_rom.py`)

- Rename `check_activator_integrity` → `check_bookmark_activator_bytes`; rewrite to operate on `bookmarks_v2` entries per §4.2.
- Remove `_validate_diagnostic_bookmark_cross_references` (obsolete per §5.5).
- §2.8 byte-identical revert: unchanged.
- State-file truth-table resolver: unchanged in logic; spec-field name in mode-detection switches from `diagnostic_bookmarks` to `bookmarks_v2`.

### §9.4 Test matrix re-run (per OPEN-013)

Cody re-runs the CLOSED-009 test matrix adapted to the new schema:
- Tests 1-3 (positive control / no-bookmark / Insert / Revert): adapted for new schema; expected to pass identically.
- Tests 4-10 (state-context failure modes): adapted; mode-detection now keys off `bookmarks_v2` not `diagnostic_bookmarks`.
- Tests 11-12 (§2.7 activator integrity, §2.8 byte-identical): rewritten for new check semantics.
- New tests for: out-of-bounds `runtime_genesis_pc`; forbidden `arcade_pc` field in bookmarks_v2; legacy `diagnostic_bookmarks` field rejection.

### §9.5 Positive-control re-issue (BM-003)

After implementation and test-matrix re-run pass:
- Cody (or Tighe) authors BM-003 entry targeting runtime PC `0x03A19C` (positive control — same target BM-002 intended, corrected coordinates).
- Build executes diagnostic path; gate's new §2.7 passes; ROM produced as Build 00NN diagnostic.
- MAME trace expected to show helper park (Outcome A) — confirms mechanism validity.
- BM-003 Revert produces Build 00NN+1 byte-identical to pre-Insert canonical baseline; §2.8 passes.
- OPEN-012 closure: positive-control Outcome A confirmed.
- OPEN-013 closure: re-verification matrix passed.
- BM-001's original evidence question (was runtime PC `0x055948` reached?) becomes investigable via a fresh BM-004 cycle.

---

## Phase 10 Integrity

- Phase 1 `identity_offset` semantics settled with cited address_map.json data: YES — global constant `0x200` for all 75 `arcade_copy` segments
- Phase 2 `runtime_genesis_pc` (specifically `bookmarks_v2`) spec path specified, separate from `opcode_replace`, no `arcade_pc` field: YES — §2 with 9-field schema; §2.2 hard lock; §2.3 confirms opcode_replace untouched
- Phase 3 post-relocation insertion stage named concretely: YES — new `_apply_bookmarks_v2` stage inside postpatcher (between opcode_replace application and bytearray flush); fixed ROM-to-CPU mapping cited
- Phase 4 mandatory gate check specified with failure ID: YES — `GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES`; procedure in §4.2; mandatory per §4.3
- Phase 5 every CLOSED-009 mechanism walked individually: YES — 8 mechanisms in §5.1-§5.8 with REVISED/OBSOLETE/REPLACED/UNCHANGED dispositions; summary table §5.9
- Phase 6 PC-relative screening specified + cycle IDs retired: YES — §6.1 (first-instruction screening criterion + procedure); §6.2 (BM-001/BM-002 retired; BM-003 next)
- Phase 7 new OPEN issue decision documented: YES — OPEN-013 recommended (§8)
- All 8 deliverables resolved with cited evidence: YES (1: §2; 2: §3; 3: §4; 4: §5; 5: §6.1; 6: §1; 7: §6.2; 8: §2.2-§2.3)
- No implementation / no builds / no ROM or evidence modifications: YES
- Coordinate model specified (not re-deliberated): YES
- Ambiguities surfaced: 4 (§7) with chosen interpretations
- All STOP conditions either passed or documented: YES (no STOP triggered)
