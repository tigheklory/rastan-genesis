# Live Decode Buffer Wiring Fix Results

## 1. Purpose

Implement exactly one fix category: align live decode destination and live upload source so the corrected PC090OJ decode output is the same buffer uploaded to VRAM tile region 1024+ before `genesistan_sprite_commit_asm()` consumes LUT-derived SAT indices.

## 2. Exact Files Changed

Changed in this pass:

- `apps/rastan/src/main.c`
- `docs/design/live_decode_buffer_wiring_fix_results.md`
- `AGENTS_LOG.md`

No edits were applied in this pass to:

- `apps/rastan/src/startup_trampoline.s`
- any spec/JSON file

## 3. Live Decode Destination

In `genesistan_sprite_tile_prepare()` (`apps/rastan/src/main.c`), the decode destination is now explicitly bound to one local pointer:

```c
u32 *const live_decode_upload_buffer = wram_overlay.launcher.frontend_runtime_sprite_tile_buffer;
```

Decoded cells are written via:

```c
frontend_decode_pc090oj_cell(code, live_decode_upload_buffer + ((u32)slot * 4U * 8U));
```

Concrete buffer address in this build (from disassembly):

- `wram_overlay + 0x800 = 0xE0FF72D4`

## 4. Live Upload Source

The same pointer is now used as upload source:

```c
VDP_loadTileData((const u32 *)live_decode_upload_buffer,
                 FRONTEND_RUNTIME_SPRITE_TILE_BASE,
                 unique_count * 4U,
                 DMA);
```

Compiled disassembly confirms upload source address:

- `0x200174: pea e0ff72d4` before `DMA_doDmaFast` (VDP load path)

## 5. Wiring Fix Applied

Applied a single wiring alignment fix in `genesistan_sprite_tile_prepare()`:

- introduced `live_decode_upload_buffer` as the single live buffer reference
- switched `memset`, decode destination arithmetic, and `VDP_loadTileData` source to that same pointer

No SAT logic, palette, flipscreen, size policy, LUT indexing policy, or helper ownership logic was changed in this pass.

## 6. Build Performed

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Observed result:

- compile/link succeeded
- normal release postpatch still failed at known preimage guard:
  - `opcode_replace at 0x0560DA`

Runtime validation artifact used:

- `dist/Rastan_285.bin`

Artifact provenance:

- produced by manual `postpatch_startup_rom.py` run with `/tmp/startup_title_remap_temp.json`
- classification: **unofficial exploratory runtime evidence only**

## 7. Decode Buffer Proof

Probe:

- script: `/tmp/live_decode_buffer_wiring_probe.lua`
- output: `/tmp/live_decode_buffer_wiring_probe.txt`

Representative decoded code event:

- `decode_event frame=202 pc=20010E code=03CA slot=0 slot_addr=00FF72D4`
- `decode_first16=11 99 81 11 18 98 88 88 18 81 18 89 11 11 88 89`
- `decode_first_nonzero_offset=0`

Result:

- decoded output is nonzero immediately after decode completion for representative code `0x03CA`

## 8. Upload Source Proof

From the same probe:

- `upload_event frame=202 pc=200174 upload_base=E0FF72D4`
- `upload_first16=11 99 81 11 18 98 88 88 18 81 18 89 11 11 88 89`
- `upload_first_nonzero_offset=0`

Result:

- upload source buffer is nonzero immediately before upload

## 9. Same-Buffer Proof

Runtime and static proof both match:

- probe end line: `decode_base=E0FF72D4 upload_base=E0FF72D4`
- decode sample bytes and upload sample bytes are byte-identical in the same frame/event window
- disassembly shows both decode writes and upload source referencing `0xE0FF72D4`

Conclusion:

- `decode destination == upload source` for live path

## 10. VRAM Verification

Frame 700 VRAM sample from probe:

- `vram8000_words frame700=1199 8111 1898 8888 1881 1889 1111 8889`

Comparison against prior known values:

- prior reference: `1199 8111 1898 8888 1881 1889 1111 8889`
- post-fix:       `1199 8111 1898 8888 1881 1889 1111 8889`

VRAM status:

- **unchanged**

## 11. Visual Verification

Artifacts:

- baseline: `/tmp/build283_full_prototype_frame700.png`
- prior pass: `/tmp/build284_sprite_interp_fix_frame700.png`
- current: `/tmp/build285_live_decode_wiring_frame700.png`

MD5 comparison:

- `build283`: `772d9e9357388e71a32ea2f94658f9f3`
- `build284`: `772d9e9357388e71a32ea2f94658f9f3`
- `build285`: `772d9e9357388e71a32ea2f94658f9f3`

Frame comparison:

- current frame is byte-identical to prior baseline frames

Classification:

- **FAIL** (no meaningful visual improvement)

## 12. No-Scope-Drift Verification

Confirmed for this pass:

- no spec/json changes
- no helper reintroduced into live ownership path
- no SAT logic changed
- no palette/flip/background changes
- no LUT redesign
- no `startup_trampoline.s` edits in this pass

Runtime sanity (same probe):

- `HIT 03A208 801`
- `HIT 200000 801`
- `HIT 202CB4 802`
- `HIT 2007EA 2` (helper not live owner)

## 13. Final Result

Single wiring fix was implemented in `genesistan_sprite_tile_prepare()` by forcing one explicit live buffer pointer for both decode destination and upload source.

Post-fix proof confirms decode and upload now use the same nonzero buffer (`0xE0FF72D4`) with matching bytes at runtime.

VRAM tile-region sample and visual output remain unchanged in this pass.
