# Andy — Address Map Artifact Design (Build 0029)

**Status:** SPEC COMPLETE
**Scope:** Design-only. No code, no patcher edits.
**Build Context:** Build 0029, `rastan-direct` profile.

---

## 1. Summary

This document specifies a new build-time artifact
`build/rastan-direct/address_map.json` emitted by
`tools/translation/postpatch_startup_rom.py`. The artifact is the **single
authoritative record** of every address transformation applied by the patcher
in one build. It captures:

- Every region of the output Genesis ROM, classified by kind.
- Every byte of `arcade_pc ↔ genesis_rom_offset` mapping, recorded as
  contiguous segments with explicit start/end bounds (never as a formula).
- Every Genesis-only region (vectors, wrapper, padding, rom patches) that has
  no arcade origin.

Reverse lookup (`genesis_rom_offset → arcade_pc`) and forward lookup
(`arcade_pc → genesis_rom_offset`) operate **only** on this artifact. No
external formula is permitted; the artifact carries the mapping data in full.

The artifact **supplements** `rastan_direct_patch_manifest.json`. The manifest
remains unchanged.

---

## 2. Transformation Inventory (`postpatch_startup_rom.py`)

Every location in the patcher where an address transformation or ROM byte
placement occurs is listed. "Affects mapping" means this transformation changes
the `arcade_pc ↔ genesis_rom_offset` correspondence and therefore must emit one
or more segment records. "Byte-only" means it overwrites bytes already inside
a previously-recorded segment without altering that segment's mapping identity
(the segment's `kind` already permits the rewrite; e.g. a rewrite inside
`arcade_copy` does not change the arcade → genesis offset relationship for that
region, it just updates the byte contents).

| # | Transformation class | Location (line) | Inputs | Effect on address space | Currently in manifest? | Emits segment record? |
|---|----------------------|-----------------|--------|-------------------------|------------------------|-----------------------|
| 1 | `preserved_genesis_vectors` snapshot | 631 | `rom_bytes[0:0x400]` pre-copy | Captures Genesis vector/header bytes to be restored after relocation. | Implicit (`preserved_genesis_vector_table`). | `preserved_vectors` segment at `[0x000000, 0x000400)`. |
| 2 | `shift_replacements` Pass A (variable-length patches) | 638–700 | `spec.shift_replacements`, disasm | Reshifts maincpu layout; `shift_deltas` list. | No (not in manifest for rastan_direct). | Zero or many `patched_site` segments with per-site `arcade_start/_end_exclusive`, `genesis_start/_end_exclusive` (lengths may differ). Also updates cumulative shift table used by later segments. |
| 3 | `ensure_rom_size` / `ensure_size_at_least` | 702, 731, 1125, 1141 | target size | Grows ROM buffer; zero-fills new tail. | No. | Any new tail byte covered by a `genesis_only/padding` or explicit segment; recorded at emit time. |
| 4 | `whole_maincpu_copy` | 711–739 | `source_start/end`, `dest_start` | Copies arcade `maincpu.bin[source_start:source_end]` → ROM `[dest_start, dest_end)`. Defines the base arcade → genesis linear mapping. | Yes (`whole_maincpu_copy` block). | One **tentative** `arcade_copy` segment covering `[dest_start, dest_end)`. Later transformations carve it up. |
| 5 | `copied_ranges` identity overlays | 750–768 | `spec.copied_ranges` when `keep_identity_overlays` | Identity copies at arcade PCs (unused by rastan_direct). | Yes (`copied_ranges`). | `arcade_copy` segment per entry (at arcade PC = genesis offset). |
| 6 | `rom_absolute_call_relocation` | 770–795 | opcode set, scan windows | Rewrites absolute 32-bit operands of `0x4EB9` / `0x4EF9` / etc. inside the arcade copy to point to the relocated addresses. | Yes (in `address_rewrites` / `rom_absolute_call_relocation`). | None (byte-only inside existing `arcade_copy` segment; operand values do not change the arcade_pc↔genesis_rom_offset map). |
| 7 | `absolute_rewrite_groups` | 799–826 | `spec.absolute_rewrite_groups` | Rewrites long pointer values (constants). | Yes (in `address_rewrites`). | None (byte-only). |
| 8 | `window_rewrite_rules` | 828–887 | `spec.window_rewrite_rules` | Rewrites 32-bit values within arcade windows. | Yes (in `address_rewrites`). | None (byte-only). |
| 9 | `verbatim_restores` | 889–895 | `spec.verbatim_restores` | Copies original bytes back over a window. | Implicit (spec only). | None (byte-only inside `arcade_copy`). |
| 10 | `shim_jumps` | 897–917 | `spec.shim_jumps` | Overwrites an arcade-PC window with an absolute JMP to a Genesis symbol. | Yes (in `address_rewrites`). | `genesis_only/shim_jump` segment carved out of `arcade_copy` at the shim window (arcade identity gone — the bytes now name a Genesis target). |
| 11 | `absolute_long_pointer_tables` | 919–955 | `spec.absolute_long_pointer_tables` | Rewrites table entries to relocated addresses. | Yes (in `address_rewrites`). | None (byte-only). |
| 12 | `opcode_replace` | 957–994 | `spec.opcode_replace[i]` | Overwrites `len(original_bytes)` at `arcade_pc + relocation + shift`. `len(original)==len(replacement)`. | Yes (in `address_rewrites` per entry). | `patched_site` segment per entry with `arcade_start`, `arcade_end_exclusive`, `genesis_start`, `genesis_end_exclusive`, `original_bytes`, `replacement_bytes`, `note`. Carves out of `arcade_copy`. |
| 13 | `rom_opcode_replace` | 998–1027 | `spec.rom_opcode_replace[i]` | Overwrites at fixed `rom_pc` (no arcade source). | Yes (in `address_rewrites`). | `genesis_only/rom_patch` segment at `[rom_pc, rom_pc+len)`. If it falls inside `arcade_copy`, that range is carved out (arcade identity removed). |
| 14 | `deferred_operand_entries` Pass B | 1031–1071 | `deferred_operand_entries` from Pass A | Writes final 32-bit operand into a previously-placed template. | Yes (entry kind `relocate_after_shift_operand`). | None (byte-only inside a patched_site emitted by transformation 2 — operand is inside that site). |
| 15 | `palette_pre_conversion` | 1100–1132 | symbol `genesistan_palette_rom_table` | Writes 4096 bytes of palette data at the symbol's ROM offset. | Yes (in `address_rewrites`). | `genesis_only/palette_table` segment covering `[palette_rom_sym, palette_rom_sym + 0x1000)` if the symbol exists. (Symbol is always inside wrapper region; no arcade overlap.) |
| 16 | `workram_anchor` | 1138–1150 | symbol `genesistan_arcade_workram_words` | Writes 4 bytes at fixed ROM `0x10C000`. | Yes (in `address_rewrites`). | `genesis_only/workram_anchor` segment `[0x10C000, 0x10C004)` if the symbol exists. |
| 17 | `generated_stubs` and `patch_startup_vectors` | 1172–1197 | `spec.generated_stubs`, `_reset_entry` | Non-rastan_direct profile only. | Yes (in `normal_result_stub`/`test_result_stub`/`startup_vectors`). | `genesis_only/generated_stub` segments when applied. |
| 18 | `preserved_genesis_vectors` restore | 748 (non-direct) / 1206 (direct) | snapshot from #1 | Restores Genesis vectors over the arcade-copied bytes. | Implicit. | Converts `[0x000000, 0x000400)` from `arcade_copy` to `preserved_vectors`. Always executed. |
| 19 | `update_genesis_checksum` | 427–436, 1208 | full ROM | Writes 2-byte checksum at `0x18E:0x190`. | Yes (`checksum`). | None (byte-only inside `preserved_vectors`). |

**Transformation class count: 19.**

Transformations that **define or alter** the arcade ↔ genesis mapping (emit
segment records): **#1, #2, #4, #5, #10, #12, #13, #15, #16, #17, #18** — 11 classes.

Transformations that are **byte-only** (no mapping change; recorded as edit
entries within an existing segment but do not create new segments): #3, #6, #7,
#8, #9, #11, #14, #19 — 8 classes.

---

## 3. Artifact Schema — `build/rastan-direct/address_map.json`

Top-level object (all keys mandatory; no optional keys; additional keys are an
error):

```jsonc
{
  "schema_version": 1,
  "build_inputs": {
    "variant": "<string>",
    "patcher_profile": "<string>",
    "spec_path": "<absolute path>",
    "manifest_path": "<absolute path>",
    "rom_path": "<absolute path>",
    "symbols_path": "<absolute path>",
    "maincpu_path": "<absolute path>"
  },
  "genesis_rom_size_bytes": <int>,
  "relocation_delta": "0xNNNNNN",
  "arcade_source_start": "0xNNNNNN",
  "arcade_source_end_exclusive": "0xNNNNNN",
  "wrapper_region": {
    "genesis_start": "0x00070000",
    "genesis_end_exclusive": "0xNNNNNN"
  },
  "segments": [ /* strictly ordered; see §3.1 */ ],
  "segment_coverage": {
    "total_genesis_bytes_covered": <int>,
    "gaps": [],
    "overlaps": []
  },
  "shift_deltas": [ [ "0xNNNNNN", <int_delta> ], ... ]
}
```

Invariants enforced at emit time (the patcher aborts the build if any fails):

- `segments` is sorted by `genesis_start` strictly ascending.
- `segments[0].genesis_start == 0`.
- `segments[-1].genesis_end_exclusive == genesis_rom_size_bytes`.
- For every adjacent pair, `segments[i].genesis_end_exclusive == segments[i+1].genesis_start` (no gaps).
- No two segments overlap.
- `segment_coverage.total_genesis_bytes_covered == genesis_rom_size_bytes`.
- `segment_coverage.gaps == []` and `segment_coverage.overlaps == []`.

### 3.1 Segment record types

Every segment object has these common fields:

```jsonc
{
  "genesis_start": "0xNNNNNN",
  "genesis_end_exclusive": "0xNNNNNN",
  "size_bytes": <int>,
  "kind": "arcade_copy | patched_site | preserved_vectors | genesis_only"
}
```

Kind-specific fields:

**`arcade_copy`** — identity mapping between arcade source and Genesis ROM.
```jsonc
{
  "kind": "arcade_copy",
  "arcade_start": "0xNNNNNN",
  "arcade_end_exclusive": "0xNNNNNN",
  "source": "whole_maincpu_copy | copied_range:<name>",
  "identity_offset": <int>
  // Invariant: arcade_end_exclusive - arcade_start == genesis_end_exclusive - genesis_start
  // Invariant: genesis_start - arcade_start == identity_offset (constant over segment)
}
```

**`patched_site`** — an `opcode_replace` or `shift_replacement` target.
```jsonc
{
  "kind": "patched_site",
  "arcade_start": "0xNNNNNN",
  "arcade_end_exclusive": "0xNNNNNN",
  "origin": "opcode_replace | shift_replacement",
  "original_bytes": "<hex>",
  "replacement_bytes": "<hex>",
  "note": "<string>",
  "shift_delta": <int>   // genesis length - arcade length, >=0 for opcode_replace (always 0 in this profile)
}
```

**`preserved_vectors`** — Genesis-native vectors/header; arcade bytes at the
same offsets (if any) are not present in the Genesis ROM.
```jsonc
{
  "kind": "preserved_vectors",
  "tag": "genesis_vectors_header"
}
```

**`genesis_only`** — any Genesis-native region with no arcade origin.
```jsonc
{
  "kind": "genesis_only",
  "tag": "wrapper | padding | shim_jump | rom_patch | generated_stub | palette_table | workram_anchor"
}
```

Kind-specific invariants:
- `arcade_copy`: `arcade_end_exclusive - arcade_start == genesis_end_exclusive - genesis_start`.
- `patched_site`: `len(original_bytes)/2 == arcade_end_exclusive - arcade_start` and
  `len(replacement_bytes)/2 == genesis_end_exclusive - genesis_start`.
- `preserved_vectors` and `genesis_only` have no arcade fields.

### 3.2 No approximation fields

The schema contains **no** formula, shortcut, range-hint, or approximation
field. Lookups use segment data verbatim; `identity_offset` is a recorded fact,
not a formula parameter.

---

## 4. Emission Point Design

For each transformation from §2 that affects mapping, the patcher appends
segment records to an in-memory list `segments`. After all transformations are
applied and before the final write, the list is sorted by `genesis_start` and
the invariants in §3 are checked. The artifact is then serialized and written.

| Transformation | Emission point | Record emitted |
|----------------|----------------|----------------|
| #1 `preserved_genesis_vectors` snapshot | After restore at line 748 or 1206. | Append `preserved_vectors` segment `[0x000000, 0x000400)`. Overrides any prior `arcade_copy` covering that range. |
| #2 `shift_replacements` Pass A | Immediately after the for-loop at 686 resolves `_resolved_rep`. | Append `patched_site` with `origin="shift_replacement"` per entry. Deferred templates record length of `replacement_template + zero operand`. |
| #4 `whole_maincpu_copy` | Immediately after line 732 (the slice write). | Append one tentative `arcade_copy` segment `[dest_start, dest_end)` with `identity_offset = dest_start - source_start`. |
| #5 `copied_ranges` identity | Inside the for-loop at 750–768 when `keep_identity_overlays` is true. | Append one `arcade_copy` segment per entry with `identity_offset = 0`. |
| #10 `shim_jumps` | Inside the for-loop at 897–917 after `rom_bytes[start:end]` write. | Append `genesis_only` with `tag="shim_jump"`. |
| #12 `opcode_replace` | Inside the for-loop at 957–994 after the slice write at line 985. | Append `patched_site` with `origin="opcode_replace"`. Data available: `arcade_pc`, `rom_pc`, `expected.hex()`, `new_bytes.hex()`, `note`. |
| #13 `rom_opcode_replace` | Inside the for-loop at 998–1027 after the slice write. | Append `genesis_only` with `tag="rom_patch"`. |
| #14 `deferred_operand_entries` Pass B | After the for-loop at 1031–1071. | No new segment. Patched_site from #2 already covers operand bytes; deferred operand is a byte-only edit inside it. |
| #15 `palette_pre_conversion` | Inside the if-block at 1100–1132 after line 1126. | Append `genesis_only` with `tag="palette_table"` and size `_PALETTE_ENTRIES * 2`. |
| #16 `workram_anchor` | Inside the if-block at 1138–1150 after line 1143. | Append `genesis_only` with `tag="workram_anchor"` size 4. |
| #17 `generated_stubs` | After lines 1187–1195 in non-direct profile. | Append `genesis_only` with `tag="generated_stub"` per stub. |
| Wrapper region | Once, just before segment assembly finalization (no specific transformation — derived from link-script layout, see §6). | Append `genesis_only` with `tag="wrapper"` spanning the wrapper extent. |
| Padding between arcade_copy end and wrapper start | Derived from gap in accumulated segments. | Append `genesis_only` with `tag="padding"`. |

### 4.1 Segment assembly pass (deferred)

After all transformations run, the patcher executes a finalization pass that
collapses the emitted segment list into the final canonical form:

1. Start with the tentative `arcade_copy` segment from #4.
2. For every `patched_site` with `origin=opcode_replace`: carve it out of the
   containing `arcade_copy`. The two surrounding `arcade_copy` pieces inherit
   `identity_offset` and compute their own `arcade_start/_end` from
   `genesis_start/_end - identity_offset`.
3. For every `patched_site` with `origin=shift_replacement` and non-zero shift:
   carve out and propagate shift into subsequent `arcade_copy` piece
   `identity_offset` values (consult `shift_deltas`).
4. For every `genesis_only` segment whose range intersects an `arcade_copy`
   piece: carve the intersection out (including #10 shim_jumps, #13 rom_patch,
   #15 palette_table if overlapping, #16 workram_anchor, #17 generated_stub).
5. Apply `preserved_vectors` as the final override for `[0x000000, 0x000400)`.
6. Fill any remaining gaps with `genesis_only` `tag="padding"`.
7. Sort, validate invariants from §3, emit.

Each of these steps is a simple interval operation. Every byte of the output
ROM belongs to exactly one segment after finalization.

---

## 5. Output File Design

| Property | Value |
|----------|-------|
| Path | `build/rastan-direct/address_map.json` |
| Written by | `tools/translation/postpatch_startup_rom.py` immediately after the existing `manifest_path.write_text(...)` at line 1339. |
| Replaces existing manifest? | **No.** The existing manifest remains verbatim. |
| Supplements | Yes — the map is a separate, additional file. |
| Consumed by | `tools/addr_lookup.py` (see `docs/design/Andy_address_lookup_tool_design.md`). No existing consumer is affected. |
| Failure mode | If any §3 invariant fails, the patcher raises `RuntimeError` and the build aborts. |

The path is adjacent to the manifest so a single build directory holds all
address artifacts for the build.

---

## 6. Wrapper Region Boundaries (Evidence)

Source files consulted:
- `apps/rastan-direct/link.ld` — linker script.
- `apps/rastan-direct/out/symbol.txt` — final symbol table.
- `apps/rastan-direct/Makefile:71–80` — build pipeline invocation.

`apps/rastan-direct/link.ld` declares three sections:

```
. = 0x000000;
.text.boot : { *(.text.boot) }          ← boot section starts at 0x000000; _start lives at 0x000202

. = 0x00070000;
.text.wrapper : { *(.text .text.*) *(.rodata .rodata.*) *(.data .data.*) }

.bss 0xFF4000 (NOLOAD) : { ... }         ← BSS, NOT in ROM
```

Therefore the wrapper region begins at exactly `0x00070000`.

End of wrapper comes from the last ROM-resident symbol in `symbol.txt`:

```
000fb7c1 T z80_driver_end
```

`z80_driver_end` is the final byte-address of the embedded Z80 driver (the
wrapper's highest ROM-resident content). Observed built ROM size is
`wc -c apps/rastan-direct/dist/rastan_direct_video_test.bin = 1030084` bytes
= `0x000FB944`. Therefore:

- **Wrapper region `[0x00070000, 0x000FB944)`** for this build.

The wrapper's upper bound is variable (depends on wrapper code size) — the
artifact MUST record it as `wrapper_region.genesis_end_exclusive =
genesis_rom_size_bytes` on every build. The patcher computes this after all
ROM writes complete (line 1209 `rom_path.write_bytes(rom_bytes)`) and records
`genesis_rom_size_bytes = len(rom_bytes)` at that moment.

The `0x00070000` lower bound is stable because `link.ld` is version-controlled
and checked by the build. If `link.ld` is changed the emit-time invariant
check `segments.find(kind==genesis_only, tag=="wrapper").genesis_start ==
0x00070000` must fail and force a design review. This guard is part of the
artifact's consistency checks.

---

## 7. Lookup Algorithms

Both algorithms operate on the sorted, gap-free `segments` list from §3.1.
Binary search for `genesis_rom_offset` is permitted because segments are
sorted and non-overlapping. For `arcade_pc` lookup, a separate sorted-by-
`arcade_start` index is built from the segments that have arcade fields
(`arcade_copy` + `patched_site`); this index is purely derived data and is
not stored in the artifact.

### 7.1 Forward: `arcade_pc → genesis_rom_offset`

Input: `arcade_pc` (int).

1. Binary-search the arcade-indexed segment list for a segment `s` where
   `s.arcade_start <= arcade_pc < s.arcade_end_exclusive`.
2. If no segment is found → return
   `{kind: UNKNOWN, reason: "arcade_pc not in any arcade_copy or patched_site segment"}`.
3. If `s.kind == arcade_copy`:
   `genesis_rom_offset = s.genesis_start + (arcade_pc - s.arcade_start)`.
   Return `{kind: ARCADE_COPY, genesis_rom_offset, segment: s}`.
4. If `s.kind == patched_site`:
   - If `s.shift_delta == 0` and `arcade_pc == s.arcade_start`:
     return `{kind: PATCHED_SITE, genesis_rom_offset: s.genesis_start, segment: s}`.
   - Else: return `{kind: PATCHED_SITE_INTERIOR, genesis_rom_offset: s.genesis_start + (arcade_pc - s.arcade_start) if shift_delta==0 else UNKNOWN_INTERIOR, segment: s}`. The `patched_site` replacement bytes are a semantic unit; interior offsets have no meaningful `genesis_rom_offset` unless the patch preserves byte-for-byte arcade positions (which `opcode_replace` entries do by enforcing equal lengths). For `shift_replacement` patches with non-zero `shift_delta`, there is **no interior mapping** — return `UNKNOWN_INTERIOR`.

### 7.2 Reverse: `genesis_rom_offset → arcade_pc`

Input: `genesis_rom_offset` (int).

1. Reject if `genesis_rom_offset < 0 or >= genesis_rom_size_bytes` → return
   `{kind: UNKNOWN, reason: "genesis_rom_offset out of ROM bounds"}`.
2. Binary-search `segments` for the segment `s` where
   `s.genesis_start <= genesis_rom_offset < s.genesis_end_exclusive`. Exactly
   one segment must match (enforced by §3 invariants).
3. Switch on `s.kind`:
   - `arcade_copy`:
     `arcade_pc = s.arcade_start + (genesis_rom_offset - s.genesis_start)`.
     Return `{kind: ARCADE_COPY, arcade_pc, segment: s}`.
   - `patched_site`:
     - If `genesis_rom_offset == s.genesis_start`:
       Return `{kind: PATCHED_SITE, arcade_pc: s.arcade_start, segment: s}`.
     - Else (interior):
       - If `s.shift_delta == 0`: return
         `{kind: PATCHED_SITE_INTERIOR, arcade_pc: s.arcade_start + (genesis_rom_offset - s.genesis_start), segment: s}`.
       - Else: return
         `{kind: PATCHED_SITE_INTERIOR, arcade_pc: UNKNOWN_INTERIOR, segment: s}`.
   - `preserved_vectors`: return
     `{kind: PRESERVED_VECTORS, arcade_pc: null, segment: s}`.
   - `genesis_only`: return
     `{kind: GENESIS_ONLY, tag: s.tag, arcade_pc: null, segment: s}`.

### 7.3 Non-ROM address classification

Input: `addr` (int, arbitrary).

Non-ROM classification runs **before** 7.1/7.2 only if the caller explicitly
requests auto-detection. It does **not** consult `segments` and does **not**
attempt arcade_pc mapping. It uses only the enumerated hardware-address ranges
proven in `docs/design/Andy_address_lookup_tool_design.md` §5:

1. If `addr ∈ [0xC00000, 0xC0FFFF]` → `HW_ADDRESS / PC080SN` (sub-region by
   range as per existing design doc). Terminal.
2. If `addr ∈ {0xC20000, 0xC20002}` → `HW_ADDRESS / PC080SN / YSCROLL`. Terminal.
3. If `addr ∈ {0xC40000, 0xC40002}` → `HW_ADDRESS / PC080SN / XSCROLL`. Terminal.
4. If `addr ∈ [0xD00000, 0xD03FFF]` → `HW_ADDRESS / PC090OJ / SPRITE_RAM`. Terminal.
5. If `addr ∈ [0x380000, 0x38000F]` → `HW_ADDRESS / TC0040IOC`. Terminal.
6. If `addr ∈ [0xFF0000, 0xFFFFFF]` → `GENESIS_WRAM`. Terminal.
7. Else if `addr ∈ [0, genesis_rom_size_bytes)`: fall through to 7.2 (ROM space).
8. Else: `UNKNOWN / out_of_known_space`. Terminal.

No case in 7.3 attempts `arcade_pc` mapping. Classification is final.

---

## 8. Worked Validation Examples

For each, the artifact snippet used is a minimal excerpt of the segment list
under the schema from §3.

### Example 1 — `arcade_pc: 0x055968` (known patched site)

Relevant segment (emitted from `opcode_replace[0]` in spec):
```jsonc
{
  "kind": "patched_site",
  "genesis_start": "0x055B68",
  "genesis_end_exclusive": "0x055B92",
  "size_bytes": 42,
  "arcade_start": "0x055968",
  "arcade_end_exclusive": "0x055992",
  "origin": "opcode_replace",
  "original_bytes": "206d10a0...",
  "replacement_bytes": "4eb900070134...",
  "note": "Route PC080SN BG strip producer ...",
  "shift_delta": 0
}
```
Forward lookup (§7.1) finds this segment; `arcade_pc == arcade_start` → returns
`{kind: PATCHED_SITE, genesis_rom_offset: 0x055B68}`. One segment, one path.

### Example 2 — `arcade_pc: 0x03C3FE` (unpatched arcade code)

Segments include two `arcade_copy` pieces adjacent to the `0x03AD44` patched
site (`arcade_pc 0x03AD44` is the BG fill hook site per spec line 129). The
`arcade_copy` piece containing `0x03C3FE` has:
```jsonc
{
  "kind": "arcade_copy",
  "genesis_start": "0x03AD78",         // 0x03AD44+6+0x200 after site carve
  "genesis_end_exclusive": "0x03ADFE", // up to next patched site
  "arcade_start": "0x03AD78",
  "arcade_end_exclusive": "0x03ADFE",
  "source": "whole_maincpu_copy",
  "identity_offset": "0x000200"
}
```
A later `arcade_copy` piece covers `[0x03AE22+0x200, <next site>)` and so on,
eventually covering `arcade_pc 0x03C3FE`. Forward lookup returns
`genesis_rom_offset = arcade_pc + identity_offset = 0x03C3FE + 0x000200 = 0x03C5FE`.
`{kind: ARCADE_COPY, genesis_rom_offset: 0x03C5FE}`. One segment, one path.

### Example 3 — `genesis_rom_offset: 0x000100` (Genesis vectors region)

Segment: `{kind: preserved_vectors, genesis_start: 0x000000, genesis_end_exclusive: 0x000400, tag: "genesis_vectors_header"}`.
Reverse lookup returns `{kind: PRESERVED_VECTORS, arcade_pc: null}`. No arcade
mapping is attempted. One segment, one path.

### Example 4 — `genesis_rom_offset: 0x0007002A` (wrapper — `_VINT_handler`)

Exact address from `apps/rastan-direct/out/symbol.txt`:
`0007002a T _VINT_handler`. Lies inside the wrapper segment
`{kind: genesis_only, genesis_start: 0x00070000, genesis_end_exclusive: 0x000FB944, tag: "wrapper"}`.
Reverse lookup returns `{kind: GENESIS_ONLY, tag: "wrapper", arcade_pc: null}`.
One segment, one path. Value `0x000FB944` is the proven wrapper end
(§6 evidence: observed ROM size `wc -c = 1030084`).

### Example 5 — `runtime_genesis_pc: 0xC09EA0` (hardware address)

Classification 7.3 step 1: `0xC09EA0 ∈ [0xC00000, 0xC0FFFF]` →
`HW_ADDRESS / PC080SN`. Sub-range: `[0xC08000, 0xC0BFFF]` → `FG_TILEMAP`.
Terminal. The artifact's `segments` list is **not** consulted because the
address is not in `[0, genesis_rom_size_bytes)`. No `arcade_pc` mapping is
attempted, consistent with Rule 13. Result:
`{kind: HW_ADDRESS, chip: "PC080SN", region: "FG_TILEMAP", base: 0xC08000, offset_from_base: 0x1EA0}`.

---

## 9. Impact on Existing Manifest

| Question | Answer |
|----------|--------|
| Does the address-map artifact replace the existing manifest? | **No.** |
| Does `rastan_direct_patch_manifest.json` need to be modified? | **No.** |
| Are there existing consumers of the manifest that would be affected? | **No.** `addr_lookup.py` (design in progress) is a new consumer of the new artifact; the manifest continues to serve its existing role (verification logs, test harnesses reading `address_rewrites`). |
| Relation between artifacts | The manifest is the **edit log** (what was changed). The address map is the **mapping state** (what the output ROM means for each byte). They are complementary. |

Classification: **supplement**.

---

## 10. What Cody Must Implement (Zero Design Decisions Remaining)

1. Extend `tools/translation/postpatch_startup_rom.py` with an in-memory
   `segments: list[dict]` list and a module-level helper
   `_append_segment(record)` that appends to it and sets an internal sequence
   number for debugging.
2. At every emission point in §4 (column "Record emitted"), append the exact
   record with the fields specified in §3.1. No fields added, no fields omitted.
3. After `rom_path.write_bytes(rom_bytes)` (line 1209) and before the
   `manifest_path.write_text` call (line 1339), execute the finalization pass
   from §4.1 (interval-carve steps 1–7).
4. Validate every invariant listed in §3 (including the lower-bound wrapper
   guard from §6). On any failure raise `RuntimeError` with a clear message.
5. Serialize `segments` plus top-level fields per §3 to
   `build/rastan-direct/address_map.json`. Path is derived from
   `manifest_path.with_name("address_map.json")`.
6. Do not alter any manifest writer code or any existing rewrite-log entry.
7. No new CLI flags. No new spec keys.
8. Unit-free correctness requirement: for Build 0029 the resulting
   `segments` MUST satisfy `total_genesis_bytes_covered == 0xFB944` and the
   46 `patched_site` segments MUST correspond 1:1 to the 46
   `rewrite_log` entries with `kind=="opcode_replace"`.

The address-lookup tool `tools/addr_lookup.py`
(`docs/design/Andy_address_lookup_tool_design.md`) must be updated after
Cody finishes, to read from `address_map.json` instead of deriving the
mapping from the manifest. That update is scoped in the lookup-tool design
doc, not here.

---

## 11. Next-Step Impact

- Replaces the `+0x200` shortcut in the current lookup tool with an
  authoritative segment table — removes the "formula-valid-until-shift-
  replacements-appear" guard rail.
- Unblocks Cody audits that require precise Genesis-offset → arcade-function
  resolution across future builds that introduce `shift_replacements`,
  `rom_opcode_replace`, `shim_jumps`, or new generated stubs.
- Provides the single artifact that encodes "what does this byte of the
  Genesis ROM mean?" — a primitive needed before any future automated
  translation-rule audit.

---

## 12. STOP Conditions

None triggered.

- All 19 transformation classes in `postpatch_startup_rom.py` are represented
  in the schema (§3) with an emission point (§4) and a mapping impact (§2).
- Wrapper boundaries are proven from `link.ld` (lower bound `0x00070000`,
  hard-coded in linker script) and the observed ROM size (upper bound equals
  `genesis_rom_size_bytes`, emitted at build time).
- Every validation case (§8) resolves through exactly one segment under the
  schema defined in §3 and the algorithms defined in §7.
