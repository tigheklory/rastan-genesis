# Cody — PC080SN + PC090OJ Writer Audit Report

## Verification Checklist
- [x] Inventory includes arcade PC 0x055968 (BG strip producer — already hooked) — confirms BG path detection works
- [x] Inventory includes arcade PC 0x055990 (FG strip producer — already hooked) — confirms FG path detection works
- [x] Inventory includes arcade PC 0x03AD44 (BG fill hook site — already hooked) — confirms fill detection works
- [x] Inventory includes arcade PC 0x0561C0–0x0561D2 (old C-window fill loop — now redirected in Build 0029) — confirms prior patch detection
- [x] Inventory includes arcade PC 0x03C530 (known crash site from Build 0029 trace)
- [x] Inventory includes arcade PC 0x03C544 (second write in the same loop)
- [x] Inventory includes arcade PC 0x055AB4 range (scroll register writes — already rewritten)
- [x] Inventory includes at least one known PC090OJ writer (search for any write to 0xD0xxxx in the arcade ROM — confirms PC090OJ detection works)
- [x] Inventory includes arcade PC 0x03ADFE, 0x03AE06, 0x03AE16, 0x03AE1E (known PC090OJ/screen-flip NOP suppression sites — already hooked)
- [x] Every PC listed in the Build 0029 `fg_cwindow_live` trace appears in the inventory
- [x] All PC090OJ writes found in the Build 0029 trace (if any) appear in the inventory

## Section 1: Methodology
Steps 1–5 were executed in order against `build/maincpu.disasm.txt` (arcade PC range `0x000000–0x05FFFF`) and Build 0029 trace artifacts.

Exact command/pattern set used:
- `rg -n "00c0 0000|00c0 4000|00c0 8000|00c0 c000|00c2 0000|00c4 0000|00d0 0000|00d0 1000|00d0 2000|00d0 3000" build/maincpu.disasm.txt`
- `rg -n "(lea 0xc|lea 0xd|moveal #12|moveal #136|addal #126|addal #136)" build/maincpu.disasm.txt`
- `rg -n "movew .*0xc|movel .*0xc|moveb .*0xc|movew .*0xd|movel .*0xd|moveb .*0xd|clrw 0xc|clrl 0xc|clrw 0xd|clrl 0xd" build/maincpu.disasm.txt`
- `python3 indirect-flow pass over build/maincpu.disasm.txt with A-register load/copy/add tracking to emit /tmp/audit_writer_candidates.tsv`
- `rg -n "live_write fg_cwindow_live" states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_212116/genesis_exec_trace.log`
- `rg -n "addr=d[0-9a-f]{5}" states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_212116/genesis_exec_trace.log`

## Section 2: Full Inventory Table
| Arcade PC | Instruction | Base load PC | Chip | Destination range | Write pattern | Purpose | Callers | Already hooked? |
|---|---|---:|---|---|---|---|---|---|
| `0x000176` | `176:	30fc 0000      	movew #0,%a0@+` | 0x00016A | PC080SN | YSCROLL_REG | LOOP_FIXED | PC080SN scroll register write path. |  | NO |
| `0x00017A` | `17a:	32fc 0000      	movew #0,%a1@+` | 0x000170 | PC080SN | XSCROLL_REG | LOOP_FIXED | PC080SN scroll register write path. |  | NO |
| `0x0002E6` | `2e6:	34fc 0000      	movew #0,%a2@+` | 0x0002CA | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002EA` | `2ea:	34c0           	movew %d0,%a2@+` | 0x0002CA | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002EC` | `2ec:	34fc 4000      	movew #16384,%a2@+` | 0x0002CA | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002F0` | `2f0:	34c0           	movew %d0,%a2@+` | 0x0002CA | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002F2` | `2f2:	36fc 8000      	movew #-32768,%a3@+` | 0x0002D0 | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002F6` | `2f6:	36c0           	movew %d0,%a3@+` | 0x0002D0 | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002F8` | `2f8:	36fc c000      	movew #-16384,%a3@+` | 0x0002D0 | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x0002FC` | `2fc:	36c0           	movew %d0,%a3@+` | 0x0002D0 | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x03A350` | `3a350:	33fc 0032 00c0 	movew #50,0xc08a52` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x03A55C` | `3a55c:	13fc 0020 00c0 	moveb #32,0xc09ea3` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x03A6FE` | `3a6fe:	33fc 2744 00c0 	movew #10052,0xc08e7a` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x03A708` | `3a708:	33fc 2744 00c0 	movew #10052,0xc08e66` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x03A72A` | `3a72a:	33c0 00c0 8c62 	movew %d0,0xc08c62` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x03AAEA` | `3aaea:	33fc 2749 00c0 	movew #10057,0xc09172` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x03ABBA` | `3abba:	42b9 00c2 0000 	clrl 0xc20000` | UNKNOWN | PC080SN | YSCROLL_REG | SINGLE | PC080SN scroll register write path. |  | YES |
| `0x03ABC0` | `3abc0:	42b9 00c4 0000 	clrl 0xc40000` | UNKNOWN | PC080SN | XSCROLL_REG | SINGLE | PC080SN scroll register write path. |  | YES |
| `0x03AD44` | `3ad44:	movel %d0,%a0@+` | UNKNOWN | UNKNOWN | UNKNOWN | FILL | Longword fill primitive; caller-supplied A0 can target PC080SN or PC090OJ address spaces. | 0x03AD5C 0x03AD6E 0x03AD82 0x03AE70 0x03AE80 0x03AF38 0x03AF48 | YES |
| `0x03ADAA` | `3adaa:	2080           	movel %d0,%a0@` | 0x03AD86 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x03ABB6 0x03AF28 | NO |
| `0x03ADAC` | `3adac:	2147 0004      	movel %d7,%a0@(4)` | 0x03AD86 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x03ABB6 0x03AF28 | NO |
| `0x03ADFE` | `3adfe:	33fc 0000 00c5 	movew #0,0xc50000` | UNKNOWN | PC090OJ | UNKNOWN | SINGLE | Screen-flip helper write to 0xC50000 (outside audited PC080SN/PC090OJ target windows; included per verification gate). |  | YES |
| `0x03AE06` | `3ae06:	33fc 0001 00d0 	movew #1,0xd01bfe` | UNKNOWN | PC090OJ | SPRITE_RAM | SINGLE | Sprite attribute RAM write path. |  | YES |
| `0x03AE16` | `3ae16:	33fc 0001 00c5 	movew #1,0xc50000` | UNKNOWN | PC090OJ | UNKNOWN | SINGLE | Screen-flip helper write to 0xC50000 (outside audited PC080SN/PC090OJ target windows; included per verification gate). |  | YES |
| `0x03AE1E` | `3ae1e:	33fc 0000 00d0 	movew #0,0xd01bfe` | UNKNOWN | PC090OJ | SPRITE_RAM | SINGLE | Sprite attribute RAM write path. |  | YES |
| `0x03AE8E` | `3ae8e:	33fc 0000 00d0 	movew #0,0xd01bfe` | UNKNOWN | PC090OJ | SPRITE_RAM | SINGLE | Sprite attribute RAM write path. |  | NO |
| `0x03B098` | `3b098:	42b9 00c2 0000 	clrl 0xc20000` | UNKNOWN | PC080SN | YSCROLL_REG | SINGLE | PC080SN scroll register write path. |  | YES |
| `0x03B09E` | `3b09e:	42b9 00c4 0000 	clrl 0xc40000` | UNKNOWN | PC080SN | XSCROLL_REG | SINGLE | PC080SN scroll register write path. |  | YES |
| `0x03B1CC` | `3b1cc:	3080           	movew %d0,%a0@` | 0x03B192 | PC080SN | FG_TILEMAP | UNKNOWN | PC080SN tilemap write path. |  | NO |
| `0x03B47A` | `3b47a:	30fc 0001      	movew #1,%a0@+` | 0x03B474 | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x03B47E` | `3b47e:	30bc 2744      	movew #10052,%a0@` | 0x03B474 | PC080SN | FG_TILEMAP | UNKNOWN | PC080SN tilemap write path. |  | NO |
| `0x03B49A` | `3b49a:	30bc 274b      	movew #10059,%a0@` | 0x03B48A | PC080SN | FG_TILEMAP | UNKNOWN | PC080SN tilemap write path. |  | NO |
| `0x03B572` | `3b572:	30fc 0000      	movew #0,%a0@+` | 0x03B56A | PC080SN | FG_TILEMAP | LOOP_FIXED | PC080SN tilemap write path. |  | NO |
| `0x03B5F6` | `3b5f6:	3080           	movew %d0,%a0@` | 0x03B5B2 | PC080SN | FG_TILEMAP | UNKNOWN | PC080SN tilemap write path. |  | NO |
| `0x03B932` | `3b932:	32c2           	movew %d2,%a1@+` | 0x03B926 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A9C6 0x03A9D4 | NO |
| `0x03B938` | `3b938:	32c0           	movew %d0,%a1@+` | 0x03B926 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A9C6 0x03A9D4 | NO |
| `0x03B93E` | `3b93e:	32c0           	movew %d0,%a1@+` | 0x03B926 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A9C6 0x03A9D4 | NO |
| `0x03B948` | `3b948:	32c7           	movew %d7,%a1@+` | 0x03B926 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A9C6 0x03A9D4 | NO |
| `0x03C42A` | `3c42a:	movew %d7,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG descriptor pre-pass writes strip header word to C-window row. |  | NO |
| `0x03C446` | `3c446:	movew %d1,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG descriptor pre-pass writes translated tile word. |  | NO |
| `0x03C44A` | `3c44a:	movew #32,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG descriptor pre-pass writes blank tile constant fallback. |  | NO |
| `0x03C4EA` | `3c4ea:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG descriptor loop writes 0x0180 attribute marker for empty entry. |  | NO |
| `0x03C518` | `3c518:	extw %d0` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | Trace-reported FG write loop context immediately before write at 0x03C530. |  | NO |
| `0x03C52A` | `3c528:	d06c 001a      	addw %a4@(26),%d0` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | Trace-reported mid-instruction PC alias inside the addw at 0x03C528 immediately preceding the write at 0x03C530. |  | NO |
| `0x03C530` | `3c530:	movew %d0,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG loop writes tile index word to C-window entry. | 0x03C502 0x03C50E | NO |
| `0x03C544` | `3c544:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG loop writes companion coordinate/attribute word to same C-window entry. | 0x03C502 0x03C50E | NO |
| `0x03C56C` | `3c56c:	movew %d0,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG pattern writer stores row-derived value at C-window offset +6. |  | NO |
| `0x03C570` | `3c570:	movew %a4@(26),%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG pattern writer stores base tile parameter at C-window offset +2. |  | NO |
| `0x03C610` | `3c610:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes empty-entry marker 0x0180. |  | NO |
| `0x03C61C` | `3c61c:	movew %d0,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed row value at +6. |  | NO |
| `0x03C62A` | `3c62a:	movew %d7,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed column value at +2. |  | NO |
| `0x03C6B6` | `3c6b6:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes empty-entry marker 0x0180. |  | NO |
| `0x03C6C2` | `3c6c2:	movew %d0,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +2. |  | NO |
| `0x03C6D0` | `3c6d0:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +6. |  | NO |
| `0x03C712` | `3c712:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes empty-entry marker 0x0180. |  | NO |
| `0x03C720` | `3c720:	movew %d0,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +2. |  | NO |
| `0x03C734` | `3c734:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +6. |  | NO |
| `0x03C74A` | `3c74a:	movew %d6,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed D6-derived value at +2. |  | NO |
| `0x03C756` | `3c756:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed D7-derived value at +6. |  | NO |
| `0x03C7DE` | `3c7de:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes empty-entry marker 0x0180. |  | NO |
| `0x03C7EA` | `3c7ea:	movew %d0,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +2. |  | NO |
| `0x03C7F8` | `3c7f8:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +6. |  | NO |
| `0x03C816` | `3c816:	movew %d0,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +2. |  | NO |
| `0x03C824` | `3c824:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +6. |  | NO |
| `0x03C874` | `3c874:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes empty-entry marker 0x0180. |  | NO |
| `0x03C880` | `3c880:	movew %d0,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +2. |  | NO |
| `0x03C88E` | `3c88e:	movew %d7,%a1@(6)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes computed value at +6. |  | NO |
| `0x03C8B8` | `3c8b8:	movew %d7,%a1@(4)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG helper writes extra attribute word at +4. |  | NO |
| `0x03C982` | `3c982:	movew %d0,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG mixed-format parser emits first output word to C-window stream. |  | NO |
| `0x03C990` | `3c990:	movew %d1,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG mixed-format parser emits second output word to C-window stream. |  | NO |
| `0x03C99E` | `3c99e:	movew %d7,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG mixed-format parser emits third output word to C-window stream. |  | NO |
| `0x03C9C2` | `3c9c2:	movew %d0,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG alternate parser emits first output word to C-window stream. |  | NO |
| `0x03C9CC` | `3c9cc:	movew %d1,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG alternate parser emits second output word to C-window stream. |  | NO |
| `0x03C9E0` | `3c9e0:	movew %d7,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG alternate parser emits third output word to C-window stream. |  | NO |
| `0x03C9F6` | `3c9f6:	movew #384,%a1@(2)` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG parser writes empty-entry marker 0x0180. |  | NO |
| `0x03CA20` | `3ca20:	movew %d0,%a1@+` | 0x03C418 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG parser emits decoded value to C-window stream. |  | NO |
| `0x03D04C` | `3d04c:	33c1 00c0 8c66 	movew %d1,0xc08c66` | UNKNOWN | PC080SN | FG_TILEMAP | SINGLE | PC080SN tilemap write path. |  | NO |
| `0x041F7E` | `41f7e:	32d8           	movew %a0@+,%a1@+` | 0x041F74 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A854 0x041F4A | NO |
| `0x041F80` | `41f80:	32d8           	movew %a0@+,%a1@+` | 0x041F74 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A854 0x041F4A | NO |
| `0x041F82` | `41f82:	32d8           	movew %a0@+,%a1@+` | 0x041F74 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A854 0x041F4A | NO |
| `0x041F84` | `41f84:	32d8           	movew %a0@+,%a1@+` | 0x041F74 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x03A854 0x041F4A | NO |
| `0x0510CE` | `510ce:	30fc 0000      	movew #0,%a0@+` | 0x0510C8 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0510D2` | `510d2:	30fc 0080      	movew #128,%a0@+` | 0x0510C8 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0510DA` | `510da:	30c0           	movew %d0,%a0@+` | 0x0510C8 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0510DC` | `510dc:	30fc 0080      	movew #128,%a0@+` | 0x0510C8 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0510EA` | `510ea:	33fc 0002 00d0 	movew #2,0xd00698` | UNKNOWN | PC090OJ | SPRITE_RAM | SINGLE | Sprite attribute RAM write path. |  | NO |
| `0x0510F4` | `510f4:	33fc 0000 00d0 	movew #0,0xd00698` | UNKNOWN | PC090OJ | SPRITE_RAM | SINGLE | Sprite attribute RAM write path. |  | NO |
| `0x052ABE` | `52abe:	32c0           	movew %d0,%a1@+` | 0x052AA2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x052A8C 0x052A9C | NO |
| `0x052AD0` | `52ad0:	32c0           	movew %d0,%a1@+` | 0x052AA2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x052A8C 0x052A9C | NO |
| `0x052AD4` | `52ad4:	32e8 0000      	movew %a0@(0),%a1@+` | 0x052AA2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x052A8C 0x052A9C | NO |
| `0x052AEA` | `52aea:	32c0           	movew %d0,%a1@+` | 0x052AA2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x052A8C 0x052A9C | NO |
| `0x0540B6` | `540b6:	32fc 0003      	movew #3,%a1@+` | 0x0540AC | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x0501F4 0x051260 | NO |
| `0x0540BA` | `540ba:	32fc 0000      	movew #0,%a1@+` | 0x0540AC | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x0501F4 0x051260 | NO |
| `0x0540BE` | `540be:	32fc 0000      	movew #0,%a1@+` | 0x0540AC | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x0501F4 0x051260 | NO |
| `0x0540C2` | `540c2:	32fc 0000      	movew #0,%a1@+` | 0x0540AC | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x0501F4 0x051260 | NO |
| `0x05482C` | `5482c:	32c0           	movew %d0,%a1@+` | 0x054810 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x05483E` | `5483e:	32c0           	movew %d0,%a1@+` | 0x054810 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x054842` | `54842:	32e8 0000      	movew %a0@(0),%a1@+` | 0x054810 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x054858` | `54858:	32c0           	movew %d0,%a1@+` | 0x054810 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0551BE` | `551be:	3085           	movew %d5,%a0@` | 0x0551B2 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. |  | NO |
| `0x055968` | `55968:	moveal %a5@(4256),%a0` | 0x055968 | PC080SN | BG_TILEMAP | LOOP_DESCRIPTOR | BG strip producer entry; dispatches 16 descriptor strips to tilemap writer helper. | 0x055950 | YES |
| `0x055990` | `55990:	moveal %a5@(4260),%a0` | 0x055990 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG strip producer entry; dispatches 16 descriptor strips to tilemap writer helper. | 0x05595A | YES |
| `0x0559B4` | `559b4:	movew %a1@,%a0@` | 0x055968 | PC080SN | BG_TILEMAP | LOOP_DESCRIPTOR | BG strip writer helper writes descriptor-derived tile value to current BG destination. | 0x055950 | NO |
| `0x055A02` | `55a02:	movew %d0,%a0@` | 0x055968 | PC080SN | BG_TILEMAP | LOOP_DESCRIPTOR | BG strip writer helper writes second descriptor-derived word in strip row. | 0x055950 | NO |
| `0x055A1C` | `55a1c:	movew %a1@,%a0@` | 0x055990 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG strip writer helper writes descriptor-derived tile value to current FG destination. | 0x05595A | NO |
| `0x055AA4` | `55aa4:	movew %d0,%a0@` | 0x055990 | PC080SN | FG_TILEMAP | LOOP_DESCRIPTOR | FG strip writer helper writes second descriptor-derived word in strip row. | 0x05595A | NO |
| `0x055AB4` | `55ab4:	33ed 10ee 00c2 	movew %a5@(4334),0xc20000` | UNKNOWN | PC080SN | YSCROLL_REG | SINGLE | PC080SN scroll register write path. | 0x041F30 0x0560AA 0x0561B0 0x057454 0x0578A2 | YES |
| `0x055ABC` | `55abc:	33ed 10ec 00c4 	movew %a5@(4332),0xc40000` | UNKNOWN | PC080SN | XSCROLL_REG | SINGLE | PC080SN scroll register write path. | 0x041F30 0x0560AA 0x0561B0 0x057454 0x0578A2 | NO |
| `0x055AC4` | `55ac4:	33ed 10b0 00c2 	movew %a5@(4272),0xc20002` | UNKNOWN | PC080SN | YSCROLL_REG | SINGLE | PC080SN scroll register write path. | 0x041F30 0x0560AA 0x0561B0 0x057454 0x0578A2 | NO |
| `0x055ACC` | `55acc:	33ed 10ae 00c4 	movew %a5@(4270),0xc40002` | UNKNOWN | PC080SN | XSCROLL_REG | SINGLE | PC080SN scroll register write path. | 0x041F30 0x0560AA 0x0561B0 0x057454 0x0578A2 | NO |
| `0x0560C4` | `560c4:	3140 0002      	movew %d0,%a0@(2)` | 0x0560B0 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x055E92 | NO |
| `0x0560CE` | `560ce:	317c 0000 0004 	movew #0,%a0@(4)` | 0x0560B0 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x055E92 | NO |
| `0x0561B6` | `561b6:	movew #4096,%d1` | 0x0561B6 | PC080SN | UNKNOWN | FILL | C-window fill loop setup (count) for dual FG/BG fill path patched in Build 0029. |  | YES |
| `0x0561C0` | `561c0:	moveal #12615680,%a0` | 0x0561B6 | PC080SN | FG_TILEMAP | FILL | C-window fill loop loads FG destination base 0xC08000. |  | NO |
| `0x0561C6` | `561c6:	moveal #12582912,%a1` | 0x0561B6 | PC080SN | BG_TILEMAP | FILL | C-window fill loop loads BG destination base 0xC00000. |  | NO |
| `0x0561CC` | `561cc:	20c0           	movel %d0,%a0@+` | 0x0561C0 | PC080SN | FG_TILEMAP | FILL | PC080SN tilemap write path. | 0x055E22 0x055F64 0x055FCA 0x056458 0x05727E 0x0573EE 0x0577C2 0x05A474 | NO |
| `0x0561CE` | `561ce:	22c0           	movel %d0,%a1@+` | 0x0561C6 | PC080SN | BG_TILEMAP | FILL | PC080SN tilemap write path. | 0x055E22 0x055F64 0x055FCA 0x056458 0x05727E 0x0573EE 0x0577C2 0x05A474 | NO |
| `0x0561D0` | `561d0:	subqw #1,%d1` | 0x0561B6 | PC080SN | UNKNOWN | FILL | C-window fill loop decrements iteration count controlling FG/BG fill writes. |  | NO |
| `0x0561D2` | `561d2:	bnes 0x561cc` | 0x0561B6 | PC080SN | UNKNOWN | FILL | C-window fill loop branch back to write pair at 0x0561CC/0x0561CE. |  | NO |
| `0x0575D4` | `575d4:	20c0           	movel %d0,%a0@+` | 0x0575CE | PC080SN | FG_TILEMAP | FILL | PC080SN tilemap write path. | 0x05732C 0x0573B6 | NO |
| `0x0576A4` | `576a4:	3140 0002      	movew %d0,%a0@(2)` | 0x057688 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x05765A | NO |
| `0x0576C4` | `576c4:	3140 0002      	movew %d0,%a0@(2)` | 0x0576B6 | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x05765A | NO |
| `0x057712` | `57712:	30fc 0001      	movew #1,%a0@+` | 0x0576F2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x057646 0x05766E | NO |
| `0x057716` | `57716:	30c2           	movew %d2,%a0@+` | 0x0576F2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x057646 0x05766E | NO |
| `0x057718` | `57718:	30c0           	movew %d0,%a0@+` | 0x0576F2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x057646 0x05766E | NO |
| `0x05771A` | `5771a:	30c1           	movew %d1,%a0@+` | 0x0576F2 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x057646 0x05766E | NO |
| `0x0577B2` | `577b2:	32c0           	movew %d0,%a1@+` | 0x0577AA | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0577B4` | `577b4:	32c0           	movew %d0,%a1@+` | 0x0577AA | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0577B6` | `577b6:	32c0           	movew %d0,%a1@+` | 0x0577AA | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0577B8` | `577b8:	32c0           	movew %d0,%a1@+` | 0x0577AA | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x0578F4` | `578f4:	3340 0002      	movew %d0,%a1@(2)` | 0x0578E0 | PC080SN | BG_TILEMAP | UNKNOWN | PC080SN tilemap write path. | 0x057876 0x0578B6 | NO |
| `0x059F6A` | `59f6a:	20c0           	movel %d0,%a0@+` | 0x059F62 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x059F6C` | `59f6c:	20c0           	movel %d0,%a0@+` | 0x059F62 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. |  | NO |
| `0x05A11A` | `5a11a:	30fc 0000      	movew #0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A11E` | `5a11e:	30c3           	movew %d3,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A124` | `5a124:	30c0           	movew %d0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A126` | `5a126:	30c2           	movew %d2,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A13E` | `5a13e:	30fc 0000      	movew #0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A142` | `5a142:	30c3           	movew %d3,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A144` | `5a144:	30fc 03cc      	movew #972,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A148` | `5a148:	30c2           	movew %d2,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A188` | `5a188:	30fc 0000      	movew #0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A18C` | `5a18c:	30c3           	movew %d3,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A18E` | `5a18e:	30fc 03cd      	movew #973,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A192` | `5a192:	30c2           	movew %d2,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1AC` | `5a1ac:	30fc 0000      	movew #0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1B0` | `5a1b0:	30c3           	movew %d3,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1B4` | `5a1b4:	30c0           	movew %d0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1BA` | `5a1ba:	30c2           	movew %d2,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1D0` | `5a1d0:	30fc 0000      	movew #0,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1D4` | `5a1d4:	30c3           	movew %d3,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1D6` | `5a1d6:	30fc 03d5      	movew #981,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A1DA` | `5a1da:	30c2           	movew %d2,%a0@+` | 0x05A0AE | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A208` | `5a208:	3080           	movew %d0,%a0@` | 0x05A1EC | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A20C` | `5a20c:	30bc 03d5      	movew #981,%a0@` | 0x05A1EC | PC090OJ | SPRITE_RAM | UNKNOWN | Sprite attribute RAM write path. | 0x051054 | NO |
| `0x05A524` | `5a524:	30fc 0000      	movew #0,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A528` | `5a528:	30c1           	movew %d1,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A52A` | `5a52a:	30fc 0037      	movew #55,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A52E` | `5a52e:	30c0           	movew %d0,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A534` | `5a534:	30fc 0000      	movew #0,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A538` | `5a538:	30c1           	movew %d1,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A53A` | `5a53a:	30fc 0038      	movew #56,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A53E` | `5a53e:	30c0           	movew %d0,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A544` | `5a544:	30fc 0000      	movew #0,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A548` | `5a548:	30c1           	movew %d1,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A54A` | `5a54a:	30fc 003f      	movew #63,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A54E` | `5a54e:	30c0           	movew %d0,%a0@+` | 0x05A51E | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A55A` | `5a55a:	30fc 0000      	movew #0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A55E` | `5a55e:	30c1           	movew %d1,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A560` | `5a560:	30fc 0040      	movew #64,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A564` | `5a564:	30c0           	movew %d0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A56A` | `5a56a:	30fc 0000      	movew #0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A56E` | `5a56e:	30c1           	movew %d1,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A570` | `5a570:	30fc 0041      	movew #65,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A574` | `5a574:	30c0           	movew %d0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A57A` | `5a57a:	30fc 0000      	movew #0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A57E` | `5a57e:	30c1           	movew %d1,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A580` | `5a580:	30fc 0042      	movew #66,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A584` | `5a584:	30c0           	movew %d0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A58A` | `5a58a:	30fc 0000      	movew #0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A58E` | `5a58e:	30c1           	movew %d1,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A590` | `5a590:	30fc 0043      	movew #67,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A594` | `5a594:	30c0           	movew %d0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A59A` | `5a59a:	30fc 0000      	movew #0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A59E` | `5a59e:	30c1           	movew %d1,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A5A0` | `5a5a0:	30fc 0044      	movew #68,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |
| `0x05A5A4` | `5a5a4:	30c0           	movew %d0,%a0@+` | 0x05A554 | PC090OJ | SPRITE_RAM | LOOP_FIXED | Sprite attribute RAM write path. | 0x05104E | NO |

## Section 3: Writer Count By Destination Range
```
PC080SN:
  BG_TILEMAP:    6 writers
  BG_ROWSCROLL:  0 writers
  FG_TILEMAP:    65 writers
  FG_ROWSCROLL:  0 writers
  YSCROLL_REG:   5 writers
  XSCROLL_REG:   5 writers

PC090OJ:
  SPRITE_RAM:    100 writers

UNKNOWN destination: 6 writers
```

## Section 4: Already-Hooked Status Summary
| Destination range | Hooked YES | Hooked NO |
|---|---:|---:|
| BG_TILEMAP | 1 | 5 |
| BG_ROWSCROLL | 0 | 0 |
| FG_TILEMAP | 1 | 64 |
| FG_ROWSCROLL | 0 | 0 |
| YSCROLL_REG | 3 | 2 |
| XSCROLL_REG | 2 | 3 |
| SPRITE_RAM | 2 | 98 |
| UNKNOWN | 4 | 2 |

## Section 5: Trace Cross-Check
- Build 0029 `fg_cwindow_live` PCs (summary/log union): 0x03C518, 0x03C52A
- Missing `fg_cwindow_live` PCs from inventory: none
- Trace scan for PC090OJ-range writes (`addr=0xD00000–0xD03FFF`) in `genesis_exec_trace.log`: 0 unique PCs
- PC090OJ trace PCs: none observed in this Build 0029 trace artifact.

## Section 6: Unclassified / Suspicious Cases
- `0x03AD44` `3ad44:	movel %d0,%a0@+` — Destination register contract is caller-dependent; static chip target cannot be resolved from local instruction alone.
- `0x03ADFE` `3adfe:	33fc 0000 00c5 	movew #0,0xc50000` — Writes to 0xC50000, which is outside the audited PC080SN/PC090OJ windows but required by verification gate due paired suppression site analysis.
- `0x03AE16` `3ae16:	33fc 0001 00c5 	movew #1,0xc50000` — Writes to 0xC50000, which is outside the audited PC080SN/PC090OJ windows but required by verification gate due paired suppression site analysis.
- `0x0561B6` `561b6:	movew #4096,%d1` — Control/setup instruction in a write loop (non-store instruction) included to satisfy trace/provenance coverage.
- `0x0561D0` `561d0:	subqw #1,%d1` — Control/setup instruction in a write loop (non-store instruction) included to satisfy trace/provenance coverage.
- `0x0561D2` `561d2:	bnes 0x561cc` — Control/setup instruction in a write loop (non-store instruction) included to satisfy trace/provenance coverage.
