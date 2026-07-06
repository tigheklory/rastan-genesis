# Andy — Semantic PC080SN / PC090OJ Operation Recording Architecture, Phase 1 (Design / Static Only)

**Author:** Andy
**Date:** 2026-07-05
**Baseline:** Build 0140, `dist/rastan-direct/rastan_direct_video_test_build_0140.bin`, SHA256 `f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`.
**Authoritative mapping:** `build/rastan-direct/address_map.json`.
**Scope:** Static architecture analysis, taxonomy, profiling-plan design, migration planning. **No** implementation/source/spec/tool/Makefile/ROM/build/bookmark/runtime change. Arcade↔Genesis mappings from `address_map.json`, no arithmetic. Labels **[OBS]** verified from source; **[EVID]** Cody trace/census; **[INT]** interpretation.

> **AMENDMENT (2026-07-05): static gates closed; profiling boundary corrected.** Andy has now resolved the two static prerequisites (BG strip entry §2a; PC090OJ SAT-slot ownership §11a) — these are **removed from Cody's task**. The Build 0140 disposition (§14) is **no longer "all retain-and-generalize"**; each item now carries a status among {proven reusable primitive / candidate for generalization / likely replacement / likely removal / profiling decision required}. The first migration family is **not preselected** — the immediate next step is a **profiling gate** with candidate Branches A–D (§16). Profiling is split into **two separate environments** (Genesis Build 0140 vs original arcade, §13). `opcode_replace = 133` is **no longer a permanent acceptance requirement** (§17). Palette stays **outside** the first migration boundary (§8-note). Established rules (push-based recording; no content/committed-shadow diffing; PC080SN and PC090OJ separate; interrupt-safe publication; readback gate; no frame-pipeline change; no scaffolding) are preserved unchanged.

---

## 1. Executive decision

**Outcome A — architecture rules + profiling plan ready.** The permanent architecture records **arcade intent at the producer** (a published dirty record or semantic descriptor) and **presents only recorded work at VBlank**, never reconstructing intent by diffing tile/sprite content or committed VRAM. Per-family the mechanism is chosen by cost, not universally: **compact-geometry families (strips, runs, rectangles, fills, scene loads, sprite ranges, structural SAT) → semantic descriptors; scattered fixed-slot changes → exact dirty bits; full-plane/near-full → broad fallback; immediate VDP only inside a statically proven display-off window.** Build 0140's FG narrow strip path is a **proven-correct producer-specific primitive**, but whether it becomes the permanent PC080SN mechanism is **profiling-dependent, not preselected** (§14). The permanent representation per family cannot be chosen without **logical-operation-instance profiling** (the census measured raw writes, not logical operations, amplification, repeat/overlap, or readback). Therefore the concrete next step is a **profiling gate** (the exact Cody task in §13/§20). Its output selects among **candidate Branches A–D** (§16): family-level PC080SN strip descriptor, exact PC080SN dirty-slot metadata, PC090OJ field/structural recording, or a permanent CPU→DMA conversion — **Build 0140's existing shape is not the default winner merely because it exists.** PC090OJ has an intent record (candidate bitset) + code-keyed residency + DMA presentation, but it is **not fully semantic**: the candidate bitset is a **record-level touched flag** that loses field/structural/value distinctions, and the emitted **SAT slot is packing-order, not a stable arcade identity** (§11a) — so its next boundary is likewise profiling-gated.

---

## 2. Current architecture inventory

### PC080SN [OBS `tilemap_hooks.s`, `vdp_comm.s`, `scene_load.s`, `palette_hooks.s`; EVID census]

| Family | Arcade entry → Genesis | Helper | Logical op | Staging/mirror write | Current dirty metadata | Presenter | CPU/DMA | granularity | amplification |
|---|---|---|---|---|---|---|---|---|---|
| FG vertical strip | `0x055990→0x055B90` | `genesistan_hook_tilemap_fg` (0x0703EA) | 16-col-stride-4 × 4-row interleave (64 cells) | `staged_fg_buffer` (0xFF501A) | **Build 0140: descriptor `fg_narrow_desc_table` + suppress broad**; else `fg_row_dirty` (0xFF4006) | `vdp_commit_fg_narrow_strips` + `vdp_commit_fg_strips_if_dirty` | CPU strided (0x08) / CPU full-row | narrow 64 w / broad 256 w | 4.0× (broad) → 1.0× (narrow) |
| BG vertical strip | `0x055968→0x055B68` (BG); observed `0x055C80/0x055C94` are `arcade_copy` | `genesistan_hook_tilemap_plane_a` (0x070248) | same shape into Plane B | `staged_bg_buffer` (0xFF401A) | `bg_row_dirty` (0xFF4002), broad row | `vdp_commit_bg_strips_if_dirty` | CPU full-row | 256 w/dirty row | 4.0× |
| Bulk scene fill/clear/copy | `0x03AD44` (`0x03AD48`) | `genesistan_hook_3ad44_dispatch` (routes tilemap fills + PC090OJ fills) | longword fill/copy of ranges | staged_bg/fg / `pc090oj_object_ram` | broad row / mirror-dirty | broad commits | CPU | full rows | high (whole plane) |
| Full-plane clear/init | `0x0561B6` | (NOP-suppressed / fill hooks) | 4096-cell C-window clear | staged buffers | broad | broad | CPU | full plane | max |
| FG fill (single-cell) | `0x3A550/0x3A8FE/0x3A908/0x3ACEA` | `genesistan_hook_inline_fg_write_*` → `genesistan_hook_tilemap_fg_fill` (0x0703EA-family) | one cell (D0 code, D1 count) | `staged_fg_buffer` | per-cell `fg_row_dirty` | broad FG commit | CPU full-row | 64 w for 1 cell | 64× (worst) |
| Text/glyph | `0x03BB48`, `0x03C2E2`, `0x0563A6` | text-writer hooks | string/number glyph runs | staged_fg/bg | broad row | broad | CPU | full rows | high |
| Block/row copy | `0x05A4DE` | block-copy hook (`genesistan_hook_tilemap_bg_blockcopy` 676) | rectangle copy | staged_bg | broad row | broad | CPU | full rows | high |
| Scroll latch X/Y | `0x055ABA/…/0xC20000/0xC40000` | CLR.W redirects → `staged_scroll_x/y_bg/fg` | scroll register value | `staged_scroll_*` (8 B) | none (unconditional commit) | `vdp_commit_scroll` | CPU 4 w + regs | 4 w | 1.0× |
| Control latch | `0xC50000` | ctrl NOP/redirect | screen-flip/control | `pc090oj_ctrl_shadow`/none | none | — | — | — | — |
| Scene load | producer hooks → `load_scene_tiles` (`scene_load.s`) | `load_scene_tiles` | bulk tile-pattern preload | direct VRAM | its own DISPLAY_OFF + IRQ mask | self (main-loop, own display-off window) | CPU stream | pattern DMA-eligible | transition-only |
| Palette | `0x59AD4/0x03AB00/0x045DB8/0x03BA64` | `genesistan_palette_hook_*` (`palette_hooks.s`) | CRAM bank/entry/run update | `staged_palette_words` (0xFF601A) | `palette_dirty` byte | `vdp_commit_palette` (after DISPLAY_ON) | CPU 64 w | whole-table on any change | up to 64× |

Ordering dependence: strips/fills are order-sensitive at the C-window (later writes overwrite); readback dependence: **unproven** for the C-window (no arcade-readback evidence yet — a gate, §10). Timing context: all producers run in the arcade **main loop** (no VDP ownership) except `load_scene_tiles` (own display-off window) and the VBlank commits (display off). Fallback owner: the broad `fg_row_dirty`/`bg_row_dirty` + full-row commits.

### PC090OJ [OBS `pc090oj_hooks.s`, `pc090oj_assets.s`]

| Family | Producer hooks | Logical op | Mirror write | Recording | Presenter | CPU/DMA |
|---|---|---|---|---|---|---|
| Sprite state (position/tile/attr) | `3b902/3b926/3b930/3b802/41dae/41f5e/45dfa/54810/5607c/56114/5a098/3ad84/54052/59f5e` | write PC090OJ object records | `pc090oj_object_ram` (0xFF67EA, 256×8 B) | **candidate bitset** (0xFF6FEA, set on every mirror write, clear on code-zero) | VBlank mirror **scan** (candidate-gated decode of 256 records → descriptors/SAT) | CPU decode |
| Sprite-list / SAT structure | scan → `.Lvcs_link_chain_build` | pack drawables 0..N-1, link chain, terminator | `staged_sprite_sat` / `staged_sprite_descriptor_table` | derived per frame | link build (WRAM) | CPU |
| Sprite-pattern upload | scan → `.Lvcs_tile_dma` | DMA 4-tile pattern per changed slot | `sprite_tile_resident_code` (0xFF674A) | **residency cache** (code-keyed: DMA only if emitted code ≠ resident) | `.Lvcs_tile_dma` | **VRAM DMA** |
| SAT transfer | `.Lvcs_sat_dma` | upload active_count×4 words | — | active_count | `.Lvcs_sat_dma` | **VRAM DMA** (active-count, ≤320 w) |

**Assessment:** PC090OJ already publishes intent (candidate bitset) and uses code-keyed (not pixel-content) re-DMA avoidance + DMA presentation — largely aligned with the target. The remaining non-semantic cost is the **per-frame decode of every candidate record and full SAT rebuild** (it does not diff content — it decodes recorded-touched slots — so it complies with rules 1–4, but it rebuilds structure every frame regardless of how few fields changed).

---

### 2a. BG strip entry — RESOLVED STATICALLY (Andy) [OBS `address_map.json`, `tilemap_hooks.s:80-242`]

- **Logical descriptor-list BG producer entry:** `arcade_pc 0x055968 → runtime_genesis_pc 0x055B68` (`patched_site`), replacement bytes `4eb900070248 4e71…` = `jsr 0x070248` (+NOP pad) → **`genesistan_hook_tilemap_plane_a`** (runtime `0x070248`). Map note: "Route PC080SN BG strip producer through rastan-direct hook symbol at 0x055968."
- **Geometry/semantics vs FG `0x055990`:** `genesistan_hook_tilemap_plane_a` (lines 80-242) is **byte-for-byte structurally identical** to `genesistan_hook_tilemap_fg` — same descriptor list (`moveq #15` × 4-row loop), same `dest += 0x400` / `col d2 = (d2+4)&0x3F` stride-4 interleave, same LUT compose, differing **only** in {BG dest offset, `CWINDOW_BASE_BG`, `staged_bg_buffer`, `bg_row_dirty`, BG strip index}. It still uses the **pre-0140 broad** `bset %d1,bg_row_dirty` (lines 218-220); it does **not** have the Build 0140 narrow-descriptor path. → **STATICALLY PROVEN: the `0x055968` BG producer is the same semantic strip family as FG `0x055990` and can share one semantic strip helper.**
- **The census-dominant gameplay BG stream is a DIFFERENT producer, not this entry.** Census `BG_VERTICAL_STRIP_STREAM` (23.7%) was identified by observed inner write PCs `0x055C80/0x055C94` (arcade driver, nothing patched) — these are **raw inner writes, not a semantic entry** (do not classify them as independent operations). They sit ~0x300 bytes from `0x055968`, so they are **not** inside the `0x055968` producer body; and `0x055C68` is separately mapped to `genesistan_hook_itempage_strip_blit → genesistan_hook_tilemap_bg_fill` (item-page column, a single-cell-fill mechanism, not the descriptor-list strip). **Which producer actually emits the gameplay BG column stream — the `0x055968` descriptor-list producer or the `0x055C7A` region — is a runtime-attribution question, not statically resolvable here.** Do **not** assume the census's BG traffic flows through `0x055968` and do **not** assume FG+BG are one permanent descriptor family solely on shape similarity.
- **Facts still requiring Cody runtime evidence:** (i) which BG entry actually fires during gameplay BG streaming and at what frequency; (ii) the runtime geometry of the gameplay BG stream (is it the same 16×4 stride-4 shape?); (iii) whether the `0x055C7A`/item-page path is a separable strip family or a distinct fill family. Cody is **not** asked to re-derive entries or mappings (Andy resolved the descriptor-list entry above).

## 3. Proven semantic operation taxonomy [EVID census + audits]

- **PC080SN `FG_VERTICAL_STRIP_STREAM`** — 36.3% of partial-Stage-1 traffic; producer `0x055990`; 16-col-stride-4 × 4-row interleave; complete attr/code tile state; multi-strip-per-frame in gameplay. **PROVEN** (census + FG current-path + overlap audits + Build 0140).
- **PC080SN `BG_VERTICAL_STRIP_STREAM`** — 23.7%; `0x055C80/0x055C94` (entry `~0x055C7A`); BG counterpart of the FG strip. **PROVEN family**; entry currently `arcade_copy` (needs entry audit before absorption).
- **PC080SN `BULK_SCENE_FILL_CLEAR_MIRROR`** — 28.7%; `0x03AD44`; broad longword fill/copy of ranges (scene lifecycle). **PROVEN family**; broad-fallback-shaped (whole plane/large ranges).
- **PC080SN `SCROLL_LATCH_X/Y`** — 10.9%; register latch; already cheap (4 words). **PROVEN**, non-amplifying.
- **PC090OJ sprite-state family** — the per-site producer hooks write object records; VBlank derives SAT. **PROVEN** (Builds 0126–0137 evidence).

## 4. Strongly supported candidate families

- **PC080SN single-cell FG/BG writes** (`0x3A550/0x3A8FE/0x3A908/0x3ACEA` glyph/immediate) — scattered fixed cells (dirty-bit-shaped), currently broad-amplified (64× worst). Strongly supported by static shape; frequency low in census (text 0.19%).
- **PC080SN full-plane clear/init** (`0x0561B6`), **block/row copy** (`0x05A4DE`) — broad-fallback-shaped.
- **PC090OJ field-only updates** (position-only vs tile/attr vs structural) — the per-site hooks strongly suggest field-vs-structural separability, but the field/structural boundary is not yet measured per frame.
- **PC080SN palette** — whole-table-on-any-change today; strongly supported candidate for a small dirty-entry set (which of 64 CRAM entries changed).

## 5. Unknown families (require profiling)

- **Readback**: whether arcade code reads back the FG/BG C-window (0xC08000/0xC00000), sprite RAM (0xD00000), or palette RAM (0x200000) — **the central gate** (§10).
- **Logical-operation counts & amplification per family** (census gives raw writes only).
- **Repeated writes to the same slot before VBlank** (dirty-collapse ratio).
- **Multi-family / same-slot overlap** per frame.
- **PC090OJ field-vs-structural change ratio** per frame; how often deactivation needs only a predecessor-link patch vs a rebuild.
- **Whether the SAT rebuild / mirror-scan CPU is a black-strip contributor** vs the tilemap CPU commits.

---

## 6. Recording-mechanism decision rules

**Per-family, cheapest correct mechanism — never one universal abstraction; PC080SN and PC090OJ are not forced to share (rule 11).**

- **A. Exact dirty bit** — **eligibility:** the operation touches **few, scattered, fixed slots** where a per-slot bit + traversal is cheaper than a descriptor, and run formation gives no benefit. Preferred **starting** candidate for single/scattered tiles and single sprite-field changes. **Not** for compact geometry (→ descriptors) or full-plane (→ broad). Publish: complete staging value → detail bit → summary bit (summary last). VBlank reads staging for the value; **never compares the value to decide if it changed** (rule 7). Structures to compare by profiling: 2048-bit exact plane bitmap (256 B) vs 32-bit row-summary + per-dirty-row 64-bit mask vs bounded slot-list + dup-prevention bits.
- **B. Cached semantic descriptor** — **eligibility:** one compact record is cheaper than setting+traversing many slot bits, for families with **compact geometry** (horizontal/vertical run, interleaved strip, rectangle, fill, clear, scene load, sprite range, structural SAT, final register latch). The descriptor represents the **family/operation**, not "one patched PC executed" (rule B). Publish payload → count last, in an IRQ-masked append (§7). Default: **retained in order** (no global dedup); a merge/last-value-wins rule is allowed only per-family with proof it preserves ordering, intermediate side effects, readback, overlap, structure.
- **C. Immediate VDP** — **eligibility ONLY** when execution is in a statically proven VDP-ownership window: (1) inside the VBlank handler (display off), or (2) a producer that establishes its **own** proven display-off window (`scene_load.s`: SR-mask + DISPLAY_OFF + stream + DISPLAY_ON + restore). **Main-loop execution alone is NOT proof** (rule 14) — those producers must record intent and never touch VDP. Immediate VDP is never chosen "because it's simpler."

**Do not pre-decide** which of A/B/C wins for single/scattered/run/strip/rectangle/fill/sprite families (rule 10) — the representative-case cost model (§8) plus profiling selects per family.

---

## 7. Interrupt publication and consumption rules

Single 68000: the risk is **VINT preempting a producer mid-publish** (VBlank is the interrupt; producers run in the main loop and are preempted while VBlank runs, so no producer appends *during* the handler). The only unsafe window is a producer interrupted between writing its value and publishing it.

- **Descriptor mechanism:** the append (write payload → increment count) executes in a **short VINT-masked critical section** (`move sr,-(sp); ori #0x0700,sr; <write payload>; <count++>; move (sp)+,sr`). This makes payload+count atomic w.r.t. VBlank. VBlank (already IRQ context) reads `count` (single-word atomic), processes `[0,count)`, then resets `count=0`. **A producer interrupted before entering the critical section defers its whole operation to the next VBlank** (payload not yet written) — matching the current frame model (an operation not yet published by VBlank presents next frame). This eliminates the **orphan/erase race** (a payload written at index N while VBlank resets count=0, then a naked `count++` mis-pointing to index 0) that a non-masked append would allow.
- **Dirty-bit mechanism:** publish order **staging value → detail bit → summary bit (summary last)**. VBlank scans **summary → detail → staging** and **clears only the detail bits under summary bits it processed, incrementally — never a wholesale bitmap clear**. A producer interrupted after setting a detail bit but before its summary bit is simply not visited (summary unset) → its bit + staging persist → presented next VBlank. Because per-slot IRQ masking would be too costly for high-rate per-cell dirtying, the summary-last order + incremental clear is the safe protocol; the summary set may be IRQ-masked only when it is once-per-operation.
- **Consumption boundary:** VBlank **snapshots** the count/summary at entry, consumes exactly that, clears incrementally, and never inspects slot values to decide presentation (rule 7). Newly published work (after the snapshot) cannot exist during the handler (producers preempted) and, for descriptors, cannot be half-visible (IRQ-masked append). **Deferral-by-one-frame is explicitly compared to the existing frame semantics** and accepted only because the current model already presents at the next VBlank boundary — no *extra* latency is introduced (a producer that would have missed the current VBlank already did so).

**Prevented:** torn metadata, partial descriptors, lost dirty bits, summary/detail disagreement, count-reset races, consumption-before-payload-complete, VBlank erasing newly published state.

---

## 8. Total instruction-cost model (direction + profiling need — no premature global ranking)

Cost = producer-record + publication + VBlank-traverse + address-setup + transfer + clear + fallback. Representative cases (▲ = likely-cheapest candidate, to be confirmed by profiling):

| Case | dirty bits | slot list | descriptor | direct VDP | broad fallback |
|---|---|---|---|---|---|
| 1 isolated tile | ▲ (1 bit; read+write 1 word) | ok | heavy (append+traverse for 1) | no (main-loop) | 64× amplify |
| 2–3 scattered tiles | ▲ | ▲ | heavy | no | amplify |
| repeated writes to 1 tile | ▲ (bit idempotent; collapses) | dup risk | dup risk | no | amplify |
| short horizontal run | ok | ok | ▲ (1 descriptor) | no | amplify |
| short vertical run | ok | ok | ▲ | no | amplify |
| interleaved strip (FG/BG) | 64 bits | 64 entries | ▲ **descriptor** (Build 0140-proven) | no | 4× |
| overlapping strips | bits merge free | list dup | descriptors retained-in-order | no | 4× |
| rectangle | many bits | many | ▲ descriptor | no | amplify |
| large fill | many bits | overflow | descriptor/fill-op | scene_load window ▲ | ▲ broad plane |
| ~entire plane | bitmap saturates | overflow | fill-op | ▲ (own window) | ▲ broad plane |
| 1 sprite position change | ▲ field-dirty (patch X/Y) | ok | ok | no | full SAT rebuild |
| 1 sprite tile/attr change | ▲ field-dirty (+ maybe re-DMA) | ok | ok | no | rebuild |
| multiple position changes | ▲ field-dirty set | list | range descriptor | no | rebuild |
| 1 activation | structural (insert+link) | — | ▲ structural descriptor | no | rebuild |
| 1 deactivation | ▲ **predecessor-link patch** (link healing) | — | structural descriptor | no | rebuild |
| ordering/priority change | structural | — | ▲ structural | no | rebuild |
| near-full sprite rebuild | — | — | — | no | ▲ full rebuild |

No winner is asserted without the profiling assumptions in §13.

---

## 9. PC080SN candidate exact-change models

Candidates (choice deferred to profiling):
1. **Exact 2048-bit cell bitmap + 32-bit dirty-row summary** — WRAM 256 B/plane + 4 B summary; producer 1 `bset` + row-summary `bset`/cell; VBlank traverses summary→row→bits, forms runs from **bit indices only** (never staging content), reads staging for values. Isolated-cell cheap; run formation from a set row's 64-bit mask via bit-scan.
2. **Exact bitmap + bitmap-word activity summary** — coarser summary (which 16-bit words of the bitmap are nonzero) for sparse planes.
3. **Bounded dirty-slot list + duplicate-prevention bits** — append slot index + a "already-listed" bit to prevent repeated-write duplication; cheap for very sparse frames, overflow → broad.
4. **Semantic operation descriptors** (Build 0140 shape) — one record per strip/run/rect/fill; cheapest for compact geometry (strips = 60% of traffic).
5. **Hybrid** — descriptors for compact families (strip/fill/scene), exact dirty bits for scattered single-cell/text, broad fallback on saturation.

For each: WRAM, producer cost, VBlank traverse, clear cost, publication (§7), isolated-cell, repeated-write collapse, overlap, run formation (metadata-only), full-row threshold (when a dirty row's set-count ≥ T → upload full row), full-plane threshold, CPU-vs-DMA break-even (short strided runs favor CPU; large contiguous runs/rows favor DMA), fallback, skipped/delayed presentation. **Run formation inspects only dirty bits / slot indices / descriptors — never staging contents** (rules 8). The strided-CPU-vs-DMA break-even and the full-row/full-plane thresholds are the primary numbers the profiler must produce. **Leading hybrid:** descriptors for strip/fill/scene + broad fallback; exact bits only if profiling shows meaningful scattered single-cell frequency.

---

## 10. Mirror / readback gates

| Buffer | Writers | Readers (Genesis) | Arcade readback? | Role | Removable? |
|---|---|---|---|---|---|
| `pc090oj_object_ram` | producer hooks | mirror scan | **UNPROVEN** (sprite RAM 0xD00000 arcade-visible; arcade may re-read to modify a field) | arcade-visible sprite state | **NO until proven** |
| `staged_fg_buffer`/`staged_bg_buffer` | tilemap hooks | FG/BG commits | none observed (Genesis composed nametable, not C-window mirror) | Genesis presentation | eventually, **gated** |
| C-window 0xC08000/0xC00000 (no mirror kept) | arcade (intercepted) | — | **UNPROVEN** (FG audit: no evidence, not proof) | arcade-visible tile RAM | mirror only if readback proven |
| `staged_palette_words` | palette hooks | palette commit | palette RAM 0x200000 readback **UNPROVEN** | Genesis CRAM staging | gated |
| `sprite_tile_resident_code` / candidate bitset | tile DMA / mirror writes | scan / tile DMA | n/a (Genesis-only helper state) | derived intent/residency | keep |

**Gate rule:** do **not** authorize mirror/staging removal or command-only handling for any family until the profiler proves its region is **not** read back by arcade-derived code with behavioral effect (rule 12/13). A mirror may **remain** as desired arcade-visible hardware state, but **must not be used to infer which operation occurred** — that is the dirty/descriptor's job. **Committed-VRAM shadow diffing is rejected as the central mechanism** (discards operation-time intent, reconstructs later, costs CPU, risks sync, conflicts with the translation objective); a full-plane committed shadow is **not** a default and would be documented only as a narrowly justified exception where operation-time intent is genuinely unavailable (none identified).

---

## 11. PC090OJ and Genesis SAT candidate models

Design separately from PC080SN. Candidates (selection profiling-gated):
- **Keep current** candidate-bitset mirror-scan + code-keyed residency + active-count SAT DMA (works; rebuilds structure each frame).
- **Field-level sprite dirty** — per-slot flags for {X, Y, tile, palette/attr, size-if-linkage-unaffected}; VBlank **patches only changed SAT fields** for still-linked slots (no rebuild).
- **Structural dirty** — {activation, deactivation, insertion, removal, count change, link-order, termination, priority remap}; VBlank does a **partial structural patch**.
- **Link healing (explicit):** on deactivation — **predecessor link → successor**, successor + terminator unchanged → a **small predecessor-link patch** may suffice instead of a full rebuild.
- **Bounded sprite-slot list / sprite-range descriptor** for clustered changes.
- **Full SAT rebuild** as the fallback (current behavior); **partial SAT link patch** and **one-entry patch** as intermediates.
- **Sprite-pattern upload** handled **separately** from SAT-entry presentation (already: residency-cached tile DMA vs SAT DMA are distinct).

**Field-vs-structural boundary:** field = X/Y/tile/palette/size with linkage unaffected → patchable in place; structural = activation/deactivation/insertion/removal/count/link/termination/priority → link-aware patch or rebuild. **Do not assume every field change is patchable** (requires proving generated-SAT slot ownership is stable across frames — the emit packs by emission order, which can shift, so a "slot" is not a stable arcade identity; this is the key proof), and **do not assume every deactivation needs a rebuild** (link healing). **Proof required to choose among one-field / one-entry / predecessor-link / partial / full rebuild:** per-frame counts of field-only vs structural changes, and whether emission-order packing keeps a given arcade record at a stable SAT slot (if not, field-patch needs a stable arcade-record→SAT-slot map). Account separately for SAT entry state, SAT link structure, sprite-pattern VRAM, and pattern-cache state.

---

### 11a. PC090OJ SAT-slot ownership — RESOLVED STATICALLY (Andy) [OBS `pc090oj_hooks.s`]

Pipeline: arcade object record → `pc090oj_object_ram[R]` (R = arcade record index 0..255) → candidate bitset → mirror scan decode → emit to SAT slot → link chain → SAT DMA.

- **Emitted SAT slot = packing order, NOT the arcade record index.** The scan emits with `d0 = pc090oj_emitted_count`, incremented once per drawable emit (`.Lvcs_mirror_emit`). So record R's SAT slot = **the number of drawable records with index < R** among the current candidate/drawable set. **Not stable.**
- **Stability holds ONLY while the drawable set and ordering are unchanged.** Any activation or deactivation of a **lower-indexed** record shifts R's SAT slot by ±1; packing compresses actives into new contiguous positions 0..N-1 every frame.
- **One object's activation/deactivation shifts all later SAT entries** (compaction). Priority/ordering: the scan visits records in **index order**, so SAT order = index order of drawables — changing a record's fields (not its index) preserves order, but the record→slot mapping still depends on the drawable set below it.
- **Field-only update patchability by identity:**
  - **by arcade object index R:** stable — but only in the **mirror** (`pc090oj_object_ram[R]`), which the producer already updates; it does **not** give the SAT slot.
  - **by generated descriptor index:** NO (packing order).
  - **by stable SAT index:** NO (packing shifts).
  - **by an additional arcade-record→SAT-index map:** possible, but that map must be **maintained/invalidated on every activation/deactivation/ordering change** — so field-patch-in-place is only viable in frames where the drawable set is unchanged, or with a rebuilt map.
- **Four identities separated:** (1) **field identity** = arcade record index + field {X,Y,tile,attr}, stable in the mirror; (2) **emitted SAT-slot identity** = packing order, unstable; (3) **link ownership** = rebuilt each frame from packed order, structural, tied to SAT slots; (4) **pattern-residency ownership** = `sprite_tile_resident_code` keyed by **SAT slot** (slot·2), so a slot's record can change → the code-compare self-corrects (re-DMA) but a drawable-set shift causes residency churn on shifted slots.
- **What the candidate bitset records / loses:** it records "arcade record R was written by a producer since last clear" (a **record-level touched flag**, cleared on code-zero decode). It **loses**: which field changed (X vs Y vs tile vs attr vs activation), field-vs-structural class, the value (decoded from the mirror each frame), and change-vs-still-present (a present-unchanged record stays a candidate and is re-decoded every frame). **It does not enable field-patch** (no field granularity, no stable SAT-slot).
- **Statically guaranteed:** arcade record index is the stable identity **in the mirror only**; SAT slot is packing-order and unstable; field-patch-in-place requires (a) field-level dirty state **and** (b) a maintained record→SAT-slot map or a stable-slot allocation scheme.
- **Requires Cody runtime measurement:** how often the drawable set/ordering actually changes per frame (churn rate → whether a maintained map + field-patch beats full rebuild); the field-only-vs-structural change ratio; the deactivation link-heal frequency. Cody is **not** asked to derive the packer's static ownership rules (Andy resolved them above).

## 12. VBlank presentation candidates (consume recorded intent; no content compare)

Family-aware primitives, each with the evidence needed to select it: isolated-tile CPU write; short horizontal CPU run; horizontal DMA run; strided CPU run (Build 0140); semantic rectangle; full row; full plane; pending scroll/control register write; sprite-field patch; SAT link patch; partial SAT rebuild; full SAT rebuild; sprite-pattern upload. Selection inputs: run length (CPU vs DMA break-even), dirty density (exact vs broad), geometry (descriptor vs bits), structural vs field (patch vs rebuild). **Preserve the current frame model** — no one-frame lag, no FRONT/BACK swap, no active-display bulk VDP, no conditional frame repetition, no general command interpreter. Thresholds are **not finalized** without §13 data.

---

## 13. Cody profiling plan (next task; measures LOGICAL operations, not raw writes)

**Type:** runtime profiling on Build 0140 (MAME Genesis + native debugger; user-driven BlastEm for any visual). **No** committed-VRAM shadow, **no** desired-vs-committed comparison, **no** implementation.

**Per logical operation instance, per family, capture:** family ID; arcade entry + completion PC (via `address_map.json`); mapped Genesis helper path; operation geometry (rows/cols/stride/count); logical cells or sprite slots changed; exact slots / semantic region; **repeated writes to the same slot before VBlank** (collapse ratio); unique final published slots; operation ordering; overlap with another family/same slot; **readback** (instrument reads of C-window 0xC08000/0xC00000, sprite RAM 0xD00000, palette RAM 0x200000 and whether the read value affects later branches); timing context (main-loop vs VBlank vs scene_load window); staging/mirror words written; **dirty metadata the proposed model would publish**; **descriptors the proposed model would publish**; current dirty rows/broad flags; current VDP words; current CPU-write path; current DMA path; current VBlank contribution; frontend/attract state; original-arcade gameplay state.

**Two separate EVIDENCE ENVIRONMENTS (distinct MAME drivers — do not merge; do not treat arcade addresses as Genesis runtime addresses):**
- **Environment 1 — Genesis Build 0140 (MAME Genesis driver, the Build 0140 ROM):** measure currently-reachable frontend/attract operation families; present Genesis helper behavior; staging work; dirty metadata; VDP words; **CPU vs DMA presentation**; **DISPLAY_OFF contribution**; black-strip relevance; and **PC090OJ scan, link-build, tile-DMA, SAT-DMA cost** separately. Also: **which BG entry actually fires during any reachable BG streaming** (runtime attribution of §2a) and **PC090OJ drawable-set churn / field-vs-structural ratio** (runtime side of §11a).
- **Environment 2 — Original Rastan arcade (MAME arcade driver, original arcade program):** measure gameplay semantic-operation families; logical operation boundaries; operation geometry; repeated writes; overlap; **arcade readback** — accesses to `0xC08000`, `0xC00000`, `0xD00000`, `0x200000`. Static disassembly should identify candidate read sites first so runtime taps are targeted. **For every readback finding, classify:** (i) read occurred; (ii) value was consumed; (iii) value affected a branch / address / later write / visible state; (iv) behavioral significance unknown. The arcade addresses are **not** Genesis Build 0140 runtime addresses.

**Rankings (separate, not combined):**
- **Final-architecture priority:** rank by `family_frequency × current_logical→Genesis_amplification × presentation_cost` (frontend and gameplay reported separately).
- **Frontend black-strip relevance:** rank by `family_frequency_in_strip_frames × actual_DISPLAY_OFF_cost_in_those_frames`.
- **Classify sprite/SAT presentation** as CPU-loop / DMA / mixed and measure its contribution (mirror-scan + link = CPU; tile DMA + SAT DMA = DMA). This may reveal a permanent DMA conversion (e.g., the mirror-scan/link CPU, or BG/FG strip commits) — **but the profiling task must not implement it.**

**Static prerequisites are CLOSED by Andy (§2a, §11a) and REMOVED from Cody's task** — Cody does not derive BG entries, prove arcade↔Genesis mappings, or establish the PC090OJ packer's SAT-ownership rules. Cody measures only the **runtime** counterparts: (a) which BG producer emits the gameplay stream and its frequency/geometry; (b) the PC090OJ drawable-set churn rate and field-only-vs-structural change ratio (the runtime input to the §11a field-patch-vs-rebuild decision). **Cody must not be asked to redesign the architecture while profiling.**

---

## 14. Build 0140 disposition and successor table

**Build 0140 is the proven-correct current baseline and proof-of-concept, but its permanent disposition is PROFILING-DEPENDENT — not preselected as retain-and-generalize.** Build 0140 may remain the code baseline while profiling occurs; that is not acceptance of its architecture as permanent. Status per item ∈ {**proven reusable primitive**, **candidate for generalization**, **likely replacement**, **likely removal**, **profiling decision required**}:

| Build 0140 item | Present status | Correctness responsibility it owns | 0x055990-specific? | Candidate permanent owners | Profiling result → generalize | Profiling result → replace/remove | Fallback until decided |
|---|---|---|---|---|---|---|---|
| `fg_narrow_desc_table` | **profiling decision required** | holds pending FG strip regions | yes (FG only) | family strip descriptor (Branch A) / exact dirty bits (Branch B) | Branch A: strips lowest total cost, FG+BG one family → generalize to `pc080sn_strip_desc_table` | Branch B: scattered/overlap dominates or descriptors cost more → **replace** with exact dirty metadata | broad `fg_row_dirty` |
| `fg_narrow_desc_count` | profiling decision required | published (last) count | yes | generalized count (IRQ-masked §7) | Branch A | Branch B: **remove** with the table | broad |
| `fg_narrow_pending_rows` | **candidate for generalization** | producer-local fallback row accumulator | no (two-phase pattern is generic) | any two-phase producer | any descriptor branch keeps it | pure-dirty branch: **remove** (broad set inline) | — |
| producer-local transaction logic | **candidate for generalization** | two-phase append-or-broad, invalid/overflow/wrap fallback | pattern generic; thresholds FG-specific | strip/rect/fill producers | descriptor branch → generalize | pure-dirty branch: **replace** with bit-publish | broad |
| selected-producer dirty suppression | **proven reusable primitive** | descriptor-success suppresses broad without touching other producers' bits | no (the core push rule) | all descriptor-backed families | retained in any descriptor branch | pure-dirty branch: **replace** (dirty is the record) | broad |
| `vdp_commit_fg_narrow_strips` | profiling decision required | strided FG presentation | yes (FG strided) | `vdp_commit_pc080sn_strips` (Branch A) / DMA presenter (Branch D) | Branch A/D → generalize | Branch B: **replace** with exact-bit presenter | general FG commit |
| VBlank tail-call arrangement | **proven reusable primitive** | presenter runs before general FG commit, autoinc restored | no | any narrow presenter slot | retained | — | — |
| boot initialization | **candidate for generalization** | cold-clears the pending state | no | whatever state the winner uses | retained/renamed | pure-dirty branch: **replace** (clear bitmap) | — |
| verification-tool expected-value changes | **candidate for generalization** | records the current invariant values | no | migration invariant bookkeeping | updated per §17 | updated per §17 | — |

**No item is asserted retain-and-generalize on static evidence alone.** Every "profiling decision required" item names both the generalization owner and the explicit replacement/removal successor (so rule 15 — no indefinite parallel machinery — is honored either way: absorption *or* replacement, decided by profiling, in the first semantic implementation build). No standalone cleanup build is needed unless the pure-dirty branch replaces the descriptor path, in which case removal is part of that migration.

---

## 15. Permanent code ownership

- **PC080SN semantic helpers + strip descriptors + dirty/summary metadata:** consolidate strip/fill/text producers' *recording* logic under `tilemap_hooks.s` (already owns the FG/BG producers); keep `scene_load.s` as the self-owned display-off transition; keep `palette_hooks.s` for CRAM. **PC080SN presentation** (strip presenter, broad commits, scroll) stays in `vdp_comm.s`.
- **PC090OJ helpers, sprite-slot/field dirty, SAT structural metadata, sprite/SAT presentation:** stay in `pc090oj_hooks.s` (already the single owner) — do **not** split.
- **WRAM allocation + metadata publication protocols:** the new PC080SN strip/dirty state lives in the FG/tilemap `.bss` (above ~0xFF7106); publication protocol (§7) documented once and reused.
- **Maintainability note:** PC080SN ownership is currently spread across `scene_load.s`/`tilemap_hooks.s`/`palette_hooks.s`/`vdp_comm.s`. **Recommend consolidating only the strip *recording* path** into `tilemap_hooks.s` as it generalizes (directly supports the semantic architecture); **do not restructure files for aesthetics** — scroll/palette/scene ownership stays where behavior lives.

---

## 16. First migration boundary / profiling gate

**The immediate next boundary is the PROFILING GATE (the §13 Cody task). The first implementation family is NOT preselected.** The static gates that were prerequisites are now closed by Andy (BG descriptor-list entry = `0x055968` §2a; PC090OJ SAT slot = packing-order/unstable §11a); the remaining unknowns (logical-operation frequency, amplification, repeat/overlap, readback, gameplay BG attribution, PC090OJ churn/field-vs-structural ratio) are strictly runtime. Profiling output selects among:

- **Branch A — family-level PC080SN strip descriptor**, if profiling proves FG and BG (the `0x055968` producer, and whichever producer emits the gameplay BG stream) are one compatible semantic family, strip descriptors are lowest total cost, the family has meaningful frequency×amplification, and ordering/overlap are preserved. (Generalizes Build 0140.)
- **Branch B — exact PC080SN dirty-slot metadata**, if profiling proves scattered/overlapping fixed-slot work dominates, descriptor retention creates more total work, or exact bits give cheaper final presentation. (Replaces Build 0140's descriptor path.)
- **Branch C — PC090OJ field or structural recording**, if profiling proves SAT construction/scan is a dominant cost and stable-or-conditionally-stable SAT ownership (§11a) permits narrow patching (field-patch with a maintained record→slot map, or a stable-slot allocation).
- **Branch D — permanent CPU→VDP-DMA conversion**, if profiling proves an existing presentation stage is a CPU loop, a major DISPLAY_OFF contributor, and DMA preserves the semantic architecture (candidate stages: PC080SN broad row commits, PC090OJ mirror-scan/link CPU).

**The final-architecture priority comes from profiling. Build 0140's existing code shape is not the default winner because it exists.** The two-view rankings and CPU/DMA classification (§13) produce the branch selection.

**Palette scope (referenced as §8-note):** the palette path (`palette_hooks.s`, whole-table-on-any-change → `staged_palette_words`) remains documented as a **future** semantic candidate (dirty-CRAM-entry set) but is **explicitly outside the first PC080SN/PC090OJ profiling and implementation decision** unless Environment-1 evidence shows palette materially contributes to the **same** presentation/DISPLAY_OFF bottleneck. Palette work must not expand the first migration scope.

---

## 17. Acceptance rules (for the later implementation)

Original semantic geometry preserved; final staging/compatibility state preserved; readback behavior preserved; no lost tile/sprite update; no dirty-bit ownership loss; no descriptor-overflow loss (broad fallback); no operation-order change without proof; no SAT-linkage corruption; no active-display VDP corruption; no frame-pipeline change; broad fallback remains correct; **superseded one-off code generalized OR removed when its successor is proven**; measurable family-wide improvement; no permanent parallel architecture without documented need; metadata publication/consumption preemption-safe (§7); no partial descriptor visible; no operation published before its value is complete; **no newly published dirty state erased by VBlank cleanup**; no unintended extra-frame delay.

**Mapping acceptance (corrected — `opcode_replace = 133` is NOT a permanent fixed requirement):**
- `address_map.json` **gaps remain zero**;
- `address_map.json` **overlaps remain zero**;
- **every changed patched site is expected and documented** by the selected migration;
- **wrapper bytes remain unchanged where no wrapper change was authorized**;
- **unexpected** mapping changes are a **stop condition**;
- **predictable, reviewed** mapping changes required by the selected family migration are **allowed**.
- The current `opcode_replace = 133` is recorded as the **Build 0140 baseline** for diffing, but **must not block a legitimate permanent migration** that documents its patched-site change.

## 18. Revert rules

Revert on: staging mismatch; readback mismatch; missed dirty slot; incorrect geometry; command-ordering change; queue-overflow loss; dirty metadata surviving incorrectly across frames; dirty metadata cleared before presentation; VBlank consumes a partial descriptor; VBlank consumes metadata before staging complete; VBlank loses an operation published across the interrupt boundary; VBlank clears newly published dirty state; SAT link corruption; sprite disappearance; sprite-ordering regression; VDP autoincrement/address-state corruption; direct VDP outside proven ownership; new exception; frontend-progression regression; address-map/wrapper invariant failure; need for scaffolding outside the intended architecture.

---

## 19. Outcome

**Outcome A — static gates closed and corrected Cody profiling task ready.** Both static prerequisites are resolved by Andy: **BG descriptor-list entry = `0x055968 → genesistan_hook_tilemap_plane_a` (0x070248), statically proven the same strip family as FG `0x055990`; the census-dominant gameplay BG stream (`0x055C80/94`) is a separate producer whose attribution is runtime** (§2a); **PC090OJ emitted SAT slot = packing-order, not a stable arcade identity; the candidate bitset is a record-level touched flag that loses field/structural/value distinctions; field-patch needs field-level dirty + a maintained record→slot map** (§11a). Build 0140's disposition is **profiling-dependent** (§14, per-item status), the first family is **not preselected** (§16, Branches A–D), profiling is split into **two environments** (§13), the mapping acceptance rule no longer fixes `opcode_replace` (§17), and palette stays outside the first boundary. No final unprofiled representation is asserted; no static fact remains unresolvable (not Outcome B); no proven-arcade-semantics conflict invalidates a family (not Outcome C) — the `0x055968` BG family is proven compatible with FG, though its gameplay dominance is a separate runtime question.

## 20. Exact next Cody task outline

**"Cody — PC080SN/PC090OJ Logical-Operation Profiling in TWO environments (Build 0140)"**
- Evidence-only; **no** committed-VRAM shadow, **no** desired-vs-committed diff, **no** source/build change, **no** architecture redesign. **Static gates are already closed by Andy — Cody does not derive entries/mappings or the PC090OJ packer rules.**
- **Environment 1 (Genesis Build 0140, MAME Genesis driver + native debugger; user-driven BlastEm for visuals):** per-family logical operations via taps on the mapped Genesis helpers (from `address_map.json`); staging/dirty/VDP-word counts; **CPU vs DMA presentation**; **DISPLAY_OFF contribution**; black-strip relevance; PC090OJ scan/link/tile-DMA/SAT-DMA cost; **runtime BG-entry attribution** (which producer emits any BG stream) and **PC090OJ drawable-set churn + field-vs-structural ratio**.
- **Environment 2 (original Rastan arcade, MAME arcade driver):** gameplay semantic-operation families; logical boundaries/geometry; repeated writes; overlap; **readback taps on 0xC08000/0xC00000/0xD00000/0x200000**, each finding classified {read occurred / value consumed / affected branch-address-write-visible-state / significance unknown}. Arcade addresses are not Genesis runtime addresses.
- Produce the **two separate views** and the two rankings (final-architecture priority = freq×amplification×cost; black-strip = strip-freq×DISPLAY_OFF-cost); classify sprite/SAT presentation CPU/DMA/mixed.
- Deliver a report enabling Andy to select among **Branches A–D** (§16) — do **not** preselect a family and do **not** implement any DMA conversion or descriptor generalization surfaced by the profiling.

**Confirmation:** no source, spec, tool, Makefile, ROM, build, bookmark, runtime, VBlank-order, DISPLAY_OFF/ON, or frame-pipeline change was made — one design document and one AGENTS_LOG entry only.
