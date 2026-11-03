# Andy — Build 55 Active Palette Writer + Bootstrap Re-entry Classification

**Agent:** Andy (Claude Code)
**Type:** Architectural classification + strategic next-work decision (analytical only — no implementation)
**Build:** rastan-direct Build 0055 (Build 55a delivered 3 helpers patched but unreached at runtime)
**Date:** 2026-05-03
**Scope:** classify the active palette producer at `runtime_genesis_pc 0x03BC84` (`arcade_pc 0x03BA84`); choose hook surface; classify `_bootstrap` re-entry; pick project's next-work split.

---

## 0. Executive verdict

The Build 55 white-CRAM regression is correctly diagnosed as **Cause 1 (missing producer)** but the locked design's three intercept sites (`0x59AD4`, `0x03AB00`, `0x045DB8`) **do not run** in this build's startup phase. They are correctly patched per [`Cody_build55_palette_implementation.md`](docs/design/Cody_build55_palette_implementation.md) §B.6 and have zero runtime hits per [`Cody_build55_mame_palette_runtime_trace.md`](docs/design/Cody_build55_mame_palette_runtime_trace.md) §2.1. The actually-active palette producer is **arcade-original code at `runtime_genesis_pc 0x03BC84` (arcade_pc `0x03BA84`)**, classified `arcade_copy` segment with identity offset `+0x200` per [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.1.

**The active writer body at `0x03BC64..0x03BC86` performs the EXACT same per-word conversion as `0x59AD4`** — both translate arcade `0RGB-444` source words to arcade `xBGR-555` via `out = ((raw & 0x0F00) >> 7) | ((raw & 0x00F0) << 2) | ((raw & 0x000F) << 11)` (§1.2 side-by-side). The differences: `0x03BC64` lacks the `0xFFFF` sentinel-skip, expects `%a3`/`%a0`/`%d3` register contract, and is reached from `_bootstrap` re-entry (`0x022C → 0x024A → 0x03B110 → 0x03BBF8 → 0x03BC64`), NOT from `_vblank_service`.

**Recommended hook shape: Option B — function-body replacement of inner loop `0x03BA64..0x03BA87`** (36-byte span; `JSR + RTS + 14 NOPs`). New helper `genesistan_palette_hook_3ba64` reuses the locked design's xBGR-555 → Genesis CRAM conversion + `bank & 0x03` SKIP-≥4 mapping. count_guard 93 → 94.

**Bootstrap re-entry classification: (b) Contributing.** Chain-probe trace shows `_bootstrap_clear_staging` runs FIRST within each cycle, `0x03BC64` writes happen LATER. CRAM is NOT cleared by bootstrap (only `staged_palette_words` and `palette_dirty` are). With Option B helper setting `palette_dirty := 1`, `_vblank_service` (255 hits/64s active) commits to CRAM; CRAM persists across cycles. Bootstrap re-entry IS a real bug (15 cycles in 64s = soft-reset loop) but does not block the visibility fix.

**Strategic decision: Option B (visibility fix first, Build 55b).** Bootstrap re-entry investigation deferred to Build 55c. Reasoning: §1.5 = (b) means fix is unblocked; visible CRAM is a critical diagnostic enabler for downstream work; sequential B → 55c is cleaner than parallel C.

**Locked elements UNCHANGED:** xBGR-555 → Genesis CRAM conversion; `bank & 0x03` SKIP-≥4 mapping; helper architecture (RTS-return; staging → VBlank → VDP); `palette_hooks.s` file; `vdp_commit_palette` infrastructure; `_vblank_service` palette gate. Build 55a helpers (`_59ad4`, `_03ab00`, `_45dae`) remain patched and will activate once arcade execution progresses past bootstrap.

---

## §1.1 New picture confirmation

| # | Fact | Status | Citation |
|---:|---|---|---|
| 1 | 3 Build 55 helpers patched correctly but not reached | CONFIRMED | [`Cody_build55_palette_implementation.md`](docs/design/Cody_build55_palette_implementation.md) §B.6 (postpatch + symbol resolution PASS); [`Cody_build55_mame_palette_runtime_trace.md`](docs/design/Cody_build55_mame_palette_runtime_trace.md) §2.1 (all 3 helpers and `vdp_commit_palette` `hit_count = 0` over 64s emulated) |
| 2 | Active writer is arcade-original copied code | CONFIRMED | [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.1 (`address_map.json:1229-1236`: `kind=arcade_copy`, `identity_offset=512`); §1.7 (Arcade-original); arcade_pc `0x03BA84` exists in [`build/maincpu.disasm.txt:74896`](build/maincpu.disasm.txt#L74896); 32-instruction body byte-match between runtime and arcade |
| 3 | Active chain reaches via `_bootstrap` re-entry, not `_vblank_service` | CONFIRMED | [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.6 — chain-probe trace ([`debug.log:44-52, 3190-3196`](states/traces/build55_active_palette_chain_probe_20260504_150000/debug.log)) shows repeated ordering `BP_BOOT_022C → BP_BOOT_024A → BP_FN_3B110 → BP_FN_3BBF8 → BP_FN_3BC64`; no static call edge from `_vblank_service` (`0x000700C2`) into this chain |
| 4 | Mixed zero/non-zero xBGR-555-shaped values | CONFIRMED | [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.5 (11760 writes / 64s; 1305 zero (11.10%) + 10455 non-zero (88.90%); MIXED); samples `0x200000←0x00FF`, `0x200006←0x0202`, `0x20000A←0x032E`, ..., `0x20001E←0x034C` (increment-by-6 sequence) |
| 5 | `_vblank_service` runs but `vdp_commit_palette` never called (palette_dirty stays 0) | CONFIRMED | [`Cody_build55_mame_palette_runtime_trace.md`](docs/design/Cody_build55_mame_palette_runtime_trace.md) §2.1 (`_vblank_service` 255 hits / 64s) + §2.3 (`palette_dirty` 15 writes, all `pre=0 post=0` from `pc=0x27A` bootstrap clear path) + §2.4 (`vdp_commit_palette` `hit_count = 0`) |

**§1.1 result: 5/5 confirmed.**

---

## §1.2 Active writer body analysis

### Disassembly (verbatim from [`build/genesis_postpatch.disasm.txt:74785-74827`](build/genesis_postpatch.disasm.txt#L74785-L74827))

```
; Outer caller 0x03BBF8 (entry from 0x03B110: bsrw 0x3BBF8)
3bbf8: 263c 0000 0300   movel #768, %d3            ; loop count for first invocation
3bbfe: 41f9 0020 0000   lea 0x200000, %a0          ; dest = arcade palette RAM base
3bc04: 47f9 0004 ecf6   lea 0x4ecf6, %a3           ; src = arcade ROM 0x4ECF6
3bc0a: 6100 0058        bsrw 0x3bc64               ; FIRST CALL — 768 words to 0x200000..0x2005FE
3bc0e: 263c 0000 0010   movel #16, %d3
3bc14: 47f9 0005 0062   lea 0x50062, %a3           ; src = arcade ROM 0x50062
3bc1a: 6100 0048        bsrw 0x3bc64               ; SECOND CALL — 16 words to 0x200600..0x20061E (%a0 post-incremented)
3bc1e: 4e75             rts

; Wrapper at 0x03BC56 (separate caller path, falls through into the loop)
3bc60: d6c0             addaw %d0, %a3
3bc62: 7610             moveq #16, %d3             ; FALL-THROUGH SETS %d3=16

; Inner loop body at 0x03BC64 (REPLACEMENT TARGET)
3bc64: 301b             movew %a3@+, %d0           ; raw arcade source word (0RGB-444)
3bc66: 3400             movew %d0, %d2
3bc68: 0240 0f00        andiw #0x0F00, %d0         ; R nibble at raw[11:8]
3bc6c: ee48             lsrw #7, %d0               ; → out[4:1]
3bc6e: 3202             movew %d2, %d1
3bc70: 0241 00f0        andiw #0x00F0, %d1         ; G nibble at raw[7:4]
3bc74: e549             lslw #2, %d1               ; → out[9:6]
3bc76: 0242 000f        andiw #0x000F, %d2         ; B nibble at raw[3:0]
3bc7a: ea5a             rorw #5, %d2               ; → out[14:11] (ROR5 ≡ <<11 for value with only bits[3:0] set)
3bc7c: 8041             orw %d1, %d0               ; combine
3bc7e: 8042             orw %d2, %d0
3bc80: 30c0             movew %d0, %a0@+           ; write, post-increment
3bc82: 5383             subql #1, %d3
3bc84: 66de             bnes 0x3bc64               ; back-edge (%d3 > 0)
3bc86: 4e75             rts
```

### Side-by-side conversion comparison vs. `0x59AD4`

Per [`Cody_build55_palette_bank_mapping_evidence.md`](docs/design/Cody_build55_palette_bank_mapping_evidence.md) §1.1, the `0x59AD4` per-entry formula is:
- `part_a = (raw & 0x0F00) >> 7`
- `part_b = (raw & 0x00F0) << 2`
- `part_c = (raw & 0x000F) << 11` (computed via `<<8` then `<<3`)
- `out = part_a | part_b | part_c`

`0x03BC64` body produces the IDENTICAL transformation (R nibble → out[4:1], G nibble → out[9:6], B nibble → out[14:11], `or` instead of `add` since the parts don't overlap). The `rorw #5` on a value with only bits[3:0] set is algebraically equivalent to `<<11`. The two routines emit byte-identical output for any input.

**Conclusion: locked design's xBGR-555 → Genesis CRAM conversion (per [`apps/rastan/src/main.c:1008-1017`](apps/rastan/src/main.c#L1008-L1017)) applies UNCHANGED to the active writer.**

### Findings

- **Entry signature** (helper input contract at JSR to `0x03BA64`):
  - `%a3` = source pointer (arcade ROM, post-incremented by `%d3` words)
  - `%a0` = destination pointer (`0x200000`-based for `0x03BBF8` callers, post-incremented by `%d3` words)
  - `%d3` = loop count
  - `%a5` = arcade workram base (preserved by helper convention)
  - `%d0`/`%d1`/`%d2` = scratch (clobbered; not depended on by callers post-return)

- **Conversion shape:** per-word `0RGB-444` → `xBGR-555` (R nibble → bits[4:1], G nibble → bits[9:6], B nibble → bits[14:11], even bits and bit[15] always 0). Identical to `0x59AD4`'s per-entry conversion.

- **Destination range and iteration count inference:** Per `0x03BBF8` invocation: 768 words to `0x200000..0x2005FE` + 16 words to `0x200600..0x20061E` = **784 words / 1568 bytes / 49 banks of 16 entries**. Cody's 11760 / 784 = **15** invocations — matches the 15 bootstrap re-entries in [§1.6 of archaeology](docs/design/Cody_build55_03bc84_origin_archaeology.md). Genesis-relevant subset: **first 64 source words from the first invocation only** (banks 0..3 = tilemap-consumed Genesis lines 0..3); banks 4..47 from first invocation and bank 48 from second invocation = SKIP per locked `bank & 0x03` rule.

- **Sample value pattern:** the increment-by-6 sequence (`0x202, 0x32E, 0x334, 0x33A, 0x340, 0x346, 0x34C`) is the OUTPUT after conversion. The pattern of bottom-bit-zero per channel (out[0]=out[5]=out[10]=out[15]=0) is exactly what the conversion formula produces — every output is a valid xBGR-555 word with low bit per channel zero. Source data is a smoothly-varying gradient palette in arcade ROM (not animated; not random; deterministic per cycle).

- **Format:** **arcade xBGR-555** confirmed via formula match to `0x59AD4` (which itself was confirmed xBGR-555 by [`Cody_build55_mame_palette_format_evidence.md`](docs/design/Cody_build55_mame_palette_format_evidence.md) — `palette_device::xBGR_555`).

- **Sentinel handling: NONE.** Unlike `0x59AD4`'s `0xFFFF` skip, `0x03BC64` translates every source word unconditionally. Helper does not need an early-skip path.

---

## §1.3 Hook surface evaluation

### §1.3.A — Write-site hook at `0x03BC80` (single `movew %d0, %a0@+`)

- Span: 2 bytes — too small for a 6-byte JSR.
- Extending the span backward into the conversion (`orw` instructions) or forward across the `bnes` back-edge collapses into Option B with worse ergonomics. The fundamental problem is that ANY span ≥6 bytes around `0x03BC80` either subsumes the back-edge target (`0x03BC64`) or the loop body's data dependencies.
- Per-word call overhead would be 11760 helper invocations / 64s — wasteful when batching is trivial.
- **NOT VIABLE in pure form** (span size); extended forms collapse to Option B.

### §1.3.B — Function-body replacement of inner loop `0x03BA64..0x03BA87`

- Span: 36 bytes. Replacement: `JSR + RTS + 14 NOPs`.
- **Branch-target safety:** static callers `0x03BC0A`, `0x03BC1A` (BSRs to `0x03BC64` entry); wrapper `0x03BC56..0x03BC62` falls through to entry. Internal `bnes 0x3bc64` is span-internal (becomes helper logic). No external branches into mid-span observed in the surrounding disassembly. Cody Phase A grep would re-verify mechanically.
- **Register-contract:** `%a0`/`%a3`/`%d3` well-defined at entry per §1.2. Helper must advance `%a0` by `%d3 * 2` to preserve caller's post-increment chain (caller `0x03BBF8` reuses `%a0` between its two BSR calls).
- **Conversion + bank-mapping:** locked Option A applies UNCHANGED.
- **Coverage:** 100% of 11760 writes/64s — all paths funnel through the inner loop.
- **Spec impact:** 1 new opcode_replace entry; count_guard 93 → 94.
- **VIABLE — RECOMMENDED.**

### §1.3.C — Caller-level hook at `0x03BBF8`

- Span: 38 bytes (entire `0x03BBF8..0x03BC1F` orchestrator).
- Static callers `0x03B110`, `0x03B380`, `0x03B446` all target entry per [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.6.
- **Coverage gap:** the `0x03BC56` wrapper path also reaches `0x03BC64` (per §1.2) but does NOT go through `0x03BBF8`. Option C would miss any wrapper-path palette updates. Option B catches all paths.
- Same opcode_replace cost as Option B.
- **VIABLE but inferior** — narrower coverage than B for the same cost.

### §1.3.D — Generic write translator (intercept all writes to `0x200000..0x200FFF`)

- Genesis hardware does not support memory-mapped write interception. Software shadow at `0xFF????` would require modifying every code path that writes to `0x200000` (broad NOP audit + redirected JSR insertion).
- This is broad arcade-RAM shadowing (Rule 22 / invariant 3 violation: "no memory shadowing").
- **NOT VIABLE — Rule 22 violation.**

---

## §1.4 Recommended hook shape: B

### Cited reasoning

1. **100% coverage of the active writer.** All paths (BSRs from `0x03BBF8`, fall-through from `0x03BC56` wrapper) funnel through the inner loop at `0x03BC64`. Per [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.6, the chain-probe shows `BP_FN_3BC64` = 11760 (matches total writes).
2. **Locked conversion + bank-mapping apply unchanged** (§1.2 algebraic identity to `0x59AD4`). Rule 18 LOCKED elements preserved.
3. **Architecture-compliant.** Helper is RTS-returning leaf (Rule 4 / invariant 2); no new lifecycle (invariant 1); writes only to existing `staged_palette_words` + `palette_dirty` flag (no shadowing — invariant 3); staging → VBlank → VDP pattern preserved (invariant 9 — `_vblank_service` already runs; helper activates the dormant commit path).
4. **Same architectural pattern as locked `0x59AD4` body replacement.** Helper does not maintain arcade-side palette RAM at `0x200000` — that's the same decision documented in [`Andy_build55_palette_translation_design.md`](docs/design/Andy_build55_palette_translation_design.md) §0 for `0x59AD4`. No arcade reader of `0x200000..0x20061F` cares about the contents post-hook.
5. **Sentinel-skip absence simplifies the helper** vs. `0x59AD4`. No `0xFFFF` early-skip needed.
6. **Minimal spec surface.** 1 new `opcode_replace` entry; 1 new helper symbol; reuses existing `palette_hooks.s` file.

### Phase A precheck requirements (Cody verifies before implementation)

- **§A.1 register-contract gate** at `arcade_pc 0x03BA64`: verify `%a0`, `%a3`, `%d3` well-defined at every reachable entry. From §1.2:
  - `0x03BC0A` BSR: `%a0=0x200000`, `%a3=0x4ECF6`, `%d3=768` ✓
  - `0x03BC1A` BSR: `%a0=0x200600` (post-inc), `%a3=0x50062`, `%d3=16` ✓
  - Wrapper fall-through (`0x03BC56`-path): `%a3` set by wrapper, `%d3=16` from `0x3BC62`. `%a0` set by wrapper's caller (`0x03BC2A: lea %a5@(5632), %a0` for known wrapper-caller `0x03BC20`) — may NOT be `0x200000`-based. **Helper must robustly handle `%a0` outside `0x200000..0x200FFF` (treat as no-op).**
- **§A.2 span-safety gate** at `0x03BA64..0x03BA87`: grep [`build/maincpu.disasm.txt`](build/maincpu.disasm.txt) for any branch/jsr/jmp landing in the interior `0x03BA66..0x03BA85`. Expected: NONE.
- **§A.3 side-effect preservation:** helper advances `%a0` by `%d3*2` and `%a3` by `%d3*2` to preserve caller's pointer-chain.
- **§A.4 caller post-call dependency:** verify no caller reads `%d0`/`%d1`/`%d2` between BSR return and next reset. Expected: NONE.

---

## §1.5 Bootstrap re-entry classification

### Order of clear vs. writes within each cycle

From [`Cody_build55_03bc84_origin_archaeology.md`](docs/design/Cody_build55_03bc84_origin_archaeology.md) §1.6 chain-probe trace ([`debug.log:44-52, 3190-3196`](states/traces/build55_active_palette_chain_probe_20260504_150000/debug.log)):

```
BP_BOOT_022C   ; bootstrap re-entry
BP_BOOT_024A   ; calls _bootstrap_clear_staging (clears staged_palette_words, palette_dirty)
BP_FN_3B110    ; later: 0x03B110 → 0x03BBF8 → 0x03BC64
BP_FN_3BBF8
BP_FN_3BC64    ; writes happen LAST
```

**Within each cycle: clear FIRST, write LATER.**

### CRAM persistence

`_bootstrap_clear_staging` ([`apps/rastan-direct/src/boot/boot.s:168-208`](apps/rastan-direct/src/boot/boot.s#L168-L208)) clears WRAM staging buffers (`staged_palette_words[0..63]`) and `palette_dirty` only. It does NOT clear Genesis CRAM. Once `vdp_commit_palette` runs (which it will, when `palette_dirty == 1` is observed at VBlank), CRAM is populated and persists across bootstrap re-entries.

### Sequence with Option B helper installed

1. Cycle N: `_bootstrap_clear_staging` runs → `staged_palette_words=0`, `palette_dirty=0`.
2. `0x03BBF8 → 0x03BC64`: helper fires, translates first 64 source words from `0x4ECF6` → `staged_palette_words[0..63]`, sets `palette_dirty := 1`.
3. Some VBlank during cycle N (255 vblank hits / 64s / 15 cycles ≈ 17 vblanks per cycle): `_vblank_service` reads `palette_dirty=1`, calls `vdp_commit_palette`, copies staging → CRAM, clears `palette_dirty=0`.
4. Cycle N+1: bootstrap re-entry. Clear runs. Helper re-stages. CRAM remains populated from cycle N's commit; cycle N+1's commit refreshes with same values.

**No conflict.** White CRAM goes away after first successful stage-then-commit within any cycle.

### HV Counter / BlastEm relation

The BlastEm HV Counter port 8 fatal error (parked) and the bootstrap re-entry pattern MAY share a root cause — both are arcade-progression bugs. Hypothesis: BlastEm strict-fatals on a write to a read-only register; MAME silently allows or remaps it; the underlying arcade behavior in both cases triggers a soft-reset back to `0x0202`. **This hypothesis is NOT supported by direct evidence in current Cody traces.** Confirming it requires a separate Cody evidence task tracing the trigger source for the jumps to `0x0202` (Build 55c scope).

### Classification: (b) Contributing

- Real bug (15 cycles in 64s ≠ normal Rastan boot — original arcade boots once).
- Does NOT block visibility fix: clear-before-write order; CRAM persists; `_vblank_service` already commits.
- NOT (a) blocking: clear-before-write means staging gets repopulated within each cycle.
- NOT (c) unrelated/normal: re-entry indicates soft-reset loop.
- NOT (d) unresolved: enough evidence to classify as (b).

---

## §1.6 Strategic next-work split: Option B

### Cited reasoning

1. **§1.5 = (b) — Option B unblocked.** Bootstrap re-entry does not prevent CRAM population.
2. **Visible palette is a critical diagnostic enabler.** Build 55a's all-white CRAM makes downstream rendering bug triage nearly impossible. Once colors are correct, regressions in Block-A, tilemap, and PC090OJ helpers become visually distinguishable.
3. **The active writer is doing real arcade-faithful work.** Translating it is exactly the kind of helper-replacement the architecture mandates.
4. **Locked Build 55a helpers WILL activate downstream.** `_59ad4`, `_03ab00`, `_45dae` are correctly patched. Once Build 55c addresses bootstrap re-entry and arcade execution progresses past startup, they fire automatically. Andy's recommendation is additive — keep locked helpers, ADD the active-writer helper.
5. **Sequential B → 55c is cleaner than parallel C.** Bootstrap investigation requires deep exception/vector tracing; benefits from having palette-correct visuals as a debugging anchor.
6. **Option D rejected** — §§1.1-1.5 give sufficient evidence to choose direction.

### Build 55b/55c sequencing

- **Build 55b** (this task's scope; Cody implements): single new opcode_replace entry at `arcade_pc 0x03BA64`; new helper `genesistan_palette_hook_3ba64`; count_guard 93 → 94. Verification: MAME trace shows `vdp_commit_palette` reaching non-zero hits and CRAM containing non-`0x0EEE` values.
- **Build 55c** (deferred; Cody evidence task only): trace the trigger that causes execution to jump back to `0x0202` (exception vectors, watchdog, HV Counter port 8 write, bus error). Output: classification report. NO implementation in 55c — implementation in subsequent build per Andy classification.
- **Build 56** (separately deferred): sprite bank-line table — out of scope.

---

## §1.7 Architecture compliance verification

For Option B + Build 55b:

| # | Invariant | Preserved? | Reasoning |
|---:|---|---|---|
| 1 | No Genesis-side lifecycle | YES | Helper invoked from arcade-triggered chain |
| 2 | Helpers RTS-return | YES | Helper does work, RTS |
| 3 | No memory shadowing | YES | Writes only to existing `staged_palette_words` and `palette_dirty` |
| 4 | No scaffolding | YES | Production-intent; no debug paths |
| 5 | v3.1 closures intact | YES | `_3b930`, `_54810` untouched |
| 6 | v3.2 dispatch contract | YES | `0x03AD44` untouched |
| 7 | `opcode_replace 0x03AF04` | YES | Untouched |
| 8 | `_bootstrap` closure | **PRE-EXISTING violation** | Bootstrap IS re-entering; this redesign does NOT introduce new re-entry. Build 55c addresses. |
| 9 | `_vblank_service` closure | YES | Helper sets `palette_dirty`; `_vblank_service` reads/commits per existing pattern; activates dormant commit path |
| 10 | D6-fix patches | YES | Untouched |

**Result: 9/10 fully preserved by this redesign; invariant 8 has a PRE-EXISTING violation (bootstrap re-entry) that this redesign does not introduce, and which Build 55c is scoped to address.**

This redesign introduces ZERO new architectural violations.

---

## §1.8 Bounded Cody next task(s)

### Build 55b — Active writer hook implementation

**Phase A precheck (read-only):**

1. §A.1 register-contract gate at `0x03BA64` per §1.4.
2. §A.2 span-safety gate at `0x03BA64..0x03BA87` per §1.4.
3. §A.3 side-effect preservation: helper advances `%a0` and `%a3` by `%d3*2`.
4. §A.4 combined: PROCEED/STOP.

**Phase B implementation (writes):**

| field | value |
|---|---|
| New helper | `genesistan_palette_hook_3ba64` in [`apps/rastan-direct/src/palette_hooks.s`](apps/rastan-direct/src/palette_hooks.s) |
| Helper input contract | `%a0` = dest pointer (treat as `0x200000`-based bank-detection input); `%a3` = source pointer (arcade ROM, `0RGB-444` words); `%d3` = loop count |
| Helper conversion | per source word: `0RGB-444` → Genesis CRAM `BGR-333` (locked Option A; algebraically equivalent to xBGR-555 → CRAM via main.c:1008-1017). NO sentinel handling. |
| Helper bank-mapping | `bank_idx = (%a0 - 0x00200000) / 0x20`, computed per word from running `%a0`. If `bank_idx ∈ {0..3}`: stage to `staged_palette_words[bank_idx*16 + entry_in_bank]`. Else: SKIP. If `%a0` outside `0x200000..0x200FFF` (wrapper-path): SKIP all (no-op). Set `palette_dirty := 1` if any word staged. |
| Side effects | Advance `%a0` by `%d3 * 2`; advance `%a3` by `%d3 * 2`. Save/restore scratch via `movem.l`; preserve `%a5`. |
| New `opcode_replace` entry | `arcade_pc 0x03BA64`; original 36 bytes (`0x03BA64..0x03BA87`); replacement = `4EB9 {sym} 4E75 4E71×14` (JSR + RTS + 14 NOPs). Style matches `0x059AD4` body replacement. |
| Updated `count_guard` | 93 → 94 |
| Updated `required_symbols` | add `genesistan_palette_hook_3ba64` |
| Postpatcher invariant | byte count measured-not-presumed (Build 54 D6-fix discipline). Capture first-failure delta and update `tools/translation/postpatch_startup_rom.py` to measured value. |

**Verification gates:**

- Postpatcher: `count = 94`; total bytes measured-not-presumed.
- Boot guard: PASS pre/post-patch.
- Symbol resolution: `genesistan_palette_hook_3ba64` present.
- D00778 invariant: unchanged.
- VRAM roundtrip: unchanged.
- 10 invariants per §1.7 (with pre-existing #8 violation noted, NOT introduced by this build).

**Build 55b runtime verification gate (REQUIRED):**

- MAME 64s headless trace: `genesistan_palette_hook_3ba64` `hit_count ≥ 15 × 49 = 735` (15 bootstrap cycles × 49 inner-loop entries per cycle).
- `vdp_commit_palette` `hit_count ≥ 1` (proves commit path activated).
- CRAM watchpoint: at least one CRAM line gets non-`0x0EEE` value.
- Visual: title-screen palette no longer all-white.

### Build 55c — Bootstrap re-entry root cause investigation (DEFERRED — Cody evidence only)

Scope outline (NOT in scope for Build 55b):

1. Identify all static call sources to bootstrap entry `0x0202` (grep postpatch disasm for `bsrw/bras/jsr/jmp 0x0202`; check exception vector table at `0x0008..0x003C`).
2. MAME watchpoint trace: breakpoint on `0x0202` with last-N-PCs capture; correlate against the 15 observed entries.
3. HV Counter `0xC00008` write watchpoint: confirm/refute BlastEm hypothesis under MAME.
4. Output: `Cody_build55c_bootstrap_reentry_evidence.md` with classification (single trigger / multiple triggers / unknown).
5. NO implementation. Implementation in Build 55d per Andy classification of Cody's evidence.

---

## Phase 2 Integrity

- §1.1 new picture confirmed: YES (5/5 facts confirmed)
- §1.2 active writer body analyzed: YES (entry signature + conversion + destination + sample + format + sentinel)
- §1.3 four hook-surface options evaluated: YES (A NOT VIABLE; B VIABLE-recommended; C VIABLE-inferior; D NOT VIABLE per Rule 22)
- §1.4 recommended hook shape: **B** with cited reasoning + Phase A precheck requirements
- §1.5 bootstrap re-entry: **(b) contributing**
- §1.6 strategic next-work split: **B** (Build 55b first; Build 55c deferred)
- §1.7 architecture compliance: 9/10 fully preserved; invariant 8 PRE-EXISTING violation NOT introduced by this redesign
- §1.8 bounded Cody next task(s): Build 55b implementation plan (COMPLETE) + Build 55c evidence task (deferred outline)
- All conclusions cited (Rule 17): YES
- No revisiting locked elements (Rule 18): YES
- Arcade-copy hook discipline (Rule 19): YES — Phase A gates specified
- Bootstrap re-entry analysis explicit (Rule 20): YES — classified (b)
- Strategic decision with cited reasoning (Rule 21): YES
- Invariants preserved (Rule 22): 9/10; pre-existing #8 noted independently
- Scope discipline (Rule 23): YES
- No new evidence collection beyond specified Cody follow-up (Rule 24): YES
- No external sources (Rule 25): YES
- No source/spec/tool modifications: YES
- STOP triggered: NO — Build 55b unblocked.
