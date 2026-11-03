# Andy — SGDK Slot Reservation Removal Classification

**Agent:** Andy (Claude Code)
**Type:** Design classification (analytical only — no implementation, no new evidence collection)
**Build:** rastan-direct, post-Build-58c (canonical ROM `dist/rastan-direct/rastan_direct_video_test_build_0057.bin`)
**Date:** 2026-05-07
**Naming:** descriptive output filename (no build number) per OPEN-002 extended policy
**Scope:** classify whether the slot 0..19 tile reservation should be removed; specify the lockstep fix shape; identify risks; produce a bounded Cody implementation outline.

---

## 0. Executive verdict

**§1.1 classification: NO** — the slot 0..19 reservation is unjustified by any live direct-rastan code path. The reservation is purely an SGDK-era convention preserved in the precompute tool (`TILE_CACHE_BASE_A = 20` in [`tools/translation/precompute_pc080sn_tile_lut.py:39`](tools/translation/precompute_pc080sn_tile_lut.py#L39)). No SGDK runtime, no font/debug tiles, no system tiles, and no live VRAM writer touches slots 0..19 in direct-rastan.

**§1.2 fix shape: lockstep regeneration via single tool change.** Set `TILE_CACHE_BASE_A = 0` in the precompute tool. The tool atomically regenerates the LUT (`pc080sn_tile_vram_lut.bin`) and all three scene preload manifests (`pc080sn_scene_preload_{title,gameplay,endround}.bin`) in a single invocation — lockstep is automatic because a single producer emits both sides. All slot assignments shift down by 20 (tile `0x20` previously slot `0x14` now slot `0x00`; tile `0x23` previously slot `0x15` now slot `0x01`; etc.). `scene_load.s`, `tilemap_hooks.s`, `pc080sn_attr_lut.bin`, and `specs/rastan_direct_remap.json` are UNCHANGED.

**Two residual risks documented in §1.4** — neither blocks the fix, but Cody must address each at implementation time:
- **R1 — LUT-unmapped sentinel collision:** the script header convention `lut[arcade_tile] = 0 means unmapped` ([`precompute_pc080sn_tile_lut.py:6`](tools/translation/precompute_pc080sn_tile_lut.py#L6)) overlaps with the new "real tile at slot 0" assignment. Unmapped tile references would render as the slot-0 tile instead of falling back to blank.
- **R2 — `vdp_commit_tiles_if_dirty` dormant scaffolding:** [`vdp_comm.s:183-198`](apps/rastan-direct/src/vdp_comm.s#L183-L198) declares `VRAM_TILE_BASE = 0x20` (slot 1) and a 48-word commit path gated on `tiles_dirty`, but `tiles_dirty` is never set to 1 anywhere in the project (verified by source grep). Path is dead scaffolding (Rule 14 candidate for removal). If activated in future, it would corrupt scene tile slot 1.

**§1.5 OPEN-004 dependency: independent.** Pattern Viewer verification does not require active gameplay; bootstrap re-entry does not block the visual gate. Full in-game rendering verification remains blocked by OPEN-004 but is not required for this fix's verification.

**§1.7 next ROM-producing build number:** the Makefile auto-increments `build/rastan-direct/build_counter.txt` per [`apps/rastan-direct/Makefile:124-131`](apps/rastan-direct/Makefile#L124-L131). Cody reads the printed `numbered build artifact: ...` line to confirm the actual sequential number; per OPEN-002 extended policy, no letter suffix anywhere.

**Locked elements unchanged:** Build 55a palette helpers (`_59ad4`, `_03ab00`, `_45dae`); Build 55b active-writer hook (`genesistan_palette_hook_3ba64`); v3.1/v3.2 PC090OJ closures; D6-fix patches; opcode_replace at `0x03AF04`; `_bootstrap` and `_vblank_service` closures; conversion path; `bank & 0x03` SKIP-≥4 mapping.

---

## §1.1 Reservation justification analysis

### The single source of the reservation

The 20-slot reservation comes from one constant:

```python
# tools/translation/precompute_pc080sn_tile_lut.py:39-42
TILE_CACHE_BASE_A = 20
TILE_CACHE_SIZE_A = 1004
TILE_CACHE_BASE_B = 1280
TILE_CACHE_SIZE_B = 160
```

The slot allocator [`build_slot_sequence`](tools/translation/precompute_pc080sn_tile_lut.py#L347-L351) emits:
- Range A: slots `20..1023` (1004 slots, starts at `20 = 0x14`)
- Range B: slots `1280..1439` (160 slots)

A separate constant `PC080SN_TABLE_TILE_OFFSET = 0x14` ([`precompute_pc080sn_tile_lut.py:44`](tools/translation/precompute_pc080sn_tile_lut.py#L44)) is **vestigial** — defined but never referenced in the script body (verified by grep `PC080SN_TABLE_TILE_OFFSET` in the file).

`TILE_CACHE_BASE_A` and `TILE_CACHE_BASE_B` are referenced ONLY in this one tool (verified by grep across `tools/` and `apps/`). The other hit (`apps/rastan/inc/main.h`) is in the SGDK-based `apps/rastan/` tree, NOT direct-rastan.

### Direct-rastan dependency search

Searched `apps/rastan-direct/src/` for any code consuming slots 0..19:

| Suspected consumer | Finding | Status |
|---|---|---|
| SGDK runtime | None — direct-rastan does not link SGDK; grep for `SGDK\|sgdk\|FONT_BASE\|SYSTEM_TILE\|debug_tile` returned no source matches in `apps/rastan-direct/src/` | NOT PRESENT |
| Font/debug overlay tiles | None — no font, debug overlay, or system tile path in direct-rastan | NOT PRESENT |
| `crash_init_cram` | [`crash_handler.s:285-289`](apps/rastan-direct/src/crash_handler.s#L285-L289) writes only CRAM (palette), not VRAM tile data | NO COLLISION |
| `vdp_commit_tiles_if_dirty` | [`vdp_comm.s:183-198`](apps/rastan-direct/src/vdp_comm.s#L183-L198) writes `staged_tile_words` (48 words = 3 tiles) to `VRAM_TILE_BASE = 0x20` (slot 1) **only if `tiles_dirty == 1`**; `tiles_dirty` writers are: `boot.s:176` (clears to 0), `vdp_comm.s:196` (clears to 0); reader: `crash_handler.s:251`. **NO source ever sets it to 1.** Path is dormant scaffolding. | DORMANT (R2) |
| `crash_init_cram` blank tile | None — no init writes to VRAM tile slots in current direct-rastan source | NOT PRESENT |
| LUT consumer post-offset | Verified by Cody §5.1 of [`Cody_build58_offset_graphics_evidence.md`](docs/design/Cody_build58_offset_graphics_evidence.md): `tilemap_hooks.s` uses LUT lookup directly with no constant offset added; verified independently by inspection of [`tilemap_hooks.s:115-116, 287-288, 402-403, 1056-1057`](apps/rastan-direct/src/tilemap_hooks.s) — `lea genesistan_pc080sn_tile_vram_lut, %a2/%a3` followed by mask-and-load. | NO POST-OFFSET |
| `.L3c950_store_blank_tile_preserve_attr` | [`tilemap_hooks.s:828-868`](apps/rastan-direct/src/tilemap_hooks.s#L828-L868) writes tile id `0x0180` via the attribute LUT for sentinel cells; references the *attribute* LUT (`%a3`), not the slot LUT, and uses arcade tile id `0x0180` (not slot id). After reservation removal, tile `0x0180` continues to translate via the regenerated slot LUT to whatever new slot it gets assigned. | NO COLLISION |

### Cody Build 58 evidence corroboration

Per [`Cody_build58_offset_graphics_evidence.md`](docs/design/Cody_build58_offset_graphics_evidence.md):
- §3.3: "Direct-rastan therefore diverges from the full old audit statement (partially matches: reservation start yes; **slot0 blank no**)"
- §3.4: "Sampled values in this range are not all zero in the available capture"

This indicates that even slot 0's "blank" status was not strongly preserved at the captured timestamp. The reservation as a "blank cell fallback" was implicit (slots 0..19 happen to be unwritten because the allocator skips them) rather than explicitly designed as blank tile data.

### Classification

**§1.1 result: NO — reservation is unjustified by any live direct-rastan code path.**

The 20-slot reservation is SGDK-era convention preserved in the precompute tool's slot allocator constants. The only currently-defined direct-rastan path that references low slots is `vdp_commit_tiles_if_dirty`, which is dormant scaffolding (never activated). No font, debug, system tile, or other consumer requires the reservation.

---

## §1.2 Fix shape (lockstep design)

### Single-point change in the precompute tool

The reservation comes from one constant in one file. Changing it produces the lockstep regeneration of LUT + all three preload manifests because the tool emits all four artifacts from the same allocator state in a single invocation:

| Action | Location | Change |
|---|---|---|
| Set base | [`tools/translation/precompute_pc080sn_tile_lut.py:39`](tools/translation/precompute_pc080sn_tile_lut.py#L39) | `TILE_CACHE_BASE_A = 20` → `TILE_CACHE_BASE_A = 0` |
| (Optional) Tile size | [`tools/translation/precompute_pc080sn_tile_lut.py:40`](tools/translation/precompute_pc080sn_tile_lut.py#L40) | `TILE_CACHE_SIZE_A = 1004` may be increased to `1024` to reclaim freed slot budget; not required for fix correctness; Cody decides at implementation per current scene-tile usage observed in `pc080sn_unique_tile_count.txt` |
| (Optional) Vestigial cleanup | [`tools/translation/precompute_pc080sn_tile_lut.py:44`](tools/translation/precompute_pc080sn_tile_lut.py#L44) | `PC080SN_TABLE_TILE_OFFSET = 0x14` is unreferenced in the script body and may be removed for cleanliness; not required for fix correctness |

### Atomic regeneration step

Re-run the precompute tool from the project root:

```
python3 tools/translation/precompute_pc080sn_tile_lut.py
```

This atomically regenerates (per the tool's `--*-output` defaults, [`precompute_pc080sn_tile_lut.py:483-526`](tools/translation/precompute_pc080sn_tile_lut.py#L483-L526)):

- `build/pc080sn_tile_vram_lut.bin` (LUT — slots shifted down by 20)
- `build/pc080sn_scene_preload_title.bin`
- `build/pc080sn_scene_preload_gameplay.bin`
- `build/pc080sn_scene_preload_endround.bin`
- `build/pc080sn_vram_preload.bin` (legacy compatibility — title manifest mirror)
- `build/pc080sn_tile_vram_lut_words.inc`
- `build/pc080sn_vram_preload_words.inc`
- `build/pc080sn_unique_tile_count.txt`
- `build/pc080sn_source_scene_map.bin` (independent of slot mapping)

Lockstep is automatic — no opportunity for partial regeneration because one tool invocation produces all artifacts from the same allocator state.

### Source files unchanged

| File | Change | Reason |
|---|---|---|
| [`apps/rastan-direct/src/scene_load.s`](apps/rastan-direct/src/scene_load.s) | NONE | `slot << 5` formula at line 67 is generic; `.incbin` at lines 100-124 includes the regenerated artifacts directly |
| [`apps/rastan-direct/src/tilemap_hooks.s`](apps/rastan-direct/src/tilemap_hooks.s) | NONE | LUT lookup is direct (no post-offset), per Cody §5.1; LUT contents change but lookup mechanism does not |
| [`build/pc080sn_attr_lut.bin`](build/pc080sn_attr_lut.bin) | NONE | Attribute LUT is independent of slot mapping (encodes attribute bits like priority/flip/palette, not slot id) |
| [`specs/rastan_direct_remap.json`](specs/rastan_direct_remap.json) | NONE | `opcode_replace` entries are independent of tile slot mapping |
| Build 55a/55b helpers (`palette_hooks.s`) | NONE | Independent of tile slot path |
| PC090OJ helpers (`pc090oj_hooks.s`, `pc090oj_assets.s`) | NONE | Sprite path; independent of tile slot mapping |

### Build outputs that change

The Makefile build pipeline ([`apps/rastan-direct/Makefile:91-92, 109-143`](apps/rastan-direct/Makefile#L91-L143)) produces a new `dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin` where `NNNN` is the next sequential counter (auto-incremented from `build/rastan-direct/build_counter.txt`). Per OPEN-002 extended policy, no letter suffix.

The postpatched disasm at `build/genesis_postpatch.disasm.txt` is regenerated.

---

## §1.3 Affected files / artifacts (full enumeration)

| Path | Type | Action | Reason |
|---|---|---|---|
| [`tools/translation/precompute_pc080sn_tile_lut.py`](tools/translation/precompute_pc080sn_tile_lut.py) | Tool | EDIT (single-line `TILE_CACHE_BASE_A = 0`) | The single point of reservation control |
| [`build/pc080sn_tile_vram_lut.bin`](build/pc080sn_tile_vram_lut.bin) | Generated artifact | REGENERATE via tool | LUT entries shift down by 20 |
| [`build/pc080sn_scene_preload_title.bin`](build/pc080sn_scene_preload_title.bin) | Generated artifact | REGENERATE via tool | Slot assignments shift |
| [`build/pc080sn_scene_preload_gameplay.bin`](build/pc080sn_scene_preload_gameplay.bin) | Generated artifact | REGENERATE via tool | Slot assignments shift |
| [`build/pc080sn_scene_preload_endround.bin`](build/pc080sn_scene_preload_endround.bin) | Generated artifact | REGENERATE via tool | Slot assignments shift |
| [`build/pc080sn_vram_preload.bin`](build/pc080sn_vram_preload.bin) | Generated artifact | REGENERATE via tool (legacy mirror of title) | Auto via tool |
| [`build/pc080sn_tile_vram_lut_words.inc`](build/pc080sn_tile_vram_lut_words.inc) | Generated artifact | REGENERATE via tool | C-include mirror of LUT |
| [`build/pc080sn_vram_preload_words.inc`](build/pc080sn_vram_preload_words.inc) | Generated artifact | REGENERATE via tool | C-include mirror of preload |
| [`build/pc080sn_unique_tile_count.txt`](build/pc080sn_unique_tile_count.txt) | Generated artifact | REGENERATE via tool | Auto via tool |
| [`build/pc080sn_source_scene_map.bin`](build/pc080sn_source_scene_map.bin) | Generated artifact | REGENERATE via tool (no content change since map is by source addr) | Auto via tool |
| [`build/pc080sn_attr_lut.bin`](build/pc080sn_attr_lut.bin) | Existing artifact | UNCHANGED | Attribute LUT is independent of slot mapping |
| [`apps/rastan-direct/src/scene_load.s`](apps/rastan-direct/src/scene_load.s) | Source | UNCHANGED | `slot << 5` is generic; `.incbin` references regenerated artifacts |
| [`apps/rastan-direct/src/tilemap_hooks.s`](apps/rastan-direct/src/tilemap_hooks.s) | Source | UNCHANGED | LUT lookup is direct (no post-offset) per Cody §5.1 |
| [`specs/rastan_direct_remap.json`](specs/rastan_direct_remap.json) | Spec | UNCHANGED | `opcode_replace` is independent of tile slot path |
| [`apps/rastan-direct/Makefile`](apps/rastan-direct/Makefile) | Build script | UNCHANGED | Auto-increments build counter |
| Documentation (`docs/design/`) | Docs | UPDATE OPEN-009 + AGENTS_LOG entry | Per OPEN-009 closure flow |

---

## §1.4 Risks

### R1 — LUT-unmapped sentinel collision (residual cosmetic risk; not a structural break)

**Description:** The precompute script's header documents `lut[arcade_tile] -> Genesis VRAM slot (0 means unmapped)` ([`precompute_pc080sn_tile_lut.py:6`](tools/translation/precompute_pc080sn_tile_lut.py#L6)). The slot allocator excludes arcade tile id 0 from assignment ([`precompute_pc080sn_tile_lut.py:362`](tools/translation/precompute_pc080sn_tile_lut.py#L362) — `if tile != 0`), so `lut[0] = 0` is the default unmapped state for tile id 0 and any other tile that didn't get a slot.

After regeneration with `TILE_CACHE_BASE_A = 0`:
- Some real arcade tile X gets `lut[X] = 0` (slot 0 contains real tile X's pixels)
- Unmapped tiles (including arcade tile id 0) still have `lut[unmapped] = 0`
- Both real tile X references and unmapped tile references render to slot 0
- Visual effect: nametable cells with arcade tile id 0 (or any unmapped id) display real tile X content instead of "whatever's in slot 0 which is currently zero/blank"

**Severity:** COSMETIC residual. Arcade gameplay uses MAPPED tiles in production frames; unmapped references typically appear only in edge cases (out-of-range tile ids, debug states). The "fallback to slot 0 = blank" was implicit (slot 0 happened to be unwritten) rather than explicitly designed.

**Mitigation options (Cody implementation choice):**
- (a) Accept residual: arcade gameplay should reference only mapped tiles; document the change in OPEN-009 and verify no production frame uses tile id 0.
- (b) Defensive: set `TILE_CACHE_BASE_A = 1` instead of `0`; preserve slot 0 as the "blank fallback" tile (1-slot reservation; Pattern Viewer shows tile data starting at slot 1 = VRAM 0x20). This is a strict subset of "remove the 20-slot reservation" and still resolves OPEN-009's main concern (no large blank block in Pattern Viewer).
- (c) Aggressive: change unmapped sentinel from `0` to `0xFFFF` and update tilemap_hooks.s LUT consumer to skip writes when LUT returns `0xFFFF`. This expands the lockstep to include `tilemap_hooks.s` source changes. Not recommended for this initial fix.

**Recommendation:** Andy recommends Cody picks (a) for the implementation gate (full removal per OPEN-009 closure expectation), with (b) available as a fallback if Cody discovers production frames using tile id 0 during verification.

### R2 — `vdp_commit_tiles_if_dirty` dormant scaffolding (separate concern; no current collision)

**Description:** [`apps/rastan-direct/src/vdp_comm.s:52, 183-198`](apps/rastan-direct/src/vdp_comm.s#L52) declares:
```
.equ VRAM_TILE_BASE,        0x00000020         ; line 52 (slot 1)
vdp_commit_tiles_if_dirty:
    tst.b   tiles_dirty
    beq.s   .Ltiles_done
    move.l  #VRAM_TILE_BASE, %d0
    bsr     vdp_set_vram_write_addr
    lea     staged_tile_words, %a0
    move.w  #(48 - 1), %d7                     ; 48 words = 3 tiles = slots 1..3
.Ltile_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Ltile_copy
    clr.b   tiles_dirty
.Ltiles_done:
    rts
```

Source grep confirms `tiles_dirty` is only written to clear (`clr.b tiles_dirty` at boot.s:176 and vdp_comm.s:196). NO source sets it to 1. The path is dead.

After reservation removal, slot 1 contains scene tile data. If `vdp_commit_tiles_if_dirty` is activated in the future (without other changes), it would corrupt scene tile slot 1's pixels (and slots 2, 3).

**Severity:** ZERO impact on Build 55b → next-build behavior because the path is dormant. The risk is forward-looking: a future task that sets `tiles_dirty := 1` would silently corrupt scene tile slots 1..3.

**Mitigation:** This is RULES.md Rule 14 / Rule 5 territory ("no scaffolding"; "If a bug exists, fix the real system. Do not introduce temporary code paths"). The dormant `vdp_commit_tiles_if_dirty` should be classified as scaffolding-to-remove OR repurposed-with-relocated-base in a SEPARATE follow-up task. This is NOT in the lockstep scope for the slot reservation removal.

**Recommendation:** Cody implementation does NOT touch `vdp_commit_tiles_if_dirty` in this build. After the slot reservation removal lands, a follow-up task classifies the path as scaffolding-to-delete or infrastructure-to-relocate. Open as a new tracked issue if needed.

### R3 — Lockstep coherence

Automatic. Single tool invocation regenerates LUT + 3 preload manifests + ancillary outputs. Verification: all artifacts have matching mtimes from the same `python3 precompute_pc080sn_tile_lut.py` invocation.

### R4 — OPEN-004 compatibility

Independent of bootstrap re-entry. Pattern Viewer verification uses the VDP Pattern Viewer (visual inspection of tile data placement at slot 0+), not active gameplay. Bootstrap re-entry does not affect Pattern Viewer state because the loader writes scene tiles during bootstrap (the 11760 writes / 64s observed in [`Cody_build55b_video_30fps_debug_windows.md`](docs/design/Cody_build55b_video_30fps_debug_windows.md) come from the bootstrap-driven palette path; tile data preload also runs during bootstrap via [`load_scene_tiles`](apps/rastan-direct/src/scene_load.s)).

**Verification scope for this fix:** Pattern Viewer verification only. Full in-game render verification remains BLOCKED by OPEN-004 and is not a gate for this fix.

### R5 — `tilemap_hooks.s` post-LUT offset

Verified NONE. Per Cody §5.1: tilemap_hooks.s uses LUT lookup directly with no constant offset added. Independently confirmed by grep over [`tilemap_hooks.s`](apps/rastan-direct/src/tilemap_hooks.s) for `0x14` constants — no post-LUT offset found. After regeneration, hooks continue to work unchanged because the LUT itself contains the new slot values.

### R6 — Postpatcher invariant

The LUT and preload manifest sizes are unchanged (LUT is fixed `16384 * 2` bytes; preload manifests are tile-count + sentinel terminator words; tile counts don't change). However, the postpatcher byte count covers the entire ROM and may shift if any embedded `.incbin` boundary changes — Cody must measure the actual byte count after the build per Build 54 D6-fix discipline (measure-not-presume) and update [`tools/translation/postpatch_startup_rom.py`](tools/translation/postpatch_startup_rom.py) to the measured value.

### R7 — Build numbering

Per [`apps/rastan-direct/Makefile:124-131`](apps/rastan-direct/Makefile#L124-L131), the Makefile auto-increments `build/rastan-direct/build_counter.txt` and produces `dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin`. The next number after canonical `0057.bin` is whatever the counter increments to. Cody verifies by reading the printed `numbered build artifact: ...` line. Per OPEN-002 extended policy: no letter suffix anywhere in the produced filename, task header, dump directory, or trace folder.

---

## §1.5 OPEN-004 dependency assessment

| Question | Answer | Reasoning |
|---|---|---|
| Pattern Viewer slot-placement fix proceeds NOW (before OPEN-004 resolves)? | YES | Tile preload runs during bootstrap; Pattern Viewer shows VRAM tile data state regardless of gameplay progression; bootstrap re-entry does not block tile data being written by `load_scene_tiles` |
| Full in-game rendering verification blocked by OPEN-004? | YES | Active gameplay required to verify tilemap rendering; bootstrap loop blocks gameplay; full verification deferred until OPEN-004 resolves |
| Verification scope achievable for this fix | Pattern Viewer slot 0 placement + LUT example checks (5 tile id → slot pairs) + locked Build 55a/55b helpers intact | Visual inspection sufficient for OPEN-009 closure |

---

## §1.6 Verification gates for the eventual Cody implementation

1. **Postpatcher passes** with measured byte count (not presumed; per Build 54 D6-fix discipline). If byte count shifts from the prior `0057.bin` baseline, capture the measured value and update `postpatch_startup_rom.py` invariant.
2. **D00778 verification passes** (existing test, unchanged).
3. **VRAM roundtrip self-test** continues to pass (`pc090oj_dma_self_test` already runs at boot per [`boot.s:165`](apps/rastan-direct/src/boot/boot.s#L165); should be unaffected by tile slot changes).
4. **Pattern Viewer in Exodus** shows tile data starting at slot `0` (VRAM `0x0000`) instead of slot `0x14` (VRAM `0x0280`).
5. **Five LUT examples verified post-regeneration:**
   - tile `0x20 → 0x00` (was `0x14`)
   - tile `0x23 → 0x01` (was `0x15`)
   - tile `0x01 → 0x3E` (was `0x52`) — exact value depends on allocator order; Cody captures the actual values from the regenerated LUT
   - At least 2 additional tile id → slot pairs cross-checked between LUT and preload manifests for internal consistency
6. **Build 55a palette helpers remain intact:** `genesistan_palette_hook_59ad4`, `genesistan_palette_hook_03ab00`, `genesistan_palette_hook_45dae` symbols present in `apps/rastan-direct/out/symbol.txt`; opcode_replace entries at `0x059AD4`, `0x03AB00`, `0x045DB8` unchanged in spec.
7. **Active palette writer hook intact:** `genesistan_palette_hook_3ba64` symbol present; opcode_replace at `arcade_pc 0x03BA64` unchanged.

---

## §1.7 Bounded Cody next task

**Per §1.1 = NO:** produce a Cody implementation prompt outline.

### Task framing (per OPEN-002 extended naming policy)

- **Task name (descriptive — no build number):** "Cody — SGDK Slot Reservation Removal Implementation"
- **ROM produced:** YES — next sequential after canonical `0057.bin`. Cody confirms exact number from the Makefile's `numbered build artifact: ...` print line.
- **Design doc filename:** `docs/design/Cody_slot_reservation_removal_implementation.md` (descriptive, no build number per OPEN-002)
- **Trace folder:** auto-named by Makefile per the trace timestamp; will use sequential build number per Makefile convention
- **NO letter suffix** anywhere

### Phase A precheck (read-only)

1. Confirm `TILE_CACHE_BASE_A = 20` in [`tools/translation/precompute_pc080sn_tile_lut.py:39`](tools/translation/precompute_pc080sn_tile_lut.py#L39) — the single change point.
2. Confirm `tiles_dirty` is never set to 1 anywhere (re-grep `apps/rastan-direct/src/`); if it IS set somewhere, STOP and re-classify R2.
3. Confirm `tilemap_hooks.s` uses no post-LUT constant offset (re-verify Cody §5.1 finding); if a `0x14` post-offset is discovered, STOP and re-classify the lockstep.
4. Capture pre-regeneration LUT examples for diff comparison: tile `0x20 → ?`, tile `0x23 → ?`, tile `0x01 → ?`.

### Phase B implementation

1. Edit [`tools/translation/precompute_pc080sn_tile_lut.py:39`](tools/translation/precompute_pc080sn_tile_lut.py#L39): `TILE_CACHE_BASE_A = 20` → `TILE_CACHE_BASE_A = 0`.
2. (Optional) Increase `TILE_CACHE_SIZE_A` from `1004` to `1024` to reclaim freed slot budget. NOT required for the fix; only if Cody observes scene-tile-budget pressure.
3. (Optional cleanup) Remove vestigial `PC080SN_TABLE_TILE_OFFSET = 0x14` at [`precompute_pc080sn_tile_lut.py:44`](tools/translation/precompute_pc080sn_tile_lut.py#L44). NOT required for the fix.
4. Run `python3 tools/translation/precompute_pc080sn_tile_lut.py` from project root. Verify output:
   - `Title range`, `Gameplay range`, `End-Round range` lines printed
   - `Range overlap check: PASS (disjoint)` printed
   - All output artifacts (LUT, 3 preloads, source-scene map, count) regenerated with new mtimes
5. Build the ROM via `make -C apps/rastan-direct` (or the project's standard build invocation). Capture the printed `numbered build artifact: ...` line for the new sequential ROM filename.
6. Postpatcher byte count: capture FIRST-RUN failure delta (if any), update `postpatch_startup_rom.py` invariant to measured value, re-run.
7. Commit: NO (per project discipline; user authorizes commits explicitly).

### Phase C verification

Run gates 1-7 from §1.6.

### Phase D documentation

1. Append AGENTS_LOG entry per project template.
2. Update OPEN-009 with implementation evidence (do NOT close yet — closure requires Tighe visual confirmation in Pattern Viewer).
3. Update OPEN-002 evidence with this consecutive-clean-build instance (one of three required for OPEN-002 closure).
4. R2 (`vdp_commit_tiles_if_dirty` dormant scaffolding) — do NOT address in this build; Cody may flag for a separate scaffolding-removal task.

---

## Phase 2 Integrity

- §1.1 reservation justified: NO (with cited evidence per dependency search table)
- §1.2 fix shape specified: lockstep regeneration via single `TILE_CACHE_BASE_A = 0` change in precompute tool; LUT and 3 preload manifests regenerated atomically by single tool invocation
- §1.3 all affected files/artifacts enumerated: YES (16 entries in table; 1 EDIT, 9 REGENERATE, 6 UNCHANGED)
- §1.4 risks identified: 7 risks (R1 LUT-sentinel cosmetic; R2 vdp_commit_tiles_if_dirty dormant scaffolding; R3 lockstep coherence; R4 OPEN-004 compatibility; R5 hook offset confirmed absent; R6 postpatcher measure-not-presume; R7 build numbering per Makefile counter and OPEN-002 extended policy)
- §1.5 OPEN-004 dependency assessed: Pattern Viewer fix independent; full in-game render verification blocked but not required for this fix's gate
- §1.6 verification gates defined: 7 gates
- §1.7 bounded Cody implementation plan produced: COMPLETE (descriptive task name; ROM number deferred to Makefile auto-increment; no letter suffix anywhere)
- All claims cite specific evidence: YES (file:line citations for every constant, every consumer search, every Cody report reference)
- No source/spec/tool/ROM/build modifications by Andy: YES (this is classification only)
- No lockstep violations recommended: YES (preload + LUT change atomically via single tool invocation)
- No closures: YES (OPEN-009 stays open until Cody implementation + Tighe visual verification)
- No letter-suffix naming used: YES (output doc name `Andy_slot_reservation_removal_classification.md`; recommended Cody task name `Cody — SGDK Slot Reservation Removal Implementation`)
- All STOP conditions either passed or documented: YES (no STOP triggered)
