1. Executive Summary
Implemented the one-field patch-spec correction for arcade PC `0x03AD44`: replacement tail changed from `NOP (4e71)` to `RTS (4e75)` to preserve the original function return contract after the hook call.

2. Preconditions Verified
- `specs/rastan_direct_remap.json` contains `arcade_pc = 0x03AD44`.
- That entry has `original_bytes = 20C0534166FA4E75`.
- Before edit, that entry had `replacement_bytes = 4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e71`.
- `opcode_replace_count` is `35`.
- Built ROM at offset `0x03AF44` began with `4E B9`.
- Existing gameplay patch at `0x055968` remains present.

3. Original Incorrect Patch Entry
- `arcade_pc`: `0x03AD44`
- `original_bytes`: `20C0534166FA4E75`
- `replacement_bytes` (before): `4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e71`

4. Exact Change Applied (`4e71` → `4e75`)
Changed only the tail in the existing `0x03AD44` entry:
- from: `4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e71`
- to:   `4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e75`
No other `opcode_replace` entry was edited by this fix.

5. Build Verification
Build command:
- `source tools/setup_env.sh && make -C apps/rastan-direct`
Result:
- Build succeeded.
- No spec parse errors.
- No patch byte mismatch errors.
- No symbol resolution errors.
- ROM artifact produced.

6. Post-Build ROM Verification at `0x03AF44`
Verified rebuilt ROM bytes at `apps/rastan-direct/dist/rastan_direct_video_test.bin`, offset `0x03AF44`:
- `4E B9 00 07 02 D2 4E 75`
This matches the required shape `4E B9 ?? ?? ?? ?? 4E 75` and confirms the tail is now `4E 75`.

7. Final Result
The `0x03AD44` replacement now restores the original return contract by ending in `RTS` instead of `NOP`, with no hook-code changes and no scope expansion.
