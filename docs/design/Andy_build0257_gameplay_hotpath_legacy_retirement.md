# Build 0257 — Gameplay Hot-Path PC080SN Tall-Buffer Producer Retirement

**Agent:** Andy · **Type:** source-changing performance-oriented legacy retirement · **Build produced: YES (0257).**
**STOP: NO.** User authorization: Tighe approved Andy performing the implementation/build.

## 1. Baseline

Build **0256** (verified current): ROM `dist/rastan-direct/rastan_direct_video_test_build_0256.bin`, SHA-256
`0fd658fd2e6976bfc9ccf2dd497369d53b27d7ea84f88d7de11f2c5b2e86a170`, size `1592196`, counter `256`. Build 0256
**preserved** (SHA re-verified). Pre-edit: canonical coverage `0x184B84`, opcode-replace count `221`. Tall BSS:
`staged_bg_tall_buffer` (8 KB), `staged_fg_tall_buffer` (8 KB), `bg_tall_dirty`, `fg_tall_dirty`. Toolchain
capability confirmed (m68k-elf + Java + `make release`).

## 2. User priority

Gameplay speed + meaningful PC090OJ/PC080SN legacy removal — not a Push-Player-Button/frontend/cosmetic/tiny task.

## 3. Files / reports read

`RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`,
`CLOSED_ISSUES.md`; Cody 0251–0255 + Andy plan/0256 docs; `tilemap_hooks.s`, `vdp_comm.s`, `boot/boot.s`,
`pc090oj_hooks.s`; translation scripts; `out/symbol.txt`, `address_map.json`, patch manifest,
`specs/rastan_direct_remap.json`.

## 4. PC080SN tall-buffer producer audit (primary target — proven fully dead)

1. **`staged_bg_tall_buffer` / `staged_fg_tall_buffer` read anywhere?** NO. Their only consumer was the tall
   projector, which was gated off in gameplay since Build 0252 and removed entirely (stub + calls) in Build
   0256. Both are write-only.
2. **`bg_tall_dirty` / `fg_tall_dirty` acted on anywhere?** NO — only the removed projector read them.
3. **`fill_tall` side effects beyond the tall buffers/dirty flags?** NONE. `genesistan_hook_tilemap_bg_fill_tall`
   writes only `staged_bg_tall_buffer` + `bg_tall_dirty`; `..._fg_fill_tall` writes only `staged_fg_tall_buffer`
   + `fg_tall_dirty`.
4. **`bg_fill_tall` caller?** NONE — zero callers (fully dead; `staged_bg_tall_buffer` was never even written).
   **`fg_fill_tall` caller?** only `genesistan_stage_fg_src_column`.
5. **`genesistan_stage_fg_src_column`** (called from the live gameplay BG hook `genesistan_hook_tilemap_plane_a`
   and the unreached FG hook) loops **16 segs × 4 rows = 64** cells/frame, each calling `fg_fill_tall` — its own
   comment: "routing each cell through the gameplay-only tall FG backing helper ... Collision is intentionally
   NOT authored here." Its only output is the dead tall buffer.
6. **Does removing it change live Plane A?** NO. Live Plane A/FG is produced by `genesistan_hook_tilemap_plane_a
   _selector0_native` / `_selector12_native` + the pan publisher into **`staged_fg_buffer`** (consumed by
   `vdp_commit_fg_narrow_strips`). **Decisive proof:** Build 0256 removed the tall projector and FG still renders
   (user-verified) — so the tall path contributes zero visible output.
7. **Frontend C-window/text require the tall buffers?** NO — `genesistan_hook_cwindow_clear` cleared the tall
   buffer but nothing read it; the live `staged_fg_buffer` clear + `fg_row_dirty` are retained.
8. **Collision independent?** YES — `genesistan_stage_bg_collision_column` touches no tall buffer/`fill_tall`
   (retained).
9. **Removable this build?** YES — the whole chain (producers + buffers + dirty flags + calls) is dead.
10. **Expected reduction:** ~16 KB WRAM (two 8 KB tall buffers) + ~600 bytes code (3 function bodies + call sites
    + C-window/boot loops) + the per-frame 64-call `fg_fill_tall` loop off the gameplay hot path.

## 5. PC090OJ gameplay hot-path audit (secondary — no removable gameplay legacy this build)

- `pc090oj_native_emit_pass` is the scene-1 gameplay finalizer (native lanes); `native_sprite_emit`,
  `native_sprite_frame_begin`, `native_stage_player_blocks_41f5e`, PLAYER_BODY lifecycle are the live gameplay
  path — all intact and out of scope.
- `pc090oj_legacy_emit_pass` executes only when `genesistan_current_scene_id != 1` (non-gameplay/frontend) — not
  a gameplay-speed path.
- `pc090oj_object_ram` is retained arcade persistent object state (KF-069); gameplay writes it as arcade state,
  not as a removable mirror. Do not remove until all producers/consumers convert.
- **No removable gameplay-hot PC090OJ legacy scanner/decoder path** exists in scene 1 (the old candidate/scanner
  path is already inactive). The next meaningful PC090OJ target is **frontend/non-gameplay conversion** of the
  `object_ram`+`legacy_emit_pass` producers to native SAT — a frontend effort, not a gameplay-speed bottleneck.
  This build therefore takes the meaningful PC080SN chunk and leaves PC090OJ untouched.

## 6. Exact source changes

**`tilemap_hooks.s`:** removed `.global genesistan_hook_tilemap_bg_fill_tall` + `..._fg_fill_tall`; removed the
`bsr genesistan_stage_fg_src_column` from `genesistan_hook_tilemap_plane_a` (kept the collision `bsr`) and from
`genesistan_hook_tilemap_fg` (gameplay path now `movem`/`rts`); removed the dead `staged_fg_tall_buffer` clear +
`fg_tall_dirty` set from `genesistan_hook_cwindow_clear` (kept the live `staged_fg_buffer` clear + `fg_row_dirty`);
removed the three function bodies `genesistan_stage_fg_src_column`, `genesistan_hook_tilemap_bg_fill_tall`,
`genesistan_hook_tilemap_fg_fill_tall` (+ their doc comments). (Unused `FG_PRODUCER_SEG_COUNT/ROW_COUNT` `.equ`
left in place — compile-time only, no ROM/WRAM cost.)

**`vdp_comm.s`:** removed `.global` for `bg_tall_dirty`/`fg_tall_dirty`/`staged_bg_tall_buffer`/
`staged_fg_tall_buffer`; removed the `bg_tall_dirty`/`fg_tall_dirty` storage; removed the two `.space (4096*2)`
tall buffers. **Retained** `staged_bg_buffer`/`staged_fg_buffer` (live), `bg_row_dirty`/`fg_row_dirty`,
`fg_narrow_desc_*`.

**`boot/boot.s`:** removed the four tall `.extern`s, the two `clr.b bg_tall_dirty`/`fg_tall_dirty`, and the two
`staged_*_tall_buffer` boot clear loops. Nothing else touched.

**`postpatch_startup_rom.py` + `verify_canonical_rom.py`:** `CANONICAL_TOTAL_GENESIS_BYTES_COVERED`
`0x184B84` → `0x18492C` (−0x258 = −600 code bytes). Opcode count unchanged.

**Not touched:** `pc090oj_hooks.s`, `specs/rastan_direct_remap.json`, native Plane A/B producers, strip commits,
`fg_narrow_desc_*`, collision, PC090OJ, input, palette/CRAM, rope/reset, audio, frontend logic.

## 7. Reductions

- **WRAM (BSS): ~16 KB freed** — `staged_bg_tall_buffer` (8 KB) + `staged_fg_tall_buffer` (8 KB) + 2×dirty. The
  whole WRAM BSS shifted down ~16 KB (e.g. `pc090oj_object_ram` `0xFFAF9A` → `0xFF6F92`).
- **ROM/code: −600 bytes** (coverage `0x184B84` → `0x18492C`).
- **Gameplay hot path:** the 64-call/frame `fg_fill_tall` loop (dead tall staging) removed from the live gameplay
  BG hook every frame.

## 8. Static + runtime validation

- **GATE_PASS.** Counter **256 → 257**. ROM `dist/rastan-direct/rastan_direct_video_test_build_0257.bin`; SHA-256
  `6aa273c9f1337b9d4e16a39a90ae5ee50debbf2eeb475ea3e0d0f92577e79b3e`; size **1591596** (−600 vs 0256). Rolling =
  numbered. Build 0256 preserved.
- Removed symbols (`staged_bg/fg_tall_buffer`, `bg/fg_tall_dirty`, the three functions) **absent** from
  `out/symbol.txt`. Protected survivors present: `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_narrow_strips`,
  `plane_a_selector0/12_native`, `genesistan_stage_bg_collision_column`, `pc090oj_native_emit_pass`,
  `native_sprite_emit`, `native_stage_player_blocks_41f5e`, `staged_bg/fg_buffer`, `fg_narrow_desc_table`.
- Build 0256 projector retirement preserved (projector symbols still absent).
- **Build 0254 D00298/D002B0 remaps preserved and self-adjusted:** the spec uses the **symbol expression**
  `207C{symbol:pc090oj_object_ram+0x298}` / `+0x2B0`; with `pc090oj_object_ram` now at `0xFF6F92`, they resolve
  to `0xFF722A` / `0xFF7242` (both inside the 2 KB object-RAM allocation, writable WRAM). No raw `0x00D00298` /
  `0x00D002B0` immediate remains in the postpatch disasm.
- Build 0255 demo-input fix preserved (`0x00FF0118` rebase + `0x052C1C` table relocation present; `0x00FF0118`
  is a fixed A5-relative address, unaffected by BSS shifts).
- Opcode count **221 → 221**. Coverage `0x184B84 → 0x18492C`; gaps `[]`; overlaps `[]`.
- MAME smoke `states/traces/rastan_direct_video_test_build_0257_mame_30s_20260804_154143/`: frames `1798`,
  ~993% speed, no unmapped/fatal/error entries.

## 9. User verification required (post-Andy)

Gameplay speed/feel ≥ 0256; title/story/high-score still good; item-description screen unchanged; attract demo
scripted action; normal gameplay Rastan/lizard men/bats/axe; BG/FG tile strips still update; no new map/tile
corruption beyond preexisting; no new sprite disappearance/flicker.

## 10. Issues / findings

- Open issues touched: OPEN-001 (PC080SN)/OPEN-024-adjacent rendering cleanup. New: none. Closed: none.
- Deferred: PC090OJ frontend/non-gameplay `object_ram`+`legacy_emit_pass` conversion (next PC090OJ target, not a
  gameplay-speed path); item-description screen; Push-Player-Button coin-up residue.
- KNOWN_FINDINGS: Option A — no new finding; **not edited** (Build 0255 sync still pending).
- **Andy follow-up recommended: YES** — brief review after user acceptance to confirm no FG/BG/map regression and
  measure any speed change; then plan the PC090OJ frontend conversion.

## 11. STOP status

**STOP: NO.** The whole PC080SN tall-buffer producer chain was proven dead (no reader, no live side effect,
collision/live buffers separable, decisive Build 0256 rendering proof), removed cleanly with GATE_PASS, ~16 KB
WRAM + 600 bytes freed and the per-frame dead `fg_fill_tall` loop retired, while every protected native/PC090OJ/
collision/0254/0255/0256 path was preserved. This is a meaningful chunk, not a tiny cleanup. User visual/speed
verification is the remaining acceptance gate.
