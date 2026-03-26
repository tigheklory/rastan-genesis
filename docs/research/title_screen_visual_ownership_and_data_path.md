# Title Screen Visual Ownership and Data Path (Build 220)

## 1) Purpose
Identify exactly which code/data paths are responsible for drawing the title screen in Build 220, and determine why title visuals remain incomplete/garbage-heavy after dispatch-target fixes.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant sections)
- `README.md`
- `docs/research/title_screen_state_cluster_analysis.md`
- `dist/Rastan_220.bin` (direct ROM disassembly via `m68k-elf-objdump`)
- `apps/rastan/src/main.c` (title text hook implementation)
- `specs/startup_title_remap.json` (shift-table context)

## 3) Title Visual Entry Path
Proven title cluster (Build 220):
- major/title cluster: `0x03AAB8..0x03ABF6`
- init body: `0x03AADE..0x03AB20`
- idle/coin body: `0x03AB28..0x03ABF6`

Title init/output call chain from `0x03AADE`:
- `0x03AADE -> bsr 0x03AFEA` (state/display control flags)
- `0x03AAE2 -> bsr 0x03AF5E` (buffer prep helper path)
- `0x03AAE6 -> bsr 0x03B06C` (setup helper; internally calls text/scroll path)
- `0x03AAEC -> jsr 0x20060C` (`genesistan_render_sprites_vdp` bridge)
- `0x03AAF2 -> jsr 0x05A174` (logo/sprite descriptor initializer)
- `0x03AAFA/0x03AB0A/0x03AB16/0x03AB1C -> bsr 0x03BD5E -> jsr 0x2027B8`
  (`genesistan_hook_text_writer_3bb48` bridge)
- `0x03AB0E -> jsr 0x05A626` (title lower text/layout helper)

Additional pre-coin visual path in same state family:
- `0x03AA9C -> jsr 0x059F36` (table-driven conversion helper)

Type classification in this path:
- text/tile related: `0x03BD5E -> 0x2027B8`, `0x05A626`, `0x059F36/0x059CEA`
- sprite/logo related: `0x05A174`, `0x20060C` (sprite render bridge)
- palette related: per-frame `load_arcade_palette()` in frontend loop, plus conversion helper family (`0x059F36/0x059CEA`) used in title-state visuals
- background/tilemap related: `0x03AF5E`, `0x03B06C` (including nested `0x03B076` path)

## 4) Title Element Ownership
1. Top HUD text (`1UP`, `HIGH SCORE`, `2UP`)
- trigger in title state: `0x03AAFA`, `0x03AB0A`
- helper/routine: `0x03BD5E -> 0x2027B8 (genesistan_hook_text_writer_3bb48)`
- data source: text ID descriptor table consumed by hook (`TEXT_WRITER_3BB48_TABLE_BASE` in C)
- confidence: High

2. Large RASTAN logo / sword-T
- trigger in title state: `0x03AAF2`
- helper/routine: `0x05A174`, then `0x20060C (genesistan_render_sprites_vdp)`
- data source: descriptor writes to work/shadow memory regions (`0xE0FF4094`, `0x0010C170` immediates in helper)
- confidence: Medium

3. TAITO text
- trigger in title state: `0x03AB0E` + `0x03AB14`
- helper/routine: `0x05A626` + `0x03BD5E`
- data source: helper table bases `0x05A970`, `0x05B178`; plus text ID dispatch via `0x03BD5E`
- confidence: Medium

4. Copyright lines
- trigger in title state: `0x03AB1C`
- helper/routine: `0x03BD5E -> 0x2027B8`
- data source: text ID table via hook
- confidence: Medium

5. `CREDIT 0`
- trigger in title state: idle body `0x03AB28..`
- helper/routine: coin/credit logic in idle body + text/refresh helper calls (`0x03C4F8`, `0x03BA14`, sprite refresh calls)
- data source: A5 credit fields (`A5+0x0012`) and text helper path
- confidence: Medium

6. Title background/tile preparation
- trigger in title state: `0x03AADE/0x03AAE2/0x03AAE6` and pre-coin `0x03AA9C`
- helper/routine: `0x03AFEA`, `0x03AF5E`, `0x03B06C`, `0x059F36`
- data source: helper-local immediate bases and conversion tables
- confidence: High

## 5) Data/Table Source Validation
- `0x03BD5E -> 0x2027B8 -> genesistan_hook_text_writer_3bb48_impl`
  - dependency: `TEXT_WRITER_3BB48_TABLE_BASE` (`main.c`) currently `0x003BD7C`
  - expected shifted entry for arcade `0x03BB7C`: `0x003BD92` (delta +0x16)
  - classification: **STALE_TABLE_BASE**

- `genesistan_hook_text_writer_3c3fe` (not primary title init call, but same title text system family)
  - dependency: `TEXT_WRITER_3C3FE_TABLE_BASE` currently `0x003C654`
  - expected shifted entry for arcade `0x03C454`: `0x003C66C` (delta +0x18)
  - classification: **POSSIBLE_STALE_TABLE_BASE**

- `0x059F36`
  - dependency: `movea.l #0x059E9A,a3` table base immediate
  - observed at `0x059E9A`: executable-code bytes, not table base blob; table-like blob starts later (`0x059EB0` region)
  - classification: **STALE_TABLE_BASE**

- `0x059E6A` / `0x059EE4` (same conversion/helper family)
  - dependency: same `movea.l #0x059E9A,a3` base immediate
  - classification: **STALE_TABLE_BASE**

- `0x05A626`
  - dependencies: `lea 0x05A970,a0`, `lea 0x05B178,a0`, `jsr 0x059CEA`
  - these immediate targets resolve to dense data-like blocks and a live helper entry
  - classification: **VALID**

- `0x05A174`
  - dependencies: immediate work/shadow addresses only (`0xE0FF4094`, `0x0010C170`), no title table-base immediate
  - classification: **VALID**

- `0x03AF5E` / `0x03B06C` title prep helpers
  - dependency: call chain into `0x03AF56` scaffold body
  - classification: **SCAFFOLD_DEPENDENCY**

## 6) Title-Specific Scaffold Audit
- Path: `0x03AAE2 -> 0x03AF5E -> 0x03AF56`
  - result: called worker body at `0x03AF56` is NOP/NOP/NOP/RTS
  - title impact: expected prep side effects are effectively no-op
  - classification: **TITLE_TEXT_SCAFFOLD_RISK**

- Path: `0x03AAE6 -> 0x03B06C -> 0x03B076 -> 0x03AF56`
  - result: nested prep path also funnels through NOP/RTS scaffold
  - title impact: title background/text prep path partially no-op
  - classification: **TITLE_TEXT_SCAFFOLD_RISK**

- Path: title text dispatch `0x03AAFA/0x03AB0A/0x03AB14/0x03AB1C -> 0x03BD5E -> 0x2027B8`
  - result: path is live, but consumes stale text table base in C hook constants
  - classification: **TITLE_DATA_STALE_RISK**

- Path: title logo/sprite `0x03AAF2 -> 0x05A174 -> 0x20060C`
  - result: live helper + live sprite bridge observed; no scaffold on this direct chain
  - classification: **SAFE**

- Path: pre-coin conversion `0x03AA9C -> 0x059F36`
  - result: live path with stale table-base immediate (`0x059E9A`)
  - classification: **TITLE_DATA_STALE_RISK**

## 7) Ranked Title-Screen Blockers
1. **TITLE_DATA_TABLE_STALE**
- Proven stale bases in title-active paths:
  - `0x059F36` family uses stale `0x059E9A`
  - title text hook constants in `main.c` are stale vs shifted table locations

2. **TITLE_SCAFFOLD_DEPENDENCY**
- Title init helper paths (`0x03AF5E`, `0x03B06C`) depend on `0x03AF56` NOP/RTS body, suppressing expected prep work.

3. **TITLE_BACKGROUND_TILEMAP_PATH_BROKEN**
- Resulting from #1/#2 in title-prep helper chains; background/text composition remains incomplete/garbage-heavy.

## 8) Minimal Next Fix Target
=== TITLE_VISUAL_MINIMAL_FIX_TARGET ===
- fix_area: title-visual data-base correctness in active title text/conversion helpers.
- exact_helper_or_data_path: `genesistan_hook_text_writer_3bb48_impl` table-base constants (`TEXT_WRITER_3BB48_TABLE_BASE`, and same-family `3C3FE` base) plus `0x059F36/0x059E6A/0x059EE4` A3 table-base immediate currently set to `0x059E9A`.
- why_this_is_the_minimum_title-visual_step: dispatch targets are already corrected; title visuals are now blocked primarily by stale table/data bases on live title-output paths.
- what_must_NOT_be_changed: no forced state changes, no NOP insertion/bypass, no startup/launcher/gameplay redesign, no shadow RAM reintroduction.

## 9) Uncertainties
- Exact per-element ownership split between `0x05A626` helper output and text IDs (`30/32`) remains medium confidence without a direct on-screen correlated capture.
- `0x03AF56` original intended side effects are not reconstructed in this pass; only current scaffold impact is proven.

## 10) Conclusion
With title dispatch fixed, Build 220 title visuals remain broken primarily due stale data/table bases on live title text/conversion paths, with secondary suppression from title-init helpers that currently route into scaffolded NOP/RTS bodies.
