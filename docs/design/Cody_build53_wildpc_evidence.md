# Cody Build 53 Wild PC Evidence (Read-Only)

## Scope
- Task type: read-only evidence extraction.
- Inputs used: repo artifacts only.
- No source/spec/tool modifications were made for this evidence collection.

## §1.1 Artifact locations
- Build 53 ROM (numbered): `dist/rastan-direct/rastan_direct_video_test_build_0053.bin`
- Build ROM (current output path): `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Address map: `build/rastan-direct/address_map.json`
- Patch manifest: `build/rastan-direct/rastan_direct_patch_manifest.json`
- Arcade disassembly: `build/maincpu.disasm.txt`
- Postpatch disassembly: `build/genesis_postpatch.disasm.txt`
- Linker symbol map: `apps/rastan-direct/out/symbol.txt`
- Exodus extraction context: `docs/design/Cody_exodus_frame_extraction_build_53_2.md`

Evidence:
- File existence/timestamps: `ls -l` capture over the files above (local command output).

## §1.2 runtime_genesis_pc 0x000711CE -> arcade_pc mapping (from artifact)
Address-map evidence:
- `build/rastan-direct/address_map.json:1916-1920`:
```json
{
  "genesis_start": "0x070000",
  "genesis_end_exclusive": "0x17C96C",
  "size_bytes": 1100140,
  "kind": "genesis_only",
  "tag": "wrapper"
}
```

Observed mapping result from address-map artifact:
- `runtime_genesis_pc 0x000711CE` is inside the `genesis_only` wrapper segment.
- No `arcade_start`/`arcade_end_exclusive` fields are present for this segment.
- Arcade mapping value from artifact for this runtime PC: `N/A (no arcade segment mapping entry)`.

Supporting metadata:
- `build/rastan-direct/address_map.json:16-20` (`wrapper_region`)
- `build/rastan-direct/address_map.json:1916-1920` (segment entry)

## §1.3 Disassembly dump around runtime_genesis_pc 0x000711CE
Requested target file (`build/maincpu.disasm.txt`) lookup:
- Search for `711ce` in `build/maincpu.disasm.txt`: no matches.
- Last disassembly address in `build/maincpu.disasm.txt`:
  - `build/maincpu.disasm.txt` final line content includes `5fffe` out-of-bounds notice.

Because §1.2 produced no artifact arcade mapping entry for `0x000711CE`, no `arcade_pc` key exists to anchor a `maincpu.disasm.txt` dump for this runtime PC.

Supplemental runtime disassembly window (postpatch ROM disassembly) for the requested ±128-byte window:
- Source: `build/genesis_postpatch.disasm.txt:124006-124082`
```text
71150: 6608            bnes 0x7115a
71152: 0884 0004       bclr #4,%d4
71156: 0884 0006       bclr #6,%d4
7115a: 0803 0006       btst #6,%d3
7115e: 6608            bnes 0x71168
71160: 0884 0005       bclr #5,%d4
71164: 0884 0006       bclr #6,%d4
71168: 13c4 00ff 60fe  moveb %d4,0xff60fe
7116e: 7aff            moveq #-1,%d5
71170: 0806 0005       btst #5,%d6
71174: 6604            bnes 0x7117a
71176: 0885 0003       bclr #3,%d5
7117a: 0807 0005       btst #5,%d7
7117e: 6604            bnes 0x71184
71180: 0885 0004       bclr #4,%d5
71184: 7000            moveq #0,%d0
71186: 0802 0006       btst #6,%d2
7118a: 6602            bnes 0x7118e
7118c: 7001            moveq #1,%d0
7118e: 4a39 00ff 6100  tstb 0xff6100
71194: 6610            bnes 0x711a6
71196: 4a00            tstb %d0
71198: 6704            beqs 0x7119e
7119a: 0885 0005       bclr #5,%d5
7119e: 13c0 00ff 6100  moveb %d0,0xff6100
711a4: 6006            bras 0x711ac
711a6: 13c0 00ff 6100  moveb %d0,0xff6100
711ac: 13c5 00ff 60ff  moveb %d5,0xff60ff
711b2: 4e75            rts
711b4: 3200            movew %d0,%d1
711b6: e449            lsrw #2,%d1
711b8: 7401            moveq #1,%d2
711ba: e3aa            lsll %d1,%d2
711bc: 2639 00ff 6744  movel 0xff6744,%d3
711c2: 8682            orl %d2,%d3
711c4: 23c3 00ff 6744  movel %d3,0xff6744
711ca: 4e75            rts
711cc: 3c00            movew %d0,%d6
711ce: ccfc 000c       muluw #12,%d6
711d2: 41f9 00ff 6384  lea 0xff6384,%a0
711d8: d1c6            addal %d6,%a0
711da: 3c00            movew %d0,%d6
711dc: e74e            lslw #3,%d6
711de: 43f9 00ff 6104  lea 0xff6104,%a1
711e4: d2c6            addaw %d6,%a1
711e6: 3c28 0008       movew %a0@(8),%d6
711ea: 3142 0002       movew %d2,%a0@(2)
711ee: 3144 0004       movew %d4,%a0@(4)
711f2: 3141 0006       movew %d1,%a0@(6)
711f6: 3143 0008       movew %d3,%a0@(8)
711fa: 3145 000a       movew %d5,%a0@(10)
711fe: 0c42 0180       cmpiw #384,%d2
71202: 6700 0098       beqw 0x7129c
71206: 4a43            tstw %d3
71208: 6700 0092       beqw 0x7129c
7120c: 3a01            movew %d1,%d5
7120e: 8a42            orw %d2,%d5
71210: 8a43            orw %d3,%d5
71212: 8a44            orw %d4,%d5
71214: 6700 0086       beqw 0x7129c
71218: 3a3c 8001       movew #-32767,%d5
7121c: 8a46            orw %d6,%d5
7121e: bc68 0008       cmpw %a0@(8),%d6
71222: 3c28 0008       movew %a0@(8),%d6
71226: bc43            cmpw %d3,%d6
71228: 6704            beqs 0x7122e
7122a: 0045 0004       oriw #4,%d5
7122e: 3085            movew %d5,%a0@
71230: 3a02            movew %d2,%d5
71232: 0245 01ff       andiw #511,%d5
71236: 0645 0080       addiw #128,%d5
7123a: 0245 01ff       andiw #511,%d5
7123e: 3285            movew %d5,%a1@
71240: 337c 0500 0002  movew #1280,%a1@(2)
71246: 3a3c 8000       movew #-32768,%d5
7124a: 3c01            movew %d1,%d6
7124c: 0246 000f       andiw #15,%d6
```

## §1.4 Exact instruction at runtime_genesis_pc 0x000711CE
Verbatim instruction:
- `build/genesis_postpatch.disasm.txt:124044`
- `711ce: ccfc 000c       muluw #12,%d6`

## §1.5 Address-map entry covering runtime_genesis_pc 0x000711CE
Full covering entry from address map:
- `build/rastan-direct/address_map.json:1916-1920`
```json
{
  "genesis_start": "0x070000",
  "genesis_end_exclusive": "0x17C96C",
  "size_bytes": 1100140,
  "kind": "genesis_only",
  "tag": "wrapper"
}
```

Patch metadata fields (`origin`, `original_bytes`, `replacement_bytes`, `note`) are not present in this covering entry.

## §1.6 Search for 0x008F831C / variants in repo artifacts
Search patterns used (case-insensitive):
- `0x008f831c`
- `0x8f831c`
- `008f831c`
- `8f831c`

Searched paths:
- `build/rastan-direct/*`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`
- `apps/rastan-direct/out/symbol.txt`
- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/*.s`
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md`

Occurrences found:
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md:140`
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md:141`
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md:142`
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md:143`
- `docs/design/Cody_exodus_frame_extraction_build_53_2.md:144`

No occurrences found in:
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`
- `apps/rastan-direct/out/symbol.txt`
- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/*.s`

## §1.7 Address-space classification for 0x008F831C
Observed range checks (Genesis address-space buckets requested in task):
- ROM range `[0x000000, 0x3FFFFF]`: `0x008F831C` is not in range.
- WRAM range `[0xFF0000, 0xFFFFFF]`: not in range.
- VDP I/O range `[0xC00000, 0xC0001F]`: not in range.
- Z80 range `[0xA00000, 0xA0FFFF]`: not in range.

Classification:
- `Other unmapped space` (under the requested bucket set).

## §1.8 Control-flow hazard instructions in the ±128-byte disassembly window
Window used:
- Runtime window from `0x711CE - 0x80` to `0x711CE + 0x80`
- Source lines: `build/genesis_postpatch.disasm.txt:124006-124082`

Observed matching instructions (requested classes):
- `build/genesis_postpatch.disasm.txt:124034` -> `711b2: 4e75            rts`
- `build/genesis_postpatch.disasm.txt:124042` -> `711ca: 4e75            rts`

Observed counts in this window:
- RTS: 2
- RTE: 0
- JMP: 0
- JSR: 0
- BSR: 0
- Stack-manipulation forms requested (`-(SP)`, `(SP)+`, `pea`, `link`, `unlk`): 0
- Indirect branches (`jmp/jsr (An)` or displacement forms): 0

## §1.9 Exodus register context (verbatim)
Source: `docs/design/Cody_exodus_frame_extraction_build_53_2.md:139-145`

Last good (Frame 108):
```text
Frame 108 (source 527, t=17.567s): A0=0x00FFF32C A1=0x00FF6B1C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x00000AA4 D1=0x00000000 D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00000000 D6=0x00000AA4 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711CE USP=0xFFFFFFFF SSP=0x00FEFFB0 S=1 T=0 IPM=7 SR=0x2700
```

Wild (Frames 109-113):
```text
Frame 109 (source 528, t=17.600s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x008F831C USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 110 (source 529, t=17.633s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x008F831C USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 111 (source 530, t=17.667s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x008F831C USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 112 (source 531, t=17.700s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x008F831C USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 113 (source 532, t=17.733s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x008F831C USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
```

Exception (Frame 114):
```text
Frame 114 (source 533, t=17.767s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
```

## §1.10 Helper symbol cross-check
Symbol addresses (from `apps/rastan-direct/out/symbol.txt`):
- `genesistan_hook_3ad44_dispatch` -> `0x00071434` (`symbol.txt:183`)
- `genesistan_hook_tilemap_bg_fill` -> `0x00070570` (`symbol.txt:163`)
- `vdp_commit_sprites` -> `0x00071834` (`symbol.txt:193`)
- `genesistan_pc090oj_dma_self_test` -> `0x000719F6` (`symbol.txt:194`)

Remap references (`specs/rastan_direct_remap.json`):
- `genesistan_hook_3ad44_dispatch` appears in replacement bytes:
  - `arcade_pc 0x03AD44` -> `replacement_bytes: 4EB9{symbol:genesistan_hook_3ad44_dispatch}4E75` (`specs/rastan_direct_remap.json:307-310`)
- `genesistan_hook_tilemap_bg_fill`:
  - present in `required_symbols` (`specs/rastan_direct_remap.json:83`)
  - no direct `{symbol:genesistan_hook_tilemap_bg_fill}` in any `replacement_bytes` field.
- `vdp_commit_sprites`:
  - present in `required_symbols` (`specs/rastan_direct_remap.json:121`)
  - no direct `{symbol:vdp_commit_sprites}` in any `replacement_bytes` field.
- `genesistan_pc090oj_dma_self_test`:
  - present in `required_symbols` (`specs/rastan_direct_remap.json:122`)
  - no direct `{symbol:genesistan_pc090oj_dma_self_test}` in any `replacement_bytes` field.

ROM-range check (against `address_map.json` total covered bytes = `0x17C96C`):
- `0x00070570`, `0x00071434`, `0x00071834`, `0x000719F6` are all within `[0x000000, 0x17C96C)`.

## Integrity checklist
- §1.1 artifacts located: YES
- §1.2 mapping cited from artifact: YES (result: no arcade mapping entry for this runtime PC)
- §1.3 disassembly window captured: YES (maincpu lookup result documented; postpatch runtime window provided)
- §1.4 exact instruction identified verbatim: YES
- §1.5 covering address-map entry quoted: YES
- §1.6 search complete with occurrences: YES
- §1.7 address-space classification stated: YES
- §1.8 control-flow hazard list in window: YES
- §1.9 register context reproduced verbatim: YES
- §1.10 helper symbol cross-check complete: YES
- Analysis/diagnosis/hypothesis/recommendation: NONE

