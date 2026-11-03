# Build 0256 — PC080SN Tall-Projector Consumer Retirement (Implementation)

**Agent:** Andy · **Type:** source-changing dead-code retirement (Slice 1) · **Build produced: YES (Build 0256).**
**STOP: NO.**

## 1. Baseline

- Input build **0255** (verified current): ROM `dist/rastan-direct/rastan_direct_video_test_build_0255.bin`,
  SHA-256 `edfd03534b1766309de105a1dad00671d0ac73eb3ca0fa5dfe7cc3859b378673`, size `1592224`, counter `255`.
- Build 0255 numbered ROM **preserved** (SHA re-verified unchanged after the 0256 build).
- Current opcode-replace count measured live before edits: **221** (not the stale 218 from earlier notes).
- Current canonical coverage before edits: **0x184BA0**.

## 2. User delegation override

Tighe explicitly authorized Andy to perform this source-changing implementation/build, overriding the prior
Cody-only production-build boundary **for this task**. Environment capability confirmed before editing: the
m68k-elf toolchain (`m68k-elf-as/gcc/ld` 2.43.1/14.2.0) + Java run, and `make release` builds and validates.

## 3. Prior Andy spec summary

Implements Slice 1 of `Andy_build0256_pc080sn_tall_projector_consumer_retirement.md`: retire the dead PC080SN
tall-projector **consumer interface only** — the two no-op projector stubs + their `_vblank_service` call sites
+ the redundant Build 0252 scene gate + the dead `*_tall_project_base` globals + boot clears. Producers, tall
buffers, dirty flags, native Plane A/B, frontend, and PC090OJ are out of scope (Slice 2 / do-not-touch).

## 4. Files read

`RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`,
`CLOSED_ISSUES.md`; Cody reports 0251–0255 + the two Andy Build 0255/0256 design docs;
`apps/rastan-direct/src/vdp_comm.s`, `boot/boot.s`, `tilemap_hooks.s`, `pc090oj_hooks.s`; the translation
scripts; `out/symbol.txt`, `address_map.json`, patch manifest, `specs/rastan_direct_remap.json`.

## 5. Xref proof (reconfirmed at Build 0255, pre-edit)

**Projector stubs** `vdp_project_bg_tall_if_dirty` (`0x00070148`), `vdp_project_fg_tall_if_dirty` (`0x0007014A`):
each body was a Build 0253 comment + a single `rts` (pure no-op, no live projector body); the only call sites
were `vdp_comm.s:198`/`:200` inside `_vblank_service`; no external/generated xref required the exported symbols;
unlinking them does not break linking (confirmed by GATE_PASS after removal).

**Project-base globals** `bg_tall_project_base` (`0x00FF404C`), `fg_tall_project_base` (`0x00FF4054`): zero
reads anywhere; only writes were the boot `clr.w` at `boot.s:207`/`:210`; no source/generated dependency on the
exported names; safe to delete (confirmed by GATE_PASS).

## 6. Exact source changes made

**`apps/rastan-direct/src/vdp_comm.s`:**
- Removed `.global vdp_project_bg_tall_if_dirty` + `.global vdp_project_fg_tall_if_dirty`.
- Removed `.global bg_tall_project_base` + `.global fg_tall_project_base`.
- Collapsed the `_vblank_service` scene gate (see §7).
- Removed both no-op stub bodies (`vdp_project_bg_tall_if_dirty:` … `rts`, `vdp_project_fg_tall_if_dirty:` …
  `rts`) and the orphaned pre-comment; left a one-line Build 0256 retirement note.
- Removed the storage `bg_tall_project_base: .word 0` and `fg_tall_project_base: .word 0`. **Retained**
  neighbouring `bg_tall_dirty`, `fg_tall_dirty`, `bg_row_dirty`, `fg_row_dirty`, `fg_native_gameplay_owner`.

**`apps/rastan-direct/src/boot/boot.s`:**
- Removed `clr.w bg_tall_project_base` + `clr.w fg_tall_project_base`.
- Removed the now-unused `.extern bg_tall_project_base` + `.extern fg_tall_project_base`. Nothing else touched.

**`tools/translation/postpatch_startup_rom.py` + `verify_canonical_rom.py`:**
- `CANONICAL_TOTAL_GENESIS_BYTES_COVERED`: `0x184BA0` → **`0x184B84`** (measured −0x1C = −28 bytes of dead
  Genesis code/data). Opcode-replace count intentionally left unchanged.

**Not touched:** `tilemap_hooks.s`, `pc090oj_hooks.s`, `specs/rastan_direct_remap.json`, and every do-not-touch
symbol.

## 7. `_vblank_service` before/after — commit-order proof

Before:
```asm
    bsr vdp_commit_tiles_if_dirty
    cmpi.b #1, genesistan_current_scene_id
    beq.s .Lvs_skip_gameplay_tall_projectors
    bsr vdp_project_bg_tall_if_dirty      ; no-op
    bsr vdp_commit_bg_strips_if_dirty
    bsr vdp_project_fg_tall_if_dirty      ; no-op
    bra.s .Lvs_after_tall_projectors
.Lvs_skip_gameplay_tall_projectors:
    bsr vdp_commit_bg_strips_if_dirty
.Lvs_after_tall_projectors:
    bsr vdp_commit_fg_narrow_strips
```
After:
```asm
    bsr vdp_commit_tiles_if_dirty
    bsr vdp_commit_bg_strips_if_dirty
    bsr vdp_commit_fg_narrow_strips
```
Both prior branches reduced to the same single `bsr vdp_commit_bg_strips_if_dirty` (the projectors were no-ops),
so the gate is provably redundant. **Surviving commit order preserved:** `tiles → bg strips → fg narrow`.
`vdp_commit_sprites_vram`, palette, scroll, DMA, and the VBlank tail are unchanged. Static check: **0** `bsr/jsr`
to either projector symbol remain (the two remaining name occurrences are inside the removal comment only).

## 8. Producer / tall-buffer / native Plane A/B untouched

`genesistan_hook_tilemap_bg_fill_tall` / `fg_fill_tall`, `staged_bg/fg_tall_buffer`, `bg_tall_dirty`
(`0xFF404A`) / `fg_tall_dirty` (`0xFF4050`) all remain (verified present in `out/symbol.txt`). The native FG
(Plane A) producer loop (`tilemap_hooks.s:1084`) and all native Plane A/B producers, strip commits, frontend
C-window/text, and every `pc090oj_*` path were not edited.

## 9. Build + validation results

- **GATE_PASS: YES.** Counter **255 → 256**.
- Numbered ROM `dist/rastan-direct/rastan_direct_video_test_build_0256.bin`; SHA-256
  `0fd658fd2e6976bfc9ccf2dd497369d53b27d7ea84f88d7de11f2c5b2e86a170`; size **1592196** (−28 vs 0255).
- Rolling ROM SHA equals numbered SHA. Build 0255 ROM preserved (`edfd0353…` unchanged).
- **Opcode-replace count: 221 → 221 (unchanged).**
- **Canonical coverage: 0x184BA0 → 0x184B84; gaps `[]`; overlaps `[]`.** Size/coverage deltas both = 28 bytes.
- `RASTAN_GAMEPLAY_HUD_SPRITES = 2` present in `out/symbol.txt`.
- Static validation: `vdp_project_bg_tall_if_dirty` / `vdp_project_fg_tall_if_dirty` / `bg_tall_project_base` /
  `fg_tall_project_base` **no longer exist** in `out/symbol.txt`; `vdp_commit_bg_strips_if_dirty` (`0x701A0`) and
  `vdp_commit_fg_narrow_strips` (`0x725A4`) exist and are still called; Build 0254 D00298/D002B0 remaps present;
  Build 0255 demo-input selector rebase (`0x00FF0118`) + `0x052C1C` table relocation present.
- MAME smoke `states/traces/rastan_direct_video_test_build_0256_mame_30s_20260804_143819/`: frames `1798`,
  ~966% speed, normal stop; **no unique unmapped memory addresses / fatal / error** entries.

## 10. User verification required (post-Andy)

- Frontend/title/story/high-score still render.
- Attract gameplay demo still starts and scripted action still occurs.
- D00298/D002B0 fatal remains absent.
- Normal gameplay still shows Rastan, lizard men, bats, axe item.
- No new visual regressions.

## 11. Open/Closed Issues + findings

- Open issues touched: OPEN-017 / OPEN-024-adjacent native-rendering cleanup. New: none. Closed: none.
- Deferred: **Slice 2** — retire `staged_bg/fg_tall_buffer` + `bg/fg_tall_dirty` + the `fill_tall` producer
  writes (needs the native-FG-producer audit, since `fg_fill_tall` is called inside the Plane A producer).
- KNOWN_FINDINGS: Option A — no new finding; **not edited** (Build 0255 sync still pending).
- **Andy follow-up recommended: YES** — a short review after user acceptance to confirm no visual regression and
  to green-light Slice 2.

## 12. STOP status

**STOP: NO.** All Phase-1/2 proofs held, the edits matched the spec, GATE_PASS was clean with a pure 28-byte
dead-code/data delta, opcode count unchanged, and no do-not-touch/producer/native/PC090OJ/frontend path was
altered. User visual verification of Build 0256 is the remaining acceptance gate.
