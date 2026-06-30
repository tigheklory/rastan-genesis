# Cody - Build 0120 Item-Page BG Strip Producer Route

**Date:** 2026-06-30  
**Type:** Implementation + build + static verification; runtime validation attempted but target path not exercised  
**Build:** 0120  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`  
**SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`  
**Scope:** Route the item-page 64-cell BG strip producer through existing Genesis BG staging via `genesistan_hook_tilemap_bg_fill`. No KF-038 scroll/staging-size work, no `bg_fill` rewrite, no PC080SN render-loop rewrite, no sprites/HUD/Window/gameplay work, no systemic ROM-wide KF-036 pass, no diagnostic ROM, no bookmark cycle.

## Phase 0

Read and applied:

- `RULES.md`
- `ARCHITECTURE.md`
- latest relevant `AGENTS_LOG.md`
- `docs/design/Cody_post_itemscroll_runaway_fill_hv_counter_evidence.md`
- `docs/design/Cody_build0119_itempage_strip_populator_pointer_relocation.md`
- `docs/design/Andy_build0119_itempage_strip_destination_hv_write_design.md`
- task prompt `[Cody - Build 0120 Item-Page BG Strip Producer Route - Implementation]`

Classification: **EXTENDING** KF-032 / OPEN-022 producer-route family, with KF-028/OPEN-016 and KF-036 predecessor layers treated as fixed context. OPEN-001 context. OPEN-015 context for runtime crash-record discipline. No contradiction detected.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. The change is a production opcode replacement at a copied arcade producer entry that redirects raw PC080SN BG C-window writes through an existing Genesis helper/staging path. No fake data, skip, bypass, broad runtime mirror, address masking, or diagnostic scaffolding was added.

## Implementation

Added `genesistan_hook_itempage_strip_blit` in `apps/rastan-direct/src/tilemap_hooks.s`.

The hook reads the existing Build 0119 source-side outputs and destination cursor:

- `Genesis-WRAM 0x00FF10F8`: item-page BG destination cursor, arcade-native PC080SN BG C-window address.
- `Genesis-WRAM 0x00FF1100`: relocated strip source pointer, expected `0x0000D31C` for the proven case.
- `Genesis-WRAM 0x00FF1104`: attr/header word, expected `0x0002` for the proven case.
- `Genesis-WRAM 0x00FF10F6`: column word.

Loop behavior:

```asm
for d2 = 0..63:
    d7 = d2 * 32 + col * 2
    code = word at (strip_base + d7)
    D0 = (attr << 16) | code
    A0 = current PC080SN BG C-window destination
    D1 = 1
    bsr genesistan_hook_tilemap_bg_fill
    dest += 0x100
write dest back to 0x00FF10F8
rts
```

This preserves the arcade-native destination cursor model and lets `genesistan_hook_tilemap_bg_fill` perform the sanctioned PC080SN BG C-window-to-`staged_bg_buffer` decode. It does **not** replace the cursor with a raw staging-buffer pointer and does **not** raw-write to `HW_ADDRESS 0x00C00000..0x00C03FFF`.

Register discipline: the hook uses `d0/d1/d2/d7/a0/a1/a2/a3` as scratch/loop state and saves/restores caller `%d1` around the full helper. The called `genesistan_hook_tilemap_bg_fill` preserves registers with its own `movem` convention, so loop state survives each call.

## Patch Shape

Required clean 10-byte entry patch applied at `runtime_genesis_pc 0x00055E5E` / `arcade_pc 0x00055C5E`:

- Build 0119 runtime bytes: `206D10F8 227C00FF1104`
- Spec original bytes after removing overlapped inner rebase: `206D10F8 227C0010D104`
- Build 0120 runtime bytes: `4EF90007163C 4E71 4E71`

Disassembly:

```asm
55e5e: 4ef9 0007 163c  jmp 0x7163c
55e64: 4e71            nop
55e66: 4e71            nop
```

Hook address:

```text
0007163c T genesistan_hook_itempage_strip_blit
```

Hook disassembly excerpt:

```asm
7163c: 2f01                 movel %d1,%sp@-
7163e: 267c 00ff 10f8      moveal #0xff10f8,%a3
71644: 2053                 moveal %a3@,%a0
71646: 267c 00ff 1100      moveal #0xff1100,%a3
7164c: 2453                 moveal %a3@,%a2
7164e: 227c 00ff 1104      moveal #0xff1104,%a1
71654: 3e11                 movew %a1@,%d7
71656: 4847                 swap %d7
71658: 4247                 clrw %d7
7165a: 4242                 clrw %d2
7165c: 3202                 movew %d2,%d1
7165e: eb49                 lslw #5,%d1
71660: 3039 00ff 10f6      movew 0xff10f6,%d0
71666: e348                 lslw #1,%d0
71668: d240                 addw %d0,%d1
7166a: 4280                 clrl %d0
7166c: 3032 1000            movew %a2@(0,%d1:w),%d0
71670: 8087                 orl %d7,%d0
71672: 7201                 moveq #1,%d1
71674: 6100 ef12            bsrw 0x70588
71678: d1fc 0000 0100      addal #256,%a0
7167e: 5242                 addqw #1,%d2
71680: 0c42 0040            cmpiw #64,%d2
71684: 66d6                 bnes 0x7165c
71686: 267c 00ff 10f8      moveal #0xff10f8,%a3
7168c: 2688                 movel %a0,%a3@
7168e: 221f                 movel %sp@+,%d1
71690: 4e75                 rts
```

## Overlap Handling / Invariants

Existing Build 0119 had an inner opcode_replace at `arcade_pc 0x055C62` for the literal `0x0010D104 -> 0x00FF1104`. The required 10-byte entry patch covers that instruction, so the old inner site was removed to prevent overlapping patched-site segments. The new `arcade_pc 0x055C5E` entry uses raw arcade original bytes and supersedes the old inner rebase.

Resulting mechanical delta:

- `opcode_replace` patched-site count: `133 -> 133` (add `0x055C5E`, remove covered `0x055C62`)
- `total_genesis_bytes_covered`: `0x17CFC0 -> 0x17D018` (`+0x58`)
- hook symbol code span: `0x7163C..0x71691` (`0x56` bytes), with ROM/coverage growth matching the postpatch gate's observed mechanical result
- canonical invariant constants updated to `133 / 0x17D018`

Manifest verification:

```text
patch_counts: opcode_replace_and_rom_opcode_replace = 133
postpatch_expected_opcode_replace_sites = 133
postpatch_expected_total_genesis_bytes_covered = 0x17D018
bookmarks_v2_count = 0
bookmarks_v2_applied = []
```

The manifest contains `arcade_pc 0x055C5E` and no `arcade_pc 0x055C62` entry.

## Build Verification

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

Outputs:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
- `cmp` numbered vs rolling: `0` (byte-identical)
- Standard release trace: `states/traces/rastan_direct_video_test_build_0120_mame_30s_20260630_103650/`
- Boot guard: PASS
- Canonical gate: `GATE_PASS`

ROM size comparison:

- Build 0119: `1560512` bytes
- Build 0120: `1560600` bytes
- delta: `+88` bytes (`+0x58`)

## Dead-Body Reachability

Static scan of generated disassembly for references into now-dead body `runtime_genesis_pc 0x00055E68..0x00055EA0` found only internal references from within that dead body:

```text
55e70: bsrw 0x55e7a
55e9e: bnes 0x55e7c
```

External references into `0x55E68..0x55EA0`: **0**.

## Static Producer Equivalence

For the proven Build 0119 source-side case:

- `Genesis-WRAM 0x00FF1100 = 0x0000D31C`
- `Genesis-WRAM 0x00FF1104 = 0x0002`
- `Genesis-WRAM 0x00FF10F8 = 0x00C00008`
- `Genesis-WRAM 0x00FF10F6 = 0x0002`

The static first routed cell for column 2 is:

- `A0 = 0x00C00008`
- source code word = `word(0x0000D31C + 0x0002 * 2) = word(0x0000D320) = 0x04A8`
- `D0 = 0x000204A8`
- `D1 = 1`

All static destinations produced by the loop are:

```text
0x00C00008, 0x00C00108, 0x00C00208, ..., 0x00C03F08
```

These are 64 PC080SN BG C-window destinations, all in `[0x00C00000, 0x00C04000)`, so they are in-window for `genesistan_hook_tilemap_bg_fill`. The final cursor writeback is `0x00C04008`; it is only stored back to `Genesis-WRAM 0x00FF10F8`, not passed to `bg_fill`.

## Runtime Validation Attempt

Trace directory:

```text
states/traces/build_0120_itempage_bg_strip_route_20260630_103840/
```

Debugger script:

```text
states/traces/build_0120_itempage_bg_strip_route_20260630_103840/build0120_itempage_bg_strip_route.cmd
```

Runs attempted:

1. Direct MAME Genesis-driver run, 120 emulated seconds: no hit.
2. Direct MAME Genesis-driver run, 900 emulated seconds: no hit.
3. Project wrapper run (`tools/mame/run_genesis_trace_wsl.sh`, project `genesistrace.lua` homepath), 900 emulated seconds: no hit.
4. Control run against Build 0119 old producer entry under the same direct harness, 120 emulated seconds: no hit.

Project-wrapper 900-second summary copied to:

```text
states/traces/build_0120_itempage_bg_strip_route_20260630_103840/genesis_exec_summary_wrapper_900s.txt
states/traces/build_0120_itempage_bg_strip_route_20260630_103840/genesis_exec_trace_wrapper_900s.log
```

The wrapper run completed by time limit:

```text
frames=53931
fg_cwindow_live count=0
vdp_ports_live count=630320 first_frame=0 last_frame=12867 ...
```

No scripted stop condition fired:

- `genesistan_hook_itempage_strip_blit` was not reached.
- raw `HW_ADDRESS 0x00C00008` watchpoint did not fire.
- crash-common breakpoint did not fire.
- no hook-entry/return dumps were produced.

### Runtime Validation Status

Runtime item-page proof is **not complete** in this task because the available no-input MAME validation did not exercise the item-page strip producer path. Therefore the following are **statically verified but not runtime-hit** here:

- first routed `bg_fill` call (`A0=0x00C00008`, `D0=0x000204A8`, `D1=1`)
- 64 `bg_fill` calls
- 64 in-window destinations at runtime
- `staged_bg_buffer` row/column writes at runtime
- `bg_row_dirty` update from this producer at runtime
- `0x00FF10F8` cursor writeback at runtime

Observed in the long wrapper run:

- no raw `0x00C00008` write hit
- no crash hit
- no FG C-window live write hit

This should be read narrowly: the validation path did **not** reach the producer. It is not evidence that the producer route is unnecessary, nor a runtime proof that all 64 calls occurred. No memory seeding, synthetic state forcing, fake data, or diagnostic ROM was used.

## Prior Outputs / Regression Notes

Build 0119 source-side hook outputs are preserved structurally: the new hook reads the same `0x00FF1100` and `0x00FF1104` slots produced by `genesistan_hook_itempage_strip_populate`, and the Build 0120 manifest retains the predecessor opcode replacements at the populator sites except for the intentionally superseded overlapped consumer inner site.

The standard release MAME smoke run completed and the project-wrapper 900-second run completed without crash. No title/story/high-score regression was observed in these automated no-input smoke runs, but this is not a full visual or input regression pass.

BlastEm/Nomad strict status for the item-page producer remains **UNKNOWN / not exercised** in this task. The MAME watchpoint did not see the old raw `0x00C00008` write in the available no-input window, but the item-page producer itself was not reached, so this is not a strict-emulator proof for that producer.

## Classification

Implementation side: **PASS** for the required production route shape, canonical build, patch bytes, overlap handling, and static equivalence.

Runtime validation side: **STOP-limited / not fully proven** because the no-input MAME paths did not reach the item-page strip producer. The next evidence step, if required before closing this slice, should use a reproducible input/runtime harness that reaches the item-page `2/2/4` producer path without memory seeding or fake state, then rerun the existing debugger script to collect the 64-call `bg_fill` proof and strict raw-write absence.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-022 / KF-032: progressed with implementation of the item-page BG strip producer route.
- KF-028 / OPEN-016: predecessor source-side relocation remains context.
- KF-036: predecessor mapped-WRAM slot lesson remains context.
- OPEN-001: context only.
- OPEN-015: context only; no formatted exception screen values used.
- KF-038 item-scroll/staging-size remains intentionally deferred.
- `KNOWN_FINDINGS.md`: not edited.
- Issues opened/closed: none.

## Non-Actions

No KF-038 item-scroll/staging-size fix, no `bg_fill` rewrite, no PC080SN render-loop rewrite, no sprites/HUD/Window/gameplay changes, no systemic ROM-wide KF-036 pass, no fake data, no skip/bypass, no broad runtime mirror, no address masking/write suppression, no diagnostic scaffolding, and no bookmark cycle.

## STOP

STOP status: **YES (validation-limited)**. The implementation/build/static verification completed, but the required runtime item-page 64-cell route proof could not be captured because the producer path was not reached in the available no-input MAME validation windows.
