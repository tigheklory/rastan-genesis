# [Cody — Build 53 .Lpc090oj_emit_slot Caller Trace]

Type: Read-only evidence extraction (no source/spec/tool modifications, no analysis)

## Scope
- Target video: `states/screenshots/Build_53-2.mp4` (30fps, 5120x1394)
- Target extracted frames: `/tmp/exodus_frames_build53_2_14_19/frame_100.png` .. `frame_107.png` (local frames 100..107 = source 519..526)
- Target runtime address: `runtime_genesis_pc 0x000711CC` (`.Lpc090oj_emit_slot` entry)

## §1.1 Per-frame register transcription for frames 100-107
Source: [docs/design/Cody_exodus_frame_extraction_build_53_2.md:131](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L131) .. [docs/design/Cody_exodus_frame_extraction_build_53_2.md:138](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L138)

All eight frames (100..107) contain the same register state:

- Frame 100 (source 519, t=17.300s):
  - `A0=0x00FFF32C` `A1=0x00FF6B1C` `A2=0xFFFFFFFF` `A3=0x00050082` `A4=0xFFFFFFFF` `A5=0x00FF0000` `A6=0xFFFFFFFF` `A7=0x00FEFFB0`
  - `D0=0x00000AA4` `D1=0x00000000` `D2=0x00000080` `D3=0xFFFF0080` `D4=0x00000001` `D5=0x00000000` `D6=0x00000AA4` `D7=0xFFFF0030`
  - `PC=0x000711CE` `SR=0x2700` `USP=0xFFFFFFFF` `SSP=0x00FEFFB0` `IPM=7` `CCR XN ZVC = 0 0 0 0 0`
- Frame 101 (source 520, t=17.333s): unchanged from frame 100
- Frame 102 (source 521, t=17.367s): unchanged from frame 100
- Frame 103 (source 522, t=17.400s): unchanged from frame 100
- Frame 104 (source 523, t=17.433s): unchanged from frame 100
- Frame 105 (source 524, t=17.467s): unchanged from frame 100
- Frame 106 (source 525, t=17.500s): unchanged from frame 100
- Frame 107 (source 526, t=17.533s): unchanged from frame 100

Address-space tags used above:
- `PC`: runtime ROM address (`runtime_genesis_pc`)
- `A7`/`SSP` and `A0`/`A1`/`A5`: WRAM-space addresses

## §1.2 Earliest frame where D0 equals 0x00000AA4
Evidence:
- Frame 100 has `D0=0x00000AA4`: [docs/design/Cody_exodus_frame_extraction_build_53_2.md:131](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L131)
- Frame 099 (prior frame) also has `D0=0x00000AA4`: [docs/design/Cody_exodus_frame_extraction_build_53_2.md:130](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L130)

Result:
- Earliest frame in the requested window `[100..107]` with `D0=0x00000AA4`: **frame 100**
- `D0` transition occurred **before** this window (already set in frame 099)
- Transition-frame PC inside this window: `runtime_genesis_pc 0x000711CE`
- Instruction at `runtime_genesis_pc 0x000711CE` (verbatim): `muluw #12,%d6`
  - Citation: [build/genesis_postpatch.disasm.txt:124044](build/genesis_postpatch.disasm.txt#L124044)

## §1.3 Earliest frame where *(0x00FEFFB0) equals 0x008F831C
Memory target:
- `0x00FEFFB0` (WRAM stack location)

Attempt/evidence:
- The recorded extraction layout contains VDP editors, not a Main RAM memory window:
  - VRAM Memory Editor panel: [docs/design/Cody_exodus_frame_extraction_build_53_2.md:17](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L17)
  - CRAM Memory Editor panel: [docs/design/Cody_exodus_frame_extraction_build_53_2.md:18](docs/design/Cody_exodus_frame_extraction_build_53_2.md#L18)
- No per-frame memory-byte transcription for `0x00FEFFB0..0x00FEFFB3` is present in frames 100..107.

Result:
- Memory viewer coverage for WRAM `0x00FEFFxx`: **NO**
- Earliest frame where `*(0x00FEFFB0)==0x008F831C`: **EVIDENCE GAP** (not visible in current frame set/panels)

## §1.4 All BSR/BSRW/JSR instructions targeting 0x000711CC in runtime ROM
Search artifact: [build/genesis_postpatch.disasm.txt](build/genesis_postpatch.disasm.txt)

Observed callsites (all `bsrw 0x711cc`):

1. `runtime_genesis_pc 0x000712CC` — `bsrw 0x711cc` — return `0x000712D0` — owner `rastan_direct_update_inputs`
   - disasm line: [build/genesis_postpatch.disasm.txt:124124](build/genesis_postpatch.disasm.txt#L124124)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:175](apps/rastan-direct/out/symbol.txt#L175)
2. `runtime_genesis_pc 0x000712FE` — `bsrw 0x711cc` — return `0x00071302` — owner `rastan_direct_update_inputs`
   - disasm line: [build/genesis_postpatch.disasm.txt:124142](build/genesis_postpatch.disasm.txt#L124142)
3. `runtime_genesis_pc 0x0007132E` — `bsrw 0x711cc` — return `0x00071332` — owner `rastan_direct_update_inputs`
   - disasm line: [build/genesis_postpatch.disasm.txt:124159](build/genesis_postpatch.disasm.txt#L124159)
4. `runtime_genesis_pc 0x00071370` — `bsrw 0x711cc` — return `0x00071374` — owner `genesistan_pc090oj_hook_target_3b902`
   - disasm line: [build/genesis_postpatch.disasm.txt:124184](build/genesis_postpatch.disasm.txt#L124184)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:176](apps/rastan-direct/out/symbol.txt#L176)
5. `runtime_genesis_pc 0x000713C8` — `bsrw 0x711cc` — return `0x000713CC` — owner `genesistan_pc090oj_hook_target_3b930`
   - disasm line: [build/genesis_postpatch.disasm.txt:124217](build/genesis_postpatch.disasm.txt#L124217)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:178](apps/rastan-direct/out/symbol.txt#L178)
6. `runtime_genesis_pc 0x000714F6` — `bsrw 0x711cc` — return `0x000714FA` — owner `genesistan_pc090oj_hook_init_priority_3ad84`
   - disasm line: [build/genesis_postpatch.disasm.txt:124307](build/genesis_postpatch.disasm.txt#L124307)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:184](apps/rastan-direct/out/symbol.txt#L184)
7. `runtime_genesis_pc 0x000715D2` — `bsrw 0x711cc` — return `0x000715D6` — owner `genesistan_pc090oj_hook_score_digit_3b802`
   - disasm line: [build/genesis_postpatch.disasm.txt:124382](build/genesis_postpatch.disasm.txt#L124382)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:185](apps/rastan-direct/out/symbol.txt#L185)
8. `runtime_genesis_pc 0x00071676` — `bsrw 0x711cc` — return `0x0007167A` — owner `genesistan_pc090oj_hook_slot_init_54052`
   - disasm line: [build/genesis_postpatch.disasm.txt:124433](build/genesis_postpatch.disasm.txt#L124433)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:186](apps/rastan-direct/out/symbol.txt#L186)
9. `runtime_genesis_pc 0x000716D2` — `bsrw 0x711cc` — return `0x000716D6` — owner `genesistan_pc090oj_hook_sprite_update_54810`
   - disasm line: [build/genesis_postpatch.disasm.txt:124463](build/genesis_postpatch.disasm.txt#L124463)
   - owner symbol line: [apps/rastan-direct/out/symbol.txt:187](apps/rastan-direct/out/symbol.txt#L187)
10. `runtime_genesis_pc 0x0007174C` — `bsrw 0x711cc` — return `0x00071750` — owner `genesistan_pc090oj_hook_sprite_decay_5607c`
    - disasm line: [build/genesis_postpatch.disasm.txt:124501](build/genesis_postpatch.disasm.txt#L124501)
    - owner symbol line: [apps/rastan-direct/out/symbol.txt:188](apps/rastan-direct/out/symbol.txt#L188)
11. `runtime_genesis_pc 0x00071788` — `bsrw 0x711cc` — return `0x0007178C` — owner `genesistan_pc090oj_hook_copy_56114`
    - disasm line: [build/genesis_postpatch.disasm.txt:124521](build/genesis_postpatch.disasm.txt#L124521)
    - owner symbol line: [apps/rastan-direct/out/symbol.txt:189](apps/rastan-direct/out/symbol.txt#L189)
12. `runtime_genesis_pc 0x000717DE` — `bsrw 0x711cc` — return `0x000717E2` — owner `genesistan_pc090oj_hook_status_sprite_5a098`
    - disasm line: [build/genesis_postpatch.disasm.txt:124550](build/genesis_postpatch.disasm.txt#L124550)
    - owner symbol line: [apps/rastan-direct/out/symbol.txt:191](apps/rastan-direct/out/symbol.txt#L191)

Count: **12** callsites.

## §1.5 ±32-byte disassembly window around each callsite
Windows below are verbatim from `build/genesis_postpatch.disasm.txt` with address+bytes+instruction and show nearby D0/D6 setup lines.

1. Callsite `0x000712CC` — window: [build/genesis_postpatch.disasm.txt:124114](build/genesis_postpatch.disasm.txt#L124114) .. [build/genesis_postpatch.disasm.txt:124134](build/genesis_postpatch.disasm.txt#L124134)
   - D0/D6 setup in window: `moveq #0,%d1`, `movew #384,%d2`, `moveq #0,%d6`, then `bsrw 0x711cc`.
2. Callsite `0x000712FE` — window: [build/genesis_postpatch.disasm.txt:124130](build/genesis_postpatch.disasm.txt#L124130) .. [build/genesis_postpatch.disasm.txt:124152](build/genesis_postpatch.disasm.txt#L124152)
   - D0/D6 setup in window: `moveq #0,%d0`, `moveq #0,%d6`, then `bsrw 0x711cc`.
3. Callsite `0x0007132E` — window: [build/genesis_postpatch.disasm.txt:124147](build/genesis_postpatch.disasm.txt#L124147) .. [build/genesis_postpatch.disasm.txt:124170](build/genesis_postpatch.disasm.txt#L124170)
   - D0/D6 setup in window: `moveq #18,%d0`, `moveq #0,%d6`, then `bsrw 0x711cc`.
4. Callsite `0x00071370` — window: [build/genesis_postpatch.disasm.txt:124171](build/genesis_postpatch.disasm.txt#L124171) .. [build/genesis_postpatch.disasm.txt:124194](build/genesis_postpatch.disasm.txt#L124194)
   - D0/D6 setup in window: `moveq #0,%d0`, `moveq #0,%d6`, then `bsrw 0x711cc`.
5. Callsite `0x000713C8` — window: [build/genesis_postpatch.disasm.txt:124203](build/genesis_postpatch.disasm.txt#L124203) .. [build/genesis_postpatch.disasm.txt:124227](build/genesis_postpatch.disasm.txt#L124227)
   - D0/D6 setup in window: `moveq #4,%d6` then later `moveq #0,%d6`, then `bsrw 0x711cc`.
6. Callsite `0x000714F6` — window: [build/genesis_postpatch.disasm.txt:124296](build/genesis_postpatch.disasm.txt#L124296) .. [build/genesis_postpatch.disasm.txt:124317](build/genesis_postpatch.disasm.txt#L124317)
   - D0/D6 setup in window: `moveq #76,%d0`, `moveq #2,%d6`, then `bsrw 0x711cc`.
7. Callsite `0x000715D2` — window: [build/genesis_postpatch.disasm.txt:124369](build/genesis_postpatch.disasm.txt#L124369) .. [build/genesis_postpatch.disasm.txt:124395](build/genesis_postpatch.disasm.txt#L124395)
   - D0/D6 setup in window: `moveq #0,%d5`, `moveq #0,%d6`, then `bsrw 0x711cc`.
8. Callsite `0x00071676` — window: [build/genesis_postpatch.disasm.txt:124423](build/genesis_postpatch.disasm.txt#L124423) .. [build/genesis_postpatch.disasm.txt:124443](build/genesis_postpatch.disasm.txt#L124443)
   - D0/D6 setup in window: `moveq #72,%d0`, `moveq #0,%d6`, then `bsrw 0x711cc`.
9. Callsite `0x000716D2` — window: [build/genesis_postpatch.disasm.txt:124452](build/genesis_postpatch.disasm.txt#L124452) .. [build/genesis_postpatch.disasm.txt:124473](build/genesis_postpatch.disasm.txt#L124473)
   - D0/D6 setup in window: `moveq #0,%d6`, then `bsrw 0x711cc`.
10. Callsite `0x0007174C` — window: [build/genesis_postpatch.disasm.txt:124491](build/genesis_postpatch.disasm.txt#L124491) .. [build/genesis_postpatch.disasm.txt:124511](build/genesis_postpatch.disasm.txt#L124511)
    - D0/D6 setup in window: `moveq #0,%d5`, `moveq #0,%d6`, then `bsrw 0x711cc`.
11. Callsite `0x00071788` — window: [build/genesis_postpatch.disasm.txt:124510](build/genesis_postpatch.disasm.txt#L124510) .. [build/genesis_postpatch.disasm.txt:124531](build/genesis_postpatch.disasm.txt#L124531)
    - D0/D6 setup in window: `moveq #64,%d0`, `moveq #0,%d6`, then `bsrw 0x711cc`.
12. Callsite `0x000717DE` — window: [build/genesis_postpatch.disasm.txt:124539](build/genesis_postpatch.disasm.txt#L124539) .. [build/genesis_postpatch.disasm.txt:124559](build/genesis_postpatch.disasm.txt#L124559)
    - D0/D6 setup in window: `moveq #30,%d0`, `moveq #0,%d6`, then `bsrw 0x711cc`.

## Phase-2 Integrity Checklist
- §1.1 frames 100-107 transcribed (8 frames): YES
- §1.2 D0=0xAA4 transition frame identified: YES (earliest in window = frame 100; transition before window)
- §1.3 `*(0x00FEFFB0)=0x008F831C` transition identified: EVIDENCE-GAP (WRAM memory bytes not visible)
- §1.4 callsites to `0x000711CC` enumerated: YES (12)
- §1.5 ±32-byte windows dumped: YES (12)
- Addresses cited from artifacts: YES
- Analysis/diagnosis/hypotheses/recommendations: NONE
- Source/spec/tool modifications: NONE

