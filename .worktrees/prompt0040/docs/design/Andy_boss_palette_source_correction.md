# Andy — Boss Palette Source Correction (0x3C9E8)

**Agent:** Andy · **Type:** Static RE correction + manifest/bestiary update. **NO ROM/MAME/Genesis.**
**Build counter:** 360 (unchanged). Cody files untouched. **Artifact:** republished (Version 6) at
`https://claude.ai/artifact/Dopg3mwMHdUMsZJSQgXDVR`.

Mandatory RULES.md report for the boss-palette-source correction. Origin: Cody's boss-palette recon
proved the current model mis-attributed boss palettes to `0x45684`/`0x456EC`. This pass verifies the
real path in the live arcade code, decompiles `0x3C9E8`, and corrects the authoritative manifest +
C tree + bestiary. Authoritative source: `build/regions/maincpu.bin`.

---

## A. 0x3C9E8 exact semantics

The Ghidra export showed `FUN_0003c9e8` as an empty void; it is **not** — it has an implicit D0
in/out contract. Byte-exact 68000:

```
3C9E8: btst #6,%a4@(39)     ; test actor +0x27 bit 6
3C9EE: beq  0x3C9F4         ; bit6 clear -> D0 unchanged
3C9F0: moveb %a4@(39),%d0   ; bit6 set -> D0.LOW := +0x27 (moveb keeps D0 high byte)
3C9F4: rts                  ; return D0
```

Raw: `raw/0003c9e8.c` (COMPLETE). Semantic: `rastan_actor_render.c: apply_actor_attribute_override`.

## B. D0 input/output contract

- **in:** `D0` = compositor program control WORD (high byte = control/flags, incl. the `0x4000`
  HFLIP already OR'd by the caller at `0x3C9BA`; low byte = attribute, whose nibble 0..3 = palette
  line). `A4` = ActorRecord.
- **out:** `D0`. If `+0x27` bit6 == 0 → **unchanged** (palette line = program control byte & 0x0F).
  If bit6 == 1 → **D0.low := +0x27** (palette line = +0x27 & 0x0F). `moveb` preserves the high byte.

## C. Compositor → override → SAT flow

In the 0x3C902 general interpreter the callers `0x3C97E` and `0x3C9BE` do `bsr 0x3C9E8` then
`movew %d0,%a1@+` (`0x3C982` / `0x3C9C2`) — the returned D0 is written **straight to PC090OJ SAT
word 0**. No later masking/remapping changes the low nibble before the SAT write.

## D. Field-actor override vs embedded-compositor palette

`+0x27` is an **optional override**, not the unconditional palette source. Its bit6 is set only by
`0x45684`, whose **sole caller is the field-schedule installer** `0x4A086` (call site `0x4A0CE`).
Therefore:
- **Field-schedule actors** run `0x45684` → `+0x27 |= (nibble | 0x40)` → bit6 set → palette = `+0x27`.
- **Boss BODY / component actors** come from the record-type path
  `0x45330 → 0x4449E → 0x453A8 → 0x4543E`, which **never calls `0x45684`**, so `+0x27` stays `0x00`
  (bit6 clear) → palette = the **embedded compositor control nibble**.

## E. Six boss normal-state palette lines

Verified against the live programs/anims (Cody's recon reproduced in-repo): all six boss bodies
resolve to **palette line F**, from the compositor control byte (no `+0x27` override):

| Round | base | anim | program | line |
|---|---|---|---|---|
| R1 | 0x061D | 0x00 | 0x47908 | F |
| R2 | 0x0753 | 0xD6 | 0x499DA | F |
| R3 | 0x082C | 0x24 | 0x47EB4 | F |
| R4 | 0x07BF | 0xE0 | 0x49B90 | F |
| R5 | 0x0988 | 0x82 | 0x490DE | F |
| R6 | 0x0B35 | 0x66 | 0x3FA5E | F |

## F. Six round palette-pool sources

Line F resolved through the existing `0x3BA88 → 0x4FD02` model
(`pool = byte[0x3BA88 + (round-1)*32 + 0xF]`) — **all six verified byte-exact in the live ROM**:

| Round | lookup | pool | colors |
|---|---|---|---|
| R1 | 0x3BA97 | 11 | 0x4FE62 |
| R2 | 0x3BAB7 | 3 | 0x4FD62 |
| R3 | 0x3BAD7 | 2 | 0x4FD42 |
| R4 | 0x3BAF7 | 11 | 0x4FE62 |
| R5 | 0x3BB17 | 3 | 0x4FD62 |
| R6 | 0x3BB37 | 11 | 0x4FE62 |

These are recorded per boss in `actors[].palette_instances[]` with the 16-colour swatch.

## G. R5 / R6 component behaviour

- **R5:** five type-0x11 components, `+0x27 = 0`, compositor line F (same 0x3C9E8 embedded rule).
- **R6:** type 0x17/0x18/0x19 → line F; type 0x1A → line 0. **Verified in the live ROM: R6 line 0 and
  line F both resolve to pool 11** (`byte[0x3BA88+5*32+0x0] == byte[…+0xF] == 11`), so the four
  structural records share the same colours (0x4FE62) despite different attribute nibbles. The
  attribute distinction is preserved (not flattened); only the resulting pool coincides.

## H. Stale 0x45684 / 0x456EC / family-2 boss assumption — corrected

- **Manifest (authoritative):** all six BOSS actors `actor_family_3e` **2 → 0** (record-type path,
  `+0x3E=0`, NOT family-2); `palette_source` → *"compositor program control nibble F (0x3C9E8:
  +0x27=0, bit6 clear); round pool via 0x3BA88[…][0xF]"*; `palette_status` PROVEN; per-round
  `palette_instances[]` added.
- **C tree:** `rastan_actor_helpers.c` (0x45684 header) corrected — `0x456EC` re-labelled the
  **family-2 FIELD** palette (0x45684 path), with an explicit note that boss bodies keep `+0x27=0`
  and use `0x3C9E8`; `rastan_actor_tables.c` — the `0x4544E`/`0x454BA/D2/EA` tables re-labelled
  **family-2 loader tables (the 0x033E hunter route)**, NOT boss BODY records.
- **Bestiary:** boss cards now show *"line 0xF · pool N · compositor control (0x3C9E8, +0x27=0)"* and
  **PALETTE PROVEN (compositor F)**; the old "line inferred" wording is gone. 0 boss cards cite
  `0x456EC`.

## I. C files updated

- `raw/0003c9e8.c` (COMPLETE, new) — the D0 contract.
- `rastan_actor_render.c` (semantic; Cody's `apply_actor_attribute_override` verified byte-exact).
- `rastan_actor_helpers.c`, `rastan_actor_tables.c` — stale "boss palette" labels corrected.
- `function_coverage.csv` (+1 → 74 rows / 58 COMPLETE), `historical_claim_audit.csv` (+1 → 55),
  `README.md` (already lists the render/palette files).

## J. Remaining boss palette uncertainty

None for the **normal state** (all six lines + pools + colours proven). The exhaustive
all-animation-phase audit (programs selected by `0x4D110`/`0x4D650`/`0x4DB50`/`0x4E29C`) is a separate
later pass and was intentionally **not** started here.

## Validation

- Coverage guard: **PASS** (74 rows, 58 COMPLETE). Fidelity guard: **PASS**.
- `gcc -std=c11 -fsyntax-only`: **PASS** (76 files). Manifest consistency guard: **PASS**.
- Boss pools R1–R6 (11/3/2/11/3/11) + R6 line0==lineF==pool11: **verified in the live ROM**.

## Related documents

`docs/design/Cody_boss_palette_next_target_recon.md` (the recon that flagged this),
`docs/design/Andy_h10_materialized_actor_render_palette_decompilation.md` (render/palette chain).
