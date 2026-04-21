# Andy — VRAM Tile-Start Offset Analysis

**Agent:** Andy
**Type:** Forensic Analysis + Design (no implementation)
**Build context:** Build 0050+ `rastan-direct`
**Architecture compliance:** CONFIRMED (analysis-only; no source, spec, or tool modifications).

**Outcome:** producer and consumer **agree** on a VRAM tile-slot base of **0x14 (tile 20)**. Origin is **INHERITED_FROM_SGDK** with concrete documentary evidence. The offset is **NOT required** by any current rastan-direct Genesis-side consumer; it is a legacy SGDK-era reservation of 20 low VRAM tile slots. Minimum correct production fix: change **one constant** in `tools/translation/precompute_pc080sn_tile_lut.py:39` from `TILE_CACHE_BASE_A = 20` to `TILE_CACHE_BASE_A = 1` (keeping slot 0 reserved as the LUT's "unmapped" sentinel). Both producer and consumer regenerate atomically from the same tool, so the change is a single-file edit. **Confidence: HIGH.** The briefing's classification of "deferred optimization, not a blocking bug" is correct — no rendering corruption exists.

---

## Address-space legend

- `VRAM_OFFSET 0x<xxxx>` — byte offset within Genesis VRAM.
- `tile_index 0x<xx>` — VRAM tile slot number; `VRAM_OFFSET = tile_index × 0x20` (each 8×8 4bpp tile is 32 bytes).
- `arcade_tile 0x<xxxx>` — 14-bit arcade tile code (0..0x3FFF) from PC080SN C-window / ROM.
- file:line citations refer to the current working tree.

---

## Phase 1 — Producer analysis (upload side)

### 1. Locate `genesistan_pc080sn_tile_vram_lut`

- Declaration (assembly): [apps/rastan-direct/src/scene_load.s:5, 99-100](apps/rastan-direct/src/scene_load.s#L99-L100)
- Binary: [build/pc080sn_tile_vram_lut.bin](build/pc080sn_tile_vram_lut.bin), 32768 bytes = 16384 × u16 words.
- Generator: [tools/translation/precompute_pc080sn_tile_lut.py](tools/translation/precompute_pc080sn_tile_lut.py), writer at line 608.

### 2. Locate scene preload tables

- Declarations: [apps/rastan-direct/src/scene_load.s:8-13, 111-123](apps/rastan-direct/src/scene_load.s#L111-L123)
- Binaries:
  - [build/pc080sn_scene_preload_title.bin](build/pc080sn_scene_preload_title.bin), 3366 bytes.
  - [build/pc080sn_scene_preload_gameplay.bin](build/pc080sn_scene_preload_gameplay.bin), 3318 bytes.
  - [build/pc080sn_scene_preload_endround.bin](build/pc080sn_scene_preload_endround.bin), 4270 bytes.
- Generator: `write_scene_manifest()` at [tools/translation/precompute_pc080sn_tile_lut.py:430-436](tools/translation/precompute_pc080sn_tile_lut.py#L430-L436) called from `main()` lines 619-621.

### 3. First-tile upload VRAM destination

First 8 words of `build/pc080sn_scene_preload_title.bin` (big-endian, pairs of `(arcade_tile, dst_slot)`):

```
offset 0x00:  0x0020  0x0014   ← first pair: arcade tile 0x20 → dst slot 0x14
offset 0x04:  0x0023  0x0015
offset 0x08:  0x0024  0x0016
offset 0x0C:  0x0025  0x0017
```

[apps/rastan-direct/src/scene_load.s:52-67](apps/rastan-direct/src/scene_load.s#L52-L67) processes this manifest:

```
.Lload_scene_pair_loop:
    move.w  (%a0)+, %d2        ; d2 = arcade_tile (source)
    cmpi.w  #0xFFFF, %d2
    beq.s   .Lload_scene_pairs_done
    move.w  (%a0)+, %d3        ; d3 = dst_slot
    ...
    moveq   #0, %d0
    move.w  %d3, %d0
    lsl.l   #5, %d0             ; d0 = dst_slot × 32  → VRAM byte offset
    bsr     vdp_set_vram_write_addr
```

For the first pair `d3 = 0x0014`: `d0 = 0x0014 × 0x20 = 0x0280`.

```
First tile upload destination:  VRAM_OFFSET 0x00000280 = tile index 0x0014 (20 decimal)
Source of the offset:            precompute_pc080sn_tile_lut.py:39 `TILE_CACHE_BASE_A = 20`
Derivation chain:
  1. precompute_pc080sn_tile_lut.py:39  `TILE_CACHE_BASE_A = 20`
  2. precompute_pc080sn_tile_lut.py:347-351 `build_slot_sequence()` begins with `range(20, 20+1004)`
  3. precompute_pc080sn_tile_lut.py:381-399 `assign_tile()` picks the first available slot
     from that sequence (= 20) for the first tile assigned
  4. precompute_pc080sn_tile_lut.py:619 `write_scene_manifest(...SCENE_TITLE,...)` emits pair
     (arcade_tile=0x20, dst_slot=0x14) as the first title entry
  5. build/pc080sn_scene_preload_title.bin first 4 bytes: 00 20 00 14 (verified via xxd)
  6. scene_load.s:66 `lsl.l #5, %d0` — multiplies dst_slot by 32
  7. scene_load.s:67 `bsr vdp_set_vram_write_addr` programs the VDP to write at VRAM byte 0x280
```

---

## Phase 2 — Consumer analysis (reference side)

### 2a. Tilemap / nametable writes (`staged_bg_buffer`, `staged_fg_buffer`)

The BG and FG strip hooks in `apps/rastan-direct/src/tilemap_hooks.s` translate arcade tile codes to Genesis VRAM slots via runtime LUT lookup, **not via any hardcoded offset**.

From [apps/rastan-direct/src/tilemap_hooks.s](apps/rastan-direct/src/tilemap_hooks.s) (pattern used by `genesistan_hook_tilemap_plane_a`, `_tilemap_fg`, `_tilemap_bg_fill`, `_cwindow_clear`, and every `_text_writer_*` hook):

```asm
lea     genesistan_pc080sn_tile_vram_lut, %a2
...
move.w  (%a4), %d3            ; d3 = arcade tile code from C-window
andi.w  #0x3FFF, %d3           ; mask to 14-bit tile index
add.w   %d3, %d3               ; *2 for word-indexed LUT
move.w  0(%a2,%d3.w), %d3      ; d3 = LUT[arcade_tile] = VRAM slot
or.w    (%sp), %d3             ; combine with attribute bits
move.w  %d3, 0(%a6,%d0.w)      ; write to staged_{bg,fg}_buffer as nametable entry
```

The hook writes the **LUT value verbatim** as the Genesis nametable tile index. No addition, no subtraction, no `#0x14` constant appears anywhere in `tilemap_hooks.s`.

### 2b. Sprite descriptor translation

Sprite Block-A translation logic is not yet wired in the current rastan-direct build (the sprite hooks listed in the decomposition design — `genesistan_hook_tilemap_*` — handle only PC080SN tilemap, not PC090OJ sprites). No current Genesis-side consumer of sprite tile indices exists.

### 2c. `opcode_replace` entries that write tile indices directly

Grepped [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json): every `replacement_bytes` field encodes either `{symbol:…}` placeholders (resolved to Genesis WRAM / helper symbol addresses, never to VRAM tile slots) or NOP pads / pointer literals. **No opcode_replace entry writes a VRAM tile index directly.**

### Consumer reference-site table

| site | file:line / spec entry | role | tile-base assumption | evidence |
| ---- | ---------------------- | ---- | --------------------- | -------- |
| `genesistan_hook_tilemap_plane_a` (BG strip hook) | [tilemap_hooks.s](apps/rastan-direct/src/tilemap_hooks.s) (lines with `0(%a2,%d3.w)` LUT lookup) | read `LUT[arcade_tile]` → emit as nametable tile index | **whatever the LUT says** — no hardcoded base | LUT-driven; no `#0x14` in the file |
| `genesistan_hook_tilemap_fg` (FG strip hook) | ibid. | same | same | same |
| `genesistan_hook_tilemap_bg_fill` | ibid. | same | same | same |
| `genesistan_hook_text_writer_*` (all 9 variants) | ibid. | same | same | same |
| `genesistan_hook_number_renderer_3c2e2` | ibid. | same | same | same |
| `genesistan_hook_cwindow_clear` | ibid. | reads LUT at arcade tile `0x0020` (space), writes that value verbatim as the clear-tile nametable entry | LUT-driven | LUT-driven; no hardcoded base |
| `genesistan_hook_number_renderer_3c2e2` suppression-detection | ibid. | reads `LUT[0x0030]` (ASCII '0') to compare against staged nametable entries for leading-zero suppression | LUT-driven | no hardcoded slot |
| opcode_replace entries in `specs/rastan_direct_remap.json` | all 56 entries scanned | redirect arcade hardware writes to Genesis shadows / hooks; none write a VRAM tile index | no VRAM tile assumption | grep for tile-slot literals in `replacement_bytes`: none found |
| VRAM crash font (`crash_handler.s` base `0x8000` = tile 1024) | [apps/rastan-direct/src/crash_handler.s](apps/rastan-direct/src/crash_handler.s) | fault-only; uses tile range `1024..1279` (outside both cache regions) | tile 1024, not low tiles | explicitly documented in [Andy_crash_handler_spec.md](docs/design/Andy_crash_handler_spec.md); crash-only, never invoked during runtime |

### Producer/consumer agreement

- **Producer base (Phase 1):** VRAM tile slot `0x14` (from `TILE_CACHE_BASE_A = 20`).
- **Consumer base:** no hardcoded base anywhere in `tilemap_hooks.s` / `specs/rastan_direct_remap.json` / `vdp_comm.s`; every consumer reads `genesistan_pc080sn_tile_vram_lut` at runtime and emits the value it finds.
- The LUT values **are** generated from the same tool that generates the preload binaries, with both sides using the same `TILE_CACHE_BASE_A` constant — the producer and consumer are byte-identical in their slot-base choice by construction.

```
Producer base (Phase 1 result):          tile index 0x14 (slot 20)
Consumer base assumption(s):             LUT-driven (no hardcoded offset)
Producer and all consumers agree:        YES
Mismatch sites:                          NONE
```

No mismatch. The 0x14 offset is expressed in one place (`TILE_CACHE_BASE_A`) and flows through both the preload binary and the LUT binary.

---

## Phase 3 — Origin analysis

Concrete evidence of SGDK origin — all citations are to files currently present in the tree:

1. **Explicit SGDK reservation table.** [docs/design/direct_pc080sn_bulk_tilemap_validation_gate.md:190](docs/design/direct_pc080sn_bulk_tilemap_validation_gate.md#L190):

    ```
    | 0–15 | 16 | SGDK system (reserved) | No |
    ```

    This is the cleanest single piece of evidence — an in-repo design document explicitly documenting VRAM slots 0-15 as "SGDK system (reserved)."

2. **SGDK reference pipeline section.** [docs/design/Andy_pc080sn_tile_preload_system_design.md](docs/design/Andy_pc080sn_tile_preload_system_design.md) §3 is titled **"SGDK Reference Pipeline"** and documents `genesistan_preload_scene_tiles` in `apps/rastan/src/main.c` as the SGDK-side origin of the preload-manifest design. §3 states: *"Destination: vram_slot (SGDK tile index, not byte address — SGDK API converts internally)"* and *"The SGDK reference uses scene-scoped preload due to VRAM overflow in an earlier prototype."*

3. **SGDK migration proposal.** [docs/design/Cody_no_sgdk_direct_execution_proposal.md](docs/design/Cody_no_sgdk_direct_execution_proposal.md) is the explicit proposal to migrate *away* from SGDK to the `apps/rastan-direct/` branch. Quote (line 121): *"Building this in apps/rastan-direct/ preserves apps/rastan/ while enabling deterministic single-owner VDP publishing and direct arcade boot."*

4. **Parallel SGDK-based application.** `apps/rastan/` exists as the SGDK-based predecessor of `apps/rastan-direct/` (file listings, repo-wide grep confirms).

5. **SGDK address-mapping diagnosis.** [docs/design/Andy_sgdk_vs_rastan_direct_address_mapping_diagnosis.md](docs/design/Andy_sgdk_vs_rastan_direct_address_mapping_diagnosis.md) compares the two address maps and references `entry_symbol_address = 0x0003A208` as a pre-decomposition value that matches SGDK-era layout.

6. **Historical analysis of the `0x14` constant.** [docs/design/pc080sn_semantic_mismatch_analysis_build294.md](docs/design/pc080sn_semantic_mismatch_analysis_build294.md) documents a *separate* `PC080SN_TABLE_TILE_OFFSET = 0x14` constant that was a different (and now-refuted) misinterpretation of arcade-side displacement — but the doc corroborates that the Python generator carries multiple `0x14` constants originating from SGDK-era thinking.

### Numeric fit

SGDK's default VRAM tile-reservation convention (per the widely-used SGDK sources in `tools/sgdk/` and in `apps/rastan/`) reserves a block at the start of tile VRAM for SGDK's own font / system tiles. A 20-tile reserve (exact: 16 SGDK-system slots + 4 guard / convenience slots per the validation-gate table) is consistent with SGDK's default layout.

### Origin verdict

```
Evidence of SGDK origin found:   YES
Evidence citations:
  docs/design/direct_pc080sn_bulk_tilemap_validation_gate.md:190 (explicit table row "0–15 | 16 | SGDK system (reserved)")
  docs/design/Andy_pc080sn_tile_preload_system_design.md §3 "SGDK Reference Pipeline"
  docs/design/Cody_no_sgdk_direct_execution_proposal.md:121
  docs/design/Andy_sgdk_vs_rastan_direct_address_mapping_diagnosis.md
  docs/design/pc080sn_semantic_mismatch_analysis_build294.md (corroborating)
  apps/rastan/ (SGDK-based predecessor exists in-tree)
Origin verdict:                  INHERITED_FROM_SGDK
```

---

## Phase 4 — Requirement analysis

### 4a. Genesis-side consumers of VRAM tile slots 0x00-0x13

Exhaustive scan of `apps/rastan-direct/src/` for references to low tile slots:

- `vdp_comm.s` — no use of tile slots 0..0x13. All VDP reg constants (`#0x04`, `#0x06`, etc.) are register *values*, not slot indices.
- `tilemap_hooks.s` — no hardcoded reference to slots 0..0x13. Every tile index used in nametable writes is LUT-sourced.
- `scene_load.s` — `genesistan_scene_preload_{title,gameplay,endround}.bin` first destinations are all ≥ 0x14 (the preload binary contents begin with `0x0014` and increase from there; verified by `xxd` on the title manifest).
- `boot.s` — `_bootstrap_clear_staging` clears Plane A *nametable* (not tile data VRAM) with `0x0000`. That writes tile index 0 into every Plane A cell, which renders as whatever is at VRAM `0x0000..0x001F` (= tile slot 0). This is the only implicit use of slot 0; it relies on slot 0 being blank.
- `crash_handler.s` — crash font lives at VRAM `0x8000` (tile 1024) per [Andy_crash_handler_spec.md](docs/design/Andy_crash_handler_spec.md). Crash stubs do not touch low tiles during normal runtime (fault-only).
- `sound/` — no VRAM access at all (sound-comm and Z80 driver don't interact with VDP).

```
Genesis-side consumers of low VRAM tiles (slots 0x00-0x13):
  - slot 0x00: IMPLICIT USE as the LUT's "unmapped" sentinel. LUT[unmapped_arcade_tile] = 0
               emits tile 0 as the nametable entry. Plane A clear at boot also writes tile
               index 0 to every cell. Both rely on slot 0 rendering as "blank" (pixels = 0).
  - slots 0x01-0x13: UNUSED. No Genesis-side code writes to or references these.
```

### 4b. Arcade-side references to tile base 0x14

- `specs/rastan_direct_remap.json` — all 56 opcode_replace entries scanned. No entry encodes a VRAM tile index; all references are either WRAM symbols or hook call redirects.
- Arcade ROM does not have visibility into Genesis VRAM slot numbering — it writes arcade tile codes (0..0x3FFF) which the hooks translate via LUT. The arcade cannot observe the `TILE_CACHE_BASE_A` value.

```
Arcade-side references to tile base 0x14:  NONE (arcade does not see VRAM slots)
```

### 4c. VDP hardware constraints on low tile usage

Genesis VDP does not restrict tile slot 0 or any low tile to a reserved role. Tile index 0 in a nametable entry simply points to VRAM bytes `0x0000..0x001F` (first 32 bytes of VRAM tile area). Any slot 0..0x7FF (2048 max) is a valid nametable tile reference. **No VDP constraint exists.**

### Offset-still-required determination

```
Offset still required:  NO

Justification: No Genesis-side consumer in the current rastan-direct tree uses any of
VRAM tile slots 0x01..0x13 (19 slots). Crash handler sits at slot 1024+ and is fault-
only. Slots 0x14..0x3FF are the low tile cache; they are fully sufficient without the
19 extra reserved slots below. The only slot in the 0..0x13 range that has any role is
slot 0, which is implicitly depended on by (a) the LUT's "0 means unmapped" sentinel
convention — the hooks write LUT[0] = 0 verbatim as a nametable entry, so any arcade
tile that falls through unmapped points cells at VRAM slot 0; (b) the boot-time
Plane A clear which writes tile index 0 to every cell. Both uses expect slot 0 to
render as a blank tile. The current build does not explicitly upload a blank tile to
slot 0 — it relies on VDP-reset VRAM being zero, which is the common emulator default
but not a hardware guarantee. So slot 0 should remain reserved by convention, but
slots 1..0x13 can be reclaimed as part of the tile cache.
```

---

## Phase 5 — Fix direction

Since Phase 4 concludes the 20-slot reservation is not required (only slot 0 is), the minimum correct production fix is a **one-constant change** in the generator.

### Recommended change set

```
Producer: tools/translation/precompute_pc080sn_tile_lut.py
  Line 39:
    Before:  TILE_CACHE_BASE_A = 20
    After:   TILE_CACHE_BASE_A = 1
  Line 40 stays unchanged (`TILE_CACHE_SIZE_A = 1004`) — cache A moves from slots 20..1023
    to slots 1..1004. If the build wants to reclaim the full 19 slots additionally, the
    size can be raised to 1023 (cache A: slots 1..1023). Either variant is safe; the
    minimum-scope recommendation is slot-shift only, leaving size at 1004.

  Optional cleanup (recommended, not strictly necessary):
    Line 44:
      Before:  PC080SN_TABLE_TILE_OFFSET = 0x14
      After:   (remove line)
    This constant is defined but not referenced anywhere else in the file (verified via
    grep on the tool). It is dead code — a stale leftover from the refuted Build-294
    arcade-displacement hypothesis. Removing it is documentation-cleanup scope.

Consumer(s): NONE — no source edit required.
  The LUT binary (build/pc080sn_tile_vram_lut.bin) and the three scene preload binaries
  (build/pc080sn_scene_preload_{title,gameplay,endround}.bin) are all re-emitted by the
  same tool run. scene_load.s and tilemap_hooks.s consume them at runtime without any
  hardcoded base constant, so the source is unaffected.

Total source lines affected:        1 (value change), or 2 if the dead constant is also removed.
Simultaneous change required:       NO — the single-line change propagates atomically through
                                    the build because the tool regenerates both binaries in the
                                    same invocation.
```

### Risk assessment

Primary risk: setting `TILE_CACHE_BASE_A = 0` (instead of `1`) would allocate a real arcade tile into VRAM slot 0, colliding with the LUT's "0 means unmapped" sentinel convention. Any arcade tile whose LUT entry is `0` (intentional sentinel or unassigned tile) would render as the *actual* tile stored in slot 0 — typically whatever the first tile alphabetically/ordered was — instead of blank. This would be a visible, cascading rendering regression across every cell pointing at an unmapped tile. **Stop at `TILE_CACHE_BASE_A = 1`.** Slot 0 remains implicitly reserved as the blank tile by convention; the change recovers only slots 1..0x13 (19 tile slots, ≈ 608 bytes of VRAM).

Secondary risk: a downstream tool or doc not inspected here might encode the old `20` value by coincidence. A post-change sanity check should grep for the literal `20` in tile contexts across `tools/` and `docs/design/` before the change is finalised. Global Rule 8 is satisfied for the analysis (SGDK origin is proven with concrete citations); the downstream-grep step belongs to Cody's implementation pass, not this analysis.

Tertiary risk: the current VRAM-reset convention (emulators typically zero VRAM at reset) means slot 0 *happens* to render as blank without any explicit tile upload. If a future emulator leaves VRAM with garbage after reset, cells pointing at slot 0 would render garbage. This is a pre-existing bug in the current build (not introduced by the proposed fix). A separate follow-up prompt could specify an explicit "write a blank tile to slot 0 as part of `_bootstrap_clear_staging`" — out of scope here.

### Confidence

```
Confidence: HIGH.

Justification: Producer and consumer agreement is proven mechanically by the
fact that both binaries are emitted by the same Python run from one constant.
The constant's value is hardcoded in one file on one line. SGDK origin is
proven by at least one in-repo document (direct_pc080sn_bulk_tilemap_
validation_gate.md:190) that explicitly tags the reserved range as "SGDK
system (reserved)." No current Genesis-side consumer uses the reserved
slots (verified by reading all assembler files in apps/rastan-direct/src/
and grepping for low-slot literals). The only dependency on a specific slot
in the 0..0x13 range is the LUT-zero sentinel's implicit reliance on slot 0
rendering as blank — a dependency preserved by stopping the fix at base=1.
The fix is a single-line constant edit in a generator tool; the generator
re-emits both producer and consumer artefacts in lockstep, eliminating the
producer/consumer-drift risk that a split fix would carry.
```

---

## Summary

- Producer VRAM destination: VRAM_OFFSET `0x00000280` = tile index `0x14` (20 decimal).
- Consumer tile base: LUT-driven at runtime; no hardcoded base exists in any consumer file.
- Producer/consumer agreement: **YES**. Mismatch sites: **NONE**.
- SGDK origin evidence: **YES** — multiple concrete citations in `docs/design/`.
- Origin verdict: **INHERITED_FROM_SGDK**.
- Offset still required: **NO** (slot 0 usage is a convention-level dependency, not a reservation requirement).
- Recommended fix scope: one constant in `tools/translation/precompute_pc080sn_tile_lut.py:39` (`TILE_CACHE_BASE_A`: `20` → `1`). No source file edits in `apps/rastan-direct/src/` required.
- Fix confidence: **HIGH**.
- STOP triggered: **NO**.
