# Andy — PC080SN Arcade Producer → Genesis Ring-Plane Contract (Phase 2)

> **⚠️ HISTORICAL RESEARCH/BUILD RECORD — superseded for arcade facts.**
> The canonical, address-faithful arcade publisher and **layer-ownership** model now lives in **`docs/arcade_reference/pc080sn/`** (README, address_index, core_publishers.c, core_publishers_assembly.md, unresolved.md). Where this document uses "BG/FG" labels or implies the core publishers write `0xC08xxx` generically, or that only `0x0559B2` produces collision, **the canonical reference is authoritative**: the gameplay core publishers (`0x055948/0x055968/0x055990/0x0559B2/0x055A14`) write **`pc080sn_tilemap1_0xC08000`** and **both** cell producers emit one collision store each at `0x10DE00`; `0x055E54` is one proven `pc080sn_tilemap0_0xC00000` cursor setup, with the complete tilemap-0 producer set unresolved. This file is retained for its build/decision history (0236/0238 etc.), not as the arcade source of truth.

**Date:** 2026-07-24 · **Mode:** research only — NO source/ROM/tool/spec/hook/counter change (verified at end). Baseline Build 0235 (`9aff0b11…`). Evidence: arcade Ghidra `linear_disassembly.tsv` + `call_graph_edges.tsv` (static). **Matched runtime traces were NOT run this session** — the specific runtime confirmations required before Build 0236 are listed in §12/§13.

---

## 1. Recovered arcade producer call graph
```
VBlank IRQ 0x03A008 ──(state 2..3)──► 0x041F30  per-frame gameplay tick
   0x041F30: jsr 0x55AB4 (scroll commit) ; bsr 0x45D72 (asset-DMA seq) ;
             jsr 0x5988C ; jsr 0x59882 ; bsr 0x47004 ; bsr 0x41F5E (sprites) ;
             (a5@0x2A2==2? 0x45DFA) ; bsr 0x41DAE (sprites)

STREAMING TRIGGERS (camera boundary crossing):
  horizontal:  0x055822 ─┐   vertical: 0x05572E→0x055788 ─┐   init: 0x050434 ─┐
  (0x0556FC)  ───────────┴──────────────────────────────┴─────────────────────┴──► 0x055948
  0x055948  publish ONE column: (a5@0x10A8==0 ? BG 0x055968 : FG 0x055990) ;
            a5@0x10CA++ ; 0x558A2 (every 4 cols: 0x55904 descriptor rebuild; wrap at 16)
     0x055968 BG column(16) ─► 0x0559B2 BG cell : visual tile → 0xC08xxx  +  collision → 0x10DE00
     0x055990 FG column(16) ─► 0x055A14 FG cell : visual tile → 0xC08xxx  (+ attr, dir-reversed idx)
  0x055904  rebuild 16-entry descriptor table 0x10D1C0 (source ptrs 0x10D200) from map state
  0x055AB4  scroll commit: 4 MOVE.W → 0xC2/C40000/0002 (Genesis: staged_scroll_*)

FRONTEND / INIT (NOT gameplay streaming):
  0x05744E family ─► 0x05743C (descriptor unpack) + 0x5A4DE (block-copy engine)
```

## 2. Role of 0x05743C and 0x05744E (Phase 1 unknown — RESOLVED)
- **0x05743C** = a **12-byte descriptor unpacker** (primitive), 5 instructions: `a0=(a2)`, `a1=(a2+4)`, `d0=(a2+8)`, `d1=(a2+10)`, `rts`. Pure register load, no side effects; the argument-setup shim for the block-copy engine **0x5A4DE**.
- **0x05744E** = a **scripted frontend/init art-stamp**: sets `a5@0x10EC=352`, commits scroll (0x55AB4), then unpacks+block-copies **4 hard-coded descriptors** (0x581AA/B6/C2/CE, d2=4/4/5/5). It is one of a table of such routines (0x0574A4/B8/CE…). **It is NOT the gameplay map-publication root** — a correction to the Phase 1 tentative label. It stamps fixed composition blocks (title/attract/HUD frame), driven by literal pointers, not camera state.
- **Why 0x05744E calls 0x05743C between 0x055AB4 and 0x5A4DE:** the scroll commit positions the layer, 0x05743C loads each block's src/dst/dims from its descriptor, and 0x5A4DE copies it — a set-scroll-then-stamp-blocks sequence for a static screen.

## 3. Authoritative map / camera / scroll / collision variables (A5-relative; a5=0x10C000 arcade / 0x00FF0000 Genesis)
| Addr | dec | Meaning |
|---|---|---|
| a5@0x10A0 | 4256 | BG dest cursor (into 0xC08xxx name RAM) |
| a5@0x10A4 | 4260 | FG dest cursor |
| a5@0x10A8 | 4264 | layer/direction selector (0=BG, 2=FG-forward, else reversed) |
| a5@0x10AE / 0x10B0 | 4270/4272 | BG / FG horizontal scroll accumulators (&511 wrap) |
| a5@0x10B6 / 0x10BA | 4278/4282 | FG / vertical scroll accumulators (btst #3 = tile cross) |
| a5@0x10C6 | 4294 | map source pointer |
| a5@0x10CA | 4298 | column sub-index (0..3; rebuild at 4) |
| a5@0x10CC | 4300 | row/group index (0..15; wrap at 16) |
| a5@0x10D8 / 0x10DA | 4312/4314 | scroll deltas |
| a5@0x10EC / 0x10EE | 4332/4334 | BG / FG scroll commit values |
| **0xC08000** | — | PC080SN name RAM base (visual tiles) |
| **0x10DE00** | — | collision map: `0x10DE00 + (dest−0xC08000)/2` (Genesis 0x00FF1E00) |
| 0x10D1C0 / 0x10D200 | — | descriptor table (16) / source-pointer table |

## 4. Horizontal & vertical streaming behavior (recovered)
- **Both directions use the SAME publisher 0x055948** (one 16-tile column/row of cells), differing only in dest-cursor computation and which scroll accumulator gates the crossing.
- **Horizontal cross** (0x055822): dest = `0xC08000 + (row<<4) + (col<<2)`; publish; update BG accum `a5@0x10AE −= delta, &511`.
- **Vertical cross** (0x05572E→0x055788): when vertical accum `a5@0x10B6 += delta` sets **bit 3 (8px tile)** → publish; dest = `0xC08000 + (a5@0x10CC<<10) + (a5@0x10CA<<8)`.
- **Direction reversal**: 0x055A14 inverts the sub-index (`notw %d7; andiw #3`) when `a5@0x10A8 != 2` — the arcade already handles reversed streaming.
- **Wrapping**: scroll accumulators are masked `&511` (512 px = 64 tiles) → **the arcade name RAM is already a 64-tile circular buffer**; the visible window is a rotated view.
- **Collision** (0x0559D4): every BG visual cell writes a parallel collision word to `0x10DE00 + (dest−0xC08000)/2` unless `desc+32==255`. Same tile index as the visual — collision and visual are co-produced and inherently aligned.

## 5. Exact semantic replacement boundaries (gameplay)
| Arcade | When | Role | Genesis-native target |
|---|---|---|---|
| **0x055948** | per column/row crossing | **THE publish-one-column/row boundary** | publish entering VDP plane column/row |
| **0x0559B2** (BG cell) | per cell ×16 | visual→name RAM + collision→0x10DE00 | write BG (Plane B) cell + keep collision in WRAM |
| **0x055A14** (FG cell) | per cell ×16 | visual→name RAM (dir-aware) | write FG (Plane A) cell |
| **0x055904** | every 4 columns | descriptor (source-ptr) rebuild | **keep** (map/source selection = arcade-owned) |
| **0x055AB4** | per frame | scroll commit | commit VSRAM/HSCROLL (already staged) |
| streaming triggers 0x055822/0x05572E/0x0556FC/0x050434 | camera cross / init | **decide** when/where to publish | **keep** (arcade owns camera & progression) |
| 0x05744E family, 0x5A4DE, 0x05743C | frontend/init | scripted art stamp | keep as block staging (frontend) |

**Principle:** the arcade keeps owning *when/what/where* (triggers, descriptor rebuild, camera, collision). Genesis owns only the *how* — turning each cell/column write into the equivalent 64×64 VDP plane cell, and committing the already-computed scroll.

## 6. Classification of Phase 1 hooks
- **Semantic boundary (retarget to native ring writes):** `genesistan_hook_tilemap_plane_a` (0x055968 BG col), `genesistan_hook_tilemap_fg` (0x055990 FG col), and the underlying cell path — these are where the arcade emits one column of cells.
- **Keep (arcade-owned mid-level):** 0x055904 descriptor rebuild (`genesistan_hook_pc080sn_descriptor_rebuild`), 0x055AB4 scroll (staged_scroll_*).
- **Low-level primitives to bypass once cells route to VDP:** `pc080sn_bg_scroll_fill` / `pc080sn_fg_scroll_fill`, `tilemap_bg_fill[_tall]` / `tilemap_fg_fill[_tall]`, the 0x03AD44 tilemap dispatch branch, `cwindow_clear` (becomes a plane-clear), inline_fg_write_* (frontend).
- **Frontend/compat:** 0x05744E family, block-copy 0x05A4DE, item-page, glyph/number/text-writer HUD producers.

## 7. Direct arcade-call retargeting plan
Route the **cell writes** (0x0559B2 `movew %a1@,%a0@` and 0x055A14) — i.e. the arcade's `*(0xC08xxx)=tile` — to a Genesis helper that maps `(dest−0xC08000)` to a VDP nametable address in a **64×64 Plane** (BG=Plane B, FG=Plane A), preserving the arcade's tile-index/wrap. Because dest already carries the wrapped world position, the VDP cell = `plane_base + ((tilerow & 63)*64 + (tilecol & 63))*2`. Scroll commit (0x055AB4) already maps to VSRAM/HSCROLL. Collision (0x10DE00 write in 0x0559D4) is left in WRAM untouched. **No new decision logic on the Genesis side.**

## 8. Genesis circular-plane helper contract (derived)
- `plane_cell_write(dest_offset, tile_word, layer)` → VDP write at `PLANE(layer) + wrap64(dest_offset)`; `layer` from `a5@0x10A8` (BG vs FG). Tile/attr/flip/priority come from the arcade tile word unchanged (palette via existing PROUTE).
- `commit_scroll()` = existing 0x055AB4 staging → VSRAM (vertical) + HSCROLL (horizontal) from a5@0x10EC/0x10EE and per-line residual.
- **Boundary events** fall out naturally: horizontal cross → 16 cell-writes forming a column; vertical cross → 16 forming a row; diagonal → both (two 0x055948 calls, already the arcade behavior); sub-tile → scroll commit only; changed resident cell → a single cell-write; scene init / jump → full 64×64 population (the 0x050434 init path already walks all columns).
- **Row/col intersection on diagonal:** handled by two independent column/row publishes (arcade already serializes them); the corner cell is written twice, harmlessly.
- **Level independence from VRAM size:** guaranteed because the arcade indexes with `&511` (64-tile) wrap regardless of level length — the plane is a sliding 64×64 window; long levels never exceed it.

## 9. Buffers / projection code to retire
Genesis-only intermediates that become unnecessary once cells route directly to the 64×64 plane:
- **`staged_bg_tall_buffer`, `staged_fg_tall_buffer`** (emulate a >32-row virtual map — redundant; the arcade window is already ≤64).
- **`vdp_project_bg_tall_if_dirty` / `vdp_project_fg_tall_if_dirty`** and the **32×64 projection copies**, `bg_tall_project_base`/`fg_tall_project_base`, `bg_tall_dirty`/`fg_tall_dirty` (the ~45k-cyc/copy cost measured in the optimization report — eliminated).
- **`staged_bg_buffer` / `staged_fg_buffer` + strip commits** likely retire too (direct VDP cell writes replace the shadow-then-strip-DMA), OR remain as a thin dirty-cell VDP write queue. **[decide in Build 0236 after runtime confirm]**
- Low-level fills (`pc080sn_bg/fg_scroll_fill`, `tilemap_*_fill[_tall]`) become dead once the cell path is retargeted.

## 10. Collision / render relationship (preservation strategy)
Collision stays a **separate WRAM channel at 0x10DE00** (Genesis 0x00FF1E00), produced by 0x0559B2 exactly as today — it must NOT move into the VDP cache. Alignment is automatic: both the visual cell and its collision word derive from the **same dest cursor** (`0x10DE00 + (dest−0xC08000)/2`), so if the Genesis visual mapping preserves the arcade `(dest−0xC08000)` tile index, collision indexed by the same expression stays pixel-aligned to the visual world. **The KF-067 8px / OPEN-0159 un-rebased issues must be resolved as part of this so visual and collision share the single origin (see coordinate report).**

## 11. Ordered Build 0236 implementation plan
1. **Confirm (runtime):** the a5 field roles in §3, the `dest → 0xC08xxx` cell address range, and that horizontal+vertical+reversal all funnel through 0x055948 (matched traces: horizontal travel, both vertical directions, reversal, first rope as ordinary vertical stream).
2. **Map** `(dest−0xC08000)` → 64×64 VDP nametable offset for BG (Plane B) and FG (Plane A); verify against a static full-column publish at scene init (0x050434).
3. **Add** `plane_cell_write` helper; retarget the cell path (0x0559B2/0x055A14 visual store) to it while leaving collision (0x10DE00) and descriptor rebuild (0x055904) intact.
4. **Commit scroll** via existing staging (VSRAM/HSCROLL); delete the tall-buffer projection + copies.
5. **Full-refresh** path for scene init/jump (populate all 64×64 from the init walk).
6. **Retire** dead buffers/fills once parity holds; keep collision in WRAM.
7. **Verify** frame-for-frame plane parity vs Build 0235 across the §11.1 movement set; confirm collision unchanged; run gates.

## 12. GO / STOP recommendation
**CONDITIONAL GO for Build 0236 design; STOP on immediate implementation** until the §11.1 runtime confirmations are captured. The static model is strong and internally consistent (the arcade is already a 64-tile circular publisher with co-produced aligned collision), which makes a direct-retarget architecturally sound and lets us delete the expensive tall-buffer projection. But three facts were established statically only and must be runtime-confirmed before writing code: (a) exact a5 field semantics under real movement, (b) the precise `dest → 0xC08xxx → VDP` offset mapping (including BG vs FG plane bases and any 0xC20000/0xC40000 vs 0xC08000 split), and (c) that vertical/reversal streaming truly reuses 0x055948 with no separate row-producer.

## 13. Remaining uncertainties (explicit)
- FG cell producer 0x055A14 was only partially dumped; its exact collision/attr handling and the `a5@0x10A8==2` branch need full disassembly.
- The 0xC08000 name-RAM base vs the 0xC20000/0xC40000 scroll-register destinations (0x055AB4) — need the exact BG/FG plane base split; 0xC08000 may be an FG name area with BG elsewhere.
- 0x05988C / 0x059882 / 0x047004 (other 0x041F30 callees) not traced — confirm none also publish map cells.
- Indirect callers of 0x055948 beyond the four found, and the 0x050634 init loop (not located in the linear export — likely data-adjacent), need runtime PC capture.
- No matched arcade/Genesis runtime traces were run this session (deferred by scope); §11.1 is the required next step.

---

## 14. RUNTIME CONFIRMATION (Phase 2B, 2026-07-24) — matched arcade MAME traces
Arcade `rastan` (World Rev 1, roms/rastan.zip) in MAME, Stage 1, scripted movement + write-taps on name RAM (0xC08000–0xC0FFFF) and collision (0x10DE00–0x10DFFF). **Exec-taps and `screen:vpos()`/`vblank()` inside memory taps are unreliable in this MAME**, so timing was measured with a `screen:register_vblank` flag and fields were read at frame boundaries.

### Corrected A5 field addressing (IMPORTANT)
`%a5@(N)` = a5 + N where a5 = **0x10C000**, so the "0x10A8"-style offsets are DECIMAL 4264 = **absolute 0x10D0A8**, NOT 0x10C0A8. All map fields live in **0x10D0xx** (consistent with the descriptor table 0x10D1C0 / source 0x10D200 / collision 0x10DE00). Confirmed live values:
| Field | Abs | Runtime observation |
|---|---|---|
| a5@0x10A0 BG cursor | 0x10D0A0 (long) | = **0xC08100** (recomputed each column-publish; not monotonic) |
| a5@0x10A4 FG cursor | 0x10D0A4 (long) | = **0xC08000** |
| a5@0x10A8 selector | 0x10D0A8 | **0x0000 throughout Stage-1-start horizontal movement** (BG path); FG/selector=2 not exercised |
| a5@0x10AE BG h-scroll | 0x10D0AE | tracks right movement: 0x0001→0x01FB→0x0197→0x016C (decreasing, &511 wrap) |
| a5@0x10B0 FG h-scroll | 0x10D0B0 | 0x0149 (semi-static; parallax) |
| a5@0x10B6 / 0x10BA v-scroll | 0x10D0B6 / 0x10D0BA | 0x0008 / 0x0049 (stable — no vertical streaming reached) |
| a5@0x10CA / 0x10CC | 0x10D0CA / 0x10D0CC | 0 at frame boundaries (transient per publish) |

### Confirmed
1. **Name RAM = 0xC08000–0xC0BFFE** (0x4000 B = PC080SN, dual 64×64 planes). Writes are **contiguous word writes** (column-major: consecutive addresses = a column's rows), in bursts on tile-boundary crossings — matches the static 16-cell column publisher.
2. **Collision = 0x10DE00–0x10DFFE**, full grid; index proven statically as `0x10DE00 + (name_dest − 0xC08000)/2` (0x0559D4), runtime range-confirmed.
3. **TIMING (definitive): production is 100% ACTIVE-display** — `duringVBLANK=0`, `duringACTIVE=19718` over the movement window. The arcade writes its dual-ported PC080SN name RAM throughout the active frame.
4. **Scene init / level load** publishes full planes: bursts of **8192 writes (= one 64×64 plane)** and larger at state transitions (a5@0x10C002: 2→3), i.e. full-cache population, not incremental — matches the §8 "scene init = full 64×64 populate" requirement.
5. BG horizontal streaming uses selector=0 (0x055968 path) exclusively; the shared publisher structure is consistent with §4.

### VDP publication DECISION (resolved)
**Queued write — append already-decided cell writes to a VBlank-owned commit structure; flush to the 64×64 VDP planes during VBlank.** Immediate VDP writes are INVALID: the arcade produces during active display (result #3), which the Genesis VDP cannot replicate (VRAM writes must be VBlank/DMA). The queue holds only the arcade's already-decided `(plane, cell_index, tile_word)` writes — no scheduler, renderer, or map engine. The current Genesis staging (stage buffer → VBlank DMA) already embodies this model; the ring redesign keeps queue→VBlank-commit and replaces only the heavy tall-buffer projection with a bounded per-cell/column queue.

### Collision alignment result
The collision write uses the SAME wrapped cell index as the visual (`(dest−0xC08000)/2`) — confirmed by construction (0x0559D4) and range. Any remaining visual/collision misalignment is a **Genesis-side origin/rebase defect** (KF-067 8px row base; OPEN-0159 un-rebased 0x10DE00→0x00FF1E00), NOT an arcade-model difference: the fix is to make the Genesis collision producer use the identical `(dest−0xC08000)/2` index the visual mapping uses, under one shared origin.

### Remaining uncertainties (for Build 0236 step 1 verification)
- **Exact dest→(row,col,plane) decode** and the BG/FG split within 0xC08000–0xC0BFFF: base + column-major stride confirmed; full decode (static: horizontal `0xC08000+(row<<4)+(col<<2)`, vertical `+(0xCC<<10)+(0xCA<<8)`) not runtime-cross-checked, and the FG (selector=2) plane base not observed.
- **Vertical / reversal / diagonal streaming** not captured at runtime (Stage-1-start is horizontal; rope/vertical not reached in automation) — static path (0x05572E→0x055948) is clear; capture on the rope before finalizing.
- Whether **0x05988C / 0x059882 / 0x047004** (other 0x041F30 callees) also write map cells — not directly ruled out (all captured writes had the BG-streaming signature).
- Publisher 0x055948 reach not exec-counted (exec-taps unreliable here); inferred from column bursts + shared structure.

### GO / STOP
**CONDITIONAL GO** — proceed to Build 0236 DESIGN/prototype of the queue→VBlank plane-map helper (the core contract is confirmed: active-display production ⇒ VBlank queue; name base 0xC08000 dual-plane; collision same-index; column-major streaming via a shared publisher). **Capture the four remaining uncertainties above as step 1 of implementation** before committing the exact dest→VDP mapping. Do NOT implement immediate VDP writes.

---

## 15. BUILD 0236 IMPLEMENTATION ATTEMPT → STOP (2026-07-24)
Deep read of the LIVE Genesis path (tilemap_hooks.s plane_a/fg + vdp_comm.s) to scope the retarget. Result: **STOP without consuming Build 0236** — the horizontal mapping is proven, but the vertical→VSRAM windowing required to go native 64×64 is unproven (a task STOP condition) and the pass/fail criteria are visual (require user verification).

### Resolved (implementation-ready) — horizontal BG cell mapping
The live plane_a hook ALREADY maps the arcade dest to a plane cell and writes `staged_bg_buffer` directly (no tall buffer on this path):
- `cell = (a5@0x10A0 [dest, 0xC08xxx] − ARCADE_PC080SN_CWINDOW_BASE_BG(0xC00000)) / 4` (2 words/cell; `&3==0` guard)
- `row = cell & 0x1F` (32 rows today), `col = (cell>>6) & 0x3F` (64) — **column-major, matches the arcade** (§2/§14)
- write offset in `staged_bg_buffer` = `row*128 + col*2 + strip*2`; sets `bg_row_dirty` bit `row`
- FG: `genesistan_stage_fg_src_column` uses `ARCADE_PC080SN_CWINDOW_BASE_FG`, same structure → `staged_fg_buffer` → Plane A.
- BG=Plane B (VRAM 0xC000), FG=Plane A (VRAM 0xE000); each region is 0x2000 = room for 64×64.
- Collision: `genesistan_stage_bg_collision_column` reproduces 0x0559B2's `0x10DE00+(dest−0xC08000)/2` side-channel into WRAM.

### The current architecture being replaced (confirmed)
- **Planesize reg = 0x01 → 64×32** (NOT 64×64). The plane is only 32 tall.
- `staged_bg_buffer` = 32×64; strip commit DMAs ≤32 dirty rows (`cmpi #32`) to Plane B.
- The 32 tall rows cannot show the taller arcade map, so `vdp_project_bg/fg_tall_if_dirty` re-projects a 32-row window out of the 64-row `staged_*_tall_buffer` on each vertical tile crossing and forces a full 32-row DMA; the coarse vertical scroll is consumed there, leaving **VSRAM only the `&7` sub-tile residual** (the proven 0223 model).

### Why 64×64 native is a COUPLED change (not a drop-in)
Going native requires ALL of: `row&0x1F → &0x3F`; 64-row `staged_*_buffer` + 64-bit `*_row_dirty`; strip commit `cmpi #64`; **planesize 0x01 → 0x11 (64×64)**; delete the tall projection; and — critically — **move the FULL vertical scroll into VSRAM** (a 64-tall ring is 512 px; VSRAM must window it), replacing the current `&7`-residual scroll in `vdp_commit_scroll`.

### The blocking unproven fact (STOP)
The **arcade-vertical-scroll → Genesis-VSRAM windowing equation on a 64-tall ring is unproven.** Phase 2B could not capture vertical streaming (Stage-1-start is horizontal; the rope/vertical section was not reached in automation) and the FG selector=2 base was never observed. This is exactly the mapping whose earlier wrong version produced the **cyan seam / half-screen FG displacement / rolling black bar in Builds 0224-0227** — the same defects this task lists as fail criteria. Those are **visual** defects that headless automation cannot self-verify (they required user inspection to detect/clear before).

Per the task's own STOP conditions — *"STOP only for: unproven BG/FG mapping … severe map corruption …"* — the vertical/FG mapping is unproven, so shipping a one-shot 64×64 rewrite would risk exactly the corruption listed, unverifiable without the user. **STOP is the faithful call.**

### Precise unblock path (for the next build attempt)
1. Matched arcade+Genesis capture of a VERTICAL streaming section (reach the rope): record a5@0x10B6/0x10BA (v-scroll), a5@0x10CC (row index), and the resulting name-RAM dest rows, to derive `VSRAM = f(arcade_v_scroll)` on the 64-tall ring; also observe the FG selector=2 dest base.
2. Prototype the 64×64 change behind a build flag (`PC080SN_RING64`), default OFF so Build 0236 stays byte-identical to 0235 until proven.
3. Validate horizontal FIRST (VSRAM near-constant at Stage-1-start), then vertical/reversal/diagonal, WITH the user available for the cyan-seam / displacement / black-bar visual checks.
4. Only then flip the flag and consume a build number.

**STOP: YES — no Build 0236; counter remains 235; no source changed.** Horizontal mapping resolved and recorded above; the single blocking measurement (vertical→VSRAM) is specified.

---

## 16. BUILD 0236 IMPLEMENTED — BG native 64×64 ring (2026-07-24)
**Build 0236:** `dist/rastan-direct/rastan_direct_video_test_build_0236.bin`, SHA256 `f471be01ec5db584cabe0f76f3421229d0a7e61a7dbdfb80d236f7083ccf439f`, size 1,588,488, counter 236, GATE_PASS, VRAM overlap check PASS. Builds 0228-0235 preserved.

### VRAM decision (resolved during implementation)
Two 64×64 planes (0xC000-0xFFFF) collide with SAT (0xF800) + HSCROLL (0xFC00), and VRAM is full (BG tiles 0x20-0x7FFF, sprite tiles 0x8000-0xBFFF). Freeing room for both needs a sprite-tile-cache cut (residency associativity change, sprite-baseline risk). **Plane B (BG) 64×64 fits cleanly in the free 0xD000 gap (0xC000-0xDFFF) with NO SAT/HSCROLL/sprite relocation.** So this build converts **BG to the native ring; FG (Plane A) stays on its working tall-projection path** (rows 32-63 kept off-screen by its residual VSRAM, harmlessly overlapping SAT/HSCROLL which still function). Full FG conversion needs the VRAM freed first (documented next step).

### Implemented BG mapping (code path changed)
- **Interception (unchanged):** `genesistan_hook_tilemap_plane_a` writes `staged_bg_buffer` directly (the real gameplay BG source; the BG tall buffer is only fed by the frontend item-page, so projecting it in gameplay was clobbering plane_a — now disabled).
- **Cell mapping:** `cell=(a5@0x10A0 dest − 0xC00000)/4`; **row = cell & 0x3F (0..63, was truncated &0x1F)**; col=(cell>>6)&0x3F; buffer offset `row*128 + col*2 + strip*2` into the 64×64 `staged_bg_buffer` (grown 2048→4096 words).
- **Dirty:** two 32-bit masks `bg_row_dirty` (rows 0-31) + `bg_row_dirty_hi` (rows 32-63); plane_a sets the bit for the written row.
- **Commit (`vdp_commit_bg_strips_if_dirty`):** scans 64 rows, DMAs only dirty rows (64 words each) to Plane B, clears both masks. Repeated same-cell writes collapse (shadow holds final value; one DMA/dirty row).
- **Scroll:** BG VSRAM = `(−staged_scroll_y_bg + 8) & 0x1FF` (full 512px window) in gameplay (was `& 0x0007` residual); HSCROLL unchanged (arcade-owned commit).
- **Planesize:** VDP reg 16 `0x01 → 0x11` (64×64, both planes).
- **Old path bypassed in gameplay:** `vdp_project_bg_tall_if_dirty` returns immediately (scene==1); the 32×64 BG projection copy + full-row refresh no longer run.
- **Collision:** unchanged — `genesistan_stage_bg_collision_column` still mirrors 0x0559B2's `0x10DE00+(dest−0xC08000)/2` into WRAM, same wrapped index as the visual.

### Measured (headless, Build 0236 vs baseline)
- Boots (scene 0 title) → Stage 1 (scene 1); ran to F7500+ with no crash/lock.
- **BG tall projector: 0 gameplay calls** (was ~0.18/frame on vertical scroll @ ~45k cyc each — removed).
- BG plane populated: 212 non-blank tiles in visible rows 0-31; rows 32-63 empty until vertical streaming (not reachable at flat Stage-1-start).
- HUD score (0x002A) + white 1UP (0x39/0x48/0x46) = 0235 baseline; sprite pipeline (pc090oj_hooks.s) + SAT/HSCROLL VRAM bases untouched → PC090OJ/palette/score preserved by construction.
- VBlank strictly lighter than 0235 (removed the tall-projection copy; commit is bounded to dirty rows ≤64).

### User-test items (headlessly unreachable)
Horizontal visual coherence (no cyan seam/displacement); **vertical scroll** (rows 32-63 populate + VSRAM sign/offset correct — derive/confirm on the rope); reversal/diagonal. FG conversion pending the VRAM-freeing decision.

## Compliance
Build 0236 produced (counter 236). Source changed: tilemap_hooks.s (BG plane_a 64-row) + vdp_comm.s (planesize, 64-row BG buffer/dirty/commit, BG projection gameplay-skip, BG full VSRAM) + paired coverage invariants. FG/collision/sprite/frontend untouched. All numbered artifacts preserved. (Matched arcade MAME traces are read-only; the Genesis Build 0235 side was already characterized in the optimization report's gameplay measurement and was not re-run this session — the arcade contract was the open question.)

---

## 17. ARCADE PC080SN NAME-RAM FORMAT & TWO-LAYER LAYOUT (2026-07-25, MAME `rastan` + Ghidra)
Recovered directly from the arcade (authority order arcade-first), correcting all prior Genesis-buffer-derived occupancy claims.

**Name-RAM cell format (arcade HW addresses):** each cell = **2 words**: `word0` (even addr) = **`0x0003` constant attribute** (palette/priority); `word1` (odd addr) = **tile code**. Measured: even words = 0x0003 x4096; odd words = the real tiles. The visual "blank" is a tile value in `word1` (not 0x0003, not the Genesis-converted 0x2000).

**Two active tilemap layers (each 64x64 ring, 0x4000 bytes):**
| Arcade name-RAM base | Role | word1 content (measured, gameplay) |
|---|---|---|
| **0xC00000** | **BG - dense background scenery** | tiles ~0x0665-0x06B8, many x62, no dominant base |
| **0xC08000** | **FG - playfield/foreground** (collision-aligned) | base tile **0x0020** ~59% + varied 0x00CD/0x00CC/0x00D8 |
| 0xC04000 | unused | all 0x0000 |

**Scroll (0x055AB4):** a5@0x10EE->0xC20000(X) / a5@0x10B0->0xC20002(Y); a5@0x10EC->0xC40000(X) / a5@0x10AE->0xC40002(Y). Measured parallax: (0x149,0x149) vs (0x1B3,0x166) - layers scroll independently.

**Collision (0x0559B2/0x0559D4):** for the **0xC08000 (FG) layer**, collision_word -> 0x10DE00 + (dest - 0xC08000)/2, from descriptor +20+... (or +34 when desc+32==255). Ties collision to the FG/playfield layer's cell index; BG (0xC00000) has no collision channel.

**Cell producer 0x0559B2 (address-faithful):** loop d2=0..3: *(a0)=*(a1) (word1 tile from streaming map source a1); collision to 0x10DE00; a0+=2; *(a0)=desc[0+a5@0x10CA*2+d2*8] (word0/attr); a0+=254 (=> +256/iter). 0x055A14 (FG) mirrors with a direction-reversed sub-index (notw when a5@0x10A8!=2).

**Open arcade cross-checks:** definitive a5@0x10A8 selector->layer mapping; 0xC00000 layer base/blank tile; scene-init cadence; 64->32 resident-window origin per layer. (Selector-tagged write capture needed; prior attempts had a capture-window/selector-read miss.)

## Compliance (arcade-analysis update)
Design/reference-only. No source, ROM, tool, spec, hook, or build counter changed this session. Counter remains 238. All numbered artifacts preserved.
