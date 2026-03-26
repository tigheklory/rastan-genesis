# Title Prep Output Final-State Audit (Build 223)

## 1) Purpose
Determine whether restored title-prep helper outputs are final-architecture-valid Genesis outputs or legacy shadow/hardware-era outputs that must be replaced.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest sections, including Build 223)
- `README.md`
- `docs/research/title_screen_visual_ownership_and_data_path.md`
- `dist/Rastan_223.bin` disassembly (`m68k-elf-objdump`)
- `apps/rastan/out/symbol.txt`
- `specs/startup_title_remap.json`

## 3) Restored Output Inventory

1. `A0=0xE0FF404C`
- semantic meaning: base of `genesistan_shadow_d00000_words` (shadowed PC090OJ sprite RAM root)
- evidence:
  - symbol map: `e0ff404c b genesistan_shadow_d00000_words`
  - title prep writes: `0x03AF62`, `0x03AF88`
  - additional frontend writes: `0x52CC0`, `0x542CA`, `0x54A2E`, `0x56656`
- classification: `LEGACY_D_WINDOW_SHADOW`

2. `A0=0xE0FF41BC`
- semantic meaning: descriptor subregion inside `genesistan_shadow_d00000_words` (offset from D-window shadow base), used as active frontend/title descriptor list region
- evidence:
  - title prep write: `0x03AF74`
  - helper usage: `0x42094`, `0x46062`, `0x5625C`, `0x56286`, `0x562C6`, `0x5789E`, `0x579C0`
- classification: `TITLE_SPRITE_DESCRIPTOR_BUFFER`

3. `A0=0x00C00100`
- semantic meaning: direct write target in arcade C-window/MMIO space (hardware-era output path)
- evidence:
  - title prep write: `0x03B076` loads `A0=0x00C00100`, then calls fill helper
- classification: `DIRECT_HARDWARE_OUTPUT`

4. `A0=0xE0FFC954`
- semantic meaning: WRAM shadow-style/staging sink paired with `0x00C00100` fill call in title-prep helper
- evidence:
  - title prep write: `0x03B086`
  - immediate appears only at this site in Build 223 binary scan
- classification: `LEGACY_C_WINDOW_SHADOW`

## 4) Final-State Validity Per Output

1. `0xE0FF404C`
- should still exist in final architecture? `NO`
- why: this is D-window shadow backing (`genesistan_shadow_d00000_words`), and project direction is to remove this after sprite rewrites.
- final Genesis-native owner: title/front-end sprite SAT construction path (`genesistan_render_sprites_vdp` / final `vdp_sprite_sat_build_*`) writing VDP SAT + tile uploads directly.

2. `0xE0FF41BC`
- should still exist in final architecture? `NO`
- why: although currently used as an active descriptor buffer, it is still a sub-buffer of D-window shadow memory.
- final Genesis-native owner: same sprite SAT pipeline as above, with descriptors sourced from validated workram structures and emitted directly to VDP SAT.

3. `0x00C00100`
- should still exist in final architecture? `NO`
- why: this is direct hardware-era output into arcade C-window address space semantics.
- final Genesis-native owner: VDP-native tilemap/text clear/write path (`vdp_plane_region_clear` + text/tile hooks), not raw C-window-space writes.

4. `0xE0FFC954`
- should still exist in final architecture? `NO`
- why: legacy shadow/staging style target with no proven standalone live consumer in Build 223.
- final Genesis-native owner: either removed entirely if no consumer, or replaced by explicit Genesis-side owned staging buffer only if a proven consumer remains.

## 5) Downstream Consumer Audit

1. `0xE0FF404C`
- downstream consumers/producers observed:
  - write/build routines: `0x03AF5E`, `0x03AF84`, `0x52CC0`, `0x542CA`, `0x54A2E`, `0x56656`, `0x579C0`
  - indirect use via +0x170 descriptor windows
- consumer live in Build 223: `YES`
- Genesis-valid or legacy-only: `LEGACY-ONLY` (shadow D-window descriptor chain)

2. `0xE0FF41BC`
- downstream consumers observed:
  - table-copy and descriptor handlers: `0x5625C -> 0x54369`, `0x56286 -> 0x5632A`
  - per-frame update loops: `0x562C6`, `0x5788A`, `0x578E8`, `0x57908`, `0x579C0`
- consumer live in Build 223: `YES`
- Genesis-valid or legacy-only: `LEGACY-ONLY` (still D-window shadow chain)

3. `0x00C00100`
- downstream consumer observed: none in software; written for hardware-side effects by `0x03B076`
- consumer live in Build 223: write site is live, software consumer not proven
- Genesis-valid or legacy-only: `LEGACY-ONLY` direct hardware-era output

4. `0xE0FFC954`
- downstream consumer observed: none proven beyond write site (`0x03B086`)
- consumer live in Build 223: `UNKNOWN/NOT PROVEN`
- Genesis-valid or legacy-only: `LEGACY-ONLY` shadow-style staging target

## 6) Final Architecture Judgment
Primary answer:
- **restored helper behavior is restoring legacy output semantics that should be replaced with Genesis-native logic**.

Why:
- 3/4 restored targets are clearly legacy shadow or direct hardware-era outputs.
- the remaining target (`0xE0FF41BC`) is active but still anchored to D-window shadow ownership.
- no restored target is a final direct VDP-native ownership endpoint.

## 7) Minimal Correct Next Step
=== TITLE_PREP_FINAL_STATE_NEXT_STEP ===
- keep_or_replace: `REPLACE`
- exact_target_or_path: `title-prep fill path 0x03AF5E/0x03B076 that currently emits to 0xE0FF404C, 0xE0FF41BC, 0x00C00100, 0xE0FFC954`
- final_owner_system: `Genesis-native title render pipeline: direct sprite SAT builder + VDP tilemap/text clear/write path`
- why_this_is_the_correct_next_step: `the restored outputs are predominantly legacy shadow/hardware endpoints; replacing ownership at this path aligns title prep with final architecture instead of extending transitional shadow behavior`
- what_must_NOT_be_done: `do not restore additional legacy helpers, do not add bypass/NOP scaffolds, do not reintroduce shadow RAM as a long-term mechanism`

## 8) Uncertainties
- `0xE0FFC954` has no proven consumer in Build 223 disassembly scans; full dynamic provenance was not captured in this pass.
- some `0xE0FF404C` references outside title range may be data-like or non-title code paths; classification is based on proven title/front-end relevant call clusters.

## 9) Conclusion
The Build 223 title-prep scaffold replacement restored execution, but the restored write targets are still legacy shadow/direct-hardware-era outputs. For final architecture, this path should be replaced by direct Genesis-owned sprite/tilemap title prep ownership rather than kept as-is.
