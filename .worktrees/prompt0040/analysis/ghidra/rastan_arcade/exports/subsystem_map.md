# Rastan Arcade Subsystem Map

| subsystem | anchor addresses | notes |
|---|---|---|
| startup/reset | `0x03A000,0x03AE86,0x039F80` | reset vector/startup body/warm restart watchdog gate |
| VBlank/lifecycle | `0x03A008` | arcade Level-5 VBlank handler and state dispatch |
| title/attract text | `0x03ACAE,0x03BD48,0x0565A6` | known title glyph producer, glyph renderer, shared PC080SN text writer |
| PC080SN tilemaps | `HW 0xC00000-0xC0FFFF` | BG/FG tilemap C-window references in hw_refs.tsv |
| PC080SN scroll | `HW 0xC20000/0xC40000` | Y/X scroll hardware references in hw_refs.tsv |
| PC090OJ sprites | `0x03B930,0x03B802,HW 0xD00000-0xD03FFF` | sprite producers and object RAM references |
| palette | `HW 0x200000-0x200FFF,0x380000` | CLCS palette RAM and sprite palette-control refs |
| input/sound/watchdog | `HW 0x390000,0x3E0000,0x3C0000` | input ports, PC060HA sound comm, watchdog |

Detailed static references are in `hw_refs.tsv`, `function_inventory.tsv`, and `call_graph_edges.tsv`.
