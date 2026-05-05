# Andy — Build 55 Palette `0x045DAE` Intercept Redesign

**Agent:** Andy (Claude Code)
**Type:** Narrow architectural redesign — analytical only (no implementation, no broad redesign, no new evidence collection)
**Build:** rastan-direct Build 0055 (target; Build 0054 baseline post-D6-fix, post-v3.2 dispatch)
**Date:** 2026-05-03
**Scope:** ONE element of `Andy_build55_palette_translation_design.md` is revised — the `0x045DAE` bypass intercept. All other Build 55 design elements remain LOCKED.

---

## 0. Executive verdict

**Recommended option: D — narrower intercept around `jsr 0x3A2D0` copy call at `arcade_pc 0x045DB8`.**

Cody Phase A (`Cody_build55_palette_phase_a_block.md`) proved the locked design's `0x045DAE..0x045DF8` 74-byte function-body replacement is **unsafe**:

- External branch into span: `0x45D76: bsrw 0x45DC4` (the parent at `0x45D72` calls a sub-routine whose entry point is INSIDE the proposed span)
- Internal-but-shared branch targets: `0x45D82: beqs 0x45DC2` and `0x45DCA: beqs 0x45DC2` (both share an RTS at `0x45DC2` inside the span)
- Required fall-through side effects: `addqw #1, %a5@(568)` at `0x45DBE` and `addqw #1, %a5@(3152)` at `0x45DF4` (game-state counters)

**Option D resolves all three problems by replacing only the single `jsr 0x3a2d0` instruction at `arcade_pc 0x045DB8`** (6 bytes) with `jsr genesistan_palette_hook_45dae` (6 bytes). The replacement span is one instruction; it contains no branch targets, no RTS, no counter updates. The surrounding routine flow (early-out, bounds-exceed, counter-increment, RTS) executes natively and unmodified. The helper translates only the bulk-path's 64 source words and stages them to Genesis CRAM iff the arcade bank base is 0 (idx=0 → banks 0..3 = tilemap-consumed); for idx ≥ 1 (banks 4..31) the helper is a near-no-op (just RTS).

**Sibling `0x045DE4` is left untouched.** Its `jsr 0x3a2d0` at `0x45DEE` writes to `0x200600` (banks 48..79 — outside tilemap-consumed range and outside Genesis-line-mappable range). The arcade-side write to arcade palette RAM has no Genesis-visible effect; no intercept is required (consistent with the locked design's IGNORE classification for this site).

**Locked Build 55 elements UNCHANGED:**
- `0x59AD4` body replacement (register-contract gate GREEN per Cody §A.1)
- `0x03AB00` single-word bypass intercept
- Conversion path (xBGR-555 → Genesis CRAM via [`apps/rastan/src/main.c:1008-1017`](apps/rastan/src/main.c#L1008-L1017))
- Bank-mapping rule (`bank & 0x03 → Genesis line`; banks ≥ 4 SKIP)
- Sprite handling (Build 56 follow-up)
- High-bank treatment (SKIP)
- All 10 Andy v3.2 §1.8 architectural invariants

**Spec impact:** unchanged from locked design — still 3 new `opcode_replace` entries; `count_guard 90 → 93`. Only the third entry's address and shape differ (single-instruction JSR swap at `0x45DB8` instead of 74-byte body replacement at `0x45DAE`).

---

## §1.1 Parent caller chain analysis

Read from [build/maincpu.disasm.txt](build/maincpu.disasm.txt) lines 88340–88380 (range `0x45D70..0x45DF8`):

```
88340:   45D70: rts                                  ; END of preceding routine
88341:   45D72: bsrw 0x45D7C                         ; PARENT entry — invokes routine 1 (path 1)
88342:   45D76: bsrw 0x45DC4                         ; PARENT — invokes routine 2 (path 2)
88343:   45D7A: rts                                  ; PARENT exit

; ─── Routine 1 (palette path 1, base 0x200000) ───────────────────────
88344:   45D7C: movew %a5@(568), %d0                 ; counter A
88345:   45D80: tstw %d0
88346:   45D82: beqs 0x45DC2                         ; if 0 → shared RTS at 0x45DC2
88347:   45D84: subqw #1, %d0
88348:   45D86: cmpiw #8, %d0
88349:   45D8A: bcss 0x45DA4                         ; bulk path
88350:   45D8C: clrw %a5@(568)                       ; bounds-exceeded: state mutation
88351:   45D90: movew #1, %a5@(5040)                 ;   state mutation
88352:   45D96: jsr 0x3BA20                          ;   arcade subroutine call
88353:   45D9C: movew #1, %a5@(3152)                 ;   state mutation (counter B init)
88354:   45DA2: rts                                  ;   exit (bounds-exceeded path)
; bulk path:
88355:   45DA4: muluw #128, %d0                      ; idx = (counter_A - 1)
88356:   45DA8: lea %a5@(5632), %a0                  ; src = workram + idx*128
88357:   45DAC: addaw %d0, %a0
88358:   45DAE: lea 0x200000, %a1                    ; dst = 0x200000 + idx*128
88359:   45DB4: addaw %d0, %a1
88360:   45DB6: moveq #64, %d0                       ; entry count for arcade copy
88361:   45DB8: jsr 0x3A2D0                          ; ← OPTION D REPLACEMENT TARGET (6 bytes)
88362:   45DBE: addqw #1, %a5@(568)                  ; ← STATE COUNTER MUTATION
88363:   45DC2: rts                                  ; ← shared RTS (also target of beqs from 0x45D82 and 0x45DCA)

; ─── Routine 2 (palette path 2, base 0x200600) ───────────────────────
88364:   45DC4: movew %a5@(3152), %d0                ; counter B
88365:   45DC8: tstw %d0
88366:   45DCA: beqs 0x45DC2                         ; if 0 → shared RTS in routine 1
88367:   45DCC: subqw #1, %d0
88368:   45DCE: cmpiw #8, %d0
88369:   45DD2: bcss 0x45DDA                         ; bulk path
88370:   45DD4: clrw %a5@(3152)                      ; bounds-exceeded
88371:   45DD8: rts
; bulk path:
88372:   45DDA: muluw #128, %d0
88373:   45DDE: lea %a5@(5632), %a0
88374:   45DE2: addaw %d0, %a0
88375:   45DE4: lea 0x200600, %a1                    ; dst = 0x200600 + idx*128 (banks 48..79)
88376:   45DEA: addaw %d0, %a1
88377:   45DEC: moveq #64, %d0
88378:   45DEE: jsr 0x3A2D0                          ; arcade copy (path 2)
88379:   45DF4: addqw #1, %a5@(3152)                 ; ← STATE COUNTER MUTATION
88380:   45DF8: rts
```

### Function-boundary findings

- **Parent routine `0x45D72`** is a 3-instruction trampoline (`bsrw; bsrw; rts`) — it sequences two distinct sub-routines.
- **Routine 1 body** spans `0x45D7C..0x45DC2` (78 bytes). Sub-routine entry is `0x45D7C`; its bulk-path RTS at `0x45DC2` is shared with routine 2's early-out path.
- **Routine 2 body** spans `0x45DC4..0x45DF8` (52 bytes). Sub-routine entry is `0x45DC4`; its early-out branches BACK INTO routine 1's body to reach the shared RTS at `0x45DC2` — a tight cross-routine coupling.
- **Three independent control-flow exits** through routine 1: bounds-exceeded RTS at `0x45DA2`, bulk-path RTS at `0x45DC2`, early-out RTS at `0x45DC2` (shared).
- **Two RTS exits** through routine 2: bounds-exceeded RTS at `0x45DD8`, bulk-path RTS at `0x45DF8`. Plus the cross-routine early-out branch back to `0x45DC2` (routine 1's RTS).

### External branch landscape (verified for Option D's proposed span)

I queried the disassembly for any external reference into `0x45DB8..0x45DBD` (Option D's 6-byte span):

```
Bash grep: 0x45db[8-d] → no hits
```

Only references to addresses inside `0x45D72..0x45DF8` from outside the parent routine:
- `0x41F36: bsrw 0x45D72` (parent entry, line 83784) — outside Option D's span
- `0x3A818: jsr 0x45DFA` (next routine, already covered by `opcode_replace 0x045DFA` at [`specs/rastan_direct_remap.json:619-622`](specs/rastan_direct_remap.json#L619-L622)) — outside parent routine
- `0x41F54: beqw 0x45DFA` (line 83790) — same as above

**Option D's span at `0x45DB8..0x45DBD` has zero external branches landing inside it.** Phase A §A.2.a gate-in-design: GREEN.

### Game-state mutations summary

Per Rule 19, any redesign that includes these instructions in its replacement span must reproduce them exactly:

| pc | instruction | role |
|---|---|---|
| `0x45D8C` | `clrw %a5@(568)` | bounds-exceed clear of counter A |
| `0x45D90` | `movew #1, %a5@(5040)` | sets external state flag |
| `0x45D96` | `jsr 0x3BA20` | calls another arcade routine — opaque side effects |
| `0x45D9C` | `movew #1, %a5@(3152)` | initializes counter B |
| `0x45DBE` | `addqw #1, %a5@(568)` | post-bulk-path counter A increment |
| `0x45DD4` | `clrw %a5@(3152)` | bounds-exceed clear of counter B |
| `0x45DF4` | `addqw #1, %a5@(3152)` | post-bulk-path counter B increment |

Option D's span (`0x45DB8..0x45DBD`) excludes ALL seven mutations. They execute natively after the helper returns.

---

## §1.2 Four-option evaluation

### Option A — Replace at `0x45D72` (parent trampoline + both routines)

- **Span:** `0x45D72..0x45DF8` (≈138 bytes spanning parent + routine 1 + routine 2)
- **Branch-target safety:** External entry only at `0x45D72` (Rule 20 OK on this axis), but the helper now subsumes BOTH routines and their cross-routine shared RTS at `0x45DC2`. All internal branches become helper logic.
- **Game-state preservation (Rule 19):** Helper MUST reproduce all 7 mutations enumerated above, plus `jsr 0x3BA20` (an opaque arcade subroutine call). Reproducing arcade JSR semantics inside a Genesis helper is permissible (helpers may JSR back into arcade), but doing so for a span this large transforms the helper into a flow-control replica of two arcade routines plus their parent. This crosses into "control-flow ownership" territory bordering RULES.md Rule 4 ("Forbidden: control-flow ownership") and Rule 7 ("No hidden state machines").
- **Sibling 0x045DE4 handling (Rule 21):** Subsumed; helper handles banks 48..79 path with SKIP semantics (no Genesis emit) but must still update counter B and call back into arcade where needed.
- **Helper complexity:** Highest of all options — must replicate two routines' control flow, branches, three counter mutations, plus a JSR-to-arcade trampoline. Each branch and side effect represents a future drift risk.
- **Spec impact:** 1 entry, 138-byte replacement.
- **State:** **NOT VIABLE.** Helper complexity violates spirit of Rule 4 (helper performs hardware translation, not control-flow replication). Even if mechanically correct, this option creates a 138-byte helper whose bug surface dwarfs the alternatives.

### Option B — Split into two smaller intercepts

- **Span 1 candidate:** `0x45DAE..0x45DC1` (20 bytes — bulk-path body excluding the trailing RTS at `0x45DC2`). Replacement: `JSR helper` (6) + NOPs (14). Original RTS at `0x45DC2` continues to handle the early-out (`beqs 0x45DC2` at `0x45D82`) AND the helper's flow (helper RTS pops to `0x45DB4`, NOPs run, hit RTS at `0x45DC2`).
- **Span 2 candidate:** `0x45DDA..0x45DF7` or similar for routine 2's bulk path (sibling 0x45DE4).
- **Branch-target safety:** Span 1 — `beqs 0x45DC2` at `0x45D82` lands at the original RTS (not in the span). Span 1 is safe. But the helper must INCLUDE the addqw at `0x45DBE` in its work (since it's inside the span). Helper preserves `addqw #1, %a5@(568)` mutation. Span 2 — same shape, different counter.
- **Game-state preservation (Rule 19):** Helper must reproduce both addqw mutations.
- **Sibling 0x045DE4 handling (Rule 21):** Handled in Span 2 (separate intercept) — SKIP banks 48..79; preserve counter B via addqw replication.
- **Helper complexity:** Moderate — two helpers, each translates + counter increment.
- **Spec impact:** 2 entries.
- **State:** **VIABLE** but inferior to Option D. Two entries instead of one; helper carries a counter increment for sibling path that does no Genesis-visible work; more spec surface area than necessary.

### Option C — Defer `0x045DAE` to Build 55b

- Build 55a ships with only `0x59AD4` body hook + `0x03AB00` intercept.
- `0x045DAE` write-through (banks 0..31) still occurs but never reaches Genesis CRAM.
- Visible impact: tilemap palette would render correctly for whatever `0x59AD4` provides, but the second palette source (the `0x45DAE` 32-bank sweep) is missing. From [Cody §1.4](docs/design/Cody_build55_palette_bank_mapping_evidence.md), `0x45DAE` is reached from `0x41F36: bsrw 0x45D72` — this is **inside the PC090OJ April-6 caller cluster** and runs during normal sprite frame setup. Skipping it would visibly disrupt sprite-related palette state (banks 0..3 are tilemap-consumed but the sprite descriptor pre-write at `0x41F36` likely uses these for state staging).
- **State:** **NOT VIABLE for Build 55.** Skipping the `0x45DAE` path is not a partial-correctness deferral — it is a known palette-omission in a frequently-executed path. The locked design already classified this as a required intercept; downgrading it would silently regress the palette on the same frame the locked design intended to fix.

### Option D — Narrower intercept around `jsr 0x3A2D0` copy call

- **Span:** `0x45DB8..0x45DBD` (single 6-byte `jsr 0x3a2d0` instruction)
- **Replacement bytes:** `4EB9 {symbol:genesistan_palette_hook_45dae}` (6 bytes — exact byte-for-byte swap; no NOPs needed)
- **Branch-target safety (Rule 20):** Verified by grep — no external branch lands at `0x45DB8..0x45DBD`. The instruction immediately before (`0x45DB6: moveq #64, %d0`) is fall-through; the instruction immediately after (`0x45DBE: addqw #1, %a5@(568)`) is fall-through. **Phase A §A.2.a gate-in-design: GREEN.**
- **Game-state preservation (Rule 19):** TRIVIALLY satisfied. All seven game-state mutations enumerated in §1.1 are OUTSIDE the span and execute natively.
- **Sibling 0x045DE4 handling (Rule 21):** No replacement; arcade-side `jsr 0x3a2d0` at `0x45DEE` writes to `0x200600` (banks 48..79) which is outside Genesis-line-mappable range. Arcade RAM update has no Genesis-visible effect. Counter B's `addqw` at `0x45DF4` continues to execute natively. Consistent with locked design IGNORE classification.
- **Helper complexity:** Lowest. Helper input contract: `%a0` = source-pointer (workram + idx*128), `%a1` = arcade-RAM dest (`0x200000 + idx*128`), `%d0` = 64 (entry count). Helper computes idx from `%a1`, translates 64 words IF idx == 0, RTS.
- **Helper register-contract (Rule 19 / Rule 22):** The original `jsr 0x3a2d0` clobbers some registers (per arcade convention for copy routines); the helper must observe the same clobber set or save/restore. Register save/restore via `movem.l` is the helper convention used throughout `pc090oj_hooks.s` (see [`apps/rastan-direct/src/pc090oj_hooks.s`](apps/rastan-direct/src/pc090oj_hooks.s)).
- **Spec impact:** 1 entry, 6-byte replacement (no NOP padding).
- **State:** **VIABLE — RECOMMENDED.**

---

## §1.3 Recommended option: D

### Cited reasoning

1. **Branch-target safety (Rule 20) is trivially satisfied.** The single-instruction span has no internal branches and no external branch targets — verified by grep over [build/maincpu.disasm.txt](build/maincpu.disasm.txt). Phase A §A.2.a gate-in-design: GREEN. (Versus Option A which subsumes 138 bytes of complex flow; versus Option B which requires careful boundary placement to avoid the shared RTS at `0x45DC2`.)

2. **Game-state preservation (Rule 19) is automatic.** All seven game-state mutations identified in §1.1 (counter A clear/increment, counter B init/clear/increment, external state flag at `%a5@(5040)`, JSR to arcade `0x3BA20`) are OUTSIDE the span and execute natively after the helper RTSs. (Versus Option A which must replicate all seven; versus Option B which must replicate two counter increments.)

3. **Helper register-contract is well-defined.** At the JSR site (`0x45DB8`), the prior 6 instructions (`0x45DA4..0x45DB6`) establish a clean register state: `%a0` = workram source ptr, `%a1` = `0x200000 + idx*128` arcade dest ptr, `%d0` = 64. Helper reads these, translates iff bank base ∈ {0..3}, RTS. Mirrors the helper convention used by `0x59AD4` body replacement and the existing PC090OJ helpers.

4. **Sibling 0x045DE4 handling (Rule 21) is consistent with locked-design IGNORE.** No second intercept needed; arcade-side write to `0x200600` (banks 48..79) has no Genesis-visible effect. Counter B's increment at `0x45DF4` runs natively.

5. **Spec surface area is minimal.** 1 new `opcode_replace` entry, 6-byte replacement, no NOPs. (Versus Option A's 138-byte body replacement; versus Option B's 2-entry split with NOP padding.)

6. **All 10 Andy v3.2 §1.8 architectural invariants preserved.** No Genesis lifecycle introduced; helper RTS-returns; no shadowing; no scaffolding; v3.1/v3.2 closures untouched; opcode_replace at `0x3AF04` untouched; `_bootstrap` and `_vblank_service` closures intact; D6-fix patches preserved.

### Comparison to Cody's noted redesign options

Cody's Phase A §"Redesign Required Before Phase B" enumerated two minimal redesign options:
- **Option (1) Replace at `0x45D72` entry** ↔ Andy Option A — NOT VIABLE per §1.2.
- **Option (2) Split into separate safe replacement entries** ↔ Andy Option B — VIABLE but inferior to Option D.

Cody's enumerated set did NOT include the "narrower around copy call" form. Andy Option D supersedes both of Cody's enumerated options as a strictly less-invasive fix.

---

## §1.4 Revised Cody implementation plan

### Locked Build 55 elements UNCHANGED

The following elements of [`docs/design/Andy_build55_palette_translation_design.md`](docs/design/Andy_build55_palette_translation_design.md) remain locked and unchanged by this redesign:

- §1.2 fix shape: `0x59AD4` body replacement helper UNCHANGED
- §1.3 bank-mapping rule (`bank & 0x03 → Genesis line`; banks ≥ 4 SKIP) UNCHANGED
- §1.4 conversion path (xBGR-555 → Genesis CRAM via [`apps/rastan/src/main.c:1008-1017`](apps/rastan/src/main.c#L1008-L1017)) UNCHANGED
- §1.5 sprite handling (Build 56 follow-up) UNCHANGED
- §1.6 high-bank treatment (SKIP) UNCHANGED
- §1.7 bypass intercept for `0x03AB00` UNCHANGED
- `genesistan_palette_hook_59ad4` helper signature, file location, and behavior UNCHANGED
- `genesistan_palette_hook_3ab00` helper signature, file location, and behavior UNCHANGED

### REVISED — `0x045DAE` intercept

Replace the single `jsr 0x3a2d0` at `arcade_pc 0x045DB8` with `jsr genesistan_palette_hook_45dae`.

#### Helper specification

| field | value |
|---|---|
| Helper symbol | `genesistan_palette_hook_45dae` |
| File location | [`apps/rastan-direct/src/palette_hooks.s`](apps/rastan-direct/src/palette_hooks.s) (same file as 59ad4 / 3ab00 helpers) |
| Helper convention | RTS-returning leaf; saves/restores all clobbered scratch registers via `movem.l` per `pc090oj_hooks.s` precedent |
| Input contract at JSR | `%a0` = source-pointer (workram + idx*128); `%a1` = arcade-RAM dest (`0x200000 + idx*128`, idx ∈ 0..7); `%d0` = 64 (arcade-copy entry count) |
| Output | If `(%a1 - 0x200000) == 0` (idx == 0, banks 0..3): translate 64 source words at `%a0` from xBGR-555 to Genesis CRAM and stage to `staged_palette_words[0..63]`; set `palette_dirty := 1`. Otherwise: no-op (banks 4..31 not Genesis-consumed). |
| Side effects on registers | All scratch restored before RTS. `%a5` untouched. |
| Architecture compliance | RTS-returning helper (Rule 4); no flow-control ownership; staging-then-commit pattern preserved; `palette_dirty` flag follows existing v3.2 convention. |

#### Pseudocode

```asm
genesistan_palette_hook_45dae:
    movem.l %d0-%d3/%a0-%a2, -(%sp)         ; save scratch
    movea.l %a1, %a2
    suba.l  #0x00200000, %a2                 ; %a2 = bank-base offset
    cmpa.l  #0x00000080, %a2                 ; idx >= 1?  banks >= 4?
    bcc.s   .skip                            ; if so, no Genesis emit
    ; idx == 0: translate 64 source words → staged_palette_words[0..63]
    lea     staged_palette_words, %a2
    moveq   #63, %d3
.loop:
    move.w  (%a0)+, %d0                      ; raw arcade word (xBGR-555)
    ; Step A→B: xBGR-555 → Genesis CRAM (per main.c:1008-1017)
    ;   r5 = raw[4:0],  g5 = raw[9:5],  b5 = raw[14:10]
    ;   rn = ((r5 >> 2) & 0x07) << 1
    ;   gn = ((g5 >> 2) & 0x07) << 1
    ;   bn = ((b5 >> 2) & 0x07) << 1
    ;   genesis = (bn << 8) | (gn << 4) | rn
    ; ... bit-twiddle implementation ...
    move.w  %d1, (%a2)+
    dbra    %d3, .loop
    move.b  #1, palette_dirty
.skip:
    movem.l (%sp)+, %d0-%d3/%a0-%a2
    rts
```

(Cody implements the bit-twiddle Step A→B in assembly, reusing the same conversion shape Cody is already implementing for `genesistan_palette_hook_59ad4`. Helper does NOT call original `0x3a2d0`; arcade-side palette RAM at `0x200000` is not Genesis-consumed, consistent with the locked design's `0x59AD4` body-replacement decision.)

#### `opcode_replace` entry

```json
{
  "arcade_pc": "0x045DB8",
  "original_bytes": "4EB90003A2D0",
  "replacement_bytes": "4EB9{symbol:genesistan_palette_hook_45dae}",
  "note": "Build 55 palette bypass intercept at 0x045DB8 (helper genesistan_palette_hook_45dae). Single-instruction JSR-target swap: replaces arcade copy 'jsr 0x3a2d0' with Genesis-side palette translation helper. Helper translates 64 source words at %a0 from xBGR-555 to Genesis CRAM and stages to staged_palette_words[0..63] iff %a1 == 0x200000 (idx==0, banks 0..3 tilemap-consumed); skips for idx>=1 (banks 4..31). Surrounding routine flow at 0x45D7C..0x45DC2 (counter A check, bounds, addqw, RTS) executes natively. Sibling 0x45DE4/0x45DEE path (banks 48..79) intentionally not intercepted — outside Genesis-line-mappable range. Replaces locked-design 0x045DAE 74-byte body replacement after Cody Phase A precheck flagged external branch target into span. See Andy_build55_palette_045dae_redesign.md."
}
```

### Updated count_guard

| | locked design | Option D redesign |
|---|---:|---:|
| Build 54 baseline `count_guard` | 90 | 90 |
| New entries | +3 (`0x59AD4`, `0x03AB00`, `0x045DAE`) | +3 (`0x59AD4`, `0x03AB00`, `0x045DB8`) |
| Build 55 target `count_guard` | 93 | 93 |

**Unchanged: 90 → 93.**

### Updated `required_symbols`

Same 3 helpers as locked design:
- `genesistan_palette_hook_59ad4`
- `genesistan_palette_hook_3ab00`
- `genesistan_palette_hook_45dae`

(Symbol name `genesistan_palette_hook_45dae` is retained for continuity with the path identified by `0x045DAE`. The name is informative; the actual JSR site is `0x045DB8` inside that path.)

### Phase A gate requirements for new span

Cody must verify before Phase B implementation:

- **§A.1 register-contract gate (input registers):** Verify `0x45DB8` JSR's three input registers (`%a0`, `%a1`, `%d0`) are well-defined immediately before the JSR (set up by `0x45DA4..0x45DB6` — verified by Andy in §1.1 above).
- **§A.2.a span-safety gate (no external branches into span):** Verify no instruction in `build/maincpu.disasm.txt` branches to any address in `0x45DB8..0x45DBD`. Andy has verified this by grep; Cody should re-verify mechanically.
- **§A.2.b fall-through side effects:** None inside the 6-byte span. The post-JSR instruction (`0x45DBE: addqw #1, %a5@(568)`) is OUTSIDE the span and is the routine's natural fall-through; it executes after helper RTS.
- **§A.3 combined gate:** Expected GREEN.
- **Helper register clobber audit:** Helper must save/restore any register the arcade caller relies on across the JSR. Original `jsr 0x3a2d0` is an arcade copy routine — Cody must determine its callee-save contract from the arcade body and ensure the helper observes it.

### Verification gates (UNCHANGED)

All Build 55 verification gates from the locked design remain in force:
- Postpatcher `count_guard = 93`
- Postpatcher byte count measured-not-presumed (Build 54 D6-fix discipline)
- D00778 invariant unchanged
- VRAM roundtrip unchanged
- Symbol resolution for all three new helpers
- All 10 Andy v3.2 §1.8 invariants preserved (verified §1.5)
- Build 55 boot CRAM populated with translated palette before first frame (visual gate)

---

## §1.5 Architecture compliance verification

### 10 invariants per Andy v3.2 §1.8

| # | Invariant | Preserved by Option D? | Reasoning |
|---:|---|---|---|
| 1 | No Genesis-side lifecycle introduced | YES | Helper is RTS-returning leaf; no Genesis-owned loop or scheduling |
| 2 | Helpers RTS-return, no flow-control ownership | YES | Helper executes single linear path + early-skip, RTSs immediately |
| 3 | No memory shadowing | YES | Helper writes to `staged_palette_words` (existing staging buffer); no new shadow region |
| 4 | No scaffolding | YES | Helper is production-intent; no test paths, no debug-only branches |
| 5 | v3.1 closures intact (`_3b930`, `_54810` D6-fix discipline) | YES | Helpers untouched by this redesign |
| 6 | v3.2 polymorphic dispatch contract at `0x03AD44` | YES | Untouched |
| 7 | `opcode_replace` at `0x03AF04` (vector preservation closure) | YES | Untouched |
| 8 | `_bootstrap` closure (one-time init only, no re-entry) | YES | No `_bootstrap` modification |
| 9 | `_vblank_service` closure (palette gate at lines 166-170) | YES | Helper sets `palette_dirty`; `_vblank_service` reads and commits per existing pattern |
| 10 | D6-fix patches preserved (`_3b930`/`_54810` save/restore) | YES | Untouched |

**10/10 invariants preserved.**

### Task-specific compliance

| Item | Status | Notes |
|---|---|---|
| Game-state counters at `%a5@(568)` and `%a5@(3152)` preserved (Rule 19) | YES | All counter mutations OUTSIDE Option D's 6-byte span; execute natively |
| Branch-target safety verified for new span (Rule 20) | YES | grep verified zero external branches into `0x45DB8..0x45DBD` |
| Sibling `0x045DE4` handling specified (Rule 21) | YES | No intercept; arcade-side write to banks 48..79 has no Genesis-visible effect |
| No broadening (Rule 18) | YES | `0x59AD4`, `0x03AB00`, conversion, bank mapping, sprite, high-bank UNTOUCHED |
| No new evidence collection (Rule 24) | YES | Used only existing Cody evidence + locked design + disassembly |
| No sprite expansion (Rule 25) | YES | Sprite path remains Build 56 follow-up |
| No broad NOP audit (Rule 26) | YES | Only the single 6-byte JSR replacement; no NOPs introduced |
| Phase A gate-in-design (Rule 23) | GREEN | §1.4 documents gate verification |

---

## Phase 2 Integrity

- §1.1 parent caller chain analyzed: YES
- §1.2 four options evaluated: YES (A NOT VIABLE; B VIABLE-inferior; C NOT VIABLE; D VIABLE-recommended)
- §1.3 recommended option: **D** — narrower intercept around `jsr 0x3a2d0` copy call at `0x045DB8`
- §1.4 revised Cody implementation plan produced: COMPLETE
- §1.5 architecture compliance: 10/10 invariants preserved by Option D — YES
- Game-state counters preserved (Rule 19): YES
- Branch-target safety verified (Rule 20): YES
- Sibling 0x045DE4 handling specified (Rule 21): YES
- All conclusions cited (Rule 17): YES
- No broadening (Rule 18): YES — locked elements untouched
- No new evidence collection (Rule 24): YES
- No sprite expansion (Rule 25): YES
- No broad NOP audit (Rule 26): YES
- No source/spec/tool modifications: YES
- All STOP conditions either passed or documented: YES
- STOP triggered: NO — Cody is unblocked to implement Build 55 with the revised `0x045DAE` intercept (`opcode_replace` at `0x045DB8` instead of `0x045DAE`).
