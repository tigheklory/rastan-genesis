# [Cody — Palette Code Deletion Context Audit]

Type: Read-only project artifact review (documentary archaeology + cross-reference comparison)  
Build context: rastan-direct Build 0054

## §1.1 — Commit `ec0445d` inspection

Commit metadata (verbatim):

- Commit: `ec0445d191cb45139729b8ad7e18f4f0e7c90ca2`
- Subject: `Build 50`
- AuthorDate: `Mon Apr 20 22:38:43 2026 -0400`

Palette/deletion-context file movements in this commit:

- `apps/rastan-direct/src/main_68k.s` was renamed to `apps/rastan-direct/src/tilemap_hooks.s` with 71% similarity.
- `apps/rastan-direct/src/vdp_comm.s` was added.
- `apps/rastan-direct/src/scene_load.s` was added.
- Commit stat for these three files: `476 insertions(+), 602 deletions(-)`.

Citations:

- commit summary (`rename`/`create`): `git show -M --summary ec0445d -- apps/rastan-direct/src/main_68k.s apps/rastan-direct/src/tilemap_hooks.s apps/rastan-direct/src/scene_load.s apps/rastan-direct/src/vdp_comm.s`
- commit stat: `git show -M --stat ec0445d -- apps/rastan-direct/src/main_68k.s apps/rastan-direct/src/tilemap_hooks.s apps/rastan-direct/src/scene_load.s apps/rastan-direct/src/vdp_comm.s`
- AGENTS_LOG Build 50 decomposition entry:
  - `main_68k.s (deleted)` plus new `vdp_comm.s`, `tilemap_hooks.s`, `scene_load.s`: [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:30099)
  - `main_68k.s deleted: YES`: [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:30107)
  - Makefile object split (`main_68k.o` removed; new objects added): [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:30114)

Palette-related replacement in same commit:

- Removed from old `main_68k.s` patch view:
  - `palette_dirty` gate lines
  - `vdp_commit_palette`
  - `palette_init_words`
  - `staged_palette_words`
- Added in same commit patch view:
  - `.global vdp_commit_palette`
  - `.global _vblank_service`
  - `.global palette_dirty`
  - `.global staged_palette_words`
  - `_vblank_service` palette gate and `vdp_commit_palette` in new file

Citation:

- `git show -M ec0445d -- apps/rastan-direct/src/main_68k.s apps/rastan-direct/src/vdp_comm.s apps/rastan-direct/src/scene_load.s | rg -n "palette|staged_palette_words|palette_dirty|vdp_commit_palette|_vblank_service|palette_init_words"`

## §1.2 — Commit `5ccb0ce` snapshot (`main_68k.s`)

Snapshot section reviewed:

- `init_staging_state` at lines including:
  - `clr.b   palette_dirty`
  - `lea     staged_palette_words, %a0`
  - clear loop over 64 words

Citation:

- `git show 5ccb0ce:apps/rastan-direct/src/main_68k.s | nl -ba | sed -n '2038,2325p'`

`palette_init_words` sample (first 16 entries, verbatim):

```asm
.word 0x0000,0x000E,0x00E0,0x0E00,0x00EE,0x0E0E,0x0EE0,0x020C
.word 0x0022,0x0046,0x006A,0x008C,0x00A2,0x00C6,0x00EA,0x002E
```

Citation:

- `5ccb0ce:apps/rastan-direct/src/main_68k.s` lines shown in:
  - `git show 5ccb0ce:apps/rastan-direct/src/main_68k.s | nl -ba | sed -n '2148,2208p'`

`staged_palette_words` / `palette_dirty` declarations in snapshot:

- `palette_dirty:` byte symbol exists
- `staged_palette_words:` 64×2-byte space exists

Citation:

- same `sed -n '2038,2325p'` snapshot output above.

## §1.3 — SGDK C implementation inspection

### `apps/rastan/src/main.c`

`convert_xbgr555_to_genesis` (verbatim):

```c
static u16 convert_xbgr555_to_genesis(u16 raw)
{
    const u16 r = (raw >> 0) & 0x1F;
    const u16 g = (raw >> 5) & 0x1F;
    const u16 b = (raw >> 10) & 0x1F;
    const u16 rn = (u16)(((r >> 2) & 0x07) << 1);
    const u16 gn = (u16)(((g >> 2) & 0x07) << 1);
    const u16 bn = (u16)(((b >> 2) & 0x07) << 1);

    return (u16)((bn << 8) | (gn << 4) | rn);
}
```

`convert_clcs_to_genesis` (verbatim):

```c
static u16 convert_clcs_to_genesis(u16 raw)
{
    return (u16)(((raw >> 1) & 0x000EU)
               | ((raw >> 2) & 0x00E0U)
               | ((raw >> 3) & 0x0E00U));
}
```

`load_arcade_palette` (verbatim body excerpt):

```c
static void load_arcade_palette(void)
{
    uint16_t buf[64];
    uint16_t i;
    uint16_t block = 0xFFFFU;
    uint16_t b;

    for (b = 0; b < (2048U / 64U); b++) {
        const uint16_t base = (uint16_t)(b * 64U);
        for (i = 0; i < 64U; i++) {
            if (genesistan_palette_clcs[base + i] != 0) {
                block = b;
                break;
            }
        }
        if (block != 0xFFFFU) {
            break;
        }
    }

    if (block == 0xFFFFU) {
        SYS_disableInts();
        PAL_setColors(0, (const u16 *)genesistan_palette_rom_table, 64, DMA);
        VDP_waitDMACompletion();
        SYS_enableInts();
        return;
    }

    for (i = 0; i < 64U; i++) {
        const uint16_t c = genesistan_palette_clcs[(block * 64U) + i];
        buf[i] = convert_clcs_to_genesis(c);
    }

    SYS_disableInts();
    PAL_setColors(0, (const u16 *)buf, 64, DMA);
    VDP_waitDMACompletion();
    SYS_enableInts();
}
```

Citations:

- [main.c](/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c:630)
- [main.c](/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c:1008)

### `apps/rastan/src/startup_bridge.c`

Palette declarations (verbatim):

```c
const uint16_t genesistan_palette_rom_table[2048] = {0};
uint16_t genesistan_palette_clcs[2048]
    __attribute__((section(".bss.patcher")));
```

Citation:

- [startup_bridge.c](/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_bridge.c:117)

### Other SGDK palette-related source in `apps/rastan/src/`

- `apps/rastan/src/startup_trampoline.s` contains:
  - `genesistan_palette_commit_asm` with in-file comment:
    - `TEMPORARY PROOF FIX (Build 320)`
    - `TEMPORARY diagnostic fix — not final palette architecture`
  - second symbol occurrence under stub section (`genesistan_palette_commit_asm: rts`)

Citation:

- [startup_trampoline.s](/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_trampoline.s:85)
- [startup_trampoline.s](/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_trampoline.s:1001)

## §1.4 — Cross-reference findings

### Deleted (`5ccb0ce`) ↔ SGDK C

Observed overlaps:

- Both contain palette-buffer/dirty concepts and startup/commit-era palette symbols.
- `5ccb0ce` snapshot has `palette_init_words`/`staged_palette_words`/`palette_dirty`.
- SGDK C has `genesistan_palette_rom_table`/`genesistan_palette_clcs` plus conversion and load function.

Observed difference:

- `5ccb0ce` snapshot excerpt reviewed shows static `palette_init_words` table usage context in asm snapshot.
- SGDK C `load_arcade_palette` path reads from `genesistan_palette_clcs` with fallback to `genesistan_palette_rom_table`.

Classification for this relation (evidence-only): **unclear** (derived/superseded/unrelated not explicitly documented in commit message text).

### SGDK C ↔ postpatcher `_taito_to_genesis`

Observed:

- SGDK C `convert_clcs_to_genesis` bit-shift pattern:
  - `((raw >> 1) & 0x000E) | ((raw >> 2) & 0x00E0) | ((raw >> 3) & 0x0E00)`
- postpatcher `_taito_to_genesis`:
  - `r3 = ((src >> 8) & 0xF) >> 1`
  - `g3 = ((src >> 4) & 0xF) >> 1`
  - `b3 = (src & 0xF) >> 1`
  - `return (r3 << 1) | (g3 << 5) | (b3 << 9)`

Citations:

- [main.c](/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c:1020)
- [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py:1547)

Comparison result for SGDK C ↔ postpatcher: **match** (for that CLCS conversion path expression set).

### Palette data character evidence

Observed:

- Postpatcher palette block is explicitly labeled `Build 113 placeholder` and `Greyscale ramp`.
- AGENTS_LOG records `palette_init_words` as diagnostic values in prior direct-era work.
- AGENTS_LOG later records that `palette_init_words` execution path was removed from normal boot while symbol remained.

Citations:

- [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py:1573)
- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:26015)
- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:29049)
- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:29063)

Palette data character classification: **placeholder/diagnostic evidence present** (in the cited project artifacts).

## §1.5 — Best-supported evidence path (project-internal documentation support)

Best-supported path in project documentation/history: **`postpatch_startup_rom.py` + `startup_bridge.c` + SGDK C runtime fallback/capture path**.

Evidence basis:

- Explicit comments in tool code on source/target format and placeholder note:
  - [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py:1536)
  - [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py:1573)
- SGDK symbols and runtime load logic are present and cross-referenced by name:
  - [startup_bridge.c](/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_bridge.c:125)
  - [main.c](/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c:630)
- AGENTS_LOG continuity references these symbols and paths across multiple entries:
  - [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:9998)
  - [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:10257)

## §1.6 — Deletion classification

Deletion classification from cited artifacts:

- `main_68k.s` deletion occurred in a decomposition commit that simultaneously added `vdp_comm.s`, `tilemap_hooks.s`, and `scene_load.s` and updated Makefile object list.
- Palette commit infrastructure symbols moved into `vdp_comm.s` in the same commit patch stream.
- `palette_init_words`/synthetic startup path was recorded later as non-executing in normal boot.

Classification: **intentionally obsolete (decomposition/split) with partial replacement of infrastructure in new files; diagnostic palette table path not carried as an active normal-boot producer path in current direct source.**

Citations:

- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:30099)
- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:30114)
- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:29049)
- [AGENTS_LOG.md](/home/tighe/projects/rastan-genesis/AGENTS_LOG.md:29063)
- `git show -M` commit evidence in §1.1 and palette symbol migration grep in §1.1.

## Phase 2 — Integrity

- §1.1 commit `ec0445d` inspected: **YES**
- §1.2 commit `5ccb0ce` snapshot inspected: **YES**
- §1.3 SGDK C implementation inspected: **YES**
- §1.4 cross-reference comparison performed: **YES**
- §1.5 best-supported path identified: **YES**
- §1.6 deletion classified: **YES**
- All findings cited from artifacts: **YES**
- No analysis/hypotheses/recommendations/implementation: **YES**
- No external sources: **YES**
- SGDK treated as evidence, not authority: **YES**
- All three sources cross-referenced: **YES**
- No source/spec/tool modifications: **YES**

## Phase 2 readiness status (for downstream authority selection)

- Phase 2 readiness: **BLOCKED**
- Evidence still missing for direct implementation authority selection:
  1. Current direct-rastan authoritative palette producer source path in active `apps/rastan-direct/src/` (not historical SGDK/deleted asm evidence).
  2. Current direct-rastan authoritative palette payload mapping artifact per scene (`0/1/2`) analogous to tile manifests.
  3. Explicit project artifact selecting which historical conversion path is authoritative for the current direct-rastan producer path.
