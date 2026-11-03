# Andy — Current Gameplay Avoidable Runtime-Calculation Audit

**Date:** 2026-10-18 · **Type:** READ-ONLY architecture/performance audit. **No** production source,
Makefile, generator, ROM, MAME, trace, build-number/counter change. Phase D/E not started. Output:
this doc + one `AGENTS_LOG.md` entry only.

## 1. Repository state actually audited

- **Current HEAD:** `4ae4d82262845d36fdbaad22f886997cd8fd2713` ("Record Build 0452 source commit").
- **git status:** clean of production changes; the only working-tree deltas are my prior read-only
  decompilation/doc additions (`analysis/decompilation/c/rastan_attract_item_description.c`,
  `raw/0005607c.c`, several `docs/design/Andy_*.md`, coverage/README). No production source modified.
- **Current build/source state:** counter = **452**; Build 0452 source present (commit `8cf04c69`
  "Build 0452 eliminate BEST-5 runtime address arithmetic") on top of accepted Build 0451
  (`cc8787f6`, locked by `c61f062e`).
- **Accepted baseline:** Build **0451** (`070bbee9…`); `_invincible` rope 798/798/798. Build 0452
  (`7dc9230c…`, same 798 rope) is a candidate; **not upgraded to accepted here**.
- **Build 0452 present:** YES.
- **Files treated as authority:** `apps/rastan-direct/src/{pc090oj_hooks,tilemap_hooks,fg_tile_cache,
  vdp_comm,dma,palette_hooks}.s`, the generators under `tools/translation/`, generated
  `build/*`/`out/*`, `build/rastan-direct/address_map.json`, linker symbols. Prior reports = history.
- **Historical reports found stale:** the "universal ten-byte per-piece interpreter" sprite audit
  (retired Build 0407, §3B); the "Plane B calls `fg_boundary_resolve_b` 32×/column" claim (hoisted
  Build 0434, §3C). Both corrected below from current source.

## 2. Current gameplay presentation pipeline (CURRENT labels)

```
arcade gameplay worker (jmp 0x3A208, runs AFTER the VBlank publish)
  ├─ sprite dispatch hooks 0x41DAE/0x45DFA -> pc090oj_native_emit_pass (.Lnq_gameplay)
  │     ├─ (HUD mode 2) .Lnq_project_p1_hud  -> native_queue_hud           [ARCADE SEMANTIC input; presentation build]
  │     ├─ per-actor piece emit:
  │     │     .Lnative_generic_frame_try  (generated 4096-byte base LUT -> O(1) class -> finalized frame)
  │     │     .Lnative_death_frame_try    (compact death stream; 0x0A73/0x0275/0x0A5A)
  │     │     .Lnative_universal_general_try (generated O(1) index; NOT the old interpreter)
  │     └─ .Lnq_emit_lane x6 lanes -> .Lnq_emit_entry (shared finalizer) -> staged SAT (double-buffered)
  │           finalizer: code identity -> blank bitset -> opaque bbox ptr -> 9-bit X/Y wrap ->
  │                      flip -> origin offset -> viewport bbox clip -> residency -> SAT record
  ├─ tilemap hooks -> .Lplane_a/.Lplane_b_publish_logical_row_native (on crossed rows) -> staged_fg/bg_buffer + dirty rows
  └─ scroll hooks -> staged_scroll_*  ; palette hooks -> staged_palette_words (+ palette_pending)
VBlank _vblank_service -> dma_publish_frame: palette(gated) / tiles(dirty) / Plane B(dirty) /
  Plane A(dirty) / sprite tile-worklist(<=12) + SAT DMA(640B, unconditional) / scroll
```

Stage classification (current):

| Stage | Classification |
|---|---|
| actor lifecycle/state/AI/anim selection/positions/collision | ARCADE SEMANTIC (must remain runtime) |
| generated base-LUT classification + finalized-vi index | NECESSARY GENESIS PRESENTATION (already generated/O(1)) |
| `.Lnq_project_p1_hud` queue rebuild | CHANGE-DRIVEN CANDIDATE (per-frame today; §3A) |
| `.Lnq_emit_entry` geometry (X/Y+dx/dy, flip, wrap, clip) | NECESSARY GENESIS PRESENTATION (genuinely dynamic) |
| opaque-bbox source pointer reconstruction | possible per-piece HOISTABLE/duplicate (§3E) |
| Plane A/B row producers | NECESSARY (already hoisted per-row, Build 0434/0439) |
| residency / tile-DMA worklist (<=12) | NECESSARY GENESIS PRESENTATION |
| unconditional SAT DMA (640B) | NECESSARY in gameplay (sprites move); CHANGE-DRIVEN only for static lanes |
| palette (gated), tiles/plane (dirty) | already change-driven |

## 3. Previously suspected opportunities — current verdict

### A. Gameplay reduced 1UP / P1 score HUD
**Status: STILL EXISTS.** `.Lnq_project_p1_hud` (pc090oj_hooks.s:2616) is called **unconditionally
every gameplay frame** (`.Lnq_gameplay:2580`, HUD mode 2). It clears `native_hud_count`, re-reads the
3 live BCD bytes at `0xFF011E/011F/0120`, re-extracts 6 nibbles, re-emits 6 digit sprites + 3 fixed
label sprites (`0xD039/D048/D046`) into `native_queue_hud` — no score-change gate.
**Current cost:** producer CPU = ~6 nibble extracts + 9 `native_sprite_emit_fast` calls/frame; the
finalizer then re-processes those ~9 queue entries into the SAT (`.Lnq_emit_lane`), and the SAT is
DMA'd unconditionally. **Rope relevance: LOW** — on the pre-rope route the P1 score is ~0, so after
leading-zero suppression the HUD is ~1–2 digits + 3 labels; the producer saving is tens of cycles,
not a frame. **Safe optimization:** cache `native_queue_hud` (and a `hud_score_shadow` = the 3 BCD
bytes); when the shadow is unchanged, skip the `.Lnq_project_p1_hud` rebuild (the finalizer still
emits the cached queue). Saves producer CPU only; the live BCD remains authoritative (never
hard-coded). Finite BCD domain → STRONG static proof. Benefit is modest; include only as a low-risk
cleanup.

### B. Universal sprite record interpretation
**Status: CHANGED / effectively FIXED (Build 0407).** The old per-piece "universal ten-byte
interpreter" is retired: `pc090oj_hooks.s:1013-1022` states the former fallback parser is gone and "a
generated miss owns no output; it must never re-enter arcade descriptor/piece-stream parsing."
**Current representation:** generated **4096-byte base LUT → O(1) classification → one usage
descriptor → finalized vi** (`.Lnative_generic_frame_try`), with a compact death stream and the
generated `.Lnative_universal_general_try` index. **Reachable records:** go through the generated O(1)
classifier; there is no runtime frame-record scan (reject cost is O(1), not O(records)).
**Static/dynamic:** piece geometry/identity are **already baked** into finalized-vi records; the only
per-piece runtime left is the finalizer geometry (§3E), which is genuinely dynamic. **The old
"Four-Armed base 0x02E8" conversion proposal is obsolete** — the general path is already generated.

### C. Plane-B horizontal / directional column residency
**Status: ALREADY FIXED (Build 0434).** The gameplay Plane-B row producer
(`.Lplane_b_publish_logical_row_native`, tilemap_hooks.s:1351) loads `fg_boundary_active_lut` **once**
(1384) and uses an inline **cached source-group** (`14(%sp)`/`16(%sp)`), re-deriving the group only
when it changes — it does **not** call `fg_boundary_resolve_b` per cell. (`fg_boundary_resolve_b` at
:130 is in the **frontend C-window fill hook**, not the gameplay path.) **Current setup count per
crossed row:** one LUT base load + one cached-group check per group change + one `divu.w #6` row-index
computation (1378, per-row, already hoisted out of the cell loop). **Safe hoist:** none material
remaining; the per-row `divu.w` is low-frequency (crossed rows only) — not worth a reciprocal rewrite.

### D. Remaining runtime address / offset conversions
**Status: mostly ADDRESSED.** Build 0452 removed the BEST-5 `source − 0x0010C000` conversion; the
KF-036/KF-044 raw-WRAM-literal class was fixed at known gameplay sites (`0x10C242`/Build 0366,
`0x10C508`/0386, `0x10D2A8`/0440, BEST-5/0452). **Occurrences in normal-gameplay hot paths:** none
newly found — gameplay work state is addressed **A5-relative** (legitimate `A5 + displacement`, not
"calculation"), and retained-code absolute operands are handled by the declarative shift/relocation
pipeline. The remaining raw-literal instances in the tree are **frontend/attract/itempage**
(`0x10D000/0x10D100`, documented separately) — **out of gameplay scope**. No gameplay
subtract-base/add-base rebase remains to convert. (Do not replace A5-relative addressing with magic
Genesis absolutes.)

### E. Shared sprite finalizer (`.Lnq_emit_entry`)
**Current avoidable work:** (1) a per-piece **opaque-bbox source pointer reconstruction**
(`andi #0xFFF; lsl #4; lea pc090oj_opaque_bbox` at `.Lnq_identity_validated`) — the comment at that
site notes "Build 0409 reconstructed this same source a second time below," i.e. the code/source is
derived twice on some paths; consolidating to one derivation would save a few cycles **per piece**
(the only genuinely per-piece-frequency item found). (2) The code-identity branch ladder (bits
12/13/15 + blank-code bitset) runs per piece, but is data-driven by the piece's own code word and is
short for finalized-vi records. **Necessary work (do NOT remove):** 9-bit X/Y wrap, actor X/Y + dx/dy
(legitimate dynamic), flip mapping, origin offset, **viewport bbox clip** (off-screen rejection —
correctness), residency lookup, used-cell marking, DMA worklist, SAT record/link, lane ordering,
80-entry capacity. These own clipping/residency/ordering/palette/SAT-link correctness and must stay in
the shared finalizer.

## 4. Newly discovered opportunities

**Name: per-piece duplicate bbox/source derivation in the finalizer.**
Current path: `pc090oj_hooks.s` `.Lnq_emit_entry` (`.Lnq_identity_validated` / `.Lnq_bbox_source_ready`).
Why unnecessary: the piece code is masked/shifted and the opaque-bbox base is derived on more than one
path for the same piece (Build-0409 comment). Arcade semantics preserved: identical bbox/geometry.
Build-time/hoisted representation: compute the bbox pointer once and carry it; or bake the bbox index
into the finalized-vi record so no `andi/lsl/lea` is needed per piece.
Expected CPU significance: **LOW–MEDIUM** (per-piece frequency × many pieces/frame, but only a few
cycles each). Risk: LOW. Static proof: old-vs-new per-piece SAT/bbox record comparison over all
finalized vi (STRONG).

**Name: HUD lane re-emission into the SAT when unchanged (extends §3A).**
Current path: `.Lnq_project_p1_hud` + `.Lnq_emit_lane` over `native_queue_hud`.
Why unnecessary: on an unchanged-score frame the HUD queue and its SAT entries are byte-identical.
Build-time/hoisted representation: a `hud_sat_valid` + `hud_score_shadow` gate that reuses the cached
HUD queue (and, in a later change-driven SAT model, its cached SAT entries). Expected CPU: LOW
(rope route HUD is tiny). Risk: LOW. Proof: finite BCD domain (STRONG).

No other per-frame gameplay recomputation of material size was found: the sprite identity/piece
geometry is already generated/baked (Build 0403–0407), Plane A/B are hoisted per-row (0434/0439),
palette is `palette_pending`-gated, plane/tile DMA is dirty-gated, and the SAT DMA volume (640 B) is
genuinely dynamic in gameplay. **The gameplay pipeline is already near its efficient floor.**

## 5. Complete ranked table

| Rank | Candidate | Subsystem | Frequency | Runtime removed | Runtime retained | ROM | WRAM | VRAM | CPU opp. | Rope | Risk | Verifier | Current-tree evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Finalizer duplicate bbox/source derivation | sprite finalizer | per piece | 1 masked derive/piece on dup paths | all geometry/clip | ~0 | 0 | 0 | LOW–MED | YES | LOW | STRONG | `.Lnq_emit_entry` + Build-0409 comment |
| 2 | HUD rebuild change-gate (A) | gameplay HUD | per frame | ~9 emits when score unchanged | live BCD read when changed | small | +4 (shadow) | 0 | LOW | LOW | LOW | STRONG | `.Lnq_project_p1_hud:2616` unconditional |
| 3 | HUD SAT-lane cache | finalizer/HUD | per frame | HUD lane SAT re-emit when unchanged | dynamic lanes | small | small | 0 | LOW | LOW | MED | MODERATE | depends on change-driven SAT |
| 4 | Plane-B per-row `divu.w #6` | Plane B | per crossed row | one divide/crossed row | index semantics | small | 0 | 0 | LOW | YES(low) | MED | STRONG | tilemap_hooks.s:1378 |

(No HIGH-CPU candidate exists in the current tree; see §6 DO NOT PURSUE.)

## 6. Safe / moderate / reject

### SAFE / LOW-RISK
1. **Finalizer duplicate bbox/source derivation** — derive once / bake the index; per-piece, provable
   by SAT-record equivalence.
2. **HUD rebuild change-gate (A)** — cache the reduced HUD queue when the 3 BCD score bytes are
   unchanged; live BCD stays authoritative; finite-domain proof.

### MODERATE-RISK
1. **HUD SAT-lane cache** — only beneficial inside a broader change-driven SAT model; touches SAT
   ownership (ordering/capacity) → moderate.
2. **Plane-B `divu.w` → reciprocal/index** — low frequency; a reciprocal multiply or maintaining the
   walker as an index changes a semantic representation → moderate for little gain.

### DO NOT PURSUE
1. **Change-driven SAT for moving gameplay sprites** — most sprites move every frame; the SAT
   genuinely changes; gating it risks ordering/residency/clip correctness for near-zero gain.
2. **Bypassing the shared finalizer for "direct SAT"** — would break clipping/residency/ordering/
   palette/SAT-link/capacity. Rejected.
3. **Re-deriving the retired universal interpreter or the old Four-Armed conversion** — obsolete;
   path is already generated/O(1).
4. **Replacing A5-relative gameplay addressing with Genesis absolutes** — not a calculation problem;
   would reintroduce magic addresses.

## 7. Recommended next implementation

**Candidate:** consolidate the **per-piece duplicate bbox/source derivation** in the shared finalizer
(bake the opaque-bbox index into the finalized-vi record, or derive the pointer exactly once and carry
it), eliminating the redundant `andi/lsl/lea` on the duplicated path.

- **Exact source boundary:** `apps/rastan-direct/src/pc090oj_hooks.s` `.Lnq_emit_entry`
  (`.Lnq_identity_validated` → `.Lnq_bbox_source_ready`), plus the generated finalized-vi record
  shape if the index is baked.
- **Exact generated/build-time boundary:** the sprite-frame generator that emits finalized-vi records
  (so the bbox/opaque index is a baked field rather than re-derived at runtime).
- **Arcade-owned state preserved:** all — only presentation geometry derivation is touched; actor
  state, positions, flip, clip semantics unchanged.
- **Genesis work removed:** one masked pointer reconstruction per piece on the duplicated path.
- **Runtime work remaining:** actor X/Y + dx/dy, flip, 9-bit wrap, viewport clip, residency, SAT
  build (all genuinely dynamic).
- **ROM/WRAM/VRAM change:** ROM ~0 (maybe a wider finalized-vi record field); WRAM 0; VRAM 0.
- **Rope-route relevance:** YES (runs for every rendered piece throughout gameplay).
- **Required verifier:** old-vs-new per-piece SAT/bbox record comparison over **all** finalized vi
  (exhaustive generator equivalence) + final-ROM disassembly showing the duplicate derivation gone.
- **Required Tighe hardware validation:** gameplay sprite positions/clipping unchanged (visual).
- **Why preferable to the runner-up (HUD gate):** it is **per-piece** (rope-relevant across the whole
  route) whereas the HUD gate saves tens of cycles on a near-empty pre-rope HUD; both are low-risk,
  but this one touches the genuine hot path with an equally strong static proof.

> Honest caveat: the current gameplay pipeline is already heavily optimized (Builds 0403–0452). **No
> candidate found promises a HIGH CPU / multi-frame rope win.** Before investing further
> micro-optimization, the highest-value step is actually a **profiling read** using the existing
> `profile_native_*` symbols (`profile_native_universal_entry/index_lookup/frame_ready/piece`,
> `profile_native_levelb_entry`, `profile_native_geometry_entry`, `profile_native_bbox_entry`, …) to
> measure which finalizer/producer stage dominates on the rope route — so the next optimization is
> evidence-ranked rather than guessed. (That measurement is a separate, authorized-run task; not done
> here.)

## 8. Longer-term queue (no implementation authorized)

1. **Profiling pass** via the existing `profile_native_*` symbols on the `_invincible` rope route to
   rank finalizer vs producer vs Plane A/B vs DMA by measured cost.
2. **HUD rebuild change-gate (A)** once (1) confirms it is non-trivial.
3. **Plane-B per-row index** reciprocal/representation change only if profiling shows row-crossing
   setup is material on the rope route.
4. **Change-driven SAT for static-only lanes** (HUD / any proven-static sprite) — only within a safe
   SAT-dirty contract that preserves ordering/residency/capacity.
5. **Finalized-vi record widening** to bake more static per-piece fields (bbox index, flip/attr
   invariants) if (1) shows the finalizer's per-piece identity ladder is hot.

## FINAL STATUS

Production modified: NO. ROM built: NO. MAME run: NO. New trace: NO. Build number consumed: NO.
Build counter changed: NO. Phase D: NO. Phase E: NO.
