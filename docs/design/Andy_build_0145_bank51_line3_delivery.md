# Andy — Build 0145: Deliver Arcade Bank 51 to Genesis CRAM Line 3 (Outcome A, retained)

**Agent:** Andy, temporarily filling Cody's implementation/runtime-evidence role (exception ends Thursday evening).
**Type:** Implementation + verification. One production edit, one ROM (Build 0145).
**Baseline:** `rastan-direct-proposal` @ `c311d3c` (retained Build 0144). Build 0144 SHA
`ba1ed586daa587cf0f6d2ffe851c0771b9d4ad42fb94677af42cdeed3d9d91ae` (not overwritten).

## Outcome
**Outcome A — bank 51 delivered correctly.** The existing `0x059AD4` palette helper now accepts the arcade's bank-51
update (`d0 = 0x33`) and stages it into Genesis palette line 3 through the existing conversion/staging body. On the
item screen, staged line 3 is nonzero and equals the arcade bank-51 source word-for-word (16/16), the four item
sprites (records 64-67) render visibly with correct bank-51 colours, and bank 48 / line 2 / planes / header are
unchanged. Production change **retained and committed**.

## Exact `0x059AD4` change (`genesistan_palette_hook_59ad4`, `apps/rastan-direct/src/palette_hooks.s`)
Before the existing `cmpi.w #4,%d0; bcc .L59_done` low-bank gate, a special case for `d0 == 0x33` remaps the
destination to line 3 and falls into the same accepted conversion/staging body (source unchanged = `a0 + d1*32`):
```
    cmpi.w  #0x0033, %d0
    bne.s   .L59_not_bank51
    moveq   #3, %d0                 /* arcade bank 51 -> Genesis line 3 */
    bra.s   .L59_dest_ready
.L59_not_bank51:
    cmpi.w  #4, %d0
    bcc.s   .L59_done
.L59_dest_ready:
```
Low banks 0..3 keep `line = d0`; every other high bank keeps the existing `<4` rejection. No new bank-copy
mechanism, no new producer, no direct CRAM write — the existing `.Lxbgr555_to_cram` conversion, `staged_palette_words`
destination, and `palette_dirty` assertion are reused, returning normally to arcade execution.

## Bank-51 arcade source
Arcade palette bank 51 at `HW_ADDRESS 0x00200660` (bank 51 × 0x20), reached through the existing hook's own source
computation (`a0 + d1*32`) for the arcade's `d0=0x33` write. Confirmed correct by the result: staged line 3 equals
the converted arcade bank-51 words (below).

## Staged line-3 result (item screen, 16 raw Genesis CRAM words)
```
0000 0000 0eee 08ae 044a 0246 0008 0006 00ee 006e 0080 0060 0888 0666 0040 000e
```
RGB (3-bit/chan): `. . #ffffff #ffb691 #b64848 #6d4824 #910000 #6d0000 #ffff00 #ff6d00 #009100 #006d00 #919191
#6d6d6d #004800 #ff0000` = white / flesh / red / brown / dark-red / yellow / orange / green / grey / red.
**Staged line 3 == converted arcade bank 51: 16/16 words match** (channel-exact against arcade `0x200660`).

## Bank-51 SAT selector result
Item screen (`2/2/6`): records 64-67 → Genesis palette **line 3** (correct); records 28-45 → line 2. Selector map
unchanged from Build 0144 (`pc090oj_hooks.s` not touched). Records 64-67 remain represented; geometry/tile/link/size
/priority/visibility unchanged (SAT untouched this build).

## Item-sprite visible result
The four bank-51 item sprites are **now visible** with plausible arcade colours — a green-shaft/red weapon by
`ARMATURE` and a red sword by `IRE SWORD` (Build 0144 rendered them black/invisible because line 3 was zero).

## Bank 48 / line 2 — unchanged
Staged line 2 is byte-identical to Build 0144 on both captured screens
(`0000 0000 0008 004e 008e 00ee 08ee 0eee 0a00 0e40 0e80 0ec0 0eea 0000 0000 0000` = bank 48); records 28-45 → line 2.
The `0x03BA64` determiner and the SAT selector were not modified.

## Header regression check (title 0/1/0)
`1UP` = yellow, `HI SCORE` = orange, score text white — unchanged from Build 0144 (arcade-correct). Staged line 2
unchanged. Bank-48 header sprites still select line 2.

## Plane regression check
None. RASTAN logo (yellow/gold, Plane B line 1), sword, and text (Plane A line 0) render unchanged; plane palette
selection was not touched (only staged line 3 changed, which no plane consumes).

## Smoke check
Frontend cycled through title (`0/1/0`) and item (`2/2/6`) with no crash/regression; GATE_PASS and clean 30 s auto
trace. Note: on screens without bank-51 sprites (e.g. title), staged line 3 remains zero — harmless, since no
selector uses line 3 there; it is populated on the item screen where the arcade issues the `d0=0x33` update.

## Build 0145
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0145.bin`
- **SHA256:** `b5c903a942b669e869b5b2d4ed4448f96d402707e3dcda946afabe2eb4dd23f7`
- **Size:** 1,563,900 B (Build 0144 = 1,563,888; +12 B). Builds 0142 and 0144 not overwritten.
- **Source changed:** `apps/rastan-direct/src/palette_hooks.s` only.
- **Paired canonical (value-only, authorized):** `CANONICAL_TOTAL_GENESIS_BYTES_COVERED 0x17DCF0 → 0x17DCFC`
  (`postpatch_startup_rom.py` + `verify_canonical_rom.py`); `opcode_replace` unchanged (133).
- **Generated:** `out/palette_hooks.o/.elf/symbol.txt`, disasm, `rom_inventory.json`, numbered ROM, auto trace.
- **Address-map:** `total_genesis_bytes_covered = 1563900 = 0x17DCFC`; **gaps = 0, overlaps = 0**; no patched-site/
  wrapper change. **Unexpected-delta: none** (confined to the edited helper + normal generated consequences).

## Architecture-compliance statement
CONFIRMED. The change is an in-place special case inside the existing arcade-called helper `genesistan_palette_hook_59ad4`
that returns via RTS through the single existing palette path (`0x059AD4 → conversion → staged_palette_words →
palette_dirty → vdp_commit_palette → CRAM`). No direct CRAM write, second producer, second commit, second VBlank,
Genesis-owned loop/lifecycle, screen-state detection, palette restoration, or diagnostic instrumentation was added.
Arcade code retains execution ownership.

## Open/Closed Issues Impact
- **OPEN-006 (sprite/high-bank palette mapping deferred):** advanced. The frontend sprite palette is now complete:
  bank 48 → Genesis line 2 (Build 0144, correct header on all five screens) and bank 51 → Genesis line 3 (Build 0145,
  item sprites correct), both resident simultaneously, with planes on lines 0/1 unchanged. Not closed — the general
  high-bank mapping for gameplay and other arcade sprite banks remains outside this frontend scope and requires its
  own verification and Tighe approval.
- **OPEN-024 / OPEN-001:** context only, unchanged, not closed.
- No issue closed; no duplicate opened.

## KNOWN_FINDINGS impact
Propose (pending curation, not auto-added): the arcade's per-colbank frontend sprite palette load reaches Genesis via
two producers — bank 48 through `genesistan_palette_hook_3ba64` (arcade `0x03BA64`) at boot, and bank 51 through
`genesistan_palette_hook_59ad4` (arcade `0x059AD4`, `d0=0x33`) on the item screen; routing each to Genesis lines 2/3
respectively yields arcade-correct frontend sprite colours. Confidence CONFIRMED (native selectors + staged dumps +
16/16 arcade-bank match + visual), Applicability BUILD_SPECIFIC (Build 0145 frontend), Rediscovery Hazard HIGH.
Consolidates the pending KF-039/KF-040 proposals.

## Explicit statements
Production change **retained** (Outcome A). No unrelated source changed; `pc090oj_hooks.s`, the bank-48/bank-51
selectors, `0x03BA64`, staged line 2, plane palettes, Window, sprite records/geometry, and gameplay were not touched.
