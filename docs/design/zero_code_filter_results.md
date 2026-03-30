# Zero-Code Content Filter Results

## 1. Purpose

Implement exactly one content-selection rule in the live sprite path:

- Block-A entries with `code == 0x0000` are inactive and must not produce decode output, LUT entries, or SAT output.

Also add active-entry count tracking for the current prepare pass.

## 2. Exact Files Changed

- `apps/rastan/src/main.c`
- `docs/design/zero_code_filter_results.md`
- `AGENTS_LOG.md`

No changes were made in this pass to:

- `apps/rastan/src/startup_trampoline.s`
- any spec/JSON file
- palette/background/scroll systems

## 3. Zero-Code Filter Rule

Implemented in `genesistan_sprite_tile_prepare()`:

- Canonical source remains `0xE0FF11FE`.
- Existing sentinel filter remains unchanged.
- New guard added before unique-code lookup / decode / LUT writes:

```c
if (code == 0)
{
    continue;
}
```

Source location:

- `apps/rastan/src/main.c:1114-1117`

This ensures zero-code entries leave `lut[idx]` and `attr_lut[idx]` at zero (from initial clear loop).

## 4. Active Count Field

Added to launcher WRAM overlay:

- `volatile uint16_t genesistan_sprite_active_count;`
- `apps/rastan/src/main.c:182`

Prepare-pass tracking:

- Local counter `u16 active_count = 0;` (`main.c:1092`)
- Incremented only after sentinel and zero-code checks pass (`main.c:1119`)
- Written at end of prepare (`main.c:1156`):
  - `wram_overlay.launcher.genesistan_sprite_active_count = active_count;`

Compiled store proof:

- `genesistan_sprite_tile_prepare` disassembly:
  - `200074: movew %d5,e0ff93ec <wram_overlay+0x2918>`

## 5. Build Performed

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Result:

- compile/link succeeded
- normal release postpatch failed at known guard:
  - `opcode_replace at 0x0560DA`

Runtime validation artifact used:

- `dist/Rastan_287.bin`

Artifact provenance:

- manual `postpatch_startup_rom.py` with `/tmp/startup_title_remap_temp.json`
- classification: **unofficial exploratory runtime evidence only**

## 6. Zero-Code Proof

Probe:

- script: `/tmp/zero_code_filter_probe.lua`
- output: `/tmp/zero_code_filter_probe.txt`

Required 3 zero-code entries:

- `zero_code_entry idx=1 word2=0000 code=0000 lut=0000 attr_lut=0000`
- `zero_code_entry idx=2 word2=0000 code=0000 lut=0000 attr_lut=0000`
- `zero_code_entry idx=3 word2=0000 code=0000 lut=0000 attr_lut=0000`

Summary line:

- `entry_summary zero_code_entries=17 nonzero_code_entries=1`

This proves zero-code entries are filtered and do not get LUT/attr values.

## 7. Nonzero-Code Preservation Proof

From same probe:

- `nonzero_entry idx=0 word2=03CA code=03CA lut=0400 attr_lut=6000`

This proves the nonzero-code path remains active and LUT assignment still works for the active entry.

## 8. SAT Reduction Proof

From probe:

- `active_count=1 active_count_addr=E0FF93EC`
- `sat_chain traversal_len=1 chain_ok=true last_link=0`
- `active_vs_chain active_count=1 traversal_len=1 match=true`

Result:

- SAT traversal is reduced to active entries (1), no longer 18.

## 9. Link-Chain No-Regression Proof

From probe:

- `sat_chain traversal_len=1 chain_ok=true last_link=0`

Additional safety:

- `sat_summary nonzero_entries=5 sat_attr_8001_entries=0`

Interpretation:

- link chain remains valid (`chain_ok=true`)
- last link terminates with zero
- fallback `0x8001` path remains absent

## 10. Visual Verification

Attempted frame capture at sample frame:

- intended path: `/home/tighe/projects/rastan-genesis/docs/design/artifacts/build287_zero_code_filter_frame700.png`
- probe line: `snapshot ... ok=true err=nil`

In this environment, snapshot API returned success but no PNG file was emitted, so no new frame MD5 comparison could be performed in-pass.

Classification:

- **PARTIAL**

Reason:

- active-set reduction is concretely proven (`18 -> 1` via chain/active_count match)
- but no new visual artifact could be produced here for direct image comparison

## 11. No-Scope-Drift Verification

Confirmed for this pass:

- no assembly changes in this pass (`startup_trampoline.s` untouched)
- no SAT link-chain logic changes
- no attr decode logic changes
- canonical source still `0xE0FF11FE`
- no spec/json changes
- helper not live owner remains true (`HIT 20083E 2` vs sustained live hits)

Live-path hit evidence:

- `HIT 03A208 801`
- `HIT 202DD6 801`
- `HIT 200000 801`
- `HIT 202D08 802`
- `HIT 20083E 2`

## 12. Final Result

The approved zero-code content-selection slice is implemented and runtime-proven:

- `code == 0` entries are skipped in prepare
- `lut[idx]` / `attr_lut[idx]` remain zero for zero-code entries
- active_count is tracked and stored in WRAM
- SAT traversal is reduced to active entries and still link-chain-correct

No scope drift was introduced.
