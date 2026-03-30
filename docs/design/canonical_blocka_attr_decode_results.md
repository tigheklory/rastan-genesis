# Canonical Block-A Source + word0 Attr Decode Results

## 1. Purpose

Implement exactly two approved sprite-system rules:

1. Canonical Block-A source unification (`genesistan_sprite_tile_prepare()` reads `0xE0FF11FE`)
2. word0 attribute decode into SAT word2 via a new parallel attr LUT

No size/grouping/link-chain/tile-order/spec changes were made in this pass.

## 2. Exact Files Changed

- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- `docs/design/canonical_blocka_attr_decode_results.md`
- `AGENTS_LOG.md`

## 3. Canonical Block-A Source Change

Code change in `genesistan_sprite_tile_prepare()`:

- Old source base: `workram_bytes + 0x11B2`
- New canonical source base: `0xE0FF11FE`

Source proof:

- `apps/rastan/src/main.c:1084` now uses:
  - `const u8 *entry = (const u8 *)0xE0FF11FE;`

Compiled proof:

- `genesistan_sprite_tile_prepare` disassembly contains:
  - `200044: moveal #-520154626,%a5` (`0xE0FF11FE`)

Commit path still uses the same source:

- `apps/rastan/src/startup_trampoline.s:85` and `:106`
- disassembly:
  - `202d16: moveal #-520154626,%a0`
  - `202d44: moveal #-520154626,%a0`

## 4. New Attr LUT Structure

Added new WRAM LUT alongside tile LUT:

- `apps/rastan/src/main.c:181`
  - `volatile uint16_t genesistan_sprite_attr_lut[18];`

Assembly offset constant added:

- `apps/rastan/src/startup_trampoline.s:25`
  - `#define FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET 0x28F4`

Compiled proof of address:

- `202d50: lea e0ff93c8 <wram_overlay+0x28f4>,%a4`

## 5. word0 Decode Rule

Implemented in prepare loop (`apps/rastan/src/main.c:1139-1144`):

- `flipy = (word0 >> 15) & 1`
- `flipx = (word0 >> 14) & 1`
- `raw_bank = word0 & 0x000F`
- `sprite_colbank = (genesistan_arcade_workram_words[10] & 0x00E0) >> 1`
- `color = raw_bank | sprite_colbank`
- `pal_line = (color >> 4) & 0x3`
- `attr_lut[idx] = (pal_line << 13) | (flipy << 12) | (flipx << 11)`

## 6. SAT word2 Construction Change

Assembly commit now ORs attr LUT into SAT word2:

- `apps/rastan/src/startup_trampoline.s:124`
  - `or.w (%a4), %d1`

SAT word2 construction in asm is now:

- `(tile_lut[idx] & 0x07FF) | 0x8000 | attr_lut[idx]`

## 7. Build Performed

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Result:

- Compile/link succeeded.
- Standard release postpatch failed at known preimage gate:
  - `opcode_replace at 0x0560DA`

Runtime validation artifact used:

- `dist/Rastan_286.bin`

Artifact provenance:

- Manual `postpatch_startup_rom.py` run with `/tmp/startup_title_remap_temp.json`
- Classification: **unofficial exploratory runtime evidence only**

## 8. Canonical Source Proof

Static + compiled proof:

- Prepare source: `0xE0FF11FE` (`main.c:1084`, disasm `200044`)
- Commit source: `0xE0FF11FE` (`startup_trampoline.s:85,:106`, disasm `202d16`, `202d44`)

Runtime context (probe `/tmp/canonical_blocka_attr_probe.txt`):

- `entry_scan valid_written=18 nonzero_tile_lut=18`

## 9. Attr LUT Proof

Probe (`/tmp/canonical_blocka_attr_probe.txt`) sampled 3 entries:

- `sprite_ctrl=0060 sprite_colbank=0030`
- `attr_decode idx=0 word0=0000 flipy=0 flipx=0 raw_bank=0 pal_line=3 attr_lut=6000 expected=6000 match=true`
- `attr_decode idx=1 word0=0000 flipy=0 flipx=0 raw_bank=0 pal_line=3 attr_lut=6000 expected=6000 match=true`
- `attr_decode idx=2 word0=0000 flipy=0 flipx=0 raw_bank=0 pal_line=3 attr_lut=6000 expected=6000 match=true`

This proves:

- `attr_lut[idx] == (pal_line << 13) | (flipy << 12) | (flipx << 11)`

## 10. SAT word2 Proof

Probe (`/tmp/canonical_blocka_attr_probe.txt`) sampled SAT word2 for 3 entries:

- `sat_word2 idx=0 sat_entry=0 tile_lut=0400 attr_lut=6000 sat_w2=E400 expected=E400 match=true`
- `sat_word2 idx=1 sat_entry=1 tile_lut=0404 attr_lut=6000 sat_w2=E404 expected=E404 match=true`
- `sat_word2 idx=2 sat_entry=2 tile_lut=0404 attr_lut=6000 sat_w2=E404 expected=E404 match=true`

Formula holds in runtime sample:

- `SAT.word2 == (tile_index & 0x07FF) | 0x8000 | attr_lut[idx]`

## 11. Title-Logo Stability Note

Observed in this run:

- `title_stability idx=0 word0=0000 attr_lut=6000 expected_word2=E400 note=nonzero_attr`

Interpretation:

- For sampled title entries, `word0` remains `0x0000`, but `sprite_colbank=0x0030` produced `pal_line=3`, so `attr_lut` is nonzero (`0x6000`).
- Therefore SAT word2 is **not unchanged** versus prior hardcoded palette behavior; it now carries decoded palette-line bits by design.

## 12. Visual Verification

Probe attempted snapshot at frame 700:

- `snapshot frame=700 path=/home/tighe/projects/rastan-genesis/docs/design/artifacts/build286_canonical_blocka_attr_frame700.png ok=true err=nil`

In this environment, no PNG file was emitted at that path (same behavior seen with direct snapshot tests), so no new frame binary comparison could be performed here.

Visual classification for this pass:

- **FAIL** (no new verifiable frame artifact emitted in this environment)

## 13. No-Regression / No-Scope-Drift Verification

Runtime no-regression indicators from probe:

- `sat_chain traversal_len=18 chain_ok=true nonzero_entries=18 sat_attr_8001_entries=0`
- `HIT 03A208 801`
- `HIT 202DCA 801`
- `HIT 200000 801`
- `HIT 202CFC 802`
- `HIT 200834 2`

Interpretation:

- all 18 Block-A entries still processed in sampled title path
- link chain remains correct
- fallback `0x8001` not reintroduced
- helper remains non-owner (`200834` rare hits vs sustained live prepare/commit hits)

No-scope-drift confirmations:

- no spec/JSON changes
- no size/grouping logic changes
- no link-chain logic changes
- no tile-order changes
- no helper reintroduction
- no palette/background/scroll system expansion

## 14. Final Result

Implemented the exact two-rule slice:

1. Prepare now reads canonical Block-A source `0xE0FF11FE` (matching commit)
2. word0 attr decode is active through new `genesistan_sprite_attr_lut[18]`, and commit ORs it into SAT word2

Runtime proof confirms both rules are active and formula-correct in sampled entries. Visual proof remains unconfirmed in this environment due snapshot file emission issue.
