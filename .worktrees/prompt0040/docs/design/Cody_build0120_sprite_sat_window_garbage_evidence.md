# Cody - Build 0120 Sprite SAT + Window Garbage Evidence

**Date:** 2026-06-30
**Build:** 0120
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Type:** Evidence only / build-state audit
**Scope:** Sprite SAT one-entry evidence, PC090OJ producer reachability inventory, and Window VRAM garbage reconciliation. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark. No runtime probing. No implementation. No fix design.

Address labels used below:

- `arcade_pc`: original arcade maincpu code address.
- `runtime_genesis_pc`: Build 0120 runtime PC.
- `genesis_rom_offset`: Build 0120 ROM file offset. For mapped code sites below, the JSON map places runtime PC and file offset at the same value.
- `Genesis-WRAM`: Genesis work RAM address.
- `HW_ADDRESS`: 68000 hardware address as executed by the translated program.
- `PC090OJ address`: arcade object/sprite hardware address in the `HW_ADDRESS 0x00D00000..` range.
- `VDP address`: Genesis VDP port address.
- `VRAM address`: Genesis VDP VRAM address.

All arcade-to-Genesis code correlations in this note use `build/rastan-direct/address_map.json`; no arithmetic offset is used as proof.

## Phase 0

Read for this task: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `docs/design/Cody_sprite_window_buildstate_inventory.md`, `AGENTS_LOG.md` tail, `apps/rastan-direct/src/vdp_comm.s`, `apps/rastan-direct/src/pc090oj_hooks.s`, `apps/rastan-direct/src/boot/boot.s`, `apps/rastan-direct/src/scene_load.s`, `specs/rastan_direct_remap.json`, `build/rastan-direct/address_map.json`, `apps/rastan-direct/out/symbol.txt`, `build/maincpu.disasm.txt`, and `build/genesis_postpatch.disasm.txt`.

Classification: **EXTENDING** OPEN-024 and OPEN-023. OPEN-006, OPEN-021, OPEN-001, and OPEN-015 are context. No issue is closed or renamed. No new issue is opened because the one-sprite and Window-garbage evidence are covered by OPEN-024 and OPEN-023.

User-provided Exodus evidence inspected:

- `states/screenshots/build_120/Exodus_build_120_story_screen_window_boundaries_off.png`
- `states/screenshots/build_120/Exodus_build_120_title_screen_window_boundaries_on.png`

Visual observations from those screenshots:

- Story screen: Layer A contains story text and credit text; Layer B contains the king/figure artwork. The Sprite pane shows one small outlined sprite-like box. The Window pane shows repeated purple/magenta patterned bands and small colored/white elements.
- Title screen: Layer A contains TAITO/copyright/credit text; Layer B contains the RASTAN/sword title art. The Sprite pane again shows one small outlined sprite-like box. The Window pane again shows repeated patterned bands.
- These screenshots support the user observation that the king/figure is tilemap/Plane-B output, not the sprite layer, and that the visible Sprite-pane state is a single persistent entry, not a populated PC090OJ sprite set.

## Part A - Genesis SAT / One-Junk-Sprite Evidence

### A1. SAT Staging Model

Current symbols from `apps/rastan-direct/out/symbol.txt`:

| Symbol | Address space | Address | Evidence role |
|---|---|---:|---|
| `staged_sprite_sat` | `Genesis-WRAM` | `0x00FF6104` | 80 staged Genesis SAT entries, 8 bytes each |
| `staged_sprite_descriptor_table` | `Genesis-WRAM` | `0x00FF6384` | 80 semantic sprite descriptors, 12 bytes each |
| `staged_sprite_dirty` | `Genesis-WRAM` | `0x00FF6744` | Dirty block bitset |
| `staged_sprite_active_count` | `Genesis-WRAM` | `0x00FF6748` | Count of descriptors with valid bit set during link build |
| `vdp_commit_sprites` | `runtime_genesis_pc` / `genesis_rom_offset` | `0x00071ECC` | VBlank sprite commit helper; `genesis_only` map segment `0x00070000..0x0017D017` |

`apps/rastan-direct/src/vdp_comm.s` calls `vdp_commit_sprites` once per `_vblank_service`, after BG/FG commits and before palette/scroll/display-on. VDP register 5 is initialized to `0x7C`, so the SAT base is `VRAM address 0xF800`.

### A2. Inactive Entry Representation

There are two inactive-entry shapes in the current code:

- Boot-clear staging shape from `apps/rastan-direct/src/boot/boot.s`: `staged_sprite_sat` and `staged_sprite_descriptor_table` are zeroed. A boot-zero SAT slot is therefore `[word0=0x0000, word1=0x0000, word2=0x0000, word3=0x0000]`.
- Explicit helper-clear shape from `.Lpc090oj_emit_invalid` in `apps/rastan-direct/src/pc090oj_hooks.s`: descriptor word0 becomes `0x8000` before commit, and SAT words become `[0x0000, 0x0500, 0x0000, 0x0000]`. After `.Lvcs_clear_dirty`, descriptor word0 is masked with `0x7FFF`, so the touched bit is cleared and descriptor word0 becomes invalid (`0x0000`) unless another valid bit remains.

Slot 0 is not special in the code: the link builder scans slots `0..79` and treats any descriptor with bit 0 set as valid. However, Genesis SAT link semantics make slot/link termination behavior visually important: if slot 0 has a visible Y/tile/X tuple and its link terminates, it can be the only visible sprite.

### A3. SAT Clear / Link Termination Status

`vdp_commit_sprites` always runs four phases:

1. `.Lvcs_link_chain_build`
2. `.Lvcs_tile_dma`
3. `.Lvcs_sat_dma`
4. `.Lvcs_clear_dirty`

What it does:

- Recomputes links among descriptors whose descriptor word0 bit 0 is set.
- Sets the previous valid slot link to the next valid slot.
- Sets the final valid slot word1 to `0x0500`, leaving link bits zero for termination.
- DMAs the full 640-byte `staged_sprite_sat` buffer to `VRAM address 0xF800` every VBlank.
- Clears `staged_sprite_dirty` and clears only descriptor touched bit 15.

What it does **not** do:

- It does not sweep all unused `staged_sprite_sat` entries to hidden values every VBlank.
- It does not clear descriptor valid bit 0 during `.Lvcs_clear_dirty`.
- It does not use `staged_sprite_active_count` to zero/trim SAT entries after the last active sprite.
- It does not independently clear `VRAM address 0xF800..0xFA7F`; it overwrites VRAM SAT by DMA from whatever is currently in `staged_sprite_sat`.

Therefore, if a slot becomes valid once and no later routed helper clears that slot, the descriptor can remain valid and the staged SAT entry can persist across title/story pages. Conversely, if all descriptors are invalid and `staged_sprite_sat` is zeroed, the Sprite pane's one outlined box may be a viewer representation of a zero/terminated SAT, not an active game sprite. The screenshot alone does not distinguish these.

### A4. Code Capable of Creating Exactly One Active SAT Entry

Candidate routes, from code evidence rather than names alone:

- `.Lpc090oj_emit_slot`: any routed helper that calls this once with a valid tuple can create one active slot.
- `genesistan_pc090oj_hook_target_3b930`: loops up to four entries from `%a0`; if the caller count is one, it can emit exactly one valid slot in the `14..17` range.
- `genesistan_pc090oj_hook_copy_56114`: copies a descriptor list into slots `64..67` until `0xFFFF`; a one-entry list can emit exactly one active slot.
- `genesistan_pc090oj_hook_sprite_decay_5607c`: iterates slots `56..63` and re-emits only descriptors whose valid bit is already set, so it can preserve or update a single stale valid sprite.
- `genesistan_pc090oj_hook_score_digit_3b802` and `genesistan_pc090oj_hook_status_sprite_5a098`: can emit multiple score/status entries, but their paths are screen/state dependent and are not proven to be active on the shown title/story screenshots.
- `genesistan_pc090oj_hook_init_priority_3ad84`: emits slots `76..79` with tile zero, which `.Lpc090oj_emit_slot` treats as invalid. It should not create a visible sprite by itself.
- Clear helpers (`3b926`, `59f5e`, `56440`, and the PC090OJ branch in `3ad44`) should produce invalid/hidden SAT entries, not one visible sprite, unless stale validity/link state elsewhere remains.

### A5. Cross-Screen Persistence Lever

The user evidence says the single Sprite-pane entry is persistent and apparently unchanged across title and story pages.

Static evidence is more consistent with **STALE / never-cleared entry** than with a healthy active sprite set:

- `vdp_commit_sprites` does not clear every unused staged SAT slot every VBlank.
- `.Lvcs_clear_dirty` clears touched bit 15 only, not valid bit 0.
- A valid descriptor can remain active until a specific helper clears that slot.
- The title/story screenshots do not show a populated changing sprite set; they show one small persistent boxed entry.

However, **actively rewritten bad entry** remains possible until runtime evidence proves whether the staged SAT entry changes over time.

Smallest runtime check to settle it:

- Use an emulator/debugger that can dump memory and VRAM around `runtime_genesis_pc 0x00071ECC` (`vdp_commit_sprites`). MAME debugger can use breakpoints and memory dumps; Exodus can inspect VDP/SAT visually; BlastEm lacks data watchpoints, so use breakpoints/snapshots rather than watchpoints there.
- Break immediately before `vdp_commit_sprites` and immediately after it on both title and story pages.
- Dump `Genesis-WRAM 0x00FF6104..0x00FF6383` (`staged_sprite_sat`), `Genesis-WRAM 0x00FF6384..0x00FF6743` (`staged_sprite_descriptor_table`), `Genesis-WRAM 0x00FF6744` (`staged_sprite_dirty`), `Genesis-WRAM 0x00FF6748` (`staged_sprite_active_count`), and `VRAM address 0xF800..0xFA7F` (SAT).
- If the same nonzero/still-valid slot persists with no producer hits, classify stale. If it is rewritten every frame or page by a helper PC, classify active bad producer.

### A6. One-Sprite Classification

Current classification: **unresolved, leaning stale `staged_sprite_sat` / stale valid descriptor or viewer-visible zero/termination artifact**.

Not enough evidence for:

- healthy expected sprite output,
- full uninitialized SAT VRAM, because `vdp_commit_sprites` DMAs staged SAT to `VRAM address 0xF800` every VBlank,
- raw PC090OJ writer bypassing staging as the direct cause of this specific visible one-sprite state, because no runtime writer for this one slot was captured.

## Part B - PC090OJ Producer Reachability

### B1. Routed PC090OJ Hook Likely Use

The following table uses exact JSON map fields and spec/source evidence. Function-name-only conclusions are marked tentative.

| Hook / site | `arcade_pc` | `runtime_genesis_pc` / `genesis_rom_offset` | Map kind | Likely use | Evidence |
|---|---:|---:|---|---|---|
| `genesistan_hook_3ad44_dispatch` | `0x03AD44` | `0x03AF44` | `patched_site` | title/story clear utility plus tilemap utility | Spec note: 3 PC090OJ-targeting callers route bulk-clear slots `76..79`; 4 tilemap callers route BG/FG/scroll fills. |
| `genesistan_pc090oj_hook_init_priority_3ad84` | `0x03AD84` | `0x03AF84` | `patched_site` | title/attract priority-frame init, tentative | Spec note: callers through `0x3AD72`, slots `76..79`, D00778-origin priority-frame context. Tile zero makes emitted slots invalid. |
| `genesistan_pc090oj_hook_score_digit_3b802` | `0x03B802` | `0x03BA02` | `patched_site` | gameplay/status/HUD | Spec note: 10 score/HUD digit callers; code maps score-data source into slots `22..29`. |
| `genesistan_pc090oj_hook_target_3b902` | `0x03B902` | `0x03BB02` | `patched_site` | title/attract/VBlank sprite utility, exact screen unknown | Spec note: callers include VBlank/state-region sites; helper emits or clears slots `0..4`. |
| `genesistan_pc090oj_hook_target_3b926` | `0x03B926` | `0x03BB26` | `patched_site` | clear utility, exact screen unknown | Code clears slots `5..13`. |
| `genesistan_pc090oj_hook_target_3b930` | `0x03B930` | `0x03BB30` | `patched_site` | init/helper writer, exact screen unknown | Spec note: reached from init function `0x3B8B0`; code emits up to slots `14..17` from `%a0`. |
| `genesistan_pc090oj_hook_target_41dae` | `0x041DAE` | `0x041FAE` | `patched_site` | gameplay/object sprites | Spec note and code: emits Block-A 18-sprite frame to slots `0..17`. |
| `genesistan_pc090oj_hook_target_41f5e` | `0x041F5E` | `0x04215E` | `patched_site` | gameplay/object sprites | Spec note/code: emits/copies Block-B to slots `18..21`. |
| `genesistan_pc090oj_hook_target_45dfa` | `0x045DFA` | `0x045FFA` | `patched_site` | gameplay/object sprites | Spec note/code: alternate 22-sprite frame emitter, slots `0..21`. |
| `genesistan_pc090oj_hook_slot_init_54052` | `0x054052` | `0x054252` | `patched_site` | item/status/setup | Code preserves C-chip text-RAM clears and emits slots `72..75`; exact screen is not proven here. |
| `genesistan_pc090oj_hook_sprite_update_54810` | `0x054810` | `0x054A10` | `patched_site` | gameplay/object update | Code uses scroll/position offsets and table records to emit four slots per call into `44..55`. |
| `genesistan_pc090oj_hook_sprite_decay_5607c` | `0x05607C` | `0x05627C` | `patched_site` | gameplay/object decay | Code decrements Y on existing valid slots `56..63`. |
| `genesistan_pc090oj_hook_copy_56114` | `0x056114` | `0x056314` | `patched_site` | gameplay/object copy | Code copies descriptor list into slots `64..67`. |
| `genesistan_pc090oj_hook_zero_fill_56440` | `0x056440` | `0x056640` | `patched_site` | clear utility | Code clears slots `68..71`. |
| `genesistan_pc090oj_hook_target_59f5e` | `0x059F5E` | `0x05A15E` | `patched_site` | title/status/item clear utility, exact screen unknown | Spec note: clears slots `0..7`; callers include `0x051266`, `0x0519A0`, `0x055E18`. |
| `genesistan_pc090oj_hook_status_sprite_5a098` | `0x05A098` | `0x05A298` | `patched_site` | status/UI | Code emits slots `30..43`; spec note says status/UI sprite descriptors. |
| `genesistan_pc090oj_hook_audit_guard` | `0x0510EA` / `0x0510F4` | `0x0512EA` / `0x0512F4` | `patched_site` | guarded raw PC090OJ writes, reachability previously zero in FU1 | Spec notes say 0 hits in observed boot+attract+demo gameplay and helper halts if reached. |

Routed helper capability for title/story sprites today: **not proven**. The title/story screenshots show tilemap content on Plane A/B and one Sprite-pane entry, but no trace proves routed PC090OJ producers are intentionally producing title/story sprites on those pages.

### B2. Remaining Raw PC090OJ Writer Cluster Classification

| Cluster | `arcade_pc` | `runtime_genesis_pc` / `genesis_rom_offset` | Map kind | Classification | Evidence |
|---|---:|---:|---|---|---|
| Raw base writer | `0x0510C8` / `0x0510CE` | `0x0512C8` / `0x0512CE` | `arcade_copy` | unknown / likely debug or special single-entry writer | It loads `PC090OJ address 0x00D00000`, writes four words, then parks in `bra 0x512E0`. It is copied and dangerous if reached, but normal use is not proven. |
| Four-slot writer | `0x052AA2` / `0x052ABE` | `0x052CA2` / `0x052CBE` | `arcade_copy` | object/gameplay animation/update, likely | Called from `runtime_genesis_pc 0x052C8C` and `0x052C9C`; code uses table `0x0005DC5E` plus `%a5@(4762/4764)` offsets and writes four PC090OJ entries to base `0x00D00000`. |
| D00298 writer entry | `0x05A502` / `0x05A51E` / `0x05A524` | `0x05A702` / `0x05A71E` / `0x05A724` | `arcade_copy` | status/UI raw PC090OJ path statically; dynamic BlastEm path unresolved | Direct caller `runtime_genesis_pc 0x05124E` enters this routine if `%a5@(52)==0`; code writes status-like tiles `0x37/0x38/0x3F...` at `PC090OJ address 0x00D00298`. |
| D002B0 continuation | `0x05A554` / `0x05A55A` | `0x05A754` / `0x05A75A` | `arcade_copy` | continuation of same status/UI raw path | Same routine changes destination to `PC090OJ address 0x00D002B0` and continues writing entries. |

### B3. D00298 Caller / Predecessor Trace

Mapped sites:

- `runtime_genesis_pc 0x0005124E` / `genesis_rom_offset 0x0005124E` maps to `arcade_pc 0x0005104E`, kind `arcade_copy`.
- `runtime_genesis_pc 0x0005A702` / `genesis_rom_offset 0x0005A702` maps to `arcade_pc 0x0005A502`, kind `arcade_copy`.
- `runtime_genesis_pc 0x0005A724` / `genesis_rom_offset 0x0005A724` maps to `arcade_pc 0x0005A524`, kind `arcade_copy`.

Local flow at `runtime_genesis_pc 0x0005124E`:

```asm
51246: cmpi.w #0,%a5@(52)
5124c: bne.s 0x51254
5124e: jsr 0x5a702
51254: jsr 0x5a298
```

Local flow at `runtime_genesis_pc 0x0005A702`:

```asm
5a702: clr.l %d0
5a704: move.w 0x10c200,%d0
5a70a: btst #5,%d0
5a70e: beq.s 0x5a716
5a710: move.w #0x0180,%d1
5a714: bra.s 0x5a71a
5a716: move.w #0x0070,%d1
5a71a: move.w #0x0060,%d0
5a71e: movea.l #0x00D00298,%a0
5a724: move.w #0,(%a0)+
```

Static classification: `0x5A702` is a copied arcade status/UI PC090OJ writer with a normal direct caller at `0x5124E`. It is therefore **not statically dead** and not merely data.

Dynamic classification for the user-observed BlastEm fatal: **unresolved between normal status flow and reset/bootstrap re-entry fallout**. Prior manual evidence suggests the path may be reached after the `0x3A1A8` non-BCS bootstrap/re-entry path, but static code also shows a normal direct caller. Static evidence alone cannot prove which dynamic route led to the BlastEm `D00298` fatal.

Smallest safe runtime breakpoint plan:

- Stop at `runtime_genesis_pc 0x0005A71E`, before the dangerous first write at `runtime_genesis_pc 0x0005A724`.
- Capture PC/SR/A0/A5/SP, `%a5@(0)`, `%a5@(2)`, `%a5@(4)`, `%a5@(18)`, `%a5@(44)`, `%a5@(52)`, and the return address on the stack.
- Do not step over `0x5A724`; this is the first raw write to `PC090OJ address 0x00D00298`.
- At `runtime_genesis_pc 0x0003B292`, use step-in (`s`), not step-over (`n`), because the call may contain the path that reaches the fatal.

## Part C - Window Garbage Evidence

### C1. Build 0120 VRAM Layout

Derived from `apps/rastan-direct/src/vdp_comm.s` register setup and commit targets:

| Region | Source | VRAM address range | Evidence |
|---|---|---:|---|
| Plane B nametable | VDP reg 4 = `0x06`; commit base `VRAM_PLANE_B_BASE` | `VRAM address 0xC000..0xCFFF` | 64x32 cells = 4096 bytes |
| Plane A nametable | VDP reg 2 = `0x38`; commit base `VRAM_PLANE_A_BASE` | `VRAM address 0xE000..0xEFFF` | 64x32 cells = 4096 bytes |
| Window nametable | VDP reg 3 = `0x3C`; Exodus viewer shows Mapping Address `0x0F000` | `VRAM address 0xF000..0xFFFF` if using the configured 64x32 footprint | Exact visibility depends on Window X/Y and VDP mode; storage footprint follows current plane geometry / Exodus cell width 64, height 32 |
| SAT | VDP reg 5 = `0x7C`; `vdp_commit_sprites` DMA dest | `VRAM address 0xF800..0xFA7F` | 80 entries * 8 bytes = 640 bytes |
| H-scroll table | VDP reg 13 = `0x3F`; `vdp_commit_scroll` base | `VRAM address 0xFC00..0xFC03` currently written | Register base covers H-scroll table region; current code writes two words per frame |
| PC080SN tile patterns | `load_scene_tiles`; `vdp_commit_tiles_if_dirty` | Dynamic manifests plus `VRAM_TILE_BASE 0x0020`; scene preload writes to LUT-selected tile VRAM | Exact current scene tile spans are manifest-dependent |
| PC090OJ sprite tile patterns | `vdp_commit_sprites` tile DMA | `VRAM address 0x8000..0xA77F` for slots `0..79` (`SPRITE_TILE_BASE 1024`, 4 tiles/slot, 32 bytes/tile) | Computed from code: `(1024 + slot*4) * 32` |
| Crash plane rendering | `crash_handler.s` | Plane A `VRAM address 0xE000..` | Crash-only, not active for the screenshots |

Uncertainty: exact hardware-visible Window coverage with Window X/Y zero is not independently proven here from Genesis hardware docs. Existing project evidence treats it as not visible to the player, while Exodus can inspect its nametable contents directly.

### C2. Overlap Check

Assuming the current 64x32 Window nametable footprint (`VRAM address 0xF000..0xFFFF`), overlap is real:

| Window span | Other region | Other span | Overlap |
|---:|---|---:|---:|
| `0xF000..0xFFFF` | SAT | `0xF800..0xFA7F` | `0xF800..0xFA7F` |
| `0xF000..0xFFFF` | H-scroll table region | base `0xFC00`; current writes `0xFC00..0xFC03` | at least `0xFC00..0xFC03`; broader table storage may also lie in the Window span |
| `0xF000..0xFFFF` | Plane A nametable | `0xE000..0xEFFF` | none |
| `0xF000..0xFFFF` | Plane B nametable | `0xC000..0xCFFF` | none |
| `0xF000..0xFFFF` | PC090OJ sprite tile region | `0x8000..0xA77F` | none |
| `0xF000..0xFFFF` | common PC080SN tile pattern region | dynamic / manifest-dependent | no static overlap proven here |

Interpretation: the Window garbage is plausibly Window-viewer interpretation of overlapping SAT/H-scroll storage, plus any stale/uninitialized words in the rest of `0xF000..0xFFFF`. This is stronger than a hidden Window producer theory because no Window producer/staging/commit path exists.

### C3. Window Clear Status

No code was found that clears `VRAM address 0xF000..0xFFFF` as a Window nametable range during boot or scene transition.

What boot clears:

- `staged_bg_buffer`, `staged_fg_buffer`, `staged_sprite_sat`, and descriptor staging in `Genesis-WRAM`.
- Plane A VRAM `0xE000..0xEFFF` through `_bootstrap_clear_staging`.

What boot does not clear:

- Plane B VRAM as a whole.
- Window VRAM `0xF000..0xFFFF` as a Window nametable.
- SAT VRAM directly; SAT VRAM is later overwritten by `vdp_commit_sprites` DMA from `staged_sprite_sat`.

Clearing Window registers is not the same as clearing Window nametable VRAM contents.

### C4. Current Window Write Sources

No direct game Window staging/commit source was found. Current writes into the Window VRAM span are from overlapping VDP regions:

- `vdp_commit_sprites` DMAs staged SAT to `VRAM address 0xF800..0xFA7F`, inside the Window span.
- `vdp_commit_scroll` writes H-scroll data at `VRAM address 0xFC00..`, inside the Window span.
- Any stale/uninitialized VRAM words in `0xF000..0xFFFF` remain visible in the Exodus Window viewer because no Window clear path exists.

No active `vdp_commit_window`, `staged_window_buffer`, or Window dirty path exists.

### C5. Window X/Y Register Writes

Source search found VDP Window register writes only in `vdp_boot_setup`:

```asm
VDP_REG_WINDOW_X = 17, value 0x00
VDP_REG_WINDOW_Y = 18, value 0x00
```

No later source write to VDP registers 17 or 18 was found. Therefore, under the current register state and existing project interpretation, Window garbage is resident in VRAM and visible in VDP tools, but not proven visible to the player. If any future code changes Window X/Y, the resident garbage could become player-visible.

### C6. Window Garbage Classification

Current classification: **overlap with intentional VRAM regions plus stale/uninitialized Window VRAM**.

Evidence:

- Window base is `VRAM address 0xF000`.
- Window's 64x32 footprint overlaps SAT at `0xF800..0xFA7F` and H-scroll writes at `0xFC00..`.
- No Window nametable clear exists.
- No Window producer exists.
- Exodus Window pane shows resident patterned data while title/story Plane A/B display coherent game content.

Not classified as active Window producer garbage.

## Part D - Result Classification

1. **Why does Exodus show only one sprite?**
   Static evidence cannot fully answer. The most likely explanations are stale `staged_sprite_sat` / stale valid descriptor, or Exodus showing a zero/terminated SAT artifact as a small box. It is not evidence of a healthy PC090OJ sprite set.

2. **Is the one visible sprite expected, stale, or malformed?**
   Unresolved, leaning stale/malformed. It is not expected proof of correct sprite behavior.

3. **Is Genesis SAT fully cleared/terminated every VBlank?**
   No. `vdp_commit_sprites` rebuilds links among valid descriptors and DMAs all staged SAT to VRAM, but it does not clear every unused staged SAT entry every VBlank and does not clear descriptor valid bits.

4. **Are routed PC090OJ helpers actually capable of producing title/story sprites today?**
   They are capable of producing SAT entries in general, but title/story intentional sprite production is not proven. The story king/figure is on Plane B in user evidence, not the sprite layer.

5. **Are remaining raw PC090OJ writers likely responsible for missing sprites, only for D00298 crash, both, or unresolved?**
   Unresolved. The raw `0xD00298` cluster is a plausible cause of the BlastEm/Nomad fatal. Missing/incomplete sprites may also involve routed-helper coverage gaps, stale SAT state, palette/high-bank mapping (OPEN-006), or raw writers, but this audit does not prove which.

6. **Is Window nametable garbage stale, overlapping, actively written, or unresolved?**
   Best classification: overlapping + stale. The Window nametable span overlaps SAT and H-scroll storage and is not cleared as Window VRAM. No active Window producer was found.

7. **Is Window garbage currently visible to the player, or only visible in VDP tools?**
   Only proven visible in VDP tools. No post-boot Window X/Y writes were found, and prior project evidence treats Window X/Y zero as effectively disabled/not covering the screen. Player visibility would need a register-state capture or a future Window X/Y write.

8. **Evidence still needed before sprite-routing design:**
   A runtime SAT state capture at title/story pages: `staged_sprite_sat`, `staged_sprite_descriptor_table`, `staged_sprite_active_count`, and `VRAM address 0xF800..0xFA7F` before/after `vdp_commit_sprites`, plus producer breakpoints for the routed helper that last wrote the visible slot. For D00298, stop at `runtime_genesis_pc 0x0005A71E` before `0x0005A724` and capture caller/return/state.

9. **Evidence still needed before Window cleanup/design:**
   A VRAM dump of `0xF000..0xFFFF` correlated against `0xF800..0xFA7F` SAT and `0xFC00..` H-scroll writes, plus VDP register 17/18 confirmation during title/story. This will distinguish purely overlapped tool-visible garbage from player-visible Window risk.

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-024, OPEN-023, OPEN-006, OPEN-021, OPEN-001, OPEN-015.
- **OPEN-024:** Remains open. One Sprite-pane entry does not prove sprite subsystem health; SAT clearing/producer coverage remain unresolved.
- **OPEN-023:** Remains open. Window VRAM garbage is real in Exodus VDP tools and overlaps SAT/H-scroll storage; no Window translation path exists.
- **OPEN-006:** Remains open. Sprite palette/high-bank correctness was not proven.
- **OPEN-021:** Context only; high-score SCORE/ROUND provenance not addressed.
- **OPEN-001:** Context only; Plane A/B title/story evidence remains separate from sprite/window gaps.
- **OPEN-015:** Context only; no crash-screen fields were used as reliable evidence.
- **Closed issues touched:** NONE.
- **New issues opened:** NONE. Existing OPEN-024 and OPEN-023 cover the unresolved findings.
- **Issues closed:** NONE.
- **Issues intentionally deferred:** D00298 implementation, sprite routing design, Window cleanup design, OPEN-006 palette mapping, OPEN-015 crash-handler fixes.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update from this evidence pass. The report refines build-state interpretation but does not establish a new durable mechanism beyond the existing OPEN issue coverage.

## STOP

STOP triggered: **NO**.
