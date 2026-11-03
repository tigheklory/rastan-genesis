# Build 0473 — Caller-Specific Retained-Cut Preservation

Date: 2026-10-22

Agent: Cody

Task: RG-014 caller-specific retained-cut preservation reduction

## Result

Build 0473 is a valid, performance-neutral candidate awaiting Tighe's real-Genesis
acceptance. It preserves accepted Build 0472 behavior in the established automated
suite and exactly matches Build 0472's deterministic rope result.

- baseline: accepted Build 0472
- produced build: 0473
- exact ROM-producing source: `f6e975b864af2aca7bdf24b0a40a9db43bd62f59`
- normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0473.bin`
- SHA-256: `42cac0085a0078ffbc4293e493ece95280e854d4d2b5bf4512756bb095ded717`
- size: 2,739,896 bytes
- build counter: 472 -> 473
- configured family: normal, `_d`, `_s`, `_do`, `_c`, `_full_hud`, and
  `_invincible`, all present and configuration-verified
- canonical replacement inventory: 228 opcode-replacement sites; expected Genesis
  coverage `0x29CEB8`; the established shift engine applied 81 shift replacements
- candidate status: **AWAITING TIGHE HARDWARE ACCEPTANCE**

The immutable `accepted/build-0472` reference was not moved, and no
`accepted/build-0473` reference was created.

## Scope and semantic boundary

The PC090OJ semantic cut is unchanged: retained arcade actor lifecycle, animation,
position, attribute, visibility, and ordering decisions remain above the cut; the
already-retired PC090OJ descriptor/object-record production, object-RAM mirror/scan,
and record-decoding tail remains below it. The native path continues to generate
final Genesis semantic pieces and SAT entries directly.

This build removes no additional chip tail and introduces no shadow, mirror, virtual
chip RAM, compatibility layer, gameplay authority, fallback, or state machine. It is
an ABI-ownership optimization around the existing semantic cut, not a new native
conversion. Existing compatibility outside this path is unchanged.

The only production behavior changed is preservation ownership at retained arcade
cuts `0x041DAE` and `0x045DFA`:

1. each gameplay hook saves `D4/D6/A2-A6` once;
2. it calls the matching internal stage dispatcher;
3. it calls the internal gameplay-only finalizer;
4. it restores `D4/D6/A2-A6` once and returns to retained arcade code.

The original operation's proven clobber set `D0-D3/D5/D7/A0-A1` is no longer
restored solely for these retained callers. Conservative public dispatcher wrappers
and the public VBlank finalizer retain their prior ABI. The required inner `D5/A1`
actor-loop save and `D6` semantic-queue save remain intact.

No finalizer semantic instruction, clipping, residency, palette, SAT format/order,
HUD behavior, gameplay behavior, or retained-code replacement size changed. Address-
map comparison shows no changed `shift_delta`; only expected native helper target
addresses moved.

## Helper contract inventory

| Entry | Caller(s) | Preservation before | Build 0473 contract |
|---|---|---|---|
| `native_stage_dispatch_41dae` | conservative/public-capable wrapper | `D0-D7/A0-A6` | unchanged wrapper; calls internal entry |
| `native_stage_dispatch_41dae_retained_cut` | retained cuts only | new | no redundant outer frame; hook owns `D4/D6/A2-A6` |
| `native_stage_dispatch_45dfa` | conservative/public-capable wrapper | `D0-D7/A0-A6` | unchanged wrapper; calls internal entry |
| `native_stage_dispatch_45dfa_retained_cut` | retained cuts only | new | no redundant outer frame; hook owns `D4/D6/A2-A6` |
| `.Lnative_emit_actor_common` | both internal dispatchers | `D5/A1` | unchanged and required across nested generated probes |
| `.Lnq_emit_lane` | gameplay/frontend finalizers | word `D6` | unchanged and required across piece finalization |
| `pc090oj_native_emit_pass` | VBlank and other public callers | `D0-D7/A0-A3` plus `A4` on gameplay | conservative public gameplay ABI unchanged |
| `pc090oj_native_emit_pass_retained_cut` | retained cuts only | new | gameplay-only internal entry under hook frame |

There are no saved-path early returns, double restores, or exits that bypass the
outer restore. Public frontend finalization retains its own established frame.

## Assembled ABI and calculated cost

Final linked symbols from the Build 0473 ELF:

| Symbol | Address |
|---|---:|
| `genesistan_pc090oj_hook_target_41dae` | `0x073BD8` |
| `genesistan_pc090oj_hook_target_45dfa` | `0x073C18` |
| `native_stage_dispatch_41dae` | `0x074146` |
| `native_stage_dispatch_41dae_retained_cut` | `0x074154` |
| `native_stage_dispatch_45dfa` | `0x0742F6` |
| `native_stage_dispatch_45dfa_retained_cut` | `0x074304` |
| `pc090oj_native_emit_pass` | `0x074E3A` |
| `pc090oj_native_emit_pass_retained_cut` | `0x074E5E` |

Object disassembly encodes the retained-cut save as MOVEM mask `0x0A3E` and the
restore as `0x7C50`, exactly `D4/D6/A2-A6`.

| Static preservation metric | Build 0472 | Build 0473 | Change |
|---|---:|---:|---:|
| outer save/restore instructions | 6 | 2 | -4 |
| longword transfers | 56 | 14 | -42 |
| maximum outer stack | 60 bytes | 28 bytes | -32 bytes |
| calculated 68000 preservation cost | 496 cycles | 132 cycles | **-364 cycles/pass** |

The assembled structure matches RG-013's prediction. These are static 68000 timing
calculations, not a universal runtime or frame-rate claim.

## Validation

All runtime validation used the MAME USA/NTSC `genesis` driver. No original-arcade
trace, new gameplay route, input movie, save-state exploration, profiling
instrumentation, AI navigation, or bot was created.

- source assembly/link and bounded preservation verifier: **PASS**
- pre/post boot guards and canonical gate: **PASS**
- R1-S1 gameplay entry: **PASS**, including 240 post-entry frames and zero address,
  bus, illegal-instruction, or crash-handler entries
- seven production epochs: **PASS**, full Plane-A and fixed Plane-B LUT checks
- generated sprite/frame verifier: **PASS** (`1200` primary, `416` secondary,
  `38` generic, `1898` universal-general, `24` universal-specialized, and `60`
  compact-death native records)
- direct-dispatch plus retained-cut ABI verifier: **PASS**
- native HUD verifier: **PASS**, including 57 dirty cases, unchanged-frame no-rebuild,
  lifecycle dirtiness, and accepted score/1UP geometry
- fixed30: **PASS**, 1,798 frames and zero live FG C-window writes
- final-life static map: **PASS**, `0x03A3C0 -> 0x03B332`
- final-life zero-input: **PASS**, GAME OVER at frame 3,576 after three death entries
- writer-event/presentation regression: **PASS**, score `001234`, dirty consumed,
  seven semantic records, both SAT banks observed, Continue/re-entry complete at
  frame 4,429
- RG-004 Continue/frontend: **PASS** at frame 2,728; 83 staged/83 VRAM names,
  zero name mismatches, zero nonblank outside-panel cells, staged CRAM equals CRAM
- RG-004 attract/title: **PASS** at frame 7,215; natural demo and death observed;
  all four first-title, second-title, and terminal CRAM lines match
- complete seven-ROM family and invincibility contract: **PASS**

Presentation-equivalence coverage therefore retains semantic queue behavior,
generated frames, SAT construction, palette selection, residency, Plane A/B, and HUD.

## Deterministic rope benchmark

The established `_invincible` benchmark and inputs were reused unchanged.

| Build | Trial 1 | Trial 2 | Trial 3 | Median |
|---|---:|---:|---:|---:|
| accepted 0472 | 795 | 795 | 795 | 13,267.083 ms |
| candidate 0473 | 795 | 795 | 795 | 13,267.083 ms |

Deterministic: **YES**. Frame change: `0`. Time change: `0.000 ms`. Result:
**SAME**. The benchmark proves no regression on this exact route; it does not measure
the calculated instruction saving directly or establish universal CPU performance.

The smaller, exact caller ABI and 32-byte outer-stack reduction are worthwhile
architectural simplifications with no observed regression, so the recommendation is
to retain the candidate pending Tighe's hardware test. It is not accepted yet.

## Deferred and untouched work

- reverse-residency `D0/D2` mask reduction: untouched
- direct guarded Large/Small Bat fast paths: untouched
- persistent bat handles: untouched
- actor-family classifier, PC080SN, dirty flags, HUD, clipping, residency, palette,
  SAT semantics, and gameplay: untouched
- full HUD: known absent in normal gameplay and untouched

## Files and tooling

ROM-producing commit files:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `tools/translation/verify_pc090oj_direct_dispatch.py`

Bookkeeping files added/updated after validation:

- this report
- `AGENTS_LOG.md`

Existing project tools reused: the Makefile build/gate/family pipeline, generated
address map and disassembly, direct-dispatch/frame/HUD verifiers, gameplay-entry and
epoch gates, fixed30 trace, final-life regression, HUD event regression, RG-004
frontend probe, and deterministic rope benchmark.

New tooling created: none. The existing direct-dispatch verifier was extended with
the bounded retained-cut ABI/stack contract because it already owns the relevant
dispatch and finalizer structural checks.

Concurrent RG-011/RG-012/RG-013 reports and decompilation, audio work, Palette
Composer work, and unrelated user changes remain preserved and unstaged.

## USER MUST VERIFY

On real NTSC Genesis hardware, Tighe should verify normal Build 0473 through R1-S1:
initial 1UP/score placement, player and enemy sprite geometry/palettes/order during
ordinary movement and the first rope attachment, damage/death presentation, score
updates, final-life GAME OVER, Continue, and gameplay re-entry. Confirm no missing,
corrupt, flickering, or reordered sprites compared with accepted Build 0472.

## Status

Build 0473 is produced, consumed, automated-validation clean, and performance-neutral.
Hardware acceptance is pending. STOP.
