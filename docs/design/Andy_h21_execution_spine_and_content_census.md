# Andy — H21: Execution Spine + Exhaustive Game-Content Census + Dependency Roadmap

**Agent:** Andy · Static RE (ORIGINAL ARCADE 68000, variant world_rev1). **No Genesis impl · no ROM
build · no MAME · runtime build counter 377 untouched (external Cody value, never written by me).**
Authoritative source: `build/regions/maincpu.bin`, Ghidra `rastan_arcade_ref.gpr`. Durable C first.

> **Headline.** Rastan is **interrupt-driven**: after reset init the 68000 idles in a 2-instruction
> loop and *all* per-frame work runs in the L5/VBlank ISR (0x3A008), which I decompiled COMPLETE.
> Coverage now reports a **primary physical-code metric = unique executable byte (union)**: **17.1%
> fully decompiled / 25.1% touched** (span-sum secondary, 14.2% / 21.7%; H20's 13.9% / 21.4% kept as
> historical). Two complementary dashboards are live in the Bestiary (V15). Content census enumerates
> the full cast + hazards; the Centaur is **not absent** — it is one of four PROVEN field bases whose
> human name is still PENDING.

## A. Execution spine (bottom-up engine) — PROVEN
Reset 0x3A000 → `braw 0x3AE86` (HW init: PC080SN @0xC50000, PC090OJ @0xD0xxxx, int-ack 0x350008,
sound 0x3E0001, palette clear @0x200000; SSP=0x10DE00) → `braw 0x3A080` idle loop
(`jsr 0x510C6; bra self`). Per-frame work is the **L5/VBlank ISR at 0x3A008** (raw/0003a008.c,
COMPLETE, byte-faithful):
1. mask IRQs (`ori #0xF00,%sr`), ack 0x350008, latch D0→0x3C0000;
2. if `A5+0x02 ∈ [2,4)`: pre-pass 0x3A126, then if `A5+0x00 != 0` and freeze flag `A5+0x1394 != 1`
   → **actor update 0x41F30** (whole live cast);
3. five fixed pre-frame subsystems: 0x3AB7C, 0x3ABE2, 0x3A0A8, 0x3EEFA, 0x3EF5C;
4. dispatch the **8-state master handler** via table @0x3A06C (tail-call, RTE tail 0x3A074).

**Dispatch table @0x3A06C** (decoded from maincpu.bin): s0→0x3A9FE, s1→0x3A8AC, s2→0x3A15A,
s3→0x3AB6E, s4→0x3EF25, s5→0x3A071, s6→0x3FD0E, s7→0x3A2E8.
Selectors: `A5+0x00` master state, `A5+0x02` frame sub-state (gates actor pass), `A5+0x1394` freeze.
Evidence: `analysis/decompilation/h21_execution_spine.tsv`, `h21_frame_lifecycle.tsv`,
`raw/0003a008.c`, `rastan_execution_spine.c`. The 8 handlers + 5 subsystems remain on the frontier.

## B. Coverage metric correction (primary = unique executable byte)
`gamewide_coverage_summary.json` now carries `primary_metric = "unique_executable_byte_union"`:
- **PRIMARY (union 33,274 B):** fully **17.1%** (5,686 B), touched **25.1%** (8,364 B).
- Secondary (span-sum 40,392 B): 14.2% / 21.7%.
- Historical (H20 span-sum): 13.9% / 21.4% (retained in `historical_h20`).
Two new COMPLETE routines this pass (0x3A008 ISR, 0x3A080 idle) raised the count to 55 COMPLETE.
The union metric counts each byte once and only credits COMPLETE when a COMPLETE function covers it —
it prevents both the span-sum double-count and status inflation.

## C. Game-content census (enumerate, don't over-decompile)
- `h21_gameplay_object_census.tsv` — 38 manifest actors, multidimensional
  (identity/creation/state/family/graphics/palette/behavior/reachability/round). Field enemies + all
  6 bosses are behavior-PROVEN; materialized/effect rows carry their H14/H15/H16 statuses.
- `h21_hazard_census.tsv` — 7 hazards with PROVEN-route candidate mechanisms, honest statuses:
  - **cave_block** PROVEN (H17, PAL-PC090OJ-STAGE1-CAVE-BLOCK-001).
  - **centaur** PARTIAL — see §D.
  - **floor_spears / stalagmites** PENDING (terrain-hazard marker route via 0x40E88/0x40EDE).
  - **bouncing_fireballs / flame_blocks** PENDING (projectile child via 0x4092E).
  - **ropes** PARTIAL — traversal terrain in the collision grid (H13), not a sprite actor.
- `h21_player_frame_inventory.tsv` — **75 player composite slots** enumerated from table 0x5BD40
  (offsets 0x0096..0x070C, strictly monotonic = a real 75-entry frame→piece table). Per-frame cell
  extraction is the frontier (CF-01), so slots are exposed with honest PENDING status, not fabricated.

## D. Centaur — NOT absent, name PENDING
The Centaur is **not** missing from the code. Four field-enemy bases carry a proven object identity
but no assigned human name yet: **0x01CB, 0x043A, 0x06E2, 0x0889** (the Bestiary shows these as
"OBJECT PROVEN / NAME PENDING"). The Centaur is one of these; pinning which requires per-base sprite
silhouette decode (CF-02/CF-05). Assigning a name without that decode would be fabrication, so it is
left PENDING with the candidate set named.

## E. Frontiers (dependency-ordered)
- `content_frontier.csv` — 7 rows (CF-01 player cells → CF-07 boss state machines).
- `code_frontier.csv` — 12 undecompiled subsystems ranked by remaining bytes; largest are
  ACTOR_CORE_LIFECYCLE (14,226 B), PC090OJ_COMPOSITOR (5,468 B), COLLISION_DAMAGE (3,234 B).

## F. Bestiary — two dashboards, live (V15)
`https://claude.ai/artifact/Dopg3mwMHdUMsZJSQgXDVR` now shows, top of page:
1. **Arcade 68000 Decompilation Roadmap** — union-primary %, span-sum secondary, per-subsystem bars.
2. **Game Content / Bestiary Coverage** — behavior-proven ratio per category, the 7-row hazard census,
   and the 75 player composite slots with frontier note.
Manifest `_synced_through = H21`. Generator: `tools/graphics_optimizer/build_bestiary.py`.

## G. Durable C added
`raw/0003a008.c` (ISR, COMPLETE) + `rastan_execution_spine.c` (semantic spine), registered in
`function_coverage.csv` for 0x3A008 and 0x3A080. `gcc -std=c11 -fsyntax-only` clean.

## H. Guards
- GAME-WIDE COVERAGE GUARD: **PASS** (334 funcs, fully 14.2% span-sum / 17.1% union, 275 NOT_DECOMPILED).
- Fidelity guard: **PASS**. Actor coverage guard: **PASS** (96 COMPLETE / 9 PARTIAL / 5 stub).
- Bestiary `consistency_check`: **PASS**.

## I. Honest negatives / limits kept visible
- Palette registry unchanged (no new palette decision this pass); cave-block cites its Decision ID.
- No hazard/enemy identity was invented; PENDING rows name the exact next dependency.
- Item/collectible reward path stays H19/H20 (A5+0x12C8 vestigial; equipment-field xref is CF-06).
- The union metric is reported alongside span-sum and H20's figure — no silent metric swap.
