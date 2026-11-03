# Build 0421 — Native Background Independent Audit (Andy)

**Date:** 2026-10-13 · **Type:** READ-ONLY independent audit. No production source, no ROM, no build
number, Cody's working tree untouched. HEAD = Build 0419 (accepted); the 0420/0421 changes are
uncommitted in Cody's tree and were diffed directly (`git diff HEAD`). Build 0419 is the visual
oracle; 0420 crashes; **real Genesis is authoritative over any verifier PASS.**

---

## Headline

- **Collision/visual SEMANTIC MODEL is SOUND.** Arcade relationship is **Classification B** (collision
  and visual share a descriptor/metatile source but are **independent fields**, not derived from each
  other). Cody's 64-byte record (`tile[16]` + `collision[16]`) is **shared allocation, not shared
  semantics** — it co-stores the two independent fields the arcade descriptor itself co-stores. The
  record is keyed by the **descriptor pointer**, never by a final Genesis tile/VRAM/name identity.
- **The Segment-0 regression is a bounded implementation bug: a +0x200 copy-base pointer-convention
  mismatch between the generator's record keying and the runtime's effective metatile address.** The
  runtime indexes `index[d2]` and gets a record the generator built from `data[d2]`, but the live 0419
  path reads the metatile at `SECOND_WORD_BASE(0x200)+d2 = data[0x200+d2]`. The off-by-0x200 record
  yields coherent-but-wrong Plane-A tiles (and wrong collision) at Segment 0.
- **The verifier PASS is real but tests generator-internal consistency, not runtime-key equivalence
  against the 0419 effective address** — that is the gap.
- **0420 crash correctly diagnosed and fixed** (`tst.l %a0` illegal → `cmpa.l #0,%a0`).

**Recommendation: A — architecture/record-format/semantic-model SOUND; fix the bounded record-keying
bug (and validate the 4-cell / 16-col grouping at segment boundaries; track the dynamic-collision
republish risk).**

---

## Arcade collision model

- **Authoritative storage:** `collision_map_64x64_words_base` @ `0x00FF1E00` (64×64 words), a
  **separate WRAM map** — not Plane A/B.
- **Writers:** the strip/metatile producer traversal (expands descriptor collision field → map) and
  the dynamic `collision_map_surface_mark_5a2ee` (cave-block / surface marks).
- **Readers:** `collision_map_lookup_53a2e` (arcade PC 0x53A2E) from many gameplay sites; it indexes
  the 64×64 map by **camera scroll (`A5+0x10B0/0x10AE`) + probe coords (D1/D2)** — `((D2 + (−scrollY &
  0x1FF) & 0x1F8))*0x20 + (((D1 + (−scrollX & 0x1FF))>>1)+8 & 0xFC)) >> 1`. **Collision is read by
  world/camera coordinate, never from a VRAM tile/name word.**
- **Collision derived from visual tile identity: NO.** The descriptor metatile carries 16 tile
  identities (pointer+0x00..+0x1E) **and** 16 collision words (pointer+0x20..+0x3E, uniform if
  `+0x20==0x00FF`) as **separate co-located fields**. The renderer traverses one descriptor and emits
  both products in one pass (incidental co-traversal), but the collision value is a distinct field.
- Identical visual tiles **can** have different collision (different descriptor); different tiles
  **can** share collision. Dynamic writes (cave block) change collision **without** changing the
  static tile identity.
- **Relationship: B.** Evidence: the generator reads collision from `pointer+0x20` (separate field),
  not from the tile words; the arcade reader uses the separate 64×64 map, not VRAM.

## Genesis collision model

- **Storage:** independent WRAM `collision_map_64x64_words_base` @ `0xFF1E00` (same as arcade).
- **Plane A owns collision: NO. Plane B owns collision: NO.** Collision is the separate WRAM map.
- **Gameplay reads VDP visual tile data for collision: NO** (reads the WRAM map by coordinate).
- Writers: the native entering-strip producers (`resolve_plane_a_collision_cell` /
  `resolve_plane_a_name_collision_cell`) write the map from the descriptor/record collision field;
  dynamic cave-block mark writes it directly.

## 0419 fused accessor

`resolve_plane_a_name_collision_cell` fuses the **common source-pointer / ring-unwrap / descriptor
address** work and returns the name word (D0) + collision word (D2) from one traversal. **Shared
traversal: VALID. Semantic coupling introduced: NO** — standalone `resolve_plane_a_cell` (visual) and
`resolve_plane_a_collision_cell` (collision-only, used for non-resident rows) remain; collision
storage stays the independent WRAM map. This is a cost fusion of address work, not a semantic merge.
0419 is accepted on hardware and is architecturally clean.

## 0421 generated record

- **Visual and collision physically co-located: YES** (one 64-byte record: `tile[16]` then
  `collision[16]`).
- **Semantically independent: YES** — the two arrays are read from the arcade descriptor's two
  separate fields (`pointer+0x00` tiles, `pointer+0x20` collision); neither is computed from the
  other. The uniform-collision case (`+0x20==0x00FF`) is pre-expanded to 16 copies — a convenience,
  not a coupling.
- **Shared index justified: YES** — both fields belong to the same arcade metatile descriptor, so one
  record index (the descriptor pointer) is the correct natural key.
- **Collision tied to final Genesis tile identity: NO** — keyed by descriptor pointer, not by VRAM
  slot / name word / palette-priority-flip bits.
- **Assessment:** the record FORMAT and SEMANTIC model are correct (shared allocation, independent
  fields). The bug is in how the record is *keyed/sourced* at runtime (see Segment-0).

## Plane B

- **Any gameplay collision ownership: NO.** Plane B is parallax visual only; collision is the WRAM map.
- **Historical "BG collision side-channel":** the arcade BG producer traversal, while emitting the BG
  visual product, also writes the separate collision map — a side *output* of the same traversal, not
  a property of Plane B. It never means "Plane B owns collision."
- **0421 Plane-B path safe (for collision ownership): YES** — the new Plane-B 16-column group cache
  touches only the Plane-B visual descriptor/name staging; it does not make Plane B authoritative for
  collision. (Its *visual* correctness at boundaries is a separate question — see grouping.)

## Dynamic collision — RISK (track; not the Segment-0 cause)

The generated record carries **static** collision defaults. The native entering-strip producer writes
the collision map from the record on **every republish** (scroll). The destroyable cave block mutates
collision at runtime (`collision_map_surface_mark_5a2ee`). **Risk: a scroll republish can restore the
static collision over a gameplay-modified (destroyed) cell.** This risk exists in **both 0419 and
0421** (0419 also wrote collision from the descriptor each republish), so it is not a new 0421
regression — but it must be validated (does the arcade re-mark each frame, or is the mark lost on
republish?). A native static table must never periodically overwrite dynamic collision; confirm with a
destroy-then-scroll test.

## Segment-0 regression — ROOT CAUSE (bounded keying bug)

**Reproduced/explained: YES (static derivation).** Constants: `ARCADE_START=0xF08`,
`GENESIS_START=0x1108` (Δ=+0x200), `SECOND_WORD_BASE=0x200`.

- **0419 effective metatile address:** `resolve_plane_a_cell` reads `d2` = the descriptor word1
  (original-relative pointer), then `movea.l #SECOND_WORD_BASE,%a0; adda.l %d2,%a0` → metatile at
  **`data[0x200 + d2]`**.
- **0421 runtime:** `.Lplane_a_native_metatile_record_from_d2` does `lea native_metatile_index,%a1;
  adda.l %d2,%a1; move.w (%a1),%d3` → indexes **`index[d2]`**.
- **Generator (`gen_pc080sn_native_metatiles.py`):** for each descriptor `pointer = be16(data,
  offset+2)` it sets `index[pointer] = id` with `record_for(data, pointer)` (reads **`data[pointer]`**)
  **and** `index[pointer+0x200] = id2` with `record_for(data, pointer+0x200)` (reads
  **`data[pointer+0x200]`**).

**Mismatch:** the runtime key `index[d2]` resolves to the record built from **`data[d2]`**, but the
correct metatile (per 0419) is at **`data[0x200+d2]`**, whose record the generator stored at
`index[d2+0x200]` — a key the runtime never uses. So every Plane-A cell via the generated path loads a
record sourced **0x200 bytes too low** (reading descriptor-table-region bytes reinterpreted as a
metatile) → **coherent-but-wrong tiles**, visible immediately at Segment-0 initial population (which
uses the entering-row block4 path). **First divergence:** the first logical cell of the Segment-0
initial fill whose descriptor word1 `d2` has `data[d2] != data[0x200+d2]` (essentially all of them).
Plane: **A** (and collision shares the same mis-keyed record). Exact mathematical assumption violated:
*the generator's base-pointer record must be sourced from the runtime's effective address
`SECOND_WORD_BASE + d2`, not from the raw `d2`.*

## Grouping assumptions

- **Plane-A four-cell grouping: CONDITIONAL.** The entering-ROW block4 path is 4-aligned (`d4` starts
  0, steps 4, spans 0..63), so within the pure vertical/initial path a 4-col block is well-formed. The
  assumption "4 adjacent logical cells share one descriptor" holds **only if** a logical 4-col block
  (col/4) never straddles two source segments under the current ring/segment alignment. At Segment-0
  startup with non-zero ring alignment this must be proven; block4 selects ONE descriptor per 4-col
  block and would smear it across a mid-block segment boundary. **Validate before accepting.** (The
  horizontal selector-0 entering-column path still uses the per-cell resolve, so it is unaffected.)
- **Plane-B 16-column cache: CONDITIONAL.** The cache (`14(%sp)` group, `16(%sp)` valid) refreshes when
  `source_group = C>>4` changes within a row and is initialized invalid before the loop, so a single
  full-row pass is self-consistent. The risk is the same boundary class: a 16-col group spanning two
  descriptors (segment boundary / non-zero alignment) returns a stale descriptor for the tail columns.
  **Validate at the Segment-0 start alignment.**

## Collision differential (mandatory)

**0419 vs 0421: DIFFERENT.** Because 0421 reads collision from the **same mis-keyed record**
(`0x20(%a0,…)` within the off-by-0x200 record), the collision words written to the 64×64 map differ
from 0419's (which read `0x20(SECOND_WORD_BASE+d2,…)`). **First difference:** the collision cell for
the first Segment-0 metatile whose `data[d2+0x20]` region ≠ `data[0x200+d2+0x20]` — i.e. the same
first-divergent cell as the visual. 0419 value = descriptor collision at `0x200+d2`; 0421 value =
bytes at `d2` reinterpreted as collision. **Do not infer collision correctness from visual** — both
are wrong here, and the collision error is a silent gameplay-physics hazard independent of the visible
tile error.

## Verifier gap

Cody's 4,733/4,733 PASS proves **`record_for(data, pointer)` is self-consistent** (the generated
record equals an independent re-read of `data[pointer]`). It does **not** prove the **runtime key
equivalence**: that for every descriptor word1 `d2` the runtime can select, `index[d2]` resolves to a
record whose 16 tiles/16 collision words equal the **0419 live-path** result at `SECOND_WORD_BASE+d2`.
**Missing invariant/test:** "for all selectable `d2`, `native_metatile_records[index[d2]]` ==
(0419 `resolve_plane_a_cell` tiles at `0x200+d2`, 0419 collision at `0x200+d2+0x20`)." Also uncovered:
the 4-cell/16-col grouping at non-zero ring/segment-boundary alignment, and initial-population
placement. The verifier checks *record contents*, not *map placement / runtime indexing*.

## 0420 crash

**Cody diagnosis: CONFIRMED.** `TST.L An` is illegal on the 68000 (TST added An operands only on
68020+); PC 0x070A72 is in the new metatile leaf. **0421 replacement legal: YES** — `cmpa.l #0,%a0`
(tilemap_hooks.s:955) computes `A0−0` and sets Z iff `A0==0`, equivalent to the intended zero-pointer
test. **Similar illegal instructions remain: NO** — the only other address-register TST was already
fixed (`move.l %a5,%d0` at pc090oj_hooks.s:2153, replacing `tst.l %a5`); no live `tst.l %an` remains.

## Performance counts

Cody's structural reductions are **PLAUSIBLE/PARTIAL** but should not be converted to cycle
percentages. The paired vertical row goes from 64 per-cell descriptor traversals to one block4 per
4-col block = **16** blocks/plane → ~16–21 descriptor traversals (plus the record-index leaf: an extra
indexed load + `cmpa` + the 4-wide stage loop per block). Raw metatile interpretation genuinely drops
(the record pre-expands tiles+collision). **Residency lookups unchanged at 128** (per-cell
`fg_cache_resolve` still runs in the block4 stage loop — I see `bsr fg_cache_resolve` per staged
word). So the real savings = removing per-cell descriptor re-walk + attr re-derivation, **not** the
residency path. **Material improvement if correctness is fixed: YES (likely)** — but smaller than a
naive 128→16 reading implies, because the per-word `fg_cache_resolve` and the new indexing/branch
overhead remain. Benchmark it rather than claim a percentage.

## Rope benchmark

**Sound: YES**, with deterministic state-variable start/stop (not host wall-clock).
- **Start:** first frame Rastan is controllable — gate on `genesistan_current_scene_id == 1` AND the
  arcade game-mode == 2 (gameplay) AND the first frame input is sampled (reuse the scene/mode gate the
  frame-timing trace already uses). Begin the frame counter there.
- **Stop:** first rope attachment — the deterministic game-state transition where the player enters the
  rope-grab state. Use the rope/climb state flag the rope work established (the `A5+0x1308`/player-state
  grab bit from the Build-0281/0365 rope lineage; confirm the exact flag with a watchpoint in the
  established rope trace). Stop on its first set.
- **Metrics:** **emulated frames** (primary) and derived **emulated milliseconds** (frames / 59.922).
  Never host wall-clock. Report gameplay-frames too (ticks), since the crawl ratio matters.
- **Trials:** deterministic input script (coin, start, hold RIGHT); 3–5 identical runs to confirm
  determinism (should be identical). Compare 0419 vs the corrected build.
- Reuse `tools/mame/scripts/native_sprite_fullgame_closeout.lua`'s input/scene plumbing; drive RIGHT
  continuously; this is pure instrumentation (no production change). Provide to Cody, do not implement
  in his tree.

---

## FINAL RECOMMENDATION — **A (architecture sound; bounded implementation bug)**

The collision/visual semantic model (Classification B), the 64-byte record format (shared allocation,
independent fields, keyed by descriptor pointer), and the 0419 fused accessor are **sound and should
be retained**. The Segment-0 regression is a **bounded +0x200 record-keying/source bug**: fix so the
runtime key `index[d2]` resolves to the record sourced from the runtime's effective metatile address
(`SECOND_WORD_BASE + d2`) — either source the base-pointer record from `data[0x200+pointer]`, or have
the runtime index `index[d2+0x200]`, consistently. **Before re-acceptance also:** (1) validate the
Plane-A 4-cell and Plane-B 16-col grouping at non-zero ring/segment-boundary alignment; (2) add the
verifier invariant (runtime-key == 0419 effective-address result); (3) test dynamic cave-block
collision survives a republish. **What may be retained:** the generator, record format, fused accessor,
0420 crash fix, Plane-B cache *structure*. **What must be changed:** the record-source/index keying
(the 0x200 convention), plus the grouping/dynamic-collision/verifier validations above.

---

**CODY TREE MODIFIED: NO. PRODUCTION MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO.**
