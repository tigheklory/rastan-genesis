# Andy — Build Pipeline Determinism Gate Design

**Agent:** Andy (Claude Code)
**Type:** Design (analytical only — no implementation, no source/spec/tool/Makefile/build/ROM modifications)
**Build:** rastan-direct, post-Build-0061 regression recovery (canonical ROM `dist/rastan-direct/rastan_direct_video_test_build_0061.bin`, SHA256 `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Date:** 2026-05-08
**Naming:** descriptive output filename per OPEN-002 extended policy
**Scope:** design the build pipeline determinism gate that resolves OPEN-010's design portion. The gate proves a ROM is acceptable as canonical before any emulator debugging or bookmark cycle begins.

---

## 0. Executive verdict

**The trustworthiness predicate:**

> A ROM is canonical if and only if every byte that the source-of-truth says should be embedded in it IS embedded in it, and nothing that should not be in it has slipped in. Specifically: every `.incbin` artifact's bytes appear at the correct ROM offset; the diagnostic bookmark helper bytes appear at their canonical address; the postpatcher's structural invariants pass; the ROM filename matches sequential build numbering; every required symbol resolves; and every `.s` file with `.incbin` directives has a Makefile rule listing those inputs as dependencies.

A ROM that satisfies all of the above is canonical. A ROM that fails any check is non-canonical and is **forbidden** as a baseline for subsequent work — bookmark cycles, evidence collection, or downstream-build inputs.

**Gate structure:**

The gate is a single verification step at the end of `make`, running on the final post-patch ROM. It performs six checks (§2). Any failure aborts the build, removes the candidate ROM, and is recorded in `AGENTS_LOG.md`. The gate's expected SHAs are derived at run-time from the on-disk source-of-truth artifacts (no separate "expected SHAs" file to drift). Helper SHA is the only static baseline (recorded once in [`docs/design/Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) and the canonical-introduction `AGENTS_LOG` entry per Rule 10).

**Pipeline integration:** added as a `make` recipe step after postpatcher invariants and before the sequential-numbered-artifact copy. Failed gate → no numbered ROM produced. Hardest-to-bypass placement because the build itself enforces the gate.

**Coverage:** the gate is a content scanner, not an enumerator. Adding a new `.s` file with `.incbin`, a new generated artifact, or a new helper does not require the gate to be modified — the gate discovers the new content from the source files and the symbol map.

**Out of scope (Cody implementation work, after this design lands and Tighe approves):** the actual gate script (Python tool), Makefile recipe addition, helper-integrity config wiring, and the systematic remediation of any future `.incbin` dependency holes the gate's audit might surface.

---

## §1 Trustworthiness predicate (explicit)

The gate enforces the following six-part predicate over a candidate ROM `R` produced by `make`:

1. **Embedded `.incbin` byte-match.** For every `.incbin <path>` directive in any `apps/rastan-direct/src/*.s` file, the bytes of `<path>` (as it exists on disk at gate-run time) appear in `R` at the offset resolved by the corresponding symbol in `apps/rastan-direct/out/symbol.txt`. Byte-for-byte equality. SHA256 over a region that should equal the file equals the SHA256 of the file.

2. **Helper integrity.** The two bytes at the resolved address of `genesistan_diag_bookmark` in `R` equal `60 FE`, and SHA256 over those two bytes equals the canonical helper SHA recorded in [`docs/design/Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.4 (currently `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb` per [`Cody_build60_regression_fix_and_audit.md`](docs/design/Cody_build60_regression_fix_and_audit.md) § "Helper Preservation").

3. **Postpatcher structural invariants.** `total_genesis_bytes_covered` and `opcode_replace patched_site count` match the values asserted in [`tools/translation/postpatch_startup_rom.py:1757-1763`](tools/translation/postpatch_startup_rom.py#L1757-L1763) (currently `0x17CAEC` and `94`).

4. **ROM naming compliance.** `R`'s filename matches `rastan_direct_video_test_build_NNNN.bin` where `NNNN` is the next sequential number per `build/rastan-direct/build_counter.txt`. No letter suffixes per OPEN-002 extended policy.

5. **Symbol resolution.** Every symbol referenced by `{symbol:NAME}` templates in [`specs/rastan_direct_remap.json`](specs/rastan_direct_remap.json) resolves to an address in `apps/rastan-direct/out/symbol.txt`, and every region symbol referenced in §1.1 (e.g., `genesistan_pc080sn_tile_vram_lut`, `genesistan_diag_bookmark`) resolves to an address inside `R`'s byte range.

6. **`.incbin` Makefile dependency completeness.** Every `.incbin <path>` directive in every `apps/rastan-direct/src/*.s` file `F` corresponds to an explicit dependency `<path>` in the Makefile rule that builds `F`'s `.o`. No silent dependency holes.

A ROM that satisfies all six is canonical. A ROM that fails any one is non-canonical.

The predicate is intentionally narrow: it verifies content equality, structural invariants, and pipeline-completeness. It does NOT verify behavior (that requires emulation), regression against prior canonicals (that requires history), or future-proofing claims (that requires speculation). Behavior verification happens in subsequent emulator-based work; the gate's job is solely to certify that the ROM contains what it claims to contain.

---

## §2 Verification checks (one per predicate clause)

### §2.1 Embedded `.incbin` byte-match

**What it verifies:** every `.incbin` artifact's on-disk bytes appear at the correct ROM offset.

**Why load-bearing:** Build 60's regression was exactly this check failing. Make linked a stale `scene_load.o` whose embedded LUT/preload bytes were pre-CLOSED-007 even though the on-disk artifacts were post-fix. Per [`Cody_build60_regression_forensics.md`](docs/design/Cody_build60_regression_forensics.md) §3.3, Build 60's embedded LUT SHA `9f2f2e8e...` differed from the on-disk LUT SHA `ca9c3dcf...`. This check would have flagged that immediately.

**Procedure:**

```
For each .s file F in apps/rastan-direct/src/:
  Parse F for .incbin "<path>" directives. <path> is relative to the .s file's directory.
  For each .incbin found:
    Resolve the corresponding symbol (the .global symbol immediately preceding the .incbin in F)
    From apps/rastan-direct/out/symbol.txt, get the symbol's ROM offset O
    From <path>, read N bytes (file size) and compute SHA_disk
    From R at offset O, read N bytes and compute SHA_rom
    If SHA_disk != SHA_rom: FAIL with target=symbol, path=<path>, expected=SHA_disk, found=SHA_rom
```

**Currently-applicable artifacts (per [`Cody_build60_regression_fix_and_audit.md`](docs/design/Cody_build60_regression_fix_and_audit.md) § "Embedded Region Verification"):**

| Symbol | Source `.s` | `.incbin` path | Build 0061 SHA |
|---|---|---|---|
| `genesistan_pc080sn_tile_vram_lut` | scene_load.s | `build/pc080sn_tile_vram_lut.bin` | `ca9c3dcf...` |
| `genesistan_pc080sn_attr_lut` | scene_load.s | `build/pc080sn_attr_lut.bin` | `2614c7b4...` |
| `genesistan_pc080sn_tile_rom` | scene_load.s | `build/regions/pc080sn.bin` | `a33372eb...` |
| `genesistan_scene_preload_title` | scene_load.s | `build/pc080sn_scene_preload_title.bin` | `e0a814f2...` |
| `genesistan_scene_preload_gameplay` | scene_load.s | `build/pc080sn_scene_preload_gameplay.bin` | `462c428c...` |
| `genesistan_scene_preload_endround` | scene_load.s | `build/pc080sn_scene_preload_endround.bin` | `690835b8...` |
| (pc090oj_genesis bytes) | pc090oj_assets.s | `build/pc090oj_genesis.bin` | (Cody computes at first gate run) |
| (pc090oj_slot_lut bytes) | pc090oj_assets.s | `build/pc090oj_slot_lut.bin` | (Cody computes at first gate run) |

The gate doesn't hard-code this list. It scans for `.incbin` at run time.

### §2.2 Helper integrity

**What it verifies:** the diagnostic bookmark helper bytes match Rule 10's canonical SHA.

**Why load-bearing:** Rule 10 specifies the helper is immutable across builds. Build 60 forensics confirmed helper preserved at `0x00071C78`; Build 0061 fix verified the same. This check makes that preservation an automated build gate rather than a manual post-build check.

**Procedure:**

```
Read genesistan_diag_bookmark address from apps/rastan-direct/out/symbol.txt → A
Read 2 bytes from R at offset A → bytes_helper
If bytes_helper != hex(60FE): FAIL (helper bytes corrupted)
Compute SHA256(bytes_helper) → SHA_helper
If SHA_helper != "20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb": FAIL (canonical drift)
```

The canonical SHA is recorded in [`docs/design/Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.4 and [`AGENTS_LOG.md`](AGENTS_LOG.md) helper-introduction entry. Updates to canonical SHA require both a design-doc revision AND an AGENTS_LOG entry justifying the change (Rule 10's helper-immutability constraint should make this never happen, but if it ever does, the gate fails until baseline is updated explicitly).

### §2.3 Postpatcher structural invariants

**What it verifies:** the ROM's segment-coverage byte count and `opcode_replace` site count match the project's recorded baseline.

**Why load-bearing:** these invariants already exist in the postpatcher and have caught real bugs (the comment block at [`postpatch_startup_rom.py:1737-1755`](tools/translation/postpatch_startup_rom.py#L1737-L1755) documents 7+ historical baseline updates from real Build 53/54/55/55b/0060 events). The gate's job is to confirm the postpatcher ran successfully — not to duplicate its logic.

**Procedure:**

```
The Makefile's $(BIN) recipe currently invokes postpatcher and would fail $(BIN) on RuntimeError.
The gate confirms the postpatcher exited cleanly by examining whether the build succeeded up to the gate step.
If the gate is reachable, postpatcher invariants passed by definition.
No additional verification logic; this clause is satisfied by Makefile sequencing.
```

This delegation keeps the gate orthogonal to postpatcher's concerns and avoids drift between two checks of the same invariant.

### §2.4 ROM naming compliance per OPEN-002

**What it verifies:** the produced ROM's filename uses sequential numbering with no letter suffix.

**Why load-bearing:** OPEN-002's extended policy bans letter suffixes across all artifact types. A failed gate that allows `0061b.bin` to ship would silently regress on OPEN-002. The gate enforces the policy mechanically.

**Procedure:**

```
Read build/rastan-direct/build_counter.txt → expected NNNN (zero-padded 4 digits)
Construct expected filename: rastan_direct_video_test_build_NNNN.bin
List dist/rastan-direct/ for the just-produced numbered artifact filename
If filename != expected: FAIL (naming policy violation)
If filename matches /[0-9]+[a-z]/: FAIL (letter suffix)
```

The Makefile's [build counter logic at lines 124-131](apps/rastan-direct/Makefile#L124-L131) already produces the expected filename. The gate verifies that nothing renamed it after the fact (an alias copy or accidental rename).

### §2.5 Symbol resolution

**What it verifies:** every `{symbol:NAME}` template in the spec resolves, and every region symbol points within ROM bounds.

**Why load-bearing:** if a symbol fails to resolve, postpatcher already fails earlier — but a symbol that resolves to an OUT-OF-BOUNDS address would silently corrupt downstream verification (e.g., reading 32768 bytes from offset `R_size - 100` would read past EOF and pad with zeros, masking byte mismatches). The gate enforces that every symbol used by any check points to a valid ROM range.

**Procedure:**

```
Parse apps/rastan-direct/out/symbol.txt → dict[symbol_name → ROM offset]
For every symbol referenced by §2.1's .incbin scan:
  If symbol not in dict: FAIL
  If symbol_address + region_byte_count > len(R): FAIL (out of bounds)
For every symbol referenced by §2.2 (genesistan_diag_bookmark):
  Same checks
For every {symbol:NAME} reference in specs/rastan_direct_remap.json:
  If NAME not in dict: FAIL
  (Address bounds check: postpatcher already enforced this; gate trusts.)
```

### §2.6 `.incbin` Makefile dependency completeness

**What it verifies:** every `.s` file using `.incbin` has corresponding Makefile dependencies for those `.incbin` inputs.

**Why load-bearing:** Build 60's regression mechanism. Per [`Cody_build60_regression_fix_and_audit.md`](docs/design/Cody_build60_regression_fix_and_audit.md) § "Phase 2 audit", scene_load.s had 6 `.incbin` inputs but only listed itself as a Makefile dependency. The fix added the 6 deps explicitly. The gate's audit makes this hole-detection automated for every `.s` file going forward.

**Procedure:**

```
Read apps/rastan-direct/Makefile.
Parse rules for each .o target: extract dependency list.
For each .s file F in apps/rastan-direct/src/:
  Compute O_F = expected .o name (out/F_basename.o)
  Find Makefile rule for O_F: extract its dependency list D_F
  Parse F for .incbin "<path>" directives: list I_F (paths normalized)
  For each path P in I_F:
    Compute P_root = $(ROOT)/<path-from-Makefile-perspective>
    If P_root not in D_F: FAIL (missing .incbin dependency in Makefile)
```

This check runs at the source level, not against the candidate ROM. It is a pipeline-completeness check rather than a content check. Adding it to the gate ensures that even if a developer adds a new `.incbin` directive without the matching Makefile dependency, the gate refuses to ship the ROM.

---

## §3 Pipeline integration point

### Where the gate runs

**Recommended placement:** as a `make` recipe step in `apps/rastan-direct/Makefile`, inside the `$(BIN)` target, after postpatcher and the postpatch disasm step, but **before** the numbered-artifact copy at [Makefile lines 124-131](apps/rastan-direct/Makefile#L124-L131).

Concretely (Cody implements; this is illustrative):

```makefile
$(BIN): $(PREPATCH_BIN) $(SYMBOLS) $(PATCH_SPEC) $(PATCHER) $(BOOT_GUARD) | $(DIST_DIR)
    # ... existing pre-patch and patch steps unchanged ...
    $(PYTHON) "$(PATCHER)" ...                # postpatcher (existing)
    $(PYTHON) "$(BOOT_GUARD)" --rom "$@"      # boot guard (existing)
    $(OBJDUMP) -D ... > $(ROOT)/build/genesis_postpatch.disasm.txt   # disasm (existing)
    $(PYTHON) "$(ROOT)/tools/translation/verify_build_determinism.py" \
        --rom "$@" \
        --src-dir "$(SRC_DIR)" \
        --makefile "$(MAKEFILE_LIST)" \
        --symbols "$(SYMBOLS)" \
        --spec "$(PATCH_SPEC)" \
        --helper-canonical-sha 20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb
    # ... existing numbered-artifact copy and trace ...
```

### Why this placement

- **After postpatcher:** §2.3 delegates to postpatcher; gate runs after to confirm postpatcher's success implicitly.
- **Before numbered-artifact copy:** the numbered artifact (`0061.bin`, `0062.bin`, ...) is the canonical record of the build. If the gate fails, no numbered artifact gets created. There's no "almost-canonical" or "candidate" state shipping into the dist directory.
- **Inside `$(BIN)` recipe:** Make's dependency model ensures `$(BIN)` cannot be considered up-to-date unless every recipe step (including the gate) succeeded. A subsequent `make` with no source changes won't regenerate, but cannot bypass the gate either — the gate's success is part of `$(BIN)`'s validity.
- **Hardest to bypass:** running `make` is the only sanctioned way to produce a ROM in this project. Putting the gate inside `make` means there's no "alternative path" to a ROM that skips verification. Manual byte-edits to a ROM file would not be canonical (the gate's check would catch it on next `make`); manual builds outside `make` would not produce a canonical ROM at all.

### Why not pre-link or post-link-but-pre-postpatch

Pre-link checks could catch stale objects faster (before incurring link time), but they cannot verify the final ROM's embedded content (the ROM doesn't exist yet). The cost of incurring link time on a doomed build is acceptable; the benefit of verifying the ACTUAL ROM rather than its predecessors is large. A post-link, post-postpatch check is the latest, most authoritative point and catches everything the earlier checks could plus everything they couldn't.

A future optimization could add a fast pre-link sanity layer (just the `.incbin` Makefile dependency audit, which doesn't need the ROM) for fast failure. That's an enhancement, not part of the initial gate.

---

## §4 Failure semantics

### When any §2 check fails

1. **Gate exits non-zero with a structured error message.** The message identifies which check failed (§2.1 through §2.6), what was expected, what was found, and the specific symbol/file/path involved.

2. **Make recipe fails.** Because the gate is part of `$(BIN)`'s recipe, non-zero exit aborts the build. The recipe's later steps (numbered-artifact copy, MAME trace) do not run.

3. **The candidate ROM at `dist/rastan-direct/rastan_direct_video_test.bin` is removed.** Make's `.DELETE_ON_ERROR` (or an explicit `rm` step in the failure path) ensures no candidate-canonical ROM lingers on disk. Future `make` invocations re-run the full build, not skip the gate via cached ROM presence.

   Cody's implementation choice: `.DELETE_ON_ERROR:` line in Makefile is the cleanest mechanism. Alternative is an explicit `trap`/cleanup step in the gate's failure path.

4. **No numbered ROM is produced.** The build counter at `build/rastan-direct/build_counter.txt` is NOT incremented; the next sequential number remains the same as before the failed build. Failed builds do not consume sequential build numbers. (This requires the build counter increment to happen AFTER the gate, not before — Makefile sequencing handles this.)

5. **AGENTS_LOG entry records the failure.** The agent that ran the failed build creates an AGENTS_LOG entry documenting: which check failed, why, what was the immediate cause (e.g., "stale `.o`", "uncommitted `.incbin` regenerate"), and whether a fix follow-up is required.

6. **Rule 10 bookmark cycle blocking.** Per Rule 10's "byte-verified against canonical ROM" constraint, bookmark cycles cannot proceed against a non-canonical ROM. Failed gate → no canonical ROM → bookmark cycles blocked until next clean build. This is enforced by Cody discipline (bookmark task templates per [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.5 reference the most-recent canonical ROM).

### What a failing-gate message should contain

```
DETERMINISM GATE FAILURE: <check_id> (e.g., §2.1 embedded .incbin byte-match)
Symbol: genesistan_pc080sn_tile_vram_lut
Source .s file: apps/rastan-direct/src/scene_load.s
.incbin path: build/pc080sn_tile_vram_lut.bin
Expected SHA256 (from disk artifact): ca9c3dcf1aa3624c3660aa3b7443625433341941955c2c3f7c5956f44f5d3e92
Found SHA256 (from ROM at offset 0x000F1EC0, length 32768): 9f2f2e8ed1d6439d268d12cf19e2c72dc684779b6681880133338a03840b9d74
Likely cause: stale .o file linked instead of regenerated; recommend `rm out/<file>.o && make`.
```

The message MUST identify the failing check, the comparison values, and a likely cause. Format is Cody's call; content above is the floor.

---

## §5 Baseline maintenance

The gate distinguishes intentional baseline changes from silent regressions by **deriving its expected values from project-controlled source-of-truth files at gate-run time**, not from a separate "expected SHAs" sidecar that could drift.

### Per-check baseline source

| Check | Baseline source | Update mechanism |
|---|---|---|
| §2.1 `.incbin` byte-match | The on-disk generated artifact files themselves | Re-running the generator (e.g., `precompute_pc080sn_tile_lut.py`) updates the on-disk artifact; gate re-derives expected SHA at next run; no gate config change |
| §2.2 helper integrity | Constant `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb` recorded in [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.4 | Helper SHA should never change per Rule 10 immutability. If it ever does (intentional protocol change), update is via Andy design-doc revision + AGENTS_LOG entry justifying the change + Makefile `--helper-canonical-sha` argument update. Three-place change makes silent drift impossible. |
| §2.3 postpatcher invariants | Constants in [`postpatch_startup_rom.py:1757-1763`](tools/translation/postpatch_startup_rom.py#L1757-L1763) | Source-controlled edit to the postpatcher script with comment-block update at lines 1737-1755. Build 60 already followed this pattern (`0x17CAE8` → `0x17CAEC` for helper introduction). Gate trusts postpatcher. |
| §2.4 naming compliance | `build/rastan-direct/build_counter.txt` (auto-incremented by Makefile) | No baseline maintenance needed; counter is monotonically advancing. |
| §2.5 symbol resolution | `apps/rastan-direct/out/symbol.txt` (regenerated every build by `nm`) | No baseline maintenance needed; symbol table is always current. |
| §2.6 `.incbin` Makefile audit | The Makefile and `.s` files themselves | Adding a new `.incbin` directive WITHOUT the matching Makefile dep fails the gate — that IS the maintenance feedback loop. |

### Distinguishing intentional updates from silent regressions

The key insight: for §2.1, the gate compares ROM-embedded bytes to ON-DISK ARTIFACT bytes. Both sides reflect the current state. If the artifact gets regenerated (intentional update), the on-disk file changes AND the ROM gets re-built embedding the new bytes — both sides change consistently. If a stale `.o` is linked (silent regression — Build 60), the artifact is current but the ROM embeds old bytes — the two sides diverge and the gate catches it.

Silent regressions are by definition divergences between source-of-truth and final artifact. The gate detects exactly that.

For §2.2 (helper integrity), Rule 10 specifies the helper is immutable, so changes to the canonical SHA are inherently suspect. The three-place update requirement (design doc + AGENTS_LOG + Makefile arg) is friction by design — accidental drift is impossible.

For §2.3 (postpatcher invariants), the postpatcher's existing comment block at lines 1737-1755 already documents every historical baseline update with the build number that caused it. This convention extends naturally; the gate doesn't need to enforce documentation discipline (the convention already exists), but the structural invariants themselves are checked.

### What if the on-disk artifact is itself wrong?

The gate cannot detect that. If `precompute_pc080sn_tile_lut.py` is modified to produce buggy output and re-run, both the on-disk artifact AND the ROM-embedded bytes will reflect the bug, and §2.1 will pass. This is a generator correctness concern, not a determinism concern. The gate's predicate is "ROM contains what source-of-truth says it should contain," not "source-of-truth is correct." Generator correctness is verified by other means (manual inspection, visual verification, prior CLOSED-007 design doc, etc.).

---

## §6 Coverage

### How new content is covered without gate changes

**New `.s` file with `.incbin`:** §2.1 scans `apps/rastan-direct/src/*.s` at gate-run time. A new `.s` file is automatically picked up. §2.6 audits the new file's Makefile dependencies. No gate code change.

**New generated artifact (new `.incbin` directive in existing `.s`):** same as above. Gate scans the directive list. New artifact is automatically verified.

**New helper symbol (e.g., a future bookmark or hook helper):** §2.5 catches missing symbols. §2.2 currently hard-codes `genesistan_diag_bookmark` because Rule 10 specifies it as the bookmark helper. Other helpers don't have an immutable-bytes constraint and don't need their own §2.2 entry. If a future Rule (Rule 11+) introduces another immutable helper, §2.2 expands by config.

**New `opcode_replace` entry:** §2.5 verifies the `{symbol:...}` reference resolves. Postpatcher's existing invariant (§2.3) catches count drift.

**New build artifact type entirely (unlikely, but possible):** would require a new §2.X check. Gate is extensible; adding a new check is a Cody implementation task with corresponding Andy design (this doc would be revised).

### Bounded vs unbounded coverage

§2.1 and §2.6 are unbounded — they iterate over content. §2.2 through §2.5 are currently bounded (specific helpers, specific invariants, specific naming pattern), but each is bounded by an external standard (Rule 10, postpatcher source, OPEN-002 policy, symbol map) that itself can grow. Adding to those external standards is documented elsewhere; the gate adapts mechanically.

The audit confirms that ALL current `.s` files using `.incbin` are covered (per [`Cody_build60_regression_fix_and_audit.md`](docs/design/Cody_build60_regression_fix_and_audit.md) Phase 2: scene_load.s and pc090oj_assets.s; the audit confirmed pc090oj_assets.s already had complete deps). The gate's correctness does not depend on this count remaining bounded.

---

## §7 Interaction with existing project mechanisms

### Postpatcher (`tools/translation/postpatch_startup_rom.py`)

Postpatcher already verifies:
- `total_genesis_bytes_covered == 0x17CAEC` (line 1757)
- `opcode_replace patched_site count == 94` (line 1758)
- Site-key uniqueness (lines 1767-1773)
- Various semantic checks throughout

Gate's relationship: orthogonal. Gate does NOT duplicate postpatcher's checks. Gate verifies what postpatcher CANNOT (embedded `.incbin` bytes vs on-disk source-of-truth, helper preservation, naming compliance, dependency completeness). Postpatcher's success is a precondition for gate to run; gate's success is the final canonical certification.

### Make's dependency tracking (`apps/rastan-direct/Makefile`)

Make's dep tracking is necessary but not sufficient:
- Necessary: without proper deps, stale objects link and embed wrong bytes (Build 60).
- Not sufficient: even with perfect deps, content errors (wrong artifact, wrong helper bytes, wrong invariants) can ship if not verified.

Gate's relationship: §2.6 enforces dependency completeness as project policy. §2.1 catches any consequences of missing deps that escaped §2.6's audit. Defense in depth.

### Manual SHA recording in design docs and AGENTS_LOG

Currently, SHAs are recorded in design docs (`Andy_diagnostic_bookmark_helper_design.md`, Cody Build 60 fix audit) and AGENTS_LOG entries. These records are informational — a reviewer can manually compare them but no tool enforces it.

Gate's relationship: replaces manual comparison with automated check for the helper SHA. The other SHAs (LUT, preloads, etc.) become self-verifying because the gate compares to current on-disk artifacts; recorded SHAs in AGENTS_LOG are now historical reference rather than active baselines.

### Boot guard (`tools/translation/verify_rastan_direct_boot_guard.py`)

Boot guard verifies bootstrap-region bytes. It runs twice per build (pre-patch and post-patch per Makefile lines 110, 120).

Gate's relationship: orthogonal. Boot guard checks low-ROM bootstrap; gate checks the rest of the ROM (embedded artifacts, helper, naming, symbols, deps). Both should pass for a canonical ROM.

---

## §8 Rule 9 + Rule 10 compliance

### Rule 9 — "If It Doesn't Belong in Final Build, It Doesn't Belong Here"

The gate IS final-build infrastructure:
- The verification script (`tools/translation/verify_build_determinism.py` per Cody implementation) ships as part of the build pipeline.
- Its checks are production-intent, not scaffolding. They run on every ROM-producing build, not as ad-hoc diagnostic tooling.
- The ROM that ships to end users (if the project ever distributes ROMs) is the canonical ROM that passed the gate.

The gate doesn't introduce any code into the ROM itself; it's a tooling layer around the build. Rule 9 is satisfied because the gate's tooling belongs in the production pipeline (it would be used by every build forever) and the ROM it certifies is canonical-by-construction.

### Rule 10 — Diagnostic Bookmarks

Rule 10's helper-immutability and SHA-verifiability requirements are mechanically enforced by §2.2. Without the gate, helper integrity is verified by manual byte-comparison and SHA recording — work that humans do reliably most of the time but not always. The gate makes helper integrity a build precondition, eliminating the human-error window.

Rule 10's "byte-verified against canonical ROM" requirement (in the Constraints section) is what bookmark cycles need from the gate: a way to know whether a ROM is canonical before using it as a baseline. The gate provides exactly that. Bookmark cycle templates (per [`Andy_diagnostic_bookmark_helper_design.md`](docs/design/Andy_diagnostic_bookmark_helper_design.md) §1.5) reference "canonical ROM" — that term is defined by the gate.

### Compliance summary

| Element | Compliance |
|---|---|
| Rule 9: gate is final-build infrastructure | YES (production pipeline integration; runs on every ROM-producing build) |
| Rule 9: gate doesn't add scaffolding | YES (verification only; no behavior modification, no test code in ROM) |
| Rule 10: helper bytes immutable | YES (§2.2 enforces) |
| Rule 10: SHA-verifiable | YES (§2.2 hashes and compares) |
| Rule 10: byte-verified against canonical ROM | YES (gate's existence defines "canonical ROM") |
| Rule 10: insert/revert byte verification | YES (§2.1 verifies activator entries' embedded bytes match expected; §2.2 verifies helper survives every cycle) |

---

## §9 Surfaced ambiguities

### Ambiguity 1 — Where the canonical helper SHA lives

**Question:** Should the canonical helper SHA `20825b36...` be:
(a) hard-coded in Makefile as a `--helper-canonical-sha` argument,
(b) stored in a config file that gate and design doc both reference,
(c) stored only in the design doc and read by gate at run-time?

**Chosen interpretation:** **(a) — Makefile argument, mirrored by design doc and AGENTS_LOG entry.**

**Reasoning:**
- Three-place storage (Makefile + design doc + AGENTS_LOG entry) creates intentional friction for changes. Updating the SHA requires touching all three; nobody will accidentally drift one.
- Reading from a config file (option b) introduces a fourth surface (the config) that itself could drift; net adds complexity.
- Reading from the design doc at gate run-time (option c) makes the gate parse markdown at build time, which is fragile (markdown format changes break verification).
- The argument-in-Makefile pattern matches existing `--variant world_rev1` and similar — fits established convention.

### Ambiguity 2 — Whether the gate runs `make` itself or is a separate tool

**Question:** Is the gate a Python script that the Makefile invokes (one of many recipe steps), or a standalone wrapper that invokes `make` and verifies the result?

**Chosen interpretation:** **A Python script invoked by the Makefile recipe, NOT a wrapper around `make`.**

**Reasoning:**
- Wrappers around `make` are bypassable (anyone can run `make` directly).
- A recipe step is part of `make` itself, so any `make` invocation runs it.
- Putting the gate inside `make` makes the gate part of the build's correctness contract: `$(BIN)` is not up-to-date without it.
- This matches how postpatcher and boot guard are integrated.

### Ambiguity 3 — Failed-build cleanup mechanism

**Question:** When the gate fails, should the candidate ROM be removed via `.DELETE_ON_ERROR:`, an explicit `rm` in the failure path, or left on disk for forensics?

**Chosen interpretation:** **`.DELETE_ON_ERROR:` directive in Makefile.**

**Reasoning:**
- `.DELETE_ON_ERROR:` is the standard Make idiom for "remove failed targets." Cleanest, most consistent with Make conventions.
- Leaving a failed ROM on disk creates ambiguity about whether the file is canonical — exactly the ambiguity the gate exists to eliminate.
- Forensics that need the failed ROM can copy it before re-running (the gate's failure message identifies the issue precisely; usually no extra forensics needed).
- If forensics demand the failed file, an explicit override (e.g., `make BYPASS_DELETE_ON_ERROR=1`) could be added later; not required for the initial gate.

### Ambiguity 4 — Build counter increment timing

**Question:** Should the build counter increment happen BEFORE the gate (so failed builds consume sequential numbers, leaving gaps) or AFTER (so failed builds don't consume numbers, sequence stays dense)?

**Chosen interpretation:** **AFTER the gate. Failed builds do NOT consume sequential numbers.**

**Reasoning:**
- Per OPEN-002 extended policy, build numbers are reserved for ROM-producing tasks. A failed gate produces no canonical ROM; therefore, no number consumed.
- Currently the Makefile increments BEFORE the postpatcher succeeds (line 124-127 happens before the postpatcher invocation in some readings). Cody must verify and possibly reorder: counter increment + numbered copy must happen AFTER the gate, atomically as the final step.
- Gaps in the sequence (e.g., 0061 → 0063, skipping 0062) would suggest a build was attempted and failed. That's actually informative; OPEN-002 tracking can interpret it. But cleaner is dense-sequence-only-on-success: 0061 → 0062 means 0062 IS canonical. No ambiguity.
- Cody's implementation choice; this design recommends AFTER.

### Ambiguity 5 — `.incbin` path normalization

**Question:** `.incbin` paths in `.s` files are relative to the `.s` file's directory (e.g., `"../../build/pc080sn_tile_vram_lut.bin"` in `apps/rastan-direct/src/scene_load.s`). Makefile dependencies are typically relative to the Makefile or use `$(ROOT)`. How does §2.6 reconcile?

**Chosen interpretation:** **Normalize both sides to absolute paths anchored at the project root, then compare.**

**Reasoning:**
- Both representations resolve to the same actual file on disk; comparing the resolved absolute path is unambiguous.
- This handles current pattern (`../../build/...` in `.s` and `$(ROOT)/build/...` in Makefile) without forcing either side to change format.
- Cody implements via `pathlib.Path.resolve()` or equivalent.

---

## Phase 4 Integrity

- Gate design document produced with all §OBJECTIVE items resolved: YES
  - Trustworthiness predicate stated explicitly: §1 (six-part predicate)
  - Verification checks specified: 6 checks in §2 (`.incbin` byte-match, helper integrity, postpatcher invariants, naming compliance, symbol resolution, `.incbin` Makefile dep audit)
  - Pipeline integration point: §3 (Makefile recipe step inside `$(BIN)` after postpatcher, before numbered-artifact copy)
  - Failure semantics: §4 (non-zero exit, recipe abort, `.DELETE_ON_ERROR:`, no counter increment, AGENTS_LOG record, bookmark cycles blocked)
  - Baseline maintenance: §5 (per-check sources; intentional-vs-silent distinction by source-of-truth derivation)
  - Coverage: §6 (content-scanner approach; new files/artifacts/helpers covered without gate code change)
  - Interaction with existing mechanisms: §7 (postpatcher orthogonal; Make defense-in-depth; manual SHA recording superseded by automated check; boot guard orthogonal)
- General gate (not scene_load-specific): YES — §2.1 iterates over all `.s` files; §2.6 audits all of them; §6 explicitly addresses scope-expansion
- Trustworthiness predicate stated explicitly: YES — §1 six-part predicate
- Pipeline integration point specified with rationale: YES — §3
- Failure semantics specified: YES — §4 (six-step failure flow)
- Baseline maintenance approach specified: YES — §5 (per-check baseline source table; silent-regression detection mechanism)
- Rule 9 + Rule 10 compliance demonstrated: YES — §8 compliance table
- No forbidden modifications by Andy: YES (this task is documentation only; Cody implements the gate)
- Ambiguities surfaced: 5 (§9)
- All STOP conditions either passed or documented: YES (no STOP triggered)
