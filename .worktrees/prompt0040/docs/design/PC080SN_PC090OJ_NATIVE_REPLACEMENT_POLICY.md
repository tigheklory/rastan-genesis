# PC080SN / PC090OJ Native-Replacement Architecture Policy

**Status:** CANONICAL / AUTHORITATIVE architecture policy. This document governs all
current and future PC080SN (tilemap) and PC090OJ (sprite/object) graphics work in the
`apps/rastan-direct/` assembly project.

**Date established:** 2026-07-27 (Tighe architecture decision).
**Supersedes:** any earlier statement — in design docs, `AGENTS.md`, prompts, or agent
guides — that implies a software PC080SN/PC090OJ device, virtual chip RAM, C-window /
name-RAM shadow, object-RAM mirror, generic chip-address translation, or full-map
projection as the *final* architecture. Historical build reports and failure evidence
are NOT rewritten; they carry a superseded banner and link here.

---

## 1. The architecture decision (authoritative)

The final Rastan Genesis architecture **must not emulate, reproduce, mirror, or translate
the hardware behavior of the arcade PC080SN or PC090OJ after the arcade program has already
specialized its output for those chips.**

The original arcade program remains authoritative for gameplay and for the highest-level
semantic graphics decisions. The required transformation is:

```
original arcade semantic decision  →  native Genesis VDP realization
```

It must **not** be:

```
original arcade chip-specific operation
    → software PC080SN/PC090OJ representation
    → helper interprets or projects that representation
    → Genesis VDP realization
```

The implementation must **cut at the highest safe original-arcade boundary where the game
has decided *what* graphics operation is required but has not yet begun executing
hardware-specific PC080SN or PC090OJ mechanics.**

---

## 2. The semantic-versus-chip-specific boundary model

Every graphics code path has two halves separated by a **semantic cut**:

- **ABOVE the cut — arcade semantic decision (RETAIN, arcade-owned):** the game has
  decided the meaning of the operation (which scene/map, which camera/scroll, which
  source/descriptor, which ring/stream step, that an entering row/column must publish,
  the logical terrain-cell identity, the collision word, which actor exists and its
  position/animation/priority/palette/flip/visibility/order). This is gameplay/graphics
  *intent*. It stays in the arcade program.

- **BELOW the cut — chip-specific execution (REPLACE, then prune):** the code that exists
  only to operate the physical PC080SN/PC090OJ — walking chip name-RAM/object-RAM
  addresses, computing chip-shaped destinations, writing chip registers/control words,
  and any software that re-reads or decodes those chip-shaped writes afterward.

The native tail consumes the **arcade semantic state directly** and produces **final
Genesis Plane A / Plane B name-table data and bounded VDP jobs** (PC080SN) or **final
Genesis SAT entries** (PC090OJ). It never consumes a chip-shaped software representation.

**Litmus test:** *If the native helper's input is a fake chip address, a virtual name-RAM
cell, a projected/tall buffer, a PC090OJ object record, a mirror, or a shadow, then the
cut was made too low — below the chip-specific execution instead of above it. That helper
is transitional compatibility code, not the accepted final architecture.*

---

## 3. PC080SN policy (tilemap → Plane A / Plane B)

### Retain (arcade-owned semantic decisions)
- scene and map selection;
- camera and scroll decisions;
- source and descriptor selection;
- ring and stream progression;
- the decision to publish an entering row or column;
- logical terrain-cell identity;
- collision publication (to `0x10DE00`);
- timing and VBlank ownership.

### Replace, and ultimately prune (PC080SN-specific execution)
- PC080SN name-RAM / C-window address walking;
- PC080SN register writes;
- PC080SN rowscroll / device control;
- chip-specific destination calculations made *after* the semantic operation is known;
- generic PC080SN address-range dispatch;
- readable PC080SN mirrors or shadows;
- virtual arcade-format name RAM;
- 64×64 translated visual shadows;
- tall-buffer projection used as a software representation of PC080SN name RAM;
- later interpretation of chip-shaped writes into Genesis output.

The native tail directly generates final Plane A / Plane B data and bounded VDP jobs from
the retained arcade semantic state (source/descriptor/ring/scroll at the publication
event). Preferred: regenerate the entering edge from arcade state; keep a cache only under
the cache rule (§7).

---

## 4. PC090OJ policy (object → SAT)

### Retain (arcade-owned semantic decisions)
- actor lifecycle;
- spawn and retirement decisions;
- animation;
- position; priority; palette; flip; visibility;
- ordering when behavior depends on it.

### Replace, and ultimately prune (PC090OJ-specific execution)
- PC090OJ object-RAM record production;
- chip-specific object control words;
- object-RAM mirrors or shadows;
- software scans of emulated PC090OJ records;
- decoding chip-formatted records after they have been written;
- generic PC090OJ device emulation.

The native tail directly generates final Genesis SAT entries from the retained arcade
actor/object decisions.

---

## 5. Examples of correct and incorrect replacement

### PC080SN — CORRECT
> At the arcade producer boundary the game has decided "publish entering column N of
> tilemap1, source block S, ring step R." The native helper reads S/R/scroll, converts
> each cell's tile+attr once via the LUT, writes the final Plane A name words to the
> wrapped 64×32 cell, and reproduces the collision store — **without ever forming a
> C-window address or a virtual name-RAM cell.** The complete PC080SN name-RAM walk below
> the boundary is retired.

### PC080SN — INCORRECT
> The arcade writes chip-shaped cells into a virtual name-RAM / tall buffer; a VBlank
> "projector" later reads that buffer and copies it to the VDP. This keeps a software
> PC080SN representation and merely relocates the chip walk — **rejected as final
> architecture** (may exist only as clearly-labeled transitional compatibility, §7).

### PC090OJ — CORRECT
> At the actor→object boundary the game has decided an actor's position/anim/priority/
> palette/flip/visibility. The native helper writes the final Genesis SAT entry directly
> from those actor fields. The PC090OJ object-RAM record production below is retired.

### PC090OJ — INCORRECT
> The game writes PC090OJ object-RAM records into a mirror; a helper scans/decodes the
> mirror each frame to build the SAT. This is object-RAM emulation — **rejected as final
> architecture** (transitional only, §7).

---

## 6. Boundary-selection requirements (must be proven for every boundary)

Using an existing call site is acceptable **only when that call site is the highest safe
semantic producer boundary.** It is **not** sufficient that a helper is called from an old
PC080SN/PC090OJ hook. For every boundary, documentation and implementation must prove:

1. **what arcade semantic decision has already been made** above the boundary;
2. **what arcade-owned state and side effects remain above** the boundary (ring/source/
   descriptor progression, collision, scroll, timing, loop bookkeeping, return contract);
3. **where chip-specific execution begins below** the boundary;
4. **which complete PC080SN/PC090OJ block will be bypassed or retired;**
5. **that the replacement consumes semantic arcade state, not a chip-shaped software
   representation.**

A boundary that reproduces the visible result but drops an arcade-owned side effect
(counter/cursor/ring advance, collision, descriptor progression) is invalid — a
**visible-only replacement is prohibited.**

---

## 7. Temporary compatibility rules

Existing compatibility code may remain **temporarily** when a frontend or unconverted path
still requires it. Such code must be:

- explicitly labeled **transitional / compatibility-only**;
- isolated from converted native gameplay ownership;
- prevented from overwriting native output;
- accompanied by identified producers **and** consumers;
- accompanied by a removal boundary or a stated unresolved blocker.

**Do not** introduce new shadows, mirrors, virtual chip RAM, generic device dispatch, or
parallel renderers as a shortcut. **Do not** describe transitional compatibility code as
the target native architecture.

**Cache rule:** prefer regenerating the entering edge from arcade state at the publication
event. A retained cache is allowed only if you prove (1) a value that cannot be regenerated
at the event, (2) the exact dependent producer, (3) the minimum dimensions/fields, (4) why
it is not a virtual chip name-RAM/object-RAM. No 64×64 shadow, no arcade-format mirror, no
retaining non-resident converted cells by default.

---

## 8. Prohibited final architecture

Explicitly prohibited as the accepted final design (permitted only as isolated, labeled,
scheduled-for-removal transitional compatibility per §7):

- software PC080SN or PC090OJ device emulation;
- virtual / arcade-format name RAM; C-window / name-RAM shadow;
- object-RAM mirror or shadow; software scan/decode of emulated object records;
- 64×64 translated visual shadow; tall-buffer projection as a name-RAM stand-in;
- generic PC080SN/PC090OJ address-range dispatch / chip-address translation;
- writing chip-shaped state and decoding it afterward;
- helpers attached only at final hardware-write sites (rather than the semantic boundary);
- parallel/feature-flag gameplay renderers; Genesis-owned scene manager/scheduler/parser.

(These stack on top of `RULES.md`, which independently forbids a Genesis main loop,
Genesis frame ownership, and control-flow ownership.)

---

## 9. Implementation-review checklist

Future reviewers apply this compact checklist to any PC080SN/PC090OJ change:

- [ ] Is the selected boundary **semantic** rather than chip-write-level?
- [ ] What complete PC080SN/PC090OJ-specific block is **completely bypassed**?
- [ ] Does new code consume **arcade semantic state** or chip-shaped state?
- [ ] Are any **mirrors, shadows, virtual device RAM, range dispatchers, or projectors**
      being introduced or retained?
- [ ] Is retained compatibility **explicitly isolated and temporary** (with producers,
      consumers, and a removal boundary)?
- [ ] Does arcade code still own **gameplay, frame progression, and VBlank**?
- [ ] Does the Genesis helper **directly generate final VDP/SAT output**?
- [ ] Is there a **documented path for retiring** superseded compatibility code?

---

## 10. Native hardware replacement rule (mandatory future-prompt block)

Every future PC080SN/PC090OJ prompt must include this block directly (not only by
reference) so the decision survives partial context:

> **Native hardware replacement rule:**
> Preserve the original arcade semantic decision and cut before PC080SN/PC090OJ-specific
> execution. Replace the complete chip-specific tail with direct Genesis VDP/SAT
> production. Do not create or retain software PC080SN/PC090OJ devices, virtual chip RAM,
> C-window/name-RAM shadows, object-RAM mirrors, generic chip-address translation, or
> projection as the final architecture. Any temporary compatibility path must be
> explicitly identified and isolated.

---

## 11. Required prompt wording

Future PC080SN/PC090OJ implementation prompts must:

1. include the §10 block verbatim (concise wording is fine; the meaning is fixed);
2. require the agent to name **the semantic cut** and **the chip-specific tail being
   removed** before implementing;
3. require the §6 boundary proof (1–5) for the chosen boundary;
4. require the §9 checklist to be answered in the final report;
5. forbid introducing any §8 structure as anything other than isolated, labeled,
   scheduled-for-removal transitional compatibility (§7).

---

## 12. Required Agent Acknowledgement

**Andy and Cody must read this policy before proposing or implementing any PC080SN or
PC090OJ work.** In their response they must explicitly identify:

- **the semantic cut** they are making (what arcade decision is retained above it), and
- **the chip-specific tail** being removed below it (which complete PC080SN/PC090OJ block
  is bypassed/retired), and
- **any transitional compatibility** they are retaining, with its producers/consumers and
  removal boundary.

A response that cannot state the semantic cut and the removed chip tail is not compliant
with this policy and must not be merged.

---

## 13. Relationship to other governance

- `RULES.md` — non-negotiable rule referencing this policy (arcade owns execution; this
  policy adds the semantic-cut requirement for PC080SN/PC090OJ).
- `ARCHITECTURE.md` — native-replacement section linking here.
- `PROMPT_TEMPLATE.md` — carries the §10 mandatory block for PC080SN/PC090OJ prompts.
- `AGENTS.md` / `AGENT_GUIDE.md` — concise references directing agents here.

This policy is documentation/governance only. It does not by itself change any production
source, spec, Makefile, ROM, or build counter.
