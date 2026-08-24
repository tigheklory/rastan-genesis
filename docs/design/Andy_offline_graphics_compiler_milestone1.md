# Andy — Offline Graphics Compiler, Milestone 1 (implemented)

**Type:** tool implementation. No production runtime change, no ROM, Build 0302 not consumed.

## What was built
`tools/translation/compile_pc080sn_genesis.py` — an offline arcade→Genesis PC080SN graphics compiler
that **evolves** (imports, does not duplicate) the decoders in `precompute_pc080sn_tile_lut.py`. Build
target: **`make -C apps/rastan-direct pc080sn-compile`**. Inputs are arcade/project data only —
`build/regions/{maincpu,pc080sn}.bin` + `specs/palette_decisions.json`. **No trace/screenshot/route
input** (verified: 0 production trace dependencies; the only grep hit is a docstring comment).

## Pipeline (all from arcade data)
1. **Map-stream progression walk** — decodes the forward segment progression from the arcade tables
   `0x5073A` (stage→start segment), `0x50EE0` (segment→stream offset), `0x50F6B` (selector stream;
   direction bytes 0/1/2 advance, event 4/6/7 freeze). No recorded route used.
2. **Per-segment Plane-A tile sets** via the reused strip-source/metatile decoder.
3. **Graphics epochs** — coalesces consecutive segments into the coarsest epoch whose resident tile
   set fits the sprite-safe plane band.
4. **VRAM slot allocation** — tile-lifetime with slot reuse (retain across consecutive epochs, free
   when a code leaves, reallocate on return); band **64..703** (0..63 reserved; sprites at 1024;
   Plane-B region reserved above). Self-validating (no two live codes share a slot; nothing enters
   sprite space).
5. **Repacked Genesis patterns** (DMA-ordered), **base LUT + per-epoch patches**, **DMA transition
   runs**, **palette route** (registry proven/decided only), generated **metadata + docs**.

## Actual compiler-derived results
- Segments decoded: **139** · Epochs: **23** · Granularity: per-arcade-segment coalesced to fit the
  band (coarsest safe), derived from the map-stream tables + strip-source structure.
- Plane-A peak unique patterns: **579** · Peak combined resident (A+text): **638 / 640** · Avg
  occupancy: **527**.
- Generated pattern data: **246,912 bytes** (repacked for DMA).
- LUT: flat `0x4000`-word base (**32,768 bytes**) + per-epoch (code,slot) patches (largest **940**,
  avg **662**).
- Largest transition: **537** new patterns / **17,184** bytes; avg new/transition ≈ high (see below).
- Palette route rows (proven/decided): **2**; unresolved registry rows: **4**.
- **Self-validation: PASS** · **Deterministic rebuild: PASS** (byte-identical across delete+rerun) ·
  **Trace inputs: 0**.

## Generated assets (`build/pc080sn_genesis_compiled/`)
`patterns.bin`, `lut_base.bin`, `lut_patches.inc`, `dma_transitions.inc`, `epochs.json`, `epochs.inc`,
`cram_epochs.bin`, `cram_transitions.inc`, `palette_route_epochs.inc`, `report.json`. Docs:
`docs/generated/pc080sn_genesis/stage1_epochs.md` (byproduct of the same model — one source of truth).

## Honest decoder gaps (classified, not faked)
- **Stage-1 scoping imperfect (DECODER_SEMANTICS_UNPROVEN):** the walk followed direction bytes for
  139 segments (whole forward run) rather than stopping precisely at the Stage-1 boundary — the
  `a5@0x1242` stage-index granularity (0x5073A targets step by 4) is not yet pinned. The pipeline is
  correct; the *range* over-covers. Fixing the exact stage bound is a bounded decoder task.
- **Plane B (DECODER_SEMANTICS_UNPROVEN):** M1 reserves a bounded Plane-B region (320 slots) and
  compiles Plane A fully; per-segment BG streaming is deferred (the whole-stage BG set 854 does not
  fit as a constant — confirming both planes must stream).
- **CRAM colour contents (DECODER_SEMANTICS_UNPROVEN):** arcade palette-RAM source not yet decoded;
  M1 emits palette *line routing* from the registry, not per-line colour words.
- **Sprite coexistence (DECODER_SEMANTICS_UNPROVEN):** static enemy/spawn model not decoded; sprite
  routing comes only from `palette_decisions.json` (no trace-derived family list).
- **DMA minimization:** retention is consecutive-epoch only; the 537-pattern largest transition is
  large — cross-gap retention + finer/greedier epochs would reduce it (Milestone-1 correctness first).

## Recommended Milestone 2 (thin runtime contract)
Replace `fg_tile_cache.s`'s per-cell hash/liveness with: **(a)** read the arcade discriminator
(segment / map-stream position), **(b)** on an epoch-boundary crossing, execute the precomputed
`dma_transitions` run(s) + apply the `lut_patches` delta + `cram_transitions`, **(c)** per cell, one
indexed `slot = active_LUT[code]` read (O(1)) — no runtime allocation/eviction. Prove it against the
same arcade route capture (validation only). Do not wire until the compiler's Stage-1 scoping + Plane-B
+ CRAM colour gaps above are closed enough to drive the real screen.
