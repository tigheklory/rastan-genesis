# Genesis Round 1 Phase 1 — Human-Played Semantic Trace Harness

**Author:** Andy · **Date:** 2026-09-07 · **Type:** INFRASTRUCTURE / trace instrumentation
**Build produced:** NO · **Build counter:** 348 → 348 · **Production/renderer changes:** NONE

---

## 1. Phase 0 baseline statement
- **Classification:** INFRASTRUCTURE (external MAME trace tooling; no game/renderer change).
- **Relevant priors:** the Layer-A residency/publication model (`Andy_sonic1_vs_rainbow_islands_...`,
  `Andy_pure_publisher_audit_...`); the semantic-owner work (`fg_boundary_advance_segment`,
  `fg_boundary_transition_step`, record→package chain); the gate-stop thread
  (`Andy_semantically_valid_seven_epoch_gate_replacement.md`, `Cody_audit_andy_semantic_epoch_gate_stop.md`).
- **HIGH rediscovery hazards:** (a) MAME DRC bypasses Lua instruction-fetch taps — **call-level
  tracing of the owners is unreliable**, so this harness infers map-segment/package/publication
  activity from authoritative WRAM state each frame (reads in a frame notifier are reliable);
  (b) Genesis input field names are `P1 Start`/`P1 Right`/`P1 A..C` (no arcade `Coin 1`);
  (c) A5=0x00FF0000 is the gameplay work-RAM base.
- **Open issues touched:** OPEN-001/OPEN-018 (Layer-A / native plane rendering) — this sets up
  evidence, resolves nothing.
- **Contradiction check:** none.
- **KNOWN_FINDINGS impact:** Option A — no new finding to index (INFRASTRUCTURE).

## 2. Task classification
INFRASTRUCTURE. No ROM, no production source, no canonical-gate change, no counter change.

## 3. Relevant KF entries / hazards
See §1. No `KF-NNN` requires modification.

## 4. Exact purpose of the trace
Capture, once per arcade-owned frame during a **human** playthrough of Round 1 Phase 1, the
relationship: **camera/scroll X/Y → entering rows/columns → map-segment progression → Genesis
residency packages → Plane A publication**, plus a keypress marker for visible Layer-A corruption.
Two goals: (A) natural map-segment/residency progression evidence; (B) the known **Plane A vertical
+ horizontal combined-scroll population failure**.

## 5. Why Genesis is the primary capture
The immediate questions concern our translated arcade execution plus the Genesis-native Plane A/B
residency/publication system, and the reported failure is Genesis-specific (Layer A does not
populate properly when vertical scrolling combines with horizontal). Arcade capture is a later,
targeted follow-up if a specific divergence needs authoritative PC080SN row/column semantics.

## 6. Round 1 Phase 1 map-segment model
Phase 1 map segments are sequential, left-to-right; each segment contains its full vertical
component (vertical camera movement happens within a segment). Human terminology: "Round 1 Phase 1
map segment N (`active_record=N`)". Progression: segment 0 → 1 → 2 → 3 → … The trace marks
`MAP_SEGMENT_CHANGE` on each `active_record` change and logs `arcade_record` (A5+0x013E) alongside.

## 7. Known vertical/combined-scroll Plane A failure
Tighe: R1 collision ~99% correct, but Layer A does not populate properly when vertical scrolling
occurs with horizontal scrolling; vertical scrolling itself is messed up. The harness therefore
foregrounds the **vertical (Plane-A row) and combined X/Y** signals and lets Tighe mark the visible
break so it can be correlated with publication state afterward. No assumptions are baked in
(not-collision, not-solely-horizontal).

## 8. Fields traced continuously (`phase1_frames.tsv`, per frame)
Identity: `frame, scene, arcade_record, active_record (map segment), active_package, active_variant,
pending_record, pending_package, epoch_trans, pattern_dma_trans, selector, strip_index, strip_group,
tileset, scene_a0`.
Camera/scroll: `scroll_x_fg, scroll_y_fg, dx_fg, dy_fg, scroll_x_bg, scroll_y_bg` (Plane A = fg).
Publication state: `tiles_dirty, bg_rows+bg_mask, fg_rows+fg_mask (Plane-A 32-bit row-dirty),
fg_narrow (narrow-column/horizontal-seam count), fg_narrow_pend, fg_owner, reseed`.
Residency: `slots_ret, slots_reass, miss_a, miss_b`.
Plane-A integrity: `fg_sum, fg_xor` (checksum of the 2048-word staged Plane-A name buffer each
frame) + `lut034C` (an OPT-003 canary).

## 9. Events traced (`phase1_events.tsv`)
`MAP_SEGMENT_CHANGE`, `RESIDENCY_PACKAGE_CHANGE`, `X_BOUNDARY_CROSS`, `Y_BOUNDARY_CROSS`,
`DUAL_AXIS_CROSS` (X and Y tile-boundary cross in the same frame — the bug regime),
`DUAL_AXIS_PUBLICATION` (row-dirty and narrow-column publication in the same frame — ordering /
overwrite questions), `USER_MARK` (Tighe's keypress). Each carries camera, segment, package, and
publication context.

## 10. Exact symbols/addresses and provenance
Symbol set: `tools/mame/rastan_phase1_trace_symbols.txt` (curated, permanent). **Only Genesis
WRAM/BSS STATE addresses; NO code addresses.** BSS/WRAM symbols are placed by `link.ld` and are
independent of `.text` size, so they are identical across the Build 0348 tree and its variants
(verified: `active_record=0xFFB218`, `active_lut=0xFF6188` identical in every build this session).
Because the harness reads only these (and cannot reliably tap code under DRC), native code-symbol
drift between build variants does not affect the capture. Arcade entries assume A5=0x00FF0000.
Key addresses: scene 0xFFC068; arcade_record 0xFF013E; active_record 0xFFB218; active_package
0xFFB21C; selector 0xFF10A8; strip_index 0xFF10CA; scroll_x/y_fg 0xFF409A/0xFF409E;
fg_row_dirty 0xFF4006; fg_narrow_desc_count 0xFF408C; staged_fg_buffer 0xFF50A0; active_lut 0xFF6188.

## 11. Map-segment tracing
`active_record` (+ `arcade_record`) per frame; `MAP_SEGMENT_CHANGE` event on change. Smoke-verified
(0→1 captured).

## 12. Horizontal-column tracing
`X_BOUNDARY_CROSS` on each 8px `scroll_x_fg` tile crossing; `fg_narrow_desc_count` (the
narrow-column/entering-column publisher) captured per frame and in the event. If there is no clean
"entering-column semantic event" callback (there is not, under DRC), this pairing (X crossing +
narrow-column count + scroll delta) is the reconstructable proxy. Smoke-verified (207 X crossings).

## 13. Vertical-row tracing
`Y_BOUNDARY_CROSS` on each 8px `scroll_y_fg` tile crossing; `fg_row_dirty` mask + popcount (the
Plane-A row publisher) captured per frame and in the event. This is the primary bug axis.
Smoke-verified (43 Y crossings; `fg_owner=0`/`fg_rows=0` faithfully recorded — evidence, not fault).

## 14. Combined-axis publication tracing
`DUAL_AXIS_CROSS` (X+Y cross same frame) and `DUAL_AXIS_PUBLICATION` (row + narrow-column same
frame) events, each with ordering-relevant context (dx, dy, fg_rows, fg_mask, fg_narrow).
Smoke-verified (3 DUAL_AXIS_CROSS). These are the special-interest cases for "does one axis overwrite
the other / is one omitted / wrong destination."

## 15. Residency/package tracing
`active_package` per frame; `RESIDENCY_PACKAGE_CHANGE` on change (with map segment, camera,
epoch_transitions). `slots_retained/reassigned`, `miss_a/b`, `pattern_dma_trans` captured.

## 16. Transition/stable handoff tracing
`fg_boundary_transition_step` (the column-45 overlap→stable handoff) and `fg_boundary_advance_segment`
cannot be call-tapped under DRC; their EFFECTS are captured via `active_package`/`active_variant`
changes and the `RESIDENCY_PACKAGE_CHANGE` events (which record epoch_transitions and camera). The
record→package chain (0/1/2→pkg0, 3→pkg5 rope, 4→pkg6 waterfall, 5→pkg2, …) lets the analysts label
overlap vs stable from the captured package sequence.

## 17. VBlank/publication observability
Per-frame `fg_row_dirty`/`bg_row_dirty` masks (staged during the tick, before next-VBlank commit),
`fg_narrow_desc_count`, `tiles_dirty`, `staged_dest_ptr_*`, and the staged Plane-A checksum let the
analysts correlate staged content with row vs narrow-column publication volume without heavy VBlank
instrumentation. The harness does not tap the commit routines (DRC) and does not change publication
timing.

## 18. User-visible corruption marker
`USER_MARK` event on a keypress edge. Default key **M** (`KEYCODE_M`; free vs the Genesis pad).
Smoke-verified that the key code resolves and the poll runs without error (an actual keypress was
not exercised headless). Tighe presses **M** whenever Layer A visibly breaks; no need to stop
playing or type anything else.

## 19. Trace output files / schema
Per session dir `states/traces/rastan_phase1_human_trace_<timestamp>/`:
`trace_metadata.txt` (ROM/symbol/harness identity + frame count), `phase1_frames.tsv` (§8 header),
`phase1_events.tsv` (`frame  event  detail`), `SHA256SUMS.txt`. TSV, tab-separated, header row.

## 20. Raw-evidence preservation policy
Each run writes a **unique timestamped** directory (never overwritten). On exit the runner writes
`SHA256SUMS.txt` of the three raw files and `chmod -R a-w` locks the directory read-only. The raw
trace is immutable evidence: Andy and Cody analyze **copies / derived files**, never the raw. Both
agents receive the same raw trace.

## 21. ROM / symbol / hash matching
Primary ROM: **Build 0348** `dist/rastan-direct/rastan_direct_video_test_build_0348.bin`, SHA-256
`fac088eb0f8e9d374af80d9381aeecfe20be2ec6138ab688cfc6d0c45db1bf6b`. The runner records the live ROM
SHA, symbol-file SHA (`2428f0103b06592c…`), and harness SHA (`e28dfbf2cd954f71…`) into
`trace_metadata.txt` every run, so a ROM/symbol mismatch is detectable. Symbols are BSS/WRAM state
only (§10) — valid for 0348 regardless of code drift.

## 22. Smoke-test evidence
Headless run on 0348.bin with scripted input (scratch-only driver; NOT part of the harness):
harness armed (marker key resolved), 7191 frames captured and closed cleanly, scroll X/Y changing,
`active_record` 0xFFFF→0→1 and package/selector/tileset/scene_a0 resolving, events emitted —
MAP_SEGMENT_CHANGE ×5, RESIDENCY_PACKAGE_CHANGE ×4, X_BOUNDARY_CROSS ×207, Y_BOUNDARY_CROSS ×43,
DUAL_AXIS_CROSS ×3. Per-frame Plane-A checksum ran with negligible overhead. No ROM/build/counter
change.

## 23. Exact instructions for Tighe
```
1. Run:  tools/mame/run_rastan_phase1_trace_wsl.sh
         (traces Build 0348 by default; pass a ROM path to trace a different one)
2. MAME opens in a window with sound; controls are the normal Genesis pad keys.
3. Play Round 1 Phase 1 normally, start to end.
4. Use the vertical areas naturally, INCLUDING horizontal movement while the camera moves
   up/down (climbing/descending). Do not avoid the known graphics bug.
5. When Layer A visibly breaks (missing tiles / corrupt vertical population / wrong combined
   scroll), press  M  (keep playing; no need to stop or type).
6. Continue playing after the corruption so recovery/persistence is captured too.
7. Reach the end of Phase 1 (Phase 2 is out of scope but harmless if you drift in).
8. Exit MAME normally (close the window / Esc).
9. Send the whole generated folder:
      states/traces/rastan_phase1_human_trace_<timestamp>/
   (trace_metadata.txt, phase1_frames.tsv, phase1_events.tsv, SHA256SUMS.txt)
```

## 24. Files created/modified
Created (permanent, untracked): `tools/mame/rastan_phase1_trace_symbols.txt`,
`tools/mame/scripts/rastan_phase1_semantic_trace.lua`, `tools/mame/run_rastan_phase1_trace_wsl.sh`,
this report. No production source or ROM changed. (The uncommitted `palette_pending` working state
was momentarily reverted to confirm the 0348 tree, then restored — no work lost.)

## 25. Open/Closed Issues Impact
OPEN-001/OPEN-018 (Layer-A/native plane rendering): evidence harness prepared; nothing resolved or
closed. No issue opened.

## 26. KNOWN_FINDINGS impact
Option A — no new finding to index (INFRASTRUCTURE).

## 27. Build status
No build produced. Counter 348 → 348. Build 0348 artifacts intact (SHA `fac088eb…`).

## 28. Next step after Tighe captures the trace
Tighe plays all of Round 1 Phase 1 and returns the untouched raw trace directory. Andy and Cody then
analyze that SAME raw trace **independently** (neither reads the other's conclusions first) to answer:
why does native Genesis Layer-A population diverge when vertical and horizontal scrolling interact?
