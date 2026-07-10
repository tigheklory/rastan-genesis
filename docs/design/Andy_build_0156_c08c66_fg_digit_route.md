# Andy — Build 0156: Route the Raw C08C66 FG Digit Write Through Staging

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `bacecd1` (Build 0155 accepted). Build 0155 ROM `f226278f…`, counter 155.
**Evidence dir:** `states/traces/build_0155_stage1_fg_plane/`.

## Outcome
**Implemented.** The raw PC080SN FG single-digit writer at runtime `0x03D24C` (arcade `0x03D04C`),
`move.w %d1, 0x00C08C66`, is now routed through the existing FG staging path. This removes the raw C-window
store that strict-target emulators fault on — user report: **BlastEm strict-freezes at write address C08C66**
during gameplay (after the repeated fall/death sequence). Byte-neutral `opcode_replace`; no NOP, no hardcoded
cell.

## The writer (sibling of Build 0152's C08C62)
```
0x3D244  moveq   #9, %d1
0x3D246  sub.w   %d0, %d1
0x3D248  addi.w  #48, %d1        ; d1 = digit tile 0x30..0x39 (= 9 - d0 + 0x30)
0x3D24C  move.w  %d1, 0x00C08C66 ; raw FG C-window store  <-- replaced
0x3D252  rts
```
This is the exact structural sibling of `0x03A72A → 0xC08C62` (Build 0152, `genesistan_hook_inline_fg_write_
3a92a`). The earlier analysis flagged `0x03D04C/0xC08C66` as an unrouted sibling "not yet proven to block";
Build 0155 validation now proves it blocks BlastEm.

## Fix
`opcode_replace` at arcade `0x03D04C`: `33C100C08C66` → `4EB9{symbol:genesistan_hook_inline_fg_write_3d04c}`
(6→6 bytes). New hook mirrors `genesistan_hook_inline_fg_write_3a92a`:
```
genesistan_hook_inline_fg_write_3d04c:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08C64, %a0      ; FG cell base (code word at +2 = 0xC08C66)
    move.l  %d1, %d0             ; live digit code from caller's d1
    andi.l  #0x0000FFFF, %d0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill   ; LUT + attr conversion + staging + fg_row_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    tst.w   %d1                  ; reproduce the original MOVE.W N/Z/V/C
    rts
```
Digit tiles `0x30..0x39` are already LUT-mapped (slots 8..17). Registers preserved (`fg_fill` saves/restores
`d0-d7/a0-a6`); CCR reproduced via `tst.w %d1`. Routes to the existing `staged_fg_buffer` → `fg_row_dirty` →
existing FG VBlank commit — no new staging/commit path.

## Validation
- **Route (static):** `0x3D24C` is now `jsr 0x708C8` (the hook); the preceding `moveq/sub/addi` that compute
  `d1` are unchanged. Build 0152 `0xC08C62` route intact (`0x3A92A = jsr 0x70894`).
- **Route (runtime, Genesis MAME):** **0 raw writes to `0xC08C66`** over gameplay (the store is now a `jsr`);
  deterministic across two clean boots (byte-identical).
- **Build 0155 fixes intact:** at 2/3/0, `scene_id=1`, `staged_bg=2048`, `staged_fg=2048` (FG plane still
  populated). No generator/LUT/manifest change, so BG rendering and the frontend are byte-identical to Build
  0155 (title/BEST 5 unchanged).
- **Gate/map:** GATE_PASS; boot guard PASS; 30-s trace clean; address-map `gaps=[]`, `overlaps=[]`, covered
  `0x182064`, `opcode_replace=135`. Canonical paired updates: `opcode_replace_count 134→135` (spec expectations
  + both gate scripts) and coverage `0x182044 → 0x182064` (+0x20, the new hook).

## Build 0156
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0156.bin`
- **SHA256:** `03c6e8aa747700235437706adb206968b1f737453ad436959681e19d299fdf01`
- **Size:** 1,581,156 B. Counter 156. Builds 0142–0155 not overwritten.

## Scope / deferrals
Per the user's focus, this build handles only the blocking C08C66 boundary. **Not** touched (the stated next
boundaries): gameplay PC090OJ sprite production/display, scroll/control state, collision/falling, and
continue/game-over cleanup. The repeated fall/death behavior itself (BlastEm/Kega) is downstream of sprite +
scroll + collision, which follow after sprite/scroll visibility is sufficient. Exodus black screen recorded,
not investigated; no emulator-specific behavior added.

## Architecture-compliance statement
CONFIRMED. Reused `genesistan_hook_tilemap_fg_fill` + existing FG dirty/VBlank commit; byte-neutral
`opcode_replace`; no NOP, no hardcoded cell/screen, no second renderer/commit path, no dead-writer patch. The
Build 0155 FG hook, Build 0154 BG model, and Build 0152 `0xC08C62` route are untouched.

## Open issue impact
- **OPEN-017 / OPEN-018:** advanced — the last known raw PC080SN FG single-digit writer in the gameplay path
  (`0xC08C66`) is now routed through staging, clearing the BlastEm strict-target freeze. Remaining gameplay
  boundaries (sprites, scroll, collision) unchanged. Not closed; no duplicate.
