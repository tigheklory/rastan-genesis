# Andy — CHECKPOINT H10: Materialized Actor Rendering + Palette Decompilation

**Agent:** Andy · **Type:** Static reverse engineering (ORIGINAL ARCADE 68000) + report update.
**Build counter:** 360 (unchanged). **NO ROM, NO MAME, NO Genesis change.** Cody files untouched.
**Artifact:** republished (Version 4) at `https://claude.ai/artifact/Dopg3mwMHdUMsZJSQgXDVR`.

Mandatory RULES.md standalone report for CHECKPOINT H10. Goal: replace the H5/H6 materialized
actors' **RAW TILE EVIDENCE** placeholders with **legal, arcade-assembled sprites in real arcade
colours**, by decompiling the actual render-dispatch and palette-attribute chain. Authoritative
source: `build/regions/maincpu.bin` (+ `pc090oj.bin`). Reconstructed C is auditable, NOT Taito source.

---

## A. Materialized actor render-dispatch architecture

Per-actor render loops (`0x41DAE`…) load `d0 = +0x01` (anim), `d6 = +0x20` (mirror), `d7 = +0x02`
(facing) and call **`0x3D054`**:

```
0x3D054: d0 = anim*2; d1 = +0x38 (compositor SELECTOR)
   selector 1 -> jmp 0x4770E (table 0x4771C)
   selector 2 -> jmp 0x3F0BC (table 0x3F0CE)
   selector 3 -> jmp 0x3FFDC (table 0x40004)
   selector 4 -> jmp 0x3FFF0 (table 0x4002C)
   selector 0 -> program = 0x3D09E + word[0x3D09E + anim*2]; jmp 0x3C902
```

**Key proof:** every non-zero selector target (`0x4770E`/`0x3F0BC`/`0x3FFDC`/`0x3FFF0`) is an
identical thunk that indexes its own program table by anim and `jmp/braw 0x3C902` — **the same
general compositor interpreter**. So the selector only chooses the *program table*; the interpreter
is shared across all five. Raw: `raw/0003d054.c`, `raw/0003f0bc.c`. Semantic: `rastan_actor_render.c`.

## B. Animation → compositor selection path

`program = COMPOSITOR_TABLE[selector] + be16(COMPOSITOR_TABLE[selector] + anim*2)`, with tables
`{0:0x3D09E, 1:0x4771C, 2:0x3F0CE, 3:0x40004, 4:0x4002C}`. The offline `compositor_vm.py` already
implements this exact indexing and the 0x3C902 control-byte interpreter, so once the correct
`(base, anim, selector)` is supplied the frame assembles deterministically.

## C. Compositor modes actually used by the H5/H6 actors

The materialized actors overwhelmingly use **compositor selector +0x38 = 2** (set at
`0x436D2`/`0x437A4`/`0x438D6`/`0x439C4`/`0x43D50`/`0x43D82`/`0x441E6`/`0x44240` …), a few use 0
(retarget-inherited). All 12 extracted `(base, anim, selector)` triples produce **general programs**
(control bytes 0x00/0x40/0x70/0x80) — **none hits an unimplemented special control mode**. So no new
compositor handler had to be written; the "special program modes" caveat does not apply to this cast.

## D. Newly decompiled compositor handlers

None required — the four selector thunks (§A) were the only render-dispatch code between the actor
record and 0x3C902, and they are trivial table-index+branch thunks (now in C). The 0x3C902 general
interpreter was already validated.

## E. Materialized actor legal-frame table

`analysis/actor_decompilation/h10_materialized_frame_programs.tsv` — one row per actor with
`base, anim, selector, program_addr, piece_count, palette_line`. All 12 assemble (4–13 pieces):

| base | anim | sel | program | pieces | pal line |
|---|---|---|---|---|---|
| 0x0224 | 0x07 | 2 | 0x3F275 | 4 | 0x1 |
| 0x0179 | 0x70 | 2 | 0x3FBE4 | 8 | 0x1 |
| 0x09F6 | 0x00 | 2 | 0x3F1D4 | 10 | 0x1 |
| 0x0DAB | 0x74 | 0 | 0x3E204 | 13 | 0x4 |
| 0x09EA | 0x74 | 0 | 0x3E204 | 13 | 0x4 |
| 0x00F4 · 0x0266 · 0x0235 · 0x01FC · 0x0236 · 0x0546 · 0x05E9 | 0x00 | 0 | 0x3D298 | 9 | 0x4 |

(anim=0 for the retarget-inherited bases is a **frame-0 representative** — the clean explicit
`(base,anim,sel)` triples are 0x0224/0x0179/0x09F6/0x0DAB.)

## F. Palette assignment architecture

**`0x45684`** resolves the palette line into `+0x27` (raw `raw/00045684.c`, semantic
`rastan_actor_palette.c`):

```
family(+0x3E) != 2 : nibble = tbl_0x45722[(round-1)*12 + family]
family(+0x3E) == 2 : nibble = tbl_0x456EC[variant(+0x752)*18 + (round-1)*3 + comp_adj]
                      comp_adj = (+0x38 >= 3) ? +0x38-2 : +0x38
+0x27 |= (nibble | 0x40)     (bit6 = "use +0x27 low nibble as PC090OJ line")
```

Final 16 colours = the per-round ROM palette `0x3BA88[round-1][nibble] → pool → 0x4FD02` — the same
`rom_field_palette(round, nibble)` the field actors use. Both nibble tables are preserved byte-exact.

## G. Palette behaviour across in-place transformations

Everything the `0x033E` hunter materializes is **family-2**, so its palette line comes from
`0x456EC`. The in-place base transforms (H5/H6: `0x40E9C`, `0x40F82`, `0x40FAC`, …) rewrite `+0x1E`
but **do not re-run `0x45684`** — they only touch `+0x1E`/`+0x0D`/`+0x01`. Therefore the transformed
sprite **retains the hunter's creation-time palette line** (`+0x27`); only its graphics base changes.
This is proven, not assumed.

## H. Per-round palette-instance results

The family-2 line is **round-specific** (table row `(round-1)*3`) and variant/comp-specific. Because
the materialized cast's exact round is still PENDING (they are not round-pinned), the exact palette
instance is **PARTIAL**: the bestiary renders each with the **round-1 representative** family-2 line
(comp 2 → line 0x1; comp 0 → line 0x4) and labels it *"round-representative · ROUND PENDING"*. The
data model (`render.palette = {kind:'materialized_fam2', round, nibble}`) already permits a distinct
per-round instance the moment a round is pinned.

## I. Actor-by-actor visual reconstruction status

All 12 materialized actors: **FRAME LEGAL (VM)** + **PALETTE PARTIAL (round-representative)** —
category **B** (frame legal, palette pending exact round). The controller `0x033E` stays **FRAME
PENDING** by design (it is the hidden scanner, not a sprite). No materialized actor remains RAW-TILE.

## J. Exact remaining frame/palette blockers

- **Palette:** exact per-round instance blocked only on pinning each materialized actor's round
  (same 0x7E-door / progression blocker as the phase work) — the palette math itself is proven.
- **Frame:** the 6 retarget-inherited bases render frame-0; their per-state animation index (the
  exact idle/attack frame) would come from walking each H5 state handler's `0x3CEB0` sequence — a
  refinement, not a blocker (a legal frame already assembles).

## K. C files created / updated

- `raw/0003d054.c` (COMPLETE) — render selector dispatch.
- `raw/0003f0bc.c` (COMPLETE) — selector thunks (2/1/3/4) → shared 0x3C902.
- `raw/00045684.c` (COMPLETE) — palette-attribute resolver + both nibble tables.
- `rastan_actor_render.c`, `rastan_actor_palette.c` (semantic).
- `function_coverage.csv` (+3 → 70 rows / 54 COMPLETE), `historical_claim_audit.csv` (+2 → 52),
  `README.md`.

## L. Validation

- Coverage guard: **PASS** (70 rows, 54 COMPLETE; H5 10/10).
- Fidelity guard: **PASS**.
- `gcc -std=c11 -fsyntax-only`: **PASS** (71 files).
- Manifest consistency guard (`build_bestiary.py`): **PASS**.
- Compositor VM: renders all 12 materialized actors as general programs (0 special-mode failures).

## Related documents

`docs/design/Andy_h6_marker_materialization_decompilation.md` (materialization routes),
`docs/design/Andy_h8_enemy_damage_item_drop_decompilation.md` (0x3CEB0 anim core),
`docs/design/Andy_bestiary_integrity_repair.md` (the gallery this pass fills in).
Evidence: `analysis/actor_decompilation/h10_materialized_frame_programs.tsv`.
