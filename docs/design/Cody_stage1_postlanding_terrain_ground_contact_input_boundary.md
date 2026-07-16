# Cody - Stage 1 Post-Landing Terrain / Ground-Contact / Input Boundary

**Date:** 2026-07-14  
**Type:** Analysis-first runtime evidence + documentation only  
**Build context:** Build 0169 candidate, `rastan-direct`  
**Scope:** PC080SN terrain/tilemap staging, ground-contact transition, collision-map relation, and input/control only as it relates to the post-landing no-input walking observation. No source/spec/tool/ROM/build changes. No PC090OJ sprite work.

## Artifact Identity

The annotated screenshot itself does not embed a ROM path/SHA, so its identity cannot be proven from the image alone. The tested artifact for this report is the current Build 0169 candidate on disk:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0169.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `b8c87809fe84650b8c31b7b835469609034fca29cf43a4f2aeb669925acc1634`
- Size: `1,581,480` bytes
- Counter: `169`
- Numbered and rolling ROMs are byte-identical by SHA.

Interpretation: Tighe's screenshot is treated as user-reported Build 0169 visual evidence, while all measured runtime data below is from the exact Build 0169 ROM above.

## Phase 0

Relevant priors loaded:

- KF-010: BG maps to Plane B; FG maps to Plane A.
- KF-011: arcade VBlank owns frame progression; Genesis VBlank is servicing-only.
- KF-015: vertical scroll commit uses `-raw + 8` after Build 0166.
- KF-022: input registers are active-low.
- KF-032: raw PC080SN writes must route through staging.
- KF-038: 32-row Genesis staging can alias longer PC080SN layouts; do not globally change row mapping without design.
- KF-040/KF-041: Stage 1 outside producer and tile-residency history; runtime Stage 1 tile model differs from earlier static model.
- KF-042: Stage 1 pass selector relocation fixed BG-vs-FG selector.
- KF-044: raw WRAM immediates can silently write ROM if not rebased.

Rediscovery hazard HIGH findings touched: KF-010, KF-011, KF-015, KF-032, KF-038, KF-040, KF-041, KF-042. No contradiction detected.

Task classification: EXTENDING, OPEN-017 / OPEN-001 gameplay visual and collision boundary.

Open issues touched: OPEN-017 primary; OPEN-001 context. OPEN-024/PC090OJ intentionally not touched.

## Evidence Inspected

- Screenshot observation from Tighe in the current prompt.
- `states/traces/build0169_bg_collision_candidate_20260714_162157/`
- `states/traces/build0169_ground_contact_alignment_20260714_134458/`
- New evidence-only trace: `states/traces/build0169_postlanding_terrain_input_20260714_175544/`
- `build/pc080sn_tile_vram_lut.bin`
- `build/pc080sn_attr_lut.bin`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `build/genesis_postpatch.disasm.txt`
- `apps/rastan-direct/out/symbol.txt`

## Tighe Visual Observations Recorded

- The annotated screenshot is post-landing, after Rastan has made ground contact.
- Real Genesis freezes instantly when Rastan makes contact with the ground.
- BlastEm and MAME Genesis-driver continue after contact; Rastan becomes stuck in a walking animation with zero user input.
- The automatic movement is not caused by Tighe pressing left/right.
- Exodus locks earlier on the scene palette change and remains deferred as gameplay verifier.
- Exodus VDP/tile-memory view suggests Stage 1 sky/cloud tiles are present in VDP/tile memory; this is used only as tile-residency evidence.
- Directional, jump, attack, and down+attack input appear ineffective.
- The manual GIMP 8-pixel upward layer move is not treated as proof; it remains a visual alignment clue only.
- Bottom crop / cyan-intended area is accepted and deferred.

## Coordinate Mapping

The annotated 320x224 regions were sampled as screen tile columns/rows, then converted to Genesis staged-plane rows using the current scroll convention:

- H scroll approximation: `(raw_x - 16)`
- V scroll approximation: `(-raw_y + 8)`
- Plane column: `((screen_col*8 + hscroll) >> 3) & 0x3F`
- Plane row: `((screen_row*8 + vscroll) >> 3) & 0x1F`

At Build 0169 post-landing frame 820:

- State: `2/3/0`
- Player: `X=0x0020`, `Y=0x0070`
- Mode: `0x0003` at frame 820; later `0x0001` by frame 900 in the sampled MAME run
- Flags: `0x0004`
- Camera/staged scroll: BG/FG raw Y `0x0149`
- Scene ID: `1`
- Staged BG nonzero cells: `2048/2048`
- Staged FG nonzero cells: `2016/2048`

## Region Evidence at Post-Landing Frame 820

### MAGENTA wall region

Sampled screen columns/rows: `(0,0)`, `(1,4)`, `(2,12)`, `(1,22)`.

Build 0169 staged BG cells:

| screen cell | plane cell | Genesis BG word | code | palette line | expected arcade BG code |
|---|---|---:|---:|---:|---:|
| `0,0` | `62,23` | `0x4286` | `0x0286` | `2` | `0x0610` |
| `1,4` | `63,27` | `0x425D` | `0x025D` | `2` | `0x061E` |
| `2,12` | `0,3` | `0x4256` | `0x0256` | `2` | `0x04D2` |
| `1,22` | `63,13` | `0x4278` | `0x0278` | `2` | `0x0576` |

Arcade equivalent BG attr for these samples was `0x0002`; `build/pc080sn_attr_lut.bin` maps attr `0x0002 -> 0x4000`, i.e. Genesis palette line 2. Therefore the sampled cell attribute line is not the first proven palette-line divergence. The sampled tile codes do not match the arcade-equivalent cells, so the visual colour error cannot be reduced to "same tile, wrong palette" from this evidence.

Result: structurally-present wall observation is visually plausible, but sampled data does not prove tile-code equivalence. The first proven divergence is tile/source selection; palette/CRAM content may still be wrong, but not as the first cell-word divergence.

### BLACK sky region

Sampled screen columns/rows: `(2,0)`, `(8,1)`, `(16,2)`, `(24,4)`, `(32,6)`, `(39,7)`, `(12,8)`, `(28,0)`.

At frame 820, Build 0169 staged BG codes were in the lower range:

- `0x025A`, `0x026B`, `0x023C`, `0x025C`, `0x023C`, `0x024F`, `0x025C`, `0x0286`

Arcade-equivalent BG codes for the same sampled visible cells were:

- `0x0602`, `0x05DD`, `0x05F5`, `0x061D`, `0x063E`, `0x077E`, `0x065A`, `0x060C`

Tile residency check from `build/pc080sn_tile_vram_lut.bin` for the expected arcade sky/cloud codes:

- `0x05DD -> 0x01A3`
- `0x05F5 -> 0x01BB`
- `0x0602 -> 0x01C8`
- `0x060C -> 0x01D2`
- `0x061D -> 0x01E3`
- `0x063E -> 0x0204`
- `0x065A -> 0x0220`
- `0x077E -> 0x0344`

Result: sky/cloud tiles are loaded/mapped in the LUT, but the staged BG cells do not reference them. This is a loaded-but-not-referenced failure, not a tile-residency failure.

### YELLOW ground/platform region

Sampled screen columns/rows: `(2,16)`, `(8,17)`, `(16,18)`, `(24,20)`, `(32,22)`, `(39,24)`, `(12,26)`, `(28,27)`.

At frame 820, Build 0169 staged BG codes:

- `0x0281`, `0x026B`, `0x023C`, `0x02EA`, `0x023C`, `0x0285`, `0x023C`, `0x024C`

Arcade-equivalent BG codes for the same sampled visible cells:

- `0x050C`, `0x0521`, `0x0539`, `0x0550`, `0x0575`, `0x058C`, `0x05B1`, `0x05C1`

Tile residency check for expected ground/platform codes:

- `0x050C -> 0x00D3`
- `0x0521 -> 0x00E7`
- `0x0539 -> 0x00FF`
- `0x0550 -> 0x0116`
- `0x0575 -> 0x013B`
- `0x058C -> 0x0152`
- `0x05B1 -> 0x0177`
- `0x05C1 -> 0x0187`

Result: ground/platform tiles are loaded/mapped in the LUT, but the staged BG cells do not reference them. This matches the screenshot's missing-ground region as a tilemap/source-window problem, not missing graphics residency.

### Uncolored mountain band

Sampled screen columns/rows: `(2,8)`, `(8,9)`, `(16,10)`, `(24,11)`, `(32,12)`, `(39,13)`, `(12,15)`, `(28,16)`.

At frame 820, Build 0169 staged BG codes:

- `0x025A`, `0x022C`, `0x0244`, `0x02C3`, `0x0264`, `0x039D`, `0x024C`, `0x025C`

Arcade-equivalent BG codes:

- `0x0650`, `0x04AC`, `0x04C0`, `0x04C8`, `0x04DA`, `0x04E1`, `0x0506`, `0x0516`

Expected arcade codes are resident in the LUT (`0x04AC -> 0x0073`, `0x04C0 -> 0x0087`, `0x0650 -> 0x0216`, etc.), but Build 0169 references different lower codes. The visible mountain band is therefore partial visual similarity, not cell-equivalence proof.

### CYAN crop note

Bottom crop from arcade vertical resolution remains accepted/deferred. No implementation time was spent on it.

## First Proven Terrain Divergence

The first proven terrain divergence is the staged BG/visible tilemap source selection after landing:

- Expected arcade-visible BG cells in the sampled regions use tile codes `0x04AC..0x077E`.
- Build 0169 staged BG cells in the same scrolled visible region use lower tile codes `0x022C..0x039D`.
- The expected arcade sky, mountain, wall, and ground codes are present in `build/pc080sn_tile_vram_lut.bin` with nonzero Genesis tile slots.

Classification: loaded-but-not-referenced / wrong PC080SN source row-window or source-table selection. This evidence does not prove a bounded fix yet, because it does not identify the exact producer source address or table cursor that selected the lower code range.

## BG/FG Ownership

Terrain samples are primarily BG/Plane-B cells. FG/Plane-A samples in the same regions are mostly transparent/blank code `0x0000` with priority/palette artifacts (`0x6000`) and do not explain the missing sky/ground. This points away from a simple FG-vs-BG ownership swap and toward a wrong BG source/window/row selection.

Collision production is now separate from the visual FG_SRC helper in Build 0169. Build 0169 restored the opening collision row/col `6/6` to `0x0000`, falls to `Y=0x0070`, reaches camera Y `0x0149`, and avoids mode `0x0008` in the sampled window. However, collision is not byte-identical to arcade in prior samples (`row/col 36/6`: Build 0169 `0x0020`, arcade `0x0000`). The visible terrain divergence and the remaining collision-content divergence may share a BG source/window root, but this trace does not prove the exact common source.

## Ground-Contact / Hardware-Freeze Evidence

Prior ground-contact traces:

- Arcade: first gameplay at frame 307, falls from `Y=0x0030` to `Y=0x0070`, first grounded flag at frame 400, mode `0x0000`, camera Y `0x0149`.
- Build 0168: first gameplay row/col `6/6` collision `0x0003`, grounds early at `Y=0x0030`, camera Y remains `0x0000`.
- Build 0169: first gameplay at frame 541, row/col `6/6` collision `0x0000`, reaches `Y=0x0070`, first grounded flag at frame 766, camera Y `0x0149`, no mode `0x0008` through frame 1120.

New Build 0169 post-landing trace:

- Frame 820: state `2/3/0`, player `0x0020/0x0070`, mode `0x0003`, flags `0x0004`, camera `0x0000/0x0149`.
- Frame 900: state still `2/3/0`, player still `0x0020/0x0070`, mode `0x0001`, move/state field `0x0084`, camera X increments to `0x0001`.

Real Genesis hardware freeze is user-reported and not reproduced in MAME in this trace. No contact-time VDP/DMA/SAT hazard is proven here. Treat real-hardware freeze as unresolved and requiring hardware-side or strict-target timing evidence.

## Input / Control Evidence

The input helper was exercised in six MAME Genesis-driver runs after landing:

| input case | frame 820 shadow bytes `6180/6181/6182/6183` | frame 900 player state |
|---|---|---|
| zero | `FF/FF/FF/FF` | mode `0001`, move `0084` |
| right | `F7/FF/FF/FF` | mode `0001`, move `0084` |
| left | `FB/FF/FF/FF` | mode `0001`, move `0084` |
| jump | `CF/FF/FF/FF` | mode `0001`, move `0084` |
| attack | `BF/FF/AF/FF` | mode `0001`, move `0084` |
| down+attack | `BD/FF/AF/FF` | mode `0001`, move `0084` |

Interpretation:

- The Genesis helper writes distinct active-low input values into the intended shadow bytes.
- Static disassembly shows code reads the shadow addresses, not raw unmapped arcade input addresses: `0x3A690`, `0x3A6A2`, `0x3A6A8`, `0x3A978`, `0x3A97E`, `0x3A9B8`, `0x3AB1A`, `0x3AD96`, `0x3AE04`, `0x3AE94`, `0x3AEB2`, `0x3AEBC`, `0x3AEFE`, `0x3AF1C`, `0x3AF26`.
- The sampled player mode/move outcome after landing is identical across zero/right/left/jump/attack/down+attack.

Input/control classification: **E — movement is automatic from the post-landing/player-state transition, not from user directional input**. A/B/C are not supported by this trace: the helper writes distinct values, static code reads the shadow addresses, and active-low polarity is consistent with KF-022. D remains adjacent, but E is the narrower classification because the same mode/move transition appears with zero input.

Limitation: MAME's generic read tap did not capture the shadow-address reads in this script, so runtime PC-read evidence is static+state-correlated rather than direct execute-tap proof. This is sufficient to reject "helper did not write" and "all inputs identical," but not sufficient to patch input.

## Primary Answers

1. Are sky tiles loaded but not referenced? **YES.** Expected arcade sky/cloud codes have nonzero LUT slots, but Build 0169 staged BG references lower wrong codes.
2. Are ground/platform tiles loaded but not referenced? **YES.** Expected arcade ground/platform codes have nonzero LUT slots, but Build 0169 staged BG references lower wrong codes.
3. Is the left wall structurally correct but using wrong palette/attribute bits? **Not proven.** Sampled wall cells use palette line 2, consistent with arcade attr `0x0002 -> 0x4000`; sampled tile codes do not match arcade-equivalent cells.
4. Is Genesis staging the wrong PC080SN source rows/window after landing? **YES, strongly supported.** The visible sampled cells point at a lower code range than arcade-equivalent visible cells while expected tiles are resident.
5. Is BG/FG pass ownership wrong? **Not as a simple swap.** Terrain is BG/Plane-B in both sampled evidence sets; FG is mostly blank/transparent. The issue is likely source/window/row selection within the BG terrain path.
6. Is the collision map produced from the same wrong terrain source/pass? **Partially unresolved.** Build 0169 moved collision to BG-pass ownership and fixed the early fall/contact boundary, but remaining collision mismatch may share the visual source/window problem.
7. Does ground contact trigger a VDP/DMA/SAT/timing hazard on real Genesis? **User-reported freeze yes; mechanism not proven.** MAME does not reproduce it here.
8. Is input truly not reaching player logic? **Input helper reaches shadow state; player response does not change.** Classification E: automatic movement from landing/player-state transition.

## Build Decision

No Build 0170 was produced. The evidence proves a terrain divergence class, but not the exact bounded source pointer/row/window write to change. Per the state-causality rule, the next implementation must first prove which earlier code chooses the wrong BG source/window that yields `0x02xx/0x03xx` visible codes instead of arcade-equivalent `0x04xx..0x07xx` codes.

Recommended next narrow task: trace the Stage 1 post-landing BG terrain producer from scene entry through the sampled visible cells, logging source pointer/block/strip/row for cells that currently stage `0x025A/0x026B/0x023C/...` and compare against the arcade source that produces `0x0602/0x05DD/0x050C/...` for the same scrolled visible cells.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-001 context.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: real Genesis freeze mechanism, PC090OJ sprites/OPEN-024, D00298, Exodus as verifier, bottom crop, broad PC080SN rewrite, input patching.

## KNOWN_FINDINGS Impact

Option A — no new finding indexed. The durable mechanism is narrowed but not fully pinned to an exact producer/source-write yet.

## STOP

STOP triggered: YES for implementation/build. Evidence proves loaded-but-not-referenced/wrong BG source-window behavior, but the exact source pointer/row/window fix locus is not proven.
