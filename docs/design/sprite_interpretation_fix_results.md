# Sprite Interpretation Fix Results

## 1. Purpose

Implement only the two confirmed sprite interpretation blockers from `docs/design/sprite_interpretation_failure_diagnosis.md`:

1. SAT link chain in `genesistan_sprite_commit_asm`
2. 2x2 tile ordering in `frontend_decode_pc090oj_cell()`

No architecture changes, no spec changes, no fallback/helper reintroduction.

## 2. Exact Files Changed

- `apps/rastan/src/startup_trampoline.s`
- `apps/rastan/src/main.c`

Also updated for required reporting:

- `docs/design/sprite_interpretation_fix_results.md`
- `AGENTS_LOG.md`

## 3. Fix 1 — SAT Link Chain

### Problem (confirmed)

`genesistan_sprite_commit_asm` wrote SAT word1 as fixed `0x0500`, so every entry had `link=0` and VDP traversal stopped after the first sprite.

### Implemented change

In `apps/rastan/src/startup_trampoline.s`:

- Added a count pass over the same filtered entry set (`word1 != 0x0180` and LUT entry nonzero).
- Added write-pass link generation using written-entry index only.
- Preserved 2x2 size bits (`0x0500` upper nibble behavior).
- Last written SAT entry now terminates with `link=0`.

### Evidence

From `/tmp/sprite_interpretation_fix_probe.txt` (frame 700):

- `sat_link_proof idx=0 sat=0168 0501 8400 0090 size_nibble=5 link=1`
- `sat_link_proof idx=1 sat=0080 0502 8404 0080 size_nibble=5 link=2`
- `sat_link_proof idx=2 sat=0080 0503 8404 0080 size_nibble=5 link=3`
- `sat_link_proof idx=3 sat=0080 0504 8404 0080 size_nibble=5 link=4`
- `sat_link_proof idx=4 sat=0080 0505 8404 0080 size_nibble=5 link=5`
- `sat_last_written idx=17 word1=0500 link=0`
- `sat_chain traversal_len=18 chain_ok=true`

This confirms sequential link chain and valid terminator behavior.

## 4. Fix 2 — Tile Ordering / Decode Layout

### Problem (confirmed)

`frontend_decode_pc090oj_cell()` emitted row-major `[TL, TR, BL, BR]` while the current 2x2 Genesis sprite interpretation requires `[TL, BL, TR, BR]` for correct placement.

### Implemented change

In `apps/rastan/src/main.c`:

- For `y < 8`: right-half destination changed from slot 1 to slot 2.
- For `y >= 8`: left-half destination changed from slot 2 to slot 1.

Current assignment is now:

- slot 0 = top-left
- slot 1 = bottom-left
- slot 2 = top-right
- slot 3 = bottom-right

This is the required corrected order.

## 5. Build Performed

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Result:

- Compile/link succeeded.
- Standard release postpatch failed on known opcode preimage gate (`opcode_replace at 0x0560DA`).

Runtime validation artifact used in this pass:

- `dist/Rastan_284.bin`

How artifact was produced:

- Ran `postpatch_startup_rom.py` manually against fresh `apps/rastan/out/rom.bin` with `/tmp/startup_title_remap_temp.json`.

Important classification:

- This runtime validation is **unofficial exploratory runtime evidence only** (temporary external spec copy), not official clean release-flow proof.

## 6. SAT Link Proof

Probe script: `/tmp/sprite_interpretation_fix_probe.lua`

Probe output: `/tmp/sprite_interpretation_fix_probe.txt`

Key lines:

- `sat_link_proof idx=0 ... word1=0501 ... link=1`
- `sat_link_proof idx=1 ... word1=0502 ... link=2`
- `sat_link_proof idx=2 ... word1=0503 ... link=3`
- `sat_link_proof idx=3 ... word1=0504 ... link=4`
- `sat_link_proof idx=4 ... word1=0505 ... link=5`
- `sat_last_written idx=17 word1=0500 link=0`
- `sat_chain traversal_len=18 chain_ok=true`
- `sat_summary nonzero_entries=18 sat_attr_8001_entries=0`

Interpretation:

- Link increments across written entries.
- Last written entry terminates chain with link 0.
- More than one sprite entry is traversable by VDP (chain length 18).

## 7. Decode Ordering Proof

Code-level proof from `apps/rastan/src/main.c`:

```c
if (y < 8)
{
    tile_left = dst + (0 * 32) + (y * 4);
    tile_right = dst + (2 * 32) + (y * 4);
}
else
{
    tile_left = dst + (1 * 32) + ((y - 8) * 4);
    tile_right = dst + (3 * 32) + ((y - 8) * 4);
}
```

This directly enforces `[TL, BL, TR, BR]` slot ordering.

Runtime probe context for representative cell (`code0=03CA`) showed source row bytes:

- `decode_src_rows TL=11 99 81 11 TR=88 99 99 11 BL=12 33 32 22 BR=21 89 79 82`

Live decode staging bytes sampled at `DECODE_BASE` were zero in this run (`decode_slots ... 00`), which is consistent with the known tertiary LUT/decode-buffer mismatch diagnosis and is out of scope for this two-fix pass.

## 8. Visual Verification

Visual artifacts:

- Previous baseline: `/tmp/build283_full_prototype_frame700.png`
- Current run: `/tmp/build284_sprite_interp_fix_frame700.png`

Evidence:

- `md5sum` is identical for both frame captures:
  - `772d9e9357388e71a32ea2f94658f9f3`

Classification:

- **FAIL** (no meaningful visible improvement in the captured frame).

## 9. No-Scope-Drift Verification

Confirmed in this pass:

- No JSON/spec file modified.
- No helper reintroduced into live path.
- No one-sprite logic added.
- No logo-specific logic added.
- No LUT redesign attempted.
- No palette/flip/background work added.

Additional regression checks from probe:

- Fallback still off: `sat_attr_8001_entries=0`.
- Helper still not live owner: `HIT 2007EA 2` while live path hits are sustained (`HIT 03A208 801`, `HIT 200000 801`, `HIT 202CB4 802`).

## 10. Final Result

Implemented exactly the two scoped fixes:

1. SAT link chain now uses sequential links over written entries and terminates correctly.
2. Decoder output ordering is updated to `[TL, BL, TR, BR]` at source-assignment level.

Runtime evidence confirms the primary blocker (link chain) is fixed and multi-entry SAT traversal now works (`traversal_len=18`).

Visual output is unchanged in the sampled frame, so overall visual classification for this pass remains **FAIL**.
