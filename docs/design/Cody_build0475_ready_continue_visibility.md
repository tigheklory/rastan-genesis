# Cody Build 0475 — READY / Continue Visibility Attempt

## Result

Build 0475 is **REJECTED / NOT ACCEPTED / PERMANENTLY CONSUMED**. The Makefile reached the
postpatch transformer, produced its rolling prepatch ROM, and assigned crash/build identity 0475,
but failed before numbered publication. `.DELETE_ON_ERROR` removed the rolling output. There is no
Build-0475 numbered ROM or SHA-256; the artifact is missing and must not be recreated.

Exact attempted source was `a6b0b6796de0f638e78e6cf10f708ce1396c0d7e`. Accepted Build 0473
remains unchanged. Build 0474 remains rejected/consumed.

## Failure

Canonical shift reflow itself succeeded for 86 replacement sites, 7,202 relative branches, two
declared branches, 628 absolute-long references, and 20 jump-table entries. Postpatch then correctly
rejected the byte-neutral site at retained `arcade_pc 0x03A47E`: its validated instruction block
still expected the prior shifted BSR displacement `0x16C8`, while the two new RG-016 insertions before
that source and two before its retained `0x03BB48` target require `0x16D4`. This is a stale generated-
layout expectation, not a READY/Continue semantic failure.

No primary runtime regression, seven-ROM family, or rope benchmark ran because no final ROM was
published. The correction must update that exact reflow-validated byte sequence and use the next
sequential build number.

## Artifact record

- baseline: accepted Build 0473
- attempted build: 0475
- source: `a6b0b6796de0f638e78e6cf10f708ce1396c0d7e`
- normal ROM: artifact missing
- SHA-256: unavailable
- size: unavailable
- counter transition: 474 -> 475 (manual consumed-number preservation)
- status: REJECTED / NOT ACCEPTED / ARTIFACT MISSING
- existing project tools reused: Makefile-owned linker/postpatch/reflow/gates
- new tooling created: none

## USER MUST VERIFY

Nothing from Build 0475 can be tested because no numbered ROM was published. Hardware verification
belongs to the next successfully produced candidate.

STOP status: continue only with the next sequential number after correcting the proven reflow
expectation; never rebuild or reuse 0475.
