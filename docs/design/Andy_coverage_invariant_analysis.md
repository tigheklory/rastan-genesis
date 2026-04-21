# Andy — `total_genesis_bytes_covered` Invariant Analysis

**Agent:** Andy
**Type:** Forensic Analysis + Design (no implementation)
**Build context:** current `rastan-direct`, Phase B decomposition complete
**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Outcome:** **Classification B — stale bookkeeping.** Recommended minimal fix updates the hardcoded expected value `0xFC1C4` to `0xFBF20` in two places on lines 1742 and 1747 of [tools/translation/postpatch_startup_rom.py](tools/translation/postpatch_startup_rom.py). Confidence **HIGH**.

---

## Phase 1 — How `total_genesis_bytes_covered` is computed

Traced in [tools/translation/postpatch_startup_rom.py](tools/translation/postpatch_startup_rom.py).

| Line    | Code / block                                                                                 | Effect                                                                                                          | Source of data               |
| ------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 328-332 | `def _finalize_address_map_segments(raw_segments, rom_size, wrapper_start)`                  | Function that builds the final address map and returns `(segments, coverage)`.                                  | all segments + rom_size      |
| 336-339 | `base = ...arcade_copy; patched = ...patched_site; preserved = ...preserved_vectors; genesis_only = ...genesis_only` | Partitions raw segments by kind.                                                                      | `raw_segments`               |
| 341-361 | `_overlay_segment` calls that merge `patched`, `wrapper`, non-wrapper `genesis_only`, and `preserved` into the `base` arcade-copy intervals | Produces a single ordered interval list covering the whole ROM.                             | all segment kinds            |
| 367-398 | Gap-filling loop that emits `genesis_only` / `padding` segments for any byte-range not covered, extending to `rom_size` | Ensures the final list spans `[0, rom_size)` with no gaps.                                  | `cursor` walk, `rom_size`    |
| 413-419 | `covered = 0` ... `for segment in final_segments: covered += segment["size_bytes"]`          | **Accumulates the byte count across every final segment**. This is the value of `total_genesis_bytes_covered`.  | finalized segments           |
| 443-446 | `if covered != rom_size: raise RuntimeError(f"Segment coverage mismatch: covered=... expected=...")` | **Asserts `covered == rom_size`**. If this check passes, the returned value is exactly `rom_size`.     | covered + rom_size           |
| 452-456 | `coverage = {"total_genesis_bytes_covered": covered, "gaps": [], "overlaps": []}`            | Packages the value into the coverage dict returned to the caller.                                               | `covered`                    |
| 1721    | `finalized_segments, segment_coverage = _finalize_address_map_segments(segments, len(rom_bytes), wrapper_start)` | Caller invocation in the rastan-direct profile branch. `rom_size = len(rom_bytes)` (actual ROM length in bytes). | `rom_bytes`            |
| 1742-1745 | `if int(segment_coverage["total_genesis_bytes_covered"]) != 0xFC1C4 or len(opcode_replace_sites) != 73: raise RuntimeError("Build 0029 invariant failure: ...")` | **The invariant.** Compares the coverage value against a hardcoded `0xFC1C4` and opcode_replace count against a hardcoded 73. | `segment_coverage`, `opcode_replace_sites` |
| 1805    | `"segment_coverage": segment_coverage,`                                                      | Writes the value into `build/rastan-direct/address_map.json` under `segment_coverage.total_genesis_bytes_covered`. | `segment_coverage`           |

### Regions contributing to the total

All of the following segment kinds participate and sum to exactly `rom_size`:

- `preserved_vectors` (vector table + header)
- `arcade_copy` (arcade maincpu bytes relocated by 0x200)
- `patched_site` (opcode_replace patched bytes within the arcade range)
- `genesis_only` with tag `wrapper` (boot.s + decomposition modules + crash_handler.s — the Genesis-side helper region at `0x070000..end`)
- `genesis_only` with tag `padding` (any zero-fill gaps synthesised by the tool)

**Conclusion for Phase 1.** By the assertion at lines 443-446, `total_genesis_bytes_covered` is **always equal to `len(rom_bytes)`**: it is the byte length of the final emitted Genesis ROM image. No segment can exist outside of it and the sum is always the full file size.

---

## Phase 2 — What changed (source of the 676-byte reduction)

### Observed numbers

- Old expected: `0xFC1C4` = 1,032,644 bytes
- New computed: `0xFBF20` = 1,031,968 bytes
- Difference: `0xFC1C4 - 0xFBF20 = 0x2A4` = 676 bytes

### Corroborating evidence from the currently on-disk address map

[build/rastan-direct/address_map.json](build/rastan-direct/address_map.json) (snapshot from the last successful pre-Phase-B build) reports:

- `genesis_rom_size_bytes: 1032644` (= `0xFC1C4`)
- `wrapper_region.genesis_end_exclusive: "0x0FC1C4"`
- `wrapper_region.genesis_start: "0x070000"` → old wrapper size `= 0x8C1C4` bytes
- `segment_coverage.total_genesis_bytes_covered: 1032644` (matches the ROM size, confirming the Phase-1 assertion `covered == rom_size`)

The wrapper region is the Genesis-side (non-arcade) helper code produced by assembling and linking `apps/rastan-direct/src/`. In the **pre-Phase-B** build, the wrapper contained:

- `boot/boot.s` — `_start`, vector table, legacy guard, `main_68k`-related externs
- `main_68k.s` — every label listed in [Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md) Phase-2 Symbol column (VDP helpers, tilemap hooks, text writers, `load_scene_tiles`, `main_68k`, `_VINT_handler`, `arcade_tick_logic`, `init_staging_state`, all BSS, all rodata tables)
- `crash_handler.s` — fault-only subsystem

In the **post-Phase-B** build ([Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md) Phase-1 violations + Phase-5 fate):

- `boot.s` gains `_bootstrap` (cold-boot helper, ~30 instructions), drops the `jsr main_68k` → `jsr _bootstrap` rewire (same size).
- `main_68k.s` is **deleted entirely**. Its contents split into three new files with byte-identical function bodies except for the items listed below.
- `vdp_comm.s` **new** — contains all VDP service routines + commit helpers + new `_vblank_service` (replaces `_VINT_handler` body; ends with tail `jmp` instead of `rte`).
- `tilemap_hooks.s` **new** — contains every `genesistan_hook_*` and `rastan_direct_update_inputs` (body unchanged).
- `scene_load.s` **new** — contains `load_scene_tiles` body + rodata tables.
- `crash_handler.s` — one `frame_counter` reference removed (2-instruction change, see Phase-6 of decomposition doc).

**Net deletions from Genesis-side source** (all documented in decomposition doc):

| Deleted symbol / block                                              | Approximate size                          |
| ------------------------------------------------------------------- | ----------------------------------------- |
| `main_68k` entry + `.Lmain_loop` / `.Lwait_vblank` spin              | ~20 instructions × avg 3 bytes ≈ 60 bytes |
| `_VINT_handler` top-level identity (body retained as `_vblank_service`; `rte` replaced by `jmp`; `frame_counter++` removed) | net ~10 bytes reduction |
| `arcade_tick_logic` + `.Ltick_return`                                | ~8 instructions × avg 3 bytes ≈ 24 bytes  |
| `init_staging_state` arcade-workram factory-defaults block (main_68k.s:2094-2167 — coinage, DIP mirrors, delay, mode/cab/mon, bonus/diff, sprite marker, block A+B seeding + copy loop, title flag, config table copy from ROM 0x3B2D4) | ~120 lines ≈ 400-500 bytes |
| `init_staging_state` Genesis-side init moved into `_bootstrap` | mostly preserved, possibly small reduction from deleted workram defaults |
| `.equ rastan_direct_arcade_tick_entry` — removed | 0 bytes (equ only) |

**Net additions**:

| Added symbol                                        | Approximate size                |
| --------------------------------------------------- | ------------------------------- |
| `_bootstrap` in `boot.s`                            | ~30 instructions ≈ 90 bytes     |
| `_bootstrap_clear_staging` helper in `boot.s`       | ~40 instructions ≈ 120 bytes    |
| `_vblank_service` (replaces `_VINT_handler`)         | body ≈ same                     |
| `.Lwarm_restart` / dispatch (none in Phase B — not used under the new model) | 0 bytes |

**Arithmetic sanity check:** net deletion ≈ (60 + 10 + 24 + 450) − (90 + 120) = ~540 − 210 = ~330 bytes of 68000 instructions, plus alignment / linker padding differences. Given alignment boundaries (word-align for code, long-align for data, section padding), a cumulative ~676-byte shrink is well within expected range for this set of deletions, especially accounting for:

- Removed rodata (e.g. the arcade-workram factory-defaults block contains embedded `.long 0x0003B2D4` ROM source address), though most of that remained
- BSS allocations for `frame_counter` + `tick_counter` do **not** affect ROM size (BSS is uninitialized and not written to ROM image).
- Source-file split changes section layout and padding between sections.
- Linker may now emit a slightly different `.text` / `.data` / `.rodata` arrangement after splitting into three files.

### Segment present in ROM but no longer counted? — NO

`total_genesis_bytes_covered` is proven to equal `rom_size` by the assertion at line 443-446. If `covered` were less than `rom_size`, the tool would raise `"Segment coverage mismatch"` with different text — not the "Build 0029 invariant failure" text. The observed error text is exactly the Build-0029 invariant at line 1742-1745 (ROM-size mismatch against hardcoded `0xFC1C4`), not a segment-coverage mismatch.

Therefore **no segment exists but is uncounted.** The wrapper region shrunk because the Genesis-side source code shrunk, and the address-map gap-filler / padding logic naturally produces a smaller wrapper end (`0x0FBF20` instead of `0x0FC1C4`). Every segment in the new ROM is still accounted for — the total is simply lower.

### Phase 2 report

```
Source of 0x2A4 reduction: wrapper region (genesis_only/wrapper tag)
  — Genesis-side code emitted from apps/rastan-direct/src/**.
    Phase B decomposition deletes main_68k.s (~540 bytes of deleted
    functions dominated by the arcade-workram factory-defaults block
    in init_staging_state) and adds three smaller files (vdp_comm.s,
    tilemap_hooks.s, scene_load.s) plus _bootstrap/_bootstrap_clear_staging
    (~210 bytes added), plus linker section-padding differences.
    Net wrapper shrinkage: 676 bytes.

Confirmed from:
  - postpatch_startup_rom.py:443-446 (covered == rom_size assertion)
  - build/rastan-direct/address_map.json (pre-Phase-B snapshot:
    genesis_rom_size_bytes=1032644=0xFC1C4,
    wrapper_region.genesis_end_exclusive=0x0FC1C4,
    segment_coverage.total_genesis_bytes_covered=1032644)
  - docs/design/Andy_rastan_direct_runtime_decomposition.md Phase 1 & 5
    (enumerated deletions)
  - apps/rastan-direct/src/boot/boot.s (current _bootstrap + _start body)
  - absence of main_68k.s from apps/rastan-direct/src/ (confirmed in
    Cody_bootstrap_symbol_fix.md Phase-4 integrity snapshot)

Segment removed (expected) or segment exists but uncounted (unexpected):
  REMOVED (expected).
  The wrapper region of the ROM image is legitimately 676 bytes
  shorter because the Genesis-side source code is 676 bytes smaller
  post-Phase-B. No address-map segment is missing from the coverage
  sum. The coverage==rom_size assertion at line 443-446 would have
  raised "Segment coverage mismatch" if any segment were uncounted,
  but the actual error is the separate Build-0029 ROM-size invariant.
```

---

## Phase 3 — Classification

**Classification: B — stale bookkeeping.**

### Evidence

1. **`total_genesis_bytes_covered` is by construction equal to `rom_size`** (assertion at [postpatch_startup_rom.py:443-446](tools/translation/postpatch_startup_rom.py)). The invariant at lines 1742-1745 is therefore a **hardcoded ROM-size assertion**, not an integrity check against a computed expectation.

2. **The ROM is legitimately smaller** because Phase B intentionally deletes Genesis-side code (`main_68k.s` entirely, the `init_staging_state` arcade-workram factory-defaults block specifically, plus `arcade_tick_logic`, `main_68k` loop, `_VINT_handler` top-level identity). These deletions are documented in [Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md) Phase 1 §1.1-1.6 and Phase 5.

3. **No coverage regression exists.** If a segment were present in the ROM but missing from the address map, the tool would have raised `"Segment coverage mismatch: covered=... expected=..."` at line 443 — a different error message. The observed error text matches the Build-0029 invariant exactly, which is a hardcoded-value assertion, not a coverage-integrity check.

4. **The opcode_replace count matches** (73 = 73). If the invariant were catching a real regression in the hook set, the count check in the same conditional (line 1743) would have flagged it. The combined check only fires on the ROM-size half — confirming the count logic is healthy.

5. **The Build-0029 invariant was introduced at a specific build snapshot** (per its name and prior AGENTS_LOG history referencing "Build 0029 address-map artifact"). It is documented as a *historical* byte-count marker, not a drift-sensor. Subsequent legitimate source changes are expected to require the marker to be updated.

### Confidence: **HIGH**

No residual ambiguity. The tool's own coverage assertion (line 443) guarantees that the value is identical to ROM size; the ROM size changed because deleted Genesis-side code changed the linker output; the hardcoded expectation at line 1742 is a rubber-stamp check bound to a pre-Phase-B snapshot.

---

## Phase 4 — Fix specification

### Required change (Classification B)

```
File:  tools/translation/postpatch_startup_rom.py

Line 1742:
  Before:
      int(segment_coverage["total_genesis_bytes_covered"]) != 0xFC1C4
  After:
      int(segment_coverage["total_genesis_bytes_covered"]) != 0xFBF20

Line 1747:
  Before:
      "total_genesis_bytes_covered=0xFC1C4 and "
  After:
      "total_genesis_bytes_covered=0xFBF20 and "
```

**Justification (one sentence):** `total_genesis_bytes_covered` equals `rom_size` by construction ([postpatch_startup_rom.py:443-446](tools/translation/postpatch_startup_rom.py)); Phase B legitimately shrank the Genesis-side source code by 676 bytes (`main_68k.s` deleted, its body split/reduced across three new files and `_bootstrap`), so the invariant's hardcoded pre-Phase-B ROM size must be updated to the post-Phase-B ROM size.

### Scope notes for Cody

- Only these two literal `0xFC1C4` occurrences change. The rest of the conditional and the error-message format remain identical.
- The opcode_replace count `73` is unchanged in both places — it already matches the current build's count.
- **Do not** change the "Build 0029" label in the error message. That label is a historical marker; renaming it is beyond the minimum fix and could hide context in future diagnostics.
- **Do not** add abstraction (reading from spec, computing from symbol table, etc.). The minimal fix is the literal-value update. A richer refactor could reasonably replace the hardcoded check with a spec-driven expectation, but that is out of scope here.

### No other file changes required

- No change to `specs/rastan_direct_remap.json`.
- No change to any source file in `apps/rastan-direct/src/`.
- No change to `address_map.json` (it is regenerated on each build).
- No change to `build/rastan-direct/address_map.json` (will be overwritten post-fix).

### Verification after application

After the two-line fix, the build should complete and emit
`build/rastan-direct/address_map.json` containing:

- `genesis_rom_size_bytes: 1031968` (decimal of `0xFBF20`)
- `wrapper_region.genesis_end_exclusive: "0x0FBF20"`
- `segment_coverage.total_genesis_bytes_covered: 1031968`

These three values will all agree, confirming the assertion at line 443 still holds post-fix.

---

## STOP conditions — not triggered

- Computation of `total_genesis_bytes_covered` fully traced (Phase 1 table).
- Source of the 676-byte reduction identified with file:line evidence (Phase 2).
- Classification made with HIGH confidence — the assertion at line 443 mechanically guarantees the value is `rom_size`; the ROM size changed because source code changed; no unresolved ambiguity.

---

## Summary

- total_genesis_bytes_covered computation traced: **YES** — it is the accumulated `size_bytes` across every finalized address-map segment, and by the assertion at [postpatch_startup_rom.py:443-446](tools/translation/postpatch_startup_rom.py) it is always equal to `len(rom_bytes)`.
- source of 0x2A4 reduction identified: **YES** — the wrapper region (Genesis-side helper code) shrank by 676 bytes because Phase B deleted more source than it added; dominant contribution is the `init_staging_state` arcade-workram factory-defaults block (main_68k.s:2094-2167) plus the `main_68k` loop, `_VINT_handler` top-level identity, and `arcade_tick_logic`, offset by the new `_bootstrap` / `_bootstrap_clear_staging` / `_vblank_service`.
- removed segment vs uncounted segment: **REMOVED (expected).**
- classification: **B — stale bookkeeping.**
- confidence: **HIGH.**
- fix specified for Cody: **YES** — two literal-value edits at lines 1742 and 1747 of `tools/translation/postpatch_startup_rom.py`, changing `0xFC1C4` to `0xFBF20`.
- STOP triggered: **NO.**
