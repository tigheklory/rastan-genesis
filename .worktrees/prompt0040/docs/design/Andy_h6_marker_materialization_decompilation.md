# Andy — CHECKPOINT H6: Marker → State → Actor Materialization Decompilation

**Agent:** Andy · **Type:** Static reverse engineering (ORIGINAL ARCADE 68000). NO MAME, NO ROM,
NO Genesis change. **Build counter: 360 (unchanged).**
**Manifest/bestiary/`build_bestiary.py`:** NOT modified. Cody verification files untouched.

This is the mandatory RULES.md standalone report for CHECKPOINT H6. It closes the complete
**latent-hunter → collision-marker match → marker-specific branch → ActorRecord mutation →
materialized actor → initial state** routing that the C-recovery audit had deliberately left as
`0x41180 = PARTIAL`.

Authoritative sources: `build/regions/maincpu.bin` + `build/maincpu.disasm.txt` + the Ghidra
export. The reconstructed C is an **auditable representation, NOT original Taito source**; the
68000 binary remains final authority.

---

## A. Scope

State-0 marker/hunter scanning and in-place materialization, PC range `0x4117E..0x41D07`, plus the
two marker-chain **transform** states it produces (`0x40E88` state 0x1E, `0x40EDE` state 0x20)
which assign the *visible* base and retarget the next marker. This is a full arcade-code
decompilation pass, not a bestiary/roster/MAME pass.

## B. Functions covered

| PC | Semantic name | Raw C | Semantic C | Status |
|---|---|---|---|---|
| `0x41180` | state-0 scanner/hunter main | `raw/00041180.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x41064` | hunter row-scan (find +0x0D in row) | `raw/00041064.c` | `rastan_actor_dispatch.c` | COMPLETE |
| `0x41336` | floor-marker X placement (neighbour facing) | `raw/00041180.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x41362` | character-hunter materialization dispatch (28 routes) | `raw/00041180.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x40E88` | state 0x1E marker-chain transform (retarget) | `raw/00040e88.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x40EDE` | state 0x20 torch/light transform (retarget + anim) | `raw/00040ede.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x45418` | `+0x29` attribute loader (table `0x4542E`) | `raw/00045418.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x41BEE` | light/fire-source registration | `raw/00041bee.c` | `rastan_actor_materialization.c` | **COMPLETE** |
| `0x4103A` | marker consume / retarget (re-arm hunter) | `raw/0004103a.c` | `rastan_actor_materialization.c` | **PARTIAL** |

`0x53A2E` (collision-grid cell address) and `0x40A60`/`0x40A86` (floor transition table) were
lifted COMPLETE in the second recovery pass and are consumed here unchanged.

## C. `0x41180` semantic control flow

```
0x41180 state-0 handler (fires from 0x40BAA[0], base 0x033E, off-screen Y=0x180):
  decrement +0x1C timer; if nonzero -> 0x4117E rts (wait)          [gate every 2 frames]
  re-arm +0x1C = 2
  bsr 0x41064  (HUNTER ROW-SCAN: only when mode +0x03 != 0 && +0x30 != 0)
      -> walks the collision grid row via 0x53A2E, matches high byte == +0x0D target char,
         locking onto the +0x2F-th occurrence; returns cell address + char.
  if found -> 0x41362 materialize -> 0x41332 (braw 0x40BAA: re-dispatch THIS frame)
  if armed hunter and nothing found -> rts (keep hunting next frame)
  else (floor mode, or +0x30==0):
      0x4114A default X value (from camera 0x10B8 + facing +0x04)
      progression gates: abort if (0x13E==133 & 0x10CC>=1) or (0x13E==110 & 0x10CC>=13)
      seed scan X (+ fine scroll 0x10AE&7), scan Y (768 if floor & camera 0x10C0>=176)
      choose scan budget 0x26 or 0x40 (0x13E membership test, 17 values + 2 ranges)
      0x4127E VERTICAL COLUMN SCAN via 0x53A2E:
          floor mode  -> match structural marker 0x31..0x3C
          hunter mode -> match +0x0D target char
          step +/-0x80 (up/down) with 0x2000 wrap; exhaust budget -> rts
      on match: fine-scroll Y fixup (0x10B0&7)
          hunter mode -> 0x41362 materialize
          floor  mode -> +0x05 = class(+0x04)+1; 0x41336 place X; 0x40A06 transition; 0x40BAA
```

`0x53A2E` maps `(worldX, worldY)` to a 64×64 word grid at `0x10DE00` (row stride `0x80`,
span `0x2000`), high byte = marker character. Positions are **collision-cell world coordinates**
(A5+0x216 X, A5+0x218 Y), fine-scroll corrected, then per-marker pixel offsets; Y masked `&0x1FF`.

## D. `0x41362` route map (materialization classifier)

`0x41362` is a **large character classifier**: it stores the matched cell address into `+0x0E`,
sets `+0x07=1`/`+0x09=1`, then a binary-search compare chain (with a secondary `0x41414` dispatch
for chars `< 'O'`) routes each marker character to a per-marker handler that assigns
**state (+0x05)**, **anim (+0x01)**, and (for most) the `+0x29` attribute via `0x45418`. **28
marker/character routes** are proven (`analysis/actor_decompilation/h6_marker_materialization_routes.tsv`).
Every handler re-guards `d0 == +0x0D` and tails to `0x41332 → 0x40BAA`.

| Marker char(s) | State +0x05 | 0x40BAA handler |
|---|---|---|
| `0x31..0x44` | 0x1D | `0x44082` |
| `'E'` 0x45 | 0x18 | `0x44082` |
| `'F'` 0x46 | 0x1D | `0x44082` |
| `'G'` 0x47 | 0x1C | `0x4415A` |
| `'H'` 0x48 | 0x1E | `0x40E88` (transform) |
| `'I'` 0x49 | rec_type=1 | `0x4092E` (projectile; template copy from A5+0x588) |
| `'K'` 0x4B | 0x19 | `0x4396A` |
| `'L'` 0x4C | 0x1A | `0x43B32` |
| `'M'` 0x4D | 0x1B | `0x43ECC` |
| `'O'..'Q'` 0x4F-0x51 | 0x20 | `0x40EDE` (torch/light) |
| `'R'..'V'` 0x52-0x56 | 0x1A | `0x43B32` |
| `'W','X'` 0x57-0x58 | 0x19 | `0x4396A` |
| `'Y'..']'` 0x59-0x5D | 0x17 | `0x43F88` |
| `'^','_','` `` 0x5E-0x60 | 0x16 | `0x43AE6` |
| `'a','b','c'` 0x61-0x63 | 0x15 | `0x43840` |
| `'d'` 0x64 | 0x14 | `0x4375C` |
| `'e','f'` 0x65-0x66 | 0x13 | `0x4375C` |
| `'g','h','i'` 0x67-0x69 | 0x1A | `0x43B32` |
| `'j','k'` 0x6A-0x6B | 0x18 | `0x44082` |
| `'l','m'` 0x6C-0x6D | 0x1D | `0x44082` |
| `'n','o','p'` 0x6E-0x70 | 0x15 | `0x43840` |
| `'q','r'` 0x71-0x72 | 0x21 | `0x44082` |
| `'s','t','u'` 0x73-0x75 | 0x22 | `0x43636` |
| `'v','w'` 0x76-0x77 | 0x1A | `0x43B32` |
| `'x'` 0x78 | 0x21 | `0x44082` |
| `'y'` 0x79 | 0x22 | `0x43636` |
| `'z'` 0x7A | 0x15 | `0x43840` |
| `'{'` 0x7B | 0x21 | `0x44082` |

The state → `0x40BAA` handler mapping is derived from the proven self-relative jump table at
`0x40BC2` (states 0x13..0x22 route through the `0x40E48..0x40E70` `braw` thunks to the ten H5
handlers; states 0x1E/0x1F/0x20 route to the transform handlers `0x40E88`/`0x42EF8`/`0x40EDE`).
Characters `>= '|'` (0x7C) have no route.

**Materialization vs later transformation (task §9).** For the char-hunter path, `0x41180`
assigns **state, anim, and attribute — NOT the visible base `+0x1E`** (case B): the base is set
later by the state handler or by the retarget chain. The direct exceptions are `'I'` (record-type-1
projectile: full 32-byte record copied from the `A5+0x588` template) and the transform states.
Progression gates (`A5+0x13E`, 30 recorded in `h6_progression_gates.tsv`) and round gates
(`A5+0x118`, 5 in `h6_round_gates.tsv`) select per-scene position offsets and conditional
linked-object spawns (`0x43F52`/`0x43F4E`, e.g. multi-segment enemies).

## E. Graphics/base assignments proven in H6

The visible `+0x1E` base + next target char are assigned by the transform-state retarget chain:

- **`0x40E88` (state 0x1E, `'H'`):** when the tracked `+0x0E` marker vanishes — `0x13E<0x18` →
  `0x4103A` then base **`0x0F4`**, retarget char **`'O'`** (this is the code at `0x40E9C`);
  `0x18..0x2E` → step + spawn a 5-part linked object (`0x43F52`); `>=0x2F` → step only.
- **`0x40EDE` (state 0x20, `'O'/'P'/'Q'` torch):** `0x40F52` registers the light source, then by
  progress band: `<0x10` → base **`0xDAB`** retarget **`'I'`** anim `0x74` (`0x40F82`);
  `0x18..0x26` → base **`0x9EA`** retarget **`'a'`** (`0x40FAC`); `0x4E..0x53` → base **`0x9EA`**
  retarget **`'q'`** comp `+0x38=2` (`0x40FCC`); other bands → step. The 90-frame fire animation
  table at `0x40FE0` is preserved in `raw/00040ede.c`.

Additional bases discovered in H6 (assigned via retarget, distinct from the H5 transient bases):
**`0x0F4`, `0xDAB`, `0x9EA`**. `0x41BEE` writes the light-source record at `A5+0x1282 + 6*+0x2F`
(active word + `0xD00460 + 0x50*A5+0x214` graphics pointer) and the global torch flag `A5+0x1280`.

## F. ActorRecord fields clarified in H6

- **`+0x0E..+0x11` (polymorphic).** In the **hunter/materialization context** `0x41180` writes the
  full 32-bit **collision-map cell ADDRESS** here (`movel %a0,%a4@(14)` at `0x41362`); `0x40E74`
  re-reads that address to recheck the marker. This is **not** an index — it is a live grid
  pointer. (In the materialized ground/airborne engines the low byte is reused as an animation
  index; the header keeps `field_0e[4]` neutral with `ar_cell_addr()` for the hunter view.)
- **`+0x2F` (variant_2f):** the occurrence ordinal the row-scan locks onto (Nth matching cell), and
  the light-source slot index in `0x41BEE`.
- **`+0x07`/`+0x09`:** set to 1 on materialization (init flag / frame countdown).
- **`+0x1C`:** state-0 scan cadence (re-armed to 2 frames).

## G. Remaining partial dependency

**`0x4103A` remains PARTIAL.** Its control flow is fully lifted — it calls `0x4092E` (retire/step)
and then re-arms the same record as a fresh latent hunter (`+0x00/+0x03/+0x04=1`, `+0x1C=1`,
`+0x20=1`, `+0x1A=0x180`), after which the caller writes the next base/target. But the `0x4092E`
callee body (generic active-actor step / retire / score / drop) is **deliberately not decompiled
in H6** — it is an H7 target. `0x4103A` is therefore **not** claimed COMPLETE, and the coverage +
historical-audit guards enforce that.

## H. Verification

- Coverage guard (`check_actor_decompilation_coverage.py`): **PASS** — rows 58, COMPLETE 38,
  PARTIAL 10, STUB_ONLY 10; H5 handler PCs covered 10/10.
- Fidelity guard (`check_decompilation_fidelity.py`): **PASS** — layout contract compiles, COMPLETE
  raw files carry `ORIGINAL ARCADE PC:` with no ellipsis, PARTIAL marked, jump table int16.
- `gcc -std=c11 -fsyntax-only`: **PASS** on the full tree (51 files: semantic + raw).
- Historical audit: 40 rows (H6 upgraded `0x41180` PARTIAL→COMPLETE, `0x41BEE` STUB→COMPLETE,
  `0x4103A` STUB→PARTIAL with the `0x4092E` deferral noted).

## I. Exact next undecompiled dependency

**`0x4092E`** — generic active-actor step/retire (and its drop/score children, incl. `0x447F0`).
This is the H7 target and is **not** started in this pass.

## Related documents

`docs/design/Andy_actor_decompilation_c_recovery.md` (C-tree contract + guards),
`docs/design/Andy_actor_state_machine_decompilation.md` (0x40BAA dispatch, states 0x13-0x22),
`docs/design/Andy_actor_behavioral_identity_decompilation.md` (H5 handlers).
Evidence: `analysis/actor_decompilation/h6_marker_materialization_routes.{json,tsv}`,
`h6_progression_gates.tsv`, `h6_round_gates.tsv`.
