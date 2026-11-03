# Cody - Build 0158 Intro Drop / Landing Runtime Proof

**Date:** 2026-07-10  
**Type:** Analysis-only runtime proof  
**Baseline branch:** `rastan-direct-proposal`  
**Baseline HEAD:** `e4297f4`  
**Accepted build:** Build 0157  
**Genesis ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0157.bin`  
**Genesis ROM SHA256:** `725c36a27a4ea55a4a99bcbca4bd5dde3bbaf00cffe6b5005b8997b90cdd2c4a`  
**Counter context:** `157`

## Scope

Analysis only. No source, spec, tool, Makefile, ROM, invariant, bookmark, or issue-ledger changes were made. No fix was implemented. The trace is limited to the Stage 1 intro drop -> landing -> early stable-control boundary.

Out of scope by directive: continue/game-over, D00298, Exodus, audio, tilemaps, sprite rendering, and general scroll cleanup.

## Phase 0

Relevant KNOWN_FINDINGS priors:

- KF-010: Genesis visible layers use staging buffers and VBlank commits.
- KF-011: arcade VBlank/game logic remains the frame producer; Genesis service performs hardware commit work.
- KF-032: raw PC080SN/PC090OJ writes must route through Genesis staging rather than touching VDP aliases directly.
- KF-039: arcade work-RAM absolute/A5-base addresses must map from arcade `0x0010C000` to Genesis WRAM `0x00FF0000` by offset.
- KF-040 / KF-041: Stage 1 PC080SN/source-model context; referenced as adjacent gameplay-rendering state, not rederived.

Rediscovery Hazard HIGH findings touched: KF-011, KF-032, KF-039, KF-040, KF-041. No contradiction detected.

Deferred appendix entries relevant: none found for this bounded intro-drop task.

Task classification: **EXTENDING**. This extends OPEN-001 / OPEN-017 gameplay bring-up evidence after Build 0157.

Open issues touched: OPEN-001, OPEN-017, OPEN-024 as context. OPEN-018 context only.  
Closed issues touched: none.  
Contradiction of CONFIRMED or STRONG finding: **NONE**.

Architecture compliance: **CONFIRMED**. The arcade code remains the program; Genesis-side behavior is treated as helper/translation/staging. No scaffolding or second renderer path was introduced.

## Files / Evidence Inspected

Required inputs:

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- `docs/design/Cody_player_death_fall_analysis.md`
- `docs/design/Cody_build0158_player_floor_trace_targets.md`
- `build/rastan-direct/address_map.json`
- `apps/rastan-direct/out/symbol.txt`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`

Runtime evidence produced:

- Trace directory: `states/traces/build_0158_intro_drop_landing_runtime_proof_20260710_232927/`
- Arcade timeline: `arcade_intro_timeline.log`
- Genesis timeline: `genesis_intro_timeline.log`
- Arcade native debugger trace: `arcade_native_debug_trace.log`
- Genesis native debugger trace: `genesis_native_debug_trace.log`
- Debug command files: `arcade_intro_debug.cmd`, `genesis_intro_debug.cmd`

Both MAME runs completed with exit code `0`. The first headless pass produced Lua timelines but not native debugger logs; a bounded debugger-enabled rerun produced the native traces.

## Address Mapping Discipline

All compared code PCs below are exact `arcade_copy` hits in `build/rastan-direct/address_map.json`, not arithmetic proofs.

| arcade_pc | runtime_genesis_pc | Segment/source | Classification | Confidence |
|---:|---:|---|---|---|
| `0x05052E` | `0x05072E` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x050534` | `0x050734` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x051034` | `0x051234` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x051038` | `0x051238` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x0512C8` | `0x0514C8` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x0517FA` | `0x0519FA` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x053850` | `0x053A50` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x0538EA` | `0x053AEA` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x053956` | `0x053B56` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x0539C2` | `0x053BC2` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x053A2E` | `0x053C2E` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |
| `0x053A6E` | `0x053C6E` | `arcade_copy`, `whole_maincpu_copy` | copied arcade code, shifted | high |

A5/work-RAM fields use KF-039 offset-preserving mapping:

| Field | arcade work-RAM address | Genesis-WRAM address | Classification |
|---|---:|---:|---|
| player X, `a5+0x10BE` | `0x0010D0BE` | `0x00FF10BE` | A5-relative work RAM |
| player Y, `a5+0x10C0` | `0x0010D0C0` | `0x00FF10C0` | A5-relative work RAM |
| entry command, `a5+0x137A` | `0x0010D37A` | `0x00FF137A` | A5-relative work RAM |

## Q1 - Stage 1 Intro Drop Alignment

### Event Timeline

| Logical event | Arcade frame/delta | Arcade state / values | Genesis frame/delta | Genesis state / values |
|---|---:|---|---:|---|
| Setup sample | frame `250` | state `2/2/7`, player `0000/0000`, cmd `0000`, death `00FF/0001` | frame `250` | state `2/2/7`, player `0000/0000`, cmd `0000`, death `00FF/0001` |
| First active gameplay | frame `307`, delta `0` | state `2/3/0`, player `0020/0030`, cmd `0000`, move `0000`, da `0000`, e8 `0003`, camera `0000/0000` | frame `533`, delta `0` | state `2/3/0`, player `0020/0030`, cmd `0000`, move `0000`, da `0000`, e8 `0003`, camera `0000/0000` |
| Command first diverges | frame `308`, delta `1` | cmd becomes `00FF`; Y still `0030` | frame `536`, delta `3` | cmd becomes `5553`; Y becomes `0034` |
| First post-active Y movement | frame `311`, delta `4` | Y `0031` | frame `536`, delta `3` | Y `0034` |
| active+10 | frame `317`, delta `10` | Y `0037`, cmd `00FF` | frame `543`, delta `10` | Y `003C`, cmd `5553` |
| active+30 | frame `337`, delta `30` | Y `006E`, cmd `00FF` | frame `563`, delta `30` | Y `005C`, cmd `5553` |
| First landing Y `0x0070` | frame `338`, delta `31` | Y `0070`, move `0002`, da `0001`, camera `0000/01FF` | frame `576`, delta `43` | Y `0070`, move `0002`, da `0000`, camera `0000/0000` |
| Stable landing sample | frame `342`, delta `35` | Y `0070`, move `0002`, da `0003`, camera `0000/01F3` | frame `580`, delta `47` | Y `0070`, move `0002`, da `0004`, camera `0000/01FC` |
| active+60 | frame `367`, delta `60` | Y `0070`, move `0002`, da `0003`, camera `0000/01A8` | frame `593`, delta `60` | Y `0070`, move `0002`, da `0004`, camera `0000/01E8` |
| Active-state exit | frame `895`, delta `588` | state `2/4/0`, flags `0004`, move `0000`, d8/da `0001/0002`, e8 `0008`, camera `0001/0149` | frame `846`, delta `313` | state `2/4/0`, flags `0200`, move `0000`, d8/da `0000/0004`, e8 `0008`, camera `0000/0147` |

Note: the arcade Lua summary listed `y_change=307` because the setup sample's prior Y was `0`; the first post-active downward Y change is frame `311`, active delta `4`.

### Classification

**B + C + D.** Build 0157 does not fail the intro drop outright: Genesis reaches the same landing Y (`0x0070`) and sets movement/contact bitfield `a5+0x10D0 = 0x0002`. However, compared to the original arcade runtime, Genesis:

- falls more slowly in logical active-frame time (`delta 43` vs arcade `delta 31` landing);
- uses a different command word (`0x5553` vs `0x00FF`);
- produces a different stable vertical correction value (`a5+0x10DA = 0x0004` vs arcade `0x0003`);
- starts camera/scroll movement later and with a different cadence (`0x01FC` at stable sample vs arcade `0x01F3`).

It is **not** E/F for the intro landing boundary: Genesis does land and does not exit/death before landing in this trace. The later active-state exit differs, but that is downstream of the bounded drop/landing proof.

## Q2 - Entry Command `a5+0x137A` Writer

### Proven Writes

Native watchpoints show the active-gameplay command write comes from mapped equivalent PCs:

- Arcade: `arcade_pc 0x051034` writes `0x00FF` into arcade work RAM `0x0010D37A`.
- Genesis: `runtime_genesis_pc 0x051234` writes `0x5553` into Genesis-WRAM `0x00FF137A`.

Disassembly:

```asm
; arcade_pc 0x05102E..0x051034
5102e: 3039 0010 c016  movew 0x10c016,%d0
51034: 3b40 137a       movew %d0,%a5@(4986)

; runtime_genesis_pc 0x05122E..0x051234
5122e: 3039 0010 c016  movew 0x10c016,%d0
51234: 3b40 137a       movew %d0,%a5@(4986)
```

Representative trace lines:

```text
ARCADE  EVENT CMD_WRITE cyc=38947729 pc=051038 addr=0010D37A size=16 data=000000FF state=0002/0003/0000 y=0030
GENESIS EVENT CMD_WRITE cyc=66622329 pc=051238 addr=00FF137A size=16 data=00005553 state=0002/0003/0000 y=0030
```

The debugger reports the post-instruction PC (`0x051038` / `0x051238`); the write instruction is at `0x051034` / `0x051234`.

### Classification

**A / C, with exact source boundary.** Genesis receives the corresponding copied arcade write, but the value differs because the copied instruction still reads absolute `0x0010C016` before writing to `a5+0x137A`. Arcade reads live arcade work RAM at `0x0010C016`; Genesis reads the same absolute address in the Genesis runtime address space, not the KF-039 mapped WRAM address `0x00FF0016`.

Observable fact: the written command values are `0x00FF` arcade and `0x5553` Genesis at the same mapped routine boundary.  
Interpretation: the immediate next implementation boundary is the raw work-RAM literal read at mapped instruction pair `arcade_pc 0x05102E` / `runtime_genesis_pc 0x05122E`, not the later Y writer itself.

## Q3 - Player Y `a5+0x10C0` Writes During Drop

### Setup Write

The setup routine initializes X/Y from the stage setup table:

```asm
; arcade
5052e: movew %d1,%a5@(4286)  ; X
50534: movew %d1,%a5@(4288)  ; Y

; Genesis
5072e: movew %d1,%a5@(4286)  ; X
50734: movew %d1,%a5@(4288)  ; Y
```

Both runtimes enter active gameplay with player `X/Y = 0x0020/0x0030`.

### Runtime Movement / Landing Writes

The landing write is produced by mapped collision/movement helper pairs:

- Arcade write: debugger post-PC `0x053942`; instruction at/around arcade vertical landing helper in `0x0538EA..0x053954`.
- Genesis write: debugger post-PC `0x053B42`; mapped equivalent helper range `0x053AEA..0x053B54`.

Representative landing lines:

```text
ARCADE  EVENT Y_WRITE cyc=42956007 pc=053942 addr=0010D0C0 data=00000070 state=0002/0003/0000 x=0020 cmd=00FF move=0002 da=0001
GENESIS EVENT Y_WRITE cyc=71733169 pc=053B42 addr=00FF10C0 data=00000070 state=0002/0003/0000 x=0020 cmd=5553 move=0002 da=0000
```

Arcade Y cadence after active begins: `0030,0030,0030,0030,0031,0032,0033,0034,0035,0036,0037,...,006E,0070`.  
Genesis Y cadence after active begins: `0030,0030,0030,0034,0034,0034,0034,0038,...,006C,0070`.

### Interpretation

Downward Y movement is expected for Stage 1; the bug is not falling. The divergence is that Genesis reaches the same landing Y through a slower, coarser correction sequence while holding the wrong command word (`0x5553`).

The Y writers are active and mapped; this is not a missing Y-update path. The first proven upstream divergence is the entry-command source value at `0x051034/0x051234`.

## Q4 - Collision / Floor Reads Before and At Landing

Collision/floor candidate routines were hit in both runs before and at landing.

Event counts from native traces:

| Event | Arcade count | Genesis count |
|---|---:|---:|
| `COLL_ENTRY_0538EA` / `COLL_ENTRY_053AEA` | `531` | `63` |
| `COLL_ENTRY_053956` / `COLL_ENTRY_053B56` | `461` | `63` |
| `COLL_ENTRY_0539C2` / `COLL_ENTRY_053BC2` | `70` | `0` |
| `MAP_HELPER_053A2E` / `MAP_HELPER_053C2E` | `4449` | `634` |
| `PROBE_053A6E` / `PROBE_053C6E` | `531` | `2` |
| `CORRECTION_0512C8` / `CORRECTION_0514C8` | `588` | `120` |
| `MOVE_ACCUM_0517FA` / `MOVE_ACCUM_0519FA` | `531` | `63` |

Representative pre-landing and landing-window Genesis events:

```text
GENESIS EVENT COLL_ENTRY_053B56 ... y=006C cmd=5553 move=0000 da=0000 d2=00000084 a0=0010E60C
GENESIS EVENT CORRECTION_0514C8 ... y=006C cmd=5553 move=0000 da=0000
GENESIS EVENT Y_WRITE pc=053B42 ... data=00000070 ... cmd=5553 move=0002 da=0000
GENESIS EVENT CORRECTION_0514C8 ... y=0070 cmd=5553 move=0002 da=0000
```

Therefore collision/floor reads are happening. The issue is not absence of collision execution. Genesis takes a different path frequency/cadence and produces different correction state after the already-proven command divergence.

## First Exact Divergence

**First exact proven runtime divergence:** copied arcade routine `arcade_pc 0x051034` / `runtime_genesis_pc 0x051234` writes different command values to `a5+0x137A`:

- Arcade writes `0x00FF` to `0x0010D37A`.
- Genesis writes `0x5553` to `0x00FF137A`.

The immediately preceding instruction reads absolute `0x0010C016` in both images. In arcade this is work RAM; in Genesis this is not the mapped A5/WRAM address. This matches the KF-039/KF-036 class of raw work-RAM literal rebase gaps.

## Recommended Next Boundary

No fix was implemented here. The smallest safe next investigation/implementation boundary is the raw work-RAM literal read feeding the command copy:

- `arcade_pc 0x05102E`: `move.w 0x0010C016,%d0`
- `runtime_genesis_pc 0x05122E`: same copied read in Build 0157
- destination write: `a5+0x137A` (`arcade 0x0010D37A`, Genesis-WRAM `0x00FF137A`)

Any implementation should first prove what state should exist at mapped Genesis-WRAM `0x00FF0016`, which earlier code creates that state, and why the copied absolute read still sees `0x5553`. Do not patch the landing/Y routine as the first step; it is downstream and active.

## STOP Status

STOP triggered: **NO**.

The initial missing native debugger logs were resolved by bounded debugger-enabled reruns. Runtime evidence is sufficient for a documentation-level answer and a narrow next boundary. No implementation was attempted.

## Open / Closed Issues Impact

Open issues touched: OPEN-001, OPEN-017, OPEN-024; OPEN-018 context only.  
New issues opened: none.  
Issues closed: none.  
Issues intentionally deferred: continue/game-over, D00298, Exodus, audio, tilemaps, sprite rendering, general scroll cleanup.

## KNOWN_FINDINGS Impact

Option A - no new finding to index yet. This evidence is consistent with existing KF-039/KF-036 raw work-RAM mapping lessons and narrows one concrete runtime boundary, but no new durable architecture rule was established.
