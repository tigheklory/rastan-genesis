# Opcode Change Audit — Keep / Rework / Revert

## 1. Purpose

Audit the accumulated opcode, spec, and translation changes made to Rastan Genesis.
Classify each meaningful change against the final intended architecture:
- arcade-intent → WRAM staging → Genesis VBlank DMA → VDP
- proper semantic relocation via shift_table_patcher
- no wrappers, shims, or scaffolding in the final path

References used: AGENTS.md, AGENTS_LOG.md (all major build sections through Build 271),
docs/design/rastan_graphics_translation_layer.md,
docs/design/rastan_vblank_and_vdp_buffer_architecture.md,
docs/design/rastan_opcode_to_vdp_translation.md,
docs/design/rastan_68000_opcode_patch_templates.md,
docs/research/title_screen_graphics_call_inventory.md,
docs/research/first_visible_graphics_failure.md,
docs/research/true_text_producer_entry.md,
docs/research/text_producer_execution_failure.md,
docs/research/text_record_rejection_point.md,
docs/research/build246_real_game_text_translation.md,
docs/research/build271_title_logo_sprite_translation.md,
docs/research/rainbow_islands_arcade_vs_genesis_graphics_comparison.md,
docs/research/cadash_arcade_vs_genesis_graphics_comparison.md,
specs/startup_title_remap.json, tools/translation/shift_table_patcher.py,
tools/translation/postpatch_startup_rom.py, apps/rastan/src/main.c.

---

## 2. Change Inventory

### 2.1 Infrastructure / Build Architecture

| ID | Change | Location |
|----|--------|----------|
| I-1 | Whole-maincpu relocated copy mode (`whole_maincpu_copy`, dest `0x000200`) | spec `policy` + `whole_maincpu_copy` |
| I-2 | ROM absolute call relocation (scans relocated copy, rewrites absolute ROM targets) | spec `rom_absolute_call_relocation` + patcher |
| I-3 | `shift_table_patcher.py` relocation engine: absolute, relative, jump-table | `tools/translation/shift_table_patcher.py` |
| I-4 | `postpatch_startup_rom.py` orchestration (apply shift replacements, then opcode_replace) | `tools/translation/postpatch_startup_rom.py` |
| I-5 | `rom_opcode_replace` feature in patcher (added Build 246, entries later cleared) | `spec.rom_opcode_replace = []` |

### 2.2 Hardware Shadow / Window Mappings

| ID | Change | Location |
|----|--------|----------|
| H-1 | Input shadows: 0x390001/3/5/7/9/B → named symbols | spec `absolute_rewrite_groups` |
| H-2 | Watchdog/control shadows: 0x350008, 0x380000, 0x3C0000 → named symbols | spec `absolute_rewrite_groups` |
| H-3 | Sound mailbox shadows: 0x3E0001/3 → named symbols | spec `absolute_rewrite_groups` |
| H-4 | Workram shadow: 0x10C000 → genesistan_arcade_workram_words | spec `absolute_rewrite_groups` |
| H-5 | Palette shadow: 0x200000 → genesistan_palette_clcs / wram_overlay | spec `absolute_rewrite_groups` |
| H-6 | C-Window shadow: 0xC50000 → genesistan_shadow_reg_c50000 | spec `absolute_rewrite_groups` |
| H-7 | DIP switch shadow: 0x390009/B → genesistan_shadow_dip1/2 | spec `absolute_rewrite_groups` |

### 2.3 Title Init Helper Patches (opcode_replace)

| ID | Change | Arcade PC | Replacement |
|----|--------|-----------|-------------|
| T-1 | Sprite RAM clear redirect | `0x03AD4C` | Fills `0xE0FF11FE` (36 longs) + `0xE0FF01BC` (8 longs) with zero instead of D00000 |
| T-2 | Tile plane clear redirect | `0x03AE64` | Fills `0xE0FFC84C` (text shadow) with 0x20 instead of C00100/C08100 |
| T-3 | Scroll init clears | `0x03ABBA`, `0x03ABC0`, `0x03B098`, `0x03B09E` | `jsr genesistan_scroll_from_workram_vdp` instead of clrls to 0xC20000/C40000 |
| T-4 | Text dispatch hook | `0x03BB48` | `jsr genesistan_hook_text_writer_3bb48; rts` |
| T-5 | Secondary text dispatch hook | `0x03C3FE` | `jmp genesistan_hook_text_writer_3c3fe` |
| T-6 | Scroll writes in game engine | `0x055AB4/BC/C4/CC`, `0x00016A`, `0x000170` | `jsr genesistan_scroll_from_workram_vdp` |
| T-7 | Many C-Window base stores → NOP | `0x055E54`, `0x055818`, `0x055B84`, `0x056032`, `0x05605C`, `0x0503EC/F6/00/0C/16/20`, `0x0561C0` | NOP |
| T-8 | Direct C-Window writes → NOP | `0x03A350`, `0x03A552`, `0x03A55C`, `0x03A72A`, `0x03AAEA`, `0x03D04C` | NOP |
| T-9 | 0x0560DA function body → all NOP | `0x0560DA` | 52 bytes of 0x4E71 |
| T-10 | Startup zero-writes → NOP | `0x000514`, `0x000518`, `0x00052A` | NOP |
| T-11 | Tilemap plane A hook | `0x055968` | `jsr genesistan_hook_tilemap_plane_a; rts; NOPs` |
| T-12 | Tilemap plane B hook | `0x055990` | `jsr genesistan_hook_tilemap_plane_b; rts; NOPs` |
| T-13 | Various display control NOPs | `0x03A6FE`, `0x03A708`, `0x03AC54`, `0x0556F2`, `0x0558C6`, `0x0558E0`, `0x055904`, `0x05577E`, `0x03A6B2`, `0x03A860`, `0x03A294`, `0x03A2B2`, `0x0556F2`, `0x05577E` | NOP |
| T-14 | `0x03BB66/68/74/76` tile writes → NOP | those addresses | NOP |
| T-15 | `0x03B1CC`, `0x03B47A`, `0x03B47E`, `0x03B49A`, `0x03B572`, `0x03B5F6` writes → NOP | those addresses | NOP |
| T-16 | `0x052858`, `0x052974`, `0x0575CE` base loads → rts+NOP | those addresses | `rts; NOP; NOP` |

### 2.4 Sprite Renderer Redirects

| ID | Change | Arcade PC(s) | Replacement |
|----|--------|-------------|-------------|
| S-1 | Multiple sprite renderer callsite redirects | `0x03A20E`, `0x03A264`, `0x03A640`, `0x03A6C4`, `0x03A818`, `0x03A820`, `0x03A854`, `0x03A8E0`, `0x03A9C6`, `0x03A9D4`, `0x03B8E8`, `0x03B8F0`, `0x041DAE`, `0x041F5E`, `0x045DFA` | `jsr/jmp genesistan_render_sprites_vdp_bridge` |

### 2.5 Logo / Sprite Producer Descriptor Retargets

| ID | Change | Arcade PC(s) | Detail |
|----|--------|-------------|--------|
| D-1 | Block-A producer clear base retarget | `0x059F62` | `0xD00048` alias → `0xE0FF11FE` (renderer-consumed block-A) |
| D-2 | Block-B producer descriptor base retargets | `0x059F76`, `0x059F9A`, `0x059FDE` | `0x10C170` → `0xE0FF01BC` (renderer-consumed block-B) |
| D-3 | Block-B slot retargets +8,+16,+24 | `0x059FFC/05A014`, `0x05A032/05A04A`, `0x05A068/05A080` | table-entry slots → renderer-consumed WRAM offsets |
| D-4 | Block-A builder base retarget | `0x05A0AE` | `0xE0FF62F6` → `0xE0FF11FE` |
| D-5 | Block-A descriptor attr force | `0x05A11A`, `0x05A13E`, `0x05A188`, `0x05A1AC`, `0x05A1D0` | `movew #0` → `movew #0x80` (forces non-zero attr) |
| D-6 | Block-A descriptor builder retarget | `0x05A1EC` | Same as D-4 (secondary path) |
| D-7 | `0x059F90` RTS extension | `0x059F90` | `rts` → `bsr +0x124; bsr +0x04; rts` (adds calls before the RTS) |

### 2.6 C-Level Translation Hooks (main.c)

| ID | Change | Symbol | Detail |
|----|--------|--------|--------|
| C-1 | Title text producer (3BB48 path) | `genesistan_hook_text_writer_3bb48_impl` | Decodes descriptor table at 0x3BD92, maps to SGDK tile draw via tile cache |
| C-2 | Secondary text producer (3C3FE path) | `genesistan_hook_text_writer_3c3fe` | Decodes 3C3FE format, draws via rastan_draw_tile_xy |
| C-3 | Tilemap plane A updater | `genesistan_hook_tilemap_plane_a` | Stateful col/row counter, writes to VDP plane A via VDP_setTileMapXY |
| C-4 | Tilemap plane B updater | `genesistan_hook_tilemap_plane_b` | Same pattern, plane B |
| C-5 | Sprite renderer | `genesistan_render_sprites_vdp` | Full sprite decode + SAT build + VDP upload |
| C-6 | Scroll publisher | `genesistan_scroll_from_workram_vdp` | Reads WRAM scroll words, writes to VDP scroll regs |
| C-7 | VDP layout sync | `genesistan_sync_title_vdp_layout` | Sets plane A/B/SAT addresses, plane size, disables window |
| C-8 | Text destination mapper | `text_writer_ptr_to_xy` | Maps arcade C-Window pointer to screen col/row; hardcoded `col_bias=32` |
| C-9 | Tile attribute builder | `text_writer_build_tile_attr` | Looks up glyph in font table, resolves VRAM slot via tile cache |

---

## 3. Per-Change Classification Table

### Infrastructure (I)

| ID | Classification | Reasoning | Relocation Risk |
|----|---------------|-----------|-----------------|
| I-1 | **KEEP** | Whole-maincpu relocated copy is the correct baseline architecture | Low — this is the copy mode foundation |
| I-2 | **KEEP** | Absolute call relocation is required for any relocated code to function | Low — systematic pass at build time |
| I-3 | **KEEP** | The shift_table_patcher is the core relocation engine for all opcode replacements | Low — well-defined, tested infrastructure |
| I-4 | **KEEP** | Orchestration pipeline is correct; `rom_opcode_replace` support is a useful safety valve | Low |
| I-5 | **KEEP** (cleared correctly) | `rom_opcode_replace` was used in Build 246 for a transient fix, then cleared. The feature exists for genuine edge cases. Keeping the cleared list is correct. | N/A |

### Hardware Shadow / Window Mappings (H)

| ID | Classification | Reasoning | Relocation Risk |
|----|---------------|-----------|-----------------|
| H-1 | **KEEP** | Input register shadows are required; 0x390000 maps to Genesis-side input state | Low |
| H-2 | **KEEP** | These hardware controls must not write to unmapped Genesis space | Low |
| H-3 | **KEEP** | Sound mailbox shadow is required for PC060HA simulation | Low |
| H-4 | **KEEP** | Workram base must redirect to Genesis WRAM | Low |
| H-5 | **REWORK** | `wram_overlay` is used in frontend_core but `genesistan_palette_clcs` in startup_common. This inconsistency means palette accesses in different code ranges hit different symbols. Consolidate to single palette symbol. | Medium — different symbols in different ranges |
| H-6 | **KEEP** | C50000 shadow is a non-VDP stub; correct for now until replaced by VDP control write | Low |
| H-7 | **KEEP** | DIP switch shadow needed for arcade game logic | Low |

### Title Init Helper Patches (T)

| ID | Classification | Reasoning | Relocation Risk |
|----|---------------|-----------|-----------------|
| T-1 | **REWORK** | Clears the descriptor input windows (block-A/B for 0x05A174 producer), not the actual SAT staging buffer (genesistan_shadow_d00000_words). The clear intent is correct — the target is wrong. Should clear genesistan_shadow_d00000_words for the SAT, plus the descriptor windows. Uses hardcoded WRAM addresses instead of symbols. | Medium — hardcoded 0xE0FF11FE/01BC |
| T-2 | **KEEP** | Correct redirection: tile plane clear now targets the text shadow buffer. Both fills go to 0xE0FFC84C which is the right WRAM owner. The count (0x0800 words) and fill value (0x20) are correct. | Low |
| T-3 | **KEEP** | Scroll clears correctly redirected to VDP scroll publisher. These were clearing arcade scroll chip registers; calling the Genesis scroll function is the right substitution. | Low — uses symbol |
| T-4 | **KEEP** | Text dispatch hook plumbing is correct direction. The hook calls the C translation function. | Low — uses symbol |
| T-5 | **KEEP** | Secondary text dispatch hook plumbing is correct direction. | Low — uses symbol |
| T-6 | **KEEP** | Scroll writes in game engine correctly redirected. Covers the production scroll callsites, not just the init path. | Low — uses symbol |
| T-7 | **KEEP** | Silencing C-Window base stores prevents arcade code from seeding wrong pointer values into workram (which would be used to compute tile/text destinations). These are necessary "poison prevention" patches. However, see T-7a below. | Medium — some may have non-graphics uses |
| T-7a | Note on T-7 | Several of these NOPs silence stores of 0xC0xxxx addresses into workram slots (e.g., A5@(0x10A0/A4/A8/F8)). These workram slots are used by tilemap update code as the current-layer base pointer. By NOPing them, those pointers remain at whatever was last written (possibly 0 or stale). This is acceptable only while the tilemap hooks (T-11/T-12) completely replace the tilemap update path. If tilemap hooks are removed, these NOPs must also be reverted or replaced with shadow-WRAM redirects. | High — depends on tilemap hook coverage |
| T-8 | **KEEP** | Direct C-Window writes at isolated callsites. NOPing these prevents crashes from writing to unmapped Genesis space. | Low |
| T-9 | **REVERT** | The entire body of the function at 0x0560DA (52 bytes) was NOPed without documented purpose. The function body includes: pointer comparison against a WRAM range, a conditional call, and a WRAM store sequence. It is not clear this function has no non-graphics side effects. Silencing an unknown function body is too risky without full analysis. | High — unknown effects |
| T-10 | **KEEP** | Startup-time zero writes and early-init pointer setup. The 0x00052A patch (entry stub → rts) redirects the early arcade startup self-test path. This is needed for boot flow. | Low |
| T-11 | **REWORK** | The tilemap plane-A hook uses stateful col/row counters (genesistan_hook_col_a/row_a) that advance on each call. This is wrong: it assumes tile updates arrive in a strict sequential order and makes the position depend on call count, not on the actual destination address in the arcade op. If any tile update is skipped, omitted, or reordered, the col/row state drifts. The correct approach is to decode the actual arcade destination address from the instruction operand and map it to a plane cell coordinate. | High — state drift under any non-sequential call pattern |
| T-12 | **REWORK** | Same issue as T-11 for plane B. | High |
| T-13 | **KEEP (mostly)** | These NOP various display control writes (tilemap state sets, C-Window base advancement, etc.) that would corrupt WRAM state or write to unmapped space. Most are correct. Exception: any NOP of code that has correct non-graphics side effects must be reviewed individually. | Medium — not all have been fully audited |
| T-14 | **KEEP** | NOPs tile writes at specific callsites that wrote directly into C-Window. Prevents unmapped-space writes. | Low |
| T-15 | **KEEP** | Silences various small writes that go to C-Window or invalid addresses in the title flow. | Low |
| T-16 | **REWORK** | `rts; NOP; NOP` at 0x052858/052974/0575CE replaces `movea.l #0xE0FFE2A2, A1` (loads a C-Window-derived address into A1). The return-early approach means the calling code gets a stale A1, which may not be what the callers need. Better to redirect the load to an appropriate WRAM address rather than bailing early. | Medium — callers may use A1 |

### Sprite Renderer Redirects (S)

| ID | Classification | Reasoning | Relocation Risk |
|----|---------------|-----------|-----------------|
| S-1 | **REWORK** | The concept (redirect arcade sprite renderer callsites to a Genesis VDP sprite bridge) is correct and aligns with the final architecture. However, there are 15 callsites redirected all to the same bridge, across multiple different game states and contexts (title, gameplay, boss, test mode). Not all contexts have been validated. In the final architecture, these should all use the same bridge (correct), but the bridge itself is called redundantly — some call sites are in paths that haven't been confirmed to have valid producer state yet. Verify each callsite's producer state before VBlank publish, but keep the retargeting. | Medium — some callsites may fire before producer state is valid |

### Logo / Sprite Producer Descriptor Retargets (D)

| ID | Classification | Reasoning | Relocation Risk |
|----|---------------|-----------|-----------------|
| D-1 | **KEEP** | Retargets block-A producer to renderer-consumed window. Confirmed working in Build 271 (producer writes land in correct WRAM block). | Low |
| D-2 | **KEEP** | Retargets block-B producer bases to renderer-consumed block. Same validation. | Low |
| D-3 | **KEEP** | Retargets block-B slot sub-offsets. Correct. | Low |
| D-4 | **KEEP** | Same as D-1 for secondary code path. | Low |
| D-5 | **REVERT** | Forcing descriptor attr word from 0x0000 to 0x0080 is a descriptor content hack. The original attr value 0x0000 was the real arcade value. Forcing 0x0080 makes descriptors "non-empty" so they pass renderer checks, but uses a wrong attribute (0x0080 = palette 0, priority 0, tile index partial). This is scaffolding that should not survive into the final architecture. The correct fix is to ensure that non-zero attr comes from the real arcade descriptor content, not from a forced overwrite. | None — but wrong semantics |
| D-6 | **KEEP** | Same as D-4 (secondary block-A path). | Low |
| D-7 | **REVERT** | Inserting two BSR calls at the RTS of 0x059F90 is a trampoline-style extension. It adds opaque calls "for free" at the function's return boundary without changing the callsite. This is the exact kind of "extension hack" forbidden by the architecture. The correct approach (per design document) is to fix the call order at the title init cluster (0x03AAB8) by swapping the producer and renderer calls explicitly. | Medium — brittle against shifts at the extended addresses |

### C-Level Translation Hooks (C)

| ID | Classification | Reasoning | Relocation Risk |
|----|---------------|-----------|-----------------|
| C-1 | **REWORK** | The text producer implementation is directionally correct (decodes descriptor table, resolves glyph via tile cache, draws to Genesis plane). However, it currently calls `rastan_draw_tile_xy` which writes directly to VDP during the hook call — not to the text shadow buffer. The VBlank architecture requires text cells to be written to the text shadow (`0xE0FFC84C`) for VBlank DMA publish. Currently the draw is live/immediate, bypassing the WRAM-staging → VBlank-DMA pipeline. This works when called in the right window but is fragile outside VBlank timing. | N/A — C code |
| C-2 | **REWORK** | Same issue as C-1: secondary text writer also draws immediately to VDP via tile_xy, not via text shadow staging. | N/A |
| C-3 | **REVERT** | Col/row counter approach is wrong-direction (see T-11). The final architecture does not use call-count position tracking. The hook should decode the actual arcade tile destination address. | N/A |
| C-4 | **REVERT** | Same as C-3. | N/A |
| C-5 | **REWORK** | The sprite renderer itself is correct in concept. It decodes descriptor tuples, builds Genesis SAT entries, and uploads to VDP. However, it is called from both the main loop and from the VBlank bridge, without a single defined VBlank-only publish path. The renderer should be called exclusively from the VBlank publish step, not from ad-hoc callsites in the main SCREEN_FRONTEND_LIVE loop. | N/A |
| C-6 | **KEEP** | Scroll from workram to VDP is correct. It reads the staged WRAM scroll values and writes to VDP. This is the right direction and the right behavior. | N/A |
| C-7 | **REWORK** | `genesistan_sync_title_vdp_layout` is called from `request_start_rastan()` and from the `SCREEN_FRONTEND_LIVE` loop. Calling it repeatedly in the main loop is scaffolding — VDP layout should be initialized once at scene entry, not re-set every frame from C code. In the final architecture, this setup either goes into the VBlank init step or is preserved from the initial scene setup. Keep the function; remove the repeat call from the frame loop. | N/A |
| C-8 | **REWORK** | `text_writer_ptr_to_xy` is architecturally correct (maps arcade destination pointer to screen coordinate), but `col_bias = 32U` is hardcoded. The comment says "0x400 byte page viewport offset / 0x100 bytes per row" which is correct for the page-2 text layout (`0xC08400` start). However, this bias only works for page-2 text (FG/Plane A). Page-0 text (BG/Plane B) uses a different page base and would need a different bias. Make col_bias derived from the page layout constant, not hardcoded. | N/A |
| C-9 | **KEEP** | Tile attribute builder correctly resolves glyph codes through the font table and tile cache. This is the correct pattern for glyph tile resolution. | N/A |

---

## 4. Scaffolding / Hack Identification

### 4.1 Descriptor Attribute Force (D-5): REVERT

**What it is**: Five opcode patches at `0x05A11A`, `0x05A13E`, `0x05A188`, `0x05A1AC`, `0x05A1D0`
replace `movew #0x0000, Dn/An@` with `movew #0x0080, Dn/An@`. This forces logo descriptor
attribute fields from 0 (the real arcade value) to 0x80 (a fake non-zero value).

**Why it is scaffolding**: The renderer checks for zero attrs to decide if a descriptor entry
is empty. By hardcoding 0x0080, the sprites pass the "non-empty" check with wrong
attribute data. 0x0080 is not derived from any arcade state; it was chosen to make the
renderer "see" entries. This is fake data injection.

**Verdict**: REVERT. The real arcade attr value is 0x0000 because the descriptor is not yet
computed or the field is zero-initialized. The fix must come from ensuring the full descriptor
tuple is populated correctly (with the tile index, real Y/X coordinates, and the
actual attribute word from the producer logic) — not from overwriting the attr field.

### 4.2 RTS Extension at 0x059F90 (D-7): REVERT

**What it is**: A patch that replaces a plain `rts` with `bsr +0x124; bsr +0x04; rts`.
It inserts two call-ahead branches before the function return.

**Why it is scaffolding**: This is a trampoline-style extension. It uses the return boundary
of a function as a hook insertion point to add extra behavior "for free" without
modifying the callsite or clearly owning the added calls. The architecture explicitly forbids
trampolines. The intent (run the producer before the renderer in the same frame) is correct,
but the mechanism is wrong.

**Verdict**: REVERT. The proper fix is to reorder the explicit call sequence in the
`0x03AAB8` title init cluster so the producer (0x03AAF2) runs before the renderer
(0x03AAEC) via explicit opcode replacement at those addresses.

### 4.3 Function NOP at 0x0560DA (T-9): REVERT

**What it is**: The entire body of the function at `0x0560DA` (52 bytes) was replaced with
`4E71` NOPs. The original body contains: a pointer comparison against a WRAM range, a
conditional branch, a loop that loads and calls a subroutine, and a WRAM store sequence.

**Why it is scaffolding**: The function was NOPed without documented understanding of what it
does. It is not labeled in any research document. It is not proven to be graphics-only code.
Silencing an entire function body without analysis is a blanket suppression that may hide
valid non-graphics behavior (state management, sound commands, timer updates, etc.).

**Verdict**: REVERT or analyze first. The body should be examined (it appears to be a
sprite/descriptor iteration loop based on the original bytes), and only the
graphics-output portions should be redirected; non-graphics state management must be preserved.

### 4.4 Tilemap Col/Row Counter State (C-3, C-4): REVERT

**What it is**: `genesistan_hook_tilemap_plane_a/b` track the current output column and row
using static counters (`genesistan_hook_col_a/row_a`, `col_b/row_b`). Each call advances
the column by 16 (one cell block), wrapping to the next row at 64.

**Why it is scaffolding**: Position tracking by call count depends on the assumption that
every tile update arrives in strict left-to-right, top-to-bottom sequential order, and that
no updates are skipped. This assumption is violated when:
- The arcade code performs non-sequential tile updates (e.g., updating only dirty regions)
- Updates for different contexts are interleaved
- The hooks are not called the same number of times across different frames

The correct approach is to decode the actual arcade destination address from the tile update
instruction and map it to the plane coordinate. This is how Rainbow Islands Genesis handles
plane writes: compute VDP destination from the data, not from call position.

**Verdict**: REVERT. Implement proper destination-address decoding from the arcade tile
operand.

### 4.5 VDP Layout Re-sync in Frame Loop (C-7 partial): REWORK

**What it is**: `genesistan_sync_title_vdp_layout()` is called on every frame iteration in
`SCREEN_FRONTEND_LIVE`. This re-programs VDP plane/SAT addresses 60 times per second.

**Why it is scaffolding**: VDP plane and SAT addresses are configured once per scene, not
per frame. Calling this every frame is a workaround for the symptom (VDP might lose layout
state) rather than fixing the root cause (layout was not properly initialized once at scene
entry). The function itself is not wrong; the repeated call pattern is wrong.

**Verdict**: REWORK. Keep `genesistan_sync_title_vdp_layout` but call it only once at
title entry (in the scene initialization path), not every frame.

### 4.6 Immediate VDP Draw vs Text Shadow Staging (C-1, C-2 partial)

**What it is**: `genesistan_hook_text_writer_3bb48_impl` and `genesistan_hook_text_writer_3c3fe`
both call `rastan_draw_tile_xy` which directly calls `VDP_setTileMapXY` during the hook.
This means text cells are written immediately to VDP when the hook fires, not staged to
the text shadow buffer for VBlank DMA.

**Why this is scaffolding**: In the final VBlank architecture:
- Producers run and write to WRAM staging
- VBlank DMA pushes staging to VDP

The current approach works by accident when the hook fires inside the started-path frame
loop (which happens to be roughly VBlank-synchronized in the current implementation).
If the hook fires outside VBlank timing, or if the WRAM-staging → VBlank-DMA pipeline
is formalized, these hooks will bypass the staging layer entirely.

**Verdict**: REWORK. Text hooks should write to the text shadow at `0xE0FFC84C`, and the
VBlank publish step should DMA from the shadow to Plane A/B VRAM. The draw tile calls
should be moved to the VBlank publish step.

---

## 5. Semantic Relocation Audit

### 5.1 Changes That Are Safe Under Semantic Relocation

These use symbol references or are identity-safe:

| Change | Why Safe |
|--------|----------|
| All scroll/hook replacements using `{symbol:...}` | Symbol addresses resolved at link time; not brittle against shifts |
| `genesistan_hook_text_writer_3bb48 / 3c3fe / tilemap_plane_a/b` replacements | Symbol-referenced, correct |
| `genesistan_scroll_from_workram_vdp` replacements | Symbol-referenced |
| `genesistan_render_sprites_vdp_bridge` replacements | Symbol-referenced |
| Hardware window mappings in absolute_rewrite_groups | Table-driven, symbol-resolved, not sensitive to code shifts |
| ROM absolute call relocation (I-2) | Systematic pass, not patch-specific |
| `shift_table_patcher.py` infrastructure | Relocates everything after shifts |

### 5.2 Changes That Rely on Brittle Absolute Addresses

These use hardcoded addresses rather than symbols, making them vulnerable to shift:

| Change | Problem | Risk |
|--------|---------|------|
| T-1: fills at `0xE0FF11FE` and `0xE0FF01BC` | Hardcoded WRAM addresses in replacement_bytes | If WRAM layout changes, these targets shift without warning |
| T-2: fill at `0xE0FFC84C` | Hardcoded text shadow address | Same |
| D-1 through D-4: descriptor retargets at `0xE0FF11FE`, `0xE0FF01BC`, `0xE0FF01C4/CC/D4` | Hardcoded WRAM window addresses | If WRAM layout shifts, these retargets point to wrong memory |
| D-7: `bsr +0x124; bsr +0x04` | Relative displacements from the extension point | If anything between 0x059F90 and the call targets shifts, these break silently |

**Recommended fix**: All `0xE0FF...` addresses in replacement_bytes should be expressed
as `{symbol:named_buffer}` references, resolving to the linker-generated WRAM symbols.
This is supported by the patcher's `{symbol:NAME}` syntax.

### 5.3 Jump Table and Branch Changes Likely to Break After Further Shifts

| Change | Risk |
|--------|------|
| D-7: RTS extension (D-7) with relative bsr offsets | Any insertion between 0x059F90 and the target routines changes the displacement. The patcher's branch fixer would fix these, but only if they are within the known source range and recognized as branches. An extension past a function boundary might not be covered. |
| T-16: `rts; NOP; NOP` replacing a LEA at 0x052858/052974/0575CE | These are in the game engine range (0x040000-0x060000). After shifts, any callers of these routines that expect A1 to be set will get wrong behavior. |

### 5.4 Changes That Should Be Rewritten To Use Semantic Anchors

Per the `rastan_vblank_and_vdp_buffer_architecture.md` semantic relocation strategy:

1. All opcode_replace entries with `0xE0FF...` in replacement_bytes should be converted
   to `{symbol:...}` form using the corresponding named buffer symbols.

2. D-7 (RTS extension) should be reverted entirely; the correct fix uses two separate
   opcode_replace entries at the actual callsites (0x03AAEC and 0x03AAF2) to reorder them,
   each using `original_bytes` validation.

3. T-1 (0x03AD4C) should be converted to symbol-referenced form once the SAT buffer
   and descriptor windows are declared as named symbols in `required_symbols`.

---

## 6. Original Intent Restoration Judgment

### 6.1 Title Text Path

**Current state**: Partially correct. The `genesistan_hook_text_writer_3bb48_impl` hook
fires on the correct arcade producer dispatch (0x03BD5E → 0x03BB48), decodes the right
descriptor table (0x3BD92), and draws visible title text ("CREDIT" through the word "CREDI"
visible in Build 259/271). The text actually renders.

**Versus arcade intent**: Arcade intent is for the text producer to write cell data to the
PC080SN C-Window, then the hardware composites it. Genesis equivalent should write to text
shadow (WRAM), then VBlank DMA publishes to Plane A/B VRAM. Current implementation skips
the staging step and writes directly to VDP. This is a temporary approximation.

**Judgment**: Closer to correct than temporary approximation, but not final architecture.
The path works; the plumbing needs tightening (staging → VBlank DMA).

### 6.2 Title Sprite / Logo Path

**Current state**: Partially blocked. Descriptor producer (0x05A174) now writes to
renderer-consumed WRAM windows (Build 271 confirmed: block-A at 0xE0FF11FE, block-B at
0xE0FF01BC are non-zero at frame 673). The renderer executes (HIT 2005C4=161).
However, the logo sprite tile staging is still empty (`sprite_code0=0000`,
`tilebuf_nonzero=0/2048`), and SAT writes are zero.

**Root cause (confirmed in title_logo_decode_breakpoint.md)**: The logo consumer
at `0x20064C` reads from the descriptor window when it is still zero — timing/ordering
issue where the renderer fires before the descriptor windows are live.

**Versus arcade intent**: Arcade intent is PC090OJ descriptor writes, then hardware
composites sprites. Genesis equivalent should build SAT tuples and DMA to VDP SAT.
Current state has the descriptor retargets in place (correct direction) but the
producer→renderer ordering is wrong.

**Judgment**: Wrong semantic behavior. Producer must precede renderer in the call order.
The D-5 attr force hack further contaminates the descriptor content.
Needs the ordering fix plus reverting D-5.

### 6.3 PC080SN Tilemap Path

**Current state**: The tilemap hooks T-11/T-12 (plane A/B) exist with the col/row counter
approach. Various C-Window base stores have been NOPed. The hooks have not been proven to
produce visible tilemap content in the title/attract path (they are called from different
code paths than the text producer).

**Versus arcade intent**: Arcade intent is tile-indexed cell writes into PC080SN pages.
Genesis equivalent is decode destination address → compute plane nametable entry → write
via VDP or WRAM staging. The current col/row counter approach is wrong-direction.

**Judgment**: Temporary approximation (counter approach) plus inadequate (not proven active
in title path). Needs real address-decode implementation.

### 6.4 PC090OJ Sprite Path

**Current state**: The broad redirect of 15 sprite renderer callsites to
`genesistan_render_sprites_vdp_bridge` is in place. The renderer executes for the title path.
SAT output is not yet reaching VDP (SAT-range writes = 0 in Build 271).

**Versus arcade intent**: Arcade intent is PC090OJ descriptor list → hardware composite sprites.
Genesis equivalent is SAT tuples in WRAM → VBlank DMA to VDP SAT. Current state has
the bridge in place but the SAT DMA path is not yet proven to fire after valid descriptor data.

**Judgment**: Temporary approximation. Bridge concept is correct; DMA endpoint not proven.

### 6.5 Palette Path

**Current state**: Pre-converted ROM table (`genesistan_palette_rom_table`) is declared
in required_symbols. The `load_arcade_palette()` function calls DMA copy from ROM to CRAM.
CRAM non-zero was confirmed in Build 259 (cram_nonzero=960/962). Palette renders correctly.

**Versus arcade intent**: The pre-converted ROM table approach is correct and aligns with
the architecture decision (Build 112 session). No runtime conversion.

**Judgment**: Closest to final architecture of all subsystems. The main refinement needed
is ensuring the palette DMA fires at the right point in the VBlank sequence (Step 4 per
`rastan_vblank_and_vdp_buffer_architecture.md`).

### 6.6 Scroll / Control Path

**Current state**: Scroll writes are redirected via `genesistan_scroll_from_workram_vdp`
at all major callsites. The function reads staged WRAM values and writes to VDP.
Confirmed operational (scroll values propagate, arcade scroll state remains correct).

**Versus arcade intent**: Arcade uses PC080SN chip register writes. Genesis uses VDP
scroll registers. The WRAM-stage → VDP-publish pattern is correct.

**Judgment**: Closest to final architecture alongside palette. Keep as-is.

### 6.7 VBlank Behavior

**Current state**: The Genesis build currently runs the arcade game loop from a C-level
SCREEN_FRONTEND_LIVE loop. The arcade VBlank interrupt (level 5, 0x3A008) does fire in
arcade execution, but in the Genesis context the game logic runs from the SGDK main loop
frame. The VBlank publish steps (SAT DMA, tilemap DMA) are not yet systematically executed
from within an actual Genesis VBlank callback.

**Versus arcade intent**: Arcade VBlank interrupt does sprite RAM clear, tile plane clear,
text producers, and timing. Genesis equivalent must preserve timing/input/sound semantics
and add VDP DMA publish. Current state has neither the VBlank DMA publish nor the correct
in-VBlank staging → publish pipeline.

**Judgment**: Wrong semantic behavior. The VBlank-driven publish pipeline has not been
implemented. This is the single largest architectural gap remaining.

### 6.8 Translation Infrastructure

**Current state**: `shift_table_patcher.py` handles absolute, relative, and jump-table
relocation. The patcher is well-tested and has caught real issues (Build 214 semantic
entry validation). `original_bytes` validation is in place. The pipeline is sound.

**Versus intended architecture**: The semantic relocation strategy calls for function
signature anchoring (not just address validation), jump table index-based recomputation,
and post-patch manifests. These are enhancements to an already-functional base.

**Judgment**: Good foundation. The enhancements from `rastan_vblank_and_vdp_buffer_architecture.md`
section 9 should be added but are not urgent blockers.

---

## 7. Cleanup Plan

### Phase 1 — Revert Immediately (Before Any New Implementation)

These changes contaminate the code with wrong data or obscure intent. Reverting restores
accurate arcade intent before any new translation work begins.

**1a. Revert descriptor attr force (D-5)**:
- `0x05A11A`, `0x05A13E`, `0x05A188`, `0x05A1AC`, `0x05A1D0`
- Restore `movew #0x0000` (the real arcade attr value)
- Rationale: fake descriptor content; must be gone before any valid descriptor content analysis

**1b. Revert 0x059F90 RTS extension (D-7)**:
- `0x059F90`: restore the original `4E75` (rts only)
- Rationale: trampoline-style extension; replaced by explicit call-order swap at 0x03AAB8

**1c. Revert 0x0560DA full-function NOP (T-9)**:
- `0x0560DA`: restore original bytes
- Then analyze: identify which parts are graphics-only vs non-graphics
- NOP only the graphics-output portions; preserve non-graphics state logic

**1d. Revert tilemap plane hook col/row counter approach (C-3, C-4)**:
- `0x055968` and `0x055990`: restore original bytes (or replace with a
  properly-decoded address-based mapping approach)
- Do not implement the new approach yet; just remove the wrong approach

### Phase 2 — Rework Before New Implementation

These changes are directionally right but must be corrected before they can serve as
reliable foundation.

**2a. Fix T-1 (0x03AD4C) to target correct SAT buffer and use symbols**:
- Change hardcoded `0xE0FF11FE`/`0xE0FF01BC` to named symbol references
- Ensure the SAT staging buffer (`genesistan_shadow_d00000_words`) is also cleared
- Adjust block sizes to match actual producer/consumer contracts

**2b. Fix descriptor producer retargets (D-1 through D-4) to use symbol references**:
- Replace hardcoded `0xE0FF11FE`, `0xE0FF01BC`, `0xE0FF01C4/CC/D4` in replacement_bytes
  with `{symbol:...}` tokens
- Declare corresponding named symbols in `required_symbols`

**2c. Fix text_writer_ptr_to_xy col_bias**:
- Derive `col_bias` from the actual C-Window page layout constant instead of hardcoding 32
- Add a compile-time assertion or comment documenting the derivation

**2d. Fix genesistan_sync_title_vdp_layout call frequency**:
- Remove from SCREEN_FRONTEND_LIVE frame loop
- Keep in request_start_rastan handoff (one-time setup at scene entry)

**2e. Fix H-5 palette symbol inconsistency**:
- Consolidate: use a single symbol for the 0x200000 palette window across all code ranges

**2f. Fix S-1: audit per-callsite producer state before bridge fires**:
- For each of the 15 sprite renderer callsites, verify that the producer has run before
  the renderer bridge fires
- Remove any callsite where producer state is provably not yet valid

### Phase 3 — Solid Foundation (Keep As-Is)

These are correct, architecture-aligned, and should remain as-is:

- I-1, I-2, I-3, I-4: infrastructure (copy mode, ROM relocation, shift table, patcher)
- H-1, H-2, H-3, H-4, H-6, H-7: hardware shadow mappings
- T-2: tile plane clear → text shadow (correct)
- T-3, T-6: scroll redirects (correct)
- T-4, T-5: text dispatch hook plumbing (correct)
- T-8, T-10, T-14, T-15: selective C-Window write NOPs (correct; prevent unmapped writes)
- T-13: display control NOPs (mostly correct; individual review if regressions appear)
- D-1, D-2, D-3, D-4, D-6: descriptor producer retargets (correct direction, need symbol fixup in Phase 2)
- C-6: scroll from workram VDP (correct)
- C-9: tile attribute builder (correct)
- C-7 (function kept): genesistan_sync_title_vdp_layout (keep the function; fix calling pattern in Phase 2)

---

## 8. Final Recommendations

### Priority 1: Undo contamination before any new work

Revert D-5 (attr force), D-7 (RTS extension), T-9 (0x0560DA NOP block), C-3/C-4
(col/row counter hooks) in one batch. These make the codebase lie about arcade intent
and will corrupt any analysis or new implementation built on top of them.

### Priority 2: Fix producer/renderer ordering at 0x03AAB8

Per `rastan_vblank_and_vdp_buffer_architecture.md` Section 12:
swap the call order of `0x03AAEC` (renderer) and `0x03AAF2` (producer) in the title init
cluster. Implement as two explicit opcode_replace entries with `original_bytes` validation,
not via D-7's RTS extension.

### Priority 3: Implement VBlank publish pipeline

The single largest architectural gap. Add the VBlank-driven publish sequence:
SAT staging → DMA, text shadow → DMA, scroll → VSRAM.
This does NOT require reverting existing changes; it adds missing work on top of Phase 3 foundation.

### Priority 4: Symbol-ify hardcoded WRAM addresses

Convert all `0xE0FF...` addresses in replacement_bytes to `{symbol:...}` form.
This makes the spec robust against WRAM layout changes.

### Priority 5: Implement real tilemap address decoding

After reverting C-3/C-4 col/row counters, implement proper destination-address decoding
for the tilemap plane hooks. Map arcade C-Window destination address → Genesis plane
cell index → VDP nametable write. This follows the Rainbow Islands pattern confirmed
in the comparative research.
