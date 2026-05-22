# Andy — Diagnostic Bookmark Postpatch Invariant Design

**Agent:** Andy (Claude Code)
**Type:** Design (analytical only — no implementation, no source/spec/tool/Makefile/build/ROM modifications)
**Build:** rastan-direct, post-BM-001-Insert-STOP (canonical baseline `dist/rastan-direct/rastan_direct_video_test_build_0062.bin`, SHA256 `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Date:** 2026-05-12
**Naming:** descriptive output filename per OPEN-002 extended policy
**Scope:** extend `Andy_diagnostic_bookmark_helper_design.md` to resolve the two postpatcher invariant conflicts surfaced by Cody's BM-001 STOP. Make canonical-build invariants context-aware so diagnostic builds work without weakening protections.

---

## 0. Executive verdict

**Philosophy:** canonical builds remain strictly canonical; diagnostic builds get context-aware treatment; protections are never globally weakened.

**Two non-negotiable design constraints from the prompt are upheld:**
1. Canonical invariant (`patched_site == 94`, `total_genesis_bytes_covered == 0x17CAEC`) remains strict for canonical builds. The invariant becomes context-aware, not optional.
2. `required_symbols` allowlist remains principled. Diagnostic symbol references are allowed only for explicitly approved symbols (initially `genesistan_diag_bookmark`). Arbitrary symbol references remain forbidden.

**Core mechanism: a single new top-level spec field `diagnostic_bookmarks` distinguishes canonical from diagnostic builds.**

- When `diagnostic_bookmarks` is absent or empty → build is **canonical** → existing invariants enforced unchanged
- When `diagnostic_bookmarks` is non-empty → build is **diagnostic** → context-aware invariants computed from the array's contents

Each entry in `diagnostic_bookmarks` carries the cycle ID, target address, pre-insert canonical bytes, and pre-insert canonical ROM SHA256. Each corresponding opcode_replace entry carries a matching `bookmark_cycle: "BM-NNN"` field for self-identification. Activator format remains exactly as Andy's prior helper design specified: `replacement_bytes = "4EF9{symbol:genesistan_diag_bookmark}<NOP padding>"`.

**Approved diagnostic symbols:** a hardcoded tuple `DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)` in postpatcher source, governed by Rule 10 amendment friction (postpatcher source edit + AGENTS_LOG entry + helper design revision). Diagnostic symbols are always-resolvable regardless of spec's `required_symbols`. Adding a new diagnostic symbol is a three-place change.

**Gate behavior:** §2.1, §2.2, §2.4, §2.6 unchanged across both build modes. §2.3 delegates to postpatcher's context-aware invariant. §2.5 acquires a diagnostic symbol resolution check. Two new diagnostic-only checks: §2.7 activator integrity (verifies activator bytes embed correctly resolved helper address) and §2.8 byte-identical revert (verifies BM-N Revert produces a ROM SHA-identical to the canonical baseline that preceded BM-N Insert).

**Cycle lifecycle:**
- BM-N Insert produces a diagnostic build (sequential number per OPEN-002, no letter suffix). Diagnostic builds are NOT canonical baselines.
- BM-N Revert produces a canonical build SHA-identical to the pre-Insert canonical baseline. The revert build becomes the new canonical baseline.

**Out of scope (Cody implementation work after this design lands):** postpatcher edit (DIAGNOSTIC_SYMBOLS tuple + context-aware invariant), gate edit (§2.5 diagnostic resolution + new §2.7/§2.8), spec format documentation update, BM-001 retry end-to-end through the new system.

---

## §1 Current state model (cited evidence)

### §1.1 Postpatcher `required_symbols` mechanism

Per [`tools/translation/postpatch_startup_rom.py:906-912`](tools/translation/postpatch_startup_rom.py#L906-L912):

```python
required_symbols = tuple(spec.get("required_symbols", []))
```

The list comes from `specs/rastan_direct_remap.json` (spec-driven). Line 964 then constructs `symbol_addresses = parse_symbol_table(symbols_path, required_symbols)` — only symbols in this allowlist are resolvable for `{symbol:NAME}` template substitution.

Effect: any opcode_replace entry that references a symbol NOT in `required_symbols` triggers `RuntimeError: Replacement references missing symbol: <NAME>`. This is what BM-001 hit: `genesistan_diag_bookmark` is in `out/symbol.txt` but not in `required_symbols`, so resolution fails.

This is a legitimate trust mechanism. Without it, any symbol exported by the link step could be referenced by spec entries, which would defeat the purpose of explicit symbol declaration. The allowlist forces deliberate addition.

### §1.2 Postpatcher count + coverage invariant

Per [`tools/translation/postpatch_startup_rom.py:1756-1766`](tools/translation/postpatch_startup_rom.py#L1756-L1766):

```python
if (
    int(segment_coverage["total_genesis_bytes_covered"]) != 0x17CAEC
    or len(opcode_replace_sites) != 94
):
    raise RuntimeError(
        "Build 0029 invariant failure: ..."
    )
```

Hardcoded values updated historically via documented comment block at lines 1737-1755 each time the project intentionally added/removed opcode_replace entries or changed wrapper-byte coverage. Current baseline (`94`, `0x17CAEC`) corresponds to Build 0061+ post-helper-introduction state.

Effect: any build with `len(opcode_replace_sites) != 94` triggers the invariant failure. This is what BM-001 hit: adding a bookmark activator brings the count to 95.

This is the second legitimate trust mechanism. The count invariant catches silent spec growth (anyone adding a spec entry without updating the invariant gets caught immediately). Disabling it globally would reopen the silent-growth attack surface.

### §1.3 Gate delegation to postpatcher (§2.3)

Per [`Andy_build_pipeline_determinism_gate_design.md`](docs/design/Andy_build_pipeline_determinism_gate_design.md) §2.3, the gate delegates structural invariant verification to the postpatcher. The gate's §2.3 check is satisfied implicitly: if the gate runs at all (Makefile recipe step after postpatcher), the postpatcher must have passed. This delegation keeps the gate orthogonal to postpatcher concerns.

This delegation is correct in principle. The conflict is that the postpatcher's check is build-context-agnostic; it doesn't know whether the build is canonical or diagnostic.

### §1.4 Activator representation from prior helper design

Per [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.3:

```json
{
  "arcade_pc": "0xXXXXXX",
  "original_bytes": "<canonical bytes at target>",
  "replacement_bytes": "4EF9{symbol:genesistan_diag_bookmark}<NOP padding>",
  "note": "DIAGNOSTIC BOOKMARK ACTIVATOR — ..."
}
```

This format is byte-correct (Cody's BM-001 attempt produced valid bytes at the target). The activator's `note` field is informational. The conflict surfaces only at postpatcher invariant time.

---

## §2 Build context distinction mechanism

### §2.1 The `diagnostic_bookmarks` spec field

A new top-level field is added to `specs/rastan_direct_remap.json`:

```json
{
  "version": 1,
  ...existing fields...,
  "diagnostic_bookmarks": [
    {
      "cycle_id": "BM-001",
      "target_arcade_pc": "0x055948",
      "pre_insert_canonical_bytes": "0c6d000010a8660a",
      "pre_insert_canonical_rom_sha256": "72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc",
      "linked_opcode_replace_index": <integer>
    }
  ]
}
```

**Behavior:**
- **Absent or empty array:** build is **canonical**. All existing invariants apply unchanged.
- **Non-empty array:** build is **diagnostic**. Context-aware invariants apply.

**Why top-level rather than nested under `policy`:** discoverability. Top-level fields are visible in cursory spec inspection. Nesting under `policy` risks the field being missed in reviews. The spec already has top-level `version`, `scope`, `policy`, `direct_execution`, `whole_maincpu_copy`, etc.; adding `diagnostic_bookmarks` at top-level matches existing convention.

**Field semantics:**
- `cycle_id`: matches the corresponding opcode_replace entry's `bookmark_cycle` field; matches AGENTS_LOG cycle identifier
- `target_arcade_pc`: matches the opcode_replace entry's `arcade_pc`
- `pre_insert_canonical_bytes`: hex string of the bytes that were at the target in the canonical baseline before Insert; matches the opcode_replace entry's `original_bytes` (consistency check)
- `pre_insert_canonical_rom_sha256`: SHA256 of the canonical baseline ROM (e.g., Build 0062) captured at Insert time; used by §2.8 revert verification
- `linked_opcode_replace_index`: zero-based index into the spec's `opcode_replace` array for the matching activator entry; postpatcher and gate use this for consistency checks

### §2.2 Activator entry self-identification

Each bookmark activator in the spec's `opcode_replace` array carries an extra field:

```json
{
  "arcade_pc": "0x055948",
  "original_bytes": "0c6d000010a8660a",
  "replacement_bytes": "4EF94EF94E714E714E71",
  "note": "DIAGNOSTIC BOOKMARK ACTIVATOR — BM-001 — ...",
  "bookmark_cycle": "BM-001"
}
```

(The `replacement_bytes` value above is illustrative; actual content uses `{symbol:genesistan_diag_bookmark}` plus NOP padding to fill the 8-byte span.)

The `bookmark_cycle` field is the entry's self-identification:
- Postpatcher uses it to compute N (count of bookmark activators) and Σ (sum of span lengths)
- Gate uses it for §2.7 activator integrity verification
- Reviewers grep for `bookmark_cycle` to spot all active activators in spec diffs

**Consistency rule:** every opcode_replace entry with `bookmark_cycle: "BM-NNN"` must have a matching entry in `diagnostic_bookmarks` with the same `cycle_id`. Conversely, every entry in `diagnostic_bookmarks` must reference (via `linked_opcode_replace_index`) an opcode_replace entry with the same cycle ID. Mismatch is a postpatcher error.

### §2.3 Why this mechanism is hard to bypass

- The spec field is version-controlled; spec diffs show its presence and contents clearly
- The activator entry self-identifies via `bookmark_cycle`; visual review of diffs catches activators
- The two structures cross-reference (consistency rule); a malformed spec triggers postpatcher error
- The mechanism is read by BOTH postpatcher AND gate; both check context and apply context-aware behavior
- A canonical build with `diagnostic_bookmarks` accidentally non-empty (e.g., forgotten cleanup) would be classified diagnostic, producing a non-canonical ROM — visible to anyone using it as baseline

---

## §3 Context-aware count invariant

### §3.1 Formula

Define:
- `canonical_count = 94`
- `canonical_coverage = 0x17CAEC`
- `N = len(diagnostic_bookmarks)`
- `Σ = sum(len(original_bytes) / 2 for each opcode_replace entry with bookmark_cycle field set)` (in bytes, since `original_bytes` is a hex string with 2 hex chars per byte)

**Canonical build expected invariants:**
- `patched_site count == canonical_count` (94)
- `total_genesis_bytes_covered == canonical_coverage` (`0x17CAEC`)

**Diagnostic build expected invariants:**
- `patched_site count == canonical_count + N`
- `total_genesis_bytes_covered == canonical_coverage + Σ`

### §3.2 Validation logic

Postpatcher pseudocode (Cody implements):

```python
diagnostic_bookmarks = spec.get("diagnostic_bookmarks", [])
is_diagnostic = len(diagnostic_bookmarks) > 0

if is_diagnostic:
    bookmark_activators = [
        site for site in opcode_replace_sites
        if site.get("bookmark_cycle") is not None
    ]
    if len(bookmark_activators) != len(diagnostic_bookmarks):
        raise RuntimeError(
            f"Diagnostic build consistency failure: "
            f"diagnostic_bookmarks has {len(diagnostic_bookmarks)} entries but "
            f"opcode_replace has {len(bookmark_activators)} bookmark_cycle-tagged entries."
        )
    # Cross-reference each entry
    for db in diagnostic_bookmarks:
        cycle_id = db["cycle_id"]
        matching = [a for a in bookmark_activators if a.get("bookmark_cycle") == cycle_id]
        if len(matching) != 1:
            raise RuntimeError(
                f"Diagnostic build consistency failure: "
                f"diagnostic_bookmarks entry {cycle_id} has {len(matching)} matching opcode_replace entries; expected exactly 1."
            )
    Σ = sum(len(a["original_bytes"]) // 2 for a in bookmark_activators)
    N = len(bookmark_activators)
    expected_count = canonical_count + N
    expected_coverage = canonical_coverage + Σ
else:
    # Canonical build: existing invariant
    expected_count = canonical_count       # 94
    expected_coverage = canonical_coverage  # 0x17CAEC

if (
    int(segment_coverage["total_genesis_bytes_covered"]) != expected_coverage
    or len(opcode_replace_sites) != expected_count
):
    raise RuntimeError(
        f"Build 0029 invariant failure: expected "
        f"total_genesis_bytes_covered=0x{expected_coverage:X} and "
        f"opcode_replace patched_site count={expected_count}; got "
        f"total_genesis_bytes_covered=0x{int(segment_coverage['total_genesis_bytes_covered']):X} "
        f"opcode_replace patched_site count={len(opcode_replace_sites)}. "
        f"build_context={'diagnostic' if is_diagnostic else 'canonical'}."
    )
```

**Why compute Σ rather than store it statically:** the opcode_replace entries are already authoritative for span sizes. Adding a static `expected_coverage_delta` field to `diagnostic_bookmarks` would create a second source that could drift. Computing from the authoritative source (the opcode_replace entry's `original_bytes`) is self-consistent.

**Why preserve `canonical_count`/`canonical_coverage` as hardcoded constants:** they encode the "real" canonical baseline that the project commits to. Diagnostic adjustments are additive deltas; the baseline itself is not negotiable per build. Future legitimate canonical changes (new helper, new production patch) update these constants via the existing documented edit pattern at [`postpatch_startup_rom.py:1737-1755`](tools/translation/postpatch_startup_rom.py#L1737-L1755).

---

## §4 Approved diagnostic symbol allowlist

### §4.1 The DIAGNOSTIC_SYMBOLS tuple

A new module-level constant in [`tools/translation/postpatch_startup_rom.py`](tools/translation/postpatch_startup_rom.py):

```python
# DIAGNOSTIC_SYMBOLS — symbols that are always resolvable for {symbol:NAME} template substitution,
# independent of the spec's required_symbols allowlist.
#
# Adding a new symbol to this tuple requires:
#   1. A Rule 10 (or successor) amendment justifying the diagnostic role
#   2. A design doc revision documenting the symbol's purpose
#   3. An AGENTS_LOG entry recording the addition
# This three-place friction prevents silent expansion. Do NOT add symbols here speculatively.
#
# Current entries:
#   - genesistan_diag_bookmark: Rule 10 bookmark helper (see docs/design/Andy_diagnostic_bookmark_helper_design.md)
DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)
```

### §4.2 How it integrates with `required_symbols`

Postpatcher behavior (pseudocode):

```python
required_symbols = tuple(spec.get("required_symbols", []))
# ... existing required_symbols filtering (lines 906-912) unchanged ...

all_symbol_addresses = parse_symbol_table(symbols_path, required_names=None)
required_addrs = parse_symbol_table(symbols_path, required_symbols)

# Diagnostic symbols are always available, regardless of spec
diagnostic_addrs = {
    name: all_symbol_addresses[name]
    for name in DIAGNOSTIC_SYMBOLS
    if name in all_symbol_addresses
}
symbol_addresses = {**required_addrs, **diagnostic_addrs}
```

Effect: `{symbol:genesistan_diag_bookmark}` resolves whether or not `genesistan_diag_bookmark` is in `required_symbols`. Other symbols still require `required_symbols` membership.

If a diagnostic symbol is missing from `out/symbol.txt` (e.g., helper was removed from build), `diagnostic_addrs` skips it; downstream template resolution then fails with the existing error message. This is the correct behavior: the helper must be linked into the ROM for diagnostic builds to work.

### §4.3 Why hardcoded, not spec-driven

Spec-driven `approved_diagnostic_symbols` would let activator spec entries effectively allowlist their own symbols — anti-pattern. Hardcoded matches the helper SHA's three-place friction model: changes require postpatcher source edit, design doc revision, and AGENTS_LOG entry. Silent expansion is impossible.

### §4.4 Governance for future additions

Adding a new diagnostic symbol (e.g., a future Rule 11 immutable helper) requires:
1. **Rule amendment** that introduces the new helper and specifies its immutability
2. **Design doc revision** documenting the helper's bytes, address, SHA, and diagnostic role (analogous to `Andy_diagnostic_bookmark_helper_design.md`)
3. **Postpatcher source edit** adding the symbol to `DIAGNOSTIC_SYMBOLS` tuple with comment-block update
4. **AGENTS_LOG entry** documenting the addition

This three-place change (rule + design + source) plus AGENTS_LOG cross-reference makes additions deliberate. The pattern matches the helper-SHA three-place friction documented in [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.4.

---

## §5 Insert / Revert lifecycle

### §5.1 BM-N Insert task

**Preconditions:**
- The most recent canonical baseline is identified (e.g., Build 0062, SHA `72f9f33d...`)
- The bookmark target arcade_pc is decided (e.g., `0x055948`)
- The original bytes at the target in the canonical baseline are captured (from spec's existing opcode_replace entry if production-patched, or from the canonical ROM at the resolved offset otherwise)
- This design has landed and Tighe has approved

**Spec edits (all in a single insert task, no other unrelated changes):**

1. **Add `diagnostic_bookmarks` array entry** (top-level field; create the array if absent):
   ```json
   "diagnostic_bookmarks": [
     {
       "cycle_id": "BM-001",
       "target_arcade_pc": "0x055948",
       "pre_insert_canonical_bytes": "0c6d000010a8660a",
       "pre_insert_canonical_rom_sha256": "72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc",
       "linked_opcode_replace_index": <integer>
     }
   ]
   ```

2. **Add opcode_replace activator entry** at `target_arcade_pc` with `bookmark_cycle` field:
   ```json
   {
     "arcade_pc": "0x055948",
     "original_bytes": "0c6d000010a8660a",
     "replacement_bytes": "4EF9{symbol:genesistan_diag_bookmark}4E71",
     "note": "DIAGNOSTIC BOOKMARK ACTIVATOR — BM-001 — reverts in immediately-following ROM-producing build per Rule 10. Evidence question: <question>.",
     "bookmark_cycle": "BM-001"
   }
   ```

   `replacement_bytes` total span equals `len(original_bytes)/2 = 8 bytes`. `4EF9` is the 6-byte JMP absolute long opcode; `{symbol:...}` is 4 bytes resolved at postpatch; combined = 6 bytes; +2 NOP bytes (`4E71`) to fill the 8-byte span.

3. **If a production entry already exists at this `arcade_pc`:** comment it out in the spec (suspend). The activator entry replaces it for the diagnostic build. On Revert, the suspended entry is restored.

   Whether `0x055948` has an existing production entry: per the source disassembly, `0x055948` is a dispatcher inside the arcade ROM range that's not currently patched. (Cody confirms via spec search at Insert time.) If no production entry exists, no suspension is needed.

4. **Update `linked_opcode_replace_index`** in the `diagnostic_bookmarks` entry to point at the new activator's array index in `opcode_replace`.

**Build:**
- Run `make`. Postpatcher detects `diagnostic_bookmarks` non-empty → diagnostic mode → context-aware invariant check (expected = 95 sites, `0x17CAF4` coverage; assuming Σ = 8 for BM-001).
- Gate runs. §2.1, §2.2, §2.4, §2.6 unchanged. §2.3 trusts postpatcher. §2.5 verifies all references resolve (including diagnostic symbol). New §2.7 verifies activator bytes at target embed correctly resolved helper address. §2.8 skipped (this is Insert, not Revert).
- Sequential ROM produced (e.g., Build 0063 = BM-001 Insert).

**AGENTS_LOG entry per template from [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.5 "Insert task entry"** with one additional field: `pre_insert_canonical_rom_sha256` (used by Revert verification).

### §5.2 BM-N Revert task

**Preconditions:**
- BM-N Insert produced a diagnostic ROM (Build N_insert) immediately prior
- This task is the **immediately-following ROM-producing build** per Rule 10's revert obligation; the clock measures ROM-producing builds (per Rule 10 explicit text)
- The `pre_insert_canonical_rom_sha256` from the Insert is known (recorded in AGENTS_LOG Insert entry)

**Spec edits:**

1. **Remove the activator opcode_replace entry** (the one with `bookmark_cycle: "BM-N"`)
2. **Remove the `diagnostic_bookmarks` array entry** for "BM-N"; if the array becomes empty, the field may be removed or left as an empty array (both classify as canonical)
3. **If a production entry was suspended on Insert, restore it** (uncomment) — must be byte-for-byte identical to its pre-Insert content

**Build:**
- Run `make`. Postpatcher detects `diagnostic_bookmarks` empty → canonical mode → canonical invariants enforced (94 sites, `0x17CAEC`).
- Gate runs in canonical mode. §2.1-§2.6 standard. §2.7 skipped (no diagnostic activators). NEW §2.8 ACTIVATES: verifies post-revert ROM SHA256 == pre-insert canonical baseline SHA256.
- Sequential ROM produced (e.g., Build 0064 = BM-001 Revert).

**§2.8 byte-identical revert check:**
- The build counter is in the filename, not the ROM bytes; therefore the post-revert ROM should be byte-identical to the pre-Insert canonical baseline.
- §2.8 reads `pre_insert_canonical_rom_sha256` from the most-recent `diagnostic_bookmarks` cycle's AGENTS_LOG entry (or, if Cody prefers, from a transient state file stored during Insert and consumed during Revert).
- §2.8 computes SHA256 of the post-revert ROM; compares to the recorded baseline SHA; mismatch → STOP.

**Why byte-identical (not just predicate-equivalent):** Rule 10's "byte-verified against canonical ROM" specifies byte-level comparison. Predicate equivalence (same checks pass) is weaker than byte equality. Byte equality is the tighter contract and the one Rule 10 implies. Any divergence from byte-identical means the revert was imperfect (extra spec edit slipped in, NOP padding chose different bytes, etc.) and the build is suspect.

**Build 0064 becomes the new canonical baseline.** Subsequent canonical builds compare against Build 0064 (which == Build 0062 by SHA).

### §5.3 Cycle constraints (per Rule 10)

- **One bookmark cycle in flight at any time.** `diagnostic_bookmarks` array has at most one entry. (Spec-level enforcement: postpatcher rejects multi-entry arrays. Cody implementation choice.)
- **Insert and Revert are scoped tasks.** No other source/spec/tool/build change in either task.
- **Revert is the immediately-following ROM-producing build after Insert.** Sequential build numbers measured in ROM-producing builds (per Rule 10 explicit text). Non-ROM tasks between Insert and Revert do not satisfy the revert obligation.

---

## §6 Gate behavior per check

### §6.1 Per-check matrix

| Check | Canonical build | Diagnostic build (Insert) | Diagnostic build (Revert) |
|---|---|---|---|
| §2.1 `.incbin` byte-match | enforce | enforce | enforce |
| §2.2 helper integrity | enforce | enforce | enforce |
| §2.3 postpatcher invariants | canonical (94, 0x17CAEC) | context-aware (94+N, 0x17CAEC+Σ) | canonical (94, 0x17CAEC) |
| §2.4 ROM naming | sequential, no suffix | sequential, no suffix | sequential, no suffix |
| §2.5 symbol resolution | only references present in spec | adds DIAGNOSTIC_SYMBOLS resolution check | only references present in spec (same as canonical) |
| §2.6 `.incbin` Makefile audit | enforce | enforce | enforce |
| §2.7 activator integrity | skip (no activators) | enforce | skip (activators removed) |
| §2.8 byte-identical revert | skip | skip | enforce |

### §6.2 §2.5 diagnostic symbol resolution check

When `diagnostic_bookmarks` is non-empty, §2.5 additionally verifies:
- Every `cycle_id` in `diagnostic_bookmarks` matches exactly one opcode_replace entry's `bookmark_cycle` field
- Every opcode_replace entry's `bookmark_cycle` field matches exactly one `diagnostic_bookmarks` entry's `cycle_id`
- For each pair, `linked_opcode_replace_index` points at the correct array index
- For each activator, `genesistan_diag_bookmark` resolves to an address in `out/symbol.txt`, and that address falls within ROM bounds

### §6.3 §2.7 activator integrity (new)

Runs only when `diagnostic_bookmarks` non-empty.

```
For each entry E in diagnostic_bookmarks:
  Get A = the opcode_replace entry at index E.linked_opcode_replace_index
  Verify A.bookmark_cycle == E.cycle_id
  Verify A.arcade_pc == E.target_arcade_pc
  Verify A.original_bytes == E.pre_insert_canonical_bytes
  Compute resolved_helper_addr = symbol_addresses["genesistan_diag_bookmark"]
  Construct expected_activator_bytes = "4EF9" + big-endian-4-byte(resolved_helper_addr) + NOP padding to len(A.original_bytes)
  Read ROM at offset (A.arcade_pc translated to ROM offset, accounting for whole_maincpu copy +0x200)
  Compare ROM bytes to expected_activator_bytes
  Mismatch → STOP with diagnostic ID GATE_FAIL_2_7_ACTIVATOR_BYTES
```

### §6.4 §2.8 byte-identical revert (new)

Runs only when the current spec has empty `diagnostic_bookmarks` AND the previous build's AGENTS_LOG indicates a bookmark cycle Insert just occurred (i.e., this build is a Revert).

How Revert detection works: Cody chooses the mechanism. Options:
- (a) Read most-recent AGENTS_LOG entries for Insert marker; if found, this build is a Revert
- (b) Transient state file written by Insert, consumed by Revert
- (c) Explicit Makefile target or build flag

Andy recommends (b) — a simple state file `build/rastan-direct/active_bookmark_baseline.json` storing the `pre_insert_canonical_rom_sha256` is written by postpatcher during Insert, read by gate during Revert. The file is removed on successful Revert. State file presence + empty `diagnostic_bookmarks` = Revert build.

```
If active_bookmark_baseline.json exists AND diagnostic_bookmarks empty:
  Read recorded_baseline_sha from file
  Compute current_rom_sha = SHA256(current_rom_bytes)
  If current_rom_sha != recorded_baseline_sha:
    STOP with diagnostic ID GATE_FAIL_2_8_REVERT_BYTE_MISMATCH
  Remove active_bookmark_baseline.json
```

---

## §7 Formal definitions

### §7.1 Canonical build

A ROM build whose spec has empty or absent `diagnostic_bookmarks`. The build:
- Passes the six gate checks (§2.1-§2.6) per [`Andy_build_pipeline_determinism_gate_design.md`](docs/design/Andy_build_pipeline_determinism_gate_design.md)
- Passes postpatcher canonical invariant (94, 0x17CAEC)
- Is suitable as a baseline for any downstream work (bookmark cycles, evidence collection, further builds)
- Examples: Build 0061, Build 0062, Build 0064 (post-BM-001-Revert)

### §7.2 Diagnostic build

A ROM build whose spec has non-empty `diagnostic_bookmarks`. The build:
- Passes the six gate checks PLUS §2.7 activator integrity
- Passes postpatcher context-aware invariant (94+N, 0x17CAEC+Σ)
- Is suitable for diagnostic evidence collection (bookmark cycle observation in MAME/Exodus)
- Is **NOT** suitable as a baseline for downstream canonical work
- Examples: Build 0063 (BM-001 Insert, after this design lands and is implemented)

### §7.3 Canonical baseline

The most recent canonical build. Used by §2.8 as the SHA reference for Revert verification. Updated on every successful canonical build.

### §7.4 Revert-to-canonical

A Revert task produces a canonical build (per §7.1) byte-identical to the canonical baseline that preceded the corresponding Insert. Byte-identicalness is enforced by §2.8.

### §7.5 Cycle integrity invariant

For any complete bookmark cycle BM-N:
- BM-N Insert produces diagnostic build `D_N`
- BM-N Revert produces canonical build `C_revert_N`
- `SHA256(C_revert_N) == SHA256(C_baseline_pre_N)` where `C_baseline_pre_N` is the canonical baseline before BM-N Insert

If this invariant fails, BM-N cycle is invalid. Subsequent bookmark cycles cannot proceed until the discrepancy is resolved (either by re-Reverting or by investigating spec corruption).

---

## §8 Implementation summary (Cody implements after this design lands)

### §8.1 Postpatcher changes (`tools/translation/postpatch_startup_rom.py`)

1. Add module-level `DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)` constant with documented comment block
2. Merge `DIAGNOSTIC_SYMBOLS` addresses into `symbol_addresses` dict (around line 964)
3. Read `diagnostic_bookmarks` from spec
4. Compute context-aware `expected_count` and `expected_coverage`
5. Update invariant error message to include `build_context` label
6. Add cross-reference consistency check (cycle_id matching between `diagnostic_bookmarks` and opcode_replace entries)
7. On diagnostic build (Insert path), write `build/rastan-direct/active_bookmark_baseline.json` with `pre_insert_canonical_rom_sha256` from the diagnostic_bookmarks entry

### §8.2 Gate changes (`tools/translation/verify_canonical_rom.py`)

1. Read `diagnostic_bookmarks` from spec to determine `is_diagnostic`
2. §2.5: when `is_diagnostic`, add diagnostic symbol resolution + cross-reference consistency checks
3. §2.7: new check; runs only when `is_diagnostic`; verifies activator bytes per §6.3 procedure
4. §2.8: new check; runs only when `is_diagnostic == false` AND `active_bookmark_baseline.json` exists; verifies byte-identical revert per §6.4 procedure
5. Add new failure IDs: `GATE_FAIL_2_5_DIAGNOSTIC_CROSS_REFERENCE`, `GATE_FAIL_2_7_ACTIVATOR_BYTES`, `GATE_FAIL_2_8_REVERT_BYTE_MISMATCH`

### §8.3 Spec format documentation

Update inline comments in `specs/rastan_direct_remap.json` (or accompanying README if one exists) to document:
- `diagnostic_bookmarks` field structure
- `bookmark_cycle` field on opcode_replace entries
- Cross-reference requirements

### §8.4 First end-to-end test

After implementation:
1. Build 0063 = BM-001 Insert at target `0x055948` with helper-jump
2. Verify Build 0063 is diagnostic (postpatcher emits diagnostic mode label; gate runs §2.7)
3. Bookmark cycle evidence collection (MAME breakpoint at `genesistan_diag_bookmark` address; check whether execution reaches the helper)
4. Build 0064 = BM-001 Revert
5. Verify Build 0064 SHA == Build 0062 SHA (§2.8 passes)
6. AGENTS_LOG records evidence outcome
7. OPEN-001/OPEN-004 evidence base advances per cycle result

### §8.5 No changes to

- `RULES.md` Rule 10 (current text remains accurate; this design fills in the helper-design's deferred mechanics)
- `Andy_diagnostic_bookmark_helper_design.md` activator format (`4EF9{symbol:...}` + NOP padding remains correct; this design adds metadata around it)
- `Andy_build_pipeline_determinism_gate_design.md` six-check structure (this design extends with §2.7/§2.8; the original six checks are preserved)
- `apps/rastan-direct/src/diag_bookmark.s` (helper source unchanged)
- `apps/rastan-direct/Makefile` core structure (gate invocation may need optional flag pass-through, e.g., for build counter context; Cody decides at implementation time)

---

## §9 Rule 9 + Rule 10 compliance

### §9.1 Rule 9

Diagnostic builds are NOT final-build ROMs. They are evidence-collection artifacts. However, the postpatcher and gate code that makes them possible IS final-build infrastructure: it ships in the pipeline forever, runs on every ROM-producing build, and is production-intent.

Rule 9 question: "Would this exist in the final production ROM?" — the diagnostic *infrastructure* (postpatcher invariant model, gate's §2.7/§2.8 checks, DIAGNOSTIC_SYMBOLS tuple) would, because it runs on every build. The diagnostic *output* (Build 0063 etc.) is intentionally transient per Rule 10's revert obligation. Build 0063 does not ship to end users; Build 0064 (the Revert) is byte-identical to Build 0062 (the canonical) and is the version that ships.

Rule 9 is satisfied: pipeline infrastructure belongs in the project; transient diagnostic ROMs are provably reverted by the immediately-following canonical build.

### §9.2 Rule 10

| Rule 10 constraint | Compliance |
|---|---|
| Helper in safe high-ROM region | unchanged from prior helper design |
| Bytes immutable across builds | unchanged; SHA `20825b36...` |
| SHA256-verifiable | unchanged |
| Default body self-loop, not STOP | unchanged |
| Helper inert when not jumped to | unchanged |
| Helper persists as infrastructure | unchanged |
| Activator reverted in immediately-following ROM-producing build | enforced by §2.8 byte-identical revert check |
| Activator persistence across two consecutive ROM builds forbidden | enforced by §2.8 + cycle integrity invariant in §7.5 |
| Insert + revert logged in AGENTS_LOG | unchanged; template from prior helper design §1.5 used (with one additional field: `pre_insert_canonical_rom_sha256`) |
| Byte-verified against canonical ROM | strengthened by §2.8 (SHA equality, not just predicate equivalence) |
| ROM, not WRAM | unchanged |
| Scoped task | enforced by §5.3 (one cycle in flight; Insert/Revert each are scoped) |
| At most one bookmark cycle in flight | enforced by §5.3 + spec-level rejection of multi-entry diagnostic_bookmarks |
| Observation only | unchanged |
| STOP conditions cited | §6 specifies STOP for §2.7 and §2.8 failures |

All Rule 10 constraints from the prior helper design remain satisfied; this design strengthens "byte-verified against canonical ROM" from predicate-equivalence to byte-equality via §2.8.

---

## §10 Surfaced ambiguities

### Ambiguity 1 — Diagnostic build numbering

**Question:** should diagnostic builds get sequential numbers (Build 0063 = BM-001 Insert) or a separate numbering scheme (`BM001_insert.bin`)?

**Chosen interpretation:** **sequential numbering, no separate scheme.**

**Reasoning:**
- OPEN-002 extended policy says sequential numbers, no letter suffixes. A separate scheme like `BM001_insert.bin` would violate the spirit (per OPEN-002: "Task labels, design doc filenames, dump directories, and trace folders must NOT use letter suffixes either"). A `BM001` prefix would be in conflict.
- Diagnostic builds consume build counter slots because they are ROM-producing tasks.
- Disambiguation between canonical and diagnostic happens via AGENTS_LOG and the spec's `diagnostic_bookmarks` field, not via filename. The filename simply identifies the sequential ROM.
- Discipline (per cycle templates) ensures the canonical baseline tracked for §2.8 is the most-recent CANONICAL build, not the most-recent build by number.

**Cost:** anyone reading a filename in isolation cannot tell whether a build is canonical or diagnostic. Mitigated by AGENTS_LOG entries and the spec being version-controlled.

### Ambiguity 2 — Where DIAGNOSTIC_SYMBOLS tuple lives

**Question:** hardcoded in postpatcher source vs. in a separate config module vs. in the spec.

**Chosen interpretation:** **hardcoded in postpatcher source.**

**Reasoning:**
- Three-place friction (postpatcher source + design doc + AGENTS_LOG) matches the helper SHA's friction model. Documented in §4.4.
- Spec-driven would be permissive; activator entries could effectively allowlist their own symbols.
- Separate config module would add a fourth surface to drift.
- The helper-canonical-SHA pattern in `Andy_diagnostic_bookmark_helper_design.md` already establishes the precedent.

### Ambiguity 3 — Computed vs. static Σ (coverage delta)

**Question:** compute Σ from activator span lengths, or store statically as a field in `diagnostic_bookmarks` entry?

**Chosen interpretation:** **computed from activator span lengths.**

**Reasoning:**
- The opcode_replace entry's `original_bytes` is already authoritative for span. Duplicating in `diagnostic_bookmarks` would add drift surface.
- Computed Σ is self-consistent with the linked opcode_replace entry.
- One fewer field to validate; cross-reference check (cycle_id matching) already enforces linkage.

### Ambiguity 4 — Revert SHA-identical vs. predicate-equivalent

**Question:** must BM-N Revert produce a ROM SHA-identical to the pre-Insert canonical, or merely satisfy the canonical predicate?

**Chosen interpretation:** **SHA-identical (stronger).**

**Reasoning:**
- Rule 10's "byte-verified against canonical ROM" wording implies byte-equality.
- The build counter is in the filename, not the ROM bytes; SHA-identical is achievable.
- Predicate equivalence is weaker; a Revert that adds an unrelated spec change could pass canonical checks but introduce a subtle byte difference. SHA-equality catches that.
- §2.8 is added specifically to enforce this stronger contract.

### Ambiguity 5 — Mechanism for Revert detection (gate's §2.8 trigger)

**Question:** how does the gate know "this build is a Revert"?

**Chosen interpretation:** **state file written by postpatcher on Insert, consumed by gate on Revert.**

**Reasoning:**
- A transient state file (`build/rastan-direct/active_bookmark_baseline.json`) is the simplest mechanism that doesn't require Cody to parse AGENTS_LOG at gate time.
- File presence + empty `diagnostic_bookmarks` = Revert build.
- File absence + empty `diagnostic_bookmarks` = canonical build (not a Revert).
- File presence + non-empty `diagnostic_bookmarks` = Insert build (postpatcher writes file).
- File removed by gate on successful Revert.

**Alternative (rejected):** parse AGENTS_LOG for most-recent Insert entry. Rejected because it couples gate to AGENTS_LOG format, fragile if AGENTS_LOG structure changes.

### Ambiguity 6 — Multi-entry diagnostic_bookmarks (multi-target cycles)

**Question:** should the spec field support multiple simultaneous entries (multi-target cycle)?

**Chosen interpretation:** **NO — single-entry only.**

**Reasoning:**
- Rule 10's "at most one bookmark cycle in flight at any time" constraint (per [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.6) carries forward.
- Multi-entry would require a more complex revert protocol (which entry reverts in which build?) that Rule 10 explicitly forbids.
- Postpatcher rejects multi-entry `diagnostic_bookmarks` arrays as a consistency error.
- Future Rule 10 amendment could relax this; not required now.

---

## §11 New OPEN issue tracking

**Recommendation: open OPEN-011 to track Cody implementation.**

Justification:
- The implementation spans postpatcher source, gate script, spec format documentation, and end-to-end testing. Substantial Cody work.
- Without OPEN-011, the implementation status would only be visible in AGENTS_LOG — easy to lose track of during context switches.
- BM-001 (and any downstream bookmark cycle) is blocked until OPEN-011 closes; the issue ledger should reflect that block visibly.
- OPEN-008 (issue-tracking process) is already a passive context-only issue; OPEN-011 is the active implementation tracking.

Brief content for OPEN-011 (Andy specifies the entry; Cody can refine details when adding):
- Title: "Postpatch invariant model + diagnostic symbol allowlist + gate context-awareness (per Andy_diagnostic_bookmark_postpatch_invariant_design.md)"
- Status: OPEN
- Priority: HIGH
- Discovered by: Cody (BM-001 STOP)
- Observed in build: BM-001 Insert STOP (no ROM produced)
- Summary: Bookmark mechanism conflicts with postpatcher's canonical-build invariants. Design produced; implementation pending.
- Suspected area: `tools/translation/postpatch_startup_rom.py`, `tools/translation/verify_canonical_rom.py`, `specs/rastan_direct_remap.json` format
- Next required task: Cody implements per `docs/design/Andy_diagnostic_bookmark_postpatch_invariant_design.md`; then end-to-end test (BM-001 Insert producing Build 0063 + BM-001 Revert producing Build 0064 byte-identical to Build 0062)
- Closure condition: BM-001 cycle completes end-to-end with §2.8 SHA-identical revert verification passing

---

## Phase 5 Integrity

- Design document with all 8 §OBJECTIVE items resolved: YES
  - 1. Activator representation: §1.4 + §2.2 (`bookmark_cycle` field added; `4EF9{symbol:...}` template form confirmed)
  - 2. Approved diagnostic symbol mechanism: §4 (`DIAGNOSTIC_SYMBOLS` tuple hardcoded; three-place friction governance)
  - 3. Build context distinction: §2.1 (`diagnostic_bookmarks` top-level spec field; presence + non-emptiness = diagnostic)
  - 4. Context-aware count invariant: §3 (computed `expected_count`/`expected_coverage`; existing canonical constants preserved)
  - 5. Insert/revert lifecycle: §5 (spec edits, build flow, AGENTS_LOG fields, cycle constraints)
  - 6. Gate behavior per check on diagnostic builds: §6 (matrix table; §2.5 expansion; new §2.7/§2.8)
  - 7. Formal definitions: §7 (canonical, diagnostic, canonical baseline, revert-to-canonical, cycle integrity invariant)
  - 8. Interaction with gate's six checks: §6 (per-check matrix); §8.2 (implementation summary)
- Canonical invariant preserved for canonical builds: YES (§3.1 explicitly preserves `canonical_count = 94`, `canonical_coverage = 0x17CAEC`; canonical mode runs unchanged invariant check)
- `required_symbols` allowlist principled, not permissive: YES (§4.3: hardcoded DIAGNOSTIC_SYMBOLS tuple, not spec-driven; three-place friction for additions)
- Build context distinction specified: YES (§2 — spec field + activator self-identification + cross-reference rule)
- Context-aware count invariant formula specified: YES (§3.1 — `94 + N` and `0x17CAEC + Σ`; §3.2 — validation pseudocode)
- Activator representation specified: YES (§2.2 — confirms prior helper design + adds `bookmark_cycle` field)
- Insert/revert lifecycle specified: YES (§5)
- Per-check gate behavior on diagnostic builds specified: YES (§6 matrix + §6.2/§6.3/§6.4 procedures)
- Rule 9 and Rule 10 compliance demonstrated: YES (§9 — Rule 9 reasoning; §9.2 Rule 10 14-row table including strengthening via §2.8)
- No forbidden modifications: YES (this task is documentation only)
- Helper design cross-reference: YES — forward cross-reference added at the END of [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.8 "What this design does NOT do" or §1.9 "RULES.md update decision" — Cody can add at implementation time, or Andy can add separately. Andy chose NOT to edit the prior helper design in this task to keep scope clean; cross-reference via AGENTS_LOG entry is sufficient (the prior design's §1.3 "Activator specification" remains accurate; this new design extends it).
- New OPEN issue (OPEN-011) recommended: YES (§11)
- Surfaced ambiguities: 6 (§10)
- All STOP conditions either passed or documented: YES (no STOP triggered)
