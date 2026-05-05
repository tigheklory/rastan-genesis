# Cody Build 55 Palette Phase A Block

Type: Phase A precheck-only STOP report (read-only)
Build context: rastan-direct Build 0054 baseline

## Outcome

- §A.1 register-contract gate: **GREEN**
- §A.2 span-safety gate: **RED-BRANCH**
- §A.3 combined gate: **STOP** (Phase B blocked)

No Phase B implementation work was performed.

---

## §A.1 Register-Contract Verification (`0x59AD4`)

Mutated-by-original routine set from `0x59AD4` body:
- `%a0`, `%a1`, `%d0`, `%d1`, `%d2`, `%d3`, `%d6`

Evidence for body mutation source:
- `build/maincpu.disasm.txt` at `0x59AD4..0x59B18`.

Per-caller post-call scan result (next instructions until next `BSR/JSR/RTS`):

| caller arcade_pc | call kind | immediate post-call behavior | reads mutated regs before rewriting? |
|---|---|---|---|
| `0x511BC` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x511D0` | `jsr` | `nop; rts` | NO |
| `0x56136` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5614A` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5615C` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5616E` | `jsr` | `rts` | NO |
| `0x56184` | `jsr` | `rts` | NO |
| `0x56198` | `jsr` | `rts` | NO |
| `0x575FE` | `bsrw` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x57610` | `bsrw` | compares/increments memory fields, then `rts` | NO |
| `0x57816` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5782A` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5783E` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x57850` | `jsr` | `rts` | NO |
| `0x598C2` | `bsrw` | branches, then recomputes `%d0/%d1/%a0` before next call | NO |
| `0x598F0` | `bsrw` | `nop`, then memory compares/increments | NO |
| `0x5999A` | `bsrw` | memory compares/increments then `rts` | NO |
| `0x599F0` | `bsrw` | rewrites `%a0/%d0/%d1`, then next call path | NO |
| `0x59A20` | `bsrw` | rewrites `%a0/%d0/%d1`, then next call path | NO |
| `0x59A50` | `bsrw` | rewrites `%a0/%d0/%d1`, then next call path | NO |
| `0x59A80` | `bsrw` | memory compare/increment, then `rts` | NO |
| `0x59E06` | `jsr` | works on `%d5`, rewrites `%d0` before compare, then `rts` | NO |
| `0x5A364` | `jsr` | immediate `bsrw 0x5a38e` | NO |
| `0x5A3BA` | `jsr` | rewrites `%a1/%a0/%d0/%d1/%d2`, then `bsrw` | NO |
| `0x5A3EC` | `jsr` | rewrites `%a1/%a0/%d0/%d1/%d2`, then `bsrw` | NO |
| `0x5A41E` | `jsr` | rewrites `%a1/%a0/%d0/%d1/%d2`, then `bsrw` | NO |
| `0x5A450` | `jsr` | rewrites `%a1/%a0/%d0/%d1/%d2`, then `bsrw` | NO |
| `0x5A488` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5A49C` | `jsr` | rewrites `%a0/%d0/%d1`, then next call | NO |
| `0x5A4B0` | `jsr` | rewrites `%d1/%a1/%a0` before use, then `jsr` | NO |

Summary:
- Dependent callers: **0 / 30**
- Gate result: **GREEN**

Caller evidence list:
- `build/maincpu.disasm.txt` lines containing all 30 call sites and immediate neighborhoods: `0x511BC`, `0x511D0`, `0x56136`, `0x5614A`, `0x5615C`, `0x5616E`, `0x56184`, `0x56198`, `0x575FE`, `0x57610`, `0x57816`, `0x5782A`, `0x5783E`, `0x57850`, `0x598C2`, `0x598F0`, `0x5999A`, `0x599F0`, `0x59A20`, `0x59A50`, `0x59A80`, `0x59E06`, `0x5A364`, `0x5A3BA`, `0x5A3EC`, `0x5A41E`, `0x5A450`, `0x5A488`, `0x5A49C`, `0x5A4B0`.

---

## §A.2 Span-Safety Verification (`0x045DAE` replacement span)

Proposed replacement span under check:
- `0x045DAE..0x045DF8`

### §A.2.a External branch targets into the span

External target found:
- `0x45D76: bsrw 0x45DC4`

This is a branch from outside the proposed replacement entry point into the middle of the proposed span (`0x45DC4` is inside `0x45DAE..0x45DF8`).

Additional internal branch targets inside span:
- `0x45D82: beqs 0x45DC2`
- `0x45DCA: beqs 0x45DC2`
- `0x45DD2: bcss 0x45DDA`

Evidence:
- `build/maincpu.disasm.txt` around `0x45D72..0x45DF8`.

Gate result for branch safety: **RED-BRANCH**.

### §A.2.b Required fall-through side effects

Observed inside span:
- path 1 updates `%a5@(568)` (`addqw #1,%a5@(568)` at `0x45DBE`) then returns at `0x45DC2`.
- path 2 updates `%a5@(3152)` (`addqw #1,%a5@(3152)` at `0x45DF4`) then returns at `0x45DF8`.

Because §A.2.a already fails (external branch into span), Phase A stops regardless.

---

## §A.3 Combined Gate Decision

- §A.1: GREEN
- §A.2: RED-BRANCH
- Combined: **STOP**

Phase B is blocked by mandatory gate rule.

---

## Redesign Required Before Phase B

Observed blocker implies the `0x045DAE..0x045DF8` single-entry function-body replacement is unsafe in current shape.

Minimal redesign options to resolve before implementation:
1. Replace at `0x45D72` entry (covering both internal paths) so no external branch lands in NOP padding.
2. Or split into separate safe replacement entries where no cross-entry branch target lands inside another replaced span.

No implementation was performed in this run.
