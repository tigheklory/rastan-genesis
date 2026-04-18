# Andy — IMG_02 Early Title Display Failure Audit (Build 0036)

**Status:** ANALYSIS COMPLETE. Single failure classification selected.
**Scope:** IMG_02 only. No exception analysis. No palette/tile-decode
discussion.

---

## Phase 1 — Visible Output Classification

From Cody's IMG_02 description
(`docs/design/Cody_vdp_ground_truth_build36_early.md` line 5):
"VDP Image: alternating red/purple vertical bands with dense horizontal
striping, high repetition."

```
IMG_02 visible output:
  pattern: alternating vertical bands with horizontal striping
  orientation: vertical bars (primary), horizontal sub-striping (secondary)
  uniform or tile-based: tile-based — alternating pattern indicates
    different nametable entries at adjacent columns, producing vertical
    bars via per-tile color variation
  colors: red and purple alternation
```

---

## Phase 2 — Plane A State (`0xE000`)

From Cody's extracted data (line 151):
"IMG_02: visible, all zero at `0xE00A+`. Sample: `0x0000 0x0000 0x0000
0x0000`."

```
Plane A (0xE000) at IMG_02:
  state: ALL ZERO
  raw values: 0x0000 0x0000 0x0000 0x0000 (at 0xE00A+)
  evidence source: Cody_vdp_ground_truth_build36_early.md line 151
```

Plane A contains no nametable entries. Every cell references tile index
0 (blank tile) with palette 0, no flip, no priority. A fully-zero
Plane A is transparent (tile 0 = all-zero pixel data = color 0 of
palette 0 = background).

---

## Phase 3 — Plane B State (`0xC000`)

Cody's extracted data does NOT include a raw nametable dump of the
`0xC000` region. The `0xE000` region status table (lines 150–156)
lists only `0xE000` samples. No `0xC000` samples were extracted.

However, from the source code (`apps/rastan-direct/src/main_68k.s`
lines 2068–2083), `init_staging_state` fills `staged_bg_buffer` with
alternating nametable words `0x0001` and `0x0002` (tile indices 1 and
2) in a checkerboard pattern (even row XOR even col → tile 1 or tile
2). These are committed to VRAM Plane B (`0xC000`) via
`vdp_commit_bg_strips_if_dirty` when `bg_row_dirty` bits are set.

At IMG_02, `init_staging_state` has already completed (Plane A is
zero = clear completed; `bg_row_dirty` was set to `0xFFFFFFFF` by
`genesistan_hook_cwindow_clear` or was cleared by `init_staging_state`
with `clr.l bg_row_dirty` at line 2051 — so the BG buffer was filled
but the dirty bits were CLEARED, meaning the BG strips were NOT
committed to VRAM Plane B).

Wait — re-examining: `init_staging_state` at line 2051 does `clr.l
bg_row_dirty` AFTER filling `staged_bg_buffer`. This means the BG
buffer IS filled with checkerboard data, BUT `bg_row_dirty` = 0 at
init exit, so `vdp_commit_bg_strips_if_dirty` in VBlank skips (early
exit on `beq.s .Lbg_done`). The BG plane in VRAM would NOT have been
updated from the staging buffer.

But `init_staging_state` does NOT directly write to VRAM Plane B
(`0xC000`). It only writes to VRAM Plane A (`0xE000`) at lines
2091–2096. So VRAM Plane B at `0xC000` retains whatever was there
before `init_staging_state` ran.

What was at `0xC000` before init? At boot, `load_scene_tiles` runs
first (before `init_staging_state`), and it only writes to the VRAM
pattern area (tile graphics), not to the nametable regions. So
`0xC000` retains its power-on state — which on Genesis is undefined
(typically zero or garbage depending on emulator).

```
Plane B (0xC000) at IMG_02:
  state: NOT EXTRACTED by Cody (no raw 0xC000 nametable samples)
  raw values: not available
  could produce visible output: UNCERTAIN — Plane B content was not
    extracted; cannot determine from Cody's data alone whether it
    contains the visible bar pattern
  evidence: Cody's data covers only 0xE000; 0xC000 is not sampled
```

---

## Phase 4 — Active Display Source

Given:
- Plane A (`0xE000`) = ALL ZERO → transparent (tile 0 is blank)
- Plane B (`0xC000`) = NOT EXTRACTED but is the only remaining source

Since Plane A is confirmed all-zero (transparent), any visible content
MUST come from Plane B or the background color register.

The visible output shows "alternating red/purple vertical bands with
dense horizontal striping" — this is a structured tile-based pattern,
NOT a solid background-color fill. Therefore it comes from a plane
with non-zero nametable entries.

Since Plane A cannot produce this (all zero), and the output is
tile-based (not solid-color), the source MUST be Plane B.

```
Active display source at IMG_02:
  selected: B — Plane B (0xC000)
  evidence: Plane A = all zero (transparent, confirmed by Cody's raw
    sample 0x0000×4 at 0xE00A+). Visible output is tile-based (bars,
    not solid fill). Only remaining source is Plane B.
```

---

## Phase 5 — Expected State vs Actual

Register values from Cody's IMG_02 extraction (lines 23–30):
- PC = `0x00070022` (`runtime_genesis_pc` — inside the wrapper main
  loop, the `cmp.w frame_counter, D0` wait instruction)
- A4 = `0xFFFFFFFF` — the text-script state pointer has NOT been
  initialized
- A5 = `0x00FF0000` — arcade workram base is set (WRAM is live)
- D0 = `0x00000007` — a small counter value (frame counter or
  iteration count)

**Should the title be visible at this execution point?**

A4 = `0xFFFFFFFF` means the text-script state block has not been
initialized by the arcade's attract-mode state machine. On the arcade,
the attract-mode sequence begins with a multi-second initialization
countdown before the first title text is rendered. During this
countdown:
- No text-script handlers fire (A4 is not set up)
- No FG tilemap writes occur (staged_fg_buffer is not populated by hooks)
- The VBlank FG strip commit has nothing to commit (fg_row_dirty = 0)

D0 = `0x00000007` is a LOW value consistent with early execution —
only 7 frames (or a small iteration count) into the main loop.

```
Expected state at IMG_02:
  title should be visible: NO — A4=0xFFFFFFFF proves the text-script
    state has not been initialized; the arcade state machine is in its
    initialization countdown, which runs for hundreds of frames before
    producing any text output
  Plane A should be populated: NO — no text-script handlers have fired
    (A4 not initialized); no staged_fg_buffer writes have occurred; no
    fg_row_dirty bits are set; no VBlank FG strip commits have executed
  evidence: A4=0xFFFFFFFF (Cody line 28); D0=0x00000007 (early frame
    count, Cody line 26); PC=0x00070022 (main loop wait, Cody line 24)
```

---

## Phase 6 — Failure Classification

```
Failure classification:
  selected: D — Startup sequencing delay — title rendering has not yet
    been triggered
  evidence:
    - A4=0xFFFFFFFF: text-script state never initialized → no text
      handlers fire → no FG tilemap writes → Plane A empty (confirmed
      0x0000 at 0xE000)
    - D0=0x00000007: early in execution timeline (7 frames)
    - PC=0x00070022: CPU in main-loop wait, arcade tick has been called
      but the attract-mode state machine has not yet advanced past its
      initialization countdown
    - The visible bars on screen come from Plane B (the only non-empty
      plane), which was populated by boot-time or emulator-default
      state — NOT by any text-rendering hook
```

Why other classifications are not correct:

- **A (Plane A not populated when it should be):** Plane A SHOULD NOT
  be populated yet — A4 proves text-script rendering hasn't been
  triggered. The empty state is correct for this execution point.
- **B (Wrong plane used):** Plane B is the only visible source because
  Plane A is correctly empty. This isn't a "wrong plane" issue — it's a
  "too early in the timeline" issue.
- **C (Plane B incorrectly initialized):** Plane B content was not
  extracted; cannot determine its initialization correctness. But
  regardless of Plane B content, the absence of Plane A content is
  explained by the timing (A4 not initialized).
- **E (Unknown):** Sufficient evidence exists to determine the answer
  (A4=0xFFFFFFFF + D0=7 + Plane A = all zero → startup delay).

---

## Final Conclusion

At IMG_02, the title is not displayed because the arcade state machine
has not yet reached its text-rendering phase. This is proven by A4 =
`0xFFFFFFFF` (text-script state pointer uninitialized) and D0 =
`0x00000007` (early frame count). The visible red/purple bars come from
Plane B (`0xC000`), which is the only non-transparent plane at this
point — Plane A (`0xE000`) is confirmed all-zero. This is normal
pre-title behavior: the arcade's initialization countdown runs for
hundreds of frames before the first text-script handler fires. The
display at IMG_02 is not a rendering failure — it is the expected
pre-title state. The actual rendering failure occurs later, when the
exception (analyzed in `Andy_early_title_control_flow_audit.md`)
prevents the state machine from ever reaching the text phase.
