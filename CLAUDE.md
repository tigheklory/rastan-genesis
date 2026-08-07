# CLAUDE.md — Project Guidance for Rastan Genesis

This file records permanent project intent for anyone (including AI agents) working on the
Rastan Genesis port. Read it alongside `RULES.md` and `ARCHITECTURE.md` before starting work.

Rastan Genesis is a **hardware-level translation** of the original Taito Rastan arcade program
to the Sega Genesis. The arcade program stays authoritative; only its arcade-chip-specific
*execution* is replaced with native Genesis hardware realization.

---

## Holistic Native-Replacement Mandate

The Rastan Genesis project is a hardware-level translation of the original arcade program, not an
accumulation of compatibility patches.

The original arcade program remains authoritative for gameplay, state, timing, traversal and
semantic decisions. PC090OJ and PC080SN device-specific execution must ultimately be removed and
replaced by native Sega Genesis VDP/SAT realization.

Use Rainbow Islands' native Mega Drive implementation philosophy and Sonic 1's BuildSprites-style
semantic-object → mapping/piece-expansion → sequential SAT production as **structural references
where applicable**. They are examples of clean native Genesis realization — not sources of any
Rastan-specific game logic.

Work by **complete semantic ownership boundaries**, not merely by individual patched functions,
record writers, screens or symptoms.

If a low-level routine lacks required semantic information, **trace upstream** until the complete
semantic owner is found. Split ownership *expands the task boundary*; it is not by itself a reason
to STOP.

Prefer **one coherent producer-family / subsystem replacement that removes legacy code** over
multiple screen-specific gates or small compatibility patches.

Do not create a growing hybrid architecture in which native and legacy renderers are selected by
increasingly specific scene/state conditions.

Every implementation task should seek to make the legacy subsystem **materially smaller**.

The target shape is always:

    original arcade semantic decision
        -> mapping / glyph / piece selection
        -> compact native Genesis sprite/plane production
        -> staged SAT / Plane data
        -> existing arcade-owned VBlank commit

and never:

    arcade semantic state -> emulated PC090OJ/PC080SN record -> compatibility RAM
        -> scan / decode / project -> Genesis output

---

## Efficiency Is a Project Requirement

Efficiency matters. Repeated STOPs, avoidable analysis loops, unnecessary intermediate builds and
tiny partial changes consume paid model/tool usage and **real money** for Tighe. Do not force
another iteration when the requested architectural direction is already clear.

Use analysis to **enable** implementation, not to avoid it. The desired working loop is:

    understand the complete semantic subsystem
        -> trace whatever ownership is necessary
        -> implement the clean native replacement
        -> remove the obsolete legacy tail
        -> validate it
        -> move on

Being "safe" by repeatedly declining the actual work, making tiny partial changes, or forcing
another prompt is **not** efficient and is **not** helpful.

---

## Never Delete a Producer Before Replacing Every Live Semantic Consumer

A legacy PC090OJ/PC080SN producer may be retired **only after every live semantic behavior it
supplies has a proven native owner**.

Seeing that one or two screens already have native equivalents does **not** prove that all callers
are superseded. Existing native ownership in one state does not establish ownership in another.

A global `rts`, NOP, dead-write suppression, skipped call, or discarded output is **not** native
replacement — it is deletion of behavior.

Before retiring a shared producer:

- Enumerate **all** live callers and identify the semantic output each caller relies on.
- If callers use different layout/state owners, trace those owners and unify them at the correct
  semantic boundary.
- Do **not** infer an output is unnecessary merely because the currently reachable test harness
  does not display it. "Not observed in the current test window" is not evidence of deadness.
- If a caller cannot be naturally reached, build an **external** validation method (MAME input
  script, state-driving Lua, save state, deterministic setup, watchpoint/provenance trace) rather
  than deleting its output untested. Never add production ROM scaffolding for this.

The required order is always:

    prove semantic ownership -> implement native replacement -> validate consumers -> remove legacy

Never:

    remove producer -> see what breaks -> patch individual screens afterward

Build 0267 violated this: `0x3B802`/`0x5A098` were stubbed to `rts` after proving only the title and
gameplay consumers, and the title-only harness missed that ROUND/READY, the throne/PUSH-BUTTON
screen and the ranking screen still consumed `0x3B802`'s high-score output. That regression cost
paid usage and real money to detect and undo. It must not recur.
