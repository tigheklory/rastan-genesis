# Cody Build 58 Offset Graphics / Tile Base Evidence

## Scope and Method
- Task type: evidence-only (no implementation)
- Canonical ROM for this report: `dist/rastan-direct/rastan_direct_video_test_build_0057.bin`
- Sources used first: existing screenshots/crops, existing traces, disassembly, source, manifests/LUT artifacts
- Read-only dump fallback (§0): NOT RUN (current captures did not expose Plane A/B nametable ranges; required next capture is listed in §7/F)

## §1 ROM Identity (OPEN-002 gate)

### §1.1 SHA256 and file identity
- `0057.bin` SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`
- `0055b.bin` SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`
- Byte-identical: YES
- File sizes: both `1559272` bytes
- mtimes:
  - `0057.bin`: `2026-05-05 11:30:53 -0400`
  - `0055b.bin`: `2026-05-05 11:31:04 -0400`

Evidence: shell outputs captured from `sha256sum` and `stat` on both files.

### §1.2 Canonical ROM
- Canonical sequential ROM: `dist/rastan-direct/rastan_direct_video_test_build_0057.bin`
- Alias ROM: `dist/rastan-direct/rastan_direct_video_test_build_0055b.bin`
- All sections below refer to canonical `0057.bin`.

## §2 VDP Plane Base Configuration (Hypothesis D)

### §2.1 Register write source in project code
`apps/rastan-direct/src/vdp_comm.s` writes these values in `vdp_boot_setup`:
- reg2 (Plane A): `0x38` (`vdp_comm.s:71-73`)
- reg3 (Window): `0x3C` (`vdp_comm.s:75-77`)
- reg4 (Plane B): `0x06` (`vdp_comm.s:79-81`)
- reg5 (SAT): `0x7C` (`vdp_comm.s:83-85`)

The observed effective bases from video debug panes are:
- Layer A `0xE000`
- Layer B `0xC000`
- Window `0xF000`
- Sprites `0xF800`

Evidence: `docs/design/Cody_build55b_video_30fps_debug_windows.md` (Plane Viewer section).

### §2.1.a Decode basis used
Decode basis used is local project documentation in:
- `docs/design/build318_vdp_plane_base_nametable_correlation.md:7-14`

Applied to current values:
- reg2 `0x38` -> Plane A `0xE000` (matches)
- reg3 `0x3C` -> Window `0xF000` (matches)
- reg4 `0x06` -> Plane B `0xC000` (matches)
- reg5 `0x7C` -> SAT `0xF800` (matches)

### §2.1.c Trace corroboration of control-port register writes
In `states/traces/build55b_active_writer_trace_20260505_113900/debug.log`:
- line 28: `pre=8238`
- line 30: `pre=833C`
- line 32: `pre=8406`
- line 34: `pre=857C`

These are the same register writes emitted by `vdp_set_reg` at runtime (`pc=0x7008E`).

### §2.2 Hypothesis D result
- Hypothesis D (wrong plane/table base configuration): REFUTED
- Reason: code writes, runtime trace writes, and viewer-observed effective addresses are consistent.

## §3 VRAM Tile Data Load / Slot Reservation (Hypothesis A)

### §3.1 Visible VRAM evidence from screenshots
From `states/screenshots/build_55b_debug_crops2/sec_00020_center_probe_2x.png` and `sec_00050.png`:
- VRAM Memory Editor view is in low VRAM range (`0x000..` visible), not nametable ranges
- Nontrivial pattern data is visible in low VRAM (e.g., around `0x29A`, `0x2AA`, `0x2C0`)
- At `0x000` row, values include mixed `0000` and `FFFF` (not all-zero)

### §3.2 Load mechanism and base from source + trace
Load path in `apps/rastan-direct/src/scene_load.s`:
- Scene preload pair loop reads `(tile_id, vram_slot)` pairs (`scene_load.s:53-58`)
- VRAM destination address = `slot << 5` (`scene_load.s:65-68`)
- 16 word writes per tile are CPU writes (`move.w (%a2)+, VDP_DATA`) (`scene_load.s:70-73`)

Trace corroboration (`build55b_active_writer_trace.../debug.log`):
- `WP_VDP_CTRL` at `pc=0x700B4` shows `d0` sequence `0x280, 0x2A0, 0x2C0...` (first sample starts at line 4286)
- `0x280` corresponds to slot `0x14` (`0x14 * 0x20`)
- Data-port writes are dominated by `pc=0x71CD4` (13,456 writes)
  - This equals `841 tiles * 16 words` (title preload pair count 841)

### §3.3 Reservation verification vs prior audit
Prior audit claim (AGENTS_LOG old entry): tile 0 blank, scene tiles start at slot 20.

Current direct-rastan evidence:
- Preload manifests all have `slot_min = 0x14` (title/gameplay/endround)
- Title manifest first pairs start at slot `0x14`
- Trace control writes also begin at VRAM `0x280` (slot `0x14`)
- Screenshot low VRAM shows slot 0 area is not all-zero at sampled time

Conclusion:
- "Scene preload starts at slot 20" is preserved by current preload + loader behavior.
- "Tile 0 blank" is NOT confirmed in current captures; sampled slot 0 contains non-zero words.
- Direct-rastan therefore diverges from the full old audit statement (partially matches: reservation start yes; slot0 blank no).

### §3.4 Slot-0 location
- Slot 0 VRAM address: `0x0000..0x001F`
- Sampled values in this range are not all zero in the available capture.

### §3.5 Hypothesis A result
- Hypothesis A (tile graphics loaded at wrong VRAM base): REFUTED (for preload/load base)
- Reason: active loader writes scene tiles from slot `0x14` by design (`slot<<5`) and trace shows first write base `0x280`.

## §4 Plane A/B Tile Index Values (Hypothesis B)

### §4.1 Plane A first-row indices
- NOT VISIBLE in current screenshots/crops.
- Required range to answer decisively: VRAM `0xE000..0xEFFF` word dump or Memory Editor capture positioned to `0xE000`.

### §4.2 Plane B first-row indices
- NOT VISIBLE in current screenshots/crops.
- Required range to answer decisively: VRAM `0xC000..0xCFFF` word dump or Memory Editor capture positioned to `0xC000`.

### §4.3 Constant index offset check
- INSUFFICIENT from current captures because nametable ranges are not visible.

### §4.5 Pattern-view correlation
- Pattern Viewer shows meaningful pattern data in low VRAM and striped blocks, but without simultaneous nametable words at `0xC000/0xE000`, constant index-offset proof is not possible.

### §4.6 Hypothesis B result
- Hypothesis B: INSUFFICIENT

## §5 PC080SN Translation / LUT (Hypothesis C)

### §5.1 Translation path and LUT presence
In `apps/rastan-direct/src/tilemap_hooks.s`:
- Both BG and FG hooks load:
  - `genesistan_pc080sn_tile_vram_lut` (`%a2`) (`tilemap_hooks.s:115,287`)
  - `genesistan_pc080sn_attr_lut` (`%a3`) (`tilemap_hooks.s:116,288`)
- Tile index translation uses LUT lookup:
  - mask tile id, index LUT, load translated slot (`tilemap_hooks.s:168-172` and FG analog)
- No additional constant offset is added after LUT lookup.

### §5.2 LUT + preload artifact checks
Artifacts:
- `build/pc080sn_tile_vram_lut.bin`
- `build/pc080sn_attr_lut.bin`
- `build/pc080sn_scene_preload_title.bin`
- `build/pc080sn_scene_preload_gameplay.bin`
- `build/pc080sn_scene_preload_endround.bin`

Findings from artifact parse:
- All preload manifests: `slot_min=0x14`
- Tile LUT examples:
  - tile `0x20 -> 0x14`
  - tile `0x23 -> 0x15`
  - tile `0x01 -> 0x52`
- For first 1024 tiles, non-zero LUT targets were present in title slot set in this check.

### §5.4 Hypothesis C result
- Hypothesis C (LUT maps to wrong slot base): REFUTED (for checked LUT/preload consistency)
- Reason: translation uses LUT directly, and checked LUT targets align with preload slot set.

## §6 Viewer Interpretation Check (Hypothesis E)

### §6.1 Real rendering vs debug-view artifact
- OPEN-001 user report states offset is visible in actual rendered output.
- VDP Image Window in captures shows on-screen artifacting/striping, not just Pattern Viewer-only anomalies.

### §6.2 Hypothesis E result
- Hypothesis E (pure viewer interpretation artifact): REFUTED
- Reason: issue is reported in actual rendered output, not only debug viewer reinterpretation.

## §7 Consolidated Finding

### §7.1 Hypothesis table
| Hypothesis | Evidence Section | Status | Reasoning |
|---|---|---|---|
| A: Tile data loaded at wrong VRAM base | §3 | REFUTED | Loader writes to slot-based `slot<<5`; trace shows first scene load base at `0x280` (slot `0x14`) matching manifests. |
| B: Plane nametable indices offset by constant | §4 | INSUFFICIENT | `0xC000..0xEFFF` nametable word ranges are not visible in current captures. |
| C: PC080SN LUT maps to wrong slots | §5 | REFUTED | Translation uses LUT directly; checked LUT/preload artifacts align. |
| D: VDP plane/table base configuration wrong | §2 | REFUTED | reg writes and effective bases match (`E000/C000/F000/F800`). |
| E: Viewer interpretation artifact | §6 | REFUTED | Offset issue reported in actual render context (OPEN-001) and image window is affected. |
| F: Evidence insufficient | synthesis | YES | Nametable word evidence is missing for definitive B confirmation/refutation. |

### §7.2 Most-likely origin
- Most likely origin: F (insufficient to discriminate final root between nametable-index-level causes)
- Current strongest narrowing: D/C/A are refuted by available evidence; unresolved discriminator is direct Plane A/B nametable word content at `0xE000..0xEFFF` and `0xC000..0xCFFF`.

### §7.3 Required next evidence (exact)
Capture or dump at a single stable timestamp (same run state) for canonical `0057.bin`:
- VRAM `0x0000..0x1FFF`
- VRAM `0x0C000..0x0CFFF`
- VRAM `0x0E000..0x0EFFF`
- VRAM `0x0F000..0x0FFFF`
- VDP regs `0x00..0x17`

This is sufficient to resolve Hypothesis B directly.

## §8 Integrity
- §1 SHA256 reconciliation complete: YES
- §2 VDP register decoding documented from local project docs + source + trace: YES
- §3 tile data load + reservation comparison vs prior audit: YES
- §4 plane A/B first-row indices: NOT VISIBLE (required ranges listed)
- §5 PC080SN translation/LUT analysis: YES
- §6 interpretation hypothesis check: YES
- §7 hypothesis table complete: YES
- §0 dumps run: NONE
- Source/spec/tool/build/ROM modifications: NO
- ROM renames: NO
- Quick fix proposed: NO
