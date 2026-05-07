# CLOSED_ISSUES.md

This file tracks resolved issues moved from OPEN_ISSUES.md. Do not delete entries. Each closure must include the build, evidence, and verification method.

Closure note format:
- Closed issue ID (matches original OPEN-### ID)
- Original title
- Closed by (agent/build/observation)
- Build/artifact that closed it
- Evidence (cited reference)
- Closure note
- Related still-open issue, if any

---

## CLOSED-001 — Build 53 D0/D6 runaway / wild PC / stack corruption

- **Original title:** Build 53 D0/D6 runaway / wild PC / stack corruption
- **Closed by:** Cody implementation per Andy root cause classification
- **Build/artifact:** Build 54
- **Evidence:** Andy `docs/design/Andy_build54_palette_root_cause.md` classified root cause as Origin C primary + Origin D contributing; Cody Build 54 applied D6 save/restore patches in `_3b930` and `_54810`; Build 54 produced ROM and passed postpatcher / D00778 / VRAM self-test.
- **Closure note:** Wild D0/D6 `0xAA4` path closed unless reappears in later traces.
- **Related still-open issue:** NONE.

---

## CLOSED-002 — Unsafe `0x045DAE` body replacement design

- **Original title:** Unsafe `0x045DAE` body replacement design
- **Closed by:** Andy redesign to `0x045DB8` JSR swap (Option D)
- **Build/artifact:** Build 55 design (pre-implementation Phase A revealed unsafe span)
- **Evidence:** Cody Phase A (`docs/design/Cody_build55_palette_phase_a_block.md`) found external branch `0x45D76 → 0x45DC4` into proposed span plus 7 game-state mutations; Andy `docs/design/Andy_build55_palette_045dae_redesign.md` recommended Option D (6-byte JSR swap).
- **Closure note:** Closed as design issue. Runtime usefulness of the resulting helper remains tracked under OPEN-007.
- **Related still-open issue:** OPEN-007.

---

## CLOSED-003 — Six NOPs at `0x03ADFE`/`0x03AE06`/etc. suspected as palette suppression

- **Original title:** Six NOPs at `0x03ADFE`/`0x03AE06`/etc. suspected as palette suppression
- **Closed by:** Cody NOP provenance audit / Claude classification
- **Build/artifact:** Build 55 investigation
- **Evidence:** NOPs proven to suppress screen flip / DMA trigger writes, NOT palette writes.
- **Closure note:** Do not reopen without new evidence directly tying these specific NOPs to palette behavior.
- **Related still-open issue:** NONE.

---

## CLOSED-004 — Palette format question (MAME/Taito format)

- **Original title:** Palette format question (MAME/Taito format)
- **Closed by:** Cody MAME palette format evidence
- **Build/artifact:** Build 55 evidence chain
- **Evidence:** `docs/design/Cody_build55_mame_palette_format_evidence.md` confirms `palette_device::xBGR_555` at `0x200000..0x200FFF` per local MAME `rastan.cpp`; `0x59AD4` and active `0x03BA64` conversion confirmed compatible with xBGR-555 layout.
- **Closure note:** Future palette helpers may use either faithful 2-step conversion OR algebraically equivalent direct conversion if documented.
- **Related still-open issue:** NONE.

---

## CLOSED-005 — `0x03BC84` origin unknown / suspected SGDK or checkerboard scaffolding

- **Original title:** `0x03BC84` origin unknown / suspected SGDK or checkerboard scaffolding
- **Closed by:** Cody `0x03BC84` origin archaeology
- **Build/artifact:** Build 55 archaeology
- **Evidence:** `docs/design/Cody_build55_03bc84_origin_archaeology.md` proved address-map class `arcade_copy`, runtime `0x03BC84` maps to arcade `0x03BA84`, runtime body matches arcade body relocated by `+0x200`, no repo source origin found.
- **Closure note:** Active writer remains relevant per Build 55b hook design; origin question is resolved.
- **Related still-open issue:** NONE (active writer fix is OPEN-007 / OPEN-003).

---

## CLOSED-006 — All-white CRAM / no visible palette in Exodus

- **Original title:** All-white CRAM / no visible palette in Exodus
- **Closed by:** Tighe visual verification after Build 55b active-writer hook
- **Build/artifact:** Build 55b (per Cody's `0055b.bin` / `0057.bin` — OPEN-002 ROM identity)
- **Evidence:**
  - Tighe visual observation that palette is loaded in Exodus after Build 55b active-writer hook.
  - Cody video extraction (`docs/design/Cody_build55b_video_30fps_debug_windows.md`) confirms CRAM is NOT all `0x0EEE`. Sampled rows at sec 20/sec 50 include:
    - Row `00`: `0000 0EEE 000E 0468 08AC 04EA`
    - Row `0C`: `0246 0EEE 0EEE 0EEE 0EEE 0EEE`
    - Row `60`: `0000 0868 0846 0646 0624 0424`
    - Row `6C`: `0402 0202 0202 028C 044C 0226`
    - Row `78`: `0004 0002 0222 0424`
- **Closure note:** Closed ONLY for "all-white palette in Exodus" symptom. The MAME trace disagreement (which suggests the palette pipeline differs between emulators) remains open as OPEN-003.
- **Related still-open issue:** OPEN-003 (MAME vs Exodus disagreement).

---

## CLOSED-007 — SGDK-era slot 0..19 tile reservation in direct-rastan

- **Status:** CLOSED
- **Closed in build/artifact:** `dist/rastan-direct/rastan_direct_video_test_build_0059.bin`
- **ROM SHA256:** `1135e1aaa2e2c39d64a8390c024dd8e67a998b53f829f2cd7e4eabea2d02ec23`
- **Closed by:** Cody SGDK Slot Reservation Removal Implementation + Tighe Pattern Viewer visual confirmation in Exodus
- **Original priority:** MEDIUM
- **Discovered by:** Tighe (Pattern Viewer screenshot in Exodus)
- **Original summary:** Pattern Viewer showed real Rastan tile data beginning at slot `0x14` / VRAM `0x0280`, leaving slots 0..19 unused — appeared to be SGDK-era reservation no longer serving any purpose in direct-rastan.
- **Root cause:** Single constant `TILE_CACHE_BASE_A = 20` at `tools/translation/precompute_pc080sn_tile_lut.py:39`. Andy classified reservation NOT justified in direct-rastan (no SGDK runtime, no font/debug/system tile dependency, `crash_init_cram` writes CRAM only, `tiles_dirty` never set to 1, `tilemap_hooks.s` no post-LUT offset).
- **Fix:** One-line edit `TILE_CACHE_BASE_A = 20 → 0`. Tool re-run atomically regenerated LUT + 3 preload manifests from same allocator state (lockstep automatic via single producer). `pc080sn_attr_lut.bin` SHA unchanged. No source/spec edits.
- **Evidence:**
  - Andy classification: `docs/design/Andy_slot_reservation_removal_classification.md`
  - Cody implementation: `docs/design/Cody_slot_reservation_removal_implementation.md`
  - Cody Build 59 video debug capture: `docs/design/Cody_build59_video_30fps_debug_windows.md`
  - 8 verification gates PASS (postpatcher, D00778, VRAM roundtrip, tile data at slot 0 manifest proof, 5 LUT examples, palette helpers intact, active palette writer hook intact, blank-tile sentinel preserved at new slot 0)
  - LUT examples post-fix: tile `0x20 → 0x00` (was `0x14`), tile `0x23 → 0x01` (was `0x15`), tile `0x01 → 0x3E` (was `0x52`)
  - Tighe visual confirmation in Exodus VDP Pattern Viewer: 20-slot reservation gap is gone; tile data begins immediately at slot 0 / VRAM 0x0000
- **Closure note:** Reservation removed via single-constant change in single producer tool. Lockstep coherence preserved automatically (one tool emits LUT + all 3 preload manifests). R1 cosmetic risk (`lut[unmapped]=0` collision with real tile at slot 0) substantially mitigated because the tile that moved into slot 0 is itself blank — old slot 0x14 was tile `0x0020` with all-zero pattern bytes, now at slot 0 still all-zero. R2 dormant scaffolding (`vdp_commit_tiles_if_dirty` — `tiles_dirty` never set) flagged for separate follow-up but not opened as new issue.
- **Related still-open issues:**
  - OPEN-001 — visible composed output remains incorrect despite correct preload + active VRAM + populated CRAM; symptom transformed but root cause separate
  - OPEN-003 — MAME Build 59 progression unverified vs. Exodus active state
  - OPEN-004 — bootstrap re-entry status on Build 59 unverified
