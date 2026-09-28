# Andy — CHECKPOINT H13: Exact Collision-Word Layout + Six Phase-2 Rosters

**Agent:** Andy · **Type:** Static RE (arcade) + Cody reconciliation.
**Constraints honored:** NO ROM build · NO MAME · NO Genesis-runtime change · **runtime build
counter: 373, unchanged by H13** · Cody historical reports untouched · protected Cody files untouched · no fabricated
rosters/actors · unknowns kept PENDING. Authoritative source: `build/regions/maincpu.bin` +
`build/maincpu.disasm.txt` (original Taito arcade program).

> **Result:** The H13 core question is **PROVEN** and the stop-condition gate is satisfied, so the
> six rosters are produced. The exact 0x55904 → 0x559B2 mapping is closed **and independently
> corroborated by two Cody arcade-runtime traces**. Roster round-pinning of the H10 materialized
> cast is done only where a **unique** phase-2 grid marker proves it; the rest stay PENDING (not
> fabricated).

---

## §0. Cody-corpus reading — honest disclosure (NO false compliance)

H13 §0 asked to read **every** Cody-authored Markdown file. There are **405 `Cody*.md` files,
26.6 MB (~7M tokens)**. Full line-by-line ingestion is infeasible within one session budget and
would violate the project efficiency mandate. Per the checkpoint's explicit escape clause I
**report the status honestly and do not claim compliance**
(`analysis/actor_decompilation/h13_cody_reading_status.tsv`):

- **Read in full this checkpoint (5, all H13-critical):** `Cody_build0115_itempage_exit_5591A…`,
  `Cody_build0228_rope_collision_address_mapping`, `Cody_build0169_bg_pass_collision_producer_candidate`,
  `Cody_collision_map_grounding_implementation`, `Cody_build0246_native_plane_a_vertical_source_proof`.
- **Whole-corpus grep** for the arcade collision terms (`0x55904`, `0x559B2`, `0x1691C`,
  `0x10D040`, `collision record`) → 13 files touch them; the 5 core ones were read, the other 8 are
  rope/plane-A **Genesis-runtime** reports.
- **~135 files** substance-scanned in a prior batch → confirmed overwhelmingly Genesis-runtime
  build history, not arcade collision semantics.
- **~400 files were NOT read line-by-line.** No claim of full compliance is made.

The 5 core files are reconciled against the arcade code in
`analysis/actor_decompilation/h13_cody_report_reconciliation.tsv`.

---

## §1. The exact mapping — PROVEN (closes the H11/H12 blocker)

**Question (verbatim):** *what exact bytes/words from one 0x40-byte ROM descriptor are transformed
by 0x55904 into the record layout consumed by 0x559B2 as `col_record[20 + subcol*2 + row*8]`?*

**Answer (all from the arcade disassembly):**

```
0x502CC  0x10D000[col] = 0x1691C + col*0x22C0 + (A5+0x13E)*0x40          (col 0..15)
         → the per-(col,scene) DESCRIPTOR PAGE: 0x40 bytes = 16 four-byte entries {word0, word1}

0x558A2  strip = A5+0x10CA cycles 0..3; every 4 strips 0x558C6 advances ALL 16 descriptor
         pointers +4 (next entry) and calls 0x55904 to rebuild; 0x558E0 advances scene A5+0x13E
         after 16 entries (16 × 4 = 0x40, the page stride)

0x55904  per entry:  word0  = @entry        → 0x10D080[col]   (name-table tile word)
                      word1  = @(entry+2)    → 0x10D040[col]   = 16-bit ROM POINTER to the
                                                                 collision RECORD  ("col_record")

0x55968  BG dispatch: a0 = A5+0x10A0 dest cursor; for the 16 columns a2 = 0x10D040[col] = col_record

0x559B2  per cell d2 = 0..3:
             if col_record[0x20] == 0x00FF:  cw = col_record[0x22]                (uniform fill)
             else:                           cw = col_record[20 + strip*2 + cell*8]
             grid[0x10DE00 + (a0 − 0xC08000)/2] = cw
             (companion word col_record[0 + strip*2 + cell*8] written to the next dest word)

0x41294  CONSUMER: d0 = grid_word >> 8   →  MARKER = HIGH byte  → 0x41362 route classifier (H6)
```

So **`col_record` is the record pointed to by the descriptor entry's `word1` (bytes at entry+2)**,
and the record is a compact **4×4 grid**: `subcol/strip = A5+0x10CA (0..3)`, `row/cell = d2 (0..3)`,
byte offsets `0x14..0x32`. `20` in `[20 + subcol*2 + row*8]` is **decimal 20 = 0x14 hex** (the
arcade `lea a2@(20,d7:w)` displacement). The exact bytes of one descriptor that become the cell
are: **`word1` (entry+2) selects the record; `col_record[0x14 + strip*2 + cell*8]` is the collision
word; its high byte is the marker.** Full field table:
`analysis/actor_decompilation/h13_55904_record_mapping.tsv`.

### Reconciliation of the `0x20` vs `20` ambiguity (important)

Cody's `collision_map_grounding_implementation` noted the source formula as
`"0x20 + strip*2 + cell*8"`. The arcade code disambiguates this: the **source displacement is
DECIMAL 20 (= 0x14 hex)** (`0x559CE lea a2@(20,d7:w)`); **hex 0x20 is the CONTROL/sentinel word
offset** (`0x559B6 lea a2@(0x20); cmpiw #0x00FF`) and **hex 0x22 the uniform alternate**
(`0x559D4`). The cell loop register is **D2** (confirmed). H11/H12's `[20 + subcol*2 + row*8]` (20
decimal) was therefore **correct**; H13 adds the previously-missing `word1` indirection and the
sentinel path.

### Independent corroboration (Cody arcade-runtime traces)

- **`Cody_build0115` (breakpoint at 0x5591A, original arcade):** "0x55904 rebuilds a 16-entry table;
  copies the first descriptor word to 0x10D080+ and converts the **second** descriptor word into a
  long pointer at 0x10D040+"; trace `0x1691C: 00 03 20 FC` → word0=0x0003, **word1=0x20FC** (record
  ptr). Matches this decode exactly.
- **`Cody_build0228`:** "reads **word 2(descriptor)** as the block pointer then reads collision
  values from that block; **entry size 4 bytes**; **strip index 0x10CA**." Matches exactly.

---

## §2. Raw + semantic C (COMPLETE)

- **`raw/000559b2.c`** — byte-faithful `0x559B2` (BG) and `0x55A14` (FG) producers, the `0x55904`
  record build, and the `0x41294` high-byte marker decode. Status **COMPLETE**.
- **`rastan_scene_map.c`** — semantic `collision_record_ptr(col, prog_13e, entry)`,
  `collision_grid_word(rec, strip, cell)`, `collision_marker(...)`; the H11 header block's
  "REMAINING BLOCKER" note is replaced with the closed H13 mapping.
- **Coverage:** `function_coverage.csv` updated — `0x559B2` note rewritten; `0x55904`, `0x55A14`
  added COMPLETE. **Audit:** `historical_claim_audit.csv` +1 H13 row.
- `gcc -fsyntax-only` **PASS on all 100 C files**.

---

## §3. The six Phase-2 rosters (marker → proven H6 route)

Produced record-accurately by `tools/analysis/decode_rastan_scene_markers.py` (extended this
checkpoint). Only the **castle** scenes inside each round window (section kind ≠ 0) are enumerated;
the character-hunter band `0x45..0x7B` is mapped through the **proven H6 `0x41362` route table**.
Full data: `h13_phase2_marker_occurrences.tsv`, `h13_phase2_collision_cells.tsv`.

| Round | Castle scenes (0x13E) | Character-hunter markers → state (0x40BAA handler) |
|---|---|---|
| **R1** | 0x11, 0x15 | `0x45`→0x18 (0x44082) · `0x4D`→0x1B (0x43ECC) |
| **R2** | 0x2B, 0x2C | `0x47`→0x1C (0x4415A) |
| **R3** | 0x41, 0x42, 0x43 | `0x4F`→0x20 torch (0x40EDE) · `0x67/0x68/0x69`→0x1A (0x43B32) · `0x76`→0x1A |
| **R4** | 0x5A | `0x45`→0x18 (0x44082) · `0x46`→0x1D (0x44082) |
| **R5** | 0x6E, 0x70 | `0x4C/0x52/0x53/0x54/0x67`→0x1A (0x43B32) · `0x4F`→0x20 torch · `0x6E`→0x15 (0x43840) · `0x71`→0x21 (0x44082) · `0x74/0x79`→0x22 (0x43636) |
| **R6** | 0x85 | `0x4C/0x52`→0x1A (0x43B32) · `0x6E`→0x15 (0x43840) · `0x71/0x72`→0x21 (0x44082) |

The dominant floor/structural band `0x31..0x3C` (esp. `0x3A` = Cody-proven scheduled-hostile
zero-X positioning) is present in every round and is terrain structure, not the enemy roster.

---

## §4. H10 materialized-cast round-pinning (honest; PENDING where unproven)

`h13_phase2_actor_rosters.tsv` cross-references each of the 12 H10 materialized bases to the rounds
whose phase-2 grid markers route to its handler. **Only handler-level REACHABILITY is claimed where
a unique grid marker proves it:**

- **`materialized_0x0DAB`** (state 0x20 torch, handler 0x40EDE) → **REACHABLE in R3, R5** (the
  torch markers `0x4F..0x51` occur there).
- **`materialized_0x0179`** (state 0x15, handler 0x43840) → **REACHABLE in R5, R6** (state-0x15
  markers `0x6E..0x70` occur there).
- **The other 10** (`0x00F4`, `0x09EA`, `0x0224`, `0x0266`, `0x0235`, `0x09F6`, `0x01FC`, `0x0236`,
  `0x0546`, `0x05E9`) stay **PENDING**: they are reached by chain transforms or generic/multi-site
  H5 handlers not tied to a single phase-2 grid marker, so round-pinning them now would be
  fabrication. Their **human identity, exact legal frame, and per-round palette instance remain
  PENDING** exactly as H10 left them.

No manifest actor was invented, renamed, or force-pinned.

---

## §5. Evidence files (this checkpoint)

- `analysis/decompilation/c/raw/000559b2.c` (COMPLETE) · `rastan_scene_map.c` (semantic).
- `analysis/decompilation/c/function_coverage.csv` (+2, note rewrite) ·
  `historical_claim_audit.csv` (+1).
- `analysis/actor_decompilation/h13_55904_record_mapping.tsv`,
  `h13_descriptor_layout.tsv`, `h13_phase2_collision_cells.tsv`,
  `h13_phase2_marker_occurrences.tsv`, `h13_phase2_actor_rosters.tsv`,
  `h13_cody_report_reconciliation.tsv`, `h13_cody_reading_status.tsv`.
- `tools/analysis/decode_rastan_scene_markers.py` (extended with the H13 record-accurate layer).

## §6. Validation

- Enumerator deterministic checks **PASS**: all six rounds have a proven phase-2 start; every
  enumerated `0x45..0x7B` marker resolves to a proven H6 route.
- `gcc -fsyntax-only` **PASS** (100/100 C files).
- Mapping corroborated by two independent Cody arcade-runtime traces (§1).
- Runtime build counter: **373, unchanged by H13**; no ROM build, no MAME, no Genesis-runtime change.
