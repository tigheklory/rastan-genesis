# Andy — CHECKPOINT H14: Phase-2 Marker-Chain Execution + Materialized Round-Pinning

**Agent:** Andy · **Type:** Static RE (arcade). **NO Genesis impl · NO ROM build · NO MAME · runtime
build counter 373, unchanged.** Authoritative: `build/regions/maincpu.bin` + `build/maincpu.disasm.txt`.

> **Result:** Every H13 Phase-2 character-marker occurrence was executed through its exact state
> handler branch. **Four** H10 materialized bases are now round-pinned by an *exact `+0x1E` write*;
> the other **eight are PROVEN ABSENT from Phase-2**. State is NOT actor identity — the same handler
> writes different bases per progression band and current char.

Bookkeeping (§0): H13 report corrected to "runtime build counter: 373, unchanged"; Bestiary status
text (`synced through`, `per-scene roster OPEN`, boss `positions PENDING`, boss palette source) is
corrected and now reads **synced through H14**.

---

## A. H13 starting point

H13 proved the record-accurate Phase-2 marker map: `descriptor(col,p)=0x1691C+col*0x22C0+p*0x40`,
entry `word1(@+2)` = collision-record ptr, collision word = `rec[0x14+strip*2+cell*8]` (or `rec[0x22]`
when `rec[0x20]==0xFF`), marker = high byte. The six castle-scene character rosters (`0x45..0x7B`)
and their proven H6 states are H14's input (`h13_phase2_marker_occurrences.tsv`). Castle scenes:
R1 {0x11,0x15}, R2 {0x2b,0x2c}, R3 {0x41,0x42,0x43}, R4 {0x5a}, R5 {0x6e,0x70}, R6 {0x85}.

## B. Marker-chain execution model

`tools/analysis/execute_phase2_marker_chains.py` deterministically runs the **proven** handler
branches (not a CPU emulator) for each H13 occurrence, emitting the exact branch, `+0x1E` base,
retarget `+0x0D`, `+0x01` anim, `+0x38` compositor, and whether the retarget target exists in the
same round's castle map. A base is round-pinned **only** on an actual `+0x1E` write for a real H13
occurrence — never from handler reachability. Branch provenance: the COMPLETE H5/H6 raw C plus the
newly-promoted-COMPLETE `0x43B32` full band matrix.

## C. Target-marker search / occurrence ordering

Retarget continuation is checked against the **real H13 map** (`round_marker_map()`), not ASCII
order. The arcade hunter search is `0x41064` (grid step `+8`/cell, wrap at the `|0x7f` column
boundary, match `word>>8 == +0x0D`, occurrence gated by `+0x2F`/`+0x30`); `0x4103A` clears+re-arms
the record as a latent hunter before the caller writes the next base/char. When a retarget char is
absent from the round's castle map, the record stays a latent off-screen hunter (chain terminates
in-scene) — recorded as `next_in_scene = no(absent->latent)` in
`h14_marker_chain_transitions.tsv`.

## D. State 0x1A / 0x43B32 exact transitions (the master dispatcher)

`0x43B32` is a **progression-band × current-char** matrix (full decode promoted to COMPLETE in
`raw/00043b32.c`). It writes seven different bases depending on band/char — proving *state ≠
identity*. The real H13 inputs resolve as:

- **R3 (prog 0x41–0x43, band D):** entry chars 0x67/0x68/0x69/0x76 — band D handles only
  0x53/0x54/0x55, so all R3 state-0x1A markers hit `else → 0x4092E` (**plain step, NO base write**).
- **R5 (prog 0x6e/0x70, band K):** char **0x67 → base 0x00F4**, next 0x4f, `+0x30=2`; chars
  0x4c/0x52/0x53/0x54 → `else → 0x4092E` (no base).
- **R6 (prog 0x85, band N):** entry chars 0x4c/0x52 — band N handles only 0x67, so both → `0x4092E`
  (no base).

So state 0x1A yields exactly **one** phase-2 base write: **0x00F4 in R5** (via char 0x67).

## E. State 0x18 / 0x1C / 0x1D / 0x21 / 0x22 transitions

- **0x18 (0x44082):** prog<0x18 → plain (R1 0x45 @0x15: no base). prog≥0x2f → **0x0224** next 0x55
  (R4 0x45 @0x5a). 
- **0x1C (0x4415A):** low-prog (R2 0x47 @0x2b/0x2c<0x2f) → **0x0224**, next 0x52/0x4c per `+0x2F`
  ordinal. (High-prog char matrix stays PARTIAL; not reached by any H13 occurrence.)
- **0x1D / 0x21 (0x44082 else):** prog≥0x18 → **0x00F4** next 0x4f. Fires for R4 0x46, R5 0x71,
  R6 0x71/0x72.
- **0x22 (0x43636):** R3 special-cases 0x73/0x74 (→0x00F4/0x0266) but R3 has none; R5 chars
  0x74/0x79 ≠ 0x73 → plain (no base). So no phase-2 base from state 0x22 given H13 inputs.

## F. State 0x1B burst-spawner ownership (R1 0x4D)

`0x43ECC` is a controller, not a species. The parent sets `+0x01=0x7A` and, after the `+0x1C`
timer + X-gate, calls `0x43F4E` → walks the 5-record component block at **A5+0x3C8**; each active
component is activated by `0x447F0`→`0x448B2` into **state 0x0F** (handler 0x40CCC) with sfx 0x10.
The child graphics base/anim are **parent-template-defined** (filled before activation), so the
child identity is **PENDING** — it is not one of the 12 H10 bases by any proven write. Parent role =
burst controller (visible frame anim 0x7A); no H10 materialized base is produced.

## G. State 0x15 exact 0x0179 branch (major acceptance criterion)

`0x43840` writes **base 0x0179 only** at `0x438B6`: `round==6 && char==0x6e && prog>=0x80`
(→ next 0x48, anim 0x70). Therefore:

- **R5** char 0x6e (round 5, generic branch) → **base 0x09EA** (next 0x71, anim 0x27, comp 2) —
  **NOT 0x0179**.
- **R6** char 0x6e @ prog 0x85 (≥0x80) → **base 0x0179** (0x438B6).

**0x0179 is PROVEN PRESENT in R6 only; PROVEN ABSENT in R5** (which writes 0x09EA). Handler
reachability in R5/R6 does not imply the 0x0179 write.

## H. State 0x20 torch / 0x0DAB transform chain

`0x40EDE` animates the torch (light source, frame table 0x40FE0) and, on marker-gone, runs
`0x40F52` which retargets by progression band: **base 0x0DAB only when prog<0x10** (0x40F82);
0x18..0x26 → 0x09EA(next 'a'); ≥0x54 → 0x09EA(next 'q'). H13 torch occurrences are R3 (prog
0x41–0x43, step band) and R5 (prog 0x6e–0x70, ≥0x54 band → **0x09EA** on retarget). **0x0DAB is
never written in Phase-2** (requires prog<0x10, which is Round-1 phase-1 territory). R5 torch
retarget corroborates 0x09EA's R5 presence.

## I. Six-round visible-base results

`h14_phase2_visible_bases.tsv`. Exact `+0x1E` writes for real H13 occurrences:

| Round | Base writes (entry marker → handler → base) |
|---|---|
| R1 | none (0x45→plain; 0x4D→burst controller, children PENDING) |
| R2 | **0x0224** (0x47→0x4415A) |
| R3 | none (torch stays torch; 0x67/0x68/0x69/0x76 band-D plain) |
| R4 | **0x0224** (0x45→0x44082), **0x00F4** (0x46→0x44082) |
| R5 | **0x00F4** (0x67→0x43B32-K; 0x71→0x44082), **0x09EA** (0x6e→0x43840; torch retarget) |
| R6 | **0x0179** (0x6e→0x43840@0x438B6), **0x00F4** (0x71/0x72→0x44082) |

## J. H10 materialized round-pinning

`h14_materialized_round_pinning.tsv` — every one of the 12 is now resolved (no handler-level
inference):

| Base | Verdict |
|---|---|
| 0x0224 | **PROVEN PRESENT — R2, R4** |
| 0x00F4 | **PROVEN PRESENT — R4, R5, R6** |
| 0x09EA | **PROVEN PRESENT — R5** |
| 0x0179 | **PROVEN PRESENT — R6** |
| 0x0DAB | **PROVEN ABSENT** (only prog<0x10, not Phase-2) |
| 0x0266 | **PROVEN ABSENT** (needs band C/D char 0x53/0x67/0x68 or prog-0x5a — no H13 occurrence) |
| 0x01FC | **PROVEN ABSENT** (needs state-0x1A prog<0x18; R1 castle has no state-0x1A marker) |
| 0x0236 | **PROVEN ABSENT** (needs state-0x1A char 0x55 prog 0x18–0x2e; none) |
| 0x0546 | **PROVEN ABSENT** (needs state-0x1A char 0x4c prog 0x63–0x6d; none) |
| 0x0235 | **PROVEN ABSENT** (state 0x19 marker 0x4b/0x57/0x58 never occurs in Phase-2) |
| 0x09F6 | **PROVEN ABSENT** (state 0x19; same) |
| 0x05E9 | **PROVEN ABSENT** (state 0x17 marker 0x59–0x5d never occurs in Phase-2) |

Each PRESENT verdict carries round, entry marker, handler, and exact base-write PC in the TSV.
Each ABSENT verdict is a static proof that the base-write branch's (state × prog band × char)
never coincides with the H13 castle-scene inventory.

## K. Newly discovered materialized bases

**None** in the Phase-2 chains. Base **0x0D5F** (§15) is written only at **0x426DC** (a non-Phase-2
system, outside the marker-chain handlers), so it is not reached by any Phase-2 chain and is not
added. Transient-vs-terminal notes: R5 0x00F4 (via 0x67 / 0x71) retargets to in-scene 0x4f → becomes
a torch (transient); R6 0x0179 retargets to 0x48 which is **absent** → terminal 0x0179; R2/R4 0x0224
retarget targets absent → terminal.

## L. Exact per-round palette instances

`h14_materialized_palette_instances.tsv`. Resolver `0x45684` (family-2, the 0x033E hunter, variant
0): `nibble = pal_nib_456ec[(round-1)*3 + comp_adj]`, colours from `0x3BA88[round][nibble] → pool →
0x4FD02`. Per H10, transforms rewrite `+0x1E` but do NOT re-run `0x45684`, so the instance is the
hunter's creation-time line. `comp_adj` = the base's compositor selector (0x0224/0x0179 sel2 → 2;
0x00F4/0x09EA sel0 → 0), which reproduces H10's round-1 nibbles (4/1/1/4). Resolved instances:
0x0224 R2 → nibble 0x1 pool 0x0b; 0x0224 R4, 0x00F4 R4/R5/R6, 0x09EA R5, 0x0179 R6 → nibble 0x0
pool 0x0b (16 raw ROM words recorded). **Dependency:** the hunter's true variant (`+0x752`) /
creation-time `+0x38` — variant 0 is the H10-established value used here.

## M. Manifest / Bestiary synchronization

`docs/design/rastan_actor_graphics_manifest.json`: `_synced_through` → **H14**; the four PRESENT
materialized actors carry `round_presence`/`round_status = PROVEN PRESENT` + palette instance; the
eight ABSENT carry `PROVEN ABSENT FROM PHASE-2`; dashboard rows fixed (boss positions decoded, boss
line F = `0x3BA88[round][15]`, phase/roster row reflects H13+H14). `rastan_actor_bestiary.html`
regenerated (**synced through H14**, no `per-scene roster OPEN` / `exact round PENDING` /
`positions PENDING` text; consistency PASS). Not redesigned.

## N. Remaining exact dependencies

- The **burst-spawner (0x1B) child identity** (A5+0x3C8 template base/anim) — parent-defined; not
  written by a proven constant.
- The materialized hunter's exact **variant (`+0x752`) and creation-time `+0x38`** (palette line);
  variant 0 assumed per H10.
- `0x4415A` **high-prog char matrix** stays PARTIAL (not reached by any H13 Phase-2 occurrence).
- Human-readable species identity + exact legal animation frame per base (unchanged from H10).

## Validation

- Chain executor deterministic checks **PASS** (every H13 char marker → exactly one handled state;
  all pins have an exact base-write evidence row).
- `gcc -fsyntax-only` **PASS** (100/100). Coverage guard **PASS** (99 rows, 85 COMPLETE; 10/10 H5
  handlers). Fidelity guard **PASS**. Manifest consistency **PASS**.
- Runtime build counter **373 → 373**; no ROM build, no MAME, no Genesis-runtime change.
- Evidence: `h14_marker_chain_transitions.tsv`, `h14_phase2_visible_bases.tsv`,
  `h14_materialized_round_pinning.tsv`, `h14_materialized_palette_instances.tsv`;
  `raw/00043b32.c` promoted COMPLETE.
