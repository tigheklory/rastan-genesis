# Cody - Build 0120 D00298 Post-2/2/5 Path Analysis

**Date:** 2026-06-30
**Type:** Evidence / static + manual-runtime reconciliation only
**Build:** 0120
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark cycle. No diagnostics inserted. No BlastEm automation.

## Phase 0

Read and applied `RULES.md`, `ARCHITECTURE.md`, current `AGENTS_LOG.md`, and the previous Build 0120 evidence note `docs/design/Cody_build0120_D00298_runaway_fill_writer_evidence.md`.

Classification: **EXTENDING** OPEN-022 / Build 0120 post-item-strip evidence. OPEN-001 context. OPEN-015 context for crash-record reliability. This report accepts Tighe's manual BlastEm stepping evidence as the runtime observation source and performs static/address-map reconciliation only.

## Accepted Manual Evidence

The manual BlastEm observations establish the following path and state:

- Build 0120 item-page strip hook is live and returns cleanly.
- Item strip loop exits normally at `runtime_genesis_pc 0x00050682`.
- Return chain proceeds through `0x5040A`, `0x5040E`, `0x50442`, `0x50446 rts`, `0x4551C`, `0x4553C bsr 0x4670E`, `0x45540 rts`, then `0x3A85C move.w #5,%a5@(4)`.
- After `runtime_genesis_pc 0x0003A85C`, state is `Genesis-WRAM 0x00FF0000/0002/0004 = 0x0002/0x0002/0x0005`.
- Therefore the immediate post-item-strip state is `2/2/5`, not `2/3/0`.
- `runtime_genesis_pc 0x00055EA2` returns cleanly through the `FF0074 == 0` path and is not currently the observed D00298 writer.
- Main-loop cadence reaches `runtime_genesis_pc 0x0003B292: bsr 0x3A1A8`.
- On the manually inspected pass, `Genesis-WRAM 0x00FF0018 = 0x0001` and step-ins through `0x3A1A8 -> 0x3A1AC` are safe.
- Fatal D00298 behavior is observed when stepping over the `0x3B292` call, so the dangerous path starts at `0x3A1A8` or from control flow reached when the safe branch is not taken.

## Address Mapping

All mappings below are from `build/rastan-direct/address_map.json`.

| runtime_genesis_pc | map kind | arcade_pc |
|---|---|---|
| `0x0003A274` | `arcade_copy` | `0x0003A074` |
| `0x00055EA2` | `arcade_copy` | `0x00055CA2` |
| `0x00055FD6` | `arcade_copy` | `0x00055DD6` |
| `0x0003A27E` | `arcade_copy` | `0x0003A07E` |
| `0x0003B27E` | `arcade_copy` | `0x0003B07E` |
| `0x0003B28C` | `arcade_copy` | `0x0003B08C` |
| `0x0003B292` | `arcade_copy` | `0x0003B092` |
| `0x0003A1A8` | `arcade_copy` | `0x00039FA8` |
| `0x0003A1AA` | `arcade_copy` | `0x00039FAA` |
| `0x0003A1AC` | `arcade_copy` | `0x00039FAC` |

Additional D00298 candidate mapping:

| runtime_genesis_pc | map kind | arcade_pc | role |
|---|---|---|---|
| `0x0005124E` | `arcade_copy` | `0x0005104E` | only direct caller found for `0x5A702` |
| `0x0005A702` | `arcade_copy` | `0x0005A502` | D00298 sprite writer routine entry |
| `0x0005A71E` | `arcade_copy` | `0x0005A51E` | loads `A0 = HW_ADDRESS 0x00D00298` |
| `0x0005A724` | `arcade_copy` | `0x0005A524` | first write through that A0 |

## Local Control Flow

### VBlank tail `0x3A274..0x3A27E`

```asm
3a274:  jsr 0x55ea2
3a27a:  andiw #0xf0ff,%sr
3a27e:  rte
```

The manual observation that `0x55EA2` returns cleanly places execution back at `0x3A27A`, then `0x3A27E rte`, then the interrupted main-loop address.

### `0x55EA2..0x55FDA`

Relevant manual path:

```asm
55ea2:  cmpiw #0,%a5@(74)      ; Genesis-WRAM 0x00FF0074
55ea8:  beqw 0x55fd6
...
55fd6:  clrw %a5@(5068)
55fda:  rts
```

With `Genesis-WRAM 0x00FF0074 = 0`, the branch at `0x55EA8` is taken, `Genesis-WRAM 0x00FF13CC` is cleared, and the routine returns. This path contains no `HW_ADDRESS 0x00D00298` literal and no PC090OJ write.

Classification: `0x55EA2` is a clean sound/mailbox-ish service path in this observation, **not** the D00298 writer.

### Main loop `0x3B27E..0x3B296`

```asm
3b27e:  movew %d0,0x003c0000
3b284:  tstw %a5@(7184)        ; Genesis-WRAM 0x00FF1C10
3b288:  bras 0x3b28c
3b28c:  cmpiw #0x0100,%a5@(18); Genesis-WRAM 0x00FF0018
3b292:  bsrw 0x3a1a8
3b296:  bras 0x3b27e
```

Manual stepping proved `0x3B27E`, `0x3B284`, and `0x3B288` execute safely on the tested pass. The condition used by `0x3A1A8` is set by `0x3B28C`, immediately before the `bsr`.

### Watchdog wrapper / non-BCS path `0x3A180..0x3A1AC`

```asm
3a180:  tstw %a5@(44)
3a184:  beqs 0x3a18c
3a186:  subqw #1,%a5@(44)
3a18a:  rts
3a18c:  movel #0x000a0000,%d1
3a192:  movel 0x0,%d0
3a196:  subil #1,%d1
3a19c:  bnes 0x3a192
3a19e:  moveal 0x0,%sp
3a1a2:  moveal 0x4,%a0
3a1a6:  jmp %a0@
3a1a8:  bcss 0x3a1ac
3a1aa:  bras 0x3a18c
3a1ac:  rts
```

`runtime_genesis_pc 0x0003A1A8` does not compute anything itself. It consumes the carry flag left by the caller. If carry is set, it returns immediately. If carry is clear, it branches to `0x3A18C`, delays, reloads SP from vector `0x00000000`, reloads PC from vector `0x00000004`, and jumps to the reset vector.

Build 0120 vector values from the ROM:

- initial SP vector: `0x00FF0000`
- reset PC vector: `0x00000202`

So the non-BCS path is a bootstrap/re-entry path, not a local D00298 writer.

## 0x3A1A8 Condition Source

The carry flag used at `0x3A1A8` is set by the immediately preceding caller instruction:

```asm
3b28c: cmpiw #0x0100,%a5@(18)
3b292: bsrw 0x3a1a8
```

68000 `cmpi.w #imm,<ea>` computes `<ea> - imm` for condition codes. Carry is set when an unsigned borrow occurs, i.e. when `<ea> < imm`.

Therefore:

- If `Genesis-WRAM 0x00FF0018 < 0x0100`, carry is set, `BCS` at `0x3A1A8` is taken, and the routine returns at `0x3A1AC`.
- If `Genesis-WRAM 0x00FF0018 >= 0x0100`, carry is clear, `BCS` is not taken, and `0x3A1AA` branches to the watchdog/bootstrap re-entry path at `0x3A18C`.

Manual safe pass:

- `Genesis-WRAM 0x00FF0018 = 0x0001`
- `0x0001 < 0x0100`, so carry is set and `0x3A1A8 -> 0x3A1AC rts` is expected.

Unsafe condition:

- `Genesis-WRAM 0x00FF0018 >= 0x0100`, or any stale/altered CCR state entering `0x3A1A8` without the `0x3B28C` compare, would make the wrapper fall through to `0x3A18C`.

## D00298 Candidate Writer

Static scan found the direct D00298 candidate in a copied arcade routine:

```asm
5a702:  clrl %d0
5a704:  movew 0x10c200,%d0
5a70a:  btst #5,%d0
5a70e:  beqs 0x5a716
5a710:  movew #0x0180,%d1
5a714:  bras 0x5a71a
5a716:  movew #0x0070,%d1
5a71a:  movew #0x0060,%d0
5a71e:  moveal #0x00d00298,%a0
5a724:  movew #0,%a0@+
5a728:  movew %d1,%a0@+
5a72a:  movew #0x0037,%a0@+
5a72e:  movew %d0,%a0@+
```

`runtime_genesis_pc 0x0005A71E` loads `A0` with `HW_ADDRESS 0x00D00298`. The first dangerous write is `runtime_genesis_pc 0x0005A724`, which writes through `A0@+` to `HW_ADDRESS 0x00D00298`.

Only direct caller found:

```asm
51246:  cmpiw #0,%a5@(52)
5124c:  bnes 0x51254
5124e:  jsr 0x5a702
51254:  jsr 0x5a298
```

So the static candidate path is:

`runtime_genesis_pc 0x0005124E -> 0x0005A702 -> 0x0005A71E -> 0x0005A724`

Mapped:

`arcade_pc 0x0005104E -> 0x0005A502 -> 0x0005A51E -> 0x0005A524`

## D00298 Address Classification

`HW_ADDRESS 0x00D00298` is most likely a raw PC090OJ/sprite-RAM hardware destination used by copied arcade code.

It is **not** most likely computed from the manual pre-call `A6=0x00FF0298`; that would require separately adding `0x00D00000`, and no such operation is present in the inspected `0x3B292 -> 0x3A1A8` wrapper.

It is **not** most likely computed from `D0=0x00010000` or `D7=0x00020000`; the static D00298 writer uses an immediate long literal loaded into `A0`.

It is **not** a direct write literal instruction like `move.w ...,0x00D00298`; instead the literal is loaded into `A0`, then subsequent `A0@+` writes hit the target.

It may be reached through corrupted or unintended control flow if `0x3A1A8` falls through into the bootstrap/re-entry path. In that case, the D00298 write itself is a normal copied-arcade sprite write, but its execution at this point in the translated runtime is likely downstream of the watchdog/re-entry path rather than part of the safe `2/2/5` item-page loop.

## Relationship To State 2/2/5

The manual evidence corrects the immediate post-item-strip state to `2/2/5`. That matters: the Build 0120 hook returns cleanly, `0x3A85C` writes `%a5@(4)=5`, and `0x55EA2` is not the D00298 writer.

The D00298 failure is therefore downstream of the post-strip `2/2/5` state, in the main-loop/watchdog wrapper path, not in the strip hook itself.

The safe observed calls at `0x3B292` are explained by `Genesis-WRAM 0x00FF0018=0x0001`, which makes `0x3A1A8` return. The dangerous condition is when `0x00FF0018` reaches or exceeds `0x0100`, causing the non-returning `0x3A18C` bootstrap/re-entry path.

## Relationship To Prior MAME 2/3/0 Evidence

The prior MAME evidence reached crash-common with state `2/3/0/0` and showed crash-record/high-WRAM pattern corruption, but it did not reproduce the `HW_ADDRESS 0x00D00298` watchpoint.

This report does not treat MAME and BlastEm as identical paths. The manual BlastEm evidence is narrower and stronger for the immediate post-strip sequence: `2/2/5` after `0x3A85C`, safe `0x55EA2`, then main-loop calls to `0x3A1A8`.

Reconciliation:

- Manual BlastEm: proves immediate post-strip state is `2/2/5` and points to the `0x3B292 -> 0x3A1A8` branch condition as the next boundary.
- Prior MAME: proves a later scripted path can reach crash-common with corrupted crash record and state `2/3/0`, but did not catch D00298.
- Neither source proves that formatted exception-screen PC/address/vector fields are trustworthy; they remain non-authoritative unless independently captured from debugger-side evidence or a non-corrupted WRAM crash record.

## Most Likely D00298 Writer Path

**Most likely path, not fully runtime-proven in this report:**

1. `runtime_genesis_pc 0x0003B28C` compares `Genesis-WRAM 0x00FF0018` against `0x0100`.
2. `runtime_genesis_pc 0x0003B292` calls `0x3A1A8`.
3. If carry is clear (`FF0018 >= 0x0100`), `0x3A1A8` does not return; `0x3A1AA` branches to `0x3A18C`.
4. `0x3A18C..0x3A1A6` delays, reloads SP/PC from vectors, and jumps to reset PC `0x00000202`.
5. Downstream copied arcade execution reaches `runtime_genesis_pc 0x0005124E`, the only direct caller found for `0x5A702`.
6. `0x5A702` reaches `0x5A71E`, loads `A0=HW_ADDRESS 0x00D00298`, and `0x5A724` performs the first write to that target.

What is proven:

- `0x3A1A8` is controlled by the carry from `0x3B28C`.
- `FF0018=0x0001` makes the observed branch safe.
- `0x5A71E/0x5A724` is the static literal writer path for `HW_ADDRESS 0x00D00298`.
- `0x5124E` is the only direct caller found for `0x5A702`.

What is not proven:

- This report does not contain a debugger-side capture of `runtime_genesis_pc 0x0005A71E` or `0x0005A724` during the BlastEm fatal.
- This report does not prove the exact dynamic route from reset vector `0x00000202` to `0x5124E` in the failing pass.

## Next Single BlastEm Stop Target

Recommended next manual stop target:

`runtime_genesis_pc 0x0005A71E`

Reason: this is before the first dangerous write. It loads `A0 = HW_ADDRESS 0x00D00298`; the actual first write occurs at `runtime_genesis_pc 0x0005A724`. Stopping at `0x5A71E` lets Tighe confirm whether the fatal path has reached the known D00298 writer before executing the write.

At that stop, capture:

- PC and SR
- `A0`, `A5`, `SP`
- `%a5@(0)/(2)/(4)/(18)/(44)/(52)` = `Genesis-WRAM 0x00FF0000/0002/0004/0018/002C/0034`
- a short call/return context if BlastEm exposes it

Do not step past `runtime_genesis_pc 0x0005A724` unless intentionally testing the fatal write.

## STOP Status

**STOP: NO for this evidence task.**

The requested static/manual reconciliation is complete. No implementation is authorized from this report alone because the dynamic handoff from `0x3A18C` re-entry to `0x5124E/0x5A702` has not yet been captured in BlastEm.

## Non-Actions

No source, spec, tool, Makefile, ROM, build, invariant, bookmark, or issue-status changes were made. No `KNOWN_FINDINGS.md` update was made.

## Open / Closed Issues Impact

- OPEN-022 / KF-032: context; Build 0120 strip route remains exonerated for the immediate post-strip state.
- OPEN-001: context only.
- OPEN-015: context only; exception-screen fields remain non-authoritative.
- Issues opened: NONE.
- Issues closed: NONE.
- KNOWN_FINDINGS impact: Option A - no update from this evidence-only path analysis.
