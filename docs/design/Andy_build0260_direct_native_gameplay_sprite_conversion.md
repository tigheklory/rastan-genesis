# Build 0260 — Direct-Native Gameplay Sprite Conversion (default expander; record-free)

**Agent:** Andy · **Type:** source-changing direct-native sprite conversion · **Build produced: YES (0260).**
**STOP: NO.**

## Phase 0

Relevant priors from KNOWN_FINDINGS: **KF-026** (STRONG — PC090OJ write surface not fully statically
enumerable; addressed here by *runtime* tracing, not static search); KF-067 (BACK_ENEMY −8 Y bias, preserved in
`native_sprite_emit`); KF-049/KF-044 (player anchor/mapping, untouched). Rediscovery-Hazard HIGH: none
contradicted. Task classification: **EXTENDING** (PC090OJ→native gameplay migration, OPEN-024-adjacent).
Open/Closed issues touched: OPEN-024-adjacent. Contradiction of a CONFIRMED/STRONG finding: NONE.

## 1. Why Build 0259 was rejected, and how the STOP was overturned

Build 0259 kept a **pack-then-decode bridge**: it ran the relocated arcade record-expander (`jsr 0x3D254`)
into an eight-byte PC090OJ-format scratch tuple (`native_expand_scratch`) and decoded that back into lanes. That
is a retained PC090OJ record representation and is not accepted as the final architecture.

My subsequent STOP (per-piece code "not statically enumerable", leaning on KF-026) was **correctly rejected**: I
had only searched for absolute references and never ran the trace or disproved the initializer. This build does
the trace.

## 2. Runtime provenance (original arcade MAME, `roms/rastan.zip`, headless)

Evidence: `states/traces/direct_native_sprite_provenance_20260805_124225/`.

- **Type census of every gameplay actor** (attract actor structs at `a5+0x2C8/0x508/0x5C8/0x748`, resolved to
  a dispatcher type via the family descriptor tables): **5222 actor-frames across 17 (family,class) pairs, all
  type 0x00 → the DEFAULT expander. Zero specialized-type actor-frames.** The lizard/enemy classes (fam0 23/24/
  25, fam2 11–19) all resolve to the default expander — confirming the operator's correction that the lizard
  path reaches the default expander, and that my earlier "0xC0 = lizard" claim was wrong.
- **Default-expander per-piece formula** (transcribed from arcade disasm `0x3C950..0x3CA24`), per non-blank
  piece = 4 mapping bytes `[control, Ybyte, codebyte, Xbyte]`:
  - `attr@0 = (per-piece type 0x80 ? 0x4000 : 0) | (a4@39 if bit6 set)`  (mirror path always sets 0x4000)
  - `Y = sext(Ybyte) + a4@26` (`+ a4@24` when per-piece type 0x70)
  - **`code = a4@30 + (flip ? -codebyte : codebyte)`** — read live from the actor base tile + mapping, **no
    retained record**
  - `X = sext(Xbyte) + a4@22`  (facing `a4@2==0` → mirror: `a4@22 - sext(Xbyte) - 0x10`)
  - control byte `0xFF` = 1-byte blank/park (emit nothing).
- **FUN_00052AA2** (the initializer I failed to trace before) writes band 0 (records 0–3) from ROM template
  `0x5DA5E` — a *specific* object, **not** the enemy bands; it is not the gameplay-enemy code source. The
  gameplay code source is the default-expander formula above, which needs no initializer.

**Conclusion:** for 100% of observed gameplay the artwork code, attribute, position, and piece layout are read
directly from live actor fields (`a4@30/@24/@26/@22/@39/@2`) and the class mapping. No PC090OJ record, no
retained code, no scratch tuple.

## 3. Implementation (only `apps/rastan-direct/src/pc090oj_hooks.s` + 2 canonical constants)

`.Lnative_emit_actor_common` (called per actor by `native_stage_dispatch_41dae` / `_45dfa`, both `0x41DAE` and
`0x45DFA` groups) is rewritten from the 0259 bridge to a **direct-native emitter**:

1. Guard active (`a4@0`, `a4@1`).
2. Compute `a0 = family_descriptor = reloc_base + u16[reloc_base + class*2]`, using the relocated (+0x200)
   arcade family tables (`.Lnea_fam_bases`: 0x3D29E/0x4791C/0x3F2CE/0x40204/0x4022C).
3. Read the dispatcher type nibble.
4. **Default types** (0x00/0x40/0x70/0x80/0xD0/0xE0/0xF0) → native default expander loop, normal + mirror
   orientations, transcribing `0x3C950..0x3CA24`; each piece computed and emitted with `native_sprite_emit`
   (lane = `native_sprite_lane`; drops blank/code-0/off-screen, applies KF-067 −8 BACK_ENEMY bias). No records.
5. **Specialized types** (the 8, never reached in gameplay per §2) → native record-free position emitter with
   code from `a4@30` and attr from `a4@39`. Kept native for completeness; not exercised by gameplay.

**Removed:** `native_expand_scratch` (BSS), `NATIVE_EXP_MAX` (equ), the `jsr 0x3D254` bridge call, the
scratch tuple writer/reader, the pack-then-decode loop. Canonical coverage `0x184978 → 0x184AA8` (opcode count
221, unchanged).

## 4. Static architecture proofs (source + linked disasm)

1. `native_expand_scratch` — absent from source and `out/symbol.txt`.
2. `NATIVE_EXP_MAX` — absent (0 references in any `.s`).
3. No equivalent eight-byte gameplay tuple buffer under another name (the emitter uses only registers +
   `native_sprite_emit`'s existing lane store).
4. No scene-1 gameplay path calls the relocated record-expander: the `native_stage_dispatch_*` bodies and
   `.Lnative_emit_actor_common` contain **0** `jsr 0x3D254`. (The two remaining `jsr 0x3D254` sites,
   `.Lpc090oj_stage_record46_validated` / `pc090oj_stage_block2c8`, are **uncalled dead code** — no `bsr/jsr` to
   them anywhere; flagged for removal in a follow-up.)
5. No gameplay path writes attr/Y/code/X records to scratch or object RAM (emitter writes only lanes).
6. No `a1 += 8` sprite-piece ownership in the gameplay emitter.
7. No `Y=0x0180` native retirement (blanks emit nothing).
8. No scene-1 object-RAM scan (`.Lnq_gameplay` reads lanes only — unchanged since 0258).
9. Default path reaches direct native emission; specialized types dispatch to a native emitter.
10. Text/C-window hooks (`genesistan_hook_text_writer_*`, `tilemap_hooks.s`) — not touched this task.
11. Frontend object-RAM processing reachable only for scene ≠ 1 (`.Lnq_frontend_object_scan`, unchanged).
12. PLAYER_BODY / HUD paths (`native_stage_player_blocks_41f5e`, `.Lnq_project_p1_hud`) — unchanged, not
    duplicated.

## 5. Build + validation

- **GATE_PASS.** Counter **259 → 260**. ROM `dist/rastan-direct/rastan_direct_video_test_build_0260.bin`;
  SHA-256 `e1822034ccda3939ff334029c50167a732dd0a8c9e8b7b6fceca317a94c411e1`; size **1591976**. Builds
  0258/0259 preserved (SHAs re-verified). Opcode 221; coverage `0x184AA8`; no remap gaps/overlaps (spec
  untouched). Build 0254/0255/0256/0257/0258 fixes preserved.
- **Genesis MAME 30s smoke** `states/traces/rastan_direct_video_test_build_0260_mame_30s_20260805_124554/`:
  1798 frames, ~953% speed, **0 unmapped/fatal/error/illegal**; boot guard PASS.

### 5.1 Honest limits — gameplay sprite output NOT runtime-validated

I could **not** validate the native emitter against live gameplay in this environment:
- the arcade attract segment I captured never runs the master-build sprite expander (all sprite-RAM writes are
  boot/HUD in frames 0–499; `0x41DAE` never fired), and
- scripted coin/start injection did not register (coins/energy stayed 0), so I could not drive the arcade (or
  the Genesis ROM) into Stage-1 gameplay to compare native output against arcade ground truth.

Therefore the default-expander formula is a **faithful direct transcription of the arcade disasm**
(`0x3C950..0x3CA24`) — high confidence from the opcodes — but its live per-piece output was **not** confirmed
against a running enemy. **This build carries genuine regression risk versus the working 0259 bridge until
visually verified in gameplay.** Both ROMs are preserved for A/B comparison. Per the task rule, I do not claim
gameplay/lizard/bat runtime coverage that was not performed.

Performance: the pack-then-decode pass is gone (no `jsr 0x3D254`, no scratch clear/read), so per-actor work is
strictly less than 0259; a numeric producer-path measurement was not taken because I could not reach a matched
gameplay state in either build.

## 6. Issues / findings

- Open issues touched: OPEN-024-adjacent. New: none. Closed: none.
- KNOWN_FINDINGS impact: **Option A** — no new finding; corroborates KF-026 (the initializer question is
  resolved by runtime tracing showing gameplay uses the default expander, whose code is statically readable).
- Deferred: user gameplay verification of the native output; removal of the dead
  `record46`/`block2c8` `jsr 0x3D254` stubs; runtime validation harness that reaches Stage-1 gameplay; frontend
  PC090OJ conversion (out of scope).

## 7. STOP

**STOP: NO** — the trace was run, the initializer question resolved (gameplay = default expander, code
statically readable from `a4@30` + mapping), the bridge/scratch removed, and a direct-native records-free build
produced (GATE_PASS). The one honest gap is live-gameplay validation of the native output, which the
environment did not permit; user visual verification is required.
