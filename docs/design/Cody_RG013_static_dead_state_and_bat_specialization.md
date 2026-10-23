# RG-013 Static Dead-State Analysis and Bat-Family Native Specialization

Date: 2026-10-22  
Agent: Cody  
Scope: static 68000/native data-flow analysis and bounded reconstructed C

## Scope control and baseline

The accepted baseline remains Build 0472. The normal ROM
`dist/rastan-direct/rastan_direct_video_test_build_0472.bin` still hashes to
`5b855e163a572c3a511a76470199c9cb13324f6ea0739bbd0f6834b80092dc7a`.
The annotated `accepted/build-0472` tag peels to exact ROM-producing source
`4d5aadb0e92387617594404f9e757597c87517a3`; the counter remains 472.

No MAME process, gameplay, trace, movie, save state, bot, production source,
remap specification, ROM build, or build number was used. The supplied RG-013
text physically ends after `Do NOT change: finalizer; clipping`, in the middle
of its implementation constraints. Static Phases 1 and 2 are safe and complete
from the available text. Producing Build 0473 without the missing remainder
would not be instruction-complete, so Build 0473 was not produced or consumed.

## Policy boundary

The PC090OJ semantic cut remains retained arcade actor lifecycle, animation
selector, orientation, position, attribute policy, visibility and ordering to
final Genesis semantic pieces and SAT entries. The removed chip tail remains
the PC090OJ descriptor/piece interpreter, object-RAM formatting and mirroring,
object-RAM scan, and record decoder. This analysis removes no additional chip
tail and introduces no compatibility state, shadow, mirror, cache, or gameplay
authority. The generated Level-A/Level-B compatibility classifiers remain
transitional native-coverage machinery.

## Evidence reused

- canonical Ghidra function inventory, call graph, xrefs and full listing;
- `build/maincpu.disasm.txt` original 68000 disassembly;
- current `pc090oj_hooks.s`, generated base/usage/frame tables and verifiers;
- RG-007 airborne functions without reopening their completed analysis;
- RG-011/RG-012 reports and reconstructed actor lifecycle/template code;
- current address map where mapped-PC evidence was required.

No new tracing or analysis infrastructure was created.

## Phase 1 — static register and CCR analysis

### Retained function-body cuts 0x41DAE and 0x45DFA

Both original functions ultimately call `0x03D054` and its selected compositor
tail. Across every compositor-0 path relevant to current R1-S1 gameplay, the
original operation writes/clobbers `D0,D1,D2,D3,D5,D7,A0,A1`. It preserves
`D4,D6,A2,A3,A4,A5,A6`. Specialized compositor dispatches retain the same
preserved set. Therefore the replacement is not required to restore the eight
registers the original operation itself destroyed.

Classification at the retained return boundary:

| State | Classification | Reason |
|---|---|---|
| D0,D1,D2,D3,D5,D7,A0,A1 | DEAD for replacement preservation | The original replaced operation clobbers them on all rendering paths; they are not part of its caller-visible ABI. |
| A5 | LIVE — preserve | Retained global base is read immediately by following update functions. |
| D4,D6,A2,A3,A4,A6 | UNKNOWN — preserve | The original operation preserves them; complete downstream proof does not justify weakening that contract. |
| N,Z,V,C | DEAD | Tail return reaches `0x03AB7C`, whose first instruction is `TST.W`, or direct caller `0x03A818`, whose successor establishes new flags before a conditional consumer. |
| X | DEAD on the audited successors | No ADDX/SUBX/ROXL/ROXR or other X consumer occurs before later arithmetic establishes a new value. |

Current native ownership unnecessarily preserves all 15 registers in each
stage dispatcher and then separately preserves 12 registers plus A4 in the
gameplay finalizer. A safe caller-specific design is one outer hook-frame save
of the exact original-preserved set `D4/D6/A2-A6` around dispatch plus finalizer,
with internal no-preserve entries. The public VBlank finalizer entry must retain
its existing conservative ABI.

Static cost, using documented 68000 MOVEM timing (`MOVEM.L regs,-(SP)` =
`8+8n`; `MOVEM.L (SP)+,regs` = `12+8n`) and ordinary longword stack moves:

| Item | Current | Candidate | Difference |
|---|---:|---:|---:|
| Save/restore instructions | 6 | 2 | 4 avoided |
| Register longword transfers | 56 | 14 | 42 avoided |
| Maximum outer stack frame | 60 bytes | 28 bytes | 32 bytes avoided |
| SR/CCR stack operations | 0 | 0 | none |
| JSR/RTS | unchanged in conservative design | unchanged | none claimed |
| Cycles | 496 | 132 | **364 CALCULATED cycles/gameplay presentation pass** |

This is calculated static instruction time, not measured gameplay performance.
It is broad, once-per-gameplay-update work and is the highest-ranked candidate.

### Per-actor generated dispatch

`.Lnative_emit_actor_common` must preserve D5 (stage loop/index) and A1 (legacy
lane cursor). Both are read after the nested generated probes. Its current
`MOVEM.L D5/A1` is minimal: 8 stack bytes and four longword transfers remain.

`.Lnative_generic_frame_try` returns D0 as a live hit/miss value; its caller
immediately tests it. D2 is a live input and D5 becomes the retained piece
ceiling. D0-D4/D6-D7/A0-A3 are internal scratch once the wrapper's D5/A1
contract is honored. Each internal branch establishes CCR before consuming it;
no incoming CCR is live. There is no redundant save/restore at the Level-B or
Level-A boundary.

### Semantic queue and piece finalization

At `.Lnq_emit_lane`, A0 is the live queue cursor, D5 is the live emitted count,
A2/A3 are live residency/SAT contexts, and D6 is the loop counter. The explicit
word save of D6 around `.Lnq_emit_entry_cached` is required because the entry
clobbers D6. D1-D4 are overwritten by the next tuple before reuse. Incoming CCR
is dead; the entry establishes flags before every branch.

The general `.Lnq_emit_entry` work remains semantically live: position, clipping,
attribute/variant selection, capacity, residency, DMA work and SAT order are
dynamic. No finalizer or clipping removal is proposed.

### Reverse-residency miss helper

`.Lnq_reverse_replace` currently saves
`D0-D2/D6-D7/A0-A1` (7 longs). At its only caller:

- D0 (forward-table byte offset) and D2 (Y) are live after return;
- D1 is restored by the caller's explicit word pop before any use;
- D6, D7 and A1 are overwritten at `.Lnq_hit` before use;
- A0 is not read after return;
- CCR is overwritten before any conditional or extended-arithmetic consumer.

The statically sufficient helper mask is therefore `D0/D2`.

| Item | Current | Candidate | Difference |
|---|---:|---:|---:|
| MOVEM mask | 7 longs | 2 longs | 5 longs |
| Stack | 28 bytes | 8 bytes | 20 bytes avoided |
| Longword transfers | 14 | 4 | 10 avoided |
| SR/CCR operations | 0 | 0 | none |
| Cycles | 132 | 52 | **80 CALCULATED cycles/residency replacement** |

This is valid but miss-only and therefore ranks below the broad retained-cut
candidate.

### Other audited preservation

The gameplay HUD score dirty notifier's SR save/restore is live because it
replaces sites with distinct flag contracts. The public VBlank finalizer,
contact-coordinate helper, status producer, and unrelated PC080SN dispatcher
retain multiple caller contracts; no narrower universally safe mask was proven.
Unknown state remains preserved.

## Phase 2 — Large Bat / Small Bat lifecycle closure

New bounded reconstructions cover original `0x45B18` and `0x45BE8`.

### Creation and activation

`0x45B18` owns fixed records:

- A5+0x06C8: rec_type 0x0A/comp 0 in every round except round 2, where it is
  deliberately rec_type 0x12/comp 1;
- A5+0x09C8: one rec_type 0x0B/comp 0 Small Bat;
- A5+0x0988: another Small Bat from round 4;
- A5+0x0948: another Small Bat from round 6.

Each record is first passed through `0x4092E`, which zeros the complete 0x40-byte
record and its companion. The creator then writes rec_type and compositor,
`0x4543E` applies the record-type template, `0x45CFC` sets active/state 3/timer,
and `0x45BE8` writes X/Y anchors and sets only `+0x27` bit 7. Thus bit 6 remains
clear and the live bat uses embedded palette policy.

The template records establish:

| Family | rec_type | Base | Initial selector | Config/pieces | Comp | Policy |
|---|---:|---:|---:|---:|---:|---|
| Large Bat | 0x0A | 0x03F6 | 0xB6 | 0x0002 | 0 | embedded |
| Small Bat | 0x0B | 0x0268 | 0xB9 | 0x0001 | 0 | embedded |

Animation remains authoritative and dynamic over B6-B8 / B9-BB. Orientation,
position, motion, state, clipping, effective control bank, residency and SAT
order remain dynamic.

### Impact, death, retirement, and reuse

- RG-007 `0x4736A` can send an airborne actor through `0x447F0/0x448B2` to
  state 0x0F after the proven ground-impact condition.
- `0x447CE` has the separate rec_type 10/11 freeze reaction.
- `0x44804` can start the lethal state-0x0F transition; type 11 participates in
  its score branch.
- `0x42ABC` owns bat death presentation: it sets comp 0, base 0x0275 and selector
  0xA8, then calls `0x4092E` on the following gated update.
- Types 10/11 use this short bat-pop path. They do not enter the ordinary
  `0x40CCC` family-12 reward/drop conversion.
- `0x4092E` zeros rec_type, base, comp and palette byte; no bat identity remains.
- Later `0x45B18` reuse again starts with the same complete clear and template
  application. No partial/stale identity survives.

Whole-program direct-writer review also exposes two important aliases:
rec_type 0x0A is used by the round-5 boss-body table, and rec_type 0x0B is used
by the five-component creator. Therefore rec_type alone is not a globally unique
bat handle. Their non-bat selectors/bases differ, but a creation-time handle
would require creator-specific establishment plus invalidation at impact/death
and clear/reuse sites.

### Specialization decision

A persistent presentation handle is **NOT WORTHWHILE / NOT SAFE** under the
prompt's bounded-site rule: it needs additional lifecycle maintenance and
rec_type is aliased. No handle, dirty flag, or scattered store hook is proposed.

A nonpersistent direct guard is statically safe: rec_type 0x0A plus selector
B6-B8, or rec_type 0x0B plus selector B9-BB, followed by the still-dynamic
control-bank check, orientation and generated frame lookup. Creation completes
all base/comp/policy writes before activation; death changes selector to A8 in
the same update that changes base; clear zeros both. Thus no rendered transient
can satisfy a bat selector while carrying a non-bat base/comp/policy. This path
would avoid stable-family rediscovery without owning gameplay state.

An exact assembly sketch was not implemented because the prompt remainder is
missing. Structural CALCULATED savings versus the current generic hit path are:

| Window | Instructions avoided | Data/table reads avoided | MULU avoided |
|---|---:|---:|---:|
| one Large Bat frame | 29 | 12 | 1 |
| one Small Bat frame | 27 | 12 | 1 |
| Large + Small frame | 56 | 24 | 2 |
| pair for 30 frames | 1,680 | 720 | 60 |
| pair for 60 frames | 3,360 | 1,440 | 120 |
| pair for 120 frames | 6,720 | 2,880 | 240 |

These are straight-line instruction/read counts from the current Level-B
classification and the proposed guarded fast path. They are not measured time
and deliberately exclude the unchanged orientation, frame, piece and finalizer
work. A final cycle number requires the exact assembled branch layout.

## Candidate ranking and disposition

1. **Combined caller-specific retained-cut preservation** — fully proven,
   broad, 364 calculated cycles per gameplay presentation pass; recommended.
2. **Reverse-residency helper mask D0/D2** — fully proven, 80 calculated cycles
   per replacement, but miss-only.
3. **Direct guarded bat fast path** — lifecycle/equivalence basis proven and
   bounded, but bat-only and adds dispatch structure for non-bat actors.
4. **Persistent bat handle** — rejected.

Only candidate 1 should be considered for Build 0473. It was not implemented
because the supplied RG-013 instructions are truncated inside the explicit
`Do NOT change` list. No optimization was combined, no build was produced, and
accepted Build 0472 remains unchanged.

## Durable outputs

- `analysis/decompilation/c/raw/00045b18.c`
- `analysis/decompilation/c/raw/00045be8.c`
- `analysis/decompilation/c/rastan_actor_creation.c`
- `analysis/decompilation/c/function_coverage.csv`

Coverage after this bounded work: 141 COMPLETE, 10 PARTIAL, 0 STUB_ONLY.
