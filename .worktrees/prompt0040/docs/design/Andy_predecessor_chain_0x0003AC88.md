# Andy — Immediate Predecessor Chain to runtime_genesis_pc 0x0003AC88 (Build 0077)

**Author:** Andy
**Date:** 2026-06-11
**Build:** 0077 (canonical baseline SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** STATIC backward trace only. Documentation-only. No source / spec / tool / Makefile / ROM modifications. No bookmark cycle. No runtime probing.

---

## Phase 0 — Baseline statement

**Classification:** EXTENDING KF-003.

**Relevant priors:** KF-001 (watchdog routine 0x3A180; counter `%a5@(44)`=`0xFF002C`; HIGH hazard), KF-003 (kick-site inventory; reset-to-main-loop equivalence settled; HIGH hazard), KF-004 (runtime PC = ROM file offset; CONFIRMED), KF-006 (identity_offset = 0x200; CONFIRMED), KF-011 (arcade Level-5 VBlank owns progression; HIGH hazard), KF-019 (MAME parked-helper sampling gap; context).

**HIGH-hazard findings touched:** KF-001, KF-003, KF-004, KF-011. None contradicted.

**Open issues touched:** OPEN-001, OPEN-004 (context only; not closed).

**Phase 0 STOP:** not triggered. No CONFIRMED/STRONG contradiction detected.

This task backward-traces from the title-state ENTRY kick at Genesis runtime `0x0003AC88` (arcade source `0x0003AA88` per KF-006) until the first stopping condition, per §0.2.

---

## Phase 1 — Backward trace (arcade source `build/maincpu.disasm.txt`)

All Genesis addresses below = arcade source + `0x200`. Citations are arcade-source line numbers unless noted.

### Step 1 — In-routine predecessors of the kick — STATICALLY_PROVEN

```
3aa7e:  426d 0004      clrw   %a5@(4)            ; clear inner sub-state
3aa82:  3b7c 0001 0002 movew  #1, %a5@(2)        ; advance title sub-state → 1
3aa88:  3b7c 00d0 002c movew  #208, %a5@(44)     ; THE KICK (counter ← 208)
3aa8e:  4e75           rts
```
Source: `maincpu.disasm.txt:73692-73695`. The kick is the tail of a handler that advances the title sub-state. Its routine begins at `0x3aa54`.

### Step 2 — Routine entry `0x3aa54` — STATICALLY_PROVEN

```
3aa54:  4eb9 0005 a356 jsr 0x5a356        ; routine entry
3aa5a:  701e           moveq #30, %d0
3aa5c:  0c79 0001 0005fffe cmpiw #1, 0x5fffe
... (text-producer dispatch block, KF-013) ...
3aa7e:  (falls through to the kick)
```
Source: `maincpu.disasm.txt:73679-73695`. `0x3aa54` is the entry; it falls straight through to the kick. No branch leaves the routine before `0x3aa88`. (Genesis: `0x3ac54`, `genesis_postpatch.disasm.txt:73523`.)

### Step 3 — Reaching `0x3aa54` via inner sub-dispatch — STATICALLY_PROVEN (structure) / EXPECTED_BUT_RUNTIME_DEPENDENT (selector `%a5@(4)`)

`0x3aa54` is an indirect `jmp` target. Grep confirms no symbolic caller (`genesis_postpatch.disasm.txt`: `3ac54` appears only as its own definition). It is reached through a two-level computed dispatch. Inner dispatch:

```
3aa26:  302d 0004      movew %a5@(4), %d0     ; read inner sub-state
3aa2a:  d040           addw  %d0, %d0
3aa2c:  41fa 000e      lea %pc@(0x3aa3c), %a0 ; inner table base
3aa30:  d0c0           addaw %d0, %a0
3aa32:  3010           movew %a0@, %d0
3aa34:  41fa 0006      lea %pc@(0x3aa3c), %a0
3aa38:  d0c0           addaw %d0, %a0
3aa3a:  4ed0           jmp %a0@
3aa3c:  [0004][0018]   <- inner jump table (raw words)
```
Inner table at `0x3aa3c`: word[0]=`0x0004` → `0x3aa3c+4`=`0x3aa40`; word[1]=`0x0018` → `0x3aa3c+0x18`=`0x3aa54`. So **inner sub-state `%a5@(4)==1` selects the kick handler `0x3aa54`**; `%a5@(4)==0` selects `0x3aa40`, which sets up and advances `%a5@(4)→1` without kicking:
```
3aa40:  bsrw 0x3add8 / bsrw 0x3ad4c / bsrw 0x3ae5a
3aa4c:  3b7c 0001 0004 movew #1, %a5@(4)   ; inner sub-state → 1
3aa52:  4e75           rts
```
Source: `maincpu.disasm.txt:73664-73679`. `%a5@(4)` is a WRAM value → EXPECTED_BUT_RUNTIME_DEPENDENT (expected sequence: `%a5@(4)` 0→1 across two dispatch passes).

### Step 4 — Reaching the inner dispatch via outer sub-dispatch — STATICALLY_PROVEN (structure) / EXPECTED_BUT_RUNTIME_DEPENDENT (selector `%a5@(2)`)

The inner dispatch entry `0x3aa26` is itself the outer-table target for outer sub-state `%a5@(2)==0`. Outer dispatch is the title dispatcher at `0x3a9fe`:

```
3a9fe:  4a6d 002c      tstw  %a5@(44)       ; test shared counter
3aa02:  6706           beqs  0x3aa0a         ; if zero → dispatch
3aa04:  536d 002c      subqw #1, %a5@(44)    ; else decrement and...
3aa08:  4e75           rts                   ; ...return (no dispatch this frame)
3aa0a:  302d 0002      movew %a5@(2), %d0    ; read outer sub-state
3aa0e:  d040           addw  %d0, %d0
3aa10:  41fa 000e      lea %pc@(0x3aa20), %a0
...
3aa1e:  4ed0           jmp %a0@
3aa20:  [0006][0070][0138][302d]...  <- outer jump table
```
Outer table at `0x3aa20`: word[0]=`0x0006` → `0x3aa20+6`=`0x3aa26` (the inner dispatch). So **outer sub-state `%a5@(2)==0` routes to the inner dispatch.** Source: `maincpu.disasm.txt:73652-73667`.

**Key observation (new):** the title dispatcher at `0x3a9fe` gates dispatch on `%a5@(44)` — the *same* WRAM counter the watchdog routine (KF-001, `0x3a180`) tests. The dispatcher decrements `%a5@(44)` each frame and only advances the sub-state machine when it reaches 0. `%a5@(44)` is therefore dual-use: a frame-delay timer for the title state machine **and** the watchdog expiry counter. STATICALLY_PROVEN (both readers cite `%a5@(44)`).

### Step 5 — Reaching the title dispatcher via master dispatch — STATICALLY_PROVEN (structure) / EXPECTED_BUT_RUNTIME_DEPENDENT (selector `%a5@(0)`)

`0x3a9fe` is an indirect `jmp` target reached from the master dispatch inside the VBlank handler:

```
3a052:  487a 0020      pea %pc@(0x3a074)     ; push handler-return addr
3a056:  302d 0000      movew %a5@(0), %d0    ; read MASTER state
3a05a:  d040           addw  %d0, %d0
3a05c:  41fa 000e      lea %pc@(0x3a06c), %a0
...
3a06a:  4ed0           jmp %a0@
3a06c:  [0992][0840][00ee][0b02]  <- master jump table
```
Master table at `0x3a06c`: word[0]=`0x0992` → `0x3a06c+0x992`=`0x3a9fe` (title dispatcher). So **master state `%a5@(0)==0` routes to the title dispatcher.** Source: `maincpu.disasm.txt:72966-72975`.

### Step 6 — Reaching the master dispatch: VBlank handler entry `0x3a008` — STATICALLY_PROVEN

The master dispatch is the tail of the VBlank handler that begins at arcade `0x3a008` (Genesis `0x3a208`):
```
3a008:  007c 0f00      oriw #3840, %sr       ; raise IPM (handler prologue)
3a00c:  4279 0035 0008 clrw 0x350008         ; arcade hardware write
3a012:  33c0 003c 0000 movew %d0, 0x3c0000   ; arcade hardware write
3a018:  302d 0002      movew %a5@(2), %d0
... (handler body: bsrw 0x3a126/0x41f30/0x3ab7c/0x3abe2/0x3a0a8/0x3eefa/0x3ef5c) ...
3a052:  pea 0x3a074 ; 3a056: master dispatch
```
Source: `maincpu.disasm.txt:72947-72966`. The VBlank handler entry `0x3a008` is the predecessor of the master dispatch.

### Step 7 — Stopping condition: tie-in to the Genesis Level-6 VBlank vector

On the Genesis side, `0x3a208` (the VBlank handler entry) is referenced by exactly one instruction (grep: `jmp 0x3a208` at `genesis_postpatch.disasm.txt:122740`):
```
700c2:  48e7 fffe      moveml %d0-%fp, %sp@-   ; Genesis Level-6 service prologue
... (hardware-servicing helpers: 0x7007e, 0x70106, 0x70130, 0x7017e, 0x719b0,
     0x701cc, 0x701ec — staged-commit / plane DMA / sprite-scroll commit) ...
700fc:  4cdf 7fff      moveml %sp@+, %d0-%fp
70100:  4ef9 0003 a208 jmp 0x3a208            ; hand off to arcade VBlank handler
```
`0x700c2` is the target of the Genesis Level-6 autovector (vector table offset `0x78` = `0x000700c2`, `genesis_postpatch.disasm.txt` `.data` offset 0x78). This is **validated territory**: KF-011 establishes Genesis VBlank as servicing-only handing to arcade; BM-004 runtime evidence shows execution repeatedly inside the `0x700c2` helper tree (observed PCs `0x70106`-region, `0x7015c`, `0x70162`, `0x7017c`, `0x705f6`, `0x70628`, `0x70636`, `0x700a0`, `0x719b0`-region `0x719d4`/`0x719e0`, `0x71cdc`/`0x71ce2`).

The backward trace stops here: the chain ties into validated VBlank territory, **but only through the runtime state-selector gates identified in Steps 3-5**. This is NOT a full static connection (the special-case STOP requires *no* runtime gate; gates exist), so the trace does not trigger the contradiction-elevation case.

**Chain (9 nodes, kick → tie-in):**
`0x3ac88` ← `0x3ac54` ← [inner jmp `0x3ac3a`, `%a5@(4)==1`] ← [outer jmp `0x3ac1e`, `%a5@(2)==0`] ← `0x3abfe` [`%a5@(44)==0`] ← [master jmp `0x3a26a`, `%a5@(0)==0`] ← `0x3a256` ← `0x3a208` ← [`jmp` `0x70100`] ← `0x700c2` (Level-6 vector).

---

## Phase 2 — Genesis comparison (`build/genesis_postpatch.disasm.txt`)

| Chain node (arcade) | Genesis | Translated-flow equiv? | Notes |
|---|---|---|---|
| kick `0x3aa88` | `0x3ac88` (`3b7c 00d0 002c`) | YES | identical encoding; `%a5@(44)`→`0xFF002C` via A5 rebase |
| handler entry `0x3aa54` | `0x3ac54` | YES | byte-identical structure (jsr target relocated +0x200) |
| inner table `0x3aa3c` | `0x3ac3c` (`0004`,`0018`) | YES | identical offsets |
| outer dispatcher `0x3a9fe` | `0x3abfe` | YES | byte-identical (`tstw %a5@(44)`/`beqs`/`subqw`/jump table) |
| master table `0x3a06c` | `0x3a26c` (`0992`,`0840`,`00ee`,`0b02`) | YES | identical offsets |
| master dispatch `0x3a056` | `0x3a256` | YES | byte-identical |
| **VBlank entry `0x3a008`-`0x3a018`** | **`0x3a208`-`0x3a218`** | **YES (with substitution)** | arcade `clrw 0x350008` + `movew %d0,0x3c0000` (12 bytes, two arcade hardware-register writes) → **6× `4e71` NOP** on Genesis (12 bytes). See below. |

**The only byte-level difference on the entire chain is the VBlank-entry hardware-write substitution.** Arcade `0x3a00c` writes arcade hardware at `0x350008`, and `0x3a012` strobes `0x3c0000` (per KF-025, the watchdog/control comparison target — the same address the main loop strobes at `0x3b07e`/`0x3b27e`). Both are arcade hardware that does not exist on Genesis; the translation replaces them with length-preserving NOPs. **Neither write feeds any branch on the path to the kick** — the dispatch decisions read only `%a5@(0)/%a5@(2)/%a5@(4)/%a5@(44)`, none of which is touched by these two writes. Per the translated-flow-equivalence test, this is a hardware-elision shim, **not a divergence** capable of altering reachability of `0x0003AC88`.

(These NOPs are the translator's hardware-write elision in the post-patch artifact; they are not patch scaffolding and are disclosed here as an observation only.)

**Phase 2 result:** the predecessor chain is translated-flow equivalent at every node. No divergence.

---

## Phase 3 — Outcome classification + timing evaluation

### Outcome: **B — Runtime dependency found.**

The chain from the kick back to the Level-6 VBlank vector is statically equivalent between arcade and Build 0077 (only the reachability-neutral hardware-write NOP substitution differs). Progression to `0x0003AC88` is gated entirely by runtime WRAM values:

- `%a5@(0)` (master state) must be `0` → routes to title dispatcher.
- `%a5@(2)` (outer sub-state) must be `0` → routes to inner dispatch.
- `%a5@(4)` (inner sub-state) must reach `1` → selects the kick handler (requires `0x3ac40` to run once first).
- `%a5@(44)` (shared counter) must reach `0` while the above hold → the title dispatcher only advances when it decrements to zero. This counter is dual-use with the KF-001 watchdog.

A secondary runtime dependency: the VBlank handler body (`0x3a218`-`0x3a252`) must complete to reach the master dispatch at `0x3a256` (it makes several `bsrw` calls first). BM-004 sampling shows the `0x700c2` helper tree running but never directly samples `0x3a208`+ (consistent with the brief, fast arcade handler being missed by 30 FPS sampling, per KF-019 — not evidence of non-execution).

### Timing evaluation (§0.3)

- **Estimated chain duration (VBlank entry `0x3a208` → kick `0x3ac88`, single pass):** the VBlank handler body is a fixed sequence of `bsrw` calls plus the two-level dispatch — on the order of low-thousands of M68000 cycles per frame, even generously counting the sub-routines. The kick handler `0x3ac54`-`0x3ac88` itself is a short text-dispatch block (tens of `bsrw`/`moveq` pairs).
- **Watchdog window:** ~3.6 s ≈ 21.6 M cycles at 6 MHz.
- **Timing starvation plausible: NO.** The predecessor chain executes in a tiny fraction of the watchdog window; the chain is not too *long* to complete. Reachability is gated by state-selector **values** and the `%a5@(44)` countdown race, not by chain execution duration.

(Note — out of scope but flagged: because `%a5@(44)` is decremented both by the title dispatcher at `0x3abfe` and by the watchdog at `0x3a180`, whether the title dispatcher reaches its zero-counter dispatch before the watchdog reaches its zero-counter expiry is a counter-race question. Resolving it requires tracing the watchdog routine, which KF-001 owns. Not pursued here.)

---

## Phase 4 — KNOWN_FINDINGS impact

### Option C — Proposed update to KF-003.

Justification: the evidence substantively sharpens KF-003's model. KF-003 currently states reachability "is determined at runtime by VBlank dispatch and state-machine progression" without recording the actual dispatch structure. This task establishes the concrete 9-node chain, the three state selectors (`%a5@(0)/%a5@(2)/%a5@(4)`), and a previously unrecorded durable fact: **`%a5@(44)` is dual-use** — both the watchdog expiry counter (KF-001) and the title dispatcher's per-frame delay timer at `0x3abfe`. That dual-use is non-obvious system behavior worth canonicalizing.

**Proposed additive text** (append to KF-003 Use-as-prior; existing wording preserved):

> The concrete predecessor chain to the first kick `0x0003AC88` (Andy, `docs/design/Andy_predecessor_chain_0x0003AC88.md`) is: Genesis Level-6 VBlank vector → `0x700c2` (servicing helpers) → `jmp 0x3a208` (arcade VBlank handler) → master dispatch on `%a5@(0)` at `0x3a256` (state 0 → `0x3abfe`) → title dispatcher gated on `%a5@(44)==0`, sub-dispatch on `%a5@(2)` (0) and `%a5@(4)` (1) → handler `0x3ac54` → kick `0x3ac88`. The chain is translated-flow equivalent arcade↔Genesis; the only byte difference is reachability-neutral NOP elision of arcade hardware writes (`0x350008`, `0x3c0000`) at the VBlank entry. The counter `%a5@(44)` is dual-use: the title dispatcher at `0x3abfe` decrements it each frame and dispatches only at zero, the same cell the KF-001 watchdog tests for expiry.

Confidence axis: STRONG (unchanged). Status/Applicability/Rediscovery Hazard: unchanged. Last verified: bump to 2026-06-11 (Build 0077). Cody applies after Tighe acknowledges; Andy does not edit KNOWN_FINDINGS.md directly.

---

## Phase 5 — Recommended next task

**BM-005 bookmark on Genesis runtime PC `0x0003A256`** (the master-dispatch `movew %a5@(0),%d0`, immediately before the computed `jmp`).

Rationale — this is the cheapest decisive bisection of the runtime gates:
- **If `0x3a256` is reached** → the Genesis VBlank service hands off to the arcade VBlank handler and the handler body runs to completion every frame; the dispatch executes. The open question then narrows to the state-selector values (`%a5@(0)/%a5@(2)/%a5@(4)`) and the `%a5@(44)` counter race — a downstream BM-006 on `0x0003ABFE` (title dispatcher entry) would isolate whether master state routes to title.
- **If `0x3a256` is NOT reached** → the VBlank handler body is hanging or faulting in one of its pre-dispatch `bsrw` calls (`0x3a326/0x42130/0x3ad7c/0x3ade2/0x3a2a8/0x3f0fa/0x3f15c`), or the Level-6 handoff `jmp 0x3a208` is not executing. The next backward target becomes those sub-calls.

`0x3a256` sits one node upstream of all four state-selector gates, so it cleanly separates "VBlank dispatch machinery runs" from "state values select the kick path" — exactly the bisection BM-004's clean Outcome B leaves open. (Secondary follow-up target, if `0x3a256` hits: `0x0003ABFE`.)

This is an evidence-capture handoff (BM-005), not an implementation task. No Outcome-A divergence exists, so no Cody implementation is proposed.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001, OPEN-004 (context; chain sharpens localization of the progression-failure boundary; no status change).
- **Closed issues touched:** None.
- **New issues opened:** None.
- **Issues closed:** None.
- **Issues intentionally deferred:** None.

## STOP triggered

NO.
