# Rastan Arcade Main CPU Memory Map

Source: `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`, `rastan_state::main_map`.

| address range | label | access | note |
|---|---|---|---|
| `arcade_pc 0x000000-0x05FFFF` | maincpu ROM | R/X | World Rev 1 MAME `maincpu`, 6x64 KiB LOAD16_BYTE interleave |
| `arcade_WRAM 0x10C000-0x10FFFF` | work RAM | R/W | A5 base commonly `0x10C000` |
| `arcade_HW_ADDRESS 0x200000-0x200FFF` | CLCS palette RAM | R/W | xBGR-555 palette RAM, 2048 words |
| `arcade_HW_ADDRESS 0x350008-0x350009` | unknown/nop write | W | MAME nopw |
| `arcade_HW_ADDRESS 0x380000-0x380001` | sprite control | W | sprite palette bank / coin / lockout |
| `arcade_HW_ADDRESS 0x390000-0x39000B` | inputs / DIP | R | P1/P2/SPECIAL/SYSTEM/DSWA/DSWB |
| `arcade_HW_ADDRESS 0x3C0000-0x3C0001` | watchdog | W | watchdog reset |
| `arcade_HW_ADDRESS 0x3E0000-0x3E0003` | PC060HA sound comm | R/W | master port / comm |
| `arcade_HW_ADDRESS 0xC00000-0xC0FFFF` | PC080SN tilemap | R/W | BG/FG tilemap C-window |
| `arcade_HW_ADDRESS 0xC20000-0xC20003` | PC080SN Y scroll | W | yscroll_word_w |
| `arcade_HW_ADDRESS 0xC40000-0xC40003` | PC080SN X scroll | W | xscroll_word_w |
| `arcade_HW_ADDRESS 0xC50000-0xC50003` | PC080SN control | W | ctrl_word_w |
| `arcade_HW_ADDRESS 0xD00000-0xD03FFF` | PC090OJ sprite RAM | R/W | object/sprite RAM |

## Ghidra Blocks

| block | start | end | R | W | X | volatile |
|---|---:|---:|---|---|---|---|
| `ram` | `00000000` | `0005ffff` | true | true | true | false |
| `arcade_WRAM` | `0010c000` | `0010ffff` | true | true | false | false |
| `arcade_palette_RAM` | `00200000` | `00200fff` | true | true | false | true |
| `arcade_io` | `00350008` | `00350009` | false | true | false | true |
| `arcade_sprite_ctrl` | `00380000` | `00380001` | false | true | false | true |
| `arcade_inputs` | `00390000` | `0039000b` | true | false | false | true |
| `arcade_watchdog` | `003c0000` | `003c0001` | false | true | false | true |
| `arcade_sound_comm` | `003e0000` | `003e0003` | true | true | false | true |
| `PC080SN_tilemap` | `00c00000` | `00c0ffff` | true | true | false | true |
| `PC080SN_yscroll` | `00c20000` | `00c20003` | false | true | false | true |
| `PC080SN_xscroll` | `00c40000` | `00c40003` | false | true | false | true |
| `PC080SN_ctrl` | `00c50000` | `00c50003` | false | true | false | true |
| `PC090OJ_sprite_RAM` | `00d00000` | `00d03fff` | true | true | false | true |
