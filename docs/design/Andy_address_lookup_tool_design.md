# Andy — Address Lookup Tool Design (Build 0029)

**Status:** SPEC COMPLETE
**Scope:** Design-only. No code or scripts produced.
**Build Context:** Build 0029, `rastan-direct`.

---

## 1. Summary

This document specifies `tools/addr_lookup.py`: a reverse lookup tool that maps any
`runtime_genesis_pc` or `genesis_rom_offset` back to its corresponding `arcade_pc`
(or classifies the address as Genesis-only / hardware-memory / unknown).

The tool is **pure analysis** — it reads two authoritative build artifacts
(`specs/rastan_direct_remap.json`, `build/rastan-direct/rastan_direct_patch_manifest.json`)
plus `apps/rastan-direct/out/symbol.txt`. It never modifies source, spec, or ROM.

---

## 2. Address Space Definitions

| Label | Definition | Authoritative source |
|-------|------------|----------------------|
| `arcade_pc` | Offset inside the original Taito arcade `maincpu` ROM image (`build/regions/maincpu.bin`), range `0x000000–0x05FFFF`. | `build/maincpu.disasm.txt`, `specs/rastan_direct_remap.json` `opcode_replace[].arcade_pc` |
| `genesis_rom_offset` | Byte offset inside the built Genesis cartridge image `apps/rastan-direct/dist/rastan_direct_video_test.bin`. | `build/rastan-direct/rastan_direct_patch_manifest.json` `whole_maincpu_copy.dest_start`, `opcode_replace[].rom_pc` |
| `runtime_genesis_pc` | 68k program counter observed at runtime (BlastEm/Exodus/MAME Genesis) during execution. | Equal to `genesis_rom_offset` for code executing from cart ROM (Genesis cart maps 1:1 at `0x000000`). Confirmed by `tools/translation/verify_rastan_direct_boot_guard.py:11` (`EXPECTED_RESET_VECTOR = 0x00000202` — reset jumps to ROM offset `0x000202` directly as PC). |

**Equality claim, proven:**
`runtime_genesis_pc == genesis_rom_offset` for any PC inside the cart ROM range.
Evidence: Genesis Mode-1 cart mapping is identity at `0x000000–0x3FFFFF`; the reset
vector `0x00000202` in `verify_rastan_direct_boot_guard.py:11` is used as both the
ROM offset of the start prologue (`EXPECTED_START_PROLOGUE_OFFSET = 0x000202`,
line 16) and the initial PC. No MMU, no shadow, no bank switching is configured.

---

## 3. Manifest Coverage (Evidence)

- `build/rastan-direct/rastan_direct_patch_manifest.json` contains the key fields
  `arcade_pc` and `rom_pc` on every `opcode_replace` entry (example at line 48–49
  of the manifest: `"arcade_pc": "0x055968"`, `"rom_pc": "0x055B68"`).
- Count of `"rom_pc"` fields in manifest: **46**.
- Count of `"arcade_pc"` fields in manifest: **46** (plus 2 `opcode_replace` kind
  markers outside the per-entry list; these refer to the same 46 entries).
- Count of entries in `specs/rastan_direct_remap.json` `opcode_replace` array: **46**
  (verified by `"opcode_replace_count": 46` at line 383).

**Conclusion:** manifest is fully 1:1 with spec. The manifest is the authoritative
lookup source for every patched arcade PC.

---

## 4. Mapping Formula for Unpatched Regions

From `tools/translation/postpatch_startup_rom.py:978`:

```python
rom_pc = arcade_pc + relocation_delta + accumulated_shift_before(arcade_pc, shift_deltas)
```

- `relocation_delta` is derived at line 715:
  `relocation_delta = dest_start - source_start` — where `dest_start = 0x000200`
  and `source_start = 0x000000` (per manifest `whole_maincpu_copy` block, lines
  18–23). **`relocation_delta = 0x000200`.**
- `shift_deltas` is built from `shift_replacements`. In `specs/rastan_direct_remap.json`,
  there is **no `shift_replacements` key at all** (verified by full-file grep; the
  only top-level arrays are `copied_ranges`, `opcode_replace`, `rom_opcode_replace`
  (empty, line 381), and `expectations`). Therefore `shift_deltas == []` and
  `accumulated_shift_before(x, [])` returns `0` for every `x`.

**Proven formula for the current build:**

```
genesis_rom_offset = arcade_pc + 0x000200            (arcade_pc ∈ [0x000000, 0x060000))
arcade_pc          = genesis_rom_offset - 0x000200   (genesis_rom_offset ∈ [0x000200, 0x060200))
```

This formula is constant across the entire unpatched region and is directly
invertible. It applies only inside the arcade-copied window.

---

## 5. Gap Analysis — Addresses That Cannot Be Resolved to an `arcade_pc`

| Region | Address range | Classification | Reason |
|--------|---------------|----------------|--------|
| Genesis reset/vector/header/bootstrap | `0x000000–0x0001FF` | `GENESIS_ONLY/vectors` | Preserved by `preserved_low_rom_bootstrap` (manifest lines 41–44). No arcade equivalent. |
| Genesis wrapper / hook bodies | `0x00070000–0x0007FFFF` (per `verify_rastan_direct_boot_guard.py:19–20`, `EXPECTED_WRAPPER_LOW_BOUND/HIGH_BOUND`) | `GENESIS_ONLY/wrapper` | Genesis-native 68k code (hooks, staged buffer maintainers, VINT handler). No arcade source. |
| Inter-region padding | `0x060200–0x06FFFF` (between arcade copy end and wrapper base) | `GENESIS_ONLY/padding` | Space between the end of the relocated arcade image and the wrapper base. Non-executable except via bug. |
| PC080SN tilemap / rowscroll / scroll regs | `0xC00000–0xC0FFFF`, `0xC20000`, `0xC40000` | `HW_ADDRESS/PC080SN` | Arcade hardware memory destinations, not code PCs. Cannot have an `arcade_pc`. |
| PC090OJ sprite RAM | `0xD00000–0xD03FFF` | `HW_ADDRESS/PC090OJ` | Arcade hardware memory destination. Not code. |
| TC0040IOC | `0x380000–0x38000F` | `HW_ADDRESS/TC0040IOC` | Arcade I/O register. Not code. |
| Genesis WRAM / staged buffers | `0xFF0000–0xFFFFFF` | `GENESIS_WRAM` | RAM used by hooks (staged tilemaps, scroll mirrors, dirty flags). Not code. |
| Genesis VDP ports | `0xC00000–0xC0001F` for VDP in Genesis mode | *N/A in rastan-direct* | The arcade memory map overlaps this range and is translated by hooks; the tool must flag `0xC00000–0xC0FFFF` as `HW_ADDRESS/PC080SN`, because in this project those are arcade semantics not Genesis VDP semantics. |

**Special case — `0xC09EA0`**: this is a hardware memory address inside
`0xC08000–0xC0BFFF` (PC080SN FG tilemap). It is **not a code PC** and has no
`arcade_pc` mapping. The tool returns
`HW_ADDRESS/PC080SN/FG_TILEMAP` with offset `0x1EA0` from the FG tilemap base
`0xC08000`. This case is documented in §8 worked example 3.

---

## 6. Complete Lookup Algorithm (Ordered, Non-Overlapping)

Input: `(addr: u32, space: {arcade_pc | genesis_rom_offset | runtime_genesis_pc | auto})`

Normalization:
- If `space == runtime_genesis_pc`, treat as `genesis_rom_offset` (§2 equality proof).
- If `space == auto`, apply heuristic in §7.

Resolution order (first match wins; paths are disjoint by range):

**Case G (gate): hardware / RAM / vectors — tested first because ranges overlap nothing else.**
1. If `addr ∈ [0xC00000, 0xC0FFFF]` → `HW_ADDRESS/PC080SN` (sub-range: `BG_TILEMAP` `0xC00000–0xC03FFF`, `BG_ROWSCROLL` `0xC04000–0xC07FFF`, `FG_TILEMAP` `0xC08000–0xC0BFFF`, `FG_ROWSCROLL` `0xC0C000–0xC0FFFF`).
2. If `addr ∈ {0xC20000, 0xC20002}` → `HW_ADDRESS/PC080SN/YSCROLL`.
3. If `addr ∈ {0xC40000, 0xC40002}` → `HW_ADDRESS/PC080SN/XSCROLL`.
4. If `addr ∈ [0xD00000, 0xD03FFF]` → `HW_ADDRESS/PC090OJ/SPRITE_RAM`.
5. If `addr ∈ [0x380000, 0x38000F]` → `HW_ADDRESS/TC0040IOC`.
6. If `addr ∈ [0xFF0000, 0xFFFFFF]` → `GENESIS_WRAM` (annotate with matching symbol from `symbol.txt` if any).

**Case A (arcade space):** space ≡ `arcade_pc`.
- A1. If `addr ∈ [0x000000, 0x060000)` → look up in manifest `opcode_replace[].arcade_pc`:
  - if found → return `{kind: PATCHED_SITE, arcade_pc: addr, genesis_rom_offset: entry.rom_pc, note: entry.note}`.
  - if not found → return `{kind: UNPATCHED_ARCADE, arcade_pc: addr, genesis_rom_offset: addr + 0x200}`.
- A2. Otherwise → `UNKNOWN/arcade_pc_out_of_range`.

**Case R (Genesis ROM space):** space ≡ `genesis_rom_offset`.
- R1. If `addr ∈ [0x000000, 0x000200)` → `GENESIS_ONLY/vectors`.
- R2. If `addr ∈ [0x000200, 0x060200)`:
  - Compute candidate `arcade_pc = addr - 0x200`.
  - Look up candidate in manifest `opcode_replace[].arcade_pc`:
    - if found AND `entry.rom_pc == addr` → `{kind: PATCHED_SITE, arcade_pc, genesis_rom_offset: addr, note}`.
    - if found AND `addr ∈ [entry.rom_pc, entry.rom_pc + len(entry.replacement_bytes)/2)` → `{kind: PATCHED_SITE_INTERIOR, arcade_pc: entry.arcade_pc, genesis_rom_offset: addr, offset_within_patch: addr - entry.rom_pc}`.
    - else → `{kind: UNPATCHED_ARCADE, arcade_pc, genesis_rom_offset: addr}`.
- R3. If `addr ∈ [0x060200, 0x070000)` → `GENESIS_ONLY/padding`.
- R4. If `addr ∈ [0x070000, 0x080000)` → `GENESIS_ONLY/wrapper`. Resolve function via `symbol.txt` nearest-preceding match.
- R5. Otherwise → `UNKNOWN/rom_offset_out_of_range`.

Disjointness: ranges `[0,0x200)`, `[0x200,0x60200)`, `[0x60200,0x70000)`, `[0x70000,0x80000)` partition the cart ROM. Case G ranges are all outside the ROM offset range. Every input resolves through exactly one path.

---

## 7. `--space auto` Heuristic

| Address range | Assumed space |
|---------------|---------------|
| `[0x000000, 0x000200)` | `genesis_rom_offset` (Case R1 — vectors) |
| `[0x000200, 0x060200)` | `genesis_rom_offset` (Case R2 — arcade-copied window) |
| `[0x060200, 0x080000)` | `genesis_rom_offset` (Case R3/R4) |
| `[0xC00000, 0xC0FFFF]`, `0xC20000`, `0xC40000`, `[0xD00000, 0xD03FFF]`, `[0x380000, 0x38000F]` | `HW_ADDRESS` (Case G) |
| `[0xFF0000, 0xFFFFFF]` | `GENESIS_WRAM` (Case G6) |
| `[0x060000, 0x060200)` | Ambiguous — could be `arcade_pc` end (exclusive) or `genesis_rom_offset`. Tool MUST require explicit `--space` in this window. |
| Anything else | Require explicit `--space`. |

---

## 8. Worked Examples

### Example 1 — Known patched site

Input: `--addr 0x055B68 --space genesis_rom_offset` (or `runtime_genesis_pc`).

Path: Case R2 → `addr - 0x200 = 0x055968` → manifest lookup finds entry with
`arcade_pc = 0x055968`, `rom_pc = 0x055B68`.

Output:
```json
{
  "input": {"addr": "0x055B68", "space": "genesis_rom_offset"},
  "kind": "PATCHED_SITE",
  "arcade_pc": "0x055968",
  "genesis_rom_offset": "0x055B68",
  "runtime_genesis_pc": "0x055B68",
  "note": "Route PC080SN BG strip producer through rastan-direct hook symbol at 0x055968."
}
```

### Example 2 — Unpatched arcade code address

Input: `--addr 0x03C3FE --space arcade_pc`.

Path: Case A1 → manifest has no `arcade_pc == 0x03C3FE` → formula
`genesis_rom_offset = 0x03C3FE + 0x200 = 0x03C5FE`.

Output:
```json
{
  "input": {"addr": "0x03C3FE", "space": "arcade_pc"},
  "kind": "UNPATCHED_ARCADE",
  "arcade_pc": "0x03C3FE",
  "genesis_rom_offset": "0x03C5FE",
  "runtime_genesis_pc": "0x03C5FE"
}
```

### Example 3 — Build 0029 crash address `0xC09EA0`

Input: `--addr 0xC09EA0 --space auto` (or any `space` — Case G is checked first).

Path: Case G1 → `addr ∈ [0xC08000, 0xC0BFFF]` → `PC080SN/FG_TILEMAP`.
Offset inside FG tilemap: `0xC09EA0 - 0xC08000 = 0x1EA0`. This is a **data sink**,
not a code PC — therefore the tool returns `HW_ADDRESS` and explicitly does NOT
attempt an `arcade_pc` mapping (such a mapping does not exist).

Output:
```json
{
  "input": {"addr": "0xC09EA0", "space": "auto"},
  "kind": "HW_ADDRESS",
  "chip": "PC080SN",
  "region": "FG_TILEMAP",
  "base": "0xC08000",
  "offset_from_base": "0x1EA0",
  "note": "Hardware memory address; not a code PC. Use the PC080SN writer audit to find code that writes here."
}
```

This explicitly signals to the caller that resolving a hardware-address crash
requires a separate writer-audit step (see
`docs/design/Cody_pc080sn_writer_audit.md`).

---

## 9. Tool Interface Specification

**Location:** `tools/addr_lookup.py`

**Inputs (CLI):**

```
addr_lookup.py --addr <hex> [--space arcade_pc|genesis_rom_offset|runtime_genesis_pc|auto]
               [--format human|json] [--manifest <path>] [--spec <path>] [--symbols <path>]
```

- `--addr` (required): hex address, `0x`-prefixed.
- `--space` (optional, default `auto`): see §7.
- `--format` (optional, default `human`): `human` prints a one-line summary plus
  key/value block; `json` emits the object from §8 to stdout.
- `--manifest` (optional, default `build/rastan-direct/rastan_direct_patch_manifest.json`).
- `--spec` (optional, default `specs/rastan_direct_remap.json`). Consulted for
  `note` field and as cross-check against manifest.
- `--symbols` (optional, default `apps/rastan-direct/out/symbol.txt`). Consulted
  only for `GENESIS_ONLY/wrapper` and `GENESIS_WRAM` annotations.

**Exit codes:**
- `0` — resolved to any non-UNKNOWN `kind`.
- `2` — `UNKNOWN` result.
- `3` — input parse error or ambiguous space requiring explicit `--space`.

**Pre-conditions checked at start:**
- manifest exists and contains a non-empty `opcode_replace` list where every entry
  has both `arcade_pc` and `rom_pc`.
- manifest `whole_maincpu_copy.dest_start - source_start == 0x200`. If not, the
  tool aborts with exit 3 and a message saying the formula in §4 no longer holds
  and the tool must be updated.
- spec `rom_opcode_replace` is empty AND spec contains no `shift_replacements`
  key. If either is violated the tool aborts with a message stating that
  `accumulated_shift_before` may be nonzero and the formula must be extended.

These pre-conditions are **guard rails**, not policy choices — they ensure the
tool fails loudly if the build pipeline grows a new kind of relocation that
invalidates the proven formula.

---

## 10. Integration Notes

- **Andy (analysis):** use this tool before writing hook specs whenever a trace
  report cites a `runtime_genesis_pc` or `genesis_rom_offset`. The tool is the
  single source of truth for "which arcade function is that?"
- **Cody (implementation/audit):** use this tool when classifying writers or
  reading trace logs. For any trace PC, run the tool first and cite its output in
  the audit row. This eliminates the class of mistake where the arcade PC column
  in an audit is off by `0x200` (i.e. someone pasted the Genesis ROM offset).
- **The tool resolves PC-space ambiguity only.** It cannot identify which code
  wrote to a hardware address — that is the writer-audit's job
  (see `docs/design/Cody_pc080sn_writer_audit.md`). Example 3 above shows this
  boundary explicitly.
- **Formula stability.** The `+0x200` shortcut is valid **only while the spec
  contains no `shift_replacements`**. If shifted relocations are ever added, the
  tool's pre-condition check fires and the formula in §4 must be re-derived.

---

## 11. Next-Step Impact

- Unblocks accurate cross-referencing between BlastEm/MAME trace logs (which
  emit `runtime_genesis_pc`) and the arcade disassembly (`build/maincpu.disasm.txt`,
  indexed by `arcade_pc`).
- Removes an entire class of manual errors (forgetting the `0x200` offset,
  conflating Genesis-only wrapper code with arcade code, treating hardware-memory
  addresses as code PCs).
- Required before any further hook-spec work, including completing the
  `0x03C3FE` / `0x03C4D2` text-writer spec decision recorded in
  `docs/design/Andy_text_writer_3c3fe_hook_spec.md`.

---

## 12. STOP Conditions

None triggered. All required fields were found, all formulas were derived from
source-of-truth files, and all three validation cases resolved through a single
deterministic path.
