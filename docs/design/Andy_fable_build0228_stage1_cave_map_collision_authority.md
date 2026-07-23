# Andy/Fable — Stage 1 Cave Map/Collision Authority (investigation; **STOP — Build 0228 NOT consumed**)

**Date:** 2026-07-20 · **Mode:** Andy/Fable (Opus) · **Evidence:** `states/traces/build0228_stage1_cave_map_collision_authority_20260720_221041/`
**Recovered state:** counter 227, rolling = Build 0227 (`5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`, 1,584,068) byte-identical. opcode 216. coverage 0x182BC4. Builds 0223–0227 preserved. JSON re-hashed this task: address_map `2556e6f2160716bb…`, patch manifest `f62a412449f81b83…`, spec `318f3469b1d53f14…` (no fixed offsets).
**Build status: NO numbered build produced. Counter stays 227. Nothing patched.**

## Why STOP (honest boundary)
Three parallel arcade-disassembly agents were killed mid-run by the account monthly-spend limit; their partial leads are folded in below. Continuing economically with local MAME (not spend-limited) I **localized the blocker precisely and confirmed a real collision-producer divergence**, but did **not** reach a *proven patch-safe boundary* for the progression blocker. Patching now would be speculative (forbidden). This documents the narrowed blocker and the exact next capture.

## Central proven finding: the cave is DOWNSTREAM-BLOCKED by a Stage-1 progression stall
Every user-reported cave symptom (wrong cave tiles, missing destructible cover, pit resets, broken rope/lava) is **downstream of one blocker**: **Genesis Build 0227 Rastan cannot progress past the first outdoor pit, so the cave is never reached.** Matched runtime (both local MAME):

- **GENESIS 0227** (hold-right + periodic attack/jump, 6500 frames): scroll X **oscillates 0x407E↔0x4339 and never advances**; player mode word (arcade 0x10D0E8 → Genesis **0xFF10E8**) cycles walk-states 1→2→3, then at scroll **0x4339 goes to mode 7** and the camera **snaps backward** to 0x407E — repeatedly; occasional **mode 8 (death) → respawn** to an early checkpoint. Tileset stays 1 (outdoor); source pointer never leaves the outdoor family (0xD31C–0xF31C); **cave tileset 3 / source ≥0xFB1C never reached.** Snapshot at the stall (`stuck227/0000.png`): Rastan at the edge of a pit/gap, mode 7.
- **ARCADE Rastan** (same input envelope): walks freely **past this point to the cave/rope area** — snapshot `arc/0003.png` shows the **green vertical rope**, the **pit drop into the cave**, the dark cave wall, and brown rocky terrain. (Its checkpoint had advanced to the rope area after a death.)

So: arcade progresses with hold-right; Genesis stalls at the first pit (mode-7 bounce). **This stall is the reset/relocation symptom and the reason the cave tileset plumbing from Build 0218 is never exercised.**

## Confirmed collision-producer divergence (matched dumps) — refines KF-067
Matched flat-ground collision-map dumps (ARCADE 0x10DE00 vs GENESIS 0xFF1E00, rows 36–44, `acoll.txt`/`gcoll.txt`):

| | ground-surface markers (0x3400/0x3A00) | pattern | solid floor 0x0001 | rows 36–37 |
|---|---|---|---|---|
| **Arcade** | **row 38** | **contiguous** across columns | rows 40+ | 0000 |
| **Genesis 0227** | **row 39 (one row / 8px LOWER)** | **sparse: 2-of-every-4 columns** (0000 0000 3A00 3A00…) | rows 40+ (matches) | spurious **0x0020** |

Two concrete `genesistan_stage_bg_collision_column` (tilemap_hooks.s) divergences:
1. **Row shift +1 (8px low)** — matched-evidence confirmation of **KF-067** at the producer, not just a rendering symptom.
2. **Sparse surface markers** — Genesis writes the ground-top marker to only half the columns (structural; identical pattern at two different scroll positions), where the arcade writes them contiguously. Plus spurious 0x0020 in the rows above.
The **solid floor (rows 40+) matches** in both, which is why Rastan stands on flat ground normally — so these divergences are **not yet proven** to be the mode-7 pit-stall cause. Naming them the cause and patching would be speculative. **KF-067 explicitly forbids blindly moving the row** (it is compensated at the lizard rendering boundary; any change needs a joint player/enemy/terrain retune with matched proof).

## First-divergence questions — status
1. **Cave descriptor family reached?** NO — Genesis never leaves outdoor source 0xD31C–0xF31C; the attr=0x0003 / 0xF91C·0x1011C cave family is never selected because the camera/producer never advances past the pit. The Build 0218 split-residency is correct-by-construction but **unexercised**.
2. **Wrong brick cave cause?** Not reachable to observe in Genesis; unproven. Cannot be attributed to tileset selection until the cave is reached.
3. **Destructible cover ownership?** UNPROVEN (cave unreachable). Prior agent confirmed **no Genesis code** handles a destructible cave-cover (neither tilemap mutation nor object) — so if the arcade owns it, the port currently omits whatever produces it. Owner (PC080SN map-mutation vs PC090OJ object) still to be proven from arcade code.
4. **Reset/relocation cause?** Partially classified: the dominant one is the **mode-7 bounce at the first pit** (camera cannot advance, snaps back); a secondary is **mode-8 death→respawn**. Whether mode 7 is fall/blocked/hazard is unproven (agent killed before decoding it). Not a stack/PC corruption (arcade code runs cleanly; no impossible-PC).
5. **Rope ownership?** UNPROVEN (unreachable). Prior agent confirmed **no rope-specific Genesis code exists** — the rope is whatever the arcade produces through the generic BG/FG/collision path. Arcade agent lead: **player mode 6 skips floor/side collision at arcade 0x05385A → jumps 0x053896** = strong rope/climb-state candidate; state dispatcher at 0x051A32 (cmpi 9/6/4); mode 8 death written at 0x053E0C / 0x0553E6. Unverified.
6. **KF-067 revisit:** confirmed at producer level (above). Not touched — needs joint retune with matched proof.

## Arcade authority leads captured before the spend-limit kill (unverified, for the next session)
- Descriptor table **arcade ROM 0x03951C**, 6-byte entries (attr.w + source.l), indexed at a **12-byte stride** by surrounding code; a descriptor pointer is cached near **0x10D0FC**; progression state candidate near **0x10D386** (both read **constant 0/3** in runtime here — so those two specific addresses are NOT the live progression counter; the real one is still unidentified).
- **No death/drowning/collision *hooks* on the Genesis side** — that logic runs as **native arcade code** on the 68000; the Genesis 0x03xxxx hooks are all input/palette/sprite/text video translation. So the reset/rope/hazard behavior is arcade-native and must be understood from the arcade disassembly + matched WRAM, not from Genesis hooks.
- Player **mode word = arcade 0x10D0E8** (Genesis 0xFF10E8): modes 1/2/3 walk, 4 jump, 6 rope/climb-candidate, 7 (Genesis-specific at the pit), 8 death.

## Implementation
NONE. No patch-safe boundary proven for the progression blocker. No coordinate-triggered cave loader, no forced scene/coords, no collision-row move, no compatibility-middleware restore — none attempted.

## Exact next capture required (the narrow blocker)
The blocker is the mode-7 pit stall. To reach a patch-safe boundary WITHOUT burning spend on unattended scripts that cannot pass the pit:
1. **Interactive matched runtime — Tighe plays** the SAME sequence in both, while a lua logs per-frame: player mode (0x10D0E8/0xFF10E8), player world X/Y (address still to be identified — scan the WRAM delta around 0x10D0E8 while walking), camera/scroll, the live descriptor/progression counter, and the collision words under Rastan's feet at the pit:
   - **ARCADE**: walk to the pit, fall/drop into the cave, land, cross/climb the rope. Capture the mode transitions and collision reads at the pit and at cave-entry.
   - **GENESIS 0227**: same sequence; capture where it diverges (the mode-7 bounce) with the matched collision reads.
2. Decode **arcade mode 7** and the code that reads the collision at the pit edge (arcade 0x05385A region and callers of FUN_00053A2E) to prove whether the pit stall is (a) the sparse/low collision surface, (b) a scroll clamp keyed off the unidentified progression counter, or (c) a cave-entry trigger the Genesis state never satisfies.
3. Only then patch the proven owner (likely `genesistan_stage_bg_collision_column` for the surface, or the progression-counter feed) as Build 0228.

## Deferred issue inventory (recorded, NOT fixed — kept SEPARATE per instruction)
**Display/timing:** BG can shear/stretch during vertical scroll (separate display-on DMA/scroll-timing investigation). Build 0227 is slightly slower than the fastest N1/N2 iterations; 68k-Counter cycle optimization deliberately held for later.
**Sprite/object/lifecycle:** one unwanted gray fireball/orb persists; killed enemies leave random gray stationary remnants after death (ownership UNPROVEN — may be wrongly-represented death effects, item objects, or palette routes, NOT assumed to be stale SAT); only observed item drop is a gem with WRONG palette; item-drop selection/coverage may be incomplete; the **axe near the cave ceiling is missing**; the **large bat guarding the axe is missing**; only the small bat appears — killable but **green instead of arcade brown**; Rastan's **sword hitbox horizontally misaligned**; enemy→Rastan damage incomplete.
**Cave subsystem (this task, blocked):** wrong brick cave tiles; missing destructible cave cover; pit/cave resets/relocations; rope wrong art + no climb-out + lava death on jump-off. All unreachable until the progression stall is fixed.

## Regression / architecture
No code changed → N1 sprites, N2 planes, display-on, no-bars, coverage, opcode all unchanged from Build 0227. **Architecture compliance: CONFIRMED** (nothing patched; no middleware restore, no forced state). **STOP: YES** — narrow blocker documented; exact next capture specified; Build 0228 not consumed.

## USER MUST VERIFY / DO (Tighe)
The next step genuinely needs you: play **Build 0227** (and arcade Rastan) to the cave/rope with an interactive MAME capture running the logging lua (I can prepare it), so I can capture matched player-mode + collision + progression state at the pit and cave-entry. Automation cannot pass the pit. Confirm on hardware that the pit stall / backward reset reproduces as captured.

---

## Producer analysis (2026-07-21, static; no MAME) — arcade 0x0559B2 / 0x055A14 vs genesistan_stage_bg_collision_column

**Traces preserved:** Genesis `rope_lava_run.txt`, arcade `arcade_rope_run.txt` (+ arcade_snaps/0026.png = Rastan climbing the arcade rope, mode 5).

### 1. Arcade producers (from linear_disassembly)
Two arcade column producers write BOTH the visible tile AND the collision word from the same block, to `collision = 0x10DE00 + ((cwindow_dest - 0xC08000) >> 1)`:
- **BG / pass 0 — 0x0559B2** (driver 0x055968, runs when `*(a5+0x10A8)==0`): `collision = *(block + 20 + row*8 + strip*2)`; `tile = *(block + 0 + row*8 + strip*2)`; dest advances +256 B/row.
- **FG / pass≠0 — 0x055A14** (driver 0x055990): `collision = *(block + 20 + stripT*8 + row*2)` where `stripT = (*(a5+0x10A8)==2) ? strip : (~strip & 3)` — i.e. **row and strip roles are SWAPPED vs the BG variant, plus a strip complement.** It also writes collision to 0x10DE00.
- Block pointers: descriptor list at **0x10D000 (=a5+0x1000)**; block-ptr table **0x10D040** rebuilt by **0x055904** as `block = *(descriptor+2)`.

### 2. Genesis side
`genesistan_stage_bg_collision_column` replicates **only the BG/0x0559B2 variant** (`*(block+20+row*8+strip*2)`, RAW strip, same dest formula, `&0x1FFF`). It does **not** implement the FG/0x055A14 collision path (swapped indexing + strip complement).

### 3. Row/column correspondence (user point 2)
Collision ring col = `(cwindow_dest-0xC08000)>>1` (word index) — identical formula both sides, and the arcade drives `cwindow_dest` identically on both, so **ring columns correspond by construction**; the rope landmark appearing at the same ring cols (36–55) in both captures confirms the scroll phases were compatible. World-cell identity beyond that depends on matched scroll phase (evidenced, not independently proven). **KF-067 row +1 is NOT explained by this producer** (row stride 256 B = 1 collision row on both sides); the 8px displacement must arise on the READ side or a base offset — unresolved here, do not fold into this fix.

### 4. Provenance of 0x0106 / 0x049C / 0x04A0 / 0x0002 (user point 3) — NOT "garbage"
These are **sequential/structured** (`0x049C 0x049D 0x049E 0x049F`, `0x0106 0x0107`), i.e. consistent with **valid tile/block data read at the WRONG index**, exactly the "valid data in the wrong format/location" the user flagged — NOT random garbage, and **0x0002 is NOT singled out as the hazard.** The BG-vs-FG index swap (`row*8+strip*2` vs `stripT*8+row*2`) is a concrete mechanism that would make the Genesis read land on tile-adjacent cells of the block, yielding tile-code-like words where the arcade's correct variant yields clean `0x0006/0x0008`.

### 5. Camera/scroll semantics (user point) — EARLIER LABEL CORRECTED
- **0x10C200 is NOT the camera.** It is incremented `+1` per frame at **0x03A7B0** (a frame/timer counter); the earlier `camera−worldX≈0xF0` was **coincidental** (both advanced ~1/frame during that specific ground walk) and broke on the rope (worldX became rope-relative while 0x10C200 kept counting). Do not use it as a camera.
- **Real scroll (0x055AB4 committer):** `*(a5+0x10EE)`→`0xC20000` and `*(a5+0x10B0)`→`0xC20002` (FG plane X/Y); `*(a5+0x10EC)`→`0xC40000`, `*(a5+0x10AE)`→`0xC40002` (BG plane); 0x10EE is fed from 0x10B0 (0x055B28). So the value my arcade logger labeled `worldY=0x10D0EE` is actually the **FG scroll register value** — re-label required before any alignment math.

### 6. First divergence + patch-safe boundary — CANDIDATE, not yet proven
Strongest candidate: **the Genesis replicates only the BG collision producer; the cave/rope columns are (likely) produced by the arcade FG producer 0x055A14 with its swapped `stripT*8+row*2` indexing + strip complement, so the Genesis collision at those columns is read with the wrong index → tile-like values → lethal read.** Boundary would be `genesistan_stage_bg_collision_column` / an FG collision path. **NOT PROVEN** because it requires the runtime `*(a5+0x10A8)` pass value and the descriptor/block pointer AT the rope columns.

### Shared-root (user point 5) — SUPPORTED, not established
Tile and collision come from the same producer+block, so a wrong block → both wrong (supports shared root). But collision also has the BG/FG index-variant issue independent of tiles, and tiles have a separate residency/LUT path. **Do not record shared root as fact.**

### What ONE more capture must prove (user point 4 — dynamic read)
The existing trace dumped the collision MAP, not the READ the lethal path performs. Needed: a **read watchpoint on the Genesis collision region (0xFF1E00–0xFF3E00) armed across the jump→mode-8 window**, logging (exact address, value returned, reader PC). Plus, at the rope columns: `*(a5+0x10A8)` (=0xFF10A8) pass value, the descriptor at 0x10D000/block ptr at 0x10D040, and the FG scroll (0x10D0EE/0x10D0EC) — to confirm which producer owns the rope columns and prove the exact cell/index. Only then is the boundary patch-safe.

**STOP: continue investigation; Build 0228 NOT consumed; counter 227.**

---

## CORRECTIONS + CODY HANDOFF (2026-07-21) — supersedes all rope/causality claims above

**This section is authoritative. Earlier statements that conflict with it are retracted.**

### Accepted state
- Rolling/accepted: **Build 0227**, SHA `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`, size 1,584,068, **counter 227**. No patch. Build 0228 NOT consumed.

### Preserved evidence (do not overwrite)
All under `states/traces/build0228_stage1_cave_map_collision_authority_20260720_221041/`:
- Traces: `rope_lava_run.txt` (Genesis play), `arcade_rope_run.txt` (+`arcade_snaps/0026.png` = arcade rope climb), `rope_causality_run.txt` (Genesis read/write causality).
- Loggers: `rope_lava_logger.lua`, `arcade_rope_logger.lua`, `rope_causality_logger.lua`.
- Launched (interactive, user-driven): `mame genesis -cart dist/rastan-direct/rastan_direct_video_test_build_0227.bin -video soft -sound none -skip_gameinfo -nomaximize -homepath build/mame/home -snapshot_directory <snaps> -autoboot_script <logger>`. Arcade: `mame rastan -rompath roms -video soft -sound none -skip_gameinfo -nomaximize -autoboot_script <logger>`. (OpenGL auto-exits ~23s on the arcade driver here; use `-video soft`.)

### Corrected runtime-PC mappings (via address_map.json relocation_delta=0x200; segments carry no arcade_start, and shift_deltas exist — treat as APPROXIMATE, Cody must verify against segments/shift_deltas, NOT assume fixed -0x200)
- Writer `genesis 0x070798` = **Genesis hook `genesistan_stage_bg_collision_column`** (0x0706EE..0x0707B6 per out/symbol.txt); UNMAPPED to arcade (wrapper region).
- Reader `genesis 0x053D6E` → arcade ~0x53B6E; `0x053C90`→~0x53A90; `0x053CF8`→~0x53AF8; `0x053FA6`→~0x53DA6; `0x041494`→~0x41294; `0x0518A2`→~0x516A2. These are native arcade player/collision code running relocated.

### Corrected source-block calc (runtime A2 − 0x200 = arcade ROM offset)
- A2=0x1200 → arcade **0x1000** (normal ground): `+0..+31 = 0x0020`(×16); **`+32 = 0x00FF`, `+34 = 0x0000`**.
- A2=0x257C → arcade **0x237C** (rope): `+0..+31 = 0x0492..0x04A1` (sequential); **`+32 = 0x0001`** (≠0xFF), `+34 = 0x0000`.
- A2=0x1B70 → arcade **0x1970** (rope): `+0..+31 = 0x0110,0x0132,0x0261…0x0260,0x0107`; **`+32 = 0x0000`** (≠0xFF).
- (My earlier dump at 0x1200 was the WRONG offset and I misread 0x00F1 as 0x00FF — retracted.)

### Producer logic (from genesistan_stage_bg_collision_column + arcade 0x0559B2)
`if *(block+32)==0x00FF: collision=*(block+34)  else: collision=*(block+20+row*8+strip*2)`. Writer for cells in this trace ran with `sel(0xFF10A8)=0` (the column-streaming / 0x0559B2 variant, which the Genesis hook mirrors).

### PROVEN
1. During DEATH#1 (worldX=0x0116, the user's "jump straight up on the left of the rope"; user confirms enemies deal NO damage in Genesis, so death is collision-driven, not enemy).
2. At **F2124** native reader `genesis 0x053D6E` read collision cell **0xFF3258** (= collision row 40, col 44) value **0x049C**; other rope cells 0xFF2ED8=0x0260, 0xFF2EDA=0x0107 read by 0x053C90/0x053CF8.
3. Last writer of those cells = `genesistan_stage_bg_collision_column` (0x070798) with block A2=0x00257C (arcade 0x237C) / 0x001B70 (arcade 0x1970), sel=0.
4. Those blocks have `+32 ≠ 0x00FF`, so the producer took the `block+20+row*8+strip*2` branch and wrote the sequential `0x04xx/0x01xx` values from that region into the collision map.
5. The arcade collision at the SAME rope cells (arcade_rope_run.txt) is small codes **0x0006 (rows 40-44) / 0x0008 (rows 37-39)**, not these values.
6. **mode→8 first observed at F2135/F2136 — ~11–12 frames AFTER the 0x049C read, NOT one frame.**

### DISPROVEN / RETRACTED
- ❌ "0x049C was the exact read that initiated the death (one frame before)." The gap is ~11–12 frames; **the trace does NOT prove which collision read causes or schedules the mode-8 transition.**
- ❌ "tile-only block" classification — RETRACTED; the original block format and producer semantics are NOT proven (the `+0..+31 = 0x049x` bytes only *resemble* tile codes).
- ❌ "garbage" as a proven property — these are structured/sequential values of unknown original meaning read in the collision role.
- ❌ shared root with the wrong cave-interior tiles — NOT asserted.
- ❌ earlier 0x1200/0x00FF numbers — corrected above.

### SUPPORTED HYPOTHESES (not proven)
- The rope-column collision cells hold `*(block+20+…)` values from blocks whose `+32≠0xFF`, and the arcade at those cells has small collision codes — so the block/descriptor handed to the producer for the rope columns is likely wrong (or lacks the `+32==0xFF` marker) vs the arcade.

### UNANSWERED (blockers before any fix)
- **Which collision read actually causes/schedules the mode-8 write** (11–12 frame gap; not tied to a specific read yet).
- Whether the **arcade uses a different block/descriptor** for the rope columns (arcade A2 was NOT captured) → descriptor-selection divergence vs producer/handling divergence.
- The **original block format** and the meaning of `+32/+20/+34`, i.e. proof of the producer's intended semantics.

### EXACT NEXT INVESTIGATION FOR CODY
1. Instrument a single Genesis Build 0227 run (user drives the rope death) capturing, with one monotonic event counter:
   - every WRITE to player mode **0xFF10E8**: writer runtime PC, old mode, new mode, event#.
   - every READ from **0xFF1E00–0xFF3DFF**: address, value, access width/mask, runtime reader PC, event#.
   - relevant registers (A0–A3, D0–D2, PC) at each collision read AND at the mode write.
   - the LAST collision read in the same native control-flow chain immediately preceding the mode-8 write (walk the event stream backward from the mode-8 write to the nearest collision read on the same code path).
   - existing last-writer provenance for that specific cell (reuse the write-tap map from `rope_causality_logger.lua`).
2. Map EVERY runtime PC through address_map.json **segments + shift_deltas** (not fixed −0x200).
3. Extend `arcade_rope_logger.lua` to record, per collision WRITE at the rope columns, the block pointer **A2** and the descriptor/selector, then one short arcade rope pass — to compare the arcade rope block vs Genesis 0x237C/0x1970 and decide descriptor-selection vs producer divergence.
4. Establish the original block format (what `+0..+31`, `+32`, `+34` mean) from the arcade producer + level data before classifying the values.

### CONDITIONS REQUIRED BEFORE ANY PATCH / BUILD 0228
- The specific collision read that causes/schedules mode-8 is proven (read→branch/state→mode write chain).
- The arcade rope block/descriptor is captured and compared → divergence classified (descriptor vs producer).
- The block format + producer semantics are proven.
- Only then design the smallest native fix; preserve N1/N2, no DISPLAY_OFF, no mirror restore, no forced state; counter advances to 0228.

---

## CODY CONTINUATION (2026-07-21) — native rope-death chain proven; patch boundary still unsafe

**Status:** Evidence-only continuation from the authoritative `CORRECTIONS + CODY HANDOFF` section above. Build 0228 was **not** produced. Counter remains **227**. No source/spec/ROM/Makefile changes were made.

### Additional traces captured

New evidence directory:

`states/traces/build0228_rope_death_cody_proof_20260721_135322/`

Key files:

- `native_events.log` — reduced native debugger event stream from Build 0227.
- `first_mode8_window_events.log` — event window around the first proven mode-8 write.
- `arcade_rope_producer_events.log` — original arcade rope producer write events.
- `arcade_rope_producer_reduced.log` — reduced rope-band producer events.
- `cody_rope_death_proof_summary.md` — compact summary of the evidence below.

### Address-mapping discipline

The runtime PCs below were resolved through `build/rastan-direct/address_map.json` segments, not by assuming fixed arithmetic identity.

| runtime_genesis_pc | address-map result | Meaning |
|---:|---:|---|
| `0x0550BE` | `arcade_pc 0x054EBE`, `arcade_copy` | actual `move.w #8,%a5@(4328)` mode writer |
| `0x0550C4` | `arcade_pc 0x054EC4`, `arcade_copy` | post-instruction PC logged by the write watchpoint |
| `0x054F84` | `arcade_pc 0x054D84`, `arcade_copy` | caller-side flag test block |
| `0x054FA4` | `arcade_pc 0x054DA4`, `arcade_copy` | `bsr 0x550AE` when `FF10CE` bit 8 is set |
| `0x053D70` | `arcade_pc 0x053B70`, `arcade_copy` | native collision read of `0x0107` |
| `0x053DD0` | `arcade_pc 0x053BD0`, `arcade_copy` | code-7 compare/read site |
| `0x053FF0` | `arcade_pc 0x053DF0`, `arcade_copy` | post-PC for `FF10CE` bit-8 set helper |
| `0x053FD4` | `arcade_pc 0x053DD4`, `arcade_copy` | post-PC for `FF10CE` bit-2 set helper |
| `0x07079C` | Genesis-only wrapper region | post-PC inside `genesistan_stage_bg_collision_column` |
| `0x0704A4` | Genesis-only wrapper region | `genesistan_hook_tilemap_plane_a` |

Data-pointer conversion remains separate from PC mapping. For example, the Genesis helper's runtime data pointer `a2=0x00003A88` is not a PC and is not resolved through `address_map.json`.

### Proven collision-read to mode-8 chain

The first relevant mode-8 write in this capture was:

```text
EVENT MODE_WRITE cyc=335382730 pc=0550C4 addr=00FF10E8 size=16 data=00000008 post=0002 sr=2700 mode=0002 worldX=0030 worldY=0148 scBG=01A3 flags10CE=0124 flags1132=0018 ptr111C=00FF2DD8
```

The watchpoint reports the post-instruction PC. The actual writer is `runtime_genesis_pc 0x0550BE`:

```asm
550AE: cmpi.w #0,%a5@(64)
550B4: bne    0x550C4
550B6: cmpi.w #0,%a5@(68)
550BC: bne    0x550C4
550BE: move.w #8,%a5@(4328)  ; Genesis-WRAM 0x00FF10E8 player mode
550C4: rts
```

The caller-side native code checks the collision/death flag field before calling the mode writer:

```asm
54F8C: move.w %a5@(4302),%d0  ; Genesis-WRAM 0x00FF10CE
54F90: btst   #9,%d0
54F96: bsr    0x550A0         ; bit-9 path, if set
54F9A: move.w %a5@(4302),%d0
54F9E: btst   #8,%d0
54FA4: bsr    0x550AE         ; writes mode 8 if a5+64/a5+68 are zero
```

The collision read that sets the proven bit-8 predicate is a structured value, but wrong for the arcade rope role:

```text
EVENT COLL_READ_ROPE cyc=335201566 pc=053D70 addr=00FF30DA size=16 data=00000107 mem=0107 masked=07 sr=2700 mode=0002 worldX=0030 worldY=0148 scBG=01A4 ptr111C=00FF2DD8
```

The native code then compares the masked value against collision code `7`:

```asm
53DD0: move.w (%a0),%d0       ; watchpoint reports pc=053DD0 / post-read variants around this block
53DD2: andi.w #0x007f,%d0
53DD4: cmpi.w #0x0007,%d0
53DD8: bne    0x53DF0
53DDC: bsr    0x53FE4         ; sets bit 8 in FF10CE
53DE0: bsr    0x53FC8         ; sets bit 2 in FF10CE
```

The resulting state writes are captured directly:

```text
EVENT PLAYER_STATE_WRITE cyc=335201744 pc=053FF0 addr=00FF10CE size=16 data=00000120 ... flags10CE=0020
EVENT PLAYER_STATE_WRITE cyc=335201812 pc=053FD4 addr=00FF10CE size=16 data=00000124 ... flags10CE=0120
EVENT PLAYER_STATE_WRITE cyc=335203038 pc=053F94 addr=00FF1132 size=16 data=00000018 ... flags1132=0010
```

So the corrected chain is:

`Genesis-WRAM 0x00FF30DA = 0x0107` -> masked collision code `0x07` -> native code-7 branch -> `Genesis-WRAM 0x00FF10CE` bit 8 set -> delayed native flag check at `runtime_genesis_pc 0x054F84/0x054FA4` -> mode-8 write at `runtime_genesis_pc 0x0550BE`.

This supersedes the earlier uncertainty about whether the `0x049C` read was the initiating event. In this capture, `0x0107` at `0x00FF30DA` is the proven collision value that sets the death predicate. The later mode-8 write is delayed, not part of one uninterrupted collision-reader call.

### Last-writer provenance for the proven cell

The last writer to `Genesis-WRAM 0x00FF30DA` before the lethal read was the Genesis-only collision helper:

```text
READ  EVENT COLL_READ_ROPE  cyc=335201566 pc=053D70 addr=00FF30DA data=00000107 mem=0107 masked=07
WRITE EVENT COLL_WRITE_HELPER cyc=304251108 pc=07079C addr=00FF30DA data=00000107 sel=0000 a2=00003A88 d5=00C0A4B4 d7=00020001
```

`runtime_genesis_pc 0x07079C` is the post-PC for the write inside `genesistan_stage_bg_collision_column`, whose source is `apps/rastan-direct/src/tilemap_hooks.s`. The helper is called from `genesistan_hook_tilemap_plane_a`, after the gameplay-scene gate, before the normal BG staging path.

Relevant source locations:

- `apps/rastan-direct/src/tilemap_hooks.s:114` — `genesistan_hook_tilemap_plane_a`.
- `apps/rastan-direct/src/tilemap_hooks.s:131-132` — gameplay call to `genesistan_stage_fg_src_column` and `genesistan_stage_bg_collision_column`.
- `apps/rastan-direct/src/tilemap_hooks.s:376` — `genesistan_stage_bg_collision_column`.
- `apps/rastan-direct/src/tilemap_hooks.s:415-428` — replicated collision value selection: `block+34` when `block+32 == 0x00FF`, otherwise `block+20 + row*8 + strip*2`.

### Original arcade producer comparison

A new original arcade MAME run captured producer-side rope-band writes from the original `rastan` driver. The producer was arcade PC `0x0559EC`, the `0x0559B2` BG/pass-0 collision path, with selector `sel10A8=0`.

Original arcade disassembly at that site:

```asm
559B2: clr.w  %d2
559B4: move.w (%a1),(%a0)
559B6: lea    32(%a2),%a6
559BA: move.w (%a6),%d0
559BC: cmpi.w #0x00ff,%d0
559C0: beq    0x559D4
559C2: move.w %a5@(4298),%d7
559C8: move.w %d2,%d0
559CA: lsl.w  #3,%d0
559CE: lea    20(%a2,%d7.w),%a6
559D8: move.w (%a6),%d0
559EA: movea.l %d7,%a6
559EC: move.w %d0,(%a6)       ; collision map write
```

Representative original arcade rope-band writes from `arcade_rope_producer_reduced.log`:

```text
EVENT ARCADE_COLL_WRITE_ROPE_BAND f=001716 pc=0559EC addr=10F0D8 row=37 col=44 data=00000008 sel10A8=0000 a2=00002648
EVENT ARCADE_COLL_WRITE_ROPE_BAND f=001716 pc=0559EC addr=10F158 row=38 col=44 data=00000008 sel10A8=0000 a2=00002648
EVENT ARCADE_COLL_WRITE_ROPE_BAND f=001716 pc=0559EC addr=10F1D8 row=39 col=44 data=00000008 sel10A8=0000 a2=00002648
EVENT ARCADE_COLL_WRITE_ROPE_BAND f=001716 pc=0559EC addr=10F258 row=40 col=44 data=00000006 sel10A8=0000 a2=00001C14
```

The arcade producer writes small rope collision codes (`0x0008` / `0x0006`) through the BG/pass-0 path. This corrects the earlier strongest hypothesis that the rope death was likely caused by using only the BG producer while arcade used the FG/swapped-index producer. The fresh arcade producer evidence shows the rope-band samples are also BG/pass-0 (`sel10A8=0`) in the original arcade run.

### Classified first divergence

The first proven divergence is therefore not a BG-vs-FG producer-variant mismatch. It is a **source/block selection mismatch at the collision producer surface**:

- Original arcade rope-band producer event: arcade PC `0x0559EC`, `sel10A8=0`, source blocks such as `a2=0x00002648` for row 37-39 small code `0x0008` and `a2=0x00001C14` for row 40 small code `0x0006`.
- Genesis lethal collision cell: Genesis-only helper `runtime_genesis_pc 0x07079C`, `sel=0`, source path `a2=0x00003A88`, wrote `0x0107` into `Genesis-WRAM 0x00FF30DA`.

The structured Genesis value `0x0107` is not classified as garbage. It is valid structured data being used in the collision role at the wrong point in the rope-death path.

### Implementation gate result

**Build 0228 was not produced.** The lethal read-to-mode chain is now proven, and the divergence class is narrowed to collision source/block selection. However, the correction boundary is still not patch-safe because the trace does not yet prove which earlier state creator should have selected the arcade rope blocks for the Genesis helper.

Unsafe fixes explicitly rejected:

- Blanket clamping `0x0107`/`0x04xx` collision values.
- Coordinate-specific rope/lava exceptions.
- Forcing player mode/state or suppressing mode 8.
- Reintroducing unrelated DISPLAY_OFF/PC090OJ/mirror changes.
- Changing the helper to hardcode the sampled arcade blocks without proving the descriptor-selection owner.

The next single missing proof is upstream provenance for the divergent source-block selection: compare the original arcade descriptor/list path that produces `a2=0x00002648/0x00001C14` with the Genesis descriptor/list path that produces `a2=0x00003A88` for the same rope-band columns, including the descriptor list slot, descriptor pointer, second-word/block pointer, selector, strip index, and destination cursor.

### Open / Known Findings impact

- Open issues touched: OPEN-017 / Stage-1 cave/rope/collision progression context; OPEN-001 broad gameplay/rendering context.
- New issues opened: none.
- Issues closed: none.
- KNOWN_FINDINGS impact: no new durable finding indexed yet. Existing KF-073/KF-067 context remains, but this result is still a boundary-narrowing investigation, not a completed architecture finding.

### STOP status

**STOP: YES.** Evidence insufficient for a safe source fix. Build 0228 not consumed; counter remains 227.
