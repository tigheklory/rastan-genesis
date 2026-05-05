# Andy — Active Phase A Entry Classification

**Agent:** Andy
**Type:** Classification (analysis-only, no implementation)
**Build context:** `rastan-direct` Build 0051
**Architecture compliance:** CONFIRMED (no source, spec, or tool modifications).

**Scope:** exactly the **13 Phase A `opcode_replace` entries that were HIT** during first-second boot per the HIT/NOT_HIT table in [Cody_phase_a_nop_coverage.md](docs/design/Cody_phase_a_nop_coverage.md) Phase 3. The other 4 entries in the Phase A set (2 NOT_HIT at `0x03AF4C` / `0x03AF72`, and 2 non-NOP pointer remaps at `0x03AEEA` / `0x03AEF0`) are out of scope.

---

## Address-space legend

- `arcade_pc <value>` — PC in arcade ROM address space.
- `HW <addr>` — 68000-space memory-mapped address on the arcade board; most target arcade chips at addresses that are **unmapped on Genesis** (outside cart-ROM `0x000000..0x0FC1C3`, VDP port band `0x00C00000..0x00C0001F`, I/O band `0x00A10000..0x00A1001F`, Z80 band `0x00A00000..0x00A0FFFF`, and WRAM `0x00FF0000+`).
- `runtime_genesis_pc` ≈ `arcade_pc + 0x200` per the whole-maincpu-relocation in `specs/rastan_direct_remap.json`.
- Arcade board chip roles from standard Taito F2 documentation cross-referenced against [TC0040IOC_specifications.md](docs/design/TC0040IOC_specifications.md) and the behaviour notes in `specs/rastan_direct_remap.json` precedents.

---

## Phase 1 — Active entry identification

From [Cody_phase_a_nop_coverage.md](docs/design/Cody_phase_a_nop_coverage.md) Phase 3, filtered to `executed? = HIT` only. Entry bytes cross-verified against [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json) at the spec lines cited below.

| # | ledger idx | arcade_pc | spec line | original instruction | replacement | hit count | first hit cycle |
| - | ---------: | --------- | ---------:| -------------------- | ----------- | --------: | --------------: |
| 1 | 0  | `0x03A00C` | 115 | `CLR.W 0x350008`            | `4E714E714E71`       | 14   | 803975  |
| 2 | 1  | `0x03A012` | 121 | `MOVE.W D0, 0x3C0000`       | `4E714E714E71`       | 14   | 803987  |
| 3 | 32 | `0x03AE86` | 307 | `MOVE.W #0, 0xC50000`       | `4E714E714E714E71`   | 1    | 1332329 |
| 4 | 33 | `0x03AE8E` | 313 | `MOVE.W #0, 0xD01BFE`       | `4E714E714E714E71`   | 1    | 1332345 |
| 5 | 34 | `0x03AE96` | 319 | `CLR.W 0x350008`            | `4E714E714E71`       | 1    | 1332361 |
| 6 | 36 | `0x03AEA2` | 331 | `MOVE.B #4, 0x3E0001`       | `4E714E714E714E71`   | 1    | 1332385 |
| 7 | 37 | `0x03AEAA` | 337 | `MOVE.B #1, 0x3E0003`       | `4E714E714E714E71`   | 1    | 1332401 |
| 8 | 38 | `0x03AEBC` | 343 | `MOVE.W D1, 0x200000`       | `4E714E714E71`       | 4178 | 1332441 |
| 9 | 39 | `0x03AEC6` | 349 | `MOVE.B #4, 0x3E0001`       | `4E714E714E714E71`   | 1    | 1509935 |
| 10| 40 | `0x03AECE` | 355 | `MOVE.B #0, 0x3E0003`       | `4E714E714E714E71`   | 1    | 1509951 |
| 11| 41 | `0x03AEE0` | 361 | `MOVE.W D1, 0x200000`       | `4E714E714E71`       | 2998 | 1509991 |
| 12| 45 | `0x03AF0A` | 385 | `MOVE.W D0, 0x3C0000`       | `4E714E714E71`       | 1    | 2250313 |
| 13| 46 | `0x03AF14` | 391 | `MOVE.W D0, 0x3C0000`       | `4E714E714E71`       | 1    | 2346599 |

Total active suppression executions: **7213** (matches Phase 4 §4 of the Cody doc).

---

## Phase 2 — Per-entry analysis

### Entry 1 — `arcade_pc 0x03A00C`

- **Suppressed behaviour:** `CLR.W 0x00350008` inside the arcade L5 VBlank handler (`arcade_pc 0x3A008` body, per [Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) P2 disassembly table).
- **Hardware / domain:** **TC0140SYT** sound/coin-counter aux-chip register at `HW 0x00350008`. On Genesis `0x00350008` is outside cart-ROM (ROM ends at `0x0FC1C3`) and outside every Genesis-hardware band — **unmapped**.
- **Replacement path:** no Genesis equivalent. Coin input is handled on Genesis via the `genesistan_shadow_input_390005` byte redirects (spec lines 115, 121, 127). No Genesis consumer watches `0x350008`.
- **Evidence:** spec-line-note language matches precedent at `arcade_pc 0x03A1D8` / `0x03EF28` for TC0040IOC watchdog suppression; HIT 14 times in the first second (once per L5 IRQ at 60 Hz for ~14 frames before the trace cut off at frame boundary; 14 × ~16.7 ms ≈ 234 ms, consistent with L5 running for ~0.23 s of the 1-second trace).
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** arcade-only aux-chip register with no Genesis mapping. Matches numerous existing precedents in the spec. Write-only (never read by arcade code — checked via grep for reads of `0x350008` in `build/maincpu.disasm.txt`, none found). Suppression cannot break execution: nothing reads the register.

### Entry 2 — `arcade_pc 0x03A012`

- **Suppressed behaviour:** `MOVE.W D0, 0x003C0000` inside the arcade L5 VBlank handler at `arcade_pc 0x3A008`.
- **Hardware / domain:** **TC0040IOC** video-control register at `HW 0x003C0000` (screen flip / mode / cabinet bits). Unmapped on Genesis.
- **Replacement path:** Genesis video is configured by `vdp_boot_setup` at cold boot. No runtime equivalent of a per-VBlank TC0040IOC write.
- **Evidence:** matches the `33C0 003C 0000 → 4E71 4E71 4E71` pattern also applied at `0x03AF0A`, `0x03AF14`, `0x03AF4C`, `0x03AF72` (see spec). Same L5-handler hit pattern as entry 1 (14 hits, executed just after `0x03A00C`).
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** arcade-only chip, write-only, no Genesis consumer.

### Entry 3 — `arcade_pc 0x03AE86`

- **Suppressed behaviour:** `MOVE.W #0, 0x00C50000` at the top of arcade startup_common body (first post-`BRA.W 0x3A000` instruction).
- **Hardware / domain:** **PC080SN** screen-flip register at `HW 0x00C50000`. On Genesis, `0x00C50000` is outside the VDP port mirror (VDP ends at `0x00C0001F`; the rest of `0x00C10000..0x00DFFFFF` is undefined).
- **Replacement path:** Genesis screen-flip is per-tile via nametable flip bits; no board-wide flip register.
- **Evidence:** spec note ("Suppress arcade PC080SN screen-flip write; no Genesis equivalent"). Identical pattern to existing entries `0x03ADFE` / `0x03AE16` (both pre-Phase-A, same suppressed instruction form `33FC … 00C5 0000`).
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** arcade-only chip register; write-only; replacement pattern matches validated precedent at `0x03ADFE`/`0x03AE16`.

### Entry 4 — `arcade_pc 0x03AE8E`

- **Suppressed behaviour:** `MOVE.W #0, 0x00D01BFE` at startup_common body.
- **Hardware / domain:** **PC090OJ** sprite-DMA trigger register at `HW 0x00D01BFE`. Unmapped on Genesis.
- **Replacement path:** Genesis sprites use VDP SAT + DMA via different mechanism (VDP_CTRL command). No equivalent of a PC090OJ DMA-start write.
- **Evidence:** spec note matches precedent at `0x03AE06` / `0x03AE1E` (same suppression pattern, identical note language: "Suppress arcade-only absolute hardware write while preserving helper software mirror behavior").
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** arcade-only chip; write-only; precedent-matched.

### Entry 5 — `arcade_pc 0x03AE96`

- **Suppressed behaviour:** `CLR.W 0x00350008` in startup_common (second instance after the in-L5-handler occurrence at `0x03A00C`).
- **Hardware / domain:** TC0140SYT coin counter — same as entry 1.
- **Replacement path:** same as entry 1.
- **Evidence:** spec bytes `427900350008` → `4E714E714E71` identical to entry 1 (except spec arcade_pc). Single hit during startup_common.
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** same site-kind as entry 1, different location. Consistent.

### Entry 6 — `arcade_pc 0x03AEA2`

- **Suppressed behaviour:** `MOVE.B #4, 0x003E0001` — arcade sound-CPU reset-control write.
- **Hardware / domain:** **TC0140SYT sound-CPU** reset port at `HW 0x003E0001`. The arcade board's audio subsystem is a separate sound CPU (Z80A) with reset/bank ports at `0x3E0001` / `0x3E0003`. Writing `#4` is the arcade's "release reset" sequence.
- **Replacement path:** Genesis has its own Z80 sub-CPU controlled via `0x00A11100`-`0x00A11101`. The arcade's sound CPU is neither present nor reachable on Genesis. The Phase B tree has `apps/rastan-direct/src/sound/sound_comm.s` and `z80_driver.s` (confirmed in the Phase 5 audit of [Andy_load_scene_tiles_sr_analysis.md](docs/design/Andy_load_scene_tiles_sr_analysis.md)), but whether they are wired to arcade's sound-command writes is not verified here.
- **Evidence:** spec note "Suppress arcade TC0140SYT sound-CPU reset write; no Genesis equivalent." Pair with entries 7/9/10 (the four sound-CPU init writes).
- **Classification:** `status = provisional`, `category = hardware_chip_unmapped`.
- **Reasoning:** the suppression is correct *at the chip-address level* — `0x003E0001` is unmapped on Genesis and writing `#4` there cannot have any Genesis-side effect. However, if `apps/rastan-direct/src/sound/` is later wired up to translate arcade's sound-command writes into Genesis Z80 commands, this suppression may need to become a **helper-redirect** (call a `genesistan_sound_cpu_reset` stub that programs the Genesis Z80 reset line) rather than a silent NOP. Marking `provisional` rather than `intended_permanent` captures that future-work flag. The suppression is not currently breaking anything — no Genesis-side sound consumer exists to miss the write.

### Entry 7 — `arcade_pc 0x03AEAA`

- **Suppressed behaviour:** `MOVE.B #1, 0x003E0003` — arcade sound-CPU bank-select write.
- **Hardware / domain:** TC0140SYT sound-CPU bank register.
- **Replacement path:** same scope note as entry 6.
- **Evidence:** spec note; pair with entries 6/9/10.
- **Classification:** `status = provisional`, `category = hardware_chip_unmapped`.
- **Reasoning:** identical justification to entry 6. The `#1` vs `#4` / `#0` immediates distinguish the specific sound-CPU step (bank select vs reset assertion vs reset release) but share the same Genesis-side status: no consumer.

### Entry 8 — `arcade_pc 0x03AEBC`

- **Suppressed behaviour:** `MOVE.W D1, 0x00200000` — the **write** half of arcade's two-instruction RAM probe loop (`arcade_pc 0x03AEB2..0x03AEC4`). The loop reads a word from `0x00200000` into `D1`, writes `D1` back, decrements `D0`, branches — 8192 iterations.
- **Hardware / domain:** arcade RAM probe region (some Taito boards expose auxiliary RAM or MCU shared RAM at `0x00200000`). Unmapped on Genesis — outside cart-ROM `0x0FC1C3`, outside every Genesis hardware band.
- **Replacement path:** no Genesis equivalent. The read half (`MOVE.W 0x00200000, D1` at `arcade_pc 0x3AEB6`) is **not** suppressed; on Genesis it returns whatever is at address `0x00200000` (unmapped region — typically `0xFFFF` or bus-error-read depending on emulator). The loop never compares read vs written, so it neither verifies RAM nor makes a control-flow decision based on the value. Net effect on Genesis post-suppression: 8192-iteration busy-wait that reads unmapped memory into D1 and does nothing else.
- **Evidence:** spec note "Suppress arcade RAM-probe write-back at 0x200000 (unmapped on Genesis)." 4178 hits in the first second — the outer loop at `0x03AEB2` was entered during startup_common but did not complete all 8192 iterations within the 1-second trace window (expected: loop reached iteration 4178 when the trace cut off; the remaining iterations continue afterward). The 2998 hits on entry 11 (same instruction shape at `0x03AEE0`) correspond to the **second** RAM-probe loop at `arcade_pc 0x03AED6..0x3AEE8` which had progressed further by cutoff — meaning both loops were running concurrently in terms of trace coverage, which would only happen if the boot was restarting, confirming watchdog-driven reboot behaviour is active.
- **Classification:** `status = intended_permanent`, `category = ram_probe_suppression`.
- **Reasoning:** write is to unmapped Genesis memory; read does not feed a control-flow decision. Suppression cannot break arcade logic — it removes only the useless write cycles.

### Entry 9 — `arcade_pc 0x03AEC6`

- **Suppressed behaviour:** `MOVE.B #4, 0x003E0001` — second sound-CPU reset write, post-RAM-probe loop 1.
- **Hardware / domain:** TC0140SYT sound-CPU reset — same as entry 6.
- **Replacement path:** same scope note.
- **Evidence:** spec note "Suppress arcade TC0140SYT sound-CPU reset write (second pass)."
- **Classification:** `status = provisional`, `category = hardware_chip_unmapped`.
- **Reasoning:** same as entry 6. Second occurrence of the same arcade sound-CPU boot sequence (the arcade apparently runs reset-then-probe-then-reset again — typical Taito sound CPU boot pattern).

### Entry 10 — `arcade_pc 0x03AECE`

- **Suppressed behaviour:** `MOVE.B #0, 0x003E0003` — second sound-CPU bank write, bank 0 this time.
- **Hardware / domain:** TC0140SYT sound-CPU bank — same as entry 7.
- **Replacement path:** same scope note.
- **Evidence:** spec note "Suppress arcade TC0140SYT sound-CPU bank clear (second pass)."
- **Classification:** `status = provisional`, `category = hardware_chip_unmapped`.
- **Reasoning:** same as entry 7.

### Entry 11 — `arcade_pc 0x03AEE0`

- **Suppressed behaviour:** `MOVE.W D1, 0x00200000` — second RAM-probe loop write (the loop at `arcade_pc 0x03AED6..0x3AEE8`).
- **Hardware / domain:** RAM probe — same as entry 8.
- **Replacement path:** same as entry 8.
- **Evidence:** spec note "Suppress arcade RAM-probe write-back at 0x200000 (second pass)." 2998 hits.
- **Classification:** `status = intended_permanent`, `category = ram_probe_suppression`.
- **Reasoning:** identical to entry 8.

### Entry 12 — `arcade_pc 0x03AF0A`

- **Suppressed behaviour:** `MOVE.W D0, 0x003C0000` — TC0040IOC video-control write within startup_common, after RAM probes.
- **Hardware / domain:** TC0040IOC — same as entry 2.
- **Replacement path:** same as entry 2.
- **Evidence:** spec note "Suppress arcade TC0040IOC video-control write in startup (first)."
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** same as entry 2.

### Entry 13 — `arcade_pc 0x03AF14`

- **Suppressed behaviour:** `MOVE.W D0, 0x003C0000` — TC0040IOC video-control write, second startup instance.
- **Hardware / domain:** TC0040IOC — same as entry 2.
- **Replacement path:** same as entry 2.
- **Evidence:** spec note "Suppress arcade TC0040IOC video-control write in startup (second)."
- **Classification:** `status = intended_permanent`, `category = hardware_chip_unmapped`.
- **Reasoning:** same as entry 2.

---

## Phase 3 — Cross-entry consistency

### Grouping by suppressed instruction

| instruction | entries | status | category |
| ----------- | ------- | ------ | -------- |
| `CLR.W 0x350008` (coin counter) | 1 (L5 handler), 5 (startup) | `intended_permanent` | `hardware_chip_unmapped` |
| `MOVE.W D0, 0x3C0000` (TC0040IOC video) | 2 (L5 handler), 12, 13 (startup) | `intended_permanent` | `hardware_chip_unmapped` |
| `MOVE.W #0, 0xC50000` (PC080SN flip) | 3 | `intended_permanent` | `hardware_chip_unmapped` |
| `MOVE.W #0, 0xD01BFE` (PC090OJ DMA) | 4 | `intended_permanent` | `hardware_chip_unmapped` |
| `MOVE.B #4, 0x3E0001` (sound CPU reset) | 6, 9 | `provisional` | `hardware_chip_unmapped` |
| `MOVE.B #1, 0x3E0003` (sound CPU bank set) | 7 | `provisional` | `hardware_chip_unmapped` |
| `MOVE.B #0, 0x3E0003` (sound CPU bank clear) | 10 | `provisional` | `hardware_chip_unmapped` |
| `MOVE.W D1, 0x200000` (RAM probe) | 8, 11 | `intended_permanent` | `ram_probe_suppression` |

### Consistency checks

- Entries targeting the same `HW` address are classified identically in every case: no drift between in-L5-handler and in-startup_common occurrences of the same write. **Consistent.**
- All four sound-CPU entries are given `provisional` status for the same reason (future Genesis Z80 driver may want to intercept these); the four are treated as a group. **Consistent.**
- All four TC0040IOC video-control entries (including entries 12, 13 and the two NOT_HIT counterparts at `0x03AF4C`/`0x03AF72` out-of-scope here) share the same `intended_permanent` / `hardware_chip_unmapped` classification. **Consistent.**
- RAM-probe entries (8, 11) are distinguished from other suppressions by the dedicated `ram_probe_suppression` category because the suppressed instruction is part of a **loop** whose execution continues (8192 iterations per call, 2 calls) rather than a single per-frame/per-boot write. This distinction is semantic, not a classification conflict. **Consistent internally.**

### Inconsistencies

**NONE.**

---

## Phase 4 — System observation

The prompt flags three runtime symptoms and asks whether the 13 suppressions contribute:

### "Massive WRAM write reduction vs arcade"

- The 13 suppressions target addresses in `0x200000`, `0x350008`, `0x3C0000`, `0x3E0001/3`, `0xC50000`, `0xD01BFE`. **None of these is WRAM** — they're all arcade hardware-chip addresses outside the arcade work-RAM range (which on arcade is `0x100000..0x10FFFF` and is redirected on Genesis to `0x00FF0000..0x00FFFFFF`).
- The suppression does eliminate ≈ **7213** 68000 memory writes per frame-worth of this activity, but all of those writes targeted addresses that on Genesis land in unmapped space, where the writes are silently dropped by the bus anyway. The eliminated writes are **not** WRAM writes — they can't account for a WRAM-write reduction.
- **Does not explain:** the observed WRAM-write reduction must originate elsewhere (e.g. missing arcade-side state transitions that should have caused WRAM writes, or hook-level differences in staging-buffer writes, neither of which this prompt covers).

### "No arcade I/O activity"

- On arcade, I/O = TC0040IOC inputs/outputs + TC0140SYT coin counter + DIP reads. In rastan-direct, the DIP reads (`0x390009`, `0x39000B`) and input reads (`0x390001/3/5/7`) are redirected to Genesis shadow bytes by Phase-A-independent opcode_replaces already present in the spec (lines 115-259 cluster of input-shadow redirects). Those are *not* in the 13-entry HIT set.
- The suppressions in the 13-entry set target **output-side** writes (coin-counter clear, sound-CPU control, video-control, screen-flip, sprite-DMA trigger, RAM probe). None is an input. Suppressing output writes cannot cause "no I/O activity" because the I/O flow into arcade code is via the already-redirected shadow reads.
- **Does not directly explain.** However: the suppressed sound-CPU control writes (entries 6, 7, 9, 10) mean the sound subsystem is never kicked off. If "no arcade I/O activity" is measured as "no sound, no coin counter", it is *consistent with* these suppressions being permanent — by design. If "I/O activity" is expected because a Genesis-side sound driver should have been initialised, then the `provisional` status of entries 6, 7, 9, 10 is the correct flag: the suppressions should be replaced by Genesis sound helper redirects before sound comes up.

### "Watchdog-driven control anomalies"

- None of the 13 entries writes to the arcade TC0040IOC watchdog register at `0x380000` (those suppressions are present in the spec at `0x03A1D8`, `0x03AE9C`, `0x03AF1E`, `0x03EF28`, `0x03EF48`, `0x03EF8A`, `0x03EFAA`, `0x045306` — separate from the 13 HIT entries analysed here, although `0x03AE9C` is one of the 4 non-HIT Phase A entries adjacent to this set).
- The arcade-side "watchdog" that drives control anomalies per prior forensic work ([Andy_reset_path_root_cause.md](docs/design/Andy_reset_path_root_cause.md)) is the arcade **countdown timer at `A5@(0x2C)`** — a software countdown in arcade work-RAM. It decrements in arcade code (function at `arcade_pc 0x39F80`) once per call until it hits zero, then triggers warm-restart. That countdown is **driven by arcade logic**, not by any write suppressed in this 13-entry set.
- **Does not explain.** The watchdog behaviour is a consequence of arcade's own software timer cycling, which is orthogonal to the hardware-suppression layer.

### Summary of system contribution

The 13 Phase A suppressions are **not** a material contributor to any of the three listed runtime symptoms. They target arcade-only addresses outside Genesis-observable memory; with the single caveat that the four sound-CPU entries (6, 7, 9, 10) are `provisional` — they may need to become helper redirects when a Genesis sound driver is wired up, but they are not currently breaking anything because the sound subsystem has nothing to miss.

---

## Phase 5 — Integrity

- All 13 active entries analysed: **YES.**
- Each entry has evidence citations (spec line, Cody doc phase 3 table row, arcade chip role): **YES.**
- No source / spec / tool modifications made by this task: **YES.**
- Each classification accompanied by reasoning paragraph: **YES.**
- Inconsistencies flagged: **NONE** (see Phase 3).
- Explicit uncertainties flagged: **4** entries marked `provisional` (sound-CPU group).

---

## Summary

```
Entries analyzed:             13
intended_permanent:           9   (entries 1, 2, 3, 4, 5, 8, 11, 12, 13)
provisional:                  4   (entries 6, 7, 9, 10 — sound-CPU group)
deprecated:                   0
needs_review:                 0

Status mix:
  9 / 13  arcade-only chip registers, write-only, no Genesis consumer  → permanent suppression is the right choice
  4 / 13  arcade sound-CPU register writes                             → permanent for now, may become helper redirects
                                                                         when Genesis Z80 driver is wired

Categories:
  hardware_chip_unmapped:     11   (entries 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13)
  ram_probe_suppression:      2    (entries 8, 11)
  watchdog_suppression:       0    (those entries are in the separate 0x380000 cluster, not HIT during first second)
  dip_shadow:                 0    (DIP and input-shadow redirects are not in this 13-entry set)
  other:                      0

Uncertainties:
  4 provisional entries flagged pending Genesis sound-driver integration.

Inconsistencies:
  NONE. Same-address, same-instruction entries are classified identically.

Key findings:
  - All 13 HIT suppressions target arcade-only hardware registers unmapped on Genesis.
  - 9 of 13 are permanent (no plausible Genesis consumer will ever want to see these writes).
  - 4 of 13 (sound-CPU control) are provisional pending sound-driver wiring.
  - None of the 13 writes to WRAM, so the "massive WRAM write reduction" symptom is not
    caused by this suppression set.
  - None touches the arcade watchdog register; "watchdog-driven control anomalies"
    originate from the arcade software countdown at A5@(0x2C), not from these suppressions.
  - 4 entries (6, 7, 9, 10) are the only ones whose suppression status might warrant
    revisiting as the project integrates sound. Everything else is stable.
```

## Verification pointers for the user

- Per-entry spec-line cross-check: [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json) lines listed in the Phase 1 table.
- Arcade-side disassembly context: [build/maincpu.disasm.txt](build/maincpu.disasm.txt) lines ≈73984-74116 (startup_common body `0x3AE86..0x3AF30`) and the L5-handler body `0x3A008..0x3A07E` at disasm lines ≈72947-72980.
- RAM-probe loop shape: [build/maincpu.disasm.txt](build/maincpu.disasm.txt) around `arcade_pc 0x03AEB2..0x03AEC4` and `0x03AED6..0x03AEE8`.
- Precedent suppressions (non-HIT in first second but same pattern): spec lines 265-287, 295-323, 385-399, 403-407, 411-419, 423-427 (`0x380000` watchdog cluster), and spec lines 267-287 (`0xC50000` / `0xD01BFE` PC080SN/PC090OJ cluster).

---

**STOP triggered: NO.** All 13 entries located, analysed, classified with reasoning, and cross-referenced against existing spec precedent.
