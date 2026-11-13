# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0123 — exact 0548/0549 binary regression + 0563 throne forensics

**Author:** Andy · **Date:** 2026-11-11 · **Type:** READ-ONLY. No production source, generator, ROM, or build
counter changed. Primary evidence = the actual preserved ROMs (disassembled with the project m68k toolchain).
This record CORRECTS specific conclusions in PROMT-ID-0121. 0121/0122 docs are left intact.

Confidence tags: [BINARY] proven by actual ROM bytes; [SRC/DOC] proven by source/spec/report; [INFER] strong
inference; [PENDING-RUNTIME] needs working MAME (wedged in this sandbox).

## Preserved ROMs (actual files)

| Build | Path (`dist/rastan-direct/`) | Size | SHA-256 |
|---|---|---|---|
| 0548 | `rastan_direct_video_test_build_0548.bin` | 3,985,080 | `957633318954f3fd690e488685288118d4e307073fdb19db04f5dbc7ebbfded8` |
| 0549 | `rastan_direct_video_test_build_0549.bin` | 3,985,080 | `3c900760db5f861869cee73c45173b899207c5250ea1215d0cdd36a509c88923` |
| 0554 | `...0554.bin` | 3,985,080 | `a8bb2a579b2ce73e078d958dbec88dd457f2b591f238aeaeae1c2db021cff193` |
| 0560 | `...0560.bin` | 3,985,080 | `59cf10310051d864d4724726e2c1ef9cfb9440fb26bdb513a315cf8d5cba0fb9` |
| 0561 | `...0561.bin` | 4,443,832 | `b08e505eb648ba688a5862c951b97c62ad6b3f9667a4a4b85c0e609022c85565` |
| 0562 | `...0562.bin` | 4,443,832 | `aada40c58760658f2951c372a1897779c2f1d17e5f824fb674bf8724ee39dadf` |
| 0563 | `...0563.bin` | 4,443,832 | `6dd40cba2254a9136613a9e441e818a43cff05405275b175c3d206f9a45ae557` |

No per-build ELF/map/symbol survives; ROMs disassembled directly (Genesis cart, ROM offset == Genesis PC).
Design docs found in `docs/design/` for this era: `Cody_build_0106_*` (PROMT-0106 scroll-clear/C-lite), and the
0104/0105/0106 AGENTS_LOG entries; the 0106 commit series `34b938a7 d616ecfd 624dbea7 14fe7967 e8ae0945
b7a10783` (all 2026-11-07). [DOC]

## Regression 1 — attract crash: exact 0548 → 0549 binary delta

### The only meaningful ROM difference [BINARY]

`cmp` of the two 3,985,080-byte ROMs: **241 differing bytes in exactly 4 clusters**:
- `0x00018E-0x18F` (2 B) — ROM header checksum (noise).
- **`0x055F9D-0x0560C1` (293 B) — the single meaningful code change** (copied-arcade teardown dispatch,
  arcade 0x055F0E/0x055F22/0x055FFA/0x056018 region).
- `0x07521F` (1 B) and `0x3CC8DB` (1 B) — isolated build-number/checksum bytes (noise).

The `$70Bxx` crash region is **byte-identical** between 0548 and 0549. So the crash code did not change; only
what *reaches* it changed.

### The exact instruction that changed [BINARY]

At ROM `0x55FBE`, immediately after the teardown restores the retained next-scene record
(`movew %a5@(5048),%d0 ; movew %d0,%a5@(318)` → `A5+0x13E`):

- **Build 0548:** `6000 0110  braw 0x560d0`   (branch to the common teardown exit)
- **Build 0549:** `4eb9 0007 0b38  jsr 0x70b38` + `4e75  rts`   (call the native scene reseed/publish, then
  return)

`0x70b38` sets the reseed-pending flag at `0xFFB2F3` and `bsr 0x709e8` (the native Plane-A replay / Plane-B
scene reseed).

### The exact crash [BINARY]

Crash PC per Tighe's screenshots is `$70Bxx` (the "$708A4" in the 0123 prompt is a transcription slip; actual
0549 = `$70BA4`). In the 0549 ROM:

- Trap instruction: **`0x70BA2: 4e40  trap #0`** (TRAP #0 = vector `$20`). The stacked/displayed PC is the next
  address, `0x70BA4` — matching the 0549 screenshot exactly.
- Containing function `0x70B4E`: loads a 16-entry descriptor-pointer list from WRAM `0xFF1000 / 0xFF1040 /
  0xFF1080`, and for each entry validates the pointer `%a4` against `[0x0F08, 0x3A00C)` (upper bound =
  `PLANE_B_DESC_TABLE_ARCADE_END`), then rebases `+0x200`. An out-of-range pointer branches to the trap.
- Source label: **`.Lscene_scroll_reseed_rebuild_bad_ptr`** (`apps/rastan-direct/src/tilemap_hooks.s:1072`), the
  descriptor-rebuild guard of `.Lscene_scroll_reseed_rebuild_loop` (source constant
  `PC080SN_DESC_REBUILD_SRC_TABLE = 0x00FF1000`).
- **Failed invariant:** a Plane-B scene-descriptor pointer in the retained reseed source table `0xFF1000` is
  outside the legal arcade descriptor-table range.

### Why 0549 triggers it / why 0548 does not [BINARY + SRC]

0548: the state-8 teardown for attract-demo gameplay entry `braw 0x560d0` — it never ran the Plane-B descriptor
rebuild, so no pointer validation, no trap.
0549: the same teardown now `jsr 0x70b38` → native reseed → `.Lscene_scroll_reseed_rebuild_loop` validates the
`0xFF1000` descriptor list. In the attract-demo context that list is not a valid gameplay Plane-B descriptor set
(the natural-subround path populates it; attract entry does not), so the first out-of-range pointer trips
`trap #0`. The crash code is identical in both builds; only the 0549-added `jsr` reaches it with an attract-time
descriptor table.

### First-bad source change / commit / report [BINARY + SRC/DOC]

**Commit `14fe7967` "Correct subround versus round-clear ownership (0106)" (PROMT-ID-0106).** Its spec hunk adds
the opcode_replace at `arcade_pc 0x055F2A` whose note states it redirects the state-8 natural next-subround
post-teardown to "reuse the existing finite native Plane-A replay and generated Plane-B scene-entry product …
then return exactly as the displaced branch to 0x05602A did." That is exactly the `braw 0x560d0` → `jsr 0x70b38`
+`rts` splice observed in the 0549 binary. The companion `14fe7967` change in `pc090oj_hook_zero_fill_56440`
flipped the gameplay-ownership substate 13↔8; `e8ae0945`/`b7a10783` adjusted descriptor-generation handling and
reseed shared-package context. **The causal binary splice is `14fe7967`'s `0x055F2A` post-teardown publication
cut.** This CONFIRMS 0121's `14fe7967` lead and NARROWS it from "14fe7967 + e8ae0945 + b7a10783" to the single
`0x055F2A` splice.

Part-D answer [BINARY]: YES — a change scoped to the natural next-subround transition (reconstruct the next
gameplay scene after teardown) made the attract-mode gameplay-entry path run the Plane-B descriptor rebuild with
a descriptor table it cannot validate.

### Later builds are the same invariant [BINARY]

`trap #0` in the reseed rebuild, PC drifts only with code layout:

| Build | crash trap addr | displayed PC | function / label | invariant |
|---|---|---|---|---|
| 0549 | `0x70BA2` | `$70BA4` | `.Lscene_scroll_reseed_rebuild_bad_ptr` | 0xFF1000 descriptor ptr out of Plane-B range |
| 0554 | `0x70BAE` | `$70BB0` | same | same |
| 0560 | `0x70BAE` | `$70BB0` | same | same |
| 0561 | ~`$70BD2` | `$70BD4` | same (R2 build shifted +; 4,443,832-byte ROM) | same |
| 0562 | ~`$70BD2` | `$70BD4` | same | same |
| 0563 | ~`$70BCE` | `$70BD0` | same | same |

(0561–0563 trap addresses are the same function shifted by the R2 code growth; exact per-build addresses are
[INFER] from the matching screenshot PCs + identical function shape — not independently re-disassembled for each
here, but the invariant is identical. [PENDING-RUNTIME] exact per-build trap address confirmation if wanted.)

### Correction to the A3=$599DE claim [BINARY] — RETRACTED

0121 claimed `A3=$000599DE` "proved" a scene-descriptor driver band. The faulting invariant at `0x70BA2`
validates **`%a4`** (the descriptor pointer read from `0xFF1000`), not `%a3`. `A3` is not consumed by the
failing check. The `$599DE` value is residue from the retained arcade scene code that ran before the reseed and
is NOT causally relevant to the trap. **Retract the A3 diagnosis; the causally-relevant value is the `0xFF1000`
descriptor pointer in `%a4`.**

### Correction to the trap label [BINARY]

0121 named the trap `.Lscene_scroll_reseed_bad_source_generation`. The actual executed trap is
`.Lscene_scroll_reseed_rebuild_bad_ptr` (the two reseed traps were conflated). Corrected.

### Smallest recommended correction boundary (NOT implemented)

Restrict the `14fe7967` `0x055F2A` post-teardown native reseed/publish to the natural next-subround caller, OR
ensure the attract-demo gameplay-entry path presents a valid `0xFF1000` Plane-B descriptor table before the
rebuild runs. Must preserve the natural R1-S2→R1-S3 reconstruction that 0106 fixed, and must NOT weaken the
`.Lscene_scroll_reseed_rebuild_bad_ptr` invariant (it correctly catches an invalid descriptor table). The exact
attract substate/descriptor-table state is [PENDING-RUNTIME].

## Regression 2 — throne/frontend palette: 0562 → 0563 (PROMT-ID-0119)

### CRAM contents vs name-word routing [SRC]

The 0562→0563 ROM byte-diff (1,269,942 bytes) is dominated by shift-table address drift (0119's generator
Plane-B change + code reflow shifts everything downstream), so it does not localize the writer — this is why the
analysis is source-grounded, not raw-byte-grounded, for the throne.

**Frontend CRAM is unchanged by 0119.** 0119's palette-hook edits (`genesistan_palette_hook_59ad4 / _3ba64 /
_45dae`) only removed the `stage<23` lines that are reached *after* `cmpi.b #1, genesistan_current_scene_id`.
The frontend throne/story runs with `scene_id != 1`, so it takes the unchanged `dest_ok` / full-staging branch;
the removed lines were never on the frontend path. Therefore frontend palette CRAM production is logically
identical in 0562 and 0563. [SRC]

**The regression is NAME-WORD routing.** 0119 forced the Plane-B palette-line index to 2 in the frontend-
reachable producers `genesistan_hook_tilemap_bg_fill`, `genesistan_hook_tilemap_bg_blockcopy`, and the BG
scene-preamble `.Lbg_hook_desc_loop`. These are ungated (no `fg_native_gameplay_owner` / `SCENE_GAMEPLAY_ID`
check, unlike `fg_fill`). Frontend Plane-B name words that previously selected Genesis Line 0/1 (via `attr&3`→
`genesistan_pc080sn_attr_lut`) now select Line 2, which carries no frontend palette → recoloured throne/story.
CRAM stayed the same while the selected line changed `0/1 → 2`: conclusively name-word routing. [SRC/INFER]

### Exact writer of the wrong throne cells [INFER / PENDING-RUNTIME]

The throne/frontend background is produced through the PC080SN BG hooks. Of the three 0119-changed frontend-
reachable producers, the full-screen frontend fill is most consistent with `genesistan_hook_tilemap_bg_fill`
and/or the BG scene-preamble `.Lbg_hook_desc_loop` (both `staged_bg_buffer` writers that run at screen/scene
entry); `bg_blockcopy` contributes for block moves. The precise per-cell writer for the throne figure vs
backdrop is [PENDING-RUNTIME] (MAME wedged; byte-diff swamped). All three are the 0119 changes responsible.

### Which 0119 classification was wrong [SRC]

0119/0121 ultimately identified these three as frontend-reachable, which is correct; the ORIGINAL 0119
classification that labelled `bg_fill`/`bg_blockcopy`/BG-preamble "gameplay Plane-B producers" and forced them
to Line 2 **unconditionally** is the wrong classification. They are shared frontend+gameplay producers and the
Line-2 forcing must be gameplay-gated.

### Smallest recommended correction boundary (NOT implemented)

Gate the Line-2 forcing in `bg_fill` / `bg_blockcopy` / `.Lbg_hook_desc_loop` on gameplay ownership
(`fg_native_gameplay_owner != 0` or `genesistan_current_scene_id == SCENE_GAMEPLAY_ID`, mirroring `fg_fill`), so
the frontend keeps its `attr&3`→Line 0/1 selection while gameplay Plane-B still selects Line 2. Preserve: the
gameplay Plane-B→L2 behaviour 0119 targeted (do not revert the gameplay fix); R1 gameplay unchanged. (Separately,
0563 did NOT fix R2-S1 Layer-B content — the per-round Line-2 palette selection at R2 entry remains open and is
unrelated to this throne routing regression.)

## Confidence summary

- 0548/0549 single meaningful delta `0x55FBE braw→jsr 0x70b38`: **[BINARY]**.
- Trap = `.Lscene_scroll_reseed_rebuild_bad_ptr` at `0x70BA2`, invariant = `0xFF1000` descriptor ptr out of
  Plane-B range: **[BINARY]**.
- Cause = `14fe7967` `0x055F2A` post-teardown reseed splice: **[BINARY + SRC/DOC]**.
- Same invariant 0549–0560 (addresses), 0561–0563 same function shifted: **[BINARY for 0549/0554/0560; INFER +
  PENDING-RUNTIME for exact 0561–0563 addresses]**.
- A3=$599DE causal claim: **RETRACTED [BINARY]**.
- Throne = name-word routing, frontend CRAM unchanged: **[SRC]**; exact per-cell writer: **[PENDING-RUNTIME]**.

No production source, generator, ROM, or build counter changed in this task.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0123`
