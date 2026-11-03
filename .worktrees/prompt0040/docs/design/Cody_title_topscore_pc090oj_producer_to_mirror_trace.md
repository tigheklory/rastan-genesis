# Cody - Title Top-Score PC090OJ Producer-to-Mirror Trace

**Date:** 2026-07-02  
**Type:** Evidence / attribution only  
**Build:** 0126, `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`  
**Build SHA256:** `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`  
**Scope:** Trace original arcade title top-score PC090OJ producers and compare them with Build 0126 Genesis PC090OJ mirror/SAT state. No source/spec/tool/Makefile/ROM/build edits. No bookmark. No fix design or implementation.

Address labels used below:

- `arcade_pc`: original arcade main CPU code address.
- `runtime_genesis_pc`: Build 0126 Genesis runtime PC / ROM offset.
- `HW_ADDRESS`: arcade/Genesis hardware-visible address.
- `Genesis-WRAM`: Genesis work RAM address.

All arcade-to-Genesis code correlations in this report were resolved through `build/rastan-direct/address_map.json`. No arithmetic offset was used as proof.

## Phase 0

Classification: **EXTENDING** `OPEN-001` / `OPEN-024`.

Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md` tail, `docs/design/Cody_title_screen_arcade_vs_genesis_sprite_delta_baseline.md`, `docs/design/Cody_temp_sprite_sat_suppression_black_cover_test.md`, `docs/design/Cody_pc090oj_object_ram_phase1_implementation.md`, `docs/design/Cody_pc090oj_blank_bitset_unmapped_guard_implementation.md`, `docs/design/Cody_build0124_final_composite_black_cover_attribution.md`, and `docs/design/Andy_pc090oj_object_ram_to_genesis_sat_architecture.md`.

Relevant high-hazard/context findings: KF-011 frame ownership, KF-032 raw PC080SN/PC090OJ hardware write routing, KF-036 mapped-base discipline, and the active PC090OJ/object-RAM work in `OPEN-024`. `OPEN-015` is context only and was not touched.

Contradiction detected: **NO**. The prior title sprite-delta baseline is preserved: original arcade steady title frame contains the 27 visible top-score PC090OJ objects, while Build 0126 frame-60 final staged/true SAT contains no corresponding objects.

## Evidence Artifacts

Trace directory:

`states/traces/title_topscore_pc090oj_producer_to_mirror_trace_20260702_001702/`

Primary files:

- `arcade/arcade_pc090oj_topscore_write_trace.lua`
- `arcade/arcade_pc090oj_topscore_write_trace.log`
- `genesis_build0126/genesis_pc090oj_topscore_trace.lua`
- `genesis_build0126/genesis_pc090oj_topscore_trace.log`
- `genesis_build0126/genesis_debug_pc090oj_producer.cmd`
- `genesis_build0126/genesis_debug_pc090oj_producer_stderr.log`
- `raw_dumps/baseline_frame_060_arcade_pc090oj_d00000_0800.bin`
- `raw_dumps/baseline_frame_060_genesis_pc090oj_object_ram_ff674a.bin`
- `raw_dumps/baseline_frame_060_genesis_staged_sprite_sat_ff6104.bin`
- `raw_dumps/baseline_frame_060_genesis_staged_sprite_desc_ff6384.bin`
- `raw_dumps/baseline_frame_060_genesis_true_vdp_sat_f800.bin`
- `raw_dumps/baseline_frame_060_genesis_counts_ff6f4a.bin`
- `raw_dumps/PROVENANCE.txt`
- `decode/baseline_arcade_frame060_pc090oj_decode.csv`
- `decode/baseline_genesis_frame060_mirror_decode.csv`
- `decode/baseline_genesis_frame060_sat_decode.csv`
- `decode/reduce_title_topscore_trace.py`
- `decode/title_topscore_producer_to_mirror_summary.json`
- `decode/title_topscore_producer_to_mirror_summary.md`

The `baseline_frame_060_*` dumps were copied from `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/` with provenance recorded, so this task can compare fresh producer-write evidence against the already-captured steady title-state delta.

## Target Objects

The audited original arcade top-score PC090OJ entries are:

`4, 5, 6, 7, 8, 22, 23, 24, 25, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45`

That is **27 entries**.

Baseline frame-60 comparison from the copied prior dumps:

- Original arcade visible target entries: `27 / 27`.
- Build 0126 Genesis `pc090oj_object_ram` target entries matching arcade: `0 / 27`.
- Build 0126 Genesis mirror-visible target entries: `1 / 27`, but it is a wrong/mismatched entry (`entry 4 = 0000 0000 0001 0000`, not arcade `0000 0000 003B 0088`).
- Build 0126 final Genesis SAT nonzero target slots: `0 / 27`.

## Original Arcade Producer Trace

A MAME Lua write tap watched `HW_ADDRESS 0x00D00000..0x00D007FF` in original arcade `rastan`, filtered to the target entries above.

Observed producer write counts:

| arcade_pc | Writes | Role |
|---|---:|---|
| `0x03AD48` | 108 | Earlier PC090OJ clear/offscreen initialization for target entries |
| `0x03B936` | 23 | `0x3B930` table-copy loop, word source byte 0 |
| `0x03B93C` | 23 | `0x3B930` table-copy loop, word source byte 1 |
| `0x03B942` | 23 | `0x3B930` table-copy loop, tile/code conversion call return path |
| `0x03B94C` | 22 | `0x3B930` table-copy loop branch/iteration tail |
| `0x03B87E` | 4 | Score-digit helper record path |
| `0x03B856` | 2 | Score-digit helper update path |
| `0x03B85E` | 2 | Score-digit helper tile/code write path |
| `0x03B83A` | 2 | Score-digit helper update path |
| `0x03B842` | 2 | Score-digit helper tile/code write path |

The title top-score setup is the copied arcade routine beginning at `arcade_pc 0x03B8B0`:

```asm
3b8b0: lea    pc@(0x3b950),a0
3b8b4: lea    0xd00020,a1
3b8ba: moveq  #24,d1
3b8bc: bsrw   0x3b930
...
3b8c8: lea    pc@(0x3b9b0),a0
3b8cc: lea    0xd000e0,a1
3b8d2: bsrw   0x3b930
...
3b8d8: lea    pc@(0x3b9d4),a0
3b8dc: lea    0xd00128,a1
3b8e2: bsrw   0x3b930
```

The shared arcade table-copy loop at `arcade_pc 0x03B930` writes four PC090OJ words per object through the caller-provided `A1` destination and caller-provided `D1` count:

```asm
3b930: clrw   d2
3b932: movew  d2,(a1)+
3b934: clrw   d0
3b936: moveb  (a0)+,d0
3b938: movew  d0,(a1)+
3b93a: clrw   d0
3b93c: moveb  (a0)+,d0
3b93e: movew  d0,(a1)+
3b940: movew  (a0)+,d7
3b942: jsr    0x5b512
3b948: movew  d7,(a1)+
3b94a: subq   #1,d1
3b94c: bne    0x3b932
```

So the original arcade title top-score producer is not a sprite scanner side effect. It explicitly writes PC090OJ object RAM target ranges at `HW_ADDRESS 0x00D00020`, `0x00D000E0`, and `0x00D00128`, using ROM source tables at `arcade_pc 0x03B950`, `0x03B9B0`, and `0x03B9D4`, plus score-digit helper updates for entries `22..25`.

## Address-Map Correlation

Every relevant arcade producer PC mapped exactly through `build/rastan-direct/address_map.json`:

| arcade_pc | runtime_genesis_pc | Segment kind | Meaning |
|---|---|---|---|
| `0x03AD48` | `0x03AF48` | `patched_site` | PC090OJ + tilemap polymorphic dispatch via `genesistan_hook_3ad44_dispatch` |
| `0x03B8B0` | `0x03BAB0` | `arcade_copy` | Title top-score setup is copied |
| `0x03B8BC` | `0x03BABC` | `arcade_copy` | First `bsrw 0x3B930` call site is copied |
| `0x03B8D2` | `0x03BAD2` | `arcade_copy` | Second `bsrw 0x3B930` call site is copied |
| `0x03B8E2` | `0x03BAE2` | `arcade_copy` | Third `bsrw 0x3B930` call site is copied |
| `0x03B930` | `0x03BB30` | `patched_site` | `0x3B930` loop body replaced by `genesistan_pc090oj_hook_target_3b930` |
| `0x03B936` | `0x03BB36` | `patched_site` | Inside replaced `0x3B930` loop span |
| `0x03B93C` | `0x03BB3C` | `patched_site` | Inside replaced `0x3B930` loop span |
| `0x03B942` | `0x03BB42` | `patched_site` | Inside replaced `0x3B930` loop span |
| `0x03B94C` | `0x03BB4C` | `patched_site` | Inside replaced `0x3B930` loop span |
| `0x03B83A` | `0x03BA3A` | `patched_site` | Inside replaced score-digit helper span `0x3B802..0x3B8B0` |
| `0x03B842` | `0x03BA42` | `patched_site` | Inside replaced score-digit helper span `0x3B802..0x3B8B0` |
| `0x03B856` | `0x03BA56` | `patched_site` | Inside replaced score-digit helper span `0x3B802..0x3B8B0` |
| `0x03B85E` | `0x03BA5E` | `patched_site` | Inside replaced score-digit helper span `0x3B802..0x3B8B0` |
| `0x03B87E` | `0x03BA7E` | `patched_site` | Inside replaced score-digit helper span `0x3B802..0x3B8B0` |

No arithmetic mapping was used as proof.

## Build 0126 Genesis Path

Build 0126 disassembly preserves the title setup but routes the write loop through a helper wrapper:

```asm
3bab0: lea    pc@(0x3bb50),a0
3bab4: lea    0xd00020,a1
3baba: moveq  #24,d1
3babc: bsrw   0x3bb30
...
3bb30: jsr    0x00071a12
3bb36: rts
```

The helper at `runtime_genesis_pc 0x00071A12` is `genesistan_pc090oj_hook_target_3b930`. Its source-level behavior is not equivalent to the arcade loop:

```asm
genesistan_pc090oj_hook_target_3b930:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    moveq   #14, %d0
    move.w  %d1, %d6
    cmpi.w  #4, %d6
    bls.s   .Lhook_3b930_count_ok
    moveq   #4, %d6
...
.Lhook_3b930_loop:
    ... read one table tuple from %a0 ...
    bsr     .Lpc090oj_emit_slot
    addq.w  #1, %d0
    subq.w  #1, %d6
    bra.s   .Lhook_3b930_loop
```

Differences that matter for this task:

- Arcade `0x3B930` uses caller-provided `A1` to select the object-RAM destination entries.
- Build 0126 helper ignores the caller-provided `A1` destination for slot selection.
- Arcade first title call passes `D1=24` and `A1=HW_ADDRESS 0x00D00020`, covering entries `4..27`.
- Build 0126 helper hardcodes start slot `14` and clamps `D1` to at most `4`, emitting only helper-owned slots `14..17`.
- The later arcade calls with `D1=9`, `A1=0x00D000E0` and `A1=0x00D00128` are also truncated and relocated into the same helper-owned slot scheme rather than preserving entries `28..45`.

The score-digit helper replacement `genesistan_pc090oj_hook_score_digit_3b802` is also helper-owned rather than object-RAM-destination-faithful. It maps arcade destination pointer progression to slots `22..29` only:

```asm
move.l  %a4, %d3
subi.l  #0x00D00000, %d3
lsr.l   #3, %d3
subi.w  #17, %d3
bcs.s   .Lhook_3b802_next
cmpi.w  #7, %d3
bhi.s   .Lhook_3b802_next
move.w  %d3, %d0
addi.w  #22, %d0
```

This preserves some score-digit semantics for a limited helper slot range, but it does not reproduce the complete original arcade title top-score object-RAM entries.

## Genesis Runtime Evidence and Limitation

A Genesis MAME Lua watch pass over `pc090oj_object_ram`, staged sprite descriptors, staged SAT, final SAT, and raw `HW_ADDRESS 0x00D00000..0x00D007FF` completed only in early boot due the frame-notifier workflow not reaching the intended steady title window. It recorded boot clears but not the title producer window.

A follow-up MAME debugger script was prepared to break on the mapped producer sites, but the headless command failed before execution because the Qt debugger could not connect to a display:

```text
qt.qpa.xcb: could not connect to display :0
This application failed to start because no Qt platform plugin could be initialized.
```

Therefore this pass does **not** claim a fresh debugger-side breakpoint hit on Build 0126 `runtime_genesis_pc 0x03BB30` / `0x00071A12`.

The already-captured stable frame-60 baseline remains valid evidence for the final state:

| Entry | Original arcade frame-60 words | Build 0126 mirror frame-60 words | Build 0126 SAT nonzero |
|---:|---|---|---:|
| 4 | `0000 0000 003B 0088` | `0000 0000 0001 0000` | 0 |
| 5 | `0000 0000 003A 0078` | `0000 0100 0000 0100` | 0 |
| 6 | `0000 0000 003C 0098` | `0000 0100 0000 0100` | 0 |
| 7 | `0000 0000 003D 00A8` | `0000 0100 0000 0100` | 0 |
| 8 | `0000 0008 003E 00B8` | `0000 0100 0000 0100` | 0 |
| 22 | `0000 0010 002B 00A8` | `0000 0100 0000 0100` | 0 |
| 23 | `0000 0010 002D 00A0` | `0000 0100 0000 0100` | 0 |
| 24 | `0000 0010 0031 0098` | `0000 0100 0000 0100` | 0 |
| 25 | `0000 0010 002C 0090` | `0000 0100 0000 0100` | 0 |
| 28..45 | all visible top-score entries | all offscreen/blank mirror words | 0 |

## Classification

### Finding: producer replacement under-emits and misplaces title top-score PC090OJ entries.

The original arcade title top-score path writes the 27 visible entries through PC090OJ object RAM using caller-provided destination/count semantics:

- `arcade_pc 0x03B8B0` setup provides ROM source table, `A1`, and `D1`.
- `arcade_pc 0x03B930` table-copy loop writes the actual PC090OJ entries.
- `arcade_pc 0x03B802` score-digit helper updates part of the top-score digit group.

Build 0126 does not preserve those object-RAM destination/count semantics at the corresponding mapped sites. The copied setup calls a patched `0x3B930` wrapper, and `genesistan_pc090oj_hook_target_3b930` hardcodes helper slot `14` and clamps the original count to four. That explains why the original 27 title top-score objects are absent from `pc090oj_object_ram` and final SAT in the Build 0126 frame-60 baseline.

This is not evidence that the final SAT scanner alone is losing a correct mirror. The mirror is already not arcade-equivalent for the audited entries. It is also not a raw `HW_ADDRESS 0xD00000` write problem for this title path, because the relevant arcade writer bodies are patched/replaced rather than copied raw writers.

## Story Black-Cover Successor

The story-screen black-cover successor remains **not addressed** by this task. This evidence only attributes the title top-score PC090OJ absence. It does not resolve the later story composite black cover, transparent-pen behavior, sprite priority, or the broader PC090OJ pipeline.

## OPEN / KNOWN_FINDINGS Impact

- `OPEN-024`: touched directly. This report identifies a producer-to-mirror semantic gap for the title top-score PC090OJ path.
- `OPEN-001`: touched as rendering context. The title top-score absence is one component of the broader graphics-output gap.
- `OPEN-023`, `OPEN-006`, `OPEN-015`: context only; no work performed.
- Issues opened: none.
- Issues closed: none.
- `KNOWN_FINDINGS.md`: no update in this evidence-only task. A canonical update can wait for the next agreed mechanism-level PC090OJ finding.

## STOP Status

STOP triggered: **NO** for the evidence/classification goal.

Measurement limitation: fresh Genesis debugger breakpoint proof was not captured because MAME's Qt debugger failed in the headless environment. This is recorded as a limitation, not used as contrary evidence. The classification rests on original arcade runtime write evidence, exact JSON address-map correlation, Build 0126 disassembly/source behavior at the mapped patched sites, and the prior stable frame-60 Genesis mirror/SAT baseline.
