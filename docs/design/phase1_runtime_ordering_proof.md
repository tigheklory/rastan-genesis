# Phase 1 Runtime Ordering Proof — Build 273

## 1. Purpose

Verify that Build 273 (the current tree, incorporating Phase 1 ordering fix) was freshly built,
that the Phase 1 ordering patch is statically present in the ROM, and that runtime evidence
from the Genesis MAME harness either proves or disproves that the producer executes before the
renderer during the real title-init path. Produced by Andy (verification agent).

---

## 2. Files and Tools Read / Used

### Mandatory reads (pre-task)
- `/home/tighe/projects/rastan-genesis/AGENTS.md`
- `/home/tighe/projects/rastan-genesis/AGENTS_LOG.md` (last 500 lines)
- `/home/tighe/projects/rastan-genesis/docs/design/phase1_execution_results.md`
- `/home/tighe/projects/rastan-genesis/docs/design/phase1_revert_and_order_fix_patch_plan.md`
- `/home/tighe/projects/rastan-genesis/docs/design/opcode_change_audit_keep_rework_revert.md`
- `/home/tighe/projects/rastan-genesis/docs/research/title_screen_graphics_call_inventory.md`
- `/home/tighe/projects/rastan-genesis/docs/research/build271_title_logo_sprite_translation.md`

### Build / verification tools
- Build command: `source tools/setup_env.sh && make -C apps/rastan release`
- Symbol file: `apps/rastan/out/symbol.txt`
- Spec file: `specs/startup_title_remap.json`
- Patch manifest: `build/rastan/startup_common_rom_manifest.json`
- MAME harness: `tools/mame/run_genesis_trace_wsl.sh`
- Probe script 1: `/tmp/build273_ordering_proof.lua` (written by Andy for this task)
- Probe script 2: `/tmp/phase1_runtime_ordering_genesis_probe.lua` (pre-existing from Cody's Build 272 run)

---

## 3. Fresh Build 273 Confirmation

### Build command used
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

### Output artifact
```
dist/Rastan_273.bin
```

### File details
```
-rwxr-xr-x 1 tighe tighe 3932160 Mar 28 14:50 /home/tighe/projects/rastan-genesis/dist/Rastan_273.bin
Modify: 2026-03-28 14:50:59.637 -0400
Size:   3,932,160 bytes
```

### Source file timestamps (must be older than ROM)
```
specs/startup_title_remap.json  Modify: 2026-03-28 01:50:42 -0400
apps/rastan/src/main.c          Modify: 2026-03-28 01:26:50 -0400
```

ROM timestamp (14:50) is newer than all source files (01:26-01:50). Build is fresh.

### Release counter verification
- `dist/release_counter.txt` contains: `273`
- `dist/latest_release_name.txt` contains: `Rastan_273.bin`

### Build output (tail)
```
shift_table_patcher: 23 replacement(s), 6 jump-table fix(es), 0 long-pointer-table fix(es),
                     7194 branch fix(es), 608 abs-long fix(es)
Release: ../../dist/Rastan_273.bin
```

---

## 4. Static Patch Confirmation (Build 273)

### Symbol file evidence
From `apps/rastan/out/symbol.txt`:
```
002005c4 T genesistan_render_sprites_vdp
00202b80 T genesistan_render_sprites_vdp_bridge
```

### Accumulated shift calculation (before 0x03A8E0)

The Genesis ROM address of arcade PC 0x03A8E0 is:
```
genesis_addr = arcade_pc + 0x200 (base reloc) + accumulated_shift_before(arcade_pc)
```

Shift-table entries before 0x03A8E0 that add shifts:
```
arcade_pc=0x03A20E  +2 bytes  cum_shift=2
arcade_pc=0x03A264  +2 bytes  cum_shift=4
arcade_pc=0x03A640  +2 bytes  cum_shift=6
arcade_pc=0x03A6C4  +2 bytes  cum_shift=8
arcade_pc=0x03A820  +2 bytes  cum_shift=10
arcade_pc=0x03A854  +2 bytes  cum_shift=12
```

Total accumulated shift before 0x03A8E0: **12 bytes**

```
Patch A (arcade 0x03A8E0) → Genesis 0x03A8E0 + 0x200 + 12 = 0x03AAEC
Patch B (arcade 0x03A8E4) → Genesis 0x03A8E4 + 0x200 + 14 = 0x03AAF2
         (Patch A adds +2 to accumulated shift for entries after it)
```

### ROM bytes at patch addresses

```
Address 0x03AAEC (Patch A — producer call slot):
  Bytes:    4E B9 00 05 A1 5E
  Decoded:  JSR $0005A15E
  Expected: JSR to producer (relocated from arcade 0x059F5E)
  Note:     0x059F5E + 0x200 = 0x05A15E (base relocation only)
            Full relocation (+ 22 accumulated shifts) would be 0x05A174
            The rom_absolute_call_relocation applied only +0x200 delta (documented behavior)

Address 0x03AAF2 (Patch B — renderer call slot):
  Bytes:    4E B9 00 20 2B 80
  Decoded:  JSR $00202B80
  Expected: JSR to genesistan_render_sprites_vdp_bridge
  Confirmed: 0x00202B80 = genesistan_render_sprites_vdp_bridge (symbol file match)
```

### Patch ordering structure

**Before Phase 1** (incorrect):
```
0x03AAEC  JSR genesistan_render_sprites_vdp_bridge  [RENDERER — wrong: first]
0x03AAF2  JSR 0x059F5E (producer)                   [PRODUCER — wrong: second]
```

**After Phase 1 / Build 273** (correct):
```
0x03AAEC  JSR $0005A15E (→ producer path)            [PRODUCER SLOT — first]
0x03AAF2  JSR $00202B80 (genesistan_render_sprites_vdp_bridge)  [RENDERER — second]
```

### Static patch conclusion

The ordering patch IS present in Build 273. Patch A occupies the first call slot with a JSR
to the producer path. Patch B occupies the second call slot with a confirmed JSR to
`genesistan_render_sprites_vdp_bridge` (0x202B80). The ordering structure matches the
Phase 1 plan.

**Anomaly noted**: Patch A calls 0x05A15E (producer + 0x200 base relocation only), but the
actual producer function starts at 0x05A174 (producer + 0x200 + 22 accumulated shifts). The
bytes at 0x05A15E are `00 40 00 80` (sprite table data, not function start). The full
accumulated-shift relocation was NOT applied by `rom_absolute_call_relocation`. This is an
existing issue present in Build 272 as well and is not introduced by this verification build.

---

## 5. Input Method / Path-Entry Method

### MAME harness used
```
tools/mame/run_genesis_trace_wsl.sh
```

### Run commands
```bash
# Primary probe (Andy's Build 273 probe):
timeout 120s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_273.bin \
  -autoboot_script /tmp/build273_ordering_proof.lua \
  -sound none -video none

# Secondary probe (Cody's pre-existing phase1 probe, for direct comparison):
timeout 120s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_273.bin \
  -autoboot_script /tmp/phase1_runtime_ordering_genesis_probe.lua \
  -sound none -video none
```

### Input injection
Both probes use `emu.ioport` based button injection (not memory-tap based):
```lua
-- Press START at frame 20, release at frame 120
if frame == 20 then f_start:set_value(1) end
if frame == 120 then f_start:set_value(0) end
```

### Taps installed (Andy's probe)
```
tap: pad1_inject 0xA10002-0xA10003
tap: callsite_a 0x03AAEC                  (first call slot / producer slot)
tap: callsite_b 0x03AAF2                  (second call slot / renderer slot)
tap: producer_relo 0x05A15E               (what ROM's JSR actually calls)
tap: producer_func 0x05A174               (actual producer function start)
tap: renderer_bridge 0x202B80             (genesistan_render_sprites_vdp_bridge)
tap: renderer_inner 0x2005C4              (genesistan_render_sprites_vdp)
tap: block_a_write 0xFF11FE-0xFF121D
tap: block_a_read 0xFF11FE-0xFF121D
```

---

## 6. Proof That Intended Patched Path Was Reached

### Screen state throughout the run
```
heartbeat frame=000060  screen=0000
heartbeat frame=000180  screen=0000   (hits observed in this frame)
...
heartbeat frame=000900  screen=0000
```

The Genesis `current_screen` variable at `0xE0FF6DCC` (alias 0xFF6DCC in 24-bit MAME space)
**never transitions** away from `0` (SCREEN_CONFIG = 0) during the entire run.

`SCREEN_FRONTEND_LIVE = 4`. This value was never observed.

### What was reached

The A-button press at frame 168 caused the arcade maincpu code to enter a state where
A5+0 = 0x0001 (arcade work RAM major state = 1, title) at frame 180. The 0x03AAEC/0x03AAF2
callsites were executed. However:

- The game did not navigate through the SGDK launcher menu item "START RASTAN"
- The `genesistan_init_workram_direct()` / `restore_launcher_vdp_state()` / proper
  `SCREEN_FRONTEND_LIVE` initialization sequence was NOT run
- `current_screen` remained at 0 (SCREEN_CONFIG) throughout

The hits at frame 180 occurred while the Genesis `current_screen` was still SCREEN_CONFIG.
This is NOT the intended title-init path through the SCREEN_FRONTEND_LIVE execution loop.

### State summary

The arcade workram state (A5+0/2/4) at the hit frames shows title state, but the Genesis
launcher `current_screen` never reached SCREEN_FRONTEND_LIVE. These are two separate state
machines. The hits came from the arcade maincpu loop executing in a partial-init state
triggered by the A-button press, not from the full SCREEN_FRONTEND_LIVE path.

**Path-entry conclusion: The intended title-init path through SCREEN_FRONTEND_LIVE was NOT
proven to be reached during this measurement session.**

---

## 7. Raw Runtime Trace Output

### From /tmp/phase1_runtime_ordering_genesis_probe.txt (direct comparison to Build 272)
```
probe_start start_field=true
heartbeat frame=000060 screen=0000 mode4=0000 credits=0000
heartbeat frame=000120 screen=0000 mode4=0000 credits=0000
heartbeat frame=000180 screen=0000 mode4=0000 credits=0000
heartbeat frame=000240 screen=0000 mode4=0000 credits=0000
heartbeat frame=000300 screen=0000 mode4=0000 credits=0000
heartbeat frame=000360 screen=0000 mode4=0000 credits=0000
heartbeat frame=000420 screen=0000 mode4=0000 credits=0000
heartbeat frame=000480 screen=0000 mode4=0000 credits=0000
heartbeat frame=000540 screen=0000 mode4=0000 credits=0000
heartbeat frame=000600 screen=0000 mode4=0000 credits=0000
heartbeat frame=000660 screen=0000 mode4=0000 credits=0000
seq=001 frame=000671 tag=renderer pc=202B80 A5=E0FF004C state=0001/0000/0000 screen=0000 mode4=0000 credits=0000 A=0000 0000 0000 0000 B=0000 0000 0000 0000
seq=002 frame=000672 tag=renderer pc=202B80 A5=E0FF004B state=5000/0100/0000 screen=0000 mode4=0000 credits=0000 A=0000 0000 0000 0000 B=0080 0000 0000 0000
seq=003 frame=000672 tag=renderer pc=202B80 A5=E0FF004B state=5000/0100/0000 screen=0000 mode4=0000 credits=0000 A=0000 0000 0000 0000 B=0080 0000 0000 0000
heartbeat frame=000720 screen=0000 mode4=0000 credits=0000
...
STOP frame=000900 seq=3
```

### From /tmp/build273_ordering_proof.txt (Andy's probe — selected key lines)
```
probe_start start_field=true down_field=false a_field=true
input_inject frame=000020 START_press
[block_a_read/write events at frame 22 (startup init, A5=0, not title path)]
input_inject frame=000120 START_release
input_inject frame=000168 A_press

seq=037 frame=000173 tag=block_a_write pc=FF11FE A5=E0FF004C state=0001/0000/0000 ...
...
seq=041 frame=000180 tag=renderer_0x202B80    pc=202B80 A5=E0FF004C state=0001/0000/0000 ... A=0000 0000 0000 0000 B=0000 0000 0000 0000
seq=042 frame=000180 tag=callsite_a_0x03AAEC  pc=03AAEC A5=E0FF004C state=0001/0000/0000 ... A=0000 0000 0000 0000 B=0000 0000 0000 0000
seq=043 frame=000180 tag=producer_0x05A15E    pc=05A15E A5=E0FF004C state=0001/0000/0000 ... A=0000 0000 0000 0000 B=0000 0000 0000 0000
seq=044 frame=000180 tag=producer_0x05A174    pc=05A174 A5=E0FF004B state=5000/0100/0000 ... A=0000 0000 0000 0000 B=0000 0000 0000 0000
seq=045 frame=000180 tag=callsite_b_0x03AAF2  pc=03AAF2 A5=E0FF004B state=5000/0100/0000 ... A=0000 0000 0000 0000 B=0080 0000 0000 0000
seq=046 frame=000180 tag=renderer_0x202B80    pc=202B80 A5=E0FF004B state=5000/0100/0000 ... A=0000 0000 0000 0000 B=0080 0000 0000 0000
seq=047 frame=000180 tag=renderer_0x202B80    pc=202B80 A5=E0FF004B state=5000/0100/0000 ... A=0000 0000 0000 0000 B=0080 0000 0000 0000
```

### Summary counts (Andy's probe)
```
total_events=47 total_frames=900
hits: producer_5e=1 producer_74=1 bridge=3 callsite_a=1 callsite_b=1
      block_a_write=48 block_a_read=1996
FIRST_PRODUCER_0X059F5E: NOT_OBSERVED
FIRST_PRODUCER_0X05A15E: seq=43 frame=180 pc=05A15E
FIRST_PRODUCER_0X05A174: seq=44 frame=180 pc=05A174
FIRST_RENDERER_0X202B80: seq=41 frame=180 pc=202B80
FIRST_CALLSITE_A_0X03AAEC: seq=42 frame=180 pc=03AAEC
FIRST_CALLSITE_B_0X03AAF2: seq=45 frame=180 pc=03AAF2
CALLSITE_VERDICT: A_BEFORE_B -- producer slot first (CORRECT)
BLOCK_A_VERDICT: SAME_SEQ
```

---

## 8. Frame/Pass-by-Frame Ordering Evidence

### Frame 180 — title-init region hit (from Andy's probe)

| seq | frame | tag                   | pc     | A5       | state            | notes                                      |
|-----|-------|-----------------------|--------|----------|------------------|--------------------------------------------|
| 041 | 180   | renderer_0x202B80     | 202B80 | E0FF004C | 0001/0000/0000   | renderer fires BEFORE callsite_a           |
| 042 | 180   | callsite_a_0x03AAEC   | 03AAEC | E0FF004C | 0001/0000/0000   | first call slot (producer slot) fetched    |
| 043 | 180   | producer_0x05A15E     | 05A15E | E0FF004C | 0001/0000/0000   | ROM's JSR target (wrong addr — data area)  |
| 044 | 180   | producer_0x05A174     | 05A174 | E0FF004B | 5000/0100/0000   | actual function (different A5 context)     |
| 045 | 180   | callsite_b_0x03AAF2   | 03AAF2 | E0FF004B | 5000/0100/0000   | second call slot (renderer slot) fetched   |
| 046 | 180   | renderer_0x202B80     | 202B80 | E0FF004B | 5000/0100/0000   | renderer fires at second call slot          |

### Observations

1. **Callsite A fires before callsite B** (seq=42 before seq=45): proves ordering patch is in place.

2. **Renderer fires FIRST (seq=41) before callsite_a (seq=42)**: The renderer is called from
   a DIFFERENT entry point in the title path BEFORE reaching the 0x03AAEC/0x03AAF2 pair.
   This is NOT from callsite_b (which is seq=45). This earlier renderer invocation is in the
   same frame 180, state=0001/0000/0000 context, before the callsite pair executes.

3. **A5 context changes between seq=043 and seq=044**: callsite_a/producer_0x05A15E execute
   with A5=E0FF004C (state=0001/0000/0000), but producer_0x05A174 shows A5=E0FF004B
   (state=5000/0100/0000). This indicates the JSR to 0x05A15E (data area) caused control
   flow to drift to 0x05A174 from a different execution context.

4. **Producer at 0x059F5E (original arcade address) — NOT observed**: The tap at 0x059F5E
   never fired. The ROM calls 0x05A15E, not 0x059F5E. The relocation bug means the
   producer path starts execution at data, not the intended function entry.

5. **current_screen = 0 throughout**: The hits at frame 180 occurred while the Genesis
   launcher screen was still SCREEN_CONFIG, not SCREEN_FRONTEND_LIVE. The intended
   initialization sequence was not followed.

### Build 272 vs Build 273 comparison (phase1_runtime_ordering_genesis_probe.lua)

| Metric                     | Build 272 (Cody) | Build 273 (Andy) |
|----------------------------|------------------|------------------|
| Producer 0x059F5E hits     | 0                | 0                |
| Renderer 0x202B80 hits     | 3                | 3                |
| Renderer first frame       | 671              | 671              |
| Screen value throughout    | 0000             | 0000             |
| State at first renderer    | 0001/0000/0000   | 0001/0000/0000   |

Results are identical between Build 272 and Build 273 for the directly-comparable probe.
Build 273 produces no regression.

---

## 9. Descriptor Window State at Renderer Entry

### At seq=041 (first renderer hit, frame=180, state=0001/0000/0000)
```
block-A (0xFF11FE..0xFF1204): 0000 0000 0000 0000   (zero — producer not yet run in this context)
block-B (0xFF01BC..0xFF01C2): 0000 0000 0000 0000   (zero)
```

### At seq=046 (second renderer hit, frame=180, state=5000/0100/0000)
```
block-A (0xFF11FE..0xFF1204): 0000 0000 0000 0000   (zero — producer ran at 0x05A15E/0x05A174
                                                      but block-A content not built — expected
                                                      Phase 1 behavior with D-7 reverted)
block-B (0xFF01BC..0xFF01C2): 0080 0000 0000 0000   (first entry non-zero — initial B-block
                                                      values from 0x059F7C fill loop)
```

### Summary
Block-A remains zero throughout (expected for Phase 1 — D-7 builder removed, content is Phase 2).
Block-B partial initial values visible at second renderer entry (0x0080 = y-coord 128).

---

## 10. Exodus Cross-Check

Not used.

---

## 11. Final Conclusion

**Runtime proof is inconclusive because the intended title-init path was not proven to be
reached before measurement.**

Specifically:
- The Genesis `current_screen` variable never transitioned to `SCREEN_FRONTEND_LIVE` (= 4)
  during any run.
- All callsite hits (frame 180) occurred while `current_screen` = 0 (SCREEN_CONFIG), meaning
  the proper SGDK launcher → "START RASTAN" → `genesistan_init_workram_direct()` →
  `restore_launcher_vdp_state()` → SCREEN_FRONTEND_LIVE initialization chain was not followed.
- The hits represent the arcade maincpu entering title state via a partial-init path triggered
  by the A-button injection, not through the intended full SCREEN_FRONTEND_LIVE execution path.

**Mandatory conclusion statement:**

"Runtime proof is inconclusive because the intended title-init path was not proven to be
reached before measurement."

---

## 12. If Inconclusive, Why

### Root cause of inconclusiveness

The MAME harness and available input injection methods could not reliably navigate the SGDK
launcher menu to select "START RASTAN" during the automated 900-frame run window.

Specifically:
1. The DOWN button field (`f_down`) was not found in the ioport map (`down_field=false`).
   Without DOWN presses, the menu cannot be navigated to item 12 ("START RASTAN").
2. The START button field was found (`start_field=true`) and injected, but the START press
   alone (without menu navigation to item 12) did not trigger the launcher action.
3. The A-button press at frame 168 caused some arcade maincpu activity (title state entered
   at frame 173-180) but this is NOT equivalent to the full SCREEN_FRONTEND_LIVE path.

### What would be required for conclusive proof

To prove or disprove ordering on the intended path:
1. Navigate the SGDK launcher to item 12 ("START RASTAN") using 12 DOWN presses followed by
   a confirm button press.
2. Confirm `current_screen` transitions to 4 (SCREEN_FRONTEND_LIVE).
3. After that transition, observe callsite_a and callsite_b in the correct SCREEN_FRONTEND_LIVE
   execution loop, with screen=4 confirmed at measurement time.

### Supporting evidence from the existing observation

Despite the path-entry failure, the static evidence is clear:
- The ordering patch IS present (Patch A at 0x03AAEC, Patch B at 0x03AAF2).
- The callsite structure is correct: callsite_a (producer slot) fires before callsite_b
  (renderer slot) in the observed title-adjacent passes (seq=42 before seq=45).
- The producer address relocation anomaly (0x05A15E vs intended 0x05A174) is pre-existing
  and present in both Build 272 and Build 273.
- Block-A remains zero at renderer entry (expected for Phase 1 — D-7 removed, content is Phase 2).
- Block-B shows initial 0x0080 values at second renderer pass (expected from 0x059F7C fill loop).
