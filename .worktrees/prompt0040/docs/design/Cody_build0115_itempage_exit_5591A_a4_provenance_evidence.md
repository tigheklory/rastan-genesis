# Cody - Build 0115 Item-Page Exit / 0x5591A A4 Provenance Evidence

**Date:** 2026-06-29
**Type:** Runtime evidence + static provenance, evidence only
**Build:** Build 0115, `dist/rastan-direct/rastan_direct_video_test_build_0115.bin`
**Build SHA256:** `5af34e440a79f2d9d447a767592ea903d026edea3f174a97d446b03ed23026e3`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark cycle. No implementation. No skip/transition patch.

Address labels:
- `runtime_genesis_pc` / `genesis_rom_offset`: Genesis runtime PC and ROM offset (KF-004)
- `arcade_pc`: original arcade code address
- `HW_ADDRESS`: arcade/Genesis hardware address space
- `WRAM`: Genesis work RAM

All arcade-to-Genesis code correlations below use `build/rastan-direct/address_map.json`; no raw `+0x200` arithmetic is used as proof.

## Phase 0 - Baseline

Relevant priors loaded: KF-036 (mapped work-RAM base lesson), KF-038 (long PC080SN BG C-window rows alias in current 32-row Genesis BG staging), KF-032 (PC080SN raw writes should route through staging), KF-010 (BG/FG staging and VDP commit), and OPEN-015 (crash screen numeric fields unreliable; use WRAM crash record/debugger-side evidence).

Open issues touched: OPEN-001, OPEN-022, OPEN-023, OPEN-024, OPEN-015 context only. No issue was opened or closed.

Classification: **EXTENDING** Build 0115 item-page crash evidence. No contradiction detected.

## Evidence Artifacts

Original arcade runtime trace:

- `states/traces/original_arcade_itempage_exit_5591a_20260629_142000/original_arcade_5591a.cmd`
- `states/traces/original_arcade_itempage_exit_5591a_20260629_142000/native_debug_trace.log`
- `states/traces/original_arcade_itempage_exit_5591a_20260629_142000/native_events.log`
- `states/traces/original_arcade_itempage_exit_5591a_20260629_142000/arcade_ram_10c000_item.bin`
- `states/traces/original_arcade_itempage_exit_5591a_20260629_142000/arcade_table_10d000_item.bin`

The MAME run exited via debugger after the targeted item-state rebuild evidence was captured. The wrapper timeout returned nonzero, but the debugger exit and trace artifacts are valid evidence.

Build 0115 crash evidence source:

- Prior WRAM crash-record evidence from `docs/design/Cody_build0115_itemdesc_crash_scroll_evidence.md`
- Prior gameplay/demo evidence limitation from `docs/design/Cody_build0115_gameplay_demo_crash_pc080sn_evidence.md`
- Static disassembly in `build/maincpu.disasm.txt` and `build/genesis_postpatch.disasm.txt`
- Address authority: `build/rastan-direct/address_map.json`

## Address Mapping Discipline

`build/rastan-direct/address_map.json` maps the relevant copied arcade segment as:

```json
{
  "genesis_start": "0x054A64",
  "genesis_end_exclusive": "0x055B68",
  "kind": "arcade_copy",
  "arcade_start": "0x054864",
  "arcade_end_exclusive": "0x055968",
  "identity_offset": 512
}
```

Exact mapped PCs used:

| runtime_genesis_pc | arcade_pc | Evidence |
|---|---|---|
| `0x00055AC6` | `0x000558C6` | table source-pointer advance routine |
| `0x00055AE0` | `0x000558E0` | phase/counter advance routine |
| `0x00055B04` | `0x00055904` | 16-entry rebuild routine entry |
| `0x00055B18` | `0x00055918` | `moveal %a0@,%a4` source pointer load |
| `0x00055B1A` | `0x0005591A` | `movew %a4@,%a2@+` faulting/copy instruction |
| `0x00055B22` | `0x00055922` | pointer-rebase base immediate |
| `0x00055B2C` | `0x0005592C` | stores rebuilt pointer to table |

Critical address-space result: `0x0010D000`, `0x0010D040`, `0x0010D080`, and `0x0010D0A8` are **not Genesis WRAM in Build 0115**. `address_map.json` places them in the Genesis-only wrapper/ROM segment:

```json
{
  "genesis_start": "0x070000",
  "genesis_end_exclusive": "0x17CF08",
  "kind": "genesis_only",
  "tag": "wrapper"
}
```

So copied arcade code that reads/writes raw `0x0010Dxxx` addresses is not accessing a mapped work-RAM table in Build 0115.

## Part 1 - Original Arcade Behavior

Original arcade executes the corresponding routine at `arcade_pc 0x00055904` and the copy instruction at `arcade_pc 0x0005591A` during item-page state `%a5@(0)=2`, `%a5@(2)=2`, `%a5@(4)=4`.

Static arcade routine at `arcade_pc 0x00055904`:

```asm
55904: 207c 0010 d000  moveal #0x0010d000,%a0
5590a: 227c 0010 d040  moveal #0x0010d040,%a1
55910: 247c 0010 d080  moveal #0x0010d080,%a2
55916: 7010            moveq #16,%d0
55918: 2850            moveal %a0@,%a4
5591a: 34d4            movew %a4@,%a2@+
5591c: 4281            clrl %d1
5591e: 322c 0002       movew %a4@(2),%d1
55922: 287c 0000 0000  moveal #0,%a4
55928: 49f4 1800       lea %a4@(0,%d1:l),%a4
5592c: 22cc            movel %a4,%a1@+
5592e: d1fc 0000 0004  addal #4,%a0
55934: 5340            subqw #1,%d0
55936: 66e0            bnes 0x55918
55938: 286d 10c6       moveal %a5@(4294),%a4
5593c: 4240            clrw %d0
5593e: 1014            moveb %a4@,%d0
55940: 33c0 0010 d0a8  movew %d0,0x0010d0a8
55946: 4e75            rts
```

Original arcade runtime evidence from the breakpoint at `arcade_pc 0x0005591A` shows all 16 loop iterations read valid source pointers from `arcade-RAM 0x0010D000..0x0010D03F`:

| Index | Source pointer from `0x10D000+` | Rebuilt pointer word | Copied word |
|---:|---|---|---|
| 0 | `0x0001691C` | `0x000020FC` | `0x0003` |
| 1 | `0x00018BDC` | `0x000020FC` | `0x0003` |
| 2 | `0x0001AE9C` | `0x000020FC` | `0x0003` |
| 3 | `0x0001D15C` | `0x000020FC` | `0x0003` |
| 4 | `0x0001F41C` | `0x000020FC` | `0x0003` |
| 5 | `0x000216DC` | `0x000020FC` | `0x0003` |
| 6 | `0x0002399C` | `0x000020FC` | `0x0003` |
| 7 | `0x00025C5C` | `0x000020FC` | `0x0003` |
| 8 | `0x00027F1C` | `0x000020FC` | `0x0003` |
| 9 | `0x0002A1DC` | `0x000020FC` | `0x0003` |
| 10 | `0x0002C49C` | `0x00002048` | `0x0003` |
| 11 | `0x0002E75C` | `0x00002048` | `0x0003` |
| 12 | `0x00030A1C` | `0x00002048` | `0x0003` |
| 13 | `0x00032CDC` | `0x00002048` | `0x0003` |
| 14 | `0x00034F9C` | `0x00002048` | `0x0003` |
| 15 | `0x0003725C` | `0x00002048` | `0x0003` |

Representative original arcade event:

```text
EVENT ARCADE_COPY_5591A_ITEM ... d0=00000010 a0=0010D000 a1=0010D040 a2=0010D080 a4=0001691C a4_word=0003 a4_plus2=20FC ...
```

The table dump at `states/traces/original_arcade_itempage_exit_5591a_20260629_142000/arcade_table_10d000_item.bin` confirms the original arcade's live table state:

```text
10D000: 0001 691C 0001 8BDC ... 0003 725C
10D040: 0000 20FC ... 0000 2048
10D080: 0003 0003 ... 0003
```

Original source descriptor bytes at the first and later source pointers begin with the copied word plus the pointer word:

```text
arcade maincpu 0x1691C: 00 03 20 FC ...
arcade maincpu 0x18BDC: 00 03 20 FC ...
arcade maincpu 0x2C49C: 00 03 20 48 ...
arcade maincpu 0x3725C: 00 03 20 48 ...
```

Interpretation from original arcade runtime: `arcade_pc 0x00055904` rebuilds a 16-entry PC080SN descriptor/list table. It copies the first descriptor word to `arcade-RAM 0x0010D080+` and converts the second descriptor word into a long pointer stored at `arcade-RAM 0x0010D040+`.

## Part 2 - Build 0115 Genesis Divergence

The copied Build 0115 routine is structurally the same except the pointer-rebase base immediate has been changed from `#0` to `#0x200`:

```asm
55b04: 207c 0010 d000  moveal #0x0010d000,%a0
55b0a: 227c 0010 d040  moveal #0x0010d040,%a1
55b10: 247c 0010 d080  moveal #0x0010d080,%a2
55b16: 7010            moveq #16,%d0
55b18: 2850            moveal %a0@,%a4
55b1a: 34d4            movew %a4@,%a2@+
55b1c: 4281            clrl %d1
55b1e: 322c 0002       movew %a4@(2),%d1
55b22: 287c 0000 0200  moveal #512,%a4
55b28: 49f4 1800       lea %a4@(0,%d1:l),%a4
55b2c: 22cc            movel %a4,%a1@+
```

Build 0115 crash record from prior evidence:

- `runtime_genesis_pc 0x00055B1A`: `movew %a4@,%a2@+`
- Stacked PC: `runtime_genesis_pc 0x00055B1C`
- Fault address: `0x0000000F`
- `%a4 = 0x0000000F`
- `%a2 = 0x0010D080`
- State: `%a5@(0)=0x0002`, `%a5@(2)=0x0002`, `%a5@(4)=0x0004`, `%a5@(44)=0x0000`

Proven `%a4` chain:

1. `runtime_genesis_pc 0x00055B04` loads `%a0 = 0x0010D000`.
2. `runtime_genesis_pc 0x00055B18` executes `moveal %a0@,%a4`.
3. In Build 0115, `0x0010D000` is not mapped work RAM; it is in the `genesis_only wrapper` ROM segment.
4. ROM bytes at `genesis_rom_offset 0x0010D000` begin `00 00 00 0F`, so the copied arcade load produces `%a4 = 0x0000000F`.
5. `runtime_genesis_pc 0x00055B1A` attempts `movew %a4@,%a2@+`, causing an odd-address source read from `0x0000000F`.

Build 0115 bytes at the raw table addresses:

```text
0x0010D000: 00 00 00 0F 00 00 00 0D 00 00 00 0D 00 00 00 C2 ...
0x0010D040: 22 21 31 11 55 53 B5 5B ...
0x0010D080: 00 00 0F 54 00 00 0D 53 ...
0x0010D0A8: 55 31 B3 33 00 00 B2 22 ...
```

These are ROM/wrapper bytes, not live table state. The crash is therefore not random uninitialized WRAM; it is copied arcade code using raw arcade RAM addresses that currently land in Genesis ROM/wrapper space.

Proven `%a2` chain:

- `runtime_genesis_pc 0x00055B10` loads `%a2 = 0x0010D080` directly.
- In the original arcade, this is an arcade work-RAM output table address.
- In Build 0115, `address_map.json` says this address is Genesis wrapper/ROM space, not WRAM.
- The fault happens on the source read before the destination write completes, but the destination is also unmapped for this routine's intended table model.

Upstream table-update routine:

```asm
55ac6: 7010            moveq #16,%d0
55ac8: 207c 0010 d000  moveal #0x0010d000,%a0
55ace: 5890            addql #4,%a0@
55ad0: d1fc 0000 0004  addal #4,%a0
55ad6: 5340            subqw #1,%d0
55ad8: 66f4            bnes 0x55ace
55ada: 426d 10ca       clrw %a5@(4298)
55ade: 4e75            rts
```

This confirms the copied Genesis path still expects the raw `0x0010D000` table to be mutable RAM. It is not.

## Part 3 - State-Machine Target / Skip Safety

Original arcade state timeline shows the routine runs in item-description cleanup/rebuild state, not after a proven gameplay/demo transition:

```text
s0=0002, s2=0002, s4=0004 at arcade_pc 0x00055904 / 0x0005591A
```

The trace captured the item-state rebuild and then stopped. It does **not** prove the next clean gameplay/demo state target or a safe transition PC to skip to.

Therefore:

- Proven: the Build 0115 crash occurs before a gameplay/demo transition is established in evidence.
- Proven: original arcade completes the same `0x55904` rebuild in the same item-page state with valid table pointers.
- Not proven: a safe future diagnostic skip target after this routine.
- Not safe: skipping `runtime_genesis_pc 0x00055B04..0x00055B46` as a workaround. The routine creates descriptor/list state; bypassing it would skip state creation and violate the state-causality rule.

## Part 4 - Separable vs KF-038 Entangled

Verdict: **Separable pointer/table mapping bug.**

This crash is not caused by KF-038 row aliasing.

Why:

- KF-038 concerns BG staging geometry: later `HW_ADDRESS 0x00C03428` aliases onto earlier `HW_ADDRESS 0x00C01428` in the current 32-row Genesis BG staging buffer.
- The `runtime_genesis_pc 0x00055B1A` crash occurs before any such row-alias decision matters; the CPU dereferences `%a4=0x0000000F` because the source pointer table at raw `0x0010D000` was read from Genesis wrapper/ROM bytes instead of arcade work RAM.
- Original arcade proves the same routine's intended input table contains valid ROM pointers (`0x0001691C..0x0003725C`) and the routine completes all 16 entries.
- The immediate root is a KF-036-style raw arcade work-RAM base problem: the copied routine still uses `0x0010D000/0x0010D040/0x0010D080/0x0010D0A8` instead of a mapped Genesis WRAM representation.

Caveat: the routine participates in PC080SN descriptor/list state generation, so a future fix must respect PC080SN layout semantics. But the odd-address crash itself is separable from the tall-map/scroll aliasing mechanism.

## Recommendation

No implementation was performed.

Recommended next step, if authorized later: repair or route the `0x0010D000..0x0010D0A8` arcade work-RAM table model so copied arcade code reads/writes mapped mutable state instead of Genesis wrapper/ROM bytes. Do **not** skip the routine and do **not** treat this as a text-writer/dispatcher or KF-038 row-alias symptom.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: context; item/graphics progression still blocked by a real copied-arcade table fault.
- OPEN-022/OPEN-023/OPEN-024: context only; no status changes.
- OPEN-015: context; WRAM/debugger-side crash record is the reliable crash source.
- KF-038: not contradicted; this task distinguishes a separate raw arcade work-RAM table bug from row-alias corruption.
- KF-036: reinforced by current Build 0115 evidence; no `KNOWN_FINDINGS.md` update was made in this evidence-only task.

New issues opened: none. Issues closed: none.

## STOP

STOP status: **NO** for evidence collection. The A4 provenance and original arcade intent are pinned. STOP applies only to implementation/skip placement: no safe skip target was proven, and no fix is authorized in this task.
