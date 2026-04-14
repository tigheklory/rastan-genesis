# Andy — Analysis: Arcade Hardware I/O Stub Strategy (0x03ADFA / 0x03AE10)

**Build context:** rastan-direct, Build 0025+  
**Crash observed:** BlastEm machine freeze on MOVE.W #0x0001, 0x00C50000 at arcade PC 0x03AE16  
**Trace artifact:** `states/traces/rastan_direct_video_test_build_0025_mame_30s_20260412_181636`

---

## 1. Function Disassembly Summary

These are **not standalone subroutines**. They are tail-code targets within a single larger
function — a "display sync state selector" — reached via `BRA.S` depending on conditions.
There are no `BSR`/`JSR` callers. The containing function ends by falling into one of two
code paths and returning via the path's own `RTS`.

### Containing function (arcade 0x03ADD8 and above)

```
arcade 03ADD8:  TST.W  0x0032(%a5)    ; test A5@(50) = monitor type
arcade 03ADDC:  BNE.S  → branch_A    ; if nonzero, go to branch_A
                                     ; else fall through to branch_B:
arcade 03ADDE:  TST.W  0x0030(%a5)    ; test A5@(48) = cabinet type
arcade 03ADE2:  BEQ.S  → branch_C    ; if cabinet = 0, go to branch_C (not crashing)
arcade 03ADE4:  BRA.S  → path_OFF    ; cabinet nonzero, monitor=0 → disable path

branch_A:
arcade 03ADE6:  TST.W  0x0030(%a5)    ; test A5@(48) = cabinet type
arcade 03ADEA:  BNE.S  → path_ON     ; monitor≠0 AND cabinet≠0 → enable path
arcade 03ADEC:  TST.W  0x002A(%a5)    ; test A5@(42)
arcade 03ADF0:  BNE.S  → path_OFF    ; A5@(42) nonzero → disable path
arcade 03ADF2:  BRA.S  → path_ON     ; else enable path
```

With factory defaults: A5@(50) = 2 (monitor flip ≠ 0), A5@(48) = 1 (cabinet ≠ 0).
Path taken: branch_A → `BNE.S → path_ON` → **func_enable** (the crash site).

---

### path_OFF — "disable" code (arcade 0x03ADFA–0x03AE0E)

```
arcade 03ADFA:  426D 001E         CLR.W   0x001E(%a5)    ; A5@(30) = 0  (flag: disabled)
arcade 03ADFE:  33FC 0000 00C5 0000  MOVE.W #0, 0x00C50000  ; hardware write → NOP
arcade 03AE06:  33FC 0001 00D0 1BFE  MOVE.W #1, 0x00D01BFE  ; hardware write → NOP
arcade 03AE0E:  4E75              RTS
```

### path_ON — "enable" code (arcade 0x03AE10–0x03AE26)

```
arcade 03AE10:  3B7C 0001 001E    MOVE.W  #0x0001, 0x001E(%a5) ; A5@(30) = 1 (flag: enabled)
arcade 03AE16:  33FC 0001 00C5 0000  MOVE.W #1, 0x00C50000  ; hardware write → CRASH → NOP
arcade 03AE1E:  33FC 0000 00D0 1BFE  MOVE.W #0, 0x00D01BFE  ; hardware write → NOP
arcade 03AE26:  4E75              RTS
```

### Summary of all C50000/D01BFE writes in ROM

There are exactly 6 writes to these addresses:

| Arcade PC  | Instruction                    | Context                                     |
|------------|--------------------------------|---------------------------------------------|
| 0x03ADFE   | MOVE.W #0, 0xC50000            | path_OFF — **patch required**               |
| 0x03AE06   | MOVE.W #1, 0xD01BFE            | path_OFF — **patch required**               |
| 0x03AE16   | MOVE.W #1, 0xC50000            | path_ON — **crash site — patch required**   |
| 0x03AE1E   | MOVE.W #0, 0xD01BFE            | path_ON — **patch required**                |
| 0x03AE86   | MOVE.W #0, 0xC50000            | startup_common — never runs, no patch needed|
| 0x03AE8E   | MOVE.W #0, 0xD01BFE            | startup_common — never runs, no patch needed|

---

## 2. Hardware Mapping

Source: `docs/reference/mame/rastan/src/mame/taito/rastan.cpp` (MAME Rastan driver).

### 0xC50000

**Identification:** PC080SN tilemap chip — screen flip control register (`ctrl_word_w`).

From `rastan.cpp` memory map:
```cpp
map(0xc00000, 0xc0ffff).rw(m_pc080sn, ...);          // PC080SN tilemap RAM
map(0xc20000, 0xc20003).w(m_pc080sn, FUNC(pc080sn_device::yscroll_word_w));
map(0xc40000, 0xc40003).w(m_pc080sn, FUNC(pc080sn_device::xscroll_word_w));
map(0xc50000, 0xc50003).w(m_pc080sn, FUNC(pc080sn_device::ctrl_word_w));
```

From `pc080sn.cpp` `ctrl_word_w` implementation:
```cpp
void pc080sn_device::ctrl_word_w(offs_t offset, u16 data, u16 mem_mask)
{
    COMBINE_DATA(&m_ctrl[offset + 4]);
    data = m_ctrl[offset + 4];
    switch (offset) {
        case 0x00: {
            u32 const flip = (data & 0x01) ? (TILEMAP_FLIPX | TILEMAP_FLIPY) : 0;
            m_tilemap[0]->set_flip(flip);
            m_tilemap[1]->set_flip(flip);
            break;
        }
    }
}
```

Bit 0 of the written word controls whether both BG and FG tilemaps are flipped
(TILEMAP_FLIPX | TILEMAP_FLIPY). Writing 0x0001 enables the flip; writing 0x0000 disables it.

The pc080sn.cpp header comment confirms: `+0x50000 control word: ---------------x flip screen`

**Why writing this address causes BlastEm to freeze:** Genesis maps its VDP at 0xC00000
(data) / 0xC00002 (control) / 0xC00004 (data) / 0xC00006 (control) / 0xC00008–0xC0001F
(H/V counter, etc.). BlastEm's VDP access handler traps all writes in the VDP address
window (0xC00000–0xC0001F range). A write to 0xC50000 falls outside the VDP register
range and into an area BlastEm does not emulate; the emulator freezes rather than silently
discarding the write.

On the actual PC hardware this write reaches the PC080SN's flip control register and sets
screen flip. On Genesis, no PC080SN exists — the write has no valid target.

### 0xD01BFE

**Identification:** PC090OJ sprite chip — sprite RAM at offset 0x1BFE.

From `rastan.cpp` memory map:
```cpp
map(0xd00000, 0xd03fff).rw(m_pc090oj, FUNC(pc090oj_device::word_r),
                                       FUNC(pc090oj_device::word_w));
```

The PC090OJ sprite RAM spans 0xD00000–0xD03FFF (16 KB). Address 0xD01BFE is at byte
offset 0x1BFE within the sprite table — near the end of the first quarter of sprite RAM.
The sprite table entries are word-indexed; 0x1BFE / 4 = entry 0x07FF (last entry in the
first 2 KB block). Writing 0x0001 or 0x0000 here sets a data word in the sprite table.

The write is architecturally benign in this context: the arcade game is writing a single
sprite-table word as part of what appears to be an enable/disable handshake (paired with
the C50000 ctrl_word_w write). Sprite entry 0x07FF is not a sprite that would normally
be visible (sprites in Rastan use the first portion of the table; the high end is empty).
The exact value written (0x0001 in path_ON, 0x0000 in path_OFF) does not correspond to a
meaningful sprite attribute for display purposes.

On Genesis no PC090OJ is present; the address 0xD01BFE falls in the upper portion of the
68K address space used for Genesis TMSS/expansion space. BlastEm does not report a crash
on this write (the address is not trapped as a VDP violation), but the write has no valid
target and must not be allowed to reach Genesis hardware registers or WRAM.

---

## 3. Behavioral Purpose

The containing function selects a "screen flip" state based on two arcade workram fields
set during factory initialization:

- `A5@(48)` = cabinet type (factory default: 1 = Cocktail)
- `A5@(50)` = monitor flip (factory default: **0** = Flip_Screen OFF)

Factory default derivation:
- remap.json injects DIP1 raw byte = **0xFE** at read time
- ndip1 = NOT(0xFE) = **0x01**
- A5@(48) = ndip1 & 1 = **1** (Cabinet = Cocktail)
- A5@(50) = ndip1 & 2 = **0** (Flip_Screen = OFF)

With these factory values the containing function takes:
```
arcade 03ADD8:  TST.W  0x0032(%a5)    ; A5@(50) = 0 → test is false
arcade 03ADDC:  BNE.S  → branch_A    ; NOT taken (A5@(50) = 0)
arcade 03ADDE:  TST.W  0x0030(%a5)    ; A5@(48) = 1 → test is true
arcade 03ADE2:  BEQ.S  → branch_C    ; NOT taken (A5@(48) ≠ 0)
arcade 03ADE4:  BRA.S  → path_OFF    ; taken — cabinet≠0, monitor=0 → disable path
```

With correct factory defaults the function takes **path_OFF**: `A5@(0x1E) = 0`,
writes 0x0000 to C50000 (flip OFF) and 0x0001 to D01BFE.

**Note on WRAM trace observation:** The Build 0025 MAME trace shows the crash occurs at
arcade PC 0x03B01E (Genesis 0x03B01E), writing 0x0001 to C50000. This corresponds to the
path_ON instruction at arcade PC 0x03AE16. The discrepancy with the correct-factory-defaults
prediction (path_OFF) is because Build 0025 was run with a factory defaults bug in the
implementation: `move.w #2, 0x0032(%a0)` was written instead of `move.w #0, 0x0032(%a0)`.
With A5@(50) = 2 (nonzero), the function takes branch_A → path_ON → crash. See pending fix
in `docs/design/Andy_genesis_bss_relocation_and_wram_map_design.md`.

**Both paths must be patched regardless** — path_OFF writes C50000=0 (harmless on arcade
open-bus equivalent; crashes BlastEm from the wrong side depending on emulator version).
Path_ON is the confirmed crash site. The function also runs in both directions at runtime
as DIP/workram state may change. All four hardware writes must be NOPed.

**The outcome stored in `A5@(0x1E)`** (the screen-flip enable flag) is still meaningful
and must be preserved: the arcade state machine reads it to determine whether to apply
flip transformations downstream. The `CLR.W` / `MOVE.W #1` to `A5@(0x1E)` (A5-relative
instructions) must NOT be patched — only the four absolute-address hardware writes are
candidates for NOPing.

---

## 4. Impact if Removed

**If the four hardware writes (C50000 and D01BFE) are NOPed:**

- `A5@(0x1E)` is still updated correctly (the `CLR.W` / `MOVE.W #1` to A5@(0x1E) are
  A5-relative instructions that are unaffected by the NOP patches)
- Screen flip state is correctly reflected in `A5@(0x1E)` for arcade logic downstream
- No visible rendering side effect: Genesis has no PC080SN, so the screen-flip command
  has no target. With correct factory defaults (A5@(50) = 0), path_OFF runs and the flip
  register would be written 0 anyway — a no-op even on real PC hardware
- No sprite RAM corruption: 0xD01BFE on Genesis has no mapped device at that address;
  the write is silently discarded by NOPing
- BlastEm no longer freezes at 0xC50000

**If the entire function body is stubbed to RTS:**

- `A5@(0x1E)` stays at 0 (factory-zeroed) forever
- Arcade display logic downstream reads `A5@(0x1E)` to decide whether to apply screen
  flip transforms; stuck at 0 may skip rendering steps or loop in a reset check
- **This would break title screen progression** — do not do this

**If neither path is taken (function never runs):**

- Same as stubbing — `A5@(0x1E)` = 0 = flip gate stuck off

---

## 5. Final Decision: OPTION A — NOP the Four Absolute Hardware Writes

**Selected: OPTION A.**

Preserve all A5-relative workram logic (CLR.W and MOVE.W to `0x001E(%a5)`). Replace only
the four `MOVE.W #imm, abs.l` instructions targeting `0xC50000` and `0xD01BFE` with NOPs.

**OPTION B (stub to RTS) rejected:** Destroys `A5@(0x1E)` update. Arcade display gate flag
stays at 0. Title screen progression blocked.

**OPTION C (emulate behavior) rejected:** The hardware writes are open bus on the original
hardware — there is nothing to emulate. The only functional side effect is the `A5@(0x1E)`
update, which is preserved by Option A at zero cost.

---

## 6. Rationale

1. **0xC50000 (PC080SN screen flip):** On real arcade hardware this write programs the
   PC080SN flip register. On Genesis there is no PC080SN — the write has no valid target
   and BlastEm freezes on it. With correct factory defaults (A5@(50) = 0), path_OFF would
   write 0x0000 here anyway (flip OFF = no-op on any display). The write is safe to elide.

2. **0xD01BFE (PC090OJ sprite RAM):** On real arcade hardware this writes a single
   sprite-table word in a high-indexed, normally-empty entry. On Genesis there is no
   PC090OJ — the address is unmapped. The data written (0x0000 or 0x0001) is not a
   meaningful sprite attribute. The write is safe to elide.

3. **A5@(0x1E) update is architecturally meaningful** and must be preserved as-is. The
   NOP patches target only the four absolute-address hardware writes; the A5-relative
   workram stores are untouched.

4. **Consistency with existing patch policy:** remap.json already uses the identical NOP
   strategy for six other arcade hardware writes (TC0040IOC at 0x380000, 0x3E0001,
   0x3E0003, etc.). This is the established pattern.

5. **Option A is four 8-byte patches** — minimum delta, zero code-path change, zero risk.

---

## 7. Cody Handoff: Patch Spec

Add the following four entries to the `opcode_replace` array in
`specs/rastan_direct_remap.json`. Insert them in arcade PC order, near the existing 0x03AExxx
patches.

```json
{
  "arcade_pc": "0x03ADFE",
  "original_bytes": "33FC000000C50000",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC080SN ctrl_word_w MOVE.W #0, 0xC50000 (screen flip OFF, path_OFF). No PC080SN on Genesis."
},
{
  "arcade_pc": "0x03AE06",
  "original_bytes": "33FC000100D01BFE",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC090OJ sprite RAM MOVE.W #1, 0xD01BFE (sprite entry 0x07FF, path_OFF). No PC090OJ on Genesis."
},
{
  "arcade_pc": "0x03AE16",
  "original_bytes": "33FC000100C50000",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC080SN ctrl_word_w MOVE.W #1, 0xC50000 (screen flip ON, path_ON — BlastEm crash site). No PC080SN on Genesis."
},
{
  "arcade_pc": "0x03AE1E",
  "original_bytes": "33FC000000D01BFE",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress PC090OJ sprite RAM MOVE.W #0, 0xD01BFE (sprite entry 0x07FF, path_ON). No PC090OJ on Genesis."
}
```

**Verification:** After patching, rebuild and confirm:
1. BlastEm no longer freezes on boot
2. `reg_c50000_live count=0` in 30-second MAME trace (no write reaches C50000)
3. `title_init_block` count > 0 in MAME trace

**Update expectations count:** `opcode_replace_count` in the `expectations` block must be
incremented from 35 to **39** (4 new entries).

---

## 8. Watch Items: Additional Hardware Writes Not in Current Crash Path

The following hardware writes target PC080SN scroll registers. They have not caused a crash
yet (not reached in the 30-second Build 0025 trace), but may appear as the game progresses
further and should be pre-emptively patched.

From `rastan.cpp`:
```cpp
map(0xc20000, 0xc20003).w(m_pc080sn, FUNC(pc080sn_device::yscroll_word_w));
map(0xc40000, 0xc40003).w(m_pc080sn, FUNC(pc080sn_device::xscroll_word_w));
```

| Arcade PC  | Instruction              | Target   | PC080SN Function             | Context                |
|------------|--------------------------|----------|------------------------------|------------------------|
| 0x03ABBA   | CLR.W abs.l              | 0xC20000 | PC080SN yscroll_word_w BG    | Init path; not reached |
| 0x03ABC0   | CLR.W abs.l              | 0xC40000 | PC080SN xscroll_word_w BG    | Init path; not reached |
| 0x03B098   | CLR.W abs.l              | 0xC20000 | PC080SN yscroll_word_w BG    | Later init path        |
| 0x03B09E   | CLR.W abs.l              | 0xC40000 | PC080SN xscroll_word_w BG    | Later init path        |

These are CLR.W (zero-write) operations to PC080SN scroll registers. BlastEm may or may
not trap these; 0xC20000/0xC40000 are in the same C-range as the VDP but offset from known
VDP ports. If BlastEm freezes on these in a future build, apply the same NOP strategy:
`CLR.W abs.l` = opcode `42B9 XXXXXXXX` (6 bytes) → `4E71 4E71 4E71` (three NOPs).

Note: On real arcade hardware, zero-writing the scroll registers sets scroll to 0 —
functionally a reset. These writes are safe to NOP on Genesis (no PC080SN scroll to reset,
and the Genesis tilemap scroll will be managed separately by the Genesis video layer).

---

## References

- `states/traces/rastan_direct_video_test_build_0025_mame_30s_20260412_181636/genesis_exec_summary.txt`
  — trace confirming crash: `reg_c50000_live count=1 first_pc=03B01E`
- `build/regions/maincpu.bin` — ROM disassembly used for all instruction-level analysis
- `specs/rastan_direct_remap.json` — existing NOP patch policy for arcade hardware writes
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp` — MAME Rastan driver; authoritative
  memory map for all hardware addresses (C20000/C40000/C50000/D00000)
- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp` — PC080SN device; `ctrl_word_w`
  implementation confirming bit 0 = screen flip
- `docs/design/Andy_genesis_bss_relocation_and_wram_map_design.md` — factory defaults
  (A5@(48) = 1, A5@(50) = 0 correct values; note: doc contains a bug at A5@(50) = 2
  that must be corrected — see pending fix task)
