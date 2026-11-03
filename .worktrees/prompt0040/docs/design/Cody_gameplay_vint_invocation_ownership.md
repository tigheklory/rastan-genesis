# Cody - Gameplay VINT Invocation Ownership Audit

**Date:** 2026-07-12
**Type:** Analysis-only source/static audit
**Working candidate:** Build 0162
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0162.bin`
**ROM SHA256:** `7bcb31790b2c6db44425655d486c0b74bf3a286a23e77b912594e7e78a9674b9`
**Accepted build policy:** Build 0160 remains accepted unless Tighe accepts a newer candidate.
**Scope:** No source/spec/tool/Makefile/ROM edits. No build. No broad runtime. No collision, PC080SN/FG_SRC, palette, or PC090OJ represent-logic work.

Address labels: `runtime_genesis_pc` = patched-ROM runtime/code address; `arcade_pc` = original arcade code address; `HW_ADDRESS` = hardware address; `Genesis-WRAM` = Genesis work RAM.

## 1. Baseline / Repo State

- Branch: `rastan-direct-proposal`
- HEAD: `9cea9e8`
- `git status --short` before this report: clean
- Build 0162 ROM SHA verified from disk: `7bcb31790b2c6db44425655d486c0b74bf3a286a23e77b912594e7e78a9674b9`
- Canonical constants inspected:
  - `tools/translation/postpatch_startup_rom.py`: `CANONICAL_OPCODE_REPLACE_COUNT = 137`, `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x1820AC`
  - `tools/translation/verify_canonical_rom.py`: same values

## 2. Phase 0 / Priors

Relevant priors from `KNOWN_FINDINGS.md`:

- **KF-011:** arcade Level-5/VBlank owns frame progression; Genesis VBlank is servicing-only.
- **KF-013:** text/producer dispatch inside arcade VBlank is expected, not itself a violation.
- **KF-001:** known VBlank-to-state-machine predecessor chain: Genesis Level-6 vector -> `_vblank_service` -> `runtime_genesis_pc 0x3A208` arcade VBlank handler.
- **KF-010:** BG/FG are committed through Genesis staging to Plane B/A.
- **KF-032:** raw copied PC080SN/PC090OJ hardware writes must route through staging, not VDP mirror space.
- **KF-043:** recent gameplay palette fixes explain CRAM population; they do not explain sprite prepare frequency.

Open issues touched as context: **OPEN-017**, **OPEN-024**, **OPEN-001**. CLOSED issues: none touched. Contradiction of CONFIRMED/STRONG finding: **NONE**.

Task classification: **EXTENDING**. This extends Andy's Build 0163 sprite-prepare activation-gate STOP by auditing VINT ownership rather than PC090OJ representation.

## 3. Current Andy Evidence Summary

From `docs/design/Andy_build0163_sprite_prepare_activation_gate.md` and `docs/design/Andy_gameplay_sat_link_management.md`:

- `vdp_prepare_sprites` is called unconditionally from `_vblank_service`.
- Therefore, if the measurement is an entry/call measurement, `vdp_prepare_sprites` frequency equals `_vblank_service` frequency.
- During Build 0162 gameplay, `_vblank_service` / `vdp_prepare_sprites` reportedly ran on only about 40% of gameplay frames.
- BG/palette can look stable because VRAM/CRAM retain prior commits, but sprites need recurring SAT maintenance/commit, so skipped service frames can leave stale/flickering SAT.
- Separate issue, intentionally not analyzed here: even when prepare runs, the represent engine froze at 6 and did not activate the 24 gameplay object records.

## 4. VINT Vector Ownership

**Installed vector.** Genesis Level-6 autovector vector 30 lives at ROM offset `0x000078`. Build 0162 ROM bytes show:

```text
0x000070: 00000466 00000466 000700c2 00000466
```

The longword at `0x000078` is `0x000700C2`, matching `_vblank_service` in `apps/rastan-direct/out/symbol.txt`:

```text
000700c2 T _vblank_service
```

**Source install.** `apps/rastan-direct/src/boot/boot.s` installs vector 30 directly:

```asm
.org 0x000000
...
.long _crash_stub_other             /* 29 */
.long _vblank_service               /* 30 */
.long _crash_stub_other             /* 31 */
```

**Postpatch/vector preservation.** `build/rastan-direct/address_map.json` marks `0x000000..0x0011A4` as `kind=preserved_vectors`, and `build/rastan-direct/rastan_direct_patch_manifest.json` records the same preserved low-ROM/vector block. `tools/translation/postpatch_startup_rom.py` preserves `0x000000..preserve_low_rom_end` after rewrite passes for `rastan_direct`, explicitly to keep the vector/header/bootstrap bytes intact.

**Overwrite assessment.** On 68000 Genesis there is no VBR relocation in this code path; vectors are fetched from address `0x000000`. In this ROM, that low region is ROM and postpatch-preserved. No inspected source path writes or copies vector data over the vector table. Because the vector table is ROM-resident and preserved, a later runtime overwrite of the active vector is not a credible source-level mechanism.

**Conclusion:** VINT vector installed and owned by Genesis low-ROM bootstrap/vector table. Vector-not-installed or vector-overwritten is refuted by source, ROM bytes, and address-map/manifest structure.

## 5. VDP VINT Enable Ownership

VDP register 1 is the Mode 2 register. In `apps/rastan-direct/src/vdp_comm.s`:

```asm
.equ VDP_REG_MODE2,         1
.equ VDP_MODE2_DISPLAY_OFF, 0x34
.equ VDP_MODE2_DISPLAY_ON,  0x74
```

Both `0x34` and `0x74` keep VINT-enable bit 5 set. They differ by display-enable bit 6.

Known source-level register-1 writers:

- `vdp_boot_setup`: initializes Mode 2 to `0x34` (display off, VINT enabled).
- `_vblank_service`: writes `0x34` before commits and `0x74` after sprite VRAM commit.
- `load_scene_tiles` in `scene_load.s`: saves SR, raises mask, writes `0x34`, uploads tile patterns, writes `0x74`, restores SR.

Other VDP-control writes in inspected source:

- `vdp_set_vram_write_addr` writes VRAM address commands to `VDP_CTRL`; not register 1.
- `vdp_commit_palette` / `vdp_commit_scroll` write CRAM/VSRAM/VRAM address commands; not register 1.
- `pc090oj_hooks.s` tile/SAT DMA writes registers `0x93..0x97` and DMA/VRAM control words through `VDP_CTRL`; not register 1.
- `tilemap_hooks.s` narrow FG commit temporarily changes autoincrement register 15 to `0x08`, then restores it to `0x02`; not register 1.

No full VDP register-shadow owner was found in the inspected code. Register ownership is immediate-command based, with dirty/staging variables for content but not a persistent Mode-2 shadow variable.

**Conclusion:** Known Genesis helper/source writes preserve VINT enable. A raw or corrupted write to `HW_ADDRESS 0x00C00004` during gameplay remains runtime-watchable, but no inspected source helper intentionally clears VINT enable.

## 6. 68K SR / Interrupt-Mask Ownership

Inspected source SR writers:

- `boot.s`: `_start` executes `move.w #0x2700,%sr` before bootstrap; this is boot-only.
- `scene_load.s`: `load_scene_tiles` saves SR, executes `ori.w #0x0700,%sr`, performs tile upload/display toggle, then restores SR.
- `pc090oj_hooks.s`: `.Lpc090oj_family_apply_record` saves SR, executes `ori.w #0x0700,%sr`, writes/syncs one PC090OJ mirror record, then restores SR.

Chained arcade VBlank SR handling in `build/genesis_postpatch.disasm.txt`:

```asm
3a208: 007c 0f00       oriw  #0x0f00,%sr
...
3a274: 4eb9 0005 5ea2  jsr   0x55ea2
3a27a: 027c f0ff       andiw #0xf0ff,%sr
3a27e: 4e73            rte
```

`ori.w #0x0f00,%sr` raises interrupt mask bits while inside the arcade VBlank body. `andi.w #0xf0ff,%sr` clears those interrupt-mask bits immediately before `rte`.

SR can mask level-6 interrupts when the interrupt priority mask is 6 or 7. The inspected helper critical sections do this intentionally, but they restore the previous SR. No inspected source path leaves SR permanently masked. However, if `_vblank_service` plus the chained arcade VBlank body is long enough to overlap the next VBlank interval, the CPU remains in an interrupt-context/masked chain and cannot re-enter `_vblank_service` for that interval. Static source can show this risk shape, but not the elapsed duration.

## 7. `_vblank_service` Entry / Exit Model

`_vblank_service` is entered by Genesis Level-6 VINT through vector 30. Its source model in `vdp_comm.s`:

```asm
_vblank_service:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     rastan_direct_update_inputs
    bsr     vdp_prepare_sprites
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg
    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_narrow_strips
    bsr     vdp_commit_sprites_vram
    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg
    tst.b   palette_dirty
    beq.s   .Lvs_skip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lvs_skip_palette:
    bsr     vdp_commit_scroll
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    jmp     (0x00003A208).l
```

Generated disassembly confirms the same order at `runtime_genesis_pc 0x700C2..0x70108`:

```asm
700c2: movem.l save
700c6: bsrw 0x71534       ; input
700ca: bsrw 0x7219c       ; vdp_prepare_sprites
700d2: bsrw 0x7007e       ; reg1 = 0x34 DISPLAY_OFF, VINT still enabled
700d6: bsrw 0x7010e       ; tiles
700da: bsrw 0x70138       ; BG
700de: bsrw 0x7182a       ; FG narrow + FG rows
700e2: bsrw 0x721e0       ; sprite VRAM/SAT commit
700ea: bsrw 0x7007e       ; reg1 = 0x74 DISPLAY_ON, VINT still enabled
700f6: bsrw 0x701d4       ; optional palette
70100: bsrw 0x701f4       ; scroll
70104: movem.l restore
70108: jmp 0x3a208        ; arcade VBlank body owns final rte
```

`_vblank_service` does **not** `rte`; it tail-jumps into the arcade VBlank handler. The arcade VBlank handler owns final interrupt return via `rte` at `runtime_genesis_pc 0x3A27E`. This matches project architecture: Genesis VBlank is service-only; arcade VBlank owns progression and return.

## 8. Arcade VINT Chain Model

The arcade VBlank body begins at `runtime_genesis_pc 0x3A208`. It raises SR mask, performs arcade VBlank/state dispatch, calls tail service `0x55EA2`, lowers SR mask, and executes `rte`.

This is architecturally intentional per KF-011/KF-013. It also means `_vblank_service` entry rate is coupled to the combined wall-clock/cycle duration of:

1. Genesis input update.
2. PC090OJ prepare.
3. Display-off tile/BG/FG/sprite VRAM work.
4. Display-on palette/scroll work.
5. Full arcade VBlank body `0x3A208..0x3A27E` and subcalls.

If that combined path remains active or masked across the next VBlank edge, a subsequent `_vblank_service` entry can be missed or coalesced. Static inspection identifies this as the strongest code-backed suspect, but it still requires cycle/VCounter runtime proof.

## 9. Frame Counter / Measurement Trust

Existing Build 0157 trace scripts under `states/traces/build_0157_gameplay_sprites/` use MAME Lua `emu.register_frame_done`, which is emulator-frame based, not a counter incremented by `_vblank_service`. Those older artifacts are not direct Build 0162 proof, but they show the team's usual external-frame measurement style.

Andy's Build 0162 report lists per-frame prepare-call presence/absence. If that measurement used an entry/write tap on `_vblank_service`/`vdp_prepare_sprites` and an external emulator frame counter, it is trustworthy for service-frequency. If it used a counter updated only by arcade/Genesis VBlank itself, it could undercount or self-confirm the missing-service condition.

Dirty flags cannot explain a direct `_vblank_service` or `vdp_prepare_sprites` entry measurement: `vdp_prepare_sprites` runs before display-off and before dirty-gated commits. Dirty flags can make a commit do little work, but they do not gate prepare.

Recommended next trust check: count four PCs against an external MAME frame index and cycle/VCounter timestamp:

- `_vblank_service` entry `runtime_genesis_pc 0x700C2`
- `_vblank_service` tail jump site `runtime_genesis_pc 0x70108`
- arcade VBlank entry `runtime_genesis_pc 0x3A208`
- arcade `rte` `runtime_genesis_pc 0x3A27E`

## 10. Candidate Root-Cause Matrix

| Candidate | Class | Evidence / rationale |
|---|---|---|
| VINT vector overwritten or not installed | **D - Refuted** | ROM vector 30 at `0x78` = `0x000700C2`; `boot.s` installs `_vblank_service`; address map/manifest preserve low vectors; no inspected copy/write path owns vector table later. |
| Known Genesis helper clears VDP VINT enable | **C - Unlikely** | Known Mode-2 writes are `0x34`/`0x74`, both VINT-enabled. Other inspected VDP_CTRL writes are VRAM/CRAM/VSRAM/DMA/autoinc, not reg1 disable. |
| Raw/corrupted VDP control write clears VINT enable | **B - Possible** | Not proven in source. Any runtime write to `VDP_CTRL` with register-1 value clearing bit 5 would explain missing VINT. Needs watchpoint on `HW_ADDRESS 0x00C00004`. |
| SR interrupt mask blocks level-6 | **B - Possible** | Source has deliberate `ori.w #0x0700,%sr` critical sections and arcade VBlank raises mask at `0x3A208`. All inspected helpers restore/clear mask, so permanent mask is not proven. Long masked occupancy remains possible. |
| `_vblank_service` chain to arcade VINT interfering with return/ack | **B - Possible** | Tail `jmp 0x3A208` is intentional architecture and final `rte` exists, so not inherently wrong. But entry/exit/ack timing should be measured with cycle/VCounter and VDP status/control observations. |
| Handler duration/reentrancy causing missed service | **A - Likely** | Code-backed strongest suspect: `_vblank_service` does input + PC090OJ prepare + tile/BG/FG/sprite commits + optional palette + scroll, then runs full arcade VBlank before `rte`. If this chain overlaps the next VBlank, re-entry is masked/not possible. Needs runtime duration proof. |
| Measurement counter artifact | **B - Possible** | Andy's conclusion should stand unless source evidence disproves it, but the exact frame source must be recorded. External MAME frame counter is good; self-counting inside VBlank would be suspect. |
| Scene/gameplay intentionally lowers sprite prepare rate | **D - Refuted for prepare frequency** | `vdp_prepare_sprites` is unconditional in `_vblank_service`; no scene/gameplay gate exists around the call. Lower game logic cadence cannot make prepare skip if VINT service enters. |
| Dirty flag makes it look like VINT did not run | **D - Refuted for entry measurements** | Dirty flags gate content commits, not `_vblank_service` entry or `vdp_prepare_sprites`. Prepare runs before dirty-gated visible commits. |
| `load_scene_tiles` masks VINT long enough during steady gameplay | **C - Unlikely for steady gameplay** | It raises SR and toggles display during scene loads, but not every steady gameplay frame. Could matter at transitions, not the reported continuing gameplay rate by itself. |
| PC090OJ family critical sections mask VINT long enough | **B - Possible contributor** | `.Lpc090oj_family_apply_record` raises SR around mirror write/sync/clear. It restores SR per record. Many producer records could add masked time, but static inspection does not prove it reaches frame-scale. |

## 11. Most Likely Next Runtime Watchpoints for Andy

1. **VINT service chain timing**
   - Watch PCs: `0x700C2`, `0x70108`, `0x3A208`, `0x3A27E`.
   - Log: external frame number, cycle, VCounter/HCounter if available, SR.
   - Expected good: one `0x700C2 -> 0x70108 -> 0x3A208 -> 0x3A27E` chain per displayed frame, completing before the next VBlank edge.
   - Failure meaning: missing entries or overlong chains prove duration/reentrancy/masking as the service-rate cause.

2. **VDP register 1 / control-port writes**
   - Watch `HW_ADDRESS 0x00C00004` writes.
   - Decode 16-bit register writes where `(word & 0xFF00) == 0x8100`.
   - Expected good values: `0x8134` or `0x8174`; both keep VINT enable bit 5 set.
   - Failure meaning: any `0x81xx` with bit 5 clear proves VINT-enable clobber.

3. **SR mask writes / high-mask duration**
   - Watch source PCs: `0x3A208`, `0x3A27A`, `0x71BDC`, `0x71C14`, and scene-load SR save/restore sites (`0x72E46` / `0x72EB0` in current generated disassembly).
   - Expected good: masks are short and restored before the next VBlank edge.
   - Failure meaning: SR remains at IPM >= 6 through VBlank, blocking Level-6 entry.

4. **Vector sanity**
   - Watch ROM offset `0x000078` for writes, if emulator can report attempted ROM writes.
   - Expected good: no writes; longword remains `0x000700C2`.
   - Failure meaning: unexpected low-ROM write attempt, probably not effective on real ROM but useful evidence of stray memory corruption.

5. **Measurement source sanity**
   - Use MAME/host frame callback or VCounter-derived frame boundary, not a counter maintained inside `_vblank_service` or arcade VBlank.
   - Expected good: external frame count advances every video frame regardless of missed service.
   - Failure meaning: if the only frame counter is VBlank-owned, it cannot independently prove missed VINTs.

## 12. Recommended Next Andy Task

Run a bounded runtime timing trace for Build 0162 (or the current successor candidate if Tighe chooses it) over the gameplay window where prepare was observed at about 40%. Capture only:

- `_vblank_service` entry/tail and arcade VBlank entry/RTE counts per external frame.
- VDP register-1 writes and values.
- SR/IPM changes at the listed mask sites.
- Cycle/VCounter duration across the combined Genesis-service + arcade-VBlank chain.

Do **not** change source, do not fix PC090OJ represent logic, and do not broaden into collision/PC080SN/palette until the VINT ownership chain is proven.

## 13. Files Inspected

- `AGENTS.md`
- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- `KNOWN_FINDINGS.md`
- `docs/design/Andy_build0163_sprite_prepare_activation_gate.md`
- `docs/design/Andy_gameplay_sat_link_management.md`
- `docs/design/Andy_gameplay_sprite_path_ownership.md`
- `docs/design/Andy_gameplay_palette_lines_0_1_population.md`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/boot/boot.s` (needed for vector ownership)
- `apps/rastan-direct/src/scene_load.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/palette_hooks.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `specs/rastan_direct_remap.json`
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/startup_common_relocations.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `build/genesis_postpatch.disasm.txt`
- `build/maincpu.disasm.txt`
- `states/traces/build_0157_gameplay_sprites/`
- `dist/rastan-direct/rastan_direct_video_test_build_0162.bin` (SHA/vector-byte verification only)

## 14. Files Changed

- Created `docs/design/Cody_gameplay_vint_invocation_ownership.md`.
- No source/spec/tool/Makefile/ROM/build artifact changes.

## 15. Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024, OPEN-001.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: PC090OJ represent freeze, collision, PC080SN/FG_SRC, palette, gameplay scroll, raw-write inventory, visual fixes.

## 16. KNOWN_FINDINGS Impact

Option A - no new finding to index. This audit narrows the VINT ownership hypotheses but does not prove a durable root-cause mechanism. A KF update should wait for the bounded timing trace to distinguish overlong/masked service from VDP-reg1 clobber or measurement artifact.

## 17. Architecture Compliance

CONFIRMED. The audit preserves the architecture: arcade VBlank remains frame/progression owner; Genesis `_vblank_service` is treated as a hardware-service chain that stages/commits and tail-jumps back to the arcade VBlank. No source changes, no alternate renderer/SAT path, no diagnostic ROM, and no Genesis-owned gameplay lifecycle were introduced.

## 18. STOP Status

STOP triggered: **NO**. Analysis completed. Root cause not confirmed; next step is bounded runtime timing evidence.
