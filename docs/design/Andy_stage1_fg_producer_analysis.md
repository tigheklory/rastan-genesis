# Andy — Stage 1 FG Producer Analysis: ROM Model Proven, Hook Boundary Wrong (no build)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** evidence-only analysis.
**No committed source/ROM/build** (an implementation attempt was made, proven non-functional at runtime, and
reverted — see "Implementation attempt & revert").
**Baseline:** `rastan-direct-proposal` @ `4716a4c` (Build 0154 accepted, `5346934`). Build 0154 ROM
`69bd306e1998e892f5fbf451d17e5657d82f7565cacc7c462d2c5b02b3fabfd8`, counter 154. Working tree clean.
**Evidence dir:** `states/traces/build_0155_stage1_fg_plane/`.

## Outcome
**Bounded stop, no build.** The Stage 1 FG **ROM-owned deterministic source model is fully proven** (100% cell
reproduction) and the **generator extraction works** (48/49 codes mapped). But the intended live Genesis hook
boundary — `genesistan_hook_tilemap_plane_a` (`0x070248`), the reimplementation of the arcade FG producer
`0x055968` — **does not execute at Stage 1 on Genesis**, so an FG-staging preamble there never fires and the FG
plane is not populated. The remaining blocker is finding the *actual live* Genesis FG-producer boundary; the
descriptor-producer dispatch path that carries the FG on the arcade is dynamically bypassed on Genesis.

## FG source model — PROVEN (ROM-owned, deterministic, 100% validated)
The arcade FG producer `0x055968` (writer `0x0559B2`) fills the Stage 1 FG plane. The complete chain
(all builders traced: SRC builder `0x0502CC`, descriptor rebuild `0x055904`, writer `0x0559B2`):

1. **SRC table** (`0x10D000`, 16 longs) built by `0x0502CC`: `SRC[seg] = 0x1691C + seg*0x22C0 + stage*0x40`
   (stage index `a5@0x13E = 0` at Stage 1), advanced `+4` per display-column-group by `0x0558C6`.
2. **Rebuild** `0x055904`: `ATTR[seg] = ROM_word(SRC[seg])` (= `0x0003`); block `PTR[seg] =
   PC080SN_DESC_SECOND_WORD_BASE(0x200) + ROM_word(SRC[seg]+2)` → written to `0x10D040` (Genesis `0xFF1040`,
   **already relocated +0x200**).
3. **Writer** `0x0559B2`: per FG cell `code = ROM_word(PTR[seg] + colidx*2 + row*8)`, `attr = ATTR[seg]`, where
   plane row = `seg*4 + row` (seg 0..15, row 0..3) and display column `dcol = group*4 + colidx`
   (group 0..15, colidx = `a5@0x10CA` = `dcol & 3`). The `0x00FF` sentinel at `PTR+0x20` affects only the
   `0x10DE00` work-RAM shadow source, **not** the code.

**Validation:** an offline reconstruction from `build/regions/maincpu.bin` using this exact formula reproduces
the captured arcade FG plane **2048/2048 cells (100%)** for rows 0-31, all 64 columns
(`arc_fgcol.txt`, `arc_full.txt`). The complete Stage 1 FG code set is **49 distinct codes**; **48 have valid
non-blank PC080SN patterns**; the 1 remaining (`0x020`) is the **transparent default** (blank 32-byte pattern),
so mapping it to tile 0 is semantically safe.

## Generator extraction — WORKS
A `collect_runtime_gameplay_fg_tiles` walk of the proven chain (no hardcoded codes) derives the 49 FG codes; the
regenerated global LUT maps **48/49** (only transparent `0x020` unmapped), the gameplay manifest grows 914 → 962,
peak scene stays **1067/1164**, and output is byte-identical across two runs. This part is correct and ready.

## Live boundary — the blocker (why the build did not work)
The intended fix routed the arcade FG producer `0x055968` (address-map: `patched_site → 0x055B68 → jsr
genesistan_hook_tilemap_plane_a 0x070248`) by adding an FG-destination branch to `0x070248` that replays the
16-segment × 4-row writer into `genesistan_hook_tilemap_fg_fill`. Runtime evidence on the built ROM
(`gen_dbg.txt`, `gen_exec.txt`) proves this **cannot work at that boundary**:
- At Stage 1 (`2/2/4`) the FG dest slot `0xFF10A0`, the rebuilt PTR table `0xFF1040`, and the colidx `0xFF10CA`
  are written by **`PC 0x050650` / `0x0505F6`** (Genesis gameplay setup), cycling C-window bases — **not** by
  `0x070248`.
- `genesistan_hook_tilemap_plane_a` (`0x070248`) **never executes**: no store originates from it, and the
  descriptor-producer dispatcher path (`0x055B48 → 0x055B68 → 0x070248`) is dynamically bypassed — the same
  class as the dead raw writers (Build 0154 / KF-040). On Genesis the BG plane is produced by the *strip*
  producer (`0x055C68 → genesistan_hook_itempage_strip_blit 0x716CA`), and the descriptor-producer path that
  carries the FG on the arcade does not run.
- Consequently the FG-staging preamble at `0x070248` never fired: `staged_fg_buffer` stayed at 76/2048 (empty),
  identical to Build 0154. The candidate ROM was **functionally identical to Build 0154** for the FG and was
  reverted rather than shipped as a false "FG restored" build.

## Implementation attempt & revert
The generator FG extraction, the `0x070248` FG preamble, and the paired canonical-coverage bump
(`0x181EE8 → 0x182028`) were implemented and a ROM built cleanly (GATE_PASS, boot guard PASS). Runtime
validation showed **no FG staging** (hook boundary dead). Per the no-broken-build / no-false-claim discipline,
all source, generator, and constant changes were reverted and the numbered ROM removed; the tree is back to the
accepted Build 0154 state. No numbered build was produced.

## Smallest next task (bounded)
Find the **actual live Genesis FG-producer boundary** at Stage 1:
1. Trace `PC 0x050650`/`0x0505F6` (Genesis gameplay setup writing the FG dest slot `0xFF10A0` with C-window
   bases): determine which routine it invokes to fill the FG plane, and whether that routine is `arcade_copy`
   (dead), hooked, or absent — mirror the Build 0154 BG resolution (the BG's live producer was the strip
   `0x055C68`, not the descriptor `0x055968`).
2. Identify the FG analogue of the BG strip producer (or the live call site that should stage the FG), and place
   the proven 16×4 replay there (routing to `genesistan_hook_tilemap_fg_fill` → `staged_fg_buffer` → existing FG
   dirty/VBlank commit), reading the runtime-built `0xFF1040`/`0xFF1080` tables.
3. Then re-apply the (already-correct) generator FG extraction so the LUT/manifest cover the 49 FG codes.

The FG **source model, code set, and generator extraction are done**; only the live producer/hook boundary
remains to be located.

## Confirmations
No committed source/JSON/ROM/build. No manual FG code list (extraction is structural), no hand-edited LUT, no
hardcoded Plane A cells, no forced scroll, no `state==2/3/0` test, no dead-raw-writer patch, no second renderer.
The reverted attempt is documented above for the audit trail. Gameplay sprites (absent) and Exodus (black) were
not investigated.

## Open issue impact
- **OPEN-017:** advanced — the Stage 1 FG source model is now fully proven (deterministic ROM chain, 49 codes,
  100% cell reproduction) and the generator extraction is validated, but the live Genesis FG-producer boundary is
  proven **not** to be `0x070248` (dynamically bypassed). Bounded next task = locate the live FG producer/call
  site (analogous to the Build 0154 BG strip resolution). Not closed; no duplicate.
