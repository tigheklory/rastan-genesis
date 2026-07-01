# Cody - Sprite (PC090OJ) + Window Layer Build-State Inventory

**Date:** 2026-06-30
**Build context:** Build 0120, `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**Build SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Type:** Evidence / audit only
**Scope:** Sprite (PC090OJ) and Genesis Window-layer build-state inventory. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark. No runtime probing. No fix design.

Address labels used below:

- `arcade_pc`: original arcade maincpu address.
- `runtime_genesis_pc`: Build 0120 runtime PC / ROM offset.
- `Genesis-WRAM`: Genesis work RAM address.
- `HW_ADDRESS`: hardware address as seen by the translated 68000.

All arcade-to-Genesis code correlations below were checked through `build/rastan-direct/address_map.json`; arithmetic offsets are not used as proof.

## Phase 0

Read for this audit: `RULES.md`, `ARCHITECTURE.md`, `AGENTS.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, the latest `AGENTS_LOG.md` tail, `specs/rastan_direct_remap.json`, `build/rastan-direct/address_map.json`, `apps/rastan-direct/src/vdp_comm.s`, `apps/rastan-direct/src/pc090oj_hooks.s`, `apps/rastan-direct/src/pc090oj_assets.s`, `apps/rastan-direct/out/symbol.txt`, `build/maincpu.disasm.txt`, and `build/genesis_postpatch.disasm.txt`.

Classification: **EXTENDING**. This audit touches OPEN-024 and OPEN-023 directly, with OPEN-006, OPEN-021, OPEN-001, and OPEN-015 as context. No issue is closed. No new issue is opened because the unresolved sprite and Window findings below are already covered by the existing OPEN issue set.

Contradiction detected: **NO**.

## Executive Summary

Sprite status: **partial implementation exists, but PC090OJ is not complete.** Build 0120 has a real Genesis sprite staging path (`staged_sprite_sat`, descriptor staging, dirty flag, sprite tile DMA, SAT DMA to VRAM `0xF800`) and a set of PC090OJ opcode replacements routed through `pc090oj_hooks.s`. However, copied arcade routines that still write raw `HW_ADDRESS 0x00D0xxxx` remain in the executable image. OPEN-024 should remain open.

Window status: **not implemented as a translated game-rendering layer.** The Genesis VDP Window registers are initialized, but project evidence says the Window is disabled/zero-sized in practice, and there is no `staged_window_buffer`, no Window dirty flag, no Window commit helper, and no current game element routed to the Window layer. OPEN-023 should remain open.

Layer separation: current title/story/high-score/item text work is PC080SN BG/FG staging into Genesis Plane B / Plane A, not Genesis Window. Some score/HUD digit work is routed through PC090OJ sprite helpers into SAT slots, but that does not make the Window layer active.

## Sprite / PC090OJ Inventory

### Hardware Contract

Per project architecture, arcade `HW_ADDRESS 0x00D00000..0x00D03FFF` is PC090OJ object/sprite RAM. On Genesis this hardware address range aliases VDP port space unless translated. Correct Build 0120 behavior therefore requires sprite writers to route into Genesis sprite staging/SAT, not raw `0x00D0xxxx` hardware writes.

### Present Genesis Sprite Infrastructure

Symbols from `apps/rastan-direct/out/symbol.txt`:

| Symbol | Address space | Address | Purpose |
|---|---|---:|---|
| `staged_sprite_sat` | `Genesis-WRAM` | `0x00FF6104` | 80 Genesis SAT entries, 8 bytes each |
| `staged_sprite_descriptor_table` | `Genesis-WRAM` | `0x00FF6384` | Per-slot semantic sprite descriptors |
| `staged_sprite_dirty` | `Genesis-WRAM` | `0x00FF6744` | Dirty/touched state |
| `staged_sprite_active_count` | `Genesis-WRAM` | `0x00FF6748` | Active sprite count |
| `rastan_pc090oj` | `runtime_genesis_pc` / ROM | `0x000722DC` | Preconverted PC090OJ graphics data |
| `pc090oj_slot_lut` | `runtime_genesis_pc` / ROM | `0x000F22DC` | Slot lookup data |
| `vdp_commit_sprites` | `runtime_genesis_pc` | `0x00071ECC` | VBlank sprite commit helper |

`apps/rastan-direct/src/vdp_comm.s` initializes Genesis VDP register 5 to `0x7C`, setting the SAT base to VRAM `0xF800`. `_vblank_service` calls `vdp_commit_sprites` once per VBlank after tile/BG/FG commits and before palette/scroll/display-on.

`apps/rastan-direct/src/pc090oj_hooks.s` contains a real sprite staging route:

- `.Lpc090oj_emit_slot` emits semantic sprite state into `staged_sprite_descriptor_table` and `staged_sprite_sat`.
- The route uses 80 SAT slots.
- SAT word 0 is transformed Y with Genesis sprite bias/mask.
- SAT word 1 defaults to size/link data; `vdp_commit_sprites` later rebuilds link bits.
- SAT word 2 uses priority, palette bits, flip bits, and a tile index derived from the slot.
- SAT word 3 is transformed X with Genesis sprite bias/mask.
- Invalid/clear slots are converted into inactive SAT entries and marked dirty.
- `vdp_commit_sprites` uploads changed sprite tiles from `rastan_pc090oj` to VRAM tile slots, DMAs `staged_sprite_sat` to VRAM `0xF800`, and clears dirty/touched state.

Interpretation: the project is not missing a sprite subsystem entirely. The current issue is coverage/completeness of PC090OJ producer routing and exact sprite semantics, not total absence of sprite staging.

### Routed PC090OJ Opcode-Replacement Surface

The following current patched sites were verified through `build/rastan-direct/address_map.json`. They are current routed sprite-related coverage, not proof of full PC090OJ completeness.

| `arcade_pc` | `runtime_genesis_pc` | Map kind | Current role |
|---:|---:|---|---|
| `0x03AD44` | `0x03AF44` | `patched_site` | PC090OJ + tilemap polymorphic utility dispatch |
| `0x03AD84` | `0x03AF84` | `patched_site` | PC090OJ priority-frame/init route |
| `0x03B802` | `0x03BA02` | `patched_site` | Score/HUD digit sprite route |
| `0x03B902` | `0x03BB02` | `patched_site` | Sprite writer route, slots `0..4` per spec note |
| `0x03B926` | `0x03BB26` | `patched_site` | Sprite writer route, slots `5..13` per spec note |
| `0x03B930` | `0x03BB30` | `patched_site` | Sprite helper route, slots `14..17` per spec note |
| `0x041DAE` | `0x041FAE` | `patched_site` | 18-sprite frame route, slots `0..17` per spec note |
| `0x041F5E` | `0x04215E` | `patched_site` | Sprite route, slots `18..21` per spec note |
| `0x045DFA` | `0x045FFA` | `patched_site` | Sprite route, slots `0..21` per spec note |
| `0x0510EA` | `0x0512EA` | `patched_site` | PC090OJ audit guard |
| `0x0510F4` | `0x0512F4` | `patched_site` | PC090OJ audit guard |
| `0x054052` | `0x054252` | `patched_site` | Sprite-slot init route, slots `72..75` per spec note |
| `0x054810` | `0x054A10` | `patched_site` | Sprite update route, slots `44..55` per spec note |
| `0x05607C` | `0x05627C` | `patched_site` | Sprite-decay route, slots `56..63` per spec note |
| `0x056114` | `0x056314` | `patched_site` | Sprite copy route, slots `64..67` per spec note |
| `0x056440` | `0x056640` | `patched_site` | Sprite zero-fill route, slots `68..71` per spec note |
| `0x059F5E` | `0x05A15E` | `patched_site` | Sprite clear route, slots `0..7` per spec note |
| `0x05A098` | `0x05A298` | `patched_site` | Status/UI sprite route, slots `30..43` per spec note |

Relevant hook symbols include `genesistan_hook_3ad44_dispatch`, `genesistan_pc090oj_hook_init_priority_3ad84`, `genesistan_pc090oj_hook_score_digit_3b802`, `genesistan_pc090oj_hook_target_3b902`, `genesistan_pc090oj_hook_target_3b926`, `genesistan_pc090oj_hook_target_3b930`, `genesistan_pc090oj_hook_target_41dae`, `genesistan_pc090oj_hook_target_41f5e`, `genesistan_pc090oj_hook_target_45dfa`, `genesistan_pc090oj_hook_slot_init_54052`, `genesistan_pc090oj_hook_sprite_update_54810`, `genesistan_pc090oj_hook_sprite_decay_5607c`, `genesistan_pc090oj_hook_copy_56114`, `genesistan_pc090oj_hook_zero_fill_56440`, `genesistan_pc090oj_hook_target_59f5e`, and `genesistan_pc090oj_hook_status_sprite_5a098`.

### Remaining Raw PC090OJ Writer Gaps

The following concrete copied arcade routines still contain raw PC090OJ writes. These are not an exhaustive dynamic proof of every possible raw sprite path, but they are executable copied code sites verified through `build/rastan-direct/address_map.json`.

| `arcade_pc` | `runtime_genesis_pc` | Kind | Evidence |
|---:|---:|---|---|
| `0x0510C8` | `0x0512C8` | `arcade_copy` | Loads `HW_ADDRESS 0x00D00000` into `%a0` |
| `0x0510CE` | `0x0512CE` | `arcade_copy` | Writes PC090OJ words through `%a0@+` |
| `0x052AA2` | `0x052CA2` | `arcade_copy` | Loads `HW_ADDRESS 0x00D00000` into `%a1` |
| `0x052ABE` | `0x052CBE` | `arcade_copy` | Four-slot PC090OJ writer loop through `%a1@+` |
| `0x05A502` | `0x05A702` | `arcade_copy` | Copied routine containing `HW_ADDRESS 0x00D00298` writer |
| `0x05A51E` | `0x05A71E` | `arcade_copy` | Loads `HW_ADDRESS 0x00D00298` into `%a0` |
| `0x05A524` | `0x05A724` | `arcade_copy` | First raw write to `%a0@+` after `0x00D00298` load |
| `0x05A554` | `0x05A754` | `arcade_copy` | Loads `HW_ADDRESS 0x00D002B0` into `%a0` |
| `0x05A55A` | `0x05A75A` | `arcade_copy` | Writes raw PC090OJ words through `%a0@+` |

Local disassembly evidence:

```asm
; arcade_pc 0x0510C8, runtime_genesis_pc 0x0512C8
movea.l #0x00D00000,%a0
; later words are written through (%a0)+
```

```asm
; arcade_pc 0x052AA2, runtime_genesis_pc 0x052CA2
movea.l #0x00D00000,%a1
; loop writes multiple PC090OJ entries through (%a1)+
```

```asm
; arcade_pc 0x05A51E, runtime_genesis_pc 0x05A71E
movea.l #0x00D00298,%a0
; arcade_pc 0x05A524, runtime_genesis_pc 0x05A724
move.w #0x0000,(%a0)+
```

The `HW_ADDRESS 0x00D00298` path is consistent with the manual BlastEm fatal discussed in the Build 0120 D00298 evidence chain, but the current audit does not add runtime proof. It records only that a copied executable PC090OJ writer remains and is a plausible raw-hardware hazard.

### Sprite Build-State Classification

Sprite route classification: **partial / incomplete**.

Proven:

- Genesis sprite staging, sprite descriptor staging, SAT commit, sprite tile DMA, and PC090OJ graphics assets exist.
- Multiple PC090OJ producer functions are opcode-replaced and route into sprite staging.
- At least three copied arcade routines still contain raw `HW_ADDRESS 0x00D0xxxx` PC090OJ writes.

Not proven by this audit:

- That every sprite visual defect is caused by the listed raw writers.
- That sprite palette/high-bank mapping is correct.
- That sprite priority/link/size semantics are fully arcade-equivalent.
- That the D00298 BlastEm fatal path is dynamically identical to MAME behavior.

## Genesis Window Layer Inventory

### Boot Configuration

`apps/rastan-direct/src/vdp_comm.s` defines and initializes Genesis Window registers:

| VDP register | Source name | Boot value | Current project interpretation |
|---:|---|---:|---|
| `3` | `VDP_REG_WINDOW` | `0x3C` | Window nametable base, prior audit records VRAM `0xF000` |
| `17` | `VDP_REG_WINDOW_X` | `0x00` | Window X position/enable state |
| `18` | `VDP_REG_WINDOW_Y` | `0x00` | Window Y position/enable state |

Per existing project audit (`docs/design/Andy_post_plane_b_fix_palette_audit.md`), Window X/Y zero leaves the Window effectively disabled / covering no visible columns or rows. This audit did not re-derive Genesis VDP Window hardware behavior from external docs.

### No Window Staging or Commit Path Found

Source and symbol searches found no active Window translation path:

- No `staged_window_buffer`.
- No `window_dirty`.
- No `vdp_commit_window`.
- No Window producer hook.
- No game-element route that writes a Window staging buffer.

Current architecture in `AGENTS.md` says arcade BG layer maps to Genesis Plane B and arcade FG/text/HUD maps to Genesis Plane A; no separate text Window layer exists in the current port architecture.

### Window Build-State Classification

Window route classification: **configured but not game-active / not implemented as a translation target**.

Proven:

- VDP Window base register is initialized at boot.
- No staged Window buffer or commit helper exists in current source/symbols.
- Current PC080SN BG/FG text/artwork paths target Plane B / Plane A staging, not Window.

Not proven by this audit:

- That no future design should use Window.
- That every visible artifact is unrelated to Window.
- That Window register values are ideal for all modes.

## Element / Layer Matrix

| Element class | Arcade source | Current Genesis target | Build-state note |
|---|---|---|---|
| Title logo / title art | PC080SN BG C-window | Plane B staging (`staged_bg_buffer`) | Active area of OPEN-001 / title graphics work |
| Title/story/credits text | PC080SN FG C-window | Plane A staging (`staged_fg_buffer`) | Active PC080SN text route, not Window |
| High-score NAME/SCORE/ROUND text | PC080SN FG C-window | Plane A staging | OPEN-021 remains for SCORE/ROUND source provenance |
| Item-description text | PC080SN BG C-window | Plane B staging | Build 0115+ evidence; long-row aliasing tracked separately |
| Score/HUD digit sprites | PC090OJ | SAT staging via `genesistan_pc090oj_hook_score_digit_3b802` | Sprite path component; does not activate Window |
| Gameplay/enemy/object sprites | PC090OJ | SAT staging where routed | Partial; raw PC090OJ copied writers remain |
| Genesis Window | None proven in current game route | None active | OPEN-023 remains open |

## Issue Impact

- **OPEN-024:** Remains open. This audit supports the existing classification that sprite support is incomplete: routed PC090OJ helpers exist, but copied raw PC090OJ writers remain.
- **OPEN-023:** Remains open. Window registers are initialized, but no active game-rendering Window staging/commit path exists.
- **OPEN-006:** Remains open. This audit did not prove sprite high-bank/palette correctness; `pc090oj_hooks.s` derives palette bits, but no arcade-vs-Genesis sprite palette equivalence was measured here.
- **OPEN-021:** Remains open. This audit does not resolve high-score SCORE/ROUND source provenance.
- **OPEN-001:** Context only. Sprite/Window state is separate from the current PC080SN BG/FG graphics-output problem, though all affect visible rendering.
- **OPEN-015:** Context only. No crash-handler work was performed; any crash-screen numeric fields remain subject to OPEN-015 reliability limits.
- **Closed issues:** No closed issue is reopened by this audit.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update from this audit alone. The audit inventories current subsystem coverage and known open gaps, but it does not establish a new durable mechanism beyond existing OPEN issue coverage.

## STOP

STOP triggered: **NO**.

