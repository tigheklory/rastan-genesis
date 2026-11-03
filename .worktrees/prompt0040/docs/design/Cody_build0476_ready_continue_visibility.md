# Cody Build 0476 — READY / Continue Visibility Candidate

## Result

Build 0476 is **REJECTED / NOT ACCEPTED / PERMANENTLY CONSUMED**. It produced the complete seven-ROM
family and passed postpatch, canonical, boot, static final-life and configured-family verification,
but the mandatory Genesis NTSC gameplay-entry and epoch gates both stalled before gameplay. No CPU
exception occurred.

## Artifact record

- baseline: accepted Build 0473
- produced build: 0476
- exact source: `cd44c988a7b38b0c509e7f339ee9a07f387f537c`
- normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0476.bin`
- SHA-256: `a53de59abe75d1b4b517b9e888bf1e14f56f003c6edfdd075d95d367c34999d9`
- size: 2,739,896 bytes
- counter transition: 475 -> 476
- replacement inventory: 228 byte-neutral sites; 86 shift replacements; generated reflow repaired
  7,202 relative branches, two declared branches, 628 absolute-long references and 20 jump-table
  entries
- seven-ROM family: complete and configuration-verified

## Root cause

Genesis NTSC evidence stopped at tuple `2/2/7`, repeatedly executing READY construction/clear work.
The current original arcade disassembly proves a nine-entry READY-controller jump table at
`0x03A5D2`, consumed by `0x03A5BC..0x03A5D0`. Entry 7 is displacement `0x0184` to READY dwell
`0x03A756`; entry 8 is `0x0192` to `0x03A764`. RG-016 inserts six bytes before the first target and
twelve before the second. Because that table was not declared, entry 7 landed six bytes early and
re-entered READY construction every frame.

This is the same missing-crossing-reference class warned by Builds 0470/0471. The bounded correction
is to declare the existing nine-entry table for canonical shift reflow. No presentation hook,
gameplay logic, wait, poll, fallback or renderer behavior changes.

## Validation

- postpatch/canonical/boot: PASS
- static final-life target: PASS (`0x03A3C0 -> 0x03B34A`)
- generated sprite/frame and direct-dispatch verification: PASS
- RG-014 retained-cut/register preservation: PASS
- native HUD/item/title verification: PASS
- seven-ROM family: PASS
- Genesis NTSC R1-S1 entry: FAIL, maximum frame budget, gameplay not reached
- Genesis NTSC production epoch 0: FAIL, gameplay installer not reached
- primary death/READY/Continue routes: NOT RUN because entry failure is an earlier hard gate
- rope: NOT RUN

Existing project tools reused: Makefile-owned canonical/build guards, gameplay-entry gate, epoch gate,
generated graphics verifiers and final-life static verifier. New tooling created: none.

## USER MUST VERIFY

Do not hardware-test Build 0476 as a candidate. It is retained only as rejected evidence.

STOP status: continue only as the next sequential build after declaring the proven table; never
overwrite or reuse 0476.
