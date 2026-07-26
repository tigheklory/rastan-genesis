# Rastan Arcade — PC080SN Whole-ROM Access Inventory

Whole-ROM static inventory of every 68000 access to the PC080SN space. Authority: opcodes → Ghidra → MAME map (ranges only). Neutral tilemap names. Coverage baseline: full `linear_disassembly.tsv` (121,606 lines) searched for the PC080SN immediate ranges + all pointer-base immediates + reconciled against the 77 Genesis PC080SN replacement sites.

## 1. PC080SN arcade memory map
| Range | R/W (by Rastan CPU) | Meaning | Rastan uses? |
|---|---|---|---|
| **0xC00000–0xC03FFF** | R/W | name RAM quadrant — **`pc080sn_tilemap0_0xC00000`** (content-bearing) | yes |
| 0xC04000–0xC07FFF | R/W | name RAM quadrant — used as tilemap1 cursor in sel==1 scenes (0x050420) | some scenes |
| **0xC08000–0xC0BFFF** | R/W | name RAM quadrant — **`pc080sn_tilemap1_0xC08000`** (content-bearing; gameplay + text/HUD) | yes |
| 0xC0C000–0xC0FFFF | (cleared only) | name RAM quadrant — no gameplay content observed | boot-clear only |
| **0xC20000 / 0xC20002** | **W only** | scroll layer-A X / Y (fed `a5@0x10EE / a5@0x10B0`) | yes |
| **0xC40000 / 0xC40002** | **W only** | scroll layer-B X / Y (fed `a5@0x10EC / a5@0x10AE`) | yes |
Cell format (both content tilemaps): 2 words — word0 (even)=source/control word (runtime 0x0003, bits undecoded), word1 (odd)=tile. No separate CPU-visible control register is accessed by Rastan. (Note: whether the four 0x4000 quadrants are two tilemaps + two mirrors, or a chip-specific split, is a PC080SN-hardware detail — see unresolved; Rastan only content-writes the 0xC00000 and 0xC08000 quadrants.)

## 2. Direct access sites (immediate PC080SN address)
| Arcade PC(s) | Op | R/W | Target | Subsystem |
|---|---|---|---|---|
| `0x00016A`,`0x000170` | `lea 0xc2/c40002,%a` | — (ptr) | scroll | boot scroll-ptr setup |
| `0x0002CA…0x00069A` (~30 `lea`) | `lea 0xc0xxxx,%a` | — (ptr) | tilemap0/1 quadrants | boot init copy roots |
| `0x00054A`,`0x000550`,`0x00055A`,`0x000560` | `lea 0xc00000/04000/08000/0c000` | W(loop) | all 4 quadrants | boot clear |
| `0x03A350`,`0x03A6FE`,`0x03A708`,`0x03A72A`,`0x03AAEA`,`0x03D04C` | `movew #imm/%d,0xc08xxx` | **W** | tilemap1 cells | inline FG/text writes |
| `0x03A47E`,`0x03A552`,`0x03AC54` | `cmpi[w/b] #imm,0xc0xxxx` | **R** | tilemap1 cells | text/HUD compare-reads |
| `0x03A55C` | `moveb #32,0xc09ea3` | W | tilemap1 | text write |
| `0x03ABBA`,`0x03ABC0`,`0x03B098`,`0x03B09E` | `clrl 0xc20000/c40000` | W | scroll | frontend scroll clear |
| `0x03AE64`,`0x03AE74`,`0x03AF2C`,`0x03AF3C`,`0x03AF52`,`0x03AF62` | `lea 0xc00100/08100/00000/08000/04000/0c000` | W(loop) | quadrants | dispatch/clear (0x03AD44 family) |
| `0x03B192…0x03B5B2` (~10 `lea`) | `lea 0xc08xxx/09xxx,%a` | — (ptr) | tilemap1 | number/text writers |
| `0x055AB4`,`0x055ABC`,`0x055AC4`,`0x055ACC` | `movew a5@,0xc2/c4` | **W** | scroll | gameplay scroll commit |

## 3. Indirect / shared access roots (pointer-derived destinations)
| Root PC | Sets | Base | Reaches | Callers / family |
|---|---|---|---|---|
| `0x0503EC` | `a5@0x10A0` | 0xC08000 | tilemap1 | scene-init cursor seed (0x0503xx) |
| `0x050400` | `a5@0x10A4` | 0xC08000 | tilemap1 | scene-init cursor seed |
| `0x0503F6`,`0x05040C` | `0x10D0F8` | 0xC00000 | tilemap0 | scene-init cursor seed (3rd cursor) |
| `0x050420` | `%d0` | 0xC04000 | quadrant | scene-init |
| `0x055818`,`0x0556F2`,`0x05577E` | `a5@0x10A0/0x10A4` (`addil #0xC08000`) | 0xC08000 | tilemap1 | **gameplay triggers** (H 0x055808 / V 0x0556E0) → 0x055948 |
| `0x055E54` | `a5@0x10A0` | 0xC00400 | **tilemap0** | state-gated (guard `a5@0x13AA==2`) — one proven tilemap0 cursor |
| `0x0561C0`,`0x0561C6` | `%a0`,`%a1` | 0xC08000, 0xC00000 | both | C-window clear (0x0561B6) / item-page |
| `0x056032`,`0x05605C`,`0x0578E0` | `%a1` | 0xC00xxx | tilemap0 | item/status page |
| `0x052858`,`0x052974` | `%a0` | 0xC08000 | tilemap1 | 0x052xxx scene family |
| `0x05A370…0x05A456` (`0x05A38E`,`0x05A3C0`,`0x05A3F2`,`0x05A424`,`0x05A456`) | `%a1` src, dest via descriptor | 0xC0xxxx | quadrants | **block-copy engine 0x05A4DE** (frontend art) |
| gameplay cell writers `0x0559B2`/`0x055A14` | via `a0` cursor | 0xC08000 | tilemap1 + collision 0x10DE00 | 0x055968/0x055990 (see core_publishers) |
| text/glyph writers `0x03C4D2…0x03C950`,`0x03BB48`,`0x03C2E2` | computed `base+off` | 0xC08xxx/09xxx | tilemap1 | HUD/text/number/highscore |

Descriptor rebuild `0x055904` fills the source/descriptor tables (0x10D040/0x10D080) consumed by the gameplay cell writers (not a direct PC080SN access itself).

## 4. Classification by subsystem
- **Gameplay tilemap1 publication:** 0x055948/0x055968/0x055990/0x0559B2/0x055A14 (+ triggers 0x055808/0x0556E0; cursors 0xC08000). Collision co-produced at 0x10DE00.
- **Tilemap0 init/streaming:** 0x055E54 (0xC00400), scene-init 0x0503F6/0x05040C (0x10D0F8=0xC00000), item-page 0x056032/0x05605C/0x0561C6. **Incomplete — see unresolved.**
- **Scene initialization & clearing:** boot clear 0x00054A–0x000560 (all quadrants); dispatch/clear 0x03AF2C-0x03AF62; C-window clear 0x0561B6; scene-init cursor seeds 0x0503xx / 0x052xxx.
- **Frontend/title/attract composition:** block-copy 0x05A4DE + descriptors 0x05A370–0x05A456; 0x00016A/0x0002xx–0x00069A boot art roots.
- **Item / status page:** 0x055C2E (populate), 0x055C5E (blit), 0x056032/0x05605C/0x0561C0.
- **HUD / text / numbers / high-score:** inline FG 0x03A350/0x03A6FE/0x03A708/0x03A72A/0x03AAEA/0x03D04C; text writers 0x03C4D2…0x03C950 + dispatch 0x0563A6; glyph 0x03BB48; number 0x03C2E2; high-score 0x03C3FE; compare-reads 0x03A47E/0x03A552/0x03AC54.
- **Scroll / control publication:** gameplay 0x055AB4; frontend clears 0x03ABBA/0x03ABC0/0x03B098/0x03B09E; boot 0x00016A.
- **Shared block-copy / fill primitive:** 0x05A4DE (block-copy engine, multi-scene); 0x03AD44 (polymorphic dispatch → tilemap fills); boot/C-window clear loops.
- **Readback access:** 0x03A47E, 0x03A552, 0x03AC54 (name-RAM compare-reads).

## 5. Call-root summary
- **Vector/boot:** 0x00016A + 0x0002xx–0x00069A + 0x00054A (init art + clear).
- **Frontend/attract dispatch:** 0x03AD44 family (fills/dispatch), 0x03Axxx inline/text, 0x03Bxxx/0x03Cxxx text/number, block-copy 0x05A4DE.
- **Scene setup:** 0x0503xx / 0x0512xx / 0x0526xx–0x0528xx / 0x052BC8 (per-scene cursor/descriptor seeds; many in the Genesis replacement leads).
- **Gameplay per-frame:** triggers 0x055808/0x0556E0 → 0x055948 → publishers → cells; scroll commit 0x055AB4.
- **Item/status:** 0x055C2E/0x055C5E + 0x056032.

## 6. Readback conclusion — **CPU READBACK: YES (name RAM only, compare-reads)**
The arcade **reads PC080SN name RAM**: `cmpiw #73,0xc0883a` (0x03A47E), `cmpib #48,0xc09ea3` (0x03A552), `cmpib #67,0xc09e87` (0x03AC54) — read-only compares of existing tile cells (text/HUD conditional logic), **not** read-modify-write of tile data. Scroll and (no separate) control registers are **write-only** (only `clr`/`move` stores; no read observed anywhere in the ROM). So Rastan's PC080SN interaction is **write-dominant but not write-only**: the Genesis translation must satisfy those three name-RAM compare-reads (all are in the replacement-site set), while scroll/control can be treated write-only.

## 7. Coverage method
Full disassembly searched for: (a) hex immediates `0xc0xxxx`/`0xc2xxxx`/`0xc4xxxx`; (b) decimal immediates in the PC080SN ranges (12582912–12648447, 12713984, 12845056) used as pointer/cursor bases; (c) the 77 Genesis PC080SN-related `opcode_replace` sites reconciled as leads and each verified to an arcade PC above. Direct accesses = complete. Indirect accesses = enumerated by pointer-base root (not per-iteration).

## 8. Unresolved possible accesses
See `unresolved.md` items 5–7: (5) complete tilemap0 producer set (which 0x050xxx/0x052xxx sites write 0xC00000 vs 0xC08000); (6) whether 0xC04000/0xC0C000 quadrants are ever content-written (or pure mirror/clear); (7) individual computed cell targets inside the text/number writers (0x03Cxxx) — classified by base, per-cell targets not enumerated (acceptable per scope).

## 9. Recommended reconstruction order (later checkpoints)
1. **Gameplay triggers + camera/scroll + 64-row ring** (0x055808/0x0556E0/0x055948 already partly done) — highest port value.
2. **Scene initialization / tilemap0 producer set** (0x0503xx/0x055E54/0x052xxx) — resolves unresolved #5/#6.
3. **Shared clear/fill + block-copy primitive** (0x05A4DE, 0x0561B6, 0x03AD44) — needed by both gameplay and frontend.
4. **HUD/text/number/high-score + the three compare-reads** (0x03Axxx/0x03Bxxx/0x03Cxxx) — the read-back path.
5. **Item/status page** (0x055C2E/0x055C5E) — lowest gameplay priority.
