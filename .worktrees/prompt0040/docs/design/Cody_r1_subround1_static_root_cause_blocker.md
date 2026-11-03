# Cody — R1 Subround-1 Static Root-Cause Blocker

**Date:** 2026-10-19

**Scope:** Static ROM/disassembly/contract analysis only. No MAME gameplay, trace, route, save state, or new harness.

**Accepted baseline:** Build 0455, source `bb09135dee3e6491a844c84635a70710291a33f6`.
**Result:** A durable stale map-selector-stream pointer is proven and explains the persistent premature auto-walk class, but the mandatory Build-0445 versus Build-0446 endpoint movement cannot be reconciled from the preserved artifacts. Per the task gate, no production fix and no Build 0456 were made.

## Resume and evidence discipline

- The invalid uncommitted passive watcher `tools/mame/scripts/r1_subround1_transition_arm_capture.lua` was removed. It produced no accepted evidence.
- Andy's three reports were read in full and left unchanged:
  - `Andy_build0442_0446_subround1_early_end_regression.md`
  - `Andy_r1_subround1_exact_stale_reference.md`
  - `Andy_r1_subround1_0442_0446_root_cause.md`
- Tighe's hardware results are retained as facts: 0442 good; 0443/0444 crash; 0445 playable and early near Segment 11; 0446 playable and early near Segment 13; later descendants remain affected.
- Exact preserved ROMs, original arcade bytes, checked-in Ghidra exports, generated address maps, and current source/spec were used. No nearby commit was substituted for an uncommitted historical artifact.

## Original glyph renderer contract

The semantic arcade entry is `0x03BB48`; `0x03BD48` was the pre-reflow Genesis runtime entry.

The original routine:

1. copies selector/mode `D0` to `D1`;
2. masks `D0` to seven bits and multiplies it by four;
3. addresses the pointer table at arcade `0x03BB7C`;
4. loads `[destination.l, attribute.w, zero-terminated bytes...]`;
5. emits attribute+glyph words, or attribute+space words when the input low byte is negative;
6. consumes the zero terminator and returns.

Contract:

- input: `D0`; descriptor table/data; no stack arguments;
- clobbers: `D0`, `D1`, `D2`, `A0`, `A1`, CCR;
- preserves: `D3-D7`, `A2-A6`, including `A5`;
- final `D0=0`; `A0` is one byte beyond the terminator; `A1` advances four bytes per character;
- stack is balanced;
- the terminating `move.b`/`beq` leaves `Z=1`, `N=V=C=0`, with `X` unchanged;
- memory effects are the two original PC080SN words per emitted character.

All 48 direct callers in Builds 0442, 0445, 0446, and 0455 are the same frontend/state-display caller family in the `0x03A5xx..0x03B8xx` runtime range. No steady-state gameplay caller exists. Post-return inspection finds no caller that consumes `D3` before replacing it or returning.

## Native glyph renderer contract and D3

Build 0442's byte-neutral wrapper at runtime `0x03BD48` calls the native worker at `0x072196`. Builds 0445/0446 move the callable entry to `0x03BD4A`, perform selector preparation and PC-relative table-base setup in the wrapper, call the same worker, then return.

The worker uses `D3` as scratch, which violates the original preservation contract. Nested staging helpers save/restore their own broader scratch set; `A5` and stack balance are preserved; source/destination pointer advancement and terminal flags otherwise match the original.

This D3 defect predates known-good Build 0442. More decisively, no gameplay caller reaches this renderer and none of the frontend callers uses returned D3. It cannot feed the map-stream initializer or advance worker, which explicitly load/clear their own `D0/D1/A1/A4` state. D3 is therefore a real separate contract defect but is **not proven causal** and was not changed.

## Builds 0443–0446 glyph crash and correction

- 0443/0444: reflow moved the glyph table, but the native worker retained absolute `movea.l #0x0003BD7C,A0`. The reported `GEN PC 0x000721AA / FAULT 0xBEA80003` is the resulting odd descriptor dereference.
- 0445: the wrapper changed to PC-relative setup, but `lea +8(PC),A0` resolves to `0x03BD5C`, the wrapper's `RTS`, two bytes before the table at `0x03BD5E`.
- 0446: `lea +10(PC),A0` resolves correctly to `0x03BD5E`.

The 0445 base does not describe an alternative valid record walk. For selector zero it loads `A0=0x4E750003`; subsequent selectors similarly produce odd garbage such as `0xBE7A0003`. If invoked, the next longword descriptor read address-errors. Consequently 0445 has no valid returned register/CCR/pointer/memory-write state from this path. The prior claim that it returns after writing a different number of glyphs is rejected.

## Exact 0445-versus-0446 artifact difference

The full preserved ROM diff contains exactly three bytes:

| ROM offset | 0445 | 0446 | meaning |
|---:|---:|---:|---|
| `0x00018F` | `0x40` | `0x43` | header checksum byte |
| `0x03BD55` | `0x08` | `0x0A` | glyph-table LEA displacement |
| `0x2958DB` | `0x35` | `0x36` | crash-screen build digit |

Only the glyph displacement changes executable semantics. The 48-call frontend caller set, all gameplay code, the map-stream initializer, and the map-stream data are otherwise byte-identical. Since executing the 0445 glyph path would fault rather than return altered live state, static evidence supplies no causal bridge from this byte to a playable gameplay endpoint shift.

## Proven stale map-selector-stream pointer

The original initializer at arcade `0x0503BC..0x0503DA` computes:

```text
A1 = 0x050EE0 + word(A5+0x013E)
D1 = byte(A1)
D0 = 0x050F6B + D1
A5+0x10C6 = D0
```

`0x050EE0` is relocated through the normal absolute-address path. The `MOVE.L #imm,D0` at arcade `0x0503CE` is not. A Build-0305 byte-neutral `opcode_replace` hard-codes `0x00051171` in `specs/rastan_direct_remap.json`. It is a historical generated address embedded as policy and does not follow later `shift_deltas`.

Exact mapping/data proof:

| build | `address_map.json` / unique ROM location for arcade `0x050F6B` | embedded operand | error |
|---|---:|---:|---:|
| 0442 | `0x051171` | `0x051171` | 0 |
| 0443/0444 | `0x051173` | `0x051171` | -2 bytes |
| 0445/0446 | `0x051153` | `0x051171` | +30 bytes |
| current 0455 | `0x051155` | `0x051171` | +28 bytes |

The original table's first 64 bytes occur uniquely at each mapped address. The embedded operand signature occurs once in each inspected ROM at the initializer. This directly refutes the report claim that all relevant gameplay inputs were relocated correctly.

## Static causal path for the persistent early-end class

The selector stream is not merely presentation data:

1. `0x0503CE..0x0503D6` seeds `A5+0x10C6` from the selector stream.
2. `FUN_000558A2` calls `FUN_000558E0` after four strips times sixteen groups.
3. `FUN_000558E0` clears `A5+0x10CC`, increments `A5+0x10C6`, publishes `*(A5+0x10C6)` to `A5+0x10A8`, and increments progression `A5+0x013E`.
4. `player_main_update_51090` reaches `FUN_00052732` through the retained player-state dispatcher.
5. `FUN_00052732` compares `A5+0x10A8` against 4, 5, and 6. Any match writes player mode `A5+0x10E8=7`, the scripted end/auto-walk mode.

With the correct base, R1 selector values for progression `0x00..0x16` have nonzero directional selections only at the intended late indices and never present event 4/5/6 prematurely. With the 0445/0446 +30-byte stale base, the decoded R1 sequence contains event `4` at progression index `0x0C`, then `1,1,6,...,7`. Thus retained arcade code enters mode 7 before the true final records/door. Current 0455's +28 error similarly introduces event 4 at index `0x0E` and event 6 at `0x14`.

This is a complete static chain for the persistent regression class:

```text
title/glyph reflow changes copied-data address
  -> hard-coded Build-0305 operand remains 0x051171
  -> A5+0x10C6 points 30 bytes late in 0445/0446
  -> FUN_000558E0 publishes premature selector 4 to A5+0x10A8
  -> FUN_00052732 writes A5+0x10E8 = 7
  -> scripted auto-walk begins before true final map/door
```

Build 0442 works because its then-current map for `0x050F6B` was exactly `0x051171`.

## Why the task remains blocked

The prompt requires one root cause to explain both persistent early termination and the distinct 0445-versus-0446 endpoint movement. The proven stale selector pointer explains the former but cannot distinguish 0445 from 0446: both ROMs load the same `0x051171`, contain the same correctly relocated table at `0x051153`, and decode the same premature selector sequence.

The only executable byte difference is the glyph LEA. Its callers are frontend-only, and its 0445 value cannot return a subtly altered state: it creates an odd invalid descriptor pointer and faults if executed. Therefore neither proposed branch is statically proven:

- A (glyph change returns live state that feeds map progression): disproven by the 0445 faulting path and absence of gameplay callers;
- B (another effective artifact difference): disproven within the preserved ROM bytes, but not reconcilable with the authoritative hardware endpoint observations.

The exact unresolved static dependency is the identity/effective execution difference between the hardware-tested 0445 and 0446 images beyond the three preserved artifact bytes. Static analysis of these files cannot manufacture that missing distinction. This is not a request for a gameplay trace; none was attempted.

## Deferred correct fix shape

Once the 0445/0446 contradiction is resolved or Tighe authorizes treating it as independent, the stale pointer must be fixed declaratively: remove the literal Build-0305 runtime address and make arcade target `0x050F6B` resolve through the final shift/address map. A root-specific verifier should assert that the final operand equals the generated map for `0x050F6B` on every configured ROM. No historical `+30/-30`, segment count, camera maximum, forced player X, delayed transition, fake door, or auto-walk suppression is acceptable.

No source/spec production change, ROM build, build-number consumption, Phase D, or Phase E occurred.
