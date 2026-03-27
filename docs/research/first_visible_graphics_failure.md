# First Visible Graphics Failure

## Section 1 - First Graphics Producer
First proven graphics-producing instruction in the live title init path is the text dispatch call:

- Address: `0x03AAFA` (`bsrw 0x03BD5E`), with `D0=0x0009` set at `0x03AAF8`
- Follow-up text IDs in same init block: `0x03AB0A` (`D0=0x000A/0x000B`), `0x03AB16` (`D0=0x001E`), `0x03AB1C` (`D0=0x0020`)
- Intended visual result: title text lines should be emitted (attr+glyph cells) through the text writer path and become visible on the active plane.

Evidence:
- Static title cluster disassembly (`dist/Rastan_232.bin`):
  - `0x03AAFA -> bsr 0x03BD5E`
  - `0x03AB0A -> bsr 0x03BD5E`
- Runtime (`/tmp/title_forward_probe.txt`):
  - `title_text_disp_03BD5E=1` (hit)

## Section 2 - Current Translation Path
Trace of that exact producer path in current image:

1. `0x03AAFA` calls `0x03BD5E`.
2. `0x03BD5E` currently does `jsr 0x2027C0` then `rts`.
3. `0x2027C0` is not the text wrapper now; it is a mid-body copy/dispatch region.
4. Real wrapper (`push A5 -> jsr 0x20034C -> pop A5 -> rts`) is at `0x202A4C`.

Evidence:
- Static disassembly:
  - `0x03BD5E: jsr 0x2027C0`
  - `0x202A4C: movel a5,-(sp); jsr 0x20034C; movea.l (sp)+,a5; rts`
- Runtime (`/tmp/title_forward_probe.txt`):
  - `text_wrap_2027C0=1`
  - `text_prod_20034C=0`
  - `tile_a_200000=0`
  - `tile_b_2001A6=0`

Where data goes now:
- Text-shadow window writes do occur at `0xFFC84C..0xFFCC4B`, but top writers are clear/maintenance paths (`0x03AF5A`, `0x20161E`), not `0x20034C`.
- Snapshot cells are spaces (`glyph=0x0020`) with zero attrs.

## Section 3 - VDP Verification
Using current probe evidence:

- Is tile data in VRAM? **NO (for title-producing path)**
  - `0x20034C=0`, `0x200000=0`, `0x2001A6=0` in `/tmp/title_forward_probe.txt`.
  - DMA stream associated with transfer path is zero payload in `/tmp/build228_vdp_value_hist.txt`:
    - `pc=202D80..202DA0`: all writes are `0000` (e.g. `count=572 zero=572` per PC).

- Is SAT populated? **NO (not meaningfully populated)**
  - `/tmp/title_forward_probe.txt`:
    - `blockA nonzero_bytes=0/144`
    - `blockB nonzero_bytes=3/32`
    - only one partial block-B entry (`w2=3127`, `w3=0031`, with `w0/w1=0`), not a drawable stable tuple set.

- Are planes written? **NO**
  - `/tmp/title_forward_probe.txt`:
    - `tile_a_200000=0`
    - `tile_b_2001A6=0`

Note:
- VDP ports are active (`vdp_data_writes=23487`, `vdp_ctrl_writes=13575`), but activity is not equivalent to valid title geometry/text output.

## Section 4 - Exact Breakpoint
=== FIRST_GRAPHICS_TRANSLATION_FAILURE ===
- arcade_producer: `0x03AAFA -> 0x03BD5E` (title text dispatch IDs `9/10/11/30/32`)
- expected_genesis_output:
  - `0x03BD5E -> 0x202A4C -> 0x20034C`
  - produce non-space attr/glyph cells in text-shadow (`0xFFC84C+`) and then active plane/tile output
- actual_result:
  - `0x03BD5E -> 0x2027C0` (stale/wrong semantic target)
  - `0x20034C` never executes
  - plane writers remain inactive (`0x200000=0`, `0x2001A6=0`)
  - downstream sprite descriptors are also near-empty (`A=0/144`, `B=3/32`)
- why nothing appears:
  - the first title text producer handoff lands on a stale target, so real text production never starts; remaining VDP activity is mostly palette/clear/zero-payload traffic, yielding no meaningful visible title composition.

## Section 5 - DMA / Upload Path
- Is DMA used for upload? **YES**
  - Control-side DMA programming is present in active path (`/tmp/build228_vdp_value_hist.txt`):
    - `0x202CA8=9340`, `0x202CB0=9400`, `0x202CBE=9590`, `0x202CCE=96F9`, `0x202CDE=971C`, `0x202D58=4000/7400`, `0x202E66=8F02`.
- Where:
  - VDP control/data write owners include `0x202D58`, `0x202E66`, and data stream `0x202D80..0x202DDE` (`/tmp/build228_vdp_write_probe_pcs.txt`).
- What data:
  - Transfer data is predominantly/all zeros in the sampled upload path (`/tmp/build228_vdp_value_hist.txt`, `pc=202D80..202DA0` and `202DBE/CA/D4/DE` all zero-dominant).

Why this still prevents rendering:
- DMA engine activity alone is not enough; current producer paths do not supply meaningful title text/tile/sprite payload, so DMA/upload cycles move zero/clear data instead of drawable content.
