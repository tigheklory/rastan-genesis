# Flag / Gate Semantics (`A5+0x0100`, `A5+0x0104`)

## Purpose
Analyze launcher-owned/title-init flag semantics as control gates (not just values), including write ownership, read/test sites, and ordering constraints.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (A5+0x0104 causality analysis, startup forensics)
- `README.md`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `build/rastan/startup_common_relocations.json`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin` (cross-check from existing research traces)
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin` (cross-check from existing research traces)
- MAME reference source: `src/mame/taito/rastan.cpp`, `src/mame/taito/taitoipt.h`

## Address Mapping Note
Mapped using current `shift_replacements` deltas plus relocation `+0x200`:
- Example: `arcade_addr 0x04528C -> genesis_rom_addr 0x0454A8`.

## Findings

## `A5+0x0104` (critical gate)

### Known writes

| Writer | arcade_addr | genesis_rom_addr | Instruction / action | Behavior |
|---|---|---|---|---|
| Launcher direct init | N/A (C path) | N/A | `genesistan_arcade_workram_words[130] = 1` in `genesistan_init_workram_direct()` | Immediate early assertion before frontend tick.
| Frontend state handler | `0x03A1F2` | `0x03A3F2` | `move.b #1,(0x0104,A5)` | Runtime assertion in arcade flow.
| Frontend transition handler | `0x03A7EC` | `0x03A9F4` | `move.b #1,(0x0104,A5)` | Later runtime assertion.
| Data-region decode artifacts | `0x0001264`, `0x0001790`, `0x0002F58`, `0x0003798` | shifted equivalents | `oril ...,%a5@(260)` | Low-confidence non-executable decodes.

### Known reads/tests/gates

| Reader/test site | arcade_addr | genesis_rom_addr | Instruction | If zero | If non-zero | Downstream consequence |
|---|---|---|---|---|---|---|
| Frontend path gate #1 | `0x03A624` | `0x03A828` | `tst.b (0x0104,A5)` | Keep default branch | Enter alternate branch | Affects `A5@(0x1394)` / `A5@(0x1242)` behavior.
| Frontend path gate #2 | `0x03A714` | `0x03A91C` | `tst.b (0x0104,A5)` | executes selector-digit text path | skips selector-digit display branch | Suppresses/changes selector display behavior.
| Selector seed gate (critical) | `0x04528C` | `0x0454A8` | `tst.b (0x0104,A5)` + `bne` | writes `A5+0x0118`/`A5+0x0117` | skips those writes | Zero selector persists, enabling later underflow.
| Seed helper branch | `0x0452BA` | `0x0454D6` | `tst.b (0x0104,A5)` | branch A | branch B | Internal seed/helper behavior differs.
| Seed helper branch | `0x0452CE` | `0x0454EA` | `tst.b (0x0104,A5)` | branch A | branch B | Internal seed/helper behavior differs.

### Semantics judgment for `A5+0x0104`
- Launcher allowed to assert immediately: **NO**.
- Should launcher leave it zero initially: **YES**.
- Should arcade code own first assertion: **YES**.
- Required side effects before it becomes `1`:
  1. Selector seed routine `0x04527E` must execute with gate open.
  2. `A5+0x0118` and `A5+0x0117` must be seeded from the `0x05FF9E`-derived value.
  3. Only after seed completion should runtime transition handlers assert `A5+0x0104`.

## `A5+0x0100` (title/transition flag/counter)

### Known writes

| Writer | arcade_addr | genesis_rom_addr | Instruction / action | Behavior |
|---|---|---|---|---|
| Launcher direct init | N/A (C path) | N/A | `genesistan_arcade_workram_words[128] = 1` | Early explicit seed in launcher path.
| Frontend runtime write | `0x03A522` | `0x03A726` | `move.w %a5@(54),%a5@(256)` | Re-seeds from bonus/config-derived value.
| Frontend runtime write | `0x03AB42` | `0x03AD54` | `move.w #1,%a5@(256)` | Direct runtime set in title/transition block.
| Title init/runtime | `0x03B798` | `0x03B9AA` | `addq.w #1,%a5@(256)` | Increment-style runtime mutation.
| Gameplay-side path | `0x057800` | `0x057A16` | `move.w #1,%a5@(256)` | Additional runtime write outside pure startup.

### Known reads/uses

| Reader/use site | arcade_addr | genesis_rom_addr | Instruction | Effect |
|---|---|---|---|---|
| Counter consume | `0x03A200` | `0x03A400` | `subq.w #1,%a5@(256)` + branch | Treats field as decrementing gate/counter.
| Transition block copy use | `0x03A294`, `0x03A2A6`, `0x03A2B2`, `0x03A2C4` | `0x03A498`, `0x03A4AA`, `0x03A4B6`, `0x03A4C8` | `lea %a5@(256),...` | Uses `A5+0x0100` block as transition buffer source/destination.
| Additional transition uses | `0x03AB28`, `0x03AB3A` | `0x03AD3A`, `0x03AD4C` | `lea %a5@(256),...` | Further staging/copy semantics.

### Semantics judgment for `A5+0x0100`
- Launcher allowed to assert immediately: **CONDITIONAL / UNPROVEN**.
- Proven crash causality tied to this field: **NO** (current proven root cause is `A5+0x0104`).
- Practical constraint: this field is actively used as counter/buffer anchor very early; changing it requires paired transition-order validation.

## Uncertainties
- `A5+0x0100` exact first-value requirement under all launcher-driven entry states is not fully proven from static flow alone.
- Current spec still contains transition-cluster bypasses (`0x03A294`, `0x03A2B2`) that can distort observed behavior around `A5+0x0100` usage.

## Conclusion
- `A5+0x0104` is a strict sequencing gate and must not be asserted by launcher before `0x04527E` seed execution.
- `A5+0x0100` is an active runtime counter/buffer anchor; adjust only with explicit transition-order validation.
- The minimal safe design center is to preserve natural arcade ownership of first `A5+0x0104` assertion while retaining required non-video launcher state.
