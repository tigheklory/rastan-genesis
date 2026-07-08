# Andy — Build 0146: PC090OJ 0x03B902 Faithful Translation Correction (Outcome B, retained)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** bounded correction + verification.
**Baseline:** `rastan-direct-proposal` @ `0b3f8b484bcc51685252f8350514fbc6d29b2915`; accepted ROM
`dist/rastan-direct/rastan_direct_video_test_build_0145.bin` = `b5c903a942b669e869b5b2d4ed4448f96d402707e3dcda946afabe2eb4dd23f7`.
**Evidence dir:** `states/traces/build_0146_pc090oj_3b902_fix/`.

## Outcome
**Outcome B — GH fixed, separate UP defect remains.** The `0x03B902` translation is now faithful; the title header
renders complete `HIGH SCORE`; record 4 (the "GH" glyph) is preserved; no unrelated regression. The independent,
out-of-scope missing "UP" in "2UP" still remains and was **not** investigated. Production change **retained**.

## Proven arcade 0x03B902 semantics
Disassembly of the authoritative body (`objdump` of the `address_map` original_bytes; runtime-confirmed):
```
3b902: lea 0xD00088,%a1        ; a1 = PC090OJ records 17..21 (HW_ADDRESS 0xD00088)
3b908: tst.w %d1
3b90a: bne.s 3b918             ; d1 != 0 -> fill
       ; clear path (d1 == 0):
3b90c: lea %pc@(0x3b984),%a0   ; a0 = 5-record descriptor table at 0x3B984
3b910: moveq #5,%d1
3b912: bsr 0x3b930             ; copy 5 records (table -> records 17..21)
3b916: rts
       ; fill path (d1 != 0):
3b918: moveq #5,%d0
3b91a: move.b %d1,2(%a1)       ; write byte d1 to the Y-high byte (offset 2) only
3b91e: addq.l #8,%a1           ; next record
3b920: subq.w #1,%d0
3b922: bne.s 3b91a             ; x5  (records 17..21)
3b924: rts
```
The arcade `0x03B902` operates exclusively on records 17..21; it never touches record 4. Runtime: the title invokes
only the **fill** path (`CALL3B902 d1=0x0001`), and the fill writes `0xD0008A` (record 17 Y-high). The clear-path
table at `0x3B984` (Genesis `0x3BB84`) decodes as 5 valid descriptors: `Y=EC code=2A`, `Y=E8 code=34/35/36/2B`.

## Previous Genesis helper behavior (Build 0142–0145)
`genesistan_pc090oj_hook_target_3b902` looped records **0..4** calling `.Lpc090oj_emit_slot` with full descriptors
(clear path → code 0; fill path → code 1, X 0). This wrote records the arcade never touches and, at record 4,
overwrote the correct GH descriptor (`code 0x3B, X 0x88`) with `(0,0,1,0)` — the proven cause of the missing GH.

## New Genesis helper behavior (Build 0146)
`apps/rastan-direct/src/pc090oj_hooks.s`, `genesistan_pc090oj_hook_target_3b902` (registers fully preserved via
`movem`, matching the prior contract):
- **Clear path (d1==0):** `lea 0xD00088,%a1; lea 0x3BB84,%a0; moveq #5,%d1; bsr genesistan_pc090oj_hook_target_3b930`
  — delegates to the existing faithful `0x3B930` copy translation to write the 5-record table into records 17..21
  (mirror + candidate). Mirrors the arcade `bsr 0x3B930`.
- **Fill path (d1!=0):** loop 5 records writing byte `d1` to the Y-high byte (offset 2) of records 17..21 via the
  existing `.Lpc090oj_mirror_write_byte_a1_d0` (`a1 = 0xD0008A + 8*i`), which sets the per-record candidate so the
  retained renderer re-syncs. Mirrors the arcade `move.b %d1,2(%a1)` ×5.

## Why this implementation is faithful and minimal
It reproduces the arcade `0x03B902` exactly (same destination records 17..21, same per-path operation) while reusing
the existing mirror/candidate/copy pipeline (`genesistan_pc090oj_hook_target_3b930`, `mirror_write_byte`). The fill
path writes only the single Y-high byte per record (no full descriptor), matching the arcade byte write. It touches
no records outside 17..21, changes no other field, alters no caller-visible register, and requires no renderer,
allocator, palette, or additional-file change. Clear and fill paths are handled separately because they are distinct
arcade operations (table copy vs single-byte Y update).

## Exact records and fields written (runtime-verified)
- **Fill (title):** `pc=0x71A30` (the new helper's `mirror_write_byte` call) writes byte `0x01` to `0xFF6A3A`,
  `0xFF6A42`, `0xFF6A4A`, `0xFF6A52`, `0xFF6A5A` — the Y-high bytes of mirror records 17,18,19,20,21 only. No other
  field and no other record is written by this helper.
- **Records 0..4 no longer written by 3b902:** watchpoints on mirror record 3 (`0xFF69C8`) and record 4 (`0xFF69D0`)
  show zero writes from the helper; the only record-4 writers are boot-clear (`pc=0x320`), the `0x3AD48` clear
  translation (`genesistan_hook_3ad44_dispatch`, `pc=0x71C6A/0x71C7E`, Y=0x100), and the GH producer (`pc=0x719EC`,
  `code 0x3B`). **Zero code-1 writes to record 4.**
- **Clear path** not exercised on the title (title uses fill only); its faithful table-copy target is records 17..21.

## Final record-4 descriptor
Mirror record 4 at the settled title frame = `word0 0x0000, Y 0x0000, code 0x003B, X 0x0088` (**GH**), represented on
SAT slot 0. Records 5–8 = `0x3A/0x3C/0x3D/0x3E` (HI/ S/CO/RE), slots 1–4 — the full `HIGH SCORE` set is intact.

## HIGH SCORE visual result
Title screen: `HIGH SCORE` renders **complete** (H-I-G-H space S-C-O-R-E) in orange, matching the arcade;
`1UP` yellow, score digits white. Screenshot `states/traces/build_0146_pc090oj_3b902_fix/snaps/gen146_title.png`.

## Whether UP returned
**No.** `2UP` still renders as `2` with the `UP` missing — an independent, state-dependent defect explicitly out of
scope. Not investigated. Reported as a separate remaining defect.

## Build 0145 palette / item-screen regression result
No regression. Item screen (state 2/2/6): represented count **22** (identical to Build 0145); `(bank 48 → line 2): 18`
(records 28–45), `(bank 51 → line 3): 4` (records 64–67); staged line 2 = bank 48, staged line 3 = bank 51 (both
populated, byte-identical to Build 0145 `line3 = 0000 0000 0eee 08ae 044a 0246 0008 0006 00ee 006e 0080 0060 0888
0666 0040 000e`); the four bank-51 item sprites remain visible with correct colours. Palette lines, item sprites, and
the rest of `HIGH SCORE` are unchanged. Snapshot `snaps/gen146_item.png`.

## Build 0146
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0146.bin`
- **SHA256:** `3edcf345d1c6e547b993f72b29ab9d80f7fa58823ad992de962391a5ce8a416b`
- **Size:** 1,563,892 B (Build 0145 = 1,563,900; −8 B, the new body is smaller). Builds 0142–0145 not overwritten.
- **Address-map:** `opcode_replace = 133`; `total_genesis_bytes_covered = 1563892 = 0x17DCF4`; **gaps = 0, overlaps = 0**;
  no patched-site/wrapper change.
- **Production source changed:** `apps/rastan-direct/src/pc090oj_hooks.s` (only `genesistan_pc090oj_hook_target_3b902`).
- **Canonical coverage change:** `0x17DCFC → 0x17DCF4` (paired, value-only) in `postpatch_startup_rom.py` +
  `verify_canonical_rom.py`.
- **Generated files changed:** `out/pc090oj_hooks.o/.elf/symbol.txt`, disasm, `rom_inventory.json`, numbered ROM, trace.
- **Unexpected-delta assessment:** none — confined to the edited helper and normal generated consequences.

## Architecture-compliance statement
CONFIRMED. The change is an in-place faithful reimplementation inside the existing arcade-called helper
`genesistan_pc090oj_hook_target_3b902` (returns via RTS), reusing the existing mirror/candidate pipeline and the
existing `0x3B930` copy translation. No Genesis-owned loop/lifecycle, second VBlank, second renderer, direct
committed-SAT patching, screen-specific handling, word-specific special-casing, diagnostic code, tooling, or
scaffolding. Retained renderer, mirror, candidate bitset, record identity, `record_to_slot`, SAT allocator, pattern
residency, and VBlank commit are intact. Palette (Build 0144/0145), planes, assets, and unrelated hooks untouched.

## Open/Closed Issues Impact
- **OPEN-024 (PC090OJ subsystem incomplete):** advanced — the `0x03B902` translation is corrected to faithfully
  match the arcade (records 17..21; fill = Y-high byte, clear = table copy), eliminating the record-4 clobber. Not
  closed (broader PC090OJ correctness, gameplay, and the separate `2UP`/`UP` defect remain).
- **OPEN-001 (title/attract graphics incomplete):** advanced — `HIGH SCORE` now renders complete. Remaining
  documented title defects (missing `UP` in `2UP`, etc.) are unaffected. Not closed.
- No issue closed; no duplicate opened.

## KNOWN_FINDINGS impact
Propose (pending curation, not auto-added): arcade `0x03B902` targets PC090OJ records 17..21 (`0xD00088`) — clear
path copies the 5-record table at `0x3B984` via `0x3B930`, fill path writes only the Y-high byte; the faithful
Genesis translation reuses `genesistan_pc090oj_hook_target_3b930` and a Y-high byte mirror write. Confidence CONFIRMED
(arcade disasm + arcade/Genesis watchpoints + visual), Applicability BUILD_SPECIFIC (Build 0146), Hazard HIGH.

## Scope statement
The separate missing `UP` in `2UP`, palette work (Builds 0143–0145), score values/extra zeros, item-screen layout,
PC080SN, gameplay, audio, scrolling, and real-hardware behavior were not investigated.
