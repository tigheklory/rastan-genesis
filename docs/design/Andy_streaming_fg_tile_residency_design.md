# Streaming Plane-A/Plane-B PC080SN Tile Residency — Implementation Design (rev 3, pre-Build-0301)

**Status:** DESIGN ONLY. No ROM produced. **Build 0301 is NOT consumed** — the next *produced* ROM will be
Build 0301. This is the policy Cody implements; it invents no behavior at implementation time.

**Tighe's locked decisions:** (1) **both-plane streaming** (FG-only rejected); (2) **hash-table forward map by
default** — the 32 KB direct map only if a linker/RAM-map check proves it fits with zero collision; (3)
**title/endround/static screens keep the existing static preload**; the streaming cache is **reset on
gameplay entry**.

## 0. Diagnosis this fixes (Build-0300 cave capture)
Cave reached (seg 1→2→3, tm0=0, selector=0); Plane-A names mostly stable; **0 pattern-overwrites** with 67–206
stable slots evaluated → not dynamic corruption. `tileset_id` stayed **1 (outdoor residency)** through the
cave → correct cave patterns never resident → cave draws real map cells against **outdoor patterns** = static
wrong tiles. Visible working set **≈124–206 tiles/plane** ≪ cache A (1004). Per-segment residency is invalid.
Fix: resident only the currently-visible tiles, streamed on demand into sprite-safe VRAM, keyed by code.

---

## 1. Hook point (where a code becomes a name word)
**File `apps/rastan-direct/src/tilemap_hooks.s`.** The static-LUT read is the exact code→slot point. Today at
each site: `andi.w #0x3FFF,%d3; add.w %d3,%d3; move.w 0(%a2,%d3.w),%d3` (`%a2 =
genesistan_pc080sn_tile_vram_lut`), then `or.w attr,%d3; move.w %d3,(cell)`.

**Replace every gameplay FG *and* BG LUT read with `bsr fg_cache_resolve`** (ABI in §8). The `or.w attr` +
name-word store are unchanged. Sites (verified):

| line | function | plane |
|---|---|---|
| 308–310 | `..._selector0_native` | FG |
| 425–427 | `..._selector12_native` | FG |
| 627–636 | `genesistan_plane_a_pan_publish_entering_rows_down` | FG |
| 704+ | same pan function | BG (staged_bg_buffer) |
| BG preamble (~976, `genesistan_hook_tilemap_plane_a`) | BG column staging | BG |

Cody converts **every** `0(%a2,%d3.w)` PC080SN tile-LUT read in the gameplay FG/BG producers (grep anchor
`genesistan_pc080sn_tile_vram_lut`). Pattern source is already linked: `genesistan_pc080sn_tile_rom`
(`build/regions/pc080sn.bin`, 32 B/tile); the cache uploads from `genesistan_pc080sn_tile_rom + code*32`.

---

## 2. Ownership model (Cache A only)
- **Slots 0..1003** (`TILE_CACHE_BASE_A=0`, `SIZE_A=1004`) — sprite-safe (sprites at 1024+). **Cache B
  (1344..1503) unused; slots 1024.. never touched.**
- **Reserved / pinned (never allocated by the streamer):** slot **0** (blank); ~4 HUD-digit slots at
  `VRAM_TILE_BASE=0x20`; **~60 text/HUD-font tiles pinned** (§7). Usable streaming ≈ **940**.
- **Fits (both planes):** FG≈124–206 + BG≈150–200 + pinned≈60 ≈ **410–470 ≪ 940** (~2× headroom). FG-only
  overflows (static BG 854 + text 60 leaves ~90 < 200) — hence both planes stream.

## 3. Cache key
**Key = `code & 0x3FFF`.** The 8×8 pattern is a pure function of the code (`pc080sn_rom[code*32]`); palette/
flip live in the name word (`.Lplane_a_native_attr_from_word`), so same code = same pattern always (no
alias); different codes = different slots. Do **not** fold tileset/page/group/segment into the key.

**Forward map (decision 2 = hash by default):** open-addressed hash, `FG_HASH_BUCKETS = 2048` (power of two),
each bucket = `{ code:u16, slot:u16 }` (8 KB), empty = code sentinel `0xFFFF`. `hash(code) = (code*2654435761)
>> 21 & (FG_HASH_BUCKETS-1)`; linear probe. Load ≈470/2048 ≈ 23% → short probes. Reverse map
`fg_cache_rev[1004]` (code per slot; `0xFFFF`=free), `fg_cache_touch[1004]` (u16 last-resolved frame — LRU
hint only, §5), `fg_slot_live_frame[1004]` (u16 — staged-buffer live snapshot, the eviction safety proof,
§5.1), `fg_state[1004]` (FREE / RESIDENT / PINNED / RESERVED). `fg_frame_ctr` u16 (+1 each VBlank).
`fg_evict_live_attempts` u16 (dev counter, must stay 0). Direct
32 KB map allowed ONLY if the linker map proves a free contiguous 32 KB region with no BSS/stack/workram
collision.

---

## 4. Upload policy + resident/pending/overflow contract (fixes issue #2 and #1)

### 4.1 Resident-means-uploaded invariant
**A code is installed in the forward map ONLY when its pattern upload for this frame is guaranteed.** The
whole upload queue is drained every VBlank *before* the name-word commits (§6), so "enqueued this frame" ⇒
"in VRAM before this frame's names display." Therefore:

`fg_cache_resolve(d3=code) → d3=slot`:
1. Hash-lookup `code`. If **RESIDENT/PINNED** → `fg_cache_touch[slot]=fg_frame_ctr`; return `slot`.
2. Not resident → attempt to enqueue an upload:
   - If `fg_upload_count < FG_UPLOAD_CAP`: `slot = fg_cache_alloc()` (§5); install
     `fwd[code]=slot`, `fg_cache_rev[slot]=code`, `fg_state[slot]=RESIDENT`,
     `touch=fg_frame_ctr`; append `(slot,code)` to `fg_upload_q`, `fg_upload_count++`. Return `slot`
     (upload guaranteed at this VBlank).
   - Else (**queue full this frame**): do **NOT** install any mapping; `fg_upload_overflow++`; **return slot
     0 (blank)** for this cell this frame. The code stays not-resident and is **retried next frame** (its
     cells show blank, never stale, until a frame has queue room).

This closes the bug: the forward map never says "resident" for a slot whose pattern hasn't been uploaded, and
an overflowed tile is guaranteed to be retried (it is never installed, so the next resolve re-attempts).
**No name word ever points at a slot whose intended pattern is not in VRAM** — worst case a cell is *blank*
(slot 0) for one or more frames, never garbage/stale.

`FG_UPLOAD_CAP` (start = **48**) also bounds VBlank DMA time: 48×16 words = 768 words — comfortably within
VBlank. The whole queue (≤ CAP) is fully drained each VBlank, so enqueued ⇒ uploaded-this-VBlank holds.

### 4.2 Cold-cache / gameplay-entry prewarm (fixes issue #1)
On the **title/endround → gameplay** transition (the only cache reset), the first frame reveals the whole
screen (hundreds of FG+BG tiles) — far above `FG_UPLOAD_CAP`. Policy: **blocking bulk prewarm with display
off**, reusing the existing scene-transition display-off window (`load_scene_tiles` already toggles
`VDP_MODE2_DISPLAY_OFF/ON`):
1. On gameplay entry: reset the cache (all slots FREE except reserved; re-pin text/HUD; clear hash);
   **display OFF** (already off during the scene load).
2. Run **one full FG and BG production pass** (staging only) so every initially-visible code is resolved →
   allocated + enqueued. During prewarm, `FG_UPLOAD_CAP` is treated as **unbounded** (bulk mode): drain the
   entire prewarm queue with PIO/DMA to VRAM *before display on* (no VBlank-time limit while blanked).
3. **Display ON.** The first visible frame therefore has every visible pattern present — no cold-cache
   garbage, no blanks.
4. Steady state thereafter uses the bounded per-frame path (§4.1). Because prewarm resolved the full visible
   set, steady-state new tiles/frame = scroll-edge only (≤ a few), so overflow never occurs in normal play.

This is policy option "prewarm the visible working set before display resumes," combined with the §4.1
"blank unresolved cells" safety net for any steady-state edge case.

---

## 5. Eviction — live-slot proof from the staged buffers, NOT from resolve frequency

**Corrected safety model (issue: producers publish only changed/entering cells, so `touch` set by
`fg_cache_resolve` does NOT prove visibility — a stable visible tile may never be re-resolved and would look
"old").** Live-slot detection must therefore be rebuilt from the **actual staged buffers each frame**,
independent of how often the producer runs.

### 5.1 Per-frame live-mark snapshot (hard safety proof)
Add `fg_slot_live_frame[1004]` (u16). Once per gameplay frame, **before any production/resolve mutates the
staged buffers** (i.e. immediately after the VBlank commit, at frame start), run `fg_cache_mark_live()`:
- scan **all 2048 cells** of `staged_fg_buffer` (Plane A) and **all 2048 cells** of `staged_bg_buffer`
  (Plane B);
- for each cell, `slot = name_word & 0x07FF`; if `slot != 0`, set `fg_slot_live_frame[slot] = fg_frame_ctr`.

Because the staged buffers are **persistent, complete** representations of each plane (they hold every cell,
updated incrementally — not just the edge the producer touched this frame), this snapshot captures **every
slot the currently-committed/displayed plane references**, regardless of producer frequency. Taking it at
frame start (before production overwrites any cell) guarantees a slot that is about to be *replaced* this
frame is still recorded live for this frame (protecting it while it remains displayed until the next VBlank).

### 5.2 Liveness test
A slot is **LIVE** and MUST NOT be evicted if ANY of:
- `fg_state[slot] ∈ {PINNED, RESERVED}`, OR
- `fg_slot_live_frame[slot] == fg_frame_ctr` (referenced by the displayed plane — hard proof from §5.1), OR
- `fg_cache_touch[slot] == fg_frame_ctr` (referenced by this frame's in-production resolves so far).

This covers both the **displayed** plane (staged snapshot) and the **in-production** plane (this-frame
touches), which is exactly the "both displayed and in-production" requirement.

### 5.3 Allocator
`fg_cache_alloc()`:
1. any **FREE** non-reserved slot (`fg_state==FREE`); else
2. among slots that are **NOT LIVE** (§5.2) and `state==RESIDENT`, pick the **oldest `fg_cache_touch`** (LRU
   is now only a tiebreak among safe candidates); clear its `fwd` entry and reassign; else
3. **no non-live slot** (cannot happen at ≈470/940; guard anyway): do **not** evict any live slot — return
   blank slot 0 for this cell, `fg_upload_overflow++`, install nothing (retry next frame).

`fg_cache_touch` is now **an optimization only** (LRU ordering among non-live candidates), never the safety
proof. The safety proof is the §5.1 staged-buffer live scan (+ this-frame touch for in-production). Any
attempt to evict a LIVE slot is a bug: the allocator refuses it (step 3) and increments
`fg_evict_live_attempts` (must stay 0 — §9).

With ≈2× headroom, free/non-live slots are always available and evictions hit only genuinely off-screen
tiles; measured 124–206/plane keeps occupancy ≪ capacity.

---

## 6. VBlank ordering (both planes) — fixes issue #3
`_vblank_service` (`vdp_comm.s:175`) exact order:
1. **`vdp_commit_streamed_tiles`** — drain `fg_upload_q`: for each `(slot,code)` DMA 16 words from
   `genesistan_pc080sn_tile_rom + code*32` to VRAM `slot*32` (reuse `.Lplane_dma_row`: `d0=slot*32`, `d1=16`,
   `a0=source`); clear queue + `fg_upload_count`; `fg_frame_ctr++`.
2. `vdp_commit_bg_strips_if_dirty` (BG name words).
3. `vdp_commit_fg_strips_if_dirty` / narrow strips (FG name words).
4. `vdp_commit_tiles_if_dirty` (HUD digits — unchanged), `vdp_prepare_sprites`/`vdp_commit_sprites_vram`,
   `vdp_commit_palette`, `vdp_commit_scroll` — existing safe order, unchanged unless proven necessary.

**Live-mark placement:** `fg_cache_mark_live()` (§5.1) runs **once at gameplay frame start — after this
VBlank service's commits, before the next frame's production/resolve** — so it snapshots the just-committed
(displayed) plane before any producer mutates the staged buffers. It is NOT part of the eviction-time path;
eviction (during resolve) only *reads* `fg_slot_live_frame`.

**Invariant:** no frame commits a BG or FG name word before its newly-assigned tile pattern exists in VRAM —
step 1 precedes steps 2–3, and (§4.1) a name word only references an installed slot whose upload is in step 1
of this same VBlank (or already resident from a prior frame).

---

## 7. Pinned/reserved initialization (fixes issue #6)
At **cache reset (gameplay entry)**:
- `fg_state[0]=RESERVED`; slot 0 is the blank tile, **never allocated**, and is the value `fg_cache_resolve`
  returns for pending/overflow/blank cases. (VRAM slot 0 must contain a transparent/blank pattern — ensure the
  prewarm or init writes it.)
- HUD-digit slots (`VRAM_TILE_BASE` region, ~slots 1..3) → `fg_state=RESERVED`, excluded from `fg_cache_alloc`.
- **Text/HUD-font tiles** (`extract_text_writer_tiles`, ~60 codes incl. 0x20): for each such code, at reset
  pre-install a pinned entry — allocate a fixed low slot, `fwd[code]=slot`, `fg_cache_rev[slot]=code`,
  `fg_state[slot]=PINNED`, upload its pattern during prewarm. `fg_cache_resolve` then finds these RESIDENT/
  PINNED → returns the pinned slot (no duplicate, never 0). `fg_cache_alloc` skips PINNED/RESERVED slots.
- If a pinned code appears in FG/BG map data, resolve returns the pinned slot (step 1). The generator still
  supplies the text-tile *set* (for the pin list) and the `0x21/0x2D` special-glyph invariant is preserved by
  pinning those glyphs' slots.

---

## 8. ABI contract for `fg_cache_resolve` (fixes issue #5)
The producer sites are hot; register safety is specified, not inferred:
- **Input:** `d3.w` = arcade tile code (caller has already `andi.w #0x3FFF` — or resolve masks defensively).
- **Output:** `d3.w` = Genesis tile slot (0..1003; 0 = blank for pending/overflow).
- **Clobbered:** `d3` only (the output).
- **Preserved:** **all** other registers — `d0–d2, d4–d7, a0–a6, CCR-not-relied-on`. Implement by
  `movem.l` saving every scratch register the body uses (and the hash/alloc helpers it calls) at entry and
  restoring at exit. In particular `a2` (old LUT base) is preserved even though it's no longer used for the
  read, so no callsite that later reuses `a2` breaks.
- **Stack:** uses the stack for the `movem` save/restore and the `bsr` return address; bounded, no alloca.
- **May call subroutines:** yes (`fg_hash_lookup`, `fg_cache_alloc`, enqueue) — all must obey the same
  preserve-all-but-scratch discipline internally; the outer `movem` covers them.
- **Callsite safety:** replaces exactly the `move.w 0(%a2,%d3.w),%d3` read; the only cross-read register
  contract at those sites was `d3` in→out (and `a2` as LUT base). With d3-only clobber + a2 preserved, it is
  safe at all five sites. Cody must confirm no site relies on CCR flags set by the old `move.w` (they do not —
  each site follows with `or.w`/`add.w` that set their own flags).

---

## 9. Build / test plan + success criteria (fixes issues #4 and #7)
**Build only after this rev is accepted.** Generator (`precompute_pc080sn_tile_lut.py`): drop the Build-0299/
0300 per-segment cave scenes (4/5/6/7/8) + selector; keep the pattern source and the text/HUD tile *set* (pin
list); title/endround keep static preload. Update canonical coverage/opcode invariants. Runtime: implement
`fg_cache_resolve`/`fg_cache_alloc`/hash/`vdp_commit_streamed_tiles`/prewarm/BSS; wire the VBlank order (§6);
convert the LUT sites; remove the per-segment selector + its `load_scene_tiles` ids. **RAM check (blocking):**
place the ~8 KB hash (or 32 KB direct only if the linker map proves it) with no collision. Release → GATE_PASS
→ this is **Build 0301**.

**Detector additions (test tooling, `genesistrace.lua`) — mirror Plane A onto Plane B:**
- keep `staged_fg_buffer` → `LIVE_PLANE_A_PATTERN_OVERWRITE` + `PA_STAT`;
- add `staged_bg_buffer` → `LIVE_PLANE_B_PATTERN_OVERWRITE` + `PB_STAT` (live/stable/name-churn);
- add `FG_CACHE_STAT` (from the cache BSS, read via the maincpu space): occupancy (non-FREE non-reserved
  slots), new-uploads/frame, pending/overflow count, evictions/frame, **`fg_evict_live_attempts`**, and the
  **live-slot count** the runtime derived from its §5.1 staged-buffer scan;
- add an **independent detector cross-check**: the detector itself scans `staged_fg_buffer` + `staged_bg_buffer`
  each sample, decodes referenced slots, and verifies that **no slot it observes as referenced by either plane
  was evicted/reassigned that frame** (i.e. the runtime's live proof matches an outside observer's).

**Build 0301 success criteria (all required):**
1. cave visual tiles **materially corrected** (cave cells resolve to cave patterns, not outdoor);
2. outdoor visual tiles **not regressed** (same tiles; 0 overwrites);
3. **0 `LIVE_PLANE_A_PATTERN_OVERWRITE` AND 0 `LIVE_PLANE_B_PATTERN_OVERWRITE`** while stable slots are
   evaluated;
4. **no unresolved/stale tile slots after initial population** (prewarm covers frame-1; steady-state cells are
   correct-or-blank, never stale) — `FG_CACHE_STAT` pending returns to 0 after entry;
5. **no upload-queue overflow in normal steady state** (`fg_upload_overflow` ≈ 0 after prewarm);
6. **zero attempted live-slot evictions** — `fg_evict_live_attempts == 0`; every eviction is of a slot NOT
   referenced by either the current Plane-A or Plane-B staged snapshot (§5.2), proven by the live scan, not by
   touch age;
7. **live-slot count (from the §5.1 staged-buffer scan) ≈ visible occupancy** and ≈ the cache occupancy
   (≈400–500), well under 940 — confirms the live proof tracks real visibility;
8. **sprites still cannot collide** — Cache B unused, slots 1024+ untouched (structural).

**Test route:** headless reproduces seg 1→2→3 (+ outdoor); interactive optional. PA_STAT/PB_STAT names stay
low-churn (scroll edge only).

## 10. Out of scope
Missing cave-entrance block: deferred. Rope: expected fixed by streaming; verify, don't special-case; if still
wrong, record `Rope: DEFERRED`. Collision, HUD sprites, palette: unchanged.

**Next step:** review rev 2; on acceptance, implement exactly this and produce the first numbered ROM as
Build 0301.
