# Build 318 — VDP Plane Base / Nametable / Pattern Region Correlation Audit

## 1. VDP Register State

All register values are set by `force_clean_vram_init()` in [main.c:2062-2079](apps/rastan/src/main.c#L2062-L2079), and also by `genesistan_sync_title_vdp_layout()` at [main.c:1430-1439](apps/rastan/src/main.c#L1430-L1439) via SGDK wrappers. Both set identical values.

| Register | Raw Value | Data Byte | Decoded VRAM Address | Description |
|----------|-----------|-----------|---------------------|-------------|
| 2 | 0x8238 | 0x38 | 0xE000 | Plane A (FG) nametable base. Bits [5:3] = 7, shifted left by 13 = 0xE000 |
| 3 | 0x8334 | 0x34 | 0xD000 | Window plane base. Bits [5:1] = 0x1A, shifted left by 11 = 0xD000 |
| 4 | 0x8406 | 0x06 | 0xC000 | Plane B (BG) nametable base. Bits [2:0] = 6, shifted left by 13 = 0xC000 |
| 5 | 0x857C | 0x7C | 0xF800 | SAT base. Bits [6:1] = 0x3E, shifted left by 9 = 0xF800 |
| 13 | 0x8D3C | 0x3C | 0xF000 | HScroll table base. Bits [5:0] = 0x3C, shifted left by 10 = 0xF000 |
| 16 | 0x9001 | 0x01 | 64x32 | Scroll size. H=64 (bits [1:0]=1), V=32 (bits [5:4]=0) |

**Nametable size**: 64 columns x 32 rows x 2 bytes/entry = **4096 bytes (0x1000)**

## 2. Actual Nametable Write Targets

From `genesistan_pc080sn_commit_planes` in [startup_trampoline.s:800-822](apps/rastan/src/startup_trampoline.s#L800-L822):

| Plane | VDP Command | Decoded VRAM Address | Buffer Source | Words Written | Write Mode |
|-------|-------------|---------------------|---------------|---------------|------------|
| BG (Plane B) | 0x40000003 | **0xC000** | `pc080sn_bg_buffer` | 2048 | Full-plane, word-by-word, auto-increment |
| FG (Plane A) | 0x60000003 | **0xE000** | `pc080sn_fg_buffer` | 2048 | Full-plane, word-by-word, auto-increment |

Both use auto-increment = 2 (set by `move.w #0x8F02, (%a1)` at line 803).

## 3. Read vs Write Correlation

| Plane | VDP Reads From (Register) | Engine Writes To (Command) | Match? |
|-------|--------------------------|---------------------------|--------|
| Plane A (FG) | 0xE000 (reg 2 = 0x38) | 0xE000 (cmd 0x60000003) | **MATCH** |
| Plane B (BG) | 0xC000 (reg 4 = 0x06) | 0xC000 (cmd 0x40000003) | **MATCH** |

**Both plane nametable write targets exactly match the VDP register base addresses.**

## 4. Pattern Region Overlap Check

### VRAM Layout

| Address Range | Size | Purpose |
|--------------|------|---------|
| 0x0000 - 0xBFFF | 48 KB | Tile pattern data (tiles 0-1535) |
| 0xC000 - 0xCFFF | 4 KB | Plane B (BG) nametable |
| 0xD000 - 0xDFFF | 4 KB | Window plane nametable |
| 0xE000 - 0xEFFF | 4 KB | Plane A (FG) nametable |
| 0xF000 - 0xF003 | 4 B | HScroll table (full-screen mode) |
| 0xF004 - 0xF7FF | ~2 KB | Unused |
| 0xF800 - 0xFA7F | 640 B | SAT (sprite attribute table) |
| 0xFA80 - 0xFFFF | ~1.4 KB | Unused |

### Address 0xE700 Analysis

The user observed tile block 0x0738 at VRAM address 0xE700.

- 0xE700 is at offset 0x0700 from Plane A base (0xE000)
- That is nametable word 896 = **row 14, column 0**
- 0xE700 falls within **Plane A nametable** range (0xE000-0xEFFF)
- **This is NOT pattern memory** — it is a nametable entry

The value 0x0738 at that address is a **nametable word** that references tile index 0x738 (with no palette/flip bits set in the upper bits, or possibly with attributes). This tells the VDP to render pattern tile 0x738 at row 14, column 0.

### Is pattern memory being displayed as nametable?

**NO.** The VDP is correctly reading from the nametable region. The nametable entries themselves reference tile indices in the pattern area. This is normal VDP operation.

## 5. Tile Index Correlation

The visible band in the user's screenshots shows colored dots at approximately row 14-15.

- The nametable at row 14 (VRAM 0xE700) contains non-zero entries (e.g., tile index 0x0738)
- Tile 0x0738 is a valid PC080SN scene preload tile in pattern memory
- The dots represent these tiles rendered with the debug palette (palette line 0 = red)
- The rest of the screen (rows 0-13, 16-31) shows black because those nametable entries are 0x0000 (tile 0, palette 0, entry 0 = black)

**The nametable correctly references tile indices. The tiles are rendering with the debug palette.**

The sparse dots rather than filled tiles indicate that most pixels in these tiles use color index 0 (black/transparent), with only a few pixels using higher color indices — consistent with text/font tiles or sparse decorative tiles.

## 6. Scroll State Verification

### HScroll

The scroll commit function writes HScroll data using VDP command **0x7C000003**.

**BUG CONFIRMED**: This command decodes to VRAM address **0xFC00**, not 0xF000.

- VDP register 13 says HScroll table is at 0xF000
- Scroll commit writes HScroll data to 0xFC00
- **The VDP reads stale/zero HScroll data from 0xF000** — HScroll is effectively always 0

The correct command should be **0x70000003** (VRAM write at 0xF000).

However, in the isolation build, scroll commit is RTS'd, so this bug has no effect there. The HScroll values are 0 (from VRAM clear), which means no horizontal offset — correct for title screen.

### VScroll

VScroll uses VSRAM command 0x40000010 (VSRAM write at address 0). This is correct.

In the isolation build, scroll commit is RTS'd, so VSRAM stays at 0 (from the VSRAM clear in `force_clean_vram_init`). No vertical offset.

### Scroll Causing Misalignment?

**NO** — in the isolation build, scroll is disabled (function RTS'd). Both H and V scroll are 0. The visible band at row ~14 is from actual nametable content, not scroll-induced misalignment.

## 7. Final Determination

| Question | Answer |
|----------|--------|
| Is Plane A base correct? | **YES** — reg 2 = 0x38, Plane A reads from 0xE000 |
| Is Plane B base correct? | **YES** — reg 4 = 0x06, Plane B reads from 0xC000 |
| Is tilemap written to same region VDP reads? | **YES** — FG commit writes to 0xE000, BG commit writes to 0xC000 |
| Is pattern memory being interpreted as tilemap? | **NO** — VDP reads from correct nametable regions |

### Primary Root Cause Classification

**OTHER**: The VDP plane bases, nametable write targets, and display configuration are all correct and consistent. The visible band of dots is real nametable content — specifically, the title text writer tiles written to rows ~14-15 of the FG nametable via `rastan_draw_tile_xy()` → `pc080sn_fg_buffer`. The remainder of the nametable is zero (tile 0, palette line 0, color 0 = black).

The display is working correctly. The apparent problem is that:
1. Only title text occupies a narrow band — the rest of the nametable is empty
2. In the isolation build, no gameplay tilemap hooks fire (only the text writer populates the FG buffer)
3. The BG buffer is entirely empty (no BG producer during title/attract mode)

### Separate Bug Found: HScroll Write Address

The HScroll commit in `genesistan_scroll_commit_vdp()` uses command `0x7C000003` which writes to VRAM 0xFC00 instead of the intended 0xF000. The correct command is `0x70000003`. This bug exists in the non-isolated build and means horizontal scroll never takes effect.
