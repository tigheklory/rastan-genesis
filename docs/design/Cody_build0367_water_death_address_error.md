# Cody — Build 0367 Water-Death Address Error Fix

Date: 2026-09-22  
Agent: Cody  
Accepted input baseline: Build 0366  
Produced build: Build 0367

## Result and acceptance status

Build 0367 corrects the malformed native HUD-queue store that caused the reported
water-death address error. The canonical and gameplay-entry gates pass, and the normal
GENESIS NTSC MAME trace records no address error, bus error, illegal instruction, or
crash-handler entry. Neither automated run reaches the reported water-death sequence,
so this is a testable candidate rather than a claim of user acceptance. Tighe's BlastEm
water-death and regression validation remains required.

The semantic cut is unchanged: retained arcade gameplay energy/status decisions feed a
native Genesis HUD queue directly. The already-retired PC090OJ record-writing tail stays
retired. No legacy hardware tail was newly removed in Build 0367, and no legacy hardware
dependency was reintroduced.

## Reported exception and exact effective address

The Build 0366 crash screen reported:

- stacked Genesis PC: `0x00073884`
- fault address: `0x00FFBC3F`
- relevant registers: `A0=0x00FFB800`, `D0=0x000003CF`
- captured `SR=0x2F10`
- crash-handler warning: `SP OUT OF WRAM RANGE`

Build 0366 contained these bytes beginning at `0x00073880`:

```text
31 80 01 70 00 00 00 14
```

They came from this source spelling:

```asm
move.w %d0, (2 * NATIVE_QUEUE_ENTRY_BYTES + 4)(%a0)
```

GNU `as` selected indexed/full-extension syntax rather than the intended 68000
`d16(A0)` mode. On the target 68000, the active brief-index interpretation forms the
word-write destination as:

```text
base A0       0x00FFB800
index D0.W  + 0x000003CF
disp8       + 0x00000070
             ----------
destination  0x00FFBC3F
```

`0x00FFBC3F` is odd, so the `MOVE.W` write raises the address error. The faulting opcode
starts at Genesis PC `0x00073880`; the stacked `0x00073884` reflects the 68000's progress
through this malformed effective-address encoding, not a separate bad instruction. `A0`
is the correct native HUD queue base and `D0=0x03CF` is a valid HUD cell/code value. The
failure is therefore neither a stale death pointer nor corrupted queue state: a valid
data value was accidentally consumed as an address index.

The other directly useful displayed values are consistent with this producer: the helper
uses `0x03D5` as its empty/blink code, `0x0080` in HUD positioning, and retained work RAM
base `A5=0x00FF0000`. They are not needed to establish the exact fault address. No semantic
claim is made from screen values that were not needed or not unambiguously legible.

## Arcade provenance and water-death comparison

Original arcade code at `0x05A1EC..0x05A20C` selects the HUD code and performs an ordinary
word store to the status object's destination at offset `+20`. In the direct-native helper
`genesistan_pc090oj_hook_status_sprite_5a098`, that destination is native HUD queue entry 2's
code word. The intended operation is therefore exactly `MOVE.W D0,20(A0)`.

The helper's sole retained call source is arcade `0x051054`, within the shared gameplay
update reached from arcade `0x041F0E`. Static comparison shows that the water/floor type-8
path at original arcade `0x053E00..0x053E0C` sets contact bit 9 and player mode
`A5+0x10E8=8`; it does not replace the energy/status pointer or create a water-specific HUD
destination. Normal damage paths update retained energy at `A5+0x013A` and refresh state at
`A5+0x12FC`. Both paths converge on the same status producer. The first relevant divergence
is consequently the native status helper's malformed effective address when its low-energy
code is selected, before the later death/retirement/checkpoint sequence.

Existing life-loss provenance documents the retained mode-8 transition through original
`0x051998` into the ordinary death-state sequence. Build 0367 does not alter that state
machine, respawn/checkpoint data, water contact handling, or any death pointer.

## Stack warning classification

The `SP OUT OF WRAM RANGE` message is classified as **OTHER**, not the root cause. The ROM's
initial supervisor stack is `0x00FF0000`; predecrement naturally enters `0x00FEFFFF...`,
which is in the Genesis WRAM mirror. The crash screen's range check recognizes only the
canonical `0x00FF0000`-and-above spelling when deciding whether to dump the stack. No stack
instruction, call convention, return address, or stack owner changed in this fix, while the
register arithmetic above independently reproduces the exact reported fault address.

## Source correction

Build 0367 changes only the address-mode expression in this producer:

```asm
.equ NATIVE_HUD_LOW_ENERGY_CODE_OFFSET, 0x0014

.Lstatus_blink_store:
    lea     native_queue_hud, %a0
    move.w  %d0, NATIVE_HUD_LOW_ENERGY_CODE_OFFSET(%a0)
```

Using an absolute assembler symbol forces the intended 68000 `d16(A0)` encoding while
retaining the declarative meaning of the queue layout. This is a source correction, not a
NOP, RTS bypass, equal-length patch, shadow, fallback, water special case, or suppressed
rendering path. The remap spec did not require a change because the affected helper is linked
native source and the existing semantic replacement remains authoritative.

Final canonical machine code is:

```text
0007387A  41F9 00FF B800   lea     0x00FFB800,a0
00073880  3140 0014        move.w  d0,20(a0)
00073884  0C6D 0001 1328   cmpi.w  #1,4904(a5)
```

Thus the corrected instruction is four bytes, `31 40 00 14`, and the old stacked PC now
names the valid following comparison. A narrow audit of `pc090oj_hooks.s` found no other
instance of the malformed arithmetic-expression-before-`(An)` form. Same-syntax candidates:
**NONE**.

## Files changed for Build 0367

- `apps/rastan-direct/src/pc090oj_hooks.s` — corrected the native HUD queue code-word store.
- `docs/design/Cody_build0367_water_death_address_error.md` — this standalone proof.
- `AGENTS_LOG.md` — durable build/result entry.

The working tree also contains prior accepted work. Those unrelated changes are not attributed
to Build 0367.

Semantic subsystem changed: direct-native gameplay energy/status HUD queue address formation.
Rope visual/contact semantics, rope attachment/release, cave-block collision, cave palette,
water contact logic, death/respawn logic, and palette decisions are unchanged at source level.

## Build and validation evidence

Counter transition: `366 -> 367`  
Consumed ledger: `0367 PRODUCED 2026-09-22 auto-recorded-by-release [canonical=PASS entry=PASS epoch=FAIL]`

All artifacts are 1,719,992 bytes:

| Variant | Artifact | SHA-256 |
|---|---|---|
| canonical | `dist/rastan-direct/rastan_direct_video_test_build_0367.bin` | `10e17efe76571205c89755e8f2472530cf3b4ab8f11b2b2075d8de7b85efaf61` |
| `_d` | `dist/rastan-direct/rastan_direct_video_test_build_0367_d.bin` | `55938129445985b57a64d02cd4cc72f58fe9d7ce4cbcfe764e1b1849854e6d4c` |
| `_s` | `dist/rastan-direct/rastan_direct_video_test_build_0367_s.bin` | `91f8614536e476baaa419b3b7148693a2ce63c5049206318a8bbadb4a7715f82` |
| `_do` | `dist/rastan-direct/rastan_direct_video_test_build_0367_do.bin` | `4a7c5a4ab43203c67b40385bfc9943e1b7c09c134889c8f4565832d101d82a35` |
| `_c` | `dist/rastan-direct/rastan_direct_video_test_build_0367_c.bin` | `93c6be9682bf6c5d52b4b2d13a3491a6f1398803287a02f7d2d991a0fe31fce6` |

Static/generated validation:

- object disassembly: `move.w %d0,%a0@(20)`
- final canonical disassembly: corrected opcode at `0x00073880`
- pre- and post-patch boot guards: PASS
- canonical gate: PASS (`GATE_PASS`)
- opcode replacements: 228
- shift replacements: 70; branch repairs: 7,214; absolute-long repairs: 630
- expected Genesis-byte coverage: `0x1A3EB8`; coverage delta: `0x0`
- five-artifact complete-set check: PASS
- known seven-epoch phase-1 gate: FAIL; the Makefile preserved and recorded the numbered build

Dynamic validation used GENESIS NTSC MAME:

- gameplay-entry gate: PASS, 240 frames, gameplay/control observed, zero address errors,
  bus errors, illegal instructions, or crash-handler entries; trace
  `states/traces/build0367_gameplay_entry_gate_20260922_173806`
- standard 30-second trace: 1,798 frames; trace
  `states/traces/rastan_direct_video_test_build_0367_mame_30s_20260922_173809`

Neither automated trace reaches the user-reported water-death event. ORIGINAL ARCADE evidence
for this fix is static disassembly/Ghidra provenance; no new arcade runtime capture was needed.
BlastEm validation is not available in the automated gate and remains the user acceptance step.

## Required user regression validation

Test Build 0367 in BlastEm and confirm:

1. the same water death no longer raises the `0x00073884` / `0x00FFBC3F` address error;
2. the death animation and death-state progression complete;
3. respawn/checkpoint behavior remains correct;
4. ordinary damage and low-energy HUD behavior remain correct;
5. the Build 0361 `D00462` fix remains intact;
6. rope render/grab/ride/jump-release behavior remains intact;
7. the Build 0366 cave block remains solid and destructible.

The cave-block color is known to remain wrong, is deferred to Andy, and is not a Build 0367
acceptance criterion.

## Tool reuse declaration

Existing project tools reused: canonical Ghidra exports and original maincpu disassembly;
Makefile-owned assembler/linker/postpatch pipeline; address map and final disassembly; boot,
canonical, gameplay-entry, complete-artifact, transition-retention, and seven-epoch gates; and
the established GENESIS NTSC MAME trace harness.

New tooling created: **NONE**.  
Why new tooling was necessary: **N/A**.

## Stop status

Technical blocker: **NO**. Build 0367 is complete and testable. Final acceptance of the exact
water-death path is pending Tighe's BlastEm result.
