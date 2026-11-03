# Sub-Round-2 Actor Roster — Static Decompilation

**Static arcade decompilation of `build/regions/maincpu.bin` + Ghidra. No Genesis/ROM/build;
counter 360. No MAME in this pass.** Terminology is SUB-ROUND 1 / SUB-ROUND 2 / BOSS (per
`A5+0x13E` progression), never "castle" as a semantic label.

## Method (code, not observation)

The roster is an OUTPUT of the spawn code, derived as follows:
1. Round-end boundaries proven from `0x502AC` = {0x16,0x2D,0x44,0x5B,0x72,0x89}.
2. Field schedule `0x4A104` fully decoded (installer `0x4A086`): `block=(0x13E−round)>>1`, 5×8-byte
   slots, `[class, family, comp|variant, f36, timer, f34]`. Family→base via `0x4544E`/`0x45502`/
   `0x45562` (cross-checked against `corrected_semantic_families.json`).
3. Sub-round-2 window = the contiguous region at each round's end where the schedule is dominated
   by **family-2 (`0x033E`) spawners** (§4b of `Andy_actor_system_architecture.md`).
4. Char-targeted materialization via `0x41180`/`0x40baa`, `0x13E`-gated.

Offline decoders (durable): `tools/analysis/decode_field_schedule.py`;
evidence `analysis/actor_subround2/field_schedule_decode.txt` and
`analysis/actor_subround2/subround2_schedule_rosters.json`.

## Key finding — the field schedule does NOT list sub-round-2 hostiles directly

In every round's sub-round-2 window the schedule slots are **predominantly family-2 (`0x033E`,
comp 0/3/4, anim `0x93`) spawner entries**, not direct hostile families. The visible sub-round-2
enemies (e.g. R1 armored men, wizards, bats) are materialized through the **char-targeted spawner
path** (`0x41180`, `+0x03≠0`, target char `+0x0D` ∈ `0x45..0x7b`), whose target characters live in
the **sub-round-2 scene's map-column collision data**. So the schedule proves the *mechanism and
the family-2 variant* per round; the exact char-spawned identities require the per-scene marker
decode (remaining blocker, below).

## Marker → enemy dispatch (proven, `0x41180` + `0x40baa` + `0x40a86`)

- Floor-marker transition table `0x40a86` (4-byte `(cur_state, marker, new_state, term=0xFF)`):
  `0x31→s5, 0x32→s8, 0x33→s4, 0x34→flip(s1↔s2), 0x35→s6, 0x36→s9, 0x37→s7(term), 0x38→s10,
  0x39→s3, 0x3b→s11, 0x3c→s12, 0x3e/0x3f→s13(turn), 0x40/0x41→s14(turn)`.
- Letter markers (`0x45..0x7b`) in `0x41180` set state/anim/position directly and call the
  per-enemy init, gated on `A5+0x13E`. Notable proven direct bases: armored man `0x0A73`/`0x0A5A`
  (comp 2); direct-set bases `0x0275/0x00F4/0x0DAB/0x09EA` at `0x40DE2/0x40E9C/0x40F82/0x40FAC`.
- Config `0x41d26` (`0x41d08`) sets `+0x0D` (next target char) and chaining fields per state.

## Per-round SUB-ROUND 2

Format: schedule-proven content (statically complete) + remaining unknowns.

### ROUND 1 — SUB-ROUND 2  (`0x13E` 0x11–0x16, boss 0x16)
- **Schedule content:** family-2 spawners ONLY — `0x033E` comp0/comp3/comp4, variant 0.
  No direct roaming families are scheduled in this window.
- **Interpretation:** the entire R1 sub-round-2 hostile set is produced by the char-targeted
  spawner path fed by the family-2 mechanism. Independently, the direct-base handlers prove armored
  man `0x0A73`/`0x0A5A` (comp 2). Wizard/bat identities are char-spawned (PENDING marker decode).
- **HOSTILE ACTORS (proven bases):** `0x0A73`/`0x0A5A` armored men (direct handler, comp 2) —
  IDENTITY: armored man (matches R1 sub-round-2 ground truth). Others PENDING.
- **CONTROLLERS:** family-2 `0x033E` spawner actors (comp 0/3/4).

### ROUND 2 — SUB-ROUND 2  (`0x13E` 0x28–0x2D, boss 0x2D)
- **Schedule content:** family-2 spawners `0x033E` (comp0/3/4, variants 0–1) + **family-5
  `0x01CB`** (direct hostile).
- **HOSTILE ACTORS:** `0x01CB` (family 5) — IDENTITY PENDING. Char-spawned set PENDING marker decode.
- **CONTROLLERS:** family-2 `0x033E`.

### ROUND 3 — SUB-ROUND 2  (`0x13E` 0x3F–0x44, boss 0x44)
- **Schedule content:** family-2 `0x033E` (comp3/4, variants 0–1) + **family-5 `0x01CB`**.
- **HOSTILE ACTORS:** `0x01CB` — IDENTITY PENDING. Char-spawned set PENDING.
- **CONTROLLERS:** family-2 `0x033E`.

### ROUND 4 — SUB-ROUND 2  (`0x13E` 0x56–0x5B, boss 0x5B)
- **Schedule content:** family-2 `0x033E` (comp0/3/4, variants 0–2) + **family-5 `0x01CB`**.
- **HOSTILE ACTORS:** `0x01CB` — IDENTITY PENDING. Char-spawned set PENDING.
- **CONTROLLERS:** family-2 `0x033E`.

### ROUND 5 — SUB-ROUND 2  (`0x13E` 0x6D–0x72, boss 0x72)
- **Schedule content:** family-2 `0x033E` (comp3/4, variants 1–2) + **family-5 `0x01CB`** +
  **family-6 `0x03B3`**.
- **HOSTILE ACTORS:** `0x01CB`, `0x03B3` — IDENTITIES PENDING. Char-spawned set PENDING.
- **CONTROLLERS:** family-2 `0x033E`.

### ROUND 6 — SUB-ROUND 2  (`0x13E` 0x7E–0x89, boss 0x89)
- **Schedule content:** the longest/most mixed sub-round-2. Family-2 `0x033E` (comp0/3/4, variants
  1–2) INTERLEAVED with direct roaming families: `0x00D0` (f1), `0x01CB` (f5), `0x02E8` (f3),
  `0x03B3` (f6), `0x0400` (f11), `0x0889` (f10).
- **HOSTILE ACTORS:** `0x00D0, 0x01CB, 0x02E8, 0x03B3, 0x0400, 0x0889` scheduled directly
  (IDENTITIES PENDING) + char-spawned set PENDING.
- **CONTROLLERS:** family-2 `0x033E`.

## Remaining static unknowns (exact next targets)
1. **Per-scene letter-marker set** (the char-spawned identities). Decode chain: `0x507C5[0x13E]` →
   `0x3951C` descriptor (12-byte) → column-layout long → the column-record format loaded by
   `0x56128`/`0x561A0` → collision field `@(0x14+row*8+col*2)` / `@0x22` → HIGH byte marker char.
2. **`0x033E` family-2 semantic role** — is `0x033E` (anim `0x93`) a visible enemy or a
   child-spawner? Decode its update routine + compositor program.
3. **Human names** for families `0x00D0/0x01CB/0x02E8/0x0420/0x03B3/0x043A/0x0241/0x06E2/0x0889/
   0x0400` — technical bases proven; semantic names deferred (do not infer from screenshots).
