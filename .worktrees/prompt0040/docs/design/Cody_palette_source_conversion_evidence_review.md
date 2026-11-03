# [Cody — Palette Source and Conversion Evidence Review]

Type: Read-only project artifact review  
Scope: Project-internal artifacts only (no external sources, no implementation)

## 1. Required artifacts reviewed

- `RULES.md` (109 lines) and `ARCHITECTURE.md` (162 lines) were read in full.
- `AGENTS_LOG.md` context around line 21335 and later palette-related entries were reviewed.
- `docs/design/Andy_build54_palette_root_cause.md` reviewed.
- `docs/design/Cody_build54_cram_white_palette_evidence.md` reviewed.
- `apps/rastan-direct/src/scene_load.s` reviewed.
- `apps/rastan-direct/src/vdp_comm.s` reviewed.
- `tools/build_rastan_regions.py` reviewed.
- `build/regions/variant.json` reviewed.

## 2. Project-internal evidence inventory

### 2.1 Where palette data was expected to come from

- AGENTS_LOG documents design intent:
  - `DMA D: palette — ROM table → CRAM (128 bytes); per scene change only` at `AGENTS_LOG.md:21335`.
- Andy root-cause document repeats that design intent and ties it to the missing producer:
  - `docs/design/Andy_build54_palette_root_cause.md:20`
  - `docs/design/Andy_build54_palette_root_cause.md:67`
  - `docs/design/Andy_build54_palette_root_cause.md:73`

### 2.2 How many palette entries were expected

- Design intent explicitly states `128 bytes` (64 words):
  - `AGENTS_LOG.md:21335`
  - `docs/design/Andy_build54_palette_root_cause.md:20`
  - `docs/design/Andy_build54_palette_root_cause.md:124`

### 2.3 Scene-ID mapping evidence

- Current direct path scene selection is explicit in `load_scene_tiles`:
  - scene `0` title (default path) / scene `1` gameplay / scene `2` endround:
    - `apps/rastan-direct/src/scene_load.s:33`
    - `apps/rastan-direct/src/scene_load.s:34`
    - `apps/rastan-direct/src/scene_load.s:36`
    - `apps/rastan-direct/src/scene_load.s:39`
    - `apps/rastan-direct/src/scene_load.s:41`
    - `apps/rastan-direct/src/scene_load.s:44`
- Current direct path includes tile preload manifests only (no palette manifests):
  - `apps/rastan-direct/src/scene_load.s:112`
  - `apps/rastan-direct/src/scene_load.s:117`
  - `apps/rastan-direct/src/scene_load.s:122`

### 2.4 Existing conversion evidence inside the project

- Legacy/SGDK-era conversion code exists in `apps/rastan/src/main.c`:
  - `convert_xbgr555_to_genesis` at `apps/rastan/src/main.c:1008`
  - `convert_clcs_to_genesis` at `apps/rastan/src/main.c:1020`
  - `load_arcade_palette` uses `genesistan_palette_clcs`/`genesistan_palette_rom_table` at:
    - `apps/rastan/src/main.c:630`
    - `apps/rastan/src/main.c:652`
    - `apps/rastan/src/main.c:659`
    - `apps/rastan/src/main.c:660`
- Legacy palette symbols exist in SGDK-era startup bridge:
  - `genesistan_palette_rom_table` at `apps/rastan/src/startup_bridge.c:125`
  - `genesistan_palette_clcs` at `apps/rastan/src/startup_bridge.c:128`
- Patcher history includes an in-tool conversion function and palette table fill:
  - `_taito_to_genesis` and `palette_pre_conversion` comments/logic:
    - `tools/translation/postpatch_startup_rom.py:1536`
    - `tools/translation/postpatch_startup_rom.py:1537`
    - `tools/translation/postpatch_startup_rom.py:1547`
    - `tools/translation/postpatch_startup_rom.py:1570`

### 2.5 Prior implementation evidence in repo history

- `apps/rastan-direct/src/main_68k.s` existed and was later deleted:
  - deletion recorded at `git` commit `ec0445d` (`D apps/rastan-direct/src/main_68k.s`).
- Prior `main_68k.s` contained palette staging/commit symbols:
  - `palette_dirty`, `staged_palette_words`, `vdp_commit_palette`, `palette_init_words` found in commit `5ccb0ce` snapshot.
  - Example locations from that snapshot:
    - `init_staging_state` clears `palette_dirty` and `staged_palette_words`:
      - `5ccb0ce:apps/rastan-direct/src/main_68k.s` lines 2052, 2057
    - `palette_init_words` table:
      - `5ccb0ce:apps/rastan-direct/src/main_68k.s` line 2173

## 3. Current direct-path evidence gaps (project artifacts only)

- Current direct palette infrastructure exists (`vdp_commit_palette`, `palette_dirty`, `staged_palette_words`):
  - `apps/rastan-direct/src/vdp_comm.s:168`
  - `apps/rastan-direct/src/vdp_comm.s:171`
  - `apps/rastan-direct/src/vdp_comm.s:274`
  - `apps/rastan-direct/src/vdp_comm.s:299`
  - `apps/rastan-direct/src/vdp_comm.s:329`
- Current direct producer path is not present in current source:
  - `scene_load.s` has tile loading only in current file body (`apps/rastan-direct/src/scene_load.s:27-94`).
- Current build-region generator emits only `maincpu`, `pc080sn`, `pc090oj`, `audiocpu`, `adpcm` and `variant.json`:
  - `tools/build_rastan_regions.py:175`
  - `tools/build_rastan_regions.py:185`
  - `tools/build_rastan_regions.py:199`
  - `tools/build_rastan_regions.py:212`
  - `tools/build_rastan_regions.py:213`
  - `tools/build_rastan_regions.py:215`
- Current variant manifest contains only maincpu variant metadata:
  - `build/regions/variant.json:2`

## 4. Required yes/no determinations

- Existing palette source evidence found in project: **YES**
- Existing conversion evidence found in project: **YES**
- Existing scene mapping evidence found in project: **YES** (scene IDs 0/1/2 mapping exists in `scene_load.s`)
- Prior implementation found in git history: **YES**

## 5. Phase 2 readiness assessment (inventory-only)

Phase 2 readiness: **BLOCKED**

Missing evidence to proceed from current project artifacts alone:

1. A direct-rastan active palette source artifact (scene palette data files or direct-table symbols) in current build outputs/sources.
2. A direct-rastan current-path artifact that selects one conversion path for Build 54 producer work (legacy/SGDK evidence exists, but current direct path does not include an active producer implementation using one of those conversions).
3. A current direct build artifact mapping scene `0/1/2` to concrete palette payload files analogous to existing tile preload manifests.

## 6. Stop-condition status

- STOP triggered: **NO**
- Reason: Required files were readable; this task remained project-internal and implementation-free.
