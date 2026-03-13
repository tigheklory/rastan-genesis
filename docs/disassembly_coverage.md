# Rastan 68000 Disassembly Coverage

This file tracks which parts of the arcade `68000` program are already
understood well enough to work from, and which parts still need direct study.

Use it together with:

- [docs/disassembly_reference.md](/home/tighe/projects/rastan-genesis/docs/disassembly_reference.md)
- [build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt)
- [tools/show_disasm_range.py](/home/tighe/projects/rastan-genesis/tools/show_disasm_range.py)

Status terms:

- `high`: enough understanding to port or mirror behavior with confidence
- `medium`: structure is clear, but ownership/details are still unresolved
- `low`: only partial structure or weak hypotheses

## Coverage Table

| Range | Subsystem | Status | Notes |
| --- | --- | --- | --- |
| `0x000000..0x003fff` | vectors / boot / early tables | low | raw binary disassembly only; mostly not useful for current gameplay work |
| `0x03a772..0x03a85e` | input latch and top-level mode flow | high | title/start to gameplay handoff is mapped well enough to mirror |
| `0x03b8b0..0x03c54f` | startup/test/title display writers | medium | real `0xC08000` text-RAM and `0xD000xx` startup display paths are now identified; glyph/tile mapping still needs implementation |
| `0x03c9e8..0x03d1ff` | sprite attribute/builder front-end | medium | dispatcher role is clear, but non-family-1 branches need more work |
| `0x03d054..0x0400ff` | sprite-family dispatchers | low | only family-1 path has meaningful coverage so far |
| `0x04092e..0x040a46` | actor reset / replacement logic | medium | generic object reinit path is understood structurally |
| `0x045248..0x04527c` | direct actor seed helper | high | `0x45248` is now well understood and reused by direct `0x02c8` seeds |
| `0x043f4e..0x043f86` | fixed-slot sweep/reset helper | high | `0x43f4e/0x43f52` sweep `0x03c8` entries and call `0x447f0`; they are not class writers |
| `0x040b66..0x041e22` | `0x02c8` actor system | high | update, state cluster, and frame logic are now documented; body ownership still unresolved |
| `0x040c62..0x040cca` | `0x02c8` repack/fallback matcher | medium | matches entries on `+0x3e` and `+0x752`, then forces `0x44852`; not a class bridge |
| `0x04375c..0x0441a0` | `0x02c8` transition/side-effect cluster | medium | transition/timer logic is documented; ownership value is low |
| `0x044c5a..0x044fa8` | `0x02c8` filter/selector helpers | high | overlap-table logic is understood well enough |
| `0x041cfa..0x041d24` | `0x02c8` record loader | high | table shape and field writes are confirmed |
| `0x041dd2..0x041e9e` | object-group render passes to PC090OJ RAM | medium | destinations and source groups are known |
| `0x041f0e..0x041fff` | active gameplay loop entry | medium | top-level role is clear; many callees still need subsystem notes |
| `0x0420e6..0x042fff` | `0x0508` actor state machine | medium | dispatch and key player-linked coordinate copies are known |
| `0x0433ac..0x0450cf` | helper/effect constructors and bridges | low | several small constructors identified, but not comprehensively mapped |
| `0x0443e0..0x0449ff` | player-linked visibility / bridge logic | high | `0x447b6`, `0x447ce`, `0x448b2` are strong anchors |
| `0x0449b4..0x044fff` | `0x02c8` proximity / visibility and follow-on paths | medium | enough to prioritize this region for body ownership |
| `0x0450d8..0x045fff` | stage/event helper actor systems | medium | many constructors known; several proven false leads for player body |
| `0x04543e..0x0457ff` | animation records and palette application | high | `0x4543e` and `0x45684` roles are well established |
| `0x046216..0x0464ff` | fixed-slot event state machines on `0x028a/0x0288/0x021c` | medium | clearly generic choreography controllers; useful mainly to rule out false ownership assumptions |
| `0x04650e..0x04677a` | stage-id dispatcher into generic fixed-slot seeds | medium | bridges `a5 + 0x0118` into `0x4677c` and neighboring slot seeds; not body ownership by itself |
| `0x046300..0x046776` | generic fixed-slot event seeding cluster | medium | shows `0x46790` is reused broadly across non-`0x02c8` slots too |
| `0x04677c..0x04684c` | direct `0x02c8` constructor / seeding path | medium | strong positive constructor evidence; still not proven player-body ownership |
| `0x04684e..0x046c1f` | concrete `0x02c8` branch cluster | medium | now identified as a useful body-facing lead |
| `0x047140..0x0474ff` | dominant `0x02c8` frame builders | high | frame logic and state sensitivity are now documented clearly |
| `0x04770e..0x0478ff` | family-1 sprite builder path | high | frame-record parser and tile decode are validated |
| `0x04a0d8..0x04a1ff` | generic spawn/replacement table path | medium | useful for palette/form logic, not proven body ownership |
| `0x04c706..0x04cb04` | event-driven direct `0x02c8` reseeds | medium | confirms `0x46790` is a live seeding entry point in stage/event code |
| `0x0501ea..0x0505a4` | stage initialization | high | stage/player spawn defaults are well documented |
| `0x051024..0x054a32` | active stage-entry and event flow | medium | entry logic is mapped well enough to separate it from body rendering |

## Strongly Understood Regions

These are stable enough to treat as factual working ground:

- `0x3a772..0x3a85e`
- `0x41cfa..0x41d24`
- `0x443e0..0x449ff`
- `0x4543e..0x457ff`
- `0x4770e` plus family-1 frame records
- `0x501ea..0x505a4`

## Weak or Misleading Regions

These have already produced false positives or still lack ownership proof:

- `0x0748` helper/subpart paths
- `0x45b2e` multipart helper constructor
- ad hoc family-1 candidate rendering without actor ownership proof
- stage-family actor candidates derived from `0x4449e` alone

## Current Bottleneck

The major blocker is no longer graphics decoding.

The current blocker is:

- identifying which constructor seeds the real `0x02c8` player-body actor
- proving its class/state path through `0x447b6`, `0x4684e`, `0x47140`, or
  `0x473b8`

The latest change is that direct `0x02c8` constructor-side evidence now exists.
The blocker is no longer "all constructor-side paths are helper-only." The
remaining blocker is proving which of those direct seeds reaches the bridge as
class `10`, `11`, or `18`, and where the seeded `0x02c8` slot picks up its
body-facing runtime state.

## Recommended Documentation Order

To keep expanding coverage without wasting time:

1. finish a dedicated `0x02c8` reference
2. finish a dedicated `0x0508` reference
3. finish a dedicated bridge/visibility reference
4. finish a dedicated constructor reference
5. finish a dedicated `0x02c8` frame reference
6. finish a dedicated `0x02c8` state reference
7. finish a dedicated `0x02c8` transition reference
8. finish a dedicated `0x02c8` filter reference
9. finish a dedicated `0x02c8` constructor reference
10. finish a dedicated startup-to-gameplay reference
11. finish a dedicated sprite/animation reference
12. only then fill in lower-value helper clusters
