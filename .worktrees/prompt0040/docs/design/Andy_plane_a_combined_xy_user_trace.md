# Andy — User-Driven Plane-A Combined-X/Y Trace (Build 0398) — EXTERNAL, READ-ONLY

**Baseline:** Build 0398. **Counter:** 398 → 398 (no ROM, no build, no production source changed).
**Build 0399 consumed: NO.** This is external MAME-Lua instrumentation only; it never reads or writes a
ROM/WRAM location to modify it, and it adds no production scaffolding. Platform: **GENESIS NTSC MAME**
(`genesis`).

## 1. Purpose

Catch the intermittent misplaced-8×8 Plane-A terrain cell that appears during **combined horizontal +
vertical** camera scrolling (see `Andy_build0399_plane_a_combined_xy_misplaced_cell.md`). The defect is
intermittent, so a fixed-length headless capture will usually miss it. Instead **Tighe plays normally**, and
when he **sees** a bad tile he presses **M once**. A rolling buffer keeps the streaming history from *before*
the keypress, so the first bad streaming event is preserved rather than lost.

## 2. What Tighe runs

```
tools/mame/run_plane_a_xy_trace_wsl.sh
```

That launches the USA/NTSC `genesis` machine with the current baseline ROM
`dist/rastan-direct/rastan_direct_video_test_build_0398.bin` (pass a different ROM path as the first argument
to override). The game window is interactive and plays at full speed — the trace samples once per frame, so
there is no per-instruction slowdown.

## 3. How to use it

1. Run the command above. The terminal prints `[plane_a_xy] READY ...` and a SELF-TEST banner.
   **Do the self-test first:** click the MAME window to give it focus, then tap **M** once. You should
   immediately see `[plane_a_xy] MARK (pre) frame N -> ...` in the terminal and a
   `plane_a_xy_marker_N.txt` appear. If nothing prints, keys are not reaching MAME (window focus / WSLg
   keyboard) — fix that before the real capture. (The **comma** key `,` also marks, in case M is awkward on
   your keyboard.) After the self-test you can ignore that throwaway file.
2. Play normally. **Fastest repro:** Segment 2/3 **climbable rope** — jump off so the camera moves
   vertically AND a little horizontally; or jump up/down ordinary stepped terrain with some horizontal drift.
3. The moment you **see** a misplaced Plane-A terrain cell (a stray/duplicated 8×8 tile, or a cell missing
   where terrain should be), press **M once**. The terminal immediately prints
   `[plane_a_xy] MARK (pre) frame N -> ...plane_a_xy_marker_N.txt ... [pre 180 + post 0]` and the file is
   written **right then** (the pre-history is saved instantly, so pausing or quitting now cannot lose it),
   followed by `[plane_a_xy] M at frame N; pre-history saved, capturing 30 more frames...`.
4. Press **F12** for a MAME screenshot. It is saved in the **same** trace dir,
   `build/mame/home/plane_a_xy/` (the launcher sets `-snapshot_directory` there). That one gameplay
   screenshot is all that's needed — the Plane-A name-table content that an Exodus-style tilemap viewer would
   show is **already in the trace .txt** as the per-cell `staged` vs `vram` words on the COMBINED frames.
   (MAME has no Exodus "Plane-A boundaries" overlay; don't look for one.)
5. Keep playing for ~½ second; the terminal then prints
   `[plane_a_xy] MARK (final) frame N -> ... [pre 180 + post 30]` and the same file is rewritten with the
   post-roll included. If you close MAME before that, an on-stop backstop flushes whatever was captured. You
   may press M again later for another occurrence in the same session; each press writes its own numbered pair.

## 4. Output

Written to `build/mame/home/plane_a_xy/` (the F12 screenshot lands here too):

- `plane_a_xy_marker_<frame>.txt` — one line per frame: the **180 frames before** the mark (pre-marker
  rolling history) followed by the **30 frames after** (post-marker tail). At the Genesis 60 Hz that is roughly
  3 s before + 0.5 s after the keypress. `<frame>` is the frame number at the keypress, which names the capture.
  The file is written the instant M is pressed (pre-history only) and rewritten once with the post-roll added;
  if MAME is closed in between, the on-stop backstop flushes what was captured.
- `plane_a_xy_marker_<frame>_summary.txt` — counts of combined-X/Y frames, front-advanced frames, and
  staged≠VRAM intersections, plus how to read the full file.

Per-frame columns (`# columns:` header in the file):

```
FRAME  sx sy   grp idx ref   col nrow  COMBINED front_adv  | ev:...  | isect(staged/vram)
```

| Field | Source | Meaning |
|---|---|---|
| `sx` / `sy` | `staged_scroll_x_fg` 0xFF409A / `staged_scroll_y_fg` 0xFF409E | staged Plane-A scroll X / Y |
| `grp` / `idx` | arcade `strip_group` a5@0x10CC / `strip_index` a5@0x10CA | live horizontal front block / front cell-in-block |
| `ref` | `plane_a_src_ref_block` 0xFF61F4 | resolver mode: `10` (=16) ⇒ resident/vertical ring-unwrap; else horizontal leading-edge |
| `col` | `fg_col_dirty` 0xFF61EC (two longs) | number of dirty Plane-A columns this frame |
| `nrow` | `fg_row_dirty` 0xFF4006 (one long) | number of dirty Plane-A rows this frame |
| `CMOTION` | derived | **both** scroll axes moved vs the previous frame = true combined H+V motion (H and V dirty on separate frames, so same-frame col+row never happens — this is the real combined indicator) |
| `front_adv` | derived | the live front (`grp:idx`) changed vs the previous frame (0x558C6 advanced the source) |
| `ev:` | per-PC hooks (if available) | intra-frame producer order: Hsel0/Hsel12/Vup/Vdown/COMMIT with each one's grp/idx/ref |
| `dirty` | `fg_col_dirty` / `fg_row_dirty` | per frame, which columns/rows were dirtied (COL n / ROW n) and by which producer (via `ref`) |

Plus, at the top of every dump, the **full `staged_fg_buffer` grid** (32 rows × 64 cols of Plane-A name
words) captured at the marker instant, with the scroll→ring-cell mapping. This is the intended Plane-A
content the VBlank DMA publishes. Because the defect persists statically after the motion stops, the
misplaced cell is pinned here **even if you press M several seconds after seeing it** — no need to catch the
producing frame.

**Why not VRAM:** this MAME genesis build does **not** expose Plane-A VRAM to Lua — the `:gen_vdp`
`videoram` space is a 16 KB stub (`address_mask 0x3FFF`) that reads all-zero; the real 64 KB VRAM is internal
to the `315_5313`. So the trace reads the staged buffer (WRAM, fully readable) and uses the **F12
screenshot** as the "actually displayed" ground truth.

## 5. How the capture answers the first-divergence question

The static narrowing (`Andy_build0399_...md` §4) needs to split one captured bad cell into Case A vs Case B.
With VRAM unreadable, the split is made from the **staged grid + the screenshot**:

- **Case A — staging itself was wrong (producer bug).** The on-screen bad cell, located in the staged grid
  via the scroll mapping, holds the **wrong** word (one that breaks the local terrain pattern / differs from
  what re-entry produces). The error is upstream in the producer — mechanism 1 (H and V read the live front
  at different points and a `front_adv` landed between them) or mechanism 2 (resident-mode ring-unwrap
  boundary flip). The `ref` toggle (horizontal `= strip_group` vs `10`hex=16 resident/vertical) and
  `FRONT_ADV`/`CMOTION` in the combined window identify the suspect producer and frame.
- **Case B — the DMA/commit mis-published (staging was correct).** The staged cell at the bad on-screen
  location is **correct/consistent** with its neighbours, yet the screenshot shows the wrong tile ⇒ the
  publication (`vdp_commit_fg_narrow_strips` order/omission) is at fault. Fits "self-repairs on re-entry."

To locate the bad cell: the summary prints `screen top-left ring cell rowR colC` from the marker scroll;
"upper right of screen" is ~row R (+0–3) and col C+36..39 (320 px ≈ 40 cells wide), wrapped into the 32×64
ring. I cross-check against the F12 screenshot.

## 6. Mechanism notes (reused project conventions — not rediscovered)

- **M marker:** `machine.input:code_from_token("KEYCODE_M")` with edge-detect (`marker_prev`), exactly the
  established marker in `tools/mame/scripts/rastan_genesis_rope_ledge_human_trace.lua`. **Reused: YES.**
- **Output dir:** `-homepath` + `homepath` option, as in `genesistrace.lua`.
- **VRAM read:** `machine.devices[":gen_vdp"].spaces["videoram"]`, as in the project's VRAM dump scripts.
- **Launcher:** `run_plane_a_xy_trace_wsl.sh` mirrors `run_genesis_trace_wsl.sh` (MAME discovery, WSLg audio,
  window/resolution, `-skip_gameinfo`, `-homepath`, `-autoboot_script`).
- **Sampling / poll model:** per-frame via `emu.register_frame_done` (always playable), the SAME hook the
  proven `USER_MARK` marker uses. This matters: `register_frame_done` runs **after** MAME polls physical
  input each frame, so `code_pressed` reflects the live key state. The earlier version used
  `emu.add_machine_frame_notifier`, which fires **before** the input poll — `code_pressed` read stale/empty
  state and the M press was never seen (the cause of two empty user runs). A fallback to
  `add_machine_frame_notifier` remains only if `register_frame_done` is ever absent. A guarded `cpu:add_exec`
  block adds intra-frame producer-PC events **only if** this MAME exposes it; this build does not, so the
  script prints `per-PC hooks: not installed` and falls back cleanly. The per-frame discriminator
  (staged-vs-VRAM on combined frames + front_adv) is captured regardless.

## 7. Mechanical validation (performed by Andy — no gameplay)

A throwaway copy with a synthetic mark injected at a fixed frame (no keypress, output redirected to a scratch
dir) was run headless on Build 0398:

- M path fires → `dump()` runs → **both** `plane_a_xy_marker_<frame>.txt` and `_summary.txt` are created. **PASS**
- Retained history is correct and non-overlapping: a mark at frame 40 produced `retained 70 (pre 40 + post 30)`,
  frames F1..F70 in order, no duplicated frames. **PASS** (the ring holds pre-marker frames only; post frames
  go to a separate tail).
- **Root cause of the empty user runs (found and fixed):** the marker was polled from
  `emu.add_machine_frame_notifier`, which fires before MAME polls physical input, so `code_pressed` never saw
  the M press — two user runs (one with a 5–10 s wait, which already ruled out post-roll timing, and the
  measured 60/s frame rate confirms ½ s post-roll completes) produced no mark and no file. Switched the
  poll/sample loop to `emu.register_frame_done` (the same hook the proven `USER_MARK` marker uses, which runs
  after input is polled). Headless confirms the script now selects `register_frame_done`, both marker tokens
  (M and comma) resolve under `assert`, and the pre/final dumps fire. The live keypress itself can only be
  confirmed by the on-screen SELF-TEST (tap M at the title and watch for `MARK (pre)`).
- Loss-proofing: the mark path writes the file immediately (`MARK (pre) ... [pre N + post 0]`) and rewrites it
  after the post-roll (`MARK (final) ... [pre N + post 30]`); `emu.add_machine_stop_notifier` is present in this
  MAME build, so the on-stop backstop is active. **PASS.**
- Columns/header well-formed; summary counters present. **PASS**

Fields read all-zero in that headless run because the emulator never left boot (no input, nothing scrolled);
that is expected and confirms only the *mechanism*. The real values populate during interactive play. Andy
performed **no gameplay verification** of the defect itself — authority for gameplay observation: **TIGHE**.

---
Production source changed: **NO** · ROM built: **NO** · Counter after: **398** · Build 0399 consumed: **NO**.
