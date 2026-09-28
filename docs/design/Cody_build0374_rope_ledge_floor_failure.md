# Cody — Build 0374 rope-side ledge floor failure

**Date:** 2026-09-24  
**Baseline:** Build 0373  
**Task result:** stopped without a patch or ROM because the requested first differing floor read is not present in the available evidence

## Result

The exact arcade landing and Genesis pass-through moments are **not captured** by the two
authoritative human `USER_MARK` traces. The ORIGINAL ARCADE window contains 213 frames
(`1725..1937`) with player Y fixed at `0x0070` and retained ring Y fixed at `0x127`: Rastan is
already standing on the upper ledge for the entire window. The GENESIS NTSC Build-0373 window
contains 241 frames (`1828..2068`) with player Y fixed at `0x0070` and retained ring Y fixed at
`0x147`: Rastan is already standing 32 pixels lower for the entire window.

Consequently neither trace contains the requested transition:

```text
ORIGINAL ARCADE: falling -> floor read -> downward motion stopped
GENESIS NTSC:    same world height -> no-floor read -> continued fall
```

The captures also do not record the player foot extent at `A5+0x1130`, pending displacement in
`D6`, or instruction-level reads. Those values are required to reconstruct the exact point and
address tested. Reporting a PC/address/value for either transition would therefore be an
inference, contrary to the task's stop rule.

No production file, map cell, collision cell, graphics path, or ROM was changed.

## Last proven player-floor boundary

Canonical Ghidra exports establish the original general floor-probe contract, but not its dynamic
values at the missing transition:

1. `player_ground_contact_probe_family_53b34` begins at arcade PC `0x053B34`.
2. The first beneath-player probe is prepared at `0x053B5A..0x053B68`:
   - `D1 = word(A5+0x10BE)` (player X);
   - `D2 = word(A5+0x10C0) + word(A5+0x1130) + D6` (player Y plus foot extent plus the pending
     vertical displacement).
3. `0x053B6A` calls the shared ring lookup at `0x053A2E`.
4. `0x053B6E` reads the collision word from `(A0)` and `0x053B70` masks it with `0x007F`.
5. The family classifies low-seven-bit terrain codes `1`, `3`, `4`, `7`, `6`, `8`, and `0x7E`;
   the ordinary code-`1` branch sets the retained contact state through `0x053DC8` and sets the
   applicable probe bit in `A5+0x1132`. The later left/right foot probes repeat the same lookup
   contract with X adjusted by `A5+0x112E`.

The exact Genesis reader is retained arcade code. Build 0373 maps the shared lookup entry
`0x053A2E` to runtime Genesis PC `0x053B4A`; the only relevant production change in the lookup is
the accepted collision-buffer base relocation from arcade WRAM `0x0010DE00` to Genesis WRAM
`0x00FF1E00`. Static inspection therefore does not supply a reader-code divergence.

The `collision_probe_row/col/word` columns in the human TSVs are explicitly **not** the floor
probe. The scripts evaluated `0x053A2E` with raw player X/Y only. They did not apply
`A5+0x1130 + D6` or the left/right X extent. Those columns cannot be relabeled as the requested
floor read.

## What remains unproven

The evidence does not establish:

- the arcade instruction/frame on which downward movement is stopped;
- the arcade `D1`, `D2`, `D6`, `A0`, collision word, or resulting Y at that instruction;
- the Genesis instruction/frame at the same world height;
- the equivalent Genesis `D1`, `D2`, `D6`, `A0`, word, and classifier result;
- the first dynamic value that differs between those two events.

Because that first difference is absent, no exact root cause and no one-cause patch are proven.
The 32-pixel separation is measured outcome evidence, not proof of which floor input caused it.

## Visual symptom

The same cause does **not** yet obviously explain the missing graphics. No collision failure was
proven, and the existing captures do not establish a common first failing producer/publication
boundary for the visual and player-floor paths. The visual problem remains outside this stopped
task.

## Tool and architecture record

Existing project tools reused:

- canonical Ghidra exports under `analysis/ghidra/rastan_arcade/exports/`;
- `build/maincpu.disasm.txt` and `build/rastan-direct/address_map.json`;
- `tools/mame/scripts/rastan_arcade_rope_ledge_human_trace.lua`;
- `tools/mame/scripts/rastan_genesis_rope_ledge_human_trace.lua`;
- completed ORIGINAL ARCADE and GENESIS NTSC Build-0373 human trace directories.

New tooling created: **None**.

Why new tooling was necessary: **Not applicable**. The task required a proven first divergence;
the established captures do not contain the two transition events, so the explicit stop rule was
followed instead of creating another route or guessing.

The semantic architecture is unchanged: retained arcade player physics and collision consumers
continue to read the relocated native collision grid. No manual collision, manual graphics,
shadow, fallback, NOP, RTS bypass, or special case was introduced.

## Disposition

- FIRST difference: **NOT PROVEN**
- Root cause: **NOT PROVEN**
- Fix: **NONE**
- Does the same cause explain the missing graphics: **NOT PROVEN**
- Build 0374: **NOT BUILT**
- SHA-256: **Not applicable**

