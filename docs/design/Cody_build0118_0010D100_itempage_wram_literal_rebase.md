# Cody - Build 0118 0x10D100/0x10D104 Item-Page Work-RAM Literal Rebase

**Date:** 2026-06-29  
**Type:** Implementation + build + validation  
**Build:** 0118  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0118.bin`  
**SHA256:** `aa88da2f35e45974caf61059b4af82ff1c06622e8e011386e1c73d8e1d92fc5f`  
**Scope:** Apply Andy's selected bounded KF-036 design for the four static `0x0010D100/0x0010D104` work-RAM literal operands in the item-page descriptor cluster. No source assembly changes. No helper/hook. No systemic ROM-wide raw-literal pass. No KF-038/bg_fill/sprites/HUD/Window/gameplay work. No bookmark cycle.

## Phase 0

Classification: **EXTENDING** KF-036 / OPEN-016 item-page descriptor work. Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md` context, `docs/design/Cody_build0117_post_descriptor_relocation_crash_evidence.md`, and `docs/design/Andy_0010D100_itempage_descriptor_cluster_crash_design.md`.

STOP conditions were not triggered before implementation. The four requested sites were verified in the Build 0117/0118 pre-patch image with exact bytes and exact code mapping through `build/rastan-direct/address_map.json`.

## Address-Mapping Discipline

Code-address mapping used `build/rastan-direct/address_map.json` authority:

| runtime_genesis_pc | arcade_pc | segment kind |
|---|---|---|
| `0x00055E34` | `0x00055C34` | `patched_site` after build |
| `0x00055E3A` | `0x00055C3A` | `patched_site` after build |
| `0x00055E62` | `0x00055C62` | `patched_site` after build |
| `0x00055E68` | `0x00055C68` | `patched_site` after build |

The RAM mapping follows KF-036 work-RAM mapping, not `address_map.json`:

- arcade-RAM `0x0010C000` -> Genesis-WRAM `0x00FF0000`
- arcade-RAM `0x0010D100` -> Genesis-WRAM `0x00FF1100`
- arcade-RAM `0x0010D104` -> Genesis-WRAM `0x00FF1104`

## Implementation

Added exactly four byte-neutral `opcode_replace` entries to `specs/rastan_direct_remap.json`:

| runtime_genesis_pc | arcade_pc | before | after | meaning |
|---|---|---|---|---|
| `0x00055E34` | `0x00055C34` | `227C0010D100` | `227C00FF1100` | populator output slot `0x0010D100 -> 0x00FF1100` |
| `0x00055E3A` | `0x00055C3A` | `247C0010D104` | `247C00FF1104` | populator output slot `0x0010D104 -> 0x00FF1104` |
| `0x00055E62` | `0x00055C62` | `227C0010D104` | `227C00FF1104` | consumer first-word slot `0x0010D104 -> 0x00FF1104` |
| `0x00055E68` | `0x00055C68` | `267C0010D100` | `267C00FF1100` | consumer pointer slot `0x0010D100 -> 0x00FF1100` |

Canonical invariant updates:

- `opcode_replace` count: `129 -> 133`
- `total_genesis_bytes_covered`: unchanged at `0x17CF68`

Files intentionally edited for implementation:

- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

No source assembly was edited.

## Build Verification

Command run:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Canonical gate: `GATE_PASS`
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0118.bin`
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `aa88da2f35e45974caf61059b4af82ff1c06622e8e011386e1c73d8e1d92fc5f`
- Numbered vs rolling `cmp`: `0` / byte-identical
- Release trace artifact: `states/traces/rastan_direct_video_test_build_0118_mame_30s_20260629_202524/`

Generated disassembly confirms:

```asm
55e34: 227c 00ff 1100  moveal #16716032,%a1
55e3a: 247c 00ff 1104  moveal #16716036,%a2
...
55e62: 227c 00ff 1104  moveal #16716036,%a1
55e68: 267c 00ff 1100  moveal #16716032,%a3
55e6e: 2453            moveal %a3@,%a2
```

ROM byte verification:

- `0x055E34`: `227C00FF1100`
- `0x055E3A`: `247C00FF1104`
- `0x055E62`: `227C00FF1104`
- `0x055E68`: `267C00FF1100`

Manifest verification:

- `patch_counts.opcode_replace_and_rom_opcode_replace = 133`
- `postpatch_expected_opcode_replace_sites = 133`
- `postpatch_expected_total_genesis_bytes_covered = 0x17CF68`
- Four new `address_rewrites` entries exist at arcade PCs `0x055C34`, `0x055C3A`, `0x055C62`, `0x055C68`.

Build 0117 -> Build 0118 ROM diff is scoped to the checksum plus the four expected operand changes:

| Offset(s) | Meaning |
|---|---|
| `0x00018E..0x00018F` | ROM checksum `0x4957 -> 0x4D13` |
| `0x055E37..0x055E38` | operand `0x10D1 -> 0xFF11` at `0x55E34` |
| `0x055E3D..0x055E3E` | operand `0x10D1 -> 0xFF11` at `0x55E3A` |
| `0x055E65..0x055E66` | operand `0x10D1 -> 0xFF11` at `0x55E62` |
| `0x055E6B..0x055E6C` | operand `0x10D1 -> 0xFF11` at `0x55E68` |

## Runtime Validation

Read-only MAME debugger evidence was captured with no diagnostic ROM changes and no bookmark cycle.

Evidence directories:

- `states/traces/build_0118_0010d100_itempage_wram_literal_rebase_20260629_202633/`
- `states/traces/build_0118_0010d100_itempage_wram_literal_rebase_halt_20260629_202736/`

### Descriptor Hook Still Held

`states/traces/build_0118_0010d100_itempage_wram_literal_rebase_20260629_202633/wram_ff1000_after_descriptor_hook.bin` confirms the Build 0117 descriptor hook output remains intact:

```text
FF1040: 0000 22FC ... 0000 2248 ...
FF1080: 0003 0003 ...
```

### Rebased Slots Are Used

At `runtime_genesis_pc 0x00055E6E` and before the old faulting read, the slot window is:

```text
FF10F0: 0000 0000 0000 0000 00C0 0000 0003 951C
FF1100: 2048 0013 0013 0000 0000 0000 0000 0000
```

Observable facts:

- `0x00FF10FC = 0x0003951C` (walker source)
- `0x00FF1100 = 0x20480013` (pointer slot now read from WRAM, not raw ROM `0x0010D100`)
- `0x00FF1104 = 0x0013` (first-word slot now read from WRAM, not raw ROM `0x0010D104`)
- The old Build 0117 garbage pointer `0x22113111` is gone.

### Crash Boundary After Literal Rebase

The old raw-literal failure mode is removed, but validation reaches Andy's anticipated **Case B**: the slot is now real WRAM, yet the pointer field stored into it is still invalid/odd for the consumer.

Authoritative crash record at halt:

```text
CRASH_STACKED_SR       = 0x2704
CRASH_STACKED_PC       = runtime_genesis_pc 0x00055E90
CRASH_FAULT_ADDRESS    = 0x20480013
IR                     = 0x3016
```

`IR=0x3016` identifies the faulting instruction as:

```asm
runtime_genesis_pc 0x00055E8E: movew %a6@,%d0
```

The stacked PC `0x00055E90` is the next instruction, consistent with the same group-0 frame convention observed in Build 0117. State at halt remains item-page state:

```text
WRAM 0xFF0000/0002/0004 = 0x0002 / 0x0002 / 0x0004
```

## Outcome

The bounded Build 0118 implementation succeeds at its stated objective:

- The four raw `0x0010D100/0x0010D104` literal operands are rebased to `0x00FF1100/0x00FF1104`.
- The consumer now reads the populated WRAM slots, not ROM garbage at raw arcade RAM addresses.
- The previous Build 0117 fault address `0x22113111` is eliminated.

The validation gate exposes the expected follow-up:

- `0x00FF1100` is populated with `0x20480013` from the descriptor field at source `0x0003951C` (`ROM bytes: 0013 2048 0013 2048 ...`).
- The consumer dereferences that odd value and faults at the same copied instruction `0x55E8E`.
- This is **not** a reason to broaden this task retroactively. It is the separate pointer-field correctness problem Andy explicitly gated as a follow-up if the slot contained a raw/invalid value.

## Non-Actions

- No source assembly changes.
- No helper or hook added.
- No broad KF-036 ROM-wide literal pass.
- No KF-038/bg_fill work.
- No sprite/HUD/Window/gameplay work.
- No bookmark cycle.
- No issue opened or closed.
- No `KNOWN_FINDINGS.md` edit.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-016 / KF-028: context only; not closed.
- KF-036: extended with a confirmed next-page raw work-RAM literal instance fixed in Build 0118.
- OPEN-001 / OPEN-022 / OPEN-024: context only.
- OPEN-015: crash-handler caution respected; debugger/WRAM record used.
- KNOWN_FINDINGS impact: Option A for this task; no canonical edit performed.

## STOP

STOP triggered: **NO** for the implementation/build task.

A follow-up task is required for the newly exposed `0x20480013` pointer-field correctness failure. This task deliberately stops at the authorized four-site literal rebase.
