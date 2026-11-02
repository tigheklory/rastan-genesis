# Build 0528 — R1-S2 no-publication retained-row correction

Date: 2026-11-02  
Agent: Cody  
Task: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055`  
Baseline: Build 0526; Build 0527 was tested unchanged and not accepted  
Produced build: 0528, candidate only

## Outcome

The R1-S2 camera's no-publication vertical-motion path was rebuilding exposed Plane A rows from the
already-advanced current record. Original arcade `$0558E0` had completed record 16, saved its
selector in `A5+$132C`, and advanced `A5+$013E` to record 17. Because `$055704/$055790` changes Y
without writing name RAM, the original hardware still exposes record 16. Build 0528 reproduces that
retained predecessor: existing `record-1` native pan rows for selector 1/2, or live descriptor
pointers one complete 16-entry revolution back for selector 0.

Build 0527's ordinary entering-row residency change did not execute on this route and therefore did
not affect Tighe's observed problem. Build 0526's separate mixed selector-1/selector-0 ring suffix
correction remains intact.

## Artifacts and source identity

Build-counter transition: 0527 -> 0528. Ledger status:
`canonical=PASS entry=PASS epoch=PASS`.

Implementation source commit: `e667827c7ba776813e692d78b718887e10564fda`.

| ROM | Bytes | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0528.bin` | 3,792,568 | `d814e0fec605af60e29a044bc867c4d37591828921f8546720f4aeba7d6107c2` |
| `dist/rastan-direct/rastan_direct_video_test_build_0528_S1-2.bin` | 3,792,568 | `c4c6fbe2fbc1f684c344eecc0f9fd588b43301a82863bc4a206df02d5acfc82c` |

The S1-2 derivative differs only at the established selector `$DF` and direct-start music command
`$27` sites. The canonical manifest records 228 opcode-replacement sites, expected coverage
`0x39DEB8`, and coverage delta `0x50000`.

## Files changed

- `apps/rastan-direct/src/tilemap_hooks.s`
- `tools/translation/verify_bg_a_incremental_background.py`
- `tools/translation/verify_plane_a_scene_fill_maps.py`
- this report and the assignment report
- `AGENTS_LOG.md`

## Semantic scope and architecture

Subsystem changed: native Plane A realization during an original no-publication foreground-Y step.

Semantic cut: the original arcade decision to move Y while retaining the completed PC080SN ring.
The removed chip tail is PC080SN name-RAM retention/exposure below that decision; Genesis emits final
Plane A name words. No additional legacy code was removed. Existing descriptor tables, pan-row
assets, staging/dirty-row publication, collision grid, and the Build 0527 ordinary-publication
behavior intentionally remain. No new shadow tilemap, map, buffer, runtime translator, VRAM/DMA
allocation, collision path, or scene-specific coordinate adjustment was added.

## Static proof

- Original Ghidra/disassembly flow proves `$0558E0` advances `A5+$013E` after retaining the completed
  selector and that `$055704/$055790` can move Y without `$055948/$055990/$055A14` publication.
- Record 16 versus record 17 differs nonuniformly across exposed rows, explaining why two features
  appear displaced in opposite directions without a global X offset.
- All 16 pointer groups by all 64 columns select the exact prior selector-0 revolution.
- 16,384 no-publication predecessor cells prove package/asset coverage.
- Existing selector gate passes 128 destination, 1,869,856 selection, 1,869,856 output, and 4,096
  residency cases.
- Scene/fill gate passes 24,576 scene, 204,800 checkpoint, 16,384 pan, 16,384 predecessor, and
  1,138,688 authored-descriptor cell checks.
- Subround validation proves the S1-2 derivative changes only its two declared bytes.

## Runtime validation and regressions

Exact runtime platform: Genesis-driver MAME, USA/NTSC target, through the Makefile-required
30-second release trace. Result: 1,798 frames; final PC `$03B2C8`; SP `$00FEFFFC`; no unique unmapped
addresses. Canonical, gameplay-entry, seven-epoch/package, and boot gates passed.

No original arcade MAME runtime, BlastEm, Exodus, real-hardware, task-specific trace, automated
R1-S2 traversal, or save-state test was run. Static original-arcade evidence was used as directed.
The gates protect boot, entry, epoch/package selection, selector transforms, checkpoints, pan assets,
and declared subround patch scope; they do not replace Tighe's visual route test.

## Limitations, USER MUST VERIFY, and STOP

This is not accepted. Tighe must use `_S1-2` to verify:

1. unchanged initial castle composition;
2. both reported chains remain aligned while rows 25..32 scroll into view;
3. upward/downward camera reversal is coherent;
4. the record-17 to record-18 selector transition remains correct;
5. R1-S1/R1-S2 checkpoint respawn, collision/traversal, Plane B, sprites, palettes,
   Re-In-Carnation, and boss entry remain unchanged.

Unresolved limitation: actual gameplay appearance on Tighe's route is untested here. STOP status:
**NO**. Build status: **candidate pending Tighe**.

Full evidence report:
`docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055_r1s2_scrolled_metatile_alignment.md`.
