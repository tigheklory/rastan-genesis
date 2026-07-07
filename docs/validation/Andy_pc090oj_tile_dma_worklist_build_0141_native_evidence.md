# Andy — Build 0141 Native DISPLAY_OFF / Tile-DMA / SAT Verification (Evidence Only)

**Date:** 2026-07-06
**Type:** Evidence only — **no** implementation/source/ROM/build/tool/branch/commit change. Build 0141 preserved.
**Build 0141:** `dist/rastan-direct/rastan_direct_video_test_build_0141.bin`, SHA256 `cebd389e8114b316881188623b41d4b71808b5738a39d2cd4a773163bc8aa04c`.
**Build 0140 baseline:** `f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`.
**Branch:** `rastan-direct-proposal` (unchanged; HEAD `5182e0092f9d3ee5bf5c5d7b716ac3ac40cc7999`; not committed/pushed).
**Evidence dir:** `states/traces/build0141_native_displayoff_dma_sat_20260706_194758/`.

**Outcome A** — exact DISPLAY_OFF intervals, direct tile-DMA evidence, byte-identical SAT parity, removed-path proof, coverage audit, and valid MAME execution proof all completed.

## MAME execution (established native-debugger workflow, reused)
Reused the prior successful Cody harness (`-debug -debugger qt -debugscript` with `bpset <pc>,1,{tracelog "…cyc=%d…",totalcycles,…;g}` and a lua that exits after N frames). **Successful command:**
```
mame genesis -cart <ROOT>/dist/rastan-direct/rastan_direct_video_test_build_0141.bin \
  -window -nothrottle -sound none -skip_gameinfo \
  -snapshot_directory <TDIR>/screenshots -snapname b0141_%i \
  -debug -debugger qt -debugscript <TDIR>/build0141_debug.cmd \
  -autoboot_script <TDIR>/frames.lua  > mame_stdout.log 2> mame_stderr.log
```
- MAME exe `/usr/games/mame`; driver `genesis`; working dir repo root; video `-window`; debugger `qt`; debugscript `build0141_debug.cmd`; lua `frames.lua`.
- **Exit status 0.** stdout: `Average speed: 16.98% (12 seconds)` — ran to the lua's `machine:exit()` at frame 800 (intentional completion, not a crash). stderr: only benign ALSA/Qt/runtime-dir warnings, no fatal error.
- **ROM-load proof:** `sha256sum` of the loaded cart path = `cebd389e…aa04c` (Build 0141); the debugscript resolved Build 0141 PCs and fired **702 VBLANK / 702 DISPLAY_OFF / 702 DISPLAY_ON / 702 SAT_DMA** events; `lua_frames.log` reached states `0/1/0`, `0/1/2`, `2/2/6`.
- The prior `-debugger none` did not execute native breakpoints; `-debugger qt` is the established working method (per the prior Cody note). A window opening/closing was **not** treated as proof — exit code, stdout speed line, EV-event counts, and lua frame log confirm a full run.

## 1. Build 0141 runtime addresses (re-derived from `out/symbol.txt` + `build/genesis_postpatch.disasm.txt`)
| Item | runtime_genesis_pc / WRAM |
|---|---|
| DISPLAY_OFF boundary (MODE2=0x34 setup) | `0x0700CE` |
| DISPLAY_ON boundary (MODE2=0x74 setup) | `0x0700E6` |
| VBLANK entry | `0x0700C2` |
| tile-DMA worklist commit entry (`.Lvcs_tile_dma`) | `0x0723BE` (reads count `0xFF69AE`; `beq` skip if 0) |
| sprite-pattern DMA trigger | `0x072452` (`move.l %d1,(%a3)`, cmd carries 0x40/0x80) |
| residency write (post-DMA) | `0x07245E`→`0x072462` (`sprite_tile_resident_code[slot]=code`) |
| SAT DMA entry (`.Lvcs_sat_dma`) | `0x07246C` (length = active×4; source `0xFF6188`) |
| worklist count / table | `0xFF69AE` / `0xFF686E` |
| staged SAT / active-count | `0xFF6188` / `0xFF67CC` |
| resident-code array | `0xFF67CE` |
- `_vblank_service`/DISPLAY_OFF/ON PCs are unchanged vs Build 0140; sprite commit internals moved (`vdp_commit_sprites_vram=0x72166`, tile-DMA `0x723BE`, SAT `0x7246C`).

## 2. DISPLAY_OFF intervals (native `totalcycles`, interval = cyc@0x0700E6 − cyc@0x0700CE)
| State (stable, count=0) | Build 0141 interval (cyc, median) | Build 0140 ref | Reduction |
|---|---:|---:|---:|
| `0/1/0` | **1426** | 16350 | **−14924 (91.3%)** |
| `0/1/2` | **1426** | 16350 | **−14924 (91.3%)** |
| `2/2/6` | **1426** | 16548 | **−15122 (91.4%)** |

- Distribution: across 209/161/161 stable samples per state the **min = median = 1426 cycles**; occasional larger frames (up to ~56,428) occur with sprite `count=0` and are attributable to unrelated **PC080SN tilemap (BG/FG) broad commits** in the same DISPLAY_OFF window (not touched by this change). Representative clean pairs: `0/1/0` OFF cyc=6844075 ON cyc=6845501 → 1426; `0/1/2` OFF=35352385 ON=35353811 → 1426; `2/2/6` OFF=80799695 ON=80801121 → 1426.
- ~1426 cyc ≈ ~2.9 scanlines of display-off — consistent with Tighe's "much thinner but a thin line remains" (the residual is the DMA/register window + pre-DISPLAY_OFF work that still delays when DISPLAY_OFF begins, out of this change's scope).

## 3. Nonzero worklist frame (direct debugger evidence)
Peak burst commit: `TILE_COMMIT_ENTRY count=0x001B (27)`, `active=0x1B` → **27 `TILE_DMA_TRIGGER` events in that frame (count == triggers, exact).** All 27 entries (slot / required code / prior resident / DMA command):

| slot | code | prior_resident | ctrl (VRAM-write+DMA) |
|---:|---:|---:|---|
|0|0x0001|0x0000|0x40000082| |1|0x0001|0x0000|0x40800082| |2|0x0001|0x0000|0x41000082| |3|0x0001|0x0000|0x41800082| |4|0x0001|0x0000|0x42000082|
|5|0x003A|0x0000|0x42800082| |6|0x003C|0x0000|0x43000082| |7|0x003D|0x0000|0x43800082| |8|0x003E|0x0000|0x44000082| |9–14|0x002A|0x0000|0x448…0x470| |15|0x0039|…| |16|0x0048|…| |17|0x0046|…| |18–23|0x002A|…| |24|0x0039|…| |25|0x0049|…| |26|0x0047|0x0000|0x4D000082|

Proven directly from `totalcycles`-stamped debugger events (not source construction):
- **tile-DMA trigger count == worklist count** (27 == 27; run-wide 124 triggers).
- **every tile DMA is 64 words** — length is programmed by the fixed immediates `0x9340`/`0x9400` (reg 0x13=0x40, reg 0x14=0x00 → 0x0040 = 64 words) at `0x723F8`/`0x723FC` for every entry (disasm-confirmed; not per-entry-variable).
- **no entry skipped, no extra DMA** — loop bound = count; trigger count equals count each frame.
- **every trigger carried the VRAM-write+DMA command bits** (`ctrl & 0x40000080 == 0x40000080` for all 124).
- **every trigger had `prior_resident != required code`** (a real change) — cold entries here show prior_resident=0x0000.
- **residency changes only after the DMA:** 124 `TILE_RESIDENT_AFTER` events == 124 triggers, and for every one `resident-after[slot] == required code` (read at `0x072462`, after the DMA trigger at `0x072452`). No pre-DMA residency update observed.

## 4. SAT parity vs Build 0140 (direct dump compare)
Both builds share `staged_sprite_sat = 0xFF6188` (it precedes the Build 0141 BSS insertion). At settled `2/2/6` (`active=0x20`), the full 640-byte staged SAT was dumped from each build via the debugger `save`:
- `sat_0140_226.bin` and `sat_0141_226.bin` are **byte-identical** — SHA256 `45faaa8af92da1fc44598758eca82799dcc8bde82da2d3b0f9fecb87c54e0c10` for both; `cmp` = 0.
- **Link chain / ordering identical** — the dump's word1 fields are `0x0501, 0x0502, 0x0503, 0x0504…` (link 0→1→2→3→4…), the same in both builds.
- **active count / SAT-DMA words match for all three states:** `0/1/0`→23→92, `0/1/2`→23→92, `2/2/6`→32→128 (identical to Build 0140). Other observed active/word pairs: 27→108, 39→156, 31→124 (transition frames).

**Build 0141 SAT matches Build 0140 exactly** (contents, link chain, ordering, word count) — proven by dump, not by source.

## 5. Removed-path proof (stable Build 0141 frames)
- **Worklist count = 0** in every settled `0/1/0`/`0/1/2`/`2/2/6` frame (`TILE_COMMIT_ENTRY count=0000`).
- **The fixed 80-slot residency scan does not execute** — it is replaced; with count=0 the commit takes the `beq` zero-entry path and **0 `TILE_DMA_TRIGGER` events** occur in stable frames (all 124 triggers are in transition frames).
- **`.Lvcs_clear_dirty` does not execute** — it is removed from the build; no such PC/routine exists (SAT DMA `0x7246C` is followed directly by the loop `rts`; there is no cleanup loop). Confirmed absent in the disasm and in the event stream.
- **SAT DMA still executes once per frame** — 702 `SAT_DMA` events over 702 commits.

## 6. Coverage-constant audit
`git diff tools/translation/postpatch_startup_rom.py tools/translation/verify_canonical_rom.py`:
- **Functional change (both files): exactly `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17D680 → 0x17D688`** — as expected; `CANONICAL_OPCODE_REPLACE_COUNT` unchanged (133).
- **Transparency note:** each file's diff also contains **two documentation comment lines** describing the Build 0141 change, consistent with the file's existing per-build comment convention (e.g. the pre-existing `# Build 0113 …` line). These are documentation-only (no logic change). Under the strictest reading ("only change is the constant"), these comment lines are additional; they are flagged here for Tighe's decision. **No file was edited in this evidence task** — the diff is exactly the Build 0141 implementation state. This does not affect correctness (the ROM built and runs correctly).

## Known visual result (per Tighe's BlastEm; not addressed here)
Black strip much thinner but a thin line remains; frontend progresses; extra upper-left/upper-right zeros, zero high score, incorrect colors, imperfect positioning, and the stray upper-left sprite all remain. Consistent with this change: the ~91% DISPLAY_OFF reduction thins the strip (to ~2.9 lines), and none of the listed items are touched by the tile-DMA worklist (SAT is byte-identical). No fix attempted.

## Evidence files
`build0141_debug.cmd`, `frames.lua`, `mame_stdout.log`, `mame_stderr.log`, `lua_frames.log`, `ev_extract.log` (3056 EV cycle events), `native_debug_trace.log.gz` (full native trace, gzipped 3.9 MB from 219 MB), `sat_0140_226.bin` / `sat_0141_226.bin` (byte-identical SAT dumps), `sat140.cmd` / `sat141.cmd` / `exit_lua.lua`.

## Unresolved / limitations
None material. The DISPLAY_OFF interval has occasional larger-frame outliers driven by unrelated PC080SN tilemap commits (documented above); the sprite-attributable stable interval is 1426 cycles. Screenshots via `-snapshot_directory` were configured but headless snapshotting is unreliable; visual confirmation is Tighe's BlastEm role (already reported).

## Outcome A
Exact DISPLAY_OFF intervals (1426 cyc, ~91% reduction), direct per-entry tile-DMA evidence (count==triggers, 64-word DMAs, post-DMA residency), byte-identical SAT parity, removed-path proof, coverage audit, and valid MAME execution proof are complete. No implementation, source, ROM, build, tool, branch, commit, or pipeline change was made in this evidence task.
