# Andy — H15 (durable-C): Family-2 Palette Lifetime & the Parallel A4+0x752 Variant

**Agent:** Andy · **Type:** Static RE (arcade) — durable-C completion. **NO Genesis impl · NO ROM
build · NO MAME · runtime build counter 373, unchanged.** Authoritative: `build/maincpu.disasm.txt`.

> **Scope note:** Only **§11 (Durable C is a required output)** of the H15 prompt was provided — not
> the investigative sections. §11 names the exact routines (0x4A086, 0x4544E, 0x45494, 0x45684,
> 0x4103E) and the exact behavior to prove (family-2 hunter palette lifetime, 0x4103E
> preservation, the parallel A4+0x752 byte), which is the dependency my H14 report flagged
> ("variant 0 assumed"). This report executes that durable-C work. If H15's §1–10 intended a
> different scope, say so and I'll adjust.

---

## The proven finding (palette lifetime)

Tracing the family-2 materialized hunter's palette state end-to-end in the arcade disassembly:

1. **Creation (0x4A086):** the schedule entry's byte 2 splits into `+0x38 = e[2]&0x0F` (compositor)
   and **`A4+0x752 = e[2]>>4` (VARIANT)** — `0x4A09C: moveb d6,%a4@(1874)`. It then calls the
   template loader (0x4544E) and the palette resolver (0x45684) with **no variant argument** — both
   read `a4@(0x752)` directly (`0x4544E 0x4545A: tstb %a4@(1874)`; `0x45684 0x456C2: moveb
   %a4@(1874),d0`).

2. **A4+0x752 is a PARALLEL byte**, outside the 0x40-byte record (0x752 ≫ 0x40). It is the durable
   family-2 identity selector: it indexes the family-2 template rows (0x454BA/0x454D2/0x454EA via
   the 0x45494 branch) and the family-2 palette nibble table (0x456EC, `variant*18`).

3. **Retire/re-arm (0x4103A → 0x4092E + 0x4103E):** `0x4092E` zeroes two spans — the 0x40-byte
   record (0x00..0x3F) and a 0x20-byte companion at `record+0x702`/`+0x4E2`. **A4+0x752 lies
   outside both** (companion ends at +0x721 / +0x501), so **the variant SURVIVES**. The palette line
   `+0x27` is *inside* the record, so it is **zeroed**. `0x4103E` re-arms six fields and restores
   neither `+0x27` nor `+0x752`.

4. **0x45684 is creation-only** (single caller 0x4A0CE). The marker-chain transforms
   (0x40E9C/0x40F82/0x43B32-rebase/…) do **not** re-run it. Therefore across a transform the durable
   palette-relevant state a hunter carries is the **VARIANT (+0x752)**, not the resolved line
   (`+0x27`). A transformed actor renders with `+0x27 = 0` → `0x3C9E8` (bit6 clear) keeps the
   **compositor control-byte** palette nibble, not the creation-time 0x45684 line.

### Refinement of prior claims

- **H10** said transforms "retain the hunter's creation-time palette line (+0x27)". H15 makes this
  precise: **+0x27 is reset by 0x4092E**; what actually persists is the **variant (+0x752)**. The
  rendered palette of a *transformed* actor comes from the compositor control byte (0x3C9E8), not
  the creation-time line.
- **H14** resolved the materialized bases assuming *variant 0*; H15 proves the variant is
  `schedule[2]>>4` (a real per-actor field). The H14 palette-instance table therefore describes the
  **creation-time** 0x45684 resolve; the **post-transform render palette** (control-byte-derived) is
  a distinct value. This is recorded as a remaining dependency, not silently overwritten.

## §11 audit result (the five named routines)

| PC | Prior status | Action |
|---|---|---|
| 0x4A086 | COMPLETE raw / PARTIAL sem | **UPDATED** — writes VARIANT to A4+0x752; loaders read it there (dropped spurious args) |
| 0x4544E | COMPLETE (GHIDRA_RAW) | **UPDATED** — reads `a4@(0x752)` (not an arg); documents the 0x45494 family-2 branch |
| 0x45494 | **MISSING** | **ADDED (COMPLETE)** — family-2 template branch of 0x4544E (fall-in `beqs 0x45454`); table by +0x38, row by +0x752, shared 0x4546E tail |
| 0x45684 | COMPLETE (H10) | **UPDATED comment** — variant lifetime + creation-only; render-palette consequence |
| 0x4103E | COMPLETE raw / no doc | **UPDATED** — documents preservation of +0x752 and non-restoration of +0x27 |
| 0x4092E (helper) | COMPLETE | **UPDATED comment** — +0x752 outside both cleared spans → persists |
| A4+0x752 (type model) | undocumented | **UPDATED** `rastan_arcade_types.h` — parallel variant byte + +0x27 lifetime notes |

## Explicit C change lists (§11)

**NEW RAW C:** none as a new file — `0x45494` is the family-2 fall-in branch of `0x4544E` (no
independent caller) and is represented in `raw/0004544e.c`; it gets its own COMPLETE coverage row.

**UPDATED RAW C:**
- `raw/0004103e.c` — palette-lifetime header + preservation semantics.
- `raw/0004a086.c` — writes `B(r,0x752)=variant`; loaders read it (arg-free); provenance.
- `raw/0004544e.c` — reads `B(r,0x752)`; documents the 0x45494 family-2 branch + 0x4546E tail.
- `raw/00045684.c` — variant-lifetime + creation-only + render-palette consequence.
- `raw/0004092e.c` — +0x752 outside both cleared spans → variant persists.

**NEW SEMANTIC C:** none (all owning modules already existed).

**UPDATED SEMANTIC C:**
- `rastan_actor_creation.c` — `sched_install_4a086` (variant → parallel A4+0x752) and
  `child_hunter_create_4103e` (preserves +0x752, does not restore +0x27).
- `rastan_arcade_types.h` — field model for the parallel A4+0x752 variant and the +0x27 lifetime.

**C FUNCTIONS PROMOTED TO COMPLETE:** `0x45494` (was MISSING → COMPLETE, family-2 template branch).

**Audited & confirmed already sufficient (reused, not duplicated):** `0x45684` (H10 resolver body
byte-faithful — comment refined only), `rastan_actor_helpers.c` / `rastan_actor_palette.c` variant
signatures (kept as an explicit model of the parallel byte, provenance documented).

## Validation

- `gcc -fsyntax-only` **PASS** (100/100). Coverage guard **PASS** (100 rows, 86 COMPLETE, 10/10 H5
  handlers). Fidelity guard **PASS** (100 coverage / 65 audit rows). `historical_claim_audit.csv`
  +1 H15 reconciliation row.
- Runtime build counter **373 → 373**; no ROM build, no MAME, no Genesis-runtime change.

---

# H15 continuation — Exact post-transform DISPLAY palettes

## R. Post-transform renderer path (proven)

`actor +0x38 → 0x3D054 (COMPOSITOR_TABLE[sel]) → program = table + be16(table + anim*2) → 0x3C902`.
Each program piece is `control,y,tile,x`; the SAT word-0 is finalised by `0x3C9E8`: with **+0x27
bit6 = 0** (the proven post-transform state for every family-2 transform), word-0 is the program
control word **unchanged**, so the **display palette line = control byte & 0x0F**. `0x45684` is
creation-only and is NOT re-run by transforms or by re-materialization (0x41362), so `+0x27` stays
0 all the way to render — the display palette is therefore *never* the creation-time 0x45684 line.

## S. Seven H14 render-palette instances (authoritative)

Render state is taken from the exact H14 base-write event (`h15_render_program_trace.tsv`);
palettes in `h15_materialized_render_palettes.tsv`. Selector/anim as the handler leaves them
(post-0x4103A zero): the five 0x0224/0x00F4 writes leave `sel 0, anim 0`; 0x43840 explicitly sets
`sel 2/anim 0x27` (0x09EA) and `anim 0x70` (0x0179).

| Instance | sel | anim | program | control | display line(s) | pool → 0x4FD02 |
|---|---|---|---|---|---|---|
| 0x0224 R2 | 0 | 0x00 | 0x3D298 | 0x00 | **0x0** | pool 0x0B |
| 0x0224 R4 | 0 | 0x00 | 0x3D298 | 0x00 | **0x0** | pool 0x0B |
| 0x00F4 R4 | 0 | 0x00 | 0x3D298 | 0x00 | **0x0** | pool 0x0B |
| 0x00F4 R5 | 0 | 0x00 | 0x3D298 | 0x00 | **0x0** | pool 0x0B |
| 0x00F4 R6 | 0 | 0x00 | 0x3D298 | 0x00 | **0x0** | pool 0x0B |
| 0x09EA R5 | 2 | 0x27 | 0x3F3E9 | 0x0D | **0xC (6 pieces) + 0xD (2)** | pools 0x23 / 0x07 |
| 0x0179 R6 | 0 | 0x70 | 0x3E1C0 | 0x0C | **0xC** | pool 0x23 |

Each row's 16 raw ROM words are in `h15_materialized_render_palettes.tsv`. No display palette is
taken from 0x45684.

## T. Creation-time vs display-time (kept separate, per §2/§8/§10)

- **A. Creation variant** — parallel `A4+0x752 = schedule[2]>>4` (persists across clears).
- **B. Creation palette attribute** — `+0x27` from 0x45684 (family-2 variant/round/comp);
  **cleared to 0 by 0x4092E** on the first transform. Tabulated in
  `h14_materialized_palette_instances.tsv`, now headed **RECLASSIFIED: CREATION-TIME, not display**.
- **C. Post-transform display palette** — compositor control nibble (§S), in
  `h15_materialized_render_palettes.tsv`. `historical_claim_audit.csv` carries the explicit OLD→NEW
  reconciliation.

## U. Frame classification & the `+0x27` question (§5/§7)

`+0x27 = 0` for all seven (no writer re-sets it before render — 0x45684 creation-only, 0x41362
does not call it). Frames:
- **0x09EA R5, 0x0179 R6:** anim is **handler-set** (0x27, 0x70) → the palette is exact for the
  carried animation.
- **The five sel0/anim0 writes:** anim is **handler-left (0)** and each re-arms to an off-screen
  hunter (0x4103A sets Y=0x180) targeting its next char; so the frame is **REPRESENTATIVE** (the
  handler-left/default program 0x3D298). The palette line is still exact for that state (0), and —
  because the control nibble is what any selector-0 program feeds through a bit6-clear 0x3C9E8 —
  the *mechanism* (control-byte, not 0x45684) is exact regardless of the eventual on-screen anim.
  The single-value display line for these five is therefore reported as line 0 for the proven
  handler-left state, with the exact-frame caveat noted.

## V. Renderer C reconciliation (§9)

`0x3C9E8` (`raw/0003c9e8.c`, `rastan_actor_render.c`) and `0x3D054` (`raw/0003d054.c`) were already
COMPLETE and already model "bit6 clear → control-byte nibble". Added an explicit H15 note in
`rastan_actor_render.c` tying that to transformed family-2 actors (+0x27=0 → display = control
nibble; pointer to the H15 evidence). No C still claims transformed actors retain `+0x27` (the only
matches are the corrected H15 comments stating it is reset). No new renderer function was required.

## W. Manifest / Bestiary sync (§11)

The four present bases carry `palette_status = PROVEN (post-transform DISPLAY)` and a
`materialized_display_h15` render palette (round + display nibble); the bestiary swatch now reads
**"DISPLAY line 0xN · H15 compositor control byte (+0x27=0)"** and the round badge shows **ROUND
PROVEN**. The eight absent bases show **PHASE-2 ABSENT (H14)** (preserved exactly; not "absent from
the whole game") with their creation-time line labelled as such. The dashboard summary and
phase-assignment row now state Phase-2 placement + display palettes are resolved. No materialized
card shows "ROUND PENDING" / "round-representative". Bestiary regenerated; consistency PASS. Not
redesigned.

## X. Remaining exact dependency

The **exact on-screen first-frame animation** for the five sel0/anim0 instances (they re-arm to
hunters; 0x41362 may assign a new anim at re-materialization). This affects only *which* selector-0
program frame is shown, not the palette *mechanism* (always the control nibble with +0x27=0).
Human-readable species identity is likewise still pending. The variant source and the display-palette
mechanism are both now proven.

## Evidence & explicit C lists (continuation)

- **NEW:** `analysis/actor_decompilation/h15_materialized_render_palettes.tsv`,
  `h15_render_program_trace.tsv`.
- **RECLASSIFIED (not overwritten):** `h14_materialized_palette_instances.tsv` (header note).
- **UPDATED SEMANTIC C:** `rastan_actor_render.c` (0x3C9E8 display-palette consequence for
  transformed family-2 actors).
- **NEW RAW C:** none. **PROMOTED COMPLETE:** none new (renderer functions already COMPLETE).
- `historical_claim_audit.csv`: +1 OLD→NEW display-palette reconciliation row.
