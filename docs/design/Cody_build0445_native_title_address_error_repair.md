# Cody — Build 0445 Native-Title Address-Error Repair

## Scope and baseline

- Accepted baseline: Build 0442, source commit
  `c7ca1439e5cad8028043e8b3ff56fe7282addb1d`.
- Failed title candidates retained: Builds 0443 and 0444.
- This report follows Tighe's authoritative Build-0444 BlastEm crash screen and
  repairs only its proven `0x000721AA` address error.
- No new route, manual gameplay, benchmark, guard, clamp, fallback, or repeated
  PC080SN title draw was added.

## Exact Build-0444 fault

The displayed stacked PC is `0x000721AA`, in
`genesistan_hook_glyph_renderer_3bd48` in
`apps/rastan-direct/src/tilemap_hooks.s`. The instruction at `0x721AA` is
`3418`, `move.w (a0)+,d2`, but it is the continuation PC recorded for the
preceding failed group-0 memory cycle. The instruction which actually attempts
the invalid access is:

```text
0x721A8: 2258    movea.l (a0)+,a1
```

That is a 32-bit read through `A0`. The unchanged fault-time
`A1=0x00FF0166` proves the `movea.l` did not complete. The crash handler's
fault address and register snapshot agree: `FAULT=A0=0xBEA80003`.

The local Build-0444 sequence was:

```text
move.w  d0,d1
andi.w  #0x007F,d0
lsl.w   #2,d0
movea.l #0x0003BD7C,a0
adda.w  d0,a0
movea.l (a0),a0
movea.l (a0)+,a1       ; failed; stacked continuation PC 0x721AA
move.w  (a0)+,d2
```

At the fault `D0=8`, selecting descriptor-table entry 2. The Build-0443
`0x03AA54` insertion had shifted the copied glyph pointer table from runtime
`0x03BD7C` to `0x03BD7E`, but this Genesis-only helper retained the historical
literal `0x03BD7C`. Entry 2 was consequently read two bytes early:

```text
stale base 0x03BD7C + 8 -> long 0xBEA80003
correct base 0x03BD7E + 8 -> long 0x0003BEC0
```

The correct descriptor at `0x03BEC0` begins with the destination longword
`0x00C09E84`. Therefore the expected `A0` before the failing read was
`0x0003BEC0`; after a successful `movea.l (a0)+,a1`, the expected `A0` at the
displayed continuation PC was `0x0003BEC4` and `A1` was `0x00C09E84`.

This is a reflow/relocation contract defect, not a generated three-map format,
endianness, width, stride, ABI, or stack defect. The generated maps remain
three aligned 4096-byte final-name-word arrays and their existing equivalence
verifier still passes.

## Stack-screen diagnostic

The supplied screenshot displays `FRAME SP 00FEFFE2`, not `00FFFFE2` as
transcribed in the prompt. The crash report masks the high byte, forces the
address even, and permits its raw stack dump only when the result is at least
`0x00FF0000`. `0x00FEFFE2` is below that deliberately narrow range, so
`SP OUT OF WRAM RANGE` is accurate for the displayed frame SP. It does not
explain the odd `A0` read and is not the primary fault.

## Attempted repair and Build-0445 correction

Arcade semantic cut `0x03BB48` remains the glyph/string semantic producer;
the retired tail remains the PC080SN cell-write loop. The old 52-byte
byte-neutral replacement was converted to a proper 52-to-20-byte
`shift_replacements` entry:

1. retain the arcade selector decode (`D1=selector`, `D0=(selector&0x7F)*4`);
2. resolve the immediately adjacent pointer table PC-relatively;
3. call the Genesis-native final Plane-A staging helper;
4. return, with no NOP padding.

The helper now consumes `A0=table base` instead of embedding a runtime ROM
address. However, Build 0445 encoded `lea +8(pc),a0`. On 68000 the PC-relative
base for this instruction is the extension-word address, not the address after
the extension word. Build 0445 therefore resolved `A0=0x03BD5C`, the preceding
`RTS`, rather than the mapped table at `0x03BD5E`:

```text
runtime wrapper: 0x03BD4A
41FA0008 at:       0x03BD52
actual LEA result: 0x03BD5C
mapped table:      0x03BD5E
entry 2 read:      0xBE880003
```

Tighe's Build-0445 crash screen independently proves the same calculation:
stacked continuation PC `0x7219C`, fault/A0 `0xBE880003`, and `D0=8`. The
correct Build-0446 encoding is `41FA000A`, which resolves exactly to the mapped
table. The native-title verifier now rejects both the old byte-neutral cut and
the incorrect `+8` encoding. Total Genesis coverage remains
`0x295EB8`; only the inventory class changed from 232 to 231 byte-neutral
opcode replacements. The prior `0x03AA20` three-entry dispatch-table repair is
retained.

## Build 0445 result

- Artifact family: canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, and
  `_invincible` all produced and family verification passed.
- Generated-title equivalence: PASS.
- Assembly/link, postpatch, boot guards, coverage, canonical gate: PASS.
- Gameplay-entry gate: **FAIL** — a new address error at external frame 31/32.
- Epoch gate: **FAIL** — the same new exception.
- Standard fixed 30-second run: **FAIL** as acceptance evidence; it completed
  1,798 external frames while halted in the crash screen.

The automated artifacts initially identified only vector 3 and frame SP
`0x00FEFFE2`. Tighe then supplied the improved Build-0445 crash screen, closing
the evidence gap and proving the incorrect PC-relative displacement above.

## Artifacts

- Canonical ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0445.bin`
- Size: `2711224` bytes.
- Canonical SHA-256:
  `23b574cece108eb97914e2d1e3afafb870c76360c11db3fe87276ec9514caf16`
- `_d`: `3ead7df8517269501f054c4d598c3028cc5f8d78e0f561f34119776757f9b753`
- `_s`: `89c3f0e5af0040c42b5012341697c86775e69e688d0320a98b17231a2a618c16`
- `_do`: `78a95e7ac5b854a586e3de0ee8357b01e769df4d3cf7c27eac20e0ec2b059af1`
- `_c`: `ea8f20fb155acf7a2bde165d367a0c9d342834a1d7a7371048678f66c80359d6`
- `_full_hud`: `e473436dd0f39c8dede87d168e1e0abc1be2941db9e3b7cb3817dd7eb1d12c73`
- `_invincible`: `b408439870df68bab7a63b82042c4b5303c6b21467c57cc16d37180c04fb7335`
- Counter: `444 -> 445`.
- Candidate source commit: none; normal runtime gates failed.
- Real-hardware acceptance: not requested for a failed-gate candidate.

## Next user action

Build 0445 is preserved as the failed off-by-two candidate. Build 0446 contains
the corrected `+10` displacement. Screen 2 work has not started.
