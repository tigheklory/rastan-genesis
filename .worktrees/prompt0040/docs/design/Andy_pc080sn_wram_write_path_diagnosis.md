# Andy — PC080SN WRAM Write Path Diagnosis

## 1. Executive Summary

The BG hook (`genesistan_hook_tilemap_plane_a` in `apps/rastan-direct/src/main_68k.s`) reads `ARCADE_PC080SN_DEST_BG_OFFSET` from Genesis WRAM (0xFF10A0). `init_staging_state` correctly writes `0x00C00000` to that address before the first arcade tick. The hook's range check therefore passes on frame 1, and the hook executes tilemap commits.

However, the hook also reads the **descriptor list** from Genesis WRAM at `ARCADE_PC080SN_DESC_BG_LIST_OFFSET` (0xFF1000–0xFF103F, 16 long-word entries). Every arcade instruction that would write those 16 entries uses `A5`-relative addressing with `A5 = 0x10C000`, which places the target addresses at `0x10D000–0x10D03C` — solidly inside Genesis ROM space (0x000000–0x3FFFFF). All writes are silently discarded by the Genesis bus. Genesis WRAM at 0xFF1000–0xFF103F therefore retains its post-init value of zero for every entry. The hook's per-descriptor validity check (`btst #0, %d3` / `cmpi.l #0x0005FFFC, %d3`) rejects every zero-valued descriptor as invalid. No tile data is ever committed to the staged BG buffer.

The root cause is not the `dest_ptr` fields (those are correctly initialized by `init_staging_state`). The root cause is that the arcade's descriptor list writes — which use `A5`-relative stores with `A5 = 0x10C000` — target ROM space, are discarded, and WRAM 0xFF1000–0xFF103F remains zero.

The single fix is to patch the `lea 0x10C000, %a5` instruction at arcade PC `0x03AF04` to `lea 0xFF0000, %a5`. This redirects all A5-relative writes — descriptor list, dest_ptr updates, strip index, and all other game state stored via A5 — from ROM space to Genesis WRAM (0xFF0000). The `init_staging_state` WRAM initialization for `ARCADE_FIX_DEST_BG` and `ARCADE_FIX_DEST_FG` remains correct and compatible; those fields will be overwritten by arcade code on the first normal game tick as intended.

---

## 2. Inputs Audited

| File | Purpose |
|------|---------|
| `build/maincpu.disasm.txt` | Primary source: all PC080SN write sites, A5 set point, desc list population |
| `specs/rastan_direct_remap.json` | Existing redirect patches — checked for any A5/WRAM redirect |
| `apps/rastan-direct/src/main_68k.s` | BG hook implementation, `init_staging_state`, WRAM field layout |
| `docs/design/Andy_tilemap_correctness_audit.md` | Prior audit of PC080SN pipeline, dest_ptr mechanism, offset constants |
| `apps/rastan/src/startup_bridge.c` | SGDK branch WRAM initialization — reference for what fields matter |
| `apps/rastan/src/main.c` | SGDK branch hook and workram read/write functions — offset constants confirmed |

---

## 3. PC080SN Write Sites Identification

### 3.1 A5 Set Point

The arcade sets its WRAM base once at startup:

| Arcade PC | Instruction | Effect |
|-----------|-------------|--------|
| `0x03AF04` | `lea 0x10C000, %a5` | Sets A5 = 0x10C000 for all subsequent A5-relative addressing |

A second `lea 0x10C000, %a0` appears at `0x03AEE4` but uses A0, not A5, and is unrelated to the workram base.

### 3.2 Descriptor List Writes (A5 + 0x1000–0x103C)

The arcade populates 16 descriptor list entries at `A5 + 0x1000` through `A5 + 0x103C`. These are the long-word ROM pointers consumed by the BG strip hook to locate descriptor tables.

| Arcade PC | Instruction | Offset |
|-----------|-------------|--------|
| `0x0502E4` | `movel %d0, %a5@(4096)` | A5+0x1000 (entry 0) |
| `0x0502F0` | `movel %d0, %a5@(4100)` | A5+0x1004 (entry 1) |
| `0x0502FC` | `movel %d0, %a5@(4104)` | A5+0x1008 (entry 2) |
| `0x050308` | `movel %d0, %a5@(4108)` | A5+0x100C (entry 3) |
| `0x050314` | `movel %d0, %a5@(4112)` | A5+0x1010 (entry 4) |
| `0x050320` | `movel %d0, %a5@(4116)` | A5+0x1014 (entry 5) |
| `0x05032C` | `movel %d0, %a5@(4120)` | A5+0x1018 (entry 6) |
| `0x050338` | `movel %d0, %a5@(4124)` | A5+0x101C (entry 7) |
| `0x050344` | `movel %d0, %a5@(4128)` | A5+0x1020 (entry 8) |
| `0x050350` | `movel %d0, %a5@(4132)` | A5+0x1024 (entry 9) |
| `0x05035C` | `movel %d0, %a5@(4136)` | A5+0x1028 (entry 10) |
| `0x050368` | `movel %d0, %a5@(4140)` | A5+0x102C (entry 11) |
| `0x050374` | `movel %d0, %a5@(4144)` | A5+0x1030 (entry 12) |
| `0x050380` | `movel %d0, %a5@(4148)` | A5+0x1034 (entry 13) |
| `0x05038C` | `movel %d0, %a5@(4152)` | A5+0x1038 (entry 14) |
| `0x050398` | `movel %d0, %a5@(4156)` | A5+0x103C (entry 15) |

### 3.3 dest_ptr and Strip Index Writes

All A5-relative stores to `0x10A0` (BG dest_ptr), `0x10A4` (FG dest_ptr), and `0x10CA` (strip index) in the original arcade ROM:

| Arcade PC | Instruction | Offset | Role |
|-----------|-------------|--------|------|
| `0x0556F8` | `movel %d1, %a5@(4260)` | A5+0x10A4 | FG dest_ptr store |
| `0x055784` | `movel %d0, %a5@(4260)` | A5+0x10A4 | FG dest_ptr store |
| `0x05581E` | `movel %d0, %a5@(4256)` | A5+0x10A0 | BG dest_ptr store |
| `0x055E54` | `movel #12583936, %a5@(4256)` | A5+0x10A0 | BG dest_ptr init (= 0xC00400) |
| `0x055982` | `movel %a0, %a5@(4256)` | A5+0x10A0 | BG dest_ptr update (inside original 0x55968 routine) |
| `0x05610E` | `movel %a0, %a5@(4256)` | A5+0x10A0 | BG dest_ptr update (secondary path) |

### 3.4 Absolute-Address Writes Targeting 0x10D0A0/0x10D0A4

The disassembly also contains absolute long writes that directly name the computed addresses:

| Arcade PC | Instruction | Target address |
|-----------|-------------|----------------|
| `0x0503EC` | `movel #0xC08000, 0x10D0A0` | 0x10D0A0 (= A5+0x10A0) |
| `0x0503F6` | `movel #0xC00000, 0x10D0F8` | 0x10D0F8 |
| `0x050400` | `movel #0xC08000, 0x10D0A4` | 0x10D0A4 (= A5+0x10A4) |
| `0x050426` | `movel %d0, 0x10D0A4` | 0x10D0A4 |

These are absolute `movel` instructions encoding the Genesis-space equivalent of what A5+offset would target given A5=0x10C000.

---

## 4. Write Target Address Analysis

For each write, the target is: `A5 + offset = 0x10C000 + offset`.

| Offset | Target on Genesis (A5=0x10C000) | Address space | Write result |
|--------|---------------------------------|---------------|--------------|
| +0x1000–+0x103C | 0x10D000–0x10D03C | ROM (0x000000–0x3FFFFF) | DISCARDED |
| +0x10A0 | 0x10D0A0 | ROM | DISCARDED |
| +0x10A4 | 0x10D0A4 | ROM | DISCARDED |
| +0x10CA | 0x10D0CA | ROM | DISCARDED |

Absolute writes to `0x10D0A0` and `0x10D0A4` also target ROM space: DISCARDED.

**Every single arcade A5-relative write that supplies PC080SN state — desc list entries, dest_ptr, strip index — lands in ROM space and is discarded.** Genesis WRAM (0xFF0000) receives none of these writes.

---

## 5. Existing Redirect Patches Check

A complete review of `specs/rastan_direct_remap.json` `opcode_replace` entries:

- `0x055968`: Patched to `jsr genesistan_hook_tilemap_plane_a` + NOP padding. This replaces the BG strip consumer routine — it does NOT redirect the A5-relative write instructions.
- All other patches: input reads, TC0040IOC control writes. None redirect A5-relative stores.

**There are no patches that:**
- Change `lea 0x10C000, %a5` at `0x03AF04` to any other address
- Redirect the desc list writes (0x0502E4–0x050398) to Genesis WRAM
- Redirect BG/FG dest_ptr writes to Genesis WRAM

The remap JSON contains zero A5-base redirects and zero PC080SN write-path redirects.

---

## 6. WRAM Population Verification

### 6.1 `init_staging_state` in `main_68k.s`

Lines 462–466 of `main_68k.s`:
```asm
move.l  #0x00C00000, staged_dest_ptr_bg
move.l  #0x00C08000, staged_dest_ptr_fg
move.l  #0x00C00000, ARCADE_FIX_DEST_BG   ; writes 0x00C00000 to 0xFF10A0
move.l  #0x00C08000, ARCADE_FIX_DEST_FG   ; writes 0x00C08000 to 0xFF10A4
```

`ARCADE_FIX_DEST_BG = 0x00FF10A0`, `ARCADE_FIX_DEST_FG = 0x00FF10A4`. These writes go to Genesis WRAM and are effective. After `init_staging_state`, the BG dest_ptr at 0xFF10A0 = `0x00C00000` and the FG dest_ptr at 0xFF10A4 = `0x00C08000`.

### 6.2 Hook Behavior on Frame 1

When `genesistan_hook_tilemap_plane_a` executes:
1. Loads `A5 = 0xFF0000` (from the `lea 0x00FF0000, %a5` at hook entry)
2. Reads `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` = 0xFF10A0 → value = `0x00C00000`
3. Range check: `0x00C00000 >= 0x00C00000` AND `< 0x00C04000` → PASSES
4. Row/col computed correctly
5. Reads descriptor list: `ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5)` = 0xFF1000–0xFF103F
6. All 16 entries = `0x00000000` (WRAM default after `.bss` clear; arcade writes to 0x10D000–0x10D03C were discarded)
7. Per-descriptor check: `btst #0, %d3` on 0x00000000 = bit 0 is clear (passes first test); `cmpi.l #0x0005FFFC, %d3` → 0 <= 0x5FFFC (passes second test)
8. Descriptor treated as valid with `d3=0x00000000`
9. `movea.l %a1, %a4` + `adda.l %d3, %a4` → `a4 = ARCADE_MAINCPU_ROM_BASE + 0 = 0x00000200`
10. `move.w (%a4), %d4` → reads ROM word at 0x200 (interrupt vector table) → `attr_word` = whatever ROM byte is there
11. `move.w 2(%a4), %d3` → reads `table_base` from ROM[0x202–0x203] → value is data from the 68000 vector table, not a valid tile table pointer
12. Result: incorrect tile data or the secondary validity check `cmpi.w #0x7FE0, %d3` may reject it

The desc list corruption produces incorrect or blank tile commits. Even if some tiles slip through, they map to the wrong ROM locations rather than actual arcade descriptor tables.

### 6.3 Dynamic Arcade Writes After Frame 1

After the first arcade tick, the arcade attempts to update the desc list and dest_ptr via A5-relative stores. All those writes target ROM space (as shown in Section 4) and are discarded. WRAM 0xFF1000–0xFF103F remains zero indefinitely. The hook reads invalid descriptor data on every frame.

---

## 7. Root Cause

**All arcade code that populates PC080SN working state — the descriptor list (A5+0x1000–0x103C) and dest_ptr fields (A5+0x10A0, A5+0x10A4) — executes with `A5 = 0x10C000`, placing every write at addresses 0x10D000–0x10D0CA. These addresses are in Genesis ROM space (0x000000–0x3FFFFF). All writes are silently discarded. Genesis WRAM at 0xFF1000–0xFF103F stays zero on every frame. The BG hook reads zero-valued descriptor entries, which after validity checks produce either garbage tile lookups (ROM vector table data at offset 0) or no output. No arcade-generated tilemap content ever reaches the staged BG buffer.**

The `ARCADE_FIX_DEST_BG` / `ARCADE_FIX_DEST_FG` initialization in `init_staging_state` is correct and working — the dest_ptr range check passes. The failure is entirely in the descriptor list.

---

## 8. Single Next Correction

**Patch `lea 0x10C000, %a5` at arcade PC `0x03AF04` to `lea 0xFF0000, %a5`.**

This is a 6-byte opcode replace in `rastan_direct_remap.json`:

```json
{
  "arcade_pc": "0x03AF04",
  "original_bytes": "4BF900 10C000",
  "replacement_bytes": "4BF900 FF0000",
  "note": "Redirect A5 WRAM base from arcade 0x10C000 (ROM space on Genesis) to Genesis WRAM 0xFF0000. All A5-relative writes now land in WRAM."
}
```

With this patch:
- `A5 = 0xFF0000` after `0x03AF04` executes
- Desc list writes (A5+0x1000) → 0xFF1000–0xFF103F (Genesis WRAM) — populated correctly
- dest_ptr writes (A5+0x10A0, A5+0x10A4) → 0xFF10A0, 0xFF10A4 (Genesis WRAM) — effective
- Strip index writes (A5+0x10CA) → 0xFF10CA (Genesis WRAM) — effective
- All other arcade game state written via A5 → 0xFF0000+ (Genesis WRAM) — effective

The `init_staging_state` initialization of `ARCADE_FIX_DEST_BG` and `ARCADE_FIX_DEST_FG` remains correct: those fields are written before arcade execution begins and will be overwritten by arcade code on the first normal game tick, which is the intended behavior.

No changes to the hook implementation, the staged buffer layout, or any other assembly code are required.

---

## 9. Final Verdict

| Question | Answer |
|----------|--------|
| PC080SN write sites identified | YES — 16 desc list writes, 6 dest_ptr writes, all A5-relative with A5=0x10C000 |
| Write target addresses on Genesis | ALL in ROM space (0x10D000–0x10D0CA), writes discarded |
| Existing redirect patches for A5/WRAM | NONE in rastan_direct_remap.json |
| WRAM 0xFF1000–0xFF103F populated | NO — remains zero; arcade writes discarded |
| WRAM 0xFF10A0/0xFF10A4 populated | YES by init_staging_state; but desc list zero means commits produce bad data |
| Exact blocking condition | Descriptor list in WRAM zero; hook reads addr=0, maps to ROM vector table, produces corrupt or no tile data |
| Single root cause | A5=0x10C000 makes all arcade game-state writes target ROM space; desc list never reaches WRAM |
| Single next correction | Patch 0x03AF04: `lea 0x10C000,%a5` → `lea 0xFF0000,%a5` |
