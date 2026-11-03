# Cody MAME PC080SN Extraction (Task 2)

## 2A. MAME Version and Source Paths

- MAME binary: `MAME v0.276 (unknown)`
- Source files extracted for this run:
  - `/tmp/mame_src/pc080sn.cpp` (from `https://raw.githubusercontent.com/mamedev/mame/mame0276/src/mame/taito/pc080sn.cpp`)
  - `/tmp/mame_src/rastan.cpp` (from `https://raw.githubusercontent.com/mamedev/mame/mame0276/src/mame/taito/rastan.cpp`)

## 2B. Tilemap RAM Layout (Verbatim Source Excerpts)

```cpp
Standard memory layout (two 64x64 tilemaps with 8x8 tiles)

0000-3fff BG
4000-41ff BG rowscroll      (only verified to exist on Topspeed)
4200-7fff unknown/unused?
8000-bfff FG    (FG/BG layer order fixed per game; Topspeed has BG on top)
c000-c1ff FG rowscroll      (only verified to exist on Topspeed)
c200-ffff unknown/unused?

Double width memory layout (two 128x64 tilemaps with 8x8 tiles)

0000-7fff BG
8000-ffff FG
(Tile layout is different; tiles and colors are separated:
0x0000-3fff  color / flip words
0x4000-7fff  tile number words)

```
```cpp
	m_ram = make_unique_clear<u16[]>(PC080SN_RAM_SIZE / 2);

	m_bg_ram[0]       = m_ram.get() + 0x0000 /2;
	m_bg_ram[1]       = m_ram.get() + 0x8000 /2;
	m_bgscroll_ram[0] = m_ram.get() + 0x4000 /2;
	m_bgscroll_ram[1] = m_ram.get() + 0xc000 /2;

```
```cpp
void rastan_state::main_map(address_map &map)
{
	map(0x000000, 0x05ffff).rom();
	map(0x10c000, 0x10ffff).ram();
	map(0x200000, 0x200fff).ram().w("palette", FUNC(palette_device::write16)).share("palette");
	map(0x350008, 0x350009).nopw();    // 0 only (often) ?
	map(0x380000, 0x380001).w(FUNC(rastan_state::spritectrl_w));  // sprite palette bank, coin counters & lockout
	map(0x390000, 0x390001).portr("P1");
	map(0x390002, 0x390003).portr("P2");
	map(0x390004, 0x390005).portr("SPECIAL");
	map(0x390006, 0x390007).portr("SYSTEM");
	map(0x390008, 0x390009).portr("DSWA");
	map(0x39000a, 0x39000b).portr("DSWB");
	map(0x3c0000, 0x3c0001).w("watchdog", FUNC(watchdog_timer_device::reset16_w));
	map(0x3e0000, 0x3e0001).nopr();
	map(0x3e0001, 0x3e0001).w("ciu", FUNC(pc060ha_device::master_port_w));
	map(0x3e0003, 0x3e0003).rw("ciu", FUNC(pc060ha_device::master_comm_r), FUNC(pc060ha_device::master_comm_w));
	map(0xc00000, 0xc0ffff).rw(m_pc080sn, FUNC(pc080sn_device::word_r), FUNC(pc080sn_device::word_w));
	map(0xc20000, 0xc20003).w(m_pc080sn, FUNC(pc080sn_device::yscroll_word_w));
	map(0xc40000, 0xc40003).w(m_pc080sn, FUNC(pc080sn_device::xscroll_word_w));
	map(0xc50000, 0xc50003).w(m_pc080sn, FUNC(pc080sn_device::ctrl_word_w));
	map(0xd00000, 0xd03fff).rw(m_pc090oj, FUNC(pc090oj_device::word_r), FUNC(pc090oj_device::word_w));  // sprite ram
}
```

Derived values:
- Arcade map for Rastan PC080SN: `0xC00000-0xC0FFFF` (`word_r/word_w`).
- PC080SN RAM size in device: `0x10000` bytes (`PC080SN_RAM_SIZE`).
- Standard layout BG region: `0x0000-0x3FFF` bytes inside PC080SN RAM.
- Standard layout FG region: `0x8000-0xBFFF` bytes inside PC080SN RAM.
- RAM organization is 16-bit words (`u16`), accessed through `word_r/word_w` offsets.

## 2C/2D. Tile Index Fetch and Screen Position Mapping (Verbatim Excerpts + Formulae)

```cpp
template <unsigned N>
TILE_GET_INFO_MEMBER(pc080sn_device::get_tile_info)
{
	u16 code, attr;

	if (!m_dblwidth)
	{
		code = m_bg_ram[N][2 * tile_index + 1] & 0x3fff;
		attr = m_bg_ram[N][2 * tile_index];
	}
	else
	{
		code = m_bg_ram[N][tile_index + 0x2000] & 0x3fff;
		attr = m_bg_ram[N][tile_index];
	}

	tileinfo.set(0,
			code,
			(attr & 0x1ff),
			TILE_FLIPYX((attr & 0xc000) >> 14));
}
```

For standard (non-dblwidth) mode:
- Tilemap scan: `TILEMAP_SCAN_ROWS`, dimensions `64x64`.
- `tile_index = row * 64 + col`.
- `attr_word = m_bg_ram[N][2 * tile_index]`
- `code_word = m_bg_ram[N][2 * tile_index + 1]`
- `tile_number = code_word & 0x3FFF`
- `palette_field = attr_word & 0x01FF`
- `flip_bits = (attr_word & 0xC000) >> 14` (passed to `TILE_FLIPYX`)

Address formula (Rastan BG layer, N=0):
- `base = 0xC00000`
- `attr_addr = base + 4 * (row*64 + col)`
- `code_addr = base + 4 * (row*64 + col) + 2`

## 2E. Strip Write Mechanism

```cpp
void pc080sn_device::word_w(offs_t offset, u16 data, u16 mem_mask)
{
	COMBINE_DATA(&m_ram[offset]);

	if (!m_dblwidth)
	{
		if (offset < 0x2000)
			m_tilemap[0]->mark_tile_dirty(offset / 2);
		else if (offset >= 0x4000 && offset < 0x6000)
			m_tilemap[1]->mark_tile_dirty((offset & 0x1fff) / 2);
	}
	else
	{
		if (offset < 0x4000)
			m_tilemap[0]->mark_tile_dirty((offset & 0x1fff));
		else if (offset >= 0x4000 && offset < 0x8000)
			m_tilemap[1]->mark_tile_dirty((offset & 0x1fff));
	}
}
```

- No dedicated PC080SN strip-write handler is present in `pc080sn.cpp`; writes are generic `word_w(offset, data, mem_mask)` writes into RAM and tile dirty marking.

## 2F. Non-Obvious Transformations

- No XOR/interleave address transform is present for standard mode in `get_tile_info`.
- Double-width mode uses a different split layout (`tile_index + 0x2000` for code), but Rastan is configured as standard 64x64 scan-rows in this extraction.
