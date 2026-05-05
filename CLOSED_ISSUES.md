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
- **Evidence:** Tighe visual observation that palette is loaded in Exodus after Build 55b active-writer hook.
- **Closure note:** Closed ONLY for "all-white palette in Exodus" symptom. The MAME trace disagreement (which suggests the palette pipeline differs between emulators) remains open as OPEN-003.
- **Related still-open issue:** OPEN-003 (MAME vs Exodus disagreement).
