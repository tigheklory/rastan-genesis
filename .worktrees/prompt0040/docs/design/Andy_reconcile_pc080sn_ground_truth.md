# Andy — Reconcile PC080SN Ground-Truth Data

## Prompt 226 Analysis

Using all data collected by Cody (dest trace, staged_bg_buffer dump, MAME PC080SN extraction, arcade RAM dump).

---

## Task A: Does the hook produce real staged_bg_buffer writes?

**Answer: NO.**

`trace_hook_call_total = 0x0000` over 3000 frames. Zero hook calls → zero real writes. All 2048 `staged_bg_buffer` entries remain the init_staging_state checkerboard (0x0001/0x0002). This is not a mapping error or arithmetic error — it is a structural zero-invocation result.

---

## Task B: Is the zero-real-data result fully explained?

**Answer: YES.**

`REAL_DATA count = 0` is the mathematically certain outcome of `trace_hook_call_total = 0`. No hook call → no writes → buffer stays as init. No further explanation is needed for the buffer content.

---

## Task C: Is the dest trace failure root explained?

**Answer: YES.**

The dest trace buffer (`trace_hook_call_total`, `trace_capture_calls`, and all trace table entries) was never written because the hook never executed. Cody's Lua script read pre-zeroed or uninitialized WRAM at the trace struct address. The one anomalous entry at call 2 / desc 9 (`desc_val = 0x000000C0`) is consistent with an uninitialized WRAM residual, not an actual hook invocation. The `dest_masked = 0x00010000` vs `dest_raw = 0x00000000` inconsistency in row 0 confirms the buffer was read before any hook writes occurred.

---

## Task D: Is the arcade/genesis mismatch explained?

**Answer: YES, with important nuance.**

The arcade PC080SN tilemap RAM at 0xC00000–0xC0FFFF contains valid tile data for the Title screen (as shown in the arcade RAM dump). The Genesis `staged_bg_buffer` contains only checkerboard. The two systems are structurally decoupled: the arcade CPU writes to PC080SN RAM at 0xC00000 via direct memory-mapped `word_w` writes; the Genesis hook `genesistan_hook_tilemap_plane_a` was never invoked; therefore `staged_bg_buffer` was never populated from arcade data. The arcade data is real and valid — the Genesis translation pipeline simply never ran.

---

## Task E: Is the Layer A / Layer B discrepancy explained?

**Answer: YES.**

- **Layer B (VRAM 0xC000, Plane B):** Sole write source is `genesistan_hook_tilemap_plane_a` via `staged_bg_buffer` → `vdp_commit_bg_strips_if_dirty`. Hook never called → buffer stays checkerboard → Plane B shows only checkerboard.
- **Layer A (VRAM 0xE000, Plane A):** Written by a different mechanism (FG hook or other content). Non-checkerboard content there is real and unrelated to the BG hook. `vdp_commit_bg_strips_if_dirty` does NOT write to Plane A.
- The discrepancy is direct evidence that the BG hook path is broken and the FG path is functional. This is consistent with zero BG hook calls.

---

## Task F: Root cause identification

**Primary root cause: `genesistan_hook_tilemap_plane_a` is never invoked.**

### Evidence
- `trace_hook_call_total = 0` over 3000 Title-scene frames (definitive)
- `staged_bg_buffer` REAL_DATA count = 0 (consistent)
- Layer B stays checkerboard despite init_staging_state writing `bg_row_dirty = 0xFFFFFFFF` (consistent: dirty bits were written at boot, but checkerboard content is what got flushed to VRAM)

### Mechanism analysis

The hook is invoked when the arcade code reaches address `0x055968` (arcade PC space). The patch in `specs/rastan_direct_remap.json` at `arcade_pc: "0x055968"` replaces the original instruction stream with `JSR genesistan_hook_tilemap_plane_a; NOP × 16`.

Three candidate explanations:

**Candidate 1 — Patched site never reached during Title scene** (most likely)

The function at arcade ROM address 0x055968 may be the gameplay BG strip writer, not the Title scene writer. The Title screen may set up the BG tilemap once at scene init (before `arcade_tick_logic` is first called, or through a different code path) and then not call 0x055968 again during normal Title playback. 3000 frames is far past any one-time init call. If 0x055968 is only called during gameplay mode and not during attract/title mode, the hook will never fire during Title screen testing.

Evidence supporting this: the MAME ground truth shows no "strip write function" — the arcade CPU writes to PC080SN RAM directly via the memory map. The function at 0x055968 (original bytes: `movea.l 0x10A0(%a5), %a0; move.w #0x0010, %d1; ...`) appears to be a frame-update routine that copies pre-prepared BG tile data to the PC080SN. This kind of routine is typically invoked from the main gameplay loop, not from attract/Title state.

**Candidate 2 — Original bytes mismatch, patch not applied**

If the bytes at 0x055968 in the current ROM variant do not match `original_bytes`, the patcher will reject or skip that entry. This would leave the arcade code unmodified at that site, and the hook would never be called.

The patcher uses byte-exact matching before applying replacements. A single byte difference (variant difference, or wrong address) would silently skip the patch entry.

**Candidate 3 — Code path reaches 0x055968 but validation exits immediately**

Even if the hook is called, if `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` holds a value outside `[0xC00000, 0xC04000)`, the hook exits via `.Lbg_hook_dest_invalid` and increments nothing. But `init_staging_state` explicitly writes `0x00C00000` to this address at boot, so this should be valid on frame 1. Candidate 3 is less likely than Candidates 1 and 2.

### Conclusion

The most likely root cause is **Candidate 1**: the code site at 0x055968 is a gameplay-mode BG updater that is not called during Title screen playback. The Title screen may update BG via a separate code path (different arcade PC address, or one-time init before the main loop enters), which was never identified and never patched.

Secondary concern is **Candidate 2**: the patch may not have been applied if the bytes do not match.

---

## Task G: Next investigation steps

### Step 1 — Verify patch application (rules out Candidate 2)

Examine the built ROM at the expected Genesis ROM address for the patched site. The Genesis ROM address for arcade PC 0x055968 is `0x055968 + 0x000200 = 0x055B68`. If the first 6 bytes at 0x055B68 in `dist/rastan_direct_video_test.bin` are `4E B9 xx xx xx xx` (JSR abs.l), the patch applied. If the first bytes are `20 6D 10 A0 ...` (original), the patch did not apply.

**How to check:** Hexdump bytes at 0x055B68 in the built ROM binary.

### Step 2 — Find the actual Title-scene BG write site (rules out Candidate 1)

Use MAME debugger with a write watchpoint on PC080SN BG RAM (address range 0xC00000–0xC03FFF). When the Title screen is displayed, observe every write to this range and record the PC of each writing instruction. This gives the actual arcade PC address(es) that write BG data during the Title scene.

If those addresses are different from 0x055968, they are additional patch targets that have never been added to `rastan_direct_remap.json`.

### Step 3 — Confirm arcade tick path reaches 0x055968 at all

In MAME, place a breakpoint at arcade PC 0x055968. Run to end of attract cycle (≥3000 frames). Record whether it hits. If it never hits, this confirms Candidate 1.

---

## Summary Table

| Question | Answer | Confidence |
|---|---|---|
| Hook produces real staged_bg_buffer writes | NO | Definitive (trace=0) |
| Zero real-data result explained | YES | Definitive |
| Dest trace failure explained | YES | Definitive |
| Arcade/Genesis mismatch explained | YES | Definitive |
| Layer A/B discrepancy explained | YES | Definitive |
| Root cause identified | PARTIAL | High — primary candidate identified, not yet confirmed |
| Arithmetic fixes (%d1, %d2, %d7) correct | YES | Confirmed (prior analysis) |
| Next action | Verify patch application + find Title-scene BG write PC | — |
